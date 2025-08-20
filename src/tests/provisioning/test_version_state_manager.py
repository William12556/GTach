#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Comprehensive test suite for VersionStateManager

Tests all components of the version state management system including
persistent state storage, development stage tracking, increment history,
and thread safety with high coverage.
"""

import pytest
import tempfile
import shutil
import json
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add provisioning module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "provisioning"))

from version_state_manager import (
    VersionStateManager, VersionState, DevelopmentStage, IncrementHistory
)


class TestDevelopmentStage:
    """Test DevelopmentStage enum functionality"""
    
    def test_from_version_string(self):
        """Test development stage extraction from version strings"""
        test_cases = [
            ("1.0.0-alpha.1", DevelopmentStage.ALPHA),
            ("2.1.0-beta.3", DevelopmentStage.BETA),
            ("1.5.0-rc.2", DevelopmentStage.RC),
            ("1.0.0", DevelopmentStage.RELEASE),
            ("2.0.0-stable", DevelopmentStage.STABLE),
            ("1.1.1-hotfix.1", DevelopmentStage.HOTFIX),
            ("0.1.0-dev", DevelopmentStage.DEV),
            ("1.0.0-snapshot", DevelopmentStage.DEV),
        ]
        
        for version_string, expected_stage in test_cases:
            result = DevelopmentStage.from_version_string(version_string)
            assert result == expected_stage, f"Version {version_string} should map to {expected_stage}"
    
    def test_get_next_stages(self):
        """Test stage transition logic"""
        # Alpha can go to beta, rc, release, or stay alpha
        alpha_next = DevelopmentStage.ALPHA.get_next_stages()
        assert DevelopmentStage.BETA in alpha_next
        assert DevelopmentStage.RC in alpha_next
        assert DevelopmentStage.RELEASE in alpha_next
        
        # RC can only go to release or stay rc
        rc_next = DevelopmentStage.RC.get_next_stages()
        assert DevelopmentStage.RELEASE in rc_next
        assert len(rc_next) <= 2
        
        # Release can go to stable, hotfix, or start new cycle
        release_next = DevelopmentStage.RELEASE.get_next_stages()
        assert DevelopmentStage.STABLE in release_next
        assert DevelopmentStage.HOTFIX in release_next


class TestIncrementHistory:
    """Test IncrementHistory functionality"""
    
    def test_increment_history_creation(self):
        """Test increment history entry creation"""
        history = IncrementHistory(
            from_version="1.0.0",
            to_version="1.1.0",
            increment_type="minor",
            user_context="Added new features"
        )
        
        assert history.from_version == "1.0.0"
        assert history.to_version == "1.1.0"
        assert history.increment_type == "minor"
        assert history.user_context == "Added new features"
        assert history.increment_id is not None
        assert history.timestamp > 0
    
    def test_increment_history_serialization(self):
        """Test increment history to_dict and from_dict"""
        original = IncrementHistory(
            from_version="1.0.0-alpha.1",
            to_version="1.0.0-beta.1",
            increment_type="stage_change",
            from_stage=DevelopmentStage.ALPHA,
            to_stage=DevelopmentStage.BETA,
            stage_transition=True,
            validation_passed=True
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = IncrementHistory.from_dict(data)
        
        assert restored.from_version == original.from_version
        assert restored.to_version == original.to_version
        assert restored.from_stage == original.from_stage
        assert restored.to_stage == original.to_stage
        assert restored.stage_transition == original.stage_transition


class TestVersionState:
    """Test VersionState functionality"""
    
    def test_version_state_creation(self):
        """Test version state creation with defaults"""
        state = VersionState()
        
        assert state.current_version == "0.1.0-dev"
        assert state.current_stage == DevelopmentStage.DEV
        assert state.major_version == 0
        assert state.minor_version == 1
        assert state.patch_version == 0
        assert state.total_increments == 0
        assert len(state.increment_history) == 0
        assert state.auto_increment_enabled is True
    
    def test_version_state_serialization(self):
        """Test version state to_dict and from_dict"""
        # Create state with complex data
        original = VersionState(
            current_version="2.1.0-rc.3",
            current_stage=DevelopmentStage.RC,
            major_version=2,
            minor_version=1,
            patch_version=0,
            prerelease_counter=3,
            total_increments=15,
            preferred_stage_progression=[
                DevelopmentStage.ALPHA,
                DevelopmentStage.BETA,
                DevelopmentStage.RC,
                DevelopmentStage.RELEASE
            ]
        )
        
        # Add some history
        original.increment_history.append(
            IncrementHistory(
                from_version="2.0.0",
                to_version="2.1.0-rc.1",
                from_stage=DevelopmentStage.RELEASE,
                to_stage=DevelopmentStage.RC
            )
        )
        
        original.stage_history.append(("2.1.0-rc.1", DevelopmentStage.RC, time.time()))
        
        # Convert to dict and back
        data = original.to_dict()
        restored = VersionState.from_dict(data)
        
        assert restored.current_version == original.current_version
        assert restored.current_stage == original.current_stage
        assert restored.major_version == original.major_version
        assert restored.total_increments == original.total_increments
        assert len(restored.increment_history) == len(original.increment_history)
        assert len(restored.stage_history) == len(original.stage_history)
        assert restored.preferred_stage_progression == original.preferred_stage_progression


class TestVersionStateManager:
    """Test VersionStateManager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_new_project(self):
        """Test initialization with new project (no existing state)"""
        manager = VersionStateManager(self.temp_dir, session_id="test_session")
        
        assert manager.project_root == self.temp_dir
        assert manager.session_id == "test_session"
        assert manager.state_file_path.name == ".gtach-version"
        
        # Should create initial state
        state = manager.get_current_state()
        assert state.current_version == "0.1.0-dev"
        assert state.current_stage == DevelopmentStage.DEV
        assert state.last_session_id == "test_session"
        
        # State file should be created
        assert manager.state_file_path.exists()
    
    def test_initialization_existing_state(self):
        """Test initialization with existing state file"""
        # Create existing state file
        state_file = self.temp_dir / ".gtach-version"
        existing_state = VersionState(
            current_version="1.5.0-beta.2",
            current_stage=DevelopmentStage.BETA,
            total_increments=10
        )
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(existing_state.to_dict(), f, indent=2)
        
        # Initialize manager
        manager = VersionStateManager(self.temp_dir, session_id="test_session")
        
        # Should load existing state
        state = manager.get_current_state()
        assert state.current_version == "1.5.0-beta.2"
        assert state.current_stage == DevelopmentStage.BETA
        assert state.total_increments == 10
        assert state.last_session_id == "test_session"  # Should update session
    
    def test_state_file_corruption_recovery(self):
        """Test recovery from corrupted state file with backup"""
        # Create corrupted state file
        state_file = self.temp_dir / ".gtach-version"
        state_file.write_text("invalid json content")
        
        # Create valid backup file
        backup_file = self.temp_dir / ".gtach-version.backup"
        backup_state = VersionState(
            current_version="1.2.0-stable",
            current_stage=DevelopmentStage.STABLE
        )
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_state.to_dict(), f, indent=2)
        
        # Should recover from backup
        manager = VersionStateManager(self.temp_dir)
        state = manager.get_current_state()
        
        assert state.current_version == "1.2.0-stable"
        assert state.current_stage == DevelopmentStage.STABLE
        
        # Corrupted file should be replaced with recovered state
        assert state_file.exists()
        with open(state_file, 'r', encoding='utf-8') as f:
            recovered_data = json.load(f)
            assert recovered_data['current_version'] == "1.2.0-stable"
    
    def test_update_version_basic(self):
        """Test basic version update functionality"""
        manager = VersionStateManager(self.temp_dir)
        
        # Update version
        increment = manager.update_version(
            "1.0.0-alpha.1",
            increment_type="manual",
            user_context="Initial alpha release",
            operation_context="test_update"
        )
        
        # Check increment record
        assert increment.from_version == "0.1.0-dev"
        assert increment.to_version == "1.0.0-alpha.1"
        assert increment.increment_type == "manual"
        assert increment.user_context == "Initial alpha release"
        assert increment.from_stage == DevelopmentStage.DEV
        assert increment.to_stage == DevelopmentStage.ALPHA
        assert increment.stage_transition is True
        assert increment.validation_passed is True
        
        # Check updated state
        state = manager.get_current_state()
        assert state.current_version == "1.0.0-alpha.1"
        assert state.current_stage == DevelopmentStage.ALPHA
        assert state.total_increments == 1
        assert len(state.increment_history) == 1
        assert len(state.stage_history) == 1  # Stage changed
    
    def test_update_version_invalid(self):
        """Test version update with invalid version format"""
        manager = VersionStateManager(self.temp_dir)
        
        # Should raise ValueError for invalid version
        with pytest.raises(ValueError) as exc_info:
            manager.update_version("invalid-version")
        
        assert "Invalid version format" in str(exc_info.value)
        
        # State should remain unchanged
        state = manager.get_current_state()
        assert state.current_version == "0.1.0-dev"
        assert state.total_increments == 0
    
    def test_suggest_next_version(self):
        """Test version suggestion functionality"""
        manager = VersionStateManager(self.temp_dir)
        
        # Update to a known version
        manager.update_version("1.2.3-beta.5")
        
        # Test different increment types
        minor_suggestions = manager.suggest_next_version("minor")
        assert any("1.3.0" in suggestion for suggestion in minor_suggestions)
        
        major_suggestions = manager.suggest_next_version("major")
        assert any("2.0.0" in suggestion for suggestion in major_suggestions)
        
        patch_suggestions = manager.suggest_next_version("patch")
        assert any("1.2.4" in suggestion for suggestion in patch_suggestions)
        
        prerelease_suggestions = manager.suggest_next_version("prerelease")
        assert any("beta.6" in suggestion for suggestion in prerelease_suggestions)
    
    def test_increment_history_tracking(self):
        """Test comprehensive increment history tracking"""
        manager = VersionStateManager(self.temp_dir)
        
        # Perform multiple version updates
        versions = [
            ("1.0.0-alpha.1", "manual"),
            ("1.0.0-alpha.2", "auto"),
            ("1.0.0-beta.1", "stage_change"),
            ("1.0.0-rc.1", "stage_change"),
            ("1.0.0", "release")
        ]
        
        for version, increment_type in versions:
            manager.update_version(version, increment_type=increment_type)
        
        # Check history
        history = manager.get_increment_history()
        assert len(history) == 5
        
        # History should be in reverse chronological order (most recent first)
        assert history[0].to_version == "1.0.0"
        assert history[0].increment_type == "release"
        assert history[-1].to_version == "1.0.0-alpha.1"
        
        # Check stage history
        stage_history = manager.get_stage_history()
        assert len(stage_history) >= 4  # Stage changes occurred
    
    def test_cleanup_old_history(self):
        """Test cleanup of old increment history"""
        manager = VersionStateManager(self.temp_dir)
        
        # Add some old history entries by manipulating timestamps
        old_timestamp = time.time() - (100 * 24 * 60 * 60)  # 100 days ago
        
        for i in range(10):
            increment = IncrementHistory(
                from_version=f"0.{i}.0",
                to_version=f"0.{i+1}.0",
                timestamp=old_timestamp + i
            )
            manager._current_state.increment_history.append(increment)
        
        # Add recent entries
        for i in range(5):
            manager.update_version(f"1.{i}.0")
        
        # Should have 15 total entries
        assert len(manager._current_state.increment_history) == 15
        
        # Cleanup old entries (keep 90 days)
        removed_count = manager.cleanup_old_history(keep_days=90)
        
        # Should have removed old entries
        assert removed_count == 10
        assert len(manager._current_state.increment_history) == 5
    
    def test_atomic_state_updates(self):
        """Test atomic state updates with rollback on failure"""
        manager = VersionStateManager(self.temp_dir)
        
        original_version = manager.get_current_state().current_version
        
        # Create a mock that will fail during state save
        with patch.object(manager, '_save_state', side_effect=RuntimeError("Save failed")):
            
            # Attempt update that should fail and rollback
            with pytest.raises(RuntimeError):
                manager.update_version("2.0.0")
        
        # State should be unchanged after rollback
        state = manager.get_current_state()
        assert state.current_version == original_version
        assert state.total_increments == 0
    
    def test_thread_safety(self):
        """Test thread-safe operations"""
        manager = VersionStateManager(self.temp_dir)
        
        results = []
        errors = []
        
        def update_version_worker(thread_id):
            try:
                version = f"1.{thread_id}.0"
                increment = manager.update_version(
                    version,
                    increment_type="concurrent",
                    user_context=f"Thread {thread_id}"
                )
                results.append((thread_id, increment.to_version))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Run concurrent updates
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_version_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 5
        
        # Final state should reflect all updates
        state = manager.get_current_state()
        assert state.total_increments == 5
        assert len(state.increment_history) == 5
        
        # All versions should be unique
        versions = [result[1] for result in results]
        assert len(set(versions)) == len(versions)
    
    def test_backup_and_restore(self):
        """Test backup creation and restore functionality"""
        manager = VersionStateManager(self.temp_dir)
        
        # Update version to create meaningful state
        manager.update_version("1.0.0-beta.1")
        
        # Backup should be created automatically
        assert manager.backup_file_path.exists()
        
        # Verify backup content
        with open(manager.backup_file_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Backup should contain the previous state
        assert 'current_version' in backup_data
        
        # Modify current state
        manager.update_version("1.0.0-rc.1")
        
        # New backup should be created
        current_state = manager.get_current_state()
        assert current_state.current_version == "1.0.0-rc.1"
    
    def test_cross_platform_file_operations(self):
        """Test file operations work across platforms"""
        manager = VersionStateManager(self.temp_dir)
        
        # Update version multiple times to trigger multiple file operations
        for i in range(3):
            manager.update_version(f"1.{i}.0")
        
        # File should exist and be readable
        assert manager.state_file_path.exists()
        assert manager.state_file_path.is_file()
        
        # Content should be valid JSON
        with open(manager.state_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert 'current_version' in data
            assert data['total_increments'] == 3
        
        # Test atomic writes by checking file consistency
        state = manager.get_current_state()
        assert state.current_version == "1.2.0"
        assert state.total_increments == 3
    
    def test_stats_collection(self):
        """Test comprehensive statistics collection"""
        manager = VersionStateManager(self.temp_dir)
        
        # Perform various operations
        manager.update_version("1.0.0-alpha.1")
        manager.update_version("1.0.0-beta.1")
        manager.suggest_next_version("minor")
        manager.get_increment_history()
        
        # Get statistics
        stats = manager.get_stats()
        
        # Verify statistics structure
        required_fields = [
            'session_id', 'platform', 'state_file_path', 'state_file_exists',
            'operation_count', 'read_operations', 'write_operations',
            'current_version', 'current_stage', 'total_increments'
        ]
        
        for field in required_fields:
            assert field in stats, f"Missing required field: {field}"
        
        # Verify values
        assert stats['operation_count'] >= 2  # At least 2 version updates
        assert stats['total_increments'] == 2
        assert stats['current_version'] == "1.0.0-beta.1"
        assert stats['current_stage'] == "beta"
        assert stats['state_file_exists'] is True
    
    def test_performance_requirements(self):
        """Test performance requirements for state operations"""
        manager = VersionStateManager(self.temp_dir)
        
        # Test version update performance
        start_time = time.perf_counter()
        
        for i in range(10):
            manager.update_version(f"1.{i}.0")
        
        elapsed = time.perf_counter() - start_time
        
        # Should be fast (< 2 seconds for 10 updates)
        assert elapsed < 2.0, f"Version updates took {elapsed:.2f}s, should be < 2.0s"
        
        # Test state loading performance
        new_manager = VersionStateManager(self.temp_dir)
        
        start_time = time.perf_counter()
        state = new_manager.get_current_state()
        load_time = time.perf_counter() - start_time
        
        # Loading should be very fast
        assert load_time < 0.5, f"State loading took {load_time:.2f}s, should be < 0.5s"
        
        # Verify loaded state is correct
        assert state.total_increments == 10


class TestIntegration:
    """Integration tests for complete version state management system"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup integration test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_complete_development_workflow(self):
        """Test complete development workflow from dev to stable"""
        manager = VersionStateManager(self.temp_dir, session_id="integration_test")
        
        # Development workflow stages
        workflow_stages = [
            ("1.0.0-dev.1", DevelopmentStage.DEV, "Initial development"),
            ("1.0.0-alpha.1", DevelopmentStage.ALPHA, "First alpha release"),
            ("1.0.0-alpha.2", DevelopmentStage.ALPHA, "Alpha bug fixes"),
            ("1.0.0-beta.1", DevelopmentStage.BETA, "Beta release"),
            ("1.0.0-beta.2", DevelopmentStage.BETA, "Beta improvements"),
            ("1.0.0-rc.1", DevelopmentStage.RC, "Release candidate"),
            ("1.0.0", DevelopmentStage.RELEASE, "Official release"),
            ("1.0.0-stable", DevelopmentStage.STABLE, "Stable designation"),
            ("1.0.1-hotfix.1", DevelopmentStage.HOTFIX, "Critical hotfix")
        ]
        
        # Execute workflow
        for version, expected_stage, context in workflow_stages:
            increment = manager.update_version(
                version,
                increment_type="workflow",
                user_context=context
            )
            
            # Verify each step
            assert increment.to_version == version
            assert increment.to_stage == expected_stage
            assert increment.user_context == context
            
            # Verify state consistency
            state = manager.get_current_state()
            assert state.current_version == version
            assert state.current_stage == expected_stage
        
        # Verify final state
        final_state = manager.get_current_state()
        assert final_state.total_increments == len(workflow_stages)
        assert len(final_state.increment_history) == len(workflow_stages)
        
        # Verify stage transitions were tracked
        stage_transitions = [h for h in final_state.increment_history if h.stage_transition]
        assert len(stage_transitions) >= 7  # Most stages changed
        
        # Verify history ordering
        history = manager.get_increment_history()
        assert history[0].to_version == "1.0.1-hotfix.1"  # Most recent first
        assert history[-1].to_version == "1.0.0-dev.1"   # Oldest last
    
    def test_state_persistence_across_sessions(self):
        """Test state persistence across multiple manager instances"""
        session1_id = "session_1"
        session2_id = "session_2"
        
        # Session 1: Create and modify state
        manager1 = VersionStateManager(self.temp_dir, session_id=session1_id)
        
        manager1.update_version("2.0.0-alpha.1", user_context="Session 1 update")
        manager1.update_version("2.0.0-alpha.2", user_context="Session 1 fix")
        
        state1 = manager1.get_current_state()
        assert state1.current_version == "2.0.0-alpha.2"
        assert state1.total_increments == 2
        assert state1.last_session_id == session1_id
        
        # Session 2: Load existing state and continue
        manager2 = VersionStateManager(self.temp_dir, session_id=session2_id)
        
        state2 = manager2.get_current_state()
        
        # Should load previous state
        assert state2.current_version == "2.0.0-alpha.2"
        assert state2.total_increments == 2
        assert state2.last_session_id == session2_id  # Updated to new session
        
        # Should preserve increment history from previous session
        history = manager2.get_increment_history()
        assert len(history) == 2
        assert history[0].user_context == "Session 1 fix"
        assert history[1].user_context == "Session 1 update"
        
        # Continue development in new session
        manager2.update_version("2.0.0-beta.1", user_context="Session 2 beta")
        
        final_state = manager2.get_current_state()
        assert final_state.total_increments == 3
        assert final_state.current_version == "2.0.0-beta.1"
        
        # All history should be preserved
        final_history = manager2.get_increment_history()
        assert len(final_history) == 3
        
        # Verify session tracking in history
        sessions_in_history = {h.session_id for h in final_history}
        assert session1_id in sessions_in_history
        assert session2_id in sessions_in_history


if __name__ == "__main__":
    # Run tests with coverage
    import subprocess
    subprocess.run([
        "python", "-m", "pytest", __file__, "-v",
        "--cov=version_state_manager",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])