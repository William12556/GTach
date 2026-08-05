Created: 2026 August 04

# Change: Draw the Gauge Face Once, Cache the Glyphs, and Tessellate to the Arc

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-821919ce"
  title: "The RADIAL invariant layer is pre-rendered into a surface keyed by the state it depends on and blitted per frame; rendered text surfaces are cached by (text, size, colour); draw_donut_arc scales its vertex count with the sweep angle"
  date: "2026-08-04"
  author: "William Watson"
  status: "deferred"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-821919ce"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-821919ce"
  description: >
    Resolves issue-821919ce. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 findings
    §5.2, §5.3, §5.4 and §5.5 with §9.2 recommendations 9, 10 and 11.
    Task list reference ai/task.md §7.3.5. Cache-key obligations from
    ai/workspace/report/task-list-cross-check-discrepancies.md §7.0
    (discrepancy D3).

scope:
  summary: >
    Three independent efficiency changes. The gauge face is drawn once
    into a cached surface and blitted; text surfaces are memoised; arc
    tessellation becomes proportional to sweep. The cache is keyed, not
    singular, so the changes that will alter the layer cannot leave it
    stale.
  affected_components:
    - name: "DisplayManager._radial_static_layer"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._radial_layer_key"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "draw_donut_arc"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine.render_text"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "fps_limit and conditional frame skipping. Recommendations 12 and 13, task 7.3.6 (9ed1c77e)."
    - "The framebuffer write path. Recommendations 2, 3, 4, 6, 7, 8 — changes 66ef59a0 and 49b21ace, both landed."
    - "Instrumentation. Recommendations 15 to 18, change-0b00759c, landed."
    - "The band colours, the face palette and the shift-cue colours. Owned by 5014040c and 5012004e; this change reads them and keys on them."
    - "The centre disc, the indicator line and the fill arc. They vary per frame by definition and are drawn on top of the cached layer, not into it."
    - "Font caching in typography.py:191. Already present; this change caches rendered surfaces, which is a different thing."

