#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Gauge display and touch corrections (change-2550e4ee).

Covers EDITS A to E: display attributes assigned before fallible
initialisation, single reads of the setup manager, long press decided by
movement and duration, bounded touch-start age, one link evaluation per
frame, the cause-line font, the redline warning, the palette save
warning, Clear settings over every stored device, the rpm_bands default,
the splash text-fit checks and the corrected lock test.
"""

import logging
import types

import pygame
import pytest

import gtach.comm.device_store as device_store_module
import gtach.display.manager as manager_module
import gtach.display.splash as splash_module
import gtach.display.touch_interface as touch_interface_module
import gtach.utils.config as config_module
from gtach.core import ThreadManager
from gtach.display.input.interfaces import TouchAction
from gtach.display.input.touch_coordinator import TouchEventCoordinator
from gtach.display.manager import DisplayManager
from gtach.display.models import (
    DAY_PALETTE,
    NIGHT_PALETTE,
    DisplayConfig,
    DisplayMode,
    RPMBands,
)
from gtach.display.splash import SplashScreen
from gtach.display.touch import TouchHandler
from gtach.display.typography import TypographyConstants, get_font_manager

LONG_PRESS = 1.0


def _raise_runtime_error(*args, **kwargs):
    raise RuntimeError("injected fault")


class _StubTouchInterface:
    """Accepts the callback registration and nothing else."""

    def register_callback(self, callback):
        pass

    def stop(self):
        pass


@pytest.fixture
def manager(monkeypatch):
    """A real DisplayManager whose touch interface fails to initialise."""
    monkeypatch.setattr(
        touch_interface_module, "create_touch_interface", _raise_runtime_error
    )
    dm = DisplayManager(ThreadManager())
    dm.config.touch_long_press = LONG_PRESS
    return dm


def _run_one_frame(dm):
    """Run exactly one iteration of the display loop."""
    dm.thread_manager.update_heartbeat = lambda name: dm._shutdown_event.set()
    dm._display_loop()


def _loop_errors(caplog):
    return [
        r
        for r in caplog.records
        if r.levelno >= logging.ERROR and "Display loop error" in r.getMessage()
    ]


# ---------------------------------------------------------------- EDIT A


class TestInitialisationFaults:
    """C04: a touch or monitor fault degrades to an inactive component."""

    def test_constructs_and_renders_without_touch_or_monitor(self, monkeypatch, caplog):
        monkeypatch.setattr(
            touch_interface_module, "create_touch_interface", _raise_runtime_error
        )
        monkeypatch.setattr(manager_module, "PerformanceMonitor", _raise_runtime_error)

        dm = DisplayManager(ThreadManager())

        assert dm.touch_handler is None
        assert dm.performance_monitor is None
        assert dm._setup_manager is None
        assert dm._in_setup_mode is False
        assert dm._setup_entry_callback is None
        assert dm._splash_screen is not None

        caplog.clear()
        with caplog.at_level(logging.ERROR):
            _run_one_frame(dm)
            dm._shutdown_event.clear()
            dm.config.mode = DisplayMode.RADIAL
            _run_one_frame(dm)
        assert _loop_errors(caplog) == []

    def test_status_report_tolerates_missing_monitor(self, manager):
        manager.performance_monitor = None

        stats = manager.get_performance_stats()
        state = manager.get_display_state()

        assert "rendering_stats" in stats
        assert "performance_metrics" not in stats
        assert state["components_initialized"]["performance_monitor"] is False


class _SetupStub:
    def __init__(self):
        self.render_calls = 0
        self.touch_calls = 0
        self.state = types.SimpleNamespace(current_screen=None)

    def render(self, surface):
        self.render_calls += 1

    def handle_touch_event(self, pos):
        self.touch_calls += 1
        return None


def _make_vanishing_setup_manager(dm, stub):
    """Make _setup_manager read as stub once, then None (C05)."""
    reads = {"n": 0}

    class _Vanishing(type(dm)):
        @property
        def _setup_manager(self):
            reads["n"] += 1
            return stub if reads["n"] == 1 else None

        @_setup_manager.setter
        def _setup_manager(self, value):
            pass

    dm.__class__ = _Vanishing
    return reads


class TestSetupManagerReadOnce:
    """C05: test-and-use of _setup_manager reads the attribute once."""

    def test_handle_touch_event(self, manager, caplog):
        stub = _SetupStub()
        manager._in_setup_mode = True
        _make_vanishing_setup_manager(manager, stub)

        with caplog.at_level(logging.ERROR):
            manager.handle_touch_event((10, 10))

        assert stub.touch_calls == 1
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]

    def test_render_path(self, manager, caplog):
        stub = _SetupStub()
        manager.config.mode = DisplayMode.RADIAL
        manager._in_setup_mode = True
        _make_vanishing_setup_manager(manager, stub)

        with caplog.at_level(logging.ERROR):
            _run_one_frame(manager)

        assert stub.render_calls == 1
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


# ---------------------------------------------------------------- EDIT B


def _touch_handler(dm):
    return TouchHandler(dm, touch_interface=_StubTouchInterface())


def _gesture(handler, start, end, duration, t0=100.0):
    handler._process_touch(0, start[0], start[1], True, t0)
    handler._process_touch(0, end[0], end[1], False, t0 + duration)


@pytest.fixture
def gauge(manager, monkeypatch):
    """Connected RADIAL gauge with recording swipe and long-press handlers."""
    manager.config.mode = DisplayMode.RADIAL
    manager._palette = DAY_PALETTE
    calls = []
    for name in (
        "_handle_swipe_up",
        "_handle_swipe_down",
        "_handle_swipe_left",
        "_handle_swipe_right",
    ):
        original = getattr(manager, name)

        def recorder(start, end, _name=name, _original=original):
            calls.append(_name)
            return _original(start, end)

        monkeypatch.setattr(manager, name, recorder)
    manager.calls = calls
    return manager


class TestLongPressRequiresRest:
    """C06 (decision D6): movement decides swipe; a held button presses."""

    def test_slow_swipe_is_a_swipe(self, gauge):
        handler = _touch_handler(gauge)

        _gesture(handler, (240, 240), (240, 100), 1.5)

        assert gauge.calls == ["_handle_swipe_up"]
        assert gauge._palette is DAY_PALETTE

    def test_hold_at_rest_on_gauge_is_a_long_press(self, gauge):
        handler = _touch_handler(gauge)

        _gesture(handler, (240, 240), (240, 240), 1.5)

        assert gauge.calls == []
        assert gauge._palette is NIGHT_PALETTE

    def test_hold_on_button_presses_it_once(self, gauge):
        pressed = []
        gauge.touch_coordinator.register_button_region(
            "held",
            pygame.Rect(200, 200, 80, 80),
            TouchAction.BUTTON_PRESS,
            lambda pos: pressed.append(pos),
        )
        handler = _touch_handler(gauge)

        _gesture(handler, (240, 240), (242, 241), 1.5)

        assert pressed == [(240, 240)]
        assert gauge._palette is DAY_PALETTE

    def test_release_exactly_at_threshold_is_a_swipe(self, gauge):
        threshold = gauge.touch_coordinator.swipe_threshold
        handler = _touch_handler(gauge)

        _gesture(handler, (240, 240), (240, 240 - threshold), 1.5)

        assert gauge.calls == ["_handle_swipe_up"]
        assert gauge._palette is DAY_PALETTE

    def test_duration_exactly_long_press_at_rest_is_a_long_press(self, gauge):
        handler = _touch_handler(gauge)

        _gesture(handler, (240, 240), (240, 240), LONG_PRESS, t0=0.0)

        assert gauge._palette is NIGHT_PALETTE

    def test_setup_mode_routes_long_hold_to_short_press(self, gauge):
        stub = _SetupStub()
        gauge._in_setup_mode = True
        gauge._setup_manager = stub
        handler = _touch_handler(gauge)

        _gesture(handler, (240, 240), (240, 240), 1.5)

        assert stub.touch_calls == 1
        assert gauge._palette is DAY_PALETTE


class _RecordingManager:
    """Records the DisplayManager calls the touch path can make."""

    def __init__(self):
        self.config = types.SimpleNamespace(
            mode=DisplayMode.RADIAL, touch_long_press=LONG_PRESS
        )
        self.touch_coordinator = TouchEventCoordinator()
        self.calls = []

    def is_in_setup_mode(self):
        return False

    def handle_touch_event(self, pos):
        self.calls.append(("tap", pos))

    def _handle_long_press(self, start, end):
        self.calls.append(("long_press", start))

    def __getattr__(self, name):
        if name.startswith("_handle_swipe_"):
            return lambda start, end: self.calls.append(("swipe", name))
        raise AttributeError(name)


class TestStaleTouchStart:
    """C07: a touch start older than _TOUCH_START_MAX_AGE_S is not used."""

    def test_constant(self):
        assert TouchHandler._TOUCH_START_MAX_AGE_S == 10.0

    def test_down_replaces_stale_start(self):
        dm = _RecordingManager()
        handler = _touch_handler(dm)

        handler._process_touch(0, 50, 50, True, 0.0)
        handler._process_touch(0, 300, 300, True, 20.0)
        handler._process_touch(0, 300, 300, False, 20.2)

        assert dm.calls == [("tap", (300, 300))]

    def test_release_of_stale_start_does_nothing(self):
        dm = _RecordingManager()
        handler = _touch_handler(dm)

        handler._process_touch(0, 50, 50, True, 0.0)
        handler._process_touch(0, 50, 50, False, 12.0)

        assert dm.calls == []
        assert handler._touch_start is None

    def test_recent_start_is_kept(self):
        dm = _RecordingManager()
        handler = _touch_handler(dm)

        handler._process_touch(0, 50, 50, True, 0.0)
        handler._process_touch(0, 55, 55, True, 0.5)

        assert handler._touch_start == (0.0, 50, 50)


# ---------------------------------------------------------------- EDIT C


class TestOneLinkEvaluationPerFrame:
    """O2: the link callback is asked once per frame."""

    @pytest.mark.parametrize("connected", [True, False])
    def test_one_call_per_frame(self, manager, connected):
        manager.config.mode = DisplayMode.RADIAL
        calls = []

        def link():
            calls.append(1)
            return connected

        manager._link_connected_callback = link

        _run_one_frame(manager)

        assert len(calls) == 1


class TestCauseLineFont:
    def test_cause_line_uses_small_text_font(self, manager, monkeypatch):
        sizes = {}
        real = get_font_manager()

        def get_font(size):
            font = real.get_font(size)
            sizes[id(font)] = size
            return font

        monkeypatch.setattr(
            manager_module,
            "get_font_manager",
            lambda: types.SimpleNamespace(get_font=get_font),
        )
        drawn = {}
        render_text = manager.rendering_engine.render_text

        def recording_render_text(target, text, font, *args, **kwargs):
            drawn[text] = sizes.get(id(font))
            return render_text(target, text, font, *args, **kwargs)

        monkeypatch.setattr(
            manager.rendering_engine, "render_text", recording_render_text
        )
        manager._link_cause_callback = lambda: "no bluetooth controller"

        manager._render_disconnected()

        assert drawn["no bluetooth controller"] == TypographyConstants.FONT_SMALL_TEXT


class TestRedlineAboveFullScale:
    """C09: a redline above the cap is reported once, at load."""

    def test_warning_at_load(self, monkeypatch, caplog):
        bands = RPMBands(
            idle_max=999,
            torque_start=3000,
            caution_start=6000,
            warning_start=9000,
            danger_start=11000,
            redline_rpm=12000,
        )
        monkeypatch.setattr(config_module, "load_engine_profile", lambda name: bands)
        monkeypatch.setattr(
            touch_interface_module, "create_touch_interface", _raise_runtime_error
        )

        with caplog.at_level(logging.WARNING):
            dm = DisplayManager(ThreadManager())
            dm._gauge_max_rpm()

        assert dm._gauge_max_rpm() == 9000
        warnings = [
            r
            for r in caplog.records
            if r.levelno == logging.WARNING and "off the dial" in r.getMessage()
        ]
        assert len(warnings) == 1


class TestPaletteSaveFailure:
    """C03: the palette switches for the session; one WARNING."""

    def test_failed_save(self, manager, monkeypatch, caplog):
        manager._palette = DAY_PALETTE
        monkeypatch.setattr(manager._config_store, "save", _raise_runtime_error)

        with caplog.at_level(logging.WARNING):
            manager._toggle_palette()

        assert manager._palette is NIGHT_PALETTE
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1

    def test_successful_save_returns_true(self, manager):
        assert manager._save_config() is True


class _FakeStore:
    def __init__(self, macs, failing=()):
        self.devices = [types.SimpleNamespace(mac_address=m) for m in macs]
        self.failing = set(failing)
        self.removed = []

    def get_all_devices(self):
        return list(self.devices)

    def remove_device(self, mac):
        self.removed.append(mac)
        return mac not in self.failing


class TestClearSettings:
    """A09: every stored device is removed and the results checked."""

    def _clear(self, manager, monkeypatch, store):
        monkeypatch.setattr(device_store_module, "get_device_store", lambda: store)
        entered = []
        manager._setup_entry_callback = lambda: entered.append(True)
        manager._on_clear_settings()
        return entered

    def test_removes_primary_and_secondary(self, manager, monkeypatch):
        store = _FakeStore(["AA:AA", "BB:BB"])

        entered = self._clear(manager, monkeypatch, store)

        assert store.removed == ["AA:AA", "BB:BB"]
        assert entered == [True]

    def test_failed_removal_is_logged(self, manager, monkeypatch, caplog):
        store = _FakeStore(["AA:AA", "BB:BB"], failing=["BB:BB"])

        with caplog.at_level(logging.ERROR):
            entered = self._clear(manager, monkeypatch, store)

        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert "BB:BB" in errors[0].getMessage()
        assert entered == [True]


# ---------------------------------------------------------------- EDIT D


class TestRpmBandsDefault:
    def test_each_instance_has_its_own_bands(self):
        first = DisplayConfig(mode=DisplayMode.RADIAL)
        second = DisplayConfig(mode=DisplayMode.RADIAL)

        assert isinstance(first.rpm_bands, RPMBands)
        assert first.rpm_bands is not second.rpm_bands

    def test_explicit_bands_kept(self):
        bands = RPMBands(redline_rpm=7000)

        assert DisplayConfig(mode=DisplayMode.RADIAL, rpm_bands=bands).rpm_bands is (
            bands
        )


class TestSplashFitChecks:
    """O5: each text-fit check runs once, with the size drawn."""

    def test_checks_once_with_drawn_size(self, monkeypatch):
        real = get_font_manager()
        checks = []
        drawn_sizes = set()

        def get_font(size):
            drawn_sizes.add(size)
            return real.get_font(size)

        def validate(text, size, center=None):
            checks.append((text, size))
            return True

        monkeypatch.setattr(
            splash_module,
            "get_font_manager",
            lambda: types.SimpleNamespace(
                get_font=get_font, validate_text_fits_circular_display=validate
            ),
        )
        splash = SplashScreen(surface_size=(480, 480), duration=4.0)
        surface = pygame.Surface((480, 480))

        for _ in range(30):
            splash.render(surface)

        assert sorted(checks) == sorted(
            [
                (splash._app_title, SplashScreen._TITLE_FONT_SIZE),
                (splash._version_text, SplashScreen._VERSION_FONT_SIZE),
            ]
        )
        assert {size for _text, size in checks} <= drawn_sizes


# ---------------------------------------------------------------- EDIT E


class TestLockTestDetectsCallbackUnderLock:
    """F02: the corrected test fails against dispatch under the lock."""

    def test_fails_when_callback_runs_under_lock(self, monkeypatch):
        from test_callbacks_outside_locks import TestTouchCoordinatorButtonCallback

        def dispatch_under_lock(self, pos):
            with self._lock:
                region = self._find_hit_region(pos)
                region.metadata["callback"](pos)
                return region.action_type

        monkeypatch.setattr(
            TouchEventCoordinator, "handle_touch_down", dispatch_under_lock
        )

        with pytest.raises(AssertionError):
            TestTouchCoordinatorButtonCallback().test_callback_may_register_regions()

    def test_passes_against_real_coordinator(self):
        from test_callbacks_outside_locks import TestTouchCoordinatorButtonCallback

        TestTouchCoordinatorButtonCallback().test_callback_may_register_regions()
