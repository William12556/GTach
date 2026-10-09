# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Pre-initialised settle in OBDProtocol._initialize_protocol (issue-04c18cda)."""

import threading
import time

import pytest

from gtach.comm.obd import OBDProtocol
from gtach.comm.sim_transport import SimTransport
from gtach.core.thread import ThreadManager


@pytest.fixture
def protocol(monkeypatch):
    transport = SimTransport()
    transport.connect()
    thread_manager = ThreadManager()
    proto = OBDProtocol(transport, thread_manager, adapter_pre_initialised=True)
    heartbeats = []
    commands = []

    def record_heartbeat(name):
        if name == "obd_protocol":
            heartbeats.append(time.monotonic())

    real_send = transport.send_command

    def record_send(command, timeout=2.0):
        commands.append(command)
        return real_send(command, timeout)

    monkeypatch.setattr(thread_manager, "update_heartbeat", record_heartbeat)
    monkeypatch.setattr(transport, "send_command", record_send)
    yield proto, heartbeats, commands
    thread_manager.shutdown()


def test_settle_keeps_heartbeat_gap_bounded(protocol):
    proto, heartbeats, _ = protocol

    start = time.monotonic()
    assert proto._initialize_protocol() is True
    duration = time.monotonic() - start

    gaps = [b - a for a, b in zip(heartbeats, heartbeats[1:])]
    assert max(gaps) <= 0.6
    assert duration >= 1.4


def test_stop_during_settle_returns_false_without_commands(protocol):
    proto, _, commands = protocol
    timer = threading.Timer(0.2, proto.shutdown_event.set)
    timer.start()

    start = time.monotonic()
    result = proto._initialize_protocol()
    duration = time.monotonic() - start
    timer.join()

    assert result is False
    assert duration <= 0.7
    assert "ATE0" not in commands


def test_stop_already_set_returns_immediately(protocol):
    proto, _, commands = protocol
    proto.shutdown_event.set()

    start = time.monotonic()
    assert proto._initialize_protocol() is False
    assert time.monotonic() - start < 0.1
    assert commands == []
