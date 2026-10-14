# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Display performance monitoring components for OBDII display system.

This module provides performance monitoring and metrics collection
functionality extracted from the monolithic display manager.
"""

from .interfaces import MetricType, PerformanceMetrics, PerformanceMonitorInterface
from .monitor import PerformanceMonitor

__all__ = [
    "PerformanceMonitor",
    "PerformanceMonitorInterface",
    "PerformanceMetrics",
    "MetricType",
]
