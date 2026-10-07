# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Utility components for OBDII display application."""

from .config import ConfigStore, AppConfig
from .home import gtach_home
from .terminal import TerminalRestorer
from .dependencies import DependencyValidator, validate_dependencies
from .platform import get_platform_type, PlatformType

__all__ = [
    'ConfigStore',
    'AppConfig',
    'gtach_home',
    'TerminalRestorer',
    'DependencyValidator',
    'validate_dependencies',
    'get_platform_type',
    'PlatformType'
]