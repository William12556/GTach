Created: 2026 April 27

# Strategic Domain Primer

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Architecture](<#2.0 architecture>)
[3.0 Responsibilities](<#3.0 responsibilities>)
[4.0 Workflow](<#4.0 workflow>)
[5.0 Protocol Reference](<#5.0 protocol reference>)
[6.0 Document Conventions](<#6.0 document conventions>)
[7.0 Constraints](<#7.0 constraints>)
[8.0 Templates](<#8.0 templates>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document is a concise operational primer for the Strategic Domain. It distils
[governance.md](governance.md) into actionable guidance. Governance.md is authoritative;
this document provides orientation and quick reference only.

Prime Directive: Follow the [workflow](workflow.md).

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Architecture

The framework separates software development into two domains:

| Domain | Role | Implementation |
|---|---|---|
| Strategic | Plan, control, validate | Claude Desktop |
| Tactical | Execute, generate code | AEL (Ralph Loop) or Claude Code |

Communication between domains is filesystem-based (MCP). Neither domain has
direct conversational access to the other.

**Tactical Domain implementations:**

- **AEL (Autonomous Execution Loop)** — reference implementation. Runs a
  worker/reviewer cycle (Ralph Loop) until `SHIP` or `BLOCKED`. State resides
  in `.ael/ralph/`. Requires oMLX inference endpoint and `config.yaml`.
- **Claude Code** — alternative profile. Manual invocation; no automated loop.
  Uses `CLAUDE.md` as tactical context file. See `ai/profiles/claude.md`.

**ael-mcp (Claude Desktop profile, optional)** — standalone MCP server exposing
`start_ael`, `ael_status`, and `reset_ael` tools to Claude Desktop. Allows the
Strategic Domain to launch AEL and query outcome without human terminal relay.
See P09 §1.10.3 Option B and P01 §1.2.8.

Implementation profiles are defined in `ai/profiles/`. The active profile
determines the tactical context file name, skills directory, and AEL configuration.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Responsibilities

The Strategic Domain owns the following functions:

**Planning**
- Requirements elicitation (P10)
- Three-tier design hierarchy: master → domain → component (P02)
- Name registry maintenance

**Execution Coordination**
- T04 prompt authoring and AEL command delivery (P09)
- Context budget check before every T04 prompt
- Human handoff: ready-to-execute command after approval

**Quality**
- Code review after AEL SHIP (or Claude Code completion)
- Test documentation and pytest generation (P06)
- Configuration audit against design baseline (P08)

**Issue Management**
- T03 issue creation from failed tests or AEL BLOCKED (P04)
- T02 change document creation from issues (P03)
- Issue–change one-to-one coupling enforcement

**Governance**
- Traceability matrix updates at every phase transition (P05)
- Document lifecycle management: active → closed (P00 §1.1.14)
- Git commit after every iteration increment

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Workflow

Condensed stage sequence. See [workflow.md](workflow.md) for the full flowchart.

```
P01  Project Initialization  →  run budget.py
P10  Requirements            →  human approval → baseline
P02  Design (Tier 1–3)       →  human approval per tier → git tag baseline
P09  T04 Prompt              →  check context-budget.md → human approval
     AEL  →  SHIP or BLOCKED
            Option A: human runs terminal command (all profiles)
            Option B: Strategic Domain calls start_ael / polls ael_status
                      (Claude Desktop + ael-mcp only)
     Claude Code  →  human-directed execution (no loop)
       SHIP / complete  →  P08 code review → P06 test → progressive validation
       BLOCKED          →  P04 issue → P03 change → P09 new prompt
P06  Tests pass              →  human acceptance
P00  Close documents         →  move to closed/ → git commit → AEL reset
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Protocol Reference

| Protocol | Name | Key Action |
|---|---|---|
| P00 | Governance | Master directives, architecture, document conventions |
| P01 | Project Initialization | Folder structure, .gitignore, venv, budget.py |
| P02 | Design | Three-tier hierarchy, name registry, Mermaid diagrams |
| P03 | Change | T02 from T03 issue; one-to-one coupling; trivial exemption |
| P04 | Issue | T03 from test failure or BLOCKED; issue–change coupling |
| P05 | Trace | Traceability matrix updates at every phase boundary |
| P06 | Test | T05 docs, pytest generation, progressive validation |
| P07 | Quality | Code validation, automated audits via AEL hooks |
| P08 | Audit | Periodic compliance audit; findings → issues |
| P09 | Prompt | T04 authoring, tactical_brief, AEL command delivery |
| P10 | Requirements | T07 elicitation before design; baseline before Tier 1 |

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Document Conventions

**Naming**

| Pattern | Example |
|---|---|
| Master (singleton) | `design-<project>-master.md` |
| All other documents | `<class>-<8-hex-uuid>-<name>.md` |

Document classes: `design`, `change`, `issue`, `prompt`, `test`, `result`,
`audit`, `trace`, `requirements`.

**UUID propagation**: The first document created in a workflow cycle (issue or
change) generates the UUID. All coupled documents inherit it.

**Iteration**: Increments when a document re-enters a cycle after failure.
Both coupled documents (issue + change) increment together. Git commit
required after each increment.

**Lifecycle**

| State | Location | Mutability |
|---|---|---|
| Active | `workspace/<class>/` | Mutable |
| Closed | `workspace/<class>/closed/` | Immutable |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Constraints

**Forbidden**
- Creating, modifying, or deleting source code or documents without explicit
  human request (both domains).
- Exceeding the Tactical Domain context budget when authoring T04 prompts.
- Issuing an AEL command when `tactical_brief` is empty.

**Context Budget**
- `context-budget.md` must exist in `.ael/ralph/` before authoring any T04
  prompt. If absent, instruct human to run `python ai/ael/src/budget.py`.
- Read budget before sizing `tactical_brief` (~200–400 tokens target).

**tactical_brief Format**
- Must be a ` ```yaml ` fenced block with `tactical_brief:` as the root key.
- Plain text blocks are not detected by the orchestrator.

**Trivial Change Exemption** (P03 §1.4.12)
- Qualifies only when both trivial AND surgical, and all five criteria met:
  single function, ≤20 line delta, no interface changes, unambiguous,
  human-approved.
- Exempt from T03 → T02 → T04 → AEL. Git commit is the sole audit record.

**Change Documentation Scope**
- Full issue/change/prompt workflow applies to `src/` changes only.
- `workspace/` document changes may be made directly after human approval.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Templates

All templates reside in `ai/templates/`. Read the template before creating
any document.

| Template | Document Class | Location |
|---|---|---|
| T01 | Design | `ai/templates/T01-design.md` |
| T02 | Change | `ai/templates/T02-change.md` |
| T03 | Issue | `ai/templates/T03-issue.md` |
| T04 | Prompt | `ai/templates/T04-prompt.md` |
| T05 | Test | `ai/templates/T05-test.md` |
| T06 | Result | `ai/templates/T06-result.md` |
| T07 | Requirements | `ai/templates/T07-requirements.md` |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-04-27 | Initial draft |
| 0.2 | 2026-04-28 | Added ael-mcp to §2.0 Architecture; annotated §4.0 Workflow AEL step with Option A/B |

---

Copyright (c) 2026 William Watson. MIT License.
