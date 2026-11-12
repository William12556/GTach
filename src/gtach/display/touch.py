#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Touch input handling for OBDII display application.
Manages touch events and gestures using the touch interface abstraction layer.
"""

import logging
import time
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from .manager import DisplayManager
    from .touch_interface import TouchInterface

# Import touch interface abstraction
try:
    from .touch_interface import TouchEvent, TouchEventType, create_touch_interface

    TOUCH_INTERFACE_AVAILABLE = True
except ImportError:
    TOUCH_INTERFACE_AVAILABLE = False
    logging.getLogger("TouchHandler").error("Touch interface abstraction not available")

# Swipe threshold used when the coordinator is unavailable.
_DEFAULT_SWIPE_THRESHOLD = 100


def _swipe_threshold(display_manager: "DisplayManager") -> int:
    """The coordinator's swipe threshold, shared by every gesture test.

    Args:
        display_manager: The display manager owning the coordinator.

    Returns:
        Minimum movement in pixels for a swipe; _DEFAULT_SWIPE_THRESHOLD
        if the coordinator is unavailable.
    """
    coordinator = getattr(display_manager, "touch_coordinator", None)
    return int(getattr(coordinator, "swipe_threshold", _DEFAULT_SWIPE_THRESHOLD))


class TouchHandler:
    """Handles touch input and gestures using the touch interface abstraction layer"""

    # A stored touch start older than this is stale: a lost touch-up must
    # not carry its time and position into the next gesture (issue-2550e4ee).
    _TOUCH_START_MAX_AGE_S = 10.0

    def __init__(
        self,
        display_manager: "DisplayManager",
        touch_interface: Optional["TouchInterface"] = None,
    ) -> None:
        """Initialize touch handler

        Args:
            display_manager: Display manager instance
            touch_interface: Pre-initialised touch interface; if provided,
                skips self-initialisation
        """
        self.logger = logging.getLogger("TouchHandler")
        self.display_manager = display_manager
        self._touch_start: Optional[Tuple[float, int, int]] = None

        self.touch_interface: Optional["TouchInterface"]
        if touch_interface is not None:
            self.touch_interface = touch_interface
        else:
            self.touch_interface = self._initialize_touch_interface()

        self._setup_touch_handler()

    def _initialize_touch_interface(self) -> Optional["TouchInterface"]:
        """Initialize touch interface using the abstraction layer"""
        try:
            if not TOUCH_INTERFACE_AVAILABLE:
                self.logger.error("Touch interface abstraction not available")
                return None

            # Use the factory function to create appropriate interface
            interface = create_touch_interface()
            self.logger.info(f"Touch interface created: {interface.__class__.__name__}")

            # Start the interface
            interface.start()
            self.logger.info("Touch interface started successfully")

            return interface

        except Exception as e:
            self.logger.error(
                f"Failed to initialize touch interface: {e}", exc_info=True
            )
            return None

    def _setup_touch_handler(self) -> None:
        """Set up touch event handler using the abstraction layer"""
        if self.touch_interface is None:
            self.logger.warning(
                "No touch interface available - touch events will not be processed"
            )
            return

        try:
            # Register our touch event handler with the abstraction layer
            self.touch_interface.register_callback(self._handle_touch_event)
            self.logger.debug("Touch event callback registered with interface")
        except Exception as e:
            self.logger.error(f"Failed to register touch callback: {e}", exc_info=True)

    def _handle_touch_event(self, event: TouchEvent) -> None:
        """Handle TouchEvent objects from the abstraction layer"""
        try:
            # Convert normalized coordinates to pixel coordinates (480x480 display)
            x = int(event.x * 480)
            y = int(event.y * 480)

            # Ensure coordinates are within valid bounds
            x = max(0, min(479, x))
            y = max(0, min(479, y))

            # Log touch events for debugging
            self.logger.debug(
                f"Touch event: {event.event_type.name} at ({x}, {y}) - normalized "
                f"({event.x:.3f}, {event.y:.3f})"
            )

            # Convert TouchEventType to boolean state for existing logic
            if event.event_type == TouchEventType.TOUCH_DOWN:
                state = True
            elif event.event_type == TouchEventType.TOUCH_UP:
                state = False
            else:  # TOUCH_MOVE - treat as touch down for now
                state = True

            # Call existing touch handling logic
            self._process_touch(0, x, y, state, event.timestamp)

        except Exception as e:
            self.logger.error(f"Error handling touch event: {e}", exc_info=True)

    def _process_touch(
        self,
        touch_id: int,
        x: int,
        y: int,
        state: bool,
        timestamp: Optional[float] = None,
    ) -> None:
        """Track a touch and classify it on release.

        A down or move records the start when none is stored, or when the
        stored start is older than _TOUCH_START_MAX_AGE_S. On release a
        stale start is discarded without action. In setup mode every
        release goes to the short-press path. Otherwise movement at or
        above the swipe threshold is a swipe whatever the duration; a
        hold of at least touch_long_press below the threshold presses the
        button it started on, or is a long press if it started on none
        (issue-2550e4ee).

        Args:
            touch_id: Touch slot; unused.
            x: Touch x in pixels.
            y: Touch y in pixels.
            state: True for down or move, False for release.
            timestamp: time.monotonic() of the event; now when None.
        """
        try:
            current_time = timestamp if timestamp is not None else time.monotonic()

            if state:
                if (
                    self._touch_start is None
                    or current_time - self._touch_start[0] > self._TOUCH_START_MAX_AGE_S
                ):
                    self._touch_start = (current_time, x, y)
                return

            if self._touch_start is None:
                return

            start_time, start_x, start_y = self._touch_start
            self._touch_start = None
            duration = current_time - start_time
            self.logger.debug(
                f"Touch end: duration={duration:.3f}s, pos=({x},{y}), "
                f"start=({start_x},{start_y})"
            )

            if self.display_manager.is_in_setup_mode():
                self._handle_short_press(x, y, start_x, start_y)
                return

            if duration > self._TOUCH_START_MAX_AGE_S:
                self.logger.debug("Touch start stale; release ignored")
                return

            movement = max(abs(x - start_x), abs(y - start_y))
            if (
                movement >= _swipe_threshold(self.display_manager)
                or duration < self.display_manager.config.touch_long_press
            ):
                self._handle_short_press(x, y, start_x, start_y)
            elif self._starts_on_button(start_x, start_y):
                self._handle_short_press(start_x, start_y, start_x, start_y)
            else:
                self._handle_long_press(x, y)

        except Exception as e:
            self.logger.error(f"Touch processing error: {e}", exc_info=True)

    def _starts_on_button(self, x: int, y: int) -> bool:
        """Whether (x, y) lies on a registered button region.

        Args:
            x: Touch x in pixels.
            y: Touch y in pixels.

        Returns:
            True if the coordinator's hit test finds a button there.
        """
        coordinator = getattr(self.display_manager, "touch_coordinator", None)
        if coordinator is None:
            return False
        return bool(coordinator.is_button_at((x, y)))

    def _handle_long_press(self, x: int, y: int) -> None:
        """Delegate a long press to the DisplayManager.

        The DisplayManager owns the mode gating and the palette toggle.
        A long press has one position, passed as both start and end.
        """
        try:
            self.display_manager._handle_long_press((x, y), (x, y))

        except Exception as e:
            self.logger.error(f"Long press handling error: {e}", exc_info=True)

    def _handle_short_press(self, x: int, y: int, start_x: int, start_y: int) -> None:
        """Handle short press and swipe events"""
        try:
            in_setup = self.display_manager.is_in_setup_mode()
            self.logger.debug(f"Short press at ({x}, {y}), in_setup_mode={in_setup}")
            if in_setup:
                # A vertical drag on the device list moves the focus;
                # anything else is a tap (change-479b2e51).
                if self._handle_setup_swipe(x, y, start_x, start_y):
                    return
                self._handle_setup_touch(x, y)
                return

            # Vertical swipes move between the gauge and OPTIONS;
            # horizontal swipes page the options menu. Swipes are tested
            # before the region dispatch, so a swipe ending over a
            # button is not a tap on it. The entry, exit and paging
            # rules are the DisplayManager's.
            dx = x - start_x
            dy = y - start_y
            if max(abs(dx), abs(dy)) >= _swipe_threshold(self.display_manager):
                # The dominant axis wins. An exact diagonal
                # (abs(dx) == abs(dy)) falls to the vertical branch
                # deliberately: leaving OPTIONS is the more recoverable
                # outcome of the two, being one swipe from undone.
                if abs(dx) > abs(dy):
                    if dx < 0:
                        self.display_manager._handle_swipe_left(
                            (start_x, start_y), (x, y)
                        )
                    else:
                        self.display_manager._handle_swipe_right(
                            (start_x, start_y), (x, y)
                        )
                else:
                    if dy > 0:
                        self.display_manager._handle_swipe_down(
                            (start_x, start_y), (x, y)
                        )
                    else:
                        self.display_manager._handle_swipe_up(
                            (start_x, start_y), (x, y)
                        )
                return

            # The coordinator is consulted on every screen, with no mode
            # test: it holds the regions of the current view, and a
            # screen without regions is a no-op (issue-7d4e91a3).
            action = self.display_manager.handle_touch_event((x, y))
            self.logger.debug(f"Touch dispatch at ({x}, {y}) -> {action}")

        except Exception as e:
            self.logger.error(f"Short press handling error: {e}", exc_info=True)

    def _handle_setup_swipe(self, x: int, y: int, start_x: int, start_y: int) -> bool:
        """Consume a vertical swipe on the setup DEVICE_LIST screen.

        Measured before the tap dispatch with the same swipe threshold as
        the non-setup path (change-479b2e51).

        Args:
            x, y: Touch end position.
            start_x, start_y: Touch start position.

        Returns:
            True if a swipe was consumed and no tap should be
            dispatched; False to fall through to the tap dispatch.
        """
        try:
            setup_manager = getattr(self.display_manager, "_setup_manager", None)
            if setup_manager is None or not hasattr(
                setup_manager, "handle_setup_swipe"
            ):
                return False

            # Scoped to the device list: no other setup screen changes
            # behaviour.
            from .setup_models import SetupScreen

            if setup_manager.state.current_screen != SetupScreen.DEVICE_LIST:
                return False

            swipe_threshold = _swipe_threshold(self.display_manager)
            dx = x - start_x
            dy = y - start_y

            # Vertical must dominate; a horizontal drag keeps its
            # existing behaviour of falling through to the dispatch.
            if abs(dy) < swipe_threshold or abs(dy) < abs(dx):
                return False

            direction = 1 if dy > 0 else -1
            setup_manager.handle_setup_swipe(direction)
            self.logger.debug(
                f"Setup device-list swipe consumed: direction={direction:+d}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Setup swipe handling error: {e}", exc_info=True)
            return False

    def _handle_setup_touch(self, x: int, y: int) -> None:
        """Handle touch events in setup mode"""
        try:
            action = self.display_manager.handle_touch_event((x, y))

            # Handle special setup actions that affect the main application
            if action and hasattr(action, "name"):
                if action.name == "EXIT_SETUP":
                    self.display_manager.exit_setup_mode()

        except Exception as e:
            self.logger.error(f"Setup touch handling error: {e}", exc_info=True)

    def stop(self) -> None:
        """Stop touch handler and clean up touch interface"""
        try:
            if self.touch_interface is not None:
                self.touch_interface.stop()
                self.logger.info("Touch interface stopped")
            else:
                self.logger.debug("No touch interface to stop")
        except Exception as e:
            self.logger.error(f"Error stopping touch interface: {e}", exc_info=True)
