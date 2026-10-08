Created: 2026 October 07

# Change: Python-Level On-Request Stack Dump

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-1a8f40ea"
  title: "Replace faulthandler.register(SIGUSR1) with a Python-level SIGUSR1 handler installed for the process lifetime"
  date: "2026-10-07"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-1a8f40ea"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-1a8f40ea"
  description: "Resolves issue-1a8f40ea and the remaining part of issue-fe755cfd. Approved by William Watson on 2026-10-07."

scope:
  summary: "New module gtach.utils.stack_dump; main.py installs it and no longer arms faulthandler.register; tests."
  affected_components:
    - name: "stack_dump"
      file_path: "src/gtach/utils/stack_dump.py (new)"
      change_type: "add"
    - name: "main"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_stack_dump_handler.py (new), tests/test_stack_dump_toggle.py, tests/test_stacks_log_rotation.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Capturing stalls in which C code holds the GIL (a Python handler cannot run then)."
    - "Fatal-error capture (faulthandler.enable, unchanged)."

rational:
  problem_statement: "See issue-1a8f40ea."
  proposed_solution: >
    EDIT A — new gtach/utils/stack_dump.py: format_all_threads() builds the
    dump from sys._current_frames() and threading.enumerate() (thread
    names), most recent call first, faulthandler-compatible layout plus a
    '=== gtach <version> pid <pid> dump <time> ===' header; make_handler()
    appends it to stacks.log and never raises; install() sets the handler
    with signal.signal(SIGUSR1) and returns False off the main thread or
    without SIGUSR1.

    EDIT B — main.py: main() calls stack_dump.install(lambda: _STACKS_LOG)
    after setup_logging, for every run regardless of debug.
    enable_stack_dumps arms faulthandler.enable only; disable_stack_dumps
    no longer unregisters. _DUMP_SIGNAL and the signal import removed;
    docstrings updated.

    EDIT C — tests: new test_stack_dump_handler.py; the two existing files
    assert that neither faulthandler.register nor dump_traceback_later is
    armed.
  alternatives_considered:
    - option: "Remove on-request dumps."
      reason_rejected: "Loses the diagnostic needed for 674bec49 and field faults."
  benefits:
    - "SIGUSR1 never terminates or crashes the process; dumps available with debug off."
  risks:
    - risk: "A dump may be slightly inconsistent while threads keep running."
      mitigation: "Frames are reference-counted Python objects; staleness, not memory errors."

technical_details:
  current_behavior: "C-level dump without the GIL; SIGUSR1 default action when debug off."
  proposed_behavior: "Python-level dump; handler always installed."
  implementation_approach: "Edits A to C."
  code_changes:
    - component: "stack_dump"
      file: "src/gtach/utils/stack_dump.py"
      change_summary: "format_all_threads, make_handler, install"
      functions_affected: ["format_all_threads", "make_handler", "install"]
      classes_affected: []
    - component: "main"
      file: "src/gtach/main.py"
      change_summary: "install handler; drop faulthandler.register/unregister"
      functions_affected: ["main", "enable_stack_dumps", "disable_stack_dumps"]
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "Operator: kill -USR1 <MainPID>"
      change_type: "behaviour"
      details: "Appends one dump with thread names to /opt/gtach/stacks.log, whether or not debug is on."
      backward_compatible: "yes"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-fe755cfd"
      relationship: "supersedes its SIGUSR1 mechanism"

testing_requirements:
  test_approach: "Unit tests including a real SIGUSR1 to the test process."
  test_cases:
    - scenario: "format_all_threads with a parked named thread."
      expected_result: "Thread name and function present; header first."
    - scenario: "Real SIGUSR1 after install."
      expected_result: "Dump appended; process continues."
    - scenario: "install off the main thread."
      expected_result: "False."
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
  verification_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Pre-commit check (Python 3.10, stub environment): 20 signals -> 20 dumps; 300 signals with four busy threads -> no fault; off-main install False; unwritable path handled. Full suite on the Mac 2026-10-07: 471 passed, 2 xfailed. On device: Pi 0.4.7 pid 453, 2026-10-08 09:48-09:49: five SIGUSR1 requests with debug on and one with debug off (toggle off 09:49:29); six dumps appended, each naming all seven threads; same PID throughout (no restart); no fatal record."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-fe755cfd"
      relationship: "supersedes in part"
  related_issues:
    - issue_ref: "issue-1a8f40ea"
      relationship: "resolves"
    - issue_ref: "issue-fe755cfd"
      relationship: "resolves (reopened)"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document; approved and implemented."

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
| 1.0 | 2026-10-07 | Initial change document; approved and implemented. |
| 1.1 | 2026-10-08 | Verified on device; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
