Created: 2026 June 10

# govwatch — Operational Guide

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Installation](<#2.0 installation>)
[3.0 Invocation](<#3.0 invocation>)
[4.0 Panels](<#4.0 panels>)
[5.0 Key Bindings](<#5.0 key bindings>)
[6.0 Phase Inference Reference](<#6.0 phase inference reference>)
[7.0 Alert Codes Reference](<#7.0 alert codes reference>)
[8.0 dashboard-alerts.md](<#8.0 dashboard-alerts.md>)
[9.0 Common Issues](<#9.0 common issues>)
[Version History](<#version history>)

---

## 1.0 Purpose

`govwatch` is a read-only governance monitoring TUI for downstream projects. It
infers the current workflow phase, runs a compliance scan over open workspace
documents, lists open documents grouped by UUID, and emits an alert summary to
`ai/dashboard-alerts.md` and (on request) the clipboard.

Run it from a downstream project root at any point during a development cycle.
It writes nothing except `ai/dashboard-alerts.md`.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Installation

`govwatch` is propagated to downstream projects via `bin/sync-skel.sh` and
`bin/propagate.sh`. The module resides at `ai/src/govwatch.py`.

Install dependencies from the project root:

```bash
pip install -r ai/src/requirements-govwatch.txt
```

Dependencies: `textual`, `rich`.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Invocation

Run from the project root:

```bash
python ai/src/govwatch.py
```

| Argument | Default | Purpose |
|---|---|---|
| `--project PATH` | current working directory | Override the project root |
| `--interval N` | `5` | Polling interval in seconds |

govwatch validates that `ai/workspace/` exists under the project root on startup.
If not found, it prints a diagnostic and exits non-zero without entering the TUI.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Panels

The TUI renders three panels side by side.

### 4.1 Workflow State

Shows the inferred workflow phase (see §6.0), AEL status and iteration derived
from `ai/state/ralph/` state files, and context budget status derived from
`ai/state/ralph/context-budget.md`.

Colour coding: green = active/ok, yellow = warning, red = blocked/abort,
dim = idle/unknown.

### 4.2 Compliance Alerts

Lists all VIOLATION and WARNING alerts from the current scan, coloured red and
yellow respectively. The panel footer shows the last-scan timestamp and total
VIOLATION / WARNING counts. See §7.0 for alert codes.

### 4.3 Document Registry

Lists all open (non-closed) governance documents, grouped by UUID. Each group
shows the document class and filename alongside a parse status indicator
(`✓` or `!`). Open issues are listed separately as a to-do reference.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Key Bindings

| Key | Action |
|---|---|
| `C` | Copy the alert summary to the clipboard |
| `R` | Force an immediate scan refresh |
| `Q` | Quit |

The clipboard payload is identical to `dashboard-alerts.md` content. Paste it
into Claude Desktop for Strategic Domain review.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Phase Inference Reference

Phase is derived from open documents and AEL state. Precedence is top-down;
the first matching condition wins.

| Priority | Condition | Phase |
|---|---|---|
| 1 | AEL status is `running` | Tactical execution |
| 2 | Open prompt (T04) present; AEL idle or ship | Awaiting prompt execution |
| 3 | Open change (T02) and issue (T03) present; no open prompt | Change cycle |
| 4 | Open issue (T03) present; no open change | Issue raised |
| 5 | Open test (T05) or result (T06) present | Test phase |
| 6 | No open documents | Idle |

Conditions 2–6 evaluate only over open (non-`closed/`) documents.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Alert Codes Reference

### 7.1 Tier 1 — Filename and Structure

| Code | Severity | Condition |
|---|---|---|
| FR-02-01 | VIOLATION | Change document has no coupled issue sharing its UUID |
| FR-02-02 | WARNING | Issue document has no coupled change sharing its UUID |
| FR-02-03 | VIOLATION | Prompt document has no coupled change sharing its UUID (skipped for design-sourced prompts, §1.4.1) |
| FR-02-04 | WARNING | Filename does not match governance naming convention |
| FR-02-05 | WARNING | AEL reports SHIP but open documents remain |
| FR-02-06 | WARNING | AEL `task.md` does not reference any open prompt document |
| FR-02-07 | WARNING | `context-budget.md` absent while an AEL-targeted prompt document is open |

### 7.2 Tier 2 — Document Content

| Code | Severity | Condition |
|---|---|---|
| FR-02-08 | VIOLATION | Coupled change/issue iteration numbers differ |
| FR-02-09 | VIOLATION | Body `id` UUID differs from filename UUID |
| FR-02-10 | VIOLATION | Prompt `tactical_brief` absent, empty, or placeholder (only when target_profile is ael or absent) |
| FR-02-11 | WARNING | Issue missing required fields |
| FR-02-12 | WARNING | Change missing required fields |

### 7.3 Parse and Internal

| Code | Severity | Condition |
|---|---|---|
| PARSE-WARN | WARNING | Document could not be fully parsed |
| WRITE-WARN | WARNING | `dashboard-alerts.md` write failed |
| CE-T1-ERR | WARNING | Tier 1 check raised an unexpected error |
| CE-T2-ERR | WARNING | Tier 2 check raised an unexpected error |

[Return to Table of Contents](<#table of contents>)

---

## 8.0 dashboard-alerts.md

govwatch overwrites `ai/dashboard-alerts.md` on every scan
cycle. It is the only file govwatch writes. The format is plain markdown:

```
# govwatch alerts — <project name>

Scan: <ISO timestamp>
Phase: <phase>
AEL: <status> [iteration N]
Budget: <ok|warn|abort|unknown>

## Violations (<count>)
- [<code>] <message> (<document>)

## Warnings (<count>)
- [<code>] <message> (<document>)
```

Sections with no entries show `none`. Add `ai/dashboard-alerts.md` to the project
`.gitignore` — it reflects transient state and changes on every scan.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Common Issues

| Symptom | Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: No module named 'textual'` | Dependencies not installed | `pip install -r ai/src/requirements-govwatch.txt` |
| `ai/workspace/ not found` startup error | Wrong working directory or `--project` path | Run from the project root or pass `--project <path>` |
| `C` key shows "Copy error" | `pbcopy` not available | macOS only; not applicable on other platforms |
| `WRITE-WARN` in Compliance Alerts | `dashboard-alerts.md` not writable | Check file permissions in the project root |
| FR-02-04 for legacy filenames | Old freeform documents predate UUID convention | Expected; no action required unless remediation is desired |
| AEL status shows `idle` when AEL is running | `ai/state/ralph/` absent or state files not yet written | Normal at startup; refreshes on next poll cycle |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-10 | Initial guide |
| 1.1 | 2026-06-14 | Updated paths for ai/ consolidation: output ai/dashboard-alerts.md, state ai/state/ralph/, validates ai/workspace/ |
| 1.2 | 2026-07-02 | §7.1/§7.2: FR-02-03 skipped for design-sourced prompts, FR-02-07/FR-02-10 scoped to AEL-targeted prompts (issue-713437bc) |

---

Copyright (c) 2026 William Watson. MIT License.
