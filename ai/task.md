Created: 2026 July 29

# Task List

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Active Governance Cycles](<#2.0 active governance cycles>)
[3.0 Audit — Unresolved Findings](<#3.0 audit — unresolved findings>)
[4.0 Audit — State Requiring Verification](<#4.0 audit — state requiring verification>)
[5.0 Noted Open Items](<#5.0 noted open items>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document lists unfinished work identified by a review of `ai/workspace`
on 2026-07-29. It is a status index, not a governance document. Item status
is stated factually; no priority ranking is implied beyond section grouping.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Active Governance Cycles

Documents present in `<class>/` (not `<class>/closed/`) with an approved
change document but no evidence of Claude Code execution or closure.

### 2.1 `b7e3f90a` — Dead code cleanup

- Issue, change, and prompt documents present and approved.
- Scope: delete seven dead files/packages, remove `AsyncSyncBridge` and
  four dead `ThreadManager` methods from `core/thread.py`, remove
  `setup_logging` group from `utils/config.py`, remove unused font asset.
- Status: **not yet executed**. No closure or verification evidence found.
- Supporting report: `ai/workspace/report/dead-code-report.md`.

### 2.2 `f993f871` — OPTIONS update check/install

- Issue, change, and prompt documents present and approved.
- Scope: new `utils/updater.py`; `DisplayManager` OPTIONS sub-state machine
  with a fourth "Check for updates" button; `GTachApplication._request_restart()`;
  `gtach.service` `Restart=always`.
- Status: **documentation state is inconsistent with deployed state.**
  `README.md` (v2.3, 2026-06-19) already documents `deploy.sh --stage` and
  "install via GTach update menu" as available functionality, implying this
  change has shipped. The governance triple remains active/unclosed. Verify
  against `src/gtach/utils/updater.py`, `src/gtach/display/manager.py`, and
  `gtach.service` on the Mac and/or Pi, then close the documents if
  implementation is confirmed present.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Audit — Unresolved Findings

Findings from closed-scope audits that identified defects but have no
corresponding issue/change/prompt cycle.

### 3.1 UI Navigation Logic (`audit-ui-navigation-logic-report.md`, 2026-05-29)

- **Finding A** (priority 1): stale `OPTIONS` mode persists after setup
  re-entry via "Clear settings"; connected screen renders as the options
  screen instead of the radial/digital screen.
- **Finding B** (priority 2): simulation toggle button is not
  state-indicating; label does not reflect current `_sim_mode` or
  destination mode.
- **Finding C** (priority 3): terminology overlap between the display-layer
  simulation flag and the launch-time simulated transport — design decision,
  not yet raised as an issue.
- Status: **no T03 issues raised** for Findings A or B as of this review.

### 3.2 Splash Screen Debug Session (`audit-splash-hang-debug-session-state-report.md`, 2026-04-30)

- Defects 1–3 (critical): missing `DisplayMode.ACKNOWLEDGEMENT` enum value;
  `_ack_state_manager` never initialized in `DisplayManager`; `rpm_bands`
  and `engine_profile` missing from `DisplayConfig`. All three qualify for
  the Trivial Change Exemption per the report.
- Defect 4 (low): `ThreadManager` heartbeat key mismatch for the `setup`
  thread.
- §4.3: root cause of the WELCOME-screen touch-unresponsiveness hang not
  confirmed; flagged as requiring live-device investigation.
- Status: **verify against current source** — this report is three months
  old relative to this review; other changes (including `f2c8a3e7` macOS
  removal) have landed since. Confirm which defects, if any, remain before
  acting.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Audit — State Requiring Verification

### 4.1 `comm/` transport layer audit (`b4e8c012` / `2f612d17` / `a4c8e2f1`)

- `audit-b4e8c012-index.md` shows all 20 items marked `[x]` complete.
- `audit-b4e8c012-report.md` contains detailed findings for only 6 of the
  20 indexed items (`sim_transport.py` ×2, `transport.py::OBDTransport`,
  `device_store.py::DeviceStore`, `models.py::BluetoothDevice`,
  `sim_bluetooth.py::SimBluetoothPairing`).
- `prompt-a4c8e2f1-comm-audit.md` (dated 2026-06-17, same day as the index
  and report files) states 18 items remain unchecked — contradicting the
  index's all-checked state.
- Both index and report files carry identical filesystem creation
  timestamps (2026-06-17 15:41–15:42), consistent with a bulk copy during
  the `workspace/` → `ai/workspace/` migration rather than genuine
  completion activity.
- Status: **inconsistent record — origin unresolved.** Determine whether
  the remaining 14 items were audited and the report is merely incomplete,
  or whether the index was checked off without corresponding audit work,
  before treating this audit as closed.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Noted Open Items

Carried forward from prior sessions; not represented by workspace documents.

- `ConfigManager.setup_logging()` dead code — subsumed by `b7e3f90a` §2.1
  scope (Phase 3 / Phase 4 in the prompt document).
- `faulthandler` output not captured in app-owned log files under systemd.
- Three pre-existing `LLM-Governance-and-Orchestration` framework defects
  — not addressed; framework changes originate in that repository, not
  here.
- Duplicate-read pattern in the AEL worker model (same file read 3–5× per
  phase) — identified as a reliability signal under quantization; potential
  future recipe improvement, no issue raised.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial task list from `ai/workspace` state review. |

---

Copyright (c) 2026 William Watson. MIT License.
