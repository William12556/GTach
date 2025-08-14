#!/usr/bin/env python3
"""
Version State Manager for GTach Application Provisioning System

Provides persistent version state management with development stage tracking, 
increment history, and comprehensive session-based logging per Protocol 8.

Features:
- Persistent state storage in .gtach-version file
- Development stage tracking (alpha, beta, rc, release, stable)
- Increment history preservation with comprehensive metadata
- Thread-safe operations with atomic file writes
- Cross-platform compatibility per Protocol 6
- Integration with existing VersionManager for validation

Architecture:
- VersionStateManager: Main coordinator for persistent state operations
- DevelopmentStage: Enumeration of all development stages
- VersionState: Dataclass for state representation
- IncrementHistory: Detailed tracking of version changes
"""

import os
import json
import time
import uuid
import threading
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from contextlib import contextmanager
from enum import Enum, auto
import logging

try:
    from .version_manager import VersionManager, Version
    from .logging_config import get_provisioning_logger
except ImportError:
    # Fallback for development/testing
    import sys
    sys.path.append(str(Path(__file__).parent))
    from version_manager import VersionManager, Version
    from logging_config import get_provisioning_logger

try:
    from ..obdii.utils.platform import get_platform_type, PlatformType
except ImportError:
    # Fallback when running standalone
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from obdii.utils.platform import get_platform_type, PlatformType


class DevelopmentStage(Enum):
    """Development stages for version management"""
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"           # Release candidate
    RELEASE = "release"  # Stable release
    STABLE = "stable"    # Long-term stable
    HOTFIX = "hotfix"    # Emergency fix
    DEV = "dev"         # Development/snapshot

    @classmethod
    def from_version_string(cls, version: str) -> Optional['DevelopmentStage']:
        """
        Extract development stage from version string.
        
        Args:
            version: Version string to analyze
            
        Returns:
            DevelopmentStage or None if no stage found
        """
        version_lower = version.lower()
        
        # Check for explicit stage identifiers
        if 'alpha' in version_lower:
            return cls.ALPHA
        elif 'beta' in version_lower:
            return cls.BETA
        elif 'rc' in version_lower:
            return cls.RC
        elif 'dev' in version_lower or 'snapshot' in version_lower:
            return cls.DEV
        elif 'hotfix' in version_lower:
            return cls.HOTFIX
        elif 'stable' in version_lower:
            return cls.STABLE
        else:
            # Assume release for standard semantic versions
            return cls.RELEASE

    def get_next_stages(self) -> List['DevelopmentStage']:
        """
        Get valid next development stages from current stage.
        
        Returns:
            List of possible next stages
        """
        transitions = {
            self.ALPHA: [self.BETA, self.RC, self.RELEASE, self.ALPHA],
            self.BETA: [self.RC, self.RELEASE, self.BETA], 
            self.RC: [self.RELEASE, self.RC],
            self.RELEASE: [self.STABLE, self.HOTFIX, self.ALPHA, self.BETA],
            self.STABLE: [self.HOTFIX, self.ALPHA, self.BETA],
            self.HOTFIX: [self.STABLE, self.RELEASE],
            self.DEV: [self.ALPHA, self.BETA, self.RC, self.RELEASE, self.DEV]
        }
        
        return transitions.get(self, [])


