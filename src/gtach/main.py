#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
OBDII RPM Display - Unified Application Entry Point

Author: William Watson
Created: 2025-07-02

This module provides the single, unified entry point for the OBDII RPM Display application.
It handles configuration hierarchy, argument parsing, and application initialization.
"""

import sys
import os
import logging
import argparse
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import dependency validator
from .utils import validate_dependencies


def setup_configuration_paths() -> dict:
    """
    Establish standardized configuration hierarchy.
    
    Returns:
        dict: Configuration paths in order of precedence
    """
    config_paths = {
        'user_config': Path.home() / '.config' / 'obdii' / 'config.yaml',
        'system_config': Path('/etc/obdii/config.yaml'),
        'env_config': os.getenv('OBDII_CONFIG'),
        'logging_config': os.getenv('OBDII_LOGGING', '/etc/obdii/logging.yaml')
    }
    
    return config_paths


def find_configuration_file() -> Optional[Path]:
    """
    Find configuration file using standardized hierarchy.
    
    Returns:
        Path to configuration file or None if not found
    """
    config_paths = setup_configuration_paths()
    
    # 1. Environment variable (highest precedence)
    if config_paths['env_config'] and Path(config_paths['env_config']).exists():
        return Path(config_paths['env_config'])
    
    # 2. User configuration
    if config_paths['user_config'].exists():
        return config_paths['user_config']
    
    # 3. System configuration
    if config_paths['system_config'].exists():
        return config_paths['system_config']
    
    # 4. Default fallback (built-in defaults will be used)
    return None


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for unified runtime interface.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='OBDII RPM Display - Real-time engine monitoring',
        prog='obdii'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file (overrides hierarchy)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--service',
        action='store_true',
        help='Run in service mode (daemon)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='OBDII RPM Display 1.0.0'
    )
    
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    parser.add_argument(
        '--test-hardware',
        action='store_true',
        help='Test hardware connections and exit'
    )
    
    parser.add_argument(
        '--validate-logging',
        action='store_true',
        help='Validate logging system and exit'
    )
    
    parser.add_argument(
        '--logging-health-check',
        action='store_true',
        help='Perform comprehensive logging health check and exit'
    )
    
    parser.add_argument(
        '--validate-dependencies',
        action='store_true',
        help='Validate all dependencies and exit'
    )
    
    return parser.parse_args()


# Global lock for thread-safe logging initialization
_logging_lock = threading.Lock()
_logging_initialized = False
_logging_health_status = {"status": "unknown", "errors": [], "warnings": []}


def validate_logging_configuration() -> Dict[str, Any]:
    """
    Validate logging system configuration and return health status.
    
    Returns:
        dict: Comprehensive logging system health report
    """
    validation_result = {
        "status": "healthy",
        "errors": [],
        "warnings": [],
        "checks": {},
        "timestamp": time.time()
    }
    
    try:
        # Check 1: Verify logging module is properly imported
        try:
            import logging as test_logging
            validation_result["checks"]["logging_module"] = "✅ Available"
        except ImportError as e:
            validation_result["errors"].append(f"Logging module import failed: {e}")
            validation_result["checks"]["logging_module"] = "❌ Failed"
            validation_result["status"] = "critical"
        
        # Check 2: Test basic logger creation
        try:
            test_logger = logging.getLogger("validation_test")
            validation_result["checks"]["logger_creation"] = "✅ Working"
        except Exception as e:
            validation_result["errors"].append(f"Logger creation failed: {e}")
            validation_result["checks"]["logger_creation"] = "❌ Failed"
            validation_result["status"] = "critical"
        
        # Check 3: Verify handler functionality
        try:
            # Test stream handler
            stream_handler = logging.StreamHandler()
            validation_result["checks"]["stream_handler"] = "✅ Available"
            
            # Test null handler (always available)
            null_handler = logging.NullHandler()
            validation_result["checks"]["null_handler"] = "✅ Available"
        except Exception as e:
            validation_result["errors"].append(f"Handler creation failed: {e}")
            validation_result["checks"]["handlers"] = "❌ Failed"
            validation_result["status"] = "degraded"
        
        # Check 4: Test log directory permissions
        log_locations = []
        
        # System log directory
        system_log_dir = Path('/var/log/obdii')
        if system_log_dir.exists():
            if os.access(system_log_dir, os.W_OK):
                log_locations.append(f"✅ System: {system_log_dir} (writable)")
                validation_result["checks"]["system_log_dir"] = "✅ Writable"
            else:
                log_locations.append(f"⚠️  System: {system_log_dir} (read-only)")
                validation_result["checks"]["system_log_dir"] = "⚠️  Read-only"
                validation_result["warnings"].append("System log directory is not writable")
        else:
            validation_result["checks"]["system_log_dir"] = "❌ Not found"
        
        # User log directory
        user_log_dir = Path.home() / '.local' / 'share' / 'obdii' / 'logs'
        try:
            user_log_dir.mkdir(parents=True, exist_ok=True)
            test_file = user_log_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
            log_locations.append(f"✅ User: {user_log_dir} (writable)")
            validation_result["checks"]["user_log_dir"] = "✅ Writable"
        except (OSError, PermissionError) as e:
            log_locations.append(f"❌ User: {user_log_dir} (failed: {e})")
            validation_result["checks"]["user_log_dir"] = "❌ Failed"
            validation_result["warnings"].append(f"User log directory not accessible: {e}")
        
        validation_result["log_locations"] = log_locations
        
        # Check 5: Test formatter functionality
        try:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            test_record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="test message", args=(), exc_info=None
            )
            formatted = formatter.format(test_record)
            validation_result["checks"]["formatter"] = "✅ Working"
        except Exception as e:
            validation_result["errors"].append(f"Formatter test failed: {e}")
            validation_result["checks"]["formatter"] = "❌ Failed"
            validation_result["status"] = "degraded"
        
        # Check 6: Test YAML configuration support
        try:
            import yaml
            validation_result["checks"]["yaml_support"] = "✅ Available"
        except ImportError:
            validation_result["checks"]["yaml_support"] = "❌ Not available"
            validation_result["warnings"].append("YAML support not available - will use basic configuration")
        
        # Determine overall status
        if validation_result["errors"]:
            if any("critical" in str(error).lower() for error in validation_result["errors"]):
                validation_result["status"] = "critical"
            else:
                validation_result["status"] = "degraded"
        elif validation_result["warnings"]:
            validation_result["status"] = "degraded"
        
    except Exception as e:
        validation_result["status"] = "critical"
        validation_result["errors"].append(f"Validation process failed: {e}")
    
    return validation_result


def test_logging_functionality() -> bool:
    """
    Test actual logging functionality with different levels and handlers.
    
    Returns:
        bool: True if logging system is functional
    """
    try:
        # Create a test logger
        test_logger = logging.getLogger("logging_functionality_test")
        
        # Test different log levels
        test_logger.debug("Debug level test message")
        test_logger.info("Info level test message")
        test_logger.warning("Warning level test message")
        test_logger.error("Error level test message")
        
        # Test exception logging
        try:
            raise ValueError("Test exception for logging")
        except ValueError:
            test_logger.exception("Exception logging test")
        
        return True
    except Exception as e:
        print(f"ERROR: Logging functionality test failed: {e}")
        return False


def perform_logging_health_check() -> Dict[str, Any]:
    """
    Perform comprehensive logging system health check.
    
    Returns:
        dict: Detailed health check results
    """
    print("🔍 Performing logging system health check...")
    
    health_check = {
        "timestamp": time.time(),
        "validation": None,
        "functionality_test": False,
        "thread_safety_test": False,
        "overall_status": "unknown"
    }
    
    # Run validation
    health_check["validation"] = validate_logging_configuration()
    
    # Test functionality
    health_check["functionality_test"] = test_logging_functionality()
    
    # Test thread safety
    health_check["thread_safety_test"] = test_logging_thread_safety()
    
    # Determine overall status
    if health_check["validation"]["status"] == "critical":
        health_check["overall_status"] = "critical"
    elif not health_check["functionality_test"]:
        health_check["overall_status"] = "degraded"
    elif not health_check["thread_safety_test"]:
        health_check["overall_status"] = "degraded"
    elif health_check["validation"]["status"] == "degraded":
        health_check["overall_status"] = "degraded"
    else:
        health_check["overall_status"] = "healthy"
    
    return health_check


def test_logging_thread_safety() -> bool:
    """
    Test logging system thread safety.
    
    Returns:
        bool: True if thread safety test passes
    """
    try:
        results = []
        test_logger = logging.getLogger("thread_safety_test")
        
        def log_worker(worker_id: int):
            """Worker function for thread safety testing"""
            try:
                for i in range(10):
                    test_logger.info(f"Worker {worker_id} - Message {i}")
                    time.sleep(0.01)  # Small delay
                results.append(f"worker_{worker_id}_success")
            except Exception as e:
                results.append(f"worker_{worker_id}_failed_{e}")
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Check results
        success_count = sum(1 for result in results if "success" in result)
        return success_count == 3
        
    except Exception as e:
        print(f"ERROR: Thread safety test failed: {e}")
        return False


def create_logging_fallback_handler() -> logging.Handler:
    """
    Create a robust fallback logging handler that always works.
    
    Returns:
        logging.Handler: Fallback handler for emergency logging
    """
    try:
        # Try to create a stream handler first
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            '[FALLBACK] %(asctime)s - %(levelname)s - %(message)s'
        ))
        return handler
    except Exception:
        # If even that fails, create a null handler
        return logging.NullHandler()


def setup_logging_with_validation(debug: bool = False, config_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Setup logging with debug-conditional validation to optimize performance.
    
    Production mode: Simple, fast logging setup with minimal overhead
    Debug mode: Comprehensive validation and fallback mechanisms
    
    Args:
        debug: Enable debug level logging and comprehensive validation
        config_file: Optional logging configuration file
        
    Returns:
        dict: Setup results and validation status
    """
    global _logging_initialized, _logging_health_status
    
    setup_result = {
        "success": False,
        "method": "unknown",
        "validation": None,
        "warnings": [],
        "errors": []
    }
    
    # Thread-safe initialization
    with _logging_lock:
        if _logging_initialized:
            setup_result["success"] = True
            setup_result["method"] = "already_initialized"
            setup_result["validation"] = _logging_health_status
            return setup_result
        
        try:
            if debug:
                # Debug mode: Comprehensive validation and testing
                setup_result["validation"] = validate_logging_configuration()
                
                if setup_result["validation"]["status"] == "critical":
                    setup_result["errors"].append("Critical logging system issues detected")
                    # Set up emergency fallback
                    fallback_handler = create_logging_fallback_handler()
                    logging.getLogger().addHandler(fallback_handler)
                    logging.getLogger().setLevel(logging.ERROR)
                    setup_result["method"] = "emergency_fallback"
                    setup_result["success"] = True
                    return setup_result
                
                # Call setup_logging function
                setup_logging(debug, config_file)
                setup_result["method"] = "debug_validated_setup"
                
                # Validate the setup worked in debug mode
                if test_logging_functionality():
                    setup_result["success"] = True
                    _logging_initialized = True
                    _logging_health_status = setup_result["validation"]
                else:
                    setup_result["errors"].append("Logging functionality test failed after setup")
                    # Set up fallback
                    fallback_handler = create_logging_fallback_handler()
                    logging.getLogger().addHandler(fallback_handler)
                    setup_result["method"] = "fallback_after_failure"
                    setup_result["success"] = True
            else:
                # Production mode: Fast, minimal setup without extensive validation
                setup_logging(debug, config_file)
                setup_result["method"] = "production_optimized"
                setup_result["success"] = True
                _logging_initialized = True
                # Minimal validation result for production
                setup_result["validation"] = {"status": "production_mode", "checks": {}, "warnings": [], "errors": []}
                _logging_health_status = setup_result["validation"]
                
        except Exception as e:
            setup_result["errors"].append(f"Setup failed: {e}")
            # Emergency fallback for both modes
            try:
                fallback_handler = create_logging_fallback_handler()
                logging.getLogger().addHandler(fallback_handler)
                logging.getLogger().setLevel(logging.WARNING if debug else logging.INFO)
                setup_result["method"] = "emergency_fallback"
                setup_result["success"] = True
            except Exception as fallback_error:
                setup_result["errors"].append(f"Even fallback failed: {fallback_error}")
                setup_result["success"] = False
    
    return setup_result


