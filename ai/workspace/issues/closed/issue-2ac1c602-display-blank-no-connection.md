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
  title: "Display goes blank after startup when no OBD connection is available, and does not recover: WatchdogMonitor's critical-thread shutdown path tears down the application without terminating the process, so systemd's Restart=always never engages"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "closed"
  severity: "critical"
  type: "defect"
  iteration: 3
  coupled_docs:
    change_ref: "change-2ac1c602"
    change_iteration: 2

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Reported 2026-08-12. William observed the display going blank after
    startup, correlated with absence of an active Emulator/Bluetooth OBD
    connection. Reproduced the same day with --debug enabled; start.log
    and debug.log for the reproduction were reviewed, and gtach.service
    status was confirmed independently on gtach.local.

affected_scope:
  components:
    - name: "GTachApplication.shutdown / run"
      file_path: "src/gtach/app.py"
    - name: "WatchdogMonitor._initiate_graceful_shutdown"
      file_path: "src/gtach/core/watchdog.py"
    - name: "RFCOMMTransport._open"
      file_path: "src/gtach/comm/rfcomm.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: >
    GTach running on gtach.local, started with --debug, no ELM327
    emulator or Bluetooth OBD adapter reachable.
  steps:
    - "Start GTach on gtach.local with --debug and no ELM327 emulator or Bluetooth OBD connection reachable."
    - "Observe the display through splash screen and into the DISCONNECTED normal-mode screen."
    - "Wait through one failed RFCOMM connect/retry cycle."
    - "Observe the display and touch interface stop responding entirely."
    - "Check `systemctl status gtach` on gtach.local: the original PID remains 'active (running)' with no restart, indefinitely."
  frequency: "always"
  reproducibility_conditions: >
    Reproduced under the stated precondition on the first attempt.
    Confirmed as causal, not merely correlated: the log timeline and the
    source of WatchdogMonitor's shutdown path together account for the
    full sequence from freeze to permanent unresponsiveness.
  preconditions: "No OBD transport reachable at connect time."
  test_data: >
    debug.log timeline (2026-08-12, gtach.local):

      07:38:57 - normal operation begins; DisplayRenderingEngine panning
        buffers at ~30 Hz; DISCONNECTED screen rendering (no paired/
        reachable device).
      07:39:07.293 - RFCOMMTransport ERROR: Failed to connect to
        DC:A6:32:54:AD:77 ch1: [Errno 112] Host is down.
      07:39:07.294 - RFCOMMTransport WARNING: retrying in 5.0 seconds.
      07:39:11.412 - LAST log activity from any thread before the gap
        (DisplayRenderingEngine "Panned to buffer 1"). This is ~1 s
        after the second connect() attempt would have begun following
        the 5 s retry delay.
      [51.7 s of complete silence — no output from any thread]
      07:40:03.090 - WatchdogMonitor ERROR: Thread display critical
        timeout (51.7s) - initiating emergency procedures.
      07:40:03.093-101 - WatchdogMonitor CRITICAL: Critical thread
        display failed recovery - initiating graceful shutdown; calls
        the shutdown callback (GTachApplication.shutdown).
      07:40:03.101-181 - shutdown() runs to completion: display, RFCOMM
        transport (forced disconnect), OBD protocol and ThreadManager
        are all torn down and logged as stopped/complete.
      07:40:03.182 - WatchdogMonitor ERROR: Thread obd_protocol
        critical timeout (51.7s) also fires, in the same check cycle.
      07:40:08.224 - the SECOND RFCOMM connect() attempt — the one that
        began the silent window — finally returns its own "Host is
        down" failure, 5 s AFTER the transport socket was force-closed
        during shutdown. That call had been in flight for the entire
        51.7 s gap.

    systemctl status gtach (2026-08-12, ~5 minutes after the above):

      Active: active (running) since Wed 2026-08-12 07:38:48 CEST;
        5min ago
      Main PID: 728 (gtach)

    The PID and start time are unchanged from the original process
    start at 07:38:48 — i.e. the SAME process that logged its own full
    shutdown at 07:40:03 is still reported "active (running)" five
    minutes later. The process did not exit, and systemd therefore
    never restarted it.
  error_output: >
    RFCOMMTransport ERROR "Failed to connect ... [Errno 112] Host is
    down" (twice, 61 s apart against a 5 s retry delay). WatchdogMonitor
    ERROR/CRITICAL for both 'display' and 'obd_protocol' critical
    timeouts, 51.7 s. No Python exception or traceback anywhere in
    either log; no faulthandler stack dump appears despite --debug being
    active, because nothing was left running long enough after 07:40:03
    to hit the next 15 s dump interval — see analysis.

