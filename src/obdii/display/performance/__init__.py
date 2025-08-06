"""
Display performance monitoring components for OBDII display system.

This module provides performance monitoring and metrics collection
functionality extracted from the monolithic display manager.
"""

from .monitor import PerformanceMonitor
from .interfaces import PerformanceMonitorInterface, PerformanceMetrics, MetricType

# Legacy compatibility functions
_global_performance_manager = None

def initialize_performance_manager(surface_size, log_file=None):
    """Legacy compatibility function for performance manager initialization"""
    global _global_performance_manager
    _global_performance_manager = PerformanceMonitor(target_fps=60)
    _global_performance_manager.start_monitoring()
    return _global_performance_manager

def get_performance_manager():
    """Legacy compatibility function to get performance manager"""
    global _global_performance_manager
    if _global_performance_manager is None:
        _global_performance_manager = PerformanceMonitor(target_fps=60)
        _global_performance_manager.start_monitoring()
    return _global_performance_manager

def cleanup_performance_manager():
    """Legacy compatibility function to cleanup performance manager"""
    global _global_performance_manager
    if _global_performance_manager:
        _global_performance_manager.stop_monitoring()
        _global_performance_manager = None

__all__ = [
    'PerformanceMonitor',
    'PerformanceMonitorInterface',
    'PerformanceMetrics',
    'MetricType',
    'initialize_performance_manager',
    'get_performance_manager', 
    'cleanup_performance_manager'
]