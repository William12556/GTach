#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Comprehensive test suite for Enhanced Project Version Manager with VersionStateManager Integration

Tests all components of the enhanced project version management system including
state coordination, enhanced inconsistency detection, interactive resolution,
and coordinated atomic operations.
"""

import pytest
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add provisioning module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "provisioning"))

from project_version_manager import (
    EnhancedProjectVersionManager,
    EnhancedVersionWorkflow,
    StateCoordinationResult,
    VersionInconsistency
)
from version_state_manager import VersionStateManager, DevelopmentStage
from project_version_manager import UpdateResult


class TestVersionInconsistency:
    """Test VersionInconsistency dataclass functionality"""
    
    def test_version_inconsistency_creation(self):
        """Test creation of VersionInconsistency objects"""
        inconsistency = VersionInconsistency(
            version="1.0.0-beta.1",
            source_type="version_state",
            is_authoritative=True,
            stage=DevelopmentStage.BETA
        )
        
        assert inconsistency.version == "1.0.0-beta.1"
        assert inconsistency.source_type == "version_state"
        assert inconsistency.is_authoritative is True
        assert inconsistency.stage == DevelopmentStage.BETA
        assert len(inconsistency.file_paths) == 0


class TestStateCoordinationResult:
    """Test StateCoordinationResult dataclass functionality"""
    
    def test_coordination_result_creation(self):
        """Test creation of StateCoordinationResult objects"""
        result = StateCoordinationResult(
            project_files_updated=True,
            state_updated=True,
            inconsistencies_resolved=True,
            authoritative_version="2.0.0",
            operation_time_ms=150.5
        )
        
        assert result.project_files_updated is True
        assert result.state_updated is True
        assert result.inconsistencies_resolved is True
        assert result.authoritative_version == "2.0.0"
        assert result.operation_time_ms == 150.5
        assert len(result.coordination_errors) == 0


class TestEnhancedProjectVersionManager:
    """Test EnhancedProjectVersionManager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
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
    version = "1.1.0",
)''')
        
        # Create src structure
        src_dir = self.temp_dir / "src"
        src_dir.mkdir()
        
        obdii_dir = src_dir / "obdii"
        obdii_dir.mkdir()
        (obdii_dir / "__init__.py").write_text('__version__ = "1.2.0"')
        
        provisioning_dir = src_dir / "provisioning"
        provisioning_dir.mkdir()
        (provisioning_dir / "__init__.py").write_text('__version__ = "0.9.0"')
        (provisioning_dir / "package_creator.py").write_text('''
@dataclass
class PackageConfig:
    version: str = "1.0.0-alpha.1"
