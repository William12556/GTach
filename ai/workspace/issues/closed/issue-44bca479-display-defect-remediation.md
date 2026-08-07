Created: 2026 July 30

# Issue: Status Indicator Drawn Outside the Panel, Touch Regions Rebuilt Every Frame, Event Poll Inert

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-44bca479"
  title: "The connection status indicator is drawn 73 px outside the circular viewport; touch regions are cleared and rebuilt 60 times a second, discarding any touch that lands in the window; the SDL event poll is unreachable"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-44bca479"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Recommendation 19 (§9.4) addressing finding §8.1; recommendation 20
    addressing §8.2; recommendation 22 addressing §8.4.
    Task list reference: ai/task.md §7.3.8.

affected_scope:
  components:
    - name: "DisplayManager._draw_status_indicator"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_acknowledgement_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._render_disconnected"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
    - name: "TouchEventCoordinator"
      file_path: "src/gtach/display/input/touch_coordinator.py"
  designs: []
  version: "0.2.67"

reproduction:
  prerequisites: >
    GTach running on gtach.local with the HyperPixel 2.1 Round panel.
  steps:
    - "Observe any normal display mode. The connection status dot is never visible anywhere on the panel."
    - "Compute its position: _draw_status_indicator draws at (20, 20); the viewport centre is (240, 240) with radius 238."
    - "Enter the OPTIONS screen and tap a button repeatedly. Occasionally a tap has no effect."
    - "Read _draw_options_menu, _draw_update_view, _draw_acknowledgement_mode and _render_disconnected: each begins by clearing the touch regions and then re-registering them, on every frame."
    - "Read the event-poll block at the head of _display_loop and note that SDL_VIDEODRIVER is dummy and set_mode is never called."
  frequency: "always"
  reproducibility_conditions: >
    Faults (a) and (c) are unconditional. Fault (b) is a race: a touch is
    lost only if it acquires the region lock between the clear and the
    re-registration, so it is intermittent from the operator's point of
    view while being structurally present 60 times a second.
  preconditions: >
    480 x 480 circular panel; viewport radius 238 px; fps_limit 60.
    Touch events arrive on a separate thread through
    TouchHandler._handle_touch_event.
  test_data: >
    Distance of the indicator from the viewport centre:
    sqrt((240 - 20)^2 + (240 - 20)^2) = sqrt(220^2 + 220^2) = 311 px.
    The circular viewport radius is 238 px, so the indicator is 73 px
    outside it.
  error_output: "None. No exception is raised for any of the three."

