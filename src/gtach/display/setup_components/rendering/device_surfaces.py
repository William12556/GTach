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

    # DEVICE_LIST slot interior, in slot-surface pixels (change-d38362aa).
    # Fixed offsets for the 60 px slot and the measured font heights:
    # name on the first line, type label on the second, four signal bars
    # on the right. NAME_RIGHT_RESERVE keeps the name clear of the bars.
    TEXT_LEFT = 24
    NAME_Y = 0
    TYPE_Y = 27
    TYPE_DOT_X = 14
    TYPE_DOT_RADIUS = 6
    NAME_RIGHT_RESERVE = 79
    BAR_COUNT = 4
    BAR_WIDTH = 5
    BAR_GAP = 3
    BAR_BASE_HEIGHT = 8
    BAR_STEP = 6
    BAR_RIGHT_INSET = 14
    BAR_BOTTOM_BELOW_CENTRE = 13

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
            # DEVICE_LIST signal bars (change-d38362aa): lit bars in the
            # text white, unlit bars in a grey visible on every slot tint.
            "signal_lit": (220, 220, 220),
            "signal_unlit": (110, 110, 125),
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
            # Extract layout parameters; scale and opacity only key the
            # cache (both are 1.0 for DEVICE_LIST, change-d38362aa).
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

            # DEVICE_LIST slots are drawn at full scale and opacity
            # (change-d38362aa), so the surface matches the slot size.
            item_surface = pygame.Surface((item_width, item_height), pygame.SRCALPHA)

            if selected:
                bg_color = self.colors["selected_surface"]
            elif use_alternating_bg and item_index % 2 == 1:
                bg_color = (25, 25, 35)
            else:
                bg_color = self.colors["surface"]

            # Draw background with rounded corners
            bg_height = item_height - 2
            bg_rect = pygame.Rect(0, 0, item_width, bg_height)
            corner_radius = 8
            pygame.draw.rect(
                item_surface, bg_color, bg_rect, border_radius=corner_radius
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

            # Device type indicator
            pygame.draw.circle(
                item_surface,
                self.get_device_type_color(device),
                (self.TYPE_DOT_X, bg_height // 2),
                self.TYPE_DOT_RADIUS,
            )

            # Device name, truncated clear of the signal bars
            name_font = get_font_manager().get_font(TypographyConstants.FONT_BODY)
            device_name = self._truncate_text(
                device.name, name_font, item_width - self.NAME_RIGHT_RESERVE
            )
            name_surface = name_font.render(device_name, True, self.colors["text"])
            item_surface.blit(name_surface, (self.TEXT_LEFT, self.NAME_Y))

            # Device type label
            type_font = get_font_manager().get_font(TypographyConstants.FONT_SMALL_TEXT)
            type_surface = type_font.render(
                self.get_device_type_text(device), True, self.colors["text_dim"]
            )
            item_surface.blit(type_surface, (self.TEXT_LEFT, self.TYPE_Y))

            # Signal strength bars, bottom-aligned, rising left to right
            if (
                hasattr(device, "signal_strength")
                and device.signal_strength is not None
            ):
                self._draw_signal_bars(
                    item_surface,
                    self.get_signal_bars(device.signal_strength),
                    item_width,
                    bg_height,
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

    def _draw_signal_bars(
        self,
        surface: pygame.Surface,
        lit_bars: int,
        item_width: int,
        bg_height: int,
    ) -> None:
        """Draw the four DEVICE_LIST signal bars at the slot's right edge.

        Args:
            surface: Slot surface to draw on.
            lit_bars: Number of bars to draw in the lit colour (0-4).
            item_width: Slot surface width in pixels.
            bg_height: Height of the slot background in pixels.
        """
        block_width = self.BAR_COUNT * self.BAR_WIDTH + (self.BAR_COUNT - 1) * (
            self.BAR_GAP
        )
        left_x = item_width - self.BAR_RIGHT_INSET - block_width
        bottom_y = bg_height // 2 + self.BAR_BOTTOM_BELOW_CENTRE

        for i in range(self.BAR_COUNT):
            bar_height = self.BAR_BASE_HEIGHT + self.BAR_STEP * i
            bar_color = (
                self.colors["signal_lit"]
                if i < lit_bars
                else self.colors["signal_unlit"]
            )
            bar_rect = pygame.Rect(
                left_x + i * (self.BAR_WIDTH + self.BAR_GAP),
                bottom_y - bar_height,
                self.BAR_WIDTH,
                bar_height,
            )
            pygame.draw.rect(surface, bar_color, bar_rect)

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
