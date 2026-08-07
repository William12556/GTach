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
[6.0 Blocked — Implemented but Not Fully Operative](<#6.0 blocked — implemented but not fully operative>)
[7.0 Implemented, Pending Formal Test Closure](<#7.0 implemented, pending formal test closure>)
[8.0 Deferred](<#8.0 deferred>)
[9.0 Deferred by Design](<#9.0 deferred by design>)
[10.0 Release Status](<#10.0 release status>)
[11.0 Governance Notes](<#11.0 governance notes>)
[Version History](<#version history>)

---

## 0.0 Summary

| # | ID | Item | Status |
|---|---|---|---|
| 4.1 | — | `faulthandler` output not captured under systemd | ☐ Open |
| 4.2 | `c1d4b8e6` | Debug toggle unreachable; `engine_profiles.yaml` unpackaged; stale footer | ☐ Open — authored 2026-08-05, not implemented |
| 4.3 | — | OBD stream desynchronises during initialisation | ☐ Open — not yet raised as a triple; severity is init-phase robustness, not data integrity |
| 4.4 | — | Minimal pytest suite (P06 prerequisite) | ☐ Open — `tests/` collects zero items; blocks formal T06 closure for §7.0 items |
| 5.1 | — | Splash audit §4.3 — WELCOME screen touch-unresponsiveness | ☐ Unverified — needs live device |
| 6.1 | `b02ed4ea` | Options menu — *Clear settings* has no entry point | ☐ Blocked — needs §7.7 layout decision (P10) |
| 6.2 | `5014040c` | Annular band indicator — contrast criterion unsatisfiable as specified | ☐ Blocked — needs palette decision |
| 6.3 | `5012004e` | Night palette toggle — unreachable, no `DOUBLE_TAP` gesture exists | ☐ Blocked — needs gesture-subsystem work |
| 7.0 | 15 triples | Implemented, prompt closed, issue/change open pending T06 | See §7.0 |
| 8.1 | `821919ce` | Render caching | ⏸ Deferred — own withdrawal condition met, zero measured overruns |
| 8.2 | `9ed1c77e` Part 3 | Conditional render | ⏸ Deferred — same basis; Parts 1–2 shipped |
| 9.1 | — | UI Navigation audit — Finding C (terminology) | Deferred by design |
| 9.2 | — | Display report §7.7 (options screen re-layout) | Deferred to P10 |

All items closed prior to 2026-08-07 (including `b7e3f90a`, `f993f871`,
`c84ffe6f`/`85cc0241`, the splash-hang defects, the `comm/` audit,
`4c038bed`, `0b00759c`/`c5dedd71`, `5a9dc15e`, `11be4865`, `1143427b`,
`7f2a9c04`, `3e8b1d72`) are listed in §3.0 with one line each. Full
verification detail and the complete investigation narrative behind
every entry on this page are in
`ai/workspace/report/task-log-2026-08.md`.

[Return to Table of Contents](<#table of contents>)

---

## 1.0 Purpose

This document lists unfinished work. It was rebuilt on 2026-08-07 from a
1,841-line revision that had accumulated a full investigation diary
alongside the task state. That narrative — the eight cross-check and
on-target sessions run between 2026-08-04 and 2026-08-05, and the
extended verification detail behind each completed item — has been
relocated to `ai/workspace/report/task-log-2026-08.md` without
alteration. This page now carries only current state: what remains
open, what is blocked pending a decision, what is implemented but not
yet formally closed, and what has been deferred. See §11.0 for what
changed in this rebuild and why.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source Verification Method

Status below is drawn from three sources, cross-checked against each
other: the `status` field of each governance document in
`ai/workspace/{issues,change,prompt}/` (and its `closed/` subfolder);
targeted `Grep` of `src/gtach` for the symbols each governance document
names; and the git/GitHub commit history. `pyproject.toml` currently
reports `0.3.3`. Note that a prompt document's presence in `prompt/closed/`
is **not** by itself evidence of implementation in this project's
practice — several deferred and not-yet-implemented triples (for example
`821919ce`, `c1d4b8e6`) have closed prompt documents. The `change`
document's `status` field is the reliable indicator.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Completed

All items below are verified and their governance documents are closed.
No further action required. Verification detail: `task-log-2026-08.md` §1.0–§6.0.

| ID | Item |
|---|---|
| `b7e3f90a` | Dead code cleanup |
| `f993f871` | OPTIONS update check/install |
| `c84ffe6f` / `85cc0241` | UI Navigation Logic audit — Findings A and B |
| — | Splash Screen Debug Session audit — Defects 1–4 |
| `b4e8c012` / `2f612d17` / `a4c8e2f1` | `comm/` transport layer audit |
| `4c038bed` | RPM signal conditioning |
| `0b00759c` / `c5dedd71` | Performance instrumentation |
| `5a9dc15e` | Watchdog lock discipline |
| `11be4865` | Platform detection consolidation |
| `1143427b` | `RWLock` notification defect — see §11.2, closure deviates from the Standing Closure Rule |
| `7f2a9c04` | `DisplayMode.DIGITAL` reference removal — verified on-target 2026-08-05, zero errors in 362 KB of log |
| `3e8b1d72` | OPTIONS swipe navigation — verified on-target 2026-08-05, operator confirmed |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Open

### 4.1 ☐ `faulthandler` output not captured in app-owned log files under systemd

`app.py:42–44` targets `sys.stderr`. Under systemd, `stderr` goes to the
journal, not `/opt/gtach/debug.log` or `start.log`. No fix scoped.

### 4.2 ☐ `c1d4b8e6` — Debug toggle unreachable; unpackaged asset; stale footer

Three independent faults, authored as one triple 2026-08-05:
`gtach/__init__.py`'s re-export shadows the `main` module so `app.py`
cannot reach its debug/startup-log handlers; `assets/engine_profiles.yaml`
is absent from the built wheel (`pyproject.toml` package-data names only
fonts); `_draw_update_view`'s footer still instructs a long press that no
longer acts. `change-c1d4b8e6` status is `proposed` — **not
implemented**. Detail: `task-log-2026-08.md` §6.1–§6.3.

### 4.3 ☐ OBD response stream desynchronises during initialisation

Not yet raised as a triple. A `0100` timeout during the ELM327 protocol
search leaves an undrained late response that offsets the stream by one
command for the remainder of initialisation. Confirmed to recover once
polling reaches steady state, and confirmed not to corrupt the displayed
value (874 responses / 4,193 frames, all within the emulator's actual
range). Severity: initialisation-phase robustness, not data integrity.
Detail: `task-log-2026-08.md` §6.4, §8.2.

### 4.4 ☐ Minimal pytest suite unwritten (§8.2 prerequisite, P06)

`tests/` collects zero items. This is the structural reason fifteen
implemented triples in §7.0 cannot be formally closed: the Standing
Closure Rule (§11.1) requires a passing T06 result document, and no T05
can pass against a suite that does not run. Scope: `PlatformDetector`,
`WatchdogMonitor`, `PerformanceMonitor`, `RWLock`, `DeviceStore`,
`DisplayManager` RPM conditioning — all `unittest.mock`/`threading`/
`tempfile`, except the last which needs `SDL_VIDEODRIVER=dummy`.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Requires Live-Device Verification

### 5.1 ☐ Splash audit §4.3 — WELCOME screen touch-unresponsiveness

The splash audit's touch-routing investigation
(`HyperPixelTouchInterface` → `TouchHandler` → `SetupDisplayManager`) was
left unresolved pending live testing. Static review cannot confirm
current behaviour, and no on-target session to date has specifically
exercised the WELCOME screen.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Blocked — Implemented but Not Fully Operative

Each item below shipped and is technically present in source, but cannot
be exercised as specified until a decision or a further change is made.

### 6.1 `b02ed4ea` — Options menu has no entry point to *Clear settings*

The three-control touch-target budget on the options screen is full; the
confirmation view recommendation 24 requires is unreachable. Resolution
is display report §7.7's circular re-layout, deferred to a future
requirements cycle (P10) — see §9.2.

### 6.2 `5014040c` — Annular band indicator's contrast criterion is unsatisfiable

`5014040c` and `5012004e` each fix palette values and require every band
colour to reach 3:1 contrast against the face ground; both cannot hold
for blue given the fixed palette (measured: day blue 2.21:1, night blue
1.55:1). Implemented as specified because both prompts forbid changing
the colours. Needs a decision: lighter blue, lighter ground, or drop the
3:1 bar for band fills.

### 6.3 `5012004e` — Night palette toggle cannot fire

Specified as a double-tap; `GestureType` has no `DOUBLE_TAP` member.
Delivered with registration conditional on the gesture's existence, so it
activates automatically once the touch subsystem provides double-tap
disambiguation. No work item currently scoped to add it.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Implemented, Pending Formal Test Closure

The fifteen triples below are implemented in source and verified by
direct inspection or an ephemeral test script, but per the Standing
Closure Rule (§11.1) their issue and change documents remain open until
a passing T06 result document exists against the coupled T05 — which
§4.4's unwritten pytest suite currently makes impossible for any of
them. This is one structural gap, not fifteen separate open questions.

| Task | UUID | Slug | Primary files |
|---|---|---|---|
| 7.3.2 | `66ef59a0` | `framebuffer-write-path` | `display/rendering/engine.py` |
| 7.3.3 | `cb28980f` | `framebuffer-geometry-query` | `display/rendering/engine.py`, `utils/terminal.py` |
| 7.3.4 | `49b21ace` | `framebuffer-vsync-pageflip` | `display/rendering/engine.py` |
| 7.3.6 | `9ed1c77e` (Parts 1–2 only) | `frame-pacing-conditional-render` | `display/manager.py`, `config/config.yaml` |
| 7.3.8 | `44bca479` | `display-defect-remediation` | `display/manager.py`, `display/input/touch_coordinator.py` |
| 7.3.9 | `b02ed4ea` | `button-system-touch-targets` | `display/manager.py`, `display/typography.py` — also see §6.1 |
| 7.3.10 | `378703da` | `radial-centre-readout` | `display/manager.py`, `display/models.py`, `utils/config.py`, `config/config.yaml` |
| 7.3.11 | `5014040c` | `annular-band-indicator` | `display/manager.py` — also see §6.2 |
| 7.3.12 | `5012004e` | `night-palette-toggle` | `display/manager.py`, `display/models.py` — also see §6.3 |
| 7.3.13 | `4c3c3e1f` | `update-view-progress` | `display/manager.py` |
| 7.4.1 | `394c3bbb` | `config-device-persistence-retirement` | `utils/config.py` |
| 7.4.4 | `52414414` | `device-store-pairing-robustness` | `comm/device_store.py`, `comm/pairing.py` |
| 7.4.5 | `6481f8ce` | `transport-consolidation` | `comm/transport.py`, `comm/rfcomm.py`, `comm/serial_transport.py`, `comm/tcp_transport.py`, `main.py`, `app.py` |
| 7.4.6 | `2d545bf5` | `thread-shutdown-budget` | `core/thread.py`, `app.py` |
| 7.4.7 | `d32ccc49` | `utils-comm-housekeeping` | `utils/home.py`, `utils/config.py`, `comm/obd.py` |

Authoring detail, dependency notes and the corrections found while
writing these triples: `task-log-2026-08.md` §2.0.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Deferred

Both items below are complete, authored documents that were withdrawn
rather than implemented further, on the strength of a condition each
change document set for itself in advance. Deferred, not rejected — both
remain implementable if a heavier render path, a slower target, or a
measured GIL-contention problem makes them relevant again.

| ID | Item | Basis |
|---|---|---|
| `821919ce` | Render caching (`display/manager.py`, `display/rendering/engine.py`) | Own withdrawal condition — "if RADIAL frames already complete well inside budget" — met: 46% of a 33.3 ms budget used at median, zero overruns in 32 samples, flicker resolved |
| `9ed1c77e` Part 3 | Conditional render (`display/manager.py`) | Falls under the same document's stated fallback once the `fps_limit` reduction (Parts 1–2, shipped) removed all measured overruns on its own |

Full measurement history: `task-log-2026-08.md` §8.0–§9.0.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Deferred by Design

### 9.1 UI Navigation audit — Finding C (terminology)

Overlap between the display-layer `_sim_mode` flag and the launch-time
simulated transport. The audit report explicitly defers this to
consensus rather than treating it as a fix. Not a defect; listed here
only so it is not lost.

### 9.2 Display report §7.7 — Options screen re-layout

A circular re-layout proposal with no corresponding numbered
recommendation, outside the twenty-triple remediation scope. Deferred to
a future requirements cycle (P10). This is also where §6.1's *Clear
settings* entry point and §6.3's night-toggle placement are expected to
be resolved.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Release Status

- **v0.3.0** — shipped. Fourteen items, all authored and implemented;
  four closed outright, the rest in §7.0's pending-test-closure state.
- **v0.4.0** — six of eight triples implemented and verified on-target
  (`b02ed4ea`, `378703da`, `5014040c`, `5012004e`, `394c3bbb`, `6481f8ce`),
  plus two on-target defects found and fixed (`7f2a9c04`, `3e8b1d72`).
  The remaining two (`821919ce`, `9ed1c77e` Part 3) are deferred per
  §8.0 — v0.4.0 can be cut without them.
- Build/release procedure unchanged:

```bash
./bin/build.sh                 # Build distribution artefacts
./bin/deploy.sh --stage        # Stage a wheel for in-app update
./bin/deploy.sh                # Full deploy: transfer, install, restart
./bin/release.sh               # Cut the GitHub release
```

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Governance Notes

### 11.1 Standing Closure Rule

Governance §1.1.14.3 sets a different closure criterion per document
class: a prompt closes when code lands and is human-confirmed; a change
or issue closes only once a passing T06 result document exists against
the coupled T05 (§1.7.18, §1.7.15). Five documents were closed before
this rule was recorded and are grandfathered: `4c038bed`, `5a9dc15e`,
`11be4865`, `0b00759c`, `c5dedd71`. Their T05 documents remain active in
`ai/workspace/test/`, so a T06 can still be produced without reopening
anything.

### 11.2 `1143427b` deviates from §11.1 without a grandfather entry

Closed (issue, change, prompt) without a T06 result document and without
appearing on the grandfather list above. Not a source-code defect — the
`RWLock` fix is independently verified by AST comparison and a
25-assertion run. A governance-process gap. Undecided: generate the T06
from the test run that now exists in the working tree
(`tests/utils/test_rwlock.py`), or add `1143427b` to the grandfather
list with a stated reason. Detail: `task-log-2026-08.md` §3.4.

### 11.3 A note on this document's cross-references

Section numbers in this revision do not match the pre-2026-08-07
revision. `change-c1d4b8e6`'s citation of "task.md §9.10" for the OBD
desynchronisation now resolves to §4.3 above (current state) or
`task-log-2026-08.md` §6.4/§8.2 (narrative). No other governance document
was found to cite a `task.md` section number by search of
`ai/workspace/`.

### 11.4 What changed in the 2026-08-07 rebuild

The prior revision (17.0, 1,841 lines) mixed current state with a full
investigation diary (§9.0–§9.13) and extended per-item verification
prose. That narrative was relocated, unaltered, to
`ai/workspace/report/task-log-2026-08.md`. Three corrections were made
in the process: `7f2a9c04` and `3e8b1d72`, both fully closed in their
governance documents and verified on-target, were still shown as
open/pending in the prior revision's summary table — corrected here.
`c1d4b8e6` carried two contradictory status rows in the prior revision's
§0.0 (one "implemented", one "not implemented") — resolved against the
authoritative source, `change-c1d4b8e6`'s `status: proposed` field: not
implemented. `821919ce`, already recorded as deferred in its own change
document, was still appearing in an active-gate table — moved to §8.0.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0–17.0 | 2026-07-29 to 2026-08-05 | See `ai/workspace/report/task-log-2026-08.md` for the full history of these revisions; their content is preserved there. |
| 18.0 | 2026-08-07 | Rebuilt from a 1,841-line revision that had accumulated a full investigation diary (former §9.0–§9.13) and extended per-item verification prose alongside current task state. That narrative was relocated, unaltered, to `ai/workspace/report/task-log-2026-08.md`. Restructured around current state only: §3.0 Completed (one line per item), §4.0 Open, §5.0 Requires Live-Device Verification, §6.0 Blocked, §7.0 Implemented Pending Formal Test Closure (fifteen triples collapsed under one structural explanation rather than fifteen repeated caveats), §8.0 Deferred, §9.0 Deferred by Design, §10.0 Release Status, §11.0 Governance Notes. Corrected three discrepancies found during the rebuild: `7f2a9c04` and `3e8b1d72` were shown open/pending despite being closed and on-target-verified; `c1d4b8e6` carried two contradictory status rows, resolved to "not implemented" per its change document's `status: proposed` field; `821919ce` was shown in an active-gate table despite its own change document already recording `status: deferred`. Document length reduced from 1,841 to approximately 330 lines. |

---

Copyright (c) 2026 William Watson. MIT License.
