Created: 2026 August 05

# Prompt: Free the Operator from the Options Screen

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-7f2a9c04"
  task_type: "debug"
  source_ref: "change-7f2a9c04"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-7f2a9c04"
    change_iteration: 1

context:
  purpose: >
    The operator cannot leave the OPTIONS screen on gtach.local.
    change-378703da removed DisplayMode.DIGITAL under a four-file
    constraint that excluded display/touch.py and
    display/navigation_gestures.py. Both still reference it, both are
    constructed at runtime, and TouchHandler is wired to a live touch
    interface. The long press that leaves OPTIONS raises
    AttributeError, the surrounding handler catches and logs it, and the
    gesture silently does nothing.
  integration: >
    Two files: src/gtach/display/touch.py and
    src/gtach/display/navigation_gestures.py. Executor is Claude Code;
    AEL is not used.

    CONFIRMED ON TARGET. logs/start.log from the 2026-08-05 gtach.local
    session carries five lines and no other errors in 3.5 MB:

      06:39:54,899  TouchHandler ERROR Short press handling error: DIGITAL
      06:39:55,878  TouchHandler ERROR Short press handling error: DIGITAL
      06:39:57,403  TouchHandler ERROR Short press handling error: DIGITAL
      06:40:08,372  TouchHandler ERROR Long press handling error: DIGITAL
      06:40:09,798  TouchHandler ERROR Long press handling error: DIGITAL

    The message body is the bare word DIGITAL because accessing a
    missing Enum member raises AttributeError('DIGITAL') and both
    handlers log f'...: {e}' without the type.

    ONE LINE IS THE FIX. touch.py:171. Everything else in this prompt is
    consequence — dead code that switches between two modes of which one
    no longer exists.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/touch.py and src/gtach/display/navigation_gestures.py."
    - "Do NOT modify display/manager_backup.py or display/setup_original_backup.py. Both carry DIGITAL references; neither is imported anywhere; both are excluded by the standing backup-file convention."
    - "Do NOT modify src/gtach/display/manager.py. change-378703da left it correct."
    - "Do NOT modify src/gtach/display/input/. The coordinator is not implicated."
    - "Do NOT restore DisplayMode.DIGITAL. Its retirement is a decision taken in ai/task.md §7.3.14 and implemented; this change completes it."
    - "Do NOT change the OPTIONS access gesture. Replacing long press with swipe-down/up is change-3e8b1d72 and depends on this change."
    - "Do NOT narrow the except-Exception handlers that swallowed the fault. Considered and deferred — see change-7f2a9c04 alternatives_considered."
    - "Do NOT touch the early returns in _handle_short_press for setup mode and OPTIONS. They precede the block you are removing."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Repoint the three DisplayMode.DIGITAL references that describe
    surviving behaviour to RADIAL, and remove the seven that switch
    between two modes.
  requirements:
    functional:
      - "TouchHandler._handle_long_press sets RADIAL when leaving OPTIONS."
      - "A long press while in OPTIONS returns to RADIAL and raises nothing."
      - "A long press while not in OPTIONS still enters OPTIONS."
      - "The horizontal-swipe branch is absent from _handle_short_press."
      - "_process_settings_touch has no setting_id == 'mode' branch."
      - "_process_settings_touch's 'save' branch sets RADIAL."
      - "NavigationGestureHandler._exit_settings sets RADIAL."
      - "_cycle_display_mode is removed, or is a no-op with a comment if it has a caller."
      - "grep -rn 'DisplayMode.DIGITAL' src/gtach matches only the two backup files."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Neutral. Code removed from gesture paths that run at human rates"
      metric: "time"

