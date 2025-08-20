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

from ..display.setup_models import BluetoothDevice

class DeviceStore:
    """Manages persistent storage of paired Bluetooth devices"""
    
    def __init__(self, config_path: str = "config/devices.yaml"):
        self.logger = logging.getLogger('DeviceStore')
        self.config_path = config_path
        
        # Check yaml availability and warn if not available
        if not YAML_AVAILABLE:
            self.logger.warning("YAML library not available - device storage will use in-memory fallback")
            self.config = {
                'paired_devices': {},
                'setup': {
                    'completed': False,
                    'first_run': True,
                    'discovery_timeout': 30
                }
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
                'paired_devices': {},
                'setup': {
                    'completed': False,
                    'first_run': True,
                    'discovery_timeout': 30
                }
            }
            return
            
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                self.config = {
                    'paired_devices': {},
                    'setup': {
                        'completed': False,
                        'first_run': True,
                        'discovery_timeout': 30
                    }
                }
                self._save_config()
        except Exception as e:
            self.logger.error(f"Failed to load device config: {e}")
            self.config = {
                'paired_devices': {},
                'setup': {
                    'completed': False,
                    'first_run': True,
                    'discovery_timeout': 30
                }
            }
    
    def _save_config(self) -> None:
        """Save device configuration to file"""
        if not YAML_AVAILABLE:
            self.logger.debug("YAML not available - config will not be persisted")
            return
            
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"Failed to save device config: {e}")
    
    def save_paired_device(self, device: BluetoothDevice, is_primary: bool = True) -> None:
        """Save a paired device to storage"""
        try:
            device_data = {
                'name': device.name,
                'mac_address': device.mac_address,
                'device_type': device.device_type,
                'last_connected': datetime.now().isoformat(),
                'connection_verified': device.connection_verified,
                'signal_strength': device.signal_strength
            }
            
            if is_primary:
                self.config['paired_devices']['primary'] = device_data
            else:
                # Add to secondary devices
                if 'secondary' not in self.config['paired_devices']:
                    self.config['paired_devices']['secondary'] = {}
                self.config['paired_devices']['secondary'][device.mac_address] = device_data
            
            self._save_config()
            self.logger.info(f"Saved {'primary' if is_primary else 'secondary'} device: {device.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to save device {device.name}: {e}")
    
    def get_primary_device(self) -> Optional[BluetoothDevice]:
        """Get the primary paired device"""
        try:
            primary_data = self.config.get('paired_devices', {}).get('primary')
            if primary_data:
                return BluetoothDevice(
                    name=primary_data['name'],
                    mac_address=primary_data['mac_address'],
                    device_type=primary_data.get('device_type', 'ELM327'),
                    signal_strength=primary_data.get('signal_strength', 0),
                    last_seen=datetime.fromisoformat(primary_data.get('last_connected', datetime.now().isoformat())),
                    is_paired=True,
                    connection_verified=primary_data.get('connection_verified', False)
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
                device = BluetoothDevice(
                    name=device_data['name'],
                    mac_address=device_data['mac_address'],
                    device_type=device_data.get('device_type', 'ELM327'),
                    signal_strength=device_data.get('signal_strength', 0),
                    last_seen=datetime.fromisoformat(device_data.get('last_connected', datetime.now().isoformat())),
                    is_paired=True,
                    connection_verified=device_data.get('connection_verified', False)
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
    
    def set_primary_device(self, mac_address: str) -> bool:
        """Set a device as primary by MAC address"""
        try:
            # Check if it's already primary
            primary = self.config.get('paired_devices', {}).get('primary')
            if primary and primary.get('mac_address') == mac_address:
                return True
            
            # Find device in secondary devices
            secondary_devices = self.config.get('paired_devices', {}).get('secondary', {})
            if mac_address in secondary_devices:
                device_data = secondary_devices[mac_address]
                
                # Move current primary to secondary if it exists
                if primary:
                    if 'secondary' not in self.config['paired_devices']:
                        self.config['paired_devices']['secondary'] = {}
                    self.config['paired_devices']['secondary'][primary['mac_address']] = primary
                
                # Set new primary
                self.config['paired_devices']['primary'] = device_data
                
                # Remove from secondary
                del secondary_devices[mac_address]
                
                self._save_config()
                self.logger.info(f"Set primary device: {mac_address}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to set primary device {mac_address}: {e}")
            return False
    
    def is_setup_complete(self) -> bool:
        """Check if initial setup is complete"""
        return self.config.get('setup', {}).get('completed', False)
    
    def mark_setup_complete(self) -> None:
        """Mark initial setup as complete"""
        try:
            if 'setup' not in self.config:
                self.config['setup'] = {}
            self.config['setup']['completed'] = True
            self.config['setup']['first_run'] = False
            self._save_config()
            self.logger.info("Setup marked as complete")
        except Exception as e:
            self.logger.error(f"Failed to mark setup complete: {e}")
    
    def is_first_run(self) -> bool:
        """Check if this is the first run"""
        return self.config.get('setup', {}).get('first_run', True)
    
    def get_discovery_timeout(self) -> int:
        """Get discovery timeout setting"""
        return self.config.get('setup', {}).get('discovery_timeout', 30)
    
    def set_discovery_timeout(self, timeout: int) -> None:
        """Set discovery timeout setting"""
        try:
            if 'setup' not in self.config:
                self.config['setup'] = {}
            self.config['setup']['discovery_timeout'] = timeout
            self._save_config()
        except Exception as e:
            self.logger.error(f"Failed to set discovery timeout: {e}")
    
    def clear_all_devices(self) -> None:
        """Clear all paired devices"""
        try:
            self.config['paired_devices'] = {}
            self._save_config()
            self.logger.info("Cleared all devices")
        except Exception as e:
            self.logger.error(f"Failed to clear devices: {e}")
    
    def get_device_by_mac(self, mac_address: str) -> Optional[BluetoothDevice]:
        """Get a specific device by MAC address"""
        for device in self.get_all_devices():
            if device.mac_address == mac_address:
                return device
        return None