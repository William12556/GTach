#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
GTach Release Utilities
Helper functions for git operations and release automation support.

This module provides utility functions for:
- Git repository operations and validation
- File system operations with safety checks
- Version format validation and parsing
- Network connectivity verification
- Cross-platform compatibility helpers

Author: GTach Project Contributors
Created: 2025-08-17
Protocol: Protocol 13 Release Management Standards
"""

import json
import logging
import os
import platform
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.request import urlopen
from urllib.error import URLError

# Thread-safe operations
_git_lock = threading.Lock()
_file_lock = threading.Lock()

class GitOperationError(Exception):
    """Exception for git operation failures."""
    pass

class ValidationError(Exception):
    """Exception for validation failures."""
    pass

class NetworkError(Exception):
    """Exception for network connectivity issues."""
    pass

def get_logger() -> logging.Logger:
    """Get configured logger instance."""
    return logging.getLogger('release_automation')

def run_git_command(cmd: List[str], cwd: Optional[Path] = None, 
                   timeout: int = 30) -> subprocess.CompletedProcess:
    """Execute git command with thread safety and error handling.
    
    Args:
        cmd: Git command and arguments
        cwd: Working directory
        timeout: Command timeout in seconds
        
    Returns:
        CompletedProcess instance
        
    Raises:
        GitOperationError: On git command failure
    """
    logger = get_logger()
    
    with _git_lock:
        try:
            full_cmd = ['git'] + cmd
            logger.debug(f"Executing git command: {' '.join(full_cmd)}")
            
            result = subprocess.run(
                full_cmd,
                cwd=cwd or Path.cwd(),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            if result.returncode != 0:
                error_msg = f"Git command failed: {' '.join(full_cmd)}\n"
                error_msg += f"Return code: {result.returncode}\n"
                if result.stderr:
                    error_msg += f"Error: {result.stderr}"
                raise GitOperationError(error_msg)
                
            return result
            
        except subprocess.TimeoutExpired as e:
            raise GitOperationError(f"Git command timeout: {' '.join(full_cmd)}")
        except Exception as e:
            raise GitOperationError(f"Git command execution failed: {e}")

def get_git_repository_info(repo_path: Optional[Path] = None) -> Dict[str, str]:
    """Get comprehensive git repository information.
    
    Args:
        repo_path: Path to git repository
        
    Returns:
        Dictionary with repository information
        
    Raises:
        GitOperationError: If not a git repository or operation fails
    """
    work_path = repo_path or Path.cwd()
    
    try:
        # Verify this is a git repository
        run_git_command(['rev-parse', '--git-dir'], cwd=work_path)
        
        # Get repository information
        info = {}
        
        # Current branch
        result = run_git_command(['branch', '--show-current'], cwd=work_path)
        info['current_branch'] = result.stdout.strip()
        
        # Remote URL
        try:
            result = run_git_command(['config', '--get', 'remote.origin.url'], cwd=work_path)
            info['remote_url'] = result.stdout.strip()
        except GitOperationError:
            info['remote_url'] = ''
            
        # Latest commit
        result = run_git_command(['rev-parse', 'HEAD'], cwd=work_path)
        info['latest_commit'] = result.stdout.strip()
        
        # Repository status
        result = run_git_command(['status', '--porcelain'], cwd=work_path)
        info['has_changes'] = bool(result.stdout.strip())
        
        # Check if ahead/behind remote
        try:
            run_git_command(['fetch', '--dry-run'], cwd=work_path, timeout=10)
            result = run_git_command(['rev-list', '--count', '--left-right', 'HEAD...@{upstream}'], cwd=work_path)
            ahead_behind = result.stdout.strip().split('\t')
            info['commits_ahead'] = int(ahead_behind[0]) if len(ahead_behind) > 0 else 0
            info['commits_behind'] = int(ahead_behind[1]) if len(ahead_behind) > 1 else 0
        except (GitOperationError, ValueError, IndexError):
            info['commits_ahead'] = 0
            info['commits_behind'] = 0
            
        return info
        
    except GitOperationError as e:
        raise GitOperationError(f"Failed to get repository info: {e}")

def validate_git_repository_state(repo_path: Optional[Path] = None, 
                                required_branch: str = 'main') -> bool:
    """Validate git repository is in suitable state for release.
    
    Args:
        repo_path: Path to git repository
        required_branch: Required branch name
        
    Returns:
        True if repository state is valid
        
    Raises:
        ValidationError: If repository state is invalid
    """
    logger = get_logger()
    
    try:
        info = get_git_repository_info(repo_path)
        
        # Check branch
        if info['current_branch'] != required_branch:
            raise ValidationError(
                f"Must be on {required_branch} branch. Current: {info['current_branch']}"
            )
            
        # Check for uncommitted changes
        if info['has_changes']:
            raise ValidationError("Repository has uncommitted changes")
            
        # Check if behind remote
        if info['commits_behind'] > 0:
            raise ValidationError(
                f"Repository is {info['commits_behind']} commits behind remote"
            )
            
        logger.info("Git repository state validation passed")
        return True
        
    except GitOperationError as e:
        raise ValidationError(f"Git repository validation failed: {e}")

def get_existing_tags(repo_path: Optional[Path] = None, pattern: str = 'v*') -> List[str]:
    """Get list of existing git tags matching pattern.
    
    Args:
        repo_path: Path to git repository
        pattern: Tag pattern to match
        
    Returns:
        List of matching tags
    """
    try:
        result = run_git_command(['tag', '-l', pattern], cwd=repo_path)
        tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
        return sorted(tags)
        
    except GitOperationError:
        return []

def tag_exists(tag_name: str, repo_path: Optional[Path] = None) -> bool:
    """Check if git tag exists.
    
    Args:
        tag_name: Tag name to check
        repo_path: Path to git repository
        
    Returns:
        True if tag exists
    """
    try:
        run_git_command(['rev-parse', '--verify', f'refs/tags/{tag_name}'], cwd=repo_path)
        return True
    except GitOperationError:
        return False

def validate_version_format(version: str) -> Dict[str, Union[str, int, bool]]:
    """Validate and parse version string format.
    
    Args:
        version: Version string to validate
        
    Returns:
        Dictionary with parsed version information
        
    Raises:
        ValidationError: If version format is invalid
    """
    logger = get_logger()
    
    # Protocol 13 numeric version format patterns
    patterns = {
        'development': r'^(\d+)\.(\d+)\.(\d+)\.0(\d{2})$',
        'alpha': r'^(\d+)\.(\d+)\.(\d+)\.1(\d{2})$',
        'beta': r'^(\d+)\.(\d+)\.(\d+)\.2(\d{2})$',
        'rc': r'^(\d+)\.(\d+)\.(\d+)\.3(\d{2})$',
        'production': r'^(\d+)\.(\d+)\.(\d+)$'
    }
    
    for phase, pattern in patterns.items():
        match = re.match(pattern, version)
        if match:
            groups = match.groups()
            
            result = {
                'phase': phase,
                'major': int(groups[0]),
                'minor': int(groups[1]),
                'patch': int(groups[2]),
                'is_prerelease': phase != 'production',
                'original': version
            }
            
            if len(groups) > 3:
                result['iteration'] = int(groups[3])
            else:
                result['iteration'] = 0
                
            logger.debug(f"Version {version} validated as {phase} release")
            return result
    
    raise ValidationError(f"Invalid version format: {version}")

def safe_file_operation(operation: callable, *args, max_retries: int = 3, 
                       retry_delay: float = 0.5, **kwargs):
    """Execute file operation with thread safety and retry logic.
    
    Args:
        operation: File operation function to execute
        *args: Positional arguments for operation
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds
        **kwargs: Keyword arguments for operation
        
    Returns:
        Operation result
        
    Raises:
        Exception: If operation fails after all retries
    """
    logger = get_logger()
    
    with _file_lock:
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"File operation failed (attempt {attempt + 1}): {e}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"File operation failed after {max_retries} attempts: {e}")
                    
        raise last_exception

def validate_file_permissions(file_path: Path, required_permissions: str = 'r') -> bool:
    """Validate file exists and has required permissions.
    
    Args:
        file_path: Path to file
        required_permissions: Required permissions ('r', 'w', 'x', 'rw', etc.)
        
    Returns:
        True if file has required permissions
        
    Raises:
        ValidationError: If file doesn't exist or lacks permissions
    """
    if not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
        
    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
        
    # Check permissions
    checks = {
        'r': file_path.readable,
        'w': file_path.writable,
        'x': lambda: os.access(file_path, os.X_OK)
    }
    
    for perm in required_permissions:
        if perm in checks and not checks[perm]():
            raise ValidationError(f"File lacks {perm} permission: {file_path}")
            
    return True

def check_network_connectivity(timeout: int = 10) -> bool:
    """Check network connectivity to GitHub.
    
    Args:
        timeout: Connection timeout in seconds
        
    Returns:
        True if connectivity is available
    """
    logger = get_logger()
    
    try:
        with urlopen('https://api.github.com', timeout=timeout) as response:
            if response.status == 200:
                logger.debug("Network connectivity verified")
                return True
    except URLError as e:
        logger.warning(f"Network connectivity check failed: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error during connectivity check: {e}")
        
    return False

def get_platform_info() -> Dict[str, str]:
    """Get current platform information.
    
    Returns:
        Dictionary with platform details
    """
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'platform': platform.platform()
    }

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def validate_asset_file(file_path: Path) -> Dict[str, Union[str, int, bool]]:
    """Validate release asset file.
    
    Args:
        file_path: Path to asset file
        
    Returns:
        Dictionary with asset information
        
    Raises:
        ValidationError: If asset is invalid
    """
    logger = get_logger()
    
    # Check file exists and permissions
    validate_file_permissions(file_path, 'r')
    
    # Get file information
    stat = file_path.stat()
    
    # Validate file size (not empty, not too large)
    if stat.st_size == 0:
        raise ValidationError(f"Asset file is empty: {file_path}")
        
    max_size = 100 * 1024 * 1024  # 100MB limit
    if stat.st_size > max_size:
        raise ValidationError(f"Asset file too large (>{format_file_size(max_size)}): {file_path}")
    
    # Validate file extension
    valid_extensions = {'.tar.gz', '.zip', '.whl', '.egg', '.tar', '.bz2'}
    if not any(str(file_path).endswith(ext) for ext in valid_extensions):
        logger.warning(f"Unusual asset file extension: {file_path}")
    
    asset_info = {
        'path': str(file_path),
        'name': file_path.name,
        'size_bytes': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'modified_time': stat.st_mtime,
        'is_valid': True
    }
    
    logger.debug(f"Asset validated: {file_path.name} ({asset_info['size_formatted']})")
    return asset_info

def create_temp_file(content: str, suffix: str = '.tmp', prefix: str = 'release_') -> Path:
    """Create temporary file with content.
    
    Args:
        content: Content to write to file
        suffix: File suffix
        prefix: File prefix
        
    Returns:
        Path to temporary file
    """
    import tempfile
    
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=suffix, 
        prefix=prefix, 
        delete=False
    ) as f:
        f.write(content)
        return Path(f.name)

def cleanup_temp_files(temp_files: List[Path]) -> None:
    """Clean up temporary files safely.
    
    Args:
        temp_files: List of temporary file paths to remove
    """
    logger = get_logger()
    
    for temp_file in temp_files:
        try:
            if temp_file.exists():
                temp_file.unlink()
                logger.debug(f"Cleaned up temp file: {temp_file}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")

def get_repo_owner_and_name(repo_path: Optional[Path] = None) -> Tuple[str, str]:
    """Extract repository owner and name from git remote.
    
    Args:
        repo_path: Path to git repository
        
    Returns:
        Tuple of (owner, repository_name)
        
    Raises:
        ValidationError: If cannot extract repository information
    """
    try:
        info = get_git_repository_info(repo_path)
        remote_url = info['remote_url']
        
        if not remote_url:
            raise ValidationError("No remote URL configured")
            
        # Parse GitHub URLs
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
            r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, remote_url)
            if match:
                return match.group(1), match.group(2)
                
        raise ValidationError(f"Could not parse repository URL: {remote_url}")
        
    except GitOperationError as e:
        raise ValidationError(f"Failed to get repository information: {e}")

def validate_github_cli_auth() -> Dict[str, str]:
    """Validate GitHub CLI authentication and get user info.
    
    Returns:
        Dictionary with authentication information
        
    Raises:
        ValidationError: If authentication fails
    """
    logger = get_logger()
    
    try:
        # Check auth status
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise ValidationError("GitHub CLI not authenticated")
            
        # Get user information
        user_result = subprocess.run(
            ['gh', 'api', 'user'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if user_result.returncode != 0:
            raise ValidationError("Failed to get GitHub user information")
            
        user_data = json.loads(user_result.stdout)
        
        auth_info = {
            'username': user_data.get('login', ''),
            'user_id': str(user_data.get('id', '')),
            'email': user_data.get('email', ''),
            'name': user_data.get('name', '')
        }
        
        logger.info(f"GitHub CLI authenticated as: {auth_info['username']}")
        return auth_info
        
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as e:
        raise ValidationError(f"GitHub CLI authentication validation failed: {e}")
    except Exception as e:
        raise ValidationError(f"Unexpected error during auth validation: {e}")

# Utility functions for common operations
def ensure_directory_exists(dir_path: Path) -> None:
    """Ensure directory exists, create if necessary."""
    safe_file_operation(dir_path.mkdir, parents=True, exist_ok=True)

def get_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate file hash."""
    import hashlib
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()