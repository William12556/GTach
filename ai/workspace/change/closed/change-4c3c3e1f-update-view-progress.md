Created: 2026 July 30

# Change: Animated Ring Indicator on the Update-Check View

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-4c3c3e1f"
  title: "Add _draw_update_spinner — an eight-dot ring advanced from the frame counter — and call it from _draw_update_view while _update_status is 'checking'"
  date: "2026-07-30"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-4c3c3e1f"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-4c3c3e1f"
  description: >
    Resolves issue-4c3c3e1f. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 finding §7.8
    and recommendation 28 (§9.5). Task list reference ai/task.md §7.3.13.

scope:
  summary: >
    One addition and one call site in src/gtach/display/manager.py. Add a
    private method that draws a ring of eight dots with one highlighted,
    the highlighted index derived from self._frame_counter. Call it from
    _draw_update_view only while _update_status is 'checking'. No new
    instance state and no change to the update workflow.
  affected_components:
    - name: "DisplayManager._draw_update_spinner"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-b8c9d0e1-component_display_manager"
      sections:
        - "Update sub-view rendering"
  out_of_scope:
    - "self._update_wheel (manager.py:76, 1324, 1339, 1349). The source report reads this as a disabled spinner; it holds the wheel filename returned by updater.find_available_update and consumed by updater.stage_pending. It is not touched."
    - "src/gtach/utils/updater.py. The check's cost is dominated by zipfile testzip over each candidate wheel, and making that cheaper or reportable as a percentage is a separate concern from indicating that it is running."
    - "Progress as a percentage or a wheel count. find_available_update reports no intermediate state, so any percentage would be fabricated. An indeterminate indicator is the honest one."
    - "The 'pending' status. It is set after stage_pending succeeds and is immediately followed by _restart_callback (manager.py:1350-1353), so the application is shutting down; an indicator there would outlive its subject."
    - "_register_update_view_regions and every touch region. No control is added, moved or removed."
    - "src/gtach/display/rendering/engine.py. No new drawing primitive is introduced; the indicator is composed from the existing draw_circle."
    - "Conditional rendering and frame skipping — recommendations 12 to 14, task 7.3.6. This change constrains that work; it does not perform it."

rational:
  problem_statement: >
    _draw_update_view renders one of five fixed strings selected from
    _update_status (manager.py:1234-1243). While the status is 'checking'
    the surface is identical frame to frame and no control is registered,
    so a check that is running and an application that has stopped
    present the same picture. The check is a directory scan plus a CRC
    pass over each candidate wheel (utils/updater.py:54-93) dispatched to
    a three-worker pool, so its duration is neither instantaneous nor
    predictable from the operator's side.
  proposed_solution: >
    Draw eight dots on a circle of radius 34 centred at (240, 270), one
    of them highlighted, and advance the highlighted index from
    self._frame_counter. Call the method from _draw_update_view only when
    _update_status is 'checking', after the status message and before the
    hint text.
  alternatives_considered:
    - option: "Reuse self._update_wheel as the spinner phase, as the report's wording implies it was meant to be."
      reason_rejected: >
        The field is live. _run_update_check assigns it the wheel
        filename at manager.py:1339 and _on_confirm_install passes it to
        updater.stage_pending at manager.py:1349. Repurposing it would
        break the install path. The report's premise is incorrect and is
        recorded as such in issue-4c3c3e1f.
    - option: "Derive the animation phase from time.monotonic()."
      reason_rejected: >
        change-4c038bed established the frame counter as the timebase for
        periodic display effects, at manager.py:694-698, so the duty cycle
        is equal by construction at any frame rate. A second, independent
        timebase on the same surface would be gratuitous, and would make
        the effect dependent on scheduler jitter that the frame counter
        is immune to.
    - option: "Animate the status text itself — cycling 'Checking.', 'Checking..', 'Checking...'."
      reason_rejected: >
        Cheapest of all, but it re-renders a text surface every few
        frames and changes the string's width, so the centred text
        shifts. A ring of eight draw_circle calls is both steadier and,
        on this rendering path, no more expensive than one render_text.
    - option: "Add draw_arc to the rendering engine and sweep an arc."
      reason_rejected: >
        A better-looking indicator, but it adds a primitive to
        display/rendering/engine.py, which is the file three other
        triples in this batch have already modified. The dot ring needs
        no engine change at all.
    - option: "Report progress as a fraction of the wheels scanned."
      reason_rejected: >
        find_available_update returns only a final result
        (utils/updater.py:65-93); it publishes no intermediate state. A
        fraction would require changing the updater's interface to gain
        a number the operator has no use for.
  benefits:
    - "A running check is distinguishable from a stalled application without a second source of information."
    - "No new instance state; the animation is a pure function of self._frame_counter and self.config.fps_limit."
    - "No change to the update workflow, the touch regions, or the rendering engine."
    - "The frame-counter timebase is the one already established for periodic display effects, so there is one such mechanism in the file rather than two."
  risks:
    - risk: >
        The indicator overlaps the status message or a button on some
        status, producing a worse screen than the static one.
      mitigation: >
        It is drawn only for 'checking', and _register_update_view_regions
        registers no button for that status (manager.py:1124-1134), so
        the band from y = 210 to y = 390 is unoccupied. The ring occupies
        y = 230 to y = 310 inclusive of the dot radius. The status
        message sits at (240, 180) in a 26 px font, whose lower extent is
        approximately y = 197.
    - risk: >
        The indicator falls outside the circular viewport.
      mitigation: >
        The furthest spinner pixel is 40 px from (240, 270), which is
        30 px below the viewport centre (240, 240). Its greatest distance
        from the centre is therefore 70 px, against a viewport radius of
        238 px. Verified arithmetically before the coordinate was chosen,
        as issue-44bca479 recorded should be done for any fixed
        coordinate on this panel.
    - risk: >
        A permanently animated element blocks the conditional-render
        optimisation proposed by recommendations 12 to 14.
      mitigation: >
        Recorded here and in issue-4c3c3e1f rather than left to be
        discovered. The constraint is narrow — the update view cannot be
        frame-skipped while _update_status is 'checking' — and 7.3.6 must
        treat the checking state as always-dirty. ai/task.md §7.6.1 does
        not carry this row; it should gain one when 7.3.6 is authored.
    - risk: >
        The dots are too small to read at 229 ppi.
      mitigation: >
        6 px is 0.66 mm, against the 5 px connection indicator relocated
        under change-44bca479. Eight of them moving together are a much
        larger visual target than one static dot. Confirm on the panel;
        if the ring is hard to see, the dot radius and ring radius are
        two constants in one method.

