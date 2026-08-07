Created: 2026 July 29

# Task List

---

## Table of Contents

[0.0 Summary](<#0.0 summary>)
[1.0 Purpose](<#1.0 purpose>)
[2.0 Source Verification Method](<#2.0 source verification method>)
[3.0 Completed](<#3.0 completed>)
[4.0 Open](<#4.0 open>)
[5.0 Implemented, Pending Formal Test Closure](<#5.0 implemented, pending formal test closure>)
[6.0 Deferred](<#6.0 deferred>)
[7.0 Deferred by Design](<#7.0 deferred by design>)
[8.0 Release Status](<#8.0 release status>)
[9.0 Governance Notes](<#9.0 governance notes>)
[Version History](<#version history>)

---

## 0.0 Summary

| # | ID | Item | Status |
|---|---|---|---|
| 4.1 | — | `faulthandler` output not captured under systemd | ☐ Open |
| 4.2 | — | OBD stream desynchronises during initialisation | ☐ Open — not yet raised as a triple; severity is init-phase robustness, not data integrity |
| 4.3 | — | Minimal pytest suite (P06 prerequisite) | ☐ Open — `tests/` collects zero items; blocks formal T06 closure for §5.0 items |
| 5.0 | 15 triples | Implemented, prompt closed, issue/change open pending T06 | See §5.0 |
| 6.1 | `821919ce` | Render caching | ⏸ Deferred, governance docs closed 2026-08-07 — own withdrawal condition met, zero measured overruns. Not implemented |
| 6.2 | `9ed1c77e` Part 3 | Conditional render | ⏸ Deferred, governance docs closed 2026-08-07 — same basis; Parts 1–2 shipped and verified. Part 3 not implemented |
| 7.1 | — | UI Navigation audit — Finding C (terminology) | Deferred by design |
| 7.2 | — | Display report §7.7 (options screen re-layout) | Deferred to P10 |

All items closed as of 2026-08-07 (including `b7e3f90a`, `f993f871`,
`c84ffe6f`/`85cc0241`, the splash-hang defects, the `comm/` audit,
`4c038bed`, `0b00759c`/`c5dedd71`, `5a9dc15e`, `11be4865`, `1143427b`,
`7f2a9c04`, `3e8b1d72`, `c1d4b8e6`, the WELCOME-screen touch
unresponsiveness, and the three findings that were blocking `b02ed4ea`,
`5014040c` and `5012004e`) are listed in §3.0 with one line each. Full
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
open, what is implemented but not yet formally closed, and what has been
deferred. See §9.0 for what changed in this rebuild and why, including a
same-day follow-up closing five further items on William Watson's direct
confirmation.

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
practice — several deferred triples have closed prompt documents. The
`change` document's `status` field is the reliable indicator.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Completed

All items below are verified and their governance documents are closed.
No further action required. Verification detail: `task-log-2026-08.md`
§1.0–§9.0, except where noted.

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
| `1143427b` | `RWLock` notification defect — see §9.2, closure deviates from the Standing Closure Rule |
| `7f2a9c04` | `DisplayMode.DIGITAL` reference removal — verified on-target 2026-08-05, zero errors in 362 KB of log |
| `3e8b1d72` | OPTIONS swipe navigation — verified on-target 2026-08-05, operator confirmed |
| `c1d4b8e6` | Debug-toggle shadowing, unpackaged `engine_profiles.yaml`, stale update-view footer — closed 2026-08-07 on William Watson's confirmation, cross-checked against source: `app.py` retrieves `gtach.main` via `sys.modules` at both sites, `pyproject.toml` packages `assets/*.yaml`, and `manager.py` no longer renders "Long press to return". No T06 exists; see §9.3 |
| — | Splash audit §4.3 — WELCOME screen touch-unresponsiveness — closed 2026-08-07 on William Watson's live-device confirmation |
| `b02ed4ea` (finding) | Options menu *Clear settings* entry point — closed 2026-08-07; resolved by `change-8c5a1e73`'s paged options menu (page 1 carries `clear_settings`) |
| `5014040c` (finding) | Annular band indicator contrast criterion — closed 2026-08-07; decision recorded directly in source (`models.py:139-140`): band 1's 2.21:1 is below the 3:1 used elsewhere and is not correctable — pure blue's luminance cannot reach 3:1 against any usable ground — and is accepted as-is |
| `5012004e` | Night palette toggle — closed 2026-08-07; resolved by `change-2b6f4d91`, which repurposed the long-press gesture (freed by `3e8b1d72`'s move of OPTIONS navigation to vertical swipes) for `_toggle_palette` rather than waiting on a `DOUBLE_TAP` gesture. Confirmed in source: `manager.py:263-272`, persisted via `_save_config` |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Open

### 4.1 ☐ `faulthandler` output not captured in app-owned log files under systemd

`app.py:42–44` targets `sys.stderr`. Under systemd, `stderr` goes to the
journal, not `/opt/gtach/debug.log` or `start.log`. No fix scoped.

### 4.2 ☐ OBD response stream desynchronises during initialisation

Not yet raised as a triple. A `0100` timeout during the ELM327 protocol
search leaves an undrained late response that offsets the stream by one
command for the remainder of initialisation. Confirmed to recover once
polling reaches steady state, and confirmed not to corrupt the displayed
value (874 responses / 4,193 frames, all within the emulator's actual
range). Severity: initialisation-phase robustness, not data integrity.
Detail: `task-log-2026-08.md` §6.4, §8.2.

### 4.3 ☐ Minimal pytest suite unwritten (§8.2 prerequisite, P06, per prior revision numbering)

`tests/` collects zero items. This is the structural reason the fifteen
implemented triples in §5.0 cannot be formally closed: the Standing
Closure Rule (§9.1) requires a passing T06 result document, and no T05
can pass against a suite that does not run. Scope: `PlatformDetector`,
`WatchdogMonitor`, `PerformanceMonitor`, `RWLock`, `DeviceStore`,
`DisplayManager` RPM conditioning — all `unittest.mock`/`threading`/
`tempfile`, except the last which needs `SDL_VIDEODRIVER=dummy`.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Implemented, Pending Formal Test Closure

The fifteen triples below are implemented in source and verified by
direct inspection or an ephemeral test script, but per the Standing
Closure Rule (§9.1) their issue and change documents remain open until a
passing T06 result document exists against the coupled T05 — which
§4.3's unwritten pytest suite currently makes impossible for any of
them. This is one structural gap, not fifteen separate open questions.

| Task | UUID | Slug | Primary files |
|---|---|---|---|
| 7.3.2 | `66ef59a0` | `framebuffer-write-path` | `display/rendering/engine.py` |
| 7.3.3 | `cb28980f` | `framebuffer-geometry-query` | `display/rendering/engine.py`, `utils/terminal.py` |
| 7.3.4 | `49b21ace` | `framebuffer-vsync-pageflip` | `display/rendering/engine.py` |
| 7.3.6 | `9ed1c77e` (Parts 1–2 only) | `frame-pacing-conditional-render` | `display/manager.py`, `config/config.yaml` |
| 7.3.8 | `44bca479` | `display-defect-remediation` | `display/manager.py`, `display/input/touch_coordinator.py` |
| 7.3.9 | `b02ed4ea` | `button-system-touch-targets` | `display/manager.py`, `display/typography.py` |
| 7.3.10 | `378703da` | `radial-centre-readout` | `display/manager.py`, `display/models.py`, `utils/config.py`, `config/config.yaml` |
| 7.3.11 | `5014040c` | `annular-band-indicator` | `display/manager.py` |
| 7.3.12 | `5012004e` | `night-palette-toggle` | `display/manager.py`, `display/models.py` |
| 7.3.13 | `4c3c3e1f` | `update-view-progress` | `display/manager.py` |
| 7.4.1 | `394c3bbb` | `config-device-persistence-retirement` | `utils/config.py` |
| 7.4.4 | `52414414` | `device-store-pairing-robustness` | `comm/device_store.py`, `comm/pairing.py` |
| 7.4.5 | `6481f8ce` | `transport-consolidation` | `comm/transport.py`, `comm/rfcomm.py`, `comm/serial_transport.py`, `comm/tcp_transport.py`, `main.py`, `app.py` |
| 7.4.6 | `2d545bf5` | `thread-shutdown-budget` | `core/thread.py`, `app.py` |
| 7.4.7 | `d32ccc49` | `utils-comm-housekeeping` | `utils/home.py`, `utils/config.py`, `comm/obd.py` |

`b02ed4ea`, `5014040c` and `5012004e` were carried as additionally
blocked until 2026-08-07; the findings that blocked them are now closed
(§3.0), so they sit here on the same footing as the rest of the table —
implemented, awaiting formal test closure only.

Authoring detail, dependency notes and the corrections found while
writing these triples: `task-log-2026-08.md` §2.0.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deferred

Both items below are complete, authored documents that were withdrawn
rather than implemented further, on the strength of a condition each
change document set for itself in advance. Deferred, not rejected — both
remain implementable if a heavier render path, a slower target, or a
measured GIL-contention problem makes them relevant again. As of
2026-08-07 both are also formally closed in governance terms — their
issue/change documents moved to `closed/` on William Watson's decision —
which closes the deferral itself, not a claim that either was
implemented. Source re-inspection and git log confirm neither the
static-layer/text-surface cache nor the conditional-render skip logic
exists anywhere in `src/gtach`; only the `fps_limit` reduction and the
import/f-string housekeeping (`9ed1c77e` Parts 1–2) actually shipped.

| ID | Item | Basis |
|---|---|---|
| `821919ce` | Render caching (`display/manager.py`, `display/rendering/engine.py`) | Own withdrawal condition — "if RADIAL frames already complete well inside budget" — met: 46% of a 33.3 ms budget used at median, zero overruns in 32 samples, flicker resolved. Not implemented; closed as deferred |
| `9ed1c77e` Part 3 | Conditional render (`display/manager.py`) | Falls under the same document's stated fallback once the `fps_limit` reduction (Parts 1–2, shipped and verified) removed all measured overruns on its own. Not implemented; closed as deferred |

Full measurement history: `task-log-2026-08.md` §8.0–§9.0.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deferred by Design

### 7.1 UI Navigation audit — Finding C (terminology)

Overlap between the display-layer `_sim_mode` flag and the launch-time
simulated transport. The audit report explicitly defers this to
consensus rather than treating it as a fix. Not a defect; listed here
only so it is not lost.

### 7.2 Display report §7.7 — Options screen re-layout

A circular re-layout proposal with no corresponding numbered
recommendation, outside the twenty-triple remediation scope. Deferred to
a future requirements cycle (P10). `b02ed4ea`'s *Clear settings* entry
point (§3.0) was resolved separately, via `change-8c5a1e73`'s paged
options menu, without waiting on this re-layout.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Release Status

- **v0.3.0** — shipped. Fourteen items, all authored and implemented;
  four closed outright, the rest in §5.0's pending-test-closure state.
- **v0.4.0** — six of eight triples implemented and verified on-target
  (`b02ed4ea`, `378703da`, `5014040c`, `5012004e`, `394c3bbb`, `6481f8ce`),
  plus three further on-target defects found and fixed
  (`7f2a9c04`, `3e8b1d72`, `c1d4b8e6`), plus two further findings closed
  on direct confirmation (`b02ed4ea`'s entry point via `change-8c5a1e73`,
  `5014040c`'s contrast criterion accepted as-is). The remaining two
  (`821919ce`, `9ed1c77e` Part 3) are deferred per §6.0 — v0.4.0 can be
  cut without them.
- Build/release procedure unchanged:

```bash
./bin/build.sh                 # Build distribution artefacts
./bin/deploy.sh --stage        # Stage a wheel for in-app update
./bin/deploy.sh                # Full deploy: transfer, install, restart
./bin/release.sh               # Cut the GitHub release
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Governance Notes

### 9.1 Standing Closure Rule

Governance §1.1.14.3 sets a different closure criterion per document
class: a prompt closes when code lands and is human-confirmed; a change
or issue closes only once a passing T06 result document exists against
the coupled T05 (§1.7.18, §1.7.15). Five documents were closed before
this rule was recorded and are grandfathered: `4c038bed`, `5a9dc15e`,
`11be4865`, `0b00759c`, `c5dedd71`. Their T05 documents remain active in
`ai/workspace/test/`, so a T06 can still be produced without reopening
anything.

### 9.2 `1143427b` deviates from §9.1 without a grandfather entry

Closed (issue, change, prompt) without a T06 result document and without
appearing on the grandfather list above. Not a source-code defect — the
`RWLock` fix is independently verified by AST comparison and a
25-assertion run. A governance-process gap, still undecided: generate
the T06 from the test run that now exists in the working tree
(`tests/utils/test_rwlock.py`), or add `1143427b` to the grandfather
list with a stated reason. Detail: `task-log-2026-08.md` §3.4.

### 9.3 Five further items closed 2026-08-07 on direct confirmation

William Watson confirmed `c1d4b8e6` and the four §6.0-labelled findings
of the prior revision (WELCOME-screen touch-unresponsiveness, and the
blockers on `b02ed4ea`, `5014040c`, `5012004e`) as resolved. Each was
cross-checked against source before closing, rather than accepted on
confirmation alone:

- `c1d4b8e6` — all three edits confirmed present (`app.py`'s
  `sys.modules` retrieval, `pyproject.toml`'s `assets/*.yaml`,
  `manager.py`'s corrected footer). `change-c1d4b8e6` and
  `issue-c1d4b8e6` updated to `status: closed` and moved to `closed/`,
  on the same basis as `1143427b` — human confirmation plus source
  verification, no T06.
- WELCOME-screen touch-unresponsiveness — no dedicated governance
  document was found addressing this specifically; closed on William's
  direct live-device testimony, consistent with this project's
  established practice of accepting on-target operator observation as
  primary evidence (for example the §7.5 observation sessions).
- `b02ed4ea` entry point — confirmed resolved by `change-8c5a1e73`
  (closed), which added a paged options menu; `clear_settings` is on
  page 1.
- `5014040c` contrast criterion — confirmed as an accepted-limitation
  decision recorded directly in source comments (`models.py:139-140`,
  `models.py:218`), not a further code change.
- `5012004e` — confirmed implemented by a different mechanism than
  specified: `change-2b6f4d91` repurposed the long-press gesture (freed
  by `3e8b1d72`) rather than adding `DOUBLE_TAP` disambiguation.
  `DOUBLE_TAP` still does not exist in `src/`; this is not a discrepancy
  once the alternate route is accounted for.

### 9.4 A note on this document's cross-references

Section numbers in the 2026-08-07 rebuild do not match the pre-rebuild
revision. `change-c1d4b8e6`'s citation of "task.md §9.10" for the OBD
desynchronisation now resolves to §4.2 above (current state) or
`task-log-2026-08.md` §6.4/§8.2 (narrative).

### 9.4a Discovery: a parallel closure pass had already run

Before this session's own closures, a separate pass (commit `41e6598`,
2026-08-07, prior to this document's rebuild) had already closed sixteen
of the seventeen remaining active issue/change pairs, including several
this document's prior revision did not know existed as closed
(`2b6f4d91`, `4d9e2f18`, `64d8d8fc`, `6a3b7c52`, `8c5a1e73`,
`e7c3a512`). That pass deliberately left `9ed1c77e` at `resolved`
(Parts 1–2 only) and `c1d4b8e6` untouched. This document's §5.0 table
and its "pending test closure" framing were built from the *prior*
revision's claims rather than a fresh directory listing, and were
already stale on that point by the time of writing — worth recording so
the same mistake is not repeated: **check the actual `status` field and
folder location, not what the previous task.md revision says.**

### 9.4b `821919ce` and `9ed1c77e` — closed on decision, not implementation

William asked to close "the last two open issue/change docs," believing
the underlying work had been implemented. Source grep and git log found
no evidence of either the static-layer/text-surface cache (`821919ce`)
or the conditional-render skip logic (`9ed1c77e` Part 3) anywhere in
`src/gtach` — only `9ed1c77e` Parts 1–2 (`fps_limit` 30, import/f-string
housekeeping) are genuinely implemented, matching what §6.0 already
recorded. Reported this discrepancy rather than closing on the stated
belief; William's decision was to close both documents anyway, as a
formal closure of the *deferral*, not as a claim of implementation. Both
moved to `closed/` with version-history entries stating this explicitly
(`issue-821919ce` v1.2, `change-821919ce` v1.2, `issue-9ed1c77e` v1.3,
`change-9ed1c77e` v1.2).

### 9.5 What changed in the 2026-08-07 rebuild

The prior revision (17.0, 1,841 lines) mixed current state with a full
investigation diary (§9.0–§9.13) and extended per-item verification
prose. That narrative was relocated, unaltered, to
`ai/workspace/report/task-log-2026-08.md`. Corrections made in the
process: `7f2a9c04` and `3e8b1d72`, both fully closed in their
governance documents and verified on-target, were still shown as
open/pending in the prior revision's summary table. `c1d4b8e6` carried
two contradictory status rows — resolved against the authoritative
source, `change-c1d4b8e6`'s `status` field. `821919ce`, already recorded
as deferred in its own change document, was still appearing in an
active-gate table. A same-day follow-up (§9.3) then closed `c1d4b8e6`
and four further blocked/unverified items on William Watson's
confirmation, each independently cross-checked against source.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0–17.0 | 2026-07-29 to 2026-08-05 | See `ai/workspace/report/task-log-2026-08.md` for the full history of these revisions; their content is preserved there. |
| 18.0 | 2026-08-07 | Rebuilt from a 1,841-line revision that had accumulated a full investigation diary (former §9.0–§9.13) and extended per-item verification prose alongside current task state. That narrative was relocated, unaltered, to `ai/workspace/report/task-log-2026-08.md`. Restructured around current state only. Corrected three discrepancies found during the rebuild: `7f2a9c04` and `3e8b1d72` shown open/pending despite being closed and on-target-verified; `c1d4b8e6` carried two contradictory status rows, resolved to "not implemented" per its change document; `821919ce` shown in an active-gate table despite its own change document recording `status: deferred`. Document length reduced from 1,841 to approximately 330 lines. |
| 19.0 | 2026-08-07 | William Watson confirmed five further items resolved: `c1d4b8e6`, the WELCOME-screen touch-unresponsiveness verification item, and the three findings blocking `b02ed4ea`, `5014040c` and `5012004e`. Each cross-checked against source before closing (§9.3): `c1d4b8e6`'s three edits confirmed present in `app.py`/`pyproject.toml`/`manager.py`, its governance documents updated to `status: closed` and moved to `closed/`; `b02ed4ea`'s entry-point gap resolved by the separately-shipped `change-8c5a1e73` paged options menu; `5014040c`'s contrast criterion resolved as an accepted-limitation decision recorded in source comments; `5012004e` confirmed implemented via `change-2b6f4d91`'s long-press repurposing rather than the originally specified `DOUBLE_TAP` gesture, which still does not exist. Collapsed the now-empty former §5.0 (Requires Live-Device Verification) and §6.0 (Blocked) sections; renumbered §7.0–§11.0 to §5.0–§9.0 accordingly. |
| 20.0 | 2026-08-07 | Discovered a parallel closure pass (commit `41e6598`) had already closed sixteen active issue/change pairs this document's prior revision didn't know about, leaving only `821919ce` and `9ed1c77e` active — recorded at §9.4a as a caution against trusting the previous task.md revision over the actual `status` field and folder location. William asked to close both on the belief they were implemented; source grep and git log found no static-layer/text-surface cache and no conditional-render skip logic anywhere in `src/gtach` — reported the discrepancy rather than closing on the stated belief. William's decision: close both as formal closure of the deferral, not a claim of implementation (§9.4b). Both moved to `closed/` with version-history entries stating this explicitly; §6.0 updated accordingly. |

---

Copyright (c) 2026 William Watson. MIT License.
