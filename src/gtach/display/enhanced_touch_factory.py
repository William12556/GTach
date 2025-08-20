#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Enhanced TouchInterfaceFactory with platform-aware module loading.
Provides sophisticated hardware detection and mock fallbacks for development.
"""

import logging
import time
import threading
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass

# Import platform detection utilities
try:
    from ..utils.platform import (
        get_platform_type, is_raspberry_pi, is_gpio_available,
        get_hardware_modules, get_conditional_import_status,
        PlatformType
    )
    PLATFORM_UTILS_AVAILABLE = True
except ImportError:
    PLATFORM_UTILS_AVAILABLE = False


class TouchInterfaceType(Enum):
    """Types of touch interfaces"""
    HARDWARE = auto()
    MOCK = auto()
    HYBRID = auto()


class TouchSimulationMode(Enum):
    """Touch simulation modes for development"""
    NONE = auto()
    BASIC = auto()
    INTERACTIVE = auto()
    AUTOMATED = auto()


@dataclass
class TouchInterfaceCapabilities:
    """Capabilities of a touch interface"""
    supports_multitouch: bool = False
    supports_pressure: bool = False
    supports_gestures: bool = True
    supports_simulation: bool = False
    max_touch_points: int = 1
    resolution: tuple = (480, 480)
    platform_specific: bool = False


class EnhancedTouchInterface(ABC):
    """Enhanced abstract base class for touch interfaces"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._running = False
        self._callbacks = []
        self._capabilities = TouchInterfaceCapabilities()
    
    @abstractmethod
    def start(self) -> None:
        """Start the touch interface"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the touch interface"""
        pass
    
    @abstractmethod
    def register_callback(self, callback: Callable) -> None:
        """Register a touch event callback"""
        pass
    
    def get_capabilities(self) -> TouchInterfaceCapabilities:
        """Get interface capabilities"""
        return self._capabilities
    
    def is_running(self) -> bool:
        """Check if interface is running"""
        return self._running
    
    def get_info(self) -> Dict[str, Any]:
        """Get interface information"""
        return {
            'type': self.__class__.__name__,
            'running': self._running,
            'capabilities': self._capabilities.__dict__,
            'callback_count': len(self._callbacks)
        }


