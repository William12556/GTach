# Claude Code Prompt: Version State Manager Implementation

**Created**: 2025 08 14

**Prompt ID**: [009]
**Task Type**: Feature
**Complexity**: Complex
**Priority**: High

## Context

The GTach provisioning system requires enhanced version management capabilities that maintain persistent version state, provide stage-based development workflows, and integrate seamlessly with package creation. This implementation creates a comprehensive VersionStateManager that stores version information in a dedicated `.gtach-version` file with full metadata tracking.

## Issue Description

Current version management lacks persistent state storage and stage-based workflow guidance. Users must manually input versions without context about development stages or increment history. The system needs a centralized version state manager that:

1. Maintains version state in `.gtach-version` file
2. Tracks development stages (alpha, beta, rc, release, stable)
3. Provides intelligent increment suggestions
4. Records increment history and metadata
5. Integrates with existing package creation workflow

## Technical Analysis

### Root Cause
No centralized version state management system exists. Current implementation relies on scanning project files for versions, leading to:
- Inconsistent version detection
- No development stage tracking
- Manual version input without guidance
- No increment history preservation

### Impact Assessment
- **Functionality**: Adds comprehensive version state management
- **Performance**: Minimal impact - JSON file I/O operations
- **Compatibility**: Maintains backward compatibility with existing workflows
- **Dependencies**: Integrates with existing VersionManager and ProjectVersionManager

### Platform Constraints
- **Development**: Mac Mini M4 (macOS) 
- **Deployment**: Raspberry Pi (Linux)
- **Requirements**: Thread-safe file operations, cross-platform path handling
- **Python Version**: 3.9+
- **Memory/CPU**: Minimal additional resource usage

## Solution Strategy

Implement a VersionStateManager class that provides persistent version state management through a JSON-based state file, stage-based increment workflows, and seamless integration with the existing provisioning system.

## Implementation Plan

### Primary Changes

1. **File**: `src/provisioning/version_state_manager.py`
   **Purpose**: Create new VersionStateManager class
   **Implementation**: Complete version state management system
   **Key Features**:
   - JSON-based `.gtach-version` file management
   - Development stage enumeration and transitions
   - Increment history tracking with timestamps
   - Thread-safe file operations
   - Integration with existing VersionManager

2. **File**: `src/provisioning/__init__.py`
   **Purpose**: Export new VersionStateManager class
   **Change**: Add import for VersionStateManager

### Supporting Changes

3. **File**: `src/provisioning/create_package.py`
   **Purpose**: Integration preparation (will be handled in subsequent prompt)
   **Note**: This prompt focuses on VersionStateManager implementation only

## Technical Requirements

### Core Requirements
- **Thread Safety**: All file operations must be thread-safe with proper locking
- **Error Handling**: Comprehensive error handling with Protocol 8 compliant logging
- **Logging**: Debug logging with session timestamps and detailed operation tracking
- **Performance**: Efficient JSON serialization/deserialization with minimal overhead

### Platform-Specific Requirements
- **Mac Mini (Development)**: Full functionality with development-friendly logging
- **Raspberry Pi (Deployment)**: Optimized file I/O with resource-conscious operations
- **Cross-Platform**: Consistent file path handling and permission management

### Dependencies
- **Required**: json, threading, pathlib, datetime, enum
- **Project**: version_manager.py (existing VersionManager integration)
- **Logging**: Protocol 8 compliant session-based logging

## Success Criteria

- [ ] VersionStateManager class successfully created with all required methods
- [ ] `.gtach-version` file creation and persistence works correctly
- [ ] Development stage transitions function properly
- [ ] Increment history tracking preserves metadata accurately
- [ ] Thread-safe operations prevent data corruption
- [ ] Cross-platform compatibility verified
- [ ] Integration with existing VersionManager seamless
- [ ] Debug logging captures all operations with proper session timestamps

## Risk Assessment

### Risk Level: Medium
- **Primary Risk**: File corruption during concurrent access
- **Mitigation**: Atomic file operations with proper locking mechanisms
- **Rollback**: File-based state allows easy restoration from backups

## Expected Outcome

### Before
- No persistent version state management
- Manual version input without development context
- No increment history tracking

### After
- Comprehensive version state stored in `.gtach-version` file
- Stage-based development workflow with intelligent suggestions
- Complete increment history with metadata tracking
- Thread-safe operations across all platforms

### Verification Method
- Version state file creation and modification testing
- Concurrent access testing for thread safety
- Cross-platform file operation validation
- Integration testing with existing VersionManager

## Claude Code Prompt

```
ITERATION: 009
TASK: Implement VersionStateManager for Persistent Version State Management
CONTEXT: Creating comprehensive version management system for GTach provisioning with persistent state storage, stage-based workflows, and increment history tracking.

PROTOCOL REVIEW REQUIRED:
- Review Protocol 8 (Logging and Debug Standards) for session-based logging requirements
- Review Protocol 6 (Cross-Platform Development Standards) for thread-safe operations
- Apply Protocol 1 (Project Structure Standards) for proper file organization

ISSUE DESCRIPTION: 
Implement a VersionStateManager class that maintains persistent version state in a dedicated `.gtach-version` file. The system must support development stage tracking (alpha, beta, rc, release, stable), increment history preservation, and seamless integration with existing version management components.

SOLUTION STRATEGY: 
Create a comprehensive VersionStateManager class with JSON-based state persistence, development stage enumeration, thread-safe file operations, and intelligent increment suggestion algorithms.

IMPLEMENTATION PLAN:
1. Create VersionStateManager class in src/provisioning/version_state_manager.py
2. Implement DevelopmentStage enum with all required stages
3. Create VersionState dataclass for state representation
4. Implement thread-safe JSON file operations with atomic writes
5. Add stage-based increment logic with intelligent suggestions
6. Create increment history tracking with comprehensive metadata
7. Integrate with existing VersionManager for validation
8. Add comprehensive error handling and Protocol 8 logging
9. Update src/provisioning/__init__.py to export new class

SUCCESS CRITERIA:
- VersionStateManager class created with full functionality
- .gtach-version file management works correctly
- Development stage transitions operate properly  
- Increment history tracks all metadata accurately
- Thread-safe operations prevent data corruption
- Cross-platform compatibility verified
- Integration with VersionManager seamless
- Debug logging captures all operations with session timestamps

DEPENDENCIES: 
- Existing version_manager.py VersionManager class
- Protocol 8 logging standards compliance
- Protocol 6 cross-platform development standards
- JSON serialization for state persistence
- Threading for concurrent access protection
```

## Additional Notes

This implementation focuses solely on creating the VersionStateManager infrastructure. Integration with create_package.py and enhanced user workflows will be handled in subsequent prompts to maintain manageable implementation scope and proper testing isolation.

---

**Related Documents**:
- [[Change Plan: Enhanced Version State Management System]]
- [[Protocol 8: Logging and Debug Standards]]
- [[Protocol 6: Cross-Platform Development Standards]]

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
