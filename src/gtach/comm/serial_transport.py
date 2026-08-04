"""
Serial Transport Implementation

This module provides an implementation of the OBDTransport interface using
pyserial for direct UART communication with an ELM327 OBD-II adapter.

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
"""

import logging
from typing import Optional

import serial
from serial.tools import list_ports

from .transport import OBDTransport, TransportState, TransportError


class SerialTransport(OBDTransport):
    """Serial transport implementation for direct UART communication.

    Supplies the four handle primitives plus its own port discovery;
    OBDTransport holds the connect/disconnect/send_command skeleton
    (change-6481f8ce).
    """

    _IO_ERRORS = (serial.SerialException,)
    # pyserial signals a timeout by returning b'' rather than raising.
    _TIMEOUT_ERRORS = ()
    # read_until returns b'' on timeout with the port still open, so an
    # empty read must NOT be treated as the peer closing.
    _EMPTY_READ_IS_EOF = False

    def __init__(self, port: Optional[str] = None, baudrate: int = 38400, retry_delay: float = 5.0):
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._retry_delay = retry_delay
        self._resolved_port = None

    def _describe(self) -> str:
        """Describe the endpoint, for log messages."""
        port = self._resolved_port or self._port or 'auto'
        return f"serial device {port} at {self._baudrate} baud"

    def _open(self) -> Optional['serial.Serial']:
        """Discover the port if necessary and open it.

        Returns:
            The open port, or None if no device could be found.
        """
        logger = logging.getLogger('SerialTransport')

        # Discover port if not specified
        resolved_port = self._port
        if resolved_port is None:
            resolved_port = self._discover_port()

        if resolved_port is None:
            logger.warning("No serial port found")
            return None

        self._resolved_port = resolved_port
        return serial.Serial(
            port=resolved_port,
            baudrate=self._baudrate,
            timeout=2
        )

    def _close(self, handle) -> None:
        """Close the serial port if it is open."""
        if handle.is_open:
            handle.close()

    def _write(self, handle, data: bytes) -> None:
        """Write bytes to the serial port."""
        handle.write(data)

    def _read(self, handle, n: int) -> bytes:
        """Read up to the '>' prompt.

        pyserial supplies read_until, which returns the whole response
        in one call, so the base class's loop breaks on the first
        iteration. n is part of the abstract signature and unused here.
        """
        return handle.read_until(b'>')

    def _set_timeout(self, handle, timeout: float) -> None:
        """Apply the read timeout. pyserial uses an attribute."""
        handle.timeout = timeout

    def _discover_port(self) -> Optional[str]:
        """Discover available serial ports matching known OBD adapter patterns.

        Returns:
            Optional[str]: The device path if found, None otherwise.
        """
        logger = logging.getLogger('SerialTransport')

        # List of patterns to match against device names and descriptions
        patterns = ['ELM', 'OBD', 'OBDII']

        for port in list_ports.comports():
            # Check device name and description (case-insensitive)
            device_name = port.device
            description = getattr(port, 'description', '')

            # Normalize strings for case-insensitive comparison
            device_name_lower = device_name.lower()
            description_lower = description.lower()

            # Check if any pattern matches in device name or description
            if any(pattern.lower() in device_name_lower for pattern in patterns):
                logger.debug("Probing port %s (matched device name)", device_name)
                if self._probe_port(device_name):
                    logger.info("ELM327 probe passed on %s", device_name)
                    return device_name
                else:
                    logger.warning("Port %s matched pattern but failed ELM327 probe — skipping", device_name)
                    continue

            if any(pattern.lower() in description_lower for pattern in patterns):
                logger.debug("Probing port %s (matched description: %s)", device_name, description)
                if self._probe_port(device_name):
                    logger.info("ELM327 probe passed on %s", device_name)
                    return device_name
                else:
                    logger.warning("Port %s matched pattern but failed ELM327 probe — skipping", device_name)
                    continue

        logger.info("No OBD device found in available serial ports")
        return None

    def _probe_port(self, device: str) -> bool:
        """Probe a serial port to verify it responds with ELM327 identification.

        Opens the specified serial device, sends an ATZ reset command, and checks
        if the response contains "ELM327". This validates that a name-matched port
        is actually connected to an ELM327 OBD-II adapter.

        Args:
            device: The device path to probe (e.g., /dev/cu.ELM327-xxx).

        Returns:
            bool: True if the device responds with an ELM327 identification string,
                  False otherwise (including on any errors).
        """
        logger = logging.getLogger('SerialTransport')
        probe_serial = None
        try:
            # Open the port with a 2-second timeout
            probe_serial = serial.Serial(device, self._baudrate, timeout=2)

            # Send ATZ (reset) command
            probe_serial.write(b'ATZ\r')

            # Read response until '>' prompt
            response = probe_serial.read_until(b'>')

            # Decode and check for ELM327 in response (case-insensitive)
            decoded_response = response.decode('ascii', errors='ignore')
            if 'ELM327' in decoded_response.upper():
                logger.debug("ELM327 identified on %s", device)
                return True
            else:
                logger.debug("No ELM327 response on %s", device)
                return False

        except serial.SerialException as e:
            logger.debug("SerialException probing %s: %s", device, e)
            return False
        except Exception as e:
            logger.debug("Unexpected error probing %s: %s", device, e)
            return False
        finally:
            # Always close the probe connection
            if probe_serial is not None:
                try:
                    if probe_serial.is_open:
                        probe_serial.close()
                except Exception:
                    pass
