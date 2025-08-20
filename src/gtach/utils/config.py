#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Configuration management for OBDII display application.
Handles settings loading/saving using OBDII_HOME paths.
"""

import os
import sys
import datetime
import configparser
import logging
import threading
import uuid
import time
import weakref
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union, Callable
from pathlib import Path
from contextlib import contextmanager

# Conditional import of yaml
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

# Import the BluetoothDevice class from the comm module
try:
    from ..comm.models import BluetoothDevice
except ImportError:
    # Fall back for direct imports during development or testing
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from comm.models import BluetoothDevice

# Import OBDII_HOME utilities
from .home import get_config_file, get_home_path, ensure_directories


class RWLock:
    """Reader-Writer lock for ConfigManager concurrent access optimization
    
    Allows multiple concurrent readers or single writer access.
    Prevents reader starvation by limiting writer priority.
    """
    
    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._read_ready = threading.Condition(threading.RLock())
        self._write_ready = threading.Condition(threading.RLock())
        self._readers_lock = threading.Lock()
        
    @contextmanager
    def read_lock(self):
        """Acquire read lock - multiple readers allowed concurrently"""
        self._acquire_read()
        try:
            yield
        finally:
            self._release_read()
            
    @contextmanager 
    def write_lock(self):
        """Acquire write lock - exclusive access"""
        self._acquire_write()
        try:
            yield
        finally:
            self._release_write()
            
    def _acquire_read(self):
        """Acquire read access"""
        with self._read_ready:
            while self._writers > 0:
                self._read_ready.wait()
            with self._readers_lock:
                self._readers += 1
                
    def _release_read(self):
        """Release read access"""
        with self._readers_lock:
            self._readers -= 1
            if self._readers == 0:
                with self._write_ready:
                    self._write_ready.notify_all()
                    
    def _acquire_write(self):
        """Acquire write access"""
        with self._write_ready:
            while self._writers > 0 or self._readers > 0:
                self._write_ready.wait()
            self._writers += 1
            
        with self._read_ready:
            while self._readers > 0:
                self._read_ready.wait()
                
    def _release_write(self):
        """Release write access"""
        with self._write_ready:
            self._writers -= 1
            self._write_ready.notify_all()
        with self._read_ready:
            self._read_ready.notify_all()
            
    def get_stats(self) -> Dict[str, int]:
        """Get lock statistics for monitoring"""
        with self._readers_lock:
            return {
                'active_readers': self._readers,
                'active_writers': self._writers
            }


class ConfigTransaction:
    """Context manager for atomic configuration transactions
    
    Provides rollback capability and ensures atomic updates.
    """
    
    def __init__(self, config_manager: 'ConfigManager', config: 'OBDConfig'):
        self.config_manager = config_manager
        self.original_config = self._deep_copy_config(config)
        self.current_config = self._deep_copy_config(config)
        self._committed = False
        
    def __enter__(self) -> 'OBDConfig':
        return self.current_config
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not self._committed:
            # Exception occurred and not committed - rollback is automatic
            # since we haven't saved the changes yet
            pass
        return False  # Don't suppress exceptions
        
    def commit(self) -> bool:
        """Commit transaction changes atomically"""
        if self._committed:
            raise RuntimeError("Transaction already committed")
            
        try:
            success = self.config_manager._atomic_save_config(self.current_config)
            if success:
                self._committed = True
            return success
        except Exception:
            # Rollback by not setting _committed
            raise
            
    def rollback(self):
        """Explicit rollback to original configuration"""
        if self._committed:
            raise RuntimeError("Cannot rollback committed transaction")
        self.current_config = self._deep_copy_config(self.original_config)
        
    def _deep_copy_config(self, config: 'OBDConfig') -> 'OBDConfig':
        """Create deep copy of configuration"""
        return OBDConfig.from_dict(config.to_dict())


class ConfigValidator:
    """Hardware-aware configuration validator
    
    Validates configuration settings against platform capabilities and constraints.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.ConfigValidator')
        self._platform_info = self._detect_platform()
        
    def validate_config(self, config: 'OBDConfig') -> Dict[str, Any]:
        """Validate complete configuration
        
        Returns:
            Dictionary with validation results and any issues found
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'platform_specific': {}
        }
        
        try:
            # Validate bluetooth settings
            self._validate_bluetooth_config(config.bluetooth, validation_result)
            
            # Validate display settings  
            self._validate_display_config(config.display, validation_result)
            
            # Validate OBD settings
            self._validate_obd_config(config, validation_result)
            
            # Platform-specific validation
            self._validate_platform_constraints(config, validation_result)
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation failed: {e}")
            
        return validation_result
        
    def _validate_bluetooth_config(self, bt_config: 'BluetoothConfig', result: Dict[str, Any]):
        """Validate Bluetooth configuration settings"""
        # Validate timeouts are positive
        timeout_fields = ['scan_duration', 'retry_delay', 'timeout', 'bleak_timeout', 
                         'service_discovery_timeout', 'notification_timeout', 'keepalive_interval',
                         'elm327_timeout', 'elm327_init_delay']
        
        for field in timeout_fields:
            value = getattr(bt_config, field)
            if value <= 0:
                result['errors'].append(f"Bluetooth {field} must be positive, got {value}")
                result['valid'] = False
                
        # Validate retry limits
        if bt_config.retry_limit < 0:
            result['errors'].append(f"Bluetooth retry_limit must be non-negative, got {bt_config.retry_limit}")
            result['valid'] = False
            
        if bt_config.elm327_retries < 0:
            result['errors'].append(f"ELM327 retries must be non-negative, got {bt_config.elm327_retries}")
            result['valid'] = False
            
    def _validate_display_config(self, display_config: 'DisplayConfig', result: Dict[str, Any]):
        """Validate display configuration settings"""
        # Validate display mode
        valid_modes = ['DIGITAL', 'GAUGE']
        if display_config.mode not in valid_modes:
            result['errors'].append(f"Invalid display mode '{display_config.mode}', must be one of {valid_modes}")
            result['valid'] = False
            
        # Validate RPM thresholds
        if display_config.rpm_warning <= 0:
            result['errors'].append(f"RPM warning threshold must be positive, got {display_config.rpm_warning}")
            result['valid'] = False
            
        if display_config.rpm_danger <= display_config.rpm_warning:
            result['errors'].append(f"RPM danger threshold ({display_config.rpm_danger}) must be higher than warning ({display_config.rpm_warning})")
            result['valid'] = False
            
        # Validate FPS limit
        if display_config.fps_limit <= 0 or display_config.fps_limit > 120:
            result['warnings'].append(f"FPS limit {display_config.fps_limit} may cause performance issues")
            
        # Validate touch settings
        if display_config.touch_long_press <= 0:
            result['errors'].append(f"Touch long press duration must be positive, got {display_config.touch_long_press}")
            result['valid'] = False
            
    def _validate_obd_config(self, config: 'OBDConfig', result: Dict[str, Any]):
        """Validate OBD connection settings"""
        # Validate timeout
        if config.timeout <= 0:
            result['errors'].append(f"OBD timeout must be positive, got {config.timeout}")
            result['valid'] = False
            
        # Validate reconnect attempts
        if config.reconnect_attempts < 0:
            result['errors'].append(f"OBD reconnection attempts must be non-negative, got {config.reconnect_attempts}")
            result['valid'] = False
            
        # Validate baudrate
        valid_baudrates = [9600, 19200, 38400, 57600, 115200]
        if config.baudrate not in valid_baudrates:
            result['warnings'].append(f"Unusual baudrate {config.baudrate}, typical values are {valid_baudrates}")
            
    def _validate_platform_constraints(self, config: 'OBDConfig', result: Dict[str, Any]):
        """Validate platform-specific constraints"""
        platform_result = {}
        
        if self._platform_info['is_pi']:
            # Raspberry Pi specific validation
            platform_result['pi_validation'] = self._validate_pi_constraints(config)
        elif self._platform_info['is_mac']:
            # macOS specific validation  
            platform_result['mac_validation'] = self._validate_mac_constraints(config)
            
        result['platform_specific'] = platform_result
        
    def _validate_pi_constraints(self, config: 'OBDConfig') -> Dict[str, Any]:
        """Validate Raspberry Pi specific constraints"""
        pi_result = {'checks': [], 'recommendations': []}
        
        # Check FPS limits for Pi performance
        if config.display.fps_limit > 30:
            pi_result['recommendations'].append(f"Consider reducing FPS limit from {config.display.fps_limit} to 30 or lower for better Pi performance")
            
        # Check Bluetooth timeout settings for Pi
        if config.bluetooth.bleak_timeout < 5.0:
            pi_result['recommendations'].append(f"Consider increasing Bluetooth timeout from {config.bluetooth.bleak_timeout}s to 5s+ on Pi")
            
        # Check for GPIO/I2C availability
        if Path('/sys/class/gpio').exists():
            pi_result['checks'].append('GPIO interface available')
        else:
            pi_result['checks'].append('GPIO interface not found')
            
        return pi_result
        
    def _validate_mac_constraints(self, config: 'OBDConfig') -> Dict[str, Any]:
        """Validate macOS specific constraints"""
        mac_result = {'checks': [], 'recommendations': []}
        
        # macOS can handle higher performance settings
        if config.display.fps_limit < 60:
            mac_result['recommendations'].append(f"macOS can handle higher FPS (current: {config.display.fps_limit})")
            
        return mac_result
        
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect platform information for validation"""
        import platform
        
        system = platform.system()
        machine = platform.machine()
        
        return {
            'system': system,
            'machine': machine,
            'is_pi': system == 'Linux' and machine.startswith(('arm', 'aarch')),
            'is_mac': system == 'Darwin',
            'is_arm': machine.startswith(('arm', 'aarch')),
        }


