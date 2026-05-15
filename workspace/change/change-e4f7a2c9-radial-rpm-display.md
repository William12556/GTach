Created: 2026 May 15

# Change: Add RADIAL RPM Display Mode

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
change_info:
  id: "change-e4f7a2c9"
  title: "Add RADIAL RPM display mode"
  date: "2026-05-15"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e4f7a2c9"
    issue_iteration: 1

source:
  type: "enhancement"
  reference: "issue-e4f7a2c9"
  description: >
    Implement a new RADIAL display mode as a third RPM visualisation
    option alongside the existing DIGITAL and GAUGE modes.

scope:
  summary: >
    Add DisplayMode.RADIAL enum value, implement _draw_radial_mode()
    in DisplayManager, update swipe gesture routing to cycle through
    all three modes, and update config persistence.
  affected_components:
    - name: "DisplayMode"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "TouchHandler / gesture routing"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master.md"
      sections:
        - "8.3 Display Domain"
        - "9.1.3 DisplayConfig"
        - "13.4 Display Mode Flow"
  out_of_scope:
    - "Changes to DIGITAL or GAUGE rendering."
    - "New configuration parameters beyond existing rpm_bands/rpm_danger."
    - "Touch gesture changes beyond mode cycling."

rational:
  problem_statement: >
    Only two RPM display modes exist. A radial arc mode provides a more
    intuitive analogue-style visualisation without a traditional needle,
    better suited to the circular display form factor.
  proposed_solution: >
    Add a RADIAL mode rendered as a donut arc from 7 o'clock to 5 o'clock
    (300 degree active sweep). The filled portion tracks current RPM using
    existing RPMBands colours; headroom is light grey. The inert bottom arc
    carries the 'RPM x 1000' label; the centre circle carries 'GTach'.
    Danger zone triggers a 2 Hz red/black flash on the centre circle.
  alternatives_considered:
    - option: "Traditional needle gauge"
      reason_rejected: "Already implemented as GAUGE mode."
    - option: "Vertical bar fill"
      reason_rejected: "Inconsistent with circular display form factor."
  benefits:
    - "Intuitive radial fill — RPM progress immediately visible."
    - "Band colours retained — consistent visual language with DIGITAL mode."
    - "No numeric readout clutter — purely visual."
    - "Danger flash on centre circle provides peripheral alert."
  risks:
    - risk: "Performance: arc drawing more expensive than simple fill."
      mitigation: "Use pygame.draw.arc with pre-computed angles; profile on Pi."
    - risk: "Danger flash uses time.monotonic() — consistent with existing pattern."
      mitigation: "Reuse _get_band_colour() flash logic pattern."

technical_details:
  current_behavior: >
    DisplayMode enum contains SPLASH, DIGITAL, GAUGE, SETTINGS,
    ACKNOWLEDGEMENT. Swipe gestures toggle between DIGITAL and GAUGE.
    _draw_digital_mode() and _draw_gauge_mode() exist in DisplayManager.
  proposed_behavior: >
    DisplayMode gains RADIAL value. _draw_radial_mode() is added to
    DisplayManager. Swipe gesture cycles DIGITAL -> GAUGE -> RADIAL -> DIGITAL.
    Config persistence saves/loads RADIAL as a valid mode name.
  implementation_approach: >
    1. Add RADIAL to DisplayMode enum in models.py.
    2. Implement _draw_radial_mode() in manager.py using pygame arc drawing.
    3. Update _render_normal_modes() to dispatch to _draw_radial_mode().
    4. Update swipe handlers to cycle through three modes.
    5. No new config fields required — rpm_bands and rpm_danger already present.

  code_changes:
    - component: "DisplayMode"
      file: "src/gtach/display/models.py"
      change_summary: "Add RADIAL = auto() to DisplayMode enum."
      functions_affected: []
      classes_affected:
        - "DisplayMode"

    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Add _draw_radial_mode() method. Update _render_normal_modes()
        dispatch. Update _handle_swipe_left() and _handle_swipe_right()
        to cycle DIGITAL -> GAUGE -> RADIAL -> DIGITAL.
      functions_affected:
        - "_draw_radial_mode"
        - "_render_normal_modes"
        - "_handle_swipe_left"
        - "_handle_swipe_right"
      classes_affected:
        - "DisplayManager"

    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: >
        Update mode toggle logic to include RADIAL in the cycle.
      functions_affected:
        - "handle_touch_event (or equivalent toggle)"
      classes_affected: []

  interface_changes: []
  data_changes: []

dependencies:
  internal:
    - component: "RPMBands"
      impact: "Read-only — band colours and thresholds consumed unchanged."
    - component: "DisplayConfig"
      impact: "rpm_danger threshold read for flash trigger; no new fields."
    - component: "_get_band_colour"
      impact: "Reused for fill colour selection per RPM value."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Manual visual test on Pi using --transport simbt."
  test_cases:
    - scenario: "RPM = 0: arc shows full grey headroom, no fill."
      expected_result: "Grey arc 7 o'clock to 5 o'clock. Centre dark, GTach label visible."
    - scenario: "RPM = 3500: arc shows blue fill to approx 1/3 of sweep."
      expected_result: "Blue fill, grey headroom, white indicator line at correct position."
    - scenario: "RPM = 6000 (>= danger_start 5800): centre circle flashes."
      expected_result: "Red/black 2 Hz flash on centre circle. Fill in red band."
    - scenario: "Swipe left/right: cycles through all three modes."
      expected_result: "DIGITAL -> GAUGE -> RADIAL -> DIGITAL cycling confirmed."
    - scenario: "Config save/load: RADIAL persists across restart."
      expected_result: "App restarts in RADIAL mode if last saved mode was RADIAL."
  regression_scope:
    - "DIGITAL mode rendering unchanged."
    - "GAUGE mode rendering unchanged."
    - "Swipe gesture still functional in DIGITAL and GAUGE."
  validation_criteria:
    - "All arc geometry correct: 7 o'clock start, 5 o'clock end, 300 degree sweep."
    - "Band colours match existing RPMBands thresholds."
    - "Graduation marks visible at 1000 RPM intervals (labelled 1-7)."
    - "Band boundary marks coloured per band."
    - "White indicator line tracks RPM accurately."
    - "Centre circle danger flash at 2 Hz above danger_start."
    - "GTach label visible in centre; RPM x 1000 in lower inert arc."

implementation:
  implementation_steps:
    - step: "Add RADIAL to DisplayMode enum."
      owner: "Claude Code"
    - step: "Implement _draw_radial_mode() in DisplayManager."
      owner: "Claude Code"
    - step: "Update _render_normal_modes() dispatch."
      owner: "Claude Code"
    - step: "Update swipe handlers for three-mode cycle."
      owner: "Claude Code"
    - step: "Update touch.py mode toggle."
      owner: "Claude Code"
  rollback_procedure: "Revert changes to models.py, manager.py, touch.py."
  deployment_notes: "Build wheel, deploy to Pi, test with --transport simbt."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates:
    - design_ref: "design-gtach-master.md"
      sections_updated:
        - "8.3 Display Domain"
        - "9.1.3 DisplayConfig"
        - "13.4 Display Mode Flow"
      update_date: ""
  related_changes: []
  related_issues:
    - issue_ref: "issue-e4f7a2c9"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-05-15"
    author: "William Watson"
    changes:
      - "Initial change document creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes          |
|---------|------------|------------------|
| 1.0     | 2026-05-15 | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
