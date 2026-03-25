"""
RFCOMM Transport Implementation

This module provides an implementation of the OBDTransport interface using
RFCOMM sockets for Classic Bluetooth communication with an ELM327 OBD-II adapter.

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
"""

import logging
import socket
import threading
from typing import Optional

from .transport import OBDTransport, TransportState, TransportError


class RFCOMMTransport(OBDTransport):
    """RFCOMM transport implementation for Classic Bluetooth communication."""
    
    def __init__(self, mac_address: str, channel: int = 1, retry_delay: float = 5.0):
        super().__init__()
        self._mac_address = mac_address
        self._channel = channel
        self._retry_delay = retry_delay
        self._sock = None
        self._state = TransportState.DISCONNECTED
    
    def connect(self) -> bool:
        """Establish an RFCOMM connection to the OBD device.
        
        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        logger = logging.getLogger('RFCOMMTransport')
        with self._lock:
            self._state = TransportState.CONNECTING
        
        try:
            # Guard against platforms where AF_BLUETOOTH is not available (e.g., macOS)
            if not hasattr(socket, 'AF_BLUETOOTH'):
                raise OSError("AF_BLUETOOTH not supported on this platform")
            
            self._sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self._sock.settimeout(10)
            self._sock.connect((self._mac_address, self._channel))
            self._sock.settimeout(None)
            
            with self._lock:
                self._state = TransportState.CONNECTED
            logger.info("Connected to RFCOMM device %s on channel %d", self._mac_address, self._channel)
            return True
        except OSError as e:
            logger.error("Failed to connect to RFCOMM device: %s", e)
            self._close_socket()
            with self._lock:
                self._state = TransportState.DISCONNECTED
            return False
        except Exception as e:
            logger.error("Unexpected error during RFCOMM connection: %s", e)
            self._close_socket()
            with self._lock:
                self._state = TransportState.ERROR
            return False
    
    def disconnect(self) -> None:
        """Close the RFCOMM connection."""
        logger = logging.getLogger('RFCOMMTransport')
        self._shutdown.set()
        with self._lock:
            self._close_socket()
            self._state = TransportState.DISCONNECTED
        logger.info("Disconnected from RFCOMM device")
    
    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the OBD device and receive the response.
        
        Args:
            command: The OBD command to send.
            timeout: Timeout in seconds for the response.
            
        Returns:
            Optional[str]: The response from the device, or None if the command failed.
        """
        logger = logging.getLogger('RFCOMMTransport')
        if not self.is_connected():
            logger.warning("Cannot send command: transport is not connected")
            return None
        
        try:
            # Prepare the command
            encoded_cmd = (command.strip() + '\r').encode('ascii')
            self._sock.sendall(encoded_cmd)
            
            # Set timeout for response
            self._sock.settimeout(timeout)
            
            # Read response until '>' prompt is received
            buf = b''
            while True:
                data = self._sock.recv(1024)
                if not data:
                    # Connection closed by the other end
                    with self._lock:
                        self._state = TransportState.DISCONNECTED
                    logger.error("Connection closed by device")
                    return None
                buf += data
                if b'>' in buf:
                    break
            
            # Decode and strip the response
            response = buf.decode('ascii', errors='ignore').strip()
            # Remove the trailing '>' prompt
            response = response.rstrip('>').strip()
            return response
        except socket.timeout:
            logger.warning("Timeout waiting for response from device")
            return None
        except OSError as e:
            logger.error("Error communicating with device: %s", e)
            with self._lock:
                self._state = TransportState.DISCONNECTED
            self._close_socket()
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
    
    def _close_socket(self) -> None:
        """Close the socket if it is open."""
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            finally:
                self._sock = None
