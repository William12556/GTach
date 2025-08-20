#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Performance Monitor - Extracted from display manager and performance.py.

Provides comprehensive performance monitoring, metrics collection,
and analysis for the OBDII display system.
"""

import time
import threading
import logging
import uuid
import os
import psutil
from collections import deque, defaultdict
from typing import Dict, Any, Optional, List, Tuple
import pygame

from .interfaces import PerformanceMonitorInterface, PerformanceMetrics, MetricType

class PerformanceMonitor(PerformanceMonitorInterface):
    """
    Comprehensive performance monitoring system for display operations.
    
    Tracks FPS, render times, memory usage, cache performance, and provides
    detailed metrics for optimization and debugging.
    """
    
    def __init__(self, target_fps: int = 60, history_duration: int = 300):
        self.logger = logging.getLogger('PerformanceMonitor')
        self._lock = threading.RLock()
        
        # Configuration
        self.target_fps = target_fps
        self.history_duration = history_duration  # seconds
        self.frame_time_target = 1.0 / target_fps
        
        # Monitoring state
        self._monitoring = False
        self._start_time = 0.0
        
        # Frame tracking
        self._active_frames: Dict[str, float] = {}  # frame_id -> start_time
        self._frame_history = deque(maxlen=target_fps * 10)  # Last 10 seconds
        self._frame_count = 0
        self._dropped_frames = 0
        
        # Render operation tracking
        self._render_operations = defaultdict(list)  # operation -> [durations]
        self._operation_counts = defaultdict(int)
        
        # Cache tracking
        self._cache_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
        
        # Memory tracking
        self._memory_samples = deque(maxlen=60)  # Last 60 samples
        self._process = psutil.Process() if psutil else None
        
        # Performance thresholds
        self.thresholds = {
            'min_fps': target_fps * 0.8,  # 80% of target
            'max_frame_time_ms': (1.0 / target_fps) * 1000 * 1.2,  # 120% of target
            'max_memory_mb': 100.0,  # Reasonable limit for Pi
            'min_cache_hit_rate': 0.7  # 70% cache hit rate
        }
        
        # Metrics history
        self._metrics_history = deque(maxlen=history_duration)
        self._last_metrics_update = 0.0
        
        # Dirty regions tracking (for optimization)
        self._dirty_regions = []
        self._total_dirty_area = 0
        
        # Font cache integration
        self._font_cache_enabled = False
        self._font_cache = {}
        
    def start_monitoring(self) -> bool:
        """Start performance monitoring"""
        with self._lock:
            try:
                if self._monitoring:
                    return True
                
                self._monitoring = True
                self._start_time = time.time()
                self._frame_count = 0
                self._dropped_frames = 0
                
                # Clear histories
                self._frame_history.clear()
                self._metrics_history.clear()
                self._memory_samples.clear()
                
                # Reset operation tracking
                self._render_operations.clear()
                self._operation_counts.clear()
                self._cache_stats.clear()
                
                self.logger.info(f"Performance monitoring started (target: {self.target_fps} FPS)")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start performance monitoring: {e}")
                return False
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        with self._lock:
            try:
                if not self._monitoring:
                    return
                
                duration = time.time() - self._start_time
                avg_fps = self._frame_count / duration if duration > 0 else 0
                
                self.logger.info(f"Performance monitoring stopped. "
                               f"Duration: {duration:.1f}s, "
                               f"Frames: {self._frame_count}, "
                               f"Avg FPS: {avg_fps:.1f}, "
                               f"Dropped: {self._dropped_frames}")
                
                self._monitoring = False
                
            except Exception as e:
                self.logger.error(f"Error stopping performance monitoring: {e}")
    
    def record_frame_start(self) -> str:
        """Record start of frame rendering and return frame ID"""
        if not self._monitoring:
            return ""
        
        with self._lock:
            try:
                frame_id = str(uuid.uuid4())[:8]
                current_time = time.time()
                
                self._active_frames[frame_id] = current_time
                
                # Clean up old frame IDs (safety measure)
                cutoff_time = current_time - 1.0  # 1 second timeout
                expired_frames = [fid for fid, start_time in self._active_frames.items() 
                                if start_time < cutoff_time]
                for fid in expired_frames:
                    del self._active_frames[fid]
                    self._dropped_frames += 1
                
                return frame_id
                
            except Exception as e:
                self.logger.error(f"Error recording frame start: {e}")
                return ""
    
    def record_frame_end(self, frame_id: str) -> float:
        """Record end of frame rendering and return frame time"""
        if not self._monitoring or not frame_id:
            return 0.0
        
        with self._lock:
            try:
                current_time = time.time()
                
                if frame_id not in self._active_frames:
                    self.logger.warning(f"Frame {frame_id} not found in active frames")
                    return 0.0
                
                start_time = self._active_frames.pop(frame_id)
                frame_time = current_time - start_time
                
                # Record frame data
                self._frame_history.append({
                    'timestamp': current_time,
                    'frame_time': frame_time,
                    'frame_id': frame_id
                })
                
                self._frame_count += 1
                
                # Check for dropped frame
                if frame_time > self.frame_time_target * 1.5:
                    self._dropped_frames += 1
                
                # Update metrics periodically
                if current_time - self._last_metrics_update >= 1.0:
                    self._update_metrics_history()
                    self._last_metrics_update = current_time
                
                return frame_time
                
            except Exception as e:
                self.logger.error(f"Error recording frame end: {e}")
                return 0.0
    
    def record_render_operation(self, operation_type: str, duration: float) -> None:
        """Record a render operation with timing"""
        if not self._monitoring:
            return
        
        with self._lock:
            try:
                self._render_operations[operation_type].append(duration)
                self._operation_counts[operation_type] += 1
                
                # Limit history size per operation
                if len(self._render_operations[operation_type]) > 100:
                    self._render_operations[operation_type] = \
                        self._render_operations[operation_type][-50:]
                        
            except Exception as e:
                self.logger.error(f"Error recording render operation: {e}")
    
    def record_cache_hit(self, cache_type: str) -> None:
        """Record a cache hit"""
        if not self._monitoring:
            return
        
        with self._lock:
            self._cache_stats[cache_type]['hits'] += 1
    
    def record_cache_miss(self, cache_type: str) -> None:
        """Record a cache miss"""
        if not self._monitoring:
            return
        
        with self._lock:
            self._cache_stats[cache_type]['misses'] += 1
    
    def update_memory_usage(self, usage_mb: float) -> None:
        """Update current memory usage"""
        if not self._monitoring:
            return
        
        with self._lock:
            current_time = time.time()
            self._memory_samples.append({
                'timestamp': current_time,
                'usage_mb': usage_mb
            })
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        with self._lock:
            try:
                current_time = time.time()
                
                # Calculate FPS from recent frames
                fps = self._calculate_current_fps()
                
                # Calculate average frame time
                frame_time_ms = self._calculate_average_frame_time() * 1000
                
                # Calculate render time
                render_time_ms = self._calculate_average_render_time() * 1000
                
                # Get memory usage
                memory_mb = self._get_current_memory_usage()
                
                # Calculate cache hit rate
                cache_hit_rate = self._calculate_cache_hit_rate()
                
                # Get dirty regions info
                dirty_regions_count = len(self._dirty_regions)
                
                return PerformanceMetrics(
                    fps=fps,
                    frame_time_ms=frame_time_ms,
                    render_time_ms=render_time_ms,
                    memory_usage_mb=memory_mb,
                    cache_hit_rate=cache_hit_rate,
                    dirty_regions_count=dirty_regions_count,
                    buffer_writes=self._operation_counts.get('buffer_write', 0),
                    total_frames=self._frame_count,
                    dropped_frames=self._dropped_frames,
                    last_update_time=current_time
                )
                
            except Exception as e:
                self.logger.error(f"Error getting current metrics: {e}")
                return PerformanceMetrics()
    
    def get_historical_metrics(self, seconds: int = 60) -> List[PerformanceMetrics]:
        """Get historical metrics for specified time period"""
        with self._lock:
            try:
                current_time = time.time()
                cutoff_time = current_time - seconds
                
                return [metrics for metrics in self._metrics_history 
                       if metrics.last_update_time >= cutoff_time]
                       
            except Exception as e:
                self.logger.error(f"Error getting historical metrics: {e}")
                return []
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        with self._lock:
            try:
                self._frame_history.clear()
                self._metrics_history.clear()
                self._memory_samples.clear()
                self._render_operations.clear()
                self._operation_counts.clear()
                self._cache_stats.clear()
                self._active_frames.clear()
                self._dirty_regions.clear()
                
                self._frame_count = 0
                self._dropped_frames = 0
                self._total_dirty_area = 0
                
                self.logger.debug("Performance metrics reset")
                
            except Exception as e:
                self.logger.error(f"Error resetting metrics: {e}")
    
    def set_target_fps(self, fps: int) -> None:
        """Set target FPS for performance monitoring"""
        with self._lock:
            self.target_fps = fps
            self.frame_time_target = 1.0 / fps
            self.thresholds['min_fps'] = fps * 0.8
            self.thresholds['max_frame_time_ms'] = (1.0 / fps) * 1000 * 1.2
            
            self.logger.debug(f"Target FPS updated to {fps}")
    
    def is_performance_acceptable(self) -> bool:
        """Check if current performance meets acceptable thresholds"""
        try:
            metrics = self.get_current_metrics()
            
            # Check FPS threshold
            if metrics.fps < self.thresholds['min_fps']:
                return False
            
            # Check frame time threshold
            if metrics.frame_time_ms > self.thresholds['max_frame_time_ms']:
                return False
            
            # Check memory threshold
            if metrics.memory_usage_mb > self.thresholds['max_memory_mb']:
                return False
            
            # Check cache hit rate threshold (if cache is active)
            if (metrics.cache_hit_rate > 0 and 
                metrics.cache_hit_rate < self.thresholds['min_cache_hit_rate']):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking performance: {e}")
            return False
    
    def _calculate_current_fps(self) -> float:
        """Calculate current FPS from recent frame history"""
        try:
            if not self._frame_history:
                return 0.0
            
            current_time = time.time()
            recent_frames = [f for f in self._frame_history 
                           if current_time - f['timestamp'] <= 1.0]
            
            return len(recent_frames)
            
        except Exception:
            return 0.0
    
    def _calculate_average_frame_time(self) -> float:
        """Calculate average frame time from recent frames"""
        try:
            if not self._frame_history:
                return 0.0
            
            recent_frames = list(self._frame_history)[-30:]  # Last 30 frames
            total_time = sum(f['frame_time'] for f in recent_frames)
            
            return total_time / len(recent_frames)
            
        except Exception:
            return 0.0
    
    def _calculate_average_render_time(self) -> float:
        """Calculate average render operation time"""
        try:
            all_durations = []
            for operation_durations in self._render_operations.values():
                all_durations.extend(operation_durations[-10:])  # Last 10 per operation
            
            if not all_durations:
                return 0.0
            
            return sum(all_durations) / len(all_durations)
            
        except Exception:
            return 0.0
    
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            if self._process:
                memory_info = self._process.memory_info()
                return memory_info.rss / (1024 * 1024)  # Convert to MB
            elif self._memory_samples:
                return self._memory_samples[-1]['usage_mb']
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate"""
        try:
            total_hits = sum(stats['hits'] for stats in self._cache_stats.values())
            total_misses = sum(stats['misses'] for stats in self._cache_stats.values())
            total_requests = total_hits + total_misses
            
            if total_requests == 0:
                return 0.0
            
            return total_hits / total_requests
            
        except Exception:
            return 0.0
    
    def _update_metrics_history(self) -> None:
        """Update metrics history with current snapshot"""
        try:
            current_metrics = self.get_current_metrics()
            self._metrics_history.append(current_metrics)
            
        except Exception as e:
            self.logger.error(f"Error updating metrics history: {e}")
    
    def add_dirty_region(self, rect: pygame.Rect) -> None:
        """Add a dirty region for optimization tracking"""
        if not self._monitoring:
            return
        
        with self._lock:
            try:
                self._dirty_regions.append({
                    'rect': rect,
                    'timestamp': time.time(),
                    'area': rect.width * rect.height
                })
                
                self._total_dirty_area += rect.width * rect.height
                
                # Limit dirty region history
                if len(self._dirty_regions) > 100:
                    removed = self._dirty_regions.pop(0)
                    self._total_dirty_area -= removed['area']
                    
            except Exception as e:
                self.logger.error(f"Error adding dirty region: {e}")
    
    def get_dirty_regions(self) -> List[pygame.Rect]:
        """Get current dirty regions for partial updates"""
        with self._lock:
            try:
                current_time = time.time()
                
                # Return regions from the last frame
                recent_regions = [r['rect'] for r in self._dirty_regions 
                                if current_time - r['timestamp'] <= 0.1]
                
                return recent_regions
                
            except Exception as e:
                self.logger.error(f"Error getting dirty regions: {e}")
                return []
    
    def clear_dirty_regions(self) -> None:
        """Clear dirty regions after processing"""
        with self._lock:
            self._dirty_regions.clear()
            self._total_dirty_area = 0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            try:
                metrics = self.get_current_metrics()
                
                return {
                    'current_metrics': metrics.to_dict(),
                    'thresholds': dict(self.thresholds),
                    'performance_acceptable': self.is_performance_acceptable(),
                    'monitoring_duration': time.time() - self._start_time if self._monitoring else 0,
                    'cache_details': dict(self._cache_stats),
                    'operation_counts': dict(self._operation_counts),
                    'target_fps': self.target_fps
                }
                
            except Exception as e:
                self.logger.error(f"Error getting performance summary: {e}")
                return {}