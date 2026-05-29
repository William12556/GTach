Created: 2026 May 29

# Issue: OPTIONS simulation button label is not state-indicating

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Analysis](<#6.0 analysis>)
- [7.0 Resolution](<#7.0 resolution>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-85cc0241"
  title: "OPTIONS simulation button label is not state-indicating"
  date: "2026-05-29"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-85cc0241"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: "workspace/audit/audit-ui-navigation-logic-report.md §4.2"
  description: >
    On-device test (2026-05-29) reported in audit-ui-navigation-logic-report.md as
    symptoms S1 and S3 (Finding B). The OPTIONS-screen simulation control does not
    indicate its current state or its destination, so the operator cannot tell that
    it toggles between simulation and live (Bluetooth) display.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "DisplayManager._draw_options_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._on_simulation_mode"
      file_path: "src/gtach/display/manager.py"
  designs:
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
  version: "on-device build, 2026-05-29 session"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: "Application running; long-press available to reach OPTIONS."
  steps:
    - "Long-press to enter the OPTIONS screen."
    - "Observe the lower button label while simulation is off."
    - "Tap the button to enter simulation, then long-press back into OPTIONS."
    - "Observe the lower button label while simulation is on."
  frequency: "always"
  error_output: >
    gtach-debug.log records the toggle ('Simulation mode on' / 'Simulation mode off'),
    confirming the flag changes; the on-screen label does not change.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behavior

```yaml
behavior:
  expected: >
    The OPTIONS simulation control is a state-indicating toggle whose label shows the
    destination: when simulation is off it indicates it will activate simulation;
    when simulation is on it indicates it will return to the live (Bluetooth) display.
  actual: >
    The label is the fixed string 'Simulation mode' regardless of the _sim_mode state.
    When simulation is active, the same label still reads 'Simulation mode' even though
    pressing it returns to the live display.
  impact: >
    The operator cannot tell which direction the control will switch, and there is no
    visible affordance to return from simulation to Bluetooth from the OPTIONS screen.
  workaround: "None; the control still toggles, but its direction is not legible."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Analysis

```yaml
analysis:
  root_cause: >
    _draw_options_mode() renders a hardcoded 'Simulation mode' label for the lower
    button. _on_simulation_mode() toggles _sim_mode and sets config.mode to DIGITAL
    (on) or RADIAL (off), but the rendered label is never derived from _sim_mode, so
    it neither reflects the current state nor the destination.
  technical_notes: >
    - manager.py _draw_options_mode(): the lower button label string is fixed.
    - manager.py _on_simulation_mode(): toggle logic is correct; only the label is
      non-indicating.
    - The DISCONNECTED screen 'Simulate' button is out of scope: that screen only
      appears when simulation is off, so its fixed label is already correct.
  related_issues:
    - issue_ref: "issue-f3e2d1c0"
      relationship: "related"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  approach: "Implement per change-85cc0241 and prompt-85cc0241"
  change_ref: "change-85cc0241"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-29 | Initial issue. |

---

Copyright (c) 2026 William Watson. MIT License.
