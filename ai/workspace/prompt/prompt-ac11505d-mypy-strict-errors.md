Created: 2026 October 09

# Prompt: mypy Strict Clean

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-ac11505d"
  task_type: "refactor"
  source_ref: "change-ac11505d"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-ac11505d"
    change_iteration: 1

context:
  purpose: "mypy src/ reports 0 errors under the strict pyproject.toml settings, with no runtime behaviour change."
  integration: "src/gtach/ (all subpackages); pyproject.toml [dev] extra and [[tool.mypy.overrides]]."
  knowledge_references:
    - "ai/workspace/issues/issue-ac11505d-mypy-strict-errors.md"
    - "ai/workspace/change/change-ac11505d-mypy-strict-errors.md"
  constraints:
    - "CRITICAL: no runtime behaviour change. Permitted: annotations; typing.cast; TYPE_CHECKING-only imports; Optional/Union corrections in annotations; narrowing that cannot alter the runtime path; deleting code mypy reports unreachable only when it is also unreachable at runtime."
    - "CRITICAL: where a fix would need a runtime change, add '# type: ignore[<code>]  # TODO: issue-ac11505d candidate defect - <reason>' on that line instead, and list it in the report."
    - "Do not relax any [tool.mypy] setting; no ignore_errors; no module-wide ignores for gtach modules; no bare '# type: ignore' without a code."
    - "Third-party modules without inline types: add the matching types-* package to [project.optional-dependencies].dev; if none exists, add the module to the existing ignore_missing_imports override. No runtime dependency changes."
    - "Any only for genuinely dynamic values (parsed YAML, pygame event payloads)."
    - "Do not type-check or modify tests/ except where a test breaks on an annotation change (record it)."
    - "Run last, after the other eight changes of this batch."

specification:
  description: "Clear mypy src/ subpackage by subpackage: utils, core, comm, display."
  requirements:
    functional:
      - "pytest results unchanged (same pass count as before this change)."
    technical:
      language: "Python"
      version: "3.9+ (annotations must parse on 3.9: no PEP 604 'X | Y' at runtime; use Optional/Union or 'from __future__ import annotations' only where the module already uses it)"
      standards:
        - "Type hints on all public interfaces (CLAUDE.md §4 rule 2)"
  performance: []

design:
  architecture: "Incremental, per subpackage, each step verified."
  components:
    - name: "Baseline"
      type: "module"
      purpose: "pip install -e .[dev]; mypy src/ | tail -1; record count by error code (mypy src/ --no-error-summary | sed -n 's/.*\\[\\(.*\\)\\]$/\\1/p' | sort | uniq -c)."
    - name: "Per subpackage (utils, core, comm, display)"
      type: "module"
      purpose: "Fix; mypy src/gtach/<pkg>; pytest tests/; commit referencing change-ac11505d."
      logic:
        - "Prioritise union-attr, arg-type and index errors; each that reflects a real defect becomes a TODO suppression, not a fix."
        - "Record per subpackage: errors before/after, suppressions added."
    - name: "Final"
      type: "module"
      purpose: "mypy src/ (0 errors); pytest tests/; import smoke check; 8 s simtcp smoke run; flake8 on changed files."

data_schema:
  entities: []

error_handling:
  strategy: "Not applicable."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "mypy src/."
      expected: "Success: no issues found."
    - scenario: "pytest tests/."
      expected: "Same pass count as the pre-change baseline."
    - scenario: "python -c 'import gtach.app, gtach.main'; SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 python -m gtach --transport simtcp."
      expected: "Import succeeds; run reaches the timeout without errors."
  edge_cases: []
  validation:
    - "grep -rn 'type: ignore' src/gtach: every match carries an error code and, if added by this change, the issue-ac11505d TODO."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ after each subpackage and on completion; report counts."
  files:
    - path: "src/gtach/"
      content: "Annotations and type-only constructs"
    - path: "pyproject.toml"
      content: "types-* stubs in [dev]; overrides only where no stubs exist"

success_criteria:
  - "mypy src/ reports 0 errors."
  - "pytest tests/ passes with the baseline pass count."
  - "Report contains: baseline and final counts by code, per-subpackage table, full list of TODO suppressions (file:line, code, reason), stub packages added."
  - "If not completed: completed subpackages committed; remaining count and remaining files in the report; prompt T-Doc left open."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants: []

notes: "The TODO suppression list is the input for follow-up issues raised by the planner. Human verification: normal use on the Pi."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-ac11505d iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
