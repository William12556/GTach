Created: 2026 May 08

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-d2e4a1f9"
  title: "DisplayManager reads ThreadManager.threads dict without state lock — data race"
  date: "2026-05-08"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "code_review"
  test_ref: ""
  description: >
    _draw_status_indicator in manager.py accesses self.thread_manager.threads
    directly without acquiring _state_lock. ThreadManager documents threads as
    protected by _state_lock. Concurrent modification by watchdog or OBD thread
    can produce a stale or partially-updated read on CPython (GIL prevents
    corruption but not stale reads).

affected_scope:
  components:
    - name: "DisplayManager._draw_status_indicator"
      file_path: "src/gtach/display/manager.py"
    - name: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
  designs:
    - design_ref: ""
  version: "0.2.37"

reproduction:
  prerequisites: "Normal running application."
  steps:
    - "Not directly reproducible — race condition."
    - "Under load, watchdog or OBD restart modifies threads dict while display reads it."
  frequency: "intermittent"
  reproducibility_conditions: "Thread restart or watchdog activity coincident with display frame."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    Status indicator reflects accurate thread state. Read is consistent with
    the locked state seen by ThreadManager.
  actual: >
    On CPython, GIL prevents dict corruption but does not prevent the display
    thread reading a stale status value from a ThreadInfo object being
    concurrently modified by the watchdog thread.
  impact: >
    Low. Status indicator may show incorrect connection state for one frame.
    No crash risk on CPython. Not a data flow concern but a correctness issue.
  workaround: "None needed — impact is cosmetic."

environment:
  python_version: "3.9"
  os: "Linux (Raspberry Pi Zero 2W, Debian)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    _draw_status_indicator bypasses ThreadManager's public API and reads
    the internal threads dict directly. ThreadManager provides
    get_thread_status(name) which acquires _state_lock. The display manager
    should use the public API.
  technical_notes: >
    Replace direct dict access with thread_manager.get_thread_status('transport').
    This uses the existing locked accessor and removes the direct dependency
    on ThreadManager internals.
  related_issues:
    - issue_ref: ""
      relationship: ""

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Replace direct threads dict access in _draw_status_indicator with
    thread_manager.get_thread_status('transport').
  change_ref: "change-d2e4a1f9"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    ThreadManager internal state (threads dict, ThreadInfo objects) should
    only be accessed via ThreadManager public methods. Direct dict access
    from outside ThreadManager should be treated as a code smell.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "Code review: confirm no direct threads dict access remains in manager.py"
    - "Run gtach --transport simbt and confirm status indicator still renders"
    - "No KeyError or AttributeError in log"
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-d2e4a1f9"
  test_refs: []

notes: "Low severity. Does not affect RPM data flow. Correctness fix."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial issue document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
