Created: 2026 July 30

# Test: Performance Instrumentation

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-0b00759c"
  title: "Unit tests for render-time measurement, integer frame IDs, the periodic-logging gate and rate-limited memory sampling"
  date: "2026-07-30"
  author: "William Watson"
  status: "planned"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-0b00759c"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "PerformanceMonitor; DisplayManager._display_loop instrumentation call order"
  design_refs: []
  change_refs:
    - "change-0b00759c"
    - "change-c5dedd71"
  requirement_refs:
    - "display-ui-graphics-review.md §6.1"
    - "display-ui-graphics-review.md §6.2"
    - "display-ui-graphics-review.md §9.3 recommendations 15, 16, 17, 18"

scope:
  description: >
    Verifies that frame_time_ms measures rendered work rather than the
    loop period, that frame identifiers are integers with 0 reserved as
    the disabled sentinel, that the periodic-logging decision is taken
    inside the monitor, and that psutil is read at most once per second.
    This is the measurement on which tasks 7.3.5 and 7.3.6 will be
    judged, so its correctness is load-bearing for the rest of the
    display work.
  test_objectives:
    - "Confirm a bracketed interval reports the bracketed duration, not the frame target."
    - "Confirm record_frame_end is called before the pacing sleep in the display loop."
    - "Confirm frame ID 0 is never issued as a valid identifier."
    - "Confirm should_log_periodic fires exactly once per 600 recorded frames."
    - "Confirm the psutil read is rate limited and that a failed read does not poison the cache."
    - "Confirm the annotations corrected by change-c5dedd71 agree with the implementation."
  in_scope:
    - "src/gtach/display/performance/monitor.py — record_frame_start, record_frame_end, should_log_periodic, _get_current_memory_usage, reset_metrics"
    - "src/gtach/display/manager.py — instrumentation call order within _display_loop only"
    - "PerformanceMonitorInterface frame-ID annotations (change-c5dedd71)"
  out_scope:
    - "What is rendered. This change altered measurement only"
    - "_calculate_current_fps, _update_metrics_history, get_historical_metrics — unmodified"
    - "The dirty-region API: add_dirty_region, get_dirty_regions, clear_dirty_regions — unused by the render path and untouched"
    - "fps_limit selection and frame skipping — recommendations 12 and 13, task 7.3.6"
    - "Absolute frame-time figures on target hardware — that is ai/task.md §7.5.3"
  dependencies:
    - "unittest.mock for psutil.Process and for the time source"
    - "pygame importable for the module-level Rect reference; no display surface required"

test_environment:
  python_version: "3.9+ (development platform); 3.11 on target"
  os: "macOS Apple Silicon (development); Debian Linux Raspberry Pi OS (target)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
    - name: "unittest.mock"
      version: "stdlib"
    - name: "psutil"
      version: "mocked"
    - name: "pygame"
      version: "SDL_VIDEODRIVER=dummy; import only"
  test_framework: "pytest"
  test_data_location: "Inline fixtures. A PerformanceMonitor constructed with target_fps=60 and monitoring started"

