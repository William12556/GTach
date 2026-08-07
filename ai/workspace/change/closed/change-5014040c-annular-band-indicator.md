Created: 2026 August 04

# Change: A Dark Gauge Face with the Band Carried by the Ring

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-5014040c"
  title: "RADIAL's r=232 ground becomes a fixed dark fill, ticks and numerals are re-coloured for it, the coloured fill arc becomes the sole band indicator, and _get_band_colour returns a band index and one colour instead of a background/text pair"
  date: "2026-08-04"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-5014040c"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-5014040c"
  description: >
    Resolves issue-5014040c. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 finding §7.2
    with §9.5 recommendation 26, scoped by ai/task.md §7.3.14. Task list
    reference ai/task.md §7.3.11.

scope:
  summary: >
    The gauge face stops being a bright surface. The r=232 ground
    becomes dark, the ticks and numerals invert to suit it, the existing
    coloured arc becomes the band cue in its own right, and
    _get_band_colour sheds the text-colour half of its return value,
    which lost its only consumer when DIGITAL was retired.
  affected_components:
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._get_band_colour"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "The hysteresis logic in _get_band_colour (manager.py:652-670). Preserved exactly. It is change-4c038bed's contribution and the reason the method was retained through 378703da."
    - "_get_shift_cue (manager.py:680-713) and the centre disc it fills. The centre is the shift cue's, not the band's; its colours are unchanged."
    - "The shift border (_draw_shift_border, manager.py:562) and the r=244 border ring."
    - "The centre numeric readout added by change-378703da. It stays white."
    - "The inert bottom arc and the 'RPM x 1000' label, except where the label's colour must change for legibility."
    - "The night palette (7.3.12, 5012004e). This change introduces the dark ground; that change introduces a dimmed variant of it and of everything else."
    - "Render caching (7.3.5, 821919ce). This change makes the band ring non-static, which is an obligation on that triple's cache key, discharged there. See dependencies."
    - "Display report §4.2, band colour thrash. Already closed by change-4c038bed's hysteresis."
    - "_draw_digital_mode and the full-field band fill. Already removed by change-378703da, which is a prerequisite."

