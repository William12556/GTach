Created: 2026 August 12

# Issue: No Recovery From Mid-Session Link Loss

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-9c2f41d8"
  title: "A read timeout does not mark the transport down, and reconnect_indefinitely is never re-entered, so the OBD loop polls a dead socket indefinitely after mid-session link loss; disconnect() additionally sets the shutdown event that reconnect_indefinitely loops on, which would permanently disable any naive fix"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "closed"
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
    Reported 2026-08-12. William stopped the ELM327 emulator while
    GTach was running and connected, then later restarted it. GTach did
    not recover in either direction: it neither tore down the dead link
    nor reconnected when the emulator returned. Diagnosed from
    logs/debug.log for the 12:06 and 12:15 runs and from source review
    of transport.py and obd.py.

affected_scope:
  components:
    - name: "OBDTransport.send_command (timeout branch)"
      file_path: "src/gtach/comm/transport.py"
    - name: "OBDTransport.disconnect"
      file_path: "src/gtach/comm/transport.py"
    - name: "OBDTransport.reconnect_indefinitely"
      file_path: "src/gtach/comm/transport.py"
    - name: "OBDProtocol._protocol_loop"
      file_path: "src/gtach/comm/obd.py"
    - name: "GTachApplication._start_obd / _start_normal_mode (transport thread lifecycle)"
      file_path: "src/gtach/app.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: >
    GTach running on gtach.local, connected to the ELM327 emulator on
    ELM327-Emulator.local, with debug logging enabled.
  steps:
    - "Confirm GTach is connected and displaying live RPM."
    - "Stop the ELM327 emulator."
    - "Observe the display switch to DISCONNECTED within ~2 s."
    - "Observe debug.log: 'Timeout waiting for response' repeats every ~1.07 s indefinitely, each followed by a TX. No disconnect, no reconnect attempt."
    - "Restart the ELM327 emulator."
    - "Observe that GTach does not reconnect."
  frequency: "always"
  reproducibility_conditions: >
    Deterministic. Follows from the exception ordering in send_command
    and from reconnect_indefinitely having exactly two call sites, both
    at startup.
  test_data: >
    debug.log, 12:06 run (pid 725), link loss:

      12:11:12.073 - first RFCOMMTransport WARNING "Timeout waiting for
        response from device (cmd='010C', timeout=1.0s)".
      12:11:13.019 - DisplayManager INFO "Link lost — no data for
        2.0s". The DISCONNECTED screen is drawn and its regions
        registered at 12:11:37.870. Display-side detection works.
      12:11:12 to 12:11:59 - 38 consecutive read timeouts, one every
        ~1.07 s, each followed by "TX: b'010C\\r'". Writes continue to
        succeed; only reads time out.
      Throughout - no "Disconnected from", no "Failed to connect", no
        reconnect attempt of any kind. grep for reconnect activity
        across the run returns nothing.

    debug.log, 12:15 run, after the application was restarted:

      12:15:08.478 - "Starting GTach application v0.4.1".
      12:15:08.767 - RFCOMMTransport ERROR "Failed to connect to RFCOMM
        device DC:A6:32:54:AD:77 on channel 1: [Errno 16] Device or
        resource busy" — on the very first attempt, before the retry
        loop.
      12:15:08 to 12:17:59 - the same EBUSY failure every 5.0 s, 12
        occurrences in this log alone, continuing to the end of the
        capture.

    Source, transport.py:

      285-288  except self._TIMEOUT_ERRORS: logs the warning and
               returns None. It does not discard the handle and does
               not change _state. socket.timeout is an OSError
               subclass, so this branch is deliberately ordered before
               _IO_ERRORS at 289, which DOES discard the handle and set
               DISCONNECTED.
      225-232  disconnect() calls self._shutdown.set() at line 228.
      342,349  reconnect_indefinitely loops on
               `while not self._shutdown.is_set()` and waits on the
               same event.
      119      _shutdown is set nowhere else and cleared nowhere at
               all.

    Source, obd.py:

      80       `while self.transport.is_connected():` is the inner
               poll loop's only exit condition.

    Source, app.py:

      389, 433 the only two call sites of reconnect_indefinitely, both
               in _start_obd and _start_normal_mode respectively, each
               in a one-shot daemon thread whose target returns on the
               first successful connect.
  error_output: >
    RFCOMMTransport WARNING "Timeout waiting for response from device
    (cmd='010C', timeout=1.0s)", repeating indefinitely. Later, after
    an application restart, RFCOMMTransport ERROR "Failed to connect
    ... [Errno 16] Device or resource busy", repeating every 5 s. No
    exception or traceback in either case.

