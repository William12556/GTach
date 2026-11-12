Created: 2026 November 11

# Report: Remove Unused Code and Configuration Keys

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Method](<#2. method>)
3. [Removed Symbols](<#3. removed symbols>)
4. [Candidates Kept](<#4. candidates kept>)
5. [Observed, Not Removed](<#5. observed, not removed>)
6. [Tests](<#6. tests>)
7. [Line Count](<#7. line count>)
8. [Success Criteria](<#8. success criteria>)
9. [Deviations and Notes for the Planner](<#9. deviations and notes for the planner>)
10. [Version History](<#version history>)

---

## 1. Summary

prompt-cfa4e617 (change-cfa4e617, issue-cfa4e617; run 1 of proposal-71ab3751) was implemented in one commit on branch `claude/dreamy-sagan-vhk58i`. EDITS A to H were applied. The only additions are the plain imports of EDIT F, the comment of EDIT G, the CLAUDE.md rule of EDIT H and one new test. The issue and change T-Docs remain active pending test results. The prompt T-Doc was closed and moved to `ai/workspace/prompt/closed/`.

One part of EDIT B was not applied, on the operator's decision during the run. `rpm_warning` and `rpm_danger` remain in the schema; section 4 gives the reason.

- pytest: 589 passed (588 before, plus the one new test). One pre-existing flaky test is described in section 6.
- mypy `src/`: no issues. No `type: ignore` was added.
- flake8, black and isort report nothing in the touched files. Their pre-existing findings in `comm/sim_transport.py` and `main.py` are unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 2. Method

The RULE of change-cfa4e617 was applied to each candidate before it was deleted. The procedure was as follows:

- `src/` and `tests/` were searched for the name and for its string form (`"name"`, `.name ==`, `getattr`, `hasattr`, `monkeypatch.setattr`, `sys.modules`).
- The search also covered subclasses and interfaces that reach the candidate, and repository files outside `ai/` (configs, `bin/`, README).
- Runtime availability of every import fallback was confirmed by importing the ten modules; every flag was `True` and `SplashConfig` resolved.
- After each group (A to G), `pytest tests/` and `mypy src/` were run.

[Return to Table of Contents](<#table of contents>)

---

## 3. Removed Symbols

Names in *italics* were not named in the change. They were removed under the RULE's write-only clause, or because a listed deletion left them orphaned or unreachable. Section 9 has the planner notes on these.

### EDIT A: touch coordinator

| File | Removed |
|---|---|
| `display/input/touch_coordinator.py` | `register_slider_region`, `handle_touch_move`, `handle_touch_up`, `handle_gesture`, `register_gesture_callback`, `_handle_slider_touch_down`, `_handle_slider_drag`, `_calculate_slider_value`, `_end_slider_interaction`, `_recognize_gesture`, `_is_drag_gesture`, `get_slider_value`, `set_slider_value`. Also their state: `_slider_state`, `_gesture_callbacks`, `long_press_duration`, `drag_threshold`, `tap_timeout`. Also *`_touch_state`* (write-only once the readers were gone; its writes in `handle_touch_down` were removed), *the slider branch of `handle_touch_down`* (no slider region can exist), the `cast` and `GestureType` imports, and docstring phrases about gestures and sliders. |
| `display/input/interfaces.py` | `GestureType`; the abstract `handle_touch_move`, `handle_touch_up` and `handle_gesture`; *`TouchAction.MODE_CHANGE`* and *`TouchAction.SLIDER_INTERACTION`* (orphaned; no `.value` or name lookup of `TouchAction` exists). |
| `display/input/__init__.py` | `GestureType` import and `__all__` entry; docstring phrase. |
| `display/manager.py` | The two `register_gesture_callback` calls and their comments. Also *`_setup_touch_callbacks`* and its call, because the method was empty afterwards. `_handle_swipe_down` and `_handle_swipe_up` are kept, because `touch.py:250-254` calls them. |

### EDIT B: configuration (partial; see section 4)

| File | Removed |
|---|---|
| `display/models.py` | The eleven `DisplayConfig.gesture_*` fields and their comments. No positional construction of `DisplayConfig` exists. |
| `utils/default-config.txt` | File deleted. No source, packaging (`pyproject.toml` package-data has no `*.txt`), script or test references it. |

### EDIT C: setup coordinator

| File | Removed |
|---|---|
| `display/setup_components/state/coordinator.py` | The control auto-hide group: `register_interaction`, `_update_control_visibility`, `get_control_alpha`, `are_controls_visible`, and `_controls_visible`, `_last_interaction_time`, `_control_auto_hide_delay`, `_control_fade_duration`, `_control_alpha`, `_control_visibility_lock`. The filter toggle: `toggle_device_filter`, `show_all_devices`. The manual entry group: `enter_manual_entry_mode`, `exit_manual_entry_mode`, `update_manual_mac_input`, `is_valid_mac_address`, `manual_entry_mode`, `manual_mac_input`. Also `set_focused_index`, the three removed keys of `get_focus_info`, the `_update_control_visibility` call in `update_animation`, and the `time` import. |
| `display/setup.py` | `_render_manual_entry_screen` and its branch in `_render_screen`; the `register_interaction` call in `handle_touch_event`; the `show_all_devices` argument of `start_discovery` in `_setup_loop`. Also *the `else` fallback of `_render_screen`*: once the manual-entry branch was gone, mypy reported it unreachable. Every write to `current_screen` is a `SetupScreen` member, so the fallback is unreachable at runtime too. |
| `display/setup_models.py` | `SetupAction.SAVE`, `TEST_CONNECTION`, `CHANGE_DEVICE`, `REMOVE_DEVICE`, `ADD_DEVICE`, `REFRESH`, `MANUAL_ENTRY`, `CONFIRM`, `TOGGLE_FILTER`, `CONNECT_MANUAL`. |

### EDIT D: platform

| File | Removed |
|---|---|
| `utils/platform.py` | `PlatformError`, `run_platform_test`, `log_platform_info`, `clear_detection_cache` and the module-level `check_gpio_availability`. Also *the `if __name__ == "__main__"` block*: it was the only caller of `run_platform_test` and `log_platform_info`, and nothing in the repository runs `python -m gtach.utils.platform`. The `sys` import went with it. No private helper became unreferenced. |

### EDIT E: performance monitor

| File | Removed |
|---|---|
| `display/performance/monitor.py` | `add_dirty_region`, `get_dirty_regions`, `clear_dirty_regions`, `_dirty_regions`, `_total_dirty_area`. Members without a caller: `record_render_operation`, `record_cache_hit`, `record_cache_miss`, `update_memory_usage`, `get_historical_metrics`, `set_target_fps`, `_font_cache_enabled`, `_font_cache`. The write-only chain: `_metrics_history`, `_update_metrics_history`, `_last_metrics_update`, the periodic call in `record_frame_end`, and *`history_duration`* (parameter and attribute; no caller passes it). Also the `pygame` import and a comment sentence about dirty-region timestamps. `dirty_regions_count` is no longer passed to `PerformanceMetrics`; it takes its default of 0, the value it always had. |
| `display/performance/interfaces.py` | The abstract `record_render_operation`, `record_cache_hit`, `record_cache_miss`, `update_memory_usage`, `get_historical_metrics`, `set_target_fps`; the `List` import. |

### EDIT F: dead import fallbacks

All ten listed files now use a plain import. pyproject.toml lists `pygame>=2.0` and `PyYAML>=6.0` as required dependencies; `SplashConfig` and `TouchHandler` are package-internal.

| File | Fallback removed | Flag and branches removed |
|---|---|---|
| `display/manager.py` | pygame | `PYGAME_AVAILABLE`; the early return in `_display_loop`. |
| `display/setup.py` | pygame | `PYGAME_AVAILABLE`; the unavailable branch in `__init__`. |
| `display/setup_components/rendering/device_surfaces.py` | pygame | `PYGAME_AVAILABLE`; the unavailable branch in `__init__`. |
| `display/typography.py` | pygame | `PYGAME_AVAILABLE`; three branches (`__init__`, `get_font`, `get_plain_font`). |
| `display/splash.py` | pygame, `SplashConfig` | Flag kept (section 4). |
| `display/graphics/splash_graphics.py` | pygame | Flag kept (section 4). |
| `display/__init__.py` | `TouchHandler` | `TOUCH_HANDLER_AVAILABLE` and its `__all__` entry; `"TouchHandler"` is now listed in `__all__` directly. |
| `utils/config.py` | yaml | `YAML_AVAILABLE`; one branch in `load_engine_profile`. |
| `utils/ack_state.py` | yaml | `YAML_AVAILABLE`; three branches. |
| `comm/device_store.py` | yaml | `YAML_AVAILABLE`; three branches; docstring clause; the `Any` import (its only use, the `self.config: Any` annotation, sat in the removed branch; mypy infers `Any` from `yaml.safe_load`). |

### EDIT G and EDIT H

- `comm/pairing.py`: the four-line comment citing `discover_all_devices` is now one line: "The timeout is coerced to int; range() below requires one."
- `CLAUDE.md`: rule 9 added to section 4, as `**Comments**:` followed by the rule text exactly as given in the change. Version history row 1.9 added.

[Return to Table of Contents](<#table of contents>)

---

## 4. Candidates Kept

| Candidate | Reference that kept it |
|---|---|
| `rpm_warning`, `rpm_danger` in `AppConfig`, `CONFIG_KEYS`, `DisplayConfig` and the two construction sites in `DisplayManager` (EDIT B, decision D3) | Kept on the operator's decision during the run. Decision D3 rests on the premise "ConfigStore preserves unknown keys, so existing files stay valid". That holds for `load` and `save`, but not for `ConfigStore.validate()`: `utils/config.py` reports every key outside `CONFIG_KEYS` as `unknown key`, and `main.py:371-380` then exits with status 1. Every `config.yaml` that `DisplayManager._save_config` has written contains both keys, and so does `config/config.example.yaml`. Removing the keys would therefore make `gtach --validate-config` fail on existing files, which is a behaviour change. They must stay together: if `DisplayConfig` lost them while `AppConfig` kept them, `_save_config` would overwrite a user's values with the defaults. |
| `SetupAction.EXIT_SETUP` | `display/touch.py:342` compares `action.name == "EXIT_SETUP"` (a lookup by string). |
| `PYGAME_AVAILABLE` in `display/splash.py` | Assigned to `SplashScreen._graphics_available` (`splash.py:129`), which is read in four places and reported in the status dict at `splash.py:716`. Removing the flag would need a non-subtractive substitution or a cascade into `_graphics_available`. It is now the constant `True` after the plain import. |
| `PYGAME_AVAILABLE` in `display/graphics/splash_graphics.py` | `if not PYGAME_AVAILABLE or surface is None:`. With the flag removed, mypy reports `return False` as unreachable, because `surface` is not `Optional`. Removing the guard would change behaviour for a `None` surface (an error log instead of a silent `False`). It is now the constant `True` after the plain import. |
| `TouchEventCoordinator.swipe_threshold` | Read through `getattr` at `display/touch.py:227-229` and `309-311` (prompt constraint). |
| `SetupStateCoordinator.update_animation` and its call site | Still advances `animation_time`, which `setup.py:484` and `setup.py:735` read. Only the `_update_control_visibility` call was removed. |
| `PerformanceMonitor.reset_metrics` (and its abstract method) | Called by `tests/test_performance_instrumentation.py` (lines 112, 158, 170, 222). The RULE searches `tests/` as well as `src/`. |
| `PerformanceMonitor.is_performance_acceptable` | Called by `get_performance_summary`. |
| `BluetoothSetupInterface.start_discovery(show_all_devices=...)`, `BluetoothPairing.discover_elm327_devices(show_all_devices=...)` | Prompt constraint (runs 2 and 4). |

[Return to Table of Contents](<#table of contents>)

---

## 5. Observed, Not Removed

These have no reader, or are now constant, but are outside the listed scope, or removing them would modify kept code. They are listed for later runs.

- `TouchEventCoordinator.display_center`: no reader.
- `TouchEventCoordinator._stats["gestures_recognized"]` and `["slider_interactions"]`: now always 0. They are kept because `get_stats()` returns them to `DisplayManager.get_performance_stats`.
- `PlatformDetector.clear_cache`: no caller since `clear_detection_cache` was removed. EDIT D extends removal only to private helpers.
- `MetricType` (`display/performance/interfaces.py`, exported): no reference anywhere.
- `PerformanceMonitor._render_operations`, `_operation_counts`, `_cache_stats`, `_memory_samples`: no longer written, but still read by `get_current_metrics`, `get_performance_summary`, `_get_current_memory_usage` and `reset_metrics`, so they are constant-empty. Removing them would change those readers and the `operation_counts` and `cache_details` keys of the summary.
- `DisplayConfig.rpm_warning`, `rpm_danger`: still written and not read by any rendering path (see section 4).

[Return to Table of Contents](<#table of contents>)

---

## 6. Tests

- **Added:** `tests/test_config_store.py::TestSave::test_retired_gesture_key_and_rpm_keys_survive`. It loads a file containing `rpm_warning`, `rpm_danger` (non-default values) and `gesture_swipe_threshold`, then saves. It asserts that no record at WARNING or above is logged and that all three keys and values survive the save. Because the rpm keys were kept, they round-trip as known keys and the gesture key as an unknown key.
- **Deleted:** none. No test imported a removed symbol.
- **Reduced:** none. The `update_animation` stub in `tests/test_setup_complete_hold.py` and the `SimpleNamespace(swipe_threshold=...)` doubles still match kept members.
- **Result:** `pytest tests/` gives 589 passed. `mypy src/` reports no issues.
- **Pre-existing flaky test:** `tests/test_pi_reset.py::TestDispatchIsOffThread::test_second_press_while_in_flight_is_ignored` failed in 2 of about 8 full-suite runs on the changed tree. It passed 25 of 25 runs of `test_pi_reset.py` alone, on both the baseline and the changed tree. Over 8 full-suite runs of the unchanged baseline in a separate worktree, it failed in 1 of 8, so it predates this change. The test counts live threads named `pi_reset`; `test_worker_is_a_daemon` releases its worker without waiting for it to exit, so a lingering worker can make the count 2. None of the files this change touches is involved. The test was not modified (subtractive scope).

[Return to Table of Contents](<#table of contents>)

---

## 7. Line Count

`wc -l` over `src/gtach`, excluding `__pycache__`:

| Scope | Before | After | Delta |
|---|---|---|---|
| All files (`*.py`, `default-config.txt`, `engine_profiles.yaml`, font) | 20430 | 19279 | −1151 |
| `*.py` only | 19938 | 18817 | −1121 |

`git diff --stat` for `src/`, `tests/` and `CLAUDE.md`: 23 files changed, 62 insertions, 1192 deletions.

[Return to Table of Contents](<#table of contents>)

---

## 8. Success Criteria

| Criterion | Result |
|---|---|
| No name listed for deletion remains in `src/`, except candidates reported as kept | Met. A whole-word search of `src/` and `tests/` for every removed name finds only the new test's `gesture_swipe_threshold` key and `SimBluetoothManager.discover_all_devices`, a different class. |
| `utils/default-config.txt` absent and unreferenced | Met. |
| No dead import fallback with a `TODO: issue-ac11505d` marker remains for pygame, yaml, `SplashConfig` or `TouchHandler` | Met. No `dead fallback` marker remains under `src/`. |
| `git diff` shows only deletions, the EDIT F imports, the EDIT G comment, the CLAUDE.md rule and test changes | Met, with the edits that the deletions forced: un-indenting the kept branch where a flag test was removed, dropping a flag from a compound condition, listing `"TouchHandler"` in `__all__`, collapsing `start_discovery(state)` onto one line, and `PYGAME_AVAILABLE = True` in two files (section 4). |
| `pytest tests/` passes; `mypy src/` clean | Met (section 6). |
| `TODO: issue-ac11505d` markers removed only where EDIT F or a deletion removes their line | Met. Thirteen markers were removed: eleven fallbacks, the `TouchAction.DRAG` line in `handle_touch_move`, and the manual-entry branch in `_render_screen`. |

[Return to Table of Contents](<#table of contents>)

---

## 9. Deviations and Notes for the Planner

1. **EDIT B partly not applied.** `rpm_warning` and `rpm_danger` were kept (section 4) on the operator's decision. Decision D3 and the change's `data_changes` entry should be revisited: removing the keys needs `validate()` to tolerate retired keys, or an accepted behaviour change for `--validate-config`. The traceability item "design-b4c5d6e7: remove rpm_warning and rpm_danger from the key list" does not apply yet.
2. **Write-only removal with a runtime side effect.** Removing `_update_metrics_history` stops a once-per-second `get_current_metrics()` call from `record_frame_end`. Its result was only appended to `_metrics_history`, which nothing reads. The call also refreshed the cached psutil reading, so the periodic log now reads RSS on demand. No output changes; per-frame work is reduced.
3. **Public names removed:**
   - `gtach.display.input.GestureType`;
   - `gtach.display.TOUCH_HANDLER_AVAILABLE`;
   - `TouchAction.MODE_CHANGE` and `SLIDER_INTERACTION`;
   - the `history_duration` parameter of `PerformanceMonitor`;
   - six `PerformanceMonitorInterface` methods;
   - three `TouchEventInterface` methods.

   No caller exists in the repository. `TouchEventInterface` is a backward-incompatible change, as the change document declares.
4. **Unlisted removals forced by a deletion:** the `_render_screen` `else` fallback (otherwise a `type: ignore` would have been needed), `_setup_touch_callbacks` (empty), and the `platform.py` `__main__` block (only caller of two deleted functions).
5. Device session A (proposal-71ab3751 section 7.0) remains outstanding for gauge, touch and setup behaviour.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial report for prompt-cfa4e617. |

---

Copyright (c) 2026 William Watson. MIT License.
