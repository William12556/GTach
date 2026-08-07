Created: 2026 July 30

# Change: Indicator Inside the Viewport, Regions Registered per View, Dead Poll Removed

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-44bca479"
  title: "Move the status indicator to (240, 60); register touch regions on view change via a detected view key rather than in the render path; remove the unreachable SDL event poll"
  date: "2026-07-30"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-44bca479"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-44bca479"
  description: >
    Resolves issue-44bca479. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0
    recommendations 19, 20 and 22. Task list reference ai/task.md §7.3.8.

scope:
  summary: >
    Three independent corrections in src/gtach/display/manager.py. Move
    the connection status indicator inside the circular viewport.
    Introduce a view key so touch regions are registered once when the
    view changes rather than on every frame. Remove the SDL event poll,
    which cannot fire under the dummy driver.
  affected_components:
    - name: "DisplayManager.__init__"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_status_indicator"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._current_view_key"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._register_view_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_acknowledgement_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._render_disconnected"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "_render_mode_selector (manager.py:1170). It registers regions but is never called from any code path — report §7.6 — and task 7.3.10 proposes removing it."
    - "_register_save_button (manager.py:1266). Belongs to the setup flow, which does not exhibit the clear-and-rebuild pattern."
    - "The clear_regions call at manager.py:1375. It runs on acknowledgement dismissal, which is a genuine transition, and is correct."
    - "Button geometry, touch-target sizes and the TypographyConstants design system — recommendations 24 and 27, task 7.3.9."
    - "src/gtach/display/input/touch_coordinator.py. Its RLock and API are unchanged; only the calling pattern changes."
    - "Increasing the indicator radius. 5 px is 0.55 mm at 229 ppi and arguably too small, but resizing is not in recommendation 19."

rational:
  problem_statement: >
    Three defects reported under display review §8.0. The status
    indicator is drawn 73 px outside the circular viewport and cannot be
    seen. Touch regions are cleared and rebuilt from the render path 60
    times a second, so a touch arriving in that window on the input
    thread finds an empty region set and is discarded. The SDL event poll
    cannot fire, because the dummy driver creates no window, and its
    comment describes macOS behaviour on a platform the project no longer
    supports.
  proposed_solution: >
    Relocate the indicator to (240, 60), 180 px from the centre and well
    inside the 238 px viewport. Compute a view key each frame from the
    mode, the options sub-view and the update status; when it changes,
    clear and re-register once. Delete the event poll and replace the
    stale comment with one recording why there is no event handling.
  alternatives_considered:
    - option: "Wrap every self.config.mode assignment in a setter that fires the registration hook."
      reason_rejected: >
        There are roughly fourteen assignment sites. Wrapping each is
        invasive, and a future assignment added elsewhere would bypass the
        hook silently. Detecting the change is robust against that.
    - option: "Key the registration on self.config.mode alone."
      reason_rejected: >
        Four other pieces of state decide which controls exist.
        _update_status selects the update view's controls and is written
        by a worker thread. _options_view selects menu against update
        sub-view. The disconnected screen is not a DisplayMode at all —
        the enum holds only SPLASH, DIGITAL, RADIAL, OPTIONS and
        ACKNOWLEDGEMENT, and _render_normal_modes derives the disconnected
        case from the obd_protocol thread status and _sim_mode, giving it
        precedence over the mode. And _in_setup_mode matters because the
        setup subsystem owns its own regions. Keying on mode alone would
        leave the Setup and Simulate buttons unregistered whenever the
        transport dropped.
    - option: "Keep registration in the render path but hold the coordinator's lock across the clear and the re-registration."
      reason_rejected: >
        It would close the race but retain a full clear-and-rebuild at 60
        Hz, and would hold an input lock from the render thread for the
        duration of every frame's registration work. Registering once per
        view is both correct and cheaper.
    - option: "Place the indicator at (240, 300), the report's other suggestion."
      reason_rejected: >
        It sits inside the RADIAL inert bottom arc, which is sensible
        there, but in DIGITAL the numeral is rendered at 180 px centred on
        (240, 215) and extends to roughly y = 280. (240, 60) is clear of
        the numeral in DIGITAL and outside the r = 99 centre disc in
        RADIAL. Final placement still needs confirmation on the panel.
    - option: "Document the event poll rather than removing it, as recommendation 22 permits."
      reason_rejected: >
        The code cannot execute and its comment is actively misleading —
        it describes a macOS Cocoa run-loop interaction on a platform
        removed under issue-f2c8a3e7. Removing it and recording why in a
        comment leaves the reader better informed than retaining it.
  benefits:
    - "The operator regains an at-a-glance connection indication."
    - "A tap on a registered control always acts, removing an intermittent failure that is indistinguishable from a mis-tap."
    - "Registration work moves off the frame path entirely for every static screen."
    - "One fewer dead code path, and one fewer stale comment describing a removed platform."
  risks:
    - risk: >
        A view whose key does not change but whose controls should — a
        registration missed because the key is incomplete.
      mitigation: >
        The key covers every input the four affected methods branch on:
        config.mode, _options_view and _update_status. The registration
        function is the single place that maps a key to controls, so a
        future view that adds a branch has one obvious place to extend.
        State the requirement in its docstring.
    - risk: >
        Button rectangles are read by the render methods before the
        registration function has computed them.
      mitigation: >
        Registration runs earlier in the same frame as the first draw of a
        new view, because the key is evaluated before rendering. Initialise
        the rect attributes to None in __init__ and have the render
        methods guard, so a missed ordering degrades to a control that is
        not drawn rather than an AttributeError.
    - risk: >
        Removing the event poll removes the only pygame.QUIT handler, so
        a future SDL presentation path would have no shutdown route.
      mitigation: >
        Shutdown is driven by _shutdown_event, set by the application and
        the watchdog. Record in the replacing comment that any future
        change reinstating a real SDL video driver must reinstate event
        handling with it.
    - risk: >
        (240, 60) collides with a RADIAL tick mark or numeral.
      mitigation: >
        Geometrically it is 180 px from the centre, inside the r = 232
        background and outside the r = 99 centre disc, so it lands in the
        arc band. Confirm on the panel; if it collides, (240, 300) is the
        recorded alternative and the change is a single coordinate.

