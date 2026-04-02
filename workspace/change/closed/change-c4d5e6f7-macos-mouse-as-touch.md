# Change: macOS Mouse-as-Touch Input

Created: 2026-04-01

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-c4d5e6f7"
  title: "Implement mouse-as-touch gesture simulation for macOS mode"
  date: "2026-04-01"
  author: "William Watson"
  status: "verified"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c4d5e6f7"
    issue_iteration: 1

source:
  type: "enhancement"
  reference: "issue-c4d5e6f7"
  description: >
    REQ g1h2i3j4 requires touch input in macOS mode to be driven by pygame mouse
    events. The display loop currently ignores all mouse input.

scope:
  summary: >
    Add macOS-guarded mouse event handling in DisplayManager._display_loop.
    Translate MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP into swipe, long-press,
    and tap gestures. Route classified gestures to the existing gesture handler.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
      sections:
        - "Display loop event processing"
  out_of_scope:
    - "Changes to NavigationGestureHandler or TouchEventCoordinator"
    - "Any Pi/Linux event handling"
    - "New gesture types beyond swipe-left, swipe-right, long-press, tap"

rational:
  problem_statement: >
    Without mouse input, no gesture-driven functionality (mode switching, setup
    entry via long-press) is accessible on macOS. macOS mode cannot serve as a
    functional test environment for the Pi application.
  proposed_solution: >
    Intercept pygame mouse events inside _display_loop on macOS. Track button-down
    position and timestamp. On button-up, classify the gesture by horizontal delta
    and hold duration, then invoke the corresponding handler on gesture_handler or
    touch_coordinator. MOUSEMOTION with button held feeds into swipe tracking.
  alternatives_considered:
    - option: "Inject synthetic pygame.FINGERDOWN/FINGERUP events"
      reason_rejected: >
        Requires pygame.FINGERDOWN event type which behaves differently per platform.
        Direct gesture classification in the event loop is simpler and more reliable.
    - option: "Subclass NavigationGestureHandler to consume mouse events"
      reason_rejected: >
        Unnecessary indirection. The existing handler interface already accepts
        classified gestures; translation at the event loop boundary is sufficient.
  benefits:
    - "All gesture-driven UI paths exercisable on macOS via mouse"
    - "No new dependencies"
    - "Zero impact on Pi production code path"
  risks:
    - risk: "Gesture thresholds may feel different with mouse vs finger"
      mitigation: >
        Use the same swipe_threshold and long_press duration values already
        configured in NavigationGestureHandler/GestureConfig. Tune if needed.

technical_details:
  current_behavior: >
    _display_loop iterates pygame.event.get() and checks only for pygame.QUIT.
    All other event types are ignored.
  proposed_behavior: >
    On macOS (platform.system() == 'Darwin'), the event loop additionally handles:
    - pygame.MOUSEBUTTONDOWN (button==1): record _mouse_down_pos=(x,y),
      _mouse_down_time=time.monotonic(), _mouse_dragging=True
    - pygame.MOUSEMOTION (buttons[0]): update _mouse_current_pos=(x,y)
    - pygame.MOUSEBUTTONUP (button==1): classify gesture:
        dx = x - _mouse_down_pos.x
        dy = y - _mouse_down_pos.y
        hold = time.monotonic() - _mouse_down_time
        if hold >= LONG_PRESS_THRESHOLD (default 1.0s):
            call _handle_long_press(_mouse_down_pos, (x,y))
        elif abs(dx) >= SWIPE_THRESHOLD (default 50px) and abs(dx) > abs(dy):
            call _handle_swipe_left or _handle_swipe_right as appropriate
        else:
            call handle_touch_event((x,y))  (tap)
      reset _mouse_dragging=False
    State variables (_mouse_down_pos, _mouse_down_time, _mouse_dragging,
    _mouse_current_pos) are instance-level, initialised in __init__ on Darwin.
  implementation_approach: >
    1. In __init__, detect platform and initialise mouse state variables on Darwin.
    2. In _display_loop, after existing pygame.QUIT check, add Darwin-guarded
       elif branches for MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP.
    3. Read SWIPE_THRESHOLD from GestureConfig if gesture_handler is available,
       otherwise use hardcoded default of 50px.
    4. Read LONG_PRESS_THRESHOLD from config.touch_long_press (already exists
       in DisplayConfig, default 1.0s).
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Add Darwin platform detection in __init__; add mouse state variables;
        extend _display_loop event processing with MOUSEBUTTONDOWN/MOTION/UP
        handlers; add _classify_mouse_gesture() helper method.
      functions_affected:
        - "__init__"
        - "_display_loop"
      classes_affected:
        - "DisplayManager"

dependencies:
  internal:
    - component: "NavigationGestureHandler / GestureConfig"
      impact: "Read-only: SWIPE_THRESHOLD sourced from existing config if available"
    - component: "DisplayConfig"
      impact: "Read-only: touch_long_press used as long-press duration threshold"
  external: []

testing_requirements:
  test_approach: "Manual functional test on macOS"
  test_cases:
    - scenario: "Horizontal drag left > 50px, < 1s"
      expected_result: "Display mode switches (DIGITAL <-> GAUGE)"
    - scenario: "Horizontal drag right > 50px, < 1s"
      expected_result: "Display mode switches"
    - scenario: "Mouse button held > 1s without drag"
      expected_result: "Long-press handler fires (mode -> SETTINGS or setup entry)"
    - scenario: "Click and release < 50px delta, < 1s"
      expected_result: "handle_touch_event called with click position"
    - scenario: "Same actions executed on Pi (no Darwin guard)"
      expected_result: "Behaviour unchanged; mouse handling code not reached"
  validation_criteria:
    - "All four gesture types trigger correct handler on macOS"
    - "No regression on Pi: mouse handling code path is unreachable"
    - "No new imports required"

implementation:
  implementation_steps:
    - step: "Add Darwin platform check and mouse state vars to __init__"
      owner: "AEL"
    - step: "Add MOUSEBUTTONDOWN/MOTION/UP handling in _display_loop event loop"
      owner: "AEL"
    - step: "Add _classify_mouse_gesture() helper"
      owner: "AEL"
  rollback_procedure: "Revert manager.py to prior commit"

traceability:
  design_updates:
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
      sections_updated:
        - "Event processing"
  related_issues:
    - issue_ref: "issue-c4d5e6f7"
      relationship: "resolves"

notes: >
  SWIPE_THRESHOLD and LONG_PRESS_THRESHOLD are not new configuration values.
  They are read from existing GestureConfig and DisplayConfig respectively.
  No configuration schema changes are required.

version_history:
  - version: "1.0"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Initial change document"
  - version: "1.1"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Closed — implemented by Claude Code and verified"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | William Watson | Initial change document |
| 1.1 | 2026-04-01 | William Watson | Closed — implemented by Claude Code and verified |

---

Copyright (c) 2026 William Watson. MIT License.
