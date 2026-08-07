Created: 2026 August 05

# Change: One Colour for the Sweep, Bold Marks for the Headroom

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-64d8d8fc"
  title: "The RADIAL fill arc is drawn as a single arc in the active band's colour, band boundary marks are widened to 7 px, the centre disc is filled from two new band-indexed palette tuples, and _get_shift_cue takes the active band index as a parameter"
  date: "2026-08-05"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-64d8d8fc"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-64d8d8fc"
  description: >
    Resolves issue-64d8d8fc. Human-originated cognitive-load
    requirement. Withdraws the graduated-arc constraint imposed by
    prompt-5014040c.

scope:
  summary: >
    The sweep stops being graduated. One arc, one colour, chosen by the
    hysteresised active band. The band boundary marks are bolded so the
    headroom cue the graduation used to carry survives. The centre disc
    is filled from the band rather than from a separate shift palette,
    with a dim variant for the steady states and a bright variant for
    the upshift flash's lit phase. The shift border is untouched.
  affected_components:
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._get_shift_cue"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "Palette"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "_get_band_colour (manager.py:1020-1079). Byte-identical. It already owns the band and already carries the hysteresis; this change only widens what its answer is used for."
    - "The hysteresis margin itself. _band_hysteresis stays at 75.0 RPM."
    - "_draw_shift_border and the three shift_border_* colours. The border keeps its own semantic; see issue-64d8d8fc §2.3."
    - "The flash period and duty cycle. Unchanged at fps_limit/2 frames, driven from the frame counter."
    - "The condition that produces the flash. Unchanged at rpm >= caution_start."
    - "The six band colours in Palette.bands. Unchanged in both palettes."
    - "The major tick marks and numerals at step 8, and the white RPM indicator line at step 10."
    - "The centre numeric readout. Stays white, stays 72 px."
    - "The headroom and inert track arcs."
    - "Render caching (change-821919ce). The centre disc was already non-static because it flashes; this change adds the active band index to what it depends on, which that change's cache key must already carry for the arc."

