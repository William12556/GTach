Created: 2026 August 12

# Change: Watchdog Critical-Thread Recovery Must Terminate the Process

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-2ac1c602"
  title: "Watchdog critical-thread recovery terminates the process so systemd Restart=always engages; transport thread registered and monitored advisory-only; faulthandler stack dumps written to an app-owned log"
  date: "2026-08-12"
  author: "William Watson"
  status: "implemented"
  priority: "critical"
  iteration: 2
  coupled_docs:
    issue_ref: "issue-2ac1c602"
    issue_iteration: 3

source:
  type: "issue"
  reference: "issue-2ac1c602"
  description: >
    Resolves issue-2ac1c602 iteration 2. Authored after independent
    re-verification of the issue's findings against
    src/gtach/app.py, src/gtach/core/watchdog.py,
    src/gtach/core/thread.py, src/gtach/comm/transport.py,
    src/gtach/comm/rfcomm.py, src/gtach/main.py, bin/gtach.service and
    the 2026-08-12 logs/start.log and logs/debug.log.

    The re-verification confirmed the issue's primary finding, confirmed
    the untracked-transport-thread observation, and corrected two
    subsidiary claims. Both corrections are recorded in
    rational.problem_statement and notes; issue-2ac1c602 should be
    advanced to iteration 3 to absorb them.

scope:
  iteration_2_addendum: >
    Iteration 1 is implemented, committed and deployed to gtach.local.
    Iteration 2 adds one further edit, EDIT F, correcting a defect in
    iteration 1's own delivery: the faulthandler arming added by EDIT A
    is gated on setup_logging's debug argument, which derives from the
    --debug command-line flag. bin/gtach.service's ExecStart is
    `/opt/gtach/venv/bin/gtach` with no such flag, so args.debug is
    False on every service-launched run and faulthandler is never
    armed. /opt/gtach/stacks.log was consequently never created on the
    2026-08-12 09:11 verification run.

    Debug logging in the field is enabled at RUNTIME through the
    OPTIONS screen toggle, which calls
    GTachApplication.toggle_debug_logging (app.py:208-238). That method
    raises _debug_handler's level and does nothing else. The arming
    must follow the same signal.

    EDIT F: expose arm and disarm helpers in main.py, where log-file
    ownership already lives, and call them from toggle_debug_logging in
    addition to the existing startup path. No other part of iteration 1
    is altered.

  summary: >
    Three edits across four files. (1) Give WatchdogMonitor a shutdown
    callback that ends the process rather than one that only tears down
    components, with a hard backstop if orderly exit does not complete.
    (2) Register the 'transport' thread with ThreadManager and give
    WatchdogMonitor an advisory-only monitoring tier so a legitimately
    long blocking connect() is observed without triggering recovery or
    shutdown. (3) Direct faulthandler's periodic stack dumps to an
    app-owned log file so the cause of a process-wide stall is
    recoverable from the same location as start.log and debug.log.
  affected_components:
    - name: "GTachApplication.__init__ / _watchdog_shutdown / _force_exit"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "GTachApplication._initialize_normal_mode_components (transport thread start)"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "WatchdogMonitor.critical_threads / advisory_threads / _check_thread_health"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
    - name: "OBDTransport.reconnect_indefinitely"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "setup_logging (faulthandler stack-dump target)"
      file_path: "src/gtach/main.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "bin/gtach.service. Restart=always, RestartSec=5, StartLimitIntervalSec=60 and StartLimitBurst=3 are correct as configured; the unit never receives the process exit it is waiting for. No unit change is required or made."
    - "Determining the cause of the process-wide ~52 s thread stall. This change makes that cause observable (edit 3) but does not attempt to fix it. Any fix follows from a subsequent reproduction under edit 3."
    - "Bounding or restructuring RFCOMMTransport._open()'s blocking connect(). Deferred pending the stall cause."
    - "Registering the main thread with ThreadManager. 'main' is named in WatchdogMonitor.critical_threads but has never been registered; this change removes the misleading entry but does not add main-thread heartbeating."
    - "Process exit code signalling. The orderly watchdog exit path returns the normal exit code; only the backstop exits non-zero. systemd Restart=always restarts on either, so exit-code differentiation is not required to resolve the issue."
    - "faulthandler output for non-debug runs. Stack dumps remain gated on --debug."

