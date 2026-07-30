Created: 2026 July 30

# Test: RPM Signal Conditioning

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-4c038bed"
  title: "Unit tests for EMA smoothing, band hysteresis, frame-counter flash phase and the blue-band text colour"
  date: "2026-07-30"
  author: "William Watson"
  status: "planned"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-4c038bed"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "DisplayManager._condition_rpm; DisplayManager._get_band_colour; DisplayManager._get_shift_cue"
  design_refs: []
  change_refs:
    - "change-4c038bed"
  requirement_refs:
    - "display-ui-graphics-review.md §4.2"
    - "display-ui-graphics-review.md §4.3"
    - "display-ui-graphics-review.md §4.4"
    - "display-ui-graphics-review.md §7.1"
    - "display-ui-graphics-review.md §9.1 recommendations 1 and 5; §9.5 recommendation 23"

scope:
  description: >
    Verifies that a steady RPM produces a steady picture: the displayed
    figure is exponentially smoothed, band selection is sticky within a
    hysteresis margin, the shift-cue flash has an equal duty cycle derived
    from the frame counter, and the torque-approach band renders white on
    blue. Also verifies the invariant that conditioning is display-side
    only — self._last_rpm must continue to hold the raw value.
  test_objectives:
    - "Confirm the EMA reaches 63% of a step within its 150 ms time constant and seeds rather than ramps on the first call."
    - "Confirm alternating samples straddling a threshold produce no band change."
    - "Confirm a full sweep produces exactly one transition per boundary, in each direction."
    - "Confirm the hysteresis margin is clamped so no band becomes unreachable under a narrow RPMBands configuration."
    - "Confirm the flash duty cycle is equal at any configured frame rate."
    - "Confirm the torque-approach band returns white text."
    - "Confirm no logged or reported RPM figure changed."
  in_scope:
    - "src/gtach/display/manager.py — _condition_rpm, _get_band_colour, _get_shift_cue"
    - "The _frame_counter increment in _display_loop"
    - "The _condition_rpm call sites in _draw_digital_mode and _draw_radial_mode"
  out_scope:
    - "Pixel output. No surface is rasterised or compared"
    - "src/gtach/display/models.py — RPMBands and DisplayConfig are read only and unmodified"
    - "comm/obd.py and app.py — the raw sample rate is unchanged"
    - "The annular band indicator, which supersedes the rec 23 correction for the main readout — recommendation 26, task 7.3.11"
    - "Frame skipping and fps_limit reduction — recommendations 12 and 13, task 7.3.6"
    - "Whether the conditioning resolves the observed flicker — that is ai/task.md §7.5.2, an on-target observation"
  dependencies:
    - "SDL_VIDEODRIVER=dummy set before pygame import"
    - "A DisplayManager constructed with a mocked rendering engine, thread manager and touch coordinator"
    - "unittest.mock for the time source used by _condition_rpm"

test_environment:
  python_version: "3.9+ (development platform); 3.11 on target"
  os: "macOS Apple Silicon (development); Debian Linux Raspberry Pi OS (target)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
    - name: "unittest.mock"
      version: "stdlib"
    - name: "pygame"
      version: "SDL2 with the dummy video driver"
  test_framework: "pytest"
  test_data_location: >
    Inline fixtures. Default RPMBands thresholds are used unless a case
    states otherwise: idle_max 999, torque_start 3000, caution_start 4500,
    warning_start 5500, danger_start 5800, redline_rpm 6000.

