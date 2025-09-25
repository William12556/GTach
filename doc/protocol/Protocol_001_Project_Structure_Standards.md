# Protocol 1: Project Structure Standards

**Created**: 2025 01 06  
**Version**: 3.2  
**Status**: Active  
**Last Updated**: 2025 09 25  

## Purpose

Establish standardized directory structure and file organization principles for the GTach project to maintain consistency, facilitate navigation, and support cross-platform development workflows.

## Directory Structure Requirements

### Root Directory Structure
```
/Users/williamwatson/Documents/GitHub/GTach/
├── README.md                  # Project overview and setup instructions
├── RELEASE_NOTES.md          # Current release summary with links to detailed release documentation
├── .gitignore                 # Git exclusion patterns
├── requirements.txt           # Python dependencies
├── license.md                 # Project licensing information
├── pyproject.toml            # Modern Python project configuration
├── releases/                 # Release documentation directory
│   └── RELEASE_NOTES_v*.md   # Detailed version-specific release documentation
├── src/                      # Source code directory (organized functional hierarchy)
│   ├── [module_files].py     # Root-level modules
│   ├── functional_domain/    # Functional grouping (level 1)
│   │   ├── [component].py    # Domain components (level 2)
│   │   └── component_group/  # Component categories (level 2)
│   │       └── [impl].py     # Specific implementations (level 3 maximum)
│   └── tests/                # Test files only
├── doc/                      # Project documentation (Obsidian managed)
│   ├── protocol/             # Development protocols
│   ├── prompts/              # AI tool prompts organized by tool type
│   │   ├── claude/           # Claude Code prompts (Protocol 4)
│   │   └── codestral/        # Codestral 22b prompts (Protocol 14)
│   ├── change/               # Change documentation
│   ├── audits/               # Code and process audits
│   ├── design/               # Design documents
│   │   ├── diagrams/         # Visual documentation (Protocol 12)
│   │   │   ├── master/       # Master document hierarchy
│   │   │   │   ├── system_architecture.md    # Master System Architecture
│   │   │   │   ├── component_interaction.md  # Master Component Interaction
│   │   │   │   ├── cross_platform.md        # Master Cross-Platform Architecture
│   │   │   │   ├── hardware_interface.md    # Master Hardware Interface
│   │   │   │   └── data_flow.md             # Master Data Flow
│   │   │   ├── architecture/ # System architecture diagrams (subsidiary)
│   │   │   ├── components/   # Component interaction diagrams (subsidiary)
│   │   │   ├── hardware/     # Hardware interface diagrams (subsidiary)
│   │   │   ├── cross_platform/ # Cross-platform architecture diagrams (subsidiary)
│   │   │   └── data_flow/    # Data flow and process diagrams (subsidiary)
│   │   └── [design_docs]     # Design documents
│   ├── hardware/             # Hardware documentation and specifications
│   │   ├── diagrams/         # Hardware-specific visual documentation (subsidiary)
│   │   └── [hardware_docs]   # Hardware specifications
│   ├── issues/               # Issue tracking
│   └── templates/            # Document templates
└── ai/                       # AI coordination materials (separate hierarchy)
    ├── sessions/             # Session-based conversation continuity (Protocol 11)
    │   ├── session_[YYYYMMDD]/ # Daily session organization
    │   └── active_session/   # Current session working state
    ├── project_knowledge/    # Persistent technical knowledge and reference materials
    │   ├── architecture/     # System architecture knowledge
    │   ├── patterns/         # Implementation patterns and standards
    │   ├── decisions/        # Architectural decision records
    │   ├── lessons_learned/  # Experience-based knowledge
    │   └── cross_platform/   # Platform-specific knowledge
    ├── project_instructions/ # AI tool instructions and workflow guidance
    │   ├── session_management/ # Session continuity procedures
    │   ├── analysis_frameworks/ # Systematic analysis approaches
    │   ├── prompt_evolution/ # Prompt improvement tracking
    │   └── workflow_optimization/ # Workflow enhancement patterns
    └── synopses/             # Conversation summaries and session continuity
        ├── active/           # Current iteration synopsis materials
        ├── completed/        # Completed iteration records
        └── analysis/         # Cross-session analysis and insights
```

### Source Code Organization

#### Primary Principles
- **Three-Level Maximum**: Maximum three levels of nesting within src/ for complex embedded systems
- **Functional Hierarchy**: Organize by functional domain → component category → specific implementation
- **Single Responsibility**: Each module focuses on specific functionality
- **Clear Naming**: Descriptive file and directory names using snake_case
- **Test Isolation**: All test files contained within src/tests/ directory

#### Directory Organization Guidelines
- **Root Level**: Core application modules and simple utilities
- **Level 1 - Functional Domains**: Related modules grouped by primary function (comm/, display/, core/)
- **Level 2 - Component Categories**: Logical groupings within domains (components/, input/, rendering/)
- **Level 3 - Specific Implementations**: Concrete implementations (bluetooth/, layout/, state/)
- **Maximum Nesting**: Three levels maximum (src/domain/category/implementation.py)
- **Domain Examples**: comm/, display/, core/, utils/, config/