behavior:
  expected: >
    The connection status is visible. A touch that lands on a registered
    control acts on it. Code that cannot execute is not present.
  actual: >
    Three independent defects, grouped because they are the report's
    Priority 4 set and all sit in manager.py.

    (a) Status indicator outside the visible area — manager.py:1524-1525.
    _draw_status_indicator draws a 5 px radius dot at (20, 20). That is
    311 px from the viewport centre, which has radius 238, so the dot is
    73 px beyond the edge of the circular panel and cannot be seen. It is
    drawn on every frame in every normal mode. The coordinate is one
    chosen for a rectangular display.

    (b) Touch regions rebuilt every frame — manager.py:978, 1028, 1301,
    1391. _draw_options_menu, _draw_update_view,
    _draw_acknowledgement_mode and _render_disconnected each call
    touch_coordinator.clear_regions() and then re-register their regions,
    from inside the render path. Touch events are delivered on a separate
    thread. TouchEventCoordinator guards its region map with an RLock, so
    the dictionary cannot be corrupted — but a touch that acquires the
    lock between the clear and the re-registration observes an empty or
    partial region set and is discarded. The window recurs at the frame
    rate.

    (c) Inert event poll — the head of _display_loop. The loop polls the
    SDL event queue and handles pygame.QUIT. SDL_VIDEODRIVER is set to
    dummy and set_mode is never called, so no window exists and no window
    events are generated. The poll loop and the QUIT path are unreachable.
    The comment above them explains macOS Cocoa run-loop behaviour, which
    is doubly stale: macOS runtime support was removed under
    issue-f2c8a3e7.
  impact: >
    (a) removes a diagnostic the operator would otherwise have at a
    glance — whether the OBD transport is connected — and costs a draw
    call per frame to produce nothing.

    (b) is the operator-visible one: a tap that does nothing, with no
    feedback and no way to distinguish it from a mis-tap. It compounds
    the adjacent-target problem recorded in report §7.3, where the
    options buttons are 6.1 mm tall with a 1.1 mm separation.

    (c) costs almost nothing at runtime and misleads a reader into
    believing the application handles window events and can be closed by
    the window manager.
  workaround: >
    (b) Tap again. There is no workaround for (a).

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    All three are artefacts of assumptions that were true earlier in the
    project and are not true now. The indicator coordinate assumes a
    rectangular display. The registration-in-render pattern assumes that
    drawing and input registration are the same concern, which holds only
    while nothing else touches the regions concurrently. The event poll
    assumes an SDL presentation path that the dummy driver removed.
  technical_notes: >
    For (b), the report's prescription — "registration belongs at mode
    entry, not in the render path" — needs a mode-transition hook, and
    there is none. There are roughly fourteen sites assigning
    self.config.mode, so wrapping each would be invasive and would leave
    a future assignment able to bypass the hook.

    A detection-based hook is more robust: derive a view key each frame
    and re-register only when it changes. The key must include more than
    the mode, and identifying its members needs care.

      - self._options_view selects between the menu and the update
        sub-view within DisplayMode.OPTIONS.
      - self._update_status decides which controls _draw_update_view
        registers, and a worker thread writes it in _run_update_check, so
        omitting it would leave the wrong regions registered after an
        asynchronous change.
      - The disconnected condition is not a DisplayMode. The enum has
        only SPLASH, DIGITAL, RADIAL, OPTIONS and ACKNOWLEDGEMENT;
        _render_normal_modes shows the disconnected screen when the
        obd_protocol thread is not RUNNING and simulation mode is off,
        and gives that check precedence over the mode. Omitting it would
        mean the Setup and Simulate buttons were never registered when
        the transport drops — turning an intermittent fault into a
        permanent one on the very screen that exists to recover from it.
      - self._in_setup_mode matters because the setup subsystem registers
        and owns its own regions. The hook must not clear them, and
        leaving setup must trigger re-registration of the normal view.

    The render methods currently compute their button rectangles inline
    and register them in the same pass. Moving registration out requires
    the rectangles to exist before the first draw of a view. Computing
    them in the registration function and having the render methods read
    them preserves a single source for the geometry and gives the right
    ordering, since registration runs on the frame the view changes.

    Two registration sites are deliberately out of scope.
    _render_mode_selector (manager.py:1170) registers regions but is
    never called from any code path — report §7.6 — and task 7.3.10
    proposes removing it. _register_save_button (manager.py:1266) belongs
    to the setup flow, which does not exhibit the clear-and-rebuild
    pattern.

    The clear_regions() call at manager.py:1375 is not part of this
    fault: it runs on acknowledgement dismissal, which is a genuine
    transition, and is correct where it is.

    For (c), removal is preferable to documentation. pygame.event.poll()
    on the dummy driver returns NOEVENT immediately and pumps nothing
    that matters; the QUIT path cannot fire; and the surviving comment
    describes a platform the project no longer supports. Shutdown is
    driven entirely by _shutdown_event.
  related_issues:
    - issue_ref: "issue-b02ed4ea"
      relationship: "blocks"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Relocate the status indicator inside the circular viewport; introduce
    a view-key hook so touch regions are registered once per view rather
    than once per frame; remove the unreachable event poll and its stale
    comment. See change-44bca479.
  change_ref: "change-44bca479"
  resolved_date: "2026-07-31"
  resolved_by: "Claude Code, per prompt-44bca479"
  fix_description: >
    Five edits to src/gtach/display/manager.py, as specified. No departure
    from the prompt's text was required.

    Defect 1, the invisible indicator. _draw_status_indicator draws at
    (240, 60) instead of (20, 20). That is 180 px from the viewport centre,
    inside the 238 px radius; the old position was 311 px out, 73 px beyond
    the edge of the circular panel. The thread-status lookup, the colour
    mapping, the 5 px radius and the exception handler are unchanged.

    Defect 2, the region-set race. Registration is now driven by a change in
    a view key rather than by the render path. _current_view_key returns
    (mode, _options_view, _update_status, disconnected, _in_setup_mode);
    _display_loop evaluates it before the render dispatch and calls
    _register_view_regions only when it differs from _registered_view. That
    function clears once, gives the derived disconnected condition
    precedence over config.mode exactly as _render_normal_modes does, and
    dispatches to one of four new helpers that compute the rectangles and
    issue the registrations. It returns without clearing while in setup
    mode, so the setup subsystem's own regions survive. Every region name,
    TouchAction and callback was moved verbatim; a signature-level
    comparison against the previous file confirms all ten are unchanged.
    The four render methods now draw only, reading the rectangles from self
    behind None guards, so geometry has a single owner and a control cannot
    be drawn that was not registered.

    Defect 3, the dead poll. The pygame.event.poll block and its macOS
    comment are removed. SDL_VIDEODRIVER is 'dummy' and set_mode is never
    called, so no window exists and the QUIT path was unreachable. Shutdown
    remains driven solely by _shutdown_event.