@dataclass
class BluetoothConfig:
    """Bluetooth-specific configuration settings (Bleak-optimized)"""
    saved_devices: List[BluetoothDevice] = field(default_factory=list)
    auto_connect: bool = True
    last_device: Optional[str] = None  # MAC address of last device
    
    # Core connection settings
    scan_duration: float = 8.0  # Seconds to scan for devices (Bleak-optimized)
    retry_limit: int = 3  # Max reconnection attempts
    retry_delay: float = 3.0  # Seconds between retry attempts
    timeout: float = 2.0  # Connection timeout in seconds
    
    # Bleak-specific settings
    bleak_timeout: float = 10.0  # Bleak operation timeout
    service_discovery_timeout: float = 5.0  # Service discovery timeout
    notification_timeout: float = 1.0  # Notification response timeout
    keepalive_interval: float = 5.0  # Keepalive check interval
    
    # Device filtering
    device_filter: List[str] = field(default_factory=lambda: ["OBD", "ELM", "OBDII"])
    
    # ELM327 specific settings  
    elm327_timeout: float = 2.5  # ELM327 command timeout
    elm327_retries: int = 2  # ELM327 command retries
    elm327_init_delay: float = 1.0  # Delay after connection before initialization

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "saved_devices": [device.to_dict() for device in self.saved_devices],
            "auto_connect": self.auto_connect,
            "last_device": self.last_device,
            "scan_duration": self.scan_duration,
            "retry_limit": self.retry_limit,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "bleak_timeout": self.bleak_timeout,
            "service_discovery_timeout": self.service_discovery_timeout,
            "notification_timeout": self.notification_timeout,
            "keepalive_interval": self.keepalive_interval,
            "device_filter": self.device_filter,
            "elm327_timeout": self.elm327_timeout,
            "elm327_retries": self.elm327_retries,
            "elm327_init_delay": self.elm327_init_delay
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BluetoothConfig':
        """Create instance from dictionary"""
        if not data:
            return cls()
            
        # Extract and convert the saved devices
        saved_devices = []
        for device_data in data.get("saved_devices", []):
            if isinstance(device_data, dict):
                saved_devices.append(BluetoothDevice.from_dict(device_data))
                
        return cls(
            saved_devices=saved_devices,
            auto_connect=data.get("auto_connect", True),
            last_device=data.get("last_device"),
            scan_duration=data.get("scan_duration", 8.0),
            retry_limit=data.get("retry_limit", 3),
            retry_delay=data.get("retry_delay", 3.0),
            timeout=data.get("timeout", 2.0),
            bleak_timeout=data.get("bleak_timeout", 10.0),
            service_discovery_timeout=data.get("service_discovery_timeout", 5.0),
            notification_timeout=data.get("notification_timeout", 1.0),
            keepalive_interval=data.get("keepalive_interval", 5.0),
            device_filter=data.get("device_filter", ["OBD", "ELM", "OBDII"]),
            elm327_timeout=data.get("elm327_timeout", 2.5),
            elm327_retries=data.get("elm327_retries", 2),
            elm327_init_delay=data.get("elm327_init_delay", 1.0)
        )


