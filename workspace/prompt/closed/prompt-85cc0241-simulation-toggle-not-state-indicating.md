Created: 2026 May 29

# Prompt: Make OPTIONS simulation button a state-indicating toggle

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Error Handling](<#5.0 error handling>)
- [6.0 Testing](<#6.0 testing>)
- [7.0 Deliverable](<#7.0 deliverable>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-85cc0241"
  task_type: "debug"
  source_ref: "change-85cc0241"
  date: "2026-05-29"
  iteration: 1
  status: "closed"
  coupled_docs:
    change_ref: "change-85cc0241"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Make the OPTIONS-screen simulation control legible by labelling it with its
    destination, derived from the current _sim_mode state.

  integration: >
    Display domain: src/gtach/display/manager.py, function _draw_options_mode.
    No other files or domains affected.

  constraints:
    - "Modify only the label of the lower OPTIONS button in _draw_options_mode"
    - "Do not change _on_simulation_mode, button geometry, or touch registration"
    - "Do not change the DISCONNECTED screen"
    - "Exclude setup_original_backup.py and any *_backup.py from all changes"
    - "Read _draw_options_mode before editing"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Derive the lower OPTIONS button label from self._sim_mode: 'Bluetooth' when True,
    'Simulation mode' when False. Render the derived label in place of the fixed string.

  requirements:
    functional:
      - "When _sim_mode is False, lower button label is 'Simulation mode'"
      - "When _sim_mode is True, lower button label is 'Bluetooth'"
      - "Touch region key, geometry, and handler (_on_simulation_mode) unchanged"
      - "Upper 'Clear settings' button unchanged"
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Reuse the existing centred render_text path"
        - "No interface/signature change"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Label-derivation change within an existing render method"

  components:
    - name: "DisplayManager._draw_options_mode"
      type: "function"
      purpose: "Render OPTIONS screen with a state-indicating simulation label"
      logic:
        - "Compute sim_label = 'Bluetooth' if self._sim_mode else 'Simulation mode'"
        - "Pass sim_label to the existing render_text call for the lower button"
        - "Leave the 'Clear settings' label, geometry, and touch registration unchanged"

  dependencies:
    internal:
      - "manager.py: DisplayManager._sim_mode (already maintained)"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: "No new error paths; label derivation is a simple conditional."
  logging:
    level: "DEBUG"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing

```yaml
testing:
  unit_tests:
    - scenario: "_sim_mode False on OPTIONS render"
      expected: "Lower button label is 'Simulation mode'"
    - scenario: "_sim_mode True on OPTIONS render"
      expected: "Lower button label is 'Bluetooth'"
  edge_cases:
    - "Rapid toggle: label matches _sim_mode on the next render"
  validation:
    - "On-device: label reflects sim state; toggle works in both directions"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deliverable

```yaml
deliverable:
  format_requirements:
    - "Modify file in place; preserve all behaviour not in scope"
  files:
    - path: "src/gtach/display/manager.py"
      content: "Derive lower OPTIONS button label from _sim_mode in _draw_options_mode"

success_criteria:
  - "Lower OPTIONS button label is derived from _sim_mode"
  - "Toggle continues to function in both directions"
  - "No changes outside _draw_options_mode"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Modify one function in src/gtach/display/manager.py. Read the function before
  editing. Exclude any *_backup.py files.

  Target: DisplayManager._draw_options_mode(self).

  In that method the lower button is currently rendered with a fixed label
  "Simulation mode" via a render_text call. Change only that label so it reflects
  self._sim_mode:

    sim_label = "Bluetooth" if self._sim_mode else "Simulation mode"

  Use sim_label as the text argument in the existing render_text call for the lower
  button. Do not change:
  - the upper "Clear settings" label,
  - button rectangles (self._options_btn_clear, self._options_btn_sim),
  - touch registration keys or the _on_simulation_mode handler.

  Rationale: the control toggles _sim_mode but the fixed label never reflects state,
  so the operator cannot tell it will return to the live (Bluetooth) display when
  simulation is active. The label must show the destination.

  Hard constraints:
  - Only the lower-button label in _draw_options_mode changes.
  - Do not modify _on_simulation_mode, the DISCONNECTED screen, or geometry.
  - No signature change.

  Deliverable: modified manager.py saved in place.
  Verify: _draw_options_mode selects the lower-button label from self._sim_mode
  ('Bluetooth' when True, 'Simulation mode' when False).
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-29 | Initial prompt. |

---

Copyright (c) 2026 William Watson. MIT License.
