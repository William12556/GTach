Created: 2026 August 05

# Prompt: Take the Glare Out of Torque and Caution

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-e7c3a512"
  task_type: "implementation"
  source_ref: "change-e7c3a512"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-e7c3a512"
    change_iteration: 1

context:
  purpose: >
    The day torque and caution bands are the two brightest elements on
    the panel — 0.715 and 0.928 relative luminance — against a danger
    band at 0.213. The instrument's brightness order runs almost exactly
    counter to its urgency order. The operator reports green and yellow
    as too bright in daylight and the night palette as good.
  integration: >
    One file: src/gtach/display/models.py. Two tuples. Executor is
    Claude Code; AEL is not used.

    This is a values change. No consumer needs modifying: palette.bands
    already drives the arc segments at manager.py:1043 and the threshold
    marks at manager.py:1297-1302, and both read whatever is there.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/models.py."
    - "Modify only DAY_PALETTE.bands indices 2 and 3. Every other value in that tuple, and every other field of DAY_PALETTE, stays."
    - "Do NOT touch NIGHT_PALETTE. The operator finds it good."
    - "Do NOT touch band_centres or band_centres_lit in either palette. Those are the centre disc, already dim, and not what was reported."
    - "Do NOT brighten the danger band to correct the ordering. Pure red is 0.2126 by definition and diluting it toward pink discards the redline convention for a property the shift-cue flash already supplies."
    - "Do NOT alter the face colours — ground, track, tick, line, edge, label. change-5014040c set them."
    - "Do NOT touch band 1's (0, 0, 255). Its 2.21:1 is below the 3:1 used elsewhere and is not correctable — pure blue is 0.0722 and cannot reach 3:1 against any ground darker than itself. Recorded in ai/task.md §9.8.5 item 3."
    - "Do NOT modify src/gtach/display/manager.py."
    - "PEP 8; keep the existing comment style in this file, which records the reasoning behind each colour group."

specification:
  description: >
    Reduce the day torque and caution band luminance by roughly half,
    holding hue and legibility.
  requirements:
    functional:
      - "DAY_PALETTE.bands[2] is (0, 170, 0)."
      - "DAY_PALETTE.bands[3] is (205, 180, 0)."
      - "Every other value in DAY_PALETTE is unchanged."
      - "NIGHT_PALETTE is unchanged."
      - "A comment records the measured luminances and the reason, so the values are not read as arbitrary and restored."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.9)"
      standards:
        - "Professional docstrings"
  performance:
    - target: "None. Constant values"
      metric: "time"

design:
  architecture: >
    Colours that carry a rank should have a brightness order chosen
    rather than inherited from the colour space. sRGB weights green at
    0.7152 and red at 0.2126, so a palette picked for hue distinctness
    at full saturation makes green and yellow dominate whatever they
    mean.
  components:
    - name: "DAY_PALETTE.bands"
      type: "constant"
      purpose: "The arc segments and threshold marks."
      logic:
        - "Index 2, torque: (0, 255, 0) -> (0, 170, 0). Luminance 0.7152 -> 0.287, contrast 6.12:1."
        - "Index 3, caution: (255, 255, 0) -> (205, 180, 0). Luminance 0.9278 -> 0.456, contrast 9.17:1."
        - "Index 3 keeps red and green within 15% of one another so the hue stays yellow rather than drifting to olive."
  dependencies:
    internal:
      - "manager.py:1043 and 1297-1302 — the consumers. Read-only, unmodified."
    external: []

error_handling:
  strategy: "None applicable. Constant values."
  exceptions:
    - exception: "None."
      condition: "n/a"
      handling: "n/a"
  logging:
    level: "None"
    format: "n/a"

testing:
  unit_tests:
    - scenario: "Relative luminance of DAY_PALETTE.bands[2], by the WCAG definition."
      expected: "<= 0.36. Record the figure."
    - scenario: "Relative luminance of DAY_PALETTE.bands[3]."
      expected: "<= 0.51. Record the figure."
    - scenario: "Contrast of bands 2, 3, 4 and 5 against DAY_PALETTE.ground."
      expected: ">= 4.5:1 each."
    - scenario: "Contrast of band 1 against ground."
      expected: "2.21:1, unchanged. Assert it is unchanged rather than that it passes."
    - scenario: "Band 2's channel values."
      expected: "Green non-zero, red and blue zero."
    - scenario: "Band 3's channel values."
      expected: "abs(r - g) / max(r, g) <= 0.15; blue zero."
    - scenario: "CIE76 delta-E between each adjacent pair of day bands."
      expected: ">= 25 for every pair. Record all five figures."
    - scenario: "Luminance of band 2 compared with band 4."
      expected: "Band 2 strictly lower — torque no longer brighter than warning."
    - scenario: "NIGHT_PALETTE compared field by field with its previous values."
      expected: "Identical."
    - scenario: "DAY_PALETTE.band_centres and band_centres_lit."
      expected: "Identical to before."
    - scenario: "DAY_PALETTE bands 0, 1, 4, 5 and every non-band field."
      expected: "Identical to before."
    - scenario: "A rendered frame per band through the existing headless arrangement."
      expected: "The arc uses the new colours; no other drawing call differs."
  edge_cases:
    - "Band 0 and band 1 are both (0, 0, 255) and both stay. Band 0 is never displayed as an arc segment — rpm > band_start gates it — but it is part of the tuple and must not be disturbed."
    - "The threshold marks at manager.py:1297-1302 use the same tuple, so they dim with the arc. That is intended: they are the same information at the rim."
    - "delta-E between bands 0 and 1 is zero, they being the same colour. Exclude that pair from the adjacent-separation assertion, or the test fails on a pre-existing and deliberate duplication."
  validation:
    - "git diff shows exactly two changed value lines plus the added comment."
    - "grep confirms NIGHT_PALETTE is untouched."

