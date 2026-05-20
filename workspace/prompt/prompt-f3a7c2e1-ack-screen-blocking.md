Created: 2026 May 20

# Prompt: Implement Blocking Acknowledgement Screen

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Deliverables](<#5.0 deliverables>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Notes](<#7.0 notes>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-f3a7c2e1"
  task_type: "code_generation"
  source_ref: "change-f3a7c2e1"
  date: "2026-05-20"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a7c2e1"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    The acknowledgement screen (DisplayMode.ACKNOWLEDGEMENT) is set after
    splash but never rendered. The display loop falls through to RPM rendering
    immediately. This task adds a rendered, blocking acknowledgement screen
    that requires an explicit tap to dismiss.
  integration: >
    Display domain — src/gtach/display/manager.py only.
    AcknowledgementStateManager is already instantiated as self._ack_state_manager.
    TouchEventCoordinator is self.touch_coordinator.
  constraints:
    - "Modify src/gtach/display/manager.py only"
    - "Do not modify manager_backup.py or any backup/test file"
    - "No timeout auto-dismiss — explicit tap only"
    - "Do not alter splash screen, ack_state.py, or any other component"
    - "Long-press to settings must remain functional from ack screen"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Add a blocking acknowledgement screen to DisplayManager. When
    DisplayMode.ACKNOWLEDGEMENT is active the screen renders a prompt
    and blocks all transitions until the operator taps anywhere to dismiss.
    On dismissal: save ack state and transition to _post_splash_mode.
  requirements:
    functional:
      - "ACKNOWLEDGEMENT branch added to _render_normal_modes()"
      - "_draw_acknowledgement_mode() renders a visible prompt on a black background"
      - "Full-screen tap region registered via touch_coordinator dismisses the screen"
      - "_on_acknowledgement_dismissed() saves ack state and sets config.mode = _post_splash_mode"
      - "No auto-transition on timeout"
      - "Long-press still navigates to SETTINGS from ACKNOWLEDGEMENT mode"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Thread-safe — config.mode mutations only, no new locks required"
        - "Comprehensive error handling with DEBUG logging"
        - "Professional docstrings"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Add two methods to DisplayManager; add one branch in _render_normal_modes()"
  components:
    - name: "_render_normal_modes"
      type: "function"
      purpose: "Route ACKNOWLEDGEMENT mode to new render method"
      logic:
        - "Add 'elif self.config.mode == DisplayMode.ACKNOWLEDGEMENT:' branch"
        - "Call self._draw_acknowledgement_mode()"

    - name: "_draw_acknowledgement_mode"
      type: "function"
      purpose: "Render the acknowledgement screen and register tap dismissal"
      logic:
        - "Clear touch regions: self.touch_coordinator.clear_regions()"
        - "Fill back buffer black"
        - "Draw circular border using self._draw_shift_border((200, 0, 0))"
        - "Render title text 'GTach' centred near top of circle"
        - "Render body text: 'OBD tachometer — experimental software'"
        - "Render instruction text: 'Tap to acknowledge and continue'"
        - "Register full-screen tap region via touch_coordinator that calls self._on_acknowledgement_dismissed"

    - name: "_on_acknowledgement_dismissed"
      type: "function"
      purpose: "Handle tap dismissal — save ack state and transition mode"
      logic:
        - "Call self._ack_state_manager.save_acknowledgement(self.config.rpm_bands, self.config.engine_profile)"
        - "self.touch_coordinator.clear_regions()"
        - "self.config.mode = self._post_splash_mode"
        - "Log INFO: 'Acknowledgement dismissed — transitioning to {_post_splash_mode.name}'"

  dependencies:
    internal:
      - "DisplayMode.ACKNOWLEDGEMENT (display/models.py)"
      - "AcknowledgementStateManager.save_acknowledgement (utils/ack_state.py)"
      - "TouchEventCoordinator.clear_regions, register_button_region (display/input.py)"
      - "_draw_shift_border, _get_cached_font, rendering_engine (existing DisplayManager members)"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Modify the file in place — do not create new files"
  files:
    - path: "src/gtach/display/manager.py"
      content: "Add _draw_acknowledgement_mode, _on_acknowledgement_dismissed, and ACKNOWLEDGEMENT branch in _render_normal_modes"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "After splash, ACKNOWLEDGEMENT screen renders with visible text"
  - "Screen does not auto-transition — persists until tap"
  - "Tap dismisses screen, saves ack state, transitions to _post_splash_mode"
  - "Long-press from ack screen still enters SETTINGS"
  - "No regressions in DIGITAL, RADIAL, SETTINGS, or SPLASH modes"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Notes

```yaml
notes: >
  save_acknowledgement() signature — verify against
  src/gtach/utils/ack_state.py before implementing.
  The register_button_region signature is:
    register_button_region(name, rect, action, callback)
  Use a pygame.Rect covering the full 480x480 surface for the tap region.
  Use _get_cached_font() for all text rendering.
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  File: src/gtach/display/manager.py

  Task: Add blocking acknowledgement screen to DisplayManager.

  Steps:
  1. In _render_normal_modes(), add branch:
       elif self.config.mode == DisplayMode.ACKNOWLEDGEMENT:
           self._draw_acknowledgement_mode()

  2. Add _draw_acknowledgement_mode():
     - clear_regions()
     - fill back buffer black
     - _draw_shift_border((200, 0, 0))
     - render 'GTach' title, body warning text, 'Tap to acknowledge' instruction
     - register full-screen (480x480) tap region → self._on_acknowledgement_dismissed

  3. Add _on_acknowledgement_dismissed():
     - save_acknowledgement(self.config.rpm_bands, self.config.engine_profile)
       [verify exact signature in src/gtach/utils/ack_state.py first]
     - clear_regions()
     - self.config.mode = self._post_splash_mode
     - log INFO

  Constraints:
  - manager.py only; no backups or other files
  - No timeout auto-dismiss
  - Long-press to SETTINGS must remain functional from ack screen

  Success: ack screen renders, blocks until tapped, dismisses correctly.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-20 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