technical_details:
  current_behavior: >
    _draw_update_view (manager.py:1225-1275) clears the surface, draws
    the shift border, renders the title 'Update' at (240, 80), selects a
    status string from _update_status (manager.py:1234-1243) and renders
    it at (240, 180), draws whichever buttons the status presents
    (manager.py:1255-1271), and renders 'Long press to return' at
    (240, 410). For the 'checking' status the string is 'Checking…' and
    no button is drawn, so consecutive frames are identical.
  proposed_behavior: >
    Identical, except that when _update_status is 'checking' an eight-dot
    ring is drawn centred at (240, 270), with one dot highlighted and the
    highlighted index advancing once every fps_limit / 8 frames — about
    7.5 steps per second at 60 fps, one revolution in approximately
    1.07 s. The step is floored at one frame, so the period holds at
    approximately 1.07 s for any fps_limit of 8 or more and shortens
    below that.
  implementation_approach: >
    Two edits in src/gtach/display/manager.py.

    EDIT 1 — add _draw_update_spinner, placed immediately before
    _draw_update_view. It computes the highlighted index from
    self._frame_counter using the same construction as the shift-cue
    flash at manager.py:694-698, then issues eight draw_circle calls, one
    per dot, with the highlighted dot in a brighter colour and a slightly
    larger radius. All geometry is local to the method; no instance
    attribute is added. The body is wrapped so a drawing failure cannot
    take down the update view, matching the convention of every other
    draw helper in the file.

    EDIT 2 — call it from _draw_update_view. A single guarded call
    placed after the status message is rendered and before the button
    block, so the dots sit beneath the message and above where a button
    would be if the status presented one.

    No other line of the method changes. In particular the status-string
    selection, the button block and the hint text are untouched.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Add a frame-counter-driven eight-dot ring indicator and draw it
        on the update sub-view while a check is in flight.
      functions_affected:
        - "_draw_update_spinner"
        - "_draw_update_view"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "DisplayManager._frame_counter"
      impact: "Read only. Advanced once per frame in _display_loop at manager.py:451 by change-4c038bed; this change adds a second reader and no writer."
    - component: "DisplayManager._run_update_check"
      impact: "Unchanged. It writes _update_status from a worker thread, which is what gates the indicator on and off; that write already drives re-registration through the view key introduced by change-44bca479."
    - component: "RenderingEngine.draw_circle"
      impact: "Called from a new site. display/rendering/engine.py:516-526 is unmodified."
    - component: "task 7.3.6 (9ed1c77e), recommendations 12 to 14"
      impact: "Constrained by this change. Conditional rendering must treat the update view as always dirty while _update_status is 'checking', or the indicator will freeze — reproducing the very fault this change corrects. ai/task.md §7.6.1 carries no row for this; add one when 7.3.6 is authored."
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Unit tests on the development platform with SDL_VIDEODRIVER=dummy and
    a recording stub for the rendering engine, so every draw_circle call
    can be inspected for centre, radius and colour. Geometry claims are
    checked arithmetically rather than by eye. On-target confirmation for
    the visible effect.
  test_cases:
    - scenario: "Render 48 consecutive frames with _update_status 'checking', fps_limit 60, and _frame_counter incrementing by one per frame."
      expected_result: "The highlighted dot occupies each of the eight ring positions at least once."
    - scenario: "Render frame N and frame N + 8 with fps_limit 60."
      expected_result: "The highlighted index differs by exactly one, modulo eight."
    - scenario: "Render frame N and frame N + 1 with fps_limit 60."
      expected_result: "The highlighted index is unchanged for seven of every eight frame pairs."
    - scenario: "Render with _update_status set to each of 'idle', 'available', 'none', 'error' and 'pending'."
      expected_result: "No spinner dot is drawn in any of the five."
    - scenario: "Compute the distance from (240, 240) to the outermost pixel of the outermost dot."
      expected_result: "70 px, inside the 238 px viewport radius."
    - scenario: "Compare the spinner's vertical extent with the status message and hint text positions."
      expected_result: "Spinner occupies y 230 to 310. The message baseline area ends near y 197 and the hint is at y 410; no overlap."
    - scenario: "Render the update view with _update_status 'available' after a check completes."
      expected_result: "Install and cancel buttons are drawn exactly as before this change, and no dot is drawn."
    - scenario: "Force draw_circle to raise inside the spinner."
      expected_result: "Logged at ERROR with a traceback; _draw_update_view completes and the rest of the view still renders."
    - scenario: "Set fps_limit to 30 and render 24 frames."
      expected_result: "The highlighted index advances once every 4 frames, so a revolution still takes approximately 1.07 s."
  regression_scope:
    - "pytest tests/ — no new failures."
    - "Manual on target: Check for updates with no wheel staged; confirm the indicator turns and then 'No update found' with a Back button appears."
    - "Manual on target: Check for updates with a newer wheel staged; confirm the indicator turns and then Install and Cancel appear."
    - "Manual on target: long press during a check still returns to the options menu."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "_update_wheel is assigned only at manager.py:76, 1324 and 1339 and read only at manager.py:1349, unchanged from the current file."
    - "No new instance attribute is added to DisplayManager.__init__."
    - "time.monotonic and time.time do not appear in _draw_update_spinner."
    - "src/gtach/display/rendering/engine.py is unmodified."
    - "src/gtach/utils/updater.py is unmodified."
    - "No file other than src/gtach/display/manager.py is modified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — add _draw_update_spinner before _draw_update_view."
      owner: "Claude Code"
    - step: "EDIT 2 — call it from _draw_update_view under the 'checking' guard."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Unit tests against a recording rendering stub; verify the geometry arithmetically."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; confirm the indicator turns during a check and that the completed states are unchanged."
      owner: "William Watson"
  rollback_procedure: >
    Single file, single commit, additive. git revert restores the
    previous behaviour. No data, configuration or interface migration is
    involved.
  deployment_notes: >
    The effect is visible on the panel, so on-target confirmation takes
    one tap. Stage a wheel with bin/deploy.sh --stage to exercise the
    'available' path as well as the 'none' path.

