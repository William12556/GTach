Created: 2026 August 04

# Issue: Touch Targets Below Comfortable Size on a Vehicle-Mounted Panel; a Declared Button Design System That No Screen Uses

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-b02ed4ea"
  title: "Every touch target in the main UI is below the comfortable minimum for a hand-operated panel subject to vehicle motion, the four options-menu items are separated by 10 px, and TypographyConstants declares a button design system that DisplayManager does not apply at any call site"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-b02ed4ea"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Findings §7.3 (Touch Target Dimensions) and §7.4 (Declared Design
    System Not Applied), with §9.5 recommendations 24 and 27. The
    report's own numbering is preserved so coverage remains auditable
    after the report closes (ai/task.md §7.6.4). Task list reference
    ai/task.md §7.3.9.

affected_scope:
  components:
    - name: "DisplayManager._register_options_menu_regions"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._register_disconnected_regions"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._register_update_view_regions"
      file_path: "src/gtach/display/manager.py"
    - name: "TypographyConstants"
      file_path: "src/gtach/display/typography.py"
    - name: "TouchEventCoordinator.register_button_region"
      file_path: "src/gtach/display/input/touch_coordinator.py"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: >
    Source checkout at 0.3.2. The geometric findings are arithmetic on
    constants in the source and require no hardware; the ergonomic
    conclusion requires the panel.
  steps:
    - "rec 24 §7.3 — read manager.py:1089-1100. button_width 300, button_height 55, four buttons at y 92, 157, 222 and 287."
    - "rec 24 §7.3 — subtract: 157 - (92 + 55) = 10. The separation between adjacent options buttons is 10 px."
    - "rec 24 §7.3 — at 229 ppi, 1 mm = 9.02 px. 55 px = 6.10 mm; 10 px = 1.11 mm."
    - "rec 24 §7.3 — read manager.py:1148-1166. Disconnected buttons are 240 x 70 (7.76 mm) at y 240 and 330, separation 20 px."
    - "rec 24 §7.3 — read manager.py:1118-1119. Update-view buttons are 280 x 60 (6.65 mm)."
    - "rec 27 §7.4 — read typography.py:114-117. BUTTON_CORNER_RADIUS 6, BUTTON_BORDER_WIDTH 2, BUTTON_TOUCH_EXPANSION 8, BUTTON_PRESS_SCALE 0.95 are declared."
    - "rec 27 §7.4 — read manager.py:1211-1214. draw_rect is called with no border_radius argument, so the declared radius is not applied."
    - "rec 27 §7.4 — read touch_coordinator.py:144-171. register_button_region constructs TouchRegion from the rect as given; no expansion is applied."
    - "rec 27 §7.4 — grep TypographyConstants in manager.py and confirm no button constant is referenced from any register or draw method."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional. The geometry is fixed at every call site and does not
    depend on configuration, platform or runtime state.

    The consequence — an adjacent-item mis-tap — is probabilistic and
    depends on the operator, on vehicle motion and on which pair of
    items is involved. It has not been measured on the target.
  preconditions: >
    None for the arithmetic. On-panel confirmation requires gtach.local
    with the HyperPixel 2.1 Round.
  test_data: >
    Physical scale is derived from the 229 ppi figure in the Pimoroni
    specification cited by the report, giving 9.02 px/mm.

    Measured against the report's proposed minimum of 72 px (8 mm):

      options menu     55 px  =  6.10 mm   — 76% of the proposal
      update view      60 px  =  6.65 mm   — 83%
      disconnected     70 px  =  7.76 mm   — 97%
      BUTTON_FLOATING  44 px  =  4.88 mm   — 61%

    Separation, against the proposed 16 px:

      options menu     10 px  =  1.11 mm   — 63% of the proposal
      disconnected     20 px  =  2.22 mm   — meets it
      update view      80 px between install and cancel — meets it

    The options menu is therefore the only screen that fails on both
    axes, and is the screen where the consequence of a mis-tap is
    highest: Clear settings sits 10 px above Simulation mode, and the
    two are not equivalent in effect.

    VERTICAL BUDGET, since it constrains the remedy. The circular
    viewport has radius 238 about (240, 240). A 300 px wide button
    centred horizontally spans x 90 to 390, i.e. 150 px either side of
    centre, so its corners lie on a chord at |dy| = sqrt(238^2 - 150^2)
    = 184.7 px — usable y from 55 to 425, 370 px. Three 72 px buttons
    with 16 px separation occupy 3*72 + 2*16 = 248 px, leaving 122 px
    for the title and footer. Four occupy 4*72 + 3*16 = 336 px, leaving
    34 px, which does not accommodate the existing title at y 55 or the
    "Long press to return" footer at y 400. This is the arithmetic
    behind the report's "no more than three targets per screen"; it is
    a consequence of the geometry, not a preference.
  error_output: >
    None. Neither finding produces an error. A mis-tap invokes the
    adjacent control's callback, which is indistinguishable from an
    intended invocation.