rational:
  problem_statement: >
    CONFIRMED, PRIMARY. WatchdogMonitor is constructed in
    GTachApplication.__init__ (app.py:51-58) with
    shutdown_callback=self.shutdown. On a critical-thread timeout,
    WatchdogMonitor._handle_critical_timeout calls
    _initiate_graceful_shutdown, which calls that callback
    (watchdog.py:346-352). GTachApplication.shutdown (app.py:358-388)
    stops the watchdog, setup manager, display, transport, OBD protocol
    and thread manager. It sets nothing that ends the process.
    GTachApplication.run (app.py:345-356) exits its loop only on
    self._stop_event, which only _request_restart (app.py:191) and
    _signal_handler (app.py:393) ever set. Neither is on this path. The
    main thread therefore polls a never-set event indefinitely in a
    process with every worker torn down. Confirmed independently by the
    reported systemctl output: PID 728, started 07:38:48, still
    "active (running)" more than five minutes after its own shutdown
    logged completion at 07:40:03.

    CONFIRMED, SECONDARY. app.py:338 starts reconnect_indefinitely as a
    bare threading.Thread(name='transport') and never calls
    ThreadManager.register_thread. WatchdogMonitor iterates only
    thread_manager.threads (watchdog.py:151), so the 'transport' entry
    in critical_threads (watchdog.py:91) monitors nothing. 'main' is in
    the same set and is likewise never registered.

    CORRECTION 1 to the issue's analysis — the stall is process-wide,
    and this is confirmed, not hypothesised. WatchdogMonitor runs with
    warning_timeout=15.0, recovery_timeout=30.0, critical_timeout=45.0,
    check_interval=5.0. A 51.7 s stall of the display thread should have
    produced warnings from ~07:39:26 and a soft-recovery attempt from
    ~07:39:41, all before the critical timeout. The watchdog's own
    closing statistics in debug.log read
    "warnings=0, soft_recovery=0/0, hard_recovery=0/0, shutdowns=1" —
    no intermediate escalation occurred at all. The WatchdogMonitor
    thread was therefore itself stalled across the same window and
    resumed with a single check reading 51.7 s. Three independent Python
    threads — display, obd_protocol and WatchdogMonitor — stopped and
    resumed together. That is a confirmed process-wide stall.

    CORRECTION 2 to the issue's analysis — the stall is NOT accounted
    for by RFCOMMTransport._open()'s connect() call. The stall window is
    07:39:11.412 to 07:40:03.090 (51.68 s). The second connect() began
    at approximately 07:39:12.29 (07:39:07.294 plus the 5.0 s retry
    delay) and returned at 07:40:08.224 (55.9 s). The stall started
    ~0.9 s BEFORE connect() was entered and ended ~5.1 s BEFORE it
    returned. The two windows fail to coincide at both ends. A
    GIL-holding connect() would produce coincident windows. The issue's
    "connect() does not release the GIL" mechanism is therefore not
    supported by the timeline and should not be carried forward as the
    working hypothesis. CPython's socket connect releases the GIL for
    the duration of the syscall, which is consistent with this
    observation.

    CORRECTION 3 to the issue's analysis — faulthandler dumps were
    produced and were not lost to timing. app.py:42-45 arms
    faulthandler.dump_traceback_later(15, repeat=True, file=sys.stderr)
    under --debug. faulthandler's timer runs in C and is unaffected by
    Python-level thread stalls, so roughly three dumps fell inside the
    51.7 s window. They went to stderr. The comment at app.py:38-41
    asserts "stderr is already captured by the run command's tee into
    the debug log", which does not hold for a systemd-launched run,
    where bin/gtach.service captures stderr to the journal instead.
    The dumps exist; they are simply not co-located with the logs that
    were reviewed. This is the single highest-value diagnostic already
    available and is currently discarded by default.
  proposed_solution: >
    Edit 1 — terminate on watchdog critical timeout. Introduce
    GTachApplication._watchdog_shutdown as the watchdog's callback. It
    sets self._stop_event and returns, so run()'s loop exits within
    0.5 s and run()'s finally block performs the single, ordered
    teardown via shutdown(), which is already idempotent via
    _shutdown_called (app.py:360-362). It additionally arms a daemon
    threading.Timer of _EXIT_BACKSTOP_SEC (20.0 s) calling
    _force_exit, which flushes logging and calls os._exit(1) if orderly
    exit has not completed. _stop_event construction moves above the
    WatchdogMonitor construction so the attribute exists before the
    callback can be bound.

    Ordering decision, which the issue left open: the callback sets
    _stop_event ONLY. It does not call shutdown() directly. Teardown is
    left entirely to run()'s finally block. Calling shutdown() from the
    watchdog thread would re-enter WatchdogMonitor.stop() from that same
    thread; watchdog.py:114 guards the self-join, so it does not
    deadlock today, but the correctness of the recovery path should not
    depend on that guard. Teardown from the main thread is the simpler
    and more defensible arrangement, and the 20 s backstop bounds it
    unconditionally.

    Edit 2 — make 'transport' monitoring honest. Register the transport
    thread with ThreadManager; give reconnect_indefinitely an optional
    heartbeat callback invoked once per retry iteration; set
    WatchdogMonitor.critical_threads to {'display'} and add
    advisory_threads = {'transport'}, whose level is clamped to
    'warning' in _check_thread_health so an advisory thread can never
    trigger recovery or shutdown. A blocking connect() lasting tens of
    seconds is expected transport behaviour, not a fault, and must not
    be able to restart the application.

    Edit 3 — make the stall observable. Move faulthandler arming from
    app.py into main.py's setup_logging, alongside the existing
    _START_LOG and _DEBUG_LOG definitions, and target a new
    _STACKS_LOG = '/opt/gtach/stacks.log' opened line-buffered in append
    mode and held in a module-level reference. Also call
    faulthandler.enable(file=...) so a hard crash writes there too.
  alternatives_considered:
    - option: "Have the watchdog callback call sys.exit()."
      reason_rejected: >
        sys.exit() raises SystemExit in the calling thread. The callback
        runs on the WatchdogMonitor thread, where SystemExit terminates
        only that thread and leaves the main loop polling. It does not
        end the process.
    - option: "Have the watchdog callback call os._exit(1) immediately."
      reason_rejected: >
        Ends the process without flushing log handlers or restoring the
        terminal, discarding the diagnostic record of the very event
        being recovered from. Retained only as the 20 s backstop, where
        the orderly path has already been given its chance.
    - option: "Keep shutdown_callback=self.shutdown and additionally set _stop_event inside shutdown()."
      reason_rejected: >
        Couples an unrelated concern into shutdown(), which is also
        reached from run()'s finally block and from atexit
        (app.py:69). Setting a stop event from the atexit path is
        meaningless at best. A dedicated callback keeps the terminal
        recovery action explicit and separately testable.
    - option: "Register 'transport' and leave it in critical_threads."
      reason_rejected: >
        A single blocking connect() of 45 s or more would then trigger
        graceful shutdown and, after this change, a process restart —
        converting an expected condition into a restart loop. The
        observed connect() lasted 55.9 s, so this would fire on the
        reported scenario itself.
    - option: "Remove 'transport' from critical_threads and leave the thread unregistered."
      reason_rejected: >
        Resolves the inconsistency by abandoning the intent. The
        transport thread would remain entirely unobserved. The advisory
        tier costs one clamp in _check_thread_health and preserves the
        warning signal.
    - option: "Investigate the stall with py-spy or strace on target, as the issue proposes."
      reason_rejected: >
        Not rejected, but subordinated. faulthandler is already armed
        under --debug and already produced dumps across the stall
        window; redirecting its output is a smaller change that yields
        the same per-thread stack evidence without requiring an
        operator to attach a tool to a live reproduction. External
        tooling remains available if the dumps prove insufficient.
  benefits:
    - "A critical-thread timeout produces a restart rather than a permanent hang. The reported failure becomes self-recovering."
    - "The 20 s backstop makes termination unconditional, independent of whether teardown itself wedges."
    - "Any future critical timeout from any cause is covered, not only this one."
    - "WatchdogMonitor.critical_threads stops naming threads it does not monitor."
    - "The next reproduction yields per-thread stack traces from inside the stall window, in a file alongside the logs already collected."
  risks:
    - risk: >
        Until the stall cause is found, each failed reconnect cycle
        under the no-connection condition becomes a ~52 s freeze
        followed by a restart, rather than one freeze followed by a
        permanent hang. On a Pi Zero 2W the restart itself costs
        several seconds of black screen.
      mitigation: >
        Accepted deliberately. A recurring 52 s freeze that self-clears
        is strictly preferable to a dead screen requiring
        `systemctl restart gtach`. Whether the residual freeze is
        acceptable is the product decision the issue identifies, to be
        taken once this change is in place and edit 3 has produced
        stack evidence.
    - risk: >
        Restart looping could exhaust the systemd start limit
        (StartLimitBurst=3 within StartLimitIntervalSec=60).
      mitigation: >
        Arithmetic does not support this on the observed timings. One
        cycle is ~52 s of stall plus RestartSec=5, so starts are ~57 s
        apart and at most two fall inside any 60 s window. Verify
        against `systemctl show gtach -p NRestarts` during the
        verification run rather than assuming.
    - risk: >
        The backstop timer fires during a legitimately slow but
        progressing teardown, truncating cleanup.
      mitigation: >
        20.0 s exceeds the sum of the bounded joins on that path:
        WatchdogMonitor.stop joins for up to 5.0 s (watchdog.py:115)
        and ThreadManager.shutdown defaults to 10.0 s
        (thread.py:333). The timer is a daemon thread and is not
        cancelled, but os._exit after a completed orderly exit is
        unreachable because the interpreter has already gone.
    - risk: >
        stacks.log grows without bound during a long --debug session.
      mitigation: >
        Dumps occur only under --debug, at 15 s intervals, and are
        small. The file is opened in append mode; it is not rotated by
        this change. Note as an operational item rather than solve it
        here.
    - risk: >
        Registering 'transport' introduces a heartbeat call into
        transport.py, a comm-layer module with no current dependency on
        core.
      mitigation: >
        The heartbeat is passed in as an optional callable. transport.py
        imports nothing new; app.py supplies the binding.

