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

class DisplayMode(Enum):
    """Display mode enumeration for different display screens"""
    SPLASH = auto()    # Application startup splash screen
    DIGITAL = auto()   # Digital RPM display mode
    GAUGE = auto()     # Analog gauge RPM display mode
    SETTINGS = auto()  # Settings configuration screen

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