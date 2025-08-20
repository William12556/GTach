#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Hardware interface for OBDII display application.
Provides touch interface abstraction with support for both real hardware and mock implementations.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any, List, Tuple
from enum import Enum, auto
from dataclasses import dataclass
from functools import wraps


class TouchEventType(Enum):
    """Touch event types"""
    TOUCH_DOWN = auto()
    TOUCH_UP = auto()
    TOUCH_MOVE = auto()
    TOUCH_HOLD = auto()
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()
    SWIPE_UP = auto()
    SWIPE_DOWN = auto()


@dataclass
class TouchEvent:
    """
    Touch event data structure.
    
    Attributes:
        event_type: Type of touch event
        x: X coordinate (0-1 normalized)
        y: Y coordinate (0-1 normalized)
        pressure: Touch pressure (0-1, if available)
        timestamp: Event timestamp
        duration: Duration for hold events
        distance: Distance for swipe events
    """
    event_type: TouchEventType
    x: float
    y: float
    pressure: float = 0.0
    timestamp: float = 0.0
    duration: float = 0.0
    distance: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class TouchZone:
    """
    Define a touch zone for event handling.
    
    Attributes:
        name: Zone identifier
        x: X coordinate (0-1 normalized)
        y: Y coordinate (0-1 normalized)
        width: Zone width (0-1 normalized)
        height: Zone height (0-1 normalized)
        callback: Function to call on touch
    """
    
    def __init__(self, name: str, x: float, y: float, width: float, height: float, 
                 callback: Optional[Callable[[TouchEvent], None]] = None):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.callback = callback
        self.logger = logging.getLogger(f'TouchZone.{name}')
    
    def contains(self, x: float, y: float) -> bool:
        """Check if coordinates are within this zone"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def handle_touch(self, event: TouchEvent) -> bool:
        """Handle touch event if it's within this zone"""
        if self.contains(event.x, event.y):
            if self.callback:
                try:
                    self.callback(event)
                    self.logger.debug(f"Touch event handled in zone {self.name}")
                    return True
                except Exception as e:
                    self.logger.error(f"Error handling touch in zone {self.name}: {e}")
            return True
        return False


