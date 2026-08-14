Created: 2026 August 12

# Issue: Touch Dispatch Is Gated on OPTIONS Mode, Leaving DISCONNECTED and ACKNOWLEDGEMENT Controls Registered but Dead

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-7d4e91a3"
  title: "TouchHandler._handle_short_press dispatches to the touch coordinator only when config.mode is OPTIONS, so the DISCONNECTED screen's Setup and Simulate buttons and the ACKNOWLEDGEMENT screen's dismiss region are registered, drawn, and never hit-tested"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-7d4e91a3"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Reported 2026-08-12 during on-target verification of
    change-2ac1c602 on gtach.local, with no ELM327 emulator running.
    William observed that the DISCONNECTED screen's Setup and Simulate
    buttons do not respond to touch, while the swipe-down gesture to
    OPTIONS and the debug toggle inside OPTIONS both work normally.
    Diagnosed from logs/debug.log (2026-08-12 09:11-09:13) and source
    review.

    Not a regression from change-2ac1c602. That change touched only
    app.py, main.py, core/watchdog.py and comm/transport.py; the
    display subsystem is unmodified. The same fall-through is visible
    in the pre-change 2026-08-12 07:38 log.

affected_scope:
  components:
    - name: "TouchHandler._handle_short_press"
      file_path: "src/gtach/display/touch.py"
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
    - name: "DisplayManager._register_touch_regions (correct; context only)"
      file_path: "src/gtach/display/manager.py"
    - name: "TouchEventCoordinator.handle_touch_down (correct; context only)"
      file_path: "src/gtach/display/input/touch_coordinator.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: >
    GTach running on gtach.local with --debug and no reachable ELM327
    emulator or Bluetooth OBD adapter, so the DISCONNECTED screen is
    displayed.
  steps:
    - "Start GTach with no OBD transport reachable; wait for the DISCONNECTED screen."
    - "Tap the Setup button. Observe no response."
    - "Tap the Simulate button. Observe no response."
    - "Long-press anywhere on the DISCONNECTED screen. Observe no response."
    - "Swipe down to OPTIONS. Observe that this works."
    - "Tap the debug toggle in OPTIONS. Observe that this works."
  frequency: "always"
  reproducibility_conditions: >
    Deterministic. The behaviour follows directly from a single
    conditional in source and does not depend on timing, hardware
    state or connection state beyond reaching the affected screens.
  preconditions: >
    config.mode is any DisplayMode other than OPTIONS, and the
    application is not in setup mode.
  test_data: >
    debug.log (2026-08-12, gtach.local):

      09:11:28.240 - TouchHandler "Options touch action:
        TouchAction.SETTINGS_CHANGE". The debug toggle, actioned from
        inside OPTIONS. The dispatch path works there.

      09:11:29.091-092 - TouchEventCoordinator "Cleared all touch
        regions", then "Registered touch region: disconnected_setup"
        and "Registered touch region: disconnected_simulate". Both
        DISCONNECTED regions are registered, and no later clear occurs.

      09:12:52.665 - TouchHandler "Short press at (272, 408),
        in_setup_mode=False". No further line follows.
      09:12:53.964 - Short press at (225, 404). No further line.
      09:12:54.737 - Short press at (220, 401). No further line.
      09:12:55.303 - Short press at (237, 380). No further line.
      09:12:56.208 - Short press at (244, 397). No further line.
      09:12:56.746 - Short press at (244, 315). No further line.

    Six short presses, all inside the registered button column
    (y 240-400, x centred, width 240), all reaching
    TouchHandler._handle_short_press, none producing any subsequent
    record.

    DisplayManager.handle_touch_event logs at INFO level
    "Touch event at {pos}" (manager.py:2418). That string appears
    NOWHERE in debug.log for the entire run. The touch coordinator is
    therefore never consulted for any of these presses. This is the
    decisive evidence: the failure is a missing dispatch, not a failed
    hit-test.
  error_output: >
    None. No exception, no warning, no error is logged. The method
    returns normally having done nothing, which is why the condition
    presents as an unresponsive control rather than as a fault.

