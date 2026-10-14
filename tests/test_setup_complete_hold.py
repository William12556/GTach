#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""'Setup Complete!' is held before normal mode takes over.

Without a hold the screen was replaced within one 0.05 s loop cycle
and could not be read (observed 2026-10-09 during test-d26ca557
TC-002; trivial exemption P04.12). A fake clock drives the loop, so
the tests take no real time.
"""

import logging
import threading
import types
from typing import List

# Not aliased as 'setup_module': pytest treats a module-level name
# 'setup_module' as its xunit setup hook and tries to call it.
from gtach.display import setup as setup_mod
from gtach.display.setup import SetupDisplayManager
from gtach.display.setup_models import SetupScreen


def _manager(on_complete):
    """A SetupDisplayManager with only what _setup_loop reads."""
    manager = SetupDisplayManager.__new__(SetupDisplayManager)
    manager.logger = logging.getLogger("test.setup")
    manager._shutdown_event = threading.Event()
    manager._on_complete = on_complete
    manager.heartbeats = 0

    def _beat(_name):
        manager.heartbeats += 1

    manager.thread_manager = types.SimpleNamespace(update_heartbeat=_beat)
    state = types.SimpleNamespace(current_screen=SetupScreen.COMPLETE)
    manager.state_coordinator = types.SimpleNamespace(
        update_animation=lambda dt: None, get_state=lambda: state
    )
    return manager


def _fake_clock(monkeypatch, on_sleep=None):
    """Replace time.monotonic and time.sleep with a manual clock."""
    now = [100.0]

    def _sleep(seconds):
        now[0] += seconds
        if on_sleep is not None:
            on_sleep()

    monkeypatch.setattr(setup_mod.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(setup_mod.time, "sleep", _sleep)
    return now


def test_on_complete_waits_for_the_hold(monkeypatch):
    called_at: List[float] = []
    now = _fake_clock(monkeypatch)
    manager = _manager(lambda: called_at.append(now[0]))

    manager._setup_loop()

    assert len(called_at) == 1
    assert called_at[0] - 100.0 >= SetupDisplayManager._COMPLETE_HOLD_S
    # The loop keeps cycling during the hold, so the heartbeat continues.
    assert manager.heartbeats > 1


def test_shutdown_during_hold_skips_on_complete(monkeypatch):
    called: List[bool] = []
    manager = _manager(lambda: called.append(True))
    _fake_clock(monkeypatch, on_sleep=manager._shutdown_event.set)

    manager._setup_loop()

    assert called == []


def test_hold_constant():
    assert SetupDisplayManager._COMPLETE_HOLD_S == 2.0
