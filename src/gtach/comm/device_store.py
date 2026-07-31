#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Persistent device storage for OBDII display application.
Manages paired device configuration and setup state.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Conditional import of yaml with fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

from .models import BluetoothDevice

class DeviceStore:
    """Manages persistent storage of paired Bluetooth devices"""
    
    def __init__(self, config_path: str = "config/devices.yaml"):
        self.logger = logging.getLogger('DeviceStore')
        self.config_path = config_path
        
        # Check yaml availability and warn if not available
        if not YAML_AVAILABLE:
            self.logger.warning("YAML library not available - device storage will use in-memory fallback")
            self.config = {
                'paired_devices': {}
            }
        else:
            self._ensure_config_dir()
            self._load_config()
    
    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists"""
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def _load_config(self) -> None:
        """Load device configuration from file"""
        if not YAML_AVAILABLE:
            self.logger.debug("YAML not available - using default config")
            self.config = {
                'paired_devices': {}
            }
            return
            
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                self.config = {
                    'paired_devices': {}
                }
                self._save_config()
        except Exception as e:
            self.logger.error(f"Failed to load device config: {e}")
            self.config = {
                'paired_devices': {}
            }

        # Runs on every exit path, including the error path above.
        self._normalise_config()

    def _normalise_config(self) -> None:
        """Enforce the structure the writers assume.

        yaml.safe_load returns whatever the file contains. An
        empty file, a partially written file or a hand edit can
        produce a mapping with no 'paired_devices' key, a null
        value under that key, or a top level that is not a
        mapping at all. save_device previously indexed into
        self.config['paired_devices'] directly and raised
        KeyError, which its own handler swallowed — so pairing
        reported success and persisted nothing (core review
        §3.4, recommendation #4).

        The contract is enforced once here rather than at each
        assignment site.
        """
        if not isinstance(self.config, dict):
            self.logger.warning(
                f"devices.yaml top level is {type(self.config).__name__}, "
                f"expected mapping — using an empty store"
            )
            self.config = {}

        paired = self.config.get('paired_devices')
        if not isinstance(paired, dict):
            if paired is not None:
                self.logger.warning(
                    f"paired_devices is {type(paired).__name__}, "
                    f"expected mapping — replacing"
                )
            self.config['paired_devices'] = {}

        secondary = self.config['paired_devices'].get('secondary')
        if secondary is not None and not isinstance(secondary, dict):
            self.logger.warning(
                f"paired_devices.secondary is {type(secondary).__name__}, "
                f"expected mapping — replacing"
            )
            self.config['paired_devices']['secondary'] = {}

    def _save_config(self) -> bool:
        """Save device configuration to file.

        Returns:
            True when the store was written to disk, False otherwise —
            including when YAML is unavailable, since nothing is
            persisted in that state.
        """
        if not YAML_AVAILABLE:
            self.logger.debug("YAML not available - config will not be persisted")
            return False

        try:
            tmp_path = self.config_path + '.tmp'
            with open(tmp_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            os.replace(tmp_path, self.config_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save device config: {e}")
            return False
    
    def save_device(self, device: BluetoothDevice, is_primary: bool = True) -> bool:
        """Save a paired device to storage.

        Args:
            device: The device to persist.
            is_primary: Store as the primary device rather than under
                the secondary mapping.

        Returns:
            True when the device reached disk, False when it did not —
            because the write failed, or because YAML is unavailable and
            the store is in-memory only. Callers that report pairing
            success to the operator should consult it.
        """
        try:
            device_data = {
                'name': device.name,
                'mac_address': device.mac_address,
                'device_type': device.device_type
            }
            
            # Include last_connected if it exists
            if device.last_connected:
                device_data['last_connected'] = device.last_connected.isoformat()
            
            # setdefault rather than direct indexing: a devices.yaml
            # that exists but carries no paired_devices key raised
            # KeyError here, on BOTH branches, and the except below
            # swallowed it (core review §3.4, recommendation #4).
            paired = self.config.setdefault('paired_devices', {})

            if is_primary:
                paired['primary'] = device_data
            else:
                paired.setdefault('secondary', {})[device.mac_address] = device_data

            saved = self._save_config()
            if saved:
                self.logger.info(f"Saved {'primary' if is_primary else 'secondary'} device: {device.name}")
            else:
                self.logger.error(f"Device {device.name} was not persisted")
            return saved

        except Exception as e:
            self.logger.error(f"Failed to save device {device.name}: {e}")
            return False
    
    def get_primary_device(self) -> Optional[BluetoothDevice]:
        """Get the primary paired device"""
        try:
            primary_data = self.config.get('paired_devices', {}).get('primary')
            if primary_data:
                last_connected = None
                if primary_data.get('last_connected'):
                    last_connected = datetime.fromisoformat(primary_data['last_connected'])
                
                return BluetoothDevice(
                    name=primary_data['name'],
                    mac_address=primary_data['mac_address'],
                    device_type=primary_data.get('device_type', 'UNKNOWN'),
                    last_connected=last_connected
                )
            return None
        except Exception as e:
            self.logger.error(f"Failed to get primary device: {e}")
            return None
    
    def get_all_devices(self) -> List[BluetoothDevice]:
        """Get all paired devices"""
        devices = []
        
        # Add primary device
        primary = self.get_primary_device()
        if primary:
            devices.append(primary)
        
        # Add secondary devices
        try:
            secondary_devices = self.config.get('paired_devices', {}).get('secondary', {})
            for mac_address, device_data in secondary_devices.items():
                last_connected = None
                if device_data.get('last_connected'):
                    last_connected = datetime.fromisoformat(device_data['last_connected'])
                device = BluetoothDevice(
                    name=device_data['name'],
                    mac_address=device_data['mac_address'],
                    device_type=device_data.get('device_type', 'UNKNOWN'),
                    last_connected=last_connected
                )
                devices.append(device)
        except Exception as e:
            self.logger.error(f"Failed to get secondary devices: {e}")
        
        return devices
    
    def remove_device(self, mac_address: str) -> bool:
        """Remove a device from storage"""
        try:
            # Check if it's the primary device
            primary = self.config.get('paired_devices', {}).get('primary')
            if primary and primary.get('mac_address') == mac_address:
                del self.config['paired_devices']['primary']
                self._save_config()
                self.logger.info(f"Removed primary device: {mac_address}")
                return True
            
            # Check secondary devices
            secondary_devices = self.config.get('paired_devices', {}).get('secondary', {})
            if mac_address in secondary_devices:
                del secondary_devices[mac_address]
                self._save_config()
                self.logger.info(f"Removed secondary device: {mac_address}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove device {mac_address}: {e}")
            return False
    
    def get_device_by_mac(self, mac_address: str) -> Optional[BluetoothDevice]:
        """Get a specific device by MAC address"""
        for device in self.get_all_devices():
            if device.mac_address == mac_address:
                return device
        return None