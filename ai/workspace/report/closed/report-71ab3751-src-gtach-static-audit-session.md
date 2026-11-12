# Session Report — Static Audit of src/gtach (71ab3751)

Created: 2026 November 11

## Table of Contents

- [1.0 Purpose](#10-purpose)
- [2.0 Session Record](#20-session-record)
- [3.0 Results](#30-results)
- [4.0 Corrections Made During the Session](#40-corrections-made-during-the-session)
- [5.0 Assessment of the Application](#50-assessment-of-the-application)
- [6.0 Limitations](#60-limitations)
- [7.0 Artefacts and Open Items](#70-artefacts-and-open-items)
- [Version History](#version-history)

---

## 1.0 Purpose

This report records the planner session of 2026-11-10 and 2026-11-11 that produced `audit-71ab3751`. It states what was requested, what was done, what was found, and what remains open. The audit report is the authoritative record of the findings; this document does not repeat them in full.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Session Record

| Step | Request | Action | Output |
|---|---|---|---|
| 1 | Static source audit of all code in `src/gtach`, primarily for bugs and defects | Read the primer, README, T08 template and prior audits. Read all 60 Python files (19,998 lines) in full at commit `94ce959b`. Traced thread lifecycle, shutdown, setup, reconnect and touch paths. Ran `compileall` and mypy on a copy. | `audit-71ab3751-src-gtach-static.md` v1.0: 31 findings (3 medium, 28 low) |
| 2 | Review the open scheduled daily audits and integrate valid findings | Re-checked every finding and observation of `audit-005f1cf4`, `audit-8264c76d`, `audit-008e2929` and `audit-fccd5931` against the audited commit. Read the cited `bin/` and `tests/` locations. | Audit v1.1: 43 findings (4 medium, 39 low); new §5.0 dispositions |
| 3 | Opinion of the application | Given in conversation; summarised in [5.0](#50-assessment-of-the-application) | — |
| 4 | Session report and remediation proposal | This report and `proposal-71ab3751-audit-remediation-and-simplification.md` | Two documents |

No source file, test, script or governance document was changed. `ai/task.md` was not changed.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Results

### 3.1 Findings

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 0 |
| Medium | 4 |
| Low | 39 |
| **Total** | **43** |

Medium findings:

- **A01:** a connect that completes after `disconnect()` leaves an open RFCOMM link (`comm/transport.py`). The race is confirmed; the EBUSY consequence is suspected.
- **D01:** discovery outcomes are not presented; an empty scan repeats without feedback and the designed "No devices found" state is unreachable.
- **A02:** the serial transport does not recover from a removed device (suspected).
- **C08:** the stored-device probe acts after the operator has left the screen (from `audit-005f1cf4` §4.0).

Distribution of the 43 findings: comm 11, core and top level 6, display top level 9, display subfolders 4, utils 6, tests 3, bin 3, cross-cutting 1.

### 3.2 Tooling

- `compileall`: all 60 files compile.
- mypy 2.3.1 with `--check-untyped-defs`: no issues.
- flake8, bandit and pytest were not run; the analysis environment had no package index access.

### 3.3 Scheduled audits

- 13 findings were added from the four scheduled audits and 3 existing findings were extended.
- `audit-008e2929` F1 and most of `audit-005f1cf4` §13.0 were found resolved.
- All valid content of the four audits is now carried by `audit-71ab3751`. They were not moved to `closed/`.

### 3.4 Efficiency observations

Five observations (O1 to O5) were recorded outside the finding count. The one with the largest expected effect is O1: the root logger is fixed at DEBUG, so every `logger.debug` call creates a record with debug off.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Corrections Made During the Session

- **B05 withdrawn.** Version 1.0 reported timed waits on the wall clock (`app.py:594` and several joins) as a defect. This was wrong. change-4f671d09 excluded those sites deliberately, and its reasoning for `app.py:594` holds: `Event.set()` wakes the waiter regardless of the clock. The error was found while validating an observation in `audit-008e2929`.
- **psutil.** An intermediate note that psutil was declared required but unused was discarded before publication; `display/performance/monitor.py` imports it.
- **Count.** The first v1.1 text stated 12 added findings; the correct number, 13, was written before the session's summary was given.
- **G01 re-rated.** `audit-005f1cf4` §5.0 was rated medium there and low in the integrated report, because the script verifies a closed audit and the `main.py` cause is already in `ai/task.md`.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Assessment of the Application

This is a judgement from reading the source, not from operating the device.

Strengths:

- The failure-handling design is sound: capture-then-use handle discipline, the `drop_link` and `disconnect` separation, recovery by process restart, and the exit backstop.
- Uncertain link states resolve to "disconnected", so a stale reading is not presented as live.
- No critical or high defect was found. The medium findings lie on the setup and reconnect edges, not in the steady-state gauge path.
- Decisions are traceable to issues in the code.

Weaknesses:

- **W1 — Size.** A substantial share of the code is unused scaffolding. The estimate of a quarter to a third of `src/gtach` is a reading impression; it was not measured.
- **W2 — Setup flow structure.** State is spread over four components and running operations cannot be cancelled. Findings D01, C01, C08, X01 and D02 follow from this structure.
- **W3 — Comment volume and staleness.** History comments outweigh code in places and some are stale (A11, B02, B06, E02).
- **W4 — `display/manager.py`.** At 2,690 lines it combines rendering, touch registration, options logic and update handling.

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Limitations

- Static review only. Nothing was verified on the Pi; five findings are marked suspected (A01 consequence, A02, A06, A12, C07).
- pygame, pyserial, PyBluez and hyperpixel2r were not installed; statements about their behaviour rest on documentation and recall.
- `tests/` and `bin/` were read only at the locations cited by the scheduled audits.
- The T08 YAML block in the audit report was written by hand and was not parsed by a YAML tool.
- Line numbers were taken from a working copy of the audited commit and spot-checked, not all re-verified.

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Artefacts and Open Items

### 7.1 Artefacts

| Document | Location | Git |
|---|---|---|
| Audit report v1.1 | `ai/workspace/audit/audit-71ab3751-src-gtach-static.md` | Tracked |
| This report | `ai/workspace/report/report-71ab3751-src-gtach-static-audit-session.md` | Tracked |
| Proposal | `ai/workspace/proposal/proposal-71ab3751-audit-remediation-and-simplification.md` | Tracked since 2026-11-11 |

### 7.2 Open items

1. Decide on the proposal, including its decision points.
2. Close the four scheduled audits as superseded, or keep them active.
3. Verify the suspected findings on the device (audit §6.0).
4. `ai/task.md` does not yet reference `audit-71ab3751`.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial report |
| 1.1 | 2026-11-11 | §7.1: proposal is tracked in git since the `.gitignore` change of 2026-11-11 |

---

Copyright (c) 2026 William Watson. MIT License.
