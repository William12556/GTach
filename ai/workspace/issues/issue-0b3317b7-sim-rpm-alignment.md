# Issue: Simulation RPM Alignment

Created: 2026 November 24

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-0b3317b7"
  title: "Startup simulation and OPTIONS simulation mode sweep RPM with different formulas, so the two modes behave differently"
  date: "2026-11-24"
  reporter: "William Watson"
  status: "resolved"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-0b3317b7"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Observed by the operator: in the startup simulation (simtcp, simbt) RPM
    rises and falls more slowly and peaks higher than in the simulation mode
    selected on OPTIONS page 1. The synthetic RPM is computed in two places
    with different formulas.

affected_scope:
  components:
    - name: "SimTransport"
      file_path: "src/gtach/comm/sim_transport.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs:
    - design_ref: "design-7d3e9f5a-domain_comm (SimTransport)"
    - design_ref: "design-b8c9d0e1-component_display_manager (OPTIONS page 1, simulation mode)"
  version: "1.0.0rc1 (ee64236)"

reproduction:
  prerequisites: "GTach at ee64236."
  steps:
    - "Start gtach with --transport simtcp and watch one sweep."
    - "Start gtach against an adapter or emulator, enable Simulation mode on OPTIONS page 1 and watch one sweep."
  frequency: "always"
  reproducibility_conditions: "Any simulation session."
  preconditions: ""
  test_data: ""
  error_output: "None (behaviour, not an error)."

behavior:
  expected: >
    Both simulation paths produce the same sweep: 800 to 6600 RPM, sine
    wave, one full sweep every 15 s, from one shared definition.
  actual: >
    SimTransport._compute_rpm_response: 800 + 2850 * (1 + sin(t * 2π / 60)),
    800-6500 RPM, 60 s period, monotonic elapsed time. DisplayManager
    _draw_radial_mode in simulation mode: int(3000 + 3000 * sin(time.time())),
    0-6000 RPM, 2π s (about 6.3 s) period, wall clock.
  impact: "The two simulation modes are not comparable; the OPTIONS mode drops to 0 RPM and uses the wall clock."
  workaround: "None."

environment:
  python_version: "3.9+"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "The OPTIONS simulation mode (prompt-f3e2d1c0) added its own synthetic RPM expression in the display layer instead of reusing the SimTransport sweep."
  technical_notes: >
    The OPTIONS mode bypasses the transport and OBD parser; only the RPM
    value is synthetic. Replacing the transport at runtime was considered
    and rejected by the operator (2026-11-24): reconnect_indefinitely loops
    on _shutdown, which disconnect() sets permanently, so a swap would need
    a new transport and supervisor thread per toggle. Option chosen: one
    shared sim_rpm(t) function used by both paths.
  related_issues:
    - issue_ref: "issue-72f95f73"
      relationship: "related"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "change-0b3317b7"
  change_ref: "change-0b3317b7"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "One definition of the synthetic sweep, covered by a unit test."
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "pytest tests/ passes."
    - "On gtach.local: the simtcp startup sweep and the OPTIONS simulation mode both sweep 800-6600 RPM in about 15 s."
  verification_results: ""

traceability:
  design_refs:
    - "design-7d3e9f5a-domain_comm"
    - "design-b8c9d0e1-component_display_manager"
  change_refs:
    - "change-0b3317b7"
  test_refs: []

notes: ""

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-24"
    author: "William Watson"
    changes:
      - "Initial issue."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "issue"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-24 | Initial issue |

---

Copyright (c) 2026 William Watson. MIT License.
