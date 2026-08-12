Created: 2026 August 12

# Issue: Display Blanks After Startup When No OBD Connection Is Present

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-2ac1c602"
  title: "Display goes blank after startup, reported to correlate with absence of an active Emulator/Bluetooth OBD connection"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Reported 2026-08-12. William observes the display going blank after
    startup, and notes this appears to occur when no Emulator or Bluetooth
    OBD connection is running. start.log for the affected run (pulled via
    bin/pull_logs.sh) was reviewed and shows a clean startup sequence
    through "Startup complete — start.log closed", with no error or
    warning entries.

affected_scope:
  components:
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: >
    GTach running on gtach.local. Reported condition: no ELM327 emulator
    or Bluetooth OBD adapter connection active at or after startup.
  steps:
    - "Start GTach on gtach.local with no ELM327 emulator or Bluetooth OBD connection available."
    - "Observe the display through splash screen and into normal mode."
    - "Display reportedly goes blank at some point after startup."
  frequency: "intermittent"
  reproducibility_conditions: >
    Reported to correlate with absence of an active OBD connection at
    startup. Not yet confirmed as causal; no reproduction has been run
    with diagnostic instrumentation active.
  preconditions: "Unconfirmed. Requires reproduction with --debug to isolate."
  test_data: ""
  error_output: >
    None captured. start.log (pulled 2026-08-12, covering a 2026-08-07
    run) ends cleanly at "Startup complete — start.log closed" with no
    exception, warning, or watchdog escalation logged. debug.log is 0
    bytes, confirming the application was not started with --debug for
    that run, so no faulthandler thread-stack dumps exist to correlate
    against the blanking.

behavior:
  expected: >
    The display remains active in normal operating mode independent of
    whether an OBD transport connection is currently available.
  actual: >
    The display reportedly goes blank after startup under the stated
    condition. No corroborating log evidence has yet been captured.
  impact: >
    Loss of the primary display function during use, with no visible
    fault indication to the operator.
  workaround: >
    Reported workaround: ensure an ELM327 emulator or Bluetooth OBD
    connection is active before/at startup.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    Not yet determined. No log evidence is available to confirm a causal
    link between OBD connection absence and display blanking:
    start.log is written only during the startup phase and is closed
    deliberately once startup completes (per its own log line), so it
    cannot capture a post-startup fault. debug.log was empty for the
    reviewed run, indicating --debug was not used, so the periodic
    faulthandler stack dump at app.py:43-45 was never active. The
    reported correlation with connection absence is a hypothesis, not a
    confirmed cause.
  technical_notes: >
    Two recovery mechanisms already exist and are relevant to scoping
    this issue before any new watchdog is designed:

    1. In-process: WatchdogMonitor (src/gtach/core/watchdog.py) monitors
    thread heartbeats via ThreadManager and escalates through WARNING →
    SOFT_RECOVERY → HARD_RECOVERY → GRACEFUL_SHUTDOWN → EMERGENCY_SHUTDOWN.
    'display', 'transport', and 'main' are registered as critical
    threads; critical-thread recovery failure is designed to trigger
    _initiate_graceful_shutdown, which calls the application shutdown
    callback or falls back to os._exit(1).

    2. Process-level: bin/gtach.service already sets Restart=always,
    RestartSec=5, StartLimitIntervalSec=60, StartLimitBurst=3. If the
    process exits (including via WatchdogMonitor's emergency path),
    systemd already restarts it.

    These two mechanisms only combine correctly if a hang actually
    causes the process to exit. If the display thread hangs without the
    watchdog's critical-timeout path being reached — or reaches it but
    the shutdown callback itself blocks — the process remains alive and
    systemd's Restart=always never triggers, since it only acts on
    process exit. Whether this is what is happening here is unconfirmed
    and is the first thing a reproduction with --debug should establish.
  related_issues:
    - issue_ref: ""
      relationship: >
        No formal issue reference yet. Related open item recorded in
        ai/task.md (untracked as T03): faulthandler output targets
        sys.stderr, which systemd routes to the journal rather than
        debug.log, under normal (non-debug) invocation. That item is a
        contributing factor to why no diagnostic trace exists for this
        report.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Investigation, not yet a fix. Proposed first steps: (1) reproduce
    with gtach started via --debug so faulthandler's periodic
    thread-stack dump is active and captured, per the run command's
    existing tee into debug.log; (2) reproduce specifically without an
    ELM327 emulator/Bluetooth connection present to test the reported
    correlation; (3) inspect WatchdogMonitor's thread_health state
    (get_thread_health_status) during the hang to determine whether it
    is detecting the condition and whether/how far it escalates; (4) on
    that basis, determine whether a new watchdog mechanism is needed at
    all, or whether the fix is to the existing escalation path (e.g. a
    shutdown callback that can itself block, or a critical-thread set
    that does not cover the thread actually hanging).
  change_ref: ""
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
    To be determined pending root cause.
  process_improvements: >
    Runtime state should be captured continuously, not only during the
    startup phase, so intermittent post-startup faults are diagnosable
    from a single log pull rather than requiring a live debug session.

verification_enhanced:
  verification_steps:
    - "Start GTach on gtach.local with --debug and no OBD connection present; reproduce the blanking."
    - "Pull logs and confirm faulthandler thread-stack dumps are present in debug.log at the time of blanking."
    - "Identify which thread(s), if any, are parked/blocked at that point."
    - "Query WatchdogMonitor.get_thread_health_status() behaviour (via added logging or a debug hook) to confirm whether the watchdog detected the condition and which recovery level it reached."
    - "Confirm whether the process exited (systemd Restart=always would show a new PID) or remained alive and unresponsive."
  verification_results: >
    Not started. All steps require on-target reproduction with --debug.

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  issue-49b21ace (framebuffer vsync/page-flip tearing) was closed
  2026-08-07 on confirmation that GTach functions correctly on
  gtach.local. This is a separate, newly reported symptom (blanking, not
  tearing) and is not a reopening of that issue. Related task.md item
  (faulthandler/sys.stderr capture gap) has not yet been raised as its
  own T03; it is referenced here rather than duplicated because it
  directly affects this issue's diagnosability.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial issue document from user report of display blanking after startup, reported to correlate with absence of an active OBD connection."

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
| 1.0 | 2026-08-12 | Initial issue document from user report. Root cause not yet determined; no log evidence available since the run was not started with --debug. |

---

Copyright (c) 2026 William Watson. MIT License.
