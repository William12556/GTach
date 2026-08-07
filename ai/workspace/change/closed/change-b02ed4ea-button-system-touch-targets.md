Created: 2026 August 04

# Change: One Button Geometry Owner, Targets at 72 px, and a Confirmation Before Settings Are Cleared

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-b02ed4ea"
  title: "DisplayManager gains a button geometry helper and a button draw helper driven by TypographyConstants; the options menu is re-laid to three targets at >= 72 px with >= 16 px separation and Clear settings moves behind a confirmation view"
  date: "2026-08-04"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b02ed4ea"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b02ed4ea"
  description: >
    Resolves issue-b02ed4ea. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 findings §7.3
    and §7.4 with §9.5 recommendations 24 and 27. Task list reference
    ai/task.md §7.3.9.

scope:
  summary: >
    Two helpers in DisplayManager — one computing button rects from
    TypographyConstants and registering them with the declared touch
    expansion, one drawing a button with the declared corner radius and
    border. The four register methods and their three render methods are
    rewritten against them. The options menu drops from four targets to
    three; Clear settings moves to a confirmation sub-view.
  affected_components:
    - name: "DisplayManager._button_column"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._draw_button"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._register_options_menu_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._register_confirm_view_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._draw_confirm_view"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._register_update_view_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._register_disconnected_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._render_disconnected"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._current_view_key"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._register_view_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "TypographyConstants"
      file_path: "src/gtach/display/typography.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "TouchEventCoordinator.register_button_region and every other method of touch_coordinator.py. Unmodified — the expansion is applied by the caller so the setup subsystem's registrations are unaffected."
    - "The setup subsystem's own touch registration (display/setup.py and display/setup_components/). It owns its regions; _register_view_regions returns early while in setup mode (manager.py:1054-1055)."
    - "The acknowledgement view's full-screen region (manager.py:1136-1144). It is 480 x 480; no minimum can improve it."
    - "The RPM slider and save-button registrations at manager.py:1463 and 1519. _render_mode_selector, _register_rpm_sliders, _register_save_button and _render_slider_visuals are not reachable from any live path; they are dead code and are not corrected here. Their disposition belongs with 7.3.10 (378703da), which retires the mode machinery."
    - "The mode-entry registration mechanism introduced by 44bca479. Preserved exactly; this change adds views to it and does not alter when it fires."
    - "Display report §7.7, the circular options re-layout. Deferred to a P10 cycle per ai/task.md §7.3.15 and revisited after this change is observed."
    - "The night-palette toggle (7.3.12, 5012004e). It is a fourth control and its siting is that triple's problem, constrained by the three-item budget this change establishes."
    - "Font sizes and the font cache. Unchanged."

