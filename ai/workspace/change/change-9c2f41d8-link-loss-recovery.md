Created: 2026 August 12

# Change: Detect a Dead Link and Reconnect for the Life of the Process

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-9c2f41d8"
  title: "Mark the transport down after consecutive read timeouts; add a link-teardown operation that does not set the shutdown event; make reconnect_indefinitely a process-lifetime loop that resumes retrying whenever the link drops"
  date: "2026-08-12"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-9c2f41d8"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-9c2f41d8"
  description: >
    Resolves issue-9c2f41d8. A read timeout leaves _state CONNECTED and
    the handle live, so OBDProtocol polls a dead socket indefinitely;
    and reconnect_indefinitely's only call sites are at startup, in
    threads that return on first success, so nothing reconnects even if
    the transport were marked down.

scope:
  summary: >
    Three edits, all in src/gtach/comm/transport.py. Count consecutive
    read timeouts in send_command and drop the link on crossing a
    threshold. Add drop_link(), which discards the handle and sets
    DISCONNECTED without touching _shutdown. Restructure
    reconnect_indefinitely into a process-lifetime loop that supervises
    the link rather than returning on first success.
  affected_components:
    - name: "OBDTransport.send_command"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "OBDTransport.drop_link"
      file_path: "src/gtach/comm/transport.py"
      change_type: "add"
    - name: "OBDTransport.reconnect_indefinitely"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "OBDTransport.__init__ (consecutive-timeout counter)"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/comm/obd.py. No change is required. _protocol_loop's inner loop already exits on `while self.transport.is_connected():`, and already resets _adapter_initialised when it does (obd.py:104). Correcting is_connected() to tell the truth is sufficient."
    - "src/gtach/app.py. The transport thread is already created as a daemon and already registered with ThreadManager as 'transport' with a heartbeat binding (change-2ac1c602). Making reconnect_indefinitely long-lived means the existing thread simply never returns, so no lifecycle change is needed."
    - "src/gtach/comm/rfcomm.py. The socket primitives are correct."
    - "OBDTransport.disconnect. It retains its current behaviour, including setting _shutdown, because the application-shutdown path requires exactly that."
    - "[Errno 16] Device or resource busy on connect after a restart. Deliberately excluded per the issue: it may be a symptom of the abandoned socket this change stops abandoning, and diagnosing it first risks solving a consequence of a defect already identified. Re-examine after this change is deployed."
    - "WatchdogMonitor. 'transport' remains advisory-only. A supervising transport thread that blocks in connect() for tens of seconds is still expected behaviour and must not trigger recovery."

