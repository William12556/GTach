# Change: Simulation RPM Alignment

Created: 2026 November 24

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-0b3317b7"
  title: "One shared sim_rpm(t) sweep, 800-6600 RPM with a 15 s period, for startup simulation and OPTIONS simulation mode"
  date: "2026-11-24"
  author: "William Watson"
  status: "implemented"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-0b3317b7"
    issue_iteration: 1
    prompt_ref: "prompt-0b3317b7"

source:
  type: "issue"
  reference: "issue-0b3317b7"
  description: "Align the two synthetic RPM generators through one shared function (operator decision 2026-11-24, option B)."

scope:
  summary: >
    Add a module-level function sim_rpm(t) to comm/sim_transport.py that
    returns 800 + 2900 * (1 + sin(t * 2π / 15)). SimTransport and the
    DisplayManager simulation mode both call it. Update the two RPM-value
    assertions in tests/test_sim_transport.py and add tests for sim_rpm.
  affected_components:
    - name: "SimTransport / sim_rpm"
      file_path: "src/gtach/comm/sim_transport.py"
      change_type: "modify"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "SimTransport tests"
      file_path: "tests/test_sim_transport.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-7d3e9f5a-domain_comm"
      sections:
        - "SimTransport description (sim_rpm named as the sweep definition)"
  out_of_scope:
    - "Replacing the transport at runtime when the OPTIONS toggle is used."
    - "Signal conditioning (_condition_rpm), band hysteresis and gauge scaling."
    - "The encoding of 010C responses, the ELM327 init responses and all other SimTransport behaviour."
    - "Moving or removing the OPTIONS simulation mode control."

rational:
  problem_statement: "Two formulas produce different sweeps (800-6500 RPM / 60 s against 0-6000 RPM / 6.3 s), and the OPTIONS variant uses the wall clock."
  proposed_solution: "One function holds the sweep; both paths call it with a monotonic time base."
  alternatives_considered:
    - option: "Swap to SimTransport at runtime when the OPTIONS toggle is used"
      reason_rejected: "Needs supervisor thread teardown and restart, reference rewiring in the OBD layer and display-to-app coupling; operator chose alignment only."
    - option: "Duplicate the aligned expression in both files (option A)"
      reason_rejected: "Leaves two definitions that can drift apart again."
  benefits:
    - "Identical sweep in both modes; a future range or period change is made once."
    - "OPTIONS simulation mode no longer depends on the wall clock (consistent with issue-72f95f73)."
  risks:
    - risk: "Circular import: comm.pairing and comm.sim_bluetooth import display.setup_models."
      mitigation: "DisplayManager imports sim_rpm inside the simulation-mode branch, following the existing function-local comm import at manager.py line 2374. After the first frame this is a sys.modules lookup."
    - risk: "Peak slope rises to about 1215 RPM/s (four times the previous transport sweep), so conditioning and band hysteresis visibly lag the sweep."
      mitigation: "Expected behaviour, not a defect; recorded here so device observations are read correctly."
    - risk: "6600 RPM exceeds the abarth_595_turismo redline and rpm_warning (6500); every sweep enters the top band."
      mitigation: "Intended by the operator. gauge_full_scale() has a 7000 RPM floor, so the needle is not clipped on any profile."

