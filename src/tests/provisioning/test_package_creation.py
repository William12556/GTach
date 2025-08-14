#!/usr/bin/env python3
"""
Comprehensive test suite for Enhanced Package Creation with VersionStateManager Integration

Tests all components of the enhanced package creation workflow including
version state management integration, stage-based workflows, consistency enforcement,
and multi-package session handling.
"""

import pytest
import tempfile
import shutil
import sys
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

# Add provisioning module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "provisioning"))

# Import modules under test
from create_package import (
    handle_version_state_workflow,
    resolve_version_inconsistencies, 
    handle_stage_based_increment,
    show_version_history,
    get_manual_version_input,
    handle_post_package_version_update,
    handle_multi_package_session
)

from version_state_manager import VersionStateManager, VersionState, DevelopmentStage
from project_version_manager import VersionWorkflow


class TestVersionStateWorkflow:
    """Test handle_version_state_workflow functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.session_id = "test_session"
        self.mock_logger = Mock()
        
        # Create minimal project structure
        (self.temp_dir / "src" / "obdii").mkdir(parents=True)
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_workflow_use_current_version(self, mock_print, mock_input):
        """Test workflow when user chooses to use current version"""
        # Mock user selecting option 1 (use current version)
        mock_input.return_value = "1"
        
        # Call workflow
        result_version, state_manager = handle_version_state_workflow(
            self.temp_dir, self.session_id, self.mock_logger
        )
        
        # Should return current version from state manager
        assert result_version is not None
        assert state_manager is not None
        assert result_version == "0.1.0-dev"  # Default initial version
        
        # Logger should record selection
        self.mock_logger.info.assert_any_call(f"User selected current version: {result_version}")
    
    @patch('create_package.handle_stage_based_increment')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_workflow_stage_based_increment(self, mock_print, mock_input, mock_stage_increment):
        """Test workflow when user chooses stage-based increment"""
        # Mock user selecting option 2 (stage-based increment)
        mock_input.return_value = "2"
        mock_stage_increment.return_value = "1.0.0-alpha.1"
        
        result_version, state_manager = handle_version_state_workflow(
            self.temp_dir, self.session_id, self.mock_logger
        )
        
        assert result_version == "1.0.0-alpha.1"
        assert state_manager is not None
        
        # Should have called stage-based increment handler
        mock_stage_increment.assert_called_once()
    
    @patch('create_package.get_manual_version_input')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_workflow_manual_version_entry(self, mock_print, mock_input, mock_manual_input):
        """Test workflow when user chooses manual version entry"""
        # Mock user selecting option 3 (manual entry)
        mock_input.return_value = "3"
        mock_manual_input.return_value = "2.0.0-beta.1"
        
        result_version, state_manager = handle_version_state_workflow(
            self.temp_dir, self.session_id, self.mock_logger
        )
        
        assert result_version == "2.0.0-beta.1"
        assert state_manager is not None
        
        # Should have called manual input handler
        mock_manual_input.assert_called_once()
    
    @patch('create_package.show_version_history')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_workflow_view_history_then_exit(self, mock_print, mock_input, mock_show_history):
        """Test workflow when user views history then exits"""
        # Mock user selecting option 4 (history) then 5 (exit)
        mock_input.side_effect = ["4", "5"]
        
        result_version, state_manager = handle_version_state_workflow(
            self.temp_dir, self.session_id, self.mock_logger
        )
        
        assert result_version is None
        assert state_manager is not None
        
        # Should have shown history
        mock_show_history.assert_called_once()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_workflow_invalid_choice_handling(self, mock_print, mock_input):
        """Test workflow handles invalid choices gracefully"""
        # Mock user entering invalid choice, then valid choice
        mock_input.side_effect = ["invalid", "99", "1"]
        
        result_version, state_manager = handle_version_state_workflow(
            self.temp_dir, self.session_id, self.mock_logger
        )
        
        assert result_version is not None
        assert state_manager is not None


class TestVersionInconsistencyResolution:
    """Test resolve_version_inconsistencies functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_logger = Mock()
        
        # Create project structure
        (self.temp_dir / "src" / "obdii").mkdir(parents=True)
        (self.temp_dir / "src" / "provisioning").mkdir(parents=True)
        
        # Create test files with different versions
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach"
version = "1.0.0"
''')
        
        (self.temp_dir / "src" / "obdii" / "__init__.py").write_text('__version__ = "1.1.0"')
        (self.temp_dir / "src" / "provisioning" / "__init__.py").write_text('__version__ = "0.9.0"')
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_sync_to_state_version(self, mock_print, mock_input):
        """Test synchronizing project files to state manager version"""
        mock_input.return_value = "1"  # Option 1: Sync to state version
        
        state_manager = VersionStateManager(self.temp_dir)
        version_workflow = VersionWorkflow(self.temp_dir)
        
        # Update state manager to specific version
        state_manager.update_version("2.0.0-stable")
        
        result = resolve_version_inconsistencies(
            state_manager, version_workflow, self.mock_logger
        )
        
        assert result is True
        
        # Verify project files were synchronized
        updated_state = version_workflow.project_manager.get_current_versions()
        for file_path, version in updated_state.items():
            if version is not None:
                assert version == "2.0.0-stable"
    
    @patch('builtins.input')
    @patch('builtins.print') 
    def test_update_state_to_project_version(self, mock_print, mock_input):
        """Test updating state manager to most common project version"""
        mock_input.return_value = "2"  # Option 2: Update state to project version
        
        state_manager = VersionStateManager(self.temp_dir)
        version_workflow = VersionWorkflow(self.temp_dir)
        
        result = resolve_version_inconsistencies(
            state_manager, version_workflow, self.mock_logger
        )
        
        assert result is True
        
        # State manager should be updated
        current_state = state_manager.get_current_state()
        # Should be updated to one of the project versions (most common)
        assert current_state.current_version in ["1.0.0", "1.1.0", "0.9.0"]


class TestStageBasedIncrement:
    """Test handle_stage_based_increment functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_logger = Mock()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prerelease_increment(self, mock_print, mock_input):
        """Test prerelease increment selection"""
        state_manager = VersionStateManager(self.temp_dir)
        
        # Set up state with beta version
        state_manager.update_version("1.0.0-beta.1")
        
        # Mock user selecting first option (prerelease) and confirming
        mock_input.side_effect = ["1", "y"]
        
        result = handle_stage_based_increment(state_manager, self.mock_logger)
        
        assert result is not None
        assert "beta" in result.lower()
        
        # State should be updated
        current_state = state_manager.get_current_state()
        assert current_state.current_version == result
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_major_version_increment(self, mock_print, mock_input):
        """Test major version increment selection"""
        state_manager = VersionStateManager(self.temp_dir)
        
        # Set up state with release version
        state_manager.update_version("1.5.0")
        
        # Mock user selecting major increment option and confirming
        mock_input.side_effect = ["3", "y"]  # Assuming major is option 3
        
        result = handle_stage_based_increment(state_manager, self.mock_logger)
        
        assert result is not None
        assert result.startswith("2.")  # Should be major increment
    
    @patch('create_package.get_manual_version_input')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_custom_version_selection(self, mock_print, mock_input, mock_manual_input):
        """Test custom version selection"""
        state_manager = VersionStateManager(self.temp_dir)
        mock_manual_input.return_value = "3.0.0-alpha.1"
        
        # Mock user selecting custom version option
        mock_input.return_value = str(5)  # Assuming custom is last option
        
        result = handle_stage_based_increment(state_manager, self.mock_logger)
        
        assert result == "3.0.0-alpha.1"
        mock_manual_input.assert_called_once()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_increment_cancellation(self, mock_print, mock_input):
        """Test increment cancellation"""
        state_manager = VersionStateManager(self.temp_dir)
        
        # Mock user selecting cancel option
        mock_input.return_value = str(6)  # Assuming cancel is last option
        
        result = handle_stage_based_increment(state_manager, self.mock_logger)
        
        assert result is None


class TestManualVersionInput:
    """Test get_manual_version_input functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_logger = Mock()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_valid_version_input(self, mock_print, mock_input):
        """Test valid version input and confirmation"""
        # Mock user entering valid version and confirming
        mock_input.side_effect = ["1.2.3-alpha.1", "y"]
        
        result = get_manual_version_input(self.mock_logger)
        
        assert result == "1.2.3-alpha.1"
        self.mock_logger.info.assert_called_with(
            "Manual version selected: 1.2.3-alpha.1 (manual)"
        )
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_invalid_then_valid_version(self, mock_print, mock_input):
        """Test invalid version followed by valid version"""
        # Mock user entering invalid version, then valid version and confirming
        mock_input.side_effect = ["invalid-version", "2.0.0", "yes"]
        
        result = get_manual_version_input(self.mock_logger)
        
        assert result == "2.0.0"
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_user_cancellation(self, mock_print, mock_input):
        """Test user cancellation"""
        mock_input.return_value = "cancel"
        
        result = get_manual_version_input(self.mock_logger)
        
        assert result is None
        self.mock_logger.info.assert_called_with(
            "Manual version input cancelled (manual)"
        )
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_max_attempts_exceeded(self, mock_print, mock_input):
        """Test behavior when max attempts are exceeded"""
        # Mock user entering invalid versions for all attempts
        mock_input.return_value = "invalid-version"
        
        result = get_manual_version_input(self.mock_logger)
        
        assert result is None
        self.mock_logger.warning.assert_called()


class TestPostPackageVersionUpdate:
    """Test handle_post_package_version_update functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_logger = Mock()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_no_update_when_versions_match(self):
        """Test no update prompt when package version matches state version"""
        state_manager = VersionStateManager(self.temp_dir)
        current_state = state_manager.get_current_state()
        package_version = current_state.current_version
        
        # Should return without prompting since versions match
        with patch('builtins.input') as mock_input:
            handle_post_package_version_update(
                state_manager, package_version, self.mock_logger
            )
            
            # Input should not be called
            mock_input.assert_not_called()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_update_state_version(self, mock_print, mock_input):
        """Test updating state manager to package version"""
        state_manager = VersionStateManager(self.temp_dir)
        package_version = "2.0.0-release"
        
        # Mock user accepting update but declining file sync
        mock_input.side_effect = ["y", "n"]
        
        handle_post_package_version_update(
            state_manager, package_version, self.mock_logger
        )
        
        # State should be updated
        current_state = state_manager.get_current_state()
        assert current_state.current_version == package_version
        
        # Logger should record the update
        self.mock_logger.info.assert_any_call(
            f"Post-package version update: 0.1.0-dev → {package_version}"
        )
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_decline_update(self, mock_print, mock_input):
        """Test declining post-package update"""
        state_manager = VersionStateManager(self.temp_dir)
        original_version = state_manager.get_current_state().current_version
        package_version = "2.0.0-release"
        
        # Mock user declining update
        mock_input.return_value = "n"
        
        handle_post_package_version_update(
            state_manager, package_version, self.mock_logger
        )
        
        # State should remain unchanged
        current_state = state_manager.get_current_state()
        assert current_state.current_version == original_version
        
        self.mock_logger.info.assert_called_with("User declined post-package version update")


class TestMultiPackageSession:
    """Test handle_multi_package_session functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_logger = Mock()
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_decline_another_package(self, mock_print, mock_input):
        """Test declining to create another package"""
        state_manager = VersionStateManager(self.temp_dir)
        
        # Mock user declining another package
        mock_input.return_value = "n"
        
        result = handle_multi_package_session(state_manager, self.mock_logger)
        
        assert result is False
        self.mock_logger.info.assert_called_with(
            "User declined multi-package session continuation"
        )
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_accept_with_patch_increment(self, mock_print, mock_input):
        """Test accepting another package with patch increment"""
        state_manager = VersionStateManager(self.temp_dir)
        
        # Set up state with a version
        state_manager.update_version("1.0.0")
        
        # Mock user accepting another package, wanting increment, choosing patch
        mock_input.side_effect = ["y", "y", "1"]
        
        result = handle_multi_package_session(state_manager, self.mock_logger)
        
        assert result is True
        
        # Version should be incremented
        current_state = state_manager.get_current_state()
        assert current_state.current_version.startswith("1.0.")
        assert current_state.current_version != "1.0.0"  # Should be incremented
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_accept_without_increment(self, mock_print, mock_input):
        """Test accepting another package without increment"""
        state_manager = VersionStateManager(self.temp_dir)
        original_version = state_manager.get_current_state().current_version
        
        # Mock user accepting another package but declining increment
        mock_input.side_effect = ["y", "n"]
        
        result = handle_multi_package_session(state_manager, self.mock_logger)
        
        assert result is True
        
        # Version should remain unchanged
        current_state = state_manager.get_current_state()
        assert current_state.current_version == original_version


class TestShowVersionHistory:
    """Test show_version_history functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('builtins.print')
    def test_show_history_with_increments(self, mock_print):
        """Test showing version history with increment data"""
        state_manager = VersionStateManager(self.temp_dir)
        
        # Create some history
        state_manager.update_version("1.0.0-alpha.1", increment_type="initial")
        state_manager.update_version("1.0.0-beta.1", increment_type="stage_change") 
        state_manager.update_version("1.0.0", increment_type="release")
        
        show_version_history(state_manager)
        
        # Should have printed version information
        mock_print.assert_called()
        
        # Check that key information was displayed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        
        # Should contain current version info
        assert any("Current Version: 1.0.0" in call for call in print_calls)
        
        # Should contain increment history
        assert any("Recent Increments" in call for call in print_calls)
        
        # Should contain stage transitions
        assert any("Stage Transitions" in call for call in print_calls)
        
        # Should contain statistics
        assert any("Statistics" in call for call in print_calls)
    
    @patch('builtins.print')
    def test_show_empty_history(self, mock_print):
        """Test showing version history with no increments"""
        state_manager = VersionStateManager(self.temp_dir)
        
        show_version_history(state_manager)
        
        # Should still show basic information
        mock_print.assert_called()
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        
        # Should contain current version (default)
        assert any("Current Version: 0.1.0-dev" in call for call in print_calls)
        
        # Should contain statistics even with no history
        assert any("Statistics" in call for call in print_calls)


class TestIntegrationWorkflows:
    """Integration tests for complete workflows"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create project structure
        (self.temp_dir / "src" / "obdii").mkdir(parents=True)
        (self.temp_dir / "src" / "provisioning").mkdir(parents=True)
        
        # Create test files
        (self.temp_dir / "pyproject.toml").write_text('''[project]