rational:
  problem_statement: >
    The transport models whether a socket is open, not whether the peer
    is answering, and the two diverged for 47 s of observed logging
    without anything noticing.

    send_command's timeout branch (transport.py:285-288) logs and
    returns None, leaving _state CONNECTED and _handle live.
    socket.timeout is an OSError subclass, so this branch is ordered
    deliberately before the _IO_ERRORS branch at 289 — the branch that
    discards the handle and sets DISCONNECTED. A read timeout is
    therefore structurally excluded from the only path that marks the
    transport down. OBDProtocol._protocol_loop's inner loop (obd.py:80)
    exits only on is_connected() going false, so it writes and times
    out at ~1 Hz forever: 38 consecutive occurrences observed between
    12:11:12 and 12:11:59.

    reconnect_indefinitely has exactly two call sites (app.py:389,
    app.py:433), both at startup, each in a thread whose target returns
    on the first successful connect. After that, no path back into
    reconnection exists for the process lifetime.

    And disconnect() sets self._shutdown (transport.py:228) — the same
    event reconnect_indefinitely loops on (342) and waits on (349),
    cleared nowhere. Tearing down a dead link by calling disconnect()
    would permanently disable reconnection.
  proposed_solution: >
    EDIT L — count consecutive read timeouts. Add
    _consecutive_timeouts, guarded by the existing _lock, and a class
    constant _MAX_CONSECUTIVE_TIMEOUTS = 5. Reset the counter to zero
    on any successful response. In the timeout branch, increment it and
    call drop_link() on reaching the threshold, logging at ERROR that
    the link is being dropped.

    Five is chosen against the observed timings rather than by taste. A
    command timeout is 1.0 s and the observed cycle was ~1.07 s, so the
    threshold trips at ~5.4 s — long enough that a single slow adapter
    response cannot trip it, short enough to sit under the display's
    own link-lost declaration at 2.0 s plus a reconnect cycle, and well
    under WatchdogMonitor's 15 s warning threshold.

    EDIT M — separate link teardown from transport shutdown. Add
    drop_link(), which takes _lock, calls _discard_handle_locked() and
    sets _state to DISCONNECTED. It does NOT touch _shutdown.
    disconnect() is unchanged and continues to set _shutdown for the
    application-shutdown path. This distinction is the load-bearing
    part of the change.

    EDIT N — supervise the link for the process lifetime. Restructure
    reconnect_indefinitely so that a successful connect no longer
    returns. It instead waits, heartbeating, until either is_connected()
    goes false — at which point it falls back into the retry loop — or
    _shutdown is set, at which point it returns. The thread already
    registered as 'transport' therefore lives for the process, which is
    what registering it implied, and its heartbeat continues to flow in
    both the connected and reconnecting states.
  alternatives_considered:
    - option: "Call disconnect() on repeated timeouts."
      reason_rejected: >
        disconnect() sets _shutdown, which reconnect_indefinitely loops
        on and which is cleared nowhere. Reconnection would be
        permanently disabled. This is the trap recorded in the issue:
        the change would pass unit tests asserting the transport goes
        not-connected, and never reconnect on target.
    - option: "Drop the link on the first timeout rather than on a threshold."
      reason_rejected: >
        A lone timeout is normal against a busy adapter and would cause
        needless reconnect cycles. The observed failure produced 38 in
        a row; a threshold distinguishes the two without tuning.
    - option: "Detect link loss in obd.py by tracking data recency, mirroring DisplayManager._link_lost."
      reason_rejected: >
        Places the knowledge in a consumer rather than in the transport
        that owns the socket, leaving every other consumer of
        is_connected() still misinformed. The transport should not
        report connected when it is not.
    - option: "Have the application restart the transport thread on link loss."
      reason_rejected: >
        Requires a link-loss callback into app.py, a new thread each
        cycle, and re-registration with ThreadManager on every
        reconnect — ThreadManager.register_thread warns and returns
        early when an active entry of the same name exists, so the
        registration would have to be torn down first. A supervising
        loop inside the existing thread achieves the same outcome with
        no lifecycle churn.
    - option: "Clear _shutdown at the top of reconnect_indefinitely so disconnect() can be reused."
      reason_rejected: >
        Makes the shutdown event non-monotonic and races the
        application-shutdown path: a disconnect issued during shutdown
        could be undone by a reconnect loop clearing the flag. A
        separate operation is safer than a shared one with a reset.
  benefits:
    - "Restoring the OBD source restores the display with no operator action."
    - "is_connected() becomes truthful, correcting every consumer at once rather than one at a time."
    - "obd.py needs no change: its existing exit condition starts working."
    - "The 'transport' thread becomes genuinely long-lived, which is what its ThreadManager registration already implied."
    - "The abandoned socket is now closed on link loss, which may also remove the EBUSY-on-restart condition."
  risks:
    - risk: >
        A slow but healthy adapter trips the threshold and causes a
        needless reconnect cycle.
      mitigation: >
        Five consecutive timeouts at 1.0 s each is ~5.4 s of complete
        silence. Any successful response resets the counter, so only
        sustained silence trips it. If field evidence shows false
        trips, the constant is a single named value to raise.
    - risk: >
        reconnect_indefinitely no longer returns, so a defect in its
        loop becomes a permanently running thread rather than one that
        exits.
      mitigation: >
        Both loop conditions test _shutdown, and the supervising wait
        uses _shutdown.wait() rather than time.sleep(), so shutdown
        interrupts it immediately rather than after a poll interval.
        Covered by an explicit shutdown-path test and a regression step.
    - risk: >
        The transport thread now heartbeats continuously where before
        it stopped heartbeating after connecting.
      mitigation: >
        Correct and intended. Previously the registered 'transport'
        entry went stale the moment the thread returned, which would
        have produced perpetual advisory warnings; this change makes
        the registration meaningful. Confirm no 'Heartbeat for unknown
        thread' warnings appear across a reconnect cycle.
    - risk: >
        drop_link() is called from the OBD thread while
        reconnect_indefinitely reads is_connected() from the transport
        thread.
      mitigation: >
        Both go through the existing _lock. drop_link performs no
        blocking call while holding it — _discard_handle_locked closes
        a socket, which does not block on a dead link. The worst case
        is one extra supervising-loop iteration before the drop is
        observed.
    - risk: >
        Reconnecting mid-session leaves the ELM327 adapter in an
        unknown state.
      mitigation: >
        Already handled. _protocol_loop resets _adapter_initialised
        when the inner loop exits (obd.py:104) and re-runs
        _initialize_protocol on the next pass. issue-a3f1d8e2 covered
        the re-initialisation semantics; this change is the first to
        exercise them mid-session, so the reconnect verification step
        should confirm the adapter comes back cleanly.

