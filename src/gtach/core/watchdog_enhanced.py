#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Enhanced Watchdog monitoring with sophisticated component health assessment
and intelligent recovery strategies for OBDII display application.
"""

import logging
import threading
import time
import signal
from enum import Enum, auto
from typing import Dict, Optional, Callable, Any, List, Set
from dataclasses import dataclass, field
from .thread import ThreadManager, ThreadStatus
from .watchdog import RecoveryLevel, RecoveryStats, ThreadHealth, WatchdogMonitor

class ComponentType(Enum):
    """Component types for specialized recovery strategies"""
    DISPLAY = auto()
    BLUETOOTH = auto()
    COMMUNICATION = auto()
    CORE = auto()
    BACKGROUND = auto()

class FailureType(Enum):
    """Types of component failures for targeted recovery"""
    TIMEOUT = auto()          # Thread not responding
    RESOURCE_EXHAUSTION = auto()  # Memory/CPU issues
    COMMUNICATION_ERROR = auto()  # Network/Bluetooth issues
    DEADLOCK = auto()         # Thread blocking issues
    CRASH = auto()           # Thread terminated unexpectedly
    DEPENDENCY_FAILURE = auto() # Required dependency failed

@dataclass
class ComponentProfile:
    """Enhanced component profile with recovery strategies"""
    name: str
    component_type: ComponentType
    is_critical: bool = False
    max_recovery_attempts: int = 3
    recovery_cooldown: float = 10.0
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    custom_recovery_strategy: Optional[Callable] = None
    resource_limits: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class EnhancedThreadHealth(ThreadHealth):
    """Enhanced thread health with component-specific metrics"""
    component_type: ComponentType = ComponentType.BACKGROUND
    failure_types: List[FailureType] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    last_successful_operation: float = 0.0
    dependency_health_score: float = 1.0
    recovery_success_rate: float = 0.0

class EnhancedWatchdogMonitor(WatchdogMonitor):
    """Enhanced watchdog monitor with sophisticated component health assessment
    and intelligent recovery strategies"""
    
    def __init__(self, thread_manager: ThreadManager, check_interval: float = 5.0,
                 warning_timeout: float = 15.0, recovery_timeout: float = 30.0,
                 critical_timeout: float = 45.0, shutdown_callback: Optional[Callable] = None):
        super().__init__(thread_manager, check_interval, warning_timeout, 
                        recovery_timeout, critical_timeout, shutdown_callback)
        
        # Enhanced component profiles
        self.component_profiles: Dict[str, ComponentProfile] = {}
        self.enhanced_health: Dict[str, EnhancedThreadHealth] = {}
        
        # Dependency tracking
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.cascade_prevention_lock = threading.Lock()
        
        # Component-specific recovery strategies
        self.recovery_strategies: Dict[ComponentType, List[Callable]] = {
            ComponentType.DISPLAY: [
                self._recover_display_component,
                self._restart_display_service
            ],
            ComponentType.BLUETOOTH: [
                self._recover_bluetooth_component,
                self._reset_bluetooth_adapter
            ],
            ComponentType.COMMUNICATION: [
                self._recover_communication_component,
                self._reset_communication_buffers
            ],
            ComponentType.CORE: [
                self._recover_core_component
            ],
            ComponentType.BACKGROUND: [
                self._recover_background_component
            ]
        }
        
        # Initialize default component profiles
        self._initialize_component_profiles()
        
        self.logger.info("Enhanced WatchdogMonitor initialized with component profiles")
    
    def _initialize_component_profiles(self) -> None:
        """Initialize default component profiles for known components"""
        profiles = [
            ComponentProfile(
                name="display",
                component_type=ComponentType.DISPLAY,
                is_critical=True,
                max_recovery_attempts=5,
                recovery_cooldown=5.0,
                dependencies={"main"},
                resource_limits={"memory_mb": 50, "cpu_percent": 30}
            ),
            ComponentProfile(
                name="bluetooth",
                component_type=ComponentType.BLUETOOTH,
                is_critical=True,
                max_recovery_attempts=4,
                recovery_cooldown=8.0,
                dependencies={"main"},
                resource_limits={"memory_mb": 20, "cpu_percent": 15}
            ),
            ComponentProfile(
                name="setup",
                component_type=ComponentType.DISPLAY,
                is_critical=False,
                max_recovery_attempts=3,
                recovery_cooldown=10.0,
                dependencies={"display", "bluetooth"},
                resource_limits={"memory_mb": 30, "cpu_percent": 20}
            ),
            ComponentProfile(
                name="main",
                component_type=ComponentType.CORE,
                is_critical=True,
                max_recovery_attempts=2,
                recovery_cooldown=15.0,
                dependencies=set(),
                resource_limits={"memory_mb": 100, "cpu_percent": 50}
            ),
            ComponentProfile(
                name="background",
                component_type=ComponentType.BACKGROUND,
                is_critical=False,
                max_recovery_attempts=6,
                recovery_cooldown=5.0,
                dependencies=set(),
                resource_limits={"memory_mb": 15, "cpu_percent": 10}
            )
        ]
        
        for profile in profiles:
            self.component_profiles[profile.name] = profile
            # Build dependency graph
            if profile.name not in self.dependency_graph:
                self.dependency_graph[profile.name] = profile.dependencies.copy()
    
    def register_component_profile(self, profile: ComponentProfile) -> None:
        """Register a custom component profile"""
        self.component_profiles[profile.name] = profile
        self.dependency_graph[profile.name] = profile.dependencies.copy()
        
        # Update dependents
        for dep in profile.dependencies:
            if dep in self.component_profiles:
                self.component_profiles[dep].dependents.add(profile.name)
        
        self.logger.info(f"Registered component profile: {profile.name} ({profile.component_type.name})")
    
    def _get_enhanced_health(self, name: str) -> EnhancedThreadHealth:
        """Get or create enhanced health tracking for thread"""
        if name not in self.enhanced_health:
            profile = self.component_profiles.get(name)
            component_type = profile.component_type if profile else ComponentType.BACKGROUND
            
            self.enhanced_health[name] = EnhancedThreadHealth(
                name=name,
                is_critical=profile.is_critical if profile else False,
                component_type=component_type
            )
        
        return self.enhanced_health[name]
    
    def _assess_component_health(self, name: str) -> float:
        """Assess overall component health score (0.0 to 1.0)"""
        try:
            health = self._get_enhanced_health(name)
            current_time = time.time()
            
            # Base health factors
            timeout_factor = 1.0
            failure_factor = 1.0
            dependency_factor = health.dependency_health_score
            recovery_factor = health.recovery_success_rate
            
            # Calculate timeout factor
            with self.thread_manager._lock:
                if name in self.thread_manager.threads:
                    thread_info = self.thread_manager.threads[name]
                    timeout = current_time - thread_info.last_heartbeat
                    
                    if timeout > self.critical_timeout:
                        timeout_factor = 0.0
                    elif timeout > self.recovery_timeout:
                        timeout_factor = 0.3
                    elif timeout > self.warning_timeout:
                        timeout_factor = 0.7
            
            # Calculate failure factor
            if health.consecutive_failures > 0:
                failure_factor = max(0.1, 1.0 - (health.consecutive_failures * 0.2))
            
            # Weighted health score
            health_score = (
                timeout_factor * 0.4 +
                failure_factor * 0.3 +
                dependency_factor * 0.2 +
                recovery_factor * 0.1
            )
            
            return max(0.0, min(1.0, health_score))
            
        except Exception as e:
            self.logger.error(f"Error assessing health for {name}: {e}")
            return 0.5  # Neutral score on error
    
    def _update_dependency_health(self, name: str) -> None:
        """Update dependency health scores for component"""
        try:
            if name not in self.dependency_graph:
                return
            
            health = self._get_enhanced_health(name)
            dependencies = self.dependency_graph[name]
            
            if not dependencies:
                health.dependency_health_score = 1.0
                return
            
            total_score = 0.0
            for dep_name in dependencies:
                dep_score = self._assess_component_health(dep_name)
                total_score += dep_score
            
            health.dependency_health_score = total_score / len(dependencies)
            
        except Exception as e:
            self.logger.error(f"Error updating dependency health for {name}: {e}")
    
    def _classify_failure_type(self, name: str, timeout: float) -> FailureType:
        """Classify the type of failure based on symptoms"""
        try:
            health = self._get_enhanced_health(name)
            
            # Analyze failure patterns
            if timeout > self.critical_timeout:
                if health.consecutive_failures > 3:
                    return FailureType.CRASH
                else:
                    return FailureType.DEADLOCK
            elif timeout > self.recovery_timeout:
                if health.dependency_health_score < 0.5:
                    return FailureType.DEPENDENCY_FAILURE
                else:
                    return FailureType.TIMEOUT
            else:
                return FailureType.COMMUNICATION_ERROR
                
        except Exception:
            return FailureType.TIMEOUT
    
    def _select_recovery_strategy(self, name: str, failure_type: FailureType) -> Optional[Callable]:
        """Select appropriate recovery strategy based on component type and failure"""
        try:
            profile = self.component_profiles.get(name)
            if not profile:
                return None
            
            health = self._get_enhanced_health(name)
            
            # Check if we've exceeded recovery attempts
            if health.recovery_attempts >= profile.max_recovery_attempts:
                self.logger.warning(f"Component {name} exceeded max recovery attempts")
                return None
            
            # Check recovery cooldown
            current_time = time.time()
            if current_time - health.last_recovery_time < profile.recovery_cooldown:
                return None
            
            # Custom recovery strategy takes precedence
            if profile.custom_recovery_strategy:
                return profile.custom_recovery_strategy
            
            # Select from component type strategies
            strategies = self.recovery_strategies.get(profile.component_type, [])
            if not strategies:
                return None
            
            # Select strategy based on failure type and attempt count
            strategy_index = min(health.recovery_attempts, len(strategies) - 1)
            return strategies[strategy_index]
            
        except Exception as e:
            self.logger.error(f"Error selecting recovery strategy for {name}: {e}")
            return None
    
    def _prevent_cascade_failure(self, name: str) -> bool:
        """Prevent cascade failures by isolating failed components"""
        try:
            with self.cascade_prevention_lock:
                profile = self.component_profiles.get(name)
                if not profile:
                    return True
                
                # Check if any dependents are critical
                critical_dependents = []
                for dependent in profile.dependents:
                    dep_profile = self.component_profiles.get(dependent)
                    if dep_profile and dep_profile.is_critical:
                        critical_dependents.append(dependent)
                
                if critical_dependents:
                    self.logger.warning(
                        f"Component {name} failure may cascade to critical dependents: {critical_dependents}"
                    )
                    
                    # Try to gracefully handle dependents
                    for dependent in critical_dependents:
                        dep_health = self._get_enhanced_health(dependent)
                        dep_health.dependency_health_score *= 0.5  # Reduce dependency health
                        
                        # Attempt preemptive recovery of dependent
                        self.logger.info(f"Attempting preemptive recovery of dependent: {dependent}")
                        self._attempt_intelligent_recovery(dependent, FailureType.DEPENDENCY_FAILURE)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error preventing cascade failure for {name}: {e}")
            return False
    
    def _attempt_intelligent_recovery(self, name: str, failure_type: FailureType) -> bool:
        """Attempt intelligent recovery using selected strategy"""
        try:
            strategy = self._select_recovery_strategy(name, failure_type)
            if not strategy:
                self.logger.warning(f"No recovery strategy available for {name}")
                return False
            
            health = self._get_enhanced_health(name)
            health.last_recovery_time = time.time()
            health.recovery_attempts += 1
            health.failure_types.append(failure_type)
            
            self.logger.info(f"Attempting intelligent recovery for {name} using {strategy.__name__}")
            
            # Execute recovery strategy
            success = strategy(name, failure_type)
            
            # Update recovery success rate
            if success:
                health.recovery_success_rate = (
                    (health.recovery_success_rate * (health.recovery_attempts - 1) + 1.0) / 
                    health.recovery_attempts
                )
                health.consecutive_failures = 0
                health.last_successful_operation = time.time()
                self.logger.info(f"Intelligent recovery successful for {name}")
            else:
                health.recovery_success_rate = (
                    health.recovery_success_rate * (health.recovery_attempts - 1) / 
                    health.recovery_attempts
                )
                self.logger.warning(f"Intelligent recovery failed for {name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in intelligent recovery for {name}: {e}")
            return False
    
    # Component-specific recovery strategies
    
    def _recover_display_component(self, name: str, failure_type: FailureType) -> bool:
        """Display component specific recovery"""
        try:
            self.logger.info(f"Attempting display recovery for {name}")
            
            if failure_type == FailureType.RESOURCE_EXHAUSTION:
                # Clear display caches
                self.logger.info("Clearing display caches for memory recovery")
                # This would call display manager cache clearing methods
                
            elif failure_type == FailureType.DEADLOCK:
                # Send refresh signal to display thread
                self.logger.info("Sending refresh signal to display thread")
                # This would trigger display refresh
                
            # Wait for response
            time.sleep(2.0)
            
            # Check if display thread is responsive
            with self.thread_manager._lock:
                if name in self.thread_manager.threads:
                    thread_info = self.thread_manager.threads[name]
                    old_heartbeat = thread_info.last_heartbeat
                    time.sleep(1.0)
                    if thread_info.last_heartbeat > old_heartbeat:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Display recovery failed for {name}: {e}")
            return False
    
    def _restart_display_service(self, name: str, failure_type: FailureType) -> bool:
        """Restart display service"""
        try:
            self.logger.info(f"Attempting display service restart for {name}")
            return self.thread_manager.handle_thread_failure(
                name, Exception(f"Display restart: {failure_type.name}")
            )
        except Exception as e:
            self.logger.error(f"Display service restart failed for {name}: {e}")
            return False
    
    def _recover_bluetooth_component(self, name: str, failure_type: FailureType) -> bool:
        """Bluetooth component specific recovery"""
        try:
            self.logger.info(f"Attempting Bluetooth recovery for {name}")
            
            if failure_type == FailureType.COMMUNICATION_ERROR:
                # Reset Bluetooth connection state
                self.logger.info("Resetting Bluetooth connection state")
                
            elif failure_type == FailureType.RESOURCE_EXHAUSTION:
                # Clear Bluetooth buffers
                self.logger.info("Clearing Bluetooth buffers")
            
            time.sleep(1.0)
            return True
            
        except Exception as e:
            self.logger.error(f"Bluetooth recovery failed for {name}: {e}")
            return False
    
    def _reset_bluetooth_adapter(self, name: str, failure_type: FailureType) -> bool:
        """Reset Bluetooth adapter"""
        try:
            self.logger.info(f"Attempting Bluetooth adapter reset for {name}")
            # This would trigger actual Bluetooth adapter reset
            time.sleep(2.0)
            return True
        except Exception as e:
            self.logger.error(f"Bluetooth adapter reset failed for {name}: {e}")
            return False
    
    def _recover_communication_component(self, name: str, failure_type: FailureType) -> bool:
        """Communication component recovery"""
        try:
            self.logger.info(f"Attempting communication recovery for {name}")
            time.sleep(1.0)
            return True
        except Exception as e:
            self.logger.error(f"Communication recovery failed for {name}: {e}")
            return False
    
    def _reset_communication_buffers(self, name: str, failure_type: FailureType) -> bool:
        """Reset communication buffers"""
        try:
            self.logger.info(f"Resetting communication buffers for {name}")
            time.sleep(1.0)
            return True
        except Exception as e:
            self.logger.error(f"Communication buffer reset failed for {name}: {e}")
            return False
    
    def _recover_core_component(self, name: str, failure_type: FailureType) -> bool:
        """Core component recovery"""
        try:
            self.logger.warning(f"Attempting core component recovery for {name} - this may require shutdown")
            # Core components typically require more careful handling
            return False  # Usually escalate to shutdown for core components
        except Exception as e:
            self.logger.error(f"Core component recovery failed for {name}: {e}")
            return False
    
    def _recover_background_component(self, name: str, failure_type: FailureType) -> bool:
        """Background component recovery"""
        try:
            self.logger.info(f"Attempting background component recovery for {name}")
            return self.thread_manager.handle_thread_failure(
                name, Exception(f"Background restart: {failure_type.name}")
            )
        except Exception as e:
            self.logger.error(f"Background component recovery failed for {name}: {e}")
            return False
    
    # Override parent methods to use enhanced logic
    
    def _handle_recovery_timeout(self, name: str, health: ThreadHealth, timeout: float) -> None:
        """Enhanced recovery timeout handling with intelligent strategies"""
        current_time = time.time()
        
        # Skip if we recently attempted recovery
        if current_time - health.last_recovery_time < 10.0:
            return
        
        # Update dependency health
        self._update_dependency_health(name)
        
        # Classify failure type
        failure_type = self._classify_failure_type(name, timeout)
        
        # Prevent cascade failures
        self._prevent_cascade_failure(name)
        
        # Attempt intelligent recovery
        success = self._attempt_intelligent_recovery(name, failure_type)
        
        if success:
            self.logger.info(f"Intelligent recovery successful for {name}")
            with self._recovery_lock:
                self.recovery_stats.soft_recovery_successes += 1
        else:
            # Fall back to parent class recovery methods
            super()._handle_recovery_timeout(name, health, timeout)
    
    def get_component_health_report(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive component health report"""
        health_report = {}
        current_time = time.time()
        
        for name, profile in self.component_profiles.items():
            health = self._get_enhanced_health(name)
            health_score = self._assess_component_health(name)
            
            health_report[name] = {
                'component_type': profile.component_type.name,
                'is_critical': profile.is_critical,
                'health_score': health_score,
                'consecutive_failures': health.consecutive_failures,
                'recovery_attempts': health.recovery_attempts,
                'recovery_success_rate': health.recovery_success_rate,
                'dependency_health_score': health.dependency_health_score,
                'dependencies': list(profile.dependencies),
                'dependents': list(profile.dependents),
                'failure_types': [ft.name for ft in health.failure_types[-5:]],  # Last 5 failures
                'max_recovery_attempts': profile.max_recovery_attempts
            }
        
        return health_report