Created: 2026 August 05

# Change: Ask the Link, Not the Thread

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-4d9e2f18"
  title: "A link-state test combining a transport connectivity callback with a data-staleness timeout replaces the thread-status proxy in both _render_normal_modes and _draw_status_indicator, so a lost adapter shows the DISCONNECTED screen and a red indicator"
  date: "2026-08-05"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-4d9e2f18"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-4d9e2f18"
  description: >
    Resolves issue-4d9e2f18. Raised under P04 from the operator's bench
    report of 2026-08-05 and log evidence from three consecutive
    sessions. Detection and presentation decided by the operator on the
    same date.

scope:
  summary: >
    One link-state test, used in the two places that currently ask the
    thread manager. A timestamp on the sample drain, a connectivity
    callback injected by app.py, and hysteresis so the screen cannot
    flap.
  affected_components:
    - name: "DisplayManager._link_lost"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._last_sample_ts"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._link_connected_callback"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._render_normal_modes"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_status_indicator"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._current_view_key"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication.start"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "comm/. The transport is asked through a callback; nothing in comm is modified. is_connected() already exists on the OBDTransport interface."
    - "OBDProtocol's loop. It already sleeps and continues correctly when disconnected; its behaviour is not the defect."
    - "reconnect_indefinitely. Retrying indefinitely is correct; the defect is that the display reads the retrying thread's liveness as success."
    - "_render_disconnected and the DISCONNECTED screen's controls. Built by earlier changes, correct, and reached more often after this."
    - "The ACKNOWLEDGEMENT and OPTIONS screens. Link state does not gate them; an operator must be able to reach settings with the adapter down."
    - "Simulation mode. Explicitly exempt — the whole point is a display without an adapter."
    - "The OBD desynchronisation of ai/task.md §9.10.4 and the sluggishness of §9.12. Separate."

rational:
  problem_statement: >
    The connection indicator and the DISCONNECTED screen are both gated
    on the obd_protocol thread's OS status. That thread stays RUNNING
    for the life of the process because its transport retries
    indefinitely, so the indicator is green whenever the software is
    running and the DISCONNECTED screen is unreachable. A driver reads a
    stale needle and a green light as live data.
  proposed_solution: >
    Derive link state from the link: a connectivity callback for the
    fast path and a staleness timeout for the case the socket cannot
    report. Gate both call sites on it, with hysteresis on recovery.
  alternatives_considered:
    - option: "Use transport.is_connected() alone."
      reason_rejected: >
        Cheapest, and misses exactly the failure met on the bench. An
        RFCOMM socket to an adapter that has lost power does not fail
        when the power goes; it fails at the next write or timeout.
        There is a window in which the socket reports connected and no
        data arrives, and the operator sat in that window."
    - option: "Use data staleness alone."
      reason_rejected: >
        Robust and simple, and adds latency equal to the threshold on a
        clean disconnect the socket would have reported at once.
        Rejected in favour of taking both signals, which costs one
        boolean."
    - option: "Keep the gauge and mark it stale — dashes for the numeral, red border."
      reason_rejected: >
        Offered to the operator and not taken. It preserves spatial
        context and avoids blanking the instrument on a blip, at the
        cost of new rendering states and no route to Setup. The
        DISCONNECTED screen already exists and already carries the
        controls that give the operator somewhere to go."
    - option: "Have OBDProtocol stop its thread when the transport drops, so the existing thread-status test becomes correct."
      reason_rejected: >
        Superficially the smallest change and wrong in substance. The
        thread must stay alive to reconnect; stopping it would trade a
        display defect for a recovery defect, and would put the
        watchdog in the position of restarting a thread that stopped
        deliberately."
  benefits:
    - "The instrument stops reporting a live connection it does not have — the substantive safety-relevant correction."
    - "The DISCONNECTED screen becomes reachable by the condition it was written for, giving the operator Setup and Simulate when the adapter is gone."
    - "A stale reading is no longer displayed as current."
  risks:
    - risk: >
        Flapping. A link delivering samples sporadically oscillates
        between the gauge and the DISCONNECTED screen, which is worse
        than either.
      mitigation: >
        Loss requires the condition to hold; recovery requires evidence
        that data is flowing rather than that one sample arrived —
        two samples no more than LOSS_TIMEOUT apart. Asserted with a
        sporadic-sample test."
    - risk: >
        A momentary blip blanks the gauge, which the operator has
        accepted but will still notice.
      mitigation: >
        LOSS_TIMEOUT is set at 2.0 s against a 20-50 Hz data rate, so
        it takes 40 to 100 consecutive missed samples to trigger. That
        is not a blip."
    - risk: >
        The callback is absent — app.py fails to inject it, or the
        display is constructed in a path that does not.
      mitigation: >
        _link_lost treats a missing callback as 'cannot assess socket
        state' and falls back to staleness alone rather than assuming
        connected. Assuming connected would reproduce the defect
        silently; assuming disconnected would blank the gauge on every
        start. Staleness alone is correct in both directions."
    - risk: >
        The view key omits the link state, so the screen changes without
        touch regions being re-registered — the DISCONNECTED screen's
        controls would be drawn and dead.
      mitigation: >
        The link state joins the key in the same edit. Note the key
        already carries a 'disconnected' member computed the old way;
        that member is the thing being corrected, not a new one."
  benefits_measurement: >
    Sessions in which a lost adapter was reported as connected: 3 of 3
    -> 0. Time from adapter loss to the operator being told: never ->
    at most LOSS_TIMEOUT.

