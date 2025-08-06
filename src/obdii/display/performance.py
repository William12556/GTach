#!/usr/bin/env python3
"""
Performance optimization system for OBDII display application.

Implements font caching, dirty rectangle rendering, and performance monitoring
to maintain 60 FPS operation on resource-constrained Raspberry Pi Zero 2W.
"""

import os
import sys
import logging
import threading
import time
import weakref
import gc
import platform
from collections import OrderedDict, deque
from typing import Optional, Tuple, Dict, List, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# Conditional imports for hardware dependencies
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring system health."""
    frame_time: float = 0.0
    fps: float = 0.0
    memory_usage_mb: float = 0.0
    cache_hit_rate: float = 0.0
    dirty_regions_count: int = 0
    full_redraws: int = 0
    timestamp: float = field(default_factory=time.time)


class CacheEvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"          # Least Recently Used
    SIZE = "size"        # Largest size first
    AGE = "age"          # Oldest first


class PlatformType(Enum):
    """Platform types for optimization."""
    RASPBERRY_PI = "raspberry_pi"
    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class FontCache:
    """
    Thread-safe LRU font cache for optimized memory usage.
    
    Features:
    - LRU eviction with configurable maximum size
    - Thread-safe access and eviction
    - Cache hit/miss statistics
    - Memory usage tracking
    - Debug logging for cache operations
    """
    
    def __init__(self, max_size: int = 10, eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU):
        """
        Initialize font cache.
        
        Args:
            max_size: Maximum number of font objects to cache
            eviction_policy: Policy for cache eviction
        """
        self.logger = logging.getLogger('FontCache')
        self.max_size = max_size
        self.eviction_policy = eviction_policy
        
        # Thread-safe cache storage
        self._cache_lock = threading.RLock()
        self._cache: OrderedDict[Tuple[int, str], pygame.font.Font] = OrderedDict()
        
        # Cache statistics
        self._stats_lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._creation_time: Dict[Tuple[int, str], float] = {}
        
        # Memory tracking
        self._estimated_memory_usage = 0
        
        self.logger.info(f"FontCache initialized with max_size={max_size}, policy={eviction_policy.value}")
    
    def get_font(self, size: int, font_path: Optional[str] = None) -> Optional[pygame.font.Font]:
        """
        Get cached font object or create new one.
        
        Args:
            size: Font size in pixels
            font_path: Optional path to font file (None for default)
            
        Returns:
            pygame.font.Font object or None if creation fails
        """
        if not PYGAME_AVAILABLE:
            return None
        
        cache_key = (size, font_path or "default")
        
        with self._cache_lock:
            # Check cache hit
            if cache_key in self._cache:
                font = self._cache[cache_key]
                # Move to end (most recently used) for LRU
                self._cache.move_to_end(cache_key)
                
                with self._stats_lock:
                    self._hits += 1
                
                self.logger.debug(f"Cache HIT: {cache_key}")
                return font
            
            # Cache miss - create new font
            with self._stats_lock:
                self._misses += 1
            
            self.logger.debug(f"Cache MISS: {cache_key}")
            
            try:
                # Initialize pygame font system if needed
                if not pygame.font.get_init():
                    pygame.font.init()
                
                # Create font object
                if font_path and os.path.exists(font_path):
                    font = pygame.font.Font(font_path, size)
                else:
                    font = pygame.font.Font(None, size)
                
                # Add to cache
                self._add_to_cache(cache_key, font)
                
                return font
                
            except Exception as e:
                self.logger.error(f"Failed to create font {cache_key}: {e}")
                return None
    
    def _add_to_cache(self, cache_key: Tuple[int, str], font: pygame.font.Font) -> None:
        """Add font to cache with eviction if necessary."""
        
        # Check if eviction needed
        while len(self._cache) >= self.max_size:
            self._evict_font()
        
        # Add font to cache
        self._cache[cache_key] = font
        self._creation_time[cache_key] = time.time()
        
        # Estimate memory usage (rough approximation)
        estimated_size = cache_key[0] * 50  # ~50 bytes per pixel size
        self._estimated_memory_usage += estimated_size
        
        self.logger.debug(f"Added to cache: {cache_key}, cache_size={len(self._cache)}")
    
    def _evict_font(self) -> None:
        """Evict font based on eviction policy."""
        if not self._cache:
            return
        
        with self._stats_lock:
            self._evictions += 1
        
        if self.eviction_policy == CacheEvictionPolicy.LRU:
            # Remove least recently used (first item in OrderedDict)
            cache_key, font = self._cache.popitem(last=False)
        elif self.eviction_policy == CacheEvictionPolicy.SIZE:
            # Remove largest font
            cache_key = max(self._cache.keys(), key=lambda k: k[0])
            font = self._cache.pop(cache_key)
        elif self.eviction_policy == CacheEvictionPolicy.AGE:
            # Remove oldest font
            cache_key = min(self._creation_time.keys(), key=lambda k: self._creation_time[k])
            font = self._cache.pop(cache_key)
        
        # Clean up tracking
        self._creation_time.pop(cache_key, None)
        
        # Update memory estimate
        estimated_size = cache_key[0] * 50
        self._estimated_memory_usage -= estimated_size
        
        self.logger.debug(f"Evicted from cache: {cache_key}")
    
    def clear(self) -> None:
        """Clear all cached fonts."""
        with self._cache_lock:
            self._cache.clear()
            self._creation_time.clear()
            self._estimated_memory_usage = 0
            
        self.logger.info("Font cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._stats_lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests) if total_requests > 0 else 0.0
            
            return {
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'estimated_memory_mb': self._estimated_memory_usage / (1024 * 1024)
            }
    
    def get_memory_usage(self) -> float:
        """Get estimated memory usage in MB."""
        return self._estimated_memory_usage / (1024 * 1024)


class DirtyRectTracker:
    """
    Thread-safe dirty rectangle tracking for efficient rendering.
    
    Features:
    - Track changed screen regions per frame
    - Merge overlapping rectangles for efficiency
    - Full redraw fallback mechanism
    - Thread-safe region management
    """
    
    def __init__(self, screen_size: Tuple[int, int], full_redraw_interval: int = 60):
        """
        Initialize dirty rectangle tracker.
        
        Args:
            screen_size: (width, height) of screen
            full_redraw_interval: Frames between full redraws
        """
        self.logger = logging.getLogger('DirtyRectTracker')
        self.screen_size = screen_size
        self.full_redraw_interval = full_redraw_interval
        
        # Thread-safe dirty region tracking
        self._dirty_lock = threading.RLock()
        self._dirty_regions: List[pygame.Rect] = []
        self._frame_counter = 0
        self._last_full_redraw = 0
        
        # Performance tracking
        self._merge_count = 0
        self._full_redraws = 0
        
        self.logger.info(f"DirtyRectTracker initialized for {screen_size}")
    
    def add_dirty_region(self, rect: pygame.Rect) -> None:
        """
        Add a dirty region to be updated.
        
        Args:
            rect: Rectangle area that needs updating
        """
        if not PYGAME_AVAILABLE:
            return
        
        with self._dirty_lock:
            # Clip to screen bounds
            clipped_rect = rect.clip(pygame.Rect(0, 0, *self.screen_size))
            if clipped_rect.width > 0 and clipped_rect.height > 0:
                self._dirty_regions.append(clipped_rect)
        
        self.logger.debug(f"Added dirty region: {rect}")
    
    def add_dirty_regions(self, rects: List[pygame.Rect]) -> None:
        """Add multiple dirty regions efficiently."""
        with self._dirty_lock:
            for rect in rects:
                clipped_rect = rect.clip(pygame.Rect(0, 0, *self.screen_size))
                if clipped_rect.width > 0 and clipped_rect.height > 0:
                    self._dirty_regions.append(clipped_rect)
    
    def get_dirty_regions(self, merge_threshold: int = 50) -> List[pygame.Rect]:
        """
        Get optimized list of dirty regions for current frame.
        
        Args:
            merge_threshold: Maximum distance for merging adjacent rectangles
            
        Returns:
            List of rectangles to update
        """
        with self._dirty_lock:
            self._frame_counter += 1
            
            # Check for full redraw
            if (self._frame_counter - self._last_full_redraw) >= self.full_redraw_interval:
                self._last_full_redraw = self._frame_counter
                self._full_redraws += 1
                self._dirty_regions.clear()
                
                full_rect = pygame.Rect(0, 0, *self.screen_size)
                self.logger.debug("Full redraw triggered")
                return [full_rect]
            
            if not self._dirty_regions:
                return []
            
            # Get current regions and clear for next frame
            regions = self._dirty_regions.copy()
            self._dirty_regions.clear()
            
            if len(regions) > 1:
                regions = self._merge_rectangles(regions, merge_threshold)
            
            self.logger.debug(f"Returning {len(regions)} dirty regions")
            return regions
    
    def _merge_rectangles(self, rects: List[pygame.Rect], threshold: int) -> List[pygame.Rect]:
        """Merge overlapping and nearby rectangles."""
        if len(rects) <= 1:
            return rects
        
        merged = []
        remaining = rects.copy()
        
        while remaining:
            current = remaining.pop(0)
            
            # Find all rectangles that should be merged with current
            to_merge = [current]
            i = 0
            while i < len(remaining):
                other = remaining[i]
                
                # Check if rectangles overlap or are close enough to merge
                if self._should_merge(current, other, threshold):
                    to_merge.append(remaining.pop(i))
                    # Expand current to include the merged rectangle
                    current = current.union(other)
                else:
                    i += 1
            
            # If we merged multiple rectangles, try again with the expanded rectangle
            if len(to_merge) > 1:
                self._merge_count += 1
                remaining.insert(0, current)
            else:
                merged.append(current)
        
        return merged
    
    def _should_merge(self, rect1: pygame.Rect, rect2: pygame.Rect, threshold: int) -> bool:
        """Check if two rectangles should be merged."""
        # Check if they overlap
        if rect1.colliderect(rect2):
            return True
        
        # Check if they're close enough to merge
        expanded_rect1 = rect1.inflate(threshold * 2, threshold * 2)
        return expanded_rect1.colliderect(rect2)
    
    def force_full_redraw(self) -> None:
        """Force a full redraw on the next frame."""
        with self._dirty_lock:
            self._last_full_redraw = 0  # Force full redraw
    
    def clear(self) -> None:
        """Clear all dirty regions."""
        with self._dirty_lock:
            self._dirty_regions.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dirty rectangle statistics."""
        return {
            'frame_count': self._frame_counter,
            'merge_count': self._merge_count,
            'full_redraws': self._full_redraws,
            'pending_regions': len(self._dirty_regions)
        }


