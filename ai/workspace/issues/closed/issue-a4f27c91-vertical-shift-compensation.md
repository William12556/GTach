Created: 2026 August 07

# Issue: Composed Frame Displayed ~8 px Above the Panel's Active Area

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-a4f27c91"
  title: "The composed 480x480 frame is displayed approximately 8 px higher than the panel's active area, clipping the top of circular UI elements and leaving a blank band at the bottom edge"
  date: "2026-08-07"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-a4f27c91"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Reported as visible border misalignment on gtach.local: top of the
    RADIAL shift-cue border barely visible, small gap at the bottom edge.
    Measured directly via a sequence of diagnostic pygame scripts writing
    test patterns to /dev/fb0, independent of GTach application code.

affected_scope:
  components:
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
  designs:
    - design_ref: "design-c9d0e1f2"
  version: "0.4.0"

reproduction:
  prerequisites: >
    GTach running or stopped on gtach.local with the HyperPixel 2.1 Round
    panel.
  steps:
    - "Observe the RADIAL mode shift-cue border (_draw_shift_border, manager.py), a circle centred at (240, 240) radius 244: the top arc is barely visible; a gap is visible between the bottom arc and the panel's physical edge."
    - "With GTach stopped, write a ring test pattern (concentric circles at radius 238/226, centred (240,240)) directly to /dev/fb0 via a standalone pygame script with SDL_VIDEODRIVER=dummy. The same asymmetry appears, confirming the shift is not introduced by GTach's own render path."
    - "Write a crosshair diagnostic with 2 px ticks labelled by absolute buffer row number near each edge (rows 0-40 and 439-479), plus explicit ROW 0 and ROW 479 markers, directly to /dev/fb0 by the same method."
    - "Observe that the ROW 0 marker is not visible and the lowest fully-visible tick is at row 10, with one further unlabelled tick (row 8) visible above it — placing the true cutoff at row 8. The ROW 479 marker remains visible at the bottom edge."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional. Reproduced identically through GTach's own render path
    and through an isolated pygame script with no GTach application code
    in the path, which rules out DisplayRenderingEngine's composition
    logic, DisplayManager's draw calls, and touch/gesture handling as the
    origin.
  preconditions: >
    480 x 480 circular HyperPixel 2.1 Round panel, legacy DPI fbdev path,
    /dev/fb0.
  test_data: >
    Crosshair diagnostic, 2 px tick resolution near each edge: rows 0-7 of
    the composed buffer are not visible on the panel; row 8 is the first
    visible row. Row 479 (the buffer's last row) remains visible at the
    bottom. Measured shift: approximately 8 px, direction: composed
    content displayed higher on the panel than the buffer's own geometry
    specifies.
  error_output: "None. No exception is raised; the framebuffer write reports success."

behavior:
  expected: >
    The 480 x 480 composed frame's row 0 should align with the panel's
    physical top edge and row 479 with its physical bottom edge, so a
    circle centred at the buffer's true centre (240, 240) appears centred
    on the round panel.
  actual: >
    The image is displayed approximately 8 px higher than the panel's
    active area. Rows 0-7 of the composed buffer fall above the visible
    area and are not shown; the panel's own bottom edge shows a blank
    band of comparable height, since the panel is a fixed 480-row device
    and the buffer's content, once shifted up, no longer reaches its
    physical bottom row.
  impact: >
    Every circular UI element drawn on the assumption of a true (240, 240)
    centre is rendered visibly off-centre on the physical device. The
    RADIAL shift-cue border (radius 244) is the most visible instance:
    thin or clipped near the top, with a gap near the bottom. Cosmetic
    only — no functional or touch-mapping impact has been observed or is
    expected, since touch calibration is independent of the framebuffer
    write path.
  workaround: "None."

environment:
  python_version: "3.9.2"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "2.6.1 (SDL 2.28.4)"
  domain: "domain_1"

analysis:
  root_cause: >
    Isolation testing places the origin below GTach's framebuffer-write
    boundary. A script with no GTach code in its path, writing directly
    to /dev/fb0, reproduces the identical ~8 px upward shift. This rules
    out DisplayRenderingEngine.write_to_framebuffer's composition and
    write logic, and everything above it in the render path, as the
    cause. The remaining candidate is a fixed DPI scan-window or
    panel-active-area offset specific to this HyperPixel 2.1 Round
    unit's driver/hardware combination.
  technical_notes: >
    A published report of the identical symptom on the identical panel
    model, using the identical dpi_timings string present in
    docs/pi-setup.md, recorded that adjusting dpi_timings had no effect
    on the misalignment (Pimoroni Buccaneers forum, "Content not in
    center of HyperPixel 2.1 Round", accessed 2026-08-07). A related
    report attributes a similar-sounding symptom on pre-Pi4 boards to an
    outdated bundled pygame/SDL build; this was checked and ruled out
    here, since gtach.local runs pygame 2.6.1 / SDL 2.28.4, which is
    current.

    Given dpi_timings adjustment is not established as effective for this
    panel, and a boot-time config.txt change to a headless,
    network-only-accessible device carries a risk of losing all access
    if the panel fails to initialise, compensating the known, measured
    offset in software at the framebuffer-write boundary is the lower-risk
    path. A config.txt backup (/boot/config.txt.bak) has been taken
    independently of this issue, in case DPI timing adjustment is
    attempted separately in future.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Compensate the measured offset in DisplayRenderingEngine.write_to_framebuffer:
    prepend blank rows equal to the measured offset and drop the same
    number of trailing rows from the composed payload before it is
    written to /dev/fb0. Confined to the framebuffer-write boundary; no
    change to the composition surface, draw calls, touch coordinate
    mapping, or any component outside this method. See change-a4f27c91.
  change_ref: "change-a4f27c91"
  resolved_date: "2026-08-07"
  resolved_by: "Claude Code, per prompt-a4f27c91"
  fix_description: >
    VERTICAL_OFFSET_PX = 8 added as a class-level constant on
    DisplayRenderingEngine (engine.py:73), citing this issue. A row-shift
    step added to write_to_framebuffer between the existing
    size-reconciliation block and the write-branch dispatch: computes
    row_bytes from self.fb_line_length (falling back to
    self.surface_size[0] * 4), then shift_bytes = row_bytes *
    VERTICAL_OFFSET_PX; when 0 < shift_bytes < payload length, replaces
    payload with bytes(shift_bytes) + payload[:-shift_bytes], preserving
    total length. Both the page-flip and single-buffer write branches
    consume the same payload variable. Falls through to the original
    unshifted payload on any exception or out-of-range shift_bytes, so
    the compensation can never turn a successful write into a failed one.
    Confirmed present in source at engine.py:73, 109-110, 670-782.

verification:
  verified_date: "2026-08-07"
  verified_by: "William Watson"
  test_results: >
    pytest tests/ — 19 passed (baseline 11, +8 new test cases in
    tests/display/rendering/test_engine.py), 0 failed. python -m
    py_compile src/gtach/display/rendering/engine.py passes. Full detail
    in ai/workspace/report/v0.4.0-a4f27c91-vertical-shift-compensation.md.

    On-target: GTach deployed to gtach.local; William confirmed the
    display now appears centred. This satisfies the primary symmetry
    check in verification_enhanced below; the itemised crosshair
    re-measurement and explicit bottom-margin check were not run
    separately, superseded by direct visual confirmation on the actual
    UI (the RADIAL shift-cue border) rather than the diagnostic pattern.
  closure_notes: >
    Closed on William Watson's on-target confirmation. Two follow-up
    items raised in the implementation report — possible touch-
    calibration offset from the shifted display, and the unmeasured
    per-frame cost of the row-shift copy — are not defects in this fix
    and do not block closure; recorded as ai/task.md §4.4 and §4.5 for
    separate investigation.

prevention:
  preventive_measures: >
    A rendering symmetry defect on this hardware should be isolated
    against a test pattern written independently of GTach's own render
    path before being attributed to application code. This issue was
    diagnosed with exactly that method before authoring.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "On gtach.local, with GTach stopped: re-run the 2 px-resolution crosshair diagnostic, this time writing through DisplayRenderingEngine.write_to_framebuffer directly (a short harness constructing the engine and one composed crosshair frame is acceptable), and confirm row 0 is now visible at the panel's physical top edge."
    - "Confirm the panel's true bottom edge shows no more than a 1-2 px blank margin in the same test."
    - "On gtach.local: confirm the RADIAL shift-cue border (_draw_shift_border, manager.py) appears visually centred, with no visible clipping at the top and no visible gap at the bottom."
    - "Confirm no code outside DisplayRenderingEngine.write_to_framebuffer in src/gtach/display/rendering/engine.py is modified."
    - "pytest tests/ passes, unchanged count from the pre-change baseline."
  verification_results: ""

traceability:
  design_refs:
    - "design-c9d0e1f2"
  change_refs:
    - "change-a4f27c91"
  test_refs: []

notes: >
  Measurement history, for reference against the fix: a coarse
  10 px-labelled crosshair first placed the cutoff between rows 0 and 20;
  a 2 px-resolution crosshair near each edge narrowed this to row 8 as
  the first visible row. The fix should use the row-8 figure. If the
  on-target verification step finds a residual clipping or gap of a few
  pixels, the compensation constant should be adjusted directly rather
  than reopening the diagnostic sequence, since the isolation and
  measurement method is already established.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Initial issue document. Root cause isolated by direct /dev/fb0 diagnostic scripts, independent of GTach application code. Offset measured at 8 px via 2 px-resolution edge crosshair."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status open -> closed. Resolution, verification and closure_notes recorded following implementation (prompt-a4f27c91) and William Watson's on-target confirmation that the display appears centred on gtach.local. Source cross-checked against the implementation report before closure. Two follow-up items (touch calibration, per-frame cost) recorded in ai/task.md §4.4-4.5 rather than blocking closure."
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
| 1.0 | 2026-08-07 | Initial issue document. Root cause isolated to below GTach's framebuffer-write boundary via direct /dev/fb0 diagnostics; offset measured at 8 px. |
| 1.1 | 2026-08-07 | Status open → closed. Closed on William Watson's on-target confirmation the display appears centred; source cross-checked against the implementation report. Follow-up items recorded in ai/task.md §4.4-4.5. |

---

Copyright (c) 2026 William Watson. MIT License.
