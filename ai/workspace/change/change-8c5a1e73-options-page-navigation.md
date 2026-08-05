Created: 2026 August 05

# Change: Two Pages, Wrapping, and Clear Settings Reachable Again

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-8c5a1e73"
  title: "The options menu gains a page index carried in the view key, two controls per page, a page indicator, and wrapping horizontal-swipe navigation wired from TouchHandler; Clear settings is bound on page two to the confirmation entry point change-b02ed4ea left unused"
  date: "2026-08-05"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-8c5a1e73"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-8c5a1e73"
  description: >
    Resolves issue-8c5a1e73. Raised under P04 from finding §6.4 of
    ai/workspace/report/v0.4.0-triple-implementation-session.md and the
    operator's proposal of 2026-08-05, which specified the page contents
    and wrapping. Task list reference ai/task.md §9.8.5 item 4.

scope:
  summary: >
    A page index on the options menu, two controls per page instead of
    three, a non-interactive page indicator, and horizontal swipes wired
    by direct call from TouchHandler. Clear settings returns to the user
    interface behind the confirmation already built for it.
  affected_components:
    - name: "DisplayManager._options_page"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._handle_swipe_left"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._handle_swipe_right"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._current_view_key"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._register_options_menu_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._handle_swipe_down"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "TouchHandler._handle_short_press"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/display/input/. Not modified. The coordinator's gesture dispatch is inert (issue-2b6f4d91); these swipes are wired by direct call as the vertical ones and the long press are."
    - "_on_clear_settings, _on_clear_settings_requested, _on_cancel_clear, _register_confirm_view_regions and _draw_confirm_view. All built by change-b02ed4ea, all correct, all unmodified. This change supplies the route in and nothing else."
    - "_button_column and _draw_button. The geometry helpers are unchanged; only what is passed to them changes."
    - "The update sub-view and the confirm sub-view. Paging applies to the menu only."
    - "The three-target maximum. Two per page is inside it; the constraint is not relaxed."
    - "Display report §7.7's circular re-layout. This change may make it closable — see issue-8c5a1e73 technical_notes — but does not close it."

rational:
  problem_statement: >
    Clear settings, its confirmation view and its cancel path are
    implemented and unreachable. change-b02ed4ea evicted the control to
    meet recommendation 24's 72 px minimum, built the confirmation it
    also required, and left the entry point unbound because supplying
    one was a scope decision.
  proposed_solution: >
    Two pages of two controls, navigated by wrapping horizontal swipe,
    with the page carried in the view key and shown by an indicator.
  alternatives_considered:
    - option: "Put a fourth control back on one screen."
      reason_rejected: >
        Fails the arithmetic: four 72 px targets at 16 px separation
        need 336 px of a 370 px usable band, leaving nothing for the
        title at y 55 or the footer at y 400. That is the finding
        change-b02ed4ea exists to fix."
    - option: "A scrolling list."
      reason_rejected: >
        Introduces momentum, hit-testing during scroll, and a scroll
        indicator — a gesture vocabulary the application does not
        otherwise have, on a screen with four items."
    - option: "Reach Clear settings from the DISCONNECTED screen instead."
      reason_rejected: >
        Plausible, since that is when clearing a bad pairing is most
        wanted. Rejected because it hides a destructive control on a
        screen the operator reaches by fault rather than by choice, and
        because it leaves the options menu inconsistent — three controls
        with a fourth elsewhere."
    - option: "Vertical swipe to page, matching the enter/leave gesture."
      reason_rejected: >
        Collides directly: vertical swipes enter and leave OPTIONS
        (change-3e8b1d72). Horizontal is free and orthogonal."
    - option: "Three pages of one or two, leaving room to grow."
      reason_rejected: >
        Premature. Four controls fit two pages with a spare slot on
        each; a third page adds a swipe for nothing."
  benefits:
    - "Clear settings is reachable, and the confirmation view built for it stops being dead code."
    - "Two controls per page rather than three leaves margin inside the vertical budget for a fifth control later."
    - "Uses a gesture that is detected and currently consumed by nothing."
    - "May close display report §7.7 rather than deferring it further."
  risks:
    - risk: >
        The view key omits the page, so regions are registered for one
        page and drawn for another — controls in the wrong places.
      mitigation: >
        The page index is added to _current_view_key in the same edit,
        and the tests assert that registered region identifiers match
        the drawn page for both pages. This is the change's principal
        correctness risk and its principal test."
    - risk: >
        A horizontal swipe is taken for a vertical one or vice versa,
        so paging leaves OPTIONS or leaving OPTIONS pages.
      mitigation: >
        TouchHandler compares abs(dx) with abs(dy) and dispatches to the
        larger axis, testing both before the OPTIONS early return.
        Asserted for a diagonal in both dominant directions."
    - risk: >
        Nothing tells the operator a second page exists — the objection
        display §7.6 raised against the swipe that change-378703da
        retired.
      mitigation: >
        A two-dot page indicator is part of this change, not an
        optional extra. Non-interactive, so it consumes no touch
        target."
    - risk: >
        Clear settings is bound directly to _on_clear_settings rather
        than to the confirmation entry point, restoring the one-tap
        destructive action recommendation 24 exists to prevent.
      mitigation: >
        Page two binds _on_clear_settings_requested. A success criterion
        asserts that _on_clear_settings is not reachable from any menu
        region, and a test asserts DeviceStore is untouched on the
        cancel path."
    - risk: >
        A stale page index persists across a visit, so the operator
        returns to OPTIONS on page two unexpectedly.
      mitigation: >
        _handle_swipe_down resets the page to zero on entry, alongside
        the _options_view reset it already performs."
  benefits_measurement: >
    Controls implemented but unreachable: 1 -> 0. Dead views: 1 -> 0.
    Controls per options screen: 3 -> 2, against a maximum of 3.