design:
  architecture: >
    RADIAL is the only normal display mode. A reference that means
    'return to the normal screen' points at RADIAL; a reference that
    means 'switch to the other mode' has nothing to point at and is
    removed rather than repointed, because a control that switches
    RADIAL to RADIAL reads as intentional and does nothing.
  components:
    - name: "TouchHandler._handle_long_press"
      type: "function"
      purpose: "Enter and leave OPTIONS."
      logic:
        - "The else-branch — reached when already in OPTIONS — calls change_mode(DisplayMode.RADIAL)."
        - "Everything above it, including the disconnected early return, is unchanged."
    - name: "TouchHandler._handle_short_press"
      type: "function"
      purpose: "Route setup and options touches; no longer switches mode."
      logic:
        - "Keep the setup early return and the OPTIONS early return exactly as they are."
        - "Remove the swipe-detection block below them, including the swipe_threshold local and the dx computation that serve only it."
    - name: "TouchHandler._process_settings_touch"
      type: "function"
      purpose: "Adjust RPM thresholds and save."
      logic:
        - "Remove the setting_id == 'mode' branch entirely."
        - "The branch that followed it becomes the first; make it an if rather than an elif."
        - "The 'save' branch's ternary collapses to change_mode(DisplayMode.RADIAL)."
    - name: "NavigationGestureHandler._exit_settings"
      type: "function"
      purpose: "Leave the settings screen."
      logic:
        - "change_mode(DisplayMode.RADIAL)."
    - name: "NavigationGestureHandler._cycle_display_mode"
      type: "function"
      purpose: "Nothing, now that there is one mode."
      logic:
        - "grep for callers first."
        - "No caller: delete the method."
        - "A caller: keep the signature, make the body log at DEBUG and return, and comment that mode cycling ended with DIGITAL's retirement. Record which was done in the commit message."
  dependencies:
    internal:
      - "DisplayManager.change_mode — assigns the mode and saves. Unmodified."
      - "DisplayManager._initialize_legacy_components — constructs both classes. Unmodified."
    external: []

error_handling:
  strategy: >
    Unchanged. The handlers that swallowed this fault are deliberately
    left alone: an unhandled exception on the touch thread of a vehicle
    display is worse than an inert gesture. The fault is removed at
    source instead.
  exceptions:
    - exception: "AttributeError"
      condition: "Should no longer be reachable from these paths."
      handling: "Not specifically caught. If it recurs the fix is incomplete."
  logging:
    level: "Unchanged"
    format: "Existing"

