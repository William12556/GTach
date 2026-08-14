Created: 2026 August 14

# T02 Change — Reposition OPTIONS Screen Title and Controls

---

## 1.0 Table of Contents

[2.0 Document](<#2.0 document>)
[Version History](<#version history>)

---

## 2.0 Document

```yaml
# T02 Change - YAML Format

change_info:
  id: "change-61c7ba7f"
  title: "Shift OPTIONS screen title, buttons, and indicators down to clear the status dot"
  date: "2026-08-14"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-61c7ba7f"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-61c7ba7f"
  description: "OPTIONS title text overlays the connection status indicator dot."

scope:
  summary: >
    Move the OPTIONS screen's title, button column, page indicator, and
    hint text down by a uniform 45 px so the title no longer overlaps
    the status dot at (240, 60).
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Status indicator position or size"
    - "Any screen other than the OPTIONS menu (update view, confirm view, DISCONNECTED)"

rational:
  problem_statement: >
    The "Options" title at (240, 55) overlaps the status dot at (240, 60),
    making both harder to read.
  proposed_solution: >
    Apply a uniform 45 px downward shift to every fixed-position element
    on the options menu: title (55->100), button column top (140->185),
    page indicator (350->395), hint text (400->445). A uniform shift
    preserves the existing relative spacing between elements rather than
    requiring each gap to be re-derived.
  alternatives_considered:
    - option: "Move only the title, leave buttons/indicator/hint in place"
      reason_rejected: >
        Leaves an uneven, visually unbalanced gap between title and
        button column and was not what was requested.
    - option: "Move the status dot instead of the title"
      reason_rejected: >
        Out of scope — the status dot's position is shared with the
        DISCONNECTED screen and other modes; issue is specific to OPTIONS.
  benefits:
    - "Title and status dot become visually distinct"
    - "Existing element spacing (button separation, indicator-to-hint gap) is preserved"
  risks:
    - risk: "Shifted elements could fall outside the 238 px circular viewport"
      mitigation: >
        Verified by manual geometry check: button column outer corners
        at ~183 px from centre (limit 238 px); hint text at ~205 px from
        centre. Both within bounds with margin.

technical_details:
  current_behavior: >
    _draw_options_menu renders the title at (240, 55); the page indicator
    at y=350; the hint text at (240, 400). _register_options_menu_regions
    passes top=140 to _button_column for the button geometry.
  proposed_behavior: >
    Title at (240, 100); button column top=185; page indicator at y=395;
    hint text at (240, 445). No other geometry, colour, or behaviour changes.
  implementation_approach: >
    Update the four fixed y-coordinate literals in place. No new
    functions, parameters, or state.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Change title y from 55 to 100 in _draw_options_menu; change
        button column top from 140 to 185 in _register_options_menu_regions;
        change page indicator y from 350 to 395 in _draw_options_menu;
        change hint text y from 400 to 445 in _draw_options_menu.
      functions_affected:
        - "_draw_options_menu"
        - "_register_options_menu_regions"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Manual on-target verification (no automated display tests exist for this render path)"
  test_cases:
    - scenario: "Enter OPTIONS from RADIAL"
      expected_result: "Title 'Options' is fully clear of the status dot"
    - scenario: "View options page 0 and page 1"
      expected_result: "Both buttons on each page remain within the circular viewport and are tappable"
    - scenario: "View page indicator and hint text"
      expected_result: "Both are legible and unclipped by the viewport edge"
  regression_scope:
    - "OPTIONS menu touch regions (simulation_mode, debug_toggle, clear_settings, check_updates)"
  validation_criteria:
    - "No button corner falls outside the 238 px circular viewport (per _button_column's existing corner check)"

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Update the four y-coordinate literals in src/gtach/display/manager.py"
      owner: "Claude Code"
  rollback_procedure: "Revert the four literals to their prior values (55, 140, 350, 400)"
  deployment_notes: "Standard build/deploy/install cycle; no config or migration changes"

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-61c7ba7f"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial change creation"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#1.0 table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial change creation |

---

Copyright (c) 2026 William Watson. MIT License.
