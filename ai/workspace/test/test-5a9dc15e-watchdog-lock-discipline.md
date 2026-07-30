Created: 2026 July 30

# Test: Watchdog Lock Discipline

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-5a9dc15e"
  title: "Unit tests for collect-then-dispatch health checking and two-phase soft-recovery heartbeat observation"
  date: "2026-07-30"
  author: "William Watson"
  status: "planned"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-5a9dc15e"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "WatchdogMonitor._check_thread_health; WatchdogMonitor._attempt_soft_recovery"
  design_refs: []
  change_refs:
    - "change-5a9dc15e"
  requirement_refs:
    - "core-comm-utils-code-review.md §3.3"
    - "core-comm-utils-code-review.md §4.1"
    - "core-comm-utils-code-review.md §7.0 recommendation #2"

scope:
  description: >
    Verifies that no blocking call executes while thread_manager._lock is
    held, that soft recovery can now observe a heartbeat written during
    its own observation window, and that the collect-then-dispatch
    restructure preserves the dispatch set, order and statistics of the
    original traversal. Establishes the regression net for
    change-5a9dc15e ahead of v0.3.0 (ai/task.md §8.2).
  test_objectives:
    - "Confirm soft recovery succeeds when the monitored thread advances its heartbeat during the window — the case the previous implementation could not observe."
    - "Confirm a competing update_heartbeat is not blocked for the duration of a recovery attempt."
    - "Confirm thread_manager._lock is held only for the health-check traversal, not for the handlers."
    - "Confirm handler dispatch set and order are unchanged by the restructure."
    - "Confirm a thread unregistered mid-window is handled without exception."
  in_scope:
    - "src/gtach/core/watchdog.py — _check_thread_health and _attempt_soft_recovery"
  out_scope:
    - "src/gtach/core/thread.py — unmodified by change-5a9dc15e"
    - "_attempt_hard_recovery — its sleep was already outside the lock; reviewed and unchanged"
    - "get_thread_health_status — traverses under the lock but makes no blocking call"
    - "_emergency_shutdown — calls os._exit; not unit testable and out of scope"
    - "_initiate_graceful_shutdown beyond confirming it remains reachable from _handle_critical_timeout"
  dependencies:
    - "unittest.mock for the ThreadManager double"
    - "threading for the competing-heartbeat probe"
    - "No pygame, no hardware"

test_environment:
  python_version: "3.9+ (development platform); 3.11 on target"
  os: "macOS Apple Silicon (development); Debian Linux Raspberry Pi OS (target)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
    - name: "unittest.mock"
      version: "stdlib"
    - name: "threading"
      version: "stdlib"
  test_framework: "pytest"
  test_data_location: "Inline fixtures. A ThreadManager double exposing _lock (an RLock), threads (a dict of ThreadInfo-like objects) and update_heartbeat"

