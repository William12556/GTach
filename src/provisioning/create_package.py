#!/usr/bin/env python3
"""
Enhanced GTach Application Package Creator with Version State Management

Production script for creating GTach deployment packages with comprehensive 
version state management, stage-based workflows, and intelligent increment suggestions.

Usage:
    python create_package.py

Features:
- Comprehensive version state management with persistent storage
- Stage-based development workflow (dev → alpha → beta → rc → release → stable)
- Intelligent increment suggestions based on current stage
- Project consistency enforcement with version synchronization
- Multi-package session handling with increment tracking
- Optional project version updates after package creation
- Backward compatibility with manual version input
- Comprehensive logging and error handling per Protocol 8

Protocol Compliance:
- Protocol 8: Comprehensive logging and debug standards
- Protocol 6: Cross-platform development standards
- Protocol 2: Systematic iteration workflow
"""

import sys
import logging
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from provisioning import (
    PackageCreator, PackageConfig, PackageManifest,
    ConfigProcessor, PlatformConfig,
    ArchiveManager, ArchiveConfig, CompressionFormat,
    VersionStateManager, VersionState, DevelopmentStage
)
from provisioning.logging_config import setup_provisioning_logging, cleanup_provisioning_logging
from provisioning.version_manager import VersionManager
from provisioning.project_version_manager import VersionWorkflow


def handle_version_state_workflow(project_root: Path, 
                                session_id: str, 
                                logger: logging.Logger) -> Tuple[Optional[str], VersionStateManager]:
    """
    Handle comprehensive version state workflow with stage-based management.
    
    Args:
        project_root: Project root directory
        session_id: Current session identifier
        logger: Logger instance for operation tracking
        
    Returns:
        Tuple of (selected_version, state_manager)
    """
    logger.info("Starting version state workflow")
    
    try:
        # Initialize version state manager
        state_manager = VersionStateManager(project_root, session_id=session_id)
        current_state = state_manager.get_current_state()
        
        print(f"\n🔧 GTach Version State Management")
        print(f"=" * 50)
        
        # Show current version state
        print(f"\n📊 Current Version State:")
        print(f"   Version: {current_state.current_version}")
        print(f"   Stage: {current_state.current_stage.value}")
        print(f"   Total Increments: {current_state.total_increments}")
        
        # Show recent history if available
        if current_state.total_increments > 0:
            print(f"   Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_state.last_updated))}")
            
            recent_history = state_manager.get_increment_history(limit=3)
            if recent_history:
                print(f"\n📋 Recent Changes:")
                for i, entry in enumerate(recent_history, 1):
                    print(f"   {i}. {entry.from_version} → {entry.to_version} ({entry.increment_type})")
        
        # Check for project consistency issues
        version_workflow = VersionWorkflow(project_root)
        project_stats = version_workflow.project_manager.get_stats()
        
        if project_stats.get('has_inconsistencies', False):
            logger.warning("Project version inconsistencies detected")
            consistency_resolved = resolve_version_inconsistencies(
                state_manager, version_workflow, logger
            )
            if not consistency_resolved:
                return None, state_manager
        else:
            print(f"✅ Project files are version-consistent")
        
        # Offer version management options
        print(f"\n🎯 Version Management Options:")
        print(f"1. Use current version ({current_state.current_version})")
        print(f"2. Increment version (stage-based suggestions)")
        print(f"3. Manual version entry")
        print(f"4. View version history")
        print(f"5. Exit")
        
        while True:
            choice = input(f"\nSelect option [1-5]: ").strip()
            
            if choice == "1":
                logger.info(f"User selected current version: {current_state.current_version}")
                return current_state.current_version, state_manager
            
            elif choice == "2":
                # Stage-based increment suggestions
                selected_version = handle_stage_based_increment(state_manager, logger)
                if selected_version:
                    return selected_version, state_manager
                # Continue loop if user cancelled
                
            elif choice == "3":
                # Manual version entry with fallback
                selected_version = get_manual_version_input(logger)
                if selected_version:
                    # Record manual version in state manager
                    state_manager.update_version(
                        selected_version,
                        increment_type="manual",
                        user_context="Manual version entry via package creation",
                        operation_context="package_creation_manual"
                    )
                    return selected_version, state_manager
                # Continue loop if user cancelled
                
            elif choice == "4":
                # Show detailed version history
                show_version_history(state_manager)
                # Continue loop after showing history
                
            elif choice == "5":
                logger.info("User exited version state workflow")
                return None, state_manager
                
            else:
                print("❌ Invalid choice. Please select 1-5.")
        
    except Exception as e:
        logger.error(f"Version state workflow failed: {e}", exc_info=True)
        print(f"❌ Version state workflow error: {e}")
        print("Falling back to manual version input...")
        
        # Fallback to manual version input
        fallback_version = get_manual_version_input(logger)
        if fallback_version:
            # Create minimal state manager for tracking
            try:
                state_manager = VersionStateManager(project_root, session_id=session_id)
                state_manager.update_version(
                    fallback_version,
                    increment_type="fallback",
                    user_context="Fallback after state workflow error",
                    operation_context="package_creation_fallback"
                )
                return fallback_version, state_manager
            except Exception:
                # Ultimate fallback - return version without state tracking
                return fallback_version, None
        
        return None, None


