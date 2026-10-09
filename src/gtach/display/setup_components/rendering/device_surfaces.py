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
from typing import Any, Dict, Optional, Tuple

try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    # TODO: issue-ac11505d candidate defect - dead fallback, pygame required
    pygame = None  # type: ignore[assignment]  # TODO: issue-ac11505d
    PYGAME_AVAILABLE = False

from ...setup_models import BluetoothDevice, DeviceType
from ...typography import TypographyConstants, get_font_manager


class DeviceSurfaceRenderer:
    """Device representation graphics with efficient caching and resource management"""

    # DEVICE_LIST slot indicators (change-479b2e51)
    SELECTED_BORDER_WIDTH = 3
    EMPTY_SLOT_BORDER_WIDTH = 2

    def __init__(self) -> None:
        self.logger = logging.getLogger("DeviceSurfaceRenderer")

        # Check pygame availability
        if not PYGAME_AVAILABLE:
            self.logger.warning(
                "Pygame not available - device surface rendering disabled"
            )
            self.display_available = False
        else:
            self.display_available = True

        # Colors for device rendering
        self.colors = {
            "background": (20, 20, 30),
            "surface": (40, 40, 50),
            "primary": (100, 150, 250),
            "text": (220, 220, 220),
            "text_dim": (160, 160, 160),
            "border": (60, 60, 70),
            "elm327_likely": (50, 200, 50),
            "possibly_compatible": (255, 165, 0),
            "unknown_device": (150, 150, 150),
            # DEVICE_LIST focused-slot indicators (change-479b2e51).
            # The focused slot is the only selectable one, so it is
            # tinted lighter than the unselected slots and outlined in
            # the accent colour.
            "selected_surface": (70, 70, 95),
            "selected_border": (100, 150, 250),
            "empty_slot_border": (110, 110, 125),
        }

        # Device surface cache with thread safety
        self._device_item_cache: Dict[str, Tuple[pygame.Surface, pygame.Rect]] = {}
        self._device_cache_lock = threading.Lock()

        # Performance tracking
        self._render_stats = {
            "total_renders": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "slow_renders": 0,
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
        if hasattr(device, "device_classification"):
            if device.device_classification == DeviceType.HIGHLY_LIKELY_ELM327:
                return self.colors["elm327_likely"]
            elif device.device_classification == DeviceType.POSSIBLY_COMPATIBLE:
                return self.colors["possibly_compatible"]
            else:
                return self.colors["unknown_device"]
        else:
            return (
                self.colors["elm327_likely"]
                if device.device_type == "ELM327"
                else self.colors["unknown_device"]
            )

    def get_device_type_text(self, device: BluetoothDevice) -> str:
        """Get text description for device type"""
        if hasattr(device, "device_classification"):
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
            self.logger.error(f"Error truncating text: {e}", exc_info=True)
            return text[:20]  # Fallback truncation

    def create_curved_device_surface(
        self,
        device: BluetoothDevice,
        layout_item: Dict[str, Any],
        item_index: int,
        use_alternating_bg: bool = True,
        selected: bool = False,
    ) -> Tuple[Optional[pygame.Surface], pygame.Rect]:
        """Create a device item surface with curved layout optimizations.

        Args:
            device: Device to draw.
            layout_item: Slot geometry from CircularPositioningEngine.
            item_index: Index used for the alternating background and
                the cache key.
            use_alternating_bg: Darken every second row.
            selected: Draw the focused-slot indicator — a lighter
                background tint plus an accent border marking this as
                the only selectable slot (change-479b2e51).

        Returns:
            Tuple of the rendered surface and its touch rect.
        """
        if not self.display_available:
            return None, pygame.Rect(0, 0, layout_item["width"], layout_item["height"])

        start_time = time.monotonic()  # monotonic: duration only (issue-e215a184)
        self._render_stats["total_renders"] += 1

        try:
            # Extract layout parameters
            item_width = int(layout_item["width"])
            item_height = int(layout_item["height"])
            scale_factor = layout_item["scale"]
            opacity_factor = layout_item["opacity"]

            # Create cache key
            cache_key = (
                f"curved_{device.mac_address}_{item_index}_{item_width}_"
                f"{scale_factor:.2f}_{opacity_factor:.2f}_{selected}"
            )

            # Check cache first
            with self._device_cache_lock:
                if cache_key in self._device_item_cache:
                    self._render_stats["cache_hits"] += 1
                    cached_surface, cached_rect = self._device_item_cache[cache_key]
                    touch_rect = pygame.Rect(
                        layout_item["x"] - 5,
                        layout_item["y"],
                        item_width + 10,
                        item_height,
                    )
                    return cached_surface, touch_rect

            self._render_stats["cache_misses"] += 1

            # Create scaled surface
            scaled_width = int(item_width * scale_factor)
            scaled_height = int(item_height * scale_factor)
            item_surface = pygame.Surface(
                (scaled_width, scaled_height), pygame.SRCALPHA
            )

            # Apply opacity to background
            base_alpha = int(255 * opacity_factor)

            # Alternating background with opacity
            if selected:
                bg_color = (*self.colors["selected_surface"], base_alpha)
            elif use_alternating_bg and item_index % 2 == 1:
                bg_color = (25, 25, 35, base_alpha)
            else:
                bg_color = (*self.colors["surface"][:3], base_alpha)

            # Draw background with rounded corners
            bg_rect = pygame.Rect(0, 0, scaled_width, scaled_height - 2)
            corner_radius = int(8 * scale_factor)
            pygame.draw.rect(
                item_surface, bg_color[:3], bg_rect, border_radius=corner_radius
            )

            # Focused-slot border, drawn before the content so no glyph
            # is clipped by it.
            if selected:
                pygame.draw.rect(
                    item_surface,
                    self.colors["selected_border"],
                    bg_rect,
                    self.SELECTED_BORDER_WIDTH,
                    border_radius=corner_radius,
                )

            # Device type indicator - scaled circle
            indicator_color = self.get_device_type_color(device)
            indicator_radius = int(6 * scale_factor)
            indicator_center = (int(12 * scale_factor), scaled_height // 2)
            pygame.draw.circle(
                item_surface, indicator_color, indicator_center, indicator_radius
            )

            # Scale font sizes
            body_font_size = int(TypographyConstants.FONT_BODY * scale_factor)
            small_text_font_size = int(
                TypographyConstants.FONT_SMALL_TEXT * scale_factor
            )

            # Device name with scaled font
            name_font = get_font_manager().get_font(body_font_size)

            # Truncate and render device name
            device_name = device.name
            max_name_width = int((item_width - 120) * scale_factor)
            device_name = self._truncate_text(device_name, name_font, max_name_width)

            name_surface = name_font.render(device_name, True, self.colors["text"])
            name_surface_alpha = pygame.Surface(
                name_surface.get_size(), pygame.SRCALPHA
            )
            name_surface_alpha.blit(name_surface, (0, 0))
            name_surface_alpha.set_alpha(base_alpha)

            item_surface.blit(
                name_surface_alpha, (int(24 * scale_factor), int(8 * scale_factor))
            )

            # Device type text with scaled font
            type_font = get_font_manager().get_font(small_text_font_size)

            device_type_text = self.get_device_type_text(device)
            type_surface = type_font.render(
                device_type_text, True, self.colors["text_dim"]
            )
            type_surface_alpha = pygame.Surface(
                type_surface.get_size(), pygame.SRCALPHA
            )
            type_surface_alpha.blit(type_surface, (0, 0))
            type_surface_alpha.set_alpha(int(base_alpha * 0.8))

            item_surface.blit(
                type_surface_alpha, (int(24 * scale_factor), int(26 * scale_factor))
            )

            # Signal strength indicator (scaled)
            if (
                hasattr(device, "signal_strength")
                and device.signal_strength is not None
            ):
                signal_bars = self.get_signal_bars(device.signal_strength)
                signal_x = int((item_width - 35) * scale_factor)
                signal_y = int((item_height // 2 - 8) * scale_factor)

                for i in range(4):
                    bar_height = int((4 + i * 3) * scale_factor)
                    bar_color = (
                        self.colors["primary"]
                        if i < signal_bars
                        else self.colors["border"]
                    )
                    bar_rect = pygame.Rect(
                        signal_x + int(i * 4 * scale_factor),
                        signal_y + int((16 - (4 + i * 3)) * scale_factor),
                        int(3 * scale_factor),
                        bar_height,
                    )
                    pygame.draw.rect(item_surface, bar_color, bar_rect)

                # Signal strength text (scaled)
                signal_font = get_font_manager().get_font(small_text_font_size)

                rssi_text = f"{device.signal_strength}dBm"
                rssi_surface = signal_font.render(
                    rssi_text, True, self.colors["text_dim"]
                )
                rssi_surface_alpha = pygame.Surface(
                    rssi_surface.get_size(), pygame.SRCALPHA
                )
                rssi_surface_alpha.blit(rssi_surface, (0, 0))
                rssi_surface_alpha.set_alpha(int(base_alpha * 0.7))

                rssi_rect = rssi_surface_alpha.get_rect()
                rssi_x = signal_x + int(16 * scale_factor) - rssi_rect.width // 2
                item_surface.blit(
                    rssi_surface_alpha, (rssi_x, signal_y + int(18 * scale_factor))
                )

            # Cache the rendered surface
            with self._device_cache_lock:
                if len(self._device_item_cache) > 50:
                    # Remove oldest entries
                    cache_keys = list(self._device_item_cache.keys())
                    for old_key in cache_keys[:20]:
                        del self._device_item_cache[old_key]

                self._device_item_cache[cache_key] = (item_surface, bg_rect)

            # Create extended touch region
            touch_rect = pygame.Rect(
                layout_item["x"] - 5, layout_item["y"], item_width + 10, item_height
            )

            # Track slow renders
            render_time = time.monotonic() - start_time
            if render_time > 0.015:  # > 15ms (higher threshold for curved rendering)
                self._render_stats["slow_renders"] += 1
                self.logger.warning(
                    f"Slow curved device render: {render_time * 1000:.1f}ms for "
                    f"{device.name}"
                )

            return item_surface, touch_rect

        except Exception as e:
            self.logger.error(
                f"Error creating curved device surface for {device.name}: {e}",
                exc_info=True,
            )
            # Return fallback surface
            fallback_surface = pygame.Surface(
                (layout_item["width"], layout_item["height"]), pygame.SRCALPHA
            )
            fallback_surface.fill(self.colors["surface"])
            touch_rect = pygame.Rect(
                layout_item["x"],
                layout_item["y"],
                layout_item["width"],
                layout_item["height"],
            )
            return fallback_surface, touch_rect

    def create_empty_slot_surface(
        self, layout_item: Dict[str, Any], selected: bool = False
    ) -> Tuple[Optional[pygame.Surface], pygame.Rect]:
        """Create an outlined empty frame occupying a slot's footprint.

        Drawn when the focused index has no neighbour on that side, so
        the three-slot geometry holds regardless of how many devices
        were discovered (change-479b2e51).

        Args:
            layout_item: Slot geometry from CircularPositioningEngine.
            selected: Draw the focused-slot indicator. The middle slot
                keeps its border and tint even with no device in it.

        Returns:
            Tuple of the rendered surface and its rect on the display.
        """
        item_width = int(layout_item["width"])
        item_height = int(layout_item["height"])
        slot_rect = pygame.Rect(
            layout_item["x"], layout_item["y"], item_width, item_height
        )

        if not self.display_available:
            return None, slot_rect

        try:
            scale_factor = layout_item.get("scale", 1.0)
            scaled_width = int(item_width * scale_factor)
            scaled_height = int(item_height * scale_factor)

            item_surface = pygame.Surface(
                (scaled_width, scaled_height), pygame.SRCALPHA
            )
            frame_rect = pygame.Rect(0, 0, scaled_width, scaled_height - 2)
            corner_radius = int(8 * scale_factor)

            if selected:
                pygame.draw.rect(
                    item_surface,
                    self.colors["selected_surface"],
                    frame_rect,
                    border_radius=corner_radius,
                )
                pygame.draw.rect(
                    item_surface,
                    self.colors["selected_border"],
                    frame_rect,
                    self.SELECTED_BORDER_WIDTH,
                    border_radius=corner_radius,
                )
            else:
                pygame.draw.rect(
                    item_surface,
                    self.colors["empty_slot_border"],
                    frame_rect,
                    self.EMPTY_SLOT_BORDER_WIDTH,
                    border_radius=corner_radius,
                )

            return item_surface, slot_rect

        except Exception as e:
            self.logger.error(f"Error creating empty slot surface: {e}", exc_info=True)
            fallback_surface = pygame.Surface(
                (item_width, item_height), pygame.SRCALPHA
            )
            return fallback_surface, slot_rect

    def create_slot_surface(
        self,
        device: Optional[BluetoothDevice],
        layout_item: Dict[str, Any],
        selected: bool = False,
    ) -> Tuple[Optional[pygame.Surface], Optional[pygame.Rect]]:
        """Create one DEVICE_LIST slot: a device, or an empty frame.

        The single entry point the DEVICE_LIST render uses for all
        three slots (change-479b2e51). A touch rect is returned only
        for the focused slot when it holds a device, so an unselectable
        slot cannot be registered as a touch region by accident.

        Args:
            device: Device for this slot, or None for an empty frame.
            layout_item: Slot geometry from CircularPositioningEngine.
            selected: True for the middle (focused) slot only.

        Returns:
            Tuple of the rendered surface and its touch rect, the rect
            being None for every slot that is not selectable.
        """
        try:
            if device is None:
                slot_surface, _rect = self.create_empty_slot_surface(
                    layout_item, selected=selected
                )
                return slot_surface, None

            slot_surface, touch_rect = self.create_curved_device_surface(
                device,
                layout_item,
                layout_item.get("index", 0),
                use_alternating_bg=False,
                selected=selected,
            )

            return slot_surface, touch_rect if selected else None

        except Exception as e:
            self.logger.error(f"Error creating slot surface: {e}", exc_info=True)
            return None, None

    def clear_device_cache(self) -> None:
        """Clear the device item rendering cache to free memory"""
        try:
            with self._device_cache_lock:
                cache_size = len(self._device_item_cache)
                self._device_item_cache.clear()
                if cache_size > 0:
                    self.logger.debug(f"Cleared device cache ({cache_size} items)")
        except Exception as e:
            self.logger.error(f"Error clearing device cache: {e}", exc_info=True)
