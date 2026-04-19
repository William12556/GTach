# Change: Watchdog Hard Recovery Darwin Guard for Display Thread

Created: 2026 April 15

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Dependencies](<#6.0 dependencies>)
- [7.0 Testing Requirements](<#7.0 testing requirements>)
- [8.0 Implementation](<#8.0 implementation>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Traceability](<#10.0 traceability>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-a8f2c3e1"
  title: "Watchdog hard recovery Darwin guard for display thread"
  date: "2026-04-15"
  author: "William Watson"
  status: "implemented"
  priority: "critical"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a8f2c3e1"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "issue"
  reference: "issue-a8f2c3e1"
  description: >
    WatchdogMonitor._attempt_hard_recovery calls handle_thread_failure for the
    'display' thread on Darwin, causing ThreadManager._restart_thread to start
    _display_loop on a ThreadPoolExecutor worker (background thread). This
    violates the macOS Cocoa main-thread requirement and terminates the process
    with NSInternalInconsistencyException.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Add a Darwin platform guard to WatchdogMonitor._attempt_hard_recovery.
    When the platform is Darwin and the thread name is 'display', skip the
    handle_thread_failure call and invoke _initiate_graceful_shutdown instead.
    No changes to ThreadManager, DisplayManager, or Linux/Pi behaviour.
  affected_components:
    - name: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "workspace/design/design-gtach-master.md"
      sections:
        - "Core domain — WatchdogMonitor"
  out_of_scope:
    - "ThreadManager._restart_thread"
    - "DisplayManager"
    - "app.py run() method"
    - "Raspberry Pi / Linux watchdog behaviour"
    - "Root cause of why display heartbeats expire (separate concern)"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    On Darwin, _display_loop must run on the main thread (macOS Cocoa constraint).
    WatchdogMonitor._attempt_hard_recovery unconditionally calls
    handle_thread_failure, which submits _restart_thread to a ThreadPoolExecutor
    worker. _restart_thread starts a new thread targeting _display_loop from the
    worker (background thread), violating the Cocoa constraint and crashing the
    process.
  proposed_solution: >
    In _attempt_hard_recovery, detect Darwin and, for the 'display' thread,
    replace handle_thread_failure with _initiate_graceful_shutdown. This prevents
    the illegal background-thread restart while ensuring the application shuts
    down cleanly when the display is unreachable on macOS.
  alternatives_considered:
    - option: "Guard in ThreadManager._restart_thread — skip start() for 'display' on Darwin"
      reason_rejected: >
        Couples generic thread manager to display-specific platform logic.
        Violates separation of concerns.
    - option: "Exclude 'display' from critical_threads on Darwin"
      reason_rejected: >
        Would suppress the health check entirely. Unhealthy display on Darwin
        should still trigger shutdown; it just must not attempt a background
        thread restart.
    - option: "Prevent display_thread from being registered with ThreadManager on Darwin"
      reason_rejected: >
        Would require changes across DisplayManager and ThreadManager, and
        heartbeat-based health monitoring of the display loop would be lost.
  benefits:
    - "Eliminates NSInternalInconsistencyException crash on macOS with --transport serial."
    - "Minimal change — one function, ~8 lines added."
    - "No regression on Linux/Raspberry Pi."
    - "Graceful shutdown preserves clean exit semantics on Darwin."
  risks:
    - risk: "Hardcoded thread name 'display' and platform check in watchdog."
      mitigation: >
        Acceptable short-term. Prevention section of issue-a8f2c3e1 captures
        the longer-term improvement (platform_constraints registration field).
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    WatchdogMonitor._attempt_hard_recovery (watchdog.py):
      - Calls self.thread_manager.handle_thread_failure(name, Exception(...))
        unconditionally for any thread on any platform.
      - On Darwin, this causes ThreadManager._restart_thread to create a new
        threading.Thread(target=_display_loop) and call start() from a
        ThreadPoolExecutor worker, violating the Cocoa main-thread constraint.

  proposed_behavior: >
    WatchdogMonitor._attempt_hard_recovery (watchdog.py):
      - Before calling handle_thread_failure, check if platform is Darwin AND
        thread name is 'display'.
      - If yes: log a critical message and call _initiate_graceful_shutdown
        instead of handle_thread_failure. Return immediately.
      - If no: existing behaviour unchanged.

  implementation_approach: >
    Single targeted edit to _attempt_hard_recovery in watchdog.py.
    Import platform at module level (already available in Python stdlib).
    Guard block added at the top of _attempt_hard_recovery, before the
    existing force/recovery_attempts logic.

  code_changes:
    - component: "WatchdogMonitor"
      file: "src/gtach/core/watchdog.py"
      change_summary: >
        Add Darwin guard at the start of _attempt_hard_recovery. If
        platform.system() == 'Darwin' and name == 'display', log critical
        and call _initiate_graceful_shutdown; return without calling
        handle_thread_failure.
      functions_affected:
        - "_attempt_hard_recovery"
      classes_affected:
        - "WatchdogMonitor"

  data_changes: []

  interface_changes: []
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Dependencies

```yaml
dependencies:
  internal:
    - component: "WatchdogMonitor._initiate_graceful_shutdown"
      impact: "Called instead of handle_thread_failure on Darwin for 'display' thread. Existing method, no changes required."
  external: []
  required_changes: []
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: >
    Manual validation on macOS (development platform). Unit test with mocked
    platform.system() return value. Regression confirmation on TCP path.
  test_cases:
    - scenario: "macOS, --transport serial, no device — wait 60s"
      expected_result: "No NSInternalInconsistencyException. Graceful shutdown log message present."
    - scenario: "macOS, --transport tcp, emulator running"
      expected_result: "Normal operation, display heartbeats established, watchdog never triggers."
    - scenario: "_attempt_hard_recovery called with name='display' on Darwin (unit test)"
      expected_result: "_initiate_graceful_shutdown called; handle_thread_failure not called."
    - scenario: "_attempt_hard_recovery called with name='display' on Linux (unit test)"
      expected_result: "Existing path taken; handle_thread_failure called as before."
    - scenario: "_attempt_hard_recovery called with name='transport' on Darwin (unit test)"
      expected_result: "Existing path taken; handle_thread_failure called as before."
  regression_scope:
    - "src/gtach/core/watchdog.py"
    - "macOS --transport tcp normal operation"
  validation_criteria:
    - "No crash with --transport serial on macOS after 60s."
    - "Graceful shutdown triggered when display is unreachable on Darwin."
    - "No behavioural change on Linux/Pi."
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Implementation

```yaml
implementation:
  effort_estimate: ""
  implementation_steps:
    - step: >
        Add `import platform` to watchdog.py module-level imports if not
        already present.
      owner: "Tactical Domain"
    - step: >
        In WatchdogMonitor._attempt_hard_recovery, insert guard block at the
        top of the method body (before existing force/recovery_attempts checks):

          if platform.system() == 'Darwin' and name == 'display':
              self.logger.critical(
                  f"Display thread unhealthy on Darwin — cannot restart from "
                  f"background thread (Cocoa constraint). Initiating graceful shutdown."
              )
              self._initiate_graceful_shutdown(
                  f"Display thread timeout on Darwin: {timeout:.1f}s"
              )
              return
      owner: "Tactical Domain"
  rollback_procedure: >
    Revert watchdog.py to prior commit. No other files modified.
  deployment_notes: "macOS development only. No deployment changes required."
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  implemented_date: "2026-04-17"
  implemented_by: "William Watson"
  verification_date: "2026-04-17"
  verified_by: "William Watson"
  test_results: >-
    Serial-mode run 134s, 60 FPS. Watchdog stats: warnings=0, hard_recovery=0,
    shutdowns=0. No NSInternalInconsistencyException. Darwin guard confirmed
    present and correct in watchdog.py by code review.
  issues_found: []
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Traceability

```yaml
traceability:
  design_updates:
    - design_ref: "workspace/design/design-gtach-master.md"
      sections_updated:
        - "Core domain — WatchdogMonitor"
      update_date: ""
  related_changes: []
  related_issues:
    - issue_ref: "issue-a8f2c3e1"
      relationship: "resolves"

notes: >
  Net line delta is ~8 lines added to watchdog.py. No interface changes.
  Change is confined to _attempt_hard_recovery. Does not affect ThreadManager,
  DisplayManager, or Raspberry Pi behaviour.

version_history:
  - version: "1.0"
    date: "2026-04-15"
    author: "William Watson"
    changes:
      - "Initial change document created."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author          | Changes                  |
| ------- | ---------- | --------------- | ------------------------ |
| 1.0     | 2026-04-15 | William Watson  | Initial change creation  |
| 1.1     | 2026-04-17 | William Watson  | Closed — implemented and verified |

---

Copyright (c) 2026 William Watson. MIT License.
