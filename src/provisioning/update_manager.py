#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Update Manager for GTach Application Provisioning System

Provides safe in-place package updates with rollback mechanisms, validation
procedures, and deployment safety. Implements staged update process with
comprehensive backup/restore capabilities and thread-safe operations.

Features:
- Staged update process with validation checkpoints
- Automatic backup creation and rollback on failure
- Update conflict detection and resolution
- Cross-platform update compatibility
- Thread-safe operations with Protocol 8 compliant logging
- Integration with PackageRepository and VersionManager
"""

import os
import shutil
import tempfile
import tarfile
import json
import hashlib
import logging
import threading
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
from enum import Enum, auto

# Import existing utilities following project structure
try:
    # Try relative imports first
    from ..obdii.utils.platform import get_platform_type, PlatformType
    from ..obdii.utils.config import ConfigManager
    from .package_repository import PackageRepository, PackageEntry, SearchQuery
    from .version_manager import VersionManager, Version, CompatibilityLevel
    from .package_creator import PackageManifest
except ImportError:
    # Fallback for development/testing
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from obdii.utils.platform import get_platform_type, PlatformType
    from obdii.utils.config import ConfigManager
    sys.path.append(str(Path(__file__).parent))
    from package_repository import PackageRepository, PackageEntry, SearchQuery
    from version_manager import VersionManager, Version, CompatibilityLevel
    from package_creator import PackageManifest


class UpdateStage(Enum):
    """Update process stages for staged deployment"""
    INITIALIZED = auto()
    VALIDATING_TARGET = auto()
    CREATING_BACKUP = auto()
    DOWNLOADING_PACKAGE = auto()
    VALIDATING_PACKAGE = auto()
    CHECKING_CONFLICTS = auto()
    APPLYING_UPDATE = auto()
    VALIDATING_UPDATE = auto()
    CLEANUP = auto()
    COMPLETED = auto()
    ROLLING_BACK = auto()
    ROLLBACK_COMPLETED = auto()
    FAILED = auto()


class UpdateResult(Enum):
    """Update operation results"""
    SUCCESS = auto()
    FAILED_VALIDATION = auto()
    FAILED_CONFLICTS = auto()
    FAILED_APPLICATION = auto()
    ROLLED_BACK = auto()
    CANCELLED = auto()


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    ABORT = auto()
    OVERWRITE = auto()
    BACKUP_AND_OVERWRITE = auto()
    MERGE = auto()
    SKIP = auto()


@dataclass
class UpdateConflict:
    """Represents a file conflict during update"""
    file_path: str
    conflict_type: str  # "modified", "missing", "permission", "locked"
    current_checksum: Optional[str] = None
    expected_checksum: Optional[str] = None
    suggested_resolution: ConflictResolution = ConflictResolution.ABORT
    details: Optional[str] = None


@dataclass
class ValidationResult:
    """Results from validation procedures"""
    stage: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BackupInfo:
    """Information about created backups"""
    backup_id: str
    created_at: str
    original_path: str
    backup_path: str
    package_name: str
    package_version: str
    file_count: int
    total_size: int
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'backup_id': self.backup_id,
            'created_at': self.created_at,
            'original_path': self.original_path,
            'backup_path': self.backup_path,
            'package_name': self.package_name,
            'package_version': self.package_version,
            'file_count': self.file_count,
            'total_size': self.total_size,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        """Create instance from dictionary"""
        return cls(**data)


@dataclass
class UpdateOperation:
    """Represents an update operation in progress"""
    operation_id: str
    package_name: str
    current_version: str
    target_version: str
    target_platform: str
    stage: UpdateStage
    started_at: str
    backup_info: Optional[BackupInfo] = None
    conflicts: List[UpdateConflict] = field(default_factory=list)
    validations: List[ValidationResult] = field(default_factory=list)
    progress: float = 0.0
    error_message: Optional[str] = None
    rollback_attempted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'operation_id': self.operation_id,
            'package_name': self.package_name,
            'current_version': self.current_version,
            'target_version': self.target_version,
            'target_platform': self.target_platform,
            'stage': self.stage.name,
            'started_at': self.started_at,
            'backup_info': self.backup_info.to_dict() if self.backup_info else None,
            'conflicts': [
                {
                    'file_path': c.file_path,
                    'conflict_type': c.conflict_type,
                    'current_checksum': c.current_checksum,
                    'expected_checksum': c.expected_checksum,
                    'suggested_resolution': c.suggested_resolution.name,
                    'details': c.details
                }
                for c in self.conflicts
            ],
            'validations': [
                {
                    'stage': v.stage,
                    'success': v.success,
                    'message': v.message,
                    'details': v.details,
                    'timestamp': v.timestamp
                }
                for v in self.validations
            ],
            'progress': self.progress,
            'error_message': self.error_message,
            'rollback_attempted': self.rollback_attempted
        }


@dataclass
class UpdateConfig:
    """Configuration for update operations"""
    # Backup settings
    create_backups: bool = True
    backup_retention_days: int = 30
    backup_location: Optional[str] = None
    
    # Validation settings
    validate_checksums: bool = True
    validate_dependencies: bool = True
    validate_compatibility: bool = True
    run_post_update_tests: bool = True
    
    # Conflict resolution settings
    default_conflict_resolution: ConflictResolution = ConflictResolution.ABORT
    allow_automatic_resolution: bool = False
    conflict_timeout_seconds: int = 300
    
    # Rollback settings
    auto_rollback_on_failure: bool = True
    rollback_timeout_seconds: int = 600
    preserve_logs_on_rollback: bool = True
    
    # Performance settings
    concurrent_file_operations: int = 4
    chunk_size: int = 8192
    progress_callback: Optional[Callable[[str, float], None]] = None
    
    # Platform settings
    target_directory: Optional[str] = None
    preserve_permissions: bool = True
    cross_platform_compatibility: bool = True


class UpdateManager:
    """
    Thread-safe update manager for GTach application provisioning.
    
    Provides safe in-place package updates with comprehensive rollback
    mechanisms, validation procedures, and deployment safety following
    Protocol standards for logging and cross-platform compatibility.
    """
    
    DEFAULT_UPDATE_DIR = Path.home() / ".gtach" / "updates"
    DEFAULT_BACKUP_DIR = Path.home() / ".gtach" / "backups"
    
    def __init__(self, 
                 repository: Optional[PackageRepository] = None,
                 update_config: Optional[UpdateConfig] = None,
                 target_directory: Optional[Union[str, Path]] = None):
        """
        Initialize UpdateManager with thread-safe operations.
        
        Args:
            repository: Optional PackageRepository instance
            update_config: Optional UpdateConfig for operation customization
            target_directory: Optional target directory for updates
        """
        # Session-based logging per Protocol 8
        self.logger = logging.getLogger(f'{__name__}.UpdateManager')
        
        # Repository integration
        self.repository = repository or PackageRepository()
        
        # Version manager integration
        self.version_manager = VersionManager()
        
        # Configuration setup
        self.config = update_config or UpdateConfig()
        
        # Directory setup with cross-platform compatibility per Protocol 6
        self.update_dir = self.DEFAULT_UPDATE_DIR
        self.backup_dir = Path(self.config.backup_location) if self.config.backup_location else self.DEFAULT_BACKUP_DIR
        
        if target_directory:
            self.target_directory = Path(target_directory)
        else:
            # Auto-detect target directory based on platform
            platform = get_platform_type()
            if platform == PlatformType.RASPBERRY_PI:
                self.target_directory = Path("/opt/gtach")
            else:
                self.target_directory = Path.home() / ".local" / "gtach"
        
        # Thread safety per Protocol 8
        self._update_lock = threading.RLock()
        self._operations_lock = threading.Lock()
        self._active_operations: Dict[str, UpdateOperation] = {}
        self._operation_count = 0
        self._stats_lock = threading.Lock()
        
        # Platform detection per Protocol 6
        self.source_platform = get_platform_type()
        
        # Configuration manager integration
        self.config_manager = ConfigManager()
        
        # Initialize directory structure
        self._initialize_directories()
        
        self.logger.info(f"UpdateManager initialized - Target: {self.target_directory}")
        self.logger.debug(f"Source platform: {self.source_platform.name}, Backup dir: {self.backup_dir}")
    
    def _initialize_directories(self) -> None:
        """Initialize update and backup directory structure"""
        try:
            # Create directory structure
            self.update_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            (self.backup_dir / "active").mkdir(exist_ok=True)
            (self.backup_dir / "archived").mkdir(exist_ok=True)
            
            # Create target directory if it doesn't exist
            if not self.target_directory.exists():
                self.logger.info(f"Creating target directory: {self.target_directory}")
                self.target_directory.mkdir(parents=True, exist_ok=True)
            
            self.logger.debug(f"Directory structure initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize directory structure: {e}")
            raise RuntimeError(f"Directory initialization failed: {e}") from e
    
    def start_update(self,
                     package_name: str,
                     target_version: str,
                     target_platform: Optional[str] = None,
                     conflict_resolver: Optional[Callable[[List[UpdateConflict]], Dict[str, ConflictResolution]]] = None) -> str:
        """
        Start a staged update operation.
        
        Args:
            package_name: Name of package to update
            target_version: Target version to update to
            target_platform: Target platform (auto-detected if None)
            conflict_resolver: Optional conflict resolution callback
            
        Returns:
            Operation ID for tracking the update
            
        Raises:
            RuntimeError: If update cannot be started
            ValueError: If parameters are invalid
        """
        with self._update_lock:
            self._increment_operation_count()
            
            if target_platform is None:
                target_platform = self.source_platform.name.lower().replace('_', '-')
            
            # Validate inputs
            if not package_name:
                raise ValueError("Package name cannot be empty")
            
            try:
                self.version_manager.parse_version(target_version)
            except ValueError as e:
                raise ValueError(f"Invalid target version '{target_version}': {e}") from e
            
            # Generate operation ID
            operation_id = f"update_{package_name}_{target_version}_{int(time.time())}"
            
            # Check if package currently exists and get current version
            current_version = self._detect_current_version(package_name)
            
            # Create update operation
            operation = UpdateOperation(
                operation_id=operation_id,
                package_name=package_name,
                current_version=current_version or "0.0.0",
                target_version=target_version,
                target_platform=target_platform,
                stage=UpdateStage.INITIALIZED,
                started_at=datetime.now().isoformat()
            )
            
            self._active_operations[operation_id] = operation
            
            self.logger.info(f"Started update operation: {package_name} {current_version} -> {target_version} (ID: {operation_id})")
            
            # Start update process in background
            try:
                self._execute_staged_update(operation, conflict_resolver)
                return operation_id
                
            except Exception as e:
                operation.stage = UpdateStage.FAILED
                operation.error_message = str(e)
                self.logger.error(f"Update operation {operation_id} failed during startup: {e}")
                raise RuntimeError(f"Update startup failed: {e}") from e
    
    def _detect_current_version(self, package_name: str) -> Optional[str]:
        """
        Detect current installed version of package.
        
        Args:
            package_name: Name of package to check
            
        Returns:
            Current version string or None if not installed
        """
        try:
            # Check for version file in target directory
            version_file = self.target_directory / "version.json"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                    if version_data.get('package_name') == package_name:
                        return version_data.get('version')
            
            # Check for package manifest
            manifest_file = self.target_directory / "manifest.json"
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest_data = json.load(f)
                    if manifest_data.get('package_name') == package_name:
                        return manifest_data.get('version')
            
            # Try to detect from directory structure
            if (self.target_directory / package_name).exists():
                # Package directory exists but no version info
                return "unknown"
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to detect current version for {package_name}: {e}")
            return "unknown"
    
    def _execute_staged_update(self,
                              operation: UpdateOperation,
                              conflict_resolver: Optional[Callable[[List[UpdateConflict]], Dict[str, ConflictResolution]]] = None) -> None:
        """
        Execute the staged update process.
        
        Args:
            operation: Update operation to execute
            conflict_resolver: Optional conflict resolution callback
        """
        try:
            # Stage 1: Validate target package
            self._update_stage(operation, UpdateStage.VALIDATING_TARGET, 10.0)
            target_package = self._validate_target_package(operation)
            
            # Stage 2: Create backup
            self._update_stage(operation, UpdateStage.CREATING_BACKUP, 20.0)
            if self.config.create_backups and operation.current_version != "0.0.0":
                operation.backup_info = self._create_backup(operation)
            
            # Stage 3: Download/retrieve package
            self._update_stage(operation, UpdateStage.DOWNLOADING_PACKAGE, 30.0)
            package_path = self._retrieve_package(operation, target_package)
            
            # Stage 4: Validate package integrity
            self._update_stage(operation, UpdateStage.VALIDATING_PACKAGE, 40.0)
            self._validate_package_integrity(operation, package_path, target_package)
            
            # Stage 5: Check for conflicts
            self._update_stage(operation, UpdateStage.CHECKING_CONFLICTS, 50.0)
            conflicts = self._check_update_conflicts(operation, package_path)
            if conflicts:
                operation.conflicts = conflicts
                if not self._resolve_conflicts(operation, conflicts, conflict_resolver):
                    raise RuntimeError("Update conflicts could not be resolved")
            
            # Stage 6: Apply update
            self._update_stage(operation, UpdateStage.APPLYING_UPDATE, 70.0)
            self._apply_update(operation, package_path)
            
            # Stage 7: Validate update
            self._update_stage(operation, UpdateStage.VALIDATING_UPDATE, 85.0)
            self._validate_applied_update(operation)
            
            # Stage 8: Cleanup
            self._update_stage(operation, UpdateStage.CLEANUP, 95.0)
            self._cleanup_update_files(operation, package_path)
            
            # Stage 9: Complete
            self._update_stage(operation, UpdateStage.COMPLETED, 100.0)
            
            self.logger.info(f"Update operation {operation.operation_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Update operation {operation.operation_id} failed at stage {operation.stage.name}: {e}")
            operation.error_message = str(e)
            
            # Attempt automatic rollback if configured
            if self.config.auto_rollback_on_failure and operation.backup_info:
                try:
                    self._rollback_update(operation)
                except Exception as rollback_error:
                    self.logger.critical(f"Rollback failed for operation {operation.operation_id}: {rollback_error}")
                    operation.stage = UpdateStage.FAILED
            else:
                operation.stage = UpdateStage.FAILED
            
            # Re-raise the original exception
            raise
    
    def _update_stage(self, operation: UpdateOperation, stage: UpdateStage, progress: float) -> None:
        """
        Update operation stage and progress.
        
        Args:
            operation: Update operation
            stage: New stage
            progress: Progress percentage (0-100)
        """
        operation.stage = stage
        operation.progress = progress
        
        if self.config.progress_callback:
            try:
                self.config.progress_callback(operation.operation_id, progress)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
        
        self.logger.debug(f"Operation {operation.operation_id} stage: {stage.name} ({progress:.1f}%)")
    
    def _validate_target_package(self, operation: UpdateOperation) -> PackageEntry:
        """
        Validate that target package exists and is compatible.
        
        Args:
            operation: Update operation
            
        Returns:
            Target package entry
            
        Raises:
            RuntimeError: If validation fails
        """
        try:
            # Search for target package
            query = SearchQuery(
                name=operation.package_name,
                version=operation.target_version,
                platform=operation.target_platform
            )
            
            packages = self.repository.search_packages(query)
            if not packages:
                raise RuntimeError(f"Target package not found: {operation.package_name} v{operation.target_version} ({operation.target_platform})")
            
            target_package = packages[0]
            
            # Check version compatibility if current version is known
            if operation.current_version != "0.0.0" and operation.current_version != "unknown":
                compatibility = self.version_manager.check_compatibility(
                    operation.current_version, operation.target_version
                )
                
                validation = ValidationResult(
                    stage="target_validation",
                    success=True,
                    message=f"Version compatibility: {compatibility.name.lower().replace('_', ' ')}",
                    details={
                        "current_version": operation.current_version,
                        "target_version": operation.target_version,
                        "compatibility_level": compatibility.name
                    }
                )
                operation.validations.append(validation)
                
                self.logger.debug(f"Version compatibility check: {operation.current_version} -> {operation.target_version} = {compatibility.name}")
            
            return target_package
            
        except Exception as e:
            validation = ValidationResult(
                stage="target_validation",
                success=False,
                message=f"Target validation failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            raise RuntimeError(f"Target package validation failed: {e}") from e
    
    def _create_backup(self, operation: UpdateOperation) -> BackupInfo:
        """
        Create backup of current installation.
        
        Args:
            operation: Update operation
            
        Returns:
            Backup information
            
        Raises:
            RuntimeError: If backup creation fails
        """
        try:
            backup_id = f"backup_{operation.package_name}_{operation.current_version}_{int(time.time())}"
            backup_path = self.backup_dir / "active" / f"{backup_id}.tar.gz"
            
            self.logger.info(f"Creating backup: {backup_id}")
            
            # Create backup archive
            file_count = 0
            total_size = 0
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                for item in self.target_directory.rglob('*'):
                    if item.is_file():
                        try:
                            arcname = item.relative_to(self.target_directory)
                            tar.add(item, arcname=arcname)
                            file_count += 1
                            total_size += item.stat().st_size
                        except Exception as e:
                            self.logger.warning(f"Failed to backup file {item}: {e}")
            
            # Calculate backup checksum
            checksum = self._calculate_file_checksum(backup_path)
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id=backup_id,
                created_at=datetime.now().isoformat(),
                original_path=str(self.target_directory),
                backup_path=str(backup_path),
                package_name=operation.package_name,
                package_version=operation.current_version,
                file_count=file_count,
                total_size=total_size,
                checksum=checksum
            )
            
            # Save backup metadata
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(backup_info.to_dict(), f, indent=2)
            
            validation = ValidationResult(
                stage="backup_creation",
                success=True,
                message=f"Backup created: {backup_id} ({file_count} files, {total_size:,} bytes)",
                details={
                    "backup_id": backup_id,
                    "file_count": file_count,
                    "total_size": total_size,
                    "checksum": checksum[:16] + "..."
                }
            )
            operation.validations.append(validation)
            
            self.logger.info(f"Backup created: {backup_id} ({file_count} files, {total_size:,} bytes)")
            
            return backup_info
            
        except Exception as e:
            validation = ValidationResult(
                stage="backup_creation",
                success=False,
                message=f"Backup creation failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            raise RuntimeError(f"Backup creation failed: {e}") from e
    
    def _retrieve_package(self, operation: UpdateOperation, target_package: PackageEntry) -> Path:
        """
        Retrieve package from repository.
        
        Args:
            operation: Update operation
            target_package: Target package entry
            
        Returns:
            Path to retrieved package file
            
        Raises:
            RuntimeError: If package retrieval fails
        """
        try:
            package_path = self.repository.retrieve_package(
                operation.package_name,
                operation.target_version,
                operation.target_platform
            )
            
            if not package_path or not package_path.exists():
                raise RuntimeError(f"Package file not found: {operation.package_name} v{operation.target_version}")
            
            validation = ValidationResult(
                stage="package_retrieval",
                success=True,
                message=f"Package retrieved: {package_path.name}",
                details={
                    "package_path": str(package_path),
                    "file_size": package_path.stat().st_size
                }
            )
            operation.validations.append(validation)
            
            self.logger.debug(f"Package retrieved: {package_path}")
            
            return package_path
            
        except Exception as e:
            validation = ValidationResult(
                stage="package_retrieval",
                success=False,
                message=f"Package retrieval failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            raise RuntimeError(f"Package retrieval failed: {e}") from e
    
    def _validate_package_integrity(self, operation: UpdateOperation, package_path: Path, target_package: PackageEntry) -> None:
        """
        Validate package integrity using checksums.
        
        Args:
            operation: Update operation
            package_path: Path to package file
            target_package: Expected package entry
            
        Raises:
            RuntimeError: If validation fails
        """
        try:
            if not self.config.validate_checksums:
                self.logger.debug("Checksum validation disabled by configuration")
                return
            
            # Calculate actual checksum
            actual_checksum = self._calculate_file_checksum(package_path)
            expected_checksum = target_package.checksum
            
            if actual_checksum != expected_checksum:
                raise RuntimeError(f"Package integrity check failed: checksum mismatch")
            
            # Verify package is a valid archive
            if not tarfile.is_tarfile(package_path):
                raise RuntimeError("Package file is not a valid tar archive")
            
            # Basic archive structure validation
            with tarfile.open(package_path, 'r:gz') as tar:
                members = tar.getmembers()
                if not members:
                    raise RuntimeError("Package archive is empty")
                
                # Check for manifest
                manifest_found = any(m.name == 'manifest.json' for m in members)
                if not manifest_found:
                    self.logger.warning("Package manifest not found - continuing anyway")
            
            validation = ValidationResult(
                stage="package_validation",
                success=True,
                message="Package integrity validated",
                details={
                    "expected_checksum": expected_checksum[:16] + "...",
                    "actual_checksum": actual_checksum[:16] + "...",
                    "archive_members": len(members) if 'members' in locals() else 0
                }
            )
            operation.validations.append(validation)
            
            self.logger.debug(f"Package integrity validated: {package_path.name}")
            
        except Exception as e:
            validation = ValidationResult(
                stage="package_validation",
                success=False,
                message=f"Package validation failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            raise RuntimeError(f"Package validation failed: {e}") from e
    
    def _check_update_conflicts(self, operation: UpdateOperation, package_path: Path) -> List[UpdateConflict]:
        """
        Check for potential update conflicts.
        
        Args:
            operation: Update operation
            package_path: Path to package file
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            # Extract package to temporary location for analysis
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract package
                with tarfile.open(package_path, 'r:gz') as tar:
                    tar.extractall(temp_path)
                
                # Check for file conflicts
                for item in temp_path.rglob('*'):
                    if item.is_file():
                        rel_path = item.relative_to(temp_path)
                        target_file = self.target_directory / rel_path
                        
                        if target_file.exists():
                            # File exists - check for modifications
                            try:
                                new_checksum = self._calculate_file_checksum(item)
                                current_checksum = self._calculate_file_checksum(target_file)
                                
                                if new_checksum != current_checksum:
                                    conflict = UpdateConflict(
                                        file_path=str(rel_path),
                                        conflict_type="modified",
                                        current_checksum=current_checksum,
                                        expected_checksum=new_checksum,
                                        suggested_resolution=ConflictResolution.BACKUP_AND_OVERWRITE,
                                        details="File has been modified since last update"
                                    )
                                    conflicts.append(conflict)
                                    
                            except Exception as e:
                                conflict = UpdateConflict(
                                    file_path=str(rel_path),
                                    conflict_type="permission",
                                    suggested_resolution=ConflictResolution.ABORT,
                                    details=f"Cannot access file: {e}"
                                )
                                conflicts.append(conflict)
                        
                        # Check if target directory is writable
                        elif not os.access(target_file.parent, os.W_OK):
                            conflict = UpdateConflict(
                                file_path=str(rel_path.parent),
                                conflict_type="permission",
                                suggested_resolution=ConflictResolution.ABORT,
                                details="Directory not writable"
                            )
                            conflicts.append(conflict)
            
            if conflicts:
                self.logger.warning(f"Detected {len(conflicts)} update conflicts")
                for conflict in conflicts:
                    self.logger.debug(f"Conflict: {conflict.file_path} ({conflict.conflict_type})")
            
            return conflicts
            
        except Exception as e:
            self.logger.error(f"Failed to check update conflicts: {e}")
            # Create a generic conflict to prevent update
            return [UpdateConflict(
                file_path="<unknown>",
                conflict_type="check_failed",
                suggested_resolution=ConflictResolution.ABORT,
                details=f"Conflict checking failed: {e}"
            )]
    
    def _resolve_conflicts(self,
                          operation: UpdateOperation,
                          conflicts: List[UpdateConflict],
                          conflict_resolver: Optional[Callable[[List[UpdateConflict]], Dict[str, ConflictResolution]]] = None) -> bool:
        """
        Resolve update conflicts.
        
        Args:
            operation: Update operation
            conflicts: List of conflicts to resolve
            conflict_resolver: Optional callback for conflict resolution
            
        Returns:
            True if all conflicts resolved, False otherwise
        """
        try:
            if conflict_resolver:
                # Use custom conflict resolver
                resolutions = conflict_resolver(conflicts)
            else:
                # Use default resolution strategy
                resolutions = {}
                for conflict in conflicts:
                    if self.config.allow_automatic_resolution:
                        resolutions[conflict.file_path] = conflict.suggested_resolution
                    else:
                        resolutions[conflict.file_path] = self.config.default_conflict_resolution
            
            # Check if any conflicts require aborting
            abort_conflicts = [
                path for path, resolution in resolutions.items()
                if resolution == ConflictResolution.ABORT
            ]
            
            if abort_conflicts:
                self.logger.error(f"Update aborted due to unresolvable conflicts: {abort_conflicts}")
                return False
            
            # Apply conflict resolutions
            for conflict in conflicts:
                resolution = resolutions.get(conflict.file_path, ConflictResolution.ABORT)
                if not self._apply_conflict_resolution(conflict, resolution):
                    return False
            
            validation = ValidationResult(
                stage="conflict_resolution",
                success=True,
                message=f"Resolved {len(conflicts)} conflicts",
                details={
                    "conflicts_resolved": len(conflicts),
                    "resolutions": {
                        path: resolution.name for path, resolution in resolutions.items()
                    }
                }
            )
            operation.validations.append(validation)
            
            return True
            
        except Exception as e:
            validation = ValidationResult(
                stage="conflict_resolution",
                success=False,
                message=f"Conflict resolution failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            self.logger.error(f"Conflict resolution failed: {e}")
            return False
    
    def _apply_conflict_resolution(self, conflict: UpdateConflict, resolution: ConflictResolution) -> bool:
        """
        Apply specific conflict resolution.
        
        Args:
            conflict: Conflict to resolve
            resolution: Resolution strategy
            
        Returns:
            True if resolution successful
        """
        try:
            target_file = self.target_directory / conflict.file_path
            
            if resolution == ConflictResolution.OVERWRITE:
                # Will be overwritten during update - no action needed
                self.logger.debug(f"Conflict {conflict.file_path}: will overwrite")
                return True
                
            elif resolution == ConflictResolution.BACKUP_AND_OVERWRITE:
                # Create backup of conflicting file
                if target_file.exists():
                    backup_name = f"{target_file.name}.backup.{int(time.time())}"
                    backup_file = target_file.parent / backup_name
                    shutil.copy2(target_file, backup_file)
                    self.logger.debug(f"Backed up conflicting file: {conflict.file_path} -> {backup_name}")
                return True
                
            elif resolution == ConflictResolution.SKIP:
                # Mark for skipping during update
                self.logger.debug(f"Conflict {conflict.file_path}: will skip")
                return True
                
            elif resolution == ConflictResolution.MERGE:
                # Merge not implemented for binary files
                self.logger.warning(f"Merge resolution not supported for {conflict.file_path}")
                return False
                
            else:  # ABORT
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to apply resolution for {conflict.file_path}: {e}")
            return False
    
    def _apply_update(self, operation: UpdateOperation, package_path: Path) -> None:
        """
        Apply the update to the target directory.
        
        Args:
            operation: Update operation
            package_path: Path to package file
            
        Raises:
            RuntimeError: If update application fails
        """
        try:
            self.logger.info(f"Applying update: {operation.package_name} v{operation.target_version}")
            
            # Extract package to target directory
            with tarfile.open(package_path, 'r:gz') as tar:
                # Filter out files that should be skipped due to conflicts
                skip_files = set()
                for conflict in operation.conflicts:
                    if any(res == ConflictResolution.SKIP 
                          for res in [conflict.suggested_resolution]):
                        skip_files.add(conflict.file_path)
                
                members = tar.getmembers()
                extracted_count = 0
                
                for member in members:
                    if member.name in skip_files:
                        self.logger.debug(f"Skipping file due to conflict: {member.name}")
                        continue
                    
                    try:
                        # Extract member to target directory
                        tar.extract(member, self.target_directory)
                        extracted_count += 1
                        
                        # Preserve permissions if configured
                        if self.config.preserve_permissions:
                            extracted_path = self.target_directory / member.name
                            if extracted_path.exists():
                                extracted_path.chmod(member.mode)
                                
                    except Exception as e:
                        self.logger.warning(f"Failed to extract {member.name}: {e}")
            
            # Update version information
            self._update_version_info(operation)
            
            validation = ValidationResult(
                stage="update_application",
                success=True,
                message=f"Update applied: {extracted_count} files extracted",
                details={
                    "extracted_files": extracted_count,
                    "skipped_files": len(skip_files),
                    "total_members": len(members)
                }
            )
            operation.validations.append(validation)
            
            self.logger.info(f"Update applied successfully: {extracted_count} files")
            
        except Exception as e:
            validation = ValidationResult(
                stage="update_application",
                success=False,
                message=f"Update application failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            raise RuntimeError(f"Update application failed: {e}") from e
    
    def _update_version_info(self, operation: UpdateOperation) -> None:
        """
        Update version information files.
        
        Args:
            operation: Update operation
        """
        try:
            # Create/update version.json
            version_info = {
                "package_name": operation.package_name,
                "version": operation.target_version,
                "platform": operation.target_platform,
                "updated_at": datetime.now().isoformat(),
                "previous_version": operation.current_version
            }
            
            version_file = self.target_directory / "version.json"
            with open(version_file, 'w') as f:
                json.dump(version_info, f, indent=2)
            
            self.logger.debug(f"Updated version info: {operation.target_version}")
            
        except Exception as e:
            self.logger.warning(f"Failed to update version info: {e}")
    
    def _validate_applied_update(self, operation: UpdateOperation) -> None:
        """
        Validate that the update was applied correctly.
        
        Args:
            operation: Update operation
            
        Raises:
            RuntimeError: If validation fails
        """
        try:
            validations_passed = 0
            total_validations = 0
            
            # Check version file exists and is correct
            total_validations += 1
            version_file = self.target_directory / "version.json"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                    if (version_data.get('package_name') == operation.package_name and
                        version_data.get('version') == operation.target_version):
                        validations_passed += 1
                        self.logger.debug("Version file validation passed")
                    else:
                        self.logger.warning("Version file validation failed: incorrect content")
            else:
                self.logger.warning("Version file validation failed: file not found")
            
            # Check manifest if it exists
            total_validations += 1
            manifest_file = self.target_directory / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifest_data = json.load(f)
                        if manifest_data.get('package_name') == operation.package_name:
                            validations_passed += 1
                            self.logger.debug("Manifest validation passed")
                        else:
                            self.logger.warning("Manifest validation failed: package name mismatch")
                except json.JSONDecodeError:
                    self.logger.warning("Manifest validation failed: invalid JSON")
            else:
                # Manifest might not exist - count as passed
                validations_passed += 1
            
            # Run post-update tests if configured
            if self.config.run_post_update_tests:
                total_validations += 1
                if self._run_post_update_tests(operation):
                    validations_passed += 1
            
            # Overall validation result - require at least 50% pass rate or 2 validations minimum
            min_required = max(2, int(total_validations * 0.5))
            validation_success = validations_passed >= min_required
            
            if not validation_success:
                raise RuntimeError(f"Update validation failed: {validations_passed}/{total_validations} checks passed (minimum {min_required} required)")
            
            validation = ValidationResult(
                stage="update_validation",
                success=True,
                message=f"Update validation passed: {validations_passed}/{total_validations} checks",
                details={
                    "validations_passed": validations_passed,
                    "total_validations": total_validations,
                    "pass_rate": (validations_passed / total_validations) * 100
                }
            )
            operation.validations.append(validation)
            
            self.logger.debug(f"Update validation passed: {validations_passed}/{total_validations}")
            
        except Exception as e:
            validation = ValidationResult(
                stage="update_validation",
                success=False,
                message=f"Update validation failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            raise RuntimeError(f"Update validation failed: {e}") from e
    
    def _run_post_update_tests(self, operation: UpdateOperation) -> bool:
        """
        Run post-update tests to validate functionality.
        
        Args:
            operation: Update operation
            
        Returns:
            True if tests pass
        """
        try:
            # Basic functionality tests
            test_results = []
            
            # Test 1: Check if main executable/script exists
            main_files = [
                self.target_directory / "main.py",
                self.target_directory / f"{operation.package_name}.py",
                self.target_directory / "app.py"
            ]
            
            main_file_found = any(f.exists() for f in main_files)
            test_results.append(("main_file_exists", main_file_found))
            
            # Test 2: Check directory structure
            expected_dirs = ["src", "config", "scripts"]
            dir_structure_ok = any(
                (self.target_directory / d).exists() for d in expected_dirs
            )
            test_results.append(("directory_structure", dir_structure_ok))
            
            # Test 3: Check permissions
            permissions_ok = os.access(self.target_directory, os.R_OK | os.W_OK)
            test_results.append(("permissions", permissions_ok))
            
            # Calculate test results
            passed_tests = sum(1 for _, result in test_results if result)
            total_tests = len(test_results)
            
            self.logger.debug(f"Post-update tests: {passed_tests}/{total_tests} passed")
            
            return passed_tests >= (total_tests * 0.7)  # 70% pass rate
            
        except Exception as e:
            self.logger.warning(f"Post-update tests failed: {e}")
            return False
    
    def _cleanup_update_files(self, operation: UpdateOperation, package_path: Path) -> None:
        """
        Clean up temporary files created during update.
        
        Args:
            operation: Update operation
            package_path: Path to package file
        """
        try:
            # Package file is from repository - don't delete it
            # Clean up any temporary extraction directories (handled by context managers)
            
            validation = ValidationResult(
                stage="cleanup",
                success=True,
                message="Cleanup completed",
                details={"cleaned_files": 0}
            )
            operation.validations.append(validation)
            
            self.logger.debug("Update cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
    
    def _rollback_update(self, operation: UpdateOperation) -> None:
        """
        Rollback update using backup.
        
        Args:
            operation: Update operation
            
        Raises:
            RuntimeError: If rollback fails
        """
        if not operation.backup_info:
            raise RuntimeError("No backup available for rollback")
        
        try:
            operation.rollback_attempted = True
            self._update_stage(operation, UpdateStage.ROLLING_BACK, 0.0)
            
            self.logger.warning(f"Starting rollback for operation {operation.operation_id}")
            
            # Verify backup exists
            backup_path = Path(operation.backup_info.backup_path)
            if not backup_path.exists():
                raise RuntimeError(f"Backup file not found: {backup_path}")
            
            # Verify backup integrity
            actual_checksum = self._calculate_file_checksum(backup_path)
            if actual_checksum != operation.backup_info.checksum:
                raise RuntimeError("Backup file integrity check failed")
            
            # Clear target directory
            if self.target_directory.exists():
                for item in self.target_directory.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            
            # Restore from backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(self.target_directory)
            
            operation.stage = UpdateStage.ROLLBACK_COMPLETED
            
            validation = ValidationResult(
                stage="rollback",
                success=True,
                message=f"Rollback completed using backup {operation.backup_info.backup_id}",
                details={
                    "backup_id": operation.backup_info.backup_id,
                    "restored_files": operation.backup_info.file_count
                }
            )
            operation.validations.append(validation)
            
            self.logger.info(f"Rollback completed for operation {operation.operation_id}")
            
        except Exception as e:
            validation = ValidationResult(
                stage="rollback",
                success=False,
                message=f"Rollback failed: {e}",
                details={"error": str(e)}
            )
            operation.validations.append(validation)
            
            self.logger.critical(f"Rollback failed for operation {operation.operation_id}: {e}")
            raise RuntimeError(f"Rollback failed: {e}") from e
    
    def get_update_status(self, operation_id: str) -> Optional[UpdateOperation]:
        """
        Get current status of update operation.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            UpdateOperation or None if not found
        """
        with self._operations_lock:
            return self._active_operations.get(operation_id)
    
    def cancel_update(self, operation_id: str, force_rollback: bool = False) -> bool:
        """
        Cancel an in-progress update operation.
        
        Args:
            operation_id: Operation ID to cancel
            force_rollback: Whether to force rollback if update partially applied
            
        Returns:
            True if cancelled successfully
        """
        with self._update_lock:
            operation = self._active_operations.get(operation_id)
            if not operation:
                return False
            
            try:
                if operation.stage in [UpdateStage.COMPLETED, UpdateStage.ROLLBACK_COMPLETED, UpdateStage.FAILED]:
                    # Already finished
                    return False
                
                self.logger.info(f"Cancelling update operation: {operation_id}")
                
                # If update was partially applied and backup exists, offer rollback
                if (force_rollback and 
                    operation.stage.value >= UpdateStage.APPLYING_UPDATE.value and
                    operation.backup_info):
                    try:
                        self._rollback_update(operation)
                    except Exception as e:
                        self.logger.error(f"Rollback during cancellation failed: {e}")
                        operation.stage = UpdateStage.FAILED
                        operation.error_message = f"Cancellation rollback failed: {e}"
                        return False
                
                # Mark as cancelled
                operation.stage = UpdateStage.FAILED
                operation.error_message = "Operation cancelled by user"
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to cancel operation {operation_id}: {e}")
                return False
    
    def list_backups(self, package_name: Optional[str] = None, max_age_days: Optional[int] = None) -> List[BackupInfo]:
        """
        List available backups.
        
        Args:
            package_name: Optional package name filter
            max_age_days: Optional maximum age in days
            
        Returns:
            List of backup information
        """
        backups = []
        
        try:
            # Use rglob to recursively find backup metadata files
            for metadata_file in self.backup_dir.rglob("backup_*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        backup_data = json.load(f)
                        backup_info = BackupInfo.from_dict(backup_data)
                    
                    # Apply filters
                    if package_name and backup_info.package_name != package_name:
                        continue
                    
                    if max_age_days:
                        backup_age = datetime.now() - datetime.fromisoformat(backup_info.created_at)
                        if backup_age.days > max_age_days:
                            continue
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load backup metadata {metadata_file}: {e}")
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda b: b.created_at, reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []
    
    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> int:
        """
        Clean up old backup files.
        
        Args:
            retention_days: Days to retain backups (uses config default if None)
            
        Returns:
            Number of backups cleaned up
        """
        if retention_days is None:
            retention_days = self.config.backup_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cleaned_count = 0
        
        try:
            # Use rglob to recursively find backup metadata files
            for metadata_file in self.backup_dir.rglob("backup_*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        backup_data = json.load(f)
                    
                    created_at = datetime.fromisoformat(backup_data['created_at'])
                    if created_at < cutoff_date:
                        # Remove backup files
                        backup_path = Path(backup_data['backup_path'])
                        if backup_path.exists():
                            backup_path.unlink()
                        metadata_file.unlink()
                        cleaned_count += 1
                        
                        self.logger.debug(f"Cleaned up old backup: {backup_data['backup_id']}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup backup {metadata_file}: {e}")
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old backups")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
            return 0
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA256 checksum of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hexadecimal checksum string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(self.config.chunk_size), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get update manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._stats_lock:
            # Count backups
            backup_count = len(list(self.backup_dir.rglob("backup_*.json")))
            
            # Calculate backup storage usage
            backup_size = sum(
                f.stat().st_size for f in self.backup_dir.rglob("backup_*.tar.gz")
                if f.exists()
            )
            
            return {
                'operation_count': self._operation_count,
                'active_operations': len(self._active_operations),
                'target_directory': str(self.target_directory),
                'backup_directory': str(self.backup_dir),
                'total_backups': backup_count,
                'backup_storage_bytes': backup_size,
                'repository_stats': self.repository.get_operation_stats(),
                'version_manager_stats': self.version_manager.get_stats()
            }