technical_details:
  current_behavior: >
    _render_normal_modes tests get_thread_status('obd_protocol') !=
    RUNNING and not _sim_mode, and shows _render_disconnected when true.
    _draw_status_indicator (manager.py:2158) maps RUNNING to
    ConnectionStatus.CONNECTED, STARTING to CONNECTING and anything else
    to DISCONNECTED. _current_view_key computes the same thread-status
    condition as its 'disconnected' member. The queue drain at
    manager.py:953-960 sets _last_rpm and records no time. DisplayManager
    holds no transport reference.
  proposed_behavior: >
    A single _link_lost() answers whether the adapter is delivering
    data. Both call sites and the view key use it. It is false in
    simulation mode by construction.
  implementation_approach: >
    SIX EDITS, five in manager.py and one in app.py.

    1. State. In __init__:
         self._last_sample_ts = None          # monotonic, set on drain
         self._link_connected_callback = None # injected by app.py
         self._link_ok = False                # hysteresis latch
       and class constants LINK_LOSS_TIMEOUT = 2.0 and
       LINK_RECOVERY_SAMPLES = 2.

    2. The timestamp. In _draw_radial_mode's queue drain, wherever
       _last_rpm is assigned from a drained message, also set
       self._last_sample_ts = time.monotonic() and increment a
       consecutive-sample counter. Do NOT set it in the simulation
       branch — simulated values are not evidence of a link.

    3. _link_lost(). Returns True when the adapter is not delivering:

         - False immediately if self._sim_mode. Simulation is a display
           without an adapter and must not report a lost link.
         - If the callback exists and reports not connected -> True.
         - If no sample has ever arrived -> True. This is the state at
           startup before the first sample, which is correct: the
           DISCONNECTED screen is the right thing to show while the
           transport is still connecting.
         - If time since the last sample exceeds LINK_LOSS_TIMEOUT ->
           True.
         - Otherwise False.

       Recovery hysteresis: the latch _link_ok is set only after
       LINK_RECOVERY_SAMPLES samples have arrived within
       LINK_LOSS_TIMEOUT of one another, and cleared as soon as any
       loss condition holds. _link_lost returns not self._link_ok.

    4. The two call sites. _render_normal_modes tests self._link_lost()
       in place of the thread-status comparison, keeping the
       'and not self._sim_mode' semantics — which _link_lost now
       subsumes, so the clause is removed rather than duplicated.
       _draw_status_indicator maps _link_lost() to DISCONNECTED and
       otherwise to CONNECTED; the CONNECTING state is retained for the
       case where the callback reports connected but the recovery latch
       has not yet set, which is precisely 'connecting'.

    5. The view key. Its 'disconnected' member is recomputed from
       _link_lost() rather than from thread status. This is a
       correction to an existing member, not an addition.

    6. app.py. After the other four injections at app.py:302-305, and
       at the equivalent block at 202-205:

         self._display._link_connected_callback = (
             lambda: self._transport.is_connected()
         )

       Guarded so a missing or not-yet-constructed transport yields
       False rather than raising.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _link_lost, _last_sample_ts, _link_connected_callback and the
        recovery latch added; the sample drain timestamped; both call
        sites and the view key's disconnected member gated on link
        state instead of thread status.
      functions_affected:
        - "__init__"
        - "_link_lost"
        - "_draw_radial_mode"
        - "_render_normal_modes"
        - "_draw_status_indicator"
        - "_current_view_key"
      classes_affected:
        - "DisplayManager"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: "Injects a guarded transport connectivity callback onto the display, at both injection sites."
      functions_affected:
        - "start"
        - "_start_setup_mode"
      classes_affected:
        - "GTachApplication"
  data_changes: []
  interface_changes:
    - "DisplayManager gains an optional _link_connected_callback attribute, following the existing injection pattern. Absent, it degrades to staleness-only detection rather than failing."

