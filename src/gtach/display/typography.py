#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Typography constants and font management for the OBDII display application.

This module implements minimalist typography sizing designed for the HyperPixel 2" Round display.
Font sizes have been reduced by approximately 40% while maintaining excellent readability
at the typical viewing distance of 30-50cm.

The typography system is optimized for:
- Circular display constraints
- Space-efficient layouts
- Clear hierarchy between text elements
- Thread-safe font caching
- Cross-platform compatibility (Mac/Pi)
"""

import logging
import threading
import time
from typing import Dict, Optional, Tuple, List, Any
from enum import Enum

# Conditional imports for hardware dependencies
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False


class FontCategory(Enum):
    """Font categories for different UI elements."""
    TITLE = "title"          # Main display values (RPM, etc.)
    MEDIUM = "medium"        # Section headers, warnings
    SMALL = "small"          # Labels, secondary information
    MINIMAL = "minimal"      # Status indicators, hints


class ButtonSize(Enum):
    """Standard button size categories."""
    LARGE = "large"          # Primary actions (120x40)
    MEDIUM = "medium"        # Secondary actions (80x35)
    SMALL = "small"          # Tertiary actions (60x30)
    ICON = "icon"            # Icon-only buttons (40x40)
    FLOATING = "floating"    # Floating action buttons (44x44)


class ButtonState(Enum):
    """Button visual states."""
    NORMAL = "normal"        # Default state
    HOVER = "hover"          # Mouse hover (if supported)
    PRESSED = "pressed"      # Currently being pressed
    DISABLED = "disabled"    # Not interactive


class TypographyConstants:
    """
    Centralized typography constants for minimalist design.
    
    Font sizes are optimized for the 480x480 circular display with reduced sizes
    for space efficiency while maintaining readability.
    """
    
    # Primary font sizes (reduced from original by ~40%)
    TITLE_SIZE = 36      # Main RPM display (was 120)
    MEDIUM_SIZE = 28     # Settings headers, mode labels (was 48) 
    SMALL_SIZE = 20      # Labels, warnings (was 36)
    MINIMAL_SIZE = 16    # Status text, hints (was 24)
    
    # Gauge-specific font sizes
    GAUGE_CENTER_SIZE = 28   # Center RPM readout (was 46)
    GAUGE_LABEL_SIZE = 16    # Tick mark labels (was 24)
    
    # Specific named constants for DisplayManager
    FONT_RPM_LARGE = 36      # Digital mode main RPM display
    FONT_RPM_MEDIUM = 28     # Gauge mode center readout
    FONT_LABEL_SMALL = 16    # Labels and small text
    FONT_TITLE = 36          # Settings title
    FONT_HEADING = 28        # Settings section headers
    
    # Additional constants for SetupDisplayManager
    FONT_BODY = 20           # Body text and descriptions (was 32px)
    FONT_BUTTON = 20         # Button text (was 28px)
    FONT_MINIMAL = 14        # Very small text for compact layouts
    
    # Display constraints
    DISPLAY_WIDTH = 480
    DISPLAY_HEIGHT = 480
    DISPLAY_CENTER = (240, 240)
    
    # Font validation ranges
    MIN_FONT_SIZE = 12
    MAX_FONT_SIZE = 48
    
    # Typography scale ratios for responsive sizing
    SCALE_SMALL = 0.8    # For cramped layouts
    SCALE_LARGE = 1.2    # For emphasis
    
    # Standardized button size constants (width x height in pixels)
    BUTTON_LARGE = (120, 40)     # Primary actions like "Continue", "Save"
    BUTTON_MEDIUM = (80, 35)     # Secondary actions like "Back", "Cancel"
    BUTTON_SMALL = (60, 30)      # Tertiary actions like filter toggles
    BUTTON_ICON = (40, 40)       # Icon-only buttons
    BUTTON_FLOATING = (44, 44)   # Floating action buttons (minimum touch target)
    
    # Button visual styling constants
    BUTTON_CORNER_RADIUS = 6     # Corner radius for all button types (px)
    BUTTON_BORDER_WIDTH = 2      # Standard border width for outlined buttons (px)
    BUTTON_TOUCH_EXPANSION = 8   # Touch region expansion in all directions (px)
    BUTTON_PRESS_SCALE = 0.95    # Scale factor for pressed state (95% of original)
    
    # Button font sizes (optimized for compact design)
    BUTTON_FONT_LARGE = 18       # Font size for BUTTON_LARGE
    BUTTON_FONT_MEDIUM = 16      # Font size for BUTTON_MEDIUM  
    BUTTON_FONT_SMALL = 14       # Font size for BUTTON_SMALL
    BUTTON_FONT_ICON = 16        # Font size for icon labels/fallback text


class FontManager:
    """
    Thread-safe font manager with caching and validation.
    
    Manages pygame font objects with automatic caching to prevent memory leaks
    and ensure consistent font rendering across the application.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('FontManager')
        self._font_cache: Dict[int, pygame.font.Font] = {}
        self._cache_lock = threading.RLock()
        self._initialized = False
        
        # Initialize pygame font system if available
        if PYGAME_AVAILABLE:
            self._initialize_pygame_fonts()
    
    def _initialize_pygame_fonts(self) -> None:
        """Initialize pygame font system with error handling."""
        try:
            if not pygame.font.get_init():
                pygame.font.init()
                self.logger.debug("Pygame font system initialized")
            
            # Test font creation to verify system works
            test_font = pygame.font.Font(None, 24)
            if test_font:
                self._initialized = True
                self.logger.info("Font manager initialized successfully")
            else:
                self.logger.error("Font system test failed")
                
        except Exception as e:
            self.logger.error(f"Font system initialization failed: {e}")
            self._initialized = False
    
    def get_font(self, size: int) -> Optional[pygame.font.Font]:
        """
        Get a cached font object for the specified size.
        
        Args:
            size: Font size in pixels
            
        Returns:
            pygame.font.Font object or None if unavailable
        """
        if not PYGAME_AVAILABLE or not self._initialized:
            self.logger.warning("Font system not available")
            return None
        
        # Validate font size
        validated_size = self._validate_font_size(size)
        if validated_size != size:
            self.logger.debug(f"Font size adjusted from {size} to {validated_size}")
        
        with self._cache_lock:
            if validated_size not in self._font_cache:
                try:
                    font = pygame.font.Font(None, validated_size)
                    self._font_cache[validated_size] = font
                    self.logger.debug(f"Created and cached font size {validated_size}")
                except Exception as e:
                    self.logger.error(f"Failed to create font size {validated_size}: {e}")
                    return None
            
            return self._font_cache[validated_size]
    
    def get_font_for_category(self, category: FontCategory, scale: float = 1.0) -> Optional[pygame.font.Font]:
        """
        Get a font for a specific category with optional scaling.
        
        Args:
            category: Font category (TITLE, MEDIUM, SMALL, MINIMAL)
            scale: Scale factor (default 1.0)
            
        Returns:
            pygame.font.Font object or None if unavailable
        """
        base_sizes = {
            FontCategory.TITLE: TypographyConstants.TITLE_SIZE,
            FontCategory.MEDIUM: TypographyConstants.MEDIUM_SIZE,
            FontCategory.SMALL: TypographyConstants.SMALL_SIZE,
            FontCategory.MINIMAL: TypographyConstants.MINIMAL_SIZE
        }
        
        base_size = base_sizes.get(category, TypographyConstants.SMALL_SIZE)
        scaled_size = int(base_size * scale)
        
        return self.get_font(scaled_size)
    
    def get_gauge_font(self, font_type: str = "center") -> Optional[pygame.font.Font]:
        """
        Get specialized fonts for gauge mode.
        
        Args:
            font_type: "center" for RPM readout, "label" for tick marks
            
        Returns:
            pygame.font.Font object or None if unavailable
        """
        if font_type == "center":
            return self.get_font(TypographyConstants.GAUGE_CENTER_SIZE)
        elif font_type == "label":
            return self.get_font(TypographyConstants.GAUGE_LABEL_SIZE)
        else:
            self.logger.warning(f"Unknown gauge font type: {font_type}")
            return self.get_font(TypographyConstants.SMALL_SIZE)
    
    def _validate_font_size(self, size: int) -> int:
        """
        Validate and clamp font size to acceptable bounds.
        
        Args:
            size: Requested font size
            
        Returns:
            Validated font size within acceptable range
        """
        if size < TypographyConstants.MIN_FONT_SIZE:
            self.logger.warning(f"Font size {size} below minimum, using {TypographyConstants.MIN_FONT_SIZE}")
            return TypographyConstants.MIN_FONT_SIZE
        elif size > TypographyConstants.MAX_FONT_SIZE:
            self.logger.warning(f"Font size {size} above maximum, using {TypographyConstants.MAX_FONT_SIZE}")
            return TypographyConstants.MAX_FONT_SIZE
        
        return size
    
    def calculate_text_bounds(self, text: str, font_size: int) -> Tuple[int, int]:
        """
        Calculate text dimensions for layout planning.
        
        Args:
            text: Text to measure
            font_size: Font size to use
            
        Returns:
            Tuple of (width, height) in pixels
        """
        font = self.get_font(font_size)
        if not font:
            # Fallback estimation based on typical font metrics
            char_width = font_size * 0.6  # Rough approximation
            return (int(len(text) * char_width), font_size)
        
        try:
            text_surface = font.render(text, True, (255, 255, 255))
            return text_surface.get_size()
        except Exception as e:
            self.logger.error(f"Error calculating text bounds: {e}")
            # Fallback estimation
            char_width = font_size * 0.6
            return (int(len(text) * char_width), font_size)
    
    def validate_text_fits_circular_display(self, text: str, font_size: int, 
                                          center: Tuple[int, int] = None) -> bool:
        """
        Validate that text fits within the circular display constraints.
        
        Args:
            text: Text to validate
            font_size: Font size to use
            center: Center position (defaults to display center)
            
        Returns:
            True if text fits comfortably within circular bounds
        """
        if center is None:
            center = TypographyConstants.DISPLAY_CENTER
        
        width, height = self.calculate_text_bounds(text, font_size)
        
        # Calculate required radius for text
        text_radius = max(width, height) / 2
        
        # Allow some margin from display edge
        max_radius = min(TypographyConstants.DISPLAY_WIDTH, 
                        TypographyConstants.DISPLAY_HEIGHT) / 2 - 20
        
        fits = text_radius <= max_radius
        
        if not fits:
            self.logger.debug(f"Text '{text}' at size {font_size} requires radius {text_radius:.1f}, "
                             f"max available {max_radius:.1f}")
        
        return fits
    
    def clear_cache(self) -> None:
        """Clear the font cache to free memory."""
        with self._cache_lock:
            self._font_cache.clear()
            self.logger.debug("Font cache cleared")
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get information about the current font cache."""
        with self._cache_lock:
            return {
                'cached_fonts': len(self._font_cache),
                'cached_sizes': list(self._font_cache.keys()),
                'initialized': self._initialized
            }


class ButtonRenderer:
    """
    Utility class for rendering standardized buttons with consistent sizing and touch regions.
    
    Features:
    - Standardized button sizes with automatic touch region expansion
    - Visual state management (normal, pressed, disabled)
    - Thread-safe rendering operations
    - Consistent corner radius and styling
    - Automatic font size selection based on button size
    """
    
    def __init__(self, font_manager: Optional[FontManager] = None):
        """
        Initialize button renderer.
        
        Args:
            font_manager: Font manager instance (uses global if None)
        """
        self.logger = logging.getLogger('ButtonRenderer')
        self.font_manager = font_manager or get_font_manager()
        self._render_lock = threading.RLock()
        
        # Button size mappings
        self._size_mappings = {
            ButtonSize.LARGE: TypographyConstants.BUTTON_LARGE,
            ButtonSize.MEDIUM: TypographyConstants.BUTTON_MEDIUM,
            ButtonSize.SMALL: TypographyConstants.BUTTON_SMALL,
            ButtonSize.ICON: TypographyConstants.BUTTON_ICON,
            ButtonSize.FLOATING: TypographyConstants.BUTTON_FLOATING
        }
        
        # Font size mappings
        self._font_mappings = {
            ButtonSize.LARGE: TypographyConstants.BUTTON_FONT_LARGE,
            ButtonSize.MEDIUM: TypographyConstants.BUTTON_FONT_MEDIUM,
            ButtonSize.SMALL: TypographyConstants.BUTTON_FONT_SMALL,
            ButtonSize.ICON: TypographyConstants.BUTTON_FONT_ICON,
            ButtonSize.FLOATING: TypographyConstants.BUTTON_FONT_ICON
        }
        
        # Default colors (can be overridden in render calls)
        self.default_colors = {
            ButtonState.NORMAL: {
                'background': (60, 60, 70),
                'border': (100, 100, 110),
                'text': (255, 255, 255)
            },
            ButtonState.PRESSED: {
                'background': (40, 40, 50),
                'border': (80, 80, 90),
                'text': (200, 200, 200)
            },
            ButtonState.DISABLED: {
                'background': (30, 30, 35),
                'border': (60, 60, 65),
                'text': (120, 120, 120)
            }
        }
    
    def render_button(self, surface, position: Tuple[int, int], text: str, 
                     button_size: ButtonSize, button_id: str,
                     state: ButtonState = ButtonState.NORMAL,
                     colors: Optional[Dict] = None,
                     circular_position: Optional[Tuple[float, float]] = None) -> Tuple[pygame.Rect, pygame.Rect]:
        """
        Render a button with standardized sizing and return both visual and touch regions.
        
        Args:
            surface: Pygame surface to render on
            position: (x, y) position for button center
            text: Button text to display
            button_size: ButtonSize enum value
            button_id: Unique identifier for touch handling
            state: ButtonState for visual styling
            colors: Optional color overrides
            circular_position: Optional (angle_degrees, radius) for circular positioning
            
        Returns:
            Tuple of (visual_rect, touch_rect) - visual bounds and expanded touch region
        """
        try:
            with self._render_lock:
                if not PYGAME_AVAILABLE:
                    self.logger.warning("Pygame not available for button rendering")
                    # Return placeholder rects
                    size = self._size_mappings[button_size]
                    visual_rect = pygame.Rect(position[0] - size[0]//2, position[1] - size[1]//2, size[0], size[1])
                    touch_rect = visual_rect.inflate(TypographyConstants.BUTTON_TOUCH_EXPANSION * 2, 
                                                   TypographyConstants.BUTTON_TOUCH_EXPANSION * 2)
                    return visual_rect, touch_rect
                
                # Get button dimensions and font
                width, height = self._size_mappings[button_size]
                font_size = self._font_mappings[button_size]
                font = self.font_manager.get_font(font_size)
                
                # Handle circular positioning if specified
                if circular_position:
                    angle_degrees, radius = circular_position
                    position = self._position_in_circle(angle_degrees, radius, (width, height))
                
                # Calculate visual rectangle (centered on position)
                visual_rect = pygame.Rect(
                    position[0] - width // 2,
                    position[1] - height // 2,
                    width,
                    height
                )
                
                # Apply pressed state scaling
                if state == ButtonState.PRESSED:
                    scale = TypographyConstants.BUTTON_PRESS_SCALE
                    scaled_width = int(width * scale)
                    scaled_height = int(height * scale)
                    visual_rect = pygame.Rect(
                        position[0] - scaled_width // 2,
                        position[1] - scaled_height // 2,
                        scaled_width,
                        scaled_height
                    )
                
                # Get colors for current state
                button_colors = colors or self.default_colors[state]
                
                # Render button background
                pygame.draw.rect(surface, button_colors['background'], visual_rect, 
                               border_radius=TypographyConstants.BUTTON_CORNER_RADIUS)
                
                # Render button border
                pygame.draw.rect(surface, button_colors['border'], visual_rect, 
                               TypographyConstants.BUTTON_BORDER_WIDTH,
                               border_radius=TypographyConstants.BUTTON_CORNER_RADIUS)
                
                # Render button text
                if font and text:
                    text_surface = font.render(text, True, button_colors['text'])
                    text_rect = text_surface.get_rect(center=visual_rect.center)
                    surface.blit(text_surface, text_rect)
                
                # Calculate expanded touch region
                expansion = TypographyConstants.BUTTON_TOUCH_EXPANSION
                touch_rect = pygame.Rect(
                    visual_rect.x - expansion,
                    visual_rect.y - expansion,
                    visual_rect.width + 2 * expansion,
                    visual_rect.height + 2 * expansion
                )
                
                self.logger.debug(f"Rendered button '{button_id}': visual={visual_rect}, touch={touch_rect}")
                
                return visual_rect, touch_rect
                
        except Exception as e:
            self.logger.error(f"Error rendering button '{button_id}': {e}")
            # Return safe fallback rects
            size = self._size_mappings.get(button_size, (80, 35))
            fallback_rect = pygame.Rect(position[0] - size[0]//2, position[1] - size[1]//2, size[0], size[1])
            return fallback_rect, fallback_rect.inflate(16, 16)
    
    def _position_in_circle(self, angle_degrees: float, radius: float, 
                          element_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculate position for button in circular layout.
        
        Args:
            angle_degrees: Angle in degrees (0 = right, 90 = down, etc.)
            radius: Distance from display center
            element_size: (width, height) of element
            
        Returns:
            (x, y) coordinates for element center
        """
        try:
            import math
            
            # Convert to radians
            angle_rad = math.radians(angle_degrees)
            
            # Calculate position relative to display center
            center_x, center_y = TypographyConstants.DISPLAY_CENTER
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            
            # Validate bounds
            width, height = element_size
            expansion = TypographyConstants.BUTTON_TOUCH_EXPANSION
            
            # Check if touch region fits within display bounds
            touch_left = x - width//2 - expansion
            touch_right = x + width//2 + expansion
            touch_top = y - height//2 - expansion
            touch_bottom = y + height//2 + expansion
            
            if (touch_left < 0 or touch_right > TypographyConstants.DISPLAY_WIDTH or
                touch_top < 0 or touch_bottom > TypographyConstants.DISPLAY_HEIGHT):
                self.logger.warning(f"Button at angle {angle_degrees}°, radius {radius} extends outside display")
            
            return (int(x), int(y))
            
        except Exception as e:
            self.logger.error(f"Error calculating circular position: {e}")
            # Fallback to center
            return TypographyConstants.DISPLAY_CENTER
    
    def get_button_dimensions(self, button_size: ButtonSize) -> Tuple[int, int]:
        """Get visual dimensions for a button size."""
        return self._size_mappings[button_size]
    
    def get_button_font_size(self, button_size: ButtonSize) -> int:
        """Get recommended font size for a button size."""
        return self._font_mappings[button_size]
    
    def create_touch_region_data(self, button_id: str, visual_rect: pygame.Rect, 
                               touch_rect: pygame.Rect, action_data: Any = None) -> Tuple[str, pygame.Rect, Any]:
        """
        Create touch region data tuple for integration with existing touch handling.
        
        Args:
            button_id: Unique button identifier
            visual_rect: Visual button rectangle
            touch_rect: Expanded touch rectangle
            action_data: Optional data for touch handler
            
        Returns:
            Tuple of (button_id, touch_rect, action_data) for touch region list
        """
        return (button_id, touch_rect, action_data)
    
    def validate_button_layout(self, buttons: List[Dict]) -> List[str]:
        """
        Validate that button layout doesn't have overlapping touch regions.
        
        Args:
            buttons: List of button specs with 'position', 'size', etc.
            
        Returns:
            List of warning messages about overlaps
        """
        warnings = []
        touch_rects = []
        
        try:
            for i, button in enumerate(buttons):
                pos = button.get('position', (0, 0))
                size = button.get('size', ButtonSize.MEDIUM)
                width, height = self._size_mappings[size]
                
                # Calculate touch rect
                expansion = TypographyConstants.BUTTON_TOUCH_EXPANSION
                touch_rect = pygame.Rect(
                    pos[0] - width//2 - expansion,
                    pos[1] - height//2 - expansion,
                    width + 2 * expansion,
                    height + 2 * expansion
                )
                
                # Check for overlaps with previous buttons
                for j, other_rect in enumerate(touch_rects):
                    if touch_rect.colliderect(other_rect):
                        warnings.append(f"Button {i} overlaps with button {j}")
                
                touch_rects.append(touch_rect)
                
        except Exception as e:
            warnings.append(f"Layout validation error: {e}")
        
        return warnings


