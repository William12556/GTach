# Change: Task Register Fixes — Texts, Simulation, Log Levels, Connect Causes

Created: 2026 November 12

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-76ef5387"
  title: "Shorten DEVICE_NOT_SAVED_TEXT, classify simulated devices, quiet planned-close and pairing-failure records, map ECONNABORTED, order after hciuart, and keep 'adapter not reachable' out of the wedge diagnosis"
  date: "2026-11-12"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-76ef5387"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-76ef5387"
  description: "Findings F1 to F6 of issue-76ef5387, in one Claude Code run."

scope:
  summary: "Seven small edits (A to G) in three source files, one service file and the tests."
  affected_components:
    - name: "DEVICE_NOT_SAVED_TEXT; on_pairing_complete"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "_FAKE_DEVICES"
      file_path: "src/gtach/comm/sim_bluetooth.py"
      change_type: "modify"
    - name: "_CONNECT_FAULT_CAUSES; OBDTransport.connect; OBDTransport.send_command"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "gtach.service"
      file_path: "bin/gtach.service"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-a3b4c5d6-component_display_setup_manager"
      sections:
        - "4.0 (DEVICE_LIST error-line texts)"
  out_of_scope:
    - "Automatic recovery from a wedged controller (separate ai/task.md row)."
    - "The re-check loop for PID 0C unsupported (dropped; issue-76ef5387 notes)."
    - "Any change to retry intervals, the wedge threshold or the verify retry bound."

