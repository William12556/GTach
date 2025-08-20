#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Platform Service for OBDII Foundational Services Architecture

Provides consistent hardware abstraction interfaces across subsystems.
Eliminates ad-hoc platform detection patterns and provides unified capabilities.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

# Import existing platform detection system
from ..platform import (
    PlatformDetector, PlatformType, PlatformCapabilities as BasePlatformCapabilities,
    DetectionResult, DetectionMethod, get_detector
)


class PlatformServiceError(Exception):
    """Platform service specific errors"""
    pass


class HardwareInterface(Enum):
    """Available hardware interfaces"""
    GPIO = auto()
    I2C = auto()
    SPI = auto()
    BLUETOOTH = auto()
    DISPLAY = auto()
    SERIAL = auto()
    USB = auto()


@dataclass
class PlatformCapabilities:
    """Enhanced platform capabilities with service integration"""
    # Basic capabilities from existing system
    gpio_available: bool = False
    gpio_accessible: bool = False
    gpio_permissions: bool = False
    display_hardware: bool = False
    bluetooth_available: bool = False
    i2c_available: bool = False
    spi_available: bool = False
    
    # Enhanced service capabilities
    serial_ports: List[str] = field(default_factory=list)
    usb_devices: List[str] = field(default_factory=list)
    network_interfaces: List[str] = field(default_factory=list)
    system_resources: Dict[str, Any] = field(default_factory=dict)
    
    # Performance characteristics
    cpu_cores: int = 1
    memory_mb: int = 0
    storage_type: str = "unknown"
    
    # Service-specific flags
    requires_root: bool = False
    supports_concurrent_gpio: bool = False
    has_hardware_watchdog: bool = False


@dataclass
class HardwareInterfaceInfo:
    """Information about a hardware interface"""
    interface: HardwareInterface
    available: bool
    accessible: bool
    devices: List[str] = field(default_factory=list)
    permissions_required: List[str] = field(default_factory=list)
    service_ready: bool = False
    last_check: float = field(default_factory=time.time)
    error_message: Optional[str] = None


