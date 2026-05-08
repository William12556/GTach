Created: 2026 May 08

# Prompt: Remove TEST Screen — Automatic OBD Verification After Pairing

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Error Handling](<#5.0 error handling>)
- [6.0 Deliverables](<#6.0 deliverables>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

```yaml
prompt_info:
  id: "prompt-e2f3a4b5"
  task_type: "code_modification"
  source_ref: "change-e2f3a4b5"
  date: "2026-05-08"
  iteration: 1
  coupled_docs:
    change_ref: "change-e2f3a4b5"
    change_iteration: 1
```

---

## 1.0 Prompt Information

Remove the stub `SetupScreen.TEST` screen from the Bluetooth setup wizard and replace it
with an automatic OBD connection verification step (ATZ probe over RFCOMM) that runs
immediately after pairing succeeds, requiring no user interaction.

Related documents:
- [change-e2f3a4b5-remove-test-screen-obd-verify.md](<../change/change-e2f3a4b5-remove-test-screen-obd-verify.md>)
- [issue-e2f3a4b5-remove-test-screen-obd-verify.md](<../issues/issue-e2f3a4b5-remove-test-screen-obd-verify.md>)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    SetupScreen.TEST is a stub that renders a "Testing Connection" title and a
    "Complete" button. It performs no diagnostic. Removing it and adding an automatic
    ATZ probe eliminates unnecessary user interaction and provides genuine end-to-end
    verification before exiting setup.

  integration: >
    verify_obd_connection() is added to BluetoothSetupInterface and called from
    the on_pairing_complete callback (inside the existing async worker thread) after
    PairingStatus.SUCCESS is confirmed. It uses RFCOMMTransport transiently —
    constructed, used, and destroyed within the method. The main transport in app.py
    is unaffected.

  knowledge_references:
    - "src/gtach/display/setup_models.py — SetupScreen, PairingStatus enums"
    - "src/gtach/display/setup_components/state/coordinator.py — state transitions"
    - "src/gtach/display/setup_components/bluetooth/interface.py — async pairing"
    - "src/gtach/display/setup.py — rendering and touch handling"
    - "src/gtach/comm/rfcomm.py — RFCOMMTransport (read only, do not modify)"
    - "src/gtach/comm/device_store.py — DeviceStore (read only, do not modify)"

  constraints:
    - "Python 3.9+ — no walrus operator (:=)"
    - "No new runtime dependencies"
    - "Do not modify app.py, rfcomm.py, device_store.py, pairing.py, or transport.py"
    - "RFCOMMTransport must be imported locally within verify_obd_connection() to avoid circular imports"
    - "All logging via logging.getLogger — no print statements"
    - "Copyright header: Copyright (c) 2025 William Watson. MIT License."
    - "Production target is Raspberry Pi OS (Linux) only — no macOS guards required"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Four targeted file modifications. No new files. No changes to app.py.

  requirements:
    functional:
      - "SetupScreen.TEST removed from SetupScreen enum in setup_models.py"
      - "PairingStatus.TESTING removed from PairingStatus enum in setup_models.py"
      - "verify_obd_connection(state) added to BluetoothSetupInterface"
      - "verify_obd_connection() called from on_pairing_complete after SUCCESS confirmed"
      - "On OBD verify pass: coordinator.complete_setup() called — setup exits normally"
      - "On OBD verify fail: state.error_message = 'OBD check failed'; transition to DEVICE_LIST"
      - "All SetupScreen.TEST references removed from coordinator.py state transitions and progress_map"
      - "_render_test_screen() removed from setup.py"
      - "SetupScreen.TEST removed from _render_screen() dispatch and should_cache list"
      - "DEVICE_LIST screen renders state.error_message (if set) as a single centred line in colors['danger'] below the device list; clears error_message after rendering"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8"
        - "Type hints on all modified public interfaces"
        - "Thread-safe: verify_obd_connection runs in async worker thread — no additional locking required"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  file_changes:

    setup_models.py:
      path: "src/gtach/display/setup_models.py"
      changes:
        - "Remove TEST = auto() from SetupScreen enum"
        - "Remove TESTING = auto() from PairingStatus enum"

    coordinator.py:
      path: "src/gtach/display/setup_components/state/coordinator.py"
      changes:
        - "_handle_back_navigation(): remove 'elif current == SetupScreen.TEST' branch and 'elif current == SetupScreen.COMPLETE: transition_to_screen(SetupScreen.TEST)' branch"
        - "_handle_next_navigation(): remove 'elif current == SetupScreen.TEST: complete_setup()' branch; change PAIRING branch from 'transition_to_screen(SetupScreen.TEST)' to direct call to bluetooth_interface.verify_and_complete(state) — see note below"
        - "get_setup_progress(): remove SetupScreen.TEST: 0.8 entry from progress_map; renumber or remove — COMPLETE stays at 1.0"
        - "Add set_bluetooth_interface(bluetooth_interface) method so coordinator can call verify_and_complete"

      note: >
        The coordinator needs a reference to BluetoothSetupInterface to trigger
        verify_obd_connection after pairing. The cleanest approach: add an optional
        bluetooth_interface attribute to SetupStateCoordinator, set via
        set_bluetooth_interface(). SetupDisplayManager calls this in __init__ after
        both components are instantiated. Alternatively, the on_pairing_complete
        callback in interface.py can call verify_obd_connection directly (preferred —
        avoids coordinator depending on interface). See interface.py changes below.

    interface.py:
      path: "src/gtach/display/setup_components/bluetooth/interface.py"
      changes:
        - "Add verify_obd_connection(self, state: SetupState) -> bool method"
        - "In on_pairing_complete: after confirming SUCCESS and logging, call self.verify_obd_connection(state)"
        - "If verify_obd_connection returns True: call self._state_coordinator.complete_setup() — requires coordinator reference (see below)"
        - "If verify_obd_connection returns False: set state.error_message = 'OBD check failed'; call self._state_coordinator.transition_to_screen(SetupScreen.DEVICE_LIST)"

      coordinator_reference: >
        BluetoothSetupInterface needs a reference to SetupStateCoordinator to trigger
        completion or screen transition after OBD verification. Add optional
        state_coordinator parameter to BluetoothSetupInterface.__init__() defaulting
        to None. SetupDisplayManager passes self.state_coordinator when constructing
        BluetoothSetupInterface. If state_coordinator is None, log a warning and skip
        the transition (safe fallback).

      verify_obd_connection_algorithm: |
        def verify_obd_connection(self, state: SetupState) -> bool:
            from ....comm.rfcomm import RFCOMMTransport
            from ....comm.device_store import DeviceStore
            try:
                device = DeviceStore().get_primary_device()
                if device is None:
                    self.logger.error("OBD verify: no primary device in store")
                    return False
                transport = RFCOMMTransport(device.mac_address, channel=1)
                connected = transport.connect()
                if not connected:
                    self.logger.warning("OBD verify: RFCOMM connect failed")
                    return False
                try:
                    response = transport.send_command('ATZ', timeout=5.0)
                    ok = response is not None and len(response.strip()) > 0
                    self.logger.info(f"OBD verify: {'pass' if ok else 'fail'} response={response!r}")
                    return ok
                finally:
                    transport.disconnect()
            except Exception as e:
                self.logger.error(f"OBD verify exception: {e}")
                return False

    setup.py:
      path: "src/gtach/display/setup.py"
      changes:
        - "Remove _render_test_screen() method"
        - "Remove 'elif state.current_screen == SetupScreen.TEST: self._render_test_screen(surface, state)' from _render_screen()"
        - "Remove SetupScreen.TEST from should_cache list in render()"
        - "In _render_device_list_screen(): after rendering device list and buttons, add: if state.error_message: render state.error_message centred at y=310 (above buttons) in get_minimal_font() with color colors['danger']; then set state.error_message = None via state_coordinator.update_state(error_message=None)"
        - "Pass self.state_coordinator to BluetoothSetupInterface constructor (add state_coordinator= kwarg)"

  error_message_position: >
    y=310 places the notice between the device list (ends ~y=290) and the Back/Retry
    buttons (start y=340). Single line, centred at x=240. Font: get_minimal_font().
    Color: colors['danger'] = (255, 50, 50).
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  obd_verify_timeout: >
    RFCOMMTransport.send_command() accepts timeout parameter (default 2.0 s).
    Use timeout=5.0 for ATZ to allow for slow adapter reset. If timeout occurs,
    send_command() returns None — treated as failure.
  connect_failure: >
    If transport.connect() returns False, verify_obd_connection() returns False
    immediately without attempting send_command().
  exception: >
    All exceptions in verify_obd_connection() caught at outer try/except,
    logged as error, return False.
  missing_coordinator: >
    If state_coordinator is None in BluetoothSetupInterface, log warning and
    do not attempt transition. Setup will not advance but will not crash.
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deliverables

```yaml
deliverables:
  modified_files:
    - "src/gtach/display/setup_models.py"
    - "src/gtach/display/setup_components/state/coordinator.py"
    - "src/gtach/display/setup_components/bluetooth/interface.py"
    - "src/gtach/display/setup.py"
  new_files: []
  deleted_files: []
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "grep -r 'SetupScreen.TEST' src/ returns no results"
  - "grep -r 'PairingStatus.TESTING' src/ returns no results"
  - "grep -r '_render_test_screen' src/ returns no results"
  - "verify_obd_connection method present in interface.py"
  - "error_message rendered in _render_device_list_screen when state.error_message is set"
  - "No syntax errors: python -m py_compile on all four modified files"
  - "SetupDisplayManager instantiation passes state_coordinator to BluetoothSetupInterface"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief:
  executor: "Claude Code"
  working_directory: "/Users/williamwatson/Documents/GitHub/GTach"
  execution_order:
    - step: 1
      file: "src/gtach/display/setup_models.py"
      action: "Remove TEST from SetupScreen; remove TESTING from PairingStatus"
    - step: 2
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      action: "Add state_coordinator param to __init__; add verify_obd_connection(); wire into on_pairing_complete"
    - step: 3
      file: "src/gtach/display/setup_components/state/coordinator.py"
      action: "Remove all SetupScreen.TEST references from transitions and progress_map"
    - step: 4
      file: "src/gtach/display/setup.py"
      action: "Remove _render_test_screen; remove TEST from dispatch and cache; add error_message rendering in DEVICE_LIST; pass state_coordinator to BluetoothSetupInterface"
    - step: 5
      action: "Run python -m py_compile on all four files; report results"
  phase_max_iterations: 50
  commit_message: "feat: replace TEST screen stub with automatic ATZ OBD verification"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-05-08 | William Watson | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
