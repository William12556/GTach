Created: 2026 August 05

# Change: Free the Operator from the Options Screen

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-7f2a9c04"
  title: "Three DisplayMode.DIGITAL references describing surviving behaviour are repointed to RADIAL and the seven that cycle between two modes are removed, restoring the long press that leaves the OPTIONS screen"
  date: "2026-08-05"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-7f2a9c04"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-7f2a9c04"
  description: >
    Resolves issue-7f2a9c04. Raised under P04 from finding §6.3 of
    ai/workspace/report/v0.4.0-triple-implementation-session.md and
    confirmed on target by the gtach.local session of 2026-08-05. Task
    list reference ai/task.md §9.8.5 item 1.

scope:
  summary: >
    Ten references to a removed enum member in two runtime-instantiated
    modules. Three describe behaviour that survives DIGITAL's retirement
    and are repointed; seven cycle between two modes of which one no
    longer exists and are removed.
  affected_components:
    - name: "TouchHandler._handle_long_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
    - name: "TouchHandler._handle_short_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
    - name: "TouchHandler._process_settings_touch"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
    - name: "NavigationGestureHandler._cycle_display_mode"
      file_path: "src/gtach/display/navigation_gestures.py"
      change_type: "remove"
    - name: "NavigationGestureHandler._exit_settings"
      file_path: "src/gtach/display/navigation_gestures.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "display/manager_backup.py and display/setup_original_backup.py. Both carry further DIGITAL references; neither is imported anywhere. Excluded by the standing backup-file convention (display-ui-graphics-review.md §2.1). Their disposition is a dead-file question, not this defect."
    - "src/gtach/display/manager.py. change-378703da left it correct; nothing here needs it."
    - "src/gtach/display/input/. The touch coordinator is not implicated."
    - "The OPTIONS access gesture itself. Replacing long press with swipe-down/up is change-3e8b1d72, authored separately and written against this change's output."
    - "The unreachable settings screen (_register_rpm_sliders, _render_slider_visuals, _register_save_button in manager.py). _process_settings_touch serves it and is edited here only to remove DIGITAL; whether the screen should exist at all is a separate question."
    - "The except-Exception handlers that swallowed the fault. Narrowing them would surface future faults of this class, but doing so on a vehicle display is a deliberate trade and belongs in its own cycle."

rational:
  problem_statement: >
    The operator cannot leave the OPTIONS screen. TouchHandler and
    NavigationGestureHandler still reference DisplayMode.DIGITAL, which
    change-378703da removed; both are constructed at runtime and
    TouchHandler is wired to a live touch interface. The long press that
    leaves OPTIONS raises AttributeError, the surrounding handler
    catches and logs it, and the gesture silently does nothing.
  proposed_solution: >
    Repoint the three references that mean 'return to the normal
    screen'. Remove the seven that switch between two modes, there now
    being one.
  alternatives_considered:
    - option: "Repoint all ten references to RADIAL and remove nothing."
      reason_rejected: >
        Smallest diff and fastest to verify. Rejected because it leaves
        a swipe handler that switches from RADIAL to RADIAL, a settings
        control that toggles a mode to itself, and a cycle over a
        one-element list. All three would read as intentional to the
        next author and none does anything. The operator's decision on
        this triple was to remove the dead paths."
    - option: "Restore DisplayMode.DIGITAL as an alias for RADIAL."
      reason_rejected: >
        Fixes the crash in one line and reverses a decision taken and
        implemented three sessions ago (ai/task.md §7.3.14,
        change-378703da). It would also leave a member whose name
        contradicts its meaning."
    - option: "Fold the swipe-navigation redesign in, since these are the files it touches."
      reason_rejected: >
        Offered and declined. A defect fix and a UI redesign landing
        together means a subsequent navigation problem cannot be
        attributed to either. change-3e8b1d72 is authored separately and
        depends on this change."
    - option: "Narrow the except-Exception handlers so a fault of this class surfaces rather than presenting as an inert control."
      reason_rejected: >
        Correct in principle and out of scope here. An unhandled
        exception on the touch thread of a vehicle display is worse than
        an inert gesture; the right form is a narrower catch plus an
        on-screen indication, which is a design question rather than a
        line edit. Recorded so the option is not lost."
  benefits:
    - "The operator can leave the OPTIONS screen. That is the point of the change."
    - "Ten references to a non-existent enum member removed; the package stops carrying an interface change that was only three-quarters applied."
    - "Roughly 25 lines of code that could not do anything removed."
  risks:
    - risk: >
        Removing the swipe branch from _handle_short_press disturbs the
        setup-mode routing or the options-touch routing that precede it
        in the same method.
      mitigation: >
        Both precede the swipe branch and return early (touch.py:181-186
        and 188-190). The edit is confined to the block after them. Both
        early returns are asserted unchanged."
    - risk: >
        _cycle_display_mode has a caller that is not obvious.
      mitigation: >
        grep before removing. If a caller exists it is a swipe handler
        cycling a one-element list; make the method a no-op with a
        comment rather than deleting it, and record which was done."
    - risk: >
        A further DIGITAL reference exists in a module not yet examined.
      mitigation: >
        The success criterion is a repository-wide grep rather than a
        list of expected sites — which is the discipline whose absence
        caused this defect."
  benefits_measurement: >
    Routine operator actions that fail silently: 2 -> 0. References to a
    removed enum member in imported modules: 10 -> 0. Log ERROR lines per
    session exercising both gestures: 5 -> 0.