behavior:
  expected: >
    Touch targets on a panel operated by hand in a moving vehicle are
    large enough and separated enough to be hit reliably, and a control
    whose effect is destructive is confirmed before it acts. A design
    system that is declared in code is applied by the code that draws
    the controls it describes.
  actual: >
    Two related findings, grouped because both are resolved by routing
    button geometry through one place.

    (a) rec 24, §7.3 — undersized and closely spaced targets. All four
    measured elements fall below the ~9 mm figure the report cites as
    the comfortable minimum for a hand-operated device, and higher again
    where the operator is subject to vehicle motion. The options menu is
    the worst case at 6.10 mm with 1.11 mm separation. Clear settings
    (manager.py:1102, calling _on_clear_settings at manager.py:1333)
    erases the paired device and returns the application to setup; it is
    adjacent to Simulation mode with a 10 px gap and has no confirmation
    step.

    (b) rec 27, §7.4 — a declared, unused design system.
    TypographyConstants (typography.py:107-123) declares five button
    sizes, a corner radius, a border width, a touch expansion and a
    press scale. typography.py itself uses them — at 415-416, 439,
    454-459, 468, 513 and 576 — but DisplayManager does not: it
    hard-codes width, height and y at each of the four register methods
    and calls draw_rect without a border_radius. The declared 8 px touch
    expansion is therefore never applied, because
    register_button_region (touch_coordinator.py:144-171) registers the
    rect exactly as passed. The result is square-cornered rectangles on
    a circular panel, geometry duplicated across four methods, and no
    press feedback in the main UI.
  impact: >
    (a) An adjacent-item mis-tap on the options menu can clear the
    paired device when the operator intended to toggle simulation mode.
    Recovery is re-pairing, which requires the setup flow and the
    adapter. This is the practical consequence and the reason the
    finding is not purely cosmetic.

    (b) Maintenance. Four copies of button geometry drift independently;
    a fifth screen added later starts a fifth copy. The unused constants
    are worse than absent, because a reader reasonably assumes they are
    in force.
  workaround: >
    (a) None. The operator can tap carefully. There is no confirmation
    to catch the error and no undo.

    (b) Not applicable; nothing is broken at runtime.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    (a) Geometry chosen for legibility and vertical fit rather than
    against a stated ergonomic minimum. No minimum was recorded
    anywhere, so nothing flagged the 55 px height or the 10 px gap as
    below one.

    (b) The design system was declared in typography.py and adopted by
    typography.py's own button helpers, but DisplayManager was written
    against pygame primitives directly and never routed through them.
    The two halves were never connected, and because the constants are
    used somewhere, a grep for them does not reveal that the main UI
    ignores them.
  technical_notes: >
    DEPENDENCY ON 7.3.8, NOW DISCHARGED IN SUBSTANCE.
    ai/workspace/report/task-list-cross-check-discrepancies.md §8.0
    records discrepancy D4: recommendation 20 (task 7.3.8, 44bca479)
    relocates touch registration out of the render path into a
    mode-entry hook, and authoring 7.3.9 first would produce
    registration code that 7.3.8 then has to move. D4 was discharged by
    ordering — and the ordering has now been honoured. 44bca479 is
    implemented: _register_view_regions (manager.py:1038) is called from
    _display_loop (manager.py:435-444) only when _current_view_key()
    changes, and the four per-view register methods
    (manager.py:1087, 1107, 1136, 1146) own the geometry, which the
    render methods then draw from (manager.py:1203-1219).

    This changes what this triple has to do. The report's §7.4 remedy
    "route all button drawing through a single helper" must be read
    against the current structure, in which registration and drawing are
    already separated and the geometry already has a single owner per
    view. The helper this triple adds is therefore a *geometry* helper
    used by the register methods, plus a *draw* helper used by the
    render methods, not a single function that does both — doing both
    would reintroduce registration into the render path and undo
    44bca479.

    THREE CORRECTIONS TO THE SOURCE REPORT.

    (1) §7.3's table cites the options menu at "manager.py:911-921" and
    the disconnected buttons at "manager.py:1345-1346". Neither holds at
    0.3.2: 44bca479 moved the geometry into the register methods. The
    options geometry is at manager.py:1089-1100, disconnected at
    manager.py:1148-1166, update view at manager.py:1118-1119. The
    values the report quotes are all correct; only the locations moved.

    (2) §7.4 states "TouchEventCoordinator.register_button_region() takes
    the drawn rectangle unmodified, so the declared 8 px touch expansion
    is not applied either". This is accurate, and worth stating
    precisely: the expansion cannot be applied inside
    register_button_region without changing behaviour for every existing
    caller, including the setup subsystem's own registrations, which are
    outside this triple's scope. The expansion is therefore applied by
    the caller, at the four DisplayManager register methods, by
    inflating the rect before registration — which also keeps the
    visual rect and the touch rect distinguishable, as typography.py
    already does at 415-416.

    (3) §7.3's "reduce to three items per screen" is stated as a
    proposal without its justification. The justification is the
    vertical budget computed under test_data: four 72 px targets with
    16 px separation do not fit between the title and the footer inside
    the circular viewport. Recorded so the constraint is not mistaken
    for a stylistic preference and quietly relaxed later.

    OPEN DECISION — WHICH FOURTH ITEM LEAVES THE MENU. The options menu
    currently carries four controls: Clear settings, Bluetooth /
    Simulation mode, Debug toggle, Check for updates. Three must remain
    at most. This is a product decision, not a technical one, and it is
    recorded in change-b02ed4ea under alternatives_considered with a
    recommendation rather than being settled here. The recommendation is
    that Clear settings leaves the top-level menu and is reached from
    the confirmation flow that rec 24 requires for it in any case,
    which resolves both halves of the recommendation with one structural
    change. Confirm before the change document is approved.
  related_issues:
    - issue_ref: "issue-44bca479"
      relationship: "blocked_by"
    - issue_ref: "issue-5012004e"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Introduce a button geometry helper and a button draw helper in
    DisplayManager, both driven by TypographyConstants. Re-lay the
    options menu to three items at height >= 72 px and separation
    >= 16 px, moving Clear settings behind a confirmation sub-view.
    Bring the disconnected and update-view buttons to the same minimum.
    Apply corner radius, border and touch expansion from the declared
    constants at every site. See change-b02ed4ea.
  change_ref: "change-b02ed4ea"
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
    An ergonomic minimum that exists only in a reviewer's head cannot be
    enforced. Recording it as a named constant next to the sizes it
    governs makes a future violation visible at the point it is written.

    A design system is only in force where it is called. Declaring
    constants and using them in one module while another draws the same
    class of control by hand is worse than not declaring them, because
    it defeats the grep that would otherwise find the problem.
  process_improvements: >
    The vertical budget arithmetic under test_data should be repeated
    whenever a screen gains a control, because the circular viewport
    makes the available height depend on the control's width. That is
    not obvious and will not be rediscovered.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "Every button rect registered by the four DisplayManager register methods has height >= 72."
    - "Adjacent registered rects within a view are separated by >= 16 px."
    - "The options menu registers exactly three regions."
    - "Clear settings is not reachable in one tap from the options menu; it requires the confirmation step."
    - "The confirmation view registers a confirm and a cancel region, both >= 72 px, separated by >= 16 px."
    - "Cancelling the confirmation leaves the paired device intact — DeviceStore is not called."
    - "Confirming the confirmation calls the same code path _on_clear_settings calls today."
    - "Every registered touch rect is the visual rect inflated by BUTTON_TOUCH_EXPANSION on each axis."
    - "Every button drawn in the options, update and disconnected views is drawn with border_radius == BUTTON_CORNER_RADIUS."
    - "No button geometry literal remains in any _draw_ method; the render methods read the rects the register methods stored."
    - "All button rects lie within the circular viewport: for each corner, (x-240)^2 + (y-240)^2 <= 238^2."
    - "touch_coordinator.py register_button_region is unmodified, so the setup subsystem's registrations are unaffected."
    - "Touch registration remains outside the render path — _register_view_regions is still the only caller of the register methods, per 44bca479."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-b02ed4ea"
  test_refs: []

