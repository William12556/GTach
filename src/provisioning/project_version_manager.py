#!/usr/bin/env python3
"""
Project Version Manager for GTach Application Provisioning System

Provides automated version management across all project files with atomic updates,
backup/restore functionality, and comprehensive error handling per Protocol 8.

Features:
- Thread-safe version management operations
- Atomic updates with rollback on failure
- File-specific version updaters using Strategy pattern
- Command pattern for transaction management
- Integration with existing provisioning workflow

Architecture:
- ProjectVersionManager: Coordinator for version operations
- FileVersionUpdater: Base class for file-specific handlers
- VersionWorkflow: Integration with provisioning system
"""

import re
import os
import tempfile
import shutil
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
from abc import ABC, abstractmethod
from enum import Enum, auto

try:
    from .version_manager import VersionManager, Version
except ImportError:
    # Fallback for development/testing
    import sys
    sys.path.append(str(Path(__file__).parent))
    from version_manager import VersionManager, Version


class FileType(Enum):
    """Supported file types for version management"""
    PYPROJECT_TOML = auto()
    SETUP_PY = auto()
    INIT_PY = auto()
    PACKAGE_CONFIG = auto()


class UpdateResult(Enum):
    """Result of version update operation"""
    SUCCESS = auto()
    NO_CHANGE = auto()
    FAILED = auto()
    BACKUP_CREATED = auto()
    RESTORED_FROM_BACKUP = auto()


@dataclass
class UpdateOperation:
    """Represents a version update operation"""
    file_path: Path
    file_type: FileType
    old_version: Optional[str] = None
    new_version: Optional[str] = None
    backup_path: Optional[Path] = None
    result: UpdateResult = UpdateResult.FAILED
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class FileVersionUpdater(ABC):
    """
    Abstract base class for file-specific version updaters.
    
    Implements Strategy pattern for different file types with consistent
    interface for version detection and updating.
    """
    
    def __init__(self, file_path: Path):
        """
        Initialize updater for specific file.
        
        Args:
            file_path: Path to file to manage
        """
        self.file_path = file_path
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')
        self.version_manager = VersionManager()
        
    @abstractmethod
    def detect_version(self) -> Optional[str]:
        """
        Detect current version in file.
        
        Returns:
            Current version string or None if not found
        """
        pass
        
    @abstractmethod  
    def update_version(self, new_version: str) -> bool:
        """
        Update version in file.
        
        Args:
            new_version: New version to set
            
        Returns:
            True if update was successful
        """
        pass
        
    @property
    @abstractmethod
    def file_type(self) -> FileType:
        """Get the file type this updater handles"""
        pass
        
    def validate_version(self, version_string: str) -> bool:
        """
        Validate version format.
        
        Args:
            version_string: Version to validate
            
        Returns:
            True if version is valid
        """
        try:
            self.version_manager.parse_version(version_string)
            return True
        except ValueError:
            return False
            
    def backup_file(self, backup_dir: Path) -> Optional[Path]:
        """
        Create backup of file.
        
        Args:
            backup_dir: Directory to store backup
            
        Returns:
            Path to backup file or None on failure
        """
        if not self.file_path.exists():
            return None
            
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_name = f"{self.file_path.name}.backup"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(self.file_path, backup_path)
            self.logger.debug(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {self.file_path}: {e}")
            return None
            
    def restore_from_backup(self, backup_path: Path) -> bool:
        """
        Restore file from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore was successful
        """
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, self.file_path)
                self.logger.info(f"Restored {self.file_path} from backup")
                return True
            else:
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to restore from backup {backup_path}: {e}")
            return False


