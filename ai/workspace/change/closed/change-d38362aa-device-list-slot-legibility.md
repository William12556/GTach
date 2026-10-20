Created: 2026 October 16

# Change: DEVICE_LIST Slot Column Enlargement and Signal Bar Legibility

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Target Geometry](<#2. target geometry>)
- [3. Version History](<#3. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-d38362aa"
  title: "Shift and enlarge the DEVICE_LIST slot column; redesign the slot interior for legible text and signal bars"
  date: "2026-10-16"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-d38362aa"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-d38362aa"
  description: "Resolves issue-d38362aa and the ai/task.md signal-bar item."

scope:
  summary: >
    Option A, agreed 2026-10-16 and validated by an on-device prototype
    render. The slot column moves up into the unused band below the
    title and grows to 60 px slots with 10 px gaps. Slot scale and opacity
    become 1.0. The slot interior is laid out for the measured font
    metrics: name and type lines on the left, four larger signal bars on
    the right, no dBm text. The up arrow and error line move with the
    column. Back/Retry, the title and the down arrow are unchanged.
  affected_components:
    - name: "CircularPositioningEngine.calculate_focused_slot_layout"
      file_path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_type: "modify"
    - name: "DeviceSurfaceRenderer.create_curved_device_surface"
      file_path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_type: "modify"
    - name: "SetupDisplayManager (_ARROW_UP_BASE_Y, _render_device_list_screen error line)"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "DEVICE_LIST tests"
      file_path: "tests/test_device_list_focus.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-a3b4c5d6-component_display_setup_manager"
      sections:
        - "5.3 DEVICE_LIST Screen Behaviour"
  out_of_scope:
    - "Back/Retry buttons, the title, the down arrow and the no-devices message."
    - "Slot colours, borders, selection tint and the empty-slot frame style."
    - "Focus, swipe and touch behaviour (change-479b2e51)."
    - "get_signal_bars RSSI thresholds."
    - "Typography constants (FONT_BODY 24, FONT_SMALL_TEXT 20 unchanged)."
    - "Every other setup screen."

rational:
  problem_statement: >
    See issue-d38362aa. The 45 px slots cannot hold three text elements
    at the measured font heights, a residual 0.957 scale shrinks fonts
    and bars further, the bars are 2 px wide with near-invisible unlit
    bars, and the band between title and column is unused.
  proposed_solution: >
    Move the column centre from y=240 to y=218 and set slot height 60,
    gap 10 (column y=118-318). Force scale and opacity to 1.0 for the
    three fixed slots. Re-lay the slot interior using fixed offsets
    derived from the measured metrics. Replace the dBm text and 2 px
    bars with four 5 px bars in white (lit) and grey (unlit). Move the
    up arrow to y=102-114 and the error line to centre y=84, fitted to a
    220 px width.
  alternatives_considered:
    - option: "Option B: keep the column centred on y=240 and move Back/Retry down to y≈360-416."
      reason_rejected: "Buttons approach the bezel (corners ≈225 px from centre), break consistency with the other setup screens, and leave the top band unused."
    - option: "Enlarge the bars only."
      reason_rejected: "Does not fix the clipped type label or dBm text; the slot height is the constraint."
    - option: "56 px slots with 14 px gaps (first proposal)."
      reason_rejected: "On-device font metrics show two text lines need ≈58 px."
  benefits:
    - "Name, type and signal indicator fully visible (verified in prototype render)."
    - "Middle-slot touch target grows from 45 to 60 px high."
    - "Unused vertical space is put to use."
  risks:
    - risk: "The middle slot is no longer centred on the display axis, a documented invariant of change-479b2e51."
      mitigation: "Design §5.3, the method docstring and the centring test are updated in this change."
    - risk: "The error line edges at y=84 overrun the 200 px safe radius by ≈2 px."
      mitigation: "Accepted: transient message, inside the 238 px visible edge; text fitted to 220 px."
    - risk: "Long device names truncate (for example 'ELM327-Emul…')."
      mitigation: "Accepted; truncation is existing behaviour."

technical_details:
  current_behavior: "See issue-d38362aa behavior.actual."
  proposed_behavior: "See section 2, Target Geometry."
  implementation_approach: >
    Parameterise the slot column centre in calculate_focused_slot_layout
    and override scale/opacity after the curved-geometry call. Replace
    the scaled interior drawing in create_curved_device_surface with
    fixed offsets and class constants. Adjust two setup.py values. Update
    tests to the new geometry and add legibility tests.
  code_changes:
    - component: "layout"
      file: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_summary: "Defaults item_height=60, item_spacing=10; new column_centre_y=218; scale and opacity forced to 1.0; fallback branch matches."
      functions_affected:
        - "calculate_focused_slot_layout"
      classes_affected:
        - "CircularPositioningEngine"
    - component: "rendering"
      file: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_summary: "Fixed-offset slot interior; four 5 px bars; dBm text removed; new signal colour keys."
      functions_affected:
        - "create_curved_device_surface"
      classes_affected:
        - "DeviceSurfaceRenderer"
    - component: "setup"
      file: "src/gtach/display/setup.py"
      change_summary: "_ARROW_UP_BASE_Y 154 → 114; error line centre 118 → 84 via _fit_text(max_width=220); comments updated."
      functions_affected:
        - "_render_device_list_screen"
      classes_affected:
        - "SetupDisplayManager"
  data_changes: []
  interface_changes:
    - "calculate_focused_slot_layout gains keyword column_centre_y (default 218); defaults of item_height and item_spacing change. Single caller (setup.py)."

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-479b2e51"
      relationship: "related. Introduced the three-slot layout this change resizes."
    - change_ref: "change-4005360c"
      relationship: "related. Made the signal bars render."

testing_requirements:
  test_approach: "Unit tests for geometry and rendering; on-device visual verification."
  test_cases:
    - scenario: "Slot layout geometry."
      expected_result: "Slots y=118/188/258, height 60, scale 1.0, opacity 1.0; middle centre y=218; all within the 200 px safe radius; bottom edge ≤ 322."
    - scenario: "Arrow glyphs."
      expected_result: "Up arrow pixel at (240,108); down arrow pixel at (240,328); arrows clear the column and the buttons."
    - scenario: "Signal bars at RSSI -35 (4 bars) and -82 (0 bars)."
      expected_result: "Lit-colour pixels present for a strong signal; none for 0 bars; unlit-colour pixels present."
    - scenario: "On the Pi with the emulator and at least one other device."
      expected_result: "Name and type fully visible in all three slots; bars legible; error line between title and up arrow."
  regression_scope:
    - "tests/test_device_list_focus.py"
    - "tests/test_low_defects.py (signal strength)"
    - "tests/test_setup_and_gauge.py (DEVICE_LIST error render)"
  validation_criteria:
    - "pytest tests/ passes."
    - "On-device verification passes."

implementation:
  effort_estimate: "2 hours"
  implementation_steps:
    - step: "Implement per prompt-d38362aa."
      owner: "worker (Claude Code)"
    - step: "Update design-a3b4c5d6 §5.3."
      owner: "Claude (strategic)"
    - step: "On-device verification."
      owner: "William Watson"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Deploy with bin/deploy.sh; no configuration change."

verification:
  implemented_date: "2026-10-16"
  implemented_by: "Claude Code (commit e6db4e0)"
  verification_date: "2026-10-16"
  verified_by: "William Watson"
  test_results: "pytest tests/: 588 passed, 0 failed. On the Pi: layout correct, no clipping. Error-line position verified by prototype render and unit geometry; not triggered on the device."
  issues_found:
    - "Accepted deviations (report-d38362aa §7): _fit_text host entry in tests/test_setup_and_gauge.py; named constant BAR_BOTTOM_BELOW_CENTRE; private helper _draw_signal_bars."

traceability:
  design_updates:
    - design_ref: "design-a3b4c5d6-component_display_setup_manager"
      section: "5.3"
  related_changes:
    - change_ref: "change-479b2e51"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-d38362aa"
      relationship: "resolves"

notes: "Geometry validated by a prototype render on gtach.local, 2026-10-16. Locate code by symbol, not line number."

version_history:
  - version: "1.0"
    date: "2026-10-16"
    author: "Claude"
    changes:
      - "Initial change document resolving issue-d38362aa iteration 1."
  - version: "1.1"
    date: "2026-10-16"
    author: "William Watson"
    changes:
      - "Implemented (commit e6db4e0), verified on the Pi, closed; design-a3b4c5d6 §5.3 updated."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Target Geometry

All values in display pixels (480×480, centre 240,240). Font metrics measured on gtach.local, 2026-10-16.

| Element | Current | Target |
|---|---|---|
| Title centre | y=50 | unchanged |
| Error line centre | y=118 | y=84, `_fit_text` max 220 px |
| Up arrow (apex–base) | 142–154 | 102–114 |
| Slot height / gap | 45 / 10 | 60 / 10 |
| Slot y (top, middle, bottom) | 163, 218, 273 | 118, 188, 258 |
| Middle slot centre | y=240 | y=218 |
| Slot scale / opacity | ≈0.957 / ≈0.87 | 1.0 / 1.0 |
| Down arrow (base–apex) | 322–334 | unchanged |
| Back / Retry | y=340–400 | unchanged |

Slot interior (coordinates relative to the slot surface; `bg` height = 58):

| Element | Target |
|---|---|
| Type dot | centre (14, 29), radius 6 |
| Name | FONT_BODY (24 px), blit at (24, 0), truncated to `width − 79` |
| Type label | FONT_SMALL_TEXT (20 px), blit at (24, 27) |
| Signal bars | 4 bars, 5 px wide, 3 px gap, heights 8/14/20/26, bottom-aligned at y=42, left edge `width − 43` |
| Bar colours | lit (220,220,220), unlit (110,110,125) |
| dBm text | removed |

[Return to Table of Contents](<#table of contents>)

---

## 3. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-16 | Initial change document resolving issue-d38362aa iteration 1. |
| 1.1 | 2026-10-16 | Implemented (commit e6db4e0), verified on the Pi, closed; design-a3b4c5d6 §5.3 updated. |

---

Copyright (c) 2026 William Watson. MIT License.