technical_details:
  current_behavior: >
    _draw_status_indicator draws a 5 px circle at (20, 20)
    (manager.py:1524-1525), called from the normal-mode render path at
    manager.py:531. _draw_options_menu (978), _draw_update_view (1028),
    _draw_acknowledgement_mode (1301) and _render_disconnected (1391)
    each begin with touch_coordinator.clear_regions() and register their
    controls inline. _display_loop opens with a pygame.event.poll loop
    handling pygame.QUIT.
  proposed_behavior: >
    The indicator is drawn at (240, 60). _display_loop evaluates a view
    key before rendering and calls _register_view_regions once when it
    changes. The four render methods draw only, reading rectangles the
    registration function computed. The event poll is gone.
  implementation_approach: >
    Five edits in src/gtach/display/manager.py.

    EDIT 1 — __init__. Add self._registered_view = None and initialise
    the button rect attributes the registration function will populate:
    _options_btn_clear, _options_btn_sim, _options_btn_debug,
    _options_btn_update, _update_btn_install, _update_btn_cancel, and the
    disconnected and acknowledgement rects, each to None.

    EDIT 2 — _draw_status_indicator. Change the draw coordinate from
    (20, 20) to (240, 60), with a comment recording the geometry: 180 px
    from the centre, inside the 238 px viewport, where (20, 20) was 311 px
    out.

    EDIT 3 — add _current_view_key() and _register_view_regions().
    _current_view_key returns (config.mode, _options_view,
    _update_status, the derived disconnected condition, _in_setup_mode).
    _register_view_regions returns early without clearing while in setup
    mode, then clears once and registers the controls for the current
    view, giving the disconnected condition precedence over the mode so
    the dispatch mirrors _render_normal_modes. It computes the rectangles
    and stores them on self for the render methods to read. Its docstring
    must state that any new branch in a render method has to be reflected
    in the key.

    EDIT 4 — _display_loop. Remove the event-poll block and its comment,
    replacing them with a comment recording why there is no event
    handling. Before the render dispatch, evaluate the key and
    re-register when it differs from self._registered_view.

    EDIT 5 — the four render methods. Remove the clear_regions call and
    every register_button_region call from _draw_options_menu,
    _draw_update_view, _draw_acknowledgement_mode and
    _render_disconnected. Keep every drawing call. Where a method
    currently computes a rect and then draws it, read the rect from self
    and guard against None.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Status indicator relocated inside the viewport; touch-region
        registration moved out of the render path behind a view-key
        change detector; unreachable SDL event poll removed.
      functions_affected:
        - "__init__"
        - "_draw_status_indicator"
        - "_current_view_key"
        - "_register_view_regions"
        - "_display_loop"
        - "_draw_options_menu"
        - "_draw_update_view"
        - "_draw_acknowledgement_mode"
        - "_render_disconnected"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "TouchEventCoordinator"
      impact: "Called from a new site. clear_regions and register_button_region are unchanged; the RLock still guards the region map. No modification to touch_coordinator.py."
    - component: "DisplayManager._run_update_check"
      impact: "Writes _update_status from a worker thread. That write now also drives re-registration, via the view key, on the next frame."
    - component: "task 7.3.9"
      impact: "Depends on this change. Its button helper must register through _register_view_regions rather than from the render path."
  external: []
  required_changes:
    - change_ref: "change-b02ed4ea"
      relationship: "blocks"

