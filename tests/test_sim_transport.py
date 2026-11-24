# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Tests for SimTransport.drop_link and sim_rpm (issue-50bf25ad, 0b3317b7)."""

import pytest

from gtach.comm.sim_transport import (
    SIM_RPM_MAX,
    SIM_RPM_MIN,
    SIM_RPM_PERIOD_S,
    SimTransport,
    sim_rpm,
)
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
    assert result == "41 0C 39 D0"


def test_rpm_sweep_ignores_wall_clock_steps(monkeypatch):
    import types

    import gtach.comm.sim_transport as sim_module

    call_count = [0]

    def mock_monotonic():
        call_count[0] += 1
        if call_count[0] == 1:
            return 1000.0
        return 1003.75

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
    # t = 3.75 s is a quarter period, the sweep maximum, 6600 RPM; t = 0
    # would give 39 D0.
    assert result == "41 0C 67 20"


@pytest.mark.parametrize(
    "t, expected",
    [(0.0, 3700.0), (3.75, 6600.0), (11.25, 800.0)],
)
def test_sim_rpm_values(t, expected):
    assert sim_rpm(t) == pytest.approx(expected, abs=1e-6)


def test_sim_rpm_range_over_one_period():
    samples = [sim_rpm(i * SIM_RPM_PERIOD_S / 1000) for i in range(1000)]
    assert all(SIM_RPM_MIN <= rpm <= SIM_RPM_MAX for rpm in samples)


@pytest.mark.parametrize("t", [0.0, 1.3, 3.75, 7.9, 11.25])
def test_sim_rpm_is_periodic(t):
    assert sim_rpm(t) == pytest.approx(sim_rpm(t + SIM_RPM_PERIOD_S), abs=1e-6)