class PyProjectTomlUpdater(FileVersionUpdater):
    """Version updater for pyproject.toml files"""
    
    @property
    def file_type(self) -> FileType:
        return FileType.PYPROJECT_TOML
        
    def detect_version(self) -> Optional[str]:
        """Detect version in pyproject.toml"""
        try:
            content = self.file_path.read_text()
            
            # Look for version = "x.y.z" in [project] section
            pattern = r'version\s*=\s*["\']([^"\']+)["\']'
            match = re.search(pattern, content)
            
            if match:
                version = match.group(1)
                self.logger.debug(f"Detected version in {self.file_path}: {version}")
                return version
            else:
                self.logger.warning(f"No version found in {self.file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to detect version in {self.file_path}: {e}")
            return None
            
    def update_version(self, new_version: str) -> bool:
        """Update version in pyproject.toml"""
        if not self.validate_version(new_version):
            self.logger.error(f"Invalid version format: {new_version}")
            return False
            
        try:
            content = self.file_path.read_text()
            
            # Replace version = "old" with version = "new"
            pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
            replacement = f'\\g<1>{new_version}\\g<3>'
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content == content:
                self.logger.warning(f"No version pattern found to update in {self.file_path}")
                return False
                
            self.file_path.write_text(new_content)
            self.logger.info(f"Updated version in {self.file_path} to {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update version in {self.file_path}: {e}")
            return False


class SetupPyUpdater(FileVersionUpdater):
    """Version updater for setup.py files"""
    
    @property
    def file_type(self) -> FileType:
        return FileType.SETUP_PY
        
    def detect_version(self) -> Optional[str]:
        """Detect version in setup.py"""
        try:
            content = self.file_path.read_text()
            
            # Look for version="x.y.z" in setup() call
            pattern = r'version\s*=\s*["\']([^"\']+)["\']'
            match = re.search(pattern, content)
            
            if match:
                version = match.group(1)
                self.logger.debug(f"Detected version in {self.file_path}: {version}")
                return version
            else:
                self.logger.warning(f"No version found in {self.file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to detect version in {self.file_path}: {e}")
            return None
            
    def update_version(self, new_version: str) -> bool:
        """Update version in setup.py"""
        if not self.validate_version(new_version):
            self.logger.error(f"Invalid version format: {new_version}")
            return False
            
        try:
            content = self.file_path.read_text()
            
            # Replace version="old" with version="new"
            pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
            replacement = f'\\g<1>{new_version}\\g<3>'
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content == content:
                self.logger.warning(f"No version pattern found to update in {self.file_path}")
                return False
                
            self.file_path.write_text(new_content)
            self.logger.info(f"Updated version in {self.file_path} to {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update version in {self.file_path}: {e}")
            return False


class InitPyUpdater(FileVersionUpdater):
    """Version updater for __init__.py files"""
    
    @property
    def file_type(self) -> FileType:
        return FileType.INIT_PY
        
    def detect_version(self) -> Optional[str]:
        """Detect version in __init__.py"""
        try:
            content = self.file_path.read_text()
            
            # Look for __version__ = "x.y.z"
            pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
            match = re.search(pattern, content)
            
            if match:
                version = match.group(1)
                self.logger.debug(f"Detected version in {self.file_path}: {version}")
                return version
            else:
                self.logger.warning(f"No __version__ found in {self.file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to detect version in {self.file_path}: {e}")
            return None
            
    def update_version(self, new_version: str) -> bool:
        """Update version in __init__.py"""
        if not self.validate_version(new_version):
            self.logger.error(f"Invalid version format: {new_version}")
            return False
            
        try:
            content = self.file_path.read_text()
            
            # Replace __version__ = "old" with __version__ = "new"
            pattern = r'(__version__\s*=\s*["\'])([^"\']+)(["\'])'
            replacement = f'\\g<1>{new_version}\\g<3>'
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content == content:
                self.logger.warning(f"No __version__ pattern found to update in {self.file_path}")
                return False
                
            self.file_path.write_text(new_content)
            self.logger.info(f"Updated __version__ in {self.file_path} to {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update version in {self.file_path}: {e}")
            return False


