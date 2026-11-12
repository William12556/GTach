# Issue: Session B Findings — OBD Check Reset, Truncated Notice, Misleading Record

Created: 2026 November 12

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-146491ba"
  title: "OBD check after pairing fails on a connection reset; the fallback notice is truncated on DEVICE_LIST; a link lost during initialisation is logged as a silent vehicle"
  date: "2026-11-12"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-146491ba"
    change_iteration: 1

source:
  origin: "test_result"
  test_ref: "test-71ab3751-device-session-b"
  description: "Three findings of device session B (2026-11-12) recorded in ai/task.md. None is caused by runs 1 to 5."

affected_scope:
  components:
    - name: "BluetoothSetupInterface.verify_obd_connection"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "FALLBACK_LIST_TEXT"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "_CONNECT_FAULT_CAUSES"
      file_path: "src/gtach/comm/transport.py"
    - name: "OBDProtocol._initialize_protocol"
      file_path: "src/gtach/comm/obd.py"
  designs:
    - "design-a3b4c5d6-component_display_setup_manager"
  version: "0.4.15"

reproduction:
  prerequisites: "Pi with GTach 0.4.15; ELM327 emulator on Bluetooth."
  steps:
    - "F1: run setup and pair with the emulator."
    - "F2: run setup with no ELM327 in range and another named device discoverable."
    - "F3: break the link while the protocol thread initialises the adapter."
  frequency: "F1 in 4 of 6 pairings in session B (and once in session A); F2 always; F3 timing-dependent"
  reproducibility_conditions: "F1 and F2 on the device; F3 from source."
  test_data: >
    F1: the RFCOMM connect of verify_obd_connection, issued about 25 ms
    after the pairing test closed its socket, fails with ECONNRESET
    (logs 2026-11-12 08:35:38, 09:34:57, 09:42:55; session A 06:39:55).
    The cause is the unmapped errno name 'ECONNRESET', which the busy
    retry does not cover, so setup returns to DEVICE_LIST with 'OBD
    check failed'. After Retry, the next check met EBUSY once and passed
    on its second attempt (08:36:10 to 08:36:11, 09:35:17 to 09:35:18,
    09:43:10 to 09:43:11).
    F2: FALLBACK_LIST_TEXT 'No ELM327 found - showing all devices' is
    fitted to 220 px on the DEVICE_LIST error line and shows as
    'No ELM327 fo…'. 'OBD check failed' measures 217 px in the same
    font (report-d38362aa section 8.0).
    F3: _send_command returns None when the transport is not connected
    or the read fails; _initialize_protocol passes that None to
    _report_no_vehicle, which logs 'Vehicle not answering: no valid
    0100 response (None)' and marks the vehicle silent. Seen at session
    B step B1; that log file has since rotated out of logs/.
  error_output: "F1: 'Failed to connect to RFCOMM device ... [Errno 104] Connection reset by peer (ECONNRESET)' then 'OBD verify: RFCOMM connect failed'."

behavior:
  expected: "F1: a transient reset after pairing is retried within the existing bound. F2: the notice is readable in full. F3: a lost link is not reported as a silent vehicle."
  actual: "As in test_data."
  impact: "F1: the operator must tap Retry after most pairings. F2: the notice is unreadable. F3: misleading diagnosis in the log."
  workaround: "F1: tap Retry."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "F1: the retry of issue-d26ca557 covers EBUSY only. F2: text longer than the error line. F3: None is not distinguished from a vehicle reply."
  technical_notes: >
    F1 confidence: medium that one retry 1 s after the reset suffices.
    The observed sequence after a reset was busy once, then success,
    which fits within three attempts. The device check after the fix
    confirms it.
  related_issues:
    - issue_ref: "issue-d26ca557"
      relationship: "extends; busy retry after pairing"
    - issue_ref: "issue-34781bfe"
      relationship: "related; introduced the fallback notice"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-146491ba."
  change_ref: "change-146491ba"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Fixed display texts are checked against their render width by a unit test."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source and logs. [DONE, 2026-11-12.]"
    - "After the fix: unit tests per change-146491ba."
    - "After the fix: device check — three setups with the emulator; fallback notice with no ELM327 in range."
  verification_results: ""

traceability:
  design_refs:
    - "design-a3b4c5d6-component_display_setup_manager"
  change_refs:
    - "change-146491ba"
  test_refs:
    - "test-71ab3751-device-session-b"

notes: "Remaining session B findings (ECONNABORTED after setup, EBADF at ERROR on planned disconnect, boot-time no-controller connect) stay as ai/task.md observations."

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
| 1.0 | 2026-11-12 | Initial issue document. Session B findings F1 to F3. |

---

Copyright (c) 2026 William Watson. MIT License.