technical_details:
  current_behavior: >
    display/touch.py holds eight references, at 171, 195, 198, 200, 203,
    243, 246 and 274. display/navigation_gestures.py holds two, at 428
    and 474. Attribute access on the removed member raises
    AttributeError('DIGITAL'), caught at touch.py:174-175 and 205-206
    and by the handlers in navigation_gestures.py, and logged at ERROR.
  proposed_behavior: >
    touch.py:171 and navigation_gestures.py:474 set RADIAL.
    touch.py:274's ternary collapses to RADIAL. The swipe branch, the
    settings 'mode' branch and _cycle_display_mode are gone.
  implementation_approach: >
    FIVE EDITS, TWO FILES.

    1. touch.py:168-171 — the OPTIONS exit. The else-branch becomes
       change_mode(DisplayMode.RADIAL). This single line is the fix the
       operator needs; everything else is consequence.

    2. touch.py:191-203 — the horizontal-swipe branch of
       _handle_short_press. Removed entirely, together with the
       swipe_threshold local and the dx computation that serve only it.
       The setup and options early returns above it are untouched.

    3. touch.py:241-246 — the setting_id == 'mode' branch of
       _process_settings_touch. Removed. The elif chain below it is
       unaffected; confirm the first surviving branch becomes an if or
       remains an elif correctly.

    4. touch.py:271-276 — the setting_id == 'save' branch's ternary.
       Collapses to change_mode(DisplayMode.RADIAL).

    5. navigation_gestures.py — _exit_settings (474) sets RADIAL.
       _cycle_display_mode (424-435) is removed if it has no caller, or
       made a documented no-op if it has one.
  code_changes:
    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: >
        OPTIONS exit repointed to RADIAL; the horizontal-swipe branch
        and the settings 'mode' branch removed; the save branch's
        ternary collapsed.
      functions_affected:
        - "_handle_long_press"
        - "_handle_short_press"
        - "_process_settings_touch"
      classes_affected:
        - "TouchHandler"
    - component: "NavigationGestureHandler"
      file: "src/gtach/display/navigation_gestures.py"
      change_summary: >
        _exit_settings repointed to RADIAL; _cycle_display_mode removed
        or neutralised.
      functions_affected:
        - "_exit_settings"
        - "_cycle_display_mode"
      classes_affected:
        - "NavigationGestureHandler"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "change-378703da"
      impact: "Landed. This change completes it — the enum member it removed still had references outside its four-file scope."
    - component: "DisplayManager.change_mode — manager.py:1876"
      impact: "Called by both modules. Unmodified; it assigns the mode and saves the configuration."
    - component: "DisplayManager._initialize_legacy_components — manager.py:270-318"
      impact: "Constructs both affected classes. Unmodified."
  external: []
  required_changes:
    - change_ref: "change-378703da"
      relationship: "related"
    - change_ref: "change-3e8b1d72"
      relationship: "blocks"

