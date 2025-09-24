# Codestral Prompt Template

**Created**: YYYY MM DD

**Prompt ID**: Codestral_[iteration]_[task_sequence]_[description]
**Task Type**: [Code Generation/Analysis/Optimization/Debug/Refactor]
**Complexity**: [Simple/Standard/Complex]
**Priority**: [Critical/High/Medium/Low]
**MCP Interface**: LM Studio Codestral 22b

## Context

[Algorithmic background, project state, and relevant technical information that provides context for specialized code generation]

## Algorithm Specification

[Clear, precise description of the algorithmic requirements or code generation needs]

### Mathematical Requirements (if applicable)
- **Algorithm Type**: [Computational/Optimization/Data Processing/etc.]
- **Complexity Constraints**: [Time/Space complexity requirements]
- **Mathematical Operations**: [Specific mathematical computations required]
- **Data Structures**: [Required data structures and operations]

### Performance Requirements
- **Execution Time**: [Performance targets and constraints]
- **Memory Usage**: [Memory consumption limitations]
- **Throughput**: [Data processing throughput requirements]
- **Optimization Targets**: [Specific optimization objectives]

## Technical Analysis

### Implementation Requirements
[Technical explanation of what needs to be implemented and why]

### Performance Considerations
- **Development Platform**: Mac Mini M4 (macOS) - Development testing
- **Deployment Platform**: Raspberry Pi (Linux) - Production environment
- **Hardware Constraints**: GPIO interfaces per doc/hardware/ specifications
- **Python Version**: [3.x compatibility requirements]
- **Memory/CPU**: [Platform-specific limitations and optimizations]

### Integration Context
- **Project Integration**: [How generated code integrates with existing architecture]
- **Module Dependencies**: [Required imports and module interactions]
- **Interface Requirements**: [Public interface specifications]
- **Thread Safety**: [Concurrent execution requirements and constraints]

## Code Generation Strategy

[High-level approach to code generation - the algorithmic and implementation strategy]

### Algorithm Design
1. **Primary Algorithm**: [Main algorithmic approach]
2. **Optimization Strategy**: [Performance optimization techniques]
3. **Error Handling**: [Robust error handling approach]
4. **Logging Integration**: [Debug logging requirements with traceback]

### Implementation Approach
1. **Core Function**: `[primary_function_name()]`
   - **Purpose**: [Primary function responsibility]
   - **Parameters**: [Input parameter specifications]
   - **Returns**: [Return value specifications]
   - **Complexity**: [Time/space complexity analysis]

2. **Helper Functions**: `[helper_function_name()]`
   - **Purpose**: [Helper function responsibility]
   - **Integration**: [How helpers support core functionality]

### Supporting Infrastructure
[Additional code structures needed for complete implementation]

## Technical Requirements

### Core Standards
- **Thread Safety**: [Specific thread safety implementation requirements]
- **Error Handling**: [Comprehensive error handling with crash protection]
- **Logging**: [Debug logging requirements with full traceback information]
- **Documentation**: [PyDoc/docstring requirements for professional documentation]
- **Performance**: [Specific performance targets and benchmarking requirements]

### Platform-Specific Requirements
- **Mac Mini (Development)**: [Development environment specific requirements and mocking]
- **Raspberry Pi (Deployment)**: [Production environment requirements and optimizations]
- **Cross-Platform**: [Compatibility requirements and conditional implementations]

### Code Quality Standards
- **Function Design**: Small, compact functions with single responsibility
- **Helper Utilization**: Use helper functions and classes for modularity
- **Structure Validation**: Focus on correctness and structural integrity
- **Professional Documentation**: Advanced level commenting for professional programmers

## MCP Execution Configuration

### MCP Parameters
```json
{
  "temperature": [0.1-0.3],
  "max_tokens": [1024-4096],
  "system_prompt": "Specialized system prompt for code generation task"
}
```

### System Prompt Specification
[Detailed system prompt optimized for the specific code generation task]

## Testing Strategy

### Algorithm Validation
- [ ] [Mathematical correctness verification]
- [ ] [Algorithm complexity validation]
- [ ] [Edge case handling verification]
- [ ] [Performance benchmarking]

### Integration Testing
- [ ] [Module integration verification]
- [ ] [Thread safety validation under concurrent access]
- [ ] [Cross-platform compatibility testing]
- [ ] [Error handling robustness testing]

### Platform Verification
- [ ] Mac Mini: Algorithm development and optimization testing
- [ ] Raspberry Pi: Production performance and resource utilization validation
- [ ] Cross-platform: Behavior consistency and optimization effectiveness

## Success Criteria

- [ ] [Algorithm correctness verified through comprehensive testing]
- [ ] [Performance targets met on both development and deployment platforms]
- [ ] [Thread-safe implementation validated under concurrent execution]
- [ ] [Professional documentation standards achieved]
- [ ] [Integration compatibility with existing project architecture confirmed]

## Risk Assessment

### Risk Level: [Low/Medium/High]
- **Algorithmic Risk**: [Complexity and correctness risks]
- **Performance Risk**: [Performance target achievement risks]
- **Integration Risk**: [Project integration complexity risks]
- **Mitigation Strategy**: [Specific risk mitigation approaches]
- **Rollback Plan**: [Algorithm rollback or alternative implementation approaches]

## Expected Outcome

### Before
[Current algorithmic state or performance characteristics]

### After
[Expected algorithmic improvement or new capability]

### Performance Metrics
[Quantifiable performance improvements or capabilities achieved]

## Codestral MCP Prompt

```
CODESTRAL ANALYSIS REQUEST
ITERATION: [000]
TASK TYPE: [Code Generation/Analysis/Optimization/Debug/Refactor]
CONTEXT: [Development Context and Algorithmic Background]

PROJECT STANDARDS COMPLIANCE:
- Thread safety mandatory for all concurrent operations
- Comprehensive logging with traceback information
- Cross-platform compatibility (Mac development/Pi deployment)
- Professional code documentation with PyDoc/docstrings
- Protocol adherence per project standards

ALGORITHM SPECIFICATION: [Detailed Algorithm Requirements]
PERFORMANCE REQUIREMENTS: [Performance Constraints and Targets]
INTEGRATION CONTEXT: [How code integrates with existing project structure]
SUCCESS CRITERIA: [Measurable Completion Requirements]
DEPENDENCIES: [Required Libraries, Modules, or Previous Implementations]

GENERATE: [Specific code generation request with technical specifications]
```

## MCP Execution Notes

[Special considerations for MCP execution, parameter tuning, or interface-specific requirements]

## Integration Planning

### Claude Code Integration
[How Codestral output will be integrated through Claude Code implementation]

### Project Architecture Impact
[Impact on existing project structure and integration procedures]

---

**Related Documents**:
- [[Link to related algorithm specification]]
- [[Link to performance requirements]]
- [[Link to integration design document]]

---

**MCP Interface**: LM Studio Codestral 22b  
**Execution Environment**: /Users/williamwatson/Documents/GitHub/GTach  
**Integration Protocol**: Claude Desktop → Codestral → Claude Code

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