class DevelopmentTouchInterface(EnhancedTouchInterface):
    """
    Advanced mock touch interface for development and testing.
    
    Provides comprehensive simulation capabilities for UI development
    without requiring actual hardware.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        
        # Configuration with development-friendly defaults
        self._config = {
            'simulation_mode': TouchSimulationMode.INTERACTIVE,
            'auto_feedback': True,
            'log_coordinates': True,
            'gesture_recognition': True,
            'event_history_size': 100,
            'ui_test_mode': False,
            'automated_patterns': True,
            'pressure_simulation': False,
            'multitouch_simulation': False
        }
        
        if config:
            self._config.update(config)
        
        # Development state
        self._simulation_thread = None
        self._event_history = []
        self._gesture_buffer = []
        self._ui_test_scenarios = []
        self._stats = {
            'events_generated': 0,
            'gestures_simulated': 0,
            'ui_tests_run': 0,
            'total_runtime': 0.0
        }
        
        # Set capabilities
        self._capabilities = TouchInterfaceCapabilities(
            supports_multitouch=self._config['multitouch_simulation'],
            supports_pressure=self._config['pressure_simulation'],
            supports_gestures=True,
            supports_simulation=True,
            max_touch_points=5 if self._config['multitouch_simulation'] else 1,
            resolution=(480, 480),
            platform_specific=False
        )
        
        self.logger.info("DevelopmentTouchInterface initialized for UI testing")
    
    def start(self) -> None:
        """Start the development touch interface"""
        if self._running:
            self.logger.warning("Development interface already running")
            return
        
        self._running = True
        self._stats['start_time'] = time.time()
        
        if self._config['auto_feedback']:
            self.logger.info("🎯 Development Touch Interface Started")
            self.logger.info("   Mode: UI Development & Testing")
            self.logger.info("   Simulation: Interactive touch events available")
            self.logger.info("   Commands: Use simulate_*() methods for testing")
        
        # Start automated simulation if enabled
        if self._config['simulation_mode'] == TouchSimulationMode.AUTOMATED:
            self._start_automated_simulation()
    
    def stop(self) -> None:
        """Stop the development touch interface"""
        if not self._running:
            self.logger.warning("Development interface not running")
            return
        
        self._running = False
        
        if self._simulation_thread and self._simulation_thread.is_alive():
            self._simulation_thread.join(timeout=1.0)
        
        # Calculate stats
        if 'start_time' in self._stats:
            self._stats['total_runtime'] = time.time() - self._stats['start_time']
        
        if self._config['auto_feedback']:
            self._print_session_summary()
        
        self.logger.info("Development touch interface stopped")
    
    def register_callback(self, callback: Callable) -> None:
        """Register a touch event callback"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            self.logger.debug(f"Registered touch callback: {callback.__name__}")
    
    def simulate_tap(self, x: float, y: float, duration: float = 0.1) -> None:
        """
        Simulate a tap gesture at specified coordinates.
        
        Args:
            x: X coordinate (0.0 to 1.0)
            y: Y coordinate (0.0 to 1.0)
            duration: Tap duration in seconds
        """
        if not self._running:
            self.logger.warning("Cannot simulate tap - interface not running")
            return
        
        self._simulate_touch_sequence([
            {'x': x, 'y': y, 'state': True, 'delay': 0},
            {'x': x, 'y': y, 'state': False, 'delay': duration}
        ])
        
        self._stats['events_generated'] += 2
        
        if self._config['log_coordinates']:
            pixel_x, pixel_y = int(x * 480), int(y * 480)
            self.logger.info(f"📱 Simulated tap: ({x:.3f}, {y:.3f}) -> pixel ({pixel_x}, {pixel_y})")
    
    def simulate_swipe(self, start_x: float, start_y: float, 
                      end_x: float, end_y: float, 
                      duration: float = 0.3, steps: int = 10) -> None:
        """
        Simulate a swipe gesture.
        
        Args:
            start_x, start_y: Starting coordinates (0.0 to 1.0)
            end_x, end_y: Ending coordinates (0.0 to 1.0)
            duration: Swipe duration in seconds
            steps: Number of intermediate points
        """
        if not self._running:
            self.logger.warning("Cannot simulate swipe - interface not running")
            return
        
        sequence = []
        step_delay = duration / steps
        
        # Touch down
        sequence.append({'x': start_x, 'y': start_y, 'state': True, 'delay': 0})
        
        # Intermediate points
        for i in range(1, steps):
            progress = i / steps
            x = start_x + (end_x - start_x) * progress
            y = start_y + (end_y - start_y) * progress
            sequence.append({'x': x, 'y': y, 'state': True, 'delay': step_delay})
        
        # Touch up
        sequence.append({'x': end_x, 'y': end_y, 'state': False, 'delay': step_delay})
        
        self._simulate_touch_sequence(sequence)
        self._stats['gestures_simulated'] += 1
        
        if self._config['log_coordinates']:
            direction = self._get_swipe_direction(start_x, start_y, end_x, end_y)
            self.logger.info(f"👆 Simulated {direction} swipe: ({start_x:.3f}, {start_y:.3f}) → ({end_x:.3f}, {end_y:.3f})")
    
    def simulate_long_press(self, x: float, y: float, duration: float = 1.0) -> None:
        """
        Simulate a long press gesture.
        
        Args:
            x: X coordinate (0.0 to 1.0)
            y: Y coordinate (0.0 to 1.0)
            duration: Press duration in seconds
        """
        if not self._running:
            self.logger.warning("Cannot simulate long press - interface not running")
            return
        
        self._simulate_touch_sequence([
            {'x': x, 'y': y, 'state': True, 'delay': 0},
            {'x': x, 'y': y, 'state': False, 'delay': duration}
        ])
        
        self._stats['gestures_simulated'] += 1
        
        if self._config['log_coordinates']:
            self.logger.info(f"🔒 Simulated long press: ({x:.3f}, {y:.3f}) duration={duration}s")
    
    def run_ui_test_pattern(self, pattern_name: str) -> None:
        """
        Run a predefined UI test pattern.
        
        Args:
            pattern_name: Name of the test pattern to run
        """
        patterns = {
            'corners': self._test_corner_taps,
            'center_cross': self._test_center_cross,
            'swipe_all_directions': self._test_swipe_directions,
            'rapid_taps': self._test_rapid_taps,
            'long_press_sequence': self._test_long_press_sequence
        }
        
        if pattern_name not in patterns:
            self.logger.error(f"Unknown test pattern: {pattern_name}")
            available = list(patterns.keys())
            self.logger.info(f"Available patterns: {available}")
            return
        
        self.logger.info(f"🧪 Running UI test pattern: {pattern_name}")
        patterns[pattern_name]()
        self._stats['ui_tests_run'] += 1
    
    def _simulate_touch_sequence(self, sequence: List[Dict]) -> None:
        """Execute a sequence of touch events"""
        for event in sequence:
            time.sleep(event.get('delay', 0))
            self._generate_touch_event(event['x'], event['y'], event['state'])
    
    def _generate_touch_event(self, x: float, y: float, state: bool) -> None:
        """Generate a single touch event"""
        # Clamp coordinates
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        
        # Create event data
        event_data = {
            'x': x,
            'y': y,
            'state': state,
            'timestamp': time.time(),
            'event_type': 'touch_down' if state else 'touch_up'
        }
        
        # Store in history
        self._event_history.append(event_data)
        if len(self._event_history) > self._config['event_history_size']:
            self._event_history.pop(0)
        
        # Call registered callbacks
        for callback in self._callbacks:
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(f"Error in touch callback: {e}")
    
    def _get_swipe_direction(self, x1: float, y1: float, x2: float, y2: float) -> str:
        """Determine swipe direction"""
        dx = x2 - x1
        dy = y2 - y1
        
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"
    
    def _test_corner_taps(self) -> None:
        """Test pattern: tap all four corners"""
        corners = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
        for x, y in corners:
            self.simulate_tap(x, y, 0.2)
            time.sleep(0.3)
    
    def _test_center_cross(self) -> None:
        """Test pattern: tap center and cardinal directions"""
        points = [(0.5, 0.5), (0.5, 0.1), (0.5, 0.9), (0.1, 0.5), (0.9, 0.5)]
        for x, y in points:
            self.simulate_tap(x, y, 0.15)
            time.sleep(0.25)
    
    def _test_swipe_directions(self) -> None:
        """Test pattern: swipe in all four directions"""
        swipes = [
            (0.2, 0.5, 0.8, 0.5),  # Right
            (0.8, 0.5, 0.2, 0.5),  # Left
            (0.5, 0.2, 0.5, 0.8),  # Down
            (0.5, 0.8, 0.5, 0.2)   # Up
        ]
        for start_x, start_y, end_x, end_y in swipes:
            self.simulate_swipe(start_x, start_y, end_x, end_y, 0.4)
            time.sleep(0.5)
    
    def _test_rapid_taps(self) -> None:
        """Test pattern: rapid taps at center"""
        for _ in range(5):
            self.simulate_tap(0.5, 0.5, 0.1)
            time.sleep(0.15)
    
    def _test_long_press_sequence(self) -> None:
        """Test pattern: long presses at different locations"""
        locations = [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)]
        for x, y in locations:
            self.simulate_long_press(x, y, 1.2)
            time.sleep(0.8)
    
    def _start_automated_simulation(self) -> None:
        """Start automated touch simulation thread"""
        def automation_loop():
            patterns = ['corners', 'center_cross', 'swipe_all_directions']
            pattern_index = 0
            
            while self._running:
                if self._config['automated_patterns']:
                    pattern = patterns[pattern_index % len(patterns)]
                    self.run_ui_test_pattern(pattern)
                    pattern_index += 1
                
                time.sleep(5.0)  # Wait between patterns
        
        self._simulation_thread = threading.Thread(target=automation_loop, daemon=True)
        self._simulation_thread.start()
        self.logger.info("🤖 Automated simulation started")
    
    def _print_session_summary(self) -> None:
        """Print development session summary"""
        self.logger.info("📊 Development Session Summary:")
        self.logger.info(f"   Events Generated: {self._stats['events_generated']}")
        self.logger.info(f"   Gestures Simulated: {self._stats['gestures_simulated']}")
        self.logger.info(f"   UI Tests Run: {self._stats['ui_tests_run']}")
        self.logger.info(f"   Session Duration: {self._stats.get('total_runtime', 0):.1f}s")
        self.logger.info(f"   Callbacks Registered: {len(self._callbacks)}")


