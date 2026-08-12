#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Watchdog-driven process termination and the advisory monitoring tier.

Covers change-2ac1c602: a critical-thread timeout must end the process
via the main thread's teardown path, and a thread named in
WatchdogMonitor.advisory_threads must never be able to reach recovery
or shutdown however stale its heartbeat becomes.
"""

import threading
import time

import pytest

from gtach.app import GTachApplication
from gtach.core.thread import ThreadManager
from gtach.core.watchdog import WatchdogMonitor

# Bound on every blocking assertion here. A regression in the exit path
# shows up as a loop that never returns, so an unbounded wait would turn
# a failure into a hung run with no diagnostic.
EXIT_TIMEOUT = 1.0


@pytest.fixture
def app(tmp_path, monkeypatch):
    """A constructed GTachApplication with nothing started.

    Runs in a temporary working directory because DeviceStore creates
    config/devices.yaml relative to the cwd. atexit registration is
    suppressed so a test instance does not outlive the run, and
    _force_exit is replaced so that a backstop timer which somehow
    fires cannot call os._exit inside the test process.

    TerminalRestorer is stubbed: it calls sys.stdin.fileno(), which
    pytest's capture replaces with a pseudofile that raises. Nothing
    under test touches the terminal.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('gtach.app.atexit.register', lambda *a, **k: None)
    monkeypatch.setattr('gtach.app.TerminalRestorer', lambda *a, **k: object())

    instance = GTachApplication(config_path=None, debug=False)

    forced = threading.Event()
    monkeypatch.setattr(instance, '_force_exit', forced.set)
    instance._forced_exit_event = forced
    return instance


class TestWatchdogShutdownCallback:
    """GTachApplication._watchdog_shutdown — signalling without teardown."""

    def test_sets_stop_event_and_does_not_shut_down(self, app, monkeypatch):
        """It signals the main loop; teardown is run()'s responsibility."""
        calls = []
        monkeypatch.setattr(app, 'shutdown', lambda: calls.append('shutdown'))

        app._watchdog_shutdown()

        assert app._stop_event.is_set() is True
        assert calls == []

    def test_second_invocation_is_harmless(self, app, monkeypatch):
        """WatchdogMonitor guards against this, but it must not matter."""
        monkeypatch.setattr(app, 'shutdown', lambda: pytest.fail('shutdown called'))

        app._watchdog_shutdown()
        app._watchdog_shutdown()

        assert app._stop_event.is_set() is True

    def test_backstop_timer_is_a_daemon(self, app):
        """A pending backstop must not hold the interpreter open."""
        before = {t for t in threading.enumerate()}
        app._watchdog_shutdown()
        new = [t for t in threading.enumerate() if t not in before]

        assert new, 'no backstop timer thread was started'
        assert all(t.daemon for t in new)

    def test_backstop_delay_is_twenty_seconds(self):
        assert GTachApplication._EXIT_BACKSTOP_SEC == 20.0


class TestRunLoopExit:
    """The main loop must leave promptly and tear down exactly once."""

    def test_run_returns_and_shuts_down_once(self, app, monkeypatch):
        """run() exits within EXIT_TIMEOUT of the callback returning."""
        shutdowns = []
        monkeypatch.setattr(app, 'start', lambda: None)
        monkeypatch.setattr(app, 'shutdown', lambda: shutdowns.append(time.time()))

        entered = threading.Event()
        returned = threading.Event()

        def _run():
            entered.set()
            app.run()
            returned.set()

        runner = threading.Thread(target=_run, name='run-under-test', daemon=True)
        runner.start()
        assert entered.wait(EXIT_TIMEOUT), 'run() never started'

        # Let the loop reach its wait before signalling, so this
        # exercises the wake-up rather than the pre-loop test.
        time.sleep(0.05)
        app._watchdog_shutdown()

        assert returned.wait(EXIT_TIMEOUT), 'run() did not exit promptly'
        runner.join(timeout=EXIT_TIMEOUT)
        assert len(shutdowns) == 1

    def test_watchdog_shutdown_before_loop_entry(self, app, monkeypatch):
        """_stop_event exists before the watchdog is constructed.

        The event is therefore settable before run() has been entered,
        and the loop must exit on its first test.
        """
        monkeypatch.setattr(app, 'start', lambda: None)
        monkeypatch.setattr(app, 'shutdown', lambda: None)

        app._watchdog_shutdown()

        returned = threading.Event()
        runner = threading.Thread(
            target=lambda: (app.run(), returned.set()), daemon=True
        )
        runner.start()

        assert returned.wait(EXIT_TIMEOUT), 'run() did not exit immediately'


class TestShutdownIdempotence:
    """shutdown() runs at most once per process lifetime."""

    def test_second_call_is_a_no_op(self, app):
        stops = []

        class _Recorder:
            def stop(self):
                stops.append('stop')

            def shutdown(self):
                stops.append('shutdown')

        app._watchdog = _Recorder()
        app._thread_manager = _Recorder()

        app.shutdown()
        first = list(stops)
        app.shutdown()

        assert stops == first
        assert stops.count('stop') == 1
        assert stops.count('shutdown') == 1


def _aged_thread(manager: ThreadManager, name: str, age: float) -> None:
    """Register a never-started thread whose heartbeat is `age` old."""
    thread = threading.Thread(target=lambda: None, name=name, daemon=True)
    manager.register_thread(name, thread)
    with manager._lock:
        manager.threads[name].last_heartbeat = time.time() - age


class TestAdvisoryTier:
    """critical_threads == {'display'}; advisory_threads == {'transport'}."""

    def test_membership(self):
        watchdog = WatchdogMonitor(ThreadManager())
        assert watchdog.critical_threads == {'display'}
        assert watchdog.advisory_threads == {'transport'}

    def test_advisory_timeout_warns_but_never_recovers(self, caplog):
        """A stale advisory thread produces a warning and nothing more."""
        manager = ThreadManager()
        shutdowns = []
        watchdog = WatchdogMonitor(
            manager, critical_timeout=1.0, recovery_timeout=0.5,
            warning_timeout=0.25,
            shutdown_callback=lambda: shutdowns.append('shutdown')
        )
        _aged_thread(manager, 'transport', age=600.0)

        with caplog.at_level('WARNING', logger='WatchdogMonitor'):
            watchdog._check_thread_health()

        assert any('transport' in r.message for r in caplog.records)

        stats = watchdog.get_recovery_stats()
        assert stats.warnings_issued == 1
        assert stats.shutdown_triggers == 0
        assert stats.hard_recovery_attempts == 0
        assert stats.soft_recovery_attempts == 0
        assert shutdowns == []
        assert watchdog._shutdown_initiated.is_set() is False

    def test_critical_timeout_still_shuts_down(self):
        """The display thread retains its critical escalation."""
        manager = ThreadManager()
        shutdowns = []
        watchdog = WatchdogMonitor(
            manager, critical_timeout=1.0, recovery_timeout=0.5,
            warning_timeout=0.25,
            shutdown_callback=lambda: shutdowns.append('shutdown')
        )
        _aged_thread(manager, 'display', age=600.0)

        watchdog._check_thread_health()

        assert shutdowns == ['shutdown']
        assert watchdog.get_recovery_stats().shutdown_triggers == 1
