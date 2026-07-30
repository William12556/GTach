#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Display Rendering Engine - Extracted from monolithic DisplayManager.

Handles all pygame surface operations, framebuffer management, and low-level
rendering primitives for the OBDII display system.
"""

import os
import sys
import time
import mmap
import fcntl
import struct
import logging
import threading
from typing import Tuple, Optional, Dict, Any
import pygame

from .interfaces import RenderingEngineInterface, RenderTarget, RenderingStats

# Linux framebuffer ioctls (linux/fb.h).
#
# The first three are plain values in the header. FBIO_WAITFORVSYNC
# is declared _IOW('F', 0x20, __u32), which encodes direction and
# argument size as well as type and number:
#
#   (1 << 30) | (4 << 16) | (0x46 << 8) | 0x20 == 0x40044620
#
# The display review cites 0x4620, which is the type and number
# portion only. Some drivers mask the encoding and accept it;
# relying on that is not safe.
FBIOGET_VSCREENINFO = 0x4600
FBIOPUT_VSCREENINFO = 0x4601
FBIOPAN_DISPLAY = 0x4606
FBIO_WAITFORVSYNC = 0x40044620

FB_ACTIVATE_NOW = 0
FB_ACTIVATE_VBL = 16

# struct fb_var_screeninfo is 40 x __u32 == 160 bytes.
FB_VAR_STRUCT = '40I'
FB_VAR_YRES = 1
FB_VAR_YRES_VIRTUAL = 3
FB_VAR_YOFFSET = 5
FB_VAR_ACTIVATE = 21

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
        self._view_fallback_logged = False

        # Presentation mode, decided once in _initialize_framebuffer
        self.page_flip = False           # second half established
        self.vsync_available = False     # FBIO_WAITFORVSYNC works
        self.buffer_index = 0            # half currently displayed
        self._original_var = None        # for restoration in cleanup
        self._panning_var = None         # post-resize template for the pan
        self._vsync_failed_logged = False
        self._pan_failed_logged = False
        
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
                
                # Initialize pygame — headless SDL dummy driver
                os.environ['SDL_VIDEODRIVER'] = 'dummy'

                pygame.display.init()
                pygame.font.init()
                
                # Verify font initialization
                if not pygame.font.get_init():
                    self.logger.error("Font initialization failed")
                    pygame.font.init()  # Retry
                
                # Single surface at the framebuffer's own depth. Creating it
                # at 32 bits removes the per-frame convert(32, 0) entirely:
                # converting returns a NEW surface, so converting once and
                # keeping the result would leave drawing going to the
                # unconverted original (display review §5.1, recommendation 7).
                self.back_surface = pygame.Surface(surface_size, 0, 32)

                # main_surface is retained as an alias so RenderTarget.MAIN
                # and get_surface() continue to resolve. There is no second
                # buffer: nothing happens between composition and the write,
                # so the intermediate copy had no purpose (recommendation 6).
                self.main_surface = self.back_surface

                self.logger.info(
                    f"Surface format: {self.back_surface.get_bitsize()}-bit, "
                    f"masks={self.back_surface.get_masks()}"
                )

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

            # Presentation mode. Page flipping needs the mmap path;
            # if the direct-file fallback was taken there is no
            # mapping to extend.
            if self.use_mmap:
                self.page_flip = self._setup_page_flip()

            if not self.page_flip:
                self.vsync_available = self._wait_for_vsync()

            if self.page_flip:
                mode = "page flip"
            elif self.vsync_available:
                mode = "vsync-synchronised write"
            else:
                mode = "unsynchronised write"
            self.logger.info(f"Framebuffer presentation mode: {mode}")

        except Exception as e:
            self.logger.warning(f"Framebuffer initialization failed: {e}")
            self.fb = None
            self.use_mmap = False

    def _fb_dev_usable(self) -> bool:
        """Whether the framebuffer device can accept an ioctl.

        The direct-file fallback in _initialize_framebuffer closes fb_dev
        but leaves the attribute bound, so a truthiness test alone would
        pass and the ioctl would then raise ValueError on a closed file.

        Returns:
            True if fb_dev exists and is open.
        """
        return bool(self.fb_dev) and not getattr(self.fb_dev, 'closed', False)

    def _setup_page_flip(self) -> bool:
        """Attempt to establish a second framebuffer half.

        Doubles yres_virtual so the device holds two frames, then
        remaps over both. Failure is an expected outcome on hardware
        whose framebuffer is allocated at boot, so it is logged at
        INFO and reported as False rather than raised.

        Returns:
            True if page flipping is available.
        """
        if not self._fb_dev_usable():
            return False

        try:
            raw = fcntl.ioctl(
                self.fb_dev.fileno(), FBIOGET_VSCREENINFO,
                bytes(struct.calcsize(FB_VAR_STRUCT))
            )
            self._original_var = raw

            var = list(struct.unpack(FB_VAR_STRUCT, raw))
            yres = var[FB_VAR_YRES]
            if yres <= 0:
                self.logger.info("Page flip unavailable: driver reports yres 0")
                return False

            var[FB_VAR_YRES_VIRTUAL] = yres * 2
            var[FB_VAR_ACTIVATE] = FB_ACTIVATE_NOW
            fcntl.ioctl(
                self.fb_dev.fileno(), FBIOPUT_VSCREENINFO,
                struct.pack(FB_VAR_STRUCT, *var)
            )

            # Act on what the driver granted, not what was requested.
            confirmed = struct.unpack(FB_VAR_STRUCT, fcntl.ioctl(
                self.fb_dev.fileno(), FBIOGET_VSCREENINFO,
                bytes(struct.calcsize(FB_VAR_STRUCT))
            ))
            if confirmed[FB_VAR_YRES_VIRTUAL] < yres * 2:
                self.logger.info(
                    f"Page flip unavailable: driver granted yres_virtual "
                    f"{confirmed[FB_VAR_YRES_VIRTUAL]}, needed {yres * 2}"
                )
                return False

            # Establish the new mapping BEFORE discarding the old one. If
            # the remap fails the engine must be left with a working
            # single-frame mapping; closing first would leave self.fb
            # closed and every subsequent write would fail on it.
            new_map = mmap.mmap(self.fb_dev.fileno(), self.fb_size * 2)
            old_map = self.fb
            self.fb = new_map
            if old_map is not None:
                try:
                    old_map.close()
                except Exception:
                    pass

            # The pan template must describe the enlarged geometry, not the
            # geometry captured before the resize. _original_var is kept
            # unmodified for cleanup to restore.
            self._panning_var = struct.pack(FB_VAR_STRUCT, *confirmed)

            self.logger.info("Page flip enabled: two framebuffer halves mapped")
            return True

        except Exception as e:
            errno = getattr(e, 'errno', None)
            self.logger.info(
                f"Page flip unavailable: {e}"
                + (f" (errno {errno})" if errno is not None else "")
            )
            return False

    def _wait_for_vsync(self) -> bool:
        """Block until the start of the vertical blanking interval.

        Returns:
            True if the wait succeeded. On failure the capability is
            disabled so it is not retried, and the caller proceeds
            without synchronisation.
        """
        if not self._fb_dev_usable():
            return False

        try:
            fcntl.ioctl(self.fb_dev.fileno(), FBIO_WAITFORVSYNC,
                        struct.pack('I', 0))
            return True
        except Exception as e:
            self.vsync_available = False
            if not self._vsync_failed_logged:
                self._vsync_failed_logged = True
                self.logger.info(f"Vertical-blank wait unavailable: {e}")
            return False

    def _pan_display(self, index: int) -> bool:
        """Present a framebuffer half by moving the scan-out origin.

        Args:
            index: 0 or 1 — which half to display.

        Returns:
            True if the pan succeeded.
        """
        if not self._fb_dev_usable() or self._panning_var is None:
            return False

        try:
            var = list(struct.unpack(FB_VAR_STRUCT, self._panning_var))
            var[FB_VAR_YOFFSET] = index * var[FB_VAR_YRES]
            # Asks the driver to latch at the next blanking interval.
            # Not all drivers honour it; correctness does not depend on it.
            var[FB_VAR_ACTIVATE] = FB_ACTIVATE_VBL
            fcntl.ioctl(self.fb_dev.fileno(), FBIOPAN_DISPLAY,
                        struct.pack(FB_VAR_STRUCT, *var))
            return True
        except Exception as e:
            if not self._pan_failed_logged:
                self._pan_failed_logged = True
                self.logger.info(f"Page flip failed, reverting to direct write: {e}")
            return False

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
        """No-op retained for interface compatibility.

        back_surface is written to the framebuffer directly, so there
        is no intermediate surface to swap into. The method is kept
        because it is declared on RenderingEngineInterface
        (interfaces.py:91) and called from
        DisplayManager._display_loop; removing it would be an
        interface change for no benefit (display review §5.1,
        recommendation 6).

        Returns:
            True always.
        """
        return True
    
    def write_to_framebuffer(self) -> bool:
        """
        Write main surface to display output.

        On macOS uses pygame.display.flip() to update the window.
        On Linux/Pi writes to the hardware framebuffer device.
        
        Returns:
            bool: True if write successful
        """
        with self._lock:
            start_time = time.time()
            
            try:
                if not self.back_surface:
                    return False

                if not self.fb:
                    return False

                # A buffer-protocol view over the surface's own memory.
                # mmap.write and file.write both accept it, so the frame
                # is not materialised into a bytes object first
                # (recommendation 8).
                payload = None
                try:
                    payload = self.back_surface.get_view('0')
                except Exception as e:
                    if not getattr(self, '_view_fallback_logged', False):
                        self._view_fallback_logged = True
                        self.logger.error(
                            f"Surface view unavailable, falling back to a per-frame "
                            f"copy: {e}", exc_info=True
                        )

                if payload is None:
                    converted_surface = self.back_surface.convert(32, 0)
                    buffer_data = converted_surface.get_buffer()
                    try:
                        payload = bytes(buffer_data)
                    except (TypeError, ValueError):
                        try:
                            payload = buffer_data.raw
                        except AttributeError:
                            payload = buffer_data

                # pygame.BufferProxy does not implement __len__ — its size is
                # exposed as .length. bytes and memoryview, used by the
                # fallback above, do implement it. Calling len() on the view
                # raises TypeError, which the handler below would absorb into
                # a returned False, failing every frame silently.
                actual_size = getattr(payload, 'length', None)
                if actual_size is None:
                    actual_size = len(payload)

                # Size mismatch: materialise, then truncate or pad as
                # before. Behaviour and log level are unchanged here —
                # raising the level is recommendation 21 (task 7.3.3).
                if actual_size != self.fb_size:
                    self.logger.debug(f"Buffer size mismatch: {actual_size} vs {self.fb_size}")
                    payload = bytes(payload)
                    if actual_size > self.fb_size:
                        payload = payload[:self.fb_size]
                    else:
                        payload = payload + b'\x00' * (self.fb_size - actual_size)

                # Single write, no synchronisation. flush/sync/fsync give
                # no correctness benefit on a framebuffer device and
                # lengthen the window in which the scan-out can read a
                # partially updated buffer (display review §4.1,
                # recommendation 2).
                if self.page_flip:
                    # Compose into the half the controller is not
                    # scanning, then present it atomically. No
                    # pre-write wait is needed: nothing is reading
                    # this half (display review §4.1, recommendation 4).
                    target = self.buffer_index ^ 1
                    self.fb.seek(target * self.fb_size)
                    self.fb.write(payload)
                    if self._pan_display(target):
                        self.buffer_index = target
                    else:
                        self.page_flip = False
                else:
                    # Single buffer. Beginning the write at the start
                    # of blanking narrows the window in which the
                    # scan-out can read a partially updated buffer
                    # (recommendation 3).
                    if self.vsync_available:
                        self._wait_for_vsync()
                    self.fb.seek(0)
                    self.fb.write(payload)

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
                # Restore the virtual resolution and scan-out origin, so
                # the console is usable after exit.
                if self._original_var is not None and self._fb_dev_usable():
                    try:
                        fcntl.ioctl(self.fb_dev.fileno(), FBIOPUT_VSCREENINFO,
                                    self._original_var)
                    except Exception as e:
                        self.logger.warning(f"Could not restore screen info: {e}")
                    finally:
                        self._original_var = None

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