def resolve_version_inconsistencies(state_manager: VersionStateManager,
                                  version_workflow: VersionWorkflow,
                                  logger: logging.Logger) -> bool:
    """
    Resolve project version inconsistencies with user guidance.
    
    Args:
        state_manager: Version state manager instance
        version_workflow: Version workflow manager
        logger: Logger instance
        
    Returns:
        True if inconsistencies were resolved, False otherwise
    """
    logger.info("Resolving project version inconsistencies")
    
    stats = version_workflow.project_manager.get_stats()
    version_groups = stats.get('version_groups', {})
    
    print(f"\n⚠️  Project Version Inconsistencies Detected!")
    print(f"Found {len(version_groups)} different versions across project files:")
    
    for version, count in version_groups.items():
        print(f"   • {version}: {count} files")
    
    current_state = state_manager.get_current_state()
    state_version = current_state.current_version
    
    print(f"\nVersion State Manager version: {state_version}")
    
    print(f"\nResolution Options:")
    print(f"1. Synchronize all project files to state manager version ({state_version})")
    print(f"2. Update state manager to most common project version")
    print(f"3. Set new version for entire project (interactive)")
    print(f"4. Continue with inconsistencies (not recommended)")
    
    choice = input(f"\nSelect resolution [1-4]: ").strip()
    
    try:
        if choice == "1":
            # Sync project files to state manager version
            logger.info(f"Synchronizing project files to state version: {state_version}")
            print(f"Synchronizing all project files to: {state_version}")
            
            version_workflow.project_manager.update_all_versions(state_version)
            print(f"✅ Project synchronized to state manager version")
            return True
            
        elif choice == "2":
            # Update state manager to most common project version
            most_common_version = max(version_groups.items(), key=lambda x: x[1])[0]
            logger.info(f"Updating state manager to most common version: {most_common_version}")
            print(f"Updating state manager to most common project version: {most_common_version}")
            
            state_manager.update_version(
                most_common_version,
                increment_type="synchronization",
                user_context="Synchronized to most common project version",
                operation_context="consistency_resolution"
            )
            print(f"✅ State manager updated to project version")
            return True
            
        elif choice == "3":
            # Interactive version setting
            logger.info("Starting interactive version resolution")
            print(f"Setting new version for entire project...")
            
            selected_version = version_workflow.interactive_version_update()
            if selected_version:
                # Update state manager to match
                state_manager.update_version(
                    selected_version,
                    increment_type="project_sync",
                    user_context="Project-wide version update",
                    operation_context="consistency_resolution"
                )
                print(f"✅ Project and state manager synchronized to: {selected_version}")
                return True
            else:
                print("❌ Version resolution cancelled")
                return False
                
        elif choice == "4":
            # Continue with inconsistencies
            logger.warning("User chose to continue with version inconsistencies")
            print("⚠️  Continuing with version inconsistencies")
            return True
            
        else:
            print("❌ Invalid choice")
            return False
            
    except Exception as e:
        logger.error(f"Failed to resolve version inconsistencies: {e}", exc_info=True)
        print(f"❌ Error resolving inconsistencies: {e}")
        return False


