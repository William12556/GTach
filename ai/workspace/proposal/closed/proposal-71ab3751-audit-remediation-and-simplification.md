# Proposal — Audit Remediation and Simplification (71ab3751)

Created: 2026 November 11

> **Status: Closed — completed (2026-11-12).** All five runs and the follow-up set 146491ba were implemented, verified on the device and closed; version 0.5.0. The in-car test is deferred (`ai/task.md`).

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Scope and Assumptions](#20-scope-and-assumptions)
- [3.0 Approach](#30-approach)
- [4.0 Work Packages](#40-work-packages)
- [5.0 Items Outside the Five Runs](#50-items-outside-the-five-runs)
- [6.0 Decisions Required](#60-decisions-required)
- [7.0 Sequence and Gates](#70-sequence-and-gates)
- [8.0 Alternatives Considered](#80-alternatives-considered)
- [9.0 Risks](#90-risks)
- [10.0 Coverage Check](#100-coverage-check)
- [References](#references)
- [Version History](#version-history)

---

## 1.0 Summary

- **Proposal:** resolve the 43 findings of `audit-71ab3751`, the four observed weaknesses and the applicable rows of `ai/task.md` in **five issue/change/prompt sets**, executed as five consecutive Claude Code runs.
- **Grouping rule:** one set per group of files that must be read together. No file is edited by two sets, so the runs do not conflict and each run's reading load is bounded.
- **Fast route:** author all five sets in one planner session, with prompts that cite symbols instead of line numbers, and approve them together. The runs then follow one another with only a test gate between them.
- **Order:** remove dead code first. This shrinks the files the later runs must read and removes several findings outright.
- **Not bundled:** two `bin/` fixes (workflow-exempt), the design review (planner work), and four task rows that need evidence or a vehicle before they can be specified.
- **Decisions:** all eight decisions in [6.0](#60-decisions-required) were accepted as recommended on 2026-11-11, and the five-run structure was confirmed.
- **Execution:** Claude Code cloud sessions with Opus 5.5 at medium effort, invoked directly; no engine loop ([4.8](#48-execution-profile)).

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Scope and Assumptions

### 2.1 Inputs

- `audit-71ab3751` v1.1: findings A01 to X01, observations O1 to O5.
- Weaknesses W1 to W4 from `report-71ab3751` §5.0.
- `ai/task.md` as read on 2026-11-11 (14 rows).

### 2.2 Assumptions

- **Context budget.** Version 1.0 assumed a 200,000-token window. The selected model, Claude Opus 5.5, has a 1,000,000-token window (Anthropic, 2026b). Source is estimated at 11 tokens per line, so the largest run reads about 5% of the window. Context length is therefore not a constraint. The five-run structure is kept for review size and fault bisection, not for context ([8.0](#80-alternatives-considered)).
- **Bundling is permitted.** One issue and one change may cover several findings, as in `4005360c` (low-severity defects) and `d140121d` (remaining medium defects). Issue-to-change coupling stays one to one.
- **Line counts** are from the audited commit `94ce959b`. Test file sizes were not measured.
- **Target version.** One version increment at the end (suggested 0.5.0) instead of one per run.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Approach

1. **Subtract first.** Run 1 deletes unused code and nothing else. A purely subtractive change is simple to review: the tests, mypy and a caller search either still pass or they do not.
2. **Partition by file.** Each remaining run owns a disjoint set of files. A finding that spans two partitions is split, and the interface between them is fixed in the change documents before any run starts.
3. **Contract first.** The cross-run interfaces are defined up front, so that all prompts can be written and approved in one sitting. Each is backward compatible, so a run does not break before its counterpart lands:
   - `BluetoothPairing.discover_elm327_devices` keeps its signature (the existing `show_all_devices` parameter). When no ELM327-like device was found, it returns the named devices of the same scan, all classified `UNKNOWN`; `cancel_discovery()` and `cancel_pairing()` are effective (run 2 provides, run 4 uses).
   - `OBDProtocol.stop(timeout: float = 5.0)` and a non-joining registered stop function (run 2 provides; run 3 corrects the comment that relies on it).
   - `gtach.comm.device_store.set_device_store_path(path)` (run 2 provides, run 3 calls it for `simbt` sessions; decision D5).
   - `DeviceStore.save_device` / `remove_device` return whether the change reached disk (run 2 provides, runs 4 and 5 use).
   - `SetupDisplayManager.adapter_reset_in_session` (run 4 provides, run 3 reads it with a default of `False`; finding B02).
4. **Symbol-based prompts.** Prompts name functions and classes, not line numbers, so an earlier run does not invalidate a later prompt.
5. **Comment rule.** Each run reduces history comments in the files it owns to the current behaviour plus the issue reference. One line is added to `CLAUDE.md` to keep it that way. This addresses W3 without a separate run.
6. **Tests with the code.** Each fix carries its regression test. The three test findings (F01 to F03) go with the run that owns the code under test.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Work Packages

Each package is one issue, one change and one prompt sharing a new 8-hex UUID, and one Claude Code run (`target_profile: claude_code`).

### 4.1 Overview

| Run | Title | Files owned | Lines to read | Est. tokens | Findings and task rows |
|---|---|---|---|---|---|
| 1 | Dead code removal | Deletions across `display/`, `utils/`; no behaviour change | about 4,000 | 44,000 | E01, W1, part of the mypy candidates |
| 2 | Communication layer | `comm/*` | about 3,100 | 34,000 | A01–A07, A09–A12, F03, X01 (comm part), B06 (obd part) |
| 3 | Application lifecycle, logging, utils | `app.py`, `main.py`, `core/*`, `utils/*`, `pyproject.toml` | about 2,700 | 30,000 | B01–B04, B06, B07, E02–E06, F01, O1, five task rows |
| 4 | Setup flow | `display/setup.py`, `display/setup_components/*`, `display/async_operations.py`, `display/setup_models.py` | about 2,800 before run 1 | 31,000 | D01–D04, C01, C02, C08, X01 (display part), A09 (interface part), O4, W2, discovery-fallback row |
| 5 | Gauge display and touch | `display/manager.py`, `display/touch.py`, `display/input/*`, `display/models.py`, `display/splash.py` | about 4,700 before run 1 | 52,000 | C03–C07, C09, F02, O2, O5, two task rows |

### 4.2 Run 1 — Dead code removal

- **Rule:** delete only what has no caller in `src/`; delete the tests that exist only for the deleted code; change no behaviour.
- **Candidates (each to be confirmed by a caller search in the prompt):**
  - `display/input/touch_coordinator.py`: `handle_touch_move`, `handle_touch_up`, slider and gesture-callback paths. This removes the `TouchAction.DRAG` candidate defect.
  - `display/models.py`: the eleven `gesture_*` fields.
  - `utils/config.py`, `display/models.py`: `rpm_warning`, `rpm_danger` (decision D3).
  - `utils/default-config.txt`.
  - `display/setup_components/state/coordinator.py`: control auto-hide, filter toggle, manual MAC entry (decision D2); the unreachable manual-entry branch in `display/setup.py`.
  - `utils/platform.py`: capability API without callers.
  - `display/performance/monitor.py`: dirty-region and font-cache members without callers.
  - Dead `ImportError` fallbacks for required packages that carry a `TODO: issue-ac11505d` marker.
  - Stale comment at `comm/pairing.py:132-135`.
- **Acceptance:** full pytest pass; mypy clean; the report lists removed symbols and the line count before and after.
- **Note:** this run edits files that runs 4 and 5 own. It runs first and alone, so there is no conflict.

### 4.3 Run 2 — Communication layer

- **Medium:** A01 (test `_shutdown` after `_open()`; close the handle), A02 (`OSError` in the serial error set).
- **Low:** A03, A04, A05 (WARNING, no traceback, rate-limited), A06 and A07 (chunk wait sized to the scan limit; return code logged; one manager per discovery), A09 (store changes memory only after a successful save; results returned), A10 (decision D5), A11, A12 (documented limit; no code change proposed), F03.
- **Interfaces:** the contracts of [3.0](#30-approach).
- **Task rows:** `last_connected` accepts `str` (mypy candidate); discovery-fallback mechanism (same-scan results, no second pass).

### 4.4 Run 3 — Application lifecycle, logging, utils

- **Lifecycle:** B01, B02, B03, B04 (decision D7), B06 (pass the caller's timeout), B07, F01.
- **Logging:** O1 (root level follows the debug switch after startup); `--validate-config` without file logging (also removes the cause of G01); log paths under `GTACH_HOME`; the incorrect "reboot command failed" record.
- **Utils:** E02, E03, E04, E05, E06; `load_engine_profile` DEBUG record on every start; unchecked `get_state_info` (mypy candidate).
- **Packaging:** `[tool.mypy] platform = "linux"`.

### 4.5 Run 4 — Setup flow

- **Precondition:** `design-a3b4c5d6` is updated and approved first (decision D1), because the empty-scan behaviour changes.
- **Structure (W2):** one place decides what follows a finished operation. Completion callbacks are ignored when their operation is no longer the registered one, and Cancel calls the cancel interfaces of run 2. This resolves X01, C08 and D04 by one mechanism instead of three patches.
- **Medium:** D01, C08.
- **Low:** C01, C02, D02, D03, D04, A09 (interface part), O4; `Optional` surface passed to `SetupDisplayManager` (mypy candidate).
- **Task row:** discovery fallback, user-interface part.

### 4.6 Run 5 — Gauge display and touch

- **Low:** C03, C04, C05 (local copy of `_setup_manager`), C06 (decision D6), C07 (expiry of a stale touch start), C09, F02.
- **Efficiency:** O2 (one `_link_lost()` evaluation per frame), O5.
- **Task rows:** `get_font(18)` in `_render_disconnected`; `rpm_bands` default `None` (mypy candidate).
- **Not included:** splitting `manager.py` (W4). See decision D8.

### 4.7 Document Sets

| Run | UUID | Documents (`issue-`, `change-`, `prompt-`) |
|---|---|---|
| 1 | `cfa4e617` | `…-cfa4e617-dead-code-removal.md` |
| 2 | `b4f9607a` | `…-b4f9607a-comm-layer-defects.md` |
| 3 | `042dd7ff` | `…-042dd7ff-lifecycle-logging-utils.md` |
| 4 | `34781bfe` | `…-34781bfe-setup-flow.md` |
| 5 | `2550e4ee` | `…-2550e4ee-gauge-display-touch.md` |

Deviations from 4.2 to 4.6, recorded in the change documents:

- A09 has a third part (`DisplayManager._on_clear_settings`), assigned to run 5.
- B02 needs one attribute from the setup flow, so it is completed by run 4; between runs 3 and 4 ATZ is always sent.
- Run 4 removes one `type: ignore` at a call in `app.py`, the only edit outside its own files.
- C03 and C09 are resolved by correcting the documentation and adding a warning, not by changing behaviour.
- `[tool.mypy] python_version` is left unchanged and recorded as an open point in `change-042dd7ff`.

### 4.8 Execution Profile

| Setting | Value |
|---|---|
| Worker and reviewer | Claude Code, cloud session, manual invocation (P13.3 Option C); no engine |
| Model | Claude Opus 5.5 |
| Effort | `medium` for runs 1, 2, 3 and 5. `high` may be considered for run 4, which restructures the setup flow; this is a judgement, not a measured result |
| Ultracode | Off as a session setting. Used once, by keyword, in run 1 |

**Ultracode.** Ultracode is a Claude Code setting, not a model or an effort level. When on, Claude plans a dynamic workflow (a script that runs many subagents in parallel) for each substantive task, at the session's current effort level, and each request uses more tokens and time (Anthropic, 2026a).

- **Not used for runs 2 to 5.** These runs make coupled edits in a small set of files that must be understood together; they are not a fan-out. Parallel subagents editing the same files add coordination risk. A workflow run takes no user input mid-run, so an ambiguity in a prompt would be resolved without the operator. One prompt should yield one implementation and one report.
- **Used in run 1.** Each deletion candidate needs an independent check that it has no caller, which is the many-items pattern workflows are intended for. The run-1 instruction includes the keyword `ultracode` and asks for adversarial verification of each candidate before deletion. The keyword takes effect only in a prompt typed by the operator.
- **Optional:** an independent workflow review after a run. This is a quality choice with a token cost.

**Cloud session preconditions.**

- A cloud session works from the GitHub clone. Everything a run needs must be in tracked files: the issue, change and prompt documents, `CLAUDE.md` and this proposal (tracked since 2026-11-11).
- The repository is private; the session needs GitHub access to it.
- The pytest gate needs the project's dependencies (pygame and the others in `pyproject.toml`) installed in the cloud environment. This was not checked.
- A cloud session is not assumed to reach `gtach.local` or `ELM327-Emulator.local`. On-device verification stays on the Mac ([7.0](#70-sequence-and-gates)).

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Items Outside the Five Runs

| Item | Handling | Reason |
|---|---|---|
| G02, G03 (`bin/gtach-preflight.sh`, `bin/gtach-verify-36b6ea95.sh`) | Direct edit by the planner; done 2026-11-11 | `bin/` is exempt from the workflow |
| G01 | Resolved by run 3 | The cause is in `main.py` |
| Design review row (`ai/workspace/design/`) | Planner work, before run 4 | Run 4 needs a current setup design in any case; the review is done in the same sitting |
| Stuck Bluetooth state (EBUSY) row | Re-test on the device after run 2, with the process's sockets listed during the fault; specify only then | A01 shows one in-process mechanism for a persistent EBUSY, but only on the setup path. Whether the 2026-10-08 event was in-process or in the controller cannot be decided statically |
| Render caching `821919ce`, conditional render `9ed1c77e` | Remain deferred | Their own withdrawal condition is met; O1 and O2 are cheaper. Re-evaluate with measured frame times after run 5 |
| In-car use row | After run 5, on the final version | It is the acceptance test for the whole series |
| pygame / setuptools row | Remains a monitor item | No action until it breaks |
| Four open scheduled audits | Move to `audit/closed/` | Superseded by `audit-71ab3751` §5.0 |

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Decisions Required

**Status:** D1 to D8 accepted as recommended by William Watson on 2026-11-11.

| ID | Decision | Recommendation (accepted) | Affects |
|---|---|---|---|
| D1 | Behaviour after an empty filtered scan | One automatic unfiltered pass; if still empty, DEVICE_LIST with "No devices found" and Retry. No endless rescan. Refined in `design-a3b4c5d6` §4.3, approved 2026-11-12: list the unfiltered results of the same scan instead of running a second pass | Runs 2, 4; design `a3b4c5d6` |
| D2 | Manual MAC entry and manual filter toggle (no caller today) | Remove both. D1 makes the toggle unnecessary | Run 1 |
| D3 | `rpm_warning`, `rpm_danger`, `gesture_*` config keys | Remove from the schema. `ConfigStore` preserves unknown keys, so existing files stay valid. **Revised in run 1:** the `gesture_*` fields were removed; `rpm_warning` and `rpm_danger` were kept, because `ConfigStore.validate()` reports unknown keys and `--validate-config` would then fail on existing files. The premise holds for `load` and `save` only | Run 1 |
| D4 | Extent of reduction in `utils/platform.py` | Remove only members without callers; keep detection | Run 1 |
| D5 | Simulated pairing writes to the real device store (A10) | Simulation uses its own store file | Run 2 |
| D6 | Long press and movement (C06) | A long press requires movement below the swipe threshold; otherwise the gesture is a swipe | Run 5 |
| D7 | Exit status after startup failure or watchdog exit (B04) | Non-zero for failures; zero for the update restart. `gtach.service` has `Restart=always`, so restart behaviour is unchanged | Run 3 |
| D8 | Splitting `display/manager.py` (W4) | Do not split now. It is a large refactor with no defect behind it. Reconsider when the options or update screens next change | None |

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Sequence and Gates

| Step | Actor | Action | Gate |
|---|---|---|---|
| 1 | William | Decide D1 to D8 — done 2026-11-11 | — |
| 2 | Planner | Update `design-a3b4c5d6`; review stale designs; author five issue/change/prompt sets; fix G02 and G03 | Approval of the design and of all five prompts (`approve.py`) |
| 3 | Claude Code | Run 1 | Full pytest, mypy, commit |
| 4 | Claude Code | Run 2 | Full pytest, mypy, commit |
| 5 | Claude Code | Run 3 | Full pytest, mypy, commit |
| 6 | William + planner | Device session A with the emulator: A01, link loss and reconnect, EBUSY re-test, logging | Pass before run 4 |
| 7 | Claude Code | Run 4 | Full pytest, mypy, commit |
| 8 | Claude Code | Run 5 | Full pytest, mypy, commit |
| 9 | William + planner | Device session B: setup flow end to end, touch, gauge; then the in-car test | Acceptance; version increment; close documents |

- Planner code review (P02) follows each run and precedes the next. A defect found there re-enters the cycle for that set only.
- Two device sessions instead of five keep the on-device effort low. The cost is that a fault found in session A may come from any of runs 1 to 3; the three separate commits allow bisection.

[Return to Table of Contents](#table-of-contents)

---

## 8.0 Alternatives Considered

| Alternative | Runs | Assessment |
|---|---|---|
| One set per finding | 43 | Rejected. Maximum traceability, but the approval and test overhead is out of proportion to 39 low findings |
| Sets by severity (medium first, then low) | 2 to 3 | Rejected. Each run would touch nearly every file, so the reading load is the whole codebase per run and later runs conflict with earlier ones |
| Three runs: (1) dead code + run 3, (2) comm, (3) all of `display/` | 3 | Technically viable with the 1,000,000-token window: the third run would read about 83,000 tokens of source. Not chosen, because one change over the whole display package is harder to review and a device fault is harder to bisect |
| Five runs by file partition | 5 | **Chosen** (confirmed 2026-11-11). Disjoint file ownership keeps each review small and gives five bisection points |
| Fix first, delete last | 5 | Rejected. Later runs would read and partly repair code that is then deleted |

[Return to Table of Contents](#table-of-contents)

---

## 9.0 Risks

| Risk | Mitigation |
|---|---|
| Run 1 removes something that is used through a path a caller search misses (string lookup, test-only use) | Subtractive-only rule; full test suite and mypy as the gate; removed symbols listed in the run report for review |
| Suspected findings (A01 consequence, A02, A06, A12, C07) are fixed without proof of the fault | The fixes are small and safe when the fault does not exist. A01 is checked on the device in session A |
| Run 4 changes the setup flow structure and introduces regressions | Design approval first; emulator-based end-to-end test in session B; `simbt` path kept working (B01, A10 are fixed before run 4) |
| Prompts approved together become stale if an earlier run deviates from its change document | Symbol-based prompts; the two cross-run contracts are fixed in advance; a deviating run triggers re-approval of the affected later prompt only |
| The cloud environment lacks dependencies, so the pytest gate does not run | Verify the environment with a full pytest run before run 1 |
| A needed document is not in the clone | Commit and push all issue, change, prompt and design documents before each run |
| The run-1 workflow deletes on a wrong "no caller" result | Adversarial verification per candidate; full pytest and mypy gate; removed symbols listed in the report |
| Comment reduction removes rationale that is still needed | The issue reference stays in the code; the change records hold the history |

[Return to Table of Contents](#table-of-contents)

---

## 10.0 Coverage Check

### 10.1 Audit findings

| Findings | Where |
|---|---|
| A01–A07, A10–A12, F03 | Run 2 |
| A09 | Runs 2 and 4 |
| X01 | Runs 2 and 4 |
| B01–B04, B07, E02–E06, F01 | Run 3 |
| B06 | Runs 2 and 3 |
| D01–D04, C01, C02, C08 | Run 4 |
| C03–C07, C09, F02 | Run 5 |
| E01 | Run 1 |
| G01 | Run 3 (cause) |
| G02, G03 | Direct `bin/` edit |

All 43 findings are assigned. Observations: O1 run 3, O2 and O5 run 5, O4 run 4, O3 remains with deferred row `821919ce`.

### 10.2 Weaknesses

| Weakness | Where |
|---|---|
| W1 Size | Run 1 |
| W2 Setup flow structure | Run 4 |
| W3 Comments | Comment rule in every run |
| W4 `manager.py` | Not addressed (D8) |

### 10.3 Task register rows

| Row | Where |
|---|---|
| `821919ce`, `9ed1c77e` | Remain deferred |
| `get_font(18)` | Run 5 |
| Discovery fallback | Runs 2 and 4 (D1) |
| In-car use | After run 5 |
| Stuck Bluetooth state | After run 2, evidence first |
| Design review | Planner, step 2 |
| Six mypy candidates | Runs 1 (2), 2 (1), 3 (1), 4 (1), 5 (1) |
| `[tool.mypy]` platform | Run 3 |
| `--validate-config` logging | Run 3 |
| Reset outcome log | Run 3 |
| Log paths and `GTACH_HOME` | Run 3 |
| `load_engine_profile` DEBUG record | Run 3 |
| pygame / setuptools | Remains a monitor item |

[Return to Table of Contents](#table-of-contents)

---

## References

ANTHROPIC, 2026a. *Orchestrate subagents at scale with dynamic workflows* [online]. Claude Code Docs. Available from: https://code.claude.com/docs/en/workflows [Accessed 11 November 2026].

ANTHROPIC, 2026b. *Claude Opus 5.5* [online]. Claude Platform Docs. Available from: https://platform.claude.com/docs/en/models/opus-5-5 [Accessed 11 November 2026].

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial proposal |
| 1.1 | 2026-11-11 | D1 to D8 recorded as accepted; five runs confirmed; §2.2 context budget corrected to the 1,000,000-token window of Opus 5.5; §4.7 Execution Profile added (Claude Code cloud, medium effort, ultracode guidance, cloud preconditions); §8.0 and §9.0 updated; References added |
| 1.2 | 2026-11-11 | §3.0 contracts corrected and extended (existing `show_all_devices` parameter, same-scan fallback, three further interfaces); §4.7 Document Sets added with the five UUIDs and the deviations; Execution Profile renumbered to §4.8; §5.0 G02 and G03 marked done; D1 refinement noted |
| 1.3 | 2026-11-11 | §6.0 D3 revised after run 1 (`rpm_warning`, `rpm_danger` kept) |
| 1.4 | 2026-11-12 | §6.0 D1 refinement approved |
| 1.5 | 2026-11-12 | Closed: series completed; moved to proposal/closed/ |

---

Copyright (c) 2026 William Watson. MIT License.