verification:
  verified_date: "2026-07-31"
  verified_by: "Claude Code"
  test_results: >
    Development platform only (macOS, Python 3.11.14, pygame 2.6.1). A real
    DisplayManager was constructed with a real TouchEventCoordinator —
    the region set being what is under test — stubbing only the rendering
    engine and the thread manager. Eighty-eight assertions, all passing.
    See change-44bca479 verification.test_results for the full record.

    The race was demonstrated directly rather than argued. Rendering the
    options menu repeatedly on one thread while a second thread sampled
    get_active_regions, the pre-change code was observed with an empty
    region set in 235,321,813 of 245,707,350 samples — 95.8 per cent — and
    with a partial set in a further 2,832,945. The same measurement against
    the changed code gives 0 empty and 0 partial across 150,725,081
    samples, the count never leaving 4. A touch was not merely occasionally
    unlucky; it was more likely than not to find nothing registered.

    pytest tests/ — 11 passed, unchanged by this work.

    This issue is left active pending on-target results per ai/task.md
    §8.2.1. Two of the three corrections are visible on the panel and
    neither has been seen there.
  closure_notes: >
    William confirmed on 2026-08-07 that GTach is functioning correctly
    on gtach.local, satisfying the three OUTSTANDING on-target
    verification_enhanced steps (status dot visible and colour-
    correct, every OPTIONS tap acts, shutdown paths intact). Source
    re-check: _draw_status_indicator draws at (240, 60), inside the
    viewport; _register_view_regions and the view-key mechanism are
    present exactly as described; no residual finding.

