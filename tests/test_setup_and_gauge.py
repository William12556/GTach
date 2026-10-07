#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Setup lifecycle, gauge range, cached device presence, persistent errors.

Covers change-674bec49 (audit-36b6ea95 C01, C05, C06, C08). Setup
managers are stopped when setup ends or is re-entered, the gauge's full
scale covers the configured redline, WELCOME no longer reads
devices.yaml per frame, and setup error messages stay visible, with
their own text, until the next tap.

SetupDisplayManager and GTachApplication are built with object.__new__
and only the attributes under test, so no Bluetooth interface, async
worker or setup thread is created.
"""

import logging
import threading
import types

import pygame
import pytest

import gtach.app as app_module
import gtach.comm.device_store as device_store_module
from gtach.app import GTachApplication
from gtach.display.manager import DisplayManager
from gtach.display.setup import SetupDisplayManager
from gtach.display.setup_components.layout.circular_positioning import (
    CircularPositioningEngine,
)
from gtach.display.setup_components.rendering.device_surfaces import (
    DeviceSurfaceRenderer,
)
from gtach.display.setup_components.state.coordinator import SetupStateCoordinator
from gtach.display.setup_models import PairingStatus, SetupScreen, SetupState
from gtach.display.typography import get_label_small_font

JOIN_TIMEOUT = 5.0
LONG_ERROR = ("No devices found. Ensure your ELM327 adapter is powered on "
              "and discoverable.")


@pytest.fixture(autouse=True, scope='module')
def _pygame_ready():
    """Off-screen surfaces and fonts; see tests/test_device_list_focus.py."""
    pygame.init()


def _manager(coordinator=None):
    manager = object.__new__(SetupDisplayManager)
    manager.logger = logging.getLogger('test.setup_and_gauge')
    manager.state_coordinator = coordinator or SetupStateCoordinator()
    manager.touch_regions = []
    manager._touch_regions_lock = threading.Lock()
    manager._has_device = False
    return manager


class TestStopSetup:

    def _host(self):
        manager = _manager()
        manager._shutdown_event = threading.Event()
        manager.bluetooth_interface = types.SimpleNamespace(
            cancel_operations=lambda: None, shutdown=lambda: None)  # issue-d140121d
        manager._setup_thread = None
        return manager

    def test_stop_from_the_setup_thread_does_not_join_itself(self):
        manager = self._host()
        errors = []

        def target():
            try:
                manager.stop_setup()
            except Exception as e:  # pragma: no cover - failure path
                errors.append(e)

        thread = threading.Thread(target=target, daemon=True)
        manager._setup_thread = thread
        thread.start()
        thread.join(JOIN_TIMEOUT)

        assert not thread.is_alive()
        assert errors == []

    def test_stop_twice_with_finished_thread(self):
        manager = self._host()
        thread = threading.Thread(target=lambda: None)
        thread.start()
        thread.join(JOIN_TIMEOUT)
        manager._setup_thread = thread

        manager.stop_setup()
        manager.stop_setup()


def _app():
    app = object.__new__(GTachApplication)
    app.logger = logging.getLogger('test.setup_and_gauge')
    app._obd_lock = threading.Lock()  # issue-4005360c
    return app


class TestApplicationStopsSetupManager:

    def test_completion_stops_manager_once_before_exit(self):
        app = _app()
        calls = []
        app._setup_manager = types.SimpleNamespace(stop_setup=lambda: calls.append('stop'))
        app._display = types.SimpleNamespace(exit_setup_mode=lambda: calls.append('exit'))
        app._start_obd = lambda: calls.append('obd')

        app._on_setup_complete()
        app._on_setup_complete()

        assert calls == ['stop', 'exit', 'obd']

    def test_re_entry_stops_previous_manager_first(self, monkeypatch):
        app = _app()
        calls = []
        app._setup_manager = types.SimpleNamespace(stop_setup=lambda: calls.append('old.stop'))
        app._watchdog = types.SimpleNamespace(_thread=types.SimpleNamespace(is_alive=lambda: True))
        app._thread_manager = object()
        app._display = types.SimpleNamespace(
            rendering_engine=types.SimpleNamespace(main_surface=None),
            touch_handler=None,
            set_setup_mode=lambda manager: calls.append('set_setup_mode'))

        def new_manager(*args, **kwargs):
            calls.append('new')
            return types.SimpleNamespace(start_setup=lambda: calls.append('start'))

        monkeypatch.setattr(app_module, 'SetupDisplayManager', new_manager)

        app._start_setup_mode()

        assert calls.index('old.stop') < calls.index('new')


class TestGaugeMaxRpm:

    @pytest.mark.parametrize('redline, expected', [
        (6000, 7000), (7000, 8000), (7500, 8000),
        (8500, 9000), (9000, 9000), (12000, 9000),
    ])
    def test_rule(self, redline, expected):
        host = types.SimpleNamespace(
            config=types.SimpleNamespace(
                rpm_bands=types.SimpleNamespace(redline_rpm=redline)))

        assert DisplayManager._gauge_max_rpm(host) == expected

    @pytest.mark.parametrize('host', [
        types.SimpleNamespace(),
        types.SimpleNamespace(config=types.SimpleNamespace()),
    ])
    def test_missing_configuration(self, host):
        assert DisplayManager._gauge_max_rpm(host) == 7000


class TestCachedDevicePresence:

    def test_cached_regions_use_flag_without_device_store(self, monkeypatch):
        def _forbidden(*args, **kwargs):
            raise AssertionError('DeviceStore constructed')
        monkeypatch.setattr(device_store_module, 'DeviceStore', _forbidden)
        manager = _manager()
        recorded = []
        manager._update_touch_regions_safe = recorded.append

        manager._has_device = True
        manager._update_cached_screen_touch_regions()
        manager._has_device = False
        manager._update_cached_screen_touch_regions()

        assert [[r[0] for r in regions] for regions in recorded] == [
            ['start', 'cancel_setup'], ['start']]

    def test_entry_to_welcome_refreshes_flag(self):
        coordinator = SetupStateCoordinator()
        manager = _manager(coordinator)
        refreshes = []
        manager._refresh_has_device = lambda: refreshes.append(1)
        manager._invalidate_render_cache = lambda screen=None: None
        coordinator.register_screen_transition_callback(manager._on_screen_transition)

        coordinator.transition_to_screen(SetupScreen.DISCOVERY)
        coordinator.transition_to_screen(SetupScreen.WELCOME)

        assert refreshes == [1]


class TestPersistentErrors:

    def test_device_list_render_keeps_error(self):
        state = SetupState(
            current_screen=SetupScreen.DEVICE_LIST,
            discovered_devices=[],
            selected_device=None,
            pairing_status=PairingStatus.IDLE,
            setup_complete=False,
            error_message='OBD check failed',
        )
        coordinator = SetupStateCoordinator(initial_state=state)
        host = types.SimpleNamespace(
            logger=logging.getLogger('test.setup_and_gauge'),
            colors={'background': (216, 200, 146), 'text': (0, 0, 0),
                    'text_dim': (0, 0, 0), 'border': (80, 80, 90),
                    'primary': (100, 150, 250), 'danger': (255, 50, 50)},
            state_coordinator=coordinator,
            positioning_engine=CircularPositioningEngine(),
            device_renderer=DeviceSurfaceRenderer(),
            _update_touch_regions_safe=lambda regions: None,
            _draw_focus_arrows=lambda surface, info: None,
        )

        SetupDisplayManager._render_device_list_screen(
            host, pygame.Surface((480, 480)), coordinator.get_state())

        assert coordinator.get_state().error_message == 'OBD check failed'

    def test_tap_clears_error_before_dispatch(self, monkeypatch):
        manager = _manager()
        manager.state_coordinator.update_state(error_message='Device not available')
        manager.touch_regions = [('start', pygame.Rect(0, 0, 10, 10))]
        seen = []
        monkeypatch.setattr(
            manager, '_handle_touch_action',
            lambda action, region: seen.append(
                manager.state_coordinator.get_state().error_message),
            raising=False)

        manager.handle_touch_event((5, 5))

        assert seen == [None]


class TestFitText:

    def test_short_and_long_messages(self):
        font = get_label_small_font()
        assert font is not None
        manager = _manager()

        short = manager._fit_text(font, 'Device not available')
        long = manager._fit_text(font, LONG_ERROR)

        assert short == 'Device not available'
        assert long == 'No devices found.'
        assert font.size(short)[0] <= 400
        assert font.size(long)[0] <= 400
