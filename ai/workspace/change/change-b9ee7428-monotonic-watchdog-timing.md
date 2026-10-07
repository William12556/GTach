Created: 2026 October 07

# Change: Monotonic Time for Heartbeats, Watchdog and Shutdown Budget

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-b9ee7428"
  title: "Replace time.time() with time.monotonic() for heartbeat stamps, watchdog elapsed-time checks and the ThreadManager shutdown budget; default ThreadHealth 'last' times to float('-inf')"
  date: "2026-10-07"
  author: "William Watson"
  status: "implemented"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b9ee7428"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b9ee7428"
  description: >
    Resolves issue-b9ee7428 (audit-36b6ea95 B13). A forward wall-clock
    step above 45 s causes a watchdog shutdown and restart.

scope:
  summary: >
    EDIT E in core/thread.py and EDIT F in core/watchdog.py switch
    elapsed-time arithmetic to time.monotonic(). EDIT G fixes the
    ThreadHealth defaults that would otherwise misbehave near boot.
    EDIT H updates one test helper and adds regression tests.
  affected_components:
    - name: "ThreadManager.register_thread, update_heartbeat, _restart_thread, shutdown"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "WatchdogMonitor._check_thread_health, _handle_warning_timeout, _handle_recovery_timeout, get_thread_health_status"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
    - name: "ThreadHealth"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
    - name: "_aged_thread helper"
      file_path: "tests/test_watchdog_process_termination.py"
      change_type: "modify"
    - name: "Clock-step regression tests"
      file_path: "tests/test_monotonic_watchdog_timing.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "ThreadInfo.creation_time (identity component of __hash__, not elapsed time)."
    - "RecoveryStats.last_recovery_time (never assigned; reported only)."
    - "time.time() in display/, comm/ and utils/ (audit finding C16 and timestamps)."
    - "Watchdog thresholds, tiers, recovery logic and lock discipline (change-5a9dc15e)."
    - "audit-36b6ea95 B01 (hard-recovery defects), handled in a later change."

rational:
  problem_statement: >
    Heartbeats are stamped with time.time() (thread.py:130,146,268) and
    compared with time.time() in the watchdog (watchdog.py:157,175). The
    Pi Zero 2W has no RTC; NTP steps the clock after boot. Observed
    2026-10-07: a ~4.7-day forward step made the critical display thread
    appear stalled and the application shut down and was restarted.
  proposed_solution: >
    EDIT E — core/thread.py: replace time.time() with time.monotonic()
    at register_thread (last_heartbeat), update_heartbeat
    (current_time), _restart_thread (last_heartbeat on restart) and
    shutdown (shutdown_start, remaining_timeout, cleanup_time). Update
    the ThreadInfo.last_heartbeat field comment/docstring to state the
    clock: time.monotonic().

    EDIT F — core/watchdog.py: replace time.time() with time.monotonic()
    in _check_thread_health, _handle_warning_timeout,
    _handle_recovery_timeout and get_thread_health_status.

    EDIT G — ThreadHealth.last_warning_time and last_recovery_time
    default to float('-inf'), meaning "never". With a monotonic clock
    near boot, a default of 0.0 would make `now - 0.0` equal the uptime,
    suppressing the first warning until 30 s of uptime and the first
    recovery until 10 s.

    EDIT H — tests: _aged_thread in
    tests/test_watchdog_process_termination.py ages heartbeats from
    time.monotonic(). New tests cover forward and backward wall-clock
    steps, the near-boot defaults, and a genuine stall.
  alternatives_considered:
    - option: "Detect clock steps and re-baseline heartbeats."
      reason_rejected: "More code and still racy; monotonic time removes the problem."
    - option: "Delay watchdog start until NTP sync (systemd time-sync.target)."
      reason_rejected: >
        The car usually has no network, so sync may never occur, and a
        later step would still trigger shutdown.
    - option: "Keep 0.0 defaults for ThreadHealth."
      reason_rejected: "Suppresses first warning and recovery near boot, as above."
  benefits:
    - "No restart on boot with network access."
    - "Stall detection unaffected by backward clock steps."
    - "Shutdown budget unaffected by clock steps."
  risks:
    - risk: "A missed time.time() leaves a mixed-clock comparison (monotonic heartbeat versus wall-clock now)."
      mitigation: >
        Success criteria require zero time.time() occurrences in
        core/watchdog.py and exactly one (creation_time) in
        core/thread.py; the forward-step test fails on any mixed
        comparison in the health-check path.
    - risk: "get_thread_health_status 'last_heartbeat' changes meaning."
      mitigation: "No caller outside core/ (verified by search); documented in its docstring."

