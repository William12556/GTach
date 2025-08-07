#!/usr/bin/env python3
"""
Version Manager for GTach Application Provisioning System

Provides comprehensive semantic versioning (SemVer) support for package management,
dependency resolution, and compatibility checking. Implements thread-safe operations
with Protocol 8 compliant logging.

Features:
- SemVer 2.0.0 compliant version parsing and validation
- Comprehensive version comparison operators
- Dependency resolution and compatibility checking
- Thread-safe version operations
- Range and constraint validation
- Pre-release and build metadata support
"""

import re
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import total_ordering


class VersionType(Enum):
    """Version type classification"""
    STABLE = auto()
    PRE_RELEASE = auto()
    BUILD = auto()


class CompatibilityLevel(Enum):
    """Compatibility level between versions"""
    COMPATIBLE = auto()
    MINOR_BREAKING = auto()
    MAJOR_BREAKING = auto()
    INCOMPATIBLE = auto()


@dataclass
class VersionConstraint:
    """Version constraint specification"""
    operator: str  # >=, <=, ==, !=, ~, ^
    version: 'Version'
    
    def matches(self, version: 'Version') -> bool:
        """Check if version matches this constraint"""
        if self.operator == ">=":
            return version >= self.version
        elif self.operator == "<=":
            return version <= self.version
        elif self.operator == "==":
            return version == self.version
        elif self.operator == "!=":
            return version != self.version
        elif self.operator == "~":
            # Compatible within patch level
            return (version.major == self.version.major and
                   version.minor == self.version.minor and
                   version >= self.version)
        elif self.operator == "^":
            # Compatible within minor level
            return (version.major == self.version.major and
                   version >= self.version)
        else:
            raise ValueError(f"Unsupported constraint operator: {self.operator}")


