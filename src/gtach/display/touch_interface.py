#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Hardware abstraction layer for touch interfaces in GTach display application.
Provides platform-aware touch interface selection with conditional imports.
"""

import logging
import time
import threading
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Callable, Any
from dataclasses import dataclass

# Cross-platform compatibility imports with mock objects for development
_HYPERPIXEL_AVAILABLE = False
_RPI_AVAILABLE = False

# Try to import RPi.GPIO for Raspberry Pi hardware detection
try:
    import RPi.GPIO as GPIO
    _RPI_AVAILABLE = True
except ImportError:
    # Create mock RPi.GPIO for development platforms
    class MockGPIO:
        """Mock RPi.GPIO module for development on non-Raspberry Pi platforms"""
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode):
            pass
        
        @staticmethod
        def setup(pin, mode, **kwargs):
            pass
        
        @staticmethod
        def output(pin, state):
            pass
        
        @staticmethod
        def input(pin):
            return False
        
        @staticmethod
        def cleanup():
            pass
    
    GPIO = MockGPIO()
    _RPI_AVAILABLE = False

# Try to detect hyperpixel2r availability (but don't import yet to avoid RPi dependency)
try:
    import importlib.util
    hyperpixel_spec = importlib.util.find_spec("hyperpixel2r")
    _HYPERPIXEL_AVAILABLE = hyperpixel_spec is not None
except ImportError:
    _HYPERPIXEL_AVAILABLE = False


class TouchEventType(Enum):
    """Enumeration of touch event types"""
    TOUCH_DOWN = auto()
    TOUCH_UP = auto()
    TOUCH_MOVE = auto()


@dataclass
class TouchEvent:
    """
    Touch event data structure.
    
    Attributes:
        event_type: Type of touch event (TouchEventType)
        x: Normalized X coordinate (0.0 to 1.0)
        y: Normalized Y coordinate (0.0 to 1.0)
        timestamp: Event timestamp in seconds since epoch
    """
    event_type: TouchEventType
    x: float
    y: float
    timestamp: float = 0.0
    
    def __post_init__(self):
        """Initialize timestamp if not provided"""
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        
        # Clamp coordinates to valid range
        self.x = max(0.0, min(1.0, self.x))
        self.y = max(0.0, min(1.0, self.y))


class TouchInterface(ABC):
    """
    Abstract base class for touch interface implementations.
    
    Provides a common interface for touch handling across different hardware
    implementations including HyperPixel displays and mock implementations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._callback: Optional[Callable[[TouchEvent], None]] = None
        self._running = False
        self._lock = threading.Lock()
    
    @abstractmethod
    def start(self) -> None:
        """
        Start the touch interface.
        
        Initializes hardware connections and begins touch event processing.
        Must be implemented by subclasses.
        
        Raises:
            RuntimeError: If interface fails to start
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """
        Stop the touch interface.
        
        Cleanly shuts down hardware connections and stops event processing.
        Must be implemented by subclasses.
        """
        pass
    
    def register_callback(self, callback: Callable[[TouchEvent], None]) -> None:
        """
        Register a callback function for touch events.
        
        Args:
            callback: Function to call when touch events occur.
                     Must accept a TouchEvent as its only parameter.
        
        Raises:
            ValueError: If callback is not callable
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        
        with self._lock:
            self._callback = callback
            self.logger.debug("Touch event callback registered")
    
    def unregister_callback(self) -> None:
        """Remove the current touch event callback"""
        with self._lock:
            self._callback = None
            self.logger.debug("Touch event callback unregistered")
    
    def _emit_touch_event(self, event: TouchEvent) -> None:
        """
        Emit a touch event to the registered callback.
        
        Args:
            event: TouchEvent to emit
        """
        with self._lock:
            if self._callback:
                try:
                    self._callback(event)
                except Exception as e:
                    self.logger.error(f"Error in touch callback: {e}")
            else:
                self.logger.debug(f"Touch event {event.event_type.name} at ({event.x:.3f}, {event.y:.3f}) - no callback registered")
    
    def is_running(self) -> bool:
        """
        Check if the touch interface is currently running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return self._running
    
    def get_info(self) -> dict:
        """
        Get information about the touch interface.
        
        Returns:
            dict: Interface information for debugging
        """
        return {
            'class': self.__class__.__name__,
            'running': self._running,
            'has_callback': self._callback is not None
        }


class MockHyperPixelTouch:
    """
    Mock HyperPixel Touch class for development on non-Raspberry Pi platforms.
    
    Provides the same interface as the real hyperpixel2r.Touch class but
    with simulation capabilities for development and testing.
    """
    
    def __init__(self):
        self._callback = None
        self._running = False
        self.logger = logging.getLogger('MockHyperPixelTouch')
        
    def on_touch(self, callback):
        """
        Decorator to register touch event callback.
        
        Args:
            callback: Function to call on touch events (touch_id, x, y, state)
        """
        self._callback = callback
        self.logger.debug("Touch callback registered for mock HyperPixel device")
        return callback
    
    def start(self):
        """Start the mock touch interface"""
        self._running = True
        self.logger.info("Mock HyperPixel touch interface started")
    
    def stop(self):
        """Stop the mock touch interface"""
        self._running = False
        self.logger.info("Mock HyperPixel touch interface stopped")
    
    def simulate_touch(self, x: int, y: int, state: bool, touch_id: int = 0):
        """
        Simulate a touch event for development/testing.
        
        Args:
            x: X coordinate in pixels (0-480)
            y: Y coordinate in pixels (0-480)
            state: True for touch down, False for touch up
            touch_id: Touch identifier
        """
        if self._callback and self._running:
            self.logger.debug(f"Simulating touch: id={touch_id}, pos=({x},{y}), state={state}")
            try:
                self._callback(touch_id, x, y, state)
            except Exception as e:
                self.logger.error(f"Error in mock touch callback: {e}")
        else:
            self.logger.warning("Cannot simulate touch - callback not registered or device not running")


class HyperPixelTouchInterface(TouchInterface):
    """
    Cross-platform touch interface implementation for HyperPixel displays.
    
    Automatically detects platform capability and falls back to mock
    implementation on non-Raspberry Pi systems for development.
    """
    
    def __init__(self):
        super().__init__()
        self._touch_device = None
        self._hyperpixel_available = False
        self._rpi_available = _RPI_AVAILABLE
        self._using_mock = False
        self._development_mode = False
        
        # Log platform detection results
        self.logger.info(f"Platform detection: RPi={'✅' if self._rpi_available else '❌'}, HyperPixel={'✅' if _HYPERPIXEL_AVAILABLE else '❌'}")
    
    def start(self) -> None:
        """
        Start the HyperPixel touch interface with cross-platform support.
        
        Automatically falls back to mock implementation on non-Raspberry Pi platforms.
        
        Raises:
            RuntimeError: If neither real nor mock implementation can be started
        """
        if self._running:
            self.logger.warning("HyperPixel touch interface already running")
            return
        
        # Try real hardware first if on Raspberry Pi
        if self._rpi_available and _HYPERPIXEL_AVAILABLE:
            try:
                self._start_real_hardware()
                return
            except Exception as e:
                self.logger.warning(f"Failed to start real HyperPixel hardware: {e}")
                self.logger.info("Falling back to mock implementation for development")
        
        # Fall back to mock implementation
        try:
            self._start_mock_implementation()
        except Exception as e:
            self.logger.error(f"Failed to start both real and mock implementations: {e}")
            raise RuntimeError(f"HyperPixel touch interface startup failed: {e}")
    
    def _start_real_hardware(self) -> None:
        """Start the real HyperPixel hardware implementation"""
        try:
            # Dynamic import to avoid RPi dependency on development platforms
            from hyperpixel2r import Touch
            self._hyperpixel_available = True
            self.logger.info("✅ HyperPixel2R library imported successfully")
            
            # Initialize real touch device
            self._touch_device = Touch()
            self.logger.info("✅ Real HyperPixel touch device initialized")
            
            # Set up touch event handler for real hardware
            @self._touch_device.on_touch
            def handle_real_touch(touch_id: int, x: int, y: int, state: bool):
                """Handle real touch events from HyperPixel device"""
                try:
                    # Convert pixel coordinates to normalized coordinates
                    # HyperPixel 2 Round is 480x480 pixels
                    norm_x = max(0.0, min(1.0, x / 480.0))
                    norm_y = max(0.0, min(1.0, y / 480.0))
                    
                    # Determine event type
                    event_type = TouchEventType.TOUCH_DOWN if state else TouchEventType.TOUCH_UP
                    
                    # Create and emit touch event
                    event = TouchEvent(event_type, norm_x, norm_y)
                    self.logger.debug(f"Real touch event: {event_type.name} at ({norm_x:.3f}, {norm_y:.3f})")
                    self._emit_touch_event(event)
                    
                except Exception as e:
                    self.logger.error(f"Error handling real HyperPixel touch event: {e}")
            
            self._running = True
            self._using_mock = False
            self.logger.info("✅ Real HyperPixel touch interface started successfully")
            
        except ImportError as e:
            self.logger.error(f"HyperPixel2R import failed (missing dependencies): {e}")
            raise RuntimeError(f"HyperPixel2R library dependencies not available: {e}")
        except Exception as e:
            self.logger.error(f"Real HyperPixel hardware initialization failed: {e}")
            raise RuntimeError(f"Real HyperPixel hardware startup failed: {e}")
    
    def _start_mock_implementation(self) -> None:
        """Start the mock implementation for development"""
        try:
            # Use mock touch device
            self._touch_device = MockHyperPixelTouch()
            self._hyperpixel_available = True  # Mock is "available"
            self._using_mock = True
            self._development_mode = True
            
            self.logger.info("🖥️  Using mock HyperPixel implementation for development")
            
            # Set up touch event handler for mock device
            @self._touch_device.on_touch
            def handle_mock_touch(touch_id: int, x: int, y: int, state: bool):
                """Handle mock touch events"""
                try:
                    # Convert pixel coordinates to normalized coordinates
                    norm_x = max(0.0, min(1.0, x / 480.0))
                    norm_y = max(0.0, min(1.0, y / 480.0))
                    
                    # Determine event type
                    event_type = TouchEventType.TOUCH_DOWN if state else TouchEventType.TOUCH_UP
                    
                    # Create and emit touch event
                    event = TouchEvent(event_type, norm_x, norm_y)
                    self.logger.debug(f"Mock touch event: {event_type.name} at ({norm_x:.3f}, {norm_y:.3f})")
                    self._emit_touch_event(event)
                    
                except Exception as e:
                    self.logger.error(f"Error handling mock HyperPixel touch event: {e}")
            
            # Start the mock device
            self._touch_device.start()
            
            self._running = True
            self.logger.info("✅ Mock HyperPixel touch interface started successfully")
            self.logger.info("💡 Use simulate_touch_event() method for testing touch interactions")
            
        except Exception as e:
            self.logger.error(f"Mock implementation startup failed: {e}")
            raise RuntimeError(f"Mock HyperPixel implementation failed: {e}")
    
    def stop(self) -> None:
        """Stop the HyperPixel touch interface"""
        if not self._running:
            self.logger.warning("HyperPixel touch interface not running")
            return
        
        try:
            self._running = False
            
            # Clean up touch device
            if self._touch_device:
                if self._using_mock and hasattr(self._touch_device, 'stop'):
                    self._touch_device.stop()
                self._touch_device = None
            
            implementation = "mock" if self._using_mock else "real"
            self.logger.info(f"✅ HyperPixel touch interface ({implementation}) stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping HyperPixel touch interface: {e}")
    
    def simulate_touch_event(self, x: float, y: float, state: bool, touch_id: int = 0) -> None:
        """
        Simulate a touch event for development/testing.
        
        Only works when using mock implementation.
        
        Args:
            x: Normalized X coordinate (0.0 to 1.0)
            y: Normalized Y coordinate (0.0 to 1.0)
            state: True for touch down, False for touch up
            touch_id: Touch identifier
        """
        if not self._running:
            self.logger.warning("Cannot simulate touch - interface not running")
            return
        
        if not self._using_mock:
            self.logger.warning("Touch simulation only available in mock mode (development platforms)")
            return
        
        if not hasattr(self._touch_device, 'simulate_touch'):
            self.logger.error("Mock device does not support touch simulation")
            return
        
        try:
            # Convert normalized coordinates to pixel coordinates
            pixel_x = int(x * 480)
            pixel_y = int(y * 480)
            
            # Clamp to valid range
            pixel_x = max(0, min(480, pixel_x))
            pixel_y = max(0, min(480, pixel_y))
            
            self.logger.debug(f"Simulating touch: ({x:.3f}, {y:.3f}) -> pixel ({pixel_x}, {pixel_y}), state={state}")
            self._touch_device.simulate_touch(pixel_x, pixel_y, state, touch_id)
            
        except Exception as e:
            self.logger.error(f"Error simulating touch event: {e}")
    
    def get_info(self) -> dict:
        """Get HyperPixel-specific interface information"""
        info = super().get_info()
        info.update({
            'hyperpixel_available': self._hyperpixel_available,
            'rpi_available': self._rpi_available,
            'using_mock': self._using_mock,
            'development_mode': self._development_mode,
            'device_initialized': self._touch_device is not None,
            'platform_detected': 'Raspberry Pi' if self._rpi_available else 'Development Platform',
            'implementation': 'Mock' if self._using_mock else 'Real Hardware'
        })
        return info


class MockTouchInterface(TouchInterface):
    """
    Mock touch interface implementation for development and testing.
    
    Provides comprehensive touch simulation capabilities with configurable
    behavior for development on systems without touch hardware.
    """
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__()
        self._simulation_enabled = False
        self._simulated_events = []
        self._touch_simulation_thread = None
        self._simulation_running = False
        
        # Configuration options for mock behavior
        self._config = {
            'enable_detailed_logging': True,
            'simulation_delay': 0.05,  # Delay between touch down/up in seconds
            'auto_feedback': True,  # Provide feedback for all operations
            'log_coordinates': True,  # Log coordinate information
            'simulate_pressure': False,  # Future: pressure simulation
            'gesture_recognition': True,  # Log gesture patterns
            'event_history_size': 100  # Number of events to keep in history
        }
        
        # Update config with user provided options
        if config:
            self._config.update(config)
        
        # Event history for development debugging
        self._event_history = []
        
        # Touch statistics for development insights
        self._stats = {
            'total_events': 0,
            'touch_downs': 0,
            'touch_ups': 0,
            'touch_moves': 0,
            'simulated_taps': 0,
            'gestures_detected': 0
        }
        
        if self._config['enable_detailed_logging']:
            self.logger.info("MockTouchInterface initialized with development support")
            self.logger.debug(f"Configuration: {self._config}")
    
    def start(self) -> None:
        """Start the mock touch interface with development feedback"""
        if self._running:
            self.logger.warning("Mock touch interface already running")
            return
        
        self._running = True
        self._simulation_running = True
        
        if self._config['auto_feedback']:
            self.logger.info("🖱️  Mock touch interface started - Touch simulation available")
            self.logger.info("📝 Development mode: All touch events will be logged")
            self._print_development_info()
    
    def stop(self) -> None:
        """Stop the mock touch interface with cleanup"""
        if not self._running:
            self.logger.warning("Mock touch interface not running")
            return
        
        self._running = False
        self._simulation_running = False
        self._simulated_events.clear()
        
        if self._config['auto_feedback']:
            self.logger.info("Mock touch interface stopped")
            self._print_session_stats()
    
    def configure(self, **kwargs) -> None:
        """
        Update mock interface configuration during runtime.
        
        Args:
            **kwargs: Configuration options to update
        """
        for key, value in kwargs.items():
            if key in self._config:
                old_value = self._config[key]
                self._config[key] = value
                self.logger.debug(f"Config updated: {key} = {value} (was {old_value})")
            else:
                self.logger.warning(f"Unknown configuration option: {key}")
    
    def simulate_touch(self, x: float, y: float, event_type: TouchEventType = TouchEventType.TOUCH_DOWN) -> None:
        """
        Enhanced touch simulation with comprehensive logging.
        
        Args:
            x: Normalized X coordinate (0.0 to 1.0)
            y: Normalized Y coordinate (0.0 to 1.0)
            event_type: Type of touch event to simulate
        """
        if not self._running:
            self.logger.warning("❌ Cannot simulate touch - interface not running")
            return
        
        if not self._simulation_enabled:
            self.logger.warning("❌ Touch simulation disabled - call enable_simulation() first")
            return
        
        try:
            # Validate coordinates
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                self.logger.error(f"❌ Invalid coordinates: ({x:.3f}, {y:.3f}) - must be 0.0-1.0")
                return
            
            # Create and emit event
            event = TouchEvent(event_type, x, y)
            
            # Log with detailed information
            if self._config['log_coordinates']:
                pixel_x, pixel_y = denormalize_coordinates(x, y)
                self.logger.info(f"🖱️  Simulated {event_type.name}: ({x:.3f}, {y:.3f}) -> pixel ({pixel_x}, {pixel_y})")
            
            # Update statistics
            self._update_stats(event_type)
            
            # Add to history
            self._add_to_history(event)
            
            # Emit the event
            self._emit_touch_event(event)
            
        except Exception as e:
            self.logger.error(f"❌ Error simulating touch: {e}")
    
    def simulate_tap(self, x: float, y: float, delay: Optional[float] = None) -> None:
        """
        Simulate a complete tap gesture with configurable timing.
        
        Args:
            x: Normalized X coordinate (0.0 to 1.0)
            y: Normalized Y coordinate (0.0 to 1.0)
            delay: Optional delay between down/up (uses config default if None)
        """
        if delay is None:
            delay = self._config['simulation_delay']
        
        self.logger.info(f"👆 Simulating tap at ({x:.3f}, {y:.3f}) with {delay*1000:.0f}ms delay")
        
        # Touch down
        self.simulate_touch(x, y, TouchEventType.TOUCH_DOWN)
        
        # Realistic delay
        time.sleep(delay)
        
        # Touch up
        self.simulate_touch(x, y, TouchEventType.TOUCH_UP)
        
        # Update tap statistics
        self._stats['simulated_taps'] += 1
        
        if self._config['gesture_recognition']:
            self.logger.debug(f"✅ Tap gesture completed ({self._stats['simulated_taps']} total)")
    
    def simulate_long_press(self, x: float, y: float, duration: float = 1.0) -> None:
        """
        Simulate a long press gesture.
        
        Args:
            x: Normalized X coordinate (0.0 to 1.0)
            y: Normalized Y coordinate (0.0 to 1.0)  
            duration: Press duration in seconds
        """
        self.logger.info(f"👆⏰ Simulating long press at ({x:.3f}, {y:.3f}) for {duration:.1f}s")
        
        # Touch down
        self.simulate_touch(x, y, TouchEventType.TOUCH_DOWN)
        
        # Hold for specified duration
        time.sleep(duration)
        
        # Touch up
        self.simulate_touch(x, y, TouchEventType.TOUCH_UP)
        
        if self._config['gesture_recognition']:
            self.logger.info(f"✅ Long press gesture completed ({duration:.1f}s)")
    
    def simulate_swipe(self, start_x: float, start_y: float, end_x: float, end_y: float, steps: int = 10, duration: float = 0.5) -> None:
        """
        Simulate a swipe gesture.
        
        Args:
            start_x: Starting X coordinate (0.0 to 1.0)
            start_y: Starting Y coordinate (0.0 to 1.0)
            end_x: Ending X coordinate (0.0 to 1.0)
            end_y: Ending Y coordinate (0.0 to 1.0)
            steps: Number of intermediate points
            duration: Total swipe duration in seconds
        """
        self.logger.info(f"👆↗️ Simulating swipe from ({start_x:.3f}, {start_y:.3f}) to ({end_x:.3f}, {end_y:.3f})")
        
        # Touch down at start
        self.simulate_touch(start_x, start_y, TouchEventType.TOUCH_DOWN)
        
        # Generate intermediate points
        step_delay = duration / steps
        for i in range(1, steps):
            progress = i / steps
            curr_x = start_x + (end_x - start_x) * progress
            curr_y = start_y + (end_y - start_y) * progress
            
            self.simulate_touch(curr_x, curr_y, TouchEventType.TOUCH_MOVE)
            time.sleep(step_delay)
        
        # Touch up at end
        self.simulate_touch(end_x, end_y, TouchEventType.TOUCH_UP)
        
        if self._config['gesture_recognition']:
            self.logger.info(f"✅ Swipe gesture completed in {duration:.1f}s")
    
    def simulate_touch_event(self, event_type: TouchEventType, x: float, y: float) -> None:
        """
        Legacy method - redirects to simulate_touch for backward compatibility.
        
        Args:
            event_type: Type of touch event to simulate
            x: Normalized X coordinate (0.0 to 1.0)
            y: Normalized Y coordinate (0.0 to 1.0)
        """
        self.simulate_touch(x, y, event_type)
    
    def enable_simulation(self) -> None:
        """Enable touch event simulation with feedback"""
        self._simulation_enabled = True
        if self._config['auto_feedback']:
            self.logger.info("✅ Touch simulation enabled - Ready for development testing")
            self.logger.info("💡 Use simulate_tap(), simulate_long_press(), or simulate_swipe() methods")
    
    def disable_simulation(self) -> None:
        """Disable touch event simulation with feedback"""
        self._simulation_enabled = False
        if self._config['auto_feedback']:
            self.logger.info("⛔ Touch simulation disabled")
    
    def get_development_info(self) -> dict:
        """
        Get comprehensive development information.
        
        Returns:
            dict: Detailed interface state and statistics
        """
        return {
            'interface_type': 'MockTouchInterface',
            'running': self._running,
            'simulation_enabled': self._simulation_enabled,
            'configuration': self._config.copy(),
            'statistics': self._stats.copy(),
            'event_history_size': len(self._event_history),
            'last_event': self._event_history[-1] if self._event_history else None
        }
    
    def get_info(self) -> dict:
        """Get mock interface information (legacy compatibility)"""
        info = super().get_info()
        info.update({
            'simulation_enabled': self._simulation_enabled,
            'pending_events': len(self._simulated_events),
            'total_events_processed': self._stats['total_events']
        })
        return info
    
    def print_statistics(self) -> None:
        """Print detailed usage statistics for development"""
        self.logger.info("📊 Touch Interface Statistics:")
        for key, value in self._stats.items():
            self.logger.info(f"   {key.replace('_', ' ').title()}: {value}")
    
    def clear_history(self) -> None:
        """Clear event history and reset statistics"""
        self._event_history.clear()
        self._stats = {key: 0 for key in self._stats}
        self.logger.info("🧹 Event history and statistics cleared")
    
    def _update_stats(self, event_type: TouchEventType) -> None:
        """Update internal statistics"""
        self._stats['total_events'] += 1
        if event_type == TouchEventType.TOUCH_DOWN:
            self._stats['touch_downs'] += 1
        elif event_type == TouchEventType.TOUCH_UP:
            self._stats['touch_ups'] += 1
        elif event_type == TouchEventType.TOUCH_MOVE:
            self._stats['touch_moves'] += 1
    
    def _add_to_history(self, event: TouchEvent) -> None:
        """Add event to history with size management"""
        self._event_history.append({
            'type': event.event_type.name,
            'x': event.x,
            'y': event.y,
            'timestamp': event.timestamp
        })
        
        # Maintain history size limit
        max_size = self._config['event_history_size']
        if len(self._event_history) > max_size:
            self._event_history = self._event_history[-max_size:]
    
    def _print_development_info(self) -> None:
        """Print helpful development information"""
        self.logger.info("🛠️  Development Features Available:")
        self.logger.info("   • simulate_tap(x, y) - Simulate button/UI taps")
        self.logger.info("   • simulate_long_press(x, y, duration) - Simulate long press gestures")
        self.logger.info("   • simulate_swipe(x1, y1, x2, y2) - Simulate swipe gestures")
        self.logger.info("   • get_development_info() - Get detailed interface state")
        self.logger.info("   • print_statistics() - Show usage statistics")
        self.logger.info("   • configure(**options) - Update runtime configuration")
    
    def _print_session_stats(self) -> None:
        """Print session statistics on shutdown"""
        if self._stats['total_events'] > 0:
            self.logger.info("📊 Session Summary:")
            self.logger.info(f"   Total Events: {self._stats['total_events']}")
            self.logger.info(f"   Simulated Taps: {self._stats['simulated_taps']}")
            self.logger.info(f"   Touch Downs: {self._stats['touch_downs']}")
            self.logger.info(f"   Touch Ups: {self._stats['touch_ups']}")
            if self._stats['touch_moves'] > 0:
                self.logger.info(f"   Touch Moves: {self._stats['touch_moves']}")
        else:
            self.logger.info("📊 No touch events simulated during this session")


def create_touch_interface() -> TouchInterface:
    """
    Factory function to create appropriate touch interface based on platform.
    
    Uses enhanced cross-platform detection with automatic fallback handling.
    The HyperPixelTouchInterface now handles both real hardware and mock
    implementation internally.
    
    Returns:
        TouchInterface: Platform-appropriate touch interface instance
        
    Raises:
        RuntimeError: If no suitable touch interface can be created
    """
    logger = logging.getLogger('TouchInterfaceFactory')
    
    try:
        # Enhanced platform detection with RPi module availability
        platform_info = {
            'rpi_module_available': _RPI_AVAILABLE,
            'hyperpixel_available': _HYPERPIXEL_AVAILABLE,
            'platform_type': 'Raspberry Pi' if _RPI_AVAILABLE else 'Development Platform'
        }
        
        logger.info(f"🔍 Platform Analysis:")
        logger.info(f"   RPi Module: {'✅' if _RPI_AVAILABLE else '❌'}")
        logger.info(f"   HyperPixel: {'✅' if _HYPERPIXEL_AVAILABLE else '❌'}")
        logger.info(f"   Platform: {platform_info['platform_type']}")
        
        # Try to import additional platform detection utilities for enhanced detection
        try:
            from ..utils.platform import is_raspberry_pi, is_gpio_available, get_platform_info
            additional_platform_info = get_platform_info()
            is_rpi = is_raspberry_pi()
            gpio_available = is_gpio_available()
            
            logger.debug(f"Additional platform detection: RPi={is_rpi}, GPIO={gpio_available}")
            
            # Update platform info with additional detection
            platform_info.update({
                'gpio_available': gpio_available,
                'platform_confirmed': is_rpi,
                'additional_info': additional_platform_info
            })
            
        except ImportError as e:
            logger.debug(f"Additional platform detection not available: {e}")
            platform_info.update({
                'gpio_available': _RPI_AVAILABLE,  # Use RPi module availability as fallback
                'platform_confirmed': _RPI_AVAILABLE
            })
        
        # Create HyperPixelTouchInterface with cross-platform support
        # It will automatically handle real hardware vs mock implementation
        try:
            logger.info("🔄 Creating cross-platform HyperPixel touch interface...")
            interface = HyperPixelTouchInterface()
            logger.info("✅ HyperPixel touch interface created successfully")
            return interface
            
        except Exception as e:
            logger.warning(f"HyperPixel interface creation failed: {e}")
            logger.info("🔄 Falling back to dedicated mock interface...")
            
            # Fall back to dedicated MockTouchInterface as last resort
            try:
                interface = MockTouchInterface()
                logger.info("✅ Mock touch interface created as fallback")
                return interface
            except Exception as fallback_error:
                logger.error(f"Even mock interface creation failed: {fallback_error}")
                raise RuntimeError(f"Failed to create any touch interface: {fallback_error}")
            
    except Exception as e:
        logger.error(f"Critical error in touch interface factory: {e}")
        # Ultimate fallback - try to create basic mock interface
        try:
            logger.info("🆘 Attempting emergency mock interface creation...")
            return MockTouchInterface()
        except Exception as emergency_error:
            raise RuntimeError(f"Complete touch interface factory failure: {emergency_error}")


class TouchInterfaceError(Exception):
    """Exception raised for touch interface specific errors"""
    pass


class TouchInterfaceNotAvailableError(TouchInterfaceError):
    """Exception raised when requested touch interface is not available"""
    pass


def get_available_interfaces() -> list:
    """
    Get a list of available touch interface types with platform detection.
    
    Returns:
        list: List of available interface class names with platform info
    """
    available = []
    
    # MockTouchInterface is always available
    available.append({
        'name': 'MockTouchInterface',
        'type': 'Mock',
        'platform_support': 'All Platforms',
        'status': 'Available'
    })
    
    # HyperPixelTouchInterface with cross-platform support
    hyperpixel_status = 'Available (Cross-Platform)'
    hyperpixel_details = []
    
    if _RPI_AVAILABLE:
        hyperpixel_details.append('RPi.GPIO: ✅')
    else:
        hyperpixel_details.append('RPi.GPIO: ❌ (Mock fallback)')
    
    if _HYPERPIXEL_AVAILABLE:
        hyperpixel_details.append('HyperPixel2R: ✅')
    else:
        hyperpixel_details.append('HyperPixel2R: ❌ (Mock fallback)')
    
    available.append({
        'name': 'HyperPixelTouchInterface',
        'type': 'Hardware/Mock Hybrid',
        'platform_support': 'Raspberry Pi (Hardware) + Development Platforms (Mock)',
        'status': hyperpixel_status,
        'details': hyperpixel_details
    })
    
    return available


def create_specific_interface(interface_type: str) -> TouchInterface:
    """
    Create a specific type of touch interface.
    
    Args:
        interface_type: Type of interface to create ('mock' or 'hyperpixel')
        
    Returns:
        TouchInterface: Requested touch interface instance
        
    Raises:
        TouchInterfaceNotAvailableError: If requested interface is not available
        ValueError: If interface_type is not recognized
    """
    logger = logging.getLogger('TouchInterfaceFactory')
    
    interface_type = interface_type.lower()
    
    if interface_type == 'mock':
        logger.info("Creating mock touch interface")
        return MockTouchInterface()
    
    elif interface_type == 'hyperpixel':
        try:
            logger.info("Creating HyperPixel touch interface")
            return HyperPixelTouchInterface()
        except Exception as e:
            raise TouchInterfaceNotAvailableError(f"HyperPixel interface not available: {e}")
    
    else:
        raise ValueError(f"Unknown interface type: {interface_type}")


# Module-level convenience functions
def normalize_coordinates(x: int, y: int, width: int = 480, height: int = 480) -> tuple:
    """
    Normalize pixel coordinates to 0.0-1.0 range.
    
    Args:
        x: X coordinate in pixels
        y: Y coordinate in pixels
        width: Display width in pixels (default: 480 for HyperPixel)
        height: Display height in pixels (default: 480 for HyperPixel)
        
    Returns:
        tuple: (normalized_x, normalized_y)
    """
    norm_x = max(0.0, min(1.0, x / width))
    norm_y = max(0.0, min(1.0, y / height))
    return norm_x, norm_y


def denormalize_coordinates(norm_x: float, norm_y: float, width: int = 480, height: int = 480) -> tuple:
    """
    Convert normalized coordinates back to pixel coordinates.
    
    Args:
        norm_x: Normalized X coordinate (0.0 to 1.0)
        norm_y: Normalized Y coordinate (0.0 to 1.0)
        width: Display width in pixels (default: 480 for HyperPixel)
        height: Display height in pixels (default: 480 for HyperPixel)
        
    Returns:
        tuple: (x_pixels, y_pixels)
    """
    x = int(norm_x * width)
    y = int(norm_y * height)
    return x, y