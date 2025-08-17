#!/usr/bin/env python3
"""
GTach Release Automation System
Automated release creation with git CLI authentication and GitHub integration.

This script provides comprehensive release automation including:
- Version detection from pyproject.toml
- Asset discovery and validation
- GitHub release creation via git CLI
- Release notes extraction from RELEASE_NOTES.md
- Branch validation (main branch only)
- Comprehensive error handling and rollback

Author: GTach Project Contributors
Created: 2025-08-17
Protocol: Protocol 13 Release Management Standards
"""

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        # Fallback to configparser for older Python versions
        import configparser
        tomllib = None

# Thread-safe logging configuration
_log_lock = threading.Lock()

def setup_logging(debug: bool = False) -> logging.Logger:
    """Setup thread-safe logging with traceback support."""
    with _log_lock:
        logger = logging.getLogger('release_automation')
        if logger.handlers:
            return logger
            
        level = logging.DEBUG if debug else logging.INFO
        logger.setLevel(level)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

class ReleaseError(Exception):
    """Custom exception for release automation errors."""
    pass

class GitAuthError(ReleaseError):
    """Exception for git authentication failures."""
    pass

class BranchValidationError(ReleaseError):
    """Exception for branch validation failures."""
    pass

class AssetValidationError(ReleaseError):
    """Exception for asset validation failures.""" 
    pass

