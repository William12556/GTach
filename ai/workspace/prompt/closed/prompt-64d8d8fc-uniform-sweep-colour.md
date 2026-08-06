Created: 2026 August 05

# Prompt: Draw the Sweep in One Colour and Give the Centre to the Band

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-64d8d8fc"
  task_type: "implementation"
  source_ref: "change-64d8d8fc"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-64d8d8fc"
    change_iteration: 1

context:
  purpose: >
    RADIAL's filled sweep is graduated: every segment below the leading
    one keeps its own band colour. Reading the current zone is therefore
    a two-stage spatial task — localise the sweep's leading edge, then
    judge which band it falls in. Both stages degrade in peripheral
    vision, which is where the instrument sits while the driver is
    looking at the road. Separately the centre disc, the largest
    uninterrupted region of the gauge, carries no zone information at
    all: it is filled from a three-colour shift palette that duplicates
    what the border beside it already says.
  integration: >
    Two files: src/gtach/display/models.py and
    src/gtach/display/manager.py. Executor is Claude Code; AEL is not
    used.

    THIS REVERSES A PRIOR CONSTRAINT. prompt-5014040c said, twice and
    emphatically, "Do NOT paint every segment in the active band's
    colour". That constraint is withdrawn by human decision recorded in
    issue-64d8d8fc §2.1. This task requires exactly what that prompt
    forbade. Do not treat the earlier comment in the source as
    authoritative — the comment block at manager.py:1242-1246 is being
    replaced along with the code it describes.

    WHAT THIS TASK IS NOT. It is not a change to the shift border, to
    the flash condition, to the flash period, to the band colours, to
    the hysteresis, or to _get_band_colour. All of those are preserved
    exactly. See constraints.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/models.py and src/gtach/display/manager.py."
    - "Do NOT modify _get_band_colour (manager.py:1020-1079). Not one character. It already owns the band identity and already carries the 75 RPM sticky hysteresis; this task only widens what its answer is used for."
    - "Do NOT modify _draw_shift_border, and do NOT change the three shift_border_* values in either palette. The border encodes what the driver should DO; the band encodes what the engine IS DOING. Colouring the border by band would render the upshift instruction yellow, then orange, then red as RPM rises — the inverse of the instruction. See issue-64d8d8fc §2.3."
    - "Do NOT change the condition that produces the flash. It stays rpm >= caution_start."
    - "Do NOT change the flash period or its derivation from self._frame_counter."
    - "Do NOT change the six values in Palette.bands in either palette."
    - "Do NOT change _band_hysteresis."
    - "Do NOT change the major tick marks, the numerals, the white RPM indicator line, the track arcs, or the centre numeric readout. The readout stays white and stays 72 px."
    - "Do NOT call _get_band_colour more than once per rendered frame. Each call may advance the sticky band by one step, so a second call halves the effective hysteresis. This was already true and is now load-bearing across the whole sweep."
    - "Do NOT derive the new centre colours at runtime by scaling Palette.bands. They are authored constants, for the reason NIGHT_PALETTE already records: scaling compresses hue separation, and the band cue is the instrument's primary signal."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Add two band-indexed centre-colour tuples to Palette and remove the
    three superseded scalar centre colours. Give _get_shift_cue the
    active band index and source its centre colour from the new tuples.
    Restructure _draw_radial_mode so each helper is called once per
    frame and the filled sweep is a single arc in the active band's
    colour. Widen the band boundary marks to 7 px.
  requirements:
    functional:
      - "The filled sweep from 0 to the current RPM is one draw_donut_arc call in palette.bands[active_band]."
      - "No segment loop, no segment_bounds tuple, remains in _draw_radial_mode."
      - "Band boundary marks are 7 px wide."
      - "The centre disc is palette.band_centres[active_band] in the normal and safe-downshift states."
      - "In the upshift state the centre disc alternates palette.band_centres_lit[active_band] and palette.shift_centre_dark."
      - "_get_band_colour is called exactly once per rendered frame."
      - "_get_shift_cue is called exactly once per rendered frame."
      - "The shift border colour for a given RPM is identical to the current implementation's."
      - "shift_centre_lit, shift_centre_normal and shift_centre_down are absent from Palette."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Positive. The sweep's polygon count falls from up to six 122-point polygons per frame to one, and _get_shift_cue runs once instead of twice"
      metric: "time"

