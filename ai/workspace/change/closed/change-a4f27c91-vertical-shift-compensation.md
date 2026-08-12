Created: 2026 August 07

# Change: Compensate 8 px Vertical Shift in Framebuffer Write

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-a4f27c91"
  title: "Compensate the measured 8 px vertical panel offset in DisplayRenderingEngine.write_to_framebuffer"
  date: "2026-08-07"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a4f27c91"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-a4f27c91"
  description: >
    The composed 480x480 frame is displayed approximately 8 px higher
    than the HyperPixel 2.1 Round panel's active area. Isolation testing
    places the cause below GTach's framebuffer-write boundary; a
    dpi_timings adjustment is not established as effective for this
    panel per a published report of the identical symptom. Software
    compensation at the framebuffer-write boundary is the lower-risk
    remedy.

scope:
  summary: >
    Add a single, named vertical-offset compensation to
    DisplayRenderingEngine.write_to_framebuffer: blank rows equal to the
    measured offset are prepended to the payload written to /dev/fb0,
    and the same number of trailing rows are dropped, so the visible
    image shifts down on the panel by the offset without changing the
    total bytes written.
  affected_components:
    - name: "DisplayRenderingEngine"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-c9d0e1f2"
      sections:
        - "Framebuffer write path"
  out_of_scope:
    - "dpi_timings / config.txt changes — not pursued; a published report of the identical symptom on the identical panel and dpi_timings string found timing adjustment ineffective, and a boot-time config change on a headless, network-only device carries availability risk disproportionate to a cosmetic defect."
    - "Any change to DisplayRenderingEngine's composition surface, draw calls, touch coordinate mapping, TouchEventCoordinator, or any component outside write_to_framebuffer."
    - "Runtime configurability of the offset (e.g. via config.yaml). The offset is a fixed property of one physical panel/driver combination on one deployment target, not a user-facing setting."

rational:
  problem_statement: >
    Circular UI elements drawn on the assumption of a true (240, 240)
    frame centre — most visibly the RADIAL shift-cue border — are
    rendered visibly off-centre on the physical panel: clipped near the
    top, with a gap near the bottom, because the composed frame is
    displayed roughly 8 px higher than the panel's active area.
  proposed_solution: >
    Compensate at the framebuffer-write boundary, the single point where
    all rendered output already passes before reaching hardware. Before
    the existing write, prepend row_bytes * OFFSET_PX bytes of black and
    drop the same number of bytes from the end of the payload, where
    row_bytes is the established per-row stride (self.fb_line_length,
    already computed by _query_framebuffer_geometry) and OFFSET_PX is a
    new named constant set to 8.
  alternatives_considered:
    - option: "Adjust dpi_timings in /boot/config.txt (v_back_porch / v_front_porch reallocation)."
      reason_rejected: >
        Mathematically constrained — v_front_porch has only 15 to give,
        insufficient for an 8-20 px shift depending on measurement
        round-trip, and a published report of the identical symptom on
        the identical panel and dpi_timings string found the adjustment
        had no effect. Also carries boot-availability risk on a headless
        device with no attached display for live recovery.
    - option: "Shift the composed drawing coordinates in DisplayManager (e.g. offset every draw call by 8 px)."
      reason_rejected: >
        Would require touching every draw call site across manager.py,
        splash.py, setup.py and typography.py, multiplying the change
        surface for a single physical constant that only matters at the
        point of hardware output. The framebuffer-write boundary is the
        single existing chokepoint all output already passes through.
  benefits:
    - "Circular UI elements appear correctly centred on the physical panel."
    - "Single point of change, confined to one method already responsible for hardware-specific output handling."
    - "No risk to boot availability, unlike a config.txt route."
  risks:
    - risk: "The measured 8 px figure could be imprecise; residual clipping or gap of a few pixels may remain after the fix."
      mitigation: "On-target verification re-runs the same crosshair diagnostic against the corrected output; the constant is a single named value and can be adjusted directly if the residual is visible."
    - risk: "A row-based byte shift assumes the payload is tightly packed, top-to-bottom, at self.fb_line_length bytes per row with no additional per-frame header."
      mitigation: "This assumption already holds for the existing unmodified write path (payload is written directly via fb.seek(0)/fb.write with no header), so it introduces no new assumption not already relied upon by the current code."

