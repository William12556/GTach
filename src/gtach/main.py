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


def setup_logging(debug: bool = False) -> None:
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        logging.getLogger().addHandler(logging.NullHandler())


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='GTach — real-time engine tachometer')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--version', action='version', version='GTach 0.2.0')
    parser.add_argument('--validate-config', action='store_true')
    parser.add_argument('--validate-dependencies', action='store_true')
    parser.add_argument('--macos', action='store_true')
    parser.add_argument('--transport', choices=['tcp', 'serial', 'rfcomm'], default=None)
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
