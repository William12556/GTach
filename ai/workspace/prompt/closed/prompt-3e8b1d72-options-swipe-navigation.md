Created: 2026 August 05

# Prompt: Swipe Down for Options, Swipe Up to Come Back

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-3e8b1d72"
  task_type: "implementation"
  source_ref: "change-3e8b1d72"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-3e8b1d72"
    change_iteration: 1

context:
  purpose: >
    One long press both enters and leaves the OPTIONS screen. When its
    leaving branch broke on target the operator had no second route and
    had to restart. Two distinct gestures fail independently. The touch
    subsystem already detects SWIPE_UP and SWIPE_DOWN and dispatches
    them to registered callbacks; nothing is registered.
  integration: >
    Two files: src/gtach/display/manager.py and
    src/gtach/display/touch.py. Executor is Claude Code; AEL is not
    used.

    PREREQUISITE — change-7f2a9c04 MUST HAVE LANDED. It repoints
    touch.py:171 to RADIAL and removes the horizontal-swipe branch from
    _handle_short_press. If TouchHandler._handle_long_press still names
    DisplayMode.DIGITAL, STOP and report: this prompt is being executed
    out of order and the swipe-up exit would appear to fail for a reason
    unrelated to itself.

    NOTHING IN display/input NEEDS CHANGING. GestureType declares
    SWIPE_UP and SWIPE_DOWN (interfaces.py:23-26); _recognize_gesture
    returns them for a vertical movement past the threshold
    (touch_coordinator.py:520-525); handle_gesture dispatches to
    registered callbacks (touch_coordinator.py:340-345). This is a
    registration, not a subsystem change. Do not confuse it with the
    double-tap palette toggle of change-5012004e, which is unreachable
    because GestureType has no DOUBLE_TAP member.

    TWO LIVE HANDLER PATHS. DisplayManager._handle_long_press is
    registered with the coordinator. TouchHandler._handle_long_press is
    reached from the legacy path, which registers directly on the touch
    interface (touch.py:78). The on-target log shows the TouchHandler
    one firing. BOTH must change together, or OPTIONS becomes enterable
    by one route and unleavable by the other — which is the failure this
    change exists to prevent.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and src/gtach/display/touch.py."
    - "Do NOT modify src/gtach/display/input/. The gestures already exist and already dispatch."
    - "Do NOT add a DOUBLE_TAP member or otherwise attempt to fix change-5012004e's palette toggle. Different problem."
    - "Do NOT disturb the conditional DOUBLE_TAP registration in _setup_touch_callbacks. It must survive byte-identical."
    - "Do NOT duplicate the entry/exit logic in TouchHandler. Delegate to the DisplayManager handlers, so the two paths agree by construction."
    - "Do NOT return to RADIAL unconditionally on exit. Restore the recorded entry mode; OPTIONS is reachable from the DISCONNECTED condition and returning to a dataless gauge would be wrong."
    - "Do NOT change the swipe threshold or any coordinator setting."
    - "Do NOT re-register LONG_PRESS. Its removal is the point; retaining it is the recorded fallback if the on-target trial fails, not a default."
    - "Do NOT touch the horizontal swipes or the coordinator's MODE_CHANGE default for them."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Register SWIPE_DOWN to enter OPTIONS and SWIPE_UP to return to the
    screen it was entered from, in both live handler paths. Retire the
    long-press toggle. Update the options footer text.
  requirements:
    functional:
      - "A downward swipe from RADIAL or the disconnected screen enters OPTIONS."
      - "An upward swipe from OPTIONS returns to the mode recorded on entry."
      - "With no recorded mode, an upward swipe returns to RADIAL."
      - "A downward swipe while already in OPTIONS does nothing."
      - "An upward swipe while not in OPTIONS does nothing."
      - "Neither gesture acts in SPLASH, in ACKNOWLEDGEMENT, or while in setup mode."
      - "A long press no longer enters or leaves OPTIONS, by either path."
      - "The legacy TouchHandler path produces identical outcomes to the coordinator path."
      - "The options footer reads 'Swipe up to return'."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Neutral. Gesture handling runs at human rates"
      metric: "time"

