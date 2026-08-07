Created: 2026 August 05

# Issue: One Gesture Both Enters and Leaves the Options Screen, and It Is the Gesture Most Easily Made by Accident

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-3e8b1d72"
  title: "OPTIONS is entered and left by the same long press, so the gesture's effect depends on invisible state and a single failure of it strands the operator; the vertical swipes the touch subsystem already detects are unused"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-3e8b1d72"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: "logs/start.log, on-target session 2026-08-05 06:37-06:40"
  description: >
    Proposed by the operator on 2026-08-05 after the on-target session
    in which the long-press exit from OPTIONS failed
    (issue-7f2a9c04): "I could not long press back from the Options
    screen which makes me think we should change how options are
    accessed from long press to swipe down to enter options and swipe up
    to leave options and return to the previous screen." Recorded as a
    scope extension agreed by consensus rather than as a code-review
    finding; it is not sourced from either review report.

affected_scope:
  components:
    - name: "DisplayManager._handle_long_press"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._setup_touch_callbacks"
      file_path: "src/gtach/display/manager.py"
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: >
    Source checkout at 0.3.3 with change-7f2a9c04 applied, so the
    long-press exit works and the proposal can be evaluated against a
    functioning control rather than a broken one.
  steps:
    - "Read manager.py:_handle_long_press. One handler, branching on whether config.mode is already OPTIONS."
    - "Read touch.py:_handle_long_press. A second, parallel handler doing the same thing from the legacy path."
    - "Read touch_coordinator.py:520-525. _recognize_gesture returns SWIPE_UP or SWIPE_DOWN for a vertical movement beyond the swipe threshold."
    - "Read touch_coordinator.py:265-271. During a touch move, a recognised gesture is dispatched through handle_gesture to any registered callback."
    - "Read manager.py:_setup_touch_callbacks. Only LONG_PRESS is registered, plus a conditional DOUBLE_TAP that never resolves."
    - "Confirm no callback is registered for SWIPE_UP or SWIPE_DOWN anywhere in src/gtach."
  frequency: "always"
  reproducibility_conditions: "Structural; unconditional."
  preconditions: "None."
  test_data: >
    WHAT THE SUBSYSTEM ALREADY PROVIDES. The vertical swipes are
    detected and dispatched today; only the callbacks are missing:

      touch_coordinator.py:520-525  _recognize_gesture returns
        SWIPE_DOWN when dy > 0 and SWIPE_UP when dy < 0, for any
        movement whose distance exceeds swipe_threshold and whose
        vertical component exceeds its horizontal one.
      touch_coordinator.py:265-271  handle_touch_move calls
        _recognize_gesture and, on a hit, dispatches through
        handle_gesture with the start and current positions.
      touch_coordinator.py:340-345  handle_gesture looks the gesture up
        in _gesture_callbacks and invokes the registered callable.
      interfaces.py:19-28  GestureType declares SWIPE_UP and SWIPE_DOWN.

    So this change needs no work in display/input at all — which
    distinguishes it sharply from the double-tap palette toggle
    (issue-5012004e), where GestureType has no DOUBLE_TAP member and the
    subsystem performs no disambiguation. That feature is unreachable;
    this one is a registration away.

    TWO PARALLEL LONG-PRESS HANDLERS EXIST. manager.py's
    _handle_long_press is registered with the touch coordinator.
    touch.py's _handle_long_press is reached from the legacy
    TouchHandler, which registers _handle_touch_event directly on the
    touch interface (touch.py:78). Both are live, both branch on
    config.mode, and the on-target log shows the touch.py one firing —
    the five DIGITAL errors of issue-7f2a9c04 are logged by TouchHandler,
    not by DisplayManager.

    That duplication is the reason this change is not a one-line
    registration: whichever gesture opens OPTIONS, both handlers must
    agree, or the screen becomes enterable by one route and unleavable
    by the other. That is precisely the failure the operator has just
    experienced.
  error_output: "None. Nothing fails; the proposal concerns which gesture does what."

