#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
GTach Application Package Creator

Production script for creating GTach deployment packages with cross-platform 
compatibility. Creates standardized deployment packages containing application 
source code, configuration templates, and installation scripts.

Usage:
    python create_package.py

Features:
- Basic deployment package creation for Raspberry Pi
- Custom configuration processing for target platforms
- Cross-platform development and deployment support
- Comprehensive logging and error handling

This script is the primary tool for creating GTach deployment packages.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from provisioning import (
    PackageCreator, PackageConfig, PackageManifest,
    ConfigProcessor, PlatformConfig,
    ArchiveManager, ArchiveConfig, CompressionFormat
)
from provisioning.logging_config import setup_provisioning_logging, cleanup_provisioning_logging
from provisioning.version_manager import VersionManager
from provisioning.project_version_manager import VersionWorkflow


def get_user_version_input(logger) -> str:
    """
    Get version input from user with validation and examples.
    
    Args:
        logger: Logger instance for recording version assignment decisions
        
    Returns:
        Validated version string
    """
    version_manager = VersionManager()
    
    print("\n" + "=" * 50)
    print("📦 GTach Package Version Assignment")
    print("=" * 50)
    
    # Show examples
    print("\nVersion Format Examples:")
    examples = version_manager.suggest_version_examples()
    for i, example in enumerate(examples[:6], 1):  # Show first 6 examples
        print(f"  {i}. {example}")
    print(f"  ... and more semantic version formats")
    
    print(f"\nSemantic Versioning Format: MAJOR.MINOR.PATCH[-prerelease][+build]")
    print(f"• Stable releases: 1.0.0, 2.1.3")
    print(f"• Pre-releases: 1.0.0-alpha.1, 2.0.0-beta.2, 1.5.0-rc.1")
    print(f"• Development: 0.1.0-dev.20250813, 1.0.0+build.123")
    
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        print(f"\n{'─' * 50}")
        if attempt == 1:
            version_input = input("Enter version (e.g., 0.1.0, 1.2.3-alpha.1): ").strip()
        else:
            print(f"Attempt {attempt}/{max_attempts}")
            version_input = input("Enter version: ").strip()
        
        if not version_input:
            print("❌ Error: Version cannot be empty")
            continue
        
        # Validate version format
        is_valid, feedback = version_manager.validate_version_format(version_input)
        
        if is_valid:
            print(f"✅ {feedback}")
            
            # Confirm version with user
            confirm = input(f"\nConfirm version '{version_input}'? [Y/n]: ").strip().lower()
            if confirm in ['', 'y', 'yes']:
                logger.info(f"User selected version: {version_input}")
                logger.debug(f"Version validation: {feedback}")
                print(f"✓ Version confirmed: {version_input}")
                return version_input
            else:
                print("Version selection cancelled by user")
                continue
        else:
            print(f"❌ {feedback}")
            
            if attempt < max_attempts:
                print(f"\nPlease try again ({max_attempts - attempt} attempts remaining)")
            
    # Max attempts reached
    logger.warning(f"Version input failed after {max_attempts} attempts, using default")
    print(f"\n❌ Maximum attempts ({max_attempts}) reached.")
    print("Using default version: 0.1.0-dev")
    return "0.1.0-dev"


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


