Created: 2026 October 16

# Issue: DEVICE_LIST Slot Content Clipped and Signal Bars Illegible

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-d38362aa
  title: DEVICE_LIST slot text is clipped, signal bars are illegible, and screen
    space above the slot column is unused
  date: '2026-10-16'
  reporter: William Watson
  status: open
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-d38362aa
    change_iteration: 1
source:
  origin: on_device_observation
  test_ref: test-36b6ea95 (Session E, 2026-10-08)
  description: >
    ai/task.md open item "DEVICE_LIST signal bars are very small and easily
    missed (observed on the Pi, Session E, 2026-10-08)". Extended on
    2026-10-16 by William's observation that the band between the title
    and the slot column is unused, and confirmed by an on-device render
    of the current screen (SDL dummy driver, gtach.local).
affected_scope:
  components:
  - name: CircularPositioningEngine.calculate_focused_slot_layout
    file_path: src/gtach/display/setup_components/layout/circular_positioning.py
  - name: DeviceSurfaceRenderer.create_curved_device_surface
    file_path: src/gtach/display/setup_components/rendering/device_surfaces.py
  - name: SetupDisplayManager._render_device_list_screen and arrow constants
    file_path: src/gtach/display/setup.py
  designs:
  - design_ref: design-a3b4c5d6-component_display_setup_manager §5.3
  version: HEAD at 2026-10-16
reproduction:
  prerequisites: Two or more devices discovered (ELM327 emulator plus any other).
  steps:
  - Start setup and wait for the Select Device screen.
  - Observe the slot rows and the signal indicator on the right of each row.
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: >
    Device name, device type and signal strength are fully visible and
    legible in every slot; the slot column uses the available vertical
    space of the round display.
  actual: >
    (1) The type label is clipped at the slot bottom: it is blitted at
    y=24 in the 19 px font (ascent 22, measured on the Pi), placing its
    baseline at y=46 in a 43 px surface. (2) The dBm text is clipped and
    overlaps the type label. (3) Signal bars are 2 px wide and 3-12 px
    tall; unlit bars (60,60,70) are close to invisible on the slot
    background. (4) The band y≈64-142 between the title and the up arrow
    is empty except for the transient error line.
  impact: The user cannot reliably judge adapter signal strength or device
    type when choosing a device.
  workaround: ''
environment:
  python_version: 3.9.2 (Pi)
  os: Linux (Raspberry Pi Zero 2W)
  dependencies:
  - library: pygame
    version: 2.6.1
  domain: display
analysis:
  root_cause: >
    calculate_focused_slot_layout reuses _calculate_curved_geometry, which
    applies scale≈0.957 and opacity≈0.87 to every slot. This is a
    residue of the unbounded curved list and has no function in the fixed
    three-slot layout. It shrinks fonts to 22/19 px and bars to 2 px. The
    45 px slot height cannot hold name, type and dBm lines at the measured
    font heights (24 px font: height 35, ascent 28; 20 px font: height
    29, ascent 24). The middle slot is centred on y=240, so the column
    cannot grow without colliding with Back/Retry at y=340.
  technical_notes: >
    Measured on gtach.local 2026-10-16. Renders of the current screen and
    an Option A prototype are in ~/Documents/gtach-diag/ (outside the
    repository).
  related_issues:
  - issue_ref: issue-4005360c
    relationship: Made signal bars render; size tracked separately in task.md.
  - issue_ref: issue-479b2e51
    relationship: Introduced the three-slot layout.
resolution:
  assigned_to: ''
  target_date: ''
  approach: >
    Option A, agreed 2026-10-16. Shift the slot column up into the unused
    band and enlarge it (60 px slots, 10 px gap, column y=118-318,
    middle centre y=218); slot scale and opacity 1.0; redesigned slot
    interior with larger signal bars and no dBm text.
  change_ref: change-d38362aa
  resolved_date: ''
  resolved_by: ''
  fix_description: ''
verification:
  verified_date: ''
  verified_by: ''
  test_results: ''
  closure_notes: ''
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - On the Pi, name and type text are fully visible in all three slots.
  - On the Pi, lit and unlit signal bars are distinguishable in selected
    and unselected slots.
  verification_results: ''
traceability:
  design_refs:
  - design-a3b4c5d6-component_display_setup_manager
  change_refs:
  - change-d38362aa
  test_refs:
  - ''
notes: Closes the ai/task.md signal-bar item on resolution.
loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ''
  last_review_feedback: ''
version_history:
- version: '1.0'
  date: '2026-10-16'
  author: Claude
  changes:
  - Initial issue document.
metadata:
  copyright: Copyright (c) 2026 William Watson. MIT License.
  template_version: '1.0'
  schema_type: t03_issue
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-16 | Initial issue document. |

---

Copyright (c) 2026 William Watson. MIT License.
