Created: 2026 August 05

# Issue: The Night Palette Has Never Been Displayed, Because Its Gesture Is Registered on a Dispatch Path Nothing Calls

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-2b6f4d91"
  title: "The day/night palette toggle is registered through TouchEventCoordinator.register_gesture_callback, whose dispatch entry points handle_touch_up and handle_touch_move are called by nothing, so the toggle cannot fire and the night palette has never been shown"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-2b6f4d91"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: "logs/debug.log, on-target sessions 2026-08-05"
  description: >
    Recorded as finding §6.2 of
    ai/workspace/report/v0.4.0-triple-implementation-session.md — "the
    night palette toggle cannot fire" — and attributed there to
    GestureType lacking a DOUBLE_TAP member. That diagnosis is correct
    but incomplete; the fuller cause was established on 2026-08-05 while
    scoping the operator's proposal to move the toggle to a long press.
    Task list reference ai/task.md §9.8.5 item 2.

affected_scope:
  components:
    - name: "DisplayManager._setup_touch_callbacks"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._handle_double_tap"
      file_path: "src/gtach/display/manager.py"
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
    - name: "TouchEventCoordinator.handle_touch_up"
      file_path: "src/gtach/display/input/touch_coordinator.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: "Source checkout at 0.3.3, or the deployed build on gtach.local."
  steps:
    - "Long press, double tap or otherwise gesture on the RADIAL gauge. The palette never changes; no 'Palette switched to' line appears in debug.log across any session."
    - "Read manager.py:196-205. The palette toggle is registered conditionally on getattr(GestureType, 'DOUBLE_TAP', None), which resolves to None."
    - "Read interfaces.py:19-28. GestureType declares TAP, LONG_PRESS, SWIPE_LEFT, SWIPE_RIGHT, SWIPE_UP, SWIPE_DOWN, DRAG, PINCH. There is no DOUBLE_TAP."
    - "THE FULLER CAUSE — grep handle_touch_up and handle_touch_move across src/gtach. The only occurrences are their own definitions at touch_coordinator.py:252 and 279 and the abstract declarations at interfaces.py:72 and 77. NOTHING CALLS EITHER."
    - "Read touch_coordinator.py:296-304. handle_touch_up is where LONG_PRESS and TAP are dispatched to registered callbacks. It is never reached."
    - "Read touch_coordinator.py:265-271. handle_touch_move is where recognised swipes are dispatched. It is never reached."
    - "Conclude that every register_gesture_callback registration is inert, including the SWIPE_DOWN and SWIPE_UP registrations at manager.py:183-188."
    - "Confirm the swipes nevertheless work: touch.py:202-209 calls display_manager._handle_swipe_down and _handle_swipe_up DIRECTLY, bypassing the coordinator. That direct call is what change-3e8b1d72 delivered and what the operator observes working."
  frequency: "always"
  reproducibility_conditions: "Unconditional and structural."
  preconditions: "None."
  test_data: >
    THE LIVE TOUCH PATH, established by reading rather than assumed. It
    is a chain, not two parallel sources:

      touch_interface
        -> TouchHandler._handle_touch_event      (registered at touch.py:78)
        -> TouchHandler._process_touch
        -> on release, by duration:
             >= config.touch_long_press  ->  TouchHandler._handle_long_press
             otherwise                   ->  TouchHandler._handle_short_press
        -> _handle_short_press routes taps onward via
           DisplayManager.handle_touch_event -> coordinator.handle_touch_down

    So the coordinator receives touch-DOWN only. touch_coordinator.py:472
    documents this in a comment on _handle_button_touch_down: "Execute
    callback immediately — handle_touch_up is not called in this delivery
    path (TouchHandler routes taps via handle_touch_down only)." The
    comment records the constraint accurately; what it does not say is
    that the same constraint kills the entire gesture-callback
    mechanism.

    WHAT THIS MEANS FOR THE THREE GESTURES.

      Buttons        work — dispatched from handle_touch_down.
      Swipe up/down  work — but NOT through their registrations. They
                     work because change-3e8b1d72 wired
                     TouchHandler._handle_short_press to call the
                     DisplayManager handlers directly.
      Palette toggle dead — registered only, never called directly.

    So the registrations at manager.py:183-188 are decorative. They
    describe an intent the running system does not execute, and they are
    the reason this defect was not obvious: the file appears to wire
    three gestures, two of which demonstrably work.

    LONG PRESS IS FREE AND LIVE. TouchHandler._handle_long_press
    (touch.py:157) is called from _process_touch at touch.py:142 when
    the touch duration reaches config.touch_long_press. It currently
    logs 'Long press: no action' and does nothing, change-3e8b1d72
    having removed the OPTIONS toggle from it and change-7f2a9c04 having
    removed the DIGITAL reference before that. Its one surviving
    behaviour is the DISCONNECTED early return at touch.py:161-166.
  error_output: >
    None. No exception is raised and nothing is logged; the gesture
    simply has no effect. No 'Palette switched to' line exists in any
    log pulled to date.

