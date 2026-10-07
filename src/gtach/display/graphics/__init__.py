#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Graphics utilities for OBDII display application.
Provides automotive-themed graphics components and visual effects.
"""

from .splash_graphics import (
    draw_automotive_gauge,
    AUTOMOTIVE_COLORS,
    SPLASH_COLORS
)

__all__ = [
    'draw_automotive_gauge',
    'AUTOMOTIVE_COLORS',
    'SPLASH_COLORS'
]