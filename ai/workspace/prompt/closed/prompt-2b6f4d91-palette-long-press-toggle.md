Created: 2026 August 05

# Prompt: Put the Palette Toggle on the Path That Runs

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-2b6f4d91"
  task_type: "debug"
  source_ref: "change-2b6f4d91"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-2b6f4d91"
    change_iteration: 1

context:
  purpose: >
    change-5012004e delivered a complete day/night palette — a frozen
    seventeen-colour dataclass, two instances, persistence and a
    transient on-screen confirmation — that has never been displayed.
    Its toggle is registered through
    TouchEventCoordinator.register_gesture_callback, and no registration
    made through that mechanism has ever fired.
  integration: >
    Two files: src/gtach/display/manager.py and
    src/gtach/display/touch.py. Executor is Claude Code; AEL is not
    used.

    READ THIS BEFORE ANYTHING ELSE — WHY THE OBVIOUS FIX IS WRONG.
    Finding §6.2 of the v0.4.0 implementation report attributed the
    dead toggle to GestureType lacking a DOUBLE_TAP member. That is
    true and insufficient. The fuller cause:

      TouchEventCoordinator.handle_touch_up (touch_coordinator.py:279)
      and handle_touch_move (line 252) are called by NOTHING. Grep the
      tree: the only occurrences are their own definitions and the
      abstract declarations in interfaces.py.

    handle_touch_up is where LONG_PRESS and TAP are dispatched to
    registered callbacks (line 296-304). handle_touch_move is where
    swipes are dispatched (line 265-271). Neither runs. **Every
    register_gesture_callback registration is inert**, including the
    SWIPE_DOWN and SWIPE_UP registrations at manager.py:183-188.

    The swipes work anyway, because change-3e8b1d72 wired
    TouchHandler._handle_short_press to call
    display_manager._handle_swipe_down / _handle_swipe_up DIRECTLY at
    touch.py:202-209. That direct call is the only reason they function.

    THE LIVE PATH is a chain, not two parallel sources:

      touch_interface
        -> TouchHandler._handle_touch_event   (registered, touch.py:78)
        -> TouchHandler._process_touch
        -> on release, by duration (touch.py:142):
             >= config.touch_long_press -> _handle_long_press
             otherwise                  -> _handle_short_press

    So the palette toggle goes in TouchHandler._handle_long_press, by
    direct call, exactly as the swipes went into _handle_short_press.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and src/gtach/display/touch.py."
    - "Do NOT modify src/gtach/display/input/. Repairing the coordinator's dispatch is the correct long-term fix and is deliberately out of scope — it changes how every gesture and every button is delivered on a vehicle instrument."
    - "Do NOT add a DOUBLE_TAP member to GestureType. The point of this change is that none is needed."
    - "Do NOT remove the SWIPE_DOWN and SWIPE_UP registrations at manager.py:183-188. They are inert, but if this analysis is wrong in any particular, removing them breaks swipes the operator has confirmed working."
    - "Do NOT modify _toggle_palette, the Palette dataclass, the persistence or the transient confirmation. All are change-5012004e's and all work."
    - "Do NOT remove the DISCONNECTED early return in TouchHandler._handle_long_press."
    - "Do NOT change config.touch_long_press or the duration test at touch.py:142."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Rename the palette handler to the gesture it now serves, remove the
    inert double-tap registration, and delegate to the handler from
    TouchHandler's live long-press path.
  requirements:
    functional:
      - "DisplayManager._handle_double_tap no longer exists; DisplayManager._handle_long_press does, with the same body."
      - "No DOUBLE_TAP reference remains in manager.py."
      - "TouchHandler._handle_long_press calls display_manager._handle_long_press."
      - "A long press in RADIAL toggles the palette."
      - "A long press in OPTIONS, ACKNOWLEDGEMENT, SPLASH or setup mode does not."
      - "A long press while disconnected takes the existing early return."
      - "The SWIPE_DOWN and SWIPE_UP registrations are unchanged."
      - "display/input/ is unchanged."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.9)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "None. A gesture path that runs at human rates"
      metric: "time"

design:
  architecture: >
    A feature is wired where the events actually arrive. The
    coordinator's registration mechanism describes an intent the running
    system does not execute; the direct call in TouchHandler is what the
    swipes use and what works.
  components:
    - name: "DisplayManager._handle_long_press"
      type: "function"
      purpose: "Toggle the palette. Formerly _handle_double_tap."
      interface:
        inputs:
          - name: "start_pos"
            type: "Tuple[int, int]"
          - name: "end_pos"
            type: "Tuple[int, int]"
        outputs:
          type: "TouchAction"
      logic:
        - "Body unchanged from _handle_double_tap: setup guard, RADIAL guard, _toggle_palette, SETTINGS_CHANGE, exception handler returning NONE."
        - "Docstring must state that this is the palette toggle and NOT the OPTIONS toggle change-3e8b1d72 retired from this class under the same name."
    - name: "DisplayManager._setup_touch_callbacks"
      type: "function"
      purpose: "Stop pretending to register the toggle."
      logic:
        - "Delete the conditional DOUBLE_TAP block and its else-branch DEBUG line."
        - "Add a comment recording that coordinator gesture callbacks are not dispatched and that the palette toggle is wired from touch.py."
    - name: "TouchHandler._handle_long_press"
      type: "function"
      purpose: "Deliver the long press to the palette toggle."
      logic:
        - "Keep the DISCONNECTED early return exactly as it is."
        - "Replace the 'no action' DEBUG line with a delegating call."
  dependencies:
    internal:
      - "change-5012004e — supplies _toggle_palette and everything behind it. Read-only."
      - "change-3e8b1d72 — established the delegation pattern and freed the long press."
      - "TouchHandler._process_touch, touch.py:142 — detects the long press. Read-only."
    external: []

