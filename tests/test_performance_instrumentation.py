#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""PerformanceMonitor frame bracketing, gating and psutil caching.

Automates test-0b00759c (change-0b00759c, change-c5dedd71; display
review §6.1, §6.2, §9.3). Case identifiers in each test docstring refer
to that plan.
"""

import ast
import logging
import time
import types
import typing
from pathlib import Path
from unittest import mock

import pytest

import gtach.display.manager as manager_module
import gtach.display.performance.monitor as monitor_module
from gtach.display.performance.interfaces import PerformanceMonitorInterface
from gtach.display.performance.monitor import PerformanceMonitor

MANAGER_SOURCE = Path(manager_module.__file__)


@pytest.fixture
def monitor():
    m = PerformanceMonitor(target_fps=60)
    m.start_monitoring()
    yield m
    m.stop_monitoring()


@pytest.fixture
def clock(monkeypatch):
    """Replace the monitor module's time source with a settable clock."""
    now = [1000.0]
    monkeypatch.setattr(
        monitor_module, "time", types.SimpleNamespace(time=lambda: now[0])
    )
    return now


def _process(*rss_values, error=None):
    """A psutil.Process double returning the given RSS values in bytes."""
    process = mock.Mock()
    if error is not None:
        process.memory_info.side_effect = error
    else:
        process.memory_info.side_effect = [
            types.SimpleNamespace(rss=v) for v in rss_values
        ]
    return process


def _display_loop_node():
    tree = ast.parse(MANAGER_SOURCE.read_text(encoding="utf-8"))
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_display_loop"
    )


def _calls(node, attr):
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == attr
    ]


class TestFrameBracketing:
    def test_bracketed_interval_reports_its_own_duration(self, monitor):
        """TC-001: about 5 ms, clearly below the 16.7 ms frame target."""
        frame_id = monitor.record_frame_start()
        time.sleep(0.005)
        frame_time = monitor.record_frame_end(frame_id)
        assert 0.003 < frame_time < 0.012

    def test_frame_end_precedes_pacing_sleep(self):
        """TC-002: record_frame_end is called before time.sleep(_sleep)."""
        loop = _display_loop_node()
        end_lines = [c.lineno for c in _calls(loop, "record_frame_end")]
        sleep_lines = [
            c.lineno
            for c in _calls(loop, "sleep")
            if isinstance(c.func.value, ast.Name)
            and c.func.value.id == "time"
            and c.args
            and isinstance(c.args[0], ast.Name)
            and c.args[0].id == "_sleep"
        ]
        assert len(end_lines) == 1 and len(sleep_lines) == 1
        assert end_lines[0] < sleep_lines[0]

    def test_frame_ids_are_consecutive_positive_integers(self, monitor):
        """TC-003: 1, 2, 3 after a reset; all truthy ints."""
        monitor.reset_metrics()
        ids = []
        for _ in range(3):
            frame_id = monitor.record_frame_start()
            monitor.record_frame_end(frame_id)
            ids.append(frame_id)
        assert ids == [1, 2, 3]
        assert all(isinstance(i, int) and i for i in ids)

    def test_disabled_monitoring_yields_zero_sentinel(self, caplog):
        """TC-004: start returns 0, end(0) returns 0.0, no warning."""
        m = PerformanceMonitor()
        caplog.set_level(logging.WARNING, logger="PerformanceMonitor")
        assert m.record_frame_start() == 0
        assert m.record_frame_end(0) == 0.0
        assert not [r for r in caplog.records if r.levelno >= logging.WARNING]

    def test_expiry_scan_skipped_in_steady_state(self, monitor, clock):
        """TC-005: 100 sequential frames drop nothing and leave none open."""
        for _ in range(100):
            frame_id = monitor.record_frame_start()
            clock[0] += 0.005
            monitor.record_frame_end(frame_id)
        assert monitor._dropped_frames == 0
        assert monitor._active_frames == {}

    def test_stale_frames_expire_when_several_are_open(self, monitor, clock):
        """TC-006: three frames older than 1 s are dropped by the fourth."""
        for _ in range(3):
            monitor.record_frame_start()
        clock[0] += 1.5
        fourth = monitor.record_frame_start()
        assert monitor._dropped_frames == 3
        assert list(monitor._active_frames) == [fourth]

    def test_genuine_overrun_counts_as_dropped(self, monitor, clock):
        """TC-014: an interval over 1.5 x the 1/60 s target is dropped."""
        frame_id = monitor.record_frame_start()
        clock[0] += (1.0 / 60.0) * 1.5 + 0.005
        monitor.record_frame_end(frame_id)
        assert monitor._dropped_frames == 1