#### Complexity-Based Structure
- **Simple Projects**: Flat structure with root-level modules only
- **Intermediate Systems**: Functional domains with direct components
- **Complex Embedded Systems**: Full three-level hierarchy for sophisticated architectures
- **Domain Boundaries**: Clear separation of concerns between functional areas
- **Migration Path**: Start flat, organize into domains, add categories as complexity grows

### Documentation Architecture

#### Documentation Hierarchy
- **protocol/**: Development workflow and standards documentation
- **prompts/**: AI tool prompts organized by tool type following Protocol 015 orchestration framework
  - **prompts/claude/**: Claude Code prompts following Protocol 4 standards for strategic implementation
  - **prompts/codestral/**: Codestral 22b prompts following Protocol 14 standards with MCP filesystem access
- **change/**: Change requests, impact assessments, and implementation records
- **audits/**: Code reviews, security assessments, and compliance checks
- **design/**: Architecture decisions, technical specifications, and design patterns including visual documentation through Protocol 12 diagram standards
  - **design/diagrams/**: Visual documentation organized by master documents and subsidiary categories
  - **design/diagrams/master/**: Master document hierarchy providing authoritative single sources of truth
  - **design/diagrams/components/**: Component diagrams organized by functional domain matching src/ directory structure
- **hardware/**: Hardware specifications, integration procedures, and testing documentation with visual documentation support
  - **hardware/diagrams/**: Hardware-specific visual documentation including GPIO interfaces and physical connection specifications (subsidiary)
- **issues/**: Bug reports, feature requests, and problem tracking
- **templates/**: Standardized document formats for consistent documentation

#### Diagram-Source Code Alignment
The design/diagrams/components/ directory structure must align with src/ functional domains to maintain consistency between architectural documentation and implementation organization:
- Component diagram subdirectories mirror src/ functional domain organization
- Each functional domain (e.g., comm/, display/, core/) has corresponding diagram subdirectory
- Diagram organization supports Protocol 1 three-level maximum nesting principle
- Cross-functional integration documented in master diagrams rather than component-specific diagrams

#### Obsidian Integration Requirements
- All documentation directories linked via symbolic links to Obsidian vault
- Cross-references managed manually to maintain consistency
- Markdown format mandatory for all documentation files
- No auto-generation of links or cross-references

### AI Coordination Architecture

#### AI Materials Organization
- **sessions/**: Session-based conversation continuity with daily organization and active session management (Protocol 11)
- **project_knowledge/**: Enhanced technical knowledge repository with specialized subsections for architecture, patterns, decisions, lessons learned, and cross-platform knowledge
- **project_instructions/**: AI tool coordination procedures with session management, analysis frameworks, prompt evolution, and workflow optimization capabilities
- **synopses/**: Conversation continuity materials organized into active, completed, and analysis categories for comprehensive session management

#### Separation from Project Documentation
- AI coordination materials maintained independently of project documentation hierarchy while providing enhanced session continuity and knowledge evolution capabilities
- AI directory structure excluded from core project deliverables but supports sophisticated multi-session development workflows
- Clear boundaries between development support materials and project artifacts while enabling systematic knowledge accumulation and pattern recognition
- Integration capabilities preserved while maintaining organizational separation and enabling advanced session management features

## File Naming Conventions

### Source Code Files
- **Python Modules**: snake_case.py (e.g., gpio_controller.py)
- **Test Files**: test_[module_name].py (e.g., test_gpio_controller.py)
- **Configuration Files**: [purpose]_config.py (e.g., platform_config.py)

### File Modification Standards
- **Direct Modification**: Modify existing files rather than creating new versions
- **Filename Preservation**: Maintain original filenames during enhancements
- **Prohibited Suffixes**: No _enhanced, _v2, _updated, _new, _modified suffixes
- **Version Control**: Git history provides file versioning - no manual file versioning

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
- **RELEASE_NOTES.md**: Current release summary with links to detailed release documentation in releases/ directory
- **.gitignore**: Python-specific exclusions, platform-specific temporary files, IDE configurations
- **requirements.txt**: All Python dependencies with version specifications
- **license.md**: Project licensing terms and attribution requirements

### Release Management Requirements
- **releases/ directory**: Contains detailed version-specific release documentation
- **RELEASE_NOTES_v*.md**: Detailed technical release notes following standardized format
- **Root RELEASE_NOTES.md**: Summary file linking to detailed release documentation
- **Version consistency**: Release versions must align with pyproject.toml version specifications

### Optional Configuration Files
- **pyproject.toml**: Modern Python project metadata and build system configuration
- **Makefile**: Build automation and common task shortcuts

### Root Directory Restrictions
**Prohibited in Root Directory**:
- Python source code files (.py) - All source code must reside in src/ directory
- Test files - All test files must reside in src/tests/ directory
- Implementation files - No implementation artifacts in project root
- Temporary development files - Must be excluded via .gitignore

**Exception Handling**: Only essential project configuration and documentation files permitted in root directory.

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
- Functional domain organization must align with system architecture
- No nesting beyond three levels without protocol revision
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
**Related Protocols**: Protocol 2 (Iteration Workflow), Protocol 3 (Documentation Standards), Protocol 12 (Visual Documentation Standards)

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