class PackageConfigUpdater(FileVersionUpdater):
    """Version updater for PackageConfig default values"""
    
    @property
    def file_type(self) -> FileType:
        return FileType.PACKAGE_CONFIG
        
    def detect_version(self) -> Optional[str]:
        """Detect version in PackageConfig file"""
        try:
            content = self.file_path.read_text()
            
            # Look for version: str = "x.y.z" in PackageConfig dataclass
            pattern = r'version:\s*str\s*=\s*["\']([^"\']+)["\']'
            match = re.search(pattern, content)
            
            if match:
                version = match.group(1)
                self.logger.debug(f"Detected PackageConfig version in {self.file_path}: {version}")
                return version
            else:
                self.logger.warning(f"No PackageConfig version found in {self.file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to detect version in {self.file_path}: {e}")
            return None
            
    def update_version(self, new_version: str) -> bool:
        """Update version in PackageConfig"""
        if not self.validate_version(new_version):
            self.logger.error(f"Invalid version format: {new_version}")
            return False
            
        try:
            content = self.file_path.read_text()
            
            # Replace version: str = "old" with version: str = "new"
            pattern = r'(version:\s*str\s*=\s*["\'])([^"\']+)(["\'])'
            replacement = f'\\g<1>{new_version}\\g<3>'
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content == content:
                self.logger.warning(f"No PackageConfig version pattern found to update in {self.file_path}")
                return False
                
            self.file_path.write_text(new_content)
            self.logger.info(f"Updated PackageConfig version in {self.file_path} to {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update version in {self.file_path}: {e}")
            return False


