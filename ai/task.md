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
[9.0 Cross-Check — 2026-08-04](<#9.0 cross-check — 2026-08-04>)
[9.1 Method](<#9.1 method>)
[9.2 Newly Implemented Triples — Prompt Closed, Issue/Change Open](<#9.2 newly implemented triples — prompt closed, issue/change open>)
[9.3 Reclassification — 7.3.4 Moved to v0.3.0](<#9.3 reclassification — 7.3.4 moved to v0.3.0>)
[9.4 Standing Closure Rule Deviation — `1143427b`](<#9.4 standing closure rule deviation — 1143427b>)
[9.5 Confirmed Not Yet Implemented](<#9.5 confirmed not yet implemented>)
[9.6 Verification Evidence](<#9.6 verification evidence>)
[9.7 Remaining Eight Triples Authored — 2026-08-04](<#9.7 remaining eight triples authored — 2026-08-04>)
[9.8 Implementation — 2026-08-04](<#9.8 implementation — 2026-08-04>)
[9.9 On-Target Session — 2026-08-05](<#9.9 on-target session — 2026-08-05>)
[9.10 Second On-Target Session — 2026-08-05](<#9.10 second on-target session — 2026-08-05>)
[9.11 §8.4 Observation Session — Discharged From Logs](<#9.11 §8.4 observation session — discharged from logs>)
[9.11.6 Long Run — 52 Minutes, 2026-08-05 09:34](<#9.11.6 long run — 52 minutes, 2026-08-05 09:34>)
[9.13 The Efficiency Triples Deferred — 2026-08-05](<#9.13 the efficiency triples deferred — 2026-08-05>)
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
| 7.3 | 13 UUIDs | Display review triples | **13 of 13 authored.** 2 closed (`4c038bed`, `0b00759c`); 9 prompt-closed/issue+change open (`66ef59a0`, `cb28980f`, `49b21ace`, `44bca479`, `4c3c3e1f`, `b02ed4ea`, `378703da`, `5014040c`, `5012004e`); **2 not implemented — gated** (`821919ce`, `9ed1c77e`) |
| 7.4 | 8 UUIDs | Core/comm/utils review triples | **8 of 8 authored.** 3 closed (`5a9dc15e`, `11be4865`, `1143427b`†); 5 prompt-closed/issue+change open (`52414414`, `2d545bf5`, `d32ccc49`, `394c3bbb`, `6481f8ce`). **All 8 implemented** |
| 7.5 | — | Verification prerequisites gating §7.3/§7.4 | 3 of 6 resolved — 7.5.4 decided (retire); **7.5.5 discharged 2026-08-04** by the reproduction carried out under `6481f8ce` (§9.8.4); 7.5.1's self-clearing mechanism has shipped (7.3.3), observation itself still pending §8.4. **7.5.3 alone now gates the last two triples** (§9.8.2) |
| 8.0 | — | Two-release plan: v0.3.0 diagnostic and low-risk, v0.4.0 gated and appearance-changing | v0.3.0 fully authored and implemented (14 items, §8.3); v0.4.0 fully authored 2026-08-04, **6 of 8 implemented 2026-08-04** (§9.8) |
| 9.7 | — | Eight remaining triples authored | ✅ Authored 2026-08-04; one open decision (§9.7.3), now live in source (§9.8.5 item 4) |
| 9.8 | — | Six of the eight v0.4.0 triples implemented | ✅ 2026-08-04 — 8 commits on `v0.4.0-display-triples`, unpushed. **Four findings require decision** (§9.8.5); three prompt deviations recorded (§9.8.6) |
| 9.9 | `7f2a9c04` | On-target session — operator trapped on OPTIONS screen | ☐ **Open, high.** §9.8.5 item 1 confirmed in `logs/start.log`. Triple authored 2026-08-05, not implemented. **Ship ahead of the rest of v0.4.0** |
| 9.9.2 | `c1d4b8e6` | Debug toggle fires; `app.py:155` binds the `main` function, not the module | ✅ Raised and implemented 2026-08-05. `debug.log` now fills and `start.log` closes after startup |
| 9.9.3 | `3e8b1d72` | Swipe-down/up navigation for OPTIONS — scope extension agreed | ✅ Implemented 2026-08-05, verified on target |
| 9.10 | `c1d4b8e6` | Debug toggle broken by module shadowing; `engine_profiles.yaml` unpackaged; second stale footer | ☐ Authored 2026-08-05, not implemented. Ungated |
| 9.10.4 | — | OBD stream desynchronises during initialisation | ☐ Open — no T03 raised. **Severity reduced** (§9.11.6): it recovers, and the displayed reading is correct. Init-phase robustness, not data integrity |
| 9.11 | — | §8.4 observation session | ✅ **Complete but for §7.5.2.** `821919ce` gate **CLEARS**; baseline firm at 297 samples (§9.11.6). Only the flicker characterisation needs the panel |
| 9.11.6 | `9ed1c77e` | `fps_limit` 30 removes **every** observed budget overrun | ✅ Parts 1 and 2 implemented 2026-08-05. **Part 3 deferred** (§9.13) |
| 9.13 | `821919ce` | Render caching | ⏸ **Deferred 2026-08-05.** Its own withdrawal condition met — 46% of budget, zero overruns, flicker resolved |

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

| Task | UUID | Slug | Recs | Primary files | Status (2026-08-04) |
|---|---|---|---|---|---|
| 7.3.1 | `4c038bed` | `rpm-signal-conditioning` | 1, 5, 23 | `display/manager.py` | ✅ Closed |
| 7.3.2 | `66ef59a0` | `framebuffer-write-path` | 2, 6, 7, 8 | `display/rendering/engine.py` | Implemented — prompt closed, issue/change open pending test |
| 7.3.3 | `cb28980f` | `framebuffer-geometry-query` | 21 | `display/rendering/engine.py`, `utils/terminal.py` (ioctl pattern) | Implemented — prompt closed, issue/change open pending test |
| 7.3.4 | `49b21ace` | `framebuffer-vsync-pageflip` | 3, 4 | `display/rendering/engine.py` | Implemented — prompt closed, issue/change open pending test. Reclassified from v0.4.0 into v0.3.0; see §9.3 |
| 7.3.5 | `821919ce` | `render-caching` | 9, 10, 11 | `display/manager.py`, `display/rendering/engine.py` | ☐ **Not implemented — gate failed 2026-08-04.** §7.5.3 baseline does not exist; the prompt's own gate instructs stop-and-report. Prompt T-Doc remains active. Three assumptions recorded (§9.8.2) |
| 7.3.6 | `9ed1c77e` | `frame-pacing-conditional-render` | 12, 13, 14 | `display/manager.py`, `config/config.yaml` | ☐ **Not implemented — gate failed 2026-08-04.** Gated twice: §7.5.3 and 7.3.5 landing first. Prompt T-Doc remains active (§9.8.2) |
| 7.3.7 | `0b00759c` | `performance-instrumentation` | 15, 16, 17, 18 | `display/performance/monitor.py`, `display/manager.py` | ✅ Closed |
| 7.3.8 | `44bca479` | `display-defect-remediation` | 19, 20, 22 | `display/manager.py`, `display/input/touch_coordinator.py` | Implemented — prompt closed, issue/change open pending test |
| 7.3.9 | `b02ed4ea` | `button-system-touch-targets` | 24, 27 | `display/manager.py`, `display/typography.py` (`touch_coordinator.py` read-only) | Implemented 2026-08-04 (`a34fd49`) — prompt closed, issue/change open pending test. *Clear settings* now has no entry point in source (§9.8.5 item 4) |
| 7.3.10 | `378703da` | `radial-centre-readout` | 25 | `display/manager.py`, `display/models.py`, `utils/config.py`, `config/config.yaml` | Implemented 2026-08-04 (`7035a93`) — prompt closed, issue/change open pending test. Live `DisplayMode.DIGITAL` refs survive outside the four-file scope (§9.8.5 item 1) |
| 7.3.11 | `5014040c` | `annular-band-indicator` | 26 | `display/manager.py` | Implemented 2026-08-04 (`730ae56`) — prompt closed, issue/change open pending test. Contrast criterion unsatisfiable as specified (§9.8.5 item 3); `BAND_COLOURS[0]` corrected (§9.8.6 item 1) |
| 7.3.12 | `5012004e` | `night-palette-toggle` | 29 | `display/manager.py`, `display/models.py` | Implemented 2026-08-04 (`2242387`) — prompt closed, issue/change open pending test. **Toggle cannot fire**: no `DOUBLE_TAP` gesture exists (§9.8.5 item 2) |
| 7.3.13 | `4c3c3e1f` | `update-view-progress` | 28 | `display/manager.py` | Implemented — prompt closed, issue/change open pending test |

Coverage check: recommendations 1–29 each appear exactly once across
rows 7.3.1 to 7.3.13. Status column added 2026-08-04 per the residual
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

| Task | UUID | Slug | Report items | Primary files | Status (2026-08-04) |
|---|---|---|---|---|---|
| 7.4.1 | `394c3bbb` | `config-device-persistence-retirement` | §3.6, §5.1; #1 (retirement branch), #6 | `utils/config.py` only — see §9.7 | Implemented 2026-08-04 (`251ea74`) — prompt closed, issue/change open pending test. Pre-flight grep confirmed no caller of the three retired methods |
| 7.4.2 | `5a9dc15e` | `watchdog-lock-discipline` | §3.3, §4.1; #2 | `core/watchdog.py`, `core/thread.py` | ✅ Closed |
| 7.4.3 | `11be4865` | `platform-detection-consolidation` | §3.2, §4.4; #3 | `utils/platform.py`, `utils/dependencies.py` | ✅ Closed |
| 7.4.4 | `52414414` | `device-store-pairing-robustness` | §3.4, §3.5, §5.6, §5.7; #4, #5 | `comm/device_store.py`, `comm/pairing.py` | Implemented — prompt closed, issue/change open pending test |
| 7.4.5 | `6481f8ce` | `transport-consolidation` | §4.3, §5.3, §5.8; #7 | `comm/transport.py`, `comm/rfcomm.py`, `comm/serial_transport.py`, `comm/tcp_transport.py`, `main.py`, `app.py` | Implemented 2026-08-04 in three stage commits (`3f5fc5e`, `fe879f9`, `51a930b`) — prompt closed, issue/change open pending test. **Gate cleared by carrying out the §7.5.5 reproduction first** (§9.8.4) |
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
| 7.5.3 | Read `frame_time_ms` from the periodic log line | display §10.2 | **Depends on 7.3.7** (rec 15), which has shipped. **Still not taken — this is now the sole outstanding gate on 7.3.5 and 7.3.6**, both of which were stopped and reported on 2026-08-04 rather than implemented (§9.8.2). Establishes the baseline against which they are judged |
| 7.5.4 | ✅ **DECIDED 2026-07-30 — retire.** No intended future use; `DeviceStore` is the sole device store. Call-graph evidence and two corrections to the previous framing are recorded in §7.4.8 | core §8.0 | 7.4.1 is unblocked and scoped to retirement (§3.6, §5.1). §3.1 is separated into 7.4.9, being independent of the disposition |
| 7.5.5 | ✅ **DISCHARGED 2026-08-04.** Reproduced under 7.4.5 with explicit synchronisation, against the unchanged files and again after Stage 1. Pre-change: `AttributeError` in all three transports. Post-change: handled `OSError`/`SerialException`, transport marked DISCONNECTED. Both results recorded (§9.8.4) | core §8.0 | Confirmed the §5.3 failure mode and supplied the regression test for 7.4.5. **Correction:** the `AttributeError` is caught by `send_command`'s broad handler, so the defect was silent in production — the reproduction discriminates by logged message, not by return value |
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

State as of 2026-08-04 (originally written 2026-07-30; see §9.0 for the
cross-check). All fourteen items below are now authored and implemented.

| Triple | UUID | State (2026-08-04) |
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

**Update 2026-08-04, two changes.** First, `49b21ace` (7.3.4) has
already been authored and implemented — the §7.5.1 gate cleared
mechanically once 7.3.3 shipped, per §8.3's own note. It is removed from
this table and tracked under §8.3; see §9.3. Second, all eight triples
below are now authored (§9.7). None is implemented.

**Update 2026-08-04, implementation.** Six of the eight are implemented
(§9.8). The two that remain are the two §7.5.3 gates.

| Triple | UUID | Unblocked by | State |
|---|---|---|---|
| 7.3.5 | `821919ce` | 7.5.3 baseline; keyed cache per §7.6.1 | ☐ **Gate failed — not implemented** |
| 7.3.6 | `9ed1c77e` | 7.3.5 | ☐ **Gate failed — not implemented** |
| 7.3.9 | `b02ed4ea` | — grouped here as an appearance change | ✅ Implemented (`a34fd49`) |
| 7.3.10 | `378703da` | — retires DIGITAL mode; largest behavioural change in the set | ✅ Implemented (`7035a93`) |
| 7.3.11 | `5014040c` | 7.3.1, and now 7.3.10 — see §9.7.2 item 6 | ✅ Implemented (`730ae56`) |
| 7.3.12 | `5012004e` | 7.3.11 and 7.3.9 | ✅ Implemented (`2242387`) — feature unreachable, §9.8.5 item 2 |
| 7.4.1 | `394c3bbb` | 7.5.4 decided — retire (§7.4.8). Large deletion, released here rather than with the v0.3.0 corrections | ✅ Implemented (`251ea74`) |
| 7.4.5 | `6481f8ce` | 7.5.5 reproduction | ✅ Implemented (`3f5fc5e`, `fe879f9`, `51a930b`) — gate cleared by carrying out the reproduction |

The five user interface triples are deliberately released together so the
product's appearance changes once rather than incrementally.

**Implementation order within v0.4.0.** The authoring surfaced ordering
constraints §7.6.1 does not carry, recorded in §9.7.2. The resulting
order is: `394c3bbb` (independent) → `821919ce` → `9ed1c77e` →
`b02ed4ea` → `378703da` → `5014040c` → `5012004e`, with `6481f8ce`
independent of the display chain and placed wherever its §7.5.5
reproduction is ready. `378703da` before `5014040c` is not optional:
implementing the annular indicator first means editing code that
`378703da` deletes.

**Order actually used, 2026-08-04.** `b02ed4ea` → `378703da` →
`5014040c` → `5012004e` → `394c3bbb` → `6481f8ce`, with the two gated
triples skipped. This differs from the above only in placing `394c3bbb`
sixth rather than first, which is immaterial: it touches
`utils/config.py` alone and is independent of the display chain. The
binding constraint — `378703da` before `5014040c` before `5012004e` —
was preserved.

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

## 9.0 Cross-Check — 2026-08-04

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
2026-08-04. Its own change document (`change-1143427b`, version 1.2)
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

### 9.7 Remaining Eight Triples Authored — 2026-08-04

All twenty triples in §7.3 and §7.4 now exist. The eight recorded in
§9.5 as unauthored were written on 2026-08-04: `b02ed4ea`, `378703da`,
`5014040c`, `5012004e`, `821919ce`, `9ed1c77e`, `394c3bbb`, `6481f8ce`.
Twenty-four documents, one issue/change/prompt triple each, all at
iteration 1 with `target_profile: claude_code`. None is implemented;
§7.6.4's rule that no source changes until the T04 prompt is approved
continues to apply.

#### 9.7.1 Authored Against §8.1's Advice

§8.1 records that four triples "cannot be authored correctly yet"
because they depend on §7.5 observations not yet taken. Three of those
— `821919ce`, `9ed1c77e`, `6481f8ce` — were authored anyway, on
instruction. The consequence is recorded rather than concealed: each
carries an explicit assumptions block in its issue and change
documents, and each names the section to be revised if the observation
contradicts it.

| Triple | Gate | Assumptions recorded |
|---|---|---|
| `821919ce` | §7.5.3 frame-time baseline | Three: that render cost is material; that the static layer dominates it rather than the write path; that a third 921,600-byte surface is affordable |
| `9ed1c77e` | §7.5.3, and 7.3.5 landing first | Two: that frame cost after 821919ce still justifies conditional rendering; that 30 Hz is visually acceptable for the needle |
| `6481f8ce` | §7.5.5 race reproduction | One, narrow: that the failure mode is `AttributeError`. The reproduction supplies the regression test rather than confirming the mechanism |

Each prompt makes collecting the observation its first implementation
step and instructs the executor to stop and report if it contradicts
the premise. `394c3bbb` is not gated — §7.5.4 is decided.

#### 9.7.2 Corrections to §7.3, §7.4 and §7.3.14 Found While Authoring

Seven, all recorded in the documents that carry them:

1. **`394c3bbb` file list.** §7.4 names `comm/device_store.py` and
   `comm/models.py` among its primary files. Neither may be modified:
   `BluetoothDevice` is live via `DeviceStore`, and `DeviceStore` is
   the surviving store. The change touches `utils/config.py` alone.
   The §7.4 row is corrected above.
2. **`b02ed4ea` file list.** `touch_coordinator.py` is read-only —
   applying the touch expansion inside `register_button_region` would
   enlarge every region in the application, including the setup
   subsystem's. It is applied by the caller instead.
3. **A fourth transport-name list.** Core §5.8 names three places
   holding the transport name set. There is a fourth, `app.py:267`'s
   `_fast_transports`, which classifies the same names by poll rate.
   Consolidating three of four would have left the least visible one.
4. **§7.3.14 omits `_handle_long_press`.** It says the swipe mode
   change is removed with DIGITAL. `_handle_long_press` also assigns
   DIGITAL (`manager.py:204`) and must survive with that assignment
   changed to RADIAL — it is the only route to OPTIONS.
5. **`_get_band_colour` must outlive its last caller.** Retiring
   DIGITAL leaves it uncalled, and a correct dead-code sweep would
   remove it — discarding the hysteresis `4c038bed` added, which
   `5014040c` requires. Retention is recorded in three places.
6. **Recommendation 26's subject largely dissolves.** The full-field
   band fill it replaces exists only in DIGITAL, which `378703da`
   retires. What remains for `5014040c` is RADIAL's light-grey ground,
   the tick and numeral colours that depend on it, and
   `_get_band_colour` losing a text-colour return that no longer has
   any consumer — which answers both questions §7.3.14 puts to that
   change document.
7. **The night toggle has nowhere to go.** §7.3.14 notes the toggle is
   subject to `b02ed4ea`'s geometry. It is also subject to that
   change's three-control budget, which is full — `b02ed4ea` already
   removes *Clear settings* for want of a fourth slot. `5012004e`
   sites the toggle as a double-tap gesture and names the options menu
   as its preferred home once display §7.7 frees space.

#### 9.7.3 One Open Decision

`b02ed4ea` leaves the options menu with no entry point to *Clear
settings*: the three-control budget has no fourth slot, and the
confirmation view recommendation 24 requires is reachable only from
that absent control. This is a faithful consequence of recommendation
24 as written, and display §7.7's re-layout (deferred to P10 per
§7.3.15) is where the space would come from. If an entry point is
required in v0.4.0 that is a scope extension to be agreed before the
prompt is executed. The prompt instructs the executor not to resolve it
by adding a fourth button.

#### 9.7.4 Discrepancy Discharge Status

- **D1** (type rule for core §5.x) — dischargeable. All five triples it
  named now exist: `6481f8ce` and `394c3bbb` carry `type: defect` as
  its §5.4 steps 4 and 5 require; `52414414`, `2d545bf5` and
  `d32ccc49` were typed correctly when authored.
- **D2** — discharged 2026-07-30; `d32ccc49` landed with its edit
  confined to `ConfigManager.__init__`, verified not to overlap
  `394c3bbb`'s deletion region.
- **D3** — addressed in document but not discharged: `821919ce`
  specifies the keyed cache with the palette and band members present
  from the outset, and `5014040c` and `5012004e` each extend the key's
  values. Discharge requires implementation and the night-toggle redraw
  check.
- **D4** — discharged; `44bca479` shipped, so `b02ed4ea` registers
  through the mode-entry hook by construction.
- **D5** — unchanged; awaits `b02ed4ea` on the panel.

[Return to Table of Contents](<#table of contents>)

---

### 9.8 Implementation — 2026-08-04

Six of the eight v0.4.0 triples were implemented in a single session.
Full detail is in
`ai/workspace/report/v0.4.0-triple-implementation-session.md`; this
section records what the task list needs to carry.

#### 9.8.1 Outcome

| Triple | Outcome | Commit |
|---|---|---|
| `b02ed4ea` | ✅ Implemented, verified, prompt closed | `a34fd49` |
| `378703da` | ✅ Implemented, verified, prompt closed | `7035a93` |
| `5014040c` | ✅ Implemented, verified, prompt closed | `730ae56` |
| `5012004e` | ✅ Implemented, verified, prompt closed | `2242387` |
| `394c3bbb` | ✅ Implemented, verified, prompt closed | `251ea74` |
| `6481f8ce` | ✅ Implemented, verified, prompt closed | `3f5fc5e`, `fe879f9`, `51a930b` |
| `821919ce` | ☐ Gate failed — stopped and reported | — |
| `9ed1c77e` | ☐ Gate failed — stopped and reported | — |

Branch `v0.4.0-display-triples` from `32927fc`, eight commits, **not
pushed**. `main` is unchanged. Each commit carries one triple's source
changes plus that triple's prompt T-Doc move into `closed/`.
`6481f8ce` is three commits, one per stage, as its prompt requires.

All sixteen issue and change T-Docs remain **active** per §8.2.1. No T06
result documents were produced.

#### 9.8.2 The Two Gated Triples

`821919ce` and `9ed1c77e` were not implemented. Both prompts make the
§7.5.3 `frame_time_ms` baseline a gate and instruct stop-and-report if
it is absent. It is absent: `ai/workspace/test/result/` is empty, §7.5
records 7.5.3 unresolved, and the §8.4 session requires deployment to
`gtach.local`.

No substitute measurement was taken. A frame time from macOS Apple
Silicon is not a proxy for a Pi Zero 2W and would not have cleared the
gate honestly.

This is §8.1's advice vindicated: §9.7.1 recorded that these two were
authored against it, and the first attempt to execute them stopped at
exactly the point §8.1 predicted. Nothing else depended on them —
`5012004e`'s prompt anticipates the case and instructs that the
static-layer invalidation check be recorded as not applicable.

#### 9.8.3 Verification Method

`pytest tests/` was not used and proves nothing: the suite collects zero
items and pytest is not importable in the working environment. Each
triple was verified by an ephemeral script asserting its own prompt's
success criteria against the real source, executing extracted functions
against stubs rather than inspecting text. Equivalence claims were
asserted against the pre-change source pulled from git — notably the
band-index sequence for `5014040c` and the day palette for `5012004e`.

The harnesses were not retained as project artefacts. See §9.8.7.

#### 9.8.4 §7.5.5 Discharged

The transport-race reproduction was carried out under `6481f8ce`, first
against the unchanged files and again after Stage 1, with explicit
synchronisation rather than sleeps. Pre-change: `AttributeError` in all
three transports. Post-change: handled `OSError`/`SerialException` with
the transport marked DISCONNECTED. Both results recorded.

One correction to the §5.3 framing: the `AttributeError` is caught by
`send_command`'s broad `except Exception` and returns `None` exactly as
a handled I/O error does. The defect was therefore **silent in
production**, and a reproduction that classifies by return value does
not discriminate. The first attempt did not; it was rewritten to
classify by logged message.

#### 9.8.5 Findings Requiring Decision

Four defects outside an implementing executor's authority. None is a
defect in the delivered code; each is a defect in a specification or a
gap the specifications did not anticipate. Each warrants a T03 issue
under P04 if it is to be tracked.

1. **Live `DisplayMode.DIGITAL` references survive `378703da`.**
   `display/touch.py` (8 sites) and `display/navigation_gestures.py`
   (2 sites) still reference the removed enum member, and both are
   instantiated at runtime by
   `DisplayManager._initialize_legacy_components`. The references sit in
   method bodies, so imports still succeed; those paths will raise
   `AttributeError` if executed. `378703da`'s four-file constraint
   excludes both modules, and its success criterion
   "grep -r 'DIGITAL' src/gtach returns no match" is unsatisfiable
   within that constraint — and additionally conflicts with its own
   EDIT 6(a), which mandates the literal string in the migration branch.
   **This is the only finding that can fault the running application.**

2. **The night palette toggle cannot fire.** `5012004e` specifies a
   double-tap. `GestureType` has no `DOUBLE_TAP` member and the touch
   coordinator performs no double-tap disambiguation; the prompt
   declares `display/input` read-only. The prompt's own edge-case list
   asked for this to be verified rather than assumed, and the answer is
   that no such disambiguation exists. Delivered with the registration
   conditional on `getattr(GestureType, 'DOUBLE_TAP', None)`, so the
   toggle goes live the moment the subsystem provides the gesture. Until
   then the feature is complete and unreachable.

3. **The contrast requirement is arithmetically unsatisfiable.**
   `5014040c` and `5012004e` each fix the palette values *and* require
   every band colour to reach 3:1 against the face ground. Both cannot
   hold: pure blue's relative luminance is 0.0722 and 3:1 against a
   near-black ground needs ~0.103. `5012004e` compounds it by also
   requiring every night colour to be dimmer than its day counterpart,
   capping blue from the other side. Measured as delivered: day blue
   2.21:1, night blue 1.55:1, `FACE_TRACK` 1.67:1, `FACE_EDGE` 2.02:1,
   `FACE_LINE` 2.76:1. All other pairs pass, including day tick 14.55:1
   and night tick 4.67:1. The specified constants were implemented as
   written rather than silently altered, because both prompts forbid
   changing the colours. Resolution requires a lighter blue (breaking
   the dimmer-than-day rule), a lighter ground (breaking the
   emitted-light goal), or dropping the 3:1 bar for band fills. The
   subordinate case is that a 3:1 bar may simply be the wrong test for a
   deliberately subtle track and hairline edge.

4. **`b02ed4ea` leaves *Clear settings* with no entry point.** Recorded
   as an open decision in §9.7.3 before implementation; now live in
   source. The options screen offers no route to the control at all.
   §7.7's circular re-layout is where the recovered space comes from.

#### 9.8.6 Deviations from Prompt Specifications

Three, each recorded in source and in the relevant commit message.

1. **`BAND_COLOURS[0]`** — `5014040c` EDIT C specifies `(0, 0, 0)`;
   delivered as `(0, 0, 255)`. That black was DIGITAL's idle *screen*
   background and was never an arc colour; adopting it would have
   repainted the idle arc segment black on a near-black face and erased
   it. The prompt's EDIT C palette and its constraint "Blue, blue,
   green, yellow, orange, red are unchanged" contradict each other; the
   constraint governs, because it describes what is drawn.

2. **Transport primitives are not `@abstractmethod`** — `6481f8ce`
   Stage 2 specifies them as abstract; delivered as concrete methods
   raising `NotImplementedError`, with a type check in
   `OBDTransport.__init__` preserving the `TypeError` on direct
   instantiation. Declaring them abstract makes `SimTransport`
   uninstantiable — it inherits `OBDTransport`, overrides all five
   skeleton methods and supplies none of the four primitives — and the
   same prompt forbids modifying it. Abstract declarations would have
   broken `simtcp` and `simbt` outright. Caught by the verification
   pass, not by inspection.

3. **`saved_devices` in comments** — `394c3bbb` requires the string to
   appear nowhere in `src/gtach`. Delivered with the token absent from
   code and the two explanatory comments reworded, so the criterion
   passes literally while the migration behaviour stays documented.

A fourth, minor: `app.py:91` still tests `transport_arg == 'simbt'` to
select the pairing factory. `6481f8ce` Stage 3 names three sites and
says to change nothing else, so it was left; it is a fourth place a
transport name appears as a literal.

#### 9.8.7 Governance Gaps Left Open

- **No T06 result documents.** The verification of §9.8.3 is recorded in
  the report and in commit messages, not in T05/T06 form. If §8.2.1's
  closure path is to be followed for these six triples, T05 test
  documents and T06 results are the missing artefacts.
- **§8.2's minimal pytest suite remains unwritten.** `tests/` still
  collects zero items. Every verification claim rests on ephemeral
  scripts that were not retained. Converting the six harnesses into
  `tests/` would preserve the evidence and discharge §8.2 together.
- **The branch is unpushed and unmerged.** v0.4.0 cannot be cut: two of
  its eight triples are unimplemented and one delivered feature cannot
  be operated (§9.8.5 item 2).

[Return to Table of Contents](<#table of contents>)

### 9.9 On-Target Session — 2026-08-05

The `v0.4.0-display-triples` branch was deployed to `gtach.local` and
`logs/` pulled back. The session confirmed §9.8.5 item 1 and produced
two further findings.

#### 9.9.1 §9.8.5 Item 1 Confirmed — Operator Trapped on the Options Screen

`logs/start.log` carries five lines and no other errors in 3.5 MB:

```
06:39:54,899  TouchHandler ERROR Short press handling error: DIGITAL
06:39:55,878  TouchHandler ERROR Short press handling error: DIGITAL
06:39:57,403  TouchHandler ERROR Short press handling error: DIGITAL
06:40:08,372  TouchHandler ERROR Long press handling error: DIGITAL
06:40:09,798  TouchHandler ERROR Long press handling error: DIGITAL
```

The operator could not leave the OPTIONS screen. `touch.py:171` names
`DisplayMode.DIGITAL`, which `change-378703da` removed; the access
raises `AttributeError('DIGITAL')`, `touch.py:174` catches it, and the
gesture silently does nothing. The message body is the bare word
because both handlers log `f'...: {e}'` without the exception type.

Two facts the static review did not establish. First, `TouchHandler`
registers `_handle_touch_event` on a **started** touch interface
(`touch.py:78`), so its handlers are the ones that fire — the log
attributes all five errors to `TouchHandler`, not `DisplayManager`.
Second, the fault is swallowed, which is why it presents as an inert
control rather than a crash, and why five ERROR lines sat in the log
from the first session without anything appearing to be wrong.

Raised as **`7f2a9c04`** — issue, change and prompt authored 2026-08-05,
severity high. Not gated. Should ship ahead of the rest of v0.4.0 if a
partial deployment is possible.

#### 9.9.2 New — Debug Toggle Fires but the Handler Fails

The operator reported being unable to toggle debug mode. The control
worked; what it calls did not:

```
06:40:05,090  TouchEventCoordinator DEBUG Button debug_toggle pressed at (306, 255)
06:40:05,091  DisplayManager INFO Debug logging toggle -> on
06:40:05,091  gtach.app DEBUG Could not toggle debug logging:
              'function' object has no attribute '_debug_handler'
```

`app.py:155` does `from . import main as _main` and then reads
`_main._debug_handler`. `_main` binds to the **function** `main`, not
the module — `gtach/__init__.py` exports the name — so the attribute
access fails. The exception is caught at `app.py:166` and logged at
DEBUG, so nothing surfaces to the operator.

Two consequences, both visible in the log. `debug.log` is 0 bytes while
`start.log` holds 57,560 DEBUG lines, so debug output is going to the
wrong file. And `_debug_logging_on` starts False while the application
is already logging at DEBUG, so the options label reads *Debug: Off*
when debug is in fact on — the toggle inverts a flag that never
described reality.

**Not yet raised.** It is a defect in `change-bd8f95b7`'s two-file
logging rather than in any v0.4.0 triple, and it wants its own T03.
Recorded here so it is not lost.

#### 9.9.3 Scope Extension Agreed — Swipe Navigation for OPTIONS

The operator proposed replacing the long-press OPTIONS toggle with
swipe-down to enter and swipe-up to leave, reasoning that a toggle has
no second route when one direction fails — which is exactly what
§9.9.1 produced.

Agreed by consensus and authored as **`3e8b1d72`**, separate from
`7f2a9c04` rather than folded into it: a defect fix and a navigation
redesign landing together would make a subsequent navigation problem
unattributable. `3e8b1d72` depends on `7f2a9c04`.

Two findings from scoping it. The touch subsystem **already** detects
and dispatches `SWIPE_UP` and `SWIPE_DOWN` — `GestureType` declares
them, `_recognize_gesture` returns them, `handle_gesture` dispatches
them — so no work in `display/input` is required. This distinguishes it
sharply from `5012004e`'s double-tap palette toggle, which is
unreachable because no `DOUBLE_TAP` member exists.

And there are **two live long-press handlers**, in `manager.py` and
`touch.py`. Any change to how OPTIONS is reached must address both or
produce the enterable-but-unleavable asymmetry the proposal exists to
prevent. `3e8b1d72` has the legacy path delegate to the `DisplayManager`
handlers so the two agree by construction.

#### 9.9.4 Root Cause of §9.9.1 — A File-Scoped Constraint on a Package-Wide Change

`prompt-378703da` removed an enum member — a package-wide interface
change — under a constraint permitting four files, and carried three
requirements no two of which could hold together: *grep -r 'DIGITAL'
src/gtach returns no match*, the four-file list, and its own EDIT 6(a)
mandating the literal string in the migration branch.

The executor recorded the conflict at report §6.3 and did not exceed
its scope, which was correct. The defect is in the prompt.

The lesson is recorded in `issue-7f2a9c04` prevention: a change that
alters a package-wide interface cannot be scoped by file list — the
scope is every reference, and the prompt should be written by grepping
for them rather than by naming the files the author expected to be
involved. `change-7f2a9c04` accordingly makes its success criterion a
repository-wide grep.

[Return to Table of Contents](<#table of contents>)

### 9.10 Second On-Target Session — 2026-08-05

`7f2a9c04` and `3e8b1d72` were implemented and deployed. The session
log carries **one ERROR in 362 KB** and no `DIGITAL` line: both fixes
work, swipe navigation operates, and the operator confirmed entering
and leaving OPTIONS. Four further findings.

#### 9.10.1 The Debug Toggle Is Still Broken — Raised as `c1d4b8e6`

The operator reported it working. The log disagrees, three presses,
three identical failures:

```
07:59:38,814  DisplayManager INFO  Debug logging toggle -> on
07:59:38,815  gtach.app DEBUG      Could not toggle debug logging:
                                   'function' object has no attribute '_debug_handler'
```

Root cause established: `gtach/__init__.py:11` does
`from .main import main`, so the package attribute `main` **is** the
function. `app.py`'s `from . import main as _main` therefore retrieves
the function, whose namespace holds no `_debug_handler`. The same
pattern breaks `_finish_startup_logging`, so `_start_handler` is never
demoted — which is why `start.log` reached 3.5 MB in one session while
`debug.log` stayed at 0 bytes.

The fault is **self-concealing**: both sites log at DEBUG, and one of
them is the control that turns DEBUG on. The label flips because
`_debug_logging_on` is inverted before the callback runs, which is
exactly why it appears to work.

Recorded as §9.9.2 on 2026-08-05 without a T03. Now raised.

#### 9.10.2 New — `engine_profiles.yaml` Is Not in the Wheel

```
07:59:15,874  load_engine_profile WARNING  Engine profiles file not found at
              /opt/gtach/venv/.../gtach/assets/engine_profiles.yaml, using defaults
```

`pyproject.toml:69` declares package-data as `assets/fonts/*.ttf` and
`*.otf` only. Confirmed against the built wheel: `Michroma-Regular.ttf`
is the sole entry under `assets/`.

**Current impact is zero**, and the reason matters: the
`abarth_595_turismo` profile's six thresholds are identical to the
`RPMBands` dataclass defaults, so the fallback yields the correct
numbers by coincidence. What is broken is everything the file exists
for — `generic_turbo_4cyl` and `generic_na_4cyl` are unreachable, the
`engine_profile` key is inert, and the first threshold tuning will not
reach the target.

Second occurrence of this defect class; `issue-d7f2b4e6` (Michroma font
missing from wheel) was the first, and its fix added the fonts glob
that still stands beside the unpackaged YAML.

#### 9.10.3 Carried Forward — A Second Stale Footer

`_draw_update_view` (`manager.py:1672`) still renders *"Long press to
return"*. `change-3e8b1d72` corrected the identical string in
`_draw_options_menu` and made long press inert in both handler paths;
this one was outside that prompt's stated scope and its executor
reported it at §6.2 rather than exceeding scope. The update view now
instructs a gesture that does nothing.

Raised at the operator's explicit request so it is not lost.

**§9.10.1 to §9.10.3 are grouped into one triple, `c1d4b8e6`**, on the
`change-d32ccc49` pattern: three small faults in three files, none
dependent on another. Authored 2026-08-05, not implemented.

#### 9.10.4 Open — OBD Response Stream Desynchronises After a Timeout

Not raised. Needs its own investigation and triple.

The ELM327 emulator is paired and answering — the log shows a clean
connect and a correct `ATZ` → `ELM327 v1.5` handshake. Then:

```
07:59:17,588  TX: 0100
07:59:18,632  WARNING  Timeout waiting for response (cmd='0100', timeout=1.0s)
07:59:18,633  ERROR    Initialization failed: No connection to vehicle
07:59:20,629  RX: '4100983A8013\r4100BE3FA813'      <- 0100's answer, late, doubled
07:59:21,133  RX: 'ELM327 v1.5'   after TX ATE0     <- ATZ's answer
07:59:21,137  RX: 'ATE0\rOK'      after TX ATL0     <- ATE0's answer
07:59:21,167  RX: 'OK\r\r>SEARCHING...' after TX 0100
```

Two distinct faults. The `0100` timeout of 1.0 s is shorter than the
ELM327's protocol search, which emits `SEARCHING...` and can take
several seconds. And the late response is **not drained**, so it sits
in the buffer and every subsequent read returns the previous command's
answer — the stream is offset by one and stays offset.

The second is the more serious: a single timeout permanently
desynchronises the session. Same class as `issue-a3f1d8e2` (ATZ on
reconnect causing init timeout), which is closed.

This is why OBD initialisation fails against a working emulator.

[Return to Table of Contents](<#table of contents>)

### 9.11 §8.4 Observation Session — Discharged From Logs

The §8.4 session was planned as a sitting on `gtach.local` collecting all
six §7.5 items. Five of the six are answerable from logs already pulled,
because the instrumentation each depended on has since shipped. Only
§7.5.2 still requires eyes on the panel.

Evidence is `logs/start.log` and `logs/debug.log`, session 2026-08-05
08:42:18 to 08:43:36, application version 0.3.3.

#### 9.11.1 Results

| Item | Result |
|---|---|
| 7.5.1 framebuffer geometry | ✅ **Discharged.** `Framebuffer geometry: 480x480, virtual 480, 32-bit, stride 1920 (sysfs)`. Depth is 32 and stride is 1920, exactly the values `engine.py` assumed. **Display report §8.3 is not an active fault.** `Page flip enabled: two framebuffer halves mapped` confirms `49b21ace` is operating |
| 7.5.2 flicker characterisation | ☐ **Outstanding.** Cannot be derived from a log. The only item still needing the panel |
| 7.5.3 frame-time baseline | ✅ **Discharged, indicatively.** See §9.11.2 |
| 7.5.4 `ConfigManager` disposition | ✅ Decided 2026-07-30 (retire); implemented by `394c3bbb` |
| 7.5.5 transport race | ✅ Discharged by `6481f8ce`'s reproduction (§9.8.4) |
| 7.5.6 hardware revision | ⚠️ **Substantively answered.** `Selected platform: RASPBERRY_PI_ZERO_2W (score: 1.85)` — detection is correct, which is what §7.5.6 existed to establish. The raw revision string is not logged, so the check is of the outcome rather than the input. `11be4865` had already corrected the `lstrip()` defect |

#### 9.11.2 The Frame-Time Baseline

Four periodic samples, correlated against what was on screen:

| Time | Sample | On screen |
|---|---|---|
| 08:42:59 | 59.0 FPS, **15.3 ms** | RADIAL — `obd_protocol` RUNNING since 08:42:18, so not the disconnected screen |
| 08:43:10 | 59.0 FPS, **6.3 ms** | OPTIONS — `simulation_mode` region registered 08:43:03 |
| 08:43:20 | 60.0 FPS, **14.7 ms** | RADIAL, simulation mode (on since 08:43:07) |
| 08:43:30 | 53.0 FPS, **19.3 ms** | RADIAL, simulation mode |

`frame_time_ms` measures render cost rather than loop period, `0b00759c`
having moved `record_frame_end` before the pacing sleep. So:

- **RADIAL costs 14.7 to 19.3 ms against a 16.67 ms budget** — rendering
  alone consumes 88% to 116% of the frame. The 53 FPS sample is the
  overrun showing.
- **The static OPTIONS screen costs 6.3 ms per frame**, sixty times a
  second, to draw an image that does not change.

**Caveat, stated rather than buried.** Three RADIAL samples from one
90-second session. The direction is unambiguous but this is indicative,
not a rigorous baseline. A five-minute run on the gauge would give
~30 samples; see §9.11.4.

#### 9.11.3 Gate Evaluation

**`821919ce` — gate CLEARS. Assumption A1 holds, and more strongly than
it was framed.** §9.7.1 recorded A1 as "render cost is a material
fraction of the 16.67 ms budget". It is not merely material; it is
at or over the whole budget. The static-layer cache is justified.

- **A2** — that the static layer dominates rather than the framebuffer
  write path — is *supported but not proven*. The write-path work
  (`66ef59a0`, `49b21ace`) has landed and page flip is confirmed
  operating, so the residual 14.7–19.3 ms sits after those
  optimisations. That points at rendering without isolating it.
- **A3** — memory. Steady at 37.1 MB. A third 921,600-byte surface adds
  about 0.9 MB. Affordable.

**`9ed1c77e` — partially cleared, and its two recommendations now
separate cleanly.**

- **Recommendation 12 (`fps_limit` 30) is supported independently of any
  assumption.** The application cannot sustain 60 Hz — 53 FPS was
  observed — and a 33.3 ms budget comfortably exceeds the 16.4 ms mean
  render cost. This is the cheapest available improvement and it no
  longer rests on A2's judgement about needle smoothness.
- **Recommendation 13 (conditional render)** is supported by the OPTIONS
  measurement: 6.3 ms per frame for a wholly static screen. Full
  evaluation still waits on `821919ce`, since that change alters what a
  frame costs.

#### 9.11.4 Residual On-Panel Work

Reduced from six items to two, neither long.

1. **§7.5.2 flicker characterisation.** Against display report §10.3's
   discrimination table: is it a horizontal band moving vertically
   (tearing, §4.1), a full-field colour alternation near a band
   threshold (band thrash, §4.2 — should already be gone, `4c038bed`
   added hysteresis), or confined to above `caution_start` (the
   intentional shift-cue flash, §4.4)? Then §10.4's simulation-mode
   sweep, which crosses every band boundary once per 6.28 s.
2. **A firmer frame-time baseline.** Leave the gauge running five
   minutes without touching the screen, then pull the logs. Thirty
   samples rather than three, and all of them RADIAL.

Both can be done in one sitting of about ten minutes.

#### 9.11.5 Collateral — The OBD Desynchronisation Reproduces

Not part of §8.4, but the same log carries it again and more clearly
than §9.10.4 recorded:

```
TX: ATL0   ->  RX: 'ATE0\rOK'     one command behind
TX: ATSP0  ->  RX: 'OK'
TX: 0100   ->  RX: 'OK'            0100 receives ATSP0's acknowledgement
TX: 010C   ->  (no response)
TX: 010C   ->  (no response)
TX: 010C   ->  (no response)
           ->  RX: '4100983A8013\r4100BE3FA813'   0100's answer, 3 s late
```

`0100` — the supported-PID query — receives an `OK` that belongs to
`ATSP0`, and `010C` (engine RPM) is polled three times with nothing
matching it before a stale `0100` answer arrives. The offset does not
recover.

Whether this corrupts the displayed reading was *not established* at the
time of writing. **It was tested on 2026-08-05 and does not — see
§9.11.6, which supersedes this section's severity assessment.**

[Return to Table of Contents](<#table of contents>)

### 9.11.6 Long Run — 52 Minutes, 2026-08-05 09:34

The residual work of §9.11.4 was carried out: a 52-minute run
(08:42:56 to 09:34:42), simulation mode for the bulk and Bluetooth
against the ELM327 emulator for the final 75 seconds. 15.9 MB of debug
log, **two warnings and no errors** — both warnings in the first two
seconds, being the initial `010C` timeouts.

**The frame-time baseline is now firm.** 297 samples:

| | ms |
|---|---|
| min | 6.3 |
| p25 | 14.3 |
| **median** | **14.7** |
| mean | 16.0 |
| p90 | 19.7 |
| max | 21.2 |

- **32% of frames exceed the 16.67 ms budget at 60 Hz.**
- **0% exceed the 33.3 ms budget at 30 Hz.** Not one sample in 297.

Render cost is the same in both modes — median 14.7 ms in simulation
(n=290) against 14.9 ms on Bluetooth (n=7) — so the large simulation
sample is a valid baseline for render cost. The Bluetooth sample is too
small to say anything about the tail.

**Consequence for `9ed1c77e` recommendation 12.** Reducing `fps_limit`
to 30 would eliminate **every** budget overrun observed, with a
one-line configuration change and no code. That is a stronger result
than the recommendation claimed for itself, and it reorders the
sequence: recommendation 12 should ship *before* `821919ce`, which then
becomes an optimisation on a renderer that already meets its deadline
rather than a rescue for one that does not.

**The OBD desynchronisation does not corrupt the reading — §9.10.4 and
§9.11.5 are corrected.** Two findings:

1. *It recovers.* In steady state every `TX: 010C` is answered by a
   matching `410C…`, sampled across the run. The offset is confined to
   the initialisation handshake, where the commands differ from one
   another; once polling settles into uniform `010C` the stream
   re-pairs. The earlier claim that "the offset does not recover" was
   drawn from a 90-second session and was wrong.
2. *The displayed value is correct.* Over the Bluetooth window — 874
   responses, 4,193 frames drawn — the emulator sent 14 distinct values
   spanning 0 to 4,208 RPM, and **not one displayed value fell outside
   that range**. Displayed values lie between the discrete received
   ones because `_condition_rpm`'s EMA interpolates, which is
   `4c038bed` working as designed.

§9.10.4's severity accordingly drops from *may corrupt the primary
reading* to *initialisation-phase robustness*: two timeouts, one ERROR
and a few seconds of delay at startup. Still worth a triple — a
one-second timeout against an ELM327 protocol search that emits
`SEARCHING…` is simply too short, and the undrained buffer is what
makes the first responses arrive concatenated — but it is not urgent
and it does not threaten the instrument's accuracy.

**§7.5.2 remains the only outstanding observation.** The flicker
characterisation still needs eyes on the panel; no log answers it.
**Discharged 2026-08-05 — see §9.11.7.**

[Return to Table of Contents](<#table of contents>)

### 9.11.7 §7.5.2 Discharged — The Flicker Is Gone

`fps_limit` was set to 30 on the target and the application restarted at
10:17:18. Observed on the panel: **no tearing, no flashing, no band
thrash, and the needle reads acceptably at 30 Hz.**

That discharges §7.5.2, the last §8.4 item, and closes display report
§4.0 in full.

#### 9.11.7.1 The 30 Hz Baseline

32 samples:

| | 60 Hz (n=297) | 30 Hz (n=32) |
|---|---|---|
| FPS observed | 52, 53, 54, 56, 59, 60 | **30.0 in every sample** |
| frame median | 14.7 ms | 15.3 ms |
| frame p90 | 19.7 ms | 18.7 ms |
| frame max | 21.2 ms | 19.1 ms |
| **over budget** | **32%** | **0 of 32** |
| budget used at median | 88% | **46%** |

Render cost is unchanged, as it should be — only the deadline moved.

#### 9.11.7.2 Why the Flicker Went

The FPS column is the finding. At 60 Hz the measured rate varied across
six distinct values; at 30 Hz it is 30.0 in all 32 samples. **Frame
pacing has gone from irregular to exact.**

Display report §4.5 identified frame-time jitter as what makes a tear
seam "move erratically instead of drifting smoothly", and §4.1 named
unsynchronised writes as the primary tearing mechanism. The causes were
addressed in sequence and the symptom is now absent:

| Mechanism | Addressed by |
|---|---|
| §4.1 unsynchronised writes | `66ef59a0` removed the per-frame flush/sync; `49b21ace` added page flip |
| §4.2 band colour thrash | `4c038bed` added threshold hysteresis |
| §4.3 displayed value churn | `4c038bed` added EMA smoothing |
| §4.4 unstable flash duty cycle | `4c038bed` derived the phase from the frame counter |
| §4.5 frame-time jitter | `9ed1c77e` Part 2 — `fps_limit` 30 removed every overrun |

No single change is provable as *the* fix, and this document should not
claim one. What is established is that all five candidate mechanisms
have been addressed and the symptom no longer occurs.

#### 9.11.7.3 Consequence — The Two Remaining Triples Lose Their Justification

`821919ce`'s own change document set the condition for withdrawal: "If
RADIAL frames already complete well inside the budget, this change buys
little and its medium risk is not justified — withdraw or defer it
rather than proceeding." Frames now complete at 46% of budget with zero
overruns and no flicker. **That condition is met.**

`9ed1c77e` Part 3 (conditional render) is in the same position. Static
screens still redraw 30 times a second to no effect, which is real
waste, but there is no longer a problem it solves — and its own risk is
the flash-suppression trap recorded in its prompt.

**Recommendation: defer both, and cut v0.4.0 without them.** They remain
authored and can be implemented if a future need appears — a heavier
render path, a slower target, or a measured GIL contention problem. What
should not happen is medium-risk optimisation of a renderer that meets
its deadline and shows no visible fault.

#### 9.11.7.4 Two Small Defects the Change Exposed

1. **`PerformanceMonitor` does not follow `fps_limit`.**
   `manager.py:159` constructs it as `PerformanceMonitor(target_fps=60)`,
   hardcoded. At 30 Hz its `frame_time_target` is still 16.67 ms, its
   dropped-frame threshold 25 ms rather than 50, its `min_fps` alarm 48
   rather than 24, and its history deque sized for 60 fps. Any
   dropped-frame figure read at 30 Hz is wrong. The startup line
   reporting "target: 60 FPS" is the visible symptom — and it misled
   this analysis once, being cited as evidence of the running frame rate
   before the measured FPS samples corrected it.

2. **`debug.log` never truncates.** `main.py:47` passes `mode='w'` to
   `RotatingFileHandler`, which **silently overrides it to `'a'`
   whenever `maxBytes > 0`** — verified against CPython's source and
   reproduced. The intent is defeated and the `mode='w'` is dead code.
   With `maxBytes` at 100 MB, rotation has never fired; the file reached
   31.6 MB spanning three sessions, and had to be segmented by timestamp
   for every analysis in §9.11.

[Return to Table of Contents](<#table of contents>)

### 9.13 The Efficiency Triples Deferred — 2026-08-05

`821919ce` and `9ed1c77e` Part 3 are deferred. Neither is wrong; both
were overtaken by measurement.

#### 9.13.1 The Condition Was Written in Advance and Was Met

`change-821919ce` recorded its own withdrawal condition when it was
authored on 2026-08-04, before any baseline existed:

> If RADIAL frames already complete well inside the budget, this change
> buys little and its medium risk is not justified — withdraw or defer
> it rather than proceeding.

The baseline was collected on 2026-08-05 (§9.11.6) and `9ed1c77e`
Part 2 then halved the frame rate. The condition holds:

| | At authoring (60 Hz) | Now (30 Hz) |
|---|---|---|
| Budget | 16.67 ms | 33.3 ms |
| Median render | 14.7 ms | 15.3 ms |
| Budget used | 88% | **46%** |
| Frames over budget | **32%** | **0 of 32** |
| Flicker | the open question | **resolved** (§9.11.7) |

Assumption A1 — "render cost is a material fraction of the budget" —
was true when written and is not true now. A3 was confirmed at 37.1 MB
steady. A2 was never isolated and now need not be.

`9ed1c77e` Part 3 falls with it. Its own change document named the
fallback: *take the fps_limit reduction alone if assumption A1 fails.*
It did.

#### 9.13.2 What Remains True

The waste both triples describe is real and unchanged. Twenty-seven
invariant primitives and eight invariant text rasterisations are drawn
per frame, and the static screens redraw thirty times a second to no
effect. It is waste the instrument can afford, which is the whole of
the argument.

Both are **deferred, not rejected**. The documents are complete and
implementable as authored. A heavier render path, a slower target, or a
measured GIL-contention problem would make either relevant again.

#### 9.13.3 A T02 Schema Gap This Exposed

`change_info.status` had no `deferred` value, though `issue_info.status`
has carried one since v1.0. The only available label for a sound change
not being taken forward was `rejected`, which asserts it was found wrong
on its merits.

`deferred` was added to the T02 enum (T04… T02-change.md v1.4) rather
than mislabelling these two. There is precedent: v1.3 added `closed` for
the same kind of reason.

#### 9.13.4 §8.1 Vindicated Twice

§8.1 recorded that these triples "cannot be authored correctly yet"
because they depended on observations not yet taken, and §9.7.1 recorded
that they were authored against that advice on instruction, each
carrying explicit assumptions.

Both halves of that record proved useful. The prompts halted at their
gates rather than optimising a renderer with no fault, and the
enumerated assumptions made the deferral a matter of checking A1 against
a number rather than re-arguing the design. Authoring ahead of the
measurement cost two documents that will not be used; authoring the code
ahead of it would have cost a medium-risk change to the render path.

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
| 9.0 | 2026-08-04 | Added §9.0, cross-checking §7.0's twenty triples against governance-document state, `src/gtach` and pushed git/GitHub history, following William's report that several prompts had closed with issues/changes left open pending test results. Confirmed the pattern for eight triples (`66ef59a0`, `cb28980f`, `49b21ace`, `44bca479`, `4c3c3e1f`, `52414414`, `2d545bf5`, `d32ccc49`) — prompt closed, issue and change open. Added a Status column to §7.3 and §7.4 (per the residual observation in `task-list-cross-check-discrepancies.md` §10.2) and updated §0.0, §7.5.1 and §8.3. Recorded that `49b21ace` (7.3.4) was reclassified from v0.4.0 into v0.3.0 once `cb28980f` (7.3.3) cleared its gate mechanically (§9.3); removed it from §8.5. Flagged `1143427b` (7.4.9) as closed — issue, change and prompt — without a T06 result document and without appearing on §8.2.1's grandfather list; its own change document records the on-target verification step as open and the coupled T05 as `status: planned` with all cases `not_run` (§9.4). Confirmed by direct source inspection that `394c3bbb` (7.4.1) remains unimplemented — the `ConfigManager` device-persistence methods are still present — and that all eight remaining v0.4.0 triples have no governance documents or matching commits (§9.5). |
| 10.0 | 2026-08-04 | Authored the eight remaining triples — `b02ed4ea`, `378703da`, `5014040c`, `5012004e`, `821919ce`, `9ed1c77e`, `394c3bbb`, `6481f8ce` — completing all twenty in §7.0. Twenty-four documents, all iteration 1, `target_profile: claude_code`, none implemented. Added §9.7 recording: that three gated triples were authored against §8.1's advice on instruction, each carrying an explicit assumptions block and a stop-and-report first implementation step (§9.7.1); seven corrections found while authoring, chiefly that `394c3bbb` must not touch `comm/models.py` or `comm/device_store.py`, that a fourth transport-name list exists at `app.py:267`, that `_handle_long_press` survives DIGITAL's retirement with its assignment changed, that `_get_band_colour` must outlive its last caller for `5014040c`'s benefit, and that recommendation 26's subject largely dissolves once DIGITAL is retired (§9.7.2); one open decision, the absent entry point to *Clear settings* under `b02ed4ea`'s three-control budget (§9.7.3); and the discharge status of all five cross-check discrepancies (§9.7.4). Added Status columns to the §7.3 and §7.4 rows, a state column and an implementation order to §8.5, and corrected §9.0's date, which revision 9.0 recorded as 2026-07-31 in error. |
| 17.0 | 2026-08-05 | Added §9.13 recording the deferral of `821919ce` and `9ed1c77e` Part 3. `change-821919ce`'s own withdrawal condition, written on 2026-08-04 before any baseline existed, was met by the 2026-08-05 measurement: frames now use 46% of a 33.3 ms budget with zero overruns in 32 samples and the flicker resolved, where at authoring they used 88% of 16.67 ms with 32% overrunning. Assumption A1 was true when written and is not now; A3 was confirmed; A2 need not be isolated. `9ed1c77e` Part 3 falls under its own document's stated fallback. Both **deferred, not rejected** — the documents are complete and implementable should a heavier render path or slower target make them relevant. Statuses set: `issue-821919ce` deferred, `change-821919ce` deferred, `issue-9ed1c77e` resolved, `change-9ed1c77e` implemented for Parts 1 and 2. Recorded that this exposed a T02 schema gap — `change_info.status` had no `deferred` value though T03 has carried one since v1.0, so a sound change not taken forward could only be labelled `rejected`; `deferred` was added in T02-change.md v1.4 rather than mislabelling these two, with precedent in v1.3's addition of `closed`. Also corrected the §9.9.2 summary row, which still read "no T03 raised" after `c1d4b8e6` had raised and implemented it. |
| 16.0 | 2026-08-05 | Added §9.11.7 discharging §7.5.2, the last §8.4 observation. With `fps_limit` at 30 on the target: **no tearing, no flashing, no band thrash, and an acceptable needle** — display report §4.0 closes in full. 30 Hz baseline over 32 samples: **FPS exactly 30.0 in every sample** against six distinct values at 60 Hz, median frame 15.3 ms, **zero overruns**, 46% of budget used. Recorded that frame pacing has gone from irregular to exact and that all five §4.x flicker mechanisms have been addressed, while declining to claim any single change as *the* fix. **Recommends deferring `821919ce` and `9ed1c77e` Part 3 and cutting v0.4.0 without them**: `821919ce`'s own change document set withdrawal's condition as frames completing well inside budget, and that condition is now met, so both would be medium-risk optimisation of a renderer that meets its deadline and shows no visible fault. Recorded two defects the change exposed — `PerformanceMonitor` is constructed with a hardcoded `target_fps=60` so every dropped-frame figure at 30 Hz is wrong, and `RotatingFileHandler` silently overrides `mode='w'` to `'a'` when `maxBytes > 0`, verified against CPython source, so `debug.log` has never truncated and reached 31.6 MB across three sessions. |
| 15.0 | 2026-08-05 | Added §9.11.6 recording the 52-minute run that completed the §8.4 residual work. Frame-time baseline firm at 297 samples: median 14.7 ms, mean 16.0, p90 19.7, max 21.2 against a 16.67 ms budget, with 32% of frames overrunning at 60 Hz and **none of 297 overrunning at 30 Hz**. Render cost verified equivalent in simulation and Bluetooth modes, validating the large simulation sample. Consequence recorded: `9ed1c77e` recommendation 12 alone would eliminate every observed overrun for a one-line configuration change, so it should ship *ahead* of `821919ce` rather than after it. **Corrected two earlier over-claims about the OBD desynchronisation** (§9.10.4, §9.11.5): it recovers once polling settles into uniform `010C` commands — the "does not recover" claim was drawn from a 90-second session — and it does not corrupt the displayed reading, 874 responses spanning 0–4,208 RPM producing 4,193 frames with not one displayed value outside that range, the intermediate values being `4c038bed`'s EMA interpolating as designed. Severity reduced from data integrity to initialisation-phase robustness. §7.5.2's flicker characterisation remains the only outstanding observation. |
| 14.0 | 2026-08-05 | Added §9.11 discharging the §8.4 observation session from logs already pulled, five of its six items being answerable because the instrumentation each depended on has since shipped. §7.5.1 discharged — framebuffer is 32-bit at stride 1920, exactly as `engine.py` assumed, so display report §8.3 is not an active fault and page flip is confirmed operating. §7.5.3 discharged indicatively: correlating the four periodic samples against what was on screen gives RADIAL at 14.7–19.3 ms against a 16.67 ms budget and the static OPTIONS screen at 6.3 ms, with the caveat that three RADIAL samples from one 90-second session is a direction rather than a baseline. §7.5.6 substantively answered — platform detection selects `RASPBERRY_PI_ZERO_2W` correctly, though the raw revision string is not logged. **`821919ce`'s gate clears**: assumption A1 holds more strongly than it was framed, render cost being at or over the whole budget rather than merely material; A3 confirmed at 37.1 MB steady; A2 supported but not isolated. `9ed1c77e`'s two recommendations separate — recommendation 12 is now supported independently of any assumption, the application demonstrably not sustaining 60 Hz. Residual on-panel work reduced from six items to two: §7.5.2's flicker characterisation and a five-minute run for a firmer baseline (§9.11.4). Recorded that the OBD desynchronisation reproduces and is clearer than §9.10.4 stated — `0100` receives `ATSP0`'s acknowledgement and `010C` is polled three times unanswered — and that whether it corrupts the displayed reading is not established, simulation mode having masked the real-data window (§9.11.5). |
| 13.0 | 2026-08-05 | Added §9.10 recording the second on-target session, after `7f2a9c04` and `3e8b1d72` were implemented. Both verified: one ERROR in 362 KB and no `DIGITAL` line. Raised `c1d4b8e6` grouping three small faults on the `change-d32ccc49` pattern — the debug toggle still failing because `gtach/__init__.py:11` binds `main` to the function so `app.py` cannot reach the module's handlers, a fault that is self-concealing because both sites log at DEBUG and one of them is the DEBUG control (§9.10.1); `engine_profiles.yaml` absent from the wheel, confirmed against the built artefact, with zero current impact because the abarth profile's thresholds coincide with the dataclass defaults but two profiles unreachable and the `engine_profile` key inert (§9.10.2); and the second stale *"Long press to return"* footer in `_draw_update_view`, carried from the `3e8b1d72` report §6.2 at the operator's request (§9.10.3). Recorded a fourth finding not yet raised: the OBD response stream desynchronises permanently after a timeout — `0100` times out at 1.0 s during the ELM327 protocol search, the late response is not drained, and every subsequent read returns the previous command's answer, which is why initialisation fails against a paired and answering emulator (§9.10.4). |
| 12.0 | 2026-08-05 | Added §9.9 recording the on-target `gtach.local` session. Confirmed §9.8.5 item 1 from `logs/start.log` — five `handling error: DIGITAL` lines, no other errors in 3.5 MB — and established two facts the static review did not: `TouchHandler` is the handler that fires, being registered on a started touch interface, and the fault is swallowed by its own except-Exception handler, which is why it presents as an inert control (§9.9.1). Raised `7f2a9c04` (issue/change/prompt, severity high, ungated) to complete `change-378703da`'s enum removal across the two runtime-instantiated modules its four-file scope excluded. Recorded a new defect not yet raised as a T03: the debug toggle fires but `app.py:155` binds the `main` **function** rather than the module, so `_debug_handler` is never reached — `debug.log` is empty while `start.log` holds 57,560 DEBUG lines, and the options label reads *Debug: Off* while debug is on (§9.9.2). Recorded the operator's swipe-navigation proposal as a scope extension agreed by consensus and authored it as `3e8b1d72`, separate from `7f2a9c04` so a navigation problem stays attributable; scoping found that the touch subsystem already detects and dispatches both vertical swipes, and that two live long-press handlers exist which must change together (§9.9.3). Recorded the root cause as a file-scoped constraint on a package-wide interface change, with `prompt-378703da` carrying three mutually unsatisfiable requirements (§9.9.4). |
| 11.0 | 2026-08-04 | Recorded the implementation of six of the eight v0.4.0 triples in §9.8 — `b02ed4ea`, `378703da`, `5014040c`, `5012004e`, `394c3bbb` and `6481f8ce` — as eight commits on the unpushed branch `v0.4.0-display-triples`, with all six prompt T-Docs closed and all sixteen issue and change T-Docs left active per §8.2.1. Recorded that `821919ce` and `9ed1c77e` were **not** implemented: both stopped at their §7.5.3 gate, which is the outcome §8.1 predicted and §9.7.1 anticipated (§9.8.2). Discharged §7.5.5, reproduced under `6481f8ce` against the unchanged files and again after Stage 1, with the correction that the `AttributeError` is caught by the broad handler and the defect was therefore silent in production (§9.8.4). Recorded four findings requiring decision (§9.8.5): live `DisplayMode.DIGITAL` references surviving `378703da` in `display/touch.py` and `display/navigation_gestures.py`, both runtime-instantiated, which is the only finding that can fault the running application; the night palette toggle being unreachable because no `DOUBLE_TAP` gesture exists; the contrast criterion in `5014040c` and `5012004e` being arithmetically unsatisfiable alongside the fixed palette values; and `b02ed4ea` leaving *Clear settings* with no entry point, previously hypothetical under §9.7.3 and now live in source. Recorded three prompt deviations (§9.8.6), chiefly that the transport primitives could not be `@abstractmethod` without making `SimTransport` uninstantiable and breaking `simtcp` and `simbt`. Recorded three governance gaps left open (§9.8.7): no T06 result documents, §8.2's pytest suite still unwritten with `tests/` collecting zero items, and the branch unpushed. Updated §0.0, the §7.3, §7.4 and §7.5 tables, and §8.5's state column and implementation order. Full detail in `ai/workspace/report/v0.4.0-triple-implementation-session.md`. |

---

Copyright (c) 2026 William Watson. MIT License.