test_cases:
  - case_id: "TC-001"
    description: "The first conditioning call seeds rather than ramping from zero"
    category: "boundary"
    preconditions:
      - "_rpm_last_ts is None on a freshly constructed DisplayManager"
    test_steps:
      - step: "1"
        action: "Call _condition_rpm(3000.0)"
    inputs:
      - parameter: "raw"
        value: "3000.0"
        type: "float"
    expected_outputs:
      - field: "return"
        expected_value: "3000.0"
        validation: "Exact equality. A filter starting from zero would show the needle sweeping up from rest on every start"
      - field: "_rpm_display"
        expected_value: "3000.0"
        validation: "State seeded, not filtered"
    postconditions:
      - "_rpm_last_ts is set"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Argument returned unchanged"
    defects: []

  - case_id: "TC-002"
    description: "Step response reaches 63% of the step within the time constant"
    category: "positive"
    preconditions:
      - "Conditioner seeded at 0.0"
    test_steps:
      - step: "1"
        action: "Patch the time source to advance in fixed 1/60 s increments"
      - step: "2"
        action: "Feed a constant 3000.0 for 150 ms of simulated time"
      - step: "3"
        action: "Read the returned value"
    inputs:
      - parameter: "step"
        value: "0 to 3000"
        type: "float"
      - parameter: "dt"
        value: "0.01667"
        type: "float"
    expected_outputs:
      - field: "value at t = tau"
        expected_value: "approximately 1896, that is 0.632 x 3000"
        validation: "Within 5% — the discretised EMA approximates the continuous response"
      - field: "monotonicity"
        expected_value: "Strictly increasing across the interval"
        validation: "No overshoot or oscillation"
    postconditions:
      - "The realised lag is the figure to report against on-vehicle behaviour"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Within 5% of 63% of the step, monotonic"
    defects: []

  - case_id: "TC-003"
    description: "dt is clamped at both ends"
    category: "edge"
    preconditions:
      - "Conditioner seeded"
    test_steps:
      - step: "1"
        action: "Patch the time source to return a dt of 0 or negative; call the conditioner"
      - step: "2"
        action: "Patch the time source to return a dt of 30 s; call the conditioner"
    inputs:
      - parameter: "dt"
        value: "-1.0 and 30.0"
        type: "float"
    expected_outputs:
      - field: "negative dt behaviour"
        expected_value: "Clamped to 0.001; output moves only marginally"
        validation: "A clock anomaly must not produce a step or a division error"
      - field: "large dt behaviour"
        expected_value: "Clamped to 0.5; alpha approaches but does not exceed 1"
        validation: "After a stalled frame the filter converges quickly rather than jumping"
    postconditions:
      - "No exception raised in either case"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Both clamps observed, no exception"
    defects: []

  - case_id: "TC-004"
    description: "Non-numeric input degrades to the raw value"
    category: "negative"
    preconditions:
      - "Conditioner seeded"
    test_steps:
      - step: "1"
        action: "Call _condition_rpm(None) and _condition_rpm('abc')"
    inputs:
      - parameter: "raw"
        value: "None, 'abc'"
        type: "object"
    expected_outputs:
      - field: "return"
        expected_value: "The argument, unchanged"
        validation: "Degrades to the pre-change behaviour rather than blanking the display"
      - field: "log record"
        expected_value: "One ERROR line with exc_info"
        validation: "caplog at ERROR"
    postconditions:
      - "No exception escapes into the display loop"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Argument returned and error logged"
    defects: []

  - case_id: "TC-005"
    description: "Samples straddling a threshold produce no band change — the band thrash case"
    category: "positive"
    preconditions:
      - "_active_band set to the torque-approach band (index 1)"
    test_steps:
      - step: "1"
        action: "Call _get_band_colour alternately with 2998 and 3002, fifty times"
      - step: "2"
        action: "Record every returned background colour"
    inputs:
      - parameter: "rpm sequence"
        value: "2998, 3002 repeated"
        type: "float"
    expected_outputs:
      - field: "distinct background colours returned"
        expected_value: "1"
        validation: "Exactly one. The pre-change implementation returns two, alternating the full field at the sample rate"
      - field: "_active_band"
        expected_value: "Unchanged at 1"
        validation: "Neither 3002 > 3000 + 75 nor 2998 < 999 - 75 holds"
    postconditions:
      - "This is the §4.2 reproduction; it fails against the pre-change implementation"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "One distinct colour across fifty alternating samples"
    defects: []

  - case_id: "TC-006"
    description: "A sweep produces exactly one transition per boundary in each direction"
    category: "positive"
    preconditions:
      - "_active_band set to 1"
    test_steps:
      - step: "1"
        action: "Sweep 2900 to 3200 in steps of 1, recording each band index"
      - step: "2"
        action: "Sweep back to 2900 the same way"
    inputs:
      - parameter: "sweep range"
        value: "2900 to 3200 and back"
        type: "float"
    expected_outputs:
      - field: "upward transition point"
        expected_value: "3076 — the first value exceeding 3000 + 75"
        validation: "Strict inequality against threshold plus margin"
      - field: "downward transition point"
        expected_value: "2924 — the first value below 3000 - 75"
        validation: "Strict inequality against threshold minus margin"
      - field: "total transitions"
        expected_value: "2"
        validation: "One in each direction; no chatter at the boundary"
    postconditions:
      - "Directional hysteresis is demonstrated, not merely deadband"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Exactly two transitions at the expected points"
    defects: []

  - case_id: "TC-007"
    description: "The torque-approach band renders white on blue"
    category: "positive"
    preconditions:
      - "_active_band set to 1"
    test_steps:
      - step: "1"
        action: "Call _get_band_colour with a value inside the torque-approach band"
    inputs:
      - parameter: "rpm"
        value: "2000"
        type: "float"
    expected_outputs:
      - field: "returned pair"
        expected_value: "((0, 0, 255), (255, 255, 255))"
        validation: "Exact tuple equality. WCAG 2.1 contrast rises from 2.44:1 to 8.59:1"
    postconditions:
      - "Recommendation 23 satisfied"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "White text returned for the blue band"
    defects: []

  - case_id: "TC-008"
    description: "All six band colour pairs are reachable and correct"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Drive _active_band through 0 to 5 by sweeping the full RPM range upward"
      - step: "2"
        action: "Record the pair returned at each index"
    inputs:
      - parameter: "sweep"
        value: "0 to 6500"
        type: "float"
    expected_outputs:
      - field: "palette"
        expected_value: "black/white, blue/white, green/black, yellow/black, orange/black, red/black"
        validation: "Only index 1's text colour differs from the pre-change palette"
    postconditions:
      - "No band is unreachable under default thresholds"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Six distinct pairs, matching the expected palette"
    defects: []

  - case_id: "TC-009"
    description: "The hysteresis margin is clamped under a narrow band configuration"
    category: "boundary"
    preconditions:
      - "RPMBands configured with two adjacent thresholds 100 RPM apart"
    test_steps:
      - step: "1"
        action: "Sweep across the narrow pair in both directions"
      - step: "2"
        action: "Assert both transitions occur"
    inputs:
      - parameter: "narrowest gap"
        value: "100"
        type: "int"
    expected_outputs:
      - field: "effective margin"
        expected_value: "Below 50 — that is 0.49 x 100"
        validation: "The default 75 would exceed half the gap and could make a band unreachable"
      - field: "transitions"
        expected_value: "Both directions reachable"
        validation: "No band is skipped or trapped"
    postconditions:
      - "A future RPMBands change cannot silently disable a band"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Margin clamped and both transitions observed"
    defects: []

  - case_id: "TC-010"
    description: "A large jump settles over consecutive calls rather than skipping the hysteresis test"
    category: "edge"
    preconditions:
      - "_active_band set to 0"
    test_steps:
      - step: "1"
        action: "Call _get_band_colour once with 6500"
      - step: "2"
        action: "Call repeatedly with 6500 and record _active_band after each"
    inputs:
      - parameter: "rpm"
        value: "6500"
        type: "float"
    expected_outputs:
      - field: "band after the first call"
        expected_value: "1"
        validation: "At most one step per call"
      - field: "band after five calls"
        expected_value: "5"
        validation: "Converges to the correct band within one step per frame"
    postconditions:
      - "At 60 Hz the settle time is under 100 ms and is not perceptible"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "One step per call, converging to index 5"
    defects: []

  - case_id: "TC-011"
    description: "The flash duty cycle is equal at 60 fps"
    category: "positive"
    preconditions:
      - "config.fps_limit = 60; rpm above caution_start"
    test_steps:
      - step: "1"
        action: "Advance _frame_counter through 240 frames"
      - step: "2"
        action: "Record the flash boolean returned by _get_shift_cue at each"
    inputs:
      - parameter: "frames"
        value: "240"
        type: "int"
    expected_outputs:
      - field: "complete cycles"
        expected_value: "8"
        validation: "240 frames at 60 fps is 4 s; 2 Hz gives 8 cycles"
      - field: "on and off run lengths"
        expected_value: "15 frames each, uniformly"
        validation: "half_period = round(60 / 4) = 15. Equal by construction"
    postconditions:
      - "The §4.4 duty-cycle instability is removed"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Eight cycles with uniform 15-frame halves"
    defects: []

  - case_id: "TC-012"
    description: "The flash rate is preserved when the frame rate changes"
    category: "boundary"
    preconditions:
      - "config.fps_limit = 30; rpm above caution_start"
    test_steps:
      - step: "1"
        action: "Advance _frame_counter through 120 frames"
      - step: "2"
        action: "Record the flash boolean at each"
    inputs:
      - parameter: "fps_limit"
        value: "30"
        type: "int"
    expected_outputs:
      - field: "complete cycles"
        expected_value: "8"
        validation: "120 frames at 30 fps is 4 s; still 2 Hz"
      - field: "on and off run lengths"
        expected_value: "Equal to each other"
        validation: "half_period = round(30 / 4) = 8 (rounding to even); halves remain equal"
    postconditions:
      - "Task 7.3.6, which proposes reducing fps_limit to 30, cannot alter the shift-cue rate"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Same cycle count as TC-011 with equal halves"
    defects: []

  - case_id: "TC-013"
    description: "A malformed fps_limit does not divide by zero"
    category: "negative"
    preconditions:
      - "config.fps_limit = 0"
    test_steps:
      - step: "1"
        action: "Call _get_shift_cue above caution_start"
    inputs:
      - parameter: "fps_limit"
        value: "0"
        type: "int"
    expected_outputs:
      - field: "exception"
        expected_value: "None"
        validation: "half_period floors at 1 via max(1, ...)"
      - field: "return"
        expected_value: "A valid four-tuple"
        validation: "Shape unchanged"
    postconditions:
      - "A malformed config degrades to a fast flash, not a crash"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No ZeroDivisionError"
    defects: []

  - case_id: "TC-014"
    description: "The shift-cue branches, colours and border width are unchanged"
    category: "regression"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Call _get_shift_cue below torque_start, between torque_start and caution_start, and above caution_start"
    inputs:
      - parameter: "rpm"
        value: "2000, 4000, 5000"
        type: "float"
    expected_outputs:
      - field: "below torque_start"
        expected_value: "((0, 100, 255), 12, False, (0, 40, 100))"
        validation: "Exact tuple equality"
      - field: "normal band"
        expected_value: "((200, 0, 0), 12, False, (26, 26, 26))"
        validation: "Exact tuple equality"
      - field: "above caution_start"
        expected_value: "Border (0, 180, 0), width 12, flash True, centre alternating (0, 160, 0) / (10, 10, 10)"
        validation: "Only the flash phase source changed, not the returned colours"
    postconditions:
      - "change-4c038bed altered the phase computation only"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "All three branches return their original values"
    defects: []

  - case_id: "TC-015"
    description: "_last_rpm continues to hold the raw value"
    category: "positive"
    preconditions:
      - "A DisplayManager with a mocked rendering engine and a seeded message queue"
    test_steps:
      - step: "1"
        action: "Drive _draw_digital_mode with a known raw sample"
      - step: "2"
        action: "Read self._last_rpm"
      - step: "3"
        action: "Repeat for _draw_radial_mode"
    inputs:
      - parameter: "raw sample"
        value: "3000"
        type: "float"
    expected_outputs:
      - field: "_last_rpm"
        expected_value: "The raw sample, not the conditioned value"
        validation: "Conditioning is display-side only; the raw value remains the record"
    postconditions:
      - "No logged or reported RPM figure changed"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "_last_rpm holds the raw value in both render paths"
    defects: []

  - case_id: "TC-016"
    description: "The frame counter advances exactly once per display-loop iteration"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Parse src/gtach/display/manager.py with the ast module"
      - step: "2"
        action: "Count AugAssign nodes targeting self._frame_counter within _display_loop"
    inputs:
      - parameter: "source file"
        value: "src/gtach/display/manager.py"
        type: "path"
    expected_outputs:
      - field: "increment count"
        expected_value: "1"
        validation: "A second increment would double the flash rate"
      - field: "occurrences of int(time.monotonic() * 2)"
        expected_value: "0"
        validation: "The wall-clock phase source is gone"
    postconditions:
      - "Guards against reintroduction of the §4.4 phase source"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Exactly one increment and no wall-clock phase"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "display review §4.2 — band colour thrash"
      test_cases:
        - "TC-005"
        - "TC-006"
        - "TC-009"
        - "TC-010"
    - requirement_ref: "display review §4.3 — displayed value churn"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-004"
    - requirement_ref: "display review §4.4 — unstable flash duty cycle"
      test_cases:
        - "TC-011"
        - "TC-012"
        - "TC-013"
        - "TC-014"
        - "TC-016"
    - requirement_ref: "display review §7.1 — blue band contrast failure"
      test_cases:
        - "TC-007"
        - "TC-008"
  code_coverage:
    target: "100% of _condition_rpm, _get_band_colour and _get_shift_cue branches"
    achieved: ""
  untested_areas:
    - component: "Rasterised output"
      reason: "No surface is compared. The conditioning changes what is drawn, not how; pixel comparison would test pygame rather than this change"
    - component: "Whether conditioning resolves the observed flicker"
      reason: "An on-target observation recorded as ai/task.md §7.5.2, using the §10.3 discrimination table and the §10.4 simulation sweep"
    - component: "Perceived display lag from the 150 ms time constant"
      reason: "A subjective on-vehicle judgement. TC-002 records the realised lag so it can be assessed against observed behaviour"

