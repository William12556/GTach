Created: 2026 May 08

# Change: Remove TEST Screen — Automatic OBD Verification After Pairing

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Dependencies](<#6.0 dependencies>)
- [7.0 Testing Requirements](<#7.0 testing requirements>)
- [8.0 Implementation](<#8.0 implementation>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Traceability](<#10.0 traceability>)
- [Version History](<#version history>)

---

```yaml
change_info:
  id: "change-e2f3a4b5"
  title: "Remove TEST Screen — Automatic OBD Verification After Pairing"
  date: "2026-05-08"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e2f3a4b5"
    issue_iteration: 1
```

---

## 1.0 Change Information

Removes the stub `SetupScreen.TEST` screen and replaces it with an automatic OBD
connection verification step that runs immediately after Bluetooth pairing succeeds,
requiring no user interaction.

Related issue: [issue-e2f3a4b5-remove-test-screen-obd-verify.md](<issue-e2f3a4b5-remove-test-screen-obd-verify.md>)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "enhancement"
  reference: "issue-e2f3a4b5"
  description: >
    SetupScreen.TEST is a stub with no diagnostic logic. Replacing it with an
    automatic ATZ probe eliminates unnecessary user interaction and provides genuine
    end-to-end verification before exiting setup.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Remove SetupScreen.TEST, PairingStatus.TESTING, _render_test_screen, and all
    TEST-related state transitions. Add verify_obd_connection() to
    BluetoothSetupInterface. Wire verification into the pairing completion path.
    Surface error_message on the DEVICE_LIST screen.

  affected_components:
    - name: "SetupScreen / PairingStatus enums"
      file_path: "src/gtach/display/setup_models.py"
      change_type: "modify"
    - name: "SetupStateCoordinator"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
      change_type: "modify"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"

  out_of_scope:
    - "app.py — no changes required"
    - "RFCOMMTransport — used as-is, no modification"
    - "DeviceStore — used as-is, no modification"
    - "Normal mode transport construction"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rationale:
  problem: >
    A mandatory user tap with no associated diagnostic adds friction and provides
    no value. A paired adapter that cannot respond to OBD commands will silently
    pass setup and fail only at runtime.
  solution: >
    Automatic ATZ probe over RFCOMM immediately after pairing. Zero user interaction.
    Failure returns the user to DEVICE_LIST with a clear notice.
  alternatives_considered:
    - option: "Keep TEST screen, add real ATZ logic"
      rejected_because: >
        Still requires user tap after the test. Adds a screen that serves no purpose
        once the result is known — success auto-proceeds, failure returns anyway.
    - option: "Remove TEST screen only, no probe"
      rejected_because: >
        Loses the opportunity to verify the adapter responds before exiting setup.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  description: >
    Four files are modified. No new files are created.

  setup_models.py:
    - Remove SetupScreen.TEST from SetupScreen enum.
    - Remove PairingStatus.TESTING from PairingStatus enum.

  coordinator.py (SetupStateCoordinator):
    - Remove all references to SetupScreen.TEST in _handle_back_navigation()
      and _handle_next_navigation().
    - Remove SetupScreen.TEST entry from progress_map in get_setup_progress().
    - In _handle_next_navigation(), change the PAIRING -> TEST transition to
      PAIRING -> trigger OBD verification (see interface.py below).
    - The coordinator calls bluetooth_interface.verify_obd_connection(state)
      after pairing success. On verification pass, calls complete_setup().
      On failure, sets state.error_message = "OBD check failed" and transitions
      to SetupScreen.DEVICE_LIST.

  interface.py (BluetoothSetupInterface):
    - Add verify_obd_connection(state: SetupState) -> bool method.
    - Method logic:
        1. Retrieve MAC from DeviceStore.get_primary_device().mac_address.
        2. Instantiate RFCOMMTransport(mac_address, channel=1).
        3. Call connect() with 10 s timeout.
        4. If connect() fails: return False.
        5. Send 'ATZ' via send_command(timeout=5.0).
        6. Call disconnect() unconditionally (finally block).
        7. Return True if response is not None and len > 0, else False.
    - The method runs synchronously within the async operation worker thread
      (called from the on_pairing_complete callback after PairingStatus.SUCCESS).
    - Import RFCOMMTransport locally within the method to avoid circular imports.

  setup.py (SetupDisplayManager):
    - Remove _render_test_screen() method entirely.
    - Remove SetupScreen.TEST branch from _render_screen().
    - Remove SetupScreen.TEST from the should_cache list in render().
    - In _render_device_list_screen(): if state.error_message is set, render
      it as a single line of small text below the device list, centred,
      in colors['danger']. Text: state.error_message (e.g. "OBD check failed").
      Clear error_message after rendering (set to None) so it does not persist
      across subsequent renders.

  flow_after_change:
    PAIRING (SUCCESS) -> [verify_obd_connection]
      -> pass  -> COMPLETE -> on_complete() -> normal mode
      -> fail  -> DEVICE_LIST (error_message = "OBD check failed")

  sim_mode_note: >
    When running --transport simbt, verify_obd_connection() will fail because
    RFCOMMTransport requires AF_BLUETOOTH which is not available in simulation.
    This is acceptable — simbt is a development tool and the failure path
    (return to DEVICE_LIST) is itself a testable outcome. If this becomes
    inconvenient, a future change can inject a mock verifier via the same
    factory pattern used for pairing.
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Dependencies

```yaml
dependencies:
  runtime:
    - "RFCOMMTransport (src/gtach/comm/rfcomm.py) — existing, unmodified"
    - "DeviceStore (src/gtach/comm/device_store.py) — existing, unmodified"
  no_new_packages: true
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Testing Requirements

```yaml
testing:
  manual:
    - "Pi with real ELM327: full setup flow completes without TEST screen."
    - "Pi with real ELM327: setup exits to normal mode automatically after pairing."
    - "Simulate OBD failure (power off adapter after pairing): confirm DEVICE_LIST"
      shown with 'OBD check failed' notice."
  simulation:
    - "simbt: confirm no TEST screen; confirm failure path returns to DEVICE_LIST."
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Implementation

```yaml
implementation:
  executor: "AEL (Claude Code)"
  prompt_ref: "prompt-e2f3a4b5-remove-test-screen-obd-verify.md"
  estimated_iterations: 1
  notes: >
    All changes are localised to four files. No interface changes to app.py.
    RFCOMMTransport import in interface.py must be local to avoid circular import.
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  steps:
    - "SetupScreen.TEST absent from setup_models.py."
    - "PairingStatus.TESTING absent from setup_models.py."
    - "_render_test_screen absent from setup.py."
    - "SetupScreen.TEST absent from _render_screen() and should_cache list."
    - "verify_obd_connection() present in BluetoothSetupInterface."
    - "DEVICE_LIST renders error_message when set."
    - "Full setup flow on Pi completes without user tap on any test screen."
  verified_date: ""
  verified_by: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Traceability

```yaml
traceability:
  issue_ref: "issue-e2f3a4b5"
  design_refs:
    - "design-a3b4c5d6-component_display_setup_manager.md"
    - "design-2c6b8e4d-domain_display.md"
  prompt_ref: "prompt-e2f3a4b5-remove-test-screen-obd-verify.md"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-05-08 | William Watson | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
