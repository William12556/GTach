Created: 2026 May 27

# Change: Implement OPTIONS screen, DISCONNECTED affordances, and simulation mode

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Testing Requirements](<#6.0 testing requirements>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-f3e2d1c0"
  title: "Implement OPTIONS screen, DISCONNECTED affordances, and simulation mode"
  date: "2026-05-27"
  author: "William Watson"
  status: "approved"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f3e2d1c0"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "requirement_change"
  reference: "issue-f3e2d1c0"
  description: >
    Design session 2026-05-27. Implements design documents:
    design-g1h2i3j4-gesture_reference.md §4.3, §4.4;
    design-b8c9d0e1-component_display_manager.md §5.1, §5.2.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Rename DisplayMode.SETTINGS to OPTIONS. Implement OPTIONS screen with two
    tappable items. Implement DISCONNECTED screen on-screen affordances. Wire
    long-press on DISCONNECTED to SETUP transition. Add session-only simulation
    mode flag and UI activation path.

  affected_components:
    - name: "DisplayMode"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "TouchHandler"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
    - name: "NavigationGestureHandler"
      file_path: "src/gtach/display/navigation_gestures.py"
      change_type: "modify"

  affected_designs:
    - design_ref: "design-g1h2i3j4-gesture_reference.md"
      sections: ["4.3", "4.4", "5.2"]
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
      sections: ["5.1", "5.2", "4.4", "4.6"]

  out_of_scope:
    - "Swipe up/down gesture implementation"
    - "Setup wizard touch interactions"
    - "Options screen items beyond 'Clear settings' and 'Simulation mode'"
    - "Persistent simulation mode across restarts"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    Implementation lags design. User has no UI path to re-pair a device from the
    DISCONNECTED screen, no access to an options menu, and no way to activate
    simulation mode from the UI.

  proposed_solution: >
    Implement the four source changes identified in issue-f3e2d1c0 as a single
    coherent change set. The rename is mechanical; the new screen content is
    minimal (two items each). Sim mode uses the existing --transport simbt path.

  benefits:
    - "User can re-pair without restarting the application"
    - "User can activate simulation mode without CLI flags"
    - "Code identifier matches design documentation"
    - "DISCONNECTED screen is no longer a dead end"

  risks:
    - risk: "DisplayMode.SETTINGS rename breaks any serialised config referencing the string 'SETTINGS'"
      mitigation: "Check config.yaml loading path; add backward-compatible alias if SETTINGS appears in persisted config"
    - risk: "Simulation mode activation requires access to OBD transport layer from DisplayManager"
      mitigation: "Use a session flag and callback; DisplayManager signals app layer to switch transport"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    DisplayMode.SETTINGS exists. Long press enters a partially rendered settings
    screen. DISCONNECTED screen is static. Long press on DISCONNECTED has no effect.
    No simulation mode UI.

  proposed_behavior: >
    DisplayMode.OPTIONS replaces SETTINGS. Long press enters OPTIONS screen showing
    'Clear settings' and 'Simulation mode' as tappable items. 'Clear settings' clears
    DeviceStore and transitions to SETUP. 'Simulation mode' sets a session flag and
    transitions to DIGITAL using simulated RPM data. DISCONNECTED screen shows 'Setup'
    and 'Simulate' buttons. Long press on DISCONNECTED transitions to SETUP.

  implementation_approach: >
    1. Rename enum value in models.py.
    2. Update all SETTINGS references in manager.py, touch.py, navigation_gestures.py.
    3. Rename _render_settings to _render_options; replace content with two button items.
    4. Implement _render_disconnected affordances (two buttons).
    5. Add _sim_mode: bool = False session flag to DisplayManager.
    6. Add on_simulate callback or direct flag set; when activated, bypass OBD queue
       and generate synthetic RPM data in display loop.
    7. Wire long press on DISCONNECTED in touch.py → SETUP transition.

  code_changes:
    - component: "DisplayMode"
      file: "src/gtach/display/models.py"
      change_summary: "Rename SETTINGS to OPTIONS"
      classes_affected: ["DisplayMode"]

    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Update DisplayMode.SETTINGS → OPTIONS references. Rename _render_settings
        to _render_options. Implement OPTIONS screen two-item tap routing.
        Implement DISCONNECTED screen Setup/Simulate buttons. Add _sim_mode flag.
        Implement synthetic RPM generation when _sim_mode active.
      functions_affected:
        - "_render_settings → _render_options"
        - "_render_disconnected"
        - "_on_long_press"
        - "_display_loop"

    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: "Wire long press on DISCONNECTED mode → SETUP transition"
      functions_affected:
        - "_process_touch"

    - component: "NavigationGestureHandler"
      file: "src/gtach/display/navigation_gestures.py"
      change_summary: "Update DisplayMode.SETTINGS → OPTIONS references (consistency)"
      functions_affected:
        - "_handle_long_press_gesture"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: "Manual on-device verification on gtach.local after deployment"

  test_cases:
    - scenario: "Long press from DIGITAL"
      expected_result: "Transitions to OPTIONS screen; two items visible"
    - scenario: "Tap 'Clear settings' in OPTIONS"
      expected_result: "DeviceStore cleared; transitions to SETUP"
    - scenario: "Tap 'Simulation mode' in OPTIONS"
      expected_result: "_sim_mode set; transitions to DIGITAL; RPM display shows synthetic data"
    - scenario: "Long press from OPTIONS"
      expected_result: "Returns to DIGITAL"
    - scenario: "Long press from DISCONNECTED"
      expected_result: "Transitions to SETUP"
    - scenario: "Tap 'Setup' on DISCONNECTED screen"
      expected_result: "Transitions to SETUP"
    - scenario: "Tap 'Simulate' on DISCONNECTED screen"
      expected_result: "_sim_mode set; transitions to DIGITAL with synthetic RPM"
    - scenario: "Application restart after sim mode activated"
      expected_result: "_sim_mode resets to False; normal OBD connection attempted"

  validation_criteria:
    - "No reference to DisplayMode.SETTINGS remains in active source files"
    - "OPTIONS screen renders without exception"
    - "DISCONNECTED screen renders two tappable affordances"
    - "Simulation mode produces visible RPM movement on display"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-27 | Initial change document. |

---

Copyright (c) 2026 William Watson. MIT License.
