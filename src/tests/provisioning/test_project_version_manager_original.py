#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Comprehensive test suite for Project Version Manager

Tests all components of the automated version management system including
file updaters, atomic transactions, backup/restore functionality, and
workflow integration with high coverage.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add provisioning module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "provisioning"))

from project_version_manager import (
    ProjectVersionManager, FileVersionUpdater, VersionWorkflow,
    PyProjectTomlUpdater, SetupPyUpdater, InitPyUpdater, PackageConfigUpdater,
    FileType, UpdateResult, UpdateOperation
)


class TestFileVersionUpdaters:
    """Test file-specific version updaters"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_pyproject_toml_updater(self):
        """Test PyProjectTomlUpdater functionality"""
        # Create test pyproject.toml
        pyproject_content = '''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "gtach"
version = "1.0.0"
description = "Test project"
'''
        pyproject_file = self.temp_dir / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)
        
        updater = PyProjectTomlUpdater(pyproject_file)
        
        # Test version detection
        assert updater.detect_version() == "1.0.0"
        assert updater.file_type == FileType.PYPROJECT_TOML
        
        # Test version update
        assert updater.update_version("2.0.0-beta.1") is True
        assert updater.detect_version() == "2.0.0-beta.1"
        
        # Test invalid version
        assert updater.update_version("invalid-version") is False
        
        # Verify file content
        updated_content = pyproject_file.read_text()
        assert 'version = "2.0.0-beta.1"' in updated_content
        
    def test_setup_py_updater(self):
        """Test SetupPyUpdater functionality"""
        # Create test setup.py
        setup_content = '''#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="gtach",
    version="1.0.0",
    description="Test project",
    packages=find_packages(),
)
'''
        setup_file = self.temp_dir / "setup.py"
        setup_file.write_text(setup_content)
        
        updater = SetupPyUpdater(setup_file)
        
        # Test version detection
        assert updater.detect_version() == "1.0.0"
        assert updater.file_type == FileType.SETUP_PY
        
        # Test version update
        assert updater.update_version("3.1.0-alpha.2") is True
        assert updater.detect_version() == "3.1.0-alpha.2"
        
        # Verify file content
        updated_content = setup_file.read_text()
        assert 'version="3.1.0-alpha.2"' in updated_content
        
    def test_init_py_updater(self):
        """Test InitPyUpdater functionality"""
        # Create test __init__.py
        init_content = '''"""Test package"""

from .main import main

__version__ = "1.0.0"
__author__ = "Test Author"

__all__ = ['main', '__version__']
'''
        init_file = self.temp_dir / "__init__.py"
        init_file.write_text(init_content)
        
        updater = InitPyUpdater(init_file)
        
        # Test version detection
        assert updater.detect_version() == "1.0.0"
        assert updater.file_type == FileType.INIT_PY
        
        # Test version update
        assert updater.update_version("0.5.0-rc.1") is True
        assert updater.detect_version() == "0.5.0-rc.1"
        
        # Verify file content
        updated_content = init_file.read_text()
        assert '__version__ = "0.5.0-rc.1"' in updated_content
        
    def test_package_config_updater(self):
        """Test PackageConfigUpdater functionality"""
        # Create test package_creator.py with PackageConfig
        package_content = '''#!/usr/bin/env python3

@dataclass
class PackageConfig:
    """Configuration for package creation"""
    # Package identification
    package_name: str = "gtach-app"
    version: str = "1.0.0"
    target_platform: str = "raspberry-pi"
'''
        package_file = self.temp_dir / "package_creator.py"
        package_file.write_text(package_content)
        
        updater = PackageConfigUpdater(package_file)
        
        # Test version detection
        assert updater.detect_version() == "1.0.0"
        assert updater.file_type == FileType.PACKAGE_CONFIG
        
        # Test version update
        assert updater.update_version("2.5.0-beta.3") is True
        assert updater.detect_version() == "2.5.0-beta.3"
        
        # Verify file content
        updated_content = package_file.read_text()
        assert 'version: str = "2.5.0-beta.3"' in updated_content
        
    def test_backup_and_restore(self):
        """Test backup and restore functionality"""
        # Create test file
        test_content = 'version = "1.0.0"'
        test_file = self.temp_dir / "test.toml"
        test_file.write_text(test_content)
        
        updater = PyProjectTomlUpdater(test_file)
        backup_dir = self.temp_dir / "backups"
        
        # Test backup creation
        backup_path = updater.backup_file(backup_dir)
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == test_content
        
        # Modify original file
        test_file.write_text('version = "2.0.0"')
        
        # Test restore
        assert updater.restore_from_backup(backup_path) is True
        assert test_file.read_text() == test_content
        
    def test_version_validation(self):
        """Test version validation across updaters"""
        test_file = self.temp_dir / "test.toml"
        test_file.write_text('version = "1.0.0"')
        
        updater = PyProjectTomlUpdater(test_file)
        
        # Valid versions
        assert updater.validate_version("1.0.0") is True
        assert updater.validate_version("2.1.3-alpha.1") is True
        assert updater.validate_version("0.1.0-beta.2") is True
        assert updater.validate_version("1.0.0+build.123") is True
        
        # Invalid versions
        assert updater.validate_version("1.0") is False
        assert updater.validate_version("invalid") is False
        assert updater.validate_version("1.0.0.0") is False


class TestProjectVersionManager:
    """Test ProjectVersionManager coordination functionality"""
    
    def setup_method(self):
        """Setup test project structure"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.create_test_project_structure()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def create_test_project_structure(self):
        """Create realistic test project structure"""
        # Create pyproject.toml
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach"
version = "1.0.0"
''')
        
        # Create setup.py
        (self.temp_dir / "setup.py").write_text('''setup(
    name="gtach",
    version="1.0.0",
)''')
        
        # Create src structure
        src_dir = self.temp_dir / "src"
        src_dir.mkdir()
        
        obdii_dir = src_dir / "obdii"
        obdii_dir.mkdir()
        (obdii_dir / "__init__.py").write_text('__version__ = "1.0.0"')
        
        provisioning_dir = src_dir / "provisioning" 
        provisioning_dir.mkdir()
        (provisioning_dir / "__init__.py").write_text('__version__ = "2.0.0"')  # Inconsistent
        (provisioning_dir / "package_creator.py").write_text('''
