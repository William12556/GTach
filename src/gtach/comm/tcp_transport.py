"""
TCP Transport Implementation

This module provides an implementation of the OBDTransport interface using
TCP sockets for network communication with an ELM327 OBD-II adapter or emulator.

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
"""

import logging
import socket
from typing import Optional

from .transport import OBDTransport, TransportState, TransportError


class TCPTransport(OBDTransport):
    """TCP transport implementation for network communication.

    Supplies only the four handle primitives; OBDTransport holds the
    connect/disconnect/send_command skeleton (change-6481f8ce).
    """

    # ConnectionRefusedError is an OSError subclass, so the single
    # entry covers the pair the previous implementation listed.
    _IO_ERRORS = (OSError,)
    # socket.timeout is an OSError subclass, so it must be listed
    # separately to keep being caught first.
    _TIMEOUT_ERRORS = (socket.timeout,)

    def __init__(self, host: str = 'localhost', port: int = 35000, retry_delay: float = 5.0):
        super().__init__()
        self._host = host
        self._port = port
        self._retry_delay = retry_delay

    def _describe(self) -> str:
        """Describe the endpoint, for log messages."""
        return f"TCP device {self._host}:{self._port}"

    def _open(self) -> Optional[socket.socket]:
        """Open a TCP socket to the configured host and port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((self._host, self._port))
        sock.settimeout(None)
        return sock

    def _close(self, handle) -> None:
        """Close the socket."""
        handle.close()

    def _write(self, handle, data: bytes) -> None:
        """Send bytes on the socket."""
        handle.sendall(data)

    def _read(self, handle, n: int) -> bytes:
        """Receive up to n bytes from the socket."""
        return handle.recv(n)