name = "gtach"
version = "1.0.0"
''')
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_complete_workflow_new_version(self, mock_print, mock_input):
        """Test complete workflow with new version creation"""
        session_id = "integration_test"
        mock_logger = Mock()
        
        # Mock user workflow: stage-based increment, select first option, confirm
        mock_input.side_effect = ["2", "1", "y"]
        
        # Execute workflow
        selected_version, state_manager = handle_version_state_workflow(
            self.temp_dir, session_id, mock_logger
        )
        
        assert selected_version is not None
        assert state_manager is not None
        
        # Verify state was updated
        current_state = state_manager.get_current_state()
        assert current_state.current_version == selected_version
        assert current_state.total_increments > 0
    
    @patch('builtins.input') 
    @patch('builtins.print')
    def test_workflow_with_inconsistency_resolution(self, mock_print, mock_input):
        """Test workflow with version inconsistency resolution"""
        session_id = "integration_test"
        mock_logger = Mock()
        
        # Create inconsistent project files
        (self.temp_dir / "setup.py").write_text('''setup(
    name="gtach",
    version="2.0.0",
)''')
        
        # Mock user workflow: resolve inconsistencies (option 1), then use current version
        mock_input.side_effect = ["1", "1"] 
        
        selected_version, state_manager = handle_version_state_workflow(
            self.temp_dir, session_id, mock_logger
        )
        
        assert selected_version is not None
        assert state_manager is not None


if __name__ == "__main__":
    # Run tests with coverage
    import subprocess
    subprocess.run([
        "python", "-m", "pytest", __file__, "-v",
        "--cov=create_package",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])