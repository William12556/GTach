#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Simulation Transport for GTach

Provides a synthetic OBD-II transport for hardware-free testing.
Returns scripted ELM327 responses including a sine-wave RPM sweep.
"""

import logging
import math
import time
import threading
from typing import Optional

from .transport import OBDTransport, TransportState


class SimTransport(OBDTransport):
    """Simulation transport returning synthetic ELM327 responses.

    This transport allows full GTach application testing without hardware.
    RPM values sweep from 800 to 6500 RPM on a ~60 second sine wave period.
    All standard ELM327 init commands return canonical responses.
    """

    def __init__(self):
        """Initialize the simulation transport."""
        super().__init__()
        self.logger = logging.getLogger('SimTransport')
        self._connected = False
        self._state = TransportState.DISCONNECTED

    def connect(self) -> bool:
        """Establish simulated connection (always succeeds immediately).

        Returns:
            bool: Always True.
        """
        with self._lock:
            self._shutdown.clear()
            self._connected = True
            self._state = TransportState.CONNECTED
            self.logger.info("SimTransport connected")
            return True

    def disconnect(self) -> None:
        """Close the simulated connection."""
        with self._lock:
            self._shutdown.set()
            self._connected = False
            self._state = TransportState.DISCONNECTED
            self.logger.info("SimTransport disconnected")

    def is_connected(self) -> bool:
        """Check if the simulated transport is connected.

        Returns:
            bool: Always True (sim never drops connection).
        """
        return True

    @property
    def state(self) -> TransportState:
        """Get the current transport state.

        Returns:
            TransportState: Always CONNECTED.
        """
        return TransportState.CONNECTED

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command and return a synthetic ELM327 response.

        Args:
            command: OBD-II command string (e.g., '010C' for RPM).
            timeout: Unused (responses are instantaneous).

        Returns:
            str: Synthetic ELM327 response, or 'NO DATA' for unknown commands.
        """
        cmd = command.strip().upper()
        self.logger.debug(f"SimTransport TX: {cmd}")

        # Dispatch command to appropriate handler
        response = self._handle_command(cmd)

        self.logger.debug(f"SimTransport RX: {response}")
        return response

    def _handle_command(self, cmd: str) -> str:
        """Map commands to synthetic responses.

        Args:
            cmd: Upper-case stripped command string.

        Returns:
            str: Synthetic ELM327 response.
        """
        # ELM327 initialization commands
        if cmd == 'ATZ':
            return 'ELM327 v1.5'
        elif cmd in ('ATE0', 'ATL0', 'ATS0', 'ATH0'):
            return 'OK'
        elif cmd.startswith('ATSP'):
            return 'OK'

        # OBD-II commands
        elif cmd == '0100':
            # Supported PIDs 01-20
            return '41 00 BE 3E B8 11'

        elif cmd == '010C':
            # RPM query - return sine wave 800-6500 RPM, ~12s period
            return self._compute_rpm_response()

        else:
            # Unknown command
            return 'NO DATA'

    def _compute_rpm_response(self) -> str:
        """Compute synthetic RPM value on a sine wave sweep.

        Returns:
            str: ELM327-formatted RPM response (e.g., '41 0C 1A 2B').
        """
        # Sine wave: 800 + 2850 * (1 + sin(t * 2π / 60))
        # Results in range 800-6500 RPM over ~60 second period
        t = time.time()
        rpm = 800 + 2850 * (1 + math.sin(t * 2 * math.pi / 60.0))

        # Encode RPM as ELM327 hex: RPM = ((A * 256) + B) / 4
        # Therefore: A = (rpm * 4) >> 8, B = (rpm * 4) & 0xFF
        rpm_encoded = int(rpm * 4)
        a = (rpm_encoded >> 8) & 0xFF
        b = rpm_encoded & 0xFF

        return f'41 0C {a:02X} {b:02X}'
