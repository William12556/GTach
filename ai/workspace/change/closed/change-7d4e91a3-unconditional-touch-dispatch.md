Created: 2026 August 12

# Change: Dispatch Short Presses to the Touch Coordinator Unconditionally

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-7d4e91a3"
  title: "Replace the OPTIONS-only gate in TouchHandler._handle_short_press with an unconditional dispatch to the touch coordinator, so every registered region is hit-tested regardless of screen; remove the inert DISCONNECTED branch from _handle_long_press"
  date: "2026-08-12"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-7d4e91a3"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-7d4e91a3"
  description: >
    Resolves issue-7d4e91a3. The DISCONNECTED screen's Setup and
    Simulate buttons and the ACKNOWLEDGEMENT screen's dismiss region
    are registered, drawn, and never hit-tested, because
    TouchHandler._handle_short_press reaches
    DisplayManager.handle_touch_event only when config.mode is
    DisplayMode.OPTIONS.

scope:
  summary: >
    Two edits in one file. Replace the mode-gated dispatch in
    _handle_short_press with an unconditional one placed after the
    setup and swipe branches, folding _handle_options_touch's
    diagnostics into it and deleting that now-unreferenced method.
    Remove the inert DISCONNECTED early return from _handle_long_press.
  affected_components:
    - name: "TouchHandler._handle_short_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
    - name: "TouchHandler._handle_options_touch"
      file_path: "src/gtach/display/touch.py"
      change_type: "delete"
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/display/manager.py. _register_touch_regions is correct as written and is the reference for which regions belong to which screen. No registration change is made."
    - "src/gtach/display/input/touch_coordinator.py. handle_touch_down already returns None on no hit; no coordinator change is required."
    - "Touch-target geometry. The observed presses fall well inside the registered rects; issue-b02ed4ea's geometry is not implicated."
    - "The setup-mode path (_handle_setup_touch) and the swipe branches, both of which already work and both of which return before the dispatch."
    - "DisplayManager.handle_touch_event's internal routing, including its _in_setup_mode branch, which is unreachable from this path because _handle_short_press returns earlier on the same condition."

