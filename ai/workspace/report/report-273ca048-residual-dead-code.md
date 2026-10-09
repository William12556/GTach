Created: 2026 October 09

# Report: Residual Dead Code Removed

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests and Result](<#3. tests and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [Items Kept](<#6. items kept>)
7. [On-Device Verification Outstanding](<#7. on-device verification outstanding>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-273ca048 (change-273ca048, issue-273ca048) is implemented. Groups D1 to D8 were removed in the order D7, D5, D4, D1, D3, D2, D6, D8. Before each group, `src/`, `tests/` and `bin/` were searched for each name, including string forms (`hasattr`/`getattr`, `__all__`) and iteration over `SetupScreen`. Every item was referenced only by its own definition or export, or by other items in the same group. `pytest tests/` passed after each group (559 passed each time). Nothing was kept.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| Group | File | Removed |
|---|---|---|
| D7 | `tests/conftest.py` | `ACQUIRE_TIMEOUT` and its comment. |
| D5 | `src/gtach/display/performance/__init__.py` | `initialize_performance_manager`, `cleanup_performance_manager` and their `__all__` entries. |
| D4 | `src/gtach/display/typography.py` | `ButtonSize`, `ButtonState`. |
| D1 | `src/gtach/display/touch.py` | `TouchHandler.get_touch_interface_info`. |
| D3 | `src/gtach/display/touch_interface.py` | `MockHyperPixelTouch.simulate_touch`, `HyperPixelTouchInterface.simulate_touch_event`, the "Use simulate_touch_event()" log line, `normalize_coordinates`, `denormalize_coordinates`. The internal `hasattr(..., "simulate_touch")` reference was inside `simulate_touch_event`. |
| D2 | `src/gtach/display/setup_components/layout/circular_positioning.py` | `get_circular_safe_area`, `clear_layout_cache`, and `_circular_layout_cache` (only assigned in `__init__` once `clear_layout_cache` was gone). |
| D6 | `src/gtach/display/splash.py` | `SplashScreen.get_performance_report`, including the unreachable trim branch. No attribute was used only by it: `_font_render_times`, `_total_render_time`, `_cached_fonts` and `_typography_available` are also read by `get_info` and the render path. |
| D8 | `src/gtach/display/setup_models.py`, `src/gtach/display/setup.py` | `SetupScreen.DEVICE_MANAGEMENT`, `SetupScreen.CONFIRMATION` (the last two members, so no `auto()` value shifts); the `CONFIRMATION` entry in the `should_cache` list. |

No test was deleted or adjusted.

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Result

- `pytest tests/`: 559 passed before and after every group.
- The success-criterion grep over `src`, `tests` and `bin` returns nothing.
- `python -c 'import gtach.app, gtach.main'` succeeds.
- `SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 python -m gtach --transport simtcp` ran until the timeout (exit 124) with no ImportError or AttributeError. Its only traceback is `OSError: [Errno 25] Inappropriate ioctl for device` from `RenderingEngine._query_framebuffer_geometry`, which is logged and handled. The run without this change produces the same 20 lines, so this is the container lacking a framebuffer, not a regression.
- mypy: 338 → 329 errors (38 files), because the removed code no longer counts.

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| Grep for removed names returns nothing | Met |
| Import and 8 s simtcp smoke run clean | Met (framebuffer ioctl traceback is environmental and pre-existing) |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- One blank line was removed in `touch_interface.py` after the `simulate_touch` deletion; otherwise flake8 reports E303.

[Return to Table of Contents](<#table of contents>)

---

## 6. Items Kept

Further dead code found and **not** removed, per "remove nothing beyond D1-D8":

- `_global_performance_manager` in `display/performance/__init__.py`, and its "Legacy compatibility functions" comment, now unused.
- `CircularPositioningEngine._cache_lock`, now created but never acquired.
- `TouchInterface.get_info`, `HyperPixelTouchInterface.get_info` and `MockTouchInterface.get_info` in `touch_interface.py`. Their only external caller was `get_touch_interface_info` (D1); they now call only each other through `super()`.
- `SplashScreen.get_info` in `splash.py`, which has no caller.
- The `simulated_taps` stat in `touch_interface.py`, which is never incremented now that `simulate_touch_event` is gone. It is still printed by a reachable log line, so removing it would change output.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification Outstanding

- Normal use on the Pi: boot splash, setup flow (welcome → discovery → device list → pairing → complete / current device), touch and swipe input, and the gauge display.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-273ca048. |

---

Copyright (c) 2026 William Watson. MIT License.
