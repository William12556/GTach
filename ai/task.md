Created: 2026 July 29

# Task List

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Source Verification Method](<#2.0 source verification method>)
[3.0 Implemented — Governance Closure Required](<#3.0 implemented — governance closure required>)
[4.0 Genuinely Open](<#4.0 genuinely open>)
[5.0 Requires Live-Device Verification](<#5.0 requires live-device verification>)
[6.0 Governance Record Inconsistency](<#6.0 governance record inconsistency>)
[7.0 Deferred by Design](<#7.0 deferred by design>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document lists unfinished work. Version 1.0 was built from `ai/workspace`
document state alone. This revision cross-checks each item against
`src/gtach` and corrects prior assumptions: most items recorded as "not yet
executed" were in fact already implemented in source, with the governance
record left open.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source Verification Method

`mcp-grep` searches of `src/gtach` for the specific symbols named in each
governance document's deliverable/success-criteria sections, plus
`pyproject.toml` version and `directory_tree` for file presence/absence.
`pyproject.toml` reports `version = "0.2.64"` — one increment past the
`0.2.63` baseline recorded in `issue-b7e3f90a`, consistent with unrecorded
work having landed.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Implemented — Governance Closure Required

Source confirms these are complete. No further code work identified;
remaining action is closing the governance documents (`mv` to `closed/`,
git commit) per §6.2 of `primer.md`.

### 3.1 `b7e3f90a` — Dead code cleanup

Verified against `change-b7e3f90a` / `prompt-b7e3f90a`:

| Item | Verification | Result |
|---|---|---|
| `core/watchdog_enhanced.py` | absent from tree | deleted |
| `display/hardware_interface.py` | absent from tree | deleted |
| `display/ui_testing_framework.py` | absent from tree | deleted |
| `display/enhanced_touch_factory.py` | absent from tree | deleted |
| `display/performance.py` (flat file) | absent; `performance/` package remains | deleted |
| `display/components/` | absent from tree | deleted |
| `utils/services/` | absent from tree | deleted |
| `assets/fonts/BebasNeue-Regular.ttf` | absent; only `Michroma-Regular.ttf` present | deleted |
| `AsyncSyncBridge`, `get_statistics`, `list_threads`, `get_thread_info`, `is_healthy`, `_sync_timing`, `_operation_count`, `_sync_overhead_start` in `core/thread.py` | zero grep hits in `core/thread.py` | removed |
| `ConfigManager.setup_logging`, `_setup_production_logging`, `_setup_debug_logging`, `_log_pi_hardware_status` | zero hits; only the unrelated standalone `main.py::setup_logging()` remains | removed |

Status: **fully implemented.** Move `issue-b7e3f90a-dead-code-cleanup.md`,
`change-b7e3f90a-dead-code-cleanup.md`, `prompt-b7e3f90a-dead-code-cleanup.md`
to their respective `closed/` directories.

### 3.2 `f993f871` — OPTIONS update check/install

Verified against `prompt-f993f871` success criteria:

| Requirement | Verification | Result |
|---|---|---|
| `src/gtach/utils/updater.py` exists, pure stdlib | file present in tree | present |
| `_restart_callback`, `_options_view`, `_draw_update_view`, `_on_check_updates` in `display/manager.py` | all present, matching deliverable line content | present |
| `GTachApplication._request_restart()` and `_restart_callback` wiring in `app.py` | present at `app.py:165` and both call sites (`:181`, `:251`) | present |
| `gtach.service` `Restart=always` | `bin/gtach.service:13` reads `Restart=always` | present |

Status: **fully implemented**, consistent with `README.md` §3.1/§4.2, which
already documents the update-menu workflow. Close
`issue-f993f871-options-update-check-install.md`,
`change-f993f871-options-update-check-install.md`,
`prompt-f993f871-options-update-check-install.md`.

### 3.3 UI Navigation Logic audit — Findings A and B

`audit-ui-navigation-logic-report.md` (2026-05-29) recommended fixes with
no issue/change raised. Source shows both applied:

- **Finding A** (stale `OPTIONS` mode after re-pair): `DisplayManager.exit_setup_mode()`
  (`manager.py:1494–1498`) sets `self.config.mode = self._post_splash_mode`
  on exit — the exact remediation the report proposed as the preferred
  single-site fix (§6.1).
- **Finding B** (non-indicating simulation toggle): the button label at
  `manager.py:932` is now `"Simulation mode" if self._sim_mode else "Bluetooth"`
  — state-derived, not the static label the audit found.

Status: **implemented.** No governance documents exist to close for this
audit (informal, source-only per its own scope statement); no action
required beyond noting resolution.

### 3.4 Splash Screen Debug Session audit — Defects 1–4

`audit-splash-hang-debug-session-state-report.md` (2026-04-30) documented
four defects, all noted as qualifying for the Trivial Change Exemption.
Source confirms all four are corrected:

| Defect | Verification |
|---|---|
| 1 — `DisplayMode.ACKNOWLEDGEMENT` missing | present, `display/models.py:68` |
| 2 — `_ack_state_manager` never initialized | imported and instantiated, `display/manager.py:54,117` |
| 3 — `rpm_bands`/`engine_profile` missing from `DisplayConfig` | both present, `display/models.py:101,104` |
| 4 — heartbeat key mismatch for `setup` thread | `setup.py:135` now calls `register_thread('setup', ...)` before `update_heartbeat('setup')` |

Status: **implemented.** Trivial Change Exemption applied per the audit's
own §5.2 — git commit history is the audit record; no T03/T02/T04 required.
No further action beyond noting resolution.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Genuinely Open

### 4.1 `faulthandler` output not captured in app-owned log files under systemd

`app.py:42–44` confirms `faulthandler.dump_traceback_later(15, repeat=True, file=sys.stderr)`
is still targeting `sys.stderr`, not an app-owned log file. Under systemd,
`stderr` goes to the journal (`journalctl -u gtach`), not
`/opt/gtach/debug.log` or `start.log`. This limitation is confirmed still
present in source. No fix scoped.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Requires Live-Device Verification

### 5.1 Splash audit §4.3 — WELCOME screen touch-unresponsiveness

The splash audit's root-cause investigation into the touch-routing chain
(`HyperPixelTouchInterface` → `TouchHandler` → `SetupDisplayManager`) was
left unresolved pending live testing. Static review cannot confirm current
behaviour. Given Defects 1–4 are now fixed and the report itself speculated
this symptom might resolve once those defects were corrected (§5.2, final
paragraph), on-device testing is needed to confirm whether this is still
an active issue or was resolved as a side effect.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Governance Record Inconsistency

### 6.1 `comm/` transport layer audit (`b4e8c012` / `2f612d17` / `a4c8e2f1`)

Unchanged from the prior review — this is a documentation-consistency
question, not a source-code question, and static review of `src/gtach/comm/`
does not resolve it:

- `audit-b4e8c012-index.md` shows all 20 items `[x]`.
- `audit-b4e8c012-report.md` contains detailed findings for only 6 of 20.
- `prompt-a4c8e2f1-comm-audit.md` (same date as the index/report) states 18
  items remain unchecked.
- Index and report share identical creation timestamps consistent with a
  bulk copy during the `workspace/` → `ai/workspace/` migration.

Status: **unresolved.** Determine whether the missing 14 findings exist
elsewhere (e.g., an AEL state file not yet migrated) or were never written,
before treating this audit as closed.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deferred by Design

### 7.1 UI Navigation audit — Finding C (terminology)

Overlap between the display-layer `_sim_mode` flag and the launch-time
simulated transport. The audit report explicitly defers this to
consensus rather than treating it as a fix (§6.3, §7.0). Not a defect;
listed here only so it is not lost.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial task list from `ai/workspace` state review. |
| 2.0 | 2026-07-29 | Cross-checked every item against `src/gtach`. Reclassified: `b7e3f90a`, `f993f871`, UI-nav Findings A/B, and splash-hang Defects 1–4 are all implemented in source with governance documents left open. Retained genuinely open items, live-verification items, and the `comm/` audit record inconsistency. |

---

Copyright (c) 2026 William Watson. MIT License.
