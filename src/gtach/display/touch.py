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
    
    def __init__(self, display_manager):
        """Initialize touch handler
        
        Args:
            display_manager: Display manager instance
        """
        self.logger = logging.getLogger('TouchHandler')
        self.display_manager = display_manager
        self._touch_start: Optional[Tuple[float, int, int]] = None
        
        # Initialize touch interface using abstraction layer
        self.touch_interface = self._initialize_touch_interface()
        self._setup_touch_handler()
        
        # Start the touch interface
        if self.touch_interface:
            try:
                self.touch_interface.start()
                self.logger.info("Touch interface started successfully")
                
                # Enable simulation for mock interfaces
                if hasattr(self.touch_interface, 'enable_simulation'):
                    self.touch_interface.enable_simulation()
                    self.logger.info("Touch simulation enabled for development")
                elif hasattr(self.touch_interface, '_using_mock') and self.touch_interface._using_mock:
                    self.logger.info("Using mock HyperPixel implementation")
                    
            except Exception as e:
                self.logger.error(f"Failed to start touch interface: {e}")
                self.touch_interface = None

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
            
            if state:  # Touch start
                self._touch_start = (current_time, x, y)
                
                # Start gesture tracking if gesture handler is available
                if hasattr(self.display_manager, 'gesture_handler') and self.display_manager.gesture_handler:
                    self.display_manager.gesture_handler.start_gesture_tracking((x, y), current_time)
                    
            else:  # Touch end
                if not self._touch_start:
                    return
                    
                start_time, start_x, start_y = self._touch_start
                duration = current_time - start_time
                
                # Try gesture recognition first
                gesture_handled = False
                if hasattr(self.display_manager, 'gesture_handler') and self.display_manager.gesture_handler:
                    gesture_event = self.display_manager.gesture_handler.end_gesture_tracking((x, y), current_time)
                    
                    if gesture_event:
                        gesture_handled = self.display_manager.gesture_handler.handle_gesture_event(gesture_event)
                        self.logger.debug(f"Gesture handled: {gesture_handled}")
                
                # Fall back to traditional touch handling if gesture wasn't handled
                if not gesture_handled:
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
            if self.display_manager.config.mode != DisplayMode.SETTINGS:
                self.display_manager.change_mode(DisplayMode.SETTINGS)
            else:
                self.display_manager.change_mode(DisplayMode.DIGITAL)
                
        except Exception as e:
            self.logger.error(f"Long press handling error: {e}")

    def _handle_short_press(self, x: int, y: int, start_x: int, start_y: int) -> None:
        """Handle short press and swipe events"""
        try:
            # Check if we're in setup mode first
            if self.display_manager.is_in_setup_mode():
                self._handle_setup_touch(x, y)
                return
            
            if self.display_manager.config.mode == DisplayMode.SETTINGS:
                self._handle_settings_touch(x, y)
                return
                
            # Detect left/right swipe
            swipe_threshold = 100
            dx = x - start_x
            
            if abs(dx) >= swipe_threshold:
                if dx > 0:  # Right swipe
                    self.display_manager.change_mode(DisplayMode.GAUGE)
                else:  # Left swipe
                    self.display_manager.change_mode(DisplayMode.DIGITAL)
                    
        except Exception as e:
            self.logger.error(f"Short press handling error: {e}")

    def _handle_settings_touch(self, x: int, y: int) -> None:
        """Handle touch events in settings mode.
        
        Processes touch interactions with the settings interface elements,
        updates configuration values, and saves changes when requested.
        
        Args:
            x: Touch x-coordinate
            y: Touch y-coordinate
        """
        try:
            self.logger.debug(f"Settings touch at ({x}, {y})")
            
            # Check if settings_regions exists
            if not hasattr(self.display_manager, 'settings_regions'):
                self.logger.warning("Settings regions not defined - touch ignored")
                return
            
            # Log available regions for debugging
            self.logger.debug(f"Checking {len(self.display_manager.settings_regions)} touch regions")
            
            # Check if touch point is within any interactive region
            for i, (setting_id, region) in enumerate(self.display_manager.settings_regions):
                self.logger.debug(f"Region {i}: {setting_id} at {region}")
                if region.collidepoint(x, y):
                    self.logger.info(f"Touch hit region: {setting_id}")
                    self._process_settings_touch(setting_id)
                    return
                    
            self.logger.debug("Touch did not hit any interactive region")
                    
        except Exception as e:
            self.logger.error(f"Settings touch handling error: {e}", exc_info=True)

    def _process_settings_touch(self, setting_id: str) -> None:
        """Process a touch event for a specific settings control.
        
        Args:
            setting_id: Identifier for the touched setting control
        """
        try:
            config = self.display_manager.config
            rpm_step = 100  # Increment/decrement step for RPM values
            
            # Handle different setting controls
            if setting_id == "mode":
                # Toggle between DIGITAL and GAUGE modes
                if config.mode == DisplayMode.DIGITAL:
                    config.mode = DisplayMode.GAUGE
                else:
                    config.mode = DisplayMode.DIGITAL
            
            elif setting_id == "warn_decrease":
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
                self.display_manager.change_mode(
                    DisplayMode.DIGITAL if config.mode == DisplayMode.DIGITAL 
                    else DisplayMode.GAUGE
                )
            
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