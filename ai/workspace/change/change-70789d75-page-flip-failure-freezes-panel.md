Created: 2026 October 07

# Change: Write to the Displayed Half After a Pan Failure

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-70789d75"
  title: "Single-buffer writes target the displayed half (buffer_index * fb_size); on pan failure rewrite the current frame there; log pan failure at WARNING"
  date: "2026-10-07"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-70789d75"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-70789d75"
  description: "Resolves issue-70789d75 (audit-36b6ea95 D02)."

scope:
  summary: "Three small edits in engine.py and one test addition."
  affected_components:
    - name: "DisplayRenderingEngine frame-write block"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine._pan_display"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "Engine tests"
      file_path: "tests/display/rendering/test_engine.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Retrying page flipping after a failure."
    - "Vertical-offset compensation, vsync handling and the mmap setup."
    - "cleanup() not resetting fb/fb_dev (audit D11)."

rational:
  problem_statement: "See issue-70789d75."
  proposed_solution: >
    EDIT A — in the page-flip branch's failure path (where page_flip is
    set False), additionally seek to `self.buffer_index * self.fb_size`
    and write the same payload, so the current frame reaches the
    displayed half.

    EDIT B — in the single-buffer branch, replace `self.fb.seek(0)` with
    `self.fb.seek(self.buffer_index * self.fb_size)`. Add a comment
    citing issue-70789d75.

    EDIT C — in _pan_display's except branch, log the one-time failure
    at WARNING instead of INFO, text unchanged.
  alternatives_considered:
    - option: "Pan back to half 0 before disabling page flipping."
      reason_rejected: "A second ioctl that can also fail; writing to the displayed half needs none."
  benefits:
    - "The panel keeps updating after a pan failure."
    - "The degradation is recorded in error.log."
  risks:
    - risk: "fb_size or buffer_index wrong when page flipping was never established."
      mitigation: "buffer_index is initialised to 0 (engine.py:101) and only changes after a successful pan."

technical_details:
  current_behavior: "Single-buffer writes always at offset 0."
  proposed_behavior: "Single-buffer writes at the displayed half's offset."
  implementation_approach: "Three line-level edits."
  code_changes:
    - component: "DisplayRenderingEngine"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: "EDITS A, B and C"
      functions_affected:
        - "_pan_display"
        - "the frame-presentation method containing the page-flip branch (engine.py:798-818)"
      classes_affected:
        - "DisplayRenderingEngine"
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Extend tests/display/rendering/test_engine.py using its existing engine fixture."
  test_cases:
    - scenario: "page_flip True, buffer_index 1, _pan_display patched to return False; present one frame."
      expected_result: "page_flip False; buffer_index 1; the payload was written at offset 1 * fb_size."
    - scenario: "Then present a second frame."
      expected_result: "Written at offset 1 * fb_size, not 0."
    - scenario: "page_flip False from the start, buffer_index 0; present a frame."
      expected_result: "Written at offset 0 (behaviour unchanged)."
  regression_scope:
    - "tests/display/rendering/test_engine.py"
    - "Full tests/ suite."
  validation_criteria:
    - "No `self.fb.seek(0)` remains in the single-buffer branch."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to C and tests."
      owner: "tactical"
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
  related_changes: []
  related_issues:
    - issue_ref: "issue-70789d75"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-70789d75 iteration 1."

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
| 1.0 | 2026-10-07 | Initial change document. Write to the displayed half after a pan failure. |

---

Copyright (c) 2026 William Watson. MIT License.
