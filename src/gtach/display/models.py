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
from typing import Tuple

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


@dataclass(frozen=True)
class Palette:
    """Every colour the instrument draws.

    The HyperPixel 2.1 Round's backlight cannot be reduced in
    software, so the palette's own luminance is the only
    control over emitted light. Two instances exist; the
    operator chooses between them (display review §7.9,
    recommendation 29; ai/task.md §7.3.14).

    Frozen so a drawing path cannot mutate the active
    palette.
    """
    name: str
    ground: Tuple[int, int, int]
    track: Tuple[int, int, int]
    tick: Tuple[int, int, int]
    line: Tuple[int, int, int]
    edge: Tuple[int, int, int]
    label: Tuple[int, int, int]
    bands: Tuple[Tuple[int, int, int], ...]
    band_centres: Tuple[Tuple[int, int, int], ...]


# Values copied verbatim from the constants in use before
# change-5012004e — the six FACE_ constants and BAND_COLOURS added by
# change-5014040c — so day rendering is provably unchanged. The
# shift-cue fields that once sat alongside band_centres were removed
# with the rim border they coloured (issue-950128c0); band_centres is
# now the centre disc's unconditional source.
DAY_PALETTE = Palette(
    name='day',
    ground=(16, 16, 16),
    track=(58, 58, 58),
    tick=(225, 225, 225),
    line=(90, 90, 90),
    edge=(70, 70, 70),
    label=(200, 80, 80),
    # Torque and caution were the two brightest elements on the panel —
    # 0.715 and 0.928 relative luminance against a danger band at 0.213
    # — so the instrument's brightness order ran almost exactly counter
    # to its urgency order, and the operator reported both as too bright
    # in daylight (issue-e7c3a512).
    #
    # sRGB weights green at 0.7152 and red at 0.2126, so a palette chosen
    # for hue distinctness at full saturation inherits that ordering
    # rather than choosing it. These two values are set deliberately and
    # are not arbitrary; they sit between the previous full-saturation
    # pair and the night set, and were measured against ground
    # (16, 16, 16):
    #
    #   2 torque   (0, 170, 0)     lum 0.287   6.12:1
    #   3 caution  (205, 180, 0)   lum 0.456   9.17:1
    #
    # Band 1's 2.21:1 is below the 3:1 used elsewhere and is not
    # correctable — pure blue is 0.0722 and cannot reach 3:1 against any
    # ground darker than itself (ai/task.md §9.8.5 item 3). Danger is
    # deliberately not brightened to lead the ordering: urgency is
    # carried by the shift-cue flash, not by band brightness.
    bands=(
        (0, 0, 255),        # 0 idle
        (0, 0, 255),        # 1 torque approach
        (0, 170, 0),        # 2 torque
        (205, 180, 0),      # 3 caution
        (255, 128, 0),      # 4 warning
        (255, 0, 0),        # 5 danger
    ),
    # The centre disc takes the active band's colour, so the zone
    # reading is present at the point of fixation and not only at the
    # rim (change-64d8d8fc). Dim, because the disc is 30,800 px in the
    # driver's forward field of view and the HyperPixel's backlight
    # cannot be reduced in software — full-saturation band colour here
    # would reinstate the glare change-5014040c removed from the face,
    # and would leave the white readout at 1.07:1 against band 3.
    band_centres=(
        (0, 0, 89),         # 0 idle
        (0, 0, 89),         # 1 torque approach
        (0, 89, 0),         # 2 torque
        (89, 89, 0),        # 3 caution
        (89, 45, 0),        # 4 warning
        (89, 0, 0),         # 5 danger
    ),
)

# Authored, not derived. Scaling the day palette would compress the band
# colours toward one another, and the band cue is the instrument's
# primary signal — so value is reduced while hue separation is held, and
# the separation is asserted by delta-E rather than judged by eye.
NIGHT_PALETTE = Palette(
    name='night',
    ground=(3, 3, 3),
    track=(24, 24, 24),
    tick=(120, 120, 120),
    line=(42, 42, 42),
    edge=(30, 30, 30),
    label=(100, 38, 38),
    bands=(
        (0, 0, 170),        # 0 idle
        (0, 0, 170),        # 1 torque approach
        (0, 140, 0),        # 2 torque
        (150, 140, 0),      # 3 caution
        (175, 75, 0),       # 4 warning
        (200, 0, 0),        # 5 danger
    ),
    # The band-coloured centre disc, dimmed for night on the same
    # reasoning as the day tuple above (change-64d8d8fc).
    band_centres=(
        (0, 0, 59),
        (0, 0, 59),
        (0, 49, 0),
        (52, 49, 0),
        (61, 26, 0),
        (70, 0, 0),
    ),
)

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
    gesture_enable_settings: bool = True      # Enable gestures in options

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