rational:
  problem_statement: >
    Twenty-seven of the thirty-one primitives in a RADIAL frame, and
    eight of its nine text rasterisations, produce an identical result
    sixty times a second. Every donut arc is tessellated to 122
    vertices whether it spans 20 degrees or 300.
  proposed_solution: >
    Draw the invariant twenty-seven into a surface once, keyed by the
    state they depend on, and blit it. Memoise rendered text by its
    inputs. Make the vertex count a function of the sweep.
  alternatives_considered:
    - option: "A singular cached surface with an explicit invalidate() method."
      reason_rejected: >
        Simpler, and the failure mode is a stale gauge face that looks
        correct until a band or palette change is silently not drawn.
        Cross-check D3 §7.4 step 3 requires invalidate-on-key-change
        precisely because a caller that must remember to invalidate is
        a defect waiting to be filed. Rejected on that basis.
    - option: "Move this triple after 7.3.11 and 7.3.12 and take the singular cache."
      reason_rejected: >
        This is D3 §7.5's stated alternative and it is legitimate: with
        the band ring and the night palette already in place, the static
        set really would be static and the key unnecessary. Rejected
        because the ordering is not free either — deferring the report's
        largest single render saving behind three user-interface changes
        means v0.4.0 ships the appearance changes on an unoptimised
        renderer, and the frame-pacing work in 7.3.6 depends on this one.
        The key costs perhaps fifteen lines and removes the ordering
        constraint entirely.
    - option: "Cache text surfaces inside typography.py's FontManager rather than in the rendering engine."
      reason_rejected: >
        FontManager caches fonts by size, which is a different key. Text
        surfaces depend on the string and the colour as well, and the
        engine is where render_text already lives. Putting it in the
        engine also means the setup subsystem's text benefits without
        being modified.
    - option: "Pre-render the 71 centre-readout numerals eagerly at startup."
      reason_rejected: >
        The report proposes this. Rejected in favour of the general
        (text, size, colour) memoisation, which subsumes it: the
        readout's domain is small and it will populate itself within
        seconds of running. Eager pre-rendering costs startup time on a
        Pi Zero 2W for a benefit the lazy cache delivers anyway.
  benefits:
    - "Twenty-seven primitives per frame become one blit."
    - "Eight of nine text rasterisations per frame become dictionary lookups."
    - "Arc vertex work falls by roughly 85% on the short band segments, of which there are up to six per frame."
    - "The keyed cache means 5014040c and 5012004e cannot leave a stale face, whatever order they land in."
  risks:
    - risk: >
        ASSUMPTION A1 — that render cost is a material fraction of the
        frame budget. Unverified: the §7.5.3 baseline has not been
        collected.
      mitigation: >
        Take the reading before implementing. If RADIAL frames already
        complete well inside 16.67 ms, this change buys little and its
        medium risk is not justified — withdraw or defer it rather than
        proceeding. The section this invalidates is the whole document.
    - risk: >
        ASSUMPTION A2 — that the static layer dominates render cost
        rather than the framebuffer write path, which changes 66ef59a0
        and 49b21ace addressed to unmeasured effect.
      mitigation: >
        The same §7.5.3 reading distinguishes them, since 0b00759c now
        measures render time rather than loop period. If the write path
        dominates, this change's benefit is smaller than the report
        implies and rendering.efficiency section of the release note
        should say so.
    - risk: >
        ASSUMPTION A3 — that a third 921,600-byte surface is affordable.
      mitigation: >
        Arithmetic rather than assumption: three surfaces is 2.7 MB on a
        512 MB device. Recorded as an assumption only because the
        allocation is new and the Pi Zero 2W's headroom under systemd
        has not been measured. The memory figure logged by
        change-0b00759c's monitor confirms it in the same session.
    - risk: >
        An incomplete key leaves a stale layer — the exact failure D3
        exists to prevent.
      mitigation: >
        The key is a tuple compared on every use, and every element of
        the layer is traced to a key member in the change's
        implementation_approach. The night-toggle redraw is asserted
        explicitly per D3 §7.4 step 6.
    - risk: >
        An unbounded text cache grows without limit if a caller renders
        varying strings — the update view's status text, for instance.
      mitigation: >
        The cache is bounded with a defined eviction policy. Unbounded
        memoisation on a long-running embedded process is a leak with a
        polite name.
  benefits_measurement: >
    Primitives per RADIAL frame: 31 -> 5. Text rasterisations per frame:
    9 -> 1 on the first frame at a given RPM and 0 thereafter. Arc
    vertices for a 20-degree segment: 122 -> 8. Frame time: to be
    measured against the §7.5.3 baseline, which is the criterion that
    matters and the one not yet available.

