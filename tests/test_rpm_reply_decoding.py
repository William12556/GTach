"""Decoding of the 010C reply.

Covers audit-bce0d69a finding L01 (trivial change, governance P04.12): a
reply that leaves an odd number of hexadecimal digits is dropped without
an ERROR record.
"""

import logging
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from gtach.comm.obd import OBDProtocol


class _ScriptedTransport:
    """Connected transport that answers every command from a list."""

    def __init__(self, replies: List[Optional[str]]) -> None:
        self._replies = list(replies)

    def is_connected(self) -> bool:
        return True

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        return self._replies.pop(0) if self._replies else None


def _protocol(reply: Optional[str]) -> OBDProtocol:
    transport = _ScriptedTransport([reply])
    return OBDProtocol(transport, MagicMock())  # type: ignore[arg-type]


def test_valid_reply_is_decoded():
    sample = _protocol("410C1AF8")._request_rpm()
    assert sample is not None
    assert sample.data == bytes([0x1A, 0xF8])


@pytest.mark.parametrize(
    "reply",
    [
        "410C0FA0\rCAN ERROR",  # C, A and E are hexadecimal digits: 11 in total
        "410C0FA01",
        "410C1AF",
    ],
)
def test_odd_digit_count_is_dropped_without_error(reply, caplog):
    with caplog.at_level(logging.DEBUG, logger="OBDProtocol"):
        assert _protocol(reply)._request_rpm() is None
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


def test_reply_for_another_pid_is_dropped():
    assert _protocol("410D1AF8")._request_rpm() is None
