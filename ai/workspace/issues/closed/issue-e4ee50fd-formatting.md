Created: 2026 October 07

# Issue: Formatting Tools Disagree and Were Never Applied

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-e4ee50fd"
  title: "black and isort are configured for 88 columns while flake8 defaults to 79 and CLAUDE.md requires 79; neither formatter has been applied"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4ee50fd"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-36b6ea95 finding G05. Decision by William Watson on 2026-10-07: 88 columns for all tools."

affected_scope:
  components:
    - name: "Tool configuration"
      file_path: "pyproject.toml, .flake8 (new), CLAUDE.md §7"
    - name: "Python sources"
      file_path: "src/gtach/, tests/, bin/*.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "pip install -e .[dev]"
  steps:
    - "black --check src tests; isort --check-only src tests; flake8 src tests."
  frequency: "always"
  reproducibility_conditions: "Deterministic."
  test_data: >
    Audit run: black would reformat 72 in-scope files, isort 51; flake8
    1,261 E501 at 79 columns plus 2,088 W293 and other whitespace codes.
    flake8 has no configuration.
  error_output: "None."

behavior:
  expected: "One line length (88) across black, isort, flake8 and CLAUDE.md; sources formatted."
  actual: "As in test_data."
  impact: "Formatting noise hides real lint findings."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Tool configuration diverged and formatting was never enforced."
  technical_notes: "black guarantees an equivalent AST; isort only reorders imports. The change is mechanical and is committed alone, after all functional changes."
  related_issues: []

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-e4ee50fd."
  change_ref: "change-e4ee50fd"
  resolved_date: "2026-10-08"
  resolved_by: "change-e4ee50fd"
  fix_description: "black and isort are applied at 88 columns to src, tests and bin/*.py, .flake8 sets the same limit, and CLAUDE.md §7 records it, with no change to any file's AST apart from import order (commit d44dca9b0d42de3358427f7851abae2336762557)."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "No on-device step required (formatting only); test suite unchanged in pass count at the time; deployments 0.4.5-0.4.9 ran normally."
  closure_notes: "Closed at audit-36b6ea95 close-out after on-device verification."

prevention:
  preventive_measures: "black --check and isort --check-only are part of the success criteria of future changes."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "After the fix: black --check, isort --check-only pass; flake8 reports no E501/W2xx/E1xx-E3xx findings; pytest passes."
  verification_results: "All verification steps complete; see verification.test_results."

traceability:
  design_refs: []
  change_refs:
    - "change-e4ee50fd"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 G05."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial issue document for Phase 5 formatting."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in d44dca9b0d42de3358427f7851abae2336762557; awaiting on-device verification."
  - version: "1.2"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "On-device verification complete; closed at audit-36b6ea95 close-out."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial issue document. Formatting at 88 columns. |
| 1.1 | 2026-10-07 | Fix implemented in d44dca9b0d42de3358427f7851abae2336762557; awaiting on-device verification. |
| 1.2 | 2026-10-08 | On-device verification complete; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
