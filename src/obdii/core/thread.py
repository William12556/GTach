#!/usr/bin/env python3
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
import asyncio
import weakref
from enum import Enum, auto
from typing import Dict, Optional, Callable, Any, Set, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from contextlib import contextmanager

class ThreadStatus(Enum):
    """Thread status enumeration with atomic transitions"""
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()
    RESTARTING = auto()
    
    def can_transition_to(self, new_status: 'ThreadStatus') -> bool:
        """Check if transition to new status is valid"""
        valid_transitions = {
            ThreadStatus.STARTING: {ThreadStatus.RUNNING, ThreadStatus.FAILED, ThreadStatus.STOPPING},
            ThreadStatus.RUNNING: {ThreadStatus.STOPPING, ThreadStatus.FAILED, ThreadStatus.RESTARTING},
            ThreadStatus.STOPPING: {ThreadStatus.STOPPED, ThreadStatus.FAILED},
            ThreadStatus.STOPPED: {ThreadStatus.STARTING, ThreadStatus.RESTARTING},
            ThreadStatus.FAILED: {ThreadStatus.RESTARTING, ThreadStatus.STOPPING, ThreadStatus.STOPPED},
            ThreadStatus.RESTARTING: {ThreadStatus.STARTING, ThreadStatus.FAILED, ThreadStatus.STOPPED}
        }
        return new_status in valid_transitions.get(self, set())

@dataclass(frozen=False, eq=False)
class ThreadInfo:
    """Thread information and state tracking with synchronization"""
    thread: threading.Thread
    status: ThreadStatus
    last_heartbeat: float
    restart_count: int = 0
    last_error: Optional[Exception] = None
    target_func: Optional[Callable] = None
    target_args: tuple = field(default_factory=tuple)
    target_kwargs: dict = field(default_factory=dict)
    creation_time: float = field(default_factory=time.time)
    restart_future: Optional[Future] = None
    
    def __hash__(self):
        """Make ThreadInfo hashable based on thread identity"""
        return hash((id(self.thread), self.creation_time))
    
    def __post_init__(self):
        """Extract and store thread target info safely"""
        if hasattr(self.thread, '_target') and self.thread._target:
            self.target_func = self.thread._target
            self.target_args = getattr(self.thread, '_args', ())
            self.target_kwargs = getattr(self.thread, '_kwargs', {})

