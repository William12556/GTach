# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Response alignment after a late reply (issue-dc52c4e4).

On the Pi the first 0100 after ATSP0 answered just after its 1.0 s
timeout. The late reply was then read as the reply to the next command,
and every later command read its predecessor's reply, so initialisation
failed on every retry. These tests drive OBDTransport.send_command over
a real socket pair, so the discard step and the prompt handling run
against a real file descriptor.
"""

import socket
import types

from gtach.comm.obd import OBDProtocol
from gtach.comm.serial_transport import SerialTransport
from gtach.comm.transport import OBDTransport


class _PairTransport(OBDTransport):
    """Transport over a socket pair; the peer answers scripted commands."""

    _IO_ERRORS = (OSError,)
    _TIMEOUT_ERRORS = (socket.timeout,)

    def __init__(self, replies):
        super().__init__()
        self.replies = dict(replies)
        self.peer = None

    def _open(self):
        local, self.peer = socket.socketpair()
        return local

    def _close(self, handle):
        handle.close()
        if self.peer is not None:
            self.peer.close()

    def _write(self, handle, data):
        handle.sendall(data)
        reply = self.replies.get(data.decode("ascii").strip())
        if reply is not None:
            self.peer.sendall(reply)

    def _read(self, handle, n):
        return handle.recv(n)


class _ScriptedReads(OBDTransport):
    """Transport whose reads are scripted; the handle is a plain object."""

    _IO_ERRORS = (OSError,)
    _TIMEOUT_ERRORS = (socket.timeout,)

    def __init__(self, reads):
        super().__init__()
        self._reads = list(reads)

    def _open(self):
        return object()

    def _close(self, handle):
        pass

    def _write(self, handle, data):
        pass

    def _set_timeout(self, handle, timeout):
        pass

    def _read(self, handle, n):
        if self._reads:
            return self._reads.pop(0)
        raise socket.timeout("no script left")


class TestDiscardStaleInput:

    def test_stale_bytes_do_not_answer_the_next_command(self):
        transport = _PairTransport({"ATZ": b"\r\rELM327 v1.5\r\r>"})
        assert transport.connect()
        try:
            transport.peer.sendall(b"SEARCHING...\r4100983A8013\r\r>")

            assert transport.send_command("ATZ", timeout=1.0) == "ELM327 v1.5"
        finally:
            transport.disconnect()

    def test_late_reply_does_not_shift_later_commands(self):
        transport = _PairTransport({"ATE0": b"OK\r\r>"})
        assert transport.connect()
        try:
            # 0100 gets no reply within its timeout ...
            assert transport.send_command("0100", timeout=0.2) is None
            # ... and its reply arrives afterwards.
            transport.peer.sendall(b"4100BE3FA813\r\r>")

            assert transport.send_command("ATE0", timeout=1.0) == "OK"
        finally:
            transport.disconnect()

    def test_handle_without_fileno_discards_nothing(self):
        transport = _ScriptedReads([])
        assert transport._discard_input(object()) == 0


class TestFirstPrompt:

    def test_bytes_after_the_prompt_are_dropped(self):
        transport = _ScriptedReads([b"OK\r\r>4100983A8013\r"])
        assert transport.connect()

        assert transport.send_command("ATSP0", timeout=1.0) == "OK"

    def test_reply_without_trailing_data_is_unchanged(self):
        transport = _ScriptedReads([b"410C1AF8\r\r>"])
        assert transport.connect()

        assert transport.send_command("010C", timeout=1.0) == "410C1AF8"


class TestSerialDiscard:

    def test_uses_the_port_buffer_reset(self):
        resets = []
        port = types.SimpleNamespace(
            in_waiting=7, reset_input_buffer=lambda: resets.append(1)
        )

        assert SerialTransport(port="/dev/null")._discard_input(port) == 7
        assert resets == [1]

    def test_empty_buffer_is_not_reset(self):
        resets = []
        port = types.SimpleNamespace(
            in_waiting=0, reset_input_buffer=lambda: resets.append(1)
        )

        assert SerialTransport(port="/dev/null")._discard_input(port) == 0
        assert resets == []


class _RecordingLink:
    """Records (command, timeout); answers like an ELM327."""

    def __init__(self):
        self.sent = []

    def is_connected(self):
        return True

    def send_command(self, command, timeout):
        self.sent.append((command, timeout))
        if command == "0100":
            return "SEARCHING...\r4100BE3FA813"
        return "OK"


class TestInitTimeout:

    def test_init_0100_allows_for_protocol_search(self):
        link = _RecordingLink()
        manager = types.SimpleNamespace(
            register_thread=lambda *a, **k: None, update_heartbeat=lambda name: None
        )
        protocol = OBDProtocol(link, manager, adapter_pre_initialised=False)

        assert protocol._initialize_protocol() is True
        assert ("0100", 5.0) in link.sent
        assert OBDProtocol._INIT_0100_TIMEOUT_S == 5.0