class ProjectVersionManager:
    """
    Thread-safe project version manager with atomic updates.
    
    Coordinates version updates across multiple file types with comprehensive
    error handling, backup/restore, and rollback capabilities.
    """
    
    def __init__(self, project_root: Union[str, Path]):
        """
        Initialize project version manager.
        
        Args:
            project_root: Root directory of project
        """
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(f'{__name__}.ProjectVersionManager')
        
        # Thread safety
        self._update_lock = threading.RLock()
        self._operation_count = 0
        self._stats_lock = threading.Lock()
        
        # Version manager for validation
        self.version_manager = VersionManager()
        
        # File updaters registry
        self._updaters: Dict[Path, FileVersionUpdater] = {}
        self._initialize_updaters()
        
        # Operation tracking
        self._operations_history: List[UpdateOperation] = []
        
        self.logger.info(f"ProjectVersionManager initialized for {self.project_root}")
        
    def _initialize_updaters(self) -> None:
        """Initialize file version updaters for known project files"""
        file_configs = [
            (self.project_root / "pyproject.toml", PyProjectTomlUpdater),
            (self.project_root / "setup.py", SetupPyUpdater),
            (self.project_root / "src" / "obdii" / "__init__.py", InitPyUpdater),
            (self.project_root / "src" / "provisioning" / "__init__.py", InitPyUpdater),
            (self.project_root / "src" / "provisioning" / "package_creator.py", PackageConfigUpdater),
        ]
        
        for file_path, updater_class in file_configs:
            if file_path.exists():
                self._updaters[file_path] = updater_class(file_path)
                self.logger.debug(f"Initialized updater for {file_path}")
        
        self.logger.info(f"Initialized {len(self._updaters)} file updaters")
        
    def get_current_versions(self) -> Dict[Path, Optional[str]]:
        """
        Get current versions from all managed files.
        
        Returns:
            Dictionary mapping file paths to their current versions
        """
        versions = {}
        
        for file_path, updater in self._updaters.items():
            try:
                version = updater.detect_version()
                versions[file_path] = version
                self.logger.debug(f"Current version in {file_path}: {version}")
            except Exception as e:
                self.logger.error(f"Failed to get version from {file_path}: {e}")
                versions[file_path] = None
                
        return versions
        
    def detect_version_inconsistencies(self) -> Dict[str, List[Path]]:
        """
        Detect version inconsistencies across project files.
        
        Returns:
            Dictionary mapping version strings to files with that version
        """
        current_versions = self.get_current_versions()
        version_groups: Dict[str, List[Path]] = {}
        
        for file_path, version in current_versions.items():
            if version is not None:
                if version not in version_groups:
                    version_groups[version] = []
                version_groups[version].append(file_path)
        
        self.logger.info(f"Found {len(version_groups)} different versions across project files")
        return version_groups
        
    @contextmanager
    def _atomic_transaction(self, target_version: str):
        """
        Context manager for atomic version updates with rollback.
        
        Args:
            target_version: Version to update to
        """
        backup_dir = None
        operations: List[UpdateOperation] = []
        
        try:
            # Create temporary backup directory
            backup_dir = Path(tempfile.mkdtemp(prefix="gtach_version_backup_"))
            self.logger.debug(f"Created backup directory: {backup_dir}")
            
            # Create backups
            for file_path, updater in self._updaters.items():
                operation = UpdateOperation(
                    file_path=file_path,
                    file_type=updater.file_type,
                    old_version=updater.detect_version(),
                    new_version=target_version
                )
                
                backup_path = updater.backup_file(backup_dir)
                if backup_path:
                    operation.backup_path = backup_path
                    operation.result = UpdateResult.BACKUP_CREATED
                    
                operations.append(operation)
                
            yield operations
            
        except Exception as e:
            # Rollback on any failure
            self.logger.error(f"Transaction failed, rolling back: {e}")
            
            for operation in operations:
                if operation.backup_path and operation.backup_path.exists():
                    updater = self._updaters[operation.file_path]
                    if updater.restore_from_backup(operation.backup_path):
                        operation.result = UpdateResult.RESTORED_FROM_BACKUP
                        self.logger.info(f"Rolled back {operation.file_path}")
                        
            raise
            
        finally:
            # Cleanup backup directory
            if backup_dir and backup_dir.exists():
                try:
                    shutil.rmtree(backup_dir)
                    self.logger.debug(f"Cleaned up backup directory: {backup_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup backup directory: {e}")
                    
            # Record operations
            self._operations_history.extend(operations)
            
    def update_all_versions(self, target_version: str) -> Dict[Path, UpdateResult]:
        """
        Update version across all managed files atomically.
        
        Args:
            target_version: Version to set across all files
            
        Returns:
            Dictionary mapping file paths to update results
            
        Raises:
            RuntimeError: If version update fails
        """
        with self._update_lock:
            self._increment_operation_count()
            start_time = time.perf_counter()
            
            self.logger.info(f"Starting atomic version update to {target_version}")
            
            # Validate target version
            if not self.version_manager.validate_version_format(target_version)[0]:
                raise ValueError(f"Invalid target version: {target_version}")
            
            results: Dict[Path, UpdateResult] = {}
            
            try:
                with self._atomic_transaction(target_version) as operations:
                    # Perform updates
                    for operation in operations:
                        updater = self._updaters[operation.file_path]
                        
                        if operation.old_version == target_version:
                            operation.result = UpdateResult.NO_CHANGE
                            self.logger.debug(f"No change needed for {operation.file_path}")
                        else:
                            if updater.update_version(target_version):
                                operation.result = UpdateResult.SUCCESS
                                self.logger.info(f"Updated {operation.file_path}: {operation.old_version} -> {target_version}")
                            else:
                                operation.result = UpdateResult.FAILED
                                operation.error_message = "Update operation failed"
                                
                        results[operation.file_path] = operation.result
                
                elapsed = time.perf_counter() - start_time
                success_count = sum(1 for r in results.values() if r == UpdateResult.SUCCESS)
                self.logger.info(f"Version update completed: {success_count}/{len(results)} files updated ({elapsed:.2f}s)")
                
                return results
                
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                self.logger.error(f"Version update failed after {elapsed:.2f}s: {e}")
                raise RuntimeError(f"Version update failed: {e}") from e
                
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
            current_versions = self.get_current_versions()
            inconsistencies = self.detect_version_inconsistencies()
            
            return {
                'operation_count': self._operation_count,
                'managed_files': len(self._updaters),
                'operations_history': len(self._operations_history),
                'current_versions': {str(path): version for path, version in current_versions.items()},
                'version_groups': {version: len(files) for version, files in inconsistencies.items()},
                'has_inconsistencies': len(inconsistencies) > 1
            }