design:
  architecture: >
    The band already has one owner. This change makes that owner's
    answer the only thing the sweep and the centre disc are coloured by,
    so the hysteresis that stops the colour alternating at a threshold
    now protects the entire coloured area rather than one segment of it.
    The shift border is deliberately excluded, so that colour carries
    engine state and the border carries driver instruction.
  components:
    - name: "Palette.band_centres"
      type: "constants"
      purpose: "The steady centre disc fill, indexed by band."
      logic:
        - "Six entries, dim by construction."
        - "The disc is 30,800 px in the driver's forward field of view on a panel whose backlight cannot be reduced in software. Full-saturation band colour there would reinstate the glare change-5014040c removed from the face, and would put the white readout at 1.07:1 against band 3."
    - name: "Palette.band_centres_lit"
      type: "constants"
      purpose: "The lit phase of the upshift flash, indexed by band."
      logic:
        - "Six entries, bright. Used only when rpm >= caution_start and only on the lit half of the cycle."
        - "Exists because the dim variants sit at 1.34:1 to 2.69:1 against shift_centre_dark for bands 3 to 5 — the only bands that flash — which would make the upshift cue weakest in the danger band."
    - name: "DisplayManager._get_shift_cue"
      type: "function"
      purpose: "Border from the shift state, centre from the band."
      interface:
        inputs:
          - name: "rpm"
            type: "float"
          - name: "active_band"
            type: "int"
        outputs:
          type: "Tuple[Tuple[int, int, int], int, bool, Tuple[int, int, int]]"
      logic:
        - "The three conditions, the border colours, the border width and the flash phase computation are unchanged."
        - "Only the centre colour changes, and only in where it is read from."
    - name: "DisplayManager._draw_radial_mode"
      type: "function"
      purpose: "One band lookup, one shift lookup, one sweep arc."
      logic:
        - "Call _get_band_colour once, before the surface fill."
        - "Call _get_shift_cue once, passing the band index; use its border at step 1 and its centre at step 12."
        - "Replace the segment loop with one arc from 0 to the current RPM."
  dependencies:
    internal:
      - "change-5014040c — shipped. Its FACE_ palette and its _get_band_colour signature are preserved; only its graduated-arc constraint is withdrawn."
      - "change-4c038bed — shipped. Its hysteresis is preserved unmodified."
      - "change-e4b7c3a1 — shipped. Its border and flash condition are preserved; its three centre colours are superseded."
    external: []

