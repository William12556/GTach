#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Serial Transport Implementation

This module provides an implementation of the OBDTransport interface using
serial communication for direct connection to an ELM327 OBD-II adapter.
"""

import logging
import platform
import threading
from typing import Optional

import serial
from serial.tools import list_ports

from .transport import OBDTransport, TransportState, TransportError


class SerialTransport(OBDTransport):
    """Serial transport implementation for direct UART communication."""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 38400, retry_delay: float = 5.0):
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._retry_delay = retry_delay
        self._serial = None
        self._state = TransportState.DISCONNECTED
    
    def connect(self) -> bool:
        """Establish a serial connection to the OBD device.
        
        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        logger = logging.getLogger('SerialTransport')
        with self._lock:
            self._state = TransportState.CONNECTING
        
        # Discover port if not specified
        resolved_port = self._port
        if resolved_port is None:
            resolved_port = self._discover_port()
        
        if resolved_port is None:
            logger.warning("No serial port found")
            with self._lock:
                self._state = TransportState.DISCONNECTED
            return False
        
        try:
            self._serial = serial.Serial(
                port=resolved_port,
                baudrate=self._baudrate,
                timeout=2
            )
            
            with self._lock:
                self._state = TransportState.CONNECTED
            logger.info("Connected to serial device %s at %d baud", resolved_port, self._baudrate)
            return True
        except serial.SerialException as e:
            logger.error("Failed to connect to serial device %s: %s", resolved_port, e)
            self._close_serial()
            with self._lock:
                self._state = TransportState.DISCONNECTED
            return False
        except Exception as e:
            logger.error("Unexpected error during serial connection: %s", e)
            self._close_serial()
            with self._lock:
                self._state = TransportState.ERROR
            return False
    
    def disconnect(self) -> None:
        """Close the serial connection."""
        logger = logging.getLogger('SerialTransport')
        self._shutdown.set()
        with self._lock:
            self._close_serial()
            self._state = TransportState.DISCONNECTED
        logger.info("Disconnected from serial device")
    
    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the OBD device and receive the response.
        
        Args:
            command: The OBD command to send.
            timeout: Timeout in seconds for the response.
            
        Returns:
            Optional[str]: The response from the device, or None if the command failed.
        """
        logger = logging.getLogger('SerialTransport')
        if not self.is_connected():
            logger.warning("Cannot send command: transport is not connected")
            return None
        
        try:
            # Prepare the command
            encoded_cmd = (command.strip() + '\r').encode('ascii')
            self._serial.write(encoded_cmd)
            
            # Set timeout for response
            self._serial.timeout = timeout
            
            # Read response until '>' prompt is received
            response = self._serial.read_until(b'>')
            
            # Decode and strip the response
            decoded_response = response.decode('ascii', errors='ignore').strip()
            # Remove the trailing '>' prompt
            decoded_response = decoded_response.rstrip('>').strip()
            return decoded_response
        except serial.SerialException as e:
            logger.error("Error communicating with device: %s", e)
            with self._lock:
                self._state = TransportState.DISCONNECTED
            self._close_serial()
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
    
    def _discover_port(self) -> Optional[str]:
        """Discover available serial ports matching known OBD adapter patterns.

        Returns:
            Optional[str]: The device path if found, None otherwise.
        """
        logger = logging.getLogger('SerialTransport')

        # List of patterns to match against device names and descriptions
        patterns = ['ELM', 'OBD', 'OBDII']

        for port in list_ports.comports():
            # On macOS, skip /dev/tty.* — use /dev/cu.* for outgoing connections.
            # tty.* blocks waiting for an incoming carrier; cu.* is non-blocking.
            if platform.system() == 'Darwin' and '/dev/tty.' in port.device:
                continue

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

    def _close_serial(self) -> None:
        """Close the serial connection if it is open."""
        if self._serial:
            try:
                if self._serial.is_open:
                    self._serial.close()
            except serial.SerialException:
                pass
            finally:
                self._serial = None