Created: 2026 August 14

# T03 Issue — OPTIONS Title Overlaps Status Indicator

---

## 1.0 Table of Contents

[2.0 Document](<#2.0 document>)
[Version History](<#version history>)

---

## 2.0 Document

```yaml
# T03 Issue - YAML Format

issue_info:
  id: "issue-61c7ba7f"
  title: "OPTIONS screen title text overlays the connection status indicator"
  date: "2026-08-14"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-61c7ba7f"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Operator reported the "Options" title text is rendered on top of the
    connection status indicator dot on the OPTIONS screen.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: ""

reproduction:
  prerequisites: "Application running, RADIAL or DISCONNECTED screen visible"
  steps:
    - "Swipe down to enter the OPTIONS screen"
    - "Observe the 'Options' title near the top of the circular viewport"
  frequency: "always"
  reproducibility_conditions: "OPTIONS screen, any options page"
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: "Title text and status dot are visually distinct and non-overlapping."
  actual: >
    The title is centred at (240, 55) with a 36 px font. The status dot,
    drawn unconditionally by _draw_status_indicator for every non-RADIAL
    mode including OPTIONS, is centred at (240, 60), radius 5. The two
    positions are 5 px apart, so the dot renders inside the title glyphs.
  impact: "Cosmetic only — no loss of function or touch-target integrity."
  workaround: "None required; both elements remain individually legible on close inspection."

environment:
  python_version: "3.11"
  os: "Debian GNU/Linux 11 (Bullseye)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    _draw_options_menu positions the "Options" title at a fixed y=55, a
    value chosen without accounting for _draw_status_indicator's fixed
    dot position at y=60, which is drawn on every OPTIONS frame via
    _render_normal_modes's unconditional trailing call.
  technical_notes: >
    The button column (top=140), page indicator (y=350), and "Swipe up
    to return" hint (y=400) are the only other OPTIONS-screen elements
    with fixed y-coordinates and are unaffected by the overlap itself,
    but must move in step with the title to preserve existing spacing.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Shift the title, button column, page indicator, and hint text down
    by a uniform 45 px (title 55->100, button top 140->185, page
    indicator 350->395, hint 400->445), keeping all elements within the
    238 px circular viewport.
  change_ref: "change-61c7ba7f"
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
    New fixed-position OPTIONS-screen elements should be checked against
    _draw_status_indicator's (240, 60) dot, which is drawn unconditionally
    for every non-RADIAL mode.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "On-target: enter OPTIONS, confirm title does not overlap status dot"
    - "On-target: confirm both options-menu buttons remain tappable"
    - "On-target: confirm page indicator and hint text are legible and unclipped"
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-61c7ba7f"
  test_refs: []

notes: ""

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial issue creation"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#1.0 table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial issue creation |

---

Copyright (c) 2026 William Watson. MIT License.
