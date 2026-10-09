Created: 2026 October 07

# Issue: mypy Strict Errors

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-ac11505d
  title: mypy src/ reports 333 errors in 38 files; CLAUDE.md §4 rule 2 (mypy clean)
    is not met
  date: '2026-10-07'
  reporter: Claude Code
  status: open
  severity: medium
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-ac11505d
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: Recorded by audit-36b6ea95 Section 2 (465 errors in scope at audit
    time) and deferred to a later phase.
affected_scope:
  components:
  - name: gtach package
    file_path: src/gtach/
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: ''
  steps:
  - mypy src/
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: 'Found 333 errors in 38 files (checked 58 source files) at 34c1ffd.
    Most frequent: no-untyped-def 109, assignment 62, unreachable 45, var-annotated
    26, union-attr 16, no-any-return 16, index 12, arg-type 10.'
behavior:
  expected: mypy src/ reports no errors under the strict settings in pyproject.toml.
  actual: 333 errors in 38 files.
  impact: Type defects (for example union-attr and arg-type on Optional values)
    are not caught before runtime.
  workaround: ''
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: Type hints were never completed under the strict configuration.
  technical_notes: Phases 3 and 5 removed about 130 errors with dead code. Work
    file by file; reachable defects found by mypy may need their own issues.
  related_issues:
  - issue_ref: ''
    relationship: ''
resolution:
  assigned_to: ''
  target_date: ''
  approach: Address by module in small changes, starting with union-attr, arg-type
    and index errors, which are most likely to be real defects.
  change_ref: change-ac11505d
  resolved_date: ''
  resolved_by: ''
  fix_description: ''
verification:
  verified_date: ''
  verified_by: ''
  test_results: ''
  closure_notes: ''
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - mypy src/ reports 0 errors.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-ac11505d
  test_refs:
  - ''
notes: audit-36b6ea95 Section 2 / CLAUDE.md §4 rule 2.
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
  - Coupled to change-ac11505d (P03.7); scope chosen - full target in one behaviour-preserving change, suspected defects suppressed with TODO and reported.
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
| 1.1 | 2026-10-09 | Coupled to change-ac11505d; full behaviour-preserving scope chosen. |

---

Copyright (c) 2026 William Watson. MIT License.
