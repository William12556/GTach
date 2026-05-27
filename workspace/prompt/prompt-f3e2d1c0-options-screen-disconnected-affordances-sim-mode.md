Created: 2026 May 27

# Prompt: Implement OPTIONS screen, DISCONNECTED affordances, and simulation mode

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
  id: "prompt-f3e2d1c0"
  task_type: "code_generation"
  source_ref: "change-f3e2d1c0"
  date: "2026-05-27"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3e2d1c0"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Align source code with updated display design. Rename DisplayMode.SETTINGS to
    OPTIONS. Implement OPTIONS screen with two functional items. Implement DISCONNECTED
    screen on-screen affordances. Wire DISCONNECTED long-press to SETUP. Add session-only
    simulation mode.

  integration: >
    Display domain: src/gtach/display/. Models, manager, touch handler, and navigation
    gestures files are affected. No changes to Core, Comm, or Utils domains.

  constraints:
    - "No changes outside src/gtach/display/"
    - "Simulation mode is session-only — no persistence to config.yaml"
    - "Simulation mode uses synthetic RPM data in the display loop; does not require OBD transport changes"
    - "Read models.py, manager.py, touch.py before writing any changes"
    - "Exclude manager_backup.py from all changes"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Four coordinated source changes in the display domain.

  requirements:
    functional:
      - "DisplayMode.SETTINGS renamed to DisplayMode.OPTIONS in models.py"
      - "All source references to DisplayMode.SETTINGS updated to DisplayMode.OPTIONS"
      - "OPTIONS screen renders two tappable items: 'Clear settings' and 'Simulation mode'"
      - "'Clear settings' clears DeviceStore and transitions mode to SETUP"
      - "'Simulation mode' sets session flag and transitions mode to DIGITAL"
      - "Long press from OPTIONS returns to DIGITAL"
      - "DISCONNECTED screen renders two visible on-screen buttons: 'Setup' and 'Simulate'"
      - "'Setup' button tap transitions to SETUP"
      - "'Simulate' button tap sets session flag and transitions to DIGITAL"
      - "Long press on DISCONNECTED transitions to SETUP"
      - "Simulation mode: display loop generates synthetic RPM (e.g. sine-wave 0–6000) instead of reading OBD queue"
      - "Simulation mode flag resets to False on application restart (session-only)"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe flag access"
        - "Comprehensive error handling"
        - "Debug logging for mode transitions"
        - "Professional docstrings"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Modify existing display domain components; no new modules"

  components:
    - name: "DisplayMode"
      type: "enum"
      purpose: "Rename SETTINGS to OPTIONS"
      logic:
        - "In models.py: change SETTINGS = auto() to OPTIONS = auto()"
        - "Update comment string"

    - name: "DisplayManager._render_options"
      type: "function"
      purpose: "Render OPTIONS screen with two tappable items"
      logic:
        - "Rename _render_settings to _render_options"
        - "Clear surface; draw two centred button rectangles"
        - "Label: 'Clear settings' (upper) and 'Simulation mode' (lower)"
        - "Store button rects as instance attributes for tap hit-testing"
        - "On tap detection: route to _on_clear_settings() or _on_simulation_mode()"

    - name: "DisplayManager._on_clear_settings"
      type: "function"
      purpose: "Clear DeviceStore and enter SETUP"
      logic:
        - "Call device_store.clear() or equivalent"
        - "Set mode to SETUP"

    - name: "DisplayManager._on_simulation_mode"
      type: "function"
      purpose: "Activate session-only simulation mode"
      logic:
        - "Set self._sim_mode = True"
        - "Set mode to DIGITAL"

    - name: "DisplayManager._render_disconnected"
      type: "function"
      purpose: "Render DISCONNECTED screen with Setup and Simulate buttons"
      logic:
        - "Retain existing disconnected indicator"
        - "Add two visible button affordances: 'Setup' (upper) and 'Simulate' (lower)"
        - "Store button rects for tap hit-testing"

    - name: "DisplayManager._display_loop"
      type: "function"
      purpose: "Use synthetic RPM when _sim_mode is True"
      logic:
        - "If self._sim_mode: generate rpm = int(3000 + 3000 * math.sin(time.time()))"
        - "Else: read from message_queue as normal"

    - name: "TouchHandler._process_touch"
      type: "function"
      purpose: "Wire long press on DISCONNECTED to SETUP"
      logic:
        - "In long press handler: if current mode is DISCONNECTED, call enter_setup()"

  dependencies:
    internal:
      - "models.py: DisplayMode"
      - "manager.py: DisplayManager"
      - "touch.py: TouchHandler"
      - "navigation_gestures.py: NavigationGestureHandler"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: "Log and continue; do not raise on touch routing failures"
  exceptions:
    - exception: "AttributeError"
      condition: "Button rect not yet initialised when tap occurs"
      handling: "Guard with hasattr check; log warning"
    - exception: "Exception in _on_clear_settings"
      condition: "DeviceStore clear fails"
      handling: "Log error with traceback; remain in OPTIONS"
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
    - scenario: "DisplayMode.OPTIONS exists; DisplayMode.SETTINGS does not"
      expected: "AttributeError on DisplayMode.SETTINGS"
    - scenario: "Long press from DIGITAL"
      expected: "config.mode == DisplayMode.OPTIONS"
    - scenario: "Tap 'Simulation mode' item"
      expected: "_sim_mode == True; config.mode == DisplayMode.DIGITAL"
    - scenario: "App restart"
      expected: "_sim_mode == False"

  edge_cases:
    - "Tap outside button bounds in OPTIONS — no action"
    - "Long press while already in SETUP — no transition"
    - "Simulation mode active when connection restored — sim mode remains until restart"

  validation:
    - "No occurrence of DisplayMode.SETTINGS in active source files (grep check)"
    - "OPTIONS screen renders two labelled buttons"
    - "Synthetic RPM produces visible number change on DIGITAL display"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deliverable

