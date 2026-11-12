# Change: Gauge Display and Touch Corrections

Created: 2026 November 11

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-2550e4ee"
  title: "Assign display attributes before fallible initialisation; local copies of the setup manager; long press requires a touch at rest; bounded touch-start age; one link evaluation per frame; documentation, font and default corrections"
  date: "2026-11-11"
  author: "William Watson"
  status: "implemented"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-2550e4ee"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-2550e4ee"
  description: "Resolves issue-2550e4ee. Run 5 of proposal-71ab3751."

scope:
  summary: "Five edit groups in display/manager.py, touch.py, models.py and splash.py; one test corrected; tests."
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "TouchHandler"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
    - name: "DisplayConfig"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "SplashScreen"
      file_path: "src/gtach/display/splash.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_gauge_display_touch.py (new), tests/test_callbacks_outside_locks.py"
      change_type: "add"
  affected_designs:
    - "design-b8c9d0e1-component_display_manager"
  out_of_scope:
    - "Splitting display/manager.py (decision D8)."
    - "Render caching and conditional render (deferred rows 821919ce, 9ed1c77e; observation O3)."
    - "The setup flow files (run 4) and src/gtach/comm."
    - "Gauge geometry, colours and the 9000 RPM full-scale cap itself."

rational:
  problem_statement: "See issue-2550e4ee."
  proposed_solution: >
    EDIT A (C04, C05) — DisplayManager.
    (1) touch_handler, _setup_manager, _in_setup_mode,
    _setup_entry_callback, _splash_screen and performance_monitor are
    assigned their inactive defaults before the first statement that
    can raise. The touch initialisation catches Exception (logged with
    exc_info), not only ImportError, and leaves touch_handler None.
    Every use of performance_monitor tolerates None.
    (2) Each reader of _setup_manager outside the thread that sets it
    (display loop, render path, handle_touch_event) copies it to a
    local once and tests and uses the local.

    EDIT B (C06 decision D6, C07) — TouchHandler._process_touch.
    (1) On release outside setup mode: the movement from the start
    position is compared with the swipe threshold the short-press path
    already uses. Movement at or above the threshold is handled by the
    short-press path (which performs swipes) whatever the duration. A
    long press requires duration >= touch_long_press and movement
    below the threshold. A hold that starts on a registered button
    region is a press of that button, not a palette toggle.
    (2) A stored touch start older than _TOUCH_START_MAX_AGE_S (10.0 s)
    is stale: a down or move event replaces it with the current event,
    and a release discards it without action. The age uses the same
    clock as the stored start.

    EDIT C (O2, get_font(18), C09, C03, A09 display part) —
    DisplayManager.
    (1) _link_lost() is evaluated once per frame, at the start of the
    frame; the three call sites of the frame use that value. The
    method keeps its latch update and its 'every failure path returns
    True' property.
    (2) _render_disconnected takes the cause-line font from
    TypographyConstants.FONT_SMALL_TEXT instead of the literal 18.
    (3) _gauge_max_rpm's docstring states the behaviour: full scale is
    capped at 9000, and a redline above the cap is off the dial with
    its boundary mark omitted. One WARNING is logged at configuration
    load when the configured redline exceeds the full scale.
    (4) _toggle_palette's docstring states the behaviour: the palette
    switches for the session even if the save fails. A failed save is
    logged at WARNING once per toggle; if _save_config does not report
    failure it is made to return bool.
    (5) _on_clear_settings removes every stored device
    (get_all_devices), checks each remove_device result, logs an ERROR
    naming a device that could not be removed, and then invokes the
    setup entry callback as now.

    EDIT D (rpm_bands, O5) — DisplayConfig.rpm_bands uses
    field(default_factory=RPMBands); the None handling in
    __post_init__ and the type: ignore and TODO markers at both sites
    are removed. SplashScreen performs each text-fit check once per
    instance, with the font size that is drawn for that text, not on
    every frame.

    EDIT E (F02) — test_callback_may_register_regions fails if a
    callback runs under the coordinator lock: inside the callback a
    second thread attempts to acquire the coordinator lock with a
    timeout and the test asserts that it succeeded.

    COMMENT RULE — In every file edited, comments that narrate history
    are reduced to the current behaviour plus at most one issue
    reference (CLAUDE.md section 4). In display/manager.py this is
    applied to the functions this change edits and to _link_lost; the
    rest of the file is left for a later change.
  alternatives_considered:
    - option: "C03: revert the palette when the save fails."
      reason_rejected: "The operator asked for the palette; losing it because the SD card is read-only is the worse outcome. The docstring is corrected instead."
    - option: "C09: raise the cap to follow any redline."
      reason_rejected: "Changes the dial for a case no packaged profile has; documented instead."
    - option: "C07: expire the start after touch_long_press."
      reason_rejected: "Would cut off deliberate long holds."
  benefits:
    - "A touch-interface fault degrades to a display without touch."
    - "Slow swipes navigate; held buttons press."
    - "Two fewer transport-lock acquisitions per frame."
  risks:
    - risk: "EDIT B changes gesture feel."
      mitigation: "Device session B covers slow swipe, held button and long press at rest; thresholds are the existing ones."
    - risk: "EDIT C(1): a frame uses a link state up to one frame old."
      mitigation: "33 ms at 30 Hz; the latch is still updated every frame."
    - risk: "EDIT C(5) removes secondary devices the operator wanted to keep."
      mitigation: "No screen lists or selects secondary devices; 'Clear settings' is documented as clearing the store."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits."
  code_changes:
    - component: "display"
      file: "manager.py, touch.py, models.py, splash.py"
      change_summary: "EDITS A to D"
      functions_affected:
        - "DisplayManager.__init__"
        - "DisplayManager._initialize_legacy_components"
        - "DisplayManager display loop and render path"
        - "DisplayManager.handle_touch_event"
        - "DisplayManager._toggle_palette"
        - "DisplayManager._gauge_max_rpm"
        - "DisplayManager._render_disconnected"
        - "DisplayManager._on_clear_settings"
        - "TouchHandler._process_touch"
        - "DisplayConfig.__post_init__"
        - "SplashScreen render methods"
      classes_affected: []
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-b4f9607a"
      relationship: "precedes; remove_device returns a truthful result"
    - change_ref: "change-cfa4e617"
      relationship: "precedes; removes the unused coordinator paths"

