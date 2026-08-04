Created: 2026 August 04

# Prompt: Darken the Gauge Face and Let the Ring Carry the Band

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-5014040c"
  task_type: "implementation"
  source_ref: "change-5014040c"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-5014040c"
    change_iteration: 1

context:
  purpose: >
    The RADIAL gauge face is a light-grey r=232 disc — 169,100 px of
    near-permanent brightness in a driver's forward field of view, on a
    panel whose backlight cannot be reduced in software. Its black ticks
    and numerals depend on that light ground. Separately,
    _get_band_colour still returns a text colour for a readout that no
    longer exists, and the arc that shows the band is coloured from a
    parallel threshold table that does not carry the hysteresis
    _get_band_colour holds.
  integration: >
    One file: src/gtach/display/manager.py. Executor is Claude Code;
    AEL is not used.

    PREREQUISITE — change-378703da MUST HAVE LANDED. It removes
    _draw_digital_mode and the full-field band fill that recommendation
    26 nominally targets, and it retains _get_band_colour specifically
    for this task. If _draw_digital_mode is still present in the file,
    STOP and report: this prompt is being executed out of order and the
    work would be deleted by 378703da.

    WHAT THIS TASK IS NOT. It is not "replace a full-field fill with a
    ring" — after 378703da there is no full-field fill. It is: darken
    the face, invert the ticks and numerals, give the band one owner,
    and drop a return value that has no consumer. See
    issue-5014040c technical_notes.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py."
    - "Do NOT alter the hysteresis block in _get_band_colour (manager.py:652-670). It is change-4c038bed's contribution and the whole reason the method survived 378703da. Only the palette's second column and the return statement change."
    - "Do NOT modify _get_shift_cue (manager.py:680-713). The centre disc belongs to the shift cue, not the band."
    - "Do NOT change the centre numeric readout added by 378703da. It stays white."
    - "Do NOT change the six band colours themselves. Blue, blue, green, yellow, orange, red are unchanged; only what they are drawn on changes."
    - "Do NOT change the shift border or the r=244 border ring (_draw_shift_border, manager.py:562)."
    - "Do NOT add a second band ring. The existing fill arc is the annulus."
    - "Do NOT hard-code any face colour more than once. 7.3.12 varies exactly these; they must be named constants."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Introduce named constants for the gauge face palette, apply them
    through _draw_radial_mode, reduce _get_band_colour to returning a
    band index and one colour, and colour the fill arc through it in
    place of the inline threshold table.
  requirements:
    functional:
      - "The r=232 ground is drawn in a named dark constant; (200, 200, 200) appears nowhere in _draw_radial_mode."
      - "Tick marks and numerals are drawn in a named light constant and reach >= 4.5:1 contrast against the ground."
      - "The headroom and inert arcs read as unfilled track against the ground."
      - "The zone boundary lines and inner edge ring remain visible — >= 3:1 against the ground."
      - "_get_band_colour returns Tuple[int, Tuple[int, int, int]] — the active band index and its colour."
      - "_get_band_colour's band selection, including hysteresis, is identical to the pre-change implementation."
      - "The fill arc's colour comes from _get_band_colour; the inline band_thresholds table is removed."
      - "The six band colours are unchanged."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Neutral to slightly positive. The same primitives are drawn; the inline table is replaced by a call that already runs"
      metric: "time"

