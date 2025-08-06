#!/usr/bin/env python3
"""
Navigation gesture handling for OBDII display application.
Provides comprehensive gesture-based navigation with minimal visual indicators.
"""

import logging
import threading
import time
import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List, Callable

# Import display components
from .models import DisplayMode
from .setup_models import SetupScreen

class GestureType(Enum):
    """Types of navigation gestures"""
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()
    SWIPE_UP = auto()
    SWIPE_DOWN = auto()
    EDGE_SWIPE_LEFT = auto()
    EDGE_SWIPE_RIGHT = auto()

class GestureDirection(Enum):
    """Direction of gesture for navigation"""
    HORIZONTAL = auto()
    VERTICAL = auto()

@dataclass
class GestureConfig:
    """Configuration for gesture recognition"""
    swipe_threshold: int = 80          # Minimum distance for swipe (px)
    velocity_threshold: float = 200.0  # Minimum velocity (px/s)
    edge_width: int = 40              # Edge detection width (px)
    max_gesture_time: float = 1.0     # Maximum gesture duration (s)
    edge_indicator_timeout: float = 5.0  # Edge indicator auto-hide (s)
    
    # Screen-specific gesture enables
    enable_main_navigation: bool = True
    enable_setup_navigation: bool = True
    enable_settings_gestures: bool = True
    
    # Debug visualization
    debug_mode: bool = False

@dataclass
class GestureEvent:
    """Represents a detected navigation gesture"""
    gesture_type: GestureType
    start_pos: Tuple[int, int]
    end_pos: Tuple[int, int]
    duration: float
    velocity: float
    timestamp: float

