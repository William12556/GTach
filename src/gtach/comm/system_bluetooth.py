#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
System-level Bluetooth implementation using bluetoothctl and system commands.
This provides Bluetooth functionality without requiring PyBluez.
"""

import logging
import subprocess
import socket
import re
import time
import threading
from typing import Optional, List, Tuple, Dict


class SystemBluetoothError(Exception):
    pass

class BluetoothError(SystemBluetoothError):
    pass

class BluetoothConnectionError(BluetoothError):
    pass

class BluetoothDiscoveryError(BluetoothError):
    pass

class BluetoothPairingError(BluetoothError):
    pass

class BluetoothTimeoutError(BluetoothError):
    pass


class BluetoothSocket:
    """Simple Bluetooth socket wrapper using system RFCOMM"""

    def __init__(self, socket_type: str = 'RFCOMM'):
        self.socket_type = socket_type
        self.sock = None
        self.connected = False
        self.timeout = None

    def connect(self, address_port: Tuple[str, int]) -> None:
        address, port = address_port
        try:
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.sock.connect((address, port))
            self.connected = True
        except Exception as e:
            raise BluetoothConnectionError(f"Failed to connect to {address}:{port} - {e}")

    def send(self, data: bytes) -> int:
        if not self.connected or not self.sock:
            raise BluetoothConnectionError("Socket not connected")
        try:
            return self.sock.send(data)
        except Exception as e:
            raise BluetoothConnectionError(f"Failed to send data - {e}")

    def recv(self, buffer_size: int) -> bytes:
        if not self.connected or not self.sock:
            raise BluetoothConnectionError("Socket not connected")
        try:
            return self.sock.recv(buffer_size)
        except Exception as e:
            raise BluetoothConnectionError(f"Failed to receive data - {e}")

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout
        if self.sock:
            self.sock.settimeout(timeout)

    def close(self) -> None:
        if self.sock:
            self.sock.close()
            self.connected = False


class SystemBluetoothManager:
    """System-level Bluetooth manager using bluetoothctl / hcitool"""

    def __init__(self):
        self.logger = logging.getLogger('SystemBluetoothManager')
        self._check_bluetooth_availability()

    def _check_bluetooth_availability(self) -> None:
        try:
            subprocess.run(['bluetoothctl', '--version'],
                           capture_output=True, check=True, timeout=5)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise BluetoothError("bluetoothctl not available - install bluez-utils")

    def _run_bluetoothctl(self, commands: List[str], timeout: int = 30) -> str:
        try:
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
        """Discover nearby Bluetooth devices.

        Uses hcitool scan (clean output, reliable timeout).
        Falls back to bluetoothctl if hcitool is unavailable.
        """
        self.logger.info(f"Starting device discovery for {duration} seconds")
        devices = {}
        mac_re = re.compile(r'^[0-9A-Fa-f:]{17}$')

        try:
            result = subprocess.run(
                ['hcitool', 'scan', '--flush'],
                capture_output=True,
                text=True,
                timeout=duration + 2
            )
            # hcitool scan output lines: "\t<MAC>\t<Name>"
            for line in result.stdout.splitlines():
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    mac = parts[0].strip()
                    name = parts[1].strip()
                    if mac_re.match(mac):
                        devices[mac] = name
                        self.logger.debug(f"Found: {name} ({mac})")

        except subprocess.TimeoutExpired:
            self.logger.info("hcitool scan timed out")
        except FileNotFoundError:
            self.logger.warning("hcitool not found - falling back to bluetoothctl")
            devices = self._discover_via_bluetoothctl(duration)
        except Exception as e:
            self.logger.error(f"Device discovery failed: {e}")

        result_list = list(devices.items())
        self.logger.info(f"Found {len(result_list)} devices")
        return result_list

    def _discover_via_bluetoothctl(self, duration: int) -> dict:
        """Fallback: parse live bluetoothctl scan output."""
        devices = {}
        dev_re = re.compile(r'\[NEW\]\s+Device\s+([0-9A-Fa-f:]{17})\s+(.+)')
        try:
            process = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )
            process.stdin.write('power on\nagent on\nscan on\n')
            process.stdin.flush()

            def _reader():
                for line in process.stdout:
                    m = dev_re.search(line)
                    if m and m.group(1) not in devices:
                        devices[m.group(1)] = m.group(2).strip()
                        self.logger.debug(f"btctl found: {m.group(2).strip()} ({m.group(1)})")

            t = threading.Thread(target=_reader, daemon=True)
            t.start()
            time.sleep(duration)
            try:
                process.stdin.write('scan off\nquit\n')
                process.stdin.flush()
            except Exception:
                pass
            process.terminate()
            t.join(timeout=3)
        except Exception as e:
            self.logger.error(f"bluetoothctl fallback failed: {e}")
        return devices

    def pair_device(self, mac_address: str) -> bool:
        try:
            commands = ['power on', 'agent on',
                        f'pair {mac_address}', f'trust {mac_address}']
            output = self._run_bluetoothctl(commands, timeout=30)
            if 'Pairing successful' in output:
                self.logger.info(f"Successfully paired with {mac_address}")
                return True
            self.logger.error(f"Failed to pair with {mac_address}")
            return False
        except Exception as e:
            self.logger.error(f"Pairing failed: {e}")
            return False

    def connect_device(self, mac_address: str) -> bool:
        try:
            output = self._run_bluetoothctl(
                ['power on', f'connect {mac_address}'], timeout=15)
            if 'Connection successful' in output:
                self.logger.info(f"Successfully connected to {mac_address}")
                return True
            self.logger.error(f"Failed to connect to {mac_address}")
            return False
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def disconnect_device(self, mac_address: str) -> bool:
        try:
            self._run_bluetoothctl([f'disconnect {mac_address}'], timeout=10)
            self.logger.info(f"Disconnected from {mac_address}")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection failed: {e}")
            return False

    def get_device_info(self, mac_address: str) -> Optional[Dict[str, str]]:
        try:
            output = self._run_bluetoothctl([f'info {mac_address}'], timeout=10)
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
        try:
            info = self.get_device_info(mac_address)
            if info:
                return info.get('Connected', 'no').lower() == 'yes'
            return False
        except Exception as e:
            self.logger.error(f"Failed to check connection status: {e}")
            return False


# Compatibility functions to match PyBluez API
def discover_devices(duration: int = 8, lookup_names: bool = True,
                     flush_cache: bool = False) -> List[Tuple[str, str]]:
    """Discover Bluetooth devices - compatibility function"""
    return SystemBluetoothManager().discover_devices(duration, lookup_names)


def lookup_name(mac_address: str, timeout: int = 10) -> Optional[str]:
    """Look up device name by MAC address - compatibility function"""
    info = SystemBluetoothManager().get_device_info(mac_address)
    if info:
        return info.get('Name', info.get('Alias', None))
    return None


# Constants for compatibility
RFCOMM = 'RFCOMM'