error_handling:
  strategy: >
    Unchanged. The DisplayManager handler already catches and returns
    NONE; TouchHandler's own handler already catches and logs. The
    delegation adds no new failure mode.
  exceptions:
    - exception: "Exception"
      condition: "Anything in the DisplayManager handler."
      handling: "Existing handler: log at ERROR, return TouchAction.NONE."
    - exception: "Exception"
      condition: "Anything in TouchHandler._handle_long_press."
      handling: "Existing handler at touch.py:174. Unchanged."
  logging:
    level: "Unchanged. _toggle_palette already logs 'Palette switched to <name>' at INFO"
    format: "Existing"

testing:
  unit_tests:
    - scenario: "THE ACCEPTANCE TEST. TouchHandler._handle_long_press with a stub DisplayManager, mode RADIAL, not disconnected."
      expected: "display_manager._handle_long_press called exactly once."
    - scenario: "The same test against the PRE-CHANGE file."
      expected: "Not called; a 'no action' DEBUG line logged. Run both ways and record both — a test passing against both proves nothing."
    - scenario: "DisplayManager._handle_long_press with mode RADIAL."
      expected: "_palette becomes NIGHT_PALETTE; TouchAction.SETTINGS_CHANGE returned."
    - scenario: "Called a second time."
      expected: "_palette returns to DAY_PALETTE."
    - scenario: "Called with mode OPTIONS, then ACKNOWLEDGEMENT, then SPLASH, then with _in_setup_mode True."
      expected: "No palette change and NONE returned in all four."
    - scenario: "TouchHandler._handle_long_press with the disconnected condition true."
      expected: "Early return; the DisplayManager handler not called."
    - scenario: "hasattr(DisplayManager, '_handle_double_tap')."
      expected: "False."
    - scenario: "grep DOUBLE_TAP in manager.py."
      expected: "No occurrence."
    - scenario: "_palette_notice_until after a toggle."
      expected: "Set roughly two seconds ahead, as change-5012004e specified."
    - scenario: "_save_config after a toggle."
      expected: "Called; a subsequent _load_config restores the palette."
    - scenario: "TouchHandler._handle_short_press with dy beyond the swipe threshold."
      expected: "Still calls _handle_swipe_down or _handle_swipe_up."
    - scenario: "The SWIPE_DOWN and SWIPE_UP registration calls in _setup_touch_callbacks."
      expected: "Present and unchanged."
  edge_cases:
    - "The DisplayManager handler takes (start_pos, end_pos) to match the other gesture handlers. A long press has one position; pass it twice and comment that this is deliberate rather than an oversight."
    - "A long press held over a button on the options screen: the RADIAL guard prevents any toggle, so the button behaviour is unaffected. Assert it rather than reason about it."
    - "A long press during the SPLASH screen, before _palette is meaningful: the mode guard covers it."
    - "config.touch_long_press defaults to 1.0 s. A deliberate long press is unambiguous; the muscle-memory risk is that the operator makes one expecting OPTIONS."
    - "If _toggle_palette raises — a failed save, for instance — its own handler catches it and leaves the palette unchanged. That behaviour is change-5012004e's and is not altered here."
  validation:
    - "grep confirms no DOUBLE_TAP in manager.py."
    - "git diff confirms display/input/ is untouched."
    - "git diff confirms _toggle_palette is unchanged."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        TWO EDITS.

        EDIT 1 — rename the handler. _handle_double_tap becomes
        _handle_long_press. The body does not change. Replace the
        docstring with:

            """Toggle the day/night palette. Long press, RADIAL only.

            NOT the OPTIONS toggle. A method of this name existed on
            this class until change-3e8b1d72 moved OPTIONS to the
            vertical swipes and deleted it; a reader of the git history
            will otherwise assume it has returned. This is
            change-2b6f4d91's palette toggle, which took over the long
            press because that gesture was left unclaimed.

            Args:
                start_pos: Gesture start coordinates.
                end_pos: Gesture end coordinates. For a long press this
                    is the same point as start_pos.

            Returns:
                SETTINGS_CHANGE when the palette was toggled, NONE
                otherwise.
            """

        EDIT 2 — remove the inert registration. In
        _setup_touch_callbacks, delete the whole conditional block:

            _double_tap = getattr(GestureType, 'DOUBLE_TAP', None)
            if _double_tap is not None:
                self.touch_coordinator.register_gesture_callback(
                    _double_tap, self._handle_double_tap
                )
            else:
                self.logger.debug(
                    'GestureType has no DOUBLE_TAP; palette toggle is '
                    'unreachable by gesture until the touch subsystem '
                    'provides it'
                )

        Replace it with:

            # The palette toggle is NOT registered here. Gesture
            # callbacks registered with the coordinator are never
            # invoked: handle_touch_up and handle_touch_move, which
            # dispatch to them, are called by nothing
            # (issue-2b6f4d91). The registrations above are inert for
            # the same reason — the vertical swipes work because
            # TouchHandler calls the handlers directly at
            # touch.py:202-209, and the palette toggle is wired the
            # same way in TouchHandler._handle_long_press.

        LEAVE the SWIPE_DOWN and SWIPE_UP registration calls above it
        exactly as they are. They do nothing, and removing them is out
        of scope precisely because the operator has confirmed the
        swipes working and the risk of being wrong is not worth the
        tidiness.

        If GestureType is now unused in manager.py, leave the import
        alone unless the compile check flags it — the SWIPE
        registrations still reference it.
    - path: "src/gtach/display/touch.py"
      content: |
        EDIT 3 — deliver the gesture. In TouchHandler._handle_long_press,
        replace:

                self.logger.debug('Long press: no action')

        with:

                # Delegate to the DisplayManager, which owns the mode
                # gating and the palette state. Called directly rather
                # than through the touch coordinator, whose gesture
                # callbacks are never dispatched (issue-2b6f4d91) —
                # the same route change-3e8b1d72 used for the vertical
                # swipes. A long press has one position, so it is
                # passed as both start and end.
                self.display_manager._handle_long_press((x, y), (x, y))

        KEEP the DISCONNECTED early return above it exactly as it is —
        a long press on the disconnected screen must not toggle the
        palette, and that branch returns before reaching this line.

        KEEP the surrounding try/except at touch.py:173-174 unchanged.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/display/touch.py passes."
  - "pytest tests/ passes with no new failures."
  - "The delegation test fails against the pre-change file and passes after. Both results recorded."
  - "DisplayManager has _handle_long_press and does not have _handle_double_tap."
  - "grep -n DOUBLE_TAP src/gtach/display/manager.py returns no match."
  - "A long press in RADIAL toggles _palette between DAY_PALETTE and NIGHT_PALETTE."
  - "A long press in OPTIONS, ACKNOWLEDGEMENT, SPLASH or setup mode does not toggle."
  - "TouchHandler._handle_long_press retains its DISCONNECTED early return and does not delegate on that branch."
  - "The SWIPE_DOWN and SWIPE_UP registration calls in _setup_touch_callbacks are byte-identical to their current text."
  - "TouchHandler._handle_short_press is byte-identical to its current text."
  - "_toggle_palette, the Palette dataclass, DAY_PALETTE and NIGHT_PALETTE are byte-identical."
  - "src/gtach/display/input/ is byte-identical."
  - "No file other than the two named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "touch"
        path: "src/gtach/display/touch.py"
      - name: "touch_coordinator"
        path: "src/gtach/display/input/touch_coordinator.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "TouchHandler"
        module: "gtach.display.touch"
      - name: "TouchEventCoordinator"
        module: "gtach.display.input.touch_coordinator"
    functions:
      - name: "_handle_long_press"
        module: "gtach.display.manager"
        signature: "_handle_long_press(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> TouchAction"
      - name: "_setup_touch_callbacks"
        module: "gtach.display.manager"
        signature: "_setup_touch_callbacks(self) -> None"
      - name: "_toggle_palette"
        module: "gtach.display.manager"
        signature: "_toggle_palette(self) -> None"
      - name: "_handle_long_press"
        module: "gtach.display.touch"
        signature: "_handle_long_press(self, x: int, y: int) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-2b6f4d91-palette-long-press-toggle.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results. Then, once you are finished, write
  a report of what you have done in the ai/workspace/report folder.

  The one way to get this wrong is to conclude that the registration
  mechanism should be repaired instead — calling handle_touch_up and
  handle_touch_move from TouchHandler. That IS the correct long-term
  fix and it is explicitly out of scope: it changes how every gesture
  and every button is delivered on the live input path of a vehicle
  instrument, and buttons currently fire from handle_touch_down
  deliberately, which touch_coordinator.py:472 documents. If you think
  the wider repair is necessary, report it rather than doing it.

  This change unblocks an observation as well as a feature. The night
  palette has never been displayed, so §6.1's contrast question — day
  blue at 2.21:1 and night blue at 1.55:1 against a 3:1 criterion — has
  only ever been half answerable. The day palette has now been seen on
  the panel and reads well. After this lands the night palette can be
  judged the same way, and the criterion either vindicated or discarded
  on evidence.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-2b6f4d91. |

---

Copyright (c) 2026 William Watson. MIT License.
