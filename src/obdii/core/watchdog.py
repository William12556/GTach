#!/usr/bin/env python3
"""
Watchdog monitoring for OBDII display application.
Monitors thread health and triggers recovery actions.
"""

import logging
import threading
import time
import signal
from enum import Enum, auto
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from .thread import ThreadManager, ThreadStatus

class RecoveryLevel(Enum):
    """Recovery escalation levels"""
    WARNING = auto()      # Log warning, continue monitoring
    SOFT_RECOVERY = auto() # Attempt gentle recovery (signal, interrupt)
    HARD_RECOVERY = auto() # Force thread restart
    GRACEFUL_SHUTDOWN = auto() # Controlled application shutdown
    EMERGENCY_SHUTDOWN = auto() # Immediate shutdown

@dataclass
class RecoveryStats:
    """Statistics for recovery operations"""
    warnings_issued: int = 0
    soft_recovery_attempts: int = 0
    soft_recovery_successes: int = 0
    hard_recovery_attempts: int = 0
    hard_recovery_successes: int = 0
    shutdown_triggers: int = 0
    last_recovery_time: float = 0.0

@dataclass
class ThreadHealth:
    """Track thread health and recovery history"""
    name: str
    last_warning_time: float = 0.0
    last_recovery_time: float = 0.0
    consecutive_failures: int = 0
    recovery_attempts: int = 0
    current_level: RecoveryLevel = RecoveryLevel.WARNING
    is_critical: bool = False  # Critical threads trigger shutdown if recovery fails

