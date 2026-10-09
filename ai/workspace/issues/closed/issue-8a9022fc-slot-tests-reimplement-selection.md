Created: 2026 October 07

# Issue: Slot Tests Re-implement Production Logic

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-8a9022fc
  title: TestSlotContents asserts against its own copy of the slot-selection rule
    instead of production code
  date: '2026-10-07'
  reporter: Claude Code
  status: closed
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-8a9022fc
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: audit-36b6ea95 F04, recorded as open.
affected_scope:
  components:
  - name: TestSlotContents
    file_path: tests/test_device_list_focus.py
  - name: SetupDisplayManager._render_device_list_screen
    file_path: src/gtach/display/setup.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: ''
  steps:
  - Change the slot rule at setup.py:507-512 (for example offsets (-1, 0, 1)).
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: A change to the production slot rule fails the slot-contents tests.
  actual: tests/test_device_list_focus.py:214-235 build slots with a local _slots
    helper; four tests pass whatever setup.py does.
  impact: The production rule at setup.py:507-512 is not covered by these four tests.
  workaround: ''
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: The test helper duplicates the rule rather than rendering through
    _render_device_list_screen.
  technical_notes: ''
  related_issues:
  - issue_ref: ''
    relationship: ''
resolution:
  assigned_to: ''
  target_date: ''
  approach: Drive the four tests through _render_device_list_screen (as the _Render
    helper in the same module does) and assert the devices drawn per slot.
  change_ref: change-8a9022fc
  resolved_date: '2026-10-09'
  resolved_by: Claude Code (change-8a9022fc, commit d4e11e3)
  fix_description: ''
verification:
  verified_date: '2026-10-09'
  verified_by: William Watson
  test_results: test-8a9022fc passed (4/4); mutation check gave 3 failed + 1 passed (reversed), 4 failed (all zero), 4 passed (restored).
  closure_notes: Closed. Test-only change; no on-device verification required.
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - The four tests fail when the production offsets are altered and pass when restored.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-8a9022fc
  test_refs:
  - ''
notes: audit-36b6ea95 F04.
loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ''
  last_review_feedback: ''
version_history:
- version: '1.0'
  date: '2026-10-07'
  author: Claude Code
  changes:
  - Initial issue document, raised at the close of audit-36b6ea95 remediation.
- version: '1.1'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Coupled to change-8a9022fc (P03.7).
- version: '1.2'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Resolved by change-8a9022fc; verified by test-8a9022fc; closed.
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
| 1.0 | 2026-10-07 | Initial issue document. Raised at the close of audit-36b6ea95 remediation. |
| 1.1 | 2026-10-09 | Coupled to change-8a9022fc. |
| 1.2 | 2026-10-09 | Resolved by change-8a9022fc; verified by test-8a9022fc; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