def handle_stage_based_increment(state_manager: VersionStateManager, 
                                logger: logging.Logger) -> Optional[str]:
    """
    Handle stage-based version increment with intelligent suggestions.
    
    Args:
        state_manager: Version state manager instance
        logger: Logger instance
        
    Returns:
        Selected version string or None if cancelled
    """
    logger.info("Starting stage-based increment workflow")
    
    current_state = state_manager.get_current_state()
    current_stage = current_state.current_stage
    
    print(f"\n🎯 Stage-Based Version Increment")
    print(f"Current: {current_state.current_version} ({current_stage.value})")
    
    # Show valid next stages
    next_stages = current_stage.get_next_stages()
    print(f"Valid next stages: {[stage.value for stage in next_stages]}")
    
    # Generate suggestions for different increment types
    print(f"\n💡 Increment Suggestions:")
    
    increment_options = []
    
    # Prerelease increment (within same stage)
    if current_stage != DevelopmentStage.RELEASE:
        prerelease_suggestions = state_manager.suggest_next_version("prerelease")
        if prerelease_suggestions:
            increment_options.extend([
                ("prerelease", prerelease_suggestions[0], f"Increment {current_stage.value} version")
            ])
    
    # Minor increment suggestions
    minor_suggestions = state_manager.suggest_next_version("minor")
    increment_options.extend([
        ("minor", minor_suggestions[0], "Minor version increment"),
    ])
    
    # Major increment suggestions  
    major_suggestions = state_manager.suggest_next_version("major")
    increment_options.extend([
        ("major", major_suggestions[0], "Major version increment"),
    ])
    
    # Patch increment suggestions
    patch_suggestions = state_manager.suggest_next_version("patch")
    increment_options.extend([
        ("patch", patch_suggestions[0], "Patch version increment"),
    ])
    
    # Display options
    for i, (inc_type, version, description) in enumerate(increment_options, 1):
        stage = DevelopmentStage.from_version_string(version)
        stage_name = stage.value if stage else "unknown"
        print(f"   {i}. {version} ({stage_name}) - {description}")
    
    print(f"   {len(increment_options) + 1}. Custom version")
    print(f"   {len(increment_options) + 2}. Cancel")
    
    while True:
        try:
            choice_input = input(f"\nSelect increment option [1-{len(increment_options) + 2}]: ").strip()
            choice = int(choice_input)
            
            if 1 <= choice <= len(increment_options):
                # Selected a suggested increment
                inc_type, selected_version, description = increment_options[choice - 1]
                
                print(f"\nSelected: {selected_version}")
                print(f"Description: {description}")
                
                confirm = input(f"Confirm increment to {selected_version}? [Y/n]: ").strip().lower()
                if confirm in ['', 'y', 'yes']:
                    # Update state manager
                    increment = state_manager.update_version(
                        selected_version,
                        increment_type=inc_type,
                        user_context=f"Stage-based increment: {description}",
                        operation_context="package_creation_increment"
                    )
                    
                    logger.info(f"Stage-based increment: {increment.from_version} → {selected_version}")
                    print(f"✅ Version incremented: {increment.from_version} → {selected_version}")
                    
                    if increment.stage_transition:
                        print(f"   Stage transition: {increment.from_stage.value} → {increment.to_stage.value}")
                    
                    return selected_version
                else:
                    print("Increment cancelled")
                    return None
                    
            elif choice == len(increment_options) + 1:
                # Custom version
                custom_version = get_manual_version_input(logger, context="stage-based custom")
                if custom_version:
                    state_manager.update_version(
                        custom_version,
                        increment_type="custom",
                        user_context="Custom version via stage-based workflow",
                        operation_context="package_creation_custom"
                    )
                    return custom_version
                return None
                
            elif choice == len(increment_options) + 2:
                # Cancel
                logger.info("User cancelled stage-based increment")
                return None
                
            else:
                print(f"❌ Invalid choice. Please select 1-{len(increment_options) + 2}")
                
        except ValueError:
            print(f"❌ Invalid input. Please enter a number 1-{len(increment_options) + 2}")


