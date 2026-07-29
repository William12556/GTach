Created: 2026 July 29

# Task List

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Source Verification Method](<#2.0 source verification method>)
[3.0 Completed](<#3.0 completed>)
[4.0 Open](<#4.0 open>)
[5.0 Requires Live-Device Verification](<#5.0 requires live-device verification>)
[6.0 Deferred by Design](<#6.0 deferred by design>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document lists unfinished work. Version 1.0 was built from `ai/workspace`
document state alone. Version 2.0 cross-checked each item against
`src/gtach`. Version 3.0 corrected a misstatement in 2.0. This revision
(4.0) closes the `comm/` transport layer audit following log-based root
cause analysis.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source Verification Method

`mcp-grep` searches of `src/gtach` for the specific symbols named in each
governance document's deliverable/success-criteria sections, plus
`pyproject.toml` version and `directory_tree` for file presence/absence.
`pyproject.toml` reports `version = "0.2.64"` — one increment past the
`0.2.63` baseline recorded in `issue-b7e3f90a`, consistent with unrecorded
work having landed. Section 3.5 additionally draws on
`ai/state/ralph/ael_20260617-131721.LOG`, the AEL execution log for the
run in question.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Completed

All items below are verified and their governance documents are closed.
No further action required.

### 3.1 ✅ COMPLETE — `b7e3f90a` — Dead code cleanup

| Item | Verification |
|---|---|
| `core/watchdog_enhanced.py` | absent — deleted |
| `display/hardware_interface.py` | absent — deleted |
| `display/ui_testing_framework.py` | absent — deleted |
| `display/enhanced_touch_factory.py` | absent — deleted |
| `display/performance.py` (flat file) | absent; `performance/` package remains — deleted |
| `display/components/` | absent — deleted |
| `utils/services/` | absent — deleted |
| `assets/fonts/BebasNeue-Regular.ttf` | absent — deleted |
| `AsyncSyncBridge` + dead `ThreadManager` API in `core/thread.py` | zero hits — removed |
| `ConfigManager.setup_logging` group in `utils/config.py` | zero hits — removed |

Governance documents moved to `issues/closed/`, `change/closed/`,
`prompt/closed/`.

### 3.2 ✅ COMPLETE — `f993f871` — OPTIONS update check/install

| Requirement | Verification |
|---|---|
| `src/gtach/utils/updater.py` | present, pure stdlib |
| `_restart_callback`, `_options_view`, `_draw_update_view`, `_on_check_updates` in `display/manager.py` | present, matches deliverable |
| `GTachApplication._request_restart()` + wiring in `app.py` | present at both call sites |
| `gtach.service` `Restart=always` | confirmed, `bin/gtach.service:13` |

Consistent with `README.md` §3.1/§4.2, which documents the resulting
update-menu workflow. Governance documents moved to `issues/closed/`,
`change/closed/`, `prompt/closed/`.

### 3.3 ✅ COMPLETE — UI Navigation Logic audit — Findings A and B

**Correction to the prior (2.0) revision of this document**: it stated no
governance documents existed for these findings. That was incorrect —
both have full closed issue/change/prompt cycles already in
`ai/workspace/*/closed/`:

- **Finding A** (stale `OPTIONS` mode after re-pair) → `issue-c84ffe6f-stale-options-mode-after-setup-reentry.md`
  / `change-c84ffe6f` / `prompt-c84ffe6f`. Fix verified: `DisplayManager.exit_setup_mode()`
  (`manager.py:1494–1498`) sets `self.config.mode = self._post_splash_mode`
  on exit.
- **Finding B** (non-indicating simulation toggle) → `issue-85cc0241-simulation-toggle-not-state-indicating.md`
  / `change-85cc0241` / `prompt-85cc0241`. Fix verified: button label at
  `manager.py:932` is `"Simulation mode" if self._sim_mode else "Bluetooth"`.

Both cycles were already closed prior to this review; no action required.

### 3.4 ✅ COMPLETE — Splash Screen Debug Session audit — Defects 1–4

`audit-splash-hang-debug-session-state-report.md` (2026-04-30), all four
defects qualified for the Trivial Change Exemption (§P03 §1.4.12) — git
commit history is the audit record, no T03/T02/T04 required. Source
confirms all four corrected:

| Defect | Verification |
|---|---|
| 1 — `DisplayMode.ACKNOWLEDGEMENT` missing | present, `display/models.py:68` |
| 2 — `_ack_state_manager` never initialized | imported and instantiated, `display/manager.py:54,117` |
| 3 — `rpm_bands`/`engine_profile` missing from `DisplayConfig` | both present, `display/models.py:101,104` |
| 4 — heartbeat key mismatch for `setup` thread | `setup.py:135` registers `'setup'` before `update_heartbeat('setup')` |

### 3.5 ✅ COMPLETE — `comm/` transport layer audit (`b4e8c012` / `2f612d17` / `a4c8e2f1`)

Resolved by inspecting `ai/state/ralph/ael_20260617-131721.LOG`, the AEL
execution log for the 2026-06-17 audit-continuation run launched by
`prompt-a4c8e2f1-comm-audit.md`.

**Finding**: the audit genuinely completed all 20 items. The log shows the
worker correctly building `audit-report.md` via targeted `edit` calls that
append each new section without disturbing prior ones — by loop iteration
5 the file already held correctly-preserved findings for `pairing.py` (×3),
`obd.py` (×3), `system_bluetooth.py` (×2), and `rfcomm.py::connect`. The
`audit-index.md`'s all-`[x]` state is genuine, not a false completion mark.

**What went wrong**: the copy of `audit-report.md` that reached
`ai/workspace/audit/` as `audit-b4e8c012-report.md` holds only 6 of the 20
sections — and they are the *last* 6 items in audit order (`sim_transport.py`
×2, `transport.py`, `device_store.py`, `models.py`, `sim_bluetooth.py`),
not the first 6. This pattern is consistent with a late-loop overwrite or a
truncated copy during the `workspace/` → `ai/workspace/` migration, not
with the work never having been done. The original state files
(`audit-index.md`, `audit-report.md`) no longer exist in
`ai/state/ralph/` to re-derive the complete report from directly; that
directory has since been reused for unrelated AEL test runs.

**Resolution (accepted 2026-07-29)**: closed on the strength of the index
and log evidence. The full 20-item findings text remains recoverable from
the log's `write`/`edit` tool-call payloads if a complete report is wanted
later — not undertaken here.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Open

### 4.1 ☐ OPEN — `faulthandler` output not captured in app-owned log files under systemd

`app.py:42–44` confirms `faulthandler.dump_traceback_later(15, repeat=True, file=sys.stderr)`
still targets `sys.stderr`. Under systemd, `stderr` goes to the journal
(`journalctl -u gtach`), not `/opt/gtach/debug.log` or `start.log`. No fix
scoped.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Requires Live-Device Verification

### 5.1 ☐ UNVERIFIED — Splash audit §4.3 — WELCOME screen touch-unresponsiveness

The splash audit's root-cause investigation into the touch-routing chain
(`HyperPixelTouchInterface` → `TouchHandler` → `SetupDisplayManager`) was
left unresolved pending live testing. Static review cannot confirm current
behaviour. §3.4's Defects 1–4 are now fixed, and the audit itself
speculated this symptom might resolve once those defects were corrected —
on-device testing is needed to confirm.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deferred by Design

### 6.1 — UI Navigation audit — Finding C (terminology)

Overlap between the display-layer `_sim_mode` flag and the launch-time
simulated transport. The audit report explicitly defers this to
consensus rather than treating it as a fix (§6.3, §7.0 of that report).
Not a defect; listed here only so it is not lost.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial task list from `ai/workspace` state review. |
| 2.0 | 2026-07-29 | Cross-checked every item against `src/gtach`. Reclassified `b7e3f90a`, `f993f871`, UI-nav Findings A/B, and splash-hang Defects 1–4 as implemented in source. |
| 3.0 | 2026-07-29 | Corrected 2.0's claim that no governance documents existed for UI-nav Findings A/B — both have closed issue/change/prompt cycles (`c84ffe6f`, `85cc0241`). Recorded closure of `b7e3f90a` and `f993f871`. Restructured into Completed / Open / Requires Live-Device Verification / Governance Record Inconsistency / Deferred by Design, with explicit ✅/☐ status markers. Added `comm/` audit clarification re: `prompt-a4c8e2f1`. |
| 4.0 | 2026-07-29 | Diagnosed the `comm/` audit inconsistency via `ael_20260617-131721.LOG`: all 20 items were genuinely audited; only the copied report was truncated. Accepted as resolved per human decision; moved from "Governance Record Inconsistency" into Completed (§3.5); governance documents moved to `closed/`. |

---

Copyright (c) 2026 William Watson. MIT License.
