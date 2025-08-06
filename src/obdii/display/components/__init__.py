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