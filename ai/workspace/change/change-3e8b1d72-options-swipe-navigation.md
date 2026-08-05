Created: 2026 August 05

# Change: Swipe Down for Options, Swipe Up to Come Back

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-3e8b1d72"
  title: "SWIPE_DOWN enters the OPTIONS screen and SWIPE_UP returns to the screen it was entered from, in both live handler paths; the long-press toggle is retired and the entry screen is remembered rather than assumed"
  date: "2026-08-05"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-3e8b1d72"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-3e8b1d72"
  description: >
    Resolves issue-3e8b1d72. A scope extension proposed by the operator
    on 2026-08-05 and agreed by consensus; not sourced from either code
    review. Depends on change-7f2a9c04.

scope:
  summary: >
    Two gestures replace one. The subsystem already detects both; the
    work is registering them in the two live handler paths so the screen
    cannot become enterable by one route and unleavable by the other,
    and remembering which screen to return to.
  affected_components:
    - name: "DisplayManager._handle_swipe_down"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._handle_swipe_up"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._handle_long_press"
      file_path: "src/gtach/display/manager.py"
      change_type: "remove"
    - name: "DisplayManager._setup_touch_callbacks"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._pre_options_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
    - name: "TouchHandler._handle_short_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/display/input/. GestureType already declares SWIPE_UP and SWIPE_DOWN, _recognize_gesture already returns them, and handle_gesture already dispatches them to registered callbacks. Nothing there needs changing."
    - "The double-tap palette toggle of change-5012004e. It is unreachable for a different reason — GestureType has no DOUBLE_TAP — and this change does not add one."
    - "The horizontal swipes. change-7f2a9c04 removes their handler; the coordinator's default still returns TouchAction.MODE_CHANGE for them with nothing consuming it. Left alone; recorded in issue-3e8b1d72."
    - "The options screen's own controls, the confirmation sub-view and the update sub-view. Unaffected."
    - "The 'Long press to return' footer text drawn by _draw_options_menu. It must change, and is the one visible string this change edits."
    - "Setup mode's own gesture handling. _handle_swipe_up and _handle_swipe_down return early while the setup subsystem owns the display."