class HardwareTouchInterface(EnhancedTouchInterface):
    """
    Hardware touch interface with platform-aware module loading.
    
    Automatically detects available hardware and falls back to mock
    implementation on development platforms.
    """
    
    def __init__(self):
        super().__init__()
        
        # Load hardware modules using platform detection
        self._hardware_modules = self._load_hardware_modules()
        self._touch_hardware = None
        self._gpio_module = None
        self._is_hardware_available = False
        
        # Initialize hardware if available
        self._initialize_hardware()
    
    def _load_hardware_modules(self) -> Dict[str, Any]:
        """Load hardware modules using platform detection"""
        if PLATFORM_UTILS_AVAILABLE:
            return get_hardware_modules()
        else:
            # Fallback if platform utils not available
            return {
                'gpio': {'available': False, 'is_real': False},
                'hyperpixel': {'available': False, 'is_real': False}
            }
    
    def _initialize_hardware(self) -> None:
        """Initialize hardware based on available modules"""
        gpio_info = self._hardware_modules.get('gpio', {})
        hyperpixel_info = self._hardware_modules.get('hyperpixel', {})
        
        if gpio_info.get('available') and gpio_info.get('is_real'):
            self._gpio_module = gpio_info['module']
            self.logger.info("Real GPIO module loaded")
        
        if hyperpixel_info.get('available') and hyperpixel_info.get('is_real'):
            self._touch_hardware = hyperpixel_info['module']
            self._is_hardware_available = True
            self.logger.info("Real HyperPixel module loaded")
        
        # Set capabilities based on hardware
        self._capabilities = TouchInterfaceCapabilities(
            supports_multitouch=self._is_hardware_available,
            supports_pressure=False,
            supports_gestures=True,
            supports_simulation=not self._is_hardware_available,
            max_touch_points=5 if self._is_hardware_available else 1,
            resolution=(480, 480),
            platform_specific=self._is_hardware_available
        )
        
        mode = "Hardware" if self._is_hardware_available else "Mock"
        self.logger.info(f"HardwareTouchInterface initialized in {mode} mode")
    
    def start(self) -> None:
        """Start the hardware touch interface"""
        if self._running:
            self.logger.warning("Hardware interface already running")
            return
        
        if self._is_hardware_available:
            self._start_hardware()
        else:
            self._start_mock_mode()
        
        self._running = True
    
    def stop(self) -> None:
        """Stop the hardware touch interface"""
        if not self._running:
            return
        
        if self._is_hardware_available:
            self._stop_hardware()
        
        self._running = False
        self.logger.info("Hardware touch interface stopped")
    
    def register_callback(self, callback: Callable) -> None:
        """Register a touch event callback"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            self.logger.debug(f"Registered hardware touch callback")
    
    def _start_hardware(self) -> None:
        """Start real hardware touch interface"""
        try:
            if self._touch_hardware:
                touch_interface = self._touch_hardware.get_touch()
                touch_interface.setup_callback(self._hardware_callback)
                touch_interface.start()
                self.logger.info("✅ Hardware touch interface started")
        except Exception as e:
            self.logger.error(f"Failed to start hardware interface: {e}")
            self._start_mock_mode()
    
    def _stop_hardware(self) -> None:
        """Stop real hardware touch interface"""
        try:
            if self._touch_hardware:
                touch_interface = self._touch_hardware.get_touch()
                touch_interface.stop()
                self.logger.info("Hardware touch interface stopped")
        except Exception as e:
            self.logger.error(f"Error stopping hardware interface: {e}")
    
    def _start_mock_mode(self) -> None:
        """Start in mock mode for development"""
        self.logger.info("🔧 Starting in development mock mode")
        self.logger.info("   Use TouchInterfaceFactory.create_development() for full simulation")
    
    def _hardware_callback(self, event_data: Any) -> None:
        """Handle hardware touch events"""
        for callback in self._callbacks:
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(f"Error in hardware touch callback: {e}")


class TouchInterfaceFactory:
    """
    Enhanced factory for creating touch interfaces with platform awareness.
    
    Automatically detects the platform and creates the most appropriate
    touch interface with proper fallbacks for development environments.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('TouchInterfaceFactory')
        self._platform_info = self._detect_platform()
    
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect platform capabilities"""
        info = {
            'platform_utils_available': PLATFORM_UTILS_AVAILABLE,
            'is_raspberry_pi': False,
            'gpio_available': False,
            'platform_type': 'unknown'
        }
        
        if PLATFORM_UTILS_AVAILABLE:
            try:
                info.update({
                    'is_raspberry_pi': is_raspberry_pi(),
                    'gpio_available': is_gpio_available(),
                    'platform_type': get_platform_type().name
                })
            except Exception as e:
                self.logger.debug(f"Platform detection error: {e}")
        
        return info
    
    def create_touch_interface(self, 
                             interface_type: Optional[str] = None,
                             config: Optional[Dict] = None) -> EnhancedTouchInterface:
        """
        Create appropriate touch interface based on platform and requirements.
        
        Args:
            interface_type: 'hardware', 'development', or None for auto-detect
            config: Configuration for the interface
            
        Returns:
            EnhancedTouchInterface: Platform-appropriate touch interface
        """
        if interface_type is None:
            interface_type = self._auto_detect_interface_type()
        
        self.logger.info(f"🔧 Creating {interface_type} touch interface")
        
        if interface_type == 'development':
            return DevelopmentTouchInterface(config)
        elif interface_type == 'hardware':
            return HardwareTouchInterface()
        else:
            raise ValueError(f"Unknown interface type: {interface_type}")
    
    def create_development(self, config: Optional[Dict] = None) -> DevelopmentTouchInterface:
        """Create development touch interface with simulation capabilities"""
        return DevelopmentTouchInterface(config)
    
    def create_hardware(self) -> HardwareTouchInterface:
        """Create hardware touch interface with automatic fallback"""
        return HardwareTouchInterface()
    
    def _auto_detect_interface_type(self) -> str:
        """Automatically detect the best interface type for current platform"""
        if self._platform_info['is_raspberry_pi'] and self._platform_info['gpio_available']:
            return 'hardware'
        else:
            return 'development'
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform detection information"""
        return dict(self._platform_info)
    
    def get_available_interfaces(self) -> List[Dict[str, Any]]:
        """Get list of available touch interfaces"""
        interfaces = []
        
        # Development interface (always available)
        interfaces.append({
            'name': 'DevelopmentTouchInterface',
            'type': 'Mock/Simulation',
            'platform_support': 'All Platforms',
            'capabilities': [
                'Touch simulation',
                'UI testing patterns',
                'Gesture recognition',
                'Development feedback'
            ],
            'recommended_for': 'Development and testing'
        })
        
        # Hardware interface
        hardware_status = 'Available' if self._platform_info['is_raspberry_pi'] else 'Available (Mock fallback)'
        interfaces.append({
            'name': 'HardwareTouchInterface',
            'type': 'Hardware/Hybrid',
            'platform_support': 'Raspberry Pi (Hardware) + Development Platforms (Mock)',
            'capabilities': [
                'Real hardware support',
                'Automatic mock fallback',
                'Platform detection',
                'Touch event processing'
            ],
            'recommended_for': 'Production and development',
            'status': hardware_status
        })
        
        return interfaces


# Convenience function for easy interface creation
def create_touch_interface(interface_type: Optional[str] = None, 
                         config: Optional[Dict] = None) -> EnhancedTouchInterface:
    """
    Convenience function to create a touch interface.
    
    Args:
        interface_type: 'hardware', 'development', or None for auto-detect
        config: Configuration for the interface
        
    Returns:
        EnhancedTouchInterface: Platform-appropriate touch interface
    """
    factory = TouchInterfaceFactory()
    return factory.create_touch_interface(interface_type, config)