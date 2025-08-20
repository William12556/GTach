#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Setup mode display manager for OBDII display application.
Refactored to use component-based architecture for maintainability.
"""

import logging
import threading
import time
import math
from typing import Optional, List, Tuple, Dict, Any

# Conditional import of pygame
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

from .setup_models import SetupScreen, SetupState, SetupAction, PairingStatus, BluetoothDevice, DeviceType
from .typography import (get_font_manager, get_title_display_font, get_heading_font, get_body_font, 
                         get_button_font, get_label_small_font, get_minimal_font, TypographyConstants,
                         get_button_renderer, render_standard_button, ButtonSize, ButtonState)
from .performance import get_performance_manager
from ..utils import ConfigManager
from .async_operations import get_async_manager, OperationType, OperationStatus

# Import extracted components
from .setup.bluetooth.interface import BluetoothSetupInterface
from .setup.layout.circular_positioning import CircularPositioningEngine
from .setup.rendering.device_surfaces import DeviceSurfaceRenderer
from .setup.state.coordinator import SetupStateCoordinator

class SetupDisplayManager:
    """Manages setup mode display rendering and user interaction
    
    Thread Safety:
        - touch_regions list is protected by _touch_regions_lock
        - Display thread modifies touch_regions during render operations
        - Touch handling thread reads touch_regions during event processing
        - All access to touch_regions must be synchronized using the lock
    """
    
    def __init__(self, surface, thread_manager, touch_handler):
        self.logger = logging.getLogger('SetupDisplayManager')
        self.surface = surface
        self.thread_manager = thread_manager
        self.touch_handler = touch_handler
        
        # Check pygame availability
        if not PYGAME_AVAILABLE:
            self.logger.warning("Pygame not available - setup display will use minimal functionality")
            self.display_available = False
        else:
            self.display_available = True
        
        # Initialize extracted components
        self.bluetooth_interface = BluetoothSetupInterface()
        self.positioning_engine = CircularPositioningEngine()
        self.device_renderer = DeviceSurfaceRenderer()
        self.state_coordinator = SetupStateCoordinator()
        
        # UI state and threading
        self.touch_regions = []  # Protected by _touch_regions_lock
        self._setup_thread = None
        self._shutdown_event = threading.Event()
        self._touch_regions_lock = threading.Lock()
        
        # Render state tracking
        self._screen_render_cache = {}
        self._last_rendered_screen = None
        self._screen_needs_refresh = True
        self._render_cache_lock = threading.Lock()
        
        # Colors for UI rendering
        self.colors = {
            'background': (20, 20, 30),
            'surface': (40, 40, 50),
            'primary': (100, 150, 250),
            'success': (50, 200, 50),
            'warning': (255, 165, 0),
            'danger': (255, 50, 50),
            'text': (255, 255, 255),
            'text_dim': (180, 180, 180),
            'border': (80, 80, 90)
        }
        
        # Register callbacks for component coordination
        self.state_coordinator.register_screen_transition_callback(self._on_screen_transition)
        self.state_coordinator.register_state_change_callback(self._on_state_change)
        
        self.logger.info("SetupDisplayManager initialized with component architecture")
    
    def _on_screen_transition(self, old_screen: SetupScreen, new_screen: SetupScreen) -> None:
        """Handle screen transitions from state coordinator"""
        self._invalidate_render_cache(new_screen)
        self.logger.debug(f"Screen transition handled: {old_screen.name} -> {new_screen.name}")
    
    def _on_state_change(self, changed_fields: List[str]) -> None:
        """Handle state changes from state coordinator"""
        # Invalidate cache for dynamic content changes
        if any(field in changed_fields for field in ['discovered_devices', 'pairing_status', 'selected_device']):
            self._invalidate_render_cache()
        self.logger.debug(f"State change handled: {changed_fields}")
    
    @property
    def state(self) -> SetupState:
        """Get current setup state from coordinator"""
        return self.state_coordinator.get_state()
    
    def _get_active_operation_progress(self) -> dict:
        """Initialize Bluetooth pairing asynchronously to prevent UI blocking"""
        def init_bluetooth_pairing(progress_callback=None):
            """Initialize BluetoothPairing in worker thread"""
            try:
                if progress_callback:
                    progress_callback(0.2, "Creating BluetoothPairing instance...")
                
                # Initialize BluetoothPairing
                pairing = BluetoothPairing()
                
                if progress_callback:
                    progress_callback(0.8, "Testing Bluetooth adapter...")
                
                # Test if Bluetooth is available (non-blocking check)
                try:
                    # This is a quick check that doesn't block
                    adapter_available = hasattr(pairing, 'adapter') and pairing.adapter is not None
                    if progress_callback:
                        progress_callback(1.0, "Bluetooth initialization complete")
                except Exception as e:
                    self.logger.warning(f"Bluetooth adapter check failed: {e}")
                    if progress_callback:
                        progress_callback(1.0, "Bluetooth initialization complete (limited)")
                
                return pairing
                
            except Exception as e:
                self.logger.error(f"Bluetooth pairing initialization failed: {e}")
                if progress_callback:
                    progress_callback(1.0, f"Bluetooth initialization failed: {str(e)}")
                raise
        
        def on_bluetooth_init_complete(operation):
            """Callback when Bluetooth initialization completes"""
            try:
                if operation.status == OperationStatus.COMPLETED:
                    self.pairing = operation.result
                    self._pairing_ready.set()
                    self.logger.info("Bluetooth pairing initialized successfully in background")
                elif operation.status == OperationStatus.FAILED:
                    self.logger.error(f"Bluetooth pairing initialization failed: {operation.error}")
                    # Set a None pairing to indicate failure but allow UI to continue
                    self.pairing = None
                    self._pairing_ready.set()
                else:
                    self.logger.warning(f"Bluetooth pairing initialization ended with status: {operation.status}")
                    self.pairing = None
                    self._pairing_ready.set()
                
                # Remove from active operations
                if 'bluetooth_init' in self._active_operations:
                    del self._active_operations['bluetooth_init']
                    
            except Exception as e:
                self.logger.error(f"Error in bluetooth init callback: {e}")
                self.pairing = None
                self._pairing_ready.set()
        
        # Submit the initialization operation
        try:
            operation_id = self.async_manager.submit_operation(
                OperationType.BLUETOOTH_INIT,
                init_bluetooth_pairing,
                progress_callback=on_bluetooth_init_complete
            )
            
            self._active_operations['bluetooth_init'] = operation_id
            self.logger.info(f"Bluetooth pairing initialization started (operation: {operation_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to submit bluetooth initialization operation: {e}")
            # Fallback to synchronous initialization
            try:
                self.pairing = BluetoothPairing()
                self._pairing_ready.set()
                self.logger.warning("Fallback to synchronous Bluetooth initialization")
            except Exception as fallback_error:
                self.logger.error(f"Synchronous Bluetooth initialization also failed: {fallback_error}")
                self.pairing = None
                self._pairing_ready.set()
    
    def _ensure_pairing_initialized(self) -> bool:
        """Ensure Bluetooth pairing is initialized, waiting if necessary"""
        try:
            # Wait for pairing initialization to complete (with timeout)
            if not self._pairing_ready.wait(timeout=10.0):
                self.logger.error("Timeout waiting for Bluetooth pairing initialization")
                return False
            
            # Check if pairing was successfully initialized
            if self.pairing is None:
                self.logger.error("Bluetooth pairing initialization failed")
                return False
            
            self.logger.debug("Bluetooth pairing ready for use")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring pairing initialization: {e}")
            return False
    
    def _get_active_operation_progress(self) -> dict:
        """Get progress information for active async operations"""
        return self.bluetooth_interface.get_active_operation_progress()
    
    # Performance optimization helper methods
    
    def _get_cached_font(self, size: int, font_path: str = None) -> pygame.font.Font:
        """Get cached font using performance manager, with fallback."""
        try:
            performance_manager = get_performance_manager()
            if performance_manager:
                font = performance_manager.get_font(size, font_path)
                if font:
                    return font
            
            font_manager = get_font_manager()
            return font_manager.get_font(size)
            
        except Exception as e:
            self.logger.warning(f"Error getting cached font: {e}")
            try:
                return pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
            except:
                return pygame.font.Font(None, size)
    
    def _mark_dirty_region(self, rect: pygame.Rect) -> None:
        """Mark a region as dirty for efficient rendering."""
        try:
            performance_manager = get_performance_manager()
            if performance_manager:
                performance_manager.add_dirty_region(rect)
        except Exception as e:
            self.logger.debug(f"Could not mark dirty region: {e}")
    
    # Circular layout utility methods for HyperPixel Round display
    
    def _get_circular_safe_area(self) -> dict:
        """Get circular display geometry constants for safe UI positioning.
        
        Returns:
            dict: Dictionary containing circular display geometry:
                - center: (x, y) tuple of display center
                - safe_radius: Conservative radius for UI elements
                - max_radius: Maximum usable radius
                - size: (width, height) tuple of display dimensions
        
        Thread Safety:
            This method is thread-safe and read-only.
        """
        try:
            geometry = {
                'center': self.display_center,
                'safe_radius': self.display_safe_radius,
                'max_radius': self.display_max_radius,
                'size': self.display_size
            }
            
            self.logger.debug(f"Circular display geometry: {geometry}")
            return geometry
            
        except Exception as e:
            self.logger.error(f"Error getting circular safe area: {e}")
            # Return fallback geometry
            return {
                'center': (240, 240),
                'safe_radius': 200,
                'max_radius': 220,
                'size': (480, 480)
            }
    
    def _position_in_circle(self, angle_degrees: float, radius: float, 
                          element_size: tuple = (100, 30)) -> tuple:
        """Position an element within the circular display using polar coordinates.
        
        Args:
            angle_degrees: Angle in degrees (0 = right, 90 = down, 180 = left, 270 = up)
            radius: Distance from center (0 to safe_radius)
            element_size: (width, height) tuple of element dimensions
            
        Returns:
            tuple: (x, y, width, height) rectangle coordinates for pygame.Rect
            
        Thread Safety:
            This method is thread-safe and performs read-only calculations.
        """
        try:
            # Input validation
            if radius < 0:
                raise ValueError("Radius must be non-negative")
            if radius > self.display_safe_radius:
                self.logger.warning(f"Radius {radius} exceeds safe radius {self.display_safe_radius}")
                radius = self.display_safe_radius
            
            # Convert angle to radians
            angle_radians = math.radians(angle_degrees)
            
            # Calculate position using polar coordinates
            center_x, center_y = self.display_center
            element_width, element_height = element_size
            
            # Position element center at the specified polar coordinates
            element_center_x = center_x + radius * math.cos(angle_radians)
            element_center_y = center_y + radius * math.sin(angle_radians)
            
            # Calculate top-left corner for pygame.Rect
            rect_x = int(element_center_x - element_width / 2)
            rect_y = int(element_center_y - element_height / 2)
            
            # Create rectangle coordinates
            rect_coords = (rect_x, rect_y, element_width, element_height)
            
            self.logger.debug(f"Positioned element: angle={angle_degrees}°, radius={radius}, "
                            f"size={element_size}, result={rect_coords}")
            
            return rect_coords
            
        except Exception as e:
            self.logger.error(f"Error positioning element in circle: {e}")
            # Return fallback position at center
            center_x, center_y = self.display_center
            element_width, element_height = element_size
            return (center_x - element_width // 2, center_y - element_height // 2, 
                   element_width, element_height)
    
    def _validate_circular_bounds(self, rect_coords: tuple) -> dict:
        """Validate if a rectangle fits within the circular display boundary.
        
        Args:
            rect_coords: (x, y, width, height) rectangle coordinates
            
        Returns:
            dict: Validation result containing:
                - valid: bool indicating if rectangle fits in circle
                - center_distance: Distance from display center to rect center
                - corner_distances: List of distances from center to each corner
                - max_corner_distance: Maximum corner distance from center
                - within_safe_area: bool indicating if within safe radius
                - within_max_area: bool indicating if within max radius
                
        Thread Safety:
            This method is thread-safe and performs read-only calculations.
        """
        try:
            x, y, width, height = rect_coords
            center_x, center_y = self.display_center
            
            # Calculate rectangle center
            rect_center_x = x + width / 2
            rect_center_y = y + height / 2
            
            # Distance from display center to rectangle center
            center_distance = math.sqrt((rect_center_x - center_x)**2 + 
                                      (rect_center_y - center_y)**2)
            
            # Calculate distances from display center to each corner
            corners = [
                (x, y),                    # Top-left
                (x + width, y),            # Top-right
                (x, y + height),           # Bottom-left
                (x + width, y + height)    # Bottom-right
            ]
            
            corner_distances = []
            for corner_x, corner_y in corners:
                distance = math.sqrt((corner_x - center_x)**2 + (corner_y - center_y)**2)
                corner_distances.append(distance)
            
            max_corner_distance = max(corner_distances)
            
            # Validation results
            within_safe_area = max_corner_distance <= self.display_safe_radius
            within_max_area = max_corner_distance <= self.display_max_radius
            valid = within_safe_area  # Consider valid if within safe area
            
            result = {
                'valid': valid,
                'center_distance': center_distance,
                'corner_distances': corner_distances,
                'max_corner_distance': max_corner_distance,
                'within_safe_area': within_safe_area,
                'within_max_area': within_max_area
            }
            
            self.logger.debug(f"Circular bounds validation: rect={rect_coords}, result={result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating circular bounds: {e}")
            # Return conservative validation result
            return {
                'valid': False,
                'center_distance': float('inf'),
                'corner_distances': [float('inf')],
                'max_corner_distance': float('inf'),
                'within_safe_area': False,
                'within_max_area': False
            }
    
    # Comprehensive validation and testing methods for circular layout
    
    def validate_all_screen_elements(self, screen_name: str = "current") -> dict:
        """Validate all UI elements on the current screen for circular boundary compliance.
        
        Args:
            screen_name: Name of the screen being validated (for logging)
            
        Returns:
            dict: Comprehensive validation results including:
                - screen_name: Name of the validated screen
                - total_elements: Total number of elements checked
                - valid_elements: Number of elements within safe area
                - invalid_elements: List of elements outside safe area
                - validation_summary: Overall validation status
                - performance_metrics: Timing information for validation
                
        Thread Safety:
            This method is thread-safe and reads touch regions under lock.
        """
        import time
        
        start_time = time.time()
        
        try:
            with self._touch_regions_lock:
                # Create a copy of touch regions for validation
                regions_to_validate = self.touch_regions.copy()
            
            invalid_elements = []
            valid_elements = 0
            total_elements = len(regions_to_validate)
            
            self.logger.info(f"Validating {total_elements} elements on {screen_name} screen")
            
            for i, region_data in enumerate(regions_to_validate):
                try:
                    # Extract region information (handle different region data formats)
                    if len(region_data) >= 2:
                        region_id = region_data[0]
                        region_rect = region_data[1]
                        
                        # Get rectangle coordinates
                        if hasattr(region_rect, 'x'):  # pygame.Rect object
                            rect_coords = (region_rect.x, region_rect.y, region_rect.width, region_rect.height)
                        else:  # tuple format
                            rect_coords = region_rect
                        
                        # Validate the element
                        validation_result = self._validate_circular_bounds(rect_coords)
                        
                        if validation_result['valid']:
                            valid_elements += 1
                        else:
                            invalid_elements.append({
                                'region_id': region_id,
                                'rect_coords': rect_coords,
                                'max_corner_distance': validation_result['max_corner_distance'],
                                'safe_radius': self.display_safe_radius,
                                'excess_distance': validation_result['max_corner_distance'] - self.display_safe_radius
                            })
                            
                            self.logger.warning(f"Element '{region_id}' extends beyond safe area: "
                                              f"max distance {validation_result['max_corner_distance']:.1f}px "
                                              f"(safe radius: {self.display_safe_radius}px)")
                    
                except Exception as e:
                    self.logger.error(f"Error validating region {i}: {e}")
                    invalid_elements.append({
                        'region_id': f'unknown_{i}',
                        'error': str(e)
                    })
            
            end_time = time.time()
            validation_time = end_time - start_time
            
            # Calculate validation summary
            validation_passed = len(invalid_elements) == 0
            
            validation_summary = {
                'passed': validation_passed,
                'total_elements': total_elements,
                'valid_elements': valid_elements,
                'invalid_count': len(invalid_elements),
                'success_rate': (valid_elements / total_elements * 100) if total_elements > 0 else 100
            }
            
            # Log summary
            if validation_passed:
                self.logger.info(f"✓ Screen '{screen_name}' validation PASSED: "
                               f"all {total_elements} elements within safe area")
            else:
                self.logger.warning(f"✗ Screen '{screen_name}' validation FAILED: "
                                  f"{len(invalid_elements)} of {total_elements} elements outside safe area")
            
            return {
                'screen_name': screen_name,
                'total_elements': total_elements,
                'valid_elements': valid_elements,
                'invalid_elements': invalid_elements,
                'validation_summary': validation_summary,
                'performance_metrics': {
                    'validation_time': validation_time,
                    'elements_per_second': total_elements / validation_time if validation_time > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during screen validation: {e}")
            return {
                'screen_name': screen_name,
                'error': str(e),
                'validation_summary': {'passed': False, 'error': True}
            }
    
    def render_debug_overlay(self, surface) -> None:
        """Render visual debugging overlay showing circular boundary and safe zones.
        
        Args:
            surface: Pygame surface to draw the overlay on
            
        Thread Safety:
            This method is thread-safe and performs read-only operations.
        """
        try:
            if not self.display_available:
                return
            
            # Get display geometry
            geometry = self._get_circular_safe_area()
            center_x, center_y = geometry['center']
            safe_radius = geometry['safe_radius']
            max_radius = geometry['max_radius']
            
            # Colors for debug overlay (semi-transparent)
            safe_area_color = (0, 255, 0, 64)      # Green for safe area
            warning_area_color = (255, 165, 0, 64)  # Orange for warning area
            danger_area_color = (255, 0, 0, 32)     # Red for danger area
            center_color = (255, 255, 255, 128)     # White for center point
            
            # Create overlay surface with per-pixel alpha
            overlay = pygame.Surface((480, 480), pygame.SRCALPHA)
            
            # Draw danger area (outside max radius)
            pygame.draw.circle(overlay, danger_area_color, (center_x, center_y), max_radius + 20, 20)
            
            # Draw warning area (between safe and max radius)
            if max_radius > safe_radius:
                pygame.draw.circle(overlay, warning_area_color, (center_x, center_y), max_radius, 3)
            
            # Draw safe area boundary
            pygame.draw.circle(overlay, safe_area_color, (center_x, center_y), safe_radius, 3)
            
            # Draw center point
            pygame.draw.circle(overlay, center_color, (center_x, center_y), 5)
            
            # Draw radius indicators
            font = pygame.font.Font(None, 24)
            
            # Safe radius text
            safe_text = font.render(f"Safe: {safe_radius}px", True, (0, 255, 0))
            surface.blit(safe_text, (center_x - 50, center_y - safe_radius - 25))
            
            # Max radius text
            if max_radius > safe_radius:
                max_text = font.render(f"Max: {max_radius}px", True, (255, 165, 0))
                surface.blit(max_text, (center_x - 50, center_y - max_radius - 25))
            
            # Center coordinates text
            center_text = font.render(f"Center: ({center_x}, {center_y})", True, (255, 255, 255))
            surface.blit(center_text, (center_x - 70, center_y + 15))
            
            # Blit overlay to main surface
            surface.blit(overlay, (0, 0))
            
            # Highlight invalid elements if any exist
            try:
                validation_result = self.validate_all_screen_elements("debug")
                if validation_result.get('invalid_elements'):
                    for invalid_element in validation_result['invalid_elements']:
                        if 'rect_coords' in invalid_element:
                            x, y, width, height = invalid_element['rect_coords']
                            # Draw red border around invalid elements
                            pygame.draw.rect(surface, (255, 0, 0), (x, y, width, height), 2)
                            
                            # Draw error text
                            error_text = font.render("OUT OF BOUNDS", True, (255, 0, 0))
                            surface.blit(error_text, (x, y - 20))
                            
            except Exception as e:
                self.logger.debug(f"Error highlighting invalid elements: {e}")
            
        except Exception as e:
            self.logger.error(f"Error rendering debug overlay: {e}")
    
    def test_circular_layout_integration(self) -> dict:
        """Integration test for circular layout across all setup screens.
        
        Returns:
            dict: Comprehensive test results including:
                - screens_tested: List of screens that were tested
                - overall_result: Overall test pass/fail status
                - screen_results: Individual results for each screen
                - performance_summary: Performance metrics
                - recommendations: Suggestions for improvements
        """
        import time
        
        start_time = time.time()
        
        try:
            # Define all setup screens to test
            test_screens = [
                (SetupScreen.WELCOME, "Welcome"),
                (SetupScreen.DISCOVERY, "Discovery"),
                (SetupScreen.DEVICE_LIST, "Device List"),
                (SetupScreen.PAIRING, "Pairing"),
                (SetupScreen.CURRENT_DEVICE, "Current Device"),
                (SetupScreen.COMPLETE, "Complete"),
                (SetupScreen.DEVICE_MANAGEMENT, "Device Management"),
                (SetupScreen.CONFIRMATION, "Confirmation")
            ]
            
            # Add manual entry screen if enabled
            if self.manual_entry_mode:
                test_screens.append((None, "Manual Entry"))
            
            screen_results = {}
            screens_tested = []
            overall_passed = True
            
            self.logger.info("Starting circular layout integration test")
            
            # Store original screen state
            original_screen = self.state.current_screen
            original_manual_mode = self.manual_entry_mode
            
            try:
                for screen_enum, screen_name in test_screens:
                    screens_tested.append(screen_name)
                    
                    # Set screen state for testing
                    if screen_enum is not None:
                        self.state.current_screen = screen_enum
                    else:
                        self.manual_entry_mode = True
                    
                    # Simulate rendering the screen to populate touch regions
                    if self.display_available:
                        try:
                            # Create a temporary surface for testing
                            test_surface = pygame.Surface((480, 480))
                            test_surface.fill((0, 0, 0))
                            
                            # Render the screen
                            self.render(test_surface)
                            
                            # Validate the screen
                            validation_result = self.validate_all_screen_elements(screen_name)
                            screen_results[screen_name] = validation_result
                            
                            if not validation_result['validation_summary']['passed']:
                                overall_passed = False
                                
                        except Exception as e:
                            self.logger.error(f"Error testing screen '{screen_name}': {e}")
                            screen_results[screen_name] = {
                                'error': str(e),
                                'validation_summary': {'passed': False, 'error': True}
                            }
                            overall_passed = False
                    else:
                        # Skip rendering tests if pygame not available
                        self.logger.warning(f"Skipping visual test for '{screen_name}' (pygame not available)")
                        screen_results[screen_name] = {
                            'skipped': True,
                            'validation_summary': {'passed': True, 'skipped': True}
                        }
                
            finally:
                # Restore original screen state
                self.state.current_screen = original_screen
                self.manual_entry_mode = original_manual_mode
            
            end_time = time.time()
            test_time = end_time - start_time
            
            # Generate recommendations
            recommendations = []
            total_invalid = sum(
                len(result.get('invalid_elements', []))
                for result in screen_results.values()
                if 'invalid_elements' in result
            )
            
            if total_invalid > 0:
                recommendations.append(f"Fix {total_invalid} elements that extend beyond safe area")
            
            if test_time > 1.0:
                recommendations.append("Consider optimizing validation performance")
            
            if overall_passed:
                recommendations.append("All screens pass circular layout validation")
            
            test_result = {
                'screens_tested': screens_tested,
                'overall_result': {
                    'passed': overall_passed,
                    'screens_count': len(screens_tested),
                    'passed_screens': sum(1 for r in screen_results.values() 
                                        if r.get('validation_summary', {}).get('passed', False)),
                    'failed_screens': sum(1 for r in screen_results.values() 
                                        if not r.get('validation_summary', {}).get('passed', True))
                },
                'screen_results': screen_results,
                'performance_summary': {
                    'total_test_time': test_time,
                    'screens_per_second': len(screens_tested) / test_time if test_time > 0 else 0
                },
                'recommendations': recommendations
            }
            
            # Log overall results
            if overall_passed:
                self.logger.info(f"✓ Integration test PASSED: all {len(screens_tested)} screens validated")
            else:
                failed_count = test_result['overall_result']['failed_screens']
                self.logger.warning(f"✗ Integration test FAILED: {failed_count} of {len(screens_tested)} screens have issues")
            
            return test_result
            
        except Exception as e:
            self.logger.error(f"Error during integration test: {e}")
            return {
                'error': str(e),
                'overall_result': {'passed': False, 'error': True}
            }
    
    # Enhanced logging and performance monitoring for circular positioning
    
    def log_positioning_metrics(self, operation: str, start_time: float, element_count: int = 1, 
                               additional_data: dict = None) -> None:
        """Log performance metrics for circular positioning operations.
        
        Args:
            operation: Name of the operation being measured
            start_time: Start time from time.time()
            element_count: Number of elements processed
            additional_data: Optional additional metrics to log
        """
        import time
        
        try:
            end_time = time.time()
            duration = end_time - start_time
            
            # Calculate performance metrics
            elements_per_second = element_count / duration if duration > 0 else 0
            
            # Base metrics
            metrics = {
                'operation': operation,
                'duration_ms': duration * 1000,
                'element_count': element_count,
                'elements_per_second': elements_per_second
            }
            
            # Add additional data if provided
            if additional_data:
                metrics.update(additional_data)
            
            # Log based on performance thresholds
            if duration > 0.1:  # Slow operations (>100ms)
                self.logger.warning(f"Slow circular positioning: {operation} took {duration*1000:.1f}ms "
                                   f"for {element_count} elements ({elements_per_second:.1f} elements/sec)")
            elif duration > 0.05:  # Moderate operations (>50ms)
                self.logger.info(f"Circular positioning: {operation} took {duration*1000:.1f}ms "
                                f"for {element_count} elements")
            else:  # Fast operations
                self.logger.debug(f"Circular positioning: {operation} completed in {duration*1000:.1f}ms")
            
            # Log detailed metrics in debug mode
            self.logger.debug(f"Positioning metrics: {metrics}")
            
        except Exception as e:
            self.logger.error(f"Error logging positioning metrics: {e}")
    
    def log_circular_positioning_debug(self, element_id: str, angle: float, radius: float, 
                                     result_coords: tuple, validation_result: dict = None) -> None:
        """Log detailed debug information for circular positioning operations.
        
        Args:
            element_id: Identifier for the element being positioned
            angle: Angle in degrees used for positioning
            radius: Radius used for positioning
            result_coords: Resulting (x, y, width, height) coordinates
            validation_result: Optional validation result from _validate_circular_bounds
        """
        try:
            # Create detailed log entry
            log_data = {
                'element_id': element_id,
                'positioning': {
                    'angle_degrees': angle,
                    'radius_px': radius,
                    'result_coords': result_coords
                },
                'display_config': {
                    'center': self.display_center,
                    'safe_radius': self.display_safe_radius,
                    'max_radius': self.display_max_radius
                }
            }
            
            # Add validation data if provided
            if validation_result:
                log_data['validation'] = {
                    'valid': validation_result.get('valid', False),
                    'max_corner_distance': validation_result.get('max_corner_distance', 0),
                    'within_safe_area': validation_result.get('within_safe_area', False)
                }
            
            # Calculate additional positioning metrics
            x, y, width, height = result_coords
            element_center = (x + width/2, y + height/2)
            center_distance = math.sqrt((element_center[0] - self.display_center[0])**2 + 
                                      (element_center[1] - self.display_center[1])**2)
            
            log_data['calculated_metrics'] = {
                'element_center': element_center,
                'center_distance': center_distance,
                'radius_accuracy': abs(center_distance - radius)
            }
            
            self.logger.debug(f"Circular positioning debug: {log_data}")
            
            # Log warnings for positioning issues
            if validation_result and not validation_result.get('valid', True):
                self.logger.warning(f"Element '{element_id}' positioned outside safe area: "
                                   f"max distance {validation_result.get('max_corner_distance', 0):.1f}px "
                                   f"exceeds safe radius {self.display_safe_radius}px")
            
            # Check radius accuracy
            radius_accuracy = abs(center_distance - radius)
            if radius_accuracy > 2.0:  # More than 2px off
                self.logger.warning(f"Element '{element_id}' radius accuracy issue: "
                                   f"requested {radius}px, actual {center_distance:.1f}px "
                                   f"(difference: {radius_accuracy:.1f}px)")
            
        except Exception as e:
            self.logger.error(f"Error logging circular positioning debug info: {e}")
    
    def monitor_circular_performance(self, enable_monitoring: bool = True) -> dict:
        """Enable or disable performance monitoring for circular positioning operations.
        
        Args:
            enable_monitoring: Whether to enable detailed performance monitoring
            
        Returns:
            dict: Current monitoring configuration and statistics
        """
        try:
            # Initialize monitoring state if not exists
            if not hasattr(self, '_performance_monitoring'):
                self._performance_monitoring = {
                    'enabled': False,
                    'stats': {
                        'total_positioning_calls': 0,
                        'total_validation_calls': 0,
                        'total_positioning_time': 0.0,
                        'total_validation_time': 0.0,
                        'average_positioning_time': 0.0,
                        'average_validation_time': 0.0,
                        'slow_operations_count': 0
                    },
                    'recent_operations': []
                }
            
            # Update monitoring state
            self._performance_monitoring['enabled'] = enable_monitoring
            
            if enable_monitoring:
                self.logger.info("Circular positioning performance monitoring ENABLED")
            else:
                self.logger.info("Circular positioning performance monitoring DISABLED")
            
            return self._performance_monitoring.copy()
            
        except Exception as e:
            self.logger.error(f"Error configuring performance monitoring: {e}")
            return {'error': str(e)}
    
    def get_circular_performance_report(self) -> dict:
        """Generate a comprehensive performance report for circular positioning operations.
        
        Returns:
            dict: Performance report including timing statistics and recommendations
        """
        try:
            if not hasattr(self, '_performance_monitoring'):
                return {'error': 'Performance monitoring not initialized'}
            
            stats = self._performance_monitoring['stats']
            
            # Calculate performance metrics
            report = {
                'monitoring_enabled': self._performance_monitoring['enabled'],
                'operation_counts': {
                    'total_positioning_calls': stats['total_positioning_calls'],
                    'total_validation_calls': stats['total_validation_calls'],
                    'slow_operations': stats['slow_operations_count']
                },
                'timing_statistics': {
                    'total_positioning_time_ms': stats['total_positioning_time'] * 1000,
                    'total_validation_time_ms': stats['total_validation_time'] * 1000,
                    'average_positioning_time_ms': stats['average_positioning_time'] * 1000,
                    'average_validation_time_ms': stats['average_validation_time'] * 1000
                },
                'performance_analysis': {}
            }
            
            # Performance analysis and recommendations
            avg_pos_time = stats['average_positioning_time']
            avg_val_time = stats['average_validation_time']
            
            recommendations = []
            
            if avg_pos_time > 0.01:  # > 10ms average
                recommendations.append("Positioning operations are slow - consider caching calculations")
                report['performance_analysis']['positioning_status'] = 'slow'
            elif avg_pos_time > 0.005:  # > 5ms average
                report['performance_analysis']['positioning_status'] = 'moderate'
            else:
                report['performance_analysis']['positioning_status'] = 'fast'
            
            if avg_val_time > 0.005:  # > 5ms average
                recommendations.append("Validation operations are slow - consider optimizing bounds checking")
                report['performance_analysis']['validation_status'] = 'slow'
            else:
                report['performance_analysis']['validation_status'] = 'fast'
            
            if stats['slow_operations_count'] > 10:
                recommendations.append(f"High number of slow operations ({stats['slow_operations_count']}) detected")
            
            if not recommendations:
                recommendations.append("Performance is within acceptable limits")
            
            report['recommendations'] = recommendations
            
            # Recent operations summary
            if 'recent_operations' in self._performance_monitoring:
                recent_ops = self._performance_monitoring['recent_operations'][-10:]  # Last 10 operations
                report['recent_operations'] = recent_ops
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}
    
    def reset_circular_performance_stats(self) -> None:
        """Reset all circular positioning performance statistics."""
        try:
            if hasattr(self, '_performance_monitoring'):
                self._performance_monitoring['stats'] = {
                    'total_positioning_calls': 0,
                    'total_validation_calls': 0,
                    'total_positioning_time': 0.0,
                    'total_validation_time': 0.0,
                    'average_positioning_time': 0.0,
                    'average_validation_time': 0.0,
                    'slow_operations_count': 0
                }
                self._performance_monitoring['recent_operations'] = []
                
                self.logger.info("Circular positioning performance statistics reset")
            else:
                self.logger.warning("Performance monitoring not initialized - nothing to reset")
                
        except Exception as e:
            self.logger.error(f"Error resetting performance statistics: {e}")
    
    # Circular layout optimization methods for curved device lists
    
    def _calculate_curved_list_layout(self, item_count: int, start_y: int = 100, 
                                    item_height: int = 45, item_spacing: int = 3) -> list:
        """
        Calculate curved list layout positions for circular display optimization.
        
        Creates a subtle curve that follows the display contour while maximizing
        usable space and maintaining readability.
        
        Args:
            item_count: Number of items to position
            start_y: Starting Y position for first item
            item_height: Height of each item in pixels
            item_spacing: Spacing between items in pixels
        
        Returns:
            list: List of dictionaries containing layout data for each item:
                - index: Item index
                - x: X position (dynamically calculated)
                - y: Y position
                - width: Item width (adjusted for circular bounds)
                - height: Item height
                - scale: Visual scale factor (0.95-1.0)
                - opacity: Opacity factor (0.85-1.0)
                - center_distance: Distance from display center
                - in_safe_area: Boolean indicating if within safe radius
        """
        try:
            layout_data = []
            center_x, center_y = self.display_center
            safe_radius = self.display_safe_radius
            
            # Cache circular calculations for performance
            if not hasattr(self, '_circular_layout_cache'):
                self._circular_layout_cache = {}
            
            self.logger.debug(f"Calculating curved layout for {item_count} items starting at y={start_y}")
            
            for i in range(item_count):
                # Calculate vertical position
                y_pos = start_y + i * (item_height + item_spacing)
                
                # Calculate distance from vertical center
                y_distance_from_center = abs(y_pos + item_height // 2 - center_y)
                
                # Create cache key for this position
                cache_key = f"curved_{y_pos}_{item_height}"
                
                if cache_key in self._circular_layout_cache:
                    # Use cached calculations
                    layout_item = self._circular_layout_cache[cache_key].copy()
                    layout_item['index'] = i
                    layout_item['y'] = y_pos
                else:
                    # Calculate curve offset using circular geometry
                    # Formula: x_offset = sqrt(safe_radius² - y_distance_from_center²)
                    try:
                        if y_distance_from_center <= safe_radius:
                            # Within safe circular bounds
                            horizontal_radius = math.sqrt(safe_radius**2 - y_distance_from_center**2)
                            
                            # Calculate curve offset (subtle indentation from center)
                            # Items near edges get more indentation to follow circle contour
                            curve_factor = 1.0 - (horizontal_radius / safe_radius)
                            x_offset = int(curve_factor * 15)  # Max 15px offset for subtle curve
                            
                            # Calculate dynamic item width
                            max_width_at_position = int(horizontal_radius * 2 * 0.85)  # 85% of available width
                            item_width = min(400, max_width_at_position)  # Cap at 400px, reduce as needed
                            
                            # Calculate x position (centered with curve offset)
                            x_pos = center_x - item_width // 2 + x_offset
                            
                            # Visual hierarchy calculations
                            center_distance = math.sqrt((center_x - (x_pos + item_width // 2))**2 + 
                                                      (center_y - (y_pos + item_height // 2))**2)
                            
                            # Scale and opacity based on distance from center
                            distance_ratio = center_distance / safe_radius
                            scale_factor = 1.0 - (distance_ratio * 0.05)  # 95-100% scale
                            opacity_factor = 1.0 - (distance_ratio * 0.15)  # 85-100% opacity
                            
                            in_safe_area = center_distance <= safe_radius
                            
                        else:
                            # Outside safe radius - fallback to centered positioning
                            self.logger.warning(f"Item {i} at y={y_pos} outside safe radius, using fallback")
                            x_pos = center_x - 200  # 400px width centered
                            item_width = 400
                            scale_factor = 0.95
                            opacity_factor = 0.85
                            center_distance = y_distance_from_center
                            in_safe_area = False
                            
                    except Exception as calc_error:
                        self.logger.error(f"Error in curve calculation for item {i}: {calc_error}")
                        # Safe fallback positioning
                        x_pos = center_x - 200
                        item_width = 400
                        scale_factor = 1.0
                        opacity_factor = 1.0
                        center_distance = 0
                        in_safe_area = True
                    
                    # Create layout item
                    layout_item = {
                        'index': i,
                        'x': x_pos,
                        'y': y_pos,
                        'width': item_width,
                        'height': item_height,
                        'scale': scale_factor,
                        'opacity': opacity_factor,
                        'center_distance': center_distance,
                        'in_safe_area': in_safe_area,
                        'curve_offset': x_offset if 'x_offset' in locals() else 0
                    }
                    
                    # Cache the calculation (without index and y which vary)
                    cache_item = layout_item.copy()
                    del cache_item['index']
                    del cache_item['y']
                    self._circular_layout_cache[cache_key] = cache_item
                
                layout_data.append(layout_item)
                
                # Log positioning debug info for development
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f"Item {i}: x={layout_item['x']}, y={layout_item['y']}, "
                                    f"w={layout_item['width']}, scale={layout_item['scale']:.2f}, "
                                    f"opacity={layout_item['opacity']:.2f}, safe={layout_item['in_safe_area']}")
            
            # Performance monitoring
            cache_size = len(self._circular_layout_cache)
            if cache_size > 100:  # Prevent cache from growing too large
                # Clear oldest 50% of cache entries
                cache_keys = list(self._circular_layout_cache.keys())
                for old_key in cache_keys[:cache_size // 2]:
                    del self._circular_layout_cache[old_key]
                self.logger.debug(f"Trimmed circular layout cache from {cache_size} to {len(self._circular_layout_cache)} entries")
            
            self.logger.info(f"Generated curved layout for {len(layout_data)} items with {cache_size} cached calculations")
            return layout_data
            
        except Exception as e:
            self.logger.error(f"Error calculating curved list layout: {e}")
            # Return fallback linear layout
            fallback_layout = []
            for i in range(item_count):
                fallback_layout.append({
                    'index': i,
                    'x': 40,  # Standard left margin
                    'y': start_y + i * (item_height + item_spacing),
                    'width': 400,
                    'height': item_height,
                    'scale': 1.0,
                    'opacity': 1.0,
                    'center_distance': 0,
                    'in_safe_area': True,
                    'curve_offset': 0
                })
            return fallback_layout
    
    def _create_curved_device_surface(self, device: 'BluetoothDevice', layout_item: dict, 
                                    item_index: int, use_alternating_bg: bool = True) -> tuple:
        """
        Create a device item surface with curved layout optimizations.
        
        Args:
            device: BluetoothDevice object to render
            layout_item: Layout data from _calculate_curved_list_layout()
            item_index: Index of the item for caching
            use_alternating_bg: Whether to use alternating backgrounds
            
        Returns:
            tuple: (surface, touch_rect) for the curved device item
        """
        try:
            start_time = time.time()
            
            # Extract layout parameters
            item_width = int(layout_item['width'])
            item_height = int(layout_item['height'])
            scale_factor = layout_item['scale']
            opacity_factor = layout_item['opacity']
            
            # Create cache key including curved layout parameters
            cache_key = f"curved_{device.mac_address}_{item_index}_{item_width}_{scale_factor:.2f}_{opacity_factor:.2f}"
            
            # Check cache first
            with self._device_cache_lock:
                if cache_key in self._device_item_cache:
                    cached_surface, cached_rect = self._device_item_cache[cache_key]
                    # Create touch rect at current position
                    touch_rect = pygame.Rect(layout_item['x'] - 5, layout_item['y'], 
                                           item_width + 10, item_height)
                    return cached_surface, touch_rect
            
            # Create scaled surface for curved item
            scaled_width = int(item_width * scale_factor)
            scaled_height = int(item_height * scale_factor)
            item_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
            
            # Apply opacity to background
            base_alpha = int(255 * opacity_factor)
            
            # Alternating background with opacity
            if use_alternating_bg and item_index % 2 == 1:
                bg_color = (*self.colors['surface'][:3], base_alpha)
            else:
                bg_color = (*self.colors['background'][:3], base_alpha)
            
            # Draw background with rounded corners (scaled)
            bg_rect = pygame.Rect(0, 0, scaled_width, scaled_height - 1)
            try:
                pygame.draw.rect(item_surface, bg_color[:3], bg_rect, border_radius=int(6 * scale_factor))
            except TypeError:
                # Fallback for older pygame versions without border_radius
                pygame.draw.rect(item_surface, bg_color[:3], bg_rect)
            
            # Set global alpha for the entire surface
            item_surface.set_alpha(base_alpha)
            
            # Device type indicator - scaled circle
            indicator_color = self._get_device_type_color(device)
            indicator_radius = int(6 * scale_factor)
            indicator_center = (int(12 * scale_factor), scaled_height // 2)
            pygame.draw.circle(item_surface, indicator_color, indicator_center, indicator_radius)
            
            # Scale font sizes based on layout scale factor
            body_font_size = int(TypographyConstants.FONT_BODY * scale_factor)
            minimal_font_size = int(TypographyConstants.FONT_MINIMAL * scale_factor)
            signal_font_size = int(TypographyConstants.FONT_LABEL_SMALL * scale_factor)
            
            # Device name with scaled font
            try:
                name_font = get_font_manager().get_font(body_font_size)
                if not name_font:
                    name_font = pygame.font.Font(None, body_font_size)
            except Exception as e:
                self.logger.error(f"Error getting scaled body font: {e}")
                name_font = pygame.font.Font(None, body_font_size)
            
            # Truncate device name for curved width
            device_name = device.name
            name_text = name_font.render(device_name, True, self.colors['text'])
            max_name_width = int((scaled_width - 120) * 0.7)  # Leave space for signal, adjusted for curve
            
            if name_text.get_width() > max_name_width:
                truncated_name = device_name
                while name_font.render(truncated_name + "...", True, self.colors['text']).get_width() > max_name_width:
                    truncated_name = truncated_name[:-1]
                    if len(truncated_name) <= 3:
                        break
                device_name = truncated_name + "..."
                name_text = name_font.render(device_name, True, self.colors['text'])
            
            name_y = int((8 + 6) * scale_factor)
            name_rect = name_text.get_rect(midleft=(int(25 * scale_factor), name_y))
            item_surface.blit(name_text, name_rect)
            
            # MAC address with scaled font
            try:
                mac_font = get_font_manager().get_font(minimal_font_size)
                if not mac_font:
                    mac_font = pygame.font.Font(None, minimal_font_size)
            except Exception as e:
                self.logger.error(f"Error getting scaled minimal font: {e}")
                mac_font = pygame.font.Font(None, minimal_font_size)
                
            mac_text = mac_font.render(device.mac_address, True, self.colors['text_dim'])
            mac_y = int((28 + 4) * scale_factor)
            mac_rect = mac_text.get_rect(midleft=(int(25 * scale_factor), mac_y))
            item_surface.blit(mac_text, mac_rect)
            
            # Signal strength with scaled font
            signal_percentage = max(0, min(100, int((device.signal_strength + 100) * 1.25)))
            try:
                signal_font = get_font_manager().get_font(signal_font_size)
                if not signal_font:
                    signal_font = pygame.font.Font(None, signal_font_size)
            except Exception as e:
                self.logger.error(f"Error getting scaled signal font: {e}")
                signal_font = pygame.font.Font(None, signal_font_size)
            
            # Color code signal strength
            if signal_percentage >= 70:
                signal_color = self.colors['success']
            elif signal_percentage >= 40:
                signal_color = self.colors['warning']
            else:
                signal_color = self.colors['danger']
            
            signal_text = signal_font.render(f"{signal_percentage}%", True, signal_color)
            signal_rect = signal_text.get_rect(midright=(scaled_width - int(10 * scale_factor), scaled_height // 2))
            item_surface.blit(signal_text, signal_rect)
            
            # Cache the rendered surface
            with self._device_cache_lock:
                if len(self._device_item_cache) > 50:
                    # Remove oldest entries
                    cache_keys = list(self._device_item_cache.keys())
                    for old_key in cache_keys[:20]:
                        del self._device_item_cache[old_key]
                
                self._device_item_cache[cache_key] = (item_surface, bg_rect)
            
            # Create extended touch region for curved item
            touch_rect = pygame.Rect(layout_item['x'] - 5, layout_item['y'], item_width + 10, item_height)
            
            # Log performance for slow renders
            render_time = time.time() - start_time
            if render_time > 0.015:  # > 15ms (slightly higher threshold for curved rendering)
                self.logger.warning(f"Slow curved device item render: {render_time*1000:.1f}ms for {device.name}")
            
            return item_surface, touch_rect
            
        except Exception as e:
            self.logger.error(f"Error creating curved device surface for {device.name}: {e}")
            # Return fallback surface
            fallback_surface = pygame.Surface((layout_item['width'], layout_item['height']), pygame.SRCALPHA)
            fallback_surface.fill(self.colors['surface'])
            fallback_rect = pygame.Rect(layout_item['x'], layout_item['y'], layout_item['width'], layout_item['height'])
            return fallback_surface, fallback_rect
    
    def _render_circular_debug_overlay(self, surface) -> None:
        """
        Render debug overlay showing circular boundaries and positioning guides.
        
        Only renders when debug logging is enabled. Helps with development and testing
        of circular layout positioning.
        """
        try:
            if not self.logger.isEnabledFor(logging.DEBUG):
                return
            
            center_x, center_y = self.display_center
            
            # Draw safe radius circle
            pygame.draw.circle(surface, (0, 255, 0, 100), (center_x, center_y), 
                             self.display_safe_radius, 2)
            
            # Draw maximum radius circle
            pygame.draw.circle(surface, (255, 255, 0, 100), (center_x, center_y), 
                             self.display_max_radius, 1)
            
            # Draw center crosshair
            pygame.draw.line(surface, (255, 0, 0, 150), 
                           (center_x - 10, center_y), (center_x + 10, center_y), 2)
            pygame.draw.line(surface, (255, 0, 0, 150), 
                           (center_x, center_y - 10), (center_x, center_y + 10), 2)
            
            # Draw grid lines for positioning reference
            for angle in range(0, 360, 45):
                end_x = center_x + int(self.display_safe_radius * math.cos(math.radians(angle)))
                end_y = center_y + int(self.display_safe_radius * math.sin(math.radians(angle)))
                pygame.draw.line(surface, (100, 100, 100, 80), 
                               (center_x, center_y), (end_x, end_y), 1)
            
            self.logger.debug("Rendered circular debug overlay")
            
        except Exception as e:
            self.logger.error(f"Error rendering circular debug overlay: {e}")
    
    def _precompute_circular_regions(self) -> None:
        """
        Precompute valid circular regions for performance optimization.
        
        Caches calculations for commonly used positions to avoid repeated
        trigonometric calculations during rendering.
        """
        try:
            if not hasattr(self, '_circular_regions_cache'):
                self._circular_regions_cache = {}
            
            center_x, center_y = self.display_center
            safe_radius = self.display_safe_radius
            
            # Precompute regions for device list positions
            start_y = 100
            item_height = 45
            item_spacing = 3
            
            for i in range(10):  # Precompute for up to 10 devices
                y_pos = start_y + i * (item_height + item_spacing)
                y_distance = abs(y_pos + item_height // 2 - center_y)
                
                if y_distance <= safe_radius:
                    horizontal_radius = math.sqrt(safe_radius**2 - y_distance**2)
                    max_width = int(horizontal_radius * 2 * 0.85)
                    
                    # Cache the computation
                    cache_key = f"device_pos_{y_pos}"
                    self._circular_regions_cache[cache_key] = {
                        'y_distance': y_distance,
                        'horizontal_radius': horizontal_radius,
                        'max_width': max_width,
                        'is_valid': True
                    }
                else:
                    cache_key = f"device_pos_{y_pos}"
                    self._circular_regions_cache[cache_key] = {
                        'y_distance': y_distance,
                        'horizontal_radius': 0,
                        'max_width': 0,
                        'is_valid': False
                    }
            
            self.logger.debug(f"Precomputed {len(self._circular_regions_cache)} circular regions")
            
        except Exception as e:
            self.logger.error(f"Error precomputing circular regions: {e}")
    
    def _validate_curved_touch_regions(self, layout_data: list, new_regions: list) -> list:
        """
        Validate and optimize touch regions for curved layout.
        
        Ensures touch regions don't extend outside the circular safe area
        and adjusts them for optimal touch accuracy on curved items.
        
        Args:
            layout_data: List of layout items from _calculate_curved_list_layout()
            new_regions: Current list of new touch regions
            
        Returns:
            list: Validated and optimized touch regions
        """
        try:
            validated_regions = []
            center_x, center_y = self.display_center
            safe_radius = self.display_safe_radius
            
            for region_tuple in new_regions:
                region_id = region_tuple[0]
                region_rect = region_tuple[1]
                region_data = region_tuple[2] if len(region_tuple) > 2 else None
                
                # Skip non-device regions
                if region_id != "select_device":
                    validated_regions.append(region_tuple)
                    continue
                
                # Validate device touch region against circular bounds
                rect_corners = [
                    (region_rect.left, region_rect.top),
                    (region_rect.right, region_rect.top),
                    (region_rect.left, region_rect.bottom),
                    (region_rect.right, region_rect.bottom)
                ]
                
                # Check if all corners are within safe radius
                all_corners_safe = True
                max_distance = 0
                
                for corner_x, corner_y in rect_corners:
                    distance = math.sqrt((corner_x - center_x)**2 + (corner_y - center_y)**2)
                    max_distance = max(max_distance, distance)
                    if distance > safe_radius:
                        all_corners_safe = False
                
                if all_corners_safe:
                    # Region is fully within safe area
                    validated_regions.append(region_tuple)
                    self.logger.debug(f"Touch region for {region_data.name if region_data else 'device'} "
                                    f"validated (max distance: {max_distance:.1f}px)")
                else:
                    # Adjust region to fit within safe area
                    self.logger.warning(f"Touch region for {region_data.name if region_data else 'device'} "
                                      f"extends outside safe area (max distance: {max_distance:.1f}px)")
                    
                    # Create adjusted region that fits within circular bounds
                    # Find the device in layout_data to get proper positioning
                    device_layout = None
                    for layout_item in layout_data:
                        if (layout_item['x'] <= region_rect.x <= layout_item['x'] + layout_item['width'] and
                            layout_item['y'] <= region_rect.y <= layout_item['y'] + layout_item['height']):
                            device_layout = layout_item
                            break
                    
                    if device_layout:
                        # Use the device's computed safe bounds
                        adjusted_width = min(region_rect.width, device_layout['width'])
                        adjusted_height = min(region_rect.height, device_layout['height'])
                        adjusted_x = device_layout['x']
                        adjusted_y = device_layout['y']
                        
                        adjusted_rect = pygame.Rect(adjusted_x, adjusted_y, adjusted_width, adjusted_height)
                        validated_regions.append((region_id, adjusted_rect, region_data))
                        
                        self.logger.debug(f"Adjusted touch region for {region_data.name if region_data else 'device'} "
                                        f"to fit within safe area")
                    else:
                        # Fallback: keep original region but log warning
                        validated_regions.append(region_tuple)
                        self.logger.warning(f"Could not adjust touch region for {region_data.name if region_data else 'device'}, "
                                          "using original bounds")
            
            self.logger.debug(f"Validated {len(validated_regions)} touch regions for curved layout")
            return validated_regions
            
        except Exception as e:
            self.logger.error(f"Error validating curved touch regions: {e}")
            # Return original regions on error
            return new_regions
    
    def _get_curved_layout_performance_metrics(self) -> dict:
        """
        Get performance metrics for curved layout operations.
        
        Returns:
            dict: Performance metrics including cache usage and timing data
        """
        try:
            metrics = {
                'cache_usage': {
                    'circular_layout_cache_size': len(getattr(self, '_circular_layout_cache', {})),
                    'circular_regions_cache_size': len(getattr(self, '_circular_regions_cache', {})),
                    'device_cache_size': len(getattr(self, '_device_item_cache', {}))
                },
                'optimization_status': {
                    'circular_regions_precomputed': hasattr(self, '_circular_regions_cache'),
                    'layout_caching_enabled': hasattr(self, '_circular_layout_cache'),
                    'device_surface_caching': hasattr(self, '_device_item_cache')
                },
                'memory_usage': {
                    'total_cached_objects': (
                        len(getattr(self, '_circular_layout_cache', {})) +
                        len(getattr(self, '_circular_regions_cache', {})) +
                        len(getattr(self, '_device_item_cache', {}))
                    )
                }
            }
            
            # Calculate cache efficiency if we have usage data
            if hasattr(self, '_layout_cache_hits') and hasattr(self, '_layout_cache_misses'):
                total_requests = self._layout_cache_hits + self._layout_cache_misses
                if total_requests > 0:
                    metrics['cache_efficiency'] = {
                        'hit_rate': (self._layout_cache_hits / total_requests) * 100,
                        'total_requests': total_requests,
                        'hits': self._layout_cache_hits,
                        'misses': self._layout_cache_misses
                    }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting curved layout performance metrics: {e}")
            return {'error': str(e)}
    
    def _optimize_curved_layout_cache(self) -> None:
        """
        Optimize curved layout caches for memory and performance.
        
        Cleans up old cache entries and reorganizes data for better performance.
        """
        try:
            optimizations_performed = []
            
            # Optimize circular layout cache
            if hasattr(self, '_circular_layout_cache'):
                cache_size = len(self._circular_layout_cache)
                if cache_size > 50:
                    # Keep only the most recently used entries
                    # Since we don't track usage, keep entries with 'curved_' prefix (most common)
                    curved_keys = [k for k in self._circular_layout_cache.keys() if k.startswith('curved_')]
                    other_keys = [k for k in self._circular_layout_cache.keys() if not k.startswith('curved_')]
                    
                    # Remove excess other_keys first
                    keys_to_remove = other_keys[:-25] if len(other_keys) > 25 else []
                    for key in keys_to_remove:
                        del self._circular_layout_cache[key]
                    
                    optimizations_performed.append(f"Trimmed circular layout cache: {cache_size} -> {len(self._circular_layout_cache)}")
            
            # Optimize device cache
            if hasattr(self, '_device_item_cache'):
                cache_size = len(self._device_item_cache)
                if cache_size > 40:
                    # Keep curved device items preferentially
                    curved_device_keys = [k for k in self._device_item_cache.keys() if k.startswith('curved_')]
                    other_device_keys = [k for k in self._device_item_cache.keys() if not k.startswith('curved_')]
                    
                    # Remove excess non-curved entries first
                    keys_to_remove = other_device_keys[:-20] if len(other_device_keys) > 20 else []
                    for key in keys_to_remove:
                        del self._device_item_cache[key]
                    
                    optimizations_performed.append(f"Trimmed device cache: {cache_size} -> {len(self._device_item_cache)}")
            
            # Initialize cache tracking if not present
            if not hasattr(self, '_layout_cache_hits'):
                self._layout_cache_hits = 0
                self._layout_cache_misses = 0
                optimizations_performed.append("Initialized cache hit/miss tracking")
            
            if optimizations_performed:
                self.logger.info(f"Curved layout cache optimizations: {'; '.join(optimizations_performed)}")
            else:
                self.logger.debug("Curved layout caches are within optimal size limits")
                
        except Exception as e:
            self.logger.error(f"Error optimizing curved layout cache: {e}")
    
    # Control visibility and interaction management methods
    
    def _update_control_visibility(self, force_visible: bool = False) -> None:
        """
        Update control visibility based on interaction timing and auto-hide settings.
        
        Args:
            force_visible: If True, immediately show controls regardless of timing
        """
        try:
            with self._control_visibility_lock:
                current_time = time.time()
                
                if force_visible:
                    self._controls_visible = True
                    self._control_alpha = 255
                    self._last_interaction_time = current_time
                    self.logger.debug("Controls forced visible")
                    return
                
                # Calculate time since last interaction
                time_since_interaction = current_time - self._last_interaction_time
                
                if time_since_interaction >= self._control_auto_hide_delay:
                    # Controls should be hidden or fading
                    fade_start_time = self._last_interaction_time + self._control_auto_hide_delay
                    fade_elapsed = current_time - fade_start_time
                    
                    if fade_elapsed >= self._control_fade_duration:
                        # Fully faded
                        self._controls_visible = False
                        self._control_alpha = 0
                    else:
                        # Fading in progress
                        fade_progress = fade_elapsed / self._control_fade_duration
                        self._control_alpha = int(255 * (1.0 - fade_progress))
                        self._controls_visible = True  # Still visible during fade
                else:
                    # Controls should be fully visible
                    self._controls_visible = True
                    self._control_alpha = 255
                
        except Exception as e:
            self.logger.error(f"Error updating control visibility: {e}")
    
    def _register_interaction(self) -> None:
        """Register a user interaction to reset control auto-hide timer."""
        try:
            with self._control_visibility_lock:
                self._last_interaction_time = time.time()
                was_hidden = not self._controls_visible or self._control_alpha < 255
                
                self._controls_visible = True
                self._control_alpha = 255
                
                if was_hidden:
                    self.logger.debug("Controls shown due to user interaction")
                    
        except Exception as e:
            self.logger.error(f"Error registering interaction: {e}")
    
    def _get_control_alpha(self) -> int:
        """Get current control alpha value for rendering."""
        try:
            with self._control_visibility_lock:
                return self._control_alpha
        except Exception as e:
            self.logger.error(f"Error getting control alpha: {e}")
            return 255
    
    def _are_controls_visible(self) -> bool:
        """Check if controls should be rendered."""
        try:
            with self._control_visibility_lock:
                return self._controls_visible
        except Exception as e:
            self.logger.error(f"Error checking control visibility: {e}")
            return True
    
    def _render_compact_floating_control_bar(self, surface) -> list:
        """
        Render compact floating control bar with unified segmented design.
        
        Returns:
            list: Touch regions for the control bar segments
        """
        control_regions = []
        
        try:
            # Update control visibility
            self._update_control_visibility()
            
            if not self._are_controls_visible():
                return control_regions
            
            control_alpha = self._get_control_alpha()
            if control_alpha <= 0:
                return control_regions
            
            # Control bar dimensions and positioning
            bar_y = 65
            bar_height = 30
            segment_width = 80
            separator_width = 2
            total_width = (segment_width * 2) + separator_width
            bar_x = self.display_center[0] - total_width // 2
            
            # Ensure control bar fits within safe circular area
            max_x = self.display_center[0] + self.display_safe_radius - 10
            min_x = self.display_center[0] - self.display_safe_radius + 10
            
            if bar_x + total_width > max_x:
                bar_x = max_x - total_width
            elif bar_x < min_x:
                bar_x = min_x
            
            # Create control surface with alpha
            control_surface = pygame.Surface((total_width, bar_height), pygame.SRCALPHA)
            
            # Left segment (Filter Toggle)
            left_segment = pygame.Rect(0, 0, segment_width, bar_height)
            filter_active = self.show_all_devices
            left_color = (*self.colors['warning'][:3], control_alpha) if filter_active else (*self.colors['primary'][:3], control_alpha)
            try:
                pygame.draw.rect(control_surface, left_color[:3], left_segment, border_radius=6)
            except TypeError:
                pygame.draw.rect(control_surface, left_color[:3], left_segment)
            
            # Filter text with scaled font (18px from FONT_BUTTON 20px)
            try:
                filter_font = get_font_manager().get_font(18)
                if not filter_font:
                    filter_font = pygame.font.Font(None, 18)
            except Exception as e:
                self.logger.error(f"Error getting filter font: {e}")
                filter_font = pygame.font.Font(None, 18)
            
            filter_text = "All" if filter_active else "ELM327"
            filter_surface = filter_font.render(filter_text, True, (255, 255, 255))
            filter_surface_alpha = pygame.Surface(filter_surface.get_size(), pygame.SRCALPHA)
            filter_surface_alpha.blit(filter_surface, (0, 0))
            filter_surface_alpha.set_alpha(control_alpha)
            
            filter_rect = filter_surface_alpha.get_rect(center=left_segment.center)
            control_surface.blit(filter_surface_alpha, filter_rect)
            
            # Segment separator
            separator_x = segment_width
            separator_rect = pygame.Rect(separator_x, 4, separator_width, bar_height - 8)
            separator_color = (*self.colors['border'][:3], int(control_alpha * 0.6))
            pygame.draw.rect(control_surface, separator_color[:3], separator_rect)
            
            # Right segment (Manual Entry)
            right_segment = pygame.Rect(segment_width + separator_width, 0, segment_width, bar_height)
            right_color = (*self.colors['border'][:3], control_alpha)
            try:
                pygame.draw.rect(control_surface, right_color[:3], right_segment, border_radius=6)
            except TypeError:
                pygame.draw.rect(control_surface, right_color[:3], right_segment)
            
            # Manual entry text
            try:
                manual_font = get_font_manager().get_font(18)
                if not manual_font:
                    manual_font = pygame.font.Font(None, 18)
            except Exception as e:
                self.logger.error(f"Error getting manual font: {e}")
                manual_font = pygame.font.Font(None, 18)
            
            manual_surface = manual_font.render("Manual", True, self.colors['text'])
            manual_surface_alpha = pygame.Surface(manual_surface.get_size(), pygame.SRCALPHA)
            manual_surface_alpha.blit(manual_surface, (0, 0))
            manual_surface_alpha.set_alpha(control_alpha)
            
            manual_rect = manual_surface_alpha.get_rect(center=right_segment.center)
            control_surface.blit(manual_surface_alpha, manual_rect)
            
            # Set alpha for entire control surface
            control_surface.set_alpha(control_alpha)
            
            # Blit to main surface
            surface.blit(control_surface, (bar_x, bar_y))
            
            # Create touch regions with expanded bounds (10px extension)
            left_touch = pygame.Rect(bar_x - 10, bar_y - 5, segment_width + 10, bar_height + 10)
            right_touch = pygame.Rect(bar_x + segment_width + separator_width - 5, bar_y - 5, 
                                    segment_width + 10, bar_height + 10)
            
            control_regions.append(("toggle_filter", left_touch))
            control_regions.append(("manual_entry", right_touch))
            
            self.logger.debug(f"Rendered compact control bar at ({bar_x}, {bar_y}) with alpha {control_alpha}")
            
        except Exception as e:
            self.logger.error(f"Error rendering compact floating control bar: {e}")
        
        return control_regions
    
    def _render_compact_navigation_buttons(self, surface) -> list:
        """
        Render compact navigation buttons using standardized button system.
        
        Returns:
            list: Touch regions for navigation buttons
        """
        nav_regions = []
        
        try:
            # Update control visibility
            if not self._are_controls_visible():
                return nav_regions
            
            control_alpha = self._get_control_alpha()
            if control_alpha <= 0:
                return nav_regions
            
            # Get button renderer
            button_renderer = get_button_renderer()
            
            # Custom colors for semi-transparent buttons (RGB only, alpha handled separately)
            back_colors = {
                'background': self.colors['border'][:3],
                'border': self.colors['border'][:3],
                'text': self.colors['text'][:3]
            }
            
            refresh_colors = {
                'background': self.colors['primary'][:3],
                'border': self.colors['primary'][:3],
                'text': (255, 255, 255)
            }
            
            # Back button - positioned at 225° (bottom-left) with radius 180px
            try:
                visual_rect, touch_rect = button_renderer.render_button(
                    surface=surface,
                    position=(0, 0),  # Will be overridden by circular_position
                    text="Back",
                    button_size=ButtonSize.SMALL,  # 60x30 standardized size
                    button_id="back",
                    state=ButtonState.NORMAL,
                    colors=back_colors,
                    circular_position=(225, 180)  # angle, radius
                )
                
                # Add to touch regions
                nav_regions.append(("back", touch_rect))
                
            except Exception as e:
                self.logger.error(f"Error rendering back button: {e}")
            
            # Refresh button - positioned at 315° (bottom-right) with radius 180px
            try:
                visual_rect, touch_rect = button_renderer.render_button(
                    surface=surface,
                    position=(0, 0),  # Will be overridden by circular_position
                    text="Refresh",
                    button_size=ButtonSize.SMALL,  # 60x30 standardized size
                    button_id="refresh",
                    state=ButtonState.NORMAL,
                    colors=refresh_colors,
                    circular_position=(315, 180)  # angle, radius
                )
                
                # Add to touch regions
                nav_regions.append(("refresh", touch_rect))
                
            except Exception as e:
                self.logger.error(f"Error rendering refresh button: {e}")
            
            self.logger.debug(f"Rendered standardized navigation buttons with alpha {control_alpha}")
            
        except Exception as e:
            self.logger.error(f"Error rendering compact navigation buttons: {e}")
        
        return nav_regions
    
    # Thread-safe touch region management methods
    
    def _clear_touch_regions_safe(self) -> None:
        """Thread-safe method to clear all touch regions.
        
        Prevents race conditions between display rendering and touch handling threads.
        """
        try:
            with self._touch_regions_lock:
                self.touch_regions.clear()
        except Exception as e:
            self.logger.error(f"Error clearing touch regions: {e}")
    
    def _add_touch_region_safe(self, region_data: tuple) -> None:
        """Thread-safe method to add a single touch region.
        
        Args:
            region_data: Tuple containing region information (id, rect, [optional_data])
        """
        try:
            with self._touch_regions_lock:
                self.touch_regions.append(region_data)
        except Exception as e:
            self.logger.error(f"Error adding touch region: {e}")
    
    def _update_touch_regions_safe(self, new_regions: list) -> None:
        """Thread-safe atomic method to replace all touch regions.
        
        Prevents empty region windows by atomically replacing the entire list.
        
        Args:
            new_regions: List of region tuples to replace current regions
        """
        try:
            with self._touch_regions_lock:
                self.touch_regions.clear()
                self.touch_regions.extend(new_regions)
        except Exception as e:
            self.logger.error(f"Error updating touch regions: {e}")
    
    def _clear_device_cache(self) -> None:
        """Clear the device item rendering cache to free memory."""
        try:
            with self._device_cache_lock:
                cache_size = len(self._device_item_cache)
                self._device_item_cache.clear()
                if cache_size > 0:
                    self.logger.debug(f"Cleared device cache ({cache_size} items)")
        except Exception as e:
            self.logger.error(f"Error clearing device cache: {e}")
    
    def get_device_list_metrics(self) -> dict:
        """Get performance metrics for device list rendering."""
        try:
            with self._device_cache_lock:
                return {
                    'cache_size': len(self._device_item_cache),
                    'last_render_time': self._last_render_time,
                    'compact_layout': True,
                    'max_visible_devices': 8,
                    'item_height': 45,
                    'item_spacing': 3
                }
        except Exception as e:
            self.logger.error(f"Error getting device list metrics: {e}")
            return {'error': str(e)}
    
    def start_setup(self) -> None:
        """Start the setup process"""
        self.logger.info("Starting Bluetooth setup")
        
        # Determine starting screen through state coordinator
        from ..comm.device_store import DeviceStore
        device_store = DeviceStore()
        if device_store.is_first_run():
            self.state_coordinator.transition_to_screen(SetupScreen.WELCOME)
        else:
            self.state_coordinator.transition_to_screen(SetupScreen.CURRENT_DEVICE)
        
        # Start setup thread
        self._setup_thread = threading.Thread(target=self._setup_loop, name='SetupManager')
        self._setup_thread.start()
    
    def stop_setup(self) -> None:
        """Stop the setup process and cancel all async operations"""
        self._shutdown_event.set()
        
        # Cancel Bluetooth operations
        self.bluetooth_interface.cancel_operations()
        
        if self._setup_thread:
            self._setup_thread.join()
        
        self.logger.info("Setup stopped - all operations cancelled")
    
    def _setup_loop(self) -> None:
        """Main setup processing loop"""
        while not self._shutdown_event.is_set():
            try:
                self.thread_manager.update_heartbeat('setup')
                
                # Update state coordinator animation
                self.state_coordinator.update_animation(0.05)
                
                # Handle auto-discovery if needed
                state = self.state_coordinator.get_state()
                if (state.current_screen == SetupScreen.DISCOVERY and 
                    state.pairing_status == PairingStatus.IDLE):
                    self.bluetooth_interface.start_discovery(
                        state, 
                        show_all_devices=self.state_coordinator.show_all_devices
                    )
                
                time.sleep(0.05)
                
            except Exception as e:
                self.logger.error(f"Setup loop error: {e}", exc_info=True)
                time.sleep(1.0)
    
    def _invalidate_render_cache(self, screen_type: SetupScreen = None) -> None:
        """Invalidate render cache for specific screen or all screens"""
        with self._render_cache_lock:
            if screen_type is None:
                # Invalidate all cached screens
                self._screen_render_cache.clear()
                self._screen_needs_refresh = True
                self.logger.debug("Invalidated all screen render cache")
            else:
                # Invalidate specific screen
                if screen_type in self._screen_render_cache:
                    del self._screen_render_cache[screen_type]
                    self.logger.debug(f"Invalidated render cache for {screen_type.name}")
                
                # Mark as needing refresh if it's the current screen
                if screen_type == self.state.current_screen:
                    self._screen_needs_refresh = True
    
    def _needs_screen_render(self) -> bool:
        """Check if current screen needs to be rendered"""
        with self._render_cache_lock:
            # Always render if explicitly marked as needing refresh
            if self._screen_needs_refresh:
                return True
            
            # Check if screen has changed
            if self._last_rendered_screen != self.state.current_screen:
                return True
            
            # Check if current screen is cached
            return self.state.current_screen not in self._screen_render_cache
    
    def _update_cached_screen_touch_regions(self) -> None:
        """Update touch regions for cached screens without re-rendering
        
        This method ensures touch regions are properly set even when using 
        cached renders, which is critical for touch event handling.
        """
        try:
            # Update touch regions based on current screen
            if self.state.current_screen == SetupScreen.WELCOME:
                # Welcome screen has a continue button
                new_regions = []
                continue_btn = pygame.Rect(140, 380, 200, 60)
                new_regions.append(("continue", continue_btn))
                self._update_touch_regions_safe(new_regions)
                self.logger.debug("Updated touch regions for cached WELCOME screen")
                
            elif self.state.current_screen == SetupScreen.COMPLETE:
                # Complete screen has a start app button
                new_regions = []
                start_btn = pygame.Rect(140, 380, 200, 60)
                new_regions.append(("start_app", start_btn))
                self._update_touch_regions_safe(new_regions)
                self.logger.debug("Updated touch regions for cached COMPLETE screen")
                
            elif self.state.current_screen == SetupScreen.CURRENT_DEVICE:
                # Current device screen has multiple buttons
                new_regions = []
                
                # Test button
                test_btn = pygame.Rect(60, 300, 160, 50)
                new_regions.append(("test", test_btn))
                
                # Change button  
                change_btn = pygame.Rect(260, 300, 160, 50)
                new_regions.append(("change", change_btn))
                
                # Exit button
                exit_btn = pygame.Rect(140, 380, 200, 60)
                new_regions.append(("exit", exit_btn))
                
                self._update_touch_regions_safe(new_regions)
                self.logger.debug("Updated touch regions for cached CURRENT_DEVICE screen")
                
            else:
                # For dynamic screens or screens not cached, clear touch regions
                # They will be updated when the screen is actually rendered
                self._update_touch_regions_safe([])
                self.logger.debug(f"Cleared touch regions for cached {self.state.current_screen.name} screen")
                
        except Exception as e:
            self.logger.error(f"Error updating cached screen touch regions: {e}", exc_info=True)
    
    def render(self, target_surface=None) -> None:
        """Render the current setup screen with caching to prevent unnecessary re-renders"""
        try:
            # Use provided surface or fallback to self.surface
            surface = target_surface if target_surface is not None else self.surface
            
            # Check if we need to render the current screen
            if not self._needs_screen_render():
                # Use cached render if available
                with self._render_cache_lock:
                    if self.state.current_screen in self._screen_render_cache:
                        cached_surface = self._screen_render_cache[self.state.current_screen]
                        surface.blit(cached_surface, (0, 0))
                        self.logger.debug(f"Using cached render for {self.state.current_screen.name}")
                        
                        # CRITICAL FIX: Update touch regions even when using cached render
                        # The cached render doesn't execute the individual render methods
                        # which contain the touch region updates, so we need to update them here
                        self._update_cached_screen_touch_regions()
                        return
            
            # Create a surface for caching the render
            cache_surface = surface.copy()
            cache_surface.fill(self.colors['background'])
            
            # Render the appropriate screen
            if self.state.current_screen == SetupScreen.WELCOME:
                self._render_welcome_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.DISCOVERY:
                self._render_discovery_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.DEVICE_LIST:
                self._render_device_list_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.PAIRING:
                self._render_pairing_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.TEST:
                self._render_test_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.COMPLETE:
                self._render_complete_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.CURRENT_DEVICE:
                self._render_current_device_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.DEVICE_MANAGEMENT:
                self._render_device_management_screen(cache_surface)
            elif self.state.current_screen == SetupScreen.CONFIRMATION:
                self._render_confirmation_screen(cache_surface)
            elif self.manual_entry_mode:
                self._render_manual_entry_screen(cache_surface)
            
            # Cache the rendered screen (except for dynamic screens like DISCOVERY and DEVICE_LIST)
            should_cache = self.state.current_screen in [
                SetupScreen.WELCOME, SetupScreen.PAIRING, SetupScreen.TEST, 
                SetupScreen.COMPLETE, SetupScreen.CURRENT_DEVICE, SetupScreen.CONFIRMATION
            ]
            
            if should_cache:
                with self._render_cache_lock:
                    self._screen_render_cache[self.state.current_screen] = cache_surface.copy()
                    self._screen_needs_refresh = False
                    self._last_rendered_screen = self.state.current_screen
                    self.logger.debug(f"Cached render for {self.state.current_screen.name}")
            else:
                # For dynamic screens, don't cache but still update state
                with self._render_cache_lock:
                    self._screen_needs_refresh = False
                    self._last_rendered_screen = self.state.current_screen
            
            # Copy the rendered surface to the target
            surface.blit(cache_surface, (0, 0))
                
        except Exception as e:
            self.logger.error(f"Render error: {e}", exc_info=True)
    
    def _render_welcome_screen(self, surface) -> None:
        """Render the welcome screen"""
        # Build regions list first, then atomically update
        new_regions = []
        
        # Ensure font is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Title using typography system (FONT_TITLE = 36px, was 72px)
        try:
            font_large = get_title_display_font()
            if font_large:
                self.logger.debug(f"Using title font ({TypographyConstants.FONT_TITLE}px) for welcome screen")
                title = font_large.render("Welcome", True, self.colors['text'])
                title_rect = title.get_rect(center=(240, 100))
                
                # Validate title fits in circular display
                manager = get_font_manager()
                if manager.validate_text_fits_circular_display("Welcome", TypographyConstants.FONT_TITLE, (240, 100)):
                    surface.blit(title, title_rect)
                else:
                    self.logger.warning("Welcome title may not fit in circular display")
                    surface.blit(title, title_rect)  # Display anyway
            else:
                # Fallback to pygame font 
                self.logger.error("Failed to get title font, using fallback")
                font_large = pygame.font.Font(None, 48)  # Smaller fallback
                title = font_large.render("Welcome", True, self.colors['text'])
                title_rect = title.get_rect(center=(240, 100))
                surface.blit(title, title_rect)
        except Exception as e:
            self.logger.error(f"Error rendering welcome title: {e}")
            # Emergency fallback
            font_large = pygame.font.Font(None, 36)
            title = font_large.render("Welcome", True, self.colors['text'])
            title_rect = title.get_rect(center=(240, 100))
            surface.blit(title, title_rect)
        
        # Subtitle using heading typography (FONT_HEADING = 28px, was 48px)
        try:
            font_medium = get_heading_font()
            if font_medium:
                self.logger.debug(f"Using heading font ({TypographyConstants.FONT_HEADING}px) for welcome subtitle")
                subtitle = font_medium.render("Bluetooth Setup", True, self.colors['primary'])
                subtitle_rect = subtitle.get_rect(center=(240, 150))
                surface.blit(subtitle, subtitle_rect)
            else:
                # Fallback
                self.logger.warning("Failed to get heading font, using fallback")
                font_medium = pygame.font.Font(None, 32)
                subtitle = font_medium.render("Bluetooth Setup", True, self.colors['primary'])
                subtitle_rect = subtitle.get_rect(center=(240, 150))
                surface.blit(subtitle, subtitle_rect)
        except Exception as e:
            self.logger.error(f"Error rendering welcome subtitle: {e}")
        
        # Description using body typography (FONT_BODY = 20px, was 32px)
        try:
            font_small = get_body_font()
            if not font_small:
                self.logger.warning("Failed to get body font, using fallback")
                font_small = pygame.font.Font(None, 24)
        except Exception as e:
            self.logger.error(f"Error getting body font: {e}")
            font_small = pygame.font.Font(None, 24)
        desc_lines = [
            "This setup will help you connect",
            "to your ELM327 Bluetooth adapter.",
            "",
            "Make sure your adapter is powered",
            "on and in pairing mode."
        ]
        
        y_pos = 220
        for line in desc_lines:
            if line:
                text = font_small.render(line, True, self.colors['text_dim'])
                text_rect = text.get_rect(center=(240, y_pos))
                surface.blit(text, text_rect)
            y_pos += 35
        
        # Continue button
        continue_btn = pygame.Rect(140, 380, 200, 60)
        pygame.draw.rect(surface, self.colors['primary'], continue_btn, border_radius=10)
        
        # Button text using button typography (FONT_BUTTON = 20px, was 48px)
        try:
            btn_font = get_button_font()
            if not btn_font:
                self.logger.warning("Failed to get button font, using fallback")
                btn_font = pygame.font.Font(None, 24)
        except Exception as e:
            self.logger.error(f"Error getting button font: {e}")
            btn_font = pygame.font.Font(None, 24)
            
        btn_text = btn_font.render("Continue", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=continue_btn.center)
        surface.blit(btn_text, btn_text_rect)
        
        # Add to regions list
        new_regions.append(("continue", continue_btn))
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _render_discovery_screen(self, surface) -> None:
        """Render the device discovery screen"""
        # Build regions list first, then atomically update
        new_regions = []
        
        # Ensure font is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Title using title typography (FONT_TITLE = 36px, was 60px)
        try:
            font_large = get_title_display_font()
            if font_large:
                self.logger.debug(f"Using title font ({TypographyConstants.FONT_TITLE}px) for discovery screen")
                title = font_large.render("Scanning...", True, self.colors['text'])
                title_rect = title.get_rect(center=(240, 80))
                
                # Validate title fits
                manager = get_font_manager()
                if manager.validate_text_fits_circular_display("Scanning...", TypographyConstants.FONT_TITLE):
                    surface.blit(title, title_rect)
                else:
                    self.logger.warning("Discovery title may not fit in circular display")
                    surface.blit(title, title_rect)  # Display anyway
            else:
                # Fallback
                self.logger.error("Failed to get title font for discovery screen")
                font_large = pygame.font.Font(None, 36)
                title = font_large.render("Scanning...", True, self.colors['text'])
                title_rect = title.get_rect(center=(240, 80))
                surface.blit(title, title_rect)
        except Exception as e:
            self.logger.error(f"Error rendering discovery title: {e}")
        
        # Progress circle
        center = (240, 200)
        radius = 80
        
        # Background circle
        pygame.draw.circle(surface, self.colors['border'], center, radius, 4)
        
        # Progress arc - use async operation progress if available
        async_progress = self._get_active_operation_progress()
        if async_progress['has_active_operations']:
            progress = async_progress['progress']
        else:
            progress = self.state.discovery_progress
            
        if progress > 0:
            # Calculate arc parameters
            start_angle = -90  # Start from top
            end_angle = start_angle + (360 * progress)
            
            # Draw progress arc using multiple lines
            for angle in range(int(start_angle), int(end_angle), 2):
                angle_rad = math.radians(angle)
                x = center[0] + int((radius - 2) * math.cos(angle_rad))
                y = center[1] + int((radius - 2) * math.sin(angle_rad))
                pygame.draw.circle(surface, self.colors['primary'], (x, y), 2)
        
        # Progress text using heading typography (FONT_HEADING = 28px, was 48px)
        try:
            font_medium = get_heading_font()
            if not font_medium:
                self.logger.warning("Failed to get heading font for progress text")
                font_medium = pygame.font.Font(None, 32)
        except Exception as e:
            self.logger.error(f"Error getting heading font for progress: {e}")
            font_medium = pygame.font.Font(None, 32)
            
        progress_text = font_medium.render(f"{int(progress * 100)}%", True, self.colors['text'])
        progress_rect = progress_text.get_rect(center=center)
        surface.blit(progress_text, progress_rect)
        
        # Status text using body typography (FONT_BODY = 20px, was 32px)
        try:
            font_small = get_body_font()
            if not font_small:
                self.logger.warning("Failed to get body font for status text")
                font_small = pygame.font.Font(None, 24)
        except Exception as e:
            self.logger.error(f"Error getting body font for status: {e}")
            font_small = pygame.font.Font(None, 24)
        # Status text - show async operation message if available
        if async_progress['has_active_operations'] and async_progress['message']:
            status = async_progress['message']
            color = self.colors['primary']
        elif self.state.discovered_devices:
            status = f"Found {len(self.state.discovered_devices)} devices"
            color = self.colors['success']
        else:
            status = "Searching for ELM327 devices..."
            color = self.colors['text_dim']
        
        status_text = font_small.render(status, True, color)
        status_rect = status_text.get_rect(center=(240, 320))
        surface.blit(status_text, status_rect)
        
        # Cancel button using standardized button system
        try:
            button_renderer = get_button_renderer()
            
            cancel_colors = {
                'background': self.colors['danger'],
                'border': self.colors['danger'],
                'text': (255, 255, 255)
            }
            
            visual_rect, touch_rect = button_renderer.render_button(
                surface=surface,
                position=(240, 425),  # Center horizontally, bottom of screen
                text="Cancel",
                button_size=ButtonSize.LARGE,  # 120x40 for primary action
                button_id="cancel",
                state=ButtonState.NORMAL,
                colors=cancel_colors
            )
            
            # Add to regions list
            new_regions.append(("cancel", touch_rect))
            
        except Exception as e:
            self.logger.error(f"Error rendering cancel button: {e}")
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _render_compact_device_item(self, surface, device: BluetoothDevice, y_pos: int, 
                                   item_index: int, use_alternating_bg: bool = True) -> pygame.Rect:
        """
        Render a single device item in compact format (45px height).
        
        Args:
            surface: Pygame surface to draw on
            device: BluetoothDevice object to render
            y_pos: Y position for the item
            item_index: Index of the item (for alternating backgrounds)
            use_alternating_bg: Whether to use alternating background shading
            
        Returns:
            pygame.Rect: The touch region for this device item
        """
        start_time = time.time()
        
        try:
            # Compact item dimensions
            item_height = 45
            item_width = 440
            item_x = 20
            
            # Create cache key for this device item
            cache_key = f"{device.mac_address}_{item_index}_{use_alternating_bg}"
            
            # Check cache first (thread-safe)
            with self._device_cache_lock:
                if cache_key in self._device_item_cache:
                    cached_surface, cached_rect = self._device_item_cache[cache_key]
                    surface.blit(cached_surface, (item_x, y_pos))
                    # Return updated rect with current position
                    return pygame.Rect(item_x - 5, y_pos, item_width + 10, item_height)
            
            # Create item surface for caching
            item_surface = pygame.Surface((item_width, item_height), pygame.SRCALPHA)
            
            # Alternating background for visual separation
            if use_alternating_bg and item_index % 2 == 1:
                bg_color = (25, 25, 35)  # Slightly lighter than main surface
            else:
                bg_color = self.colors['surface']
            
            # Draw background with rounded corners
            item_rect = pygame.Rect(0, 0, item_width, item_height - 2)
            pygame.draw.rect(item_surface, bg_color, item_rect, border_radius=6)
            
            # Device type indicator - 6px colored circle (compact)
            indicator_color = self._get_device_type_color(device)
            indicator_center = (12, item_height // 2)
            pygame.draw.circle(item_surface, indicator_color, indicator_center, 6)
            
            # Device name - FONT_BODY (20px) at y_offset + 8px
            try:
                name_font = get_body_font()
                if not name_font:
                    name_font = pygame.font.Font(None, 20)
                self.logger.debug(f"Using body font ({TypographyConstants.FONT_BODY}px) for compact device name")
            except Exception as e:
                self.logger.error(f"Error getting body font for device name: {e}")
                name_font = pygame.font.Font(None, 20)
            
            # Truncate device name if too long to fit
            device_name = device.name
            name_text = name_font.render(device_name, True, self.colors['text'])
            max_name_width = 280  # Leave space for signal strength
            
            if name_text.get_width() > max_name_width:
                # Truncate name with ellipsis
                truncated_name = device_name
                while name_font.render(truncated_name + "...", True, self.colors['text']).get_width() > max_name_width:
                    truncated_name = truncated_name[:-1]
                    if len(truncated_name) <= 3:
                        break
                device_name = truncated_name + "..."
                name_text = name_font.render(device_name, True, self.colors['text'])
            
            name_rect = name_text.get_rect(midleft=(25, 8 + 6))  # 8px offset + half font height
            item_surface.blit(name_text, name_rect)
            
            # MAC address - FONT_MINIMAL (14px) at y_offset + 28px  
            try:
                mac_font = get_minimal_font()
                if not mac_font:
                    mac_font = pygame.font.Font(None, 14)
                self.logger.debug(f"Using minimal font ({TypographyConstants.FONT_MINIMAL}px) for compact MAC address")
            except Exception as e:
                self.logger.error(f"Error getting minimal font for MAC address: {e}")
                mac_font = pygame.font.Font(None, 14)
            
            mac_text = mac_font.render(device.mac_address, True, self.colors['text_dim'])
            mac_rect = mac_text.get_rect(midleft=(25, 28 + 4))  # 28px offset + half font height
            item_surface.blit(mac_text, mac_rect)
            
            # Signal strength - numeric percentage (16px) instead of bars
            signal_percentage = max(0, min(100, int((device.signal_strength + 100) * 1.25)))  # Convert RSSI to %
            try:
                signal_font = get_label_small_font()
                if not signal_font:
                    signal_font = pygame.font.Font(None, 16)
            except Exception as e:
                self.logger.error(f"Error getting signal font: {e}")
                signal_font = pygame.font.Font(None, 16)
            
            # Color code signal strength
            if signal_percentage >= 70:
                signal_color = self.colors['success']
            elif signal_percentage >= 40:
                signal_color = self.colors['warning']
            else:
                signal_color = self.colors['danger']
            
            signal_text = signal_font.render(f"{signal_percentage}%", True, signal_color)
            signal_rect = signal_text.get_rect(midright=(item_width - 10, item_height // 2))
            item_surface.blit(signal_text, signal_rect)
            
            # Cache the rendered item (limit cache size)
            with self._device_cache_lock:
                if len(self._device_item_cache) > 50:  # Limit cache size
                    # Remove oldest entries
                    cache_keys = list(self._device_item_cache.keys())
                    for old_key in cache_keys[:20]:
                        del self._device_item_cache[old_key]
                
                self._device_item_cache[cache_key] = (item_surface, item_rect)
            
            # Blit to main surface
            surface.blit(item_surface, (item_x, y_pos))
            
            # Create extended touch region (5px beyond visual bounds)
            touch_rect = pygame.Rect(item_x - 5, y_pos, item_width + 10, item_height)
            
            # Log performance for slow renders
            render_time = time.time() - start_time
            if render_time > 0.01:  # > 10ms
                self.logger.warning(f"Slow compact device item render: {render_time*1000:.1f}ms for {device.name}")
            
            return touch_rect
            
        except Exception as e:
            self.logger.error(f"Error rendering compact device item for {device.name}: {e}")
            # Return fallback touch rect
            return pygame.Rect(20, y_pos, 440, 45)
    
    def _render_device_list_screen(self, surface) -> None:
        """Render the enhanced device selection screen"""
        # Build regions list first, then atomically update
        new_regions = []
        
        # Ensure font is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Title with filter indicator
        font_large = pygame.font.Font(None, 44)
        title_text = "All Devices" if self.show_all_devices else "ELM327 Devices"
        title = font_large.render(title_text, True, self.colors['text'])
        title_rect = title.get_rect(center=(240, 35))
        surface.blit(title, title_rect)
        
        # Render compact floating control bar (Filter + Manual Entry)
        control_regions = self._render_compact_floating_control_bar(surface)
        new_regions.extend(control_regions)
        
        # Device list
        if not self.state.discovered_devices:
            # No devices found using body typography (FONT_BODY = 20px, was 36px)
            try:
                font_medium = get_body_font()
                if not font_medium:
                    font_medium = pygame.font.Font(None, 24)
            except Exception as e:
                self.logger.error(f"Error getting body font for no devices message: {e}")
                font_medium = pygame.font.Font(None, 24)
            no_devices = font_medium.render("No devices found", True, self.colors['text_dim'])
            no_devices_rect = no_devices.get_rect(center=(240, 200))
            surface.blit(no_devices, no_devices_rect)
            
            # Retry button
            retry_btn = pygame.Rect(140, 300, 200, 50)
            pygame.draw.rect(surface, self.colors['primary'], retry_btn, border_radius=8)
            
            # Retry button using button typography
            try:
                retry_font = get_button_font()
                if not retry_font:
                    retry_font = pygame.font.Font(None, 24)
            except Exception as e:
                self.logger.error(f"Error getting button font for retry: {e}")
                retry_font = pygame.font.Font(None, 24)
            btn_text = retry_font.render("Retry Scan", True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=retry_btn.center)
            surface.blit(btn_text, btn_text_rect)
            
            # Add to regions list
            new_regions.append(("retry", retry_btn))
        else:
            # Render curved device list optimized for circular display
            render_start_time = time.time()
            start_y = 100  # Start after header
            item_height = 45  # Compact height
            item_spacing = 3   # Spacing between items
            max_visible_devices = 6  # Adjusted for curved layout (6 fits well within safe radius)
            
            self.logger.debug(f"Rendering curved device list: {len(self.state.discovered_devices)} devices")
            
            # Calculate curved layout for all visible devices
            device_count = min(len(self.state.discovered_devices), max_visible_devices)
            layout_data = self._calculate_curved_list_layout(
                device_count, start_y, item_height, item_spacing
            )
            
            # Render circular debug overlay if debug logging enabled
            self._render_circular_debug_overlay(surface)
            
            devices_rendered = 0
            for i, device in enumerate(self.state.discovered_devices):
                if i >= device_count:
                    break
                
                # Get layout data for this item
                layout_item = layout_data[i]
                
                # Check if item is within safe area
                if not layout_item['in_safe_area']:
                    self.logger.warning(f"Device {i} ({device.name}) positioned outside safe area")
                
                try:
                    # Create curved device surface with visual hierarchy
                    device_surface, touch_rect = self._create_curved_device_surface(
                        device, layout_item, i, use_alternating_bg=True
                    )
                    
                    # Calculate final position accounting for scale factor
                    final_x = layout_item['x']
                    final_y = layout_item['y']
                    
                    # If surface is scaled, center it within the original bounds
                    if layout_item['scale'] < 1.0:
                        surface_width = device_surface.get_width()
                        surface_height = device_surface.get_height()
                        original_width = layout_item['width']
                        original_height = layout_item['height']
                        
                        # Center the scaled surface
                        final_x += (original_width - surface_width) // 2
                        final_y += (original_height - surface_height) // 2
                    
                    # Blit the curved device item to main surface
                    surface.blit(device_surface, (final_x, final_y))
                    
                    # Add to touch regions with curved bounds
                    new_regions.append(("select_device", touch_rect, device))
                    devices_rendered += 1
                    
                    # Log detailed positioning for debug
                    if self.logger.isEnabledFor(logging.DEBUG):
                        self.logger.debug(f"Rendered curved device {i}: {device.name} at "
                                        f"({final_x}, {final_y}) scale={layout_item['scale']:.2f}, "
                                        f"opacity={layout_item['opacity']:.2f}, "
                                        f"curve_offset={layout_item['curve_offset']}px")
                    
                except Exception as e:
                    self.logger.error(f"Error rendering curved device item {i}: {e}")
                    # Skip this device and continue
                    continue
            
            # Log rendering performance
            render_time = time.time() - render_start_time
            self.logger.info(f"Rendered {devices_rendered} curved device items in {render_time*1000:.1f}ms")
            
            # Performance warning threshold slightly higher for curved rendering
            if render_time > 0.15:  # > 150ms
                self.logger.warning(f"Slow curved device list rendering: {render_time*1000:.1f}ms for {devices_rendered} devices")
            
            # Show scrolling indicator if there are more devices (positioned in safe area)
            if len(self.state.discovered_devices) > devices_rendered:
                try:
                    scroll_font = get_minimal_font()
                    if not scroll_font:
                        scroll_font = pygame.font.Font(None, 12)
                    more_text = f"+{len(self.state.discovered_devices) - devices_rendered} more"
                    more_surface = scroll_font.render(more_text, True, self.colors['text_dim'])
                    
                    # Position scroll indicator within safe circular bounds
                    last_item = layout_data[-1] if layout_data else {'y': start_y, 'height': item_height}
                    scroll_y = last_item['y'] + last_item['height'] + 15
                    
                    # Ensure scroll indicator is within safe area
                    if scroll_y + 20 <= self.display_center[1] + self.display_safe_radius:
                        more_rect = more_surface.get_rect(center=(self.display_center[0], scroll_y))
                        surface.blit(more_surface, more_rect)
                    else:
                        # Fallback: position near bottom of safe area
                        fallback_y = self.display_center[1] + self.display_safe_radius - 30
                        more_rect = more_surface.get_rect(center=(self.display_center[0], fallback_y))
                        surface.blit(more_surface, more_rect)
                        
                except Exception as e:
                    self.logger.error(f"Error rendering curved scroll indicator: {e}")
        
        # Validate and optimize touch regions for curved layout
        if len(new_regions) > 0 and any(region[0] == "select_device" for region in new_regions):
            device_layout_data = layout_data if 'layout_data' in locals() else []
            new_regions = self._validate_curved_touch_regions(device_layout_data, new_regions)
        
        # Bottom buttons - positioned using circular layout
        
        # Render compact navigation buttons (Back + Refresh)
        nav_regions = self._render_compact_navigation_buttons(surface)
        new_regions.extend(nav_regions)
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _get_signal_bars(self, rssi: int) -> int:
        """Convert RSSI to signal bar count (0-4)"""
        if rssi >= -30:
            return 4
        elif rssi >= -50:
            return 3
        elif rssi >= -70:
            return 2
        elif rssi >= -80:
            return 1
        else:
            return 0
    
    def _get_device_type_color(self, device: BluetoothDevice) -> tuple:
        """Get color for device type indicator"""
        if hasattr(device, 'device_classification'):
            if device.device_classification == DeviceType.HIGHLY_LIKELY_ELM327:
                return self.colors['elm327_likely']
            elif device.device_classification == DeviceType.POSSIBLY_COMPATIBLE:
                return self.colors['possibly_compatible']
            else:
                return self.colors['unknown_device']
        else:
            # Fallback for devices without classification
            return self.colors['elm327_likely'] if device.device_type == 'ELM327' else self.colors['unknown_device']
    
    def _get_device_type_text(self, device: BluetoothDevice) -> str:
        """Get text description for device type"""
        if hasattr(device, 'device_classification'):
            if device.device_classification == DeviceType.HIGHLY_LIKELY_ELM327:
                return "ELM327"
            elif device.device_classification == DeviceType.POSSIBLY_COMPATIBLE:
                return "Compatible"
            else:
                return "Unknown"
        else:
            return device.device_type
    
    def _render_pairing_screen(self, surface) -> None:
        """Render the device pairing screen"""
        # Build regions list first, then atomically update
        new_regions = []
        
        if not self.state.selected_device:
            # Atomically update with empty regions
            self._update_touch_regions_safe(new_regions)
            return
        
        # Ensure font is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Title
        font_large = pygame.font.Font(None, 48)
        title = font_large.render("Connecting", True, self.colors['text'])
        title_rect = title.get_rect(center=(240, 60))
        surface.blit(title, title_rect)
        
        # Device info
        font_medium = pygame.font.Font(None, 36)
        device_name = font_medium.render(self.state.selected_device.name, True, self.colors['primary'])
        name_rect = device_name.get_rect(center=(240, 120))
        surface.blit(device_name, name_rect)
        
        font_small = pygame.font.Font(None, 28)
        device_mac = font_small.render(self.state.selected_device.mac_address, True, self.colors['text_dim'])
        mac_rect = device_mac.get_rect(center=(240, 150))
        surface.blit(device_mac, mac_rect)
        
        # Status indicator
        center = (240, 220)
        if self.state.pairing_status == PairingStatus.CONNECTING:
            # Animated spinner
            angle = self.animation_time * 180
            for i in range(8):
                dot_angle = angle + (i * 45)
                dot_angle_rad = math.radians(dot_angle)
                dot_x = center[0] + int(30 * math.cos(dot_angle_rad))
                dot_y = center[1] + int(30 * math.sin(dot_angle_rad))
                alpha = int(255 * (i / 8))
                color = (*self.colors['primary'][:3], alpha)
                pygame.draw.circle(surface, color, (dot_x, dot_y), 4)
        elif self.state.pairing_status == PairingStatus.SUCCESS:
            # Checkmark
            pygame.draw.circle(surface, self.colors['success'], center, 30, 4)
            # Simple checkmark lines
            pygame.draw.line(surface, self.colors['success'], 
                           (center[0] - 15, center[1]), (center[0] - 5, center[1] + 10), 4)
            pygame.draw.line(surface, self.colors['success'], 
                           (center[0] - 5, center[1] + 10), (center[0] + 15, center[1] - 10), 4)
        elif self.state.pairing_status == PairingStatus.FAILED:
            # X mark
            pygame.draw.circle(surface, self.colors['danger'], center, 30, 4)
            pygame.draw.line(surface, self.colors['danger'], 
                           (center[0] - 15, center[1] - 15), (center[0] + 15, center[1] + 15), 4)
            pygame.draw.line(surface, self.colors['danger'], 
                           (center[0] + 15, center[1] - 15), (center[0] - 15, center[1] + 15), 4)
        
        # Status text - use async operation message if available
        async_progress = self._get_active_operation_progress()
        if async_progress['has_active_operations'] and async_progress['message']:
            status_text = async_progress['message']
        else:
            status_messages = {
                PairingStatus.CONNECTING: "Connecting to device...",
                PairingStatus.PAIRING: "Pairing with device...",
                PairingStatus.TESTING: "Testing connection...",
                PairingStatus.SUCCESS: "Connection successful!",
                PairingStatus.FAILED: self.state.error_message or "Connection failed"
            }
            status_text = status_messages.get(self.state.pairing_status, "")
        if status_text:
            text = font_small.render(status_text, True, self.colors['text'])
            text_rect = text.get_rect(center=(240, 280))
            surface.blit(text, text_rect)
        
        # Action buttons
        if self.state.pairing_status == PairingStatus.SUCCESS:
            # Continue button
            continue_btn = pygame.Rect(140, 380, 200, 60)
            pygame.draw.rect(surface, self.colors['success'], continue_btn, border_radius=10)
            
            btn_text = font_medium.render("Continue", True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=continue_btn.center)
            surface.blit(btn_text, btn_text_rect)
            
            # Add to regions list
            new_regions.append(("continue", continue_btn))
        
        elif self.state.pairing_status == PairingStatus.FAILED:
            # Retry and Back buttons
            retry_btn = pygame.Rect(90, 380, 120, 50)
            pygame.draw.rect(surface, self.colors['warning'], retry_btn, border_radius=8)
            
            retry_text = pygame.font.Font(None, 32).render("Retry", True, (255, 255, 255))
            retry_text_rect = retry_text.get_rect(center=retry_btn.center)
            surface.blit(retry_text, retry_text_rect)
            
            back_btn = pygame.Rect(270, 380, 120, 50)
            pygame.draw.rect(surface, self.colors['border'], back_btn, border_radius=8)
            
            back_text = pygame.font.Font(None, 32).render("Back", True, self.colors['text'])
            back_text_rect = back_text.get_rect(center=back_btn.center)
            surface.blit(back_text, back_text_rect)
            
            # Add to regions list
            new_regions.append(("retry", retry_btn))
            new_regions.append(("back", back_btn))
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _render_current_device_screen(self, surface) -> None:
        """Render current device management screen"""
        # Build regions list first, then atomically update
        new_regions = []
        
        # Ensure font is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Title
        font_large = pygame.font.Font(None, 48)
        title = font_large.render("Current Device", True, self.colors['text'])
        title_rect = title.get_rect(center=(240, 40))
        surface.blit(title, title_rect)
        
        # Get current device
        current_device = self.device_store.get_primary_device()
        
        if current_device:
            # Device info panel
            panel_rect = pygame.Rect(40, 90, 400, 140)
            pygame.draw.rect(surface, self.colors['surface'], panel_rect, border_radius=10)
            
            # Device details
            font_medium = pygame.font.Font(None, 36)
            font_small = pygame.font.Font(None, 28)
            
            name_text = font_medium.render(current_device.name, True, self.colors['text'])
            name_rect = name_text.get_rect(midleft=(60, 120))
            surface.blit(name_text, name_rect)
            
            mac_text = font_small.render(current_device.mac_address, True, self.colors['text_dim'])
            mac_rect = mac_text.get_rect(midleft=(60, 150))
            surface.blit(mac_text, mac_rect)
            
            status_color = self.colors['success'] if current_device.connection_verified else self.colors['warning']
            status_text = "Verified" if current_device.connection_verified else "Not tested"
            status = font_small.render(f"Status: {status_text}", True, status_color)
            status_rect = status.get_rect(midleft=(60, 180))
            surface.blit(status, status_rect)
            
            # Action buttons
            y_pos = 270
            button_width = 180
            button_height = 45
            
            # Test Connection
            test_btn = pygame.Rect(60, y_pos, button_width, button_height)
            pygame.draw.rect(surface, self.colors['primary'], test_btn, border_radius=8)
            test_text = pygame.font.Font(None, 32).render("Test Connection", True, (255, 255, 255))
            test_text_rect = test_text.get_rect(center=test_btn.center)
            surface.blit(test_text, test_text_rect)
            new_regions.append(("test", test_btn))
            
            # Change Device
            change_btn = pygame.Rect(260, y_pos, button_width, button_height)
            pygame.draw.rect(surface, self.colors['warning'], change_btn, border_radius=8)
            change_text = pygame.font.Font(None, 32).render("Change Device", True, (255, 255, 255))
            change_text_rect = change_text.get_rect(center=change_btn.center)
            surface.blit(change_text, change_text_rect)
            new_regions.append(("change", change_btn))
            
            # Remove Device
            y_pos += 60
            remove_btn = pygame.Rect(160, y_pos, button_width, button_height)
            pygame.draw.rect(surface, self.colors['danger'], remove_btn, border_radius=8)
            remove_text = pygame.font.Font(None, 32).render("Remove Device", True, (255, 255, 255))
            remove_text_rect = remove_text.get_rect(center=remove_btn.center)
            surface.blit(remove_text, remove_text_rect)
            new_regions.append(("remove", remove_btn))
            
        else:
            # No device configured
            font_medium = pygame.font.Font(None, 36)
            no_device = font_medium.render("No device configured", True, self.colors['text_dim'])
            no_device_rect = no_device.get_rect(center=(240, 200))
            surface.blit(no_device, no_device_rect)
            
            # Add Device button
            add_btn = pygame.Rect(140, 280, 200, 60)
            pygame.draw.rect(surface, self.colors['primary'], add_btn, border_radius=10)
            
            add_text = font_medium.render("Add Device", True, (255, 255, 255))
            add_text_rect = add_text.get_rect(center=add_btn.center)
            surface.blit(add_text, add_text_rect)
            
            new_regions.append(("add", add_btn))
        
        # Exit button - positioned at bottom-center using circular layout
        try:
            exit_btn = self._position_in_circle(270, 145, (100, 40))  # 270° = bottom-center
        except Exception as e:
            self.logger.warning(f"Circular positioning failed for exit button: {e}")
            exit_btn = pygame.Rect(190, 420, 100, 40)  # Fallback to bottom-center rectangular
        pygame.draw.rect(surface, self.colors['border'], exit_btn, border_radius=8)
        
        exit_text = pygame.font.Font(None, 28).render("Exit Setup", True, self.colors['text'])
        exit_text_rect = exit_text.get_rect(center=exit_btn.center)
        surface.blit(exit_text, exit_text_rect)
        
        new_regions.append(("exit", exit_btn))
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _render_complete_screen(self, surface) -> None:
        """Render setup completion screen"""
        # Build regions list first, then atomically update
        new_regions = []
        
        # Ensure font is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Success icon
        center = (240, 140)
        pygame.draw.circle(surface, self.colors['success'], center, 50, 6)
        
        # Checkmark
        pygame.draw.line(surface, self.colors['success'], 
                        (center[0] - 25, center[1]), (center[0] - 10, center[1] + 15), 6)
        pygame.draw.line(surface, self.colors['success'], 
                        (center[0] - 10, center[1] + 15), (center[0] + 25, center[1] - 15), 6)
        
        # Title
        font_large = pygame.font.Font(None, 60)
        title = font_large.render("Setup Complete!", True, self.colors['success'])
        title_rect = title.get_rect(center=(240, 220))
        surface.blit(title, title_rect)
        
        # Description
        font_medium = pygame.font.Font(None, 32)
        desc_lines = [
            "Your ELM327 device has been",
            "successfully paired and tested.",
            "",
            "You can now start using the",
            "RPM display application."
        ]
        
        y_pos = 270
        for line in desc_lines:
            if line:
                text = font_medium.render(line, True, self.colors['text_dim'])
                text_rect = text.get_rect(center=(240, y_pos))
                surface.blit(text, text_rect)
            y_pos += 30
        
        # Start App button
        start_btn = pygame.Rect(140, 400, 200, 60)
        pygame.draw.rect(surface, self.colors['primary'], start_btn, border_radius=10)
        
        btn_text = pygame.font.Font(None, 40).render("Start App", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=start_btn.center)
        surface.blit(btn_text, btn_text_rect)
        
        new_regions.append(("start_app", start_btn))
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _start_discovery(self) -> None:
        """Start device discovery using async operation framework"""
        def discovery_task(progress_callback=None):
            """Discover devices in worker thread"""
            try:
                # Ensure Bluetooth pairing is initialized before starting discovery
                if not self._ensure_pairing_initialized():
                    self.logger.error("Cannot start discovery - Bluetooth pairing not available")
                    self.state.pairing_status = PairingStatus.FAILED
                    raise RuntimeError("Bluetooth pairing not available")
                
                if progress_callback:
                    progress_callback(0.1, "Starting device discovery...")
                
                self.state.pairing_status = PairingStatus.DISCOVERING
                self.state.discovery_progress = 0.0
                self.state.discovered_devices = []  # Clear previous results
                
                def internal_progress_callback(progress):
                    """Internal progress callback to update state and external callback"""
                    self.state.discovery_progress = progress
                    if progress_callback:
                        progress_callback(0.1 + (progress * 0.8), f"Discovering devices... {int(progress * 100)}%")
                
                def device_found_callback(device):
                    """Callback when a device is found"""
                    if device not in self.state.discovered_devices:
                        self.state.discovered_devices.append(device)
                        self.logger.debug(f"Found device: {device.name} ({device.address})")
                
                # Use timeout-aware discovery with progress reporting
                devices = self.pairing.discover_elm327_devices(
                    timeout=self.state.discovery_timeout,
                    progress_callback=internal_progress_callback,
                    device_found_callback=device_found_callback,
                    show_all_devices=self.show_all_devices
                )
                
                if progress_callback:
                    progress_callback(1.0, f"Discovery complete - found {len(devices)} devices")
                
                return devices
                
            except Exception as e:
                self.logger.error(f"Device discovery failed: {e}", exc_info=True)
                self.state.pairing_status = PairingStatus.FAILED
                raise
        
        def on_discovery_complete(operation):
            """Callback when discovery operation completes"""
            try:
                if operation.status == OperationStatus.COMPLETED:
                    devices = operation.result
                    self.state.discovered_devices = devices
                    self.state.pairing_status = PairingStatus.IDLE
                    
                    # Auto-transition to device list
                    self.state.current_screen = SetupScreen.DEVICE_LIST
                    self._invalidate_render_cache()  # Invalidate cache on screen change
                    
                    self.logger.info(f"Discovery completed - found {len(devices)} devices")
                elif operation.status == OperationStatus.FAILED:
                    self.logger.error(f"Discovery failed: {operation.error}")
                    self.state.pairing_status = PairingStatus.FAILED
                else:
                    self.logger.warning(f"Discovery ended with status: {operation.status}")
                    self.state.pairing_status = PairingStatus.IDLE
                
                # Remove from active operations
                if 'device_discovery' in self._active_operations:
                    del self._active_operations['device_discovery']
                    
            except Exception as e:
                self.logger.error(f"Error in discovery callback: {e}")
                self.state.pairing_status = PairingStatus.FAILED
        
        # Submit the discovery operation
        try:
            # Cancel any existing discovery operation
            if 'device_discovery' in self._active_operations:
                existing_op_id = self._active_operations['device_discovery']
                self.async_manager.cancel_operation(existing_op_id)
                self.logger.info(f"Cancelled existing discovery operation: {existing_op_id}")
            
            operation_id = self.async_manager.submit_operation(
                OperationType.DEVICE_DISCOVERY,
                discovery_task,
                progress_callback=on_discovery_complete
            )
            
            self._active_operations['device_discovery'] = operation_id
            self.logger.info(f"Device discovery started (operation: {operation_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to submit discovery operation: {e}")
            self.state.pairing_status = PairingStatus.FAILED
    
    def handle_touch_event(self, pos: Tuple[int, int]) -> Optional[SetupAction]:
        """Handle touch events and return action with thread-safe region access"""
        try:
            # Register interaction for control auto-hide
            self._register_interaction()
            
            # Thread-safe copy of touch regions to minimize lock contention
            with self._touch_regions_lock:
                regions_copy = list(self.touch_regions)
            
            region_count = len(regions_copy)
            self.logger.info(f"Setup touch event at {pos}, checking {region_count} regions")
            self.logger.debug(f"Current screen: {self.state.current_screen.name}")
            
            # Handle empty regions gracefully
            if region_count == 0:
                self.logger.debug("No touch regions available - screen may be updating")
                return None
            
            # Process regions using the thread-safe copy
            for i, region in enumerate(regions_copy):
                if len(region) >= 2:
                    action, rect = region[:2]
                    self.logger.debug(f"Region {i}: {action} at {rect}")
                    
                    if rect.collidepoint(pos):
                        self.logger.info(f"Touch hit region {i}: {action}")
                        action_result = self._handle_touch_action(action, region)
                        self.logger.info(f"Touch action result: {action_result}")
                        return action_result
                    else:
                        self.logger.debug(f"Touch missed region {i}: {action}")
            
            self.logger.info("Touch event did not hit any regions")
            return None
            
        except Exception as e:
            self.logger.error(f"Touch event handling error: {e}", exc_info=True)
            return None
    
    def _handle_touch_action(self, action: str, region: tuple) -> Optional[SetupAction]:
        """Handle specific touch actions"""
        try:
            if action == "continue":
                if self.state.current_screen == SetupScreen.WELCOME:
                    self.state.current_screen = SetupScreen.DISCOVERY
                    self._invalidate_render_cache()  # Invalidate cache on screen change
                elif self.state.current_screen == SetupScreen.PAIRING:
                    if self.state.pairing_status == PairingStatus.SUCCESS:
                        self._complete_pairing()
                return SetupAction.NEXT
            
            elif action == "cancel":
                self.pairing.cancel_discovery()
                self.state.current_screen = SetupScreen.WELCOME
                self._invalidate_render_cache()  # Invalidate cache on screen change
                return SetupAction.CANCEL
            
            elif action == "back":
                if self.state.current_screen == SetupScreen.DEVICE_LIST:
                    self.state.current_screen = SetupScreen.DISCOVERY
                    self._invalidate_render_cache()  # Invalidate cache on screen change
                elif self.state.current_screen == SetupScreen.PAIRING:
                    self.state.current_screen = SetupScreen.DEVICE_LIST
                    self._invalidate_render_cache()  # Invalidate cache on screen change
                return SetupAction.BACK
            
            elif action == "select_device" and len(region) > 2:
                device = region[2]
                self.state.selected_device = device
                self._start_pairing(device)
                return SetupAction.SELECT_DEVICE
            
            elif action == "retry":
                if self.state.current_screen == SetupScreen.DEVICE_LIST:
                    self.state.reset_discovery()
                    self.state.current_screen = SetupScreen.DISCOVERY
                    self._invalidate_render_cache()  # Invalidate cache on screen change
                elif self.state.current_screen == SetupScreen.PAIRING:
                    if self.state.selected_device:
                        self._start_pairing(self.state.selected_device)
                return SetupAction.RETRY
            
            elif action == "refresh":
                self.state.reset_discovery()
                self.state.current_screen = SetupScreen.DISCOVERY
                self._invalidate_render_cache()  # Invalidate cache on screen change
                return SetupAction.REFRESH
            
            elif action == "start_app":
                return SetupAction.EXIT_SETUP
            
            elif action == "test":
                if self.state.selected_device:
                    self._test_device_connection(self.state.selected_device)
                return SetupAction.TEST_CONNECTION
            
            elif action == "change":
                self.state.reset_discovery()
                self.state.current_screen = SetupScreen.DISCOVERY
                self._invalidate_render_cache()  # Invalidate cache on screen change
                return SetupAction.CHANGE_DEVICE
            
            elif action == "remove":
                current_device = self.device_store.get_primary_device()
                if current_device:
                    self.device_store.remove_device(current_device.mac_address)
                    self.state.current_screen = SetupScreen.CURRENT_DEVICE
                    self._invalidate_render_cache()  # Invalidate cache on screen change
                return SetupAction.REMOVE_DEVICE
            
            elif action == "add":
                self.state.reset_discovery()
                self.state.current_screen = SetupScreen.DISCOVERY
                self._invalidate_render_cache()  # Invalidate cache on screen change
                return SetupAction.ADD_DEVICE
            
            elif action == "exit":
                return SetupAction.EXIT_SETUP
            
            elif action == "toggle_filter":
                self.show_all_devices = not self.show_all_devices
                self.state.reset_discovery()
                self.state.current_screen = SetupScreen.DISCOVERY
                self._invalidate_render_cache()  # Invalidate cache on screen change
                return SetupAction.REFRESH
            
            elif action == "manual_entry":
                self.manual_entry_mode = True
                self.manual_mac_input = ""
                return SetupAction.MANUAL_ENTRY
            
            elif action == "cancel_manual":
                self.manual_entry_mode = False
                self.manual_mac_input = ""
                return SetupAction.CANCEL
            
            elif action == "connect_manual":
                if self._is_valid_mac_address(self.manual_mac_input):
                    # Create a manual device entry
                    from datetime import datetime
                    manual_device = BluetoothDevice(
                        name=f"Manual Entry ({self.manual_mac_input})",
                        mac_address=self.manual_mac_input,
                        signal_strength=-50,  # Default signal strength
                        device_type='Manual',
                        last_seen=datetime.now(),
                        is_paired=False,
                        connection_verified=False,
                        device_classification=DeviceType.POSSIBLY_COMPATIBLE
                    )
                    self.state.selected_device = manual_device
                    self.manual_entry_mode = False
                    self._start_pairing(manual_device)
                    return SetupAction.SELECT_DEVICE
                return None
            
            elif action == "key" and len(region) > 2:
                char = region[2]
                if char == 'Del':
                    if self.manual_mac_input:
                        self.manual_mac_input = self.manual_mac_input[:-1]
                else:
                    if len(self.manual_mac_input) < 17:  # Max MAC address length
                        self.manual_mac_input += char
                return None
            
        except Exception as e:
            self.logger.error(f"Touch action error: {e}")
        
        return None
    
    def _start_pairing(self, device: BluetoothDevice) -> None:
        """Start pairing with selected device using async operation framework"""
        def pairing_task(progress_callback=None):
            """Pair with device in worker thread"""
            try:
                # Ensure Bluetooth pairing is initialized
                if not self._ensure_pairing_initialized():
                    self.logger.error("Cannot start pairing - Bluetooth pairing not available")
                    self.state.pairing_status = PairingStatus.FAILED
                    raise RuntimeError("Bluetooth pairing not available")
                
                if progress_callback:
                    progress_callback(0.1, f"Starting pairing with {device.name}...")
                
                self.state.current_screen = SetupScreen.PAIRING
                self._invalidate_render_cache()  # Invalidate cache on screen change
                
                def status_callback(status, message):
                    """Internal status callback to update state"""
                    self.state.pairing_status = status
                    if status == PairingStatus.FAILED:
                        self.state.error_message = message
                    
                    # Update progress based on status
                    if status == PairingStatus.PAIRING:
                        if progress_callback:
                            progress_callback(0.5, f"Pairing with {device.name}...")
                    elif status == PairingStatus.SUCCESS:
                        if progress_callback:
                            progress_callback(1.0, f"Successfully paired with {device.name}")
                    elif status == PairingStatus.FAILED:
                        if progress_callback:
                            progress_callback(1.0, f"Failed to pair with {device.name}: {message}")
                
                # Start the pairing process
                success = self.pairing.pair_device(device, status_callback)
                
                return success
                
            except Exception as e:
                self.logger.error(f"Device pairing failed: {e}", exc_info=True)
                self.state.pairing_status = PairingStatus.FAILED
                self.state.error_message = str(e)
                raise
        
        def on_pairing_complete(operation):
            """Callback when pairing operation completes"""
            try:
                if operation.status == OperationStatus.COMPLETED:
                    success = operation.result
                    if success:
                        self.state.pairing_status = PairingStatus.SUCCESS
                        self.logger.info(f"Successfully paired with device: {device.name}")
                    else:
                        self.state.pairing_status = PairingStatus.FAILED
                        self.logger.error(f"Failed to pair with device: {device.name}")
                elif operation.status == OperationStatus.FAILED:
                    self.state.pairing_status = PairingStatus.FAILED
                    self.state.error_message = str(operation.error) if operation.error else "Unknown pairing error"
                    self.logger.error(f"Pairing operation failed: {operation.error}")
                else:
                    self.logger.warning(f"Pairing ended with status: {operation.status}")
                    self.state.pairing_status = PairingStatus.FAILED
                
                # Remove from active operations
                if 'device_pairing' in self._active_operations:
                    del self._active_operations['device_pairing']
                    
            except Exception as e:
                self.logger.error(f"Error in pairing callback: {e}")
                self.state.pairing_status = PairingStatus.FAILED
        
        # Submit the pairing operation
        try:
            # Cancel any existing pairing operation
            if 'device_pairing' in self._active_operations:
                existing_op_id = self._active_operations['device_pairing']
                self.async_manager.cancel_operation(existing_op_id)
                self.logger.info(f"Cancelled existing pairing operation: {existing_op_id}")
            
            operation_id = self.async_manager.submit_operation(
                OperationType.DEVICE_PAIRING,
                pairing_task,
                progress_callback=on_pairing_complete
            )
            
            self._active_operations['device_pairing'] = operation_id
            self.logger.info(f"Device pairing started (operation: {operation_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to submit pairing operation: {e}")
            self.state.pairing_status = PairingStatus.FAILED
    
    def _complete_pairing(self) -> None:
        """Complete the pairing process"""
        if self.state.selected_device:
            # Save device to store
            self.device_store.save_paired_device(self.state.selected_device, is_primary=True)
            
            # Mark setup as complete
            self.device_store.mark_setup_complete()
            self.state.setup_complete = True
            
            # Move to completion screen
            self.state.current_screen = SetupScreen.COMPLETE
            self._invalidate_render_cache()  # Invalidate cache on screen change
    
    def _test_device_connection(self, device: BluetoothDevice) -> None:
        """Test connection to a device using async operation framework"""
        def connection_test_task(progress_callback=None):
            """Test OBD connection in worker thread"""
            try:
                # Ensure Bluetooth pairing is initialized
                if not self._ensure_pairing_initialized():
                    self.logger.error("Cannot test connection - Bluetooth pairing not available")
                    self.state.pairing_status = PairingStatus.FAILED
                    raise RuntimeError("Bluetooth pairing not available")
                
                if progress_callback:
                    progress_callback(0.1, f"Starting connection test with {device.name}...")
                
                self.state.pairing_status = PairingStatus.TESTING
                
                def status_callback(message):
                    """Internal status callback to update state and progress"""
                    self.state.error_message = message
                    if progress_callback:
                        progress_callback(0.5, f"Testing connection: {message}")
                
                if progress_callback:
                    progress_callback(0.3, f"Connecting to {device.name}...")
                
                # Test the OBD connection
                success = self.pairing.test_obd_connection(device, status_callback)
                
                if progress_callback:
                    if success:
                        progress_callback(1.0, f"Connection test successful for {device.name}")
                    else:
                        progress_callback(1.0, f"Connection test failed for {device.name}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"OBD connection test failed: {e}", exc_info=True)
                self.state.pairing_status = PairingStatus.FAILED
                self.state.error_message = str(e)
                raise
        
        def on_connection_test_complete(operation):
            """Callback when connection test operation completes"""
            try:
                if operation.status == OperationStatus.COMPLETED:
                    success = operation.result
                    if success:
                        device.connection_verified = True
                        self.device_store.save_paired_device(device, is_primary=True)
                        self.state.pairing_status = PairingStatus.SUCCESS
                        self.logger.info(f"Successfully tested connection to device: {device.name}")
                    else:
                        self.state.pairing_status = PairingStatus.FAILED
                        self.logger.error(f"Connection test failed for device: {device.name}")
                elif operation.status == OperationStatus.FAILED:
                    self.state.pairing_status = PairingStatus.FAILED
                    self.state.error_message = str(operation.error) if operation.error else "Unknown connection error"
                    self.logger.error(f"Connection test operation failed: {operation.error}")
                else:
                    self.logger.warning(f"Connection test ended with status: {operation.status}")
                    self.state.pairing_status = PairingStatus.FAILED
                
                # Remove from active operations
                if 'obd_connection_test' in self._active_operations:
                    del self._active_operations['obd_connection_test']
                    
            except Exception as e:
                self.logger.error(f"Error in connection test callback: {e}")
                self.state.pairing_status = PairingStatus.FAILED
        
        # Submit the connection test operation
        try:
            # Cancel any existing connection test operation
            if 'obd_connection_test' in self._active_operations:
                existing_op_id = self._active_operations['obd_connection_test']
                self.async_manager.cancel_operation(existing_op_id)
                self.logger.info(f"Cancelled existing connection test operation: {existing_op_id}")
            
            operation_id = self.async_manager.submit_operation(
                OperationType.OBD_CONNECTION_TEST,
                connection_test_task,
                progress_callback=on_connection_test_complete
            )
            
            self._active_operations['obd_connection_test'] = operation_id
            self.logger.info(f"OBD connection test started (operation: {operation_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to submit connection test operation: {e}")
            self.state.pairing_status = PairingStatus.FAILED
    
    def is_setup_complete(self) -> bool:
        """Check if setup is complete"""
        return self.state.setup_complete or self.device_store.is_setup_complete()
    
    def _render_test_screen(self, surface) -> None:
        """Render test screen placeholder"""
        # Build regions list first, then atomically update
        new_regions = []
        
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(None, 48)
        text = font.render("Testing Connection...", True, self.colors['text'])
        text_rect = text.get_rect(center=(240, 240))
        surface.blit(text, text_rect)
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _render_device_management_screen(self, surface) -> None:
        """Render device management screen placeholder"""
        # Build regions list first, then atomically update
        new_regions = []
        
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(None, 48)
        text = font.render("Device Management", True, self.colors['text'])
        text_rect = text.get_rect(center=(240, 240))
        surface.blit(text, text_rect)
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _render_confirmation_screen(self, surface) -> None:
        """Render confirmation screen placeholder"""
        # Build regions list first, then atomically update
        new_regions = []
        
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(None, 48)
        text = font.render("Confirm Action", True, self.colors['text'])
        text_rect = text.get_rect(center=(240, 240))
        surface.blit(text, text_rect)
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _render_manual_entry_screen(self, surface) -> None:
        """Render manual MAC address entry screen"""
        # Build regions list first, then atomically update
        new_regions = []
        
        # Ensure font is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Title
        font_large = pygame.font.Font(None, 44)
        title = font_large.render("Manual Entry", True, self.colors['text'])
        title_rect = title.get_rect(center=(240, 40))
        surface.blit(title, title_rect)
        
        # Instructions
        font_small = pygame.font.Font(None, 28)
        instructions = [
            "Enter the MAC address of your",
            "ELM327 device manually:",
            "",
            "Format: XX:XX:XX:XX:XX:XX"
        ]
        
        y_pos = 80
        for line in instructions:
            if line:
                text = font_small.render(line, True, self.colors['text_dim'])
                text_rect = text.get_rect(center=(240, y_pos))
                surface.blit(text, text_rect)
            y_pos += 25
        
        # Input field - centered and sized for circular display
        input_width = 320  # Reduced width to fit better within circular bounds
        input_height = 50
        input_x = self.display_center[0] - (input_width // 2)  # Center horizontally
        input_y = 190
        
        input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
        pygame.draw.rect(surface, self.colors['surface'], input_rect, border_radius=8)
        pygame.draw.rect(surface, self.colors['primary'], input_rect, 2, border_radius=8)
        
        # Input text
        font_input = pygame.font.Font(None, 36)
        input_text = font_input.render(self.manual_mac_input, True, self.colors['text'])
        input_text_rect = input_text.get_rect(midleft=(input_x + 15, input_y + input_height // 2))
        surface.blit(input_text, input_text_rect)
        
        # Cursor
        cursor_x = input_text_rect.right + 5
        cursor_y = input_text_rect.centery
        if int(self.animation_time * 2) % 2:  # Blinking cursor
            pygame.draw.line(surface, self.colors['text'], (cursor_x, cursor_y - 15), (cursor_x, cursor_y + 15), 2)
        
        # Virtual keyboard optimized for circular display
        keyboard_chars = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['A', 'B', 'C', 'D', 'E', 'F', ':', 'Del']
        ]
        
        start_y = 275  # Moved up 5px to ensure second row stays within bounds
        for row_idx, row in enumerate(keyboard_chars):
            # Further optimized key width to ensure all keys fit within safe radius
            key_width = 37  # Reduced from 39px to ensure edge keys stay within bounds
            key_height = 35
            row_width = len(row) * key_width
            
            # Center the row within the circular safe area
            center_x = self.display_center[0]
            start_x = center_x - (row_width // 2)
            
            for col_idx, char in enumerate(row):
                key_x = start_x + (col_idx * key_width)
                key_y = start_y + (row_idx * (key_height + 5))
                
                key_rect = pygame.Rect(key_x, key_y, key_width - 2, key_height)
                
                # Validate key position is within circular bounds
                try:
                    validation = self._validate_circular_bounds((key_x, key_y, key_width - 2, key_height))
                    if not validation.get('within_safe_area', True):
                        self.logger.warning(f"Key '{char}' at ({key_x}, {key_y}) extends beyond safe area")
                except Exception as e:
                    self.logger.debug(f"Key validation failed: {e}")
                
                if char == 'Del':
                    pygame.draw.rect(surface, self.colors['danger'], key_rect, border_radius=4)
                else:
                    pygame.draw.rect(surface, self.colors['border'], key_rect, border_radius=4)
                
                # Key text
                font_key = pygame.font.Font(None, 28)
                key_text = font_key.render(char, True, self.colors['text'])
                key_text_rect = key_text.get_rect(center=key_rect.center)
                surface.blit(key_text, key_text_rect)
                
                new_regions.append(("key", key_rect, char))
        
        # Action buttons - positioned using circular layout
        
        # Get button renderer for standardized buttons
        button_renderer = get_button_renderer()
        
        # Cancel button - positioned at bottom-left circular position
        try:
            cancel_colors = {
                'background': self.colors['border'],
                'border': self.colors['border'],
                'text': self.colors['text']
            }
            
            visual_rect, touch_rect = button_renderer.render_button(
                surface=surface,
                position=(0, 0),  # Will be overridden by circular_position
                text="Cancel",
                button_size=ButtonSize.MEDIUM,  # 80x35 standardized size
                button_id="cancel_manual",
                state=ButtonState.NORMAL,
                colors=cancel_colors,
                circular_position=(225, 145)  # angle, radius
            )
            
            new_regions.append(("cancel_manual", touch_rect))
            
        except Exception as e:
            self.logger.error(f"Error rendering cancel button: {e}")
        
        # Connect button - positioned at bottom-right circular position
        try:
            # Enable only if MAC address looks valid
            is_valid = self._is_valid_mac_address(self.manual_mac_input)
            
            connect_colors = {
                'background': self.colors['primary'] if is_valid else self.colors['border'],
                'border': self.colors['primary'] if is_valid else self.colors['border'],
                'text': self.colors['text']
            }
            
            button_state = ButtonState.NORMAL if is_valid else ButtonState.DISABLED
            
            visual_rect, touch_rect = button_renderer.render_button(
                surface=surface,
                position=(0, 0),  # Will be overridden by circular_position
                text="Connect",
                button_size=ButtonSize.MEDIUM,  # 80x35 standardized size
                button_id="connect_manual",
                state=button_state,
                colors=connect_colors,
                circular_position=(315, 145)  # angle, radius
            )
            
            # Only add to touch regions if valid
            if is_valid:
                new_regions.append(("connect_manual", touch_rect))
                
        except Exception as e:
            self.logger.error(f"Error rendering connect button: {e}")
        
        # Atomically update all touch regions
        self._update_touch_regions_safe(new_regions)
    
    def _is_valid_mac_address(self, mac: str) -> bool:
        """Check if MAC address format is valid"""
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac))