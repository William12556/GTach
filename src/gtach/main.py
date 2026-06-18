#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""GTach application entry point."""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

# Module-level handler references for runtime manipulation.
_start_handler: logging.Handler = None
_debug_handler: logging.Handler = None

_LOG_FORMAT = '%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'
_LOG_DATE_FMT = '%Y-%m-%d %H:%M:%S'
_START_LOG = '/opt/gtach/start.log'
_DEBUG_LOG = '/opt/gtach/debug.log'
_DEBUG_MAX_BYTES = 100 * 1024 * 1024  # 100 MB


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

    # debug.log — truncated at boot; suppressed unless toggled on.
    try:
        _debug_handler = RotatingFileHandler(
            _DEBUG_LOG, mode='w', maxBytes=_DEBUG_MAX_BYTES,
            backupCount=0, encoding='utf-8'
        )
        _debug_handler.setLevel(logging.CRITICAL + 1)  # suppressed
        _debug_handler.setFormatter(formatter)
        root.addHandler(_debug_handler)
    except OSError as e:
        print(f'[gtach] WARNING: could not open {_DEBUG_LOG}: {e}', file=sys.stderr)

    if debug and _debug_handler is not None:
        _debug_handler.setLevel(logging.DEBUG)


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
    parser.add_argument('--transport', choices=['tcp', 'serial', 'rfcomm', 'simtcp', 'simbt'], default=None)
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
