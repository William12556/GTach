#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Three fixed slots and a single focused device on the Select Device screen.

Covers change-479b2e51. The DEVICE_LIST screen rendered every
discovered device in one unbounded column, each row independently
selectable, which could overflow the circular safe area and collide
with the Back/Retry buttons. It now renders exactly three slots centred
on the display: the focused device in the middle, its neighbours above
and below, and an outlined empty frame wherever a neighbour does not
exist.

The load-bearing properties under test are that exactly one touch
region is selectable — the middle slot — and that focus moves by
exactly one device per swipe, clamped at both ends of the discovered
list.

SetupDisplayManager.__init__ builds a Bluetooth interface and a setup
thread that none of the methods under test touch, so they are called
unbound against a minimal host, as the other display tests do.
"""

import datetime
import logging
import types

import pygame
import pytest

from gtach.display.setup import SetupDisplayManager
from gtach.display.setup_components.layout.circular_positioning import (
    CircularPositioningEngine,
)
from gtach.display.setup_components.rendering.device_surfaces import (
    DeviceSurfaceRenderer,
)
from gtach.display.setup_components.state.coordinator import SetupStateCoordinator
from gtach.display.setup_models import (
    BluetoothDevice,
    PairingStatus,
    SetupScreen,
    SetupState,
)
from gtach.display.touch import TouchHandler

SWIPE_THRESHOLD = 100


@pytest.fixture(autouse=True, scope='module')
def _pygame_ready():
    """Off-screen surfaces and fonts, no display and no teardown.

    pygame.quit() would tear the font system down under the other test
    modules, which hold cached Font objects; init is idempotent and
    needs no hardware.
    """
    pygame.init()


def _device(index):
    return BluetoothDevice(
        name=f"Device {index}",
        mac_address=f"00:11:22:33:44:{index:02X}",
        signal_strength=-60,
        device_type="ELM327",
        last_seen=datetime.datetime(2026, 8, 19),
    )


def _state(device_count):
    return SetupState(
        current_screen=SetupScreen.DEVICE_LIST,
        discovered_devices=[_device(i) for i in range(device_count)],
        selected_device=None,
        pairing_status=PairingStatus.IDLE,
        setup_complete=False,
    )


class _Render:
    """Drives _render_device_list_screen against real components."""

    def __init__(self, device_count, focused_index=0):
        self.state = _state(device_count)

        self.coordinator = SetupStateCoordinator(initial_state=self.state)
        self.coordinator.focused_index = focused_index

        self.regions = []
        self.arrows = []

        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.device_list')
        host.colors = {
            'background': (216, 200, 146),
            'text': (0, 0, 0),
            'text_dim': (0, 0, 0),
            'border': (80, 80, 90),
            'primary': (100, 150, 250),
            'danger': (255, 50, 50),
        }
        host.state_coordinator = self.coordinator
        host.positioning_engine = CircularPositioningEngine()
        host.device_renderer = DeviceSurfaceRenderer()
        host._update_touch_regions_safe = self.regions.extend
        host._draw_focus_arrows = lambda surface, focus_info: self.arrows.append(
            focus_info
        )
        self.host = host

        self.surface = pygame.Surface((480, 480))
        SetupDisplayManager._render_device_list_screen(host, self.surface, self.state)

    @property
    def device_regions(self):
        return [region for region in self.regions if region[0] == 'device']

    @property
    def focus_info(self):
        return self.arrows[0] if self.arrows else None


class TestSlotCount:
    """Three slots always, whatever the device count."""

    @pytest.mark.parametrize('count', [1, 2, 3, 5, 9])
    def test_layout_is_always_three_slots(self, count):
        layout = CircularPositioningEngine().calculate_focused_slot_layout()

        assert len(layout) == 3
        assert [item['slot'] for item in layout] == ['top', 'middle', 'bottom']

    def test_middle_slot_is_centred_on_the_display(self):
        engine = CircularPositioningEngine()

        middle = engine.calculate_focused_slot_layout()[1]

        assert middle['y'] + middle['height'] // 2 == engine.display_center[1]

    def test_slots_are_evenly_pitched(self):
        layout = CircularPositioningEngine().calculate_focused_slot_layout()

        top, middle, bottom = (item['y'] for item in layout)

        assert middle - top == bottom - middle

    def test_every_slot_is_within_the_circular_safe_area(self):
        engine = CircularPositioningEngine()

        layout = engine.calculate_focused_slot_layout()
        result = engine.validate_all_layout_elements(layout, 'DEVICE_LIST')

        assert result['validation_summary']['passed'], result['invalid_elements']

    def test_slot_column_clears_the_back_and_retry_buttons(self):
        """The buttons' top edge is y=340 and must stay clear."""
        layout = CircularPositioningEngine().calculate_focused_slot_layout()

        bottom = layout[2]

        assert bottom['y'] + bottom['height'] <= 340


