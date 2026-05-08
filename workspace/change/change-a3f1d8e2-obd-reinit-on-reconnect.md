Created: 2026 May 08

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-a3f1d8e2"
  title: "Skip ATZ on reconnect to eliminate 5-9s RPM data gap"
  date: "2026-05-08"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a3f1d8e2"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-a3f1d8e2"
  description: >
    Full adapter init including ATZ runs on every reconnect, freezing RPM
    display for 5-9 seconds.

scope:
  summary: >
    Add _adapter_initialised flag to OBDProtocol. Skip ATZ when True.
    Reset flag on stop() and on inner loop exit (transport disconnect).
  affected_components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
  affected_designs:
    - design_ref: ""
      sections: []
  out_of_scope:
    - "Transport reconnect logic"
    - "Watchdog or thread management"

rational:
  problem_statement: >
    ATZ is a hardware reset command that takes up to 5 seconds. It is only
    needed at first connect or after adapter power cycle. Running it on every
    socket reconnect produces an unnecessary multi-second data gap.
  proposed_solution: >
    Track whether the adapter has been initialised with an instance flag.
    On reconnect, send only the protocol setup commands (ATE0 onwards).
    Reset the flag only when OBDProtocol is stopped or explicitly reset.
  alternatives_considered:
    - option: "Reduce ATZ timeout from 5s to 1s"
      reason_rejected: "Does not eliminate the gap, only reduces it. ATZ may legitimately need 5s on real hardware."
  benefits:
    - "Reconnect resumes RPM in under 2 seconds instead of 5-9 seconds."
    - "No impact on first-connect behaviour."
  risks:
    - risk: "Adapter may be in unknown state after unexpected disconnect."
      mitigation: >
        ATE0/ATL0/ATS0/ATSP0 are idempotent configuration commands that
        normalise adapter state. 0100 confirms protocol availability.
        This is sufficient for reconnect recovery.

technical_details:
  current_behavior: >
    _initialize_protocol always sends ATZ first, regardless of whether this
    is a first connect or reconnect.
  proposed_behavior: >
    _initialize_protocol checks self._adapter_initialised. If True, skips
    ATZ and proceeds directly to ATE0. If False, sends ATZ, then sets flag
    to True on successful completion.
  implementation_approach: >
    Two targeted edits to obd.py:
    1. Add _adapter_initialised = False in __init__.
    2. In _initialize_protocol, gate ATZ on not self._adapter_initialised;
       set flag to True after successful 0100 response.
    3. Reset _adapter_initialised = False in stop().
    4. Reset _adapter_initialised = False when inner polling loop exits
       due to transport disconnect (add reset after inner while loop).
  code_changes:
    - component: "OBDProtocol.__init__"
      file: "src/gtach/comm/obd.py"
      change_summary: "Add self._adapter_initialised = False"
      functions_affected:
        - "__init__"
      classes_affected:
        - "OBDProtocol"
    - component: "OBDProtocol._initialize_protocol"
      file: "src/gtach/comm/obd.py"
      change_summary: "Gate ATZ on not self._adapter_initialised; set flag on success"
      functions_affected:
        - "_initialize_protocol"
      classes_affected:
        - "OBDProtocol"
    - component: "OBDProtocol.stop"
      file: "src/gtach/comm/obd.py"
      change_summary: "Reset self._adapter_initialised = False"
      functions_affected:
        - "stop"
      classes_affected:
        - "OBDProtocol"
    - component: "OBDProtocol._protocol_loop"
      file: "src/gtach/comm/obd.py"
      change_summary: "Reset self._adapter_initialised = False after inner loop exits"
      functions_affected:
        - "_protocol_loop"
      classes_affected:
        - "OBDProtocol"
  interface_changes: []

dependencies:
  internal:
    - component: "SimTransport"
      impact: "None. SimTransport responds to all AT commands regardless."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Manual test on Pi with simbt. Log inspection."
  test_cases:
    - scenario: "First connect"
      expected_result: "ATZ appears in log. RPM starts within normal init time."
    - scenario: "Reconnect after transport drop"
      expected_result: "ATZ absent from log. RPM resumes within 2 seconds."
    - scenario: "stop() then start() of OBDProtocol"
      expected_result: "ATZ appears again on new start (flag reset by stop)."
  regression_scope:
    - "Normal simbt session"
    - "TCP transport session"
  validation_criteria:
    - "No ATZ in log after first connect"
    - "RPM gap on reconnect under 2 seconds"

implementation:
  implementation_steps:
    - step: "Edit OBDProtocol.__init__ — add _adapter_initialised flag"
      owner: "Claude Code"
    - step: "Edit _initialize_protocol — gate ATZ, set flag on success"
      owner: "Claude Code"
    - step: "Edit stop() — reset flag"
      owner: "Claude Code"
    - step: "Edit _protocol_loop — reset flag after inner loop exits"
      owner: "Claude Code"
  rollback_procedure: "Revert src/gtach/comm/obd.py."
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
    - issue_ref: "issue-a3f1d8e2"
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
