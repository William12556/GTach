Created: 2026 August 04

# Issue: The Majority of Each RADIAL Frame Is Redrawn Sixty Times a Second to Produce an Identical Result

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-821919ce"
  title: "RADIAL redraws its invariant layer every frame, every text surface is rasterised afresh on every call, and draw_donut_arc tessellates a 20-degree segment with the same 122 vertices as a 300-degree arc"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "deferred"
  severity: "medium"
  type: "performance"
  iteration: 1
  coupled_docs:
    change_ref: "change-821919ce"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Findings §5.3 (Static Content Redrawn Every Frame), §5.2 (Overdraw),
    §5.4 (Uncached Text Rendering) and §5.5 (Arc Tessellation), with
    §9.2 recommendations 9, 10 and 11. Task list reference ai/task.md
    §7.3.5.

affected_scope:
  components:
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "draw_donut_arc"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayRenderingEngine.render_text"
      file_path: "src/gtach/display/rendering/engine.py"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: >
    Source checkout at 0.3.2. The quantitative claims are arithmetic on
    the source; the benefit cannot be measured without the §7.5.3
    baseline, which has not been collected. See technical_notes.
  steps:
    - "rec 9 §5.3 — read manager.py:864-972. Everything between the corner fill and the centre disc is a function of the viewport geometry and the RPMBands thresholds, not of the RPM."
    - "rec 9 §5.3 — identify the three elements that do vary: the coloured fill arc (manager.py:891-896), the white indicator line (956-964) and the centre disc with its readout (974-985)."
    - "rec 9 §5.2 — count the full-area fills: surface.fill at 864, the border circle via _draw_shift_border at 866, the r=232 ground at 867, the 300-degree headroom donut at 872, the 60-degree inert donut at 878, then up to six band donuts over the same annulus."
    - "rec 10 §5.4 — read engine.py:269. Every render_text call invokes font.render, which rasterises with anti-aliasing and allocates a surface. Fonts are cached (typography.py:191); rendered surfaces are not."
    - "rec 10 §5.4 — count the calls per RADIAL frame: seven tick numerals (manager.py:930), the 'RPM x 1000' label (969) and the centre readout (983). Nine."
    - "rec 11 §5.5 — read manager.py:841. num_points = 60 is fixed regardless of the arc's angular extent, so every donut is a 122-vertex polygon."
  frequency: "always"
  reproducibility_conditions: >
    Every frame, in RADIAL, unconditionally. The magnitude of the waste
    scales with fps_limit, which is 60 by default.
  preconditions: "None."
  test_data: >
    STATIC VERSUS VARYING, enumerated from the source rather than from
    the report, because the report's list predates 378703da:

      static: the corner fill, the border ring, the r=232 ground, the
      headroom arc, the inert bottom arc, two zone boundary lines, the
      inner edge ring, seven tick marks, seven numerals, six band
      boundary marks, the 'RPM x 1000' label — 27 primitives, nine of
      them text rasterisations;
      varying: the fill arc, the indicator line, the centre disc and
      its numeral — four primitives, one of them a text rasterisation.

    So roughly 87% of the primitives and eight of the nine text
    rasterisations are invariant.

    TESSELLATION. draw_donut_arc emits 2 * (num_points + 1) = 122
    vertices for any sweep. The report's proposed
    max(4, int(sweep_deg / 2.5)) gives 120 for the 300-degree headroom
    arc, 24 for the 60-degree inert arc, and 8 for a 20-degree band
    segment. At r=232 with 2.5-degree half-segments the chord deviation
    is 232 * (1 - cos 1.25 deg) = 0.055 px, well under a pixel, so the
    accuracy is preserved. The saving is concentrated in the short
    segments, of which there are up to six per frame.

    WHAT recommendation 10 MEANS AFTER 378703da. The report proposes
    pre-rendering "the 71 DIGITAL numerals" — the domain '0.0' to '7.0'
    against six text colours. change-378703da retires DIGITAL, so that
    call site is gone. But it also adds the same numeral to the RADIAL
    centre (manager.py:983 after that change), with the same 71-string
    domain and, after change-5014040c, a single colour rather than six.
    The recommendation therefore survives with a smaller cross product:
    71 strings x 1 colour x 1 size, not 71 x 6.
  error_output: "None. This is a cost finding, not a fault."

