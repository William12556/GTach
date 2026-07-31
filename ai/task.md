Created: 2026 July 29

# Task List

---

## Table of Contents

[0.0 Summary](<#0.0 summary>)
[1.0 Purpose](<#1.0 purpose>)
[2.0 Source Verification Method](<#2.0 source verification method>)
[3.0 Completed](<#3.0 completed>)
[4.0 Open](<#4.0 open>)
[5.0 Requires Live-Device Verification](<#5.0 requires live-device verification>)
[6.0 Deferred by Design](<#6.0 deferred by design>)
[7.0 Code Review Remediation — Governance Document Creation](<#7.0 code review remediation — governance document creation>)
[7.1 Scope](<#7.1 scope>)
[7.2 Common Parameters for Every Triple](<#7.2 common parameters for every triple>)
[7.3 Display Review Triples](<#7.3 display review triples>)
[7.4 Core, Communication and Utility Review Triples](<#7.4 core, communication and utility review triples>)
[7.5 Verification Prerequisites](<#7.5 verification prerequisites>)
[7.6 Sequencing and Notes](<#7.6 sequencing and notes>)
[8.0 Release Plan](<#8.0 release plan>)
[8.1 Decision](<#8.1 decision>)
[8.2 Prerequisite — Minimal Test Suite (P06)](<#8.2 prerequisite — minimal test suite (p06)>)
[8.2.1 Standing Closure Rule](<#8.2.1 standing closure rule>)
[8.3 Release v0.3.0 — Diagnostic and Low-Risk](<#8.3 release v0.3.0 — diagnostic and low-risk>)
[8.4 Observation Session](<#8.4 observation session>)
[8.5 Release v0.4.0 — Gated and Appearance-Changing](<#8.5 release v0.4.0 — gated and appearance-changing>)
[8.6 Versioning and Build](<#8.6 versioning and build>)
[9.0 Cross-Check — 2026-07-31](<#9.0 cross-check — 2026-07-31>)
[9.1 Method](<#9.1 method>)
[9.2 Newly Implemented Triples — Prompt Closed, Issue/Change Open](<#9.2 newly implemented triples — prompt closed, issue/change open>)
[9.3 Reclassification — 7.3.4 Moved to v0.3.0](<#9.3 reclassification — 7.3.4 moved to v0.3.0>)
[9.4 Standing Closure Rule Deviation — `1143427b`](<#9.4 standing closure rule deviation — 1143427b>)
[9.5 Confirmed Not Yet Implemented](<#9.5 confirmed not yet implemented>)
[9.6 Verification Evidence](<#9.6 verification evidence>)
[Version History](<#version history>)

---

## 0.0 Summary

| Section | ID | Item | Status |
|---|---|---|---|
| 3.1 | `b7e3f90a` | Dead code cleanup | ✅ Complete |
| 3.2 | `f993f871` | OPTIONS update check/install | ✅ Complete |
| 3.3 | `c84ffe6f` / `85cc0241` | UI Navigation Logic audit — Findings A and B | ✅ Complete |
| 3.4 | — | Splash Screen Debug Session audit — Defects 1–4 | ✅ Complete |
| 3.5 | `b4e8c012` / `2f612d17` / `a4c8e2f1` | `comm/` transport layer audit | ✅ Complete |
| 4.1 | — | `faulthandler` output not captured under systemd | ☐ Open |
| 5.1 | — | Splash audit §4.3 — WELCOME screen touch-unresponsiveness | ☐ Unverified |
| 6.1 | — | UI Navigation audit — Finding C (terminology) | Deferred by design |
| 7.3 | 13 UUIDs | Display review triples | 7 of 13 authored — 2 closed (`4c038bed`, `0b00759c`), 5 prompt-closed/issue+change open (`66ef59a0`, `cb28980f`, `49b21ace`, `44bca479`, `4c3c3e1f`) |
| 7.4 | 8 UUIDs | Core/comm/utils review triples | 6 of 8 authored — 3 closed (`5a9dc15e`, `11be4865`, `1143427b`†), 3 prompt-closed/issue+change open (`52414414`, `2d545bf5`, `d32ccc49`) |
| 7.5 | — | Verification prerequisites gating §7.3/§7.4 | 2 of 6 resolved — 7.5.4 decided (retire); 7.5.1's self-clearing mechanism has shipped (7.3.3), observation itself still pending §8.4 |
| 8.0 | — | Two-release plan: v0.3.0 diagnostic and low-risk, v0.4.0 gated and appearance-changing | v0.3.0 substantially authored (13 of 14 items landed, see §9.0); v0.4.0 unchanged, 8 items to author |

† `1143427b` closed (issue, change and prompt) without a T06 result document, contrary to
§8.2.1's Standing Closure Rule and without appearing on that section's grandfather list.
See §9.4.

[Return to Table of Contents](<#table of contents>)

---

## 1.0 Purpose

This document lists unfinished work. Version 1.0 was built from `ai/workspace`
document state alone. Version 2.0 cross-checked each item against
`src/gtach`. Version 3.0 corrected a misstatement in 2.0. Version 4.0
closed the `comm/` transport layer audit following log-based root cause
analysis. Revision 5.0 added §7.0, which enumerates the governance
document triples required to implement the recommendations of the two
code review reports in `ai/workspace/report/`. Revisions 6.0 and 8.0
recorded the outcome of cross-checking §7.0 against those reports; 7.0
added the two-release delivery plan in §8.0. This revision (9.0)
cross-checks §7.0's twenty triples against current governance-document
state, `src/gtach` and the pushed git history, following a report that
several triples' prompts had closed while their issues and changes
remained open pending test results. §9.0 records the result: eight
further triples implemented (one of which, `49b21ace`, was also
reclassified from v0.4.0 into v0.3.0), plus one further closure,
`1143427b`, that deviates from §8.2.1's Standing Closure Rule.

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

Both cycles were already closed prior to this review. The audit report
itself (`audit-ui-navigation-logic-report.md`) remained in the active
`audit/` directory even though its findings were fully actioned; moved to
`audit/closed/`.

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

`audit-splash-hang-debug-session-state-report.md` remained in the active
`audit/` directory even though all four defects were fully actioned; moved
to `audit/closed/`.

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

## 7.0 Code Review Remediation — Governance Document Creation

Each numbered task below is the authoring of one complete T03 issue / T02
change / T04 prompt triple sharing a single UUID. No source code is
changed by these tasks; they produce the governance documents that
authorise the change.

### 7.1 Scope

Source reports, both version 1.0, dated 2026-07-30:

- `ai/workspace/report/core-comm-utils-code-review.md` — §7.0 numbered
  recommendations plus the recommendations embedded in findings §4.x and
  §5.x that §7.0 omits.
- `ai/workspace/report/display-ui-graphics-review.md` — §9.1 to §9.5,
  recommendations 1 to 29.

Recommendations are grouped by theme: one triple per coherent unit of
work, so that each T04 prompt addresses a single concern and a bounded
file set. Twenty triples cover all recommendations from both reports. The
report item numbers each triple carries are recorded so coverage can be
audited against the source.

All implementation is targeted at the **Claude Code** tactical profile.
AEL is not used for any of this work.

[Return to Table of Contents](<#table of contents>)

### 7.2 Common Parameters for Every Triple

| Parameter | Value |
|---|---|
| Issue path | `ai/workspace/issues/issue-<uuid>-<slug>.md` (T03) |
| Change path | `ai/workspace/change/change-<uuid>-<slug>.md` (T02) |
| Prompt path | `ai/workspace/prompt/prompt-<uuid>-<slug>.md` (T04) |
| UUID | Identical across all three documents (P00 §6.1 propagation) |
| Iteration | `1` in issue, change and prompt; issue and change increment together |
| `issue_info.type` | `defect` for core §3.x and display §8.x items; `performance` for core §4.x and display §5.x/§6.x efficiency items; `enhancement` for display §7.x user interface proposals. Core §5.x (Logic and Design) takes the type of its dominant effect: `defect` where the finding is an incorrect or unreachable behaviour (§5.3, §5.6, §5.7), `performance` where it is a resource or latency concern (§5.5, §5.9), `enhancement` where it is a maintainability or diagnostic improvement (§5.1, §5.2, §5.4). Where a triple mixes types, the issue takes the highest-severity contributing type. |
| `source.origin` | `code_review` |
| `source.description` | Cites the report filename and the specific section or recommendation number |
| `issue_info.coupled_docs.change_ref` | `change-<uuid>`, `change_iteration: 1` |
| `change` coupling | One-to-one with its issue (P03/P04) |
| `prompt_info.source_ref` | `change-<uuid>` |
| `prompt_info.target_profile` | `claude_code` |
| `prompt_info.coupled_docs` | `change_ref: change-<uuid>`, `change_iteration: 1` |
| `tactical_brief` | Not required — the context budget gate applies to `target_profile: ael` only (primer §7.0, P09) |
| Trace | `trace-traceability-matrix-master.md` updated at each phase boundary (P05) |
| Git | Commit after each triple is authored |

The Trivial Change Exemption (P03 §1.4.12) is **not** claimed for any
task below. Several individual recommendations would qualify in isolation
(for example recommendation 14, 17, 22), but each is grouped with
non-trivial work in the same file, so the full triple applies.

[Return to Table of Contents](<#table of contents>)

### 7.3 Display Review Triples

Source: `ai/workspace/report/display-ui-graphics-review.md`. "Recs" are
the numbered items in §9.0.

| Task | UUID | Slug | Recs | Primary files | Status (2026-07-31) |
|---|---|---|---|---|---|
| 7.3.1 | `4c038bed` | `rpm-signal-conditioning` | 1, 5, 23 | `display/manager.py` | ✅ Closed |
| 7.3.2 | `66ef59a0` | `framebuffer-write-path` | 2, 6, 7, 8 | `display/rendering/engine.py` | Implemented — prompt closed, issue/change open pending test |
| 7.3.3 | `cb28980f` | `framebuffer-geometry-query` | 21 | `display/rendering/engine.py`, `utils/terminal.py` (ioctl pattern) | Implemented — prompt closed, issue/change open pending test |
| 7.3.4 | `49b21ace` | `framebuffer-vsync-pageflip` | 3, 4 | `display/rendering/engine.py` | Implemented — prompt closed, issue/change open pending test. Reclassified from v0.4.0 into v0.3.0; see §9.3 |
| 7.3.5 | `821919ce` | `render-caching` | 9, 10, 11 | `display/manager.py`, `display/rendering/engine.py` | ☐ To author |
| 7.3.6 | `9ed1c77e` | `frame-pacing-conditional-render` | 12, 13, 14 | `display/manager.py`, `config/config.yaml` | ☐ To author |
| 7.3.7 | `0b00759c` | `performance-instrumentation` | 15, 16, 17, 18 | `display/performance/monitor.py`, `display/manager.py` | ✅ Closed |
| 7.3.8 | `44bca479` | `display-defect-remediation` | 19, 20, 22 | `display/manager.py`, `display/input/touch_coordinator.py` | Implemented — prompt closed, issue/change open pending test |
| 7.3.9 | `b02ed4ea` | `button-system-touch-targets` | 24, 27 | `display/manager.py`, `display/typography.py`, `display/input/touch_coordinator.py` | ☐ To author |
| 7.3.10 | `378703da` | `radial-centre-readout` | 25 | `display/manager.py`, `display/models.py` | ☐ To author |
| 7.3.11 | `5014040c` | `annular-band-indicator` | 26 | `display/manager.py`, `display/models.py` | ☐ To author |
| 7.3.12 | `5012004e` | `night-palette-toggle` | 29 | `display/manager.py`, `display/models.py`, `config/config.yaml` | ☐ To author |
| 7.3.13 | `4c3c3e1f` | `update-view-progress` | 28 | `display/manager.py` | Implemented — prompt closed, issue/change open pending test |

Coverage check: recommendations 1–29 each appear exactly once across
rows 7.3.1 to 7.3.13. Status column added 2026-07-31 per the residual
observation in `task-list-cross-check-discrepancies.md` §10.2; see §9.0
for the verification behind each entry.

#### 7.3.14 Directed Scope Decisions

Three recommendations were left open in the report as design decisions.
Direction has been given; the triples are to be authored to the decided
scope, not to the report's conditional wording.

- **7.3.10 (rec 25)** — Place the numeric RPM in the RADIAL centre disc
  **and retire DIGITAL as a separate mode.** The report's "consider" is
  resolved as accepted. Consequences to specify in the change document:
  the horizontal-swipe mode change (`manager.py:142-172`) and the unused
  `_render_mode_selector()` (`manager.py:1091`) become dead and are
  removed; report finding §7.6 (no mode affordance) is closed by
  retirement rather than by adding an indicator; `DisplayMode.DIGITAL`
  handling in `display/models.py` and any persisted `config.mode` value
  require a migration path.
- **7.3.11 (rec 26)** — Replace the full-field band colour with an
  **annular band indicator on a fixed dark ground.** Accepted, not
  conditional. This removes the band-to-text-colour coupling introduced
  in 7.3.1 by recommendation 23; the change document must state that the
  white-on-blue text correction from 7.3.1 is superseded for the main
  readout and note whether `_get_band_colour()` retains a text-colour
  return value at all.
- **7.3.12 (rec 29)** — Add a **dimmed night palette with a manual
  toggle.** No ambient light sensor is available on the target hardware,
  so automatic switching is out of scope and must not be specified. The
  toggle is an operator control; the change document must specify where
  it lives in the UI and whether its state persists across restart.
  Interacts with 7.3.9 — the toggle is a new touch target and is subject
  to the same ≥ 72 px / ≥ 16 px geometry, and with 7.3.11, since the
  annular indicator's palette must have a night variant.

#### 7.3.15 Recorded Exclusion — Display §7.7

Display report §7.7 (*Options Screen Uses a Rectangular Layout*) is a
finding with no corresponding numbered recommendation in the report's
§9.0. It is therefore outside the §7.1 scope statement, which bounds the
display source to recommendations 1 to 29, and no triple sources it.

The exclusion is recorded rather than left implicit because §7.6.4
requires that neither report be closed until every triple it sources is
closed. Without this entry, §7.7 would be an open finding with no closure
path and no owner.

Disposition: §7.7 proposes a circular re-layout of the options screen.
That is a user interface redesign, not a code-review remediation, and it
overlaps the button geometry work already scoped in 7.3.9 (recommendation
24, which reduces the screen to three items). §7.7 is deferred to a
future requirements cycle (P10) rather than converted to a twenty-first
triple. Revisit after 7.3.9 is implemented and the three-item layout can
be observed on the panel.

This entry does not alter the coverage check in §7.3: recommendations 1
to 29 each still appear exactly once.

[Return to Table of Contents](<#table of contents>)

### 7.4 Core, Communication and Utility Review Triples

Source: `ai/workspace/report/core-comm-utils-code-review.md`. References
are to that report's section numbers; `#n` refers to its §7.0 numbered
list.

| Task | UUID | Slug | Report items | Primary files | Status (2026-07-31) |
|---|---|---|---|---|---|
| 7.4.1 | `394c3bbb` | `config-device-persistence-retirement` | §3.6, §5.1; #1 (retirement branch), #6 | `utils/config.py`, `comm/device_store.py`, `comm/models.py` | ☐ To author — `get_device_by_address`/`add_or_update_device`/`remove_device` and `saved_devices` confirmed still present in `config.py`, unretired |
| 7.4.2 | `5a9dc15e` | `watchdog-lock-discipline` | §3.3, §4.1; #2 | `core/watchdog.py`, `core/thread.py` | ✅ Closed |
| 7.4.3 | `11be4865` | `platform-detection-consolidation` | §3.2, §4.4; #3 | `utils/platform.py`, `utils/dependencies.py` | ✅ Closed |
| 7.4.4 | `52414414` | `device-store-pairing-robustness` | §3.4, §3.5, §5.6, §5.7; #4, #5 | `comm/device_store.py`, `comm/pairing.py` | Implemented — prompt closed, issue/change open pending test |
| 7.4.5 | `6481f8ce` | `transport-consolidation` | §4.3, §5.3, §5.8; #7 | `comm/transport.py`, `comm/rfcomm.py`, `comm/serial_transport.py`, `comm/tcp_transport.py`, `main.py`, `app.py` | ☐ To author |
| 7.4.6 | `2d545bf5` | `thread-shutdown-budget` | §5.5, §5.9 | `core/thread.py`, `app.py` | Implemented — prompt closed, issue/change open pending test |
| 7.4.7 | `d32ccc49` | `utils-comm-housekeeping` | §4.2, §5.2, §5.4; #8 | `utils/home.py`, `utils/config.py`, `comm/obd.py` | Implemented — prompt closed, issue/change open pending test |
| 7.4.9 | `1143427b` | `rwlock-notification-defect` | §3.1; #1 (correction branch) | `utils/config.py` | ✅ Closed — but see §9.4, closure deviates from §8.2.1 |

Coverage check: §7.0 items #1 to #8 and the embedded recommendations in
§3.1–§3.6, §4.1–§4.4 and §5.1–§5.9 each appear exactly once across rows
7.4.1 to 7.4.9. §7.0 item #1 is a disjunction — correct the `RWLock`
notification bug *or* retire the subsystem — and its two branches are
claimed separately: the correction by 7.4.9 and the retirement by 7.4.1.
See §7.4.8.

#### 7.4.8 §5.1 Disposition — Decided

The §7.5.4 decision was taken on 2026-07-30: **retire**. The
`ConfigManager` device-persistence path has no intended future use.
`DeviceStore` is the sole device store by declaration.

Evidence supporting the decision, from a call-graph check rather than
from the report alone:

| Store | Live call sites outside its own module |
|---|---|
| `DeviceStore` | ~15, across `app.py`, `comm/transport.py`, `comm/sim_bluetooth.py`, `display/setup.py`, `display/manager.py`, `display/setup_components/bluetooth/interface.py` |
| `ConfigManager.get_device_by_address` / `add_or_update_device` / `remove_device` | **0** |

§3.6 corroborates: `BluetoothDevice` has no `address` attribute, so any
live call to those three methods raises `AttributeError` immediately.
The path has never executed in production.

**Two corrections to this section's previous text.**

*First — the "approximately 1,600 lines" figure was misleading.*
`utils/config.py` is 1,636 lines in total, and it also holds the live
application configuration. The device-persistence portion is a subset:
the three methods at `config.py:1400-1460`, the
`BluetoothConfig.saved_devices` field and its serialisation, and the
`BluetoothDevice` model. The retirement is a materially smaller deletion
than the report implies, and the validator, transactional-write and
session-archival machinery serves the main configuration and is retained.

*Second — retirement does NOT close §3.1.* The previous text stated that
under *retire*, "§3.1 (`RWLock` notification bug) and §3.6
(`device.address`) are closed as removed rather than fixed." That holds
for §3.6 only. `_rw_lock` guards `ConfigManager.load_config`
(`config.py:1175`, read lock at 1182, write lock at 1190) and
`save_config` (`config.py:1320`, write lock at 1330) — the whole
configuration path, which `app.py:75` and `main.py:107` exercise on every
start. Retiring the device methods does not touch it.

The deadlock has not been observed because configuration I/O is
effectively single-threaded at startup, so the writer-waiting-while-
readers-active condition is rare. It is latent but on an exercised path:
a Critical structural defect, not dead code.

§3.1 is therefore separated into its own triple, **7.4.9** (`1143427b`),
which is independent of the disposition and of 7.4.1. This is a
re-partition of existing scope, not an addition: §3.1 was already claimed
by 7.4.1, and would have been silently dropped by the retirement.

Sequencing consequence: 7.4.9 is a small correction on a live path and
ships in v0.3.0 (§8.3). 7.4.1 is a large deletion and ships in v0.4.0
(§8.5). They cannot travel together, which is the practical reason the
split is necessary rather than merely tidy.

[Return to Table of Contents](<#table of contents>)

### 7.5 Verification Prerequisites

Observations required before, or in support of, the triples above. These
are not governance cycles and carry no UUID. Items 7.5.1, 7.5.2, 7.5.5
and 7.5.6 require the live devices (`gtach.local`, and a paired ELM327 or
`ELM327-Emulator.local`).

| Task | Observation | Source | Effect |
|---|---|---|---|
| 7.5.1 | Read `bits_per_pixel`, `stride`, `virtual_size` from `/sys/class/graphics/fb0`; `fbset -i` | display §10.1 | **Gated 7.3.3 and 7.3.4.** 7.3.3 has shipped (`cb28980f`) and confirmed in source: `engine.py` queries `FBIOGET_VSCREENINFO`/`FBIOGET_FSCREENINFO` before mapping and logs a mismatch at ERROR. The gate is mechanically satisfied per §8.3's note, and 7.3.4 (`49b21ace`) has been authored and implemented on that basis. The actual on-device log line has not yet been read; do so in §8.4 as a confirmation rather than a gate |
| 7.5.2 | Characterise the flicker: moving horizontal band vs. full-field alternation vs. above-caution-only vs. last-digit churn; then the simulation-mode sweep test | display §10.3, §10.4 | Determines whether 7.3.1 or 7.3.4 is the effective fix; may reduce 7.3.4 to an efficiency item |
| 7.5.3 | Read `frame_time_ms` from the periodic log line | display §10.2 | **Depends on 7.3.7** (rec 15). Until that ships the logged figure measures padded, not render, time. Establishes the baseline against which 7.3.5, 7.3.6 are judged |
| 7.5.4 | ✅ **DECIDED 2026-07-30 — retire.** No intended future use; `DeviceStore` is the sole device store. Call-graph evidence and two corrections to the previous framing are recorded in §7.4.8 | core §8.0 | 7.4.1 is unblocked and scoped to retirement (§3.6, §5.1). §3.1 is separated into 7.4.9, being independent of the disposition |
| 7.5.5 | Reproduce the transport race: concurrent `disconnect()` and `send_command()` | core §8.0 | Confirms the §5.3 failure mode and supplies the regression test for 7.4.5 |
| 7.5.6 | Record the actual hardware revision string on the Pi Zero 2W | core §8.0 | Confirms whether the §3.2 `lstrip()` defect corrupts detection for the revision in field use; sets the severity recorded in 7.4.3 |

[Return to Table of Contents](<#table of contents>)

### 7.6 Sequencing and Notes

#### 7.6.1 Dependencies

| Task | Depends on | Reason |
|---|---|---|
| 7.3.4 | 7.5.1, 7.3.3 | Page flipping requires the true geometry; report §9.1 item 4 states the dependency |
| 7.3.6 | 7.3.1, 7.3.5 | Frame skipping must not suppress the intentional shift-cue flash (report §9.2 note); the static-layer cache changes what a frame costs |
| 7.3.11 | 7.3.1 | Supersedes the rec 23 text-colour correction for the main readout |
| 7.3.12 | 7.3.11 | The night palette must cover the annular indicator's colours |
| 7.3.9 | — | Precedes 7.3.12 if the night toggle is placed on the options screen |
| 7.4.1 | ~~7.5.4~~ | ✅ Cleared 2026-07-30. Disposition decided: retire (§7.4.8) |
| 7.4.7 | 7.4.9 | Both modify `utils/config.py`. 7.4.9 corrects the `RWLock` notification path; 7.4.7 adds the §5.2 singleton warning to `ConfigManager.__new__`/`__init__`. Disjoint regions, but 7.4.9 ships first in v0.3.0, so 7.4.7 is written against the corrected file |
| 7.4.5 | 7.5.5 | Regression test derives from the reproduction |
| 7.3.5 | 7.3.11, 7.3.12 | Recommendation 9 caches the RADIAL static layer. The annular band indicator (7.3.11) and the night palette (7.3.12) both alter static-layer content, so each requires a cache-invalidation path that recommendation 9 does not specify. Either 7.3.5 lands last, or its change document must specify an invalidation key covering band and palette state |
| 7.3.9 | 7.3.8 | Recommendation 20 (7.3.8) relocates touch registration from the render path to a mode-entry hook. Recommendations 24 and 27 (7.3.9) re-register button regions. Authoring 7.3.9 first produces registration code that 7.3.8 then has to relocate |
| 7.4.7 | 7.4.1 | Both modify `utils/config.py`. Under the *retire* disposition 7.4.1 deletes the device-persistence machinery; the §5.2 singleton warning added by 7.4.7 must be sited in surviving code. 7.4.7 is authored after the §7.5.4 decision is recorded, or its change document must confine the edit to `ConfigManager.__new__`/`__init__` |

#### 7.6.2 Recommended Authoring Order

1. **7.3.1** — report §9.1 states it should be implemented and observed
   first: lowest risk, confined to one file, and resolves the symptom
   outright if the cause is band thrash rather than tearing.
2. **7.3.7** — prerequisite for measuring anything (§7.5.3).
3. **7.4.2**, **7.4.3** — the two High severity core findings active in
   the running application.
4. **7.3.2**, **7.3.3** — low-risk framebuffer path work; 7.3.3 supplies
   the geometry facts 7.3.4 needs.
5. **7.4.4**, **7.4.7**, **7.4.6** — Medium and Low core robustness.
6. **7.3.5**, **7.3.6**, **7.3.8** — rendering efficiency and defects.
7. **7.3.4** — after 7.5.1 confirms geometry.
8. **7.4.5**, **7.4.1** — the two structural refactors, once their
   prerequisites are met.
9. **7.3.9** to **7.3.13** — user interface changes, which alter the
   product's appearance and behaviour.

#### 7.6.3 Within-Task Sequencing for 7.4.5

Report §4.3 notes that the §5.3 race must currently be fixed in three
files. Two orderings are available and the change document must state
which is taken:

- Hoist the shared connect/disconnect/send-command skeleton into
  `OBDTransport` first, then apply the lock fix once. Fewer edits, but
  the refactor carries more risk and delays the fix.
- Apply the lock fix in all three subclasses first, then refactor. The
  fix lands sooner at the cost of duplicated edits.

#### 7.6.4 Constraints

- No source code is created, changed or removed until the corresponding
  T04 prompt is authored and approved (primer §7.0).
- Each triple is authored on explicit request. §7.0 is a plan, not an
  authorisation to proceed through all twenty.
- The reports' own recommendation numbering is preserved in every issue
  document so coverage remains auditable after the reports are closed.
- Neither report is closed until all triples it sources are closed;
  both remain in `ai/workspace/report/`.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Release Plan

The §7.0 remediation is delivered in two releases rather than one. This
section records that decision, its rationale, the contents of each
release, and the test-suite work that precedes them.

### 8.1 Decision

Sixteen of the twenty triples remain outstanding. A single release
carrying all sixteen was considered and rejected for three reasons:

1. **No regression net.** `tests/` contains only `README.md`. No pytest
   suite exists, so the "pytest tests/ passes" criterion in every change
   document authored to date is vacuously satisfied. Governance
   §1.7.18 makes unit tests mandatory for every component; the project is
   currently non-compliant on that point. See §8.2.
2. **Four triples cannot be authored correctly yet.** 7.3.4, 7.3.5,
   7.3.6, 7.4.1 and 7.4.5 each depend on an observation or decision
   recorded in §7.5 that has not been taken. Authoring them now means
   authoring on assumption.
3. **Batching destroys attribution.** The display report is a
   differential diagnosis, not a fix list; §10.3 supplies a
   discrimination table for the flicker's four candidate causes. 7.3.1
   has shipped and should have removed three of them. If sixteen further
   changes land together and the symptom persists, the cause cannot be
   isolated — and 7.3.4, the highest-risk item, would be among them.

The two-release split preserves attribution while keeping the number of
deploy-and-observe cycles to two.

[Return to Table of Contents](<#table of contents>)

### 8.2 Prerequisite — Minimal Test Suite (P06)

Authored before v0.3.0 is built. This is a P06 activity: T05 test
documents in `ai/workspace/test/`, then generated pytest files in
`tests/`. It is not a T03/T02/T04 cycle — test creation from existing
source is governed by P06 §1.7.2 and §1.7.3, not by P03.

Scope is the logic already changed or about to change, prioritising
components that need no pygame surface:

| Target | Module | Covers |
|---|---|---|
| `PlatformDetector._detect_via_hardware_revision` | `utils/platform.py` | 11be4865 — revision masking, flag bits, old-style codes, non-hex input |
| `WatchdogMonitor` recovery paths | `core/watchdog.py` | 5a9dc15e — lock discipline, heartbeat observation, collect-then-dispatch |
| `PerformanceMonitor` | `display/performance/monitor.py` | 0b00759c, c5dedd71 — frame IDs, periodic gate, memory cache, dropped-frame test |
| `RWLock` | `utils/config.py` | 7.4.9 — notification symmetry, reader concurrency, writer exclusivity |
| `DeviceStore` | `comm/device_store.py` | 7.4.4 — malformed config handling, once authored |
| `DisplayManager` RPM conditioning | `display/manager.py` | 4c038bed — EMA, band hysteresis, flash phase |

All but the last require only `unittest.mock`, `threading` and
`tempfile`. The `DisplayManager` target needs `SDL_VIDEODRIVER=dummy` and
a mocked rendering engine, consistent with the existing headless
arrangement in `engine.py`.

Every acquisition assertion in the `RWLock` tests carries a timeout, so a
regression fails the suite rather than hanging it.

#### 8.2.1 Standing Closure Rule

Governance §1.1.14.3 sets a different closure criterion for each document
class in a triple, and they are not all met at the same moment:

| Class | Criterion | Met when the code lands? |
|---|---|---|
| Prompt | "Code generated successfully, human confirmed" | Yes |
| Change | "Implemented, **tested**, design updated, human accepted" | No |
| Issue | "Resolved and verified, corresponding change implemented **and tested**" | No |

§1.7.18 restates it: *Document closure — requires Stage 3 regression
pass*. §1.7.15 adds that the progressive validation sequence is mandatory
before closure.

**Rule.** Close the prompt when the code lands. Keep the issue and the
change active until a passing T06 result document exists for the coupled
T05.

The Claude Code invocation is therefore:

```
implement ai/workspace/prompt/prompt-<uuid>-<name>.md and close the
prompt when finished. Leave the issue and change active pending test
results.
```

with a second, later instruction closing the issue and change once the
result document is written.

**Why it matters.** Closed documents are immutable (§1.1.14.2, §1.1.14.6).
If a test written after closure fails, the original issue and change
cannot increment to iteration 2; §1.7.13 requires a *new* issue with a
new UUID instead. The fix and its verification then live under different
UUIDs and traceability fragments. The closed change's `test_results`
field is likewise frozen at whatever ad-hoc verification it recorded.

**Documents closed before this rule was recorded.** `4c038bed`,
`5a9dc15e`, `11be4865`, `0b00759c` and `c5dedd71` were closed on
implementation, at a point when `tests/` was empty and the "tested"
criterion was unachievable. Their verification blocks record what was
actually done — compile checks, source-order checks, hand-executed cases
— and explicitly qualify the pytest criterion, so the record is accurate
rather than overstated.

Nothing is lost. Their T05 documents remain **active** in
`ai/workspace/test/`; only the issue, change and prompt were archived. A
`result-<uuid>` document can still be created and coupled to each T05 in
the normal way, completing the verification chain without modifying any
closed document. Do not reopen them: governance already carries one
documented exception to §1.1.14.6 (v9.12) and it should not become a
pattern.

[Return to Table of Contents](<#table of contents>)

Coverage of untouched legacy code is explicitly **not** in scope. The
objective is a net beneath the changes being released, not retrospective
coverage of the whole package.

[Return to Table of Contents](<#table of contents>)

### 8.3 Release v0.3.0 — Diagnostic and Low-Risk

Contents: work already implemented, plus every outstanding triple that
carries no observational dependency and no change to the product's
appearance.

State as of 2026-07-31 (originally written 2026-07-30; see §9.0 for the
cross-check). All fourteen items below are now authored and implemented.

| Triple | UUID | State (2026-07-31) |
|---|---|---|
| 7.3.1 | `4c038bed` | Implemented, closed |
| 7.3.7 | `0b00759c` | Implemented, closed |
| — | `c5dedd71` | Implemented, closed (derived from 0b00759c) |
| 7.4.2 | `5a9dc15e` | Implemented, closed |
| 7.4.3 | `11be4865` | Implemented, closed |
| 7.4.9 | `1143427b` | Implemented, closed — deviates from §8.2.1; see §9.4 |
| 7.3.2 | `66ef59a0` | Implemented — prompt closed, issue/change open pending test |
| 7.3.3 | `cb28980f` | Implemented — prompt closed, issue/change open pending test |
| 7.3.4 | `49b21ace` | Implemented — prompt closed, issue/change open pending test. Reclassified into v0.3.0 from §8.5; see §9.3 |
| 7.3.8 | `44bca479` | Implemented — prompt closed, issue/change open pending test |
| 7.3.13 | `4c3c3e1f` | Implemented — prompt closed, issue/change open pending test |
| 7.4.4 | `52414414` | Implemented — prompt closed, issue/change open pending test |
| 7.4.6 | `2d545bf5` | Implemented — prompt closed, issue/change open pending test |
| 7.4.7 | `d32ccc49` | Implemented — prompt closed, issue/change open pending test, confined per §7.6.1 |

No triple in this release remains unauthored. `ai/workspace/test/result/`
holds no T06 result documents for any of the five triples that carry a T05
(`4c038bed`, `5a9dc15e`, `11be4865`, `0b00759c`, `1143427b`) — the four
grandfathered under §8.2.1 record this as expected; `1143427b` does not,
per §9.4.

7.4.7 sites the §5.2 singleton warning in `ConfigManager.__new__` or
`__init__` and touches no device-persistence code, so it does not collide
with the 7.4.1 retirement in v0.4.0.

7.4.9 is included because §3.1 is a Critical structural defect on the
live configuration path and is independent of the §5.1 disposition — the
retirement does not close it (§7.4.8). It is a small, well-bounded
correction to a single class, which is why it travels in v0.3.0 rather
than alongside the large deletion in v0.4.0.

**7.3.3 clears its own gate.** Recommendation 21 makes the application
query `FBIOGET_VSCREENINFO` and `FBIOGET_FSCREENINFO` and log a mismatch
at ERROR rather than DEBUG. Once shipped, the application reports its own
`bits_per_pixel`, `xres_virtual` and `line_length`, which is precisely
the observation §7.5.1 requires. The manual reading becomes automatic and
the gate on 7.3.4 clears itself.

[Return to Table of Contents](<#table of contents>)

### 8.4 Observation Session

Taken once, on `gtach.local`, after v0.3.0 is deployed. All six §7.5
items are collected in a single sitting.

| Item | Method after v0.3.0 |
|---|---|
| 7.5.1 | Read from the application's own ERROR log line, supplied by 7.3.3. `fbset -i` retained as cross-check |
| 7.5.2 | Characterise the flicker against the §10.3 discrimination table, then run the simulation-mode sweep of §10.4 |
| 7.5.3 | Read `frame_time_ms` from the periodic log line — now meaningful, since 0b00759c has shipped. Record as the baseline for 7.3.5 and 7.3.6 |
| 7.5.4 | Human decision on the `ConfigManager` disposition. Not an observation; can be taken at any time |
| 7.5.5 | Reproduce the transport race with concurrent `disconnect()` and `send_command()` |
| 7.5.6 | Record the actual hardware revision string. Retrospective — 11be4865 has already shipped — but confirms whether the defect was live or latent |

Record the outcomes in §7.5 and in the T06 result documents for the
triples they gate.

[Return to Table of Contents](<#table of contents>)

### 8.5 Release v0.4.0 — Gated and Appearance-Changing

Authored after §8.4, with the observations in hand.

**Update 2026-07-31**: `49b21ace` (7.3.4) has already been authored and
implemented — the §7.5.1 gate cleared mechanically once 7.3.3 shipped,
per §8.3's own note. It is removed from this table and now tracked under
§8.3. See §9.3.

| Triple | UUID | Unblocked by |
|---|---|---|
| 7.3.5 | `821919ce` | 7.5.3 baseline; keyed cache per §7.6.1 |
| 7.3.6 | `9ed1c77e` | 7.3.5 |
| 7.3.9 | `b02ed4ea` | — grouped here as an appearance change |
| 7.3.10 | `378703da` | — retires DIGITAL mode; largest behavioural change in the set |
| 7.3.11 | `5014040c` | 7.3.1 |
| 7.3.12 | `5012004e` | 7.3.11 |
| 7.4.1 | `394c3bbb` | 7.5.4 decided — retire (§7.4.8). Large deletion, released here rather than with the v0.3.0 corrections |
| 7.4.5 | `6481f8ce` | 7.5.5 reproduction |

The five user interface triples are deliberately released together so the
product's appearance changes once rather than incrementally.

[Return to Table of Contents](<#table of contents>)

### 8.6 Versioning and Build

Semantic versioning per governance §1.1.13. The project is in initial
development (0.y.z), so both releases take a MINOR increment.

- v0.3.0 — §8.3 contents
- v0.4.0 — §8.5 contents

Build and release use the existing project scripts; no new tooling is
required.

```bash
# Build distribution artefacts
./bin/build.sh

# Stage a wheel to the Pi for the in-app OPTIONS update flow
./bin/deploy.sh --stage

# Or full deploy: transfer, install, restart the service
./bin/deploy.sh

# Cut the GitHub release once dist/ is built and the tag is ready
./bin/release.sh
```

`bin/deploy.sh --stage` drops the wheel into `/opt/gtach/updates/` for
the *Check for updates* control added by `f993f871`, which is the cheaper
path for iteration. Release notes follow the
`RELEASE_NOTES_vMAJOR.MINOR.PATCH.md` convention of §1.1.13.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Cross-Check — 2026-07-31

William reported that several report-recommendation changes had been
completed: prompts closed, with the coupled issues and changes left open
pending test results. This section verifies that report against current
governance-document state, `src/gtach`, and the pushed git history, and
records what it found.

### 9.1 Method

Three sources, cross-checked against each other rather than taken singly,
consistent with governance's evidentiary standard:

1. **Governance documents** — `ai/workspace/{issues,change,prompt,test}/`
   and their `closed/` subfolders, listed directly, for every one of the
   twenty triples in §7.3 and §7.4.
2. **Source code** — targeted `Grep` for the symbols each report
   recommendation names, against `src/gtach` at its current state
   (`pyproject.toml` reports `0.3.2`, up from the `0.2.64` baseline in
   §2.0).
3. **Git history** — `git log --since=2026-07-30` against the local
   clone, cross-checked against `William12556/GTach` on GitHub via
   `list_commits`. The local `HEAD` commit hash matched the remote's most
   recent commit exactly, confirming the local record and the pushed
   history agree.

[Return to Table of Contents](<#table of contents>)

### 9.2 Newly Implemented Triples — Prompt Closed, Issue/Change Open

Eight triples not recorded as authored in this document's §8.3 (as
written 2026-07-30) are now implemented, each following the pattern
William described — prompt closed, issue and change left active:
`66ef59a0`, `cb28980f`, `49b21ace`, `44bca479`, `4c3c3e1f`, `52414414`,
`2d545bf5`, `d32ccc49`. Each corresponds to a distinct git commit whose
message names the change document it implements (for example `6bdf590
feat(display): size the framebuffer from the device, report disagreement
at ERROR` implements `change-cb28980f`). §7.3 and §7.4 above now carry a
Status column recording this; §8.3 is updated accordingly.

This leaves eight triples still unauthored: `821919ce`, `9ed1c77e`,
`b02ed4ea`, `378703da`, `5014040c`, `5012004e` (display, all appearance-
changing and gated to v0.4.0 by design), and `394c3bbb`, `6481f8ce` (core,
also gated to v0.4.0 pending §7.5.4/§7.5.5 — 7.5.4 is decided but 7.4.1's
change document has not yet been authored to that disposition).

[Return to Table of Contents](<#table of contents>)

### 9.3 Reclassification — 7.3.4 Moved to v0.3.0

`49b21ace` (framebuffer vsync/page-flip) was assigned to v0.4.0 in §8.5,
gated on the §7.5.1 observation via 7.3.3. §8.3's own note anticipated
that 7.3.3 shipping would clear this gate automatically, since the
application would then report its own framebuffer geometry at ERROR
severity. That is confirmed in source: `engine.py:200` queries
`FBIOGET_VSCREENINFO` before mapping, and the git commit sequence shows
`cb28980f` (7.3.3) implemented immediately before `49b21ace` (7.3.4), with
an intervening commit (`fb57e4c docs: author the final four v0.3.0
governance triples`) recording the reclassification into v0.3.0. §8.3 and
§8.5 above are updated to reflect this; no discrepancy is recorded, since
the mechanism was already documented in §8.3 before the fact.

The on-device confirmation that geometry is depth 32 / stride 1920
(§7.5.1's original purpose) has not yet been taken — the gate is cleared
mechanically, not empirically. Take the reading in §8.4 as planned, as a
confirmation rather than a blocking observation.

[Return to Table of Contents](<#table of contents>)

### 9.4 Standing Closure Rule Deviation — `1143427b`

§8.2.1 states the rule: close the prompt when code lands; keep the issue
and change active until a passing T06 result document exists for the
coupled T05. Five documents were named as closed before the rule was
recorded and exempted: `4c038bed`, `5a9dc15e`, `11be4865`, `0b00759c`,
`c5dedd71`.

`1143427b` (7.4.9, the `RWLock` notification defect) is not on that list.
Its issue, change and prompt are nonetheless all in `closed/` as of
2026-07-31. Its own change document (`change-1143427b`, version 1.2)
records the closure explicitly against an unmet criterion:

- `test_results` states on-target verification "is outstanding and ships
  with v0.3.0", and step 4 of `implementation_steps` (verify on
  `gtach.local`) is recorded as "open by design and owned by William
  Watson".
- The coupled T05, `test/test-1143427b-rwlock-notification-defect.md`,
  carries `status: "planned"` and every one of its nine test cases is
  `status: "not_run"`.
- `ai/workspace/test/result/` is empty — no T06 exists for this or any
  other triple.
- The change document itself records `pytest tests/ collected 0 items`
  at the time of closure, and a deviation on its own implementation step
  3 (generating `tests/utils/test_rwlock.py`), which it says was not done
  because the coupled prompt permitted no file outside
  `src/gtach/utils/config.py`.

`tests/utils/test_rwlock.py` and `tests/conftest.py` now exist in the
working tree, with `.pyc` cache entries indicating at least one local
pytest run, but no T06 result document records that run, and the T05's
own status field has not been updated to reflect it.

This is not a source-code defect — the `RWLock` fix itself is verified by
AST comparison and a 25-assertion development-platform run, per the
change document. It is a governance-process deviation: the issue and
change closed without the artefact §8.2.1 requires, and without being
added to its grandfather list. Recommended resolution, for decision: (a)
generate the T06 result document from the now-existing test run and treat
the record as complete, matching the four grandfathered items in
substance if not in timing, or (b) add `1143427b` to §8.2.1's grandfather
list with a stated reason, if (a) is not wanted. No document is closed or
reopened by this cross-check; §1.1.14.6 governs reopening and is outside
this section's scope.

[Return to Table of Contents](<#table of contents>)

### 9.5 Confirmed Not Yet Implemented

Spot-checked directly in source rather than inferred from the absence of
governance documents:

- **`394c3bbb`** (config-device-persistence-retirement, 7.4.1) —
  `utils/config.py` still defines `get_device_by_address`,
  `add_or_update_device` and `remove_device`, and `BluetoothConfig` still
  carries `saved_devices`. The retirement has not occurred.
- All six v0.4.0 display triples (`821919ce`, `9ed1c77e`, `b02ed4ea`,
  `378703da`, `5014040c`, `5012004e`) and `6481f8ce` (7.4.5) have no
  issue, change, prompt or test document under any name in
  `ai/workspace/`, active or closed, and no matching commit in the git
  history reviewed. Absence in this case is corroborated, not assumed.

[Return to Table of Contents](<#table of contents>)

### 9.6 Verification Evidence

| Claim | Evidence |
|---|---|
| Eight triples implemented since 2026-07-30 | `git log --oneline --since=2026-07-30` — 32 commits, each newly-implemented UUID's change document named in a `fix`/`feat`/`perf` commit message |
| Local history matches GitHub | `mcp__github__list_commits` on `William12556/GTach` — latest remote SHA `cfcf1fa9…` equals local `HEAD` |
| 7.3.3 implemented | `engine.py:40,200,367,387` — `FBIOGET_VSCREENINFO` present; queried before mapping |
| 7.3.4 implemented | `engine.py:84-89,321-329,426-466` — `page_flip`, `vsync_available`, `FBIO_WAITFORVSYNC`, `FBIOPAN_DISPLAY` present |
| 7.4.1 not implemented | `config.py:1440,1459,1482` — the three device methods and `saved_devices` (line 435) remain |
| `1143427b` closure gap | `change-1143427b` §`verification.test_results`; `test-1143427b` §`test_info.status`; `ai/workspace/test/result/` listed empty |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial task list from `ai/workspace` state review. |
| 2.0 | 2026-07-29 | Cross-checked every item against `src/gtach`. Reclassified `b7e3f90a`, `f993f871`, UI-nav Findings A/B, and splash-hang Defects 1–4 as implemented in source. |
| 3.0 | 2026-07-29 | Corrected 2.0's claim that no governance documents existed for UI-nav Findings A/B — both have closed issue/change/prompt cycles (`c84ffe6f`, `85cc0241`). Recorded closure of `b7e3f90a` and `f993f871`. Restructured into Completed / Open / Requires Live-Device Verification / Governance Record Inconsistency / Deferred by Design, with explicit ✅/☐ status markers. Added `comm/` audit clarification re: `prompt-a4c8e2f1`. |
| 4.0 | 2026-07-29 | Diagnosed the `comm/` audit inconsistency via `ael_20260617-131721.LOG`: all 20 items were genuinely audited; only the copied report was truncated. Accepted as resolved per human decision; moved from "Governance Record Inconsistency" into Completed (§3.5); governance documents moved to `closed/`. |
| 5.0 | 2026-07-30 | Added §7.0: 20 issue/change/prompt triples with assigned UUIDs covering all recommendations of `core-comm-utils-code-review.md` and `display-ui-graphics-review.md`, grouped by theme. All triples target the `claude_code` tactical profile. Recorded directed scope decisions for display recommendations 25, 26 and 29 (§7.3.14); the §5.1 decision gate on 7.4.1 (§7.4.8); six verification prerequisites (§7.5); and dependency, ordering and constraint notes (§7.6). |
| 6.0 | 2026-07-30 | Cross-checked §7.3 and §7.4 against both source reports. Coverage confirmed: display recommendations 1–29 and core §3.1–§3.6, §4.1–§4.4, §5.1–§5.9 and #1–#8 each map to exactly one triple, and every file attribution matches the reports' cited locations. Five discrepancies corrected: extended the §7.2 `issue_info.type` rule to cover core §5.x, which previously had no mapping; added three missing dependency rows to §7.6.1 (7.3.5→7.3.11/7.3.12 static-layer cache invalidation, 7.3.9→7.3.8 touch-registration relocation, 7.4.7→7.4.1 shared `utils/config.py` edit); and added §7.3.15 recording display report §7.7 as an explicit exclusion deferred to a future P10 cycle. |
| 7.0 | 2026-07-30 | Added §8.0 Release Plan. The §7.0 remediation is delivered in two releases rather than one: v0.3.0 carries the implemented work plus the seven outstanding triples with no observational dependency and no appearance change; v0.4.0 carries the gated and user-interface work after a single on-target observation session collects all six §7.5 items. Records the rationale for rejecting a single sixteen-triple release (§8.1), a minimal pytest suite as a P06 prerequisite since `tests/` is currently empty (§8.2), the observation method for each §7.5 item after v0.3.0 (§8.4), and the build and release procedure (§8.6). Notes that 7.3.3 clears the §7.5.1 gate on 7.3.4 automatically by making the application report its own framebuffer geometry. |
| 8.0 | 2026-07-30 | Recorded the §7.5.4 decision: **retire** the `ConfigManager` device-persistence path. Rewrote §7.4.8 with call-graph evidence (`DeviceStore` has ~15 live call sites; the `ConfigManager` device methods have none) and two corrections to its previous text — the "approximately 1,600 lines" figure conflated the whole of `utils/config.py` with the device-persistence subset, and retirement does **not** close §3.1, because `_rw_lock` guards the live `load_config`/`save_config` path that `app.py:75` and `main.py:107` exercise on every start. §3.1 accordingly separated into a new triple 7.4.9 (`1143427b`) — a re-partition of existing scope, not an addition; §7.0 item #1 is a disjunction whose correction and retirement branches are now claimed separately. 7.4.1 rescoped to the retirement (§3.6, §5.1) and reslugged `config-device-persistence-retirement`. §7.6.1 dependency on 7.5.4 cleared and a 7.4.7→7.4.9 row added. 7.4.9 assigned to v0.3.0 (§8.3) as a small correction on a live path; 7.4.1 remains in v0.4.0 (§8.5) as a large deletion. |
| 9.0 | 2026-07-31 | Added §9.0, cross-checking §7.0's twenty triples against governance-document state, `src/gtach` and pushed git/GitHub history, following William's report that several prompts had closed with issues/changes left open pending test results. Confirmed the pattern for eight triples (`66ef59a0`, `cb28980f`, `49b21ace`, `44bca479`, `4c3c3e1f`, `52414414`, `2d545bf5`, `d32ccc49`) — prompt closed, issue and change open. Added a Status column to §7.3 and §7.4 (per the residual observation in `task-list-cross-check-discrepancies.md` §10.2) and updated §0.0, §7.5.1 and §8.3. Recorded that `49b21ace` (7.3.4) was reclassified from v0.4.0 into v0.3.0 once `cb28980f` (7.3.3) cleared its gate mechanically (§9.3); removed it from §8.5. Flagged `1143427b` (7.4.9) as closed — issue, change and prompt — without a T06 result document and without appearing on §8.2.1's grandfather list; its own change document records the on-target verification step as open and the coupled T05 as `status: planned` with all cases `not_run` (§9.4). Confirmed by direct source inspection that `394c3bbb` (7.4.1) remains unimplemented — the `ConfigManager` device-persistence methods are still present — and that all eight remaining v0.4.0 triples have no governance documents or matching commits (§9.5). |

---

Copyright (c) 2026 William Watson. MIT License.