test_cases:
  - case_id: "TC-001"
    description: "A bracketed interval reports its own duration"
    category: "positive"
    preconditions:
      - "Monitoring started"
    test_steps:
      - step: "1"
        action: "frame_id = record_frame_start()"
      - step: "2"
        action: "Sleep 5 ms"
      - step: "3"
        action: "frame_time = record_frame_end(frame_id)"
    inputs:
      - parameter: "bracketed duration"
        value: "0.005"
        type: "float"
    expected_outputs:
      - field: "frame_time"
        expected_value: "approximately 0.005 s, and clearly below the 0.0167 s target"
        validation: "0.003 < frame_time < 0.012 — generous bounds; the discriminating assertion is that it is not near 0.0167"
    postconditions:
      - "This is the case the pre-change implementation could not satisfy, because the sleep fell inside the bracket"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Measured duration reflects the bracket, not the frame target"
    defects: []

  - case_id: "TC-002"
    description: "record_frame_end precedes the pacing sleep in the display loop"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Parse src/gtach/display/manager.py with the ast module"
      - step: "2"
        action: "Locate the _display_loop function definition"
      - step: "3"
        action: "Assert the line number of the record_frame_end call is lower than that of the time.sleep(_sleep) call"
    inputs:
      - parameter: "source file"
        value: "src/gtach/display/manager.py"
        type: "path"
    expected_outputs:
      - field: "call order"
        expected_value: "record_frame_end before time.sleep"
        validation: "Static assertion on line numbers within the function body"
    postconditions:
      - "Guards against reintroduction of the §6.2 defect by a future edit to the loop tail"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "record_frame_end appears first"
    defects: []

  - case_id: "TC-003"
    description: "Frame identifiers are consecutive positive integers"
    category: "positive"
    preconditions:
      - "Monitoring started; metrics freshly reset"
    test_steps:
      - step: "1"
        action: "Call record_frame_start three times, closing each with record_frame_end"
    inputs: []
    expected_outputs:
      - field: "returned IDs"
        expected_value: "1, 2, 3"
        validation: "Exact equality, and isinstance(id, int) for each"
      - field: "truthiness"
        expected_value: "All truthy"
        validation: "No valid ID is 0, so the loop's guard cannot reject a live frame"
    postconditions:
      - "No uuid allocation occurred"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "IDs are 1, 2, 3 and all are truthy ints"
    defects: []

  - case_id: "TC-004"
    description: "Disabled monitoring yields the 0 sentinel"
    category: "negative"
    preconditions:
      - "Monitoring not started, or stopped"
    test_steps:
      - step: "1"
        action: "Call record_frame_start()"
      - step: "2"
        action: "Call record_frame_end(0)"
    inputs:
      - parameter: "frame_id"
        value: "0"
        type: "int"
    expected_outputs:
      - field: "record_frame_start return"
        expected_value: "0"
        validation: "Integer sentinel, not the former empty string"
      - field: "record_frame_end return"
        expected_value: "0.0"
        validation: "Guard rejects the sentinel"
      - field: "warning log"
        expected_value: "None emitted"
        validation: "The sentinel is an expected value, not a missing frame"
    postconditions:
      - "No entry added to _active_frames"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "0 returned and accepted silently"
    defects: []

  - case_id: "TC-005"
    description: "The expiry scan is skipped in the steady state"
    category: "positive"
    preconditions:
      - "Monitoring started; at most one frame open at a time"
    test_steps:
      - step: "1"
        action: "Open and close 100 frames in sequence"
      - step: "2"
        action: "Assert _dropped_frames did not increase and _active_frames is empty"
    inputs:
      - parameter: "frames"
        value: "100"
        type: "int"
    expected_outputs:
      - field: "_dropped_frames"
        expected_value: "0"
        validation: "No entry expired; the scan had nothing to do and was skipped"
      - field: "_active_frames"
        expected_value: "empty dict"
        validation: "Each frame was popped by record_frame_end"
    postconditions:
      - "Steady-state cost is a counter increment and a dict insert"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No spurious dropped frames"
    defects: []

  - case_id: "TC-006"
    description: "Stale frames are still expired when more than one is open"
    category: "boundary"
    preconditions:
      - "Monitoring started"
    test_steps:
      - step: "1"
        action: "Open three frames without closing them"
      - step: "2"
        action: "Advance the monitor's time source beyond the 1 s cutoff"
      - step: "3"
        action: "Open a fourth frame, which triggers the scan"
    inputs:
      - parameter: "open frames"
        value: "3"
        type: "int"
    expected_outputs:
      - field: "_dropped_frames"
        expected_value: "3"
        validation: "The skip optimisation must not disable expiry when it is needed"
      - field: "_active_frames"
        expected_value: "Contains only the fourth frame"
        validation: "Length 1"
    postconditions:
      - "The len > 1 guard is an optimisation, not a behaviour change"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "All three stale entries expired"
    defects: []

  - case_id: "TC-007"
    description: "should_log_periodic fires exactly once per 600 frames"
    category: "positive"
    preconditions:
      - "Monitoring started; metrics reset"
    test_steps:
      - step: "1"
        action: "Record 1200 frames, calling should_log_periodic after each"
      - step: "2"
        action: "Count the True returns and record the frame numbers"
    inputs:
      - parameter: "frames"
        value: "1200"
        type: "int"
    expected_outputs:
      - field: "True count"
        expected_value: "2"
        validation: "Exactly two firings"
      - field: "firing frame numbers"
        expected_value: "600 and 1200"
        validation: "Modulo the configured _log_interval_frames"
    postconditions:
      - "No metrics object was constructed on any other frame"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Two firings at the expected frame numbers"
    defects: []

  - case_id: "TC-008"
    description: "should_log_periodic is False at frame zero and when monitoring is disabled"
    category: "boundary"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Call should_log_periodic() with _frame_count at 0"
      - step: "2"
        action: "Stop monitoring and call again"
    inputs: []
    expected_outputs:
      - field: "return at frame 0"
        expected_value: "False"
        validation: "0 % 600 == 0, so the _frame_count > 0 guard is required and must be present"
      - field: "return when disabled"
        expected_value: "False"
        validation: "Early return before the lock is taken"
    postconditions:
      - "No log line is emitted before any frame is recorded"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "False in both cases"
    defects: []

  - case_id: "TC-009"
    description: "The display loop constructs metrics only when the gate opens"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Parse src/gtach/display/manager.py with the ast module"
      - step: "2"
        action: "Assert every get_current_metrics call inside _display_loop is nested within an If whose test calls should_log_periodic"
    inputs:
      - parameter: "source file"
        value: "src/gtach/display/manager.py"
        type: "path"
    expected_outputs:
      - field: "unguarded get_current_metrics calls in _display_loop"
        expected_value: "0"
        validation: "Static assertion. Prevents the psutil read returning to the per-frame path"
      - field: "occurrences of len(frame_id)"
        expected_value: "0"
        validation: "The former string-length guard is gone"
    postconditions:
      - "Recommendation 16 cannot silently regress"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No unguarded call and no len(frame_id)"
    defects: []

  - case_id: "TC-010"
    description: "psutil is read at most once per second"
    category: "positive"
    preconditions:
      - "psutil.Process mocked; monitor holds a _process reference"
    test_steps:
      - step: "1"
        action: "Call _get_current_memory_usage 100 times without advancing the clock"
      - step: "2"
        action: "Assert memory_info call count"
    inputs:
      - parameter: "calls"
        value: "100"
        type: "int"
    expected_outputs:
      - field: "memory_info call count"
        expected_value: "1"
        validation: "The first call seeds the cache; the remaining 99 are served from it"
      - field: "returned value"
        expected_value: "Identical across all 100 calls"
        validation: "Cached value returned unchanged"
    postconditions:
      - "One /proc read per second replaces one per frame"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Exactly one underlying read"
    defects: []

  - case_id: "TC-011"
    description: "The memory cache refreshes after the sample interval"
    category: "boundary"
    preconditions:
      - "psutil.Process mocked to return two different RSS values in sequence"
    test_steps:
      - step: "1"
        action: "Call _get_current_memory_usage"
      - step: "2"
        action: "Advance the mocked clock by 1.1 s"
      - step: "3"
        action: "Call again"
    inputs:
      - parameter: "clock advance"
        value: "1.1"
        type: "float"
    expected_outputs:
      - field: "memory_info call count"
        expected_value: "2"
        validation: "The interval elapsed, so a fresh read was taken"
      - field: "second returned value"
        expected_value: "The second mocked RSS"
        validation: "Cache was replaced, not merely re-read"
    postconditions:
      - "The figure remains diagnostically useful over a long run"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Two reads and the newer value returned"
    defects: []

  - case_id: "TC-012"
    description: "A failed psutil read does not poison the cache"
    category: "negative"
    preconditions:
      - "psutil.Process.memory_info mocked to raise"
    test_steps:
      - step: "1"
        action: "Seed the cache with a successful read"
      - step: "2"
        action: "Advance the clock past the interval and make memory_info raise"
      - step: "3"
        action: "Call _get_current_memory_usage"
    inputs:
      - parameter: "memory_info"
        value: "raises Exception"
        type: "exception"
    expected_outputs:
      - field: "return"
        expected_value: "0.0"
        validation: "The existing except clause returns 0.0"
      - field: "_memory_cache_mb"
        expected_value: "The previously seeded value, unchanged"
        validation: "The cache is written only on a successful read"
    postconditions:
      - "A transient failure does not persist as a false zero"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "0.0 returned and the cache preserved"
    defects: []

  - case_id: "TC-013"
    description: "reset_metrics clears the frame counter and the memory cache"
    category: "positive"
    preconditions:
      - "Several frames recorded and the memory cache seeded"
    test_steps:
      - step: "1"
        action: "Call reset_metrics()"
      - step: "2"
        action: "Call record_frame_start()"
      - step: "3"
        action: "Call _get_current_memory_usage() with memory_info mocked"
    inputs: []
    expected_outputs:
      - field: "first frame ID after reset"
        expected_value: "1"
        validation: "_frame_id_counter was cleared"
      - field: "memory_info call count after reset"
        expected_value: "1"
        validation: "_memory_cache_ts was cleared, forcing a fresh read"
    postconditions:
      - "No stale reading survives a reset"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Counter restarts at 1 and the cache is cold"
    defects: []

  - case_id: "TC-014"
    description: "The dropped-frame test fires on a genuine overrun"
    category: "boundary"
    preconditions:
      - "target_fps=60, so frame_time_target is 1/60 s"
    test_steps:
      - step: "1"
        action: "Bracket an interval exceeding frame_time_target * 1.5"
      - step: "2"
        action: "Read _dropped_frames"
    inputs:
      - parameter: "bracketed duration"
        value: "0.030"
        type: "float"
    expected_outputs:
      - field: "_dropped_frames"
        expected_value: "1"
        validation: "The test now sees real render time, so it is meaningful for the first time"
    postconditions:
      - "A rise in this counter after change-0b00759c is the expected outcome, not a regression"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Counter incremented once"
    defects: []

  - case_id: "TC-015"
    description: "Frame-ID annotations agree between the interface and the implementation"
    category: "regression"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Read typing.get_type_hints for record_frame_start and record_frame_end on both PerformanceMonitor and PerformanceMonitorInterface"
      - step: "2"
        action: "Assert the annotations match"
    inputs: []
    expected_outputs:
      - field: "record_frame_start return annotation"
        expected_value: "int on both"
        validation: "The drift corrected by change-c5dedd71 has not returned"
      - field: "record_frame_end frame_id annotation"
        expected_value: "int on both"
        validation: "As above"
    postconditions:
      - "Interface and implementation cannot silently diverge again"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Annotations identical"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "display review §6.2 — record_frame_end after the sleep"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-014"
    - requirement_ref: "display review §6.1 — per-frame instrumentation cost"
      test_cases:
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
    - requirement_ref: "change-c5dedd71 — interface annotation drift"
      test_cases:
        - "TC-015"
  code_coverage:
    target: "100% of record_frame_start, record_frame_end, should_log_periodic, _get_current_memory_usage and reset_metrics branches"
    achieved: ""
  untested_areas:
    - component: "get_historical_metrics, _update_metrics_history, _calculate_current_fps"
      reason: "Unmodified by change-0b00759c; the change altered only what frame_time means, not how the rate is derived"
    - component: "The dirty-region API"
      reason: "Unused by the current render path and untouched by the change"
    - component: "Absolute frame-time figures on target hardware"
      reason: "An on-target observation, recorded as ai/task.md §7.5.3, not a unit test"