technical_details:
  current_behavior: >
    A critical-thread timeout tears down every worker component and
    leaves the process alive and inert forever. The 'transport' thread
    is named critical but is not monitored. faulthandler stack dumps
    are written to stderr, which under systemd is the journal and not
    the app-owned log set.
  proposed_behavior: >
    A critical-thread timeout sets the application stop event; the main
    loop exits within 0.5 s; run()'s finally block performs the single
    ordered teardown; the interpreter exits and systemd restarts the
    unit. If that sequence has not completed 20.0 s after the timeout,
    the process force-exits. The 'transport' thread is registered and
    monitored at an advisory level that can warn but never recover or
    shut down. faulthandler stack dumps and fatal-error tracebacks are
    written to /opt/gtach/stacks.log under --debug.
  implementation_approach: >
    Five localised edits. No new modules, no new dependencies, no
    interface removals. Each edit is independently revertible.
  code_changes:
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Move self._stop_event construction above the WatchdogMonitor
        construction. Add class constant _EXIT_BACKSTOP_SEC = 20.0. Add
        _watchdog_shutdown and _force_exit. Wire
        shutdown_callback=self._watchdog_shutdown. Remove the
        faulthandler block and its stale comment (relocated to
        main.py). Register the transport thread and pass a heartbeat
        binding.
      functions_affected:
        - "__init__"
        - "_watchdog_shutdown"
        - "_force_exit"
        - "_initialize_normal_mode_components"
      classes_affected:
        - "GTachApplication"
    - component: "WatchdogMonitor"
      file: "src/gtach/core/watchdog.py"
      change_summary: >
        critical_threads becomes {'display'}. Add
        advisory_threads = {'transport'}. In _check_thread_health,
        clamp any level above 'warning' to 'warning' for a thread in
        advisory_threads.
      functions_affected:
        - "__init__"
        - "_check_thread_health"
      classes_affected:
        - "WatchdogMonitor"
    - component: "OBDTransport"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        reconnect_indefinitely gains an optional heartbeat callable,
        invoked once per loop iteration before the connect attempt and
        once after it returns.
      functions_affected:
        - "reconnect_indefinitely"
      classes_affected:
        - "OBDTransport"
    - component: "setup_logging"
      file: "src/gtach/main.py"
      change_summary: >
        Add _STACKS_LOG and a module-level _stacks_file reference. When
        debug is set, open the file line-buffered in append mode, call
        faulthandler.enable(file=...) and
        faulthandler.dump_traceback_later(15, repeat=True, file=...).
      functions_affected:
        - "setup_logging"
      classes_affected: []
    - component: "EDIT F (iteration 2) — enable_stack_dumps / disable_stack_dumps"
      file: "src/gtach/main.py"
      change_summary: >
        Extract the faulthandler arming from setup_logging into a
        module-level enable_stack_dumps() and add a matching
        disable_stack_dumps() that cancels the repeat timer via
        faulthandler.cancel_dump_traceback_later() and closes
        _stacks_file. setup_logging calls enable_stack_dumps() when its
        debug argument is true, preserving the --debug startup path.
        Both helpers must be idempotent: arming twice must not open a
        second file handle or stack a second timer, and disarming when
        not armed must be a no-op.
      functions_affected:
        - "setup_logging"
        - "enable_stack_dumps"
        - "disable_stack_dumps"
      classes_affected: []
    - component: "EDIT F (iteration 2) — GTachApplication.toggle_debug_logging"
      file: "src/gtach/app.py"
      change_summary: >
        Alongside the existing _debug_handler level change, call
        _main.enable_stack_dumps() when enable is true and
        _main.disable_stack_dumps() when it is false. Retrieve the
        module through the existing sys.modules.get('gtach.main')
        route, which issue-c1d4b8e6 established and which the method
        already uses. Guard the calls so a failure to arm cannot
        prevent the debug handler from being toggled.
      functions_affected:
        - "toggle_debug_logging"
      classes_affected:
        - "GTachApplication"
  data_changes: []
  interface_changes:
    - interface: "OBDTransport.reconnect_indefinitely"
      change_type: "signature"
      details: >
        Gains keyword parameter heartbeat: Optional[Callable[[], None]]
        = None. Existing single-argument and no-argument calls are
        unaffected.
      backward_compatible: "yes"
    - interface: "WatchdogMonitor.critical_threads"
      change_type: "contract"
      details: >
        Membership reduced from {'display', 'transport', 'main'} to
        {'display'}. New sibling attribute advisory_threads = {'transport'}.
        Neither is a constructor parameter, before or after.
      backward_compatible: "n/a"