technical_details:
  current_behavior: >
    _draw_radial_mode (manager.py:788-990) draws every element from
    primitives on each call. draw_donut_arc (839-860) uses
    num_points = 60 at 841. render_text (engine.py:269) calls
    font.render unconditionally.
  proposed_behavior: >
    _draw_radial_mode computes a key, rebuilds the static surface if it
    differs from the cached one, blits the surface, then draws the fill
    arc, the indicator, the centre disc and the readout. draw_donut_arc
    derives num_points from the sweep. render_text consults a bounded
    dictionary before rasterising.
  implementation_approach: >
    THREE INDEPENDENT PARTS. They may be implemented and reverted
    separately; only Part 1 carries the assumptions above.

    PART 1 — the keyed static layer.

    The key is a tuple naming everything the invariant layer depends on:

      (viewport geometry as (outer_radius, inner_radius, centre),
       the six RPMBands thresholds,
       the palette identity,
       the active band index)

    The last two are the D3 members. The palette identity is
    self._palette.name once 5012004e lands, and a constant before that.
    The active band index is meaningful only once 5014040c makes the
    ring's colour part of the layer — before that change the arc is
    drawn on top and the band does not enter the layer at all.

    BOTH MEMBERS ARE INCLUDED FROM THE OUTSET, per D3 §7.4 step 1 and 2,
    so that neither later change has to modify the key's shape — only
    what feeds it. This is the point of the keyed design: the two
    changes that follow extend the key's VALUES, not its STRUCTURE.

    Rebuild is invalidate-on-key-change, tested at the top of
    _draw_radial_mode:

        key = self._radial_layer_key()
        if key != self._radial_layer_cached_key:
            self._radial_static_layer = self._build_radial_static_layer()
            self._radial_layer_cached_key = key

    then blit and draw the four varying primitives.

    _build_radial_static_layer draws the twenty-seven invariant
    primitives onto a fresh surface — the same code as today, with the
    varying four omitted.

    PART 2 — the text surface cache, in engine.py. render_text consults
    a dict keyed by (text, id(font), colour) before calling
    font.render. Bounded at a few hundred entries with simple
    first-in eviction; the domain in practice is the 71 readout strings
    plus a handful of fixed labels.

    id(font) rather than the font object: pygame Font objects are not
    hashable by value, and FontManager caches them by size
    (typography.py:191) so the identity is stable for the process. This
    is a real subtlety and is recorded rather than left to be
    rediscovered.

    PART 3 — the tessellation. num_points becomes
    max(4, int(abs(sweep_deg) / 2.5)) where sweep_deg is derived from
    the arc's own angular extent. The floor of 4 keeps a degenerate
    sweep drawable.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Keyed static-layer cache added; _draw_radial_mode blits it and
        draws only the four varying primitives; draw_donut_arc scales
        its vertex count with sweep.
      functions_affected:
        - "_draw_radial_mode"
        - "_build_radial_static_layer"
        - "_radial_layer_key"
        - "draw_donut_arc"
      classes_affected:
        - "DisplayManager"
    - component: "DisplayRenderingEngine"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: "render_text memoises rasterised surfaces in a bounded cache."
      functions_affected:
        - "render_text"
      classes_affected:
        - "DisplayRenderingEngine"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "change-0b00759c"
      impact: "Shipped. Its frame_time_ms is the measurement this change is judged by, and the §7.5.3 baseline it makes meaningful is the gate."
    - component: "change-5014040c"
      impact: "Extends the key's active-band value once the ring's colour becomes part of the layer. The key's structure already accommodates it."
    - component: "change-5012004e"
      impact: "Extends the key's palette value. Same structural provision. D3 §7.4 step 6 requires the toggle redraw to be verified."
    - component: "change-9ed1c77e"
      impact: "Blocked by this change — conditional frame skipping is judged against the frame cost this change alters."
  external: []
  required_changes:
    - change_ref: "change-9ed1c77e"
      relationship: "blocks"
    - change_ref: "change-5014040c"
      relationship: "related"
    - change_ref: "change-5012004e"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with SDL_VIDEODRIVER=dummy. Correctness is asserted by
    pixel comparison of a rendered frame against the pre-change
    implementation at matched inputs — the strongest available check
    that a caching refactor changed nothing visible. Cache behaviour is
    asserted by counting calls to the underlying primitives.
  test_cases:
    - scenario: "A RADIAL frame at a fixed RPM, before and after the change."
      expected_result: "Pixel-identical."
    - scenario: "Frames at several RPMs across every band."
      expected_result: "Pixel-identical in each case."
    - scenario: "Two consecutive frames at the same key."
      expected_result: "_build_radial_static_layer called once."
    - scenario: "A frame after the RPMBands thresholds change."
      expected_result: "Rebuilt."
    - scenario: "A frame after the palette changes."
      expected_result: "Rebuilt — D3 §7.4 step 6. Not applicable until 5012004e lands; assert the key member responds regardless."
    - scenario: "A frame after the active band changes."
      expected_result: "Key differs; rebuild occurs."
    - scenario: "render_text with a repeated (text, font, colour)."
      expected_result: "font.render called once; the second call returns the cached surface."
    - scenario: "render_text with 500 distinct strings."
      expected_result: "The cache stays bounded; eviction occurs; no unbounded growth."
    - scenario: "render_text with the same string in two colours."
      expected_result: "Two distinct entries, two distinct surfaces."
    - scenario: "draw_donut_arc over sweeps of 300, 60 and 20 degrees."
      expected_result: "120, 24 and 8 points respectively."
    - scenario: "Chord deviation at r=232 for each of those."
      expected_result: "< 1 px in every case, computed."
    - scenario: "The rendered arc geometry, before and after Part 3."
      expected_result: "Visually identical; pixel differences confined to sub-pixel edge antialiasing."
    - scenario: "Memory after 10,000 frames."
      expected_result: "Stable — asserted via the monitor change-0b00759c added."
  regression_scope:
    - "tests/display/ — the display suite once populated per ai/task.md §8.2."
    - "On gtach.local: frame_time_ms compared against the §7.5.3 baseline. This is the criterion; it cannot be evaluated until that baseline exists."
    - "On gtach.local: the gauge face renders correctly after a band change and, once 5012004e lands, after a palette toggle."
    - "On gtach.local: memory is stable over a long run."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py src/gtach/display/rendering/engine.py passes."
    - "pytest tests/ passes with no new failures."
    - "A rendered frame is pixel-identical to the pre-change implementation at matched inputs."
    - "The layer key includes the palette and active-band members from the outset."
    - "The text cache is bounded."
    - "No invalidate() method exists — invalidation is by key comparison only."