test_execution_summary:
  total_cases: 15
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
    - requirement_ref: "display-ui-graphics-review.md §9.3 recommendation 15"
      test_cases:
        - "TC-001"
        - "TC-002"
    - requirement_ref: "display-ui-graphics-review.md §9.3 recommendation 16"
      test_cases:
        - "TC-007"
        - "TC-009"
    - requirement_ref: "display-ui-graphics-review.md §9.3 recommendation 17"
      test_cases:
        - "TC-003"
        - "TC-004"
    - requirement_ref: "display-ui-graphics-review.md §9.3 recommendation 18"
      test_cases:
        - "TC-010"
        - "TC-011"
        - "TC-012"
  designs: []
  changes:
    - change_ref: "change-0b00759c"
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
    - change_ref: "change-c5dedd71"
      test_cases:
        - "TC-015"

notes: >
  Generated pytest file: tests/display/test_performance_monitor.py, per
  P06 §1.7.3.

  TC-001 is the case that fails against the pre-change implementation and
  is the reason the rest of the display efficiency work can be judged at
  all. It must not be dropped.

  TC-002 and TC-009 are static assertions over the source rather than
  behavioural tests. They exist because the defect they guard against is
  one of call placement, which no runtime assertion on PerformanceMonitor
  alone can detect — the monitor cannot know when its caller sleeps.

  The monitor uses time.time() rather than time.monotonic(). Tests that
  advance the clock should patch the module's time reference rather than
  sleeping, so the suite stays fast; TC-001 is the exception and uses a
  real 5 ms sleep because it is measuring the bracket itself.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial test document for change-0b00759c and change-c5dedd71, per ai/task.md §8.2."

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
| 1.0 | 2026-07-30 | Initial test document for change-0b00759c and change-c5dedd71, per ai/task.md §8.2. |

---

Copyright (c) 2026 William Watson. MIT License.
