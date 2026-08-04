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
    """Abstract base class for OBD transport implementations.

    Holds the connection skeleton once. RFCOMM, TCP and serial had
    three near-identical copies of connect, disconnect, send_command,
    is_connected and state, differing only in how a handle is opened,
    closed, written to and read from (core review §5.8). Those four
    operations are the abstract surface; everything else is concrete
    here.

    The capture-then-use discipline in send_command is the point of
    change-6481f8ce: the handle is captured under the lock ONCE and
    every subsequent operation uses that reference, so a concurrent
    disconnect() produces the I/O error the handlers expect rather than
    an AttributeError on None (core review §5.3).
    """

    # Errors a subclass's I/O raises when the handle or the peer fails.
    # Caught by connect and send_command, which mark the transport
    # disconnected and discard the handle.
    _IO_ERRORS: tuple = (OSError,)

    # Errors meaning "no response within the timeout". Logged and
    # returning None WITHOUT marking the transport disconnected. Caught
    # before _IO_ERRORS because socket.timeout is an OSError subclass.
    _TIMEOUT_ERRORS: tuple = ()

    # Whether an empty read means the peer closed the connection.
    # True for stream sockets. False for pyserial, whose read_until
    # returns b'' on timeout with the port still open.
    _EMPTY_READ_IS_EOF: bool = True

    def __init__(self):
        # OBDTransport is abstract. The four handle primitives below are
        # deliberately NOT @abstractmethod: SimTransport overrides the
        # whole skeleton and supplies none of them, and change-6481f8ce
        # may not modify it. Declaring them abstract would make
        # SimTransport uninstantiable and break simtcp and simbt. The
        # guard keeps direct instantiation an error regardless.
        if type(self) is OBDTransport:
            raise TypeError(
                "OBDTransport is abstract and cannot be instantiated"
            )
        self._shutdown = threading.Event()
        self._lock = threading.RLock()
        self._handle = None
        self._state = TransportState.DISCONNECTED

    def _open(self):
        """Open and return a connected handle.

        Returns:
            The handle, or None if no device could be resolved.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement _open"
        )

    def _close(self, handle) -> None:
        """Close the given handle."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _close"
        )

    def _write(self, handle, data: bytes) -> None:
        """Write bytes to the given handle."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _write"
        )

    def _read(self, handle, n: int) -> bytes:
        """Read up to n bytes from the given handle."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _read"
        )

    def _set_timeout(self, handle, timeout: float) -> None:
        """Apply a read timeout to the handle. Override if it differs."""
        handle.settimeout(timeout)

    def _describe(self) -> str:
        """Describe the endpoint, for log messages."""
        return self.__class__.__name__

    def _acquire_handle(self):
        """Return the handle captured under the lock.

        is_connected() reads the state under the lock and releases it,
        so a caller acting on its result is acting on a stale answer.
        Capturing the reference means a closed handle fails the way the
        code already handles (core review §5.3).

        Returns:
            The handle, or None if not connected.
        """
        with self._lock:
            return self._handle

    def _discard_handle(self) -> None:
        """Close and clear the handle, acquiring the lock."""
        with self._lock:
            self._discard_handle_locked()

    def _discard_handle_locked(self) -> None:
        """Close and clear the handle. The caller holds the lock."""
        handle = self._handle
        self._handle = None
        if handle is not None:
            try:
                self._close(handle)
            except self._IO_ERRORS:
                pass

    def connect(self) -> bool:
        """Establish a connection to the OBD device.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        logger = logging.getLogger(self.__class__.__name__)
        with self._lock:
            self._state = TransportState.CONNECTING

        try:
            handle = self._open()
            if handle is None:
                with self._lock:
                    self._state = TransportState.DISCONNECTED
                return False

            with self._lock:
                self._handle = handle
                self._state = TransportState.CONNECTED
            logger.info("Connected to %s", self._describe())
            return True
        except self._IO_ERRORS as e:
            logger.error("Failed to connect to %s: %s", self._describe(), e)
            self._discard_handle()
            with self._lock:
                self._state = TransportState.DISCONNECTED
            return False
        except Exception as e:
            logger.error("Unexpected error during connection to %s: %s",
                         self._describe(), e)
            self._discard_handle()
            with self._lock:
                self._state = TransportState.ERROR
            return False

    def disconnect(self) -> None:
        """Close the connection to the OBD device."""
        logger = logging.getLogger(self.__class__.__name__)
        self._shutdown.set()
        with self._lock:
            self._discard_handle_locked()
            self._state = TransportState.DISCONNECTED
        logger.info("Disconnected from %s", self._describe())

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the OBD device and receive the response.

        Args:
            command: The OBD command to send.
            timeout: Timeout in seconds for the response.

        Returns:
            Optional[str]: The response from the device, or None if the command failed.
        """
        logger = logging.getLogger(self.__class__.__name__)
        # Capture ONCE, before the receive loop. Re-capturing per
        # iteration would reintroduce the window this closes.
        handle = self._acquire_handle()
        if handle is None:
            logger.warning("Cannot send command: transport is not connected")
            return None

        try:
            # Prepare the command
            encoded_cmd = (command.strip() + '\r').encode('ascii')
            logger.debug("TX: %r", encoded_cmd)
            self._write(handle, encoded_cmd)

            # Set timeout for response
            self._set_timeout(handle, timeout)

            # Read response until '>' prompt is received
            buf = b''
            while True:
                data = self._read(handle, 1024)
                if not data:
                    if self._EMPTY_READ_IS_EOF:
                        # Connection closed by the other end
                        with self._lock:
                            self._state = TransportState.DISCONNECTED
                        logger.error("Connection closed by device")
                        return None
                    # A timed-out read on an open port: return what
                    # arrived, as the serial implementation always did.
                    break
                buf += data
                if b'>' in buf:
                    break

            # Decode and strip the response
            response = buf.decode('ascii', errors='ignore').strip()
            # Remove the trailing '>' prompt
            response = response.rstrip('>').strip()
            logger.debug("RX: %r", response)
            return response
        except self._TIMEOUT_ERRORS:
            logger.warning("Timeout waiting for response from device "
                           "(cmd=%r, timeout=%.1fs)", command, timeout)
            return None
        except self._IO_ERRORS as e:
            logger.error("Error communicating with device: %s", e)
            with self._lock:
                self._state = TransportState.DISCONNECTED
            self._discard_handle()
            return None
        except Exception as e:
            logger.error("Unexpected error during command send: %s", e)
            return None

    def is_connected(self) -> bool:
        """Check if the transport is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        with self._lock:
            return self._state == TransportState.CONNECTED

    @property
    def state(self) -> TransportState:
        """Get the current state of the transport.

        Returns:
            TransportState: The current state.
        """
        with self._lock:
            return self._state

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
        platform_type: The platform type (e.g., RASPBERRY_PI).
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

    # Simulation transports for hardware-free testing
    if transport_arg in ('simtcp', 'simbt'):
        from .sim_transport import SimTransport
        return SimTransport()

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
    if platform_type.name.startswith('RASPBERRY_PI'):
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
