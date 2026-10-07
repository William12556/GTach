#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Process-restart recovery and bounded OBD heartbeat gaps.

Covers change-860fd5f7 (audit-36b6ea95 A01/B02, B01, B05, B03). No
thread is restarted in process: a stalled or exited critical thread
(display, obd_protocol) leads to graceful shutdown and systemd restarts
the process. stop_thread calls the registered stop_func, dead registry
entries are replaced, the OBD loop honours its stop signal, every OBD
command refreshes the heartbeat, one command is bounded by a monotonic
deadline, and SimTransport reports its real connection state.
"""

import logging
import threading
import time
import types

import pytest

from gtach.app import GTachApplication
from gtach.comm.obd import OBDProtocol
from gtach.comm.sim_transport import SimTransport
from gtach.comm.transport import OBDTransport, TransportState
from gtach.core.thread import ThreadManager, ThreadStatus
from gtach.core.watchdog import WatchdogMonitor

JOIN_TIMEOUT = 2.0


@pytest.fixture
def manager():
    tm = ThreadManager()
    yield tm
    tm.shutdown(timeout=2.0)


def _watchdog(manager, calls):
    return WatchdogMonitor(manager, shutdown_callback=lambda: calls.append('shutdown'))


def _age(manager, name, age):
    manager.threads[name].last_heartbeat = time.monotonic() - age


def _exited_thread(name):
    t = threading.Thread(target=lambda: None, name=name, daemon=True)
    t.start()
    t.join(JOIN_TIMEOUT)
    return t


class TestEscalationWithoutRestart:

    def test_stale_obd_protocol_shuts_down(self, manager):
        calls = []
        watchdog = _watchdog(manager, calls)
        manager.register_thread('obd_protocol', threading.Thread(target=lambda: None))
        _age(manager, 'obd_protocol', watchdog.critical_timeout + 5)

        watchdog._check_thread_health()

        assert calls == ['shutdown']

    def test_stale_non_critical_thread_logs_only(self, manager, caplog):
        calls = []
        watchdog = _watchdog(manager, calls)
        original = threading.Thread(target=lambda: None)
        manager.register_thread('worker', original)
        _age(manager, 'worker', watchdog.critical_timeout + 5)

        with caplog.at_level(logging.ERROR, logger='WatchdogMonitor'):
            for _ in range(3):
                watchdog._check_thread_health()
                watchdog.thread_health['worker'].last_recovery_time = float('-inf')

        assert any(r.levelno == logging.ERROR for r in caplog.records)
        assert manager.threads['worker'].thread is original
        assert calls == []


class TestDeadThreadRule:

    def test_exited_critical_thread_shuts_down(self, manager):
        calls = []
        watchdog = _watchdog(manager, calls)
        manager.register_thread('display', _exited_thread('display'))
        manager.threads['display'].status = ThreadStatus.RUNNING

        watchdog._check_thread_health()

        assert manager.threads['display'].status == ThreadStatus.STOPPED
        assert calls == ['shutdown']

    def test_exited_non_critical_thread_is_marked_stopped(self, manager, caplog):
        calls = []
        watchdog = _watchdog(manager, calls)
        manager.register_thread('worker', _exited_thread('worker'))
        manager.threads['worker'].status = ThreadStatus.RUNNING

        with caplog.at_level(logging.INFO, logger='WatchdogMonitor'):
            watchdog._check_thread_health()

        assert manager.threads['worker'].status == ThreadStatus.STOPPED
        assert calls == []
        assert any(r.levelno == logging.INFO and 'exited' in r.getMessage()
                   for r in caplog.records)

    def test_registered_but_not_started_is_left_alone(self, manager):
        calls = []
        watchdog = _watchdog(manager, calls)
        manager.register_thread('display', threading.Thread(target=lambda: None))

        watchdog._check_thread_health()

        assert manager.threads['display'].status == ThreadStatus.STARTING
        assert calls == []


class TestStopThread:

    def test_stop_func_runs_unlocked_before_join(self, manager):
        release = threading.Event()
        worker = threading.Thread(target=release.wait, args=(JOIN_TIMEOUT,), daemon=True)
        recorded = []
        stop_calls = []

        def stop_func():
            stop_calls.append(1)

            def probe():
                acquired = manager._state_lock.acquire(timeout=1)
                if acquired:
                    manager._state_lock.release()
                recorded.append(acquired)
            helper = threading.Thread(target=probe, daemon=True)
            helper.start()
            helper.join(JOIN_TIMEOUT)
            release.set()

        manager.register_thread('x', worker, stop_func=stop_func)
        worker.start()

        assert manager.stop_thread('x', timeout=JOIN_TIMEOUT) is True
        assert stop_calls == [1]
        assert recorded == [True]

    def test_stop_func_that_raises_still_joins(self, manager):
        release = threading.Event()
        worker = threading.Thread(target=release.wait, args=(0.2,), daemon=True)

        def stop_func():
            raise RuntimeError('boom')

        manager.register_thread('x', worker, stop_func=stop_func)
        worker.start()

        assert manager.stop_thread('x', timeout=JOIN_TIMEOUT) is True


class TestRegisterThread:

    def test_dead_entry_is_replaced(self, manager):
        manager.register_thread('x', _exited_thread('x'))
        manager.threads['x'].status = ThreadStatus.RUNNING
        t2 = threading.Thread(target=lambda: None)

        manager.register_thread('x', t2)

        assert manager.threads['x'].thread is t2

    def test_live_entry_is_kept(self, manager, caplog):
        release = threading.Event()
        original = threading.Thread(target=release.wait, args=(JOIN_TIMEOUT,), daemon=True)
        manager.register_thread('x', original)
        original.start()
        manager.threads['x'].status = ThreadStatus.RUNNING
        try:
            with caplog.at_level(logging.WARNING, logger='ThreadManager'):
                manager.register_thread('x', threading.Thread(target=lambda: None))

            assert manager.threads['x'].thread is original
            assert any('already exists' in r.getMessage() for r in caplog.records)
        finally:
            release.set()
            original.join(JOIN_TIMEOUT)


class TestOBDProtocol:

    def test_stop_ends_loop_while_connected(self, manager):
        transport = SimTransport()
        transport.connect()
        obd = OBDProtocol(transport, manager)
        obd.start()
        time.sleep(0.3)

        obd.stop()
        obd.obd_thread.join(JOIN_TIMEOUT)

        assert transport.is_connected()
        assert not obd.obd_thread.is_alive()

    def test_every_command_refreshes_heartbeat(self):
        beats = []
        thread_manager = types.SimpleNamespace(
            register_thread=lambda *a, **k: None,
            update_heartbeat=beats.append)
        transport = types.SimpleNamespace(
            is_connected=lambda: True,
            send_command=lambda command, timeout: 'OK')
        obd = OBDProtocol(transport, thread_manager)

        assert obd._send_command(b'ATE0') == 'OK'
        assert beats == ['obd_protocol']


class TestSimTransportState:

    def test_reports_real_state(self):
        transport = SimTransport()

        transport.connect()
        assert transport.is_connected() is True
        assert transport.state == TransportState.CONNECTED

        transport.disconnect()
        assert transport.is_connected() is False
        assert transport.state == TransportState.DISCONNECTED


class _FakeTransport(OBDTransport):
    """Scripted handle primitives; records the call order."""

    def __init__(self, reply):
        super().__init__()
        self._reply = reply
        self.calls = []

    def _open(self):
        return object()

    def _close(self, handle):
        pass

    def _write(self, handle, data):
        self.calls.append('write')

    def _read(self, handle, n):
        self.calls.append('read')
        time.sleep(0.01)
        return self._reply

    def _set_timeout(self, handle, timeout):
        self.calls.append('set_timeout')


class TestSendCommandDeadline:

    def test_endless_searching_is_bounded(self):
        transport = _FakeTransport(b'SEARCHING')
        assert transport.connect()

        start = time.monotonic()
        result = transport.send_command('0100', timeout=0.2)
        elapsed = time.monotonic() - start

        assert result is None
        assert elapsed < 0.2 + 1.0 + 0.5
        assert transport._consecutive_timeouts == 1

    def test_timeout_set_before_write(self):
        transport = _FakeTransport(b'41 0C 1A F8\r>')
        assert transport.connect()

        result = transport.send_command('010C', timeout=0.2)

        assert transport.calls.index('set_timeout') < transport.calls.index('write')
        assert result == '41 0C 1A F8'


class TestReEnterSetup:

    def test_stops_transport_then_obd_through_manager(self):
        app = object.__new__(GTachApplication)
        app.logger = logging.getLogger('test.thread_lifecycle')
        app._obd_lock = threading.Lock()  # issue-4005360c
        stops = []
        direct = []
        app._thread_manager = types.SimpleNamespace(
            stop_thread=lambda name, timeout: stops.append((name, timeout)))
        app._transport = types.SimpleNamespace(disconnect=lambda: direct.append('disconnect'))
        app._obd = types.SimpleNamespace(stop=lambda: direct.append('obd.stop'))
        app._start_setup_mode = lambda: None

        app._re_enter_setup()

        assert stops == [('transport', 2.0), ('obd_protocol', 2.0)]
        assert direct == []