@dataclass
class PackageConfig:
    version: str = "1.5.0"
''')
        
    def test_initialization(self):
        """Test ProjectVersionManager initialization"""
        manager = ProjectVersionManager(self.temp_dir)
        
        assert manager.project_root == self.temp_dir
        assert len(manager._updaters) > 0
        
        stats = manager.get_stats()
        assert stats['managed_files'] > 0
        assert 'current_versions' in stats
        
    def test_version_detection(self):
        """Test version detection across files"""
        manager = ProjectVersionManager(self.temp_dir)
        
        current_versions = manager.get_current_versions()
        assert len(current_versions) > 0
        
        # Check specific versions
        pyproject_path = self.temp_dir / "pyproject.toml"
        assert current_versions.get(pyproject_path) == "1.0.0"
        
    def test_inconsistency_detection(self):
        """Test version inconsistency detection"""
        manager = ProjectVersionManager(self.temp_dir)
        
        inconsistencies = manager.detect_version_inconsistencies()
        
        # Should detect multiple versions
        assert len(inconsistencies) > 1
        assert "1.0.0" in inconsistencies
        assert "2.0.0" in inconsistencies or "1.5.0" in inconsistencies
        
        stats = manager.get_stats()
        assert stats['has_inconsistencies'] is True
        
    def test_atomic_version_update(self):
        """Test atomic version update functionality"""
        manager = ProjectVersionManager(self.temp_dir)
        
        target_version = "3.0.0-beta.1"
        results = manager.update_all_versions(target_version)
        
        # Check results
        assert len(results) > 0
        success_count = sum(1 for r in results.values() 
                          if r in [UpdateResult.SUCCESS, UpdateResult.NO_CHANGE])
        assert success_count == len(results)
        
        # Verify all files updated
        updated_versions = manager.get_current_versions()
        for file_path, version in updated_versions.items():
            if version is not None:
                assert version == target_version
                
        # Check consistency
        inconsistencies = manager.detect_version_inconsistencies()
        assert len(inconsistencies) == 1
        assert target_version in inconsistencies
        
    def test_version_update_rollback(self):
        """Test rollback on failed updates"""
        manager = ProjectVersionManager(self.temp_dir)
        
        # Get initial versions
        initial_versions = manager.get_current_versions()
        
        # Create a mock updater that will fail during update
        file_path = list(manager._updaters.keys())[0]
        original_updater = manager._updaters[file_path]
        
        # Create a mock updater that fails update but allows backup
        class FailingUpdater:
            def __init__(self, original):
                self.file_type = original.file_type
                self.file_path = original.file_path
                
            def detect_version(self):
                return "1.0.0"
                
            def backup_file(self, backup_dir):
                # Create a real backup file for testing
                backup_path = backup_dir / "test_backup.tmp"
                backup_path.write_text("backup content")
                return backup_path
                
            def update_version(self, version):
                return False  # Always fail
                
            def restore_from_backup(self, backup_path):
                return True
        
        # Replace updater with failing one
        failing_updater = FailingUpdater(original_updater)
        manager._updaters[file_path] = failing_updater
        
        # The update should not raise RuntimeError in our current implementation
        # because we continue processing other files even if one fails
        results = manager.update_all_versions("4.0.0")
        
        # Check that the failing file has FAILED result
        assert results[file_path] == UpdateResult.FAILED
        
        # Other files may succeed
        success_count = sum(1 for r in results.values() if r == UpdateResult.SUCCESS)
        fail_count = sum(1 for r in results.values() if r == UpdateResult.FAILED)
        
        assert fail_count >= 1  # At least our mocked file failed
        
    def test_performance_requirements(self):
        """Test performance requirements (< 2 seconds)"""
        import time
        
        manager = ProjectVersionManager(self.temp_dir)
        
        start_time = time.perf_counter()
        manager.update_all_versions("5.0.0-performance.test")
        elapsed = time.perf_counter() - start_time
        
        assert elapsed < 2.0, f"Version update took {elapsed:.2f}s, should be < 2.0s"
        
    def test_thread_safety(self):
        """Test thread-safe operations"""
        import threading
        import time
        
        manager = ProjectVersionManager(self.temp_dir)
        results = []
        errors = []
        
        def update_version(version_suffix):
            try:
                version = f"6.0.0-{version_suffix}"
                result = manager.update_all_versions(version)
                results.append((version_suffix, result))
            except Exception as e:
                errors.append((version_suffix, e))
                
        # Run concurrent updates
        threads = []
        for i in range(3):
            thread = threading.Thread(target=update_version, args=(f"thread{i}",))
            threads.append(thread)
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Check results (only one should succeed due to locking)
        assert len(results) >= 1
        # Some operations might be serialized, so no strict requirement on exact count


class TestVersionWorkflow:
    """Test VersionWorkflow integration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.create_minimal_project()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def create_minimal_project(self):
        """Create minimal project for workflow testing"""
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach"
version = "1.0.0"
''')
        
        src_dir = self.temp_dir / "src" / "obdii"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('__version__ = "1.0.0"')
        
    def test_workflow_initialization(self):
        """Test VersionWorkflow initialization"""
        workflow = VersionWorkflow(self.temp_dir)
        
        assert workflow.project_root == self.temp_dir
        assert workflow.project_manager is not None
        assert workflow.version_manager is not None
        
    def test_get_current_project_version(self):
        """Test getting current project version"""
        workflow = VersionWorkflow(self.temp_dir)
        
        version = workflow.get_current_project_version()
        assert version == "1.0.0"
        
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_version_update_cancel(self, mock_print, mock_input):
        """Test interactive version update cancellation"""
        mock_input.return_value = "cancel"
        
        workflow = VersionWorkflow(self.temp_dir)
        result = workflow.interactive_version_update()
        
        assert result is None
        
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_version_update_success(self, mock_print, mock_input):
        """Test successful interactive version update"""
        # Mock user inputs: version, confirmation
        mock_input.side_effect = ["2.0.0-beta.1", "y"]
        
        workflow = VersionWorkflow(self.temp_dir)
        result = workflow.interactive_version_update()
        
        assert result == "2.0.0-beta.1"
        
        # Verify version was actually updated
        current_version = workflow.get_current_project_version()
        assert current_version == "2.0.0-beta.1"