class ReleaseAutomation:
    """Main release automation class with comprehensive error handling."""
    
    def __init__(self, project_root: Optional[Path] = None, debug: bool = False):
        """Initialize release automation system.
        
        Args:
            project_root: Path to project root directory
            debug: Enable debug logging with traceback
        """
        self.logger = setup_logging(debug)
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.debug = debug
        self._verify_project_structure()
        
    def _verify_project_structure(self) -> None:
        """Verify required project structure exists."""
        required_files = ['pyproject.toml', 'RELEASE_NOTES.md']
        required_dirs = ['packages']
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                raise ReleaseError(f"Required file missing: {file_path}")
                
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                self.logger.warning(f"Creating missing directory: {dir_path}")
                (self.project_root / dir_path).mkdir(exist_ok=True)
    
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                    capture_output: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute command with comprehensive error handling.
        
        Args:
            cmd: Command and arguments as list
            cwd: Working directory for command
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds
            
        Returns:
            CompletedProcess instance
            
        Raises:
            ReleaseError: On command execution failure
        """
        work_dir = cwd or self.project_root
        self.logger.debug(f"Executing: {' '.join(cmd)} in {work_dir}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False
            )
            
            if result.returncode != 0:
                error_msg = f"Command failed: {' '.join(cmd)}\n"
                error_msg += f"Return code: {result.returncode}\n"
                if result.stderr:
                    error_msg += f"Error: {result.stderr}"
                if result.stdout:
                    error_msg += f"Output: {result.stdout}"
                    
                self.logger.error(error_msg)
                raise ReleaseError(error_msg)
                
            self.logger.debug(f"Command succeeded: {result.stdout}")
            return result
            
        except subprocess.TimeoutExpired as e:
            raise ReleaseError(f"Command timeout after {timeout}s: {' '.join(cmd)}")
        except Exception as e:
            if self.debug:
                import traceback
                self.logger.error(f"Command execution error: {traceback.format_exc()}")
            raise ReleaseError(f"Failed to execute command: {e}")
    
    def validate_git_auth(self) -> None:
        """Validate git CLI authentication.
        
        Raises:
            GitAuthError: If git authentication fails
        """
        try:
            # Test git authentication with a simple API call
            self.logger.info("Validating git CLI authentication...")
            result = self._run_command(['gh', 'auth', 'status'], timeout=10)
            
            if 'Logged in to github.com' not in result.stderr:
                raise GitAuthError("GitHub CLI not authenticated")
                
            self.logger.info("Git CLI authentication validated")
            
        except subprocess.CalledProcessError as e:
            raise GitAuthError(f"Git authentication validation failed: {e}")
        except Exception as e:
            if self.debug:
                import traceback
                self.logger.error(f"Auth validation error: {traceback.format_exc()}")
            raise GitAuthError(f"Failed to validate git authentication: {e}")
    
    def validate_current_branch(self) -> str:
        """Validate current branch is main.
        
        Returns:
            Current branch name
            
        Raises:
            BranchValidationError: If not on main branch
        """
        try:
            result = self._run_command(['git', 'branch', '--show-current'])
            current_branch = result.stdout.strip()
            
            if current_branch != 'main':
                raise BranchValidationError(
                    f"Releases must be created from main branch. Current: {current_branch}"
                )
                
            self.logger.info(f"Branch validation passed: {current_branch}")
            return current_branch
            
        except Exception as e:
            if self.debug:
                import traceback
                self.logger.error(f"Branch validation error: {traceback.format_exc()}")
            raise BranchValidationError(f"Failed to validate branch: {e}")
    
    def get_project_version(self) -> str:
        """Extract version from pyproject.toml.
        
        Returns:
            Version string
            
        Raises:
            ReleaseError: If version extraction fails
        """
        pyproject_path = self.project_root / 'pyproject.toml'
        
        try:
            if tomllib:
                # Use tomllib/tomli for proper TOML parsing
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                version = data['project']['version']
            else:
                # Fallback to configparser with manual parsing
                with open(pyproject_path, 'r') as f:
                    content = f.read()
                    
                # Simple regex extraction for version
                version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if not version_match:
                    raise ReleaseError("Could not find version in pyproject.toml")
                version = version_match.group(1)
            
            self.logger.info(f"Detected project version: {version}")
            return version
            
        except Exception as e:
            if self.debug:
                import traceback
                self.logger.error(f"Version detection error: {traceback.format_exc()}")
            raise ReleaseError(f"Failed to extract version: {e}")
    
    def discover_assets(self) -> List[Path]:
        """Discover and validate release assets in packages directory.
        
        Returns:
            List of asset file paths
            
        Raises:
            AssetValidationError: If no valid assets found
        """
        packages_dir = self.project_root / 'packages'
        
        if not packages_dir.exists():
            raise AssetValidationError("Packages directory not found")
            
        # Look for common release asset patterns
        asset_patterns = ['*.tar.gz', '*.zip', '*.whl', '*.egg']
        assets = []
        
        for pattern in asset_patterns:
            assets.extend(packages_dir.glob(pattern))
            
        if not assets:
            raise AssetValidationError("No release assets found in packages directory")
            
        # Validate asset files exist and are readable
        validated_assets = []
        for asset in assets:
            if asset.is_file() and asset.stat().st_size > 0:
                validated_assets.append(asset)
                self.logger.info(f"Found asset: {asset.name}")
            else:
                self.logger.warning(f"Skipping invalid asset: {asset}")
                
        if not validated_assets:
            raise AssetValidationError("No valid assets found")
            
        return validated_assets
    
    def extract_release_notes(self, version: str) -> str:
        """Extract release notes for specific version.
        
        Args:
            version: Version to extract notes for
            
        Returns:
            Release notes content
        """
        release_notes_path = self.project_root / 'RELEASE_NOTES.md'
        
        try:
            with open(release_notes_path, 'r') as f:
                content = f.read()
                
            # Extract current release section
            # Look for version-specific patterns
            version_patterns = [
                f"## Current Release: v{version}",
                f"## Release: v{version}",
                f"# Version {version}",
                f"## Version {version}"
            ]
            
            for pattern in version_patterns:
                if pattern in content:
                    # Extract section until next major heading
                    start_idx = content.find(pattern)
                    next_section = content.find('\n## ', start_idx + len(pattern))
                    if next_section == -1:
                        next_section = content.find('\n# ', start_idx + len(pattern))
                    
                    if next_section != -1:
                        notes = content[start_idx:next_section].strip()
                    else:
                        notes = content[start_idx:].strip()
                        
                    self.logger.info(f"Extracted release notes for version {version}")
                    return notes
                    
            # Fallback: use current release section
            current_release_start = content.find('## Current Release:')
            if current_release_start != -1:
                next_section = content.find('\n---', current_release_start)
                if next_section != -1:
                    notes = content[current_release_start:next_section].strip()
                else:
                    # Take first 1000 characters as fallback
                    notes = content[current_release_start:current_release_start + 1000].strip()
                    
                self.logger.info("Using current release notes section")
                return notes
                
            # Final fallback
            self.logger.warning("Could not extract version-specific notes, using default")
            return f"Release notes for version {version}\n\nFor detailed information, see RELEASE_NOTES.md"
            
        except Exception as e:
            self.logger.warning(f"Failed to extract release notes: {e}")
            return f"Release notes for version {version}\n\nFor detailed information, see RELEASE_NOTES.md"
    
    def create_github_release(self, version: str, assets: List[Path], 
                            release_notes: str, prerelease: bool = None) -> str:
        """Create GitHub release with assets.
        
        Args:
            version: Version tag
            assets: List of asset files to upload
            release_notes: Release notes content
            prerelease: Whether this is a prerelease (auto-detect if None)
            
        Returns:
            Release URL
            
        Raises:
            ReleaseError: If release creation fails
        """
        tag_name = f"v{version}"
        
        # Auto-detect prerelease status from version
        if prerelease is None:
            prerelease = any(x in version.lower() for x in ['alpha', 'beta', 'rc', '.0', '.1', '.2', '.3'])
            
        self.logger.info(f"Creating GitHub release: {tag_name} (prerelease: {prerelease})")
        
        try:
            # Create release using gh CLI
            cmd = [
                'gh', 'release', 'create', tag_name,
                '--title', f"Release {tag_name}",
                '--notes', release_notes
            ]
            
            if prerelease:
                cmd.append('--prerelease')
                
            # Add assets to command
            for asset in assets:
                cmd.append(str(asset))
                
            result = self._run_command(cmd, timeout=120)
            
            # Extract release URL from output
            release_url = result.stdout.strip()
            if not release_url.startswith('http'):
                # Fallback URL construction
                repo_result = self._run_command(['gh', 'repo', 'view', '--json', 'url'])
                repo_data = json.loads(repo_result.stdout)
                release_url = f"{repo_data['url']}/releases/tag/{tag_name}"
                
            self.logger.info(f"Release created successfully: {release_url}")
            return release_url
            
        except Exception as e:
            if self.debug:
                import traceback
                self.logger.error(f"Release creation error: {traceback.format_exc()}")
            raise ReleaseError(f"Failed to create GitHub release: {e}")
    
    def rollback_release(self, version: str) -> None:
        """Rollback release creation on failure.
        
        Args:
            version: Version to rollback
        """
        tag_name = f"v{version}"
        self.logger.warning(f"Attempting to rollback release: {tag_name}")
        
        try:
            # Delete release if it exists
            self._run_command(['gh', 'release', 'delete', tag_name, '--yes'], timeout=30)
            self.logger.info(f"Rollback completed for {tag_name}")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
    
    def create_release(self, auto_confirm: bool = False) -> Tuple[str, str]:
        """Main release creation workflow.
        
        Args:
            auto_confirm: Skip user confirmation prompts
            
        Returns:
            Tuple of (version, release_url)
            
        Raises:
            ReleaseError: If any step fails
        """
        try:
            # Step 1: Validate environment
            self.logger.info("Starting release creation workflow...")
            self.validate_git_auth()
            self.validate_current_branch()
            
            # Step 2: Get version and assets
            version = self.get_project_version()
            assets = self.discover_assets()
            release_notes = self.extract_release_notes(version)
            
            # Step 3: User confirmation (unless auto-confirm)
            if not auto_confirm:
                print(f"\nRelease Summary:")
                print(f"Version: {version}")
                print(f"Assets: {[a.name for a in assets]}")
                print(f"Release Notes Preview:\n{release_notes[:200]}...")
                
                confirm = input("\nProceed with release creation? (y/N): ").strip().lower()
                if confirm != 'y':
                    self.logger.info("Release creation cancelled by user")
                    return version, ""
            
            # Step 4: Create release
            release_url = self.create_github_release(version, assets, release_notes)
            
            self.logger.info("Release creation completed successfully")
            return version, release_url
            
        except Exception as e:
            if self.debug:
                import traceback
                self.logger.error(f"Release workflow error: {traceback.format_exc()}")
                
            # Attempt rollback on failure
            try:
                if 'version' in locals():
                    self.rollback_release(version)
            except:
                pass
                
            raise ReleaseError(f"Release creation failed: {e}")

def main():
    """Main entry point for release automation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GTach Release Automation System')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--auto-confirm', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--project-root', type=Path, help='Project root directory')
    
    args = parser.parse_args()
    
    try:
        automation = ReleaseAutomation(
            project_root=args.project_root,
            debug=args.debug
        )
        
        version, release_url = automation.create_release(auto_confirm=args.auto_confirm)
        
        if release_url:
            print(f"\n✅ Release {version} created successfully!")
            print(f"📦 Release URL: {release_url}")
        else:
            print(f"\n❌ Release creation was cancelled")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Release creation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()