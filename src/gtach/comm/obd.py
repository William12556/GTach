#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
OBD protocol handling for GTach display application.
Manages OBD communication and data processing.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional
from .transport import OBDTransport
from ..core import ThreadManager

@dataclass
class OBDResponse:
    """OBD response data structure"""
    pid: int
    data: bytes
    timestamp: float
    error: Optional[str] = None

class OBDProtocol:
    """Handles OBD protocol communication"""
    
    def __init__(self, transport: OBDTransport, thread_manager: ThreadManager):
        self.logger = logging.getLogger('OBDProtocol')
        self.transport = transport
        self.thread_manager = thread_manager
        self.shutdown_event = threading.Event()
        
        self.PROMPT = b'>'
        self.RPM_PID = 0x0C
        self.timeout = 1.0
        
        self.obd_thread = threading.Thread(
            target=self._protocol_loop,
            name='OBDProtocol'
        )
        self.thread_manager.register_thread('obd_protocol', self.obd_thread)

    def start(self) -> None:
        """Start protocol handler"""
        self.obd_thread.start()
        self.logger.info("OBD protocol handler started")

    def stop(self) -> None:
        """Stop protocol handler"""
        self.shutdown_event.set()
        self.obd_thread.join()
        self.logger.info("OBD protocol handler stopped")

    def _protocol_loop(self) -> None:
        """Main protocol handling loop"""
        while not self.shutdown_event.is_set():
            try:
                self.thread_manager.update_heartbeat('obd_protocol')
                
                if not self.transport.is_connected():
                    time.sleep(0.1)
                    continue
                
                if not self._initialize_protocol():
                    continue
                
                while self.transport.is_connected():
                    rpm_data = self._request_rpm()
                    if rpm_data:
                        self.thread_manager.message_queue.put(rpm_data)
                        self.thread_manager.data_available.set()
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Protocol error: {e}", exc_info=True)
                time.sleep(1.0)

    def _initialize_protocol(self) -> bool:
        """Initialize OBD protocol and configure ELM327"""
        try:
            # ATZ resets the adapter — allow extra time for emulator/hardware reset
            self._send_command(b"ATZ", timeout=5.0)
            self._send_command(b"ATE0")
            self._send_command(b"ATL0")  # Line feeds off
            self._send_command(b"ATS0")  # Spaces off
            self._send_command(b"ATSP0") # Auto protocol
            
            response = self._send_command(b"0100")
            if not response or response.startswith('7F'):
                raise Exception("No connection to vehicle")

            return True

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    def _send_command(self, command: bytes, timeout: float = None) -> Optional[str]:
        """Send command to ELM327 device."""
        try:
            if not self.transport.is_connected():
                return None

            command_str = command.decode('ascii')
            effective_timeout = timeout if timeout is not None else self.timeout
            return self.transport.send_command(command_str, timeout=effective_timeout)

        except Exception as e:
            self.logger.error(f"Command error: {e}")
            return None

    def _request_rpm(self) -> Optional[OBDResponse]:
        """Request engine RPM"""
        try:
            response = self._send_command(b"010C")
            if not response:
                return None
                
            if len(response) >= 8 and response.startswith('41'):
                # Strip whitespace and non-hex characters (echo, \r\n, prompts)
                import re
                hex_str = re.sub(r'[^0-9A-Fa-f]', '', response)
                if len(hex_str) < 8:
                    return None
                data = bytes.fromhex(hex_str)

                return OBDResponse(
                    pid=self.RPM_PID,
                    data=data[2:4],
                    timestamp=time.time()
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"RPM request error: {e}")
            return None