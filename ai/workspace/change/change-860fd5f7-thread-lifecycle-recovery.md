Created: 2026 October 07

# Change: Process-Restart Recovery and Bounded OBD Heartbeat Gaps

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-860fd5f7"
  title: "Remove in-process thread restart; make obd_protocol critical; treat dead started threads explicitly; call stop_func in stop_thread; replace dead registry entries; stop transport and OBD via stop_thread on setup re-entry; bound OBD heartbeat gaps (per-command deadline, timeout before write, heartbeat per command); OBD loop honours its stop signal; SimTransport reports disconnection"
  date: "2026-10-07"
  author: "William Watson"
  status: "implemented"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-860fd5f7"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-860fd5f7"
  description: "Resolves issue-860fd5f7 (audit-36b6ea95 A01/B02, B01, B05, B03)."

scope:
  summary: >
    Recovery becomes: warn, re-check, and for a critical thread shut
    down at critical_timeout so that systemd restarts the process. No
    thread is ever restarted in process. The OBD thread's heartbeat gaps
    are bounded so that it can be critical without false detections.
  affected_components:
    - name: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "OBDTransport.send_command"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "SimTransport"
      file_path: "src/gtach/comm/sim_transport.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_thread_lifecycle.py"
      change_type: "add"
    - name: "Existing watchdog tier test"
      file_path: "tests/test_watchdog_process_termination.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Watchdog thresholds (15/30/45 s) and the advisory tier for 'transport'."
    - "Overall shutdown deadline and stopping of touch, async and pairing threads (audit X02)."
    - "Setup-thread completion handling beyond the dead-thread rule (audit C01, Phase 2b)."
    - "Removal of worker_pool, _active_futures, ThreadInfo target capture and RecoveryStats hard-recovery fields (audit B06, B08; Phase 5 dead code)."
    - "OBD init response validation and back-off (audit A02, A03; Phase 2a)."
    - "GTachApplication.shutdown ordering."

rational:
  problem_statement: "See issue-860fd5f7."
  proposed_solution: >
    EDIT A — ThreadManager.
    (1) Delete _restart_thread and handle_thread_failure. Nothing else
    calls them once EDIT B removes hard recovery.
    (2) stop_thread: after setting STOPPING and releasing _state_lock,
    call thread_info.stop_func if set, in try/except with
    logger.error(..., exc_info=True), then join as today.
    (3) register_thread: if an entry exists whose status is RUNNING or
    STARTING and whose thread is alive, keep today's warning and return;
    otherwise replace the entry (debug log 'Replacing stale entry').

    EDIT B — WatchdogMonitor.
    (1) critical_threads = {'display', 'obd_protocol'}; update the
    comment to give the reason (no RPM without the OBD thread; restart
    is by process, change-860fd5f7).
    (2) Delete _attempt_hard_recovery. In _handle_recovery_timeout, the
    first attempt remains soft recovery; later attempts log one ERROR
    per attempt: 'Thread {name} unresponsive ({timeout:.1f}s); no
    in-process restart' (the existing 10 s spacing applies).
    (3) In _handle_critical_timeout, a non-critical thread logs ERROR and
    nothing else (no restart).
    (4) Dead-thread rule in _check_thread_health, phase 1 (under the
    lock, no blocking calls): for an entry with status RUNNING or
    STARTING whose thread has been started (thread.ident is not None)
    and is not alive, set status STOPPED and record a pending action.
    In phase 2: for a critical thread, log CRITICAL 'Critical thread
    {name} exited unexpectedly' and call _initiate_graceful_shutdown;
    otherwise log INFO 'Thread {name} exited; marked STOPPED'. Such an
    entry is not also evaluated for heartbeat age.
    (5) Update the class docstring's escalation list: no HARD_RECOVERY.

    EDIT C — OBDProtocol.
    (1) Inner loop condition:
    `while self.transport.is_connected() and not self.shutdown_event.is_set():`.
    (2) _send_command calls self.thread_manager.update_heartbeat('obd_protocol')
    before sending.

    EDIT D — OBDTransport.send_command.
    (1) Call self._set_timeout(handle, timeout) before self._write(...).
    (2) Add class constant _READ_DEADLINE_MARGIN_S = 1.0. Compute
    deadline = time.monotonic() + timeout + _READ_DEADLINE_MARGIN_S
    before the read loop. Before each read, remaining = deadline -
    time.monotonic(); if remaining <= 0, treat as a timeout; otherwise
    self._set_timeout(handle, min(timeout, remaining)).
    (3) Move the body of the existing `except self._TIMEOUT_ERRORS:`
    branch into a private method _record_timeout(command, timeout)
    returning None, and call it from both the except branch and the
    deadline path, so that both count towards the consecutive-timeout
    threshold and drop_link.

    EDIT E — SimTransport. is_connected returns self._connected read
    under self._lock; state returns CONNECTED if connected else
    DISCONNECTED. Update both docstrings.

    EDIT F — GTachApplication.
    (1) In _start_obd and _start_normal_mode, register 'transport' with
    stop_func=self._transport.disconnect.
    (2) In _re_enter_setup, replace the three-step block with:
    self._thread_manager.stop_thread('transport', timeout=2.0) then
    self._thread_manager.stop_thread('obd_protocol', timeout=2.0). The
    transport stop_func closes the socket first, releasing the OBD
    thread; OBDProtocol.stop is the registered stop_func of
    obd_protocol. Rewrite the comment block to describe this order and
    why STOPPING must precede the OBD stop (dead-critical-thread window).
  alternatives_considered:
    - option: "Option 2: make in-process restart safe."
      reason_rejected: >
        Decided against on 2026-10-07: more code, a new shutdown race,
        and still no remedy for a thread blocked where no timeout
        reaches.
    - option: "Keep obd_protocol non-critical."
      reason_rejected: "A stalled OBD thread would leave the tachometer without RPM indefinitely."
  benefits:
    - "No duplicate threads; a stalled critical thread is recovered by process restart within about 50 s."
    - "Simulation runs exit cleanly."
    - "Thread registry stays coherent across setup re-entry."
    - "OBD heartbeat gaps bounded at about 6 s against a 45 s threshold."
  risks:
    - risk: "A false OBD stall causes a process restart."
      mitigation: >
        EDITS C(2) and D bound every OBD step; the soak test in the
        issue's verification steps confirms the margin via error.log.
    - risk: "A dead critical thread during normal re-entry triggers shutdown."
      mitigation: "EDIT F routes the OBD stop through stop_thread, which marks STOPPING first."
    - risk: "A thread registered but not yet started is treated as dead."
      mitigation: "The dead-thread rule requires thread.ident is not None."
    - risk: "stop_func is now also called by ThreadManager.shutdown after the application already called it."
      mitigation: "OBDProtocol.stop and transport disconnect are idempotent; any exception is logged and the join proceeds."

