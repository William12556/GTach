Created: 2026 October 09

# Change: SimTransport Observes drop_link

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-50bf25ad"
  title: "Override drop_link in SimTransport so a dropped link is observed and reconnected in simulation"
  date: "2026-10-09"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-50bf25ad"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-50bf25ad"
  description: "Resolves issue-50bf25ad."

scope:
  summary: "SimTransport.drop_link clears _connected, then delegates to OBDTransport.drop_link; the strict xfail on the link-loss lifecycle test is removed."
  affected_components:
    - name: "SimTransport"
      file_path: "src/gtach/comm/sim_transport.py"
      change_type: "modify"
    - name: "TestLinkLoss.test_drop_is_observed_and_link_reconnects"
      file_path: "tests/test_lifecycle_sim.py"
      change_type: "modify"
    - name: "SimTransport drop_link unit tests"
      file_path: "tests/test_sim_transport.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "OBDTransport.drop_link and the real transports (RFCOMM, TCP, serial)."
    - "SimTransport.connect clearing _shutdown (existing behaviour)."
    - "The time.time() elapsed-time sites in sim_transport.py (issue-e215a184 scope decision, 2026-10-09)."

rational:
  problem_statement: >
    See issue-50bf25ad. SimTransport keeps its own _connected flag and
    reads it in is_connected(), but inherits OBDTransport.drop_link
    (transport.py:458 at ba661d4), which sets only _state, the handle
    and the cause. _connected stays True, so the drop is never observed
    and reconnect_indefinitely never reconnects.
  proposed_solution: >
    Add SimTransport.drop_link(self, cause: Optional[str] = None) -> None.
    Under self._lock set self._connected = False. After releasing the
    lock, call super().drop_link(cause), which records the cause
    (default _SILENT_LINK_CAUSE), sets _state to DISCONNECTED, tolerates
    the None handle and logs. Do not set _shutdown: reconnection must
    remain possible (the distinction drop_link documents). Remove the
    strict xfail marker from
    TestLinkLoss.test_drop_is_observed_and_link_reconnects.
  alternatives_considered:
    - option: "Derive is_connected from _state."
      reason_rejected: "Changes connect, disconnect and the state property of SimTransport together; the override is local to the defect."
    - option: "Clear _connected inside the lock while calling super().drop_link."
      reason_rejected: "super().drop_link logs; logging under the lock breaches CLAUDE.md §4 rule 8."
  benefits:
    - "Link-loss recovery (change-9c2f41d8, change-907de6de) becomes testable with simtcp and simbt."
  risks:
    - risk: "Sim sessions that call drop_link now actually disconnect and re-initialise."
      mitigation: "That is the intended behaviour; SimTransport.connect succeeds at once and OBDProtocol re-initialises with ATZ, which the simulator answers immediately."
    - risk: "Brief window in which is_connected() is False but _state is still CONNECTED."
      mitigation: "SimTransport.state is derived from is_connected(), so observers see DISCONNECTED from the first assignment."

technical_details:
  current_behavior: "drop_link() on SimTransport leaves is_connected() True; nothing reconnects."
  proposed_behavior: "drop_link() makes is_connected() False and state DISCONNECTED, records the cause, leaves _shutdown clear; reconnect_indefinitely reconnects after retry_delay."
  implementation_approach: "One method override; no change to the base class."
  code_changes:
    - component: "SimTransport"
      file: "src/gtach/comm/sim_transport.py"
      change_summary: "Add drop_link override."
      functions_affected:
        - "drop_link"
      classes_affected:
        - "SimTransport"
  data_changes: []
  interface_changes:
    - interface: "SimTransport.drop_link"
      change_type: "contract"
      details: "Now honours the OBDTransport.drop_link contract; signature unchanged."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "OBDTransport.drop_link"
      impact: "Called via super(); unchanged."
  external: []
  required_changes:
    - change_ref: "change-04c18cda"
      relationship: "blocks. Implement this change first; both remove a strict xfail in tests/test_lifecycle_sim.py."

testing_requirements:
  test_approach: "Remove the xfail; add unit tests for the override."
  test_cases:
    - scenario: "tests/test_lifecycle_sim.py::TestLinkLoss::test_drop_is_observed_and_link_reconnects without the xfail marker."
      expected_result: "Passes."
    - scenario: "connect(); drop_link('test cause'); read is_connected(), state, last_failure_cause and _shutdown.is_set()."
      expected_result: "False, TransportState.DISCONNECTED, 'test cause', False."
    - scenario: "connect(); drop_link() with no cause."
      expected_result: "last_failure_cause equals the base default (transport._SILENT_LINK_CAUSE)."
    - scenario: "drop_link() then connect()."
      expected_result: "connect() returns True and is_connected() is True."
  regression_scope:
    - "tests/test_lifecycle_sim.py (all classes)."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "Add the override; add tests/test_sim_transport.py; remove the xfail marker."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

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
    - change_ref: "change-9c2f41d8"
      relationship: "related. Link-loss recovery."
    - change_ref: "change-907de6de"
      relationship: "related. Reconnect path."
    - change_ref: "change-04c18cda"
      relationship: "blocks"
  related_issues:
    - issue_ref: "issue-50bf25ad"
      relationship: "resolves"

notes: "Line numbers are from ba661d4; locate code by symbol."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-50bf25ad iteration 1."

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
| 1.0 | 2026-10-09 | Initial change document resolving issue-50bf25ad iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
