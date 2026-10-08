Created: 2026 October 07

# Change: Low-Severity Corrections

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-4005360c"
  title: "Fourteen small corrections (A12, A13, A16, A18, B07, B09, B10, B12, C10, C13, C15, C16, D08, D11) and a CLAUDE.md rule 8 clarification"
  date: "2026-10-07"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-4005360c"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-4005360c"
  description: "Resolves issue-4005360c."

scope:
  summary: "One edit per finding, each local to its module."
  affected_components:
    - name: "Modules listed in issue-4005360c affected_scope"
      file_path: "src/gtach/"
      change_type: "modify"
    - name: "CLAUDE.md §4 rule 8"
      file_path: "CLAUDE.md"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_low_defects.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Dead code (change-cd5ec050)."
    - "Behaviour beyond each named defect."

rational:
  problem_statement: "See issue-4005360c."
  proposed_solution: >
    A12 tcp_transport._open: on any exception from connect, close the
    socket and re-raise (mirror rfcomm.py).

    A13 SimBluetoothPairing: clear the relevant cancel event at the start
    of each discovery and each pairing operation.

    A16 transport.py: rename ConnectionError → TransportConnectionError
    and TimeoutError → TransportTimeoutError; update every reference in
    src/ and tests/.

    A18 system_bluetooth: after process.kill() call process.communicate()
    (or wait) to reap; after terminate(), wait(timeout=3) then kill and
    wait if still running; guard the reader's dict with a lock and return
    a copy taken under it.

    B07 watchdog.py: replace the bare `except:` with `except Exception:`.

    B09 OBDTransport: add a read-only property retry_delay returning
    getattr(self, '_retry_delay', 5.0). app.py passes
    retry_delay=self._transport.retry_delay to reconnect_indefinitely at
    both thread creations. The display's existing getattr(..., 'retry_delay')
    then returns the real value.

    B10 main.py: `_start_handler: Optional[logging.Handler] = None`,
    `_debug_handler: Optional[logging.Handler] = None`. app.py:
    `config_path: Optional[str] = None`; run() annotated `-> None`.

    B12 app.py: `self._obd_lock = threading.Lock()` in __init__; the
    _obd_started check-and-set in _on_setup_complete and the reset in
    _re_enter_setup happen under it (no other call under the lock).

    C10 ConfigStore.load: a coerced fps_limit outside FPS_LIMIT_RANGE or
    touch_long_press outside TOUCH_LONG_PRESS_RANGE is replaced by its
    default with a warning.

    C13 splash.py: _font_render_times becomes collections.deque(maxlen=100);
    the progress log condition becomes a 0.5 s rate limit on a monotonic
    timestamp and logs at DEBUG; every `elapsed / self.duration` returns
    1.0 when self.duration <= 0.

    C15 typography.get_rpm_large_font: return a bold font that is not the
    shared cached instance (create and cache it under a separate key, or
    a new pygame.font.Font object); never call set_bold on a cached font.
    manager.handle_touch_event logs at DEBUG.

    C16 Replace time.time() with time.monotonic() wherever the value is
    used only for a duration or comparison: display/touch.py,
    touch_interface.py TouchEvent timestamp, input/touch_coordinator.py,
    setup_components/state/coordinator.py interaction times,
    async_operations.py start/end times and cleanup ages, splash.py
    timing. Leave time.time() where the value is shown, logged as a
    timestamp, or used as a simulation seed (manager.py sine, obd.py
    OBDResponse.timestamp, sim_transport.py).

    D08 device_surfaces.py: read signal_strength (the setup model field)
    instead of rssi at both sites.

    D11 rendering engine cleanup: set self.fb and self.fb_dev to None
    after closing; the write path already checks for None.

    Rule 8 CLAUDE.md: append "A lock that exists to serialise access to
    one file may be held across that file's read or write (DeviceStore,
    change-453f0a80); it must still never be held across a callback or a
    call into another component." Version History row.
  alternatives_considered: []
  benefits:
    - "Leaks closed; simulation usable after Cancel; signal bars visible; durations immune to clock steps."
  risks:
    - risk: "A16 rename misses a reference."
      mitigation: "grep for the old names is a success criterion."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits."
  code_changes:
    - component: "Various"
      file: "src/gtach/"
      change_summary: "One edit per finding."
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "gtach.comm.transport.ConnectionError / TimeoutError"
      change_type: "signature"
      details: "Renamed to TransportConnectionError / TransportTimeoutError."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "One focused unit test per item where behaviour changes."
  test_cases:
    - scenario: "A12: TCPTransport._open with socket.connect raising."
      expected_result: "close() called; exception propagates."
    - scenario: "A13: cancel_discovery, then discover again."
      expected_result: "Second discovery reports devices."
    - scenario: "A16: import gtach.comm.transport."
      expected_result: "No attribute ConnectionError/TimeoutError defined by the module; Transport* names exist."
    - scenario: "B09: RFCOMMTransport(mac, retry_delay=7.0).retry_delay."
      expected_result: "7.0."
    - scenario: "B12: _on_setup_complete from two threads simultaneously."
      expected_result: "_start_obd called once."
    - scenario: "C10: ConfigStore.load with fps_limit 0 and touch_long_press 9."
      expected_result: "30 and 1.0; warnings."
    - scenario: "C13: splash with duration 0."
      expected_result: "Progress 1.0; no ZeroDivisionError."
    - scenario: "C15: get_rpm_large_font twice and the cached base font."
      expected_result: "The base cached font is not bold."
    - scenario: "D08: render a device item with signal_strength -60."
      expected_result: "get_signal_bars called with -60."
    - scenario: "D11: cleanup()."
      expected_result: "fb and fb_dev are None."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Edits and tests."
      owner: "tactical"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Signal bars shown on DEVICE_LIST (Session E; small, tracked separately in task.md); simbt discovery after Cancel covered by tests/test_low_defects.py::TestSimPairingCancelIsPerRun; real discovery after Cancel passed on the Pi."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-cd5ec050"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-4005360c"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-4005360c iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in 2ade5a3769ce5396447b6526328a9b153af90182."
  - version: "1.3"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Verified on device; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial change document. Low-severity corrections. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in 2ade5a3769ce5396447b6526328a9b153af90182. |
| 1.3 | 2026-10-08 | Verified on device; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
