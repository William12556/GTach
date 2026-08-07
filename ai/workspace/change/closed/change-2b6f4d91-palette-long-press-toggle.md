Created: 2026 August 05

# Change: Put the Palette Toggle on the Path That Runs

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-2b6f4d91"
  title: "The day/night palette toggle moves from an inert double-tap registration to the live long-press path in TouchHandler, wired by direct call exactly as change-3e8b1d72 wired the vertical swipes"
  date: "2026-08-05"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-2b6f4d91"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-2b6f4d91"
  description: >
    Resolves issue-2b6f4d91. Raised under P04 from finding §6.2 of
    ai/workspace/report/v0.4.0-triple-implementation-session.md and from
    the operator's proposal of 2026-08-05 to move the toggle to a long
    press. Task list reference ai/task.md §9.8.5 item 2.

scope:
  summary: >
    Three edits. The handler is renamed to the gesture it now serves,
    the inert registration is removed, and TouchHandler's live
    long-press path calls the handler directly.
  affected_components:
    - name: "DisplayManager._handle_double_tap"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._setup_touch_callbacks"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/display/input/. Not modified. The coordinator's gesture-callback mechanism is inert but repairing it changes how every gesture and every button is delivered on a vehicle instrument — see alternatives_considered."
    - "The inert SWIPE_DOWN and SWIPE_UP registrations at manager.py:183-188. Left in place with an explanatory comment. Removing them is a few lines, but if the analysis is wrong in any particular it breaks swipes the operator has confirmed working."
    - "GestureType. No DOUBLE_TAP member is added; the point of this change is that none is needed."
    - "_toggle_palette itself (manager.py). Its body, the persistence, the transient confirmation and the Palette dataclass are all change-5012004e's and are unmodified."
    - "The DISCONNECTED early return in TouchHandler._handle_long_press. Preserved."
    - "config.touch_long_press. The duration threshold is unchanged."

rational:
  problem_statement: >
    change-5012004e delivered a complete day/night palette that has
    never been displayed. Its toggle is registered through
    TouchEventCoordinator.register_gesture_callback, whose dispatch
    entry points are called by nothing, so no registration made through
    that mechanism has ever fired.
  proposed_solution: >
    Call the handler directly from TouchHandler._handle_long_press, the
    live path, in the same manner change-3e8b1d72 used for the swipes.
  alternatives_considered:
    - option: "Add DOUBLE_TAP to GestureType and implement disambiguation in the coordinator."
      reason_rejected: >
        The obvious reading of §6.2, and it solves the wrong problem.
        The registration would still not fire, because the dispatch that
        would invoke it is unreachable. Two problems where the long
        press has none."
    - option: "Repair the coordinator by calling handle_touch_move and handle_touch_up from TouchHandler."
      reason_rejected: >
        The correct long-term fix — it would make every registration
        work and remove the class of defect rather than one instance.
        Rejected here because it changes how every gesture and every
        button is delivered on the live input path of a vehicle
        instrument, and because buttons currently fire from
        handle_touch_down deliberately (touch_coordinator.py:472
        documents the choice). That is a considered change of its own,
        not a step in making one toggle work. Recorded so the option is
        not lost."
    - option: "Keep the double tap and wire it directly from TouchHandler."
      reason_rejected: >
        Would require implementing double-tap detection in TouchHandler,
        which has none. Long press is already detected there at
        touch.py:142."
    - option: "Put the toggle on a button in the options screen instead of a gesture."
      reason_rejected: >
        change-5012004e considered and rejected this: b02ed4ea's
        three-target budget was full. It is worth revisiting once the
        options paging proposed on 2026-08-05 lands and a second page
        exists — at which point a button would be more discoverable than
        any gesture. Recorded as the preferred long-term home."
  benefits:
    - "The night palette becomes usable, which is the whole of change-5012004e's deliverable."
    - "The §6.1 contrast question becomes answerable: the night palette can be judged on the panel rather than from its measured ratios."
    - "No change to display/input, which every prompt in this area has declared read-only."
    - "One gesture, one meaning: long press was doing nothing."
  risks:
    - risk: >
        Muscle memory. Long press was the route to OPTIONS until
        change-3e8b1d72, two changes ago. An operator expecting options
        will get a palette change.
      mitigation: >
        Gated to RADIAL, and change-5012004e already draws a transient
        'Night' or 'Day' confirmation, so an accidental toggle explains
        itself. A second long press reverses it. Recorded rather than
        engineered around."
    - risk: >
        A long press intended for a button on the options screen toggles
        the palette instead.
      mitigation: >
        The handler returns early unless the mode is RADIAL, so it
        cannot fire on the options screen at all. Asserted per mode."
    - risk: >
        The analysis of the delivery path is wrong and the direct call
        double-fires alongside a registration that does work.
      mitigation: >
        The inert registration for the palette is removed in the same
        edit, so only one invocation route exists whatever the truth of
        the wider analysis. This is the reason to remove that
        registration rather than leave it."
    - risk: >
        Renaming _handle_double_tap to _handle_long_press collides
        conceptually with the OPTIONS handler of the same name that
        change-3e8b1d72 removed from this class.
      mitigation: >
        The name is free — 3e8b1d72 deleted it. The docstring states
        explicitly that this is the palette toggle and not the retired
        OPTIONS toggle, because a reader of the git history will
        otherwise assume the latter has returned."
  benefits_measurement: >
    Palette toggles achieved: 0 in every session to date -> working.
    'Palette switched to' lines in the logs: 0 -> non-zero.