technical_details:
  current_behavior: "Liveness judged by wall-clock differences."
  proposed_behavior: "Liveness judged by monotonic differences; wall-clock steps have no effect."
  implementation_approach: "Mechanical clock-source replacement in two modules plus two dataclass defaults."
  code_changes:
    - component: "ThreadManager"
      file: "src/gtach/core/thread.py"
      change_summary: "time.time() → time.monotonic() at six elapsed-time sites."
      functions_affected:
        - "register_thread"
        - "update_heartbeat"
        - "_restart_thread"
        - "shutdown"
      classes_affected:
        - "ThreadManager"
        - "ThreadInfo"
    - component: "WatchdogMonitor"
      file: "src/gtach/core/watchdog.py"
      change_summary: "time.time() → time.monotonic() at four sites; ThreadHealth defaults float('-inf')."
      functions_affected:
        - "_check_thread_health"
        - "_handle_warning_timeout"
        - "_handle_recovery_timeout"
        - "get_thread_health_status"
      classes_affected:
        - "WatchdogMonitor"
        - "ThreadHealth"
  data_changes: []
  interface_changes:
    - interface: "ThreadInfo.last_heartbeat; get_thread_health_status()['last_heartbeat']"
      change_type: "contract"
      details: "Values are time.monotonic() seconds, not epoch seconds."
      backward_compatible: "no"

dependencies:
  internal:
    - component: "Callers of ThreadInfo.last_heartbeat outside core/"
      impact: "None found in src/ (search for last_heartbeat)."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests driving _check_thread_health directly with patched time.time()."
  test_cases:
    - scenario: "Fresh heartbeat on 'display'; time.time() patched forward by 400,000 s; _check_thread_health()."
      expected_result: "No shutdown callback; no warning for 'display'."
    - scenario: "Fresh heartbeat; time.time() patched backward by 400,000 s; then a genuine stall (last_heartbeat aged 60 s on the monotonic clock)."
      expected_result: "Shutdown callback invoked (critical_timeout exceeded)."
    - scenario: "Genuine stall of 'display' beyond critical_timeout, no clock change."
      expected_result: "Shutdown callback invoked, as before."
    - scenario: "New ThreadHealth instance."
      expected_result: "last_warning_time and last_recovery_time are float('-inf')."
    - scenario: "time.monotonic() patched to return 5.0 (5 s uptime); 'display' heartbeat aged past warning_timeout."
      expected_result: "A warning is logged on the first check (not suppressed by the 30 s spacing)."
  regression_scope:
    - "tests/test_watchdog_process_termination.py in full."
    - "Full tests/ suite."
  validation_criteria:
    - "grep -n 'time.time()' src/gtach/core/watchdog.py returns nothing."
    - "grep -n 'time.time' src/gtach/core/thread.py returns only the ThreadInfo.creation_time default_factory."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS E, F, G."
      owner: "tactical"
    - step: "EDIT H."
      owner: "tactical"
    - step: "Power-cycle the Pi with Wi-Fi available; confirm no restart in the boot's journal."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5a9dc15e"
      relationship: "related. Lock discipline in _check_thread_health, preserved."
    - change_ref: "change-2ac1c602"
      relationship: "related. Critical and advisory tiers, preserved."
  related_issues:
    - issue_ref: "issue-b9ee7428"
      relationship: "resolves"

notes: >
  EDIT G is the part most likely to be missed: the defaults were correct
  only because wall-clock time is large.

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-b9ee7428 iteration 1."
  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in 29bdebedc0343da5eb20ddf25ca4b5e5c4c9c66a."

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
| 1.0 | 2026-10-07 | Initial change document. Monotonic clock for core/ timing; ThreadHealth defaults. |
| 1.2 | 2026-10-07 | Implemented in 29bdebedc0343da5eb20ddf25ca4b5e5c4c9c66a. |

---

Copyright (c) 2026 William Watson. MIT License.
