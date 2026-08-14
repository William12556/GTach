Created: 2026 August 14

# Issue: Acknowledgement Screen Text Clips Circular Viewport

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
issue_info:
  id: "issue-bdac4f18"
  title: "ACKNOWLEDGEMENT screen body and instruction text clip the circular viewport edge"
  date: "2026-08-14"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-bdac4f18"
    change_iteration: 1

source:
  origin: "user_report"
  description: >
    Once change-e22142da makes DisplayMode.ACKNOWLEDGEMENT reachable,
    the screen's body text ("OBD tachometer — experimental software")
    and instruction text ("Tap to acknowledge and continue") clip the
    circular viewport edge. Both are rendered as single un-wrapped
    lines via _get_cached_font(), which resolves through FontManager to
    Michroma-Regular.ttf — a wide geometric display face — at 24px and
    20px respectively. Reporter requested the body text be replaced
    with a short MIT-style "AS IS" warranty disclaimer and a standalone
    DISCLAIMER.md be added to the repository.

affected_scope:
  components:
    - name: "DisplayManager._draw_acknowledgement_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._get_cached_font"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayRenderingEngine.render_text"
      file_path: "src/gtach/display/rendering/engine.py"
  version: "0.4.1"

reproduction:
  prerequisites: "change-e22142da implemented, so ACKNOWLEDGEMENT is reachable."
  steps:
    - "Force an unacknowledged state (delete ack_state.yaml, or change engine_profile)."
    - "Boot GTach and observe the ACKNOWLEDGEMENT screen after splash."
  frequency: "always"
  reproducibility_conditions: "Any time the screen is shown, on any configuration."

behavior:
  expected: >
    All acknowledgement screen text fits within the 480x480 circular
    viewport (r=238) with visible margin.
  actual: >
    render_text() (rendering/engine.py) draws a single line per call —
    no word-wrap exists anywhere in the codebase. The body text at 24px
    Michroma and the instruction at 20px Michroma each exceed the safe
    chord width at their y-position and clip the bezel.
  impact: >
    Cosmetic on a safety-relevant screen — the disclaimer's legibility
    is degraded on every occurrence of the screen, which is every boot
    or setup completion until acknowledged.
  workaround: "None."

analysis:
  root_cause: >
    Two compounding causes: (1) no word-wrap capability exists in
    DisplayRenderingEngine.render_text() or anywhere else in
    src/gtach/display/; every on-screen string is one render_text()
    call. (2) FontManager.get_font(size) in typography.py resolves
    Michroma-Regular.ttf for every requested size, title through
    label — appropriate for the 72px brand title, too wide for a
    multi-word sentence at 20-24px on a 480px circular panel.
  technical_notes: >
    Confirmed on-device (gtach.local, /opt/gtach/venv, pygame 2.6.1 /
    SDL 2.28.4 / Python 3.9.2) that a non-Michroma (SDL default) font
    at 18px/20px, hard-wrapped to the verified line breaks in
    change-bdac4f18, clears the circular viewport at every line with
    52-69px margin on each side. See change-bdac4f18 §technical_details
    for the exact measurements.
  related_issues:
    - issue_ref: "issue-e22142da"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  approach: "Per change-bdac4f18."

verification:
  test_results: ""
  closure_notes: ""

traceability:
  related_issues:
    - issue_ref: "issue-e22142da"

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial issue creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.3"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