deliverable:
  format_requirements:
    - "Edit the one file in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/display/models.py"
      content: |
        ONE EDIT, in DAY_PALETTE.

        Replace:

            bands=(
                (0, 0, 255),        # 0 idle
                (0, 0, 255),        # 1 torque approach
                (0, 255, 0),        # 2 torque
                (255, 255, 0),      # 3 caution
                (255, 128, 0),      # 4 warning
                (255, 0, 0),        # 5 danger
            ),

        with:

            # Torque and caution were the two brightest elements on the
            # panel — 0.715 and 0.928 relative luminance against a
            # danger band at 0.213 — so the instrument's brightness
            # order ran almost exactly counter to its urgency order,
            # and the operator reported both as too bright in daylight
            # (issue-e7c3a512).
            #
            # sRGB weights green at 0.7152 and red at 0.2126, so a
            # palette chosen for hue distinctness at full saturation
            # inherits that ordering rather than choosing it. These two
            # values are set deliberately and are not arbitrary; they
            # sit between the previous full-saturation pair and the
            # night set, and were measured against ground (16, 16, 16):
            #
            #   2 torque   (0, 170, 0)     lum 0.287   6.12:1
            #   3 caution  (205, 180, 0)   lum 0.456   9.17:1
            #
            # Band 1's 2.21:1 is below the 3:1 used elsewhere and is not
            # correctable — pure blue is 0.0722 and cannot reach 3:1
            # against any ground darker than itself
            # (ai/task.md §9.8.5 item 3). Danger is deliberately not
            # brightened to lead the ordering: urgency is carried by the
            # shift-cue flash, not by band brightness.
            bands=(
                (0, 0, 255),        # 0 idle
                (0, 0, 255),        # 1 torque approach
                (0, 170, 0),        # 2 torque
                (205, 180, 0),      # 3 caution
                (255, 128, 0),      # 4 warning
                (255, 0, 0),        # 5 danger
            ),

        Change nothing else in the file. In particular NIGHT_PALETTE,
        band_centres and band_centres_lit all stay exactly as they are.

success_criteria:
  - "python -m py_compile src/gtach/display/models.py passes."
  - "pytest tests/ passes with no new failures."
  - "DAY_PALETTE.bands[2] == (0, 170, 0) and bands[3] == (205, 180, 0)."
  - "Luminance of bands[2] <= 0.36 and of bands[3] <= 0.51, with both figures recorded."
  - "Bands 2, 3, 4 and 5 each reach >= 4.5:1 against DAY_PALETTE.ground."
  - "Band 1 remains (0, 0, 255) at 2.21:1."
  - "Band 3's red and green channels are within 15% of one another."
  - "Adjacent day bands are separated by CIE76 delta-E >= 25, excluding the identical 0/1 pair, with all figures recorded."
  - "Band 2's luminance is strictly below band 4's."
  - "NIGHT_PALETTE is byte-identical."
  - "DAY_PALETTE.band_centres and band_centres_lit are byte-identical."
  - "DAY_PALETTE bands 0, 1, 4 and 5 and every non-band field are byte-identical."
  - "src/gtach/display/manager.py is byte-identical."
  - "No file other than src/gtach/display/models.py is modified."

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
    functions: []
    constants:
      - name: "DAY_PALETTE"
        module: "gtach.display.models"
      - name: "NIGHT_PALETTE"
        module: "gtach.display.models"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-e7c3a512-day-palette-luminance.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results. Then, once you are finished, write
  a report of what you have done in the ai/workspace/report folder.

  This is the smallest change in the project to date and needs no
  cleverness. The one thing worth resisting is the temptation to
  "finish the job" by brightening danger so the ordering matches
  urgency. Pure red is 0.2126 and making it lead would mean diluting it
  toward pink; the redline convention is worth more than a monotonic
  brightness ramp, and the shift-cue flash already supplies the urgency.

  If either value proves marginal in direct sun, (0, 185, 0) and
  (215, 190, 0) are one notch brighter at 7.19:1 and 10.20:1. Report
  that rather than adjusting on your own judgement — the operator sees
  the panel and you do not.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-e7c3a512. |

---

Copyright (c) 2026 William Watson. MIT License.
