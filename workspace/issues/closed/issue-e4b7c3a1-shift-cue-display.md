Created: 2026 May 15

# Issue: Shift Cue Display

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
issue_info:
  id: "issue-e4b7c3a1"
  title: "Shift cue display: implement gear shift visual indicators and improve radial mode legibility"
  date: "2026-05-15"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4b7c3a1"
    change_iteration: 1

source:
  origin: "requirement_change"
  description: >
    Primary goal of GTach is to provide the driver with visible gear shift cues.
    Current danger-zone flash does not encode shift direction. Border and tick
    marks/numerals too small for in-vehicle legibility.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "TypographyConstants"
      file_path: "src/gtach/display/typography.py"
  version: "current"

behavior:
  expected: >
    Radial mode displays upshift (green border/flash), safe downshift (blue border),
    and normal (dark border) states. Danger-zone background flash removed.
    Border 12 px shift states, 5 px normal. Ticks 28 px/7 px. Numerals 52 px/58 px inset.
  actual: >
    Single danger-zone red background flash only. No shift cues.
    Border 4 px. Ticks 20 px/5 px. Numerals 40 px/42 px inset.

resolution:
  assigned_to: "Claude Code"
  approach: "Implemented per change-e4b7c3a1."
  change_ref: "change-e4b7c3a1"
  resolved_date: "2026-05-26"
  resolved_by: "Claude Code"
  fix_description: >
    _get_shift_cue() and _draw_shift_border() added to DisplayManager.
    _draw_radial_mode() updated with shift cue logic, enlarged ticks and numerals.
    Danger flash removed from _get_band_colour().

verification:
  verified_date: "2026-05-26"
  verified_by: "William Watson"
  test_results: "_draw_shift_border(), _get_shift_cue() confirmed present in manager.py."
  closure_notes: "All success criteria met. Prompt audit confirmed."

version_history:
  - version: "1.0"
    date: "2026-05-15"
    author: "William Watson"
    changes:
      - "Initial issue creation."
  - version: "1.1"
    date: "2026-05-15"
    author: "William Watson"
    changes:
      - "Removed red unsafe downshift cue."
  - version: "1.2"
    date: "2026-05-26"
    author: "William Watson"
    changes:
      - "Closed — implementation verified."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes                          |
|---------|------------|----------------------------------|
| 1.0     | 2026-05-15 | Initial creation                 |
| 1.1     | 2026-05-15 | Removed red unsafe downshift cue |
| 1.2     | 2026-05-26 | Closed — implementation verified |

---

Copyright (c) 2026 William Watson. MIT License.
