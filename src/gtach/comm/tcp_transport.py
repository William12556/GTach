"""
TCP Transport Implementation

This module provides an implementation of the OBDTransport interface using
TCP sockets for communication with an ELM327 OBD-II adapter over a network.

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
"""

import logging
import socket
from typing import Optional

from .transport import OBDTransport, TransportState, TransportError


class TCPTransport(OBDTransport):
    """TCP transport implementation for network communication."""
    
    def __init__(self, host: str = 'localhost', port: int = 35000, retry_delay: float = 5.0):
        super().__init__()
        self._host = host
        self._port = port
        self._retry_delay = retry_delay
        self._sock = None
        self._state = TransportState.DISCONNECTED
    
    def connect(self) -> bool:
        """Establish a TCP connection to the OBD device.
        
        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        logger = logging.getLogger('TCPTransport')
        with self._lock:
            self._state = TransportState.CONNECTING
        
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((self._host, self._port))
            self._sock.settimeout(None)
            
            with self._lock:
                self._state = TransportState.CONNECTED
            logger.info("Connected to TCP device %s:%d", self._host, self._port)
            return True
        except (ConnectionRefusedError, OSError) as e:
            logger.error("Failed to connect to TCP device %s:%d: %s", self._host, self._port, e)
            self._close_socket()
            with self._lock:
                self._state = TransportState.DISCONNECTED
            return False
        except Exception as e:
            logger.error("Unexpected error during TCP connection: %s", e)
            self._close_socket()
            with self._lock:
                self._state = TransportState.ERROR
            return False
    
    def disconnect(self) -> None:
        """Close the TCP connection."""
        logger = logging.getLogger('TCPTransport')
        self._shutdown.set()
        with self._lock:
            self._close_socket()
            self._state = TransportState.DISCONNECTED
        logger.info("Disconnected from TCP device")
    
    def _acquire_handle(self) -> Optional[socket.socket]:
        """Return the socket captured under the lock.

        is_connected() reads the state under the lock and releases it,
        so a caller acting on its result is acting on a stale answer: a
        concurrent disconnect() sets self._sock to None and the
        subsequent call raises AttributeError instead of the OSError the
        handler below expects (core review §5.3). Capturing the
        reference means a closed socket fails the way the code already
        handles.

        Returns:
            The socket, or None if not connected.
        """
        with self._lock:
            return self._sock

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the OBD device and receive the response.

        Args:
            command: The OBD command to send.
            timeout: Timeout in seconds for the response.

        Returns:
            Optional[str]: The response from the device, or None if the command failed.
        """
        logger = logging.getLogger('TCPTransport')
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
            handle.sendall(encoded_cmd)

            # Set timeout for response
            handle.settimeout(timeout)

            # Read response until '>' prompt is received
            buf = b''
            while True:
                data = handle.recv(1024)
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
            logger.debug("RX: %r", response)
            return response
        except socket.timeout:
            logger.warning("Timeout waiting for response from device (cmd=%r, timeout=%.1fs)", command, timeout)
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