behavior:
  expected: >
    Entering and leaving a screen are distinct gestures, so the effect
    of a gesture does not depend on state the operator cannot see, and a
    failure of one direction does not strand them.
  actual: >
    A single long press toggles OPTIONS. Its effect depends on whether
    OPTIONS is already displayed — which is visible, but the gesture
    itself carries no direction. The vertical swipes the subsystem
    already detects are registered to nothing.
  impact: >
    Low in normal operation: the toggle works once change-7f2a9c04
    lands, and the operator can see which screen they are on.

    The impact that prompted the proposal is what happens when one
    direction breaks. A toggle has no second route: when the leaving
    branch failed, the only recovery was a restart. Two distinct
    gestures fail independently, and a failure of one leaves the other
    working.
  workaround: >
    Not applicable — nothing is broken. This is a change of design, not
    a repair.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    Not a defect. The long-press toggle is the design as built. The
    proposal follows from an incident: the operator met the one failure
    mode a toggle has no answer to, and concluded that entering and
    leaving should be separable. That reasoning holds independently of
    the defect that prompted it.
  technical_notes: >
    THIS IS A SCOPE EXTENSION, AGREED BY CONSENSUS. It is not a
    recommendation of either code review and carries no §7.0 task
    number. It was proposed by the operator on 2026-08-05 and accepted
    as a separate triple rather than folded into change-7f2a9c04, on the
    ground that a defect fix and a navigation redesign landing together
    would make a subsequent navigation problem unattributable — the same
    argument that staged change-6481f8ce.

    DEPENDS ON 7f2a9c04. That change repoints touch.py:171 to RADIAL and
    removes the horizontal-swipe branch from _handle_short_press. This
    change is written against the corrected file. Implementing it first
    would mean editing a handler that still raises AttributeError, and
    the swipe-up exit would appear to fail for a reason unrelated to
    itself.

    THE DUPLICATION IS THE REAL WORK. See test_data. Two live long-press
    handlers exist, in manager.py and touch.py, and the on-target log
    shows the touch.py one firing. Any change to how OPTIONS is reached
    must address both, or produce exactly the asymmetry — enterable by
    one route, unleavable by the other — that this proposal exists to
    prevent. change-3e8b1d72 records how.

    INTERACTION WITH THE HORIZONTAL SWIPES. change-7f2a9c04 removes the
    horizontal-swipe branch from touch.py because it switched between
    DIGITAL and RADIAL. The coordinator still recognises SWIPE_LEFT and
    SWIPE_RIGHT and its handle_gesture default returns
    TouchAction.MODE_CHANGE for them (touch_coordinator.py:357-358).
    Nothing consumes that today. It is out of scope here but worth
    knowing: a horizontal swipe currently returns a MODE_CHANGE action
    that no longer corresponds to any mode change.

    INTERACTION WITH 5012004e's DOUBLE TAP. That triple's palette toggle
    is unreachable because GestureType has no DOUBLE_TAP member. This
    change does not add one and does not fix it. Recorded so the two are
    not conflated: the gestures this change uses already exist.

    SWIPE DIRECTION AND THE PANEL. The proposal is swipe DOWN to enter
    and swipe UP to leave. On a 480x480 round panel with no bezel, a
    downward swipe starting near the top edge is easy; an upward swipe
    starting near the bottom edge is equally so. The convention matches
    a drawer pulled down from the top, which is the common phone
    idiom. Recorded because the opposite convention — up to open — is
    also common, and the choice should be deliberate rather than
    inherited.
  related_issues:
    - issue_ref: "issue-7f2a9c04"
      relationship: "blocked_by"
    - issue_ref: "issue-5012004e"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Register SWIPE_DOWN to enter OPTIONS and SWIPE_UP to leave it, in
    both live handler paths, and retire the long-press toggle. See
    change-3e8b1d72.
  change_ref: "change-3e8b1d72"
  resolved_date: "2026-08-05"
  resolved_by: "Claude Code, per prompt-3e8b1d72"
  fix_description: >
    SWIPE_DOWN registered to enter OPTIONS, SWIPE_UP to leave it, in
    both live handler paths (manager.py and touch.py); the long-press
    OPTIONS toggle retired from both. touch.py now carries
    _handle_swipe_down/_handle_swipe_up dispatch (confirmed in source).