design:
  architecture: >
    The face is a set of named colours in one place, because the next
    change varies all of them together. The band has one owner, so the
    hysteresis that stops the colour alternating at a threshold applies
    wherever the band is shown rather than only where it used to be
    shown.
  components:
    - name: "DisplayManager face palette constants"
      type: "constants"
      purpose: "Name the colours 7.3.12 will vary."
      logic:
        - "FACE_GROUND = (16, 16, 16) — the r=232 disc. Near-black rather than black, so the face is still distinguishable from the corners outside the viewport."
        - "FACE_TRACK = (58, 58, 58) — the headroom and inert arcs, reading as unfilled track."
        - "FACE_TICK = (225, 225, 225) — tick marks and numerals."
        - "FACE_LINE = (90, 90, 90) — zone boundary lines."
        - "FACE_EDGE = (70, 70, 70) — the inner edge ring."
        - "FACE_LABEL = (200, 80, 80) — the 'RPM x 1000' label, lightened from (200, 0, 0), which is too dark on this ground."
    - name: "DisplayManager._get_band_colour"
      type: "function"
      purpose: "Own the band identity."
      interface:
        inputs:
          - name: "rpm"
            type: "float"
        outputs:
          type: "Tuple[int, Tuple[int, int, int]]"
            
      logic:
        - "Palette becomes a flat six-tuple of colours; the second column goes."
        - "Return (band, palette[band]) instead of (bg_colour, text_colour)."
        - "The fallback at manager.py:677-678 returns (0, (0, 0, 0))."
        - "Everything between the palette and the return is unchanged."
    - name: "DisplayManager._draw_radial_mode"
      type: "function"
      purpose: "Draw the dark face and colour the arc from the band owner."
      logic:
        - "Apply the six constants at the eight sites."
        - "Replace the inline band_thresholds table with a call to _get_band_colour, keeping the cumulative segment drawing."
  dependencies:
    internal:
      - "change-378703da — prerequisite. Verify _draw_digital_mode is absent before starting."
      - "change-4c038bed — shipped. Its hysteresis is preserved and, for the first time, applies to the arc."
    external: []

error_handling:
  strategy: >
    Unchanged. _draw_radial_mode's existing handler at manager.py:989
    and _get_band_colour's at 675 both remain; only the fallback's
    return shape changes to match the new signature.
  exceptions:
    - exception: "Exception"
      condition: "Band calculation failure."
      handling: "Existing handler; returns (0, (0, 0, 0)) — band 0 and black — instead of the old ((0,0,0), (255,255,255))."
    - exception: "Exception"
      condition: "Anything in _draw_radial_mode."
      handling: "Existing handler at manager.py:989-990. Unchanged."
  logging:
    level: "ERROR, unchanged"
    format: "self.logger.error(f'Band colour calculation error: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "grep (200, 200, 200) in _draw_radial_mode."
      expected: "No occurrence."
    - scenario: "Contrast of FACE_TICK against FACE_GROUND, computed by the WCAG relative-luminance definition."
      expected: ">= 4.5:1."
    - scenario: "Contrast of FACE_LINE, FACE_EDGE and FACE_TRACK against FACE_GROUND."
      expected: ">= 3:1 each."
    - scenario: "Contrast of each of the six band colours against FACE_GROUND."
      expected: ">= 3:1 each."
    - scenario: "_get_band_colour return type at several RPM values."
      expected: "(int, (int, int, int)) in every case."
    - scenario: "Rising sweep 0 to 7000 in steps of 10."
      expected: "The band index sequence is identical to the pre-change implementation's, asserted against a copy of the old method."
    - scenario: "Falling sweep 7000 to 0 in steps of 10."
      expected: "Identical, including the hysteresis asymmetry against the rising sweep."
    - scenario: "RPM oscillating +/- 50 about torque_start, with the default 75 RPM hysteresis."
      expected: "The band index does not alternate."
    - scenario: "The same oscillation, asserted on the arc colour after the EDIT D rewiring."
      expected: "The arc colour does not alternate — a property it did not have before."
    - scenario: "An RPMBands with gaps narrower than twice the hysteresis margin."
      expected: "The margin clamp at manager.py:652-659 behaves as before; no band is unreachable."
    - scenario: "_get_band_colour raising internally, forced."
      expected: "Returns (0, (0, 0, 0)); the caller does not raise."
    - scenario: "_draw_radial_mode rendered once per band."
      expected: "The arc is drawn in the colour _get_band_colour returns for that RPM."
    - scenario: "The centre disc and readout."
      expected: "Unchanged — _get_shift_cue's fill, white numeral."
  edge_cases:
    - "rpm 0: no arc is drawn (manager.py:892 guards on rpm > band_start), so the face shows track only. The band index is still 0 and nothing raises."
    - "rpm at exactly a threshold: the hysteresis requires the value to clear it by the margin, so the band does not change. Unchanged from today and asserted."
    - "The arc segments are drawn cumulatively from 0 to the current RPM, so several band colours are on screen at once; _get_band_colour returns the ACTIVE band. The per-segment colours must continue to come from the band table for the segments below the active one. Do not collapse every segment to the active band's colour — that would erase the graduated arc."
    - "FACE_GROUND against the corners: the corners are filled (0, 0, 0) at manager.py:864 and the face is (16, 16, 16). The distinction is deliberate and slight; do not equalise them."
  validation:
    - "grep confirms each FACE_ constant is defined once and every face colour in _draw_radial_mode is one of them."
    - "git diff confirms the hysteresis block in _get_band_colour is unchanged."
    - "git diff confirms _get_shift_cue is unchanged."