rational:
  problem_statement: >
    Every touch target in the main UI is below the ~9 mm comfortable
    minimum for a hand-operated panel, and the options menu compounds
    this with a 10 px (1.11 mm) separation between four items, two of
    which — Clear settings and Simulation mode — differ greatly in
    consequence. Clear settings erases the paired device with no
    confirmation. Separately, TypographyConstants declares a button
    design system that DisplayManager applies at no call site, so the
    panel shows square-cornered rectangles, the declared 8 px touch
    expansion is never applied, and button geometry is duplicated across
    four register methods.
  proposed_solution: >
    Give button geometry one owner. _button_column computes a vertical
    stack of rects from a declared minimum height and separation,
    verifies each against the circular viewport, and registers each with
    the declared touch expansion applied. _draw_button draws one with
    the declared corner radius and border width. The four register
    methods call the first; the three render methods call the second.
    The options menu is re-laid to three items and Clear settings moves
    behind a confirmation sub-view, which satisfies both halves of
    recommendation 24 with one structural change.
  alternatives_considered:
    - option: "Apply BUTTON_TOUCH_EXPANSION inside TouchEventCoordinator.register_button_region."
      reason_rejected: >
        It is the smaller edit and the more obvious place. Rejected
        because register_button_region is called by the setup subsystem
        as well as by DisplayManager, and silently enlarging every
        registered region in the application is a behaviour change well
        outside this triple's scope — setup screens have their own
        densely packed device lists where an 8 px expansion could create
        overlaps. Applying it at the caller keeps the blast radius to
        the four views named here and keeps the visual and touch rects
        visibly distinct, which is what typography.py already does at
        415-416.
    - option: "Keep four options items and reduce the separation requirement to fit."
      reason_rejected: >
        The vertical budget in issue-b02ed4ea test_data is arithmetic,
        not preference: four 72 px targets with 16 px separation need
        336 px of a 370 px usable band, leaving nothing for the title at
        y 55 or the footer at y 400. Keeping four items means either
        targets below 72 px or separation below 16 px, which is the
        finding rather than a resolution of it.
    - option: "Paginate the options menu — three items and a Next control."
      reason_rejected: >
        The Next control is itself a fourth target, so the budget
        problem returns. Pagination also adds a navigation concept the
        UI does not otherwise have, on a screen reached by long press
        and left by long press.
    - option: "Move Debug toggle off the menu instead of Clear settings."
      reason_rejected: >
        Debug is the least destructive of the four and the one most
        plausibly wanted at a moment's notice while diagnosing on the
        vehicle. Moving Clear settings instead resolves recommendation
        24's confirmation requirement in the same step, because the
        confirmation view is where it then lives. Recorded as the
        decision taken; see the note below.
    - option: "Add a confirmation view for Clear settings but leave it on the top-level menu as a fourth item."
      reason_rejected: >
        Satisfies the confirmation half of recommendation 24 and fails
        the geometry half. The two are resolved together or the screen
        stays over budget.
  benefits:
    - "Every main-UI target reaches the stated minimum, and the options menu's mis-tap risk is removed by separation and by confirmation together."
    - "The destructive control cannot be invoked by a single mis-tap."
    - "Button geometry has one owner, so a fifth view added later inherits the minimum instead of starting a fifth copy of the constants."
    - "The declared TypographyConstants values become load-bearing, so a future reader's assumption that they are in force is correct."
    - "Round-cornered controls are visually consistent with a circular panel."
  risks:
    - risk: >
        The three-item options menu is a visible behaviour change:
        Clear settings moves and acquires a step.
      mitigation: >
        Intended and recorded in the release notes for v0.4.0, where it
        travels with the other appearance-changing triples so the
        product's appearance changes once (ai/task.md §8.5).
    - risk: >
        A new DisplayMode or view key for the confirmation view could
        desynchronise _current_view_key from _register_view_regions,
        which 44bca479's design depends on being exact.
      mitigation: >
        The confirmation is a sub-view of OPTIONS, expressed through the
        existing _options_view field rather than a new DisplayMode —
        the same mechanism the update sub-view already uses.
        _options_view is already in the view key (manager.py:1032), so
        no key change is required and the mechanism is exercised.
    - risk: >
        Enlarging the touch rect beyond the visual rect can make
        adjacent regions overlap, and the coordinator resolves overlaps
        by z-order rather than by proximity.
      mitigation: >
        16 px separation against 8 px expansion on each side leaves the
        expanded rects exactly touching, not overlapping. The check is
        arithmetic and is asserted in the tests: separation must be
        >= 2 * BUTTON_TOUCH_EXPANSION.
    - risk: >
        A taller button may push a rect outside the circular viewport at
        its corners, where it is invisible but still touch-sensitive —
        the same class of fault as display §8.1's off-screen indicator.
      mitigation: >
        _button_column verifies every corner against the r=238 viewport
        and logs at ERROR if one falls outside, rather than assuming.
        The check is asserted per view in the tests.
  benefits_measurement: >
    Target height rises from 6.10 mm to >= 8.0 mm on the options menu
    and from 6.65 mm to >= 8.0 mm on the update view. Separation rises
    from 1.11 mm to >= 1.77 mm. Single-tap destructive actions fall from
    one to zero.

