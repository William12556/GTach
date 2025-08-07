#!/usr/bin/env python3
"""
Package Repository System for GTach Application Provisioning

Provides local package storage with metadata indexing, search capabilities, and
cross-platform compatibility. Implements thread-safe operations with Protocol 8
compliant logging and Protocol 6 cross-platform standards.

Features:
- Directory-based package storage (~/.gtach/repository/)
- JSON metadata indexing and persistence
- Search/query interface (name, version, platform)
- Package CRUD operations (store, retrieve, list, delete)
- Repository maintenance (cleanup, validation)
- Thread-safe operations
- Cross-platform path handling
- Version Manager integration
"""

import os
import json
import shutil
import hashlib
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from contextlib import contextmanager

# Import version manager for integration
try:
    from .version_manager import VersionManager, Version, CompatibilityLevel
    from .package_creator import PackageManifest
except ImportError:
    # Fallback for development/testing
    import sys
    sys.path.append(str(Path(__file__).parent))
    from version_manager import VersionManager, Version, CompatibilityLevel
    from package_creator import PackageManifest


@dataclass
class PackageEntry:
    """Package entry in repository index"""
    name: str
    version: str
    platform: str
    file_path: str  # Relative to repository root
    file_size: int
    checksum: str
    created_at: str
    manifest: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PackageEntry':
        """Create instance from dictionary"""
        # Handle tags field which might be missing in old data
        if 'tags' not in data:
            data['tags'] = []
        return cls(**data)


@dataclass
class SearchQuery:
    """Search query specification"""
    name: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    version_constraint: Optional[str] = None  # e.g., ">=1.0.0", "^2.1.0"
    tags: List[str] = field(default_factory=list)
    created_after: Optional[str] = None  # ISO format date
    created_before: Optional[str] = None  # ISO format date
    
    def matches(self, entry: PackageEntry, version_manager: VersionManager) -> bool:
        """Check if entry matches this search query"""
        # Name filter
        if self.name and self.name not in entry.name:
            return False
        
        # Exact version filter
        if self.version and entry.version != self.version:
            return False
        
        # Platform filter
        if self.platform and entry.platform != self.platform:
            return False
        
        # Version constraint filter
        if self.version_constraint:
            try:
                constraint = version_manager.parse_constraint(self.version_constraint)
                entry_version = version_manager.parse_version(entry.version)
                if not constraint.matches(entry_version):
                    return False
            except Exception:
                return False  # Invalid constraint or version
        
        # Tags filter (all tags must be present)
        if self.tags and not all(tag in entry.tags for tag in self.tags):
            return False
        
        # Date range filters
        if self.created_after and entry.created_at < self.created_after:
            return False
        if self.created_before and entry.created_at > self.created_before:
            return False
        
        return True


