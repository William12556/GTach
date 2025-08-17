# Claude Code Prompt: Git Release Automation Implementation

**Created**: 2025 08 17

## Prompt Summary

**Prompt ID**: Prompt_012_01_Git_Release_Automation
**Date**: 2025 08 17
**Author**: Claude Desktop
**Version**: 1.0
**Status**: Ready for Execution

## Overview

### Purpose
Create automated git release system that integrates with existing package creation workflow using git CLI authentication and GitHub API for enhanced release management.

### Scope
Implementation of release automation scripts with Makefile integration that provides hybrid immediate/deferred release creation capabilities with automatic asset upload to GitHub releases.

### Goals and Objectives
- Streamline release creation workflow
- Maintain user control through confirmation mechanisms
- Leverage existing git CLI authentication
- Integrate seamlessly with current package creation process

## Technical Requirements

### Functional Requirements
- **FR-1**: Automatic version detection from pyproject.toml
- **FR-2**: Package asset discovery and validation from packages/ directory
- **FR-3**: GitHub release creation with asset upload capability
- **FR-4**: Hybrid workflow integration (immediate + deferred options)
- **FR-5**: Git CLI authentication utilization
- **FR-6**: Main branch enforcement for release creation

### Non-Functional Requirements
- **Performance**: Minimal impact on existing workflows
- **Reliability**: Comprehensive error handling and rollback capabilities
- **Maintainability**: Clear separation of concerns between modules
- **Cross-Platform**: Compatible with Mac development and Pi deployment environments

### Constraints
- **Technical**: Must use existing git CLI authentication
- **Platform**: Cross-platform compatibility required
- **Resource**: No additional authentication token management

## Implementation Specification

### Component Architecture
```
scripts/
├── create_release.py          # Main release automation script
└── release_utils.py          # Helper functions and utilities

Makefile                      # Enhanced with release workflow integration
```

### Interface Design
- **Public Interfaces**: Command-line interface with --auto and --interactive modes
- **Internal Interfaces**: Git CLI command execution and GitHub API integration
- **Makefile Integration**: Release targets for workflow automation

### Data Flow
Version Detection → Asset Validation → Release Notes Extraction → GitHub Release Creation → Asset Upload

## Claude Code Prompt

```
ITERATION: 012
TASK: Implement Git Release Automation System
CONTEXT: Create automated release creation system that integrates with existing package workflow using git CLI authentication. System must provide hybrid immediate/deferred release options with GitHub asset upload capabilities.

PROTOCOL ACKNOWLEDGMENT REQUIRED:
- Read and understand ALL relevant project protocols from doc/protocol/
- Read and understand ALL relevant templates from doc/templates/
- Confirm protocol and template comprehension before beginning implementation
- Apply protocol requirements and template standards throughout development process
- Document any protocol or template conflicts or clarifications needed

FILE PLACEMENT REQUIREMENT:
- ALL SOURCE CODE FILES MUST BE CREATED IN src/ DIRECTORY
- NO PYTHON FILES (.py) IN PROJECT ROOT DIRECTORY
- ALL TEST FILES MUST BE IN src/tests/ DIRECTORY

FILE MODIFICATION REQUIREMENT:
- MODIFY EXISTING FILES DIRECTLY - DO NOT CREATE NEW VERSIONS
- USE EXISTING FILENAME - NO _enhanced, _v2, _updated SUFFIXES
- VERSION CONTROL HANDLED BY GIT - NO MANUAL FILE VERSIONING
- PRESERVE ORIGINAL FILE PATHS AND NAMES

ISSUE DESCRIPTION: Manual release creation creates workflow inefficiency and potential inconsistency. Need automated system that leverages existing git CLI authentication and integrates with package creation process.

SOLUTION STRATEGY: Create Python-based release automation system with git CLI integration, automatic asset detection, and hybrid workflow support through Makefile enhancement.

IMPLEMENTATION PLAN:
1. Create scripts/create_release.py with version detection, asset discovery, and GitHub release creation
2. Create scripts/release_utils.py with helper functions for git operations and file validation
3. Enhance Makefile with release targets for hybrid workflow integration
4. Implement comprehensive error handling and rollback capabilities
5. Add branch validation to ensure releases only from main branch
6. Integrate release notes extraction from root RELEASE_NOTES.md

DETAILED REQUIREMENTS:
- Version detection from pyproject.toml using tomli or configparser
- Asset discovery in packages/ directory with validation
- Git CLI authentication utilization (no token management required)
- GitHub release creation via git CLI and API calls
- Asset upload functionality for distribution files
- Branch validation ensuring main branch only
- Release notes extraction from RELEASE_NOTES.md
- Comprehensive error handling with user feedback
- Thread-safe implementation where applicable
- Robust logging with debug capabilities
- Cross-platform compatibility (Mac/Pi)

MAKEFILE ENHANCEMENTS:
- release-prompt target: Post-package user confirmation
- release-auto target: Immediate release creation
- release-manual target: Deferred standalone execution
- Integration with existing package creation workflow

ERROR HANDLING REQUIREMENTS:
- Git authentication verification
- GitHub API error responses
- Asset file validation failures
- Network connectivity issues
- Branch validation failures
- Rollback procedures for partial operations

SUCCESS CRITERIA:
- scripts/create_release.py created with full functionality
- scripts/release_utils.py created with helper functions
- Makefile enhanced with release workflow integration
- Version detection from pyproject.toml functional
- Asset discovery and upload working
- Git CLI authentication integration successful
- Branch validation enforced
- Comprehensive error handling implemented
- Thread safety ensured where applicable
- Debug logging with traceback included

DEPENDENCIES:
- Existing git CLI authentication setup
- pyproject.toml version configuration
- packages/ directory structure
- Root RELEASE_NOTES.md file
- GitHub repository access
- Protocol 13 Release Management standards
- Protocol 5 GitHub Desktop Workflow integration
```

## Implementation Guidelines

### Code Quality Standards
- Thread safety mandatory for concurrent operations
- Comprehensive logging with debug capabilities and traceback
- Professional-level commenting and documentation
- Small, focused functions with clear responsibilities

### Testing Requirements
- Unit tests for version detection and asset discovery
- Integration tests for git CLI operations
- Cross-platform compatibility validation
- Error condition testing and recovery procedures

### Security Considerations
- Git CLI authentication security maintained
- No token storage or management required
- Secure asset upload procedures
- Input validation for all user-provided data

## Expected Outcome

### Before
Manual release creation requiring separate git operations and GitHub interface interaction

### After
Automated release creation integrated with package workflow, providing immediate or deferred options with comprehensive asset upload and error handling

### Verification Method
- Successful package creation triggers release option
- Version correctly detected from pyproject.toml
- Assets uploaded to GitHub release
- Release notes properly formatted
- Error conditions handled gracefully

## Additional Notes

This implementation maintains consistency with Protocol 13 release management standards while providing workflow efficiency improvements. The hybrid approach preserves user control while enabling automation where beneficial.

---

**Related Documents**:
- [[Change_001_Git_Release_Automation.md]]
- [[Protocol 13 Release Management Documentation Standards]]
- [[Protocol 5 GitHub Desktop Workflow Integration]]