#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
GTach Application Provisioning System

This module provides functionality for creating standardized deployment packages
containing application source code, configuration templates, and installation scripts.

Protocol compliance:
- Protocol 001: Project structure standards
- Protocol 006: Cross-platform development standards  
- Protocol 008: Logging and debug standards

Components:
- PackageCreator: Main class for creating deployment packages
- ConfigProcessor: Processes configuration templates for target platforms
- Archive management: Handles tar.gz creation and validation
"""

from .package_creator import PackageCreator, PackageConfig, PackageManifest
from .config_processor import ConfigProcessor, PlatformConfig
from .archive_manager import ArchiveManager, ArchiveMetadata, ArchiveConfig, CompressionFormat
from .version_state_manager import VersionStateManager, VersionState, DevelopmentStage, IncrementHistory

__all__ = [
    'PackageCreator', 'PackageConfig', 'PackageManifest',
    'ConfigProcessor', 'PlatformConfig', 
    'ArchiveManager', 'ArchiveMetadata', 'ArchiveConfig', 'CompressionFormat',
    'VersionStateManager', 'VersionState', 'DevelopmentStage', 'IncrementHistory'
]
__version__ = '0.1.0-alpha.1'