rational:
  problem_statement: >
    The gauge face is light grey (200, 200, 200) across a r=232 disc —
    169,100 px of near-permanent brightness in the driver's forward
    field of view, on a panel whose backlight cannot be reduced in
    software. The black ticks and numerals depend on that light ground,
    so the ground cannot be darkened without them. Separately,
    _get_band_colour still returns a text colour for a readout that no
    longer exists.
  proposed_solution: >
    Darken the ground, invert the ticks and numerals, and let the
    coloured arc — which is already an annulus between r=100 and r=232 —
    carry the band on its own. Reduce _get_band_colour to what its
    remaining caller needs.
  alternatives_considered:
    - option: "Add a separate thin band ring at a fixed radius, distinct from the progressive fill arc."
      reason_rejected: >
        Closer to a literal reading of 'annular band indicator', and
        rejected as redundant: the fill arc already terminates at the
        current RPM and is already drawn in the active band's colour
        (manager.py:891-896), so a second ring would restate what the
        arc's leading edge shows. It would also consume radial space
        between r=100 and r=232 that the arc uses, and add a second
        element for 7.3.5's cache and 7.3.12's palette to track.
    - option: "Keep the light ground and reduce only the saturation of the band colours."
      reason_rejected: >
        The ground is the larger emitter — 169,100 px against the arc's
        variable and usually smaller area. Desaturating the band would
        weaken the cue while leaving most of the emitted light in place,
        which is the wrong trade in both directions.
    - option: "Retain the (bg_colour, text_colour) return shape and ignore the second element."
      reason_rejected: >
        Smaller diff. Rejected because a returned value with no consumer
        is an invitation: the next author to need a text colour will use
        it, and it encodes assumptions from a retired mode. ai/task.md
        §7.3.14 explicitly asks this change document to state whether
        the text colour is retained. It is not."
    - option: "Make the ground black (0, 0, 0)."
      reason_rejected: >
        Minimises emitted light but removes the visual distinction
        between the gauge face and the black corners outside the
        circular viewport (manager.py:864), so the instrument loses its
        edge. A near-black (16, 16, 16) keeps the face readable as a
        face at a cost of roughly 0.5% relative luminance.
  benefits:
    - "The largest emitting region of the display drops from relative luminance 0.578 to approximately 0.005 — the night-glare cost the finding names is substantially removed."
    - "The band cue survives at full strength: the arc is unchanged in colour and extent."
    - "The readout's legibility is no longer a function of the active band, so a per-band correction of the kind recommendation 23 required cannot be needed again."
    - "_get_band_colour's signature states what it is for."
  risks:
    - risk: >
        Black ticks and numerals on a dark ground are invisible. This is
        not a subtle risk — it is a certainty if the ground is changed
        without them.
      mitigation: >
        Both are re-coloured in the same edit and their contrast is
        computed rather than judged. The verification asserts >= 4.5:1
        for each against the new ground.
    - risk: >
        Daylight legibility falls. A dark face in direct sun is harder
        to read than a light one, and the panel cannot be brightened
        beyond its maximum.
      mitigation: >
        This is the real trade and it cannot be settled statically. The
        on-target step observes the face in daylight explicitly, and the
        ground colour is a single named constant so it can be revised
        from one place if the observation goes against it. Recorded as
        the item most likely to require adjustment after v0.4.0.
    - risk: >
        7.3.5's static-layer cache, if already implemented, treats the
        ground and the ticks as invariant. They remain invariant under
        this change; the band ring does not.
      mitigation: >
        Cross-check D3 requires 7.3.5's cache key to include the active
        band index and this change to extend it. The arc was already
        redrawn per frame and was never part of the static set, so in
        practice this change adds no new invalidation obligation beyond
        what D3 already records. Stated explicitly rather than left to
        inference.
  benefits_measurement: >
    Ground relative luminance 0.5776 -> approximately 0.0048.
    Consumers of _get_band_colour's text colour: 0 before and after —
    the value is removed, not orphaned. Elements whose colour depends
    on the active band: unchanged at one, the arc.

technical_details:
  current_behavior: >
    _draw_radial_mode fills black at manager.py:864, draws the shift
    border at 866, then fills a r=232 circle (200, 200, 200) at 867. The
    headroom and inert arcs are (180, 180, 180) at 872 and 878. The
    coloured band segments are drawn at 891-896. Zone boundary lines are
    (60, 60, 60) at 905, the inner edge ring (40, 40, 40) at 910. Tick
    marks are black at 922-923 and numerals black at 931. The label is
    (200, 0, 0) at 970. _get_band_colour (616-678) returns a
    (bg_colour, text_colour) tuple from a six-row palette at 634-641.
  proposed_behavior: >
    The r=232 ground is (16, 16, 16). The headroom and inert arcs are
    a dark grey that reads as unfilled track against it. Ticks and
    numerals are light. The coloured band segments are unchanged. The
    zone boundary lines and inner edge ring are lightened enough to
    remain visible. _get_band_colour returns (band_index, colour).
  implementation_approach: >
    Four edits in one file.

    EDIT A — a named palette for the face. Introduce module-level or
    class-level constants for the ground, the unfilled track, the tick
    and numeral colour, and the two line colours, rather than repeating
    literals at eight sites. 7.3.12 will vary exactly these, so naming
    them here is what makes that change tractable.

    EDIT B — apply them in _draw_radial_mode at the eight sites listed
    under current_behavior.

    EDIT C — _get_band_colour returns (band_index, colour). The palette
    loses its second column. The hysteresis block at manager.py:652-670
    is untouched.

    EDIT D — call it from _draw_radial_mode. Today RADIAL derives its
    band segments from an inline band_thresholds list at
    manager.py:882-889 and does not call _get_band_colour at all. That
    list and the palette in _get_band_colour encode the same six bands
    twice. Route the arc's colour through _get_band_colour so the band
    identity has one owner and the hysteresis applies to the arc as it
    did to DIGITAL's background.

    EDIT D is the substantive part of "the band is carried by the ring":
    without it the ring is coloured by an unhysteresised parallel table
    and the retained method still has no caller.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Named face-palette constants added and applied at eight sites in
        _draw_radial_mode. _get_band_colour returns (band_index, colour)
        and becomes the single owner of band identity, called by the arc
        drawing loop in place of the inline threshold table.
      functions_affected:
        - "_draw_radial_mode"
        - "_get_band_colour"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes:
    - "_get_band_colour's return type changes from Tuple[Tuple[int,int,int], Tuple[int,int,int]] to Tuple[int, Tuple[int,int,int]]. It is a private method with, after change-378703da, no caller; the change cannot break an external consumer."

