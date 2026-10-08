Created: 2026 October 08

# Change: Place the WELCOME Error Message Inside the Visible Area

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-b0a9cb20"
  title: "Draw the WELCOME error message centred at y=235 (iteration 1) in a dark red error_text colour with 6.0:1 contrast (iteration 2)"
  date: "2026-10-08"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 2
  coupled_docs:
    issue_ref: "issue-b0a9cb20"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b0a9cb20"
  description: "Resolves issue-b0a9cb20."

scope:
  summary: "One constant and one coordinate in setup.py; one test file."
  affected_components:
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_welcome_error_message.py (new)"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Message text and font."
    - "Other uses of colors['warning']."
    - "Other setup screens' error display."
    - "DEVICE_LIST signal-bar size (separate task.md item)."

rational:
  problem_statement: "See issue-b0a9cb20."
  proposed_solution: >
    EDIT A — setup.py: class constant _WELCOME_MESSAGE_Y = 235 with a
    comment giving the free band (description ends y=208; Start Setup
    begins y=270 two-button, y=330 one-button; safe radius 200). In
    _render_welcome_screen, centre the error message at (240,
    self._WELCOME_MESSAGE_Y) instead of (240, 440).

    EDIT B — tests/test_welcome_error_message.py: with the constant, a
    20 px text band centred at y=235 lies within 200 px of the centre
    (240, 240) and does not intersect either button rectangle in either
    layout; source assertion that 440 is no longer used for the message.

    ITERATION 2 (approved 2026-10-08; iteration 1 deployed in 0.4.8 left
    the text hard to see). EDIT C — setup.py: new palette entry
    colors['error_text'] = (139, 0, 0), contrast 6.0:1 on the background;
    the WELCOME message uses it instead of colors['warning']. The orange
    accent is unchanged elsewhere (Cancel and Retry buttons carry white
    text). EDIT D — test: the message colour has at least 4.5:1 contrast
    against the background, read from the palette literal.
  alternatives_considered:
    - option: "Shrink or move the buttons."
      reason_rejected: "Larger change; touch targets were sized deliberately."
  benefits:
    - "The operator sees why Continue returned to WELCOME."
  risks:
    - risk: "Text crowds the description."
      mitigation: "17 px clearance above (208 to 225) and 25 px below (245 to 270)."

technical_details:
  current_behavior: "Message at y=440, not visible."
  proposed_behavior: "Message at y=235, visible."
  implementation_approach: "Edits A and B."
  code_changes:
    - component: "SetupDisplayManager"
      file: "src/gtach/display/setup.py"
      change_summary: "Message centre y 440 -> 235"
      functions_affected: ["_render_welcome_screen"]
      classes_affected: ["SetupDisplayManager"]
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Geometry assertions."
  test_cases:
    - scenario: "Message band vs safe radius and button rectangles, both layouts."
      expected_result: "Inside the radius; no intersection."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Edits A and B."
      owner: "planner (this session)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Deploy with ./bin/deploy.sh."

verification:
  implemented_date: "2026-10-08"
  implemented_by: "Claude (planner session, approved by William Watson)"
  verification_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Iteration 1: full suite 475 passed, 2 xfailed; on device (0.4.8) text present but hard to see. Iteration 2: contrast (139,0,0) on (216,200,146) = 6.0:1; full suite passed before deploy; on device (0.4.9) message clearly visible."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-674bec49"
      relationship: "follow-up"
  related_issues:
    - issue_ref: "issue-b0a9cb20"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-b0a9cb20 iteration 1."
  - version: "1.1"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Approved; implemented."
  - version: "2.0"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Iteration 2: dark red error_text colour (6.0:1) after the 0.4.8 re-test showed low contrast."

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
| 1.0 | 2026-10-08 | Initial change document. |
| 1.1 | 2026-10-08 | Approved and implemented. |
| 2.0 | 2026-10-08 | Iteration 2: dark red message colour. |
| 2.1 | 2026-10-08 | Verified on device (0.4.9); closed. |

---

Copyright (c) 2026 William Watson. MIT License.