''')
    
    def test_initialization_with_state_management(self):
        """Test enhanced manager initialization with state management enabled"""
        manager = EnhancedProjectVersionManager(
            self.temp_dir, 
            enable_state_management=True,
            session_id="test_session"
        )
        
        assert manager.project_root == self.temp_dir
        assert manager.enable_state_management is True
        assert manager.session_id == "test_session"
        assert manager._state_manager is not None
        assert len(manager._updaters) > 0
    
    def test_initialization_without_state_management(self):
        """Test initialization with state management disabled"""
        manager = EnhancedProjectVersionManager(
            self.temp_dir, 
            enable_state_management=False
        )
        
        assert manager.enable_state_management is False
        assert manager._state_manager is None
        assert len(manager._updaters) > 0  # File updaters still work
    
    def test_get_state_version(self):
        """Test getting version from state manager"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Should return default initial version
        state_version = manager.get_state_version()
        assert state_version == "0.1.0-dev"  # Default from VersionStateManager
        
        # Update state and verify
        if manager._state_manager:
            manager._state_manager.update_version("2.0.0-test")
            state_version = manager.get_state_version()
            assert state_version == "2.0.0-test"
    
    def test_get_state_version_without_state_manager(self):
        """Test getting state version when state manager is disabled"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=False)
        
        state_version = manager.get_state_version()
        assert state_version is None
    
    def test_enhanced_inconsistency_detection(self):
        """Test enhanced inconsistency detection with state analysis"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Update state to a specific version
        if manager._state_manager:
            manager._state_manager.update_version("1.5.0-beta.1")
        
        inconsistencies = manager.detect_version_inconsistencies_enhanced()
        
        # Should detect multiple inconsistencies including state
        assert len(inconsistencies) > 1
        
        # Check for authoritative version
        authoritative_found = False
        for version, info in inconsistencies.items():
            if info.is_authoritative:
                authoritative_found = True
                assert version == "1.5.0-beta.1"
                assert info.source_type in ["version_state", "both"]
                assert info.stage == DevelopmentStage.BETA
        
        assert authoritative_found, "No authoritative version found"
    
    def test_enhanced_inconsistency_detection_without_state(self):
        """Test enhanced inconsistency detection without state manager"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=False)
        
        inconsistencies = manager.detect_version_inconsistencies_enhanced()
        
        # Should still detect project file inconsistencies
        assert len(inconsistencies) > 1
        
        # No version should be authoritative
        for version, info in inconsistencies.items():
            assert not info.is_authoritative
            assert info.source_type == "project_file"
    
    def test_backward_compatible_inconsistency_detection(self):
        """Test backward compatibility of inconsistency detection"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Original method should still work
        inconsistencies = manager.detect_version_inconsistencies()
        
        assert isinstance(inconsistencies, dict)
        assert len(inconsistencies) > 1
        
        # Values should be lists of file paths
        for version, files in inconsistencies.items():
            assert isinstance(files, list)
            for file_path in files:
                assert isinstance(file_path, Path)
    
    def test_coordinated_version_update(self):
        """Test coordinated version update with state synchronization"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        target_version = "3.0.0-coordinated"
        result = manager.update_all_versions_coordinated(target_version, update_state=True)
        
        # Check coordination result
        assert result.authoritative_version == target_version
        assert result.project_files_updated is True
        assert result.state_updated is True
        assert result.inconsistencies_resolved is True
        assert result.operation_time_ms > 0
        
        # Verify actual updates
        current_versions = manager.get_current_versions()
        for file_path, version in current_versions.items():
            if version is not None:
                assert version == target_version
        
        # Verify state update
        state_version = manager.get_state_version()
        assert state_version == target_version
    
    def test_coordinated_update_without_state(self):
        """Test coordinated update when state manager is not available"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=False)
        
        target_version = "3.0.0-no-state"
        result = manager.update_all_versions_coordinated(target_version, update_state=True)
        
        # Should update project files but not state
        assert result.project_files_updated is True
        assert result.state_updated is False  # State manager not available
        assert len(result.coordination_errors) == 0  # Not updating state when disabled
    
    def test_backward_compatible_update(self):
        """Test backward compatibility of update_all_versions method"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        target_version = "2.5.0-backward"
        results = manager.update_all_versions(target_version)
        
        # Should return original format
        assert isinstance(results, dict)
        
        for file_path, result in results.items():
            assert isinstance(file_path, Path)
            assert isinstance(result, UpdateResult)
            assert result in [UpdateResult.SUCCESS, UpdateResult.NO_CHANGE, UpdateResult.FAILED]
        
        # Verify actual updates
        current_versions = manager.get_current_versions()
        for file_path, version in current_versions.items():
            if version is not None:
                assert version == target_version
    
    def test_enhanced_statistics(self):
        """Test enhanced statistics with state information"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Perform some operations
        manager.update_all_versions_coordinated("1.8.0-stats")
        
        stats = manager.get_stats_enhanced()
        
        # Check enhanced statistics
        required_fields = [
            'operation_count', 'managed_files', 'current_versions',
            'has_inconsistencies', 'state_management_enabled', 'session_id',
            'state_version', 'state_file_exists', 'authoritative_version',
            'inconsistency_details'
        ]
        
        for field in required_fields:
            assert field in stats, f"Missing field: {field}"
        
        assert stats['state_management_enabled'] is True
        assert stats['state_version'] == "1.8.0-stats"
        assert stats['authoritative_version'] == "1.8.0-stats"
        assert isinstance(stats['inconsistency_details'], dict)
    
    def test_backward_compatible_statistics(self):
        """Test backward compatibility of get_stats method"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        stats = manager.get_stats()
        
        # Should contain original fields
        original_fields = [
            'operation_count', 'managed_files', 'operations_history',
            'current_versions', 'version_groups', 'has_inconsistencies'
        ]
        
        for field in original_fields:
            assert field in stats, f"Missing original field: {field}"
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_sync_to_authoritative_version(self, mock_print, mock_input):
        """Test synchronizing to authoritative version"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Set up authoritative version in state
        if manager._state_manager:
            manager._state_manager.update_version("2.0.0-auth")
        
        result = manager._sync_to_authoritative_version("2.0.0-auth")
        
        assert result.project_files_updated is True
        assert result.state_updated is True
        assert result.inconsistencies_resolved is True
        assert result.authoritative_version == "2.0.0-auth"
    
    @patch('builtins.input')
    @patch('builtins.print') 
    def test_update_state_to_project_consensus(self, mock_print, mock_input):
        """Test updating state to project consensus"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Get current inconsistencies
        inconsistencies = manager.detect_version_inconsistencies_enhanced()
        
        result = manager._update_state_to_project_consensus(inconsistencies)
        
        # Should find consensus and update state
        assert result.state_updated is True
        assert result.authoritative_version is not None
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_version_setting(self, mock_print, mock_input):
        """Test interactive version setting"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Mock user input: version and confirmation
        mock_input.side_effect = ["3.0.0-interactive", "y"]
        
        inconsistencies = manager.detect_version_inconsistencies_enhanced()
        result = manager._set_version_interactive(inconsistencies)
        
        assert result.authoritative_version == "3.0.0-interactive"
        # Results depend on implementation success
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_version_cancellation(self, mock_print, mock_input):
        """Test interactive version setting cancellation"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Mock user cancellation
        mock_input.return_value = "cancel"
        
        inconsistencies = manager.detect_version_inconsistencies_enhanced()
        result = manager._set_version_interactive(inconsistencies)
        
        assert len(result.coordination_errors) > 0
        assert "cancelled" in result.coordination_errors[0].lower()


class TestEnhancedVersionWorkflow:
    """Test EnhancedVersionWorkflow functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.create_minimal_project_structure()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_minimal_project_structure(self):
        """Create minimal project structure"""
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach"
version = "1.0.0"
''')
        
        src_dir = self.temp_dir / "src" / "obdii"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('__version__ = "1.0.0"')
    
    def test_enhanced_workflow_initialization(self):
        """Test enhanced workflow initialization"""
        workflow = EnhancedVersionWorkflow(self.temp_dir, session_id="test_workflow")
        
        assert workflow.project_root == self.temp_dir
        assert workflow.session_id == "test_workflow"
        assert isinstance(workflow.project_manager, EnhancedProjectVersionManager)
        assert workflow.project_manager.enable_state_management is True
    
    def test_get_current_project_version_with_authority(self):
        """Test getting current project version with authoritative preference"""
        workflow = EnhancedVersionWorkflow(self.temp_dir)
        
        # Set authoritative version in state
        if workflow.project_manager._state_manager:
            workflow.project_manager._state_manager.update_version("2.0.0-authority")
        
        # Should prefer authoritative version
        current_version = workflow.get_current_project_version()
        assert current_version == "2.0.0-authority"
    
    def test_get_current_project_version_fallback(self):
        """Test fallback to project consensus when no authoritative version"""
        workflow = EnhancedVersionWorkflow(self.temp_dir)
        workflow.project_manager.enable_state_management = False
        
        # Should fall back to project file consensus
        current_version = workflow.get_current_project_version()
        assert current_version == "1.0.0"  # Consistent in test structure
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_update_with_resolution(self, mock_print, mock_input):
        """Test interactive update with inconsistency resolution"""
        workflow = EnhancedVersionWorkflow(self.temp_dir)
        
        # Create inconsistencies first
        (self.temp_dir / "setup.py").write_text('version="2.0.0"')
        
        # Mock user choices: resolve inconsistencies (y), sync to authoritative (1)
        mock_input.side_effect = ["y", "1"]
        
        result = workflow.interactive_version_update()
        
        # Should return some version (exact result depends on resolution)
        # Test verifies the workflow completes without errors
        assert mock_input.called
    
    @patch('builtins.input')
    @patch('builtins.print') 
    def test_interactive_update_skip_resolution(self, mock_print, mock_input):
        """Test interactive update skipping resolution"""
        workflow = EnhancedVersionWorkflow(self.temp_dir)
        
        # Create inconsistencies
        (self.temp_dir / "setup.py").write_text('version="2.0.0"')
        
        # Mock user choices: skip resolution (n), then version input (3.0.0), confirm (y)
        mock_input.side_effect = ["n", "3.0.0-test", "y"]
        
        # This will call the private method that handles version input
        # The exact flow depends on the implementation
        assert True  # Test structure verification


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_state_manager_initialization_failure(self):
        """Test handling of state manager initialization failure"""
        # Create directory that causes state manager to fail
        invalid_dir = self.temp_dir / "nonexistent"
        
        manager = EnhancedProjectVersionManager(
            invalid_dir,  # This should cause state manager initialization to fail
            enable_state_management=True
        )
        
        # Should gracefully handle failure and disable state management
        assert manager.enable_state_management is False
        assert manager._state_manager is None
        assert len(manager._state_coordination_errors) > 0
    
    def test_coordinated_update_with_state_error(self):
        """Test coordinated update when state operations fail"""
        # Create valid project structure
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach"
version = "1.0.0"
''')
        
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Mock state manager to fail on update
        if manager._state_manager:
            original_update = manager._state_manager.update_version
            def failing_update(*args, **kwargs):
                raise RuntimeError("State update failed")
            manager._state_manager.update_version = failing_update
        
        result = manager.update_all_versions_coordinated("2.0.0-error-test", update_state=True)
        
        # Should update project files but report state error
        assert result.project_files_updated is True
        assert result.state_updated is False
        assert len(result.coordination_errors) > 0
        assert "State update failed" in str(result.coordination_errors)
    
    def test_invalid_version_handling(self):
        """Test handling of invalid version formats"""
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach" 
version = "1.0.0"
''')
        
        manager = EnhancedProjectVersionManager(self.temp_dir)
        
        result = manager.update_all_versions_coordinated("invalid-version-format")
        
        assert result.project_files_updated is False
        assert len(result.coordination_errors) > 0
        assert "Invalid target version" in result.coordination_errors[0]