class TouchInterface(ABC):
    """
    Abstract base class for touch interface implementations.
    
    Provides a common interface for touch handling across different hardware
    implementations including real touch displays and mock implementations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._touch_handlers: Dict[TouchEventType, List[Callable[[TouchEvent], None]]] = {}
        self._touch_zones: List[TouchZone] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Touch state tracking
        self._last_touch_time = 0.0
        self._last_touch_pos = (0.0, 0.0)
        self._touch_start_time = 0.0
        self._touch_start_pos = (0.0, 0.0)
        self._is_touching = False
        
        # Configuration
        self.hold_threshold = 1.0  # seconds
        self.swipe_threshold = 0.2  # normalized distance
        self.debounce_time = 0.05  # seconds
    
    @abstractmethod
    def start(self) -> None:
        """Start the touch interface"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the touch interface"""
        pass
    
    @abstractmethod
    def _read_touch_events(self) -> List[TouchEvent]:
        """Read touch events from hardware - to be implemented by subclasses"""
        pass
    
    def on_touch(self, event_type: TouchEventType):
        """
        Decorator for registering touch event handlers.
        
        Usage:
            @touch_interface.on_touch(TouchEventType.TOUCH_DOWN)
            def handle_touch_down(event):
                print(f"Touch down at {event.x}, {event.y}")
        
        Args:
            event_type: Type of touch event to handle
        """
        def decorator(func: Callable[[TouchEvent], None]):
            self.register_touch_handler(event_type, func)
            return func
        return decorator
    
    def register_touch_handler(self, event_type: TouchEventType, 
                             handler: Callable[[TouchEvent], None]) -> None:
        """
        Register a handler for a specific touch event type.
        
        Args:
            event_type: Type of touch event
            handler: Function to call when event occurs
        """
        with self._lock:
            if event_type not in self._touch_handlers:
                self._touch_handlers[event_type] = []
            self._touch_handlers[event_type].append(handler)
            self.logger.debug(f"Registered handler for {event_type.name}")
    
    def unregister_touch_handler(self, event_type: TouchEventType,
                                handler: Callable[[TouchEvent], None]) -> None:
        """
        Unregister a touch event handler.
        
        Args:
            event_type: Type of touch event
            handler: Handler function to remove
        """
        with self._lock:
            if event_type in self._touch_handlers:
                try:
                    self._touch_handlers[event_type].remove(handler)
                    self.logger.debug(f"Unregistered handler for {event_type.name}")
                except ValueError:
                    self.logger.warning(f"Handler not found for {event_type.name}")
    
    def add_touch_zone(self, zone: TouchZone) -> None:
        """
        Add a touch zone for event handling.
        
        Args:
            zone: TouchZone to add
        """
        with self._lock:
            self._touch_zones.append(zone)
            self.logger.debug(f"Added touch zone: {zone.name}")
    
    def remove_touch_zone(self, zone_name: str) -> None:
        """
        Remove a touch zone by name.
        
        Args:
            zone_name: Name of zone to remove
        """
        with self._lock:
            self._touch_zones = [z for z in self._touch_zones if z.name != zone_name]
            self.logger.debug(f"Removed touch zone: {zone_name}")
    
    def get_touch_zone(self, zone_name: str) -> Optional[TouchZone]:
        """
        Get a touch zone by name.
        
        Args:
            zone_name: Name of zone to find
            
        Returns:
            TouchZone if found, None otherwise
        """
        with self._lock:
            for zone in self._touch_zones:
                if zone.name == zone_name:
                    return zone
        return None
    
    def _emit_touch_event(self, event: TouchEvent) -> None:
        """
        Emit a touch event to all registered handlers.
        
        Args:
            event: TouchEvent to emit
        """
        # Handle touch zones first
        zone_handled = False
        with self._lock:
            for zone in self._touch_zones:
                if zone.handle_touch(event):
                    zone_handled = True
                    break
        
        # Handle global event handlers
        with self._lock:
            if event.event_type in self._touch_handlers:
                for handler in self._touch_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        self.logger.error(f"Error in touch handler: {e}")
        
        if not zone_handled:
            self.logger.debug(f"Touch event {event.event_type.name} at ({event.x:.3f}, {event.y:.3f})")
    
    def _process_touch_events(self) -> None:
        """Process touch events from hardware"""
        try:
            events = self._read_touch_events()
            for event in events:
                self._process_single_event(event)
        except Exception as e:
            self.logger.error(f"Error processing touch events: {e}")
    
    def _process_single_event(self, event: TouchEvent) -> None:
        """Process a single touch event with gesture detection"""
        current_time = time.time()
        
        # Debounce check
        if current_time - self._last_touch_time < self.debounce_time:
            return
        
        if event.event_type == TouchEventType.TOUCH_DOWN:
            self._is_touching = True
            self._touch_start_time = current_time
            self._touch_start_pos = (event.x, event.y)
            self._last_touch_pos = (event.x, event.y)
            
        elif event.event_type == TouchEventType.TOUCH_UP:
            if self._is_touching:
                # Check for hold gesture
                hold_duration = current_time - self._touch_start_time
                if hold_duration >= self.hold_threshold:
                    hold_event = TouchEvent(
                        TouchEventType.TOUCH_HOLD,
                        event.x, event.y,
                        event.pressure,
                        current_time,
                        hold_duration
                    )
                    self._emit_touch_event(hold_event)
                else:
                    # Check for swipe gesture
                    dx = event.x - self._touch_start_pos[0]
                    dy = event.y - self._touch_start_pos[1]
                    distance = (dx**2 + dy**2)**0.5
                    
                    if distance >= self.swipe_threshold:
                        # Determine swipe direction
                        if abs(dx) > abs(dy):
                            swipe_type = TouchEventType.SWIPE_RIGHT if dx > 0 else TouchEventType.SWIPE_LEFT
                        else:
                            swipe_type = TouchEventType.SWIPE_DOWN if dy > 0 else TouchEventType.SWIPE_UP
                        
                        swipe_event = TouchEvent(
                            swipe_type,
                            event.x, event.y,
                            event.pressure,
                            current_time,
                            distance=distance
                        )
                        self._emit_touch_event(swipe_event)
                
                self._is_touching = False
        
        elif event.event_type == TouchEventType.TOUCH_MOVE:
            if self._is_touching:
                self._last_touch_pos = (event.x, event.y)
        
        # Always emit the original event
        self._emit_touch_event(event)
        self._last_touch_time = current_time
    
    def _touch_loop(self) -> None:
        """Main touch processing loop"""
        self.logger.info("Touch interface loop started")
        
        while self._running:
            try:
                self._process_touch_events()
                time.sleep(0.01)  # 100 Hz polling
            except Exception as e:
                self.logger.error(f"Error in touch loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("Touch interface loop stopped")
    
    def is_running(self) -> bool:
        """Check if touch interface is running"""
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """Get touch interface status"""
        return {
            'running': self._running,
            'handler_count': sum(len(handlers) for handlers in self._touch_handlers.values()),
            'zone_count': len(self._touch_zones),
            'is_touching': self._is_touching,
            'last_touch_time': self._last_touch_time
        }


class MockTouchInterface(TouchInterface):
    """
    Mock touch interface implementation for testing and development.
    
    Provides no-op implementations that log touch events for debugging
    on systems without touch hardware.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('MockTouchInterface')
        self._simulated_events: List[TouchEvent] = []
        self._simulation_enabled = False
    
    def start(self) -> None:
        """Start the mock touch interface"""
        if self._running:
            self.logger.warning("Mock touch interface already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._touch_loop, name='MockTouchInterface')
        self._thread.daemon = True
        self._thread.start()
        
        self.logger.info("Mock touch interface started")
    
    def stop(self) -> None:
        """Stop the mock touch interface"""
        if not self._running:
            self.logger.warning("Mock touch interface not running")
            return
        
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self.logger.warning("Mock touch interface thread did not stop cleanly")
        
        self.logger.info("Mock touch interface stopped")
    
    def _read_touch_events(self) -> List[TouchEvent]:
        """Read simulated touch events"""
        events = []
        
        if self._simulation_enabled and self._simulated_events:
            # Return and clear simulated events
            events = self._simulated_events.copy()
            self._simulated_events.clear()
        
        return events
    
    def simulate_touch_event(self, event: TouchEvent) -> None:
        """
        Simulate a touch event for testing.
        
        Args:
            event: TouchEvent to simulate
        """
        self._simulated_events.append(event)
        self.logger.debug(f"Simulated touch event: {event.event_type.name} at ({event.x:.3f}, {event.y:.3f})")
    
    def simulate_touch_down(self, x: float, y: float, pressure: float = 1.0) -> None:
        """Simulate a touch down event"""
        event = TouchEvent(TouchEventType.TOUCH_DOWN, x, y, pressure)
        self.simulate_touch_event(event)
    
    def simulate_touch_up(self, x: float, y: float, pressure: float = 0.0) -> None:
        """Simulate a touch up event"""
        event = TouchEvent(TouchEventType.TOUCH_UP, x, y, pressure)
        self.simulate_touch_event(event)
    
    def simulate_touch_move(self, x: float, y: float, pressure: float = 1.0) -> None:
        """Simulate a touch move event"""
        event = TouchEvent(TouchEventType.TOUCH_MOVE, x, y, pressure)
        self.simulate_touch_event(event)
    
    def simulate_tap(self, x: float, y: float, pressure: float = 1.0) -> None:
        """Simulate a complete tap gesture (down + up)"""
        self.simulate_touch_down(x, y, pressure)
        time.sleep(0.01)  # Small delay
        self.simulate_touch_up(x, y, 0.0)
    
    def simulate_swipe(self, start_x: float, start_y: float, end_x: float, end_y: float,
                      steps: int = 10, pressure: float = 1.0) -> None:
        """
        Simulate a swipe gesture.
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            steps: Number of intermediate move events
            pressure: Touch pressure
        """
        # Start touch
        self.simulate_touch_down(start_x, start_y, pressure)
        
        # Intermediate moves
        for i in range(1, steps):
            progress = i / steps
            x = start_x + (end_x - start_x) * progress
            y = start_y + (end_y - start_y) * progress
            self.simulate_touch_move(x, y, pressure)
            time.sleep(0.01)
        
        # End touch
        self.simulate_touch_up(end_x, end_y, 0.0)
    
    def simulate_hold(self, x: float, y: float, duration: float = 1.5, pressure: float = 1.0) -> None:
        """
        Simulate a hold gesture.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Hold duration in seconds
            pressure: Touch pressure
        """
        self.simulate_touch_down(x, y, pressure)
        time.sleep(duration)
        self.simulate_touch_up(x, y, 0.0)
    
    def enable_simulation(self) -> None:
        """Enable touch event simulation"""
        self._simulation_enabled = True
        self.logger.info("Touch simulation enabled")
    
    def disable_simulation(self) -> None:
        """Disable touch event simulation"""
        self._simulation_enabled = False
        self._simulated_events.clear()
        self.logger.info("Touch simulation disabled")
    
    def is_simulation_enabled(self) -> bool:
        """Check if simulation is enabled"""
        return self._simulation_enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get mock touch interface status"""
        status = super().get_status()
        status.update({
            'simulation_enabled': self._simulation_enabled,
            'pending_events': len(self._simulated_events),
            'interface_type': 'mock'
        })
        return status


def create_touch_interface() -> TouchInterface:
    """
    Create appropriate touch interface based on platform.
    
    Returns:
        TouchInterface: Platform-appropriate touch interface
    """
    try:
        # Try to import platform detection
        from ..utils.platform import is_raspberry_pi, is_gpio_available
        
        if is_raspberry_pi() and is_gpio_available():
            # TODO: Import and return real touch interface when implemented
            # from .hyperpixel_touch import HyperPixelTouchInterface
            # return HyperPixelTouchInterface()
            logger = logging.getLogger('TouchInterface')
            logger.info("Raspberry Pi detected, but real touch interface not implemented yet")
            return MockTouchInterface()
        else:
            logger = logging.getLogger('TouchInterface')
            logger.info("Using mock touch interface (not on Raspberry Pi)")
            return MockTouchInterface()
    
    except ImportError:
        logger = logging.getLogger('TouchInterface')
        logger.warning("Platform detection not available, using mock touch interface")
        return MockTouchInterface()


# Convenience functions for common touch zones
def create_button_zone(name: str, x: float, y: float, width: float, height: float,
                      callback: Callable[[TouchEvent], None]) -> TouchZone:
    """
    Create a button touch zone.
    
    Args:
        name: Button name
        x: X coordinate (0-1 normalized)
        y: Y coordinate (0-1 normalized)
        width: Button width (0-1 normalized)
        height: Button height (0-1 normalized)
        callback: Function to call on touch
        
    Returns:
        TouchZone: Configured button zone
    """
    return TouchZone(name, x, y, width, height, callback)


def create_fullscreen_zone(name: str, callback: Callable[[TouchEvent], None]) -> TouchZone:
    """
    Create a fullscreen touch zone.
    
    Args:
        name: Zone name
        callback: Function to call on touch
        
    Returns:
        TouchZone: Fullscreen touch zone
    """
    return TouchZone(name, 0.0, 0.0, 1.0, 1.0, callback)