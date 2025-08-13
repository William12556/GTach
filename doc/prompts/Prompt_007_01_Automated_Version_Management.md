# Claude Code Prompt: Automated Version Management Implementation

**Created**: 2025 08 13

## Prompt Header

**Prompt ID**: Prompt_007_01_Automated_Version_Management  
**Task Type**: Feature Implementation  
**Complexity**: Complex  
**Priority**: High  

## Context

The GTach project currently has version inconsistencies across multiple files (pyproject.toml uses dynamic versioning, setup.py has "1.0.0", __init__.py has "0.1.0", PackageConfig defaults to "1.0.0"). We need to implement an automated version management system that:

1. Standardizes project version to v0.1.0-alpha.1 across all files
2. Provides automated version updating capabilities
3. Integrates with the existing provisioning workflow in create_package.py
4. Enables interactive version setting and automatic incrementing

The system must maintain thread safety, provide atomic updates with rollback capability, and integrate seamlessly with existing Protocol standards.

## Protocol Review Required

- Review Protocol 1 (Project Structure Standards) for file organization compliance
- Review Protocol 3 (Documentation Standards) for code documentation requirements
- Review Protocol 8 (Logging and Debug Standards) for logging implementation
- Apply thread safety requirements and error handling per protocol standards

## Issue Description

**Current State**: Version fragmentation across project files creates confusion and potential deployment issues. The provisioning system requires manual version coordination without automated consistency checking.

**Technical Requirements**:
- Remove dynamic versioning from pyproject.toml, standardize to static versioning
- Update all version strings to v0.1.0-alpha.1 consistently
- Create ProjectVersionManager for coordinating version updates across files
- Implement FileVersionUpdater classes for different file types
- Integrate version management into create_package.py workflow
- Provide automatic version incrementing (patch, minor, major)
- Maintain atomic updates with backup/restore for error recovery

**Integration Points**:
- Existing version_manager.py for SemVer validation
- create_package.py for workflow integration
- Protocol 8 logging standards
- Protocol 1 project structure compliance

## Solution Strategy

**High-Level Approach**: Create a comprehensive version management system with three main components:

1. **ProjectVersionManager**: Central coordinator for version operations across all project files
2. **FileVersionUpdater**: Specialized handlers for different file types (Python, TOML, JSON)
3. **VersionWorkflow**: Integration layer for provisioning workflow with interactive and automatic modes

**Architecture Pattern**: Use Command pattern for version operations to enable rollback, Strategy pattern for file-type specific updates, and Observer pattern for update coordination.

**Error Handling**: Implement atomic updates with backup creation before changes and complete rollback on any failure.

## Implementation Plan

### Primary Implementation: ProjectVersionManager Module

**File**: `src/provisioning/project_version_manager.py`

Create comprehensive version management system with:

```python
class ProjectVersionManager:
    \"\"\"Central coordinator for project version management\"\"\"
    def __init__(self, project_root: Path)
    def set_project_version(self, version: str) -> bool
    def get_current_version(self) -> Optional[str]
    def increment_version(self, bump_type: str) -> str
    def validate_consistency(self) -> Dict[str, str]
    def _create_backup(self) -> str
    def _restore_backup(self, backup_id: str) -> None

class FileVersionUpdater:
    \"\"\"Base class for file-specific version updates\"\"\"
    def update_version(self, file_path: Path, new_version: str) -> bool
    def get_current_version(self, file_path: Path) -> Optional[str]
    def validate_file(self, file_path: Path) -> bool

class PyProjectUpdater(FileVersionUpdater):
    \"\"\"Handle pyproject.toml version updates\"\"\"
    # Remove dynamic = ["version"], add version = "x.y.z"

class SetupPyUpdater(FileVersionUpdater):
    \"\"\"Handle setup.py version updates\"\"\"
    # Update version="x.y.z" in setup() call

class InitPyUpdater(FileVersionUpdater):
    \"\"\"Handle __init__.py __version__ updates\"\"\"
    # Update __version__ = "x.y.z"

class PackageConfigUpdater(FileVersionUpdater):
    \"\"\"Handle PackageConfig default version\"\"\"
    # Update version: str = "x.y.z" in dataclass

class VersionWorkflow:
    \"\"\"Integration with provisioning workflow\"\"\"
    def __init__(self, project_version_manager: ProjectVersionManager)
    def interactive_version_set(self) -> str
    def auto_increment_after_package(self, bump_type: str = "patch") -> str
    def validate_and_prompt_fix(self) -> bool
```

**Thread Safety**: Use threading.RLock for all file operations
**Error Handling**: Comprehensive exception handling with Protocol 8 logging
**Backup Strategy**: Create timestamped backups before any changes
**Validation**: SemVer validation using existing VersionManager

### Supporting Implementation: File Updates

**Update Target Files to v0.1.0-alpha.1**:

1. **pyproject.toml**: Remove `dynamic = ["version"]`, add `version = "0.1.0-alpha.1"`
2. **setup.py**: Update to `version="0.1.0-alpha.1"`
3. **src/obdii/__init__.py**: Update to `__version__ = "0.1.0-alpha.1"`
4. **src/provisioning/package_creator.py**: Update PackageConfig default to `version: str = "0.1.0-alpha.1"`