# Global font manager instance
_font_manager = None
_manager_lock = threading.Lock()


def get_font_manager() -> FontManager:
    """
    Get the global font manager instance (thread-safe singleton).
    
    Returns:
        FontManager instance
    """
    global _font_manager
    
    if _font_manager is None:
        with _manager_lock:
            if _font_manager is None:
                _font_manager = FontManager()
    
    return _font_manager


def get_font(size: int) -> Optional[pygame.font.Font]:
    """
    Convenience function to get a font of specified size.
    
    Args:
        size: Font size in pixels
        
    Returns:
        pygame.font.Font object or None if unavailable
    """
    return get_font_manager().get_font(size)


def get_title_font(scale: float = 1.0) -> Optional[pygame.font.Font]:
    """Get font for title/main display elements."""
    return get_font_manager().get_font_for_category(FontCategory.TITLE, scale)


def get_medium_font(scale: float = 1.0) -> Optional[pygame.font.Font]:
    """Get font for medium/header elements."""
    return get_font_manager().get_font_for_category(FontCategory.MEDIUM, scale)


def get_small_font(scale: float = 1.0) -> Optional[pygame.font.Font]:
    """Get font for small/label elements."""
    return get_font_manager().get_font_for_category(FontCategory.SMALL, scale)


def get_minimal_font(scale: float = 1.0) -> Optional[pygame.font.Font]:
    """Get font for minimal/status elements."""
    return get_font_manager().get_font_for_category(FontCategory.MINIMAL, scale)