behavior:
  expected: >
    A gesture registered for a feature invokes that feature. The night
    palette can be selected.
  actual: >
    The palette toggle is registered on a dispatch path that nothing
    invokes, so it has never fired. The night palette — a complete,
    tested, seventeen-colour implementation delivered by change-5012004e
    — has never been displayed on the panel.
  impact: >
    The night palette is unusable. That is the whole of `5012004e`'s
    deliverable, and the reason display report §7.9 was raised: at night
    the instrument is a bright light source in the driver's forward
    field of view with no operator control.

    Secondarily, the §6.1 contrast question cannot be settled. The day
    palette has been observed and reads well; the night palette's
    measured 1.55:1 blue-on-ground figure has never been judged against
    the panel because the panel has never shown it.
  workaround: >
    None. No code path sets NIGHT_PALETTE, and the persisted `palette`
    key is only written by the toggle that cannot fire.

environment:
  python_version: "3.9 on target"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    Two layers.

    The proximate cause is the one §6.2 recorded: change-5012004e
    specified a double-tap, GestureType has no such member, and that
    prompt declared display/input read-only so the member could not be
    added. The registration was made conditional and resolves to None.

    The underlying cause is that TouchEventCoordinator's gesture-callback
    mechanism has no live caller. It was presumably written for a
    delivery path in which the coordinator sees the full touch lifecycle;
    the actual path gives it touch-down only. Every registration made
    through it is inert, and has been for as long as this arrangement has
    existed.

    change-3e8b1d72 worked around this without naming it: its prompt
    instructed the legacy TouchHandler path to delegate to the
    DisplayManager handlers "so the two paths agree by construction". In
    fact there is one path, and that delegation is the only reason the
    swipes function.
  technical_notes: >
    THE OPERATOR'S PROPOSAL, AND WHY IT IS THE RIGHT SHAPE. On
    2026-08-05 the operator proposed moving the palette toggle from
    double tap to long press. That is adopted here. It is a better fit
    than adding a DOUBLE_TAP member for three reasons:

      1. LONG_PRESS already exists in GestureType and is already
         detected by the live path, at touch.py:142.
      2. Long press is unclaimed. change-3e8b1d72 moved OPTIONS to the
         vertical swipes and left TouchHandler._handle_long_press doing
         nothing but logging.
      3. It requires no change to display/input, which every prompt
         touching this area has so far declared read-only.

    Adding DOUBLE_TAP would require implementing double-tap
    disambiguation in a subsystem whose gesture dispatch does not run —
    two problems where this proposal has none.

    WHAT THIS TRIPLE DOES NOT DO. It does not repair the coordinator's
    gesture-callback mechanism, and it does not remove the inert
    SWIPE_DOWN/SWIPE_UP registrations at manager.py:183-188. Both are
    recorded here and left for a decision:

      - Repairing the mechanism means calling handle_touch_move and
        handle_touch_up from TouchHandler, which changes how every
        gesture and every button is delivered. That is a substantial
        change to the live input path of a vehicle instrument and does
        not belong in a triple whose purpose is to make one toggle work.
      - Removing the inert registrations is a few lines, but if the
        analysis above is wrong in any particular, removing them breaks
        the swipes the operator has just confirmed working. They are
        left in place with an explanatory comment instead.

    ONE CAUTION ON THE CHOICE OF GESTURE. Long press was the route to
    the OPTIONS screen until change-3e8b1d72, two changes ago. An
    operator with muscle memory will long-press expecting options and
    receive a palette change. Mitigated by gating the toggle to RADIAL
    and by the transient on-screen confirmation change-5012004e already
    draws, but the confusion is real and worth expecting.
  related_issues:
    - issue_ref: "issue-5012004e"
      relationship: "blocked_by"
    - issue_ref: "issue-3e8b1d72"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Wire the palette toggle into TouchHandler._handle_long_press, the
    live path, exactly as change-3e8b1d72 wired the swipes into
    _handle_short_press. Remove the inert DOUBLE_TAP registration. See
    change-2b6f4d91.
  change_ref: "change-2b6f4d91"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A registration mechanism with no live caller is worse than an absent
    one: it accepts callbacks, logs that it has registered them, and
    reports success. `register_gesture_callback` logs "Registered
    callback for SWIPE_DOWN" and that line appears in every log pulled —
    while the callback has never been invoked.

    Where a feature is wired by registration, the acceptance test should
    exercise the gesture rather than assert the registration. Every test
    written for change-5012004e's toggle called the handler directly and
    passed.
  process_improvements: >
    This defect survived three triples that touched the same files —
    5012004e, 3e8b1d72 and 7f2a9c04 — because each reasoned about the
    registration rather than the delivery. The delivery path is worth
    tracing once and recording, which test_data above now does.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on both modified files passes."
    - "A long press on the RADIAL gauge toggles the palette."
    - "A long press produces a 'Palette switched to night' line in debug.log — a line that appears in no log to date."
    - "A second long press returns to day."
    - "The transient 'Night' / 'Day' confirmation renders."
    - "The choice survives a restart, the persisted palette key being written by _toggle_palette."
    - "A long press does nothing in OPTIONS, ACKNOWLEDGEMENT, SPLASH or setup mode."
    - "A long press on the DISCONNECTED screen still takes the existing early return and does not toggle."
    - "Swipe down and swipe up still enter and leave OPTIONS — the direct calls at touch.py:202-209 are untouched."
    - "Buttons on the options screen still respond."
    - "No DOUBLE_TAP reference remains in manager.py."
    - "display/input/ is unmodified."
    - "On gtach.local, at night: the night palette is legible and the §6.1 contrast question can finally be judged."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-2b6f4d91"
  test_refs: []