testing_requirements:
  test_approach: >
    Unit tests on the development platform with SDL_VIDEODRIVER=dummy, a
    mocked rendering engine and a real TouchEventCoordinator, plus
    on-target confirmation for the two visible effects.
  test_cases:
    - scenario: "Compute the distance of the new indicator coordinate from the viewport centre."
      expected_result: "180 px, inside the 238 px radius. The previous (20, 20) was 311 px."
    - scenario: "Render fifty frames with the view key unchanged."
      expected_result: "_register_view_regions called once."
    - scenario: "Change _update_status from 'checking' to 'available' between frames."
      expected_result: "_register_view_regions called again on the next frame; install and cancel regions registered."
    - scenario: "Change _options_view from 'menu' to 'update'."
      expected_result: "Re-registration occurs; the four menu regions are replaced."
    - scenario: "Change config.mode from OPTIONS to RADIAL."
      expected_result: "Re-registration occurs; no button regions remain registered."
    - scenario: "Query the registered regions while rendering the OPTIONS menu repeatedly from a second thread."
      expected_result: "The region set is never observed empty or partial after the first registration."
    - scenario: "Render the OPTIONS menu without a prior registration pass."
      expected_result: "Rect attributes are None; the method guards and draws nothing rather than raising AttributeError."
    - scenario: "Inspect manager.py for pygame.event.poll."
      expected_result: "Absent."
    - scenario: "Set _shutdown_event while the loop runs."
      expected_result: "The loop exits, as before. Shutdown does not depend on the removed poll."
  regression_scope:
    - "tests/display/ once populated."
    - "Manual on target: the status dot is visible and tracks the transport state."
    - "Manual on target: every control on OPTIONS, the update view, DISCONNECTED and the acknowledgement screen responds to touch."
    - "Manual on target: the acknowledgement screen still dismisses and transitions to the post-splash mode."
    - "Manual on target: long press still returns from OPTIONS."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "No clear_regions call remains in the four named render methods."
    - "No register_button_region call remains in the four named render methods."
    - "pygame.event.poll does not appear in manager.py."
    - "_render_mode_selector and _register_save_button are unmodified."
    - "src/gtach/display/input/touch_coordinator.py is unmodified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — view state and rect attributes in __init__."
      owner: "Claude Code"
    - step: "EDIT 2 — relocate the status indicator."
      owner: "Claude Code"
    - step: "EDIT 3 — add _current_view_key and _register_view_regions."
      owner: "Claude Code"
    - step: "EDIT 4 — remove the event poll; add the re-registration check to _display_loop."
      owner: "Claude Code"
    - step: "EDIT 5 — strip registration from the four render methods."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; confirm the indicator is visible and every control responds; confirm the indicator does not collide with RADIAL tick marks."
      owner: "William Watson"
  rollback_procedure: >
    Single file, single commit. git revert restores the previous
    behaviour. No data, configuration or interface migration is involved.
  deployment_notes: >
    Two of the three effects are visible on the panel, so on-target
    confirmation is quick. If the indicator collides with RADIAL
    furniture at (240, 60), the recorded alternative is (240, 300) and
    the correction is one coordinate.

