"""
OBD Transport Abstraction Layer

This module defines the abstract base class for OBD transport implementations,
including state management, error handling, and a factory function for selecting
the appropriate transport based on platform and arguments.

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
import argparse
import logging
import threading
from typing import Optional

from ..utils.platform import PlatformType
from .device_store import DeviceStore


class TransportState(Enum):
    """Enumeration of transport connection states."""
    
    DISCONNECTED = auto()
    """Transport is disconnected."""
    
    CONNECTING = auto()
    """Transport is in the process of connecting."""
    
    CONNECTED = auto()
    """Transport is connected and ready for communication."""
    
    ERROR = auto()
    """Transport encountered an error."""


class TransportError(Exception):
    """Base exception for transport-related errors."""
    pass


class ConnectionError(TransportError):
    """Exception raised for connection-related errors."""
    pass


class TimeoutError(TransportError):
    """Exception raised for timeout-related errors."""
    pass


class ProtocolError(TransportError):
    """Exception raised for protocol-related errors."""
    pass


class OBDTransport(ABC):
    """Abstract base class for OBD transport implementations."""
    
    def __init__(self):
        self._shutdown = threading.Event()
        self._lock = threading.RLock()
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish a connection to the OBD device.
        
        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the OBD device."""
        pass
    
    @abstractmethod
    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the OBD device and receive the response.
        
        Args:
            command: The OBD command to send.
            timeout: Timeout in seconds for the response.
            
        Returns:
            Optional[str]: The response from the device, or None if the command failed.
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the transport is currently connected.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        pass
    
    @property
    @abstractmethod
    def state(self) -> TransportState:
        """Get the current state of the transport.
        
        Returns:
            TransportState: The current state.
        """
        pass
    
    def reconnect_indefinitely(self, retry_delay: float = 5.0) -> None:
        """Attempt to reconnect indefinitely until successful or shutdown is requested.
        
        Args:
            retry_delay: Delay in seconds between retry attempts.
        """
        logger = logging.getLogger(self.__class__.__name__)
        while not self._shutdown.is_set():
            if self.connect():
                return
            logger.warning("Failed to connect, retrying in %.1f seconds...", retry_delay)
            self._shutdown.wait(retry_delay)


def select_transport(platform_type: PlatformType, args: argparse.Namespace) -> OBDTransport:
    """Factory function to select the appropriate transport based on platform and arguments.
    
    Args:
        platform_type: The platform type (e.g., MACOS, RASPBERRY_PI).
        args: Command-line arguments namespace.
        
    Returns:
        OBDTransport: An instance of the appropriate transport class.
        
    Raises:
        TransportError: If the platform is unsupported or no paired device is found.
    """
    from .rfcomm import RFCOMMTransport
    from .serial_transport import SerialTransport
    from .tcp_transport import TCPTransport
    
    transport_arg = getattr(args, 'transport', None)
    
    if transport_arg == 'tcp':
        host = getattr(args, 'obd_host', 'localhost')
        port = getattr(args, 'obd_port', 35000)
        return TCPTransport(host=host, port=port)
    
    elif transport_arg == 'serial':
        port = getattr(args, 'serial_port', None)
        return SerialTransport(port=port)
    
    elif transport_arg == 'rfcomm':
        return _get_rfcomm()
    
    # Auto-detect based on platform if no transport argument is provided
    if platform_type == PlatformType.MACOS:
        return SerialTransport()
    elif platform_type.name.startswith('RASPBERRY_PI'):
        return _get_rfcomm()
    else:
        raise TransportError('Unsupported platform')


def _get_rfcomm() -> OBDTransport:
    """Helper function to create an RFCOMM transport using the primary device.
    
    Returns:
        RFCOMMTransport: An instance of RFCOMMTransport.
        
    Raises:
        TransportError: If no paired device is found.
    """
    from .rfcomm import RFCOMMTransport
    
    ds = DeviceStore()
    dev = ds.get_primary_device()
    if not dev:
        raise TransportError('No paired device found')
    return RFCOMMTransport(mac_address=dev.mac_address)
