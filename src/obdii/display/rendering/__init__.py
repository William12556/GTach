"""
Display rendering components for OBDII display system.

This module provides rendering engine functionality extracted from the monolithic
display manager for improved maintainability and testing.
"""

from .engine import DisplayRenderingEngine
from .interfaces import RenderingEngineInterface, RenderTarget, RenderingStats

__all__ = [
    'DisplayRenderingEngine',
    'RenderingEngineInterface', 
    'RenderTarget',
    'RenderingStats'
]