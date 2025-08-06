#!/usr/bin/env python3
"""
Splash screen graphics utilities for OBDII display application.
Provides automotive-themed graphics components with professional styling.
"""

import math
import logging
from typing import Tuple, Optional

# Conditional pygame import with fallback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

# Professional automotive color palette
AUTOMOTIVE_COLORS = {
    # Primary colors
    'primary_blue': (64, 150, 255),      # OBD connector blue
    'primary_orange': (255, 140, 0),     # Warning/diagnostic orange
    'primary_green': (50, 200, 50),      # Connected/ready green
    'primary_red': (255, 60, 60),        # Error/danger red
    
    # Background colors
    'dark_background': (15, 20, 25),     # Main dark background
    'surface_dark': (25, 30, 35),        # Elevated surface
    'surface_medium': (40, 45, 50),      # Medium surface
    'surface_light': (60, 65, 70),       # Light surface
    
    # Text colors
    'text_primary': (255, 255, 255),     # Primary white text
    'text_secondary': (200, 210, 220),   # Secondary light gray
    'text_tertiary': (150, 160, 170),    # Tertiary medium gray
    'text_disabled': (100, 110, 120),    # Disabled dark gray
    
    # Accent colors
    'accent_bright': (100, 200, 255),    # Bright accent
    'accent_warm': (255, 180, 100),      # Warm accent
    'accent_cool': (100, 255, 200),      # Cool accent
    
    # Gauge colors
    'gauge_normal': (50, 200, 50),       # Normal operation green
    'gauge_warning': (255, 165, 0),      # Warning orange
    'gauge_danger': (255, 50, 50),       # Danger red
    'gauge_background': (30, 35, 40),    # Gauge background
    'gauge_tick': (180, 190, 200),       # Tick mark color
}

# Splash screen specific colors
SPLASH_COLORS = {
    'background': AUTOMOTIVE_COLORS['dark_background'],
    'title_text': AUTOMOTIVE_COLORS['text_primary'],
    'subtitle_text': AUTOMOTIVE_COLORS['text_secondary'],
    'progress_fill': AUTOMOTIVE_COLORS['primary_blue'],
    'progress_background': AUTOMOTIVE_COLORS['surface_medium'],
    'connector_active': AUTOMOTIVE_COLORS['primary_green'],
    'connector_inactive': AUTOMOTIVE_COLORS['surface_light'],
    'gauge_active': AUTOMOTIVE_COLORS['primary_blue'],
    'animation_primary': AUTOMOTIVE_COLORS['accent_bright'],
    'border': AUTOMOTIVE_COLORS['surface_light']
}

