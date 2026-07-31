Created: 2026 July 30

# Issue: Update Check Presents a Static String for an Operation of Indeterminate Duration

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-4c3c3e1f"
  title: "_draw_update_view renders a fixed 'Checking…' string while a worker scans and CRC-validates candidate wheels, so a slow or stalled check is indistinguishable from a hung application"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-4c3c3e1f"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Finding §7.8 (Update View Has No Progress Feedback); recommendation 28
    (§9.5), "Add an animated indicator to the update-check view".
    Task list reference: ai/task.md §7.3.13.

affected_scope:
  components:
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_update_spinner"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.2.67"

reproduction:
  prerequisites: >
    GTach running on gtach.local with the HyperPixel 2.1 Round panel, and
    at least one candidate wheel present in /opt/gtach/updates.
  steps:
    - "Enter the OPTIONS screen and tap Check for updates."
    - "_on_check_updates (manager.py:1319) sets _options_view to 'update' and _update_status to 'checking', then submits _run_update_check to the worker pool (manager.py:1326)."
    - "Observe the panel while the worker runs. The view shows the fixed string 'Checking…' (manager.py:1235) and nothing else changes."
    - "Observe that no control is registered while the status is 'checking' — _register_update_view_regions registers install and cancel only for 'available' and a single back button for 'none' or 'error' (manager.py:1124-1134)."
    - "There is therefore no on-screen element that changes and no control to press. The screen is byte-identical frame to frame."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional whenever _update_status is 'checking'. The operator
    perceives it as a fault only when the check takes long enough to be
    noticed, which depends on the number and size of the wheels in
    /opt/gtach/updates.
  preconditions: >
    480 x 480 circular panel, viewport radius 238 px, centre (240, 240),
    fps_limit 60. The update sub-view is reached from
    DisplayMode.OPTIONS with _options_view == 'update'.
  test_data: >
    Current update-view layout, read from source rather than assumed.
    Title 'Update' at (240, 80) (manager.py:1232). Status message at
    (240, 180) with a 26 px font (manager.py:1245-1247). Buttons, when a
    status presents them, at y 240 and y 320 for install and cancel, or
    y 300 for back, each 280 x 60 (manager.py:1124-1134). Hint text
    'Long press to return' at (240, 410) (manager.py:1275). The band
    between y = 210 and y = 390 is unoccupied while the status is
    'checking', because that status registers and draws no button.
  error_output: "None. No exception is raised; the view is simply static."

