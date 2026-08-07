Created: 2026 August 05

# Issue: Two Live Modules Still Reference a Removed Enum Member, and the Operator Cannot Leave the Options Screen

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-7f2a9c04"
  title: "TouchHandler and NavigationGestureHandler reference DisplayMode.DIGITAL, removed by change-378703da, and both are instantiated at runtime; the long press that leaves the OPTIONS screen raises AttributeError and is swallowed, so the operator is trapped on that screen"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-7f2a9c04"
    change_iteration: 1

source:
  origin: "test_result"
  test_ref: "logs/start.log, on-target session 2026-08-05 06:37-06:40"
  description: >
    Found by static review during the v0.4.0 implementation session and
    recorded as finding §6.3 of
    ai/workspace/report/v0.4.0-triple-implementation-session.md, which
    classified it as the only finding able to fault the running
    application. Confirmed on target on 2026-08-05: the operator
    deployed the branch to gtach.local, could not leave the OPTIONS
    screen by long press, and pulled the logs back. Task list reference
    ai/task.md §9.8.5 item 1.

affected_scope:
  components:
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
    - name: "TouchHandler._handle_short_press"
      file_path: "src/gtach/display/touch.py"
    - name: "TouchHandler._process_settings_touch"
      file_path: "src/gtach/display/touch.py"
    - name: "NavigationGestureHandler._cycle_display_mode"
      file_path: "src/gtach/display/navigation_gestures.py"
    - name: "NavigationGestureHandler._exit_settings"
      file_path: "src/gtach/display/navigation_gestures.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: >
    The v0.4.0-display-triples branch deployed to gtach.local. Any build
    in which change-378703da has landed.
  steps:
    - "Long press to enter the OPTIONS screen. It appears."
    - "Long press again to leave it. Nothing happens; the screen remains."
    - "Swipe horizontally on the gauge. Nothing happens."
    - "Read logs/start.log and find 'TouchHandler ERROR Long press handling error: DIGITAL'."
    - "Statically: grep DisplayMode.DIGITAL across src/gtach and find eight sites in display/touch.py and two in display/navigation_gestures.py."
    - "Confirm both classes are constructed at runtime: DisplayManager._initialize_legacy_components builds TouchHandler at manager.py:277 and NavigationGestureHandler at manager.py:312."
    - "Confirm TouchHandler is wired to a live event source: touch.py:78 registers _handle_touch_event as a callback on a started touch interface."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional on the affected paths. Every long press that would
    leave OPTIONS fails, and every horizontal swipe on the gauge fails.
    Entering OPTIONS still works, because that branch assigns
    DisplayMode.OPTIONS rather than DIGITAL.
  preconditions: "None beyond a build carrying change-378703da."
  test_data: >
    ON-TARGET EVIDENCE, from logs/start.log, session 2026-08-05:

      06:39:54,899  TouchHandler ERROR Short press handling error: DIGITAL
      06:39:55,878  TouchHandler ERROR Short press handling error: DIGITAL
      06:39:57,403  TouchHandler ERROR Short press handling error: DIGITAL
      06:40:08,372  TouchHandler ERROR Long press handling error: DIGITAL
      06:40:09,798  TouchHandler ERROR Long press handling error: DIGITAL

    Five occurrences, no other errors in 3.5 MB of log. The message body
    is the bare word DIGITAL because accessing a non-existent member of
    an Enum raises AttributeError('DIGITAL') and both handlers log
    f'...: {e}' without the exception type.

    THE FAULT IS SWALLOWED, WHICH IS WHY IT PRESENTS AS AN INERT
    CONTROL. touch.py:174-175 and 205-206 each catch Exception and log
    at ERROR without re-raising. The application does not crash; the
    gesture simply does nothing. To the operator the screen is stuck.

    SITE INVENTORY, all confirmed at 0.3.3.

      display/touch.py
        171  _handle_long_press — change_mode(DIGITAL) when leaving
             OPTIONS. LIVE. This is the trapped-operator fault.
        195  _handle_short_press — right-swipe branch, compares to
             DIGITAL. LIVE.
        198  _handle_short_press — right-swipe branch, assigns DIGITAL.
        200  _handle_short_press — left-swipe branch, compares.
        203  _handle_short_press — left-swipe branch, assigns.
        243  _process_settings_touch — setting_id 'mode', compares.
        246  _process_settings_touch — setting_id 'mode', assigns.
        274  _process_settings_touch — setting_id 'save', ternary.

      display/navigation_gestures.py
        428  _cycle_display_mode — _cycle = [DIGITAL, RADIAL].
        474  _exit_settings — change_mode(DIGITAL).

    WHAT IS ACTUALLY DEAD, AS DISTINCT FROM MERELY BROKEN. RADIAL is now
    the only normal display mode, so:

      - the swipe branches at touch.py:195-203 cycle between two modes
        of which one no longer exists. There is nothing to switch to.
      - _process_settings_touch's 'mode' branch (243-246) toggles the
        same pair, and is reached only from the settings screen whose
        registration methods (_register_rpm_sliders,
        _register_save_button) are themselves unreachable — recorded as
        dead in change-378703da scope.out_of_scope.
      - _cycle_display_mode cycles a one-element set.

    Only three sites describe behaviour that should still exist:
    touch.py:171 and navigation_gestures.py:474, both of which are
    'return to the normal screen', and touch.py:274's save-and-exit
    ternary, which collapses to RADIAL.
  error_output: >
    TouchHandler ERROR Long press handling error: DIGITAL
    TouchHandler ERROR Short press handling error: DIGITAL

    Underlying: AttributeError: DIGITAL, raised at the attribute access
    on the DisplayMode enum, before change_mode is called.

