Created: 2026 October 07

# Change: One Line Length and a Single Formatting Pass

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-e4ee50fd"
  title: "Configure flake8 for 88 columns and black compatibility, update CLAUDE.md §7, and apply black and isort once to src/gtach, tests and bin/*.py"
  date: "2026-10-07"
  author: "William Watson"
  status: "implemented"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e4ee50fd"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-e4ee50fd"
  description: "Resolves issue-e4ee50fd (audit-36b6ea95 G05)."

scope:
  summary: "Configuration plus one mechanical formatting commit."
  affected_components:
    - name: "flake8 configuration"
      file_path: ".flake8"
      change_type: "add"
    - name: "CLAUDE.md §7"
      file_path: "CLAUDE.md"
      change_type: "modify"
    - name: "Python sources"
      file_path: "src/gtach/, tests/, bin/*.py"
      change_type: "refactor"
  affected_designs: []
  out_of_scope:
    - "Fixing non-formatting flake8 findings (other than what black/isort resolve)."
    - "mypy (later phase)."
    - "bin/vendor/."

rational:
  problem_statement: "See issue-e4ee50fd."
  proposed_solution: >
    EDIT A — add .flake8: [flake8] max-line-length = 88;
    extend-ignore = E203, W503; exclude = .git, __pycache__, build, dist,
    venv, .venv, bin/vendor.

    EDIT B — CLAUDE.md §7: "Line length: 88 for black, isort and flake8
    (.flake8)"; remove the note about the divergence. Version History row.

    EDIT C — run `isort src tests bin/*.py` then `black src tests
    bin/*.py`. No manual edits to Python files in this change, except
    that if flake8 then still reports E501 for a line black cannot split
    (long strings or comments), wrap that line by hand without changing
    its meaning.
  alternatives_considered:
    - option: "79 columns."
      reason_rejected: "Decided against on 2026-10-07."
  benefits:
    - "Consistent formatting; lint output shows real findings."
  risks:
    - risk: "A large diff obscures history."
      mitigation: "One isolated commit after all functional changes; its hash can be added to a blame-ignore list by the owner."

technical_details:
  current_behavior: "Inconsistent formatting."
  proposed_behavior: "black/isort clean at 88 columns."
  implementation_approach: "Tool run."
  code_changes:
    - component: "All Python sources"
      file: "src/gtach/, tests/, bin/*.py"
      change_summary: "Formatting only."
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-cd5ec050"
      relationship: "blocked_by. Runs last in Phase 5."

testing_requirements:
  test_approach: "Tool checks and the full suite."
  test_cases:
    - scenario: "black --check src tests bin/*.py; isort --check-only src tests bin/*.py."
      expected_result: "Pass."
    - scenario: "flake8 src tests --select E1,E2,E3,E5,W2,W3."
      expected_result: "No findings."
    - scenario: "pytest tests/."
      expected_result: "Same pass count as before the change."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes with an unchanged count."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to C."
      owner: "tactical"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-cd5ec050"
      relationship: "blocked_by"
  related_issues:
    - issue_ref: "issue-e4ee50fd"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-e4ee50fd iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in d44dca9b0d42de3358427f7851abae2336762557."

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
| 1.0 | 2026-10-07 | Initial change document. 88 columns; single formatting pass. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in d44dca9b0d42de3358427f7851abae2336762557. |

---

Copyright (c) 2026 William Watson. MIT License.
