#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Gauge status symbols (change-adb3afeb).

EDIT A: Palette gains symbol and alert. EDIT B: Engine off draws a grey
ignition-key symbol; DISCONNECTED draws a dimmed gauge with an amber
information symbol, and a tap on it opens the existing DISCONNECTED
screen as a panel that a tap outside its buttons closes; the OPTIONS
title is removed.
"""

import ast
import inspect
import logging
import textwrap
import time
from typing import Any, List

import pytest

import gtach.display.manager as manager_module
import gtach.display.touch_interface as touch_interface_module
from gtach.core import ThreadManager
from gtach.display.manager import DisplayManager
from gtach.display.models import DAY_PALETTE, NIGHT_PALETTE, DisplayMode
from gtach.display.rendering import RenderTarget
from gtach.display.touch import TouchHandler

LONG_PRESS = 1.0


def _raise_runtime_error(*args: Any, **kwargs: Any) -> None:
    raise RuntimeError("injected fault")


class _StubTouchInterface:
    """Accepts the callback registration and nothing else."""

    def register_callback(self, callback: Any) -> None:
        pass

    def stop(self) -> None:
        pass


@pytest.fixture
def manager(monkeypatch):
    """A RADIAL DisplayManager with the link lost and no Engine off evidence.

    A failure cause is set, so the disconnected view is Failed and draws
    the information symbol; Connecting is covered by
    tests/test_connecting_indicator.py (change-9accfbe0).
    """
    monkeypatch.setattr(
        touch_interface_module, "create_touch_interface", _raise_runtime_error
    )
    dm = DisplayManager(ThreadManager())
    dm.config.mode = DisplayMode.RADIAL
    dm.config.touch_long_press = LONG_PRESS
    dm._palette = DAY_PALETTE
    dm._link_connected_callback = lambda: True
    dm._vehicle_silent_callback = lambda: None
    dm._link_cause_callback = lambda: "no route to host"
    return dm


def _run_one_frame(dm: DisplayManager) -> None:
    """Run exactly one iteration of the display loop."""
    dm.thread_manager.update_heartbeat = (  # type: ignore[method-assign]
        lambda name: dm._shutdown_event.set()
    )
    dm._shutdown_event.clear()
    dm._display_loop()


def _link_up(dm: DisplayManager) -> None:
    dm._last_sample_ts = time.monotonic()
    dm._link_ok = True


def _engine_off(dm: DisplayManager) -> None:
    dm._vehicle_silent_callback = lambda: time.monotonic() - 1.0


def _regions(dm: DisplayManager) -> List[str]:
    """Registered region ids in z-order, lowest first."""
    return list(dm.touch_coordinator._z_order)


@pytest.fixture
def drawn(manager, monkeypatch):
    """Record text, the panel render and both symbol helpers."""
    record: dict = {"text": [], "panel": [], "info": [], "key": []}
    engine = manager.rendering_engine
    render_text = engine.render_text

    def recording_text(target, text, *args, **kwargs):
        record["text"].append(text)
        return render_text(target, text, *args, **kwargs)

    monkeypatch.setattr(engine, "render_text", recording_text)
    monkeypatch.setattr(
        manager, "_render_disconnected", lambda: record["panel"].append(1)
    )
    for name, key in (("_draw_info_symbol", "info"), ("_draw_key_symbol", "key")):
        original = getattr(manager, name)

        def recorder(surface, palette, _key=key, _original=original):
            record[_key].append(palette)
            return _original(surface, palette)

        monkeypatch.setattr(manager, name, recorder)
    return record


def _is_readout(text: str) -> bool:
    """Whether text is the RPM readout ('4.5'); tick labels have no point."""
    whole, point, frac = text.partition(".")
    return bool(point) and whole.isdigit() and frac.isdigit()


def _back_buffer(dm: DisplayManager) -> Any:
    return dm.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)


def _pixel(dm: DisplayManager, pos: tuple) -> tuple:
    return tuple(_back_buffer(dm).get_at(pos))[:3]


def _draw_radial(dm: DisplayManager) -> None:
    dm.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
    dm._draw_radial_mode()


# ---------------------------------------------------------------- EDIT A


class TestPaletteColours:
    def test_day_values(self):
        assert DAY_PALETTE.symbol == (150, 150, 150)
        assert DAY_PALETTE.alert == (230, 160, 0)

    def test_night_values(self):
        assert NIGHT_PALETTE.symbol == (120, 120, 120)
        assert NIGHT_PALETTE.alert == (150, 105, 0)


# ---------------------------------------------------------------- EDIT B


class TestDisconnectedPanelClosed:
    def test_only_info_region_registered(self, manager):
        _run_one_frame(manager)

        assert manager._disconnected_view() is True
        assert _regions(manager) == ["disconnected_info"]
        rect = manager.touch_coordinator._regions["disconnected_info"].rect
        assert rect.size == (DisplayManager.ICON_TOUCH_SIZE,) * 2
        assert rect.center == (240, 240)

    def test_dimmed_gauge_with_info_symbol(self, manager, drawn):
        _run_one_frame(manager)

        assert drawn["panel"] == []
        assert drawn["info"] == [DAY_PALETTE]
        assert drawn["key"] == []
        assert not [t for t in drawn["text"] if _is_readout(t)]
        assert "RPM × 1000" in drawn["text"]

    def test_symbol_geometry_and_dimmed_disc(self, manager):
        manager._frame_link_lost = True

        _draw_radial(manager)

        assert _pixel(manager, (240, 300)) == DAY_PALETTE.track
        assert _pixel(manager, (240, 270)) == DAY_PALETTE.alert
        assert _pixel(manager, (240, 222)) == (0, 0, 0)
        assert _pixel(manager, (240, 245)) == (0, 0, 0)
        assert _pixel(manager, (240, 229)) == DAY_PALETTE.alert

    def test_night_palette_alert(self, manager):
        manager._frame_link_lost = True
        manager._palette = NIGHT_PALETTE

        _draw_radial(manager)

        assert _pixel(manager, (240, 270)) == NIGHT_PALETTE.alert
        assert _pixel(manager, (240, 300)) == NIGHT_PALETTE.track

    def test_status_dot_drawn(self, manager, monkeypatch):
        calls: List[int] = []
        monkeypatch.setattr(manager, "_draw_status_indicator", lambda: calls.append(1))

        _run_one_frame(manager)

        assert calls == [1]

    def test_hold_on_symbol_opens_panel_not_palette(self, manager):
        _run_one_frame(manager)
        handler = TouchHandler(manager, touch_interface=_StubTouchInterface())

        handler._process_touch(0, 240, 240, True, 100.0)
        handler._process_touch(0, 240, 240, False, 101.5)

        assert manager._disconnected_details_open is True
        assert manager._palette is DAY_PALETTE


class TestPanelOpenAndClose:
    def test_tap_opens_panel(self, manager, drawn, caplog):
        _run_one_frame(manager)
        closed_key = manager._current_view_key()

        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            manager.touch_coordinator.handle_touch_down((240, 240))
        _run_one_frame(manager)

        assert manager._disconnected_details_open is True
        assert manager._current_view_key() != closed_key
        assert _regions(manager) == ["disconnected_close", "disconnected_setup"]
        assert drawn["panel"] == [1]
        assert any(
            r.getMessage() == "DISCONNECTED details opened" for r in caplog.records
        )

    def test_reset_registered_above_close_when_set(self, manager):
        manager._reset_callback = lambda: None
        manager._disconnected_details_open = True

        _run_one_frame(manager)

        assert _regions(manager) == [
            "disconnected_close",
            "disconnected_setup",
            "disconnected_reset",
        ]

    def test_close_region_covers_the_screen(self, manager):
        manager._disconnected_details_open = True

        _run_one_frame(manager)

        rect = manager.touch_coordinator._regions["disconnected_close"].rect
        assert tuple(rect) == (0, 0, 480, 480)

    def test_buttons_take_precedence_over_close(self, manager):
        entered: List[int] = []
        reset: List[int] = []
        manager._setup_entry_callback = lambda: entered.append(1)
        manager._reset_callback = lambda: reset.append(1)
        manager._disconnected_details_open = True
        _run_one_frame(manager)

        manager.touch_coordinator.handle_touch_down(
            manager._disconnected_btn_setup.center
        )
        manager.touch_coordinator.handle_touch_down(
            manager._disconnected_btn_reset.center
        )

        assert entered == [1]
        assert reset == [1]
        assert manager._disconnected_details_open is True

    def test_tap_outside_buttons_closes(self, manager, drawn, caplog):
        manager._disconnected_details_open = True
        _run_one_frame(manager)

        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            manager.touch_coordinator.handle_touch_down((240, 120))
        _run_one_frame(manager)

        assert manager._disconnected_details_open is False
        assert _regions(manager) == ["disconnected_info"]
        assert drawn["info"]
        assert any(
            r.getMessage() == "DISCONNECTED details closed: tap" for r in caplog.records
        )


class TestPanelClosesWithTheView:
    def test_link_recovery_closes_in_the_same_frame(self, manager, drawn, caplog):
        manager._disconnected_details_open = True
        _run_one_frame(manager)
        _link_up(manager)

        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)

        assert manager._disconnected_details_open is False
        assert drawn["panel"] == [1]
        assert _regions(manager) == []
        assert any(
            r.getMessage() == "DISCONNECTED details closed: link recovered"
            for r in caplog.records
        )

    def test_engine_off_closes_in_the_same_frame(self, manager, drawn, caplog):
        manager._disconnected_details_open = True
        _run_one_frame(manager)
        _engine_off(manager)

        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)

        assert manager._frame_engine_off is True
        assert manager._disconnected_details_open is False
        assert drawn["panel"] == [1]
        assert drawn["key"]
        assert _regions(manager) == []
        assert any(
            r.getMessage() == "DISCONNECTED details closed: engine off"
            for r in caplog.records
        )

    def test_tap_in_the_frame_the_link_recovers(self, manager, drawn):
        _run_one_frame(manager)
        _link_up(manager)
        manager.touch_coordinator.handle_touch_down((240, 240))

        _run_one_frame(manager)

        assert manager._disconnected_details_open is False
        assert drawn["panel"] == []
        assert _regions(manager) == []

    def test_swipe_down_on_open_panel_enters_options(self, manager, caplog):
        manager._disconnected_details_open = True
        _run_one_frame(manager)
        handler = TouchHandler(manager, touch_interface=_StubTouchInterface())

        handler._process_touch(0, 240, 120, True, 100.0)
        handler._process_touch(0, 240, 320, False, 100.2)
        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)

        assert manager.config.mode == DisplayMode.OPTIONS
        assert manager._disconnected_details_open is False
        assert any(
            r.getMessage() == "DISCONNECTED details closed: mode change"
            for r in caplog.records
        )

    def test_swipe_up_from_options_returns_to_closed_panel(self, manager):
        manager._disconnected_details_open = True
        _run_one_frame(manager)
        manager._handle_swipe_down((240, 120), (240, 320))
        _run_one_frame(manager)

        manager._handle_swipe_up((240, 320), (240, 120))
        _run_one_frame(manager)

        assert manager.config.mode == DisplayMode.RADIAL
        assert _regions(manager) == ["disconnected_info"]


class TestEngineOff:
    def test_key_symbol_without_text_or_regions(self, manager, drawn):
        _engine_off(manager)

        _run_one_frame(manager)

        assert drawn["key"] == [DAY_PALETTE]
        assert drawn["info"] == []
        assert DisplayManager.ENGINE_OFF_TEXT not in drawn["text"]
        assert not [t for t in drawn["text"] if _is_readout(t)]
        assert _regions(manager) == []

    def test_key_geometry(self, manager):
        manager._frame_engine_off = True

        _draw_radial(manager)

        symbol = DAY_PALETTE.symbol
        assert _pixel(manager, (206, 240)) == symbol  # bow ring, left
        assert _pixel(manager, (222, 240)) != symbol  # bow ring, hollow
        assert _pixel(manager, (258, 240)) == symbol  # shaft
        assert _pixel(manager, (264, 250)) == symbol  # first tooth
        assert _pixel(manager, (274, 250)) == symbol  # second tooth
        assert _pixel(manager, (282, 240)) != symbol  # right of the shaft
        assert _pixel(manager, (240, 300)) == DAY_PALETTE.band_centres[0]

    def test_engine_off_text_retained_and_not_called(self, manager, monkeypatch):
        source = textwrap.dedent(inspect.getsource(DisplayManager))
        tree = ast.parse(source)
        callers = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and "_draw_engine_off_text" in ast.unparse(node.body)
        ]
        assert callers == []

        texts: List[str] = []
        monkeypatch.setattr(
            manager.rendering_engine,
            "render_text",
            lambda target, text, *a, **k: texts.append(text),
        )
        manager._draw_engine_off_text((240, 240))
        assert texts == [DisplayManager.ENGINE_OFF_TEXT]


class TestLiveGauge:
    def test_no_symbol_and_readout_drawn(self, manager, drawn):
        _link_up(manager)
        manager._last_rpm = 3000

        _run_one_frame(manager)

        assert drawn["info"] == []
        assert drawn["key"] == []
        assert drawn["panel"] == []
        assert any(_is_readout(t) for t in drawn["text"])
        assert _regions(manager) == []


class TestSymbolFailure:
    @pytest.mark.parametrize("name", ["_draw_info_symbol", "_draw_key_symbol"])
    def test_logged_and_gauge_continues(self, manager, monkeypatch, caplog, name):
        monkeypatch.setattr(manager_module.pygame.draw, "line", _raise_runtime_error)
        monkeypatch.setattr(manager_module.pygame.draw, "rect", _raise_runtime_error)

        with caplog.at_level(logging.ERROR, logger="DisplayManager"):
            getattr(manager, name)(_back_buffer(manager), DAY_PALETTE)

        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(errors) == 1
        assert errors[0].exc_info is not None


class TestOptionsMenu:
    def test_no_title_and_controls_unchanged(self, manager, drawn):
        _link_up(manager)
        manager._handle_swipe_down((240, 120), (240, 320))

        _run_one_frame(manager)

        assert "Options" not in drawn["text"]
        assert "Clear settings" in drawn["text"]
        assert "Check for updates" in drawn["text"]
        assert "Swipe up to return" in drawn["text"]
        assert _regions(manager) == ["clear_settings", "check_updates"]