technical_details:
  current_behavior: "Hard recovery restarts threads in process; stop_thread only joins; OBD gaps unbounded."
  proposed_behavior: "No in-process restart; stop_thread calls stop_func; bounded OBD gaps; critical OBD thread."
  implementation_approach: "Edits in six modules; one new test module; one test assertion updated."
  code_changes:
    - component: "ThreadManager"
      file: "src/gtach/core/thread.py"
      change_summary: "EDIT A"
      functions_affected:
        - "register_thread"
        - "stop_thread"
        - "handle_thread_failure (deleted)"
        - "_restart_thread (deleted)"
      classes_affected:
        - "ThreadManager"
    - component: "WatchdogMonitor"
      file: "src/gtach/core/watchdog.py"
      change_summary: "EDIT B"
      functions_affected:
        - "__init__"
        - "_check_thread_health"
        - "_handle_recovery_timeout"
        - "_handle_critical_timeout"
        - "_attempt_hard_recovery (deleted)"
      classes_affected:
        - "WatchdogMonitor"
    - component: "OBDProtocol"
      file: "src/gtach/comm/obd.py"
      change_summary: "EDIT C"
      functions_affected:
        - "_protocol_loop"
        - "_send_command"
      classes_affected:
        - "OBDProtocol"
    - component: "OBDTransport"
      file: "src/gtach/comm/transport.py"
      change_summary: "EDIT D"
      functions_affected:
        - "send_command"
        - "_record_timeout (new)"
      classes_affected:
        - "OBDTransport"
    - component: "SimTransport"
      file: "src/gtach/comm/sim_transport.py"
      change_summary: "EDIT E"
      functions_affected:
        - "is_connected"
        - "state"
      classes_affected:
        - "SimTransport"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: "EDIT F"
      functions_affected:
        - "_re_enter_setup"
        - "_start_obd"
        - "_start_normal_mode"
      classes_affected:
        - "GTachApplication"
  data_changes: []
  interface_changes:
    - interface: "ThreadManager.handle_thread_failure"
      change_type: "signature"
      details: "Removed. No callers remain after EDIT B."
      backward_compatible: "no"
    - interface: "WatchdogMonitor.critical_threads"
      change_type: "contract"
      details: "Now {'display', 'obd_protocol'}."
      backward_compatible: "no"