testing:
  unit_tests:
    - scenario: "THE ACCEPTANCE TEST. _handle_long_press with a stubbed DisplayManager whose config.mode is OPTIONS."
      expected: "change_mode called once with DisplayMode.RADIAL; no exception logged."
    - scenario: "The same test run against the PRE-CHANGE file."
      expected: "change_mode NOT called; an ERROR containing 'DIGITAL' logged. Run it both ways and record both — a test that passes against both proves nothing."
    - scenario: "_handle_long_press with config.mode RADIAL."
      expected: "change_mode called with OPTIONS. Unchanged."
    - scenario: "_handle_long_press with the disconnected condition true."
      expected: "Returns early; change_mode not called. Unchanged."
    - scenario: "_handle_short_press with dx of 150 px, mode RADIAL, not in setup."
      expected: "No change_mode call; no exception."
    - scenario: "_handle_short_press with is_in_setup_mode true."
      expected: "_handle_setup_touch called. Unchanged."
    - scenario: "_handle_short_press with mode OPTIONS."
      expected: "_handle_options_touch called. Unchanged."
    - scenario: "_process_settings_touch('mode')."
      expected: "No branch matches; no exception; config.mode unchanged."
    - scenario: "_process_settings_touch for warn_decrease, warn_increase, danger_decrease and danger_increase."
      expected: "Unchanged behaviour including the bounds at 3000, 9000 and the warning/danger separation."
    - scenario: "_process_settings_touch('save')."
      expected: "_save_config called; change_mode called with RADIAL."
    - scenario: "_exit_settings."
      expected: "change_mode called with RADIAL."
    - scenario: "_cycle_display_mode if retained."
      expected: "No exception; change_mode not called."
    - scenario: "Repository-wide grep for DisplayMode.DIGITAL."
      expected: "Matches only display/manager_backup.py and display/setup_original_backup.py."
    - scenario: "import gtach.display.touch and gtach.display.navigation_gestures."
      expected: "Both succeed."
  edge_cases:
    - "_handle_short_press's swipe block computes dx from start_x. Removing the block leaves start_x and start_y as unused parameters; do NOT change the signature — TouchHandler's caller passes them positionally."
    - "The elif chain in _process_settings_touch: removing the first branch means the next must become an if. A stray elif with no preceding if is a syntax error and will be caught by py_compile, but check it deliberately."
    - "navigation_gestures.py may import DisplayMode solely for the two references. If both go, the import becomes unused — remove it only if nothing else in the file uses the name."
    - "The five log lines are the only errors in the session. After this change a session exercising both gestures should produce none; that is the on-target acceptance test."
  validation:
    - "grep confirms no DisplayMode.DIGITAL outside the two backup files."
    - "git diff confirms the setup and options early returns in _handle_short_press are unchanged."
    - "git diff confirms display/manager.py is untouched."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/display/touch.py"
      content: |
        FOUR EDITS.

        EDIT 1 — THE FIX. At touch.py:168-171:

                if self.display_manager.config.mode != DisplayMode.OPTIONS:
                    self.display_manager.change_mode(DisplayMode.OPTIONS)
                else:
                    self.display_manager.change_mode(DisplayMode.DIGITAL)

        becomes:

                if self.display_manager.config.mode != DisplayMode.OPTIONS:
                    self.display_manager.change_mode(DisplayMode.OPTIONS)
                else:
                    # RADIAL is the only normal display mode after
                    # DIGITAL's retirement (change-378703da). This line
                    # still named DIGITAL, so leaving OPTIONS raised
                    # AttributeError, was swallowed by the handler
                    # below, and the operator could not get off the
                    # options screen (issue-7f2a9c04).
                    self.display_manager.change_mode(DisplayMode.RADIAL)

        EDIT 2 — the swipe branch. In _handle_short_press, remove the
        block that begins with the swipe_threshold local and ends with
        the left-swipe else-branch — currently touch.py:191-203, the
        whole of:

                # Detect left/right swipe
                swipe_threshold = 100
                dx = x - start_x

                if abs(dx) >= swipe_threshold:
                    ...

        Replace it with a comment recording why nothing is there:

                # No horizontal swipe handling. It switched between
                # DIGITAL and RADIAL; DIGITAL was retired
                # (change-378703da) and RADIAL is the only normal mode,
                # so there is nothing to switch to (issue-7f2a9c04).

        Leave the setup early return and the OPTIONS early return above
        it exactly as they are. Do NOT change the method signature —
        start_x and start_y become unused but the caller passes them
        positionally.

        EDIT 3 — the settings 'mode' branch. In _process_settings_touch,
        remove:

                if setting_id == "mode":
                    # Toggle between DIGITAL and RADIAL modes
                    if config.mode == DisplayMode.DIGITAL:
                        config.mode = DisplayMode.RADIAL
                    else:
                        config.mode = DisplayMode.DIGITAL

        The next branch — setting_id == "warn_decrease" — becomes the
        first and must change from elif to if.

        EDIT 4 — the save branch. Currently:

                elif setting_id == "save":
                    self.display_manager._save_config()
                    self.display_manager.change_mode(
                        DisplayMode.DIGITAL if config.mode == DisplayMode.DIGITAL
                        else DisplayMode.RADIAL
                    )

        becomes:

                elif setting_id == "save":
                    self.display_manager._save_config()
                    # One normal mode remains (change-378703da), so the
                    # ternary that chose between them collapses.
                    self.display_manager.change_mode(DisplayMode.RADIAL)
    - path: "src/gtach/display/navigation_gestures.py"
      content: |
        TWO EDITS.

        EDIT 5 — _exit_settings, at navigation_gestures.py:474:

                self.display_manager.change_mode(DisplayMode.DIGITAL)

        becomes:

                # RADIAL is the only normal mode (change-378703da).
                self.display_manager.change_mode(DisplayMode.RADIAL)

        EDIT 6 — _cycle_display_mode, at navigation_gestures.py:424-435.

        First grep the repository for callers.

        No caller — delete the method entirely.

        A caller — keep the signature and replace the body with:

                # Mode cycling ended with DIGITAL's retirement
                # (change-378703da); RADIAL is the only normal display
                # mode, so there is nothing to cycle through. Retained
                # as a no-op because <caller> still calls it.
                self.logger.debug(
                    'Display mode cycling is a no-op: RADIAL is the '
                    'only normal mode'
                )
                return

        State in the commit message which branch was taken and, if the
        second, which caller forced it.

        If DisplayMode is imported in this file solely for these two
        references, and EDIT 5 keeps one of them, the import stays.
        Check rather than assume.