class VersionWorkflow:
    """
    Version workflow integration for provisioning system.
    
    Provides high-level workflow operations for version management
    integrated with the provisioning package creation system.
    """
    
    def __init__(self, project_root: Union[str, Path]):
        """
        Initialize version workflow.
        
        Args:
            project_root: Root directory of project
        """
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(f'{__name__}.VersionWorkflow')
        self.project_manager = ProjectVersionManager(project_root)
        self.version_manager = VersionManager()
        
    def interactive_version_update(self) -> Optional[str]:
        """
        Interactive version update workflow with user input.
        
        Returns:
            Selected version string or None if cancelled
        """
        print("\n" + "=" * 60)
        print("🔧 GTach Project Version Management")
        print("=" * 60)
        
        # Show current state
        current_versions = self.project_manager.get_current_versions()
        inconsistencies = self.project_manager.detect_version_inconsistencies()
        
        print(f"\n📊 Current Version Status:")
        if len(inconsistencies) == 1:
            version = list(inconsistencies.keys())[0]
            print(f"✅ All files consistent at version: {version}")
        else:
            print(f"⚠️  Version inconsistencies detected:")
            for version, files in inconsistencies.items():
                print(f"   {version}: {len(files)} files")
        
        print(f"\n📁 Managed Files:")
        for file_path, version in current_versions.items():
            rel_path = file_path.relative_to(self.project_root)
            status = version if version else "❌ No version found"
            print(f"   {rel_path}: {status}")
        
        # Get target version from user
        print(f"\n🎯 Version Update Options:")
        examples = self.version_manager.suggest_version_examples()
        for i, example in enumerate(examples[:5], 1):
            print(f"   {i}. {example}")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"\n{'─' * 50}")
            if attempt == 0:
                version_input = input("Enter target version (or 'cancel' to abort): ").strip()
            else:
                print(f"Attempt {attempt + 1}/{max_attempts}")
                version_input = input("Enter target version: ").strip()
            
            if version_input.lower() in ['cancel', 'abort', 'exit', '']:
                print("Version update cancelled by user")
                return None
            
            # Validate version
            is_valid, feedback = self.version_manager.validate_version_format(version_input)
            if is_valid:
                print(f"✅ {feedback}")
                
                # Confirm update
                confirm = input(f"\nUpdate all files to version '{version_input}'? [y/N]: ").strip().lower()
                if confirm in ['y', 'yes']:
                    return self._execute_version_update(version_input)
                else:
                    print("Version update cancelled")
                    return None
            else:
                print(f"❌ {feedback}")
                if attempt < max_attempts - 1:
                    print(f"Please try again ({max_attempts - attempt - 1} attempts remaining)")
        
        print(f"❌ Maximum attempts reached. Version update cancelled.")
        return None
        
    def _execute_version_update(self, target_version: str) -> Optional[str]:
        """
        Execute version update with progress feedback.
        
        Args:
            target_version: Version to update to
            
        Returns:
            Updated version string or None on failure
        """
        print(f"\n🔄 Updating all project files to version {target_version}...")
        
        try:
            results = self.project_manager.update_all_versions(target_version)
            
            print(f"\n📋 Update Results:")
            success_count = 0
            for file_path, result in results.items():
                rel_path = file_path.relative_to(self.project_root)
                
                if result == UpdateResult.SUCCESS:
                    print(f"   ✅ {rel_path}: Updated successfully")
                    success_count += 1
                elif result == UpdateResult.NO_CHANGE:
                    print(f"   ➖ {rel_path}: No change needed")
                    success_count += 1
                else:
                    print(f"   ❌ {rel_path}: Update failed")
            
            if success_count == len(results):
                print(f"\n✅ Version update completed successfully!")
                print(f"   All {len(results)} files now at version {target_version}")
                self.logger.info(f"Interactive version update completed: {target_version}")
                return target_version
            else:
                print(f"\n⚠️  Version update completed with issues")
                print(f"   {success_count}/{len(results)} files updated successfully")
                return None
                
        except Exception as e:
            print(f"\n❌ Version update failed: {e}")
            self.logger.error(f"Interactive version update failed: {e}")
            return None
            
    def get_current_project_version(self) -> Optional[str]:
        """
        Get the current project version (most common version across files).
        
        Returns:
            Current project version or None if inconsistent
        """
        inconsistencies = self.project_manager.detect_version_inconsistencies()
        
        if len(inconsistencies) == 1:
            return list(inconsistencies.keys())[0]
        elif len(inconsistencies) > 1:
            # Return most common version
            most_common = max(inconsistencies.items(), key=lambda x: len(x[1]))
            self.logger.warning(f"Version inconsistencies detected, using most common: {most_common[0]}")
            return most_common[0]
        else:
            self.logger.error("No versions found in any managed files")
            return None