prevention:
  preventive_measures: >
    A coordinate on a non-rectangular display should be validated against
    the viewport, not assumed. Input registration and rendering are
    separate concerns and should not share a call path. Code made
    unreachable by a platform decision should be removed with that
    decision rather than left behind.
  process_improvements: >
    The engine already has validate_circular_bounds. Drawing calls that
    place fixed elements could be checked against it during review.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "Compute the new indicator position and confirm its distance from (240, 240) is less than 238."
    - "On gtach.local: confirm the status dot is visible and changes colour when the OBD transport connects and disconnects."
    - "Confirm no clear_regions call remains inside _draw_options_menu, _draw_update_view, _draw_acknowledgement_mode or _render_disconnected."
    - "Unit test: with a fixed view key, confirm the registration function is called once across many rendered frames."
    - "Unit test: change _update_status from 'checking' to 'available' and confirm registration runs again on the next frame."
    - "Unit test: change _options_view from 'menu' to 'update' and confirm registration runs again."
    - "On gtach.local: tap each OPTIONS button twenty times and confirm every tap acts."
    - "Confirm pygame.event.poll no longer appears in manager.py and that shutdown by the watchdog and by SIGINT both still work."
  verification_results: >
    Six of the nine steps are complete; three require gtach.local.

    PASS — python -m py_compile src/gtach/display/manager.py.

    PASS — the new indicator position is 180.0 px from (240, 240), inside
    the 238 px viewport radius. The previous position was 311.1 px, which
    is 73 px beyond the edge of the panel. The draw call is issued exactly
    once per render and the colour mapping still responds to the transport
    state.

    PASS — no clear_regions call remains inside _draw_options_menu,
    _draw_update_view, _draw_acknowledgement_mode or _render_disconnected,
    and no register_button_region call remains in any of them either,
    confirmed by walking each method's AST rather than by grep. The
    clear_regions on acknowledgement dismissal is still present, and
    _register_view_regions clears exactly once per invocation.

    PASS — with a fixed view key, fifty rendered frames call the
    registration function once.

    PASS — _update_status 'checking' to 'available' re-registers on the
    next frame and the install and cancel regions appear. The full status
    matrix was exercised: 'checking' and 'pending' register nothing,
    'available' registers install and cancel, 'none' and 'error' register
    the back region.

    PASS — _options_view 'menu' to 'update' re-registers and the four menu
    regions are replaced.

    OUTSTANDING — on gtach.local, confirm the status dot is visible and
    changes colour as the transport connects and disconnects. If it
    collides with RADIAL tick marks or numerals at (240, 60), the recorded
    alternative is (240, 300) and the correction is a single coordinate.

    OUTSTANDING — on gtach.local, tap each OPTIONS button twenty times and
    confirm every tap acts. The off-target measurement below makes the
    prediction sharp: before this change a tap had roughly a one-in-twenty
    chance of landing while the region set was populated.

    OUTSTANDING — confirm shutdown by the watchdog and by SIGINT both still
    work. pygame.event.poll and pygame.QUIT are absent from manager.py and
    the loop remains bounded by _shutdown_event, but neither shutdown path
    has been exercised.

traceability:
  design_refs: []
  change_refs:
    - "change-44bca479"
  test_refs: []

notes: >
  This is task 7.3.8 in ai/task.md §7.3 and part of step 6 in the
  recommended authoring order (§7.6.2).

  §7.6.1 records that 7.3.9 depends on this task: recommendations 24 and
  27 re-register button regions, and doing so before the mode-entry hook
  exists would produce registration code inside the render path that this
  task then has to relocate. The §7.6.2 order already places 7.3.8 at
  step 6 and 7.3.9 at step 9, so the constraint is satisfied provided the
  order is not changed.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial issue document from display-ui-graphics-review.md recommendations 19, 20 and 22."
  - version: "1.1"
    date: "2026-07-31"
    author: "Claude Code"
    changes:
      - "Status open -> resolved. change-44bca479 implemented; resolution date, executor and fix description recorded for all three defects."
      - "Recorded a direct measurement of the region-set race: 95.8 per cent of 245 million samples observed an empty region set before the change, none after."
      - "Recorded six of nine verification steps as PASS and three as OUTSTANDING pending gtach.local."
      - "Recorded that every region name, TouchAction and callback was moved verbatim, confirmed by signature comparison against the previous file."
      - "Left active pending on-target test results per ai/task.md §8.2.1."
  - version: "1.2"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status resolved -> closed. Source re-check confirms the fix present and unchanged. Closed on William's confirmation that GTach functions correctly on gtach.local, satisfying the three on-target OUTSTANDING steps."
      - "Moved to ai/workspace/issues/closed/."

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
| 1.0 | 2026-07-30 | Initial issue document from display-ui-graphics-review.md recommendations 19, 20 and 22. |
| 1.1 | 2026-07-31 | Status open → resolved; fix description and per-step verification recorded, including a direct measurement of the region-set race. Left active pending on-target results. |
| 1.2 | 2026-08-07 | Status resolved → closed. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