test_cases:
  - case_id: "TC-001"
    description: "Soft recovery succeeds when the heartbeat advances during the observation window"
    category: "positive"
    preconditions:
      - "A ThreadManager double holds one registered thread with a known last_heartbeat"
    test_steps:
      - step: "1"
        action: "Start a helper thread that sleeps 0.2 s, acquires the double's lock and increments last_heartbeat"
      - step: "2"
        action: "Call _attempt_soft_recovery('obd_protocol', health, 5.0)"
      - step: "3"
        action: "Join the helper and read recovery_stats"
    inputs:
      - parameter: "heartbeat delta"
        value: "+1.0 s applied at t=0.2 s"
        type: "float"
    expected_outputs:
      - field: "recovery_stats.soft_recovery_successes"
        expected_value: "1"
        validation: "Incremented exactly once"
      - field: "health.consecutive_failures"
        expected_value: "0"
        validation: "_reset_thread_health was called"
    postconditions:
      - "This case fails against the pre-change implementation, which held the lock across the sleep and so prevented the helper from writing"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Success recorded and health reset"
    defects: []

  - case_id: "TC-002"
    description: "Soft recovery does not report success when the heartbeat is static"
    category: "negative"
    preconditions:
      - "One registered thread; no helper writes to last_heartbeat"
    test_steps:
      - step: "1"
        action: "Call _attempt_soft_recovery with a static heartbeat"
      - step: "2"
        action: "Read recovery_stats"
    inputs:
      - parameter: "heartbeat delta"
        value: "0"
        type: "float"
    expected_outputs:
      - field: "recovery_stats.soft_recovery_attempts"
        expected_value: "1"
        validation: "Attempt still counted"
      - field: "recovery_stats.soft_recovery_successes"
        expected_value: "0"
        validation: "No success recorded"
      - field: "health.current_level"
        expected_value: "RecoveryLevel.SOFT_RECOVERY"
        validation: "Level was set and not reset"
    postconditions:
      - "Escalation to hard recovery remains available to the caller"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Attempt counted, success not counted"
    defects: []

  - case_id: "TC-003"
    description: "Thread unregistered during the observation window"
    category: "edge"
    preconditions:
      - "One registered thread"
    test_steps:
      - step: "1"
        action: "Start a helper that sleeps 0.2 s then deletes the entry from the double's threads dict under the lock"
      - step: "2"
        action: "Call _attempt_soft_recovery"
    inputs:
      - parameter: "threads dict"
        value: "Entry removed at t=0.2 s"
        type: "dict"
    expected_outputs:
      - field: "exception"
        expected_value: "None"
        validation: "Stage 3 re-tests membership before indexing; no KeyError"
      - field: "recovery_stats.soft_recovery_successes"
        expected_value: "0"
        validation: "Treated as not recovered — the conservative outcome"
    postconditions:
      - "No error logged at ERROR level; the disappearance is not an exceptional condition"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No exception and no false success"
    defects: []

  - case_id: "TC-004"
    description: "Thread absent before the observation begins"
    category: "negative"
    preconditions:
      - "The threads dict is empty"
    test_steps:
      - step: "1"
        action: "Call _attempt_soft_recovery('missing', health, 5.0)"
    inputs:
      - parameter: "name"
        value: "missing"
        type: "str"
    expected_outputs:
      - field: "return"
        expected_value: "Early return from stage 1"
        validation: "No sleep occurs; measured wall time well under 1.0 s"
      - field: "log record"
        expected_value: "One DEBUG line noting the thread is no longer registered"
        validation: "caplog at DEBUG"
    postconditions:
      - "soft_recovery_attempts was still incremented in the preamble"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Returns quickly without sleeping"
    defects: []

  - case_id: "TC-005"
    description: "A competing update_heartbeat is not blocked during soft recovery"
    category: "positive"
    preconditions:
      - "A real threading.RLock on the ThreadManager double"
    test_steps:
      - step: "1"
        action: "Start a helper thread that repeatedly acquires the lock, records the acquisition latency, and releases"
      - step: "2"
        action: "Call _attempt_soft_recovery in the main thread"
      - step: "3"
        action: "Assert the maximum observed acquisition latency"
    inputs:
      - parameter: "probe interval"
        value: "10 ms"
        type: "float"
    expected_outputs:
      - field: "max acquisition latency"
        expected_value: "< 50 ms"
        validation: "Generous bound. The pre-change implementation would show approximately 1000 ms"
    postconditions:
      - "Demonstrates §3.3 is corrected, not merely restructured"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No acquisition blocked beyond the bound"
    defects: []

  - case_id: "TC-006"
    description: "Health check dispatches the correct handler per severity band"
    category: "positive"
    preconditions:
      - "Four registered threads with heartbeat ages placing one in each band: critical, recovery, warning, healthy"
    test_steps:
      - step: "1"
        action: "Patch the four handlers with mocks"
      - step: "2"
        action: "Call _check_thread_health()"
      - step: "3"
        action: "Assert each mock was called once with the expected name"
    inputs:
      - parameter: "heartbeat ages"
        value: "critical_timeout+1, recovery_timeout+1, warning_timeout+1, 0"
        type: "float"
    expected_outputs:
      - field: "_handle_critical_timeout"
        expected_value: "Called once"
        validation: "assert_called_once_with the critical thread's name"
      - field: "_handle_recovery_timeout"
        expected_value: "Called once"
        validation: "As above"
      - field: "_handle_warning_timeout"
        expected_value: "Called once"
        validation: "As above"
      - field: "_reset_thread_health"
        expected_value: "Called once"
        validation: "For the healthy thread"
    postconditions:
      - "Comparison order critical, recovery, warning, else reset is preserved"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Exactly one handler per thread, matching its band"
    defects: []

  - case_id: "TC-007"
    description: "The state lock is released before any handler runs"
    category: "positive"
    preconditions:
      - "Three simultaneously unhealthy threads"
    test_steps:
      - step: "1"
        action: "Replace the handlers with mocks that assert the lock is acquirable from a second thread at the moment they are called"
      - step: "2"
        action: "Call _check_thread_health()"
    inputs:
      - parameter: "unhealthy threads"
        value: "3"
        type: "int"
    expected_outputs:
      - field: "lock acquirable inside each handler"
        expected_value: "True for all three"
        validation: "A second thread's non-blocking acquire succeeds during each handler call"
    postconditions:
      - "Confirms §4.1 is corrected: recovery is no longer serialized under the traversal lock"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Lock free during every handler invocation"
    defects: []

  - case_id: "TC-008"
    description: "Threads not in RUNNING or STARTING are skipped and gain no health record"
    category: "boundary"
    preconditions:
      - "One thread in STOPPED status and one in RUNNING"
    test_steps:
      - step: "1"
        action: "Call _check_thread_health()"
      - step: "2"
        action: "Inspect self.thread_health"
    inputs:
      - parameter: "statuses"
        value: "STOPPED, RUNNING"
        type: "ThreadStatus"
    expected_outputs:
      - field: "thread_health keys"
        expected_value: "Only the RUNNING thread"
        validation: "The skip precedes health-record creation, as before"
      - field: "handler calls for the STOPPED thread"
        expected_value: "None"
        validation: "No mock invoked with that name"
    postconditions:
      - "Skip semantics unchanged by the restructure"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "STOPPED thread absent from thread_health and undispatched"
    defects: []

  - case_id: "TC-009"
    description: "Empty threads dictionary"
    category: "edge"
    preconditions:
      - "No registered threads"
    test_steps:
      - step: "1"
        action: "Call _check_thread_health()"
    inputs: []
    expected_outputs:
      - field: "handler calls"
        expected_value: "None"
        validation: "The pending list is empty and phase 2 is a no-op"
      - field: "exception"
        expected_value: "None"
        validation: "No iteration error"
    postconditions:
      - "Method returns normally"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No dispatch, no exception"
    defects: []

  - case_id: "TC-010"
    description: "Dispatch order follows traversal order"
    category: "positive"
    preconditions:
      - "Three unhealthy threads inserted into the dict in a known order"
    test_steps:
      - step: "1"
        action: "Record handler invocations against a shared list"
      - step: "2"
        action: "Call _check_thread_health()"
    inputs:
      - parameter: "insertion order"
        value: "display, obd_protocol, transport"
        type: "list"
    expected_outputs:
      - field: "invocation order"
        expected_value: "display, obd_protocol, transport"
        validation: "The pending list is neither sorted nor deduplicated"
    postconditions:
      - "Ordering is a property of the restructure that must not drift"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Recorded order matches insertion order"
    defects: []

  - case_id: "TC-011"
    description: "No time.sleep call lies within a thread_manager._lock block"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Parse src/gtach/core/watchdog.py with the ast module"
      - step: "2"
        action: "For every With node whose context expression is an attribute access ending in thread_manager._lock, walk its body for a Call to time.sleep"
    inputs:
      - parameter: "source file"
        value: "src/gtach/core/watchdog.py"
        type: "path"
    expected_outputs:
      - field: "matches"
        expected_value: "0"
        validation: "Static assertion; no runtime behaviour involved"
    postconditions:
      - "Guards against reintroduction by a future edit"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Zero sleeps found inside the lock"
    defects: []

  - case_id: "TC-012"
    description: "Recovery statistics match pre-change values for a fixed input sequence"
    category: "regression"
    preconditions:
      - "A scripted sequence of health-check cycles with known heartbeat ages"
    test_steps:
      - step: "1"
        action: "Run ten cycles against a deterministic sequence"
      - step: "2"
        action: "Read get_recovery_stats()"
    inputs:
      - parameter: "cycles"
        value: "10"
        type: "int"
    expected_outputs:
      - field: "warnings_issued, soft_recovery_attempts, hard_recovery_attempts, shutdown_triggers"
        expected_value: "Values recorded as the baseline in the T06 result"
        validation: "Counting semantics unchanged by the restructure"
    postconditions:
      - "Statistics are a stable contract for the dashboard and logs"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Counters match the recorded baseline"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "core review §3.3 — lock held across time.sleep"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-004"
        - "TC-005"
        - "TC-011"
    - requirement_ref: "core review §4.1 — recovery serialized under the health-check lock"
      test_cases:
        - "TC-006"
        - "TC-007"
        - "TC-008"
        - "TC-009"
        - "TC-010"
        - "TC-012"
  code_coverage:
    target: "100% of _check_thread_health and _attempt_soft_recovery branches"
    achieved: ""
  untested_areas:
    - component: "_emergency_shutdown"
      reason: "Calls os._exit(1); not unit testable without process isolation, and unmodified by change-5a9dc15e"
    - component: "_attempt_hard_recovery"
      reason: "Unmodified. Its sleep was already outside the lock; reviewed during the change and left as written"

