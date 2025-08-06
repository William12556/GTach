#!/usr/bin/env python3
"""
Interfaces and data structures for touch event handling.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any, List, Callable
import pygame

class GestureType(Enum):
    """Types of touch gestures"""
    TAP = auto()
    LONG_PRESS = auto()
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()
    SWIPE_UP = auto()
    SWIPE_DOWN = auto()
    DRAG = auto()
    PINCH = auto()

class TouchAction(Enum):
    """Touch action results"""
    NONE = auto()
    MODE_CHANGE = auto()
    SETTINGS_CHANGE = auto()
    NAVIGATION = auto()
    SLIDER_INTERACTION = auto()
    BUTTON_PRESS = auto()

@dataclass
class TouchRegion:
    """Defines a touchable region with associated metadata"""
    region_id: str
    rect: pygame.Rect
    action_type: TouchAction
    metadata: Dict[str, Any]
    enabled: bool = True
    
class TouchEventInterface(ABC):
    """Interface for touch event coordinators"""
    
    @abstractmethod
    def register_region(self, region: TouchRegion) -> bool:
        """Register a touchable region"""
        pass
    
    @abstractmethod
    def unregister_region(self, region_id: str) -> bool:
        """Unregister a touchable region"""
        pass
    
    @abstractmethod
    def clear_regions(self) -> None:
        """Clear all registered regions"""
        pass
    
    @abstractmethod
    def handle_touch_down(self, pos: Tuple[int, int]) -> Optional[TouchAction]:
        """Handle touch down event"""
        pass
    
    @abstractmethod
    def handle_touch_move(self, pos: Tuple[int, int]) -> Optional[TouchAction]:
        """Handle touch move/drag event"""
        pass
    
    @abstractmethod
    def handle_touch_up(self, pos: Tuple[int, int]) -> Optional[TouchAction]:
        """Handle touch up/release event"""
        pass
    
    @abstractmethod
    def handle_gesture(self, gesture_type: GestureType, 
                      start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> Optional[TouchAction]:
        """Handle recognized gesture"""
        pass
    
    @abstractmethod
    def get_active_regions(self) -> List[TouchRegion]:
        """Get list of currently active touch regions"""
        pass
    
    @abstractmethod
    def validate_coordinates(self, pos: Tuple[int, int]) -> bool:
        """Validate touch coordinates are within display bounds"""
        pass