technical_details:
  current_behavior: >
    manager.py:196-205 registers _handle_double_tap conditionally on
    getattr(GestureType, 'DOUBLE_TAP', None), which is None, so the
    else-branch logs a DEBUG line and nothing is registered. Even were
    the member present, touch_coordinator.handle_touch_up — which
    dispatches to registered callbacks — is called by nothing.
    TouchHandler._handle_long_press logs 'Long press: no action' after
    its DISCONNECTED early return.
  proposed_behavior: >
    TouchHandler._handle_long_press calls
    display_manager._handle_long_press, which toggles the palette when
    the mode is RADIAL and does nothing otherwise.
  implementation_approach: >
    THREE EDITS.

    1. manager.py — rename _handle_double_tap to _handle_long_press. The
       body is unchanged: the setup-mode guard, the RADIAL guard, the
       _toggle_palette call, the return values and the exception
       handler all stay. The docstring gains a statement that this is
       the palette toggle and not the OPTIONS toggle change-3e8b1d72
       retired.

    2. manager.py — delete the conditional DOUBLE_TAP block from
       _setup_touch_callbacks, including its else-branch DEBUG line. In
       its place, a comment recording that gesture callbacks registered
       with the coordinator are not dispatched, and that the palette
       toggle is therefore wired from TouchHandler — the same route the
       swipes take.

       The SWIPE_DOWN and SWIPE_UP registrations above it are LEFT AS
       THEY ARE, with the same comment covering them. They are inert;
       removing them is out of scope.

    3. touch.py — TouchHandler._handle_long_press calls
       self.display_manager._handle_long_press((x, y), (x, y)) in place
       of its 'no action' DEBUG line, after the DISCONNECTED early
       return, following the delegation pattern change-3e8b1d72
       established at touch.py:202-209.

       The two positional arguments are the DisplayManager handler's
       signature, which takes start and end positions to match the other
       gesture handlers. A long press has one position; passing it twice
       is correct and should be commented as deliberate.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _handle_double_tap renamed to _handle_long_press; the inert
        conditional DOUBLE_TAP registration removed and replaced by a
        comment recording why the wiring lives in touch.py.
      functions_affected:
        - "_handle_double_tap"
        - "_handle_long_press"
        - "_setup_touch_callbacks"
      classes_affected:
        - "DisplayManager"
    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: >
        _handle_long_press delegates to the DisplayManager handler
        instead of logging no action.
      functions_affected:
        - "_handle_long_press"
      classes_affected:
        - "TouchHandler"
  data_changes: []
  interface_changes:
    - "DisplayManager._handle_double_tap is renamed. It is private and, being registered only through a mechanism that does not dispatch, has no live caller to break."

