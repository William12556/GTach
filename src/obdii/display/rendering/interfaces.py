#!/usr/bin/env python3
"""
Interfaces and data structures for display rendering components.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any, List
import pygame

class RenderTarget(Enum):
    """Target surface for rendering operations"""
    MAIN = auto()
    BACK_BUFFER = auto()
    FRAMEBUFFER = auto()

@dataclass
class RenderingStats:
    """Statistics for rendering performance tracking"""
    frames_rendered: int = 0
    total_render_time: float = 0.0
    average_render_time: float = 0.0
    last_render_time: float = 0.0
    surfaces_created: int = 0
    buffer_writes: int = 0
    framebuffer_errors: int = 0

class RenderingEngineInterface(ABC):
    """Interface for display rendering engines"""
    
    @abstractmethod
    def initialize(self, surface_size: Tuple[int, int], 
                   framebuffer_path: str = '/dev/fb0') -> bool:
        """Initialize the rendering engine with display parameters"""
        pass
    
    @abstractmethod
    def create_surface(self, size: Tuple[int, int], 
                      alpha: bool = False) -> Optional[pygame.Surface]:
        """Create a pygame surface with specified parameters"""
        pass
    
    @abstractmethod
    def clear_surface(self, target: RenderTarget, 
                     color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        """Clear target surface with specified color"""
        pass
    
    @abstractmethod
    def draw_circle(self, target: RenderTarget, color: Tuple[int, int, int], 
                   center: Tuple[int, int], radius: int, width: int = 0) -> None:
        """Draw circle on target surface"""
        pass
    
    @abstractmethod
    def draw_rect(self, target: RenderTarget, color: Tuple[int, int, int],
                 rect: Tuple[int, int, int, int], width: int = 0, 
                 border_radius: int = 0) -> None:
        """Draw rectangle on target surface"""
        pass
    
    @abstractmethod
    def draw_line(self, target: RenderTarget, color: Tuple[int, int, int],
                 start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 width: int = 1) -> None:
        """Draw line on target surface"""
        pass
    
    @abstractmethod
    def blit_surface(self, target: RenderTarget, source: pygame.Surface,
                    dest: Tuple[int, int], area: Optional[Tuple[int, int, int, int]] = None) -> None:
        """Blit source surface to target at specified position"""
        pass
    
    @abstractmethod
    def render_text(self, target: RenderTarget, text: str, font: pygame.font.Font,
                   color: Tuple[int, int, int], position: Tuple[int, int],
                   center: bool = True) -> pygame.Rect:
        """Render text to target surface and return bounding rect"""
        pass
    
    @abstractmethod
    def swap_buffers(self) -> bool:
        """Swap back buffer to main surface"""
        pass
    
    @abstractmethod
    def write_to_framebuffer(self) -> bool:
        """Write main surface to hardware framebuffer"""
        pass
    
    @abstractmethod
    def get_surface(self, target: RenderTarget) -> Optional[pygame.Surface]:
        """Get reference to specified surface"""
        pass
    
    @abstractmethod
    def get_stats(self) -> RenderingStats:
        """Get rendering performance statistics"""
        pass
    
    @abstractmethod
    def validate_circular_bounds(self, center: Tuple[int, int], 
                               radius: int, safe_radius: int) -> bool:
        """Validate that rendering area fits within circular display bounds"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up rendering resources"""
        pass