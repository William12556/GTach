Created: 2026 May 29

# Change: Make OPTIONS simulation button a state-indicating toggle

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
  id: "change-85cc0241"
  title: "Make OPTIONS simulation button a state-indicating toggle"
  date: "2026-05-29"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-85cc0241"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "issue"
  reference: "issue-85cc0241"
  description: >
    Resolves Finding B (symptoms S1, S3) from audit-ui-navigation-logic-report.md:
    the OPTIONS simulation control does not indicate its state or destination.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Derive the OPTIONS lower-button label from the _sim_mode flag so it shows the
    destination: 'Simulation mode' when simulation is off (press activates sim),
    'Bluetooth' when simulation is on (press returns to the live display).

  affected_components:
    - name: "DisplayManager._draw_options_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"

  affected_designs:
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
      sections: ["5.2"]

  out_of_scope:
    - "Changes to _on_simulation_mode toggle behaviour or the mode it selects"
    - "The DISCONNECTED screen 'Simulate' button (correct as-is; sim is always off there)"
    - "Renaming the _sim_mode flag or disambiguating it from transport simulation (Finding C)"
    - "Whether the screen remains on OPTIONS after the toggle"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    The lower OPTIONS button label is the fixed string 'Simulation mode'. It does not
    reflect _sim_mode, so when simulation is active the label still reads 'Simulation
    mode' although pressing it returns to the live display. The toggle direction is
    not legible.

  proposed_solution: >
    In _draw_options_mode(), choose the label from _sim_mode: 'Bluetooth' when
    _sim_mode is True (press returns to live OBD), 'Simulation mode' when False
    (press activates simulation). Touch registration and handler are unchanged.

  alternatives_considered:
    - option: "Keep the screen on OPTIONS after toggling to show the new state"
      reason_rejected: >
        Changes the established interaction (press switches to the live/sim display).
        The label change alone resolves S1 and S3; deferred as out of scope.

  benefits:
    - "Toggle direction is legible from the control itself"
    - "Operator has a visible path from simulation back to Bluetooth in OPTIONS"

  risks:
    - risk: "Label text width differs ('Bluetooth' vs 'Simulation mode')"
      mitigation: "Both fit the existing 300px button; reuse the existing centred render path"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    _draw_options_mode() renders the lower button with the fixed label 'Simulation
    mode'. _on_simulation_mode() toggles _sim_mode and sets config.mode accordingly.

  proposed_behavior: >
    _draw_options_mode() renders the lower button label as 'Bluetooth' when _sim_mode
    is True and 'Simulation mode' when False. The toggle handler is unchanged.

  implementation_approach: >
    In _draw_options_mode(), replace the literal 'Simulation mode' label string with a
    value derived from self._sim_mode (e.g. label = 'Bluetooth' if self._sim_mode else
    'Simulation mode'). Use this value in the existing render_text call. No change to
    button geometry or to the registered touch region/handler.

  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Derive the OPTIONS lower-button label from self._sim_mode in
        _draw_options_mode; render the derived label.
      functions_affected:
        - "_draw_options_mode"

  interface_changes:
    - interface: "DisplayManager._draw_options_mode"
      change_type: "contract"
      details: "No signature change; rendered label now depends on _sim_mode."
      backward_compatible: "yes"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: "Manual on-device verification on gtach.local after deployment."

  test_cases:
    - scenario: "Open OPTIONS while simulation is off"
      expected_result: "Lower button reads 'Simulation mode'"
    - scenario: "Activate simulation, long-press back into OPTIONS"
      expected_result: "Lower button reads 'Bluetooth'"
    - scenario: "Tap the button while it reads 'Bluetooth'"
      expected_result: "_sim_mode becomes False; live display resumes"
    - scenario: "Tap the button while it reads 'Simulation mode'"
      expected_result: "_sim_mode becomes True; simulation display resumes"

  regression_scope:
    - "OPTIONS 'Clear settings' button unaffected"
    - "_on_simulation_mode toggle behaviour unchanged"

  validation_criteria:
    - "Label text matches _sim_mode state on every OPTIONS render"
    - "Toggle continues to function in both directions"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-29 | Initial change document. |

---

Copyright (c) 2026 William Watson. MIT License.