implementation:
  implementation_steps:
    - step: "PRECONDITION: collect the §7.5.3 frame_time_ms baseline on gtach.local and record it here. If render cost is not material, stop and report rather than proceeding."
      owner: "William Watson"
    - step: "Part 3 — the tessellation scaling. Smallest and independent; land it first."
      owner: "Claude Code"
    - step: "Part 2 — the text surface cache in engine.py."
      owner: "Claude Code"
    - step: "Part 1 — the keyed static layer."
      owner: "Claude Code"
    - step: "Pixel-comparison tests against the pre-change implementation."
      owner: "Claude Code"
    - step: "Re-measure frame_time_ms on gtach.local and compare against the baseline."
      owner: "William Watson"
  rollback_procedure: >
    Three independent parts, ideally three commits. Any one can be
    reverted without the others. No data or configuration is involved.
  deployment_notes: >
    No visible change. The display must be pixel-identical; anything
    else is a defect in this change. Ships in v0.4.0 (ai/task.md §8.5)
    after the §7.5.3 baseline is in hand.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-9ed1c77e"
      relationship: "blocks"
    - change_ref: "change-5014040c"
      relationship: "related"
    - change_ref: "change-5012004e"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-821919ce"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-821919ce."
      - "Recorded the three assumptions arising from authoring ahead of the §7.5.3 baseline, each bound to what must be revised if the baseline contradicts it, and made collecting that baseline the first implementation step."
      - "Took D3's keyed-cache branch rather than its reordering alternative, and recorded why: the key removes the ordering constraint for about fifteen lines."
      - "Specified the key with the palette and active-band members present from the outset, so 5014040c and 5012004e extend its values rather than its structure."
      - "Recorded the id(font) subtlety in the text cache key, pygame Font objects not being hashable by value."
      - "Rejected the report's eager pre-render of the 71 numerals in favour of general lazy memoisation."
  - version: "1.1"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Status proposed -> deferred. This document's own withdrawal condition was met: it stated that if RADIAL frames already complete well inside the budget, the change buys little and its medium risk is not justified — withdraw or defer rather than proceed."
      - "The §7.5.3 baseline was collected on 2026-08-05 over 52 minutes and 297 samples (ai/task.md §9.11.6), and change-9ed1c77e Part 2 then reduced fps_limit to 30. Frames now complete at a 15.3 ms median against a 33.3 ms budget — 46% used, zero overruns in 32 samples at the new rate."
      - "Assumption A1 held when written and does not hold now. It was framed as 'render cost is a material fraction of the 16.67 ms budget', and at 60 Hz it consumed 88% of it with 32% of frames overrunning. At 30 Hz neither is true."
      - "The flicker that motivated the efficiency work is resolved (ai/task.md §9.11.7): no tearing, flashing or band thrash observed on the panel. The symptom this change would have served no longer exists."
      - "Deferred rather than rejected: the design is sound and the document is complete. A heavier render path, a slower target, or a measured GIL-contention problem would make it relevant again, and it can be implemented as authored."
      - "The prompt was never executed. Its gate — stop and report if render cost is not material — would have halted it, which is the gate working as intended."

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
| 1.0 | 2026-08-04 | Initial change document coupled to issue-821919ce. Specifies the keyed static layer, the bounded text-surface cache and the sweep-proportional tessellation, with the §7.5.3 baseline as the first implementation step. |
| 1.1 | 2026-08-05 | Status proposed → **deferred**. The §7.5.3 baseline was collected and `9ed1c77e` Part 2 reduced `fps_limit` to 30; frames now use 46% of budget with zero overruns and the flicker is resolved. This document's own withdrawal condition is met. Deferred, not rejected — the design is sound and implementable as authored should a heavier render path make it relevant. |

---

Copyright (c) 2026 William Watson. MIT License.
