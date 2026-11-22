#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Connecting indicator (change-9accfbe0).

The disconnected view splits into Connecting and Failed: while no
connect has failed the dimmed gauge carries no information symbol and a
yellow status dot, and the reconnect indicator turns around that dot in
the gauge palette's colours. After a failed connect the amber
information symbol and a red dot return, with the indicator still
turning. The DISCONNECTED panel is unchanged.
"""

import logging
import time
from typing import Any, List, Tuple

import pytest

import gtach.display.manager as manager_module
import gtach.display.touch_interface as touch_interface_module
from gtach.core import ThreadManager
from gtach.display.manager import DisplayManager
from gtach.display.models import DAY_PALETTE, NIGHT_PALETTE, DisplayMode
from gtach.display.rendering import RenderTarget

CONNECTING_COLOUR = (255, 255, 0)
DISCONNECTED_COLOUR = (255, 0, 0)
CONNECTED_COLOUR = (0, 255, 0)
STATUS_DOT_CENTRE = (240, 60)
CAUSE = "no route to host"


def _raise_runtime_error(*args: Any, **kwargs: Any) -> None:
    raise RuntimeError("injected fault")


@pytest.fixture
def manager(monkeypatch):
    """A RADIAL DisplayManager in the disconnected view, Connecting."""
    monkeypatch.setattr(
        touch_interface_module, "create_touch_interface", _raise_runtime_error
    )
    dm = DisplayManager(ThreadManager())
    dm.config.mode = DisplayMode.RADIAL
    dm._palette = DAY_PALETTE
    dm._link_connected_callback = lambda: True
    dm._vehicle_silent_callback = lambda: None
    dm._link_cause_callback = lambda: None
    return dm


@pytest.fixture
def drawn(manager, monkeypatch):
    """Record the information symbol, the status dot and the indicator."""
    record: dict = {"info": [], "panel": 0, "dots": [], "spinner": []}

    original_info = manager._draw_info_symbol

    def recording_info(surface, palette):
        record["info"].append(palette)
        return original_info(surface, palette)

    original_panel = manager._render_disconnected

    def recording_panel():
        record["panel"] += 1
        return original_panel()

    def recording_spinner(dim=None, bright=None):
        record["spinner"].append((dim, bright))

    engine = manager.rendering_engine
    draw_circle = engine.draw_circle

    def recording_circle(target, colour, centre, radius, *args, **kwargs):
        if centre == STATUS_DOT_CENTRE and radius == 5:
            record["dots"].append(tuple(colour))
        return draw_circle(target, colour, centre, radius, *args, **kwargs)

    monkeypatch.setattr(manager, "_draw_info_symbol", recording_info)
    monkeypatch.setattr(manager, "_render_disconnected", recording_panel)
    monkeypatch.setattr(manager, "_draw_reconnect_spinner", recording_spinner)
    monkeypatch.setattr(engine, "draw_circle", recording_circle)
    return record


def _run_one_frame(dm: DisplayManager) -> None:
    """Run exactly one iteration of the display loop."""
    dm.thread_manager.update_heartbeat = (  # type: ignore[method-assign]
        lambda name: dm._shutdown_event.set()
    )
    dm._shutdown_event.clear()
    dm._display_loop()


def _failed(dm: DisplayManager) -> None:
    dm._link_cause_callback = lambda: CAUSE


def _link_up(dm: DisplayManager) -> None:
    dm._last_sample_ts = time.monotonic()
    dm._link_ok = True


def _engine_off(dm: DisplayManager) -> None:
    dm._vehicle_silent_callback = lambda: time.monotonic() - 1.0


def _regions(dm: DisplayManager) -> List[str]:
    return list(dm.touch_coordinator._z_order)


def _transitions(records) -> List[str]:
    return [
        r.getMessage()
        for r in records
        if r.getMessage().startswith("Disconnected: conn")
    ]


class TestConnecting:
    def test_no_symbol_yellow_dot_and_gauge_indicator(self, manager, drawn):
        _run_one_frame(manager)

        assert manager._frame_connecting is True
        assert drawn["info"] == []
        assert drawn["dots"] == [CONNECTING_COLOUR]
        assert drawn["spinner"] == [(DAY_PALETTE.track, DAY_PALETTE.tick)]
        assert drawn["panel"] == 0
        assert _regions(manager) == ["disconnected_info"]

    def test_empty_cause_is_connecting(self, manager, drawn):
        manager._link_cause_callback = lambda: ""

        _run_one_frame(manager)

        assert manager._frame_connecting is True
        assert drawn["info"] == []

    def test_night_palette_colours_the_indicator(self, manager, drawn):
        manager._palette = NIGHT_PALETTE

        _run_one_frame(manager)

        assert drawn["spinner"] == [(NIGHT_PALETTE.track, NIGHT_PALETTE.tick)]


class TestFailed:
    def test_symbol_red_dot_and_gauge_indicator(self, manager, drawn):
        _failed(manager)

        _run_one_frame(manager)

        assert manager._frame_connecting is False
        assert drawn["info"] == [DAY_PALETTE]
        assert drawn["dots"] == [DISCONNECTED_COLOUR]
        assert drawn["spinner"] == [(DAY_PALETTE.track, DAY_PALETTE.tick)]
        assert _regions(manager) == ["disconnected_info"]

    def test_absent_callback_is_failed(self, manager, drawn):
        manager._link_cause_callback = None

        _run_one_frame(manager)

        assert manager._frame_connecting is False
        assert drawn["info"] == [DAY_PALETTE]
        assert drawn["dots"] == [DISCONNECTED_COLOUR]

    def test_raising_callback_is_failed_and_logged(self, manager, drawn, caplog):
        manager._link_cause_callback = _raise_runtime_error

        with caplog.at_level(logging.DEBUG, logger="DisplayManager"):
            _run_one_frame(manager)

        assert manager._frame_connecting is False
        assert drawn["info"] == [DAY_PALETTE]
        failures = [
            r
            for r in caplog.records
            if r.getMessage().startswith("Link cause callback failed")
        ]
        assert len(failures) == 1
        assert failures[0].levelno == logging.DEBUG
        assert failures[0].exc_info is not None

    def test_cause_with_the_first_sample_in_one_frame(self, manager, drawn):
        _failed(manager)
        manager._last_sample_ts = time.monotonic()

        _run_one_frame(manager)

        assert manager._frame_link_lost is True
        assert manager._frame_connecting is False
        assert drawn["info"] == [DAY_PALETTE]


class TestTransitionLogging:
    def test_one_line_per_transition(self, manager, drawn, caplog):
        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)
            _run_one_frame(manager)
            _failed(manager)
            _run_one_frame(manager)
            _run_one_frame(manager)
            manager._link_cause_callback = lambda: None
            _run_one_frame(manager)

        assert _transitions(caplog.records) == [
            "Disconnected: connecting",
            "Disconnected: connect failed",
            "Disconnected: connecting",
        ]

    def test_leaving_the_view_is_not_a_transition(self, manager, drawn, caplog):
        _run_one_frame(manager)

        _link_up(manager)
        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)

        assert manager._frame_connecting is False
        assert _transitions(caplog.records) == []


class TestPanelOpen:
    def test_panel_draws_its_own_indicator_in_its_own_colours(self, manager, drawn):
        manager._disconnected_details_open = True

        _run_one_frame(manager)

        assert drawn["panel"] == 1
        assert drawn["spinner"] == [(None, None)]
        assert drawn["info"] == []

    def test_panel_unaffected_by_the_transition(self, manager, drawn, caplog):
        manager._disconnected_details_open = True

        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)
            _failed(manager)
            _run_one_frame(manager)

        assert drawn["panel"] == 2
        assert drawn["spinner"] == [(None, None), (None, None)]
        assert drawn["info"] == []
        assert _transitions(caplog.records) == [
            "Disconnected: connecting",
            "Disconnected: connect failed",
        ]


class TestOtherViews:
    def test_engine_off(self, manager, drawn):
        _engine_off(manager)

        _run_one_frame(manager)

        assert manager._frame_engine_off is True
        assert manager._frame_connecting is False
        assert drawn["spinner"] == []
        assert drawn["info"] == []

    def test_live_gauge(self, manager, drawn):
        _link_up(manager)
        manager._last_rpm = 3000

        _run_one_frame(manager)

        assert manager._frame_connecting is False
        assert drawn["spinner"] == []
        assert drawn["info"] == []
        assert drawn["dots"] == [CONNECTED_COLOUR]

    def test_simulation_mode(self, manager, drawn):
        manager._sim_mode = True

        _run_one_frame(manager)

        assert manager._frame_link_lost is False
        assert manager._frame_connecting is False
        assert drawn["spinner"] == []
        assert drawn["info"] == []


class TestLinkConnecting:
    @pytest.mark.parametrize(
        "cause, expected",
        [(None, True), ("", True), (CAUSE, False), (" ", False)],
    )
    def test_cause_values(self, manager, cause, expected):
        manager._link_cause_callback = lambda: cause

        assert manager._link_connecting() is expected

    def test_absent_callback(self, manager):
        manager._link_cause_callback = None

        assert manager._link_connecting() is False


@pytest.fixture
def phase_zero(monkeypatch):
    """Freeze the indicator at the start of a rotation: dot 0 is the lead."""
    monkeypatch.setattr(manager_module.time, "monotonic", lambda: 0.0)


class TestSpinnerColours:
    def _spinner_colours(self, dm, monkeypatch, *args) -> List[Tuple[int, ...]]:
        colours: List[Tuple[int, ...]] = []
        monkeypatch.setattr(
            manager_module.pygame.draw,
            "circle",
            lambda surface, colour, centre, radius: colours.append(tuple(colour)),
        )
        dm._draw_reconnect_spinner(*args)
        return colours

    def test_defaults_are_the_panel_colours(self, manager, monkeypatch, phase_zero):
        colours = self._spinner_colours(manager, monkeypatch)

        assert len(colours) == DisplayManager._SPINNER_DOT_COUNT
        assert colours[0] == DisplayManager._DISCONNECTED_TEXT_COLOUR
        assert colours[-1] != DisplayManager._DISCONNECTED_TEXT_COLOUR

    def test_arguments_replace_them(self, manager, monkeypatch, phase_zero):
        colours = self._spinner_colours(
            manager, monkeypatch, DAY_PALETTE.track, DAY_PALETTE.tick
        )

        assert len(colours) == DisplayManager._SPINNER_DOT_COUNT
        assert colours[0] == DAY_PALETTE.tick
        assert DisplayManager._DISCONNECTED_TEXT_COLOUR not in colours

    def test_geometry_is_centred_on_the_status_dot(self, manager, phase_zero):
        manager.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
        manager._draw_reconnect_spinner(DAY_PALETTE.track, DAY_PALETTE.tick)

        surface = manager.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
        top = STATUS_DOT_CENTRE[1] - DisplayManager._SPINNER_RING_RADIUS
        assert (
            tuple(surface.get_at((STATUS_DOT_CENTRE[0], top)))[:3] == DAY_PALETTE.tick
        )