def show_version_history(state_manager: VersionStateManager) -> None:
    """
    Display comprehensive version history.
    
    Args:
        state_manager: Version state manager instance
    """
    print(f"\n📋 Version History")
    print(f"=" * 40)
    
    current_state = state_manager.get_current_state()
    
    print(f"Current Version: {current_state.current_version} ({current_state.current_stage.value})")
    print(f"Total Increments: {current_state.total_increments}")
    print(f"Creation Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_state.creation_time))}")
    print(f"Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_state.last_updated))}")
    
    # Show increment history
    history = state_manager.get_increment_history(limit=10)
    if history:
        print(f"\n🔄 Recent Increments (last {min(len(history), 10)}):")
        for i, entry in enumerate(history, 1):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry.timestamp))
            stage_info = ""
            if entry.stage_transition:
                stage_info = f" [{entry.from_stage.value if entry.from_stage else '?'} → {entry.to_stage.value}]"
            
            print(f"   {i}. {entry.from_version} → {entry.to_version}{stage_info}")
            print(f"      Type: {entry.increment_type}, Time: {timestamp}")
            if entry.user_context:
                print(f"      Context: {entry.user_context}")
    
    # Show stage history
    stage_history = state_manager.get_stage_history()
    if stage_history:
        print(f"\n🎭 Stage Transitions:")
        for version, stage, timestamp in stage_history[-5:]:  # Last 5 transitions
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            print(f"   {version} → {stage.value} ({time_str})")
    
    # Show statistics
    stats = state_manager.get_stats()
    print(f"\n📊 Statistics:")
    print(f"   Session ID: {stats.get('session_id', 'Unknown')}")
    print(f"   Platform: {stats.get('platform', 'Unknown')}")
    print(f"   Operation Count: {stats.get('operation_count', 0)}")
    print(f"   State File Size: {stats.get('state_file_size', 0)} bytes")


def get_manual_version_input(logger: logging.Logger, context: str = "manual") -> Optional[str]:
    """
    Get manual version input from user with validation.
    
    Args:
        logger: Logger instance for recording decisions
        context: Context for logging
        
    Returns:
        Validated version string or None if cancelled
    """
    version_manager = VersionManager()
    
    print(f"\n📝 Manual Version Entry")
    print(f"─" * 30)
    
    # Show examples
    print(f"Examples: 1.0.0, 2.1.3-alpha.1, 0.5.0-beta.2, 1.0.0-rc.1")
    
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            version_input = input(f"Enter version (or 'cancel' to abort): ").strip()
        else:
            print(f"Attempt {attempt}/{max_attempts}")
            version_input = input(f"Enter version: ").strip()
        
        if version_input.lower() in ['cancel', 'abort', 'exit', '']:
            logger.info(f"Manual version input cancelled ({context})")
            return None
        
        # Validate version format
        is_valid, feedback = version_manager.validate_version_format(version_input)
        
        if is_valid:
            print(f"✅ {feedback}")
            
            confirm = input(f"Confirm version '{version_input}'? [Y/n]: ").strip().lower()
            if confirm in ['', 'y', 'yes']:
                logger.info(f"Manual version selected: {version_input} ({context})")
                return version_input
            else:
                print("Version selection cancelled")
                continue
        else:
            print(f"❌ {feedback}")
            if attempt < max_attempts:
                print(f"Please try again ({max_attempts - attempt} attempts remaining)")
    
    logger.warning(f"Manual version input failed after {max_attempts} attempts ({context})")
    print(f"❌ Maximum attempts reached")
    return None


