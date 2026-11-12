#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Engine off display state (change-b29cbd71).

EDIT A: OBDProtocol records silent-vehicle evidence from 0100 replies and
re-checks the vehicle with 0100 alone after silence during polling.
EDIT B: DisplayManager shows Engine off only with the transport connected
and fresh evidence; every failure falls back to DISCONNECTED.
"""

import logging
import queue
import threading
import time
import types
from typing import Any, Callable, List, Optional

import pygame
import pytest

import gtach.display.manager as manager_module
import gtach.display.touch_interface as touch_interface_module
from gtach.comm.obd import OBDProtocol
from gtach.core import ThreadManager
from gtach.display.manager import DisplayManager
from gtach.display.models import ConnectionStatus, DisplayMode
from gtach.display.typography import TypographyConstants, get_font_manager

VALID_4100 = "4100BE3EA813"
VALID_010C = "410C1AF8"
WAIT_S = 10.0

# ---------------------------------------------------------------- EDIT A


class _ScriptTransport:
    """A transport whose replies come from per-command functions.

    Args:
        replies: Command to a function returning that command's reply.
            Commands not listed answer 'OK'.
    """

    def __init__(self, replies: dict) -> None:
        self.connected = True
        self.replies = replies
        self.sent: List[str] = []
        self.lock = threading.Lock()

    def is_connected(self) -> bool:
        return self.connected

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        with self.lock:
            self.sent.append(command)
        reply = self.replies.get(command)
        if reply is None:
            return "OK"
        result: Optional[str] = reply()
        return result

    def sent_copy(self) -> List[str]:
        with self.lock:
            return list(self.sent)


def _thread_manager() -> Any:
    return types.SimpleNamespace(
        register_thread=lambda *a, **k: None,
        update_heartbeat=lambda name: None,
        message_queue=queue.Queue(maxsize=10),
        data_available=threading.Event(),
    )


def _protocol(transport: _ScriptTransport, **kwargs: Any) -> OBDProtocol:
    return OBDProtocol(transport, _thread_manager(), **kwargs)  # type: ignore[arg-type]


def _wait_until(predicate: Callable[[], bool], timeout: float = WAIT_S) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def _const(value: Optional[str]) -> Callable[[], Optional[str]]:
    return lambda: value


@pytest.fixture
def fast_protocol(monkeypatch):
    """Short re-check and retry intervals for the threaded loop tests."""
    monkeypatch.setattr(OBDProtocol, "_RPM_SILENT_RECHECK_S", 0.2)
    monkeypatch.setattr(OBDProtocol, "_INIT_RETRY_DELAY_S", 0.05)


def _run(protocol: OBDProtocol) -> threading.Thread:
    thread = threading.Thread(target=protocol._protocol_loop, daemon=True)
    thread.start()
    return thread


def _stop(protocol: OBDProtocol, thread: threading.Thread) -> None:
    protocol.shutdown_event.set()
    thread.join(timeout=WAIT_S)
    assert not thread.is_alive()


class TestInitialisationEvidence:
    def test_no_data_sets_timestamp(self):
        protocol = _protocol(_ScriptTransport({"0100": _const("NO DATA")}))

        assert protocol._initialize_protocol() is False
        assert isinstance(protocol.last_vehicle_silent_ts(), float)

    @pytest.mark.parametrize(
        "reply",
        ["SEARCHING...UNABLE TO CONNECT", "BUS INIT: ...ERROR", "?"],
    )
    def test_adapter_replies_set_timestamp(self, reply):
        protocol = _protocol(_ScriptTransport({"0100": _const(reply)}))

        assert protocol._initialize_protocol() is False
        assert isinstance(protocol.last_vehicle_silent_ts(), float)

    def test_none_with_link_up_leaves_timestamp(self, caplog):
        protocol = _protocol(_ScriptTransport({"0100": _const(None)}))

        with caplog.at_level(logging.WARNING, logger="OBDProtocol"):
            assert protocol._initialize_protocol() is False

        assert protocol.last_vehicle_silent_ts() is None
        assert any("Vehicle not answering" in r.getMessage() for r in caplog.records)

    def test_none_with_link_up_does_not_refresh_timestamp(self):
        protocol = _protocol(_ScriptTransport({"0100": _const(None)}))
        protocol._vehicle_silent_ts = 123.0

        assert protocol._initialize_protocol() is False
        assert protocol.last_vehicle_silent_ts() == 123.0

    def test_none_with_link_down_clears_timestamp(self, caplog):
        transport = _ScriptTransport({})

        def drop() -> Optional[str]:
            transport.connected = False
            return "OK"

        transport.replies["ATSP0"] = drop
        protocol = _protocol(transport)
        protocol._vehicle_silent_ts = 123.0

        with caplog.at_level(logging.DEBUG, logger="OBDProtocol"):
            assert protocol._initialize_protocol() is False

        assert protocol.last_vehicle_silent_ts() is None
        assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert protocol._vehicle_silent is False
        assert "0100" not in transport.sent

    def test_4100_after_silent_reply_clears_timestamp(self):
        replies = iter(["NO DATA", VALID_4100])
        protocol = _protocol(_ScriptTransport({"0100": lambda: next(replies)}))

        assert protocol._initialize_protocol() is False
        assert protocol.last_vehicle_silent_ts() is not None
        assert protocol._initialize_protocol() is True
        assert protocol.last_vehicle_silent_ts() is None

    def test_signal_stop_clears_timestamp(self):
        protocol = _protocol(_ScriptTransport({}))
        protocol._vehicle_silent_ts = 123.0

        protocol._signal_stop()

        assert protocol.last_vehicle_silent_ts() is None


class TestSilenceDuringPolling:
    def test_recheck_sends_0100_only(self, fast_protocol, caplog):
        state = {"phase": "init"}

        def reply_0100() -> str:
            return VALID_4100 if state["phase"] == "init" else "NO DATA"

        def reply_010c() -> str:
            state["phase"] = "polling"
            return "NO DATA"

        transport = _ScriptTransport({"0100": reply_0100, "010C": reply_010c})
        protocol = _protocol(transport, poll_interval_s=0.01)

        with caplog.at_level(logging.INFO, logger="OBDProtocol"):
            thread = _run(protocol)
            assert _wait_until(lambda: protocol.last_vehicle_silent_ts() is not None)
            initialised = protocol._adapter_initialised
            _stop(protocol, thread)

        sent = transport.sent_copy()
        first_010c = sent.index("010C")
        after = sent[first_010c:]
        assert "0100" in after
        assert not [c for c in after if c.startswith("AT")]
        assert initialised is True
        rechecks = [
            r for r in caplog.records if "re-checking vehicle" in r.getMessage()
        ]
        assert len(rechecks) == 1
        assert rechecks[0].levelno == logging.INFO

    def test_recheck_4100_resumes_polling(self, fast_protocol, caplog):
        state = {"polls": 0, "rechecks": 0}

        def reply_0100() -> str:
            if state["polls"] == 0:
                return VALID_4100
            state["rechecks"] += 1
            return "NO DATA" if state["rechecks"] == 1 else VALID_4100

        def reply_010c() -> str:
            state["polls"] += 1
            return "NO DATA"

        transport = _ScriptTransport({"0100": reply_0100, "010C": reply_010c})
        protocol = _protocol(transport, poll_interval_s=0.01)

        with caplog.at_level(logging.INFO, logger="OBDProtocol"):
            thread = _run(protocol)
            assert _wait_until(lambda: state["rechecks"] >= 2)
            polls_at_resume = state["polls"]
            assert _wait_until(lambda: state["polls"] > polls_at_resume)
            ts = protocol.last_vehicle_silent_ts()
            _stop(protocol, thread)

        assert ts is None
        assert any(
            "Vehicle answered 0100 - polling resumed" in r.getMessage()
            for r in caplog.records
        )
        assert transport.sent_copy().count("ATZ") == 1

    def test_timeouts_never_set_timestamp(self, fast_protocol):
        state = {"polled": False, "rechecks": 0}

        def reply_0100() -> Optional[str]:
            if not state["polled"]:
                return VALID_4100
            state["rechecks"] += 1
            return None

        def reply_010c() -> Optional[str]:
            state["polled"] = True
            return None

        transport = _ScriptTransport({"0100": reply_0100, "010C": reply_010c})
        protocol = _protocol(transport, poll_interval_s=0.01)

        thread = _run(protocol)
        seen: List[Optional[float]] = []
        assert _wait_until(
            lambda: seen.append(protocol.last_vehicle_silent_ts())
            or state["rechecks"] >= 3
        )
        _stop(protocol, thread)

        assert all(ts is None for ts in seen)

    def test_valid_sample_clears_timestamp(self, fast_protocol):
        state = {"valid": False}

        def reply_0100() -> str:
            return VALID_4100

        def reply_010c() -> str:
            return VALID_010C if state["valid"] else "NO DATA"

        transport = _ScriptTransport({"0100": reply_0100, "010C": reply_010c})
        protocol = _protocol(transport, poll_interval_s=0.01)
        protocol._vehicle_silent_ts = time.monotonic()

        thread = _run(protocol)
        assert _wait_until(lambda: "010C" in transport.sent_copy())
        state["valid"] = True
        assert _wait_until(lambda: protocol.last_vehicle_silent_ts() is None)
        _stop(protocol, thread)

    def test_disconnect_during_recheck_wait(self, monkeypatch):
        monkeypatch.setattr(OBDProtocol, "_RPM_SILENT_RECHECK_S", 0.1)
        monkeypatch.setattr(OBDProtocol, "_INIT_RETRY_DELAY_S", 0.3)
        state = {"polled": False, "rechecks": 0}

        def reply_0100() -> str:
            if not state["polled"]:
                return VALID_4100
            state["rechecks"] += 1
            return "NO DATA"

        def reply_010c() -> str:
            state["polled"] = True
            return "NO DATA"

        transport = _ScriptTransport({"0100": reply_0100, "010C": reply_010c})
        protocol = _protocol(transport, poll_interval_s=0.01)

        thread = _run(protocol)
        assert _wait_until(lambda: state["rechecks"] >= 1)
        transport.connected = False
        assert _wait_until(lambda: protocol.last_vehicle_silent_ts() is None)
        rechecks = state["rechecks"]
        time.sleep(0.5)
        _stop(protocol, thread)

        assert state["rechecks"] == rechecks

    def test_stop_during_recheck_wait(self, monkeypatch):
        monkeypatch.setattr(OBDProtocol, "_RPM_SILENT_RECHECK_S", 0.1)
        monkeypatch.setattr(OBDProtocol, "_INIT_RETRY_DELAY_S", 30.0)
        state = {"polled": False, "rechecks": 0}

        def reply_0100() -> str:
            if not state["polled"]:
                return VALID_4100
            state["rechecks"] += 1
            return "NO DATA"

        def reply_010c() -> str:
            state["polled"] = True
            return "NO DATA"

        transport = _ScriptTransport({"0100": reply_0100, "010C": reply_010c})
        protocol = _protocol(transport, poll_interval_s=0.01)

        thread = _run(protocol)
        assert _wait_until(lambda: state["rechecks"] >= 1)
        started = time.monotonic()
        protocol._signal_stop()
        thread.join(timeout=WAIT_S)

        assert not thread.is_alive()
        assert time.monotonic() - started < 2.0
        assert protocol.last_vehicle_silent_ts() is None

    def test_mid_drive_gap(self, capsys):
        """Ignition off mid-drive, with the production intervals."""
        state = {"valid_until": time.monotonic() + 0.5, "last_valid": 0.0}

        def reply_010c() -> str:
            now = time.monotonic()
            if now < state["valid_until"]:
                state["last_valid"] = now
                return VALID_010C
            return "NO DATA"

        def reply_0100() -> str:
            if time.monotonic() < state["valid_until"]:
                return VALID_4100
            return "NO DATA"

        transport = _ScriptTransport({"0100": reply_0100, "010C": reply_010c})
        protocol = _protocol(transport)

        thread = _run(protocol)
        assert _wait_until(lambda: protocol.last_vehicle_silent_ts() is not None)
        ts = protocol.last_vehicle_silent_ts()
        _stop(protocol, thread)

        assert ts is not None
        gap = ts - state["last_valid"]
        with capsys.disabled():
            print(f"\nmid-drive gap, last sample to silent timestamp: {gap:.3f} s")
        assert OBDProtocol._RPM_SILENT_RECHECK_S <= gap < 3.0


# ---------------------------------------------------------------- EDIT B


def _raise_runtime_error(*args: Any, **kwargs: Any) -> None:
    raise RuntimeError("injected fault")


@pytest.fixture
def manager(monkeypatch):
    """A RADIAL DisplayManager whose touch interface fails to initialise."""
    monkeypatch.setattr(
        touch_interface_module, "create_touch_interface", _raise_runtime_error
    )
    dm = DisplayManager(ThreadManager())
    dm.config.mode = DisplayMode.RADIAL
    dm._link_connected_callback = lambda: True
    dm._vehicle_silent_callback = lambda: time.monotonic() - 1.0
    return dm


def _run_one_frame(dm: DisplayManager) -> None:
    """Run exactly one iteration of the display loop."""
    dm.thread_manager.update_heartbeat = (  # type: ignore[method-assign]
        lambda name: dm._shutdown_event.set()
    )
    dm._shutdown_event.clear()
    dm._display_loop()


@pytest.fixture
def drawn(manager, monkeypatch):
    """Record every text and status colour drawn by the manager."""
    record: dict = {"text": [], "circles": []}
    engine = manager.rendering_engine
    render_text = engine.render_text
    draw_circle = engine.draw_circle

    def recording_text(target, text, *args, **kwargs):
        record["text"].append(text)
        return render_text(target, text, *args, **kwargs)

    def recording_circle(target, colour, *args, **kwargs):
        record["circles"].append(tuple(colour))
        return draw_circle(target, colour, *args, **kwargs)

    monkeypatch.setattr(engine, "render_text", recording_text)
    monkeypatch.setattr(engine, "draw_circle", recording_circle)
    disconnected: List[int] = []
    monkeypatch.setattr(manager, "_render_disconnected", lambda: disconnected.append(1))
    record["disconnected"] = disconnected
    return record


def _is_readout(text: str) -> bool:
    """Whether text is the RPM readout ('4.5'); tick labels have no point."""
    whole, point, frac = text.partition(".")
    return bool(point) and whole.isdigit() and frac.isdigit()


def _colour(status: ConnectionStatus) -> tuple:
    c = pygame.Color(status.value)
    return (c.r, c.g, c.b)


class TestEngineOffCondition:
    def test_fresh_evidence_shows_engine_off(self, manager, drawn):
        _run_one_frame(manager)

        assert manager._frame_engine_off is True
        assert drawn["disconnected"] == []
        assert DisplayManager.ENGINE_OFF_TEXT in drawn["text"]
        assert not [t for t in drawn["text"] if _is_readout(t)]
        assert _colour(ConnectionStatus.CONNECTING) in drawn["circles"]

    def test_stale_evidence_is_disconnected(self, manager, drawn):
        manager._vehicle_silent_callback = lambda: time.monotonic() - 16.0

        _run_one_frame(manager)

        assert manager._frame_engine_off is False
        assert drawn["disconnected"] == [1]

    def test_exactly_freshness_old_counts(self, manager, monkeypatch):
        now = 1000.0
        monkeypatch.setattr(manager_module.time, "monotonic", lambda: now)
        manager._vehicle_silent_callback = (
            lambda: now - DisplayManager.ENGINE_OFF_FRESHNESS_S
        )
        manager._frame_link_lost = True

        assert manager._engine_off() is True

    @pytest.mark.parametrize(
        "link",
        [lambda: False, lambda: None, _raise_runtime_error, None],
        ids=["false", "none", "raising", "absent"],
    )
    def test_transport_not_connected(self, manager, link):
        manager._link_connected_callback = link
        manager._frame_link_lost = True

        assert manager._engine_off() is False

    @pytest.mark.parametrize(
        "silent",
        [lambda: None, _raise_runtime_error, None, lambda: "1.0"],
        ids=["none", "raising", "absent", "not-float"],
    )
    def test_no_evidence(self, manager, silent):
        manager._vehicle_silent_callback = silent
        manager._frame_link_lost = True

        assert manager._engine_off() is False

    def test_simulation_mode(self, manager):
        manager._sim_mode = True

        _run_one_frame(manager)

        assert manager._frame_engine_off is False

    def test_link_up_shows_live_gauge(self, manager, drawn):
        manager._last_sample_ts = time.monotonic()
        manager._link_ok = True
        manager._last_rpm = 3000

        _run_one_frame(manager)

        assert manager._frame_engine_off is False
        assert DisplayManager.ENGINE_OFF_TEXT not in drawn["text"]
        assert any(_is_readout(t) for t in drawn["text"])

    def test_entry_resets_conditioning(self, manager, caplog):
        manager._last_rpm = 4500
        manager._rpm_display = 4500.0
        manager._rpm_last_ts = time.monotonic()
        manager._active_band = 3

        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)
            _run_one_frame(manager)

        assert manager._last_rpm == 0
        assert manager._rpm_display == 0.0
        assert manager._rpm_last_ts is None
        assert manager._active_band == 0
        entries = [
            r
            for r in caplog.records
            if r.getMessage() == "Engine off - adapter reports no vehicle"
        ]
        assert len(entries) == 1
        assert entries[0].levelno == logging.INFO

    def test_exit_logged(self, manager, caplog):
        _run_one_frame(manager)
        manager._vehicle_silent_callback = lambda: None

        with caplog.at_level(logging.INFO, logger="DisplayManager"):
            _run_one_frame(manager)

        assert any(r.getMessage() == "Engine off cleared" for r in caplog.records)

    def test_view_key_and_regions(self, manager):
        manager._vehicle_silent_callback = lambda: None
        _run_one_frame(manager)
        disconnected_key = manager._current_view_key()
        assert manager._disconnected_btn_setup is not None
        assert manager.touch_coordinator._regions

        manager._vehicle_silent_callback = lambda: time.monotonic() - 1.0
        _run_one_frame(manager)

        assert manager._frame_engine_off is True
        assert manager._current_view_key() != disconnected_key
        assert not manager.touch_coordinator._regions


def test_engine_off_text_fits():
    pygame.font.init()
    font = get_font_manager().get_font(TypographyConstants.FONT_RPM_MEDIUM)
    width = font.size(DisplayManager.ENGINE_OFF_TEXT)[0]
    print(f"\nENGINE_OFF_TEXT width: {width} px")
    assert width <= 180
