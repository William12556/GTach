Created: 2026 October 14

# Change: Monotonic Clock for the SimTransport RPM Sweep

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-72f95f73"
  title: "Use time.monotonic() for the SimTransport RPM sweep's elapsed time"
  date: "2026-10-14"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-72f95f73"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-72f95f73"
  description: "Resolves issue-72f95f73 (sim_transport.py, excluded from change-e215a184)."

scope:
  summary: "Switch SimTransport._start_time and the elapsed-time read in _compute_rpm_response to time.monotonic(); add a clock-step regression test."
  affected_components:
    - name: "SimTransport"
      file_path: "src/gtach/comm/sim_transport.py"
      change_type: "modify"
    - name: "SimTransport tests"
      file_path: "tests/test_sim_transport.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any other file, and any other behaviour of SimTransport (responses, sweep formula, period, range)."
    - "manager.py 'timestamp' and the sin(time.time()) demo value; OBDResponse.timestamp (kept as wall-clock values by change-e215a184)."

rational:
  problem_statement: "See issue-72f95f73. A wall-clock step shifts the phase of the simulated RPM sweep."
  proposed_solution: "_start_time is read only as the subtrahend of the elapsed time, so both sites switch to time.monotonic(); no clocks are mixed."
  alternatives_considered:
    - option: "Leave as is (simulation only)."
      reason_rejected: "Inconsistent with change-4005360c and change-e215a184; the fix is two lines."
  benefits:
    - "Simulated RPM sweep is unaffected by wall-clock steps."
    - "No time.time() duration arithmetic remains in src/gtach/comm/."
  risks:
    - risk: "A reader treats _start_time as an epoch time."
      mitigation: "None exists: grep shows _start_time is read only in _compute_rpm_response."

technical_details:
  current_behavior: "sim_transport.py:38 self._start_time = time.time(); sim_transport.py:158 t = time.time() - self._start_time."
  proposed_behavior: "Both use time.monotonic(). The response for a given elapsed time is unchanged."
  implementation_approach: "Two-line edit with a comment citing issue-72f95f73; one regression test module section."
  code_changes:
    - component: "SimTransport"
      file: "src/gtach/comm/sim_transport.py"
      change_summary: "Clock switch at __init__ and _compute_rpm_response."
      functions_affected:
        - "SimTransport.__init__"
        - "SimTransport._compute_rpm_response"
      classes_affected:
        - "SimTransport"
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-e215a184"
      relationship: "related. Switched the other duration sites."

testing_requirements:
  test_approach: "Replace the time reference in gtach.comm.sim_transport with a fake whose monotonic() is scripted and whose time() fails the test if called."
  test_cases:
    - scenario: "Construct SimTransport and query 010C with monotonic() returning 1000.0 both times."
      expected_result: "Response '41 0C 39 08' (elapsed time 0, 3650 RPM); time.time() not called."
    - scenario: "Construct SimTransport with monotonic() 1000.0, then query 010C with monotonic() 1030.0."
      expected_result: "Response '41 0C 39 08' (elapsed time 30 s, half period, 3650 RPM); time.time() not called."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "grep -n 'time.time()' src/gtach/comm/sim_transport.py returns nothing."
    - "pytest tests/ passes."

implementation:
  effort_estimate: "30 minutes"
  implementation_steps:
    - step: "Edit sim_transport.py; add the tests to tests/test_sim_transport.py."
      owner: "worker and reviewer (engine loop, Mistral API)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None. The engine run also validates framework change-7d953510 live (api_key_keychain through engine-mcp)."

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
    - change_ref: "change-e215a184"
      relationship: "related"
    - change_ref: "change-4005360c"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-72f95f73"
      relationship: "resolves"

notes: "Line numbers are from GTach main bb29226."

version_history:
  - version: "1.0"
    date: "2026-10-14"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-72f95f73 iteration 1."

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
| 1.0 | 2026-10-14 | Initial change document resolving issue-72f95f73 iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
