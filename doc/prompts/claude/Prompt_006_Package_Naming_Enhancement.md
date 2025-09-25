# Claude Code Prompt Documentation

**Created**: 2025 08 13

## Prompt Summary

**Prompt ID**: 006
**Task Type**: Enhancement
**Complexity**: Standard
**Priority**: Medium

## Context

The current provisioning system generates verbose package names like `gtach-pi-deployment-1.0.0-20250813_094209.tar.gz` using automatic timestamp generation without user control. This creates unclear naming conventions and lacks version management flexibility. The enhancement aims to implement simplified semantic versioning with interactive version assignment.

## Issue Description

### Current Behavior
- Complex package naming: `gtach-pi-deployment-1.0.0-20250813_094209.tar.gz`
- Automatic timestamp generation without user input
- Platform-specific verbose naming conventions
- Fixed version numbers without interactive control

### Required Enhancement
- Simplified naming: `gtach-v0.1.0-alpha.1.tar.gz`
- Interactive version number assignment during package creation
- Semantic versioning support with pre-release identifiers
- Consistent naming across all platforms

## Solution Strategy

Implement interactive version input workflow with simplified semantic versioning format. Replace timestamp-based naming with user-controlled version assignment while maintaining package format compatibility and cross-platform consistency.

## Implementation Plan

### Primary Changes

1. **File**: `src/provisioning/create_package.py`
   - **Function**: `main()` and `create_deployment_package()`
   - **Change**: Add interactive version input prompt with validation
   - **Lines**: Around 400-450 in main execution flow

2. **File**: `src/provisioning/package_creator.py`
   - **Method**: `_create_archive()` and package naming logic
   - **Change**: Replace timestamp-based naming with semantic version format
   - **Lines**: Around 750-780 in archive creation workflow

3. **File**: `src/provisioning/version_manager.py`
   - **Methods**: Add pre-release version validation and formatting
   - **Change**: Enhance version parsing to support alpha/beta/rc identifiers
   - **Lines**: Extend existing version validation methods

### Supporting Changes
- Add version input validation functions with semantic versioning support
- Implement user-friendly prompts with examples and format guidance
- Update package configuration to support simplified naming convention
- Add version format validation and error messaging

## Technical Requirements

### Core Requirements
- **Thread Safety**: Maintain existing thread safety in package creation components
- **Error Handling**: Implement comprehensive validation for version input with clear error messages and user guidance per Protocol 8
- **Logging**: Add detailed debug logging for version assignment and package naming decisions with session timestamps
- **Performance**: Minimal performance impact from interactive prompts and validation

### Platform-Specific Requirements
- **Mac Mini (Development)**: Interactive prompts work correctly in development environment terminal
- **Raspberry Pi (Deployment)**: Package naming consistency maintained across deployment scenarios
- **Cross-Platform**: Uniform naming convention regardless of target platform (raspberry-pi, macos, linux)

### Dependencies
- **Required Packages**: Maintain existing dependencies (pathlib, datetime, re for version validation)
- **Version Constraints**: Python ≥3.9 compatibility maintained
- **Platform-Specific**: No additional platform-specific dependencies required

## Testing Strategy

### Unit Testing
- [ ] Test interactive version input validation with valid and invalid formats
- [ ] Test semantic version parsing including pre-release identifiers (alpha, beta, rc)
- [ ] Test package naming convention generation with various version formats
- [ ] Test version format validation edge cases and error handling

### Integration Testing
- [ ] Test complete package creation workflow with new interactive version input
- [ ] Test cross-platform package naming consistency across all target platforms
- [ ] Test package installation compatibility with new naming convention
- [ ] Test user experience flow for version input with validation feedback

### Platform Verification
- [ ] Mac Mini: Interactive prompts functionality and user experience validation
- [ ] Raspberry Pi: Package naming consistency and deployment compatibility verification
- [ ] Cross-platform: Version format standardization across all platforms

## Success Criteria

- [ ] Interactive version input prompts provide clear user experience with examples
- [ ] Package naming follows simplified format: `gtach-v{version}.tar.gz`
- [ ] Semantic version validation supports standard and pre-release formats
- [ ] Cross-platform naming consistency maintained regardless of target platform
- [ ] User can specify versions like `0.1.0`, `1.2.3-alpha.1`, `2.0.0-beta.2`, `1.0.0-rc.1`
- [ ] Invalid version formats provide clear error messages and examples
- [ ] No regression in existing package creation functionality

## Risk Assessment