@dataclass
class SplashConfig:
    """Splash screen configuration settings"""
    enabled: bool = True  # Enable/disable splash screen
    duration: float = 4.0  # Splash duration in seconds
    graphics_mode: str = "automotive"  # Graphics mode: 'automotive', 'minimal', 'text_only'
    animation_speed: float = 1.0  # Animation speed multiplier

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "enabled": self.enabled,
            "duration": self.duration,
            "graphics_mode": self.graphics_mode,
            "animation_speed": self.animation_speed
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplashConfig':
        """Create instance from dictionary"""
        if not data:
            return cls()
        
        # Validate graphics_mode
        valid_modes = ["automotive", "minimal", "text_only"]
        graphics_mode = data.get("graphics_mode", "automotive")
        if graphics_mode not in valid_modes:
            graphics_mode = "automotive"
        
        # Validate duration (must be positive)
        duration = data.get("duration", 4.0)
        if duration <= 0:
            duration = 4.0
        
        # Validate animation_speed (must be positive)
        animation_speed = data.get("animation_speed", 1.0)
        if animation_speed <= 0:
            animation_speed = 1.0
            
        return cls(
            enabled=data.get("enabled", True),
            duration=duration,
            graphics_mode=graphics_mode,
            animation_speed=animation_speed
        )


@dataclass
class DisplayConfig:
    """Display-specific configuration settings"""
    mode: str = "DIGITAL"  # DIGITAL or GAUGE
    rpm_warning: int = 6500
    rpm_danger: int = 7000
    fps_limit: int = 60
    touch_long_press: float = 1.0  # seconds
    splash: SplashConfig = field(default_factory=SplashConfig)  # Splash screen settings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "mode": self.mode,
            "rpm_warning": self.rpm_warning,
            "rpm_danger": self.rpm_danger,
            "fps_limit": self.fps_limit,
            "touch_long_press": self.touch_long_press,
            "splash": self.splash.to_dict()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DisplayConfig':
        """Create instance from dictionary"""
        if not data:
            return cls()
        
        # Extract splash configuration
        splash_config = SplashConfig.from_dict(data.get("splash", {}))
            
        return cls(
            mode=data.get("mode", "DIGITAL"),
            rpm_warning=data.get("rpm_warning", 6500),
            rpm_danger=data.get("rpm_danger", 7000),
            fps_limit=data.get("fps_limit", 60),
            touch_long_press=data.get("touch_long_press", 1.0),
            splash=splash_config
        )


@dataclass
class SessionConfig:
    """Session management configuration settings"""
    retention_days: int = 7  # Days to keep session logs
    enable_archival: bool = False  # Enable archiving old sessions
    max_archived_sessions: int = 20  # Maximum number of archived sessions
    archive_compression: bool = True  # Compress archived sessions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "retention_days": self.retention_days,
            "enable_archival": self.enable_archival,
            "max_archived_sessions": self.max_archived_sessions,
            "archive_compression": self.archive_compression
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """Create instance from dictionary"""
        if not data:
            return cls()
        
        return cls(
            retention_days=data.get("retention_days", 7),
            enable_archival=data.get("enable_archival", False),
            max_archived_sessions=data.get("max_archived_sessions", 20),
            archive_compression=data.get("archive_compression", True)
        )


