Created: 2026 August 12

# Prompt: Dispatch Short Presses to the Touch Coordinator Unconditionally

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-7d4e91a3"
  task_type: "debug"
  source_ref: "change-7d4e91a3"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-7d4e91a3"
    change_iteration: 1

context:
  purpose: >
    Make every registered touch region reachable. At present
    TouchHandler._handle_short_press calls into the touch coordinator
    only when config.mode is DisplayMode.OPTIONS, so the DISCONNECTED
    screen's Setup and Simulate buttons and the ACKNOWLEDGEMENT
    screen's dismiss region are registered, drawn, and never
    hit-tested.
  integration: >
    Two edits in one file: src/gtach/display/touch.py. No other source
    file is modified. No new imports, no new dependencies.
  knowledge_references:
    - "ai/workspace/issues/issue-7d4e91a3-touch-dispatch-gated-on-options-mode.md"
    - "ai/workspace/change/change-7d4e91a3-unconditional-touch-dispatch.md"
  constraints:
    - "Do not modify src/gtach/display/manager.py. _register_touch_regions is correct as written."
    - "Do not modify src/gtach/display/input/touch_coordinator.py. handle_touch_down already returns None on no hit."
    - "Do not add a DISCONNECTED member to DisplayMode in src/gtach/display/models.py. DISCONNECTED is a derived state within RADIAL by design."
    - "Do not alter the setup-mode branch or either swipe branch of _handle_short_press. Both already work and both return before the new dispatch."
    - "Retain the `from .models import DisplayMode` import at touch.py:26. It is still used at touch.py:306."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: >
    Apply edits A and B exactly as specified, then add the unit tests
    in the testing section.
  requirements:
    functional:
      - "A short press that is neither a setup-mode touch nor a swipe is dispatched to DisplayManager.handle_touch_event on every screen, with no mode test."
      - "A short press on a screen with no registered regions is a no-op that logs one DEBUG line and raises nothing."
      - "The setup-mode branch and both swipe branches retain their existing early returns."
      - "A long press on the DISCONNECTED screen behaves as on every other screen."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance: []

design:
  architecture: >
    Remove a screen-enumerating conditional from the dispatch path. The
    coordinator already knows which regions exist on the current
    screen, because DisplayManager._register_touch_regions rebuilds
    that set on every render pass. The handler therefore does not need
    to know which screens exist, and must not.
  components:
    - name: "EDIT A — src/gtach/display/touch.py: unconditional dispatch in _handle_short_press"
      type: "function"
      purpose: "Reach the coordinator on every screen rather than only in OPTIONS."
      logic:
        - "In _handle_short_press, locate the block currently at touch.py:239-241:  if self.display_manager.config.mode == DisplayMode.OPTIONS: / self._handle_options_touch(x, y) / return"
        - "REPLACE that block with an unconditional dispatch: call action = self.display_manager.handle_touch_event((x, y)), then log at DEBUG f\"Touch dispatch at ({x}, {y}) -> {action}\"."
        - "The dispatch must be the LAST statement of the try block, after the setup branch (touch.py:189-191) and after the swipe branch's return (touch.py:237). Do not reorder or alter either."
        - "Leave the existing `except Exception as e:` handler and its logger.error call intact. Add exc_info=True to it if not already present, so a raising region callback is diagnosable."
        - "Replace the block comment currently at touch.py:193-207 with one that states the new rule: the coordinator is consulted on every screen; screens with no registered regions are a no-op by construction, because _register_touch_regions clears regions on every render pass (manager.py:1454), returns early for SPLASH, and registers nothing for connected RADIAL (manager.py:1484). Cite issue-7d4e91a3. Retain the parts of the existing comment that explain why the swipe tests precede the dispatch."
        - "DELETE the method _handle_options_touch in its entirety (touch.py:246-266). Its only caller is the block being replaced. Verify no other reference exists before deleting."
    - name: "EDIT B — src/gtach/display/touch.py: remove the inert DISCONNECTED branch from _handle_long_press"
      type: "function"
      purpose: "Delete a branch that logs an action it does not perform."
      logic:
        - "In _handle_long_press, DELETE the block currently at touch.py:154-166: the local `from ..core import ThreadStatus` import, the thread_status and is_disconnected assignments, and the entire `if is_disconnected:` block including its logger.info call, its comments and its bare return."
        - "The method retains its docstring, the surviving comment block at touch.py:168-178, the delegating call self.display_manager._handle_long_press((x, y), (x, y)), and the except handler."
        - "Amend the surviving comment: the sentence 'Retained without a mode change so the disconnected early return above still runs' no longer holds and must be removed, since that early return is gone. Record instead that a long press now delegates to the DisplayManager on every screen, including DISCONNECTED, where it toggles the palette as it does elsewhere (issue-7d4e91a3, change-2b6f4d91)."
        - "Confirm that ThreadStatus is not referenced elsewhere in touch.py after the deletion. It is a function-local import used by this branch alone."

data_schema:
  entities: []

error_handling:
  strategy: >
    A raising region callback must not break touch handling for
    subsequent presses. The existing try/except in _handle_short_press
    is the containment boundary and is retained unchanged in structure.
  exceptions:
    - exception: "Exception"
      condition: "DisplayManager.handle_touch_event raises, including from a region callback."
      handling: "Caught by the existing handler in _handle_short_press; logged at ERROR with exc_info=True; not propagated."
  logging:
    level: "DEBUG"
    format: "Existing _LOG_FORMAT in main.py; no format change."

