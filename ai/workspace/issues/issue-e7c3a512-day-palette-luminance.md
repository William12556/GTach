Created: 2026 August 05

# Issue: The Band Colours Are Brightest Where They Matter Least

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-e7c3a512"
  title: "The day torque and caution band colours are the two brightest elements on the panel, at 0.715 and 0.928 relative luminance against a danger band at 0.213, so the instrument's brightness order runs almost exactly counter to its urgency order"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-e7c3a512"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Reported by the operator on 2026-08-05 after observing the day
    palette on the panel: green and yellow are too bright, while the
    night palette reads well. Quantified while scoping the report. Not a
    numbered item of either code review; the display review's §7.2 named
    full-field colour as a glare source and change-5014040c removed the
    field, leaving the band colours themselves unexamined.

affected_scope:
  components:
    - name: "DAY_PALETTE.bands"
      file_path: "src/gtach/display/models.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: "Day palette active, which is the default."
  steps:
    - "Observe the gauge with the RPM in the torque or caution band. The arc reads as noticeably brighter than the warning or danger bands."
    - "Read models.py DAY_PALETTE.bands indices 2 and 3: (0, 255, 0) and (255, 255, 0)."
    - "Compute WCAG relative luminance for each band against ground (16, 16, 16). See test_data."
    - "Order the bands by luminance and compare with their order by urgency."
  frequency: "always"
  reproducibility_conditions: "Day palette only. The operator reports the night palette as satisfactory."
  preconditions: "None."
  test_data: >
    MEASURED, day palette, against ground (16, 16, 16):

      band            colour           luminance   contrast
      1 idle/approach (0, 0, 255)        0.0722      2.21:1
      2 torque        (0, 255, 0)        0.7152     13.87:1
      3 caution       (255, 255, 0)      0.9278     17.72:1
      4 warning       (255, 128, 0)      0.3670      7.56:1
      5 danger        (255, 0, 0)        0.2126      4.76:1

    ORDER BY BRIGHTNESS   caution > torque > warning > danger > idle
    ORDER BY URGENCY      danger > warning > caution > torque > idle

    The two are close to inverted. The band meaning "good torque, keep
    going" is the second brightest element on the instrument, the band
    meaning "caution" is the brightest, and the band meaning "redline"
    is dimmer than both by a factor of three to four.

    WHY, in one line: green carries 0.7152 of the luminance coefficient
    and red only 0.2126, so a saturated green is inherently three times
    the brightness of a saturated red and yellow — being red plus green
    — is brighter still. The palette was chosen for hue distinctness and
    inherits this ordering from the colour space rather than from any
    decision.

    WHAT THIS IS NOT. It is not a contrast failure; every band is
    legible, at between 4.76:1 and 17.72:1. It is a distribution
    problem: attention is drawn to the wrong bands.

    THE NIGHT PALETTE ALREADY AVOIDS IT, which is why the operator finds
    it satisfactory. Night torque is (0, 140, 0) at 0.188 and night
    caution (150, 140, 0) at 0.252, against night danger (200, 0, 0) at
    0.127 — a spread of two to one rather than four to one.
  error_output: "None. A perceptual finding."

behavior:
  expected: >
    An instrument's most attention-getting states are the ones that most
    warrant attention, or at least are not the ones that warrant it
    least.
  actual: >
    Torque and caution are the brightest bands on the panel and danger
    is among the dimmest.
  impact: >
    Two, both mild. The instrument draws the eye during ordinary running
    and less so approaching the redline. And the overall emitted light
    in daylight running is higher than it needs to be, which is the
    concern display report §7.2 raised for the face and which
    change-5014040c addressed there without reaching the bands.

    Nothing is unreadable and no reading is wrong. The operator reports
    the display as otherwise good.
  workaround: >
    Switch to the night palette by long press, at the cost of daylight
    legibility.