def get_rpm_large_font() -> Optional[pygame.font.Font]:
    """Get font for large RPM display (digital mode)."""
    return get_font_manager().get_font(TypographyConstants.FONT_RPM_LARGE)


def get_rpm_medium_font() -> Optional[pygame.font.Font]:
    """Get font for medium RPM display (gauge center)."""
    return get_font_manager().get_font(TypographyConstants.FONT_RPM_MEDIUM)


def get_label_small_font() -> Optional[pygame.font.Font]:
    """Get font for small labels and text."""
    return get_font_manager().get_font(TypographyConstants.FONT_LABEL_SMALL)


def get_title_display_font() -> Optional[pygame.font.Font]:
    """Get font for titles and headers."""
    return get_font_manager().get_font(TypographyConstants.FONT_TITLE)


def get_heading_font() -> Optional[pygame.font.Font]:
    """Get font for section headings."""
    return get_font_manager().get_font(TypographyConstants.FONT_HEADING)


def get_body_font() -> Optional[pygame.font.Font]:
    """Get font for body text and descriptions."""
    return get_font_manager().get_font(TypographyConstants.FONT_BODY)


def get_button_font() -> Optional[pygame.font.Font]:
    """Get font for button text."""
    return get_font_manager().get_font(TypographyConstants.FONT_BUTTON)