design:
  architecture: >
    A gesture that carries its own direction does not depend on state
    the operator cannot see, and two gestures fail independently where
    one cannot. The legacy path delegates rather than duplicating,
    because two copies of the entry/exit rule is how the paths would
    come to disagree.
  components:
    - name: "DisplayManager._pre_options_mode"
      type: "attribute"
      purpose: "The mode to return to."
      logic:
        - "Initialised to None in __init__."
        - "Set on entry, read on exit, defaults to RADIAL if unset."
    - name: "DisplayManager._handle_swipe_down"
      type: "function"
      purpose: "Enter OPTIONS."
      interface:
        inputs:
          - name: "start_pos"
            type: "Tuple[int, int]"
          - name: "end_pos"
            type: "Tuple[int, int]"
        outputs:
          type: "TouchAction"
      logic:
        - "Return NONE if self._in_setup_mode."
        - "Return NONE if self.config.mode is OPTIONS, SPLASH or ACKNOWLEDGEMENT."
        - "Record self._pre_options_mode = self.config.mode."
        - "Set self._options_view = 'menu'."
        - "Set self.config.mode = DisplayMode.OPTIONS."
        - "Return TouchAction.NAVIGATION."
    - name: "DisplayManager._handle_swipe_up"
      type: "function"
      purpose: "Leave OPTIONS."
      logic:
        - "Return NONE if self._in_setup_mode."
        - "Return NONE unless self.config.mode is OPTIONS."
        - "Set self._options_view = 'menu'."
        - "Set self.config.mode = self._pre_options_mode or DisplayMode.RADIAL."
        - "Clear self._pre_options_mode."
        - "Return TouchAction.NAVIGATION."
    - name: "TouchHandler._handle_short_press"
      type: "function"
      purpose: "Detect the vertical swipe on the legacy path and delegate."
      logic:
        - "Keep the setup and OPTIONS early returns exactly as they are."
        - "Compute dy = y - start_y; if abs(dy) meets the threshold, call the DisplayManager handler and return."
        - "NOTE the ordering problem: the existing OPTIONS early return sends every short press in OPTIONS to _handle_options_touch, so an upward swipe there would never reach the delegation. The swipe test must come BEFORE that early return. See EDIT 5."
  dependencies:
    internal:
      - "change-7f2a9c04 — prerequisite."
      - "TouchEventCoordinator.register_gesture_callback — touch_coordinator.py:366. Read-only."
      - "change-5012004e's conditional DOUBLE_TAP registration — must survive."
    external: []

error_handling:
  strategy: >
    A gesture handler that raises must not propagate onto the touch
    thread. Both new handlers follow the existing convention: catch,
    log, return NONE.
  exceptions:
    - exception: "Exception"
      condition: "Anything in either new handler."
      handling: "Log at ERROR with the message and return TouchAction.NONE, matching the surviving gesture handlers' style."
  logging:
    level: "ERROR on failure; DEBUG on a rejected gesture so an unresponsive swipe is diagnosable from the log"
    format: "self.logger.error(f'Swipe down handling error: {e}')"

