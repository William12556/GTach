Created: 2026 October 07

# Issue: Periodic Stack Dumps Crash the Process

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-fe755cfd"
  title: "With debug on, faulthandler.dump_traceback_later(15, repeat=True) terminates gtach on a dump tick; systemd restarts it repeatedly"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-fe755cfd"
    change_iteration: 1

source:
  origin: "on_device_verification"
  test_ref: "ai/workspace/test/test-36b6ea95-on-device-verification.md (Session A follow-up)"
  description: "Service started with --debug through a temporary systemd drop-in; the process restarted ten times in 13 minutes."

affected_scope:
  components:
    - name: "enable_stack_dumps / disable_stack_dumps"
      file_path: "src/gtach/main.py"
  designs: []
  version: "0.4.5"

reproduction:
  prerequisites: "Debug on at start (--debug) or via OPTIONS toggle."
  steps:
    - "Run gtach with debug on for a few minutes."
  frequency: "always (ten terminations between 14:11 and 14:25 on 2026-10-07)"
  reproducibility_conditions: "Display thread busy rendering; Python 3.9.2 on the Pi."
  test_data: >
    Lifetimes from arming to termination: 75 s, 240 s, 45 s (multiples of
    the 15 s dump period). No shutdown record in any log. stacks.log.2
    (pid 1661) holds 'Fatal Python error: Segmentation fault' interleaved
    with a periodic dump, current thread = display thread
    (_draw_radial_mode). stacks.log.1 and .3 end part-way through a dump
    of the display thread.
  error_output: "Fatal Python error: Segmentation fault"

behavior:
  expected: "Debug logging does not affect process stability."
  actual: "The process terminates on a dump tick; systemd restarts it after 5 s."
  impact: "Debug cannot be used in the field; repeated restarts."
  workaround: "Keep debug off."

environment:
  python_version: "3.9.2"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    faulthandler's repeat timer dumps all threads from a C thread without
    holding the GIL. Reading a running thread's frames concurrently is
    unsafe; on the Pi the dump coincides with process termination. The
    exact faulting instruction is not determined (inference from timing
    and the interleaved fatal-error record; confidence high that the
    periodic dump is the trigger).
  technical_notes: "Related open item in ai/task.md: faulthandler capture (issue-2ac1c602)."
  related_issues:
    - "issue-2ac1c602"
    - "issue-3b8c50f2"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-fe755cfd."
  change_ref: "change-fe755cfd"
  resolved_date: ""
  resolved_by: ""
  fix_description: "change-fe755cfd implemented 2026-10-07; on-device verification pending."

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "No timer-driven cross-thread dumps."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Pi: debug on for 30 minutes; NRestarts unchanged; kill -USR1 writes one dump to stacks.log."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-fe755cfd"
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
      - "Initial issue document."

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
