#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""GTach application entry point."""

import os
import sys
import logging
import argparse
import datetime
import faulthandler
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

# Module-level handler references for runtime manipulation.
_start_handler: logging.Handler = None
_debug_handler: logging.Handler = None
# Kept referenced so faulthandler's fd stays open for the process
# lifetime; faulthandler writes to the file descriptor directly.
_stacks_file = None
# Rotation is once per PROCESS, not once per arm. Arming occurs on
# every OPTIONS toggle-on, and rotating each time would push a
# just-captured reproduction off the end of the backup chain — the
# operator toggling debug off and on three times would discard the
# very dumps they had just gone to the trouble of provoking
# (issue-3b8c50f2).
_stacks_rotated = False

_LOG_FORMAT = '%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'
_LOG_DATE_FMT = '%Y-%m-%d %H:%M:%S'
_START_LOG = '/opt/gtach/start.log'
_DEBUG_LOG = '/opt/gtach/debug.log'
_STACKS_LOG = '/opt/gtach/stacks.log'
# A dump of four threads measures ~604 bytes and the interval is 15 s,
# so an armed run produces ~145 KB per hour. Three backups plus the
# live file bound cross-run accumulation at four files — enough to
# span a watchdog restart and the run before it, which is the span
# issue-2ac1c602's verification needs.
_STACKS_BACKUPS = 3
# 10 MB is about ninety minutes of debug output at 30 Hz.
# Ten backups gives roughly sixteen hours of history for
# 110 MB of card. bin/gtach.service caps a restart loop at
# three rapid starts (StartLimitBurst), so rotate-at-start
# cannot exhaust the backups (issue-6a3b7c52).
_DEBUG_MAX_BYTES = 10 * 1024 * 1024
_DEBUG_BACKUPS = 10


def setup_logging(debug: bool = False) -> None:
    global _start_handler, _debug_handler

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # start.log — truncated at boot; startup records only.
    try:
        _start_handler = logging.FileHandler(_START_LOG, mode='w', encoding='utf-8')
        _start_handler.setLevel(logging.DEBUG)
        _start_handler.setFormatter(formatter)
        root.addHandler(_start_handler)
    except OSError as e:
        print(f'[gtach] WARNING: could not open {_START_LOG}: {e}', file=sys.stderr)

    # debug.log — rotated at boot, so each run has its own file
    # and the previous ten survive; suppressed unless toggled on.
    #
    # NOTE the absence of mode='w'. RotatingFileHandler discards
    # it whenever maxBytes > 0 and opens in append mode
    # regardless — deliberate CPython behaviour, so that
    # rotation is not defeated by truncation. The previous
    # mode='w' here was dead, and debug.log had never truncated
    # despite the comment saying it did (issue-6a3b7c52).
    # Rotation at start is done explicitly below instead, which
    # keeps the previous run rather than discarding it — the
    # distinction that matters under systemd Restart=always.
    #
    # The size is read BEFORE the handler is constructed, because
    # construction opens the file.
    _had_content = False
    try:
        _had_content = os.path.getsize(_DEBUG_LOG) > 0
    except OSError:
        _had_content = False

    try:
        _debug_handler = RotatingFileHandler(
            _DEBUG_LOG, maxBytes=_DEBUG_MAX_BYTES,
            backupCount=_DEBUG_BACKUPS, encoding='utf-8'
        )
        if _had_content:
            try:
                _debug_handler.doRollover()
            except Exception as e:
                print(
                    f'[gtach] WARNING: could not rotate '
                    f'{_DEBUG_LOG}: {e}', file=sys.stderr
                )
        _debug_handler.setLevel(logging.CRITICAL + 1)  # suppressed
        _debug_handler.setFormatter(formatter)
        root.addHandler(_debug_handler)
    except OSError as e:
        print(f'[gtach] WARNING: could not open {_DEBUG_LOG}: {e}', file=sys.stderr)

    if debug and _debug_handler is not None:
        _debug_handler.setLevel(logging.DEBUG)

    if debug:
        enable_stack_dumps()


