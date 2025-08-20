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
    address: str
    last_connected: Optional[datetime.datetime] = None
    connection_count: int = 0
    signal_strength: Optional[int] = None
    device_type: str = "UNKNOWN"  # e.g., "ELM327", "OBD", etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize device data"""
        # Convert string timestamp to datetime if needed
        if isinstance(self.last_connected, str):
            try:
                self.last_connected = datetime.datetime.fromisoformat(self.last_connected)
            except (ValueError, TypeError):
                self.last_connected = None
                
        # Ensure address is normalized to uppercase without colons
        self.address = self.address.upper().replace(':', '')
        
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
            "address": self.address,
            "connection_count": self.connection_count,
            "device_type": self.device_type
        }
        
        # Only include non-None values to keep the serialized form clean
        if self.last_connected:
            result["last_connected"] = self.last_connected.isoformat()
            
        if self.signal_strength is not None:
            result["signal_strength"] = self.signal_strength
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BluetoothDevice':
        """Create device instance from dictionary"""
        # Extract known fields
        name = data.get("name", "Unknown Device")
        address = data.get("address", "")
        last_connected_str = data.get("last_connected")
        connection_count = data.get("connection_count", 0)
        signal_strength = data.get("signal_strength")
        device_type = data.get("device_type", "UNKNOWN")
        
        # Extract metadata (any additional fields)
        metadata = {k: v for k, v in data.items() if k not in 
                   ["name", "address", "last_connected", "connection_count", 
                    "signal_strength", "device_type"]}
        
        # Parse last_connected if it exists
        last_connected = None
        if last_connected_str:
            try:
                last_connected = datetime.datetime.fromisoformat(last_connected_str)
            except (ValueError, TypeError):
                pass
                
        return cls(
            name=name,
            address=address,
            last_connected=last_connected,
            connection_count=connection_count,
            signal_strength=signal_strength,
            device_type=device_type,
            metadata=metadata
        )
