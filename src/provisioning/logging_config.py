#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Logging Configuration for GTach Provisioning System

Implements Protocol 8 compliant logging with session-based management,
comprehensive exception handling, and cross-platform compatibility.
Extends existing ConfigManager logging capabilities for provisioning operations.

Features:
- Session-based log file management
- Thread-safe logging operations
- Platform-aware log configuration
- Comprehensive exception handling
- Integration with existing ConfigManager
"""

import os
import sys
import logging
import threading
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from contextlib import contextmanager

# Import existing utilities
try:
    from ..obdii.utils.platform import get_platform_type, PlatformType
    from ..obdii.utils.config import ConfigManager
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from obdii.utils.platform import get_platform_type, PlatformType
    from obdii.utils.config import ConfigManager


class ProvisioningLogger:
    """
    Protocol 8 compliant logger for provisioning operations.
    
    Provides session-based logging with comprehensive exception handling
    and thread-safe operations. Integrates with existing ConfigManager
    logging infrastructure while extending for provisioning-specific needs.
    """
    
    _instance = None
    _instance_lock = threading.Lock()
    
    def __new__(cls):
        """Thread-safe singleton implementation"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize provisioning logger with Protocol 8 compliance"""
        if hasattr(self, '_initialized'):
            return
            
        # Base configuration
        self.logger_name = 'provisioning'
        self.logger = logging.getLogger(self.logger_name)
        
        # Thread safety
        self._setup_lock = threading.RLock()
        self._handlers_lock = threading.Lock()
        
        # Session management
        self._session_id = None
        self._session_handlers = {}
        
        # Platform detection
        self.platform = get_platform_type()
        
        # Configuration manager integration
        self.config_manager = ConfigManager()
        
        # Statistics
        self._log_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
        self._stats_lock = threading.Lock()
        
        self._initialized = True
    
    def setup_session_logging(self, 
                            session_id: Optional[str] = None,
                            debug_mode: bool = False,
                            log_dir: Optional[Union[str, Path]] = None) -> str:
        """
        Setup session-based logging per Protocol 8 standards.
        
        Args:
            session_id: Optional session identifier. Auto-generated if None.
            debug_mode: Enable debug-level logging and file output
            log_dir: Optional log directory. Uses ConfigManager default if None.
            
        Returns:
            Session identifier used for logging
        """
        with self._setup_lock:
            # Generate session ID if not provided
            if session_id is None:
                session_id = self._generate_session_id()
                
            self._session_id = session_id
            
            # Determine log directory
            if log_dir is None:
                log_dir = self._get_default_log_dir()
            else:
                log_dir = Path(log_dir)
                
            log_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Setup logging handlers based on mode
                if debug_mode:
                    self._setup_debug_logging(session_id, log_dir)
                else:
                    self._setup_production_logging(session_id)
                
                # Log session initialization
                self.logger.info(f"Provisioning session started: {session_id}")
                self.logger.debug(f"Platform: {self.platform.name}")
                self.logger.debug(f"Log directory: {log_dir}")
                
                return session_id
                
            except Exception as e:
                # Fallback to basic logging
                self._setup_fallback_logging()
                self.logger.error(f"Failed to setup session logging: {e}")
                return session_id
    
    def _generate_session_id(self) -> str:
        """
        Generate unique session identifier with timestamp.
        
        Returns:
            Session identifier string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"provisioning_{timestamp}"
    
    def _get_default_log_dir(self) -> Path:
        """
        Get default log directory using ConfigManager approach.
        
        Returns:
            Log directory path
        """
        # Try system log directory first
        system_log_dir = Path('/var/log/gtach/provisioning')
        try:
            system_log_dir.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = system_log_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
            return system_log_dir
        except (OSError, PermissionError):
            pass
        
        # Fallback to user directory
        try:
            from ..obdii.utils.home import get_home_path
            user_log_dir = get_home_path() / 'logs' / 'provisioning'
            user_log_dir.mkdir(parents=True, exist_ok=True)
            return user_log_dir
        except Exception:
            # Ultimate fallback
            import tempfile
            return Path(tempfile.gettempdir()) / 'gtach_provisioning_logs'
    
    def _setup_debug_logging(self, session_id: str, log_dir: Path) -> None:
        """
        Setup comprehensive debug logging with file output.
        
        Args:
            session_id: Session identifier
            log_dir: Log directory
        """
        with self._handlers_lock:
            # Clear existing handlers
            self.logger.handlers.clear()
            self.logger.setLevel(logging.DEBUG)
            
            # Console handler with debug level
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # File handler for debug logs
            debug_log_path = log_dir / f'{session_id}_debug.log'
            file_handler = logging.FileHandler(str(debug_log_path), mode='w')
            file_handler.setLevel(logging.DEBUG)
            
            # Comprehensive formatter
            formatter = logging.Formatter(
                '%(asctime)s - [%(name)s:%(funcName)s:%(lineno)d] - %(levelname)s - %(message)s'
            )
            
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
            
            # Store handlers for cleanup
            self._session_handlers[session_id] = [console_handler, file_handler]
            
            self.logger.debug(f"Debug logging setup complete: {debug_log_path}")
    
    def _setup_production_logging(self, session_id: str) -> None:
        """
        Setup production logging (console only).
        
        Args:
            session_id: Session identifier
        """
        with self._handlers_lock:
            # Clear existing handlers
            self.logger.handlers.clear()
            self.logger.setLevel(logging.INFO)
            
            # Console handler only
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Simple formatter for production
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
            
            # Store handler for cleanup
            self._session_handlers[session_id] = [console_handler]
    
    def _setup_fallback_logging(self) -> None:
        """Setup emergency fallback logging"""
        try:
            logging.basicConfig(
                level=logging.WARNING,
                format='[PROVISIONING-FALLBACK] %(asctime)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stderr)],
                force=True
            )
        except Exception:
            # If even basicConfig fails, we're in trouble
            pass
    
    def log_operation_start(self, operation: str, **kwargs) -> str:
        """
        Log the start of a provisioning operation.
        
        Args:
            operation: Operation name
            **kwargs: Additional operation parameters
            
        Returns:
            Operation identifier for tracking
        """
        operation_id = f"{operation}_{int(time.time())}"
        
        self.logger.info(f"=== OPERATION START: {operation} ===")
        self.logger.info(f"Operation ID: {operation_id}")
        
        if kwargs:
            for key, value in kwargs.items():
                self.logger.debug(f"  {key}: {value}")
        
        self._increment_log_count('INFO')
        return operation_id
    
    def log_operation_end(self, operation_id: str, success: bool = True, **kwargs) -> None:
        """
        Log the end of a provisioning operation.
        
        Args:
            operation_id: Operation identifier
            success: Whether operation succeeded
            **kwargs: Additional result parameters
        """
        status = "SUCCESS" if success else "FAILED"
        level = logging.INFO if success else logging.ERROR
        
        self.logger.log(level, f"=== OPERATION END: {operation_id} - {status} ===")
        
        if kwargs:
            for key, value in kwargs.items():
                self.logger.debug(f"  {key}: {value}")
        
        self._increment_log_count('INFO' if success else 'ERROR')
    
    def log_exception(self, 
                     exception: Exception, 
                     context: str = "",
                     include_traceback: bool = True) -> None:
        """
        Log exception with comprehensive context per Protocol 8.
        
        Args:
            exception: Exception to log
            context: Additional context information
            include_traceback: Whether to include full traceback
        """
        error_msg = f"Exception in provisioning"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {type(exception).__name__}: {str(exception)}"
        
        self.logger.error(error_msg)
        
        if include_traceback:
            self.logger.debug("Full traceback:")
            tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            for line in tb_lines:
                self.logger.debug(line.rstrip())
        
        # Log system state for debugging
        self._log_system_state()
        
        self._increment_log_count('ERROR')
    
    def _log_system_state(self) -> None:
        """Log current system state for debugging"""
        try:
            import platform
            import psutil
            
            self.logger.debug(f"System: {platform.system()} {platform.release()}")
            self.logger.debug(f"Python: {platform.python_version()}")
            self.logger.debug(f"Memory usage: {psutil.virtual_memory().percent}%")
            
        except ImportError:
            # psutil not available - log basic info
            import platform
            self.logger.debug(f"System: {platform.system()} {platform.release()}")
        except Exception as e:
            self.logger.debug(f"Could not log system state: {e}")
    
    @contextmanager
    def operation_context(self, operation: str, **kwargs):
        """
        Context manager for operation logging.
        
        Args:
            operation: Operation name
            **kwargs: Operation parameters
            
        Yields:
            Operation identifier
        """
        operation_id = self.log_operation_start(operation, **kwargs)
        success = False
        
        try:
            yield operation_id
            success = True
            
        except Exception as e:
            self.log_exception(e, context=operation)
            raise
            
        finally:
            self.log_operation_end(operation_id, success)
    
    def cleanup_session(self, session_id: Optional[str] = None) -> None:
        """
        Clean up session logging resources.
        
        Args:
            session_id: Session to cleanup. Uses current if None.
        """
        if session_id is None:
            session_id = self._session_id
            
        if not session_id:
            return
            
        with self._handlers_lock:
            handlers = self._session_handlers.get(session_id, [])
            
            for handler in handlers:
                try:
                    handler.close()
                    if handler in self.logger.handlers:
                        self.logger.removeHandler(handler)
                except Exception as e:
                    print(f"Warning: Failed to cleanup handler: {e}")
            
            # Remove from tracking
            if session_id in self._session_handlers:
                del self._session_handlers[session_id]
        
        self.logger.debug(f"Session cleanup completed: {session_id}")
    
    def _increment_log_count(self, level: str) -> None:
        """Thread-safe increment of log level count"""
        with self._stats_lock:
            self._log_counts[level] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.
        
        Returns:
            Dictionary with logging statistics
        """
        with self._stats_lock:
            return {
                'session_id': self._session_id,
                'platform': self.platform.name,
                'log_counts': self._log_counts.copy(),
                'active_sessions': len(self._session_handlers),
                'total_logs': sum(self._log_counts.values())
            }
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get logger instance for specific component.
        
        Args:
            name: Optional logger name suffix
            
        Returns:
            Logger instance
        """
        if name:
            full_name = f"{self.logger_name}.{name}"
            return logging.getLogger(full_name)
        return self.logger


# Global instance for convenience
_provisioning_logger = None
_logger_lock = threading.Lock()


def get_provisioning_logger() -> ProvisioningLogger:
    """
    Get global provisioning logger instance.
    
    Returns:
        ProvisioningLogger singleton
    """
    global _provisioning_logger
    
    if _provisioning_logger is None:
        with _logger_lock:
            if _provisioning_logger is None:
                _provisioning_logger = ProvisioningLogger()
    
    return _provisioning_logger


def setup_provisioning_logging(debug_mode: bool = False,
                               log_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Convenience function to setup provisioning logging.
    
    Args:
        debug_mode: Enable debug-level logging
        log_dir: Optional log directory
        
    Returns:
        Session identifier
    """
    logger = get_provisioning_logger()
    return logger.setup_session_logging(debug_mode=debug_mode, log_dir=log_dir)


def cleanup_provisioning_logging(session_id: Optional[str] = None) -> None:
    """
    Cleanup provisioning logging resources.
    
    Args:
        session_id: Optional session to cleanup
    """
    logger = get_provisioning_logger()
    logger.cleanup_session(session_id)