#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Unified Platform Detection System for OBDII Display Application.

Provides consistent, reliable platform detection with conflict resolution,
GPIO availability verification, and simplified mock system.
"""

import os
import platform
import logging
import subprocess
import importlib.util
import sys
import threading
import time
from typing import Dict, Optional, Tuple, List, Any, Union, Set
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass
from collections import defaultdict


class PlatformType(Enum):
    """Enhanced platform type enumeration with Pi variants"""
    # Raspberry Pi variants
    RASPBERRY_PI_ZERO = auto()
    RASPBERRY_PI_ZERO_2W = auto()  
    RASPBERRY_PI_4 = auto()
    RASPBERRY_PI_5 = auto()
    RASPBERRY_PI_GENERIC = auto()  # Unknown Pi variant
    
    # Other platforms
    LINUX_GENERIC = auto()
    MACOS = auto()
    WINDOWS = auto()
    UNKNOWN = auto()


class DetectionMethod(Enum):
    """Available platform detection methods"""
    DEVICE_TREE = auto()
    PROC_CPUINFO = auto()
    BCM_GPIO = auto()
    SYSTEM_PLATFORM = auto()
    HARDWARE_REVISION = auto()


@dataclass
class DetectionResult:
    """Result from a single detection method"""
    method: DetectionMethod
    platform_type: PlatformType
    confidence: float  # 0.0 to 1.0
    evidence: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class PlatformCapabilities:
    """Platform capability information"""
    gpio_available: bool = False
    gpio_accessible: bool = False  # Can actually use GPIO
    gpio_permissions: bool = False
    display_hardware: bool = False
    bluetooth_available: bool = False
    i2c_available: bool = False
    spi_available: bool = False


class MockRegistry:
    """Simplified mock system using registry pattern"""
    
    def __init__(self):
        self.logger = logging.getLogger('MockRegistry')
        self._mocks: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def register_mock(self, module_name: str, mock_instance: Any) -> None:
        """Register a mock for a module"""
        with self._lock:
            self._mocks[module_name] = mock_instance
            self.logger.debug(f"Registered mock for {module_name}")
    
    def get_mock(self, module_name: str) -> Optional[Any]:
        """Get registered mock for module"""
        with self._lock:
            return self._mocks.get(module_name)
    
    def has_mock(self, module_name: str) -> bool:
        """Check if mock is registered"""
        with self._lock:
            return module_name in self._mocks
    
    def list_mocks(self) -> List[str]:
        """List all registered mocks"""
        with self._lock:
            return list(self._mocks.keys())
    
    def clear_mocks(self) -> None:
        """Clear all registered mocks"""
        with self._lock:
            self._mocks.clear()
            self.logger.debug("Cleared all registered mocks")


class PlatformDetector:
    """
    Unified platform detection with conflict resolution and capability verification.
    
    Features:
    - Weighted detection method scoring
    - Conflict resolution algorithm
    - Actual GPIO accessibility testing
    - Result caching with thread safety
    - Raspberry Pi variant detection
    - Simplified mock system
    """
    
    def __init__(self):
        self.logger = logging.getLogger('PlatformDetector')
        self._lock = threading.RLock()
        
        # Cached results
        self._platform_type: Optional[PlatformType] = None
        self._capabilities: Optional[PlatformCapabilities] = None
        self._detection_results: List[DetectionResult] = []
        self._last_detection_time: float = 0
        self._cache_duration: float = 300.0  # 5 minutes
        
        # Mock system
        self.mock_registry = MockRegistry()
        self._initialize_default_mocks()
        
        # Detection method weights (higher = more reliable)
        self._method_weights = {
            DetectionMethod.DEVICE_TREE: 1.0,
            DetectionMethod.HARDWARE_REVISION: 0.9,
            DetectionMethod.PROC_CPUINFO: 0.8,
            DetectionMethod.BCM_GPIO: 0.6,
            DetectionMethod.SYSTEM_PLATFORM: 0.4
        }
    
    def _initialize_default_mocks(self) -> None:
        """Initialize default mock implementations"""
        self.mock_registry.register_mock('RPi.GPIO', self._create_gpio_mock())
        self.mock_registry.register_mock('hyperpixel2r', self._create_hyperpixel_mock())
        self.mock_registry.register_mock('pygame', self._create_pygame_mock())
    
    def get_platform_type(self, force_refresh: bool = False) -> PlatformType:
        """
        Get platform type with conflict resolution.
        
        Args:
            force_refresh: Force new detection, ignore cache
            
        Returns:
            PlatformType: Detected platform with highest confidence
        """
        with self._lock:
            current_time = time.time()
            
            # Check cache validity
            if (not force_refresh and 
                self._platform_type is not None and 
                (current_time - self._last_detection_time) < self._cache_duration):
                return self._platform_type
            
            try:
                # Run all detection methods
                results = self._run_all_detections()
                
                # Apply conflict resolution
                resolved_type = self._resolve_conflicts(results)
                
                # Cache results
                self._platform_type = resolved_type
                self._detection_results = results
                self._last_detection_time = current_time
                
                self.logger.info(f"Platform detected as: {resolved_type.name}")
                return resolved_type
                
            except Exception as e:
                self.logger.error(f"Platform detection failed: {e}")
                return PlatformType.UNKNOWN
    
    def _run_all_detections(self) -> List[DetectionResult]:
        """Run all detection methods and collect results"""
        results = []
        
        # Device tree detection
        try:
            result = self._detect_via_device_tree()
            if result:
                results.append(result)
        except Exception as e:
            self.logger.debug(f"Device tree detection failed: {e}")
        
        # Hardware revision detection (Pi-specific)
        try:
            result = self._detect_via_hardware_revision()
            if result:
                results.append(result)
        except Exception as e:
            self.logger.debug(f"Hardware revision detection failed: {e}")
        
        # CPU info detection
        try:
            result = self._detect_via_cpuinfo()
            if result:
                results.append(result)
        except Exception as e:
            self.logger.debug(f"CPU info detection failed: {e}")
        
        # BCM GPIO detection
        try:
            result = self._detect_via_bcm_gpio()
            if result:
                results.append(result)
        except Exception as e:
            self.logger.debug(f"BCM GPIO detection failed: {e}")
        
        # System platform detection
        try:
            result = self._detect_via_system_platform()
            if result:
                results.append(result)
        except Exception as e:
            self.logger.debug(f"System platform detection failed: {e}")
        
        return results
    
    def _detect_via_device_tree(self) -> Optional[DetectionResult]:
        """Detect platform via device tree model"""
        try:
            model_path = Path('/proc/device-tree/model')
            if not model_path.exists():
                return None
            
            with open(model_path, 'r', encoding='utf-8') as f:
                model = f.read().strip().rstrip('\x00')
            
            evidence = {'device_tree_model': model}
            
            # Parse specific Pi variants
            model_lower = model.lower()
            if 'raspberry pi zero 2' in model_lower:
                return DetectionResult(
                    DetectionMethod.DEVICE_TREE,
                    PlatformType.RASPBERRY_PI_ZERO_2W,
                    1.0,
                    evidence
                )
            elif 'raspberry pi zero' in model_lower:
                return DetectionResult(
                    DetectionMethod.DEVICE_TREE,
                    PlatformType.RASPBERRY_PI_ZERO,
                    1.0,
                    evidence
                )
            elif 'raspberry pi 5' in model_lower:
                return DetectionResult(
                    DetectionMethod.DEVICE_TREE,
                    PlatformType.RASPBERRY_PI_5,
                    1.0,
                    evidence
                )
            elif 'raspberry pi 4' in model_lower:
                return DetectionResult(
                    DetectionMethod.DEVICE_TREE,
                    PlatformType.RASPBERRY_PI_4,
                    1.0,
                    evidence
                )
            elif 'raspberry pi' in model_lower:
                return DetectionResult(
                    DetectionMethod.DEVICE_TREE,
                    PlatformType.RASPBERRY_PI_GENERIC,
                    0.9,
                    evidence
                )
            
            return None
            
        except Exception as e:
            return DetectionResult(
                DetectionMethod.DEVICE_TREE,
                PlatformType.UNKNOWN,
                0.0,
                {},
                str(e)
            )
    
    def _detect_via_hardware_revision(self) -> Optional[DetectionResult]:
        """Detect Pi variant via hardware revision code"""
        try:
            cpuinfo_path = Path('/proc/cpuinfo')
            if not cpuinfo_path.exists():
                return None
            
            revision = None
            with open(cpuinfo_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('Revision'):
                        revision = line.split(':', 1)[1].strip()
                        break
            
            if not revision:
                return None
            
            evidence = {'hardware_revision': revision}
            
            # Pi revision code mapping (simplified)
            revision_map = {
                # Pi Zero 2W
                '902120': PlatformType.RASPBERRY_PI_ZERO_2W,
                
                # Pi Zero variants
                '900092': PlatformType.RASPBERRY_PI_ZERO,
                '900093': PlatformType.RASPBERRY_PI_ZERO,
                '920092': PlatformType.RASPBERRY_PI_ZERO,
                '920093': PlatformType.RASPBERRY_PI_ZERO,
                
                # Pi 4 variants
                'a03111': PlatformType.RASPBERRY_PI_4,
                'b03111': PlatformType.RASPBERRY_PI_4,
                'b03112': PlatformType.RASPBERRY_PI_4,
                'b03114': PlatformType.RASPBERRY_PI_4,
                'c03111': PlatformType.RASPBERRY_PI_4,
                'c03112': PlatformType.RASPBERRY_PI_4,
                'c03114': PlatformType.RASPBERRY_PI_4,
                'd03114': PlatformType.RASPBERRY_PI_4,
                
                # Pi 5 variants
                'c04170': PlatformType.RASPBERRY_PI_5,
                'd04170': PlatformType.RASPBERRY_PI_5,
            }
            
            # Clean revision (remove overvoltage bit)
            clean_revision = revision.lstrip('1000')
            
            platform_type = revision_map.get(clean_revision)
            if platform_type:
                return DetectionResult(
                    DetectionMethod.HARDWARE_REVISION,
                    platform_type,
                    0.95,
                    evidence
                )
            
            # Unknown revision but Pi-like format
            if len(clean_revision) == 6 and clean_revision.isalnum():
                return DetectionResult(
                    DetectionMethod.HARDWARE_REVISION,
                    PlatformType.RASPBERRY_PI_GENERIC,
                    0.7,
                    evidence
                )
            
            return None
            
        except Exception as e:
            return DetectionResult(
                DetectionMethod.HARDWARE_REVISION,
                PlatformType.UNKNOWN,
                0.0,
                {},
                str(e)
            )
    
    def _detect_via_cpuinfo(self) -> Optional[DetectionResult]:
        """Detect platform via CPU info"""
        try:
            cpuinfo_path = Path('/proc/cpuinfo')
            if not cpuinfo_path.exists():
                return None
            
            with open(cpuinfo_path, 'r', encoding='utf-8') as f:
                cpuinfo = f.read().lower()
            
            evidence = {'cpuinfo_checked': True}
            
            # Check for Pi indicators
            pi_indicators = ['raspberry pi', 'bcm2835', 'bcm2836', 'bcm2837', 'bcm2711', 'bcm2710']
            
            for indicator in pi_indicators:
                if indicator in cpuinfo:
                    evidence['found_indicator'] = indicator
                    return DetectionResult(
                        DetectionMethod.PROC_CPUINFO,
                        PlatformType.RASPBERRY_PI_GENERIC,
                        0.8,
                        evidence
                    )
            
            return None
            
        except Exception as e:
            return DetectionResult(
                DetectionMethod.PROC_CPUINFO,
                PlatformType.UNKNOWN,
                0.0,
                {},
                str(e)
            )
    
    def _detect_via_bcm_gpio(self) -> Optional[DetectionResult]:
        """Detect platform via BCM GPIO characteristics"""
        try:
            evidence = {}
            
            # Check for BCM GPIO memory mapping
            iomem_path = Path('/proc/iomem')
            if iomem_path.exists():
                with open(iomem_path, 'r') as f:
                    iomem = f.read().lower()
                
                bcm_indicators = [
                    'bcm2835-gpio', 'bcm2836-gpio', 'bcm2837-gpio', 'bcm2711-gpio',
                    'gpio@7e200000', 'gpio@fe200000'
                ]
                
                for indicator in bcm_indicators:
                    if indicator in iomem:
                        evidence['bcm_gpio_indicator'] = indicator
                        return DetectionResult(
                            DetectionMethod.BCM_GPIO,
                            PlatformType.RASPBERRY_PI_GENERIC,
                            0.6,
                            evidence
                        )
            
            return None
            
        except Exception as e:
            return DetectionResult(
                DetectionMethod.BCM_GPIO,
                PlatformType.UNKNOWN,
                0.0,
                {},
                str(e)
            )
    
    def _detect_via_system_platform(self) -> Optional[DetectionResult]:
        """Detect platform via Python platform module"""
        try:
            system = platform.system()
            machine = platform.machine()
            
            evidence = {
                'system': system,
                'machine': machine,
                'platform': platform.platform()
            }
            
            if system == 'Darwin':
                return DetectionResult(
                    DetectionMethod.SYSTEM_PLATFORM,
                    PlatformType.MACOS,
                    0.9,
                    evidence
                )
            elif system == 'Windows':
                return DetectionResult(
                    DetectionMethod.SYSTEM_PLATFORM,
                    PlatformType.WINDOWS,
                    0.9,
                    evidence
                )
            elif system == 'Linux':
                # Check if it might be Pi based on architecture
                if machine in ['armv6l', 'armv7l', 'aarch64']:
                    return DetectionResult(
                        DetectionMethod.SYSTEM_PLATFORM,
                        PlatformType.RASPBERRY_PI_GENERIC,
                        0.3,  # Low confidence, needs other evidence
                        evidence
                    )
                else:
                    return DetectionResult(
                        DetectionMethod.SYSTEM_PLATFORM,
                        PlatformType.LINUX_GENERIC,
                        0.8,
                        evidence
                    )
            
            return DetectionResult(
                DetectionMethod.SYSTEM_PLATFORM,
                PlatformType.UNKNOWN,
                0.1,
                evidence
            )
            
        except Exception as e:
            return DetectionResult(
                DetectionMethod.SYSTEM_PLATFORM,
                PlatformType.UNKNOWN,
                0.0,
                {},
                str(e)
            )
    
    def _resolve_conflicts(self, results: List[DetectionResult]) -> PlatformType:
        """
        Resolve conflicts between detection methods using weighted scoring.
        
        Args:
            results: List of detection results
            
        Returns:
            PlatformType: Platform with highest weighted confidence
        """
        if not results:
            return PlatformType.UNKNOWN
        
        # Calculate weighted scores for each platform type
        platform_scores: Dict[PlatformType, float] = defaultdict(float)
        
        for result in results:
            if result.error:
                continue  # Skip failed detections
            
            method_weight = self._method_weights.get(result.method, 0.5)
            weighted_score = result.confidence * method_weight
            platform_scores[result.platform_type] += weighted_score
        
        if not platform_scores:
            return PlatformType.UNKNOWN
        
        # Find platform with highest score
        best_platform = max(platform_scores.items(), key=lambda x: x[1])
        
        self.logger.debug(f"Platform scoring results: {dict(platform_scores)}")
        self.logger.debug(f"Selected platform: {best_platform[0].name} (score: {best_platform[1]:.2f})")
        
        return best_platform[0]
    
    def check_gpio_availability(self, force_refresh: bool = False) -> PlatformCapabilities:
        """
        Check actual GPIO availability, not just presence.
        
        Args:
            force_refresh: Force new check, ignore cache
            
        Returns:
            PlatformCapabilities: Detailed capability information
        """
        with self._lock:
            current_time = time.time()
            
            # Check cache validity
            if (not force_refresh and 
                self._capabilities is not None and 
                (current_time - self._last_detection_time) < self._cache_duration):
                return self._capabilities
            
            capabilities = PlatformCapabilities()
            
            try:
                # Check GPIO device presence
                capabilities.gpio_available = self._check_gpio_devices()
                
                # Check actual GPIO accessibility
                if capabilities.gpio_available:
                    capabilities.gpio_accessible = self._test_gpio_access()
                    capabilities.gpio_permissions = self._check_gpio_permissions()
                
                # Check other hardware interfaces
                capabilities.display_hardware = self._check_display_hardware()
                capabilities.bluetooth_available = self._check_bluetooth_availability()
                capabilities.i2c_available = self._check_i2c_availability()
                capabilities.spi_available = self._check_spi_availability()
                
                self._capabilities = capabilities
                return capabilities
                
            except Exception as e:
                self.logger.error(f"GPIO availability check failed: {e}")
                return PlatformCapabilities()  # All False
    
    def _check_gpio_devices(self) -> bool:
        """Check if GPIO devices exist"""
        gpio_paths = [
            '/sys/class/gpio',
            '/dev/gpiochip0',
            '/dev/gpiochip1'
        ]
        
        for path in gpio_paths:
            if Path(path).exists():
                self.logger.debug(f"GPIO device found: {path}")
                return True
        
        return False
    
    def _test_gpio_access(self) -> bool:
        """Test actual GPIO access without hardware modification"""
        try:
            # Method 1: Try to access GPIO via sysfs (non-destructive)
            gpio_path = Path('/sys/class/gpio')
            if gpio_path.exists():
                try:
                    # Check if we can read GPIO chip info
                    chips = list(gpio_path.glob('gpiochip*'))
                    if chips:
                        # Try to read chip information
                        chip = chips[0]
                        base_file = chip / 'base'
                        ngpio_file = chip / 'ngpio'
                        
                        if base_file.exists() and ngpio_file.exists():
                            with open(base_file, 'r') as f:
                                base = f.read().strip()
                            with open(ngpio_file, 'r') as f:
                                ngpio = f.read().strip()
                            
                            if base.isdigit() and ngpio.isdigit():
                                self.logger.debug(f"GPIO chip readable: base={base}, ngpio={ngpio}")
                                return True
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"GPIO sysfs access failed: {e}")
            
            # Method 2: Try character device access
            dev_path = Path('/dev')
            gpio_devs = list(dev_path.glob('gpiochip*'))
            if gpio_devs:
                # Just check if we can stat the device
                for dev in gpio_devs[:1]:  # Check first device only
                    try:
                        stat = dev.stat()
                        if stat.st_mode:  # Device exists and stat-able
                            self.logger.debug(f"GPIO character device accessible: {dev}")
                            return True
                    except (OSError, PermissionError) as e:
                        self.logger.debug(f"GPIO chardev access failed: {e}")
            
            return False
            
        except Exception as e:
            self.logger.debug(f"GPIO access test failed: {e}")
            return False
    
    def _check_gpio_permissions(self) -> bool:
        """Check if current user has GPIO permissions"""
        try:
            import pwd
            import grp
            
            # Check if user is in gpio group
            username = pwd.getpwuid(os.getuid()).pw_name
            try:
                gpio_group = grp.getgrnam('gpio')
                if username in gpio_group.gr_mem:
                    self.logger.debug(f"User {username} is in gpio group")
                    return True
            except KeyError:
                self.logger.debug("No gpio group found")
            
            # Check if running as root
            if os.getuid() == 0:
                self.logger.debug("Running as root, GPIO permissions likely available")
                return True
            
            # Check specific device permissions
            gpio_devs = list(Path('/dev').glob('gpiochip*'))
            for dev in gpio_devs:
                try:
                    if os.access(dev, os.R_OK | os.W_OK):
                        self.logger.debug(f"Have R/W access to {dev}")
                        return True
                except OSError:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"GPIO permission check failed: {e}")
            return False
    
    def _check_display_hardware(self) -> bool:
        """Check for display hardware presence"""
        display_indicators = [
            '/dev/fb0',
            '/dev/fb1',
            '/sys/class/graphics/fb0'
        ]
        
        for indicator in display_indicators:
            if Path(indicator).exists():
                self.logger.debug(f"Display hardware found: {indicator}")
                return True
        
        return False
    
    def _check_bluetooth_availability(self) -> bool:
        """Check for Bluetooth availability"""
        bt_indicators = [
            '/sys/class/bluetooth',
            '/dev/rfkill'
        ]
        
        for indicator in bt_indicators:
            if Path(indicator).exists():
                return True
        
        # Check via system command
        try:
            result = subprocess.run(['which', 'bluetoothctl'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_i2c_availability(self) -> bool:
        """Check for I2C availability"""
        i2c_indicators = [
            '/dev/i2c-0',
            '/dev/i2c-1',
            '/sys/class/i2c-adapter'
        ]
        
        for indicator in i2c_indicators:
            if Path(indicator).exists():
                return True
        
        return False
    
    def _check_spi_availability(self) -> bool:
        """Check for SPI availability"""
        spi_indicators = [
            '/dev/spidev0.0',
            '/dev/spidev0.1',
            '/sys/class/spi_master'
        ]
        
        for indicator in spi_indicators:
            if Path(indicator).exists():
                return True
        
        return False
    
    def is_raspberry_pi(self) -> bool:
        """Check if running on any Raspberry Pi variant"""
        platform_type = self.get_platform_type()
        return platform_type in [
            PlatformType.RASPBERRY_PI_ZERO,
            PlatformType.RASPBERRY_PI_ZERO_2W,
            PlatformType.RASPBERRY_PI_4,
            PlatformType.RASPBERRY_PI_5,
            PlatformType.RASPBERRY_PI_GENERIC
        ]
    
    def is_gpio_available(self) -> bool:
        """Check if GPIO is available and accessible"""
        capabilities = self.check_gpio_availability()
        return capabilities.gpio_available and capabilities.gpio_accessible
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get comprehensive platform information"""
        platform_type = self.get_platform_type()
        capabilities = self.check_gpio_availability()
        
        info = {
            'platform_type': platform_type.name,
            'is_raspberry_pi': self.is_raspberry_pi(),
            'pi_variant': self._get_pi_variant_name(platform_type),
            'capabilities': {
                'gpio_available': capabilities.gpio_available,
                'gpio_accessible': capabilities.gpio_accessible,
                'gpio_permissions': capabilities.gpio_permissions,
                'display_hardware': capabilities.display_hardware,
                'bluetooth_available': capabilities.bluetooth_available,
                'i2c_available': capabilities.i2c_available,
                'spi_available': capabilities.spi_available
            },
            'system_info': {
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'architecture': platform.architecture()[0],
                'python_version': platform.python_version()
            },
            'detection_methods': [
                {
                    'method': result.method.name,
                    'platform': result.platform_type.name,
                    'confidence': result.confidence,
                    'evidence': result.evidence,
                    'error': result.error
                }
                for result in self._detection_results
            ],
            'cache_info': {
                'last_detection_time': self._last_detection_time,
                'cache_age_seconds': time.time() - self._last_detection_time if self._last_detection_time else 0
            }
        }
        
        return info
    
    def _get_pi_variant_name(self, platform_type: PlatformType) -> str:
        """Get human-readable Pi variant name"""
        variant_names = {
            PlatformType.RASPBERRY_PI_ZERO: "Raspberry Pi Zero",
            PlatformType.RASPBERRY_PI_ZERO_2W: "Raspberry Pi Zero 2W",
            PlatformType.RASPBERRY_PI_4: "Raspberry Pi 4",
            PlatformType.RASPBERRY_PI_5: "Raspberry Pi 5",
            PlatformType.RASPBERRY_PI_GENERIC: "Raspberry Pi (Unknown Variant)"
        }
        return variant_names.get(platform_type, "Not a Raspberry Pi")
    
    def import_module_with_mock(self, module_name: str, 
                               required_attrs: Optional[List[str]] = None) -> Tuple[Any, bool]:
        """
        Import module with automatic mock fallback.
        
        Args:
            module_name: Module to import
            required_attrs: Required attributes to validate
            
        Returns:
            Tuple of (module, is_real)
        """
        try:
            # Try real import
            module = importlib.import_module(module_name)
            
            # Validate required attributes
            if required_attrs:
                missing = [attr for attr in required_attrs if not hasattr(module, attr)]
                if missing:
                    raise ImportError(f"Module {module_name} missing: {missing}")
            
            self.logger.debug(f"Successfully imported real {module_name}")
            return module, True
            
        except ImportError as e:
            # Try mock fallback
            mock = self.mock_registry.get_mock(module_name)
            if mock:
                self.logger.info(f"Using mock for {module_name}: {e}")
                return mock, False
            else:
                self.logger.error(f"No mock available for {module_name}: {e}")
                raise
    
    def clear_cache(self) -> None:
        """Clear cached detection results"""
        with self._lock:
            self._platform_type = None
            self._capabilities = None
            self._detection_results = []
            self._last_detection_time = 0
            self.logger.debug("Platform detection cache cleared")
    
    def _create_gpio_mock(self):
        """Create GPIO mock implementation"""
        class MockGPIO:
            BCM = "BCM"
            BOARD = "BOARD"
            OUT = "OUT"
            IN = "IN"
            HIGH = 1
            LOW = 0
            PUD_UP = "PUD_UP"
            PUD_DOWN = "PUD_DOWN"
            PUD_OFF = "PUD_OFF"
            
            @staticmethod
            def setmode(mode): pass
            
            @staticmethod
            def setwarnings(warnings): pass
            
            @staticmethod
            def setup(pin, mode, **kwargs): pass
            
            @staticmethod
            def output(pin, state): pass
            
            @staticmethod
            def input(pin): return False
            
            @staticmethod
            def cleanup(): pass
        
        return MockGPIO()
    
    def _create_hyperpixel_mock(self):
        """Create HyperPixel mock implementation"""
        class MockHyperPixel:
            class MockTouch:
                def __init__(self):
                    self.running = False
                
                def setup_callback(self, callback): pass
                def start(self): self.running = True
                def stop(self): self.running = False
                def is_running(self): return self.running
            
            @staticmethod
            def get_touch():
                return MockHyperPixel.MockTouch()
        
        return MockHyperPixel()
    
    def _create_pygame_mock(self):
        """Create pygame mock implementation"""
        class MockPygame:
            class MockDisplay:
                @staticmethod
                def init(): return True
                @staticmethod
                def set_mode(size, **kwargs): return MockPygame.MockSurface(size)
                @staticmethod
                def flip(): pass
                @staticmethod
                def update(): pass
            
            class MockSurface:
                def __init__(self, size): self.size = size
                def fill(self, color): pass
                def blit(self, surface, pos): pass
                def get_rect(self): return MockPygame.MockRect(0, 0, *self.size)
            
            class MockRect:
                def __init__(self, x, y, w, h):
                    self.x, self.y, self.width, self.height = x, y, w, h
                def collidepoint(self, x, y):
                    return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height
            
            @staticmethod
            def init(): return True, 0
            @staticmethod
            def quit(): pass
            
            display = MockDisplay()
        
        return MockPygame()