verification:
  verified_date: "2026-08-05"
  verified_by: "William Watson (gtach.local, task.md §9.10)"
  test_results: >
    On-target session 2026-08-05: one ERROR in 362 KB and no DIGITAL
    line, confirming this change and 7f2a9c04 both clean together.
    Source re-check 2026-08-07 confirms touch.py registers
    display_manager._handle_swipe_down/_handle_swipe_up and the long
    press no longer branches on OPTIONS — it was freed for
    change-2b6f4d91's palette toggle, consistent with landing after
    this change.
  closure_notes: >
    William confirmed on 2026-08-07 that GTach is functioning correctly
    on gtach.local. No residual finding.

prevention:
  preventive_measures: >
    A control that toggles has one failure mode a pair of controls does
    not: a failure of either direction is unrecoverable, because the
    same gesture is the only route back. Where the two directions are
    cheap to separate, separating them costs one registration and
    removes that class of incident.
  process_improvements: >
    The two parallel long-press handlers were not discovered until an
    on-target log showed which one was firing. Where two modules
    register for the same input, a static reading does not reveal which
    is live; the log does.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "A downward swipe on the gauge enters OPTIONS."
    - "An upward swipe on the OPTIONS screen returns to the previous screen."
    - "A downward swipe while already in OPTIONS does nothing."
    - "An upward swipe while not in OPTIONS does nothing."
    - "A long press no longer enters or leaves OPTIONS, from either handler path."
    - "Both live handler paths agree: OPTIONS cannot be entered by one route and left only by another."
    - "The screen returned to on exit is the one that was displayed on entry."
    - "Vertical swipes do nothing in SPLASH, ACKNOWLEDGEMENT and setup mode."
    - "Vertical swipes on the DISCONNECTED screen do not enter OPTIONS."
    - "The three options controls and the confirmation sub-view are unaffected."
    - "display/input/ is unmodified."
    - "On gtach.local: swipe down to enter, swipe up to leave, repeated ten times without a restart."
    - "On gtach.local: no new ERROR lines in start.log across that session."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-3e8b1d72"
  test_refs: []

notes: >
  A scope extension agreed by consensus on 2026-08-05, not a
  code-review finding. It carries no §7.0 task number and belongs to
  neither v0.3.0 nor the v0.4.0 remediation set; it is queued behind
  change-7f2a9c04, which it depends on.

  issue_info.type is enhancement and severity low: nothing malfunctions
  once 7f2a9c04 lands. The justification is that a toggle has no second
  route when one direction fails, which the operator has just
  experienced.

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
      - "Initial issue document from the operator's proposal of 2026-08-05, recorded as a scope extension agreed by consensus rather than as a review finding."
      - "Recorded that the touch subsystem already detects and dispatches SWIPE_UP and SWIPE_DOWN, so no work in display/input is required — unlike the double-tap palette toggle of issue-5012004e, which is unreachable."
      - "Recorded the two parallel live long-press handlers, in manager.py and touch.py, as the substantive work: the on-target log shows the touch.py one firing, and a change addressing only one would produce the enterable-but-unleavable asymmetry the proposal exists to prevent."
      - "Recorded that a horizontal swipe still yields TouchAction.MODE_CHANGE from the coordinator's default with nothing consuming it."
      - "Recorded the swipe-direction convention as a deliberate choice rather than an inherited one."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status open -> closed. change-3e8b1d72 implemented and confirmed clean on-target 2026-08-05 (task.md §9.10). Source re-check confirms both swipe handlers registered and the long press freed for 2b6f4d91's palette toggle."
      - "Closed on William's confirmation that GTach functions correctly on gtach.local. Moved to ai/workspace/issues/closed/."

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
| 1.0 | 2026-08-05 | Initial issue document from the operator's 2026-08-05 proposal. Records that the vertical swipes already exist in the subsystem, and that two parallel live long-press handlers are the substantive work. |
| 1.1 | 2026-08-07 | Status open → closed. Resolution and verification recorded; confirmed clean on-target and by source re-check. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
