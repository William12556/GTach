#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Display Component Factory - Creates and configures display components.
"""

import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

from ..rendering import DisplayRenderingEngine
from ..input import TouchEventCoordinator
from ..performance import PerformanceMonitor

@dataclass
class ComponentConfig:
    """Configuration for display components"""
    display_size: Tuple[int, int] = (480, 480)
    framebuffer_path: str = '/dev/fb0'
    target_fps: int = 60
    performance_history_duration: int = 300
    touch_long_press_duration: float = 1.0
    touch_drag_threshold: int = 10
    touch_swipe_threshold: int = 50

class DisplayComponentFactory:
    """
    Factory for creating and configuring display system components.
    
    Provides centralized component creation with consistent configuration
    and proper error handling.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('DisplayComponentFactory')
    
    def create_rendering_engine(self, config: ComponentConfig) -> Optional[DisplayRenderingEngine]:
        """
        Create and initialize rendering engine.
        
        Args:
            config: Component configuration
            
        Returns:
            DisplayRenderingEngine instance or None if creation failed
        """
        try:
            engine = DisplayRenderingEngine()
            
            if engine.initialize(config.display_size, config.framebuffer_path):
                self.logger.info(f"Rendering engine created: {config.display_size}")
                return engine
            else:
                self.logger.error("Failed to initialize rendering engine")
                return None
                
        except Exception as e:
            self.logger.error(f"Rendering engine creation failed: {e}")
            return None
    
    def create_touch_coordinator(self, config: ComponentConfig) -> Optional[TouchEventCoordinator]:
        """
        Create and configure touch event coordinator.
        
        Args:
            config: Component configuration
            
        Returns:
            TouchEventCoordinator instance or None if creation failed
        """
        try:
            coordinator = TouchEventCoordinator(config.display_size)
            
            # Configure touch parameters
            coordinator.long_press_duration = config.touch_long_press_duration
            coordinator.drag_threshold = config.touch_drag_threshold
            coordinator.swipe_threshold = config.touch_swipe_threshold
            
            self.logger.info(f"Touch coordinator created: {config.display_size}")
            return coordinator
            
        except Exception as e:
            self.logger.error(f"Touch coordinator creation failed: {e}")
            return None
    
    def create_performance_monitor(self, config: ComponentConfig) -> Optional[PerformanceMonitor]:
        """
        Create and configure performance monitor.
        
        Args:
            config: Component configuration
            
        Returns:
            PerformanceMonitor instance or None if creation failed
        """
        try:
            monitor = PerformanceMonitor(
                target_fps=config.target_fps,
                history_duration=config.performance_history_duration
            )
            
            if monitor.start_monitoring():
                self.logger.info(f"Performance monitor created: {config.target_fps} FPS target")
                return monitor
            else:
                self.logger.error("Failed to start performance monitoring")
                return None
                
        except Exception as e:
            self.logger.error(f"Performance monitor creation failed: {e}")
            return None
    
    def create_all_components(self, config: ComponentConfig) -> Dict[str, Any]:
        """
        Create all display components with configuration.
        
        Args:
            config: Component configuration
            
        Returns:
            Dictionary containing created components and status
        """
        components = {
            'rendering_engine': None,
            'touch_coordinator': None,
            'performance_monitor': None,
            'creation_status': {
                'rendering_engine': False,
                'touch_coordinator': False,
                'performance_monitor': False,
                'all_successful': False
            }
        }
        
        try:
            # Create rendering engine
            components['rendering_engine'] = self.create_rendering_engine(config)
            components['creation_status']['rendering_engine'] = components['rendering_engine'] is not None
            
            # Create touch coordinator
            components['touch_coordinator'] = self.create_touch_coordinator(config)
            components['creation_status']['touch_coordinator'] = components['touch_coordinator'] is not None
            
            # Create performance monitor
            components['performance_monitor'] = self.create_performance_monitor(config)
            components['creation_status']['performance_monitor'] = components['performance_monitor'] is not None
            
            # Check if all components were created successfully
            components['creation_status']['all_successful'] = all(
                components['creation_status'].values()
            )
            
            if components['creation_status']['all_successful']:
                self.logger.info("All display components created successfully")
            else:
                failed_components = [
                    name for name, status in components['creation_status'].items()
                    if not status and name != 'all_successful'
                ]
                self.logger.warning(f"Failed to create components: {failed_components}")
            
            return components
            
        except Exception as e:
            self.logger.error(f"Component creation batch failed: {e}")
            components['creation_status']['all_successful'] = False
            return components