behavior:
  expected: >
    A short press on a registered touch region invokes that region's
    callback, on whatever screen the region belongs to. Tapping Setup
    on the DISCONNECTED screen enters setup mode; tapping Simulate
    enters simulation mode.
  actual: >
    TouchHandler._handle_short_press (touch.py:184-244) reaches the
    touch coordinator through exactly one branch:

      if self.display_manager.config.mode == DisplayMode.OPTIONS:
          self._handle_options_touch(x, y)
          return

    DisplayMode (display/models.py:63-70) has four members: SPLASH,
    RADIAL, OPTIONS and ACKNOWLEDGEMENT. DISCONNECTED is not among
    them — it is a derived render state within RADIAL, as
    _register_touch_regions itself states (manager.py:1462-1471). A
    short press on the DISCONNECTED screen therefore satisfies no
    branch: it is not setup mode, it is below the swipe threshold, and
    the mode is RADIAL rather than OPTIONS. Control falls off the end
    of the try block and the method returns None.

    The registration side is correct and was made correct
    deliberately. _register_touch_regions clears regions on every
    render pass, tests the derived disconnected condition BEFORE the
    mode tests, and calls _register_disconnected_regions
    (manager.py:1466-1473). Its comment records the exact failure now
    observed: "Setup and Simulate would be visible and dead, and that
    screen is the operator's only route out of a lost link"
    (issue-4d9e2f18). The regions are registered as intended; nothing
    ever asks the coordinator whether a press hit one.

    The same gate makes the ACKNOWLEDGEMENT screen's dismiss region
    dead. _register_acknowledgement_regions (manager.py:1696-1704)
    registers a full-screen region whose callback is
    _on_acknowledgement_dismissed. That callback has no other caller
    anywhere in src/ — its only route is the coordinator, which is
    never consulted in ACKNOWLEDGEMENT mode.

    _handle_long_press (touch.py:152-182) carries an independent but
    adjacent gap: on the DISCONNECTED condition it logs "Long press
    from DISCONNECTED - entering SETUP" and returns without acting, on
    a comment stating that "Actual SETUP entry requires app controller
    coordination". _enter_setup_from_disconnected (manager.py:2318)
    already exists and already performs that coordination.
  impact: >
    The DISCONNECTED screen is the operator's only route out of a lost
    link, and both of its controls are inert. With no OBD connection
    reachable, there is no way to enter setup or simulation from the
    running application; the screen can be left only by swiping to
    OPTIONS. The ACKNOWLEDGEMENT screen cannot be dismissed by its
    intended tap at all.

    Severity high rather than critical: the application remains
    responsive, OPTIONS is reachable by swipe, and the condition does
    not compound over time or require operator intervention at the
    service level.
  workaround: >
    Swipe down to OPTIONS, which dispatches normally, and use the
    controls there. This does not provide access to the Setup or
    Simulate actions the DISCONNECTED screen offers.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    CONFIRMED from source and corroborated by log absence.
    TouchHandler._handle_short_press gates its only call into
    DisplayManager.handle_touch_event on config.mode == OPTIONS. Any
    screen whose controls are registered under a different mode, or
    under a derived state rather than a mode, is drawn with live-looking
    controls that are never hit-tested.

    The gate is not a recent regression. It has been present since the
    file's origin commit (dc7c7ed) as a test against DisplayMode.SETTINGS;
    commit 9392d96 renamed the member to OPTIONS and the handler to
    _handle_options_touch, preserving the structure. No DISCONNECTED or
    ACKNOWLEDGEMENT branch was ever written. The registration side was
    subsequently corrected by issue-4d9e2f18 and the affordances given
    their present geometry by issue-f3e2d1c0 and issue-b02ed4ea, none of
    which touched the dispatch side. The two halves of the feature were
    therefore never connected.

    The asymmetry the operator observes — swipes work, OPTIONS taps
    work, DISCONNECTED taps do not — follows exactly. Swipes are
    handled by an earlier branch that delegates to DisplayManager's
    own swipe handlers and returns before the mode test
    (touch.py:208-237). The debug toggle is an OPTIONS-mode tap and
    passes through the one live branch.
  technical_notes: >
    The obvious correction is to make the dispatch unconditional rather
    than to add a branch per screen. TouchEventCoordinator.handle_touch_down
    (touch_coordinator.py:201-247) already returns None when
    _find_hit_region finds nothing, and _register_touch_regions
    registers nothing at all for connected RADIAL (manager.py:1484,
    "RADIAL registers nothing") and returns early for SPLASH. An
    unconditional dispatch is therefore a no-op on precisely those
    screens that have no controls, and removes the possibility of this
    defect recurring for any screen added later.

    Care is required on one point: _handle_options_touch does more than
    dispatch — it logs at DEBUG on entry and exit. Any replacement
    should preserve equivalent diagnostics, since the absence of a log
    line is what made this defect invisible for as long as it was.
  related_issues:
    - issue_ref: "issue-4d9e2f18"
      relationship: >
        Corrected the region REGISTRATION order so the DISCONNECTED
        screen's regions are registered rather than the gauge's. Its
        comment in manager.py anticipates the exact symptom reported
        here, but the defect lies on the dispatch side, which that
        issue did not reach.
    - issue_ref: "issue-f3e2d1c0"
      relationship: >
        Established the DISCONNECTED screen's Setup and Simulate
        affordances. Closed on rendering and registration; dispatch was
        not verified end to end.
    - issue_ref: "issue-b02ed4ea"
      relationship: >
        Set the button touch-target geometry used by _button_column for
        this screen. The geometry is not implicated: the observed
        presses fall well inside the registered rects.
    - issue_ref: "issue-f3a7c2e1"
      relationship: >
        Made the ACKNOWLEDGEMENT screen blocking. Its dismiss region is
        dead by the same root cause identified here.
    - issue_ref: "issue-2ac1c602"
      relationship: >
        Observed during on-target verification of that issue's fix, but
        unrelated to it. Recorded here to keep the two separate.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Selected approach: dispatch unconditionally.

    Replace the OPTIONS-only gate in
    TouchHandler._handle_short_press with an unconditional call to
    DisplayManager.handle_touch_event((x, y)), placed after the setup
    and swipe branches, retaining DEBUG logging of the position and the
    returned action. Screens with no registered regions become a
    no-op by construction rather than by omission.

    Secondary: give _handle_long_press's DISCONNECTED branch a real
    action by calling DisplayManager._enter_setup_from_disconnected,
    or remove the branch if long-press entry to setup is no longer
    wanted now that the Setup button will work. This is a product
    decision, not a defect, and should be settled before the change is
    authored.

    Verification must be end to end on target: registration alone has
    now twice been mistaken for a working control.
  change_ref: "change-7d4e91a3"
  resolved_date: "2026-08-12"
  resolved_by: "prompt-7d4e91a3 iteration 1"
  fix_description: >
    Two edits in src/gtach/display/touch.py. The OPTIONS-gated call in
    _handle_short_press was replaced by an unconditional
    DisplayManager.handle_touch_event((x, y)) dispatch placed after the
    setup and swipe branches, with the position and returned action
    logged at DEBUG. _handle_options_touch was deleted, its only caller
    having been removed. The inert DISCONNECTED early return and its
    local ThreadStatus import were removed from _handle_long_press.
    15 unit tests added in tests/test_touch_dispatch.py. See
    ai/workspace/report/report-7d4e91a3-unconditional-touch-dispatch.md.