class NavigationGestureHandler:
    """
    Handles gesture-based navigation with minimal visual indicators.
    
    Features:
    - Horizontal/vertical swipe detection with velocity tracking
    - Edge-based navigation indicators
    - Screen-specific gesture logic
    - Conflict resolution with existing touch controls
    - Thread-safe gesture state management
    """
    
    def __init__(self, display_manager, config: Optional[GestureConfig] = None):
        """
        Initialize navigation gesture handler.
        
        Args:
            display_manager: Display manager instance
            config: Gesture configuration (uses defaults if None)
        """
        self.logger = logging.getLogger('NavigationGestureHandler')
        self.display_manager = display_manager
        self.config = config or GestureConfig()
        
        # Gesture state management (thread-safe)
        self._gesture_lock = threading.Lock()
        self._active_gesture = None
        self._gesture_start_time = None
        self._gesture_start_pos = None
        self._gesture_in_progress = False
        
        # Edge indicator state
        self._edge_indicators_visible = False
        self._last_edge_interaction = 0.0
        self._edge_indicator_lock = threading.Lock()
        
        # Navigation action callbacks
        self._navigation_callbacks: Dict[str, Callable] = {}
        
        # Initialize navigation logic
        self._setup_navigation_callbacks()
        
        self.logger.info("Navigation gesture handler initialized")
        
    def _setup_navigation_callbacks(self) -> None:
        """Setup navigation action callbacks for different screens."""
        self._navigation_callbacks = {
            # Main display mode navigation
            'main_left': lambda: self._change_display_mode(DisplayMode.DIGITAL),
            'main_right': lambda: self._change_display_mode(DisplayMode.GAUGE),
            'main_up': lambda: self._show_edge_feedback("No upward navigation available"),
            'main_down': lambda: self._handle_main_down_swipe(),
            
            # Setup mode navigation  
            'setup_left': lambda: self._handle_setup_back(),
            'setup_right': lambda: self._handle_setup_forward(),
            'setup_up': lambda: self._handle_setup_scroll_up(),
            'setup_down': lambda: self._handle_setup_scroll_down(),
            
            # Settings navigation
            'settings_any_edge': lambda: self._exit_settings(),
            
            # Edge swipes for quick access
            'edge_left': lambda: self._handle_edge_navigation('left'),
            'edge_right': lambda: self._handle_edge_navigation('right'),
        }
    
    def detect_gesture(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                      duration: float, timestamp: float) -> Optional[GestureEvent]:
        """
        Detect and classify navigation gestures.
        
        Args:
            start_pos: Starting touch position (x, y)
            end_pos: Ending touch position (x, y)
            duration: Gesture duration in seconds
            timestamp: Gesture timestamp
            
        Returns:
            GestureEvent if gesture detected, None otherwise
        """
        try:
            with self._gesture_lock:
                # Calculate gesture metrics
                dx = end_pos[0] - start_pos[0]
                dy = end_pos[1] - start_pos[1]
                distance = math.sqrt(dx**2 + dy**2)
                velocity = distance / duration if duration > 0 else 0
                
                # Check if meets minimum requirements
                if distance < self.config.swipe_threshold:
                    self.logger.debug(f"Gesture too short: {distance}px < {self.config.swipe_threshold}px")
                    return None
                    
                if velocity < self.config.velocity_threshold:
                    self.logger.debug(f"Gesture too slow: {velocity:.1f}px/s < {self.config.velocity_threshold}px/s")
                    return None
                    
                if duration > self.config.max_gesture_time:
                    self.logger.debug(f"Gesture too long: {duration:.2f}s > {self.config.max_gesture_time}s")
                    return None
                
                # Determine gesture type based on direction and edge proximity
                gesture_type = self._classify_gesture(start_pos, end_pos, dx, dy)
                
                if gesture_type:
                    gesture_event = GestureEvent(
                        gesture_type=gesture_type,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        duration=duration,
                        velocity=velocity,
                        timestamp=timestamp
                    )
                    
                    self.logger.info(f"Gesture detected: {gesture_type.name} "
                                   f"({start_pos} → {end_pos}, {velocity:.1f}px/s)")
                    
                    return gesture_event
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error detecting gesture: {e}")
            return None
    
    def _classify_gesture(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                         dx: int, dy: int) -> Optional[GestureType]:
        """Classify gesture based on direction and edge proximity."""
        
        # Check for edge gestures first
        edge_width = self.config.edge_width
        display_width = 480  # HyperPixel 2" Round
        
        start_near_left_edge = start_pos[0] < edge_width
        start_near_right_edge = start_pos[0] > (display_width - edge_width)
        
        # Determine primary direction
        is_horizontal = abs(dx) > abs(dy)
        
        if is_horizontal:
            if start_near_left_edge and dx > 0:
                return GestureType.EDGE_SWIPE_LEFT
            elif start_near_right_edge and dx < 0:
                return GestureType.EDGE_SWIPE_RIGHT
            elif dx > 0:
                return GestureType.SWIPE_RIGHT
            else:
                return GestureType.SWIPE_LEFT
        else:
            if dy > 0:
                return GestureType.SWIPE_DOWN
            else:
                return GestureType.SWIPE_UP
    
    def handle_gesture_event(self, gesture: GestureEvent) -> bool:
        """
        Handle detected gesture based on current screen context.
        
        Args:
            gesture: Detected gesture event
            
        Returns:
            bool: True if gesture was handled, False otherwise
        """
        try:
            # Check if gestures are enabled for current context
            if not self._is_gesture_enabled():
                self.logger.debug("Gestures disabled for current context")
                return False
            
            # Get current context for navigation logic
            context = self._get_navigation_context()
            
            # Route gesture to appropriate handler
            action_key = self._get_action_key(context, gesture.gesture_type)
            
            if action_key in self._navigation_callbacks:
                self.logger.info(f"Executing navigation action: {action_key}")
                self._navigation_callbacks[action_key]()
                
                # Show visual feedback
                self._show_gesture_feedback(gesture)
                
                return True
            else:
                self.logger.debug(f"No action mapped for {action_key}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error handling gesture: {e}")
            return False
    
    def _is_gesture_enabled(self) -> bool:
        """Check if gestures are enabled for current context."""
        try:
            if self.display_manager.is_in_setup_mode():
                return self.config.enable_setup_navigation
            elif self.display_manager.config.mode == DisplayMode.SETTINGS:
                return self.config.enable_settings_gestures
            else:
                return self.config.enable_main_navigation
                
        except Exception as e:
            self.logger.error(f"Error checking gesture enable state: {e}")
            return False
    
    def _get_navigation_context(self) -> str:
        """Get current navigation context."""
        try:
            if self.display_manager.is_in_setup_mode():
                return "setup"
            elif self.display_manager.config.mode == DisplayMode.SETTINGS:
                return "settings"
            else:
                return "main"
                
        except Exception as e:
            self.logger.error(f"Error getting navigation context: {e}")
            return "main"
    
    def _get_action_key(self, context: str, gesture_type: GestureType) -> str:
        """Generate action key for gesture routing."""
        
        if gesture_type == GestureType.EDGE_SWIPE_LEFT:
            return "edge_left"
        elif gesture_type == GestureType.EDGE_SWIPE_RIGHT:
            return "edge_right"
        elif context == "settings":
            return "settings_any_edge"
        else:
            direction_map = {
                GestureType.SWIPE_LEFT: "left",
                GestureType.SWIPE_RIGHT: "right", 
                GestureType.SWIPE_UP: "up",
                GestureType.SWIPE_DOWN: "down"
            }
            direction = direction_map.get(gesture_type, "unknown")
            return f"{context}_{direction}"
    
    def start_gesture_tracking(self, pos: Tuple[int, int], timestamp: float) -> None:
        """Start tracking a potential gesture."""
        try:
            with self._gesture_lock:
                self._gesture_in_progress = True
                self._gesture_start_time = timestamp
                self._gesture_start_pos = pos
                
                # Show edge indicators if near edge
                self._update_edge_indicators(pos)
                
        except Exception as e:
            self.logger.error(f"Error starting gesture tracking: {e}")
    
    def end_gesture_tracking(self, pos: Tuple[int, int], timestamp: float) -> Optional[GestureEvent]:
        """End gesture tracking and detect completed gesture."""
        try:
            with self._gesture_lock:
                if not self._gesture_in_progress or not self._gesture_start_time:
                    return None
                
                duration = timestamp - self._gesture_start_time
                gesture = self.detect_gesture(self._gesture_start_pos, pos, duration, timestamp)
                
                # Reset gesture state
                self._gesture_in_progress = False
                self._gesture_start_time = None
                self._gesture_start_pos = None
                
                return gesture
                
        except Exception as e:
            self.logger.error(f"Error ending gesture tracking: {e}")
            return None
    
    def cancel_gesture(self) -> None:
        """Cancel current gesture tracking."""
        try:
            with self._gesture_lock:
                self._gesture_in_progress = False
                self._gesture_start_time = None
                self._gesture_start_pos = None
                self.logger.debug("Gesture tracking cancelled")
                
        except Exception as e:
            self.logger.error(f"Error cancelling gesture: {e}")
    
    def _update_edge_indicators(self, pos: Tuple[int, int]) -> None:
        """Update edge indicator visibility based on touch position."""
        try:
            with self._edge_indicator_lock:
                x, y = pos
                edge_width = self.config.edge_width
                
                # Check if near screen edges
                near_edge = (x < edge_width or x > (480 - edge_width))
                
                if near_edge:
                    self._edge_indicators_visible = True
                    self._last_edge_interaction = time.time()
                    
        except Exception as e:
            self.logger.error(f"Error updating edge indicators: {e}")
    
    def should_show_edge_indicators(self) -> bool:
        """Check if edge indicators should be visible."""
        try:
            with self._edge_indicator_lock:
                if not self._edge_indicators_visible:
                    return False
                
                elapsed = time.time() - self._last_edge_interaction
                if elapsed > self.config.edge_indicator_timeout:
                    self._edge_indicators_visible = False
                    return False
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking edge indicator visibility: {e}")
            return False
    
    def get_edge_indicator_alpha(self) -> int:
        """Get current alpha value for edge indicators based on interaction."""
        try:
            if not self.should_show_edge_indicators():
                return 0
            
            # Fade from 60% to 30% based on time since interaction
            elapsed = time.time() - self._last_edge_interaction
            fade_duration = 2.0  # Fade over 2 seconds
            
            if elapsed < fade_duration:
                # Interpolate from 60% to 30%
                alpha_factor = 1.0 - (elapsed / fade_duration * 0.5)
                return int(255 * 0.3 * alpha_factor + 255 * 0.3)
            else:
                return int(255 * 0.3)  # 30% opacity
                
        except Exception as e:
            self.logger.error(f"Error calculating edge indicator alpha: {e}")
            return 0
    
    # Navigation action implementations
    
    def _change_display_mode(self, mode: DisplayMode) -> None:
        """Change main display mode with smooth transition."""
        try:
            if hasattr(self.display_manager, 'transition_to_mode'):
                self.display_manager.transition_to_mode(mode, "slide")
            else:
                self.display_manager.change_mode(mode)
            self.logger.info(f"Display mode changed to {mode.name}")
        except Exception as e:
            self.logger.error(f"Error changing display mode: {e}")
    
    def _handle_main_down_swipe(self) -> None:
        """Handle down swipe in main display."""
        # Could enter settings or show quick actions
        self.logger.info("Main down swipe - showing quick actions")
        self._show_edge_feedback("Quick actions (future feature)")
    
    def _handle_setup_back(self) -> None:
        """Handle back navigation in setup mode."""
        try:
            if hasattr(self.display_manager, '_setup_manager') and self.display_manager._setup_manager:
                # Simulate back action
                self.display_manager._setup_manager.handle_touch_event((50, 400))  # Back button area
                self.logger.info("Setup back navigation triggered")
        except Exception as e:
            self.logger.error(f"Error handling setup back: {e}")
    
    def _handle_setup_forward(self) -> None:
        """Handle forward navigation in setup mode."""
        self.logger.info("Setup forward navigation (context-dependent)")
        self._show_edge_feedback("Forward navigation")
    
    def _handle_setup_scroll_up(self) -> None:
        """Handle scroll up in setup mode."""
        self.logger.info("Setup scroll up")
        self._show_edge_feedback("Scroll up")
    
    def _handle_setup_scroll_down(self) -> None:
        """Handle scroll down in setup mode."""
        self.logger.info("Setup scroll down") 
        self._show_edge_feedback("Scroll down")
    
    def _exit_settings(self) -> None:
        """Exit settings mode."""
        try:
            self.display_manager.change_mode(DisplayMode.DIGITAL)
            self.logger.info("Exited settings via gesture")
        except Exception as e:
            self.logger.error(f"Error exiting settings: {e}")
    
    def _handle_edge_navigation(self, direction: str) -> None:
        """Handle edge swipe navigation."""
        self.logger.info(f"Edge navigation: {direction}")
        self._show_edge_feedback(f"Edge swipe {direction}")
    
    def _show_gesture_feedback(self, gesture: GestureEvent) -> None:
        """Show visual feedback for completed gesture."""
        try:
            self.logger.debug(f"Showing feedback for {gesture.gesture_type.name}")
            
            # Add visual feedback through display manager
            if hasattr(self.display_manager, 'add_gesture_visual_feedback'):
                self.display_manager.add_gesture_visual_feedback(
                    gesture.gesture_type.name.lower(),
                    gesture.start_pos,
                    gesture.end_pos
                )
        except Exception as e:
            self.logger.error(f"Error showing gesture feedback: {e}")
    
    def _show_edge_feedback(self, message: str) -> None:
        """Show temporary feedback message."""
        self.logger.info(f"Edge feedback: {message}")
    
    def get_gesture_debug_info(self) -> Dict:
        """Get debug information about gesture state."""
        try:
            with self._gesture_lock:
                return {
                    'gesture_in_progress': self._gesture_in_progress,
                    'gesture_start_time': self._gesture_start_time,
                    'gesture_start_pos': self._gesture_start_pos,
                    'edge_indicators_visible': self._edge_indicators_visible,
                    'last_edge_interaction': self._last_edge_interaction,
                    'config': {
                        'swipe_threshold': self.config.swipe_threshold,
                        'velocity_threshold': self.config.velocity_threshold,
                        'edge_width': self.config.edge_width,
                        'debug_mode': self.config.debug_mode
                    }
                }
        except Exception as e:
            self.logger.error(f"Error getting debug info: {e}")
            return {'error': str(e)}