Created: 2026 October 07

# Issue: Dead Code and Shipped Backup Modules

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-cd5ec050"
  title: "Backup modules (about 5,700 lines) ship in the wheel; unreachable modules, classes, functions, restart remnants and unused imports remain across src/gtach"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-cd5ec050"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 findings A15, B06, B07 (unused imports),
    B08, C11, C12, C17, D07, D08 (dead functions), D09, E03 (framebuffer
    helpers), E07, F03 (source-text test pinning dead code), F06, G06
    (backup modules). Decision by William Watson on 2026-10-07: delete
    the backup modules from the repository.

affected_scope:
  components:
    - name: "Backup modules"
      file_path: "src/gtach/display/manager_backup.py, src/gtach/display/setup_original_backup.py"
    - name: "Dead code across the package"
      file_path: "src/gtach/"
    - name: "Tests that pin or exercise only dead code"
      file_path: "tests/"
    - name: "CLAUDE.md §2 backup exclusion rule"
      file_path: "CLAUDE.md"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "Source review."
  steps:
    - "See the cited audit findings."
  frequency: "always"
  reproducibility_conditions: "Deterministic."
  test_data: >
    As listed in the audit findings cited above. In addition, after
    change-860fd5f7 the in-process restart remnants (ThreadStatus.RESTARTING,
    ThreadInfo target capture and restart_future, ThreadManager
    _active_futures, RecoveryLevel.HARD_RECOVERY, RecoveryStats
    hard_recovery fields) have no function. flake8 reported 77 F401
    (unused import), 6 F841, 4 F811, 1 F402 and 6 F541 in scope.
  error_output: "None."

behavior:
  expected: "Only reachable code ships."
  actual: "As in test_data."
  impact: "Larger wheel and maintenance surface; misleading code; a latent self-deadlock (C11) and a latent TypeError (D07) in unreachable paths."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Code was superseded without removal."
  technical_notes: >
    ThreadManager.worker_pool is still used by DisplayManager's update
    check and is not dead. Tests that only exercise removed code are
    removed with it; tests that pin source text of removed code
    (tests/test_touch_dispatch.py requiring DisplayMode.RADIAL in
    touch.py) are adjusted.
  related_issues:
    - issue_ref: "issue-4005360c"
      relationship: "related. Correctness fixes in the same modules, applied first."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-cd5ec050."
  change_ref: "change-cd5ec050"
  resolved_date: "2026-10-08"
  resolved_by: "change-cd5ec050"
  fix_description: "The backup modules, comm/bluetooth.py, navigation_gestures.py and the unreachable code listed in change-cd5ec050 are removed, along with the in-process restart remnants and all flake8 F401, F841, F811, F402 and F541 findings in src/gtach, and the test scans are extended to os.system and os.popen (commit f7899669ddad21b97dc81429595233e1d23d75b0)."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "No step specific to this change. Bench use 2026-10-07/08 on 0.4.5-0.4.9 (setup, pairing, link losses, soak) without regression attributable to the removal. In-car use is pending vehicle preparation and is tracked in task.md as a general check, not against this issue."
  closure_notes: "Closed at audit-36b6ea95 close-out after on-device verification."

prevention:
  preventive_measures: "flake8 F401/F841/F811 clean after the formatting change."
  process_improvements: "Remove superseded code in the change that supersedes it."

verification_enhanced:
  verification_steps:
    - "Confirm from the audit. [DONE.]"
    - "After the fix: full test suite; application starts in simulation (`gtach --transport simbt`) on the development host."
  verification_results: "All verification steps complete; see verification.test_results."

traceability:
  design_refs: []
  change_refs:
    - "change-cd5ec050"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 A15, B06, B07, B08, C11, C12, C17, D07, D08, D09, E03, E07, F03, F06, G06."

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
      - "Initial issue document for Phase 5 dead-code removal."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in f7899669ddad21b97dc81429595233e1d23d75b0; awaiting on-device verification."
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
| 1.0 | 2026-10-07 | Initial issue document. Dead code and backup modules. |
| 1.1 | 2026-10-07 | Fix implemented in f7899669ddad21b97dc81429595233e1d23d75b0; awaiting on-device verification. |
| 1.2 | 2026-10-08 | On-device verification complete; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
