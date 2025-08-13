#!/usr/bin/env python3
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

__all__ = [
    'PackageCreator', 'PackageConfig', 'PackageManifest',
    'ConfigProcessor', 'PlatformConfig', 
    'ArchiveManager', 'ArchiveMetadata', 'ArchiveConfig', 'CompressionFormat'
]
__version__ = '0.1.0-alpha.1'