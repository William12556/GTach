Created: 2026 October 09

# Issue: OBD Verify Fails With EBUSY Immediately After Pairing

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-d26ca557"
  title: "verify_obd_connection opens RFCOMM about 2 ms after pairing completes and fails with EBUSY; the operator must press Retry"
  date: "2026-10-09"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-d26ca557"
    change_iteration: 1

source:
  origin: "test_result"
  test_ref: "test-c9de5fb0 TC-006 (re-pair on gtach.local, 2026-10-09)"
  description: >
    Found during on-device verification of the nine-change batch. Not
    caused by any change in that batch: the same failure appears in
    error.log on 2026-10-07 and 2026-10-08.

affected_scope:
  components:
    - name: "BluetoothSetupInterface.verify_obd_connection"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py (lines 219-223)"
    - name: "Pairing-success path that calls it"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py (around line 452)"
  designs:
    - design_ref: ""
  version: "0.4.10 (b1dd162)"

reproduction:
  prerequisites: "gtach.local with the ELM327 emulator in range."
  steps:
    - "Enter setup, tap New Setup, Start Setup."
    - "Select the adapter in the middle slot of Select Device."
  frequency: "intermittent (first attempt failed 2026-10-09 10:28:30; Retry passed 10:28:37)"
  reproducibility_conditions: "Pairing has just completed; the RFCOMM connect follows within milliseconds."
  preconditions: ""
  test_data: ""
  error_output: >
    10:28:30,334 BluetoothPairing INFO Successfully paired with ELM327-Emulator /
    10:28:30,347 DeviceStore INFO Saved primary device /
    10:28:30,349 RFCOMMTransport ERROR Failed to connect ... [Errno 16] Device or resource busy (bluetooth link busy - may need reset) /
    10:28:30,350 BluetoothSetupInterface WARNING OBD verify: RFCOMM connect failed

behavior:
  expected: "After a successful pairing the verify probe connects and setup completes in one pass."
  actual: "The probe fails with EBUSY and setup returns to Select Device; a second tap (Retry) succeeds."
  impact: "Extra operator action during setup; no data loss. The paired device is already saved on the first attempt."
  workaround: "Tap the device again (Retry)."

environment:
  python_version: "3.9.2 (gtach.local)"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "BlueZ"
      version: ""
  domain: "display/setup, comm"

analysis:
  root_cause: >
    Inferred: the ACL link created by pairing is still being torn down or
    held by bluetoothd when the RFCOMM socket connects 2 ms later, so the
    kernel returns EBUSY. Not confirmed with btmon.
  technical_notes: >
    Candidate approaches, to be decided in the change: a short bounded
    retry on EBUSY inside verify_obd_connection, or a settle delay
    between pairing and the probe. Related to the separate task.md item
    on recovery from a stuck EBUSY state after link loss.
  related_issues:
    - issue_ref: "issue-5e7a03c4"
      relationship: "related"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "Bounded link-busy-only retry in verify_obd_connection; see change-d26ca557."
  change_ref: "change-d26ca557"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: ""
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "Re-pair on gtach.local several times; setup completes without Retry each time."
  verification_results: ""

traceability:
  design_refs:
    - ""
  change_refs:
    - "change-d26ca557"
  test_refs:
    - "test-c9de5fb0 TC-006"
    - "~/Documents/gtach-testlogs/stage8-pair/ (not in the repository)"

notes: "Raised from test_result per P03.1."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial issue document, raised during on-device verification of the nine-change batch."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Coupled to change-d26ca557."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial issue document, raised during on-device verification of the nine-change batch. |
| 1.1 | 2026-10-09 | Coupled to change-d26ca557. |

---

Copyright (c) 2026 William Watson. MIT License.