behavior:
  expected: >
    Either the display remains responsive regardless of OBD connection
    availability, or, if a genuine hang occurs, the application recovers
    by actually exiting so systemd (Restart=always) relaunches it.
  actual: >
    The display and touch interface freeze completely for ~52 s, at
    which point WatchdogMonitor detects the critical-thread timeout and
    runs the application's shutdown sequence. That sequence tears down
    every worker component (display, transport, OBD, thread manager)
    but does not end the process: GTachApplication.run()'s main loop
    (`while not self._stop_event.is_set(): self._stop_event.wait(...)`)
    is never told to stop, because WatchdogMonitor's shutdown_callback is
    wired directly to GTachApplication.shutdown, which never sets
    _stop_event. The process is therefore left running indefinitely with
    no display thread, no OBD thread and no transport — permanently
    inert. Because the process never exits, systemd's Restart=always
    (bin/gtach.service) never triggers, and there is no self-recovery
    from this state.
  impact: >
    A single failed OBD connection attempt permanently blanks the
    display and disables all input, with no automatic recovery. Only a
    manual `systemctl restart gtach` or a reboot restores function.
    Severity raised from high to critical on this basis: the prior
    assessment (issue iteration 1) treated this as an intermittent
    freeze that a working recovery path would eventually clear; the
    confirmed behaviour is a permanent hang requiring operator
    intervention, in a vehicle, with no indication to the driver beyond
    a dead screen.
  workaround: >
    Manually restart the service (`systemctl restart gtach`) or power
    cycle. Ensuring an ELM327 emulator or Bluetooth OBD connection is
    reachable before startup avoids triggering the failed connect that
    starts the sequence, but does not address the underlying defect.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    ITERATION 3 PREAMBLE. Three corrections to the iteration 2 analysis
    below, and one new defect found in the iteration 2 remedy. The
    original iteration 2 text is retained unaltered beneath this
    preamble so the reasoning that was superseded remains legible.

    CORRECTION 1 — the stall is process-wide, and this is CONFIRMED,
    not hypothesised. WatchdogMonitor ran with warning_timeout=15.0,
    recovery_timeout=30.0, critical_timeout=45.0, check_interval=5.0.
    A 51.7 s stall of the display thread should have produced warnings
    from ~07:39:26 and a soft-recovery attempt from ~07:39:41, both
    before the critical timeout. The watchdog's own closing statistics
    in debug.log read "warnings=0, soft_recovery=0/0, hard_recovery=0/0,
    shutdowns=1". No intermediate escalation occurred at all. The
    WatchdogMonitor thread was therefore itself stalled across the same
    window and resumed with a single check reading 51.7 s. Three
    independent Python threads — display, obd_protocol and
    WatchdogMonitor — stopped and resumed together.

    CORRECTION 2 — the stall is NOT accounted for by
    RFCOMMTransport._open()'s connect(), and the GIL mechanism proposed
    in iteration 2 is withdrawn. The stall window is 07:39:11.412 to
    07:40:03.090 (51.68 s). The second connect() began at approximately
    07:39:12.29 (07:39:07.294 plus the 5.0 s retry delay) and returned
    at 07:40:08.224, a duration of 55.9 s. The stall started ~0.9 s
    BEFORE connect() was entered and ended ~5.1 s BEFORE it returned.
    The two windows fail to coincide at both ends. A GIL-holding
    connect() would produce coincident windows. CPython's socket
    connect releases the GIL for the duration of the syscall, which is
    consistent with this observation. The cause of the stall is
    therefore NOT established.

    CORRECTION 3 — faulthandler dumps were produced during the stall
    and were not lost to timing. app.py armed
    faulthandler.dump_traceback_later(15, repeat=True, file=sys.stderr)
    under --debug. faulthandler's repeat timer runs in a C thread and
    does not take the GIL to schedule itself, so roughly three dumps
    fell inside the 51.7 s window. They were written to stderr. The
    source comment asserted that "stderr is already captured by the run
    command's tee into the debug log", which does not hold for a
    systemd-launched run, where bin/gtach.service directs stderr to the
    journal. The dumps existed; they were simply not co-located with
    the logs under review. This is what motivated the stacks.log
    redirect in change-2ac1c602.

    NEW DEFECT, CONFIRMED — the stacks.log redirect is gated on the
    wrong signal and produced no file. Reported 2026-08-12 following
    the 09:11 verification run: /opt/gtach/stacks.log was never
    created. main.py:161 calls setup_logging(args.debug), and the
    faulthandler arming block added by change-2ac1c602 is guarded by
    `if debug:`. bin/gtach.service's ExecStart is
    `/opt/gtach/venv/bin/gtach` with NO --debug argument, so args.debug
    is False on every service-launched run and faulthandler is never
    armed. Debug logging in the field is enabled at RUNTIME through the
    OPTIONS screen toggle, which calls
    GTachApplication.toggle_debug_logging; that method raises
    _debug_handler's level and does nothing else. Confirmed by the
    09:11 logs: debug.log exists and begins at 09:11:28.240 with
    "Debug logging enabled" — the runtime toggle — while stacks.log
    does not exist. The delivered edit therefore cannot achieve its
    stated purpose under the deployed configuration.

    ITERATION 2 ANALYSIS, RETAINED. Two findings, one confirmed
    directly from source, one a well-supported but not yet
    independently verified hypothesis:

    CONFIRMED — the recovery path does not terminate the process.
    WatchdogMonitor is constructed in GTachApplication.__init__ with
    shutdown_callback=self.shutdown (app.py). When a critical thread
    timeout fires, _initiate_graceful_shutdown calls that callback
    directly. GTachApplication.shutdown() stops the watchdog, display,
    transport, OBD protocol and thread manager, but contains no call
    that sets self._stop_event, calls sys.exit(), or otherwise ends the
    interpreter. GTachApplication.run()'s only exit condition is
    `self._stop_event.is_set()`, checked in a 0.5 s poll loop — an event
    that only _request_restart() and _signal_handler() ever set. Neither
    is invoked by this path. The main thread therefore continues polling
    a never-set event forever, in a process with every worker component
    already torn down. This is confirmed by the systemctl evidence: PID
    728, started 07:38:48, was still "active (running)" more than five
    minutes after its own shutdown() logged full completion at
    07:40:03 — the same process, never exited, never restarted.

    HYPOTHESIS, not yet independently confirmed — what stalls 'display'
    and 'obd_protocol' in the first place. RFCOMMTransport._open()
    (rfcomm.py) sets sock.settimeout(10) before connect(), but the
    observed stall was ~52 s, not ~10 s, and the connect() call was
    still unresolved when forcibly closed during shutdown, finally
    erroring 5 s later. This is consistent with a known limitation of
    AF_BLUETOOTH/BTPROTO_RFCOMM sockets on Linux, where the HCI-level
    connection setup can block synchronously well past any
    application-level timeout, because Python's socket timeout
    mechanism relies on non-blocking connect() + select(), which RFCOMM
    does not reliably support. That would explain a stalled transport
    thread on its own, but 'display' and 'obd_protocol' — whose own
    loops are cheap, non-blocking, and call no connect() — also stopped
    heartbeating for the identical 51.7 s window. is_connected()'s lock
    is held only briefly around state changes, not across _open(), so
    lock contention does not explain this. The best-supported
    explanation, but not yet confirmed against the running process, is
    that the blocking connect() syscall for this socket family does not
    release the GIL for its duration on this platform/kernel
    combination, starving every other Python thread in the process
    simultaneously. Confirming this requires on-target instrumentation
    (py-spy or strace against the 'transport' thread during a
    reproduction) rather than log inference alone.

    A secondary, related observation: bin/gtach.service's
    critical_threads set in WatchdogMonitor includes 'transport', but
    app.py starts the RFCOMM reconnect loop as a bare threading.Thread
    (name='transport') that is never passed to
    ThreadManager.register_thread. WatchdogMonitor iterates only
    thread_manager.threads, so 'transport' is invisible to it — it is
    named as critical but never actually monitored. This did not
    prevent detection here only because 'display' and 'obd_protocol'
    happened to stall in the same window; a stall isolated to the
    transport thread alone would not be caught by the watchdog at all.
  technical_notes: >
    The two findings compound rather than substitute for each other.
    Even if the RFCOMM timeout is fixed and no thread ever stalls for
    50+ s again, the shutdown-callback defect is a latent hazard: ANY
    future critical-timeout event, from any cause, would produce the
    same permanent-hang outcome, because the callback wiring itself does
    not terminate the process. Both should be corrected. The systemd
    unit (bin/gtach.service, Restart=always, RestartSec=5,
    StartLimitIntervalSec=60, StartLimitBurst=3) is fine as configured
    and needs no change — it simply never gets the process exit it is
    waiting for.
  related_issues:
    - issue_ref: ""
      relationship: >
        Related open item in ai/task.md (not yet raised as its own T03):
        faulthandler output targets sys.stderr rather than an app-owned
        log file. Not a factor in this reproduction — the freeze ended
        via watchdog action before the next scheduled 15 s
        faulthandler dump could occur — but remains a gap for any future
        hang that runs longer.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    ITERATION 3. Item 1 below is IMPLEMENTED under change-2ac1c602
    iteration 1 and prompt-2ac1c602 iteration 1, and is deployed to
    gtach.local. It is NOT yet verified: the 51.7 s stall did not
    recur on the 2026-08-12 09:11 run, so the termination path was
    never exercised. On that run connect() failures returned in ~5.1 s
    each on a steady ~10.1 s cycle, the display held 30.0 FPS, and no
    WatchdogMonitor line was emitted at all. The transport thread is
    now registered, confirmed by start.log 09:11:22 "Registered thread:
    transport".

    Item 3, new in this iteration, is required before the stall can be
    observed at all: gate the faulthandler arming on the signal that
    actually turns debug on in the field, not on the startup --debug
    flag that bin/gtach.service never passes. Expose arm and disarm
    helpers in main.py alongside the existing log-file ownership, and
    call them from GTachApplication.toggle_debug_logging in addition to
    the startup path. Adding --debug to the service unit is rejected:
    it would make debug logging permanent in production and write a
    full all-thread stack dump every 15 s for the life of every run.

    Item 2 remains open and its stated mechanism is withdrawn per
    CORRECTION 2. It cannot be progressed until item 3 produces stack
    evidence from inside a stall window.

    ITERATION 2 APPROACH, RETAINED. Two corrections, in priority order:

    1. (Primary, confirmed defect) Wire WatchdogMonitor's
    shutdown_callback so a critical-thread timeout actually ends the
    process, not merely tears down its components. The minimal
    correction is for the callback to set self._stop_event (as
    _request_restart already does) in addition to, or instead of,
    calling shutdown() directly — so GTachApplication.run()'s loop exits
    and the interpreter terminates, allowing systemd's Restart=always to
    relaunch it. Needs a decision on ordering: whether _stop_event
    should be set before or after component teardown, and whether
    shutdown() should remain idempotent-safe if invoked twice (once via
    this path, once via run()'s finally block).

    2. (Secondary, hypothesis pending confirmation) Investigate why
    RFCOMMTransport._open()'s 10 s socket timeout does not bound the
    observed ~52 s stall, and confirm on-target whether other threads
    are genuinely GIL-starved during that window. If confirmed, evaluate
    whether the connect attempt should run in a way that can be bounded
    independently of the socket's own timeout (e.g. a subprocess or a
    hard join-timeout with the parent thread abandoned rather than
    waited on), since a kernel-level block in a thread cannot be
    interrupted from Python once entered.

    Item 2 is not necessarily required to resolve the reported symptom:
    correcting item 1 alone converts a permanent hang into a
    self-recovering ~52 s-per-cycle freeze-and-restart, which is closer
    to (though not identical to) the originally reported "watchdog that
    restarts the app" request. Whether that residual ~52 s freeze on
    every failed reconnect attempt is acceptable, or whether item 2 must
    also be corrected, is a product decision to make once item 1 is in
    place.
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
    A watchdog's terminal recovery action should be verified to actually
    end the process it is meant to recover, not merely assumed to from
    the fact that a shutdown() method exists and logs completion.
  process_improvements: >
    Any future watchdog-style component should have an explicit test
    exercising its most severe recovery path end-to-end — including
    confirmation that the process actually exits — not just that
    cleanup methods are called without error.

