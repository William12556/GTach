# Change: Gauge Status Symbols

Created: 2026 November 20

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-adb3afeb"
  title: "Show Engine off and DISCONNECTED as symbols on the gauge; DISCONNECTED details on a tap-opened panel; remove the OPTIONS title"
  date: "2026-11-20"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-adb3afeb"
    issue_iteration: 1
    prompt_ref: "prompt-adb3afeb"

source:
  type: "issue"
  reference: "issue-adb3afeb"
  description: "Implements design-b8c9d0e1 v2.1 (commit f6427b3)."

scope:
  summary: >
    models.py gains two palette colours; manager.py draws a dimmed gauge
    with an information symbol for DISCONNECTED, opens the existing
    DISCONNECTED screen as a panel on tap, draws an ignition-key symbol for
    Engine off, and drops the OPTIONS title; tests updated and added.
  affected_components:
    - name: "Palette, DAY_PALETTE, NIGHT_PALETTE"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_gauge_status_symbols.py (new); tests/test_engine_off_state.py, tests/test_disconnected_screen.py (assertions on replaced behaviour)"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-b8c9d0e1-component_display_manager"
      sections:
        - "3.0, 4.0, 5.2, 5.3, 5.4, 5.5, 5.7, 6.0, 8.0"
  out_of_scope:
    - "_link_lost(), _engine_off(), their constants and precedence: unchanged."
    - "_render_disconnected() content and layout (title, message, cause line, Setup, Reset, spinner): unchanged; it becomes the panel."
    - "_draw_reconnect_spinner(): unchanged."
    - "The acknowledgement screen, the OPTIONS button layout and paging, the setup screens."
    - "A night variant of the black-on-yellow panel."
    - "Swipe gestures and their handlers, except as stated in EDIT B6."

rational:
  problem_statement: "See issue-adb3afeb."
  proposed_solution: "As technical_details.implementation_approach."
  alternatives_considered:
    - option: "Image assets for the symbols"
      reason_rejected: "Adds files and a load path; primitives scale and follow the palette (design section 5.7)."
    - option: "Engine symbol with a prohibition overlay for Engine off"
      reason_rejected: "Reads as the check-engine fault lamp."
    - option: "Blue information symbol"
      reason_rejected: "Blue conventionally means neutral information; DISCONNECTED is a fault state, so amber."
  benefits:
    - "The gauge stays on screen in every RADIAL condition."
    - "Status is readable at a glance without text."
  risks:
    - risk: "The dimmed gauge could be mistaken for a live 0 RPM gauge."
      mitigation: "No fill, no readout, grey face, amber symbol, red status dot."
    - risk: "The full-screen close region may change how a swipe that starts on the open panel is handled."
      mitigation: "Verify and report (prompt); the panel is optional and closes on link recovery."
    - risk: "Grey key contrast on the night band-0 disc (estimated 4.5:1)."
      mitigation: "On-device check after merge; colours are palette data."

