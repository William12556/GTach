# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Display components for OBDII display application."""

import logging

from .manager import DisplayManager

# Import core display components (always required)
from .models import ConnectionStatus, DisplayConfig, DisplayMode
from .touch import TouchHandler

_logger = logging.getLogger("gtach.display")
_logger.debug("TouchHandler imported successfully")

__all__ = [
    "DisplayManager",
    "DisplayMode",
    "DisplayConfig",
    "ConnectionStatus",
    "TouchHandler",
]
