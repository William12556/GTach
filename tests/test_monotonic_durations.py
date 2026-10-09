# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""A wall-clock step does not distort durations or cache ages (issue-e215a184).

time.time is patched to jump by an hour, as an NTP correction after boot
does on the Pi; the figures under test must not move.
"""

import time

from gtach.display.performance.monitor import PerformanceMonitor
from gtach.utils.platform import PlatformDetector

STEP_S = 3600.0


def _step_wall_clock(monkeypatch, offset):
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + offset)


def test_platform_cache_survives_a_forward_step(monkeypatch):
    detector = PlatformDetector()
    calls = []
    real_run = detector._run_all_detections

    def spy():
        calls.append(1)
        return real_run()

    monkeypatch.setattr(detector, "_run_all_detections", spy)
    first = detector.get_platform_type()

    _step_wall_clock(monkeypatch, STEP_S)

    assert detector.get_platform_type() is first
    assert len(calls) == 1


def test_monitor_uptime_survives_a_backward_step(monkeypatch):
    monitor = PerformanceMonitor()
    assert monitor.start_monitoring() is True

    _step_wall_clock(monkeypatch, -STEP_S)

    uptime = monitor.get_performance_summary()["monitoring_duration"]
    monitor.stop_monitoring()

    assert 0 <= uptime < 5
