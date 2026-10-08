#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""RPM smoothing and sticky band selection in DisplayManager.

Automates the still-applicable cases of test-4c038bed (change-4c038bed;
display review §4.2-§4.4, §7.1). Case identifiers in each test docstring
refer to that plan. TC-011 to TC-014 tested the shift-cue flash, removed
with the rim border in 865d873 (issue-950128c0), and have no target.

DisplayManager is built with object.__new__ and only the attributes the
methods under test read, set to the values DisplayManager.__init__ uses.
"""

import ast
import logging
import math
import types
from pathlib import Path

import pytest

import gtach.display.manager as manager_module
from gtach.display.manager import DisplayManager
from gtach.display.models import DAY_PALETTE, RPMBands

MANAGER_SOURCE = Path(manager_module.__file__)
TAU = 0.150
MARGIN = 75.0


def _host(bands=None, active_band=0):
    host = object.__new__(DisplayManager)
    host.logger = logging.getLogger("DisplayManager")
    host.config = types.SimpleNamespace(rpm_bands=bands or RPMBands())
    host._palette = DAY_PALETTE
    host._rpm_display = 0.0
    host._rpm_ema_tau = TAU
    host._rpm_last_ts = None
    host._active_band = active_band
    host._band_hysteresis = MARGIN
    host._frame_counter = 0
    return host


@pytest.fixture
def clock(monkeypatch):
    """Replace the module's time source with a settable clock."""
    now = [100.0]
    monkeypatch.setattr(
        manager_module,
        "time",
        types.SimpleNamespace(monotonic=lambda: now[0], time=lambda: now[0]),
    )
    return now


def test_init_defaults_match_this_module():
    """The constants _host() uses are those DisplayManager.__init__ sets."""
    source = MANAGER_SOURCE.read_text(encoding="utf-8")
    assert "self._rpm_ema_tau = 0.150" in source
    assert "self._band_hysteresis = 75.0" in source


class TestConditioning:
    def test_first_call_seeds(self, clock):
        """TC-001: the first call returns the sample and seeds the state."""
        host = _host()
        assert host._condition_rpm(3000.0) == 3000.0
        assert host._rpm_display == 3000.0

    def test_step_response_at_tau(self, clock):
        """TC-002: 63.2 % of a step at t = tau; strictly increasing."""
        host = _host()
        host._condition_rpm(0.0)
        values = []
        for _ in range(9):  # 9 x 1/60 s = 150 ms
            clock[0] += 1.0 / 60.0
            values.append(host._condition_rpm(3000.0))
        expected = 3000.0 * (1.0 - math.exp(-1.0))  # about 1896
        assert values[-1] == pytest.approx(expected, rel=0.05)
        assert all(b > a for a, b in zip(values, values[1:]))

    def test_dt_clamped_at_both_ends(self, clock):
        """TC-003: dt <= 0 clamps to 0.001 s; dt of 30 s clamps to 0.5 s."""
        host = _host()
        host._condition_rpm(0.0)
        clock[0] -= 5.0  # clock anomaly: negative interval
        small = host._condition_rpm(3000.0)
        assert small == pytest.approx(3000.0 * (1 - math.exp(-0.001 / TAU)))
        assert 0.0 < small < 30.0

        host = _host()
        host._condition_rpm(0.0)
        clock[0] += 30.0
        large = host._condition_rpm(3000.0)
        assert large == pytest.approx(3000.0 * (1 - math.exp(-0.5 / TAU)))
        assert large < 3000.0

    @pytest.mark.parametrize("bad", [None, "abc"])
    def test_non_numeric_input_degrades_to_raw(self, clock, caplog, bad):
        """TC-004: the argument is returned and one ERROR is logged."""
        host = _host()
        host._condition_rpm(1000.0)
        clock[0] += 0.02
        caplog.set_level(logging.ERROR, logger="DisplayManager")
        assert host._condition_rpm(bad) is bad
        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert errors[0].exc_info is not None


def _sweep(host, values):
    """Return the band index after each call."""
    return [host._get_band_colour(v)[0] for v in values]