technical_details:
  current_behavior: >
    Engine off draws ENGINE_OFF_TEXT in the centre disc. DISCONNECTED
    replaces the gauge with _render_disconnected() and registers Setup and
    Reset. OPTIONS draws the title 'Options' at (240, 100).
  proposed_behavior: "design-b8c9d0e1 v2.1 sections 5.3, 5.4, 5.5, 5.7, 6.0."
  implementation_approach: >
    EDIT A (models.py): add fields symbol and alert (Tuple[int, int, int])
    to Palette after band_centres. DAY_PALETTE: symbol (150, 150, 150),
    alert (230, 160, 0). NIGHT_PALETTE: symbol (120, 120, 120),
    alert (150, 105, 0).

    EDIT B (manager.py):
    B1. Class constant ICON_TOUCH_SIZE = 144. ENGINE_OFF_TEXT stays.
    B2. Attribute _disconnected_details_open = False, initialised early in
        __init__ beside _frame_engine_off.
    B3. One helper _disconnected_view() -> bool returning
        _frame_link_lost and not _frame_engine_off and mode == RADIAL,
        used at every site that now spells out that condition
        (_render_normal_modes, _register_view_regions). In the frame loop,
        directly after _set_frame_engine_off, clear
        _disconnected_details_open when _disconnected_view() is false.
    B4. _current_view_key(): add _disconnected_details_open after the
        disconnected member; update its docstring.
    B5. _render_normal_modes(): in the disconnected view, if the panel is
        open call _render_disconnected() and return (as now); otherwise
        call _draw_radial_mode() and then _draw_status_indicator().
    B6. _register_view_regions(): in the disconnected view, if the panel is
        open register a full-screen region 'disconnected_close' (rect
        0, 0, 480, 480; callback clears the flag) FIRST, then call
        _register_disconnected_regions() unchanged, so the buttons are
        above it in z-order. If the panel is closed register only
        'disconnected_info': a centred ICON_TOUCH_SIZE square on (240, 240),
        action NAVIGATION, callback sets the flag. A hold on it presses it
        (existing button behaviour), so it does not toggle the palette.
    B7. _draw_radial_mode(): compute disconnected = _disconnected_view().
        When true: rpm 0; no fill arc, no indicator line, no readout; tick
        marks, numerals, band boundary marks and the 'RPM x 1000' label in
        palette.line; centre disc in palette.track; then
        _draw_info_symbol(). When engine off: replace the ENGINE_OFF_TEXT
        block with _draw_key_symbol(); move the text block, unchanged in
        behaviour, into a retained method _draw_engine_off_text(center)
        that is not called, with a comment saying it is kept for later use.
        Live drawing is unchanged.
    B8. _draw_info_symbol(surface, palette): filled disc r 40 at (240, 240)
        in palette.alert; dot: filled circle r 5 at (240, 222), black;
        bar: filled rect x 236-244, y 232-258, black.
    B9. _draw_key_symbol(surface, palette): palette.symbol, line width 6:
        bow ring centre (222, 240) r 18; shaft (240, 240)-(276, 240);
        teeth (264, 240)-(264, 252) and (274, 240)-(274, 252).
        Horizontal extent 204-276, centred on x 240.
    B10. _draw_options_menu(): remove the 'Options' title block. Nothing
         else in the menu moves.
  code_changes:
    - component: "Palette"
      file: "src/gtach/display/models.py"
      change_summary: "EDIT A"
      functions_affected: []
      classes_affected:
        - "Palette"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "EDIT B1-B10"
      functions_affected:
        - "__init__"
        - "_current_view_key"
        - "_register_view_regions"
        - "_render_normal_modes"
        - "_draw_radial_mode"
        - "_draw_options_menu"
        - "_disconnected_view (new)"
        - "_draw_info_symbol (new)"
        - "_draw_key_symbol (new)"
        - "_draw_engine_off_text (new, retained, not called)"
      classes_affected:
        - "DisplayManager"
  data_changes:
    - entity: "Palette"
      change_type: "schema"
      details: "Two new required fields; both instances updated. Palette is frozen and built by keyword only."
  interface_changes:
    - interface: "DisplayManager touch regions"
      change_type: "contract"
      details: "Disconnected view registers 'disconnected_info' (panel closed) or 'disconnected_close' + existing buttons (panel open)."
      backward_compatible: "n/a"

dependencies:
  internal:
    - component: "TouchEventCoordinator"
      impact: "None; relies on existing reverse z-order hit testing."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests with stubbed rendering, as in tests/test_engine_off_state.py and tests/test_disconnected_screen.py; SDL_VIDEODRIVER=dummy."
  test_cases:
    - scenario: "Disconnected, panel closed"
      expected_result: "Only 'disconnected_info' registered; _render_disconnected not called; no readout text; info symbol drawn."
    - scenario: "Tap on 'disconnected_info'"
      expected_result: "Flag set; view key changes; 'disconnected_close', 'disconnected_setup' (and 'disconnected_reset' when set) registered, buttons above close in z-order; _render_disconnected called."
    - scenario: "Tap on 'disconnected_close'"
      expected_result: "Flag cleared; dimmed gauge again."
    - scenario: "Link recovers or Engine off begins while the panel is open"
      expected_result: "Flag cleared in the same frame."
    - scenario: "Swipe down while the panel is open"
      expected_result: "OPTIONS entered and flag cleared, or panel closed; report which."
    - scenario: "Engine off"
      expected_result: "Key symbol drawn; ENGINE_OFF_TEXT not drawn; no regions registered."
    - scenario: "Live link"
      expected_result: "Gauge drawn as before; neither symbol drawn."
    - scenario: "OPTIONS menu"
      expected_result: "No 'Options' text; buttons and page indicator unchanged."
    - scenario: "Both palettes"
      expected_result: "symbol and alert present; values as EDIT A."
  regression_scope:
    - "tests/"
  validation_criteria:
    - "pytest tests/ passes."
    - "mypy src/ reports no new issues."

implementation:
  effort_estimate: "Hours"
  implementation_steps:
    - step: "Claude Code cloud session executes prompt-adb3afeb on a claude/* branch and opens a pull request."
      owner: "Claude Code"
    - step: "Planner code review; William merges in the GitHub iOS app."
      owner: "Planner / William"
    - step: "Pull to the Mac clone, deploy to gtach.local, device check."
      owner: "Planner / William"
  rollback_procedure: "git revert of the merge commit."
  deployment_notes: "bin/deploy.sh from the Mac clone after merge."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates:
    - design_ref: "design-b8c9d0e1-component_display_manager"
      sections_updated:
        - "v2.1"
      update_date: "2026-11-19"
  related_changes:
    - change_ref: "change-b29cbd71"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-adb3afeb"
      relationship: "source"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-11-20"
    author: "William Watson"
    changes:
      - "Initial change."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-20 | Initial change |

---

Copyright (c) 2026 William Watson. MIT License.
