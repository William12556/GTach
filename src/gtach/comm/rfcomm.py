"""
RFCOMM Transport Implementation

This module provides an implementation of the OBDTransport interface using
RFCOMM sockets for Classic Bluetooth communication with an ELM327 OBD-II adapter.

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
"""

import logging
import socket
from typing import Optional

from .transport import OBDTransport, TransportState, TransportError


class RFCOMMTransport(OBDTransport):
    """RFCOMM transport implementation for Classic Bluetooth communication.

    Supplies only the four handle primitives; OBDTransport holds the
    connect/disconnect/send_command skeleton (change-6481f8ce).
    """

    _IO_ERRORS = (OSError,)
    # socket.timeout is an OSError subclass, so it must be listed
    # separately to keep being caught first.
    _TIMEOUT_ERRORS = (socket.timeout,)

    def __init__(self, mac_address: str, channel: int = 1, retry_delay: float = 5.0):
        super().__init__()
        self._mac_address = mac_address
        self._channel = channel
        self._retry_delay = retry_delay

    def _describe(self) -> str:
        """Describe the endpoint, for log messages."""
        return f"RFCOMM device {self._mac_address} on channel {self._channel}"

    def _open(self) -> Optional[socket.socket]:
        """Open an RFCOMM socket to the paired device."""
        # Guard against platforms where AF_BLUETOOTH is not available (e.g., macOS)
        if not hasattr(socket, 'AF_BLUETOOTH'):
            raise OSError("AF_BLUETOOTH not supported on this platform")

        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(10)
        # Nothing else closes this socket if connect raises. It is a
        # local, and OBDTransport.connect's _IO_ERRORS handler calls
        # _discard_handle() against self._handle, which is only
        # assigned on the success path — so on failure it discards
        # None while this socket leaks. An unclosed RFCOMM socket
        # holds its ACL reference, which is a candidate mechanism for
        # the EBUSY seen on every subsequent retry (issue-5e7a03c4).
        #
        # BaseException rather than Exception: a KeyboardInterrupt or a
        # timeout delivered as a BaseException must still close it.
        try:
            sock.connect((self._mac_address, self._channel))
            sock.settimeout(None)
        except BaseException:
            try:
                sock.close()
            except Exception:
                pass
            # Bare raise, so the traceback and errno are preserved and
            # OBDTransport.connect's existing handling is unaffected.
            raise
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
