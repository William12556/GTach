#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Low-severity corrections.

Covers change-4005360c (audit-36b6ea95 A12, A13, A16, A18, B07, B09,
B10, B12, C10, C13, C15, C16, D08, D11): one focused test per item whose
behaviour changes.
"""

import datetime
import logging
import socket
import threading
import types

import pygame
import pytest
import yaml

import gtach.comm.sim_bluetooth as sim_bluetooth_module
import gtach.comm.transport as transport_module
from gtach.app import GTachApplication
from gtach.comm.rfcomm import RFCOMMTransport
from gtach.comm.sim_bluetooth import SimBluetoothPairing
from gtach.comm.tcp_transport import TCPTransport
from gtach.display.rendering.engine import DisplayRenderingEngine
from gtach.display.setup_components.layout.circular_positioning import (
    CircularPositioningEngine,
)
from gtach.display.setup_components.rendering.device_surfaces import (
    DeviceSurfaceRenderer,
)
from gtach.display.setup_models import BluetoothDevice
from gtach.display.splash import SplashScreen
from gtach.display.typography import (
    TypographyConstants,
    get_font_manager,
    get_rpm_large_font,
)
from gtach.utils.config import ConfigStore

JOIN_TIMEOUT = 5.0


@pytest.fixture(autouse=True, scope="module")
def _pygame_ready():
    """Off-screen surfaces and fonts; see tests/test_device_list_focus.py."""
    pygame.init()


class TestTcpOpenClosesOnFailure:  # A12

    def test_close_and_reraise(self, monkeypatch):
        closed = []

        class _Sock:
            def settimeout(self, value):
                pass

            def connect(self, address):
                raise ConnectionRefusedError("refused")

            def close(self):
                closed.append(True)

        monkeypatch.setattr(socket, "socket", lambda *a: _Sock())

        with pytest.raises(ConnectionRefusedError):
            TCPTransport("localhost", 1)._open()
        assert closed == [True]


class TestSimPairingCancelIsPerRun:  # A13

    def test_discovery_after_cancel(self, monkeypatch):
        monkeypatch.setattr(sim_bluetooth_module.time, "sleep", lambda s: None)
        pairing = SimBluetoothPairing()
        pairing.cancel_discovery()
        found = []

        devices = pairing.discover_elm327_devices(device_found_callback=found.append)

        assert devices
        assert found


class TestTransportExceptionNames:  # A16

    def test_no_builtin_shadowing(self):
        assert "ConnectionError" not in vars(transport_module)
        assert "TimeoutError" not in vars(transport_module)
        assert issubclass(
            transport_module.TransportConnectionError, transport_module.TransportError
        )
        assert issubclass(
            transport_module.TransportTimeoutError, transport_module.TransportError
        )


class TestRetryDelay:  # B09

    def test_configured_value(self):
        assert RFCOMMTransport("00:11:22:33:44:55", retry_delay=7.0).retry_delay == 7.0


class TestObdStartedOnce:  # B12

    def test_two_threads(self):
        app = object.__new__(GTachApplication)
        app.logger = logging.getLogger("test.low")
        app._obd_lock = threading.Lock()
        started = []
        barrier = threading.Barrier(2)
        app._display = types.SimpleNamespace(exit_setup_mode=lambda: None)

        def start_obd():
            started.append(1)

        app._start_obd = start_obd

        def worker():
            barrier.wait(JOIN_TIMEOUT)
            app._on_setup_complete()

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(JOIN_TIMEOUT)

        assert started == [1]


class TestConfigRanges:  # C10

    def test_out_of_range_values_use_defaults(self, tmp_path, caplog):
        path = tmp_path / "config.yaml"
        path.write_text(yaml.safe_dump({"fps_limit": 0, "touch_long_press": 9}))

        with caplog.at_level(logging.WARNING):
            config = ConfigStore(path).load()

        assert config.fps_limit == 30
        assert config.touch_long_press == 1.0
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "fps_limit" in messages and "touch_long_press" in messages


class TestSplashZeroDuration:  # C13

    def test_progress_complete(self):
        splash = SplashScreen((480, 480), duration=0)
        splash.start()

        assert splash.get_progress() == 1.0
        assert splash._render_text_fallback() is True


class TestRpmFontNotShared:  # C15

    def test_base_font_stays_plain(self):
        bold = get_rpm_large_font()
        assert get_rpm_large_font() is bold
        base = get_font_manager().get_font(TypographyConstants.FONT_RPM_LARGE)

        assert bold is not base
        assert bold.get_bold()
        assert base.get_bold() == TypographyConstants.FONT_BOLD


class TestSignalStrength:  # D08

    def test_uses_signal_strength(self, monkeypatch):
        renderer = DeviceSurfaceRenderer()
        renderer.display_available = True
        seen = []
        real = renderer.get_signal_bars
        monkeypatch.setattr(
            renderer,
            "get_signal_bars",
            lambda value: (seen.append(value), real(value))[1],
        )
        device = BluetoothDevice(
            name="OBD",
            mac_address="00:11:22:33:44:55",
            signal_strength=-60,
            device_type="ELM327",
            last_seen=datetime.datetime(2026, 10, 7),
        )

        layout = CircularPositioningEngine().calculate_focused_slot_layout()
        renderer.create_slot_surface(device, layout[1])

        assert seen == [-60]


class TestEngineCleanup:  # D11

    def test_handles_reset(self):
        engine = DisplayRenderingEngine()
        engine.pygame_available = False  # do not quit pygame under other tests
        engine.fb = types.SimpleNamespace(close=lambda: None)
        engine.fb_dev = types.SimpleNamespace(close=lambda: None, fileno=lambda: -1)
        engine._original_var = None

        engine.cleanup()

        assert engine.fb is None
        assert engine.fb_dev is None
