#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Watchdog liveness on the monotonic clock.

Covers change-b9ee7428. The Pi has no RTC, so NTP steps the wall clock
after boot. With heartbeats and health checks on time.time(), every
heartbeat then appeared hundreds of thousands of seconds old and the
watchdog shut the application down. Heartbeats, health checks and the
shutdown budget now use time.monotonic(); a wall-clock step in either
direction must not change any watchdog decision.
"""

import threading
import time

import pytest

import gtach.core.watchdog as watchdog_module
from gtach.core.thread import ThreadManager
from gtach.core.watchdog import ThreadHealth, WatchdogMonitor

# A step of roughly four and a half days, comparable to the one observed
# on device when NTP corrected a clock that started at the last-saved
# time.
CLOCK_STEP = 400000.0


def _register(manager: ThreadManager, name: str) -> None:
    """Register a never-started thread and give it a fresh heartbeat."""
    thread = threading.Thread(target=lambda: None, name=name, daemon=True)
    manager.register_thread(name, thread)
    manager.update_heartbeat(name)


def _watchdog(manager: ThreadManager, shutdowns: list, **timeouts) -> WatchdogMonitor:
    return WatchdogMonitor(
        manager,
        shutdown_callback=lambda: shutdowns.append('shutdown'),
        **timeouts,
    )


def _short_timeouts():
    return {'critical_timeout': 1.0, 'recovery_timeout': 0.5,
            'warning_timeout': 0.25}


def _step_wall_clock(monkeypatch, offset: float) -> None:
    real_time = time.time
    monkeypatch.setattr(time, 'time', lambda: real_time() + offset)


class TestWallClockSteps:
    """A wall-clock step in either direction changes no decision."""

    def test_forward_step_does_not_shut_down(self, monkeypatch, caplog):
        manager = ThreadManager()
        shutdowns = []
        watchdog = _watchdog(manager, shutdowns, **_short_timeouts())
        _register(manager, 'display')

        _step_wall_clock(monkeypatch, CLOCK_STEP)
        with caplog.at_level('WARNING', logger='WatchdogMonitor'):
            watchdog._check_thread_health()

        assert shutdowns == []
        assert not any('display' in r.getMessage() for r in caplog.records)

    def test_backward_step_does_not_mask_a_genuine_stall(self, monkeypatch):
        manager = ThreadManager()
        shutdowns = []
        timeouts = _short_timeouts()
        watchdog = _watchdog(manager, shutdowns, **timeouts)
        _register(manager, 'display')

        _step_wall_clock(monkeypatch, -CLOCK_STEP)
        with manager._lock:
            manager.threads['display'].last_heartbeat = (
                time.monotonic() - (timeouts['critical_timeout'] + 5)
            )
        watchdog._check_thread_health()

        assert shutdowns == ['shutdown']

    def test_advisory_thread_with_forward_step_is_not_warned(self, monkeypatch, caplog):
        manager = ThreadManager()
        shutdowns = []
        watchdog = _watchdog(manager, shutdowns, **_short_timeouts())
        _register(manager, 'transport')

        _step_wall_clock(monkeypatch, CLOCK_STEP)
        with caplog.at_level('WARNING', logger='WatchdogMonitor'):
            watchdog._check_thread_health()

        assert not any('transport' in r.getMessage() for r in caplog.records)
        assert watchdog.get_recovery_stats().warnings_issued == 0
        assert shutdowns == []


class TestStallDetectionPreserved:
    """Genuine stalls are still detected on the monotonic clock."""

    def test_critical_stall_shuts_down(self):
        manager = ThreadManager()
        shutdowns = []
        timeouts = _short_timeouts()
        watchdog = _watchdog(manager, shutdowns, **timeouts)
        _register(manager, 'display')

        with manager._lock:
            manager.threads['display'].last_heartbeat = (
                time.monotonic() - (timeouts['critical_timeout'] + 5)
            )
        watchdog._check_thread_health()

        assert shutdowns == ['shutdown']


class TestNeverDefaults:
    """'Never' is independent of where the monotonic clock starts."""

    def test_thread_health_defaults_are_minus_infinity(self):
        health = ThreadHealth(name='x')

        assert health.last_warning_time == float('-inf')
        assert health.last_recovery_time == float('-inf')

    def test_first_warning_not_suppressed_shortly_after_boot(self, monkeypatch, caplog):
        """monotonic() near zero must not look like a recent warning."""
        manager = ThreadManager()
        shutdowns = []
        watchdog = _watchdog(manager, shutdowns)
        _register(manager, 'display')

        now = 5.0
        elapsed = (watchdog.warning_timeout + watchdog.recovery_timeout) / 2
        with manager._lock:
            manager.threads['display'].last_heartbeat = now - elapsed

        monkeypatch.setattr(watchdog_module.time, 'monotonic', lambda: now)
        with caplog.at_level('WARNING', logger='WatchdogMonitor'):
            watchdog._check_thread_health()

        assert any('display' in r.getMessage() for r in caplog.records)
        assert shutdowns == []