testing:
  unit_tests:
    - scenario: "SWIPE_DOWN through a real coordinator with the mode RADIAL."
      expected: "Mode OPTIONS; _pre_options_mode RADIAL; NAVIGATION."
    - scenario: "SWIPE_UP through the coordinator with the mode OPTIONS and _pre_options_mode RADIAL."
      expected: "Mode RADIAL; NAVIGATION."
    - scenario: "Down then up from RADIAL."
      expected: "Back at RADIAL."
    - scenario: "Down then up with the obd_protocol thread not RUNNING and _sim_mode false."
      expected: "The disconnected screen again — the recorded mode is restored and the disconnected render takes precedence by itself."
    - scenario: "SWIPE_UP with _pre_options_mode None."
      expected: "RADIAL."
    - scenario: "SWIPE_DOWN while the mode is OPTIONS."
      expected: "No change; NONE."
    - scenario: "SWIPE_UP while the mode is RADIAL."
      expected: "No change; NONE."
    - scenario: "Each gesture with the mode SPLASH, with ACKNOWLEDGEMENT, and with _in_setup_mode True."
      expected: "No change in all six combinations."
    - scenario: "LONG_PRESS through the coordinator."
      expected: "No mode change; no callback registered."
    - scenario: "TouchHandler._handle_long_press with the mode OPTIONS."
      expected: "No mode change."
    - scenario: "TouchHandler._handle_short_press with dy of +150, mode RADIAL, not in setup."
      expected: "OPTIONS entered."
    - scenario: "TouchHandler._handle_short_press with dy of -150, mode OPTIONS."
      expected: "The recorded mode restored. This is the case the early-return ordering breaks if EDIT 5 is done wrongly."
    - scenario: "The full down-then-up pairing driven through the coordinator path, and again through the TouchHandler path."
      expected: "Identical outcomes. THIS IS THE PRINCIPAL TEST."
    - scenario: "TouchHandler._handle_short_press with a small dy inside OPTIONS."
      expected: "Routed to _handle_options_touch as before — a tap on a button still works."
    - scenario: "TouchHandler._handle_short_press while in setup mode."
      expected: "Routed to _handle_setup_touch as before."
    - scenario: "The conditional DOUBLE_TAP registration after the edit."
      expected: "Present and unchanged."
    - scenario: "_draw_options_menu footer string."
      expected: "'Swipe up to return'."
  edge_cases:
    - "THE EARLY-RETURN ORDERING. _handle_short_press currently returns early for OPTIONS before any swipe logic. An upward swipe inside OPTIONS must be tested before that return or the exit is unreachable from the legacy path — and the coordinator path would then be the only exit, reproducing the single-route failure in a new form."
    - "A tap inside OPTIONS must still reach _handle_options_touch. Only movements past the swipe threshold are diverted."
    - "The coordinator dispatches a recognised gesture during touch MOVE, not on release (touch_coordinator.py:265-271), so the handler fires mid-drag. Entering OPTIONS mid-drag is acceptable; confirm the subsequent touch-up does not then activate a button on the newly shown screen."
    - "The DISCONNECTED screen is a derived condition, not a DisplayMode, so _pre_options_mode records whatever mode was set beneath it. Restoring that mode returns to the disconnected screen automatically while the condition holds."
    - "_options_view is reset to 'menu' on both entry and exit, so a confirmation sub-view abandoned by swipe is not waiting on the next entry — the same reason change-b02ed4ea reset it in the long-press handler."
  validation:
    - "grep confirms no LONG_PRESS registration remains in _setup_touch_callbacks."
    - "grep confirms DisplayManager._handle_long_press is absent."
    - "git diff confirms display/input/ is untouched."
    - "git diff confirms the conditional DOUBLE_TAP block is unchanged."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        FOUR EDITS.

        EDIT 1 — the remembered mode. In __init__, beside the other
        display state:

            # The mode OPTIONS was entered from, restored on exit.
            # Not simply RADIAL: OPTIONS is reachable from the
            # DISCONNECTED condition too, and returning to a gauge with
            # no data would be wrong (change-3e8b1d72).
            self._pre_options_mode = None

        EDIT 2 — the two handlers. Add beside the surviving gesture
        handlers:

            def _handle_swipe_down(self, start_pos, end_pos) -> TouchAction:
                """Enter the OPTIONS screen.

                Paired with _handle_swipe_up. The long press that
                previously did both was a toggle, and when its leaving
                branch failed the operator had no second route
                (issue-3e8b1d72).
                """
                try:
                    if self._in_setup_mode:
                        return TouchAction.NONE
                    if self.config.mode in (
                        DisplayMode.OPTIONS,
                        DisplayMode.SPLASH,
                        DisplayMode.ACKNOWLEDGEMENT,
                    ):
                        return TouchAction.NONE
                    self._pre_options_mode = self.config.mode
                    self._options_view = 'menu'
                    self.config.mode = DisplayMode.OPTIONS
                    return TouchAction.NAVIGATION
                except Exception as e:
                    self.logger.error(f'Swipe down handling error: {e}')
                    return TouchAction.NONE

            def _handle_swipe_up(self, start_pos, end_pos) -> TouchAction:
                """Return to the screen OPTIONS was entered from."""
                try:
                    if self._in_setup_mode:
                        return TouchAction.NONE
                    if self.config.mode != DisplayMode.OPTIONS:
                        return TouchAction.NONE
                    self._options_view = 'menu'
                    self.config.mode = (
                        self._pre_options_mode or DisplayMode.RADIAL
                    )
                    self._pre_options_mode = None
                    return TouchAction.NAVIGATION
                except Exception as e:
                    self.logger.error(f'Swipe up handling error: {e}')
                    return TouchAction.NONE

        EDIT 3 — registration. In _setup_touch_callbacks, replace the
        LONG_PRESS registration with the two swipes:

            # OPTIONS is entered by a downward swipe and left by an
            # upward one. The long press that did both was a toggle
            # with no second route when one direction failed
            # (change-3e8b1d72). The coordinator already recognises
            # both gestures; only the callbacks were missing.
            self.touch_coordinator.register_gesture_callback(
                GestureType.SWIPE_DOWN, self._handle_swipe_down
            )
            self.touch_coordinator.register_gesture_callback(
                GestureType.SWIPE_UP, self._handle_swipe_up
            )

        LEAVE the conditional DOUBLE_TAP block below it exactly as it
        is. It belongs to change-5012004e.

        EDIT 4 — remove DisplayManager._handle_long_press entirely, and
        change _draw_options_menu's footer from:

            "Long press to return"

        to:

            "Swipe up to return"
    - path: "src/gtach/display/touch.py"
      content: |
        TWO EDITS.

        EDIT 5 — the legacy short-press path. READ THE WHOLE METHOD
        FIRST; the ordering matters more than the edit.

        _handle_short_press currently returns early for setup mode and
        then for OPTIONS, before any swipe logic. An upward swipe inside
        OPTIONS would therefore be routed to _handle_options_touch and
        never reach the exit. The vertical-swipe test must come AFTER
        the setup early return and BEFORE the OPTIONS early return.

        Insert, between the two early returns:

                # Vertical swipes move between the gauge and OPTIONS.
                # Tested before the OPTIONS early return, or an upward
                # swipe inside OPTIONS would be routed to
                # _handle_options_touch and the screen would again have
                # only one exit (change-3e8b1d72).
                dy = y - start_y
                if abs(dy) >= 100:
                    if dy > 0:
                        self.display_manager._handle_swipe_down(
                            (start_x, start_y), (x, y)
                        )
                    else:
                        self.display_manager._handle_swipe_up(
                            (start_x, start_y), (x, y)
                        )
                    return

        Delegate; do not reimplement the entry and exit rules here. Two
        copies is how the two paths would come to disagree.

        The threshold of 100 matches the value the removed horizontal
        branch used. If the coordinator's swipe_threshold is readable
        from here, prefer it and say so in the commit message.

        EDIT 6 — the legacy long press. In _handle_long_press, remove
        the mode-changing branch that change-7f2a9c04 repointed to
        RADIAL, so a long press no longer enters or leaves OPTIONS:

                if self.display_manager.config.mode != DisplayMode.OPTIONS:
                    self.display_manager.change_mode(DisplayMode.OPTIONS)
                else:
                    self.display_manager.change_mode(DisplayMode.RADIAL)

        becomes:

                # OPTIONS is reached by swiping, not by long press
                # (change-3e8b1d72). Retained without a mode change so
                # the disconnected early return above still runs.
                self.logger.debug('Long press: no action')

        KEEP the disconnected early return above it exactly as it is.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/display/touch.py passes."
  - "pytest tests/ passes with no new failures."
  - "SWIPE_DOWN from RADIAL enters OPTIONS and records RADIAL."
  - "SWIPE_UP from OPTIONS restores the recorded mode."
  - "SWIPE_UP with no recorded mode yields RADIAL."
  - "Neither gesture acts in OPTIONS-already, SPLASH, ACKNOWLEDGEMENT or setup mode."
  - "The down-then-up pairing produces identical outcomes through the coordinator path and through the TouchHandler path."
  - "An upward swipe inside OPTIONS reaches the exit via the legacy path — the early-return ordering is correct."
  - "A tap inside OPTIONS still reaches _handle_options_touch."
  - "No LONG_PRESS registration remains and DisplayManager._handle_long_press is absent."
  - "TouchHandler._handle_long_press changes no mode and retains its disconnected early return."
  - "The conditional DOUBLE_TAP registration is byte-identical to its current text."
  - "src/gtach/display/input/ is byte-identical."
  - "_draw_options_menu's footer reads 'Swipe up to return'."
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
      - name: "GestureType"
        module: "gtach.display.input.interfaces"
    functions:
      - name: "_handle_swipe_down"
        module: "gtach.display.manager"
        signature: "_handle_swipe_down(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> TouchAction"
      - name: "_handle_swipe_up"
        module: "gtach.display.manager"
        signature: "_handle_swipe_up(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> TouchAction"
      - name: "_setup_touch_callbacks"
        module: "gtach.display.manager"
        signature: "_setup_touch_callbacks(self) -> None"
      - name: "_handle_short_press"
        module: "gtach.display.touch"
        signature: "_handle_short_press(self, x: int, y: int, start_x: int, start_y: int) -> None"
      - name: "_handle_long_press"
        module: "gtach.display.touch"
        signature: "_handle_long_press(self, x: int, y: int) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-3e8b1d72-options-swipe-navigation.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1). Then, once you
  are finished, write a report of what you have done in the
  ai/workspace/report folder.

  Check the prerequisite first. If TouchHandler._handle_long_press still
  names DisplayMode.DIGITAL, change-7f2a9c04 has not landed and this
  prompt must not proceed.

  Two ways to get this wrong, both of which compile:

    - editing only DisplayManager's path and leaving TouchHandler's
      long press. The on-target log shows TouchHandler's handler is the
      one that fires, so the swipe would appear to do nothing;
    - putting the vertical-swipe test after the OPTIONS early return in
      _handle_short_press, which makes the upward exit unreachable from
      the legacy path and reproduces the single-route failure this
      change exists to remove.

  The on-target trial is part of the work, not a formality. Whether a
  vertical swipe is comfortable on a round bezel-less panel, and whether
  it fires accidentally while driving, is not something a bench test
  answers. If it goes badly the recorded fallback is to re-register
  LONG_PRESS alongside the swipes — one line — rather than to revert.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-3e8b1d72. |

---

Copyright (c) 2026 William Watson. MIT License.
