#!/usr/bin/env python3
"""
Circular positioning engine for HyperPixel 2" Round display.
Mathematical algorithms for device layout positioning with circular display optimization.
"""

import logging
import math
import time
import threading
from typing import List, Dict, Tuple, Any, Optional


class CircularPositioningEngine:
    """Mathematical algorithms for circular display positioning with optimization"""
    
    def __init__(self, display_center: Tuple[int, int] = (240, 240), 
                 safe_radius: int = 200, max_radius: int = 220,
                 display_size: Tuple[int, int] = (480, 480)):
        self.logger = logging.getLogger('CircularPositioningEngine')
        
        # Circular display constants
        self.display_center = display_center
        self.display_safe_radius = safe_radius
        self.display_max_radius = max_radius
        self.display_size = display_size
        
        # Performance optimization caches
        self._circular_layout_cache = {}
        self._cache_lock = threading.Lock()
        
        # Performance monitoring
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
            }
        }
        
        self.logger.info(f"Initialized CircularPositioningEngine with center={display_center}, "
                        f"safe_radius={safe_radius}, max_radius={max_radius}")
    
    def get_circular_safe_area(self) -> Dict[str, Any]:
        """Get circular display geometry constants for safe UI positioning"""
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
            return {
                'center': (240, 240),
                'safe_radius': 200,
                'max_radius': 220,
                'size': (480, 480)
            }
    
    def position_in_circle(self, angle_degrees: float, radius: float, 
                          element_size: Tuple[int, int] = (100, 30)) -> Tuple[int, int, int, int]:
        """Position an element within the circular display using polar coordinates"""
        start_time = time.time()
        
        try:
            if radius < 0:
                raise ValueError("Radius must be non-negative")
            if radius > self.display_safe_radius:
                self.logger.warning(f"Radius {radius} exceeds safe radius {self.display_safe_radius}")
                radius = self.display_safe_radius
            
            angle_radians = math.radians(angle_degrees)
            
            center_x, center_y = self.display_center
            element_width, element_height = element_size
            
            pos_x = center_x + radius * math.cos(angle_radians)
            pos_y = center_y + radius * math.sin(angle_radians)
            
            rect_x = int(pos_x - element_width // 2)
            rect_y = int(pos_y - element_height // 2)
            
            result = (rect_x, rect_y, element_width, element_height)
            
            if self._performance_monitoring['enabled']:
                self._performance_monitoring['stats']['total_positioning_calls'] += 1
                duration = time.time() - start_time
                self._performance_monitoring['stats']['total_positioning_time'] += duration
                self._performance_monitoring['stats']['average_positioning_time'] = (
                    self._performance_monitoring['stats']['total_positioning_time'] / 
                    self._performance_monitoring['stats']['total_positioning_calls']
                )
                
                if duration > 0.01:
                    self._performance_monitoring['stats']['slow_operations_count'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error positioning element in circle: {e}")
            center_x, center_y = self.display_center
            return (center_x - 50, center_y - 15, 100, 30)
    
    def validate_circular_bounds(self, rect_coords: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """Validate if a rectangle fits within the circular display boundary"""
        start_time = time.time()
        
        try:
            x, y, width, height = rect_coords
            center_x, center_y = self.display_center
            
            rect_center_x = x + width // 2
            rect_center_y = y + height // 2
            center_distance = math.sqrt((rect_center_x - center_x)**2 + (rect_center_y - center_y)**2)
            
            corners = [
                (x, y),
                (x + width, y),
                (x, y + height),
                (x + width, y + height)
            ]
            
            corner_distances = []
            for corner_x, corner_y in corners:
                distance = math.sqrt((corner_x - center_x)**2 + (corner_y - center_y)**2)
                corner_distances.append(distance)
            
            max_corner_distance = max(corner_distances)
            
            within_safe_area = max_corner_distance <= self.display_safe_radius
            within_max_area = max_corner_distance <= self.display_max_radius
            valid = within_safe_area
            
            result = {
                'valid': valid,
                'center_distance': center_distance,
                'corner_distances': corner_distances,
                'max_corner_distance': max_corner_distance,
                'within_safe_area': within_safe_area,
                'within_max_area': within_max_area
            }
            
            if self._performance_monitoring['enabled']:
                self._performance_monitoring['stats']['total_validation_calls'] += 1
                duration = time.time() - start_time
                self._performance_monitoring['stats']['total_validation_time'] += duration
                self._performance_monitoring['stats']['average_validation_time'] = (
                    self._performance_monitoring['stats']['total_validation_time'] / 
                    self._performance_monitoring['stats']['total_validation_calls']
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating circular bounds: {e}")
            return {
                'valid': False,
                'center_distance': float('inf'),
                'corner_distances': [float('inf')],
                'max_corner_distance': float('inf'),
                'within_safe_area': False,
                'within_max_area': False
            }
    
    def calculate_curved_list_layout(self, item_count: int, start_y: int = 100, 
                                   item_height: int = 45, item_spacing: int = 3) -> List[Dict[str, Any]]:
        """Calculate curved list layout positions for circular display optimization"""
        try:
            layout_data = []
            center_x, center_y = self.display_center
            safe_radius = self.display_safe_radius
            
            with self._cache_lock:
                if not hasattr(self, '_circular_layout_cache'):
                    self._circular_layout_cache = {}
            
            self.logger.debug(f"Calculating curved layout for {item_count} items starting at y={start_y}")
            
            for i in range(item_count):
                y_pos = start_y + i * (item_height + item_spacing)
                y_distance_from_center = abs(y_pos + item_height // 2 - center_y)
                
                cache_key = f"curved_{y_pos}_{item_height}"
                
                with self._cache_lock:
                    if cache_key in self._circular_layout_cache:
                        layout_item = self._circular_layout_cache[cache_key].copy()
                        layout_item['index'] = i
                        layout_item['y'] = y_pos
                    else:
                        try:
                            if y_distance_from_center <= safe_radius:
                                horizontal_radius = math.sqrt(safe_radius**2 - y_distance_from_center**2)
                                
                                curve_factor = 1.0 - (horizontal_radius / safe_radius)
                                x_offset = int(curve_factor * 15)
                                
                                max_width_at_position = int(horizontal_radius * 2 * 0.85)
                                item_width = min(400, max_width_at_position)
                                
                                x_pos = center_x - item_width // 2 + x_offset
                                
                                distance_from_center = math.sqrt((center_x - x_pos)**2 + y_distance_from_center**2)
                                scale_factor = max(0.95, 1.0 - (distance_from_center / safe_radius) * 0.05)
                                opacity_factor = max(0.85, 1.0 - (distance_from_center / safe_radius) * 0.15)
                                
                                in_safe_area = distance_from_center <= safe_radius
                            else:
                                x_pos = 40
                                item_width = 350
                                scale_factor = 0.9
                                opacity_factor = 0.8
                                distance_from_center = y_distance_from_center
                                in_safe_area = False
                        
                        except Exception as calc_error:
                            self.logger.warning(f"Error in curved layout calculation for item {i}: {calc_error}")
                            x_pos = 40
                            item_width = 350
                            scale_factor = 1.0
                            opacity_factor = 1.0
                            distance_from_center = y_distance_from_center
                            in_safe_area = False
                        
                        layout_item = {
                            'index': i,
                            'x': x_pos,
                            'y': y_pos,
                            'width': item_width,
                            'height': item_height,
                            'scale': scale_factor,
                            'opacity': opacity_factor,
                            'center_distance': distance_from_center,
                            'in_safe_area': in_safe_area
                        }
                        
                        cache_item = layout_item.copy()
                        del cache_item['index']
                        del cache_item['y']
                        self._circular_layout_cache[cache_key] = cache_item
                
                layout_data.append(layout_item)
                
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f"Item {i}: x={layout_item['x']}, y={layout_item['y']}, "
                                    f"w={layout_item['width']}, scale={layout_item['scale']:.2f}, "
                                    f"opacity={layout_item['opacity']:.2f}, safe={layout_item['in_safe_area']}")
            
            with self._cache_lock:
                cache_size = len(self._circular_layout_cache)
                if cache_size > 100:
                    cache_keys = list(self._circular_layout_cache.keys())
                    for old_key in cache_keys[:cache_size // 2]:
                        del self._circular_layout_cache[old_key]
                    self.logger.debug(f"Trimmed circular layout cache from {cache_size} to {len(self._circular_layout_cache)} entries")
            
            self.logger.info(f"Generated curved layout for {len(layout_data)} items")
            return layout_data
            
        except Exception as e:
            self.logger.error(f"Error calculating curved list layout: {e}")
            fallback_layout = []
            for i in range(item_count):
                fallback_layout.append({
                    'index': i,
                    'x': 40,
                    'y': start_y + i * (item_height + item_spacing),
                    'width': 400,
                    'height': item_height,
                    'scale': 1.0,
                    'opacity': 1.0,
                    'center_distance': 0,
                    'in_safe_area': True
                })
            return fallback_layout
    
    def validate_all_layout_elements(self, layout_data: List[Dict[str, Any]], 
                                   screen_name: str = "current") -> Dict[str, Any]:
        """Validate all layout elements for circular boundary compliance"""
        try:
            total_elements = len(layout_data)
            valid_elements = 0
            invalid_elements = []
            performance_stats = {}
            
            start_time = time.time()
            
            for item in layout_data:
                rect_coords = (item['x'], item['y'], item['width'], item['height'])
                validation_result = self.validate_circular_bounds(rect_coords)
                
                if validation_result['valid']:
                    valid_elements += 1
                else:
                    invalid_elements.append({
                        'item_index': item.get('index', -1),
                        'rect_coords': rect_coords,
                        'max_corner_distance': validation_result['max_corner_distance'],
                        'safe_radius': self.display_safe_radius,
                        'excess_distance': validation_result['max_corner_distance'] - self.display_safe_radius
                    })
            
            total_time = time.time() - start_time
            performance_stats = {
                'validation_time_ms': total_time * 1000,
                'elements_per_second': total_elements / total_time if total_time > 0 else 0,
                'average_time_per_element_ms': (total_time / total_elements * 1000) if total_elements > 0 else 0
            }
            
            validation_summary = {
                'passed': len(invalid_elements) == 0,
                'total_elements': total_elements,
                'valid_elements': valid_elements,
                'invalid_elements_count': len(invalid_elements),
                'compliance_percentage': (valid_elements / total_elements * 100) if total_elements > 0 else 100
            }
            
            result = {
                'screen_name': screen_name,
                'validation_summary': validation_summary,
                'invalid_elements': invalid_elements,
                'performance_stats': performance_stats,
                'recommendations': []
            }
            
            if len(invalid_elements) > 0:
                result['recommendations'].append(f"Adjust {len(invalid_elements)} elements to fit within safe area")
            else:
                result['recommendations'].append("All elements comply with circular layout constraints")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating layout elements: {e}")
            return {
                'screen_name': screen_name,
                'validation_summary': {'passed': False, 'error': str(e)},
                'invalid_elements': [],
                'performance_stats': {},
                'recommendations': ['Validation failed due to error']
            }
    
    def log_positioning_metrics(self, operation: str, start_time: float, element_count: int = 1, 
                               additional_data: Dict[str, Any] = None) -> None:
        """Log performance metrics for circular positioning operations"""
        try:
            duration = time.time() - start_time
            elements_per_second = element_count / duration if duration > 0 else 0
            
            metrics = {
                'operation': operation,
                'duration_ms': duration * 1000,
                'element_count': element_count,
                'elements_per_second': elements_per_second
            }
            
            if additional_data:
                metrics.update(additional_data)
            
            if duration > 0.1:
                self.logger.warning(f"Slow circular positioning: {operation} took {duration*1000:.1f}ms "
                                   f"for {element_count} elements ({elements_per_second:.1f} elements/sec)")
            elif duration > 0.05:
                self.logger.info(f"Circular positioning: {operation} took {duration*1000:.1f}ms "
                                f"for {element_count} elements")
            else:
                self.logger.debug(f"Circular positioning: {operation} completed in {duration*1000:.1f}ms")
            
            self.logger.debug(f"Positioning metrics: {metrics}")
            
        except Exception as e:
            self.logger.error(f"Error logging positioning metrics: {e}")
    
    def monitor_performance(self, enable_monitoring: bool = True) -> Dict[str, Any]:
        """Enable or disable performance monitoring for circular positioning operations"""
        try:
            self._performance_monitoring['enabled'] = enable_monitoring
            
            current_config = {
                'monitoring_enabled': enable_monitoring,
                'stats': self._performance_monitoring['stats'].copy()
            }
            
            if enable_monitoring:
                self.logger.info("Circular positioning performance monitoring enabled")
            else:
                self.logger.info("Circular positioning performance monitoring disabled")
            
            return current_config
            
        except Exception as e:
            self.logger.error(f"Error configuring performance monitoring: {e}")
            return {'error': str(e)}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report for circular positioning operations"""
        try:
            if not self._performance_monitoring['enabled']:
                return {'error': 'Performance monitoring not enabled'}
            
            stats = self._performance_monitoring['stats']
            
            report = {
                'monitoring_enabled': True,
                'total_operations': stats['total_positioning_calls'] + stats['total_validation_calls'],
                'positioning_operations': {
                    'total_calls': stats['total_positioning_calls'],
                    'total_time_ms': stats['total_positioning_time'] * 1000,
                    'average_time_ms': stats['average_positioning_time'] * 1000
                },
                'validation_operations': {
                    'total_calls': stats['total_validation_calls'],
                    'total_time_ms': stats['total_validation_time'] * 1000,
                    'average_time_ms': stats['average_validation_time'] * 1000
                },
                'performance_issues': {
                    'slow_operations_count': stats['slow_operations_count']
                },
                'recommendations': []
            }
            
            if stats['average_positioning_time'] > 0.01:
                report['recommendations'].append("Consider optimizing positioning calculations")
            if stats['average_validation_time'] > 0.005:
                report['recommendations'].append("Consider caching validation results")
            if stats['slow_operations_count'] > stats['total_positioning_calls'] * 0.1:
                report['recommendations'].append("High percentage of slow operations detected")
            
            if not report['recommendations']:
                report['recommendations'].append("Performance is within acceptable parameters")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}
    
    def reset_performance_stats(self) -> None:
        """Reset all circular positioning performance statistics"""
        try:
            self._performance_monitoring['stats'] = {
                'total_positioning_calls': 0,
                'total_validation_calls': 0,
                'total_positioning_time': 0.0,
                'total_validation_time': 0.0,
                'average_positioning_time': 0.0,
                'average_validation_time': 0.0,
                'slow_operations_count': 0
            }
            self.logger.info("Circular positioning performance statistics reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting performance statistics: {e}")
    
    def clear_layout_cache(self) -> None:
        """Clear the circular layout cache to free memory"""
        try:
            with self._cache_lock:
                cache_size = len(self._circular_layout_cache)
                self._circular_layout_cache.clear()
                self.logger.info(f"Cleared circular layout cache ({cache_size} entries)")
                
        except Exception as e:
            self.logger.error(f"Error clearing layout cache: {e}")