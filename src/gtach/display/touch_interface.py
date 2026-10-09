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
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional

# Cross-platform compatibility imports with mock objects for development
_HYPERPIXEL_AVAILABLE = False
_RPI_AVAILABLE = False

# Try to import RPi.GPIO for Raspberry Pi hardware detection
try:
    import RPi.GPIO as GPIO  # noqa: F401 — availability probe only

    _RPI_AVAILABLE = True
except ImportError:
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
        timestamp: Event timestamp, time.monotonic() seconds (issue-4005360c)
    """

    event_type: TouchEventType
    x: float
    y: float
    timestamp: float = 0.0

    def __post_init__(self):
        """Initialize timestamp if not provided"""
        if self.timestamp == 0.0:
            self.timestamp = time.monotonic()

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
        # Capture under the lock, call after releasing it (CLAUDE.md §4
        # rule 8, issue-fbe7e98a).
        with self._lock:
            callback = self._callback
        if callback:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in touch callback: {e}", exc_info=True)
        else:
            self.logger.debug(
                f"Touch event {event.event_type.name} at ({event.x:.3f}, "
                f"{event.y:.3f}) - no callback registered"
            )

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
            "class": self.__class__.__name__,
            "running": self._running,
            "has_callback": self._callback is not None,
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
        self.logger = logging.getLogger("MockHyperPixelTouch")

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
        self.logger.info(
            f"Platform detection: RPi={'✅' if self._rpi_available else '❌'}, "
            f"HyperPixel={'✅' if _HYPERPIXEL_AVAILABLE else '❌'}"
        )

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
                self._mock_fallback_log()(
                    "Falling back to mock implementation for development"
                )

        # Fall back to mock implementation
        try:
            self._start_mock_implementation()
        except Exception as e:
            self.logger.error(
                f"Failed to start both real and mock implementations: {e}",
                exc_info=True,
            )
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
                    event_type = (
                        TouchEventType.TOUCH_DOWN if state else TouchEventType.TOUCH_UP
                    )

                    # Create and emit touch event
                    event = TouchEvent(event_type, norm_x, norm_y)
                    self.logger.debug(
                        f"Real touch event: {event_type.name} at ({norm_x:.3f}, "
                        f"{norm_y:.3f})"
                    )
                    self._emit_touch_event(event)

                except Exception as e:
                    self.logger.error(
                        f"Error handling real HyperPixel touch event: {e}",
                        exc_info=True,
                    )

            self._running = True
            self._using_mock = False
            self.logger.info("✅ Real HyperPixel touch interface started successfully")

        except ImportError as e:
            self.logger.error(f"HyperPixel2R import failed (missing dependencies): {e}")
            raise RuntimeError(f"HyperPixel2R library dependencies not available: {e}")
        except Exception as e:
            self.logger.error(
                f"Real HyperPixel hardware initialization failed: {e}", exc_info=True
            )
            raise RuntimeError(f"Real HyperPixel hardware startup failed: {e}")

    def _mock_fallback_log(self):
        """Logger method for the mock-fallback messages.

        On a Raspberry Pi the mock means touch input is dead, so it is
        reported at ERROR; elsewhere it is expected and stays at INFO.
        Detection failure falls back to INFO (issue-52653cd6).
        """
        try:
            from ..utils.platform import is_raspberry_pi

            on_pi = is_raspberry_pi()
        except Exception:
            on_pi = False
        return self.logger.error if on_pi else self.logger.info

    def _start_mock_implementation(self) -> None:
        """Start the mock implementation for development"""
        try:
            # Use mock touch device
            self._touch_device = MockHyperPixelTouch()
            self._hyperpixel_available = True  # Mock is "available"
            self._using_mock = True
            self._development_mode = True

            self._mock_fallback_log()(
                "🖥️  Using mock HyperPixel implementation for development"
            )

            # Set up touch event handler for mock device
            @self._touch_device.on_touch
            def handle_mock_touch(touch_id: int, x: int, y: int, state: bool):
                """Handle mock touch events"""
                try:
                    # Convert pixel coordinates to normalized coordinates
                    norm_x = max(0.0, min(1.0, x / 480.0))
                    norm_y = max(0.0, min(1.0, y / 480.0))

                    # Determine event type
                    event_type = (
                        TouchEventType.TOUCH_DOWN if state else TouchEventType.TOUCH_UP
                    )

                    # Create and emit touch event
                    event = TouchEvent(event_type, norm_x, norm_y)
                    self.logger.debug(
                        f"Mock touch event: {event_type.name} at ({norm_x:.3f}, "
                        f"{norm_y:.3f})"
                    )
                    self._emit_touch_event(event)

                except Exception as e:
                    self.logger.error(
                        f"Error handling mock HyperPixel touch event: {e}",
                        exc_info=True,
                    )

            # Start the mock device
            self._touch_device.start()

            self._running = True
            self.logger.info("✅ Mock HyperPixel touch interface started successfully")

        except Exception as e:
            self.logger.error(f"Mock implementation startup failed: {e}", exc_info=True)
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
                if self._using_mock and hasattr(self._touch_device, "stop"):
                    self._touch_device.stop()
                self._touch_device = None

            implementation = "mock" if self._using_mock else "real"
            self.logger.info(
                f"✅ HyperPixel touch interface ({implementation}) stopped"
            )

        except Exception as e:
            self.logger.error(
                f"Error stopping HyperPixel touch interface: {e}", exc_info=True
            )

    def get_info(self) -> dict:
        """Get HyperPixel-specific interface information"""
        info = super().get_info()
        info.update(
            {
                "hyperpixel_available": self._hyperpixel_available,
                "rpi_available": self._rpi_available,
                "using_mock": self._using_mock,
                "development_mode": self._development_mode,
                "device_initialized": self._touch_device is not None,
                "platform_detected": (
                    "Raspberry Pi" if self._rpi_available else "Development Platform"
                ),
                "implementation": "Mock" if self._using_mock else "Real Hardware",
            }
        )
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
            "enable_detailed_logging": True,
            "simulation_delay": 0.05,  # Delay between touch down/up in seconds
            "auto_feedback": True,  # Provide feedback for all operations
            "log_coordinates": True,  # Log coordinate information
            "simulate_pressure": False,  # Future: pressure simulation
            "gesture_recognition": True,  # Log gesture patterns
            "event_history_size": 100,  # Number of events to keep in history
        }

        # Update config with user provided options
        if config:
            self._config.update(config)

        # Event history for development debugging
        self._event_history = []

        # Touch statistics for development insights
        self._stats = {
            "total_events": 0,
            "touch_downs": 0,
            "touch_ups": 0,
            "touch_moves": 0,
            "simulated_taps": 0,
            "gestures_detected": 0,
        }

        if self._config["enable_detailed_logging"]:
            self.logger.info("MockTouchInterface initialized with development support")
            self.logger.debug(f"Configuration: {self._config}")

    def start(self) -> None:
        """Start the mock touch interface with development feedback"""
        if self._running:
            self.logger.warning("Mock touch interface already running")
            return

        self._running = True
        self._simulation_running = True

        if self._config["auto_feedback"]:
            self.logger.info(
                "🖱️  Mock touch interface started - Touch simulation available"
            )
            self.logger.info("📝 Development mode: All touch events will be logged")

    def stop(self) -> None:
        """Stop the mock touch interface with cleanup"""
        if not self._running:
            self.logger.warning("Mock touch interface not running")
            return

        self._running = False
        self._simulation_running = False
        self._simulated_events.clear()

        if self._config["auto_feedback"]:
            self.logger.info("Mock touch interface stopped")
            self._print_session_stats()

    def get_info(self) -> dict:
        """Get mock interface information (legacy compatibility)"""
        info = super().get_info()
        info.update(
            {
                "simulation_enabled": self._simulation_enabled,
                "pending_events": len(self._simulated_events),
                "total_events_processed": self._stats["total_events"],
            }
        )
        return info

    def _print_session_stats(self) -> None:
        """Print session statistics on shutdown"""
        if self._stats["total_events"] > 0:
            self.logger.info("📊 Session Summary:")
            self.logger.info(f"   Total Events: {self._stats['total_events']}")
            self.logger.info(f"   Simulated Taps: {self._stats['simulated_taps']}")
            self.logger.info(f"   Touch Downs: {self._stats['touch_downs']}")
            self.logger.info(f"   Touch Ups: {self._stats['touch_ups']}")
            if self._stats["touch_moves"] > 0:
                self.logger.info(f"   Touch Moves: {self._stats['touch_moves']}")
        else:
            self.logger.info("📊 No touch events simulated during this session")


_touch_interface_singleton: Optional[TouchInterface] = None
_touch_interface_lock = threading.Lock()


def create_touch_interface() -> TouchInterface:
    """
    Factory function to create appropriate touch interface based on platform.

    Returns the same instance on every call (singleton). This ensures all
    callers share one hardware-connected interface and one callback chain.

    Returns:
        TouchInterface: Platform-appropriate touch interface instance

    Raises:
        RuntimeError: If no suitable touch interface can be created
    """
    global _touch_interface_singleton
    with _touch_interface_lock:
        if _touch_interface_singleton is not None:
            return _touch_interface_singleton
    logger = logging.getLogger("TouchInterfaceFactory")

    try:
        # Enhanced platform detection with RPi module availability
        platform_info = {
            "rpi_module_available": _RPI_AVAILABLE,
            "hyperpixel_available": _HYPERPIXEL_AVAILABLE,
            "platform_type": (
                "Raspberry Pi" if _RPI_AVAILABLE else "Development Platform"
            ),
        }

        logger.info("🔍 Platform Analysis:")
        logger.info(f"   RPi Module: {'✅' if _RPI_AVAILABLE else '❌'}")
        logger.info(f"   HyperPixel: {'✅' if _HYPERPIXEL_AVAILABLE else '❌'}")
        logger.info(f"   Platform: {platform_info['platform_type']}")

        # Try to import additional platform detection utilities for enhanced detection
        try:
            from ..utils.platform import (
                get_platform_info,
                is_gpio_available,
                is_raspberry_pi,
            )

            additional_platform_info = get_platform_info()
            is_rpi = is_raspberry_pi()
            gpio_available = is_gpio_available()

            logger.debug(
                f"Additional platform detection: RPi={is_rpi}, GPIO={gpio_available}"
            )

            # Update platform info with additional detection
            platform_info.update(
                {
                    "gpio_available": gpio_available,
                    "platform_confirmed": is_rpi,
                    "additional_info": additional_platform_info,
                }
            )

        except ImportError as e:
            logger.debug(f"Additional platform detection not available: {e}")
            platform_info.update(
                {
                    # Use RPi module availability as fallback
                    "gpio_available": _RPI_AVAILABLE,
                    "platform_confirmed": _RPI_AVAILABLE,
                }
            )

        # Create HyperPixelTouchInterface with cross-platform support
        # It will automatically handle real hardware vs mock implementation
        try:
            logger.info("🔄 Creating cross-platform HyperPixel touch interface...")
            interface = HyperPixelTouchInterface()
            logger.info("✅ HyperPixel touch interface created successfully")
            with _touch_interface_lock:
                _touch_interface_singleton = interface
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
                logger.error(
                    f"Even mock interface creation failed: {fallback_error}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Failed to create any touch interface: {fallback_error}"
                )

    except Exception as e:
        logger.error(f"Critical error in touch interface factory: {e}", exc_info=True)
        # Ultimate fallback - try to create basic mock interface
        try:
            logger.info("🆘 Attempting emergency mock interface creation...")
            return MockTouchInterface()
        except Exception as emergency_error:
            raise RuntimeError(
                f"Complete touch interface factory failure: {emergency_error}"
            )


class TouchInterfaceError(Exception):
    """Exception raised for touch interface specific errors"""

    pass


class TouchInterfaceNotAvailableError(TouchInterfaceError):
    """Exception raised when requested touch interface is not available"""

    pass