rational:
  problem_statement: "See issue-76ef5387 F1 to F6."
  proposed_solution: >
    EDIT A (F1): DEVICE_NOT_SAVED_TEXT = 'Not saved'; the width test
    case loses its strict xfail.
    EDIT B (F2): set device_classification on every fake device to
    match its existing device_type label: the three 'ELM327' devices
    HIGHLY_LIKELY_ELM327, 'Generic BT Adapter' ('Compatible')
    POSSIBLY_COMPATIBLE. A simbt scan then shows the normal list. The
    fallback notice stays covered by tests/test_setup_flow.py.
    EDIT C (F3): in send_command's _IO_ERRORS handler, when the captured
    handle is no longer the current handle (closed by disconnect() or
    drop_link()), log at DEBUG and return None without changing state
    or _last_failure_cause.
    EDIT D (F4): map ECONNABORTED to LINK_RESET_CAUSE. The post-pairing
    verify then retries it too, through the existing cause set.
    EDIT E (F5): add hciuart.service to After= in bin/gtach.service.
    Ordering only: no Wants= or Requires=, so a missing or failed
    hciuart neither blocks nor fails GTach.
    EDIT F (F5 related): log a pairing that returned False at WARNING;
    an exception during pairing stays at ERROR.
    EDIT G (F6): a module tuple of causes that show a working
    controller — ECONNREFUSED's and EHOSTDOWN's ('adapter not
    reachable'); a failure with one of them neither counts towards nor
    escalates to the wedge diagnosis. Replaces the two refused-only
    checks in connect().
  alternatives_considered:
    - option: "F1: keep the text and widen the error line."
      reason_rejected: "Layout change for one pixel."
    - option: "F2: leave one fake device UNKNOWN to keep the fallback reachable (ai/task.md suggestion)."
      reason_rejected: "The fallback shows only when every device is UNKNOWN, so one UNKNOWN device does not reach it."
    - option: "F3: special-case errno EBADF."
      reason_rejected: "The handle identity states the actual condition (closed by this process) and also covers other errnos a closed socket may raise."
    - option: "F5: Wants=/After= on sys-subsystem-bluetooth-devices-hci0.device."
      reason_rejected: "With no controller the start waits up to the device job timeout (90 s), delaying the display."
    - option: "F6: escalate only EBUSY."
      reason_rejected: "Narrower than needed; unmapped errnos from a wedged controller would no longer escalate."
  benefits:
    - "Correct texts and causes on the display; ERROR records only for faults."
  risks:
    - risk: "G: a wedged controller reporting EHOSTDOWN would not be diagnosed as wedged."
      mitigation: "Only EBUSY observed in a wedge (2026-10-08); the cause shown remains 'adapter not reachable', which still prompts a check."
    - risk: "E: hciuart.service absent or named differently on the image; ordering then has no effect."
      mitigation: "Device check confirms the unit and its type; no harm if absent."
    - risk: "C: a genuine I/O fault racing a planned close is logged at DEBUG."
      mitigation: "The link is being closed in that case anyway."

technical_details:
  current_behavior: "See issue-76ef5387 test_data."
  proposed_behavior: "See rational.proposed_solution."
  implementation_approach: "Edit in place; extend existing test modules; one commit."
  code_changes:
    - component: "interface.py"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: "EDIT A, EDIT F"
      functions_affected:
        - "BluetoothSetupInterface.start_pairing (on_pairing_complete)"
      classes_affected: []
    - component: "sim_bluetooth.py"
      file: "src/gtach/comm/sim_bluetooth.py"
      change_summary: "EDIT B"
      functions_affected: []
      classes_affected: []
    - component: "transport.py"
      file: "src/gtach/comm/transport.py"
      change_summary: "EDIT C, EDIT D, EDIT G"
      functions_affected:
        - "OBDTransport.connect"
        - "OBDTransport.send_command"
      classes_affected:
        - "OBDTransport"
    - component: "gtach.service"
      file: "bin/gtach.service"
      change_summary: "EDIT E"
      functions_affected: []
      classes_affected: []
  data_changes:
    - entity: "_FAKE_DEVICES"
      change_type: "validation"
      details: "device_classification set per device."
  interface_changes:
    - interface: "DEVICE_NOT_SAVED_TEXT"
      change_type: "contract"
      details: "Value 'Not saved'."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "BluetoothSetupInterface.verify_obd_connection"
      impact: "Retries ECONNABORTED through LINK_RESET_CAUSE (EDIT D)."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests; then a device check."
  test_cases:
    - scenario: "A: DEVICE_NOT_SAVED_TEXT width in get_label_small_font()."
      expected_result: "<= 220 px; no xfail."
    - scenario: "B: SimBluetoothPairing discovery fed to _present_scan_result."
      expected_result: "error_message is None; no fake device is UNKNOWN."
    - scenario: "C: send_command whose read raises OSError(EBADF) after disconnect() replaced the handle."
      expected_result: "No ERROR record; last_failure_cause unchanged; returns None."
    - scenario: "C: send_command whose read raises OSError with the handle still current."
      expected_result: "ERROR record and cause recorded, as before."
    - scenario: "D: _CONNECT_FAULT_CAUSES[errno.ECONNABORTED]."
      expected_result: "== LINK_RESET_CAUSE."
    - scenario: "F: pair_device returns False."
      expected_result: "WARNING 'Failed to pair with device', no ERROR."
    - scenario: "G: eight consecutive EHOSTDOWN failures, controller present."
      expected_result: "Cause 'adapter not reachable'; never the wedge cause."
    - scenario: "G: eight EHOSTDOWN failures, then one EBUSY."
      expected_result: "Cause LINK_BUSY_CAUSE, not the wedge cause."
    - scenario: "G: six EBUSY failures."
      expected_result: "Wedge cause, as before."
  regression_scope:
    - "tests/test_connect_error_classification.py"
    - "tests/test_comm_layer_defects.py"
    - "tests/test_reconnect_path.py"
    - "tests/test_setup_flow.py"
    - "tests/test_obd_verify_busy_retry.py"
  validation_criteria:
    - "pytest tests/ passes; mypy src/ reports no issues."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "EDITS A to G per prompt-76ef5387."
      owner: "Claude Code"
    - step: "Deploy; device check per issue-76ef5387 verification_steps."
      owner: "William Watson"
  rollback_procedure: "git revert of the implementation commit."
  deployment_notes: "EDIT E takes effect after the service file is redeployed and systemctl daemon-reload (deploy.sh / install.sh)."

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
    - change_ref: "change-146491ba"
      relationship: "extends LINK_RESET_CAUSE"
  related_issues:
    - issue_ref: "issue-5e7a03c4"
      relationship: "related"

notes: "Bundled at the owner's request; the owner delegated the technical decisions (2026-11-12)."

version_history:
  - version: "1.0"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Initial change document."

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
| 1.0 | 2026-11-12 | Initial change document. EDITS A to G. |

---

Copyright (c) 2026 William Watson. MIT License.
