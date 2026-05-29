Created: 2026 May 27

# Issue: OPTIONS screen, DISCONNECTED affordances, and simulation mode not implemented

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Behavior](<#4.0 behavior>)
- [5.0 Analysis](<#5.0 analysis>)
- [6.0 Resolution](<#6.0 resolution>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-f3e2d1c0"
  title: "OPTIONS screen, DISCONNECTED affordances, and simulation mode not implemented"
  date: "2026-05-27"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "requirement_change"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3e2d1c0"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "requirement_change"
  description: >
    Design session 2026-05-27 established four source changes required to align
    implementation with updated design documentation:
    1. DisplayMode.SETTINGS renamed to DisplayMode.OPTIONS.
    2. OPTIONS screen requires two tappable items: 'Clear settings' and 'Simulation mode'.
    3. DISCONNECTED screen requires two on-screen affordances: 'Setup' and 'Simulate'.
    4. Long press on DISCONNECTED must transition to SETUP (currently unimplemented).
    Simulation mode is session-only (does not persist across restarts).
    Design documents updated: design-g1h2i3j4, design-b8c9d0e1, design-2c6b8e4d, design-gtach-master.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "DisplayMode"
      file_path: "src/gtach/display/models.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "TouchHandler"
      file_path: "src/gtach/display/touch.py"
    - name: "NavigationGestureHandler"
      file_path: "src/gtach/display/navigation_gestures.py"
  designs:
    - design_ref: "design-g1h2i3j4-gesture_reference.md"
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
    - design_ref: "design-2c6b8e4d-domain_display.md"
    - design_ref: "design-gtach-master.md"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Behavior

```yaml
behavior:
  expected: >
    - DisplayMode enum uses OPTIONS not SETTINGS.
    - Long press from DIGITAL or RADIAL enters OPTIONS screen.
    - OPTIONS screen renders two tappable items: 'Clear settings' (→ SETUP) and
      'Simulation mode' (session-only, → DIGITAL with sim transport active).
    - Long press from OPTIONS returns to DIGITAL.
    - DISCONNECTED screen renders two on-screen affordances: 'Setup' and 'Simulate'.
    - Long press on DISCONNECTED transitions to SETUP (clears stored device).
    - Simulation mode is session-only; does not persist across restarts.

  actual: >
    - DisplayMode.SETTINGS is the active identifier.
    - Long press enters a partially implemented settings screen with no tap routing.
    - DISCONNECTED screen has no on-screen affordances.
    - Long press on DISCONNECTED does not transition to SETUP.
    - No simulation mode toggle exists in the UI.

  impact: >
    User cannot access options, cannot re-pair from DISCONNECTED without restarting the app,
    and cannot activate simulation mode from the UI.

  workaround: "Restart application to re-enter setup. Use --transport simbt CLI flag for sim mode."
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Analysis

```yaml
analysis:
  root_cause: >
    Design updated ahead of implementation. The SETTINGS → OPTIONS rename and new
    screen behaviours were specified in design documentation but source changes were
    deferred to a subsequent implementation cycle.
  technical_notes: >
    - models.py line 67: SETTINGS = auto() requires rename to OPTIONS.
    - manager.py lines 175, 181, 500: DisplayMode.SETTINGS references require update.
    - manager.py: _render_settings() requires rename to _render_options() and content
      replacement with two tappable items.
    - manager.py: _render_disconnected() requires two on-screen affordance buttons.
    - touch.py: long press on DISCONNECTED → SETUP transition not wired.
    - navigation_gestures.py lines 265, 279: SETTINGS references require update
      (file bypassed at runtime but should remain consistent).
    - Simulation mode requires a session-only boolean flag in DisplayManager and
      a mechanism to activate the simulated OBD transport path when set.
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  approach: "Implement per change-f3e2d1c0 and prompt-f3e2d1c0"
  change_ref: "change-f3e2d1c0"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-27 | Initial issue. |

---

Copyright (c) 2026 William Watson. MIT License.
