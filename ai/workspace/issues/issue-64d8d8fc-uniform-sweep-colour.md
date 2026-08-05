Created: 2026 August 05

# Issue: The Sweep Reads as One Zone, Not Six

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [2.0 Technical Notes](<#2.0 technical notes>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
issue_info:
  id: "issue-64d8d8fc"
  title: "RADIAL's filled sweep is drawn in one colour, that of the active band; boundary marks are bolded to carry the anticipatory cue the graduated arc used to carry; the centre disc takes the band colour while the shift border retains its own semantic"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-64d8d8fc"
    change_iteration: 1

source:
  origin: "requirement_change"
  description: >
    Human-originated cognitive-load requirement. The driver must be able
    to read the current RPM zone from the sweep without locating the
    sweep's leading edge against a fixed set of coloured bands. Reverses
    a constraint imposed by prompt-5014040c, which required the arc to
    remain graduated. See technical_notes.

affected_scope:
  components:
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._get_shift_cue"
      file_path: "src/gtach/display/manager.py"
    - name: "Palette"
      file_path: "src/gtach/display/models.py"
  version: "current"

behavior:
  expected: >
    The filled sweep from 0 to the current RPM is drawn in a single
    colour, that of the hysteresised active band. Band thresholds are
    marked by bold radial ticks so that headroom to the next zone
    remains readable. The centre disc is filled from the active band's
    colour. The shift border keeps its three-state semantic — green
    upshift, blue safe downshift, red normal — and is not band-coloured.
    The flash remains the upshift cue and nothing else.
  actual: >
    The sweep is graduated. Every segment below the leading one is drawn
    in its own band's colour (manager.py:1234-1255), so zone state must
    be inferred from the position of the sweep's leading edge rather
    than read from its colour. The centre disc is filled from a separate
    three-colour shift palette unrelated to the band. Band boundary
    marks are 3 px (manager.py:1315), subordinate to the 7 px major
    ticks beside them.

resolution:
  assigned_to: "Claude Code"
  approach: "Per change-64d8d8fc."
  change_ref: "change-64d8d8fc"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial issue creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Technical Notes

### 2.1 This reverses an explicit prior constraint

`prompt-5014040c` stated, in `edge_cases` and again in `notes`:

> Do not collapse every segment to the active band's colour — that
> would erase the graduated arc.

That constraint is withdrawn here by human decision. It was correct
under the assumption that the graduated arc is the more informative
display; the present requirement rejects that assumption on
cognitive-processing grounds. The graduated arc requires the driver to
localise an edge and then judge which band that edge falls in — a
two-stage spatial task. A uniformly coloured sweep makes zone state a
single-stage colour judgement.

The anticipatory information the graduation carried — how much headroom
remains before the next zone — is not discarded. It moves to the band
boundary marks, which already exist at step 9 of `_draw_radial_mode`
and are bolded for the purpose.

[Return to Table of Contents](<#table of contents>)

### 2.2 The flash is already a shift cue only

Confirmed by inspection. `_get_shift_cue` (manager.py:1081) is the sole
producer of a flash phase in the renderer, and it flashes only when
`rpm >= caution_start`, which is the upshift condition. The earlier
danger-zone background flash was removed by `change-e4b7c3a1`. No other
condition flashes. The temporal channel is therefore free to carry the
shift imperative alone once colour is taken over by the band.

[Return to Table of Contents](<#table of contents>)

### 2.3 Why the shift border is not band-coloured

The obvious extension — colour the border to match the band as well —
is rejected. The border currently encodes what the driver should *do*;
the band encodes what the engine *is doing*. These are different
quantities and colouring them identically destroys the former:

- At `caution_start` the border turns green to mean "upshift now",
  while band 3 is yellow. Band-colouring the border would render the
  upshift instruction yellow, then orange, then red as RPM rises —
  the inverse of the instruction being given.
- Bands 0 and 1 are already blue, so a band-coloured border could not
  distinguish "safe downshift" from "idle".

The centre disc is a different case. It carries no independent semantic
of its own beyond echoing the border, so it is available to the band.

[Return to Table of Contents](<#table of contents>)

### 2.4 Hysteresis already exists and is sufficient

`_band_hysteresis = 75.0` RPM (manager.py:121), applied as a sticky
single-step selection in `_get_band_colour`. No new hysteresis is
required. The change does, however, make the hysteresis load-bearing
across a much larger area: previously it governed the colour of the
leading segment only, and now it governs the whole sweep and the centre
disc. `_get_band_colour` must therefore continue to be called exactly
once per frame, since each call may advance the sticky band by one step.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes          |
|---------|------------|------------------|
| 1.0     | 2026-08-05 | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