dependencies:
  internal:
    - component: "change-378703da"
      impact: "PREREQUISITE. It removes _draw_digital_mode and the full-field fill, and retains _get_band_colour for this change. Implementing this triple first would mean editing code 378703da deletes."
    - component: "change-4c038bed"
      impact: "Shipped. Its hysteresis is preserved unmodified and, via EDIT D, is extended to the arc for the first time."
    - component: "_get_shift_cue — manager.py:680"
      impact: "Unmodified. The centre disc remains the shift cue's."
  external: []
  required_changes:
    - change_ref: "change-378703da"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "blocks"
    - change_ref: "change-821919ce"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with SDL_VIDEODRIVER=dummy and a mocked rendering engine.
    Colour decisions are asserted by computing WCAG relative luminance
    and contrast from the constants rather than by inspecting output.
    _get_band_colour is tested directly against a rising and falling RPM
    sweep and compared with the pre-change implementation's band
    selection.
  test_cases:
    - scenario: "The r=232 ground fill."
      expected_result: "The named dark constant; (200, 200, 200) appears nowhere in _draw_radial_mode."
    - scenario: "Tick mark and numeral contrast against the ground."
      expected_result: ">= 4.5:1 for both, computed."
    - scenario: "Zone boundary line and inner edge ring contrast against the ground."
      expected_result: "Visible — >= 3:1, these being non-text elements."
    - scenario: "Each of the six band colours against the ground."
      expected_result: ">= 3:1 for each, so the arc reads at every band."
    - scenario: "_get_band_colour return shape."
      expected_result: "A 2-tuple of (int, (int, int, int))."
    - scenario: "_get_band_colour band selection across a rising sweep 0 to 7000."
      expected_result: "Identical band sequence to the pre-change implementation."
    - scenario: "The same across a falling sweep 7000 to 0."
      expected_result: "Identical, including the hysteresis asymmetry."
    - scenario: "_get_band_colour with an RPMBands whose gaps are narrow."
      expected_result: "The margin clamp at manager.py:652-659 behaves as before."
    - scenario: "The arc colour at a given RPM, after EDIT D."
      expected_result: "Matches the colour _get_band_colour returns for that RPM."
    - scenario: "An RPM oscillating across a threshold by less than the hysteresis margin."
      expected_result: "The arc colour does not alternate — the property EDIT D newly confers on it."
    - scenario: "The centre readout and the centre disc."
      expected_result: "Unchanged: white numeral on the _get_shift_cue fill."
    - scenario: "One rendered frame per band."
      expected_result: "The band is distinguishable from the arc alone in each."
  regression_scope:
    - "tests/display/ — the display suite once populated per ai/task.md §8.2."
    - "On gtach.local, in daylight: the ticks, numerals and arc are readable on the dark face. This is the observation most likely to require a revision."
    - "On gtach.local, at night: the face is not a glare source."
    - "On gtach.local: the band changes visibly as the RPM sweeps, in simulation mode."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "pytest tests/ passes with no new failures."
    - "No colour literal appears more than once in _draw_radial_mode; all face colours come from the named constants."
    - "_get_band_colour's hysteresis block is byte-identical to its current text."
    - "_get_shift_cue is byte-identical to its current text."
    - "The inline band_thresholds table at manager.py:882-889 is gone, the band having one owner."