dependencies:
  internal:
    - component: "OBDTransport.is_connected — comm/transport.py:92"
      impact: "Called through the injected callback. Not modified; it is already on the abstract interface and implemented by all three transports."
    - component: "_render_disconnected and its regions"
      impact: "Reached far more often after this change. Not modified."
    - component: "change-44bca479's view key mechanism"
      impact: "The disconnected member is recomputed. The mechanism is unchanged."
    - component: "change-6481f8ce"
      impact: "Its handle-capture work makes is_connected's answer meaningful under concurrent disconnect. Related, not modified."
  external: []
  required_changes:
    - change_ref: "change-6481f8ce"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with a stubbed rendering engine and a controllable clock,
    so staleness can be exercised without waiting. The link callback is
    a stub returning a settable boolean. The acceptance test is that a
    powered-down adapter — callback still True, samples stopped —
    produces the DISCONNECTED screen, since that is the failure the
    operator met.
  test_cases:
    - scenario: "Callback True, samples arriving at 20 Hz."
      expected_result: "_link_lost False after the recovery threshold; gauge drawn; indicator green."
    - scenario: "ACCEPTANCE. Callback still True, samples stop, clock advances past LINK_LOSS_TIMEOUT."
      expected_result: "_link_lost True; DISCONNECTED screen; indicator red. This is the flat-battery case and it must pass."
    - scenario: "Callback False, samples still arriving."
      expected_result: "_link_lost True — the socket's report is authoritative for a clean loss."
    - scenario: "No sample has ever arrived, callback True."
      expected_result: "_link_lost True; DISCONNECTED screen shown while connecting."
    - scenario: "Simulation mode on, callback False, no samples."
      expected_result: "_link_lost False; gauge drawn; no lost-link indication."
    - scenario: "Callback absent (None), samples arriving."
      expected_result: "_link_lost False — degrades to staleness alone, not to an assumption of connected."
    - scenario: "Callback absent, samples stopped past the timeout."
      expected_result: "_link_lost True."
    - scenario: "Callback raising."
      expected_result: "Treated as unavailable; staleness alone; no exception escapes."
    - scenario: "FLAPPING. Samples arriving once every 3 s, timeout 2 s."
      expected_result: "The screen does not alternate on every sample. State the observed behaviour explicitly — with recovery requiring two samples within the timeout, a 3 s cadence never recovers and the screen stays DISCONNECTED, which is correct for a link that cannot sustain a reading."
    - scenario: "Recovery after a genuine loss: samples resume at 20 Hz."
      expected_result: "Gauge returns once LINK_RECOVERY_SAMPLES have arrived within the timeout."
    - scenario: "A single sample arriving after a long gap, then nothing."
      expected_result: "No recovery — one sample is not evidence of a link."
    - scenario: "_current_view_key across a link-state change."
      expected_result: "The key differs, so regions re-register and the DISCONNECTED screen's controls are live."
    - scenario: "The DISCONNECTED screen's Setup and Simulate controls when reached by link loss."
      expected_result: "Both act."
    - scenario: "OPTIONS and ACKNOWLEDGEMENT with the link lost."
      expected_result: "Still reachable and still drawn — link state does not gate them."
    - scenario: "Normal operation before and after the change."
      expected_result: "No visible difference while data flows."
  regression_scope:
    - "tests/display/ — once populated per ai/task.md §8.2."
    - "On the target: power down the adapter mid-session; confirm the screen changes within about two seconds and the indicator turns red."
    - "On the target: restore adapter power; confirm the gauge returns."
    - "On the target: simulation mode with no adapter present; confirm no lost-link indication."
    - "On the target: swipe to OPTIONS with the adapter down; confirm settings remain reachable."
  validation_criteria:
    - "python -m py_compile on both files passes."
    - "pytest tests/ passes with no new failures."
    - "get_thread_status('obd_protocol') is not used to determine connection status or the disconnected screen anywhere in manager.py."
    - "_link_lost returns False whenever _sim_mode is set, unconditionally."
    - "comm/ is byte-identical."

