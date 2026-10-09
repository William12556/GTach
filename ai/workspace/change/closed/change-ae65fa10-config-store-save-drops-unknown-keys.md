Created: 2026 October 09

# Change: ConfigStore Reads Unknown Keys at Save Time

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-ae65fa10"
  title: "ConfigStore.save reads the current file's unknown keys before writing"
  date: "2026-10-09"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-ae65fa10"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-ae65fa10"
  description: "Resolves issue-ae65fa10."

scope:
  summary: "save() takes unknown keys from the file as it is at save time, falling back to the keys retained by load() when the file is missing or unreadable."
  affected_components:
    - name: "ConfigStore"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
    - name: "ConfigStore tests"
      file_path: "tests/test_config_store.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "load() validation rules and CONFIG_KEYS."
    - "Concurrent saves from two ConfigStore instances (no current caller)."
    - "Overwriting a file that is not a mapping (existing behaviour)."

rational:
  problem_statement: >
    See issue-ae65fa10. save() merges known fields over self._unknown,
    which only load() fills (config.py:265, 325, 342). A store that
    saves without loading drops every unknown key from config.yaml.
  proposed_solution: >
    Extract a module-level helper _unknown_keys(data: Dict[str, Any]) ->
    Dict[str, Any] returning the keys not in CONFIG_KEYS; use it in
    load(). In save(), before taking the lock: if self.path exists, call
    self._read(); if the result is a dict, take its unknown keys; on
    OSError or yaml.YAMLError log a WARNING and use none from the file.
    Then under the lock: if keys were read from the file, store them in
    self._unknown; snapshot self._unknown. Merge the known fields over
    the snapshot and write as now. Update the class and save()
    docstrings to say unknown keys are read at save time.
  alternatives_considered:
    - option: "Call load() from save() when the store has never loaded."
      reason_rejected: "Needs a loaded flag and still loses keys added to the file after load(); reading at save time covers both."
  benefits:
    - "No caller can lose unknown keys by saving first."
  risks:
    - risk: "One extra file read per save."
      mitigation: "Saves are operator-initiated and rare; the file is small."
    - risk: "File I/O near the lock."
      mitigation: "The read happens before the lock is taken (CLAUDE.md §4 rule 8)."

technical_details:
  current_behavior: "Unknown keys come only from the last load()."
  proposed_behavior: "Unknown keys come from the file at save time; the retained set is used when the file is missing or unreadable."
  implementation_approach: "Helper extraction plus a read at the start of save()."
  code_changes:
    - component: "ConfigStore"
      file: "src/gtach/utils/config.py"
      change_summary: "_unknown_keys helper; save() reads current unknown keys."
      functions_affected:
        - "ConfigStore.load"
        - "ConfigStore.save"
        - "_unknown_keys (new)"
      classes_affected:
        - "ConfigStore"
  data_changes:
    - entity: "config.yaml"
      change_type: "validation"
      details: "Unknown keys preserved on every save."
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Regression tests in tests/test_config_store.py."
  test_cases:
    - scenario: "File contains 'foo: 1' and known keys; new ConfigStore; save(AppConfig()) without load()."
      expected_result: "File still contains foo: 1 and the known keys."
    - scenario: "load(); externally add 'bar: 2' to the file; save()."
      expected_result: "bar: 2 preserved."
    - scenario: "No file; save(AppConfig())."
      expected_result: "File contains exactly the CONFIG_KEYS."
    - scenario: "File contains invalid YAML; save(AppConfig())."
      expected_result: "Returns True, writes the known keys, logs a WARNING, raises nothing."
  regression_scope:
    - "tests/test_config_store.py"
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "Edit config.py; add the four tests."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-10-09"
  implemented_by: "Claude Code (commit 3c6472a)"
  verification_date: "2026-10-09"
  verified_by: "William Watson"
  test_results: "test-ae65fa10 passed (7/7); unknown key retained across two palette saves on gtach.local."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5fbff586"
      relationship: "related. Introduced ConfigStore."
  related_issues:
    - issue_ref: "issue-ae65fa10"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-ae65fa10 iteration 1."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Implemented, verified by test-ae65fa10, closed."

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
| 1.0 | 2026-10-09 | Initial change document resolving issue-ae65fa10 iteration 1. |
| 1.1 | 2026-10-09 | Implemented, verified by test-ae65fa10, closed. |

---

Copyright (c) 2026 William Watson. MIT License.