behavior:
  expected: >
    Removing an enum member removes every reference to it. A long press
    on the OPTIONS screen returns to the gauge.
  actual: >
    change-378703da removed DisplayMode.DIGITAL under a four-file
    constraint that excluded display/touch.py and
    display/navigation_gestures.py. Both survive, both are constructed
    at runtime, and TouchHandler is wired to a live touch interface. Ten
    references remain. Two of them are on paths the operator exercises
    routinely, and both fail silently because the surrounding handlers
    catch Exception and log.
  impact: >
    The operator cannot leave the OPTIONS screen. That is the whole of
    the practical impact and it is sufficient on its own: the screen is
    entered by long press and left by long press, and only the leaving
    is broken. Recovery is a restart.

    Horizontal swipes on the gauge also fail, but they should no longer
    do anything — that is dead behaviour failing loudly rather than
    absent behaviour.
  workaround: >
    Restart the application. There is no in-application route off the
    OPTIONS screen.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    A file-scoped constraint that did not match the change's semantic
    scope. change-378703da removed an enum member — a package-wide
    interface change — under a prompt permitting four files. The two
    modules holding the remaining references were not in that set, and
    the prompt's own success criterion, "grep -r 'DIGITAL' src/gtach
    returns no match", was therefore unsatisfiable by any correct
    execution of it.

    The executor recorded exactly this at report §6.3 and did not
    silently exceed its scope, which was the right call. The defect is
    in the prompt's scope, not in its execution.
  technical_notes: >
    WHY THE CRITERION AND THE CONSTRAINT CONTRADICTED EACH OTHER.
    prompt-378703da lists 'grep -r DIGITAL src/gtach returns no match'
    as a success criterion, constrains the executor to four files, and
    mandates the literal string 'DIGITAL' in the migration branch at its
    own EDIT 6(a). Three requirements, no two of which can hold
    together. This issue removes the first conflict; the second is
    resolved by restating the criterion in terms of DisplayMode.DIGITAL
    attribute access rather than the bare token, which is what the
    criterion was reaching for.

    ON manager_backup.py AND setup_original_backup.py. Both carry
    further DIGITAL references — five and several respectively. Neither
    is imported anywhere in src/gtach; both are excluded from review by
    the standing backup-file convention recorded in
    display-ui-graphics-review.md §2.1. They are NOT corrected here and
    are NOT the reason the grep criterion is restated. Their disposition
    is a dead-file question separate from this defect.

    WHY THE SEVERITY IS HIGH RATHER THAN CRITICAL. The application does
    not crash, does not lose data, and continues to display RPM
    correctly. A restart recovers it. It is High because a routine
    operator action has no effect and there is no in-application
    recovery.

    RELATIONSHIP TO THE SWIPE-NAVIGATION PROPOSAL. The operator has
    proposed replacing long-press OPTIONS access with swipe-down to
    enter and swipe-up to leave. That is authored separately as
    issue-3e8b1d72 and is deliberately not folded in here: this triple
    restores a broken control, and mixing a defect fix with a
    navigation redesign would make a subsequent navigation problem
    unattributable. 3e8b1d72 is written against the corrected file and
    depends on this triple landing first.
  related_issues:
    - issue_ref: "issue-378703da"
      relationship: "related"
    - issue_ref: "issue-3e8b1d72"
      relationship: "blocks"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Repoint the three sites that describe surviving behaviour to RADIAL
    and remove the four dead mode-switching paths. See change-7f2a9c04.
  change_ref: "change-7f2a9c04"
  resolved_date: "2026-08-05"
  resolved_by: "Claude Code, per prompt-7f2a9c04"
  fix_description: >
    touch.py:171 and navigation_gestures.py:474 repointed to RADIAL;
    the four dead mode-switching paths (touch.py swipe branches,
    _process_settings_touch's mode branch, _cycle_display_mode) removed.

verification:
  verified_date: "2026-08-05"
  verified_by: "William Watson (gtach.local, task.md §9.10)"
  test_results: >
    On-target session 2026-08-05 (task.md §9.10): one ERROR in 362 KB
    and no DIGITAL line, confirming both this fix and 3e8b1d72 clean.
    Source re-check 2026-08-07: grep for DisplayMode.DIGITAL across
    touch.py returns nothing; navigation_gestures.py:431 carries only an
    explanatory comment ("Mode cycling ended with DIGITAL's
    retirement").
  closure_notes: >
    William confirmed on 2026-08-07 that GTach is functioning correctly
    on gtach.local, consistent with §9.10's confirmation. No residual
    finding.

prevention:
  preventive_measures: >
    A change that alters a package-wide interface — removing an enum
    member, renaming a public attribute — cannot be scoped by file list.
    The scope is every reference, and the prompt should be written by
    grepping for them rather than by naming the files the author
    expected to be involved.

    A handler that catches Exception and logs turns a crash into an
    inert control. That is usually the right trade on a vehicle, and its
    cost is that a defect of this kind survives until someone reads the
    log. The five ERROR lines were present from the first session.
  process_improvements: >
    prompt-378703da carried a success criterion that no correct
    execution could satisfy. A criterion that contradicts the same
    document's constraints should be caught when the prompt is authored,
    by checking each criterion against the file list before the prompt
    is approved.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/touch.py src/gtach/display/navigation_gestures.py passes."
    - "grep -rn 'DisplayMode.DIGITAL' src/gtach --include=*.py returns matches only in manager_backup.py and setup_original_backup.py, neither of which is imported."
    - "TouchHandler._handle_long_press sets RADIAL when leaving OPTIONS and raises nothing."
    - "A long press while in OPTIONS returns to RADIAL — asserted against a stubbed DisplayManager."
    - "A long press while not in OPTIONS still enters OPTIONS, unchanged."
    - "The horizontal-swipe branch is absent from _handle_short_press; a swipe raises nothing and changes no mode."
    - "_process_settings_touch has no 'mode' branch; its 'save' branch sets RADIAL."
    - "NavigationGestureHandler._exit_settings sets RADIAL."
    - "_cycle_display_mode is absent, or is a documented no-op with no caller."
    - "Every other behaviour of both classes is unchanged: setup routing, options touch, slider handling, edge feedback."
    - "On gtach.local: enter OPTIONS by long press, leave by long press, and confirm the gauge returns."
    - "On gtach.local: logs/start.log contains no 'handling error: DIGITAL' line across a session exercising both gestures."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-7f2a9c04"
  test_refs: []

notes: >
  Raised under P04 from finding §6.3 of the v0.4.0 implementation
  report, and confirmed on target before this document was authored.
  It is not a numbered item of either code review and carries no §7.0
  task number; it is a consequence of change-378703da's scope.

  issue_info.type is defect and severity is high: a routine operator
  action has no effect and there is no in-application recovery.

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
      - "Initial issue document from finding §6.3 of the v0.4.0 implementation session report, confirmed on target by the 2026-08-05 gtach.local session."
      - "Recorded the on-target evidence: five 'handling error: DIGITAL' lines in logs/start.log and no other errors in 3.5 MB."
      - "Recorded that the fault is swallowed by the surrounding except-Exception handlers, which is why it presents as an inert control rather than a crash."
      - "Distinguished the three sites describing surviving behaviour from the seven that are dead now that RADIAL is the only normal mode."
      - "Recorded that prompt-378703da's grep criterion, its four-file constraint and its own EDIT 6(a) are mutually unsatisfiable, and that the executor was right to report rather than exceed scope."
      - "Recorded the backup files as out of scope and the swipe-navigation proposal as separately authored in issue-3e8b1d72."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status open -> closed. change-7f2a9c04 implemented and confirmed clean on-target 2026-08-05 (task.md §9.10, one ERROR in 362 KB, no DIGITAL line). Source re-check confirms no live DisplayMode.DIGITAL references."
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
| 1.0 | 2026-08-05 | Initial issue document from report finding §6.3, confirmed on target. Records the log evidence, the swallowed-exception mechanism, the site inventory split by whether the behaviour survives, and the mutually unsatisfiable criteria in `prompt-378703da`. |
| 1.1 | 2026-08-07 | Status open → closed. Resolution and verification recorded; confirmed clean on-target and by source re-check. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
