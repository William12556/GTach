#!/usr/bin/env python3
"""
Display Rendering Engine - Extracted from monolithic DisplayManager.

Handles all pygame surface operations, framebuffer management, and low-level
rendering primitives for the OBDII display system.
"""

import os
import sys
import time
import mmap
import logging
import threading
from typing import Tuple, Optional, Dict, Any
import pygame

from .interfaces import RenderingEngineInterface, RenderTarget, RenderingStats

class DisplayRenderingEngine(RenderingEngineInterface):
    """
    Core rendering engine for OBDII display system.
    
    Provides thread-safe rendering operations, framebuffer management,
    and hardware-specific optimizations for HyperPixel 2" Round display.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('DisplayRenderingEngine')
        self._lock = threading.RLock()
        
        # Surface management
        self.main_surface: Optional[pygame.Surface] = None
        self.back_surface: Optional[pygame.Surface] = None
        self.surface_size = (480, 480)  # HyperPixel 2" Round default
        
        # Framebuffer management
        self.fb_dev = None
        self.fb = None
        self.fb_size = 0
        self.use_mmap = False
        self.framebuffer_path = '/dev/fb0'
        
        # Display constants for HyperPixel 2" Round
        self.display_center = (240, 240)
        self.display_safe_radius = 200
        self.display_max_radius = 220
        
        # Performance tracking
        self._stats = RenderingStats()
        self._initialized = False
        
        # Check pygame availability
        try:
            import pygame
            self.pygame_available = True
        except ImportError:
            self.pygame_available = False
            self.logger.warning("Pygame not available - mock rendering mode")
    
    def initialize(self, surface_size: Tuple[int, int], 
                   framebuffer_path: str = '/dev/fb0') -> bool:
        """
        Initialize the rendering engine with display parameters.
        
        Args:
            surface_size: (width, height) of display surface
            framebuffer_path: Path to framebuffer device
            
        Returns:
            bool: True if initialization successful
        """
        with self._lock:
            try:
                self.surface_size = surface_size
                self.framebuffer_path = framebuffer_path
                self.display_center = (surface_size[0] // 2, surface_size[1] // 2)
                
                if not self.pygame_available:
                    self.logger.info("Pygame not available - using mock initialization")
                    self._initialized = True
                    return True
                
                # Initialize pygame
                os.putenv('SDL_VIDEODRIVER', 'dummy')
                pygame.display.init()
                pygame.font.init()
                
                # Verify font initialization
                if not pygame.font.get_init():
                    self.logger.error("Font initialization failed")
                    pygame.font.init()  # Retry
                
                # Create surfaces
                self.main_surface = pygame.Surface(surface_size)
                self.back_surface = pygame.Surface(surface_size)
                
                # Initialize framebuffer
                self._initialize_framebuffer()
                
                self._initialized = True
                self.logger.info(f"Rendering engine initialized: {surface_size}, framebuffer: {framebuffer_path}")
                return True
                
            except Exception as e:
                self.logger.error(f"Rendering engine initialization failed: {e}", exc_info=True)
                return False
    
    def _initialize_framebuffer(self) -> None:
        """Initialize framebuffer for hardware output"""
        try:
            # Calculate framebuffer size (RGBA32)
            self.fb_size = self.surface_size[0] * self.surface_size[1] * 4
            
            # Try memory-mapped approach first
            try:
                self.fb_dev = open(self.framebuffer_path, 'r+b')
                self.fb = mmap.mmap(self.fb_dev.fileno(), self.fb_size)
                self.use_mmap = True
                self.logger.info("Using memory-mapped framebuffer")
            except Exception as e:
                self.logger.warning(f"Memory-mapped framebuffer failed: {e}")
                # Fallback to direct file writing
                if self.fb_dev:
                    self.fb_dev.close()
                self.fb = open(self.framebuffer_path, 'wb')
                self.use_mmap = False
                self.logger.info("Using direct framebuffer writing")
                
        except Exception as e:
            self.logger.warning(f"Framebuffer initialization failed: {e}")
            self.fb = None
            self.use_mmap = False
    
    def create_surface(self, size: Tuple[int, int], 
                      alpha: bool = False) -> Optional[pygame.Surface]:
        """
        Create a pygame surface with specified parameters.
        
        Args:
            size: (width, height) of surface
            alpha: Whether to enable alpha channel
            
        Returns:
            pygame.Surface or None if creation failed
        """
        with self._lock:
            try:
                if not self.pygame_available:
                    return None
                
                if alpha:
                    surface = pygame.Surface(size, pygame.SRCALPHA)
                else:
                    surface = pygame.Surface(size)
                
                self._stats.surfaces_created += 1
                return surface
                
            except Exception as e:
                self.logger.error(f"Surface creation failed: {e}")
                return None
    
    def clear_surface(self, target: RenderTarget, 
                     color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        """Clear target surface with specified color"""
        with self._lock:
            try:
                surface = self._get_target_surface(target)
                if surface:
                    surface.fill(color)
                    
            except Exception as e:
                self.logger.error(f"Surface clear failed: {e}")
    
    def draw_circle(self, target: RenderTarget, color: Tuple[int, int, int], 
                   center: Tuple[int, int], radius: int, width: int = 0) -> None:
        """Draw circle on target surface"""
        with self._lock:
            try:
                surface = self._get_target_surface(target)
                if surface and self.pygame_available:
                    pygame.draw.circle(surface, color, center, radius, width)
                    
            except Exception as e:
                self.logger.error(f"Circle draw failed: {e}")
    
    def draw_rect(self, target: RenderTarget, color: Tuple[int, int, int],
                 rect: Tuple[int, int, int, int], width: int = 0, 
                 border_radius: int = 0) -> None:
        """Draw rectangle on target surface"""
        with self._lock:
            try:
                surface = self._get_target_surface(target)
                if surface and self.pygame_available:
                    rect_obj = pygame.Rect(rect)
                    if border_radius > 0:
                        try:
                            pygame.draw.rect(surface, color, rect_obj, width, border_radius=border_radius)
                        except TypeError:
                            # Fallback for older pygame versions
                            pygame.draw.rect(surface, color, rect_obj, width)
                    else:
                        pygame.draw.rect(surface, color, rect_obj, width)
                        
            except Exception as e:
                self.logger.error(f"Rectangle draw failed: {e}")
    
    def draw_line(self, target: RenderTarget, color: Tuple[int, int, int],
                 start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 width: int = 1) -> None:
        """Draw line on target surface"""
        with self._lock:
            try:
                surface = self._get_target_surface(target)
                if surface and self.pygame_available:
                    pygame.draw.line(surface, color, start_pos, end_pos, width)
                    
            except Exception as e:
                self.logger.error(f"Line draw failed: {e}")
    
    def blit_surface(self, target: RenderTarget, source: pygame.Surface,
                    dest: Tuple[int, int], area: Optional[Tuple[int, int, int, int]] = None) -> None:
        """Blit source surface to target at specified position"""
        with self._lock:
            try:
                surface = self._get_target_surface(target)
                if surface and source and self.pygame_available:
                    if area:
                        surface.blit(source, dest, area)
                    else:
                        surface.blit(source, dest)
                        
            except Exception as e:
                self.logger.error(f"Surface blit failed: {e}")
    
    def render_text(self, target: RenderTarget, text: str, font: pygame.font.Font,
                   color: Tuple[int, int, int], position: Tuple[int, int],
                   center: bool = True) -> pygame.Rect:
        """
        Render text to target surface and return bounding rect.
        
        Args:
            target: Target surface for rendering
            text: Text to render
            font: Font to use for rendering
            color: Text color
            position: Position for text placement
            center: Whether to center text at position
            
        Returns:
            pygame.Rect: Bounding rectangle of rendered text
        """
        with self._lock:
            try:
                surface = self._get_target_surface(target)
                if not surface or not font or not self.pygame_available:
                    return pygame.Rect(position[0], position[1], 0, 0)
                
                # Render text to temporary surface
                text_surface = font.render(text, True, color)
                
                # Calculate position
                if center:
                    text_rect = text_surface.get_rect(center=position)
                else:
                    text_rect = text_surface.get_rect(topleft=position)
                
                # Blit to target surface
                surface.blit(text_surface, text_rect)
                
                return text_rect
                
            except Exception as e:
                self.logger.error(f"Text render failed: {e}")
                return pygame.Rect(position[0], position[1], 0, 0)
    
    def swap_buffers(self) -> bool:
        """Swap back buffer to main surface"""
        with self._lock:
            try:
                if not self.main_surface or not self.back_surface:
                    return False
                
                self.main_surface.blit(self.back_surface, (0, 0))
                return True
                
            except Exception as e:
                self.logger.error(f"Buffer swap failed: {e}")
                return False
    
    def write_to_framebuffer(self) -> bool:
        """
        Write main surface to hardware framebuffer.
        
        Returns:
            bool: True if write successful
        """
        with self._lock:
            start_time = time.time()
            
            try:
                if not self.main_surface or not self.fb:
                    return False
                
                # Convert surface to proper format
                converted_surface = self.main_surface.convert(32, 0)
                buffer_data = converted_surface.get_buffer()
                
                # Convert to bytes for writing
                try:
                    buffer_bytes = bytes(buffer_data)
                except (TypeError, ValueError):
                    try:
                        buffer_bytes = buffer_data.raw
                    except AttributeError:
                        buffer_bytes = buffer_data
                
                actual_size = len(buffer_bytes)
                
                # Handle size mismatches
                if actual_size != self.fb_size:
                    self.logger.debug(f"Buffer size mismatch: {actual_size} vs {self.fb_size}")
                    if actual_size > self.fb_size:
                        buffer_bytes = buffer_bytes[:self.fb_size]
                    elif actual_size < self.fb_size:
                        buffer_bytes = buffer_bytes + b'\x00' * (self.fb_size - actual_size)
                
                # Write to framebuffer
                if self.use_mmap:
                    self.fb.seek(0)
                    self.fb.write(buffer_bytes)
                    self.fb.flush()
                    try:
                        self.fb.sync()
                    except AttributeError:
                        os.fsync(self.fb_dev.fileno())
                else:
                    self.fb.seek(0)
                    self.fb.write(buffer_bytes)
                    self.fb.flush()
                    os.fsync(self.fb.fileno())
                
                # Update statistics
                self._stats.buffer_writes += 1
                write_time = time.time() - start_time
                self._stats.total_render_time += write_time
                self._stats.last_render_time = write_time
                
                return True
                
            except OSError as e:
                self._stats.framebuffer_errors += 1
                if e.errno == 28:  # No space left on device
                    self.logger.error("Framebuffer write failed: no space left")
                    self._attempt_framebuffer_recovery()
                else:
                    self.logger.error(f"Framebuffer write error: {e}")
                return False
                
            except Exception as e:
                self._stats.framebuffer_errors += 1
                self.logger.error(f"Framebuffer write failed: {e}")
                return False
    
    def _attempt_framebuffer_recovery(self) -> None:
        """Attempt to recover from framebuffer errors"""
        try:
            self.logger.info("Attempting framebuffer recovery")
            
            # Close existing framebuffer
            if self.fb:
                if self.use_mmap:
                    self.fb.close()
                else:
                    self.fb.close()
            
            if self.fb_dev:
                self.fb_dev.close()
            
            # Reinitialize with direct writing
            self.fb = open(self.framebuffer_path, 'wb')
            self.use_mmap = False
            self.fb_dev = None
            
            self.logger.info("Framebuffer recovery completed")
            
        except Exception as e:
            self.logger.error(f"Framebuffer recovery failed: {e}")
            self.fb = None
    
    def get_surface(self, target: RenderTarget) -> Optional[pygame.Surface]:
        """Get reference to specified surface"""
        with self._lock:
            return self._get_target_surface(target)
    
    def _get_target_surface(self, target: RenderTarget) -> Optional[pygame.Surface]:
        """Internal method to get target surface"""
        if target == RenderTarget.MAIN:
            return self.main_surface
        elif target == RenderTarget.BACK_BUFFER:
            return self.back_surface
        else:
            return None
    
    def get_stats(self) -> RenderingStats:
        """Get rendering performance statistics"""
        with self._lock:
            # Calculate average render time
            if self._stats.buffer_writes > 0:
                self._stats.average_render_time = (
                    self._stats.total_render_time / self._stats.buffer_writes
                )
            
            return self._stats
    
    def validate_circular_bounds(self, center: Tuple[int, int], 
                               radius: int, safe_radius: int = None) -> bool:
        """
        Validate that rendering area fits within circular display bounds.
        
        Args:
            center: Center point of circular area
            radius: Radius of area to validate
            safe_radius: Override safe radius (uses default if None)
            
        Returns:
            bool: True if area fits within safe bounds
        """
        if safe_radius is None:
            safe_radius = self.display_safe_radius
        
        # Calculate distance from display center
        dx = center[0] - self.display_center[0]
        dy = center[1] - self.display_center[1]
        distance_from_center = (dx * dx + dy * dy) ** 0.5
        
        # Check if the entire circular area fits within safe radius
        return (distance_from_center + radius) <= safe_radius
    
    def cleanup(self) -> None:
        """Clean up rendering resources"""
        with self._lock:
            try:
                if self.fb:
                    if self.use_mmap:
                        self.fb.close()
                    else:
                        self.fb.close()
                
                if self.fb_dev:
                    self.fb_dev.close()
                
                if self.pygame_available:
                    pygame.quit()
                
                self._initialized = False
                self.logger.info("Rendering engine cleanup completed")
                
            except Exception as e:
                self.logger.error(f"Rendering engine cleanup error: {e}")
    
    def is_initialized(self) -> bool:
        """Check if rendering engine is initialized"""
        return self._initialized
    
    def record_frame(self) -> None:
        """Record completion of frame rendering for statistics"""
        with self._lock:
            self._stats.frames_rendered += 1