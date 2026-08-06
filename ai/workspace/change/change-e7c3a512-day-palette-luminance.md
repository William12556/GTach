Created: 2026 August 05

# Change: Take the Glare Out of Torque and Caution

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-e7c3a512"
  title: "DAY_PALETTE.bands index 2 becomes (0, 170, 0) and index 3 becomes (205, 180, 0), halving the luminance of the torque and caution bands while holding hue and legibility; the night palette and all other bands are unchanged"
  date: "2026-08-05"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e7c3a512"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-e7c3a512"
  description: >
    Resolves issue-e7c3a512. Raised under P04 from the operator's
    observation of 2026-08-05 that the day green and yellow are too
    bright while the night palette reads well.

scope:
  summary: >
    Two tuples in one file.
  affected_components:
    - name: "DAY_PALETTE.bands"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "NIGHT_PALETTE, in its entirety. The operator finds it good, and change-5012004e's day/night separation exists so the two can be tuned independently."
    - "band_centres and band_centres_lit in both palettes. Introduced by change-64d8d8fc and already dim; the day caution centre is (89, 89, 0). Not implicated in the report."
    - "Day bands 0, 1, 4 and 5 — idle, torque approach, warning and danger. Unchanged; the report named green and yellow."
    - "The face colours — ground, track, tick, line, edge, label. change-5014040c set them and they are not the subject."
    - "src/gtach/display/manager.py. The consumers of palette.bands need no change; only the values move."
    - "The shift-cue colours and the flash. Urgency is carried by the flash, which is why this change does not attempt to make danger the brightest band."
    - "Triangular shift indicators. Proposed on 2026-08-05 and declined by the operator."

rational:
  problem_statement: >
    The day torque and caution bands are the two brightest elements on
    the panel at 0.715 and 0.928 relative luminance, against a danger
    band at 0.213. The instrument's brightness order runs almost exactly
    counter to its urgency order, and the two brightest states are the
    two that warrant least attention.
  proposed_solution: >
    Reduce those two bands to roughly half their luminance, holding hue
    and keeping every band well clear of the legibility threshold.
  alternatives_considered:
    - option: "Darken the ground further instead of the bands."
      reason_rejected: >
        The ground is already (16, 16, 16) at 0.005 luminance, one step
        from black. There is nothing left to take, and the disparity is
        between the bands rather than between band and ground."
    - option: "Brighten danger toward (255, 60, 60) so the ordering matches urgency."
      reason_rejected: >
        The only way to make danger the brightest band, since pure red
        is 0.2126 by definition. Rejected: it dilutes the redline
        convention for a property the shift-cue flash already supplies,
        and the operator's report was that green and yellow are too
        bright, not that red is too dim."
    - option: "Adopt the night values for day."
      reason_rejected: >
        Night torque is (0, 140, 0) at 0.188 and night caution
        (150, 140, 0) at 0.252. Those are chosen for darkness and would
        be marginal in direct sun, which is the condition the day
        palette exists for. The values here sit between the two."
    - option: "Scale both bands by a single factor."
      reason_rejected: >
        The same objection change-5012004e recorded against deriving the
        night palette by scaling: a uniform factor compresses the bands
        toward one another. These two are authored separately and their
        mutual separation is asserted."
  benefits:
    - "The two brightest elements on the instrument stop being the two that matter least."
    - "Torque falls below warning in brightness, so the ordering is closer to the urgency it accompanies."
    - "Less emitted light in daylight running, continuing what change-5014040c did for the face."
  risks:
    - risk: >
        Daylight legibility falls. A dimmer green in direct sun is the
        condition the day palette exists for.
      mitigation: >
        Both bands remain above 6:1 against the ground — torque at
        6.12:1 and caution at 9.17:1 — where the criterion applied
        elsewhere in this project is 3:1 for non-text. The values are
        also two named tuples, so a revision after observation costs one
        line each."
    - risk: >
        The bands become less distinguishable from one another,
        weakening the primary cue.
      mitigation: >
        Adjacent-band separation is asserted by CIE76 delta-E >= 25, the
        same criterion change-5012004e applied to the night set, rather
        than judged by eye."
    - risk: >
        Hue drifts — a dimmed yellow reading as olive or brown.
      mitigation: >
        Band 3 keeps its red and green channels within 15% of one
        another, which holds the hue in the yellow family. Asserted."
  benefits_measurement: >
    Torque luminance 0.7152 -> 0.287, a 60% reduction. Caution 0.9278 ->
    0.456, a 51% reduction. Brightest-to-dimmest spread across the five
    displayed bands: 13.0x -> 6.4x.

