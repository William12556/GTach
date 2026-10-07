Created: 2026 October 07

# Issue: SimTransport Link Drop Not Observed

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-50bf25ad
  title: SimTransport.is_connected ignores drop_link, so link loss and reconnection
    cannot be exercised with the simulator
  date: '2026-10-07'
  reporter: Claude Code
  status: open
  severity: medium
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: ''
    change_iteration: null
source:
  origin: test_result
  test_ref: tests/test_lifecycle_sim.py::TestLinkLoss::test_drop_is_observed_and_link_reconnects
    (strict xfail)
  description: Found by the audit-36b6ea95 Phase 4 SimTransport lifecycle test (commit
    34c1ffd).
affected_scope:
  components:
  - name: SimTransport
    file_path: src/gtach/comm/sim_transport.py
  - name: OBDTransport.drop_link
    file_path: src/gtach/comm/transport.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: SimTransport connected.
  steps:
  - Start SimTransport.reconnect_indefinitely and OBDProtocol as app.py does.
  - Call transport.drop_link().
  - Read transport.is_connected().
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: is_connected() is False after drop_link(); reconnect_indefinitely reconnects
    after retry_delay; OBDProtocol re-initialises.
  actual: is_connected() stays True; the drop is never observed and nothing reconnects.
  impact: Link-loss recovery (issue-9c2f41d8, change-907de6de) cannot be tested
    with the documented simulation transport (CLAUDE.md §6); simtcp/simbt sessions
    never exercise the DISCONNECTED path through drop_link.
  workaround: None in code; the real transports (RFCOMM, TCP, serial) are unaffected.
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: SimTransport keeps its own _connected flag (sim_transport.py:61-69)
    and overrides connect/disconnect/is_connected, but inherits OBDTransport.drop_link
    (transport.py:416), which sets only _state and the handle. _connected is never
    cleared.
  technical_notes: SimTransport.state is derived from is_connected(), so it also
    stays CONNECTED.
  related_issues:
  - issue_ref: issue-860fd5f7
    relationship: related
  - issue_ref: issue-907de6de
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: Override drop_link in SimTransport (clear _connected and _state under
    _lock, record the cause), or derive is_connected from _state; remove the xfail
    marker from the lifecycle test.
  change_ref: ''
  resolved_date: ''
  resolved_by: ''
  fix_description: ''
verification:
  verified_date: ''
  verified_by: ''
  test_results: ''
  closure_notes: ''
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - tests/test_lifecycle_sim.py::TestLinkLoss::test_drop_is_observed_and_link_reconnects
    passes without the xfail marker.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - ''
  test_refs:
  - tests/test_lifecycle_sim.py::TestLinkLoss::test_drop_is_observed_and_link_reconnects
    (strict xfail)
notes: Raised from test_result per P03.1.
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

---

Copyright (c) 2026 William Watson. MIT License.