error_handling:
  strategy: >
    Unchanged. Both existing handlers remain; only _get_shift_cue's
    fallback return value changes, because the constant it names is
    being removed.
  exceptions:
    - exception: "Exception"
      condition: "Shift cue calculation failure."
      handling: "Existing handler. Returns (DAY_PALETTE.shift_border_normal, 12, False, DAY_PALETTE.band_centres[0]) — the previous fallback named DAY_PALETTE.shift_centre_normal, which no longer exists."
    - exception: "Exception"
      condition: "Anything in _draw_radial_mode."
      handling: "Existing handler. Unchanged."
  logging:
    level: "ERROR, unchanged"
    format: "self.logger.error(f'Shift cue calculation error: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "Render one frame at 5000 RPM and capture the draw_donut_arc calls."
      expected: "Two track arcs and exactly one fill arc, the fill in palette.bands[active_band]."
    - scenario: "Render one frame at rpm 0."
      expected: "No fill arc. Nothing raises."
    - scenario: "Render one frame at 7000 RPM."
      expected: "One fill arc spanning the full 300 degrees in palette.bands[5]."
    - scenario: "Patch _get_band_colour and render one frame."
      expected: "Called exactly once."
    - scenario: "Patch _get_shift_cue and render one frame."
      expected: "Called exactly once."
    - scenario: "RPM oscillating +/- 50 about bands.caution_start across successive frames, with _band_hysteresis at 75."
      expected: "The fill arc colour does not alternate."
    - scenario: "WCAG contrast of (255, 255, 255) against each of the six band_centres entries, both palettes."
      expected: ">= 4.5:1 for all twelve."
    - scenario: "WCAG contrast of (255, 255, 255) against each of the six band_centres_lit entries, both palettes."
      expected: ">= 3:1 for all twelve. The large-text threshold, the readout being 72 px and the lit phase transient."
    - scenario: "WCAG contrast of band_centres_lit[i] against shift_centre_dark for i in 3, 4, 5, both palettes."
      expected: ">= 3:1 for all six."
    - scenario: "WCAG relative luminance of each band_centres entry, both palettes."
      expected: "<= 0.10 for all twelve."
    - scenario: "_get_shift_cue border colour at rpm below torque_start, between the thresholds, and above caution_start."
      expected: "shift_border_down, shift_border_normal, shift_border_caution — asserted against a copy of the pre-change implementation."
    - scenario: "_get_shift_cue flash flag at rpm above and below caution_start."
      expected: "True and False respectively."
    - scenario: "_get_shift_cue centre colour across consecutive frames at rpm above caution_start."
      expected: "Alternates band_centres_lit[active_band] and shift_centre_dark with a period of fps_limit/2 frames."
    - scenario: "_get_shift_cue centre colour at rpm below caution_start."
      expected: "Constant band_centres[active_band] across frames."
    - scenario: "_get_shift_cue forced to raise internally."
      expected: "Returns the documented fallback; the caller does not raise."
    - scenario: "getattr on both palettes for the three removed field names."
      expected: "AttributeError in all six cases."
    - scenario: "Band boundary mark line width."
      expected: "7."
  edge_cases:
    - "rpm 0: the fill arc is skipped, as it is today, and the track shows through. active_band is 0 and _get_shift_cue is still called."
    - "rpm exactly at a threshold: the hysteresis requires the value to clear it by the margin, so the band does not change. Unchanged from today."
    - "Bands 0 and 1 are the same blue in both palettes, so the sweep looks identical across idle and torque-approach. This is pre-existing — the graduated arc had it too. Do not 'fix' it; it is out of scope."
    - "The upshift state spans bands 3, 4 and 5, so band_centres_lit entries 0, 1 and 2 are never displayed. Define them anyway, for indexing uniformity, and do not assert flash contrast on them."
    - "_get_shift_cue's fallback runs before active_band can be trusted. Index band_centres at 0, not at active_band."
    - "The palette is read once per frame at manager.py:1148 to stop a night toggle landing mid-frame (change-5012004e). Both new tuples must be read through that same local, not through self._palette."
  validation:
    - "git diff confirms _get_band_colour is unchanged."
    - "git diff confirms _draw_shift_border is unchanged."
    - "git diff confirms the three shift_border_* values are unchanged in both palettes."
    - "grep confirms segment_bounds no longer appears in manager.py."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "Cite change-64d8d8fc in a comment where a change is motivated by it, following the existing convention in both files."
  files:
    - path: "src/gtach/display/models.py"
      content: |
        EDIT A — the centre palette moves to the band.

        In the Palette dataclass, replace these three field
        declarations:

            shift_centre_lit: Tuple[int, int, int]
            shift_centre_normal: Tuple[int, int, int]
            shift_centre_down: Tuple[int, int, int]

        with:

            band_centres: Tuple[Tuple[int, int, int], ...]
            band_centres_lit: Tuple[Tuple[int, int, int], ...]

        Retain shift_centre_dark. Retain all three shift_border_*
        fields. Keep the declaration order tidy: the two new tuples
        belong beside bands, not beside the shift_border_* group.

        In DAY_PALETTE, remove shift_centre_lit=(0, 160, 0),
        shift_centre_normal=(26, 26, 26) and
        shift_centre_down=(0, 40, 100), and add:

            # The centre disc takes the active band's colour, so the
            # zone reading is present at the point of fixation and not
            # only at the rim (change-64d8d8fc). Dim, because the disc
            # is 30,800 px in the driver's forward field of view and
            # the HyperPixel's backlight cannot be reduced in software
            # — full-saturation band colour here would reinstate the
            # glare change-5014040c removed from the face, and would
            # leave the white readout at 1.07:1 against band 3.
            band_centres=(
                (0, 0, 89),         # 0 idle
                (0, 0, 89),         # 1 torque approach
                (0, 89, 0),         # 2 torque
                (89, 89, 0),        # 3 caution
                (89, 45, 0),        # 4 warning
                (89, 0, 0),         # 5 danger
            ),
            # The lit phase of the upshift flash. Bright, and displayed
            # only while rpm >= caution_start and only on half the
            # cycle. A single dim tuple flashed against
            # shift_centre_dark measures 1.34:1 to 2.69:1 for bands 3
            # to 5 — the only bands that flash — which would make the
            # upshift cue weakest in the danger band.
            band_centres_lit=(
                (0, 0, 200),        # 0 idle — never displayed
                (0, 0, 200),        # 1 torque approach — never displayed
                (0, 130, 0),        # 2 torque — never displayed
                (115, 115, 0),      # 3 caution
                (180, 90, 0),       # 4 warning
                (220, 0, 0),        # 5 danger
            ),

        In NIGHT_PALETTE, remove the same three fields and add:

            band_centres=(
                (0, 0, 59),
                (0, 0, 59),
                (0, 49, 0),
                (52, 49, 0),
                (61, 26, 0),
                (70, 0, 0),
            ),
            # Equal to NIGHT_PALETTE.bands at present. The night band
            # colours are already dim enough that no separate lit
            # variant is needed to satisfy the flash contrast, and
            # dimming them further drops bands 4 and 5 to 2.98:1 and
            # 2.66:1 against shift_centre_dark. Kept as its own tuple
            # for structural symmetry with DAY_PALETTE and so the two
            # can diverge without a signature change.
            band_centres_lit=(
                (0, 0, 170),
                (0, 0, 170),
                (0, 140, 0),
                (150, 140, 0),
                (175, 75, 0),
                (200, 0, 0),
            ),

        Authored, not scaled, on the reasoning NIGHT_PALETTE already
        records. The values were selected against four computed
        constraints and the test suite re-asserts all four:

          - band_centres against white: >= 4.5:1. This fill is
            persistent, so the readout must meet the normal-text
            threshold against it. Worst case 7.36:1, day band 3.
          - band_centres relative luminance: <= 0.10. Worst case
            0.0927, day band 3, against 0.578 for the face
            change-5014040c removed.
          - band_centres_lit against white: >= 3:1. The lit phase is
            transient and the readout is 72 px, well past WCAG's 24 px
            large-text boundary, so the large-text threshold applies.
            Worst case 3.47:1, night band 3. Do not tighten this to
            4.5:1 — night bands 2 and 3 cannot satisfy it without
            dimming, and dimming breaks the flash constraint below.
          - band_centres_lit against shift_centre_dark, bands 3 to 5:
            >= 3:1. Worst case 3.39:1, night band 5, against a 5.68:1
            day and 2.59:1 night baseline for the green flash it
            replaces.

        Update the comment at models.py:109-112, which enumerates "the
        five colours returned by _get_shift_cue". There are now four
        border and centre constants plus two tuples.
    - path: "src/gtach/display/manager.py"
      content: |
        THREE EDITS.

        EDIT B — _get_shift_cue takes the band.

        The signature becomes:

            def _get_shift_cue(self, rpm: float, active_band: int) -> Tuple[Tuple[int, int, int], int, bool, Tuple[int, int, int]]:

        Document active_band in the Args section: "Active band index
        from _get_band_colour, hysteresised. Selects the centre disc
        fill."

        The three branches keep their conditions, their border colours
        and their border widths. Only the centre changes:

            if rpm >= bands.caution_start:
                # Upshift cue. The border stays green — it says what
                # the driver should DO. The centre takes the band's
                # colour, which says what the engine IS DOING, and
                # flashes against the dark phase to carry the shift
                # imperative on the temporal channel (change-64d8d8fc).
                centre = (
                    palette.band_centres_lit[active_band] if flash
                    else palette.shift_centre_dark
                )
                return palette.shift_border_caution, 12, True, centre
            elif rpm <= bands.torque_start:
                return (palette.shift_border_down, 12, False,
                        palette.band_centres[active_band])
            else:
                return (palette.shift_border_normal, 12, False,
                        palette.band_centres[active_band])

        The fallback becomes:

            return (DAY_PALETTE.shift_border_normal, 12, False,
                    DAY_PALETTE.band_centres[0])

        Index 0, not active_band — the fallback runs precisely when the
        band cannot be trusted.

        The flash-phase computation above the branches is unchanged.

        EDIT C — one lookup each, one arc.

        Today _draw_radial_mode calls _get_shift_cue at manager.py:1198
        for the border and again at manager.py:1336 for the centre, and
        _get_band_colour once at manager.py:1219. Both _get_shift_cue
        calls have identical inputs and the frame counter does not
        advance between them, so they agree by accident rather than by
        construction. Collapse them.

        Immediately after the palette is read at manager.py:1148, and
        BEFORE surface.fill, add:

            # One lookup each per frame. _get_band_colour's sticky
            # selection advances at most one band per call, so a second
            # call would halve the effective hysteresis — which now
            # governs the whole sweep and the centre disc, not one
            # segment (change-64d8d8fc).
            active_band, band_colour = self._get_band_colour(rpm)
            border_colour, _, _, centre_colour = self._get_shift_cue(
                rpm, active_band
            )

        At manager.py:1198, keep self._draw_shift_border(border_colour)
        and delete the _get_shift_cue call on that line.

        Delete the _get_band_colour call at manager.py:1219.

        Replace the whole of step 4 — the comment block at
        manager.py:1213-1217, the segment_bounds tuple at 1224-1232 and
        the loop at 1234-1255 — with:

            # 4. Draw the filled sweep in the active band's colour.
            #    One colour, not six: reading the zone from a graduated
            #    arc means localising the sweep's leading edge and then
            #    judging which band it falls in, and both stages degrade
            #    in peripheral vision. A uniform sweep makes it a single
            #    colour judgement. The headroom cue the graduation
            #    carried moves to the bolded boundary marks at step 9
            #    (change-64d8d8fc; withdraws prompt-5014040c's
            #    graduated-arc constraint).
            if rpm > 0:
                draw_donut_arc(
                    band_colour,
                    rpm_to_angle_rad(0),
                    rpm_to_angle_rad(rpm),
                )

        The local `bands = self.config.rpm_bands` at manager.py:1218 is
        still needed by step 9. Keep it, moving it if the deletion
        leaves it stranded.

        At manager.py:1336, delete the second _get_shift_cue call.
        centre_colour is already in scope from the top of the method.
        The flash_centre flag was never read at that site and is
        discarded above with `_`.

        EDIT D — bold the boundary marks.

        The band boundary marks at step 9 are now the only indication of
        how much headroom remains before the next zone. At 3 px they are
        subordinate to the 7 px major ticks beside them. Change the line
        width at manager.py:1315 from 3 to 7 and extend the comment at
        manager.py:1294-1296:

            # 9. Draw band boundary marks at thresholds.
            #    7 px, matching the major ticks: with the sweep drawn in
            #    one colour these marks carry the whole of the
            #    anticipatory cue — where the next zone begins — and are
            #    distinguished from the major ticks by colour, not
            #    weight (change-64d8d8fc).

        Leave the 28 px mark length alone. The radial layout is
        undisturbed by the width change and the length is a single
        literal if on-target observation shows 7 px is insufficient.

