#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Splash screen graphics utilities for OBDII display application.
Provides automotive-themed graphics components with professional styling.
"""

import logging
import math
from typing import Tuple

# Conditional pygame import with fallback
try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    # TODO: issue-ac11505d candidate defect - dead fallback, pygame required
    pygame = None  # type: ignore[assignment]  # TODO: issue-ac11505d
    PYGAME_AVAILABLE = False

# Professional automotive color palette
AUTOMOTIVE_COLORS = {
    # Primary colors
    "primary_blue": (64, 150, 255),  # OBD connector blue
    "primary_orange": (255, 140, 0),  # Warning/diagnostic orange
    "primary_green": (50, 200, 50),  # Connected/ready green
    "primary_red": (255, 60, 60),  # Error/danger red
    # Background colors
    "dark_background": (15, 20, 25),  # Main dark background
    "surface_dark": (25, 30, 35),  # Elevated surface
    "surface_medium": (40, 45, 50),  # Medium surface
    "surface_light": (60, 65, 70),  # Light surface
    # Text colors
    "text_primary": (255, 255, 255),  # Primary white text
    "text_secondary": (200, 210, 220),  # Secondary light gray
    "text_tertiary": (150, 160, 170),  # Tertiary medium gray
    "text_disabled": (100, 110, 120),  # Disabled dark gray
    # Accent colors
    "accent_bright": (100, 200, 255),  # Bright accent
    "accent_warm": (255, 180, 100),  # Warm accent
    "accent_cool": (100, 255, 200),  # Cool accent
    # Gauge colors
    "gauge_normal": (50, 200, 50),  # Normal operation green
    "gauge_warning": (255, 165, 0),  # Warning orange
    "gauge_danger": (255, 50, 50),  # Danger red
    "gauge_background": (30, 35, 40),  # Gauge background
    "gauge_tick": (180, 190, 200),  # Tick mark color
}

# Splash screen specific colors
SPLASH_COLORS = {
    "background": AUTOMOTIVE_COLORS["dark_background"],
    "title_text": AUTOMOTIVE_COLORS["text_primary"],
    "subtitle_text": AUTOMOTIVE_COLORS["text_secondary"],
    "progress_fill": AUTOMOTIVE_COLORS["primary_blue"],
    "progress_background": AUTOMOTIVE_COLORS["surface_medium"],
    "connector_active": AUTOMOTIVE_COLORS["primary_green"],
    "connector_inactive": AUTOMOTIVE_COLORS["surface_light"],
    "gauge_active": AUTOMOTIVE_COLORS["primary_blue"],
    "animation_primary": AUTOMOTIVE_COLORS["accent_bright"],
    "border": AUTOMOTIVE_COLORS["surface_light"],
}


def draw_automotive_gauge(
    surface: "pygame.Surface", center: Tuple[int, int], radius: int, progress: float
) -> bool:
    """
    Draw an automotive-style circular gauge with progress indication.

    Renders a professional gauge similar to those found in modern vehicles,
    with tick marks, colored zones, and a progress indicator suitable for
    startup progress or diagnostic status display.

    Args:
        surface: Pygame surface to draw on
        center: Center point as (x, y) tuple
        radius: Gauge radius in pixels
        progress: Progress value from 0.0 to 1.0

    Returns:
        bool: True if drawing succeeded, False on error

    Raises:
        None: All exceptions are caught and logged
    """
    if not PYGAME_AVAILABLE or surface is None:
        return False

    logger = logging.getLogger("SplashGraphics")

    try:
        center_x, center_y = center

        # Validate inputs
        if radius <= 0 or progress < 0:
            logger.warning(
                f"Invalid gauge parameters: radius={radius}, progress={progress}"
            )
            return False

        # Clamp progress to valid range
        progress = max(0.0, min(1.0, progress))

        # Gauge configuration
        start_angle = 225  # Start at bottom-left (225 degrees)
        total_sweep = 270  # Total 270-degree sweep

        # Draw gauge background ring
        background_thickness = max(2, radius // 20)
        try:
            pygame.draw.circle(
                surface,
                AUTOMOTIVE_COLORS["gauge_background"],
                center,
                radius,
                background_thickness,
            )
        except Exception as e:
            logger.error(f"Error drawing gauge background: {e}", exc_info=True)
            return False

        # Draw tick marks around the gauge
        tick_count = 12  # Major tick marks
        minor_tick_count = 60  # Minor tick marks

        # Draw minor ticks
        for i in range(minor_tick_count):
            angle = start_angle - (i / minor_tick_count * total_sweep)
            angle_rad = math.radians(angle)

            # Calculate tick positions
            outer_radius = radius - background_thickness
            inner_radius = outer_radius - (radius // 25)  # Short minor ticks

            outer_x = center_x + int(outer_radius * math.cos(angle_rad))
            outer_y = center_y - int(outer_radius * math.sin(angle_rad))
            inner_x = center_x + int(inner_radius * math.cos(angle_rad))
            inner_y = center_y - int(inner_radius * math.sin(angle_rad))

            tick_color = AUTOMOTIVE_COLORS["gauge_tick"]
            tick_width = 1

            try:
                pygame.draw.line(
                    surface,
                    tick_color,
                    (outer_x, outer_y),
                    (inner_x, inner_y),
                    tick_width,
                )
            except Exception:
                continue  # Skip individual tick errors

        # Draw major ticks
        for i in range(tick_count):
            angle = start_angle - (i / tick_count * total_sweep)
            angle_rad = math.radians(angle)

            # Calculate tick positions
            outer_radius = radius - background_thickness
            inner_radius = outer_radius - (radius // 12)  # Longer major ticks

            outer_x = center_x + int(outer_radius * math.cos(angle_rad))
            outer_y = center_y - int(outer_radius * math.sin(angle_rad))
            inner_x = center_x + int(inner_radius * math.cos(angle_rad))
            inner_y = center_y - int(inner_radius * math.sin(angle_rad))

            tick_color = AUTOMOTIVE_COLORS["text_secondary"]
            tick_width = 2

            try:
                pygame.draw.line(
                    surface,
                    tick_color,
                    (outer_x, outer_y),
                    (inner_x, inner_y),
                    tick_width,
                )
            except Exception:
                continue  # Skip individual tick errors

        # Draw progress arc
        if progress > 0:
            progress_angle = progress * total_sweep
            progress_thickness = max(3, radius // 15)

            # Calculate color based on progress
            if progress < 0.6:
                arc_color = AUTOMOTIVE_COLORS["gauge_normal"]
            elif progress < 0.85:
                arc_color = AUTOMOTIVE_COLORS["gauge_warning"]
            else:
                arc_color = AUTOMOTIVE_COLORS["gauge_danger"]

            # Draw progress arc using multiple lines for smooth appearance
            arc_radius = radius - background_thickness - (progress_thickness // 2)
            arc_steps = max(10, int(progress_angle))

            for i in range(arc_steps):
                angle = start_angle - (i / arc_steps * progress_angle)
                next_angle = start_angle - ((i + 1) / arc_steps * progress_angle)

                angle_rad = math.radians(angle)
                next_angle_rad = math.radians(next_angle)

                x1 = center_x + int(arc_radius * math.cos(angle_rad))
                y1 = center_y - int(arc_radius * math.sin(angle_rad))
                x2 = center_x + int(arc_radius * math.cos(next_angle_rad))
                y2 = center_y - int(arc_radius * math.sin(next_angle_rad))

                try:
                    pygame.draw.line(
                        surface, arc_color, (x1, y1), (x2, y2), progress_thickness
                    )
                except Exception:
                    continue

        # Draw center hub
        hub_radius = max(3, radius // 15)
        try:
            pygame.draw.circle(
                surface, AUTOMOTIVE_COLORS["surface_medium"], center, hub_radius
            )
            pygame.draw.circle(
                surface, AUTOMOTIVE_COLORS["text_secondary"], center, hub_radius, 1
            )
        except Exception as e:
            logger.error(f"Error drawing gauge hub: {e}", exc_info=True)

        return True

    except Exception as e:
        logger.error(f"Automotive gauge drawing failed: {e}", exc_info=True)
        return False