class PlatformService:
    """
    Unified platform abstraction service.
    
    Provides:
    - Consistent hardware interface detection
    - Platform capability assessment
    - Hardware resource management
    - Cross-subsystem platform coordination
    - Performance-optimized platform queries
    """
    
    def __init__(self, detector: Optional[PlatformDetector] = None):
        """
        Initialize platform service.
        
        Args:
            detector: Optional existing PlatformDetector instance
        """
        self.logger = logging.getLogger('PlatformService')
        
        # Use provided detector or get global instance
        self._detector = detector or get_detector()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Cached platform information
        self._platform_type: Optional[PlatformType] = None
        self._capabilities: Optional[PlatformCapabilities] = None
        self._hardware_interfaces: Dict[HardwareInterface, HardwareInterfaceInfo] = {}
        
        # Cache management
        self._cache_timestamp: float = 0
        self._cache_duration: float = 300.0  # 5 minutes
        
        # Performance monitoring
        self._operation_count = 0
        self._interface_checks = 0
        self._performance_lock = threading.Lock()
        
        # Hardware change callbacks
        self._change_callbacks: List[Callable[[HardwareInterface, bool], None]] = []
        
        self.logger.debug("PlatformService initialized")
    
    def get_platform_type(self, force_refresh: bool = False) -> PlatformType:
        """
        Get detected platform type.
        
        Args:
            force_refresh: Force new detection
            
        Returns:
            Detected platform type
        """
        with self._lock:
            if force_refresh or self._platform_type is None:
                self._platform_type = self._detector.get_platform_type(force_refresh)
                self.logger.debug(f"Platform type detected: {self._platform_type.name}")
            
            return self._platform_type
    
    def get_capabilities(self, force_refresh: bool = False) -> PlatformCapabilities:
        """
        Get comprehensive platform capabilities.
        
        Args:
            force_refresh: Force new capability check
            
        Returns:
            Platform capabilities
        """
        with self._lock:
            current_time = time.time()
            cache_age = current_time - self._cache_timestamp
            
            if (force_refresh or 
                self._capabilities is None or 
                cache_age > self._cache_duration):
                
                self._capabilities = self._detect_capabilities()
                self._cache_timestamp = current_time
                self.logger.debug("Platform capabilities refreshed")
            
            return self._capabilities
    
    def _detect_capabilities(self) -> PlatformCapabilities:
        """Detect comprehensive platform capabilities"""
        try:
            # Get basic capabilities from existing detector
            base_caps = self._detector.check_gpio_availability(force_refresh=True)
            
            # Create enhanced capabilities
            capabilities = PlatformCapabilities(
                gpio_available=base_caps.gpio_available,
                gpio_accessible=base_caps.gpio_accessible,
                gpio_permissions=base_caps.gpio_permissions,
                display_hardware=base_caps.display_hardware,
                bluetooth_available=base_caps.bluetooth_available,
                i2c_available=base_caps.i2c_available,
                spi_available=base_caps.spi_available
            )
            
            # Detect additional capabilities
            self._detect_serial_ports(capabilities)
            self._detect_usb_devices(capabilities)
            self._detect_network_interfaces(capabilities)
            self._detect_system_resources(capabilities)
            self._detect_service_flags(capabilities)
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Error detecting capabilities: {e}")
            return PlatformCapabilities()  # Return empty capabilities on error
    
    def _detect_serial_ports(self, capabilities: PlatformCapabilities) -> None:
        """Detect available serial ports"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            capabilities.serial_ports = [port.device for port in ports]
            self.logger.debug(f"Found {len(capabilities.serial_ports)} serial ports")
        except ImportError:
            self.logger.debug("PySerial not available for port detection")
        except Exception as e:
            self.logger.debug(f"Error detecting serial ports: {e}")
    
    def _detect_usb_devices(self, capabilities: PlatformCapabilities) -> None:
        """Detect USB devices"""
        try:
            from pathlib import Path
            usb_path = Path('/sys/bus/usb/devices')
            if usb_path.exists():
                devices = [d.name for d in usb_path.iterdir() if d.is_dir()]
                capabilities.usb_devices = devices
                self.logger.debug(f"Found {len(devices)} USB devices")
        except Exception as e:
            self.logger.debug(f"Error detecting USB devices: {e}")
    
    def _detect_network_interfaces(self, capabilities: PlatformCapabilities) -> None:
        """Detect network interfaces"""
        try:
            import socket
            import subprocess
            
            # Try to get interface names via system command
            result = subprocess.run(['ls', '/sys/class/net'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                capabilities.network_interfaces = result.stdout.strip().split('\n')
                self.logger.debug(f"Found {len(capabilities.network_interfaces)} network interfaces")
        except Exception as e:
            self.logger.debug(f"Error detecting network interfaces: {e}")
    
    def _detect_system_resources(self, capabilities: PlatformCapabilities) -> None:
        """Detect system resource information"""
        try:
            import os
            import psutil
            
            # CPU information
            capabilities.cpu_cores = os.cpu_count() or 1
            
            # Memory information
            memory = psutil.virtual_memory()
            capabilities.memory_mb = int(memory.total / (1024 * 1024))
            
            # Storage information
            disk = psutil.disk_usage('/')
            capabilities.system_resources = {
                'disk_total_gb': int(disk.total / (1024**3)),
                'disk_free_gb': int(disk.free / (1024**3)),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            self.logger.debug(f"System resources: {capabilities.cpu_cores} cores, {capabilities.memory_mb}MB RAM")
            
        except ImportError:
            self.logger.debug("psutil not available for system resource detection")
        except Exception as e:
            self.logger.debug(f"Error detecting system resources: {e}")
    
    def _detect_service_flags(self, capabilities: PlatformCapabilities) -> None:
        """Detect service-specific capability flags"""
        try:
            import os
            from pathlib import Path
            
            # Check if running as root
            capabilities.requires_root = (os.getuid() == 0) if hasattr(os, 'getuid') else False
            
            # Check for hardware watchdog
            watchdog_paths = ['/dev/watchdog', '/dev/watchdog0']
            capabilities.has_hardware_watchdog = any(Path(p).exists() for p in watchdog_paths)
            
            # Platform-specific flags
            platform_type = self.get_platform_type()
            if platform_type in [PlatformType.RASPBERRY_PI_4, PlatformType.RASPBERRY_PI_5]:
                capabilities.supports_concurrent_gpio = True
                capabilities.storage_type = "microsd"
            elif platform_type == PlatformType.MACOS:
                capabilities.storage_type = "ssd"
            
            self.logger.debug(f"Service flags: root={capabilities.requires_root}, "
                            f"watchdog={capabilities.has_hardware_watchdog}")
            
        except Exception as e:
            self.logger.debug(f"Error detecting service flags: {e}")
    
    def check_hardware_interface(self, interface: HardwareInterface, force_refresh: bool = False) -> HardwareInterfaceInfo:
        """
        Check specific hardware interface availability.
        
        Args:
            interface: Hardware interface to check
            force_refresh: Force new check
            
        Returns:
            Hardware interface information
        """
        with self._lock:
            current_time = time.time()
            
            # Check cache
            if (not force_refresh and 
                interface in self._hardware_interfaces and
                current_time - self._hardware_interfaces[interface].last_check < 60.0):
                return self._hardware_interfaces[interface]
            
            # Perform interface check
            with self._performance_lock:
                self._interface_checks += 1
            
            info = self._check_interface(interface)
            info.last_check = current_time
            self._hardware_interfaces[interface] = info
            
            return info
    
    def _check_interface(self, interface: HardwareInterface) -> HardwareInterfaceInfo:
        """Check specific hardware interface"""
        try:
            if interface == HardwareInterface.GPIO:
                return self._check_gpio_interface()
            elif interface == HardwareInterface.I2C:
                return self._check_i2c_interface()
            elif interface == HardwareInterface.SPI:
                return self._check_spi_interface()
            elif interface == HardwareInterface.BLUETOOTH:
                return self._check_bluetooth_interface()
            elif interface == HardwareInterface.DISPLAY:
                return self._check_display_interface()
            elif interface == HardwareInterface.SERIAL:
                return self._check_serial_interface()
            elif interface == HardwareInterface.USB:
                return self._check_usb_interface()
            else:
                return HardwareInterfaceInfo(
                    interface=interface,
                    available=False,
                    accessible=False,
                    error_message="Unknown interface type"
                )
                
        except Exception as e:
            return HardwareInterfaceInfo(
                interface=interface,
                available=False,
                accessible=False,
                error_message=str(e)
            )
    
    def _check_gpio_interface(self) -> HardwareInterfaceInfo:
        """Check GPIO interface"""
        capabilities = self.get_capabilities()
        
        devices = []
        permissions = []
        
        if capabilities.gpio_available:
            devices.extend(['/dev/gpiochip0', '/sys/class/gpio'])
        
        if not capabilities.gpio_permissions:
            permissions.extend(['gpio group membership', 'root privileges'])
        
        return HardwareInterfaceInfo(
            interface=HardwareInterface.GPIO,
            available=capabilities.gpio_available,
            accessible=capabilities.gpio_accessible,
            devices=devices,
            permissions_required=permissions,
            service_ready=capabilities.gpio_accessible and capabilities.gpio_permissions
        )
    
    def _check_i2c_interface(self) -> HardwareInterfaceInfo:
        """Check I2C interface"""
        from pathlib import Path
        
        devices = []
        available = False
        accessible = False
        
        # Check for I2C devices
        for i in range(10):  # Check i2c-0 through i2c-9
            device_path = Path(f'/dev/i2c-{i}')
            if device_path.exists():
                devices.append(str(device_path))
                available = True
                
                # Check accessibility
                try:
                    import os
                    if os.access(device_path, os.R_OK | os.W_OK):
                        accessible = True
                except OSError:
                    pass
        
        permissions = ['i2c group membership'] if available and not accessible else []
        
        return HardwareInterfaceInfo(
            interface=HardwareInterface.I2C,
            available=available,
            accessible=accessible,
            devices=devices,
            permissions_required=permissions,
            service_ready=available and accessible
        )
    
    def _check_spi_interface(self) -> HardwareInterfaceInfo:
        """Check SPI interface"""
        from pathlib import Path
        
        devices = []
        available = False
        accessible = False
        
        # Check for SPI devices
        spi_patterns = ['/dev/spidev0.0', '/dev/spidev0.1', '/dev/spidev1.0']
        for pattern in spi_patterns:
            device_path = Path(pattern)
            if device_path.exists():
                devices.append(str(device_path))
                available = True
                
                # Check accessibility
                try:
                    import os
                    if os.access(device_path, os.R_OK | os.W_OK):
                        accessible = True
                except OSError:
                    pass
        
        permissions = ['spi group membership'] if available and not accessible else []
        
        return HardwareInterfaceInfo(
            interface=HardwareInterface.SPI,
            available=available,
            accessible=accessible,
            devices=devices,
            permissions_required=permissions,
            service_ready=available and accessible
        )
    
    def _check_bluetooth_interface(self) -> HardwareInterfaceInfo:
        """Check Bluetooth interface"""
        capabilities = self.get_capabilities()
        
        devices = []
        if capabilities.bluetooth_available:
            devices.extend(['/sys/class/bluetooth', '/dev/rfkill'])
        
        return HardwareInterfaceInfo(
            interface=HardwareInterface.BLUETOOTH,
            available=capabilities.bluetooth_available,
            accessible=capabilities.bluetooth_available,  # Assume accessible if available
            devices=devices,
            service_ready=capabilities.bluetooth_available
        )
    
    def _check_display_interface(self) -> HardwareInterfaceInfo:
        """Check display interface"""
        capabilities = self.get_capabilities()
        
        devices = []
        if capabilities.display_hardware:
            devices.extend(['/dev/fb0', '/sys/class/graphics/fb0'])
        
        return HardwareInterfaceInfo(
            interface=HardwareInterface.DISPLAY,
            available=capabilities.display_hardware,
            accessible=capabilities.display_hardware,
            devices=devices,
            service_ready=capabilities.display_hardware
        )
    
    def _check_serial_interface(self) -> HardwareInterfaceInfo:
        """Check serial interface"""
        capabilities = self.get_capabilities()
        
        return HardwareInterfaceInfo(
            interface=HardwareInterface.SERIAL,
            available=len(capabilities.serial_ports) > 0,
            accessible=True,  # Assume accessible
            devices=capabilities.serial_ports,
            service_ready=len(capabilities.serial_ports) > 0
        )
    
    def _check_usb_interface(self) -> HardwareInterfaceInfo:
        """Check USB interface"""
        capabilities = self.get_capabilities()
        
        return HardwareInterfaceInfo(
            interface=HardwareInterface.USB,
            available=len(capabilities.usb_devices) > 0,
            accessible=True,  # Assume accessible
            devices=capabilities.usb_devices,
            service_ready=len(capabilities.usb_devices) > 0
        )
    
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        return self._detector.is_raspberry_pi()
    
    def is_gpio_available(self) -> bool:
        """Check if GPIO is available and accessible"""
        gpio_info = self.check_hardware_interface(HardwareInterface.GPIO)
        return gpio_info.service_ready
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get comprehensive platform information"""
        platform_type = self.get_platform_type()
        capabilities = self.get_capabilities()
        
        # Get hardware interface status
        interface_status = {}
        for interface in HardwareInterface:
            info = self.check_hardware_interface(interface)
            interface_status[interface.name.lower()] = {
                'available': info.available,
                'accessible': info.accessible,
                'service_ready': info.service_ready,
                'devices': info.devices,
                'permissions_required': info.permissions_required
            }
        
        return {
            'platform_type': platform_type.name,
            'is_raspberry_pi': self.is_raspberry_pi(),
            'capabilities': {
                'cpu_cores': capabilities.cpu_cores,
                'memory_mb': capabilities.memory_mb,
                'storage_type': capabilities.storage_type,
                'requires_root': capabilities.requires_root,
                'supports_concurrent_gpio': capabilities.supports_concurrent_gpio,
                'has_hardware_watchdog': capabilities.has_hardware_watchdog
            },
            'hardware_interfaces': interface_status,
            'system_resources': capabilities.system_resources,
            'serial_ports': capabilities.serial_ports,
            'network_interfaces': capabilities.network_interfaces,
            'cache_info': {
                'cache_age': time.time() - self._cache_timestamp,
                'cache_duration': self._cache_duration
            }
        }
    
    def add_hardware_change_callback(self, callback: Callable[[HardwareInterface, bool], None]) -> None:
        """
        Add callback for hardware availability changes.
        
        Args:
            callback: Function to call when hardware status changes
        """
        with self._lock:
            self._change_callbacks.append(callback)
            self.logger.debug("Added hardware change callback")
    
    def _notify_hardware_change(self, interface: HardwareInterface, available: bool) -> None:
        """Notify callbacks of hardware changes"""
        for callback in self._change_callbacks:
            try:
                callback(interface, available)
            except Exception as e:
                self.logger.error(f"Error in hardware change callback: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached platform information"""
        with self._lock:
            self._platform_type = None
            self._capabilities = None
            self._hardware_interfaces.clear()
            self._cache_timestamp = 0
            self.logger.debug("Platform service cache cleared")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get platform service statistics"""
        with self._lock:
            with self._performance_lock:
                return {
                    'operation_count': self._operation_count,
                    'interface_checks': self._interface_checks,
                    'cached_interfaces': len(self._hardware_interfaces),
                    'change_callbacks': len(self._change_callbacks),
                    'cache_age': time.time() - self._cache_timestamp if self._cache_timestamp else 0
                }
    
    def get_detector(self) -> PlatformDetector:
        """Get underlying platform detector"""
        return self._detector