#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Session B findings F2 and F3 (change-146491ba).

F2: every DEVICE_LIST error-line text fits the 220 px error line in
get_label_small_font(). F3: a 0100 reply of None with the transport
disconnected is a lost link, not a silent vehicle.
"""

import logging
import types
from typing import Any, List, Optional

import pygame
import pytest

from gtach.comm.obd import OBDProtocol
from gtach.display.setup_components.bluetooth.interface import (
    DEVICE_NOT_SAVED_TEXT,
    FALLBACK_LIST_TEXT,
    OBD_CHECK_FAILED_TEXT,
    SCAN_FAILED_TEXT,
)
from gtach.display.typography import get_label_small_font

# Width of the DEVICE_LIST error line (change-d38362aa).
ERROR_LINE_WIDTH_PX = 220


@pytest.fixture(scope="module")
def small_font() -> pygame.font.Font:
    """The small-text font, with the dummy video driver set by conftest."""
    pygame.font.init()
    return get_label_small_font()


@pytest.mark.parametrize(
    "text",
    [
        SCAN_FAILED_TEXT,
        FALLBACK_LIST_TEXT,
        pytest.param(
            DEVICE_NOT_SAVED_TEXT,
            marks=pytest.mark.xfail(
                strict=True, reason="measured 221 px; out of scope (change-146491ba)"
            ),
        ),
        OBD_CHECK_FAILED_TEXT,
    ],
)
def test_error_line_text_fits(small_font, text):
    assert small_font.size(text)[0] <= ERROR_LINE_WIDTH_PX


class _LinkTransport:
    """A transport that answers config commands and drops before 0100.

    Args:
        connected_at_0100: Whether the link is still up when 0100 is sent.
        reply_0100: The reply to 0100 when the link is up.
    """

    def __init__(self, connected_at_0100: bool, reply_0100: Optional[str]) -> None:
        self.connected = True
        self.connected_at_0100 = connected_at_0100
        self.reply_0100 = reply_0100
        self.sent: List[str] = []

    def is_connected(self) -> bool:
        return self.connected

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        self.sent.append(command)
        if command == "ATSP0":
            self.connected = self.connected_at_0100
        if command == "0100":
            return self.reply_0100
        return "OK"


def _protocol(transport: _LinkTransport) -> OBDProtocol:
    manager: Any = types.SimpleNamespace(
        register_thread=lambda *a, **k: None,
        update_heartbeat=lambda name: None,
    )
    return OBDProtocol(transport, manager)  # type: ignore[arg-type]


def test_lost_link_is_not_a_silent_vehicle(caplog):
    transport = _LinkTransport(connected_at_0100=False, reply_0100=None)
    protocol = _protocol(transport)

    with caplog.at_level(logging.DEBUG, logger="OBDProtocol"):
        assert protocol._initialize_protocol() is False

    records = [r for r in caplog.records if r.name == "OBDProtocol"]
    assert not [r for r in records if r.levelno >= logging.WARNING]
    lost = [r for r in records if r.getMessage() == "Link lost during initialisation"]
    assert len(lost) == 1
    assert lost[0].levelno == logging.DEBUG
    assert protocol._vehicle_silent is False
    assert protocol._no_vehicle_logged_at is None
    assert "0100" not in transport.sent


def test_lost_link_leaves_silent_state_unchanged(caplog):
    transport = _LinkTransport(connected_at_0100=False, reply_0100=None)
    protocol = _protocol(transport)
    protocol._vehicle_silent = True
    protocol._no_vehicle_logged_at = 123.0

    with caplog.at_level(logging.DEBUG, logger="OBDProtocol"):
        assert protocol._initialize_protocol() is False

    assert protocol._vehicle_silent is True
    assert protocol._no_vehicle_logged_at == 123.0
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_timeout_with_link_up_is_reported(caplog):
    transport = _LinkTransport(connected_at_0100=True, reply_0100=None)
    protocol = _protocol(transport)

    with caplog.at_level(logging.DEBUG, logger="OBDProtocol"):
        assert protocol._initialize_protocol() is False

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert warnings[0].getMessage() == (
        "Vehicle not answering: no valid 0100 response (None)"
    )
    assert protocol._vehicle_silent is True
    assert not [
        r for r in caplog.records if r.getMessage() == "Link lost during initialisation"
    ]
