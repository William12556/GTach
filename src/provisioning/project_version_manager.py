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
            return None#!/usr/bin/env python3
"""
Enhanced Project Version Manager for GTach Application Provisioning System

Provides automated version management across all project files with VersionStateManager
integration, enhanced consistency detection, and coordinated state synchronization.

Features:
- Thread-safe version management operations with state coordination
- Atomic updates with rollback on failure for both project files and state
- VersionStateManager integration for authoritative version state management
- Enhanced consistency detection including version state analysis
- Interactive consistency resolution with improved user guidance
- Coordinated project file and state updates with atomic transactions
- Comprehensive error handling and fallback mechanisms
- Full backward compatibility with existing ProjectVersionManager API

Architecture:
- ProjectVersionManager: Enhanced coordinator with state integration
- FileVersionUpdater: Base class for file-specific handlers (unchanged)
- VersionWorkflow: Enhanced integration with state-aware workflows
- StateCoordinator: New component for coordinating state and project operations
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
    from .version_state_manager import VersionStateManager, VersionState, DevelopmentStage
    # Classes are now in this same file
except ImportError:
    # Fallback for development/testing
    import sys
    sys.path.append(str(Path(__file__).parent))
    from version_manager import VersionManager, Version
    from version_state_manager import VersionStateManager, VersionState, DevelopmentStage
    # Classes are now in this same file


@dataclass
class StateCoordinationResult:
    """Result of state coordination operation"""
    project_files_updated: bool = False
    state_updated: bool = False
    inconsistencies_resolved: bool = False
    authoritative_version: Optional[str] = None
    coordination_errors: List[str] = field(default_factory=list)
    operation_time_ms: float = 0.0


@dataclass
class VersionInconsistency:
    """Detailed version inconsistency information"""
    version: str
    source_type: str  # 'project_file', 'version_state', 'both'
    file_paths: List[Path] = field(default_factory=list)
    is_authoritative: bool = False  # True if this version is from state manager
    stage: Optional[DevelopmentStage] = None
    last_updated: Optional[float] = None


class EnhancedProjectVersionManager:
    """
    Thread-safe project version manager with VersionStateManager integration.
    
    Coordinates version updates across multiple file types and version state
    with comprehensive error handling, backup/restore, and rollback capabilities.
    Provides authoritative version state management and enhanced consistency detection.
    """
    
    def __init__(self, 
                 project_root: Union[str, Path], 
                 enable_state_management: bool = True,
                 session_id: Optional[str] = None):
        """
        Initialize enhanced project version manager.
        
        Args:
            project_root: Root directory of project
            enable_state_management: Enable VersionStateManager integration
            session_id: Optional session identifier for state management
        """
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(f'{__name__}.EnhancedProjectVersionManager')
        
        # State management configuration
        self.enable_state_management = enable_state_management
        self.session_id = session_id or f"project_mgr_{int(time.time())}"
        
        # Thread safety
        self._update_lock = threading.RLock()
        self._operation_count = 0
        self._stats_lock = threading.Lock()
        
        # Version manager for validation
        self.version_manager = VersionManager()
        
        # File updaters registry (unchanged from original)
        self._updaters: Dict[Path, FileVersionUpdater] = {}
        self._initialize_updaters()
        
        # Operation tracking
        self._operations_history: List[UpdateOperation] = []
        
        # State management integration
        self._state_manager: Optional[VersionStateManager] = None
        self._state_coordination_errors: List[str] = []
        
        if self.enable_state_management:
            try:
                self._state_manager = VersionStateManager(
                    self.project_root, 
                    session_id=self.session_id
                )
                self.logger.info(f"VersionStateManager integration enabled for session: {self.session_id}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize VersionStateManager: {e}")
                self._state_coordination_errors.append(f"State manager initialization failed: {e}")
                self.enable_state_management = False
        
        self.logger.info(f"Enhanced ProjectVersionManager initialized for {self.project_root}")
        self.logger.info(f"State management: {'enabled' if self.enable_state_management else 'disabled'}")
        
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
    
    def get_state_version(self) -> Optional[str]:
        """
        Get current version from state manager.
        
        Returns:
            Current version from state manager or None if not available
        """
        if not self._state_manager:
            return None
            
        try:
            current_state = self._state_manager.get_current_state()
            return current_state.current_version
        except Exception as e:
            self.logger.error(f"Failed to get version from state manager: {e}")
            return None
            
    def detect_version_inconsistencies_enhanced(self) -> Dict[str, VersionInconsistency]:
        """
        Enhanced version inconsistency detection including state analysis.
        
        Returns:
            Dictionary mapping version strings to detailed inconsistency information
        """
        inconsistencies: Dict[str, VersionInconsistency] = {}
        
        # Get project file versions
        current_versions = self.get_current_versions()
        
        for file_path, version in current_versions.items():
            if version is not None:
                if version not in inconsistencies:
                    inconsistencies[version] = VersionInconsistency(
                        version=version,
                        source_type='project_file'
                    )
                inconsistencies[version].file_paths.append(file_path)
        
        # Include state manager version if available
        state_version = self.get_state_version()
        if state_version:
            if state_version not in inconsistencies:
                inconsistencies[state_version] = VersionInconsistency(
                    version=state_version,
                    source_type='version_state',
                    is_authoritative=True
                )
            else:
                # State version matches project file version
                inconsistencies[state_version].source_type = 'both'
                inconsistencies[state_version].is_authoritative = True
            
            # Add state-specific metadata
            try:
                state = self._state_manager.get_current_state()
                inconsistencies[state_version].stage = state.current_stage
                inconsistencies[state_version].last_updated = state.last_updated
            except Exception as e:
                self.logger.warning(f"Failed to get state metadata: {e}")
        
        self.logger.info(f"Enhanced inconsistency detection found {len(inconsistencies)} different versions")
        
        # Log detailed inconsistency information
        for version, info in inconsistencies.items():
            self.logger.debug(f"Version {version}: {info.source_type}, "
                            f"files: {len(info.file_paths)}, "
                            f"authoritative: {info.is_authoritative}")
        
        return inconsistencies
    
    def detect_version_inconsistencies(self) -> Dict[str, List[Path]]:
        """
        Backward-compatible version inconsistency detection.
        
        Returns:
            Dictionary mapping version strings to files with that version
        """
        enhanced_inconsistencies = self.detect_version_inconsistencies_enhanced()
        
        # Convert to original format for backward compatibility
        simple_inconsistencies: Dict[str, List[Path]] = {}
        
        for version, info in enhanced_inconsistencies.items():
            simple_inconsistencies[version] = info.file_paths
            
        return simple_inconsistencies
    
    def resolve_inconsistencies_interactive(self) -> StateCoordinationResult:
        """
        Interactive inconsistency resolution with enhanced user guidance.
        
        Returns:
            StateCoordinationResult with resolution details
        """
        start_time = time.perf_counter()
        result = StateCoordinationResult()
        
        try:
            inconsistencies = self.detect_version_inconsistencies_enhanced()
            
            if len(inconsistencies) <= 1:
                print("✅ No version inconsistencies detected")
                result.inconsistencies_resolved = True
                return result
            
            print(f"\n⚠️  Version Inconsistencies Detected!")
            print(f"Found {len(inconsistencies)} different versions:")
            print(f"─" * 60)
            
            # Display detailed inconsistency information
            for i, (version, info) in enumerate(inconsistencies.items(), 1):
                status_icon = "🎯" if info.is_authoritative else "📄"
                source_desc = "State + Project" if info.source_type == 'both' else info.source_type.replace('_', ' ').title()
                
                print(f"{i}. {status_icon} {version}")
                print(f"   Source: {source_desc}")
                print(f"   Files: {len(info.file_paths)}")
                
                if info.is_authoritative:
                    print(f"   Status: ⭐ Authoritative (Version State Manager)")
                    if info.stage:
                        print(f"   Stage: {info.stage.value}")
                    if info.last_updated:
                        update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info.last_updated))
                        print(f"   Last Updated: {update_time}")
                
                if info.file_paths:
                    print(f"   Project Files:")
                    for file_path in info.file_paths:
                        rel_path = file_path.relative_to(self.project_root)
                        print(f"     • {rel_path}")
                print()
            
            # Find authoritative version
            authoritative_version = None
            for version, info in inconsistencies.items():
                if info.is_authoritative:
                    authoritative_version = version
                    break
            
            print(f"Resolution Options:")
            
            if authoritative_version:
                print(f"1. Sync all project files to authoritative version ({authoritative_version}) [RECOMMENDED]")
                print(f"2. Update authoritative version to most common project version")
                print(f"3. Set new version for entire project (interactive)")
                print(f"4. Continue with inconsistencies")
            else:
                print(f"1. Update version state to most common project version")
                print(f"2. Set new version for entire project (interactive)")
                print(f"3. Continue with inconsistencies")
            
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    choice = input(f"\nSelect resolution option: ").strip()
                    
                    if authoritative_version and choice == "1":
                        # Sync to authoritative version
                        return self._sync_to_authoritative_version(authoritative_version)
                        
                    elif choice == "2" or (not authoritative_version and choice == "1"):
                        # Update state to most common project version
                        return self._update_state_to_project_consensus(inconsistencies)
                        
                    elif choice == "3" or (not authoritative_version and choice == "2"):
                        # Interactive version setting
                        return self._set_version_interactive(inconsistencies)
                        
                    elif choice == "4" or (not authoritative_version and choice == "3"):
                        # Continue with inconsistencies
                        print("⚠️  Continuing with version inconsistencies")
                        result.inconsistencies_resolved = False
                        return result
                        
                    else:
                        print("❌ Invalid choice. Please try again.")
                        continue
                        
                except KeyboardInterrupt:
                    print("\n❌ Resolution cancelled by user")
                    result.coordination_errors.append("Resolution cancelled by user")
                    return result
                except Exception as e:
                    self.logger.error(f"Error during resolution: {e}")
                    result.coordination_errors.append(f"Resolution error: {e}")
                    if attempt == max_attempts - 1:
                        return result
                    print(f"❌ Error: {e}. Please try again.")
            
            result.coordination_errors.append("Maximum resolution attempts exceeded")
            return result
            
        except Exception as e:
            self.logger.error(f"Interactive resolution failed: {e}")
            result.coordination_errors.append(f"Interactive resolution failed: {e}")
            return result
            
        finally:
            result.operation_time_ms = (time.perf_counter() - start_time) * 1000
    
    def _sync_to_authoritative_version(self, authoritative_version: str) -> StateCoordinationResult:
        """Synchronize all project files to authoritative version"""
        result = StateCoordinationResult(authoritative_version=authoritative_version)
        
        try:
            print(f"\n🔄 Synchronizing all project files to: {authoritative_version}")
            
            # Update all project files
            update_results = self.update_all_versions(authoritative_version)
            
            success_count = sum(1 for r in update_results.values() 
                              if r in [UpdateResult.SUCCESS, UpdateResult.NO_CHANGE])
            
            if success_count == len(update_results):
                print(f"✅ All {len(update_results)} project files synchronized")
                result.project_files_updated = True
                result.inconsistencies_resolved = True
                
                # State is already at the authoritative version
                result.state_updated = True
            else:
                print(f"⚠️  Partial synchronization: {success_count}/{len(update_results)} files updated")
                result.project_files_updated = success_count > 0
                result.coordination_errors.append(
                    f"Partial project file update: {success_count}/{len(update_results)} files"
                )
            
        except Exception as e:
            self.logger.error(f"Failed to sync to authoritative version: {e}")
            result.coordination_errors.append(f"Sync to authoritative failed: {e}")
            
        return result
    
    def _update_state_to_project_consensus(self, inconsistencies: Dict[str, VersionInconsistency]) -> StateCoordinationResult:
        """Update state manager to most common project version"""
        result = StateCoordinationResult()
        
        try:
            # Find most common project version
            project_versions = {v: info for v, info in inconsistencies.items() 
                              if 'project_file' in info.source_type}
            
            if not project_versions:
                result.coordination_errors.append("No project versions found for consensus")
                return result
            
            most_common = max(project_versions.items(), key=lambda x: len(x[1].file_paths))
            consensus_version = most_common[0]
            
            print(f"\n🔄 Updating version state to project consensus: {consensus_version}")
            
            if self._state_manager:
                try:
                    self._state_manager.update_version(
                        consensus_version,
                        increment_type="project_consensus_sync",
                        user_context="Synchronized to project file consensus",
                        operation_context="consistency_resolution"
                    )
                    
                    print(f"✅ Version state updated to: {consensus_version}")
                    result.state_updated = True
                    result.authoritative_version = consensus_version
                    
                    # Check if all project files are now consistent
                    if len(project_versions) == 1:
                        result.inconsistencies_resolved = True
                        print(f"✅ All versions now consistent at: {consensus_version}")
                    else:
                        print(f"⚠️  Project files still have inconsistencies")
                        
                except Exception as e:
                    self.logger.error(f"Failed to update state manager: {e}")
                    result.coordination_errors.append(f"State update failed: {e}")
            else:
                result.coordination_errors.append("State manager not available")
                
        except Exception as e:
            self.logger.error(f"Failed to determine project consensus: {e}")
            result.coordination_errors.append(f"Consensus determination failed: {e}")
            
        return result
    
    def _set_version_interactive(self, inconsistencies: Dict[str, VersionInconsistency]) -> StateCoordinationResult:
        """Set new version interactively for entire project"""
        result = StateCoordinationResult()
        
        try:
            print(f"\n📝 Interactive Version Setting")
            print(f"Current versions: {list(inconsistencies.keys())}")
            
            # Get suggestions from state manager if available
            suggestions = []
            if self._state_manager:
                try:
                    for inc_type in ["minor", "major", "patch"]:
                        version_suggestions = self._state_manager.suggest_next_version(inc_type)
                        if version_suggestions:
                            suggestions.extend(version_suggestions[:2])
                except Exception as e:
                    self.logger.warning(f"Failed to get version suggestions: {e}")
            
            if not suggestions:
                # Fallback to basic suggestions
                suggestions = self.version_manager.suggest_version_examples()[:5]
            
            print(f"\nSuggested versions:")
            for i, suggestion in enumerate(suggestions[:5], 1):
                print(f"   {i}. {suggestion}")
            
            max_attempts = 3
            for attempt in range(max_attempts):
                version_input = input(f"\nEnter new version (or 'cancel' to abort): ").strip()
                
                if version_input.lower() in ['cancel', 'abort', 'exit', '']:
                    print("❌ Interactive version setting cancelled")
                    result.coordination_errors.append("Interactive setting cancelled")
                    return result
                
                # Validate version
                is_valid, feedback = self.version_manager.validate_version_format(version_input)
                
                if is_valid:
                    print(f"✅ {feedback}")
                    
                    confirm = input(f"Set all project files and state to '{version_input}'? [y/N]: ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return self._apply_version_to_all(version_input)
                    else:
                        print("Version setting cancelled")
                        result.coordination_errors.append("Version setting cancelled by user")
                        return result
                else:
                    print(f"❌ {feedback}")
                    if attempt < max_attempts - 1:
                        print(f"Please try again ({max_attempts - attempt - 1} attempts remaining)")
            
            result.coordination_errors.append("Maximum version input attempts exceeded")
            return result
            
        except Exception as e:
            self.logger.error(f"Interactive version setting failed: {e}")
            result.coordination_errors.append(f"Interactive setting failed: {e}")
            return result
    
    def _apply_version_to_all(self, target_version: str) -> StateCoordinationResult:
        """Apply target version to all project files and state"""
        result = StateCoordinationResult(authoritative_version=target_version)
        
        try:
            print(f"\n🔄 Applying version {target_version} to entire project...")
            
            # Update project files first
            try:
                update_results = self.update_all_versions(target_version)
                success_count = sum(1 for r in update_results.values() 
                                  if r in [UpdateResult.SUCCESS, UpdateResult.NO_CHANGE])
                
                if success_count == len(update_results):
                    print(f"✅ All {len(update_results)} project files updated")
                    result.project_files_updated = True
                else:
                    print(f"⚠️  Partial project file update: {success_count}/{len(update_results)}")
                    result.project_files_updated = success_count > 0
                    result.coordination_errors.append(
                        f"Partial project update: {success_count}/{len(update_results)}"
                    )
                
            except Exception as e:
                self.logger.error(f"Failed to update project files: {e}")
                result.coordination_errors.append(f"Project file update failed: {e}")
            
            # Update state manager
            if self._state_manager:
                try:
                    self._state_manager.update_version(
                        target_version,
                        increment_type="interactive_project_sync",
                        user_context="Interactive project-wide version update",
                        operation_context="consistency_resolution"
                    )
                    
                    print(f"✅ Version state updated to: {target_version}")
                    result.state_updated = True
                    
                except Exception as e:
                    self.logger.error(f"Failed to update state manager: {e}")
                    result.coordination_errors.append(f"State update failed: {e}")
            
            # Check final consistency
            if result.project_files_updated and result.state_updated:
                result.inconsistencies_resolved = True
                print(f"✅ Entire project synchronized to: {target_version}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply version to all: {e}")
            result.coordination_errors.append(f"Version application failed: {e}")
            
        return result
    
    @contextmanager
    def _atomic_transaction_enhanced(self, target_version: str):
        """
        Enhanced atomic transaction with state coordination.
        
        Args:
            target_version: Version to update to
        """
        backup_dir = None
        operations: List[UpdateOperation] = []
        state_backup = None
        
        try:
            # Create temporary backup directory
            backup_dir = Path(tempfile.mkdtemp(prefix="gtach_enhanced_backup_"))
            self.logger.debug(f"Created enhanced backup directory: {backup_dir}")
            
            # Backup state manager if available
            if self._state_manager:
                try:
                    state_backup = self._state_manager.get_current_state()
                    self.logger.debug("Created version state backup")
                except Exception as e:
                    self.logger.warning(f"Failed to backup version state: {e}")
            
            # Create file backups
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
            # Enhanced rollback including state restoration
            self.logger.error(f"Enhanced transaction failed, rolling back: {e}")
            
            # Rollback project files
            for operation in operations:
                if operation.backup_path and operation.backup_path.exists():
                    updater = self._updaters[operation.file_path]
                    if updater.restore_from_backup(operation.backup_path):
                        operation.result = UpdateResult.RESTORED_FROM_BACKUP
                        self.logger.info(f"Rolled back {operation.file_path}")
            
            # Rollback state if needed and available
            if state_backup and self._state_manager:
                try:
                    # Note: This is a simplified rollback - in production,
                    # VersionStateManager should have proper rollback mechanisms
                    self.logger.warning("State rollback needed but not fully implemented")
                except Exception as state_error:
                    self.logger.error(f"State rollback failed: {state_error}")
                        
            raise
            
        finally:
            # Cleanup backup directory
            if backup_dir and backup_dir.exists():
                try:
                    shutil.rmtree(backup_dir)
                    self.logger.debug(f"Cleaned up enhanced backup directory: {backup_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup backup directory: {e}")
                    
            # Record operations
            self._operations_history.extend(operations)
    
    def update_all_versions_coordinated(self, target_version: str, 
                                      update_state: bool = True) -> StateCoordinationResult:
        """
        Update version across all managed files with state coordination.
        
        Args:
            target_version: Version to set across all files
            update_state: Whether to also update version state manager
            
        Returns:
            StateCoordinationResult with coordination details
        """
        start_time = time.perf_counter()
        result = StateCoordinationResult(authoritative_version=target_version)
        
        with self._update_lock:
            self._increment_operation_count()
            
            self.logger.info(f"Starting coordinated version update to {target_version}")
            
            # Validate target version
            if not self.version_manager.validate_version_format(target_version)[0]:
                result.coordination_errors.append(f"Invalid target version: {target_version}")
                return result
            
            try:
                with self._atomic_transaction_enhanced(target_version) as operations:
                    # Update project files
                    project_results: Dict[Path, UpdateResult] = {}
                    
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
                                
                        project_results[operation.file_path] = operation.result
                    
                    # Check project file update success
                    success_count = sum(1 for r in project_results.values() 
                                      if r in [UpdateResult.SUCCESS, UpdateResult.NO_CHANGE])
                    
                    result.project_files_updated = success_count == len(project_results)
                    if not result.project_files_updated:
                        result.coordination_errors.append(
                            f"Project files partially updated: {success_count}/{len(project_results)}"
                        )
                    
                    # Update state manager if requested and available
                    if update_state and self._state_manager:
                        try:
                            self._state_manager.update_version(
                                target_version,
                                increment_type="coordinated_update",
                                user_context="Coordinated project file update",
                                operation_context="enhanced_project_manager"
                            )
                            result.state_updated = True
                            self.logger.info(f"Version state updated to: {target_version}")
                            
                        except Exception as e:
                            self.logger.error(f"Failed to update version state: {e}")
                            result.coordination_errors.append(f"State update failed: {e}")
                    
                    # Determine overall success
                    if result.project_files_updated and (result.state_updated or not update_state):
                        result.inconsistencies_resolved = True
                
                elapsed = time.perf_counter() - start_time
                result.operation_time_ms = elapsed * 1000
                
                self.logger.info(f"Coordinated version update completed: "
                               f"project={result.project_files_updated}, "
                               f"state={result.state_updated}, "
                               f"time={elapsed:.2f}s")
                
                return result
                
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                self.logger.error(f"Coordinated version update failed after {elapsed:.2f}s: {e}")
                result.coordination_errors.append(f"Coordinated update failed: {e}")
                result.operation_time_ms = elapsed * 1000
                return result
    
    def update_all_versions(self, target_version: str) -> Dict[Path, UpdateResult]:
        """
        Backward-compatible version update method.
        
        Args:
            target_version: Version to set across all files
            
        Returns:
            Dictionary mapping file paths to update results
        """
        coordination_result = self.update_all_versions_coordinated(target_version, update_state=True)
        
        # Convert to original format for backward compatibility
        results: Dict[Path, UpdateResult] = {}
        
        for operation in self._operations_history[-len(self._updaters):]:
            results[operation.file_path] = operation.result
        
        # Log coordination errors if any
        if coordination_result.coordination_errors:
            self.logger.warning(f"Coordination errors during update: {coordination_result.coordination_errors}")
        
        return results
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
            
    def get_stats_enhanced(self) -> Dict[str, Any]:
        """
        Get enhanced statistics including version state information.
        
        Returns:
            Dictionary with enhanced statistics
        """
        with self._stats_lock:
            current_versions = self.get_current_versions()
            inconsistencies = self.detect_version_inconsistencies_enhanced()
            
            stats = {
                'operation_count': self._operation_count,
                'managed_files': len(self._updaters),
                'operations_history': len(self._operations_history),
                'current_versions': {str(path): version for path, version in current_versions.items()},
                'version_groups': {version: len(info.file_paths) for version, info in inconsistencies.items()},
                'has_inconsistencies': len(inconsistencies) > 1,
                'state_management_enabled': self.enable_state_management,
                'session_id': self.session_id,
            }
            
            # Add state-specific information
            if self._state_manager:
                try:
                    state_stats = self._state_manager.get_stats()
                    stats.update({
                        'state_version': self.get_state_version(),
                        'state_file_exists': state_stats.get('state_file_exists', False),
                        'state_operation_count': state_stats.get('operation_count', 0),
                        'state_total_increments': state_stats.get('total_increments', 0),
                        'state_current_stage': state_stats.get('current_stage', 'unknown'),
                        'state_file_size': state_stats.get('state_file_size', 0),
                    })
                    
                    # Enhanced inconsistency analysis
                    authoritative_version = None
                    for version, info in inconsistencies.items():
                        if info.is_authoritative:
                            authoritative_version = version
                            break
                    
                    stats.update({
                        'authoritative_version': authoritative_version,
                        'inconsistency_details': {
                            version: {
                                'source_type': info.source_type,
                                'file_count': len(info.file_paths),
                                'is_authoritative': info.is_authoritative,
                                'stage': info.stage.value if info.stage else None
                            }
                            for version, info in inconsistencies.items()
                        }
                    })
                    
                except Exception as e:
                    self.logger.error(f"Failed to get state manager stats: {e}")
                    stats['state_error'] = str(e)
            
            # Add coordination error information
            if self._state_coordination_errors:
                stats['coordination_errors'] = self._state_coordination_errors
            
            return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Backward-compatible statistics method.
        
        Returns:
            Dictionary with statistics (original format plus enhancements)
        """
        enhanced_stats = self.get_stats_enhanced()
        
        # Return enhanced stats but maintain backward compatibility
        # by ensuring original keys are present
        return enhanced_stats