dependencies:
  internal:
    - component: "tests/test_watchdog_process_termination.py"
      impact: "TestAdvisoryTier.test_membership expects {'display'}; update to {'display', 'obd_protocol'}."
  external:
    - component: "systemd gtach.service"
      impact: "Restart=always, RestartSec=5 performs the recovery. Unchanged."
  required_changes:
    - change_ref: "change-b9ee7428"
      relationship: "blocked_by. Monotonic watchdog timing (implemented)."

testing_requirements:
  test_approach: "Unit tests in tests/test_thread_lifecycle.py; one updated assertion."
  test_cases:
    - scenario: "Stale critical 'obd_protocol' past critical_timeout."
      expected_result: "Shutdown callback called once."
    - scenario: "Stale non-critical thread past recovery and critical timeouts over several checks."
      expected_result: "ERROR logged; the ThreadInfo.thread object is unchanged; no shutdown."
    - scenario: "Critical thread started and finished, status RUNNING."
      expected_result: "Status STOPPED; shutdown callback called."
    - scenario: "Non-critical thread started and finished, status RUNNING."
      expected_result: "Status STOPPED; no shutdown."
    - scenario: "Critical thread registered but not started."
      expected_result: "No status change; no shutdown."
    - scenario: "stop_thread with a stop_func that records a non-blocking acquire of the manager's lock from a helper thread."
      expected_result: "stop_func called once, before the join, with the lock free."
    - scenario: "register_thread for a name whose existing thread is dead but status RUNNING."
      expected_result: "Entry replaced with the new thread."
    - scenario: "register_thread for a name whose existing thread is alive and RUNNING."
      expected_result: "Entry unchanged; warning logged."
    - scenario: "OBDProtocol on a connected SimTransport; stop()."
      expected_result: "The OBD thread exits within 2 s while the transport is still connected."
    - scenario: "SimTransport connect, disconnect."
      expected_result: "is_connected True then False; state CONNECTED then DISCONNECTED."
    - scenario: "send_command against a fake handle whose reads return b'SEARCHING' indefinitely, timeout 0.2 s."
      expected_result: "Returns None within timeout + margin + 0.5 s; the consecutive-timeout counter increased by one."
    - scenario: "send_command call order on a fake handle."
      expected_result: "_set_timeout is called before _write."
    - scenario: "OBDProtocol._send_command with a recording thread manager."
      expected_result: "update_heartbeat('obd_protocol') called once per command."
    - scenario: "GTachApplication._re_enter_setup with a recording thread manager and patched _start_setup_mode."
      expected_result: "stop_thread('transport', ...) then stop_thread('obd_protocol', ...), in that order; no direct _obd.stop() call."
  regression_scope:
    - "tests/test_watchdog_process_termination.py, tests/test_monotonic_watchdog_timing.py, tests/test_link_loss_recovery.py, tests/test_transport_heartbeat.py."
    - "Full tests/ suite."
  validation_criteria:
    - "grep for _restart_thread, handle_thread_failure and _attempt_hard_recovery in src/ returns nothing."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to F and tests."
      owner: "tactical"
    - step: "On the development host: gtach --transport simtcp; SIGTERM; exit within a few seconds."
      owner: "human"
    - step: "On the Pi: soak test with link losses; review error.log."
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
    - change_ref: "change-b9ee7428"
      relationship: "blocked_by"
    - change_ref: "change-9c2f41d8"
      relationship: "related. drop_link and timeout counting reused."
  related_issues:
    - issue_ref: "issue-860fd5f7"
      relationship: "resolves"

notes: >
  Decision record: Option 1 (no in-process restart) chosen by William
  Watson on 2026-10-07, with the three heartbeat-gap measures.

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-860fd5f7 iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in f5d58f524eec17374c9cda9cad449616e4f65ba9."

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
| 1.0 | 2026-10-07 | Initial change document. Process-restart recovery; bounded OBD heartbeat gaps; lifecycle fixes. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in f5d58f524eec17374c9cda9cad449616e4f65ba9. |

---

Copyright (c) 2026 William Watson. MIT License.
