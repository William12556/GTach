Created: 2026 November 12

# Report: Gauge Display and Touch Corrections

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Changes by Edit](<#2. changes by edit>)
3. [Comment Rule](<#3. comment rule>)
4. [Tests](<#4. tests>)
5. [Success Criteria](<#5. success criteria>)
6. [Deviations and Notes for the Planner](<#6. deviations and notes for the planner>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-2550e4ee (change-2550e4ee, issue-2550e4ee; run 5 of proposal-71ab3751) was implemented in one commit on branch `claude/blissful-cannon-l2gjtt`. EDITS A to E and the COMMENT RULE were applied. The issue and change T-Docs remain active pending test results. The prompt T-Doc was closed and moved to `ai/workspace/prompt/closed/`.

- pytest `tests/`: 721 passed. The base commit had 694; the new `tests/test_gauge_display_touch.py` adds 27.
- mypy `src/`: no issues.
- black, isort and flake8 report nothing in `src/gtach/display/` or in the new test module. The flake8 finding F401 (`inspect` unused, line 533) in `tests/test_disconnected_screen.py` is present on the base commit, in a line this change does not touch.
- `git diff` touches `display/manager.py`, `display/touch.py`, `display/models.py`, `display/splash.py`, `display/input/touch_coordinator.py`, `tests/`, and the T-Docs under `ai/workspace/`.
- Python 3.9 is not available on this host (3.13). The code uses no syntax or library call newer than 3.9.

Regression check: with `src/` reverted to the base commit, the new tests behaved as follows:

- 18 of the 23 tests that do not run a display-loop frame fail.
- The frame-running C04 test hangs. On the base code, `record_frame_start` on a missing `performance_monitor` raises before the heartbeat, so the loop never reaches its exit condition. This is the per-frame error C04 describes.
- The 5 tests that pass on the base code are expected to pass there:
  - The two `rpm_bands` tests: the old `__post_init__` also produced separate instances.
  - The setup-mode routing test: that behaviour is unchanged.
  - The two F02 tests: the test file under them was already the corrected version.

[Return to Table of Contents](<#table of contents>)

---

## 2. Changes by Edit

| Edit | File | Change |
|---|---|---|
| A(1) | `manager.py` | `touch_handler`, `_setup_manager`, `_in_setup_mode`, `_setup_entry_callback`, `_splash_screen` and `performance_monitor` are assigned inactive defaults in `__init__` before `_initialize_components()`, which runs before any thread starts. `_initialize_legacy_components` no longer assigns the setup attributes. Its touch initialisation catches `Exception`, logs at ERROR with `exc_info`, and leaves `touch_handler` None. The performance monitor is assigned only after `start_monitoring()` succeeds. `stop`, the display loop, `get_performance_stats` and `get_display_state` tolerate `performance_monitor is None`. |
| A(2) | `manager.py` | The display loop copies `_setup_manager` and `performance_monitor` to locals once per frame. `_render_setup_mode` now takes the setup manager as an argument. `handle_touch_event` copies the attribute to a local and tests and uses the local. `_register_view_regions` only tests the attribute and does not use it. `touch.py` `_handle_setup_swipe` already read it once via `getattr`. |
| B(1) | `touch.py` | `_process_touch`, on release outside setup mode: if the movement `max(abs(dx), abs(dy))` is at or above the swipe threshold, or the duration is below `touch_long_press`, the release goes to the short-press path. Otherwise, if the start position is on a button region, the release goes to the short-press path at the start position, so the button's action runs once. Otherwise it is a long press. The threshold lookup the short-press path performed is now the module function `_swipe_threshold(display_manager)`, used by all three call sites. In setup mode every release still goes to `_handle_short_press` first. |
| B(2) | `touch.py` | The class constant is `_TOUCH_START_MAX_AGE_S = 10.0`. A down or move event replaces a stored start older than this. A release whose duration exceeds it discards the start without action. Both use the event's own clock. `timestamp if timestamp else …` became `timestamp is not None`, so a timestamp of 0.0 is no longer replaced by `time.monotonic()`. |
| C(1) | `manager.py` | `_display_loop` sets `self._frame_link_lost = self._link_lost()` at the start of each frame. `_current_view_key`, `_register_view_regions`, `_render_normal_modes` and `_draw_status_indicator` read that value. `_link_lost` keeps its latch, its transition logging and the property that every failure path returns True. Its code is unchanged; only its docstring and one comment changed. The initial value is True. |
| C(2) | `manager.py` | The cause-line font in `_render_disconnected` is now `TypographyConstants.FONT_SMALL_TEXT` (20 px). |
| C(3) | `manager.py` | The new module function `gauge_full_scale(redline)` and the module constant `GAUGE_MAX_RPM_CAP = 9000` hold the formula unchanged. `_gauge_max_rpm` delegates to them, and its docstring now describes the cap and the off-dial redline. `_load_config` logs one WARNING when the loaded redline exceeds full scale. |
| C(4) | `manager.py` | `_save_config` returns `bool`. When the save fails, `_toggle_palette` logs one WARNING and keeps the new palette. Its docstring states this behaviour. |
| C(5) | `manager.py` | `_on_clear_settings` iterates `get_all_devices()` and checks each `remove_device` result. It logs an ERROR naming each device that could not be removed, then invokes the setup entry callback as before. |
| D | `models.py` | `rpm_bands: RPMBands = field(default_factory=RPMBands)`. `__post_init__`, the `type: ignore` markers and the TODO markers are removed. `RPMBands` was already defined before `DisplayConfig`. |
| D | `splash.py` | The new `_check_fit_once(key, text, font_size)` validates once per key per instance, with the size actually drawn: title 72, subtitle `FONT_BODY`, version 40. The sizes are named `_TITLE_FONT_SIZE` and `_VERSION_FONT_SIZE`. Before this change the checks ran every frame with 36, 24 and 20 px against drawn sizes of 72, 24 and 40. |
| E | `tests/test_callbacks_outside_locks.py` | Inside the callback, a second thread tries to acquire the coordinator lock with a 1 s timeout. The test asserts that the acquisition succeeded and that the region registered by the callback exists. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Comment Rule

- **`manager.py`:** applied to the edited functions and to `_link_lost`:
  - `__init__` (performance monitor block)
  - `_toggle_palette`
  - `_initialize_legacy_components`
  - `_save_config`
  - `_display_loop`
  - `_render_setup_mode`
  - `_render_normal_modes`
  - `_gauge_max_rpm`
  - `_current_view_key` (the "disconnected" item)
  - `_register_view_regions` (the disconnected comment)
  - `_on_clear_settings`
  - `_render_disconnected` (the cause-line comment)
  - `_draw_status_indicator`
  - `handle_touch_event`

  The `_current_view_key` docstring named "Setup and Simulate" buttons. It now names Setup and Reset, which are the buttons the screen registers. The rest of the file is unchanged, as the change specifies.
- **`touch.py`:** the history narration was reduced in `_handle_long_press`, `_handle_short_press`, `_handle_setup_swipe` and `_handle_setup_touch`. Line-number references to `manager.py` that were no longer accurate were removed.
- **`models.py`:** the palette and `DisplayMode.RADIAL` comments were reduced. One comment stated that urgency "is carried by the shift-cue flash"; the shift cue was removed (issue-950128c0), so that clause was removed.
- **`splash.py`:** the history in the colour-scheme comment, the layout-mode comments and the border comment was reduced, along with the font docstrings that stated incorrect sizes.
- **`touch_coordinator.py`:** the module docstring no longer says "Extracted from monolithic DisplayManager".

[Return to Table of Contents](<#table of contents>)

---

## 4. Tests

The new module is `tests/test_gauge_display_touch.py`. It covers each `testing_requirements.test_cases` row of change-2550e4ee, plus the prompt's edge cases:

| Scenario | Test |
|---|---|
| C04: touch and monitor faults; one frame | `TestInitialisationFaults`. A real `DisplayManager` with `create_touch_interface` and `PerformanceMonitor` raising; one SPLASH frame and one RADIAL frame run with no loop error. The status report with `performance_monitor` None. |
| C05: `_setup_manager` non-None on the first read, None on the second | `TestSetupManagerReadOnce`. A property subclass is set on the instance. Covers `handle_touch_event` and one display-loop frame; the setup stub is called once and nothing is logged at ERROR. |
| C06: slow swipe; hold at rest; hold on a button; release exactly at the threshold; duration exactly `touch_long_press`; long hold in setup mode | `TestLongPressRequiresRest`. Uses a real `TouchHandler` on a real `DisplayManager` and checks the palette state. The button callback runs exactly once. |
| C07: down at 0, down at 20, release at 20.2; down at 0, release at 12 | `TestStaleTouchStart` |
| O2: one link callback call per frame | `TestOneLinkEvaluationPerFrame`, for a connected and a disconnected callback |
| Cause-line font | `TestCauseLineFont`. Also corrected in `tests/test_disconnected_screen.py`, which asserted the old 18 px. |
| C09: redline 12000 | `TestRedlineAboveFullScale`. Returns 9000 and logs exactly one WARNING. |
| C03: save fails | `TestPaletteSaveFailure`. The palette switches and exactly one WARNING is logged; a successful save returns True. |
| A09: two devices; one fails to remove | `TestClearSettings` |
| `rpm_bands` default | `TestRpmBandsDefault`. Each instance gets its own `RPMBands`, and an explicit argument is kept. |
| O5: 30 splash frames | `TestSplashFitChecks`. One check per drawn text, with the drawn size. |
| F02: patched coordinator | `TestLockTestDetectsCallbackUnderLock`. The corrected test raises `AssertionError` against a coordinator that dispatches under its lock, and passes against the real one. |

[Return to Table of Contents](<#table of contents>)

---

## 5. Success Criteria

| Criterion | Result |
|---|---|
| Constructs and renders after a touch or monitor fault | Met (C04 test) |
| No two-read test-and-use of `_setup_manager` | Met (A(2)) |
| Swipe never a long press; held button presses | Met (C06 tests) |
| Touch start older than 10 s unused | Met (C07 tests) |
| One `_link_lost` per frame | Met (O2 test) |
| Cause line uses `FONT_SMALL_TEXT` | Met |
| `_gauge_max_rpm` and `_toggle_palette` docstrings match behaviour | Met |
| `_on_clear_settings` removes all devices and checks the results | Met |
| No `type: ignore` at `DisplayConfig.rpm_bands` | Met |
| Splash fit checks once each | Met |
| `test_callback_may_register_regions` fails under the lock | Met (F02 test) |
| `git diff` limited to the permitted files and `tests/` | Met. `display/input/touch_coordinator.py` is within `display/input/*`. |
| pytest and mypy pass | Met |

[Return to Table of Contents](<#table of contents>)

---

## 6. Deviations and Notes for the Planner

1. **New public method `TouchEventCoordinator.is_button_at(pos)`.** The coordinator's hit test `_find_hit_region` is private and must be called under the coordinator lock. `is_button_at` wraps it under the lock and invokes no callback. The change document lists `interface_changes: []`; this method is an addition and is recorded here. It is used only by `TouchHandler._starts_on_button`.
2. **A hold on a button presses at the start position.** The change specifies "a hold that starts on a registered button region is a press of that button". The release is therefore dispatched at the start position, not at the end position. The movement is below the swipe threshold, so the two positions differ by less than the threshold.
3. **Stale-start replacement on down or move applies in setup mode too.** It changes only which start is stored, not where a release is routed; setup-mode releases still go directly to the short-press path. The release-side discard applies outside setup mode only, as the constraint requires.
4. **The release-side staleness test uses the gesture duration.** It compares `current_time - start_time` with the limit. This is the same quantity as the start's age at release, measured on the event clock.
5. **A failed palette save logs twice.** `_save_config` keeps its ERROR record with `exc_info` (CLAUDE.md §4 rule 6), and `_toggle_palette` adds the one WARNING that the change requires.
6. **Helpers are module functions rather than methods.** `_swipe_threshold` in `touch.py`, and `gauge_full_scale` with `GAUGE_MAX_RPM_CAP` in `manager.py`, are module-level. Existing tests call `TouchHandler` and `DisplayManager` methods unbound against `SimpleNamespace` hosts (`test_touch_dispatch.py`, `test_device_list_focus.py`, `test_setup_and_gauge.py`, `test_config_store.py`), and new methods on `self` would not exist on those hosts.
7. **C(1) evaluates the link before the frame's sample drain.** The drain stays in `_render_normal_modes`, so the frame value reflects samples drained up to the previous frame. The change document records this as risk EDIT C(1): one frame, about 33 ms at 30 Hz.
8. **Test-only correction.** `tests/test_disconnected_screen.py::test_cause_line_is_unchanged_position_and_font` was renamed `test_cause_line_position_and_font` and now expects `FONT_SMALL_TEXT`.
9. **Design refresh.** design-b8c9d0e1 should record the per-frame link value, the touch classification and the new coordinator method. This is a planner task (traceability.design_updates).
10. **Verification.** Device session B (slow swipe, held button, long press at rest, palette toggle, DISCONNECTED cause line, Clear settings) and then the in-car test remain open.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial report for prompt-2550e4ee. |

---

Copyright (c) 2026 William Watson. MIT License.
