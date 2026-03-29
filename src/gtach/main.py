#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Main entry point for GTach application.
Handles command-line argument parsing, logging setup, and application lifecycle.
"""

import sys
import argparse
import logging
from .app import GTachApplication
from .utils import ConfigManager


def setup_logging(debug: bool) -> None:
    """Configure logging based on debug flag.
    
    Args:
        debug: If True, enable DEBUG level logging
    """
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
    else:
        # In production, use NullHandler to avoid logging to stderr
        logging.getLogger().__handlers__.clear()
        logging.getLogger().addHandler(logging.NullHandler())


def find_configuration_file() -> str:
    """Find the configuration file location.
    
    Checks in the following order:
    1. GTACH_CONFIG environment variable
    2. ~/.config/gtach/config.yaml
    3. /etc/gtach/config.yaml
    
    Returns:
        Path to configuration file
        
    Raises:
        FileNotFoundError: If no configuration file is found
    """
    import os
    from pathlib import Path
    
    # Check environment variable first
    config_path = os.environ.get('GTACH_CONFIG')
    if config_path and Path(config_path).exists():
        return str(Path(config_path).resolve())
    
    # Check user configuration directory
    user_config = Path.home() / '.config' / 'gtach' / 'config.yaml'
    if user_config.exists():
        return str(user_config.resolve())
    
    # Check system configuration
    system_config = Path('/etc/gtach/config.yaml')
    if system_config.exists():
        return str(system_config.resolve())
    
    raise FileNotFoundError(
        "Configuration file not found. "
        "Please set GTACH_CONFIG environment variable or create a config file at "
        "~/.config/gtach/config.yaml or /etc/gtach/config.yaml"
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='GTach - GPIO-based Tachometer Application',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Core arguments
    parser.add_argument(
        '--config',
        help='Path to configuration file',
        default=None
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version and exit'
    )
    
    # Validation flags
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration file and exit'
    )
    parser.add_argument(
        '--validate-dependencies',
        action='store_true',
        help='Validate system dependencies and exit'
    )
    
    # Platform-specific arguments
    parser.add_argument(
        '--macos',
        action='store_true',
        help='Force macOS platform mode'
    )
    parser.add_argument(
        '--transport',
        choices=['tcp', 'serial', 'rfcomm'],
        default=None,
        help='Force specific transport protocol'
    )
    
    # Transport-specific arguments
    parser.add_argument(
        '--obd-host',
        default='localhost',
        help='OBD adapter host address'
    )
    parser.add_argument(
        '--obd-port',
        type=int,
        default=35000,
        help='OBD adapter port number'
    )
    parser.add_argument(
        '--serial-port',
        help='Serial port device path'
    )
    
    return parser.parse_args()


def validate_dependencies() -> bool:
    """Validate system dependencies.
    
    Returns:
        True if all dependencies are satisfied
    """
    import sys
    from packaging import version
    
    try:
        import serial
        if version.parse(serial.__version__) < version.parse('3.5'):
            print(f"WARNING: pyserial version {serial.__version__} < 3.5 recommended", file=sys.stderr)
            return False
        
        # Check for platform-specific dependencies
        import platform
        if platform.system() == 'Linux' and platform.machine() in ['armv7l', 'aarch64']:
            try:
                import RPi.GPIO
            except ImportError:
                print("WARNING: RPi.GPIO not found on Raspberry Pi", file=sys.stderr)
                return False
        
        return True
        
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Dependency validation error: {e}", file=sys.stderr)
        return False


def validate_config(config_path: str) -> bool:
    """Validate configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if configuration is valid
    """
    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        # Basic validation - ensure required sections exist
        if not isinstance(config, dict):
            print("ERROR: Configuration must be a YAML mapping", file=sys.stderr)
            return False
        
        return True
        
    except Exception as e:
        print(f"Configuration validation error: {e}", file=sys.stderr)
        return False


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code: 0 for success, non-zero for errors
    """
    args = parse_arguments()
    
    # Show version and exit if requested
    if args.version:
        import importlib.metadata
        try:
            version = importlib.metadata.version('gtach')
            print(f"GTach version {version}")
        except Exception:
            print("GTach version 0.2.0")
        return 0
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Validate dependencies if requested
    if args.validate_dependencies:
        if validate_dependencies():
            print("All dependencies validated successfully")
            return 0
        else:
            return 1
    
    # Find and validate configuration file
    try:
        config_file = args.config if args.config else find_configuration_file()
        if args.validate_config:
            if validate_config(config_file):
                print("Configuration validated successfully")
                return 0
            else:
                return 1
        
        # Create and run application
        logger.info(f"Starting GTach with config: {config_file}")
        app = GTachApplication(config_file, args.debug, args)
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())