implementation:
  implementation_steps:
    - step: "Write the acceptance test first — callback True, samples stopped — and confirm it fails against the current code, which shows the gauge."
      owner: "Claude Code"
    - step: "Add the state, the constants and the sample timestamp."
      owner: "Claude Code"
    - step: "Add _link_lost with the hysteresis latch."
      owner: "Claude Code"
    - step: "Convert both call sites and the view key member."
      owner: "Claude Code"
    - step: "Inject the callback at both app.py sites, guarded."
      owner: "Claude Code"
    - step: "Compile checks and the full assertion set, including the flapping case."
      owner: "Claude Code"
    - step: "On the target: power down the adapter mid-session and confirm the screen and indicator both change."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the thread-status
    proxy and with it the defect. No persisted state is involved.
  deployment_notes: >
    Visible and intended: with no adapter the instrument now shows the
    DISCONNECTED screen rather than a gauge. On a bench without an
    adapter that is the expected state, not a fault — simulation mode is
    the route to a working display.

verification:
  implemented_date: "2026-08-05"
  implemented_by: "Claude Code, per prompt-4d9e2f18 (commits dd49e17, 62af231)"
  verification_date: "2026-08-07"
  verified_by: "Claude Code (source re-check); William Watson (gtach.local)"
  test_results: >
    Report: acceptance test discriminates cleanly, pytest tests/ 11
    passed. Source re-check confirms _link_lost, LINK_LOSS_TIMEOUT and
    _last_sample_ts present and wired at every cited call site. William
    confirmed 2026-08-07 that GTach functions correctly on gtach.local.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-6481f8ce"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-4d9e2f18"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-4d9e2f18, implementing the operator's decisions of 2026-08-05: detection by socket state OR staleness, presentation by falling back to the DISCONNECTED screen."
      - "Recorded flapping as the design risk and specified recovery as two samples within the loss timeout rather than one, with the sporadic-sample behaviour stated explicitly rather than left to emerge."
      - "Recorded that an absent callback degrades to staleness alone rather than assuming connected, assuming connected being the defect this change exists to remove."
      - "Recorded that stopping the OBD thread on transport loss — which would make the existing test correct — was rejected as trading a display defect for a recovery defect."
      - "Recorded that the view key's disconnected member is corrected rather than added, and must be, or the DISCONNECTED screen's controls would be drawn and dead."

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
| 1.0 | 2026-08-05 | Initial change document coupled to issue-4d9e2f18. Replaces the thread-status proxy with a link-state test combining transport connectivity and data staleness, with recovery hysteresis. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation and verification recorded, confirmed by source re-check. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
