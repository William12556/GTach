#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Async operation framework for non-blocking UI operations.
Provides worker thread architecture for setup operations and other blocking tasks.
"""

import logging
import threading
import queue
import time
from enum import Enum, auto
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field

class OperationType(Enum):
    """Types of async operations"""
    BLUETOOTH_INIT = auto()
    DEVICE_DISCOVERY = auto()
    DEVICE_PAIRING = auto()
    OBD_CONNECTION_TEST = auto()
    GENERAL_TASK = auto()

class OperationStatus(Enum):
    """Status of async operations"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()

@dataclass
class AsyncOperation:
    """Represents an async operation"""
    id: str
    operation_type: OperationType
    status: OperationStatus = OperationStatus.PENDING
    progress: float = 0.0
    result: Any = None
    error: Optional[Exception] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AsyncOperationManager:
    """
    Manages async operations to keep UI responsive during blocking tasks.
    
    Features:
    - Worker thread pool for executing blocking operations
    - Thread-safe communication with UI thread
    - Progress tracking and status updates
    - Cancellation support
    - Error handling and recovery
    """
    
    def __init__(self, max_workers: int = 2):
        """Initialize async operation manager
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.logger = logging.getLogger('AsyncOperationManager')
        self.max_workers = max_workers
        
        # Thread-safe data structures
        self.operations: Dict[str, AsyncOperation] = {}
        self.operation_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self._operations_lock = threading.Lock()
        
        # Worker threads
        self.workers = []
        self._shutdown_event = threading.Event()
        self._next_operation_id = 0
        
        # Progress callbacks
        self.progress_callbacks: Dict[str, Callable[[AsyncOperation], None]] = {}
        
        self.logger.info(f"AsyncOperationManager initialized with {max_workers} workers")
    
    def start(self) -> None:
        """Start worker threads"""
        if self.workers:
            return  # Already started
        
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f'AsyncWorker-{i}',
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"Started {len(self.workers)} async worker threads")
    
    def stop(self) -> None:
        """Stop all worker threads"""
        self._shutdown_event.set()
        
        # Cancel all pending operations
        with self._operations_lock:
            for operation in self.operations.values():
                if operation.status == OperationStatus.PENDING:
                    operation.status = OperationStatus.CANCELLED
        
        # Wait for workers to finish
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5.0)
        
        self.workers.clear()
        self.logger.info("Async operation manager stopped")
    
    def submit_operation(self, operation_type: OperationType, task_func: Callable,
                        *args, progress_callback: Optional[Callable] = None,
                        metadata: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """Submit an async operation
        
        Args:
            operation_type: Type of operation
            task_func: Function to execute in worker thread
            *args: Arguments for task function
            progress_callback: Optional progress callback
            metadata: Optional operation metadata
            **kwargs: Keyword arguments for task function
            
        Returns:
            Operation ID for tracking
        """
        with self._operations_lock:
            operation_id = f"op_{self._next_operation_id}"
            self._next_operation_id += 1
        
        operation = AsyncOperation(
            id=operation_id,
            operation_type=operation_type,
            metadata=metadata or {}
        )
        
        with self._operations_lock:
            self.operations[operation_id] = operation
        
        if progress_callback:
            self.progress_callbacks[operation_id] = progress_callback
        
        # Queue the work
        work_item = {
            'operation_id': operation_id,
            'task_func': task_func,
            'args': args,
            'kwargs': kwargs
        }
        
        self.operation_queue.put(work_item)
        
        self.logger.debug(f"Submitted operation {operation_id} ({operation_type.name})")
        return operation_id
    
    def get_operation_status(self, operation_id: str) -> Optional[AsyncOperation]:
        """Get current status of an operation
        
        Args:
            operation_id: ID of operation to check
            
        Returns:
            AsyncOperation object or None if not found
        """
        with self._operations_lock:
            return self.operations.get(operation_id)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a pending operation
        
        Args:
            operation_id: ID of operation to cancel
            
        Returns:
            True if operation was cancelled, False if not found or already running
        """
        with self._operations_lock:
            operation = self.operations.get(operation_id)
            if operation and operation.status == OperationStatus.PENDING:
                operation.status = OperationStatus.CANCELLED
                operation.end_time = time.time()
                self.logger.info(f"Cancelled operation {operation_id}")
                return True
        
        return False
    
    def get_active_operations(self) -> Dict[str, AsyncOperation]:
        """Get all active (non-completed) operations
        
        Returns:
            Dictionary of active operations
        """
        with self._operations_lock:
            return {
                op_id: op for op_id, op in self.operations.items()
                if op.status in {OperationStatus.PENDING, OperationStatus.RUNNING}
            }
    
    def cleanup_completed_operations(self, max_age_seconds: float = 300.0) -> None:
        """Clean up old completed operations
        
        Args:
            max_age_seconds: Maximum age for completed operations
        """
        current_time = time.time()
        to_remove = []
        
        with self._operations_lock:
            for op_id, operation in self.operations.items():
                if (operation.status in {OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED} and
                    operation.end_time and (current_time - operation.end_time) > max_age_seconds):
                    to_remove.append(op_id)
            
            for op_id in to_remove:
                del self.operations[op_id]
                if op_id in self.progress_callbacks:
                    del self.progress_callbacks[op_id]
        
        if to_remove:
            self.logger.debug(f"Cleaned up {len(to_remove)} completed operations")
    
    def _worker_loop(self) -> None:
        """Main worker thread loop"""
        worker_name = threading.current_thread().name
        self.logger.debug(f"Worker {worker_name} started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get work item with timeout
                try:
                    work_item = self.operation_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                operation_id = work_item['operation_id']
                
                # Check if operation was cancelled
                with self._operations_lock:
                    operation = self.operations.get(operation_id)
                    if not operation or operation.status == OperationStatus.CANCELLED:
                        self.operation_queue.task_done()
                        continue
                    
                    # Mark as running
                    operation.status = OperationStatus.RUNNING
                
                self.logger.debug(f"Worker {worker_name} executing operation {operation_id}")
                
                try:
                    # Create progress callback for this operation
                    def progress_callback(progress: float, message: str = ""):
                        self._update_operation_progress(operation_id, progress, message)
                    
                    # Execute the task
                    task_func = work_item['task_func']
                    args = work_item['args']
                    kwargs = work_item['kwargs']
                    
                    # Add progress callback to kwargs if the function expects it
                    if 'progress_callback' in task_func.__code__.co_varnames:
                        kwargs['progress_callback'] = progress_callback
                    
                    result = task_func(*args, **kwargs)
                    
                    # Mark as completed
                    with self._operations_lock:
                        operation = self.operations.get(operation_id)
                        if operation:
                            operation.status = OperationStatus.COMPLETED
                            operation.result = result
                            operation.progress = 1.0
                            operation.end_time = time.time()
                    
                    self.logger.debug(f"Operation {operation_id} completed successfully")
                    
                except Exception as e:
                    # Mark as failed
                    with self._operations_lock:
                        operation = self.operations.get(operation_id)
                        if operation:
                            operation.status = OperationStatus.FAILED
                            operation.error = e
                            operation.end_time = time.time()
                    
                    self.logger.error(f"Operation {operation_id} failed: {e}", exc_info=True)
                
                # Notify progress callback if registered
                if operation_id in self.progress_callbacks:
                    try:
                        with self._operations_lock:
                            operation = self.operations.get(operation_id)
                            if operation:
                                self.progress_callbacks[operation_id](operation)
                    except Exception as e:
                        self.logger.error(f"Progress callback error for {operation_id}: {e}")
                
                self.operation_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Worker {worker_name} error: {e}", exc_info=True)
        
        self.logger.debug(f"Worker {worker_name} stopped")
    
    def _update_operation_progress(self, operation_id: str, progress: float, message: str = "") -> None:
        """Update operation progress
        
        Args:
            operation_id: ID of operation
            progress: Progress value (0.0 to 1.0)
            message: Optional progress message
        """
        with self._operations_lock:
            operation = self.operations.get(operation_id)
            if operation:
                operation.progress = max(0.0, min(1.0, progress))
                if message:
                    operation.metadata['progress_message'] = message
        
        # Notify progress callback if registered
        if operation_id in self.progress_callbacks:
            try:
                with self._operations_lock:
                    operation = self.operations.get(operation_id)
                    if operation:
                        self.progress_callbacks[operation_id](operation)
            except Exception as e:
                self.logger.error(f"Progress callback error for {operation_id}: {e}")


# Global async operation manager instance
_async_manager = None

def get_async_manager() -> AsyncOperationManager:
    """Get global async operation manager instance"""
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncOperationManager()
        _async_manager.start()
    return _async_manager

def shutdown_async_manager() -> None:
    """Shutdown global async operation manager"""
    global _async_manager
    if _async_manager:
        _async_manager.stop()
        _async_manager = None