testing:
  unit_tests:
    - scenario: "Short press, is_in_setup_mode() False, displacement below the swipe threshold, config.mode RADIAL."
      expected: "display_manager.handle_touch_event called exactly once with the tuple (x, y)."
    - scenario: "Same, but config.mode ACKNOWLEDGEMENT."
      expected: "display_manager.handle_touch_event called exactly once with (x, y)."
    - scenario: "Same, but config.mode OPTIONS."
      expected: "display_manager.handle_touch_event called exactly once with (x, y)."
    - scenario: "Short press with is_in_setup_mode() True."
      expected: "_handle_setup_touch called; handle_touch_event NOT called."
    - scenario: "Press with dy at or above the swipe threshold and abs(dy) > abs(dx), dy positive."
      expected: "_handle_swipe_down called; handle_touch_event NOT called."
    - scenario: "Press with dx at or above the swipe threshold and abs(dx) > abs(dy), dx negative."
      expected: "_handle_swipe_left called; handle_touch_event NOT called."
    - scenario: "handle_touch_event raises RuntimeError."
      expected: "_handle_short_press returns normally; the error is logged; the exception does not propagate."
    - scenario: "_handle_long_press invoked with the OBD thread not RUNNING and sim mode off."
      expected: "display_manager._handle_long_press called with ((x, y), (x, y)); no 'entering SETUP' message logged."
  edge_cases:
    - "Displacement exactly equal to the swipe threshold — the existing >= test must be preserved, so it is a swipe and does not dispatch."
    - "Exact diagonal, abs(dx) == abs(dy), at or above the threshold — must continue to fall to the vertical branch, per the existing comment."
    - "handle_touch_event returns None — the DEBUG line must still be logged and nothing else must happen."
  validation:
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/display/touch.py').read())\""

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing file in place. Do not create new modules."
  files:
    - path: "src/gtach/display/touch.py"
      content: "EDIT A and EDIT B"
    - path: "tests/test_touch_dispatch.py"
      content: "Unit tests for testing.unit_tests items 1-8"

success_criteria:
  - "grep -n '_handle_options_touch' src/gtach/display/touch.py returns no match."
  - "No executable occurrence of '_handle_options_touch' remains anywhere in src/ or tests/ (searching those two trees only; occurrences in ai/ T-Docs are out of scope)."
  - "In _handle_short_press, the call to self.display_manager.handle_touch_event is not enclosed by any test of self.display_manager.config.mode."
  - "The setup-mode branch and both swipe branches of _handle_short_press retain their early returns and are otherwise unchanged."
  - "grep -n 'ThreadStatus' src/gtach/display/touch.py returns no match."
  - "grep -n 'Long press from DISCONNECTED' src/gtach/display/touch.py returns no match."
  - "_handle_long_press still calls self.display_manager._handle_long_press((x, y), (x, y))."
  - "The import at src/gtach/display/touch.py line 26, 'from .models import DisplayMode', is retained, and DisplayMode remains referenced in the file."
  - "src/gtach/display/manager.py, src/gtach/display/input/touch_coordinator.py and src/gtach/display/models.py are byte-identical to their pre-change state."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "touch"
        path: "src/gtach/display/touch.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "models"
        path: "src/gtach/display/models.py"
    classes:
      - name: "TouchHandler"
        module: "gtach.display.touch"
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "TouchEventCoordinator"
        module: "gtach.display.input.touch_coordinator"
      - name: "DisplayMode"
        module: "gtach.display.models"
    functions:
      - name: "_handle_short_press"
        module: "gtach.display.touch"
        signature: "(self, x: int, y: int, start_x: int, start_y: int) -> None"
      - name: "_handle_long_press"
        module: "gtach.display.touch"
        signature: "(self, x: int, y: int) -> None"
      - name: "handle_touch_event"
        module: "gtach.display.manager"
        signature: "(self, pos: Tuple[int, int]) -> Optional[object]"
      - name: "handle_touch_down"
        module: "gtach.display.input.touch_coordinator"
        signature: "(self, pos: Tuple[int, int]) -> Optional[TouchAction]"
    constants: []

notes: >
  On-target verification is a human step and is not part of this
  prompt. After deployment to gtach.local with no reachable OBD
  transport: tap Setup on the DISCONNECTED screen and confirm setup
  mode is entered; tap Simulate and confirm simulation mode is entered;
  confirm the ACKNOWLEDGEMENT screen dismisses on tap; confirm a tap on
  the connected RADIAL gauge does nothing and logs no error; confirm
  swipe navigation and OPTIONS paging are unchanged.

  Note one intended behaviour change from EDIT B: a long press on the
  DISCONNECTED screen will now toggle the day/night palette, as it does
  on every other screen. This is deliberate and is recorded under
  rational.risks in change-7d4e91a3.

  Two prior issues, issue-f3e2d1c0 and issue-f3a7c2e1, closed on the
  registration half of this feature without verifying that a callback
  fired. Verification of this change must observe an effect on target,
  not a registration line in a log.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial prompt implementing change-7d4e91a3 iteration 1. Two edits in src/gtach/display/touch.py plus one unit test module. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