def demonstrate_configuration_processing():
    """Demonstrate: Custom configuration template processing"""
    print("\n=== Configuration Processing Demonstration ===")
    
    session_id = setup_provisioning_logging(debug_mode=False)
    logger = logging.getLogger('provisioning.example')
    
    try:
        project_root = Path(__file__).parent.parent.parent
        
        # Create sample template directory and files
        template_dir = project_root / "temp_templates"
        template_dir.mkdir(exist_ok=True)
        
        # Create a sample configuration template
        config_template = """
# GTach Configuration Template
app:
  name: ${package_name}
  version: ${version}
  install_dir: ${app_dir}
  user: ${user}
  group: ${group}

platform:
  type: ${platform_name}
  gpio_enabled: ${gpio_available}
  performance_profile: ${performance_profile}

display:
  fps_limit: ${fps_limit}
  mode: digital

bluetooth:
  scan_duration: 8.0
  timeout: ${bluetooth_timeout}
"""
        
        (template_dir / "gtach.template.yaml").write_text(config_template)
        
        # Process templates for different platforms
        platforms = ["raspberry-pi", "macos", "linux"]
        
        for platform in platforms:
            print(f"\nProcessing templates for {platform}:")
            
            processor = ConfigProcessor(project_root, platform)
            output_dir = project_root / f"temp_output_{platform}"
            output_dir.mkdir(exist_ok=True)
            
            # Add custom variables
            custom_vars = {
                "package_name": "gtach-custom",
                "version": "2.0.0"
            }
            
            processed_files = processor.process_templates(
                template_dir, output_dir, custom_vars
            )
            
            print(f"  ✓ Processed {len(processed_files)} files:")
            for file_path in processed_files:
                print(f"    - {file_path}")
        
        # Cleanup temporary files
        import shutil
        shutil.rmtree(template_dir)
        for platform in platforms:
            output_dir = project_root / f"temp_output_{platform}"
            if output_dir.exists():
                shutil.rmtree(output_dir)
        
    except Exception as e:
        logger.error(f"Configuration processing failed: {e}")
        print(f"✗ Error: {e}")
    finally:
        cleanup_provisioning_logging(session_id)


def demonstrate_archive_management():
    """Demonstrate: Direct archive management operations"""
    print("\n=== Archive Management Demonstration ===")
    
    session_id = setup_provisioning_logging(debug_mode=False)
    logger = logging.getLogger('provisioning.example')
    
    try:
        project_root = Path(__file__).parent.parent.parent
        
        # Create sample source directory
        source_dir = project_root / "temp_source"
        source_dir.mkdir(exist_ok=True)
        
        # Create sample files
        sample_files = [
            "main.py",
            "config/settings.yaml", 
            "data/sample.txt",
            "scripts/deploy.sh"
        ]
        
        for file_path in sample_files:
            full_path = source_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Sample content for {file_path}\n")
        
        # Initialize archive manager
        manager = ArchiveManager()
        
        # Test different compression formats
        formats = [
            ("sample.tar.gz", CompressionFormat.TAR_GZ),
            ("sample.tar.bz2", CompressionFormat.TAR_BZ2),
            ("sample.zip", CompressionFormat.ZIP)
        ]
        
        archives_dir = project_root / "temp_archives"
        archives_dir.mkdir(exist_ok=True)
        
        for filename, format_type in formats:
            print(f"\nTesting {format_type.name} format:")
            
            # Configure archive with progress callback
            progress_updates = []
            def progress_callback(current, total):
                progress_updates.append((current, total))
            
            config = ArchiveConfig(
                compression_level=6,
                create_checksums=True,
                include_metadata=True,
                progress_callback=progress_callback
            )
            
            # Create archive
            archive_path = archives_dir / filename
            metadata = manager.create_archive(source_dir, archive_path, config)
            
            print(f"  ✓ Created: {metadata.filename}")
            print(f"    Files: {metadata.file_count}")
            print(f"    Uncompressed: {metadata.uncompressed_size:,} bytes")
            print(f"    Compressed: {metadata.compressed_size:,} bytes")
            print(f"    Ratio: {metadata.compressed_size/metadata.uncompressed_size:.2%}")
            print(f"    Checksum: {metadata.checksum_sha256[:16]}..." if metadata.checksum_sha256 else "    No checksum")
            print(f"    Progress updates: {len(progress_updates)}")
            
            # Verify integrity
            is_valid = manager.verify_archive_integrity(archive_path)
            print(f"    Integrity: {'✓ Valid' if is_valid else '✗ Invalid'}")
            
            # Test extraction
            extract_dir = project_root / f"temp_extract_{format_type.name}"
            extract_metadata = manager.extract_archive(archive_path, extract_dir)
            
            print(f"    Extraction: ✓ {extract_metadata.file_count} files")
            
            # Cleanup extract directory
            import shutil
            shutil.rmtree(extract_dir)
        
        # Show manager stats
        stats = manager.get_stats()
        print(f"\nArchive Manager Stats:")
        print(f"  Total operations: {stats['operation_count']}")
        print(f"  Archives created: {stats['archives_created']}")
        print(f"  Archives extracted: {stats['archives_extracted']}")
        print(f"  Bytes processed: {stats['bytes_processed']:,}")
        
        # Cleanup temporary files
        import shutil
        shutil.rmtree(source_dir)
        shutil.rmtree(archives_dir)
        
    except Exception as e:
        logger.error(f"Archive management failed: {e}")
        print(f"✗ Error: {e}")
    finally:
        cleanup_provisioning_logging(session_id)


