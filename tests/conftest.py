#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Shared pytest configuration for the GTach test suite.

Sets the SDL dummy video driver before any test imports pygame, matching
the headless arrangement DisplayRenderingEngine.initialize uses at
engine.py:92. Display tests therefore create no window and never call
set_mode.
"""

import os
import shutil
import tempfile

import pytest

# Must precede the first pygame import anywhere in the suite.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# Must precede the first gtach import anywhere in the suite. Everything
# GTach reads and writes at runtime lives under gtach_home(); pointing
# GTACH_HOME at a temporary directory keeps the suite out of /opt/gtach
# and the repository (audit-36b6ea95 F05, issue-5fbff586).
_TEST_HOME = tempfile.mkdtemp(prefix="gtach-test-home-")
os.environ["GTACH_HOME"] = _TEST_HOME


def pytest_sessionfinish(session, exitstatus):
    """Remove the temporary GTACH_HOME created for the session."""
    shutil.rmtree(_TEST_HOME, ignore_errors=True)


@pytest.fixture(autouse=True)
def _reset_device_store():
    """Discard the shared DeviceStore after each test (issue-453f0a80)."""
    yield
    from gtach.comm.device_store import reset_device_store

    reset_device_store()


# Bound applied to every blocking acquisition assertion in the suite. A
# lost-wakeup defect manifests as a thread that never returns, so an
# unbounded wait would convert a regression into a hung run with no
# diagnostic. Three orders of magnitude above the expected acquisition
# time, so it discriminates without being tight.
ACQUIRE_TIMEOUT = 2.0