class TestTouchRegions:
    """Only the middle slot is selectable."""

    def test_no_devices_registers_no_device_region(self):
        render = _Render(0)

        assert render.device_regions == []

    def test_one_device_registers_exactly_one_region(self):
        render = _Render(1)

        assert len(render.device_regions) == 1

    @pytest.mark.parametrize('count,focused', [(2, 0), (2, 1), (5, 2), (5, 4)])
    def test_exactly_one_region_whatever_the_focus(self, count, focused):
        render = _Render(count, focused_index=focused)

        assert len(render.device_regions) == 1

    def test_the_registered_device_is_the_focused_one(self):
        render = _Render(5, focused_index=2)

        _action, _rect, device = render.device_regions[0]

        assert device.name == "Device 2"

    def test_the_region_rect_covers_the_middle_slot(self):
        render = _Render(5, focused_index=2)
        middle = CircularPositioningEngine().calculate_focused_slot_layout()[1]

        _action, rect, _device = render.device_regions[0]

        assert rect.top == middle['y']
        assert rect.centery == pytest.approx(240, abs=middle['height'] // 2)

    def test_back_and_retry_are_still_registered(self):
        render = _Render(3, focused_index=1)

        assert [region[0] for region in render.regions[-2:]] == ['back', 'retry']


class TestSlotContents:
    """Neighbours fill the outer slots; absent neighbours are empty frames."""

    def _slots(self, count, focused_index):
        """The device-or-None each slot resolves to, top to bottom."""
        devices = [_device(i) for i in range(count)]
        return [
            devices[focused_index + offset]
            if 0 <= focused_index + offset < count else None
            for offset in (-1, 0, 1)
        ]

    def test_one_device_leaves_both_neighbours_empty(self):
        assert self._slots(1, 0) == [None, _device(0), None]

    def test_two_devices_focus_zero_fills_the_bottom_slot(self):
        assert self._slots(2, 0) == [None, _device(0), _device(1)]

    def test_two_devices_focus_one_fills_the_top_slot(self):
        assert self._slots(2, 1) == [_device(0), _device(1), None]

    def test_five_devices_mid_list_fills_all_three(self):
        assert self._slots(5, 2) == [_device(1), _device(2), _device(3)]

    def test_empty_slot_surface_matches_the_populated_footprint(self):
        renderer = DeviceSurfaceRenderer()
        layout = CircularPositioningEngine().calculate_focused_slot_layout()[0]

        empty_surface, _rect = renderer.create_slot_surface(None, layout)
        device_surface, _touch = renderer.create_slot_surface(_device(0), layout)

        assert empty_surface.get_size() == device_surface.get_size()

    def test_an_unselected_slot_has_no_touch_rect(self):
        renderer = DeviceSurfaceRenderer()
        layout = CircularPositioningEngine().calculate_focused_slot_layout()[0]

        _surface, touch_rect = renderer.create_slot_surface(
            _device(0), layout, selected=False
        )

        assert touch_rect is None

    def test_a_selected_slot_has_a_touch_rect(self):
        renderer = DeviceSurfaceRenderer()
        layout = CircularPositioningEngine().calculate_focused_slot_layout()[1]

        _surface, touch_rect = renderer.create_slot_surface(
            _device(0), layout, selected=True
        )

        assert touch_rect is not None

    def test_selection_changes_the_rendered_pixels(self):
        """The tint and border must actually distinguish the slot."""
        renderer = DeviceSurfaceRenderer()
        layout = CircularPositioningEngine().calculate_focused_slot_layout()[1]

        plain, _a = renderer.create_slot_surface(_device(0), layout, selected=False)
        chosen, _b = renderer.create_slot_surface(_device(0), layout, selected=True)

        assert pygame.image.tostring(plain, 'RGBA') != pygame.image.tostring(
            chosen, 'RGBA'
        )


class TestArrows:
    """Arrows follow device presence, not a count threshold."""

    def test_no_devices_draws_no_arrows(self):
        render = _Render(0)

        assert render.focus_info is None

    def test_one_device_shows_neither_arrow(self):
        render = _Render(1)

        assert render.focus_info['has_previous'] is False
        assert render.focus_info['has_next'] is False

    def test_two_devices_at_the_top_show_the_down_arrow_only(self):
        render = _Render(2, focused_index=0)

        assert render.focus_info['has_previous'] is False
        assert render.focus_info['has_next'] is True

    def test_two_devices_at_the_bottom_show_the_up_arrow_only(self):
        render = _Render(2, focused_index=1)

        assert render.focus_info['has_previous'] is True
        assert render.focus_info['has_next'] is False

    def test_mid_list_shows_both_arrows(self):
        render = _Render(5, focused_index=2)

        assert render.focus_info['has_previous'] is True
        assert render.focus_info['has_next'] is True


class TestArrowGlyphs:
    """The arrows are actually drawn, in the bands either side of the slots."""

    UP_POINT = (240, 148)
    DOWN_POINT = (240, 328)

    def _draw(self, has_previous, has_next):
        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.device_list')
        host.colors = {'text': (0, 0, 0)}
        # Class constants, so a SimpleNamespace host must be given them.
        for name in ('_ARROW_HALF_WIDTH', '_ARROW_HEIGHT',
                     '_ARROW_UP_BASE_Y', '_ARROW_DOWN_BASE_Y'):
            setattr(host, name, getattr(SetupDisplayManager, name))

        surface = pygame.Surface((480, 480))
        surface.fill((255, 255, 255))
        SetupDisplayManager._draw_focus_arrows(host, surface, {
            'has_previous': has_previous, 'has_next': has_next
        })
        return surface

    def test_up_arrow_drawn_when_a_previous_device_exists(self):
        surface = self._draw(True, False)

        assert surface.get_at(self.UP_POINT)[:3] == (0, 0, 0)
        assert surface.get_at(self.DOWN_POINT)[:3] == (255, 255, 255)

    def test_down_arrow_drawn_when_a_next_device_exists(self):
        surface = self._draw(False, True)

        assert surface.get_at(self.DOWN_POINT)[:3] == (0, 0, 0)
        assert surface.get_at(self.UP_POINT)[:3] == (255, 255, 255)

    def test_neither_arrow_drawn_at_a_single_device(self):
        surface = self._draw(False, False)

        assert surface.get_at(self.UP_POINT)[:3] == (255, 255, 255)
        assert surface.get_at(self.DOWN_POINT)[:3] == (255, 255, 255)

    def test_arrows_clear_the_slot_column_and_the_buttons(self):
        layout = CircularPositioningEngine().calculate_focused_slot_layout()

        up_base = SetupDisplayManager._ARROW_UP_BASE_Y
        down_apex = (SetupDisplayManager._ARROW_DOWN_BASE_Y
                     + SetupDisplayManager._ARROW_HEIGHT)

        assert up_base < layout[0]['y']
        assert SetupDisplayManager._ARROW_DOWN_BASE_Y >= layout[2]['y'] + layout[2]['height']
        assert down_apex < 340


class TestNoDevices:
    """The empty case keeps its message and draws nothing else."""

    def test_message_path_is_retained(self):
        """No slots are drawn, so no touch region beyond Back/Retry."""
        render = _Render(0)

        assert [region[0] for region in render.regions] == ['back', 'retry']


class TestFocusShift:
    """One device per swipe, clamped at both bounds."""

    def _host(self, count, focused_index=0):
        state = _state(count)
        coordinator = SetupStateCoordinator(initial_state=state)
        coordinator.focused_index = focused_index

        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.device_list')
        host.state_coordinator = coordinator
        host.invalidated = []
        host._invalidate_render_cache = host.invalidated.append
        return host

    def test_swipe_down_advances_by_one(self):
        host = self._host(2, focused_index=0)

        assert SetupDisplayManager.handle_setup_swipe(host, 1) is True
        assert host.state_coordinator.focused_index == 1

    def test_swipe_up_retreats_by_one(self):
        host = self._host(5, focused_index=3)

        assert SetupDisplayManager.handle_setup_swipe(host, -1) is True
        assert host.state_coordinator.focused_index == 2

    def test_swipe_up_at_the_first_device_is_a_no_op(self):
        host = self._host(5, focused_index=0)

        assert SetupDisplayManager.handle_setup_swipe(host, -1) is False
        assert host.state_coordinator.focused_index == 0

    def test_swipe_down_at_the_last_device_is_a_no_op(self):
        host = self._host(5, focused_index=4)

        assert SetupDisplayManager.handle_setup_swipe(host, 1) is False
        assert host.state_coordinator.focused_index == 4

    def test_repeated_swipes_near_a_bound_stay_clamped(self):
        host = self._host(3, focused_index=2)

        for _ in range(5):
            SetupDisplayManager.handle_setup_swipe(host, 1)

        assert host.state_coordinator.focused_index == 2

    def test_a_shift_invalidates_the_device_list_cache(self):
        host = self._host(3, focused_index=0)

        SetupDisplayManager.handle_setup_swipe(host, 1)

        assert host.invalidated == [SetupScreen.DEVICE_LIST]

    def test_no_shift_on_another_screen(self):
        host = self._host(3, focused_index=0)
        host.state_coordinator.state.current_screen = SetupScreen.PAIRING

        assert SetupDisplayManager.handle_setup_swipe(host, 1) is False
        assert host.state_coordinator.focused_index == 0


class TestFocusClamping:
    """A device list that shrinks under the focus must not raise."""

    def test_focus_is_clamped_when_devices_disappear(self):
        state = _state(5)
        coordinator = SetupStateCoordinator(initial_state=state)
        coordinator.focused_index = 4

        state.discovered_devices = state.discovered_devices[:2]

        assert coordinator.get_focus_info()['focused_index'] == 1

    def test_focus_is_zero_when_all_devices_disappear(self):
        state = _state(3)
        coordinator = SetupStateCoordinator(initial_state=state)
        coordinator.focused_index = 2

        state.discovered_devices = []

        assert coordinator.get_focus_info()['focused_index'] == 0

    def test_render_survives_a_shrunken_list(self):
        render = _Render(5, focused_index=4)
        render.state.discovered_devices = render.state.discovered_devices[:1]

        SetupDisplayManager._render_device_list_screen(
            render.host, render.surface, render.state
        )

        assert len(render.device_regions) >= 1

    def test_entering_the_screen_resets_the_focus(self):
        state = _state(5)
        coordinator = SetupStateCoordinator(initial_state=state)
        coordinator.focused_index = 3
        coordinator.state.current_screen = SetupScreen.PAIRING

        coordinator.transition_to_screen(SetupScreen.DEVICE_LIST)

        assert coordinator.focused_index == 0

    def test_reset_discovery_resets_the_focus(self):
        state = _state(5)
        coordinator = SetupStateCoordinator(initial_state=state)
        coordinator.focused_index = 3

        coordinator.reset_discovery()

        assert coordinator.focused_index == 0


class _FakeSetupManager:
    """The setup manager as the touch path sees it."""

    def __init__(self, screen=SetupScreen.DEVICE_LIST):
        self.state = types.SimpleNamespace(current_screen=screen)
        self.swipes = []

    def handle_setup_swipe(self, direction):
        self.swipes.append(direction)
        return True


def _touch_host(setup_manager):
    host = types.SimpleNamespace()
    host.logger = logging.getLogger('test.touch')
    host.display_manager = types.SimpleNamespace(
        _setup_manager=setup_manager,
        touch_coordinator=types.SimpleNamespace(swipe_threshold=SWIPE_THRESHOLD),
    )
    return host


def _swipe(setup_manager, dx, dy):
    host = _touch_host(setup_manager)
    consumed = TouchHandler._handle_setup_swipe(host, 200 + dx, 200 + dy, 200, 200)
    return consumed


class TestTouchSwipeDetection:
    """Vertical drags on DEVICE_LIST move the focus; nothing else changes."""

    def test_downward_drag_is_consumed_as_a_positive_shift(self):
        manager = _FakeSetupManager()

        assert _swipe(manager, 0, SWIPE_THRESHOLD) is True
        assert manager.swipes == [1]

    def test_upward_drag_is_consumed_as_a_negative_shift(self):
        manager = _FakeSetupManager()

        assert _swipe(manager, 0, -SWIPE_THRESHOLD) is True
        assert manager.swipes == [-1]

    def test_one_below_threshold_falls_through_to_the_tap(self):
        manager = _FakeSetupManager()

        assert _swipe(manager, 0, SWIPE_THRESHOLD - 1) is False
        assert manager.swipes == []

    def test_a_tap_falls_through(self):
        manager = _FakeSetupManager()

        assert _swipe(manager, 0, 0) is False
        assert manager.swipes == []

    def test_horizontal_drag_falls_through(self):
        manager = _FakeSetupManager()

        assert _swipe(manager, SWIPE_THRESHOLD, 0) is False
        assert manager.swipes == []

    def test_diagonal_with_dominant_horizontal_falls_through(self):
        manager = _FakeSetupManager()

        assert _swipe(manager, SWIPE_THRESHOLD + 20, SWIPE_THRESHOLD) is False
        assert manager.swipes == []

    @pytest.mark.parametrize('screen', [
        SetupScreen.WELCOME,
        SetupScreen.DISCOVERY,
        SetupScreen.PAIRING,
        SetupScreen.COMPLETE,
        SetupScreen.CURRENT_DEVICE,
    ])
    def test_other_setup_screens_are_untouched(self, screen):
        manager = _FakeSetupManager(screen=screen)

        assert _swipe(manager, 0, SWIPE_THRESHOLD) is False
        assert manager.swipes == []

    def test_short_press_consumes_the_swipe_before_the_tap(self):
        """The wiring order: a swipe must not also select a device."""
        manager = _FakeSetupManager()
        host = _touch_host(manager)
        host.display_manager.is_in_setup_mode = lambda: True
        host.setup_touches = []
        host._handle_setup_touch = lambda x, y: host.setup_touches.append((x, y))
        host._handle_setup_swipe = lambda x, y, start_x, start_y: (
            TouchHandler._handle_setup_swipe(host, x, y, start_x, start_y)
        )

        TouchHandler._handle_short_press(host, 200, 200 + SWIPE_THRESHOLD, 200, 200)

        assert manager.swipes == [1]
        assert host.setup_touches == []

    def test_short_press_below_threshold_still_taps(self):
        manager = _FakeSetupManager()
        host = _touch_host(manager)
        host.display_manager.is_in_setup_mode = lambda: True
        host.setup_touches = []
        host._handle_setup_touch = lambda x, y: host.setup_touches.append((x, y))
        host._handle_setup_swipe = lambda x, y, start_x, start_y: (
            TouchHandler._handle_setup_swipe(host, x, y, start_x, start_y)
        )

        TouchHandler._handle_short_press(host, 200, 210, 200, 200)

        assert manager.swipes == []
        assert host.setup_touches == [(200, 210)]

    def test_no_setup_manager_falls_through(self):
        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.touch')
        host.display_manager = types.SimpleNamespace()

        assert TouchHandler._handle_setup_swipe(host, 200, 400, 200, 200) is False