class PerformanceMonitor:
    """
    Performance monitoring system for frame rates and memory usage.
    
    Features:
    - Frame time tracking with rolling averages
    - Memory usage monitoring
    - Performance alerts and thresholds
    - Metrics logging to file
    """
    
    def __init__(self, log_file: Optional[str] = None, sample_interval: float = 5.0):
        """
        Initialize performance monitor.
        
        Args:
            log_file: Optional file path for metrics logging
            sample_interval: Seconds between memory usage samples
        """
        self.logger = logging.getLogger('PerformanceMonitor')
        self.log_file = log_file
        self.sample_interval = sample_interval
        
        # Performance tracking
        self._perf_lock = threading.Lock()
        self._frame_times = deque(maxlen=60)  # Last 60 frames
        self._last_frame_time = time.time()
        self._frame_count = 0
        
        # Memory tracking
        self._memory_samples = deque(maxlen=720)  # Last hour at 5s intervals
        self._last_memory_sample = time.time()
        
        # Alert thresholds
        self.fps_threshold = 30.0  # Alert if FPS drops below 30
        self.memory_threshold_mb = 256.0  # Alert if memory exceeds 256MB
        
        # Start background monitoring
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info(f"PerformanceMonitor initialized, logging to: {log_file}")
    
    def record_frame(self) -> float:
        """
        Record frame completion and return frame time.
        
        Returns:
            Frame time in milliseconds
        """
        current_time = time.time()
        
        with self._perf_lock:
            frame_time = (current_time - self._last_frame_time) * 1000  # Convert to ms
            self._frame_times.append(frame_time)
            self._last_frame_time = current_time
            self._frame_count += 1
        
        return frame_time
    
    def get_current_fps(self) -> float:
        """Get current FPS based on recent frame times."""
        with self._perf_lock:
            if not self._frame_times:
                return 0.0
            
            avg_frame_time_ms = sum(self._frame_times) / len(self._frame_times)
            if avg_frame_time_ms > 0:
                return 1000.0 / avg_frame_time_ms
            return 0.0
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if not PSUTIL_AVAILABLE:
            return 0.0
        
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except Exception as e:
            self.logger.warning(f"Failed to get memory usage: {e}")
            return 0.0
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        with self._perf_lock:
            frame_time = self._frame_times[-1] if self._frame_times else 0.0
            fps = self.get_current_fps()
        
        memory_mb = self.get_memory_usage()
        
        return PerformanceMetrics(
            frame_time=frame_time,
            fps=fps,
            memory_usage_mb=memory_mb,
            cache_hit_rate=0.0,  # Will be updated by caller
            dirty_regions_count=0,  # Will be updated by caller
            full_redraws=0  # Will be updated by caller
        )
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                current_time = time.time()
                
                # Sample memory usage
                if current_time - self._last_memory_sample >= self.sample_interval:
                    memory_mb = self.get_memory_usage()
                    self._memory_samples.append((current_time, memory_mb))
                    self._last_memory_sample = current_time
                    
                    # Check thresholds
                    self._check_performance_alerts(memory_mb)
                    
                    # Log metrics
                    self._log_metrics()
                
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)
    
    def _check_performance_alerts(self, memory_mb: float) -> None:
        """Check performance thresholds and log alerts."""
        fps = self.get_current_fps()
        
        if fps > 0 and fps < self.fps_threshold:
            self.logger.warning(f"Performance alert: FPS dropped to {fps:.1f}")
        
        if memory_mb > self.memory_threshold_mb:
            self.logger.warning(f"Memory alert: Usage {memory_mb:.1f}MB exceeds threshold")
    
    def _log_metrics(self) -> None:
        """Log performance metrics to file."""
        if not self.log_file:
            return
        
        try:
            metrics = self.get_metrics()
            
            log_entry = (
                f"{time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"FPS: {metrics.fps:.1f}, "
                f"Frame: {metrics.frame_time:.1f}ms, "
                f"Memory: {metrics.memory_usage_mb:.1f}MB\n"
            )
            
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
                
        except Exception as e:
            self.logger.error(f"Failed to log metrics: {e}")
    
    def stop(self) -> None:
        """Stop performance monitoring."""
        self._monitoring = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)


