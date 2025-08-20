#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Configuration Service for OBDII Foundational Services Architecture

Provides atomic configuration operations with validation and coordination
across subsystems. Eliminates ad-hoc configuration access patterns.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable, Union, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

# Import existing configuration system
from ..config import ConfigManager, OBDConfig, ConfigTransaction, ConfigValidator


class ConfigurationError(Exception):
    """Configuration service specific errors"""
    pass


class ConfigurationValidationError(ConfigurationError):
    """Configuration validation errors"""
    pass


@dataclass
class ConfigurationEvent:
    """Configuration change event"""
    event_type: str  # 'updated', 'validated', 'loaded', 'saved'
    config_path: Optional[str] = None
    section: Optional[str] = None
    key: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationService:
    """
    Atomic configuration service with validation and coordination.
    
    Provides:
    - Thread-safe atomic configuration operations
    - Configuration validation and consistency checking
    - Change notifications and event handling
    - Integration with existing ConfigManager
    - Cross-subsystem configuration coordination
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize configuration service.
        
        Args:
            config_manager: Optional existing ConfigManager instance
        """
        self.logger = logging.getLogger('ConfigurationService')
        
        # Use provided ConfigManager or create new one
        self._config_manager = config_manager or ConfigManager()
        
        # Thread safety
        self._lock = threading.RLock()
        self._operation_lock = threading.Lock()
        
        # Configuration cache with validation
        self._config_cache: Optional[OBDConfig] = None
        self._cache_timestamp: float = 0
        self._cache_valid: bool = False
        
        # Event system
        self._event_callbacks: Dict[str, List[Callable]] = {
            'updated': [],
            'validated': [],
            'loaded': [],
            'saved': [],
            'error': []
        }
        self._event_lock = threading.Lock()
        
        # Validation system
        self._validator = ConfigValidator()
        self._validation_enabled = True
        
        # Performance monitoring
        self._operation_count = 0
        self._validation_count = 0
        self._performance_lock = threading.Lock()
        
        # Configuration sections registry
        self._section_handlers: Dict[str, Dict[str, Any]] = {}
        
        self.logger.debug("ConfigurationService initialized")
    
    @contextmanager
    def _performance_timing(self, operation: str) -> ContextManager[None]:
        """Context manager for performance monitoring"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            with self._performance_lock:
                self._operation_count += 1
                if elapsed > 0.1:  # Log slow operations
                    self.logger.warning(f"Slow configuration operation {operation}: {elapsed:.3f}s")
    
    def load_configuration(self, validate: bool = True) -> OBDConfig:
        """
        Load configuration with atomic operation and validation.
        
        Args:
            validate: Whether to validate configuration after loading
            
        Returns:
            Loaded configuration object
            
        Raises:
            ConfigurationError: If loading fails
            ConfigurationValidationError: If validation fails
        """
        with self._performance_timing("load_configuration"):
            with self._lock:
                try:
                    # Load configuration through existing manager
                    config = self._config_manager.load_config()
                    
                    # Validate if requested
                    if validate and self._validation_enabled:
                        validation_result = self._validate_configuration(config)
                        if not validation_result['valid']:
                            error_msg = f"Configuration validation failed: {validation_result['errors']}"
                            self._emit_event('error', metadata={'validation_errors': validation_result['errors']})
                            raise ConfigurationValidationError(error_msg)
                    
                    # Update cache
                    self._config_cache = config
                    self._cache_timestamp = time.time()
                    self._cache_valid = True
                    
                    # Emit event
                    self._emit_event('loaded', metadata={'validation_enabled': validate})
                    
                    self.logger.debug("Configuration loaded successfully")
                    return config
                    
                except Exception as e:
                    self._cache_valid = False
                    self._emit_event('error', metadata={'error': str(e)})
                    if isinstance(e, ConfigurationValidationError):
                        raise
                    raise ConfigurationError(f"Failed to load configuration: {e}") from e
    
    def save_configuration(self, config: OBDConfig, validate: bool = True) -> bool:
        """
        Save configuration with atomic operation and validation.
        
        Args:
            config: Configuration to save
            validate: Whether to validate before saving
            
        Returns:
            True if successful
            
        Raises:
            ConfigurationError: If saving fails
            ConfigurationValidationError: If validation fails
        """
        with self._performance_timing("save_configuration"):
            with self._lock:
                try:
                    # Validate if requested
                    if validate and self._validation_enabled:
                        validation_result = self._validate_configuration(config)
                        if not validation_result['valid']:
                            error_msg = f"Configuration validation failed: {validation_result['errors']}"
                            self._emit_event('error', metadata={'validation_errors': validation_result['errors']})
                            raise ConfigurationValidationError(error_msg)
                    
                    # Save through existing manager
                    success = self._config_manager.save_config(config)
                    
                    if success:
                        # Update cache
                        self._config_cache = config
                        self._cache_timestamp = time.time()
                        self._cache_valid = True
                        
                        # Emit event
                        self._emit_event('saved', metadata={'validation_enabled': validate})
                        
                        self.logger.debug("Configuration saved successfully")
                    else:
                        self._emit_event('error', metadata={'error': 'Save operation failed'})
                        raise ConfigurationError("Configuration save operation failed")
                    
                    return success
                    
                except Exception as e:
                    self._emit_event('error', metadata={'error': str(e)})
                    if isinstance(e, ConfigurationValidationError):
                        raise
                    raise ConfigurationError(f"Failed to save configuration: {e}") from e
    
    def create_transaction(self, config: Optional[OBDConfig] = None) -> ConfigTransaction:
        """
        Create atomic configuration transaction.
        
        Args:
            config: Base configuration for transaction
            
        Returns:
            Configuration transaction context manager
        """
        with self._performance_timing("create_transaction"):
            if config is None:
                config = self.get_cached_configuration()
            
            transaction = self._config_manager.create_transaction(config)
            self.logger.debug("Configuration transaction created")
            return transaction
    
    def get_cached_configuration(self, max_age: float = 60.0) -> OBDConfig:
        """
        Get cached configuration with age validation.
        
        Args:
            max_age: Maximum cache age in seconds
            
        Returns:
            Cached or freshly loaded configuration
        """
        with self._lock:
            current_time = time.time()
            cache_age = current_time - self._cache_timestamp
            
            # Check cache validity
            if (self._config_cache is None or 
                not self._cache_valid or 
                cache_age > max_age):
                
                self.logger.debug(f"Cache miss or expired (age: {cache_age:.1f}s), reloading")
                return self.load_configuration()
            
            self.logger.debug(f"Using cached configuration (age: {cache_age:.1f}s)")
            return self._config_cache
    
    def update_section(self, section: str, updates: Dict[str, Any], validate: bool = True) -> bool:
        """
        Update specific configuration section atomically.
        
        Args:
            section: Configuration section name
            updates: Dictionary of key-value updates
            validate: Whether to validate after update
            
        Returns:
            True if successful
        """
        with self._performance_timing(f"update_section({section})"):
            try:
                transaction = self.create_transaction()
                with transaction as config:
                    # Get section object
                    if not hasattr(config, section):
                        raise ConfigurationError(f"Unknown configuration section: {section}")
                    
                    section_obj = getattr(config, section)
                    old_values = {}
                    
                    # Apply updates
                    for key, value in updates.items():
                        if hasattr(section_obj, key):
                            old_values[key] = getattr(section_obj, key)
                            setattr(section_obj, key, value)
                        else:
                            raise ConfigurationError(f"Unknown configuration key: {section}.{key}")
                    
                    # Validate if requested
                    if validate and self._validation_enabled:
                        validation_result = self._validate_configuration(config)
                        if not validation_result['valid']:
                            raise ConfigurationValidationError(f"Validation failed: {validation_result['errors']}")
                    
                    # Commit transaction
                    success = transaction.commit()
                    
                    if success:
                        # Update cache
                        self._config_cache = config
                        self._cache_timestamp = time.time()
                        self._cache_valid = True
                        
                        # Emit update events
                        for key, new_value in updates.items():
                            old_value = old_values.get(key)
                            self._emit_event('updated', 
                                           section=section, 
                                           key=key, 
                                           old_value=old_value, 
                                           new_value=new_value)
                        
                        self.logger.debug(f"Updated section '{section}' with {len(updates)} changes")
                    
                    return success
                    
            except Exception as e:
                self._emit_event('error', metadata={'section': section, 'error': str(e)})
                if isinstance(e, (ConfigurationError, ConfigurationValidationError)):
                    raise
                raise ConfigurationError(f"Failed to update section '{section}': {e}") from e
    
    def get_section_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get value from configuration section.
        
        Args:
            section: Configuration section name
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        try:
            config = self.get_cached_configuration()
            
            if not hasattr(config, section):
                return default
            
            section_obj = getattr(config, section)
            return getattr(section_obj, key, default)
            
        except Exception as e:
            self.logger.error(f"Error getting {section}.{key}: {e}")
            return default
    
    def set_section_value(self, section: str, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set single configuration value atomically.
        
        Args:
            section: Configuration section name
            key: Configuration key
            value: New value
            validate: Whether to validate after setting
            
        Returns:
            True if successful
        """
        return self.update_section(section, {key: value}, validate)
    
    def _validate_configuration(self, config: OBDConfig) -> Dict[str, Any]:
        """
        Validate configuration using existing validator.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation result dictionary
        """
        with self._performance_lock:
            self._validation_count += 1
        
        try:
            result = self._validator.validate_config(config)
            
            # Emit validation event
            self._emit_event('validated', metadata={
                'valid': result['valid'],
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', [])
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return {
                'valid': False,
                'errors': [f"Validation system error: {e}"],
                'warnings': []
            }
    
    def register_section_handler(self, section: str, handler_config: Dict[str, Any]) -> None:
        """
        Register a handler for configuration section changes.
        
        Args:
            section: Configuration section name
            handler_config: Handler configuration
        """
        with self._lock:
            self._section_handlers[section] = handler_config
            self.logger.debug(f"Registered handler for section '{section}'")
    
    def add_event_callback(self, event_type: str, callback: Callable[[ConfigurationEvent], None]) -> None:
        """
        Add callback for configuration events.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function
        """
        if event_type not in self._event_callbacks:
            raise ConfigurationError(f"Unknown event type: {event_type}")
        
        with self._event_lock:
            self._event_callbacks[event_type].append(callback)
            self.logger.debug(f"Added callback for event type '{event_type}'")
    
    def _emit_event(self, event_type: str, **kwargs) -> None:
        """
        Emit configuration event to callbacks.
        
        Args:
            event_type: Type of event
            **kwargs: Event data
        """
        event = ConfigurationEvent(event_type=event_type, **kwargs)
        
        with self._event_lock:
            callbacks = self._event_callbacks.get(event_type, [])
            
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in event callback for {event_type}: {e}")
    
    def enable_validation(self, enabled: bool = True) -> None:
        """
        Enable or disable configuration validation.
        
        Args:
            enabled: Whether to enable validation
        """
        with self._lock:
            self._validation_enabled = enabled
            self.logger.info(f"Configuration validation {'enabled' if enabled else 'disabled'}")
    
    def clear_cache(self) -> None:
        """Clear configuration cache"""
        with self._lock:
            self._config_cache = None
            self._cache_timestamp = 0
            self._cache_valid = False
            self.logger.debug("Configuration cache cleared")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get configuration service statistics"""
        with self._lock:
            with self._performance_lock:
                return {
                    'cache_valid': self._cache_valid,
                    'cache_age': time.time() - self._cache_timestamp if self._cache_timestamp else 0,
                    'operation_count': self._operation_count,
                    'validation_count': self._validation_count,
                    'validation_enabled': self._validation_enabled,
                    'event_callbacks': {k: len(v) for k, v in self._event_callbacks.items()},
                    'section_handlers': len(self._section_handlers)
                }
    
    def export_configuration(self, include_metadata: bool = False) -> Dict[str, Any]:
        """
        Export current configuration as dictionary.
        
        Args:
            include_metadata: Whether to include service metadata
            
        Returns:
            Configuration dictionary
        """
        config = self.get_cached_configuration()
        config_dict = config.to_dict()
        
        if include_metadata:
            config_dict['_service_metadata'] = {
                'export_timestamp': time.time(),
                'cache_timestamp': self._cache_timestamp,
                'validation_enabled': self._validation_enabled,
                'service_stats': self.get_service_stats()
            }
        
        return config_dict
    
    def import_configuration(self, config_dict: Dict[str, Any], validate: bool = True) -> bool:
        """
        Import configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            validate: Whether to validate imported configuration
            
        Returns:
            True if successful
        """
        try:
            # Remove service metadata if present
            if '_service_metadata' in config_dict:
                config_dict = config_dict.copy()
                del config_dict['_service_metadata']
            
            # Create configuration object
            config = OBDConfig.from_dict(config_dict)
            
            # Save configuration
            return self.save_configuration(config, validate)
            
        except Exception as e:
            self._emit_event('error', metadata={'import_error': str(e)})
            raise ConfigurationError(f"Failed to import configuration: {e}") from e
    
    def get_configuration_manager(self) -> ConfigManager:
        """Get underlying configuration manager"""
        return self._config_manager
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Cleanup if needed
        pass