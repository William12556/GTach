#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""One Setup button and a reconnect spinner on the DISCONNECTED screen.

Covers change-4f1e82b7. Simulate duplicated OPTIONS page 0's
simulation_mode control and is removed; the screen gains an indicator
so an operator can see that GTach is alive and roughly when the next
connect attempt falls.

The indicator was originally a retry-countdown arc at the bottom of
the screen. Adding the BT Reset button (change-8a63d5f1) filled the
band the arc assumed was free and the arc clipped the button, so it
was replaced with an 8-dot rotating spinner in the upper half of the
screen (issue-<pending>). The same change also fixed the connection
status dot never being drawn on this screen, and switched the screen
from red-on-black to pale-dusty-yellow-on-black text for readability.

The load-bearing property under test is that the spinner's phase
derives from time.monotonic() and from NO transport attribute.
TestPhaseIsIndependentOfTransport asserts this behaviourally and at
source level.
"""

import logging
import types

import pytest

from gtach.display.manager import DisplayManager
from gtach.display.models import DAY_PALETTE


def _code_only(func):
    """Source of func with the docstring and comments removed.

    The docstring names the transport in order to state that the phase
    does NOT come from it, so a source-level assertion about the code
    must not read it.
    """
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source).body[0]
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        first = tree.body[1]
    else:
        first = tree.body[0]

    lines = source.splitlines()[first.lineno - 1:]
    return '\n'.join(line for line in lines
                     if line.strip() and not line.lstrip().startswith('#'))


class _Recorder:
    """Captures what the render asked to draw."""

    def __init__(self, surface=object()):
        self.texts = []
        self.buttons = []
        self.polygons = []
        self._surface = surface

    def as_host(self, **overrides):
        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.disconnected')
        host._palette = DAY_PALETTE
        # Class constants, so a SimpleNamespace host must be given them.
        host._RETRY_ARC_DEFAULT_PERIOD = (
            DisplayManager._RETRY_ARC_DEFAULT_PERIOD
        )
        host._DISCONNECTED_BG_COLOUR = DisplayManager._DISCONNECTED_BG_COLOUR
        host._DISCONNECTED_TEXT_COLOUR = DisplayManager._DISCONNECTED_TEXT_COLOUR
        host._SPINNER_CENTRE = DisplayManager._SPINNER_CENTRE
        host._SPINNER_RING_RADIUS = DisplayManager._SPINNER_RING_RADIUS
        host._SPINNER_DOT_RADIUS = DisplayManager._SPINNER_DOT_RADIUS
        host._SPINNER_DOT_COUNT = DisplayManager._SPINNER_DOT_COUNT
        host._link_cause_callback = None
        host._retry_interval_callback = None
        host._disconnected_btn_setup = None
        host._disconnected_btn_bt_reset = None
        host._get_cached_font = lambda size: f'font-{size}'
        host._draw_status_indicator = lambda: None
        host._draw_button = lambda rect, label, fill, font: \
            self.buttons.append((rect, label))
        host._draw_reconnect_spinner = lambda: None
        host.rendering_engine = types.SimpleNamespace(
            clear_surface=lambda *a, **k: None,
            get_surface=lambda target: self._surface,
            render_text=lambda target, text, font, colour, pos, center=False:
                self.texts.append((text, pos, font, colour)),
        )
        for name, value in overrides.items():
            setattr(host, name, value)
        return host


class TestOneButton:
    """Exactly one region; the Setup rect is unmoved."""

    def _registered(self):
        """Drive _register_disconnected_regions against a recording column."""
        calls = []

        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.disconnected')
        # Unset, so change-8a63d5f1's Bluetooth Reset button is not
        # registered and the single-button form these tests describe
        # still holds.
        host._bluetooth_reset_callback = None

        def _column(specs, width, top, **kwargs):
            calls.append(types.SimpleNamespace(
                specs=tuple(specs), width=width, top=top, kwargs=kwargs
            ))
            # One rect per spec, as the real _button_column returns.
            return ['rect-%d' % i for i in range(len(tuple(specs)))]

        host._button_column = _column
        host._enter_setup_from_disconnected = lambda: None
        DisplayManager._register_disconnected_regions(host)
        return host, calls[0]

    def test_exactly_one_region_registered(self):
        _host, call = self._registered()

        assert len(call.specs) == 1
        assert call.specs[0][0] == 'disconnected_setup'

    def test_no_simulate_region(self):
        _host, call = self._registered()

        assert all(spec[0] != 'disconnected_simulate' for spec in call.specs)

    def test_geometry_unchanged(self):
        """width and top must match the pre-change two-button call."""
        _host, call = self._registered()

        assert call.width == 240
        assert call.top == 240

    def test_setup_rect_is_the_first_rect(self):
        """_button_column stacks downward, so first-of-one == first-of-two."""
        host, _call = self._registered()

        assert host._disconnected_btn_setup == 'rect-0'

    def test_sim_attribute_and_region_are_gone_from_the_module(self):
        import gtach.display.manager as manager_module

        source = open(manager_module.__file__, encoding='utf-8').read()

        assert '_disconnected_btn_sim' not in source
        assert 'disconnected_simulate' not in source

    def test_no_control_added_in_the_freed_slot(self):
        """The slot is deliberately empty pending a separate issue."""
        _host, call = self._registered()

        assert len(call.specs) == 1


class TestSpinnerPeriod:
    """The rotation period falls back to 5.0 whenever it cannot be trusted."""

    def _draw(self, callback, monkeypatch, monotonic=1000.0, circle=None):
        recorder = _Recorder()
        host = recorder.as_host(_retry_interval_callback=callback)

        captured = []

        import gtach.display.manager as manager_module
        monkeypatch.setattr(manager_module.time, 'monotonic', lambda: monotonic)
        monkeypatch.setattr(
            manager_module.pygame.draw, 'circle',
            circle or (lambda surface, colour, pos, radius:
                       captured.append((colour, pos, radius)))
        )

        DisplayManager._draw_reconnect_spinner(host)
        return captured

    def test_default_period_constant(self):
        assert DisplayManager._RETRY_ARC_DEFAULT_PERIOD == 5.0

    def test_callback_unset_uses_default(self, monkeypatch):
        captured = self._draw(None, monkeypatch)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_zero_period_falls_back(self, monkeypatch):
        """Must not raise ZeroDivisionError."""
        captured = self._draw(lambda: 0, monkeypatch)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_negative_period_falls_back(self, monkeypatch):
        captured = self._draw(lambda: -1, monkeypatch)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_raising_callback_falls_back(self, monkeypatch):
        def _boom():
            raise RuntimeError('interval exploded')

        captured = self._draw(_boom, monkeypatch)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_non_numeric_period_falls_back(self, monkeypatch):
        captured = self._draw(lambda: 'five', monkeypatch)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_bool_is_not_accepted_as_a_period(self, monkeypatch):
        """True is an int in Python; a period of 1.0 would be wrong."""
        captured = self._draw(lambda: True, monkeypatch)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_period_shorter_than_a_frame_stays_in_range(self, monkeypatch):
        """The phase must remain valid for a tiny period."""
        captured = self._draw(lambda: 0.001, monkeypatch)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_very_large_clock_still_yields_a_valid_phase(self, monkeypatch):
        captured = self._draw(lambda: 5.0, monkeypatch, monotonic=1e12)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT

    def test_drawing_failure_does_not_propagate(self, monkeypatch, caplog):
        def _boom(surface, colour, pos, radius):
            raise RuntimeError('circle exploded')

        with caplog.at_level(logging.DEBUG, logger='test.disconnected'):
            self._draw(lambda: 5.0, monkeypatch, circle=_boom)

        assert any('Reconnect spinner render error' in r.getMessage()
                   for r in caplog.records)


class TestPhaseIsIndependentOfTransport:
    """The critical constraint: the spinner is driven by the frame clock."""

    def _dots(self, monkeypatch, monotonic, period=5.0):
        """Return the colours of the dots drawn at a given clock reading."""
        import gtach.display.manager as manager_module

        recorder = _Recorder()
        host = recorder.as_host(_retry_interval_callback=lambda: period)

        captured = []
        monkeypatch.setattr(manager_module.time, 'monotonic', lambda: monotonic)
        monkeypatch.setattr(
            manager_module.pygame.draw, 'circle',
            lambda surface, colour, pos, radius: captured.append(colour)
        )

        DisplayManager._draw_reconnect_spinner(host)

        assert len(captured) == DisplayManager._SPINNER_DOT_COUNT
        return captured

    def _lead_index(self, dots):
        """Index of the brightest (nearest-black) dot — the current lead."""
        return min(range(len(dots)), key=lambda i: sum(dots[i]))

    def test_spinner_advances_with_the_clock_alone(self, monkeypatch):
        """No transport state changes between the two renders."""
        n = DisplayManager._SPINNER_DOT_COUNT
        lead_at_t = self._lead_index(self._dots(monkeypatch, 1000.0))
        lead_at_t_plus = self._lead_index(self._dots(monkeypatch, 1002.5))

        # Half a 5.0 s period elapsed, so the lead should have advanced
        # by roughly half the dot count.
        advance = (lead_at_t_plus - lead_at_t) % n
        assert advance == pytest.approx(n / 2, abs=1)

    def test_phase_is_periodic(self, monkeypatch):
        """One full period later, the spinner is back where it started."""
        lead_at_t = self._lead_index(self._dots(monkeypatch, 1000.0))
        lead_at_t_plus_period = self._lead_index(self._dots(monkeypatch, 1005.0))

        assert lead_at_t_plus_period == lead_at_t

    def test_source_reads_monotonic_and_no_transport_state(self):
        code = _code_only(DisplayManager._draw_reconnect_spinner)

        assert 'time.monotonic()' in code
        # The period is the ONLY thing asked of the transport, and it is
        # asked through the interval callback.
        for forbidden in (
            '_link_connected_callback',
            '_link_cause_callback',
            '_transport',
            'is_connected',
            'last_failure_cause',
        ):
            assert forbidden not in code, forbidden

    def test_phase_line_derives_only_from_clock_and_period(self):
        code = _code_only(DisplayManager._draw_reconnect_spinner)

        phase_lines = [line.strip() for line in code.splitlines()
                       if 'phase' in line and '=' in line]
        assert phase_lines
        assert any('time.monotonic()' in line and 'period' in line
                   for line in phase_lines), phase_lines


class TestRenderIntegration:
    """The rest of the screen is unchanged."""

    def _render(self, **overrides):
        recorder = _Recorder()
        host = recorder.as_host(**overrides)
        DisplayManager._render_disconnected(host)
        return recorder, host

    def test_only_setup_is_drawn(self):
        recorder, _host = self._render(_disconnected_btn_setup='rect-0')

        assert recorder.buttons == [('rect-0', 'Setup')]

    def test_cause_line_is_unchanged_position_and_font(self):
        """change-5e7a03c4's line keeps its position and font.

        Its colour is no longer independent of the rest of the page —
        the DISCONNECTED screen now draws all text in
        _DISCONNECTED_TEXT_COLOUR (issue-<pending>).
        """
        recorder, _host = self._render(
            _link_cause_callback=lambda: 'no bluetooth controller'
        )

        drawn = {text: (pos, font, colour)
                 for text, pos, font, colour in recorder.texts}
        assert 'no bluetooth controller' in drawn
        pos, font, colour = drawn['no bluetooth controller']
        assert pos == (240, 210)
        assert font == 'font-18'
        assert colour == DisplayManager._DISCONNECTED_TEXT_COLOUR

    def test_title_and_message_unchanged(self):
        recorder, _host = self._render()

        texts = [text for text, _pos, _font, _colour in recorder.texts]
        assert texts == ['Disconnected', 'OBD connection not available']

    def test_title_and_message_use_the_page_text_colour(self):
        recorder, _host = self._render()

        colours = [colour for _text, _pos, _font, colour in recorder.texts]
        assert colours == [DisplayManager._DISCONNECTED_TEXT_COLOUR] * 2

    def test_spinner_is_drawn_after_the_button(self):
        order = []
        recorder = _Recorder()
        host = recorder.as_host(_disconnected_btn_setup='rect-0')
        host._draw_button = lambda *a: order.append('button')
        host._draw_reconnect_spinner = lambda: order.append('spinner')

        DisplayManager._render_disconnected(host)

        assert order == ['button', 'spinner']

    def test_status_indicator_is_drawn(self):
        """issue-<pending>: previously unreachable for this screen."""
        order = []
        recorder = _Recorder()
        host = recorder.as_host()
        host._draw_status_indicator = lambda: order.append('status')

        DisplayManager._render_disconnected(host)

        assert 'status' in order
