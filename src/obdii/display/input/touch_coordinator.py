#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Touch Event Coordinator - Extracted from monolithic DisplayManager.

Handles touch event processing, gesture recognition, and interaction
with UI components for the OBDII display system.
"""

import logging
import time
import threading
from typing import Tuple, Optional, Dict, Any, List, Callable
import pygame

from .interfaces import TouchEventInterface, TouchRegion, TouchAction, GestureType

class TouchEventCoordinator(TouchEventInterface):
    """
    Coordinates touch events and manages interactive regions.
    
    Provides centralized touch event handling, gesture recognition,
    and slider interaction support for the OBDII display system.
    """
    
    def __init__(self, display_bounds: Tuple[int, int] = (480, 480)):
        self.logger = logging.getLogger('TouchEventCoordinator')
        self._lock = threading.RLock()
        
        # Display configuration
        self.display_bounds = display_bounds
        self.display_center = (display_bounds[0] // 2, display_bounds[1] // 2)
        
        # Touch regions management
        self._regions: Dict[str, TouchRegion] = {}
        self._z_order = []  # Track region layering for overlap handling
        
        # Touch state tracking
        self._touch_state = {
            'active': False,
            'start_pos': None,
            'current_pos': None,
            'start_time': None,
            'active_region': None,
            'gesture_recognized': False
        }
        
        # Slider interaction state
        self._slider_state = {
            'active': False,
            'region_id': None,
            'initial_pos': None,
            'initial_value': None,
            'track_bounds': None
        }
        
        # Configuration
        self.long_press_duration = 1.0  # seconds
        self.drag_threshold = 10  # pixels
        self.swipe_threshold = 50  # pixels
        self.tap_timeout = 0.5  # seconds
        
        # Gesture callbacks
        self._gesture_callbacks: Dict[GestureType, Callable] = {}
        
        # Statistics
        self._stats = {
            'touches_processed': 0,
            'gestures_recognized': 0,
            'slider_interactions': 0,
            'last_touch_time': 0
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
                    self.logger.warning(f"Region {region.region_id} already registered, updating")
                
                self._regions[region.region_id] = region
                
                # Add to z-order if not present
                if region.region_id not in self._z_order:
                    self._z_order.append(region.region_id)
                
                self.logger.debug(f"Registered touch region: {region.region_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to register region {region.region_id}: {e}")
                return False
    
    def register_slider_region(self, region_id: str, rect: pygame.Rect, 
                             track_start_x: int, track_width: int,
                             min_val: int, max_val: int, current_val: int) -> bool:
        """
        Convenience method to register a slider region.
        
        Args:
            region_id: Unique identifier for the slider
            rect: Touch area rectangle
            track_start_x: X position where slider track starts
            track_width: Width of slider track
            min_val: Minimum slider value
            max_val: Maximum slider value
            current_val: Current slider value
            
        Returns:
            bool: True if registration successful
        """
        metadata = {
            'type': 'slider',
            'track_start_x': track_start_x,
            'track_width': track_width,
            'min_val': min_val,
            'max_val': max_val,
            'current_value': current_val
        }
        
        region = TouchRegion(
            region_id=region_id,
            rect=rect,
            action_type=TouchAction.SLIDER_INTERACTION,
            metadata=metadata
        )
        
        return self.register_region(region)
    
    def register_button_region(self, region_id: str, rect: pygame.Rect,
                             action_type: TouchAction = TouchAction.BUTTON_PRESS,
                             callback: Optional[Callable] = None) -> bool:
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
        metadata = {
            'type': 'button',
            'callback': callback
        }
        
        region = TouchRegion(
            region_id=region_id,
            rect=rect,
            action_type=action_type,
            metadata=metadata
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
                self.logger.error(f"Failed to unregister region {region_id}: {e}")
                return False
    
    def clear_regions(self) -> None:
        """Clear all registered regions"""
        with self._lock:
            try:
                self._regions.clear()
                self._z_order.clear()
                self.logger.debug("Cleared all touch regions")
                
            except Exception as e:
                self.logger.error(f"Failed to clear regions: {e}")
    
    def handle_touch_down(self, pos: Tuple[int, int]) -> Optional[TouchAction]:
        """
        Handle touch down event.
        
        Args:
            pos: Touch position (x, y)
            
        Returns:
            TouchAction or None
        """
        with self._lock:
            try:
                if not self.validate_coordinates(pos):
                    return None
                
                current_time = time.time()
                
                # Update touch state
                self._touch_state = {
                    'active': True,
                    'start_pos': pos,
                    'current_pos': pos,
                    'start_time': current_time,
                    'active_region': None,
                    'gesture_recognized': False
                }
                
                # Find the topmost region that contains the touch point
                hit_region = self._find_hit_region(pos)
                
                if hit_region:
                    self._touch_state['active_region'] = hit_region.region_id
                    
                    # Handle slider touch down
                    if hit_region.metadata.get('type') == 'slider':
                        return self._handle_slider_touch_down(pos, hit_region)
                    
                    # Handle button touch down
                    elif hit_region.metadata.get('type') == 'button':
                        return self._handle_button_touch_down(pos, hit_region)
                
                # Update statistics
                self._stats['touches_processed'] += 1
                self._stats['last_touch_time'] = current_time
                
                return None
                
            except Exception as e:
                self.logger.error(f"Touch down handling error: {e}")
                return None
    
    def handle_touch_move(self, pos: Tuple[int, int]) -> Optional[TouchAction]:
        """Handle touch move/drag event"""
        with self._lock:
            try:
                if not self._touch_state['active'] or not self.validate_coordinates(pos):
                    return None
                
                self._touch_state['current_pos'] = pos
                
                # Handle active slider drag
                if self._slider_state['active']:
                    return self._handle_slider_drag(pos)
                
                # Check for gesture recognition
                if not self._touch_state['gesture_recognized']:
                    gesture = self._recognize_gesture()
                    if gesture:
                        self._touch_state['gesture_recognized'] = True
                        return self.handle_gesture(gesture, 
                                                 self._touch_state['start_pos'], pos)
                
                return TouchAction.DRAG if self._is_drag_gesture() else None
                
            except Exception as e:
                self.logger.error(f"Touch move handling error: {e}")
                return None
    
    def handle_touch_up(self, pos: Tuple[int, int]) -> Optional[TouchAction]:
        """Handle touch up/release event"""
        with self._lock:
            try:
                if not self._touch_state['active']:
                    return None
                
                current_time = time.time()
                touch_duration = current_time - self._touch_state['start_time']
                
                # End slider interaction
                if self._slider_state['active']:
                    self._end_slider_interaction()
                
                # Determine action based on touch characteristics
                action = None
                
                if not self._touch_state['gesture_recognized']:
                    if touch_duration >= self.long_press_duration:
                        # Long press
                        action = self.handle_gesture(GestureType.LONG_PRESS,
                                                   self._touch_state['start_pos'], pos)
                    elif touch_duration <= self.tap_timeout and not self._is_drag_gesture():
                        # Tap
                        action = self.handle_gesture(GestureType.TAP,
                                                   self._touch_state['start_pos'], pos)
                
                # Execute button callback if applicable
                if (self._touch_state['active_region'] and 
                    self._touch_state['active_region'] in self._regions):
                    
                    region = self._regions[self._touch_state['active_region']]
                    callback = region.metadata.get('callback')
                    if callback and callable(callback):
                        try:
                            callback(pos)
                        except Exception as e:
                            self.logger.error(f"Button callback error: {e}")
                
                # Reset touch state
                self._touch_state = {
                    'active': False,
                    'start_pos': None,
                    'current_pos': None,
                    'start_time': None,
                    'active_region': None,
                    'gesture_recognized': False
                }
                
                return action
                
            except Exception as e:
                self.logger.error(f"Touch up handling error: {e}")
                return None
    
    def handle_gesture(self, gesture_type: GestureType, 
                      start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> Optional[TouchAction]:
        """Handle recognized gesture"""
        try:
            self.logger.debug(f"Gesture recognized: {gesture_type.name} from {start_pos} to {end_pos}")
            
            # Update statistics
            self._stats['gestures_recognized'] += 1
            
            # Execute registered callback if available
            if gesture_type in self._gesture_callbacks:
                try:
                    result = self._gesture_callbacks[gesture_type](start_pos, end_pos)
                    if result:
                        return result
                except Exception as e:
                    self.logger.error(f"Gesture callback error: {e}")
            
            # Default gesture handling
            if gesture_type == GestureType.TAP:
                return TouchAction.BUTTON_PRESS
            elif gesture_type == GestureType.LONG_PRESS:
                return TouchAction.NAVIGATION
            elif gesture_type in [GestureType.SWIPE_LEFT, GestureType.SWIPE_RIGHT]:
                return TouchAction.MODE_CHANGE
            
            return None
            
        except Exception as e:
            self.logger.error(f"Gesture handling error: {e}")
            return None
    
    def register_gesture_callback(self, gesture_type: GestureType, 
                                callback: Callable[[Tuple[int, int], Tuple[int, int]], TouchAction]) -> None:
        """Register callback for specific gesture type"""
        self._gesture_callbacks[gesture_type] = callback
        self.logger.debug(f"Registered callback for {gesture_type.name}")
    
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
            self.logger.error(f"Hit region detection error: {e}")
            return None
    
    def _handle_slider_touch_down(self, pos: Tuple[int, int], region: TouchRegion) -> TouchAction:
        """Handle touch down on slider region"""
        try:
            metadata = region.metadata
            
            self._slider_state = {
                'active': True,
                'region_id': region.region_id,
                'initial_pos': pos,
                'initial_value': metadata['current_value'],
                'track_bounds': {
                    'start_x': metadata['track_start_x'],
                    'width': metadata['track_width'],
                    'min_val': metadata['min_val'],
                    'max_val': metadata['max_val']
                }
            }
            
            # Calculate new value based on touch position
            new_value = self._calculate_slider_value(pos, self._slider_state['track_bounds'])
            metadata['current_value'] = new_value
            
            self._stats['slider_interactions'] += 1
            self.logger.debug(f"Slider {region.region_id} touched: value={new_value}")
            
            return TouchAction.SLIDER_INTERACTION
            
        except Exception as e:
            self.logger.error(f"Slider touch down error: {e}")
            return TouchAction.NONE
    
    def _handle_slider_drag(self, pos: Tuple[int, int]) -> TouchAction:
        """Handle slider drag interaction"""
        try:
            if not self._slider_state['active']:
                return TouchAction.NONE
            
            region_id = self._slider_state['region_id']
            if region_id not in self._regions:
                return TouchAction.NONE
            
            # Calculate new value
            new_value = self._calculate_slider_value(pos, self._slider_state['track_bounds'])
            
            # Update region metadata
            region = self._regions[region_id]
            old_value = region.metadata['current_value']
            region.metadata['current_value'] = new_value
            
            if new_value != old_value:
                self.logger.debug(f"Slider {region_id} dragged: {old_value} -> {new_value}")
            
            return TouchAction.SLIDER_INTERACTION
            
        except Exception as e:
            self.logger.error(f"Slider drag error: {e}")
            return TouchAction.NONE
    
    def _calculate_slider_value(self, pos: Tuple[int, int], track_bounds: Dict) -> int:
        """Calculate slider value based on touch position"""
        try:
            touch_x = pos[0]
            track_start = track_bounds['start_x']
            track_width = track_bounds['width']
            min_val = track_bounds['min_val']
            max_val = track_bounds['max_val']
            
            # Calculate normalized position (0.0 to 1.0)
            relative_x = touch_x - track_start
            normalized_pos = max(0.0, min(1.0, relative_x / track_width))
            
            # Convert to value range
            value_range = max_val - min_val
            new_value = int(min_val + (normalized_pos * value_range))
            
            return max(min_val, min(max_val, new_value))
            
        except Exception as e:
            self.logger.error(f"Slider value calculation error: {e}")
            return track_bounds.get('min_val', 0)
    
    def _handle_button_touch_down(self, pos: Tuple[int, int], region: TouchRegion) -> TouchAction:
        """Handle touch down on button region"""
        try:
            self.logger.debug(f"Button {region.region_id} pressed at {pos}")
            return region.action_type
            
        except Exception as e:
            self.logger.error(f"Button touch down error: {e}")
            return TouchAction.NONE
    
    def _end_slider_interaction(self) -> None:
        """End active slider interaction"""
        if self._slider_state['active']:
            region_id = self._slider_state['region_id']
            self.logger.debug(f"Ended slider interaction: {region_id}")
            
            self._slider_state = {
                'active': False,
                'region_id': None,
                'initial_pos': None,
                'initial_value': None,
                'track_bounds': None
            }
    
    def _recognize_gesture(self) -> Optional[GestureType]:
        """Recognize gesture based on current touch state"""
        try:
            if not self._touch_state['active']:
                return None
            
            start_pos = self._touch_state['start_pos']
            current_pos = self._touch_state['current_pos']
            
            if not start_pos or not current_pos:
                return None
            
            # Calculate movement
            dx = current_pos[0] - start_pos[0]
            dy = current_pos[1] - start_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            # Check if movement exceeds swipe threshold
            if distance >= self.swipe_threshold:
                # Determine primary direction
                if abs(dx) > abs(dy):
                    # Horizontal swipe
                    return GestureType.SWIPE_RIGHT if dx > 0 else GestureType.SWIPE_LEFT
                else:
                    # Vertical swipe
                    return GestureType.SWIPE_DOWN if dy > 0 else GestureType.SWIPE_UP
            
            return None
            
        except Exception as e:
            self.logger.error(f"Gesture recognition error: {e}")
            return None
    
    def _is_drag_gesture(self) -> bool:
        """Check if current touch constitutes a drag gesture"""
        try:
            if not self._touch_state['active']:
                return False
            
            start_pos = self._touch_state['start_pos']
            current_pos = self._touch_state['current_pos']
            
            if not start_pos or not current_pos:
                return False
            
            dx = current_pos[0] - start_pos[0]
            dy = current_pos[1] - start_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            return distance >= self.drag_threshold
            
        except Exception as e:
            self.logger.error(f"Drag detection error: {e}")
            return False
    
    def get_active_regions(self) -> List[TouchRegion]:
        """Get list of currently active touch regions"""
        with self._lock:
            return [region for region in self._regions.values() if region.enabled]
    
    def validate_coordinates(self, pos: Tuple[int, int]) -> bool:
        """Validate touch coordinates are within display bounds"""
        try:
            x, y = pos
            return (0 <= x <= self.display_bounds[0] and 
                   0 <= y <= self.display_bounds[1])
        except (ValueError, TypeError):
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get touch coordinator statistics"""
        with self._lock:
            return dict(self._stats)
    
    def get_slider_value(self, region_id: str) -> Optional[int]:
        """Get current value of a slider region"""
        with self._lock:
            if region_id in self._regions:
                region = self._regions[region_id]
                if region.metadata.get('type') == 'slider':
                    return region.metadata.get('current_value')
            return None
    
    def set_slider_value(self, region_id: str, value: int) -> bool:
        """Set value of a slider region"""
        with self._lock:
            try:
                if region_id in self._regions:
                    region = self._regions[region_id]
                    if region.metadata.get('type') == 'slider':
                        min_val = region.metadata['min_val']
                        max_val = region.metadata['max_val']
                        clamped_value = max(min_val, min(max_val, value))
                        region.metadata['current_value'] = clamped_value
                        return True
                return False
                
            except Exception as e:
                self.logger.error(f"Set slider value error: {e}")
                return False