technical_details:
  current_behavior: >
    _register_options_menu_regions registers three specs —
    simulation_mode, debug_toggle, check_updates — via _button_column at
    width 300, top 110, and sets _options_btn_clear to None.
    _draw_options_menu iterates the three stored rects.
    _current_view_key returns (mode, _options_view, _update_status,
    disconnected, _in_setup_mode). _on_clear_settings_requested exists at
    manager.py:1675 and is bound to nothing. Horizontal swipes are
    detected by the coordinator and consumed by nothing;
    TouchHandler._handle_short_press tests dy only.
  proposed_behavior: >
    The menu holds two pages of two controls. A horizontal swipe pages
    with wrapping. The page appears in the view key so registration
    follows it, and in an indicator so the operator can see it.
  implementation_approach: >
    SIX EDITS.

    1. State. self._options_page = 0 in __init__.

    2. The key. _current_view_key gains self._options_page. This is the
       edit that must not be forgotten; everything else is inert
       without it.

    3. Registration. _register_options_menu_regions selects its specs by
       page:

         page 0 — simulation_mode  -> _on_simulation_mode
                  debug_toggle     -> _on_debug_toggle
         page 1 — clear_settings   -> _on_clear_settings_requested
                  check_updates    -> _on_check_updates

       Two specs through _button_column at width 300, top 140 — two
       72 px targets separated by 16 px span 140 to 300, comfortably
       inside the 55-425 band and leaving room for the indicator below.

       Rects for controls not on the current page are set to None, as
       the method already does for _options_btn_clear, so a stale
       reference is a visible None rather than a rect from the other
       page.

    4. Drawing. _draw_options_menu draws the current page's two controls
       and a page indicator: two dots at y 350, 20 px apart, the active
       one filled in the palette's tick colour and the inactive one
       outlined. Read the palette once, as _draw_radial_mode does.

    5. Paging handlers. _handle_swipe_left and _handle_swipe_right on
       DisplayManager. Both return NONE unless the mode is OPTIONS, the
       sub-view is 'menu' and setup mode is inactive. Otherwise they
       move the page by +1 or -1 modulo the page count and return
       NAVIGATION. Modulo gives wrapping in both directions, as
       specified.

    6. Delivery. TouchHandler._handle_short_press gains a horizontal
       test alongside the vertical one it already has, dispatching to
       whichever axis dominates. Both must be tested BEFORE the OPTIONS
       early return, for the reason change-3e8b1d72 recorded: that
       return sends every short press in OPTIONS to
       _handle_options_touch, so a swipe tested after it would never
       page.

    Page entry. _handle_swipe_down sets self._options_page = 0 alongside
    its existing _options_view reset.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _options_page added and carried in the view key; menu
        registration and drawing become per-page; page indicator added;
        _handle_swipe_left and _handle_swipe_right added; page reset on
        entry.
      functions_affected:
        - "__init__"
        - "_current_view_key"
        - "_register_options_menu_regions"
        - "_draw_options_menu"
        - "_handle_swipe_left"
        - "_handle_swipe_right"
        - "_handle_swipe_down"
      classes_affected:
        - "DisplayManager"
    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: >
        _handle_short_press dispatches horizontal swipes to the paging
        handlers, choosing the dominant axis.
      functions_affected:
        - "_handle_short_press"
      classes_affected:
        - "TouchHandler"
  data_changes: []
  interface_changes:
    - "The options screen gains a second page. Visible to the operator and the point of the change; the page indicator makes it discoverable."