technical_details:
  current_behavior: >
    Geometry is hard-coded at four sites, all introduced by 44bca479:

      _register_options_menu_regions (manager.py:1087-1105) — 300 x 55
      at y 92, 157, 222, 287. Four regions.
      _register_update_view_regions (manager.py:1107-1134) — 280 x 60,
      y depending on _update_status.
      _register_acknowledgement_regions (manager.py:1136-1144) —
      480 x 480.
      _register_disconnected_regions (manager.py:1146-1179) — 240 x 70
      at y 240 and 330.

    Rects are stored on self and the render methods draw from them
    (manager.py:1203-1219 for the options menu). draw_rect is called
    without a border_radius. register_button_region
    (touch_coordinator.py:144-171) registers the rect as given.

    _on_clear_settings (manager.py:1333) is invoked directly by the
    region registered at manager.py:1102.
  proposed_behavior: >
    Geometry is computed by _button_column from constants. Registration
    applies the declared expansion. Drawing applies the declared radius
    and border. The options menu presents Bluetooth/Simulation, Debug
    and Check for updates. Clear settings is reached from the
    confirmation sub-view, which presents Clear settings and Cancel, and
    only the former invokes the existing _on_clear_settings body.
  implementation_approach: >
    Six steps in src/gtach/display/manager.py and one in
    src/gtach/display/typography.py.

    STEP 1 — typography.py. Add three constants beside the existing
    button block at typography.py:114-117, so the ergonomic minimum
    lives with the sizes it governs rather than in a review document:

        # Minimum comfortable target for a panel operated by hand in a
        # moving vehicle. 72 px = 8.0 mm at the HyperPixel 2.1 Round's
        # 229 ppi (display review §7.3, recommendation 24).
        BUTTON_MIN_TOUCH_HEIGHT = 72
        BUTTON_MIN_SEPARATION = 16
        # The circular viewport a control must lie inside.
        VIEWPORT_RADIUS = 238

    Add nothing else and change no existing constant. BUTTON_FLOATING
    stays 44 x 44: it is unused by DisplayManager and correcting it
    would alter typography.py's own button helpers, which are outside
    this scope.

    STEP 2 — _button_column. A single method computing and registering a
    centred vertical stack:

        def _button_column(self, specs, width, top, height=None,
                           separation=None) -> list

    where specs is a sequence of (region_id, action, callback) triples.
    It computes height and separation from TypographyConstants when not
    given, asserts height >= BUTTON_MIN_TOUCH_HEIGHT and separation >=
    max(BUTTON_MIN_SEPARATION, 2 * BUTTON_TOUCH_EXPANSION), builds each
    pygame.Rect centred on x=240, verifies all four corners against
    VIEWPORT_RADIUS about (240, 240) and logs at ERROR on failure,
    registers each with the rect inflated by BUTTON_TOUCH_EXPANSION on
    each axis, and returns the visual rects in order.

    The distinction between the visual rect and the registered rect is
    the whole point of the method and must not be collapsed: the render
    methods draw the returned visual rects, the coordinator holds the
    inflated ones.

    STEP 3 — _draw_button. One method drawing a visual rect with
    border_radius=BUTTON_CORNER_RADIUS and a
    BUTTON_BORDER_WIDTH outline, with the label centred on the rect
    rather than on a repeated constant. BUTTON_PRESS_SCALE is NOT
    applied: no pressed state is tracked in DisplayManager and adding
    one is a separate concern. Recorded so its absence is deliberate.

    STEP 4 — the options menu. _register_options_menu_regions calls
    _button_column with three specs and stores the returned rects.
    _draw_options_menu draws them through _draw_button. Clear settings
    is removed from this view; its callback becomes _on_clear_settings_
    requested, which sets self._options_view = 'confirm_clear'.

    STEP 5 — the confirmation view. _register_confirm_view_regions
    registers two targets through _button_column: confirm, whose
    callback is the existing _on_clear_settings, and cancel, whose
    callback returns _options_view to 'menu'. _draw_confirm_view renders
    the consequence in plain words — that the paired device is erased
    and setup will run at next start — above the two controls.
    _register_view_regions gains the 'confirm_clear' branch alongside
    the existing 'update' branch at manager.py:1074-1078, and
    _draw_options_mode (manager.py:992) gains the matching dispatch.

    STEP 6 — the remaining views. _register_update_view_regions and
    _register_disconnected_regions are rewritten against
    _button_column. Their y origins are adjusted so the taller controls
    remain inside the viewport; the update view's two-control case and
    its one-control case are both stacked from a single top value rather
    than from separate literals.

    STEP 7 — _current_view_key. No change is required, because
    _options_view is already a member (manager.py:1032). Confirm this
    explicitly rather than assuming it: the key must distinguish
    'confirm_clear' from 'menu' or the confirmation's regions will not
    be registered when the view changes.
  code_changes:
    - component: "TypographyConstants"
      file: "src/gtach/display/typography.py"
      change_summary: >
        Three constants added: BUTTON_MIN_TOUCH_HEIGHT,
        BUTTON_MIN_SEPARATION, VIEWPORT_RADIUS. No existing constant
        altered.
      classes_affected:
        - "TypographyConstants"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _button_column and _draw_button added. The options, update and
        disconnected register methods rewritten against them, and their
        render methods against _draw_button. A confirm_clear sub-view
        added to OPTIONS with its own register and draw methods, and
        wired into _register_view_regions and _draw_options_mode. Clear
        settings removed from the top-level menu.
      functions_affected:
        - "_button_column"
        - "_draw_button"
        - "_register_options_menu_regions"
        - "_draw_options_menu"
        - "_register_confirm_view_regions"
        - "_draw_confirm_view"
        - "_register_update_view_regions"
        - "_draw_update_view"
        - "_register_disconnected_regions"
        - "_render_disconnected"
        - "_register_view_regions"
        - "_draw_options_mode"
        - "_on_clear_settings_requested"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes:
    - "_options_view accepts a third value, 'confirm_clear', alongside 'menu' and 'update'. It is session state and is not persisted, so no configuration migration arises."