rational:
  problem_statement: >
    A single long press both enters and leaves OPTIONS. When its leaving
    branch failed on target the operator had no second route and had to
    restart. Two distinct gestures fail independently. The touch
    subsystem already detects the vertical swipes and dispatches them to
    registered callbacks; nothing is registered.
  proposed_solution: >
    Register SWIPE_DOWN to enter and SWIPE_UP to leave, in both live
    handler paths, remember the screen OPTIONS was entered from, and
    retire the long-press toggle.
  alternatives_considered:
    - option: "Register the swipes and keep the long press as well."
      reason_rejected: >
        Retains a third route and is the safest option against the
        possibility that vertical swipes prove awkward on a round
        bezel-less panel. Rejected because it keeps the toggle whose
        single-route failure is the reason for the change, and because
        two mechanisms for one action drift. Recorded as the fallback if
        the on-target trial goes badly: re-registering LONG_PRESS is one
        line."
    - option: "Swipe up to enter, swipe down to leave."
      reason_rejected: >
        Equally defensible — the opposite convention is common. The
        operator specified down-to-enter, which matches the drawer idiom
        of pulling a panel down from the top. Recorded as a deliberate
        choice rather than an inherited one, and reversible in two
        lines."
    - option: "Change only DisplayManager's handler and leave TouchHandler's long press."
      reason_rejected: >
        The smaller edit and precisely the failure mode this change
        exists to prevent: OPTIONS enterable by a swipe and leavable
        only by a long press that the operator no longer expects to
        use. The on-target log shows TouchHandler's handler is the one
        that fires, so leaving it alone would in fact mean the swipe did
        nothing at all."
    - option: "Return to RADIAL on exit rather than to the screen OPTIONS was entered from."
      reason_rejected: >
        Simpler, and correct in almost every case, RADIAL being the only
        normal mode. Rejected because OPTIONS is reachable from the
        DISCONNECTED condition too, and returning to RADIAL from there
        would show a gauge with no data. Remembering the entry state is
        four lines and is correct in both."
  benefits:
    - "Entering and leaving are separate gestures, so a failure of one does not strand the operator."
    - "The gesture carries its direction: down opens, up closes, independent of invisible state."
    - "Uses detection the subsystem already performs; no work in display/input."
    - "Removes the duplicated long-press branching from two modules."
  risks:
    - risk: >
        A vertical swipe on the gauge is made by accident while the
        vehicle moves, opening OPTIONS unexpectedly.
      mitigation: >
        The coordinator requires movement beyond swipe_threshold with a
        vertical component exceeding the horizontal, which a jolt rarely
        satisfies. If it proves troublesome the threshold is a
        coordinator setting; raising it is out of this change's scope
        but is the first adjustment to try."
    - risk: >
        Vertical swipes prove awkward on a round panel without a bezel.
      mitigation: >
        Trial on gtach.local is an implementation step, not an
        afterthought. The fallback — re-register LONG_PRESS alongside —
        is one line and is recorded under alternatives_considered."
    - risk: >
        The two handler paths disagree, producing exactly the
        enterable-but-unleavable asymmetry this change exists to
        prevent.
      mitigation: >
        Both are edited in the same change and the verification asserts
        the pairing from both entry points rather than from one. This is
        the change's principal correctness risk and its principal test."
    - risk: >
        A swipe fires during the splash or acknowledgement screens and
        opens OPTIONS over them.
      mitigation: >
        Both handlers return early unless the mode is RADIAL or the
        disconnected condition holds. Asserted for SPLASH,
        ACKNOWLEDGEMENT and setup mode individually."
  benefits_measurement: >
    Gestures that can strand the operator on OPTIONS: 1 -> 0. Routes
    into OPTIONS: 1 -> 1, and out: 1 -> 1, but independent. Modules
    holding long-press mode branching: 2 -> 0.

technical_details:
  current_behavior: >
    DisplayManager._handle_long_press branches on whether config.mode is
    OPTIONS, entering or leaving accordingly, and is registered for
    GestureType.LONG_PRESS in _setup_touch_callbacks.
    TouchHandler._handle_long_press does the same from the legacy path
    and is the one the on-target log shows firing. No callback is
    registered for SWIPE_UP or SWIPE_DOWN. _draw_options_menu draws
    'Long press to return'.
  proposed_behavior: >
    A downward swipe from RADIAL or the DISCONNECTED screen records the
    current state and enters OPTIONS. An upward swipe from OPTIONS
    returns to the recorded state. Neither long-press handler changes
    the mode. The footer reads 'Swipe up to return'.
  implementation_approach: >
    FIVE STEPS.

    STEP 1 — remember the entry state. Add
    self._pre_options_mode = None in __init__. It holds the DisplayMode
    that was current when OPTIONS was entered, so the exit returns
    there rather than assuming RADIAL. The DISCONNECTED screen is a
    derived condition rather than a mode, so recording config.mode is
    sufficient — the disconnected render takes precedence on return by
    itself.

    STEP 2 — the two handlers on DisplayManager.

      _handle_swipe_down: return NONE if in setup mode or if the mode is
      already OPTIONS, SPLASH or ACKNOWLEDGEMENT. Otherwise record
      _pre_options_mode, set _options_view to 'menu', set the mode to
      OPTIONS, return NAVIGATION.

      _handle_swipe_up: return NONE unless the mode is OPTIONS and not
      in setup mode. Otherwise set _options_view to 'menu', restore the
      recorded mode — defaulting to RADIAL if none was recorded — and
      return NAVIGATION.

    STEP 3 — registration. In _setup_touch_callbacks, register both, and
    remove the LONG_PRESS registration. Leave the conditional DOUBLE_TAP
    registration exactly as change-5012004e left it.

    STEP 4 — remove DisplayManager._handle_long_press. It has no other
    caller once its registration goes.

    STEP 5 — the legacy path. TouchHandler._handle_long_press stops
    changing the mode; its disconnected early return stays.
    TouchHandler._handle_short_press gains the same vertical-swipe
    handling, delegating to the DisplayManager methods rather than
    duplicating the logic — which is what keeps the two paths in
    agreement by construction rather than by discipline.

    Finally, _draw_options_menu's footer text changes from 'Long press
    to return' to 'Swipe up to return'.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _pre_options_mode added; _handle_swipe_down and _handle_swipe_up
        added and registered; _handle_long_press and its registration
        removed; options footer text updated.
      functions_affected:
        - "__init__"
        - "_setup_touch_callbacks"
        - "_handle_swipe_down"
        - "_handle_swipe_up"
        - "_handle_long_press"
        - "_draw_options_menu"
      classes_affected:
        - "DisplayManager"
    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: >
        The long-press handler no longer changes mode; the short-press
        handler detects vertical swipes and delegates to the
        DisplayManager handlers.
      functions_affected:
        - "_handle_long_press"
        - "_handle_short_press"
      classes_affected:
        - "TouchHandler"
  data_changes: []
  interface_changes:
    - "The gesture that opens OPTIONS changes. This is visible to the operator and is the point of the change; the options footer is updated to say so."

