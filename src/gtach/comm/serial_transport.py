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
            # Check device name and description (case-insensitive)
            device_name = port.device
            description = getattr(port, 'description', '')
            
            # Normalize strings for case-insensitive comparison
            device_name_lower = device_name.lower()
            description_lower = description.lower()
            
            # Check if any pattern matches in device name or description
            if any(pattern.lower() in device_name_lower for pattern in patterns):
                logger.info("Found OBD device on port %s", device_name)
                return device_name
            
            if any(pattern.lower() in description_lower for pattern in patterns):
                logger.info("Found OBD device (description: %s) on port %s", description, device_name)
                return device_name
        
        logger.info("No OBD device found in available serial ports")
        return None
    
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