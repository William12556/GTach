Created: 2026 October 09

# Change: Bounded EBUSY Retry in Post-Pairing OBD Verify

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-d26ca557"
  title: "verify_obd_connection retries the RFCOMM connect, a bounded number of times, only when it fails with the link-busy cause"
  date: "2026-10-09"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-d26ca557"
    issue_iteration: 1

source:
  type: "issue"
  reference: "ai/workspace/issues/issue-d26ca557-obd-verify-ebusy-after-pairing.md"
  description: >
    The post-pairing OBD verify opens RFCOMM about 2 ms after pairing
    completes and intermittently fails with EBUSY; the operator must tap
    the device again.

scope:
  summary: >
    In verify_obd_connection, when connect() fails and the transport's
    last_failure_cause is the link-busy cause, wait briefly and retry, up
    to three attempts in total. Any other failure returns False at once,
    as now. Expose the link-busy cause string as a public constant in
    transport.py so the comparison does not duplicate the literal.
  affected_components:
    - name: "BluetoothSetupInterface.verify_obd_connection"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "LINK_BUSY_CAUSE constant (new) and _CONNECT_FAULT_CAUSES"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "Regression tests (new)"
      file_path: "tests/test_obd_verify_busy_retry.py"
      change_type: "add"
  affected_designs:
    - design_ref: ""
      sections:
        - ""
  out_of_scope:
    - "start_device_probe and the main transport's first connect after setup."
    - "Recovery from a persistent EBUSY state after link loss (separate task.md item, issue-5e7a03c4)."
    - "Suppressing the RFCOMMTransport ERROR line logged for each busy attempt."
    - "Confirming the ACL-teardown mechanism with btmon."

rational:
  problem_statement: >
    Pairing succeeds and the device is saved, then the RFCOMM connect
    within milliseconds returns EBUSY ('bluetooth link busy - may need
    reset'). Setup returns to Select Device. A retry 7 s later succeeds.
    The cause is inferred (ACL link still held after pairing), not
    confirmed.
  proposed_solution: >
    Retry only the classified link-busy failure: up to
    _VERIFY_BUSY_ATTEMPTS = 3 attempts, _VERIFY_BUSY_RETRY_DELAY_S = 1.0 s
    apart, logging each retry at INFO. The adapter-absent override in
    _classify_connect_error yields a different cause, so a missing
    controller is not retried. Three attempts stay below the transport's
    six-failure wedge escalation.
  alternatives_considered:
    - option: "Fixed settle delay between pairing and the probe."
      reason_rejected: "Adds the delay to every setup, and the required duration is unknown; a cause-conditional retry costs nothing when the link is free."
    - option: "Retry on any connect failure."
      reason_rejected: "A genuine timeout costs up to 10 s per attempt, tripling the wait before the operator sees the failure."
    - option: "Expose the errno from OBDTransport instead of comparing cause strings."
      reason_rejected: "A new property and state field for one caller; the classified cause already carries the information."
  benefits:
    - "Setup completes in one pass when the link frees within ~2 s."
  risks:
    - risk: "If the link stays busy longer than ~2 s the behaviour is unchanged (Retry still needed)."
      mitigation: "Constants are class attributes; on-device verification decides whether tuning is needed."
    - risk: "Up to 2 s extra blocking on the pairing worker thread when the link stays busy."
      mitigation: "The verify path already blocks up to 15 s (connect plus ATZ); the UI thread is not involved."

technical_details:
  current_behavior: >
    verify_obd_connection constructs RFCOMMTransport, calls connect()
    once, and returns False with 'OBD verify: RFCOMM connect failed' if
    it fails.
  proposed_behavior: >
    The connect is attempted up to three times while the failure cause
    equals LINK_BUSY_CAUSE, sleeping 1.0 s between attempts. On success
    the ATZ probe and disconnect run as before. On a non-busy failure, or
    after the last busy attempt, it logs the existing warning and returns
    False.
  implementation_approach: >
    transport.py: define LINK_BUSY_CAUSE = "bluetooth link busy - may need
    reset" above _CONNECT_FAULT_CAUSES and use it for the EBUSY entry (no
    behaviour change). interface.py: add the two class constants; wrap the
    connect in a loop reusing one RFCOMMTransport instance; time.sleep
    between attempts (worker thread; time.sleep is clock-step safe).
  code_changes:
    - component: "transport"
      file: "src/gtach/comm/transport.py"
      change_summary: "Public LINK_BUSY_CAUSE constant; mapping uses it."
      functions_affected: []
      classes_affected: []
    - component: "interface"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: "Bounded busy-only retry around connect()."
      functions_affected:
        - "BluetoothSetupInterface.verify_obd_connection"
      classes_affected:
        - "BluetoothSetupInterface"
  data_changes: []
  interface_changes:
    - interface: "gtach.comm.transport.LINK_BUSY_CAUSE"
      change_type: "contract"
      details: "New public constant; value identical to the existing mapping entry."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "OBDTransport.last_failure_cause"
      impact: "Read after a failed connect; existing property."
  external:
    - library: "BlueZ"
      version_change: "none"
      impact: "none"
  required_changes:
    - change_ref: "change-4f671d09"
      relationship: "related (both modify transport.py and interface.py; implement after change-4f671d09)"

testing_requirements:
  test_approach: "Unit tests with a fake RFCOMMTransport and patched time.sleep; on-device re-pairing by the operator."
  test_cases:
    - scenario: "First connect fails with LINK_BUSY_CAUSE, second succeeds; ATZ returns a non-empty reply."
      expected_result: "True; two connects; one sleep of 1.0 s; disconnect called."
    - scenario: "Connect fails with 'connection timed out'."
      expected_result: "False; one connect; no sleep."
    - scenario: "Connect fails with LINK_BUSY_CAUSE three times."
      expected_result: "False; three connects; two sleeps."
    - scenario: "transport.LINK_BUSY_CAUSE equals _CONNECT_FAULT_CAUSES[errno.EBUSY]."
      expected_result: "Equal."
  regression_scope:
    - "tests/ (full suite)"
  validation_criteria:
    - "pytest tests/ passes."
    - "On gtach.local: re-pair several times; setup completes without Retry each time."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "Implement per prompt-d26ca557, after prompt-4f671d09."
      owner: "Claude Code"
    - step: "Re-pair on gtach.local several times."
      owner: "William Watson"
  rollback_procedure: "git revert the implementing commit."
  deployment_notes: "Normal wheel deploy."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found:
    - issue_ref: ""

traceability:
  design_updates:
    - design_ref: ""
      sections_updated:
        - ""
      update_date: ""
  related_changes:
    - change_ref: "change-5e7a03c4"
      relationship: "related (introduced connect-error classification)"
    - change_ref: "change-4f671d09"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-d26ca557"
      relationship: "source"

notes: "Retry count and delay are an initial choice without btmon evidence of how long the link stays busy; adjust after on-device verification if needed. Line numbers are from b464bee; locate code by symbol."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document from issue-d26ca557 iteration 1."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Dependency note: interface.py is also modified by change-4f671d09."

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
| 1.0 | 2026-10-09 | Initial change document from issue-d26ca557 iteration 1. |
| 1.1 | 2026-10-09 | Dependency note: interface.py is also modified by change-4f671d09. |

---

Copyright (c) 2026 William Watson. MIT License.
