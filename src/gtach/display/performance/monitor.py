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

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any, DefaultDict, Deque, Dict, List

import psutil

from .interfaces import PerformanceMetrics, PerformanceMonitorInterface


class PerformanceMonitor(PerformanceMonitorInterface):
    """
    Comprehensive performance monitoring system for display operations.

    Tracks FPS, render times, memory usage, cache performance, and provides
    detailed metrics for optimization and debugging.
    """

    def __init__(self, target_fps: int = 60):
        self.logger = logging.getLogger("PerformanceMonitor")
        self._lock = threading.RLock()

        # Configuration
        self.target_fps = target_fps
        self.frame_time_target = 1.0 / target_fps

        # Monitoring state
        self._monitoring = False
        # Durations, ages and history timestamps below use time.monotonic()
        # so a wall-clock step cannot distort them (issue-e215a184).
        self._start_time = 0.0

        # Frame tracking
        self._active_frames: Dict[int, float] = {}  # frame_id -> start_time
        # Last 10 seconds
        self._frame_history: Deque[Dict[str, float]] = deque(maxlen=target_fps * 10)
        self._frame_count = 0
        self._dropped_frames = 0

        # Instrumentation cost reduction (change-0b00759c)
        self._frame_id_counter = 0  # monotonic frame ID source
        self._memory_cache_mb = 0.0  # cached psutil RSS reading
        self._memory_cache_ts = 0.0  # time.monotonic() of that reading
        self._memory_sample_interval = 1.0  # seconds between psutil reads
        self._log_interval_frames = 600  # periodic log cadence

        # Render operation tracking
        # operation -> [durations]
        self._render_operations: DefaultDict[str, List[float]] = defaultdict(list)
        self._operation_counts: DefaultDict[str, int] = defaultdict(int)

        # Cache tracking
        self._cache_stats: DefaultDict[str, Dict[str, int]] = defaultdict(
            lambda: {"hits": 0, "misses": 0}
        )

        # Memory tracking
        self._memory_samples: Deque[Dict[str, float]] = deque(maxlen=60)  # Last 60
        self._process = psutil.Process() if psutil else None

        # Performance thresholds
        self.thresholds = {
            "min_fps": target_fps * 0.8,  # 80% of target
            "max_frame_time_ms": (1.0 / target_fps) * 1000 * 1.2,  # 120% of target
            "max_memory_mb": 100.0,  # Reasonable limit for Pi
            "min_cache_hit_rate": 0.7,  # 70% cache hit rate
        }

    def start_monitoring(self) -> bool:
        """Start performance monitoring"""
        with self._lock:
            try:
                if self._monitoring:
                    return True

                self._monitoring = True
                self._start_time = time.monotonic()
                self._frame_count = 0
                self._dropped_frames = 0

                # Clear histories
                self._frame_history.clear()
                self._memory_samples.clear()

                # Reset operation tracking
                self._render_operations.clear()
                self._operation_counts.clear()
                self._cache_stats.clear()

                self.logger.info(
                    f"Performance monitoring started (target: {self.target_fps} FPS)"
                )
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to start performance monitoring: {e}", exc_info=True
                )
                return False

    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        with self._lock:
            try:
                if not self._monitoring:
                    return

                duration = time.monotonic() - self._start_time
                avg_fps = self._frame_count / duration if duration > 0 else 0

                self.logger.info(
                    f"Performance monitoring stopped. "
                    f"Duration: {duration:.1f}s, "
                    f"Frames: {self._frame_count}, "
                    f"Avg FPS: {avg_fps:.1f}, "
                    f"Dropped: {self._dropped_frames}"
                )

                self._monitoring = False

            except Exception as e:
                self.logger.error(
                    f"Error stopping performance monitoring: {e}", exc_info=True
                )

    def record_frame_start(self) -> int:
        """Record start of frame rendering and return frame ID.

        Returns:
            Positive, monotonically increasing frame ID, or 0 when monitoring
            is disabled or an error occurs.
        """
        if not self._monitoring:
            return 0

        with self._lock:
            try:
                self._frame_id_counter += 1
                frame_id = self._frame_id_counter
                current_time = time.monotonic()

                self._active_frames[frame_id] = current_time

                # Clean up old frame IDs (safety measure). In steady state
                # exactly one frame is active, so the scan is skipped.
                if len(self._active_frames) > 1:
                    cutoff_time = current_time - 1.0  # 1 second timeout
                    expired_frames = [
                        fid
                        for fid, start_time in self._active_frames.items()
                        if start_time < cutoff_time
                    ]
                    for fid in expired_frames:
                        del self._active_frames[fid]
                        self._dropped_frames += 1

                return frame_id

            except Exception as e:
                self.logger.error(f"Error recording frame start: {e}", exc_info=True)
                return 0

    def record_frame_end(self, frame_id: int) -> float:
        """Record end of frame rendering and return frame time.

        Args:
            frame_id: Identifier returned by record_frame_start. 0 means
                monitoring was disabled, and the call is a no-op.

        Returns:
            Frame duration in seconds, or 0.0.
        """
        if not self._monitoring or not frame_id:
            return 0.0

        with self._lock:
            try:
                current_time = time.monotonic()

                if frame_id not in self._active_frames:
                    self.logger.warning(f"Frame {frame_id} not found in active frames")
                    return 0.0

                start_time = self._active_frames.pop(frame_id)
                frame_time = current_time - start_time

                # Record frame data
                self._frame_history.append(
                    {
                        "timestamp": current_time,
                        "frame_time": frame_time,
                        "frame_id": frame_id,
                    }
                )

                self._frame_count += 1

                # Check for dropped frame
                if frame_time > self.frame_time_target * 1.5:
                    self._dropped_frames += 1

                return frame_time

            except Exception as e:
                self.logger.error(f"Error recording frame end: {e}", exc_info=True)
                return 0.0

    def should_log_periodic(self) -> bool:
        """Whether the caller should emit the periodic performance line.

        Replaces a per-frame get_current_metrics() call made only to
        read a frame counter the monitor already holds. Constructing
        the metrics object also performs a psutil read, so testing
        the counter directly removes that cost from the frame path.

        Returns:
            True on every self._log_interval_frames-th recorded frame.
        """
        if not self._monitoring:
            return False

        try:
            with self._lock:
                return (
                    self._frame_count > 0
                    and self._frame_count % self._log_interval_frames == 0
                )
        except Exception as e:
            self.logger.error(
                f"Error testing periodic log interval: {e}", exc_info=True
            )
            return False

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        with self._lock:
            try:
                current_time = time.monotonic()

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

                return PerformanceMetrics(
                    fps=fps,
                    frame_time_ms=frame_time_ms,
                    render_time_ms=render_time_ms,
                    memory_usage_mb=memory_mb,
                    cache_hit_rate=cache_hit_rate,
                    buffer_writes=self._operation_counts.get("buffer_write", 0),
                    total_frames=self._frame_count,
                    dropped_frames=self._dropped_frames,
                    last_update_time=current_time,
                )

            except Exception as e:
                self.logger.error(f"Error getting current metrics: {e}", exc_info=True)
                return PerformanceMetrics()

    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        with self._lock:
            try:
                self._frame_history.clear()
                self._memory_samples.clear()
                self._render_operations.clear()
                self._operation_counts.clear()
                self._cache_stats.clear()
                self._active_frames.clear()

                self._frame_count = 0
                self._dropped_frames = 0
                self._frame_id_counter = 0
                self._memory_cache_mb = 0.0
                self._memory_cache_ts = 0.0

                self.logger.debug("Performance metrics reset")

            except Exception as e:
                self.logger.error(f"Error resetting metrics: {e}", exc_info=True)

    def is_performance_acceptable(self) -> bool:
        """Check if current performance meets acceptable thresholds"""
        try:
            metrics = self.get_current_metrics()

            # Check FPS threshold
            if metrics.fps < self.thresholds["min_fps"]:
                return False

            # Check frame time threshold
            if metrics.frame_time_ms > self.thresholds["max_frame_time_ms"]:
                return False

            # Check memory threshold
            if metrics.memory_usage_mb > self.thresholds["max_memory_mb"]:
                return False

            # Check cache hit rate threshold (if cache is active)
            if (
                metrics.cache_hit_rate > 0
                and metrics.cache_hit_rate < self.thresholds["min_cache_hit_rate"]
            ):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking performance: {e}", exc_info=True)
            return False

    def _calculate_current_fps(self) -> float:
        """Calculate current FPS from recent frame history"""
        try:
            if not self._frame_history:
                return 0.0

            current_time = time.monotonic()
            recent_frames = [
                f for f in self._frame_history if current_time - f["timestamp"] <= 1.0
            ]

            return len(recent_frames)

        except Exception:
            return 0.0

    def _calculate_average_frame_time(self) -> float:
        """Calculate average frame time from recent frames"""
        try:
            if not self._frame_history:
                return 0.0

            recent_frames = list(self._frame_history)[-30:]  # Last 30 frames
            total_time = sum(f["frame_time"] for f in recent_frames)

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
                now = time.monotonic()
                if (
                    self._memory_cache_ts
                    and now - self._memory_cache_ts < self._memory_sample_interval
                ):
                    return self._memory_cache_mb

                memory_info = self._process.memory_info()
                self._memory_cache_mb = memory_info.rss / (1024 * 1024)
                self._memory_cache_ts = now
                return self._memory_cache_mb
            elif self._memory_samples:
                return self._memory_samples[-1]["usage_mb"]
            else:
                return 0.0

        except Exception:
            return 0.0

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate"""
        try:
            total_hits = sum(stats["hits"] for stats in self._cache_stats.values())
            total_misses = sum(stats["misses"] for stats in self._cache_stats.values())
            total_requests = total_hits + total_misses

            if total_requests == 0:
                return 0.0

            return total_hits / total_requests

        except Exception:
            return 0.0

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            try:
                metrics = self.get_current_metrics()

                return {
                    "current_metrics": metrics.to_dict(),
                    "thresholds": dict(self.thresholds),
                    "performance_acceptable": self.is_performance_acceptable(),
                    "monitoring_duration": (
                        time.monotonic() - self._start_time if self._monitoring else 0
                    ),
                    "cache_details": dict(self._cache_stats),
                    "operation_counts": dict(self._operation_counts),
                    "target_fps": self.target_fps,
                }

            except Exception as e:
                self.logger.error(
                    f"Error getting performance summary: {e}", exc_info=True
                )
                return {}
