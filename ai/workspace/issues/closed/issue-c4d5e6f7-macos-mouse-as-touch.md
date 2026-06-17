# Issue: macOS Mouse-as-Touch Input

Created: 2026-04-01

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-c4d5e6f7"
  title: "macOS mode provides no touch simulation — mouse events are ignored"
  date: "2026-04-01"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-c4d5e6f7"
    change_iteration: 1

source:
  origin: "requirement_change"
  description: >
    REQ g1h2i3j4 states touch input in macOS mode shall be driven by pygame
    mouse events. The display loop currently processes only pygame.QUIT. No
    mouse events are handled, so all touch-driven functionality (mode swipe,
    long-press to setup) is inaccessible on macOS.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs:
    - design_ref: "design-gtach-master.md §8.3"
    - design_ref: "design-2c6b8e4d-domain_display.md"
  version: "0.2.0"

reproduction:
  prerequisites: "Running GTach on macOS with --macos flag"
  steps:
    - "Launch application on macOS"
    - "Attempt to swipe left/right to switch display mode"
    - "Attempt long-press on disconnected screen to enter setup"
  frequency: "always"
  reproducibility_conditions: "macOS platform only"
  error_output: "No response to mouse input; gestures silently ignored"

behavior:
  expected: >
    Mouse button down/up and motion events are translated into touch gestures
    (swipe, long-press, tap) and routed to the existing gesture handler.
  actual: >
    _display_loop processes only pygame.QUIT. All other pygame events including
    MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION are discarded.
  impact: >
    All gesture-driven functionality is unavailable on macOS. Application
    cannot be used as a functional test environment for the Pi production build.
  workaround: "None"

environment:
  python_version: "3.9+"
  os: "macOS 14+ (Darwin)"
  dependencies:
    - library: "pygame"
      version: ">=2.0"
  domain: "domain_1"

analysis:
  root_cause: >
    The pygame event loop in DisplayManager._display_loop only checks for
    pygame.QUIT. Mouse event handling was never implemented.
  technical_notes: >
    Gesture classification logic (swipe threshold, long-press duration) should
    mirror the existing NavigationGestureHandler thresholds. Mouse button 1
    maps to touch down/up; MOUSEMOTION with button held maps to touch move.
    Platform guard (platform.system() == 'Darwin') confines changes to macOS.

resolution:
  approach: "Implement mouse event handling in _display_loop (macOS-guarded)"
  change_ref: "change-c4d5e6f7"
  resolved_date: "2026-04-01"
  resolved_by: "Claude Code"
  fix_description: >\n    Added _is_macos flag and mouse state variables to DisplayManager.__init__.\n    Extended _display_loop to handle MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP\n    inside Darwin-guarded block. Added _dispatch_mouse_gesture() method classifying\n    long-press, swipe, and tap, delegating to existing gesture_handler.

traceability:
  design_refs:
    - "design-gtach-master.md"
    - "design-2c6b8e4d-domain_display.md"
    - "design-b8c9d0e1-component_display_manager.md"
  change_refs:
    - "change-c4d5e6f7"

version_history:
  - version: "1.0"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Initial issue document"
  - version: "1.1"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Closed — implemented and verified"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | William Watson | Initial issue document |
| 1.1 | 2026-04-01 | William Watson | Closed — implemented and verified |

---

Copyright (c) 2026 William Watson. MIT License.