verification_enhanced:
  verification_steps:
    - "Confirm via source review that GTachApplication.shutdown() contains no path that sets _stop_event or exits the interpreter. [DONE — confirmed above.]"
    - "Confirm via systemctl status that a watchdog-triggered shutdown leaves the original PID running rather than restarting. [DONE — PID 728, no restart after 5+ minutes.]"
    - "After the primary fix, reproduce the same no-connection scenario and confirm systemctl shows a new PID / restart count increment following the critical timeout."
    - "Instrument the 'transport' thread's connect() call (py-spy dump or strace) during a live reproduction to confirm or rule out the GIL-starvation hypothesis for items affecting 'display' and 'obd_protocol'."
    - "Confirm whether register_thread('transport', ...) should be added so WatchdogMonitor's critical_threads entry for 'transport' is actually monitored, independent of whether other threads also stall."
  verification_results: >
    First two steps complete, as recorded in test_data and root_cause
    above. Remaining steps require the primary fix to exist (for
    restart confirmation) or a further live reproduction with
    instrumentation attached (for the GIL hypothesis and the untracked
    'transport' thread).

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  issue-49b21ace (framebuffer vsync/page-flip tearing) was closed
  2026-08-07 and is unrelated to this issue. This is iteration 2 of
  issue-2ac1c602: iteration 1 recorded the user report with no log
  evidence available (debug mode had not been used); this iteration
  incorporates the first successful --debug reproduction and the
  systemctl confirmation that the process does not self-recover.

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
  - version: "2.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Iteration 1 -> 2. Incorporated first successful --debug reproduction: full debug.log timeline recorded in reproduction.test_data."
      - "Confirmed root cause (not hypothesis): WatchdogMonitor's shutdown_callback (GTachApplication.shutdown) tears down all worker components but never sets _stop_event or otherwise ends the process, so GTachApplication.run()'s main loop never exits and systemd's Restart=always never engages. Confirmed independently via systemctl status showing the original PID still active, unrestarted, more than five minutes after its own logged shutdown completion."
      - "Recorded as a separate, unconfirmed hypothesis: RFCOMMTransport._open()'s 10s socket timeout does not appear to bound the observed ~52s connect() stall, and 'display'/'obd_protocol' losing heartbeats in the same window is provisionally attributed to GIL starvation during that blocking call, pending on-target instrumentation (py-spy/strace) to confirm."
      - "Noted a related but distinct defect: the 'transport' thread is never registered with ThreadManager, so WatchdogMonitor's own critical_threads listing of 'transport' is not actually monitored."
      - "Severity raised high -> critical: the confirmed behaviour is a permanent, non-recovering hang, not an intermittent freeze that self-clears."
      - "Status open -> investigating. Resolution approach revised: primary fix is correcting WatchdogMonitor's shutdown wiring so the process actually exits; RFCOMM connect-timeout investigation is secondary and not required to address the reported symptom."
  - version: "3.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Iteration 2 -> 3. Coupled to change-2ac1c602 iteration 2."
      - "CORRECTION 1: the process-wide nature of the stall is upgraded from hypothesis to confirmed. The watchdog's own closing statistics record warnings=0 and soft_recovery=0/0 against a 51.7s stall and a 15s warning threshold, which is only possible if the WatchdogMonitor thread was itself stalled across the same window."
      - "CORRECTION 2: the 'connect() does not release the GIL' mechanism is withdrawn. The stall window (07:39:11.412-07:40:03.090) fails to coincide with the connect() call (07:39:12.29-07:40:08.224) at both ends. The cause of the stall is not established."
      - "CORRECTION 3: faulthandler dumps were produced inside the stall window, its repeat timer being a C thread unaffected by Python-level stalls, but were written to stderr, which under systemd is the journal rather than the app-owned log set."
      - "NEW DEFECT: the stacks.log redirect delivered by change-2ac1c602 iteration 1 produced no file. It is gated on setup_logging's debug argument, which derives from --debug; bin/gtach.service passes no such flag, and field debug is enabled at runtime through the OPTIONS toggle, which does not arm faulthandler."
      - "Recorded that item 1 of the resolution approach is implemented and deployed but NOT verified: the stall did not recur on the 2026-08-12 09:11 run, so the termination path was never exercised."
      - "Recorded the 09:11 run's healthy characteristics: connect() failures returning in ~5.1s on a ~10.1s cycle, 30.0 FPS sustained, no WatchdogMonitor output, transport thread registered."

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
| 2.0 | 2026-08-12 | Iteration 1 -> 2. Reproduced with --debug; confirmed root cause is WatchdogMonitor's shutdown_callback not terminating the process (verified via source review and systemctl status showing no restart). RFCOMM connect-timeout stall recorded as a related, unconfirmed hypothesis. Severity raised to critical; status changed to investigating. |
| 3.0 | 2026-08-12 | Iteration 2 -> 3. Three corrections to the iteration 2 analysis: the process-wide stall is confirmed rather than hypothesised; the connect()-holds-GIL mechanism is withdrawn as contradicted by the timeline; faulthandler dumps were produced but written to the journal. New defect recorded: the stacks.log redirect delivered under change-2ac1c602 iteration 1 is gated on the startup --debug flag, which bin/gtach.service never passes, so no file was created. Primary fix implemented and deployed but not verified — the stall did not recur. |

---

Copyright (c) 2026 William Watson. MIT License.
