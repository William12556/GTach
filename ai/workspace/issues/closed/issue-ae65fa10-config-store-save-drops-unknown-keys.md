Created: 2026 October 07

# Issue: ConfigStore Save Without Load Drops Unknown Keys

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-ae65fa10
  title: ConfigStore.save on a store that has not loaded overwrites config.yaml
    without its unknown keys
  date: '2026-10-07'
  reporter: Claude Code
  status: closed
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-ae65fa10
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: Recorded in report-5fbff586 Deviations.
affected_scope:
  components:
  - name: ConfigStore
    file_path: src/gtach/utils/config.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: ''
  steps:
  - 'Write config.yaml with an extra key foo: 1.'
  - Create a new ConfigStore and call save(AppConfig()) without load().
  - Read config.yaml.
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: 'foo: 1 is preserved, as it is after load() then save().'
  actual: foo is removed; save() merges over self._unknown, which is filled only
    by load() (config.py:265, 325, 342).
  impact: 'Latent: DisplayManager always loads before saving, so no current caller
    loses data.'
  workaround: Call load() before save().
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: Unknown keys are cached from the last load() rather than read at save
    time.
  technical_notes: ''
  related_issues:
  - issue_ref: issue-5fbff586
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: In save(), read the current file's unknown keys (or load if never loaded)
    before merging.
  change_ref: change-ae65fa10
  resolved_date: '2026-10-09'
  resolved_by: Claude Code (change-ae65fa10, commit 3c6472a)
  fix_description: ''
verification:
  verified_date: '2026-10-09'
  verified_by: William Watson
  test_results: test-ae65fa10 passed (7/7); an unknown key survived two palette saves on gtach.local.
  closure_notes: Closed after on-device verification of the nine-change batch.
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - A unit test saving on a fresh store preserves an unknown key.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-ae65fa10
  test_refs:
  - ''
notes: Follow-up to change-5fbff586.
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
  - Coupled to change-ae65fa10 (P03.7).
- version: '1.2'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Resolved by change-ae65fa10; verified by test-ae65fa10; closed.
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
| 1.1 | 2026-10-09 | Coupled to change-ae65fa10. |
| 1.2 | 2026-10-09 | Resolved by change-ae65fa10; verified by test-ae65fa10; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
