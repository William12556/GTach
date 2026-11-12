#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Touch Event Coordinator.

Holds the touch regions of the current view and dispatches touches to
them for the OBDII display system.
"""

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from .interfaces import TouchAction, TouchEventInterface, TouchRegion


class TouchEventCoordinator(TouchEventInterface):
    """
    Coordinates touch events and manages interactive regions.

    Provides centralized touch event handling
    for the OBDII display system.
    """

    def __init__(self, display_bounds: Tuple[int, int] = (480, 480)):
        self.logger = logging.getLogger("TouchEventCoordinator")
        self._lock = threading.RLock()

        # Display configuration
        self.display_bounds = display_bounds
        self.display_center = (display_bounds[0] // 2, display_bounds[1] // 2)

        # Touch regions management
        self._regions: Dict[str, TouchRegion] = {}
        self._z_order: List[str] = []  # Track region layering for overlap handling

        # Configuration
        self.swipe_threshold = 50  # pixels

        # Statistics
        self._stats: Dict[str, float] = {
            "touches_processed": 0,
            "gestures_recognized": 0,
            "slider_interactions": 0,
            "last_touch_time": 0,
        }

    def register_region(self, region: TouchRegion) -> bool:
        """
        Register a touchable region.

        Args:
            region: TouchRegion instance to register

        Returns:
            bool: True if registration successful
        """
        with self._lock:
            try:
                if region.region_id in self._regions:
                    self.logger.warning(
                        f"Region {region.region_id} already registered, updating"
                    )

                self._regions[region.region_id] = region

                # Add to z-order if not present
                if region.region_id not in self._z_order:
                    self._z_order.append(region.region_id)

                self.logger.debug(f"Registered touch region: {region.region_id}")
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to register region {region.region_id}: {e}", exc_info=True
                )
                return False

    def register_button_region(
        self,
        region_id: str,
        rect: pygame.Rect,
        action_type: TouchAction = TouchAction.BUTTON_PRESS,
        callback: Optional[Callable] = None,
    ) -> bool:
        """
        Convenience method to register a button region.

        Args:
            region_id: Unique identifier for the button
            rect: Touch area rectangle
            action_type: Type of action this button performs
            callback: Optional callback function to execute

        Returns:
            bool: True if registration successful
        """
        metadata = {"type": "button", "callback": callback}

        region = TouchRegion(
            region_id=region_id, rect=rect, action_type=action_type, metadata=metadata
        )

        return self.register_region(region)

    def unregister_region(self, region_id: str) -> bool:
        """Unregister a touchable region"""
        with self._lock:
            try:
                if region_id in self._regions:
                    del self._regions[region_id]

                if region_id in self._z_order:
                    self._z_order.remove(region_id)

                self.logger.debug(f"Unregistered touch region: {region_id}")
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to unregister region {region_id}: {e}", exc_info=True
                )
                return False

    def clear_regions(self) -> None:
        """Clear all registered regions"""
        with self._lock:
            try:
                self._regions.clear()
                self._z_order.clear()
                self.logger.debug("Cleared all touch regions")

            except Exception as e:
                self.logger.error(f"Failed to clear regions: {e}", exc_info=True)

    def handle_touch_down(self, pos: Tuple[int, int]) -> Optional[TouchAction]:
        """
        Handle touch down event.

        Args:
            pos: Touch position (x, y)

        Returns:
            TouchAction or None
        """
        # A button callback is captured under the lock and invoked after
        # it is released (CLAUDE.md §4 rule 8, issue-fbe7e98a).
        result = None
        deferred = None
        deferred_region_id = None
        with self._lock:
            try:
                if not self.validate_coordinates(pos):
                    return None

                current_time = time.monotonic()

                # Find the topmost region that contains the touch point
                hit_region = self._find_hit_region(pos)

                handled = False
                if hit_region:
                    # Handle button touch down
                    if hit_region.metadata.get("type") == "button":
                        result, deferred = self._handle_button_touch_down(
                            pos, hit_region
                        )
                        deferred_region_id = hit_region.region_id
                        handled = True

                if not handled:
                    # Update statistics
                    self._stats["touches_processed"] += 1
                    self._stats["last_touch_time"] = current_time

            except Exception as e:
                self.logger.error(f"Touch down handling error: {e}", exc_info=True)
                return None

        if deferred is not None:
            try:
                deferred(pos)
            except Exception as e:
                self.logger.error(
                    f"Button callback error for {deferred_region_id}: {e}",
                    exc_info=True,
                )

        return result

    def is_button_at(self, pos: Tuple[int, int]) -> bool:
        """Whether the topmost region at pos is a button. Invokes nothing.

        Args:
            pos: Touch position (x, y).

        Returns:
            True if a registered, enabled button region contains pos.
        """
        with self._lock:
            region = self._find_hit_region(pos)
            return region is not None and region.metadata.get("type") == "button"

    def _find_hit_region(self, pos: Tuple[int, int]) -> Optional[TouchRegion]:
        """Find the topmost region that contains the touch point"""
        try:
            # Check regions in reverse z-order (topmost first)
            for region_id in reversed(self._z_order):
                if region_id in self._regions:
                    region = self._regions[region_id]
                    if region.enabled and region.rect.collidepoint(pos):
                        return region
            return None

        except Exception as e:
            self.logger.error(f"Hit region detection error: {e}", exc_info=True)
            return None

    def _handle_button_touch_down(
        self, pos: Tuple[int, int], region: TouchRegion
    ) -> Tuple[TouchAction, Optional[Callable]]:
        """Resolve a touch down on a button region.

        The callback is returned rather than invoked: handle_touch_down
        calls it after releasing the coordinator lock (issue-fbe7e98a).

        Returns:
            (action type, callback or None).
        """
        try:
            self.logger.debug(f"Button {region.region_id} pressed at {pos}")
            callback = region.metadata.get("callback")
            if not (callback and callable(callback)):
                callback = None
            return region.action_type, callback

        except Exception as e:
            self.logger.error(f"Button touch down error: {e}", exc_info=True)
            return TouchAction.NONE, None

    def get_active_regions(self) -> List[TouchRegion]:
        """Get list of currently active touch regions"""
        with self._lock:
            return [region for region in self._regions.values() if region.enabled]

    def validate_coordinates(self, pos: Tuple[int, int]) -> bool:
        """Validate touch coordinates are within display bounds"""
        try:
            x, y = pos
            return 0 <= x <= self.display_bounds[0] and 0 <= y <= self.display_bounds[1]
        except (ValueError, TypeError):
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get touch coordinator statistics"""
        with self._lock:
            return dict(self._stats)
