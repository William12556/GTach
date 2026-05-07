#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Shared data models for display components.
Contains enums and data classes used across display modules.
"""

from enum import Enum, auto
from dataclasses import dataclass

@dataclass
class RPMBands:
    """RPM threshold bands for colour-coded display zones.

    Attributes:
        idle_max: Maximum RPM for idle zone (blue)
        torque_start: Start of torque zone (green)
        caution_start: Start of caution zone (yellow)
        warning_start: Start of warning zone (orange)
        danger_start: Start of danger zone (red)
        redline_rpm: Redline RPM threshold
    """
    idle_max: int = 999
    torque_start: int = 3000
    caution_start: int = 4500
    warning_start: int = 5500
    danger_start: int = 5800
    redline_rpm: int = 6000

    def __post_init__(self):
        """Validate that thresholds are strictly ascending."""
        thresholds = [
            self.idle_max,
            self.torque_start,
            self.caution_start,
            self.warning_start,
            self.danger_start,
            self.redline_rpm
        ]

        # Check strictly ascending
        for i in range(len(thresholds) - 1):
            if thresholds[i] >= thresholds[i + 1]:
                raise ValueError(
                    f"RPM thresholds must be strictly ascending. "
                    f"Got {thresholds[i]} >= {thresholds[i + 1]}"
                )

        # Check valid range
        for threshold in thresholds:
            if threshold <= 0 or threshold > 15000:
                raise ValueError(
                    f"RPM thresholds must be > 0 and <= 15000. Got {threshold}"
                )

class DisplayMode(Enum):
    """Display mode enumeration for different display screens"""
    SPLASH = auto()           # Application startup splash screen
    DIGITAL = auto()          # Digital RPM display mode
    GAUGE = auto()            # Analog gauge RPM display mode
    SETTINGS = auto()         # Settings configuration screen
    ACKNOWLEDGEMENT = auto()  # RPM threshold acknowledgement screen

class ConnectionStatus(Enum):
    """Connection status for indicator"""
    DISCONNECTED = 'red'
    CONNECTING = 'yellow'
    CONNECTED = 'green'

@dataclass
class DisplayConfig:
    """Display configuration settings"""
    mode: DisplayMode
    rpm_warning: int = 6500  # Fiat 500 Abarth redline
    rpm_danger: int = 7000   # Danger zone
    fps_limit: int = 60
    touch_long_press: float = 1.0  # seconds

    # Gesture navigation settings
    gesture_swipe_threshold: int = 80          # Minimum swipe distance (px)
    gesture_velocity_threshold: float = 200.0  # Minimum swipe velocity (px/s)
    gesture_edge_width: int = 40              # Edge detection width (px)
    gesture_max_time: float = 1.0             # Maximum gesture duration (s)
    gesture_edge_timeout: float = 5.0         # Edge indicator timeout (s)

    # Gesture enables per context
    gesture_enable_main: bool = True          # Enable gestures in main display
    gesture_enable_setup: bool = True         # Enable gestures in setup mode
    gesture_enable_settings: bool = True      # Enable gestures in settings

    # Visual feedback settings
    gesture_transition_duration: float = 0.2  # Screen transition time (s)
    gesture_edge_indicator_size: int = 20     # Edge indicator size (px)
    gesture_debug_mode: bool = False          # Show gesture debug visualization
    engine_profile: str = 'abarth_595_turismo'  # Engine profile identifier for acknowledgement state

    # RPM colour bands
    rpm_bands: RPMBands = None  # Will be initialized with default in __post_init__

    def __post_init__(self):
        """Initialize rpm_bands if not provided."""
        if self.rpm_bands is None:
            self.rpm_bands = RPMBands()