environment:
  python_version: "3.9 on target"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    The six band colours were chosen as maximally distinct hues, which
    they are, and their relative brightness was never a criterion. In
    sRGB the luminance coefficients are fixed — 0.2126 red, 0.7152
    green, 0.0722 blue — so a palette selected for hue separation at
    full saturation inherits a brightness ordering it did not choose.
    change-5014040c removed the full-field glare and darkened the face
    but left the band colours at full saturation, so the disparity
    became more visible against the darker ground rather than less.
  technical_notes: >
    SCOPE IS TWO TUPLES. palette.bands drives the arc segments
    (manager.py:1043) and the six threshold marks
    (manager.py:1297-1302). The centre disc uses the separate
    band_centres and band_centres_lit sets introduced by
    change-64d8d8fc, which are already dim — day caution centre is
    (89, 89, 0) — and are not implicated in the report.

    THE NIGHT PALETTE IS NOT CHANGED. The operator finds it good, and
    change-5012004e's day/night separation exists precisely so the two
    can be tuned independently.

    RED CANNOT BE MADE THE BRIGHTEST, and this issue does not ask for
    it. Pure red is 0.2126 by definition; making danger the brightest
    band would require diluting it toward pink, which discards the
    redline convention for a property the flash already supplies.
    _get_shift_cue flashes the centre above caution_start, so urgency is
    carried by motion rather than by brightness — the band colour needs
    only to be identifiable. Correcting the ordering is therefore not
    the goal; compressing the spread is.

    WHAT THE OPERATOR DECIDED AGAINST, recorded so it is not revisited
    by accident: up and down triangular shift indicators were proposed
    on 2026-08-05 and declined. The colour-blindness argument for a
    shape cue — roughly 8% of men cannot reliably separate the green
    upshift border from the red normal border — remains on the record
    here without being actioned.
  related_issues:
    - issue_ref: "issue-5014040c"
      relationship: "related"
    - issue_ref: "issue-5012004e"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Reduce the day torque and caution band luminance by roughly half,
    holding hue and keeping every band well above the legibility
    threshold. See change-e7c3a512.
  change_ref: "change-e7c3a512"
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
    A palette chosen for hue distinctness inherits sRGB's luminance
    ordering whether or not that ordering suits the meaning of the
    colours. Where colours carry a rank — severity, urgency, depth —
    the brightness order is a design property and should be computed
    rather than left to the colour space.
  process_improvements: >
    change-5014040c computed contrast for every element against the new
    ground and recorded the figures, which is why this was quantifiable
    in minutes. It did not compare the bands with each other, which is
    the check that would have caught this.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/models.py passes."
    - "Day band 2 luminance is reduced by at least 50% from 0.7152."
    - "Day band 3 luminance is reduced by at least 45% from 0.9278."
    - "Every day band retains at least 4.5:1 contrast against the ground."
    - "Day band 2 remains recognisably green and band 3 recognisably yellow — the green channel dominates band 2, and bands 3's red and green channels remain within 15% of one another."
    - "Adjacent day bands remain mutually distinguishable by CIE76 delta-E >= 25, the criterion change-5012004e applied to the night set."
    - "Day band 2's luminance falls below day band 4's, so torque is no longer brighter than warning."
    - "NIGHT_PALETTE is byte-identical."
    - "band_centres and band_centres_lit are byte-identical in both palettes."
    - "Bands 0, 1, 4 and 5 are byte-identical in the day palette."
    - "On the panel: the arc is visibly calmer in the torque and caution bands and every band remains identifiable in daylight."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-e7c3a512"
  test_refs: []

notes: >
  Raised under P04 from the operator's observation of 2026-08-05. A
  scope extension agreed by consensus; not a code-review finding.

  issue_info.type is enhancement and severity low: nothing is
  unreadable and no reading is wrong. It is a distribution of attention
  rather than a fault.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial issue document from the operator's observation that the day green and yellow are too bright while the night palette reads well."
      - "Quantified the report: the band brightness order runs almost exactly counter to the urgency order, torque and caution being the two brightest elements and danger dimmer than both by three to four times."
      - "Recorded the cause as sRGB's fixed luminance coefficients — green 0.7152 against red 0.2126 — inherited by a palette selected for hue distinctness at full saturation."
      - "Recorded that this is a distribution problem rather than a contrast failure, every band measuring between 4.76:1 and 17.72:1."
      - "Recorded that red cannot be made the brightest band without discarding the redline convention, and that urgency is already carried by the shift-cue flash rather than by band brightness — so the goal is compressing the spread, not inverting it."
      - "Recorded the night palette as satisfactory and out of scope, and the operator's decision against triangular shift indicators, with the colour-blindness argument left on the record unactioned."

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
| 1.0 | 2026-08-05 | Initial issue document. Quantifies the operator's report as an inverted brightness-to-urgency ordering arising from sRGB's luminance coefficients. |

---

Copyright (c) 2026 William Watson. MIT License.