dependencies:
  internal:
    - component: "ThreadManager"
      impact: >
        register_thread and update_heartbeat are called with a new name,
        'transport'. Neither is modified. update_heartbeat already
        handles the STARTING to RUNNING transition (thread.py:138-155).
    - component: "GTachApplication.run"
      impact: >
        Its finally block becomes the sole teardown path for the
        watchdog-triggered case, where previously teardown ran on the
        watchdog thread and the finally block was never reached.
  external:
    - library: "faulthandler (stdlib)"
      version_change: "none"
      impact: "Output target changes from sys.stderr to an app-owned file."
  required_changes: []

testing_requirements:
  test_approach: >
    Unit tests for the two behavioural units that can be exercised off
    target, plus an on-target reproduction of the reported scenario for
    the parts that cannot.
  test_cases:
    - scenario: >
        Construct GTachApplication, invoke _watchdog_shutdown directly,
        and inspect _stop_event.
      expected_result: "_stop_event.is_set() is True immediately on return."
    - scenario: >
        Run GTachApplication.run in a thread with a stubbed start(),
        invoke _watchdog_shutdown from another thread.
      expected_result: "run() returns within 1.0 s and shutdown() has been called exactly once."
    - scenario: >
        Call shutdown() twice in succession.
      expected_result: "Second call returns immediately; teardown side effects occur once (existing _shutdown_called guard)."
    - scenario: >
        WatchdogMonitor with advisory_threads={'transport'} and a
        registered 'transport' whose heartbeat is aged past
        critical_timeout; run one _check_thread_health cycle.
      expected_result: >
        A warning is logged for 'transport'. No recovery attempt is
        made, _initiate_graceful_shutdown is not called, and
        recovery_stats.shutdown_triggers remains 0.
    - scenario: >
        Same, but for a registered 'display' thread aged past
        critical_timeout.
      expected_result: "_initiate_graceful_shutdown is called; the shutdown callback runs."
    - scenario: >
        reconnect_indefinitely called with a heartbeat callable and a
        transport whose connect() returns False once then True.
      expected_result: "The callable is invoked at least once per iteration; the method returns on success."
    - scenario: >
        reconnect_indefinitely called with no heartbeat argument.
      expected_result: "Behaviour unchanged; no exception."
    - scenario: >
        On target: start gtach with no reachable ELM327 emulator or
        Bluetooth adapter and wait through one failed connect cycle.
      expected_result: >
        Following the critical timeout, `systemctl status gtach` shows a
        NEW main PID and a later start time, and
        `systemctl show gtach -p NRestarts` has incremented.
    - scenario: >
        On target with --debug: reproduce the stall and inspect
        /opt/gtach/stacks.log.
      expected_result: >
        The file contains dumps timestamped inside the stall window,
        each listing every thread and its stack, including the
        display, obd_protocol, transport and WatchdogMonitor threads.
  regression_scope:
    - "Normal startup and shutdown on target, with a reachable OBD connection."
    - "SIGTERM and SIGINT shutdown paths, which set _stop_event by the pre-existing route."
    - "Options-screen restart path (_request_restart), which also sets _stop_event."
    - "Simulation transports (simtcp, simbt), which use the same reconnect_indefinitely."
    - "tests/ suite in full."
  validation_criteria:
    - "GTachApplication.shutdown remains reachable exactly once per process lifetime."
    - "No new import of gtach.core into gtach.comm."
    - "faulthandler is armed only when debug is set."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Edit src/gtach/main.py: add _STACKS_LOG, _stacks_file, faulthandler arming inside setup_logging."
      owner: "tactical"
    - step: "Edit src/gtach/app.py: remove the faulthandler block; reorder _stop_event; add _EXIT_BACKSTOP_SEC, _watchdog_shutdown, _force_exit; rewire shutdown_callback."
      owner: "tactical"
    - step: "Edit src/gtach/app.py: register the transport thread and pass the heartbeat binding."
      owner: "tactical"
    - step: "Edit src/gtach/comm/transport.py: add the heartbeat parameter to reconnect_indefinitely."
      owner: "tactical"
    - step: "Edit src/gtach/core/watchdog.py: critical_threads, advisory_threads, level clamp."
      owner: "tactical"
    - step: "Add unit tests per testing_requirements.test_cases items 1-7."
      owner: "tactical"
    - step: "Deploy to gtach.local and run the two on-target scenarios."
      owner: "human"
  rollback_procedure: >
    Revert the commit. The five edits are additive or localised; no
    data, configuration or unit-file state is migrated, so revert is
    complete. If only the restart behaviour must be withdrawn while
    retaining diagnostics, restore
    shutdown_callback=self.shutdown in app.py and leave the main.py
    edit in place.
  deployment_notes: >
    /opt/gtach must be writable by the service user (root, per
    bin/gtach.service) for stacks.log. start.log and debug.log already
    live there, so no new permission is required. bin/gtach.service
    needs no change.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5a9dc15e"
      relationship: >
        related. Previously narrowed WatchdogMonitor's lock discipline
        in _check_thread_health; this change adds the advisory clamp to
        the same method's phase-2 dispatch.
    - change_ref: "change-6a3b7c52"
      relationship: >
        related. Established the app-owned start.log and debug.log in
        main.py that stacks.log now joins.
  related_issues:
    - issue_ref: "issue-2ac1c602"
      relationship: "resolves"
    - issue_ref: "issue-e4a6c8f2"
      relationship: >
        related. Watchdog self-join on Darwin; the same self-join guard
        at watchdog.py:114 is the reason the current callback wiring
        does not deadlock, and part of why this change moves teardown
        off the watchdog thread rather than relying on it.