@dataclass
class OBDConfig:
    """Complete application configuration settings"""
    # OBD connection settings
    port: str = "AUTO"  
    baudrate: int = 38400
    timeout: float = 1.0
    reconnect_attempts: int = 3
    fast_mode: bool = True
    
    # Component configurations
    bluetooth: BluetoothConfig = field(default_factory=BluetoothConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    
    # General application settings
    debug_logging: bool = False
    data_log_enabled: bool = False
    data_log_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "timeout": self.timeout,
            "reconnect_attempts": self.reconnect_attempts,
            "fast_mode": self.fast_mode,
            "bluetooth": self.bluetooth.to_dict(),
            "display": self.display.to_dict(),
            "session": self.session.to_dict(),
            "debug_logging": self.debug_logging,
            "data_log_enabled": self.data_log_enabled,
            "data_log_path": self.data_log_path
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OBDConfig':
        """Create instance from dictionary"""
        if not data:
            return cls()
            
        # Extract component configurations
        bluetooth_config = BluetoothConfig.from_dict(data.get("bluetooth", {}))
        display_config = DisplayConfig.from_dict(data.get("display", {}))
        session_config = SessionConfig.from_dict(data.get("session", {}))
        
        return cls(
            port=data.get("port", "AUTO"),
            baudrate=data.get("baudrate", 38400),
            timeout=data.get("timeout", 1.0),
            reconnect_attempts=data.get("reconnect_attempts", 3),
            fast_mode=data.get("fast_mode", True),
            bluetooth=bluetooth_config,
            display=display_config,
            session=session_config,
            debug_logging=data.get("debug_logging", False),
            data_log_enabled=data.get("data_log_enabled", False),
            data_log_path=data.get("data_log_path")
        )


class SessionManager:
    """Manages session-based logging operations including cleanup and archival"""
    
    def __init__(self, log_dir: Path, session_config: SessionConfig = None):
        """Initialize session manager
        
        Args:
            log_dir: Directory containing session log files
            session_config: Session management configuration
        """
        self.log_dir = Path(log_dir)
        self.session_config = session_config or SessionConfig()
        self.archive_dir = self.log_dir / 'archived_sessions'
        
        # Session metadata tracking
        self._session_metadata = {}
        
    def get_session_log_pattern(self, session_id: str) -> List[str]:
        """Get list of log file patterns for a session.
        
        Supports both new single file pattern (debug-conditional) and legacy multi-file patterns
        for backward compatibility with existing session cleanup.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of log file patterns for the session
        """
        # New debug-conditional single file pattern (primary)
        patterns = [f"obdii_debug_{session_id}.log"]
        
        # Legacy multi-file patterns for backward compatibility
        legacy_patterns = [
            f"obdii_{session_id}.log",
            f"error_{session_id}.log",
            f"debug_{session_id}.log"
        ]
        
        patterns.extend(legacy_patterns)
        return patterns
    
    def list_session_logs(self) -> Dict[str, List[Path]]:
        """List all session log files grouped by session ID.
        
        Handles both new single file pattern (obdii_debug_{session_id}.log) and legacy 
        multi-file patterns for comprehensive session management.
        
        Returns:
            Dictionary mapping session IDs to their log files
        """
        session_files = {}
        
        if not self.log_dir.exists():
            return session_files
        
        try:
            for log_file in self.log_dir.glob("*_*.log"):
                session_id = None
                filename = log_file.stem
                
                # Handle new single file pattern: obdii_debug_{session_id}.log
                if filename.startswith('obdii_debug_'):
                    # Extract session ID from obdii_debug_YYYYMMDD_HHMMSS.log
                    session_part = filename[12:]  # Remove 'obdii_debug_' prefix
                    if '_' in session_part and len(session_part.split('_')) == 2:
                        session_id = session_part
                
                # Handle legacy patterns: prefix_{session_id}.log
                else:
                    parts = filename.split('_')
                    if len(parts) >= 3:  # prefix_YYYYMMDD_HHMMSS
                        session_id = '_'.join(parts[-2:])  # YYYYMMDD_HHMMSS
                
                # Group files by session ID
                if session_id:
                    if session_id not in session_files:
                        session_files[session_id] = []
                    session_files[session_id].append(log_file)
                        
        except Exception as e:
            print(f"Warning: Error listing session logs: {e}")
        
        return session_files
    
    def get_session_age_days(self, session_id: str) -> float:
        """Get the age of a session in days
        
        Args:
            session_id: Session identifier in format YYYYMMDD_HHMMSS
            
        Returns:
            Age of session in days, or -1 if invalid format
        """
        try:
            from datetime import datetime
            session_datetime = datetime.strptime(session_id, "%Y%m%d_%H%M%S")
            age = datetime.now() - session_datetime
            return age.total_seconds() / (24 * 3600)  # Convert to days
        except ValueError:
            return -1  # Invalid session ID format
    
    def cleanup_old_sessions(self) -> Dict[str, Any]:
        """Clean up old session logs based on retention policy
        
        Returns:
            Dictionary with cleanup results
        """
        results = {
            "sessions_processed": 0,
            "sessions_removed": 0,
            "sessions_archived": 0,
            "files_removed": 0,
            "errors": []
        }
        
        try:
            session_files = self.list_session_logs()
            
            for session_id, files in session_files.items():
                results["sessions_processed"] += 1
                age_days = self.get_session_age_days(session_id)
                
                if age_days < 0:
                    results["errors"].append(f"Invalid session ID format: {session_id}")
                    continue
                
                if age_days > self.session_config.retention_days:
                    # Session is older than retention policy
                    if self.session_config.enable_archival:
                        # Archive the session
                        archived = self._archive_session(session_id, files)
                        if archived:
                            results["sessions_archived"] += 1
                        else:
                            results["errors"].append(f"Failed to archive session: {session_id}")
                    else:
                        # Remove the session
                        removed_count = self._remove_session_files(files)
                        if removed_count > 0:
                            results["sessions_removed"] += 1
                            results["files_removed"] += removed_count
                        else:
                            results["errors"].append(f"Failed to remove session: {session_id}")
                            
        except Exception as e:
            results["errors"].append(f"Cleanup operation failed: {e}")
        
        return results
    
    def _remove_session_files(self, files: List[Path]) -> int:
        """Remove session log files
        
        Args:
            files: List of log files to remove
            
        Returns:
            Number of files successfully removed
        """
        removed_count = 0
        for log_file in files:
            try:
                if log_file.exists():
                    log_file.unlink()
                    removed_count += 1
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not remove log file {log_file}: {e}")
        
        return removed_count
    
    def _archive_session(self, session_id: str, files: List[Path]) -> bool:
        """Archive session log files
        
        Args:
            session_id: Session identifier
            files: List of log files to archive
            
        Returns:
            True if archival successful, False otherwise
        """
        try:
            # Create archive directory if it doesn't exist
            self.archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Create session archive directory
            session_archive_dir = self.archive_dir / session_id
            session_archive_dir.mkdir(exist_ok=True)
            
            # Copy files to archive directory
            archived_count = 0
            for log_file in files:
                if log_file.exists():
                    try:
                        import shutil
                        archive_path = session_archive_dir / log_file.name
                        shutil.copy2(log_file, archive_path)
                        
                        # Optionally compress the file
                        if self.session_config.archive_compression:
                            self._compress_file(archive_path)
                        
                        # Remove original file after successful archive
                        log_file.unlink()
                        archived_count += 1
                        
                    except Exception as e:
                        print(f"Warning: Could not archive file {log_file}: {e}")
                        continue
            
            # Create session metadata file
            self._create_session_metadata(session_archive_dir, session_id, archived_count)
            
            return archived_count > 0
            
        except Exception as e:
            print(f"Warning: Session archival failed for {session_id}: {e}")
            return False
    
    def _compress_file(self, file_path: Path) -> bool:
        """Compress a log file using gzip
        
        Args:
            file_path: Path to file to compress
            
        Returns:
            True if compression successful, False otherwise
        """
        try:
            import gzip
            import shutil
            
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file after successful compression
            file_path.unlink()
            return True
            
        except Exception as e:
            print(f"Warning: Could not compress file {file_path}: {e}")
            return False
    
    def _create_session_metadata(self, archive_dir: Path, session_id: str, file_count: int) -> None:
        """Create metadata file for archived session
        
        Args:
            archive_dir: Directory where session is archived
            session_id: Session identifier
            file_count: Number of files archived
        """
        try:
            from datetime import datetime
            
            metadata = {
                "session_id": session_id,
                "archived_at": datetime.now().isoformat(),
                "file_count": file_count,
                "compression_enabled": self.session_config.archive_compression
            }
            
            metadata_file = archive_dir / "session_metadata.json"
            import json
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not create session metadata: {e}")
    
    def cleanup_old_archives(self) -> Dict[str, Any]:
        """Clean up old archived sessions based on max_archived_sessions limit
        
        Returns:
            Dictionary with cleanup results
        """
        results = {
            "archives_processed": 0,
            "archives_removed": 0,
            "errors": []
        }
        
        try:
            if not self.archive_dir.exists():
                return results
            
            # Get all archived session directories
            archived_sessions = []
            for session_dir in self.archive_dir.iterdir():
                if session_dir.is_dir():
                    # Extract session timestamp for sorting
                    try:
                        session_id = session_dir.name
                        age_days = self.get_session_age_days(session_id)
                        if age_days >= 0:
                            archived_sessions.append((session_dir, age_days))
                    except Exception:
                        continue
            
            results["archives_processed"] = len(archived_sessions)
            
            # Sort by age (oldest first) and remove excess archives
            archived_sessions.sort(key=lambda x: x[1], reverse=True)  # Newest first
            
            # Remove oldest archives if we exceed the limit
            if len(archived_sessions) > self.session_config.max_archived_sessions:
                sessions_to_remove = archived_sessions[self.session_config.max_archived_sessions:]
                
                for session_dir, _ in sessions_to_remove:
                    try:
                        import shutil
                        shutil.rmtree(session_dir)
                        results["archives_removed"] += 1
                    except Exception as e:
                        results["errors"].append(f"Could not remove archive {session_dir.name}: {e}")
                        
        except Exception as e:
            results["errors"].append(f"Archive cleanup failed: {e}")
        
        return results
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about session logs and archives
        
        Returns:
            Dictionary with session statistics
        """
        stats = {
            "active_sessions": 0,
            "total_log_files": 0,
            "archived_sessions": 0,
            "oldest_session_age_days": None,
            "newest_session_age_days": None,
            "disk_usage_mb": 0
        }
        
        try:
            # Count active sessions
            session_files = self.list_session_logs()
            stats["active_sessions"] = len(session_files)
            
            # Count total log files and calculate ages
            session_ages = []
            for session_id, files in session_files.items():
                stats["total_log_files"] += len(files)
                age = self.get_session_age_days(session_id)
                if age >= 0:
                    session_ages.append(age)
            
            if session_ages:
                stats["oldest_session_age_days"] = max(session_ages)
                stats["newest_session_age_days"] = min(session_ages)
            
            # Count archived sessions
            if self.archive_dir.exists():
                stats["archived_sessions"] = len([d for d in self.archive_dir.iterdir() if d.is_dir()])
            
            # Calculate disk usage
            stats["disk_usage_mb"] = self._calculate_disk_usage()
            
        except Exception as e:
            print(f"Warning: Could not calculate session stats: {e}")
        
        return stats
    
    def _calculate_disk_usage(self) -> float:
        """Calculate total disk usage of session logs in MB
        
        Returns:
            Disk usage in megabytes
        """
        total_size = 0
        
        try:
            # Calculate active session log sizes
            if self.log_dir.exists():
                for log_file in self.log_dir.glob("*.log"):
                    total_size += log_file.stat().st_size
            
            # Calculate archived session sizes
            if self.archive_dir.exists():
                for archive_file in self.archive_dir.rglob("*"):
                    if archive_file.is_file():
                        total_size += archive_file.stat().st_size
        
        except Exception as e:
            print(f"Warning: Could not calculate disk usage: {e}")
        
        return total_size / (1024 * 1024)  # Convert to MB


class ConfigManager:
    """Thread-safe configuration manager using OBDII_HOME structure
    
    Provides atomic configuration operations with reader-writer locks for
    optimal concurrent access patterns. Implements thread-safe singleton
    with double-checked locking and hardware-aware validation.
    """
    
    _instance = None
    _instance_lock = threading.Lock()
    _instances = weakref.WeakSet()  # Track instances for testing
    
    def __new__(cls, config_path: Optional[str] = None, force_new: bool = False):
        """Thread-safe singleton with double-checked locking"""
        if force_new:  # For testing
            instance = super().__new__(cls)
            cls._instances.add(instance)
            return instance
            
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instances.add(cls._instance)
        return cls._instance
        
    def __init__(self, config_path: Optional[str] = None, force_new: bool = False):
        """Initialize thread-safe configuration manager
        
        Args:
            config_path: Optional path to configuration file.
                         Defaults to OBDII_HOME/config/config.yaml
            force_new: Force creation of new instance (for testing)
        """
        # Prevent double initialization of singleton
        if hasattr(self, '_initialized') and not force_new:
            return
            
        # Ensure OBDII directories exist
        ensure_directories()
        
        # Use OBDII_HOME structure for config path
        if config_path is None:
            self.config_path = str(get_config_file("config.yaml"))
        else:
            self.config_path = config_path
            
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Legacy config path (for migration)
        legacy_home = os.path.expanduser("~/.obdii")
        self.legacy_ini_path = os.path.join(legacy_home, "config.ini")
        self.legacy_yaml_path = os.path.join(legacy_home, "config.yaml")
        
        # Thread-safe configuration access
        self._rw_lock = RWLock()
        self._config_cache = None
        self._cache_timestamp = 0
        self._cache_lock = threading.Lock()
        
        # Thread-safe logging initialization
        self._logging_lock = threading.Lock()
        self._logging_initialized = False
        
        # Session-based logging management with thread safety
        self._session_id = None
        self._session_lock = threading.Lock()
        self._session_log_dir = None
        self._session_manager = None
        self.session_config = SessionConfig()  # Default session configuration
        
        # Configuration validator
        self._validator = ConfigValidator()
        
        # Performance monitoring
        self._operation_count = 0
        self._read_count = 0
        self._write_count = 0
        self._performance_lock = threading.Lock()
        
        # Mark as initialized
        self._initialized = True
        
        # Log initialization
        self.logger = logging.getLogger(f'{__name__}.ConfigManager')
        if hasattr(logging.getLogger(), 'handlers') and logging.getLogger().handlers:
            self.logger.debug(f"ConfigManager initialized with path: {self.config_path}")
        
    @contextmanager
    def _performance_timing(self, operation_type: str):
        """Context manager for performance monitoring"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            with self._performance_lock:
                self._operation_count += 1
                if operation_type == 'read':
                    self._read_count += 1
                elif operation_type == 'write':
                    self._write_count += 1
                    
                # Log slow operations
                if elapsed > 0.1:  # 100ms threshold
                    self.logger.warning(f"Slow config {operation_type}: {elapsed:.3f}s")
                elif self._operation_count % 100 == 0:
                    self.logger.debug(f"Config performance: {self._read_count} reads, {self._write_count} writes, avg {elapsed:.3f}s")
                    
    def load_config(self) -> OBDConfig:
        """Load configuration with thread-safe caching and validation
        
        Returns:
            Complete application configuration object
        """
        with self._performance_timing('read'):
            with self._rw_lock.read_lock():
                # Check cache first
                cached_config = self._get_cached_config()
                if cached_config is not None:
                    return cached_config
                    
        # Need to load from disk - acquire write lock for cache update
        with self._performance_timing('read'):
            with self._rw_lock.write_lock():
                # Double-check cache after acquiring write lock
                cached_config = self._get_cached_config()
                if cached_config is not None:
                    return cached_config
                    
                try:
                    config = self._load_config_from_disk()
                    
                    # Validate configuration
                    validation_result = self._validator.validate_config(config)
                    if not validation_result['valid']:
                        self.logger.warning(f"Configuration validation errors: {validation_result['errors']}")
                        if validation_result['warnings']:
                            self.logger.info(f"Configuration warnings: {validation_result['warnings']}")
                    
                    # Update cache
                    self._update_cache(config)
                    return config
                    
                except Exception as e:
                    self.logger.error(f"Failed to load configuration: {e}")
                    # Return default config on error
                    default_config = OBDConfig()
                    self._update_cache(default_config)
                    return default_config
                    
    def _get_cached_config(self) -> Optional[OBDConfig]:
        """Get cached configuration if still valid"""
        with self._cache_lock:
            if self._config_cache is None:
                return None
                
            # Check if cache is still valid (file modification time)
            try:
                if os.path.exists(self.config_path):
                    file_mtime = os.path.getmtime(self.config_path)
                    if file_mtime > self._cache_timestamp:
                        # File modified, cache invalid
                        self._config_cache = None
                        return None
                        
                return self._config_cache
            except OSError:
                # Error checking file, invalidate cache
                self._config_cache = None
                return None
                
    def _update_cache(self, config: OBDConfig) -> None:
        """Update configuration cache"""
        with self._cache_lock:
            self._config_cache = config
            self._cache_timestamp = time.time()
            
    def _load_config_from_disk(self) -> OBDConfig:
        """Load configuration from disk with migration support"""
        try:
            # Try to load YAML config from OBDII_HOME first
            if os.path.exists(self.config_path):
                return self._load_yaml_config()
                
            # Check for legacy config in ~/.obdii and migrate
            if os.path.exists(self.legacy_yaml_path):
                config = self._load_yaml_config_from_path(self.legacy_yaml_path)
                # Save to new OBDII_HOME location
                self._atomic_save_config(config)
                return config
                
            # Fall back to legacy INI if it exists
            if os.path.exists(self.legacy_ini_path):
                config = self._load_legacy_ini_config()
                # Save as YAML in OBDII_HOME for future use
                self._atomic_save_config(config)
                return config
                
            # No config exists, create a default one
            config = OBDConfig()
            self._atomic_save_config(config)
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config from disk: {e}")
            raise
    
    def _load_yaml_config(self) -> OBDConfig:
        """Load configuration from YAML file"""
        return self._load_yaml_config_from_path(self.config_path)
    
    def _load_yaml_config_from_path(self, path: str) -> OBDConfig:
        """Load configuration from YAML file at specified path"""
        if not YAML_AVAILABLE:
            print("YAML not available - cannot load YAML configuration")
            return OBDConfig()
            
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return OBDConfig()
            
        return OBDConfig.from_dict(data)
    
    def _load_legacy_ini_config(self) -> OBDConfig:
        """Load configuration from legacy INI file"""
        config_parser = configparser.ConfigParser()
        config_parser.read(self.legacy_ini_path)
        
        # Convert INI format to dictionary
        data = {}
        if "OBD" in config_parser.sections():
            obd_section = config_parser["OBD"]
            data.update({
                "port": obd_section.get("port", "AUTO"),
                "baudrate": obd_section.getint("baudrate", 38400),
                "timeout": obd_section.getfloat("timeout", 1.0),
                "reconnect_attempts": obd_section.getint("reconnect_attempts", 3),
                "fast_mode": obd_section.getboolean("fast_mode", True)
            })
            
        if "DISPLAY" in config_parser.sections():
            display_section = config_parser["DISPLAY"]
            data["display"] = {
                "mode": display_section.get("mode", "DIGITAL"),
                "rpm_warning": display_section.getint("rpm_warning", 6500),
                "rpm_danger": display_section.getint("rpm_danger", 7000),
                "fps_limit": display_section.getint("fps_limit", 60)
            }
            
        return OBDConfig.from_dict(data)
            
    def save_config(self, config: OBDConfig) -> bool:
        """Save configuration with thread-safe atomic operation
        
        Args:
            config: Configuration object to save
        
        Returns:
            True if successful, False otherwise
        """
        with self._performance_timing('write'):
            with self._rw_lock.write_lock():
                success = self._atomic_save_config(config)
                if success:
                    # Update cache with new config
                    self._update_cache(config)
                return success
                
    def _atomic_save_config(self, config: OBDConfig) -> bool:
        """Atomically save configuration to disk
        
        Uses temporary file and rename for atomic operation.
        
        Args:
            config: Configuration object to save
        
        Returns:
            True if successful, False otherwise
        """
        if not YAML_AVAILABLE:
            self.logger.error("YAML not available - configuration will not be persisted")
            return False
            
        try:
            # Validate configuration before saving
            validation_result = self._validator.validate_config(config)
            if not validation_result['valid']:
                self.logger.error(f"Cannot save invalid configuration: {validation_result['errors']}")
                return False
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Convert to dictionary
            config_dict = config.to_dict()
            
            # Atomic save using temporary file
            temp_path = f"{self.config_path}.tmp.{uuid.uuid4().hex[:8]}"
            
            try:
                with open(temp_path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
                    f.flush()  # Ensure data is written
                    os.fsync(f.fileno())  # Force filesystem sync
                    
                # Atomic rename
                if os.name == 'nt':  # Windows
                    if os.path.exists(self.config_path):
                        os.remove(self.config_path)
                os.rename(temp_path, self.config_path)
                
                self.logger.debug(f"Configuration saved atomically to {self.config_path}")
                return True
                
            except Exception as e:
                # Clean up temp file on error
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except OSError:
                    pass
                raise e
                
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_home_path(self) -> Path:
        """Get OBDII home directory path"""
        return get_home_path()
            
    def get_device_by_address(self, config: OBDConfig, address: str) -> Optional[BluetoothDevice]:
        """Find a device in the configuration by its address
        
        Args:
            config: Configuration object to search
            address: Device MAC address to find
        
        Returns:
            BluetoothDevice if found, None otherwise
        """
        # Normalize address format
        normalized_address = address.upper().replace(':', '')
        
        for device in config.bluetooth.saved_devices:
            if device.address.upper().replace(':', '') == normalized_address:
                return device
                
        return None
        
    def add_or_update_device(self, config: OBDConfig, device: BluetoothDevice) -> OBDConfig:
        """Add or update a device in the configuration
        
        Args:
            config: Current configuration
            device: Device to add or update
        
        Returns:
            Updated configuration
        """
        # Check if device already exists
        existing_device = self.get_device_by_address(config, device.address)
        
        if existing_device:
            # Update existing device
            idx = config.bluetooth.saved_devices.index(existing_device)
            config.bluetooth.saved_devices[idx] = device
        else:
            # Add new device
            config.bluetooth.saved_devices.append(device)
            
        return config
        
    def remove_device(self, config: OBDConfig, address: str) -> OBDConfig:
        """Remove a device from the configuration
        
        Args:
            config: Current configuration
            address: Device address to remove
        
        Returns:
            Updated configuration
        """
        device = self.get_device_by_address(config, address)
        
        if device:
            config.bluetooth.saved_devices.remove(device)
            
            # Reset last_device if it was the removed device
            if config.bluetooth.last_device == device.address:
                config.bluetooth.last_device = None
                
        return config
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID using UUID with timestamp prefix
        
        Ensures global uniqueness even under high concurrency.
        
        Returns:
            str: Unique session ID in format YYYYMMDD_HHMMSS_UUID
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = uuid.uuid4().hex[:8]  # 8 character UUID suffix
        return f"{timestamp}_{unique_suffix}"
    
    def get_session_id(self) -> str:
        """Get the current session ID with thread-safe generation
        
        Returns:
            str: Current session ID
        """
        with self._session_lock:
            if self._session_id is None:
                self._session_id = self.generate_session_id()
            return self._session_id
            
    def create_transaction(self, config: Optional[OBDConfig] = None) -> ConfigTransaction:
        """Create a configuration transaction for atomic updates
        
        Args:
            config: Configuration to base transaction on, loads current if None
        
        Returns:
            ConfigTransaction for atomic updates
        """
        if config is None:
            config = self.load_config()
        return ConfigTransaction(self, config)
        
    def get_lock_stats(self) -> Dict[str, Any]:
        """Get reader-writer lock statistics for monitoring
        
        Returns:
            Dictionary with lock and performance statistics
        """
        lock_stats = self._rw_lock.get_stats()
        
        with self._performance_lock:
            performance_stats = {
                'total_operations': self._operation_count,
                'read_operations': self._read_count,
                'write_operations': self._write_count,
                'read_write_ratio': self._read_count / max(1, self._write_count)
            }
            
        return {
            'lock_stats': lock_stats,
            'performance_stats': performance_stats,
            'cache_status': {
                'cached': self._config_cache is not None,
                'cache_timestamp': self._cache_timestamp
            }
        }
        
    def validate_config(self, config: OBDConfig) -> Dict[str, Any]:
        """Validate configuration using hardware-aware validator
        
        Args:
            config: Configuration to validate
        
        Returns:
            Validation results with errors, warnings, and platform info
        """
        return self._validator.validate_config(config)
        
    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> 'ConfigManager':
        """Get singleton instance with optional config path
        
        Args:
            config_path: Optional configuration file path
        
        Returns:
            ConfigManager singleton instance
        """
        return cls(config_path)
        
    @classmethod
    def reset_singleton(cls) -> None:
        """Reset singleton instance (for testing)"""
        with cls._instance_lock:
            cls._instance = None
    
    def clear_session_logs(self, log_dir: Path) -> None:
        """Clear current session debug log file before creating new one.
        
        Note: This method is now simplified for single debug file approach.
        
        Args:
            log_dir: Directory containing log files to clear
        """
        if not log_dir.exists():
            return
            
        session_id = self.get_session_id()
        debug_log_file = log_dir / f"obdii_debug_{session_id}.log"
        
        try:
            if debug_log_file.exists():
                debug_log_file.unlink()
                print(f"Cleared existing debug log: {debug_log_file}")
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not clear debug log {debug_log_file}: {e}")
    
    def get_session_manager(self) -> Optional[SessionManager]:
        """Get the current SessionManager instance
        
        Returns:
            SessionManager instance if initialized, None otherwise
        """
        return self._session_manager
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics using SessionManager
        
        Returns:
            Dictionary with session statistics
        """
        if self._session_manager:
            return self._session_manager.get_session_stats()
        return {}
    
    def cleanup_old_sessions(self) -> Dict[str, Any]:
        """Cleanup old sessions using SessionManager
        
        Returns:
            Dictionary with cleanup results
        """
        if self._session_manager:
            return self._session_manager.cleanup_old_sessions()
        return {"error": "SessionManager not initialized"}
    
    def cleanup_old_archives(self) -> Dict[str, Any]:
        """Cleanup old archived sessions using SessionManager
        
        Returns:
            Dictionary with cleanup results
        """
        if self._session_manager:
            return self._session_manager.cleanup_old_archives()
        return {"error": "SessionManager not initialized"}
    
    def setup_logging(self, debug: bool = False) -> None:
        """Configure debug-conditional logging with platform detection.
        
        Production mode: Console-only logging with minimal overhead
        Debug mode: Console + single debug file with comprehensive logging
        
        Args:
            debug: Enable debug file logging and detailed output if True
        """
        # Thread-safe logging initialization
        with self._logging_lock:
            if self._logging_initialized:
                return
                
            try:
                # Detect platform for ARM compatibility and debugging
                platform_info = self._detect_platform()
                
                if debug:
                    # Generate session ID only for debug mode
                    session_id = self.get_session_id()
                    print(f"Debug mode: Initializing logging with session ID: {session_id}")
                    print(f"Platform: {platform_info['description']}")
                    
                    # Setup debug logging with file output
                    self._setup_debug_logging(session_id, platform_info)
                else:
                    # Production mode: console-only logging
                    self._setup_production_logging()
                
                self._logging_initialized = True
                
            except Exception as e:
                # Emergency fallback: basic console logging only
                print(f"Error setting up logging: {e}")
                try:
                    logging.basicConfig(
                        level=logging.WARNING,
                        format='[FALLBACK] %(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler(sys.stderr)],
                        force=True
                    )
                    self._logging_initialized = True
                except Exception as fallback_error:
                    print(f"Critical: Even fallback logging failed: {fallback_error}")
    
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect platform information for ARM compatibility and debugging.
        
        Returns:
            dict: Platform information including system, machine, and capabilities
        """
        import platform
        
        system = platform.system()
        machine = platform.machine()
        
        # Determine if running on Raspberry Pi
        is_pi = (system == 'Linux' and 
                (machine.startswith('arm') or machine.startswith('aarch')))
        
        # Determine if running on Mac
        is_mac = system == 'Darwin'
        
        platform_info = {
            'system': system,
            'machine': machine,
            'is_pi': is_pi,
            'is_mac': is_mac,
            'is_arm': machine.startswith(('arm', 'aarch')),
            'description': f"{system}/{machine}"
        }
        
        # Add Pi-specific detection
        if is_pi:
            try:
                # Check for Pi-specific files
                pi_model = "Unknown Pi"
                if Path('/proc/device-tree/model').exists():
                    with open('/proc/device-tree/model', 'r') as f:
                        pi_model = f.read().strip().replace('\x00', '')
                platform_info['pi_model'] = pi_model
                platform_info['description'] = f"Raspberry Pi ({pi_model})"
            except Exception:
                platform_info['pi_model'] = "Unknown Pi"
        
        return platform_info
    
    def _setup_production_logging(self) -> None:
        """Setup minimal console-only logging for production mode.
        
        Optimized for minimal resource usage and overhead.
        """
        try:
            # Console handler only - no file logging in production
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Simple formatter for production
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            root_logger.handlers.clear()  # Remove any existing handlers
            root_logger.addHandler(console_handler)
            
            print("Production logging: Console output only")
            
        except Exception as e:
            print(f"Error setting up production logging: {e}")
            # Ultimate fallback
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                force=True
            )
    
    def _setup_debug_logging(self, session_id: str, platform_info: Dict[str, Any]) -> None:
        """Setup comprehensive debug logging with file output.
        
        Args:
            session_id: Unique session identifier
            platform_info: Platform detection results
        """
        try:
            # Determine log directory with platform-aware fallback
            log_dir = self._get_log_directory()
            self._session_log_dir = log_dir
            
            print(f"Debug logging directory: {log_dir}")
            
            # Clear any existing debug log for this session
            self._clear_debug_logs(log_dir, session_id)
            
            # Setup handlers
            handlers = []
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # Debug file handler (single file approach)
            debug_log_path = log_dir / f'obdii_debug_{session_id}.log'
            file_handler = logging.FileHandler(str(debug_log_path), mode='w')
            file_handler.setLevel(logging.DEBUG)
            
            # Comprehensive formatter for debug mode
            formatter = logging.Formatter(
                '%(asctime)s - [%(name)s:%(funcName)s:%(lineno)d] - %(levelname)s - %(message)s'
            )
            
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            handlers.extend([console_handler, file_handler])
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            root_logger.handlers.clear()  # Remove any existing handlers
            
            for handler in handlers:
                root_logger.addHandler(handler)
            
            print(f"Debug logging: Console + file ({debug_log_path})")
            
            # Log platform information for debugging
            logger = logging.getLogger(__name__)
            logger.debug(f"Platform detection: {platform_info}")
            logger.debug(f"Debug session started: {session_id}")
            
            # Initialize SessionManager for debug mode session tracking
            if not self._session_manager:
                self._session_manager = SessionManager(log_dir, self.session_config)
                logger.debug(f"SessionManager initialized for directory: {log_dir}")
            
            # Log hardware interface availability on Pi
            if platform_info['is_pi']:
                self._log_pi_hardware_status(logger)
            
        except Exception as e:
            print(f"Error setting up debug logging: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to console-only
            self._setup_production_logging()
    
    def _get_log_directory(self) -> Path:
        """Get appropriate log directory with platform-aware fallback.
        
        Returns:
            Path: Log directory path
        """
        # Try system log directory first
        system_log_dir = Path('/var/log/obdii')
        try:
            system_log_dir.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = system_log_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
            return system_log_dir
        except (OSError, PermissionError):
            pass
        
        # Fallback to OBDII_HOME logs directory
        try:
            user_log_dir = get_home_path() / 'logs'
            user_log_dir.mkdir(parents=True, exist_ok=True)
            return user_log_dir
        except Exception:
            # Ultimate fallback to temp directory
            import tempfile
            return Path(tempfile.gettempdir()) / 'obdii_logs'
    
    def _clear_debug_logs(self, log_dir: Path, session_id: str) -> None:
        """Clear debug log file for current session.
        
        Args:
            log_dir: Log directory path
            session_id: Session identifier
        """
        debug_log_file = log_dir / f'obdii_debug_{session_id}.log'
        try:
            if debug_log_file.exists():
                debug_log_file.unlink()
                print(f"Cleared existing debug log: {debug_log_file}")
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not clear debug log {debug_log_file}: {e}")
    
    def _log_pi_hardware_status(self, logger: logging.Logger) -> None:
        """Log Raspberry Pi hardware interface status for debugging.
        
        Args:
            logger: Logger instance for output
        """
        try:
            # Check framebuffer
            fb_status = "Available" if Path('/dev/fb0').exists() else "Not found"
            logger.debug(f"Framebuffer (/dev/fb0): {fb_status}")
            
            # Check I2C interfaces
            i2c_interfaces = list(Path('/dev').glob('i2c-*'))
            if i2c_interfaces:
                logger.debug(f"I2C interfaces: {[i.name for i in i2c_interfaces]}")
            else:
                logger.debug("I2C interfaces: None found")
            
            # Check GPIO access
            gpio_status = "Available" if Path('/sys/class/gpio').exists() else "Not found"
            logger.debug(f"GPIO interface: {gpio_status}")
            
            # Check for HyperPixel display (I2C address 0x15 on bus 11)
            try:
                # This is a safe check that doesn't require actual I2C communication
                if Path('/dev/i2c-11').exists():
                    logger.debug("HyperPixel I2C bus (11): Available")
                else:
                    logger.debug("HyperPixel I2C bus (11): Not found")
            except Exception as e:
                logger.debug(f"HyperPixel check error: {e}")
                
        except Exception as e:
            logger.debug(f"Error checking Pi hardware status: {e}")
    
    def clear_cache(self) -> None:
        """Clear configuration cache (thread-safe)"""
        with self._cache_lock:
            self._config_cache = None
            self._cache_timestamp = 0
            self.logger.debug("Configuration cache cleared")
            
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        pass  # ConfigManager is singleton, no cleanup needed
        
    def __del__(self):
        """Cleanup on garbage collection"""
        try:
            # Log final statistics if logger available
            if hasattr(self, 'logger') and hasattr(self, '_performance_lock'):
                stats = self.get_lock_stats()
                self.logger.debug(f"ConfigManager cleanup - final stats: {stats['performance_stats']}")
        except Exception:
            pass  # Best effort cleanup
            
    # NOTE: Complex YAML logging methods have been removed in favor of 
    # the simplified debug-conditional approach implemented above.
    # This provides better performance and reliability while maintaining
    # thread safety through proper synchronization primitives.
