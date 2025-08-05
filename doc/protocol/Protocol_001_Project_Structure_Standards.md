# Protocol 1: Project Structure Standards

**Created**: 2025 01 06  
**Version**: 1.0  
**Status**: Active  

## Purpose

Establish standardized directory structure and file organization principles for the GTach project to maintain consistency, facilitate navigation, and support cross-platform development workflows.

## Directory Structure Requirements

### Root Directory Structure
```
/Users/williamwatson/Documents/GitHub/GTach/
├── README.md                  # Project overview and setup instructions
├── .gitignore                 # Git exclusion patterns
├── requirements.txt           # Python dependencies
├── license.md                 # Project licensing information
├── setup.py                   # Python package setup configuration
├── pyproject.toml            # Modern Python project configuration
├── src/                      # Source code directory (flat structure)
│   └── tests/                # Test files only
├── doc/                      # Project documentation (Obsidian managed)
│   ├── protocol/             # Development protocols
│   ├── prompts/              # Claude Code prompts archive
│   ├── change/               # Change documentation
│   ├── audits/               # Code and process audits
│   ├── design/               # Design documents
│   ├── hardware/             # Hardware documentation and specifications
│   ├── issues/               # Issue tracking
│   └── templates/            # Document templates
└── ai/                       # AI coordination materials (separate hierarchy)
    ├── project_knowledge/    # Persistent technical knowledge and reference materials
    ├── project_instructions/ # AI tool instructions and workflow guidance
    └── synopses/             # Conversation summaries and session continuity
```

### Source Code Organization

#### Primary Principles
- **Flat Structure**: Maximum one level of subdirectories within src/
- **Single Responsibility**: Each module focuses on specific functionality
- **Clear Naming**: Descriptive file and directory names using snake_case
- **Test Isolation**: All test files contained within src/tests/ directory

#### Subdirectory Guidelines
- Platform-specific modules may have single-level subdirectories (src/platform/)
- Configuration modules may be grouped (src/config/)
- Utility functions should remain in root src/ level
- No nested subdirectories beyond one level

### Documentation Architecture

#### Documentation Hierarchy
- **protocol/**: Development workflow and standards documentation
- **prompts/**: Archive of all Claude Code prompts organized by iteration
- **change/**: Change requests, impact assessments, and implementation records
- **audits/**: Code reviews, security assessments, and compliance checks
- **design/**: Architecture decisions, technical specifications, and design patterns
- **hardware/**: Hardware specifications, integration procedures, and testing documentation
- **issues/**: Bug reports, feature requests, and problem tracking
- **templates/**: Standardized document formats for consistent documentation

#### Obsidian Integration Requirements
- All documentation directories linked via symbolic links to Obsidian vault
- Cross-references managed manually to maintain consistency
- Markdown format mandatory for all documentation files
- No auto-generation of links or cross-references

### AI Coordination Architecture

#### AI Materials Organization
- **project_knowledge/**: Technical knowledge repository for cross-iteration reference
- **project_instructions/**: AI tool coordination procedures and workflow guidance
- **synopses/**: Conversation continuity materials and session summaries

#### Separation from Project Documentation
- AI coordination materials maintained independently of project documentation hierarchy
- AI directory structure excluded from core project deliverables
- Clear boundaries between development support materials and project artifacts
- Integration capabilities preserved while maintaining organizational separation

## File Naming Conventions

### Source Code Files
- **Python Modules**: snake_case.py (e.g., gpio_controller.py)
- **Test Files**: test_[module_name].py (e.g., test_gpio_controller.py)
- **Configuration Files**: [purpose]_config.py (e.g., platform_config.py)

### Documentation Files
- **Protocols**: Protocol_[number]_[title].md (e.g., Protocol_001_Project_Structure_Standards.md)
- **Design Documents**: Design_[iteration]_[component].md (e.g., Design_001_GPIO_Interface.md)
- **Change Documents**: Change_[iteration]_[description].md (e.g., Change_001_GPIO_Implementation.md)
- **Templates**: Template_[document_type].md (e.g., Template_Design_Document.md)

### Iteration-Based Numbering
- **Format**: Three-digit zero-padded numbers (001, 002, 003)
- **Scope**: Applied to all development iterations and associated documentation
- **Persistence**: Numbers never reused, sequential assignment only

## Root Directory File Requirements

### Mandatory Files
- **README.md**: Comprehensive project overview with setup instructions and usage examples
- **.gitignore**: Python-specific exclusions, platform-specific temporary files, IDE configurations
- **requirements.txt**: All Python dependencies with version specifications
- **license.md**: Project licensing terms and attribution requirements

### Optional Configuration Files
- **setup.py**: Python package installation and distribution configuration
- **pyproject.toml**: Modern Python project metadata and build system configuration
- **Makefile**: Build automation and common task shortcuts

## Cross-Platform Considerations

### Path Standards
- **Separator**: Forward slashes (/) for all path references
- **Absolute Paths**: Avoided in documentation and configuration
- **Relative Paths**: Used consistently from project root
- **Platform Detection**: Implemented in code, not reflected in structure

### Platform-Specific Components
- **Configuration**: Managed through JSON configuration files
- **Dependencies**: Specified in requirements.txt with platform markers when necessary
- **Testing**: Cross-platform compatibility validated through multi-layer testing architecture

## Validation Requirements

### Structure Compliance
- All directories must exist before code implementation begins
- No deviation from flat source structure without documented justification
- Documentation directories must be populated with appropriate templates

### File Organization
- Source files categorized by functionality, not implementation details
- Test coverage requirements met for all modules
- Documentation updated before code commits

## Integration with Development Workflow

### Iteration Management
- Each iteration creates numbered subdirectories within relevant doc/ folders
- Source code changes tracked through git with iteration-based commit messages
- Documentation updates mandatory before iteration completion

### Tool Integration
- Structure supports Claude Desktop design responsibilities
- Compatible with Claude Code development workflow requirements
- Facilitates GitHub Desktop version control operations
- Enables Obsidian vault management of documentation

## Compliance Monitoring

### Regular Assessments
- Directory structure validated before each iteration
- File naming conventions checked during code reviews
- Documentation completeness verified before commits

### Corrective Actions
- Structure violations addressed immediately
- Non-compliant files renamed or relocated
- Missing documentation created before proceeding with development

---

**Implementation Priority**: Immediate  
**Dependencies**: None  
**Related Protocols**: Protocol 2 (Iteration Workflow), Protocol 3 (Documentation Standards)