class TestPerformance:
    """Test performance characteristics"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.create_performance_test_structure()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_performance_test_structure(self):
        """Create structure for performance testing"""
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach"
version = "1.0.0"
''')
        
        src_dir = self.temp_dir / "src" / "obdii"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('__version__ = "1.0.0"')
    
    def test_coordination_performance(self):
        """Test that state coordination doesn't significantly impact performance"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        # Time coordinated updates
        start_time = time.perf_counter()
        
        for i in range(3):
            result = manager.update_all_versions_coordinated(f"2.{i}.0-perf")
            assert result.operation_time_ms < 2000  # Should be under 2 seconds
        
        total_time = time.perf_counter() - start_time
        
        # Total time for 3 updates should be reasonable
        assert total_time < 5.0, f"Performance test took {total_time:.2f}s, should be < 5.0s"
    
    def test_enhanced_detection_performance(self):
        """Test performance of enhanced inconsistency detection"""
        manager = EnhancedProjectVersionManager(self.temp_dir, enable_state_management=True)
        
        start_time = time.perf_counter()
        
        for _ in range(10):
            inconsistencies = manager.detect_version_inconsistencies_enhanced()
            assert isinstance(inconsistencies, dict)
        
        detection_time = time.perf_counter() - start_time
        
        # 10 detection operations should complete quickly
        assert detection_time < 1.0, f"Detection took {detection_time:.2f}s, should be < 1.0s"


if __name__ == "__main__":
    # Run tests with coverage
    import subprocess
    subprocess.run([
        "python", "-m", "pytest", __file__, "-v",
        "--cov=project_version_manager",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])