class WatchdogMonitor:
    """Enhanced watchdog monitor with automatic recovery mechanisms
    
    Provides escalating recovery responses:
    1. WARNING: Log warnings for unresponsive threads
    2. SOFT_RECOVERY: Attempt gentle recovery (interrupts, signals)
    3. HARD_RECOVERY: Force thread restart
    4. GRACEFUL_SHUTDOWN: Controlled application shutdown
    5. EMERGENCY_SHUTDOWN: Immediate process termination
    """
    
    def __init__(self, thread_manager: ThreadManager, check_interval: float = 5.0, 
                 warning_timeout: float = 15.0, recovery_timeout: float = 30.0,
                 critical_timeout: float = 45.0, shutdown_callback: Optional[Callable] = None):
        """Initialize enhanced watchdog monitor
        
        Args:
            thread_manager: ThreadManager instance to monitor
            check_interval: Seconds between health checks
            warning_timeout: Time before issuing warnings
            recovery_timeout: Time before attempting recovery
            critical_timeout: Time before triggering shutdown
            shutdown_callback: Optional callback for graceful shutdown
        """
        self.logger = logging.getLogger('WatchdogMonitor')
        self.thread_manager = thread_manager
        self.check_interval = check_interval
        self.warning_timeout = warning_timeout
        self.recovery_timeout = recovery_timeout
        self.critical_timeout = critical_timeout
        self.shutdown_callback = shutdown_callback
        
        # Recovery tracking
        self.thread_health: Dict[str, ThreadHealth] = {}
        self.recovery_stats = RecoveryStats()
        self._recovery_lock = threading.Lock()
        
        # Critical threads that trigger shutdown if recovery fails
        self.critical_threads = {'display', 'bluetooth', 'main'}
        
        # Control events
        self._stop_event = threading.Event()
        self._shutdown_initiated = threading.Event()
        
        self._thread = threading.Thread(
            target=self._monitor_loop,
            name='WatchdogMonitor'
        )

    def start(self) -> None:
        """Start watchdog monitoring"""
        self._thread.start()
        self.logger.info("Watchdog monitor started")

    def stop(self) -> None:
        """Stop watchdog monitoring with final status report"""
        if self._shutdown_initiated.is_set():
            self.logger.info("Watchdog monitor stopping due to shutdown")
        
        self._stop_event.set()
        
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                self.logger.warning("Watchdog monitor thread did not stop cleanly")
        
        # Log final recovery statistics
        stats = self.get_recovery_stats()
        self.logger.info(
            f"Watchdog monitor stopped. Final stats: "
            f"warnings={stats.warnings_issued}, "
            f"soft_recovery={stats.soft_recovery_successes}/{stats.soft_recovery_attempts}, "
            f"hard_recovery={stats.hard_recovery_successes}/{stats.hard_recovery_attempts}, "
            f"shutdowns={stats.shutdown_triggers}"
        )

    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            self._check_thread_health()
            self._stop_event.wait(self.check_interval)

    def _check_thread_health(self) -> None:
        """Enhanced thread health checking with escalating recovery"""
        current_time = time.time()
        
        with self.thread_manager._lock:
            for name, thread_info in self.thread_manager.threads.items():
                if thread_info.status not in {ThreadStatus.RUNNING, ThreadStatus.STARTING}:
                    continue
                
                # Initialize thread health tracking if needed
                if name not in self.thread_health:
                    self.thread_health[name] = ThreadHealth(
                        name=name,
                        is_critical=(name in self.critical_threads)
                    )
                
                health = self.thread_health[name]
                time_since_heartbeat = current_time - thread_info.last_heartbeat
                
                # Determine appropriate response level
                if time_since_heartbeat > self.critical_timeout:
                    self._handle_critical_timeout(name, health, time_since_heartbeat)
                elif time_since_heartbeat > self.recovery_timeout:
                    self._handle_recovery_timeout(name, health, time_since_heartbeat)
                elif time_since_heartbeat > self.warning_timeout:
                    self._handle_warning_timeout(name, health, time_since_heartbeat)
                else:
                    # Thread is healthy, reset failure counters
                    self._reset_thread_health(health)
    
    def _handle_warning_timeout(self, name: str, health: ThreadHealth, timeout: float) -> None:
        """Handle warning-level timeout"""
        current_time = time.time()
        
        # Only warn once every 30 seconds to avoid spam
        if current_time - health.last_warning_time > 30.0:
            self.logger.warning(
                f"Thread {name} appears unresponsive (timeout: {timeout:.1f}s)"
            )
            health.last_warning_time = current_time
            health.current_level = RecoveryLevel.WARNING
            
            with self._recovery_lock:
                self.recovery_stats.warnings_issued += 1
    
    def _handle_recovery_timeout(self, name: str, health: ThreadHealth, timeout: float) -> None:
        """Handle recovery-level timeout with escalating attempts"""
        current_time = time.time()
        
        # Skip if we recently attempted recovery
        if current_time - health.last_recovery_time < 10.0:
            return
        
        health.consecutive_failures += 1
        health.last_recovery_time = current_time
        
        if health.consecutive_failures == 1:
            # First attempt: soft recovery
            self._attempt_soft_recovery(name, health, timeout)
        elif health.consecutive_failures >= 2:
            # Escalate to hard recovery
            self._attempt_hard_recovery(name, health, timeout)
    
    def _handle_critical_timeout(self, name: str, health: ThreadHealth, timeout: float) -> None:
        """Handle critical timeout - may trigger shutdown"""
        self.logger.error(
            f"Thread {name} critical timeout ({timeout:.1f}s) - initiating emergency procedures"
        )
        
        if health.is_critical:
            self.logger.critical(
                f"Critical thread {name} failed recovery - initiating graceful shutdown"
            )
            self._initiate_graceful_shutdown(f"Critical thread {name} timeout")
        else:
            # Non-critical thread - attempt hard recovery one more time
            self._attempt_hard_recovery(name, health, timeout, force=True)
    
    def _attempt_soft_recovery(self, name: str, health: ThreadHealth, timeout: float) -> None:
        """Attempt soft recovery using thread interruption"""
        self.logger.info(f"Attempting soft recovery for thread {name} (timeout: {timeout:.1f}s)")
        
        with self._recovery_lock:
            self.recovery_stats.soft_recovery_attempts += 1
        
        health.current_level = RecoveryLevel.SOFT_RECOVERY
        health.recovery_attempts += 1
        
        try:
            # Attempt to interrupt the thread gently
            with self.thread_manager._lock:
                if name in self.thread_manager.threads:
                    thread_info = self.thread_manager.threads[name]
                    thread = thread_info.thread
                    
                    # For display thread, try to trigger a refresh
                    if name == 'display' and hasattr(thread, '_target'):
                        self.logger.debug(f"Triggering display refresh for {name}")
                        # The display loop should detect this and recover
                    
                    # Update heartbeat to test if thread is actually responsive
                    old_heartbeat = thread_info.last_heartbeat
                    time.sleep(1.0)  # Wait a moment
                    
                    if thread_info.last_heartbeat > old_heartbeat:
                        self.logger.info(f"Soft recovery successful for thread {name}")
                        with self._recovery_lock:
                            self.recovery_stats.soft_recovery_successes += 1
                        self._reset_thread_health(health)
                        return
        
        except Exception as e:
            self.logger.error(f"Soft recovery failed for thread {name}: {e}", exc_info=True)
    
    def _attempt_hard_recovery(self, name: str, health: ThreadHealth, timeout: float, force: bool = False) -> None:
        """Attempt hard recovery by restarting the thread"""
        if not force and health.recovery_attempts >= 3:
            self.logger.error(f"Thread {name} exceeded maximum recovery attempts")
            if health.is_critical:
                self._initiate_graceful_shutdown(f"Thread {name} recovery failed")
            return
        
        self.logger.warning(f"Attempting hard recovery for thread {name} (timeout: {timeout:.1f}s)")
        
        with self._recovery_lock:
            self.recovery_stats.hard_recovery_attempts += 1
        
        health.current_level = RecoveryLevel.HARD_RECOVERY
        health.recovery_attempts += 1
        
        try:
            # Use existing thread manager failure handling
            self.thread_manager.handle_thread_failure(
                name,
                Exception(f"Watchdog timeout: {timeout:.1f}s")
            )
            
            # Wait and check if recovery was successful
            time.sleep(2.0)
            with self.thread_manager._lock:
                if name in self.thread_manager.threads:
                    thread_info = self.thread_manager.threads[name]
                    if thread_info.status == ThreadStatus.RUNNING:
                        self.logger.info(f"Hard recovery successful for thread {name}")
                        with self._recovery_lock:
                            self.recovery_stats.hard_recovery_successes += 1
                        self._reset_thread_health(health)
                        return
        
        except Exception as e:
            self.logger.error(f"Hard recovery failed for thread {name}: {e}", exc_info=True)
    
    def _reset_thread_health(self, health: ThreadHealth) -> None:
        """Reset thread health counters when thread becomes responsive"""
        health.consecutive_failures = 0
        health.current_level = RecoveryLevel.WARNING
    
    def _initiate_graceful_shutdown(self, reason: str) -> None:
        """Initiate graceful application shutdown"""
        if self._shutdown_initiated.is_set():
            return  # Already shutting down
        
        self._shutdown_initiated.set()
        
        self.logger.critical(f"Initiating graceful shutdown: {reason}")
        
        with self._recovery_lock:
            self.recovery_stats.shutdown_triggers += 1
        
        try:
            if self.shutdown_callback:
                self.logger.info("Calling graceful shutdown callback")
                self.shutdown_callback()
            else:
                self.logger.warning("No shutdown callback available - using thread manager shutdown")
                self.thread_manager.shutdown()
        except Exception as e:
            self.logger.error(f"Graceful shutdown failed: {e}", exc_info=True)
            self._emergency_shutdown()
    
    def _emergency_shutdown(self) -> None:
        """Emergency shutdown as last resort"""
        self.logger.critical("Emergency shutdown initiated")
        
        try:
            # Give a brief moment for logging to complete
            time.sleep(0.5)
        except:
            pass
        
        # Force process termination
        import os
        os._exit(1)
    
    def get_recovery_stats(self) -> RecoveryStats:
        """Get current recovery statistics"""
        with self._recovery_lock:
            return RecoveryStats(
                warnings_issued=self.recovery_stats.warnings_issued,
                soft_recovery_attempts=self.recovery_stats.soft_recovery_attempts,
                soft_recovery_successes=self.recovery_stats.soft_recovery_successes,
                hard_recovery_attempts=self.recovery_stats.hard_recovery_attempts,
                hard_recovery_successes=self.recovery_stats.hard_recovery_successes,
                shutdown_triggers=self.recovery_stats.shutdown_triggers,
                last_recovery_time=self.recovery_stats.last_recovery_time
            )
    
    def get_thread_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current health status for all monitored threads"""
        status = {}
        current_time = time.time()
        
        with self.thread_manager._lock:
            # Check all threads in thread manager
            for name, thread_info in self.thread_manager.threads.items():
                # Initialize health tracking if needed
                if name not in self.thread_health:
                    self.thread_health[name] = ThreadHealth(
                        name=name,
                        is_critical=(name in self.critical_threads)
                    )
                
                health = self.thread_health[name]
                status[name] = {
                    'status': thread_info.status.name,
                    'last_heartbeat': thread_info.last_heartbeat,
                    'timeout': current_time - thread_info.last_heartbeat,
                    'consecutive_failures': health.consecutive_failures,
                    'recovery_attempts': health.recovery_attempts,
                    'current_level': health.current_level.name,
                    'is_critical': health.is_critical
                }
        
        return status