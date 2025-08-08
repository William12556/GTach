# Protocol 2: Iteration-Based Development Workflow

**Created**: 2025 01 06  
**Version**: 1.1  
**Status**: Active  

## Purpose

Define the systematic approach for iterative development cycles that support single-developer workflow with AI assistance, ensuring consistent documentation, testing, and deployment procedures across all development phases.

## Iteration Framework

### Sequential Numbering System
- **Format**: Three-digit zero-padded sequential numbers (001, 002, 003)
- **Persistence**: Numbers never reused regardless of iteration outcome
- **Scope**: Applied to all development activities, documentation, and version tracking
- **Assignment**: Sequential allocation based on chronological order of iteration initiation

### Iteration Triggers
Development iterations are initiated when one of the following conditions occurs:

#### New Feature Development
- Implementation of previously unimplemented functionality
- Addition of new capabilities to existing modules
- Integration of external dependencies or APIs
- Creation of new user interfaces or interaction patterns

#### Debugging and Issue Resolution
- Resolution of identified bugs or defects
- Performance optimization requirements
- Security vulnerability remediation
- Cross-platform compatibility corrections

### Iteration Lifecycle

#### Phase 1: Planning and Design
**Duration**: Variable based on complexity  
**Deliverables**: Design document, change plan, success criteria

**Activities**:
- Requirements analysis and clarification
- Previous iteration synopsis review and context integration
- Technical design specification creation
- Impact assessment on existing codebase
- Resource and timeline estimation
- Risk identification and mitigation planning
- AI coordination strategy development

**Documentation Requirements**:
- Design document in doc/design/Design_[iteration]_[component].md
- Change plan in doc/change/Change_[iteration]_[description].md
- Integration requirements specification
- AI coordination context documentation in ai/project_knowledge/

#### Phase 2: Implementation
**Duration**: Focused development sprint  
**Deliverables**: Functional code, unit tests, integration tests

**Activities**:
- Claude Code prompt creation and execution
- Source code development following thread safety requirements
- Comprehensive logging and error handling implementation
- Unit test creation and validation
- Integration test development

**Documentation Requirements**:
- Claude Code prompts archived in doc/prompts/Prompt_[iteration]_[task].md
- Implementation notes and decision records
- Code review preparation materials

#### Phase 3: Testing and Validation
**Duration**: Comprehensive testing cycle  
**Deliverables**: Test results, validation reports, deployment confirmation

**Activities**:
- Multi-layer testing execution (Unit, Business Logic, Platform Interface, Hardware Integration)
- Cross-platform compatibility validation
- Performance benchmarking where applicable
- Security assessment for relevant components
- Documentation completeness verification

**Testing Architecture Implementation**:
```
Layer 1: Unit Tests (Mac Compatible)
├── Individual function and method testing
├── Mock-based dependency isolation
└── Automated execution in development environment

Layer 2: Business Logic Tests (Mac Compatible)  
├── Component integration testing
├── Workflow validation testing
└── Data processing accuracy verification

Layer 3: Platform Interface Tests (Mock Mac/Real Pi)
├── Platform-specific API interaction testing
├── Configuration management validation
└── Cross-platform behavior verification

Layer 4: Hardware Integration Tests (Pi Only)
├── GPIO interface validation
├── System resource utilization testing
└── Real-world scenario simulation
```

#### Phase 4: Documentation and Review
**Duration**: Documentation completion and review cycle  
**Deliverables**: Complete documentation set, audit trail, lessons learned

**Activities**:
- Technical documentation updates
- User documentation modifications
- Code review completion and approval
- Security and compliance review where applicable
- Performance impact assessment
- AI coordination materials archival and organization
- Conversation synopsis creation for future iteration continuity

#### Phase 5: Deployment and Integration
**Duration**: Code integration and deployment verification  
**Deliverables**: Integrated codebase, deployment verification, rollback plan

**Activities**:
- Git integration with single commit per iteration
- Deployment package creation and transfer to target platform (Raspberry Pi)
- Package installation/update via setup.py on target platform
- Integration testing in production environment
- Rollback procedure validation
- Stakeholder communication and approval

## Documentation Standards per Iteration

### Mandatory Documents
Each iteration must produce the following documentation set:

**Design Documentation**:
- Technical specification document
- Architecture decision records
- Interface definitions and contracts
- Performance and scalability considerations
- Visual documentation per Protocol 12 standards including system architecture diagrams, component interaction diagrams, and cross-platform architecture visualizations
- Master document validation and subsidiary diagram coordination where system-level changes are involved

**Implementation Documentation**:
- Claude Code prompt archive with complete context
- Code review notes and approval records
- Implementation decision justifications
- Technical debt identification and management plan

**Testing Documentation**:
- Test plan and test case specifications
- Test execution results and coverage reports
- Performance benchmarking results
- Cross-platform validation confirmations

**Change Documentation**:
- Change impact assessment
- Integration procedures and verification steps
- Rollback procedures and contingency plans
- Stakeholder communication records

**AI Coordination Documentation**:
- Conversation synopsis for iteration continuity
- AI tool coordination records and effectiveness assessment
- Technical knowledge updates in ai/project_knowledge/
- AI workflow optimization insights and recommendations

### Documentation Quality Standards
- All documents must include creation timestamp
- Comprehensive cross-references to related iterations
- Clear success criteria and acceptance definitions
- Detailed implementation procedures and verification steps

## Commit and Version Control Integration

### Single Commit Policy
Each completed iteration results in exactly one commit to the main branch, ensuring:
- Clear correlation between iterations and code changes
- Simplified rollback procedures and change tracking
- Comprehensive commit messages with iteration context
- Atomic changes that can be independently validated

### Commit Message Format
```
Iteration [number]: [brief description]

- Feature/Bug: [detailed description]
- Testing: [validation summary] 
- Documentation: [updates completed]
- Platform: [compatibility status]
```

### Pre-Commit Validation
Before commit execution, the following validations must be completed:
- All iteration documentation updated and reviewed
- Test suite execution with 100% pass rate
- Code review completed and approved
- Cross-platform compatibility confirmed where applicable

## Cross-Platform Development Integration

### Development Environment Workflow
- **Primary Development**: M4 Mac Mini with full development stack
- **Target Deployment**: Raspberry Pi Linux with production configuration
- **Testing Strategy**: Mac-compatible development with Pi validation

### Platform-Specific Considerations
- Configuration management through platform detection and JSON configuration
- Conditional imports and mocks for cross-platform compatibility
- Automated deployment and testing pipeline between platforms
- Platform-specific performance and resource optimization

### Enhanced Deployment Workflow
- **Mac Pre-flight Testing**: Complete test suite execution before Pi deployment
- **Package Creation**: Tar archive creation with deployment manifest
- **Secure Transfer**: SCP-based package transfer to Pi environment
- **Installation/Update**: setup.py execution for package installation or update
- **Production Validation**: Hardware integration testing on target platform
- **Rollback Capability**: Previous version restoration procedures for failed deployments

## Quality Assurance Integration

### Code Quality Requirements
- Thread safety mandatory for all concurrent operations
- Comprehensive crash logging with full traceback information
- Robust error handling and graceful degradation
- Professional-level code commenting and documentation

### Testing Requirements
- Unit test coverage minimum 80% for all modules
- Integration test coverage for all public interfaces
- Cross-platform compatibility validation for all platform-dependent code
- Performance regression testing for optimization-focused iterations

### Security and Compliance
- Security review for all external interface implementations
- Data protection compliance for any data handling modifications
- Access control validation for system resource interactions
- Audit trail maintenance for all significant changes

## Iteration Metrics and Tracking

### Success Criteria Definition
Each iteration must define measurable success criteria including:
- Functional requirements satisfaction
- Performance benchmarks and acceptance thresholds
- Cross-platform compatibility confirmation
- Documentation completeness verification

### Progress Tracking
- Iteration duration tracking and analysis
- Defect density monitoring across iterations
- Technical debt accumulation and resolution tracking
- Platform-specific issue identification and resolution

### Continuous Improvement
- Retrospective analysis after each iteration
- Process refinement based on lessons learned
- Tool effectiveness evaluation and optimization
- Workflow efficiency measurement and enhancement

---

**Implementation Priority**: Immediate  
**Dependencies**: Protocol 1 (Project Structure)  
**Related Protocols**: Protocol 3 (Documentation Standards), Protocol 4 (Claude Integration), Protocol 6 (Cross-Platform Development), Protocol 11 (Enhanced AI Memory and Session Management), Protocol 12 (Visual Documentation Standards)