dependencies:
  internal:
    - component: "change-b02ed4ea"
      impact: "PREREQUISITE, landed. Built _button_column, the three-target budget and the entire confirmation view this change supplies the route to."
    - component: "change-3e8b1d72"
      impact: "Established the direct-call delivery pattern and the early-return ordering constraint in _handle_short_press. Its vertical swipes must keep working."
    - component: "change-2b6f4d91"
      impact: "Wired the long press the same way. Its palette toggle must keep working."
    - component: "change-44bca479"
      impact: "Introduced the view key that registration follows. Not modified; the page is added to it."
    - component: "change-5012004e"
      impact: "Supplies the palette the indicator reads its colours from."
  external: []
  required_changes:
    - change_ref: "change-b02ed4ea"
      relationship: "blocked_by"
    - change_ref: "change-3e8b1d72"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with a stubbed rendering engine and a real
    TouchEventCoordinator, so registration is exercised rather than
    mocked. The principal assertion is that the registered region set
    matches the drawn page for both pages — the failure the view key
    exists to prevent.
  test_cases:
    - scenario: "_current_view_key with _options_page 0 and then 1."
      expected_result: "The two keys differ. THE PRINCIPAL TEST — everything else is inert if this fails."
    - scenario: "_register_options_menu_regions with _options_page 0."
      expected_result: "Exactly simulation_mode and debug_toggle registered; clear_settings and check_updates absent."
    - scenario: "The same with _options_page 1."
      expected_result: "Exactly clear_settings and check_updates registered; the other two absent."
    - scenario: "The rects stored for controls not on the current page."
      expected_result: "None in both directions."
    - scenario: "_handle_swipe_left from page 0, then from page 1."
      expected_result: "Page 1, then page 0 — wrapping."
    - scenario: "_handle_swipe_right from page 0, then from page 1."
      expected_result: "Page 1, then page 0 — wrapping the other way."
    - scenario: "Either handler with the mode not OPTIONS, with _options_view 'update', with 'confirm_clear', and with _in_setup_mode True."
      expected_result: "No page change and NONE returned, in all four."
    - scenario: "The clear_settings region's callback on page 1."
      expected_result: "_on_clear_settings_requested — _options_view becomes 'confirm_clear'; DeviceStore is not called."
    - scenario: "Cancel on the confirmation view."
      expected_result: "Back to the menu; DeviceStore untouched."
    - scenario: "Confirm on the confirmation view."
      expected_result: "The existing _on_clear_settings runs."
    - scenario: "grep for a menu region bound directly to _on_clear_settings."
      expected_result: "None — the destructive action is reachable only through the confirmation."
    - scenario: "Every rect on both pages, all four corners."
      expected_result: "Inside r=238 about (240, 240); height >= 72; separation >= 16."
    - scenario: "TouchHandler._handle_short_press with dx 150 and dy 10, mode OPTIONS."
      expected_result: "Pages. The horizontal axis dominates."
    - scenario: "The same with dx 10 and dy 150."
      expected_result: "Leaves OPTIONS. The vertical axis dominates."
    - scenario: "A diagonal with dx 120 and dy 100."
      expected_result: "Pages — dominant axis wins, and the test states which."
    - scenario: "TouchHandler._handle_short_press with a small dx and dy inside OPTIONS."
      expected_result: "Routed to _handle_options_touch; a tap on a button still works."
    - scenario: "Horizontal swipe in RADIAL."
      expected_result: "Nothing; no exception."
    - scenario: "_handle_swipe_down into OPTIONS with _options_page previously 1."
      expected_result: "Page 0."
    - scenario: "Vertical swipes and the long-press palette toggle after the change."
      expected_result: "Unchanged behaviour."
    - scenario: "The page indicator."
      expected_result: "Two dots drawn; the filled one matches _options_page."
  regression_scope:
    - "tests/display/ — once populated per ai/task.md §8.2."
    - "On gtach.local: swipe down, page across, and confirm each of the four controls acts."
    - "On gtach.local: Clear settings opens the confirmation and cancel leaves the pairing intact."
    - "On gtach.local: swipe up still leaves OPTIONS from either page."
    - "On gtach.local: long press still toggles the palette."
    - "On gtach.local: observe whether the two-item pages weaken display report §7.7's corner-region argument (ai/task.md §7.3.15)."
  validation_criteria:
    - "python -m py_compile on both files passes."
    - "pytest tests/ passes with no new failures."
    - "_current_view_key includes _options_page."
    - "No menu region is bound directly to _on_clear_settings."
    - "All targets on both pages are >= 72 px, separated by >= 16 px, inside the viewport."
    - "display/input/ is byte-identical."
    - "The confirmation view methods are byte-identical."

