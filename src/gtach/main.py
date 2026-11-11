#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""GTach application entry point."""

import argparse
import datetime
import faulthandler
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, TextIO

from .utils.home import DEFAULT_GTACH_HOME, gtach_home

# Module-level handler references for runtime manipulation.
_start_handler: Optional[logging.Handler] = None
_debug_handler: Optional[logging.Handler] = None
_error_handler: Optional[logging.Handler] = None
# Kept referenced so faulthandler's fd stays open for the process
# lifetime; faulthandler writes to the file descriptor directly.
_stacks_file: Optional[TextIO] = None
# stacks.log is rotated once per process, not once per arm
# (issue-3b8c50f2).
_stacks_rotated = False

_LOG_FORMAT = "%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s"
_LOG_DATE_FMT = "%Y-%m-%d %H:%M:%S"
# Log file paths. These hold the default-home paths until setup_logging
# derives them from gtach_home() (issue-042dd7ff).
_START_LOG = str(DEFAULT_GTACH_HOME / "start.log")
_DEBUG_LOG = str(DEFAULT_GTACH_HOME / "debug.log")
_STACKS_LOG = str(DEFAULT_GTACH_HOME / "stacks.log")
_ERROR_LOG = str(DEFAULT_GTACH_HOME / "error.log")
# Dumps are written on fatal errors and on request (SIGUSR1), so each
# run's file is small; three backups span a watchdog restart and the run
# before it (issue-2ac1c602).
_STACKS_BACKUPS = 3
# 10 MB is about ninety minutes of debug output at 30 Hz; ten backups
# keep about sixteen hours (issue-6a3b7c52).
_DEBUG_MAX_BYTES = 10 * 1024 * 1024
_DEBUG_BACKUPS = 10
# error.log: WARNING and above, size rotation only (issue-269871a0).
_ERROR_MAX_BYTES = 1 * 1024 * 1024
_ERROR_BACKUPS = 5
# Root logger level after startup while debug is off.
_RUNTIME_LOG_LEVEL = logging.WARNING


def _derive_log_paths() -> None:
    """Set the four log paths from gtach_home()."""
    global _START_LOG, _DEBUG_LOG, _STACKS_LOG, _ERROR_LOG
    home = gtach_home()
    _START_LOG = str(home / "start.log")
    _DEBUG_LOG = str(home / "debug.log")
    _STACKS_LOG = str(home / "stacks.log")
    _ERROR_LOG = str(home / "error.log")


def set_runtime_log_level(debug: bool) -> None:
    """Set the root logger level for the running application.

    DEBUG while debug is on; WARNING otherwise, so logger.debug and
    logger.info calls build no record. Handler levels are unchanged
    (issue-042dd7ff).

    Args:
        debug: Whether debug logging is on.
    """
    logging.getLogger().setLevel(logging.DEBUG if debug else _RUNTIME_LOG_LEVEL)


