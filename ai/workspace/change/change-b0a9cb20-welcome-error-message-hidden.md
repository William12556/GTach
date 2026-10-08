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
  title: "Draw the WELCOME error message centred at y=235, between the description and the Start Setup button"
  date: "2026-10-08"
  author: "William Watson"
  status: "implemented"
  priority: "medium"
  iteration: 1
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
    - "Message text, font and colour."
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
  verification_date: ""
  verified_by: ""
  test_results: "Geometry check: band 140..340 x 225..245 clear of all three button rectangles; farthest corner 101 px from centre. Full pytest run pending (owner)."
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

---

Copyright (c) 2026 William Watson. MIT License.
