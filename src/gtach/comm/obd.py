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
import queue
import re
import threading
import time
from dataclasses import dataclass
from typing import Optional

from ..core import ThreadManager
from .transport import OBDTransport


@dataclass
class OBDResponse:
    """OBD response data structure"""

    pid: int
    data: bytes
    timestamp: float
    error: Optional[str] = None


class OBDProtocol:
    """Handles OBD protocol communication"""

    # Wait after a failed initialisation before retrying (issue-907de6de).
    _INIT_RETRY_DELAY_S: float = 2.0

    # Timeout for the initialisation 0100. After ATSP0 the adapter
    # searches for the vehicle protocol before answering
    # ('SEARCHING...'), which takes over 1 s on the emulator and can
    # take several seconds on a vehicle. With the transport's 1.0 s
    # margin the read is bounded at 6 s, below the watchdog's 15 s
    # warning threshold (issue-dc52c4e4).
    _INIT_0100_TIMEOUT_S: float = 5.0

    # Settle after connecting to a pre-initialised adapter, waited in
    # slices with a heartbeat after each (issue-04c18cda).
    _PRE_INIT_SETTLE_S: float = 1.5
    _SETTLE_SLICE_S: float = 0.5

    def __init__(
        self,
        transport: OBDTransport,
        thread_manager: ThreadManager,
        poll_interval_s: float = 0.05,
        adapter_pre_initialised: bool = False,
    ):
        self.logger = logging.getLogger("OBDProtocol")
        self.transport = transport
        self.thread_manager = thread_manager
        self.shutdown_event = threading.Event()

        self.PROMPT = b">"
        self.RPM_PID = 0x0C
        self.timeout = 1.0
        self.poll_interval_s = poll_interval_s
        self._adapter_initialised = adapter_pre_initialised
        self.logger.info(
            f"OBDProtocol init — adapter_pre_initialised={adapter_pre_initialised}"
        )

        self.obd_thread = threading.Thread(
            target=self._protocol_loop, name="OBDProtocol"
        )
        self.thread_manager.register_thread(
            "obd_protocol", self.obd_thread, stop_func=self.stop
        )

    def start(self) -> None:
        """Start protocol handler"""
        self.obd_thread.start()
        self.logger.info("OBD protocol handler started")

    def stop(self) -> None:
        """Stop protocol handler"""
        self._adapter_initialised = False
        self.shutdown_event.set()
        if self.obd_thread.is_alive():
            self.obd_thread.join(timeout=5.0)
        self.logger.info("OBD protocol handler stopped")

    def _protocol_loop(self) -> None:
        """Main protocol handling loop"""
        while not self.shutdown_event.is_set():
            try:
                self.thread_manager.update_heartbeat("obd_protocol")

                if not self.transport.is_connected():
                    time.sleep(0.1)
                    continue

                if not self._initialize_protocol():
                    # Back off rather than retry at once (issue-907de6de).
                    self.thread_manager.update_heartbeat("obd_protocol")
                    self.shutdown_event.wait(self._INIT_RETRY_DELAY_S)
                    continue

                while (
                    self.transport.is_connected() and not self.shutdown_event.is_set()
                ):
                    self.thread_manager.update_heartbeat("obd_protocol")
                    rpm_data = self._request_rpm()
                    if rpm_data:
                        try:
                            self.thread_manager.message_queue.put_nowait(rpm_data)
                        except queue.Full:
                            # Queue full — discard oldest, insert newest.
                            # Narrowed from a catch-all handler: a genuine
                            # programming error here was being counted as
                            # queue pressure and discarded, three times per
                            # sample (core review §4.2). Anything other
                            # than Full or Empty now reaches the loop's own
                            # handler below and is logged with a traceback.
                            try:
                                self.thread_manager.message_queue.get_nowait()
                            except queue.Empty:
                                pass
                            try:
                                self.thread_manager.message_queue.put_nowait(rpm_data)
                            except queue.Full:
                                pass
                        self.thread_manager.data_available.set()
                    time.sleep(self.poll_interval_s)

                self._adapter_initialised = False
                self.logger.debug("Transport disconnected — adapter init flag reset")

            except Exception as e:
                self.logger.error(f"Protocol error: {e}", exc_info=True)
                self.thread_manager.update_heartbeat("obd_protocol")
                time.sleep(1.0)

    def _initialize_protocol(self) -> bool:
        """Initialize OBD protocol and configure ELM327"""
        try:
            self.thread_manager.update_heartbeat("obd_protocol")
            if not self._adapter_initialised:
                # Full init — ATZ resets the adapter (slow on emulator)
                self._send_command(b"ATZ", timeout=5.0)
                self.thread_manager.update_heartbeat("obd_protocol")
            else:
                # Adapter already reset by setup probe — skip ATZ only.
                # Settle briefly to allow emulator to accept new RFCOMM connection.
                # Sliced so a stop interrupts it and the heartbeat gap stays
                # within one slice (issue-04c18cda).
                self.logger.debug(
                    "Skipping ATZ — adapter pre-initialised; "
                    f"settling {self._PRE_INIT_SETTLE_S}s"
                )
                deadline = time.monotonic() + self._PRE_INIT_SETTLE_S
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    if self.shutdown_event.wait(min(self._SETTLE_SLICE_S, remaining)):
                        self.logger.debug("Settle interrupted by stop")
                        return False
                    self.thread_manager.update_heartbeat("obd_protocol")

            # Config commands are fast and do not reset the adapter. They must
            # always run — ATE0 (echo off) is required for correct response parsing.
            self._send_command(b"ATE0")
            self._send_command(b"ATL0")  # Line feeds off
            self._send_command(b"ATS0")  # Spaces off
            self._send_command(b"ATSP0")  # Auto protocol
            self.thread_manager.update_heartbeat("obd_protocol")

            response = self._send_command(b"0100", timeout=self._INIT_0100_TIMEOUT_S)
            # Only a positive 0100 reply proves the vehicle answered;
            # NO DATA, '?' and 7F replies do not (issue-907de6de).
            normalised = re.sub(r"\s", "", (response or "").upper())
            if "4100" not in normalised:
                raise Exception(f"No valid 0100 response: {response!r}")

            self._adapter_initialised = True
            return True

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def _send_command(self, command: bytes, timeout: float = None) -> Optional[str]:
        """Send command to ELM327 device."""
        try:
            # One heartbeat per command bounds the gap (issue-860fd5f7).
            self.thread_manager.update_heartbeat("obd_protocol")
            if not self.transport.is_connected():
                return None

            command_str = command.decode("ascii")
            effective_timeout = timeout if timeout is not None else self.timeout
            return self.transport.send_command(command_str, timeout=effective_timeout)

        except Exception as e:
            self.logger.error(f"Command error: {e}", exc_info=True)
            return None

    def _request_rpm(self) -> Optional[OBDResponse]:
        """Request engine RPM"""
        try:
            response = self._send_command(b"010C")
            if not response:
                return None

            if len(response) >= 8 and response.startswith("41"):
                # Strip whitespace and non-hex characters (echo, \r\n, prompts)
                hex_str = re.sub(r"[^0-9A-Fa-f]", "", response)
                if len(hex_str) < 8:
                    return None
                data = bytes.fromhex(hex_str)
                # Decode only a mode 01 reply for PID 0C (issue-907de6de).
                if len(data) < 4 or data[0] != 0x41 or data[1] != self.RPM_PID:
                    return None

                return OBDResponse(
                    pid=self.RPM_PID, data=data[2:4], timestamp=time.time()
                )

            return None

        except Exception as e:
            self.logger.error(f"RPM request error: {e}", exc_info=True)
            return None
