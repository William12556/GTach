Created: 2026 October 07

# Issue: Wall-Clock Durations Remaining

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-e215a184
  title: Durations and cache ages outside the change-4005360c file list still use
    time.time()
  date: '2026-10-07'
  reporter: Claude Code
  status: closed
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-e215a184
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: Remaining scope of audit-36b6ea95 C16. change-4005360c switched only
    the files it listed; report-4005360c lists the sites kept.
affected_scope:
  components:
  - name: DeviceSurfaceRenderer
    file_path: src/gtach/display/setup_components/rendering/device_surfaces.py
  - name: CircularPositioningEngine
    file_path: src/gtach/display/setup_components/layout/circular_positioning.py
  - name: DisplayRenderingEngine
    file_path: src/gtach/display/rendering/engine.py
  - name: PerformanceMonitor
    file_path: src/gtach/display/performance/monitor.py
  - name: PlatformDetector
    file_path: src/gtach/utils/platform.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: ''
  steps:
  - grep -rn 'time.time()' src/gtach
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: time.monotonic() wherever the value is a duration, rate or cache age.
  actual: time.time() at device_surfaces.py:168,344; circular_positioning.py:89,127,310,332;
    engine.py:742,890; monitor.py (FPS, uptime and cache-age arithmetic, 11 sites);
    platform.py:124,500,735.
  impact: A wall-clock step (NTP correction after boot on the Pi, issue-b9ee7428)
    distorts FPS, render-time and uptime figures and can invalidate or prolong the
    platform-detection cache.
  workaround: ''
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: C16 was scoped to the files named in change-4005360c.
  technical_notes: Keep time.time() for values shown as timestamps (monitor.py:539
    'timestamp', manager.py debug info, OBDResponse.timestamp).
  related_issues:
  - issue_ref: issue-4005360c
    relationship: related
  - issue_ref: issue-b9ee7428
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: Switch the duration-only sites to time.monotonic().
  change_ref: change-e215a184
  resolved_date: '2026-10-09'
  resolved_by: Claude Code (change-e215a184, commit 00c9129)
  fix_description: ''
verification:
  verified_date: '2026-10-09'
  verified_by: William Watson
  test_results: test-e215a184 passed (6/6); FPS and frame time steady across forced -1 h and +2 h clock steps on gtach.local.
  closure_notes: Closed. The clock-step test exposed a separate defect in blocking waits on Python 3.9, raised as issue-4f671d09.
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - grep shows time.time() only at timestamp and seed sites; pytest passes.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-e215a184
  test_refs:
  - ''
notes: audit-36b6ea95 C16 (residual).
loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ''
  last_review_feedback: ''
version_history:
- version: '1.0'
  date: '2026-10-07'
  author: Claude Code
  changes:
  - Initial issue document, raised at the close of audit-36b6ea95 remediation.
- version: '1.1'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Coupled to change-e215a184 (P03.7); scope kept to the five listed files (sim_transport.py excluded, tracked in task.md).
- version: '1.2'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Resolved by change-e215a184; verified by test-e215a184; closed.
metadata:
  copyright: Copyright (c) 2026 William Watson. MIT License.
  template_version: '1.0'
  schema_type: t03_issue
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial issue document. Raised at the close of audit-36b6ea95 remediation. |
| 1.1 | 2026-10-09 | Coupled to change-e215a184; scope kept to the five listed files. |
| 1.2 | 2026-10-09 | Resolved by change-e215a184; verified by test-e215a184; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
