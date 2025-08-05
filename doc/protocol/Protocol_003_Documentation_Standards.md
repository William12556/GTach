# Protocol 3: Documentation Standards

**Created**: 2025 01 06  
**Version**: 1.0  
**Status**: Active  

## Purpose

Establish comprehensive documentation standards that ensure consistency, maintainability, and cross-platform compatibility while integrating seamlessly with Obsidian vault management and supporting iterative development workflows.

## Path Referencing Standards

### Universal Path Format
All documentation must use forward slash (/) path separators regardless of the authoring platform, ensuring compatibility across macOS, Linux, and Windows environments. This standard applies to all relative and absolute path references within documentation files.

### Relative Path Requirements
Documentation must reference all project files using relative paths from the project root directory. Absolute paths are prohibited except when referencing external resources or system-specific configurations that cannot be expressed relatively.

**Standard Format Examples**:
- Source code reference: `src/gpio_controller.py`
- Documentation reference: `doc/protocol/Protocol_001_Project_Structure_Standards.md`
- Test file reference: `src/tests/test_gpio_controller.py`
- Template reference: `doc/templates/Template_Design_Document.md`
- Hardware reference: `doc/hardware/gpio_pin_specifications.md`
- AI knowledge reference: `ai/project_knowledge/cross_platform_testing_paradigm.md`
- AI synopsis reference: `ai/synopses/Synopsis_001_GPIO_Implementation.md`
- AI instructions reference: `ai/project_instructions/Claude_Code_Prompt_Guidelines.md`

### Cross-Reference Management
All cross-references between documents must be maintained manually to ensure accuracy and prevent broken links. Automated link generation is prohibited to maintain precise control over document relationships and ensure compatibility with version control systems.

## Code Block Documentation Format

### Source Code Referencing Standard
When referencing source code within documentation, the following format must be used consistently:

**Format**: `File: [relative_path] | Date: YYYYMMDD | Code: [code_snippet_or_function_name]`

**Examples**:
```
File: src/gpio_controller.py | Date: 20250106 | Code: initialize_gpio_pins()
File: src/config/platform_config.py | Date: 20250106 | Code: detect_platform()
File: src/tests/test_gpio_controller.py | Date: 20250106 | Code: class TestGPIOController
```

### Code Block Syntax Requirements
All code blocks must specify the appropriate language for syntax highlighting. Python code blocks must use the `python` language identifier, configuration files must use appropriate identifiers (`json`, `yaml`, `toml`), and shell commands must use `bash` or `shell` identifiers.

**Implementation Example**:
```python
def initialize_gpio_pins(pin_configuration):
    """Initialize GPIO pins based on platform-specific configuration."""
    platform = detect_platform()
    return configure_pins_for_platform(platform, pin_configuration)
```

### Line Number Exclusion Policy
Line numbers must not be included in code references due to the maintenance burden they create. Code references should use function names, class names, or distinctive code patterns that remain stable across minor modifications.

## Document Structure Standards

### Mandatory Header Information
Every documentation file must include a standardized header containing:
- **Created**: Timestamp in YYYY MM DD format
- **Version**: Semantic versioning for protocol documents, iteration numbering for implementation documents
- **Status**: Active, Draft, Deprecated, or Archived
- **Dependencies**: References to related protocols or documents where applicable

### Section Organization Requirements
Documentation must follow a logical hierarchical structure using markdown heading levels appropriately. Primary sections use level 2 headings (##), subsections use level 3 headings (###), and detailed specifications use level 4 headings (####). Level 1 headings are reserved for document titles.

### Content Formatting Standards
Technical documentation must maintain professional formatting with consistent use of emphasis, code formatting, and structural elements. Bold text is reserved for critical concepts and requirements, italic text for definitions and emphasis, and code formatting for technical terms and file references.

## Markdown Syntax Requirements

### Standard Markdown Compliance
All documentation must adhere to CommonMark specifications to ensure consistent rendering across different markdown processors. This includes proper escaping of special characters, consistent list formatting, and standard table syntax where applicable.

### Code Block Enhancement
Code blocks must include language specifications for syntax highlighting and should contain complete, executable examples where possible. Incomplete code snippets must be clearly marked as partial implementations with explanatory context.

### Table Standards
Tables must use standard markdown table syntax with proper column alignment indicators. Complex data presentations should be supplemented with explanatory text to ensure accessibility and comprehension.

## Integration with Development Tools

### Obsidian Vault Integration
Documentation directories must be linked to Obsidian vault through symbolic links, enabling seamless editing and cross-referencing while maintaining the project directory structure. The Obsidian vault serves as the primary editing environment for all documentation.

### Version Control Compatibility
All documentation formats must be compatible with git version control, ensuring meaningful diffs and merge conflict resolution. Binary formats are prohibited except for essential diagrams and images that cannot be represented in text.

### Claude Code Integration
Documentation must support the Claude Code workflow by providing clear context and references that can be included in prompts. Code references should be sufficiently detailed to enable accurate prompt generation without requiring additional file inspection.

## Quality Assurance Standards

### Consistency Validation
Documentation consistency must be validated before each iteration commit. This includes verifying path references, checking cross-reference accuracy, and ensuring adherence to formatting standards.

### Completeness Requirements
Each iteration must produce complete documentation covering design decisions, implementation details, testing procedures, and integration requirements. Incomplete documentation prevents iteration completion and code commits.

### Review and Approval Process
All documentation modifications must undergo review for technical accuracy, clarity, and adherence to standards. Critical protocol documents require approval before implementation, while implementation documentation requires validation before commit.

## Template Integration

### Standardized Document Templates
All documentation categories must have corresponding templates in the `doc/templates/` directory. These templates ensure consistency and completeness while reducing documentation creation overhead.

### Template Compliance
New documents must be created from appropriate templates and must maintain template structure while adapting content for specific requirements. Deviations from template structure require justification and approval.

### Template Evolution
Templates must be updated based on lessons learned and process improvements identified during iteration retrospectives. Template changes require validation across existing documents to ensure consistency.

## Cross-Platform Documentation Considerations

### Platform-Specific Content Management
Documentation must clearly distinguish between platform-independent content and platform-specific implementations. Platform-specific sections must be clearly marked and organized to facilitate maintenance and updates.

### Configuration Documentation Standards
Configuration file documentation must include examples for all supported platforms with clear explanations of platform-specific variations. Default configurations must be documented with explanations of modification procedures.

### Deployment Documentation Requirements
Deployment procedures must be documented for both development (Mac) and production (Raspberry Pi) environments with clear step-by-step instructions and verification procedures.

## Documentation Maintenance Procedures

### Regular Review Cycles
Documentation accuracy must be validated during each iteration to ensure continued relevance and accuracy. Outdated information must be updated or marked as deprecated with appropriate migration guidance.

### Archive Management
Superseded documentation must be moved to archive locations with clear indicators of replacement documents. Archived documents must retain their original structure and content for historical reference.

### Continuous Improvement
Documentation standards must evolve based on usage patterns, tool capabilities, and process improvements identified through regular retrospectives and quality assessments.

---

**Implementation Priority**: Immediate  
**Dependencies**: Protocol 1 (Project Structure), Protocol 2 (Iteration Workflow)  
**Related Protocols**: Protocol 4 (Claude Integration), Protocol 7 (Obsidian Integration)