def get_minimal_font() -> Optional[pygame.font.Font]:
    """Get font for minimal/compact text elements."""
    return get_font_manager().get_font(TypographyConstants.FONT_MINIMAL)


def validate_font_system() -> Dict[str, bool]:
    """
    Validate the font system is working correctly.
    
    Returns:
        Dictionary with validation results
    """
    manager = get_font_manager()
    
    results = {
        'pygame_available': PYGAME_AVAILABLE,
        'font_system_initialized': manager._initialized,
        'can_create_fonts': False,
        'cache_working': False
    }
    
    if PYGAME_AVAILABLE and manager._initialized:
        # Test font creation
        test_font = manager.get_font(24)
        results['can_create_fonts'] = test_font is not None
        
        # Test caching
        test_font2 = manager.get_font(24)
        results['cache_working'] = test_font is test_font2
    
    return results


# Global button renderer instance
_button_renderer = None
_button_renderer_lock = threading.Lock()


def get_button_renderer() -> ButtonRenderer:
    """
    Get the global button renderer instance (thread-safe singleton).
    
    Returns:
        ButtonRenderer instance
    """
    global _button_renderer
    
    if _button_renderer is None:
        with _button_renderer_lock:
            if _button_renderer is None:
                _button_renderer = ButtonRenderer()
    
    return _button_renderer