rational:
  problem_statement: >
    Reading the current zone from a graduated arc is a two-stage task:
    localise the sweep's leading edge, then judge which coloured band
    that edge falls in. Both stages are spatial and both degrade in
    peripheral vision, which is where an instrument sits while the
    driver is looking at the road. Separately, the centre disc — the
    largest uninterrupted region of the gauge — carries no zone
    information at all, being filled from a three-colour shift palette
    that duplicates what the border already says.
  proposed_solution: >
    Draw the filled sweep as one arc in the active band's colour, so
    zone state is a single-stage colour judgement available to a glance.
    Bold the existing band boundary marks from 3 px to 7 px so that
    headroom to the next zone remains readable without the graduation.
    Fill the centre disc from the band as well, so the zone reading is
    reinforced at the point of fixation, while leaving the border to
    carry the shift instruction.
  alternatives_considered:
    - option: "Keep the graduated arc and add a separate uniform band indicator elsewhere."
      reason_rejected: >
        Restates the same quantity twice and consumes display area. The
        graduation is not additive information once the sweep is
        uniformly coloured — it is the thing being replaced.
    - option: "Colour the shift border to match the band as well."
      reason_rejected: >
        Destroys the border's semantic. At caution_start the border is
        green for 'upshift now' while band 3 is yellow; band-colouring
        would render the upshift instruction yellow, orange, then red as
        RPM rises. Bands 0 and 1 are already blue, so a band-coloured
        border could not separate 'safe downshift' from 'idle'. Recorded
        in full at issue-64d8d8fc §2.3.
    - option: "Fill the centre disc with the band colour at full saturation."
      reason_rejected: >
        Two failures. The white 72 px readout falls to 1.07:1 against
        band 3's (255, 255, 0) — unreadable. And 30,800 px of saturated
        colour in the driver's forward field of view reinstates the
        glare that change-5014040c removed from the face. The dim
        band_centres variant holds the readout at >= 7:1 and the disc's
        relative luminance at or below 0.093.
    - option: "One band_centres tuple, flashing the dim variant against shift_centre_dark."
      reason_rejected: >
        Simpler, and rejected on measurement. The dim variants sit at
        1.34:1 to 2.69:1 against the dark phase for bands 3 to 5, which
        are the only bands that flash. The upshift cue would be weakest
        in the danger band, where it matters most. The second tuple
        restores the flash to 3.81:1 to 4.15:1 by day and 3.39:1 to
        5.94:1 at night, against baselines of 5.68:1 and 2.59:1 for the
        green flash it replaces."
    - option: "Delete the band boundary marks along with the graduation."
      reason_rejected: >
        They are the only remaining indication of how much headroom
        remains before the next zone. Removing them would make the
        instrument reactive rather than anticipatory, which is contrary
        to its stated primary purpose of providing shift cues."
  benefits:
    - "Zone state becomes a single-stage colour judgement rather than an edge-localisation followed by a band judgement."
    - "The zone reading is present at the point of fixation — the centre disc — not only at the periphery of the gauge."
    - "The polygon count for the sweep falls from up to six 122-point polygons per frame to one, on a Raspberry Pi Zero 2W."
    - "_get_shift_cue is called once per frame instead of twice, removing a latent path by which the two calls could disagree."
    - "The three shift_centre_* colours that duplicated the border's semantic are removed rather than orphaned."
  risks:
    - risk: >
        The driver loses the ability to see where the next band boundary
        is. This is a certainty if the boundary marks are not bolded in
        the same edit.
      mitigation: >
        The mark width goes from 3 px to 7 px in the same change,
        matching the major ticks and separated from them by colour. The
        mark length is deliberately left at 28 px so the existing radial
        layout is undisturbed; it is a single literal if on-target
        observation shows 7 px is insufficient.
    - risk: >
        The whole sweep now changes colour at a band crossing rather
        than one segment, so threshold flicker would be far more
        distracting than before.
      mitigation: >
        The 75 RPM sticky hysteresis in _get_band_colour already
        prevents it and is preserved unmodified. The change makes that
        hysteresis load-bearing over a much larger area, so the
        once-per-frame call invariant is stated as a success criterion
        rather than left implicit.
    - risk: >
        A band-coloured centre disc reinstates glare on a panel whose
        backlight cannot be reduced in software — the problem
        change-5014040c was created to solve.
      mitigation: >
        band_centres is dim by construction. Worst-case relative
        luminance is 0.093 for day band 3, against 0.578 for the face
        that change removed. The bright band_centres_lit variant is used
        only in the lit half of the upshift flash, which is transient
        and intentional.
    - risk: >
        Bands 0 and 1 are the same blue, so the sweep looks identical
        across the idle and torque-approach zones.
      mitigation: >
        Pre-existing and unchanged — the graduated arc had the same
        property. Not addressed here; recorded so it is not mistaken for
        a regression introduced by this change.
  benefits_measurement: >
    Sweep polygons per frame: up to 6 -> 1. _get_shift_cue calls per
    frame: 2 -> 1. _get_band_colour calls per frame: 1 -> 1. Palette
    fields carrying centre colours: 3 scalars -> 2 six-tuples plus the
    retained shift_centre_dark. White readout contrast against the
    steady centre fill: 7.36:1 worst case, day band 3.

