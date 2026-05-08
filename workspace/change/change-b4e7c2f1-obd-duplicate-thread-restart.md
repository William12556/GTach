Created: 2026 May 08

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-b4e7c2f1"
  title: "Add stop_func to ThreadInfo to prevent duplicate threads on watchdog restart"
  date: "2026-05-08"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b4e7c2f1"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b4e7c2f1"
  description: >
    Watchdog restart of obd_protocol spawns a new thread without stopping the original,
    resulting in two concurrent OBD polling threads and corrupted RPM display.

scope:
  summary: >
    Add an optional stop_func callable to ThreadInfo. ThreadManager._restart_thread
    calls stop_func() before spawning a replacement thread. OBDProtocol registers
    self.stop as stop_func at thread registration time.
  affected_components:
    - name: "ThreadInfo"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "ThreadManager._restart_thread"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "OBDProtocol.__init__"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "OBDProtocol.stop"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
  affected_designs:
    - design_ref: ""
      sections:
        - ""
  out_of_scope:
    - "SimTransport or transport layer changes"
    - "Watchdog timeout thresholds"
    - "Display manager or setup thread"

rational:
  problem_statement: >
    ThreadManager._restart_thread creates a new thread from stored target_func but has
    no mechanism to stop the original thread. The original OBDProtocol thread loop runs
    until OBDProtocol.shutdown_event is set, which only ThreadManager can reach if given
    a callable reference. Two threads then poll the same transport concurrently.
  proposed_solution: >
    Store an optional stop_func: Optional[Callable] on ThreadInfo. At restart time,
    call stop_func() and allow it to complete before starting the replacement thread.
    OBDProtocol passes self.stop as stop_func when registering. OBDProtocol.stop()
    sets shutdown_event and joins the thread with a timeout, and is made idempotent.
  alternatives_considered:
    - option: "Add a threading.Event to ThreadInfo polled by all managed thread loops"
      reason_rejected: "Requires modifying all thread loop implementations and couples loop logic to ThreadManager internals."
    - option: "ThreadManager holds a reference to OBDProtocol directly"
      reason_rejected: "Violates separation of concerns; ThreadManager must remain transport-agnostic."
  benefits:
    - "Original thread is cleanly stopped before replacement starts — no duplicate polling."
    - "Pattern is extensible to any future stateful thread registrations."
    - "No interface changes to WatchdogMonitor or transport layer."
  risks:
    - risk: "stop_func blocks longer than expected, delaying restart."
      mitigation: "OBDProtocol.stop joins with a 5-second timeout (already present). _restart_thread proceeds after stop_func returns regardless."

technical_details:
  current_behavior: >
    ThreadInfo has no stop_func field. _restart_thread starts a new thread without
    stopping the old one. The old OBDProtocol thread runs indefinitely.
  proposed_behavior: >
    ThreadInfo gains stop_func: Optional[Callable] = None. _restart_thread calls
    stop_func() if set before creating the new thread. OBDProtocol.__init__ passes
    self.stop when calling register_thread. OBDProtocol.stop() is idempotent.
  implementation_approach: >
    Five targeted edits across two files. No interface breaking changes.
  code_changes:
    - component: "ThreadInfo"
      file: "src/gtach/core/thread.py"
      change_summary: "Add stop_func: Optional[Callable] = None field to dataclass"
      functions_affected:
        - "ThreadInfo (dataclass)"
      classes_affected:
        - "ThreadInfo"
    - component: "ThreadManager.register_thread"
      file: "src/gtach/core/thread.py"
      change_summary: "Accept optional stop_func kwarg; store on ThreadInfo after creation"
      functions_affected:
        - "register_thread"
      classes_affected:
        - "ThreadManager"
    - component: "ThreadManager._restart_thread"
      file: "src/gtach/core/thread.py"
      change_summary: "Call thread_info.stop_func() before spawning replacement thread if set"
      functions_affected:
        - "_restart_thread"
      classes_affected:
        - "ThreadManager"
    - component: "OBDProtocol.__init__"
      file: "src/gtach/comm/obd.py"
      change_summary: "Pass stop_func=self.stop to register_thread"
      functions_affected:
        - "__init__"
      classes_affected:
        - "OBDProtocol"
    - component: "OBDProtocol.stop"
      file: "src/gtach/comm/obd.py"
      change_summary: "Guard join with is_alive() check for idempotency"
      functions_affected:
        - "stop"
      classes_affected:
        - "OBDProtocol"
  interface_changes:
    - interface: "ThreadManager.register_thread"
      change_type: "signature"
      details: "Add optional stop_func=None keyword argument. Existing callers unaffected (default None)."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "WatchdogMonitor"
      impact: "None. Watchdog calls handle_thread_failure which calls _restart_thread. No changes needed."
    - component: "SetupDisplayManager"
      impact: "None. Setup thread does not require a stop_func as it exits cleanly."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Manual integration test on Pi with simbt transport. Log inspection."
  test_cases:
    - scenario: "Normal operation — no watchdog restart"
      expected_result: "Single TX:010C per poll cycle throughout session."
    - scenario: "Watchdog triggers obd_protocol restart"
      expected_result: "Log shows stop_func called, single TX:010C resumes after restart, no paired TX lines."
    - scenario: "RPM sweep visual inspection after restart"
      expected_result: "Smooth sine sweep with no jumps."
  regression_scope:
    - "OBD connect and poll in simbt mode"
    - "OBD connect and poll with real ELM327 via TCP"
  validation_criteria:
    - "No paired SimTransport TX:010C lines in log after any restart event"
    - "RPM values follow single smooth trajectory"

implementation:
  implementation_steps:
    - step: "Edit ThreadInfo dataclass — add stop_func field"
      owner: "Claude Code"
    - step: "Edit ThreadManager.register_thread — accept and store stop_func kwarg"
      owner: "Claude Code"
    - step: "Edit ThreadManager._restart_thread — call stop_func before new thread"
      owner: "Claude Code"
    - step: "Edit OBDProtocol.__init__ — pass stop_func=self.stop"
      owner: "Claude Code"
    - step: "Edit OBDProtocol.stop — add is_alive() guard"
      owner: "Claude Code"
  rollback_procedure: "Revert src/gtach/core/thread.py and src/gtach/comm/obd.py to prior commit."
  deployment_notes: "Rebuild wheel and deploy to Pi after implementation."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-b4e7c2f1"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial change document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