technical_details:
  current_behavior: >
    A read timeout is logged and ignored. The transport reports
    connected indefinitely against a dead peer. The OBD loop polls at
    ~1 Hz forever. No reconnection is attempted for the life of the
    process.
  proposed_behavior: >
    Five consecutive read timeouts drop the link: the handle is closed
    and the transport reports not-connected. The OBD loop exits its
    inner poll on its existing condition and resets its adapter flag.
    The transport thread, which now supervises rather than returning,
    observes the drop and resumes retrying at the existing 5 s
    interval until it reconnects or the application shuts down.
  implementation_approach: >
    Three edits in one file. No new imports, no new dependencies, no
    change to any other module. disconnect() untouched.
  code_changes:
    - component: "OBDTransport"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        Add _MAX_CONSECUTIVE_TIMEOUTS = 5 as a class constant and
        _consecutive_timeouts = 0 in __init__. Reset the counter on a
        successful response in send_command; increment it in the
        timeout branch and call drop_link() on reaching the threshold.
        Add drop_link(). Restructure reconnect_indefinitely into a
        supervising loop.
      functions_affected:
        - "__init__"
        - "send_command"
        - "drop_link"
        - "reconnect_indefinitely"
      classes_affected:
        - "OBDTransport"
  data_changes: []
  interface_changes:
    - interface: "OBDTransport.drop_link"
      change_type: "contract"
      details: >
        New public method. Closes the current link and sets
        DISCONNECTED without setting _shutdown, so reconnection remains
        possible. Distinct from disconnect(), which ends the
        transport's life.
      backward_compatible: "yes"
    - interface: "OBDTransport.reconnect_indefinitely"
      change_type: "contract"
      details: >
        Signature unchanged. Return semantics change: it no longer
        returns on the first successful connect, but only when
        _shutdown is set. Both existing call sites already run it in a
        daemon thread and ignore its return, so neither requires
        modification.
      backward_compatible: "no"

dependencies:
  internal:
    - component: "OBDProtocol._protocol_loop"
      impact: >
        None in source. Its existing `while self.transport.is_connected():`
        exit condition begins to fire, and its existing
        _adapter_initialised reset runs, both as originally written.
    - component: "ThreadManager"
      impact: >
        The 'transport' registration becomes long-lived and continuously
        heartbeated, rather than going stale once the thread returned.
    - component: "WatchdogMonitor"
      impact: >
        None. 'transport' remains in advisory_threads and cannot
        trigger recovery or shutdown.
  external: []
  required_changes:
    - change_ref: "change-2ac1c602"
      relationship: >
        blocked_by. Registered the transport thread and added the
        heartbeat binding this change relies on.