technical_details:
  current_behavior: >
    sim_transport.py line 161: rpm = 800 + 2850 * (1 + math.sin(t * 2 * math.pi / 60.0)),
    t = time.monotonic() - self._start_time. manager.py line 1252:
    rpm = int(3000 + 3000 * math.sin(time.time())).
  proposed_behavior: >
    Both paths: rpm = sim_rpm(t) = 800 + 2900 * (1 + sin(t * 2π / 15)),
    range 800-6600 RPM, 15 s period. SimTransport passes its elapsed
    monotonic time (sweep starts at the 3700 RPM midpoint and rises);
    DisplayManager passes time.monotonic() (phase not significant).
  implementation_approach: >
    C1. comm/sim_transport.py: add module-level constants SIM_RPM_MIN = 800,
    SIM_RPM_MAX = 6600, SIM_RPM_PERIOD_S = 15.0 and a function
    sim_rpm(t: float) -> float returning
    SIM_RPM_MIN + (SIM_RPM_MAX - SIM_RPM_MIN) / 2 * (1 + math.sin(t * 2 * math.pi / SIM_RPM_PERIOD_S)),
    with a Google-style docstring citing change-0b3317b7.
    C2. SimTransport._compute_rpm_response: rpm = sim_rpm(time.monotonic() - self._start_time);
    encoding unchanged. Update the class docstring (line 28), the _handle_command
    comment (line 144) and the _compute_rpm_response comments (lines 157-159)
    to 800-6600 RPM, 15 s period, start at the 3700 RPM midpoint.
    C3. DisplayManager._draw_radial_mode, simulation branch: inside the
    branch, from ..comm.sim_transport import sim_rpm; then
    rpm = int(sim_rpm(time.monotonic())). The following two lines
    (self._last_rpm = rpm; rpm = self._condition_rpm(rpm)) are unchanged.
    C4. tests/test_sim_transport.py: test_rpm_sweep_uses_monotonic_clock
    expects "41 0C 39 D0" (t = 0, 3700 RPM). test_rpm_sweep_ignores_wall_clock_steps:
    the second monotonic value becomes 1003.75 (t = 3.75 s, quarter period,
    6600 RPM) and the expectation "41 0C 67 20"; update its comment.
    t = 15 s must not be used, since it equals t = 0 for a 15 s period
    (the defect class recorded in audit-fccd5931 F2).
    C5. tests/test_sim_transport.py: add tests for sim_rpm: values at
    t = 0, 3.75, 11.25 s are 3700, 6600, 800; sampled over one period the
    range stays within [800, 6600]; sim_rpm(t) == sim_rpm(t + 15).
    Add 0b3317b7 to the module docstring.
  code_changes:
    - component: "sim_transport"
      file: "src/gtach/comm/sim_transport.py"
      change_summary: "C1, C2"
      functions_affected:
        - "sim_rpm (new)"
        - "SimTransport._compute_rpm_response"
      classes_affected:
        - "SimTransport (docstring only)"
    - component: "display manager"
      file: "src/gtach/display/manager.py"
      change_summary: "C3"
      functions_affected:
        - "DisplayManager._draw_radial_mode"
      classes_affected: []
    - component: "tests"
      file: "tests/test_sim_transport.py"
      change_summary: "C4, C5"
      functions_affected:
        - "test_rpm_sweep_uses_monotonic_clock"
        - "test_rpm_sweep_ignores_wall_clock_steps"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "gtach.comm.sim_transport.sim_rpm"
      change_type: "signature"
      details: "New public function sim_rpm(t: float) -> float and three module constants."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "DisplayManager"
      impact: "Depends on gtach.comm.sim_transport.sim_rpm (function-local import)."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests in tests/test_sim_transport.py; full suite; device check of both modes."
  test_cases:
    - scenario: "SimTransport at elapsed t = 0"
      expected_result: "'41 0C 39 D0' (3700 RPM); time.time() not called."
    - scenario: "SimTransport at elapsed t = 3.75 s with a wall-clock step"
      expected_result: "'41 0C 67 20' (6600 RPM); time.time() not called."
    - scenario: "sim_rpm at t = 0, 3.75, 11.25 s"
      expected_result: "3700, 6600, 800 (within 1e-6)."
    - scenario: "sim_rpm sampled over one period"
      expected_result: "All values within [800, 6600]."
    - scenario: "sim_rpm periodicity"
      expected_result: "sim_rpm(t) equals sim_rpm(t + 15) within 1e-6."
  regression_scope:
    - "tests/test_sim_transport.py"
    - "tests/test_lifecycle_sim.py"
    - "tests/test_rpm_signal_conditioning.py, tests/test_connecting_indicator.py, tests/test_engine_off_state.py (set _sim_mode = True)"
    - "tests/test_monotonic_durations.py (patches time.time)"
  validation_criteria:
    - "SDL_VIDEODRIVER=dummy pytest tests/ passes."
    - "mypy src/ reports no new issues; black, isort and flake8 clean on changed src/ files."
    - "On gtach.local: simtcp startup and OPTIONS simulation mode both sweep 800-6600 RPM in about 15 s."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "C1-C5 per prompt-0b3317b7"
      owner: "Worker (profile per prompt-0b3317b7)"
    - step: "Planner review of the diff"
      owner: "Planner"
    - step: "Device check on gtach.local"
      owner: "William Watson"
    - step: "Update design-7d3e9f5a SimTransport description to name sim_rpm"
      owner: "Planner"
  rollback_procedure: "git revert of the implementation commit."
  deployment_notes: "No configuration change."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates:
    - design_ref: "design-7d3e9f5a-domain_comm"
      sections_updated:
        - "SimTransport description"
      update_date: ""
  related_changes:
    - change_ref: "change-72f95f73"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-72f95f73"
      relationship: "related"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-11-24"
    author: "William Watson"
    changes:
      - "Initial change."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-24 | Initial change |

---

Copyright (c) 2026 William Watson. MIT License.
