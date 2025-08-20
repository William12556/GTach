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
from .bluetooth import BluetoothManager
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
    
    def __init__(self, bluetooth_manager: BluetoothManager, thread_manager: ThreadManager):
        self.logger = logging.getLogger('OBDProtocol')
        self.bluetooth = bluetooth_manager
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
                
                if not self.bluetooth.is_connected():
                    time.sleep(0.1)
                    continue
                
                if not self._initialize_protocol():
                    continue
                
                while self.bluetooth.is_connected():
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
            self._send_command(b"ATZ")
            self._send_command(b"ATE0")
            self._send_command(b"ATSP0")
            self._send_command(b"ATSP8")
            
            response = self._send_command(b"0100")
            if not response or response.startswith('7F'):
                raise Exception("No connection to vehicle")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    def _send_command(self, command: bytes) -> Optional[str]:
        """Send command to ELM327 device using Bleak interface"""
        try:
            if not self.bluetooth.is_connected():
                return None
                
            # Convert bytes command to string for Bleak interface
            command_str = command.decode('ascii')
            
            # Use the new Bleak-based send_command method
            response = self.bluetooth.send_command(command_str, timeout=self.timeout)
            
            return response
            
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
                data = bytes.fromhex(response.replace(' ', ''))
                
                return OBDResponse(
                    pid=self.RPM_PID,
                    data=data[2:4],
                    timestamp=time.time()
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"RPM request error: {e}")
            return None