implementation:
  implementation_steps:
    - step: "Add the named face-palette constants."
      owner: "Claude Code"
    - step: "Apply them at the eight sites in _draw_radial_mode."
      owner: "Claude Code"
    - step: "Change _get_band_colour's return shape, preserving the hysteresis block exactly."
      owner: "Claude Code"
    - step: "Route the arc's colour through _get_band_colour and remove the inline threshold table."
      owner: "Claude Code"
    - step: "Compile check, contrast computations, and the existing suite."
      owner: "Claude Code"
    - step: "Observe the face on gtach.local in daylight and at night, and record whether the ground constant needs revision."
      owner: "William Watson"
  rollback_procedure: >
    Single commit in one file. git revert restores the light face. No
    configuration or persisted data is involved.
  deployment_notes: >
    Visible change: the gauge face goes from light grey to near-black.
    Ships in v0.4.0 with the other appearance-changing triples
    (ai/task.md §8.5). Must land after change-378703da within that
    release. The daylight observation is the one that may send this back
    for adjustment.

verification:
  implemented_date: "2026-08-04"
  implemented_by: "Claude Code, per prompt-5014040c (commit 730ae56)"
  verification_date: "2026-08-05"
  verified_by: "Claude Code (development-platform script); William Watson (gtach.local)"
  test_results: >
    Delivered as specified: dark ground, re-coloured ticks and
    numerals, inline threshold table removed, arc coloured from
    _get_band_colour. Band-index sequence proved identical to the real
    pre-change source across rising and falling sweeps at 10 RPM steps,
    hysteresis asymmetry included; no alternation under a +/-50 RPM
    oscillation about a threshold; 5000 RPM shows blue/green/yellow
    rather than one colour. William confirmed 2026-08-07 that GTach
    functions correctly on gtach.local.
  issues_found:
    - "BAND_COLOURS[0] delivered as (0, 0, 255) rather than the prompt's specified (0, 0, 0); justified in source and in issue-5014040c — the specified value was DIGITAL's screen background, never an arc colour, and the prompt's own unchanged-colours constraint governs."
    - "The WCAG 3:1 band-fill contrast requirement is arithmetically unsatisfiable alongside the fixed palette values this change and 5012004e both specify (task.md §9.8.5 item 3). Open design decision, not an implementation gap."

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-378703da"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "blocks"
    - change_ref: "change-821919ce"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-5014040c"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-5014040c."
      - "Answers ai/task.md §7.3.14's two questions: change-4c038bed's white-on-blue correction is superseded because the readout it applied to went with DIGITAL, and _get_band_colour does not retain a text-colour return value."
      - "Recorded EDIT D — routing the arc's colour through _get_band_colour — as the substantive part of the change: without it the ring is coloured by an unhysteresised parallel table and the method retained by 378703da still has no caller."
      - "Recorded the daylight-legibility trade as the item most likely to require revision after v0.4.0, and the ground colour as a single named constant so that revision is cheap."
      - "Recorded that a separate fixed band ring was considered and rejected as restating the arc's leading edge."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status proposed -> closed. Implementation and verification recorded (commit 730ae56); the arithmetically-unsatisfiable contrast criterion recorded as an open design question. Closed on William's confirmation that GTach functions correctly on gtach.local."

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
| 1.0 | 2026-08-04 | Initial change document coupled to issue-5014040c. Specifies the dark gauge face, the re-coloured ticks and numerals, the arc as the sole band cue routed through `_get_band_colour`, and the removal of its text-colour return. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation and verification recorded (commit 730ae56). Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
