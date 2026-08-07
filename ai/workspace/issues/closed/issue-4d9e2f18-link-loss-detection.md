Created: 2026 August 05

# Issue: The Instrument Reports a Live Connection Whenever Its Own Software Is Running

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-4d9e2f18"
  title: "The connection indicator and the DISCONNECTED screen are both gated on the obd_protocol thread's OS status, which stays RUNNING while the transport retries indefinitely, so a lost adapter leaves a green indicator above a gauge holding a stale RPM"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-4d9e2f18"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: "logs/start.log and logs/debug.log, on-target sessions 2026-08-05 11:38 to 11:55"
  description: >
    Found on the vehicle bench on 2026-08-05. The ELM327 emulator was
    running on a battery which went flat, taking the adapter off the
    air mid-session. The instrument continued to show a green connection
    indicator and a gauge holding its last RPM. The operator reported
    having no way to know the connection had been lost. Foreshadowed as
    an observation in this document's own §9.11 analysis of the two
    preceding sessions, where the same conflation produced a gauge
    frozen at 5941 RPM and then at 0.

affected_scope:
  components:
    - name: "DisplayManager._draw_status_indicator"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._render_normal_modes"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._current_view_key"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: >
    A paired adapter and a running application on the gauge screen. The
    fault is produced by removing the adapter's power rather than by
    closing the connection.
  steps:
    - "Connect to the adapter and confirm RPM is displayed."
    - "Cut power to the adapter — pull the battery, not the plug on a socket the stack would notice."
    - "Observe the indicator. It stays green."
    - "Observe the gauge. The needle holds its last value indefinitely."
    - "Observe that the DISCONNECTED screen, which carries the Setup and Simulate controls, is never shown."
    - "Statically — read manager.py:2158-2166. _draw_status_indicator maps ThreadStatus.RUNNING to ConnectionStatus.CONNECTED."
    - "Read manager.py:_render_normal_modes. Its disconnected test is the same thread-status comparison."
    - "Read comm/transport.py:111-122. reconnect_indefinitely loops until it succeeds or shutdown is set, so the thread hosting it never leaves RUNNING."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional whenever the transport is down and the process is
    alive. It does not require a battery failure; any loss the socket
    does not immediately report produces it, and so does a clean loss,
    because the thread survives either way.
  preconditions: "Simulation mode off."
  test_data: >
    THE CONFLATION, in two places.

      manager.py:2158  thread_status = get_thread_status('obd_protocol')
                       if thread_status == ThreadStatus.RUNNING:
                           status = ConnectionStatus.CONNECTED

      _render_normal_modes  if thread_status != ThreadStatus.RUNNING
                            and not self._sim_mode:
                                self._render_disconnected()

    Both ask "is my Python thread alive?" and present the answer as "is
    the adapter connected?". OBDProtocol's thread is alive for the
    lifetime of the process: its loop sleeps 0.1 s and continues while
    the transport is disconnected (obd.py), and the separate transport
    thread retries every 5 s indefinitely
    (transport.py:111-122). Neither ever leaves RUNNING.

    So the indicator is green whenever the software is running, which is
    to say always, and the DISCONNECTED screen is unreachable by the
    condition it was written for.

    OBSERVED THREE TIMES, in three consecutive sessions:

      11:40  gauge frozen at RPM 5941, indicator green, adapter absent
      11:46  gauge frozen at RPM 0,    indicator green, EHOSTUNREACH
      11:55  operator reports the same, having found the flat battery

    The 11:46 session's start.log shows the transport failing on the
    first attempt — "[Errno 113] No route to host" — while
    obd_protocol transitions to RUNNING three lines later. Both
    statements are in the same log, four milliseconds apart, and the
    display believed the second.

    WHY is_connected() ALONE IS NOT SUFFICIENT. The failure the operator
    met is a powered-down adapter. An RFCOMM socket to a device that has
    lost power does not fail at the moment power is lost; it fails at
    the next write, or at a keepalive, or not until a timeout. So there
    is a window in which the socket reports connected and no data is
    arriving. Detection must include a staleness test to cover it.
  error_output: >
    None on the panel — that is the defect. In the log:

      11:46:23,985 RFCOMMTransport ERROR Failed to connect to RFCOMM
                   device DC:A6:32:54:AD:77 on channel 1:
                   [Errno 113] No route to host
      11:46:23,989 ThreadManager DEBUG Thread obd_protocol transitioned
                   to RUNNING

