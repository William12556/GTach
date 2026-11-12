# Change: Engine Off Display State

Created: 2026 November 12

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-b29cbd71"
  title: "Show 'Engine off' when the adapter is connected and reports a silent vehicle; re-check the vehicle when samples stop during polling"
  date: "2026-11-12"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b29cbd71"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b29cbd71"
  description: "Resolves issue-b29cbd71 per design-e5f6a7b8 v1.1 section 6.3 and design-b8c9d0e1 v1.3 section 5.4."

scope:
  summary: "obd.py exposes silent-vehicle evidence and re-checks the vehicle after 2 s without samples; manager.py derives the engine-off condition and draws it; app.py wires one callback; tests."
  affected_components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication._start_setup_mode, _start_normal_mode"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_engine_off_state.py (new)"
      change_type: "add"
  affected_designs:
    - "design-e5f6a7b8-component_comm_obd_protocol"
    - "design-b8c9d0e1-component_display_manager"
  out_of_scope:
    - "_link_lost(), LINK_LOSS_TIMEOUT, LINK_RECOVERY_SAMPLES: unchanged."
    - "The initialisation path at connect (ATZ, settle, AT configuration) and its retry delay: unchanged."
    - "The DISCONNECTED screen, its buttons and cause line: unchanged."
    - "The A05 'Vehicle not answering' log rate limit and _vehicle_silent's logging role: unchanged."
    - "Simulation mode: unchanged; it never shows Engine off."
    - "Adapter power saving, sleep, or any engine-off timeout."