### Risk Level: Low
- **Primary Risk**: User workflow change might require adjustment period for familiar usage patterns
- **Mitigation**: Provide clear prompts, examples, and validation feedback during version input
- **Rollback**: Simple rollback available by reverting to timestamp-based naming logic

## Expected Outcome

### Before
Package creation generates verbose names like `gtach-pi-deployment-1.0.0-20250813_094209.tar.gz` with automatic timestamps and no user control over versioning.

### After
Package creation prompts user for version input and generates clean names like `gtach-v0.1.0-alpha.1.tar.gz` with semantic versioning support and interactive version control.

### Verification Method
Execute package creation workflow and verify interactive version prompts, semantic version validation, and simplified package naming format generation.

## Claude Code Prompt

```
ITERATION: 006
TASK: Implement Interactive Version Assignment and Simplified Package Naming
CONTEXT: Current provisioning system generates verbose package names like 'gtach-pi-deployment-1.0.0-20250813_094209.tar.gz' with automatic timestamps. Need to implement simplified semantic versioning with interactive version input for cleaner package names like 'gtach-v0.1.0-alpha.1.tar.gz'.

PROTOCOL REVIEW REQUIRED:
- Review Protocol 2 (Iteration Workflow) for version management integration
- Review Protocol 8 (Logging Standards) for proper error handling and user input validation
- Apply thread safety and comprehensive error handling throughout implementation

ISSUE DESCRIPTION:
Current package naming system creates verbose, unclear package names with automatic timestamp generation and no user control. Package names like 'gtach-pi-deployment-1.0.0-20250813_094209.tar.gz' are difficult to interpret and lack semantic versioning benefits. Need to implement:
1. Interactive version input prompts during package creation
2. Simplified naming convention: gtach-v{version}.tar.gz
3. Semantic versioning support with pre-release identifiers (alpha, beta, rc)
4. Cross-platform naming consistency
5. Version format validation with clear error messaging

SOLUTION STRATEGY:
Replace timestamp-based automatic naming with user-controlled semantic versioning:
- Add interactive version input with validation in create_package.py main workflow
- Update package_creator.py archive naming logic to use simplified format
- Enhance version_manager.py to support pre-release version validation
- Implement clear user prompts with examples and format guidance
- Maintain package format compatibility while improving naming clarity

IMPLEMENTATION PLAN:
1. Modify create_package.py main() function to add interactive version input prompt with validation
2. Update create_deployment_package() to accept and use user-specified version
3. Enhance PackageCreator._create_archive() to generate simplified package names using format: gtach-v{version}.tar.gz
4. Add version input validation function supporting semantic versioning (major.minor.patch) and pre-release identifiers
5. Implement user-friendly prompts with examples: "Enter version (e.g., 0.1.0, 1.2.3-alpha.1, 2.0.0-beta.2): "
6. Add version format validation with clear error messages and retry logic
7. Update PackageConfig to support user-specified versions instead of automatic generation
8. Ensure cross-platform naming consistency across all target platforms
9. Add comprehensive logging for version assignment decisions per Protocol 8
10. Test interactive workflow with various version formats and validation scenarios

SUCCESS CRITERIA:
- Interactive version input prompts provide clear user experience with examples
- Package naming follows simplified format: gtach-v{version}.tar.gz
- Semantic version validation supports formats like 0.1.0, 1.2.3-alpha.1, 2.0.0-beta.2, 1.0.0-rc.1
- Invalid version formats provide helpful error messages with examples
- Cross-platform naming consistency maintained
- No regression in package creation functionality
- User can easily specify custom versions during package creation workflow
- Clear validation feedback for incorrect version format input

DEPENDENCIES:
- src/provisioning/create_package.py (main execution flow and user interaction)
- src/provisioning/package_creator.py (package naming and archive creation logic)
- src/provisioning/version_manager.py (version validation and parsing enhancement)
- Protocol 2 iteration workflow integration for version management
- Protocol 8 logging and error handling standards for user input validation
```

## Additional Notes

This enhancement focuses on improving user experience and package identification clarity while maintaining backward compatibility with existing deployment processes. The interactive version assignment provides flexibility for development iterations while simplified naming improves package management and identification.

Key considerations:
- **User Experience**: Clear prompts and validation feedback for version input
- **Semantic Versioning**: Support for standard semver with pre-release identifiers
- **Cross-Platform Consistency**: Uniform naming regardless of target platform
- **Backward Compatibility**: Package format remains compatible with existing deployment

---

**Related Documents**:
- [[Change_006_Provisioning_Package_Naming_Enhancement.md]]
- [[Design_001_Application_Provisioning_System.md]]
- [[Protocol_002_Iteration_Based_Development_Workflow.md]]

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