behavior:
  expected: >
    While a check is in flight, the view carries a moving element, so the
    operator can distinguish a running check from a stalled application
    without a second source of information.
  actual: >
    _draw_update_view (manager.py:1225-1275) selects one of five fixed
    strings from _update_status (manager.py:1234-1243) and renders it at
    (240, 180). For the 'checking' branch the string is 'Checking…' and
    the whole surface is redrawn identically on every frame. Nothing on
    the panel changes for the duration of the check, and no control is
    registered, so the screen offers neither progress information nor an
    escape other than the long press.
  impact: >
    Diagnostic only; no data is lost and no function is unavailable. The
    operator cannot tell a slow check from a hung one and has no basis for
    deciding how long to wait before power-cycling the unit. On a display
    whose whole purpose is at-a-glance status, a screen that cannot
    distinguish "working" from "dead" is a gap in the same class as the
    invisible connection indicator corrected under issue-44bca479.
  workaround: >
    Long press returns to the options menu. The check itself continues in
    the worker pool and its result is discarded, since _on_cancel_update
    resets _update_status to 'idle' (manager.py:1362-1365).

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    The update view was authored under change-f993f871 as a status
    display driven by a single string variable. A string cannot express
    an operation in progress, and no animation primitive existed on the
    view at the time it was written.
  technical_notes: >
    THREE CORRECTIONS TO THE SOURCE REPORT. Each was found by reading
    src/gtach at 0.2.67; none changes the finding, and all three change
    the reasoning that supports it, so they are recorded rather than
    silently followed.

    (1) The report states that "self._update_wheel is set to None and
    never used as a spinner despite the field name". The field is not a
    spinner and its name does not refer to one. _update_wheel holds the
    filename of a Python wheel distribution. _run_update_check assigns it
    from updater.find_available_update() at manager.py:1339, and
    _on_confirm_install passes it to updater.stage_pending() at
    manager.py:1349. The assignment of None at manager.py:1324 is a reset
    before a new check, not a disabled animation. find_available_update
    is declared as returning Optional[Tuple[str, str]] — (filename,
    version_str) — at utils/updater.py:65. The field must not be
    repurposed; doing so would break the install path.

    (2) The report states that "a network check has indeterminate
    duration". There is no network check. updater.find_available_update
    (utils/updater.py:65-93) lists the local directory /opt/gtach/updates
    (utils/updater.py:23, 76), parses a version from each .whl filename,
    and calls validate_wheel on each candidate strictly newer than the
    installed version. validate_wheel (utils/updater.py:54-62) opens the
    file with zipfile.ZipFile and calls testzip(), which decompresses and
    CRC-checks every member of the archive. The module docstring states
    the same: "Pure filesystem logic" (utils/updater.py:11).

    The finding nevertheless stands, for a corrected reason. The check's
    duration is not indeterminate but it is unbounded in practice and
    unknown to the operator: it is proportional to the number of
    candidate wheels and to the compressed size of each, and a full CRC
    pass over a multi-megabyte wheel on a Pi Zero 2W is a matter of
    seconds, not milliseconds. It also runs on the ThreadManager worker
    pool (manager.py:1326), which has three workers (core/thread.py:81,
    97-100) shared with thread-restart work, so the check can additionally
    be queued behind unrelated work before it starts. A static string is
    an inadequate indication for an operation with that profile.

    (3) Line drift. The report cites manager.py:958 for the 'Checking…'
    string. It is at manager.py:1235 at 0.2.67. The report was written
    against 0.2.64, before change-44bca479 moved touch registration out
    of the render path and added the registration helpers. Report line
    references in this area are not usable without re-checking.

    IMPLEMENTATION NOTE — the animation must be driven by the frame
    counter, not by wall-clock time. change-4c038bed established that
    pattern for the shift cue at manager.py:694-698, with the recorded
    rationale that the duty cycle is then "equal by construction at any
    frame rate". self._frame_counter is advanced once per frame in
    _display_loop at manager.py:451 and is already available. Using
    time.monotonic() here would produce a second, independent timebase on
    the same surface.

    IMPLEMENTATION NOTE — the rendering engine offers no arc primitive.
    Its drawing surface is clear_surface, draw_circle, draw_rect,
    draw_line, blit_surface and render_text
    (display/rendering/engine.py:504-616). An animated indicator must
    therefore be composed from those, and a ring of dots with one
    highlighted is the least machinery that satisfies the recommendation.
    Adding a draw_arc to the engine for this purpose is not warranted.

    CONSEQUENCE FOR TASK 7.3.6. Recommendations 12 to 14 propose
    conditional rendering — skipping a frame when nothing has changed.
    A permanently animated element means the update view can never be
    skipped while a check is in flight. ai/task.md §7.6.1 does not record
    this relationship. It is recorded here, and in change-4c3c3e1f under
    dependencies.internal, so that whoever authors 7.3.6 sees it.
  related_issues:
    - issue_ref: "issue-44bca479"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Add a private _draw_update_spinner method to DisplayManager that
    draws a ring of eight dots below the status message, advancing the
    highlighted dot from self._frame_counter, and call it from
    _draw_update_view only while _update_status is 'checking'. No new
    instance state, no change to _update_wheel, no change to the update
    workflow. See change-4c3c3e1f.
  change_ref: "change-4c3c3e1f"
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
    A view that represents an asynchronous operation should carry a
    moving element for the duration of that operation, chosen when the
    view is designed rather than retrofitted. A field name should
    describe what the field holds; _update_wheel holds a wheel filename
    and was read by a reviewer as a spinner, which is the whole of the
    report's first error here.
  process_improvements: >
    Report findings that assert a field is unused should be checked
    against the field's write and read sites before the finding is
    accepted. In this case one grep would have shown two live uses.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "Confirm _update_wheel is still assigned at manager.py:1339 and read at manager.py:1349, and that neither line is modified."
    - "Unit test: with _update_status 'checking', render 48 consecutive frames with _frame_counter incrementing and confirm the set of highlighted dot centres covers all eight positions."
    - "Unit test: with _update_status 'checking', confirm the highlighted dot centre differs between frame N and frame N + 8 at fps_limit 60."
    - "Unit test: with _update_status in ('idle', 'available', 'none', 'error', 'pending'), confirm no spinner dot is drawn."
    - "Compute the distance of the outermost spinner pixel from the viewport centre and confirm it is inside 238 px."
    - "Confirm the spinner does not overlap the status message bounding box at (240, 180) or the hint text at (240, 410)."
    - "On gtach.local: tap Check for updates with a wheel staged in /opt/gtach/updates and confirm the indicator turns for the duration of the check."
    - "On gtach.local: confirm the install and cancel buttons appear unchanged when the check completes with 'available', and that no spinner remains."
  verification_results: ""

traceability:
  design_refs:
    - "design-b8c9d0e1-component_display_manager"
  change_refs:
    - "change-4c3c3e1f"
  test_refs: []

notes: >
  This is task 7.3.13 in ai/task.md §7.3 and the last of the display
  triples in the v0.3.0 batch (§8.3). It is step 9 in the recommended
  authoring order (§7.6.2), being a user interface change.

  Per ai/task.md §8.2.1 this issue is to be left active when the code
  lands, pending a passing T06 result. Only the coupled prompt closes on
  implementation.

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
      - "Initial issue document from display-ui-graphics-review.md finding §7.8 and recommendation 28."
      - "Recorded three corrections to the source report: _update_wheel is a live field holding a wheel filename and not an unused spinner; the check is a local filesystem and CRC operation, not a network call; the cited line 958 is 1235 at 0.2.67."
      - "Recorded the consequence for task 7.3.6, which ai/task.md §7.6.1 does not carry."

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
| 1.0 | 2026-07-30 | Initial issue document from display-ui-graphics-review.md finding §7.8 and recommendation 28, with three recorded corrections to the source report and a note on the consequence for task 7.3.6. |

---

Copyright (c) 2026 William Watson. MIT License.