technical_details:
  current_behavior: >
    _draw_radial_mode calls _get_shift_cue at manager.py:1198 for the
    border and again at 1336 for the centre, and _get_band_colour once
    at 1219. The arc loop at 1234-1255 walks six segment bounds and
    draws each segment in its own band colour, except the leading one
    which takes the active band's. Band boundary marks are drawn 3 px
    wide at 1315. The centre disc is filled at 1338 from
    _get_shift_cue's fourth return value, which comes from
    shift_centre_lit, shift_centre_dark, shift_centre_down or
    shift_centre_normal.
  proposed_behavior: >
    _get_band_colour is called once, early. Its band index is passed to
    a single _get_shift_cue call whose result serves both the border and
    the centre. The sweep is one draw_donut_arc from 0 to the current
    RPM in palette.bands[active_band]. Band boundary marks are 7 px. The
    centre disc is palette.band_centres[active_band] when steady, and
    alternates palette.band_centres_lit[active_band] against
    palette.shift_centre_dark when the upshift cue is active.
  implementation_approach: >
    Four edits across two files.

    EDIT A — models.py. Palette gains band_centres and
    band_centres_lit, each a six-tuple indexed by band. shift_centre_lit,
    shift_centre_normal and shift_centre_down are removed, their
    semantics having moved to the band. shift_centre_dark is retained as
    the flash's dark phase. The three shift_border_* fields are
    untouched. Values are authored for both palettes, not derived, on
    the same reasoning the night palette records: scaling compresses hue
    separation, and the band cue is the instrument's primary signal.

    EDIT B — _get_shift_cue gains an active_band parameter and sources
    its centre colour from the two new tuples. Its border logic, its
    flash phase computation and its three conditions are unchanged.

    EDIT C — _draw_radial_mode is restructured so _get_band_colour runs
    once before the fill and _get_shift_cue runs once thereafter, and
    the six-segment loop is replaced by a single arc.

    EDIT D — the boundary mark width literal at manager.py:1315.

    EDIT C is the substantive part. EDIT D is one character.
  code_changes:
    - component: "Palette"
      file: "src/gtach/display/models.py"
      change_summary: >
        band_centres and band_centres_lit added to the dataclass and to
        both palette instances. shift_centre_lit, shift_centre_normal
        and shift_centre_down removed.
      functions_affected: []
      classes_affected:
        - "Palette"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _get_shift_cue takes active_band and returns a band-derived
        centre colour. _draw_radial_mode calls each of the two helpers
        once per frame, draws the sweep as one arc, and widens the band
        boundary marks.
      functions_affected:
        - "_draw_radial_mode"
        - "_get_shift_cue"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes:
    - "_get_shift_cue's signature gains a positional parameter: (self, rpm: float, active_band: int). Private method, two call sites, both in _draw_radial_mode and both collapsed to one by this change."
    - "Palette loses three fields and gains two. Both palette instances are updated in the same edit; the dataclass has no external constructor."

dependencies:
  internal:
    - component: "change-5014040c"
      impact: >
        Shipped. This change withdraws its graduated-arc constraint by
        human decision. Its face palette, its FACE_ constants and its
        _get_band_colour signature are all preserved.
    - component: "change-4c038bed"
      impact: "Shipped. Its 75 RPM hysteresis is preserved unmodified and becomes load-bearing across the whole sweep and the centre disc."
    - component: "change-5012004e"
      impact: "Shipped. Both palettes are extended symmetrically; the once-per-frame palette read at manager.py:1148 is preserved."
    - component: "change-e4b7c3a1"
      impact: "Shipped. Its shift border and its flash condition are preserved exactly. Its three centre colours are superseded."
  external: []
  required_changes:
    - change_ref: "change-821919ce"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with SDL_VIDEODRIVER=dummy and a mocked rendering engine.
    Colour decisions are asserted by computing WCAG relative luminance
    and contrast from the palette constants rather than by inspecting
    rendered output. Call counts are asserted by patching the two
    helpers and rendering one frame.
  test_cases:
    - scenario: "The filled sweep at 5000 RPM."
      expected_result: "One arc in palette.bands[active_band]. No blue or green segment is drawn."
    - scenario: "The sweep at rpm 0."
      expected_result: "No fill arc is drawn; the track shows through. Nothing raises."
    - scenario: "_get_band_colour call count over one rendered frame."
      expected_result: "Exactly one."
    - scenario: "_get_shift_cue call count over one rendered frame."
      expected_result: "Exactly one."
    - scenario: "An RPM oscillating +/- 50 about a threshold, with the 75 RPM margin."
      expected_result: "The whole-sweep colour does not alternate."
    - scenario: "White (255, 255, 255) against each of the twelve band_centres entries."
      expected_result: ">= 4.5:1 for each. This fill is persistent, so the normal-text threshold applies. Worst case 7.36:1, day band 3."
    - scenario: "White against each of the twelve band_centres_lit entries."
      expected_result: ">= 3:1 for each. The lit phase is transient and the readout is 72 px, so the large-text threshold applies. Worst case 3.47:1, night band 3."
    - scenario: "band_centres_lit against shift_centre_dark, bands 3 to 5, both palettes."
      expected_result: ">= 3:1 for each — these are the only bands that flash."
    - scenario: "Relative luminance of each band_centres entry."
      expected_result: "<= 0.10, the disc being 30,800 px in the forward field of view."
    - scenario: "The shift border at rpm below torque_start, between the two thresholds, and above caution_start."
      expected_result: "shift_border_down, shift_border_normal, shift_border_caution respectively — unchanged from the current implementation."
    - scenario: "The flash phase across consecutive frames at rpm above caution_start."
      expected_result: "Alternates with a period of fps_limit/2 frames, unchanged."
    - scenario: "The flash phase at rpm below caution_start."
      expected_result: "No flash. The centre is steady band_centres[active_band]."
    - scenario: "Band boundary mark width."
      expected_result: "7 px."
    - scenario: "Palette attribute access."
      expected_result: "shift_centre_lit, shift_centre_normal and shift_centre_down are absent from both palettes."
  regression_scope:
    - "tests/display/."
    - "On gtach.local, in simulation mode: the sweep changes colour as a whole at each threshold, and does not flicker at a threshold."
    - "On gtach.local: the boundary marks are locatable at a glance at 7 px, and the next threshold's position is readable."
    - "On gtach.local, at night: the centre disc is not a glare source in any band."
    - "On gtach.local: the upshift flash is as noticeable as the green flash it replaces, in bands 3, 4 and 5."
  validation_criteria:
    - "python -m py_compile on both modified files passes."
    - "pytest tests/ passes with no new failures."
    - "_get_band_colour's text is byte-identical."
    - "_draw_shift_border's text is byte-identical."
    - "The three shift_border_* values are byte-identical in both palettes."
    - "The six-entry segment_bounds tuple and the loop over palette.bands are gone from _draw_radial_mode."

