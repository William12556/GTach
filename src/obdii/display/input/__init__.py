# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Display input handling components for OBDII display system.

This module provides touch event coordination and gesture recognition
functionality extracted from the monolithic display manager.
"""

from .touch_coordinator import TouchEventCoordinator
from .interfaces import TouchEventInterface, TouchRegion, TouchAction, GestureType

__all__ = [
    'TouchEventCoordinator',
    'TouchEventInterface',
    'TouchRegion', 
    'TouchAction',
    'GestureType'
]