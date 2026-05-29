Created: 2026 May 29

# Issue: Stale OPTIONS display mode persists after in-process setup re-entry

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
  id: "issue-c84ffe6f"
  title: "Stale OPTIONS display mode persists after in-process setup re-entry"
  date: "2026-05-29"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-c84ffe6f"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: "workspace/audit/audit-ui-navigation-logic-report.md §4.1, §5.0"
  description: >
    On-device test (2026-05-29) reported in audit-ui-navigation-logic-report.md as
    symptom S2 and Finding A. After clearing settings and re-pairing a device, the
    connected screen does not appear; the OPTIONS screen is shown instead.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "DisplayManager.exit_setup_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication._on_setup_complete"
      file_path: "src/gtach/app.py"
  designs:
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
    - design_ref: "design-gtach-master.md"
  version: "on-device build, 2026-05-29 session"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: "A paired device exists; application running in normal (connected) mode."
  steps:
    - "Long-press to enter the OPTIONS screen."
    - "Tap 'Clear settings'. The device is removed and setup is re-entered in-process."
    - "Complete pairing: select device, pair, tap Continue."
    - "Observe the screen after setup completes."
  frequency: "always"
  reproducibility_conditions: >
    Manifests only via the in-process clear-settings re-entry path. A full process
    restart does not reproduce it, because the post-splash target is derived from
    persisted config and transient modes are excluded from persistence.
  error_output: >
    gtach-debug.log: between 'Exited setup mode' (07:36:47) and the next operator
    action (07:37:24) there are no per-frame render markers for RADIAL, DIGITAL,
    DISCONNECTED, or acknowledgement modes — OPTIONS is the only mode without
    per-frame logging.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behavior

```yaml
behavior:
  expected: >
    After re-pairing completes, the display returns to the normal post-splash mode
    (RADIAL or DIGITAL), showing the connected tachometer screen.
  actual: >
    The display renders the OPTIONS screen after re-pairing, although a device is
    paired and the OBD thread is running.
  impact: >
    The operator cannot reach the connected screen after re-pairing without manually
    leaving OPTIONS. The connected display is effectively unreachable through the
    documented clear-settings workflow.
  workaround: "Long-press to leave OPTIONS, or restart the application process."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Analysis

```yaml
analysis:
  root_cause: >
    'Clear settings' is invoked from the OPTIONS screen, so config.mode == OPTIONS
    when _on_clear_settings() runs. The re-entry path (GTachApplication._re_enter_setup
    → _start_setup_mode) reuses the existing DisplayManager and never resets
    config.mode; the splash path is guarded out. On completion, _on_setup_complete
    calls exit_setup_mode() (which clears _in_setup_mode only) and _start_obd().
    Neither resets config.mode. _render_normal_modes() then dispatches on the stale
    OPTIONS value and renders _draw_options_mode().
  technical_notes: >
    - manager.py exit_setup_mode(): sets _in_setup_mode=False and _setup_manager=None
      only; does not restore a normal display mode.
    - app.py _on_setup_complete(): calls exit_setup_mode() then _start_obd();
      does not set config.mode.
    - OPTIONS is reachable only by long-press; it is a transient mode excluded from
      persistence (_save_config) and remapped to RADIAL on load (_load_config).
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
  approach: "Implement per change-c84ffe6f and prompt-c84ffe6f"
  change_ref: "change-c84ffe6f"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-29 | Initial issue. |

---

Copyright (c) 2026 William Watson. MIT License.