@total_ordering
class Version:
    """
    Semantic version implementation compliant with SemVer 2.0.0.
    
    Supports version parsing, comparison, and validation with comprehensive
    pre-release and build metadata handling.
    """
    
    # SemVer regex pattern - based on official SemVer spec
    SEMVER_PATTERN = re.compile(
        r'^(?P<major>0|[1-9]\d*)'
        r'\.(?P<minor>0|[1-9]\d*)'
        r'\.(?P<patch>0|[1-9]\d*)'
        r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
        r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    )
    
    def __init__(self, version_string: str):
        """
        Initialize Version from version string.
        
        Args:
            version_string: SemVer compliant version string
            
        Raises:
            ValueError: If version string is invalid
        """
        self.raw = version_string.strip()
        self._parse_version()
        
    def _parse_version(self) -> None:
        """Parse version string according to SemVer specification"""
        match = self.SEMVER_PATTERN.match(self.raw)
        if not match:
            raise ValueError(f"Invalid semantic version: {self.raw}")
        
        # Extract core version components
        self.major = int(match.group('major'))
        self.minor = int(match.group('minor'))
        self.patch = int(match.group('patch'))
        
        # Extract pre-release and build metadata
        self.prerelease = match.group('prerelease') or ""
        self.build_metadata = match.group('buildmetadata') or ""
        
        # Determine version type
        if self.prerelease:
            self.version_type = VersionType.PRE_RELEASE
        elif self.build_metadata and not self.prerelease:
            self.version_type = VersionType.BUILD
        else:
            self.version_type = VersionType.STABLE
            
        # Parse pre-release components for comparison
        self.prerelease_parts = []
        if self.prerelease:
            for part in self.prerelease.split('.'):
                # Try to convert to int, keep as string if not numeric
                try:
                    self.prerelease_parts.append(int(part))
                except ValueError:
                    self.prerelease_parts.append(part)
    
    def __str__(self) -> str:
        """Return string representation"""
        return self.raw
    
    def __repr__(self) -> str:
        """Return detailed representation"""
        return f"Version('{self.raw}')"
    
    def __eq__(self, other) -> bool:
        """Version equality comparison (ignores build metadata per SemVer)"""
        if not isinstance(other, Version):
            return False
        return (self.major == other.major and
                self.minor == other.minor and
                self.patch == other.patch and
                self.prerelease == other.prerelease)
    
    def __lt__(self, other) -> bool:
        """Version less-than comparison per SemVer precedence rules"""
        if not isinstance(other, Version):
            return NotImplemented
            
        # Compare major.minor.patch
        core_tuple = (self.major, self.minor, self.patch)
        other_core_tuple = (other.major, other.minor, other.patch)
        
        if core_tuple != other_core_tuple:
            return core_tuple < other_core_tuple
        
        # Pre-release versions have lower precedence than normal versions
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and not other.prerelease:
            return False
            
        # Both have pre-release - compare pre-release parts
        return self._compare_prerelease_parts(other) < 0
    
    def _compare_prerelease_parts(self, other: 'Version') -> int:
        """
        Compare pre-release parts according to SemVer rules.
        
        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        # Compare each pre-release part
        for i in range(max(len(self.prerelease_parts), len(other.prerelease_parts))):
            # Missing parts are considered lower precedence
            if i >= len(self.prerelease_parts):
                return -1
            if i >= len(other.prerelease_parts):
                return 1
                
            self_part = self.prerelease_parts[i]
            other_part = other.prerelease_parts[i]
            
            # Numeric parts are compared numerically
            if isinstance(self_part, int) and isinstance(other_part, int):
                if self_part != other_part:
                    return -1 if self_part < other_part else 1
            # Numeric parts have lower precedence than non-numeric
            elif isinstance(self_part, int):
                return -1
            elif isinstance(other_part, int):
                return 1
            # String parts compared lexically
            else:
                if self_part != other_part:
                    return -1 if self_part < other_part else 1
        
        return 0
    
    def __hash__(self) -> int:
        """Hash based on core version components"""
        return hash((self.major, self.minor, self.patch, self.prerelease))
    
    @property
    def is_stable(self) -> bool:
        """Check if this is a stable release"""
        return self.version_type in [VersionType.STABLE, VersionType.BUILD]
    
    @property
    def is_prerelease(self) -> bool:
        """Check if this is a pre-release version"""
        return self.version_type == VersionType.PRE_RELEASE
    
    def bump_major(self) -> 'Version':
        """Return new version with bumped major version"""
        return Version(f"{self.major + 1}.0.0")
    
    def bump_minor(self) -> 'Version':
        """Return new version with bumped minor version"""
        return Version(f"{self.major}.{self.minor + 1}.0")
    
    def bump_patch(self) -> 'Version':
        """Return new version with bumped patch version"""
        return Version(f"{self.major}.{self.minor}.{self.patch + 1}")
    
    def get_compatibility_level(self, other: 'Version') -> CompatibilityLevel:
        """
        Get compatibility level with another version.
        
        Args:
            other: Version to compare against
            
        Returns:
            Compatibility level
        """
        if self.major != other.major:
            return CompatibilityLevel.MAJOR_BREAKING
        elif self.minor != other.minor:
            return CompatibilityLevel.MINOR_BREAKING
        elif self.patch != other.patch:
            return CompatibilityLevel.COMPATIBLE
        elif self.prerelease != other.prerelease:
            return CompatibilityLevel.COMPATIBLE
        else:
            return CompatibilityLevel.COMPATIBLE


class VersionManager:
    """
    Thread-safe version management system for package versioning and dependency resolution.
    
    Provides comprehensive version handling, compatibility checking, and dependency
    resolution with Protocol 8 compliant logging and error handling.
    """
    
    def __init__(self):
        """Initialize VersionManager with thread-safe operations"""
        self.logger = logging.getLogger(f'{__name__}.VersionManager')
        
        # Thread safety
        self._operations_lock = threading.RLock()
        self._operation_count = 0
        self._stats_lock = threading.Lock()
        
        # Version cache for performance
        self._version_cache: Dict[str, Version] = {}
        self._cache_lock = threading.Lock()
        
        # Dependency resolution cache
        self._dependency_cache: Dict[str, List[Version]] = {}
        
        self.logger.info("VersionManager initialized")
    
    def parse_version(self, version_string: str) -> Version:
        """
        Parse version string with caching.
        
        Args:
            version_string: Version string to parse
            
        Returns:
            Parsed Version object
            
        Raises:
            ValueError: If version string is invalid
        """
        with self._cache_lock:
            if version_string not in self._version_cache:
                try:
                    self._version_cache[version_string] = Version(version_string)
                    self.logger.debug(f"Parsed version: {version_string}")
                except ValueError as e:
                    self.logger.error(f"Invalid version string '{version_string}': {e}")
                    raise
            
            return self._version_cache[version_string]
    
    def parse_constraint(self, constraint_string: str) -> VersionConstraint:
        """
        Parse version constraint string.
        
        Args:
            constraint_string: Constraint string (e.g., ">=1.0.0", "~2.1.0")
            
        Returns:
            Parsed VersionConstraint
            
        Raises:
            ValueError: If constraint string is invalid
        """
        constraint_string = constraint_string.strip()
        
        # Define constraint operators (order matters - longer first)
        operators = [">=", "<=", "==", "!=", "~", "^"]
        
        operator = None
        version_part = None
        
        for op in operators:
            if constraint_string.startswith(op):
                operator = op
                version_part = constraint_string[len(op):].strip()
                break
        
        if operator is None:
            # Default to exact match
            operator = "=="
            version_part = constraint_string
        
        if not version_part:
            raise ValueError(f"Invalid constraint string: {constraint_string}")
        
        version = self.parse_version(version_part)
        return VersionConstraint(operator, version)
    
    def check_compatibility(self, version1: Union[str, Version], 
                          version2: Union[str, Version]) -> CompatibilityLevel:
        """
        Check compatibility between two versions.
        
        Args:
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Compatibility level
        """
        with self._operations_lock:
            self._increment_operation_count()
            
            if isinstance(version1, str):
                version1 = self.parse_version(version1)
            if isinstance(version2, str):
                version2 = self.parse_version(version2)
            
            compatibility = version1.get_compatibility_level(version2)
            
            self.logger.debug(f"Compatibility check: {version1} -> {version2} = {compatibility.name}")
            return compatibility
    
    def find_compatible_versions(self, target_version: Union[str, Version],
                                available_versions: List[Union[str, Version]],
                                constraint: Optional[str] = None) -> List[Version]:
        """
        Find versions compatible with target version from available list.
        
        Args:
            target_version: Target version to match against
            available_versions: List of available versions
            constraint: Optional version constraint (e.g., "^1.0.0")
            
        Returns:
            List of compatible versions sorted by precedence
        """
        with self._operations_lock:
            self._increment_operation_count()
            
            if isinstance(target_version, str):
                target_version = self.parse_version(target_version)
            
            compatible_versions = []
            constraint_obj = None
            
            if constraint:
                constraint_obj = self.parse_constraint(constraint)
            
            for version in available_versions:
                if isinstance(version, str):
                    version = self.parse_version(version)
                
                # Check constraint if specified
                if constraint_obj and not constraint_obj.matches(version):
                    continue
                
                # Check compatibility level - only include higher or equal versions
                if version >= target_version:
                    compatibility = self.check_compatibility(target_version, version)
                    if compatibility in [CompatibilityLevel.COMPATIBLE, 
                                       CompatibilityLevel.MINOR_BREAKING]:
                        compatible_versions.append(version)
            
            # Sort by version precedence (highest first)
            compatible_versions.sort(reverse=True)
            
            self.logger.debug(f"Found {len(compatible_versions)} compatible versions for {target_version}")
            return compatible_versions
    
    def resolve_dependencies(self, dependencies: Dict[str, str]) -> Dict[str, Version]:
        """
        Resolve dependency versions from constraint specifications.
        
        Args:
            dependencies: Dict mapping package names to version constraints
            
        Returns:
            Dict mapping package names to resolved versions
            
        Raises:
            RuntimeError: If dependency resolution fails
        """
        with self._operations_lock:
            self._increment_operation_count()
            
            resolved = {}
            
            self.logger.info(f"Resolving {len(dependencies)} dependencies")
            
            for package_name, constraint_string in dependencies.items():
                try:
                    constraint = self.parse_constraint(constraint_string)
                    
                    # For this implementation, we'll use the constraint version
                    # as the resolved version. In a real system, this would
                    # query a package repository.
                    resolved_version = constraint.version
                    
                    resolved[package_name] = resolved_version
                    self.logger.debug(f"Resolved {package_name}: {constraint_string} -> {resolved_version}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to resolve dependency {package_name}: {e}")
                    raise RuntimeError(f"Dependency resolution failed for {package_name}: {e}") from e
            
            self.logger.info(f"Successfully resolved all {len(resolved)} dependencies")
            return resolved
    
    def validate_version_range(self, min_version: Union[str, Version],
                              max_version: Union[str, Version],
                              check_version: Union[str, Version]) -> bool:
        """
        Check if version falls within specified range.
        
        Args:
            min_version: Minimum version (inclusive)
            max_version: Maximum version (inclusive)  
            check_version: Version to check
            
        Returns:
            True if version is within range
        """
        if isinstance(min_version, str):
            min_version = self.parse_version(min_version)
        if isinstance(max_version, str):
            max_version = self.parse_version(max_version)
        if isinstance(check_version, str):
            check_version = self.parse_version(check_version)
        
        result = min_version <= check_version <= max_version
        
        self.logger.debug(f"Version range check: {min_version} <= {check_version} <= {max_version} = {result}")
        return result
    
    def get_latest_version(self, versions: List[Union[str, Version]],
                          include_prerelease: bool = False) -> Optional[Version]:
        """
        Get the latest version from a list of versions.
        
        Args:
            versions: List of versions
            include_prerelease: Whether to consider pre-release versions
            
        Returns:
            Latest version or None if list is empty
        """
        if not versions:
            return None
        
        parsed_versions = []
        for version in versions:
            if isinstance(version, str):
                version = self.parse_version(version)
            
            if not include_prerelease and version.is_prerelease:
                continue
                
            parsed_versions.append(version)
        
        if not parsed_versions:
            return None
        
        latest = max(parsed_versions)
        self.logger.debug(f"Latest version from {len(versions)} candidates: {latest}")
        return latest
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get version manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._stats_lock:
            return {
                'operation_count': self._operation_count,
                'cached_versions': len(self._version_cache),
                'cached_dependencies': len(self._dependency_cache)
            }
    
    def clear_cache(self) -> None:
        """Clear version and dependency caches"""
        with self._cache_lock:
            self._version_cache.clear()
            self._dependency_cache.clear()
            
        self.logger.info("Version manager caches cleared")