testing_requirements:
  test_approach: >
    Both classes are constructed with a DisplayManager, so they are
    tested against a stub exposing config, change_mode,
    is_in_setup_mode and a logger. Gesture entry points are called
    directly. The acceptance test is behavioural rather than
    structural: a long press while in OPTIONS must leave OPTIONS.
  test_cases:
    - scenario: "TouchHandler._handle_long_press while config.mode is OPTIONS."
      expected_result: "change_mode called with RADIAL. No exception. THIS IS THE ACCEPTANCE TEST."
    - scenario: "The same against the pre-change file."
      expected_result: "AttributeError raised internally and logged; change_mode not called. The test must discriminate."
    - scenario: "_handle_long_press while config.mode is RADIAL."
      expected_result: "change_mode called with OPTIONS, unchanged from today."
    - scenario: "_handle_long_press while the disconnected condition holds."
      expected_result: "The existing early return at touch.py:161-166; no mode change."
    - scenario: "_handle_short_press with a horizontal movement beyond the old swipe threshold."
      expected_result: "No mode change, no exception."
    - scenario: "_handle_short_press while in setup mode."
      expected_result: "Routed to _handle_setup_touch, unchanged."
    - scenario: "_handle_short_press while in OPTIONS."
      expected_result: "Routed to _handle_options_touch, unchanged."
    - scenario: "_process_settings_touch with setting_id 'mode'."
      expected_result: "No branch matches; no exception; no mode change."
    - scenario: "_process_settings_touch with each of warn_decrease, warn_increase, danger_decrease, danger_increase."
      expected_result: "Unchanged behaviour, including the bounds."
    - scenario: "_process_settings_touch with setting_id 'save'."
      expected_result: "_save_config called and change_mode called with RADIAL."
    - scenario: "NavigationGestureHandler._exit_settings."
      expected_result: "change_mode called with RADIAL."
    - scenario: "_cycle_display_mode, if retained."
      expected_result: "No exception and no mode change."
    - scenario: "Repository-wide grep for DisplayMode.DIGITAL."
      expected_result: "Matches only in the two backup files, neither imported."
  regression_scope:
    - "tests/display/ — once populated per ai/task.md §8.2."
    - "On gtach.local: long press into OPTIONS and long press out again. The gauge must return."
    - "On gtach.local: a session exercising both gestures produces no 'handling error: DIGITAL' line in start.log."
    - "On gtach.local: the three options controls still act, and the DISCONNECTED screen's controls still act."
  validation_criteria:
    - "python -m py_compile on both files passes."
    - "pytest tests/ passes with no new failures."
    - "grep -rn 'DisplayMode.DIGITAL' src/gtach --include=*.py matches only manager_backup.py and setup_original_backup.py."
    - "The long-press OPTIONS exit test fails against the pre-change file and passes after."
    - "The early returns in _handle_short_press for setup and options are byte-identical."

implementation:
  implementation_steps:
    - step: "Write the acceptance test first and confirm it fails against the current file — change_mode not called, AttributeError logged."
      owner: "Claude Code"
    - step: "Repoint touch.py:171 to RADIAL. Confirm the acceptance test now passes."
      owner: "Claude Code"
    - step: "Remove the swipe branch, the settings 'mode' branch, and collapse the save ternary."
      owner: "Claude Code"
    - step: "Repoint navigation_gestures.py:474; remove or neutralise _cycle_display_mode after checking for callers."
      owner: "Claude Code"
    - step: "Repository-wide grep and the full assertion set."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; enter and leave OPTIONS by long press; confirm start.log carries no DIGITAL error."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the broken
    state, so a revert is only appropriate if the change introduces a
    worse fault than the one it fixes. No data or configuration
    involved.
  deployment_notes: >
    Restores a control the operator currently has no substitute for.
    Should ship ahead of the rest of v0.4.0 if a partial deployment is
    possible; it is independent of every other outstanding triple except
    3e8b1d72, which depends on it.

verification:
  implemented_date: "2026-08-05"
  implemented_by: "Claude Code, per prompt-7f2a9c04"
  verification_date: "2026-08-05"
  verified_by: "William Watson (gtach.local, task.md §9.10)"
  test_results: >
    On-target session 2026-08-05: one ERROR in 362 KB and no DIGITAL
    line. Source re-check 2026-08-07 confirms no live DisplayMode.
    DIGITAL reference in touch.py or navigation_gestures.py. William
    confirmed 2026-08-07 that GTach functions correctly on gtach.local.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-378703da"
      relationship: "related"
    - change_ref: "change-3e8b1d72"
      relationship: "blocks"
  related_issues:
    - issue_ref: "issue-7f2a9c04"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-7f2a9c04."
      - "Recorded the operator's decision to remove the dead mode-switching paths rather than repoint all ten references."
      - "Recorded the decision not to fold in the swipe-navigation redesign, which is change-3e8b1d72 and depends on this change."
      - "Recorded narrowing the except-Exception handlers as considered and deferred: an unhandled exception on a vehicle display's touch thread is worse than an inert gesture, and the right form is a design question."
      - "Made the success criterion a repository-wide grep rather than a list of expected sites, that discipline's absence being what caused the defect."

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
| 1.0 | 2026-08-05 | Initial change document coupled to issue-7f2a9c04. Repoints the three surviving references to RADIAL and removes the seven dead mode-switching paths, restoring the long-press exit from OPTIONS. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation and verification recorded; confirmed clean on-target and by source re-check. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