behavior:
  expected: >
    Work whose result cannot have changed is not repeated. Text that
    will be identical to the last frame's is not rasterised again. A
    polygon approximation uses a vertex count proportional to the arc it
    approximates.
  actual: >
    (a) rec 9, §5.3 and §5.2 — the whole gauge face is reconstructed
    from primitives on every frame. Twenty-seven primitives produce an
    identical result 60 times a second, over an area the report
    computes at more than 5x overdraw.

    (b) rec 10, §5.4 — nine text rasterisations per RADIAL frame, of
    which eight are of strings that never change. Each allocates a
    surface and anti-aliases glyphs on a Cortex-A53.

    (c) rec 11, §5.5 — every donut arc, from a 20-degree band segment
    to the 300-degree headroom arc, is built as a 122-vertex polygon.
  impact: >
    Frame time on the target is consumed by work with no effect on the
    output. The report links this to §4.5's frame-time jitter and to GIL
    contention with the OBD thread, so the cost is not confined to
    rendering.

    How much time is not known. See technical_notes — this issue is
    authored ahead of the measurement that would quantify it.
  workaround: >
    Reducing fps_limit lowers the total cost proportionally. That is
    recommendation 12 and belongs to task 7.3.6, not here.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) on Raspberry Pi Zero 2W, Cortex-A53"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    An immediate-mode drawing loop, which is the natural way to write a
    renderer and correct until the cost matters. Nothing distinguishes
    invariant from varying content because nothing needed to. The fixed
    tessellation constant is a reasonable default chosen for the longest
    arc and then applied to all.
  technical_notes: >
    AUTHORED AHEAD OF ITS GATING OBSERVATION — READ THIS FIRST.

    ai/task.md §8.1 records that this triple "cannot be authored
    correctly yet": it depends on §7.5.3, the frame_time_ms baseline,
    which is collected in the §8.4 observation session on gtach.local
    and has not been taken. The instrumentation that makes that figure
    meaningful shipped in change-0b00759c, so the measurement is
    available — it simply has not been made.

    This triple is nonetheless authored now, by explicit instruction.
    The consequence is recorded rather than concealed: the following
    are ASSUMPTIONS, not findings, and each is marked in
    change-821919ce with the section that must be revised if the
    baseline contradicts it.

      A1. That render cost is a material fraction of the 16.67 ms
          budget. If the baseline shows RADIAL frames completing in,
          say, 3 ms, the entire triple is optimisation without a
          problem and recommendation 9's medium risk buys nothing.
      A2. That the static layer dominates that cost, rather than the
          framebuffer write path — which change-66ef59a0 and
          change-49b21ace have already addressed and whose effect is
          also unmeasured.
      A3. That a 921,600-byte cached surface is affordable in RAM on a
          512 MB Pi Zero 2W alongside the existing back and main
          surfaces. This is arithmetic rather than assumption — three
          such surfaces is 2.7 MB — but the allocation is new.

    RECOMMENDED SEQUENCING NOTWITHSTANDING. Take the §7.5.3 reading
    before implementing this change even though the documents now
    exist. Authoring ahead of the measurement is recoverable; building
    a keyed cache into the render path ahead of it is the case §8.1
    warns about.

    THE CACHE KEY IS THE WHOLE DESIGN. Cross-check discrepancy D3
    (ai/workspace/report/task-list-cross-check-discrepancies.md §7.0)
    establishes that recommendation 9's static set is static only until
    7.3.11 and 7.3.12 land: change-5014040c makes the band a property
    of the ring, and change-5012004e varies every colour in the layer.
    D3's §7.4 requires this triple to specify a keyed cache rather than
    a singular one, and to name those two changes as extending the key.

    D3 also records, at its §7.2, that the recommended authoring order
    places 7.3.5 at step 6 and 7.3.11/7.3.12 at step 9 — so the cache
    is built before the changes that invalidate it, and the "7.3.5
    lands last" branch of the recorded dependency is not the branch
    taken. The keyed-cache branch is therefore mandatory, not optional.

    D3's §7.5 offers an alternative: move this triple after 7.3.12 and
    take the simpler singular cache. change-821919ce records the
    decision under alternatives_considered.

    ONE CORRECTION TO THE REPORT. §5.4's "71 DIGITAL numerals against
    six text colours" is superseded by change-378703da. See test_data:
    the domain survives at the RADIAL centre with one colour, so the
    pre-render is 71 surfaces rather than 426.
  related_issues:
    - issue_ref: "issue-5014040c"
      relationship: "related"
    - issue_ref: "issue-5012004e"
      relationship: "related"
    - issue_ref: "issue-9ed1c77e"
      relationship: "blocks"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Pre-render the RADIAL invariant layer into a surface keyed by the
    state it depends on, blit it per frame and draw only the four
    varying primitives on top. Cache rendered text surfaces by
    (text, size, colour). Scale draw_donut_arc's vertex count with the
    sweep angle. See change-821919ce.
  change_ref: "change-821919ce"
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
    A cache whose invalidation depends on every mutating caller
    remembering to call it is a defect waiting to be filed. A key
    compared on each use cannot be forgotten — which is why D3
    specifies a key rather than an invalidate() method.
  process_improvements: >
    This issue is a worked example of authoring ahead of a gating
    measurement. The assumptions are enumerated so that, when the
    §7.5.3 baseline is taken, each can be checked against it and the
    documents revised or withdrawn on evidence rather than re-argued
    from scratch.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "A rendered RADIAL frame is pixel-identical to the pre-change implementation at the same RPM, band and palette."
    - "The static layer is rebuilt when the key changes and not otherwise."
    - "The key includes viewport geometry, the RPMBands thresholds, and — once those changes land — the active band index and the palette variant."
    - "Toggling the night palette produces a full redraw on the next frame, not a stale blit."
    - "The text cache returns an identical surface for a repeated (text, size, colour) triple."
    - "The text cache is bounded and its eviction behaviour is defined."
    - "draw_donut_arc's vertex count varies with sweep; chord deviation at r=232 remains below 1 px for every sweep drawn."
    - "Arc geometry is visually identical to the pre-change implementation at every band."
    - "Measured frame_time_ms on gtach.local falls relative to the §7.5.3 baseline — the criterion that cannot be evaluated until that baseline exists."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-821919ce"
  test_refs: []

