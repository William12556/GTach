#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Task register fixes B and F (issue-76ef5387).

B: the simulated devices are classified, so a simbt scan shows the
normal device list without the fallback notice. F: a pairing that
returns False is logged at WARNING; only an exception is an ERROR.
"""

import logging

import pygame
import pytest
from test_setup_flow import _device, _Env, _op

from gtach.comm.sim_bluetooth import _FAKE_DEVICES, SimBluetoothPairing
from gtach.display.async_operations import OperationStatus, OperationType
from gtach.display.setup_models import DeviceType, PairingStatus, SetupScreen


@pytest.fixture(autouse=True, scope="module")
def _pygame_ready():
    """Off-screen surfaces and fonts, as in tests/test_setup_flow.py."""
    pygame.init()


@pytest.fixture
def env(monkeypatch) -> _Env:
    return _Env(monkeypatch)


class TestSimulatedDevicesAreClassified:
    """EDIT B."""

    def test_no_fake_device_is_unknown(self):
        assert _FAKE_DEVICES
        for device in _FAKE_DEVICES:
            assert device.device_classification is not DeviceType.UNKNOWN

    def test_classification_matches_device_type(self):
        expected = {
            "ELM327": DeviceType.HIGHLY_LIKELY_ELM327,
            "Compatible": DeviceType.POSSIBLY_COMPATIBLE,
        }
        for device in _FAKE_DEVICES:
            assert device.device_classification is expected[device.device_type]

    def test_simbt_scan_sets_no_error_line(self, env, monkeypatch):
        sim = SimBluetoothPairing()
        monkeypatch.setattr("gtach.comm.sim_bluetooth.time.sleep", lambda s: None)
        devices = sim.discover_elm327_devices()

        env.tap("start")
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=devices),
        )

        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert len(state.discovered_devices) == len(_FAKE_DEVICES)
        assert state.error_message is None


class TestPairingFailureLogLevel:
    """EDIT F."""

    def _on_pairing(self, env) -> None:
        env.tap("start")
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=[_device(1)]),
        )
        env.tap("device", _device(1))
        assert env.state.current_screen == SetupScreen.PAIRING

    def test_pairing_returning_false_is_a_warning(self, env, caplog):
        self._on_pairing(env)

        with caplog.at_level(logging.DEBUG):
            env.complete(
                OperationType.DEVICE_PAIRING,
                _op(OperationStatus.COMPLETED, result=False),
            )

        assert env.state.pairing_status == PairingStatus.FAILED
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert any(
            r.levelno == logging.WARNING
            and "Failed to pair with device" in r.getMessage()
            for r in caplog.records
        )

    def test_pairing_exception_stays_an_error(self, env, caplog):
        self._on_pairing(env)

        with caplog.at_level(logging.DEBUG):
            env.complete(
                OperationType.DEVICE_PAIRING,
                _op(OperationStatus.FAILED, error=RuntimeError("boom")),
            )

        assert any(
            r.levelno == logging.ERROR and "Pairing operation failed" in r.getMessage()
            for r in caplog.records
        )
