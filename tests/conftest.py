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

# Must precede the first pygame import anywhere in the suite.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# Bound applied to every blocking acquisition assertion in the suite. A
# lost-wakeup defect manifests as a thread that never returns, so an
# unbounded wait would convert a regression into a hung run with no
# diagnostic. Three orders of magnitude above the expected acquisition
# time, so it discriminates without being tight.
ACQUIRE_TIMEOUT = 2.0