notes: >
  This is task 7.3.5 in ai/task.md §7.3 and step 6 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5), gated on the
  §7.5.3 baseline.

  issue_info.type is performance per ai/task.md §7.2: §5.x efficiency
  items take that type. Severity medium — a real and quantifiable waste,
  but the display functions correctly and the magnitude is unmeasured.

  This triple was authored ahead of its gating observation by explicit
  instruction, contrary to ai/task.md §8.1's reasoning. Three
  assumptions are enumerated in technical_notes and each is bound to the
  section of change-821919ce that must be revised if the §7.5.3 baseline
  contradicts it. Take that reading before implementing.

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
      - "Initial issue document from display-ui-graphics-review.md findings §5.2, §5.3, §5.4 and §5.5 with §9.2 recommendations 9, 10 and 11."
      - "Recorded that the triple is authored ahead of the §7.5.3 baseline contrary to ai/task.md §8.1, and enumerated three assumptions — that render cost is material, that the static layer dominates it, and that the cached surface is affordable — each bound to the change-document section requiring revision if the baseline contradicts it."
      - "Recorded that D3's keyed-cache branch is mandatory rather than optional, the recommended authoring order placing this triple before the two changes that invalidate the layer."
      - "Recorded one correction to the report: §5.4's 71 numerals against six colours becomes 71 against one, the DIGITAL call site having gone to change-378703da and the domain having survived at the RADIAL centre."
      - "Enumerated the static and varying primitive sets from current source rather than from the report, whose list predates 378703da."
  - version: "1.1"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Status open -> deferred. The waste this issue describes is real and unchanged — twenty-seven invariant primitives and eight invariant text rasterisations per frame — but it no longer costs anything the instrument needs."
      - "The §7.5.3 baseline was collected (ai/task.md §9.11.6) and change-9ed1c77e Part 2 halved the frame rate. Frames complete at a 15.3 ms median against a 33.3 ms budget, with zero overruns in 32 samples, and the flicker is resolved (§9.11.7)."
      - "Of the three assumptions recorded in technical_notes, A1 is now false: render cost is no longer a material fraction of the budget. A3 was confirmed at 37.1 MB steady. A2 was never isolated and now need not be."
      - "Deferred rather than closed. Nothing here was wrong; the measurement arrived after the analysis and moved the conclusion. The triple is complete and implementable should a heavier render path, a slower target or measured GIL contention make it relevant."
      - "This is the outcome ai/task.md §8.1 predicted when it recorded that this triple could not be authored correctly before its observation was taken."
  - version: "1.2"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Formally closed and moved to closed/ on William Watson's decision. This is closure of the deferral decision itself, not a claim of implementation: no static-layer surface cache, text-surface cache or vertex-count scaling exists in src/gtach as of this date (confirmed by source grep and git log — no commit implements any part of this triple). Status remains 'deferred', unchanged from v1.1; only the document's active/closed location changes, so it stops appearing as an open work item while remaining implementable per v1.1's stated condition."

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
| 1.0 | 2026-08-04 | Initial issue document from display review findings §5.2–§5.5 with recommendations 9, 10 and 11. Records the three assumptions arising from authoring ahead of the §7.5.3 baseline, the mandatory keyed-cache branch of D3, and the revised scope of the text pre-render after DIGITAL's retirement. |
| 1.1 | 2026-08-05 | Status open → deferred. The §7.5.3 baseline (frames at 15.3 ms median against a 33.3 ms budget, zero overruns) removed assumption A1; deferred, not closed, and implementable if conditions change. |
| 1.2 | 2026-08-07 | Formally closed and moved to `closed/` on William Watson's decision — closure of the deferral, not a claim of implementation. No caching code exists in source as of this date. |

---

Copyright (c) 2026 William Watson. MIT License.