technical_details:
  current_behavior: >
    write_to_framebuffer obtains a buffer-protocol view of back_surface
    (or a per-frame copy on fallback), reconciles it against
    self.fb_size if the size mismatches, and writes it directly to
    /dev/fb0 (or the appropriate half, under page flip) starting at
    the beginning of the target region. No vertical offset is applied.
  proposed_behavior: >
    Immediately before the existing size-reconciliation/write block, the
    payload is reduced by OFFSET_PX rows from its end and prefixed with
    OFFSET_PX rows of zero bytes, so its total length is unchanged. The
    existing write logic (page-flip and single-buffer paths, size
    mismatch handling, vsync wait) is otherwise untouched and operates
    on the adjusted payload exactly as it does today on the unadjusted
    one.
  implementation_approach: >
    Add a class-level named constant, e.g.
    `VERTICAL_OFFSET_PX = 8  # measured on gtach.local, issue-a4f27c91`,
    near the existing HyperPixel display constants in __init__
    (display_center, display_safe_radius, display_max_radius) or as a
    module-level constant alongside the FB_VAR_* constants — the exact
    placement is Claude Code's judgement, consistent with the file's
    existing constant style.

    In write_to_framebuffer, after `payload` is obtained (and after the
    existing size-reconciliation block, so the adjustment always
    operates on a payload already known to be exactly self.fb_size
    bytes), compute:

      row_bytes = self.fb_line_length or (self.surface_size[0] * 4)
      shift_bytes = row_bytes * VERTICAL_OFFSET_PX

    and, if shift_bytes is within the payload's length, materialise the
    adjusted payload as `bytes(shift_bytes) + payload[:-shift_bytes] if
    shift_bytes else payload` (or equivalent), before the existing
    fb.seek/fb.write calls. If shift_bytes is zero, non-positive, or
    exceeds the payload length, skip the adjustment and write the
    original payload — the existing behaviour is always a safe fallback.

    This does apply an unconditional bytes() materialisation of the
    payload each frame, in the case where VERTICAL_OFFSET_PX is nonzero
    — the existing get_view('0') fast path is used to construct the
    slice, so the zero-copy path is preserved except for the necessary
    row-shift copy itself.
  code_changes:
    - component: "DisplayRenderingEngine"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: >
        Add VERTICAL_OFFSET_PX constant; add a row-shift step in
        write_to_framebuffer between the existing size-reconciliation
        block and the existing write block.
      functions_affected:
        - "write_to_framebuffer"
      classes_affected:
        - "DisplayRenderingEngine"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "DisplayManager"
      impact: "None. DisplayManager calls write_to_framebuffer with the same signature and receives the same bool return; no caller-visible change."
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Development-platform unit test constructs a DisplayRenderingEngine
    with a stubbed/mock framebuffer object (consistent with the existing
    test approach for this component, per governance's
    development-platform testing precedent), composes a known payload
    with a distinguishable pattern at row 0 and row (height-1), calls
    write_to_framebuffer, and asserts the bytes written begin with
    VERTICAL_OFFSET_PX rows of zero followed by the original row 0. On-target
    verification against the physical panel is required per
    issue-a4f27c91 verification_enhanced, since the defect itself was
    only observable on hardware.
  test_cases:
    - scenario: "VERTICAL_OFFSET_PX rows of zero precede the original payload's first row in the bytes written to the framebuffer object."
      expected_result: "Assertion passes against the mock framebuffer's captured write() argument."
    - scenario: "Total bytes written remains exactly self.fb_size, unchanged from the pre-change behaviour."
      expected_result: "len(written_payload) == self.fb_size."
    - scenario: "Page-flip path (self.page_flip True) applies the same row-shift before writing to the target half."
      expected_result: "Mock framebuffer receives the shifted payload at the correct seek offset (target * self.fb_size)."
    - scenario: "shift_bytes computed as zero or exceeding payload length is handled without exception (defensive fallback)."
      expected_result: "Original unmodified payload is written; no exception raised."
  regression_scope:
    - "Existing write_to_framebuffer tests (size-mismatch handling, page-flip target selection, vsync wait) continue to pass unmodified."
  validation_criteria:
    - "pytest tests/ passes with count unchanged from baseline plus the new test cases in this change."
    - "On gtach.local: crosshair diagnostic through the corrected write path shows row 0 visible at the panel's top edge and no more than a 1-2 px residual margin at the bottom."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Add VERTICAL_OFFSET_PX constant with a comment citing issue-a4f27c91 and the measurement method."
      owner: "Claude Code"
    - step: "Add the row-shift computation and payload adjustment in write_to_framebuffer, after size reconciliation and before the existing write calls (both page-flip and single-buffer branches)."
      owner: "Claude Code"
    - step: "Add the four unit test cases against a mock framebuffer."
      owner: "Claude Code"
  rollback_procedure: >
    Revert the single commit. No data migration, no config.txt
    involvement, no interface change — a plain git revert restores prior
    behaviour.
  deployment_notes: >
    Standard GTach deploy workflow: build wheel on Mac, scp to
    root@gtach.local:/tmp/, install via /opt/gtach/install.sh. On-target
    verification (crosshair diagnostic, visual border check) required
    before this change is considered verified, per issue-a4f27c91.

