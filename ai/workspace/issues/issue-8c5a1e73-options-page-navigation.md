Created: 2026 August 05

# Issue: Clear Settings Is Unreachable, Because the Options Screen Holds Three Targets and Has Four Things to Offer

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-8c5a1e73"
  title: "The options screen offers no route to Clear settings: change-b02ed4ea moved it behind a confirmation sub-view and left it unbound, the 72 px ergonomic minimum admitting only three targets on one screen"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-8c5a1e73"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Recorded as an open decision in ai/task.md §9.7.3 before
    change-b02ed4ea was implemented, and as finding §6.4 of
    ai/workspace/report/v0.4.0-triple-implementation-session.md once it
    became live in source. Resolved by the operator on 2026-08-05, who
    proposed paging the options screen with a horizontal swipe and
    specified the page contents and wrapping behaviour. Task list
    reference ai/task.md §9.8.5 item 4.

affected_scope:
  components:
    - name: "DisplayManager._register_options_menu_regions"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._current_view_key"
      file_path: "src/gtach/display/manager.py"
    - name: "TouchHandler._handle_short_press"
      file_path: "src/gtach/display/touch.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: "Source checkout at 0.3.3, or the deployed build."
  steps:
    - "Swipe down to the options screen. Three controls are shown: Bluetooth/Simulation mode, Debug, Check for updates."
    - "Look for Clear settings. It is not there."
    - "Read manager.py:_register_options_menu_regions. Three specs are registered and self._options_btn_clear is explicitly set to None."
    - "Read manager.py:_on_clear_settings_requested (line 1675). It exists, sets _options_view to 'confirm_clear', and is bound to nothing."
    - "Read manager.py:_register_confirm_view_regions and _draw_confirm_view. The confirmation view is complete and unreachable."
    - "Confirm the constraint is arithmetic, not preference: see test_data."
  frequency: "always"
  reproducibility_conditions: "Unconditional since change-b02ed4ea landed."
  preconditions: "None."
  test_data: >
    THE VERTICAL BUDGET, from issue-b02ed4ea and unchanged.

    A 300 px wide control centred on a 480x480 circular viewport of
    radius 238 spans x 90 to 390, so its corners lie on a chord at
    |dy| = sqrt(238^2 - 150^2) = 184.7 px. Usable y is therefore 55 to
    425 — 370 px.

      three 72 px targets at 16 px separation = 3*72 + 2*16 = 248 px
      four  72 px targets at 16 px separation = 4*72 + 3*16 = 336 px

    370 - 336 = 34 px, which does not accommodate the title at y 55 and
    the footer at y 400. Three is the maximum, and that is geometry
    rather than taste.

    WHAT change-b02ed4ea DID AND WHY IT LEFT THIS OPEN. Display report
    recommendation 24 required both a >= 72 px target with >= 16 px
    separation AND a confirmation on Clear settings. Satisfying the
    first evicted a control; satisfying the second gave the evicted
    control somewhere to live. The confirmation view was built and the
    entry point deliberately left unbound, the prompt stating that
    supplying one was a scope extension to be agreed rather than an
    executor's decision.

    So the machinery exists and is complete: _on_clear_settings_requested,
    _register_confirm_view_regions, _draw_confirm_view, _on_cancel_clear
    and the untouched _on_clear_settings behind them. Only the route in
    is missing.

    THE GESTURE IS AVAILABLE. SWIPE_LEFT and SWIPE_RIGHT are detected by
    the coordinator at touch_coordinator.py:522 and consumed by nothing.
    change-7f2a9c04 removed the last consumer when it deleted the
    horizontal mode-switching that DIGITAL's retirement had made
    meaningless.

    Note that the coordinator's own dispatch is inert — see
    issue-2b6f4d91 — so this change wires the swipes the same way
    change-3e8b1d72 wired the vertical ones and change-2b6f4d91 wired
    the long press: by direct call from TouchHandler.
  error_output: "None. A control is absent, not faulty."

behavior:
  expected: >
    Every control the application implements is reachable from the user
    interface.
  actual: >
    Clear settings, its confirmation view and its cancel path are all
    implemented and none can be reached. The options screen presents
    three of the four controls it has.
  impact: >
    An operator cannot clear the paired device from the panel. The
    recovery path for a bad pairing — clear and re-pair — is
    unavailable, which matters on a device whose only input is the
    touchscreen.

    Secondarily, the confirmation view built by change-b02ed4ea is dead
    code until a route exists.
  workaround: >
    Delete the device store on the Pi over ssh. Not a workaround
    available to the operator at the wheel.

