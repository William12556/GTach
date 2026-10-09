Created: 2026 October 07

# Issue: Eager Package Import

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-2b3a1547
  title: Importing the gtach package eagerly imports app, pygame and the transport
    stack
  date: '2026-10-07'
  reporter: Claude Code
  status: closed
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-2b3a1547
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: Remaining part of audit-36b6ea95 B11. The hard-coded __version__
    was removed by change-52653cd6.
affected_scope:
  components:
  - name: gtach package
    file_path: src/gtach/__init__.py
  - name: main
    file_path: src/gtach/main.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: ''
  steps:
  - python -c 'import gtach.utils.home' and observe pygame's banner.
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: pygame 2.6.1 (SDL ...) printed on any gtach import
behavior:
  expected: Importing a submodule (for example gtach.utils.home, or gtach.main for
    --validate-config) loads only what it needs.
  actual: src/gtach/__init__.py:14-15 imports .app and .main, which import pygame
    and the transport stack.
  impact: Slower start of --validate-config and --validate-dependencies; the deferred
    import of app in main.py:374 is defeated.
  workaround: ''
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: Package-level convenience re-exports.
  technical_notes: tests/test_error_log.py works around the re-export of main by
    fetching gtach.main from sys.modules (issue-c1d4b8e6).
  related_issues:
  - issue_ref: issue-52653cd6
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: Make the re-exports lazy (module __getattr__) or drop them; the console
    script already targets gtach.main:main.
  change_ref: change-2b3a1547
  resolved_date: '2026-10-09'
  resolved_by: Claude Code (change-2b3a1547, commit 7a91a42)
  fix_description: ''
verification:
  verified_date: '2026-10-09'
  verified_by: William Watson
  test_results: test-2b3a1547 passed (6/6); gtach --version on gtach.local no longer prints the pygame banner.
  closure_notes: Closed after on-device verification of the nine-change batch.
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - python -c 'import gtach.main' does not import pygame; pytest passes.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-2b3a1547
  test_refs:
  - ''
notes: audit-36b6ea95 B11 (partial).
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
  - Coupled to change-2b3a1547 (P03.7); approach chosen - drop the re-exports.
- version: '1.2'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Resolved by change-2b3a1547; verified by test-2b3a1547; closed.
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
| 1.1 | 2026-10-09 | Coupled to change-2b3a1547; re-exports to be dropped. |
| 1.2 | 2026-10-09 | Resolved by change-2b3a1547; verified by test-2b3a1547; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