test_execution_summary:
  total_cases: 12
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""
  execution_time: ""
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""

traceability:
  requirements:
    - requirement_ref: "core-comm-utils-code-review.md §7.0 #2"
      test_cases:
        - "TC-001"
        - "TC-005"
        - "TC-007"
  designs: []
  changes:
    - change_ref: "change-5a9dc15e"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-004"
        - "TC-005"
        - "TC-006"
        - "TC-007"
        - "TC-008"
        - "TC-009"
        - "TC-010"
        - "TC-011"
        - "TC-012"

notes: >
  Generated pytest file: tests/core/test_watchdog_lock_discipline.py, per
  P06 §1.7.3.

  TC-001 and TC-005 are the two cases that fail against the pre-change
  implementation. They are the evidence that §3.3 was a defect rather
  than a style preference, and must not be dropped if the case list is
  trimmed.

  TC-005 and TC-007 assert timing bounds. On a loaded development machine
  these can be flaky; the 50 ms bound is deliberately an order of
  magnitude below the 1000 ms the defect produced, so it discriminates
  without being tight. If flakiness is observed, raise the bound rather
  than removing the case.

  TC-012's expected values are not yet known. Record them from the first
  green run into the T06 result, then treat them as the baseline.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial test document for change-5a9dc15e, per ai/task.md §8.2."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t05_test"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial test document for change-5a9dc15e, per ai/task.md §8.2. |

---

Copyright (c) 2026 William Watson. MIT License.