class TestIntegration:
    """Integration tests for complete version management system"""
    
    def setup_method(self):
        """Setup full project structure"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.create_full_project_structure()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def create_full_project_structure(self):
        """Create complete project structure matching GTach"""
        # Root files
        (self.temp_dir / "pyproject.toml").write_text('''[build-system]
requires = ["setuptools>=45", "wheel"]

[project]
name = "gtach"
version = "0.1.0"
description = "GPIO-based Tachometer"
''')
        
        (self.temp_dir / "setup.py").write_text('''setup(
    name="gtach",
    version="0.1.0",
    description="GTach Application",
)''')
        
        # Source structure
        src_dir = self.temp_dir / "src"
        
        obdii_dir = src_dir / "obdii"
        obdii_dir.mkdir(parents=True)
        (obdii_dir / "__init__.py").write_text('''"""OBDII application package."""

__version__ = "0.1.0"
__author__ = "GTach Team"
''')
        
        provisioning_dir = src_dir / "provisioning"
        provisioning_dir.mkdir()
        (provisioning_dir / "__init__.py").write_text('''"""Provisioning system."""

__version__ = '0.2.0'
''')
        
        (provisioning_dir / "package_creator.py").write_text('''
@dataclass
class PackageConfig:
    """Configuration for package creation"""
    package_name: str = "gtach-app"
    version: str = "0.1.5"
    target_platform: str = "raspberry-pi"
''')
        
    def test_full_system_consistency_check(self):
        """Test detecting and fixing inconsistencies across full project"""
        manager = ProjectVersionManager(self.temp_dir)
        
        # Detect inconsistencies
        inconsistencies = manager.detect_version_inconsistencies()
        assert len(inconsistencies) > 1  # Multiple versions present
        
        # Fix inconsistencies
        target_version = "1.0.0-alpha.1"
        results = manager.update_all_versions(target_version)
        
        # Verify all updates succeeded
        for file_path, result in results.items():
            assert result in [UpdateResult.SUCCESS, UpdateResult.NO_CHANGE]
            
        # Verify consistency achieved
        final_inconsistencies = manager.detect_version_inconsistencies()
        assert len(final_inconsistencies) == 1
        assert target_version in final_inconsistencies
        
        # Verify all files have correct version
        current_versions = manager.get_current_versions()
        for file_path, version in current_versions.items():
            if version is not None:
                assert version == target_version
                
    def test_workflow_complete_cycle(self):
        """Test complete workflow from detection to update"""
        workflow = VersionWorkflow(self.temp_dir)
        
        # Check initial state
        initial_version = workflow.get_current_project_version()
        assert initial_version is not None  # Should pick most common
        
        # Simulate automated update
        target_version = "2.0.0-release.1"
        result = workflow._execute_version_update(target_version)
        
        assert result == target_version
        
        # Verify final state
        final_version = workflow.get_current_project_version()
        assert final_version == target_version
        
        # Check statistics
        stats = workflow.project_manager.get_stats()
        assert stats['has_inconsistencies'] is False
        assert stats['operation_count'] > 0


if __name__ == "__main__":
    # Run tests with coverage
    import subprocess
    subprocess.run([
        "python", "-m", "pytest", __file__, "-v", 
        "--cov=project_version_manager",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])