def print_logging_validation_report(validation_result: Dict[str, Any]) -> None:
    """
    Print a comprehensive logging validation report.
    
    Args:
        validation_result: Result from validate_logging_configuration()
    """
    print("\n" + "="*60)
    print("🔍 LOGGING SYSTEM VALIDATION REPORT")
    print("="*60)
    
    # Overall status
    status_emoji = {
        "healthy": "✅",
        "degraded": "⚠️ ",
        "critical": "❌",
        "production_mode": "🚀",
        "unknown": "❓"
    }
    
    status = validation_result.get("status", "unknown")
    print(f"Overall Status: {status_emoji.get(status, '❓')} {status.upper()}")
    print()
    
    # Individual checks
    print("📋 System Checks:")
    checks = validation_result.get("checks", {})
    for check_name, check_result in checks.items():
        print(f"  {check_name.replace('_', ' ').title()}: {check_result}")
    print()
    
    # Log locations
    if "log_locations" in validation_result:
        print("📁 Log File Locations:")
        for location in validation_result["log_locations"]:
            print(f"  {location}")
        print()
    
    # Warnings
    warnings = validation_result.get("warnings", [])
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
        print()
    
    # Errors
    errors = validation_result.get("errors", [])
    if errors:
        print("❌ Errors:")
        for error in errors:
            print(f"  • {error}")
        print()
    
    # Recommendations
    print("💡 Recommendations:")
    if status == "critical":
        print("  • Logging system has critical issues - using emergency fallback")
        print("  • Check system permissions and Python logging module installation")
    elif status == "degraded":
        print("  • Some logging features are limited but system is functional")
        print("  • Consider installing missing dependencies (e.g., PyYAML)")
    elif status == "production_mode":
        print("  • Running in optimized production mode - minimal logging overhead")
        print("  • Use --debug flag for comprehensive logging validation and debugging")
    else:
        print("  • Logging system is healthy and fully functional")
    
    print("="*60)