@dataclass
class RepositoryStats:
    """Repository statistics"""
    total_packages: int
    total_size_bytes: int
    platforms: List[str]
    package_names: List[str]
    version_range: Tuple[str, str]  # (oldest, newest)
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class PackageRepository:
    """
    Thread-safe package repository for local package storage and management.
    
    Provides comprehensive package storage with metadata indexing, search
    capabilities, and cross-platform compatibility following Protocol standards.
    """
    
    DEFAULT_REPO_PATH = Path.home() / ".gtach" / "repository"
    INDEX_FILE = "index.json"
    STATS_FILE = "stats.json"
    
    def __init__(self, repository_path: Optional[Union[str, Path]] = None):
        """
        Initialize PackageRepository with thread-safe operations.
        
        Args:
            repository_path: Optional custom repository path. Defaults to ~/.gtach/repository/
        """
        # Session-based logging per Protocol 8
        self.logger = logging.getLogger(f'{__name__}.PackageRepository')
        
        # Repository path setup with cross-platform compatibility per Protocol 6
        if repository_path is None:
            self.repository_path = self.DEFAULT_REPO_PATH
        else:
            self.repository_path = Path(repository_path)
        
        self.packages_dir = self.repository_path / "packages"
        self.index_file = self.repository_path / self.INDEX_FILE
        self.stats_file = self.repository_path / self.STATS_FILE
        
        # Thread safety per Protocol 8
        self._operations_lock = threading.RLock()
        self._index_lock = threading.Lock()
        self._operation_count = 0
        self._stats_lock = threading.Lock()
        
        # Version manager integration
        self.version_manager = VersionManager()
        
        # Package index (cached in memory, persisted to disk)
        self._package_index: Dict[str, PackageEntry] = {}
        self._index_loaded = False
        
        # Repository statistics
        self._stats: Optional[RepositoryStats] = None
        
        # Initialize repository structure
        self._initialize_repository()
        
        self.logger.info(f"PackageRepository initialized: {self.repository_path}")
    
    def _initialize_repository(self) -> None:
        """Initialize repository directory structure"""
        try:
            # Create directory structure
            self.repository_path.mkdir(parents=True, exist_ok=True)
            self.packages_dir.mkdir(exist_ok=True)
            
            # Load existing index
            self._load_index()
            
            # Initialize stats
            self._update_stats()
            
            self.logger.debug(f"Repository structure initialized at {self.repository_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize repository structure: {e}")
            raise RuntimeError(f"Repository initialization failed: {e}") from e
    
    def _load_index(self) -> None:
        """Load package index from disk"""
        with self._index_lock:
            if self.index_file.exists():
                try:
                    with open(self.index_file, 'r') as f:
                        index_data = json.load(f)
                    
                    self._package_index = {
                        key: PackageEntry.from_dict(entry_data)
                        for key, entry_data in index_data.items()
                    }
                    
                    self.logger.debug(f"Loaded {len(self._package_index)} packages from index")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load package index: {e}")
                    self._package_index = {}
            else:
                self._package_index = {}
                self.logger.debug("No existing index found, starting with empty repository")
            
            self._index_loaded = True
    
    def _save_index(self) -> None:
        """Save package index to disk"""
        with self._index_lock:
            try:
                # Convert to serializable format
                index_data = {
                    key: entry.to_dict()
                    for key, entry in self._package_index.items()
                }
                
                # Atomic write
                temp_file = self.index_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(index_data, f, indent=2, sort_keys=True)
                
                # Replace original file
                temp_file.replace(self.index_file)
                
                self.logger.debug(f"Saved {len(self._package_index)} packages to index")
                
            except Exception as e:
                self.logger.error(f"Failed to save package index: {e}")
                raise RuntimeError(f"Index save failed: {e}") from e
    
    def _generate_package_key(self, name: str, version: str, platform: str) -> str:
        """Generate unique key for package identification"""
        return f"{name}#{version}#{platform}"
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _get_package_file_path(self, name: str, version: str, platform: str) -> Path:
        """Get full path for package file"""
        # Create subdirectory structure: packages/name/platform/
        package_dir = self.packages_dir / name / platform
        filename = f"{name}-{version}-{platform}.tar.gz"
        return package_dir / filename
    
    def _get_relative_package_path(self, name: str, version: str, platform: str) -> str:
        """Get relative path for package file (from repository root)"""
        full_path = self._get_package_file_path(name, version, platform)
        return str(full_path.relative_to(self.repository_path))
    
    def store_package(self, 
                     package_file: Union[str, Path], 
                     name: str, 
                     version: str, 
                     platform: str,
                     manifest: Optional[PackageManifest] = None,
                     tags: Optional[List[str]] = None) -> PackageEntry:
        """
        Store package in repository with metadata indexing.
        
        Args:
            package_file: Path to package file
            name: Package name
            version: Package version
            platform: Target platform
            manifest: Optional package manifest
            tags: Optional tags for categorization
            
        Returns:
            Created PackageEntry
            
        Raises:
            RuntimeError: If storage fails
            ValueError: If package already exists or invalid parameters
        """
        with self._operations_lock:
            self._increment_operation_count()
            
            package_file = Path(package_file)
            if not package_file.exists():
                raise ValueError(f"Package file does not exist: {package_file}")
            
            # Validate version format
            try:
                self.version_manager.parse_version(version)
            except ValueError as e:
                raise ValueError(f"Invalid semantic version '{version}': {e}") from e
            
            # Check if package already exists
            package_key = self._generate_package_key(name, version, platform)
            if package_key in self._package_index:
                raise ValueError(f"Package already exists: {name} v{version} ({platform})")
            
            self.logger.info(f"Storing package: {name} v{version} for {platform}")
            
            try:
                # Calculate destination path
                dest_path = self._get_package_file_path(name, version, platform)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy package file
                shutil.copy2(package_file, dest_path)
                
                # Calculate checksum and file info
                file_size = dest_path.stat().st_size
                checksum = self._calculate_file_checksum(dest_path)
                
                # Create package entry
                entry = PackageEntry(
                    name=name,
                    version=version,
                    platform=platform,
                    file_path=self._get_relative_package_path(name, version, platform),
                    file_size=file_size,
                    checksum=checksum,
                    created_at=datetime.now().isoformat(),
                    manifest=manifest.to_dict() if manifest else None,
                    tags=tags or []
                )
                
                # Add to index
                self._package_index[package_key] = entry
                
                # Save index and update stats
                self._save_index()
                self._update_stats()
                
                self.logger.info(f"Package stored successfully: {name} v{version} ({file_size:,} bytes)")
                return entry
                
            except Exception as e:
                self.logger.error(f"Failed to store package {name} v{version}: {e}")
                # Cleanup on failure
                try:
                    if dest_path.exists():
                        dest_path.unlink()
                except Exception:
                    pass
                raise RuntimeError(f"Package storage failed: {e}") from e
    
    def retrieve_package(self, name: str, version: str, platform: str) -> Optional[Path]:
        """
        Retrieve package file path.
        
        Args:
            name: Package name
            version: Package version
            platform: Target platform
            
        Returns:
            Path to package file or None if not found
        """
        package_key = self._generate_package_key(name, version, platform)
        
        if package_key not in self._package_index:
            return None
        
        entry = self._package_index[package_key]
        package_path = self.repository_path / entry.file_path
        
        if not package_path.exists():
            self.logger.warning(f"Package file missing for indexed entry: {package_path}")
            return None
        
        return package_path
    
    def get_package_info(self, name: str, version: str, platform: str) -> Optional[PackageEntry]:
        """
        Get package information.
        
        Args:
            name: Package name
            version: Package version
            platform: Target platform
            
        Returns:
            PackageEntry or None if not found
        """
        package_key = self._generate_package_key(name, version, platform)
        return self._package_index.get(package_key)
    
    def search_packages(self, query: SearchQuery) -> List[PackageEntry]:
        """
        Search packages using query criteria.
        
        Args:
            query: Search query specification
            
        Returns:
            List of matching PackageEntry objects
        """
        with self._operations_lock:
            self._increment_operation_count()
            
            matches = []
            
            for entry in self._package_index.values():
                if query.matches(entry, self.version_manager):
                    matches.append(entry)
            
            # Sort by version (newest first) then by name
            matches.sort(key=lambda e: (e.name, self.version_manager.parse_version(e.version)), reverse=True)
            
            self.logger.debug(f"Search query returned {len(matches)} packages")
            return matches
    
    def list_packages(self, 
                     platform: Optional[str] = None,
                     sort_by: str = "name") -> List[PackageEntry]:
        """
        List all packages with optional filtering and sorting.
        
        Args:
            platform: Optional platform filter
            sort_by: Sort criteria ("name", "version", "created_at", "size")
            
        Returns:
            List of PackageEntry objects
        """
        packages = list(self._package_index.values())
        
        # Apply platform filter
        if platform:
            packages = [p for p in packages if p.platform == platform]
        
        # Sort packages
        if sort_by == "name":
            packages.sort(key=lambda p: p.name)
        elif sort_by == "version":
            packages.sort(key=lambda p: self.version_manager.parse_version(p.version), reverse=True)
        elif sort_by == "created_at":
            packages.sort(key=lambda p: p.created_at, reverse=True)
        elif sort_by == "size":
            packages.sort(key=lambda p: p.file_size, reverse=True)
        
        return packages
    
    def delete_package(self, name: str, version: str, platform: str) -> bool:
        """
        Delete package from repository.
        
        Args:
            name: Package name
            version: Package version
            platform: Target platform
            
        Returns:
            True if deleted, False if not found
        """
        with self._operations_lock:
            self._increment_operation_count()
            
            package_key = self._generate_package_key(name, version, platform)
            
            if package_key not in self._package_index:
                return False
            
            entry = self._package_index[package_key]
            package_path = self.repository_path / entry.file_path
            
            try:
                # Remove file if it exists
                if package_path.exists():
                    package_path.unlink()
                
                # Remove from index
                del self._package_index[package_key]
                
                # Save index and update stats
                self._save_index()
                self._update_stats()
                
                self.logger.info(f"Package deleted: {name} v{version} ({platform})")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to delete package {name} v{version}: {e}")
                raise RuntimeError(f"Package deletion failed: {e}") from e
    
    def find_compatible_versions(self, 
                                name: str, 
                                target_version: str,
                                platform: str,
                                constraint: Optional[str] = None) -> List[PackageEntry]:
        """
        Find compatible versions of a package.
        
        Args:
            name: Package name
            target_version: Target version for compatibility check
            platform: Target platform
            constraint: Optional version constraint
            
        Returns:
            List of compatible PackageEntry objects
        """
        # Search for packages with same name and platform
        query = SearchQuery(name=name, platform=platform, version_constraint=constraint)
        candidates = self.search_packages(query)
        
        if not candidates:
            return []
        
        # Find compatible versions using version manager
        target_ver = self.version_manager.parse_version(target_version)
        compatible_versions = []
        
        for entry in candidates:
            entry_version = self.version_manager.parse_version(entry.version)
            if entry_version >= target_ver:
                compatibility = self.version_manager.check_compatibility(target_version, entry.version)
                if compatibility in [CompatibilityLevel.COMPATIBLE, CompatibilityLevel.MINOR_BREAKING]:
                    compatible_versions.append(entry)
        
        return compatible_versions
    
    def get_latest_version(self, name: str, platform: str, include_prerelease: bool = False) -> Optional[PackageEntry]:
        """
        Get the latest version of a package.
        
        Args:
            name: Package name
            platform: Target platform
            include_prerelease: Whether to consider pre-release versions
            
        Returns:
            PackageEntry for latest version or None if not found
        """
        query = SearchQuery(name=name, platform=platform)
        candidates = self.search_packages(query)
        
        if not candidates:
            return None
        
        # Filter out pre-release versions if not requested
        if not include_prerelease:
            candidates = [
                entry for entry in candidates
                if not self.version_manager.parse_version(entry.version).is_prerelease
            ]
        
        if not candidates:
            return None
        
        # Find latest version
        versions = [entry.version for entry in candidates]
        latest_version = self.version_manager.get_latest_version(versions, include_prerelease)
        
        if latest_version:
            # Find entry with latest version
            for entry in candidates:
                if entry.version == str(latest_version):
                    return entry
        
        return None
    
    def cleanup_repository(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Clean up repository by removing orphaned files and validating integrity.
        
        Args:
            dry_run: If True, only report what would be cleaned without making changes
            
        Returns:
            Dictionary with cleanup statistics
        """
        with self._operations_lock:
            self._increment_operation_count()
            
            stats = {
                'orphaned_files': 0,
                'missing_files': 0,
                'corrupted_files': 0,
                'total_cleaned': 0
            }
            
            self.logger.info(f"Starting repository cleanup (dry_run={dry_run})")
            
            # Find orphaned files
            indexed_files = set()
            for entry in self._package_index.values():
                indexed_files.add(self.repository_path / entry.file_path)
            
            # Scan all package files
            all_package_files = set()
            if self.packages_dir.exists():
                for file_path in self.packages_dir.rglob('*.tar.gz'):
                    all_package_files.add(file_path)
            
            # Find orphaned files (in filesystem but not in index)
            orphaned_files = all_package_files - indexed_files
            stats['orphaned_files'] = len(orphaned_files)
            
            if not dry_run:
                for orphaned_file in orphaned_files:
                    try:
                        orphaned_file.unlink()
                        self.logger.debug(f"Removed orphaned file: {orphaned_file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove orphaned file {orphaned_file}: {e}")
            
            # Find missing files (in index but not in filesystem)
            missing_entries = []
            for key, entry in self._package_index.items():
                file_path = self.repository_path / entry.file_path
                if not file_path.exists():
                    missing_entries.append(key)
                    stats['missing_files'] += 1
            
            if not dry_run:
                for key in missing_entries:
                    del self._package_index[key]
                    self.logger.debug(f"Removed missing entry from index: {key}")
            
            # Validate file integrity
            corrupted_entries = []
            for key, entry in self._package_index.items():
                if key in missing_entries:
                    continue
                
                file_path = self.repository_path / entry.file_path
                try:
                    current_checksum = self._calculate_file_checksum(file_path)
                    if current_checksum != entry.checksum:
                        corrupted_entries.append(key)
                        stats['corrupted_files'] += 1
                        self.logger.warning(f"Corrupted file detected: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to validate checksum for {file_path}: {e}")
                    corrupted_entries.append(key)
                    stats['corrupted_files'] += 1
            
            # Remove corrupted entries if not dry run
            if not dry_run:
                for key in corrupted_entries:
                    entry = self._package_index[key]
                    file_path = self.repository_path / entry.file_path
                    try:
                        if file_path.exists():
                            file_path.unlink()
                        del self._package_index[key]
                        self.logger.debug(f"Removed corrupted entry: {key}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove corrupted entry {key}: {e}")
            
            stats['total_cleaned'] = stats['orphaned_files'] + stats['missing_files'] + stats['corrupted_files']
            
            if not dry_run and (missing_entries or corrupted_entries):
                self._save_index()
                self._update_stats()
            
            self.logger.info(f"Repository cleanup completed: {stats}")
            return stats
    
    def _update_stats(self) -> None:
        """Update repository statistics"""
        if not self._package_index:
            self._stats = RepositoryStats(
                total_packages=0,
                total_size_bytes=0,
                platforms=[],
                package_names=[],
                version_range=("", ""),
                created_at=datetime.now().isoformat()
            )
            return
        
        # Calculate statistics
        total_size = sum(entry.file_size for entry in self._package_index.values())
        platforms = sorted(set(entry.platform for entry in self._package_index.values()))
        package_names = sorted(set(entry.name for entry in self._package_index.values()))
        
        # Find version range
        all_versions = [entry.version for entry in self._package_index.values()]
        try:
            parsed_versions = [self.version_manager.parse_version(v) for v in all_versions]
            oldest = str(min(parsed_versions))
            newest = str(max(parsed_versions))
            version_range = (oldest, newest)
        except Exception:
            version_range = ("", "")
        
        self._stats = RepositoryStats(
            total_packages=len(self._package_index),
            total_size_bytes=total_size,
            platforms=platforms,
            package_names=package_names,
            version_range=version_range,
            created_at=datetime.now().isoformat()
        )
        
        # Save stats to file
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self._stats.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save repository stats: {e}")
    
    def get_stats(self) -> RepositoryStats:
        """
        Get repository statistics.
        
        Returns:
            RepositoryStats object
        """
        if self._stats is None:
            self._update_stats()
        return self._stats
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """
        Get operation statistics.
        
        Returns:
            Dictionary with operation statistics
        """
        with self._stats_lock:
            return {
                'operation_count': self._operation_count,
                'repository_path': str(self.repository_path),
                'packages_loaded': len(self._package_index),
                'version_manager_stats': self.version_manager.get_stats()
            }