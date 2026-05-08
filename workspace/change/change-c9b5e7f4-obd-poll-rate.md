Created: 2026 May 08

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-c9b5e7f4"
  title: "Make OBD poll interval configurable; reduce default to 50ms"
  date: "2026-05-08"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c9b5e7f4"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-c9b5e7f4"
  description: >
    Hard-coded 100ms poll sleep limits RPM update rate to 10 Hz regardless
    of transport capability.

scope:
  summary: >
    Add poll_interval_s parameter to OBDProtocol. Replace fixed sleep(0.1)
    with sleep(self.poll_interval_s). Pass transport-appropriate value from
    app.py.
  affected_components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "GTachApplication._start_obd"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs:
    - design_ref: ""
      sections: []
  out_of_scope:
    - "Transport layer"
    - "Display manager"
    - "Thread management"

rational:
  problem_statement: >
    Fixed 10 Hz poll rate produces stepped RPM display. SimTransport and TCP
    transport can respond in under 5ms; RFCOMM typically 30-80ms. The floor
    should be set per transport, not globally.
  proposed_solution: >
    poll_interval_s parameter with default 0.05s (20 Hz floor). Sim and TCP
    transports pass 0.02s (50 Hz floor). Real RFCOMM uses default.
  alternatives_considered:
    - option: "Remove sleep entirely — let transport RTT govern rate"
      reason_rejected: >
        SimTransport has near-zero RTT. Without a floor the loop would run
        at hundreds of Hz, consuming CPU and flooding the message queue
        unnecessarily.
  benefits:
    - "Sim/TCP mode approaches 50 Hz RPM update rate — visibly smoother sweep."
    - "RFCOMM mode unchanged — no risk of overloading adapter."
    - "Configurable without code change for future transports."
  risks:
    - risk: "Higher poll rate on Pi Zero 2W increases CPU load."
      mitigation: >
        50 Hz at <5ms SimTransport RTT is 25% duty cycle for the OBD thread.
        Pi Zero 2W has measured idle headroom well above this. RFCOMM at
        30-80ms RTT produces 12-30 Hz naturally, well below 50 Hz.

technical_details:
  current_behavior: "time.sleep(0.1) unconditionally at end of inner polling loop."
  proposed_behavior: "time.sleep(self.poll_interval_s) where interval is set per transport."
  implementation_approach: >
    Three edits:
    1. OBDProtocol.__init__: add poll_interval_s=0.05 parameter; store as self.poll_interval_s.
    2. OBDProtocol._protocol_loop: replace time.sleep(0.1) with time.sleep(self.poll_interval_s).
    3. GTachApplication._start_obd: pass poll_interval_s=0.02 for simbt/simtcp/tcp transports.
  code_changes:
    - component: "OBDProtocol.__init__"
      file: "src/gtach/comm/obd.py"
      change_summary: "Add poll_interval_s=0.05 parameter"
      functions_affected:
        - "__init__"
      classes_affected:
        - "OBDProtocol"
    - component: "OBDProtocol._protocol_loop"
      file: "src/gtach/comm/obd.py"
      change_summary: "Replace sleep(0.1) with sleep(self.poll_interval_s)"
      functions_affected:
        - "_protocol_loop"
      classes_affected:
        - "OBDProtocol"
    - component: "GTachApplication._start_obd"
      file: "src/gtach/app.py"
      change_summary: "Pass poll_interval_s=0.02 for sim and TCP transports"
      functions_affected:
        - "_start_obd"
      classes_affected:
        - "GTachApplication"
  interface_changes:
    - interface: "OBDProtocol.__init__"
      change_type: "signature"
      details: "Add poll_interval_s=0.05 keyword argument. Existing callers unaffected."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "GTachApplication._start_obd"
      impact: "Needs to pass appropriate poll_interval_s per transport type."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Manual test on Pi. Log TX:010C frequency counting."
  test_cases:
    - scenario: "simbt transport"
      expected_result: "TX:010C appears at ~40-50 Hz in log. RPM sweep visibly smoother."
    - scenario: "tcp transport"
      expected_result: "TX:010C at ~40-50 Hz."
    - scenario: "RFCOMM transport (real hardware)"
      expected_result: "TX:010C rate governed by adapter RTT, ~12-30 Hz. No errors."
  regression_scope:
    - "Normal RFCOMM session with real OBD adapter"
    - "SimBT session"
  validation_criteria:
    - "No queue full errors in log"
    - "RPM sweep in sim mode noticeably smoother"
    - "No RFCOMM timeout errors"

implementation:
  implementation_steps:
    - step: "Edit OBDProtocol.__init__ — add poll_interval_s parameter"
      owner: "Claude Code"
    - step: "Edit _protocol_loop — replace sleep constant"
      owner: "Claude Code"
    - step: "Edit GTachApplication._start_obd — pass interval per transport"
      owner: "Claude Code"
  rollback_procedure: "Revert src/gtach/comm/obd.py and src/gtach/app.py."
  deployment_notes: "Rebuild wheel and deploy to Pi."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-c9b5e7f4"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial change document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
