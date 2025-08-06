# Claude Code Prompt Template

**Created**: YYYY MM DD

**Prompt ID**: [####]
**Task Type**: [Bug Fix/Feature/Refactor/Performance/Security]
**Complexity**: [Simple/Standard/Complex]
**Priority**: [Critical/High/Medium/Low]

## Context

[Project state, recent changes, and relevant background information that provides continuity between prompts]

## Issue Description

[Clear, concise description of the problem or requirement]

### Error Details (if applicable)
- **Error Type**: [Error class/category]
- **Location**: `[file.py]` line [number]
- **Error Message**:
```
[Exact error message]
```

## Technical Analysis

### Root Cause
[Technical explanation of why the issue occurs or what needs to be implemented]

### Impact Assessment
- **Functionality**: [What is affected or will be added]
- **Performance**: [Performance implications]
- **Compatibility**: [Cross-platform considerations]
- **Dependencies**: [Affected modules/systems]

### Platform Constraints
- **Development**: Mac Mini M4 (macOS)
- **Deployment**: Raspberry Pi (Linux)
- **Hardware**: GPIO interfaces per doc/hardware/ specifications
- **Python Version**: [3.x]
- **Memory/CPU**: [Specific limitations]

## Solution Strategy

[High-level approach to solving the problem - the overall plan]

## Implementation Plan

### Primary Changes
1. **File**: `[src/domain/category/component.py]`
   - **Function/Class**: `[name()]`
   - **Change**: [Specific modification]
   - **Lines**: [Approximate line numbers]

2. **File**: `[src/utils/helper_module.py]`
   - **Function/Class**: `[name()]`
   - **Change**: [Specific modification]
   - **Lines**: [Approximate line numbers]

### Supporting Changes
[List any additional files or configurations that need modification]

## Technical Requirements

### Core Requirements
- **Thread Safety**: [Specific thread safety needs]
- **Error Handling**: [Error handling strategy with crash protection]
- **Logging**: [Debug logging requirements with traceback]
- **Performance**: [Performance constraints or targets]

### Platform-Specific Requirements
- **Mac Mini (Development)**: [Development-specific requirements]
- **Raspberry Pi (Deployment)**: [Pi-specific requirements]
- **Cross-Platform**: [Compatibility requirements]

### Dependencies
- **Required Packages**: [e.g., pyserial==3.5, obd==0.7.1]
- **Version Constraints**: [e.g., >=Python 3.9]
- **Platform-Specific**: [e.g., RPi.GPIO for Pi only]

## Testing Strategy

### Unit Testing
- [ ] [Test specific functionality]
- [ ] [Test error conditions]
- [ ] [Test edge cases]

### Integration Testing
- [ ] [Test with dependent systems]
- [ ] [Test hardware interfaces (mocked on Mac)]
- [ ] [Test cross-platform compatibility]

### Platform Verification
- [ ] Mac Mini: Development environment testing with mocks
- [ ] Raspberry Pi: Hardware interface testing with real GPIO
- [ ] Cross-platform: Configuration management validation

## Success Criteria

- [ ] [Specific measurable outcome 1]
- [ ] [Specific measurable outcome 2]
- [ ] [No regression in existing functionality]
- [ ] [Thread-safe implementation verified]
- [ ] [Debug logging captures expected information]

## Risk Assessment

### Risk Level: [Low/Medium/High]
- **Primary Risk**: [Main risk description]
- **Mitigation**: [How to minimize risk]
- **Rollback**: [Quick rollback procedure if needed]

## Expected Outcome

### Before
[Description of current state or problem]

### After
[Description of expected working state]

### Verification Method
[How to confirm the implementation works correctly]

## Claude Code Prompt

```
[Insert complete Claude Code prompt here - copy-paste ready format]
ITERATION: [000]
TASK: [Brief Description]
CONTEXT: [Development Context and Background]
PROTOCOL REVIEW REQUIRED:
- Review relevant project protocols from doc/protocol/
- Apply protocol requirements throughout implementation
ISSUE DESCRIPTION: [Detailed Problem Statement]
SOLUTION STRATEGY: [High-Level Approach]
IMPLEMENTATION PLAN: [Step-by-Step Implementation Details]
SUCCESS CRITERIA: [Measurable Completion Requirements]
DEPENDENCIES: [Related Files, Protocols, or Previous Implementations]
```

## Additional Notes

[Any special considerations, related issues, or context that doesn't fit elsewhere]

---

**Related Documents**:
- [[Link to related issue]]
- [[Link to design document]]
- [[Link to change plan]]