def handle_post_package_version_update(state_manager: Optional[VersionStateManager],
                                     package_version: str,
                                     logger: logging.Logger) -> None:
    """
    Handle optional project version update after successful package creation.
    
    Args:
        state_manager: Version state manager instance (may be None)
        package_version: Version used for package creation
        logger: Logger instance
    """
    if not state_manager:
        return
    
    current_state = state_manager.get_current_state()
    
    # Only prompt if package version differs from current state
    if current_state.current_version == package_version:
        logger.debug("Package version matches state version, no update needed")
        return
    
    print(f"\n🔄 Post-Package Version Management")
    print(f"Package created with version: {package_version}")
    print(f"Current state version: {current_state.current_version}")
    
    update_choice = input(f"Update project to package version ({package_version})? [y/N]: ").strip().lower()
    
    if update_choice in ['y', 'yes']:
        try:
            # Update state manager
            increment = state_manager.update_version(
                package_version,
                increment_type="post_package_sync",
                user_context="Synchronized to package version after creation",
                operation_context="post_package_update"
            )
            
            logger.info(f"Post-package version update: {increment.from_version} → {package_version}")
            print(f"✅ Project version updated to: {package_version}")
            
            # Also sync project files if needed
            sync_files = input(f"Also sync project files to {package_version}? [Y/n]: ").strip().lower()
            if sync_files in ['', 'y', 'yes']:
                try:
                    from provisioning.project_version_manager import ProjectVersionManager
                    project_manager = ProjectVersionManager(state_manager.project_root)
                    project_manager.update_all_versions(package_version)
                    print(f"✅ All project files synchronized to: {package_version}")
                    logger.info(f"Project files synchronized to: {package_version}")
                except Exception as e:
                    logger.error(f"Failed to sync project files: {e}")
                    print(f"⚠️  Warning: Failed to sync project files: {e}")
            
        except Exception as e:
            logger.error(f"Post-package version update failed: {e}")
            print(f"❌ Failed to update project version: {e}")
    else:
        logger.info("User declined post-package version update")


def handle_multi_package_session(state_manager: Optional[VersionStateManager],
                               logger: logging.Logger) -> bool:
    """
    Handle multi-package session prompting for additional packages.
    
    Args:
        state_manager: Version state manager instance
        logger: Logger instance
        
    Returns:
        True if user wants to create another package, False otherwise
    """
    if not state_manager:
        return False
    
    print(f"\n📦 Multi-Package Session")
    
    current_state = state_manager.get_current_state()
    session_stats = state_manager.get_stats()
    
    print(f"Current session: {session_stats.get('session_id', 'Unknown')}")
    print(f"Current version: {current_state.current_version}")
    print(f"Session operations: {session_stats.get('operation_count', 0)}")
    
    create_another = input(f"Create another package in this session? [y/N]: ").strip().lower()
    
    if create_another in ['y', 'yes']:
        logger.info("User requested another package in multi-package session")
        
        # Suggest increment for next package
        increment_suggestion = input(f"Increment version for next package? [Y/n]: ").strip().lower()
        if increment_suggestion in ['', 'y', 'yes']:
            # Show quick increment options
            print(f"\nQuick increment options:")
            print(f"1. Patch increment (recommended for iterative packages)")
            print(f"2. Prerelease increment (same stage)")
            print(f"3. Keep current version")
            
            quick_choice = input(f"Select [1-3]: ").strip()
            
            if quick_choice == "1":
                patch_suggestions = state_manager.suggest_next_version("patch")
                if patch_suggestions:
                    new_version = patch_suggestions[0]
                    state_manager.update_version(
                        new_version,
                        increment_type="multi_package_patch",
                        user_context="Patch increment for multi-package session",
                        operation_context="multi_package_session"
                    )
                    print(f"✅ Version incremented to: {new_version}")
                    
            elif quick_choice == "2":
                prerelease_suggestions = state_manager.suggest_next_version("prerelease")
                if prerelease_suggestions:
                    new_version = prerelease_suggestions[0]
                    state_manager.update_version(
                        new_version,
                        increment_type="multi_package_prerelease",
                        user_context="Prerelease increment for multi-package session",
                        operation_context="multi_package_session"
                    )
                    print(f"✅ Version incremented to: {new_version}")
        
        return True
    else:
        logger.info("User declined multi-package session continuation")
        return False


