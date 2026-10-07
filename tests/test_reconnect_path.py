#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Reconnect-path corrections.

Covers change-907de6de (audit-36b6ea95 A02, A03, A04, A05, A06, A19):
init accepts only a positive 0100 reply and backs off on failure, a
peer close drops the link with a cause, Bluetooth adapter diagnoses are
opt-in, an empty serial read counts as a timeout, and RPM is decoded
only from PID 0C.
"""

import errno
import types

import pytest

import gtach.comm.transport as transport_module
from gtach.comm.obd import OBDProtocol
from gtach.comm.rfcomm import RFCOMMTransport
from gtach.comm.serial_transport import SerialTransport
from gtach.comm.tcp_transport import TCPTransport
from gtach.comm.transport import OBDTransport


def _thread_manager():
    return types.SimpleNamespace(register_thread=lambda *a, **k: None,
                                 update_heartbeat=lambda name: None)


class _ScriptedLink:
    """Answers ELM327 commands; 0100 returns the scripted reply."""

    def __init__(self, reply_0100):
        self.reply_0100 = reply_0100

    def is_connected(self):
        return True

    def send_command(self, command, timeout):
        if command == 'ATZ':
            return 'ELM327 v1.5'
        if command.startswith('AT'):
            return 'OK'
        if command == '0100':
            return self.reply_0100
        return None


def _protocol(link):
    return OBDProtocol(link, _thread_manager(), adapter_pre_initialised=False)


class TestInitValidation:

    @pytest.mark.parametrize('reply', [
        '41 00 BE 3E B8 11',
        '4100BE3EB811',
        'SEARCHING...\r41 00 BE 3E B8 11',
    ])
    def test_positive_reply_accepted(self, reply):
        assert _protocol(_ScriptedLink(reply))._initialize_protocol() is True

    @pytest.mark.parametrize('reply', [
        'NO DATA', 'UNABLE TO CONNECT', '?', '7F 01 12', None,
    ])
    def test_other_replies_rejected(self, reply):
        assert _protocol(_ScriptedLink(reply))._initialize_protocol() is False


class TestInitBackOff:

    def test_failure_waits_on_shutdown_event(self, monkeypatch):
        obd = _protocol(_ScriptedLink(None))
        results = iter([False, False])
        waits = []
        real_wait = obd.shutdown_event.wait

        def init():
            try:
                return next(results)
            except StopIteration:
                obd.shutdown_event.set()
                return False

        def wait(timeout=None):
            waits.append(timeout)
            return real_wait(0)

        monkeypatch.setattr(obd, '_initialize_protocol', init)
        monkeypatch.setattr(obd.shutdown_event, 'wait', wait)

        obd._protocol_loop()

        assert waits.count(2.0) >= 2


class _StubTimeout(Exception):
    pass


class _Stub(OBDTransport):
    """Scripted handle primitives."""

    _IO_ERRORS = (OSError,)
    _TIMEOUT_ERRORS = (_StubTimeout,)

    def __init__(self, reads=None, open_error=None):
        super().__init__()
        self._reads = list(reads or [])
        self._open_error = open_error
        self.closed_handles = []

    def _describe(self):
        return 'stub-peer'

    def _open(self):
        if self._open_error is not None:
            raise self._open_error
        return object()

    def _close(self, handle):
        self.closed_handles.append(handle)

    def _write(self, handle, data):
        pass

    def _set_timeout(self, handle, timeout):
        pass

    def _read(self, handle, n):
        if self._reads:
            return self._reads.pop(0)
        return b''


class TestPeerClose:

    def test_eof_drops_link_with_cause(self):
        transport = _Stub()
        assert transport.connect()

        assert transport.send_command('010C', timeout=0.2) is None
        assert len(transport.closed_handles) == 1
        assert transport.is_connected() is False
        assert transport.last_failure_cause == 'adapter closed the connection'


class TestAdapterChecksOptIn:

    def _fail_six(self, transport):
        causes = []
        for _ in range(6):
            assert transport.connect() is False
            causes.append(transport.last_failure_cause)
        return causes

    def test_non_bluetooth_never_reports_adapter_faults(self, monkeypatch):
        monkeypatch.setattr(transport_module, '_bluetooth_adapter_present', lambda: False)
        transport = _Stub(open_error=OSError(errno.ECONNREFUSED, 'refused'))

        causes = self._fail_six(transport)

        assert 'no bluetooth controller' not in causes
        assert transport_module._WEDGED_LINK_CAUSE not in causes

    def test_bluetooth_reports_missing_controller(self, monkeypatch):
        monkeypatch.setattr(transport_module, '_bluetooth_adapter_present', lambda: False)
        transport = _Stub(open_error=OSError(errno.ECONNREFUSED, 'refused'))
        transport._ADAPTER_CHECKS = True

        assert self._fail_six(transport)[-1] == 'no bluetooth controller'

    def test_class_defaults(self):
        assert OBDTransport._ADAPTER_CHECKS is False
        assert RFCOMMTransport._ADAPTER_CHECKS is True
        assert TCPTransport._ADAPTER_CHECKS is False
        assert SerialTransport._ADAPTER_CHECKS is False


class _SerialStub(_Stub):
    _EMPTY_READ_IS_EOF = False


class TestSerialEmptyRead:

    def test_silent_port_drops_link_once(self, monkeypatch):
        transport = _SerialStub()
        assert transport.connect()
        drops = []
        real_drop = transport.drop_link

        def drop_link(cause=None):
            drops.append(cause)
            real_drop(cause)

        monkeypatch.setattr(transport, 'drop_link', drop_link)

        for _ in range(5):
            transport.send_command('010C', timeout=0.1)

        assert len(drops) == 1
        assert transport.is_connected() is False

    def test_partial_response_still_returned(self):
        transport = _SerialStub(reads=[b'41 0C 1A F8', b''])
        assert transport.connect()

        assert transport.send_command('010C', timeout=0.2) == '41 0C 1A F8'


class TestRpmPidCheck:

    def test_only_pid_0c_is_decoded(self):
        replies = iter(['41 0D 1A F8', '41 0C 1A F8'])
        link = types.SimpleNamespace(
            is_connected=lambda: True,
            send_command=lambda command, timeout: next(replies))
        obd = _protocol(link)

        assert obd._request_rpm() is None
        response = obd._request_rpm()
        assert response is not None
        assert response.data == b'\x1a\xf8'