def setup_logging(debug: bool = False) -> None:
    """Attach the three root log handlers under gtach_home().

    The root logger is set to DEBUG for startup; set_runtime_log_level
    lowers it once startup is complete.

    * start.log — truncated at boot; written during startup and then
      silenced by GTachApplication._finish_startup_logging.
    * debug.log — rotated at start; suppressed unless debug is on.
    * error.log — always on at WARNING and above; size-rotated only and
      never rotated at start (issue-269871a0).

    A handler whose file cannot be opened is skipped with a warning on
    stderr; logging setup never prevents startup.

    Args:
        debug: Enable debug.log at DEBUG and arm stack dumps.
    """
    global _start_handler, _debug_handler, _error_handler

    _derive_log_paths()
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # start.log — truncated at boot; startup records only.
    try:
        _start_handler = logging.FileHandler(_START_LOG, mode="w", encoding="utf-8")
        _start_handler.setLevel(logging.DEBUG)
        _start_handler.setFormatter(formatter)
        root.addHandler(_start_handler)
    except OSError as e:
        print(f"[gtach] WARNING: could not open {_START_LOG}: {e}", file=sys.stderr)

    # debug.log — rotated at start, so each run has its own file;
    # suppressed unless toggled on. RotatingFileHandler opens in append
    # mode when maxBytes > 0, so rotation is explicit; the size is read
    # before construction opens the file (issue-6a3b7c52).
    _had_content = False
    try:
        _had_content = os.path.getsize(_DEBUG_LOG) > 0
    except OSError:
        _had_content = False

    try:
        _debug_handler = RotatingFileHandler(
            _DEBUG_LOG,
            maxBytes=_DEBUG_MAX_BYTES,
            backupCount=_DEBUG_BACKUPS,
            encoding="utf-8",
        )
        if _had_content:
            try:
                _debug_handler.doRollover()
            except Exception as e:
                print(
                    f"[gtach] WARNING: could not rotate " f"{_DEBUG_LOG}: {e}",
                    file=sys.stderr,
                )
        _debug_handler.setLevel(logging.CRITICAL + 1)  # suppressed
        _debug_handler.setFormatter(formatter)
        root.addHandler(_debug_handler)
    except OSError as e:
        print(f"[gtach] WARNING: could not open {_DEBUG_LOG}: {e}", file=sys.stderr)

    # error.log — always on, WARNING and above; not rotated at start,
    # so a fault that caused a restart stays in the live file
    # (issue-269871a0).
    try:
        _error_handler = RotatingFileHandler(
            _ERROR_LOG,
            maxBytes=_ERROR_MAX_BYTES,
            backupCount=_ERROR_BACKUPS,
            encoding="utf-8",
        )
        _error_handler.setLevel(logging.WARNING)
        _error_handler.setFormatter(formatter)
        root.addHandler(_error_handler)
    except OSError as e:
        _error_handler = None
        print(f"[gtach] WARNING: could not open {_ERROR_LOG}: {e}", file=sys.stderr)

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
        source = f"{_STACKS_LOG}.{i}"
        if os.path.exists(source):
            os.replace(source, f"{_STACKS_LOG}.{i + 1}")

    os.replace(_STACKS_LOG, f"{_STACKS_LOG}.1")


def _stacks_header() -> str:
    """Build the line identifying one contiguous block of dumps.

    Returns:
        A single newline-terminated line carrying the gtach version,
        the process PID and an ISO-8601 local timestamp.
    """
    try:
        from importlib.metadata import version as _pkg_version

        _ver = _pkg_version("gtach")
    except Exception:
        _ver = "unknown"

    _now = datetime.datetime.now().isoformat(timespec="seconds")
    return f"=== gtach {_ver} pid {os.getpid()} armed {_now} ===\n"


def enable_stack_dumps() -> bool:
    """Arm fatal-error capture to stacks.log.

    While armed, a fatal error (segmentation fault, abort) writes the
    traceback of every thread to stacks.log. faulthandler's dumps of a
    live process are not used, because they terminated the process on
    the Pi (issue-1a8f40ea); on-request dumps are written by
    gtach.utils.stack_dump.

    Callable at any point in the process: setup_logging calls it with
    --debug, and GTachApplication.toggle_debug_logging calls it when
    debug is switched on at runtime.

    Idempotent: a second call while armed opens no second file. On the
    first arm of a process stacks.log is rotated; on every arm a header
    with version, PID and time is written before faulthandler is armed,
    so dumps from different runs can be told apart (issue-3b8c50f2).

    Returns:
        True if stack dumps are armed on return, including when they
        were already armed. False if the log file could not be opened.
        Rotation and header failures are reported to stderr but do not
        change the result.
    """
    global _stacks_file, _stacks_rotated

    if _stacks_file is not None:
        return True

    if not _stacks_rotated:
        try:
            _rotate_stacks_log()
        except OSError as e:
            print(
                f"[gtach] WARNING: could not rotate {_STACKS_LOG}: {e}", file=sys.stderr
            )
        finally:
            # Set whether or not rotation succeeded, so a persistent
            # failure is not retried on every subsequent arm.
            _stacks_rotated = True

    try:
        _stacks_file = open(_STACKS_LOG, mode="a", buffering=1, encoding="utf-8")
        # Before arming, so that no dump can be written above the
        # header identifying it.
        try:
            _stacks_file.write(_stacks_header())
        except Exception as e:
            print(
                f"[gtach] WARNING: could not write {_STACKS_LOG} header: {e}",
                file=sys.stderr,
            )
        faulthandler.enable(file=_stacks_file)
        return True
    except OSError as e:
        print(f"[gtach] WARNING: could not open {_STACKS_LOG}: {e}", file=sys.stderr)
        _stacks_file = None
        return False