success_criteria:
  - "python -m py_compile src/gtach/display/touch.py src/gtach/display/navigation_gestures.py passes."
  - "python -c 'import gtach.display.touch, gtach.display.navigation_gestures' succeeds."
  - "pytest tests/ passes with no new failures."
  - "The long-press-out-of-OPTIONS test fails against the pre-change file and passes after. Both results recorded."
  - "grep -rn 'DisplayMode.DIGITAL' src/gtach --include=*.py matches only display/manager_backup.py and display/setup_original_backup.py."
  - "_handle_long_press sets RADIAL when in OPTIONS and OPTIONS otherwise."
  - "_handle_short_press contains no swipe-threshold logic and no mode change."
  - "The setup and OPTIONS early returns in _handle_short_press are byte-identical to their current text."
  - "_handle_short_press's signature is unchanged."
  - "_process_settings_touch has no 'mode' branch and its remaining branches behave as before."
  - "_process_settings_touch('save') calls change_mode with RADIAL."
  - "_exit_settings calls change_mode with RADIAL."
  - "_cycle_display_mode is absent or is a no-op; which, and why, stated in the commit message."
  - "src/gtach/display/manager.py is byte-identical to its current text."
  - "src/gtach/display/input/ is byte-identical."
  - "No file other than the two named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "touch"
        path: "src/gtach/display/touch.py"
      - name: "navigation_gestures"
        path: "src/gtach/display/navigation_gestures.py"
      - name: "models"
        path: "src/gtach/display/models.py"
    classes:
      - name: "TouchHandler"
        module: "gtach.display.touch"
      - name: "NavigationGestureHandler"
        module: "gtach.display.navigation_gestures"
      - name: "DisplayMode"
        module: "gtach.display.models"
    functions:
      - name: "_handle_long_press"
        module: "gtach.display.touch"
        signature: "_handle_long_press(self, x: int, y: int) -> None"
      - name: "_handle_short_press"
        module: "gtach.display.touch"
        signature: "_handle_short_press(self, x: int, y: int, start_x: int, start_y: int) -> None"
      - name: "_process_settings_touch"
        module: "gtach.display.touch"
        signature: "_process_settings_touch(self, setting_id: str) -> None"
      - name: "_exit_settings"
        module: "gtach.display.navigation_gestures"
        signature: "_exit_settings(self) -> None"
      - name: "_cycle_display_mode"
        module: "gtach.display.navigation_gestures"
        signature: "_cycle_display_mode(self, direction: int) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-7f2a9c04-digital-reference-removal.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1). Then, once you
  are finished, write a report of what you have done in the
  ai/workspace/report folder.

  Write the acceptance test before the fix and run it against the
  unchanged file. This defect has a confirmed on-target signature — five
  log lines — and a test that cannot reproduce it is not testing this
  defect.

  The single most important line is EDIT 1. If the rest of the prompt
  proves larger than expected, EDIT 1 alone restores the operator's
  ability to leave the options screen, and the dead-code removal can
  follow separately. Say so rather than half-finishing the removals.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-7f2a9c04. |

---

Copyright (c) 2026 William Watson. MIT License.