def demonstrate_cross_platform_compatibility():
    """Demonstrate: Cross-platform compatibility features"""
    print("\n=== Cross-Platform Compatibility Demonstration ===")
    
    session_id = setup_provisioning_logging(debug_mode=False)
    logger = logging.getLogger('provisioning.example')
    
    try:
        project_root = Path(__file__).parent.parent.parent
        
        # Show platform detection
        from gtach.utils.platform import get_platform_type, get_platform_info
        
        current_platform = get_platform_type()
        platform_info = get_platform_info()
        
        print(f"Current Platform: {current_platform.name}")
        print(f"Platform Details:")
        print(f"  System: {platform_info['system_info']['system']}")
        print(f"  Machine: {platform_info['system_info']['machine']}")
        print(f"  Architecture: {platform_info['system_info']['architecture']}")
        
        capabilities = platform_info['capabilities']
        print(f"  GPIO Available: {capabilities['gpio_available']}")
        print(f"  GPIO Accessible: {capabilities['gpio_accessible']}")
        print(f"  Display Hardware: {capabilities['display_hardware']}")
        
        # Show different platform configurations
        print(f"\nPlatform-Specific Configurations:")
        
        platforms = ["raspberry-pi", "macos", "linux"]
        for platform in platforms:
            processor = ConfigProcessor(project_root, platform)
            platform_config = processor._get_platform_config()
            
            if platform_config:
                vars = platform_config.template_variables
                print(f"\n{platform.upper()}:")
                print(f"  App Dir: {vars['app_dir']}")
                print(f"  User: {vars['user']}")
                print(f"  GPIO: {vars['gpio_available']}")
                print(f"  FPS Limit: {vars['fps_limit']}")
                print(f"  Performance: {vars['performance_profile']}")
        
        # Test package creation for different targets
        print(f"\nTesting Package Creation for Different Targets:")
        
        creator = PackageCreator(project_root)
        
        for target_platform in platforms:
            print(f"\nTarget: {target_platform}")
            
            config = PackageConfig(
                package_name="gtach",  # Simplified naming
                version="1.0.0-test",
                target_platform=target_platform,
                source_dirs=["src/obdii"],
                output_dir=str(project_root / "temp_packages"),
                verify_integrity=False  # Skip for speed
            )
            
            try:
                package_path = creator.create_package(config)
                package_size = package_path.stat().st_size
                print(f"  ✓ Package created: {package_path.name} ({package_size:,} bytes)")
                
                # Cleanup
                package_path.unlink()
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
        
        # Cleanup packages directory
        packages_dir = project_root / "temp_packages"
        if packages_dir.exists():
            import shutil
            shutil.rmtree(packages_dir)
        
    except Exception as e:
        logger.error(f"Cross-platform compatibility test failed: {e}")
        print(f"✗ Error: {e}")
    finally:
        cleanup_provisioning_logging(session_id)