success_criteria:
  - "python -m py_compile on both files passes."
  - "pytest tests/ passes with no new failures."
  - "_draw_radial_mode issues exactly one fill arc per frame."
  - "segment_bounds does not appear in manager.py."
  - "_get_band_colour and _get_shift_cue are each called exactly once per rendered frame, asserted by patching."
  - "_get_band_colour's text is byte-identical to its current text."
  - "_draw_shift_border's text is byte-identical to its current text."
  - "shift_border_caution, shift_border_normal and shift_border_down are byte-identical in both palettes."
  - "Palette.bands is byte-identical in both palettes."
  - "shift_centre_lit, shift_centre_normal and shift_centre_down appear nowhere in the source tree."
  - "White computes to >= 4.5:1 against all twelve band_centres entries and >= 3:1 against all twelve band_centres_lit entries."
  - "band_centres_lit[3..5] computes to >= 3:1 against shift_centre_dark in both palettes."
  - "Every band_centres entry has relative luminance <= 0.10."
  - "The band boundary mark width is 7."
  - "The centre readout is still white and still 72 px."
  - "No file other than src/gtach/display/models.py and src/gtach/display/manager.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "models"
        path: "src/gtach/display/models.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
    classes:
      - name: "Palette"
        module: "gtach.display.models"
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "_draw_radial_mode"
        module: "gtach.display.manager"
        signature: "_draw_radial_mode(self) -> None"
      - name: "_get_shift_cue"
        module: "gtach.display.manager"
        signature: "_get_shift_cue(self, rpm: float, active_band: int) -> Tuple[Tuple[int, int, int], int, bool, Tuple[int, int, int]]"
    constants:
      - name: "Palette.band_centres"
        module: "gtach.display.models"
      - name: "Palette.band_centres_lit"
        module: "gtach.display.models"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required. Invoke from the project root:
  implement ai/workspace/prompt/prompt-64d8d8fc-uniform-sweep-colour.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results.

  The two things easiest to get wrong.

  First, the call-count invariant. _get_band_colour mutates
  self._active_band and advances it at most one step per call. It is
  currently called once per frame and must remain so. If the
  restructuring in EDIT C leaves a second call anywhere — including
  inside _get_shift_cue, which must NOT call it — the effective
  hysteresis halves, and it now protects the entire coloured area of
  the gauge rather than one segment of it.

  Second, the border. There is an obvious-looking symmetry here that is
  wrong: if the centre takes the band colour, why not the border too?
  Because the border is the only remaining channel that says what the
  driver should do. At caution_start it turns green for "upshift now"
  while band 3 is yellow; band-colouring it would render that
  instruction yellow, then orange, then red as RPM rises. And bands 0
  and 1 are both blue, so a band-coloured border could not separate
  "safe downshift" from "idle". Leave it alone.

  The boundary mark width and the band_centres luminance are the two
  values most likely to come back for revision after observation on
  gtach.local. Both are single literals, deliberately.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-64d8d8fc. |

---

Copyright (c) 2026 William Watson. MIT License.
