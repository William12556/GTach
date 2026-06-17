# Prompt: macOS Mouse-as-Touch Gesture Simulation

Created: 2026-04-01

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Source Reference](<#5.0 source reference>)
- [6.0 Deliverable](<#6.0 deliverable>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-c4d5e6f7"
  task_type: "code_generation"
  source_ref: "change-c4d5e6f7"
  date: "2026-04-01"
  iteration: 1
  coupled_docs:
    change_ref: "change-c4d5e6f7"
    change_iteration: 1
```

---

## 2.0 Context

```yaml
context:
  purpose: >
    GTach runs on macOS with a pygame window for display testing. The HyperPixel
    touch screen is absent; mouse events must be translated into touch gestures so
    all gesture-driven functionality (mode switching, setup entry) is exercisable
    on macOS without Pi hardware.
  integration: >
    DisplayManager owns the pygame event loop (_display_loop). NavigationGestureHandler
    (self.gesture_handler) already classifies swipe gestures via start_gesture_tracking()
    / end_gesture_tracking() / handle_gesture_event(). Long-press has no path through
    the gesture handler (duration > max_gesture_time filters it out); _handle_long_press()
    on DisplayManager handles it directly. This change adds mouse event interception
    inside _display_loop, platform-guarded to Darwin only.
  constraints:
    - "Changes confined to src/gtach/display/manager.py"
    - "No modifications to NavigationGestureHandler, TouchEventCoordinator, or any other file"
    - "No new imports beyond platform and time (already present or stdlib)"
    - "Mouse handling code must be unreachable on non-Darwin platforms"
```

---

## 3.0 Specification

```yaml
specification:
  description: >
    Add macOS-only mouse event handling to DisplayManager._display_loop. Translate
    MOUSEBUTTONDOWN / MOUSEMOTION / MOUSEBUTTONUP into the three gesture classes
    already supported: swipe (via gesture_handler), long-press (via _handle_long_press),
    and tap (via handle_touch_event).
  requirements:
    functional:
      - "MOUSEBUTTONDOWN (button==1) starts gesture tracking and records down position and time"
      - "MOUSEMOTION with button held updates the tracked current position"
      - "MOUSEBUTTONUP (button==1) classifies and dispatches the gesture"
      - "Hold >= touch_long_press threshold dispatches long-press regardless of drag distance"
      - "Hold < threshold with drag dispatches to gesture_handler (swipe classification)"
      - "Hold < threshold without qualifying swipe dispatches tap via handle_touch_event"
      - "All mouse handling is inside a platform.system() == 'Darwin' guard"
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Preserve all existing event handling (pygame.QUIT must remain)"
        - "Mouse state variables initialised in __init__ on Darwin only"
        - "Error handling with logger.error and exc_info=True on unexpected exceptions"
        - "Debug log on each gesture classification"
```

---

## 4.0 Design

```yaml
design:
  architecture: >
    Minimal extension of the existing pygame event loop. Mouse state is tracked
    across events using instance variables. Gesture classification delegates entirely
    to existing handlers — no new gesture logic is introduced.

  components:
    - name: "DisplayManager.__init__ (Darwin additions)"
      type: "method"
      purpose: "Initialise mouse tracking state on macOS"
      logic:
        - "Detect platform.system() == 'Darwin' and set self._is_macos = True/False"
        - "On Darwin only, initialise: self._mouse_down_pos = None, self._mouse_down_time = None, self._mouse_dragging = False, self._mouse_current_pos = None"

    - name: "DisplayManager._display_loop (mouse event block)"
      type: "method section"
      purpose: "Translate mouse events into gestures on macOS"
      logic:
        - "After the existing pygame.QUIT check, add: if self._is_macos:"
        - "  MOUSEBUTTONDOWN (event.button == 1):"
        - "    self._mouse_down_pos = event.pos"
        - "    self._mouse_down_time = time.monotonic()"
        - "    self._mouse_dragging = True"
        - "    self._mouse_current_pos = event.pos"
        - "    if self.gesture_handler: self.gesture_handler.start_gesture_tracking(event.pos, self._mouse_down_time)"
        - "  MOUSEMOTION (event.buttons[0] and self._mouse_dragging):"
        - "    self._mouse_current_pos = event.pos"
        - "  MOUSEBUTTONUP (event.button == 1 and self._mouse_dragging):"
        - "    call self._dispatch_mouse_gesture(event.pos)"
        - "    reset self._mouse_dragging = False, self._mouse_down_pos = None, self._mouse_down_time = None"

    - name: "DisplayManager._dispatch_mouse_gesture"
      type: "method"
      purpose: "Classify and dispatch a completed mouse gesture"
      interface:
        inputs:
          - name: "up_pos"
            type: "Tuple[int, int]"
            description: "Mouse button-up position"
        outputs:
          type: "None"
      logic:
        - "If _mouse_down_pos or _mouse_down_time is None: return"
        - "hold = time.monotonic() - self._mouse_down_time"
        - "long_press_threshold = getattr(self.config, 'touch_long_press', 1.0)"
        - "If hold >= long_press_threshold:"
        - "  logger.debug('Mouse long-press at %s (%.2fs)', _mouse_down_pos, hold)"
        - "  call self._handle_long_press(self._mouse_down_pos, up_pos)"
        - "  return"
        - "If self.gesture_handler:"
        - "  gesture = self.gesture_handler.end_gesture_tracking(up_pos, time.monotonic())"
        - "  if gesture:"
        - "    logger.debug('Mouse gesture: %s', gesture.gesture_type.name)"
        - "    self.gesture_handler.handle_gesture_event(gesture)"
        - "    return"
        - "# Fall through: treat as tap"
        - "logger.debug('Mouse tap at %s', up_pos)"
        - "self.handle_touch_event(up_pos)"
```

---

## 5.0 Source Reference

Read the following files before implementing. Do not modify any file other than `manager.py`.

- `src/gtach/display/manager.py` — file to modify; read fully before editing
- `src/gtach/display/navigation_gestures.py` — read to confirm API:
  - `NavigationGestureHandler.start_gesture_tracking(pos, timestamp)`
  - `NavigationGestureHandler.end_gesture_tracking(pos, timestamp) -> Optional[GestureEvent]`
  - `NavigationGestureHandler.handle_gesture_event(gesture) -> bool`
- `src/gtach/display/models.py` — confirm `DisplayConfig.touch_long_press` field (default 1.0)

---

## 6.0 Deliverable

```yaml
deliverable:
  files:
    - path: "src/gtach/display/manager.py"
      content: "Modified in place — add _is_macos flag, mouse state vars, mouse event block, _dispatch_mouse_gesture method"
```

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "import platform present in manager.py (already there via _display_loop start() method — verify before adding)"
  - "import time present in manager.py (already present — verify before adding)"
  - "DisplayManager.__init__ sets self._is_macos and mouse state vars on Darwin"
  - "_display_loop handles MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP inside if self._is_macos block"
  - "_dispatch_mouse_gesture method exists and implements long-press / swipe / tap dispatch"
  - "pygame.QUIT handling is unchanged"
  - "No other files modified"
  - "No syntax errors — verify with: python -c 'import ast; ast.parse(open(\"src/gtach/display/manager.py\").read())'"
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Modify src/gtach/display/manager.py only.

  1. Read manager.py fully. Confirm 'import platform' and 'import time' are already
     present before adding them.

  2. In DisplayManager.__init__, add after existing initialisations:
       import platform as _plat
       self._is_macos = _plat.system() == 'Darwin'
       if self._is_macos:
           self._mouse_down_pos = None
           self._mouse_down_time = None
           self._mouse_dragging = False
           self._mouse_current_pos = None

  3. In _display_loop, inside the pygame.event.get() loop, after the pygame.QUIT
     check, add:
       elif self._is_macos:
           if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
               self._mouse_down_pos = event.pos
               self._mouse_down_time = time.monotonic()
               self._mouse_dragging = True
               self._mouse_current_pos = event.pos
               if self.gesture_handler:
                   self.gesture_handler.start_gesture_tracking(event.pos, self._mouse_down_time)
           elif event.type == pygame.MOUSEMOTION and self._mouse_dragging and event.buttons[0]:
               self._mouse_current_pos = event.pos
           elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._mouse_dragging:
               self._dispatch_mouse_gesture(event.pos)
               self._mouse_dragging = False
               self._mouse_down_pos = None
               self._mouse_down_time = None

  4. Add new method _dispatch_mouse_gesture(self, up_pos):
       - If _mouse_down_pos or _mouse_down_time is None: return
       - hold = time.monotonic() - self._mouse_down_time
       - long_press_threshold = getattr(self.config, 'touch_long_press', 1.0)
       - If hold >= long_press_threshold: call _handle_long_press(_mouse_down_pos, up_pos); return
       - If self.gesture_handler:
             gesture = self.gesture_handler.end_gesture_tracking(up_pos, time.monotonic())
             if gesture: self.gesture_handler.handle_gesture_event(gesture); return
       - Fallthrough tap: self.handle_touch_event(up_pos)

  5. After editing, run syntax check:
       python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"

  Do not modify any other file.
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | William Watson | Initial prompt document |
| 1.1 | 2026-04-01 | William Watson | Closed — executed by Claude Code and verified |

---

Copyright (c) 2026 William Watson. MIT License.