```yaml
deliverable:
  format_requirements:
    - "Modify files in place; do not create new modules"
    - "Preserve all existing behaviour not listed in scope"
  files:
    - path: "src/gtach/display/models.py"
      content: "Rename SETTINGS to OPTIONS"
    - path: "src/gtach/display/manager.py"
      content: "Update references; implement OPTIONS and DISCONNECTED screens; add _sim_mode; synthetic RPM"
    - path: "src/gtach/display/touch.py"
      content: "Wire DISCONNECTED long press to SETUP"
    - path: "src/gtach/display/navigation_gestures.py"
      content: "Update SETTINGS references to OPTIONS"

success_criteria:
  - "No reference to DisplayMode.SETTINGS in active source files"
  - "OPTIONS screen renders two tappable items without exception"
  - "DISCONNECTED screen renders Setup and Simulate buttons"
  - "Long press on DISCONNECTED transitions to SETUP"
  - "Simulation mode produces synthetic RPM on DIGITAL display"
  - "Session-only: _sim_mode not persisted to disk"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Modify four files in src/gtach/display/. Read each file before editing.
  Exclude manager_backup.py.

  1. models.py — rename DisplayMode.SETTINGS to DisplayMode.OPTIONS.

  2. manager.py —
     a. Update all DisplayMode.SETTINGS references to DisplayMode.OPTIONS.
     b. Rename _render_settings() to _render_options().
     c. Implement _render_options(): clear surface; draw two centred button rects
        labelled 'Clear settings' (upper half) and 'Simulation mode' (lower half).
        Store rects as self._options_btn_clear and self._options_btn_sim.
        Route tap events: 'Clear settings' → clear DeviceStore + mode=SETUP;
        'Simulation mode' → self._sim_mode=True + mode=DIGITAL.
     d. Update _render_disconnected(): add 'Setup' and 'Simulate' button rects
        (self._disconnected_btn_setup, self._disconnected_btn_sim).
        Route taps accordingly.
     e. Add self._sim_mode: bool = False to __init__.
     f. In _display_loop: if self._sim_mode, set rpm = int(3000 + 3000 * math.sin(time.time()))
        instead of reading message_queue.

  3. touch.py — in long press handler: if current mode is DISCONNECTED,
     call enter_setup() (or equivalent transition to SETUP).

  4. navigation_gestures.py — update DisplayMode.SETTINGS references to OPTIONS.

  Hard constraints:
  - Session-only sim mode: do not write _sim_mode to config.yaml.
  - No changes outside src/gtach/display/.
  - Preserve all existing display behaviour not in scope.

  Deliverable: modified files saved in place.
  Verify: grep for DisplayMode.SETTINGS returns no matches in active source.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-27 | Initial prompt. |

---

Copyright (c) 2026 William Watson. MIT License.
