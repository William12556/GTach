#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Watchdog lock discipline: no blocking call under thread_manager._lock.

Automates test-5a9dc15e (change-5a9dc15e; core review §3.3, §4.1).
Case identifiers in each test docstring refer to that plan.
"""

import ast
import logging
import threading
import time
import types
from pathlib import Path

import pytest

import gtach.core.watchdog as watchdog_module
from gtach.core.thread import ThreadManager, ThreadStatus
from gtach.core.watchdog import RecoveryLevel, ThreadHealth, WatchdogMonitor

WATCHDOG_SOURCE = Path(watchdog_module.__file__)

# Default bands: warning > 15 s, recovery > 30 s, critical > 45 s.
AGE = {"critical": 50.0, "recovery": 35.0, "warning": 20.0, "healthy": 1.0}


def _register(manager: ThreadManager, name: str) -> None:
    """Register a never-started thread (ident None) with a fresh heartbeat."""
    thread = threading.Thread(target=lambda: None, name=name, daemon=True)
    manager.register_thread(name, thread)
    manager.update_heartbeat(name)


def _set_age(manager: ThreadManager, name: str, age: float) -> None:
    with manager._lock:
        manager.threads[name].last_heartbeat = time.monotonic() - age


@pytest.fixture
def manager():
    return ThreadManager()


@pytest.fixture
def watchdog(manager):
    return WatchdogMonitor(manager, shutdown_callback=lambda: None)


class TestSoftRecovery:
    def test_heartbeat_advancing_during_window_succeeds(self, manager, watchdog):
        """TC-001: a heartbeat written inside the window is observed."""
        _register(manager, "obd_protocol")
        health = ThreadHealth(name="obd_protocol", consecutive_failures=1)

        def _beat():
            time.sleep(0.2)
            manager.update_heartbeat("obd_protocol")

        helper = threading.Thread(target=_beat)
        helper.start()
        watchdog._attempt_soft_recovery("obd_protocol", health, 5.0)
        helper.join()

        assert watchdog.get_recovery_stats().soft_recovery_successes == 1
        assert health.consecutive_failures == 0

    def test_static_heartbeat_is_not_a_success(self, manager, watchdog):
        """TC-002: attempt counted, no success, level left at SOFT_RECOVERY."""
        _register(manager, "obd_protocol")
        health = ThreadHealth(name="obd_protocol")

        watchdog._attempt_soft_recovery("obd_protocol", health, 5.0)

        stats = watchdog.get_recovery_stats()
        assert stats.soft_recovery_attempts == 1
        assert stats.soft_recovery_successes == 0
        assert health.current_level is RecoveryLevel.SOFT_RECOVERY

    def test_thread_unregistered_during_window(self, manager, watchdog):
        """TC-003: removal mid-window raises nothing and is not a success."""
        _register(manager, "obd_protocol")
        health = ThreadHealth(name="obd_protocol")

        def _remove():
            time.sleep(0.2)
            with manager._lock:
                del manager.threads["obd_protocol"]

        helper = threading.Thread(target=_remove)
        helper.start()
        watchdog._attempt_soft_recovery("obd_protocol", health, 5.0)
        helper.join()

        assert watchdog.get_recovery_stats().soft_recovery_successes == 0

    def test_thread_absent_before_observation(self, watchdog, caplog):
        """TC-004: early return without the sleep, with one DEBUG record."""
        caplog.set_level(logging.DEBUG, logger="WatchdogMonitor")
        health = ThreadHealth(name="missing")

        start = time.monotonic()
        watchdog._attempt_soft_recovery("missing", health, 5.0)
        elapsed = time.monotonic() - start

        assert elapsed < 0.5
        notes = [
            r
            for r in caplog.records
            if r.levelno == logging.DEBUG
            and "no longer registered" in r.getMessage()
        ]
        assert len(notes) == 1

    def test_competing_lock_acquisition_is_not_blocked(self, manager, watchdog):
        """TC-005: the state lock stays available throughout the window."""
        _register(manager, "obd_protocol")
        health = ThreadHealth(name="obd_protocol")
        latencies = []
        done = threading.Event()

        def _probe():
            while not done.is_set():
                start = time.monotonic()
                with manager._lock:
                    latencies.append(time.monotonic() - start)
                time.sleep(0.01)

        prober = threading.Thread(target=_probe)
        prober.start()
        try:
            watchdog._attempt_soft_recovery("obd_protocol", health, 5.0)
        finally:
            done.set()
            prober.join()

        assert latencies
        assert max(latencies) < 0.05


def _record_handlers(watchdog, calls, check=None):
    """Replace the four dispatch targets with recorders."""

    def _make(kind):
        def _handler(*args):
            name = args[0].name if kind == "reset" else args[0]
            if check is not None:
                check()
            calls.append((kind, name))

        return _handler

    watchdog._handle_critical_timeout = _make("critical")
    watchdog._handle_recovery_timeout = _make("recovery")
    watchdog._handle_warning_timeout = _make("warning")
    watchdog._reset_thread_health = _make("reset")


class TestHealthCheckDispatch:
    def test_dispatch_per_severity_band(self, manager, watchdog):
        """TC-006: each band reaches its own handler exactly once."""
        names = {"critical": "t_crit", "recovery": "t_rec", "warning": "t_warn"}
        names["healthy"] = "t_ok"
        for band, name in names.items():
            _register(manager, name)
            _set_age(manager, name, AGE[band])
        calls = []
        _record_handlers(watchdog, calls)

        watchdog._check_thread_health()

        assert sorted(calls) == sorted(
            [
                ("critical", "t_crit"),
                ("recovery", "t_rec"),
                ("warning", "t_warn"),
                ("reset", "t_ok"),
            ]
        )

    def test_lock_released_before_handlers_run(self, manager, watchdog):
        """TC-007: a second thread can take the lock inside every handler."""
        for name, band in (("a", "critical"), ("b", "recovery"), ("c", "warning")):
            _register(manager, name)
            _set_age(manager, name, AGE[band])
        acquirable = []

        def _check():
            result = []

            def _try():
                got = manager._lock.acquire(blocking=False)
                if got:
                    manager._lock.release()
                result.append(got)

            probe = threading.Thread(target=_try)
            probe.start()
            probe.join()
            acquirable.append(result[0])

        calls = []
        _record_handlers(watchdog, calls, check=_check)

        watchdog._check_thread_health()

        assert len(calls) == 3
        assert acquirable == [True, True, True]

    def test_non_running_threads_are_skipped(self, manager, watchdog):
        """TC-008: a STOPPED thread gains no health record and no call."""
        _register(manager, "stopped")
        _register(manager, "running")
        with manager._lock:
            manager.threads["stopped"].status = ThreadStatus.STOPPED
            manager.threads["running"].status = ThreadStatus.RUNNING
        calls = []
        _record_handlers(watchdog, calls)

        watchdog._check_thread_health()

        assert set(watchdog.thread_health) == {"running"}
        assert all(name != "stopped" for _, name in calls)

    def test_empty_threads_dictionary(self, watchdog):
        """TC-009: no threads, no calls, no exception."""
        calls = []
        _record_handlers(watchdog, calls)

        watchdog._check_thread_health()

        assert calls == []

    def test_dispatch_order_follows_traversal_order(self, manager, watchdog):
        """TC-010: pending actions are neither sorted nor deduplicated."""
        for name in ("display", "obd_protocol", "transport"):
            _register(manager, name)
            _set_age(manager, name, AGE["warning"])
        calls = []
        _record_handlers(watchdog, calls)

        watchdog._check_thread_health()

        assert [name for _, name in calls] == ["display", "obd_protocol", "transport"]


def _is_thread_manager_lock(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "_lock"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "thread_manager"
    )


def _is_time_sleep(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "sleep"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "time"
    )


def test_no_sleep_under_thread_manager_lock():
    """TC-011: static check of every `with self.thread_manager._lock` block."""
    tree = ast.parse(WATCHDOG_SOURCE.read_text(encoding="utf-8"))
    locked_blocks = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.With)
        and any(_is_thread_manager_lock(item.context_expr) for item in node.items)
    ]
    assert locked_blocks, "expected at least one thread_manager._lock block"
    offending = [
        call.lineno
        for block in locked_blocks
        for stmt in block.body
        for call in ast.walk(stmt)
        if _is_time_sleep(call)
    ]
    assert offending == []


def test_recovery_statistics_for_fixed_sequence(monkeypatch, manager):
    """TC-012: ten scripted cycles give fixed counts.

    The plan's pre-change baseline was never recorded and hard recovery has
    since been removed (issue-860fd5f7), so the expected values are derived
    from the current counting rules:

    - warnings: once per thread at 20 s; 25 s and 30 s are inside the
      30 s throttle;
    - soft recovery: once per thread at 35 s; no success, heartbeats are
      static;
    - shutdown: once, for the critical 'display' thread at 50 s; the
      non-critical 'worker' at 50 s is logged only.
    """
    clock = [0.0]
    fake_time = types.SimpleNamespace(
        monotonic=lambda: clock[0],
        sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )
    monkeypatch.setattr(watchdog_module, "time", fake_time)
    for name in ("display", "worker"):
        thread = threading.Thread(target=lambda: None, name=name, daemon=True)
        manager.register_thread(name, thread)
        with manager._lock:
            manager.threads[name].last_heartbeat = 0.0
    shutdowns = []
    watchdog = WatchdogMonitor(manager, shutdown_callback=lambda: shutdowns.append(1))

    for cycle in range(1, 11):
        clock[0] = cycle * 5.0
        watchdog._check_thread_health()

    stats = watchdog.get_recovery_stats()
    assert stats.warnings_issued == 2
    assert stats.soft_recovery_attempts == 2
    assert stats.soft_recovery_successes == 0
    assert stats.shutdown_triggers == 1
    assert shutdowns == [1]