class TestBandHysteresis:
    def test_straddling_samples_do_not_thrash(self):
        """TC-005: 2998/3002 alternation keeps one band and one colour."""
        host = _host(active_band=1)
        results = {host._get_band_colour(v) for v in [2998, 3002] * 50}
        assert results == {(1, DAY_PALETTE.bands[1])}
        assert host._active_band == 1

    def test_one_transition_per_boundary_each_way(self):
        """TC-006: up at 3076, down at 2924, two transitions in total."""
        host = _host(active_band=1)
        up_values = list(range(2900, 3201))
        up = _sweep(host, up_values)
        down_values = list(range(3200, 2899, -1))
        down = _sweep(host, down_values)

        assert up_values[up.index(2)] == 3076
        assert down_values[down.index(1)] == 2924
        bands = up + down
        transitions = sum(1 for a, b in zip(bands, bands[1:]) if a != b)
        assert transitions == 2

    def test_torque_approach_band_colour(self):
        """TC-007 (adapted): band 1 takes the palette's blue.

        The plan's white text colour was removed with the text-colour
        column (change-378703da); only the band colour remains.
        """
        host = _host(active_band=1)
        assert host._get_band_colour(2000) == (1, (0, 0, 255))

    def test_all_six_bands_reachable(self):
        """TC-008 (adapted): an upward sweep visits bands 0-5 in order.

        Each band's colour is the active palette's entry for that index.
        """
        host = _host()
        seen = {}
        for rpm in range(0, 7001, 10):
            band, colour = host._get_band_colour(rpm)
            seen.setdefault(band, colour)
        assert sorted(seen) == [0, 1, 2, 3, 4, 5]
        for band, colour in seen.items():
            assert colour == DAY_PALETTE.bands[band]

    def test_margin_clamped_for_narrow_bands(self):
        """TC-009: a 100 RPM gap clamps the margin to 49 RPM."""
        bands = RPMBands(
            idle_max=999,
            torque_start=3000,
            caution_start=3100,
            warning_start=5500,
            danger_start=5800,
        )
        host = _host(bands=bands, active_band=2)
        up_values = list(range(3000, 3301))
        up = _sweep(host, up_values)
        down_values = list(range(3300, 2999, -1))
        down = _sweep(host, down_values)

        # threshold 3100 with margin 0.49 x 100 = 49
        assert up_values[up.index(3)] == 3150
        assert down_values[down.index(2)] == 3050
        assert 3 in up and 2 in down

    def test_large_jump_settles_one_step_per_call(self):
        """TC-010: 0 to 6500 moves one band per call, reaching 5 after five."""
        host = _host(active_band=0)
        bands = _sweep(host, [6500] * 5)
        assert bands == [1, 2, 3, 4, 5]


class TestRawValueRetained:
    def test_radial_mode_conditions_without_overwriting_last_rpm(self, clock):
        """TC-015 (radial): _last_rpm keeps the raw sample.

        _draw_digital_mode was removed (change-378703da); the radial view
        is the only consumer.
        """
        host = _host()
        host._sim_mode = False
        host._condition_rpm(0.0)
        clock[0] += 1.0 / 60.0
        host._last_rpm = 4000

        host._draw_radial_mode()  # rendering fails on the bare host; caught

        assert host._last_rpm == 4000
        assert 0.0 < host._rpm_display < 4000.0

    def test_sim_mode_records_raw_then_conditions(self, clock):
        """TC-015 (simulation): the raw synthetic sample is stored."""
        host = _host()
        host._sim_mode = True
        host._condition_rpm(0.0)
        clock[0] = 0.0  # sin(0) = 0, so the synthetic sample is 3000
        host._rpm_last_ts = -1.0 / 60.0

        host._draw_radial_mode()

        assert host._last_rpm == 3000
        assert 0.0 < host._rpm_display < 3000.0


def test_frame_counter_advanced_once_per_iteration():
    """TC-016: one increment in _display_loop; no wall-clock phase source."""
    source = MANAGER_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    loop = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_display_loop"
    )
    increments = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.AugAssign)
        and isinstance(node.target, ast.Attribute)
        and node.target.attr == "_frame_counter"
    ]
    assert len(increments) == 1
    assert "int(time.monotonic() * 2)" not in source