def main():
    """Create GTach deployment package with version management and operation tracking"""
    print("GTach Application Package Creator")
    print("=" * 35)
    
    # Check if we're in the right location
    project_root = Path(__file__).parent.parent.parent
    if not (project_root / "src" / "obdii").exists():
        print("Error: Could not find src/obdii directory.")
        print("Please run this script from the provisioning directory.")
        return 1
    
    # Initialize version workflow
    version_workflow = VersionWorkflow(project_root)
    
    # Check for version inconsistencies and offer management
    print("\n🔍 Checking project version consistency...")
    current_version = version_workflow.get_current_project_version()
    stats = version_workflow.project_manager.get_stats()
    
    if stats['has_inconsistencies']:
        print("⚠️  Version inconsistencies detected across project files!")
        print(f"Found {len(stats['version_groups'])} different versions:")
        for version, count in stats['version_groups'].items():
            print(f"   • {version}: {count} files")
        
        print(f"\nWould you like to:")
        print(f"1. Fix version inconsistencies automatically")
        print(f"2. Set project version interactively") 
        print(f"3. Continue with current version ({current_version})")
        print(f"4. Exit")
        
        choice = input("\nSelect option [1-4]: ").strip()
        
        if choice == "1":
            # Use current most common version
            if current_version:
                print(f"Setting all files to version: {current_version}")
                version_workflow.project_manager.update_all_versions(current_version)
                print("✅ Version consistency restored!")
            else:
                print("❌ No valid version found to standardize on")
                return 1
        elif choice == "2":
            # Interactive version management
            selected_version = version_workflow.interactive_version_update()
            if selected_version:
                current_version = selected_version
                print(f"✅ Project version updated to: {current_version}")
            else:
                print("❌ Version update cancelled")
                return 1
        elif choice == "3":
            print(f"Continuing with current version: {current_version}")
        elif choice == "4":
            print("Exiting...")
            return 0
        else:
            print("Invalid choice, continuing with current version")
    else:
        print(f"✅ All project files consistent at version: {current_version}")
    
    # Track operation outcomes
    operations_successful = True
    operation_results = []
    
    # Get version for package creation (default to project version)
    user_version = current_version
    
    print(f"\n📦 Package Version Selection")
    print(f"Current project version: {current_version}")
    
    use_different = input(f"Use a different version for this package? [y/N]: ").strip().lower()
    if use_different in ['y', 'yes']:
        try:
            # Setup temporary logging for version input
            temp_session_id = setup_provisioning_logging(debug_mode=False)
            temp_logger = logging.getLogger('provisioning.version_input')
            
            user_version = get_user_version_input(temp_logger)
            cleanup_provisioning_logging(temp_session_id)
            
        except KeyboardInterrupt:
            print("\nVersion input interrupted by user.")
            return 130
        except Exception as e:
            print(f"Error during version input: {e}")
            user_version = current_version  # Fall back to project version
    else:
        print(f"Using project version: {current_version}")
        user_version = current_version
    
    try:
        # Main package creation
        try:
            create_deployment_package(user_version)
            operation_results.append(("Package Creation", True, None))
        except Exception as e:
            operations_successful = False
            operation_results.append(("Package Creation", False, str(e)))
        
        # Optional demonstrations (comment out for production use)
        try:
            demonstrate_configuration_processing()
            operation_results.append(("Configuration Processing", True, None))
        except Exception as e:
            operations_successful = False
            operation_results.append(("Configuration Processing", False, str(e)))
        
        try:
            demonstrate_archive_management()
            operation_results.append(("Archive Management", True, None))
        except Exception as e:
            operations_successful = False
            operation_results.append(("Archive Management", False, str(e)))
        
        try:
            demonstrate_cross_platform_compatibility()
            operation_results.append(("Cross-Platform Compatibility", True, None))
        except Exception as e:
            operations_successful = False
            operation_results.append(("Cross-Platform Compatibility", False, str(e)))
        
        # Report outcomes based on actual results
        print("\n" + "=" * 35)
        print("Operation Summary:")
        print("-" * 35)
        
        for operation, success, error in operation_results:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{operation}: {status}")
            if error:
                print(f"  Error: {error}")
        
        if operations_successful:
            print("\n" + "=" * 35)
            print("Package creation completed successfully!")
            return 0
        else:
            print("\n" + "=" * 35)
            print("Package creation completed with errors!")
            print("Check the error messages above for details.")
            return 1
        
    except KeyboardInterrupt:
        print("\nPackage creation interrupted by user.")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\nCritical error in package creation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()