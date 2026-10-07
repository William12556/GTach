Created: 2026 October 07

# Issue: Thread Lifecycle and Watchdog Recovery Defects

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-860fd5f7"
  title: "In-process thread restart cannot recover a stalled thread and can run two copies; the OBD loop ignores its stop signal while connected; stop_thread never calls stop_func; dead registry entries block re-registration"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-860fd5f7"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 findings A01/B02 and B01 (high), B05 and
    B03 (medium). Resolution approach (no in-process restart; stalled
    critical threads end in a process restart; obd_protocol made
    critical; OBD heartbeat gaps bounded) decided by William Watson on
    2026-10-07.

affected_scope:
  components:
    - name: "ThreadManager.register_thread / stop_thread / handle_thread_failure / _restart_thread"
      file_path: "src/gtach/core/thread.py"
    - name: "WatchdogMonitor (critical_threads, recovery escalation, health check)"
      file_path: "src/gtach/core/watchdog.py"
    - name: "OBDProtocol._protocol_loop / _send_command"
      file_path: "src/gtach/comm/obd.py"
    - name: "OBDTransport.send_command"
      file_path: "src/gtach/comm/transport.py"
    - name: "SimTransport.is_connected / state"
      file_path: "src/gtach/comm/sim_transport.py"
    - name: "GTachApplication._re_enter_setup / _start_obd / _start_normal_mode"
      file_path: "src/gtach/app.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "Development host or Pi."
  steps:
    - "A01: run `gtach --transport simtcp` and send SIGTERM; the process does not exit until killed."
    - "B01: stall the OBD thread for more than 30 s (test double); the watchdog restarts it, the new thread exits immediately, and RPM is lost for the life of the process."
  frequency: "always"
  reproducibility_conditions: "Deterministic from source."
  test_data: >
    obd.py:80 inner loop `while self.transport.is_connected():` never
    tests shutdown_event; SimTransport.is_connected returns True
    unconditionally (sim_transport.py:62-68); the OBD thread is
    non-daemon (obd.py:48-51).

    thread.py _restart_thread calls stop_func while holding _state_lock;
    OBDProtocol.stop sets shutdown_event, which is never cleared, so the
    restarted _protocol_loop exits at once; 'display' has no stop_func,
    so a second display loop can start while the stalled one is alive.
    Python threads cannot be terminated, so no in-process restart of a
    stalled thread is safe.

    thread.py stop_thread and shutdown join only; they never call the
    registered stop_func.

    app.py _re_enter_setup stops only obd_protocol; the 'transport'
    entry stays RUNNING with a dead thread, and register_thread
    (thread.py:120-125) silently refuses the new 'transport' thread.

    transport.py send_command reads until '>' with no overall deadline:
    each read resets the per-read timeout, so a peer that keeps sending
    bytes without '>' keeps the OBD thread inside one call indefinitely.
    The per-command timeout is applied after the write.
  error_output: "None specific."

behavior:
  expected: >
    Threads stop when asked; a stalled critical thread leads to a clean
    process restart; normal operation never produces a heartbeat gap
    near the watchdog thresholds.
  actual: "As in test_data. All confirmed in source."
  impact: >
    Exit hangs with simulation transports; loss of RPM after a watchdog
    restart; possible duplicate display loops; stale thread registry
    after setup re-entry.
  workaround: "Restart the service."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    The recovery design assumes a stalled thread can be replaced in
    process. In Python it cannot be stopped, so replacement either fails
    or duplicates it. Process restart under systemd (Restart=always,
    RestartSec=5) is the only reliable recovery.
  technical_notes: >
    Making obd_protocol critical requires that its heartbeat gaps are
    bounded well below critical_timeout (45 s). Three measures bound
    them: an overall per-command deadline in send_command, the timeout
    set before the write, and a heartbeat before every OBD command. The
    longest normal gap is then one ATZ command, about 6 s.

    Loss of data (adapter off, vehicle off, link down) is not a stall:
    the OBD loop keeps iterating and heartbeating, so it cannot trigger
    a restart.

    Trap: OBDProtocol registers its thread in __init__ and starts it
    later. A 'dead thread' check must therefore only consider threads
    that have been started (Thread.ident is not None), or the watchdog
    would treat a not-yet-started critical thread as dead.

    Trap: on setup re-entry, stopping the OBD thread directly and then
    marking it STOPPED leaves a window in which the watchdog sees a dead
    critical thread with status RUNNING and shuts the process down. The
    stop must go through ThreadManager.stop_thread, which marks STOPPING
    before calling stop_func.
  related_issues:
    - issue_ref: "issue-b9ee7428"
      relationship: "related. Monotonic watchdog timing."
    - issue_ref: "issue-9c2f41d8"
      relationship: "related. Established drop_link and the timeout counter reused here."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-860fd5f7."
  change_ref: "change-860fd5f7"
  resolved_date: ""
  resolved_by: ""
  fix_description: "In-process thread restart is removed in favour of process restart, obd_protocol is critical, exited started threads are marked STOPPED, stop_thread calls stop_func, dead entries are replaced, the OBD loop honours its stop signal with a heartbeat per command and a monotonic per-command deadline, SimTransport reports its real state, and setup re-entry stops transport then obd_protocol through stop_thread (commit f5d58f524eec17374c9cda9cad449616e4f65ba9)."

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Every operation on a monitored thread is time-bounded with a heartbeat between bounded steps."
  process_improvements: "Soak test with error.log review after watchdog-related changes."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-860fd5f7."
    - "After the fix: `gtach --transport simtcp`, SIGTERM, exit within a few seconds."
    - "After the fix: soak test on the Pi of several hours with link losses, adapter power cycles and emulator restarts; error.log contains no 'appears unresponsive' warning for obd_protocol."
  verification_results: "First step complete."

traceability:
  design_refs: []
  change_refs:
    - "change-860fd5f7"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 A01/B02, B01, B05, B03."

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
      - "Initial issue document from audit-36b6ea95 A01/B02, B01, B05, B03; Option 1 resolution decided."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in f5d58f524eec17374c9cda9cad449616e4f65ba9; awaiting on-device verification."

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
| 1.0 | 2026-10-07 | Initial issue document. Unsafe in-process restart, OBD stop signal, stop_func, dead registry entries; Option 1 resolution. |
| 1.1 | 2026-10-07 | Fix implemented in f5d58f524eec17374c9cda9cad449616e4f65ba9; awaiting on-device verification. |

---

Copyright (c) 2026 William Watson. MIT License.