verification:
  verified_date: "2026-08-12"
  verified_by: "William Watson"
  test_results: >
    Unit: all 15 tests in tests/test_touch_dispatch.py pass; full
    pytest tests/ suite passes. All ten prompt success criteria
    verified, including that no reference to _handle_options_touch or
    ThreadStatus remains in touch.py and that manager.py,
    touch_coordinator.py and models.py are byte-identical to their
    pre-change state.

    On target (gtach.local): operator confirmed the DISCONNECTED
    screen's Setup and Simulate controls respond, and that swipe
    navigation and OPTIONS paging are unchanged.

    Partial log corroboration, debug.log.1 2026-08-12 10:06:27.126:
    "TouchHandler DEBUG Touch dispatch at (278, 292) ->
    TouchAction.SETTINGS_CHANGE". That log line exists only on the new
    unconditional path, confirming the edit is live on target.
  closure_notes: >
    Closed on operator confirmation of on-target behaviour.

    Recorded honestly, because two prior issues closed on weaker
    evidence than they should have: the pulled logs do NOT contain a
    "Button disconnected_setup pressed" or "Button
    disconnected_simulate pressed" line, nor an
    "acknowledgement_dismiss" press. Debug logging was off for the run
    covering the operator's test window — logs/debug.log was 0 bytes at
    10:09 — so those presses were never written, rather than having
    failed. The single "Touch dispatch" line recovered from
    debug.log.1 establishes that the new code path is live; the
    button-level confirmation is the operator's direct observation.

    The ACKNOWLEDGEMENT screen's dismiss region, made live by the same
    edit, was not exercised during this test round. It is covered by
    the unit tests (config.mode ACKNOWLEDGEMENT dispatches) but not by
    an on-target observation. Noted rather than treated as verified.

