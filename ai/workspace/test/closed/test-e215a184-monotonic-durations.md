Created: 2026 October 09

# Test: Monotonic Durations in Five Files

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-e215a184"
  title: "Verify durations and cache ages are immune to wall-clock steps"
  date: "2026-10-09"
  author: "William Watson"
  status: "passed"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-e215a184"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "time.monotonic() adoption in device_surfaces.py, circular_positioning.py, engine.py, monitor.py, platform.py"
  design_refs: []
  change_refs:
    - "change-e215a184"
  requirement_refs:
    - "issue-e215a184"

scope:
  description: >
    Verifies that a forward or backward wall-clock step (for example the
    NTP correction after a cold boot on the Pi) does not invalidate the
    platform cache or corrupt monitoring durations, that the only
    remaining time.time() sites are the justified dirty-region pair, and
    that the adjusted test double still drives the performance tests.
  test_objectives:
    - "Confirm the platform-type cache survives a +3600 s wall-clock step."
    - "Confirm monitoring_duration stays in [0, 5) s after a -3600 s step."
    - "Confirm the only time.time() uses left in the five files are the dirty-region timestamp and its reader."
    - "Confirm tests/test_performance_instrumentation.py passes with the monotonic-aware clock fixture."
    - "Confirm plausible FPS and frame times across the NTP step on the device."
  in_scope:
    - "The five source files in report-e215a184 §3"
    - "tests/test_performance_instrumentation.py clock fixture"
  out_scope:
    - "PerformanceMetrics.last_update_time default in interfaces.py — unchanged"
    - "Other modules' time.time() uses"
  dependencies:
    - "Development venv with pip install -e .[dev]"
    - "TC-005 and TC-006 only: root@gtach.local, cold boot with network"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development); Debian Linux on Raspberry Pi Zero 2W (TC-005, TC-006)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest (monkeypatch of time.time)"
  test_data_location: "None"

test_cases:
  - case_id: "TC-001"
    description: "Platform cache survives a forward wall-clock step"
    category: "positive"
    preconditions:
      - "PlatformDetector fresh; _run_all_detections instrumented"
    test_steps:
      - step: "1"
        action: "Call get_platform_type()"
      - step: "2"
        action: "Advance time.time by 3600 s"
      - step: "3"
        action: "Call get_platform_type() again"
    inputs:
      - parameter: "wall-clock step"
        value: "+3600"
        type: "float (s)"
    expected_outputs:
      - field: "second result"
        expected_value: "Identical cached value"
        validation: "Equality"
      - field: "_run_all_detections calls"
        expected_value: "1"
        validation: "Call count"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_monotonic_durations.py::test_platform_cache_survives_a_forward_step"
      pass_fail_criteria: "Cache hit"
    defects: []

  - case_id: "TC-002"
    description: "Monitor uptime survives a backward wall-clock step"
    category: "negative"
    preconditions:
      - "PerformanceMonitor monitoring started"
    test_steps:
      - step: "1"
        action: "Step time.time back by 3600 s"
      - step: "2"
        action: "Read monitoring_duration"
    inputs:
      - parameter: "wall-clock step"
        value: "-3600"
        type: "float (s)"
    expected_outputs:
      - field: "monitoring_duration"
        expected_value: "0 <= value < 5"
        validation: "Range check"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_monotonic_durations.py::test_monitor_uptime_survives_a_backward_step"
      pass_fail_criteria: "Within range"
    defects: []

  - case_id: "TC-003"
    description: "Remaining wall-clock uses are only the justified pair"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -n 'time\\.time()' src/gtach/display/setup_components/rendering/device_surfaces.py src/gtach/display/setup_components/layout/circular_positioning.py src/gtach/display/rendering/engine.py src/gtach/display/performance/monitor.py src/gtach/utils/platform.py"
    inputs: []
    expected_outputs:
      - field: "matches"
        expected_value: "Two, both in monitor.py: the dirty-region timestamp and get_dirty_regions current_time"
        validation: "Inspection"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "Three lines, all monitor.py: line 49 is a comment; lines 548 (dirty-region timestamp) and 567 (get_dirty_regions current_time) are the two justified sites"
      pass_fail_criteria: "Exactly the two justified sites"
    defects: []

  - case_id: "TC-004"
    description: "Performance instrumentation tests pass with the adjusted fixture"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "pytest tests/test_performance_instrumentation.py -v"
    inputs: []
    expected_outputs:
      - field: "result"
        expected_value: "All pass; no assertion changed relative to 00c9129^"
        validation: "pytest; git diff 00c9129^ 00c9129 -- tests/test_performance_instrumentation.py shows fixture lines only"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "All tests PASSED. git diff 00c9129^ 00c9129 shows the clock fixture only: SimpleNamespace gains monotonic, plus one comment"
      pass_fail_criteria: "Pass; fixture-only diff"
    defects: []

  - case_id: "TC-005"
    description: "On-device: FPS and frame times plausible across the NTP step"
    category: "positive"
    preconditions:
      - "Branch deployed to root@gtach.local; service run with --debug"
      - "Cold boot with network so that NTP steps the clock"
    test_steps:
      - step: "1"
        action: "Cold boot; let the gauge run for several minutes"
      - step: "2"
        action: "Pull logs; inspect the periodic 'Performance:' lines in debug.log around the NTP correction"
    inputs: []
    expected_outputs:
      - field: "FPS"
        expected_value: "Approximately the target throughout; no spike or zero"
        validation: "Log inspection"
      - field: "frame time"
        expected_value: "No discontinuity at the NTP step"
        validation: "Log inspection"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local, guided by Claude)"
      actual_result: "Run with forced steps instead of a cold-boot NTP step (debug is off after boot, so a cold-boot step cannot be logged). NTP off; clock set back 1 h (real 10:05:04); forward 2 h (real 10:06:46); NTP restored (stepped back 1 h at ~10:08:30). Performance lines across all steps: 30.0 FPS, 14.5-15.9 ms frame; gauge smooth, no DISCONNECTED screen. Out-of-scope defect exposed: transport thread frozen for 102.9 s by the backward step, see issue-4f671d09"
      pass_fail_criteria: "No anomaly at the step"
    defects: []

  - case_id: "TC-006"
    description: "On-device: platform cache age is a small positive number"
    category: "boundary"
    preconditions:
      - "As TC-005"
    test_steps:
      - step: "1"
        action: "Inspect the log_platform_info 'Cache Age' line"
    inputs: []
    expected_outputs:
      - field: "Cache Age"
        expected_value: "Small positive value"
        validation: "Log inspection"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local, guided by Claude)"
      actual_result: "Cache Age: 0.1s from python -m gtach.utils.platform"
      pass_fail_criteria: "Positive and plausible"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-e215a184"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]
  code_coverage:
    target: "Classification table in report-e215a184 §2"
    achieved: ""
  untested_areas:
    - component: "Capabilities cache within the first 300 s of uptime (_last_detection_time == 0 sentinel)"
      reason: "Behaviour change recorded as benign in the report; no test asserts it either way. Candidate for review"
    - component: "device_surfaces.py, circular_positioning.py, engine.py duration sites"
      reason: "Covered by TC-003 statically only; no behavioural test injects a clock step into these local start/end pairs"

