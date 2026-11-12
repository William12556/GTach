# Change: Session B Findings — Reset Retry, Notice Text, Lost-Link Record

Created: 2026 November 12

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-146491ba"
  title: "Retry the post-pairing OBD check on a connection reset; shorten the fallback notice; do not report a lost link as a silent vehicle"
  date: "2026-11-12"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-146491ba"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-146491ba"
  description: "Resolves issue-146491ba (device session B findings F1 to F3)."

scope:
  summary: "Three edits in interface.py, transport.py and obd.py; tests."
  affected_components:
    - name: "BluetoothSetupInterface.verify_obd_connection, FALLBACK_LIST_TEXT"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "LINK_RESET_CAUSE, _CONNECT_FAULT_CAUSES"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "OBDProtocol._initialize_protocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_obd_verify_busy_retry.py, tests/test_session_b_findings.py (new)"
      change_type: "add"
  affected_designs:
    - "design-a3b4c5d6-component_display_setup_manager"
  out_of_scope:
    - "The attempt bound and delay of the verify retry (3 attempts, 1.0 s)."
    - "The other DEVICE_LIST texts, unless the width test shows one does not fit (EDIT B)."
    - "The remaining session B observations (ECONNABORTED, EBADF at ERROR, boot-time connect)."
    - "The engine-off display state."

rational:
  problem_statement: "See issue-146491ba."
  proposed_solution: >
    EDIT A (F1) — transport.py and interface.py.
    (1) transport.py: add the public constant
    LINK_RESET_CAUSE = "connection reset by adapter" and the mapping
    entry _errno.ECONNRESET: LINK_RESET_CAUSE in _CONNECT_FAULT_CAUSES,
    with a comment citing issue-146491ba. No other edit to the file.
    (2) interface.py: verify_obd_connection retries when
    last_failure_cause is LINK_BUSY_CAUSE or LINK_RESET_CAUSE, within
    the existing bound (_VERIFY_BUSY_ATTEMPTS = 3,
    _VERIFY_BUSY_RETRY_DELAY_S = 1.0). The INFO retry record names the
    cause: 'OBD verify: <cause>, retrying (attempt n/3)'. Any other
    cause returns False after one attempt, as now. The class comment
    names both causes.

    EDIT B (F2) — interface.py.
    FALLBACK_LIST_TEXT becomes "No ELM327 found" if it renders at
    220 px or less in get_label_small_font(); otherwise "No ELM327".
    The device list itself shows that all devices are offered.
    A parametrised test asserts that every DEVICE_LIST error-line
    constant (SCAN_FAILED_TEXT, FALLBACK_LIST_TEXT,
    DEVICE_NOT_SAVED_TEXT, OBD_CHECK_FAILED_TEXT) renders at 220 px or
    less in that font. If a constant other than FALLBACK_LIST_TEXT
    fails, it is not changed: its case is marked xfail with the
    measured width and the report lists it.

    EDIT C (F3) — obd.py, _initialize_protocol.
    When the 0100 reply is None and the transport is no longer
    connected, log 'Link lost during initialisation' at DEBUG and
    return False without calling _report_no_vehicle; _vehicle_silent
    and _no_vehicle_logged_at are left unchanged. A None reply with
    the transport still connected (timeout) is reported as now.
  alternatives_considered:
    - option: "F1: a settle delay before the first verify connect."
      reason_rejected: "Delays every setup; the retry costs time only when the reset occurs."
    - option: "F1: retry on every connect failure."
      reason_rejected: "A refused or unreachable adapter would wait 2 s for nothing; d26ca557 limited the retry deliberately."
    - option: "F2: a smaller font or a second line."
      reason_rejected: "The error line's geometry is fixed between the title and the up arrow (change-d38362aa)."
  benefits:
    - "Most pairings complete without Retry."
    - "The notice is readable."
    - "The log does not blame the vehicle for a link fault."
  risks:
    - risk: "EDIT A(1) changes the cause text shown on DISCONNECTED for an ECONNRESET connect failure from 'ECONNRESET' to 'connection reset by adapter'."
      mitigation: "Intended; 27 characters, within the 40-character bound the mapping test enforces."
    - risk: "EDIT A(2): reset followed by two busy failures still fails."
      mitigation: "Retry remains available; the device check measures it."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits."
  code_changes:
    - component: "comm"
      file: "transport.py, obd.py"
      change_summary: "EDIT A(1), EDIT C"
      functions_affected:
        - "OBDProtocol._initialize_protocol"
      classes_affected: []
    - component: "display"
      file: "setup_components/bluetooth/interface.py"
      change_summary: "EDIT A(2), EDIT B"
      functions_affected:
        - "BluetoothSetupInterface.verify_obd_connection"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "gtach.comm.transport.LINK_RESET_CAUSE"
      change_type: "add"

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests with the scripted RFCOMM stand-in of test_obd_verify_busy_retry.py and a stub transport for OBDProtocol; pygame with the dummy video driver for the width test."
  test_cases:
    - scenario: "Verify: connect fails with LINK_RESET_CAUSE, then succeeds."
      expected_result: "True; two connects; sleeps == [1.0]; one disconnect."
    - scenario: "Verify: LINK_RESET_CAUSE, LINK_BUSY_CAUSE, success."
      expected_result: "True; three connects."
    - scenario: "Verify: LINK_RESET_CAUSE three times."
      expected_result: "False; three connects; two sleeps."
    - scenario: "Verify: 'connection refused by adapter'."
      expected_result: "False; one connect; no sleep (existing other-failure test kept)."
    - scenario: "LINK_RESET_CAUSE == _CONNECT_FAULT_CAUSES[errno.ECONNRESET]; len <= 40."
      expected_result: "Pass."
    - scenario: "Each DEVICE_LIST error-line constant rendered in get_label_small_font()."
      expected_result: "Width <= 220 px (FALLBACK_LIST_TEXT must pass)."
    - scenario: "_initialize_protocol: 0100 returns None and is_connected() is False at that point."
      expected_result: "False; no WARNING record; _vehicle_silent unchanged; one DEBUG 'Link lost during initialisation'."
    - scenario: "_initialize_protocol: 0100 returns None with the transport connected."
      expected_result: "False; WARNING 'Vehicle not answering ... (None)'; _vehicle_silent True."
  regression_scope:
    - "tests/test_obd_verify_busy_retry.py, tests/test_connect_error_classification.py, tests/test_setup_flow.py, tests/test_comm_layer_defects.py, the OBD protocol tests."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes; mypy src/ reports no issues."

implementation:
  effort_estimate: "Small"
  implementation_steps:
    - step: "EDITS A to C and tests."
      owner: "tactical"
    - step: "Device check: three setups with the emulator; fallback notice with no ELM327 in range."
      owner: "human"
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
  design_updates:
    - "design-a3b4c5d6 section 4.0: the fallback notice text, after implementation. Planner."
  related_changes:
    - change_ref: "change-d26ca557"
      relationship: "extends"
    - change_ref: "change-34781bfe"
      relationship: "amends the fallback notice text"
  related_issues:
    - issue_ref: "issue-146491ba"
      relationship: "resolves"

notes: "Not part of the 71ab3751 series; it may ship in the same version increment."

version_history:
  - version: "1.0"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-146491ba iteration 1."

  - version: "1.1"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial change document. EDITS A to C. |
| 1.1 | 2026-11-12 | Approved for implementation. |

---

Copyright (c) 2026 William Watson. MIT License.