### Integration Implementation: Workflow Enhancement

**File**: `src/provisioning/create_package.py`

**Modifications**:
- Replace manual version input with ProjectVersionManager integration
- Add version consistency validation before package creation
- Implement post-package version increment option
- Maintain backward compatibility with existing workflow

**Key Changes**:
```python
# Replace get_user_version_input() with:
def get_managed_version_input(project_root: Path) -> str:
    \"\"\"Get version using ProjectVersionManager with consistency checking\"\"\"
    
# Add post-package increment:
def handle_post_package_increment(project_root: Path, package_version: str) -> None:
    \"\"\"Optional automatic version increment after successful package creation\"\"\"

# Integrate into main() workflow
```

## Success Criteria

### Functional Requirements
- [ ] All project files show consistent v0.1.0-alpha.1 version after implementation
- [ ] Interactive version setting with SemVer validation and user-friendly prompts
- [ ] Automatic version incrementing (patch, minor, major) with file coordination
- [ ] Version consistency validation detecting and reporting mismatches
- [ ] Complete error recovery with backup/restore on any failure
- [ ] Seamless integration with existing create_package.py workflow

### Quality Requirements
- [ ] Thread-safe implementation with proper locking for file operations
- [ ] Comprehensive logging with session timestamps per Protocol 8
- [ ] 90%+ test coverage for all version management components
- [ ] Performance: Version updates complete within 2 seconds
- [ ] Atomic updates: All files updated successfully or all rollback
- [ ] Cross-platform compatibility (Mac development, Pi deployment)

### Integration Requirements
- [ ] No breaking changes to existing provisioning workflow
- [ ] Backward compatibility with manual version input as fallback
- [ ] Integration with existing VersionManager for SemVer validation
- [ ] Protocol 1 compliance for project structure and file organization

## Dependencies

### Internal Dependencies
- `src/provisioning/version_manager.py`: Use existing SemVer validation
- `src/provisioning/create_package.py`: Integration point for workflow
- `src/obdii/utils/config.py`: Configuration management patterns
- Protocol 8 logging configuration

### Standard Library Dependencies
- `pathlib`: Cross-platform file handling
- `re`: Regex for version string matching and replacement
- `json`: JSON file parsing for configuration files
- `configparser`: INI/TOML file handling
- `threading`: Thread safety for file operations
- `tempfile`: Backup directory management
- `shutil`: File backup and restore operations

### File System Requirements
- Read/write access to project root directory
- Temporary directory access for backup creation
- File permission preservation during updates

## Claude Code Prompt

```
ITERATION: 007
TASK: Automated Version Management System Implementation
CONTEXT: GTach project has version inconsistencies across pyproject.toml (dynamic), setup.py (1.0.0), __init__.py (0.1.0), and PackageConfig (1.0.0). Need automated system to manage versions consistently and integrate with provisioning workflow.

PROTOCOL REVIEW REQUIRED:
- Review Protocol 1 (Project Structure Standards) for file organization
- Review Protocol 3 (Documentation Standards) for code documentation
- Review Protocol 8 (Logging and Debug Standards) for logging implementation
- Apply thread safety and error handling per protocol standards

ISSUE DESCRIPTION: 
Create ProjectVersionManager system with FileVersionUpdater classes for different file types. Implement atomic updates with backup/restore, integrate with create_package.py workflow, provide interactive version setting and automatic incrementing. Update all files to v0.1.0-alpha.1 consistently.

SOLUTION STRATEGY: 
Three-component architecture: ProjectVersionManager (coordinator), FileVersionUpdater (file-specific handlers), VersionWorkflow (provisioning integration). Use Command pattern for rollback, Strategy pattern for file types, atomic updates with comprehensive error handling.

IMPLEMENTATION PLAN:
1. Create src/provisioning/project_version_manager.py with ProjectVersionManager, FileVersionUpdater base class, and specific updaters (PyProjectUpdater, SetupPyUpdater, InitPyUpdater, PackageConfigUpdater)
2. Implement VersionWorkflow for create_package.py integration
3. Create comprehensive test suite in src/tests/provisioning/test_project_version_manager.py
4. Update create_package.py to use new version management system
5. Ensure all project files show v0.1.0-alpha.1 version consistently

SUCCESS CRITERIA:
- Thread-safe implementation with proper locking
- Atomic updates with backup/restore on failure
- 90%+ test coverage for all components
- Performance: version updates < 2 seconds
- Seamless integration with existing provisioning workflow
- Version consistency across all project files (v0.1.0-alpha.1)

DEPENDENCIES:
- Existing version_manager.py for SemVer validation
- Protocol 8 logging configuration
- Standard library only (pathlib, re, threading, tempfile, shutil)
- Cross-platform file handling with permission preservation
```

---

**Related Documents**:
- doc/design/Design_007_Automated_Version_Management.md
- doc/change/Change_007_Automated_Version_Management.md
- Protocol 1: Project Structure Standards
- Protocol 8: Logging and Debug Standards