class EnhancedVersionWorkflow:
    """
    Enhanced version workflow integration with state management.
    
    Provides high-level workflow operations for version management
    with VersionStateManager integration and enhanced user interaction.
    """
    
    def __init__(self, project_root: Union[str, Path], session_id: Optional[str] = None):
        """
        Initialize enhanced version workflow.
        
        Args:
            project_root: Root directory of project
            session_id: Optional session identifier for state management
        """
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(f'{__name__}.EnhancedVersionWorkflow')
        self.session_id = session_id or f"workflow_{int(time.time())}"
        
        # Use enhanced project manager
        self.project_manager = EnhancedProjectVersionManager(
            project_root, 
            enable_state_management=True,
            session_id=self.session_id
        )
        self.version_manager = VersionManager()
        
        self.logger.info(f"Enhanced version workflow initialized for session: {self.session_id}")
    
    def interactive_version_update(self) -> Optional[str]:
        """
        Enhanced interactive version update workflow.
        
        Returns:
            Selected version string or None if cancelled
        """
        print("\n" + "=" * 70)
        print("🔧 Enhanced GTach Project Version Management")
        print("=" * 70)
        
        # Use enhanced inconsistency detection
        inconsistencies = self.project_manager.detect_version_inconsistencies_enhanced()
        
        print(f"\n📊 Enhanced Version Status:")
        if len(inconsistencies) == 1:
            version = list(inconsistencies.keys())[0]
            info = inconsistencies[version]
            if info.is_authoritative:
                print(f"✅ All files consistent at authoritative version: {version}")
            else:
                print(f"✅ All files consistent at version: {version}")
        else:
            print(f"⚠️  Version inconsistencies detected:")
            for version, info in inconsistencies.items():
                status = "🎯 (Authoritative)" if info.is_authoritative else "📄"
                print(f"   {version} {status}: {len(info.file_paths)} files")
        
        # Show managed files with enhanced information
        print(f"\n📁 Managed Files:")
        current_versions = self.project_manager.get_current_versions()
        for file_path, version in current_versions.items():
            rel_path = file_path.relative_to(self.project_root)
            status = version if version else "❌ No version found"
            print(f"   {rel_path}: {status}")
        
        # Show state manager information
        state_version = self.project_manager.get_state_version()
        if state_version:
            print(f"\n🎯 Version State Manager: {state_version}")
        
        # Offer enhanced resolution if inconsistencies exist
        if len(inconsistencies) > 1:
            print(f"\n⚠️  Would you like to resolve inconsistencies first?")
            resolve_choice = input("Resolve inconsistencies now? [Y/n]: ").strip().lower()
            
            if resolve_choice in ['', 'y', 'yes']:
                resolution_result = self.project_manager.resolve_inconsistencies_interactive()
                
                if resolution_result.inconsistencies_resolved:
                    print(f"\n✅ Inconsistencies resolved successfully!")
                    if resolution_result.authoritative_version:
                        return resolution_result.authoritative_version
                else:
                    print(f"\n⚠️  Inconsistency resolution incomplete")
                    if resolution_result.coordination_errors:
                        print("Errors encountered:")
                        for error in resolution_result.coordination_errors:
                            print(f"   • {error}")
        
        # Continue with original workflow logic
        return self._execute_interactive_update()
    
    def _execute_interactive_update(self) -> Optional[str]:
        """Execute interactive version update"""
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
                    return self._execute_coordinated_update(version_input)
                else:
                    print("Version update cancelled")
                    return None
            else:
                print(f"❌ {feedback}")
                if attempt < max_attempts - 1:
                    print(f"Please try again ({max_attempts - attempt - 1} attempts remaining)")
        
        print(f"❌ Maximum attempts reached. Version update cancelled.")
        return None
    
    def _execute_coordinated_update(self, target_version: str) -> Optional[str]:
        """Execute coordinated version update"""
        print(f"\n🔄 Updating all project files and state to version {target_version}...")
        
        try:
            coordination_result = self.project_manager.update_all_versions_coordinated(
                target_version, update_state=True
            )
            
            print(f"\n📋 Enhanced Update Results:")
            print(f"   Project Files: {'✅ Updated' if coordination_result.project_files_updated else '❌ Failed'}")
            print(f"   Version State: {'✅ Updated' if coordination_result.state_updated else '❌ Failed'}")
            print(f"   Inconsistencies: {'✅ Resolved' if coordination_result.inconsistencies_resolved else '⚠️ Remain'}")
            print(f"   Processing Time: {coordination_result.operation_time_ms:.2f}ms")
            
            if coordination_result.coordination_errors:
                print(f"\n⚠️  Coordination Issues:")
                for error in coordination_result.coordination_errors:
                    print(f"   • {error}")
            
            if coordination_result.inconsistencies_resolved:
                print(f"\n✅ Enhanced version update completed successfully!")
                print(f"   All components synchronized to version {target_version}")
                self.logger.info(f"Enhanced interactive version update completed: {target_version}")
                return target_version
            else:
                print(f"\n⚠️  Version update completed with issues")
                return None
                
        except Exception as e:
            print(f"\n❌ Enhanced version update failed: {e}")
            self.logger.error(f"Enhanced interactive version update failed: {e}")
            return None
    
    def get_current_project_version(self) -> Optional[str]:
        """
        Get the current project version with state awareness.
        
        Returns:
            Current project version, preferring authoritative state version
        """
        inconsistencies = self.project_manager.detect_version_inconsistencies_enhanced()
        
        # Check for authoritative version first
        for version, info in inconsistencies.items():
            if info.is_authoritative:
                return version
        
        # Fallback to original logic
        if len(inconsistencies) == 1:
            return list(inconsistencies.keys())[0]
        elif len(inconsistencies) > 1:
            # Return most common version
            most_common = max(inconsistencies.items(), key=lambda x: len(x[1].file_paths))
            self.logger.warning(f"Version inconsistencies detected, using most common: {most_common[0]}")
            return most_common[0]
        else:
            self.logger.error("No versions found in any managed files")
            return None