#!/usr/bin/env python3
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


def create_deployment_package():
    """Create deployment package for Raspberry Pi deployment"""
    print("=== Creating GTach Deployment Package ===")
    
    # Setup logging
    session_id = setup_provisioning_logging(debug_mode=True)
    logger = logging.getLogger('provisioning.example')
    
    try:
        # Find project root (assumes running from provisioning directory)
        project_root = Path(__file__).parent.parent.parent
        logger.info(f"Using project root: {project_root}")
        
        # Create package configuration
        config = PackageConfig(
            package_name="gtach-pi-deployment",
            version="1.0.0",
            target_platform="raspberry-pi",
            source_dirs=["src/obdii"],
            output_dir=str(project_root / "packages"),
            compression_level=6,
            verify_integrity=True
        )
        
        # Initialize package creator
        creator = PackageCreator(project_root)
        
        # Create deployment package
        logger.info("Creating deployment package...")
        package_path = creator.create_package(config)
        
        print(f"✓ Package created successfully: {package_path}")
        
        # Show package stats
        stats = creator.get_stats()
        print(f"  Operation count: {stats['operation_count']}")
        print(f"  Source platform: {stats['source_platform']}")
        
    except Exception as e:
        logger.error(f"Package creation failed: {e}")
        print(f"✗ Error: {e}")
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
        from obdii.utils.platform import get_platform_type, get_platform_info
        
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
                package_name=f"gtach-{target_platform}",
                version="1.0.0",
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
    """Create GTach deployment package with optional demonstrations"""
    print("GTach Application Package Creator")
    print("=" * 35)
    
    # Check if we're in the right location
    project_root = Path(__file__).parent.parent.parent
    if not (project_root / "src" / "obdii").exists():
        print("Error: Could not find src/obdii directory.")
        print("Please run this script from the provisioning directory.")
        return
    
    try:
        # Main package creation
        create_deployment_package()
        
        # Optional demonstrations (comment out for production use)
        demonstrate_configuration_processing() 
        demonstrate_archive_management()
        demonstrate_cross_platform_compatibility()
        
        print("\n" + "=" * 35)
        print("Package creation completed successfully!")
        
    except KeyboardInterrupt:
        print("\nPackage creation interrupted by user.")
    except Exception as e:
        print(f"\nPackage creation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()