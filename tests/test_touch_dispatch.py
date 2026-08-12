#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Unconditional short-press dispatch to the touch coordinator.

Covers change-7d4e91a3: a short press that is neither a setup-mode touch
nor a swipe must reach DisplayManager.handle_touch_event on every
screen, with no test of config.mode. Gating it on DisplayMode.OPTIONS
left the DISCONNECTED screen's Setup and Simulate buttons and the
ACKNOWLEDGEMENT screen's dismiss region registered, drawn, and never
hit-tested.

TouchHandler.__init__ builds a real touch interface, which needs
hardware or an SDL event pump neither of which the unit under test
touches. Both methods use only self.logger, self.display_manager and
self._handle_setup_touch, so they are called unbound against a minimal
host instead.
"""

import logging
import types

import pytest

from gtach.display.models import DisplayMode
from gtach.display.touch import TouchHandler

SWIPE_THRESHOLD = 100


class _FakeDisplayManager:
    """Records the DisplayManager calls the touch path can make."""

    def __init__(self, mode=DisplayMode.RADIAL, touch_result='ACTION',
                 touch_raises=None, in_setup=False):
        self.config = types.SimpleNamespace(mode=mode)
        self.touch_coordinator = types.SimpleNamespace(
            swipe_threshold=SWIPE_THRESHOLD
        )
        # Present but unused after change-7d4e91a3; kept so a
        # reintroduced ThreadStatus branch would still find something
        # to read and the tests below would still detect it.
        self.thread_manager = types.SimpleNamespace(
            get_thread_status=lambda name: None
        )
        self._sim_mode = False

        self._in_setup = in_setup
        self._touch_result = touch_result
        self._touch_raises = touch_raises
        self.calls = []

    def is_in_setup_mode(self):
        return self._in_setup

    def handle_touch_event(self, pos):
        self.calls.append(('handle_touch_event', pos))
        if self._touch_raises is not None:
            raise self._touch_raises
        return self._touch_result

    def _handle_long_press(self, start, end):
        self.calls.append(('_handle_long_press', start, end))

    def _handle_swipe_left(self, start, end):
        self.calls.append(('_handle_swipe_left', start, end))

    def _handle_swipe_right(self, start, end):
        self.calls.append(('_handle_swipe_right', start, end))

    def _handle_swipe_up(self, start, end):
        self.calls.append(('_handle_swipe_up', start, end))

    def _handle_swipe_down(self, start, end):
        self.calls.append(('_handle_swipe_down', start, end))

    def names(self):
        return [call[0] for call in self.calls]


def _host(manager):
    """The minimal self the two methods under test actually use."""
    host = types.SimpleNamespace()
    host.logger = logging.getLogger('test.touch')
    host.display_manager = manager
    host.setup_touches = []
    host._handle_setup_touch = lambda x, y: host.setup_touches.append((x, y))
    return host


def _short_press(manager, x=50, y=60, start_x=None, start_y=None):
    """Invoke _handle_short_press unbound; default to zero displacement."""
    host = _host(manager)
    TouchHandler._handle_short_press(
        host, x, y,
        x if start_x is None else start_x,
        y if start_y is None else start_y,
    )
    return host


class TestDispatchIsUnconditional:
    """Every screen reaches the coordinator."""

    @pytest.mark.parametrize('mode', [
        DisplayMode.RADIAL,
        DisplayMode.ACKNOWLEDGEMENT,
        DisplayMode.OPTIONS,
    ])
    def test_dispatches_on_every_mode(self, mode):
        manager = _FakeDisplayManager(mode=mode)

        _short_press(manager, x=120, y=140)

        assert manager.calls == [('handle_touch_event', (120, 140))]

    def test_dispatch_position_is_the_end_point(self):
        """Not the start point, and passed as a single tuple."""
        manager = _FakeDisplayManager()

        _short_press(manager, x=10, y=20, start_x=15, start_y=25)

        assert manager.calls == [('handle_touch_event', (10, 20))]

    def test_no_mode_test_encloses_the_dispatch(self):
        """Source-level guard against the gate being reintroduced.

        Asserted over executable lines only: the comment explaining why
        the gate was removed names DisplayMode.OPTIONS, and must be
        free to.
        """
        import inspect

        source = inspect.getsource(TouchHandler._handle_short_press)
        code = '\n'.join(
            line for line in source.splitlines()
            if not line.lstrip().startswith('#')
        )
        assert 'config.mode' not in code
        assert 'DisplayMode' not in code


class TestEarlyReturnsPreserved:
    """The setup branch and both swipe branches still return first."""

    def test_setup_mode_bypasses_the_dispatch(self):
        manager = _FakeDisplayManager(in_setup=True)

        host = _short_press(manager, x=30, y=40)

        assert host.setup_touches == [(30, 40)]
        assert manager.calls == []

    def test_swipe_down_bypasses_the_dispatch(self):
        manager = _FakeDisplayManager()

        _short_press(manager, x=0, y=SWIPE_THRESHOLD, start_x=0, start_y=0)

        assert manager.names() == ['_handle_swipe_down']

    def test_swipe_left_bypasses_the_dispatch(self):
        manager = _FakeDisplayManager()

        _short_press(manager, x=-SWIPE_THRESHOLD, y=0, start_x=0, start_y=0)

        assert manager.names() == ['_handle_swipe_left']

    def test_displacement_exactly_at_threshold_is_a_swipe(self):
        """The existing >= test must be preserved."""
        manager = _FakeDisplayManager()

        _short_press(manager, x=0, y=-SWIPE_THRESHOLD, start_x=0, start_y=0)

        assert manager.names() == ['_handle_swipe_up']

    def test_one_below_threshold_dispatches(self):
        manager = _FakeDisplayManager()

        _short_press(manager, x=0, y=SWIPE_THRESHOLD - 1, start_x=0, start_y=0)

        assert manager.names() == ['handle_touch_event']

    def test_exact_diagonal_falls_to_the_vertical_branch(self):
        """abs(dx) == abs(dy) is deliberately vertical."""
        manager = _FakeDisplayManager()

        _short_press(
            manager, x=SWIPE_THRESHOLD, y=SWIPE_THRESHOLD, start_x=0, start_y=0
        )

        assert manager.names() == ['_handle_swipe_down']


class TestContainment:
    """A raising region callback must not escape the handler."""

    def test_exception_is_logged_and_swallowed(self, caplog):
        manager = _FakeDisplayManager(touch_raises=RuntimeError('region exploded'))

        with caplog.at_level(logging.ERROR, logger='test.touch'):
            _short_press(manager)

        assert manager.names() == ['handle_touch_event']
        assert any('Short press handling error' in r.message for r in caplog.records)
        assert any(r.exc_info for r in caplog.records)

    def test_none_result_still_logs_and_does_nothing_else(self, caplog):
        """A press on a screen with no regions is a no-op."""
        manager = _FakeDisplayManager(touch_result=None)

        with caplog.at_level(logging.DEBUG, logger='test.touch'):
            _short_press(manager, x=7, y=8)

        assert manager.calls == [('handle_touch_event', (7, 8))]
        assert any('Touch dispatch at (7, 8) -> None' in r.message
                   for r in caplog.records)


class TestLongPress:
    """The inert DISCONNECTED branch is gone; delegation is universal."""

    def test_delegates_when_disconnected(self, caplog):
        """OBD thread not RUNNING, sim mode off — still delegates."""
        manager = _FakeDisplayManager()
        host = _host(manager)

        with caplog.at_level(logging.INFO, logger='test.touch'):
            TouchHandler._handle_long_press(host, 11, 22)

        assert manager.calls == [('_handle_long_press', (11, 22), (11, 22))]
        assert not any('entering SETUP' in r.message for r in caplog.records)

    def test_thread_status_is_not_consulted(self):
        """The ThreadStatus import and its branch were removed."""
        import inspect

        source = inspect.getsource(TouchHandler._handle_long_press)
        assert 'ThreadStatus' not in source
        assert 'Long press from DISCONNECTED' not in source

    def test_module_no_longer_imports_thread_status(self):
        import inspect

        import gtach.display.touch as touch_module

        assert 'ThreadStatus' not in inspect.getsource(touch_module)


class TestDisplayModeImportRetained:
    """touch.py:26 is still needed by change_mode at touch.py:306."""

    def test_display_mode_still_referenced(self):
        import inspect

        import gtach.display.touch as touch_module

        source = inspect.getsource(touch_module)
        assert 'from .models import DisplayMode' in source
        assert 'DisplayMode.RADIAL' in source