def create_deployment_package(user_version: Optional[str] = None):
    """Create deployment package for Raspberry Pi deployment"""
    print("=== Creating GTach Deployment Package ===")
    
    # Setup logging
    session_id = setup_provisioning_logging(debug_mode=True)
    logger = logging.getLogger('provisioning.example')
    
    try:
        # Find project root (assumes running from provisioning directory)
        project_root = Path(__file__).parent.parent.parent
        logger.info(f"Using project root: {project_root}")
        
        # Validate configuration file availability before proceeding
        config_paths = [
            project_root / "src" / "config" / "config.yaml",
            project_root / "config" / "config.yaml", 
            project_root / "config.yaml"
        ]
        
        config_found = False
        for config_path in config_paths:
            if config_path.exists():
                logger.info(f"Configuration file found: {config_path}")
                config_found = True
                break
        
        if not config_found:
            logger.error("Configuration file discovery failed")
            logger.error("Searched paths:")
            for path in config_paths:
                logger.error(f"  - {path}")
            raise RuntimeError("Required configuration file (config.yaml) not found in any expected location")
        
        # Determine version to use
        if user_version:
            package_version = user_version
            logger.info(f"Using provided version: {package_version}")
        else:
            package_version = "1.0.0"
            logger.info(f"Using default version: {package_version}")
        
        # Create package configuration
        config = PackageConfig(
            package_name="gtach",  # Simplified package name
            version=package_version,
            target_platform="raspberry-pi",
            source_dirs=["src/obdii"],
            output_dir=str(project_root / "packages"),
            compression_level=6,
            verify_integrity=True
        )
        
        # Initialize package creator
        logger.info("Initializing PackageCreator...")
        creator = PackageCreator(project_root)
        
        # Create deployment package
        logger.info("Starting package creation process...")
        package_path = creator.create_package(config)
        
        logger.info(f"Package creation successful: {package_path}")
        print(f"✓ Package created successfully: {package_path}")
        
        # Show package stats
        stats = creator.get_stats()
        logger.info(f"Package creation stats: {stats}")
        print(f"  Operation count: {stats['operation_count']}")
        print(f"  Source platform: {stats['source_platform']}")
        
    except Exception as e:
        logger.error(f"Package creation failed: {e}", exc_info=True)
        print(f"✗ Error: {e}")
        raise  # Re-raise to ensure proper error propagation
    finally:
        cleanup_provisioning_logging(session_id)


def main():
    """Enhanced GTach deployment package creation with comprehensive version state management"""
    print("Enhanced GTach Application Package Creator")
    print("=" * 45)
    
    # Check if we're in the right location
    project_root = Path(__file__).parent.parent.parent
    if not (project_root / "src" / "obdii").exists():
        print("Error: Could not find src/obdii directory.")
        print("Please run this script from the provisioning directory.")
        return 1
    
    # Setup main session logging
    main_session_id = setup_provisioning_logging(debug_mode=True)
    logger = logging.getLogger('provisioning.enhanced_create_package')
    
    try:
        logger.info("Starting enhanced package creation workflow")
        
        # Handle comprehensive version state workflow
        selected_version, state_manager = handle_version_state_workflow(
            project_root, main_session_id, logger
        )
        
        if not selected_version:
            print("Package creation cancelled - no version selected")
            return 0
        
        print(f"\n📦 Creating package with version: {selected_version}")
        
        # Track operation outcomes
        operations_successful = True
        operation_results = []
        
        # Main package creation
        try:
            create_deployment_package(selected_version)
            operation_results.append(("Package Creation", True, None))
            logger.info(f"Package creation successful with version: {selected_version}")
            
        except Exception as e:
            operations_successful = False
            operation_results.append(("Package Creation", False, str(e)))
            logger.error(f"Package creation failed: {e}", exc_info=True)
        
        # Report operation results
        print("\n" + "=" * 45)
        print("Operation Summary:")
        print("-" * 45)
        
        for operation, success, error in operation_results:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{operation}: {status}")
            if error:
                print(f"  Error: {error}")
        
        if operations_successful:
            print("\n✅ Package creation completed successfully!")
            
            # Handle post-package version management
            handle_post_package_version_update(state_manager, selected_version, logger)
            
            # Check for multi-package session continuation
            if handle_multi_package_session(state_manager, logger):
                print("\n🔄 Restarting for next package...")
                return main()  # Recursive call for next package
            
            return 0
        else:
            print("\n❌ Package creation completed with errors!")
            print("Check the error messages above for details.")
            return 1
    
    except KeyboardInterrupt:
        print("\nPackage creation interrupted by user.")
        logger.info("Package creation interrupted by user (KeyboardInterrupt)")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        print(f"\nCritical error in enhanced package creation: {e}")
        logger.error(f"Critical error in enhanced package creation: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        cleanup_provisioning_logging(main_session_id)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)