implementation:
  implementation_steps:
    - step: "Add band_centres and band_centres_lit to Palette and to both instances; remove the three superseded shift_centre_* fields."
      owner: "Claude Code"
    - step: "Give _get_shift_cue an active_band parameter and source the centre colour from the new tuples."
      owner: "Claude Code"
    - step: "Restructure _draw_radial_mode to call each helper once and to draw the sweep as a single arc."
      owner: "Claude Code"
    - step: "Widen the band boundary marks to 7 px."
      owner: "Claude Code"
    - step: "Compile check, contrast and luminance computations, call-count assertions, and the existing suite."
      owner: "Claude Code"
    - step: "Observe on gtach.local: threshold behaviour, boundary mark legibility, night glare, flash conspicuity."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the graduated
    arc and the three shift centre colours. No configuration or
    persisted data is involved.
  deployment_notes: >
    Visible change. The sweep goes from six colours to one and the
    centre disc changes colour with the band. Ships in v0.4.0 with the
    other appearance-changing triples. The boundary mark width and the
    band_centres luminance are the two values most likely to be revised
    after on-target observation; both are single literals.

verification:
  implemented_date: "2026-08-05"
  implemented_by: "Claude Code, per prompt-64d8d8fc"
  verification_date: "2026-08-07"
  verified_by: "Claude Code (source re-check); William Watson (gtach.local)"
  test_results: >
    Report v0.4.0-64d8d8fc-uniform-sweep-colour.md: implemented in full,
    two files (+59/-11 models.py, +54/-54 manager.py), no departures
    required. Source re-check confirms Palette.band_centres and
    band_centres_lit present in models.py. William confirmed GTach
    functions correctly on gtach.local.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5014040c"
      relationship: "supersedes_constraint"
    - change_ref: "change-e4b7c3a1"
      relationship: "supersedes_constraint"
    - change_ref: "change-821919ce"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-64d8d8fc"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-64d8d8fc."
      - "Records the withdrawal of prompt-5014040c's graduated-arc constraint as a human decision, not a defect correction."
      - "Records the rejection of a band-coloured shift border, with the caution_start inversion as the deciding argument."
      - "Records the two-tuple centre palette as a measurement outcome: one dim tuple alone leaves the upshift flash at 1.34:1 in the danger band."
      - "Records the bold boundary marks as the replacement carrier of the headroom cue, not as a cosmetic change."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status proposed -> closed. Implementation confirmed by report and source re-check. Closed on William's confirmation that GTach functions correctly on gtach.local."

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
| 1.0 | 2026-08-05 | Initial change document coupled to issue-64d8d8fc. Specifies the single-colour sweep, the 7 px band boundary marks, the band-indexed centre disc palette, and the once-per-frame helper call invariant. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation and verification recorded. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