rational:
  problem_statement: >
    TouchHandler._handle_short_press (touch.py:184-244) calls into the
    touch coordinator through exactly one branch:

      if self.display_manager.config.mode == DisplayMode.OPTIONS:
          self._handle_options_touch(x, y)
          return

    DisplayMode (display/models.py:63-70) has four members: SPLASH,
    RADIAL, OPTIONS, ACKNOWLEDGEMENT. DISCONNECTED is not among them —
    it is a derived render state within RADIAL, as
    _register_touch_regions states at manager.py:1462-1471. A short
    press on DISCONNECTED satisfies no branch: not setup mode, below
    the swipe threshold, mode RADIAL not OPTIONS. Control falls off the
    end of the try block and the method returns having done nothing,
    silently.

    The ACKNOWLEDGEMENT screen is dead by the same gate.
    _on_acknowledgement_dismissed (manager.py:2241) has no caller in
    src/ other than the region lambda at manager.py:1703, whose only
    route is the coordinator.

    The registration side is correct and was made correct
    deliberately. Its comment records the exact symptom now observed:
    "Setup and Simulate would be visible and dead, and that screen is
    the operator's only route out of a lost link" (issue-4d9e2f18). The
    two halves of the feature were never connected.

    Confirmed by log absence. DisplayManager.handle_touch_event logs at
    INFO "Touch event at {pos}" (manager.py:2418); that string appears
    nowhere in the 2026-08-12 09:11 debug.log despite six short presses
    inside the registered button column.
  proposed_solution: >
    Dispatch unconditionally rather than adding a branch per screen.

    After the setup and swipe branches return, call
    self.display_manager.handle_touch_event((x, y)) with no mode test,
    logging the position and the returned action at DEBUG.

    This is safe on every screen that has no controls, by construction
    rather than by omission. _register_touch_regions clears all regions
    on every render pass (manager.py:1454), returns early for SPLASH
    with the comment "no controls" (manager.py:1456-1457), and
    registers nothing for connected RADIAL (manager.py:1484, "RADIAL
    registers nothing"). TouchEventCoordinator.handle_touch_down
    returns None when _find_hit_region finds nothing
    (touch_coordinator.py:227-245). A press on a screen with no
    registered regions is therefore a no-op that logs one DEBUG line.

    The decisive benefit over a per-screen branch is that no future
    screen can reintroduce this defect by omission. A screen either
    registers regions or it does not; the dispatch no longer needs to
    know which screens exist.

    Separately, remove the DISCONNECTED early return from
    _handle_long_press (touch.py:154-166), which logs "Long press from
    DISCONNECTED - entering SETUP" and returns without acting, on a
    comment stating that setup entry "requires app controller
    coordination" — coordination that _enter_setup_from_disconnected
    (manager.py:2318) already provides and that the Setup button will
    now reach. A log line claiming an action it does not perform is
    worse than no branch at all.
  alternatives_considered:
    - option: "Add an explicit DISCONNECTED branch to the existing mode gate."
      reason_rejected: >
        Leaves ACKNOWLEDGEMENT dead unless a second branch is added,
        and leaves the same omission available to every screen added
        later. The gate has now failed twice by omission — once for
        DISCONNECTED, once for ACKNOWLEDGEMENT — which is the argument
        against retaining its shape.
    - option: "Promote DISCONNECTED to a DisplayMode member."
      reason_rejected: >
        A substantial architectural change touching mode persistence
        (manager.py:518, 605-606), render dispatch
        (_render_normal_modes) and region registration, to fix a
        one-line dispatch defect. The derived-state design is
        deliberate and documented; it is the dispatch that failed to
        respect it.
    - option: "Dispatch unconditionally and retain _handle_options_touch as the call site."
      reason_rejected: >
        The method's name would then misdescribe every call. Its body
        is three lines, two of which are logging. Folding it in and
        deleting it is smaller than keeping it.
    - option: "Wire _handle_long_press's DISCONNECTED branch to _enter_setup_from_disconnected."
      reason_rejected: >
        Once the Setup button works, a second and undiscoverable route
        to the same action adds no capability. Removing the branch is
        the smaller change and eliminates a misleading log line.
  benefits:
    - "The DISCONNECTED screen's Setup and Simulate controls work. That screen is the operator's only route out of a lost link."
    - "The ACKNOWLEDGEMENT screen dismisses on tap, as issue-f3a7c2e1 intended."
    - "No screen added later can reintroduce this defect by omitting a branch."
    - "Net reduction in source: one method deleted, one dead branch removed, one conditional replaced by a direct call."
    - "Every short press now produces a DEBUG line recording the dispatch and its result. The absence of such a line is what concealed this defect."
  risks:
    - risk: >
        A press on the connected RADIAL gauge now reaches the
        coordinator where previously it did not.
      mitigation: >
        RADIAL registers no regions (manager.py:1484) and
        handle_touch_down returns None on no hit. The observable
        difference is one additional DEBUG line per press. Covered by
        an explicit test case and by an on-target verification step.
    - risk: >
        Removing the DISCONNECTED early return from _handle_long_press
        means a long press on that screen now falls through to
        DisplayManager._handle_long_press and toggles the day/night
        palette, where previously it did nothing.
      mitigation: >
        This is a deliberate and accepted behaviour change, not an
        incidental one. The palette toggle (issue-2b6f4d91) is
        available on every other screen; DISCONNECTED was excluded only
        as a side effect of the early return, whose stated purpose was
        setup entry. Recorded here so it is not discovered as a
        surprise. If it proves unwanted, the correction is to gate the
        palette toggle in DisplayManager, where the mode rules live,
        not to restore an inert branch in the handler.
    - risk: >
        DisplayManager.handle_touch_event contains an _in_setup_mode
        branch that routes to the setup manager. Reaching it twice
        could double-handle a setup touch.
      mitigation: >
        Unreachable from this path. _handle_short_press tests
        is_in_setup_mode() first and returns via _handle_setup_touch
        (touch.py:189-191), so the unconditional dispatch is only
        reached when setup mode is false.
    - risk: >
        The local `from ..core import ThreadStatus` import in
        _handle_long_press becomes unused after the branch is removed.
      mitigation: >
        Delete it with the branch. It is a function-local import used
        by that branch alone; `DisplayMode` at touch.py:26 remains in
        use at touch.py:306 and must be retained.

technical_details:
  current_behavior: >
    Short presses reach the touch coordinator only in OPTIONS mode.
    On DISCONNECTED, ACKNOWLEDGEMENT, and connected RADIAL, the press
    is discarded without dispatch, log or error. Long presses on
    DISCONNECTED log an entering-SETUP message and do nothing.
  proposed_behavior: >
    Short presses that are neither setup-mode touches nor swipes are
    dispatched to the touch coordinator on every screen. Registered
    regions fire their callbacks; screens with no registered regions
    are a logged no-op. Long presses on DISCONNECTED behave as on every
    other screen.
  implementation_approach: >
    Two localised edits in src/gtach/display/touch.py. No other file is
    touched. No new imports, no new dependencies, no interface change
    visible outside the module.
  code_changes:
    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: >
        Replace the OPTIONS-gated call with an unconditional
        handle_touch_event dispatch; delete _handle_options_touch;
        remove the DISCONNECTED early return and its local ThreadStatus
        import from _handle_long_press.
      functions_affected:
        - "_handle_short_press"
        - "_handle_options_touch"
        - "_handle_long_press"
      classes_affected:
        - "TouchHandler"
  data_changes: []
  interface_changes:
    - interface: "TouchHandler._handle_options_touch"
      change_type: "signature"
      details: >
        Removed. Private to the module; its sole caller is removed in
        the same edit. No test or external reference exists.
      backward_compatible: "n/a"

dependencies:
  internal:
    - component: "DisplayManager.handle_touch_event"
      impact: >
        Called on every non-setup, non-swipe short press rather than
        only in OPTIONS. Not modified. Its INFO-level "Touch event at
        {pos}" log now appears for every such press.
    - component: "TouchEventCoordinator.handle_touch_down"
      impact: >
        Consulted on every such press. Not modified. Its
        _stats['touches_processed'] counter will now increment on
        screens where it previously did not.
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Unit tests against a stubbed DisplayManager for the dispatch
    decision, plus on-target verification for the three affected
    screens, since registration alone has twice been mistaken for a
    working control.
  test_cases:
    - scenario: "Short press, not in setup mode, below the swipe threshold, config.mode RADIAL."
      expected_result: "display_manager.handle_touch_event is called once with (x, y)."
    - scenario: "Short press, not in setup mode, below the swipe threshold, config.mode ACKNOWLEDGEMENT."
      expected_result: "display_manager.handle_touch_event is called once with (x, y)."
    - scenario: "Short press, not in setup mode, below the swipe threshold, config.mode OPTIONS."
      expected_result: "display_manager.handle_touch_event is called once with (x, y); behaviour unchanged from before."
    - scenario: "Short press while in setup mode."
      expected_result: "_handle_setup_touch is called; handle_touch_event is NOT called."
    - scenario: "Press whose displacement meets or exceeds the swipe threshold, vertical dominant, downward."
      expected_result: "_handle_swipe_down is called; handle_touch_event is NOT called."
    - scenario: "Press whose displacement meets or exceeds the swipe threshold, horizontal dominant, leftward."
      expected_result: "_handle_swipe_left is called; handle_touch_event is NOT called."
    - scenario: "handle_touch_event raises."
      expected_result: "The exception is caught and logged by the existing handler; _handle_short_press does not propagate it."
    - scenario: "Long press while the OBD thread is not RUNNING and sim mode is off."
      expected_result: "display_manager._handle_long_press is called with ((x, y), (x, y)); no entering-SETUP message is logged."
    - scenario: "On target: tap Setup on the DISCONNECTED screen."
      expected_result: "Setup mode is entered."
    - scenario: "On target: tap Simulate on the DISCONNECTED screen."
      expected_result: "Simulation mode is entered."
    - scenario: "On target: tap the ACKNOWLEDGEMENT screen."
      expected_result: "The screen is dismissed."
    - scenario: "On target: tap the connected RADIAL gauge."
      expected_result: "Nothing happens; one DEBUG dispatch line is logged; no error."
  regression_scope:
    - "Swipe down to OPTIONS and swipe up to return."
    - "Horizontal paging within the OPTIONS menu."
    - "All OPTIONS-menu controls, including the debug toggle and the update and confirm-clear sub-views."
    - "Setup-mode touch handling throughout."
    - "Long-press palette toggle on RADIAL and OPTIONS."
    - "tests/ suite in full."
  validation_criteria:
    - "No reference to _handle_options_touch remains in src/."
    - "No mode test gates the coordinator dispatch in _handle_short_press."
    - "src/gtach/display/manager.py and src/gtach/display/input/touch_coordinator.py are byte-identical to their pre-change state."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Edit _handle_short_press: replace the OPTIONS gate with an unconditional dispatch and fold in the DEBUG logging."
      owner: "tactical"
    - step: "Delete _handle_options_touch."
      owner: "tactical"
    - step: "Edit _handle_long_press: remove the DISCONNECTED early return and its local ThreadStatus import."
      owner: "tactical"
    - step: "Add unit tests per testing_requirements.test_cases items 1-8."
      owner: "tactical"
    - step: "Deploy to gtach.local and run the four on-target scenarios."
      owner: "human"
  rollback_procedure: >
    Revert the commit. A single file is modified and no state,
    configuration or persisted data is affected.
  deployment_notes: >
    Display-only change. No service, packaging or configuration change.
    Verification requires no reachable OBD transport, so that the
    DISCONNECTED screen is displayed.

verification:
  implemented_date: "2026-08-12"
  implemented_by: "prompt-7d4e91a3 iteration 1 (claude_code)"
  verification_date: "2026-08-12"
  verified_by: "William Watson"
  test_results: >
    Unit: 15 tests added in tests/test_touch_dispatch.py, all passing;
    full pytest tests/ suite passes. All ten prompt success criteria
    verified.

    On target (gtach.local): operator confirmed the DISCONNECTED
    screen's Setup and Simulate controls respond and that swipe
    navigation and OPTIONS paging are unchanged.

    Log corroboration that the new path is live, debug.log.1
    2026-08-12 10:06:27.126: "TouchHandler DEBUG Touch dispatch at
    (278, 292) -> TouchAction.SETTINGS_CHANGE". That line exists only
    on the unconditional dispatch path.

    Not observed on target: a press of the ACKNOWLEDGEMENT screen's
    dismiss region, and the DISCONNECTED long-press palette toggle
    introduced by EDIT B. Both are covered by unit test. Recorded in
    the coupled issue's closure_notes rather than claimed as verified.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-3e8b1d72"
      relationship: >
        related. Established the swipe branches in _handle_short_press
        that this change leaves intact and dispatches after.
    - change_ref: "change-8c5a1e73"
      relationship: >
        related. Added horizontal paging to the same method.
    - change_ref: "change-2b6f4d91"
      relationship: >
        related. Established the long-press palette toggle that a
        DISCONNECTED long press now reaches, as recorded under risks.
  related_issues:
    - issue_ref: "issue-7d4e91a3"
      relationship: "resolves"
    - issue_ref: "issue-4d9e2f18"
      relationship: >
        related. Corrected the registration half of this feature and
        anticipated this symptom in a source comment.
    - issue_ref: "issue-f3e2d1c0"
      relationship: "related. Established the DISCONNECTED affordances this change makes live."
    - issue_ref: "issue-f3a7c2e1"
      relationship: "related. The ACKNOWLEDGEMENT dismiss region this change makes live."
    - issue_ref: "issue-2ac1c602"
      relationship: >
        related only by discovery. Observed during on-target
        verification of that change; different subsystem, different
        root cause, no shared code.

notes: >
  The removal of the DISCONNECTED long-press branch carries one
  behaviour change that is intended rather than incidental: a long
  press on DISCONNECTED will toggle the day/night palette, as it does
  on every other screen. This is recorded under rational.risks so it is
  not met as a surprise during verification.

  Two prior issues closed on the registration half of this feature.
  The verification steps for this change deliberately require observing
  a callback's effect on target, not a region's registration in a log.

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-7d4e91a3 iteration 1."
      - "Approach selected: unconditional dispatch rather than a per-screen branch, on the grounds that the mode gate has now failed twice by omission."
      - "Records the deliberate removal of the inert DISCONNECTED branch in _handle_long_press and the palette-toggle behaviour change that follows from it."
  - version: "1.1"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Status proposed -> closed. Implemented by prompt-7d4e91a3 iteration 1; verification block completed."
      - "Recorded that the ACKNOWLEDGEMENT dismiss region and the DISCONNECTED long-press palette toggle were unit-tested but not observed on target."

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
| 1.0 | 2026-08-12 | Initial change document. Unconditional touch dispatch in TouchHandler._handle_short_press; _handle_options_touch deleted; inert DISCONNECTED branch removed from _handle_long_press. |
| 1.1 | 2026-08-12 | Status proposed -> closed. Implemented by prompt-7d4e91a3 iteration 1 and verified by unit test and operator observation on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