notes: >
  This is task 7.3.9 in ai/task.md §7.3 and step 9 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5), grouped with the
  other user-interface triples so the product's appearance changes once
  rather than incrementally.

  issue_info.type is enhancement per ai/task.md §7.2: both §7.3 and §7.4
  are display §7.x user interface proposals. Neither is a defect — the
  code does what it was written to do. Severity is medium rather than
  low because the Clear settings adjacency has a destructive outcome and
  no confirmation.

  ai/task.md §7.6.1 records two relationships. 7.3.9 is blocked by 7.3.8
  (44bca479), which has shipped — see technical_notes. 7.3.9 precedes
  7.3.12 (5012004e) if the night-palette toggle is placed on the options
  screen; that toggle would be a fourth control, so §7.3.15's note about
  the three-item layout applies to it directly and 5012004e must site it
  elsewhere or displace an existing item.

  ai/task.md §7.3.15 defers display report §7.7 (circular options
  layout) to a future P10 cycle, to be revisited after this triple is
  implemented and the three-item layout can be observed on the panel.
  That revisit is a condition of closing the display report; it is not
  in this triple's scope.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial issue document from display-ui-graphics-review.md findings §7.3 and §7.4 with §9.5 recommendations 24 and 27."
      - "Recorded three corrections to the source report: the cited line numbers predate 44bca479 and the geometry now lives in the register methods; the 8 px touch expansion must be applied by the caller rather than inside register_button_region, to avoid changing behaviour for the setup subsystem; and the 'three items per screen' proposal is a consequence of the circular viewport's vertical budget, computed inline."
      - "Recorded that D4's dependency on 7.3.8 is discharged in substance, and what that changes: the §7.4 'single helper' becomes a geometry helper plus a draw helper, so registration is not reintroduced into the render path."
      - "Recorded the disposition of the fourth options item as an open decision with a recommendation, for confirmation before the change document is approved."

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
| 1.0 | 2026-08-04 | Initial issue document from display review findings §7.3 and §7.4 with recommendations 24 and 27. Records three corrections to the source report, the vertical-budget arithmetic behind the three-item constraint, the discharged D4 dependency on 44bca479 and its consequence for the helper design, and the open decision on which fourth options item leaves the menu. |

---

Copyright (c) 2026 William Watson. MIT License.
