#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Service Registry for OBDII Foundational Services Architecture

Provides centralized service discovery, coordination, and lifecycle management.
Eliminates ad-hoc integration patterns by providing unified service access.
"""

import logging
import threading
import time
import weakref
from typing import Dict, Optional, Any, Callable, List, Type, TypeVar, Generic
from enum import Enum, auto
from dataclasses import dataclass, field
from contextlib import contextmanager
import inspect


class ServiceState(Enum):
    """Service lifecycle states"""
    UNREGISTERED = auto()
    REGISTERED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()


class ServiceError(Exception):
    """Base exception for service-related errors"""
    pass


class ServiceNotFoundError(ServiceError):
    """Raised when a requested service is not found"""
    pass


class ServiceStateError(ServiceError):
    """Raised when service is in invalid state for operation"""
    pass


T = TypeVar('T')


@dataclass
class ServiceInfo:
    """Information about a registered service"""
    name: str
    service_type: Type
    instance: Optional[Any] = None
    state: ServiceState = ServiceState.UNREGISTERED
    dependencies: List[str] = field(default_factory=list)
    startup_callback: Optional[Callable] = None
    shutdown_callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    registration_time: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    access_count: int = 0


class ServiceRegistry:
    """
    Centralized service registry for OBDII foundational services.
    
    Provides service discovery, dependency injection, lifecycle management,
    and coordination between services. Thread-safe with proper synchronization.
    """
    
    _instance: Optional['ServiceRegistry'] = None
    _instance_lock = threading.Lock()
    
    def __new__(cls) -> 'ServiceRegistry':
        """Singleton pattern with thread-safe initialization"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize service registry"""
        # Prevent multiple initialization
        if hasattr(self, '_initialized'):
            return
        
        self.logger = logging.getLogger('ServiceRegistry')
        
        # Thread-safe service storage
        self._services: Dict[str, ServiceInfo] = {}
        self._services_lock = threading.RLock()
        
        # Service type mapping for lookup
        self._type_map: Dict[Type, str] = {}
        
        # Dependency graph for startup ordering
        self._dependency_graph: Dict[str, List[str]] = {}
        
        # Service lifecycle callbacks
        self._global_callbacks: Dict[ServiceState, List[Callable]] = {state: [] for state in ServiceState}
        
        # Performance monitoring
        self._operation_count = 0
        self._performance_lock = threading.Lock()
        
        # Weak references to avoid circular dependencies
        self._weak_refs: weakref.WeakSet = weakref.WeakSet()
        
        self._initialized = True
        self.logger.debug("ServiceRegistry initialized")
    
    @contextmanager
    def _performance_timing(self, operation: str):
        """Context manager for performance monitoring"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            with self._performance_lock:
                self._operation_count += 1
                if elapsed > 0.1:  # Log slow operations
                    self.logger.warning(f"Slow service operation {operation}: {elapsed:.3f}s")
    
    def register_service(self, 
                        name: str, 
                        service_type: Type[T], 
                        instance: Optional[T] = None,
                        dependencies: Optional[List[str]] = None,
                        startup_callback: Optional[Callable] = None,
                        shutdown_callback: Optional[Callable] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a service with the registry.
        
        Args:
            name: Unique service name
            service_type: Service class type
            instance: Optional pre-created instance
            dependencies: List of service names this service depends on
            startup_callback: Optional callback to execute on service startup
            shutdown_callback: Optional callback to execute on service shutdown
            metadata: Optional metadata about the service
        """
        with self._performance_timing(f"register_service({name})"):
            with self._services_lock:
                if name in self._services:
                    raise ServiceError(f"Service '{name}' already registered")
                
                # Validate service type
                if not inspect.isclass(service_type):
                    raise ServiceError(f"Service type must be a class, got {type(service_type)}")
                
                # Create service info
                service_info = ServiceInfo(
                    name=name,
                    service_type=service_type,
                    instance=instance,
                    state=ServiceState.REGISTERED if instance else ServiceState.UNREGISTERED,
                    dependencies=dependencies or [],
                    startup_callback=startup_callback,
                    shutdown_callback=shutdown_callback,
                    metadata=metadata or {}
                )
                
                # Store service info
                self._services[name] = service_info
                self._type_map[service_type] = name
                
                # Update dependency graph
                self._dependency_graph[name] = service_info.dependencies.copy()
                
                # Add to weak reference tracking if instance provided
                if instance:
                    self._weak_refs.add(instance)
                
                self.logger.info(f"Registered service '{name}' of type {service_type.__name__}")
                
                # Notify global callbacks
                self._notify_state_change(name, service_info.state)
    
    def get_service(self, name: str) -> Any:
        """
        Get a service instance by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service not found
            ServiceStateError: If service not ready
        """
        with self._performance_timing(f"get_service({name})"):
            with self._services_lock:
                if name not in self._services:
                    raise ServiceNotFoundError(f"Service '{name}' not found")
                
                service_info = self._services[name]
                
                # Update access statistics
                service_info.last_access_time = time.time()
                service_info.access_count += 1
                
                # Check if service needs to be started
                if service_info.state == ServiceState.REGISTERED and service_info.instance is None:
                    self._start_service(service_info)
                
                if service_info.instance is None:
                    raise ServiceStateError(f"Service '{name}' not ready (state: {service_info.state.name})")
                
                return service_info.instance
    
    def get_service_by_type(self, service_type: Type[T]) -> T:
        """
        Get a service instance by type.
        
        Args:
            service_type: Service class type
            
        Returns:
            Service instance
        """
        with self._services_lock:
            name = self._type_map.get(service_type)
            if name is None:
                raise ServiceNotFoundError(f"No service registered for type {service_type.__name__}")
            
            return self.get_service(name)  # type: ignore
    
    def has_service(self, name: str) -> bool:
        """Check if a service is registered"""
        with self._services_lock:
            return name in self._services
    
    def has_service_type(self, service_type: Type) -> bool:
        """Check if a service type is registered"""
        with self._services_lock:
            return service_type in self._type_map
    
    def _start_service(self, service_info: ServiceInfo) -> None:
        """
        Start a service instance.
        
        Args:
            service_info: Service information
        """
        try:
            self.logger.debug(f"Starting service '{service_info.name}'")
            service_info.state = ServiceState.STARTING
            
            # Check dependencies
            self._ensure_dependencies(service_info)
            
            # Create instance if not provided
            if service_info.instance is None:
                service_info.instance = service_info.service_type()
                self._weak_refs.add(service_info.instance)
            
            # Execute startup callback
            if service_info.startup_callback:
                service_info.startup_callback(service_info.instance)
            
            service_info.state = ServiceState.RUNNING
            self.logger.info(f"Started service '{service_info.name}'")
            
            # Notify state change
            self._notify_state_change(service_info.name, ServiceState.RUNNING)
            
        except Exception as e:
            service_info.state = ServiceState.FAILED
            self.logger.error(f"Failed to start service '{service_info.name}': {e}")
            self._notify_state_change(service_info.name, ServiceState.FAILED)
            raise ServiceError(f"Failed to start service '{service_info.name}': {e}") from e
    
    def _ensure_dependencies(self, service_info: ServiceInfo) -> None:
        """
        Ensure all dependencies are available and started.
        
        Args:
            service_info: Service information
        """
        for dep_name in service_info.dependencies:
            if dep_name not in self._services:
                raise ServiceError(f"Dependency '{dep_name}' not registered for service '{service_info.name}'")
            
            dep_info = self._services[dep_name]
            
            # Start dependency if needed
            if dep_info.state == ServiceState.REGISTERED and dep_info.instance is None:
                self._start_service(dep_info)
            
            # Check dependency state
            if dep_info.state not in [ServiceState.RUNNING]:
                raise ServiceError(f"Dependency '{dep_name}' not ready for service '{service_info.name}'")
    
    def stop_service(self, name: str) -> None:
        """
        Stop a service.
        
        Args:
            name: Service name
        """
        with self._performance_timing(f"stop_service({name})"):
            with self._services_lock:
                if name not in self._services:
                    raise ServiceNotFoundError(f"Service '{name}' not found")
                
                service_info = self._services[name]
                
                if service_info.state not in [ServiceState.RUNNING, ServiceState.FAILED]:
                    self.logger.debug(f"Service '{name}' already stopped or not running")
                    return
                
                try:
                    self.logger.debug(f"Stopping service '{name}'")
                    service_info.state = ServiceState.STOPPING
                    
                    # Execute shutdown callback
                    if service_info.shutdown_callback and service_info.instance:
                        service_info.shutdown_callback(service_info.instance)
                    
                    service_info.state = ServiceState.STOPPED
                    self.logger.info(f"Stopped service '{name}'")
                    
                    # Notify state change
                    self._notify_state_change(name, ServiceState.STOPPED)
                    
                except Exception as e:
                    service_info.state = ServiceState.FAILED
                    self.logger.error(f"Error stopping service '{name}': {e}")
                    self._notify_state_change(name, ServiceState.FAILED)
                    raise ServiceError(f"Failed to stop service '{name}': {e}") from e
    
    def unregister_service(self, name: str) -> None:
        """
        Unregister a service.
        
        Args:
            name: Service name
        """
        with self._performance_timing(f"unregister_service({name})"):
            with self._services_lock:
                if name not in self._services:
                    raise ServiceNotFoundError(f"Service '{name}' not found")
                
                service_info = self._services[name]
                
                # Stop service if running
                if service_info.state in [ServiceState.RUNNING, ServiceState.FAILED]:
                    self.stop_service(name)
                
                # Remove from registry
                del self._services[name]
                del self._type_map[service_info.service_type]
                del self._dependency_graph[name]
                
                self.logger.info(f"Unregistered service '{name}'")
    
    def list_services(self) -> List[str]:
        """Get list of registered service names"""
        with self._services_lock:
            return list(self._services.keys())
    
    def get_service_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a service.
        
        Args:
            name: Service name
            
        Returns:
            Service information dictionary
        """
        with self._services_lock:
            if name not in self._services:
                raise ServiceNotFoundError(f"Service '{name}' not found")
            
            service_info = self._services[name]
            
            return {
                'name': service_info.name,
                'type': service_info.service_type.__name__,
                'state': service_info.state.name,
                'dependencies': service_info.dependencies.copy(),
                'metadata': service_info.metadata.copy(),
                'registration_time': service_info.registration_time,
                'last_access_time': service_info.last_access_time,
                'access_count': service_info.access_count,
                'has_instance': service_info.instance is not None
            }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        with self._services_lock:
            state_counts = {}
            total_access_count = 0
            
            for service_info in self._services.values():
                state_name = service_info.state.name
                state_counts[state_name] = state_counts.get(state_name, 0) + 1
                total_access_count += service_info.access_count
            
            with self._performance_lock:
                return {
                    'total_services': len(self._services),
                    'state_counts': state_counts,
                    'total_access_count': total_access_count,
                    'operation_count': self._operation_count,
                    'weak_refs_count': len(self._weak_refs)
                }
    
    def add_state_callback(self, state: ServiceState, callback: Callable[[str, ServiceState], None]) -> None:
        """
        Add a global state change callback.
        
        Args:
            state: Service state to listen for
            callback: Callback function (service_name, new_state)
        """
        with self._services_lock:
            self._global_callbacks[state].append(callback)
            self.logger.debug(f"Added state callback for {state.name}")
    
    def _notify_state_change(self, service_name: str, new_state: ServiceState) -> None:
        """
        Notify callbacks of service state changes.
        
        Args:
            service_name: Name of service that changed state
            new_state: New service state
        """
        callbacks = self._global_callbacks.get(new_state, [])
        for callback in callbacks:
            try:
                callback(service_name, new_state)
            except Exception as e:
                self.logger.error(f"Error in state callback for {service_name}: {e}")
    
    def start_all_services(self) -> Dict[str, bool]:
        """
        Start all registered services in dependency order.
        
        Returns:
            Dictionary of service_name -> success_status
        """
        with self._performance_timing("start_all_services"):
            results = {}
            
            # Get services in dependency order
            ordered_services = self._get_dependency_order()
            
            for service_name in ordered_services:
                try:
                    service_info = self._services[service_name]
                    if service_info.state == ServiceState.REGISTERED and service_info.instance is None:
                        self._start_service(service_info)
                    results[service_name] = True
                except Exception as e:
                    self.logger.error(f"Failed to start service '{service_name}': {e}")
                    results[service_name] = False
            
            return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """
        Stop all running services in reverse dependency order.
        
        Returns:
            Dictionary of service_name -> success_status
        """
        with self._performance_timing("stop_all_services"):
            results = {}
            
            # Get services in reverse dependency order
            ordered_services = self._get_dependency_order()
            ordered_services.reverse()
            
            for service_name in ordered_services:
                try:
                    self.stop_service(service_name)
                    results[service_name] = True
                except Exception as e:
                    self.logger.error(f"Failed to stop service '{service_name}': {e}")
                    results[service_name] = False
            
            return results
    
    def _get_dependency_order(self) -> List[str]:
        """
        Get services in dependency order using topological sort.
        
        Returns:
            List of service names in dependency order
        """
        # Simple topological sort implementation
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ServiceError(f"Circular dependency detected involving service '{service_name}'")
            
            if service_name not in visited:
                temp_visited.add(service_name)
                
                # Visit dependencies first
                for dep_name in self._dependency_graph.get(service_name, []):
                    visit(dep_name)
                
                temp_visited.remove(service_name)
                visited.add(service_name)
                result.append(service_name)
        
        # Visit all services
        for service_name in self._services.keys():
            if service_name not in visited:
                visit(service_name)
        
        return result
    
    def clear_registry(self) -> None:
        """Clear all registered services (for testing)"""
        with self._services_lock:
            # Stop all services first
            self.stop_all_services()
            
            # Clear all data structures
            self._services.clear()
            self._type_map.clear()
            self._dependency_graph.clear()
            self._weak_refs.clear()
            
            # Reset performance counters
            with self._performance_lock:
                self._operation_count = 0
            
            self.logger.debug("Service registry cleared")
    
    @classmethod
    def get_instance(cls) -> 'ServiceRegistry':
        """Get the singleton registry instance"""
        return cls()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)"""
        with cls._instance_lock:
            if cls._instance:
                cls._instance.clear_registry()
            cls._instance = None


# Global registry instance accessor
def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance"""
    return ServiceRegistry.get_instance()


# Convenience functions for common operations
def register_service(name: str, 
                    service_type: Type[T], 
                    instance: Optional[T] = None,
                    dependencies: Optional[List[str]] = None,
                    **kwargs) -> None:
    """Register a service with the global registry"""
    registry = get_service_registry()
    registry.register_service(name, service_type, instance, dependencies, **kwargs)


def get_service(name: str) -> Any:
    """Get a service from the global registry"""
    registry = get_service_registry()
    return registry.get_service(name)


def get_service_by_type(service_type: Type[T]) -> T:
    """Get a service by type from the global registry"""
    registry = get_service_registry()
    return registry.get_service_by_type(service_type)