technical_details:
  current_behavior: >
    DAY_PALETTE.bands[2] is (0, 255, 0) and bands[3] is (255, 255, 0).
    They are consumed by the arc segments at manager.py:1043 and by the
    threshold marks at manager.py:1297-1302.
  proposed_behavior: >
    bands[2] becomes (0, 170, 0) and bands[3] becomes (205, 180, 0).
    Nothing else changes.
  implementation_approach: >
    ONE EDIT. Two tuples in DAY_PALETTE.bands, with a comment recording
    the measured luminances and why the reduction was made, so the
    values are not restored to full saturation by a later reader who
    reads them as arbitrary.

    Measured outcome, against ground (16, 16, 16):

      band 2 torque   (0, 170, 0)     lum 0.287   contrast 6.12:1
      band 3 caution  (205, 180, 0)   lum 0.456   contrast 9.17:1

    with the unchanged bands for reference:

      band 1 idle     (0, 0, 255)     lum 0.072   contrast 2.21:1
      band 4 warning  (255, 128, 0)   lum 0.367   contrast 7.56:1
      band 5 danger   (255, 0, 0)     lum 0.213   contrast 4.76:1

    Band 1's 2.21:1 is below the 3:1 figure used elsewhere and is not
    correctable: pure blue is 0.0722 and cannot reach 3:1 against any
    ground darker than itself. That is recorded in ai/task.md §9.8.5
    item 3 as a criterion that cannot be met rather than a value to fix,
    and this change does not revisit it.
  code_changes:
    - component: "DAY_PALETTE"
      file: "src/gtach/display/models.py"
      change_summary: "bands[2] and bands[3] reduced in luminance; hue held."
      classes_affected:
        - "Palette"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "change-5014040c"
      impact: "Established the dark face these bands are drawn on. Not modified."
    - component: "change-5012004e"
      impact: "Established the day/night separation that lets the day set be tuned alone, and the delta-E criterion reused here. Not modified."
    - component: "change-64d8d8fc"
      impact: "Introduced band_centres and band_centres_lit. Not modified; the centre disc is not implicated."
  external: []
  required_changes:
    - change_ref: "change-5014040c"
      relationship: "related"

testing_requirements:
  test_approach: >
    Arithmetic on the palette constants. No rendering is involved: the
    consumers are unchanged and the values are read directly.
  test_cases:
    - scenario: "Luminance of DAY_PALETTE.bands[2]."
      expected_result: "<= 0.36, a reduction of at least 50% from 0.7152."
    - scenario: "Luminance of DAY_PALETTE.bands[3]."
      expected_result: "<= 0.51, a reduction of at least 45% from 0.9278."
    - scenario: "Contrast of every day band against ground."
      expected_result: ">= 4.5:1 for bands 2, 3, 4 and 5. Band 1 remains at 2.21:1, unchanged and not correctable."
    - scenario: "Band 2's channels."
      expected_result: "Green dominant; red and blue zero. Still green."
    - scenario: "Band 3's channels."
      expected_result: "Red and green within 15% of one another; blue zero. Still yellow rather than olive."
    - scenario: "CIE76 delta-E between each adjacent pair of day bands."
      expected_result: ">= 25 for every pair; the figures recorded."
    - scenario: "Luminance of band 2 against band 4."
      expected_result: "Band 2 lower — torque is no longer brighter than warning."
    - scenario: "NIGHT_PALETTE, field by field."
      expected_result: "Identical to before the change."
    - scenario: "band_centres and band_centres_lit in both palettes."
      expected_result: "Identical to before."
    - scenario: "Day bands 0, 1, 4 and 5."
      expected_result: "Identical to before."
    - scenario: "A rendered frame in each band, via the existing headless arrangement."
      expected_result: "The arc is drawn in the new colours; nothing else differs."
  regression_scope:
    - "tests/display/ — once populated per ai/task.md §8.2."
    - "On the panel in daylight: every band identifiable, and the torque and caution bands visibly calmer."
    - "On the panel: the night palette unchanged by long press."
  validation_criteria:
    - "python -m py_compile src/gtach/display/models.py passes."
    - "pytest tests/ passes with no new failures."
    - "Only DAY_PALETTE.bands indices 2 and 3 differ from the previous file."
    - "src/gtach/display/manager.py is byte-identical."

implementation:
  implementation_steps:
    - step: "Edit the two tuples and add the explanatory comment."
      owner: "Claude Code"
    - step: "Compute and record luminance, contrast and delta-E for the day set."
      owner: "Claude Code"
    - step: "Compile check and the existing suite."
      owner: "Claude Code"
    - step: "Observe on the panel in daylight and confirm every band remains identifiable."
      owner: "William Watson"
  rollback_procedure: >
    Single commit, one file, two tuples. git revert restores full
    saturation. No persisted state.
  deployment_notes: >
    Visible: the torque and caution arc segments are dimmer. If either
    proves marginal in direct sun, (0, 185, 0) and (215, 190, 0) are one
    notch brighter at 7.19:1 and 10.20:1, and the change is one line
    each.

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
    - change_ref: "change-5014040c"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-e7c3a512"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-e7c3a512."
      - "Recorded that brightening danger to match the urgency ordering was rejected: it dilutes the redline convention for a property the shift-cue flash already supplies, and the report was about green and yellow being too bright rather than red too dim."
      - "Recorded that adopting the night values wholesale was rejected as marginal in direct sun, the day palette existing for that condition; the chosen values sit between the two sets."
      - "Recorded a single scaling factor as rejected for the same reason change-5012004e rejected it for the night palette — it compresses the bands toward one another."
      - "Recorded band 1's 2.21:1 as unchanged and not correctable, pure blue being 0.0722, per ai/task.md §9.8.5 item 3."
      - "Recorded one brighter fallback pair should the values prove marginal in direct sun."

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
| 1.0 | 2026-08-05 | Initial change document coupled to issue-e7c3a512. Halves the day torque and caution band luminance, holding hue and legibility, leaving the night palette and all other bands untouched. |

---

Copyright (c) 2026 William Watson. MIT License.
