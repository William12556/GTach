Created: 2026 October 09

# Report: Monotonic Durations in Five Files

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Classification](<#2. classification>)
3. [Files Changed](<#3. files changed>)
4. [Tests and Result](<#4. tests and result>)
5. [Success Criteria](<#5. success criteria>)
6. [Deviations](<#6. deviations>)
7. [Items Kept](<#7. items kept>)
8. [On-Device Verification Outstanding](<#8. on-device verification outstanding>)
9. [Version History](<#version history>)

---

## 1. Summary

prompt-e215a184 (change-e215a184, issue-e215a184) is implemented. Each `time.time()` site in the five files was classified per variable or record field. Every variable whose reads are only differences or comparisons with the same clock now uses `time.monotonic()` at every assignment and read. Three sites keep `time.time()`: the dirty-region `timestamp`, as the prompt directs, and the reader that compares with it.

[Return to Table of Contents](<#table of contents>)

---

## 2. Classification

Line numbers are from the parent commit.

| File | Variable / field | Assigned | Read | Decision |
|---|---|---|---|---|
| `device_surfaces.py` | local `start_time` | 168 | 344 (`render_time` difference, threshold, log of ms) | monotonic |
| `circular_positioning.py` | local `start_time` in `validate_circular_bounds` | 66 | 104 (`duration` into stats totals/averages) | monotonic |
| `circular_positioning.py` | local `start_time` in `validate_all_layout_elements` | 287 | 309 (`total_time` → ms, rates) | monotonic |
| `engine.py` | local `start_time` in the buffer write | 742 | 890 (`write_time` → `_stats` render times) | monotonic |
| `monitor.py` | `_start_time` | 101 | 133 (`stop_monitoring` duration, avg FPS), 590 (`monitoring_duration`) | monotonic |
| `monitor.py` | `_active_frames` values (`current_time` in `record_frame_start`) | 165–167 | 175 (cutoff comparison, same local), 209 (`frame_time` difference) | monotonic |
| `monitor.py` | `current_time` in `record_frame_end` → frame-history `timestamp`, `_last_metrics_update` | 203, 215, 230 | 209 (difference with `_active_frames`), 228 (comparison), 445 (`_calculate_current_fps`) | monotonic, so `_calculate_current_fps` `current_time` (443) is monotonic too |
| `monitor.py` | `_last_metrics_update` | 230 | 228 | monotonic |
| `monitor.py` | memory-history `timestamp` (`update_memory_usage`) | 307–309 | none (only `[-1]["usage_mb"]` is read) | monotonic. No reader, so no wall-clock interpretation; it now matches the other history fields. |
| `monitor.py` | `PerformanceMetrics.last_update_time` (`get_current_metrics`) | 316, 346 | 363 (`get_historical_metrics` cutoff, `current_time` at 357); `to_dict()` in `get_performance_summary` and `DisplayManager.get_performance_stats` | monotonic, with 357. `get_performance_stats` has no caller, and nothing formats, logs or persists the field as a time. |
| `monitor.py` | `_memory_cache_ts` | 486, 495 | 488–489 (truthiness, then age comparison) | monotonic; the comment "time.time() of that reading" now says `time.monotonic()`. |
| `monitor.py` | dirty-region `timestamp` | 539 | 564 (age against `current_time` at 558) | **wall-clock (kept)**, as the prompt directs. Its reader at 558 also keeps `time.time()`, so the two clocks are never mixed. |
| `platform.py` | `_last_detection_time` and the `current_time` locals | 144 (from `current_time` at 124); reset to 0 at 761 | 130, 506 (cache-age comparisons with `current_time` at 124 / 500), 735 (`cache_age_seconds`), 733 (`cache_info.last_detection_time`) | monotonic. See below. |

**`last_detection_time` consumers.** The only consumer of `get_platform_info()` outside `platform.py` is `create_touch_interface` in `touch_interface.py`, which stores the dict in a local `platform_info["additional_info"]` that is never read or logged. Inside `platform.py`, `log_platform_info` logs only `cache_age_seconds`, a difference. No consumer interprets the value as an epoch time, so it was switched.

**Remaining `time.time()` in the five files:** `monitor.py` dirty-region `timestamp` (542 after the change) and `get_dirty_regions` `current_time` (561). Both are wall-clock, as above.

[Return to Table of Contents](<#table of contents>)

---

## 3. Files Changed

| File | Change |
|---|---|
| `src/gtach/display/setup_components/rendering/device_surfaces.py` | 2 sites → monotonic. |
| `src/gtach/display/setup_components/layout/circular_positioning.py` | 4 sites → monotonic. |
| `src/gtach/display/rendering/engine.py` | 2 sites → monotonic. |
| `src/gtach/display/performance/monitor.py` | 10 sites → monotonic; block comment at the `__init__` state; `_memory_cache_ts` comment corrected. |
| `src/gtach/utils/platform.py` | 3 sites → monotonic; comment at `_last_detection_time`. |
| `tests/test_monotonic_durations.py` | New: 2 regression tests. |
| `tests/test_performance_instrumentation.py` | The `clock` fixture's fake `time` namespace gains `monotonic` (see Deviations). |

[Return to Table of Contents](<#table of contents>)

---

## 4. Tests and Result

- `test_platform_cache_survives_a_forward_step`: wall clock +3600 s; the second `get_platform_type()` returns the cached value and `_run_all_detections` ran once.
- `test_monitor_uptime_survives_a_backward_step`: wall clock −3600 s; `monitoring_duration` is in [0, 5).
- Both fail against the parent commit's source and pass after the change.
- Before: 559 passed. After: 561 passed.
- mypy error count unchanged (329).

[Return to Table of Contents](<#table of contents>)

---

## 5. Success Criteria

| Criterion | Result |
|---|---|
| Classification table; every remaining `time.time()` justified | Met |
| Two regression tests pass | Met |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 6. Deviations

- **`tests/test_performance_instrumentation.py`** is not in the prompt's file list. Its `clock` fixture replaced the monitor module's `time` with a namespace offering only `time`. After the switch, 7 tests in that file failed with `AttributeError`. The fixture now offers the same settable clock as both `time` and `monotonic`; no assertion changed. This is the minimal test-double adjustment the change requires.
- **Comments.** The prompt asks for a comment at each switched variable's initialisation. In `monitor.py` one block comment at the top of the `__init__` state covers `_start_time`, `_active_frames`, `_last_metrics_update` and the history records. Local start/end pairs carry an inline comment at the start assignment.

[Return to Table of Contents](<#table of contents>)

---

## 7. Items Kept

- `monitor.py` dirty-region `timestamp` and its reader stay `time.time()`, per the prompt.
- `PerformanceMetrics.last_update_time` in `interfaces.py` (default 0.0) is out of scope and unchanged.
- **Behaviour note, `platform.py`.** `_last_detection_time` uses 0 to mean "never detected". With `time.time()`, a capabilities result computed before any platform-type detection was never treated as cached. With `time.monotonic()`, which counts from boot on Linux, it is treated as cached during the first 300 s of uptime. The platform-type cache is unaffected, because it also checks `_platform_type is not None`. The capabilities case returns the result that was itself just computed, so the effect is benign; it is recorded here for review.

[Return to Table of Contents](<#table of contents>)

---

## 8. On-Device Verification Outstanding

- On the Pi after a cold boot (NTP step): the periodic "Performance: … FPS, … ms frame, … MB mem" lines in `debug.log` (run with `--debug`) show plausible FPS (≈ target) and frame times across the NTP correction, with no spike or zero.
- `log_platform_info` "Cache Age" is a small positive number.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-e215a184. |

---

Copyright (c) 2026 William Watson. MIT License.
