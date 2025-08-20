#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Configuration Processor for GTach Application Provisioning System

Processes platform-specific configuration templates and generates deployment-ready
configuration files. Integrates with existing configuration management while 
extending for cross-platform deployment scenarios.

Features:
- Platform-specific configuration processing
- Template variable substitution
- Configuration validation per target platform  
- Thread-safe template processing
- Integration with existing ConfigManager
"""

import os
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
from string import Template
from dataclasses import dataclass, field
from contextlib import contextmanager

# Import existing utilities following project structure  
try:
    from ..obdii.utils.platform import PlatformType, get_platform_type
    from ..obdii.utils.config import ConfigManager, OBDConfig
except ImportError:
    # Fallback for development/testing
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from obdii.utils.platform import PlatformType, get_platform_type
    from obdii.utils.config import ConfigManager, OBDConfig

# Try to import yaml for template processing
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False


@dataclass
class PlatformConfig:
    """Platform-specific configuration parameters"""
    platform_name: str
    template_variables: Dict[str, Any] = field(default_factory=dict)
    file_mappings: Dict[str, str] = field(default_factory=dict)  # template -> output
    permission_settings: Dict[str, int] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'platform_name': self.platform_name,
            'template_variables': self.template_variables,
            'file_mappings': self.file_mappings,
            'permission_settings': self.permission_settings,
            'validation_rules': self.validation_rules
        }


class ConfigProcessor:
    """
    Thread-safe configuration processor for cross-platform deployment.
    
    Processes configuration templates and generates platform-specific
    configuration files for deployment packages. Integrates with existing
    configuration management system.
    """
    
    def __init__(self, project_root: Union[str, Path], target_platform: str):
        """
        Initialize ConfigProcessor.
        
        Args:
            project_root: Project root directory
            target_platform: Target platform identifier
        """
        self.logger = logging.getLogger(f'{__name__}.ConfigProcessor')
        
        self.project_root = Path(project_root)
        self.target_platform = target_platform
        
        # Thread safety
        self._processing_lock = threading.RLock()
        self._operation_count = 0
        self._stats_lock = threading.Lock()
        
        # Platform detection and configuration
        self.source_platform = get_platform_type()
        self.config_manager = ConfigManager()
        
        # Configuration file discovery with fallback paths
        self.config_file_path = self._discover_config_file()
        
        # Platform-specific configurations
        self.platform_configs = self._initialize_platform_configs()
        
        # Template cache for performance
        self._template_cache = {}
        self._cache_lock = threading.Lock()
        
        self.logger.info(f"ConfigProcessor initialized - Target: {target_platform}")
        self.logger.debug(f"Source platform: {self.source_platform.name}")
        self.logger.info(f"Configuration file discovered at: {self.config_file_path}")
    
    def _discover_config_file(self) -> Optional[Path]:
        """
        Discover configuration file using fallback search paths.
        
        Searches multiple locations following Protocol 1 standards:
        1. src/config/config.yaml (expected location per Protocol)
        2. config/config.yaml (actual current location)  
        3. config.yaml (project root fallback)
        
        Returns:
            Path to discovered configuration file or None if not found
        """
        search_paths = [
            self.project_root / "src" / "config" / "config.yaml",  # Protocol 1 expected
            self.project_root / "config" / "config.yaml",          # Current actual location
            self.project_root / "config.yaml"                      # Root fallback
        ]
        
        for config_path in search_paths:
            if config_path.exists():
                self.logger.info(f"Configuration file found: {config_path}")
                return config_path
        
        self.logger.error("Configuration file not found in any expected location")
        self.logger.error("Searched paths:")
        for path in search_paths:
            self.logger.error(f"  - {path}")
        
        return None
    
    def _initialize_platform_configs(self) -> Dict[str, PlatformConfig]:
        """
        Initialize platform-specific configurations.
        
        Returns:
            Dictionary of platform configurations
        """
        configs = {}
        
        # Raspberry Pi configuration
        configs['raspberry-pi'] = PlatformConfig(
            platform_name='raspberry-pi',
            template_variables={
                'app_dir': '/opt/gtach',
                'log_dir': '/var/log/gtach',
                'config_dir': '/etc/gtach', 
                'user': 'pi',
                'group': 'pi',
                'python_executable': 'python3',
                'gpio_available': True,
                'display_hardware': True,
                'performance_profile': 'embedded',
                'fps_limit': 30,
                'bluetooth_timeout': 10.0,
                'service_enabled': True
            },
            file_mappings={
                'config.template.yaml': 'config.yaml',
                'service.template': 'gtach.service',
                'environment.template': '.env'
            },
            permission_settings={
                'config.yaml': 0o644,
                'gtach.service': 0o644,
                '.env': 0o600
            },
            validation_rules={
                'required_files': ['config.yaml'],
                'max_fps_limit': 30,
                'min_bluetooth_timeout': 5.0
            }
        )
        
        # macOS configuration (development)
        configs['macos'] = PlatformConfig(
            platform_name='macos',
            template_variables={
                'app_dir': '~/.local/gtach',
                'log_dir': '~/Library/Logs/gtach',
                'config_dir': '~/.config/gtach',
                'user': 'user',
                'group': 'staff', 
                'python_executable': 'python3',
                'gpio_available': False,
                'display_hardware': False,
                'performance_profile': 'development',
                'fps_limit': 60,
                'bluetooth_timeout': 5.0,
                'service_enabled': False
            },
            file_mappings={
                'config.template.yaml': 'config.yaml',
                'environment.template': '.env'
            },
            permission_settings={
                'config.yaml': 0o644,
                '.env': 0o600
            },
            validation_rules={
                'required_files': ['config.yaml'],
                'max_fps_limit': 120,
                'min_bluetooth_timeout': 1.0
            }
        )
        
        # Generic Linux configuration
        configs['linux'] = PlatformConfig(
            platform_name='linux',
            template_variables={
                'app_dir': '/usr/local/gtach',
                'log_dir': '/var/log/gtach',
                'config_dir': '/etc/gtach',
                'user': 'gtach',
                'group': 'gtach',
                'python_executable': 'python3',
                'gpio_available': False,
                'display_hardware': True,
                'performance_profile': 'standard',
                'fps_limit': 60,
                'bluetooth_timeout': 8.0,
                'service_enabled': True
            },
            file_mappings={
                'config.template.yaml': 'config.yaml',
                'service.template': 'gtach.service', 
                'environment.template': '.env'
            },
            permission_settings={
                'config.yaml': 0o644,
                'gtach.service': 0o644,
                '.env': 0o600
            },
            validation_rules={
                'required_files': ['config.yaml'],
                'max_fps_limit': 60,
                'min_bluetooth_timeout': 3.0
            }
        )
        
        return configs
    
    def process_templates(self, 
                         template_dir: Path, 
                         output_dir: Path,
                         additional_variables: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Process all configuration templates in directory.
        
        Args:
            template_dir: Directory containing template files
            output_dir: Output directory for processed files
            additional_variables: Optional additional template variables
            
        Returns:
            List of processed output file paths (relative)
            
        Raises:
            RuntimeError: If template processing fails
        """
        with self._processing_lock:
            self._increment_operation_count()
            
            start_time = time.perf_counter()
            processed_files = []
            
            self.logger.info(f"Processing templates from {template_dir} for {self.target_platform}")
            
            try:
                if not template_dir.exists():
                    self.logger.warning(f"Template directory does not exist: {template_dir}")
                    return processed_files
                    
                # Get platform configuration
                platform_config = self._get_platform_config()
                if not platform_config:
                    raise RuntimeError(f"No configuration available for platform: {self.target_platform}")
                
                # Prepare template variables
                template_vars = self._prepare_template_variables(platform_config, additional_variables)
                
                # Process each template file
                template_files = list(template_dir.glob('*.template*'))
                self.logger.debug(f"Found {len(template_files)} template files")
                
                for template_file in template_files:
                    try:
                        output_files = self._process_single_template(
                            template_file, output_dir, platform_config, template_vars
                        )
                        processed_files.extend(output_files)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to process template {template_file}: {e}")
                        # Continue processing other templates
                        
                # Validate processed configuration
                self._validate_processed_config(output_dir, platform_config)
                
                elapsed = time.perf_counter() - start_time
                self.logger.info(f"Processed {len(processed_files)} configuration files ({elapsed:.2f}s)")
                
                return processed_files
                
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                self.logger.error(f"Template processing failed after {elapsed:.2f}s: {e}")
                raise RuntimeError(f"Template processing failed: {e}") from e
    
    def _get_platform_config(self) -> Optional[PlatformConfig]:
        """
        Get configuration for target platform.
        
        Returns:
            Platform configuration or None if not found
        """
        return self.platform_configs.get(self.target_platform)
    
    def _prepare_template_variables(self,
                                  platform_config: PlatformConfig,
                                  additional_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare template variables from platform config and additional sources.
        
        Args:
            platform_config: Platform-specific configuration
            additional_variables: Optional additional variables
            
        Returns:
            Combined template variables dictionary
        """
        # Start with platform variables
        variables = platform_config.template_variables.copy()
        
        # Add current configuration values
        try:
            current_config = self.config_manager.load_config()
            config_vars = self._extract_config_variables(current_config)
            variables.update(config_vars)
        except Exception as e:
            self.logger.warning(f"Failed to load current configuration: {e}")
        
        # Add system information
        system_vars = self._get_system_variables()
        variables.update(system_vars)
        
        # Add additional variables (highest priority)
        if additional_variables:
            variables.update(additional_variables)
            
        self.logger.debug(f"Prepared {len(variables)} template variables")
        return variables
    
    def _extract_config_variables(self, config: OBDConfig) -> Dict[str, Any]:
        """
        Extract template variables from current configuration.
        
        Args:
            config: Current OBD configuration
            
        Returns:
            Dictionary of configuration-based variables
        """
        variables = {
            # OBD settings
            'obd_port': config.port,
            'obd_baudrate': config.baudrate,
            'obd_timeout': config.timeout,
            'obd_reconnect_attempts': config.reconnect_attempts,
            'obd_fast_mode': config.fast_mode,
            
            # Bluetooth settings
            'bt_scan_duration': config.bluetooth.scan_duration,
            'bt_retry_limit': config.bluetooth.retry_limit,
            'bt_timeout': config.bluetooth.timeout,
            'bt_bleak_timeout': config.bluetooth.bleak_timeout,
            
            # Display settings
            'display_mode': config.display.mode,
            'display_rpm_warning': config.display.rpm_warning,
            'display_rpm_danger': config.display.rpm_danger,
            'display_fps_limit': config.display.fps_limit,
            
            # Logging settings
            'debug_logging': config.debug_logging,
            'data_logging': config.data_log_enabled
        }
        
        return variables
    
    def _get_system_variables(self) -> Dict[str, Any]:
        """
        Get system-specific template variables.
        
        Returns:
            Dictionary of system variables
        """
        import platform
        from datetime import datetime
        
        variables = {
            'system_platform': platform.system(),
            'system_machine': platform.machine(),
            'python_version': platform.python_version(),
            'hostname': platform.node(),
            'generated_at': datetime.now().isoformat(),
            'source_platform': self.source_platform.name
        }
        
        # Add user information
        try:
            import getpass
            variables['current_user'] = getpass.getuser()
        except Exception:
            variables['current_user'] = 'unknown'
            
        return variables
    
    def _prepare_json_variables(self, template_vars: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare template variables for JSON substitution.
        
        Converts Python types to JSON-compatible string representations.
        
        Args:
            template_vars: Template variables dictionary
            
        Returns:
            Dictionary with JSON-compatible string values
        """
        json_vars = {}
        
        for key, value in template_vars.items():
            if isinstance(value, bool):
                # Convert Python bool to JSON bool
                json_vars[key] = 'true' if value else 'false'
            elif isinstance(value, (int, float)):
                # Convert numbers to strings (but without quotes in JSON)
                json_vars[key] = str(value)
            elif value is None:
                # Convert None to JSON null
                json_vars[key] = 'null'
            else:
                # All other values as strings
                json_vars[key] = str(value)
                
        return json_vars
    
    def _process_single_template(self,
                               template_file: Path,
                               output_dir: Path, 
                               platform_config: PlatformConfig,
                               template_vars: Dict[str, Any]) -> List[str]:
        """
        Process a single template file.
        
        Args:
            template_file: Template file to process
            output_dir: Output directory
            platform_config: Platform configuration
            template_vars: Template variables
            
        Returns:
            List of output file paths (relative)
        """
        processed_files = []
        
        # Determine output filename
        output_filename = self._get_output_filename(template_file, platform_config)
        output_path = output_dir / output_filename
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Process template based on file type
        if template_file.suffix.lower() in ['.yaml', '.yml']:
            self._process_yaml_template(template_file, output_path, template_vars)
        elif template_file.suffix.lower() == '.json':
            self._process_json_template(template_file, output_path, template_vars)
        else:
            self._process_text_template(template_file, output_path, template_vars)
        
        # Set file permissions
        self._set_file_permissions(output_path, output_filename, platform_config)
        
        # Calculate relative path for return
        try:
            rel_path = output_path.relative_to(output_dir)
            processed_files.append(str(rel_path))
        except ValueError:
            processed_files.append(output_path.name)
            
        self.logger.debug(f"Processed template: {template_file.name} -> {output_filename}")
        
        return processed_files
    
    def _get_output_filename(self, template_file: Path, platform_config: PlatformConfig) -> str:
        """
        Determine output filename from template filename and platform config.
        
        Args:
            template_file: Template file path
            platform_config: Platform configuration
            
        Returns:
            Output filename
        """
        template_name = template_file.name
        
        # Check platform-specific mappings first
        if template_name in platform_config.file_mappings:
            return platform_config.file_mappings[template_name]
            
        # Default: remove .template from filename
        if '.template' in template_name:
            return template_name.replace('.template', '')
            
        # Fallback: add .processed extension
        return f"{template_name}.processed"
    
    def _process_yaml_template(self, template_file: Path, output_path: Path, template_vars: Dict[str, Any]) -> None:
        """
        Process YAML template file.
        
        Args:
            template_file: Template file path
            output_path: Output file path
            template_vars: Template variables
        """
        if not YAML_AVAILABLE:
            self.logger.warning("YAML not available - falling back to text processing")
            self._process_text_template(template_file, output_path, template_vars)
            return
            
        # Read and process template
        with open(template_file, 'r') as f:
            template_content = f.read()
            
        # Substitute variables
        template = Template(template_content)
        processed_content = template.safe_substitute(template_vars)
        
        # Parse and validate YAML
        try:
            yaml_data = yaml.safe_load(processed_content)
            
            # Write formatted YAML
            with open(output_path, 'w') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
                
        except yaml.YAMLError as e:
            self.logger.error(f"YAML processing error in {template_file}: {e}")
            # Fallback to text processing
            with open(output_path, 'w') as f:
                f.write(processed_content)
    
    def _process_json_template(self, template_file: Path, output_path: Path, template_vars: Dict[str, Any]) -> None:
        """
        Process JSON template file.
        
        Args:
            template_file: Template file path
            output_path: Output file path
            template_vars: Template variables
        """
        # Read and process template
        with open(template_file, 'r') as f:
            template_content = f.read()
            
        # Convert variables to JSON-compatible format
        json_vars = self._prepare_json_variables(template_vars)
        
        # Substitute variables
        template = Template(template_content)
        processed_content = template.safe_substitute(json_vars)
        
        # Parse and validate JSON
        try:
            json_data = json.loads(processed_content)
            
            # Write formatted JSON
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON processing error in {template_file}: {e}")
            self.logger.debug(f"Processed content that failed JSON parsing: {processed_content}")
            # Fallback to text processing
            with open(output_path, 'w') as f:
                f.write(processed_content)
    
    def _process_text_template(self, template_file: Path, output_path: Path, template_vars: Dict[str, Any]) -> None:
        """
        Process text template file using string substitution.
        
        Args:
            template_file: Template file path
            output_path: Output file path
            template_vars: Template variables
        """
        # Read template
        with open(template_file, 'r') as f:
            template_content = f.read()
            
        # Substitute variables
        template = Template(template_content)
        processed_content = template.safe_substitute(template_vars)
        
        # Write processed content
        with open(output_path, 'w') as f:
            f.write(processed_content)
    
    def _set_file_permissions(self, file_path: Path, filename: str, platform_config: PlatformConfig) -> None:
        """
        Set appropriate file permissions based on platform configuration.
        
        Args:
            file_path: File to set permissions on
            filename: Filename for permission lookup
            platform_config: Platform configuration
        """
        # Only set permissions on Unix-like systems
        if os.name != 'posix':
            return
            
        # Get permission from platform config
        if filename in platform_config.permission_settings:
            permissions = platform_config.permission_settings[filename]
            try:
                file_path.chmod(permissions)
                self.logger.debug(f"Set permissions {oct(permissions)} on {filename}")
            except OSError as e:
                self.logger.warning(f"Failed to set permissions on {filename}: {e}")
    
    def _validate_processed_config(self, output_dir: Path, platform_config: PlatformConfig) -> None:
        """
        Validate processed configuration files.
        
        Args:
            output_dir: Directory containing processed files
            platform_config: Platform configuration with validation rules
            
        Raises:
            RuntimeError: If validation fails
        """
        validation_rules = platform_config.validation_rules
        
        # Early termination if base configuration file is not discoverable
        if self.config_file_path is None:
            raise RuntimeError("Configuration file not found - cannot create deployment packages")
        
        # Since we found the source configuration file, validation should focus on
        # processed template outputs rather than requiring config.yaml in output dir
        self.logger.info(f"Configuration validation passed - source config: {self.config_file_path}")
        
        # If any templates were processed, validate their content
        config_file = output_dir / 'config.yaml'
        if config_file.exists() and YAML_AVAILABLE:
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                self._validate_config_content(config_data, validation_rules)
                self.logger.debug("Processed configuration content validation passed")
                
            except Exception as e:
                self.logger.warning(f"Configuration content validation failed: {e}")
        else:
            # No processed config.yaml - this is fine since we have the source config
            self.logger.debug("No processed config.yaml found - using source configuration file")
    
    def _validate_config_content(self, config_data: Dict[str, Any], validation_rules: Dict[str, Any]) -> None:
        """
        Validate configuration file content against rules.
        
        Args:
            config_data: Loaded configuration data
            validation_rules: Validation rules to apply
        """
        # Validate FPS limit
        if 'max_fps_limit' in validation_rules:
            max_fps = validation_rules['max_fps_limit']
            if config_data.get('display', {}).get('fps_limit', 0) > max_fps:
                self.logger.warning(f"FPS limit exceeds platform maximum: {max_fps}")
        
        # Validate Bluetooth timeout
        if 'min_bluetooth_timeout' in validation_rules:
            min_timeout = validation_rules['min_bluetooth_timeout']
            bt_timeout = config_data.get('bluetooth', {}).get('bleak_timeout', 0)
            if bt_timeout < min_timeout:
                self.logger.warning(f"Bluetooth timeout below platform minimum: {min_timeout}")
    
    def create_platform_config_template(self, 
                                      output_path: Path,
                                      base_config: Optional[OBDConfig] = None) -> None:
        """
        Create a configuration template for the target platform.
        
        Args:
            output_path: Where to save the template
            base_config: Optional base configuration to use
        """
        if base_config is None:
            base_config = self.config_manager.load_config()
            
        platform_config = self._get_platform_config()
        if not platform_config:
            raise RuntimeError(f"No platform configuration for: {self.target_platform}")
        
        # Create template configuration
        template_config = base_config.to_dict()
        
        # Apply platform-specific adjustments
        template_vars = platform_config.template_variables
        
        # Update configuration values based on platform
        if 'display' in template_config:
            template_config['display']['fps_limit'] = template_vars.get('fps_limit', 60)
        
        if 'bluetooth' in template_config:
            template_config['bluetooth']['bleak_timeout'] = template_vars.get('bluetooth_timeout', 5.0)
        
        # Add platform-specific comments/documentation
        template_config['_platform_info'] = {
            'target_platform': self.target_platform,
            'generated_for': platform_config.platform_name,
            'performance_profile': template_vars.get('performance_profile', 'standard')
        }
        
        # Save template
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if YAML_AVAILABLE and output_path.suffix.lower() in ['.yaml', '.yml']:
            with open(output_path, 'w') as f:
                yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)
        else:
            with open(output_path, 'w') as f:
                json.dump(template_config, f, indent=2)
        
        self.logger.info(f"Created platform configuration template: {output_path}")
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get configuration processor statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._stats_lock:
            return {
                'operation_count': self._operation_count,
                'target_platform': self.target_platform,
                'source_platform': self.source_platform.name,
                'available_platforms': list(self.platform_configs.keys()),
                'cache_size': len(self._template_cache)
            }