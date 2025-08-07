#!/usr/bin/env python3
"""
Unit tests for UpdateManager

Tests update manager functionality including:
- Staged update process execution
- Backup creation and rollback mechanisms
- Update conflict detection and resolution
- Validation procedures and integrity checks
- Thread safety and error handling
- Cross-platform update compatibility
"""

import os
import sys
import unittest
import tempfile
import shutil
import threading
import time
import json
import tarfile
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from provisioning.update_manager import (
    UpdateManager, UpdateStage, UpdateResult, ConflictResolution,
    UpdateConflict, ValidationResult, BackupInfo, UpdateOperation, UpdateConfig
)
from provisioning.package_repository import PackageRepository, PackageEntry
from provisioning.package_creator import PackageManifest
from provisioning.version_manager import VersionManager, CompatibilityLevel


class TestUpdateConflict(unittest.TestCase):
    """Test UpdateConflict functionality"""
    
    def test_conflict_creation(self):
        """Test creating update conflict"""
        conflict = UpdateConflict(
            file_path="test/file.py",
            conflict_type="modified",
            current_checksum="abc123",
            expected_checksum="def456",
            suggested_resolution=ConflictResolution.BACKUP_AND_OVERWRITE,
            details="File modified locally"
        )
        
        self.assertEqual(conflict.file_path, "test/file.py")
        self.assertEqual(conflict.conflict_type, "modified")
        self.assertEqual(conflict.current_checksum, "abc123")
        self.assertEqual(conflict.expected_checksum, "def456")
        self.assertEqual(conflict.suggested_resolution, ConflictResolution.BACKUP_AND_OVERWRITE)
        self.assertEqual(conflict.details, "File modified locally")


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult functionality"""
    
    def test_validation_result_creation(self):
        """Test creating validation result"""
        result = ValidationResult(
            stage="package_validation",
            success=True,
            message="Package integrity validated",
            details={"checksum": "abc123"}
        )
        
        self.assertEqual(result.stage, "package_validation")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Package integrity validated")
        self.assertEqual(result.details, {"checksum": "abc123"})
        self.assertIsNotNone(result.timestamp)


class TestBackupInfo(unittest.TestCase):
    """Test BackupInfo functionality"""
    
    def test_backup_info_serialization(self):
        """Test backup info to/from dict conversion"""
        backup_info = BackupInfo(
            backup_id="backup_test_1_0_0_123456",
            created_at="2023-01-01T00:00:00",
            original_path="/opt/test",
            backup_path="/backups/backup_test_1_0_0_123456.tar.gz",
            package_name="test",
            package_version="1.0.0",
            file_count=10,
            total_size=1024,
            checksum="abc123"
        )
        
        # Test to_dict
        data = backup_info.to_dict()
        self.assertEqual(data['backup_id'], "backup_test_1_0_0_123456")
        self.assertEqual(data['package_name'], "test")
        self.assertEqual(data['file_count'], 10)
        
        # Test from_dict
        restored = BackupInfo.from_dict(data)
        self.assertEqual(restored.backup_id, backup_info.backup_id)
        self.assertEqual(restored.package_name, backup_info.package_name)
        self.assertEqual(restored.file_count, backup_info.file_count)


class TestUpdateOperation(unittest.TestCase):
    """Test UpdateOperation functionality"""
    
    def test_operation_serialization(self):
        """Test update operation to dict conversion"""
        operation = UpdateOperation(
            operation_id="test_op_123",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_TARGET,
            started_at="2023-01-01T00:00:00",
            progress=25.0
        )
        
        # Add a conflict and validation
        conflict = UpdateConflict(
            file_path="test.py",
            conflict_type="modified",
            suggested_resolution=ConflictResolution.OVERWRITE
        )
        operation.conflicts.append(conflict)
        
        validation = ValidationResult(
            stage="test_validation",
            success=True,
            message="Test passed"
        )
        operation.validations.append(validation)
        
        # Test serialization
        data = operation.to_dict()
        
        self.assertEqual(data['operation_id'], "test_op_123")
        self.assertEqual(data['package_name'], "test-app")
        self.assertEqual(data['stage'], "VALIDATING_TARGET")
        self.assertEqual(data['progress'], 25.0)
        self.assertEqual(len(data['conflicts']), 1)
        self.assertEqual(len(data['validations']), 1)
        self.assertEqual(data['conflicts'][0]['file_path'], "test.py")
        self.assertEqual(data['validations'][0]['stage'], "test_validation")


class TestUpdateConfig(unittest.TestCase):
    """Test UpdateConfig functionality"""
    
    def test_default_config(self):
        """Test default update configuration"""
        config = UpdateConfig()
        
        self.assertTrue(config.create_backups)
        self.assertEqual(config.backup_retention_days, 30)
        self.assertTrue(config.validate_checksums)
        self.assertTrue(config.auto_rollback_on_failure)
        self.assertEqual(config.default_conflict_resolution, ConflictResolution.ABORT)
        self.assertEqual(config.concurrent_file_operations, 4)
    
    def test_custom_config(self):
        """Test custom update configuration"""
        config = UpdateConfig(
            create_backups=False,
            backup_retention_days=7,
            auto_rollback_on_failure=False,
            default_conflict_resolution=ConflictResolution.OVERWRITE
        )
        
        self.assertFalse(config.create_backups)
        self.assertEqual(config.backup_retention_days, 7)
        self.assertFalse(config.auto_rollback_on_failure)
        self.assertEqual(config.default_conflict_resolution, ConflictResolution.OVERWRITE)


class TestUpdateManager(unittest.TestCase):
    """Test UpdateManager functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.target_dir = self.temp_dir / "target"
        self.repo_dir = self.temp_dir / "repository"
        self.backup_dir = self.temp_dir / "backups"
        
        # Create directories
        self.target_dir.mkdir(parents=True)
        self.repo_dir.mkdir(parents=True)
        self.backup_dir.mkdir(parents=True)
        
        # Create test configuration
        self.config = UpdateConfig(
            backup_location=str(self.backup_dir),
            target_directory=str(self.target_dir)
        )
        
        # Create mock repository
        self.mock_repository = Mock(spec=PackageRepository)
        
        # Create update manager
        self.update_manager = UpdateManager(
            repository=self.mock_repository,
            update_config=self.config,
            target_directory=self.target_dir
        )
        
        # Create test files in target directory
        self._create_test_target_files()
    
    def tearDown(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_target_files(self):
        """Create test files in target directory"""
        # Create version.json
        version_info = {
            "package_name": "test-app",
            "version": "1.0.0",
            "platform": "linux"
        }
        
        version_file = self.target_dir / "version.json"
        with open(version_file, 'w') as f:
            json.dump(version_info, f)
        
        # Create some application files
        (self.target_dir / "src").mkdir(exist_ok=True)
        (self.target_dir / "src" / "main.py").write_text("print('Hello v1.0.0')")
        (self.target_dir / "config.yaml").write_text("version: 1.0.0")
    
    def _create_test_package(self, version: str = "1.1.0", content: str = None) -> Path:
        """Create a test package file"""
        package_dir = self.temp_dir / "package_staging"
        package_dir.mkdir(exist_ok=True)
        
        # Create package content
        (package_dir / "src").mkdir(exist_ok=True)
        if content:
            (package_dir / "src" / "main.py").write_text(content)
        else:
            (package_dir / "src" / "main.py").write_text(f"print('Hello v{version}')")
        
        # Create manifest
        manifest_data = {
            "package_name": "test-app",
            "version": version,
            "platform": "linux"
        }
        with open(package_dir / "manifest.json", 'w') as f:
            json.dump(manifest_data, f)
        
        # Create package archive
        package_file = self.temp_dir / f"test-app-{version}.tar.gz"
        with tarfile.open(package_file, 'w:gz') as tar:
            for item in package_dir.rglob('*'):
                if item.is_file():
                    arcname = item.relative_to(package_dir)
                    tar.add(item, arcname=arcname)
        
        return package_file
    
    def test_initialization(self):
        """Test update manager initialization"""
        self.assertTrue(self.update_manager.target_directory.exists())
        self.assertTrue(hasattr(self.update_manager, 'repository'))
        self.assertTrue(hasattr(self.update_manager, 'version_manager'))
        self.assertTrue(hasattr(self.update_manager, 'logger'))
        self.assertTrue(hasattr(self.update_manager, '_update_lock'))
        self.assertEqual(self.update_manager.target_directory, self.target_dir)
    
    def test_detect_current_version(self):
        """Test current version detection"""
        version = self.update_manager._detect_current_version("test-app")
        self.assertEqual(version, "1.0.0")
        
        # Test with non-existent package
        version = self.update_manager._detect_current_version("non-existent")
        self.assertIsNone(version)
    
    def test_create_backup(self):
        """Test backup creation"""
        operation = UpdateOperation(
            operation_id="test_backup",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.CREATING_BACKUP,
            started_at=datetime.now().isoformat()
        )
        
        backup_info = self.update_manager._create_backup(operation)
        
        self.assertIsNotNone(backup_info)
        self.assertEqual(backup_info.package_name, "test-app")
        self.assertEqual(backup_info.package_version, "1.0.0")
        self.assertGreater(backup_info.file_count, 0)
        self.assertGreater(backup_info.total_size, 0)
        self.assertTrue(Path(backup_info.backup_path).exists())
        
        # Verify backup metadata file was created
        metadata_file = Path(backup_info.backup_path).with_suffix('.json')
        self.assertTrue(metadata_file.exists())
    
    def test_validate_target_package(self):
        """Test target package validation"""
        # Setup mock repository response
        target_package = PackageEntry(
            name="test-app",
            version="1.1.0",
            platform="linux",
            file_path="packages/test-app-1.1.0.tar.gz",
            file_size=1024,
            checksum="abc123",
            created_at=datetime.now().isoformat()
        )
        
        self.mock_repository.search_packages.return_value = [target_package]
        
        operation = UpdateOperation(
            operation_id="test_validate",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_TARGET,
            started_at=datetime.now().isoformat()
        )
        
        result = self.update_manager._validate_target_package(operation)
        
        self.assertEqual(result, target_package)
        self.assertEqual(len(operation.validations), 1)
        self.assertTrue(operation.validations[0].success)
        self.mock_repository.search_packages.assert_called_once()
    
    def test_validate_target_package_not_found(self):
        """Test target package validation when package not found"""
        self.mock_repository.search_packages.return_value = []
        
        operation = UpdateOperation(
            operation_id="test_validate_fail",
            package_name="missing-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_TARGET,
            started_at=datetime.now().isoformat()
        )
        
        with self.assertRaises(RuntimeError) as context:
            self.update_manager._validate_target_package(operation)
        
        self.assertIn("Target package not found", str(context.exception))
        self.assertEqual(len(operation.validations), 1)
        self.assertFalse(operation.validations[0].success)
    
    def test_retrieve_package(self):
        """Test package retrieval from repository"""
        # Create test package
        package_file = self._create_test_package("1.1.0")
        
        # Setup mock repository
        target_package = PackageEntry(
            name="test-app",
            version="1.1.0",
            platform="linux",
            file_path="packages/test-app-1.1.0.tar.gz",
            file_size=package_file.stat().st_size,
            checksum="abc123",
            created_at=datetime.now().isoformat()
        )
        
        self.mock_repository.retrieve_package.return_value = package_file
        
        operation = UpdateOperation(
            operation_id="test_retrieve",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.DOWNLOADING_PACKAGE,
            started_at=datetime.now().isoformat()
        )
        
        result = self.update_manager._retrieve_package(operation, target_package)
        
        self.assertEqual(result, package_file)
        self.assertTrue(result.exists())
        self.assertEqual(len(operation.validations), 1)
        self.assertTrue(operation.validations[0].success)
    
    def test_validate_package_integrity(self):
        """Test package integrity validation"""
        # Create test package
        package_file = self._create_test_package("1.1.0")
        
        # Calculate actual checksum
        with open(package_file, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        target_package = PackageEntry(
            name="test-app",
            version="1.1.0",
            platform="linux",
            file_path="packages/test-app-1.1.0.tar.gz",
            file_size=package_file.stat().st_size,
            checksum=checksum,
            created_at=datetime.now().isoformat()
        )
        
        operation = UpdateOperation(
            operation_id="test_integrity",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_PACKAGE,
            started_at=datetime.now().isoformat()
        )
        
        # Should not raise exception
        self.update_manager._validate_package_integrity(operation, package_file, target_package)
        
        self.assertEqual(len(operation.validations), 1)
        self.assertTrue(operation.validations[0].success)
    
    def test_validate_package_integrity_checksum_mismatch(self):
        """Test package integrity validation with checksum mismatch"""
        package_file = self._create_test_package("1.1.0")
        
        target_package = PackageEntry(
            name="test-app",
            version="1.1.0",
            platform="linux",
            file_path="packages/test-app-1.1.0.tar.gz",
            file_size=package_file.stat().st_size,
            checksum="wrong_checksum",
            created_at=datetime.now().isoformat()
        )
        
        operation = UpdateOperation(
            operation_id="test_integrity_fail",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_PACKAGE,
            started_at=datetime.now().isoformat()
        )
        
        with self.assertRaises(RuntimeError) as context:
            self.update_manager._validate_package_integrity(operation, package_file, target_package)
        
        self.assertIn("checksum mismatch", str(context.exception))
        self.assertEqual(len(operation.validations), 1)
        self.assertFalse(operation.validations[0].success)
    
    def test_check_update_conflicts(self):
        """Test update conflict detection"""
        # Create package with conflicting file
        package_file = self._create_test_package("1.1.0", "print('Modified content')")
        
        operation = UpdateOperation(
            operation_id="test_conflicts",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.CHECKING_CONFLICTS,
            started_at=datetime.now().isoformat()
        )
        
        conflicts = self.update_manager._check_update_conflicts(operation, package_file)
        
        # Should find conflicts since files differ
        self.assertGreater(len(conflicts), 0)
        
        # Check conflict details
        main_py_conflict = next((c for c in conflicts if "main.py" in c.file_path), None)
        self.assertIsNotNone(main_py_conflict)
        self.assertEqual(main_py_conflict.conflict_type, "modified")
    
    def test_apply_update(self):
        """Test update application"""
        # Create test package
        package_file = self._create_test_package("1.1.0")
        
        operation = UpdateOperation(
            operation_id="test_apply",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.APPLYING_UPDATE,
            started_at=datetime.now().isoformat()
        )
        
        # Apply update
        self.update_manager._apply_update(operation, package_file)
        
        # Verify update was applied
        updated_main = self.target_dir / "src" / "main.py"
        self.assertTrue(updated_main.exists())
        content = updated_main.read_text()
        self.assertIn("v1.1.0", content)
        
        # Verify version file was updated
        version_file = self.target_dir / "version.json"
        self.assertTrue(version_file.exists())
        with open(version_file, 'r') as f:
            version_data = json.load(f)
        self.assertEqual(version_data['version'], "1.1.0")
        
        self.assertEqual(len(operation.validations), 1)
        self.assertTrue(operation.validations[0].success)
    
    def test_validate_applied_update(self):
        """Test post-update validation"""
        # Configure update manager to skip post-update tests
        self.update_manager.config.run_post_update_tests = False
        
        # Setup updated files
        version_info = {
            "package_name": "test-app",
            "version": "1.1.0",
            "platform": "linux"
        }
        
        version_file = self.target_dir / "version.json"
        with open(version_file, 'w') as f:
            json.dump(version_info, f)
        
        # Add manifest file to ensure validation passes
        manifest_info = {
            "package_name": "test-app",
            "version": "1.1.0"
        }
        
        manifest_file = self.target_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest_info, f)
        
        operation = UpdateOperation(
            operation_id="test_validate_update",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_UPDATE,
            started_at=datetime.now().isoformat()
        )
        
        # Should not raise exception
        self.update_manager._validate_applied_update(operation)
        
        self.assertEqual(len(operation.validations), 1)
        self.assertTrue(operation.validations[0].success)
    
    def test_rollback_update(self):
        """Test update rollback"""
        # Create backup
        operation = UpdateOperation(
            operation_id="test_rollback",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.CREATING_BACKUP,
            started_at=datetime.now().isoformat()
        )
        
        backup_info = self.update_manager._create_backup(operation)
        operation.backup_info = backup_info
        
        # Modify target directory to simulate failed update
        modified_file = self.target_dir / "src" / "main.py"
        modified_file.write_text("print('Broken update')")
        
        # Perform rollback
        self.update_manager._rollback_update(operation)
        
        # Verify rollback restored original content
        content = modified_file.read_text()
        self.assertIn("v1.0.0", content)
        self.assertNotIn("Broken", content)
        
        self.assertEqual(operation.stage, UpdateStage.ROLLBACK_COMPLETED)
        self.assertTrue(operation.rollback_attempted)
    
    def test_rollback_update_no_backup(self):
        """Test rollback when no backup available"""
        operation = UpdateOperation(
            operation_id="test_rollback_no_backup",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.APPLYING_UPDATE,
            started_at=datetime.now().isoformat()
        )
        
        with self.assertRaises(RuntimeError) as context:
            self.update_manager._rollback_update(operation)
        
        self.assertIn("No backup available", str(context.exception))
    
    @patch('provisioning.update_manager.UpdateManager._execute_staged_update')
    def test_start_update(self, mock_execute):
        """Test starting an update operation"""
        mock_execute.return_value = None
        
        operation_id = self.update_manager.start_update(
            package_name="test-app",
            target_version="1.1.0",
            target_platform="linux"
        )
        
        self.assertIsNotNone(operation_id)
        self.assertTrue(operation_id.startswith("update_test-app_1.1.0_"))
        
        # Verify operation was registered
        operation = self.update_manager.get_update_status(operation_id)
        self.assertIsNotNone(operation)
        self.assertEqual(operation.package_name, "test-app")
        self.assertEqual(operation.target_version, "1.1.0")
        
        mock_execute.assert_called_once()
    
    def test_start_update_invalid_version(self):
        """Test starting update with invalid version"""
        with self.assertRaises(ValueError) as context:
            self.update_manager.start_update(
                package_name="test-app",
                target_version="invalid.version"
            )
        
        self.assertIn("Invalid target version", str(context.exception))
    
    def test_get_update_status(self):
        """Test getting update operation status"""
        # Create test operation
        operation = UpdateOperation(
            operation_id="test_status",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_TARGET,
            started_at=datetime.now().isoformat()
        )
        
        self.update_manager._active_operations["test_status"] = operation
        
        result = self.update_manager.get_update_status("test_status")
        self.assertEqual(result, operation)
        
        # Test non-existent operation
        result = self.update_manager.get_update_status("non_existent")
        self.assertIsNone(result)
    
    def test_cancel_update(self):
        """Test cancelling update operation"""
        # Create test operation
        operation = UpdateOperation(
            operation_id="test_cancel",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_TARGET,
            started_at=datetime.now().isoformat()
        )
        
        self.update_manager._active_operations["test_cancel"] = operation
        
        success = self.update_manager.cancel_update("test_cancel")
        self.assertTrue(success)
        self.assertEqual(operation.stage, UpdateStage.FAILED)
        self.assertIn("cancelled", operation.error_message)
    
    def test_cancel_update_non_existent(self):
        """Test cancelling non-existent update"""
        success = self.update_manager.cancel_update("non_existent")
        self.assertFalse(success)
    
    def test_list_backups(self):
        """Test listing available backups"""
        # Create test backup
        operation = UpdateOperation(
            operation_id="test_list_backups",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.CREATING_BACKUP,
            started_at=datetime.now().isoformat()
        )
        
        backup_info = self.update_manager._create_backup(operation)
        
        # List backups
        backups = self.update_manager.list_backups()
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].backup_id, backup_info.backup_id)
        
        # List with package filter
        filtered_backups = self.update_manager.list_backups(package_name="test-app")
        self.assertEqual(len(filtered_backups), 1)
        
        filtered_backups = self.update_manager.list_backups(package_name="other-app")
        self.assertEqual(len(filtered_backups), 0)
    
    def test_cleanup_old_backups(self):
        """Test cleaning up old backups"""
        # Create test backup with old timestamp
        operation = UpdateOperation(
            operation_id="test_cleanup",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.CREATING_BACKUP,
            started_at=datetime.now().isoformat()
        )
        
        backup_info = self.update_manager._create_backup(operation)
        
        # Modify backup timestamp to make it old
        metadata_file = Path(backup_info.backup_path).with_suffix('.json')
        with open(metadata_file, 'r') as f:
            data = json.load(f)
        
        old_date = (datetime.now() - timedelta(days=40)).isoformat()
        data['created_at'] = old_date
        
        with open(metadata_file, 'w') as f:
            json.dump(data, f)
        
        # Cleanup old backups
        cleaned_count = self.update_manager.cleanup_old_backups(retention_days=30)
        self.assertEqual(cleaned_count, 1)
        
        # Verify backup was removed
        self.assertFalse(Path(backup_info.backup_path).exists())
        self.assertFalse(metadata_file.exists())
    
    def test_thread_safety(self):
        """Test thread-safe operations"""
        results = []
        errors = []
        
        def update_thread(thread_id):
            try:
                # Mock the repository to return a package
                target_package = PackageEntry(
                    name=f"app-{thread_id}",
                    version="1.1.0",
                    platform="linux",
                    file_path=f"packages/app-{thread_id}-1.1.0.tar.gz",
                    file_size=1024,
                    checksum="abc123",
                    created_at=datetime.now().isoformat()
                )
                
                self.mock_repository.search_packages.return_value = [target_package]
                
                # Create test package
                package_file = self._create_test_package("1.1.0")
                self.mock_repository.retrieve_package.return_value = package_file
                
                # Just test operation creation (not full execution)
                operation = UpdateOperation(
                    operation_id=f"thread_test_{thread_id}",
                    package_name=f"app-{thread_id}",
                    current_version="1.0.0",
                    target_version="1.1.0",
                    target_platform="linux",
                    stage=UpdateStage.INITIALIZED,
                    started_at=datetime.now().isoformat()
                )
                
                with self.update_manager._update_lock:
                    self.update_manager._active_operations[operation.operation_id] = operation
                    results.append((thread_id, operation.operation_id))
                
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        
        # Verify all operations were registered
        for thread_id, operation_id in results:
            operation = self.update_manager.get_update_status(operation_id)
            self.assertIsNotNone(operation)
            self.assertEqual(operation.package_name, f"app-{thread_id}")
    
    def test_get_stats(self):
        """Test statistics collection"""
        # Create some operations and backups
        operation = UpdateOperation(
            operation_id="test_stats",
            package_name="test-app",
            current_version="1.0.0",
            target_version="1.1.0",
            target_platform="linux",
            stage=UpdateStage.VALIDATING_TARGET,
            started_at=datetime.now().isoformat()
        )
        
        self.update_manager._active_operations["test_stats"] = operation
        
        # Increment operation count manually for test
        self.update_manager._increment_operation_count()
        
        stats = self.update_manager.get_stats()
        
        self.assertIn('operation_count', stats)
        self.assertIn('active_operations', stats)
        self.assertIn('target_directory', stats)
        self.assertIn('backup_directory', stats)
        self.assertIn('total_backups', stats)
        self.assertIn('backup_storage_bytes', stats)
        self.assertIn('repository_stats', stats)
        self.assertIn('version_manager_stats', stats)
        
        self.assertGreaterEqual(stats['operation_count'], 1)
        self.assertEqual(stats['active_operations'], 1)
        self.assertEqual(stats['target_directory'], str(self.target_dir))


if __name__ == '__main__':
    unittest.main()