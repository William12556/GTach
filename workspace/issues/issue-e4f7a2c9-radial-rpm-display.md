Created: 2026 May 15

# Issue: Radial RPM Display Mode

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
issue_info:
  id: "issue-e4f7a2c9"
  title: "Add RADIAL RPM display mode"
  date: "2026-05-15"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4f7a2c9"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    GTach currently provides DIGITAL and GAUGE display modes. A third mode
    is required: a radial arc display that uses a swept fill to indicate
    RPM rather than a numeric readout or needle gauge.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayMode"
      file_path: "src/gtach/display/models.py"
    - name: "DisplayConfig"
      file_path: "src/gtach/display/models.py"
  designs:
    - design_ref: "design-gtach-master.md"
    - design_ref: "design-2c6b8e4d-domain_display.md"
  version: "current"

reproduction:
  prerequisites: "GTach running in any transport mode."
  steps:
    - "Observe that only DIGITAL and GAUGE modes are available via swipe gesture."
  frequency: "always"
  reproducibility_conditions: "N/A — enhancement, not a defect."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    A third display mode RADIAL is available. It presents RPM as a
    radial arc sweeping from 7 o'clock to 5 o'clock (via the top),
    covering 300 degrees. The arc is divided into a coloured fill
    region (0 to current RPM, using RPMBands colours) and a light
    grey headroom region (current RPM to maximum 7000 RPM). The bottom
    arc segment is an inert dark grey zone containing the 'RPM x 1000'
    label. The centre of the display is a dark circle containing the
    'GTach' label in red. Graduation marks at 1000 RPM intervals
    (white, labelled 1-7) and coloured band boundary marks are placed
    on the outer circumference. A white indicator line spans the arc
    at the current RPM position. In the danger zone (>= danger_start),
    the centre circle flashes red/black at 2 Hz.
  actual: >
    No RADIAL mode exists. Only DIGITAL and GAUGE are available.
  impact: >
    Missing display option. Existing modes are unaffected.
  workaround: "Use DIGITAL or GAUGE mode."

environment:
  python_version: "3.9+"
  os: "Raspberry Pi OS (Debian Linux)"
  dependencies:
    - library: "pygame"
      version: ">=2.0"
  domain: "domain_2"

analysis:
  root_cause: >
    RADIAL mode has not been designed or implemented. New display
    mode requires: enum addition to DisplayMode, new render method
    _draw_radial_mode() in DisplayManager, swipe gesture routing
    update, and config persistence update.
  technical_notes: >
    Arc geometry: 7 o'clock = 210 degrees clock, 5 o'clock = 150
    degrees clock, active sweep = 300 degrees clockwise via top.
    RPM ceiling = 7000. Donut arc: outer radius ~198px, inner radius
    ~88px (wide band). Danger flash: 2 Hz red/black on centre circle
    when rpm >= danger_start. Graduation marks: 1000 RPM major ticks
    (white, labelled 1-7); band boundary marks (coloured per band,
    longer tick). White indicator line at current RPM spans full arc
    band width. Centre circle: dark background, 'GTach' label in red.
    Lower inert arc: dark grey, 'RPM x 1000' label in red.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: "Implement per change-e4f7a2c9."
  change_ref: "change-e4f7a2c9"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

traceability:
  design_refs:
    - "design-gtach-master.md"
    - "design-2c6b8e4d-domain_display.md"
  change_refs:
    - "change-e4f7a2c9"
  test_refs: []

notes: >
  Display layout prototyped interactively and approved by stakeholder
  prior to governance document creation (2026-05-15).

version_history:
  - version: "1.0"
    date: "2026-05-15"
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

## Version History

| Version | Date       | Changes          |
|---------|------------|------------------|
| 1.0     | 2026-05-15 | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
