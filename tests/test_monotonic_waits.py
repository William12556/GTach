#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Clock-step-safe waits (issue-4f671d09).

On Python < 3.11 a timed Event.wait has an absolute CLOCK_REALTIME
deadline, so a backward wall-clock step extends it. The supervision
loops and two one-shot waits now use gtach.utils.waits.wait_for_event,
which never calls Event.wait. The call-site tests replace each event
with a double whose wait() raises and counts, so any remaining timed
Event.wait fails the test even where the caller swallows exceptions.
"""

import logging
import threading
import time
from typing import Any, Callable, List, Optional

from gtach.comm.obd import OBDProtocol
from gtach.comm.sim_transport import SimTransport
from gtach.comm.transport import OBDTransport
from gtach.core.thread import ThreadManager
from gtach.core.watchdog import WatchdogMonitor
from gtach.display.setup_components.bluetooth.interface import (
    BluetoothSetupInterface,
)
from gtach.display.splash import SplashScreen
from gtach.utils import waits
from gtach.utils.waits import _POLL_SLICE_S, wait_for_event

# Bound on every blocking call, so a hung loop fails instead of hanging.
JOIN_TIMEOUT = 5.0


class _NoWaitEvent(threading.Event):
    """Event whose wait() records the call and raises AssertionError."""

    def __init__(self) -> None:
        super().__init__()
        self.wait_calls = 0

    def wait(self, timeout: Optional[float] = None) -> bool:
        self.wait_calls += 1
        raise AssertionError("Event.wait called")


class _IsSetOnly:
    """Exposes only is_set(); proves the helper needs nothing else."""

    def __init__(self) -> None:
        self.flag = False

    def is_set(self) -> bool:
        return self.flag


def _run_bounded(target: Callable[[], Any]) -> Any:
    """Run target on a thread; fail if it hangs, re-raise what it raised."""
    outcome: List[Any] = []

    def _runner() -> None:
        try:
            outcome.append(("ok", target()))
        except BaseException as e:
            outcome.append(("err", e))

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join(JOIN_TIMEOUT)
    assert not thread.is_alive(), "call did not return"
    kind, value = outcome[0]
    if kind == "err":
        raise value
    return value


class TestWaitForEvent:
    def test_already_set_returns_true_without_sleeping(self, monkeypatch):
        sleeps: List[float] = []
        monkeypatch.setattr(waits.time, "sleep", sleeps.append)
        event = threading.Event()
        event.set()

        assert wait_for_event(event, 5.0) is True
        assert sleeps == []

    def test_set_by_another_thread_wakes_within_one_slice(self):
        event = threading.Event()
        timer = threading.Timer(0.2, event.set)
        start = time.monotonic()
        timer.start()

        assert wait_for_event(event, 5.0) is True
        elapsed = time.monotonic() - start
        timer.join()
        assert elapsed < 0.2 + _POLL_SLICE_S + 0.2

    def test_never_set_times_out(self):
        event = threading.Event()
        start = time.monotonic()

        assert wait_for_event(event, 0.3) is False
        elapsed = time.monotonic() - start
        assert 0.3 <= elapsed < 0.6

    def test_object_with_only_is_set(self):
        event = _IsSetOnly()
        timer = threading.Timer(0.1, lambda: setattr(event, "flag", True))
        timer.start()

        assert wait_for_event(event, 5.0) is True  # type: ignore[arg-type]
        timer.join()

    def test_non_positive_timeout_does_not_sleep(self, monkeypatch):
        sleeps: List[float] = []
        monkeypatch.setattr(waits.time, "sleep", sleeps.append)

        assert wait_for_event(threading.Event(), 0) is False
        assert wait_for_event(threading.Event(), -1.0) is False
        assert sleeps == []


class _FailingTransport(OBDTransport):
    """connect() always fails; only the reconnect skeleton is exercised."""

    def connect(self) -> bool:
        return False


class TestCallSites:
    def test_reconnect_indefinitely(self):
        transport = _FailingTransport()
        event = _NoWaitEvent()
        transport._shutdown = event
        timer = threading.Timer(0.2, event.set)
        timer.start()

        _run_bounded(lambda: transport.reconnect_indefinitely(retry_delay=0.05))
        timer.join()
        assert event.wait_calls == 0

    def test_watchdog_monitor_loop(self, monkeypatch):
        manager = ThreadManager()
        watchdog = WatchdogMonitor(manager, check_interval=0.05)
        event = _NoWaitEvent()
        watchdog._stop_event = event
        monkeypatch.setattr(watchdog, "_check_thread_health", event.set)

        _run_bounded(watchdog._monitor_loop)
        assert event.wait_calls == 0

    def test_obd_init_retry_wait(self, monkeypatch):
        transport = SimTransport()
        transport.connect()
        manager = ThreadManager()
        proto = OBDProtocol(transport, manager)
        event = _NoWaitEvent()
        proto.shutdown_event = event

        def _fail_once() -> bool:
            event.set()
            return False

        monkeypatch.setattr(proto, "_initialize_protocol", _fail_once)
        try:
            _run_bounded(proto._protocol_loop)
        finally:
            manager.shutdown()
        assert event.wait_calls == 0

    def test_obd_pre_initialised_settle(self):
        transport = SimTransport()
        transport.connect()
        manager = ThreadManager()
        proto = OBDProtocol(transport, manager, adapter_pre_initialised=True)
        event = _NoWaitEvent()
        event.set()
        proto.shutdown_event = event

        try:
            assert _run_bounded(proto._initialize_protocol) is False
        finally:
            manager.shutdown()
        assert event.wait_calls == 0

    def test_ensure_pairing_initialized(self):
        interface = BluetoothSetupInterface.__new__(BluetoothSetupInterface)
        interface.logger = logging.getLogger("test")
        event = _NoWaitEvent()
        event.set()
        interface._pairing_ready = event
        interface.pairing = object()  # type: ignore[assignment]

        assert interface.ensure_pairing_initialized() is True
        assert event.wait_calls == 0

    def test_splash_wait_for_completion_timed(self):
        splash = SplashScreen(duration=5.0)
        event = _NoWaitEvent()
        splash._completion_event = event

        assert _run_bounded(lambda: splash.wait_for_completion(timeout=0.2)) is False
        assert event.wait_calls == 0

    def test_splash_wait_for_completion_untimed(self):
        splash = SplashScreen(duration=5.0)
        splash.start()
        splash._completion_event.set()

        assert _run_bounded(splash.wait_for_completion) is True