testing_requirements:
  test_approach: >
    Unit tests against a fake transport whose _read and _open are
    scripted, plus on-target verification of both directions of a
    mid-session link loss.
  test_cases:
    - scenario: "Four consecutive read timeouts, then a successful response."
      expected_result: "The link is not dropped; the counter returns to zero."
    - scenario: "Five consecutive read timeouts."
      expected_result: "drop_link is called; is_connected() is False; an ERROR is logged."
    - scenario: "Three timeouts, a success, then three more timeouts."
      expected_result: "The link is not dropped: the success reset the counter."
    - scenario: "drop_link called on a connected transport."
      expected_result: "The handle is closed, _state is DISCONNECTED, and _shutdown is NOT set."
    - scenario: "drop_link followed by reconnect_indefinitely."
      expected_result: "The loop attempts to connect rather than exiting immediately."
    - scenario: "disconnect() called."
      expected_result: "_shutdown IS set and _state is DISCONNECTED, exactly as before this change."
    - scenario: "reconnect_indefinitely against a transport that connects on the first attempt, then has its link dropped, then connects again."
      expected_result: "The method does not return between the two connects; both connect attempts occur; the heartbeat callable is invoked in both the connected and the retrying phase."
    - scenario: "reconnect_indefinitely with _shutdown set while connected."
      expected_result: "The method returns promptly, without waiting out a retry delay."
    - scenario: "reconnect_indefinitely with _shutdown set while retrying."
      expected_result: "The method returns promptly."
    - scenario: "reconnect_indefinitely called with no heartbeat argument, as before change-2ac1c602."
      expected_result: "No exception; behaviour otherwise as specified."
    - scenario: "On target: stop the emulator mid-session."
      expected_result: "Within ~5.4 s an ERROR records the link being dropped; the timeout loop stops; reconnect attempts begin at 5 s intervals."
    - scenario: "On target: restart the emulator."
      expected_result: "GTach reconnects without operator action, the adapter re-initialises, and RPM resumes on the display."
    - scenario: "On target: shut the application down while reconnecting."
      expected_result: "Shutdown completes promptly; no thread-join warning is logged."
  regression_scope:
    - "Startup with no reachable transport, which must still retry at 5 s intervals as before."
    - "Startup with a reachable transport, which must connect and stay connected."
    - "Application shutdown from SIGTERM, from the OPTIONS restart path, and from the watchdog termination path."
    - "Simulation transports (simtcp, simbt), which share reconnect_indefinitely."
    - "The setup-mode path (_start_obd), which uses the second call site."
    - "tests/ suite in full."
  validation_criteria:
    - "disconnect() is byte-identical to its pre-change state."
    - "obd.py, app.py and rfcomm.py are byte-identical to their pre-change state."
    - "No occurrence of _shutdown.set() outside disconnect()."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Add _MAX_CONSECUTIVE_TIMEOUTS and _consecutive_timeouts; add drop_link()."
      owner: "tactical"
    - step: "Add counter reset and threshold handling to send_command."
      owner: "tactical"
    - step: "Restructure reconnect_indefinitely into a supervising loop."
      owner: "tactical"
    - step: "Add unit tests per testing_requirements.test_cases items 1-10."
      owner: "tactical"
    - step: "Deploy to gtach.local; stop and restart the emulator mid-session."
      owner: "human"
  rollback_procedure: >
    Revert the commit. One file is modified; drop_link is additive and
    unreferenced elsewhere after revert.
  deployment_notes: >
    No service, packaging or configuration change. Verification
    requires a reachable ELM327 emulator that can be stopped and
    restarted while GTach runs.

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
    - change_ref: "change-2ac1c602"
      relationship: "blocked_by. Registered and heartbeated the transport thread this change makes long-lived."
    - change_ref: "change-6481f8ce"
      relationship: "related. Established the connect/disconnect/send_command skeleton in OBDTransport that this change modifies."
    - change_ref: "change-4d9e2f18"
      relationship: "related. Display-side link-loss detection from data recency, the counterpart insight applied here to the transport."
  related_issues:
    - issue_ref: "issue-9c2f41d8"
      relationship: "resolves"
    - issue_ref: "issue-a3f1d8e2"
      relationship: >
        related. Its adapter re-initialisation semantics are exercised
        mid-session for the first time by this change.

notes: >
  The distinction between drop_link() and disconnect() is the whole of
  this change's correctness. disconnect() sets _shutdown, which
  reconnect_indefinitely loops on and which is cleared nowhere; a fix
  that reuses disconnect() would pass unit tests asserting the
  transport goes not-connected and would never reconnect on target.
  This is stated in the issue, here, and as a constraint and a success
  criterion in the prompt, deliberately.

  The EBUSY-on-restart condition is excluded from scope. It may prove
  to be a consequence of the abandoned socket that this change stops
  abandoning, in which case there will be nothing left to fix.

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-9c2f41d8 iteration 1."
      - "Three edits confined to transport.py: consecutive-timeout thresholding, drop_link() as a teardown that does not set _shutdown, and reconnect_indefinitely as a process-lifetime supervising loop."
      - "Records that obd.py requires no change because its existing exit condition begins working once is_connected() is truthful."
      - "Records the rejection of reusing disconnect(), of first-timeout dropping, of consumer-side recency detection, of application-driven thread restart, and of clearing _shutdown."

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
| 1.0 | 2026-08-12 | Initial change document. Consecutive-timeout thresholding drops a dead link; drop_link() separates link teardown from transport shutdown; reconnect_indefinitely becomes a process-lifetime supervising loop. |

---

Copyright (c) 2026 William Watson. MIT License.
