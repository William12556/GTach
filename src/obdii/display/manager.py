#!/usr/bin/env python3
"""
Display Manager - Refactored for component-based architecture.

Orchestrates display rendering, touch handling, and performance monitoring
through extracted components for improved maintainability.
"""

import os
import sys
import math
import logging
import threading
import time
from enum import Enum, auto
from typing import Optional, Tuple, Dict, Any

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

# Component imports
from .rendering import DisplayRenderingEngine, RenderTarget
from .input import TouchEventCoordinator, TouchAction, GestureType
from .performance import PerformanceMonitor

# Legacy imports for compatibility
from .models import DisplayMode, DisplayConfig, ConnectionStatus
from .splash import SplashScreen
from .typography import (get_font_manager, get_title_font, get_medium_font, get_small_font, get_minimal_font,
                         get_rpm_large_font, get_rpm_medium_font, get_label_small_font, 
                         get_title_display_font, get_heading_font, TypographyConstants,
                         get_button_renderer, ButtonSize, ButtonState)
from ..core import ThreadManager, ThreadStatus
from ..utils import TerminalRestorer

class DisplayManager:
    """
    Refactored display manager using component-based architecture.
    
    Orchestrates display rendering, touch handling, and performance monitoring
    through specialized components for improved maintainability and testing.
    """
    
    def __init__(self, thread_manager: ThreadManager, terminal_restorer: TerminalRestorer = None, config_path: str = 'config.yaml'):
        self.logger = logging.getLogger('DisplayManager')
        self.thread_manager = thread_manager
        self.config_path = config_path
        self._shutdown_event = threading.Event()
        self.terminal_restorer = terminal_restorer
        
        # Component initialization
        self._initialize_components()
        
        # Configuration
        self._load_config()
        
        # Legacy components
        self._initialize_legacy_components()
        
        # Display thread setup
        self.display_thread = threading.Thread(
            target=self._display_loop,
            name='DisplayManager'
        )
        self.thread_manager.register_thread('display', self.display_thread)
    
    def _initialize_components(self) -> None:
        """Initialize the extracted components"""
        try:
            # Initialize rendering engine
            self.rendering_engine = DisplayRenderingEngine()
            if not self.rendering_engine.initialize((480, 480)):
                self.logger.error("Failed to initialize rendering engine")
                self.display_available = False
            else:
                self.display_available = True
            
            # Initialize touch coordinator
            self.touch_coordinator = TouchEventCoordinator((480, 480))
            self._setup_touch_callbacks()
            
            # Initialize performance monitor
            self.performance_monitor = PerformanceMonitor(target_fps=60)
            self.performance_monitor.start_monitoring()
            
            self.logger.info("Display components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}", exc_info=True)
            self.display_available = False
    
    def _setup_touch_callbacks(self) -> None:
        """Setup touch gesture callbacks"""
        try:
            # Register gesture callbacks for navigation
            self.touch_coordinator.register_gesture_callback(
                GestureType.SWIPE_LEFT, self._handle_swipe_left
            )
            self.touch_coordinator.register_gesture_callback(
                GestureType.SWIPE_RIGHT, self._handle_swipe_right
            )
            self.touch_coordinator.register_gesture_callback(
                GestureType.LONG_PRESS, self._handle_long_press
            )
            
        except Exception as e:
            self.logger.error(f"Touch callback setup failed: {e}")
    
    def _handle_swipe_left(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> TouchAction:
        """Handle left swipe gesture"""
        try:
            if self.config.mode == DisplayMode.DIGITAL:
                self.config.mode = DisplayMode.GAUGE
                return TouchAction.MODE_CHANGE
            elif self.config.mode == DisplayMode.GAUGE:
                self.config.mode = DisplayMode.DIGITAL
                return TouchAction.MODE_CHANGE
            return TouchAction.NONE
        except Exception as e:
            self.logger.error(f"Swipe left handling error: {e}")
            return TouchAction.NONE
    
    def _handle_swipe_right(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> TouchAction:
        """Handle right swipe gesture"""
        try:
            if self.config.mode == DisplayMode.DIGITAL:
                self.config.mode = DisplayMode.GAUGE
                return TouchAction.MODE_CHANGE
            elif self.config.mode == DisplayMode.GAUGE:
                self.config.mode = DisplayMode.DIGITAL
                return TouchAction.MODE_CHANGE
            return TouchAction.NONE
        except Exception as e:
            self.logger.error(f"Swipe right handling error: {e}")
            return TouchAction.NONE
    
    def _handle_long_press(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> TouchAction:
        """Handle long press gesture"""
        try:
            if self.config.mode == DisplayMode.SETTINGS:
                # Exit settings mode
                self.config.mode = DisplayMode.DIGITAL
                return TouchAction.NAVIGATION
            else:
                # Enter settings mode
                self.config.mode = DisplayMode.SETTINGS
                return TouchAction.NAVIGATION
        except Exception as e:
            self.logger.error(f"Long press handling error: {e}")
            return TouchAction.NONE
    
    def _initialize_legacy_components(self) -> None:
        """Initialize legacy components for backward compatibility"""
        try:
            # Touch handler compatibility
            try:
                from .touch import TouchHandler
                self.touch_handler = TouchHandler(self)
            except ImportError as e:
                self.logger.warning(f"TouchHandler not available: {e}")
                self.touch_handler = None
            
            # Setup mode components
            self._setup_manager = None
            self._in_setup_mode = False
            
            # Initialize splash screen
            try:
                splash_config = getattr(self.config, 'splash', None)
                self._splash_screen = SplashScreen(surface_size=(480, 480), duration=4.0, config=splash_config)
                self.logger.info("Splash screen initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize splash screen: {e}")
                self._splash_screen = None
            
            # Navigation gesture handler
            try:
                from .navigation_gestures import NavigationGestureHandler, GestureConfig
                
                gesture_config = GestureConfig(
                    swipe_threshold=getattr(self.config, 'gesture_swipe_threshold', 50),
                    velocity_threshold=getattr(self.config, 'gesture_velocity_threshold', 100),
                    edge_width=getattr(self.config, 'gesture_edge_width', 30),
                    max_gesture_time=getattr(self.config, 'gesture_max_time', 2.0),
                    edge_indicator_timeout=getattr(self.config, 'gesture_edge_timeout', 3.0),
                    enable_main_navigation=getattr(self.config, 'gesture_enable_main', True),
                    enable_setup_navigation=getattr(self.config, 'gesture_enable_setup', True),
                    enable_settings_gestures=getattr(self.config, 'gesture_enable_settings', True),
                    debug_mode=getattr(self.config, 'gesture_debug_mode', False)
                )
                
                self.gesture_handler = NavigationGestureHandler(self, gesture_config)
                self.logger.info("Navigation gesture handler initialized")
                
            except ImportError as e:
                self.logger.error(f"Failed to initialize gesture handler: {e}")
                self.gesture_handler = None
            
        except Exception as e:
            self.logger.error(f"Legacy component initialization failed: {e}")
    
    def _load_config(self) -> None:
        """Load display configuration"""
        try:
            if YAML_AVAILABLE and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    saved_mode = DisplayMode[config_data.get('mode', 'DIGITAL')]
                    self.config = DisplayConfig(
                        mode=DisplayMode.SPLASH,  # Always start with splash
                        rpm_warning=config_data.get('rpm_warning', 6500),
                        rpm_danger=config_data.get('rpm_danger', 7000),
                        fps_limit=config_data.get('fps_limit', 60),
                        touch_long_press=config_data.get('touch_long_press', 1.0)
                    )
                    self._post_splash_mode = saved_mode
            else:
                if not YAML_AVAILABLE:
                    self.logger.info("YAML not available - using default configuration")
                self.config = DisplayConfig(mode=DisplayMode.SPLASH)
                self._post_splash_mode = DisplayMode.DIGITAL
                if YAML_AVAILABLE:
                    self._save_config()
                    
        except Exception as e:
            self.logger.error(f"Config load failed: {e}", exc_info=True)
            self.config = DisplayConfig(mode=DisplayMode.SPLASH)
            self._post_splash_mode = DisplayMode.DIGITAL
    
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
        """Start display manager"""
        self.start_splash()
        self.display_thread.start()
        self.logger.info("Display manager started")
    
    def start_splash(self) -> None:
        """Start the splash screen"""
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
            self.config.mode = self._post_splash_mode
    
    def stop(self) -> None:
        """Stop display manager"""
        self._shutdown_event.set()
        self.display_thread.join()
        
        # Clean up components
        try:
            self.performance_monitor.stop_monitoring()
            self.rendering_engine.cleanup()
            self.logger.info("Display manager stopped")
        except Exception as e:
            self.logger.error(f"Error stopping display manager: {e}", exc_info=True)
    
    def _display_loop(self) -> None:
        """Main display loop using component architecture"""
        if not PYGAME_AVAILABLE:
            self.logger.warning("Pygame not available - display loop disabled")
            return
        
        clock = pygame.time.Clock()
        
        self.logger.info("Display loop started with component architecture")
        
        while not self._shutdown_event.is_set():
            try:
                # Record frame start for performance monitoring
                frame_id = self.performance_monitor.record_frame_start()
                
                self.thread_manager.update_heartbeat('display')
                
                # Clear back buffer
                self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
                
                # Render current mode
                if self.config.mode == DisplayMode.SPLASH:
                    self._draw_splash_mode()
                elif self._in_setup_mode and self._setup_manager:
                    self._render_setup_mode()
                else:
                    self._render_normal_modes()
                
                # Swap buffers and write to framebuffer
                self.rendering_engine.swap_buffers()
                self.rendering_engine.write_to_framebuffer()
                
                # Tick clock and record frame end
                clock.tick(self.config.fps_limit)
                self.performance_monitor.record_frame_end(frame_id)
                
                # Periodic performance logging
                if frame_id and len(frame_id) > 0:  # Every few frames
                    metrics = self.performance_monitor.get_current_metrics()
                    if metrics.total_frames % 600 == 0:  # Every 10 seconds at 60fps
                        self.logger.info(
                            f"Performance: {metrics.fps:.1f} FPS, "
                            f"{metrics.frame_time_ms:.1f}ms frame, "
                            f"{metrics.memory_usage_mb:.1f}MB mem"
                        )
                
            except Exception as e:
                self.logger.error(f"Display loop error: {e}", exc_info=True)
                time.sleep(0.1)
        
        self.logger.info("Display loop ended")
    
    def _draw_splash_mode(self) -> None:
        """Draw splash screen"""
        try:
            if not self._splash_screen:
                self.config.mode = self._post_splash_mode
                return
            
            # Get back buffer surface for splash rendering
            back_surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
            if back_surface:
                splash_success = self._splash_screen.render(back_surface)
                
                if self._splash_screen.is_complete():
                    self.config.mode = self._post_splash_mode
                    self.logger.info(f"Splash completed - transitioning to {self._post_splash_mode.name}")
                    
                    if self._in_setup_mode:
                        self.logger.info("Setup mode was requested during splash")
                    
                    try:
                        self._splash_screen.reset()
                    except Exception as e:
                        self.logger.error(f"Error resetting splash screen: {e}")
                        
        except Exception as e:
            self.logger.error(f"Splash mode error: {e}", exc_info=True)
            self.config.mode = self._post_splash_mode
    
    def _render_setup_mode(self) -> None:
        """Render setup mode using setup manager"""
        try:
            back_surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
            if back_surface and self._setup_manager:
                self._setup_manager.render(back_surface)
        except Exception as e:
            self.logger.error(f"Setup mode render error: {e}")
            self._draw_setup_mode_fallback()
    
    def _render_normal_modes(self) -> None:
        """Render normal display modes"""
        try:
            if self.config.mode == DisplayMode.DIGITAL:
                self._draw_digital_mode()
            elif self.config.mode == DisplayMode.GAUGE:
                self._draw_gauge_mode()
            elif self.config.mode == DisplayMode.SETTINGS:
                self._draw_settings_mode()
            
            # Always draw status indicator
            self._draw_status_indicator()
            
        except Exception as e:
            self.logger.error(f"Normal mode render error: {e}")
    
    def _draw_digital_mode(self) -> None:
        """Draw digital RPM display using rendering engine"""
        try:
            # Get RPM data
            try:
                rpm_data = self.thread_manager.message_queue.get_nowait()
                rpm = ((256 * rpm_data.data[0]) + rpm_data.data[1]) / 4
            except:
                rpm = 0
            
            # Determine color based on thresholds
            if rpm >= self.config.rpm_danger:
                color = (255, 0, 0)  # Red
            elif rpm >= self.config.rpm_warning:
                color = (255, 165, 0)  # Orange
            else:
                color = (255, 255, 255)  # White
            
            # Render text using rendering engine
            font = get_rpm_large_font()
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    f"{int(rpm)}",
                    font,
                    color,
                    (240, 240),
                    center=True
                )
            
        except Exception as e:
            self.logger.error(f"Digital display error: {e}")
    
    def _draw_gauge_mode(self) -> None:
        """Draw analog gauge display using rendering engine"""
        try:
            # Get RPM data
            try:
                rpm_data = self.thread_manager.message_queue.get_nowait()
                rpm = ((256 * rpm_data.data[0]) + rpm_data.data[1]) / 4
            except:
                rpm = 0
            
            # Gauge parameters
            center = (240, 240)
            radius = 200
            max_rpm = 8000
            
            # Draw gauge background
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, (30, 30, 30), center, radius)
            
            # Draw color zones (simplified for component example)
            self._draw_gauge_zones(center, radius, max_rpm)
            
            # Draw needle
            self._draw_gauge_needle(center, radius, rpm, max_rpm)
            
            # Draw center hub
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, (60, 60, 60), center, 40)
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, (100, 100, 100), center, 38)
            
            # Draw digital readout
            font = get_rpm_medium_font()
            if font:
                needle_color = self._get_rpm_color(rpm)
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    f"{int(rpm)}",
                    font,
                    needle_color,
                    center,
                    center=True
                )
                
        except Exception as e:
            self.logger.error(f"Gauge display error: {e}")
    
    def _draw_gauge_zones(self, center: Tuple[int, int], radius: int, max_rpm: int) -> None:
        """Draw colored zones on gauge"""
        try:
            # Simplified zone drawing using rendering engine primitives
            # This is a simplified version - full implementation would draw arcs
            
            # Warning zone (orange)
            warning_start_angle = 135 - (self.config.rpm_warning / max_rpm * 270)
            warning_end_angle = 135 - (self.config.rpm_danger / max_rpm * 270)
            
            # Danger zone (red)  
            danger_start_angle = warning_end_angle
            danger_end_angle = 45
            
            # For simplicity, just draw indicator lines at thresholds
            self._draw_gauge_threshold_line(center, radius, self.config.rpm_warning, max_rpm, (255, 165, 0))
            self._draw_gauge_threshold_line(center, radius, self.config.rpm_danger, max_rpm, (255, 0, 0))
            
        except Exception as e:
            self.logger.error(f"Gauge zones error: {e}")
    
    def _draw_gauge_threshold_line(self, center: Tuple[int, int], radius: int, 
                                  rpm: int, max_rpm: int, color: Tuple[int, int, int]) -> None:
        """Draw threshold indicator line on gauge"""
        try:
            angle = 135 - (rpm / max_rpm * 270)
            angle_rad = math.radians(angle)
            
            start_x = center[0] + int((radius - 40) * math.cos(angle_rad))
            start_y = center[1] - int((radius - 40) * math.sin(angle_rad))
            end_x = center[0] + int((radius - 10) * math.cos(angle_rad))
            end_y = center[1] - int((radius - 10) * math.sin(angle_rad))
            
            self.rendering_engine.draw_line(RenderTarget.BACK_BUFFER, color, 
                                          (start_x, start_y), (end_x, end_y), 3)
            
        except Exception as e:
            self.logger.error(f"Gauge threshold line error: {e}")
    
    def _draw_gauge_needle(self, center: Tuple[int, int], radius: int, 
                          rpm: int, max_rpm: int) -> None:
        """Draw gauge needle"""
        try:
            if rpm > max_rpm:
                rpm = max_rpm
                
            needle_angle = 135 - (rpm / max_rpm * 270)
            needle_angle_rad = math.radians(needle_angle)
            
            needle_length = radius - 50
            needle_tip_x = center[0] + int(needle_length * math.cos(needle_angle_rad))
            needle_tip_y = center[1] - int(needle_length * math.sin(needle_angle_rad))
            
            needle_color = self._get_rpm_color(rpm)
            
            self.rendering_engine.draw_line(RenderTarget.BACK_BUFFER, needle_color, 
                                          center, (needle_tip_x, needle_tip_y), 4)
            
        except Exception as e:
            self.logger.error(f"Gauge needle error: {e}")
    
    def _get_rpm_color(self, rpm: int) -> Tuple[int, int, int]:
        """Get color for RPM value"""
        if rpm >= self.config.rpm_danger:
            return (255, 0, 0)  # Red
        elif rpm >= self.config.rpm_warning:
            return (255, 165, 0)  # Orange
        else:
            return (255, 255, 255)  # White
    
    def _draw_settings_mode(self) -> None:
        """Draw settings interface using touch coordinator"""
        try:
            # Clear existing touch regions
            self.touch_coordinator.clear_regions()
            
            # Background
            self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER, (40, 40, 50))
            
            # Title
            font = get_title_display_font()
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "Settings",
                    font,
                    (255, 255, 255),
                    (240, 40),
                    center=True
                )
            
            # Mode selector
            self._render_mode_selector()
            
            # RPM sliders
            self._register_rpm_sliders()
            
            # Save button
            self._register_save_button()
            
            # Instructions
            small_font = get_label_small_font()
            if small_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "Long press anywhere to exit settings",
                    small_font,
                    (150, 150, 150),
                    (240, 420),
                    center=True
                )
            
        except Exception as e:
            self.logger.error(f"Settings display error: {e}")
    
    def _render_mode_selector(self) -> None:
        """Render mode selector using touch coordinator"""
        try:
            # Mode selector layout
            selector_height = 30
            segment_width = 80
            selector_x = 240 - segment_width
            y_pos = 85
            
            # Digital button
            digital_rect = pygame.Rect(selector_x, y_pos, segment_width, selector_height)
            is_digital = self.config.mode == DisplayMode.DIGITAL
            digital_color = (100, 150, 250) if is_digital else (80, 80, 80)
            
            self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, digital_color,
                                          (digital_rect.x, digital_rect.y, digital_rect.width, digital_rect.height))
            
            # Register touch region
            self.touch_coordinator.register_button_region(
                "mode_digital", digital_rect, TouchAction.MODE_CHANGE,
                lambda pos: setattr(self.config, 'mode', DisplayMode.DIGITAL)
            )
            
            # Gauge button
            gauge_rect = pygame.Rect(selector_x + segment_width, y_pos, segment_width, selector_height)
            gauge_color = (100, 150, 250) if not is_digital else (80, 80, 80)
            
            self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, gauge_color,
                                          (gauge_rect.x, gauge_rect.y, gauge_rect.width, gauge_rect.height))
            
            # Register touch region
            self.touch_coordinator.register_button_region(
                "mode_gauge", gauge_rect, TouchAction.MODE_CHANGE,
                lambda pos: setattr(self.config, 'mode', DisplayMode.GAUGE)
            )
            
        except Exception as e:
            self.logger.error(f"Mode selector error: {e}")
    
    def _register_rpm_sliders(self) -> None:
        """Register RPM sliders with touch coordinator"""
        try:
            # Warning RPM slider
            warning_rect = pygame.Rect(60, 120, 360, 55)
            self.touch_coordinator.register_slider_region(
                "warning_rpm", warning_rect,
                track_start_x=180, track_width=200,
                min_val=1000, max_val=8000, current_val=self.config.rpm_warning
            )
            
            # Danger RPM slider
            danger_rect = pygame.Rect(60, 170, 360, 55)
            self.touch_coordinator.register_slider_region(
                "danger_rpm", danger_rect,
                track_start_x=180, track_width=200,
                min_val=1000, max_val=9000, current_val=self.config.rpm_danger
            )
            
            # Render slider visuals (simplified)
            self._render_slider_visuals("Warning RPM:", self.config.rpm_warning, 120, (255, 165, 0))
            self._render_slider_visuals("Danger RPM:", self.config.rpm_danger, 170, (255, 50, 50))
            
        except Exception as e:
            self.logger.error(f"RPM sliders error: {e}")
    
    def _render_slider_visuals(self, label: str, value: int, y_pos: int, color: Tuple[int, int, int]) -> None:
        """Render slider visual elements"""
        try:
            # Label
            font = self._get_cached_font(16)
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, label, font, (200, 200, 200),
                    (120, y_pos + 27), center=True
                )
            
            # Track
            track_rect = (180, y_pos + 25, 200, 4)
            self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (80, 80, 80), track_rect)
            
            # Thumb (simplified positioning)
            thumb_x = 180 + int((value - 1000) / 7000 * 200)  # Approximate positioning
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, color, 
                                            (thumb_x, y_pos + 27), 10)
            
            # Value display
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, str(value), font, color,
                    (420, y_pos + 27), center=True
                )
                
        except Exception as e:
            self.logger.error(f"Slider visuals error: {e}")
    
    def _register_save_button(self) -> None:
        """Register save button with touch coordinator"""
        try:
            # Calculate button position in circular layout
            save_rect = pygame.Rect(350, 300, 44, 44)
            
            self.touch_coordinator.register_button_region(
                "save", save_rect, TouchAction.SETTINGS_CHANGE,
                lambda pos: self._save_config()
            )
            
            # Draw save button
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, (0, 150, 0), 
                                            (372, 322), 22)
            
            # Checkmark (simplified)
            font = self._get_cached_font(20)
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, "✓", font, (255, 255, 255),
                    (372, 322), center=True
                )
                
        except Exception as e:
            self.logger.error(f"Save button error: {e}")
    
    def _draw_status_indicator(self) -> None:
        """Draw connection status indicator"""
        try:
            # Check bluetooth thread status
            if 'bluetooth' not in self.thread_manager.threads:
                status = ConnectionStatus.DISCONNECTED
            else:
                thread_status = self.thread_manager.threads['bluetooth'].status
                if thread_status == ThreadStatus.RUNNING:
                    status = ConnectionStatus.CONNECTED
                elif thread_status == ThreadStatus.STARTING:
                    status = ConnectionStatus.CONNECTING
                else:
                    status = ConnectionStatus.DISCONNECTED
            
            color = pygame.Color(status.value)
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, 
                                            (color.r, color.g, color.b), (20, 20), 5)
            
        except Exception as e:
            self.logger.error(f"Status indicator error: {e}")
    
    def _draw_setup_mode_fallback(self) -> None:
        """Draw basic setup mode indicator"""
        try:
            font = get_heading_font()
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "SETUP MODE",
                    font,
                    (255, 255, 0),
                    (240, 240),
                    center=True
                )
            
            # Draw border
            self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (255, 255, 0),
                                          (0, 0, 480, 480), width=3)
            
        except Exception as e:
            self.logger.error(f"Setup mode fallback error: {e}")
    
    def _get_cached_font(self, size: int, font_path: Optional[str] = None) -> Optional[pygame.font.Font]:
        """Get cached font (simplified version)"""
        try:
            font_manager = get_font_manager()
            return font_manager.get_font(size)
        except:
            try:
                return pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
            except:
                return None
    
    # Legacy compatibility methods
    def change_mode(self, mode: DisplayMode) -> None:
        """Change display mode"""
        self.config.mode = mode
        self._save_config()
    
    def set_setup_mode(self, setup_manager) -> None:
        """Enable setup mode"""
        self._setup_manager = setup_manager
        self._in_setup_mode = True
        self.logger.info(f"Entered setup mode")
    
    def exit_setup_mode(self) -> None:
        """Exit setup mode"""
        self._in_setup_mode = False
        self._setup_manager = None
        self.logger.info(f"Exited setup mode")
    
    def is_in_setup_mode(self) -> bool:
        """Check if in setup mode"""
        return self._in_setup_mode
    
    def handle_touch_event(self, pos: Tuple[int, int]) -> Optional[object]:
        """Handle touch events using touch coordinator"""
        try:
            self.logger.info(f"Touch event at {pos}")
            
            if self._in_setup_mode and self._setup_manager:
                # Route to setup manager
                return self._setup_manager.handle_touch_event(pos)
            else:
                # Use touch coordinator
                action = self.touch_coordinator.handle_touch_down(pos)
                
                # Handle slider value updates
                if action == TouchAction.SLIDER_INTERACTION:
                    self._update_config_from_sliders()
                
                return action
                
        except Exception as e:
            self.logger.error(f"Touch event error: {e}")
            return None
    
    def _update_config_from_sliders(self) -> None:
        """Update configuration from slider values"""
        try:
            warning_value = self.touch_coordinator.get_slider_value("warning_rpm")
            if warning_value is not None:
                self.config.rpm_warning = warning_value
            
            danger_value = self.touch_coordinator.get_slider_value("danger_rpm")
            if danger_value is not None:
                self.config.rpm_danger = danger_value
                
        except Exception as e:
            self.logger.error(f"Config update error: {e}")
    
    # Performance and debugging methods
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            return {
                'rendering_stats': self.rendering_engine.get_stats(),
                'touch_stats': self.touch_coordinator.get_stats(),
                'performance_metrics': self.performance_monitor.get_current_metrics().to_dict(),
                'performance_summary': self.performance_monitor.get_performance_summary()
            }
        except Exception as e:
            self.logger.error(f"Performance stats error: {e}")
            return {}
    
    def get_display_state(self) -> Dict[str, Any]:
        """Get current display state"""
        try:
            return {
                'display_mode': self.config.mode.name,
                'in_setup_mode': self._in_setup_mode,
                'components_initialized': {
                    'rendering_engine': self.rendering_engine.is_initialized(),
                    'touch_coordinator': True,
                    'performance_monitor': self.performance_monitor._monitoring
                },
                'active_touch_regions': len(self.touch_coordinator.get_active_regions()),
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"Display state error: {e}")
            return {'error': str(e)}