prevention:
  preventive_measures: >
    A registered touch region with no test proving its callback fires
    is not evidence of a working control. Where a screen's controls are
    registered under a derived state rather than a DisplayMode, the
    dispatch path must be checked against the same derived state, not
    against the mode.
  process_improvements: >
    Closing an issue on a rendered affordance should require a test or
    an on-target observation that the affordance's callback ran, not
    that its region was registered. Both issue-f3e2d1c0 and
    issue-f3a7c2e1 closed on the registration half of a two-half
    feature.

verification_enhanced:
  verification_steps:
    - "Confirm by source reading that TouchHandler._handle_short_press has exactly one call into the coordinator, gated on DisplayMode.OPTIONS. [DONE.]"
    - "Confirm that DisplayManager.handle_touch_event's INFO log line is absent from the 2026-08-12 09:11 debug.log despite six short presses on the DISCONNECTED screen. [DONE.]"
    - "Confirm that _on_acknowledgement_dismissed has no caller in src/ other than the registered region's lambda. [DONE.]"
    - "After the fix, on target: tap Setup on the DISCONNECTED screen and confirm setup mode is entered."
    - "After the fix, on target: tap Simulate on the DISCONNECTED screen and confirm simulation mode is entered."
    - "After the fix, on target: confirm the ACKNOWLEDGEMENT screen dismisses on tap."
    - "After the fix, on target: confirm a tap on the connected RADIAL gauge still does nothing and logs no error."
    - "After the fix: confirm swipe navigation and OPTIONS paging are unchanged."
  verification_results: >
    First three steps complete, as recorded in test_data and root_cause
    above. Remaining steps require the fix to exist.

traceability:
  design_refs: []
  change_refs:
    - "change-7d4e91a3"
  test_refs:
    - "tests/test_touch_dispatch.py"

notes: >
  Raised separately from issue-2ac1c602 deliberately. Different
  subsystem, different root cause, and issue-2ac1c602's change is
  already implemented and awaiting on-target verification of its own
  restart path, which did not reproduce on the 2026-08-12 09:11 run.
  Folding this in would break the one-to-one issue-change coupling.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial issue document from user report during on-target verification of change-2ac1c602."
      - "Root cause confirmed from source: TouchHandler._handle_short_press gates its only coordinator dispatch on DisplayMode.OPTIONS, and DISCONNECTED is a derived state within RADIAL rather than a DisplayMode."
      - "Corroborated by the absence of DisplayManager.handle_touch_event's INFO log line across six short presses in the 2026-08-12 09:11 debug.log."
      - "Recorded that the ACKNOWLEDGEMENT screen's dismiss region is dead by the same cause, and that _handle_long_press's DISCONNECTED branch returns without acting."
      - "Recorded that this is not a regression from change-2ac1c602: the display subsystem is unmodified and the gate dates to commit dc7c7ed."
  - version: "2.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Status open -> closed. Coupled to change-7d4e91a3 iteration 1."
      - "Resolution and verification blocks completed from prompt-7d4e91a3 iteration 1 and its report."
      - "Recorded that closure rests on the operator's direct on-target observation, and that the pulled logs contain no button-level press line because debug logging was off for the test window."
      - "Recorded that the ACKNOWLEDGEMENT dismiss region, made live by the same edit, is covered by unit test but not by an on-target observation."

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
| 1.0 | 2026-08-12 | Initial issue document. Touch dispatch gated on OPTIONS mode leaves DISCONNECTED and ACKNOWLEDGEMENT controls registered but never hit-tested. Root cause confirmed from source and corroborated by log absence. Not a regression from change-2ac1c602. |
| 2.0 | 2026-08-12 | Status open -> closed. Resolved by change-7d4e91a3 iteration 1 via prompt-7d4e91a3 iteration 1. Verified by unit test and by operator observation on gtach.local. ACKNOWLEDGEMENT dismiss region noted as unit-tested but not observed on target. |

---

Copyright (c) 2026 William Watson. MIT License.