behavior:
  expected: >
    A link that stops responding is torn down and reconnection is
    attempted until it succeeds, so that restoring the OBD source
    restores the display without operator action.
  actual: >
    CONFIRMED, PRIMARY. send_command's timeout branch
    (transport.py:285-288) logs and returns None. It leaves _state at
    CONNECTED and leaves _handle live. socket.timeout being an OSError
    subclass, this branch is ordered before the _IO_ERRORS branch at
    289 which would have discarded the handle and set DISCONNECTED — so
    a read timeout is structurally excluded from the path that marks
    the transport down. OBDProtocol._protocol_loop's inner loop
    (obd.py:80) exits only when transport.is_connected() goes false,
    which it never does. The loop therefore writes and times out
    forever at ~1 Hz.

    CONFIRMED, SECONDARY. reconnect_indefinitely has exactly two call
    sites (app.py:389, app.py:433), both at startup, each in a one-shot
    daemon thread whose target returns on the first successful connect.
    After that thread returns there is no path back into reconnection
    for the lifetime of the process. Even if the transport were
    correctly marked down, nothing would reconnect it.

    CONFIRMED, A TRAP FOR THE FIX. disconnect() sets self._shutdown
    (transport.py:228). That is the identical event
    reconnect_indefinitely loops on (342) and waits on (349), and it is
    cleared nowhere. Calling disconnect() to tear down a dead link
    would therefore permanently disable reconnection for the rest of
    the process. The obvious one-line fix — call disconnect() on
    repeated timeouts, restart the reconnect thread — silently does
    nothing, because the loop exits on its first test.

    OBSERVED, NOT EXPLAINED. After the application was restarted, every
    connect attempt fails with [Errno 16] Device or resource busy,
    from the first attempt onward and every 5 s thereafter. This is
    consistent with the RFCOMM channel to that address remaining bound
    from the abandoned session, but the mechanism is not established
    from the evidence available and may lie on the emulator side, in
    BlueZ, or in a socket not released by the previous process. It is
    recorded here because it is what the operator experiences as
    "GTach does not reconnect after I restart the emulator", but it is
    a distinct question from the two confirmed defects above.
  impact: >
    Losing the OBD link mid-session is permanent for the life of the
    process. In a vehicle this means an adapter that browns out, is
    knocked, or drops its link leaves the tachometer dead until the
    operator intervenes, with the application otherwise healthy and the
    display correctly showing DISCONNECTED.

    Not caught by any existing safeguard. The obd_protocol thread
    heartbeats normally throughout, because it is looping rather than
    stalled, so WatchdogMonitor sees nothing. The transport thread is
    advisory-only since change-2ac1c602 and has in any case already
    returned.

    Severity high rather than critical only because change-7d4e91a3
    made the DISCONNECTED screen's Setup button live, giving the
    operator a manual route. Before that change this condition was
    unrecoverable without a service restart.
  workaround: >
    Use the DISCONNECTED screen's Setup button to re-pair, or restart
    the service. Note that a service restart currently runs into the
    EBUSY condition recorded above, so it is not reliably effective.

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    The transport has two states in practice — a socket that is open,
    and a link that is working — and only models the first.
    is_connected() reports on the handle, not on whether the peer is
    responding. Every consumer that asks "are we connected?" is
    therefore asking the wrong question, and a peer that stops
    answering while leaving the socket open is invisible to all of
    them.

    The display layer does not have this problem, because
    _link_lost() reasons from data recency rather than from socket
    state (issue-4d9e2f18) — which is exactly why the DISCONNECTED
    screen appeared correctly at 12:11:13 while the transport carried
    on regardless. The correction wanted here is the transport-side
    equivalent of that same insight.
  technical_notes: >
    Any fix must separate two concepts that disconnect() currently
    conflates: closing the current link, and shutting the transport
    down for good. _shutdown is legitimately set during application
    shutdown, where reconnect_indefinitely must exit. It must not be
    set when a dead link is being torn down for the purpose of
    reconnecting. This is the single most important design constraint
    on the fix and the one most likely to be missed, because
    disconnect() is the natural-looking method to call.

    Consecutive-timeout thresholding is preferable to a single-timeout
    trigger. A lone timeout is normal against a busy adapter; the
    observed failure produced 38 in a row. A threshold of a small
    number of consecutive timeouts, reset by any successful response,
    distinguishes the two without tuning.

    The EBUSY observation should be diagnosed after the primary fix,
    not before. If the abandoned socket is the cause, closing the link
    properly on timeout may remove the condition entirely, in which
    case there is nothing further to fix. Investigating it first risks
    solving a symptom of the defect already identified.
  related_issues:
    - issue_ref: "issue-4d9e2f18"
      relationship: >
        related. Established display-side link-loss detection from data
        recency, which works correctly here. This issue is the
        transport-side counterpart that was not addressed.
    - issue_ref: "issue-a3f1d8e2"
      relationship: >
        related. Concerned adapter re-initialisation on reconnect. Its
        assumptions should be re-checked once reconnection can actually
        occur mid-session.
    - issue_ref: "issue-2ac1c602"
      relationship: >
        related. Concerned failure to connect at startup and the
        watchdog's response to it. This issue concerns loss of an
        already established link, which no watchdog path covers.
    - issue_ref: "issue-7d4e91a3"
      relationship: >
        related. Its fix supplies the only manual workaround for this
        condition, which is why severity is high rather than critical.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Three corrections, in priority order.

    1. Mark the transport down on sustained read timeouts. Count
    consecutive timeouts in send_command, reset the count on any
    successful response, and on crossing a small threshold discard the
    handle and set _state to DISCONNECTED — the same actions the
    _IO_ERRORS branch already takes. is_connected() then goes false and
    _protocol_loop's inner loop exits on its existing condition, with
    no change to obd.py required.

    2. Separate link teardown from transport shutdown. Introduce a
    close-current-link operation that discards the handle and sets
    DISCONNECTED WITHOUT touching _shutdown, and leave disconnect()
    setting _shutdown for the application-shutdown path that needs it.
    Without this, correction 3 cannot work.

    3. Re-enter reconnection when the link goes down. Make the
    transport thread's lifetime match the process rather than the first
    successful connect, so that reconnect_indefinitely resumes retrying
    whenever the transport is not connected and _shutdown is not set.
    Whether this is best done by looping inside reconnect_indefinitely
    or by restarting the thread from the application is an
    implementation choice for the change document; the thread is
    registered with ThreadManager as 'transport' and any restart must
    keep that registration coherent.

    The EBUSY condition is deliberately excluded from this scope and
    should be re-examined once the above is in place.
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
    A transport's notion of "connected" should be defined by whether
    the peer is responding, not by whether a file descriptor is open.
    Where the two can diverge, the divergence is the failure mode worth
    testing.
  process_improvements: >
    Link loss should be tested by removing the peer mid-session, not
    only by starting without one. Every prior transport issue on this
    project tested the absent-at-startup case; this condition survived
    all of them.

