#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Circular positioning engine for HyperPixel 2" Round display.
Mathematical algorithms for device layout positioning with circular display
optimization.
"""

import logging
import math
import threading
import time
from typing import Any, Dict, List, Tuple


class CircularPositioningEngine:
    """Mathematical algorithms for circular display positioning with optimization"""

    def __init__(
        self,
        display_center: Tuple[int, int] = (240, 240),
        safe_radius: int = 200,
        max_radius: int = 220,
        display_size: Tuple[int, int] = (480, 480),
    ):
        self.logger = logging.getLogger("CircularPositioningEngine")

        # Circular display constants
        self.display_center = display_center
        self.display_safe_radius = safe_radius
        self.display_max_radius = max_radius
        self.display_size = display_size

        # Performance optimization caches
        self._cache_lock = threading.Lock()

        # Performance monitoring
        self._performance_monitoring = {
            "enabled": False,
            "stats": {
                "total_positioning_calls": 0,
                "total_validation_calls": 0,
                "total_positioning_time": 0.0,
                "total_validation_time": 0.0,
                "average_positioning_time": 0.0,
                "average_validation_time": 0.0,
                "slow_operations_count": 0,
            },
        }

        self.logger.info(
            f"Initialized CircularPositioningEngine with center={display_center}, "
            f"safe_radius={safe_radius}, max_radius={max_radius}"
        )

    def validate_circular_bounds(
        self, rect_coords: Tuple[int, int, int, int]
    ) -> Dict[str, Any]:
        """Validate if a rectangle fits within the circular display boundary"""
        start_time = time.monotonic()  # monotonic: duration only (issue-e215a184)

        try:
            x, y, width, height = rect_coords
            center_x, center_y = self.display_center

            rect_center_x = x + width // 2
            rect_center_y = y + height // 2
            center_distance = math.sqrt(
                (rect_center_x - center_x) ** 2 + (rect_center_y - center_y) ** 2
            )

            corners = [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]

            corner_distances = []
            for corner_x, corner_y in corners:
                distance = math.sqrt(
                    (corner_x - center_x) ** 2 + (corner_y - center_y) ** 2
                )
                corner_distances.append(distance)

            max_corner_distance = max(corner_distances)

            within_safe_area = max_corner_distance <= self.display_safe_radius
            within_max_area = max_corner_distance <= self.display_max_radius
            valid = within_safe_area

            result = {
                "valid": valid,
                "center_distance": center_distance,
                "corner_distances": corner_distances,
                "max_corner_distance": max_corner_distance,
                "within_safe_area": within_safe_area,
                "within_max_area": within_max_area,
            }

            if self._performance_monitoring["enabled"]:
                self._performance_monitoring["stats"]["total_validation_calls"] += 1
                duration = time.monotonic() - start_time
                self._performance_monitoring["stats"][
                    "total_validation_time"
                ] += duration
                self._performance_monitoring["stats"]["average_validation_time"] = (
                    self._performance_monitoring["stats"]["total_validation_time"]
                    / self._performance_monitoring["stats"]["total_validation_calls"]
                )

            return result

        except Exception as e:
            self.logger.error(f"Error validating circular bounds: {e}", exc_info=True)
            return {
                "valid": False,
                "center_distance": float("inf"),
                "corner_distances": [float("inf")],
                "max_corner_distance": float("inf"),
                "within_safe_area": False,
                "within_max_area": False,
            }

    def _calculate_curved_geometry(
        self, y_pos: int, item_height: int
    ) -> Dict[str, Any]:
        """Compute the curved x-offset, width, scale and opacity for one row.

        Extracted from calculate_curved_list_layout so that the fixed
        3-slot layout narrows and insets its rows by exactly the same
        rule (change-479b2e51). The returned dictionary carries no
        'index' or 'y' key; the caller owns those.

        Args:
            y_pos: Row top edge in display coordinates.
            item_height: Row height in pixels.

        Returns:
            Dictionary of x, width, height, scale, opacity,
            center_distance and in_safe_area.
        """
        center_x, center_y = self.display_center
        safe_radius = self.display_safe_radius
        y_distance_from_center = abs(y_pos + item_height // 2 - center_y)

        try:
            if y_distance_from_center <= safe_radius:
                horizontal_radius = math.sqrt(
                    safe_radius**2 - y_distance_from_center**2
                )

                curve_factor = 1.0 - (horizontal_radius / safe_radius)
                x_offset = int(curve_factor * 15)

                max_width_at_position = int(horizontal_radius * 2 * 0.85)
                item_width = min(400, max_width_at_position)

                x_pos = center_x - item_width // 2 + x_offset

                distance_from_center = math.sqrt(
                    (center_x - x_pos) ** 2 + y_distance_from_center**2
                )
                scale_factor = max(
                    0.95, 1.0 - (distance_from_center / safe_radius) * 0.05
                )
                opacity_factor = max(
                    0.85, 1.0 - (distance_from_center / safe_radius) * 0.15
                )

                in_safe_area = distance_from_center <= safe_radius
            else:
                x_pos = 40
                item_width = 350
                scale_factor = 0.9
                opacity_factor = 0.8
                distance_from_center = y_distance_from_center
                in_safe_area = False

        except Exception as calc_error:
            self.logger.warning(
                f"Error in curved geometry calculation at y={y_pos}: {calc_error}",
                exc_info=True,
            )
            x_pos = 40
            item_width = 350
            scale_factor = 1.0
            opacity_factor = 1.0
            distance_from_center = y_distance_from_center
            in_safe_area = False

        return {
            "x": x_pos,
            "width": item_width,
            "height": item_height,
            "scale": scale_factor,
            "opacity": opacity_factor,
            "center_distance": distance_from_center,
            "in_safe_area": in_safe_area,
        }

    def calculate_focused_slot_layout(
        self, item_height: int = 45, item_spacing: int = 10
    ) -> List[Dict[str, Any]]:
        """Calculate the three fixed DEVICE_LIST slot positions.

        Exactly three slots are always returned — top, middle and
        bottom — independent of how many devices were discovered. The
        middle slot's vertical centre is the display centre, so the
        focused device sits on the display's horizontal axis
        (change-479b2e51). Each slot is narrowed and inset by the same
        curved rule the unbounded list uses, so all three stay inside
        the circular safe area.

        Args:
            item_height: Slot height in pixels.
            item_spacing: Vertical gap between adjacent slots.

        Returns:
            Three layout entries in top-to-bottom order, each carrying
            'slot' ('top'/'middle'/'bottom'), 'index' (0..2) and the
            same geometry keys as calculate_curved_list_layout.
        """
        try:
            center_y = self.display_center[1]
            pitch = item_height + item_spacing

            # Middle slot centred on the display axis; the other two
            # one pitch either side of it.
            middle_y = center_y - item_height // 2
            slot_names = ("top", "middle", "bottom")

            layout_data = []
            for index, (name, offset) in enumerate(zip(slot_names, (-pitch, 0, pitch))):
                y_pos = middle_y + offset
                layout_item = self._calculate_curved_geometry(y_pos, item_height)
                layout_item["index"] = index
                layout_item["slot"] = name
                layout_item["y"] = y_pos
                layout_data.append(layout_item)

                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(
                        f"Slot {name}: x={layout_item['x']}, y={y_pos}, "
                        f"w={layout_item['width']}, h={item_height}, "
                        f"safe={layout_item['in_safe_area']}"
                    )

            return layout_data

        except Exception as e:
            self.logger.error(
                f"Error calculating focused slot layout: {e}", exc_info=True
            )
            center_y = self.display_center[1]
            pitch = item_height + item_spacing
            middle_y = center_y - item_height // 2
            return [
                {
                    "index": index,
                    "slot": name,
                    "x": 65,
                    "y": middle_y + offset,
                    "width": 350,
                    "height": item_height,
                    "scale": 1.0,
                    "opacity": 1.0,
                    "center_distance": abs(offset),
                    "in_safe_area": True,
                }
                for index, (name, offset) in enumerate(
                    zip(("top", "middle", "bottom"), (-pitch, 0, pitch))
                )
            ]

    def validate_all_layout_elements(
        self, layout_data: List[Dict[str, Any]], screen_name: str = "current"
    ) -> Dict[str, Any]:
        """Validate all layout elements for circular boundary compliance"""
        try:
            total_elements = len(layout_data)
            valid_elements = 0
            invalid_elements = []
            performance_stats = {}

            start_time = time.monotonic()  # monotonic: duration only (issue-e215a184)

            for item in layout_data:
                rect_coords = (item["x"], item["y"], item["width"], item["height"])
                validation_result = self.validate_circular_bounds(rect_coords)

                if validation_result["valid"]:
                    valid_elements += 1
                else:
                    invalid_elements.append(
                        {
                            "item_index": item.get("index", -1),
                            "rect_coords": rect_coords,
                            "max_corner_distance": validation_result[
                                "max_corner_distance"
                            ],
                            "safe_radius": self.display_safe_radius,
                            "excess_distance": validation_result["max_corner_distance"]
                            - self.display_safe_radius,
                        }
                    )

            total_time = time.monotonic() - start_time
            performance_stats = {
                "validation_time_ms": total_time * 1000,
                "elements_per_second": (
                    total_elements / total_time if total_time > 0 else 0
                ),
                "average_time_per_element_ms": (
                    (total_time / total_elements * 1000) if total_elements > 0 else 0
                ),
            }

            validation_summary = {
                "passed": len(invalid_elements) == 0,
                "total_elements": total_elements,
                "valid_elements": valid_elements,
                "invalid_elements_count": len(invalid_elements),
                "compliance_percentage": (
                    (valid_elements / total_elements * 100)
                    if total_elements > 0
                    else 100
                ),
            }

            result = {
                "screen_name": screen_name,
                "validation_summary": validation_summary,
                "invalid_elements": invalid_elements,
                "performance_stats": performance_stats,
                "recommendations": [],
            }

            if len(invalid_elements) > 0:
                result["recommendations"].append(
                    f"Adjust {len(invalid_elements)} elements to fit within safe area"
                )
            else:
                result["recommendations"].append(
                    "All elements comply with circular layout constraints"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error validating layout elements: {e}", exc_info=True)
            return {
                "screen_name": screen_name,
                "validation_summary": {"passed": False, "error": str(e)},
                "invalid_elements": [],
                "performance_stats": {},
                "recommendations": ["Validation failed due to error"],
            }