@dataclass
class IncrementHistory:
    """Detailed increment history entry with comprehensive metadata"""
    
    # Identity
    increment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    
    # Version information
    from_version: Optional[str] = None
    to_version: str = ""
    increment_type: str = "manual"  # manual, auto, hotfix, etc.
    
    # Development stage tracking
    from_stage: Optional[DevelopmentStage] = None
    to_stage: Optional[DevelopmentStage] = None
    stage_transition: bool = False
    
    # Context and metadata
    user_context: str = ""
    session_id: Optional[str] = None
    platform: Optional[str] = None
    operation_context: str = ""
    
    # Validation and verification
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    # Performance metrics
    processing_time_ms: float = 0.0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum serialization"""
        data = asdict(self)
        
        # Serialize enums
        if self.from_stage:
            data['from_stage'] = self.from_stage.value
        if self.to_stage:
            data['to_stage'] = self.to_stage.value
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IncrementHistory':
        """Create from dictionary with enum deserialization"""
        # Handle enum fields
        if 'from_stage' in data and data['from_stage']:
            data['from_stage'] = DevelopmentStage(data['from_stage'])
        if 'to_stage' in data and data['to_stage']:
            data['to_stage'] = DevelopmentStage(data['to_stage'])
            
        return cls(**data)


@dataclass
class VersionState:
    """Comprehensive version state representation with development tracking"""
    
    # Version identification
    current_version: str = "0.1.0-dev"
    current_stage: DevelopmentStage = DevelopmentStage.DEV
    
    # Development progression
    major_version: int = 0
    minor_version: int = 1
    patch_version: int = 0
    prerelease_counter: int = 1
    
    # State metadata
    last_updated: float = field(default_factory=time.time)
    last_session_id: Optional[str] = None
    creation_time: float = field(default_factory=time.time)
    
    # Increment tracking
    total_increments: int = 0
    increment_history: List[IncrementHistory] = field(default_factory=list)
    
    # Stage tracking
    stage_history: List[Tuple[str, DevelopmentStage, float]] = field(default_factory=list)
    
    # Configuration and preferences
    auto_increment_enabled: bool = True
    preferred_stage_progression: List[DevelopmentStage] = field(
        default_factory=lambda: [
            DevelopmentStage.ALPHA,
            DevelopmentStage.BETA, 
            DevelopmentStage.RC,
            DevelopmentStage.RELEASE
        ]
    )
    
    # Platform and environment
    platform_info: Dict[str, str] = field(default_factory=dict)
    
    # Additional metadata
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum serialization"""
        data = asdict(self)
        
        # Serialize enums
        data['current_stage'] = self.current_stage.value
        data['preferred_stage_progression'] = [stage.value for stage in self.preferred_stage_progression]
        
        # Serialize stage history
        data['stage_history'] = [(version, stage.value, timestamp) for version, stage, timestamp in self.stage_history]
        
        # Serialize increment history
        data['increment_history'] = [history.to_dict() for history in self.increment_history]
        
        return data
    
    @classmethod  
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionState':
        """Create from dictionary with enum deserialization"""
        # Handle enum fields
        if 'current_stage' in data:
            data['current_stage'] = DevelopmentStage(data['current_stage'])
        
        if 'preferred_stage_progression' in data:
            data['preferred_stage_progression'] = [
                DevelopmentStage(stage) for stage in data['preferred_stage_progression']
            ]
        
        # Handle stage history
        if 'stage_history' in data:
            data['stage_history'] = [
                (version, DevelopmentStage(stage), timestamp) 
                for version, stage, timestamp in data['stage_history']
            ]
        
        # Handle increment history
        if 'increment_history' in data:
            data['increment_history'] = [
                IncrementHistory.from_dict(history_data) 
                for history_data in data['increment_history']
            ]
        
        return cls(**data)


