# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Display component integration module.

Provides unified interfaces and factory methods for display system components.
"""

from typing import Tuple, Optional, Dict, Any
from .factory import DisplayComponentFactory, ComponentConfig
from .coordinator import DisplayComponentCoordinator

__all__ = [
    'DisplayComponentFactory',
    'ComponentConfig', 
    'DisplayComponentCoordinator'
]