notes: >
  Three corrections to issue-2ac1c602 iteration 2 are recorded in
  rational.problem_statement and are the reason this change is scoped as
  it is. In summary: the process-wide nature of the stall is confirmed
  by the watchdog's own zero escalation counters, not merely
  hypothesised; the connect()-holds-the-GIL mechanism is contradicted by
  the timeline at both ends and should be withdrawn; and faulthandler
  dumps were produced during the stall but were written to stderr, which
  under systemd is the journal rather than the reviewed log set.
  issue-2ac1c602 should be advanced to iteration 3 to absorb these, and
  coupled_docs.issue_iteration here raised to 3 accordingly.

  This change deliberately does not attempt to explain or fix the stall.
  On the evidence available the cause is not established, and edit 3
  exists precisely to establish it on the next reproduction rather than
  to encode a guess.

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-2ac1c602 iteration 2."
      - "Records three corrections to the issue's analysis arising from independent re-verification against source and the 2026-08-12 logs."
  - version: "2.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Iteration 1 -> 2. Status proposed -> implemented; coupled issue_iteration raised 2 -> 3."
      - "Added EDIT F: extract faulthandler arming into enable_stack_dumps/disable_stack_dumps in main.py and call them from GTachApplication.toggle_debug_logging, so the runtime OPTIONS debug toggle arms stack dumps as well as the debug handler."
      - "Rationale: iteration 1's EDIT A gated arming on setup_logging's debug argument, which derives from --debug. bin/gtach.service passes no --debug, so /opt/gtach/stacks.log was never created on the 2026-08-12 09:11 verification run. The delivered edit could not achieve its stated purpose under the deployed configuration."
      - "Recorded that iteration 1 is deployed but unverified: the 51.7s stall did not recur on the 09:11 run, so the process-termination path was never exercised."
      - "Rejected adding --debug to bin/gtach.service: it would make debug logging permanent in production and write a full all-thread stack dump every 15s for the life of every run. The out_of_scope entry excluding service-unit changes stands."

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
| 1.0 | 2026-08-12 | Initial change document. Watchdog critical-thread recovery terminates the process; transport thread registered and monitored advisory-only; faulthandler stack dumps redirected to an app-owned log. Records three corrections to issue-2ac1c602 iteration 2. |
| 2.0 | 2026-08-12 | Iteration 1 -> 2. Status implemented. Adds EDIT F: faulthandler arming extracted into enable_stack_dumps/disable_stack_dumps and driven from the runtime OPTIONS debug toggle, because iteration 1 gated it on the startup --debug flag that bin/gtach.service never passes, so stacks.log was never created. |

---

Copyright (c) 2026 William Watson. MIT License.
