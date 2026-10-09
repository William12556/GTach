Created: 2026 October 09

# Report: Nine-Change Implementation Session

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Verification Method](<#3.0 verification method>)
- [4.0 Changes Implemented](<#4.0 changes implemented>)
- [5.0 Findings Requiring Decision](<#5.0 findings requiring decision>)
- [6.0 Deviations from Prompt Specifications](<#6.0 deviations from prompt specifications>)
- [7.0 Commit Record](<#7.0 commit record>)
- [8.0 Work Remaining](<#8.0 work remaining>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records one session that executed the nine T03 prompts approved on 2026-10-09. Each change has its own report in this directory; this report summarises the session as a whole, the cross-cutting findings, and what is left for a human.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Instruction and Outcome

The instruction was to implement the nine prompts in a fixed order on branch `claude/busy-albattani-t74y2a`, without merging into main:

1. 50bf25ad
2. 04c18cda
3. ae65fa10
4. c9de5fb0
5. 2b3a1547
6. 8a9022fc
7. 273ca048
8. e215a184
9. ac11505d

For each change: close the prompt T-Doc, write a report, and commit. Leave the issue and change T-Docs untouched.

Outcome: **all nine were implemented, committed and pushed.** All nine prompt T-Docs are in `ai/workspace/prompt/closed/` with the Version History row "Implemented; closed". No issue or change T-Doc was edited, and nothing changed in `CLAUDE.md`, `ai/governance/` or `ai/task.md`. No prompt was left open.

| Measure | Start of session | End of session |
|---|---|---|
| `pytest tests/` | 539 passed, 2 xfailed (strict) | 561 passed, 0 xfailed |
| `mypy src/` | 338 errors in 39 files | 0 errors (59 source files) |
| `TODO: issue-ac11505d` suppressions | 0 | 20 |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification Method

- Python 3.13 dev venv: `pip install -e .[dev]`.
- `pytest tests/` before every commit; a commit was made only on a full pass.
- Where a change added regression tests, they were also run against the unmodified source to confirm they detect the defect (50bf25ad, 04c18cda, ae65fa10, 2b3a1547, 8a9022fc mutation check, e215a184).
- black, isort and flake8 on the changed files; `mypy src/` count tracked after each change.
- 273ca048 and ac11505d: import smoke check and an 8 s `--transport simtcp` run under `SDL_VIDEODRIVER=dummy`. Each run's output was compared with a run against the code before the change.
- ac11505d: all `gtach` modules imported under Python 3.9.25, using a throwaway venv in the session scratchpad (not part of the project).
- No on-device verification: `gtach.local` is unreachable from the session.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Changes Implemented

| Change | Summary | pytest after | Change report |
|---|---|---|---|
| 50bf25ad | `SimTransport.drop_link` clears `_connected`, so a dropped simulated link is observed and reconnected. | 544 passed, 1 xfailed | `report-50bf25ad-…` |
| 04c18cda | Pre-initialised OBD settle waits in 0.5 s interruptible slices with a heartbeat after each, instead of `time.sleep(1.5)`. | 548 passed | `report-04c18cda-…` |
| ae65fa10 | `ConfigStore.save` reads unknown keys from the file at save time, so a save without load keeps them. | 553 passed | `report-ae65fa10-…` |
| c9de5fb0 | `BluetoothDevice.from_discovered` (with a `DiscoveredDevice` Protocol) replaces two hand-written conversions. | 556 passed | `report-c9de5fb0-…` |
| 2b3a1547 | `gtach/__init__.py` no longer re-exports `GTachApplication` and `main`; importing `gtach` no longer imports pygame. | 559 passed | `report-2b3a1547-…` |
| 8a9022fc | Slot-contents tests render through `_render_device_list_screen` with a recording renderer. | 559 passed | `report-8a9022fc-…` |
| 273ca048 | Dead-code groups D1–D8 removed; the suite passed after each group. | 559 passed | `report-273ca048-…` |
| e215a184 | Durations and cache ages in five files use `time.monotonic()`, with a per-variable classification table. | 561 passed | `report-e215a184-…` |
| ac11505d | mypy strict clean: utils, core, comm, display, then app/main; stub packages added to `[dev]`. | 561 passed | `report-ac11505d-…` |

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Findings Requiring Decision

The strict type check found these behavioural defects. Under the prompt's constraints they are suppressed with TODOs, not fixed. They are the main input for follow-up issues:

1. **`TouchAction.DRAG` does not exist** (`display/input/touch_coordinator.py`). Every drag in `handle_touch_move` raises AttributeError, which is logged and turned into None.
2. **The manual-entry setup screen is unreachable** (`display/setup.py`). `_render_screen` tests all six `SetupScreen` members before `manual_entry_mode`.
3. **`DisplayConfig.rpm_bands` defaults to `None`** (`display/models.py`) instead of using `default_factory=RPMBands`.
4. **`app.py` passes an `Optional` surface** to `SetupDisplayManager`, which dereferences it without a check.
5. **`AcknowledgementStateManager.get_state_info`** returns `yaml.safe_load` unchecked against its declared mapping type.
6. **`comm.models.BluetoothDevice.last_connected`** is annotated `Optional[datetime]` but accepts a str.

Other observations:

- Removing D1 in 273ca048 left these unreferenced: the `get_info` methods of the touch interfaces, `SplashScreen.get_info`, `_global_performance_manager`, and `CircularPositioningEngine._cache_lock`. They were left in place (out of scope) and are listed in that report.
- e215a184: `PlatformDetector` uses `0` to mean "never detected". Under `time.monotonic()`, capabilities computed before any platform-type detection count as cached for the first 300 s after boot. The effect is benign; it is recorded for review.
- Nine `pygame`/`yaml` import fallbacks and two class-import fallbacks are dead code, because the dependencies are mandatory. They are suppressed, not deleted.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deviations from Prompt Specifications

| Change | Deviation | Reason |
|---|---|---|
| 04c18cda | DEBUG message split across two string literals. | 88-column limit; the rendered text is unchanged. |
| 8a9022fc | Reversing the offsets fails 3 of 4 tests, not 4; an all-zero mutation was added, which fails 4 of 4. | The one-device case looks the same under reversal. |
| 8a9022fc | `grep '_slots'` still matches two existing test names. | The constraints forbid changing other test classes. |
| 273ca048 | One extra blank line removed in `touch_interface.py`. | flake8 E303 after the deletion. |
| e215a184 | `tests/test_performance_instrumentation.py` `clock` fixture also fakes `monotonic`. | Without it, 7 tests fail; that file is not in the prompt's list. |
| e215a184 | One block comment in `PerformanceMonitor.__init__` instead of one per variable. | Several adjacent variables switched together. |
| ac11505d | TODO suppressions written on two lines, with `# noqa: E501` where the line is still too long. | The prescribed one-line form exceeds 88 columns. |
| ac11505d | A few code edits that behave identically: split returns, a local rename, `assert`s after `Popen(PIPE)`, `typing.cast` after helper guards. | No pure annotation could express them; each is listed in that change's report. |

Pre-existing formatting failures were left untouched: black on `tests/test_stacks_log_rotation.py`, and flake8 E501 at `src/gtach/main.py:42`.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Commit Record

Branch `claude/busy-albattani-t74y2a`, pushed to origin; base `42d61fc`.

| Commit | Change |
|---|---|
| `3404125` | 50bf25ad |
| `1a36ed0` | 04c18cda |
| `3c6472a` | ae65fa10 |
| `7c6574e` | c9de5fb0 |
| `7a91a42` | 2b3a1547 |
| `d4e11e3` | 8a9022fc |
| `bf03008` | 273ca048 |
| `00c9129` | e215a184 |
| `e5ceb62` | ac11505d utils + stubs |
| `dae7d83` | ac11505d core |
| `5ebd823` | ac11505d comm |
| `954fb6d` | ac11505d display |
| `1a2ebee` | ac11505d app/main |
| `6b59b8c` | ac11505d prompt close + report |

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Work Remaining

- **On-device verification** on the Pi, per each change report:
  - first OBD connection after setup;
  - pairing persists across a restart;
  - the service starts and `--validate-config` runs;
  - FPS figures stay plausible across the NTP step;
  - real HyperPixel touch works;
  - general normal use.
- After the on-device tests pass, close the nine issue and change T-Docs, which were left active as instructed.
- Raise follow-up issues for the findings in section 5.0.
- Review the branch and merge it into main.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial session report. |

---

Copyright (c) 2026 William Watson. MIT License.
