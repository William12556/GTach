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
    RADIAL = auto()           # The only normal display mode; carries the
                              # arc, the indicator and the numeric readout
                              # (change-378703da retired DIGITAL)
    OPTIONS = auto()          # Options configuration screen
    ACKNOWLEDGEMENT = auto()  # RPM threshold acknowledgement screen

class ConnectionStatus(Enum):
    """Connection status for indicator"""
    DISCONNECTED = 'red'
    CONNECTING = 'yellow'
    CONNECTED = 'green'

