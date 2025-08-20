#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Dependency Service for OBDII Foundational Services Architecture

Provides runtime capability assessment and validation across subsystems.
Eliminates ad-hoc dependency checking patterns with unified validation.
"""

import logging
import threading
import time
import importlib
from typing import Dict, Any, Optional, List, Callable, Union, Set
from dataclasses import dataclass, field
from enum import Enum, auto

# Import existing dependency system
from ..dependencies import DependencyValidator, ValidationResult, DependencyType, ValidationReport


class CapabilityStatus(Enum):
    """Runtime capability status"""
    AVAILABLE = auto()
    UNAVAILABLE = auto()
    DEGRADED = auto()
    UNKNOWN = auto()


class CapabilityCategory(Enum):
    """Categories of runtime capabilities"""
    CORE = auto()           # Core Python functionality
    PLATFORM = auto()       # Platform-specific features
    HARDWARE = auto()       # Hardware interfaces
    OPTIONAL = auto()       # Optional enhancements
    DEVELOPMENT = auto()    # Development tools


@dataclass
class CapabilityResult:
    """Result of capability assessment"""
    name: str
    category: CapabilityCategory
    status: CapabilityStatus
    available: bool
    version: Optional[str] = None
    error_message: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    last_check: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubsystemCapabilities:
    """Capabilities summary for a subsystem"""
    name: str
    core_available: bool
    platform_available: bool
    hardware_available: bool
    optional_count: int
    degraded_features: List[str] = field(default_factory=list)
    missing_critical: List[str] = field(default_factory=list)
    can_operate: bool = True


class DependencyService:
    """
    Runtime dependency and capability assessment service.
    
    Provides:
    - Real-time capability validation
    - Subsystem dependency coordination
    - Graceful degradation assessment
    - Alternative capability discovery
    - Cross-subsystem dependency tracking
    """
    
    def __init__(self, validator: Optional[DependencyValidator] = None):
        """
        Initialize dependency service.
        
        Args:
            validator: Optional existing DependencyValidator instance
        """
        self.logger = logging.getLogger('DependencyService')
        
        # Use provided validator or create new one
        self._validator = validator or DependencyValidator(debug=False)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Capability tracking
        self._capabilities: Dict[str, CapabilityResult] = {}
        self._subsystem_capabilities: Dict[str, SubsystemCapabilities] = {}
        
        # Cache management
        self._last_full_check: float = 0
        self._cache_duration: float = 300.0  # 5 minutes
        
        # Capability change callbacks
        self._change_callbacks: List[Callable[[str, CapabilityStatus], None]] = []
        
        # Performance monitoring
        self._check_count = 0
        self._performance_lock = threading.Lock()
        
        # Capability definitions
        self._capability_definitions = self._define_capabilities()
        
        self.logger.debug("DependencyService initialized")
    
    def _define_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Define runtime capability assessments"""
        return {
            # Core capabilities
            'python_stdlib': {
                'category': CapabilityCategory.CORE,
                'imports': ['os', 'sys', 'threading', 'logging', 'time'],
                'required': True,
                'description': 'Python standard library'
            },
            
            'yaml_support': {
                'category': CapabilityCategory.CORE,
                'imports': ['yaml'],
                'required': True,
                'alternatives': ['json'],
                'description': 'Configuration file support'
            },
            
            # Platform capabilities
            'gpio_control': {
                'category': CapabilityCategory.PLATFORM,
                'imports': ['RPi.GPIO'],
                'platform_required': ['raspberry_pi'],
                'hardware_check': 'gpio',
                'description': 'GPIO hardware control'
            },
            
            'display_rendering': {
                'category': CapabilityCategory.PLATFORM,
                'imports': ['pygame'],
                'required': True,
                'description': 'Graphics and display rendering'
            },
            
            # Hardware capabilities
            'bluetooth_comm': {
                'category': CapabilityCategory.HARDWARE,
                'imports': ['bluetooth', 'bleak'],
                'alternatives': ['bleak'],
                'description': 'Bluetooth communication'
            },
            
            'serial_comm': {
                'category': CapabilityCategory.HARDWARE,
                'imports': ['serial'],
                'required': True,
                'description': 'Serial communication for OBD-II'
            },
            
            'hyperpixel_display': {
                'category': CapabilityCategory.HARDWARE,
                'imports': ['hyperpixel2r'],
                'platform_required': ['raspberry_pi'],
                'description': 'HyperPixel display support'
            },
            
            # Optional capabilities
            'advanced_graphics': {
                'category': CapabilityCategory.OPTIONAL,
                'imports': ['PIL', 'numpy'],
                'description': 'Advanced graphics processing'
            },
            
            'system_monitoring': {
                'category': CapabilityCategory.OPTIONAL,
                'imports': ['psutil'],
                'description': 'System resource monitoring'
            },
            
            # Development capabilities
            'development_tools': {
                'category': CapabilityCategory.DEVELOPMENT,
                'imports': ['requests', 'pytest'],
                'development_only': True,
                'description': 'Development and testing tools'
            }
        }
    
    def assess_capability(self, capability_name: str, force_refresh: bool = False) -> CapabilityResult:
        """
        Assess specific runtime capability.
        
        Args:
            capability_name: Name of capability to assess
            force_refresh: Force new assessment
            
        Returns:
            Capability assessment result
        """
        with self._lock:
            current_time = time.time()
            
            # Check cache
            if (not force_refresh and 
                capability_name in self._capabilities and
                current_time - self._capabilities[capability_name].last_check < 60.0):
                return self._capabilities[capability_name]
            
            # Perform capability assessment
            with self._performance_lock:
                self._check_count += 1
            
            result = self._check_capability(capability_name)
            result.last_check = current_time
            
            # Update cache and notify changes
            old_result = self._capabilities.get(capability_name)
            self._capabilities[capability_name] = result
            
            if old_result and old_result.status != result.status:
                self._notify_capability_change(capability_name, result.status)
            
            return result
    
    def _check_capability(self, capability_name: str) -> CapabilityResult:
        """Check specific capability"""
        try:
            definition = self._capability_definitions.get(capability_name)
            if not definition:
                return CapabilityResult(
                    name=capability_name,
                    category=CapabilityCategory.UNKNOWN,
                    status=CapabilityStatus.UNKNOWN,
                    available=False,
                    error_message="Unknown capability"
                )
            
            # Check platform requirements
            if not self._check_platform_requirements(definition):
                return CapabilityResult(
                    name=capability_name,
                    category=definition['category'],
                    status=CapabilityStatus.UNAVAILABLE,
                    available=False,
                    error_message="Platform requirements not met"
                )
            
            # Check development-only requirements
            if definition.get('development_only', False) and not self._is_development_environment():
                return CapabilityResult(
                    name=capability_name,
                    category=definition['category'],
                    status=CapabilityStatus.UNAVAILABLE,
                    available=False,
                    error_message="Development-only capability in production"
                )
            
            # Check imports
            import_results = self._check_imports(definition.get('imports', []))
            
            # Check hardware requirements
            hardware_available = self._check_hardware_requirements(definition)
            
            # Determine overall status
            if import_results['all_available'] and hardware_available:
                status = CapabilityStatus.AVAILABLE
                available = True
                error_message = None
            elif import_results['some_available'] or self._has_alternatives(definition):
                status = CapabilityStatus.DEGRADED
                available = True
                error_message = "Some features may be limited"
            else:
                status = CapabilityStatus.UNAVAILABLE
                available = False
                error_message = import_results['error_message'] or "Capability not available"
            
            return CapabilityResult(
                name=capability_name,
                category=definition['category'],
                status=status,
                available=available,
                version=import_results.get('version'),
                error_message=error_message,
                alternatives=definition.get('alternatives', []),
                dependencies=definition.get('imports', []),
                metadata={
                    'import_results': import_results,
                    'hardware_available': hardware_available,
                    'platform_checked': True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error checking capability {capability_name}: {e}")
            return CapabilityResult(
                name=capability_name,
                category=CapabilityCategory.UNKNOWN,
                status=CapabilityStatus.UNKNOWN,
                available=False,
                error_message=str(e)
            )
    
    def _check_platform_requirements(self, definition: Dict[str, Any]) -> bool:
        """Check if platform requirements are met"""
        platform_required = definition.get('platform_required', [])
        if not platform_required:
            return True
        
        try:
            # Get platform info from validator
            platform_info = self._validator.platform_info
            
            for requirement in platform_required:
                if requirement == 'raspberry_pi' and not platform_info.get('is_raspberry_pi', False):
                    return False
                elif requirement == 'linux' and not platform_info.get('is_linux', False):
                    return False
                elif requirement == 'macos' and not platform_info.get('is_macos', False):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Error checking platform requirements: {e}")
            return False
    
    def _check_imports(self, imports: List[str]) -> Dict[str, Any]:
        """Check import availability"""
        results = {
            'all_available': True,
            'some_available': False,
            'available_imports': [],
            'failed_imports': [],
            'version': None,
            'error_message': None
        }
        
        for import_name in imports:
            try:
                module = importlib.import_module(import_name)
                results['available_imports'].append(import_name)
                results['some_available'] = True
                
                # Try to get version
                if not results['version']:
                    for attr in ['__version__', 'version', 'VERSION']:
                        if hasattr(module, attr):
                            version = getattr(module, attr)
                            if callable(version):
                                version = version()
                            results['version'] = str(version)
                            break
                            
            except ImportError as e:
                results['failed_imports'].append(import_name)
                results['all_available'] = False
                if not results['error_message']:
                    results['error_message'] = str(e)
        
        return results
    
    def _check_hardware_requirements(self, definition: Dict[str, Any]) -> bool:
        """Check hardware requirements"""
        hardware_check = definition.get('hardware_check')
        if not hardware_check:
            return True
        
        try:
            # This would integrate with PlatformService when available
            # For now, do basic checks
            if hardware_check == 'gpio':
                from pathlib import Path
                return Path('/sys/class/gpio').exists()
            elif hardware_check == 'bluetooth':
                from pathlib import Path
                return Path('/sys/class/bluetooth').exists()
            elif hardware_check == 'display':
                from pathlib import Path
                return Path('/dev/fb0').exists()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Error checking hardware requirement {hardware_check}: {e}")
            return False
    
    def _has_alternatives(self, definition: Dict[str, Any]) -> bool:
        """Check if capability has available alternatives"""
        alternatives = definition.get('alternatives', [])
        if not alternatives:
            return False
        
        for alt in alternatives:
            try:
                importlib.import_module(alt)
                return True
            except ImportError:
                continue
        
        return False
    
    def _is_development_environment(self) -> bool:
        """Check if running in development environment"""
        return self._validator.platform_info.get('is_development', False)
    
    def assess_all_capabilities(self, force_refresh: bool = False) -> Dict[str, CapabilityResult]:
        """
        Assess all defined capabilities.
        
        Args:
            force_refresh: Force refresh of all capabilities
            
        Returns:
            Dictionary of capability results
        """
        with self._lock:
            current_time = time.time()
            
            # Check if full refresh is needed
            if (not force_refresh and 
                self._capabilities and
                current_time - self._last_full_check < self._cache_duration):
                return self._capabilities.copy()
            
            self.logger.debug("Performing full capability assessment")
            
            # Assess all capabilities
            for capability_name in self._capability_definitions.keys():
                self.assess_capability(capability_name, force_refresh=True)
            
            self._last_full_check = current_time
            return self._capabilities.copy()
    
    def assess_subsystem_capabilities(self, subsystem_name: str, 
                                   required_capabilities: List[str],
                                   optional_capabilities: Optional[List[str]] = None) -> SubsystemCapabilities:
        """
        Assess capabilities for a specific subsystem.
        
        Args:
            subsystem_name: Name of subsystem
            required_capabilities: List of required capability names
            optional_capabilities: List of optional capability names
            
        Returns:
            Subsystem capability assessment
        """
        with self._lock:
            optional_capabilities = optional_capabilities or []
            
            # Assess required capabilities
            missing_critical = []
            degraded_features = []
            core_available = True
            platform_available = True
            hardware_available = True
            
            for cap_name in required_capabilities:
                result = self.assess_capability(cap_name)
                
                if result.status == CapabilityStatus.UNAVAILABLE:
                    missing_critical.append(cap_name)
                    if result.category == CapabilityCategory.CORE:
                        core_available = False
                    elif result.category == CapabilityCategory.PLATFORM:
                        platform_available = False
                    elif result.category == CapabilityCategory.HARDWARE:
                        hardware_available = False
                        
                elif result.status == CapabilityStatus.DEGRADED:
                    degraded_features.append(cap_name)
            
            # Assess optional capabilities
            optional_count = 0
            for cap_name in optional_capabilities:
                result = self.assess_capability(cap_name)
                if result.status in [CapabilityStatus.AVAILABLE, CapabilityStatus.DEGRADED]:
                    optional_count += 1
                elif result.status == CapabilityStatus.DEGRADED:
                    degraded_features.append(cap_name)
            
            # Determine if subsystem can operate
            can_operate = len(missing_critical) == 0
            
            subsystem_caps = SubsystemCapabilities(
                name=subsystem_name,
                core_available=core_available,
                platform_available=platform_available,
                hardware_available=hardware_available,
                optional_count=optional_count,
                degraded_features=degraded_features,
                missing_critical=missing_critical,
                can_operate=can_operate
            )
            
            self._subsystem_capabilities[subsystem_name] = subsystem_caps
            return subsystem_caps
    
    def get_capability_summary(self) -> Dict[str, Any]:
        """Get summary of all capability assessments"""
        capabilities = self.assess_all_capabilities()
        
        summary = {
            'total_capabilities': len(capabilities),
            'available': 0,
            'degraded': 0,
            'unavailable': 0,
            'unknown': 0,
            'by_category': {cat.name: {'available': 0, 'total': 0} for cat in CapabilityCategory},
            'critical_missing': [],
            'degraded_features': []
        }
        
        for result in capabilities.values():
            # Count by status
            if result.status == CapabilityStatus.AVAILABLE:
                summary['available'] += 1
            elif result.status == CapabilityStatus.DEGRADED:
                summary['degraded'] += 1
                summary['degraded_features'].append(result.name)
            elif result.status == CapabilityStatus.UNAVAILABLE:
                summary['unavailable'] += 1
                if result.category in [CapabilityCategory.CORE, CapabilityCategory.PLATFORM]:
                    summary['critical_missing'].append(result.name)
            else:
                summary['unknown'] += 1
            
            # Count by category
            cat_name = result.category.name
            summary['by_category'][cat_name]['total'] += 1
            if result.status == CapabilityStatus.AVAILABLE:
                summary['by_category'][cat_name]['available'] += 1
        
        return summary
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing critical dependencies"""
        capabilities = self.assess_all_capabilities()
        missing = []
        
        for result in capabilities.values():
            if (result.status == CapabilityStatus.UNAVAILABLE and 
                result.category in [CapabilityCategory.CORE, CapabilityCategory.PLATFORM]):
                missing.extend(result.dependencies)
        
        return list(set(missing))  # Remove duplicates
    
    def can_system_operate(self) -> bool:
        """Check if system can operate with current capabilities"""
        capabilities = self.assess_all_capabilities()
        
        # Check for critical missing capabilities
        for result in capabilities.values():
            if (result.status == CapabilityStatus.UNAVAILABLE and 
                result.category == CapabilityCategory.CORE):
                return False
        
        return True
    
    def add_capability_change_callback(self, callback: Callable[[str, CapabilityStatus], None]) -> None:
        """
        Add callback for capability status changes.
        
        Args:
            callback: Function to call when capability status changes
        """
        with self._lock:
            self._change_callbacks.append(callback)
            self.logger.debug("Added capability change callback")
    
    def _notify_capability_change(self, capability_name: str, new_status: CapabilityStatus) -> None:
        """Notify callbacks of capability changes"""
        for callback in self._change_callbacks:
            try:
                callback(capability_name, new_status)
            except Exception as e:
                self.logger.error(f"Error in capability change callback: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached capability assessments"""
        with self._lock:
            self._capabilities.clear()
            self._subsystem_capabilities.clear()
            self._last_full_check = 0
            self.logger.debug("Dependency service cache cleared")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get dependency service statistics"""
        with self._lock:
            with self._performance_lock:
                return {
                    'check_count': self._check_count,
                    'cached_capabilities': len(self._capabilities),
                    'cached_subsystems': len(self._subsystem_capabilities),
                    'change_callbacks': len(self._change_callbacks),
                    'last_full_check_age': time.time() - self._last_full_check if self._last_full_check else 0,
                    'defined_capabilities': len(self._capability_definitions)
                }
    
    def get_validator(self) -> DependencyValidator:
        """Get underlying dependency validator"""
        return self._validator