testing_requirements:
  test_approach: "Unit tests with stubs; pygame with the dummy video driver; injected timestamps for touch."
  test_cases:
    - scenario: "C04: create_touch_interface raises RuntimeError; PerformanceMonitor construction raises."
      expected_result: "DisplayManager constructs; touch_handler None; performance_monitor None; _setup_manager, _in_setup_mode, _setup_entry_callback and _splash_screen exist; one frame renders without AttributeError."
    - scenario: "C05: a property-style stub makes _setup_manager non-None on the first read and None on the second, in the render path and in handle_touch_event."
      expected_result: "No AttributeError; the setup manager's method is called once."
    - scenario: "C06: touch at (240,240), release at (240,100) after 1.5 s, outside setup mode."
      expected_result: "The swipe handler runs; the palette is unchanged."
    - scenario: "C06: touch and release at the same point after 1.5 s on empty gauge area."
      expected_result: "Long press: the palette toggles."
    - scenario: "C06: touch and release on a registered button region after 1.5 s."
      expected_result: "The button's action runs; the palette is unchanged."
    - scenario: "C07: down at t=0 with no release; down at t=20 elsewhere; release at t=20.2."
      expected_result: "A short press at the second position; no long press, no swipe."
    - scenario: "C07: down at t=0; release at t=12."
      expected_result: "No action."
    - scenario: "O2: render one frame with a counting link callback."
      expected_result: "The callback is called once."
    - scenario: "Cause line: _render_disconnected with a cause and a recording font manager."
      expected_result: "The font size requested is FONT_SMALL_TEXT."
    - scenario: "C09: configuration with redline 12000."
      expected_result: "_gauge_max_rpm returns 9000; one WARNING at load."
    - scenario: "C03: _toggle_palette with a failing save."
      expected_result: "Palette switched; one WARNING."
    - scenario: "A09: _on_clear_settings with a primary and a secondary device; then with remove_device returning False."
      expected_result: "Both removed and the callback invoked; in the failing case an ERROR names the device and the callback is still invoked."
    - scenario: "rpm_bands: two DisplayConfig() instances."
      expected_result: "Each has its own RPMBands instance."
    - scenario: "O5: render the splash for 30 frames with a counting font manager."
      expected_result: "Each text-fit check runs once, with the size drawn."
    - scenario: "F02: run the corrected test against a coordinator patched to dispatch under its lock."
      expected_result: "The test fails; against the real coordinator it passes."
  regression_scope:
    - "tests/test_setup_and_gauge.py, tests/test_callbacks_outside_locks.py, tests/test_medium_defects.py and the display, touch and splash tests."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes; mypy src/ reports no issues."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to E and tests."
      owner: "tactical"
    - step: "Device session B, then the in-car test."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-11-12"
  implemented_by: "Claude Code"
  verification_date: ""
  verified_by: ""
  test_results: "Commit afe74234f1207b8c931b4d21048b492651713af0: pytest 721 passed (27 new in tests/test_gauge_display_touch.py); mypy src/ no issues (worker's results, report-2550e4ee section 4). Against the base code 18 of the new tests fail and the C04 frame test hangs."
  issues_found:
    - "New public method TouchEventCoordinator.is_button_at(pos) (not listed in interface_changes): wraps the private hit test under the coordinator lock; used by TouchHandler to recognise a hold on a button. Accepted."
    - "A hold on a button presses at the start position; movement is below the swipe threshold. Accepted."
    - "A failed palette save logs an ERROR in _save_config and the WARNING in _toggle_palette. Accepted."
    - "Helpers _swipe_threshold (touch.py) and gauge_full_scale (manager.py) are module functions so that existing tests with stub hosts keep working. Accepted."
    - "The per-frame link value reflects samples drained up to the previous frame (about 33 ms at 30 Hz), as recorded under risks."

traceability:
  design_updates:
    - "design-b8c9d0e1 (display manager): refresh after this run (report-71ab3751-design-review section 3.4). Planner."
  related_changes:
    - change_ref: "change-b4f9607a"
      relationship: "depends on"
    - change_ref: "change-34781bfe"
      relationship: "precedes in the run order (independent files)"
  related_issues:
    - issue_ref: "issue-2550e4ee"
      relationship: "resolves"

notes: "The version increment (suggested 0.5.0) follows device session B and is not part of this change."

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-2550e4ee iteration 1."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Implemented in afe74234f1207b8c931b4d21048b492651713af0; awaiting device session B."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial change document. EDITS A to E. |
| 1.1 | 2026-11-11 | Approved for implementation. |
| 1.2 | 2026-11-12 | Implemented in afe7423; awaiting device session B. |

---

Copyright (c) 2026 William Watson. MIT License.