test_execution_summary:
  total_cases: 6
  passed: 6
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: "100%"
  execution_time: "Targeted pytest run 26.8 s; on-device clock-step test 10:04-10:09"
  test_cycle: "Initial"

defect_summary:
  total_defects: 1
  critical: 0
  high: 1
  medium: 0
  low: 0
  issues:
    - issue_ref: "issue-4f671d09"
      severity: "high"
      status: "open"

verification:
  verified_date: "2026-10-09"
  verified_by: "William Watson"
  verification_notes: "Mac: pytest 9.1.1, Python 3.11.14. Pi: GTach 0.4.10, Python 3.9.2. The defect recorded above lies outside the five files of this change and does not fail any case here. Evidence under ~/Documents/gtach-testlogs/stage6/."
  sign_off: "Approved"

traceability:
  requirements:
    - requirement_ref: "issue-e215a184"
      test_cases: ["TC-001", "TC-002", "TC-005"]
  designs: []
  changes:
    - change_ref: "change-e215a184"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]

notes: >
  Generated pytest file: tests/test_monotonic_durations.py, per P06
  §1.7.3; the clock fixture in tests/test_performance_instrumentation.py
  was also adjusted. Written during implementation; recorded here
  retrospectively. Closed T05 test-0b00759c notes that monitor.py used
  time.time(); that note is superseded by this change. TC-005 is the
  authoritative check, since the defect only manifests on hardware with
  an NTP step. Run: pytest tests/test_monotonic_durations.py
  tests/test_performance_instrumentation.py -v.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-e215a184."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Executed on Mac and gtach.local; TC-005 run with forced clock steps; out-of-scope defect raised as issue-4f671d09; status passed."

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
| 1.0 | 2026-10-09 | Initial test document for change-e215a184. |
| 1.1 | 2026-10-09 | Executed on Mac and gtach.local; issue-4f671d09 raised for an out-of-scope defect; status passed. |

---

Copyright (c) 2026 William Watson. MIT License.
