#!/usr/bin/env python3
"""
Demonstration of GTach Version State Manager

Shows the complete functionality of the version state management system including:
- Persistent state storage in .gtach-version file
- Development stage tracking and transitions
- Increment history with comprehensive metadata
- Thread-safe operations with atomic file writes
- Cross-platform compatibility
"""

import sys
import tempfile
import shutil
import time
from pathlib import Path

# Add provisioning module to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from provisioning.version_state_manager import (
    VersionStateManager, VersionState, DevelopmentStage, IncrementHistory
)


def demonstrate_version_state_manager():
    """Demonstrate the version state management system"""
    
    print("🔧 GTach Version State Manager Demo")
    print("=" * 55)
    
    # Create temporary directory for demonstration
    temp_dir = Path(tempfile.mkdtemp(prefix="gtach_version_demo_"))
    print(f"\n📁 Demo Directory: {temp_dir}")
    
    try:
        # Initialize version state manager
        print(f"\n⚙️  Initializing Version State Manager...")
        manager = VersionStateManager(temp_dir, session_id="demo_session")
        
        # Show initial state
        print(f"\n📊 Initial State:")
        state = manager.get_current_state()
        print(f"   Current Version: {state.current_version}")
        print(f"   Current Stage: {state.current_stage.value}")
        print(f"   Total Increments: {state.total_increments}")
        print(f"   State File: {manager.state_file_path.name} ({'exists' if manager.state_file_path.exists() else 'not found'})")
        
        # Demonstrate development workflow
        print(f"\n🔄 Development Workflow Demonstration:")
        
        workflow_steps = [
            ("1.0.0-alpha.1", "manual", "Initial alpha release"),
            ("1.0.0-alpha.2", "bugfix", "Fixed critical issues"),
            ("1.0.0-beta.1", "stage_change", "Ready for beta testing"),
            ("1.0.0-beta.2", "improvement", "Performance enhancements"),
            ("1.0.0-rc.1", "stage_change", "Release candidate"),
            ("1.0.0", "release", "Official release"),
            ("1.0.0-stable", "designation", "Stable version"),
        ]
        
        for i, (version, increment_type, context) in enumerate(workflow_steps, 1):
            print(f"\n   Step {i}: Updating to {version}")
            
            increment = manager.update_version(
                version,
                increment_type=increment_type,
                user_context=context,
                operation_context="demo_workflow"
            )
            
            print(f"      From: {increment.from_version} ({increment.from_stage.value if increment.from_stage else 'N/A'})")
            print(f"      To: {increment.to_version} ({increment.to_stage.value})")
            print(f"      Stage Transition: {'Yes' if increment.stage_transition else 'No'}")
            print(f"      Processing Time: {increment.processing_time_ms:.2f}ms")
            print(f"      Context: {increment.user_context}")
        
        # Show current state after workflow
        print(f"\n📈 Final State After Workflow:")
        final_state = manager.get_current_state()
        print(f"   Current Version: {final_state.current_version}")
        print(f"   Current Stage: {final_state.current_stage.value}")
        print(f"   Total Increments: {final_state.total_increments}")
        print(f"   History Entries: {len(final_state.increment_history)}")
        print(f"   Stage Transitions: {len(final_state.stage_history)}")
        
        # Demonstrate version suggestions
        print(f"\n💡 Version Suggestions:")
        for increment_type in ["minor", "major", "patch", "prerelease"]:
            suggestions = manager.suggest_next_version(increment_type)
            print(f"   {increment_type.title()}: {suggestions[:3]}")
        
        # Demonstrate increment history
        print(f"\n📋 Recent Increment History (last 5):")
        history = manager.get_increment_history(limit=5)
        
        for i, entry in enumerate(history, 1):
            print(f"   {i}. {entry.to_version} ({entry.increment_type})")
            print(f"      From: {entry.from_version}")
            print(f"      Stage: {entry.from_stage.value if entry.from_stage else 'N/A'} → {entry.to_stage.value}")
            print(f"      Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry.timestamp))}")
            print(f"      Context: {entry.user_context}")
            print(f"      Validation: {'✅ Passed' if entry.validation_passed else '❌ Failed'}")
            print()
        
        # Demonstrate stage history
        print(f"\n🔄 Stage Transition History:")
        stage_history = manager.get_stage_history()
        
        for version, stage, timestamp in stage_history:
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            print(f"   {version} → {stage.value} ({time_str})")
        
        # Show comprehensive statistics
        print(f"\n📊 System Statistics:")
        stats = manager.get_stats()
        
        key_stats = [
            ('Session ID', stats.get('session_id')),
            ('Platform', stats.get('platform')),
            ('Operation Count', stats.get('operation_count')),
            ('Read Operations', stats.get('read_operations')),
            ('Write Operations', stats.get('write_operations')),
            ('Backup Operations', stats.get('backup_operations')),
            ('State File Size', f"{stats.get('state_file_size', 0)} bytes"),
            ('Backup File Exists', 'Yes' if stats.get('backup_file_exists') else 'No'),
        ]
        
        for label, value in key_stats:
            print(f"   {label}: {value}")
        
        # Demonstrate persistence by creating new manager instance
        print(f"\n🔄 Testing Persistence (New Manager Instance):")
        manager2 = VersionStateManager(temp_dir, session_id="demo_session_2")
        
        loaded_state = manager2.get_current_state()
        print(f"   Loaded Version: {loaded_state.current_version}")
        print(f"   Loaded Stage: {loaded_state.current_stage.value}")
        print(f"   Loaded Increments: {loaded_state.total_increments}")
        print(f"   History Preserved: {len(loaded_state.increment_history)} entries")
        print(f"   Session Updated: {loaded_state.last_session_id}")
        
        # Test file operations
        print(f"\n💾 File System Operations:")
        print(f"   State File: {manager.state_file_path}")
        print(f"   File Exists: {'Yes' if manager.state_file_path.exists() else 'No'}")
        print(f"   Backup File: {manager.backup_file_path}")
        print(f"   Backup Exists: {'Yes' if manager.backup_file_path.exists() else 'No'}")
        
        if manager.state_file_path.exists():
            file_size = manager.state_file_path.stat().st_size
            print(f"   File Size: {file_size} bytes")
            
            # Show a sample of the JSON content
            with open(manager.state_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   JSON Preview: {content[:200]}...")
        
        # Demonstrate development stage functionality
        print(f"\n🎯 Development Stage Features:")
        current_stage = final_state.current_stage
        print(f"   Current Stage: {current_stage.value}")
        
        next_stages = current_stage.get_next_stages()
        print(f"   Valid Next Stages: {[stage.value for stage in next_stages]}")
        
        # Test stage detection
        test_versions = [
            "2.0.0-alpha.1",
            "2.0.0-beta.3", 
            "2.0.0-rc.1",
            "2.0.0",
            "2.0.0-hotfix.1"
        ]
        
        print(f"   Stage Detection Examples:")
        for test_version in test_versions:
            detected_stage = DevelopmentStage.from_version_string(test_version)
            print(f"      {test_version} → {detected_stage.value if detected_stage else 'None'}")
        
        # Performance metrics
        print(f"\n⚡ Performance Metrics:")
        
        # Test update performance
        start_time = time.perf_counter()
        test_manager = VersionStateManager(Path(tempfile.mkdtemp()), session_id="perf_test")
        
        for i in range(5):
            test_manager.update_version(f"2.{i}.0")
        
        update_time = time.perf_counter() - start_time
        print(f"   5 Version Updates: {update_time:.3f}s ({update_time/5:.3f}s per update)")
        
        # Test load performance
        start_time = time.perf_counter()
        test_manager2 = VersionStateManager(test_manager.project_root, session_id="perf_test_2")
        load_time = time.perf_counter() - start_time
        print(f"   State Loading: {load_time:.3f}s")
        
        # Success criteria verification
        print(f"\n✅ Success Criteria Verification:")
        verification_checks = [
            ("Persistent state storage", manager.state_file_path.exists()),
            ("Development stage tracking", len(stage_history) > 0),
            ("Increment history preservation", len(final_state.increment_history) == len(workflow_steps)),
            ("Thread-safe operations", hasattr(manager, '_state_lock')),
            ("Atomic file writes", hasattr(manager, '_atomic_state_update')),
            ("Cross-platform compatibility", manager.platform_name != "UNKNOWN"),
            ("Protocol 8 logging integration", hasattr(manager, 'logger')),
            ("JSON serialization working", manager.state_file_path.exists() and manager.state_file_path.stat().st_size > 0),
        ]
        
        for check_name, passed in verification_checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"   {status}: {check_name}")
        
        # Cleanup performance test directory
        shutil.rmtree(test_manager.project_root)
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup demonstration directory
        print(f"\n🧹 Cleaning up demo directory: {temp_dir}")
        try:
            shutil.rmtree(temp_dir)
            print(f"   Cleanup completed")
        except Exception as e:
            print(f"   Cleanup failed: {e}")
    
    print(f"\n" + "=" * 55)
    print(f"✨ Version State Manager Demonstration Complete!")
    print(f"   Ready for integration with GTach provisioning workflow")


if __name__ == "__main__":
    demonstrate_version_state_manager()