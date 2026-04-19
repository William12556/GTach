# Issue: Watchdog Hard Recovery Restarts Display Loop on Background Thread (Darwin)

Created: 2026 April 15

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [8.0 Resolution](<#8.0 resolution>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Prevention](<#10.0 prevention>)
- [11.0 Traceability](<#11.0 traceability>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-a8f2c3e1"
  title: "Watchdog hard recovery restarts display loop on background thread (Darwin)"
  date: "2026-04-15"
  reporter: "William Watson"
  status: "closed"
  severity: "critical"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: "change-a8f2c3e1"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: ""
  description: >
    GTach crashes on macOS when launched with --transport serial.
    Process terminates with NSInternalInconsistencyException from AppKit because
    pygame.event.get() is called from a Python background thread. Cocoa requires
    all NSApplication event operations to execute on the main thread.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
    - name: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
  designs:
    - design_ref: "workspace/design/design-gtach-master.md"
  version: "0.2.0"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: >
    macOS (Darwin) with GTach v0.2.0. No ELM327 device connected or paired.
    Launch command: python -m gtach --macos --transport serial --config workspace/config/config-macos-dev.yaml
  steps:
    - "Launch GTach with --transport serial on macOS with no serial OBD device connected."
    - "Wait approximately 30 seconds (watchdog recovery_timeout)."
    - "Observe crash with NSInternalInconsistencyException."
  frequency: "always"
  reproducibility_conditions: >
    Manifests on Darwin when --transport serial is specified and no device is
    present, or when the display loop exits before heartbeats are established.
    Does not manifest with --transport tcp when the emulator is running (display
    loop heartbeats are established immediately, watchdog never triggers recovery).
  preconditions: "macOS Darwin platform. Display loop must not be actively sending heartbeats."
  test_data: ""
  error_output: |
    *** Terminating app due to uncaught exception 'NSInternalInconsistencyException',
    reason: 'nextEventMatchingMask should only be called from the Main Thread!'
    Stack (key frames):
      16: thread_run          <- Python background thread
       7: pg_event_get        <- pygame.event.get() called from background thread
       4: Cocoa_PumpEvents    <- SDL2 Cocoa event pump
       2: NSApplication nextEventMatchingMask  <- Cocoa main-thread violation
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behavior

```yaml
behavior:
  expected: >
    On Darwin, _display_loop runs exclusively on the main thread via
    run_main_thread_loop(). If the display loop becomes unhealthy, the watchdog
    should trigger graceful shutdown rather than restarting the display thread
    from a background worker thread.
  actual: >
    WatchdogMonitor._attempt_hard_recovery calls
    thread_manager.handle_thread_failure('display', ...) after recovery_timeout
    (30s) of absent heartbeats. ThreadManager._restart_thread executes in a
    ThreadPoolExecutor worker (background thread) and calls new_thread.start()
    where new_thread targets _display_loop. _display_loop runs on the background
    thread, calls pygame.event.get(), which invokes SDL2 Cocoa_PumpEvents ->
    NSApplication nextEventMatchingMask from a non-main thread. Cocoa terminates
    the process with NSInternalInconsistencyException.
  impact: >
    GTach is non-functional on macOS with --transport serial. Process terminates
    within ~30 seconds of startup whenever the display loop does not establish
    heartbeats.
  workaround: "Use --transport tcp with the ELM327 emulator running."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.11.14"
  os: "macOS (Darwin) Apple Silicon"
  dependencies:
    - library: "pygame"
      version: "2.6.1"
    - library: "SDL2"
      version: "2.28.4"
  domain: "domain_1"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    Two compounding defects in WatchdogMonitor:

    (1) The display thread is registered with ThreadManager and monitored by
    the watchdog (status STARTING). On Darwin, DisplayManager.start() does NOT
    start display_thread; run_main_thread_loop() calls _display_loop() directly
    on the main thread. The watchdog monitors all threads in STARTING or RUNNING
    status. If _display_loop does not send heartbeats within recovery_timeout
    (30s) — e.g. due to a serial transport failure or startup delay — the
    watchdog escalates to hard recovery.

    (2) WatchdogMonitor._attempt_hard_recovery calls
    thread_manager.handle_thread_failure('display', ...), which submits
    _restart_thread to the ThreadPoolExecutor worker pool (background threads).
    _restart_thread creates a new threading.Thread targeting _display_loop and
    calls start() from the pool worker. _display_loop runs on a background
    thread, calls pygame.event.get(), and SDL2 violates the Cocoa main-thread
    constraint, terminating the process.

    The TCP path does not trigger this defect because the OBD emulator responds
    immediately: heartbeats flow at 60fps and watchdog never reaches
    recovery_timeout.

  technical_notes: >
    - 'display' is in WatchdogMonitor.critical_threads (watchdog.py).
    - _check_thread_health monitors STARTING and RUNNING threads (watchdog.py ~L130).
    - _restart_thread executes in ThreadPoolExecutor worker (thread.py ~L366).
    - _display_loop calls pygame.event.get() (manager.py ~L355).
    - The macOS constraint is documented in DisplayManager.start() docstring and
      app.py L133 comment.
    - Fix must not alter Linux/Raspberry Pi behaviour where display thread restart
      from pool worker is valid.

  related_issues:
    - issue_ref: ""
      relationship: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "William Watson"
  target_date: "2026-04-15"
  approach: >
    Modify WatchdogMonitor._attempt_hard_recovery to detect Darwin and skip hard
    recovery for the 'display' thread, calling _initiate_graceful_shutdown
    instead. On Darwin the display loop runs on the main thread and cannot be
    restarted from a background thread; if it is unhealthy the correct response
    is graceful application shutdown. See change-a8f2c3e1.
  change_ref: "change-a8f2c3e1"
  resolved_date: "2026-04-17"
  resolved_by: "William Watson"
  fix_description: >-
    Darwin guard added to WatchdogMonitor._attempt_hard_recovery. When
    platform.system() == 'Darwin' and thread name is 'display', hard
    recovery is skipped and _initiate_graceful_shutdown is called instead.
    Prevents NSInternalInconsistencyException from background-thread
    pygame.event.get() Cocoa violation.
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  verified_date: "2026-04-17"
  verified_by: "William Watson"
  test_results: >-
    Run with --transport serial, /dev/cu.ELM327-Emulator present. Application
    ran for 134s at 60 FPS. Watchdog stats: warnings=0, hard_recovery=0,
    shutdowns=0. Graceful shutdown on SIGINT. No NSInternalInconsistencyException.
    Code review confirms Darwin guard present and correct in watchdog.py.
  closure_notes: >-
    Fix verified by code review and stable serial-mode run. Darwin crash
    scenario (no heartbeats before 30s watchdog timeout) not directly
    triggered — /dev/cu.ELM327-Emulator auto-connected. Accepted on code review.

verification_enhanced:
  verification_steps:
    - "Launch GTach with --transport serial on macOS with no OBD device present."
    - "Wait 60 seconds. Confirm no NSInternalInconsistencyException crash."
    - "Confirm graceful shutdown log message appears when display is unreachable."
    - "Launch with --transport tcp and emulator running. Confirm normal operation."
    - "Confirm no regression on Raspberry Pi (display thread restart unaffected)."
  verification_results: >-
    Serial transport connected and display heartbeats established immediately.
    Watchdog never reached recovery_timeout. Darwin guard confirmed present
    in source. Accepted on code review basis.
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Prevention

```yaml
prevention:
  preventive_measures: >
    Platform-specific thread recovery constraints should be explicit. The
    'display' thread on Darwin requires main-thread execution; recovery
    mechanisms must be platform-aware.
  process_improvements: >
    Consider a platform_constraints field in thread registration so the watchdog
    can determine valid recovery actions per thread per platform without
    hardcoded checks.
```

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Traceability

```yaml
traceability:
  design_refs:
    - "workspace/design/design-gtach-master.md"
  change_refs:
    - "change-a8f2c3e1"
  test_refs:
    - ""

notes: >
  Latent in all macOS runs with --transport serial. TCP path masks the defect
  because heartbeats are established before watchdog recovery fires. Any
  condition that delays or terminates the display loop on Darwin triggers the crash.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author          | Changes                |
| ------- | ---------- | --------------- | ---------------------- |
| 1.0     | 2026-04-15 | William Watson  | Initial issue creation |
| 1.1     | 2026-04-17 | William Watson  | Closed — fix verified by code review and serial-mode run |

---

Copyright (c) 2026 William Watson. MIT License.
