# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Tests for SimTransport.drop_link (issue-50bf25ad)."""

from gtach.comm.sim_transport import SimTransport
from gtach.comm.transport import _SILENT_LINK_CAUSE, TransportState


def test_drop_link_with_cause_is_observed():
    transport = SimTransport()
    transport.connect()

    transport.drop_link("test cause")

    assert transport.is_connected() is False
    assert transport.state is TransportState.DISCONNECTED
    assert transport.last_failure_cause == "test cause"
    assert transport._shutdown.is_set() is False


def test_drop_link_without_cause_uses_default():
    transport = SimTransport()
    transport.connect()

    transport.drop_link()

    assert transport.last_failure_cause == _SILENT_LINK_CAUSE


def test_connect_after_drop_link_reconnects():
    transport = SimTransport()
    transport.connect()
    transport.drop_link()

    assert transport.connect() is True
    assert transport.is_connected() is True


def test_drop_link_before_connect_is_harmless():
    transport = SimTransport()

    transport.drop_link()

    assert transport.is_connected() is False


def test_rpm_sweep_uses_monotonic_clock(monkeypatch):
    import types
    import gtach.comm.sim_transport as sim_module

    monkeypatch.setattr(
        sim_module,
        "time",
        types.SimpleNamespace(
            monotonic=lambda: 1000.0,
            time=lambda: (_ for _ in ()).throw(AssertionError()),
        ),
    )

    transport = SimTransport()
    result = transport.send_command("010C")
    assert result == "41 0C 39 08"


def test_rpm_sweep_ignores_wall_clock_steps(monkeypatch):
    import types
    import gtach.comm.sim_transport as sim_module

    call_count = [0]

    def mock_monotonic():
        call_count[0] += 1
        if call_count[0] == 1:
            return 1000.0
        return 1030.0

    monkeypatch.setattr(
        sim_module,
        "time",
        types.SimpleNamespace(
            monotonic=mock_monotonic,
            time=lambda: (_ for _ in ()).throw(AssertionError()),
        ),
    )

    transport = SimTransport()
    result = transport.send_command("010C")
    assert result == "41 0C 39 08"