verification_enhanced:
  verification_steps:
    - "Confirm from source that send_command's timeout branch neither discards the handle nor changes _state, and is ordered before the _IO_ERRORS branch that does both. [DONE.]"
    - "Confirm that reconnect_indefinitely has exactly two call sites, both at startup, in threads that return on first success. [DONE.]"
    - "Confirm that disconnect() sets the same event reconnect_indefinitely loops on, and that the event is cleared nowhere. [DONE.]"
    - "After the fix: stop the emulator mid-session; confirm the transport goes not-connected within the threshold, that the timeout loop stops, and that reconnection attempts begin."
    - "After the fix: restart the emulator; confirm GTach reconnects without operator action and RPM resumes."
    - "After the fix: confirm application shutdown still terminates the reconnect loop promptly, i.e. that separating link teardown from _shutdown has not broken the shutdown path."
    - "After the fix: confirm the 'transport' thread's ThreadManager registration remains coherent across a reconnect cycle, with no 'Heartbeat for unknown thread' warnings."
    - "After the fix: re-examine whether [Errno 16] Device or resource busy still occurs on restart after a link loss."
  verification_results: >
    First three steps complete, as recorded in test_data and behavior
    above. Remaining steps require the fix to exist.

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  The trap recorded under behavior — that disconnect() sets the event
  reconnect_indefinitely loops on — is the reason this issue is written
  at length rather than as a one-line timeout fix. A change that adds
  timeout detection and calls disconnect() would pass review, pass unit
  tests that assert the transport goes not-connected, and still never
  reconnect on target.

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
      - "Initial issue document from user report of link loss on stopping the ELM327 emulator mid-session, and of failure to reconnect on restarting it."
      - "Confirmed primary cause: send_command's timeout branch leaves _state CONNECTED and the handle live, and is ordered ahead of the _IO_ERRORS branch that would mark the transport down."
      - "Confirmed secondary cause: reconnect_indefinitely's only two call sites are at startup, in threads that return on first success."
      - "Confirmed a trap for any fix: disconnect() sets the shutdown event reconnect_indefinitely loops on, which is cleared nowhere."
      - "Recorded [Errno 16] Device or resource busy on every connect after restart as an observation whose mechanism is not established, deliberately excluded from the resolution scope."

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
| 1.0 | 2026-08-12 | Initial issue document. Read timeouts do not mark the transport down and reconnection is never re-entered after startup; disconnect() sets the event reconnect_indefinitely loops on, trapping any naive fix. EBUSY on restart recorded as unexplained and out of scope. |

---

Copyright (c) 2026 William Watson. MIT License.
