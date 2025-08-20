#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Bluetooth pairing operations for OBDII display application.
Handles device discovery, pairing, and connection testing.
"""

import logging
import threading
import time
import signal
import concurrent.futures
from typing import List, Optional, Callable
from datetime import datetime

# Try to import PyBluez, fall back to system-level implementation  
try:
    import bluetooth
    BLUETOOTH_BACKEND = 'pybluez'
except ImportError:
    try:
        from . import system_bluetooth as bluetooth
        BLUETOOTH_BACKEND = 'system'
    except ImportError:
        bluetooth = None
        BLUETOOTH_BACKEND = 'none'

from ..display.setup_models import BluetoothDevice, PairingStatus, DeviceType
from ..utils import ConfigManager

class BluetoothPairing:
    """Manages Bluetooth device discovery and pairing operations with timeout protection"""
    
    def __init__(self, config_manager: ConfigManager = None):
        self.logger = logging.getLogger('BluetoothPairing')
        self._config_manager = config_manager or ConfigManager()
        self._discovery_thread = None
        
        # Load timeout configuration from YAML file directly  
        try:
            # Load raw YAML config for pairing timeouts
            import yaml
            with open(self._config_manager.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            pairing_config = raw_config.get('bluetooth', {}).get('pairing', {})
            
            self.discovery_timeout = pairing_config.get('discovery_timeout', 30)
            self.connection_timeout = pairing_config.get('connection_timeout', 10) 
            self.lookup_timeout = pairing_config.get('lookup_timeout', 5)
            self.initialization_timeout = pairing_config.get('initialization_timeout', 15)
            self.operation_timeout = pairing_config.get('operation_timeout', 30)
        except Exception as e:
            self.logger.warning(f"Could not load pairing timeouts from config: {e}")
            # Use default timeouts
            self.discovery_timeout = 30
            self.connection_timeout = 10
            self.lookup_timeout = 5
            self.initialization_timeout = 15
            self.operation_timeout = 30
        
        self.logger.info(f"Pairing timeouts: discovery={self.discovery_timeout}s, connection={self.connection_timeout}s")
        
        # Thread pool for timeout operations
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix='BluetoothPairing')
        
        # Check bluetooth availability with timeout protection
        try:
            future = self._executor.submit(self._check_bluetooth_availability)
            self.bluetooth_available = future.result(timeout=self.initialization_timeout)
        except concurrent.futures.TimeoutError:
            self.logger.error(f"Bluetooth initialization timed out after {self.initialization_timeout}s")
            self.bluetooth_available = False
        except Exception as e:
            self.logger.error(f"Bluetooth initialization failed: {e}")
            self.bluetooth_available = False
            
        self._pairing_thread = None
        self._discovery_active = False
        self._pairing_active = False
        self._cancel_discovery = threading.Event()
        self._cancel_pairing = threading.Event()
        
    def _check_bluetooth_availability(self) -> bool:
        """Check bluetooth availability in separate thread with timeout protection"""
        try:
            if bluetooth is None:
                self.logger.warning("No Bluetooth backend available - pairing will use mock functionality")
                return False
            else:
                self.logger.info(f"Using Bluetooth backend: {BLUETOOTH_BACKEND}")
                return True
        except Exception as e:
            self.logger.error(f"Bluetooth availability check failed: {e}")
            return False
    
    def discover_elm327_devices(self, timeout: int = None, 
                               progress_callback: Optional[Callable[[float], None]] = None,
                               device_found_callback: Optional[Callable[[BluetoothDevice], None]] = None,
                               show_all_devices: bool = False) -> List[BluetoothDevice]:
        """
        Discover ELM327 devices with progress reporting
        
        Args:
            timeout: Discovery timeout in seconds
            progress_callback: Called with progress percentage (0.0-1.0)
            device_found_callback: Called when a device is found
            show_all_devices: If True, show all devices; if False, show only likely ELM327 devices
            
        Returns:
            List of discovered ELM327 devices
        """
        # Use configured or provided timeout
        if timeout is None:
            timeout = self.discovery_timeout
            
        devices = []
        self._discovery_active = True
        self._cancel_discovery.clear()
        
        try:
            mode_desc = "all devices" if show_all_devices else "ELM327 devices"
            self.logger.info(f"Starting {mode_desc} discovery (timeout: {timeout}s)")
            
            # Start discovery in chunks to provide progress updates
            chunk_duration = 4  # Discovery chunk duration
            chunks = max(1, timeout // chunk_duration)
            
            for chunk in range(chunks):
                if self._cancel_discovery.is_set():
                    self.logger.info("Discovery cancelled")
                    break
                
                # Report progress
                progress = chunk / chunks
                if progress_callback:
                    progress_callback(progress)
                
                try:
                    # Discover devices for this chunk with timeout protection
                    future = self._executor.submit(
                        bluetooth.discover_devices,
                        duration=min(chunk_duration, self.discovery_timeout // chunks),
                        lookup_names=True,
                        flush_cache=True
                    )
                    try:
                        nearby_devices = future.result(timeout=chunk_duration + 5)
                    except concurrent.futures.TimeoutError:
                        self.logger.warning(f"Bluetooth discovery chunk {chunk+1} timed out")
                        nearby_devices = []
                    
                    # Process all discovered devices
                    for addr, name in nearby_devices:
                        try:
                            # Classify device
                            device_classification = self._classify_device(name)
                            
                            # Apply filtering based on discovery mode
                            if not show_all_devices and device_classification == DeviceType.UNKNOWN:
                                continue
                            
                            # Get signal strength (RSSI)
                            signal_strength = self._get_signal_strength(addr)
                            
                            # Determine device type string for backward compatibility
                            if device_classification == DeviceType.HIGHLY_LIKELY_ELM327:
                                device_type = 'ELM327'
                            elif device_classification == DeviceType.POSSIBLY_COMPATIBLE:
                                device_type = 'Compatible'
                            else:
                                device_type = 'Unknown'
                            
                            device = BluetoothDevice(
                                name=name or f"Unknown Device ({addr})",
                                mac_address=addr,
                                signal_strength=signal_strength,
                                device_type=device_type,
                                last_seen=datetime.now(),
                                is_paired=False,
                                connection_verified=False,
                                device_classification=device_classification
                            )
                            
                            # Check if device already found
                            if device not in devices:
                                devices.append(device)
                                self.logger.info(f"Found {device_type} device: {name} ({addr})")
                                
                                if device_found_callback:
                                    device_found_callback(device)
                            
                        except Exception as e:
                            self.logger.warning(f"Error processing device {name}: {e}")
                
                except bluetooth.BluetoothError as e:
                    self.logger.error(f"Bluetooth discovery error: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected discovery error: {e}")
                    break
            
            # Final progress update
            if progress_callback:
                progress_callback(1.0)
                
            self.logger.info(f"Discovery complete. Found {len(devices)} devices")
            
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")
        finally:
            self._discovery_active = False
        
        return devices
    
    def _classify_device(self, device_name: str) -> DeviceType:
        """Classify device based on name to determine ELM327 compatibility"""
        if not device_name:
            return DeviceType.UNKNOWN
        
        name_upper = device_name.upper()
        
        # Highly likely ELM327 devices - explicit ELM327 indicators
        highly_likely_indicators = [
            'ELM327', 'ELM', 'OBDII', 'OBD-II', 'OBD2', 'OBD', 
            'SCAN', 'DIAGNOSTIC', 'AUTO', 'CAR', 'VEHICLE',
            'TORQUE', 'VGATE', 'FOSEAL', 'KONNWEI', 'ANCEL',
            'OBDLINK', 'SCANTOOL', 'VEEPEAK', 'BAFX', 'PANLONG'
        ]
        
        # Possibly compatible devices - common Bluetooth modules used in ELM327 devices
        possibly_compatible_indicators = [
            'HC-05', 'HC-06', 'HC-03', 'HC-07', 'HC-08', 'HC-09',
            'SPP-CA', 'SPP-CB', 'SPP-CC', 'SPP-CD', 'SPP-CE', 'SPP-CF',
            'LINVOR', 'JDY-', 'AT-09', 'DSD TECH', 'WAVGAT',
            'SERIAL', 'BLUETOOTH', 'BT-', 'UART', 'TTL'
        ]
        
        # Check for highly likely ELM327 devices first
        if any(indicator in name_upper for indicator in highly_likely_indicators):
            return DeviceType.HIGHLY_LIKELY_ELM327
        
        # Check for possibly compatible devices
        if any(indicator in name_upper for indicator in possibly_compatible_indicators):
            return DeviceType.POSSIBLY_COMPATIBLE
        
        # Check for numeric patterns that might indicate ELM327 devices
        # Many generic ELM327 devices use patterns like "OBDII-1234" or "BT-1234"
        import re
        numeric_patterns = [
            r'.*-\d{4}',  # Pattern like "OBDII-1234" or "BT-5678"
            r'V\d+\.\d+',  # Version patterns like "V1.5" or "V2.1"
            r'^\d{6}$',    # 6-digit numbers (common in cheap ELM327 devices)
        ]
        
        for pattern in numeric_patterns:
            if re.search(pattern, name_upper):
                return DeviceType.POSSIBLY_COMPATIBLE
        
        return DeviceType.UNKNOWN
    
    def _is_elm327_device(self, device_name: str) -> bool:
        """Legacy method for backward compatibility"""
        classification = self._classify_device(device_name)
        return classification in [DeviceType.HIGHLY_LIKELY_ELM327, DeviceType.POSSIBLY_COMPATIBLE]
    
    def _get_signal_strength(self, mac_address: str) -> int:
        """Get approximate signal strength for a device"""
        try:
            # This is a simplified approach - actual RSSI requires platform-specific code
            # For now, return a default value
            return -50  # Reasonable default RSSI
        except Exception:
            return -80  # Weak signal default
    
    def pair_device(self, device: BluetoothDevice, 
                   status_callback: Optional[Callable[[PairingStatus, str], None]] = None) -> bool:
        """
        Pair with a Bluetooth device
        
        Args:
            device: Device to pair with
            status_callback: Called with pairing status updates
            
        Returns:
            True if pairing successful, False otherwise
        """
        self._pairing_active = True
        self._cancel_pairing.clear()
        
        try:
            self.logger.info(f"Starting pairing with {device.name} ({device.mac_address})")
            
            if status_callback:
                status_callback(PairingStatus.CONNECTING, "Connecting to device...")
            
            # Create socket and attempt connection with configurable timeout
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.settimeout(self.connection_timeout)
            
            try:
                # Attempt connection on RFCOMM channel 1 (standard for SPP)
                sock.connect((device.mac_address, 1))
                
                if status_callback:
                    status_callback(PairingStatus.TESTING, "Testing connection...")
                
                # Test basic communication
                if self._test_basic_communication(sock):
                    device.is_paired = True
                    device.connection_verified = True
                    
                    if status_callback:
                        status_callback(PairingStatus.SUCCESS, "Pairing successful!")
                    
                    self.logger.info(f"Successfully paired with {device.name}")
                    return True
                else:
                    if status_callback:
                        status_callback(PairingStatus.FAILED, "Device communication test failed")
                    
                    self.logger.error(f"Communication test failed for {device.name}")
                    return False
                    
            except bluetooth.BluetoothError as e:
                if status_callback:
                    status_callback(PairingStatus.FAILED, f"Connection failed: {str(e)}")
                
                self.logger.error(f"Bluetooth connection failed: {e}")
                return False
            finally:
                try:
                    sock.close()
                except:
                    pass
                    
        except Exception as e:
            if status_callback:
                status_callback(PairingStatus.FAILED, f"Pairing error: {str(e)}")
            
            self.logger.error(f"Pairing failed: {e}")
            return False
        finally:
            self._pairing_active = False
    
    def _test_basic_communication(self, socket: bluetooth.BluetoothSocket) -> bool:
        """Test basic communication with ELM327 device"""
        try:
            # Clear any existing data
            socket.settimeout(0.5)
            try:
                while True:
                    data = socket.recv(1024)
                    if not data:
                        break
            except:
                pass
            
            # Set longer timeout for actual commands
            socket.settimeout(3.0)
            
            # Send reset command
            socket.send(b'ATZ\r')
            response = socket.recv(1024).decode('utf-8', errors='ignore')
            
            if 'ELM' not in response:
                return False
            
            # Send echo off command
            socket.send(b'ATE0\r')
            response = socket.recv(1024).decode('utf-8', errors='ignore')
            
            # Send protocol auto command
            socket.send(b'ATSP0\r')
            response = socket.recv(1024).decode('utf-8', errors='ignore')
            
            return 'OK' in response
            
        except Exception as e:
            self.logger.error(f"Communication test error: {e}")
            return False
    
    def test_obd_connection(self, device: BluetoothDevice,
                           status_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Test OBD-II communication with a paired device
        
        Args:
            device: Device to test
            status_callback: Called with status updates
            
        Returns:
            True if OBD communication successful, False otherwise
        """
        try:
            self.logger.info(f"Testing OBD connection to {device.name}")
            
            if status_callback:
                status_callback("Connecting to device...")
            
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.settimeout(10.0)
            
            try:
                sock.connect((device.mac_address, 1))
                
                if status_callback:
                    status_callback("Testing ELM327 communication...")
                
                # Test basic ELM327 communication
                if not self._test_basic_communication(sock):
                    if status_callback:
                        status_callback("ELM327 communication failed")
                    return False
                
                if status_callback:
                    status_callback("Testing OBD-II protocol...")
                
                # Test OBD-II communication
                # Try to get vehicle identification
                sock.send(b'0100\r')  # Request supported PIDs
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                
                if '41 00' in response or 'NO DATA' in response:
                    # Either we got a valid response or expected "NO DATA" (car not running)
                    device.connection_verified = True
                    
                    if status_callback:
                        status_callback("OBD-II connection verified!")
                    
                    self.logger.info(f"OBD connection test successful for {device.name}")
                    return True
                else:
                    if status_callback:
                        status_callback("OBD-II protocol not responding")
                    
                    self.logger.error(f"OBD test failed for {device.name}: {response}")
                    return False
                    
            except bluetooth.BluetoothError as e:
                if status_callback:
                    status_callback(f"Connection error: {str(e)}")
                
                self.logger.error(f"OBD test connection failed: {e}")
                return False
            finally:
                try:
                    sock.close()
                except:
                    pass
                    
        except Exception as e:
            if status_callback:
                status_callback(f"Test error: {str(e)}")
            
            self.logger.error(f"OBD connection test failed: {e}")
            return False
    
    def get_device_info(self, mac_address: str) -> Optional[BluetoothDevice]:
        """Get detailed information about a specific device"""
        try:
            # Look up device name with timeout protection
            try:
                future = self._executor.submit(bluetooth.lookup_name, mac_address, self.lookup_timeout)
                try:
                    name = future.result(timeout=self.lookup_timeout + 2)
                except concurrent.futures.TimeoutError:
                    self.logger.warning(f"Device name lookup timed out for {mac_address}")
                    name = f"Unknown Device ({mac_address})"  
            except Exception as e:
                self.logger.warning(f"Device name lookup failed for {mac_address}: {e}")
                name = f"Unknown Device ({mac_address})"
            
            if name:
                # Classify the device
                device_classification = self._classify_device(name)
                signal_strength = self._get_signal_strength(mac_address)
                
                # Determine device type string for backward compatibility
                if device_classification == DeviceType.HIGHLY_LIKELY_ELM327:
                    device_type = 'ELM327'
                elif device_classification == DeviceType.POSSIBLY_COMPATIBLE:
                    device_type = 'Compatible'
                else:
                    device_type = 'Unknown'
                
                return BluetoothDevice(
                    name=name,
                    mac_address=mac_address,
                    signal_strength=signal_strength,
                    device_type=device_type,
                    last_seen=datetime.now(),
                    is_paired=False,
                    connection_verified=False,
                    device_classification=device_classification
                )
        except Exception as e:
            self.logger.error(f"Failed to get device info for {mac_address}: {e}")
        
        return None
    
    def discover_all_devices(self, timeout: int = 30, 
                           progress_callback: Optional[Callable[[float], None]] = None,
                           device_found_callback: Optional[Callable[[BluetoothDevice], None]] = None) -> List[BluetoothDevice]:
        """
        Discover all Bluetooth devices (convenience method)
        
        Args:
            timeout: Discovery timeout in seconds
            progress_callback: Called with progress percentage (0.0-1.0)
            device_found_callback: Called when a device is found
            
        Returns:
            List of all discovered devices
        """
        return self.discover_elm327_devices(timeout, progress_callback, device_found_callback, show_all_devices=True)
    
    def cancel_discovery(self) -> None:
        """Cancel ongoing discovery operation"""
        self._cancel_discovery.set()
        self.logger.info("Discovery cancellation requested")
    
    def cancel_pairing(self) -> None:
        """Cancel ongoing pairing operation"""
        self._cancel_pairing.set()
        self.logger.info("Pairing cancellation requested")
        
    def shutdown(self) -> None:
        """Shutdown pairing operations and cleanup resources"""
        self.logger.info("Shutting down Bluetooth pairing")
        self._cancel_discovery.set()
        self._cancel_pairing.set()
        
        # Shutdown thread pool with timeout
        try:
            self._executor.shutdown(wait=True)
        except Exception as e:
            self.logger.error(f"Error shutting down thread pool: {e}")
            
    def __del__(self):
        """Cleanup on object destruction"""
        try:
            self.shutdown()
        except:
            pass
    
    def is_discovery_active(self) -> bool:
        """Check if discovery is currently active"""
        return self._discovery_active
    
    def is_pairing_active(self) -> bool:
        """Check if pairing is currently active"""
        return self._pairing_active