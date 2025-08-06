#!/usr/bin/env python3
"""
Setup-specific data models for OBDII display application.
Defines data structures used during Bluetooth setup process.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional
from datetime import datetime

class SetupScreen(Enum):
    """Setup flow screen states"""
    WELCOME = auto()
    DISCOVERY = auto()
    DEVICE_LIST = auto()
    PAIRING = auto()
    TEST = auto()
    COMPLETE = auto()
    CURRENT_DEVICE = auto()
    DEVICE_MANAGEMENT = auto()
    CONFIRMATION = auto()

class PairingStatus(Enum):
    """Bluetooth pairing status"""
    IDLE = auto()
    DISCOVERING = auto()
    CONNECTING = auto()
    TESTING = auto()
    SUCCESS = auto()
    FAILED = auto()

class DeviceType(Enum):
    """Device type classification"""
    HIGHLY_LIKELY_ELM327 = auto()
    POSSIBLY_COMPATIBLE = auto()
    UNKNOWN = auto()

@dataclass
class BluetoothDevice:
    """Represents a discovered Bluetooth device"""
    name: str
    mac_address: str
    signal_strength: int
    device_type: str
    last_seen: datetime
    is_paired: bool = False
    connection_verified: bool = False
    device_classification: DeviceType = DeviceType.UNKNOWN

    def __hash__(self):
        return hash(self.mac_address)

    def __eq__(self, other):
        if isinstance(other, BluetoothDevice):
            return self.mac_address == other.mac_address
        return False

@dataclass 
class SetupState:
    """Current state of the setup process"""
    current_screen: SetupScreen
    discovered_devices: List[BluetoothDevice]
    selected_device: Optional[BluetoothDevice]
    pairing_status: PairingStatus
    setup_complete: bool
    error_message: Optional[str] = None
    discovery_progress: float = 0.0
    discovery_timeout: int = 30

    def reset_discovery(self):
        """Reset discovery state"""
        self.discovered_devices.clear()
        self.selected_device = None
        self.pairing_status = PairingStatus.IDLE
        self.discovery_progress = 0.0
        self.error_message = None

class SetupAction(Enum):
    """User actions during setup"""
    NEXT = auto()
    BACK = auto()
    SELECT_DEVICE = auto()
    RETRY = auto()
    CANCEL = auto()
    SAVE = auto()
    TEST_CONNECTION = auto()
    CHANGE_DEVICE = auto()
    REMOVE_DEVICE = auto()
    ADD_DEVICE = auto()
    REFRESH = auto()
    MANUAL_ENTRY = auto()
    CONFIRM = auto()
    EXIT_SETUP = auto()
    TOGGLE_FILTER = auto()
    CONNECT_MANUAL = auto()