dependencies:
  internal:
    - component: "change-5012004e"
      impact: "Supplies _toggle_palette, the Palette dataclass, the persistence and the transient confirmation. All unmodified; this change only makes them reachable."
    - component: "change-3e8b1d72"
      impact: "Established the delegation pattern this change follows, and freed the long press by moving OPTIONS to the vertical swipes."
    - component: "change-7f2a9c04"
      impact: "Removed the DIGITAL reference from TouchHandler._handle_long_press, leaving it a no-op ready for this."
    - component: "TouchHandler._process_touch — touch.py:142"
      impact: "Detects the long press against config.touch_long_press and calls the handler. Read-only."
  external: []
  required_changes:
    - change_ref: "change-5012004e"
      relationship: "blocked_by"
    - change_ref: "change-3e8b1d72"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with a stubbed rendering engine. TouchHandler is driven
    against a stub DisplayManager to assert the delegation, and the
    DisplayManager handler is driven directly to assert the gating.
    The acceptance test is behavioural: a long press in RADIAL changes
    self._palette.
  test_cases:
    - scenario: "TouchHandler._handle_long_press with mode RADIAL, not disconnected."
      expected_result: "display_manager._handle_long_press called once. THE ACCEPTANCE TEST."
    - scenario: "The same against the pre-change file."
      expected_result: "Not called; a 'no action' DEBUG line logged. The test must discriminate."
    - scenario: "DisplayManager._handle_long_press with mode RADIAL."
      expected_result: "_palette moves from DAY_PALETTE to NIGHT_PALETTE; SETTINGS_CHANGE returned."
    - scenario: "Called twice."
      expected_result: "Back to DAY_PALETTE."
    - scenario: "Called with mode OPTIONS, ACKNOWLEDGEMENT, SPLASH, and with _in_setup_mode True."
      expected_result: "No palette change and NONE returned, in all four."
    - scenario: "TouchHandler._handle_long_press while the disconnected condition holds."
      expected_result: "The existing early return; the DisplayManager handler is not called."
    - scenario: "_handle_double_tap."
      expected_result: "Absent."
    - scenario: "grep DOUBLE_TAP in manager.py."
      expected_result: "No occurrence."
    - scenario: "The transient confirmation after a toggle."
      expected_result: "_palette_notice_until is set about two seconds ahead, as change-5012004e specified."
    - scenario: "Persistence round trip after a toggle."
      expected_result: "_save_config called; the palette key restored on load."
    - scenario: "TouchHandler._handle_short_press with a vertical swipe."
      expected_result: "Still calls _handle_swipe_down or _handle_swipe_up. The swipe delegation is untouched."
    - scenario: "A button tap on the options screen."
      expected_result: "Still dispatched through handle_touch_down as before."
  regression_scope:
    - "tests/display/ — once populated per ai/task.md §8.2."
    - "On gtach.local: long press on the gauge toggles the palette and logs 'Palette switched to night'."
    - "On gtach.local: swipe down and up still enter and leave OPTIONS."
    - "On gtach.local: the options buttons still respond."
    - "On gtach.local at night: the night palette is legible — the §6.1 observation that has never been possible."
  validation_criteria:
    - "python -m py_compile on both files passes."
    - "pytest tests/ passes with no new failures."
    - "No DOUBLE_TAP reference remains in src/gtach/display/manager.py."
    - "src/gtach/display/input/ is byte-identical."
    - "The SWIPE_DOWN and SWIPE_UP registrations are present and unchanged."
    - "_toggle_palette is byte-identical."

implementation:
  implementation_steps:
    - step: "Write the discriminating delegation test and confirm it fails against the current file."
      owner: "Claude Code"
    - step: "Rename the handler and update its docstring."
      owner: "Claude Code"
    - step: "Remove the conditional DOUBLE_TAP registration; add the comment recording why the wiring is in touch.py."
      owner: "Claude Code"
    - step: "Delegate from TouchHandler._handle_long_press."
      owner: "Claude Code"
    - step: "Compile checks and the assertion set."
      owner: "Claude Code"
    - step: "Deploy; long press on the gauge; confirm the palette changes and the log records it. Then judge the night palette at night, which settles §6.1's outstanding half."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the inert
    registration and the no-op long press. A config.yaml carrying
    palette: night would then be honoured on load but unchangeable —
    set it back to day before reverting, or accept a night display.
  deployment_notes: >
    Visible change: long press now does something. It did nothing in the
    build the operator is running, and it opened the OPTIONS screen in
    the build before that, so expect some confusion. The transient
    on-screen confirmation is what makes an accidental toggle
    self-explanatory.

verification:
  implemented_date: "2026-08-05"
  implemented_by: "Claude Code, per prompt-2b6f4d91"
  verification_date: "2026-08-07"
  verified_by: "William Watson (gtach.local); Claude Code (source re-check)"
  test_results: >
    Source re-check confirms _toggle_palette present, called from
    _handle_long_press gated to RADIAL, logging 'Palette switched to
    {name}'; no DOUBLE_TAP reference remains in manager.py. William
    confirmed 2026-08-07 that GTach functions correctly on gtach.local.
  issues_found:
    - "This triple was never recorded in ai/task.md despite being implemented — a governance-tracking gap, not a source defect, discovered while closing issue-5012004e and corrected by this closure."

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5012004e"
      relationship: "blocked_by"
    - change_ref: "change-3e8b1d72"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-2b6f4d91"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-2b6f4d91, adopting the operator's long-press proposal of 2026-08-05."
      - "Recorded repairing the coordinator's dispatch as the correct long-term fix and the reason for not taking it here: it changes how every gesture and button is delivered on a vehicle instrument's live input path."
      - "Recorded that the inert palette registration is removed rather than left, so that only one invocation route exists whatever the truth of the wider delivery-path analysis."
      - "Recorded the inert SWIPE registrations as deliberately left in place, removal risking swipes the operator has confirmed working."
      - "Recorded an options-screen button as the preferred long-term home once the proposed second options page exists."
      - "Recorded the muscle-memory risk: long press opened OPTIONS two changes ago."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial change document coupled to issue-2b6f4d91. Moves the palette toggle to the live long-press path by direct delegation, and removes the inert double-tap registration. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation confirmed by source re-check; recorded as untracked in ai/task.md. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