class VersionStateManager:
    """
    Thread-safe persistent version state manager with comprehensive tracking.
    
    Provides atomic state persistence, development stage management, and
    comprehensive increment history tracking with Protocol 8 compliance.
    """
    
    # Class-level constants
    STATE_FILE_NAME = ".gtach-version"
    BACKUP_FILE_SUFFIX = ".backup"
    DEFAULT_STAGE_FILE_NAME = ".gtach-version-stages"
    
    def __init__(self, project_root: Union[str, Path], session_id: Optional[str] = None):
        """
        Initialize version state manager.
        
        Args:
            project_root: Root directory of project
            session_id: Optional session identifier for logging
        """
        self.project_root = Path(project_root)
        self.state_file_path = self.project_root / self.STATE_FILE_NAME
        self.backup_file_path = self.project_root / f"{self.STATE_FILE_NAME}{self.BACKUP_FILE_SUFFIX}"
        
        # Session management
        self.session_id = session_id or f"version_state_{int(time.time())}"
        
        # Thread safety
        self._state_lock = threading.RLock()
        self._file_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        
        # Logging setup (Protocol 8 compliant)
        self.provisioning_logger = get_provisioning_logger()
        self.logger = self.provisioning_logger.get_logger('version_state_manager')
        
        # Version manager integration
        self.version_manager = VersionManager()
        
        # Platform detection (Protocol 6 compliance)
        try:
            self.platform_type = get_platform_type()
            self.platform_name = self.platform_type.name
        except Exception as e:
            self.logger.warning(f"Platform detection failed: {e}")
            self.platform_type = None
            self.platform_name = "UNKNOWN"
        
        # State management
        self._current_state: Optional[VersionState] = None
        self._state_dirty = False
        
        # Statistics and metrics
        self._operation_count = 0
        self._read_operations = 0
        self._write_operations = 0
        self._backup_operations = 0
        
        self.logger.info(f"VersionStateManager initialized: session={self.session_id}, platform={self.platform_name}")
        
        # Load or initialize state
        self._load_or_initialize_state()
    
    def _load_or_initialize_state(self) -> None:
        """Load existing state or initialize new state"""
        with self._state_lock:
            try:
                if self.state_file_path.exists():
                    self.logger.debug(f"Loading existing state from {self.state_file_path}")
                    self._load_state()
                else:
                    self.logger.info(f"No state file found, initializing new state")
                    self._initialize_new_state()
            except Exception as e:
                self.logger.error(f"Failed to load state, initializing new: {e}")
                self._initialize_new_state()
    
    def _initialize_new_state(self) -> None:
        """Initialize new version state with defaults"""
        with self._state_lock:
            # Create platform info
            platform_info = {
                'platform_type': self.platform_name,
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                'initialization_time': datetime.now(timezone.utc).isoformat()
            }
            
            self._current_state = VersionState(
                current_version="0.1.0-dev",
                current_stage=DevelopmentStage.DEV,
                last_session_id=self.session_id,
                platform_info=platform_info
            )
            
            self.logger.info(f"Initialized new version state: {self._current_state.current_version}")
            
            # Save initial state
            self._save_state()
    
    def _load_state(self) -> None:
        """Load state from persistent storage with error recovery"""
        with self._file_lock:
            self._increment_read_operations()
            
            try:
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self._current_state = VersionState.from_dict(data)
                
                # Update session tracking
                self._current_state.last_session_id = self.session_id
                
                self.logger.info(f"Loaded state: {self._current_state.current_version} "
                               f"(stage: {self._current_state.current_stage.value})")
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.error(f"State file corrupted: {e}")
                self._attempt_backup_recovery()
                
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
                raise
    
    def _attempt_backup_recovery(self) -> None:
        """Attempt to recover from backup file"""
        if self.backup_file_path.exists():
            try:
                self.logger.info("Attempting backup recovery")
                with open(self.backup_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self._current_state = VersionState.from_dict(data)
                self.logger.info("Successfully recovered from backup")
                
                # Save restored state
                self._save_state()
                
            except Exception as e:
                self.logger.error(f"Backup recovery failed: {e}")
                raise RuntimeError(f"State recovery failed: {e}")
        else:
            raise RuntimeError("No backup file available for recovery")
    
    @contextmanager
    def _atomic_state_update(self):
        """Context manager for atomic state updates with backup"""
        with self._state_lock:
            # Create backup before modification
            self._create_backup()
            
            original_state = None
            if self._current_state:
                # Deep copy current state for rollback
                original_state = VersionState.from_dict(self._current_state.to_dict())
            
            try:
                yield
                # Success - save updated state
                self._save_state()
                
            except Exception as e:
                # Rollback on failure
                self.logger.error(f"State update failed, rolling back: {e}")
                if original_state:
                    self._current_state = original_state
                raise
    
    def _create_backup(self) -> None:
        """Create backup of current state file"""
        if self.state_file_path.exists():
            with self._file_lock:
                try:
                    shutil.copy2(self.state_file_path, self.backup_file_path)
                    self._increment_backup_operations()
                    self.logger.debug(f"Created state backup: {self.backup_file_path}")
                    
                except Exception as e:
                    self.logger.warning(f"Backup creation failed: {e}")
    
    def _save_state(self) -> None:
        """Save current state to persistent storage atomically"""
        if not self._current_state:
            raise RuntimeError("No state to save")
            
        with self._file_lock:
            self._increment_write_operations()
            
            # Update state metadata
            self._current_state.last_updated = time.time()
            self._current_state.last_session_id = self.session_id
            
            # Atomic write using temporary file
            temp_path = None
            try:
                # Create temporary file in same directory
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    encoding='utf-8',
                    dir=self.project_root,
                    prefix=f"{self.STATE_FILE_NAME}.tmp",
                    delete=False
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    
                    # Write state data with formatting
                    json.dump(
                        self._current_state.to_dict(),
                        temp_file,
                        indent=2,
                        sort_keys=True
                    )
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                
                # Atomic move to final location
                if os.name == 'nt':  # Windows
                    if self.state_file_path.exists():
                        self.state_file_path.unlink()
                    temp_path.rename(self.state_file_path)
                else:  # Unix-like systems
                    temp_path.rename(self.state_file_path)
                
                self.logger.debug(f"State saved atomically to {self.state_file_path}")
                
            except Exception as e:
                # Cleanup temporary file on failure
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass
                        
                self.logger.error(f"Failed to save state: {e}")
                raise
    
    def get_current_state(self) -> VersionState:
        """
        Get current version state.
        
        Returns:
            VersionState: Current state copy
        """
        with self._state_lock:
            if not self._current_state:
                raise RuntimeError("State not initialized")
                
            # Return deep copy to prevent external modification
            return VersionState.from_dict(self._current_state.to_dict())
    
    def update_version(self, 
                      new_version: str,
                      increment_type: str = "manual",
                      user_context: str = "",
                      operation_context: str = "") -> IncrementHistory:
        """
        Update version with comprehensive tracking.
        
        Args:
            new_version: New version string
            increment_type: Type of increment (manual, auto, hotfix, etc.)
            user_context: User-provided context
            operation_context: Operation context
            
        Returns:
            IncrementHistory: Increment record
            
        Raises:
            ValueError: If version format is invalid
            RuntimeError: If state update fails
        """
        start_time = time.perf_counter()
        
        with self.provisioning_logger.operation_context("version_update", 
                                                       version=new_version, 
                                                       type=increment_type) as operation_id:
            
            # Validate new version
            is_valid, validation_message = self.version_manager.validate_version_format(new_version)
            if not is_valid:
                raise ValueError(f"Invalid version format: {validation_message}")
            
            with self._atomic_state_update():
                # Capture current state
                old_version = self._current_state.current_version
                old_stage = self._current_state.current_stage
                
                # Detect new stage
                new_stage = DevelopmentStage.from_version_string(new_version)
                if not new_stage:
                    new_stage = DevelopmentStage.RELEASE
                
                # Create increment history entry
                processing_time = (time.perf_counter() - start_time) * 1000  # milliseconds
                
                increment = IncrementHistory(
                    from_version=old_version,
                    to_version=new_version,
                    increment_type=increment_type,
                    from_stage=old_stage,
                    to_stage=new_stage,
                    stage_transition=(old_stage != new_stage),
                    user_context=user_context,
                    session_id=self.session_id,
                    platform=self.platform_name,
                    operation_context=operation_context,
                    validation_passed=is_valid,
                    processing_time_ms=processing_time,
                    metadata={
                        'operation_id': operation_id,
                        'validation_message': validation_message
                    }
                )
                
                # Update state
                self._current_state.current_version = new_version
                self._current_state.current_stage = new_stage
                self._current_state.total_increments += 1
                
                # Update semantic version components
                try:
                    parsed_version = self.version_manager.parse_version(new_version)
                    self._current_state.major_version = parsed_version.major
                    self._current_state.minor_version = parsed_version.minor
                    self._current_state.patch_version = parsed_version.patch
                    
                    # Update prerelease counter if applicable
                    if parsed_version.prerelease:
                        # Try to extract numeric part
                        for part in parsed_version.prerelease:
                            if isinstance(part, int):
                                self._current_state.prerelease_counter = part
                                break
                            elif isinstance(part, str) and part.isdigit():
                                self._current_state.prerelease_counter = int(part)
                                break
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse semantic version components: {e}")
                
                # Track stage change
                if increment.stage_transition:
                    self._current_state.stage_history.append((
                        new_version,
                        new_stage,
                        time.time()
                    ))
                    
                    self.logger.info(f"Stage transition: {old_stage.value} -> {new_stage.value}")
                
                # Add to history (keep last 100 entries)
                self._current_state.increment_history.append(increment)
                if len(self._current_state.increment_history) > 100:
                    self._current_state.increment_history = self._current_state.increment_history[-100:]
                
                # Log the update
                self.logger.info(f"Version updated: {old_version} -> {new_version} "
                               f"({increment_type}, session: {self.session_id})")
                
                self._increment_operation_count()
                
                return increment
    
    def suggest_next_version(self, increment_type: str = "minor") -> List[str]:
        """
        Suggest next version options based on current state and stage.
        
        Args:
            increment_type: Type of increment (major, minor, patch, prerelease)
            
        Returns:
            List of suggested version strings
        """
        if not self._current_state:
            return ["0.1.0-dev", "1.0.0-alpha.1"]
        
        suggestions = []
        current = self._current_state
        stage = current.current_stage
        
        try:
            parsed_version = self.version_manager.parse_version(current.current_version)
            
            # Generate suggestions based on increment type and current stage
            if increment_type == "major":
                suggestions.extend([
                    f"{parsed_version.major + 1}.0.0-alpha.1",
                    f"{parsed_version.major + 1}.0.0-beta.1",
                    f"{parsed_version.major + 1}.0.0-rc.1",
                    f"{parsed_version.major + 1}.0.0"
                ])
            elif increment_type == "minor":
                suggestions.extend([
                    f"{parsed_version.major}.{parsed_version.minor + 1}.0-alpha.1",
                    f"{parsed_version.major}.{parsed_version.minor + 1}.0-beta.1",
                    f"{parsed_version.major}.{parsed_version.minor + 1}.0-rc.1",
                    f"{parsed_version.major}.{parsed_version.minor + 1}.0"
                ])
            elif increment_type == "patch":
                suggestions.extend([
                    f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch + 1}-alpha.1",
                    f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch + 1}-beta.1",
                    f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch + 1}-rc.1",
                    f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch + 1}"
                ])
            elif increment_type == "prerelease" and stage != DevelopmentStage.RELEASE:
                # Increment prerelease version
                prerelease_num = current.prerelease_counter + 1
                stage_name = stage.value
                
                suggestions.extend([
                    f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch}-{stage_name}.{prerelease_num}",
                ])
                
                # Suggest stage progressions
                next_stages = stage.get_next_stages()
                for next_stage in next_stages[:3]:  # Limit suggestions
                    suggestions.append(
                        f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch}-{next_stage.value}.1"
                    )
            
            # Add hotfix suggestions if appropriate
            if stage in [DevelopmentStage.RELEASE, DevelopmentStage.STABLE]:
                suggestions.append(
                    f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch + 1}-hotfix.1"
                )
            
            self.logger.debug(f"Generated {len(suggestions)} version suggestions for {increment_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate version suggestions: {e}")
            # Fallback suggestions
            suggestions = ["0.1.0-dev", "1.0.0-alpha.1", "1.0.0"]
        
        return suggestions[:8]  # Limit to reasonable number
    
    def get_increment_history(self, limit: int = 50) -> List[IncrementHistory]:
        """
        Get increment history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of increment history entries (most recent first)
        """
        with self._state_lock:
            if not self._current_state:
                return []
            
            history = self._current_state.increment_history[-limit:] if limit > 0 else self._current_state.increment_history
            return list(reversed(history))  # Most recent first
    
    def get_stage_history(self) -> List[Tuple[str, DevelopmentStage, float]]:
        """
        Get development stage history.
        
        Returns:
            List of (version, stage, timestamp) tuples
        """
        with self._state_lock:
            if not self._current_state:
                return []
                
            return list(self._current_state.stage_history)
    
    def cleanup_old_history(self, keep_days: int = 90) -> int:
        """
        Clean up old increment history entries.
        
        Args:
            keep_days: Number of days of history to keep
            
        Returns:
            Number of entries removed
        """
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
        removed_count = 0
        
        with self._atomic_state_update():
            original_count = len(self._current_state.increment_history)
            
            self._current_state.increment_history = [
                entry for entry in self._current_state.increment_history
                if entry.timestamp >= cutoff_time
            ]
            
            removed_count = original_count - len(self._current_state.increment_history)
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old history entries (keeping {keep_days} days)")
        
        return removed_count
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
    
    def _increment_read_operations(self) -> None:
        """Thread-safe increment of read operations counter"""
        with self._stats_lock:
            self._read_operations += 1
    
    def _increment_write_operations(self) -> None:
        """Thread-safe increment of write operations counter"""
        with self._stats_lock:
            self._write_operations += 1
    
    def _increment_backup_operations(self) -> None:
        """Thread-safe increment of backup operations counter"""
        with self._stats_lock:
            self._backup_operations += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics.
        
        Returns:
            Dictionary with statistics and metadata
        """
        with self._stats_lock:
            state = self.get_current_state() if self._current_state else None
            
            stats = {
                'session_id': self.session_id,
                'platform': self.platform_name,
                'state_file_path': str(self.state_file_path),
                'state_file_exists': self.state_file_path.exists(),
                'backup_file_exists': self.backup_file_path.exists(),
                'operation_count': self._operation_count,
                'read_operations': self._read_operations,
                'write_operations': self._write_operations,
                'backup_operations': self._backup_operations,
            }
            
            if state:
                stats.update({
                    'current_version': state.current_version,
                    'current_stage': state.current_stage.value,
                    'total_increments': state.total_increments,
                    'history_entries': len(state.increment_history),
                    'stage_transitions': len(state.stage_history),
                    'last_updated': state.last_updated,
                    'creation_time': state.creation_time,
                    'auto_increment_enabled': state.auto_increment_enabled,
                    'preferred_stages': [stage.value for stage in state.preferred_stage_progression]
                })
                
                # File size information
                try:
                    if self.state_file_path.exists():
                        stats['state_file_size'] = self.state_file_path.stat().st_size
                    if self.backup_file_path.exists():
                        stats['backup_file_size'] = self.backup_file_path.stat().st_size
                except Exception:
                    pass
            
            return stats