def render_standard_button(surface, position: Tuple[int, int], text: str,
                         button_size: ButtonSize, button_id: str,
                         state: ButtonState = ButtonState.NORMAL,
                         colors: Optional[Dict] = None,
                         circular_position: Optional[Tuple[float, float]] = None) -> Tuple[pygame.Rect, pygame.Rect]:
    """
    Convenience function to render a standardized button.
    
    Args:
        surface: Pygame surface to render on
        position: (x, y) position for button center
        text: Button text to display
        button_size: ButtonSize enum value
        button_id: Unique identifier for touch handling
        state: ButtonState for visual styling
        colors: Optional color overrides
        circular_position: Optional (angle_degrees, radius) for circular positioning
        
    Returns:
        Tuple of (visual_rect, touch_rect) - visual bounds and expanded touch region
    """
    return get_button_renderer().render_button(
        surface, position, text, button_size, button_id, state, colors, circular_position
    )


def get_button_size_info(button_size: ButtonSize) -> Dict[str, Any]:
    """
    Get comprehensive information about a button size.
    
    Args:
        button_size: ButtonSize enum value
        
    Returns:
        Dictionary with size info including dimensions, font size, etc.
    """
    renderer = get_button_renderer()
    width, height = renderer.get_button_dimensions(button_size)
    font_size = renderer.get_button_font_size(button_size)
    
    return {
        'visual_size': (width, height),
        'touch_size': (width + 2 * TypographyConstants.BUTTON_TOUCH_EXPANSION,
                      height + 2 * TypographyConstants.BUTTON_TOUCH_EXPANSION),
        'font_size': font_size,
        'corner_radius': TypographyConstants.BUTTON_CORNER_RADIUS,
        'border_width': TypographyConstants.BUTTON_BORDER_WIDTH,
        'touch_expansion': TypographyConstants.BUTTON_TOUCH_EXPANSION
    }


