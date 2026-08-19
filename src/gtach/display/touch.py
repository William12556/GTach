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
from typing import Optional, Tuple

# Import touch interface abstraction
try:
    from .touch_interface import create_touch_interface, TouchEvent, TouchEventType
    TOUCH_INTERFACE_AVAILABLE = True
except ImportError:
    TOUCH_INTERFACE_AVAILABLE = False
    logging.getLogger('TouchHandler').error("Touch interface abstraction not available")

from .models import DisplayMode

class TouchHandler:
    """Handles touch input and gestures using the touch interface abstraction layer"""
    
    def __init__(self, display_manager, touch_interface=None):
        """Initialize touch handler

        Args:
            display_manager: Display manager instance
            touch_interface: Pre-initialised touch interface; if provided, skips self-initialisation
        """
        self.logger = logging.getLogger('TouchHandler')
        self.display_manager = display_manager
        self._touch_start: Optional[Tuple[float, int, int]] = None

        if touch_interface is not None:
            self.touch_interface = touch_interface
        else:
            self.touch_interface = self._initialize_touch_interface()

        self._setup_touch_handler()

    def _initialize_touch_interface(self):
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
            self.logger.error(f"Failed to initialize touch interface: {e}")
            return None

    def _setup_touch_handler(self) -> None:
        """Set up touch event handler using the abstraction layer"""
        if self.touch_interface is None:
            self.logger.warning("No touch interface available - touch events will not be processed")
            return
        
        try:
            # Register our touch event handler with the abstraction layer
            self.touch_interface.register_callback(self._handle_touch_event)
            self.logger.debug("Touch event callback registered with interface")
        except Exception as e:
            self.logger.error(f"Failed to register touch callback: {e}")

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
            self.logger.debug(f"Touch event: {event.event_type.name} at ({x}, {y}) - normalized ({event.x:.3f}, {event.y:.3f})")
            
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
            self.logger.error(f"Error handling touch event: {e}")

    def _process_touch(self, touch_id: int, x: int, y: int, state: bool, timestamp: float = None) -> None:
        """Process touch events with gesture recognition integration"""
        try:
            current_time = timestamp if timestamp else time.time()
            
            if state:  # Touch down/move
                if self._touch_start is None:  # Only record on first touch down
                    self._touch_start = (current_time, x, y)
                    
            else:  # Touch end
                if not self._touch_start:
                    return
                    
                start_time, start_x, start_y = self._touch_start
                duration = current_time - start_time
                self.logger.debug(f"Touch end: duration={duration:.3f}s, pos=({x},{y}), start=({start_x},{start_y})")

                # Skip gesture handler in setup mode - route directly
                if self.display_manager.is_in_setup_mode():
                    self._touch_start = None
                    self._handle_short_press(x, y, start_x, start_y)
                    return

                # Always reset gesture handler state, then use direct swipe logic
                if hasattr(self.display_manager, 'gesture_handler') and self.display_manager.gesture_handler:
                    try:
                        self.display_manager.gesture_handler.cancel_gesture()
                    except Exception:
                        pass

                # Direct swipe/press handling - no gesture handler intermediary
                if duration >= self.display_manager.config.touch_long_press:
                    self._handle_long_press(x, y)
                else:
                    self._handle_short_press(x, y, start_x, start_y)

                self._touch_start = None
                
        except Exception as e:
            self.logger.error(f"Touch processing error: {e}")

    def _handle_long_press(self, x: int, y: int) -> None:
        """Handle long press events"""
        try:
            # OPTIONS is reached by swiping, not by long press
            # (change-3e8b1d72). A long press now delegates on every
            # screen, DISCONNECTED included, where it toggles the
            # day/night palette as it does elsewhere (issue-7d4e91a3,
            # change-2b6f4d91). The branch removed from here claimed to
            # enter SETUP but only logged saying so; Setup is reached by
            # tapping the DISCONNECTED screen's button, which the same
            # issue made reachable.
            #
            # Delegate to the DisplayManager, which owns the mode
            # gating and the palette state. Called directly rather
            # than through the touch coordinator, whose gesture
            # callbacks are never dispatched (issue-2b6f4d91) —
            # the same route change-3e8b1d72 used for the vertical
            # swipes. A long press has one position, so it is
            # passed as both start and end.
            self.display_manager._handle_long_press((x, y), (x, y))

        except Exception as e:
            self.logger.error(f"Long press handling error: {e}")

    def _handle_short_press(self, x: int, y: int, start_x: int, start_y: int) -> None:
        """Handle short press and swipe events"""
        try:
            in_setup = self.display_manager.is_in_setup_mode()
            self.logger.debug(f"Short press at ({x}, {y}), in_setup_mode={in_setup}")
            if in_setup:
                # A vertical drag on the device list moves the focus
                # rather than selecting whatever it ended over
                # (change-479b2e51). Every other setup screen, and
                # every movement below the threshold, falls through to
                # the tap dispatch unchanged.
                if self._handle_setup_swipe(x, y, start_x, start_y):
                    return
                self._handle_setup_touch(x, y)
                return

            # Vertical swipes move between the gauge and OPTIONS
            # (change-3e8b1d72); horizontal swipes page within the
            # options menu (change-8c5a1e73). Both are tested before
            # the region dispatch below, and must stay that way: a
            # swipe that ends over a registered region would otherwise
            # be consumed as a tap on it, and the dispatch returns
            # nothing to distinguish the two.
            #
            # The entry, exit and paging rules are the DisplayManager's;
            # this path delegates rather than duplicating them, so the
            # two live handler paths agree by construction.
            #
            # The coordinator's own threshold, so the two paths accept
            # the same movement; 100 — the value the removed horizontal
            # branch used — if the coordinator is unavailable.
            swipe_threshold = getattr(
                getattr(self.display_manager, 'touch_coordinator', None),
                'swipe_threshold', 100
            )
            dx = x - start_x
            dy = y - start_y
            if max(abs(dx), abs(dy)) >= swipe_threshold:
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

            # The coordinator is consulted on EVERY screen, with no mode
            # test. This handler must not enumerate screens: the
            # coordinator already knows which regions exist, because
            # DisplayManager._register_touch_regions rebuilds that set
            # on every render pass (manager.py:1454). Screens with no
            # regions are therefore a no-op by construction — it
            # returns early for SPLASH (manager.py:1456) and registers
            # nothing for connected RADIAL (manager.py:1484).
            #
            # Gating this on DisplayMode.OPTIONS left the DISCONNECTED
            # screen's Setup and Simulate buttons and the
            # ACKNOWLEDGEMENT screen's dismiss region registered,
            # drawn, and never hit-tested (issue-7d4e91a3).
            action = self.display_manager.handle_touch_event((x, y))
            self.logger.debug(f"Touch dispatch at ({x}, {y}) -> {action}")

        except Exception as e:
            self.logger.error(f"Short press handling error: {e}", exc_info=True)

    def _process_settings_touch(self, setting_id: str) -> None:
        """Process a touch event for a specific settings control.
        
        Args:
            setting_id: Identifier for the touched setting control
        """
        try:
            config = self.display_manager.config
            rpm_step = 100  # Increment/decrement step for RPM values
            
            # Handle different setting controls
            if setting_id == "warn_decrease":
                # Decrease warning RPM (with minimum bound)
                new_value = max(config.rpm_warning - rpm_step, 3000)
                # Ensure warning threshold stays below danger threshold
                if new_value < config.rpm_danger:
                    config.rpm_warning = new_value
            
            elif setting_id == "warn_increase":
                # Increase warning RPM
                new_value = min(config.rpm_warning + rpm_step, config.rpm_danger - rpm_step)
                config.rpm_warning = new_value
            
            elif setting_id == "danger_decrease":
                # Decrease danger RPM (with minimum bound)
                new_value = max(config.rpm_danger - rpm_step, config.rpm_warning + rpm_step)
                config.rpm_danger = new_value
            
            elif setting_id == "danger_increase":
                # Increase danger RPM (with maximum bound)
                new_value = min(config.rpm_danger + rpm_step, 9000)
                config.rpm_danger = new_value
            
            elif setting_id == "save":
                # Save settings and exit settings mode
                self.display_manager._save_config()
                # One normal mode remains (change-378703da), so the
                # ternary that chose between them collapses.
                self.display_manager.change_mode(DisplayMode.RADIAL)
            
            # Add visual feedback for touch interaction
            self._provide_touch_feedback()
            
        except Exception as e:
            self.logger.error(f"Settings processing error: {e}", exc_info=True)

    def _provide_touch_feedback(self) -> None:
        """Provide visual feedback for touch interactions.
        
        Can be expanded with haptic or sound feedback in future versions.
        """
        try:
            # For now, we'll just log the interaction
            self.logger.debug("Touch interaction detected")
            
            # In a future version, we could add a brief flash or sound
            # to provide immediate user feedback
            
        except Exception as e:
            self.logger.error(f"Touch feedback error: {e}")
    
    def _handle_setup_swipe(self, x: int, y: int, start_x: int, start_y: int) -> bool:
        """Consume a vertical swipe on the setup DEVICE_LIST screen.

        Setup mode skips the gesture handler entirely (_process_touch),
        so the drag distance is measured here, before the tap dispatch,
        exactly as the non-setup path does in this method's caller. The
        same swipe_threshold is used so both paths accept the same
        movement (change-479b2e51).

        Args:
            x, y: Touch end position.
            start_x, start_y: Touch start position.

        Returns:
            True if a swipe was consumed and no tap should be
            dispatched; False to fall through to the tap dispatch.
        """
        try:
            setup_manager = getattr(self.display_manager, '_setup_manager', None)
            if setup_manager is None or not hasattr(setup_manager, 'handle_setup_swipe'):
                return False

            # Scoped to the device list: no other setup screen changes
            # behaviour.
            from .setup_models import SetupScreen
            if setup_manager.state.current_screen != SetupScreen.DEVICE_LIST:
                return False

            swipe_threshold = getattr(
                getattr(self.display_manager, 'touch_coordinator', None),
                'swipe_threshold', 100
            )
            dx = x - start_x
            dy = y - start_y

            # Vertical must dominate; a horizontal drag keeps its
            # existing behaviour of falling through to the dispatch.
            if abs(dy) < swipe_threshold or abs(dy) < abs(dx):
                return False

            direction = 1 if dy > 0 else -1
            setup_manager.handle_setup_swipe(direction)
            self.logger.debug(f"Setup device-list swipe consumed: direction={direction:+d}")
            return True

        except Exception as e:
            self.logger.error(f"Setup swipe handling error: {e}", exc_info=True)
            return False

    def _handle_setup_touch(self, x: int, y: int) -> None:
        """Handle touch events in setup mode"""
        try:
            # Route touch events through the DisplayManager's new handle_touch_event method
            action = self.display_manager.handle_touch_event((x, y))
            
            # Handle special setup actions that affect the main application
            if action and hasattr(action, 'name'):
                if action.name == 'EXIT_SETUP':
                    self.display_manager.exit_setup_mode()
                    
        except Exception as e:
            self.logger.error(f"Setup touch handling error: {e}")

    def stop(self) -> None:
        """Stop touch handler and clean up touch interface"""
        try:
            if self.touch_interface is not None:
                self.touch_interface.stop()
                self.logger.info("Touch interface stopped")
            else:
                self.logger.debug("No touch interface to stop")
        except Exception as e:
            self.logger.error(f"Error stopping touch interface: {e}")

    def get_touch_interface_info(self) -> dict:
        """Get information about the current touch interface for debugging"""
        try:
            info = {
                'touch_interface_available': TOUCH_INTERFACE_AVAILABLE,
                'interface_type': type(self.touch_interface).__name__ if self.touch_interface else 'None'
            }
            
            if self.touch_interface is not None:
                try:
                    interface_info = self.touch_interface.get_info()
                    info['interface_info'] = interface_info
                except AttributeError:
                    info['interface_info'] = 'get_info() not available'
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting touch interface info: {e}")
            return {'error': str(e)}

    def test_touch_simulation(self) -> None:
        """Test touch simulation functionality for development"""
        try:
            if not self.touch_interface:
                self.logger.error("No touch interface available for testing")
                return
            
            self.logger.info("Starting touch simulation test...")
            
            # Test different simulation methods
            if hasattr(self.touch_interface, 'simulate_touch_event'):
                # HyperPixel interface simulation
                self.logger.info("Testing HyperPixel touch simulation")
                self.touch_interface.simulate_touch_event(0.5, 0.5, True)  # Touch down at center
                time.sleep(0.1)
                self.touch_interface.simulate_touch_event(0.5, 0.5, False)  # Touch up
                
            elif hasattr(self.touch_interface, 'simulate_tap'):
                # Mock interface simulation
                self.logger.info("Testing mock interface tap simulation")
                self.touch_interface.simulate_tap(0.5, 0.5)
                
            else:
                self.logger.warning("Touch interface does not support simulation")
                
            self.logger.info("Touch simulation test completed")
            
        except Exception as e:
            self.logger.error(f"Touch simulation test failed: {e}")

    def simulate_settings_button_press(self, button_name: str) -> None:
        """Simulate pressing a specific settings button for testing"""
        try:
            if not self.touch_interface:
                self.logger.error("No touch interface available")
                return
            
            # Define approximate button positions (normalized coordinates)
            button_positions = {
                'mode': (0.7, 0.25),           # Mode toggle button
                'warn_decrease': (0.54, 0.375), # Warning RPM decrease
                'warn_increase': (0.9, 0.375),  # Warning RPM increase  
                'danger_decrease': (0.54, 0.5), # Danger RPM decrease
                'danger_increase': (0.9, 0.5),  # Danger RPM increase
                'save': (0.67, 0.71),          # Save button
                'center': (0.5, 0.5)           # Center for general testing
            }
            
            if button_name not in button_positions:
                self.logger.error(f"Unknown button: {button_name}. Available: {list(button_positions.keys())}")
                return
                
            x, y = button_positions[button_name]
            self.logger.info(f"Simulating touch on {button_name} button at ({x:.2f}, {y:.2f})")
            
            # Simulate tap
            if hasattr(self.touch_interface, 'simulate_touch_event'):
                self.touch_interface.simulate_touch_event(x, y, True)
                time.sleep(0.1)
                self.touch_interface.simulate_touch_event(x, y, False)
            elif hasattr(self.touch_interface, 'simulate_tap'):
                self.touch_interface.simulate_tap(x, y)
            else:
                self.logger.warning("Touch simulation not supported")
                
        except Exception as e:
            self.logger.error(f"Settings button simulation failed: {e}")