behavior:
  expected: >
    An instrument that cannot obtain data says so, prominently, and
    offers a route to recovery. A displayed number is either current or
    visibly not current.
  actual: >
    The connection indicator is green whenever the application is
    running. The gauge holds its last received value indefinitely. The
    DISCONNECTED screen, which exists for this condition and carries the
    Setup and Simulate controls, is never displayed.
  impact: >
    A driver reads a stale needle and a green light as live data at a
    constant engine speed. On a vehicle that is a safety-relevant
    misreport: the instrument's single purpose is to show engine speed,
    and it shows a plausible wrong one with a positive indication that
    it is correct.

    Secondarily, there is no route out. The DISCONNECTED screen carries
    the Setup and Simulate controls; without it the operator must know
    to swipe to OPTIONS, which the frozen display gives no reason to
    suspect is possible.
  workaround: >
    Swipe down to OPTIONS and select Simulation mode, or restart. Both
    require the operator to have already deduced that the reading is
    false, which is what the defect prevents.

environment:
  python_version: "3.9 on target"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "pyserial / RFCOMM"
      version: "n/a"
  domain: "domain_1"

analysis:
  root_cause: >
    A proxy chosen for convenience and never revisited. Thread status is
    readily available through ThreadManager's locked accessor, and at
    the time it was written the thread's liveness may have tracked the
    connection closely enough. It does not: reconnect_indefinitely makes
    the thread's survival independent of the link's state by design, so
    the proxy is not merely imprecise but inverted — the harder the
    transport is trying and failing, the more firmly the indicator
    reports success.
  technical_notes: >
    THE DISPLAY DOES NOT CURRENTLY HAVE ACCESS TO THE TRANSPORT.
    DisplayManager is constructed with a ThreadManager and a
    TerminalRestorer (app.py:301) and holds no transport reference.
    app.py holds self._transport and already injects four callables onto
    the display by attribute assignment (app.py:302-305:
    _setup_entry_callback, _restart_callback, _debug_toggle_callback,
    _debug_logging_on). A fifth, supplying the link state, follows the
    established pattern and avoids giving the display layer a reference
    into comm.

    STALENESS NEEDS A TIMESTAMP THE DISPLAY DOES NOT KEEP. The queue is
    drained in _draw_radial_mode, which sets self._last_rpm
    (manager.py:960) but records no time. A monotonic timestamp taken
    at the same point supplies the staleness test with no new plumbing.

    THE DECISIONS TAKEN, both by the operator on 2026-08-05.

      Detection — socket state OR staleness. is_connected() is the fast
      path for a clean loss; staleness is the backstop for the failure
      actually met, an adapter that vanishes without closing its
      socket.

      Presentation — fall back to the DISCONNECTED screen. It exists, it
      is unmistakable, and it carries the Setup and Simulate controls
      that give the operator somewhere to go. The cost, accepted, is
      that a momentary loss blanks the gauge.

    FLAPPING IS THE DESIGN RISK. A link delivering a sample every few
    seconds would oscillate between the gauge and the DISCONNECTED
    screen once per sample, which is worse than either state. The
    recovery rule must require evidence that data is flowing rather than
    that a single sample arrived. change-4d9e2f18 specifies it.

    THIS ALSO EXPLAINS TWO EARLIER OBSERVATIONS. The gauge frozen at
    5941 RPM in the 11:40 session and at 0 in the 11:46 session were
    both this defect, recorded at the time as "the disconnected check is
    on thread status, not transport connectivity" without a triple being
    raised. The operator's report closes that loop.
  related_issues:
    - issue_ref: "issue-6481f8ce"
      relationship: "related"
    - issue_ref: "issue-b8d5e9f0"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Introduce a link-state test combining a transport-supplied
    connectivity callback with a data-staleness timeout, and gate both
    the DISCONNECTED screen and the connection indicator on it instead
    of on thread status. See change-4d9e2f18.
  change_ref: "change-4d9e2f18"
  resolved_date: "2026-08-05"
  resolved_by: "Claude Code, per prompt-4d9e2f18 (commits dd49e17, 62af231)"
  fix_description: >
    _link_lost() combines the transport's is_connected() with a
    LINK_LOSS_TIMEOUT (2.0 s) staleness test against _last_sample_ts,
    gating both _draw_status_indicator and _render_normal_modes.
    Recovery is driven through the render loop rather than by calling
    _note_sample directly — the report's corrected second commit,
    since the original placement made loss permanent. Confirmed live in
    source at manager.py:77, 856, 944, 1425, 2341, each citing
    issue-4d9e2f18 by name.