dependencies:
  internal:
    - component: "change-7f2a9c04"
      impact: "PREREQUISITE. It repoints touch.py:171 to RADIAL and removes the horizontal-swipe branch this change edits around. Implementing first would mean editing a handler that still raises AttributeError."
    - component: "TouchEventCoordinator._recognize_gesture — touch_coordinator.py:520-525"
      impact: "Already returns SWIPE_UP and SWIPE_DOWN. Read-only."
    - component: "TouchEventCoordinator.handle_gesture — touch_coordinator.py:340-345"
      impact: "Already dispatches to registered callbacks. Read-only."
    - component: "change-5012004e"
      impact: "Its conditional DOUBLE_TAP registration sits in the method being edited and must survive untouched."
  external: []
  required_changes:
    - change_ref: "change-7f2a9c04"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with a stubbed rendering engine and a real
    TouchEventCoordinator, so the registration and dispatch path is
    exercised rather than mocked. Both handler paths are driven — the
    coordinator's gesture dispatch and TouchHandler's short-press entry
    — and the pairing is asserted from each, since a disagreement
    between them is the change's principal risk.
  test_cases:
    - scenario: "SWIPE_DOWN dispatched through the coordinator while the mode is RADIAL."
      expected_result: "Mode becomes OPTIONS; _pre_options_mode records RADIAL; NAVIGATION returned."
    - scenario: "SWIPE_UP dispatched while the mode is OPTIONS."
      expected_result: "Mode returns to the recorded value; NAVIGATION returned."
    - scenario: "Down then up from RADIAL."
      expected_result: "Back at RADIAL."
    - scenario: "Down then up while the disconnected condition holds."
      expected_result: "Back to the disconnected screen, not to a dataless gauge."
    - scenario: "SWIPE_UP with _pre_options_mode unset — the first exit after a restart into OPTIONS."
      expected_result: "RADIAL, the documented default."
    - scenario: "SWIPE_DOWN while already in OPTIONS."
      expected_result: "No change; NONE returned."
    - scenario: "SWIPE_UP while in RADIAL."
      expected_result: "No change; NONE returned."
    - scenario: "Both gestures in SPLASH, in ACKNOWLEDGEMENT, and with _in_setup_mode set."
      expected_result: "No change in every case."
    - scenario: "A long press through the coordinator."
      expected_result: "No mode change — LONG_PRESS is no longer registered."
    - scenario: "TouchHandler._handle_long_press with the mode OPTIONS."
      expected_result: "No mode change."
    - scenario: "TouchHandler._handle_short_press with a downward movement beyond the swipe threshold, mode RADIAL."
      expected_result: "OPTIONS entered — the legacy path agrees with the coordinator path."
    - scenario: "TouchHandler._handle_short_press with an upward movement, mode OPTIONS."
      expected_result: "The recorded mode restored."
    - scenario: "The same pairing asserted through both paths in one test."
      expected_result: "Identical outcomes. THIS IS THE PRINCIPAL TEST."
    - scenario: "TouchHandler._handle_short_press while in setup mode, and while in OPTIONS."
      expected_result: "The existing early returns fire; no swipe handling."
    - scenario: "The conditional DOUBLE_TAP registration."
      expected_result: "Still present and still conditional."
    - scenario: "_draw_options_menu footer."
      expected_result: "'Swipe up to return'."
  regression_scope:
    - "tests/display/ — once populated per ai/task.md §8.2."
    - "On gtach.local: swipe down to enter and up to leave, ten times, without a restart."
    - "On gtach.local: the three options controls and the Clear-settings confirmation still act."
    - "On gtach.local: no accidental OPTIONS entry during a normal drive cycle."
    - "On gtach.local: no new ERROR lines in start.log."
  validation_criteria:
    - "python -m py_compile on both files passes."
    - "pytest tests/ passes with no new failures."
    - "No LONG_PRESS registration remains in _setup_touch_callbacks."
    - "DisplayManager._handle_long_press is absent."
    - "Neither TouchHandler handler changes config.mode by long press."
    - "src/gtach/display/input/ is byte-identical."
    - "The conditional DOUBLE_TAP registration is byte-identical."