dependencies:
  internal:
    - component: "TouchEventCoordinator.register_button_region — touch_coordinator.py:144"
      impact: "Called with an inflated rect. Not modified; its other callers are unaffected."
    - component: "_register_view_regions — manager.py:1038, introduced by 44bca479"
      impact: "Gains one branch. The mode-entry registration mechanism is otherwise untouched, so recommendation 20 is not regressed."
    - component: "_on_clear_settings — manager.py:1333"
      impact: "Body unchanged. Its invoker moves from the menu region to the confirmation region."
    - component: "DeviceStore.remove_device — comm/device_store.py:236"
      impact: "Reached only through _on_clear_settings, so only after confirmation. Not modified."
  external:
    - "pygame.draw.rect border_radius — available in pygame 2.x, already used by typography.py:454-459."
  required_changes:
    - change_ref: "change-44bca479"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "blocks"
    - change_ref: "change-378703da"
      relationship: "related"

testing_requirements:
  test_approach: >
    Geometry and registration are pure arithmetic over pygame.Rect and a
    real TouchEventCoordinator, and are tested headlessly with
    SDL_VIDEODRIVER=dummy and a mocked rendering engine, consistent with
    the arrangement ai/task.md §8.2 describes for the DisplayManager
    target. Drawing is asserted by call inspection on the mocked engine
    rather than by pixel comparison. The confirmation behaviour is
    tested by asserting DeviceStore is not reached on the cancel path.
  test_cases:
    - scenario: "_button_column with three specs at the default height."
      expected_result: "Three rects, height 72, separation 16, all centred on x=240."
    - scenario: "_button_column asked for height below BUTTON_MIN_TOUCH_HEIGHT."
      expected_result: "Raises or clamps to the minimum — whichever the implementation states — and logs. It must not silently produce an undersized target."
    - scenario: "_button_column with a column that would leave the viewport."
      expected_result: "Logs at ERROR naming the offending region, as display §8.1's indicator did not."
    - scenario: "Every registered region across every view."
      expected_result: "Registered rect equals visual rect inflated by 8 on each side."
    - scenario: "Options menu registration."
      expected_result: "Exactly three regions; 'clear_settings' is not among them."
    - scenario: "Tapping the options Clear-settings position."
      expected_result: "No region there; nothing is invoked."
    - scenario: "_options_view set to 'confirm_clear'."
      expected_result: "_current_view_key changes, so _register_view_regions re-registers; two regions result."
    - scenario: "Cancel on the confirmation view."
      expected_result: "_options_view returns to 'menu'; DeviceStore.remove_device is not called."
    - scenario: "Confirm on the confirmation view."
      expected_result: "The existing _on_clear_settings path runs exactly as it does today."
    - scenario: "Update view in the 'available' status."
      expected_result: "Two regions, both >= 72 px, separation >= 16 px, both inside the viewport."
    - scenario: "Update view in the 'checking' status."
      expected_result: "No regions, unchanged from today."
    - scenario: "Disconnected view."
      expected_result: "Two regions, both >= 72 px, both inside the viewport."
    - scenario: "Every _draw_ call for a button."
      expected_result: "border_radius == BUTTON_CORNER_RADIUS is passed."
    - scenario: "Setup mode active."
      expected_result: "_register_view_regions still returns early; no region is cleared or registered."
    - scenario: "Acknowledgement view."
      expected_result: "Still one 480 x 480 region, not routed through _button_column."
  regression_scope:
    - "tests/display/ — the display suite once populated per ai/task.md §8.2."
    - "On gtach.local: each of the three options items invokes its own action and no other."
    - "On gtach.local: Clear settings requires two deliberate taps and the cancel path leaves the pairing intact."
    - "On gtach.local: the disconnected screen's Setup and Simulate controls still work after the transport drops."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py src/gtach/display/typography.py passes."
    - "pytest tests/ passes with no new failures."
    - "No button geometry integer literal remains in any _register_ or _draw_ method except the arguments passed to _button_column."
    - "Every registered region in the options, confirm, update and disconnected views has height >= 72."
    - "touch_coordinator.py is byte-identical to its current text."
    - "The four register methods are still called only from _register_view_regions."

