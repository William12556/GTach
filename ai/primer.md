Created: 2026 April 27

# Strategic Domain Primer

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Architecture](<#2.0 architecture>)
[2.1 Tactical Profiles](<#2.1 tactical profiles>)
[2.2 Monitoring Tools](<#2.2 monitoring tools>)
[3.0 Responsibilities](<#3.0 responsibilities>)
[4.0 Workflow](<#4.0 workflow>)
[4.1 Audit Modes](<#4.1 audit modes>)
[5.0 Protocol Reference](<#5.0 protocol reference>)
[6.0 Document Conventions](<#6.0 document conventions>)
[7.0 Constraints](<#7.0 constraints>)
[8.0 Templates](<#8.0 templates>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document is a concise operational primer for the Strategic Domain. It distils
`governance.md` into actionable guidance. `governance.md` is authoritative;
this document provides orientation and quick reference only.

**Prime Directive: Follow the workflow.**

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
  in `ai/state/ralph/`. Requires oMLX inference endpoint and `config.yaml`.
  Context file: `ai/context.md`.
- **Claude Code** — alternative profile. Manual invocation; no automated loop.
  Uses `CLAUDE.md` at project root as tactical context file. See `ai/profiles/claude-code.md`.

**Tactical Domain execution options** (P13.3) — after T03 prompt approval, human
selects one of three options:

- **Option A** — human executes AEL command directly (all profiles).
- **Option B** — Strategic Domain launches AEL via `ael-mcp` (Claude Desktop profile
  only). Standalone MCP server exposing `start_ael`, `ael_status`, and `reset_ael`.
  Allows the Strategic Domain to launch AEL and query outcome without human terminal
  relay. See P10.8.
- **Option C** — Claude Code manual invocation (`claude_code`/`claude_omlx` profiles).
  Human issues the task instruction directly in Claude Code. See `ai/profiles/claude-code.md` §5.0.

Implementation profiles are defined in `ai/profiles/`. The active profile
determines the tactical context file name, skills directory, and AEL configuration.

[Return to Table of Contents](<#table of contents>)

---

## 2.1 Tactical Profiles

| Aspect       | AEL (Primary)                       | Claude Code                   | claude-omlx                         |
| ------------ | ----------------------------------- | ----------------------------- | ----------------------------------- |
| Execution    | Automated Ralph Loop                | Manual                        | Manual                              |
| Inference    | oMLX → Devstral (local)             | Anthropic API → Claude Sonnet | oMLX → Devstral via Claude Code CLI |
| Loop control | `orchestrator.py`                   | Human operator                | Human operator                      |
| Context file | `ai/context.md`                     | `CLAUDE.md` (project root)    | `CLAUDE.md` (project root)          |
| Profile      | `mlx_devstral_small_2_2512_6bit.md` | `claude-code.md`              | `claude-omlx.md`                    |

[Return to Table of Contents](<#table of contents>)

---

## 2.2 Monitoring Tools

**govwatch** — a standalone read-only TUI that monitors a downstream project's
governance state at runtime. Run from the project root:

```bash
python ai/src/govwatch.py
```

Provides: inferred workflow phase, two-tier compliance alerts (coupling
violations, `tactical_brief` validity, naming convention), document registry
grouped by UUID, and an alert summary emitted to `ai/dashboard-alerts.md` and
the clipboard (`C` key).

See `ai/doc/guide-govwatch.md` for full operational detail.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Responsibilities

The Strategic Domain owns the following functions:

**Planning**

- Requirements elicitation (P11)
- Three-tier design hierarchy: master → domain → component (P12)
- Name registry maintenance

**Execution Coordination**

- T03 prompt authoring and AEL command delivery (P13)
- Context budget check before every AEL-targeted T03 prompt
- Human handoff: ready-to-execute command after approval

**Quality**

- Code review after AEL `SHIP` (or Claude Code completion)
- Test documentation and pytest generation (P15)
- Configuration audit against design baseline (P02)

**Issue Management**

- T06 issue creation from failed tests or AEL `BLOCKED` (P03)
- T07 change document creation from issues (P04)
- Issue–change one-to-one coupling enforcement

**Governance**

- Traceability matrix updates at every phase transition (P01)
- Document lifecycle management: active → closed (P00.14)
- Open-work register maintenance: `ai/task.md` (P00.20)
- Git commit after every iteration increment

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Workflow

Condensed stage sequence. See `workflow.md` for the full flowchart.

```
P10  Project Initialization  →  configure config.yaml
P11  Requirements            →  human approval → baseline
P12  Design (Tier 1–3)       →  human approval per tier → git tag baseline
P13  T03 Prompt              →  query omlx_model_status → human approval
     Human selects execution option:
       Option A: human runs AEL terminal command (all profiles)
       Option B: Strategic Domain calls start_ael / polls ael_status
                 (Claude Desktop + ael-mcp only)
       Option C: Claude Code manual invocation (claude_code/claude_omlx profiles)
     Options A/B (AEL)  →  SHIP or BLOCKED
     Option C (Claude Code)  →  human-directed execution (no loop)
       SHIP / complete  →  P02 code review → P15 test → progressive validation
       BLOCKED          →  P03 issue → P04 change → P13 new prompt
P15  Tests pass              →  human acceptance
P00  Close documents         →  move to closed/ → git commit → AEL reset
```

[Return to Table of Contents](<#table of contents>)

---

## 4.1 Audit Modes

Two audit modes serve P02 (governance P02). The operator selects by trigger phrase.

| Mode | Trigger | Actor | Procedure |
|---|---|---|---|
| Strategic | "conduct a strategic audit" | Claude Desktop | Read source via MCP, reason holistically, author `audit-<uuid>-<name>.md` (T08) inline |
| Tactical | "conduct a tactical audit" | AEL audit loop | Prepare `audit-uml.md` + `audit-index.md` + audit T03 prompt; human approval; launch per `ai/doc/guide-audit-loop.md` |

Strategic favours frontier judgement: architecture, protocol and name-registry
conformance, traceability. Tactical favours exhaustive per-item coverage and
unattended runtime (`--duration`). The orchestrator selects the audit recipe
pair automatically when `audit-index.md` is present in the state directory. If
the requested mode is unclear, ask before proceeding.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Protocol Reference

| Protocol | Name | Key Action |
|---|---|---|
| P00 | Governance | Master directives, architecture, document conventions |
| P10 | Project Initialization | Folder structure, `.gitignore`, venv, `config.yaml` |
| P12 | Design | Three-tier hierarchy, name registry, Mermaid diagrams |
| P04 | Change | T07 from T06 issue; one-to-one coupling; trivial exemption |
| P03 | Issue | T06 from test failure or `BLOCKED`; issue–change coupling |
| P01 | Trace | Traceability matrix updates at every phase boundary |
| P15 | Test | T04 docs, pytest generation, progressive validation |
| P14 | Quality | Code validation, automated audits via AEL hooks |
| P02 | Audit | Strategic or tactical audit (§4.1); findings → issues (P03) |
| P13 | Prompt | T03 authoring, `tactical_brief`, AEL command delivery |
| P11 | Requirements | T01 elicitation before design; baseline before Tier 1 |

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Document Conventions

### 6.1 Naming

| Pattern | Example |
|---|---|
| Master (singleton) | `design-<project>-master.md` |
| All other documents | `<class>-<8-hex-uuid>-<name>.md` |

Document classes: `design`, `change`, `issue`, `prompt`, `test`, `result`,
`audit`, `trace`, `requirements`.

**Exempt:** `ai/task.md` (open-work register) carries no UUID and no
lifecycle state — see P00.20.

**UUID propagation:** The first document created in a workflow cycle (issue or
change) generates the UUID. All coupled documents inherit it.

**Iteration:** Increments when a document re-enters a cycle after failure.
Both coupled documents (issue + change) increment together. Git commit
required after each increment.

### 6.2 Lifecycle

| State | Location | Mutability |
|---|---|---|
| Active | `ai/workspace/<class>/` | Mutable |
| Closed | `ai/workspace/<class>/closed/` | Immutable |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Constraints

**Forbidden**

- Creating, modifying, or deleting source code or documents without explicit
  human request (both domains).
- Exceeding the Tactical Domain context budget when authoring T03 prompts.
- Issuing an AEL command when `tactical_brief` is empty.

**Context Budget**

- Before authoring any AEL-targeted T03 prompt (prompt_info.target_profile:
  ael), call `omlx_model_status` (mcp_omlx) for the configured model; a null
  or missing `settings.max_context_window` is unresolved — warn the operator,
  same as the resolver's own unknown-window behavior.
- Read `context-budget.md` (written automatically by the orchestrator at AEL
  runtime) before sizing `tactical_brief` (~200–400 tokens target).

**`tactical_brief` Format**

- Must be a ` ```yaml ` fenced block with `tactical_brief:` as the root key.
- Plain text blocks are not detected by the orchestrator.

**Trivial Change Exemption (P04.12)**

- Qualifies only when both trivial AND surgical, and all five criteria met:
  single function, ≤20 line delta, no interface changes, unambiguous,
  human-approved.
- Exempt from T06 → T07 → T03 → AEL. Git commit is the sole audit record.

**Change Documentation Scope**

- Full issue/change/prompt workflow applies to `src/` changes only.
- `ai/workspace/` document changes may be made directly after human approval.

**Initial Implementation**

- First-time source code implementation from an approved design does not require issue or change documents.
- Forward path: approved design → T03 prompt → execution → review.
- The T06 → T07 corrective loop is triggered only by AEL `BLOCKED` or test failure.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Templates

All templates reside in `ai/templates/`. Read the template before creating
any document.

| Template | Document Class | Location |
|---|---|---|
| T02 | Design | `ai/templates/T02-design.md` |
| T07 | Change | `ai/templates/T07-change.md` |
| T06 | Issue | `ai/templates/T06-issue.md` |
| T03 | Prompt | `ai/templates/T03-prompt.md` |
| T04 | Test | `ai/templates/T04-test.md` |
| T05 | Result | `ai/templates/T05-result.md` |
| T01 | Requirements | `ai/templates/T01-requirements.md` |
| T08 | Audit | `ai/templates/T08-audit.md` |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-04-27 | Initial draft |
| 0.2 | 2026-04-28 | Added ael-mcp to §2.0 Architecture; annotated §4.0 Workflow AEL step with Option A/B |
| 0.3 | 2026-04-30 | Added §2.1 Tactical Profiles with comparison table |
| 0.4 | 2026-06-10 | Added §2.2 Monitoring Tools (govwatch) |
| 0.5 | 2026-06-14 | Relocated framework paths under ai/: workspace/ → ai/workspace/, state .ael/ralph/ → ai/state/ralph/, govwatch output → ai/dashboard-alerts.md |
| 0.6 | 2026-06-16 | Updated §2.1 profile filename reference: mlx_devstral_small_2_2512_Q8.md → mlx_devstral_small_2_2512_6bit.md |
| 0.7 | 2026-06-17 | Aligned with docs/claude/primer.md (canonical): code spans for governance.md, workflow.md, SHIP, BLOCKED, .gitignore, budget.py, tactical_brief throughout; Prime Directive bolded; ael-mcp bold extent corrected; §6.0 restructured with §6.1 Naming and §6.2 Lifecycle subsections; colon positions in UUID propagation and Iteration headings; blank lines before bullet lists in §3.0 and §7.0; tactical_brief Format and Trivial Change Exemption heading formats |
| 0.8 | 2026-06-17 | §2.0: added context file to AEL description; §2.1: added Context file row to profile comparison table |
| 0.9 | 2026-06-25 | Added §7.0 Initial Implementation constraint: initial implementation from approved design does not require issue/change documents; forward path and corrective loop trigger made explicit |
| 0.10 | 2026-06-28 | Added §4.1 Audit Modes (strategic / tactical triggers); noted automatic audit-recipe selection; updated §5.0 P08 row; added T08 Audit to §8.0 template table |
| 0.11 | 2026-07-02 | Rescoped §3.0 and §7.0 context-budget directives to AEL-targeted T04 prompts only (prompt_info.target_profile field; issue-713437bc) |
| 0.12 | 2026-07-08 | §4.0/§5.0/§7.0: replaced retired `budget.py` file-existence gate with direct `omlx_model_status` (mcp_omlx) query before authoring AEL-targeted T04 prompts; `context-budget.md` now written automatically by the orchestrator at AEL runtime (change-d42e64a9) |
| 0.13 | 2026-08-19 | Synced with governance v9.13: added Option C (Claude Code manual invocation) to §2.0 alongside Options A/B; corrected stale `ai/profiles/claude.md` → `ai/profiles/claude-code.md` reference in §2.0 and §2.1; flattened §4.0 workflow block to present Options A/B/C as one selection set, matching governance §1.10.3 structure |
| 0.14 | 2026-08-21 | Synced with governance v9.16: added §3.0 Governance bullet for `ai/task.md` open-work register maintenance (P00 §1.1.20); added §6.1 exemption note for `ai/task.md` |

---

Copyright (c) 2026 William Watson. MIT License.