def _rotate_stacks_log() -> None:
    """Shift stacks.log outward by one generation.

    Keeps _STACKS_BACKUPS generations; what was the oldest is
    discarded. A no-op when the live file is absent or empty, so a run
    that armed and produced nothing does not consume a generation.

    Generations shift from the highest downwards. Ascending order would
    overwrite each generation with the one below it before it had
    itself been moved, collapsing the whole chain to one run's content.

    os.replace rather than os.rename: an existing destination must be
    overwritten rather than raising, which os.rename does on some
    platforms.

    Raises:
        OSError: If a rename or the size check fails. The caller arms
            regardless — a failure here costs history, not evidence.
    """
    if not os.path.exists(_STACKS_LOG) or os.path.getsize(_STACKS_LOG) == 0:
        return

    for i in range(_STACKS_BACKUPS - 1, 0, -1):
        source = f'{_STACKS_LOG}.{i}'
        if os.path.exists(source):
            os.replace(source, f'{_STACKS_LOG}.{i + 1}')

    os.replace(_STACKS_LOG, f'{_STACKS_LOG}.1')


def _stacks_header() -> str:
    """Build the line identifying one contiguous block of dumps.

    Returns:
        A single newline-terminated line carrying the gtach version,
        the process PID and an ISO-8601 local timestamp.
    """
    try:
        from importlib.metadata import version as _pkg_version
        _ver = _pkg_version('gtach')
    except Exception:
        _ver = 'unknown'

    _now = datetime.datetime.now().isoformat(timespec='seconds')
    return f'=== gtach {_ver} pid {os.getpid()} armed {_now} ===\n'


def enable_stack_dumps() -> bool:
    """Arm periodic all-thread stack dumps to stacks.log.

    faulthandler's repeat timer runs in a C thread and never takes the
    GIL to schedule itself, so its dumps still land while every Python
    thread is stalled — which is exactly the window that needs
    observing (issue-2ac1c602). The dumps were originally written to
    sys.stderr, which under systemd is the journal rather than the
    app-owned log set beside start.log and debug.log, so they were not
    recoverable alongside the run they belonged to.

    Arming lives here, with the other log-file handles, but is
    deliberately callable at any point in the process lifetime rather
    than from setup_logging alone. bin/gtach.service's ExecStart passes
    no --debug, so args.debug is False on every service-launched run
    and the startup path is not the path that matters in production
    (issue-2ac1c602 iteration 3). Debug is enabled in the field at
    runtime, through the OPTIONS screen toggle, and
    GTachApplication.toggle_debug_logging calls this function on that
    signal.

    Idempotent: a second call while already armed opens no second file
    handle and stacks no second timer. Safe to call from a thread other
    than the one that ran setup_logging — faulthandler's own calls are
    thread-safe, and _stacks_file, the only shared state, transitions
    by single assignment.

    Two things happen around the arming itself. On the FIRST arm of a
    process lifetime the existing stacks.log is rotated, bounding
    cross-run accumulation without discarding the previous run — mode
    is 'a', so a relaunch appends rather than truncating. And on EVERY
    arm an identifying header is written before faulthandler is armed,
    because the dumps themselves carry no timestamp, PID or run
    identifier and would otherwise concatenate indistinguishably across
    process lifetimes (issue-3b8c50f2).

    The PID in that header is not incidental. Two headers with
    different PIDs in one stacks.log is direct evidence that systemd
    restarted the process, which is what issue-2ac1c602's verification
    requires — captured automatically, rather than needing an operator
    watching systemctl at the moment it happens.

    Both additions run at arming time, when the process is by
    definition healthy: the operator has just enabled the toggle, or
    the process has just started. Nothing here runs during a stall,
    which is why the anchor it writes survives one. Deliberately no
    Python-side periodic timer or per-dump timestamp: such a timer
    would stall in exactly the window this file exists to capture.

    Returns:
        True if stack dumps are armed on return — including when they
        were already armed. False if the log file could not be opened.
        Rotation and header failures are reported to stderr but do not
        change the result; the dumps matter more than their label.
    """
    global _stacks_file, _stacks_rotated

    if _stacks_file is not None:
        return True

    if not _stacks_rotated:
        try:
            _rotate_stacks_log()
        except OSError as e:
            print(f'[gtach] WARNING: could not rotate {_STACKS_LOG}: {e}',
                  file=sys.stderr)
        finally:
            # Set whether or not rotation succeeded, so a persistent
            # failure is not retried on every subsequent arm.
            _stacks_rotated = True

    try:
        _stacks_file = open(_STACKS_LOG, mode='a', buffering=1, encoding='utf-8')
        # Before arming, so that no dump can be written above the
        # header identifying it.
        try:
            _stacks_file.write(_stacks_header())
        except Exception as e:
            print(f'[gtach] WARNING: could not write {_STACKS_LOG} header: {e}',
                  file=sys.stderr)
        faulthandler.enable(file=_stacks_file)
        faulthandler.dump_traceback_later(15, repeat=True, file=_stacks_file)
        return True
    except OSError as e:
        print(f'[gtach] WARNING: could not open {_STACKS_LOG}: {e}', file=sys.stderr)
        _stacks_file = None
        return False


