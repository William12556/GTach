Created: 2025 October 30

# LLM Orchestration Framework

---

## Table of Contents

**Cross-cutting**

- [P00 Governance (start here)](<#p00 governance (start here)>)
- [P01 Trace](<#p01 trace>)
- [P02 Audit](<#p02 audit>)
- [P03 Issue](<#p03 issue>)
- [P04 Change](<#p04 change>)

**Lifecycle**

- [P10 Project Initialization (Execute once)](<#p10 project initialization (execute once)>)
- [P11 Requirements](<#p11 requirements>)
- [P12 Design](<#p12 design>)
- [P13 Prompt](<#p13 prompt>)
- [P14 Quality](<#p14 quality>)
- [P15 Test](<#p15 test>)

**Templates**

- [T01: Requirements](templates/T01-requirements.md)
- [T02: Design](templates/T02-design.md)
- [T03: Prompt](templates/T03-prompt.md)
- [T04: Test](templates/T04-test.md)
- [T05: Result](templates/T05-result.md)
- [T06: Issue](templates/T06-issue.md)
- [T07: Change](templates/T07-change.md)
- [T08: Audit](templates/T08-audit.md)

[Workflow](<#workflow>)
[Version History](<#version history>)
[Appendix A — Identifier Aliases](<#appendix a — identifier aliases>)

---
###### Governance Prime Directive: Follow workflow [flowchart](workflow.md)
---
## P00 Governance (start here)


  - P00.1 Purpose
    - Python based software engineering, architecture and development
  - P00.2 Scope
    - Agnostic plan, control and initiation of software generation
  - P00.3 Framework Practice
    - This governance framework defines software development processes and workflows
    - Strategic Domain/Tactical Domain separation applies to software creation, not to generated application runtime
    - Generated software/applications (outputs) are independent of framework architecture
    - Framework controls: how we build software
    - Framework does not control: how the built software operates
    - Example: \<project name\> uses this framework for development but is a standalone Python application at runtime
  - P00.4 Architecture (Model-Agnostic)
    - Strategic Domain: Plan and control: design, change, test and launching of code generation
      - Implementation options: Claude Desktop, API-based LLM
    - Tactical Domain: Execute: code generation
      - Implementation options: Ralph Loop (AEL), Claude Code, claude-omlx, custom agents, direct invocation
    - Communication: MCP filesystem (model-independent)
  - P00.5 Forbidden
    - Both domains: Unrequested creation, addition, removal or change of source code and documents is forbidden
  - P00.6 Constraints
    - Strategic Domain: Does not exceed language model context resource budget when communicating with Tactical Domain
  - P00.7 Control
    - Strategic Domain: Strategic coordination and validation authority
    - Strategic Domain: Analyzes requirements and formulates design specifications
    - Strategic Domain: Creates T03 prompts with complete technical context
    - Strategic Domain: Validates Tactical Domain implementation for protocol compliance
    - Strategic Domain: Coordinates quality assurance and integration verification
    - Tactical Domain: Tactical implementation with project awareness
    - Tactical Domain: Generates source code with MCP filesystem access
    - Tactical Domain: Performs direct file operations in src/ directory
    - Tactical Domain: Validates protocol compliance through direct file access
    - Tactical Domain: Coordinates multi-file implementations and dependencies

  - P00.8 Communication
    - Both Strategic Domain and Tactical Domain have MCP filesystem access to project
    - Model Implementation Details:
      - Strategic Domain model specified in project configuration
      - Tactical Domain model(s) specified in execution recipes
      - Multi-model orchestration supported (e.g., worker/reviewer pattern)
    - Communication uses filesystem-based message passing (semaphores)
    - Strategic Domain: Reads template from ai/templates/T03-prompt.md
    - Strategic Domain: Uses T03 template to create code generation or debug prompts for Tactical Domain
    - Strategic Domain: Embeds complete Tier 3 component design specifications and schema within prompt documents
    - Strategic Domain: Ensures prompt documents are self-contained requiring no external file references
    - Strategic Domain: Saves T03 prompt to ai/workspace/prompt/prompt-\<uuid\>-\<name\>.md
    - Strategic Domain: Provides ready-to-execute AEL command in conversation after human approval
    - Human: Executes AEL command from project root
    - AEL: Reads T03 prompt as task; runs worker/reviewer Ralph Loop until SHIP or BLOCKED
    - AEL SHIP: Strategic Domain reviews generated code, proceeds with audit
    - AEL BLOCKED: Strategic Domain creates T06 Issue from RALPH-BLOCKED.md content
    - Command format:
```bash
python ai/ael/src/orchestrator.py --mode loop \
  --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```
  - P00.9 Quality
    - Human review and approval of design, change and initiation of code generation is required
    - Strategic Domain: Provides ready-to-execute command after human approval
    - Human: Invokes Tactical Domain with provided command
    - Human: Notifies Strategic Domain when Tactical Domain completes
    - Strategic Domain: Reviews generated code before proceeding
  - P00.10 Documents
    - Master documents: \<document class\>-\<document name\>-master.md
      - No UUID assigned (master documents are singletons per project)
      - Examples: design-myproject-master.md, trace-traceability-matrix-master.md
    - All other documents: \<document class\>-\<uuid\>-\<document name\>.md
      - Strategic Domain: Generates 8-character UUID (first 8 hex digits of UUID v4)
      - Examples: change-a3f5b2c1-fix-parser.md, issue-d7e9f1a4-network-timeout.md
    - Strategic Domain: Design documents follow tier naming convention: master_, domain_, component_ prefixes
    - Strategic Domain: Insures related documents are Obsidian cross linked
    - Document classes that require a master document are: design, audit, trace and test
    - Design class includes a dedicated name registry master: design-\<project\>-name_registry-master.md
    - All document classes (issue, change, prompt, test, result) contain internal iteration field starting at 1
    - Iteration increments when document enters new cycle after failed verification
    - Git commit required after iteration field modification
    - Filesystem contains only current iteration; GitHub history preserves prior iterations
    - Coupled documents maintain synchronized iteration numbers via explicit UUID references

  - P00.11 Autonomous Execution Loop (AEL)
    - Reference implementation: Ralph Loop via Python AEL orchestrator (`ai/ael/`)
    - AEL provides autonomous iterative code generation within governance boundaries
    - Loop State Directory: `ai/state/ralph/` (ephemeral, per-task)
    - Loop Entry: After human approval of T03 Prompt
    - Integration Scripts: Project-scoped scripts reside in `<project>/bin/`. Scripts are version-controlled project artifacts. Global installation (e.g. `~/bin/`) is not required.
    - Claude Desktop Interface: `ael-mcp` (standalone repository) provides `start_ael`, `ael_status`, and `reset_ael` MCP tools for use within the Claude Desktop profile; registers once in Claude Desktop MCP configuration; serves all downstream projects via `project_dir` parameter; reference: P10.8
    - Loop Execution: Worker/reviewer cycle until SHIP or boundary exceeded
    - Loop Exit: SHIP → Strategic Domain captures work-summary.txt in T05 Result; BLOCKED → Strategic Domain seeds T06 Issue from RALPH-BLOCKED.md
    - State Files:
      - `task.md`: Task description from T03
      - `iteration.txt`: Current cycle number
      - `work-summary.txt`: Worker iteration output
      - `work-complete.txt`: Worker completion signal
      - `review-result.txt`: SHIP or REVISE decision
      - `review-feedback.txt`: Reviewer notes for next iteration
      - `.ralph-complete`: Success marker
      - `RALPH-BLOCKED.md`: Failure details
    - Boundary Conditions:
      - MAX_ITERATIONS: Configurable per task (default 10-50)
      - TOKEN_BUDGET: Aggregate token limit
      - TIME_LIMIT: Wall-clock timeout
      - DIVERGENCE: Repeated failure detection
    - Traceability: Loop summary captured in T05 Result document
  - P00.12 Configuration Management
    - GitHub repository is authoritative source for all project artifacts
    - Human: Tags design document commits when approved as baseline for code generation via GitHub Desktop (History → right-click commit → Create Tag → Push Tags)
    - Strategic Domain: Performs configuration audit verifying generated code matches approved design baseline commits
    - Strategic Domain: Uses config-audit template from ai/workspace/audit/config-audit-template.md
    - Strategic Domain: Verifies code matches tagged design baseline specifications
    - Strategic Domain: Documents findings in config-audit-NNNN-YYYY-MM-DD.md
    - Strategic Domain: Stores configuration audits in ai/workspace/audit/
    - Critical deviations: Creates issues via P03 for remediation
  - P00.13 Versioning
    - All versioning is handled via GitHub
    - Project uses Semantic Versioning per https://semver.org
    - Format: MAJOR.MINOR.PATCH (e.g., 1.0.0, 1.2.3)
    - MAJOR: Incompatible API changes or major functionality changes
    - MINOR: Backwards-compatible functionality additions
    - PATCH: Backwards-compatible bug fixes
    - Pre-release versions: MAJOR.MINOR.PATCH-alpha.N, -beta.N, -rc.N (e.g., 1.0.0-alpha.1)
    - Initial development: 0.y.z (MAJOR version zero for initial development)
    - Git tags format: vMAJOR.MINOR.PATCH (e.g., v1.0.0, v0.1.0)
    - Release notes filename: RELEASE_NOTES_vMAJOR.MINOR.PATCH.md
  - P00.14 Document Lifecycle Management
    - P00.14.1 Active State
      - Active documents reside in ai/workspace/\<class\>/
      - Active documents are mutable during iteration cycles
      - Iteration field increments with each debug/refinement cycle
      - Git commit required after each iteration increment
    - P00.14.2 Closed State
      - Upon human acceptance, documents moved to ai/workspace/\<class\>/closed/
      - Closed documents are immutable
      - Closed documents preserve final iteration number
      - Access: Read-only reference for future work
    - P00.14.3 Closure Criteria
      - Issue: Resolved and verified, corresponding change implemented and tested
      - Change: Implemented, tested, design updated, human accepted
      - Prompt: Code generated successfully, human confirmed
      - Test: Executed with passing results, result document created
      - Result: Tests passed, no issues created, acceptance confirmed
      - Audit: Per P02.8 Audit Closure (P02.8.1 criteria, P02.8.2 process)
    - P00.14.4 Archival Procedure
      - Human initiates closure after acceptance
      - Strategic Domain verifies closure criteria met
      - Strategic Domain moves coupled document set to respective closed/ subfolders
      - Git commit records closure transition
      - Closed documents referenced but not modified
    - P00.14.5 Closed Subfolder Structure
      - ai/workspace/issues/closed/
      - ai/workspace/change/closed/
      - ai/workspace/prompt/closed/
      - ai/workspace/audit/closed/
      - ai/workspace/test/closed/
      - ai/workspace/report/closed/
      - ai/workspace/test/result/closed/
    - P00.14.6 Access Constraints
      - Closed documents: Read-only access for reference
      - No modifications permitted to closed documents
      - New work requires new document with new sequence number
      - Reopening closed work: Create new issue referencing closed documents
  - P00.15 Logging Standards
    - Generated applications implement environment-based log level control
    - Debug mode enables verbose logging for development and testing
    - Normal mode restricts logging to informational events only
    - Flat file format recommended: timestamp level logger message
    - Centralized log location per application requirements
    - Log rotation policy prevents disk exhaustion
    - Test environments use debug mode for comprehensive logging
    - Production environments use normal mode for operational efficiency
    - Log artifacts preserved for failure analysis
  - P00.16 Knowledge Base
    - Projects may optionally maintain a knowledge/ subdirectory under ai/workspace/ for institutional knowledge capture
    - Knowledge documents may contain: problem statements, solutions, examples, rationale
    - Knowledge base prevents repeated problem-solving across development cycles
  - P00.17 Templates
    - All templates are external documents in ai/templates/ directory
    - Template files:
      - ai/templates/T02-design.md
      - ai/templates/T07-change.md
      - ai/templates/T06-issue.md
      - ai/templates/T03-prompt.md
      - ai/templates/T04-test.md
      - ai/templates/T05-result.md
      - ai/templates/T01-requirements.md
      - ai/templates/T08-audit.md
    - Strategic Domain: Read template from ai/templates/ before creating documents
    - Tactical Domain: Read templates when referenced in prompt documents
    - Templates contain YAML structure and JSON Schema validation rules
  - P00.18 Skills Management (Claude Code profiles only)
    - Tactical Domain: Utilizes skills from .claude/ for reusable workflows
    - Canonical source: ai/skills/ — provisioned into .claude/ during P10.8; mirrors .claude/ subdirectory organization
    - Skills organization: governance/, testing/, validation/, audit/ subdirectories under .claude/
    - Hot-reload enabled: Skill modifications activate without session restart
    - Forked contexts: Validation skills execute in isolated sub-agent contexts
    - Lifecycle hooks: PreToolUse (schema validation), PostToolUse (compliance verification), Stop (cleanup)
    - Skills repository: Project-specific skills checked into git for team sharing (.claude/settings.json tracked; .claude/settings.local.json gitignored)
    - Implementation: See ai/profiles/claude-code.md or ai/profiles/claude-omlx.md
    - Mandatory skill:
      - ai/skills/validation/run-tests.md: PostToolUse pytest execution (P15.15); required for claude_code and claude_omlx target profiles
    - Illustrative skill examples (not yet defined as canonical templates):
      - .claude/governance/validate-design.md: Schema validation before T03 prompt creation
      - .claude/testing/generate-pytest.md: Automated pytest generation from T04 documentation
      - .claude/validation/coupling-check.md: Verify iteration synchronization in coupled documents
      - .claude/audit/protocol-compliance.md: Check generated code against protocol requirements
  - P00.19 Context Optimization
    - Tactical Domain context file location:
      - AEL profile: ai/context.md (checked into git)
      - Claude Code profiles: CLAUDE.md at project root (checked into git)
    - Local context file: Personal preferences (.gitignore'd)
      - Claude Code profiles: CLAUDE.local.md at project root
    - AEL auto-load: worker recipe reads project_root/ai/context.md at task start if present
    - Content specification:
      - Project overview and technology stack
      - Common bash commands (build, test, lint)
      - Code style guidelines
      - Repository conventions (branch naming, commit patterns)
      - Governance framework location: ai/governance.md
      - Design documents location: ai/workspace/design/
      - Protocol compliance requirements summary
      - Platform-specific tooling and dependencies
    - Token efficiency: Externalize stable context from T03 prompts
    - Team coordination: Review context file changes during git commits
    - Auto-generation: Strategic Domain creates initial context file during project initialization or when absent
    - Implementation: Context file name and update mechanism defined in implementation profile (ai/profiles/)
  - P00.20 Task Register
    - Location: `ai/task.md` (project root, git-tracked)
    - Purpose: single-file index of open work items, cross-referencing document-class UUIDs (issue, change, prompt)
    - Exempt from P00.10 naming convention and P00.14 lifecycle management: no UUID, no master suffix, no closed/ archival
    - Row removed in place once the referenced document triple's closed/ records the outcome; git history preserves prior state
    - Strategic Domain: adds a row when a T06/T07/T03 triple opens; removes the row when the triple closes
    - Framework ships a skeleton `ai/task.md`; `bin/propagate.sh` excludes it from overwrite and seeds it only when absent in the target, per `context.md` treatment

[Return to Table of Contents](<#table of contents>)

## P01 Trace

  - P01.1 Traceability Matrix Management
    - Strategic Domain: Maintains traceability matrix in ai/workspace/trace/trace-traceability-matrix-master.md
    - Strategic Domain: Updates matrix when requirements, designs, code, or tests modified
  - P01.2 Traceability Verification
    - Strategic Domain: Verifies bidirectional links exist: requirements ↔ design ↔ code ↔ test (navigable forward and backward)
    - Strategic Domain: Identifies and resolves traceability gaps
    - Strategic Domain: Generates traceability reports on demand
  - P01.3 Requirements Traceability
    - Strategic Domain: Maintains traceability matrix linking requirements through implementation
    - Strategic Domain: Updates matrix when designs, code, or tests modified
    - Strategic Domain: Ensures orphaned requirements or implementations identified
  - P01.4 Traceability Matrix Structure
    - Strategic Domain: Maintains single traceability matrix in ai/workspace/trace/trace-traceability-matrix-master.md
    - Required sections:
      - Functional Requirements: ID, Requirement, Design, Code, Test, Status
      - Non-Functional Requirements: ID, Requirement, Target, Design, Code, Test, Status
      - Component Mapping: Component → Requirements → Design → Source → Test
      - Design Document Cross-Reference: Design Doc → Requirements → Code → Tests
      - Test Coverage: Test File → Requirements Verified → Code Coverage
      - Bidirectional Navigation: Forward (Req→Design→Code→Test) and Backward (Test→Code→Design→Req)
    - Strategic Domain: Updates matrix when requirements, designs, code, or tests change

[Return to Table of Contents](<#table of contents>)

## P02 Audit


  - P02.1 Purpose
    - Systematic verification of ongoing governance compliance
    - Detection of protocol drift, documentation gaps, and process deviations
    - Establishment of quality baseline for continuous improvement
  - P02.2 Audit Triggers
    - Milestone-based: Upon completion of major development phases
    - Human-requested: Ad-hoc audits when compliance concerns arise
    - Baseline: After initial code generation before production deployment
    - Mode selection: Human-requested audits resolve to one of two modes — strategic (Strategic Domain) or tactical (AEL audit loop) — per P02.9
  - P02.3 Audit Scope
    - Protocol compliance: All protocols
    - Document compliance: Naming, formatting, cross-linking, version histories
    - Code quality: Thread safety, error handling, documentation standards
    - Naming consistency: Generated code element names match name registry (modules, classes, functions, constants)
    - Traceability: Requirement ↔ design ↔ code ↔ test linkages
    - Configuration management: Code vs. baseline verification
  - P02.4 Audit Procedure
    - P02.4.1 Strategic-led (frontier reasoning)
      - Strategic Domain: Conducts systematic review of source code against governance requirements
      - Strategic Domain: Documents findings with severity classification (critical, high, medium, low)
      - Strategic Domain: Provides evidence for each finding (file paths, line numbers, specific violations)
      - Strategic Domain: Calculates compliance metrics (percentage, deficiency counts by severity)
    - P02.4.2 Tactical-led (AEL audit loop)
      - Strategic Domain: Prepares audit-uml.md and audit-index.md in the state directory; obtains human approval
      - Strategic Domain: Authors a T03 audit prompt and presents the AEL command (P13.3)
      - AEL: Runs a read-only worker/reviewer loop, one audit-index.md item per iteration, accumulating findings in audit-report.md
      - Recipe selection is automatic on presence of audit-index.md in the state directory; operational detail in ai/doc/guide-audit-loop.md
      - Outcome: findings consolidated into the audit report deliverable (P02.5)
  - P02.5 Audit Deliverables
    - Strategic Domain: Creates audit report following naming format: audit-<uuid>-<audit name>.md
    - Strategic Domain: Stores audit reports in ai/workspace/audit/ folder
    - Audit report template: ai/templates/T08-audit.md (mode field records strategic or tactical)
    - Tactical-led runs: audit-report.md is archived to audit-<uuid>-<name>.md on SHIP automatically (see guide-audit-loop.md §7)
    - Audit report structure:
    - Executive summary with compliance status and critical issue count
    - Protocol-by-protocol compliance assessment
    - Document compliance review
    - Code quality assessment
    - Critical issues section with detailed findings
    - High/medium/low priority issues sections
    - Compliance summary with metrics
    - Recommendations for remediation
    - Positive findings (strengths identification)
  - P02.6 Remediation Process
    - Strategic Domain: Converts critical and high-priority audit findings to issue documents via P03
    - Strategic Domain: References source code audit report in issue documents
    - Strategic Domain: Issue resolution follows standard P03 → P04 → implementation workflow
    - Strategic Domain: Tracks remediation progress in audit report updates
  - P02.7 Audit Trail
    - Strategic Domain: Maintains chronological audit history
    - Strategic Domain: Links related audits (initial → follow-up → closure)
    - Strategic Domain: Preserves audit reports for process improvement analysis
  - P02.8 Audit Closure
    - P02.8.1 Closure Criteria
      - All critical findings fully resolved
      - All high-priority findings addressed or mitigated with documented acceptance
      - Completion documented in audit report
      - Human approval obtained
    - P02.8.2 Closure Process
      - Strategic Domain: Conducts follow-up audit after remediation completed, when remediation changed source code
      - Human: May waive the follow-up audit when remediation changed documents only; waiver recorded in the audit report closure block
      - Strategic Domain: Verifies all closure criteria satisfied
      - Strategic Domain: Documents closure status with final compliance metrics
      - Strategic Domain: Records closure date and approver
      - Human: Reviews closure documentation
      - Human: Approves audit closure and authorizes proceeding to next phase
    - P02.8.3 Post-Closure Archival
      - Strategic Domain: Moves closed audit report to ai/workspace/audit/closed/
      - Strategic Domain: Updates audit traceability links in master traceability matrix
      - Strategic Domain: Preserves read-only access for future reference
    - P02.8.4 Reopening Closed Audits
      - Prohibited: Closed audits are immutable
      - New findings: Create new audit with reference to closed audit
      - Follow-up verification: Covered by new audit cycle

  - P02.9 Audit Modes
    - Two audit modes satisfy this protocol; the human selects by trigger phrase (primer §4.1)
    - P02.9.1 Strategic audit
      - Trigger: "conduct a strategic audit"
      - Actor: Strategic Domain (frontier reasoning)
      - Method: Reads source via MCP and reasons holistically; authors the audit report directly
      - Best for: architecture, protocol and name-registry conformance, traceability, cross-cutting judgement
      - Bound: Tactical Domain context budget does not apply; large codebases may exceed a single review pass
    - P02.9.2 Tactical audit
      - Trigger: "conduct a tactical audit"
      - Actor: AEL audit loop (local model)
      - Method: Item-by-item per audit-index.md, one per iteration, read-only; findings accumulate in audit-report.md
      - Best for: exhaustive per-function coverage and unattended runtime (--duration)
      - Flag: orchestrator selects audit recipes automatically when audit-index.md is present in the state directory
      - Procedure: ai/doc/guide-audit-loop.md
    - Both modes terminate at audit-<uuid>-<name>.md (T08) and feed remediation via P02.6 (P03)

[Return to Table of Contents](<#table of contents>)

## P03 Issue

  - P03.1 Issue creation from test results
    - Strategic Domain: Reads template from ai/templates/T06-issue.md
    - Strategic Domain: Before specifying any target file_path in a T06 issue, reads the project entry point configuration (pyproject.toml [project.scripts] or equivalent) and confirms the named file is in the deployment path
    - Strategic Domain: Creates issue documents from errors reported in ai/workspace/test/result using T06 template and saves them in folder ai/workspace/issues
  - P03.2 Reserved for future use
    - Strategic Domain: Reserved for future use
  - P03.3 Debug workflow
    - Tactical Domain: Debugs issues submitted from Tactical Domain and returns change proposal to Strategic Domain
  - P03.4 Issue updates
    - Strategic Domain: Reads template from ai/templates/T06-issue.md
    - Strategic Domain: Updates issue documents from bugs using T06 template and saves them in folder ai/workspace/issues
  - P03.5 Non-Conformance Reporting
    - Strategic Domain: Documents instances where generated code deviates from design specifications
    - Strategic Domain: Records deviation type, severity, affected components
    - Strategic Domain: Tracks non-conformance trends for process improvement
  - P03.6 Post-Implementation Review
    - Strategic Domain: Evaluates code generation effectiveness after issue resolution
    - Strategic Domain: Documents lessons learned
    - Strategic Domain: Provides protocol improvement recommendations for human review (protocols immutable, human-modified only)
  - P03.7 Issue-Change Coupling
    - Strategic Domain: Updates issue document with change_ref field (UUID) when change created
    - Strategic Domain: Sets issue status to "resolved" when corresponding change status becomes "implemented"
    - Strategic Domain: Verifies bidirectional linkage exists: issue.change_ref ↔ change.source.reference
    - Strategic Domain: Prevents issue closure without corresponding change document for source code issues
    - Strategic Domain: issue.iteration must equal change.iteration throughout cycle
    - Strategic Domain: When debugging requires new iteration, both documents increment together
    - Strategic Domain: Git commit captures synchronized iteration state
    - Strategic Domain: Validates iteration match before proceeding
    - Note: One-to-one coupling does not prevent modification of paired issue/change documents during debugging iterations

[Return to Table of Contents](<#table of contents>)

## P04 Change

  - P04.1 Change document creation
    - Strategic Domain: Reads template from ai/templates/T07-change.md
    - Strategic Domain: Creates change documents exclusively from issue documents using T07 template and saves them in folder ai/workspace/change
    - Strategic Domain: For human-requested source code changes, first creates issue document via P03, then creates change document referencing that issue
    - Strategic Domain: For enhancement or requirement change requests, creates issue document via P03 with type `enhancement` or `requirement_change` and origin `requirement_change`, then creates change document referencing that issue
    - Exception: Non-source-code changes (ai/workspace/ documents per 1.4.10) may be implemented directly after human approval without issue/change documents
    - Exception: Initial implementation of source code from an approved design document does not require issue or change documents. The forward path is: approved design → T03 prompt → Tactical Domain execution → review. Issue and change documents are required only when execution fails (AEL BLOCKED) or tests fail.
    - Cross-reference: P13.2 — T03 prompt_info.source_ref distinguishes design-sourced prompts (this exception) from change-sourced prompts; coupled_docs is required only for the latter.
  - P04.2 Document coupling
    - Strategic Domain: Ensures one-to-one coupling between issue and change documents
    - Strategic Domain: Every source code change document must reference exactly one source issue document via UUID
    - Strategic Domain: Every resolved source code issue must reference exactly one change document via UUID
    - Strategic Domain: Prohibits multiple change documents addressing same issue or multiple issues addressed by same change
    - Strategic Domain: Change references source issue UUID in coupled_docs.issue_ref field
    - Strategic Domain: Change iteration number matches source issue iteration number at creation
    - Strategic Domain: When issue iteration increments, corresponding change iteration increments synchronously
    - Strategic Domain: Verifies iteration synchronization before workflow transitions
  - P04.3 Design document updates
    - Strategic Domain: Updates all relevant design documents after implementation
  - P04.4 Design document cross-linking
    - Strategic Domain: Insures all design document updates contain change references and links to their source change document
  - P04.5 Change Review
    - Strategic Domain: Performs impact analysis before change approval
    - Strategic Domain: Evaluates effects on dependent components, interfaces, data structures
    - Strategic Domain: Documents impact analysis results in change document
  - P04.6 Requirements Change Management
    - Strategic Domain: Links requirement changes to affected design elements
    - Strategic Domain: Performs impact analysis when requirements change
    - Strategic Domain: Updates requirement traceability matrix after changes
  - P04.7 Maintenance Classification
    - Strategic Domain: Categorizes changes: corrective, adaptive, perfective, preventive
    - Strategic Domain: Records classification in change document metadata
    - Strategic Domain: Tracks change type distribution for process metrics
  - P04.8 Checkpoint Strategy
    - Tactical Domain: Creates automatic checkpoint per file modification during code generation
    - Tactical Domain: Checkpoint captures pre-modification state for rewind capability
    - Tactical Domain: Failed verifications trigger rewind to checkpoint before modification
    - Strategic Domain: Reviews checkpoint log after code generation completion
    - Git commit occurs at iteration boundaries after human approval
    - Checkpoint scope: Session-local, ephemeral
    - Human oversight: Maintained through iteration approval gates
    - Rollback efficiency: Eliminates manual file restoration during debug cycles
  - P04.9 Change Impact Analysis
    - Strategic Domain: Evaluates change effects on system integrity, performance, security
    - Strategic Domain: Identifies all components requiring modification
    - Strategic Domain: Documents cascading effects in change document
  - P04.10 Maintenance Documentation
    - Strategic Domain: Updates all affected documentation when changes implemented
    - Strategic Domain: Maintains documentation currency with code state
    - Strategic Domain: Cross-links updated documents to source change document
  - P04.11 Documentation domain
    - Change documentation is only required for source code changes in src/. Change documentation to documents in the ai/workspace/ is not required and can be made directly after human approval.
  - P04.12 Trivial Change Exemption
    - Definitions:
      - Trivial: the outcome is fully predictable before implementation; no analysis, experimentation, or design judgement is required to determine the correct solution.
      - Surgical: confined to a single, well-bounded location in the codebase; does not disturb surrounding logic, interfaces, or dependent components.
    - A qualifying change must be both trivial and surgical simultaneously. Either quality alone is insufficient.
    - When all five criteria below are satisfied, Strategic Domain may implement directly after human approval — no T06, T07, T03, or AEL required. Git commit history is the sole audit record for exempt changes.
    - Criteria (all must hold simultaneously):
      - (1) Confined to a single function or entry point
      - (2) Net line delta ≤20 lines
      - (3) No interface changes (signatures, contracts, public APIs)
      - (4) Unambiguous with no design decisions required
      - (5) Human approval obtained before implementation
    - If any criterion fails, standard T06 → T07 → T03 → AEL workflow applies.

[Return to Table of Contents](<#table of contents>)

## P10 Project Initialization (Execute once)

  - P10.1 Project folders
    - Create (see P10.6 Project folder structure)
  - P10.2 GitHub documents
    - Create .gitignore in project root:
    - Offer to keep the ai/ framework out of a fork's GitHub history entirely.
```
# Python
__pycache__/
*.pyc
.pytest_cache/
dist/
build/
*.egg-info/

# Virtual environments
venv/
.venv/

# Distribution / packaging
dist/
build/
*.egg-info/

# MacOS
.DS_Store
**/.DS_Store
.zsh_history

# Logs
*.log
**/*.log

# Obsidian
.obsidian/
*.canvas

# AI framework (consolidated under ai/)
# Owned-project (tracked) mode below: the framework lives in ai/ and is
# version-controlled; only transient state and generated output are ignored.
# Third-party fork (isolation) mode: replace this section with two lines —
#   /ai/
#   /CLAUDE.md
# — to keep the framework out of the fork's history entirely.
# else
deprecated/
ai/workspace/report/
ai/workspace/ai/
ai/workspace/proposal/
ai/workspace/proposal/closed/
ai/state/
ai/dashboard-alerts.md

# Tactical Domain
CLAUDE.local.md
.claude/settings.local.json
.claude/commands/

# other
10000
test.txt
**/tmp
*.pdf

```

  - P10.3 README
    - Create initial skeleton 'README.md' document in each folder
  - P10.4 Initialize downstream project
    - Human: Run `bin/propagate.sh <project-root>` from the framework repository root to push `ai/` into the downstream project directory
    - Human: Rename the target directory to `<project name>` if not already named
    - No recipe path configuration required. Orchestrator resolves recipes relative to its own location.
  - P10.5 Traceability Matrix
     - Create skeleton trace-traceability-matrix-master.md in ai/workspace/trace/
  - P10.6 Project folder structure
    - Note: This structure applies to projects using the framework, not to the LLM-Governance-and-Orchestration repository itself
    - The governance framework repository contains only ai/, doc/, and templates/ directories
    - ai/ holds framework files plus only the project files declared in the layout below (context.md, task.md, ael/config.yaml, state/, logs/, dashboard-alerts.md, workspace/)
    - Any other project file belongs outside ai/; bin/propagate.sh relocates such files, and retired framework files, to ai-local/ and logs them in ai-local/RELOCATED.md
    - bin/propagate.sh never deletes a file; a locally edited framework file is copied to ai-local/ before it is overwritten; the human deletes relocated files after review
    - Layout
```
    └── <project name>/
        ├── ai/                       # Framework — operational rules + execution space
        │   ├── governance.md
        │   ├── context.md            # AEL profile only — Tactical Domain context (team shared)
        │   ├── task.md                # open-work register (git-tracked)
        │   ├── state/                # AEL loop state (ephemeral, excluded from git)
        │   ├── logs/                 # AEL run-log archive (log_archive_dir)
        │   ├── dashboard-alerts.md   # govwatch output (excluded from git)
        │   └── workspace/            # Framework execution space
        │       ├── report/            # Reports (excluded from git)
        │       │   └── closed/
        │       ├── requirements/
        │       │   └── closed/
        │       ├── design/
        │       ├── change/
        │       │   └── closed/
        │       ├── issues/
        │       │   └── closed/
        │       ├── proposal/         # (excluded from git)
        │       │   └── closed/
        │       ├── prompt/
        │       │   └── closed/
        │       ├── trace/
        │       ├── audit/
        │       │   └── closed/
        │       ├── test/
        │       │   ├── closed/
        │       │   └── result/
        │       │       └── closed/
        ├── ai-local/                 # Project files relocated from ai/ by propagation (see RELOCATED.md)
        ├── .claude/                  # Claude Code profiles only; most contents git-tracked (see P10.2 excludes)
        │   ├── settings.json         # Team-shared, git-tracked
        │   ├── hooks/                # Hook scripts (e.g. run-tests.sh), git-tracked
        │   └── validation/           # Skill docs provisioned from ai/skills/, git-tracked
        ├── CLAUDE.md                 # Claude Code profiles only (team shared)
        ├── CLAUDE.local.md           # Claude Code profiles only (excluded from git)
        ├── venv/                     # Python virtual environment (excluded from git)
        ├── dist/                     # Python build artefacts (excluded from git)
        ├── docs/                     # Technical Documents
        ├── bin/                      # Project-scoped integration scripts
        ├── tests/                    # Test files (root level)
        ├── src/                      # Source code
        └── deprecated/               # Archive (excluded from git)
```

  - P10.7 Python Virtual Environment Setup (Human executes)
    - Human: virtual environment setup instructions for when project initialization completes
```
# Create virtual environment in project root
cd <project name>

python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install project dependencies
pip install -e .[dev]

# Verify installation
pip list
```
  - P10.8 Implementation Profile Setup (Human executes)
    - Human: Select implementation profile from ai/profiles/
    - Human: Create tactical context file at project root per selected profile
    - **Claude profile** (Tactical Domain = Claude Code):
      - Install Claude Code: `npm install -g @anthropic-ai/claude-code`
      - Ensure Anthropic API key is configured
      - Create `CLAUDE.md` at project root with project context
      - Create `.claude/` directory structure per P10.6
      - Provision mandatory skill: follow ai/skills/validation/run-tests.md §2.0 to install `.claude/hooks/run-tests.sh` and merge its PostToolUse block into `.claude/settings.json` (P00.18)
      - Reference: [claude-code.md](profiles/claude-code.md)
    - **claude-omlx profile** (Tactical Domain = Claude Code CLI → oMLX → Devstral):
      - Ensure oMLX is running on `http://127.0.0.1:8000` with Devstral loaded
      - Install Claude Code: `npm install -g @anthropic-ai/claude-code`
      - No Anthropic API key required
      - Create `CLAUDE.md` at project root with project context
      - Create `.claude/` directory structure per P10.6
      - Provision mandatory skill: follow ai/skills/validation/run-tests.md §2.0 to install `.claude/hooks/run-tests.sh` and merge its PostToolUse block into `.claude/settings.json` (P00.18)
      - Reference: [claude-omlx.md](profiles/claude-omlx.md)
    - **ael-mcp setup (Claude Desktop profile, optional)**:
      - Clone: `git clone https://github.com/William12556/ael-mcp`
      - Verify `mcp` package: `python3 -m pip show mcp`; install if absent: `pip3 install mcp`
      - Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ael-mcp": {
      "command": "/path/to/python3",
      "args": ["/path/to/ael-mcp/server.py"]
    }
  }
}
```
      - Replace `/path/to/python3` with the interpreter that has `mcp` installed
      - Restart Claude Desktop to load the new MCP server
      - Reference: P00.11
    - **AEL setup (both profiles)**:
      - Install AEL dependencies: `pip install -r ai/ael/requirements.txt`
      - Configure `ai/ael/config.yaml` with inference endpoint and MCP server definitions
      - `ai/ael/src/orchestrator.py` resolves context-window size at startup (config.yaml override → live oMLX query → per-model config.yaml override → unknown) and writes context-budget.md to the state directory automatically; no separate script to run
      - Recipe location: `<project name>/ai/ael/recipes/`
      - Reference: P00.11, P10.4

  - P10.9 Python documents
    - Create pyproject.toml in project root:
```
[project]
name = "\<project-name\>"
version = "0.1.0"
description = "<project description>"
authors = [{name = "<author name>"}]
license = {text = "MIT"}
requires-python = ">=3.9"
dependencies = [
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

[Return to Table of Contents](<#table of contents>)

## P11 Requirements

  - P11.1 Purpose
    - Systematic requirements capture and validation before design
    - Establishes baseline for design decomposition and traceability
  - P11.2 Requirements Capture
    - Strategic Domain: Reads template from ai/templates/T01-requirements.md
    - Strategic Domain: Assists human through requirements elicitation
    - Strategic Domain: Prompts for functional, non-functional, architectural requirements
    - Strategic Domain: Validates completeness, clarity, testability
    - Strategic Domain: Identifies conflicts and dependencies
    - Strategic Domain: Creates requirements-<project>-master.md using T01 template
    - Strategic Domain: Saves in ai/workspace/requirements/
  - P11.3 Requirements Validation
    - Strategic Domain: Verifies each requirement has objective acceptance criteria
    - Strategic Domain: Ensures requirements are testable and unambiguous
    - Strategic Domain: Documents validation results in validation section
    - Human: Reviews and approves requirements baseline
  - P11.4 Requirements Baseline
    - Human: Approves requirements document
    - Strategic Domain: Establishes baseline for design phase
    - Strategic Domain: Initializes traceability matrix with requirements
  - P11.5 Requirements Lifecycle
    - Active: ai/workspace/requirements/requirements-<project>-master.md
    - Closed: ai/workspace/requirements/closed/ after human acceptance
    - Reopening: Move from closed/ to active, proceed with change workflow
    - No iteration numbering - git history tracks all changes
  - P11.6 Requirements Change Management
    - Changes trigger P04 Change workflow
    - Strategic Domain: Performs impact analysis across design/code/test
    - Strategic Domain: Updates traceability matrix
    - Human: Approves changes
  - P11.7 Framework Development Requirements
    - Scope: requirements for extending LLM-G&O itself, held in dev/requirements/
    - Format: prose with FR/NFR/CON tables; the T01 YAML template is not used
    - T01 applies to downstream project requirements, where a local model consumes them

[Return to Table of Contents](<#table of contents>)
## P12 Design

  - P12.1 Tier 1: System Architecture
    - Strategic Domain: Reads template from ai/templates/T02-design.md
    - Strategic Domain: Creates design-\<project\>-master.md from human requirements using T02 template
    - Strategic Domain: Defines system architecture, technology stack, cross-cutting concerns
    - Strategic Domain: Includes system-level Mermaid diagrams (architecture, component interaction, state machine, data flow)
    - Strategic Domain: Clearly designates document as master design within document content
    - Strategic Domain: Initialises design-\<project\>-name_registry-master.md; populates package name, top-level module names, and Mermaid class diagram skeleton
  - P12.2 Tier 1 Review
    - Strategic Domain: Presents master design document for human approval
    - Strategic Domain: Documents review findings, required changes, approval decision
    - Strategic Domain: Proceeds with Tier 2 decomposition only after approval recorded
  - P12.3 Tier 2: Domain Decomposition
    - Strategic Domain: Reads template from ai/templates/T02-design.md
    - Strategic Domain: Decomposes master into functional domains using T02 template
    - Strategic Domain: Creates design-\<uuid\>-domain_\<name\>.md for each domain
    - Strategic Domain: Each domain defines: boundaries, interfaces, domain patterns, responsibilities
    - Strategic Domain: Includes domain-level Mermaid diagrams as needed
    - Strategic Domain: Extends name registry with domain-level module names and key class names per domain
  - P12.4 Tier 2 Review
    - Strategic Domain: Presents domain design documents for human approval
    - Strategic Domain: Documents review findings, required changes, approval decision
    - Strategic Domain: Proceeds with Tier 3 decomposition only after approval recorded
  - P12.5 Tier 3: Component Decomposition
    - Strategic Domain: Reads template from ai/templates/T02-design.md
    - Strategic Domain: Decomposes each domain into components using T02 template
    - Strategic Domain: Creates design-\<uuid\>-component_\<domain\>_\<name\>.md for each component
    - Strategic Domain: Each component defines: implementation details, interfaces, processing logic, error handling
    - Strategic Domain: Includes component-level Mermaid diagrams as needed
    - Strategic Domain: Finalises name registry with all functions, constants, and complete signatures; registry is canonical before T03 creation
  - P12.6 Tier 3 Review
    - Strategic Domain: Presents component design documents for human approval
    - Strategic Domain: Documents review findings, required changes, approval decision
    - Strategic Domain: Proceeds with T03 prompt creation only after approval recorded
  - P12.7 Design Hierarchy Naming Convention
    - Tier 1: design-\<project\>-master.md (single master document)
    - Tier 2: design-\<uuid\>-domain_\<name\>.md (one per domain)
    - Tier 3: design-\<uuid\>-component_\<domain\>_\<name\>.md
    - Registry: design-\<project\>-name_registry-master.md (singleton, maintained across all tiers)
  - P12.8 Exploration Phase
    - Tactical Domain: Supports exploratory code generation without formal design hierarchy
    - Use case: Proof-of-concept development, technology validation, prototype iteration
    - Documentation: Lightweight T03 prompts without coupled design documents
    - Permission scope: Limited to experimental/ directory tree
    - Testing: Informal validation, no formal test documentation required
    - Transition: Successful prototypes promote to formal design workflow
    - Human decision: Determines when exploration transitions to formal development
    - Audit exemption: Exploration work excluded from P02 compliance audits
    - Git workflow: Feature branches for exploration, merge on formalization
  - P12.9 Cross-Linking Requirements
    - Strategic Domain: Master lists all Tier 2 domain document references
    - Strategic Domain: Each domain lists: master parent reference, all Tier 3 component children references
    - Strategic Domain: Each component lists: domain parent reference, generated code file paths
    - Strategic Domain: Uses Obsidian internal link syntax for all cross-references
  - P12.10 Context Window Constraints
    - Strategic Domain: Ensures design documents at each tier do not exceed Tactical Domain context window
    - Strategic Domain: T03 prompts embed only Tier 3 component designs relevant to code generation task
  - P12.11 Design Verification
    - Strategic Domain: Validates design completeness at each tier before proceeding to next tier
    - Strategic Domain: Verifies all functional requirements have corresponding design coverage
    - Strategic Domain: Confirms all non-functional requirements addressed across design hierarchy
  - P12.12 Requirements Traceability
    - Strategic Domain: Assigns unique identifier to each functional and non-functional requirement
    - Strategic Domain: Maps requirements through design tiers: requirement → master → domain → component
    - Strategic Domain: Maintains bidirectional links in traceability matrix
  - P12.13 Requirements Validation
    - Strategic Domain: Verifies design hierarchy satisfies all stated requirements before baseline
    - Strategic Domain: Documents validation results in master design document
    - Strategic Domain: Resolves discrepancies before proceeding to code generation
  - P12.14 Document Storage
    - Strategic Domain: Saves all design documents in ai/workspace/design
  - P12.15 Visual Documentation Requirements
    - Strategic Domain: Embeds Mermaid diagrams directly within design documents at all tiers
    - Tier 1 Master: System architecture, overall component relationships, system-level state machines
    - Tier 2 Domain: Domain boundaries, domain internal structure, domain interfaces
    - Tier 3 Component: Component-specific flows, detailed state machines, data transformations
    - Strategic Domain: All diagrams use Mermaid syntax within markdown code blocks
    - Strategic Domain: Each diagram includes: purpose statement, legend, cross-references
    - Strategic Domain: Updates diagrams when design modifications require visual clarification
    - Strategic Domain: Maintains diagram consistency with textual design specifications
  - P12.16 Name Registry
    - Strategic Domain: Creates design-\<project\>-name_registry-master.md at Tier 1 design phase
    - Strategic Domain: Stores registry in ai/workspace/design/
    - Registry document contains two sections:
      - Mermaid class diagram: visual representation of all program elements and relationships (human comprehension)
      - YAML element table: machine-readable canonical name list (T03 prompt inclusion)
    - YAML element table structure:
      - naming_conventions: package naming rules, module casing, class casing, function casing, constant casing
      - packages: name, path
      - modules: name, import_path, package
      - classes: name, module, base_classes
      - functions: name, module, signature
      - constants: name, module, type
    - Strategic Domain: Populates incrementally — packages and modules at Tier 1, class names at Tier 2, functions and constants with full signatures at Tier 3
    - Strategic Domain: Registry must be complete and approved before first T03 prompt creation
    - Strategic Domain: Updates registry when design changes affect named elements
    - Strategic Domain: Cross-links registry document to all design documents that define its elements

[Return to Table of Contents](<#table of contents>)

## P13 Prompt

  - P13.1 Purpose
    - Manage creation and lifecycle of T03 prompt documents
    - Facilitate Strategic Domain → Tactical Domain code generation communication
  - P13.2 Prompt Creation
    - Prompt documents are always Tactical Domain specific; prompt_info.target_profile declares which profile (ael, claude_code, or claude_omlx) a given prompt targets.
    - Strategic Domain: Reads template from ai/templates/T03-prompt.md
    - Strategic Domain: Creates prompt documents from design documents (initial implementation, P04.1 exception) or from change documents (corrective/enhancement cycle) using T03 template
    - Strategic Domain: Saves prompts with naming format prompt-<uuid>-<name>.md in ai/workspace/prompt/
    - Strategic Domain: UUID assignment follows workflow initiation pattern:
    - First document created in workflow (Issue OR Change) generates new 8-character UUID
    - All subsequently coupled documents (Change, Prompt, Test, Result) inherit that UUID
    - UUID propagates through entire document lifecycle maintaining referential integrity
    - Strategic Domain: Rewrites prompt documents in place when revisions required
    - Strategic Domain: Embeds complete design specifications and schema within prompt documents
    - Strategic Domain: Ensures prompt documents are self-contained requiring no external file references
    - Strategic Domain: The following tactical_brief and context-budget directives apply only when prompt_info.target_profile is ael; tactical_brief is not consumed by claude_code or claude_omlx profiles and may be omitted for those
    - Strategic Domain: Populates tactical_brief field with a concise prose AEL task payload (~200-400 tokens); brief contains only: file(s) to modify, hard constraints, implementation steps, deliverable path(s), success criteria; all governance metadata omitted from brief
    - Strategic Domain: Calls omlx_model_status (mcp_omlx) for the configured model before authoring tactical_brief; a null or missing settings.max_context_window is treated as unresolved and the operator is warned, consistent with the resolver's own unknown-window handling
    - Strategic Domain: Reads context-budget.md (written automatically by the orchestrator at AEL runtime) and adjusts brief size to fit within available context headroom
    - Strategic Domain: Verifies tactical_brief field is non-empty before issuing AEL command; an empty or placeholder brief causes orchestrator fallback to full raw document, inflating context and risking saturation
    - Strategic Domain: Ensures tactical_brief is authored in a ```yaml fenced block with tactical_brief as the root key; the orchestrator scans only ```yaml blocks — plain text or non-YAML fenced blocks are not detected and cause fallback to raw document; when using per-section YAML blocks, §8.0 must be a dedicated ```yaml block (not ```text) with tactical_brief: as the sole root key
    - Strategic Domain: config.yaml `loop.max_iterations` controls the number of outer Ralph Loop cycles (worker + reviewer pass pairs); `loop.phase_max_iterations` controls the number of inner tool-call iterations per phase; these are distinct values and must not be conflated in T03 prompt notes
    - Strategic Domain: AEL end is logged as `INFO AEL end rc=N` in the .LOG file on all exits including unexpected termination; absence of this line in a log indicates unclean exit (signal, crash, or resource failure); log review should check for this line before concluding outcome
    - Strategic Domain: Before specifying any target file path in a T03 prompt, reads the project entry point configuration (pyproject.toml [project.scripts] or equivalent) and confirms the named file is in the deployment path
    - Strategic Domain: Embeds element_registry field in T03 prompt from name registry master, scoped to elements relevant to the code generation task
    - Strategic Domain: When source_ref references a change document (change-<uuid>), prompt references that change's UUID in coupled_docs.change_ref field, prompt iteration number matches source change iteration number, and synchronization is maintained through debug cycles; verifies coupling before prompt creation
    - Strategic Domain: When source_ref references a design document (design-<uuid>, initial implementation per P04.1), coupled_docs is omitted; no change document exists to couple to
    - GitHub version control maintains complete revision history
  - P13.3 Human Handoff
    - Strategic Domain: Verifies tactical context file exists at project root before providing command
    - Strategic Domain: If context file absent, generates initial context file with project context
    - Strategic Domain: Generated context file requires human approval before proceeding
    - Context file name: Defined in implementation profile (ai/profiles/)
    - Strategic Domain: After human approval of T03 prompt, presents Tactical Domain execution options; human selects preferred option:

    - **Option A — Human executes (all profiles):**
      - Strategic Domain: Provides ready-to-execute AEL command in conversation
      - Human: Executes command from project root directory
      - AEL exits with SHIP (proceed to review) or BLOCKED (create T06 Issue)
      - Human: Notifies Strategic Domain of AEL outcome
      - Example command:

```bash
python ai/ael/src/orchestrator.py --mode loop \
  --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

    - **Option B — Strategic Domain launches via ael-mcp (Claude Desktop profile only):**
      - Human: Chooses to delegate AEL launch to Strategic Domain
      - Strategic Domain: Calls `start_ael` with `project_dir` and T03 prompt path as `task` parameter
      - AEL runs detached; Strategic Domain returns `run_id`, PID, and log path
      - Human: Requests status check when ready
      - Strategic Domain: Calls `ael_status`; reports SHIP or BLOCKED outcome
      - On BLOCKED: Strategic Domain reads `RALPH-BLOCKED.md` and creates T06 Issue per P03

    - **Option C — Claude Code manual invocation (claude_code/claude_omlx profiles):**
      - Human: Opens Claude Code in the project root
      - Human: Issues the invocation instruction, substituting the T03 prompt path
      - Reference: ai/profiles/claude-code.md §5.0 for full procedure
      - Example instruction:


```text
Implement ai/workspace/prompt/prompt-<uuid>-<name>.md and close the prompt T-Doc
when finished. Leave the issue and change T-Docs active pending test results.
Then, once finished, write a report of what you have done in
ai/workspace/report/report-<uuid>-<name>.md.
```

  - P13.4 Wildcard Permissions
    - Tactical Domain: Supports wildcard patterns in permission grants for batch operations
    - Permission scope: src/**/*.py enables modifications across source tree
    - Validation: PreToolUse hooks verify modifications within approved scope
    - Audit trail: All wildcard-permitted modifications logged per-file
    - Human approval: Wildcard grants require explicit approval in T03 prompt
    - Rollback capability: Checkpoint system preserves state before each modification
    - Use cases: Refactoring, formatting, batch updates, code migrations
    - Constraints: Wildcard permissions limited to src/ directory tree
    - Exclusions: Configuration files, test fixtures require individual approval
  - P13.5 Prompt Revision
    - Strategic Domain: Rewrites existing prompt documents when changes needed
    - Strategic Domain: Documents revision rationale in prompt version_history section
    - GitHub commits provide complete change tracking and rollback capability

[Return to Table of Contents](<#table of contents>)

## P14 Quality

  - P14.1 Purpose
  - P14.2 Code Validation
    - Strategic Domain: Verifies generated code implements all design requirements
    - Strategic Domain: Validates against design specifications, interface contracts, data schemas
    - Strategic Domain: Documents validation results, discrepancies found
  - P14.3 Automated Audits
    - Tactical Domain: Stop hook triggers automated compliance audit after code generation
    - Audit verification: Protocol compliance, naming conventions, traceability links
    - Compliance report: Generated in session metadata for Strategic Domain review
    - Critical violations: Halt workflow, require human intervention before commit
    - Minor violations: Logged as warnings, accumulated for periodic review
    - Audit scope: Document coupling integrity, iteration synchronization, file organization
    - Human review: Strategic Domain evaluates audit findings before approving iteration
    - Audit integration: Complements P02 milestone audits with continuous checking
  - P14.7 Hook-Based Auditing
    - Tactical Domain: Lifecycle hooks enable automated audit event capture
    - PreToolUse hook: Records design context, requirements traceability before generation
    - PostToolUse hook: Captures test results, validation outcomes after modification
    - Stop hook: Logs session metrics, checkpoint usage, validation summary
    - Audit trail: Stored in session metadata for post-execution review
    - Hook configuration: Defined in <skills_dir>/audit/
    - Automated compliance: Reduces manual audit overhead for repetitive checks
    - Human review: Session metadata reviewed by Strategic Domain after completion
    - Audit scope: File-level modifications, iteration-level decisions, session-level metrics
    - Integration: Audit events linked to git commits via timestamp correlation

[Return to Table of Contents](<#table of contents>)

## P15 Test

  - P15.1 Purpose
  - P15.2 Test documentation
    - Strategic Domain: Reads template from ai/templates/T04-test.md
    - Strategic Domain: Creates test documents from source code generated by Tactical Domain using T04 template and saves them in folder ai/workspace/test
  - P15.3 Test Script Creation
    - Test location: tests/ directory at project root (not src/tests/)
    - Strategic Domain: Automatic precursor to test execution
    - Strategic Domain: Generates executable test scripts from T04 test documentation in tests/
    - Strategic Domain: Creates unit tests for components in subdirectories (tests/\<component\>/)
    - Strategic Domain: Uses pytest or unittest framework per pyproject.toml configuration
    - Strategic Domain: Names test files with test_*.py convention
    - Strategic Domain: Links test scripts to test documentation via T04 references
    - Workflow: T04 test doc creation → pytest file generation → test execution
  - P15.4 Test Planning
    - Strategic Domain: Creates comprehensive test strategy before code generation
    - Strategic Domain: Defines test scope, approach, resources, schedule
    - Strategic Domain: Identifies test types: unit, integration, system, acceptance
  - P15.5 Test Case Specification
    - Strategic Domain: Structures test cases: preconditions, inputs, expected outputs, postconditions
    - Strategic Domain: Links test cases to requirements and design elements
    - Strategic Domain: Includes positive, negative, boundary, edge cases
  - P15.6 Test Results Documentation
    - Strategic Domain: Records test execution results in standardized format
    - Strategic Domain: Captures: pass/fail status, defects found, coverage achieved
    - Strategic Domain: Links failed tests to issue documents
  - P15.7 Test Organization
    - Strategic Domain: Maintains hierarchical test structure in tests/
    - Strategic Domain: Separates permanent unit tests from ephemeral validation scripts
    - Strategic Domain: Organizes unit tests by component in subdirectories
    - Strategic Domain: Places fix validation scripts at tests/ root level
  - P15.8 Test Isolation
    - Strategic Domain: Uses temporary environments (tempfile, shutil) for test execution
    - Strategic Domain: Ensures tests create/destroy controlled test environments
    - Strategic Domain: Prevents test pollution through environment isolation
    - Strategic Domain: Enables parallel test execution through isolation
  - P15.9 Dependency Mocking
    - Strategic Domain: Uses unittest.mock to isolate component dependencies
    - Strategic Domain: Mocks external services, file systems, network calls
    - Strategic Domain: Verifies interface contracts without external dependencies
    - Strategic Domain: Documents mocking strategy in test documentation
  - P15.10 Regression Testing
    - Strategic Domain: Creates targeted validation scripts for specific fixes
    - Strategic Domain: Implements progressive validation: minimal → integration → full suite
    - Strategic Domain: Documents validation scripts with fix references
    - Strategic Domain: Removes validation scripts after fix verification
  - P15.11 Test Lifecycle Management
    - Strategic Domain: Distinguishes permanent regression suite from temporary validation
    - Strategic Domain: Maintains permanent tests in tests/\<component\>/ subdirectories
    - Strategic Domain: Archives or removes ephemeral validation scripts post-verification
    - Strategic Domain: Updates test documentation to reflect lifecycle status
  - P15.12 Test-Prompt Coupling
    - Test references source prompt UUID in coupled_docs.prompt_ref field
    - Test iteration number matches source prompt iteration number
    - Iteration synchronization maintained through debug cycles
    - Strategic Domain verifies coupling before test execution
  - P15.13 Test Result Lifecycle
    - Results named: result-<uuid>-<n>.md in ai/workspace/test/result/
    - Result references parent test UUID in coupled_docs.test_ref field
    - Result iteration matches parent test iteration
    - Failed results trigger issue creation (new UUID assigned)
    - Passed results enable document closure workflow
    - Result documents moved to ai/workspace/test/result/closed/ upon acceptance
  - P15.14 Distribution Creation (Human executes)
    - Human: Distribution build when code generation complete and tests pass
```
cd <project name>

# Clean previous build artifacts:
rm -rf dist/ build/ *.egg-info/

# Build distribution
python -m build

# Verify build artifacts
ls -lh dist/

# Test installation in clean environment
pip install dist/*.whl
```
  - P15.15 Progressive Validation Strategy
    - Strategic Domain: Implements graduated validation during debug cycles
    - Targeted validation: Execute minimal test to verify specific fix
    - Integration validation: Execute tests for dependent components
    - Regression validation: Execute full test suite before closure
    - Ephemeral scripts: Create temporary validation at tests/ root
    - Permanent tests: Maintain regression suite in component subdirectories
    - Script lifecycle: Archive or remove validation scripts post-verification
    - Validation sequence mandatory before document closure
    - **Validation Hooks (Tactical Domain, claude_code/claude_omlx profiles — mandatory):**
      - PreToolUse hook: Validates design constraints before code generation
      - PostToolUse hook: Executes targeted tests after file modification
      - Hook failures trigger checkpoint rewind automatically
      - Design validation: Verifies requirements traceability, architecture compliance
      - Code validation: Executes pytest for modified component; canonical template ai/skills/validation/run-tests.md (P00.18)
      - Hook configuration: Provisioned from ai/skills/validation/ into .claude/hooks/ and .claude/settings.json per P10.8
      - Hook scope: File-level (per modification) and iteration-level (batch)
      - Validation logs: Captured in session metadata for audit trail
  - P15.16 Test Type Selection
    - Unit tests: All component implementations (mandatory)
    - Integration tests: Component boundary interactions (as needed)
    - System tests: Full application deployment (pre-release)
    - Acceptance tests: Requirement validation (milestone-based)
    - Regression tests: All unit/integration tests (permanent)
    - Performance tests: NFR validation (periodic benchmarking)
    - Strategic Domain: Selects appropriate test type based on requirements and architecture
    - Test documentation specifies type in test_info.type field
  - P15.17 Test Execution Platforms
    - Unit tests: Development platform with comprehensive mocking
    - Integration tests: Target deployment platform with actual subsystems
    - System tests: Target deployment platform exclusively
    - Acceptance tests: Target deployment platform with stakeholder validation
    - Regression tests: Development platform (primary), target platform (validation)
    - Performance tests: Target deployment platform for accurate measurements
    - Mocking requirements:
      - Development platform: Mock all external dependencies and system services
      - Target platform: Use actual system services where integration testing required
    - Validation workflow:
      - All code changes: Unit tests on development platform
      - Pre-release: Full test suite on target deployment platform
      - Performance benchmarks: Target deployment platform measurements only
    - Platform specification:
      - Define specific development and target platforms in project design documents
      - Document platform-specific tooling and dependencies in component designs
      - Include platform requirements in test documentation
    - Cross-platform considerations:
      - Strategic Domain: Documents platform-specific limitations in test documentation
      - Mocking strategy must isolate tests from platform differences
      - Integration/system tests require target hardware availability
  - P15.18 Test Constraint Summary

    | Constraint | Rule |
    |---|---|
    | Unit tests | Mandatory for every component |
    | System/acceptance/performance tests | Target platform only |
    | Progressive validation | Stages 1→2→3 in order, no skipping |
    | Document closure | Requires Stage 3 regression pass |
    | Coupling mismatch | Blocks workflow — resolve before proceeding |
    | External dependencies in unit tests | Always mocked |
    | Ephemeral scripts | Removed at document closure |

[Return to Table of Contents](<#table of contents>)

## Workflow

See [workflow.md](workflow.md).

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Description |
| ------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.0     | 2025-10-30 | Initial enumeration |
| 1.1     | 2025-11-03 | Added T02 Change template and schema |
| 1.2     | 2025-11-03 | Added T03 Issue template and schema |
| 1.3     | 2025-11-03 | Added T04 Prompt template and schema |
| 1.4     | 2025-11-06 | Integrated IEEE/ISO standards-based directives: P00 (§1.1.11-§1.1.12), P02 (§1.3.5-§1.3.8), P03 (§1.4.5-§1.4.9), P04 (§1.5.5-§1.5.6), P05 (§1.6.2-§1.6.3), P06 (§1.7.2-§1.7.4), new P07 Quality Assurance (§1.8.1) |
| 1.5     | 2025-11-06 | Added T05 Test template and schema |
| 1.6     | 2025-11-06 | Replaced flowchart with revised version incorporating human review checkpoints, iterative cycles, and complete workflow loops |
| 1.7     | 2025-11-06 | Enhanced T04 Prompt template with output format controls to constrain Tactical Domain responses to code-only with minimal integration instructions |
| 1.8     | 2025-11-11 | Added P01 initialization square to Framework Execution Flowchart |
| 1.9     | 2025-11-11 | Added .gitignore specification to P01.2.2 |
| 2.0     | 2025-11-11 | Added pyproject.toml skeleton to P01.2.2 |
| 2.1     | 2025-11-12 | Specified GitHub Desktop as tagging mechanism in P00 1.1.11 Configuration Management |
| 2.2     | 2025-11-12 | Added P00 1.1.13 Tactical Domain Configuration and Appendix A: Tactical Domain Preset Specifications |
| 2.3     | 2025-11-13 | Added tests/ subfolder to src/ directory structure in P01.2.4 |
| 2.4     | 2025-11-13 | Enhanced P06 Test with sections 1.7.1a (test script creation), 1.7.5-1.7.9 (test organization, isolation, mocking, regression testing, lifecycle management) |
| 2.5     | 2025-11-13 | Added audit/ subfolder to workspace directory structure in P01.2.4 |
| 2.6     | 2025-11-13 | Added P08 Audit protocol establishing periodic compliance verification, audit deliverable requirements, and remediation workflow |
| 2.7     | 2025-11-13 | Added audit document class to P00 1.1.10 naming convention and updated P08 1.9.5 to use sequence numbering format |
| 2.8     | 2025-11-13 | Added P00 §1.1.3 Framework Application clarifying that Strategic Domain/2 separation applies to development workflow, not runtime architecture of generated applications. Renumbered subsequent P00 subsections §1.1.4-§1.1.13 |
| 2.9     | 2025-11-14 | Added P01 §1.2.5 traceability matrix skeleton directive and P05 §1.6.4 traceability matrix structure specification. Renumbered P01 §1.2.4 to §1.2.6 |
| 3.0     | 2025-11-14 | Replaced MCP communication with filesystem communication for Strategic Domain↔Tactical Domain (P00 1.1.7-1.1.8-1.1.9-1.1.11); removed LM Studio references; simplified T04 template; updated flowchart; deleted Appendix A |
| 3.1     | 2025-11-14 | Added P09 Prompt protocol; separated prompt management from trace; created workspace/prompt/ folder; updated P00 §1.1.10 document class list; updated P08 §1.9.3 audit scope to P00-P09 |
| 3.2     | 2025-11-16 | Removed prompt iteration numbering (P09 §1.10.2, §1.10.5); GitHub version control replaces iteration-based versioning |
| 3.3     | 2025-11-19 | Enhanced P00 Control (§1.1.7) and Communication (§1.1.8) with strategic/tactical clarification and MCP filesystem awareness; Added semantic versioning standard to P01 Versioning (§1.1.13); Added workspace/ai/ directory to P01 folder structure (§1.2.6) and .gitignore (§1.2.2); Added visual documentation requirements to P02 (§1.3.10) for embedded Mermaid diagrams; Enhanced T01 Design template with visual_documentation section; Enhanced T03 Issue template with prerequisites, reproducibility_conditions, prevention, and verification_enhanced sections |
| 3.4     | 2025-11-20 | Restructured instruction document directives: moved P00 §1.1.11 to P09 §1.10.6; deleted embedded markdown template; converted to point-by-point directive structure; renumbered P00 §1.1.12-§1.1.13 to §1.1.11-§1.1.12 |
| 3.5     | 2025-11-20 | Enhanced P00 §1.1.11 Configuration Management with configuration audit procedure directives; added config-audit template and process requirements; established baseline verification workflow |
| 3.6     | 2025-11-21 | Enforced one-to-one issue-change coupling: replaced P03 §1.4.1-§1.4.2 requiring exclusive issue-to-change relationships; added P04 §1.5.7 Issue-Change Coupling with bidirectional linkage verification |
| 3.7     | 2025-11-26 | Restructured P02 Design into three-tier hierarchy: Tier 1 System Architecture (§1.3.1-§1.3.2), Tier 2 Domain Decomposition (§1.3.3-§1.3.4), Tier 3 Component Decomposition (§1.3.5-§1.3.6); added human review gates after each tier; added Design Hierarchy Naming Convention (§1.3.7), Cross-Linking Requirements (§1.3.8); updated P00 §1.1.8 to specify Tier 3 component designs in T04 prompts; added tier naming convention to P00 §1.1.10 |
| 3.8     | 2025-11-28 | Implemented iteration-based document coupling with lifecycle management: Added iteration field and coupled_docs section to all templates (T02-T06); Enhanced P00 §1.1.10 with iteration tracking and git commit requirements; Created P00 §1.1.13 Document Lifecycle Management defining active/closed states, closure criteria, archival procedures; Added closed/ subfolders to P01 §1.2.6; Enhanced P03 §1.4.2, P04 §1.5.7, P06 §1.7.12-§1.7.13, P09 §1.10.2 with iteration synchronization and coupling requirements; Created T06 Result template and schema |
| 3.9     | 2025-11-28 | Added Python virtual environment and distribution build support: Added venv/, dist/ directories to P01 §1.2.6 folder structure; Added Python build artifacts to P01 §1.2.2 .gitignore (venv/, .venv/, *.pyc, __pycache__/, .pytest_cache/, dist/, build/, *.egg-info/); Created P01 §1.2.7 Virtual Environment Setup with consolidated setup script; Renamed P01 §1.2.2 to §1.2.8 Python documents containing pyproject.toml; Created P06 §1.7.14 Distribution Creation with human-executed directives for build artifact management and distribution creation after tests pass |
| 4.0     | 2025-11-28 | Integrated traceability matrix updates into workflow flowchart: Added P05 matrix update nodes after design approval (Trace1), code generation completion (Trace2), test execution (Trace3), and change implementation (Trace4); ensures bidirectional traceability maintained throughout development lifecycle |
| 4.1     | 2025-11-28 | Added P08 §1.9.9 Audit Closure with closure criteria, process, archival procedures, and reopening constraints; added workspace/audit/closed/ to P01 §1.2.6 folder structure; added audit closure criteria to P00 §1.1.14.3 and audit closed subfolder to P00 §1.1.14.5  |
| 4.2     | 2025-11-30 | Enhanced P06 Test with progressive validation strategy (§1.7.15), test type selection criteria (§1.7.16), platform execution specifications (§1.7.17); updated workflow flowchart to incorporate progressive validation phases and platform-specific testing requirements |
| 4.3     | 2025-12-03 | Added workspace/proposal/ directory: Added proposal document class to P00 §1.1.10; added workspace/proposal/ and workspace/proposal/closed/ to P01 §1.2.6 folder structure; added proposal directories to P01 §1.2.2 .gitignore |
| 4.4     | 2025-12-03 | Added P00 §1.1.14 Logging Standards: environment-based log level control, flat file format, rotation policy, test/production mode separation |
| 4.5     | 2025-12-04 | Simplified human handoff mechanism: Replaced P00 §1.1.8 and P00 §1.1.9 instruction document creation with conversational command delivery; replaced P09 §1.10.3 Instruction Documents with Human Handoff providing ready-to-execute commands directly in conversation; removed P09 §1.10.5 Instruction Document Creation (now covered by §1.10.3); eliminates redundant prompt-NNNN-instructions.md files while maintaining domain separation |
| 4.6     | 2025-12-04 | Added P00 §1.1.15 Knowledge Base: Both domains must consult workspace/knowledge/ when creating documents or code; established institutional knowledge capture; added knowledge/ to P01 §1.2.6 folder structure; enhanced T04 Prompt context with knowledge_references field |
| 4.7     | 2025-12-10 | Enhanced P09 §1.10.3 Human Handoff: Replaced single command format with structured approach providing governance, design, and prompt locations to Tactical Domain; changed execution from terminal command to paste-into-Tactical Domain workflow |
| 4.8     | 2025-12-11 | Enhanced P06 §1.7.3 Test Script Creation: clarified pytest generation as automatic precursor to test execution; added workflow sequence T05→pytest→execute; inserted D1_Generate_Tests node in flowchart between D1_Test_Doc and D1_Execute |
| 4.9     | 2025-12-11 | Test directory relocation: Moved tests/ from src/tests/ to project root; updated P01 §1.2.6 folder structure; updated P06 §1.7.3, §1.7.7, §1.7.11 path references; resolves Python import conflicts and aligns with pytest ecosystem standards |
| 5.0     | 2025-12-11 | Added explicit document closure node to workflow flowchart: Inserted D1_Close node between H7 ence and completion; ensures archival procedure execution visible in workflow; aligns flowchart with P00 §1.1.14.4 archival directives |
| 5.1     | 2025-12-12 | Removed platform-specific assumptions from P06 §1.7.17 Test Execution Platforms: Replaced hardcoded references to Raspberry Pi, MacOS, nmcli, systemd, sockets with generic development/target deployment platform terminology; added Platform specification guidance directing platform details to project design documents; eliminates inappropriate context bleed across projects with different deployment targets |
| 5.2     | 2025-12-12 | Enhanced T01 Design template with explicit platform specifications: Added development_environment (platform, python_version, toolchain) and target_platform (type, os, architecture, constraints) sections; updated T01 schema with corresponding validation rules; provides structured platform documentation aligned with P06 1.7.17 test execution requirements |
| 5.3     | 2025-12-12 | Template externalization: Split T01-T06 templates into separate files in /templates/ directory; implemented UUID-based document coupling replacing NNNN sequence numbering (8-character hex format: ^[0-9a-f]{8}$); updated all protocol sections and schemas with UUID patterns; maintains backward compatibility through GitHub history |
| 5.4     | 2025-12-13 | Clarified P01 1.2.6 Project folder structure: Added note that structure applies to projects using the framework, not to LLM-Governance-and-Orchestration repository itself which contains only ai/, doc/, and templates/ directories |
| 5.5     | 2025-12-13 | Added P00 §1.1.17 Templates: Explicit template location specification (ai/templates/); Updated protocol sections P02 §1.3.1/§1.3.3/§1.3.5, P03 §1.4.1, P04 §1.5.1/§1.5.4, P06 §1.7.2, P09 §1.10.2 with template read directives; Replaced internal markdown anchor references with explicit filesystem paths |
| 5.6     | 2025-12-13 | Added P10 Requirements protocol: Systematic requirements capture before design (§1.11.1-§1.11.6); Created T07 Requirements template in ai/templates/; Added workspace/requirements/ and workspace/requirements/closed/ to P01.§1.2.6 folder structure; Updated workflow flowchart with requirements elicitation phase (Start → D1_Elicit → H_Req → D1_Baseline → D1_Design); Requirements baseline precedes master design creation; No iteration numbering, git history tracks changes |
| 5.7     | 2025-01-13 | Eliminated legacy 0000 sequence from master document naming: Changed from \<class\>-0000-master_\<name\>.md to \<class\>-\<name\>-master.md; Updated P00 §1.1.10, P01 §1.2.5, P02 §1.3.1/§1.3.7, P05 §1.6.4, P10 §1.11.2/§1.11.5; Suffix pattern enables clearer alphabetical sorting while maintaining master designation |
| 5.8     | 2025-01-13 | Clarified P00 §1.1.10 document naming conventions: Explicitly separated master document naming (no UUID) from all other documents (UUID required); Added concrete examples for both patterns; Removes ambiguity about UUID assignment criteria |
| 5.9     | 2025-01-13 | Added section symbol (§) notation throughout governance document: Replaced all section number references with § prefix for formal technical documentation aesthetics and improved reference precision; Updated all protocol sections (P00-P10), subsections, and version history references |
| 6.0     | 2025-01-28 | Added Tactical Domain 2.1.0 integration Phase 1: Skills Management (P00 §1.1.18→17), Context Optimization (P00 §1.1.19→18), .claude/ directory structure (P01 §1.2.6), CLAUDE.md requirement (P09 §1.10.3 with verification and UUID format correction), .gitignore additions (P01 §1.2.2) |
| 6.1     | 2025-01-28 | Added Tactical Domain 2.1.0 integration Phase 2: Checkpoint Strategy (P03 §1.4.8 with automatic rewind capability), Validation Hooks (P06 §1.7.15 PreToolUse/PostToolUse integration), Hook-Based Auditing (P07 §1.8.7 automated audit trail capture); Renumbered P03 subsections §1.4.9-§1.4.11 |
| 6.2     | 2025-01-28 | Added Tactical Domain 2.1.0 integration Phase 3: Wildcard Permissions (P09 §1.10.4 batch operation support), Automated Audits (P07 §1.8.3 Stop hook compliance checking), Exploration Phase (P02 §1.3.8 lightweight prototyping workflow); Renumbered P02 subsections §1.3.9-§1.3.15; Renumbered P09 §1.10.5 |
| 6.3     | 2025-02-13 | Enhanced P00 §1.1.15 Knowledge Base with behavioral standards specification: workspace/knowledge/behavioral-standards.yaml provides machine-readable behavioral constraints for autonomous execution contexts; T04 template v1.2 adds behavioral_standards section (source, enforcement_level); Example files in doc/examples/ (YAML, JSON Schema, validation script) |
| 6.4     | 2025-02-13 | Phase 2 refactoring: Model-agnostic terminology (Strategic/Tactical Domain), Ralph Loop Integration (§1.1.11), model implementation options (§1.1.4), multi-model orchestration support (§1.1.8), section renumbering (§1.1.12-§1.1.19), removed duplicate Logging Standards |
| 6.5     | 2025-02-18 | Implementation profile pattern: Replaced Claude-specific references with abstract equivalents — .claude/skills/ → <skills_dir>/, CLAUDE.md → tactical context file, .claude/ → <tactical_config>/; renamed §1.1.11 to AEL; removed duplicate §1.1.4 Tactical Domain line; .gitignore Tactical Domain section replaced with profile reference; P01 §1.2.6 folder structure uses abstract placeholders; P06 §1.7.15 and P07 §1.8.7 hook paths abstracted; P09 §1.10.3 context file references abstracted; implementation profiles created in ai/implementation-profiles/ |
| 6.6     | 2026-02-18 | Corrected path references doc/implementation-profiles/ → ai/implementation-profiles/ throughout; Added P01 §1.2.8 Implementation Profile Setup: profile selection, Claude profile (Claude Code install, CLAUDE.md, .claude/ structure), OLLama profile (OLLama install, model pull, Goose install, provider config, context file), AEL setup common to both profiles |
| 6.7     | 2026-02-18 | Section renumbering corrections: P01 §1.2.8↔1.2.9 (Python documents) and §1.2.9↔1.2.8 (Implementation Profile Setup) to restore sequential order; P00 §1.1.18→17 (Templates), §1.1.19→18 (Skills Management), §1.1.20→19 (Context Optimization) to close gap at §1.1.17 |
| 6.8     | 2026-02-18 | P01 §1.2.2 .gitignore: replaced profile-specific placeholder comment with explicit entries for both profiles (CLAUDE.local.md, .claude/settings.json, .goosehints.local, .goose/ralph/); removed redundant .gitignore instruction from P01 §1.2.8 |
| 6.9     | 2026-02-18 | P01 §1.2.2 .gitignore: extended Tactical Domain section with .claude/commands/ and .goose/recipes/ to cover all known non-shared subdirectories for both profiles |
| 7.0     | 2026-02-18 | Added `bin/` directory to P01 §1.2.6 project folder structure; added Integration Scripts directive to P00 §1.1.11 AEL: project-scoped scripts reside in `<project>/bin/`, global installation not required |
| 7.1     | 2026-02-25 | Added Goose recipe integration to P01 §1.2.4: copy `ai/goose/recipes/` from framework to project, configure `ralph-loop.sh` with project-absolute recipe path; updated P01 §1.2.8 AEL setup to reference project-scoped recipes, removing `~/.config/goose/recipes/` install instruction |
| 7.2     | 2026-03-04 | Restructured repository: meta/ → framework/, src/ → skel/; Revised P01 §1.2.4: replaced manual ai/ copy with copy-from-skel/ workflow; skel/ is the deployable project skeleton maintained in the framework repository |
| 7.3     | 2026-03-04 | Renamed ai/implementation-profiles/ → ai/profiles/; renamed profile-claude-desktop.md → claude-desktop.md, profile-claude.md → claude.md, profile-ollama.md → ollama.md; updated all references in P00 §1.1.18, §1.1.19, P01 §1.2.8, P09 §1.10.3 |
| 7.4     | 2026-03-11 | Replaced Goose AEL with Python AEL orchestrator: removed ai/goose/, added ai/ael/ (orchestrator.py, mcp_client.py, parser.py, recipes); updated §1.1.11 state dir (.goose/ralph/ → .ael/ralph/), §1.2.2 .gitignore, §1.2.4 recipe path note, §1.2.8 AEL setup |
| 7.5     | 2026-03-11 | Narrowed scope to Apple Silicon + MLX: removed OLLama profile setup from §1.2.8; removed Goose/OLLama from §1.1.4 implementation options; deprecated docs/setup-goose.md, docs/setup-ollama-lmstudio.md, ai/profiles/ollama.md to deprecated/ |
| 7.6     | 2026-03-11 | Integrated AEL into workflow: replaced Tactical Domain black-box subgraph with AEL Ralph Loop + SHIP/BLOCKED decision; updated §1.1.8 command format; updated §1.1.11 Loop Exit traceability (SHIP→T06, BLOCKED→T03); updated §1.10.3 Human Handoff command format |
| 7.7     | 2026-03-12 | Added name registry: design-\<project\>-name_registry-master.md as incremental canonical element naming contract; P02 §1.3.16 registry structure; P02 §1.3.1/§1.3.3/§1.3.5 registry directives per tier; P02 §1.3.7 registry naming convention; P00 §1.1.10 registry master notation; P08 §1.9.3 naming consistency audit scope; P09 §1.10.2 element_registry prompt directive |
| 7.8     | 2026-03-14 | Added enhancement and requirement_change paths to P03 §1.4.1: creates T03 issue with type `enhancement` or `requirement_change` before T02 change document; resolves omission where T03 type enum had no accommodation for non-defect change requests |
| 7.9     | 2026-03-18 | Added P03 §1.4.12 Trivial Change Exemption: defines trivial and surgical change criteria; when all five criteria satisfied and human approval obtained, Strategic Domain may implement directly without T03, T02, T04, or AEL; git history is sole audit record |
| 8.0     | 2026-03-18 | Added P09 §1.10.2 tactical_brief directive: Strategic Domain populates concise AEL task payload (~200-400 tokens) in T04 prompt; orchestrator uses brief in preference to full document |
| 8.1     | 2026-03-20 | Added context budget: AEL orchestrator resolves context window from model config.json on disk; warn/abort thresholds enforced per phase iteration; context-budget.md written to state directory at startup for Strategic Domain; P09 §1.10.2 directive: Strategic Domain reads context-budget.md before authoring tactical_brief |
| 8.2     | 2026-03-20 | Added entry point verification directive to P04 §1.5.1 and P09 §1.10.2: Strategic Domain reads project entry point configuration (pyproject.toml [project.scripts] or equivalent) and confirms target file is in deployment path before specifying any file_path in T03 issue or T04 prompt; resolves issue c3e5b7d9 |
| 8.3     | 2026-03-24 | Added tactical_brief verification directive to P09 §1.10.2: Strategic Domain must verify tactical_brief is non-empty before issuing AEL command; T04 template v1.6 removes governance-only fields and fixes placeholder |
| 8.4     | 2026-03-25 | Added tactical_brief format constraint to P09 §1.10.2: tactical_brief must be authored in a ```yaml block with tactical_brief as root key; per-section prompts must not use ```text for §8.0; plain text blocks are invisible to orchestrator extract_tactical_brief function |
| 8.5     | 2026-03-25 | Orchestrator improvements from AEL log analysis: (1) extract_tactical_brief adds section-header fallback (Pass 2) recovering brief from plain fenced block under ## N.N Tactical Brief heading; fallback emits WARNING not DEBUG; (2) main_async pre-initialises rc=1 and logs `AEL end rc=N` in finally block to distinguish clean vs unclean termination; P09 §1.10.2: added directives clarifying max_iterations (outer cycles) vs phase_max_iterations (inner tool-call iterations) and AEL end log semantics |
| 8.6     | 2026-03-26 | Added P06 §1.7.18 Test Constraint Summary: quick-reference constraint table consolidated from testing-standards.md |
| 8.7     | 2026-03-26 | Removed behavioral standards directives from P00 §1.1.16: behavioral-standards.yaml, schema, and validator deprecated — no operational function in orchestrator; content duplicates governance protocols |
| 8.8     | 2026-03-29 | Extracted §2.0 Workflow flowchart to workflow.md; replaced §2.0 body with link; updated ToC entry and Prime Directive cross-reference |
| 8.9     | 2026-04-28 | Added ael-mcp integration: P00 §1.1.11 Claude Desktop Interface directive; P09 §1.10.3 Option A/B AEL execution (human executes or Strategic Domain launches via ael-mcp); P01 §1.2.8 ael-mcp setup steps for Claude Desktop profile |
| 9.0     | 2026-04-30 | Added claude-omlx as Tactical Domain implementation option: §1.1.4 implementation options; §1.2.8 claude-omlx profile setup steps; fixed claude.md reference path (deprecated/ → profiles/) |
| 9.1     | 2026-06-14 | Consolidated framework footprint under ai/: relocated workspace/ → ai/workspace/ across P00–P10 path references; loop state .ael/ralph/ → ai/state/ralph/ (§1.1.11); updated §1.2.2 .gitignore and §1.2.6 folder structure for ai/ layout; added ai/state/ and ai/dashboard-alerts.md; documented fork isolation mode; CLAUDE.md retained at project root (Claude Code profile) |
| 9.2     | 2026-06-16 | Updated P01 §1.2.4: replaced skel/ copy workflow with bin/propagate.sh; framework is now a single unified ai/ directory |
| 9.3     | 2026-06-16 | §1.1.17: T01-T06 → T01-T07; added T07-requirements.md to file list; §1.1.16: knowledge/ made optional; §1.2.6: knowledge/ marked optional; §1.3.8: removed mandatory knowledge/ directive |
| 9.4     | 2026-06-16 | P08 §1.9: merged duplicate "Audit Closure" sections — former §1.9.7 (short form) folded into former §1.9.9 (subsectioned form); renumbered §1.9.8 Audit Trail → §1.9.7, merged Audit Closure §1.9.9 → §1.9.8 (subsections §1.9.8.1–.4); updated cross-references in ai/doc/guide-audit-loop.md and docs/guide-audit-loop.md |
| 9.5     | 2026-06-17 | Simplified Tactical Domain configuration: removed <tactical_config>/<skills_dir>/commands placeholders from §1.2.6; added ai/context.md (AEL profile) and .claude/ block (Claude Code profiles only) to §1.2.6; scoped §1.1.18 Skills Management to Claude Code profiles; updated §1.1.19 context file paths per profile |
| 9.6     | 2026-06-17 | Added ai/context.md template; ralph-work.yaml v1.3.0 reads project_root/ai/context.md at task start; §1.1.19 notes AEL auto-load behaviour |
| 9.7     | 2026-06-17 | Renamed ai/workspace/admin/ → ai/workspace/report/ in §1.2.2 .gitignore template and §1.2.6 folder structure; added report/closed/ to §1.2.6 and §1.1.14.5 |
| 9.8     | 2026-06-25 | Added P03 §1.4.1 exception: initial implementation from approved design does not require issue or change documents; forward path is design → T04 → execution → review; corrective loop triggered only by AEL BLOCKED or test failure |
| 9.9     | 2026-06-28 | P08 §1.9: added §1.9.9 Audit Modes (strategic / tactical); split §1.9.4 into §1.9.4.1 strategic-led and §1.9.4.2 tactical-led (AEL audit loop); §1.9.2 mode-selection note; §1.9.5 T08 template and tactical archive note; registered T08-audit.md in §1.1.17 Templates and the ToC; append-only, existing §1.9.x not renumbered |
| 9.10    | 2026-07-02 | P09 §1.10.2: prompt creation clause conditioned on source_ref (design-sourced vs change-sourced, §1.4.1 exception); tactical_brief/context-budget directives scoped to target_profile == ael; coupled_docs directives conditioned on source_ref; P03 §1.4.1: added cross-reference to P09 source_ref discrimination; resolves issue-713437bc (T04 schema hard-coded AEL-exclusivity and change-document-exclusivity, contradicting §1.4.1 exception and multi-profile Tactical Domain architecture) |
| 9.11    | 2026-07-08 | P01 §1.2.8 and P09 §1.10.2: replaced retired `budget.py` file-existence precondition with orchestrator.py's own tiered context-window resolver (config.yaml override → live omlx_model_status query → per-model config.yaml override → unknown); context-budget.md now written automatically at AEL startup; Strategic Domain gate is a direct omlx_model_status call rather than a file-existence check (change-d42e64a9, Stream B) |
| 9.12    | 2026-07-17 | P06 §1.7.15 Validation Hooks made mandatory for claude_code/claude_omlx profiles; P00 §1.1.18 adds canonical skill source ai/skills/ and mandatory skill entry (ai/skills/validation/run-tests.md); P01 §1.2.6 corrected .claude/ git-tracking comment (was incorrectly marked wholly excluded) and expanded tree; P01 §1.2.8 adds mandatory skill provisioning step to both Claude Code profiles; P01 §1.2.2 .gitignore corrected .claude/settings.json → .claude/settings.local.json to match Claude Code's team-shared-settings convention |
| 9.13    | 2026-08-19 | P09 §1.10.3 added Option C — Claude Code manual invocation (claude_code/claude_omlx profiles), documenting the human-issued task instruction cross-referenced to ai/profiles/claude-code.md §5.0 |
| 9.14    | 2026-08-19 | P09 §1.10.3: corrected heading “presents AEL execution options” → “presents Tactical Domain execution options”, since Option C is not an AEL path (issue raised via GTach ai/task.md) |
| 9.15    | 2026-08-19 | P06 §1.7.15: corrected stale reference ai/profiles/claude.md → ai/profiles/claude-code.md (claude.md was an obsolete duplicate, identified via GTach ai/profiles/ audit) |
| 9.16    | 2026-08-21 | Added P00 §1.1.20 Task Register: ai/task.md open-work index, exempt from §1.1.10 naming and §1.1.14 lifecycle; added task.md to §1.2.6 folder structure; concept sourced from GTach ai/task.md |
| 10.0    | 2026-09-22 | **Breaking.** Protocol and template identifiers renumbered into workflow order, and positional citations replaced by protocol-relative ones. Protocols are now two bands: cross-cutting P00 Governance, P01 Trace (was P05), P02 Audit (was P08), P03 Issue (was P04), P04 Change (was P03); lifecycle P10 Project Initialization (was P01), P11 Requirements (was P10), P12 Design (was P02), P13 Prompt (was P09), P14 Quality (was P07), P15 Test (was P06). P05 and P16-P19 are reserved and carry no content. Templates renumbered into document-creation order and renamed: T01 Requirements (was T07), T02 Design (was T01), T03 Prompt (was T04), T04 Test (was T05), T05 Result (was T06), T06 Issue (was T03), T07 Change (was T02), T08 Audit unchanged. Citations of the form §1.x.y are retired in favour of the dotted fully-qualified form Pnn.x.y; the section sign no longer appears in a protocol citation, and every heading carries its citation string verbatim. This document is restructured so that each protocol is a top-level section keyed by its identifier and clause numbers are local to it, which decouples a citation from a protocol's ordinal position and makes any future reordering a mapping-table edit rather than a corpus-wide substitution. Appendix A carries the permanent old-to-new alias tables; the frozen historical corpus in dev/ and every closed/ directory cites the retired scheme and is read through it. Executed mechanically by dev/tools/migrate_identifiers.py from dev/tools/mapping.yaml; 654 substitutions across 32 files, 10 of 10 verification checks passing, and 1086 clause lines preserved exactly. Downstream projects remain pinned at 9.16 until propagated. See dev/proposals/proposal-eb782f83-protocol-template-reordering.md. |
| 10.1    | 2026-09-23 | Added P11.7 Framework Development Requirements: dev/ requirements are prose with FR/NFR/CON tables; T01 applies to downstream projects. P10.8: corrected claude-code.md reference link to profiles/claude-code.md. Non-breaking. |
| 10.2    | 2026-09-23 | Reconciled audit closure: P00.14.3 defers to P02.8; P02.8.2 follow-up audit required when remediation changed source code, waivable by the human with a recorded waiver otherwise. Non-breaking. |
| 10.3    | 2026-09-23 | P10.6: ai/ holds framework files and the declared project files only; other project files belong outside ai/ and are relocated to ai-local/ by bin/propagate.sh. Added ai-local/ to the layout. Non-breaking. |
| 10.4    | 2026-09-23 | P10.6: logs/ added to the declared project set and layout; bin/propagate.sh never deletes — retired framework files are relocated to ai-local/ with project files, labelled, for human deletion. Non-breaking. |
| 10.5    | 2026-09-23 | P10.6: locally edited framework files are backed up to ai-local/ before propagation overwrites them. Non-breaking. |

---
[Return to Table of Contents](<#table of contents>)

---

Copyright (c) 2026 William Watson. MIT License.

---

## Appendix A — Identifier Aliases

Permanent. It is never removed, and it is corrected only under `P04`.

**Scope.** This appendix resolves identifiers written under the scheme retired
at governance v10.0. Apply it to:

- every `closed/` directory throughout the repository;
- the development corpus in `dev/` dated before 2026-09-22, excluding the
  `eb782f83` document set;
- version-history sections anywhere in the corpus, including in this document
  and in files otherwise written in the current scheme.

Do **not** apply it to:

- `dev/smoke/ai/`, which is regenerated from `ai/` and is current-scheme
  throughout;
- the `eb782f83` proposal, requirements, design, baseline report, audit brief
  and audit report, which were written in the current scheme.

**Why the distinction matters.** Five protocol identifiers are valid under
both schemes and resolve to a *different* protocol under each:
`P01`, `P02`, `P03`, `P04`, `P10`. Seven of the eight template numbers behave the
same way. Applied to current-scheme text, this appendix silently resolves them
to the wrong protocol.
`P03 Issue` in a current-scheme document means Issue; resolved through A.1 it
would read as Change.

**Version histories.** A version-history entry records what was done under the
scheme in force when it was written. Those entries were deliberately excluded
from the migration, because rewriting them would falsify the record. Ninety-five
positional citations of the form `§1.x` survive in the live corpus on that
basis, together with roughly a hundred retired bare identifiers. Read every
version-history entry under this appendix, whatever scheme the rest of its
document uses.

### A.1 Protocol Aliases

| Retired | Name | Current |
|---|---|---|
| `P00` | Governance | `P00` |
| `P01` | Project Initialization | `P10` |
| `P02` | Design | `P12` |
| `P03` | Change | `P04` |
| `P04` | Issue | `P03` |
| `P05` | Trace | `P01` |
| `P06` | Test | `P15` |
| `P07` | Quality | `P14` |
| `P08` | Audit | `P02` |
| `P09` | Prompt | `P13` |
| `P10` | Requirements | `P11` |

### A.2 Template Aliases

The bare-identifier column resolves a retired `T0n` used without its filename,
of which the frozen corpus holds several hundred.

| Retired identifier | Retired filename | Class | Current identifier | Current filename |
|---|---|---|---|---|
| `T01` | `T01-design.md` | design | `T02` | `T02-design.md` |
| `T02` | `T02-change.md` | change | `T07` | `T07-change.md` |
| `T03` | `T03-issue.md` | issue | `T06` | `T06-issue.md` |
| `T04` | `T04-prompt.md` | prompt | `T03` | `T03-prompt.md` |
| `T05` | `T05-test.md` | test | `T04` | `T04-test.md` |
| `T06` | `T06-result.md` | result | `T05` | `T05-result.md` |
| `T07` | `T07-requirements.md` | requirements | `T01` | `T01-requirements.md` |
| `T08` | `T08-audit.md` | audit | `T08` | `T08-audit.md` |

### A.3 Citation Rule

Retired citations take the positional form `§1.<ordinal>.<a>[.<b>]`, where
`<ordinal>` is the protocol's position in the retired document. Current
citations are dotted and fully qualified: `<identifier>.<a>[.<b>]`.

| Retired ordinal | Retired protocol | Current prefix |
|---|---|---|
| `§1.1` | `P00` Governance | `P00` |
| `§1.2` | `P01` Project Initialization | `P10` |
| `§1.3` | `P02` Design | `P12` |
| `§1.4` | `P03` Change | `P04` |
| `§1.5` | `P04` Issue | `P03` |
| `§1.6` | `P05` Trace | `P01` |
| `§1.7` | `P06` Test | `P15` |
| `§1.8` | `P07` Quality | `P14` |
| `§1.9` | `P08` Audit | `P02` |
| `§1.10` | `P09` Prompt | `P13` |
| `§1.11` | `P10` Requirements | `P11` |

### A.4 Reserved Identifiers

| Identifier | Intended protocol |
|---|---|
| `P05` | Continuous Integration |
| `P06` | *unallocated* |
| `P07` | *unallocated* |
| `P08` | *unallocated* |
| `P09` | *unallocated* |
| `P16` | Execution |
| `P17` | Release |
| `P18` | Deployment and Propagation |
| `P19` | Observability |

Reserved identifiers carry no content. A citation resolving to one is a
defect, not a reference.

### A.5 Unmigrated Namespace — `schema_type`

Template document schemas carry a numeric identifier in their `schema_type`
field: `t01_design`, `t02_change`, `t03_issue` and so on. **These were not
migrated and retain the retired numbering.** `T02-design.md` declares
`schema_type: "t01_design"`.

This is a recorded exception, not an oversight left standing. The numeric
prefix cannot be migrated in isolation: `linter.py` keys its validation rules,
enum constraints, identifier patterns and coupling paths on these strings, and
every document in the frozen corpus carries them. Migrating the namespace would
require either editing frozen documents or breaking their validation, and
`CON-04` forecloses both.

| Field value | Template document |
|---|---|
| `t01_design` | `T02-design.md` |
| `t02_change` | `T07-change.md` |
| `t03_issue` | `T06-issue.md` |
| `t04_prompt` | `T03-prompt.md` |
| `t05_test` | `T04-test.md` |
| `t06_result` | `T05-result.md` |
| `t07_requirements` | `T01-requirements.md` |
| `t08_audit` | `T08-audit.md` |

The durable remedy is to retire the numeric prefix in favour of the class word,
which is scheme-independent — the same correction this migration made to
protocol citations. That is deferred to its own change.
