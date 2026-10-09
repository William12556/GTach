Created: 2026 October 09

# Change: mypy Strict Clean

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-ac11505d"
  title: "Bring mypy src/ to zero errors under the strict pyproject.toml settings without changing runtime behaviour"
  date: "2026-10-09"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-ac11505d"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-ac11505d"
  description: "Resolves issue-ac11505d (CLAUDE.md §4 rule 2). Scope confirmed 2026-10-09: full target, implemented last, behaviour-preserving."

scope:
  summary: "Type annotations and type-only constructs across src/gtach so mypy src/ reports 0 errors; suspected real defects are suppressed per line, marked TODO and reported, not fixed."
  affected_components:
    - name: "gtach package"
      file_path: "src/gtach/"
      change_type: "modify"
    - name: "Development extras"
      file_path: "pyproject.toml"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any runtime behaviour change, including new None checks, changed return values or changed exception paths."
    - "Relaxing any [tool.mypy] strict setting, ignore_errors, or module-wide ignores for gtach modules."
    - "Type-checking tests/."
    - "Fixing defects mypy reveals (each becomes a TODO and a report entry for a new issue)."

rational:
  problem_statement: "See issue-ac11505d. mypy src/ reported 333 errors in 38 files at 34c1ffd; CLAUDE.md §4 rule 2 requires mypy clean."
  proposed_solution: >
    Record the baseline count (mypy src/ after the other eight changes).
    Work subpackage by subpackage: utils, core, comm, display. Permitted
    edits: parameter and return annotations; variable annotations;
    typing.cast; TYPE_CHECKING-only imports; Optional/Union corrections
    to annotations; narrowing that cannot alter the runtime path (for
    example isinstance on a value whose type is already guaranteed by
    the call site); deleting code that mypy reports unreachable only
    when it is also unreachable at runtime (otherwise correct the
    annotation). Where a fix would require a runtime change, add
    '# type: ignore[<code>]  # TODO: issue-ac11505d candidate defect -
    <reason>' on that line and list it in the report. Third-party
    modules without inline types: add the matching types-* stub package
    (for example types-PyYAML, types-psutil, types-pyserial) to the
    [dev] extra; if no stub package exists, add the module to the
    existing [[tool.mypy.overrides]] ignore_missing_imports list. Use
    Any only for genuinely dynamic values (parsed YAML, pygame event
    payloads).
  alternatives_considered:
    - option: "Defect-prone codes only (union-attr, arg-type, index)."
      reason_rejected: "Decided against on 2026-10-09."
    - option: "Fix defects as they are found."
      reason_rejected: "Mixes behaviour changes into a typing change; each defect needs its own issue and verification."
  benefits:
    - "CLAUDE.md §4 rule 2 met; type defects caught before runtime."
    - "A list of candidate defects for triage."
  risks:
    - risk: "A type-only edit changes behaviour (for example an isinstance that is not guaranteed)."
      mitigation: "Permitted-edit list; full test suite after each subpackage; import smoke check; 8 s simtcp smoke run."
    - risk: "The session cannot finish all modules."
      mitigation: "Commit per completed subpackage with the remaining count in the report; the prompt stays open."
    - risk: "Many suppressions hide real defects."
      mitigation: "Every suppression carries a TODO with issue-ac11505d and appears in the report table."

technical_details:
  current_behavior: "mypy src/ reports errors (333 at 34c1ffd)."
  proposed_behavior: "mypy src/ reports 0 errors."
  implementation_approach: "Subpackage order utils, core, comm, display; pytest after each."
  code_changes:
    - component: "gtach"
      file: "src/gtach/"
      change_summary: "Annotations and type-only constructs."
      functions_affected: []
      classes_affected: []
    - component: "pyproject"
      file: "pyproject.toml"
      change_summary: "types-* stubs in [dev]; ignore_missing_imports only where no stubs exist."
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "Public function signatures"
      change_type: "signature"
      details: "Annotations only; no parameter, default or return-value change."
      backward_compatible: "yes"

dependencies:
  internal: []
  external:
    - library: "types-PyYAML, types-psutil, types-pyserial (as needed)"
      version_change: "added to [dev] only"
      impact: "Development environment only; no runtime dependency."
  required_changes:
    - change_ref: "change-273ca048"
      relationship: "blocked_by. Implement after all other changes of this batch."

testing_requirements:
  test_approach: "Static check plus the full suite and smoke checks."
  test_cases:
    - scenario: "mypy src/."
      expected_result: "Success: no issues found."
    - scenario: "pytest tests/."
      expected_result: "Passes, same counts as before this change."
    - scenario: "python -c 'import gtach.app, gtach.main'; SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 python -m gtach --transport simtcp."
      expected_result: "Import succeeds; the run reaches the timeout without errors."
    - scenario: "flake8 on changed files."
      expected_result: "No new findings."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "mypy src/ 0 errors; pytest tests/ passes."

implementation:
  effort_estimate: "1-2 days"
  implementation_steps:
    - step: "Baseline; utils; core; comm; display; final mypy and pytest."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commits."
  deployment_notes: "Human verification: normal use on the Pi; no step specific to this change."

verification:
  implemented_date: "2026-10-09"
  implemented_by: "Claude Code (commits e5ceb62, dae7d83, 5ebd823, 954fb6d, 1a2ebee)"
  verification_date: "2026-10-09"
  verified_by: "William Watson"
  test_results: "test-ac11505d passed (7/7); mypy --platform linux src/ clean; all modules import on Python 3.9.2 on gtach.local."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-cd5ec050"
      relationship: "related. Removed about 130 errors with dead code."
  related_issues:
    - issue_ref: "issue-ac11505d"
      relationship: "resolves"

notes: "The candidate-defect list in the report is the input for follow-up issues raised by the planner."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-ac11505d iteration 1."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Implemented, verified by test-ac11505d, closed."

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
| 1.0 | 2026-10-09 | Initial change document resolving issue-ac11505d iteration 1. |
| 1.1 | 2026-10-09 | Implemented, verified by test-ac11505d, closed. |

---

Copyright (c) 2026 William Watson. MIT License.