environment:
  python_version: "3.9 on target"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    Two requirements of one recommendation in tension on a fixed
    geometry. Recommendation 24 asked for larger, better separated
    targets and a confirmation on the destructive one; the circular
    viewport admits three targets; the screen had four controls. Neither
    requirement was wrong and neither could be dropped, so the control
    was moved somewhere safe and the route left for a decision.
  technical_notes: >
    THE OPERATOR'S RESOLUTION, TAKEN 2026-08-05. Page the options screen
    with a horizontal swipe:

      page 1 — Bluetooth / Simulation mode, Debug
      page 2 — Clear settings, Check for updates
      wrapping in both directions

    Two controls per page rather than three, which is inside the budget
    with room to spare and leaves the title and footer undisturbed.

    WHY PAGING RATHER THAN THE ALTERNATIVES. A fourth item on one screen
    fails the arithmetic above. A longer scrolling list introduces a
    gesture and a hit-testing problem the application does not otherwise
    have. Paging costs one piece of state, one key member and two
    gesture handlers, and it uses a gesture already detected and
    currently unused.

    THIS BEARS ON DISPLAY REPORT §7.7. That finding — the options screen
    uses a rectangular layout that wastes the circular panel's corners —
    was deferred to a P10 requirements cycle by ai/task.md §7.3.15,
    with the revisit conditioned on "after 7.3.9 is implemented and the
    three-item layout can be observed on the panel". Both conditions are
    now met, and paging is a second answer to the same space problem:
    fewer controls per screen means less vertical extent and less of the
    rectangular stacking §7.7 objects to. §7.7 may be closable after
    this change rather than deferred further. Not decided here.

    THE KEY MUST CARRY THE PAGE. _current_view_key (manager.py:1002)
    currently returns (mode, _options_view, _update_status,
    disconnected, _in_setup_mode). change-44bca479 made region
    registration fire only when that key changes. A page added without a
    corresponding key member would register page one's regions and then
    draw page two — controls in the wrong places, which is worse than
    the missing control this change exists to restore. Every prior
    change in this area has had to reason about that key; this one is
    the most exposed to it.

    DISCOVERABILITY. A gesture that pages between screens with no
    on-screen indication has the objection display report §7.6 raised
    against the horizontal swipe that change-378703da retired: nothing
    tells the operator a second page exists. A page indicator is
    therefore part of this change rather than an optional extra. It is
    non-interactive, so it does not consume a touch target.
  related_issues:
    - issue_ref: "issue-b02ed4ea"
      relationship: "blocked_by"
    - issue_ref: "issue-3e8b1d72"
      relationship: "related"
    - issue_ref: "issue-2b6f4d91"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Add a page index to the options menu, register and draw per page,
    put the page in the view key, and wire horizontal swipes from
    TouchHandler to page with wrapping. Bind Clear settings on page two
    to the existing confirmation entry point. See change-8c5a1e73.
  change_ref: "change-8c5a1e73"
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
    Where a change evicts a control to satisfy a geometric constraint,
    the eviction and the replacement route belong in the same decision.
    change-b02ed4ea was right to stop and ask rather than invent one,
    but the gap then lived in source for three sessions.
  process_improvements: >
    The view key introduced by change-44bca479 is now a standing hazard
    for every change to this screen: three separate triples have had to
    reason about it and a fourth would too. It is worth a comment on
    _current_view_key itself listing what must be added when a new
    piece of view state appears — which the method's docstring partly
    does already and should do explicitly.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on both modified files passes."
    - "The options screen shows two controls on page one: Simulation/Bluetooth and Debug."
    - "A horizontal swipe shows page two: Clear settings and Check for updates."
    - "A further swipe in the same direction returns to page one — wrapping in both directions."
    - "Clear settings on page two opens the confirmation view, not the destructive action."
    - "Cancel on the confirmation returns to the menu and leaves the pairing intact."
    - "Confirm on the confirmation runs the existing _on_clear_settings."
    - "A page indicator shows which page is displayed."
    - "Registered regions match the drawn page — the view key carries the page index."
    - "All targets remain >= 72 px with >= 16 px separation and inside the r=238 viewport."
    - "Horizontal swipes do nothing outside the options menu, including in the update and confirm sub-views."
    - "Vertical swipes still enter and leave OPTIONS; the long press still toggles the palette."
    - "Entering OPTIONS always shows page one."
    - "display/input/ is unmodified."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-8c5a1e73"
  test_refs: []

notes: >
  Raised under P04 from finding §6.4 of the v0.4.0 implementation report
  and the operator's proposal of 2026-08-05. A scope extension agreed by
  consensus; not a numbered item of either code review.

  issue_info.type is enhancement — nothing malfunctions, a control is
  absent. Severity medium because the absent control is the recovery
  path for a bad pairing on a device with no other input.

  Depends on change-b02ed4ea, which built the confirmation view this
  change supplies the route to.

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
      - "Initial issue document from report finding §6.4 and the operator's paging proposal of 2026-08-05, with page contents and wrapping as specified."
      - "Recorded that the three-target limit is arithmetic on the circular viewport rather than preference, and restated the calculation."
      - "Recorded that the whole confirmation machinery already exists and only the route in is missing."
      - "Recorded that _current_view_key must carry the page index, a page added without it registering one page's regions while drawing another's — the most exposed instance yet of the hazard change-44bca479 introduced."
      - "Recorded a page indicator as part of the change rather than optional, the discoverability objection of display §7.6 applying directly."
      - "Recorded that display report §7.7, deferred to P10 by §7.3.15, may be closable after this change: its revisit conditions are now met and paging answers the same space problem."

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
| 1.0 | 2026-08-05 | Initial issue document. Records the vertical-budget arithmetic, the complete-but-unreachable confirmation machinery, and the view-key hazard paging is most exposed to. |

---

Copyright (c) 2026 William Watson. MIT License.
