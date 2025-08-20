#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Device surface renderer for setup mode.
Handles device representation graphics with efficient caching and resource management.
"""

import logging
import threading
import time
from typing import Optional, Tuple, Dict, Any

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

from ...setup_models import BluetoothDevice, DeviceType
from ...typography import (get_font_manager, get_body_font, get_minimal_font, 
                          get_label_small_font, TypographyConstants)


class DeviceSurfaceRenderer:
    """Device representation graphics with efficient caching and resource management"""
    
    def __init__(self):
        self.logger = logging.getLogger('DeviceSurfaceRenderer')
        
        # Check pygame availability
        if not PYGAME_AVAILABLE:
            self.logger.warning("Pygame not available - device surface rendering disabled")
            self.display_available = False
        else:
            self.display_available = True
        
        # Colors for device rendering
        self.colors = {
            'background': (20, 20, 30),
            'surface': (40, 40, 50),
            'primary': (100, 150, 250),
            'text': (220, 220, 220),
            'text_dim': (160, 160, 160),
            'border': (60, 60, 70),
            'elm327_likely': (50, 200, 50),
            'possibly_compatible': (255, 165, 0),
            'unknown_device': (150, 150, 150)
        }
        
        # Device surface cache with thread safety
        self._device_item_cache = {}
        self._device_cache_lock = threading.Lock()
        
        # Performance tracking
        self._render_stats = {
            'total_renders': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'slow_renders': 0
        }
    
    def get_signal_bars(self, rssi: int) -> int:
        """Convert RSSI to signal bar count (0-4)"""
        if rssi >= -30:
            return 4
        elif rssi >= -50:
            return 3
        elif rssi >= -70:
            return 2
        elif rssi >= -80:
            return 1
        else:
            return 0
    
    def get_device_type_color(self, device: BluetoothDevice) -> Tuple[int, int, int]:
        """Get color for device type indicator"""
        if hasattr(device, 'device_classification'):
            if device.device_classification == DeviceType.HIGHLY_LIKELY_ELM327:
                return self.colors['elm327_likely']
            elif device.device_classification == DeviceType.POSSIBLY_COMPATIBLE:
                return self.colors['possibly_compatible']
            else:
                return self.colors['unknown_device']
        else:
            return self.colors['elm327_likely'] if device.device_type == 'ELM327' else self.colors['unknown_device']
    
    def get_device_type_text(self, device: BluetoothDevice) -> str:
        """Get text description for device type"""
        if hasattr(device, 'device_classification'):
            if device.device_classification == DeviceType.HIGHLY_LIKELY_ELM327:
                return "ELM327"
            elif device.device_classification == DeviceType.POSSIBLY_COMPATIBLE:
                return "Compatible"
            else:
                return "Unknown"
        else:
            return device.device_type
    
    def _truncate_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        """Truncate text to fit within max_width"""
        if not self.display_available:
            return text
        
        try:
            if font.size(text)[0] <= max_width:
                return text
            
            truncated = text
            while len(truncated) > 0 and font.size(truncated + "...")[0] > max_width:
                truncated = truncated[:-1]
            
            return truncated + "..." if truncated != text else text
            
        except Exception as e:
            self.logger.error(f"Error truncating text: {e}")
            return text[:20]  # Fallback truncation
    
    def render_compact_device_item(self, device: BluetoothDevice, item_width: int = 400, 
                                 item_height: int = 45, item_index: int = 0, 
                                 use_alternating_bg: bool = True) -> Tuple[Optional[pygame.Surface], pygame.Rect]:
        """Render a single device item in compact format with caching"""
        if not self.display_available:
            return None, pygame.Rect(0, 0, item_width, item_height)
        
        start_time = time.time()
        self._render_stats['total_renders'] += 1
        
        try:
            # Create cache key
            cache_key = f"compact_{device.mac_address}_{item_index}_{item_width}_{item_height}_{use_alternating_bg}"
            
            # Check cache first
            with self._device_cache_lock:
                if cache_key in self._device_item_cache:
                    self._render_stats['cache_hits'] += 1
                    cached_surface, cached_rect = self._device_item_cache[cache_key]
                    return cached_surface, cached_rect
            
            self._render_stats['cache_misses'] += 1
            
            # Create item surface
            item_surface = pygame.Surface((item_width, item_height), pygame.SRCALPHA)
            
            # Alternating background
            if use_alternating_bg and item_index % 2 == 1:
                bg_color = (25, 25, 35)
            else:
                bg_color = self.colors['surface']
            
            # Draw background with rounded corners
            item_rect = pygame.Rect(0, 0, item_width, item_height - 2)
            pygame.draw.rect(item_surface, bg_color, item_rect, border_radius=8)
            
            # Device type indicator - 6px colored circle
            indicator_color = self.get_device_type_color(device)
            indicator_center = (12, item_height // 2)
            pygame.draw.circle(item_surface, indicator_color, indicator_center, 6)
            
            # Device name - body font
            try:
                name_font = get_body_font()
                if not name_font:
                    name_font = pygame.font.Font(None, 20)
            except Exception as e:
                self.logger.error(f"Error getting body font for device name: {e}")
                name_font = pygame.font.Font(None, 20)
            
            # Truncate device name if too long
            device_name = device.name
            max_name_width = item_width - 120  # Leave space for signal and type
            device_name = self._truncate_text(device_name, name_font, max_name_width)
            
            name_surface = name_font.render(device_name, True, self.colors['text'])
            item_surface.blit(name_surface, (24, 8))
            
            # Device type text - minimal font
            try:
                type_font = get_minimal_font()
                if not type_font:
                    type_font = pygame.font.Font(None, 14)
            except Exception as e:
                self.logger.error(f"Error getting minimal font for device type: {e}")
                type_font = pygame.font.Font(None, 14)
            
            device_type_text = self.get_device_type_text(device)
            type_surface = type_font.render(device_type_text, True, self.colors['text_dim'])
            item_surface.blit(type_surface, (24, 26))
            
            # Signal strength indicator
            if hasattr(device, 'rssi') and device.rssi is not None:
                signal_bars = self.get_signal_bars(device.rssi)
                signal_x = item_width - 35
                signal_y = item_height // 2 - 8
                
                for i in range(4):
                    bar_height = 4 + i * 3
                    bar_color = self.colors['primary'] if i < signal_bars else self.colors['border']
                    bar_rect = pygame.Rect(signal_x + i * 4, signal_y + (16 - bar_height), 3, bar_height)
                    pygame.draw.rect(item_surface, bar_color, bar_rect)
                
                # Signal strength text
                try:
                    signal_font = get_label_small_font()
                    if not signal_font:
                        signal_font = pygame.font.Font(None, 12)
                except Exception:
                    signal_font = pygame.font.Font(None, 12)
                
                rssi_text = f"{device.rssi}dBm"
                rssi_surface = signal_font.render(rssi_text, True, self.colors['text_dim'])
                rssi_rect = rssi_surface.get_rect()
                rssi_x = signal_x + 16 - rssi_rect.width // 2
                item_surface.blit(rssi_surface, (rssi_x, signal_y + 18))
            
            # Cache the rendered item
            with self._device_cache_lock:
                if len(self._device_item_cache) > 50:
                    # Remove oldest entries
                    cache_keys = list(self._device_item_cache.keys())
                    for old_key in cache_keys[:20]:
                        del self._device_item_cache[old_key]
                
                self._device_item_cache[cache_key] = (item_surface, item_rect)
            
            # Track slow renders
            render_time = time.time() - start_time
            if render_time > 0.01:  # > 10ms
                self._render_stats['slow_renders'] += 1
                self.logger.warning(f"Slow compact device render: {render_time*1000:.1f}ms for {device.name}")
            
            return item_surface, item_rect
            
        except Exception as e:
            self.logger.error(f"Error rendering compact device item for {device.name}: {e}")
            # Return minimal fallback surface
            fallback_surface = pygame.Surface((item_width, item_height), pygame.SRCALPHA)
            fallback_surface.fill(self.colors['surface'])
            return fallback_surface, pygame.Rect(0, 0, item_width, item_height)
    
    def create_curved_device_surface(self, device: BluetoothDevice, layout_item: Dict[str, Any], 
                                   item_index: int, use_alternating_bg: bool = True) -> Tuple[Optional[pygame.Surface], pygame.Rect]:
        """Create a device item surface with curved layout optimizations"""
        if not self.display_available:
            return None, pygame.Rect(0, 0, layout_item['width'], layout_item['height'])
        
        start_time = time.time()
        self._render_stats['total_renders'] += 1
        
        try:
            # Extract layout parameters
            item_width = int(layout_item['width'])
            item_height = int(layout_item['height'])
            scale_factor = layout_item['scale']
            opacity_factor = layout_item['opacity']
            
            # Create cache key
            cache_key = f"curved_{device.mac_address}_{item_index}_{item_width}_{scale_factor:.2f}_{opacity_factor:.2f}"
            
            # Check cache first
            with self._device_cache_lock:
                if cache_key in self._device_item_cache:
                    self._render_stats['cache_hits'] += 1
                    cached_surface, cached_rect = self._device_item_cache[cache_key]
                    touch_rect = pygame.Rect(layout_item['x'] - 5, layout_item['y'], 
                                           item_width + 10, item_height)
                    return cached_surface, touch_rect
            
            self._render_stats['cache_misses'] += 1
            
            # Create scaled surface
            scaled_width = int(item_width * scale_factor)
            scaled_height = int(item_height * scale_factor)
            item_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
            
            # Apply opacity to background
            base_alpha = int(255 * opacity_factor)
            
            # Alternating background with opacity
            if use_alternating_bg and item_index % 2 == 1:
                bg_color = (25, 25, 35, base_alpha)
            else:
                bg_color = (*self.colors['surface'][:3], base_alpha)
            
            # Draw background with rounded corners
            bg_rect = pygame.Rect(0, 0, scaled_width, scaled_height - 2)
            pygame.draw.rect(item_surface, bg_color[:3], bg_rect, border_radius=int(8 * scale_factor))
            
            # Device type indicator - scaled circle
            indicator_color = self.get_device_type_color(device)
            indicator_radius = int(6 * scale_factor)
            indicator_center = (int(12 * scale_factor), scaled_height // 2)
            pygame.draw.circle(item_surface, indicator_color, indicator_center, indicator_radius)
            
            # Scale font sizes
            body_font_size = int(TypographyConstants.FONT_BODY * scale_factor)
            minimal_font_size = int(TypographyConstants.FONT_MINIMAL * scale_factor)
            signal_font_size = int(TypographyConstants.FONT_LABEL_SMALL * scale_factor)
            
            # Device name with scaled font
            try:
                name_font = get_font_manager().get_font(body_font_size)
                if not name_font:
                    name_font = pygame.font.Font(None, body_font_size)
            except Exception as e:
                self.logger.error(f"Error getting scaled font for device name: {e}")
                name_font = pygame.font.Font(None, body_font_size)
            
            # Truncate and render device name
            device_name = device.name
            max_name_width = int((item_width - 120) * scale_factor)
            device_name = self._truncate_text(device_name, name_font, max_name_width)
            
            name_surface = name_font.render(device_name, True, self.colors['text'])
            name_surface_alpha = pygame.Surface(name_surface.get_size(), pygame.SRCALPHA)
            name_surface_alpha.blit(name_surface, (0, 0))
            name_surface_alpha.set_alpha(base_alpha)
            
            item_surface.blit(name_surface_alpha, (int(24 * scale_factor), int(8 * scale_factor)))
            
            # Device type text with scaled font
            try:
                type_font = get_font_manager().get_font(minimal_font_size)
                if not type_font:
                    type_font = pygame.font.Font(None, minimal_font_size)
            except Exception as e:
                self.logger.error(f"Error getting scaled minimal font: {e}")
                type_font = pygame.font.Font(None, minimal_font_size)
            
            device_type_text = self.get_device_type_text(device)
            type_surface = type_font.render(device_type_text, True, self.colors['text_dim'])
            type_surface_alpha = pygame.Surface(type_surface.get_size(), pygame.SRCALPHA)
            type_surface_alpha.blit(type_surface, (0, 0))
            type_surface_alpha.set_alpha(int(base_alpha * 0.8))
            
            item_surface.blit(type_surface_alpha, (int(24 * scale_factor), int(26 * scale_factor)))
            
            # Signal strength indicator (scaled)
            if hasattr(device, 'rssi') and device.rssi is not None:
                signal_bars = self.get_signal_bars(device.rssi)
                signal_x = int((item_width - 35) * scale_factor)
                signal_y = int((item_height // 2 - 8) * scale_factor)
                
                for i in range(4):
                    bar_height = int((4 + i * 3) * scale_factor)
                    bar_color = self.colors['primary'] if i < signal_bars else self.colors['border']
                    bar_rect = pygame.Rect(
                        signal_x + int(i * 4 * scale_factor), 
                        signal_y + int((16 - (4 + i * 3)) * scale_factor), 
                        int(3 * scale_factor), 
                        bar_height
                    )
                    pygame.draw.rect(item_surface, bar_color, bar_rect)
                
                # Signal strength text (scaled)
                try:
                    signal_font = get_font_manager().get_font(signal_font_size)
                    if not signal_font:
                        signal_font = pygame.font.Font(None, signal_font_size)
                except Exception:
                    signal_font = pygame.font.Font(None, signal_font_size)
                
                rssi_text = f"{device.rssi}dBm"
                rssi_surface = signal_font.render(rssi_text, True, self.colors['text_dim'])
                rssi_surface_alpha = pygame.Surface(rssi_surface.get_size(), pygame.SRCALPHA)
                rssi_surface_alpha.blit(rssi_surface, (0, 0))
                rssi_surface_alpha.set_alpha(int(base_alpha * 0.7))
                
                rssi_rect = rssi_surface_alpha.get_rect()
                rssi_x = signal_x + int(16 * scale_factor) - rssi_rect.width // 2
                item_surface.blit(rssi_surface_alpha, (rssi_x, signal_y + int(18 * scale_factor)))
            
            # Cache the rendered surface
            with self._device_cache_lock:
                if len(self._device_item_cache) > 50:
                    # Remove oldest entries
                    cache_keys = list(self._device_item_cache.keys())
                    for old_key in cache_keys[:20]:
                        del self._device_item_cache[old_key]
                
                self._device_item_cache[cache_key] = (item_surface, bg_rect)
            
            # Create extended touch region
            touch_rect = pygame.Rect(layout_item['x'] - 5, layout_item['y'], item_width + 10, item_height)
            
            # Track slow renders
            render_time = time.time() - start_time
            if render_time > 0.015:  # > 15ms (higher threshold for curved rendering)
                self._render_stats['slow_renders'] += 1
                self.logger.warning(f"Slow curved device render: {render_time*1000:.1f}ms for {device.name}")
            
            return item_surface, touch_rect
            
        except Exception as e:
            self.logger.error(f"Error creating curved device surface for {device.name}: {e}")
            # Return fallback surface
            fallback_surface = pygame.Surface((layout_item['width'], layout_item['height']), pygame.SRCALPHA)
            fallback_surface.fill(self.colors['surface'])
            touch_rect = pygame.Rect(layout_item['x'], layout_item['y'], layout_item['width'], layout_item['height'])
            return fallback_surface, touch_rect
    
    def clear_device_cache(self) -> None:
        """Clear the device item rendering cache to free memory"""
        try:
            with self._device_cache_lock:
                cache_size = len(self._device_item_cache)
                self._device_item_cache.clear()
                if cache_size > 0:
                    self.logger.debug(f"Cleared device cache ({cache_size} items)")
        except Exception as e:
            self.logger.error(f"Error clearing device cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache and performance statistics"""
        try:
            with self._device_cache_lock:
                cache_size = len(self._device_item_cache)
                
                # Calculate cache hit rate
                total_requests = self._render_stats['cache_hits'] + self._render_stats['cache_misses']
                hit_rate = (self._render_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'cache_size': cache_size,
                    'render_stats': self._render_stats.copy(),
                    'cache_hit_rate': hit_rate,
                    'total_cache_requests': total_requests
                }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache by removing old entries and tracking efficiency"""
        try:
            with self._device_cache_lock:
                initial_size = len(self._device_item_cache)
                
                if initial_size > 40:
                    # Keep curved device items preferentially
                    curved_keys = [k for k in self._device_item_cache.keys() if k.startswith('curved_')]
                    compact_keys = [k for k in self._device_item_cache.keys() if k.startswith('compact_')]
                    
                    # Remove excess compact entries first
                    keys_to_remove = compact_keys[:-20] if len(compact_keys) > 20 else []
                    for key in keys_to_remove:
                        del self._device_item_cache[key]
                    
                    final_size = len(self._device_item_cache)
                    self.logger.info(f"Optimized device cache: {initial_size} -> {final_size} entries")
                    
                    return {
                        'optimized': True,
                        'initial_size': initial_size,
                        'final_size': final_size,
                        'entries_removed': initial_size - final_size
                    }
                else:
                    return {
                        'optimized': False,
                        'cache_size': initial_size,
                        'message': 'Cache within optimal size'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error optimizing cache: {e}")
            return {'error': str(e)}