notes: >
  Raised under P04 from finding §6.2 of the v0.4.0 implementation report
  and from the operator's proposal of 2026-08-05. Not a numbered item of
  either code review; no §7.0 task number.

  issue_info.type is defect: a delivered feature cannot be invoked.
  Severity medium — nothing malfunctions, but change-5012004e's entire
  deliverable is unreachable and §6.1 cannot be settled without it.

  This triple also unblocks the night half of §9.8.5 item 3, the
  contrast question. The day palette has been observed and reads well,
  which supports treating the 3:1 criterion as the wrong test for a
  deliberately dark face; the night palette has never been seen.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial issue document from report finding §6.2 and the operator's long-press proposal of 2026-08-05."
      - "Recorded the fuller cause, which §6.2 did not reach: TouchEventCoordinator.handle_touch_up and handle_touch_move are called by nothing, so every register_gesture_callback registration is inert — including the SWIPE_DOWN and SWIPE_UP registrations, which are decorative. The swipes work only because change-3e8b1d72 wired TouchHandler to call the DisplayManager handlers directly."
      - "Traced and recorded the live touch delivery path as a chain rather than two parallel sources, and noted that touch_coordinator.py:472 already documents the constraint without drawing its consequence."
      - "Recorded why long press is the right gesture: it exists, it is detected on the live path, it is unclaimed since change-3e8b1d72, and it needs no change to display/input."
      - "Recorded two things deliberately not done — repairing the coordinator mechanism and removing the inert registrations — with the reason for each."
      - "Recorded the muscle-memory caution: long press was the OPTIONS gesture until two changes ago."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial issue document. Records that the coordinator's gesture-callback dispatch has no live caller, which is why the palette toggle has never fired and why the swipe registrations are decorative. |

---

Copyright (c) 2026 William Watson. MIT License.
