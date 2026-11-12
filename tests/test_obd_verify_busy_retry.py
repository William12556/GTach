#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Bounded retry in the post-pairing OBD verify (issue-d26ca557, issue-146491ba).

The RFCOMM connect issued milliseconds after pairing can fail with
EBUSY or ECONNRESET. verify_obd_connection retries those two causes,
and only those, a bounded number of times.
"""

import errno
import logging
import socket
import threading
import time
import types
from typing import List, Optional

import pytest

import gtach.comm.rfcomm as rfcomm_module
from gtach.comm.transport import (
    _CONNECT_FAULT_CAUSES,
    LINK_BUSY_CAUSE,
    LINK_RESET_CAUSE,
)
from gtach.display.setup_components.bluetooth.interface import (
    BluetoothSetupInterface,
)


class _FakeRFCOMM:
    """Scripted stand-in for RFCOMMTransport; one instance per verify."""

    instances: List["_FakeRFCOMM"] = []
    script: List[Optional[str]] = []

    def __init__(self, mac_address: str, channel: int = 1) -> None:
        self.connect_calls = 0
        self.disconnect_calls = 0
        self.last_failure_cause: Optional[str] = None
        self._script = list(_FakeRFCOMM.script)
        _FakeRFCOMM.instances.append(self)

    def connect(self) -> bool:
        """Pop the next outcome: None succeeds, a string is the failure cause."""
        self.connect_calls += 1
        self.last_failure_cause = self._script.pop(0)
        return self.last_failure_cause is None

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        return "ELM327 v1.5"

    def disconnect(self) -> None:
        self.disconnect_calls += 1


@pytest.fixture
def verify(monkeypatch):
    """Return (run, sleeps); run(script) calls verify_obd_connection."""
    monkeypatch.setattr(socket, "AF_BLUETOOTH", 31, raising=False)
    monkeypatch.setattr(rfcomm_module, "RFCOMMTransport", _FakeRFCOMM)
    sleeps: List[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    _FakeRFCOMM.instances = []

    interface = BluetoothSetupInterface.__new__(BluetoothSetupInterface)
    interface.logger = logging.getLogger("test")
    interface._pairing_factory = None
    interface._ops_lock = threading.Lock()
    interface._adapter_reset = False
    device = types.SimpleNamespace(mac_address="00:11:22:33:44:55")
    interface.device_store = types.SimpleNamespace(  # type: ignore[assignment]
        get_primary_device=lambda: device
    )

    def run(script: List[Optional[str]]) -> bool:
        _FakeRFCOMM.script = script
        return interface.verify_obd_connection(None)  # type: ignore[arg-type]

    return run, sleeps


def test_busy_then_success(verify):
    run, sleeps = verify

    assert run([LINK_BUSY_CAUSE, None]) is True
    (transport,) = _FakeRFCOMM.instances
    assert transport.connect_calls == 2
    assert sleeps == [1.0]
    assert transport.disconnect_calls == 1


def test_other_failure_is_not_retried(verify):
    run, sleeps = verify

    assert run(["connection timed out"]) is False
    (transport,) = _FakeRFCOMM.instances
    assert transport.connect_calls == 1
    assert sleeps == []


def test_busy_three_times_gives_up(verify):
    run, sleeps = verify

    assert run([LINK_BUSY_CAUSE] * 3) is False
    (transport,) = _FakeRFCOMM.instances
    assert transport.connect_calls == 3
    assert len(sleeps) == 2


def test_link_busy_cause_matches_mapping():
    assert LINK_BUSY_CAUSE == _CONNECT_FAULT_CAUSES[errno.EBUSY]


def test_reset_then_success(verify):
    run, sleeps = verify

    assert run([LINK_RESET_CAUSE, None]) is True
    (transport,) = _FakeRFCOMM.instances
    assert transport.connect_calls == 2
    assert sleeps == [1.0]
    assert transport.disconnect_calls == 1


def test_reset_then_busy_then_success(verify):
    run, sleeps = verify

    assert run([LINK_RESET_CAUSE, LINK_BUSY_CAUSE, None]) is True
    (transport,) = _FakeRFCOMM.instances
    assert transport.connect_calls == 3
    assert sleeps == [1.0, 1.0]


def test_reset_three_times_gives_up(verify):
    run, sleeps = verify

    assert run([LINK_RESET_CAUSE] * 3) is False
    (transport,) = _FakeRFCOMM.instances
    assert transport.connect_calls == 3
    assert len(sleeps) == 2


def test_refused_is_not_retried(verify):
    run, sleeps = verify

    assert run(["connection refused by adapter"]) is False
    (transport,) = _FakeRFCOMM.instances
    assert transport.connect_calls == 1
    assert sleeps == []


def test_retry_record_names_the_cause(verify, caplog):
    run, _ = verify

    with caplog.at_level(logging.INFO, logger="test"):
        run([LINK_RESET_CAUSE, None])

    messages = [r.getMessage() for r in caplog.records]
    assert f"OBD verify: {LINK_RESET_CAUSE}, retrying (attempt 2/3)" in messages


def test_link_reset_cause_matches_mapping():
    assert LINK_RESET_CAUSE == _CONNECT_FAULT_CAUSES[errno.ECONNRESET]
    assert len(LINK_RESET_CAUSE) <= 40
