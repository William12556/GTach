Created: 2026 May 27

# Change: Fix Setup Loop Self-Join and Disconnected Screen Buttons

---

## Table of Contents

[1.0 Change Information](<#1.0 change information>)
[2.0 Source](<#2.0 source>)
[3.0 Scope](<#3.0 scope>)
[4.0 Rationale](<#4.0 rationale>)
[5.0 Technical Details](<#5.0 technical details>)
[6.0 Testing Requirements](<#6.0 testing requirements>)
[7.0 Verification](<#7.0 verification>)
[Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-f3c9a2e7"
  title: "Fix setup loop self-join RuntimeError and implement disconnected screen buttons"
  date: "2026-05-27"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f3c9a2e7"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "issue"
  reference: "issue-f3c9a2e7"
  description: >
    Two bugs identified from on-Pi test (v0.2.48, rfcomm transport).
    Bug 1: _setup_loop calls stop_thread on itself causing RuntimeError.
    Bug 2: _enter_setup_from_disconnected is a non-functional stub; both
    DISCONNECTED screen buttons are inoperative after setup completes.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Fix _setup_loop exit path to use break instead of stop_thread.
    Implement _enter_setup_from_disconnected via an app-level callback.
    Add setup_entry_callback attribute to DisplayManager set by app.py.
  affected_components:
    - name: "SetupDisplayManager._setup_loop"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "DisplayManager._enter_setup_from_disconnected"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-2c6b8e4d-domain_display.md"
      sections:
        - "SetupDisplayManager"
        - "DisplayManager"
    - design_ref: "design-a3b4c5d6-component_display_setup_manager.md"
      sections:
        - "_setup_loop"
  out_of_scope:
    - "Transport RUNNING race (cosmetic; resolves within one reconnect cycle)"
    - "RPM display logic"
    - "Bluetooth pairing flow"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    _setup_loop exits the COMPLETE branch by calling stop_thread('setup'),
    which joins the calling thread on itself — a Python invariant violation.
    The resulting RuntimeError is caught, the loop retries, but setup mode
    has already ended. The DISCONNECTED screen buttons are stubs: Setup
    transitions to DIGITAL which immediately re-enters DISCONNECTED; Simulate
    sets _sim_mode but the same re-entry loop prevents reaching DIGITAL.
  proposed_solution: >
    Bug 1: Replace stop_thread('setup') with break in _setup_loop. The daemon
    thread exits cleanly when the function returns; no explicit join required.

    Bug 2: Add setup_entry_callback to DisplayManager (set to None by default).
    app.py assigns a callback after initialisation that clears DeviceStore and
    starts a new SetupDisplayManager — mirroring the on_complete callback
    pattern. _enter_setup_from_disconnected calls this callback when present.

    Simulate fix: _on_simulation_mode must set _sim_mode before transitioning
    to DIGITAL. This is already correct in the code; the apparent failure is
    caused by Bug 1 preventing the DISCONNECTED→DIGITAL transition from
    completing. Resolving Bug 1 and 2 is sufficient.
  benefits:
    - "Setup completes without RuntimeError"
    - "Simulate button activates simulation mode correctly"
    - "Setup button re-enters Bluetooth setup flow from DISCONNECTED screen"
  risks:
    - risk: "setup_entry_callback not set when button tapped"
      mitigation: "Guard with 'if self._setup_entry_callback' and log warning if absent"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    _setup_loop: calls self.thread_manager.stop_thread('setup') after
    invoking on_complete — raises RuntimeError: cannot join current thread.
    _enter_setup_from_disconnected: transitions to DIGITAL with a comment
    noting actual implementation is deferred.
    DisplayManager: no setup_entry_callback attribute.
    app.py: does not register a setup re-entry callback.
  proposed_behavior: >
    _setup_loop: after invoking on_complete, executes break to exit the loop.
    The setup thread terminates normally.
    _enter_setup_from_disconnected: invokes self._setup_entry_callback() if
    set; logs a warning if not.
    DisplayManager.__init__: initialises self._setup_entry_callback = None.
    app.py: after constructing DisplayManager, assigns a lambda or method
    reference to display_manager._setup_entry_callback that clears
    DeviceStore and calls the same setup initialisation path used at startup.
  implementation_approach: >
    Three targeted edits across three files. No interface changes. No new
    classes. setup_entry_callback follows the existing on_complete callback
    pattern already used in app.py/SetupDisplayManager.
  code_changes:
    - component: "SetupDisplayManager._setup_loop"
      file: "src/gtach/display/setup.py"
      change_summary: "Replace stop_thread('setup') call with break"
      functions_affected:
        - "_setup_loop"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Add _setup_entry_callback = None in __init__ (or _initialize_legacy_components).
        Implement _enter_setup_from_disconnected to invoke the callback.
      functions_affected:
        - "__init__ / _initialize_legacy_components"
        - "_enter_setup_from_disconnected"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        After display_manager construction assign _setup_entry_callback to a
        method that clears DeviceStore, stops any running OBD threads, and
        re-initialises SetupDisplayManager via the same path used at startup.
      functions_affected:
        - "_initialise_display (or equivalent startup method)"
  interface_changes: []
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: "Manual on-Pi test with rfcomm transport and stored device"
  test_cases:
    - scenario: "Setup completes via Continue button"
      expected_result: "No RuntimeError in log; app reaches OBD mode or DISCONNECTED without freeze"
    - scenario: "Tap Simulate on DISCONNECTED screen"
      expected_result: "Simulation mode activates; radial or digital RPM display begins"
    - scenario: "Tap Setup on DISCONNECTED screen"
      expected_result: "Bluetooth setup flow starts; CURRENT_DEVICE or WELCOME screen shown"
    - scenario: "Tap Setup on DISCONNECTED then complete setup again"
      expected_result: "App transitions to OBD mode without second RuntimeError"
  validation_criteria:
    - "No 'cannot join current thread' in log"
    - "Simulate button reaches DIGITAL/RADIAL mode within one tap"
    - "Setup button enters setup mode within one tap"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Verification

```yaml
verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-f3c9a2e7"
      relationship: "resolves"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-27 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
