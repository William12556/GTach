Created: 2026 October 07

# Change: Replace Periodic Stack Dumps With On-Request Dumps

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-fe755cfd"
  title: "enable_stack_dumps registers a SIGUSR1 all-thread dump instead of a 15 s repeat timer; disable_stack_dumps unregisters it"
  date: "2026-10-07"
  author: "William Watson"
  status: "implemented"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-fe755cfd"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-fe755cfd"
  description: "Resolves issue-fe755cfd."

scope:
  summary: "main.py stack-dump arming and teardown; tests adjusted."
  affected_components:
    - name: "Stack dumps"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_stack_dump_toggle.py, tests/test_stacks_log_rotation.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Automatic dump on watchdog stall detection (possible later change)."
    - "stacks.log rotation and run header (unchanged)."
    - "app.py debug toggle (unchanged; it calls the same functions)."

rational:
  problem_statement: "See issue-fe755cfd."
  proposed_solution: >
    EDIT A — enable_stack_dumps: keep rotation, header and
    faulthandler.enable(file=_stacks_file) (fatal-error capture); replace
    faulthandler.dump_traceback_later(15, repeat=True, ...) with
    faulthandler.register(signal.SIGUSR1, file=_stacks_file,
    all_threads=True, chain=False), guarded by hasattr(faulthandler,
    'register') and hasattr(signal, 'SIGUSR1'). Docstring updated.

    EDIT B — disable_stack_dumps: replace cancel_dump_traceback_later()
    with unregister(signal.SIGUSR1) (same guards), before disable() and
    before the file is closed. Docstring updated.

    EDIT C — tests: recording doubles gain register/unregister; assertions
    on dump_traceback_later/cancel_dump_traceback_later become
    register/unregister; one test asserts dump_traceback_later is never
    called.
  alternatives_considered:
    - option: "Remove stack dumps entirely."
      reason_rejected: "Loses the on-demand diagnostic and fatal-error capture."
    - option: "Longer period."
      reason_rejected: "Same hazard, less often."
  benefits:
    - "Debug no longer destabilises the process; dumps remain available on request."
  risks:
    - risk: "SIGUSR1 sent while debug is off uses the default action and terminates gtach."
      mitigation: "Documented: send SIGUSR1 only with debug on. systemd restarts the service."
    - risk: "An on-request dump still reads other threads without the GIL."
      mitigation: "Occurs only when an operator asks for it, not every 15 s."

technical_details:
  current_behavior: "All-thread dump every 15 s while debug is on."
  proposed_behavior: "All-thread dump on SIGUSR1 while debug is on; fatal errors still recorded."
  implementation_approach: "Edits A to C."
  code_changes:
    - component: "main"
      file: "src/gtach/main.py"
      change_summary: "register/unregister SIGUSR1 replaces the repeat timer"
      functions_affected: ["enable_stack_dumps", "disable_stack_dumps"]
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "Operator: stack dump on request"
      change_type: "behaviour"
      details: "kill -USR1 <MainPID> appends one all-thread dump to /opt/gtach/stacks.log while debug is on."
      backward_compatible: "yes"

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Existing recording-double tests adapted."
  test_cases:
    - scenario: "enable_stack_dumps arms."
      expected_result: "calls == ['enable', 'register']; dump_traceback_later never called."
    - scenario: "disable_stack_dumps after enable."
      expected_result: "unregister and disable precede file close."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Edits A to C."
      owner: "planner (this session)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Deploy with ./bin/deploy.sh."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude (planner session, approved by William Watson)"
  verification_date: ""
  verified_by: ""
  test_results: "Edits A-C implemented. Pre-commit check: real faulthandler on Linux, SIGUSR1 to self writes header and all-thread dump to stacks.log. Full suite on the Mac 2026-10-07: 463 passed, 2 xfailed."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-2ac1c602"
      relationship: "supersedes the periodic dump"
  related_issues:
    - issue_ref: "issue-fe755cfd"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-fe755cfd iteration 1."
  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved; implemented in this session."

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
| 1.0 | 2026-10-07 | Initial change document. |
| 1.1 | 2026-10-07 | Approved and implemented. |

---

Copyright (c) 2026 William Watson. MIT License.