def setup_logging(debug: bool = False, config_file: Optional[Path] = None) -> None:
    """
    Configure logging using ConfigManager's session-based approach.
    
    Args:
        debug: Enable debug level logging
        config_file: Optional logging configuration file
    """
    # Debug trace to help diagnose issues
    debug_mode = debug or os.getenv('OBDII_DEBUG_LOGGING', '').lower() == 'true'
    
    if debug_mode:
        print(f"DEBUG: setup_logging called with debug={debug}, config_file={config_file}")
        print("DEBUG: Using ConfigManager session-based logging")
    
    try:
        # Use ConfigManager's session-based logging which handles session ID substitution properly
        from .utils.config import ConfigManager
        
        # Create ConfigManager instance with config file if provided
        if config_file:
            config_manager = ConfigManager(str(config_file))
        else:
            config_manager = ConfigManager()
        
        # Setup session-based logging using ConfigManager
        config_manager.setup_logging(debug=debug)
        
        if debug_mode:
            print("DEBUG: ConfigManager session-based logging configuration completed successfully")
            print(f"DEBUG: Session ID: {config_manager.get_session_id()}")
            if hasattr(config_manager, '_session_log_dir') and config_manager._session_log_dir:
                print(f"DEBUG: Log directory: {config_manager._session_log_dir}")
        return
        
    except Exception as e:
        error_msg = f"Warning: Failed to setup ConfigManager logging: {e}"
        print(error_msg)
        if debug_mode:
            print(f"DEBUG: {error_msg}")
            import traceback
            traceback.print_exc()
    
    if debug_mode:
        print("DEBUG: Using fallback basic logging configuration")
    
    # Fallback to basic logging configuration 
    # This should only be used if ConfigManager completely fails
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Try to create a basic log directory
    try:
        from .utils.home import get_home_path
        log_dir = get_home_path() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / 'obdii_fallback.log'
    except:
        # Ultimate fallback - no file logging
        log_dir = None
        log_file_path = None
    
    # Build handlers list
    log_handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file_path:
        try:
            log_handlers.append(logging.FileHandler(str(log_file_path)))
            if debug_mode:
                print(f"DEBUG: Fallback logging to: {log_file_path}")
        except (OSError, PermissionError) as e:
            if debug_mode:
                print(f"DEBUG: Cannot write to fallback log file {log_file_path}: {e}")
            # Add null handler as fallback
            log_handlers.append(logging.NullHandler())
    
    # Use the global logging module explicitly for basicConfig
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=log_handlers,
        force=True  # Force reconfiguration if already configured
    )
    
    if debug_mode:
        print(f"DEBUG: Basic fallback logging configuration completed with level {log_level}")
        if log_file_path:
            print(f"DEBUG: Fallback log file: {log_file_path}")
        else:
            print(f"DEBUG: Console-only logging (no file logging available)")