implementation:
  implementation_steps:
    - step: "Add the three constants to TypographyConstants."
      owner: "Claude Code"
    - step: "Add _button_column and _draw_button."
      owner: "Claude Code"
    - step: "Rewrite the options menu to three items; add the confirm_clear sub-view and wire it into _register_view_regions and _draw_options_mode."
      owner: "Claude Code"
    - step: "Rewrite the update-view and disconnected registrations and their render methods."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Observe the three-item layout on gtach.local and record whether display report §7.7's corner-region argument survives it, per ai/task.md §7.3.15."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the four-item
    menu and the previous geometry. No configuration or data migration
    is involved; _options_view is session state.
  deployment_notes: >
    Visible change. The options menu loses one item and Clear settings
    acquires a confirmation step. Ships in v0.4.0 with the other
    appearance-changing triples per ai/task.md §8.5. Note for the
    release notes: an operator accustomed to the four-item menu will
    find Clear settings has moved.

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
    - change_ref: "change-44bca479"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "blocks"
    - change_ref: "change-378703da"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-b02ed4ea"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-b02ed4ea."
      - "Recorded the decision that Clear settings, rather than Debug, leaves the top-level options menu — it resolves recommendation 24's geometry and confirmation requirements together."
      - "Recorded that BUTTON_TOUCH_EXPANSION is applied by the caller rather than inside register_button_region, so the setup subsystem's registrations are unaffected."
      - "Recorded that BUTTON_PRESS_SCALE is deliberately not applied, no pressed state being tracked."
      - "Recorded that the confirmation is an _options_view sub-view rather than a new DisplayMode, so 44bca479's view-key mechanism needs no change."
      - "Recorded the dead mode-selector and slider registration methods as out of scope and referred their disposition to 378703da."

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
| 1.0 | 2026-08-04 | Initial change document coupled to issue-b02ed4ea. Specifies the two helpers, the three-item options menu, the Clear-settings confirmation sub-view, and the application of the declared TypographyConstants at every main-UI button site. |

---

Copyright (c) 2026 William Watson. MIT License.
