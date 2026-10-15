Created: 2026 October 14

# Issue: SimTransport Elapsed Time Uses the Wall Clock

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-72f95f73
  title: SimTransport computes the RPM sweep's elapsed time from time.time()
  date: '2026-10-14'
  reporter: William Watson
  status: closed
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-72f95f73
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: Excluded from issue-e215a184 scope on 2026-10-09 and recorded in
    ai/task.md. SimTransport stores _start_time = time.time() and computes the
    elapsed time of the RPM sine sweep as time.time() - _start_time.
affected_scope:
  components:
  - name: SimTransport
    file_path: src/gtach/comm/sim_transport.py
  designs:
  - design_ref: ''
  version: bb29226
reproduction:
  prerequisites: GTach running with the simulation transport
  steps:
  - grep -n 'time.time()' src/gtach/comm/sim_transport.py
  frequency: always
  reproducibility_conditions: A wall-clock step while SimTransport is in use
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: The elapsed time of the RPM sweep is unaffected by wall-clock steps
    (time.monotonic(), as for the durations switched by change-4005360c and
    change-e215a184).
  actual: time.time() at SimTransport.__init__ (_start_time) and
    SimTransport._compute_rpm_response (elapsed time t).
  impact: A wall-clock step (NTP correction after boot, issue-b9ee7428) shifts
    the phase of the simulated RPM sweep. Simulation only; no effect on real
    transports.
  workaround: None needed for normal use.
environment:
  python_version: 3.9+
  os: Linux, macOS
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: sim_transport.py was out of scope for change-e215a184.
  technical_notes: _start_time is read only by _compute_rpm_response as the
    subtrahend of the elapsed time; no reader interprets it as a wall-clock time.
    Both sites can therefore switch to time.monotonic().
  related_issues:
  - issue_ref: issue-e215a184
    relationship: related
  - issue_ref: issue-b9ee7428
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: Switch both sites to time.monotonic(); add a clock-step regression test.
  change_ref: change-72f95f73
  resolved_date: '2026-10-14'
  resolved_by: engine loop, Mistral API (change-72f95f73, commit ae1ea9f)
  fix_description: ''
verification:
  verified_date: '2026-10-14'
  verified_by: William Watson
  test_results: Engine run 1e00fd66 SHIP after one cycle (syntax PASS, pytest
    PASS); full suite 583 passed; operator acceptance 163aaf8.
  closure_notes: Closed. The worker left three helper files in tests/ (removed
    before acceptance); recorded for the framework backlog.
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - grep shows no time.time() in sim_transport.py; pytest passes.
  verification_results: No time.time() in sim_transport.py; 583 passed.
traceability:
  design_refs:
  - ''
  change_refs:
  - change-72f95f73
  test_refs:
  - ''
notes: ai/task.md entry "sim_transport.py computes elapsed time with time.time()".
  Implemented by an engine loop run on the Mistral API, which also serves as the
  live validation of framework change-7d953510 (api_key_keychain).
loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ''
  last_review_feedback: ''
version_history:
- version: '1.0'
  date: '2026-10-14'
  author: William Watson
  changes:
  - Initial issue document, raised from ai/task.md.
- version: '1.1'
  date: '2026-10-14'
  author: William Watson
  changes:
  - Resolved by change-72f95f73 (ae1ea9f); verified; closed.
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
| 1.0 | 2026-10-14 | Initial issue document, raised from ai/task.md. |
| 1.1 | 2026-10-14 | Resolved by change-72f95f73; verified; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