def validate_configuration(config_path: Optional[Path]) -> bool:
    """
    Validate configuration file and report issues.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if configuration is valid
    """
    try:
        from .utils.config import ConfigManager
        
        config_manager = ConfigManager(config_path)
        config_manager.load_config()
        
        print("✓ Configuration file is valid")
        print(f"✓ Using configuration: {config_path or 'built-in defaults'}")
        return True
        
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False


def test_hardware() -> bool:
    """
    Test hardware connections and report status.
    
    Returns:
        True if hardware tests pass
    """
    print("Testing hardware connections...")
    
    tests = []
    
    # Test framebuffer
    try:
        if os.path.exists('/dev/fb0'):
            print("✓ Framebuffer (/dev/fb0) available")
            tests.append(True)
        else:
            print("✗ Framebuffer (/dev/fb0) not found")
            tests.append(False)
    except Exception:
        print("✗ Failed to test framebuffer")
        tests.append(False)
    
    # Test I2C
    try:
        if os.path.exists('/dev/i2c-1'):
            print("✓ I2C interface (/dev/i2c-1) available")
            tests.append(True)
        else:
            print("✗ I2C interface (/dev/i2c-1) not found")
            tests.append(False)
    except Exception:
        print("✗ Failed to test I2C interface")
        tests.append(False)
    
    # Test Bluetooth
    try:
        import subprocess
        result = subprocess.run(['hciconfig'], capture_output=True, text=True)
        if result.returncode == 0 and 'hci0' in result.stdout:
            print("✓ Bluetooth interface available")
            tests.append(True)
        else:
            print("✗ Bluetooth interface not available")
            tests.append(False)
    except Exception:
        print("✗ Failed to test Bluetooth interface")
        tests.append(False)
    
    # Test Python modules
    required_modules = ['pygame', 'yaml', 'serial']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ Python module '{module}' available")
            tests.append(True)
        except ImportError:
            print(f"✗ Python module '{module}' not available")
            tests.append(False)
    
    success_rate = sum(tests) / len(tests)
    print(f"\nHardware test results: {sum(tests)}/{len(tests)} passed ({success_rate:.1%})")
    
    return success_rate >= 0.8  # 80% success rate required