implementation:
  implementation_steps:
    - step: "Add _options_page and put it in _current_view_key FIRST, with the key test passing, before any registration change."
      owner: "Claude Code"
    - step: "Make registration and drawing per-page; set off-page rects to None."
      owner: "Claude Code"
    - step: "Add the page indicator."
      owner: "Claude Code"
    - step: "Add the two paging handlers with wrapping and the mode/sub-view gating."
      owner: "Claude Code"
    - step: "Wire horizontal swipes in TouchHandler, before the OPTIONS early return, dispatching to the dominant axis."
      owner: "Claude Code"
    - step: "Reset the page on entry in _handle_swipe_down."
      owner: "Claude Code"
    - step: "Compile checks and the assertion set, including the registered-matches-drawn assertion for both pages."
      owner: "Claude Code"
    - step: "Deploy; page both ways; exercise all four controls; confirm cancel leaves the pairing intact. Then judge whether §7.7 is closable."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the three-item
    single page and makes Clear settings unreachable again. No
    persisted state is involved — _options_page is session state and is
    not written to configuration.
  deployment_notes: >
    Visible change. The options screen loses a control to page two and
    gains a page indicator; Clear settings returns after three sessions
    absent. Release notes should say where it went.

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
    - change_ref: "change-b02ed4ea"
      relationship: "blocked_by"
    - change_ref: "change-3e8b1d72"
      relationship: "related"
    - change_ref: "change-2b6f4d91"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-8c5a1e73"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-8c5a1e73, implementing the operator's specification of 2026-08-05: two pages, the stated contents, wrapping."
      - "Recorded the view-key edit as the change's principal correctness risk and made it the first implementation step, a page without a key member registering one page and drawing another."
      - "Recorded that the horizontal test must precede the OPTIONS early return in _handle_short_press, for the reason change-3e8b1d72 recorded about the vertical one."
      - "Recorded the page indicator as part of the change rather than optional, display §7.6's discoverability objection applying directly."
      - "Recorded that Clear settings binds to _on_clear_settings_requested and never to _on_clear_settings, with a success criterion asserting it."
      - "Recorded two controls per page rather than three as leaving margin within the budget for a fifth control later."

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
| 1.0 | 2026-08-05 | Initial change document coupled to issue-8c5a1e73. Two pages of two controls, wrapping horizontal swipe wired from TouchHandler, page carried in the view key, and Clear settings restored behind its confirmation. |

---

Copyright (c) 2026 William Watson. MIT License.
