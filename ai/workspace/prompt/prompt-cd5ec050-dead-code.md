Created: 2026 October 07

# Prompt: Remove Dead Code and the Backup Modules

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-cd5ec050"
  task_type: "refactor"
  source_ref: "change-cd5ec050"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-cd5ec050"
    change_iteration: 1

context:
  purpose: "Remove the backup modules and unreachable code without changing reachable behaviour."
  integration: "src/gtach/, tests/, CLAUDE.md."
  knowledge_references:
    - "ai/workspace/issues/issue-cd5ec050-dead-code.md"
    - "ai/workspace/change/change-cd5ec050-dead-code.md"
    - "ai/workspace/audit/audit-36b6ea95-full-codebase.md (A15, B06-B08, C11, C12, C17, D07-D09, E03, E07, F03, F06, G06)"
  constraints:
    - "CRITICAL: before removing any item, grep src/, tests/ and bin/ for references. Remove only items with no reachable reference; keep and report anything still referenced."
    - "CRITICAL: no behaviour change in reachable code. Edits to reachable code are limited to deleting calls to removed dead code and deleting unused imports/variables."
    - "Keep ThreadManager.worker_pool (used by the update check) and the rpm_warning/rpm_danger configuration keys."
    - "Do not reformat code (formatting is the next task)."
    - "Use git rm for deleted files."
    - "Python 3.9+ compatible. PEP 8."

specification:
  description: "Apply removal groups R1 to R14 of change-cd5ec050, running pytest after each group."
  requirements:
    functional:
      - "All listed dead code removed or reported as still referenced."
      - "Reachable behaviour unchanged."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Professional docstrings"
  performance: []

design:
  architecture: "Deletion only."
  components:
    - name: "R1 to R14"
      type: "module"
      purpose: "As in change-cd5ec050."
      logic:
        - "Order: R1, R11, R12, R2, R3, R4, R5, R6, R7, R8, R9, R10, R13, R14."
        - "After each group: pytest -q; on failure fix the reference or restore the item."
        - "Record in the report, per group: items removed, items kept with the referencing site, tests deleted or adjusted."

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
    - scenario: "As listed in change-cd5ec050 testing_requirements.test_cases (including the 8 s simulation smoke run)."
      expected: "As listed there."
  edge_cases: []
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Deletions and minimal edits only."
  files:
    - path: "src/gtach/"
      content: "R1 to R13"
    - path: "tests/"
      content: "R11, R14 and reference fixes"
    - path: "CLAUDE.md"
      content: "R1 (§2 backup rule removed; Version History row)"

success_criteria:
  - "src/gtach/display/manager_backup.py, setup_original_backup.py, src/gtach/comm/bluetooth.py and src/gtach/display/navigation_gestures.py no longer exist."
  - "grep -rn 'manager_backup\\|setup_original_backup' src tests CLAUDE.md returns nothing."
  - "grep -rn 'RESTARTING\\|HARD_RECOVERY\\|hard_recovery\\|restart_future\\|_active_futures\\|target_func' src returns nothing."
  - "flake8 --select F401,F841,F811,F402,F541 src/gtach reports nothing."
  - "python -c 'import gtach.app, gtach.main' succeeds; the 8 s simtcp smoke run shows no import or attribute error."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants: []

notes: "Human verification: deploy and use normally; no on-device step specific to this change."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-cd5ec050 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