def disable_stack_dumps() -> None:
    """Disarm fatal-error capture and close stacks.log.

    A no-op when nothing is armed. The teardown order is load-bearing:
    faulthandler is disabled BEFORE the file is closed, because a fatal
    error written to a closed descriptor would itself fault.

    Errors closing the file are swallowed, but _stacks_file is set to
    None regardless so that a subsequent enable_stack_dumps can re-arm.
    """
    global _stacks_file

    if _stacks_file is None:
        return

    faulthandler.disable()
    try:
        _stacks_file.close()
    except Exception as e:
        print(f"[gtach] WARNING: could not close {_STACKS_LOG}: {e}", file=sys.stderr)
    _stacks_file = None


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GTach — real-time engine tachometer")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--debug", action="store_true")
    try:
        from importlib.metadata import version as _pkg_version

        _ver = f'GTach {_pkg_version("gtach")}'
    except Exception:
        _ver = "GTach"
    parser.add_argument("--version", action="version", version=_ver)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-dependencies", action="store_true")
    # Imported here rather than at module scope: main.py is the entry
    # point and importing comm.transport at import time would pull the
    # transport stack in ahead of argument parsing (change-6481f8ce).
    from .comm.transport import TRANSPORT_NAMES

    parser.add_argument("--transport", choices=list(TRANSPORT_NAMES), default=None)
    parser.add_argument("--obd-host", default="localhost")
    parser.add_argument("--obd-port", type=int, default=35000)
    parser.add_argument("--serial-port", default=None)
    return parser.parse_args()


def _run_validation(args: argparse.Namespace) -> Optional[int]:
    """Run a validation command if one was requested.

    Logs to stderr only and opens no log file, so it can run beside the
    service (issue-042dd7ff).

    Args:
        args: Parsed arguments.

    Returns:
        The exit status, or None when no validation command was given.
    """
    if not (args.validate_dependencies or args.validate_config):
        return None
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.debug else logging.WARNING,
        format=_LOG_FORMAT,
        datefmt=_LOG_DATE_FMT,
    )
    config_file = args.config

    if args.validate_dependencies:
        from .utils import validate_dependencies

        v = validate_dependencies(debug=args.debug)
        v.print_report(show_successful=args.debug)
        return 0 if v.can_start_application() else 1

    from .utils.config import ConfigStore

    store = ConfigStore(Path(config_file) if config_file else None)
    errors = store.validate()
    for error in errors:
        print(f"Config invalid: {error}")
    if errors:
        return 1
    print(f"Config valid: {store.path}")
    return 0


def main() -> int:
    """Run GTach.

    Returns:
        The process exit status: 1 after a startup failure, runtime
        error or watchdog exit, else 0.
    """
    args = parse_arguments()
    status = _run_validation(args)
    if status is not None:
        return status

    setup_logging(args.debug)
    # On-request stack dumps for the process lifetime, independent of
    # debug (issue-1a8f40ea).
    from .utils import stack_dump

    stack_dump.install(lambda: _STACKS_LOG)

    from .app import GTachApplication

    # One location rule: --config, else the ConfigStore default under
    # GTACH_HOME (issue-5fbff586).
    app = GTachApplication(args.config, args.debug, args)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