verification:
  implemented_date: "2026-07-31"
  implemented_by: "Claude Code, per prompt-44bca479"
  verification_date: "2026-07-31"
  verified_by: "Claude Code"
  test_results: >
    Development platform only: macOS, Python 3.11.14, pygame 2.6.1, SDL
    dummy driver. A real DisplayManager was constructed with a real
    TouchEventCoordinator, since the region set is the thing under test;
    only the rendering engine and the thread manager were stubbed, the
    former with a recorder that captures every rectangle, label and circle
    drawn. Eighty-eight assertions, all passing. Left active pending
    on-target results per ai/task.md §8.2.1.

    All five edits applied and all seventeen success criteria met. No
    departure from the prompt's text was required — the first prompt in
    this sequence for which that is true.

    THE RACE, MEASURED. The issue asserts that a touch arriving while the
    render path rebuilds the region map is discarded. That was demonstrated
    rather than reasoned about. Rendering the options menu repeatedly on
    one thread while a second thread sampled get_active_regions:

      pre-change   245,707,350 samples, 235,321,813 empty, 2,832,945
                   partial, minimum 0, maximum 4
      post-change  150,725,081 samples, 0 empty, 0 partial, minimum 4,
                   maximum 4

    95.8 per cent of samples observed no regions at all. The defect is not
    a narrow window that a touch occasionally falls into; for most of each
    frame the map was empty, and a tap was more likely to be discarded than
    honoured. This also sets the expectation for the on-target check: taps
    on OPTIONS should go from intermittent to reliable, not from reliable
    to slightly more reliable.

    Evidence by test case.

    Indicator: the draw call is at (240, 60), 180.0 px from the viewport
    centre and inside the 238 px radius; the previous (20, 20) was 311.1 px
    out. The radius, the colour mapping and the ConnectionStatus branches
    are untouched, and the call is issued exactly once per render in both
    the connected and disconnected states.

    View key: a five-element tuple carrying the mode, the options
    sub-view, the update status, the derived disconnected condition and the
    setup-mode flag. DisplayMode has no DISCONNECTED member and the string
    "DisplayMode.DISCONNECTED" does not occur in the file.

    Registration cadence: fifty frames at a fixed key produce one
    registration call. The first frame registers, _registered_view starting
    None.

    Update status: 'checking' and 'pending' register nothing; 'available'
    registers update_install and update_cancel; 'none' and 'error' register
    update_back. Transitioning 'available' to 'none' clears the install
    rect, so the render guard cannot draw a button that is no longer
    registered — the rects a status does not present are set to None by the
    registration helper.

    Options sub-view: switching 'menu' to 'update' replaces the four menu
    regions with the update view's.

    Mode: OPTIONS to RADIAL, DIGITAL or SPLASH leaves no button regions.

    Disconnected: with simulation mode off, moving the obd_protocol thread
    from RUNNING to STOPPED changes the key and registers
    disconnected_setup and disconnected_simulate. With _sim_mode True the
    same transition does not change the key and registers nothing, which is
    correct because the disconnected screen is not shown. The disconnected
    condition takes precedence over config.mode, mirroring
    _render_normal_modes: with mode OPTIONS and the transport down, the
    disconnected regions are registered rather than the menu's.

    Setup mode: with _in_setup_mode and _setup_manager set,
    _register_view_regions returns without clearing and a region owned by
    the setup subsystem survives untouched. Leaving setup changes the key
    and re-registers the normal view.

    Render methods draw only: rendering the options menu registers nothing
    and leaves the region set as it was. With the rects still None nothing
    is drawn and no AttributeError is raised. After registration the four
    drawn rectangles are equal, coordinate for coordinate, to the four
    registered regions — the check that geometry now has a single owner.
    All four labels, the title and the long-press hint are still drawn. The
    same holds for the update view in each status, the disconnected screen,
    and the acknowledgement screen, whose dismiss region is still the full
    480x480 surface.

    Failure handling: a registration that raises leaves _registered_view
    unchanged and the next frame retries. The real _register_view_regions
    logs at ERROR with a traceback and re-raises, which is what allows the
    caller to skip the key update.

    Dead poll: pygame.event.poll and pygame.QUIT are both absent from the
    file, and the loop is still bounded by _shutdown_event.is_set(). The
    view key is evaluated before the render dispatch and before
    write_to_framebuffer.

    Scope: every region name, TouchAction and callback is preserved
    verbatim, confirmed by extracting the (name, action, callback) triple
    from each register_button_region call in the previous file and in the
    new one and comparing the sets — ten registrations, identical.
    _render_mode_selector and _register_save_button are byte-identical by
    AST comparison, as are _register_rpm_sliders,
    _on_acknowledgement_dismissed, _draw_digital_mode and
    _draw_radial_mode. src/gtach/display/input/touch_coordinator.py is
    unmodified. Only src/gtach/display/manager.py was changed.

    pytest tests/ — 11 passed, unchanged by this work. No test in tests/
    exercises the display manager.

    What this does not establish: that the dot is visible on the panel, or
    that taps now act on hardware. Both are visible checks and neither has
    been made.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-b02ed4ea"
      relationship: "blocks"
  related_issues:
    - issue_ref: "issue-44bca479"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-44bca479."
  - version: "1.1"
    date: "2026-07-31"
    author: "Claude Code"
    changes:
      - "Status proposed -> implemented. Recorded implementation date, executor, verification date and development-platform test results."
      - "Recorded a direct measurement of the region-set race: 235,321,813 of 245,707,350 samples observed an empty region set before the change, none of 150,725,081 after."
      - "Recorded that no departure from the prompt's text was required."
      - "Recorded that all ten region registrations were moved verbatim, confirmed by comparing (name, action, callback) triples against the previous file."
      - "Recorded that _render_mode_selector and _register_save_button are byte-identical and touch_coordinator.py is unmodified."
      - "Left active pending on-target test results per ai/task.md §8.2.1."
  - version: "1.2"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status implemented -> closed. Source re-check confirms the fix present and unchanged. Closed on William's confirmation that GTach functions correctly on gtach.local."

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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-44bca479. |
| 1.1 | 2026-07-31 | Status proposed → implemented; development-platform test results recorded, including a direct measurement of the region-set race. Left active pending on-target results. |
| 1.2 | 2026-08-07 | Status implemented → closed. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
