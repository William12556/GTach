#!/usr/bin/env python3
"""
Display management for OBDII display application.
Handles display rendering and mode management.
"""

import os
import sys
import math
import logging
import threading
import time
import mmap
import subprocess
from enum import Enum, auto
from typing import Optional, Tuple

# Conditional imports for hardware dependencies
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

from .models import DisplayMode, DisplayConfig, ConnectionStatus
from .splash import SplashScreen
from .typography import (get_font_manager, get_title_font, get_medium_font, get_small_font, get_minimal_font,
                         get_rpm_large_font, get_rpm_medium_font, get_label_small_font, 
                         get_title_display_font, get_heading_font, TypographyConstants,
                         get_button_renderer, ButtonSize, ButtonState)
from .performance import (initialize_performance_manager, get_performance_manager, 
                         cleanup_performance_manager, PerformanceManager)
from ..core import ThreadManager, ThreadStatus
from ..utils import TerminalRestorer

class DisplayManager:
    """Manages display rendering and modes"""
    
    def __init__(self, thread_manager: ThreadManager, terminal_restorer: TerminalRestorer = None, config_path: str = 'config.yaml'):
        self.logger = logging.getLogger('DisplayManager')
        self.thread_manager = thread_manager
        self.config_path = config_path
        self._shutdown_event = threading.Event()
        self.terminal_restorer = terminal_restorer
        
        # Check pygame availability
        if not PYGAME_AVAILABLE:
            self.logger.warning("Pygame not available - display will use text-only mode")
            self.display_available = False
        else:
            self.display_available = True
            
        self._init_display()
        self._load_config()
        
        # Import TouchHandler with safe handling
        try:
            from .touch import TouchHandler
            self.touch_handler = TouchHandler(self)
        except ImportError as e:
            self.logger.warning(f"TouchHandler not available: {e}")
            self.touch_handler = None
        
        # Setup mode components
        self._setup_manager = None
        self._in_setup_mode = False
        
        # Initialize splash screen with configuration
        try:
            splash_config = getattr(self.config, 'splash', None)
            self._splash_screen = SplashScreen(surface_size=(480, 480), duration=4.0, config=splash_config)
            self.logger.info("Splash screen initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize splash screen: {e}")
            self._splash_screen = None
        
        # Circular display constants for HyperPixel 2" Round (480x480 display)
        self.display_center = (240, 240)  # Center point of circular display
        self.display_safe_radius = 200    # Safe radius for UI elements (conservative)
        self.display_max_radius = 220     # Maximum usable radius (edge of circle)
        self.display_size = (480, 480)    # Full display dimensions
        
        # Slider interaction state
        self._slider_drag_state = {
            'active': False,
            'slider_id': None,
            'initial_touch_pos': None,
            'initial_value': None
        }
        
        # Initialize navigation gesture handler
        try:
            from .navigation_gestures import NavigationGestureHandler, GestureConfig
            
            # Create gesture config from display config
            gesture_config = GestureConfig(
                swipe_threshold=self.config.gesture_swipe_threshold,
                velocity_threshold=self.config.gesture_velocity_threshold,
                edge_width=self.config.gesture_edge_width,
                max_gesture_time=self.config.gesture_max_time,
                edge_indicator_timeout=self.config.gesture_edge_timeout,
                enable_main_navigation=self.config.gesture_enable_main,
                enable_setup_navigation=self.config.gesture_enable_setup,
                enable_settings_gestures=self.config.gesture_enable_settings,
                debug_mode=self.config.gesture_debug_mode
            )
            
            self.gesture_handler = NavigationGestureHandler(self, gesture_config)
            self.logger.info("Navigation gesture handler initialized")
            
        except ImportError as e:
            self.logger.error(f"Failed to initialize gesture handler: {e}")
            self.gesture_handler = None
        
        self.display_thread = threading.Thread(
            target=self._display_loop,
            name='DisplayManager'
        )
        self.thread_manager.register_thread('display', self.display_thread)

    def _check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            # Get disk usage info for root partition
            output = subprocess.check_output(['df', '-h', '/']).decode('utf-8')
            lines = output.strip().split('\n')
            if len(lines) >= 2:
                # Parse usage percentage 
                usage_line = lines[1].split()
                if len(usage_line) >= 5:
                    usage_percent = int(usage_line[4].strip('%'))
                    if usage_percent > 90:
                        self.logger.warning(f"Low disk space: {usage_percent}% used")
                        return False
            return True
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return False

    def _get_cached_font(self, size: int, font_path: Optional[str] = None) -> Optional[pygame.font.Font]:
        """
        Get cached font using performance manager, with fallback to font manager.
        
        Args:
            size: Font size in pixels
            font_path: Optional path to font file
            
        Returns:
            pygame.font.Font object or None
        """
        try:
            # Try performance manager first
            if self.performance_manager:
                font = self.performance_manager.get_font(size, font_path)
                if font:
                    return font
            
            # Fallback to font manager
            font_manager = get_font_manager()
            return font_manager.get_font(size)
            
        except Exception as e:
            self.logger.warning(f"Error getting cached font: {e}")
            # Final fallback to pygame
            try:
                return pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
            except:
                return None

    def _init_display(self) -> None:
        """Initialize display and framebuffer"""
        try:
            # Backup framebuffer settings if terminal restorer is available
            if self.terminal_restorer:
                self.terminal_restorer.backup_framebuffer_settings()
            
            if not PYGAME_AVAILABLE:
                self.logger.info("Pygame not available - skipping display initialization")
                self.main_surface = None
                self.back_surface = None
                self.use_mmap = False
                return
            
            # Initialize pygame and font subsystem
            os.putenv('SDL_VIDEODRIVER', 'dummy')
            pygame.display.init()
            pygame.font.init()  # Explicitly initialize the font module
            
            # Check if font initialization was successful
            if not pygame.font.get_init():
                self.logger.error("Font initialization failed")
                pygame.font.init()  # Try again
            
            self.main_surface = pygame.Surface((480, 480))
            self.back_surface = pygame.Surface((480, 480))
            
            # Initialize performance management system
            try:
                log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'performance.log')
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                self.performance_manager = initialize_performance_manager((480, 480), log_file)
                self.logger.info("Performance management system initialized")
            except Exception as e:
                self.logger.warning(f"Performance manager initialization failed: {e}")
                self.performance_manager = None
            
            # Check if there's enough disk space
            self._check_disk_space()
            
            # Use memory-mapped file for framebuffer instead of direct writes
            try:
                # Try to open and map framebuffer
                self.fb_dev = open('/dev/fb0', 'r+b')
                self.fb_size = 480 * 480 * 4  # width * height * bytes_per_pixel
                self.fb = mmap.mmap(self.fb_dev.fileno(), self.fb_size)
                self.use_mmap = True
                self.logger.info("Using memory-mapped framebuffer")
            except Exception as e:
                self.logger.warning(f"Memory-mapped framebuffer failed: {e}")
                # Fall back to direct file writing
                self.fb = open('/dev/fb0', 'wb')
                self.use_mmap = False
                self.logger.info("Using direct framebuffer writing")
                
            self.logger.info("Display initialized")
            
        except Exception as e:
            self.logger.error(f"Display initialization failed: {e}", exc_info=True)
            sys.exit(1)

    def _load_config(self) -> None:
        """Load display configuration"""
        try:
            if YAML_AVAILABLE and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    # Load saved mode but always start with splash screen
                    saved_mode = DisplayMode[config_data.get('mode', 'DIGITAL')]
                    self.config = DisplayConfig(
                        mode=DisplayMode.SPLASH,  # Always start with splash
                        rpm_warning=config_data.get('rpm_warning', 6500),
                        rpm_danger=config_data.get('rpm_danger', 7000),
                        fps_limit=config_data.get('fps_limit', 60),
                        touch_long_press=config_data.get('touch_long_press', 1.0)
                    )
                    # Store the mode to transition to after splash
                    self._post_splash_mode = saved_mode
            else:
                if not YAML_AVAILABLE:
                    self.logger.info("YAML not available - using default configuration")
                self.config = DisplayConfig(mode=DisplayMode.SPLASH)
                self._post_splash_mode = DisplayMode.DIGITAL  # Default transition mode
                if YAML_AVAILABLE:
                    self._save_config()
                
        except Exception as e:
            self.logger.error(f"Config load failed: {e}", exc_info=True)
            self.config = DisplayConfig(mode=DisplayMode.SPLASH)
            self._post_splash_mode = DisplayMode.DIGITAL  # Default transition mode

    def _save_config(self) -> None:
        """Save current configuration"""
        if not YAML_AVAILABLE:
            self.logger.debug("YAML not available - configuration will not be persisted")
            return
            
        try:
            config_data = {
                'mode': self.config.mode.name,
                'rpm_warning': self.config.rpm_warning,
                'rpm_danger': self.config.rpm_danger,
                'fps_limit': self.config.fps_limit,
                'touch_long_press': self.config.touch_long_press
            }
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f)
                
        except Exception as e:
            self.logger.error(f"Config save failed: {e}")

    def start(self) -> None:
        """Start display manager with splash screen"""
        # Start the splash screen timing
        self.start_splash()
        
        # Start the display thread
        self.display_thread.start()
        self.logger.info("Display manager started")

    def start_splash(self) -> None:
        """Start the splash screen and begin timing"""
        try:
            if self._splash_screen:
                self._splash_screen.start()
                self.config.mode = DisplayMode.SPLASH
                self.logger.info("Splash screen started")
            else:
                self.logger.warning("No splash screen available - skipping to normal mode")
                self.config.mode = self._post_splash_mode
        except Exception as e:
            self.logger.error(f"Failed to start splash screen: {e}")
            # Fall back to normal mode
            self.config.mode = self._post_splash_mode

    def stop(self) -> None:
        """Stop display manager"""
        self._shutdown_event.set()
        self.display_thread.join()
        
        # Clean up resources properly
        try:
            if hasattr(self, 'fb'):
                if self.use_mmap:
                    self.fb.close()
                else:
                    self.fb.close()
                    
            if hasattr(self, 'fb_dev'):
                self.fb_dev.close()
                
            # Clean up performance manager
            if hasattr(self, 'performance_manager') and self.performance_manager:
                cleanup_performance_manager()
                self.logger.info("Performance manager cleaned up")
            
            pygame.quit()
            self.logger.info("Display manager stopped")
        except Exception as e:
            self.logger.error(f"Error closing display resources: {e}", exc_info=True)

    def _display_loop(self) -> None:
        """Main display loop with performance optimizations"""
        clock = pygame.time.Clock()
        frame_count = 0
        last_performance_log = time.time()
        
        self.logger.info("Display loop started with performance optimizations")
        
        while not self._shutdown_event.is_set():
            try:
                frame_start_time = time.time()
                
                self.thread_manager.update_heartbeat('display')
                
                # Process any pending touch events (if touch handler is available)
                if self.touch_handler and hasattr(self.touch_handler, 'touch_interface'):
                    if self.touch_handler.touch_interface and hasattr(self.touch_handler.touch_interface, 'is_running'):
                        if not self.touch_handler.touch_interface.is_running():
                            self.logger.warning("Touch interface stopped running - attempting restart")
                            try:
                                self.touch_handler.touch_interface.start()
                            except Exception as e:
                                self.logger.error(f"Failed to restart touch interface: {e}")
                
                # Clear back surface only if we're doing a full redraw
                dirty_regions = []
                if self.performance_manager:
                    dirty_regions = self.performance_manager.get_dirty_regions()
                
                if not dirty_regions or len(dirty_regions) == 1 and dirty_regions[0] == pygame.Rect(0, 0, 480, 480):
                    # Full redraw
                    self.back_surface.fill((0, 0, 0))
                else:
                    # Partial update - only clear dirty regions
                    for rect in dirty_regions:
                        self.back_surface.fill((0, 0, 0), rect)
                
                # Check for splash screen mode first - this takes priority over all other modes
                if self.config.mode == DisplayMode.SPLASH:
                    self._draw_splash_mode()
                # Check if we're in setup mode (after splash completes)
                elif self._in_setup_mode and self._setup_manager:
                    # Render setup mode UI to back surface
                    try:
                        self._setup_manager.render(self.back_surface)
                    except Exception as e:
                        self.logger.error(f"Setup mode render error: {e}")
                        # Fall back to showing setup mode indicator
                        self._draw_setup_mode_fallback()
                else:
                    # Normal display modes
                    if self.config.mode == DisplayMode.DIGITAL:
                        self._draw_digital_mode()
                        self._draw_status_indicator()
                    elif self.config.mode == DisplayMode.GAUGE:
                        self._draw_gauge_mode()
                        self._draw_status_indicator()
                    elif self.config.mode == DisplayMode.SETTINGS:
                        self._draw_settings_mode()
                        self._draw_status_indicator()
                
                # Render edge indicators for gesture navigation (on top of everything)
                self._render_edge_indicators()
                
                # Render to screen
                self.main_surface.blit(self.back_surface, (0, 0))
                
                # Write to framebuffer with error handling
                try:
                    # Convert surface to proper format and get buffer
                    converted_surface = self.main_surface.convert(32, 0)
                    buffer_data = converted_surface.get_buffer()
                    
                    # Validate buffer size using proper BufferProxy methods
                    buffer_size = None
                    buffer_bytes = None
                    
                    try:
                        # BufferProxy objects have a length property that can be accessed differently
                        if hasattr(buffer_data, 'length'):
                            buffer_size = buffer_data.length
                        elif hasattr(buffer_data, '__len__'):
                            # Some pygame versions support __len__ on BufferProxy
                            buffer_size = len(buffer_data)
                        else:
                            # Fallback: try to get the size from the surface dimensions
                            surface_width, surface_height = converted_surface.get_size()
                            bytes_per_pixel = converted_surface.get_bitsize() // 8
                            buffer_size = surface_width * surface_height * bytes_per_pixel
                            self.logger.debug(f"Calculated buffer size from surface: {buffer_size}")
                            
                        # Convert BufferProxy to bytes for size validation and writing
                        try:
                            buffer_bytes = bytes(buffer_data)
                            actual_size = len(buffer_bytes)
                            
                            # Log buffer size information for debugging
                            if buffer_size != actual_size:
                                self.logger.debug(f"Buffer size discrepancy: calculated={buffer_size}, actual={actual_size}")
                            
                        except (TypeError, ValueError) as conv_error:
                            self.logger.error(f"Failed to convert BufferProxy to bytes: {conv_error}")
                            # Try alternative conversion methods
                            try:
                                buffer_bytes = buffer_data.raw
                                actual_size = len(buffer_bytes)
                            except AttributeError:
                                # Last resort: use the buffer directly if possible
                                buffer_bytes = buffer_data
                                actual_size = buffer_size or self.fb_size
                                
                    except Exception as size_error:
                        self.logger.error(f"Buffer size validation error: {size_error}")
                        # Use fallback size calculation
                        surface_width, surface_height = converted_surface.get_size()
                        bytes_per_pixel = converted_surface.get_bitsize() // 8
                        actual_size = surface_width * surface_height * bytes_per_pixel
                        buffer_bytes = bytes(buffer_data) if buffer_data else b''
                    
                    # Validate buffer size matches expected framebuffer size
                    if actual_size != self.fb_size:
                        self.logger.warning(f"Buffer size mismatch: got {actual_size}, expected {self.fb_size}")
                        
                        # Handle size mismatches gracefully
                        if actual_size > self.fb_size:
                            # Truncate buffer to fit framebuffer
                            buffer_bytes = buffer_bytes[:self.fb_size]
                            self.logger.debug(f"Truncated buffer from {actual_size} to {self.fb_size} bytes")
                        elif actual_size < self.fb_size:
                            # Pad buffer to match framebuffer size
                            padding_needed = self.fb_size - actual_size
                            buffer_bytes = buffer_bytes + b'\x00' * padding_needed
                            self.logger.debug(f"Padded buffer from {actual_size} to {self.fb_size} bytes")
                    
                    # Ensure we have valid buffer data
                    if not buffer_bytes:
                        self.logger.error("Buffer conversion resulted in empty data")
                        continue
                    
                    if self.use_mmap:
                        # Using memory-mapped file
                        self.fb.seek(0)
                        self.fb.write(buffer_bytes)
                        self.fb.flush()  # Critical: flush memory-mapped file
                        # Force sync to ensure data reaches hardware
                        try:
                            self.fb.sync()
                        except AttributeError:
                            # mmap.sync() not available, use msync via os
                            import os
                            os.fsync(self.fb_dev.fileno())
                    else:
                        # Direct file writing
                        self.fb.seek(0)  # Ensure we write from beginning
                        self.fb.write(buffer_bytes)
                        self.fb.flush()
                        # Force kernel to write data to device
                        import os
                        os.fsync(self.fb.fileno())
                        
                except (pygame.error, ValueError, TypeError) as e:
                    self.logger.error(f"Surface conversion or buffer handling error: {e}")
                    time.sleep(0.1)  # Brief pause before retrying
                except AttributeError as e:
                    self.logger.error(f"BufferProxy attribute error: {e}")
                    # This could happen if pygame version doesn't support expected BufferProxy methods
                    time.sleep(0.1)  # Brief pause before retrying
                except OSError as e:
                    if e.errno == 28:  # No space left on device
                        # Try to recover by checking disk space and reopening the framebuffer
                        self.logger.error(f"Framebuffer write error: {e}")
                        self._check_disk_space()
                        
                        # Attempt to reopen the framebuffer
                        try:
                            if hasattr(self, 'fb'):
                                if self.use_mmap:
                                    self.fb.close()
                                else:
                                    self.fb.close()
                                    
                            # Try direct file approach if mmap failed before
                            self.fb = open('/dev/fb0', 'wb')
                            self.use_mmap = False
                            self.logger.info("Reopened framebuffer with direct writing")
                        except Exception as reopening_error:
                            self.logger.error(f"Failed to reopen framebuffer: {reopening_error}")
                            time.sleep(1.0)  # Avoid tight error loop
                    else:
                        # Some other error
                        self.logger.error(f"Framebuffer error: {e}")
                        time.sleep(0.5)
                
                clock.tick(self.config.fps_limit)
                
                # Record frame performance
                if self.performance_manager:
                    frame_time = self.performance_manager.record_frame()
                
                # Periodic performance logging
                frame_count += 1
                current_time = time.time()
                
                if current_time - last_performance_log >= 10.0:  # Log every 10 seconds
                    if self.performance_manager:
                        metrics = self.performance_manager.get_comprehensive_metrics()
                        self.logger.info(
                            f"Performance: {metrics['fps']:.1f} FPS, "
                            f"{metrics['frame_time_ms']:.1f}ms frame, "
                            f"{metrics['memory_usage_mb']:.1f}MB mem, "
                            f"{metrics['font_cache_hit_rate']:.1%} font cache hit"
                        )
                    else:
                        self.logger.debug(f"Display loop running, frame {frame_count}")
                    
                    last_performance_log = current_time
                
            except Exception as e:
                self.logger.error(f"Display error: {e}", exc_info=True)
                time.sleep(1.0)
        
        self.logger.info("Display loop ended")

    def _draw_splash_mode(self) -> None:
        """Draw splash screen and handle transition to normal mode"""
        try:
            if not self._splash_screen:
                # No splash screen available, transition immediately
                self.logger.warning("No splash screen available - transitioning to normal mode")
                self.config.mode = self._post_splash_mode
                return
                
            # Render the splash screen
            splash_success = self._splash_screen.render(self.back_surface)
            
            if not splash_success:
                self.logger.warning("Splash screen render failed - continuing with fallback")
            
            # Check if splash screen is complete
            if self._splash_screen.is_complete():
                # Transition to normal display mode
                self.config.mode = self._post_splash_mode
                self.logger.info(f"Splash screen completed - transitioning to {self._post_splash_mode.name} mode")
                
                # If setup mode was requested while splash was running, it will now be handled
                if self._in_setup_mode:
                    self.logger.info("Setup mode was requested during splash - will activate now")
                
                # Clean up splash screen resources if needed
                try:
                    self._splash_screen.reset()
                except Exception as e:
                    self.logger.error(f"Error resetting splash screen: {e}")
            
        except Exception as e:
            self.logger.error(f"Splash mode error: {e}", exc_info=True)
            # Transition to normal mode on error
            self.config.mode = self._post_splash_mode

    def _draw_digital_mode(self) -> None:
        """Draw digital RPM display"""
        try:
            try:
                rpm_data = self.thread_manager.message_queue.get_nowait()
                rpm = ((256 * rpm_data.data[0]) + rpm_data.data[1]) / 4
            except:
                rpm = 0
            
            if rpm >= self.config.rpm_danger:
                color = (255, 0, 0)  # Red
            elif rpm >= self.config.rpm_warning:
                color = (255, 165, 0)  # Orange
            else:
                color = (255, 255, 255)  # White
            
            # Use typography system for consistent font sizing (FONT_RPM_LARGE = 36px)
            try:
                font = get_rpm_large_font()
                if font:
                    self.logger.debug(f"Using RPM large font ({TypographyConstants.FONT_RPM_LARGE}px) for digital display")
                    text = font.render(f"{int(rpm)}", True, color)
                    text_rect = text.get_rect(center=(240, 240))
                    
                    # Validate text fits within circular display bounds
                    manager = get_font_manager()
                    if manager.validate_text_fits_circular_display(f"{int(rpm)}", TypographyConstants.FONT_RPM_LARGE):
                        self.back_surface.blit(text, text_rect)
                    else:
                        self.logger.warning(f"RPM text '{int(rpm)}' may not fit in circular display")
                        self.back_surface.blit(text, text_rect)  # Display anyway
                else:
                    # Fallback to pygame default font
                    self.logger.error("Failed to get RPM large font, using fallback")
                    fallback_font = pygame.font.Font(None, 32)  # Smaller fallback
                    text = fallback_font.render(f"{int(rpm)}", True, color)
                    text_rect = text.get_rect(center=(240, 240))
                    self.back_surface.blit(text, text_rect)
            except Exception as e:
                self.logger.error(f"Error rendering digital RPM display: {e}")
                # Emergency fallback
                try:
                    fallback_font = pygame.font.Font(None, 24)
                    text = fallback_font.render(f"{int(rpm)}", True, color)
                    text_rect = text.get_rect(center=(240, 240))
                    self.back_surface.blit(text, text_rect)
                except Exception as fallback_error:
                    self.logger.error(f"Emergency fallback failed: {fallback_error}")
            
        except Exception as e:
            self.logger.error(f"Digital display error: {e}")

    def _draw_gauge_mode(self) -> None:
        """Draw analog gauge display for RPM visualization.
        
        Renders a circular gauge with:
        - Tick marks for RPM ranges
        - Color-coded sections for normal, warning, and danger zones
        - A needle pointing to the current RPM value
        - Digital RPM readout in the center
        """
        try:
            # Get current RPM data from queue if available
            try:
                rpm_data = self.thread_manager.message_queue.get_nowait()
                rpm = ((256 * rpm_data.data[0]) + rpm_data.data[1]) / 4
            except:
                rpm = 0
            
            # Define gauge parameters
            center = (240, 240)
            radius = 200
            gauge_start = 135  # Degrees (left side)
            gauge_end = 45     # Degrees (right side)
            gauge_range = (gauge_start - gauge_end) % 360  # Total sweep angle
            
            max_rpm = 8000  # Maximum RPM to display
            
            # Draw gauge background (dark circle)
            pygame.draw.circle(self.back_surface, (30, 30, 30), center, radius)
            
            # Draw color zones (normal, warning, danger)
            # Each zone is a filled arc
            self._draw_gauge_zone(center, radius-10, radius-40, 
                                 0, self.config.rpm_warning, 
                                 max_rpm, gauge_start, gauge_end, 
                                 (0, 128, 0))  # Green for normal
            
            self._draw_gauge_zone(center, radius-10, radius-40, 
                                 self.config.rpm_warning, self.config.rpm_danger, 
                                 max_rpm, gauge_start, gauge_end, 
                                 (255, 165, 0))  # Orange for warning
            
            self._draw_gauge_zone(center, radius-10, radius-40, 
                                 self.config.rpm_danger, max_rpm, 
                                 max_rpm, gauge_start, gauge_end, 
                                 (255, 0, 0))  # Red for danger
            
            # Draw tick marks
            tick_interval = 1000  # RPM between major ticks
            for tick_rpm in range(0, max_rpm + 1, tick_interval):
                angle = gauge_start - (tick_rpm / max_rpm * gauge_range)
                angle_rad = math.radians(angle)
                
                # Calculate tick positions (outer and inner)
                start_x = center[0] + int((radius - 40) * math.cos(angle_rad))
                start_y = center[1] - int((radius - 40) * math.sin(angle_rad))
                end_x = center[0] + int((radius - 10) * math.cos(angle_rad))
                end_y = center[1] - int((radius - 10) * math.sin(angle_rad))
                
                # Draw tick line
                line_width = 3 if tick_rpm % 2000 == 0 else 1
                pygame.draw.line(self.back_surface, (255, 255, 255), 
                                (start_x, start_y), (end_x, end_y), line_width)
                
                # Draw RPM labels for even thousands (FONT_LABEL_SMALL = 16px)
                if tick_rpm % 2000 == 0:
                    try:
                        font = get_label_small_font()
                        if font:
                            self.logger.debug(f"Using label small font ({TypographyConstants.FONT_LABEL_SMALL}px) for gauge labels")
                        else:
                            # Fallback to gauge font system
                            font = get_font_manager().get_gauge_font("label")
                            if not font:
                                self.logger.warning("Failed to get gauge label font, skipping tick label")
                                continue
                    except Exception as e:
                        self.logger.error(f"Error getting gauge label font: {e}")
                        continue
                    # Position the label slightly inside the tick marks
                    label_x = center[0] + int((radius - 65) * math.cos(angle_rad))
                    label_y = center[1] - int((radius - 65) * math.sin(angle_rad))
                    
                    # Format RPM text (e.g., "4K" instead of "4000")
                    rpm_text = f"{tick_rpm//1000}K" if tick_rpm > 0 else "0"
                    text = font.render(rpm_text, True, (200, 200, 200))
                    text_rect = text.get_rect(center=(label_x, label_y))
                    self.back_surface.blit(text, text_rect)
            
            # Draw RPM needle
            if rpm > max_rpm:
                rpm = max_rpm  # Cap the value for display purposes
                
            needle_angle = gauge_start - (rpm / max_rpm * gauge_range)
            needle_angle_rad = math.radians(needle_angle)
            
            needle_length = radius - 50
            needle_tip_x = center[0] + int(needle_length * math.cos(needle_angle_rad))
            needle_tip_y = center[1] - int(needle_length * math.sin(needle_angle_rad))
            
            # Determine needle color based on RPM
            if rpm >= self.config.rpm_danger:
                needle_color = (255, 0, 0)  # Red
            elif rpm >= self.config.rpm_warning:
                needle_color = (255, 165, 0)  # Orange
            else:
                needle_color = (255, 255, 255)  # White
            
            # Draw the needle (thicker line)
            pygame.draw.line(self.back_surface, needle_color, center, 
                            (needle_tip_x, needle_tip_y), 4)
            
            # Draw central hub
            pygame.draw.circle(self.back_surface, (60, 60, 60), center, 40)
            pygame.draw.circle(self.back_surface, (100, 100, 100), center, 38)
            
            # Draw digital RPM readout in center using gauge typography (FONT_RPM_MEDIUM = 28px)
            try:
                font = get_rpm_medium_font()
                if font:
                    self.logger.debug(f"Using RPM medium font ({TypographyConstants.FONT_RPM_MEDIUM}px) for gauge center")
                    rpm_text = font.render(f"{int(rpm)}", True, needle_color)
                    rpm_rect = rpm_text.get_rect(center=center)
                    
                    # Validate text fits within gauge center area
                    manager = get_font_manager()
                    if manager.validate_text_fits_circular_display(f"{int(rpm)}", TypographyConstants.FONT_RPM_MEDIUM, center):
                        self.back_surface.blit(rpm_text, rpm_rect)
                    else:
                        self.logger.warning(f"Gauge RPM text '{int(rpm)}' may not fit in center area")
                        self.back_surface.blit(rpm_text, rpm_rect)  # Display anyway
                else:
                    # Fallback to gauge font system
                    self.logger.warning("Failed to get RPM medium font, using gauge font fallback")
                    font = get_font_manager().get_gauge_font("center")
                    if font:
                        rpm_text = font.render(f"{int(rpm)}", True, needle_color)
                        rpm_rect = rpm_text.get_rect(center=center)
                        self.back_surface.blit(rpm_text, rpm_rect)
                    else:
                        self.logger.error("All gauge font fallbacks failed")
            except Exception as e:
                self.logger.error(f"Error rendering gauge center RPM: {e}")
            
        except Exception as e:
            self.logger.error(f"Gauge display error: {e}", exc_info=True)

    def _draw_gauge_zone(self, center: Tuple[int, int], 
                        outer_radius: int, inner_radius: int,
                        start_rpm: int, end_rpm: int, max_rpm: int,
                        gauge_start: int, gauge_end: int,
                        color: Tuple[int, int, int]) -> None:
        """Helper method to draw a colored zone on the gauge.
        
        Args:
            center: Center point coordinates (x, y)
            outer_radius: Outer radius of the zone arc
            inner_radius: Inner radius of the zone arc
            start_rpm: RPM value where this zone starts
            end_rpm: RPM value where this zone ends
            max_rpm: Maximum RPM for scaling
            gauge_start: Starting angle of the gauge (degrees)
            gauge_end: Ending angle of the gauge (degrees)
            color: RGB color tuple for the zone
        """
        gauge_range = (gauge_start - gauge_end) % 360
        
        # Convert RPM values to angles
        start_angle = gauge_start - (start_rpm / max_rpm * gauge_range)
        end_angle = gauge_start - (end_rpm / max_rpm * gauge_range)
        
        # Draw a series of lines to approximate the arc section
        for angle in range(int(start_angle), int(end_angle), -1):
            angle_rad = math.radians(angle)
            cos_angle = math.cos(angle_rad)
            sin_angle = math.sin(angle_rad)
            
            inner_x = center[0] + int(inner_radius * cos_angle)
            inner_y = center[1] - int(inner_radius * sin_angle)
            outer_x = center[0] + int(outer_radius * cos_angle)
            outer_y = center[1] - int(outer_radius * sin_angle)
            
            pygame.draw.line(self.back_surface, color, 
                            (inner_x, inner_y), (outer_x, outer_y), 2)

    def _position_in_circle(self, angle_degrees: float, radius: float, 
                          element_size: tuple = (100, 30)) -> tuple:
        """Position an element within the circular display using polar coordinates.
        
        Args:
            angle_degrees: Angle in degrees (0 = right, 90 = down, 180 = left, 270 = up)
            radius: Distance from center (0 to safe_radius)
            element_size: (width, height) tuple of element dimensions
            
        Returns:
            tuple: (x, y, width, height) rectangle coordinates for pygame.Rect
        """
        try:
            # Input validation
            if radius < 0:
                raise ValueError("Radius must be non-negative")
            if radius > self.display_safe_radius:
                self.logger.warning(f"Radius {radius} exceeds safe radius {self.display_safe_radius}")
                radius = self.display_safe_radius
            
            # Convert angle to radians
            angle_radians = math.radians(angle_degrees)
            
            # Calculate position using polar coordinates
            center_x, center_y = self.display_center
            element_width, element_height = element_size
            
            # Position element center at the specified polar coordinates
            element_center_x = center_x + radius * math.cos(angle_radians)
            element_center_y = center_y + radius * math.sin(angle_radians)
            
            # Calculate top-left corner for pygame.Rect
            rect_x = int(element_center_x - element_width / 2)
            rect_y = int(element_center_y - element_height / 2)
            
            # Create rectangle coordinates
            rect_coords = (rect_x, rect_y, element_width, element_height)
            
            self.logger.debug(f"Positioned element: angle={angle_degrees}°, radius={radius}, "
                            f"size={element_size}, result={rect_coords}")
            
            return rect_coords
            
        except Exception as e:
            self.logger.error(f"Error positioning element in circle: {e}")
            # Return fallback position at center
            center_x, center_y = self.display_center
            return (center_x - element_size[0]//2, center_y - element_size[1]//2, 
                   element_size[0], element_size[1])

    def _render_compact_slider(self, surface, label: str, value: int, min_val: int, max_val: int, 
                             y_pos: int, slider_id: str, color: tuple = (100, 150, 250)) -> list:
        """
        Render a compact slider control with 55px total height.
        
        Args:
            surface: pygame surface to draw on
            label: Setting label text
            value: Current value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            y_pos: Y position for the slider
            slider_id: Unique identifier for touch handling
            color: Color for the slider track and thumb
            
        Returns:
            list: Touch regions for interaction
        """
        touch_regions = []
        
        try:
            # Get fonts using typography system
            try:
                label_font = self._get_cached_font(TypographyConstants.FONT_LABEL_SMALL)
                if not label_font:
                    label_font = pygame.font.Font(None, 18)
            except:
                label_font = pygame.font.Font(None, 18)
                
            try:
                value_font = self._get_cached_font(TypographyConstants.FONT_BODY)
                if not value_font:
                    value_font = pygame.font.Font(None, 20)
            except:
                value_font = pygame.font.Font(None, 20)
            
            # Layout parameters
            slider_height = 55
            track_width = 200
            track_height = 4
            thumb_diameter = 20
            
            # Calculate positions
            left_margin = 60
            right_margin = 60
            track_y = y_pos + slider_height // 2 - track_height // 2
            
            # Render label (left-aligned)
            label_surface = label_font.render(label, True, (200, 200, 200))
            label_rect = label_surface.get_rect(midleft=(left_margin, y_pos + slider_height // 2))
            surface.blit(label_surface, label_rect)
            
            # Calculate slider track position (centered between label and value display)
            available_width = 480 - left_margin - right_margin - 100  # Reserve space for value
            track_start_x = left_margin + 120  # Space after label
            track_end_x = track_start_x + track_width
            
            # Ensure track fits within safe circular area
            center_x, center_y = self.display_center
            max_track_x = center_x + self.display_safe_radius - 20
            if track_end_x > max_track_x:
                track_width = max_track_x - track_start_x
                track_end_x = track_start_x + track_width
            
            # Draw slider track
            track_rect = pygame.Rect(track_start_x, track_y, track_width, track_height)
            pygame.draw.rect(surface, (80, 80, 80), track_rect, border_radius=2)
            
            # Calculate thumb position based on value
            value_range = max_val - min_val
            if value_range > 0:
                normalized_value = (value - min_val) / value_range
                thumb_x = track_start_x + (track_width * normalized_value)
            else:
                thumb_x = track_start_x + track_width // 2
            
            thumb_y = y_pos + slider_height // 2
            
            # Draw slider track fill (progress indication)
            if value > min_val:
                fill_width = (value - min_val) / value_range * track_width
                fill_rect = pygame.Rect(track_start_x, track_y, fill_width, track_height)
                # Use a slightly darker version of the color for the fill
                fill_color = tuple(max(0, c - 40) for c in color)
                pygame.draw.rect(surface, fill_color, fill_rect, border_radius=2)
            
            # Draw slider thumb with visual feedback
            # Base thumb (main color)
            pygame.draw.circle(surface, color, (int(thumb_x), int(thumb_y)), thumb_diameter // 2)
            
            # Inner highlight for depth
            inner_color = tuple(min(255, c + 30) for c in color)
            pygame.draw.circle(surface, inner_color, (int(thumb_x), int(thumb_y)), thumb_diameter // 2 - 3)
            
            # Outer border for definition
            pygame.draw.circle(surface, (255, 255, 255), (int(thumb_x), int(thumb_y)), thumb_diameter // 2, 2)
            
            # Add subtle shadow effect
            shadow_offset = 2
            shadow_color = (20, 20, 20, 50)  # Semi-transparent dark
            try:
                pygame.draw.circle(surface, shadow_color[:3], 
                                 (int(thumb_x + shadow_offset), int(thumb_y + shadow_offset)), 
                                 thumb_diameter // 2)
            except:
                pass  # Skip shadow if alpha not supported
            
            # Render value (right-aligned)
            value_text = f"{value}"
            value_surface = value_font.render(value_text, True, color)
            value_rect = value_surface.get_rect(midright=(480 - right_margin, y_pos + slider_height // 2))
            surface.blit(value_surface, value_rect)
            
            # Create touch region (full height for easy interaction)
            touch_rect = pygame.Rect(track_start_x - 20, y_pos, track_width + 40, slider_height)
            touch_regions.append((slider_id, touch_rect, {
                'type': 'slider',
                'track_start_x': track_start_x,
                'track_width': track_width,
                'min_val': min_val,
                'max_val': max_val,
                'current_value': value
            }))
            
            self.logger.debug(f"Rendered compact slider '{label}': value={value}, "
                            f"track=({track_start_x}, {track_y}, {track_width}, {track_height})")
            
        except Exception as e:
            self.logger.error(f"Error rendering compact slider '{label}': {e}")
        
        return touch_regions

    def _draw_settings_mode(self) -> None:
        """Draw minimalist settings interface with compact slider controls."""
        try:
            # Background
            pygame.draw.rect(self.back_surface, (40, 40, 50), (0, 0, 480, 480))
            
            # Title using title typography (FONT_TITLE = 36px) at y=40
            try:
                font_title = get_title_display_font()
                if font_title:
                    self.logger.debug(f"Using title font ({TypographyConstants.FONT_TITLE}px) for settings header")
                    title = font_title.render("Settings", True, (255, 255, 255))
                    title_rect = title.get_rect(center=(240, 40))
                    
                    # Validate title fits in circular display
                    manager = get_font_manager()
                    if manager.validate_text_fits_circular_display("Settings", TypographyConstants.FONT_TITLE, (240, 40)):
                        self.back_surface.blit(title, title_rect)
                    else:
                        self.logger.warning("Settings title may not fit in circular display")
                        self.back_surface.blit(title, title_rect)  # Display anyway
                else:
                    # Fallback to medium font
                    self.logger.warning("Failed to get title font, using medium font fallback")
                    font_title = get_medium_font()
                    if font_title:
                        title = font_title.render("Settings", True, (255, 255, 255))
                        title_rect = title.get_rect(center=(240, 40))
                        self.back_surface.blit(title, title_rect)
                    else:
                        self.logger.error("All settings title font fallbacks failed")
            except Exception as e:
                self.logger.error(f"Error rendering settings title: {e}")
            
            # Store touch regions for interaction
            self.settings_regions = []
            
            # Mode selector: Compact segmented control (30px height) at y=85
            try:
                self._render_mode_selector(self.back_surface, 85)
            except Exception as e:
                self.logger.error(f"Error rendering mode selector: {e}")
            
            # Warning RPM slider at y=120 (orange color) - moved up for better spacing
            try:
                warning_regions = self._render_compact_slider(
                    self.back_surface,
                    "Warning RPM:",
                    self.config.rpm_warning,
                    1000,  # min value
                    8000,  # max value  
                    120,
                    "warning_rpm",
                    (255, 165, 0)  # Orange color
                )
                self.settings_regions.extend(warning_regions)
                self.logger.debug(f"Warning RPM slider: current value={self.config.rpm_warning}")
            except Exception as e:
                self.logger.error(f"Error rendering warning RPM slider: {e}")
            
            # Danger RPM slider at y=170 (red color) - compact spacing with warning slider
            try:
                danger_regions = self._render_compact_slider(
                    self.back_surface,
                    "Danger RPM:",
                    self.config.rpm_danger,
                    1000,  # min value
                    9000,  # max value
                    170,
                    "danger_rpm", 
                    (255, 50, 50)  # Red color
                )
                self.settings_regions.extend(danger_regions)
                self.logger.debug(f"Danger RPM slider: current value={self.config.rpm_danger}")
            except Exception as e:
                self.logger.error(f"Error rendering danger RPM slider: {e}")
            
            # Save button: Floating button (44x44) at 225°, 160px radius using standardized system
            try:
                button_renderer = get_button_renderer()
                
                # Save button colors (green background with white border and icon)
                save_colors = {
                    'background': (0, 150, 0),      # Green background
                    'border': (255, 255, 255),      # White border  
                    'text': (255, 255, 255)         # White text/icon
                }
                
                # Render save button using standardized system
                visual_rect, touch_rect = button_renderer.render_button(
                    surface=self.back_surface,
                    position=(0, 0),  # Will be overridden by circular_position
                    text="✓",  # Checkmark icon
                    button_size=ButtonSize.FLOATING,  # 44x44 standardized size
                    button_id="save",
                    state=ButtonState.NORMAL,
                    colors=save_colors,
                    circular_position=(225, 160)  # angle, radius
                )
                
                # Add to touch regions (use touch_rect for expanded hit area)
                self.settings_regions.append(("save", touch_rect))
                self.logger.debug(f"Standardized save button rendered with touch region: {touch_rect}")
                
            except Exception as e:
                self.logger.error(f"Error rendering save button: {e}")
            
            # Instructions at bottom
            try:
                small_font = get_label_small_font()
                if not small_font:
                    small_font = pygame.font.Font(None, 16)
                    
                hint = small_font.render("Long press anywhere to exit settings", True, (150, 150, 150))
                hint_rect = hint.get_rect(center=(240, 420))
                self.back_surface.blit(hint, hint_rect)
            except Exception as e:
                self.logger.error(f"Error rendering instructions: {e}")
            
            self.logger.debug(f"Settings interface rendered with {len(self.settings_regions)} touch regions")
            
        except Exception as e:
            self.logger.error(f"Settings display error: {e}", exc_info=True)

    def _render_mode_selector(self, surface, y_pos: int) -> None:
        """
        Render compact segmented control for display mode selection.
        
        Args:
            surface: pygame surface to draw on
            y_pos: Y position for the selector
        """
        try:
            # Layout parameters
            selector_height = 30
            segment_width = 80
            total_width = segment_width * 2
            selector_x = 240 - total_width // 2  # Center horizontally
            
            # Get font
            try:
                font = get_font_manager().get_font(16)
                if not font:
                    font = pygame.font.Font(None, 16)
            except:
                font = pygame.font.Font(None, 16)
            
            # Current mode
            is_digital = self.config.mode == DisplayMode.DIGITAL
            
            # Draw segments
            # Digital segment (left)
            digital_rect = pygame.Rect(selector_x, y_pos, segment_width, selector_height)
            digital_color = (100, 150, 250) if is_digital else (80, 80, 80)
            try:
                pygame.draw.rect(surface, digital_color, digital_rect, border_radius=6)
            except TypeError:
                pygame.draw.rect(surface, digital_color, digital_rect)
            
            digital_text_color = (255, 255, 255) if is_digital else (180, 180, 180)
            digital_text = font.render("DIGITAL", True, digital_text_color)
            digital_text_rect = digital_text.get_rect(center=digital_rect.center)
            surface.blit(digital_text, digital_text_rect)
            
            # Gauge segment (right)
            gauge_rect = pygame.Rect(selector_x + segment_width, y_pos, segment_width, selector_height)
            gauge_color = (100, 150, 250) if not is_digital else (80, 80, 80)
            try:
                pygame.draw.rect(surface, gauge_color, gauge_rect, border_radius=6)
            except TypeError:
                pygame.draw.rect(surface, gauge_color, gauge_rect)
                
            gauge_text_color = (255, 255, 255) if not is_digital else (180, 180, 180)
            gauge_text = font.render("GAUGE", True, gauge_text_color)
            gauge_text_rect = gauge_text.get_rect(center=gauge_rect.center)
            surface.blit(gauge_text, gauge_text_rect)
            
            # Add touch regions
            self.settings_regions.append(("mode_digital", digital_rect))
            self.settings_regions.append(("mode_gauge", gauge_rect))
            
            self.logger.debug(f"Mode selector rendered: current mode={'DIGITAL' if is_digital else 'GAUGE'}")
            
        except Exception as e:
            self.logger.error(f"Error rendering mode selector: {e}")

    def _handle_slider_interaction(self, pos: Tuple[int, int], slider_data: dict) -> bool:
        """
        Handle slider touch interaction with drag functionality.
        
        Args:
            pos: Touch position (x, y)
            slider_data: Slider metadata including track bounds and value range
        
        Returns:
            bool: True if interaction was handled
        """
        try:
            touch_x, touch_y = pos
            track_start_x = slider_data['track_start_x']
            track_width = slider_data['track_width']
            min_val = slider_data['min_val']
            max_val = slider_data['max_val']
            
            # Calculate normalized position on track (0.0 to 1.0)
            relative_x = touch_x - track_start_x
            normalized_pos = max(0.0, min(1.0, relative_x / track_width))
            
            # Convert to value in range
            value_range = max_val - min_val
            new_value = int(min_val + (normalized_pos * value_range))
            
            self.logger.debug(f"Slider interaction: pos=({touch_x}, {touch_y}), "
                            f"normalized={normalized_pos:.3f}, new_value={new_value}")
            
            return self._update_slider_value(slider_data, new_value)
            
        except Exception as e:
            self.logger.error(f"Error handling slider interaction: {e}")
            return False

    def _update_slider_value(self, slider_data: dict, new_value: int) -> bool:
        """
        Update slider value with validation and constraint enforcement.
        
        Args:
            slider_data: Slider metadata
            new_value: New value to set
            
        Returns:
            bool: True if value was updated successfully
        """
        try:
            # Apply bounds checking
            min_val = slider_data['min_val']
            max_val = slider_data['max_val']
            clamped_value = max(min_val, min(max_val, new_value))
            
            if clamped_value != new_value:
                self.logger.debug(f"Value clamped: {new_value} -> {clamped_value}")
            
            # Apply constraint validation (prevent warning > danger)
            current_warning = getattr(self.config, 'rpm_warning', 3000)
            current_danger = getattr(self.config, 'rpm_danger', 5000)
            
            # Determine which slider is being updated
            if 'warning' in str(slider_data):
                # Updating warning RPM - ensure it doesn't exceed danger RPM
                if clamped_value >= current_danger:
                    clamped_value = current_danger - 100  # Leave 100 RPM buffer
                    self.logger.debug(f"Warning RPM constrained to stay below danger: {clamped_value}")
                
                # Update config
                old_value = self.config.rpm_warning
                self.config.rpm_warning = clamped_value
                self.logger.info(f"Warning RPM updated: {old_value} -> {clamped_value}")
                
            elif 'danger' in str(slider_data):
                # Updating danger RPM - ensure it doesn't go below warning RPM
                if clamped_value <= current_warning:
                    clamped_value = current_warning + 100  # Leave 100 RPM buffer
                    self.logger.debug(f"Danger RPM constrained to stay above warning: {clamped_value}")
                
                # Update config
                old_value = self.config.rpm_danger
                self.config.rpm_danger = clamped_value
                self.logger.info(f"Danger RPM updated: {old_value} -> {clamped_value}")
            
            else:
                self.logger.warning(f"Unknown slider type in data: {slider_data}")
                return False
            
            # Update slider data for next interaction
            slider_data['current_value'] = clamped_value
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating slider value: {e}")
            return False

    def _start_slider_drag(self, pos: Tuple[int, int], slider_id: str, slider_data: dict) -> None:
        """
        Initialize slider drag state.
        
        Args:
            pos: Initial touch position
            slider_id: Unique slider identifier
            slider_data: Slider metadata
        """
        try:
            self._slider_drag_state = {
                'active': True,
                'slider_id': slider_id,
                'initial_touch_pos': pos,
                'initial_value': slider_data['current_value']
            }
            
            self.logger.debug(f"Started slider drag: {slider_id} at {pos}")
            
        except Exception as e:
            self.logger.error(f"Error starting slider drag: {e}")

    def _continue_slider_drag(self, pos: Tuple[int, int]) -> bool:
        """
        Continue active slider drag operation.
        
        Args:
            pos: Current touch position
            
        Returns:
            bool: True if drag continued successfully
        """
        try:
            if not self._slider_drag_state['active']:
                return False
            
            # Find the active slider in settings regions
            slider_id = self._slider_drag_state['slider_id']
            
            for region_id, rect, data in self.settings_regions:
                if region_id == slider_id and data.get('type') == 'slider':
                    return self._handle_slider_interaction(pos, data)
            
            self.logger.warning(f"Active slider {slider_id} not found in regions")
            return False
            
        except Exception as e:
            self.logger.error(f"Error continuing slider drag: {e}")
            return False

    def _end_slider_drag(self) -> None:
        """End active slider drag operation."""
        try:
            if self._slider_drag_state['active']:
                slider_id = self._slider_drag_state['slider_id']
                self.logger.debug(f"Ended slider drag: {slider_id}")
                
                self._slider_drag_state = {
                    'active': False,
                    'slider_id': None,
                    'initial_touch_pos': None,
                    'initial_value': None
                }
                
        except Exception as e:
            self.logger.error(f"Error ending slider drag: {e}")

    def _render_edge_indicators(self) -> None:
        """
        Render subtle edge indicators for available navigation gestures.
        
        Shows semi-transparent chevrons at screen edges with auto-hide functionality.
        """
        try:
            if not self.gesture_handler or not self.gesture_handler.should_show_edge_indicators():
                return
            
            # Get current alpha for fade effect
            alpha = self.gesture_handler.get_edge_indicator_alpha()
            if alpha <= 0:
                return
            
            # Edge indicator parameters
            indicator_size = self.config.gesture_edge_indicator_size
            indicator_height = 40
            
            # Screen dimensions
            screen_width = 480
            screen_height = 480
            center_y = screen_height // 2
            
            # Left edge indicator (< chevron)
            left_x = 10
            left_points = [
                (left_x + indicator_size, center_y - indicator_height // 2),
                (left_x, center_y),
                (left_x + indicator_size, center_y + indicator_height // 2)
            ]
            
            # Right edge indicator (> chevron)
            right_x = screen_width - 10 - indicator_size
            right_points = [
                (right_x, center_y - indicator_height // 2),
                (right_x + indicator_size, center_y),
                (right_x, center_y + indicator_height // 2)
            ]
            
            # Get navigation context to determine which indicators to show
            context = self._get_gesture_navigation_context()
            
            # Draw left indicator (back/previous)
            if self._should_show_left_indicator(context):
                self._draw_chevron(left_points, alpha, (180, 180, 180))
            
            # Draw right indicator (forward/next)
            if self._should_show_right_indicator(context):
                self._draw_chevron(right_points, alpha, (180, 180, 180))
                
        except Exception as e:
            self.logger.error(f"Error rendering edge indicators: {e}")
    
    def _draw_chevron(self, points: list, alpha: int, color: tuple) -> None:
        """Draw a chevron indicator with specified alpha."""
        try:
            if not PYGAME_AVAILABLE:
                return
            
            # Create surface with alpha for transparency
            chevron_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
            
            # Draw chevron lines
            line_color = (*color, alpha)
            pygame.draw.lines(chevron_surface, line_color[:3], False, 
                            [(p[0] - points[0][0] + 20, p[1] - points[0][1] + 20) for p in points], 3)
            
            # Set alpha and blit to main surface
            chevron_surface.set_alpha(alpha)
            self.back_surface.blit(chevron_surface, (points[0][0] - 20, points[0][1] - 20))
            
        except Exception as e:
            self.logger.error(f"Error drawing chevron: {e}")
    
    def _get_gesture_navigation_context(self) -> str:
        """Get current context for gesture navigation."""
        try:
            if self.is_in_setup_mode():
                return "setup"
            elif self.config.mode == DisplayMode.SETTINGS:
                return "settings"
            else:
                return "main"
        except:
            return "main"
    
    def _should_show_left_indicator(self, context: str) -> bool:
        """Determine if left indicator should be shown."""
        if context == "setup":
            return True  # Always show back in setup
        elif context == "settings":
            return True  # Show exit gesture
        else:
            return True  # Show mode switching
    
    def _should_show_right_indicator(self, context: str) -> bool:
        """Determine if right indicator should be shown."""
        if context == "setup":
            return False  # Usually no forward in setup
        elif context == "settings":
            return True   # Show exit gesture
        else:
            return True   # Show mode switching

    def add_gesture_visual_feedback(self, gesture_type: str, start_pos: tuple, end_pos: tuple) -> None:
        """
        Add visual feedback for completed gestures.
        
        Args:
            gesture_type: Type of gesture performed
            start_pos: Starting position of gesture
            end_pos: Ending position of gesture
        """
        try:
            if not PYGAME_AVAILABLE:
                return
            
            # Create subtle edge glow effect for successful navigation
            self._create_edge_glow_effect(gesture_type, start_pos, end_pos)
            
            self.logger.debug(f"Added visual feedback for {gesture_type} gesture")
            
        except Exception as e:
            self.logger.error(f"Error adding gesture visual feedback: {e}")
    
    def _create_edge_glow_effect(self, gesture_type: str, start_pos: tuple, end_pos: tuple) -> None:
        """Create edge glow effect for gesture feedback."""
        try:
            # Determine edge based on gesture type
            edge_x = 0
            if 'right' in gesture_type.lower():
                edge_x = 460  # Right edge
            elif 'left' in gesture_type.lower():
                edge_x = 20   # Left edge
            else:
                return  # No edge glow for vertical gestures
            
            # Create glow surface
            glow_width = 20
            glow_height = 100
            glow_surface = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
            
            # Create gradient effect
            for i in range(glow_width):
                alpha = int(255 * (1.0 - (i / glow_width)) * 0.3)  # Max 30% opacity
                color = (100, 150, 250, alpha)  # Blue glow
                pygame.draw.line(glow_surface, color[:3], (i, 0), (i, glow_height))
            
            glow_surface.set_alpha(int(255 * 0.3))
            
            # Position and blit glow
            glow_y = 240 - glow_height // 2  # Vertical center
            self.back_surface.blit(glow_surface, (edge_x - glow_width // 2, glow_y))
            
        except Exception as e:
            self.logger.error(f"Error creating edge glow effect: {e}")
    
    def transition_to_mode(self, new_mode: DisplayMode, transition_type: str = "slide") -> None:
        """
        Transition to new display mode with animation.
        
        Args:
            new_mode: Target display mode
            transition_type: Type of transition animation
        """
        try:
            if new_mode == self.config.mode:
                return  # Already in target mode
            
            old_mode = self.config.mode
            transition_duration = self.config.gesture_transition_duration
            
            self.logger.info(f"Transitioning from {old_mode.name} to {new_mode.name} "
                           f"with {transition_type} animation ({transition_duration}s)")
            
            # For now, do immediate transition
            # TODO: Implement smooth slide animations
            self.config.mode = new_mode
            
            # Add subtle visual feedback
            if hasattr(self, 'gesture_handler'):
                # Create mock gesture event for feedback
                center_pos = (240, 240)
                self.add_gesture_visual_feedback(f"transition_{transition_type}", center_pos, center_pos)
            
        except Exception as e:
            self.logger.error(f"Error transitioning to mode {new_mode}: {e}")

    def _draw_status_indicator(self) -> None:
        """Draw connection status indicator"""
        try:
            # Check if bluetooth thread exists and is registered
            if 'bluetooth' not in self.thread_manager.threads:
                status = ConnectionStatus.DISCONNECTED
            else:
                # Map ThreadStatus to ConnectionStatus
                thread_status = self.thread_manager.threads['bluetooth'].status
                if thread_status == ThreadStatus.RUNNING:
                    status = ConnectionStatus.CONNECTED
                elif thread_status == ThreadStatus.STARTING:
                    status = ConnectionStatus.CONNECTING
                else:  # STOPPING, STOPPED, FAILED
                    status = ConnectionStatus.DISCONNECTED
            
            color = pygame.Color(status.value)
            pygame.draw.circle(self.back_surface, color, (20, 20), 5)
            
        except Exception as e:
            self.logger.error(f"Status indicator error: {e}")

    def _draw_setup_mode_fallback(self) -> None:
        """Draw basic setup mode indicator when setup manager fails"""
        try:
            # Check if font is initialized
            if not pygame.font.get_init():
                pygame.font.init()
            
            # Draw setup mode indicator using heading typography (FONT_HEADING = 28px)
            try:
                font = get_heading_font()
                if font:
                    self.logger.debug(f"Using heading font ({TypographyConstants.FONT_HEADING}px) for setup mode indicator")
                    text = font.render("SETUP MODE", True, (255, 255, 0))
                    text_rect = text.get_rect(center=(240, 240))
                    
                    # Validate setup mode text fits
                    manager = get_font_manager()
                    if manager.validate_text_fits_circular_display("SETUP MODE", TypographyConstants.FONT_HEADING):
                        self.back_surface.blit(text, text_rect)
                    else:
                        self.logger.warning("Setup mode text may not fit in circular display")
                        self.back_surface.blit(text, text_rect)  # Display anyway
                else:
                    # Fallback to medium font
                    self.logger.warning("Failed to get heading font, using medium font fallback")
                    font = get_medium_font()
                    if font:
                        text = font.render("SETUP MODE", True, (255, 255, 0))
                        text_rect = text.get_rect(center=(240, 240))
                        self.back_surface.blit(text, text_rect)
                    else:
                        self.logger.error("All setup mode font fallbacks failed")
            except Exception as e:
                self.logger.error(f"Error rendering setup mode indicator: {e}")
            
            # Draw border to make it obvious
            pygame.draw.rect(self.back_surface, (255, 255, 0), (0, 0, 480, 480), 3)
            
        except Exception as e:
            self.logger.error(f"Setup mode fallback error: {e}")

    
        
    def change_mode(self, mode: DisplayMode) -> None:
        """Change display mode"""
        self.config.mode = mode
        self._save_config()
    
    def set_setup_mode(self, setup_manager) -> None:
        """Enable setup mode with the given setup manager"""
        self._setup_manager = setup_manager
        self._in_setup_mode = True
        self.logger.info(f"Entered setup mode (current display mode: {self.config.mode.name})")
    
    def exit_setup_mode(self) -> None:
        """Exit setup mode and return to normal display"""
        self._in_setup_mode = False
        self._setup_manager = None
        self.logger.info(f"Exited setup mode (current display mode: {self.config.mode.name})")
    
    def is_in_setup_mode(self) -> bool:
        """Check if currently in setup mode"""
        return self._in_setup_mode
    
    def handle_touch_event(self, pos: Tuple[int, int]) -> Optional[object]:
        """Handle touch events and route them to appropriate handlers"""
        start_time = time.time()
        try:
            self.logger.info(f"Touch event received at position: {pos}")
            self.logger.debug(f"Current state - Display mode: {self.config.mode.name}, Setup mode: {self._in_setup_mode}")
            
            # Validate coordinates
            if not self._validate_touch_coordinates(pos):
                self.logger.warning(f"Invalid touch coordinates: {pos}")
                return None
            
            # Route touch events based on current mode
            if self._in_setup_mode and self._setup_manager:
                self.logger.info("Routing touch event to setup manager")
                self.logger.debug(f"Setup manager type: {type(self._setup_manager).__name__}")
                try:
                    action = self._setup_manager.handle_touch_event(pos)
                    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                    self.logger.info(f"Setup manager returned action: {action} (processed in {processing_time:.2f}ms)")
                    
                    # Log action details if available
                    if action and hasattr(action, 'name'):
                        self.logger.info(f"Action name: {action.name}")
                        
                    return action
                except Exception as e:
                    self.logger.error(f"Setup manager touch handling error: {e}", exc_info=True)
                    # Error recovery: attempt to recover setup manager state
                    self._attempt_setup_recovery(e)
                    return None
                    
            elif self.config.mode == DisplayMode.SETTINGS:
                # Handle settings mode touch interactions
                self.logger.info("Handling settings mode touch event")
                try:
                    return self._handle_settings_touch(pos)
                except Exception as e:
                    self.logger.error(f"Settings touch handling error: {e}", exc_info=True)
                    return None
                    
            else:
                # Handle other modes if needed in the future
                self.logger.info(f"Touch event not routed - Setup mode: {self._in_setup_mode}, Display mode: {self.config.mode.name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Touch event handling error: {e}", exc_info=True)
            return None

    def _handle_settings_touch(self, pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle touch events in settings mode with slider support.
        
        Args:
            pos: Touch position (x, y)
            
        Returns:
            str: Action taken or None
        """
        try:
            x, y = pos
            
            # Check if we're continuing an active slider drag
            if self._slider_drag_state['active']:
                if self._continue_slider_drag(pos):
                    return "slider_drag_continue"
                else:
                    self._end_slider_drag()
                    return "slider_drag_end"
            
            # Check for touches on settings regions
            if not hasattr(self, 'settings_regions') or not self.settings_regions:
                self.logger.warning("No settings regions available for touch handling")
                return None
            
            for region_id, rect, data in self.settings_regions:
                if rect.collidepoint(x, y):
                    self.logger.info(f"Touch hit region: {region_id}")
                    
                    # Handle different types of settings controls
                    if data and data.get('type') == 'slider':
                        # Start slider interaction
                        self._start_slider_drag(pos, region_id, data)
                        self._handle_slider_interaction(pos, data)
                        return f"slider_interaction_{region_id}"
                    
                    elif region_id == "mode_digital":
                        # Switch to digital mode
                        self.config.mode = DisplayMode.DIGITAL
                        self.logger.info("Switched to DIGITAL mode")
                        return "mode_change_digital"
                    
                    elif region_id == "mode_gauge":
                        # Switch to gauge mode  
                        self.config.mode = DisplayMode.GAUGE
                        self.logger.info("Switched to GAUGE mode")
                        return "mode_change_gauge"
                    
                    elif region_id == "save":
                        # Save configuration
                        try:
                            self._save_config()
                            self.logger.info("Settings saved successfully")
                            return "settings_saved"
                        except Exception as e:
                            self.logger.error(f"Error saving settings: {e}")
                            return "settings_save_error"
                    
                    else:
                        self.logger.info(f"Unhandled settings region: {region_id}")
                        return f"unhandled_{region_id}"
            
            # No region hit - this might be a long press to exit settings
            # (The long press logic would be handled by the TouchHandler)
            self.logger.debug(f"Touch at {pos} did not hit any settings region")
            return None
            
        except Exception as e:
            self.logger.error(f"Error handling settings touch: {e}")
            return None
    
    def _validate_touch_coordinates(self, pos: Tuple[int, int]) -> bool:
        """Validate touch coordinates are within display bounds"""
        try:
            x, y = pos
            # Assuming 480x480 display (HyperPixel 2" Round)
            if 0 <= x <= 480 and 0 <= y <= 480:
                return True
            else:
                self.logger.warning(f"Touch coordinates {pos} outside display bounds (0-480)")
                return False
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid touch coordinate format: {pos}, error: {e}")
            return False
    
    def get_display_state(self) -> dict:
        """Get current display state for debugging and validation"""
        try:
            state = {
                'display_mode': self.config.mode.name,
                'in_setup_mode': self._in_setup_mode,
                'setup_manager_available': self._setup_manager is not None,
                'splash_screen_available': self._splash_screen is not None,
                'touch_handler_available': self.touch_handler is not None,
                'timestamp': time.time()
            }
            
            # Add splash screen state if available
            if self._splash_screen:
                state['splash_complete'] = self._splash_screen.is_complete()
                if hasattr(self._splash_screen, 'duration'):
                    state['splash_duration'] = self._splash_screen.duration
                if hasattr(self._splash_screen, '_start_time'):
                    state['splash_start_time'] = self._splash_screen._start_time
                    
            # Add setup manager state if available
            if self._setup_manager:
                state['setup_manager_type'] = type(self._setup_manager).__name__
                if hasattr(self._setup_manager, 'state'):
                    state['setup_state'] = {
                        'current_screen': self._setup_manager.state.current_screen.name,
                        'discovered_devices': len(self._setup_manager.state.discovered_devices),
                        'pairing_status': self._setup_manager.state.pairing_status.name,
                        'setup_complete': self._setup_manager.state.setup_complete
                    }
                    
            return state
            
        except Exception as e:
            self.logger.error(f"Error getting display state: {e}")
            return {'error': str(e)}
    
    def validate_splash_to_setup_transition(self) -> dict:
        """Validate the splash screen to setup mode transition"""
        try:
            validation_result = {
                'valid': True,
                'issues': [],
                'state': self.get_display_state()
            }
            
            # Check if splash screen is properly configured
            if not self._splash_screen:
                validation_result['valid'] = False
                validation_result['issues'].append("Splash screen not initialized")
            elif not hasattr(self._splash_screen, 'is_complete'):
                validation_result['valid'] = False
                validation_result['issues'].append("Splash screen missing is_complete method")
                
            # Check if setup mode is properly configured
            if self._in_setup_mode and not self._setup_manager:
                validation_result['valid'] = False
                validation_result['issues'].append("Setup mode active but no setup manager")
                
            # Check touch handler availability
            if not self.touch_handler:
                validation_result['valid'] = False
                validation_result['issues'].append("Touch handler not available")
                
            # Check display mode consistency
            if self.config.mode.name == 'SPLASH' and self._in_setup_mode:
                validation_result['issues'].append("Warning: Both splash and setup mode active (expected during transition)")
                
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Validation error: {e}"],
                'state': {}
            }
    
    def log_state_transition(self, from_state: str, to_state: str, trigger: str = None):
        """Log state transitions for debugging"""
        try:
            transition_info = {
                'from': from_state,
                'to': to_state,
                'trigger': trigger,
                'timestamp': time.time(),
                'current_state': self.get_display_state()
            }
            
            self.logger.info(f"State transition: {from_state} -> {to_state}" + 
                           (f" (trigger: {trigger})" if trigger else ""))
            self.logger.debug(f"Transition details: {transition_info}")
            
        except Exception as e:
            self.logger.error(f"Error logging state transition: {e}")
    
    def _attempt_setup_recovery(self, error: Exception):
        """Attempt to recover from setup manager errors"""
        try:
            self.logger.info("Attempting setup manager recovery")
            
            # Check if setup manager is still responsive
            if self._setup_manager:
                try:
                    # Try to get the current state
                    if hasattr(self._setup_manager, 'state'):
                        current_state = self._setup_manager.state
                        self.logger.info(f"Setup manager state: {current_state.current_screen.name}")
                        
                        # Check if we can reset touch regions
                        if hasattr(self._setup_manager, 'touch_regions'):
                            self._setup_manager.touch_regions.clear()
                            self.logger.info("Cleared touch regions for recovery")
                            
                    # Log recovery attempt
                    self.logger.info("Setup manager recovery attempt completed")
                    
                except Exception as recovery_error:
                    self.logger.error(f"Setup manager recovery failed: {recovery_error}")
                    self._setup_manager = None
                    self._in_setup_mode = False
                    self.logger.warning("Setup manager disabled due to recovery failure")
            
        except Exception as e:
            self.logger.error(f"Error during setup recovery: {e}")
    
    def test_touch_functionality(self) -> dict:
        """Test touch functionality and return results"""
        try:
            results = {
                'touch_handler_available': self.touch_handler is not None,
                'touch_interface_info': None,
                'test_simulation_result': None
            }
            
            if self.touch_handler:
                # Get touch interface info
                results['touch_interface_info'] = self.touch_handler.get_touch_interface_info()
                
                # Test simulation if available
                try:
                    self.touch_handler.test_touch_simulation()
                    results['test_simulation_result'] = 'Success'
                except Exception as e:
                    results['test_simulation_result'] = f'Failed: {e}'
            else:
                results['test_simulation_result'] = 'No touch handler available'
                
            return results
            
        except Exception as e:
            self.logger.error(f"Touch functionality test failed: {e}")
            return {'error': str(e)}
    
    def test_complete_touch_flow(self) -> dict:
        """Test complete touch event flow integration"""
        try:
            self.logger.info("Starting complete touch flow integration test")
            
            test_results = {
                'success': True,
                'tests_passed': 0,
                'tests_failed': 0,
                'test_details': [],
                'state_validation': self.validate_splash_to_setup_transition()
            }
            
            # Test 1: Validate touch coordinate handling
            test_coords = [(240, 240), (0, 0), (480, 480), (500, 500)]
            for coords in test_coords:
                try:
                    valid = self._validate_touch_coordinates(coords)
                    expected = coords[0] <= 480 and coords[1] <= 480 and coords[0] >= 0 and coords[1] >= 0
                    if valid == expected:
                        test_results['tests_passed'] += 1
                        test_results['test_details'].append(f"Coordinate validation {coords}: PASS")
                    else:
                        test_results['tests_failed'] += 1
                        test_results['test_details'].append(f"Coordinate validation {coords}: FAIL")
                        test_results['success'] = False
                except Exception as e:
                    test_results['tests_failed'] += 1
                    test_results['test_details'].append(f"Coordinate validation {coords}: ERROR - {e}")
                    test_results['success'] = False
            
            # Test 2: Test touch routing without setup mode
            try:
                old_setup_mode = self._in_setup_mode
                self._in_setup_mode = False
                
                result = self.handle_touch_event((240, 240))
                if result is None:
                    test_results['tests_passed'] += 1
                    test_results['test_details'].append("Touch routing without setup mode: PASS")
                else:
                    test_results['tests_failed'] += 1
                    test_results['test_details'].append("Touch routing without setup mode: FAIL")
                    test_results['success'] = False
                    
                self._in_setup_mode = old_setup_mode
                
            except Exception as e:
                test_results['tests_failed'] += 1
                test_results['test_details'].append(f"Touch routing without setup mode: ERROR - {e}")
                test_results['success'] = False
            
            # Test 3: Test state validation
            try:
                state = self.get_display_state()
                if 'error' not in state:
                    test_results['tests_passed'] += 1
                    test_results['test_details'].append("State validation: PASS")
                else:
                    test_results['tests_failed'] += 1
                    test_results['test_details'].append("State validation: FAIL")
                    test_results['success'] = False
                    
            except Exception as e:
                test_results['tests_failed'] += 1
                test_results['test_details'].append(f"State validation: ERROR - {e}")
                test_results['success'] = False
            
            test_results['total_tests'] = test_results['tests_passed'] + test_results['tests_failed']
            
            self.logger.info(f"Touch flow integration test completed: {test_results['tests_passed']}/{test_results['total_tests']} passed")
            return test_results
            
        except Exception as e:
            self.logger.error(f"Complete touch flow test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'tests_passed': 0,
                'tests_failed': 1
            }
    
    def simulate_touch_at_center(self) -> None:
        """Simulate a touch event at the center of the screen for testing"""
        try:
            if self.touch_handler:
                self.touch_handler.simulate_settings_button_press('center')
            else:
                self.logger.error("No touch handler available for simulation")
        except Exception as e:
            self.logger.error(f"Touch simulation failed: {e}")