Created: 2026 October 07

# Prompt: One Line Length and a Single Formatting Pass

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-e4ee50fd"
  task_type: "refactor"
  source_ref: "change-e4ee50fd"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4ee50fd"
    change_iteration: 1

context:
  purpose: "Align black, isort and flake8 at 88 columns and apply the formatters once."
  integration: ".flake8 (new), CLAUDE.md, all Python under src/gtach, tests and bin/*.py."
  knowledge_references:
    - "ai/workspace/issues/issue-e4ee50fd-formatting.md"
    - "ai/workspace/change/change-e4ee50fd-formatting.md"
  constraints:
    - "CRITICAL: this commit contains formatting only. No semantic edit to any Python file, except hand-wrapping lines black cannot split, without changing meaning."
    - "Run isort before black; both use the existing pyproject settings (88, profile black)."
    - "Do not format bin/vendor/."
    - "Do not touch ai/ or documentation other than CLAUDE.md §7."

specification:
  description: "Apply EDITS A to C of change-e4ee50fd."
  requirements:
    functional:
      - "black --check and isort --check-only pass on src, tests and bin/*.py."
      - "flake8 reports no line-length or whitespace findings."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8 at 88 columns"
  performance: []

design:
  architecture: "Not applicable."
  components:
    - name: "EDITS A to C"
      type: "module"
      purpose: "As in change-e4ee50fd."
      logic:
        - "Record pytest pass count before formatting; it must be identical after."
        - "Report flake8 counts by code before and after (informational)."

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
    - scenario: "As listed in change-e4ee50fd testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases: []
  validation:
    - "pytest tests/ passes with an unchanged count."

deliverable:
  format_requirements:
    - "One commit."
  files:
    - path: ".flake8"
      content: "EDIT A"
    - path: "CLAUDE.md"
      content: "EDIT B"
    - path: "src/gtach/, tests/, bin/*.py"
      content: "EDIT C"

success_criteria:
  - "black --check src tests bin/*.py passes."
  - "isort --check-only src tests bin/*.py passes."
  - "flake8 --select E1,E2,E3,E5,W2,W3 src tests reports nothing."
  - "pytest pass count identical before and after."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants: []

notes: "No on-device verification required."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-e4ee50fd iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-07 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
