#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Package Creator for GTach Application Provisioning System

Creates standardized deployment packages with application source, configuration 
templates, and installation scripts. Implements thread-safe operations with 
comprehensive logging per Protocol 8.

Features:
- Thread-safe package creation
- Cross-platform compatibility (Mac development, Pi deployment)
- Configuration template processing
- Archive integrity verification
- Session-based logging
"""

import os
import sys
import tarfile
import tempfile
import shutil
import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager

# Import existing utilities following project structure
try:
    # Try relative import first
    from ..gtach.utils.platform import get_platform_type, PlatformType
    from ..gtach.utils.config import ConfigManager
    from .version_manager import VersionManager, Version
except ImportError:
    # Fallback for development/testing
    sys.path.append(str(Path(__file__).parent.parent))
    from gtach.utils.platform import get_platform_type, PlatformType
    from gtach.utils.config import ConfigManager
    sys.path.append(str(Path(__file__).parent))
    from version_manager import VersionManager, Version


@dataclass
class PackageManifest:
    """Package metadata and contents manifest"""
    package_name: str
    version: str
    created_at: str
    source_platform: str
    target_platform: str
    source_files: List[str] = field(default_factory=list)
    config_templates: List[str] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'package_name': self.package_name,
            'version': self.version,
            'created_at': self.created_at,
            'source_platform': self.source_platform,
            'target_platform': self.target_platform,
            'source_files': self.source_files,
            'config_templates': self.config_templates,
            'scripts': self.scripts,
            'dependencies': self.dependencies,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PackageManifest':
        """Create instance from dictionary"""
        return cls(
            package_name=data['package_name'],
            version=data['version'],
            created_at=data['created_at'],
            source_platform=data['source_platform'],
            target_platform=data['target_platform'],
            source_files=data.get('source_files', []),
            config_templates=data.get('config_templates', []),
            scripts=data.get('scripts', []),
            dependencies=data.get('dependencies', []),
            checksum=data.get('checksum')
        )


@dataclass
class PackageConfig:
    """Configuration for package creation"""
    # Package identification
    package_name: str = "gtach-app"
    version: str = "0.1.0-alpha.1"
    target_platform: str = "raspberry-pi"
    
    # Source paths (relative to project root)
    source_dirs: List[str] = field(default_factory=lambda: ["src/obdii"])
    config_template_dirs: List[str] = field(default_factory=lambda: ["src/config"])
    script_dirs: List[str] = field(default_factory=lambda: ["scripts"])
    
    # Exclusion patterns
    exclude_patterns: Set[str] = field(default_factory=lambda: {
        "__pycache__",
        "*.pyc",
        "*.pyo", 
        "*.egg-info",
        ".git",
        ".gitignore",
        "*.log",
        "test_*",
        "*_test.py",
        ".pytest_cache"
    })
    
    # Archive settings
    compression_level: int = 6
    preserve_permissions: bool = True
    verify_integrity: bool = True
    
    # Output settings
    output_dir: Optional[str] = None
    include_dependencies: bool = True
    create_install_script: bool = True


class PackageCreator:
    """
    Thread-safe package creator for GTach application provisioning.
    
    Creates standardized deployment packages containing:
    - Application source code
    - Configuration templates
    - Installation scripts
    - Package manifest with integrity verification
    
    Supports cross-platform development (Mac -> Pi) with proper logging
    and error handling per Protocol standards.
    """
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize PackageCreator with project structure compliance.
        
        Args:
            project_root: Optional project root path. Auto-detected if None.
        """
        # Session-based logging per Protocol 8
        self.logger = logging.getLogger(f'{__name__}.PackageCreator')
        
        # Project structure setup per Protocol 1
        if project_root is None:
            self.project_root = self._auto_detect_project_root()
        else:
            self.project_root = Path(project_root)
            
        if not self.project_root.exists():
            raise RuntimeError(f"Project root does not exist: {self.project_root}")
            
        # Thread safety
        self._creation_lock = threading.RLock()
        self._operation_count = 0
        self._stats_lock = threading.Lock()
        
        # Platform detection per Protocol 6
        self.source_platform = get_platform_type()
        
        # Configuration manager integration
        self.config_manager = ConfigManager()
        
        # Version manager integration
        self.version_manager = VersionManager()
        
        # Default package configuration
        self.default_config = PackageConfig()
        
        # Workspace for package operations
        self.workspace_dir = None
        
        self.logger.info(f"PackageCreator initialized - Project root: {self.project_root}")
        self.logger.debug(f"Source platform detected: {self.source_platform.name}")
    
    def _auto_detect_project_root(self) -> Path:
        """
        Auto-detect project root directory.
        
        Uses enhanced algorithm that supports test environments by:
        1. Checking current working directory and parents (for test environments)
        2. Falling back to module location search (for production)
        
        Returns:
            Path to detected project root
            
        Raises:
            RuntimeError: If project root cannot be detected
        """
        # Strategy 1: Check current working directory and walk up
        # This handles test environments where we change to a nested test directory
        current_path = Path.cwd()
        while current_path != current_path.parent:
            if (current_path / 'src').exists():
                self.logger.debug(f"Project root detected from CWD: {current_path}")
                return current_path
            current_path = current_path.parent
        
        # Strategy 2: Check from module location and walk up
        # This handles production environments and development
        current_path = Path(__file__).parent
        while current_path != current_path.parent:
            if (current_path / 'src').exists():
                self.logger.debug(f"Project root detected from module location: {current_path}")
                return current_path
            current_path = current_path.parent
        
        # Strategy 3: Look for specific GTach project markers
        # Check for common GTach project structure markers
        current_path = Path.cwd()
        while current_path != current_path.parent:
            # Look for GTach-specific markers
            gtach_markers = [
                'src/obdii',           # Main application directory
                'src/provisioning',    # Provisioning directory  
                'doc/protocol',        # Protocol documentation
                'pyproject.toml',      # Python project config
                'requirements.txt'     # Python dependencies
            ]
            
            marker_count = sum(1 for marker in gtach_markers if (current_path / marker).exists())
            if marker_count >= 2:  # At least 2 markers present
                self.logger.debug(f"Project root detected from GTach markers: {current_path}")
                return current_path
            current_path = current_path.parent
        
        raise RuntimeError("Could not auto-detect project root directory. Please specify project_root explicitly.")
    
    def create_package(self, 
                      package_config: Optional[PackageConfig] = None,
                      output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Create deployment package with thread-safe operations.
        
        Args:
            package_config: Package configuration. Uses default if None.
            output_path: Output file path. Auto-generated if None.
            
        Returns:
            Path to created package file
            
        Raises:
            RuntimeError: If package creation fails
            ValueError: If configuration is invalid
        """
        with self._creation_lock:
            self._increment_operation_count()
            
            config = package_config or self.default_config
            start_time = time.perf_counter()
            
            self.logger.info(f"Starting package creation: {config.package_name} v{config.version}")
            
            try:
                # Validate configuration
                self._validate_config(config)
                
                # Setup workspace
                with self._setup_workspace() as workspace:
                    self.workspace_dir = workspace
                    
                    # Collect source files
                    source_files = self._collect_source_files(config)
                    self.logger.debug(f"Collected {len(source_files)} source files")
                    
                    # Copy files to workspace
                    self._copy_files_to_workspace(source_files, config)
                    
                    # Process configuration templates
                    template_files = self._process_config_templates(config)
                    
                    # Generate installation scripts
                    script_files = self._generate_install_scripts(config)
                    
                    # Create package manifest
                    manifest = self._create_manifest(
                        config, source_files, template_files, script_files
                    )
                    
                    # Create archive
                    package_path = self._create_archive(config, manifest, output_path)
                    
                    # Verify integrity
                    if config.verify_integrity:
                        self._verify_package_integrity(package_path, manifest)
                    
                    elapsed = time.perf_counter() - start_time
                    self.logger.info(
                        f"Package created successfully: {package_path} ({elapsed:.2f}s)"
                    )
                    
                    return package_path
                    
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                self.logger.error(f"Package creation failed after {elapsed:.2f}s: {e}")
                raise RuntimeError(f"Package creation failed: {e}") from e
            finally:
                self.workspace_dir = None
    
    def _validate_config(self, config: PackageConfig) -> None:
        """
        Validate package configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not config.package_name:
            raise ValueError("Package name cannot be empty")
            
        if not config.version:
            raise ValueError("Package version cannot be empty")
            
        # Validate version format using SemVer
        try:
            self.version_manager.parse_version(config.version)
        except ValueError as e:
            raise ValueError(f"Invalid semantic version '{config.version}': {e}") from e
            
        # Validate source directories exist
        for source_dir in config.source_dirs:
            full_path = self.project_root / source_dir
            if not full_path.exists():
                raise ValueError(f"Source directory does not exist: {source_dir}")
                
        # Validate output directory if specified
        if config.output_dir:
            output_path = Path(config.output_dir)
            if not output_path.parent.exists():
                raise ValueError(f"Output directory parent does not exist: {output_path.parent}")
                
        self.logger.debug("Configuration validation passed")
    
    @contextmanager
    def _setup_workspace(self):
        """
        Create temporary workspace for package operations.
        
        Yields:
            Path: Workspace directory path
        """
        workspace = None
        try:
            workspace = Path(tempfile.mkdtemp(prefix="gtach_pkg_"))
            self.logger.debug(f"Created workspace: {workspace}")
            yield workspace
        finally:
            if workspace and workspace.exists():
                try:
                    shutil.rmtree(workspace)
                    self.logger.debug(f"Cleaned up workspace: {workspace}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup workspace {workspace}: {e}")
    
    def _collect_source_files(self, config: PackageConfig) -> List[Path]:
        """
        Collect all source files based on configuration.
        
        Args:
            config: Package configuration
            
        Returns:
            List of source file paths
        """
        source_files = []
        
        for source_dir in config.source_dirs:
            dir_path = self.project_root / source_dir
            if not dir_path.exists():
                self.logger.warning(f"Source directory not found: {source_dir}")
                continue
                
            # Recursively collect files
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    # Check exclusion patterns
                    if not self._should_exclude_file(file_path, config.exclude_patterns):
                        source_files.append(file_path)
                        
        self.logger.debug(f"Collected {len(source_files)} source files from {len(config.source_dirs)} directories")
        return source_files
    
    def _should_exclude_file(self, file_path: Path, exclude_patterns: Set[str]) -> bool:
        """
        Check if file should be excluded based on patterns.
        
        Args:
            file_path: File path to check
            exclude_patterns: Set of exclusion patterns
            
        Returns:
            True if file should be excluded
        """
        # Check filename patterns
        for pattern in exclude_patterns:
            # Simple glob-style matching
            if pattern.startswith('*') and pattern.endswith('*'):
                # Contains pattern
                if pattern[1:-1] in file_path.name:
                    return True
            elif pattern.startswith('*'):
                # Suffix pattern
                if file_path.name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                # Prefix pattern
                if file_path.name.startswith(pattern[:-1]):
                    return True
            else:
                # Exact match
                if file_path.name == pattern or pattern in str(file_path):
                    return True
                    
        return False
    
    def _copy_files_to_workspace(self, source_files: List[Path], config: PackageConfig) -> None:
        """
        Copy source files to workspace maintaining directory structure.
        
        Args:
            source_files: List of source files to copy
            config: Package configuration
        """
        copied_count = 0
        
        for source_file in source_files:
            # Calculate relative path from project root
            try:
                rel_path = source_file.relative_to(self.project_root)
                dest_path = self.workspace_dir / rel_path
                
                # Create destination directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_file, dest_path)
                
                # Preserve permissions if requested
                if config.preserve_permissions:
                    shutil.copystat(source_file, dest_path)
                    
                copied_count += 1
                
            except Exception as e:
                self.logger.warning(f"Failed to copy file {source_file}: {e}")
                
        self.logger.debug(f"Copied {copied_count} files to workspace")
    
    def _process_config_templates(self, config: PackageConfig) -> List[str]:
        """
        Process configuration templates for target platform.
        
        Args:
            config: Package configuration
            
        Returns:
            List of processed template file paths (relative)
            
        Raises:
            RuntimeError: If critical configuration processing fails
        """
        template_files = []
        
        try:
            from .config_processor import ConfigProcessor
            processor = ConfigProcessor(self.project_root, config.target_platform)
            
            # Process templates for each specified directory
            for template_dir in config.config_template_dirs:
                dir_path = self.project_root / template_dir
                if not dir_path.exists():
                    self.logger.debug(f"Config template directory not found: {template_dir}")
                    continue
                    
                # Process templates in directory - any errors will propagate up
                try:
                    processed = processor.process_templates(dir_path, self.workspace_dir)
                    template_files.extend(processed)
                except Exception as e:
                    self.logger.error(f"Configuration template processing failed for {template_dir}: {e}")
                    raise RuntimeError(f"Failed to process configuration templates in {template_dir}: {e}") from e
                    
        except ImportError as e:
            self.logger.error("ConfigProcessor not available - cannot create deployment package")
            raise RuntimeError("ConfigProcessor module required for package creation") from e
            
        return template_files
    
    def _generate_install_scripts(self, config: PackageConfig) -> List[str]:
        """
        Generate installation scripts for target platform.
        
        Args:
            config: Package configuration
            
        Returns:
            List of generated script file paths (relative)
        """
        script_files = []
        
        if not config.create_install_script:
            return script_files
            
        try:
            # Create install script for target platform
            if config.target_platform == "raspberry-pi":
                script_path = self._create_pi_install_script(config)
            else:
                script_path = self._create_generic_install_script(config)
                
            if script_path:
                script_files.append(str(script_path.relative_to(self.workspace_dir)))
                
        except Exception as e:
            self.logger.warning(f"Failed to generate install script: {e}")
            
        return script_files
    
    def _create_pi_install_script(self, config: PackageConfig) -> Optional[Path]:
        """
        Create Raspberry Pi specific installation script.
        
        Args:
            config: Package configuration
            
        Returns:
            Path to created install script
        """
        script_path = self.workspace_dir / "install.sh"
        
        script_content = f"""#!/bin/bash
# GTach Application Installation Script
# Generated: {datetime.now().isoformat()}
# Target Platform: Raspberry Pi

set -e

echo "Installing {config.package_name} v{config.version}..."

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This package is designed for Raspberry Pi"
fi

# Create application directory
APP_DIR="/opt/gtach"
sudo mkdir -p "$APP_DIR"

# Copy application files
echo "Installing application files..."
sudo cp -r src/* "$APP_DIR/"

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Set permissions
sudo chown -R pi:pi "$APP_DIR"
sudo chmod +x "$APP_DIR"/*.py

# Create systemd service if service file exists
if [ -f "gtach.service" ]; then
    echo "Installing systemd service..."
    sudo cp gtach.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable gtach
fi

echo "Installation completed successfully!"
echo "Application installed to: $APP_DIR"
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        # Make script executable
        script_path.chmod(0o755)
        
        self.logger.debug(f"Created Pi install script: {script_path}")
        return script_path
    
    def _create_generic_install_script(self, config: PackageConfig) -> Optional[Path]:
        """
        Create generic installation script.
        
        Args:
            config: Package configuration
            
        Returns:
            Path to created install script
        """
        script_path = self.workspace_dir / "install.py"
        
        script_content = f"""#!/usr/bin/env python3
# GTach Application Installation Script
# Generated: {datetime.now().isoformat()}
# Target Platform: Generic

import os
import sys
import shutil
from pathlib import Path

def main():
    print("Installing {config.package_name} v{config.version}...")
    
    # Determine installation directory
    if os.name == 'posix':  # Unix-like
        app_dir = Path.home() / '.local' / 'gtach'
    else:  # Windows
        app_dir = Path.home() / 'AppData' / 'Local' / 'gtach'
    
    # Create application directory
    app_dir.mkdir(parents=True, exist_ok=True)
    print(f"Installing to: {{app_dir}}")
    
    # Copy application files
    src_dir = Path(__file__).parent / 'src'
    if src_dir.exists():
        for item in src_dir.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(src_dir)
                dest_path = app_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
    
    print("Installation completed successfully!")
    print(f"Application installed to: {{app_dir}}")

if __name__ == "__main__":
    main()
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        # Make script executable on Unix-like systems
        if os.name == 'posix':
            script_path.chmod(0o755)
        
        self.logger.debug(f"Created generic install script: {script_path}")
        return script_path
    
    def _create_manifest(self,
                        config: PackageConfig,
                        source_files: List[Path], 
                        template_files: List[str],
                        script_files: List[str]) -> PackageManifest:
        """
        Create package manifest with file listings and metadata.
        
        Args:
            config: Package configuration
            source_files: List of source files
            template_files: List of template files  
            script_files: List of script files
            
        Returns:
            Package manifest
        """
        # Convert source file paths to relative strings
        source_file_list = []
        for source_file in source_files:
            try:
                rel_path = source_file.relative_to(self.project_root)
                source_file_list.append(str(rel_path))
            except ValueError:
                # File not under project root - use name only
                source_file_list.append(source_file.name)
        
        # Load dependencies if requirements.txt exists
        dependencies = []
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists() and config.include_dependencies:
            try:
                with open(requirements_file, 'r') as f:
                    dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except Exception as e:
                self.logger.warning(f"Failed to read requirements.txt: {e}")
        
        manifest = PackageManifest(
            package_name=config.package_name,
            version=config.version,
            created_at=datetime.now().isoformat(),
            source_platform=self.source_platform.name,
            target_platform=config.target_platform,
            source_files=source_file_list,
            config_templates=template_files,
            scripts=script_files,
            dependencies=dependencies
        )
        
        # Save manifest to workspace immediately (without checksum)
        manifest_path = self.workspace_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
            
        self.logger.debug(f"Created package manifest: {len(source_file_list)} sources, {len(template_files)} templates, {len(script_files)} scripts")
        
        return manifest
    
    def _create_archive(self,
                       config: PackageConfig,
                       manifest: PackageManifest,
                       output_path: Optional[Union[str, Path]]) -> Path:
        """
        Create compressed tar archive of package.
        
        Args:
            config: Package configuration
            manifest: Package manifest
            output_path: Optional output path
            
        Returns:
            Path to created archive
        """
        # Determine output path
        if output_path:
            archive_path = Path(output_path)
        else:
            # Generate simplified filename: gtach-v{version}.tar.gz
            filename = f"gtach-v{config.version}.tar.gz"
            
            if config.output_dir:
                archive_path = Path(config.output_dir) / filename
            else:
                archive_path = self.project_root / "packages" / filename
                
        # Ensure output directory exists
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Log simplified naming decision
        self.logger.info(f"Using simplified package naming format: gtach-v{config.version}.tar.gz")
        self.logger.debug(f"Package naming - Version: {config.version}, Target: {config.target_platform}")
        
        # Create archive
        self.logger.debug(f"Creating archive: {archive_path}")
        
        with tarfile.open(archive_path, 'w:gz', compresslevel=config.compression_level) as tar:
            # Add all files from workspace (including manifest.json)
            for item in self.workspace_dir.rglob('*'):
                if item.is_file():
                    # Calculate archive name (relative to workspace)
                    arcname = item.relative_to(self.workspace_dir)
                    tar.add(item, arcname=arcname)
        
        # Calculate final checksum after complete archive creation
        checksum = self._calculate_file_checksum(archive_path)
        
        # Update manifest object with checksum (for return value only, not archived file)
        # Note: The manifest.json inside the archive will not contain the checksum since
        # it was written before the archive was completed. The checksum is available
        # in the returned manifest object for use by the caller.
        manifest.checksum = checksum
        
        archive_size = archive_path.stat().st_size
        self.logger.info(f"Archive created: {archive_path} ({archive_size:,} bytes, checksum: {checksum[:16]}...)")
        
        return archive_path
    
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
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()
    
    def validate_package_version(self, version_string: str) -> Version:
        """
        Validate and parse package version string.
        
        Args:
            version_string: Version string to validate
            
        Returns:
            Parsed Version object
            
        Raises:
            ValueError: If version is invalid
        """
        return self.version_manager.parse_version(version_string)
    
    def check_version_compatibility(self, version1: str, version2: str) -> str:
        """
        Check compatibility between two package versions.
        
        Args:
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Compatibility level as string
        """
        compatibility = self.version_manager.check_compatibility(version1, version2)
        return compatibility.name.lower().replace('_', ' ')
    
    def resolve_package_dependencies(self, dependencies: Dict[str, str]) -> Dict[str, str]:
        """
        Resolve package dependencies using version constraints.
        
        Args:
            dependencies: Dict mapping package names to version constraints
            
        Returns:
            Dict mapping package names to resolved version strings
        """
        resolved_versions = self.version_manager.resolve_dependencies(dependencies)
        return {name: str(version) for name, version in resolved_versions.items()}
    
    def get_next_version(self, current_version: str, bump_type: str = "patch") -> str:
        """
        Get next version based on bump type.
        
        Args:
            current_version: Current version string
            bump_type: Type of version bump (major, minor, patch)
            
        Returns:
            Next version string
            
        Raises:
            ValueError: If current version is invalid or bump_type is unsupported
        """
        version = self.version_manager.parse_version(current_version)
        
        if bump_type == "major":
            next_version = version.bump_major()
        elif bump_type == "minor":
            next_version = version.bump_minor()
        elif bump_type == "patch":
            next_version = version.bump_patch()
        else:
            raise ValueError(f"Unsupported bump type: {bump_type}. Use 'major', 'minor', or 'patch'")
        
        return str(next_version)
    
    def _verify_package_integrity(self, package_path: Path, manifest: PackageManifest) -> None:
        """
        Verify package integrity by checking archive contents.
        
        Args:
            package_path: Path to package file
            manifest: Package manifest
            
        Raises:
            RuntimeError: If integrity check fails
        """
        self.logger.debug("Verifying package integrity...")
        
        try:
            with tarfile.open(package_path, 'r:gz') as tar:
                # Check that manifest exists
                if 'manifest.json' not in tar.getnames():
                    raise RuntimeError("Package manifest missing from archive")
                    
                # Verify all expected files are present
                archive_files = set(tar.getnames())
                expected_files = set(manifest.source_files + manifest.config_templates + manifest.scripts + ['manifest.json'])
                
                missing_files = expected_files - archive_files
                if missing_files:
                    raise RuntimeError(f"Missing files in archive: {missing_files}")
                    
                # Additional checks could be added here
                # (file sizes, individual checksums, etc.)
                
            self.logger.debug("Package integrity verification passed")
            
        except Exception as e:
            raise RuntimeError(f"Package integrity verification failed: {e}") from e
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get package creator statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._stats_lock:
            stats = {
                'operation_count': self._operation_count,
                'project_root': str(self.project_root),
                'source_platform': self.source_platform.name
            }
            
            # Include version manager stats
            version_stats = self.version_manager.get_stats()
            stats['version_manager'] = version_stats
            
            return stats