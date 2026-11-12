# Issue: Engine Off Shown as DISCONNECTED

Created: 2026 November 12

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-b29cbd71"
  title: "With the adapter connected and the vehicle not answering (ignition off), the display shows DISCONNECTED instead of an engine-off state"
  date: "2026-11-12"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-b29cbd71"
    change_iteration: 1

source:
  origin: "test_result"
  test_ref: "test-71ab3751-device-session-a"
  description: "Observed at device session A, step A7 (2026-11-12), with the emulator's engineoff scenario. Recorded in ai/task.md as new work."

affected_scope:
  components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication (callback wiring)"
      file_path: "src/gtach/app.py"
  designs:
    - "design-e5f6a7b8-component_comm_obd_protocol (v1.1, section 6.3)"
    - "design-b8c9d0e1-component_display_manager (v1.3, section 5.4)"
  version: "0.5.0"

reproduction:
  prerequisites: "Pi with GTach 0.5.0; ELM327 emulator on Bluetooth."
  steps:
    - "Run the emulator with the engineoff scenario (test-71ab3751-device-session-a section 3.0, 'Emulator engine off')."
    - "Let GTach connect."
  frequency: "Always"
  reproducibility_conditions: "Adapter connected and answering; vehicle not answering 0100."
  test_data: >
    0100 answers 'SEARCHING... UNABLE TO CONNECT', then 'NO DATA' or
    'BUS INIT:ERROR'. OBDProtocol logs 'Vehicle not answering' and
    retries initialisation. No sample reaches the queue, so
    DisplayManager._link_lost() returns True and the DISCONNECTED
    screen is shown although the Bluetooth link is up.
    From source: once polling has started, an ignition switched off
    mid-drive gives 010C replies without a sample; the poll loop never
    re-sends 0100, so the protocol does not classify the vehicle as
    silent, and the display shows DISCONNECTED after
    LINK_LOSS_TIMEOUT.
  error_output: "None (behaviour, not an error)."

behavior:
  expected: "Adapter connected and reporting a silent vehicle: gauge at zero, 'Engine off' in place of the RPM figure, yellow status dot. Any doubt about the adapter still resolves to DISCONNECTED."
  actual: "DISCONNECTED, with Setup and Reset buttons, as for a lost adapter."
  impact: "A parked car with the adapter powered reads as a fault; the operator cannot tell a silent vehicle from a lost adapter."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "The display has two link signals, transport state and sample age, and no signal from the protocol. OBDProtocol knows the vehicle is silent (_vehicle_silent) but does not expose it, and does not re-check the vehicle when samples stop during polling."
  technical_notes: >
    A timeout (no reply) is not evidence of a silent vehicle: an
    adapter that loses power without closing its socket also times
    out. Only an adapter reply without 4100 counts
    (design-e5f6a7b8 section 6.3.1).
    An engine stalled with the ignition on is expected to answer 010C
    with 0 RPM and stay on the live gauge. Confidence: medium; to be
    confirmed in the deferred in-car test.
  related_issues:
    - issue_ref: "issue-4d9e2f18"
      relationship: "related; introduced _link_lost and the DISCONNECTED condition"
    - issue_ref: "issue-146491ba"
      relationship: "related; lost link during initialisation is not a silent vehicle"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-b29cbd71."
  change_ref: "change-b29cbd71"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Unit tests for the evidence rule and the display precedence."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source and session A notes. [DONE, 2026-11-12.]"
    - "After the fix: unit tests per change-b29cbd71."
    - "After the fix: device check with the emulator — engineoff at connect; car scenario; emulator stopped (adapter lost)."
  verification_results: ""

traceability:
  design_refs:
    - "design-e5f6a7b8-component_comm_obd_protocol"
    - "design-b8c9d0e1-component_display_manager"
  change_refs:
    - "change-b29cbd71"
  test_refs:
    - "test-71ab3751-device-session-a"

notes: "Ignition off mid-drive cannot be produced with the emulator while running; covered by unit tests and the in-car test."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Initial issue document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial issue document. |

---

Copyright (c) 2026 William Watson. MIT License.
