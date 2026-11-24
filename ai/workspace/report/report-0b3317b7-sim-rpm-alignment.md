Created: 2026 November 24

# Report: Simulation RPM Alignment — Implementation of prompt-0b3317b7

---

## Table of Contents

- [1. Summary](<#1. summary>)
- [2. What Was Changed](<#2. what was changed>)
- [3. Changed Test Assertions](<#3. changed test assertions>)
- [4. Testing](<#4. testing>)
- [5. Deviations and Observations](<#5. deviations and observations>)
- [6. T-Doc Disposition](<#6. t-doc disposition>)
- [7. Version History](<#7. version history>)

---

## 1. Summary

`prompt-0b3317b7-sim-rpm-alignment.md` was implemented: C1–C5 of
`change-0b3317b7`. A single module-level function
`gtach.comm.sim_transport.sim_rpm(t)` now defines the synthetic sweep,
800 + 2900 · (1 + sin(t · 2π / 15)), i.e. 800–6600 RPM with a 15 s period.
`SimTransport` and the `DisplayManager` OPTIONS simulation mode both call
it with a monotonic time base. No `time.time()` remains in either sweep
path.

- `SDL_VIDEODRIVER=dummy pytest tests/`: **874 passed**, 0 failed.
- `mypy src/`: `Success: no issues found in 60 source files` (same as the
  unmodified tree).
- `black --check`, `isort --check-only`, `flake8` on the changed files:
  clean.

**Not verified on target.** The device check on `gtach.local` (simtcp
startup and OPTIONS simulation mode both sweep 800–6600 RPM in about 15 s)
remains outstanding.

---

## 2. What Was Changed

| Item | File | Change |
|---|---|---|
| C1 | `src/gtach/comm/sim_transport.py` | Added module constants `SIM_RPM_MIN = 800`, `SIM_RPM_MAX = 6600`, `SIM_RPM_PERIOD_S = 15.0` and `sim_rpm(t: float) -> float`, returning `SIM_RPM_MIN + (SIM_RPM_MAX - SIM_RPM_MIN) / 2 * (1 + math.sin(t * 2 * math.pi / SIM_RPM_PERIOD_S))` (the half span is held in a local `half_span`). Google-style docstring citing change-0b3317b7. |
| C2 | `src/gtach/comm/sim_transport.py` | `_compute_rpm_response`: `rpm = sim_rpm(time.monotonic() - self._start_time)`; the 010C encoding is unchanged. Class docstring, `_handle_command` comment and `_compute_rpm_response` comment updated to 800–6600 RPM, 15 s period, start at the 3700 RPM midpoint. |
| C3 | `src/gtach/display/manager.py` | `_draw_radial_mode`, simulation branch: function-local `from ..comm.sim_transport import sim_rpm`, then `rpm = int(sim_rpm(time.monotonic()))`. `self._last_rpm = rpm` and `rpm = self._condition_rpm(rpm)` unchanged. No module-level `gtach.comm` import added. Engine-off, disconnected and live paths unchanged. |
| C4 | `tests/test_sim_transport.py` | `test_rpm_sweep_uses_monotonic_clock` and `test_rpm_sweep_ignores_wall_clock_steps` updated (section 3). t = 15 s is not used. |
| C5 | `tests/test_sim_transport.py` | Added `test_sim_rpm_values` (t = 0, 3.75, 11.25 s → 3700, 6600, 800 within 1e-6), `test_sim_rpm_range_over_one_period` (1000 samples over one period within [800, 6600]) and `test_sim_rpm_is_periodic` (sim_rpm(t) == sim_rpm(t + 15) within 1e-6 at five points). Module docstring now names 0b3317b7. |

`math` remains imported in `manager.py`; it is still used elsewhere in the
module.

---

## 3. Changed Test Assertions

| Test | Old | New |
|---|---|---|
| `test_sim_transport.py::test_rpm_sweep_uses_monotonic_clock` | `"41 0C 39 08"` (3650 RPM) | `"41 0C 39 D0"` (3700 RPM) |
| `test_sim_transport.py::test_rpm_sweep_ignores_wall_clock_steps` — second monotonic value | `1015.0` (t = 15 s) | `1003.75` (t = 3.75 s) |
| `test_sim_transport.py::test_rpm_sweep_ignores_wall_clock_steps` | `"41 0C 65 90"` (6500 RPM) | `"41 0C 67 20"` (6600 RPM) |
| `test_rpm_signal_conditioning.py::TestRawValueRetained::test_sim_mode_records_raw_then_conditions` | `host._last_rpm == 3000` | `host._last_rpm == 3700` |
| same test | `0.0 < host._rpm_display < 3000.0` | `0.0 < host._rpm_display < 3700.0` |

No unrelated assertion was changed or weakened.

---

## 4. Testing

Environment: fresh `venv`, `pip install -e .[dev]`, Python 3.13, pygame
2.6.1, `SDL_VIDEODRIVER=dummy`.

- Full suite: `874 passed in 64.77s`. Before the update of
  `test_rpm_signal_conditioning.py` (section 5), the run was 873 passed,
  1 failed (TC-015, asserting 3000).
- `tests/test_sim_transport.py`: 15 passed (4 existing drop_link tests,
  2 updated sweep tests, 9 new parametrised `sim_rpm` cases).
- Regression scope from the change document (`test_lifecycle_sim.py`,
  `test_rpm_signal_conditioning.py`, `test_connecting_indicator.py`,
  `test_engine_off_state.py`, `test_monotonic_durations.py`): all pass
  within the full run.
- `mypy src/`: no issues. `black`, `isort`, `flake8`: clean on
  `sim_transport.py`, `manager.py`, `test_sim_transport.py`.

---

## 5. Deviations and Observations

1. **Fourth file touched.** `tests/test_rpm_signal_conditioning.py`
   (TC-015) asserted the old OPTIONS formula's value at t = 0
   (`3000 + 3000·sin(0) = 3000`). Its `clock` fixture patches both
   `time.monotonic` and `time.time`, so under C3 the sample is
   `sim_rpm(0) = 3700`. The change document lists this file only under
   `regression_scope`, and the prompt's success criterion limits the diff
   to three source/test files. To satisfy the `pytest tests/ passes`
   criterion, the two assertions and their comment were updated from 3000
   to 3700 (section 3); the test's intent (raw sample stored, conditioned
   value lags below it) is unchanged. The planner should confirm or revert
   this during review.
2. **isort formatting.** `isort` inserted a blank line between
   `import types` and `import gtach.comm.sim_transport as sim_module` in the
   two existing sweep tests. Formatting only.
3. **Float exactness.** `sim_rpm(3.75)` evaluates to exactly 6600.0 on
   CPython, so `int(rpm * 4)` encodes `67 20` without truncation to `67 1F`;
   the test confirms this on the build host's platform.
4. **No `time.time()` in either sweep path.** The one remaining
   `time.time()` in `manager.py` (line 2940) is an unrelated timestamp.

---

## 6. T-Doc Disposition

| T-Doc | Action |
|---|---|
| `prompt-0b3317b7-sim-rpm-alignment.md` | Moved to `ai/workspace/prompt/closed/`. |
| `change-0b3317b7-sim-rpm-alignment.md` | Status `proposed` → `implemented`; remains active pending device test. |
| `issue-0b3317b7-sim-rpm-alignment.md` | Status `open` → `resolved`; remains active pending device test. |

Outstanding (owners per change-0b3317b7): planner review of the pull
request; device check on `gtach.local`; update of design-7d3e9f5a to name
`sim_rpm`.

---

## 7. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-24 | Initial report |

---

Copyright (c) 2026 William Watson. MIT License.