def draw_automotive_gauge(surface, center: Tuple[int, int], radius: int, 
                         progress: float) -> bool:
    """
    Draw an automotive-style circular gauge with progress indication.
    
    Renders a professional gauge similar to those found in modern vehicles,
    with tick marks, colored zones, and a progress indicator suitable for
    startup progress or diagnostic status display.
    
    Args:
        surface: Pygame surface to draw on
        center: Center point as (x, y) tuple
        radius: Gauge radius in pixels
        progress: Progress value from 0.0 to 1.0
        
    Returns:
        bool: True if drawing succeeded, False on error
        
    Raises:
        None: All exceptions are caught and logged
    """
    if not PYGAME_AVAILABLE or surface is None:
        return False
        
    logger = logging.getLogger('SplashGraphics')
    
    try:
        center_x, center_y = center
        
        # Validate inputs
        if radius <= 0 or progress < 0:
            logger.warning(f"Invalid gauge parameters: radius={radius}, progress={progress}")
            return False
            
        # Clamp progress to valid range
        progress = max(0.0, min(1.0, progress))
        
        # Gauge configuration
        start_angle = 225  # Start at bottom-left (225 degrees)
        end_angle = -45    # End at bottom-right (-45 degrees)
        total_sweep = 270  # Total 270-degree sweep
        
        # Draw gauge background ring
        background_thickness = max(2, radius // 20)
        try:
            pygame.draw.circle(surface, AUTOMOTIVE_COLORS['gauge_background'], 
                             center, radius, background_thickness)
        except Exception as e:
            logger.error(f"Error drawing gauge background: {e}")
            return False
        
        # Draw tick marks around the gauge
        tick_count = 12  # Major tick marks
        minor_tick_count = 60  # Minor tick marks
        
        # Draw minor ticks
        for i in range(minor_tick_count):
            angle = start_angle - (i / minor_tick_count * total_sweep)
            angle_rad = math.radians(angle)
            
            # Calculate tick positions
            outer_radius = radius - background_thickness
            inner_radius = outer_radius - (radius // 25)  # Short minor ticks
            
            outer_x = center_x + int(outer_radius * math.cos(angle_rad))
            outer_y = center_y - int(outer_radius * math.sin(angle_rad))
            inner_x = center_x + int(inner_radius * math.cos(angle_rad))
            inner_y = center_y - int(inner_radius * math.sin(angle_rad))
            
            tick_color = AUTOMOTIVE_COLORS['gauge_tick']
            tick_width = 1
            
            try:
                pygame.draw.line(surface, tick_color, (outer_x, outer_y), 
                               (inner_x, inner_y), tick_width)
            except Exception:
                continue  # Skip individual tick errors
        
        # Draw major ticks
        for i in range(tick_count):
            angle = start_angle - (i / tick_count * total_sweep)
            angle_rad = math.radians(angle)
            
            # Calculate tick positions
            outer_radius = radius - background_thickness
            inner_radius = outer_radius - (radius // 12)  # Longer major ticks
            
            outer_x = center_x + int(outer_radius * math.cos(angle_rad))
            outer_y = center_y - int(outer_radius * math.sin(angle_rad))
            inner_x = center_x + int(inner_radius * math.cos(angle_rad))
            inner_y = center_y - int(inner_radius * math.sin(angle_rad))
            
            tick_color = AUTOMOTIVE_COLORS['text_secondary']
            tick_width = 2
            
            try:
                pygame.draw.line(surface, tick_color, (outer_x, outer_y), 
                               (inner_x, inner_y), tick_width)
            except Exception:
                continue  # Skip individual tick errors
        
        # Draw progress arc
        if progress > 0:
            progress_angle = progress * total_sweep
            progress_thickness = max(3, radius // 15)
            
            # Calculate color based on progress
            if progress < 0.6:
                arc_color = AUTOMOTIVE_COLORS['gauge_normal']
            elif progress < 0.85:
                arc_color = AUTOMOTIVE_COLORS['gauge_warning']
            else:
                arc_color = AUTOMOTIVE_COLORS['gauge_danger']
            
            # Draw progress arc using multiple lines for smooth appearance
            arc_radius = radius - background_thickness - (progress_thickness // 2)
            arc_steps = max(10, int(progress_angle))
            
            for i in range(arc_steps):
                angle = start_angle - (i / arc_steps * progress_angle)
                next_angle = start_angle - ((i + 1) / arc_steps * progress_angle)
                
                angle_rad = math.radians(angle)
                next_angle_rad = math.radians(next_angle)
                
                x1 = center_x + int(arc_radius * math.cos(angle_rad))
                y1 = center_y - int(arc_radius * math.sin(angle_rad))
                x2 = center_x + int(arc_radius * math.cos(next_angle_rad))
                y2 = center_y - int(arc_radius * math.sin(next_angle_rad))
                
                try:
                    pygame.draw.line(surface, arc_color, (x1, y1), (x2, y2), 
                                   progress_thickness)
                except Exception:
                    continue
        
        # Draw center hub
        hub_radius = max(3, radius // 15)
        try:
            pygame.draw.circle(surface, AUTOMOTIVE_COLORS['surface_medium'], 
                             center, hub_radius)
            pygame.draw.circle(surface, AUTOMOTIVE_COLORS['text_secondary'], 
                             center, hub_radius, 1)
        except Exception as e:
            logger.error(f"Error drawing gauge hub: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Automotive gauge drawing failed: {e}")
        return False


def draw_obdii_connector(surface, center: Tuple[int, int], size: int, 
                        connected_state: bool) -> bool:
    """
    Draw a stylized OBD-II diagnostic connector icon.
    
    Renders a recognizable OBD-II connector shape with visual state indication
    for connection status. Uses automotive styling with appropriate colors
    and professional appearance.
    
    Args:
        surface: Pygame surface to draw on
        center: Center point as (x, y) tuple
        size: Connector size (width) in pixels
        connected_state: True for connected appearance, False for disconnected
        
    Returns:
        bool: True if drawing succeeded, False on error
        
    Raises:
        None: All exceptions are caught and logged
    """
    if not PYGAME_AVAILABLE or surface is None:
        return False
        
    logger = logging.getLogger('SplashGraphics')
    
    try:
        center_x, center_y = center
        
        # Validate inputs
        if size <= 0:
            logger.warning(f"Invalid connector size: {size}")
            return False
        
        # Choose colors based on connection state
        if connected_state:
            primary_color = SPLASH_COLORS['connector_active']
            secondary_color = AUTOMOTIVE_COLORS['primary_green']
            outline_color = AUTOMOTIVE_COLORS['accent_bright']
        else:
            primary_color = SPLASH_COLORS['connector_inactive']
            secondary_color = AUTOMOTIVE_COLORS['surface_medium']
            outline_color = AUTOMOTIVE_COLORS['text_tertiary']
        
        # Connector dimensions
        connector_width = size
        connector_height = int(size * 0.6)
        corner_radius = max(2, size // 20)
        
        # Main connector body (rounded rectangle)
        connector_rect = pygame.Rect(
            center_x - connector_width // 2,
            center_y - connector_height // 2,
            connector_width,
            connector_height
        )
        
        # Draw connector body
        try:
            pygame.draw.rect(surface, primary_color, connector_rect, 
                           border_radius=corner_radius)
            pygame.draw.rect(surface, outline_color, connector_rect, 2, 
                           border_radius=corner_radius)
        except Exception as e:
            logger.error(f"Error drawing connector body: {e}")
            return False
        
        # Draw connector pins (small rectangles)
        pin_width = max(2, size // 20)
        pin_height = max(4, size // 15)
        pin_spacing = max(6, size // 12)
        pin_count = 8  # Typical OBD-II pin count (simplified)
        
        # Calculate pin layout
        total_pin_width = (pin_count - 1) * pin_spacing
        pin_start_x = center_x - total_pin_width // 2
        pin_y = center_y - pin_height // 2
        
        # Draw pins in two rows (typical OBD-II layout)
        for row in range(2):
            for pin in range(pin_count // 2):
                pin_x = pin_start_x + pin * pin_spacing * 2
                pin_y_offset = pin_y + (row * (pin_height + 2))
                
                pin_rect = pygame.Rect(pin_x, pin_y_offset, pin_width, pin_height)
                
                try:
                    # Alternate pin colors for visual interest
                    pin_color = secondary_color if (pin + row) % 2 else outline_color
                    pygame.draw.rect(surface, pin_color, pin_rect)
                except Exception:
                    continue  # Skip individual pin errors
        
        # Draw cable connection indicator
        if connected_state:
            cable_width = max(3, size // 15)
            cable_length = max(10, size // 8)
            cable_x = center_x
            cable_y = center_y + connector_height // 2
            
            try:
                # Draw simple cable representation
                pygame.draw.line(surface, AUTOMOTIVE_COLORS['primary_green'],
                               (cable_x, cable_y), 
                               (cable_x, cable_y + cable_length), cable_width)
                
                # Draw cable connector end
                end_size = max(2, size // 25)
                pygame.draw.circle(surface, AUTOMOTIVE_COLORS['accent_bright'],
                                 (cable_x, cable_y + cable_length), end_size)
            except Exception as e:
                logger.error(f"Error drawing cable indicator: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"OBD-II connector drawing failed: {e}")
        return False


def draw_progress_bar(surface, rect: pygame.Rect, progress: float, 
                     color: Optional[Tuple[int, int, int]] = None) -> bool:
    """
    Draw a modern progress bar with rounded corners and smooth gradients.
    
    Creates a professional progress bar suitable for automotive applications
    with customizable styling and smooth visual progression indication.
    
    Args:
        surface: Pygame surface to draw on
        rect: Rectangle defining the progress bar bounds
        progress: Progress value from 0.0 to 1.0
        color: Optional custom color tuple (R, G, B). Uses default if None
        
    Returns:
        bool: True if drawing succeeded, False on error
        
    Raises:
        None: All exceptions are caught and logged
    """
    if not PYGAME_AVAILABLE or surface is None or rect is None:
        return False
        
    logger = logging.getLogger('SplashGraphics')
    
    try:
        # Validate inputs
        if progress < 0:
            logger.warning(f"Invalid progress value: {progress}")
            return False
            
        # Clamp progress to valid range
        progress = max(0.0, min(1.0, progress))
        
        # Use default color if none provided
        if color is None:
            color = SPLASH_COLORS['progress_fill']
        
        # Progress bar styling
        border_radius = max(2, min(rect.height // 4, 8))
        border_width = max(1, rect.height // 20)
        
        # Draw background
        background_color = SPLASH_COLORS['progress_background']
        try:
            pygame.draw.rect(surface, background_color, rect, 
                           border_radius=border_radius)
        except Exception as e:
            logger.error(f"Error drawing progress background: {e}")
            return False
        
        # Draw progress fill
        if progress > 0:
            fill_width = int(rect.width * progress)
            if fill_width > 0:
                fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
                
                try:
                    pygame.draw.rect(surface, color, fill_rect, 
                                   border_radius=border_radius)
                except Exception as e:
                    logger.error(f"Error drawing progress fill: {e}")
        
        # Draw border
        border_color = AUTOMOTIVE_COLORS['text_tertiary']
        try:
            pygame.draw.rect(surface, border_color, rect, border_width, 
                           border_radius=border_radius)
        except Exception as e:
            logger.error(f"Error drawing progress border: {e}")
        
        # Add highlight effect for enhanced appearance
        if progress > 0.1:  # Only show highlight when some progress is visible
            highlight_height = max(1, rect.height // 8)
            highlight_rect = pygame.Rect(rect.x + border_width, 
                                       rect.y + border_width,
                                       int((rect.width - 2 * border_width) * progress),
                                       highlight_height)
            
            # Create lighter version of the color for highlight
            highlight_color = tuple(min(255, c + 40) for c in color)
            
            try:
                pygame.draw.rect(surface, highlight_color, highlight_rect,
                               border_radius=max(1, border_radius // 2))
            except Exception as e:
                logger.debug(f"Highlight effect failed: {e}")  # Non-critical
        
        return True
        
    except Exception as e:
        logger.error(f"Progress bar drawing failed: {e}")
        return False


def draw_animated_dots(surface, center: Tuple[int, int], frame_count: int, 
                      animation_speed: float = 1.0) -> bool:
    """
    Draw animated loading dots with smooth pulsing and rotation effects.
    
    Creates a set of dots that pulse and rotate to indicate loading/processing
    activity. Designed for automotive applications with appropriate timing
    and visual effects.
    
    Args:
        surface: Pygame surface to draw on
        center: Center point as (x, y) tuple
        frame_count: Current frame number for animation timing
        animation_speed: Animation speed multiplier (default 1.0)
        
    Returns:
        bool: True if drawing succeeded, False on error
        
    Raises:
        None: All exceptions are caught and logged
    """
    if not PYGAME_AVAILABLE or surface is None:
        return False
        
    logger = logging.getLogger('SplashGraphics')
    
    try:
        center_x, center_y = center
        
        # Animation configuration
        dot_count = 8
        base_radius = 20  # Distance from center
        dot_size_base = 3
        dot_size_max = 6
        rotation_speed = 2.0 * animation_speed  # Degrees per frame
        pulse_speed = 0.1 * animation_speed  # Pulse cycle speed
        
        # Calculate rotation angle
        rotation_angle = (frame_count * rotation_speed) % 360
        
        # Draw each dot
        for i in range(dot_count):
            # Calculate dot position
            dot_angle = rotation_angle + (i * 360 / dot_count)
            dot_angle_rad = math.radians(dot_angle)
            
            dot_x = center_x + int(base_radius * math.cos(dot_angle_rad))
            dot_y = center_y - int(base_radius * math.sin(dot_angle_rad))
            
            # Calculate pulsing effect
            pulse_phase = (frame_count * pulse_speed + i * 0.3) % (2 * math.pi)
            pulse_factor = (math.sin(pulse_phase) + 1) / 2  # 0 to 1
            
            # Calculate dot size and opacity
            dot_size = int(dot_size_base + (dot_size_max - dot_size_base) * pulse_factor)
            
            # Calculate color with fading effect
            base_color = SPLASH_COLORS['animation_primary']
            fade_factor = 0.3 + 0.7 * pulse_factor  # 0.3 to 1.0
            
            dot_color = tuple(int(c * fade_factor) for c in base_color)
            
            try:
                # Draw main dot
                pygame.draw.circle(surface, dot_color, (dot_x, dot_y), dot_size)
                
                # Draw inner highlight for depth effect
                if dot_size > 2:
                    highlight_size = max(1, dot_size - 2)
                    highlight_color = tuple(min(255, c + 50) for c in dot_color)
                    pygame.draw.circle(surface, highlight_color, 
                                     (dot_x - 1, dot_y - 1), highlight_size)
                
            except Exception:
                continue  # Skip individual dot errors
        
        # Draw center indicator (optional)
        try:
            center_pulse = (math.sin(frame_count * pulse_speed * 2) + 1) / 2
            center_size = int(2 + 2 * center_pulse)
            center_color = AUTOMOTIVE_COLORS['accent_bright']
            
            pygame.draw.circle(surface, center_color, center, center_size)
        except Exception as e:
            logger.debug(f"Center indicator failed: {e}")  # Non-critical
        
        return True
        
    except Exception as e:
        logger.error(f"Animated dots drawing failed: {e}")
        return False


def create_gradient_surface(size: Tuple[int, int], color_start: Tuple[int, int, int],
                           color_end: Tuple[int, int, int], vertical: bool = True) -> Optional[pygame.Surface]:
    """
    Create a gradient surface for enhanced visual effects.
    
    Args:
        size: Surface size as (width, height)
        color_start: Starting color as (R, G, B)
        color_end: Ending color as (R, G, B)
        vertical: True for vertical gradient, False for horizontal
        
    Returns:
        pygame.Surface or None: Gradient surface or None on error
    """
    if not PYGAME_AVAILABLE:
        return None
        
    logger = logging.getLogger('SplashGraphics')
    
    try:
        width, height = size
        surface = pygame.Surface(size)
        
        # Calculate color step
        steps = height if vertical else width
        if steps <= 0:
            return surface
            
        r_step = (color_end[0] - color_start[0]) / steps
        g_step = (color_end[1] - color_start[1]) / steps
        b_step = (color_end[2] - color_start[2]) / steps
        
        # Draw gradient
        for i in range(steps):
            r = int(color_start[0] + r_step * i)
            g = int(color_start[1] + g_step * i)
            b = int(color_start[2] + b_step * i)
            
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            
            if vertical:
                line_rect = pygame.Rect(0, i, width, 1)
            else:
                line_rect = pygame.Rect(i, 0, 1, height)
                
            pygame.draw.rect(surface, color, line_rect)
        
        return surface
        
    except Exception as e:
        logger.error(f"Gradient surface creation failed: {e}")
        return None