test_execution_summary:
  total_cases: 16
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""
  execution_time: ""
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""

traceability:
  requirements:
    - requirement_ref: "display-ui-graphics-review.md §9.1 recommendation 1"
      test_cases:
        - "TC-002"
        - "TC-005"
        - "TC-006"
    - requirement_ref: "display-ui-graphics-review.md §9.1 recommendation 5"
      test_cases:
        - "TC-011"
        - "TC-012"
    - requirement_ref: "display-ui-graphics-review.md §9.5 recommendation 23"
      test_cases:
        - "TC-007"
  designs: []
  changes:
    - change_ref: "change-4c038bed"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-004"
        - "TC-005"
        - "TC-006"
        - "TC-007"
        - "TC-008"
        - "TC-009"
        - "TC-010"
        - "TC-011"
        - "TC-012"
        - "TC-013"
        - "TC-014"
        - "TC-015"
        - "TC-016"

notes: >
  Generated pytest file: tests/display/test_rpm_conditioning.py, per P06
  §1.7.3.

  This is the only document in the §8.2 set that needs pygame. Set
  SDL_VIDEODRIVER=dummy in a session-scoped fixture before the first
  import, matching the arrangement DisplayRenderingEngine.initialize
  already uses at engine.py:92. No display surface is created and
  set_mode is never called, so the suite remains headless.

  _get_band_colour became stateful under change-4c038bed: its result
  depends on _active_band as well as its argument. Every case that
  exercises it must therefore set _active_band explicitly in its
  preconditions rather than relying on construction order.

  TC-005 is the §4.2 reproduction and TC-011 the §4.4 reproduction. Both
  fail against the pre-change implementation and are the evidence that
  the two findings were defects. Neither may be dropped if the case list
  is trimmed.

  Task 7.3.11 replaces the full-field band colour with an annular
  indicator, which supersedes TC-007 for the main readout. When that
  change is authored, TC-007 should be retargeted at the indicator rather
  than deleted — the contrast requirement survives the presentation
  change.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial test document for change-4c038bed, per ai/task.md §8.2."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t05_test"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial test document for change-4c038bed, per ai/task.md §8.2. |

---

Copyright (c) 2026 William Watson. MIT License.
