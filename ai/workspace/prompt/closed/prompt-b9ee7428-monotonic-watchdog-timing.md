Created: 2026 October 07

# Prompt: Monotonic Time for Heartbeats, Watchdog and Shutdown Budget

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-b9ee7428"
  task_type: "debug"
  source_ref: "change-b9ee7428"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-b9ee7428"
    change_iteration: 1

context:
  purpose: >
    Stop wall-clock steps from triggering watchdog shutdowns. The Pi has
    no RTC; NTP steps the clock after boot, every heartbeat then appears
    hundreds of thousands of seconds old, and the watchdog shuts the
    application down (observed on device 2026-10-07).
  integration: >
    src/gtach/core/thread.py and src/gtach/core/watchdog.py only, plus
    tests. No new dependencies.
  knowledge_references:
    - "ai/workspace/issues/issue-b9ee7428-wall-clock-watchdog-timing.md"
    - "ai/workspace/change/change-b9ee7428-monotonic-watchdog-timing.md"
    - "ai/workspace/audit/audit-36b6ea95-full-codebase.md (B13, Section 6)"
  constraints:
    - "CRITICAL: change ThreadHealth.last_warning_time and last_recovery_time defaults from 0.0 to float('-inf'). time.monotonic() starts near zero at boot, so a 0.0 default would suppress the first warning for 30 s and the first recovery for 10 s of uptime."
    - "Every elapsed-time comparison in the health-check path must use one clock. Do not leave any time.time() in core/watchdog.py."
    - "Leave ThreadInfo.creation_time (default_factory=time.time) unchanged; it is an identity component of __hash__."
    - "Do not change watchdog thresholds, tiers (critical_threads, advisory_threads), recovery logic, or the two-phase lock discipline in _check_thread_health (change-5a9dc15e)."
    - "Do not modify any module outside src/gtach/core/ except tests."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS E to H and run the full test suite."
  requirements:
    functional:
      - "A wall-clock step in either direction does not change watchdog decisions."
      - "A genuine stall beyond critical_timeout of a critical thread still triggers graceful shutdown."
      - "The first warning and first recovery are not suppressed shortly after boot."
      - "ThreadManager.shutdown's time budget is computed on the monotonic clock."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Single clock source, time.monotonic(), for all elapsed-time arithmetic in core/."
  components:
    - name: "EDIT E — core/thread.py"
      type: "module"
      purpose: "Monotonic heartbeats and shutdown budget."
      logic:
        - "register_thread: ThreadInfo(..., last_heartbeat=time.monotonic())."
        - "update_heartbeat: current_time = time.monotonic()."
        - "_restart_thread: thread_info.last_heartbeat = time.monotonic()."
        - "shutdown: shutdown_start, the remaining_timeout computation and cleanup_time use time.monotonic()."
        - "Document on ThreadInfo.last_heartbeat (comment) that it holds time.monotonic() seconds (issue-b9ee7428)."
    - name: "EDIT F — core/watchdog.py"
      type: "module"
      purpose: "Monotonic liveness checks."
      logic:
        - "_check_thread_health, _handle_warning_timeout, _handle_recovery_timeout, get_thread_health_status: current_time = time.monotonic()."
        - "In get_thread_health_status's docstring, state that 'last_heartbeat' is a time.monotonic() value."
    - name: "EDIT G — ThreadHealth defaults"
      type: "class"
      purpose: "Represent 'never' independent of the clock origin."
      logic:
        - "last_warning_time: float = float('-inf')"
        - "last_recovery_time: float = float('-inf')"
        - "Comment: '-inf means never; monotonic time starts near zero at boot (issue-b9ee7428).'"
        - "Leave RecoveryStats.last_recovery_time unchanged."
    - name: "EDIT H — tests"
      type: "module"
      purpose: "Update the aging helper and add regression tests."
      logic:
        - "tests/test_watchdog_process_termination.py: in _aged_thread, use time.monotonic() - age. Change nothing else in that file."
        - "Create tests/test_monotonic_watchdog_timing.py with testing.unit_tests. Drive WatchdogMonitor._check_thread_health() directly, as the existing tests do. Patch time.time via monkeypatch to simulate wall-clock steps."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "Register 'display' and heartbeat it; monkeypatch time.time to return real time + 400000; call _check_thread_health() with a recording shutdown_callback."
      expected: "Shutdown callback not called; no warning naming 'display'."
    - scenario: "Register 'display'; monkeypatch time.time to return real time - 400000; set last_heartbeat to time.monotonic() - (critical_timeout + 5); call _check_thread_health()."
      expected: "Shutdown callback called once."
    - scenario: "No clock patch; 'display' last_heartbeat aged beyond critical_timeout on the monotonic clock."
      expected: "Shutdown callback called once (behaviour preserved)."
    - scenario: "ThreadHealth(name='x')."
      expected: "last_warning_time == float('-inf') and last_recovery_time == float('-inf')."
    - scenario: "Monkeypatch time.monotonic in gtach.core.watchdog to return 5.0; 'display' last_heartbeat set so that elapsed time lies between warning_timeout and recovery_timeout; call _check_thread_health() with caplog at WARNING."
      expected: "A warning naming 'display' is logged on this first check."
  edge_cases:
    - "Advisory thread 'transport' with a forward wall-clock step: no warning (its monotonic heartbeat is fresh)."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit existing files in place; add one test module."
  files:
    - path: "src/gtach/core/thread.py"
      content: "EDIT E"
    - path: "src/gtach/core/watchdog.py"
      content: "EDITS F and G"
    - path: "tests/test_watchdog_process_termination.py"
      content: "EDIT H helper update"
    - path: "tests/test_monotonic_watchdog_timing.py"
      content: "EDIT H new tests"

success_criteria:
  - "grep -n 'time.time()' src/gtach/core/watchdog.py returns no matches."
  - "grep -n 'time\\.time' src/gtach/core/thread.py returns only the ThreadInfo.creation_time default_factory line."
  - "ThreadHealth().last_warning_time and last_recovery_time default to float('-inf')."
  - "critical_threads, advisory_threads, all timeout values and the two-phase locking in _check_thread_health are unchanged."
  - "No file outside src/gtach/core/ and tests/ is modified."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "thread"
        path: "src/gtach/core/thread.py"
      - name: "watchdog"
        path: "src/gtach/core/watchdog.py"
    classes:
      - name: "ThreadManager"
        module: "gtach.core.thread"
      - name: "ThreadInfo"
        module: "gtach.core.thread"
      - name: "WatchdogMonitor"
        module: "gtach.core.watchdog"
      - name: "ThreadHealth"
        module: "gtach.core.watchdog"
    functions:
      - name: "_check_thread_health"
        module: "gtach.core.watchdog"
        signature: "(self) -> None"
      - name: "update_heartbeat"
        module: "gtach.core.thread"
        signature: "(self, name: str) -> None"
    constants: []

notes: >
  On-target verification is a human step: power the Pi off for more than
  a minute, boot with Wi-Fi available, and confirm that
  journalctl -u gtach -b shows no 'Succeeded' or 'Scheduled restart'
  entries.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-b9ee7428 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-07 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
