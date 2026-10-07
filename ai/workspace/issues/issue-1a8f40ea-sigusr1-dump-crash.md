Created: 2026 October 07

# Issue: On-Request Stack Dump Crashes the Process

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-1a8f40ea"
  title: "faulthandler.register(SIGUSR1, all_threads=True) terminates gtach with a segmentation fault while dumping a running thread; with debug off SIGUSR1 terminates the process by default action"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-1a8f40ea"
    change_iteration: 1

source:
  origin: "on_device_verification"
  test_ref: "ai/workspace/test/test-36b6ea95-on-device-verification.md (Session E)"
  description: "Six SIGUSR1 requests between ~15:45 and 15:48 on 0.4.6; NRestarts rose to 5."

affected_scope:
  components:
    - name: "enable_stack_dumps / disable_stack_dumps"
      file_path: "src/gtach/main.py"
  designs: []
  version: "0.4.6"

reproduction:
  prerequisites: "Debug on; display thread rendering."
  steps:
    - "kill -USR1 <MainPID> several times."
  frequency: "intermittent (second request of pid 1625)"
  reproducibility_conditions: "Display thread busy (logging emit at the time of the fault)."
  test_data: >
    stacks.log (pid 1625, armed 15:45:34): first dump complete; second dump
    ends inside the display thread at logging/handlers.py shouldRollover
    followed by 'Fatal Python error: Segmentation fault'. systemd restarted
    gtach with debug off; the next three SIGUSR1 requests terminated the
    process by default action. NRestarts=5; last start 15:48:14.
  error_output: "Fatal Python error: Segmentation fault"

behavior:
  expected: "A stack dump on request never affects the process."
  actual: "The dump can crash the process; with debug off the signal terminates it."
  impact: "Stack dumps cannot be used for diagnosis or verification (674bec49)."
  workaround: "Do not send SIGUSR1."

environment:
  python_version: "3.9.2"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    faulthandler's C-level all-thread dump walks other threads' frames
    without the GIL, the same mechanism as the periodic dump of
    issue-fe755cfd; the on-request form only made the fault less
    frequent. The handler was also registered only while debug was on,
    leaving SIGUSR1 at its default action (terminate) otherwise.
  technical_notes: "Reopens issue-fe755cfd: its change removed the timer but kept the unsafe dump mechanism."
  related_issues:
    - "issue-fe755cfd"
    - "issue-674bec49"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-1a8f40ea."
  change_ref: "change-1a8f40ea"
  resolved_date: ""
  resolved_by: ""
  fix_description: "change-1a8f40ea implemented 2026-10-07; on-device verification pending."

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "No faulthandler live-process dumps; test asserts neither register nor dump_traceback_later is armed."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Pi: with debug off and on, send SIGUSR1 ten times while RPM is shown and ten times in setup; NRestarts unchanged; each request appends one dump."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-1a8f40ea"
  test_refs: []

notes: ""

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
      - "Initial issue document from Session E; approved with change-1a8f40ea."

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
| 1.0 | 2026-10-07 | Initial issue document. |

---

Copyright (c) 2026 William Watson. MIT License.