implementation:
  implementation_steps:
    - step: "PRECONDITION: change-7f2a9c04 landed and its long-press exit verified working, so this change is measured against a functioning control."
      owner: "William Watson"
    - step: "Add _pre_options_mode and the two handlers."
      owner: "Claude Code"
    - step: "Register the swipes; remove the LONG_PRESS registration and DisplayManager._handle_long_press."
      owner: "Claude Code"
    - step: "Update the legacy TouchHandler path to delegate to the same handlers."
      owner: "Claude Code"
    - step: "Update the options footer text."
      owner: "Claude Code"
    - step: "Assert the pairing through both paths."
      owner: "Claude Code"
    - step: "Trial on gtach.local, including whether a vertical swipe is comfortable on the round panel and whether accidental entry occurs while driving."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the long-press
    toggle. The intermediate position — swipes registered and long press
    retained — is one line and is the recorded fallback if the trial
    goes badly.
  deployment_notes: >
    A visible change to how the options screen is reached. The footer
    text is updated so the new gesture is discoverable from the screen
    it leaves. Not part of the v0.4.0 remediation set; queued behind
    change-7f2a9c04.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-7f2a9c04"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-3e8b1d72"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-3e8b1d72, a scope extension agreed by consensus on 2026-08-05."
      - "Recorded that both live handler paths must be changed together, the on-target log showing TouchHandler's is the one that fires, and that the legacy path delegates to the DisplayManager handlers so the two agree by construction rather than by discipline."
      - "Recorded remembering the entry mode rather than returning to RADIAL, because OPTIONS is reachable from the DISCONNECTED condition and returning to a dataless gauge would be wrong."
      - "Recorded the swipe direction as a deliberate choice, reversible in two lines, and retaining the long press alongside as the stated fallback if the on-target trial goes badly."
      - "Recorded the options footer text as the one visible string this change edits."

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
| 1.0 | 2026-08-05 | Initial change document coupled to issue-3e8b1d72. Registers SWIPE_DOWN and SWIPE_UP in both live handler paths, remembers the entry screen, and retires the long-press toggle. |

---

Copyright (c) 2026 William Watson. MIT License.