verification:
  implemented_date: "2026-08-07"
  implemented_by: "Claude Code, per prompt-a4f27c91"
  verification_date: "2026-08-07"
  verified_by: "William Watson"
  test_results: >
    pytest tests/ — 19 passed (baseline 11, +8 new cases in the new file
    tests/display/rendering/test_engine.py), 0 failed. python -m
    py_compile src/gtach/display/rendering/engine.py passes. Source
    cross-checked directly: VERTICAL_OFFSET_PX = 8 at engine.py:73,
    one-time logging flags at 109-110, shift block at 670-782, both
    write branches confirmed consuming the same payload variable. Full
    detail: ai/workspace/report/v0.4.0-a4f27c91-vertical-shift-compensation.md.

    On-target: GTach deployed to gtach.local; William Watson confirmed
    the display now appears centred.
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-a4f27c91"
      relationship: "resolves"

notes: >
  VERTICAL_OFFSET_PX is set to 8 on the evidence in issue-a4f27c91. This
  is a measured physical constant for one deployment target (gtach.local
  with its specific HyperPixel 2.1 Round unit), not a general property of
  the panel model — a different physical unit could in principle measure
  differently, though no such variation is currently in evidence.

  Two follow-up items surfaced during implementation, neither blocking
  this closure: possible touch-calibration offset (the digitiser's own
  mapping was not shifted along with the image) and unmeasured per-frame
  cost of the row-shift copy (now unconditional on every frame rather
  than only on the pre-existing size-mismatch fallback path). Both
  recorded as ai/task.md §4.4 and §4.5.

version_history:
  - version: "1.0"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Initial change document, coupled to issue-a4f27c91."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status proposed -> closed. Implementation and verification recorded following prompt-a4f27c91 and William Watson's on-target confirmation. Source cross-checked against the implementation report before closure. Two follow-up items recorded in ai/task.md §4.4-4.5."
      - "Moved to ai/workspace/change/closed/."

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
| 1.0 | 2026-08-07 | Initial change document, coupled to issue-a4f27c91. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implemented and verified per prompt-a4f27c91 and William Watson's on-target confirmation. Follow-up items recorded in ai/task.md §4.4-4.5. |

---

Copyright (c) 2026 William Watson. MIT License.
