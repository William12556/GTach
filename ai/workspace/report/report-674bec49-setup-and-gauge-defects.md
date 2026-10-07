Created: 2026 October 07

# Report: Setup Lifecycle, Gauge Range, Cached Device Presence, Persistent Errors

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests Added and Result](<#3. tests added and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [On-Device Verification Outstanding](<#6. on-device verification outstanding>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-674bec49 (change-674bec49, issue-674bec49; audit-36b6ea95 C01, C05, C06 and C08) was implemented in commit `5ea2cfd77665ae7fec7e7749f2d6e499136fee7a`.

- **EDIT A:** `stop_setup` never joins the current thread.
  - `_on_setup_complete` stops the active setup manager before `exit_setup_mode`.
  - `_start_setup_mode` stops any previous manager before constructing a new one. Re-entry from DISCONNECTED goes through this path.
  - Cancel on WELCOME reaches `_on_setup_complete` through the COMPLETE state.
- **EDIT B:** the new `DisplayManager._gauge_max_rpm()` returns `min(9000, max(7000, ceil((redline + 500) / 1000) * 1000))`, with a 6000 fallback.
  - `_draw_radial_mode` uses it for the clamp, the sweep scale and the tick loop.
  - With redline 6000 the result is 7000, and the ticks run 1000 to 7000 as before.
- **EDIT C:** `_has_device` is cached. It is refreshed by `_refresh_has_device()` at `start_setup` and on every entry to WELCOME. Neither WELCOME rendering nor cached-region updates construct a DeviceStore.
- **EDIT D:** setup error messages persist until the next tap:
  - DEVICE_LIST no longer clears `error_message` while rendering;
  - `handle_touch_event` clears it after releasing `_touch_regions_lock` and before dispatch;
  - WELCOME renders the message's own text, fitted to 400 px by `_fit_text`.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/display/setup.py` | EDIT A(1) (`stop_setup` guard); EDIT C (`_has_device`, `_refresh_has_device`, `start_setup`, `_on_screen_transition`, `_render_welcome_screen`, `_update_cached_screen_touch_regions`); EDIT D (`_fit_text`, `_render_device_list_screen`, `handle_touch_event`, WELCOME error text). |
| `src/gtach/app.py` | EDIT A(2) `_on_setup_complete`; EDIT A(3) `_start_setup_mode`. |
| `src/gtach/display/manager.py` | EDIT B: `_gauge_max_rpm`; `_draw_radial_mode` clamp, `max_rpm` and tick loop (the redundant `if rpm_tick <= max_rpm` removed and its body dedented); two comments updated. |
| `tests/test_setup_and_gauge.py` | New: 17 tests. |
| `tests/test_setup_lock_order.py` | The `_manager` helper sets `_has_device = False` (see Deviations). |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_setup_and_gauge.py` has 17 tests, covering every prompt scenario and the edge case:

- **`stop_setup`:**
  - called from the setup thread itself → no exception, and the thread finishes;
  - called twice with a finished thread → no exception.
- **Application:**
  - `_on_setup_complete` twice → stop once, before `exit_setup_mode`, then `_start_obd` once;
  - `_start_setup_mode` → the old manager is stopped before the new one is constructed.
- **`_gauge_max_rpm`:**
  - redline 6000/7000/7500/8500/9000/12000 → 7000/8000/8000/9000/9000/9000;
  - missing `config` or `rpm_bands` → 7000.
- **Cached presence:**
  - with DeviceStore patched to raise on construction, cached regions are two buttons and then one;
  - DISCOVERY → WELCOME refreshes the flag once.
- **Errors:**
  - a DEVICE_LIST render keeps 'OBD check failed';
  - a tap clears the error before `_handle_touch_action` runs.
- **`_fit_text`** (production small label font): 'Device not available' is unchanged; the long no-devices message becomes 'No devices found.'; both are at most 400 px.

16 of the 17 tests fail on the pre-change code.

pytest after this commit: 372 passed (355 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| `stop_setup` guards against joining the current thread | Code review; `test_stop_from_the_setup_thread_does_not_join_itself` | Pass |
| `_on_setup_complete` and `_start_setup_mode` stop an existing setup manager | `TestApplicationStopsSetupManager` | Pass |
| 'min(7000' and 'max_rpm = 7000' absent from manager.py; `_gauge_max_rpm` exists | `grep` returns nothing; `TestGaugeMaxRpm` | Pass |
| `_update_cached_screen_touch_regions` and `_render_welcome_screen` construct no DeviceStore | AST: neither function body names DeviceStore | Pass |
| `_render_device_list_screen` no longer clears `error_message` | AST; `test_device_list_render_keeps_error` | Pass |
| The fixed 'No devices found' string is no longer used for `error_message` on WELCOME | Code review: WELCOME renders `_fit_text(font_small, state.error_message)`; the remaining 'No devices found' literal is the DEVICE_LIST empty-list placeholder | Pass |
| `pytest tests/` passes | Full run | 372 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- `tests/test_setup_lock_order.py` was changed even though the prompt does not list it: its `_manager` helper now sets `_has_device = False`.
  - Without the attribute, the cached WELCOME path in the lock-order stress test raised AttributeError.
  - render caught and logged the error, so the test still passed, but the path it exercises was cut short.
  - No assertion was changed.
- The redundant `if rpm_tick <= max_rpm` guard was dropped, as the prompt allows when behaviour is identical. That required dedenting the tick-loop body by one level.
- `_gauge_max_rpm` catches only a missing attribute path. A non-numeric `redline_rpm` would still raise, inside `_draw_radial_mode`'s existing handler.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

On the Pi:

1. The gauge looks unchanged with the current profile (abarth_595_turismo, redline 6000).
2. After Cancel on WELCOME, and after DISCONNECTED → Setup, `stacks.log` (debug on) shows at most one SetupManager thread.
3. A failed Continue probe shows 'Device not available' on WELCOME until the next tap.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-674bec49. |

---

Copyright (c) 2026 William Watson. MIT License.