# Global instance with thread-safe initialization
_detector_lock = threading.Lock()
_detector_instance: Optional[PlatformDetector] = None


def get_detector() -> PlatformDetector:
    """Get global detector instance with thread-safe initialization"""
    global _detector_instance
    
    if _detector_instance is None:
        with _detector_lock:
            if _detector_instance is None:
                _detector_instance = PlatformDetector()
    
    return _detector_instance


# Public API functions
def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi hardware"""
    try:
        return get_detector().is_raspberry_pi()
    except Exception as e:
        logger = logging.getLogger('platform.is_raspberry_pi')
        logger.debug(f"Exception in Pi detection: {e}")
        return False


def is_gpio_available() -> bool:
    """Check if GPIO is available and accessible"""
    try:
        return get_detector().is_gpio_available()
    except Exception as e:
        logger = logging.getLogger('platform.is_gpio_available')
        logger.debug(f"Exception in GPIO detection: {e}")
        return False


def get_platform_type() -> PlatformType:
    """Get detected platform type"""
    try:
        return get_detector().get_platform_type()
    except Exception as e:
        logger = logging.getLogger('platform.get_platform_type')
        logger.debug(f"Exception in platform detection: {e}")
        return PlatformType.UNKNOWN


def get_platform_info() -> Dict[str, Any]:
    """Get comprehensive platform information"""
    try:
        return get_detector().get_platform_info()
    except Exception as e:
        logger = logging.getLogger('platform.get_platform_info')
        logger.debug(f"Exception in platform info: {e}")
        return {'error': str(e), 'platform_type': 'UNKNOWN'}


def check_gpio_availability() -> PlatformCapabilities:
    """Check detailed GPIO availability"""
    try:
        return get_detector().check_gpio_availability()
    except Exception as e:
        logger = logging.getLogger('platform.check_gpio_availability')
        logger.debug(f"Exception in GPIO availability check: {e}")
        return PlatformCapabilities()


def import_module_with_mock(module_name: str, 
                          required_attrs: Optional[List[str]] = None) -> Tuple[Any, bool]:
    """Import module with automatic mock fallback"""
    try:
        return get_detector().import_module_with_mock(module_name, required_attrs)
    except Exception as e:
        logger = logging.getLogger('platform.import_module_with_mock')
        logger.error(f"Module import failed: {module_name}: {e}")
        raise


def clear_detection_cache() -> None:
    """Clear platform detection cache"""
    try:
        get_detector().clear_cache()
    except Exception as e:
        logger = logging.getLogger('platform.clear_detection_cache')
        logger.debug(f"Exception clearing cache: {e}")


def log_platform_info(level: int = logging.INFO) -> None:
    """Log comprehensive platform information"""
    try:
        logger = logging.getLogger('platform')
        info = get_platform_info()
        
        logger.log(level, "=== Unified Platform Detection ===")
        logger.log(level, f"Platform: {info.get('platform_type', 'UNKNOWN')}")
        logger.log(level, f"Pi Variant: {info.get('pi_variant', 'N/A')}")
        
        caps = info.get('capabilities', {})
        logger.log(level, f"GPIO Available: {caps.get('gpio_available', False)}")
        logger.log(level, f"GPIO Accessible: {caps.get('gpio_accessible', False)}")
        logger.log(level, f"GPIO Permissions: {caps.get('gpio_permissions', False)}")
        
        cache_info = info.get('cache_info', {})
        logger.log(level, f"Cache Age: {cache_info.get('cache_age_seconds', 0):.1f}s")
        
    except Exception as e:
        logger = logging.getLogger('platform.log_platform_info')
        logger.error(f"Exception logging platform info: {e}")


# Legacy compatibility - simplified
class PlatformError(Exception):
    """Platform detection error"""
    pass


# For testing purposes
def run_platform_test():
    """Run platform detection test"""
    print("=== Platform Detection Test ===")
    
    try:
        detector = get_detector()
        
        # Force fresh detection
        platform_type = detector.get_platform_type(force_refresh=True)
        print(f"Platform Type: {platform_type.name}")
        
        # Check capabilities
        capabilities = detector.check_gpio_availability(force_refresh=True)
        print(f"GPIO Available: {capabilities.gpio_available}")
        print(f"GPIO Accessible: {capabilities.gpio_accessible}")
        print(f"GPIO Permissions: {capabilities.gpio_permissions}")
        
        # Show detection details
        info = detector.get_platform_info()
        print(f"\nDetection Methods:")
        for method in info.get('detection_methods', []):
            print(f"  {method['method']}: {method['platform']} "
                  f"(conf: {method['confidence']:.2f})")
        
        print(f"\nCapabilities:")
        caps = info.get('capabilities', {})
        for key, value in caps.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    import sys
    
    # Configure logging for test
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if "--test" in sys.argv:
        run_platform_test()
    else:
        log_platform_info()