deliverable:
  format_requirements:
    - "Edit the one file in place. Create no new file."
    - "Cite the review section in a comment where a change is motivated by one, following the existing convention."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        FOUR EDITS.

        EDIT A — the face palette. Add as class-level constants on
        DisplayManager, above __init__, with this comment:

            # Gauge face palette. The HyperPixel's backlight cannot be
            # reduced in software, so the face's own luminance is the
            # only control over emitted light. The previous
            # (200, 200, 200) ground put 169,100 px of near-maximum
            # brightness in the driver's forward field of view
            # (display review §7.2, recommendation 26). Named rather
            # than inlined because task 7.3.12 varies all of them
            # together for the night palette.
            FACE_GROUND = (16, 16, 16)
            FACE_TRACK = (58, 58, 58)
            FACE_TICK = (225, 225, 225)
            FACE_LINE = (90, 90, 90)
            FACE_EDGE = (70, 70, 70)
            FACE_LABEL = (200, 80, 80)

        EDIT B — apply them in _draw_radial_mode, at these eight sites:

          manager.py:867  circle r=232      (200,200,200) -> self.FACE_GROUND
          manager.py:872  headroom arc      (180,180,180) -> self.FACE_TRACK
          manager.py:878  inert arc         (180,180,180) -> self.FACE_TRACK
          manager.py:905  boundary lines    (60,60,60)    -> self.FACE_LINE
          manager.py:910  inner edge ring   (40,40,40)    -> self.FACE_EDGE
          manager.py:922  tick marks        (0,0,0)       -> self.FACE_TICK
          manager.py:931  numerals          (0,0,0)       -> self.FACE_TICK
          manager.py:970  'RPM x 1000'      (200,0,0)     -> self.FACE_LABEL

        Leave manager.py:864's surface.fill((0, 0, 0)) alone — those are
        the corners outside the circular viewport, not the face.

        EDIT C — _get_band_colour's return shape. The palette at
        manager.py:634-641 becomes a flat tuple of six colours:

            # Six band colours. The text-colour column that stood beside
            # these was consumed only by _draw_digital_mode, which
            # change-378703da removed; the RADIAL readout is
            # unconditionally white, so the pairing has no remaining
            # consumer (ai/task.md §7.3.14).
            palette = (
                (0, 0, 0),          # 0 idle
                (0, 0, 255),        # 1 torque approach
                (0, 255, 0),        # 2 torque
                (255, 255, 0),      # 3 caution
                (255, 128, 0),      # 4 warning
                (255, 0, 0),        # 5 danger
            )

        The signature becomes:

            def _get_band_colour(self, rpm: float) -> Tuple[int, Tuple[int, int, int]]:

        The return at manager.py:671-673 becomes:

            self._active_band = band
            return (band, palette[band])

        The fallback at manager.py:677-678 becomes:

            return (0, (0, 0, 0))

        EVERYTHING BETWEEN the palette and the return — the thresholds
        tuple, the gap computation, the margin clamp and the sticky
        selection at manager.py:643-670 — is unchanged, character for
        character. Update the docstring's Returns section to match the
        new shape.

        EDIT D — give the band one owner. Today the arc's colours come
        from an inline table at manager.py:882-889 that restates the six
        bands and carries no hysteresis, while _get_band_colour holds
        the hysteresis and has no caller.

        Call _get_band_colour once per frame, before the arc loop, to
        establish the active band and to apply the hysteresis:

            active_band, _active_colour = self._get_band_colour(rpm)

        Then keep the cumulative segment loop, but source its per-segment
        colours from the same palette rather than from a second table.
        Extract the palette to a module-level or class-level constant —
        BAND_COLOURS — used by both _get_band_colour and the loop, so
        there is one table.

        IMPORTANT: the segments below the active band keep their own
        colours. The arc is graduated — blue, then green, then yellow up
        to the current RPM — and must stay that way. Do NOT paint every
        segment in the active band's colour. What EDIT D changes is that
        the boundary at which the ARC's leading segment changes colour is
        now the hysteresised one, so a value oscillating about a
        threshold no longer flips the leading segment.

        Remove the inline band_thresholds list at manager.py:882-889 once
        the loop reads from BAND_COLOURS and the thresholds already held
        in self.config.rpm_bands.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "pytest tests/ passes with no new failures."
  - "_draw_digital_mode is absent — confirming change-378703da landed first."
  - "The six FACE_ constants are defined once and used at all eight sites."
  - "(200, 200, 200), (180, 180, 180), (60, 60, 60), (40, 40, 40) and (200, 0, 0) do not appear as colour literals in _draw_radial_mode."
  - "FACE_TICK against FACE_GROUND computes to >= 4.5:1; FACE_TRACK, FACE_LINE, FACE_EDGE and all six band colours to >= 3:1."
  - "_get_band_colour returns Tuple[int, Tuple[int, int, int]]."
  - "The band index sequence across rising and falling sweeps is identical to the pre-change implementation."
  - "manager.py:643-670 — the thresholds, gap, margin and sticky-selection block — is byte-identical to its current text."
  - "The inline band_thresholds table at manager.py:882-889 is gone."
  - "The arc remains graduated: a frame at 5000 RPM shows blue, green and yellow segments, not one colour."
  - "_get_shift_cue is byte-identical to its current text."
  - "The centre readout is still white."
  - "surface.fill((0, 0, 0)) at manager.py:864 is unchanged."
  - "No file other than src/gtach/display/manager.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "_draw_radial_mode"
        module: "gtach.display.manager"
        signature: "_draw_radial_mode(self) -> None"
      - name: "_get_band_colour"
        module: "gtach.display.manager"
        signature: "_get_band_colour(self, rpm: float) -> Tuple[int, Tuple[int, int, int]]"
    constants:
      - name: "FACE_GROUND"
        module: "gtach.display.manager"
      - name: "FACE_TRACK"
        module: "gtach.display.manager"
      - name: "FACE_TICK"
        module: "gtach.display.manager"
      - name: "FACE_LINE"
        module: "gtach.display.manager"
      - name: "FACE_EDGE"
        module: "gtach.display.manager"
      - name: "FACE_LABEL"
        module: "gtach.display.manager"
      - name: "BAND_COLOURS"
        module: "gtach.display.manager"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-5014040c-annular-band-indicator.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  Check the prerequisite before doing anything else. If
  _draw_digital_mode is still in manager.py, change-378703da has not
  landed and this prompt must not proceed.

  EDIT D is the part that is easy to get subtly wrong. The arc is
  graduated and must stay graduated; the hysteresis applies to which
  band is active, not to what colour the segments below it are drawn in.
  A version that paints the whole arc in the active band's colour will
  compile, run, and look plausible on a static screen — and will be
  wrong the moment the RPM crosses a band.

  The daylight observation on gtach.local is the one that may send this
  change back. A dark face is better at night and worse in direct sun,
  and no static analysis settles that trade. FACE_GROUND is a single
  constant precisely so a revision costs one line.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-5014040c. |

---

Copyright (c) 2026 William Watson. MIT License.