def validate_button_system() -> Dict[str, Any]:
    """
    Validate the button rendering system is working correctly.
    
    Returns:
        Dictionary with validation results and system information
    """
    try:
        renderer = get_button_renderer()
        
        results = {
            'button_renderer_available': renderer is not None,
            'pygame_available': PYGAME_AVAILABLE,
            'button_sizes': {},
            'font_mappings': {},
            'validation_errors': []
        }
        
        # Test all button sizes
        for size in ButtonSize:
            try:
                dimensions = renderer.get_button_dimensions(size)
                font_size = renderer.get_button_font_size(size)
                
                results['button_sizes'][size.value] = {
                    'dimensions': dimensions,
                    'font_size': font_size,
                    'valid': dimensions[0] > 0 and dimensions[1] > 0 and font_size > 0
                }
                
            except Exception as e:
                results['validation_errors'].append(f"Error with {size.value}: {e}")
        
        # Test font mappings
        try:
            font_manager = get_font_manager()
            for size in ButtonSize:
                font_size = renderer.get_button_font_size(size)
                font = font_manager.get_font(font_size)
                results['font_mappings'][size.value] = font is not None
                
        except Exception as e:
            results['validation_errors'].append(f"Font mapping error: {e}")
        
        results['overall_valid'] = len(results['validation_errors']) == 0
        
        return results
        
    except Exception as e:
        return {
            'button_renderer_available': False,
            'error': str(e),
            'overall_valid': False
        }