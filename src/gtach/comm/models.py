#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Data models for communication components.
Contains dataclasses and enums used across communication modules.
"""

import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class BluetoothDevice:
    """Bluetooth device information and metadata"""
    name: str
    mac_address: str
    device_type: str = "UNKNOWN"
    last_connected: Optional[datetime.datetime] = None

    def __post_init__(self):
        """Validate and normalize device data"""
        # Convert string timestamp to datetime if needed
        if isinstance(self.last_connected, str):
            try:
                self.last_connected = datetime.datetime.fromisoformat(self.last_connected)
            except (ValueError, TypeError):
                self.last_connected = None
                
        # Ensure mac_address is normalized to uppercase PRESERVING colons
        self.mac_address = self.mac_address.upper()
        
        # Detect device type from name if not specified
        if self.device_type == "UNKNOWN":
            if "ELM" in self.name.upper():
                self.device_type = "ELM327"
            elif "OBD" in self.name.upper():
                self.device_type = "OBD"

    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary for serialization"""
        result = {
            "name": self.name,
            "mac_address": self.mac_address,
            "device_type": self.device_type
        }
        
        # Only include non-None values to keep the serialized form clean
        if self.last_connected:
            result["last_connected"] = self.last_connected.isoformat()
        
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BluetoothDevice':
        """Create device instance from dictionary"""
        # Extract known fields
        name = data.get("name", "Unknown Device")
        mac_address = data.get("mac_address", "")
        last_connected_str = data.get("last_connected")
        device_type = data.get("device_type", "UNKNOWN")
        
        # Parse last_connected if it exists
        last_connected = None
        if last_connected_str:
            try:
                last_connected = datetime.datetime.fromisoformat(last_connected_str)
            except (ValueError, TypeError):
                pass
        
        return cls(
            name=name,
            mac_address=mac_address,
            last_connected=last_connected,
            device_type=device_type
        )
