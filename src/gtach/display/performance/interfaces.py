#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Interfaces and data structures for performance monitoring.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

class MetricType(Enum):
    """Types of performance metrics"""
    FPS = auto()
    FRAME_TIME = auto()
    RENDER_TIME = auto()
    MEMORY_USAGE = auto()
    CACHE_HIT_RATE = auto()
    DIRTY_REGIONS = auto()
    BUFFER_WRITES = auto()

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    fps: float = 0.0
    frame_time_ms: float = 0.0
    render_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cache_hit_rate: float = 0.0
    dirty_regions_count: int = 0
    buffer_writes: int = 0
    
    # Additional metrics
    total_frames: int = 0
    dropped_frames: int = 0
    last_update_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'fps': self.fps,
            'frame_time_ms': self.frame_time_ms,
            'render_time_ms': self.render_time_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'cache_hit_rate': self.cache_hit_rate,
            'dirty_regions_count': self.dirty_regions_count,
            'buffer_writes': self.buffer_writes,
            'total_frames': self.total_frames,
            'dropped_frames': self.dropped_frames,
            'last_update_time': self.last_update_time
        }

class PerformanceMonitorInterface(ABC):
    """Interface for performance monitoring systems"""
    
    @abstractmethod
    def start_monitoring(self) -> bool:
        """Start performance monitoring"""
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        pass
    
    @abstractmethod
    def record_frame_start(self) -> str:
        """Record start of frame rendering and return frame ID"""
        pass
    
    @abstractmethod
    def record_frame_end(self, frame_id: str) -> float:
        """Record end of frame rendering and return frame time"""
        pass
    
    @abstractmethod
    def record_render_operation(self, operation_type: str, duration: float) -> None:
        """Record a render operation with timing"""
        pass
    
    @abstractmethod
    def record_cache_hit(self, cache_type: str) -> None:
        """Record a cache hit"""
        pass
    
    @abstractmethod
    def record_cache_miss(self, cache_type: str) -> None:
        """Record a cache miss"""
        pass
    
    @abstractmethod
    def update_memory_usage(self, usage_mb: float) -> None:
        """Update current memory usage"""
        pass
    
    @abstractmethod
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        pass
    
    @abstractmethod
    def get_historical_metrics(self, seconds: int = 60) -> List[PerformanceMetrics]:
        """Get historical metrics for specified time period"""
        pass
    
    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        pass
    
    @abstractmethod
    def set_target_fps(self, fps: int) -> None:
        """Set target FPS for performance monitoring"""
        pass
    
    @abstractmethod
    def is_performance_acceptable(self) -> bool:
        """Check if current performance meets acceptable thresholds"""
        pass