def main() -> int:
    """
    Unified application entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Determine configuration file
        config_file = None
        if args.config:
            config_file = args.config
        else:
            config_file = find_configuration_file()
        
        # Handle validation modes first (before full logging setup)
        if args.validate_dependencies:
            validator = validate_dependencies(debug=args.debug)
            validator.print_report(show_successful=args.debug)
            return 0 if validator.can_start_application() else 1
        
        if args.validate_logging:
            validation_result = validate_logging_configuration()
            print_logging_validation_report(validation_result)
            return 0 if validation_result["status"] != "critical" else 1
        
        if args.logging_health_check:
            health_check = perform_logging_health_check()
            print_logging_validation_report(health_check["validation"])
            print(f"\n🏥 Health Check Summary:")
            print(f"  Overall Status: {health_check['overall_status'].upper()}")
            print(f"  Functionality Test: {'✅ PASSED' if health_check['functionality_test'] else '❌ FAILED'}")
            print(f"  Thread Safety Test: {'✅ PASSED' if health_check['thread_safety_test'] else '❌ FAILED'}")
            return 0 if health_check["overall_status"] != "critical" else 1
        
        # Setup logging with validation
        setup_result = setup_logging_with_validation(args.debug, config_file)
        
        if not setup_result["success"]:
            print("❌ CRITICAL: Logging system setup failed completely")
            return 1
        
        if setup_result["warnings"] or setup_result["errors"]:
            print(f"⚠️  Logging setup completed with {len(setup_result['warnings'])} warnings and {len(setup_result['errors'])} errors")
            if args.debug:
                for warning in setup_result["warnings"]:
                    print(f"  WARNING: {warning}")
                for error in setup_result["errors"]:
                    print(f"  ERROR: {error}")
        
        # Show validation report in debug mode
        if args.debug and setup_result["validation"]:
            print_logging_validation_report(setup_result["validation"])
        
        logger = logging.getLogger(__name__)
        logger.info("OBDII RPM Display starting...")
        logger.info(f"Configuration: {config_file or 'built-in defaults'}")
        logger.info(f"Logging setup method: {setup_result['method']}")
        
        # Validate dependencies during startup
        logger.info("Validating dependencies...")
        dependency_validator = validate_dependencies(debug=args.debug)
        
        if not dependency_validator.can_start_application():
            logger.error("❌ CRITICAL: Missing required dependencies")
            dependency_validator.print_report(show_successful=False)
            return 1
        
        # Log dependency validation results
        summary = dependency_validator.get_summary()
        logger.info(f"Dependencies validated: {summary['available']}/{summary['total_checked']} available")
        
        if summary['warnings'] > 0:
            logger.warning(f"⚠️  {summary['warnings']} optional dependencies missing (reduced functionality)")
        
        if summary['errors'] > 0:
            logger.error(f"🟡 {summary['errors']} platform-specific dependencies missing")
        
        # Show detailed dependency report in debug mode
        if args.debug:
            dependency_validator.print_report(show_successful=True)
        
        # Handle special modes
        if args.validate_config:
            return 0 if validate_configuration(config_file) else 1
        
        if args.test_hardware:
            return 0 if test_hardware() else 1
        
        # Import and start main application
        try:
            # Try relative import first (when run as a module)
            from .app import GTachApplication
        except ImportError:
            # Fall back to absolute import (when run directly)
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from gtach.app import GTachApplication
        
        # Initialize and run application
        app = GTachApplication(config_file, args.debug)
        
        if args.service:
            logger.info("Running in service mode")
            app.run_as_service()
        else:
            logger.info("Running in interactive mode")
            app.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        return 0
    except Exception as e:
        # Use the global logging module explicitly
        try:
            logger = logging.getLogger(__name__)
            logger.error(f"Application error: {e}", exc_info=True)
        except:
            # Fallback if logging isn't configured yet
            print(f"ERROR: Application error: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
