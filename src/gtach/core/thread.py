#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Thread management for OBDII display application.
Handles thread lifecycle and inter-thread communication.

This module provides thread-safe thread management with proper synchronization,
atomic state transitions, and async/sync coordination.
"""

import logging
import threading
import queue
import time
import weakref
from enum import Enum, auto
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

class ThreadStatus(Enum):
    """Thread status enumeration with atomic transitions"""
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()
    
    def can_transition_to(self, new_status: 'ThreadStatus') -> bool:
        """Check if transition to new status is valid"""
        valid_transitions = {
            ThreadStatus.STARTING: {ThreadStatus.RUNNING, ThreadStatus.FAILED, ThreadStatus.STOPPING},
            ThreadStatus.RUNNING: {ThreadStatus.STOPPING, ThreadStatus.FAILED},
            ThreadStatus.STOPPING: {ThreadStatus.STOPPED, ThreadStatus.FAILED},
            ThreadStatus.STOPPED: {ThreadStatus.STARTING},
            ThreadStatus.FAILED: {ThreadStatus.STOPPING, ThreadStatus.STOPPED},
        }
        return new_status in valid_transitions.get(self, set())

@dataclass(frozen=False, eq=False)
class ThreadInfo:
    """Thread information and state tracking with synchronization"""
    thread: threading.Thread
    status: ThreadStatus
    # time.monotonic() seconds, not wall-clock time (issue-b9ee7428).
    last_heartbeat: float
    last_error: Optional[Exception] = None
    stop_func: Optional[Callable] = None
    creation_time: float = field(default_factory=time.time)
    
    def __hash__(self):
        """Make ThreadInfo hashable based on thread identity"""
        return hash((id(self.thread), self.creation_time))

class ThreadManager:
    """Thread-safe manager for application threads and worker pool
    
    Provides atomic state transitions, proper resource cleanup,
    and async/sync coordination with comprehensive error handling.
    """
    
    def __init__(self, num_workers: int = 3, platform_optimized: bool = True):
        """Initialize thread manager with thread-safe architecture
        
        Args:
            num_workers: Number of worker threads in pool
            platform_optimized: Enable platform-specific optimizations
        """
        self.logger = logging.getLogger('ThreadManager')
        
        # Thread-safe state management
        self.threads: Dict[str, ThreadInfo] = {}
        self._state_lock = threading.RLock()  # Reentrant lock for nested operations
        self._shutdown_event = threading.Event()
        self._cleanup_lock = threading.Lock()  # Separate lock for cleanup operations

        # Thread pool for background tasks with proper cleanup
        self.worker_pool = ThreadPoolExecutor(
            max_workers=num_workers,
            thread_name_prefix='TMWorker'
        )
        
        # Resource tracking for cleanup verification
        self._resource_tracker = weakref.WeakSet()
        
        # Message queue for thread communication — bounded to prevent stale data accumulation
        self.message_queue = queue.Queue(maxsize=5)
        self.data_available = threading.Event()

        # Backward compatibility for watchdog
        self._lock = self._state_lock
        
        self.logger.debug(f"ThreadManager initialized with {num_workers} workers")

    def register_thread(self, name: str, thread: threading.Thread, stop_func=None) -> None:
        """Register a new thread for management with atomic state transition"""
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot register thread during shutdown")

        with self._state_lock:
            if name in self.threads:
                old_thread = self.threads[name]
                if (old_thread.status in {ThreadStatus.RUNNING, ThreadStatus.STARTING}
                        and old_thread.thread.is_alive()):
                    self.logger.warning(f"Thread {name} already exists and is active")
                    return
                # A dead entry is replaced (issue-860fd5f7).
                self.logger.debug(f"Replacing stale entry for {name}")

            thread_info = ThreadInfo(
                thread=thread,
                status=ThreadStatus.STARTING,
                last_heartbeat=time.monotonic()
            )
            thread_info.stop_func = stop_func
            self.threads[name] = thread_info
            self._resource_tracker.add(thread_info)

        self.logger.debug(f"Registered thread: {name} (TID: {thread.ident})")

    def update_heartbeat(self, name: str) -> None:
        """Update thread heartbeat timestamp with atomic status transition"""
        with self._state_lock:
            if name not in self.threads:
                self.logger.warning(f"Heartbeat for unknown thread: {name}")
                return

            thread_info = self.threads[name]
            current_time = time.monotonic()

            # Atomic status transition
            if thread_info.status == ThreadStatus.STARTING:
                if thread_info.status.can_transition_to(ThreadStatus.RUNNING):
                    thread_info.status = ThreadStatus.RUNNING
                    self.logger.debug(f"Thread {name} transitioned to RUNNING")

            thread_info.last_heartbeat = current_time
                
    def get_thread_status(self, name: str) -> Optional[ThreadStatus]:
        """Get current thread status thread-safely"""
        with self._state_lock:
            thread_info = self.threads.get(name)
            return thread_info.status if thread_info else None
            
    def stop_thread(self, name: str, timeout: float = 5.0) -> bool:
        """Stop a specific thread with proper state management"""
        with self._state_lock:
            if name not in self.threads:
                self.logger.warning(f"Cannot stop unknown thread: {name}")
                return False

            thread_info = self.threads[name]

            if not thread_info.status.can_transition_to(ThreadStatus.STOPPING):
                self.logger.debug(f"Thread {name} already in terminal state: {thread_info.status}")
                return thread_info.status == ThreadStatus.STOPPED

            thread_info.status = ThreadStatus.STOPPING

        # stop_func runs after the lock is released and before the
        # join, so the thread is already STOPPING when it is released
        # (CLAUDE.md §4 rule 8, issue-860fd5f7).
        stop_func = thread_info.stop_func
        if stop_func is not None:
            try:
                stop_func()
            except Exception as e:
                self.logger.error(f"stop_func failed for {name}: {e}", exc_info=True)

        # Join outside the lock. update_heartbeat, register_thread
        # and get_thread_status all take _state_lock, so joining
        # under it blocks the very threads whose progress the join
        # is waiting on — the same defect corrected in
        # core/watchdog.py by change-5a9dc15e. thread_info is
        # bound above, so the join is unaffected by the release.
        success = True
        if thread_info.thread.is_alive():
            thread_info.thread.join(timeout=timeout)
            success = not thread_info.thread.is_alive()

        # Update final status
        with self._state_lock:
            if name in self.threads:
                self.threads[name].status = ThreadStatus.STOPPED if success else ThreadStatus.FAILED

        if success:
            self.logger.debug(f"Successfully stopped thread: {name}")
        else:
            self.logger.warning(f"Thread {name} did not stop within {timeout}s")

        return success
    
    def shutdown(self, timeout: float = 10.0) -> None:
        """Shutdown thread manager with proper resource cleanup and verification"""
        shutdown_start = time.monotonic()
        self.logger.info("Initiating ThreadManager shutdown")
        
        # Signal shutdown to all components
        self._shutdown_event.set()

        # Shutdown worker pool with timeout (Python 3.9 doesn't support timeout parameter)
        try:
            self.worker_pool.shutdown(wait=True)
            self.logger.debug("Worker pool shutdown complete")
        except Exception as e:
            self.logger.warning(f"Worker pool shutdown error: {e}")
            
        # Stop all managed threads with proper state transitions
        with self._cleanup_lock:
            remaining_timeout = timeout - (time.monotonic() - shutdown_start)
            thread_count = len(self.threads)
            budgeted_per_thread = remaining_timeout / max(1, thread_count)
            per_thread_timeout = max(1.0, budgeted_per_thread)

            # The floor guarantees each join a usable timeout and in
            # doing so abandons the caller's aggregate budget. Say
            # so rather than substituting it silently (core review
            # §5.5). The __del__ path reaches this with a 2.0s
            # budget and three threads — 0.667s each — so the
            # overrun does not require a slow worker pool.
            if thread_count and budgeted_per_thread < 1.0:
                self.logger.warning(
                    f"Shutdown budget exceeded: {timeout:.1f}s requested, "
                    f"{remaining_timeout:.1f}s remaining for {thread_count} "
                    f"thread(s) ({budgeted_per_thread:.2f}s each); flooring at "
                    f"{per_thread_timeout:.1f}s, worst case "
                    f"{per_thread_timeout * thread_count:.1f}s"
                )

            stopped_count = 0
            failed_count = 0
            
            for name in list(self.threads.keys()):
                try:
                    if self.stop_thread(name, timeout=per_thread_timeout):
                        stopped_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self.logger.error(f"Error stopping thread {name}: {e}", exc_info=True)
                    failed_count += 1
                    
        # Resource cleanup verification
        total_threads = len(self.threads)
        cleanup_time = time.monotonic() - shutdown_start
        
        self.logger.info(
            f"ThreadManager shutdown complete: {stopped_count}/{total_threads} threads stopped, "
            f"{failed_count} failed, cleanup took {cleanup_time:.2f}s"
        )
        
        # Final cleanup
        with self._state_lock:
            self.threads.clear()
            
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup"""
        self.shutdown()
        
    def __del__(self):
        """Ensure cleanup on garbage collection"""
        try:
            if not self._shutdown_event.is_set():
                self.shutdown(timeout=2.0)
        except Exception:
            pass  # Best effort cleanup