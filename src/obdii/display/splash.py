#!/usr/bin/env python3
"""
Splash screen component for OBDII display application.
Provides animated startup screen with loading indicators and application branding.
"""

import logging
import math
import threading
import time
from typing import Tuple, Optional

# Import configuration classes  
try:
    from ..utils.config import SplashConfig
except ImportError:
    # Fallback for development/testing
    SplashConfig = None

# Import typography system for consistent font sizing
try:
    from .typography import (get_font_manager, get_title_display_font, get_body_font, 
                            get_label_small_font, TypographyConstants)
    TYPOGRAPHY_AVAILABLE = True
except ImportError:
    # Fallback for development/testing without typography module
    TYPOGRAPHY_AVAILABLE = False

# Conditional import of pygame with fallback handling
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False


class SplashScreen:
    """
    Thread-safe splash screen implementation for OBDII RPM Display application.
    
    Provides animated startup screen with progress indicators, application branding,
    and graceful fallback for systems without pygame support. Designed for use
    in multi-threaded display management environments.
    
    Attributes:
        surface_size (Tuple[int, int]): Target surface dimensions in pixels
        duration (float): Minimum display duration in seconds
        logger (logging.Logger): Logger instance for debug/error reporting
        
    Thread Safety:
        All public methods are thread-safe using internal locking mechanisms.
        Safe to call from display manager threads and main application thread.
    """
    
    def __init__(self, surface_size: Tuple[int, int] = (480, 480), duration: float = 5.0, 
                 config: Optional['SplashConfig'] = None):
        """
        Initialize splash screen with specified dimensions and display duration.
        
        Args:
            surface_size: Target surface size as (width, height) tuple
            duration: Minimum splash screen display time in seconds
            config: Optional SplashConfig object for advanced configuration
            
        Raises:
            ValueError: If surface_size contains non-positive values or duration is negative
        """
        # Input validation
        if not isinstance(surface_size, (tuple, list)) or len(surface_size) != 2:
            raise ValueError("surface_size must be a tuple of (width, height)")
        
        width, height = surface_size
        if width <= 0 or height <= 0:
            raise ValueError("Surface dimensions must be positive integers")
            
        if duration < 0:
            raise ValueError("Duration must be non-negative")
        
        # Apply configuration if provided
        if config is not None:
            self.duration = config.duration if config.enabled else 0.0
            self._graphics_mode = config.graphics_mode
            self._animation_speed = config.animation_speed
            self._enabled = config.enabled
        else:
            self.duration = duration
            self._graphics_mode = "automotive"
            self._animation_speed = 1.0
            self._enabled = True
            
        # Core configuration
        self.surface_size = surface_size
        self.logger = logging.getLogger('SplashScreen')
        
        # Threading and timing controls
        self._start_time: Optional[float] = None
        self._completion_event = threading.Event()
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Animation state tracking
        self._animation_time = 0.0
        self._last_update = 0.0
        
        # Graphics availability and fallback state
        self._graphics_available = PYGAME_AVAILABLE
        self._font_initialized = False
        
        # Typography system integration and font caching
        self._typography_available = TYPOGRAPHY_AVAILABLE
        self._cached_fonts = {}  # Cache for font objects to improve performance
        self._font_cache_lock = threading.Lock()  # Thread-safe font cache access
        
        # Performance monitoring for font operations
        self._font_render_times = []  # Track font rendering performance
        self._total_render_time = 0.0
        
        # Color scheme - professional dark theme
        self._colors = {
            'background': (15, 20, 25),      # Dark blue-gray background
            'primary_text': (255, 255, 255), # Pure white for main text
            'secondary_text': (180, 190, 200), # Light gray for secondary text
            'accent': (64, 150, 255),        # Bright blue accent color
            'progress_bg': (40, 45, 50),     # Dark gray for progress background
            'progress_fill': (64, 150, 255), # Blue progress fill
            'border': (80, 90, 100)          # Medium gray for borders
        }
        
        # Application branding and version info
        self._app_title = "OBDII RPM Display"
        self._version_text = "v1.0.0"  # Placeholder version
        self._subtitle = "Bluetooth OBD-II Monitor"
        
        # Log initialization status
        if self._graphics_available:
            self.logger.info(f"SplashScreen initialized with pygame support ({surface_size[0]}x{surface_size[1]}, {duration}s)")
        else:
            self.logger.warning("SplashScreen initialized in text-only mode (pygame not available)")
        
        if self._typography_available:
            self.logger.debug("Typography system available for splash screen")
        else:
            self.logger.debug("Typography system not available - using fallback fonts")
    
    def start(self) -> None:
        """
        Start the splash screen timing mechanism.
        
        Records the current time as the splash screen start time and begins
        the countdown to completion. Thread-safe and idempotent.
        
        Note:
            Multiple calls to start() will not reset the timer if already started.
            Use reset() to restart the timing if needed.
        """
        with self._lock:
            if self._start_time is None:
                self._start_time = time.time()
                self._last_update = self._start_time
                self._completion_event.clear()
                self.logger.debug(f"Splash screen timer started (duration: {self.duration}s)")
            else:
                self.logger.debug("Splash screen timer already started")
    
    def reset(self) -> None:
        """
        Reset the splash screen to initial state.
        
        Clears timing information and resets animation state. Useful for
        restarting the splash screen or preparing for a new display cycle.
        Thread-safe operation.
        """
        with self._lock:
            self._start_time = None
            self._animation_time = 0.0
            self._last_update = 0.0
            self._completion_event.clear()
            self.logger.debug("Splash screen reset to initial state")
    
    def is_complete(self) -> bool:
        """
        Check if the splash screen has completed its minimum display duration.
        
        Returns:
            bool: True if minimum duration has elapsed since start(), False otherwise
            
        Thread Safety:
            Safe to call from any thread. Uses internal locking for consistency.
            
        Note:
            Returns False if start() has not been called yet.
        """
        with self._lock:
            if self._start_time is None:
                return False
            
            elapsed = time.time() - self._start_time
            is_done = elapsed >= self.duration
            
            # Set completion event for potential waiters
            if is_done and not self._completion_event.is_set():
                self._completion_event.set()
                self.logger.debug(f"Splash screen completed after {elapsed:.2f}s")
            
            return is_done
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Block until splash screen completes or timeout occurs.
        
        Args:
            timeout: Maximum time to wait in seconds (None for indefinite wait)
            
        Returns:
            bool: True if splash completed normally, False if timeout occurred
            
        Thread Safety:
            Safe to call from any thread. Will not block if already completed.
        """
        # Start timing if not already started
        if self._start_time is None:
            self.start()
        
        # Calculate remaining time if timeout specified
        effective_timeout = timeout
        if timeout is not None and self._start_time is not None:
            elapsed = time.time() - self._start_time
            remaining = max(0, self.duration - elapsed)
            effective_timeout = min(timeout, remaining)
        
        return self._completion_event.wait(effective_timeout)
    
    def _get_cached_font(self, font_type: str, fallback_size: int) -> Optional['pygame.font.Font']:
        """
        Get a cached font object with performance timing.
        
        Args:
            font_type: Type of font ('title', 'body', 'label')
            fallback_size: Fallback size if typography system unavailable
            
        Returns:
            pygame.font.Font object or None if unavailable
        """
        start_time = time.time()
        
        try:
            with self._font_cache_lock:
                # Check cache first
                if font_type in self._cached_fonts:
                    return self._cached_fonts[font_type]
                
                # Get font from typography system if available
                font = None
                if self._typography_available:
                    try:
                        if font_type == 'title':
                            font = get_title_display_font()
                            self.logger.debug(f"Using typography title font ({TypographyConstants.FONT_TITLE}px)")
                        elif font_type == 'body':
                            font = get_body_font()
                            self.logger.debug(f"Using typography body font ({TypographyConstants.FONT_BODY}px)")
                        elif font_type == 'label':
                            font = get_label_small_font()
                            self.logger.debug(f"Using typography label font ({TypographyConstants.FONT_LABEL_SMALL}px)")
                    except Exception as e:
                        self.logger.warning(f"Typography system error for {font_type}: {e}")
                
                # Fallback to pygame font if typography unavailable
                if font is None:
                    try:
                        if not pygame.font.get_init():
                            pygame.font.init()
                        font = pygame.font.Font(None, fallback_size)
                        self.logger.debug(f"Using fallback font {fallback_size}px for {font_type}")
                    except Exception as e:
                        self.logger.error(f"Failed to create fallback font for {font_type}: {e}")
                        return None
                
                # Cache the font for future use
                if font is not None:
                    self._cached_fonts[font_type] = font
                
                return font
                
        except Exception as e:
            self.logger.error(f"Font caching error for {font_type}: {e}")
            return None
        finally:
            # Track performance
            render_time = time.time() - start_time
            self._font_render_times.append(render_time)
            self._total_render_time += render_time
            
            # Log slow font operations
            if render_time > 0.01:  # > 10ms
                self.logger.warning(f"Slow font operation for {font_type}: {render_time*1000:.1f}ms")
    
    def render(self, surface) -> bool:
        """
        Render the splash screen graphics to the provided surface.
        
        Args:
            surface: Pygame surface to render onto, or None for text-only mode
            
        Returns:
            bool: True if rendering succeeded, False if errors occurred
            
        Thread Safety:
            Safe to call from display thread. Uses internal locking for state updates.
            
        Note:
            Automatically handles pygame availability and provides text fallback.
            Updates internal animation timing on each call.
        """
        try:
            with self._lock:
                # Update animation timing
                current_time = time.time()
                if self._last_update > 0:
                    delta_time = current_time - self._last_update
                    self._animation_time += delta_time
                self._last_update = current_time
                
                # Start timing if not already started
                if self._start_time is None:
                    self.start()
                
                # Choose rendering method based on availability
                if surface is not None and self._graphics_available:
                    return self._render_graphics(surface)
                else:
                    return self._render_text_fallback()
                    
        except Exception as e:
            self.logger.error(f"Splash screen rendering error: {e}", exc_info=True)
            return False
    
    def _render_graphics(self, surface) -> bool:
        """
        Render graphical splash screen using pygame.
        
        Args:
            surface: Pygame surface to draw on
            
        Returns:
            bool: True if rendering succeeded, False otherwise
        """
        # Skip rendering if splash is disabled
        if not getattr(self, '_enabled', True):
            return True
        try:
            # Ensure pygame font system is initialized
            if not self._font_initialized:
                if not pygame.font.get_init():
                    pygame.font.init()
                self._font_initialized = True
            
            # Clear background with dark theme color
            surface.fill(self._colors['background'])
            
            # Get surface dimensions
            width, height = surface.get_size()
            center_x, center_y = width // 2, height // 2
            
            # Render based on graphics mode
            graphics_mode = getattr(self, '_graphics_mode', 'automotive')
            
            if graphics_mode == 'text_only':
                # Text-only mode - reduced spacing from 40px to 25px
                self._draw_title_text(surface, center_x, center_y - 25)
                self._draw_subtitle_text(surface, center_x, center_y)
                self._draw_version_text(surface, center_x, center_y + 25)
            elif graphics_mode == 'minimal':
                # Minimal mode - reduced spacing for more compact layout
                self._draw_title_text(surface, center_x, center_y - 50)
                self._draw_subtitle_text(surface, center_x, center_y - 25)
                self._draw_progress_indicator(surface, center_x, center_y + 25)
                self._draw_version_text(surface, center_x, center_y + 75)
            else:
                # Full automotive mode - optimized spacing for minimalist design
                self._draw_title_text(surface, center_x, center_y - 65)
                self._draw_subtitle_text(surface, center_x, center_y - 40)
                # OBD-II icon removed to eliminate grey-to-green rectangle artifact behind gauge
                # self._draw_obdii_icon(surface, center_x, center_y)
                self._draw_progress_indicator(surface, center_x, center_y + 40)
                self._draw_version_text(surface, center_x, center_y + 90)
                self._draw_border(surface, width, height)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Graphics rendering failed: {e}")
            return False
    
    def _draw_title_text(self, surface, center_x: int, center_y: int) -> None:
        """Draw the main application title with minimalist typography (FONT_TITLE = 36px, was 56px)."""
        try:
            # Use typography system for consistent font sizing
            font_large = self._get_cached_font('title', 48)  # Fallback 48px instead of 56px
            if font_large is None:
                self.logger.error("Failed to get title font")
                return
                
            title_surface = font_large.render(self._app_title, True, self._colors['primary_text'])
            title_rect = title_surface.get_rect(center=(center_x, center_y))
            
            # Shadow effect removed to reduce rendering overhead and establish minimalist tone
            surface.blit(title_surface, title_rect)
            
            # Validate text fits within circular display if typography system available
            if self._typography_available:
                try:
                    manager = get_font_manager()
                    if not manager.validate_text_fits_circular_display(self._app_title, TypographyConstants.FONT_TITLE):
                        self.logger.warning("Splash title may not fit in circular display")
                except Exception as e:
                    self.logger.debug(f"Circular validation failed for title: {e}")
            
        except Exception as e:
            self.logger.error(f"Title text rendering failed: {e}")
    
    def _draw_subtitle_text(self, surface, center_x: int, center_y: int) -> None:
        """Draw the application subtitle with body typography (FONT_BODY = 20px, was 32px)."""
        try:
            # Use typography system for consistent body text sizing
            font_medium = self._get_cached_font('body', 28)  # Fallback 28px instead of 32px
            if font_medium is None:
                self.logger.error("Failed to get body font for subtitle")
                return
                
            subtitle_surface = font_medium.render(self._subtitle, True, self._colors['secondary_text'])
            subtitle_rect = subtitle_surface.get_rect(center=(center_x, center_y))
            surface.blit(subtitle_surface, subtitle_rect)
            
            # Validate text fits within circular display
            if self._typography_available:
                try:
                    manager = get_font_manager()
                    if not manager.validate_text_fits_circular_display(self._subtitle, TypographyConstants.FONT_BODY):
                        self.logger.warning("Splash subtitle may not fit in circular display")
                except Exception as e:
                    self.logger.debug(f"Circular validation failed for subtitle: {e}")
            
        except Exception as e:
            self.logger.error(f"Subtitle text rendering failed: {e}")
    
    def _draw_obdii_icon(self, surface, center_x: int, center_y: int) -> None:
        """Draw animated OBD-II connector icon."""
        try:
            # Import graphics function
            from .graphics.splash_graphics import draw_obdii_connector
            
            # Calculate connection animation (pulsing effect)
            if self._start_time:
                elapsed = time.time() - self._start_time
                # Animate connection state - start disconnected, connect halfway through
                connected = elapsed > (self.duration / 2)
            else:
                connected = False
            
            # Draw OBD-II connector with animation
            connector_size = 80
            connector_success = draw_obdii_connector(surface, (center_x, center_y), 
                                                   connector_size, connected)
            
            if not connector_success:
                # Fallback: simple circle indicator
                color = self._colors['accent'] if connected else self._colors['border']
                radius = 20
                pygame.draw.circle(surface, color, (center_x, center_y), radius, 3)
                
        except Exception as e:
            self.logger.error(f"OBD-II icon rendering failed: {e}")
    
    def _draw_progress_indicator(self, surface, center_x: int, center_y: int) -> None:
        """Draw simplified progress indicator with automotive gauge only."""
        try:
            # Import graphics functions
            from .graphics.splash_graphics import (
                draw_automotive_gauge, SPLASH_COLORS
            )
            
            # Calculate animation progress (0.0 to 1.0)
            if self._start_time:
                elapsed = time.time() - self._start_time
                progress = min(1.0, elapsed / self.duration)
            else:
                progress = 0.0
            
            # Draw automotive gauge as the sole progress indicator
            gauge_radius = 60
            gauge_success = draw_automotive_gauge(surface, (center_x, center_y - 20), 
                                                gauge_radius, progress)
            
            if not gauge_success:
                # Log warning but don't fall back to other indicators
                self.logger.warning("Automotive gauge rendering failed - no fallback progress indicator")
            
        except Exception as e:
            self.logger.error(f"Progress indicator rendering failed: {e}")
    
    
    def _draw_version_text(self, surface, center_x: int, center_y: int) -> None:
        """Draw version information with label typography (FONT_LABEL_SMALL = 16px, was 24px)."""
        try:
            # Use typography system for consistent label sizing
            font_small = self._get_cached_font('label', 20)  # Fallback 20px instead of 24px
            if font_small is None:
                self.logger.error("Failed to get label font for version")
                return
                
            version_surface = font_small.render(self._version_text, True, self._colors['secondary_text'])
            version_rect = version_surface.get_rect(center=(center_x, center_y))
            surface.blit(version_surface, version_rect)
            
            # Validate text fits within circular display
            if self._typography_available:
                try:
                    manager = get_font_manager()
                    if not manager.validate_text_fits_circular_display(self._version_text, TypographyConstants.FONT_LABEL_SMALL):
                        self.logger.warning("Splash version text may not fit in circular display")
                except Exception as e:
                    self.logger.debug(f"Circular validation failed for version: {e}")
            
        except Exception as e:
            self.logger.error(f"Version text rendering failed: {e}")
    
    def _draw_border(self, surface, width: int, height: int) -> None:
        """Draw decorative border around the splash screen."""
        try:
            border_thickness = 2
            border_color = self._colors['border']
            
            # Draw border rectangle
            border_rect = pygame.Rect(border_thickness, border_thickness, 
                                    width - 2 * border_thickness, 
                                    height - 2 * border_thickness)
            pygame.draw.rect(surface, border_color, border_rect, border_thickness)
            
        except Exception as e:
            self.logger.error(f"Border rendering failed: {e}")
    
    def _render_text_fallback(self) -> bool:
        """
        Provide text-based fallback when graphics are unavailable.
        
        Returns:
            bool: Always returns True (text fallback cannot fail)
        """
        try:
            # Calculate progress for text display
            if self._start_time:
                elapsed = time.time() - self._start_time
                progress = min(1.0, elapsed / self.duration)
            else:
                progress = 0.0
            
            # Create simple text progress indicator
            bar_length = 20
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            # Log progress periodically (every 0.5 seconds)
            if int(self._animation_time * 2) % 1 == 0:  # Every 0.5s
                self.logger.info(f"{self._app_title} - Loading: [{bar}] {int(progress * 100)}%")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Text fallback rendering failed: {e}")
            return True  # Fallback should never fail completely
    
    def get_progress(self) -> float:
        """
        Get current splash screen progress as a percentage.
        
        Returns:
            float: Progress value between 0.0 and 1.0, or 0.0 if not started
            
        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            if self._start_time is None:
                return 0.0
            
            elapsed = time.time() - self._start_time
            return min(1.0, elapsed / self.duration)
    
    def get_remaining_time(self) -> float:
        """
        Get remaining splash screen display time in seconds.
        
        Returns:
            float: Remaining time in seconds, or full duration if not started
            
        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            if self._start_time is None:
                return self.duration
            
            elapsed = time.time() - self._start_time
            return max(0.0, self.duration - elapsed)
    
    def set_custom_text(self, title: Optional[str] = None, 
                       subtitle: Optional[str] = None, 
                       version: Optional[str] = None) -> None:
        """
        Customize splash screen text content.
        
        Args:
            title: Custom application title (None to keep default)
            subtitle: Custom subtitle text (None to keep default)
            version: Custom version string (None to keep default)
            
        Thread Safety:
            Safe to call from any thread. Changes take effect on next render.
        """
        with self._lock:
            if title is not None:
                self._app_title = str(title)
                self.logger.debug(f"Splash title updated to: {title}")
            
            if subtitle is not None:
                self._subtitle = str(subtitle)
                self.logger.debug(f"Splash subtitle updated to: {subtitle}")
            
            if version is not None:
                self._version_text = str(version)
                self.logger.debug(f"Splash version updated to: {version}")
    
    def get_info(self) -> dict:
        """
        Get comprehensive splash screen state information for debugging.
        
        Returns:
            dict: Current state information including timing, progress, and configuration
            
        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            return {
                'surface_size': self.surface_size,
                'duration': self.duration,
                'graphics_available': self._graphics_available,
                'font_initialized': self._font_initialized,
                'started': self._start_time is not None,
                'start_time': self._start_time,
                'animation_time': self._animation_time,
                'progress': self.get_progress(),
                'remaining_time': self.get_remaining_time(),
                'is_complete': self.is_complete(),
                'app_title': self._app_title,
                'version': self._version_text,
                'typography_available': self._typography_available,
                'cached_fonts': list(self._cached_fonts.keys()),
                'font_performance': {
                    'total_render_time': self._total_render_time,
                    'average_render_time': (
                        sum(self._font_render_times) / len(self._font_render_times) 
                        if self._font_render_times else 0.0
                    ),
                    'render_operations': len(self._font_render_times)
                }
            }
    
    def get_performance_report(self) -> dict:
        """
        Get splash screen performance report including font rendering metrics.
        
        Returns:
            dict: Performance metrics and optimization suggestions
        """
        with self._lock:
            avg_render_time = (
                sum(self._font_render_times) / len(self._font_render_times) 
                if self._font_render_times else 0.0
            )
            
            report = {
                'typography_system': {
                    'available': self._typography_available,
                    'fonts_cached': len(self._cached_fonts),
                    'cache_hit_rate': 'N/A'  # Would need to track hits vs misses
                },
                'font_performance': {
                    'total_render_time_ms': self._total_render_time * 1000,
                    'average_render_time_ms': avg_render_time * 1000,
                    'operations_count': len(self._font_render_times),
                    'slow_operations': len([t for t in self._font_render_times if t > 0.01])
                },
                'optimization_status': {
                    'shadow_effects_removed': True,
                    'font_caching_enabled': True,
                    'reduced_spacing': True,
                    'minimalist_fonts': self._typography_available
                },
                'recommendations': []
            }
            
            # Generate performance recommendations
            if avg_render_time > 0.005:  # > 5ms average
                report['recommendations'].append("Font rendering is slow - consider font preloading")
            
            if not self._typography_available:
                report['recommendations'].append("Typography system not available - using fallback fonts")
            
            if len(self._font_render_times) > 100:
                # Clear old timing data to prevent memory growth
                self._font_render_times = self._font_render_times[-50:]
                report['recommendations'].append("Font timing data trimmed to prevent memory growth")
            
            if not report['recommendations']:
                report['recommendations'].append("Performance is within acceptable limits")
            
            return report