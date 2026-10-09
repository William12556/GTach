Created: 2026 October 09

# Change: Monotonic Clock for Remaining Durations

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-e215a184"
  title: "Use time.monotonic() for durations, rates and cache ages in the five files named by issue-e215a184"
  date: "2026-10-09"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e215a184"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-e215a184"
  description: "Resolves issue-e215a184 (audit-36b6ea95 C16 residual). Scope confirmed 2026-10-09: the five listed files only."

scope:
  summary: "Switch each clock variable in the listed files to time.monotonic() when all of its uses are durations or ages; keep time.time() for values used as wall-clock times."
  affected_components:
    - name: "DeviceSurfaceRenderer"
      file_path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_type: "modify"
    - name: "CircularPositioningEngine"
      file_path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "PerformanceMonitor"
      file_path: "src/gtach/display/performance/monitor.py"
      change_type: "modify"
    - name: "PlatformDetector"
      file_path: "src/gtach/utils/platform.py"
      change_type: "modify"
    - name: "Clock-step regression tests"
      file_path: "tests/test_monotonic_durations.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "src/gtach/comm/sim_transport.py elapsed-time sites (decided 2026-10-09; recorded in ai/task.md)."
    - "manager.py 'timestamp' and the sin(time.time()) demo value; OBDResponse.timestamp."
    - "Files not listed in affected_components."

rational:
  problem_statement: >
    See issue-e215a184. Durations and cache ages computed from
    time.time() are distorted by a wall-clock step, such as the NTP
    correction after boot on the Pi (issue-b9ee7428).
  proposed_solution: >
    Work per clock variable, not per line. A variable or record field
    (for example PerformanceMonitor._start_time, _memory_cache_ts,
    _last_metrics_update, the frame-history and memory-history
    'timestamp' fields, metrics.last_update_time, the _active_frames
    values; PlatformDetector._last_detection_time; local start/end
    pairs) is switched to time.monotonic() at every assignment only
    when every read of it is a difference or comparison with another
    value from the same clock. It keeps time.time() when any read
    outside its module interprets it as a wall-clock time (formatted
    as a date, compared with time.time(), logged or persisted as a
    timestamp); such cases are listed in the report. No subtraction
    may mix the two clocks. The monitor.py:539 'timestamp' field stays
    time.time(). PlatformDetector exposes 'last_detection_time' in its
    info dict (~line 733): grep its consumers; if none interprets it as
    an epoch time, switch it and note this in the report, otherwise
    keep it and report.
  alternatives_considered:
    - option: "Switch every listed line mechanically."
      reason_rejected: "Several values are stored and later compared with other stored values; a partial switch would mix clocks."
  benefits:
    - "FPS, render-time, uptime and platform-cache figures are unaffected by wall-clock steps."
  risks:
    - risk: "A value shown to a reader as a time of day becomes a monotonic number."
      mitigation: "Per-variable consumer check; such values keep time.time() and are reported."

technical_details:
  current_behavior: "time.time() at device_surfaces.py:168,344; circular_positioning.py:89,127,310,332; engine.py:742,890; monitor.py (14 sites); platform.py:124,500,735 (ba661d4)."
  proposed_behavior: "time.monotonic() for every duration-only variable; time.time() only for wall-clock values."
  implementation_approach: "Per-file classification table in the report, then edits."
  code_changes:
    - component: "display and utils"
      file: "five files listed in scope"
      change_summary: "Clock switch per variable."
      functions_affected: []
      classes_affected:
        - "DeviceSurfaceRenderer"
        - "CircularPositioningEngine"
        - "DisplayRenderingEngine"
        - "PerformanceMonitor"
        - "PlatformDetector"
  data_changes: []
  interface_changes:
    - interface: "PlatformDetector info dict 'last_detection_time'"
      change_type: "contract"
      details: "Becomes a monotonic value only if no consumer reads it as an epoch time."
      backward_compatible: "yes"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-273ca048"
      relationship: "blocked_by. Both edit circular_positioning.py."
    - change_ref: "change-4005360c"
      relationship: "related. Switched the first set of files."

testing_requirements:
  test_approach: "Clock-step regression tests with time.time patched."
  test_cases:
    - scenario: "PlatformDetector: detect once; patch time.time to return +3600 s; detect again within the cache duration."
      expected_result: "Cached result returned (no re-detection)."
    - scenario: "PerformanceMonitor: start monitoring; patch time.time to step back 3600 s; read uptime."
      expected_result: "Uptime is non-negative and below a few seconds."
    - scenario: "grep -n 'time.time()' over the five files."
      expected_result: "Only sites listed in the report as wall-clock values remain."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: "2 hours"
  implementation_steps:
    - step: "Classify each variable; edit; add tests/test_monotonic_durations.py."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Human verification: FPS and render figures in debug.log look plausible after boot on the Pi."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-4005360c"
      relationship: "related"
    - change_ref: "change-b9ee7428"
      relationship: "related. Monotonic watchdog timing."
    - change_ref: "change-273ca048"
      relationship: "blocked_by"
  related_issues:
    - issue_ref: "issue-e215a184"
      relationship: "resolves"

notes: "Line numbers are from ba661d4."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-e215a184 iteration 1."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial change document resolving issue-e215a184 iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