verification:
  verified_date: "2026-08-07"
  verified_by: "Claude Code (source re-check); William Watson (gtach.local)"
  test_results: >
    Report: acceptance test discriminates — pre-change draws the gauge
    with a green light at the bench-reproduced state, post-change draws
    DISCONNECTED with red. pytest tests/ 11 passed, unchanged. Not
    verified on target by the report itself; William's 2026-08-07
    confirmation that GTach functions correctly on gtach.local now
    covers that gap.
  closure_notes: "Closed on William's confirmation. No residual finding."

prevention:
  preventive_measures: >
    A status indicator should be derived from the thing it names. Where
    a proxy is used because the real signal is awkward to reach, the
    proxy's divergence from the signal is the defect waiting to happen,
    and it will surface at the moment the two differ most — which is
    exactly when the indicator matters.

    "Is the process alive" and "is the peer reachable" are different
    questions in every networked system. Conflating them is a
    recognisable class of fault and worth looking for wherever thread
    or process state is displayed to a user.
  process_improvements: >
    This was visible in the logs of two sessions before the operator met
    it on the bench, and was recorded both times as an observation
    without a triple. An observation that describes a user-visible
    misreport should be raised at the point it is understood rather than
    carried forward.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "With the transport reporting disconnected, the DISCONNECTED screen is shown within the loss timeout."
    - "With the transport reporting connected but no sample arriving, the DISCONNECTED screen is shown within the loss timeout — the powered-down-adapter case."
    - "The connection indicator is red whenever the DISCONNECTED screen is shown."
    - "The indicator is green only while data is actually flowing."
    - "With data flowing normally, neither the screen nor the indicator changes from present behaviour."
    - "Simulation mode is unaffected: the gauge runs and the indicator does not report a lost link."
    - "A link delivering samples at the normal rate does not flap between the gauge and the DISCONNECTED screen."
    - "Recovery from a genuine loss returns to the gauge once data is flowing again."
    - "The DISCONNECTED screen's Setup and Simulate controls work when reached by this route."
    - "The view key accounts for the link state, so the screen change re-registers touch regions."
    - "On the target: power down the adapter mid-session and confirm the screen changes and the indicator turns red."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-4d9e2f18"
  test_refs: []

notes: >
  Raised under P04 from the operator's bench report of 2026-08-05 and
  from log evidence in three consecutive sessions. Not a numbered item
  of either code review.

  issue_info.type is defect and severity is HIGH — the highest assigned
  in this project to date. The instrument misreports its primary
  quantity while positively indicating that the reading is good, on a
  device intended for use while driving. Nothing crashes, which is why
  it survived three sessions of logs.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial issue document from the operator's bench report of 2026-08-05, the ELM327 emulator's battery having gone flat mid-session while the instrument continued to report a live connection."
      - "Recorded the conflation in both places — _draw_status_indicator and _render_normal_modes — and that reconnect_indefinitely makes thread liveness independent of link state by design, so the proxy is inverted rather than merely imprecise."
      - "Recorded the 11:46 log showing 'No route to host' and 'Thread obd_protocol transitioned to RUNNING' four milliseconds apart, the display believing the second."
      - "Recorded why is_connected() alone is insufficient: a socket to a powered-down peer does not fail until the next write or timeout, so staleness is required as the backstop for the failure actually met."
      - "Recorded the operator's two decisions — detection by socket state OR staleness, presentation by falling back to the DISCONNECTED screen — and flapping as the resulting design risk."
      - "Recorded that the display holds no transport reference and that app.py's existing attribute-injection pattern supplies one without giving the display layer a reference into comm."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status open -> closed. change-4d9e2f18 implemented (commits dd49e17, 62af231), confirmed by source re-check: _link_lost, LINK_LOSS_TIMEOUT and _last_sample_ts all present and wired exactly as specified."
      - "Closed on William's confirmation that GTach functions correctly on gtach.local. Moved to ai/workspace/issues/closed/."

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
| 1.0 | 2026-08-05 | Initial issue document. Records the thread-status-as-connectivity conflation in both call sites, the log evidence from three sessions, and why socket state alone cannot detect a powered-down adapter. |
| 1.1 | 2026-08-07 | Status open → closed. Resolution and verification recorded, confirmed by source re-check. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
