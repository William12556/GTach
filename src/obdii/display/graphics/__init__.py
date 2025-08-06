#!/usr/bin/env python3
"""
Graphics utilities for OBDII display application.
Provides automotive-themed graphics components and visual effects.
"""

from .splash_graphics import (
    draw_automotive_gauge,
    draw_obdii_connector,
    draw_progress_bar,
    draw_animated_dots,
    AUTOMOTIVE_COLORS,
    SPLASH_COLORS
)

__all__ = [
    'draw_automotive_gauge',
    'draw_obdii_connector', 
    'draw_progress_bar',
    'draw_animated_dots',
    'AUTOMOTIVE_COLORS',
    'SPLASH_COLORS'
]