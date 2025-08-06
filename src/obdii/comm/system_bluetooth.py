#!/usr/bin/env python3
"""
System-level Bluetooth implementation using bluetoothctl and system commands.
This provides Bluetooth functionality without requiring PyBluez.
"""

import logging
import subprocess
import socket
import re
import time
from typing import Optional, List, Tuple, Dict
from enum import Enum, auto


class SystemBluetoothError(Exception):
    """Exception raised for system Bluetooth operations"""
    pass


class BluetoothError(SystemBluetoothError):
    """Base Bluetooth error class for compatibility with PyBluez"""
    pass


class BluetoothConnectionError(BluetoothError):
    """Raised when Bluetooth connection fails"""
    pass


class BluetoothDiscoveryError(BluetoothError):
    """Raised when Bluetooth device discovery fails"""
    pass


class BluetoothPairingError(BluetoothError):
    """Raised when Bluetooth device pairing fails"""
    pass


class BluetoothTimeoutError(BluetoothError):
    """Raised when Bluetooth operation times out"""
    pass


class BluetoothSocket:
    """Simple Bluetooth socket wrapper using system RFCOMM"""
    
    def __init__(self, socket_type: str = 'RFCOMM'):
        self.socket_type = socket_type
        self.sock = None
        self.connected = False
        self.timeout = None
        
    def connect(self, address_port: Tuple[str, int]) -> None:
        """Connect to Bluetooth device using RFCOMM"""
        address, port = address_port
        
        # Create RFCOMM socket
        try:
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.sock.connect((address, port))
            self.connected = True
        except Exception as e:
            raise BluetoothConnectionError(f"Failed to connect to {address}:{port} - {e}")
    
    def send(self, data: bytes) -> int:
        """Send data to connected device"""
        if not self.connected or not self.sock:
            raise BluetoothConnectionError("Socket not connected")
        
        try:
            return self.sock.send(data)
        except Exception as e:
            raise BluetoothConnectionError(f"Failed to send data - {e}")
    
    def recv(self, buffer_size: int) -> bytes:
        """Receive data from connected device"""
        if not self.connected or not self.sock:
            raise BluetoothConnectionError("Socket not connected")
        
        try:
            return self.sock.recv(buffer_size)
        except Exception as e:
            raise BluetoothConnectionError(f"Failed to receive data - {e}")
    
    def settimeout(self, timeout: float) -> None:
        """Set socket timeout"""
        self.timeout = timeout
        if self.sock:
            self.sock.settimeout(timeout)
    
    def close(self) -> None:
        """Close the socket"""
        if self.sock:
            self.sock.close()
            self.connected = False


class SystemBluetoothManager:
    """System-level Bluetooth manager using bluetoothctl"""
    
    def __init__(self):
        self.logger = logging.getLogger('SystemBluetoothManager')
        self._check_bluetooth_availability()
    
    def _check_bluetooth_availability(self) -> None:
        """Check if system Bluetooth tools are available"""
        try:
            subprocess.run(['bluetoothctl', '--version'], 
                         capture_output=True, check=True, timeout=5)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise BluetoothError("bluetoothctl not available - install bluez-utils")
    
    def _run_bluetoothctl(self, commands: List[str], timeout: int = 30) -> str:
        """Run bluetoothctl commands and return output"""
        try:
            # Create a script to run multiple commands
            script = '\n'.join(commands + ['quit'])
            
            process = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=script, timeout=timeout)
            
            if process.returncode != 0:
                self.logger.warning(f"bluetoothctl stderr: {stderr}")
            
            return stdout
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise BluetoothTimeoutError("bluetoothctl command timed out")
        except Exception as e:
            raise BluetoothError(f"bluetoothctl command failed: {e}")
    
    def discover_devices(self, duration: int = 8, lookup_names: bool = True) -> List[Tuple[str, str]]:
        """Discover nearby Bluetooth devices"""
        self.logger.info(f"Starting device discovery for {duration} seconds")
        
        try:
            # Start discovery
            commands = [
                'power on',
                'agent on',
                'scan on'
            ]
            
            self._run_bluetoothctl(commands, timeout=5)
            
            # Wait for discovery
            time.sleep(duration)
            
            # Stop discovery and get results
            commands = [
                'scan off',
                'devices'
            ]
            
            output = self._run_bluetoothctl(commands, timeout=10)
            
            # Parse device list
            devices = []
            device_pattern = r'Device ([0-9A-Fa-f:]{17}) (.+)'
            
            for line in output.split('\n'):
                match = re.search(device_pattern, line)
                if match:
                    mac_address = match.group(1)
                    device_name = match.group(2)
                    devices.append((mac_address, device_name))
            
            self.logger.info(f"Found {len(devices)} devices")
            return devices
            
        except Exception as e:
            self.logger.error(f"Device discovery failed: {e}")
            return []
    
    def pair_device(self, mac_address: str) -> bool:
        """Pair with a Bluetooth device"""
        try:
            commands = [
                'power on',
                'agent on',
                f'pair {mac_address}',
                f'trust {mac_address}'
            ]
            
            output = self._run_bluetoothctl(commands, timeout=30)
            
            # Check if pairing was successful
            if 'Pairing successful' in output:
                self.logger.info(f"Successfully paired with {mac_address}")
                return True
            else:
                self.logger.error(f"Failed to pair with {mac_address}")
                return False
                
        except Exception as e:
            self.logger.error(f"Pairing failed: {e}")
            return False
    
    def connect_device(self, mac_address: str) -> bool:
        """Connect to a paired Bluetooth device"""
        try:
            commands = [
                'power on',
                f'connect {mac_address}'
            ]
            
            output = self._run_bluetoothctl(commands, timeout=15)
            
            # Check if connection was successful
            if 'Connection successful' in output:
                self.logger.info(f"Successfully connected to {mac_address}")
                return True
            else:
                self.logger.error(f"Failed to connect to {mac_address}")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect_device(self, mac_address: str) -> bool:
        """Disconnect from a Bluetooth device"""
        try:
            commands = [f'disconnect {mac_address}']
            output = self._run_bluetoothctl(commands, timeout=10)
            
            self.logger.info(f"Disconnected from {mac_address}")
            return True
            
        except Exception as e:
            self.logger.error(f"Disconnection failed: {e}")
            return False
    
    def get_device_info(self, mac_address: str) -> Optional[Dict[str, str]]:
        """Get information about a specific device"""
        try:
            commands = [f'info {mac_address}']
            output = self._run_bluetoothctl(commands, timeout=10)
            
            info = {}
            for line in output.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            
            return info if info else None
            
        except Exception as e:
            self.logger.error(f"Failed to get device info: {e}")
            return None
    
    def is_device_connected(self, mac_address: str) -> bool:
        """Check if a device is currently connected"""
        try:
            info = self.get_device_info(mac_address)
            if info:
                return info.get('Connected', 'no').lower() == 'yes'
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check connection status: {e}")
            return False


# Compatibility functions to match PyBluez API
def discover_devices(duration: int = 8, lookup_names: bool = True, flush_cache: bool = False) -> List[Tuple[str, str]]:
    """Discover Bluetooth devices - compatibility function"""
    manager = SystemBluetoothManager()
    return manager.discover_devices(duration, lookup_names)


def lookup_name(mac_address: str, timeout: int = 10) -> Optional[str]:
    """Look up device name by MAC address - compatibility function"""
    manager = SystemBluetoothManager()
    info = manager.get_device_info(mac_address)
    if info:
        return info.get('Name', info.get('Alias', None))
    return None


# Constants for compatibility
RFCOMM = 'RFCOMM'