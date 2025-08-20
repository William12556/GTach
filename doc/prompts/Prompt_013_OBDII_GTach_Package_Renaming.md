# Claude Code Prompt: OBDII to GTach Package Renaming

**Created**: 2025 08 20

## Prompt Header

**Prompt ID**: Prompt_013_OBDII_GTach_Package_Renaming
**Iteration**: 013
**Date**: 2025 08 20
**Task Type**: Refactor
**Complexity**: Standard
**Priority**: Medium

## Context

This prompt implements Change_013_OBDII_GTach_Package_Renaming to systematically rename the legacy OBDII package structure to GTach while preserving technical protocol references. The task requires careful distinction between application-specific naming (to be changed) and technical OBD-II automotive protocol references (to be preserved).

## Implementation Requirements

### Tool Selection
**Claude Code** is the appropriate tool for this systematic refactoring task involving direct file operations, import statement updates, and configuration modifications.

### Technical Constraints
- Must preserve technical OBD-II protocol references
- Must maintain application functionality
- Must update all import statements systematically
- Must follow Protocol standards for file modification

## Claude Code Prompt

```
ITERATION: 013
TASK: OBDII to GTach Package Renaming Implementation
CONTEXT: Project currently uses legacy OBDII package naming that should be updated to GTach for consistency. This is a systematic refactoring task requiring careful preservation of technical OBD-II protocol references while updating application-specific naming.

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

ISSUE DESCRIPTION: 
The project contains legacy OBDII package naming from when it was originally an OBDII application. The main package is located at `src/obdii/` and contains application-specific classes like `OBDIIApplication`. Import statements throughout the codebase reference this package structure. Configuration files also reference the old package name. This needs systematic updating to use GTach naming while preserving technical references to the actual OBD-II automotive protocol.

SOLUTION STRATEGY: 
Systematic renaming approach that:
1. Renames package directory from `src/obdii/` to `src/gtach/`
2. Updates all import statements to use new package name
3. Renames application-specific classes (OBDIIApplication → GTachApplication)
4. Updates configuration files with new package references
5. Preserves technical OBD-II protocol references that refer to the automotive standard
6. Validates changes through import testing

IMPLEMENTATION PLAN:
1. **Create backup** - Ensure current state is preserved
2. **Rename package directory** - Move `src/obdii/` to `src/gtach/`
3. **Update import statements** - Systematically update all `from obdii.` to `from gtach.`
4. **Rename application classes** - Update `OBDIIApplication` to `GTachApplication`
5. **Update configuration** - Modify `pyproject.toml` with new package name and entry points
6. **Preserve technical references** - Ensure actual OBD-II protocol references remain unchanged
7. **Remove build artifacts** - Delete `src/obdii_rpm_display.egg-info/` for regeneration
8. **Validate imports** - Test that all imports work correctly
9. **Test application startup** - Verify application functions normally

SUCCESS CRITERIA:
- [ ] Package directory successfully renamed to `src/gtach/`
- [ ] All import statements updated to use `gtach` package
- [ ] Application class renamed to `GTachApplication`
- [ ] Configuration files updated with new package name
- [ ] Application starts without import errors
- [ ] Core functionality operates correctly
- [ ] Technical OBD-II protocol references preserved
- [ ] Build artifacts cleaned and ready for regeneration

DEPENDENCIES: 
- Current project structure with `src/obdii/` package
- All Python files with import statements
- `pyproject.toml` configuration file
- Protocol compliance for file modification standards
```

## Expected Outcomes

### Before Implementation
- Package located at `src/obdii/`
- Class named `OBDIIApplication`
- Import statements using `from obdii.`
- Configuration referencing old package name

### After Implementation
- Package located at `src/gtach/`
- Class named `GTachApplication`
- Import statements using `from gtach.`
- Configuration updated with new package name
- Technical OBD-II protocol references preserved

## Validation Procedures

### Import Structure Validation
1. Test basic package import: `import gtach`
2. Test application class import: `from gtach.app import GTachApplication`
3. Test main entry point: `from gtach.main import main`

### Functionality Validation
1. Application startup verification
2. Core feature operation testing
3. Configuration loading validation

## Integration with Change Management

### Related Change Document
- **Change_013_OBDII_GTach_Package_Renaming.md**: Primary change documentation with comprehensive analysis and rollback procedures

### Post-Implementation Requirements
- Update change document with implementation results
- Document any issues encountered during execution
- Record lessons learned for future refactoring tasks

## References

### Protocol Compliance
- Protocol 2: Iteration-Based Development Workflow
- Protocol 4: Claude Desktop and Claude Code Integration
- Protocol 5: GitHub Desktop Workflow Integration

### Related Documentation
- Change_013_OBDII_GTach_Package_Renaming.md
- Protocol documentation in doc/protocol/

---

**Prompt Status**: Ready for Execution
**Execution Tool**: Claude Code
**Estimated Duration**: 2-3 hours
**Risk Assessment**: Medium - Systematic approach with validation steps
