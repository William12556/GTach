#!/usr/bin/env python3
"""
Display Component Coordinator - Manages interactions between display components.
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass

from ..rendering import DisplayRenderingEngine, RenderTarget
from ..input import TouchEventCoordinator, TouchAction, GestureType
from ..performance import PerformanceMonitor

@dataclass
class ComponentStats:
    """Statistics for component coordination"""
    total_frames_coordinated: int = 0
    touch_events_processed: int = 0
    performance_updates: int = 0
    errors_encountered: int = 0
    last_update_time: float = 0.0

class DisplayComponentCoordinator:
    """
    Coordinates interactions between display system components.
    
    Manages component lifecycle, inter-component communication,
    and provides unified interface for component operations.
    """
    
    def __init__(self, rendering_engine: DisplayRenderingEngine,
                 touch_coordinator: TouchEventCoordinator,
                 performance_monitor: PerformanceMonitor):
        self.logger = logging.getLogger('DisplayComponentCoordinator')
        self._lock = threading.RLock()
        
        # Components
        self.rendering_engine = rendering_engine
        self.touch_coordinator = touch_coordinator
        self.performance_monitor = performance_monitor
        
        # Statistics
        self._stats = ComponentStats()
        
        # Component state
        self._initialized = False
        self._running = False
        
        # Event callbacks
        self._touch_callbacks: Dict[TouchAction, List[Callable]] = {}
        self._performance_callbacks: List[Callable] = []
        
        # Initialize coordination
        self._initialize_coordination()
    
    def _initialize_coordination(self) -> None:
        """Initialize coordination between components"""
        try:
            # Set up touch gesture callbacks that integrate with performance monitoring
            self.touch_coordinator.register_gesture_callback(
                GestureType.TAP, self._handle_tap_with_performance
            )
            self.touch_coordinator.register_gesture_callback(
                GestureType.DRAG, self._handle_drag_with_performance
            )
            
            self._initialized = True
            self.logger.info("Component coordination initialized")
            
        except Exception as e:
            self.logger.error(f"Coordination initialization failed: {e}")
            self._initialized = False
    
    def _handle_tap_with_performance(self, start_pos, end_pos) -> TouchAction:
        """Handle tap gesture with performance monitoring"""
        try:
            start_time = time.time()
            
            # Process tap through touch coordinator
            action = TouchAction.BUTTON_PRESS  # Default tap action
            
            # Record performance
            duration = time.time() - start_time
            self.performance_monitor.record_render_operation("tap_processing", duration)
            
            self._stats.touch_events_processed += 1
            
            return action
            
        except Exception as e:
            self.logger.error(f"Tap handling error: {e}")
            self._stats.errors_encountered += 1
            return TouchAction.NONE
    
    def _handle_drag_with_performance(self, start_pos, end_pos) -> TouchAction:
        """Handle drag gesture with performance monitoring"""
        try:
            start_time = time.time()
            
            # Process drag through touch coordinator
            action = TouchAction.DRAG
            
            # Record performance
            duration = time.time() - start_time
            self.performance_monitor.record_render_operation("drag_processing", duration)
            
            self._stats.touch_events_processed += 1
            
            return action
            
        except Exception as e:
            self.logger.error(f"Drag handling error: {e}")
            self._stats.errors_encountered += 1
            return TouchAction.NONE
    
    def start_coordination(self) -> bool:
        """Start component coordination"""
        with self._lock:
            try:
                if not self._initialized:
                    self.logger.error("Cannot start coordination - not initialized")
                    return False
                
                if self._running:
                    self.logger.warning("Coordination already running")
                    return True
                
                # Verify all components are ready
                if not self._verify_component_readiness():
                    self.logger.error("Components not ready for coordination")
                    return False
                
                self._running = True
                self.logger.info("Component coordination started")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start coordination: {e}")
                return False
    
    def stop_coordination(self) -> None:
        """Stop component coordination"""
        with self._lock:
            try:
                if not self._running:
                    return
                
                self._running = False
                
                # Clean up resources
                self._touch_callbacks.clear()
                self._performance_callbacks.clear()
                
                self.logger.info("Component coordination stopped")
                
            except Exception as e:
                self.logger.error(f"Error stopping coordination: {e}")
    
    def _verify_component_readiness(self) -> bool:
        """Verify all components are ready for coordination"""
        try:
            # Check rendering engine
            if not self.rendering_engine.is_initialized():
                self.logger.error("Rendering engine not initialized")
                return False
            
            # Check performance monitor
            if not self.performance_monitor._monitoring:
                self.logger.error("Performance monitor not running")
                return False
            
            # Touch coordinator is always ready if created
            return True
            
        except Exception as e:
            self.logger.error(f"Component readiness check failed: {e}")
            return False
    
    def coordinate_frame_rendering(self, render_callback: Callable) -> bool:
        """
        Coordinate a complete frame rendering cycle.
        
        Args:
            render_callback: Function to call for actual rendering
            
        Returns:
            bool: True if frame rendered successfully
        """
        with self._lock:
            try:
                if not self._running:
                    return False
                
                # Start frame performance tracking
                frame_id = self.performance_monitor.record_frame_start()
                
                # Clear back buffer
                self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
                
                # Execute rendering callback
                render_success = render_callback()
                
                if render_success:
                    # Swap buffers
                    self.rendering_engine.swap_buffers()
                    
                    # Write to framebuffer
                    write_success = self.rendering_engine.write_to_framebuffer()
                    
                    if write_success:
                        # Record successful frame
                        self.performance_monitor.record_frame_end(frame_id)
                        self._stats.total_frames_coordinated += 1
                        return True
                
                # Record failed frame
                self._stats.errors_encountered += 1
                return False
                
            except Exception as e:
                self.logger.error(f"Frame coordination error: {e}")
                self._stats.errors_encountered += 1
                return False
    
    def coordinate_touch_event(self, pos, event_type: str = "down") -> Optional[TouchAction]:
        """
        Coordinate touch event processing.
        
        Args:
            pos: Touch position
            event_type: Type of touch event (down, move, up)
            
        Returns:
            TouchAction or None
        """
        with self._lock:
            try:
                if not self._running:
                    return None
                
                # Record performance start
                start_time = time.time()
                
                # Route to appropriate touch handler
                action = None
                if event_type == "down":
                    action = self.touch_coordinator.handle_touch_down(pos)
                elif event_type == "move":
                    action = self.touch_coordinator.handle_touch_move(pos)
                elif event_type == "up":
                    action = self.touch_coordinator.handle_touch_up(pos)
                
                # Record performance
                duration = time.time() - start_time
                self.performance_monitor.record_render_operation(f"touch_{event_type}", duration)
                
                # Execute registered callbacks
                if action and action in self._touch_callbacks:
                    for callback in self._touch_callbacks[action]:
                        try:
                            callback(pos, action)
                        except Exception as e:
                            self.logger.error(f"Touch callback error: {e}")
                
                self._stats.touch_events_processed += 1
                return action
                
            except Exception as e:
                self.logger.error(f"Touch coordination error: {e}")
                self._stats.errors_encountered += 1
                return None
    
    def register_touch_callback(self, action: TouchAction, callback: Callable) -> None:
        """Register callback for touch actions"""
        try:
            if action not in self._touch_callbacks:
                self._touch_callbacks[action] = []
            self._touch_callbacks[action].append(callback)
            
        except Exception as e:
            self.logger.error(f"Touch callback registration error: {e}")
    
    def register_performance_callback(self, callback: Callable) -> None:
        """Register callback for performance updates"""
        try:
            self._performance_callbacks.append(callback)
            
        except Exception as e:
            self.logger.error(f"Performance callback registration error: {e}")
    
    def get_unified_stats(self) -> Dict[str, Any]:
        """Get unified statistics from all components"""
        try:
            return {
                'coordinator_stats': {
                    'total_frames_coordinated': self._stats.total_frames_coordinated,
                    'touch_events_processed': self._stats.touch_events_processed,
                    'performance_updates': self._stats.performance_updates,
                    'errors_encountered': self._stats.errors_encountered,
                    'last_update_time': self._stats.last_update_time
                },
                'rendering_stats': self.rendering_engine.get_stats(),
                'touch_stats': self.touch_coordinator.get_stats(),
                'performance_metrics': self.performance_monitor.get_current_metrics().to_dict(),
                'component_health': self.check_component_health()
            }
            
        except Exception as e:
            self.logger.error(f"Stats collection error: {e}")
            return {'error': str(e)}
    
    def check_component_health(self) -> Dict[str, bool]:
        """Check health status of all components"""
        try:
            return {
                'rendering_engine': self.rendering_engine.is_initialized(),
                'touch_coordinator': True,  # Always healthy if created
                'performance_monitor': self.performance_monitor._monitoring,
                'coordination_running': self._running,
                'overall_healthy': (
                    self.rendering_engine.is_initialized() and
                    self.performance_monitor._monitoring and
                    self._running
                )
            }
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return {'error': str(e), 'overall_healthy': False}
    
    def update_performance_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """Update performance monitoring thresholds"""
        try:
            # Update performance monitor thresholds
            for key, value in thresholds.items():
                if hasattr(self.performance_monitor.thresholds, key):
                    self.performance_monitor.thresholds[key] = value
            
            self._stats.performance_updates += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Performance threshold update error: {e}")
            return False
    
    def optimize_for_platform(self, platform: str) -> None:
        """Optimize component settings for specific platform"""
        try:
            if platform.lower() == 'raspberry_pi':
                # Conservative settings for Pi
                self.performance_monitor.set_target_fps(30)
                self.performance_monitor.thresholds['max_memory_mb'] = 50.0
                
            elif platform.lower() == 'mac':
                # Higher performance settings for Mac
                self.performance_monitor.set_target_fps(60)
                self.performance_monitor.thresholds['max_memory_mb'] = 200.0
            
            self.logger.info(f"Optimized components for {platform}")
            
        except Exception as e:
            self.logger.error(f"Platform optimization error: {e}")
    
    def is_running(self) -> bool:
        """Check if coordination is running"""
        return self._running
    
    def is_healthy(self) -> bool:
        """Check if all components are healthy"""
        health = self.check_component_health()
        return health.get('overall_healthy', False)