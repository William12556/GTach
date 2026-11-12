Created: 2026 November 12

# Report: Engine Off Display State

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [EDIT A: Silent-Vehicle Evidence and Re-check](<#2. edit a: silent-vehicle evidence and re-check>)
3. [EDIT B: Engine Off Condition and Screen](<#3. edit b: engine off condition and screen>)
4. [EDIT C: Wiring](<#4. edit c: wiring>)
5. [Measurements](<#5. measurements>)
6. [Tests](<#6. tests>)
7. [Deviations and Notes for the Planner](<#7. deviations and notes for the planner>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-b29cbd71 (change-b29cbd71, issue-b29cbd71) was implemented in one commit on branch `claude/gracious-mayer-men0zg`. EDITS A to C were applied. The prompt T-Doc was closed and moved to `ai/workspace/prompt/closed/`. The issue and change T-Docs remain active, pending the device check.

- pytest `tests/`: 766 passed, 1 xfailed (the existing `DEVICE_NOT_SAVED_TEXT` xfail).
- mypy `src/`: no issues in 60 source files.
- flake8, black and isort: no findings in the four touched Python files.
- Changed files: `src/gtach/comm/obd.py`, `src/gtach/display/manager.py`, `src/gtach/app.py`, `tests/test_engine_off_state.py` (new), the closed prompt and this report.

[Return to Table of Contents](<#table of contents>)

---

## 2. EDIT A: Silent-Vehicle Evidence and Re-check

`src/gtach/comm/obd.py`:

- **Constant.** `_RPM_SILENT_RECHECK_S: float = 2.0`.
- **State.** `self._vehicle_silent_ts: Optional[float] = None`, set in `__init__`. `_vehicle_silent` is unchanged and keeps its logging role.
- **Accessor.** `last_vehicle_silent_ts() -> Optional[float]` returns the attribute. The docstring is the one in design-e5f6a7b8 section 6.3.2.
- **Classification.** The new helper `_classify_0100(response) -> bool` contains the 4100 test that was previously inline in `_initialize_protocol`, and adds the evidence rule:
  - A reply containing `4100` clears the timestamp and returns True.
  - A non-None reply without `4100` sets the timestamp to `time.monotonic()`, calls `_report_no_vehicle` and returns False.
  - A reply of `None` calls `_report_no_vehicle` only and returns False. The timestamp is not touched.
- **Initialisation.** `_initialize_protocol` keeps the issue-146491ba lost-link branch ahead of the helper. That branch now also clears the timestamp. The ATZ, settle and AT command sequence is unchanged.
- **Clearing.** The timestamp is cleared in the following cases:
  - by a valid 010C sample;
  - in the outer loop's not-connected branch;
  - after the polling loop exits, beside the existing `_adapter_initialised = False`;
  - in `_signal_stop`;
  - in the lost-link branch of the re-check.
- **Polling.** The polling loop records `last_sample_ts`. Its start counts as a sample, and every valid sample refreshes it. When an RPM request returns no sample, `_RPM_SILENT_RECHECK_S` has elapsed and the transport is connected, the loop does the following:
  1. It logs INFO `No RPM data for 2.0s - re-checking vehicle`.
  2. It calls `_recheck_vehicle()`.
  3. On True, it resets `last_sample_ts` and resumes polling. On False, it leaves the polling loop.
- **Re-check.** `_recheck_vehicle() -> bool` loops while the transport is connected and no stop has been requested:
  1. It sends `0100` with `_INIT_0100_TIMEOUT_S`.
  2. If the reply is None and the transport is down, it clears the timestamp and returns False.
  3. If `_classify_0100` reports 4100, it resets `_vehicle_silent` and `_no_vehicle_logged_at` (as the initialisation path does), logs INFO `Vehicle answered 0100 - polling resumed` and returns True.
  4. Otherwise it waits `_INIT_RETRY_DELAY_S` through `wait_for_event`, with a heartbeat before and after the wait. A stop during the wait returns False.

  The re-check sends no ATZ and no AT command, applies no settle delay and does not change `_adapter_initialised`.

[Return to Table of Contents](<#table of contents>)

---

## 3. EDIT B: Engine Off Condition and Screen

`src/gtach/display/manager.py`:

- **Constants.** The class constants are `ENGINE_OFF_FRESHNESS_S = 15.0` and `ENGINE_OFF_TEXT = "Engine off"`.
- **Attributes.** `_vehicle_silent_callback` and `_frame_engine_off = False` are assigned near the top of `__init__`, before any step that can fail.
- **Condition.** `_engine_off() -> bool` implements design-b8c9d0e1 section 5.4.1. It returns False in any of these cases:
  - simulation mode is on;
  - `_frame_link_lost` is False;
  - either callback is absent;
  - the link callback does not return exactly `True`;
  - the silent callback does not return a `float`;
  - the timestamp is older than `ENGINE_OFF_FRESHNESS_S`;
  - any exception is raised.

  The age comparison is `<=`, so a timestamp exactly 15.0 s old still counts.
- **Per frame.** `_display_loop` calls `self._set_frame_engine_off(self._engine_off())` immediately after `_frame_link_lost` is evaluated. The new helper `_set_frame_engine_off` stores the value and acts on a transition:
  - On entry, it resets `_last_rpm = 0`, `_rpm_display = 0.0`, `_rpm_last_ts = None` and `_active_band = 0`, and logs INFO `Engine off - adapter reports no vehicle`.
  - On exit, it logs INFO `Engine off cleared`.
- **Precedence.** `_render_normal_modes` and `_register_view_regions` use `_frame_link_lost and not _frame_engine_off` (with the existing RADIAL gate). `_draw_status_indicator` shows `CONNECTING` (yellow) when `_frame_engine_off` is True, checked ahead of `_frame_link_lost`. `_current_view_key()` appends `_frame_engine_off`, and its docstring lists the new member.
- **Screen.** When engine off is set, `_draw_radial_mode` behaves as follows:
  - It uses an RPM of 0.0, so it neither reads `_last_rpm` nor calls `_condition_rpm`.
  - It draws the gauge as usual at zero, with band 0 and no indicator line, because the existing `rpm > 0` test suppresses the line.
  - It draws `ENGINE_OFF_TEXT` in white at the centre, in `get_font_manager().get_font(TypographyConstants.FONT_RPM_MEDIUM)`.
  - It skips the numeric readout.
- **Regions.** RADIAL registers no regions, so none are registered for the engine-off view.

[Return to Table of Contents](<#table of contents>)

---

## 4. EDIT C: Wiring

`src/gtach/app.py`: `_start_setup_mode` and `_start_normal_mode` each set the following, directly after `_link_cause_callback`:

```python
self._display._vehicle_silent_callback = lambda: (
    self._obd.last_vehicle_silent_ts()
    if getattr(self, "_obd", None) is not None
    else None
)
```

[Return to Table of Contents](<#table of contents>)

---

## 5. Measurements

**ENGINE_OFF_TEXT width.** The text measures **177 px** in Michroma-Regular at `FONT_RPM_MEDIUM` = 28 px, which is within the 180 px limit. Measurements used pygame 2.6.1 / SDL 2.28.4 with `SDL_VIDEODRIVER=dummy`. The candidate sizes were:

| Size (px) | Width (px) |
|---|---|
| 24 | 152 |
| 28 | 177 |
| 32 | 202 |

**Mid-drive gap.** In `test_mid_drive_gap`, the first silent timestamp came **2.006 s** after the last valid sample. That test uses the production constants (`_RPM_SILENT_RECHECK_S` 2.0, poll interval 0.05 s) and a stub transport that answers immediately. The gap is therefore the re-check threshold plus one poll cycle. On a vehicle, the time for the adapter's 0100 reply adds to this; it is bounded at about 6 s. `LINK_LOSS_TIMEOUT` is also 2.0 s, so with an immediate adapter reply DISCONNECTED would show for at most a frame or two before Engine off. The device check should confirm this.

[Return to Table of Contents](<#table of contents>)

---

## 6. Tests

`tests/test_engine_off_state.py` contains 33 tests. All of them pass.

- **Initialisation evidence.** The cases are:
  - `NO DATA` sets the timestamp.
  - `SEARCHING...UNABLE TO CONNECT`, `BUS INIT: ...ERROR` and `?` each set it.
  - `None` with the link up leaves it None, does not refresh an existing value, and still logs the WARNING.
  - `None` with the link down clears it, and the issue-146491ba assertions still hold.
  - `4100` after a silent reply clears it.
  - `_signal_stop` clears it.
- **Polling.** These tests run the threaded `_protocol_loop` with shortened intervals. They check the following:
  - The re-check sends `0100` and no `AT*` command after the first `010C`, logs one INFO record, sets the timestamp and leaves `_adapter_initialised` True.
  - A 4100 reply in the re-check resumes 010C polling and clears the timestamp, with only one ATZ in total.
  - Timeouts during polling and the re-check never set the timestamp.
  - A valid sample clears the timestamp.
  - A disconnect during the re-check wait clears the timestamp and stops the re-check.
  - A stop during a 30 s re-check wait ends the thread in under 2 s.
  - The mid-drive gap is measured with the production intervals.
- **Display.** These tests use a real `DisplayManager` with injected callbacks. They check the following:
  - Fresh evidence gives Engine off, no DISCONNECTED render, a yellow dot, `ENGINE_OFF_TEXT` drawn and no RPM readout.
  - A 16 s old timestamp gives DISCONNECTED.
  - A timestamp exactly 15.0 s old gives True.
  - The transport callback False, None, raising or absent each give False.
  - The silent callback None, raising, absent or a non-float value each give False.
  - Simulation mode gives False.
  - With the link up, the live readout is drawn.
  - Entry after a 4500 RPM reading resets the conditioning state and logs one INFO record.
  - Exit is logged.
  - The view key changes on entry, and the DISCONNECTED regions are cleared.
- **Text fit.** A test checks the `ENGINE_OFF_TEXT` width.

The regression scope (the full `tests/` suite) passes. The suite includes `test_session_b_findings.py`, the link-loss tests and the RPM conditioning tests.

[Return to Table of Contents](<#table of contents>)

---

## 7. Deviations and Notes for the Planner

1. **Location of the entry and exit handling.** The prompt places the reset and the INFO records in `_draw_radial_mode`. They are in `_set_frame_engine_off`, which `_display_loop` calls once per frame. `_draw_radial_mode` does not run when engine off ends by falling back to DISCONNECTED, or while OPTIONS is shown, so in that location the exit record would be missed and the logs would not pair. As a consequence, the reset also happens when engine off begins while OPTIONS is shown. The reset is harmless there.
2. **Re-check lost-link branch.** The change states the issue-146491ba branch for `_initialize_protocol` only. `_recheck_vehicle` applies the same rule: a None reply with the transport down clears the timestamp and logs no WARNING. This follows the fourth row of design-e5f6a7b8 section 6.3.1.
3. **Rate limit after a re-check.** When the re-check receives 4100, it resets `_vehicle_silent` and `_no_vehicle_logged_at`, as the initialisation path already does. The change does not state this explicitly. Without the reset, the A05 rate limit would carry over across a resumed drive.
4. **`getattr` in `_draw_radial_mode`.** `_draw_radial_mode` reads the flag as `getattr(self, "_frame_engine_off", False)`. Two existing tests in `test_rpm_signal_conditioning.py` construct `DisplayManager` without `__init__`. The method already reads `_last_rpm` through `getattr` for the same reason.
5. **Font.** The text uses the existing `TypographyConstants.FONT_RPM_MEDIUM` (28 px, "Gauge mode center readout") rather than a new constant.
6. **Mode independence.** As specified in design-b8c9d0e1 section 5.4.1, `_engine_off()` does not test `config.mode`. The yellow dot therefore also shows while OPTIONS is open and the engine is off. Previously the dot was red in that case.
7. **Observation, not addressed.** Consider a vehicle that answers 0100 with 4100 but never gives a valid 010C sample. For example, the vehicle might not support PID 0C. Polling would then re-check about every 2 s, with two INFO records per cycle, indefinitely. This case is outside the change's scope. Confidence that it occurs on real vehicles is low.
8. **Environment.** No `venv/` was present, so the checks ran on system Python 3.13 after `pip install -e .[dev]`. mypy was run as `python -m mypy src/` with `types-PyYAML`, `types-psutil` and `types-pyserial` installed. Without those stubs, both the base commit and this change show the same 20 environment-only errors. Black and flake8 findings in untouched files (16 files and 460 lines respectively) are identical before and after this change.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial report for prompt-b29cbd71. |

---

Copyright (c) 2026 William Watson. MIT License.
