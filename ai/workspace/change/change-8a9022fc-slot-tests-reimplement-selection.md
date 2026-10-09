Created: 2026 October 09

# Change: Slot Tests Exercise Production Rendering

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-8a9022fc"
  title: "Drive TestSlotContents through _render_device_list_screen instead of a local copy of the slot rule"
  date: "2026-10-09"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-8a9022fc"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-8a9022fc"
  description: "Resolves issue-8a9022fc (audit-36b6ea95 F04)."

scope:
  summary: "Test-only change. The four slot-contents tests assert which device each slot received from the production render path."
  affected_components:
    - name: "TestSlotContents and the _Render helper"
      file_path: "tests/test_device_list_focus.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/display/setup.py and every other source file."
    - "The other test classes in the module and the two create_slot_surface tests in TestSlotContents."

rational:
  problem_statement: >
    See issue-8a9022fc. TestSlotContents._slots rebuilds the slot rule
    (offsets -1, 0, 1) locally, so the four slot tests pass whatever
    SetupDisplayManager._render_device_list_screen does (slot rule now at
    setup.py ~515-530 at ba661d4).
  proposed_solution: >
    Give _Render an optional renderer argument (default: a real
    DeviceSurfaceRenderer). In TestSlotContents use a recording wrapper
    around a real DeviceSurfaceRenderer whose create_slot_surface records
    the device argument (or None) and the slot label of the layout item
    it receives, then delegates. Render with _Render(count,
    focused_index, renderer=recorder) and assert the recorded slot label
    → device name (or None) for: 1 device focus 0; 2 devices focus 0;
    2 devices focus 1; 5 devices focus 2. Delete the _slots helper.
  alternatives_considered:
    - option: "Refactor the slot rule into a production helper and test that."
      reason_rejected: "Changes src/ for a test defect; the render path is already drivable."
  benefits:
    - "A change to the production slot rule fails these tests."
  risks:
    - risk: "The recorder misreads the slot label from the call."
      mitigation: "Mutation check: altering the production offsets must fail all four tests."

technical_details:
  current_behavior: "Four tests assert a locally built list."
  proposed_behavior: "Four tests assert what _render_device_list_screen passed to create_slot_surface per slot."
  implementation_approach: "Recording wrapper plus an optional _Render argument."
  code_changes:
    - component: "tests"
      file: "tests/test_device_list_focus.py"
      change_summary: "Rewrite four tests; delete _slots; add recorder."
      functions_affected:
        - "TestSlotContents (four tests)"
        - "_Render.__init__"
      classes_affected:
        - "TestSlotContents"
        - "_Render"
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-479b2e51"
      relationship: "related. Introduced the focused-slot layout."

testing_requirements:
  test_approach: "Mutation check against production code."
  test_cases:
    - scenario: "pytest tests/test_device_list_focus.py."
      expected_result: "Passes."
    - scenario: "Temporarily change the production relative offsets in _render_device_list_screen (for example reverse them); run the four tests; restore the source."
      expected_result: "All four fail while altered; pass after restore. The alteration is not committed; the result is recorded in the report."
  regression_scope:
    - "tests/test_device_list_focus.py"
  validation_criteria:
    - "pytest tests/ passes; git diff shows no change under src/."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "Edit the test module; run the mutation check."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-479b2e51"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-8a9022fc"
      relationship: "resolves"

notes: "Line numbers are from ba661d4; locate code by symbol."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-8a9022fc iteration 1."

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
| 1.0 | 2026-10-09 | Initial change document resolving issue-8a9022fc iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
