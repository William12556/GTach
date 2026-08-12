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

_LOG_FORMAT = '%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'
_LOG_DATE_FMT = '%Y-%m-%d %H:%M:%S'
_START_LOG = '/opt/gtach/start.log'
_DEBUG_LOG = '/opt/gtach/debug.log'
_STACKS_LOG = '/opt/gtach/stacks.log'
# 10 MB is about ninety minutes of debug output at 30 Hz.
# Ten backups gives roughly sixteen hours of history for
# 110 MB of card. bin/gtach.service caps a restart loop at
# three rapid starts (StartLimitBurst), so rotate-at-start
# cannot exhaust the backups (issue-6a3b7c52).
_DEBUG_MAX_BYTES = 10 * 1024 * 1024
_DEBUG_BACKUPS = 10


def setup_logging(debug: bool = False) -> None:
    global _start_handler, _debug_handler, _stacks_file

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

    # stacks.log — periodic all-thread stack dumps, debug only.
    #
    # faulthandler's repeat timer runs in a C thread and never takes
    # the GIL to schedule itself, so its dumps still land while every
    # Python thread is stalled — which is exactly the window that
    # needs observing (issue-2ac1c602). This was previously armed in
    # GTachApplication.__init__ against sys.stderr; under systemd
    # stderr is the journal, not the app-owned log set beside
    # start.log and debug.log, so the dumps were not recoverable
    # alongside the run they belonged to.
    if debug:
        try:
            _stacks_file = open(_STACKS_LOG, mode='a', buffering=1, encoding='utf-8')
            faulthandler.enable(file=_stacks_file)
            faulthandler.dump_traceback_later(15, repeat=True, file=_stacks_file)
        except OSError as e:
            print(f'[gtach] WARNING: could not open {_STACKS_LOG}: {e}', file=sys.stderr)
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