class PlatformOptimizer:
    """
    Platform-specific optimizations for different hardware.
    
    Features:
    - Raspberry Pi specific optimizations
    - Mac development mode features
    - Conditional platform features
    - Hardware capability detection
    """
    
    def __init__(self):
        self.logger = logging.getLogger('PlatformOptimizer')
        self.platform = self._detect_platform()
        self.optimizations = self._get_optimizations()
        
        self.logger.info(f"Platform detected: {self.platform.value}")
        self.logger.info(f"Optimizations enabled: {list(self.optimizations.keys())}")
    
    def _detect_platform(self) -> PlatformType:
        """Detect the current platform."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Check for Raspberry Pi
        if system == "linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    if 'raspberry pi' in cpuinfo or 'bcm' in cpuinfo:
                        return PlatformType.RASPBERRY_PI
            except:
                pass
            return PlatformType.LINUX
        
        elif system == "darwin":
            return PlatformType.MACOS
        elif system == "windows":
            return PlatformType.WINDOWS
        else:
            return PlatformType.UNKNOWN
    
    def _get_optimizations(self) -> Dict[str, bool]:
        """Get platform-specific optimization settings."""
        if self.platform == PlatformType.RASPBERRY_PI:
            return {
                'disable_alpha_blending': True,
                'reduce_color_depth': True,
                'minimize_memory_usage': True,
                'aggressive_caching': True,
                'disable_debug_rendering': True,
                'prefer_software_rendering': True
            }
        elif self.platform == PlatformType.MACOS:
            return {
                'disable_alpha_blending': False,
                'reduce_color_depth': False,
                'minimize_memory_usage': False,
                'aggressive_caching': False,
                'disable_debug_rendering': False,
                'prefer_software_rendering': False
            }
        else:
            # Conservative defaults for unknown platforms
            return {
                'disable_alpha_blending': False,
                'reduce_color_depth': False,
                'minimize_memory_usage': True,
                'aggressive_caching': True,
                'disable_debug_rendering': True,
                'prefer_software_rendering': False
            }
    
    def should_disable_alpha_blending(self) -> bool:
        """Check if alpha blending should be disabled for performance."""
        return self.optimizations.get('disable_alpha_blending', False)
    
    def should_reduce_color_depth(self) -> bool:
        """Check if color depth should be reduced."""
        return self.optimizations.get('reduce_color_depth', False)
    
    def should_minimize_memory(self) -> bool:
        """Check if memory usage should be minimized."""
        return self.optimizations.get('minimize_memory_usage', True)
    
    def get_cache_size(self) -> int:
        """Get recommended cache size for platform."""
        if self.platform == PlatformType.RASPBERRY_PI:
            return 5  # Smaller cache for Pi
        else:
            return 10  # Default cache size


class PerformanceManager:
    """
    Unified performance management system.
    
    Coordinates font caching, dirty rectangle rendering, and performance monitoring
    for optimal system performance.
    """
    
    def __init__(self, screen_size: Tuple[int, int], log_file: Optional[str] = None):
        """
        Initialize performance manager.
        
        Args:
            screen_size: (width, height) of display
            log_file: Optional file for performance logging
        """
        self.logger = logging.getLogger('PerformanceManager')
        
        # Initialize subsystems
        self.platform_optimizer = PlatformOptimizer()
        
        cache_size = self.platform_optimizer.get_cache_size()
        self.font_cache = FontCache(max_size=cache_size)
        
        self.dirty_tracker = DirtyRectTracker(screen_size)
        self.performance_monitor = PerformanceMonitor(log_file)
        
        # Surface cache for rendered elements
        self._surface_cache: Dict[str, pygame.Surface] = {}
        self._surface_cache_lock = threading.Lock()
        
        # Memory pressure callbacks
        self._memory_callbacks: List[Callable] = []
        
        self.logger.info("PerformanceManager initialized")
    
    def get_font(self, size: int, font_path: Optional[str] = None) -> Optional[pygame.font.Font]:
        """Get cached font object."""
        return self.font_cache.get_font(size, font_path)
    
    def add_dirty_region(self, rect: pygame.Rect) -> None:
        """Add dirty region for next frame update."""
        self.dirty_tracker.add_dirty_region(rect)
    
    def get_dirty_regions(self) -> List[pygame.Rect]:
        """Get regions to update for current frame."""
        return self.dirty_tracker.get_dirty_regions()
    
    def record_frame(self) -> float:
        """Record frame completion and return frame time."""
        return self.performance_monitor.record_frame()
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        base_metrics = self.performance_monitor.get_metrics()
        font_stats = self.font_cache.get_stats()
        dirty_stats = self.dirty_tracker.get_stats()
        
        return {
            'fps': base_metrics.fps,
            'frame_time_ms': base_metrics.frame_time,
            'memory_usage_mb': base_metrics.memory_usage_mb,
            'font_cache_hit_rate': font_stats['hit_rate'],
            'font_cache_size': font_stats['cache_size'],
            'dirty_regions_count': dirty_stats['pending_regions'],
            'full_redraws': dirty_stats['full_redraws'],
            'platform': self.platform_optimizer.platform.value,
            'timestamp': base_metrics.timestamp
        }
    
    def cache_surface(self, key: str, surface: pygame.Surface) -> None:
        """Cache a rendered surface for reuse."""
        if self.platform_optimizer.should_minimize_memory():
            return  # Skip caching on memory-constrained platforms
        
        with self._surface_cache_lock:
            self._surface_cache[key] = surface.copy()
    
    def get_cached_surface(self, key: str) -> Optional[pygame.Surface]:
        """Get cached surface if available."""
        with self._surface_cache_lock:
            return self._surface_cache.get(key)
    
    def clear_surface_cache(self) -> None:
        """Clear all cached surfaces."""
        with self._surface_cache_lock:
            self._surface_cache.clear()
        
        self.logger.debug("Surface cache cleared")
    
    def register_memory_callback(self, callback: Callable) -> None:
        """Register callback for memory pressure events."""
        self._memory_callbacks.append(callback)
    
    def trigger_memory_cleanup(self) -> None:
        """Trigger memory cleanup callbacks."""
        self.logger.info("Triggering memory cleanup")
        
        # Clear caches
        self.font_cache.clear()
        self.clear_surface_cache()
        
        # Call registered callbacks
        for callback in self._memory_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in memory callback: {e}")
        
        # Force garbage collection
        gc.collect()
    
    def cleanup(self) -> None:
        """Clean up performance manager resources."""
        self.performance_monitor.stop()
        self.font_cache.clear()
        self.clear_surface_cache()
        
        self.logger.info("PerformanceManager cleaned up")


# Global performance manager instance
_performance_manager = None
_manager_lock = threading.Lock()


def get_performance_manager() -> Optional[PerformanceManager]:
    """Get global performance manager instance."""
    return _performance_manager


def initialize_performance_manager(screen_size: Tuple[int, int], 
                                 log_file: Optional[str] = None) -> PerformanceManager:
    """
    Initialize global performance manager.
    
    Args:
        screen_size: (width, height) of display
        log_file: Optional performance log file
        
    Returns:
        PerformanceManager instance
    """
    global _performance_manager
    
    with _manager_lock:
        if _performance_manager is None:
            _performance_manager = PerformanceManager(screen_size, log_file)
        
        return _performance_manager


def cleanup_performance_manager() -> None:
    """Clean up global performance manager."""
    global _performance_manager
    
    with _manager_lock:
        if _performance_manager:
            _performance_manager.cleanup()
            _performance_manager = None