def disable_stack_dumps() -> None:
    """Cancel periodic stack dumps and close stacks.log.

    A no-op when nothing is armed. The teardown order is load-bearing:
    the repeat timer is cancelled and faulthandler disabled BEFORE the
    file is closed, because a dump firing against a closed descriptor
    would fault inside the C timer thread.

    Errors closing the file are swallowed, but _stacks_file is set to
    None regardless so that a subsequent enable_stack_dumps can re-arm.
    """
    global _stacks_file

    if _stacks_file is None:
        return

    faulthandler.cancel_dump_traceback_later()
    faulthandler.disable()
    try:
        _stacks_file.close()
    except Exception as e:
        print(f'[gtach] WARNING: could not close {_STACKS_LOG}: {e}', file=sys.stderr)
    _stacks_file = None


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='GTach — real-time engine tachometer')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--debug', action='store_true')
    try:
        from importlib.metadata import version as _pkg_version
        _ver = f'GTach {_pkg_version("gtach")}'
    except Exception:
        _ver = 'GTach'
    parser.add_argument('--version', action='version', version=_ver)
    parser.add_argument('--validate-config', action='store_true')
    parser.add_argument('--validate-dependencies', action='store_true')
    # Imported here rather than at module scope: main.py is the entry
    # point and importing comm.transport at import time would pull the
    # transport stack in ahead of argument parsing (change-6481f8ce).
    from .comm.transport import TRANSPORT_NAMES
    parser.add_argument('--transport',
                        choices=list(TRANSPORT_NAMES),
                        default=None)
    parser.add_argument('--obd-host', default='localhost')
    parser.add_argument('--obd-port', type=int, default=35000)
    parser.add_argument('--serial-port', default=None)
    return parser.parse_args()


def find_configuration_file() -> Optional[Path]:
    import os
    env = os.getenv('GTACH_CONFIG')
    if env and Path(env).exists():
        return Path(env)
    user = Path.home() / '.config' / 'gtach' / 'config.yaml'
    if user.exists():
        return user
    system = Path('/etc/gtach/config.yaml')
    if system.exists():
        return system
    return None


def main() -> int:
    args = parse_arguments()
    config_file = args.config or find_configuration_file()
    setup_logging(args.debug)

    if args.validate_dependencies:
        from .utils import validate_dependencies
        v = validate_dependencies(debug=args.debug)
        v.print_report(show_successful=args.debug)
        return 0 if v.can_start_application() else 1

    if args.validate_config:
        try:
            from .utils.config import ConfigManager
            ConfigManager(config_file).load_config()
            return 0
        except Exception as e:
            print(f'Config invalid: {e}')
            return 1

    from .app import GTachApplication
    app = GTachApplication(config_file, args.debug, args)
    app.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
