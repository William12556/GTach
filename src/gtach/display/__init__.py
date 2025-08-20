# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Display components for OBDII display application."""

import logging

# Import core display components (always required)
from .models import DisplayMode, DisplayConfig, ConnectionStatus
from .manager import DisplayManager

# Safe import of TouchHandler with fallback handling
try:
    from .touch import TouchHandler
    TOUCH_HANDLER_AVAILABLE = True
    _logger = logging.getLogger('gtach.display')
    _logger.debug("TouchHandler imported successfully")
except ImportError as e:
    TouchHandler = None
    TOUCH_HANDLER_AVAILABLE = False
    _logger = logging.getLogger('gtach.display')
    _logger.warning(f"TouchHandler import failed: {e}")
    _logger.info("Touch functionality will not be available")

# Conditionally build __all__ list based on successful imports
__all__ = [
    'DisplayManager',
    'DisplayMode', 
    'DisplayConfig',
    'ConnectionStatus',
    'TOUCH_HANDLER_AVAILABLE'
]

# Add TouchHandler to exports only if successfully imported
if TOUCH_HANDLER_AVAILABLE:
    __all__.append('TouchHandler')