rational:
  problem_statement: "See issue-b29cbd71."
  proposed_solution: >
    EDIT A — obd.py.
    (1) Add self._vehicle_silent_ts: Optional[float] = None and the
    public method last_vehicle_silent_ts() -> Optional[float], which
    returns it. Separate from _vehicle_silent, which keeps its logging
    role only.
    (2) Evidence rule (design-e5f6a7b8 section 6.3.1). A 0100 reply
    that is not None and lacks 4100 sets _vehicle_silent_ts =
    time.monotonic(). A None reply never sets it, whether or not the
    transport is connected. A 4100 reply sets it to None. The existing
    _report_no_vehicle logging and the issue-146491ba lost-link branch
    are otherwise unchanged. The classification is one helper used by
    both the initialisation path and the re-check of (4).
    (3) Clearing. _vehicle_silent_ts becomes None on a valid 010C
    sample, whenever the protocol loop finds the transport not
    connected, on the lost-link branch of _initialize_protocol, and in
    _signal_stop.
    (4) Silence during polling (section 6.3.3). The poll loop records
    the monotonic time of the last valid sample (start of polling
    counts as one). When no valid sample has arrived for
    _RPM_SILENT_RECHECK_S = 2.0 s and the transport is connected, log
    INFO 'No RPM data for 2.0s - re-checking vehicle' and enter the
    re-check: send 0100 with _INIT_0100_TIMEOUT_S, classify per (2);
    on 4100 log INFO 'Vehicle answered 0100 - polling resumed' and
    return to polling; otherwise wait _INIT_RETRY_DELAY_S
    (shutdown-aware, heartbeat updated) and repeat while the transport
    is connected. The re-check sends no ATZ, applies no settle delay,
    repeats no AT configuration command and leaves
    _adapter_initialised unchanged. A None 0100 reply in the re-check
    is reported through _report_no_vehicle as now (rate-limited
    WARNING) and does not set the timestamp.

    EDIT B — manager.py.
    (1) Class constants ENGINE_OFF_FRESHNESS_S = 15.0 and
    ENGINE_OFF_TEXT = "Engine off". Attributes
    _vehicle_silent_callback: Optional[Callable[[], Optional[float]]]
    = None and _frame_engine_off = False, assigned in __init__ before
    any step that can fail.
    (2) _engine_off() -> bool per design-b8c9d0e1 section 5.4.1: True
    only when _frame_link_lost is True, the link-connected callback
    returns exactly True, the silent callback returns a timestamp no
    older than ENGINE_OFF_FRESHNESS_S, and simulation mode is off.
    Every failure (absent or raising callback, non-float result)
    returns False. Evaluated once per frame in _display_loop,
    immediately after _frame_link_lost.
    (3) Precedence (section 5.4.2). The three sites that decide the
    DISCONNECTED condition — _render_normal_modes,
    _register_view_regions and _draw_status_indicator — use
    `_frame_link_lost and not _frame_engine_off`.
    _current_view_key() adds _frame_engine_off. _draw_status_indicator
    shows ConnectionStatus.CONNECTING (yellow) when _frame_engine_off.
    (4) Engine off screen (section 5.4.3). In RADIAL with
    _frame_engine_off, _draw_radial_mode draws the gauge at 0 RPM and
    renders ENGINE_OFF_TEXT in white at the centre in place of the
    numeric readout, in a font whose rendered width of
    ENGINE_OFF_TEXT is 180 px or less. On the transition into engine
    off, reset _last_rpm = 0, _rpm_display = 0.0, _rpm_last_ts = None,
    _active_band = 0, and log INFO 'Engine off - adapter reports no
    vehicle'; on the transition out, log INFO 'Engine off cleared'.
    No touch regions are registered for the engine-off view.

    EDIT C — app.py.
    In both _start_setup_mode and _start_normal_mode, beside
    _link_connected_callback, set _vehicle_silent_callback to a
    guarded lambda returning
    getattr(self, "_obd", None).last_vehicle_silent_ts() when _obd
    exists, else None.
  alternatives_considered:
    - option: "Send a sentinel through the sample queue."
      reason_rejected: "The queue carries real samples only; a synthetic message would count as evidence of a live adapter (issue-4d9e2f18)."
    - option: "Treat a 0100 timeout with the link up as engine off."
      reason_rejected: "An adapter that has lost power without closing its socket also times out; the display would show Engine off for a missing adapter."
    - option: "Re-run the full initialisation (with ATZ) after silence during polling."
      reason_rejected: "Resets the adapter and its protocol search for no benefit; 0100 alone classifies the vehicle."
  benefits:
    - "A parked car with the adapter powered reads as Engine off, not as a fault."
    - "DISCONNECTED keeps its meaning: adapter lost or state unknown."
  risks:
    - risk: "Switching off while driving shows DISCONNECTED briefly (LINK_LOSS_TIMEOUT 2.0 s, then up to one 0100 search) before Engine off."
      mitigation: "Accepted; a brief fail-safe indication. The report states the measured gap from tests."
    - risk: "At connect, one initialisation cycle (ATZ, AT commands, 0100 search, 2.0 s retry delay) could exceed ENGINE_OFF_FRESHNESS_S on a slow vehicle search, making the display alternate."
      mitigation: "Emulator ATZ is about 0.5 s and 0100 is bounded at 6 s, so a cycle is under about 9 s. The device check measures the interval between silent replies."
    - risk: "A stalled engine with the ignition on may not answer 010C on some vehicles."
      mitigation: "It would then show Engine off, which is accurate. Confirmed in the in-car test."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits; no new modules in src/."
  code_changes:
    - component: "comm"
      file: "obd.py"
      change_summary: "EDIT A"
      functions_affected:
        - "OBDProtocol.__init__, _protocol_loop, _initialize_protocol, _signal_stop"
        - "OBDProtocol.last_vehicle_silent_ts (new)"
      classes_affected: []
    - component: "display"
      file: "manager.py"
      change_summary: "EDIT B"
      functions_affected:
        - "DisplayManager.__init__, _display_loop, _render_normal_modes, _register_view_regions, _current_view_key, _draw_radial_mode, _draw_status_indicator"
        - "DisplayManager._engine_off (new)"
      classes_affected: []
    - component: "app"
      file: "app.py"
      change_summary: "EDIT C"
      functions_affected:
        - "GTachApplication._start_setup_mode, _start_normal_mode"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "gtach.comm.obd.OBDProtocol.last_vehicle_silent_ts"
      change_type: "add"

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests with a stub transport for OBDProtocol (as in tests/test_session_b_findings.py) and a DisplayManager under SDL_VIDEODRIVER=dummy with injected callbacks and a controllable monotonic clock."
  test_cases:
    - scenario: "Init: 0100 replies 'NO DATA', transport connected."
      expected_result: "False; last_vehicle_silent_ts() is a float."
    - scenario: "Init: 0100 replies 'SEARCHING...UNABLE TO CONNECT' / 'BUS INIT: ...ERROR' / '?'."
      expected_result: "Timestamp set for each."
    - scenario: "Init: 0100 returns None, transport connected."
      expected_result: "False; WARNING as now; timestamp not newly set (unchanged)."
    - scenario: "Init: 0100 returns None, transport disconnected."
      expected_result: "False; timestamp None; existing 146491ba assertions still hold."
    - scenario: "Init: 0100 replies '4100...' after a silent reply."
      expected_result: "True; timestamp None."
    - scenario: "Polling: 010C replies 'NO DATA' for more than 2.0 s, transport connected; re-check 0100 replies 'NO DATA'."
      expected_result: "One INFO re-check record; 0100 sent; no ATZ or AT command sent; timestamp set; _adapter_initialised unchanged."
    - scenario: "Polling re-check: 0100 replies 4100."
      expected_result: "Polling resumes (010C sent again); timestamp None."
    - scenario: "Polling: 010C times out (None) for more than 2.0 s, transport connected; re-check 0100 times out."
      expected_result: "Timestamp stays None."
    - scenario: "Polling: valid sample after a silent period."
      expected_result: "Timestamp None."
    - scenario: "_signal_stop."
      expected_result: "Timestamp None."
    - scenario: "Display: link lost, transport callback True, timestamp age 1 s."
      expected_result: "_frame_engine_off True; no DISCONNECTED render; status CONNECTING; ENGINE_OFF_TEXT rendered; no RPM figure."
    - scenario: "Display: timestamp age 16 s."
      expected_result: "_frame_engine_off False; DISCONNECTED."
    - scenario: "Display: transport callback False, None, or raising; silent callback None, raising, or absent."
      expected_result: "_frame_engine_off False in every case."
    - scenario: "Display: simulation mode with fresh timestamp."
      expected_result: "_frame_engine_off False."
    - scenario: "Display: link up (samples flowing) with fresh timestamp."
      expected_result: "_frame_engine_off False; live gauge."
    - scenario: "Display: entry into engine off after a live 4500 RPM reading."
      expected_result: "_last_rpm 0, _rpm_display 0.0, _rpm_last_ts None, _active_band 0; one INFO record."
    - scenario: "Display: view key and regions."
      expected_result: "Key changes on entry; DISCONNECTED Setup/Reset regions not registered while engine off."
    - scenario: "ENGINE_OFF_TEXT width in the chosen font."
      expected_result: "180 px or less."
  regression_scope:
    - "tests/test_session_b_findings.py, the link-loss tests (issue-4d9e2f18), the OBD protocol tests, the display status-indicator tests."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes; mypy src/ reports no issues."

implementation:
  effort_estimate: "Medium"
  implementation_steps:
    - step: "EDITS A to C and tests."
      owner: "tactical"
    - step: "Device check with the emulator: engineoff at connect (Engine off within about 10 s, stays); car scenario (live gauge); emulator stopped while engine off (DISCONNECTED); car scenario restored (live gauge)."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Version increment at the owner's discretion."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates:
    - "design-e5f6a7b8 v1.1 section 6.3 and design-b8c9d0e1 v1.3 section 5.4 written before this change. Planner revises them if implementation deviates."
  related_changes:
    - change_ref: "change-146491ba"
      relationship: "extends the 0100 classification"
    - change_ref: "change-4d9e2f18"
      relationship: "extends the link-state derivation"
  related_issues:
    - issue_ref: "issue-b29cbd71"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-b29cbd71 iteration 1."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial change document. EDITS A to C. |

---

Copyright (c) 2026 William Watson. MIT License.
