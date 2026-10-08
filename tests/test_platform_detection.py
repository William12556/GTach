#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Masked hardware-revision parsing and consolidated Pi detection.

Automates test-11be4865 (change-11be4865; core review §3.2, §4.4).
Case identifiers in each test docstring refer to that plan.
"""

import builtins
import logging
import sys
from pathlib import Path
from unittest import mock

import pytest

from gtach.utils.dependencies import DependencyValidator
from gtach.utils.platform import PlatformDetector, PlatformType


def _detect_revision(revision_line):
    """Run _detect_via_hardware_revision against synthetic cpuinfo text."""
    content = "processor\t: 0\n" + (revision_line + "\n" if revision_line else "")
    with mock.patch.object(Path, "exists", return_value=True), mock.patch(
        "builtins.open", mock.mock_open(read_data=content)
    ):
        return PlatformDetector()._detect_via_hardware_revision()


class TestHardwareRevision:
    def test_zero_2w_base_revision(self):
        """TC-001: base code with no flag bits resolves at 0.95."""
        result = _detect_revision("Revision\t: 902120")
        assert result.platform_type is PlatformType.RASPBERRY_PI_ZERO_2W
        assert result.confidence == 0.95

    def test_zero_2w_with_overvoltage_flag(self):
        """TC-002: the flag bit is masked off; result matches TC-001."""
        result = _detect_revision("Revision\t: 1902120")
        assert result.platform_type is PlatformType.RASPBERRY_PI_ZERO_2W
        assert result.confidence == 0.95

    def test_leading_zero_base_code_is_not_over_stripped(self):
        """TC-003: '1000042' masks to '000042'; detection is not discarded.

        The former lstrip('1000') yielded '42', which failed the six-character
        test and returned None.
        """
        result = _detect_revision("Revision\t: 1000042")
        assert result is not None
        assert result.platform_type is PlatformType.RASPBERRY_PI_GENERIC
        assert result.confidence == 0.7
        assert format(int("1000042", 16) & 0xFFFFFF, "06x") == "000042"

    @pytest.mark.parametrize(
        "revision, expected",
        [
            ("a03111", PlatformType.RASPBERRY_PI_4),
            ("b03112", PlatformType.RASPBERRY_PI_4),
            ("c03114", PlatformType.RASPBERRY_PI_4),
            ("d03114", PlatformType.RASPBERRY_PI_4),
            ("c04170", PlatformType.RASPBERRY_PI_5),
            ("d04170", PlatformType.RASPBERRY_PI_5),
        ],
    )
    def test_pi4_and_pi5_mapped_revisions(self, revision, expected):
        """TC-004: mapped Pi 4 and Pi 5 codes resolve at 0.95."""
        result = _detect_revision(f"Revision\t: {revision}")
        assert result.platform_type is expected
        assert result.confidence == 0.95

    def test_old_style_four_digit_code(self):
        """TC-005: '0002' pads to '000002' and resolves to GENERIC at 0.7."""
        result = _detect_revision("Revision\t: 0002")
        assert result.platform_type is PlatformType.RASPBERRY_PI_GENERIC
        assert result.confidence == 0.7

    def test_non_hex_revision_returns_none(self):
        """TC-006: ValueError is caught by the explicit guard."""
        assert _detect_revision("Revision\t: not-hex") is None

    def test_revision_line_absent(self):
        """TC-007 (a): no Revision line returns None."""
        assert _detect_revision(None) is None

    def test_cpuinfo_absent(self):
        """TC-007 (b): /proc/cpuinfo absent returns None."""
        with mock.patch.object(Path, "exists", return_value=False):
            assert PlatformDetector()._detect_via_hardware_revision() is None

    @pytest.mark.parametrize("revision", ["A03111", "0xa03111"])
    def test_uppercase_and_prefixed_revisions(self, revision):
        """TC-008: int(s, 16) accepts both; '06x' emits the lowercase key."""
        result = _detect_revision(f"Revision\t: {revision}")
        assert result.platform_type is PlatformType.RASPBERRY_PI_4


def _open_cpuinfo(content=None, error=None):
    """Return an open() replacement that intercepts /proc/cpuinfo only."""
    real_open = builtins.open

    def _open(path, *args, **kwargs):
        if str(path) == "/proc/cpuinfo":
            if error is not None:
                raise error
            return mock.mock_open(read_data=content)()
        return real_open(path, *args, **kwargs)

    return _open


class TestDependencyValidatorPlatform:
    def test_agrees_with_platform_detector(self):
        """TC-009: is_raspberry_pi comes from the PlatformDetector accessor."""
        opened = []
        real_open = builtins.open

        def _tracking_open(path, *args, **kwargs):
            opened.append(str(path))
            return real_open(path, *args, **kwargs)

        with mock.patch(
            "gtach.utils.platform.is_raspberry_pi", return_value=True
        ), mock.patch("builtins.open", _tracking_open):
            info = DependencyValidator().platform_info
        assert info["is_raspberry_pi"] is True
        assert info["is_development"] is False
        assert "/proc/cpuinfo" not in opened

    def test_falls_back_when_platform_detection_unavailable(
        self, monkeypatch, caplog
    ):
        """TC-010: ImportError triggers the inline cpuinfo fallback."""
        monkeypatch.setitem(sys.modules, "gtach.utils.platform", None)
        caplog.set_level(logging.DEBUG, logger="DependencyValidator")
        with mock.patch(
            "builtins.open", _open_cpuinfo(content="Hardware\t: BCM2835\n")
        ):
            validator = DependencyValidator()
        assert validator.platform_info["is_raspberry_pi"] is True
        fallback = [
            r
            for r in caplog.records
            if r.levelno == logging.DEBUG
            and "PlatformDetector unavailable" in r.getMessage()
        ]
        assert len(fallback) == 1

    def test_platform_info_keys_and_types(self):
        """TC-011: six keys with their original types."""
        info = DependencyValidator().platform_info
        expected = {
            "system": str,
            "machine": str,
            "python_version": str,
            "is_raspberry_pi": bool,
            "is_linux": bool,
            "is_development": bool,
        }
        assert set(info) == set(expected)
        for key, kind in expected.items():
            assert isinstance(info[key], kind), key

    def test_non_linux_host_without_cpuinfo(self):
        """TC-012: no os.uname and no /proc/cpuinfo give sane defaults."""
        with mock.patch(
            "gtach.utils.dependencies.os.uname", side_effect=AttributeError
        ), mock.patch(
            "gtach.utils.platform.is_raspberry_pi", return_value=False
        ), mock.patch(
            "builtins.open", _open_cpuinfo(error=FileNotFoundError())
        ):
            info = DependencyValidator().platform_info
        assert info["is_raspberry_pi"] is False
        assert info["is_linux"] is False
        assert info["is_development"] is False