class TestPeriodicGate:
    def test_fires_once_per_600_frames(self, monitor, clock):
        """TC-007: True exactly at frames 600 and 1200."""
        monitor.reset_metrics()
        fired = []
        for n in range(1, 1201):
            frame_id = monitor.record_frame_start()
            clock[0] += 0.001
            monitor.record_frame_end(frame_id)
            if monitor.should_log_periodic():
                fired.append(n)
        assert fired == [600, 1200]

    def test_false_at_frame_zero_and_when_disabled(self, monitor):
        """TC-008: no firing at frame 0 or with monitoring stopped."""
        monitor.reset_metrics()
        assert monitor.should_log_periodic() is False
        monitor._frame_count = 600
        monitor.stop_monitoring()
        assert monitor.should_log_periodic() is False

    def test_display_loop_gates_metrics_construction(self):
        """TC-009: every get_current_metrics call sits under the gate."""
        loop = _display_loop_node()
        guarded = set()
        for node in ast.walk(loop):
            if isinstance(node, ast.If) and _calls(node.test, "should_log_periodic"):
                for stmt in node.body:
                    guarded.update(id(c) for c in _calls(stmt, "get_current_metrics"))
        metrics_calls = _calls(loop, "get_current_metrics")
        assert metrics_calls
        assert all(id(c) in guarded for c in metrics_calls)
        assert "len(frame_id)" not in ast.unparse(loop)


class TestMemoryCache:
    def test_psutil_read_at_most_once_per_second(self, monitor, clock):
        """TC-010: 100 calls at one instant read psutil once."""
        monitor._process = _process(50 * 1024 * 1024)
        values = {monitor._get_current_memory_usage() for _ in range(100)}
        assert monitor._process.memory_info.call_count == 1
        assert values == {50.0}

    def test_cache_refreshes_after_interval(self, monitor, clock):
        """TC-011: after 1.1 s a fresh read replaces the cached value."""
        monitor._process = _process(50 * 1024 * 1024, 60 * 1024 * 1024)
        assert monitor._get_current_memory_usage() == 50.0
        clock[0] += 1.1
        assert monitor._get_current_memory_usage() == 60.0
        assert monitor._process.memory_info.call_count == 2

    def test_failed_read_does_not_poison_cache(self, monitor, clock):
        """TC-012: a raising read returns 0.0 and leaves the cache intact."""
        monitor._process = _process(50 * 1024 * 1024)
        monitor._get_current_memory_usage()
        clock[0] += 1.1
        monitor._process = _process(error=OSError("read failed"))
        assert monitor._get_current_memory_usage() == 0.0
        assert monitor._memory_cache_mb == 50.0

    def test_reset_clears_frame_counter_and_cache(self, monitor, clock):
        """TC-013: next frame ID is 1 and the next memory call reads psutil."""
        for _ in range(3):
            monitor.record_frame_end(monitor.record_frame_start())
        monitor._process = _process(50 * 1024 * 1024)
        monitor._get_current_memory_usage()

        monitor.reset_metrics()
        assert monitor.record_frame_start() == 1
        monitor._process = _process(70 * 1024 * 1024)
        assert monitor._get_current_memory_usage() == 70.0
        assert monitor._process.memory_info.call_count == 1


@pytest.mark.parametrize("cls", [PerformanceMonitor, PerformanceMonitorInterface])
def test_frame_id_annotations_are_int(cls):
    """TC-015: interface and implementation agree on int frame IDs."""
    start = typing.get_type_hints(cls.record_frame_start)
    end = typing.get_type_hints(cls.record_frame_end)
    assert start["return"] is int
    assert end["frame_id"] is int
