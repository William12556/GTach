Created: 2026 October 07

# Issue: OBD Settle Sleep Without Heartbeat

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-04c18cda
  title: OBDProtocol._initialize_protocol sleeps 1.5 s with time.sleep and no heartbeat
    when the adapter is pre-initialised
  date: '2026-10-07'
  reporter: Claude Code
  status: open
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-04c18cda
    change_iteration: 1
source:
  origin: test_result
  test_ref: tests/test_lifecycle_sim.py::TestWatchdogQuiet::test_no_obd_unresponsive_warning
    (strict xfail)
  description: Found by the audit-36b6ea95 Phase 4 SimTransport lifecycle test (commit
    34c1ffd).
affected_scope:
  components:
  - name: OBDProtocol._initialize_protocol
    file_path: src/gtach/comm/obd.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: adapter_pre_initialised=True (the post-setup path in app._start_obd).
  steps:
  - Start OBDProtocol with adapter_pre_initialised=True under a WatchdogMonitor
    with warning_timeout=1.0.
  - Wait 2 s.
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: 'WARNING WatchdogMonitor: Thread obd_protocol appears unresponsive
    (timeout: 1.0s)'
behavior:
  expected: No heartbeat gap above the per-command bound; a stop request ends the
    wait at once.
  actual: A 1.5 s gap without heartbeat at obd.py:148; the sleep ignores shutdown_event,
    so a stop during it waits the full 1.5 s.
  impact: Below the production 15 s warning timeout, so no warning on the device
    today; it is the largest heartbeat gap in normal operation and delays stop.
  workaround: None needed with production timeouts.
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: time.sleep(1.5) between two update_heartbeat calls (obd.py:146-149),
    not shutdown_event.wait.
  technical_notes: change-860fd5f7 bounded heartbeat gaps per command; this sleep
    is outside a command.
  related_issues:
  - issue_ref: issue-860fd5f7
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: Replace the sleep with shutdown_event.wait(1.5) (returning early when
    set) and heartbeat before it; remove the xfail marker.
  change_ref: change-04c18cda
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
  - tests/test_lifecycle_sim.py::TestWatchdogQuiet::test_no_obd_unresponsive_warning
    passes without the xfail marker.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-04c18cda
  test_refs:
  - tests/test_lifecycle_sim.py::TestWatchdogQuiet::test_no_obd_unresponsive_warning
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
- version: '1.1'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Coupled to change-04c18cda (P03.7). The change supersedes resolution.approach (a single 1.5 s wait leaves a gap above the test's 1.0 s warning timeout).
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
| 1.1 | 2026-10-09 | Coupled to change-04c18cda; resolution approach superseded by the change. |

---

Copyright (c) 2026 William Watson. MIT License.