class AsyncSyncBridge:
    """Bridge for coordinating async and sync execution contexts"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._message_queue = queue.Queue()
        self._response_queue = queue.Queue()
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._bridge_lock = threading.RLock()
        self._active_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = threading.Event()
        
    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop for async operations"""
        with self._bridge_lock:
            self._event_loop = loop
            
    def submit_async_task(self, coro) -> Future:
        """Submit async coroutine from sync context"""
        with self._bridge_lock:
            if not self._event_loop or self._shutdown_event.is_set():
                future = Future()
                future.set_exception(RuntimeError("Event loop not available or shutting down"))
                return future
                
            return asyncio.run_coroutine_threadsafe(coro, self._event_loop)
            
    def send_message(self, message: Any, timeout: float = 5.0) -> Any:
        """Send message between contexts with timeout"""
        if self._shutdown_event.is_set():
            raise RuntimeError("Bridge is shutting down")
            
        try:
            self._message_queue.put(message, timeout=timeout)
            return self._response_queue.get(timeout=timeout)
        except queue.Full:
            raise TimeoutError(f"Message send timeout after {timeout}s")
        except queue.Empty:
            raise TimeoutError(f"Response timeout after {timeout}s")
            
    def shutdown(self) -> None:
        """Shutdown bridge and cleanup resources"""
        self.logger.debug("AsyncSyncBridge shutting down")
        self._shutdown_event.set()
        
        # Cancel active async tasks
        with self._bridge_lock:
            for task in self._active_tasks.copy():
                if not task.done():
                    task.cancel()
                    
            # Clear queues
            while not self._message_queue.empty():
                try:
                    self._message_queue.get_nowait()
                except queue.Empty:
                    break
                    
            while not self._response_queue.empty():
                try:
                    self._response_queue.get_nowait()
                except queue.Empty:
                    break

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
        
        # Platform optimization
        if platform_optimized:
            import platform
            if platform.system() == 'Darwin':  # macOS development
                num_workers = min(num_workers * 2, 8)  # Higher concurrency for testing
            else:  # Raspberry Pi deployment 
                num_workers = min(num_workers, 4)  # Conservative for Pi Zero 2W
                
        # Thread pool for background tasks with proper cleanup
        self.worker_pool = ThreadPoolExecutor(
            max_workers=num_workers,
            thread_name_prefix='TMWorker'
        )
        
        # Async/sync coordination
        self.async_bridge = AsyncSyncBridge(self.logger)
        
        # Resource tracking for cleanup verification
        self._active_futures: Set[Future] = set()
        self._resource_tracker = weakref.WeakSet()
        
        # Message queue for thread communication
        self.message_queue = queue.Queue()
        self.data_available = threading.Event()
        
        # Performance monitoring
        self._operation_count = 0
        self._sync_overhead_start = 0.0
        
        # Backward compatibility for watchdog
        self._lock = self._state_lock
        
        self.logger.debug(f"ThreadManager initialized with {num_workers} workers")

    @contextmanager
    def _sync_timing(self):
        """Context manager for tracking synchronization overhead"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            overhead = time.perf_counter() - start_time
            self._operation_count += 1
            if self._operation_count % 100 == 0:  # Log every 100 operations
                self.logger.debug(f"Sync overhead: {overhead:.4f}ms (op #{self._operation_count})")
    
    def register_thread(self, name: str, thread: threading.Thread) -> None:
        """Register a new thread for management with atomic state transition"""
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot register thread during shutdown")
            
        with self._sync_timing():
            with self._state_lock:
                if name in self.threads:
                    old_thread = self.threads[name]
                    if old_thread.status in {ThreadStatus.RUNNING, ThreadStatus.STARTING}:
                        self.logger.warning(f"Thread {name} already exists and is active")
                        return
                        
                thread_info = ThreadInfo(
                    thread=thread,
                    status=ThreadStatus.STARTING,
                    last_heartbeat=time.time()
                )
                self.threads[name] = thread_info
                self._resource_tracker.add(thread_info)
                
        self.logger.debug(f"Registered thread: {name} (TID: {thread.ident})")

    def update_heartbeat(self, name: str) -> None:
        """Update thread heartbeat timestamp with atomic status transition"""
        with self._sync_timing():
            with self._state_lock:
                if name not in self.threads:
                    self.logger.warning(f"Heartbeat for unknown thread: {name}")
                    return
                    
                thread_info = self.threads[name]
                current_time = time.time()
                
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
            
    def get_thread_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get thread information snapshot"""
        with self._state_lock:
            thread_info = self.threads.get(name)
            if not thread_info:
                return None
                
            return {
                'name': name,
                'status': thread_info.status,
                'last_heartbeat': thread_info.last_heartbeat,
                'restart_count': thread_info.restart_count,
                'creation_time': thread_info.creation_time,
                'is_alive': thread_info.thread.is_alive(),
                'thread_id': thread_info.thread.ident,
                'last_error': str(thread_info.last_error) if thread_info.last_error else None
            }
            
    def list_threads(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all managed threads"""
        with self._state_lock:
            return {name: self.get_thread_info(name) for name in self.threads}
            
    def is_healthy(self, heartbeat_timeout: float = 30.0) -> bool:
        """Check if all threads are healthy"""
        current_time = time.time()
        with self._state_lock:
            for name, thread_info in self.threads.items():
                if thread_info.status == ThreadStatus.FAILED:
                    return False
                if (thread_info.status == ThreadStatus.RUNNING and 
                    current_time - thread_info.last_heartbeat > heartbeat_timeout):
                    return False
            return True
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics for monitoring"""
        with self._state_lock:
            status_counts = {}
            total_restarts = 0
            oldest_thread = None
            newest_thread = None
            
            for thread_info in self.threads.values():
                status = thread_info.status.name
                status_counts[status] = status_counts.get(status, 0) + 1
                total_restarts += thread_info.restart_count
                
                if oldest_thread is None or thread_info.creation_time < oldest_thread:
                    oldest_thread = thread_info.creation_time
                if newest_thread is None or thread_info.creation_time > newest_thread:
                    newest_thread = thread_info.creation_time
                    
            return {
                'total_threads': len(self.threads),
                'status_counts': status_counts,
                'total_restarts': total_restarts,
                'operation_count': self._operation_count,
                'active_futures': len(self._active_futures),
                'uptime': time.time() - (oldest_thread or time.time()),
                'is_shutting_down': self._shutdown_event.is_set()
            }

    def handle_thread_failure(self, name: str, error: Exception) -> None:
        """Handle thread failure with atomic state transition and safe restart"""
        if self._shutdown_event.is_set():
            self.logger.debug(f"Ignoring failure for {name} during shutdown")
            return
            
        with self._sync_timing():
            with self._state_lock:
                if name not in self.threads:
                    self.logger.warning(f"Failure reported for unknown thread: {name}")
                    return
                    
                thread_info = self.threads[name]
                
                # Atomic status transition
                if not thread_info.status.can_transition_to(ThreadStatus.FAILED):
                    self.logger.warning(
                        f"Invalid status transition for {name}: {thread_info.status} -> FAILED"
                    )
                    return
                    
                thread_info.status = ThreadStatus.FAILED
                thread_info.last_error = error
                
                # Calculate backoff with jitter to prevent thundering herd
                base_backoff = min(2 ** thread_info.restart_count, 8)
                jitter = base_backoff * 0.1 * (hash(name) % 10) / 10  # Deterministic jitter
                backoff = base_backoff + jitter
                thread_info.restart_count += 1
                
                self.logger.error(
                    f"Thread {name} failed: {type(error).__name__}: {error}. "
                    f"Restart #{thread_info.restart_count} in {backoff:.2f}s",
                    exc_info=True  # Full traceback for debugging
                )
                
                # Cancel any existing restart operation
                if thread_info.restart_future and not thread_info.restart_future.done():
                    thread_info.restart_future.cancel()
                    
                # Submit restart with future tracking
                restart_future = self.worker_pool.submit(self._restart_thread, name, backoff)
                thread_info.restart_future = restart_future
                self._active_futures.add(restart_future)
                
                # Clean up completed futures
                restart_future.add_done_callback(lambda f: self._active_futures.discard(f))

    def _restart_thread(self, name: str, backoff: float) -> None:
        """Restart failed thread after backoff with proper error handling"""
        try:
            # Interruptible sleep that respects shutdown
            for _ in range(int(backoff * 10)):
                if self._shutdown_event.is_set():
                    self.logger.debug(f"Restart cancelled for {name} due to shutdown")
                    return
                time.sleep(0.1)
                
            with self._sync_timing():
                with self._state_lock:
                    if self._shutdown_event.is_set():
                        return
                        
                    if name not in self.threads:
                        self.logger.warning(f"Cannot restart {name}: thread no longer registered")
                        return
                        
                    thread_info = self.threads[name]
                    
                    # Verify we're still in a restartable state
                    if thread_info.status not in {ThreadStatus.FAILED, ThreadStatus.STOPPED}:
                        self.logger.debug(f"Thread {name} status changed to {thread_info.status}, restart cancelled")
                        return
                        
                    # Atomic transition to restarting state
                    if not thread_info.status.can_transition_to(ThreadStatus.RESTARTING):
                        self.logger.warning(f"Cannot restart {name}: invalid state {thread_info.status}")
                        return
                        
                    thread_info.status = ThreadStatus.RESTARTING
                    
                    # Validate thread target function is available
                    if not thread_info.target_func:
                        self.logger.error(f"Cannot restart {name}: no target function available")
                        thread_info.status = ThreadStatus.STOPPED
                        return
                        
                    try:
                        # Create new thread with stored target info
                        new_thread = threading.Thread(
                            target=thread_info.target_func,
                            args=thread_info.target_args,
                            kwargs=thread_info.target_kwargs,
                            name=f"{name}_r{thread_info.restart_count}",
                            daemon=thread_info.thread.daemon
                        )
                        
                        # Update thread info atomically
                        thread_info.thread = new_thread
                        thread_info.status = ThreadStatus.STARTING
                        thread_info.last_heartbeat = time.time()
                        thread_info.last_error = None
                        
                        # Start the new thread
                        new_thread.start()
                        self.logger.info(f"Successfully restarted thread: {name} (attempt #{thread_info.restart_count})")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to restart thread {name}: {e}", exc_info=True)
                        thread_info.status = ThreadStatus.FAILED
                        thread_info.last_error = e
                        
        except Exception as e:
            self.logger.error(f"Unexpected error in _restart_thread for {name}: {e}", exc_info=True)
            # Try to update status if possible
            try:
                with self._state_lock:
                    if name in self.threads:
                        self.threads[name].status = ThreadStatus.FAILED
                        self.threads[name].last_error = e
            except Exception:
                pass  # Best effort status update

    def stop_thread(self, name: str, timeout: float = 5.0) -> bool:
        """Stop a specific thread with proper state management"""
        with self._sync_timing():
            with self._state_lock:
                if name not in self.threads:
                    self.logger.warning(f"Cannot stop unknown thread: {name}")
                    return False
                    
                thread_info = self.threads[name]
                
                if not thread_info.status.can_transition_to(ThreadStatus.STOPPING):
                    self.logger.debug(f"Thread {name} already in terminal state: {thread_info.status}")
                    return thread_info.status == ThreadStatus.STOPPED
                    
                thread_info.status = ThreadStatus.STOPPING
                
                # Cancel any pending restart
                if thread_info.restart_future and not thread_info.restart_future.done():
                    thread_info.restart_future.cancel()
                    
            # Join thread outside of lock to prevent deadlock
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
        shutdown_start = time.time()
        self.logger.info("Initiating ThreadManager shutdown")
        
        # Signal shutdown to all components
        self._shutdown_event.set()
        
        # Stop async bridge first
        self.async_bridge.shutdown()
        
        # Cancel all active futures
        cancelled_count = 0
        for future in list(self._active_futures):
            if not future.done():
                future.cancel()
                cancelled_count += 1
        if cancelled_count > 0:
            self.logger.debug(f"Cancelled {cancelled_count} active futures")
            
        # Shutdown worker pool with timeout (Python 3.9 doesn't support timeout parameter)
        try:
            self.worker_pool.shutdown(wait=True)
            self.logger.debug("Worker pool shutdown complete")
        except Exception as e:
            self.logger.warning(f"Worker pool shutdown error: {e}")
            
        # Stop all managed threads with proper state transitions
        with self._cleanup_lock:
            remaining_timeout = timeout - (time.time() - shutdown_start)
            per_thread_timeout = max(1.0, remaining_timeout / max(1, len(self.threads)))
            
            stopped_count = 0
            failed_count = 0
            
            for name in list(self.threads.keys()):
                try:
                    if self.stop_thread(name, timeout=per_thread_timeout):
                        stopped_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self.logger.error(f"Error stopping thread {name}: {e}")
                    failed_count += 1
                    
        # Resource cleanup verification
        total_threads = len(self.threads)
        cleanup_time = time.time() - shutdown_start
        
        self.logger.info(
            f"ThreadManager shutdown complete: {stopped_count}/{total_threads} threads stopped, "
            f"{failed_count} failed, cleanup took {cleanup_time:.2f}s"
        )
        
        # Final cleanup
        with self._state_lock:
            self.threads.clear()
            self._active_futures.clear()
            
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