verification:
  implemented_date: "2026-07-31"
  implemented_by: "Claude Code, per prompt-4c3c3e1f"
  verification_date: "2026-07-31"
  verified_by: "Claude Code"
  test_results: >
    Development platform only: macOS, Python 3.11.14, pygame 2.6.1, SDL
    dummy driver. The real DisplayManager render path was driven with a
    recording engine, so the geometry and phase below are read from the
    draw calls the code actually issued rather than asserted against its
    source. Sixty-five assertions, all passing. Left active pending
    on-target results per ai/task.md §8.2.1.

    Both edits applied and all fourteen success criteria met. No departure
    from the prompt's text was required.

    THE FINDING, CONFIRMED DIRECTLY. §7.8 asserts that consecutive frames
    of the checking view are identical, so a running check cannot be told
    from a hung application. Rendering 64 consecutive frames with
    _update_status 'checking' and recording every draw call:

      pre-change   1 distinct frame; 63 of 63 consecutive pairs identical
      post-change  8 distinct frames; 56 of 63 consecutive pairs identical

    The finding was exactly right: before this change the view was
    literally a still image. The 56 of 63 figure after is the 8-frame step
    appearing independently of the assertion that measures it — seven of
    every eight consecutive pairs are expected to match.

    AN ERROR IN THE PROMPT'S TEST MATRIX. Unit test 1 expects 48 frames at
    fps_limit 60 to highlight all eight positions. It cannot: the same
    document fixes the step at 8 frames and states that a revolution takes
    64. Forty-eight frames advance the index six times, covering six
    positions. The implementation follows the functional requirement, which
    is unambiguous — (frame_counter // step) % 8 with
    step = max(1, round(fps_limit / 8.0)) — and the test case is the error.
    The suite asserts both the six-position result at 48 frames and the
    eight-position result at 64, so the discrepancy is recorded rather than
    silently accommodated.

    Evidence by test case.

    Shape: eight circles per frame while checking, exactly one in
    (255, 255, 255) and seven in (90, 90, 110), every one of radius 6. The
    first dot is at (240, 236), the top of the ring. All eight lie within
    a pixel of a radius-34 circle centred at (240, 270) and occupy eight
    distinct octants.

    Placement: the outermost spinner pixel is 70.0 px from the viewport
    centre — 30 px of centre offset, 34 px of ring radius, 6 px of dot
    radius — against a 238 px viewport. The ring spans y 230 to 310, clear
    of the status message centred at y 180 and of the hint at y 410. The
    spinner registers no touch region.

    Phase: the index advances by exactly one between frame N and N + 8 at
    fps_limit 60, across a full revolution, and is unchanged for 56 of 64
    consecutive frame pairs. Frame 0 highlights the top dot and frame 64
    returns to it. At fps_limit 30 the step is 4 frames and a revolution
    still takes 32 frames — the same 1.07 s, which is the point of deriving
    the step from fps_limit. At fps_limit 4 the max(1, ...) holds the step
    at one frame. A frame counter of 10^12 + 3 still yields a valid index,
    so unbounded growth is harmless.

    Gating: no dot is drawn for 'idle', 'available', 'none', 'error' or
    'pending'. With 'available' the install and cancel buttons are drawn
    exactly as before, their labels unchanged, and no circle is issued.
    With 'checking' the status message and the hint are still drawn and no
    button is.

    Containment: with draw_circle patched to raise, exactly one ERROR is
    logged, it carries a traceback, it names the spinner, and the status
    message and hint text are still drawn — the indicator is decoration and
    fails as decoration.

    Scope: an AST comparison against the previous commit shows
    _draw_update_view is the only method that differs and
    _draw_update_spinner the only one added; __init__ is byte-identical, so
    no instance attribute was introduced; _register_update_view_regions is
    byte-identical. A line-level comparison of _draw_update_view shows only
    the guarded call and its comment were added and nothing removed, with
    the status-string selection, the title, the button block and the hint
    text all intact. self._update_wheel appears on the same four lines with
    the same text. time.monotonic, time.time and pygame.time do not appear
    in the new method. src/gtach/display/rendering/engine.py and
    src/gtach/utils/updater.py are unmodified.

    pytest tests/ — 11 passed, unchanged by this work.

    What this does not establish: how the ring reads on the panel at
    229 ppi, or that a real check is long enough for the animation to be
    seen. Both need the device.
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-4c3c3e1f"
      relationship: "resolves"

notes: >
  Task 7.3.13 in ai/task.md §7.3, released in v0.3.0 (§8.3). Per §8.2.1
  this change is left active when the code lands, pending a passing T06
  result; only prompt-4c3c3e1f closes on implementation.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-4c3c3e1f."
      - "Recorded _update_wheel as explicitly out of scope, against the source report's reading of it as a disabled spinner."
      - "Recorded the constraint this change places on task 7.3.6 under dependencies.internal."
  - version: "1.1"
    date: "2026-07-31"
    author: "Claude Code"
    changes:
      - "Status proposed -> implemented. Recorded implementation date, executor, verification date and development-platform test results."
      - "Recorded a direct confirmation of finding §7.8: 64 frames of the checking view were byte-identical before the change, 8 distinct after."
      - "Recorded an error in prompt-4c3c3e1f's test matrix — 48 frames at fps 60 cover six positions, not eight — and that the implementation follows the functional requirement instead."
      - "Recorded that __init__ is byte-identical, so no instance attribute was added, and that _update_wheel is untouched at all four occurrences."
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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-4c3c3e1f. Records `_update_wheel` as out of scope against the source report's misreading, and the constraint placed on task 7.3.6. |
| 1.1 | 2026-07-31 | Status proposed → implemented; development-platform test results recorded, including a direct confirmation of §7.8 and one error found in the prompt's test matrix. Left active pending on-target results. |
| 1.2 | 2026-08-07 | Status implemented → closed. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
