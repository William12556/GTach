#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
OBDII Foundational Services Architecture

Provides unified foundational services for cross-cutting concerns:
- ServiceRegistry: Service discovery and coordination
- ConfigurationService: Atomic configuration operations
- PlatformService: Hardware abstraction interfaces
- DependencyService: Runtime capability assessment

Eliminates ad-hoc integration patterns across subsystems.
"""

from .registry import ServiceRegistry, ServiceError, ServiceState
from .configuration import ConfigurationService, ConfigurationError
from .platform import PlatformService, PlatformCapabilities
from .dependency import DependencyService, CapabilityResult

__all__ = [
    'ServiceRegistry',
    'ServiceError', 
    'ServiceState',
    'ConfigurationService',
    'ConfigurationError',
    'PlatformService',
    'PlatformCapabilities',
    'DependencyService',
    'CapabilityResult'
]

# Version information
__version__ = '1.0.0'
__author__ = 'OBDII Development Team'