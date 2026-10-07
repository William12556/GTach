#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""No call-outs under a lock in the setup path.

Covers change-e9216e17 (audit-36b6ea95 D01, X01). The display thread
held _render_cache_lock while taking the coordinator's _state_lock and
_touch_regions_lock; the touch thread held _touch_regions_lock and
_state_lock while a transition callback took _render_cache_lock. The two
orders deadlocked. Every lock is now released before any callback, touch
action or foreign-lock call.

SetupDisplayManager is built with object.__new__ and only the attributes
the methods under test read, so no Bluetooth interface, async worker or
setup thread is created.
"""

import logging
import threading
import types

import pygame
import pytest

import gtach.comm.device_store as device_store_module
from gtach.display.setup import SetupDisplayManager
from gtach.display.setup_components.state.coordinator import SetupStateCoordinator
from gtach.display.setup_models import SetupScreen

JOIN_TIMEOUT = 10.0


@pytest.fixture(autouse=True, scope="module")
def _pygame_ready():
    """Off-screen surfaces only; see tests/test_device_list_focus.py."""
    pygame.init()


@pytest.fixture
def no_device_store(monkeypatch):
    """Keep the cached-WELCOME path off the repository's devices.yaml."""
    stub = types.SimpleNamespace(get_primary_device=lambda: None)
    monkeypatch.setattr(device_store_module, "DeviceStore", lambda *a, **k: stub)


def _held(lock) -> bool:
    """True if lock is currently free; releases it again if acquired."""
    acquired = lock.acquire(blocking=False)
    if acquired:
        lock.release()
    return acquired


def _manager(coordinator=None) -> SetupDisplayManager:
    """A SetupDisplayManager with only the state render/touch use."""
    manager = object.__new__(SetupDisplayManager)
    manager.logger = logging.getLogger("test.setup_lock_order")
    manager.display_available = True
    manager.surface = pygame.Surface((480, 480))
    manager.state_coordinator = coordinator or SetupStateCoordinator()
    manager.touch_regions = []
    manager._touch_regions_lock = threading.Lock()
    manager._screen_render_cache = {}
    manager._last_rendered_screen = None
    manager._screen_needs_refresh = True
    manager._render_cache_lock = threading.Lock()
    manager._has_device = False  # cached presence (issue-674bec49)
    manager.colors = {"background": (216, 200, 146), "text": (0, 0, 0)}
    return manager


class TestCoordinatorNotifiesOutsideTheLock:
    """Callbacks run after _state_lock is released, and only on change."""

    def test_transition_callback_runs_unlocked(self):
        coordinator = SetupStateCoordinator()
        calls = []
        coordinator.register_screen_transition_callback(
            lambda old, new: calls.append((_held(coordinator._state_lock), old, new))
        )

        coordinator.transition_to_screen(SetupScreen.DISCOVERY)

        assert calls == [(True, SetupScreen.WELCOME, SetupScreen.DISCOVERY)]

    def test_state_change_callback_runs_unlocked(self):
        coordinator = SetupStateCoordinator()
        calls = []
        coordinator.register_state_change_callback(
            lambda fields: calls.append((_held(coordinator._state_lock), fields))
        )

        coordinator.update_state(error_message="x")

        assert calls == [(True, ["error_message"])]

    def test_no_callback_when_nothing_changes(self):
        coordinator = SetupStateCoordinator()
        calls = []
        coordinator.register_screen_transition_callback(
            lambda old, new: calls.append("transition")
        )
        coordinator.register_state_change_callback(lambda fields: calls.append("state"))

        coordinator.transition_to_screen(SetupScreen.WELCOME)
        coordinator.update_state(error_message=None)

        assert calls == []

    def test_callback_may_call_get_state(self):
        """Under the non-reentrant lock this self-deadlocked."""
        coordinator = SetupStateCoordinator()
        seen = []
        coordinator.register_screen_transition_callback(
            lambda old, new: seen.append(coordinator.get_state().current_screen)
        )

        worker = threading.Thread(
            target=coordinator.transition_to_screen,
            args=(SetupScreen.DISCOVERY,),
            daemon=True,
        )
        worker.start()
        worker.join(timeout=JOIN_TIMEOUT)

        assert not worker.is_alive()
        assert seen == [SetupScreen.DISCOVERY]


class TestTouchDispatchOutsideTheLock:

    def test_action_runs_with_touch_regions_lock_free(self, monkeypatch):
        manager = _manager()
        region = ("start", pygame.Rect(0, 0, 10, 10))
        manager.touch_regions = [region]
        calls = []
        monkeypatch.setattr(
            manager,
            "_handle_touch_action",
            lambda action, hit: calls.append(
                (_held(manager._touch_regions_lock), action, hit)
            ),
            raising=False,
        )

        manager.handle_touch_event((5, 5))

        assert calls == [(True, "start", region)]


class TestRenderCacheLockScope:

    def test_cached_regions_updated_with_render_cache_lock_free(self, monkeypatch):
        manager = _manager()
        manager._screen_render_cache[SetupScreen.WELCOME] = pygame.Surface((480, 480))
        manager._screen_needs_refresh = False
        calls = []
        monkeypatch.setattr(
            manager,
            "_update_cached_screen_touch_regions",
            lambda: calls.append(_held(manager._render_cache_lock)),
            raising=False,
        )

        manager.render(pygame.Surface((480, 480)))

        assert calls == [True]


class TestNoDeadlockUnderLoad:
    """The D01 interleaving, driven hard from two threads."""

    def test_render_and_touch_threads_both_finish(self, no_device_store, monkeypatch):
        coordinator = SetupStateCoordinator()
        manager = _manager(coordinator)
        coordinator.register_screen_transition_callback(manager._on_screen_transition)
        coordinator.register_state_change_callback(manager._on_state_change)

        # A full render stores a cacheable screen and its regions; the
        # region covers the whole panel so every tap hits it.
        def _render_screen(surface, state):
            manager._update_touch_regions_safe(
                [("cancel", pygame.Rect(0, 0, 480, 480))]
            )

        monkeypatch.setattr(manager, "_render_screen", _render_screen, raising=False)

        screens = [SetupScreen.CURRENT_DEVICE, SetupScreen.WELCOME]

        def _route(action, region):
            screens.reverse()
            coordinator.transition_to_screen(screens[0])

        monkeypatch.setattr(manager, "_handle_touch_action", _route, raising=False)

        target = pygame.Surface((480, 480))
        manager.render(target)  # populate the WELCOME cache
        errors = []

        def _render_loop():
            try:
                for _ in range(500):
                    manager.render(target)
            except Exception as exc:  # pragma: no cover - failure path
                errors.append(exc)

        def _touch_loop():
            try:
                for _ in range(500):
                    manager.handle_touch_event((200, 350))
            except Exception as exc:  # pragma: no cover - failure path
                errors.append(exc)

        threads = [
            threading.Thread(target=_render_loop, daemon=True),
            threading.Thread(target=_touch_loop, daemon=True),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=JOIN_TIMEOUT)

        assert all(not thread.is_alive() for thread in threads), "deadlock"
        assert errors == []
