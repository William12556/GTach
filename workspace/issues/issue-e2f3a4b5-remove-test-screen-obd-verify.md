Created: 2026 May 08

# Issue: Remove TEST Screen — Replace with Automatic OBD Verification

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [8.0 Resolution](<#8.0 resolution>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Prevention](<#10.0 prevention>)
- [11.0 Traceability](<#11.0 traceability>)
- [Version History](<#version history>)

---

```yaml
issue_info:
  id: "issue-e2f3a4b5"
  title: "Remove TEST Screen — Replace with Automatic OBD Verification"
  date: "2026-05-08"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-e2f3a4b5"
    change_iteration: 1
```

---

## 1.0 Issue Information

The `SetupScreen.TEST` screen ("Testing Connection") is a stub that performs no actual
diagnostic. It renders a title and a "Complete" button. The user must tap to advance.
This adds friction with no information value.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: ""
  description: >
    After successful Bluetooth pairing the setup wizard presents a "Testing Connection"
    screen requiring the user to tap "Complete" to proceed. The screen performs no test.
    The PairingStatus.TESTING state exists in the model but is never used. The screen
    is a placeholder with no functional purpose.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "SetupScreen / PairingStatus enums"
      file_path: "src/gtach/display/setup_models.py"
    - name: "SetupStateCoordinator"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
  designs:
    - design_ref: "design-a3b4c5d6-component_display_setup_manager.md"
    - design_ref: "design-2c6b8e4d-domain_display.md"
  version: "0.2.0"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: >
    GTach running on Raspberry Pi Zero 2W. No paired device in device store
    (fresh setup). ELM327 adapter powered on and discoverable.
  steps:
    - "Launch GTach — enters setup mode."
    - "Complete device discovery and pairing."
    - "Observe 'Testing Connection' screen with 'Complete' button."
    - "Note: no test is performed; the screen waits indefinitely for user tap."
  frequency: "always"
  reproducibility_conditions: "Every first-time setup or simbt simulation run."
  preconditions: "No paired device in device store."
  test_data: ""
  error_output: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behavior

```yaml
behavior:
  expected: >
    After successful Bluetooth pairing, automatically open an RFCOMM connection
    to the paired device, send ATZ, and verify a non-empty response within a
    timeout period. On success, proceed immediately to setup completion with no
    user interaction. On failure, return to DEVICE_LIST and display "OBD check
    failed" alongside the device entry.
  actual: >
    A static "Testing Connection" screen blocks progression until the user taps
    "Complete". No OBD command is sent. No diagnostic result is produced.
    PairingStatus.TESTING is defined in the model but never set.
  impact: >
    Unnecessary user interaction step. No real connection verification occurs,
    so a paired-but-non-functional adapter will silently proceed to normal mode
    only to fail there.
  workaround: "Tap Complete to proceed."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.9+"
  os: "Raspberry Pi OS (Linux)"
  dependencies:
    - library: "pygame"
      version: ">=2.0"
  domain: "display / comm"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    SetupScreen.TEST and PairingStatus.TESTING were added to the model as stubs
    and never implemented. The _render_test_screen method renders a static screen
    with no logic. The intent (OBD verification) was deferred and forgotten.
  technical_notes: >
    After pair_device() succeeds, the selected device MAC address is available via
    DeviceStore.get_primary_device(). An RFCOMMTransport can be instantiated
    transiently with this MAC, connect() called, ATZ sent via send_command(), and
    the socket closed immediately. This is independent of the main transport
    constructed later in app.py._start_obd(). The probe adds one RFCOMM connection
    cycle (~2-5 s) but eliminates the manual tap and catches non-functional adapters
    at setup time rather than at runtime.

    On failure the error_message field on SetupState is set to "OBD check failed"
    and the state transitions to DEVICE_LIST. The device list screen already reads
    error_message — it surfaces as a notice beneath the device list.

  related_issues: []
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "AEL"
  target_date: ""
  approach: >
    Implement per technical_notes. Remove SetupScreen.TEST, PairingStatus.TESTING,
    _render_test_screen, and all TEST-related state transitions. Add
    verify_obd_connection() to BluetoothSetupInterface. Wire the verification into
    the pairing completion path in SetupStateCoordinator. Surface error_message on
    the DEVICE_LIST screen. Full details in change-e2f3a4b5.
  change_ref: "change-e2f3a4b5"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

verification_enhanced:
  verification_steps:
    - "Run gtach --transport simbt — confirm TEST screen no longer appears."
    - "Confirm setup completes automatically after successful pairing with no user tap."
    - "With a non-functional adapter MAC: confirm 'OBD check failed' appears on DEVICE_LIST."
    - "Confirm transition from PAIRING success directly to COMPLETE (no TEST intermediate)."
    - "Confirm SetupScreen.TEST and PairingStatus.TESTING are absent from setup_models.py."
  verification_results: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Prevention

```yaml
prevention:
  preventive_measures: >
    Design stubs should be flagged as unimplemented in the model with a comment.
    Placeholder screens with no logic should not be merged.
  process_improvements: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Traceability

```yaml
traceability:
  design_refs:
    - "design-a3b4c5d6-component_display_setup_manager.md"
    - "design-2c6b8e4d-domain_display.md"
  change_refs:
    - "change-e2f3a4b5"
  test_refs: []

notes: >
  The temporary RFCOMMTransport used for the OBD probe is constructed and destroyed
  entirely within setup. It has no relationship to the main transport created in
  app.py._start_obd() after setup completes.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-05-08 | William Watson | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
