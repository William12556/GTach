# Change: Communication Layer Corrections

Created: 2026 November 11

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-b4f9607a"
  title: "Close a link that connects after disconnect; treat OSError as serial link loss; discovery fallback and wait sizing; effective pairing cancellation; truthful device-store results; separate simulation store path; quieter OBD start-up; non-joining OBD stop function"
  date: "2026-11-11"
  author: "William Watson"
  status: "implemented"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b4f9607a"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b4f9607a"
  description: "Resolves issue-b4f9607a. Run 2 of proposal-71ab3751."

scope:
  summary: "Ten edit groups, all in src/gtach/comm, plus tests."
  affected_components:
    - name: "OBDTransport"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "SerialTransport"
      file_path: "src/gtach/comm/serial_transport.py"
      change_type: "modify"
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "BluetoothPairing"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "SystemBluetoothManager, discover_devices"
      file_path: "src/gtach/comm/system_bluetooth.py"
      change_type: "modify"
    - name: "DeviceStore, set_device_store_path"
      file_path: "src/gtach/comm/device_store.py"
      change_type: "modify"
    - name: "SimTransport"
      file_path: "src/gtach/comm/sim_transport.py"
      change_type: "modify"
    - name: "BluetoothDevice"
      file_path: "src/gtach/comm/models.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_comm_layer_defects.py (new), tests/test_sim_transport.py"
      change_type: "add"
  affected_designs:
    - "design-a6b7c8d9-component_comm_device_store"
    - "design-b1c2d3e4-component_comm_transport"
  out_of_scope:
    - "Any file outside src/gtach/comm and tests/."
    - "Callers of the new or changed interfaces (app.py: run 3; display/setup*: run 4; display/manager.py: run 5)."
    - "A12: no code change beyond a comment."
    - "Automatic recovery from the stuck Bluetooth state (ai/task.md row; evidence first)."

rational:
  problem_statement: "See issue-b4f9607a."
  proposed_solution: >
    EDIT A (A01) — OBDTransport.connect: after _open() returns a
    handle, take _lock and test _shutdown. If set, do not store the
    handle: release the lock, close the handle through the existing
    discard path, leave the state DISCONNECTED and return False.
    Otherwise store it as now. disconnect() is unchanged.

    EDIT B (A03, A04) — connect: a refused connect (ECONNREFUSED) does
    not increment _consecutive_connect_failures. send_command's
    _IO_ERRORS handler records _last_failure_cause using
    _classify_connect_error(e), under _lock, with the state change.

    EDIT C (A02) — SerialTransport._IO_ERRORS becomes
    (serial.SerialException, OSError). _discard_input does not catch
    OSError; it propagates to send_command's _IO_ERRORS handler, which
    drops the link.

    EDIT D (A05, B06 obd part) — OBD initialisation: when the 0100
    reply lacks '4100', log at WARNING without a traceback and return
    False; do not raise. Rate-limit that record to the first occurrence
    and then at most once per 60 s (monotonic clock), and log one INFO
    record when the vehicle answers again. Other initialisation
    failures stay at ERROR with exc_info.
    OBDProtocol.stop gains timeout: float = 5.0 (join bound; 0 means
    signal only). The thread is registered with a stop function that
    signals without joining, so ThreadManager.stop_thread's own timeout
    is the bound. Direct callers of stop() keep the 5 s join.

    EDIT E (A06, A07) — pairing.py: the wait for one discovery chunk is
    not shorter than the back end's own limit for that chunk
    (system back end: duration * 2 + 5 s) plus 1 s, so a chunk is not
    abandoned while its scan is still running.
    system_bluetooth.py: discover_devices logs hcitool's return code and
    the first line of stderr at WARNING when the return code is not 0.
    The module-level discover_devices reuses one lazily created
    SystemBluetoothManager instead of building one per call.

    EDIT F (discovery fallback, decision D1; contract for run 4) —
    discover_elm327_devices keeps its signature. With
    show_all_devices=False, devices classified UNKNOWN that have a
    non-empty name are collected in a second list during the scan
    instead of being discarded. If, after the last chunk, no ELM327 or
    compatible device was found, the scan was not cancelled and the
    second list is not empty, the method logs one INFO record, calls
    device_found_callback for each of those devices and returns them.
    Every returned device then has device_classification
    DeviceType.UNKNOWN, which is how a caller recognises the fallback.
    No second scan is run. SimBluetoothPairing is unchanged.

    EDIT G (X01 comm part; contract for run 4) — pair_device tests
    _cancel_pairing before the connect and again after it returns; when
    set, it closes the socket and returns False without calling
    status_callback. cancel_discovery() keeps its per-chunk effect;
    after a cancel, discover_elm327_devices makes no further callback
    (no fallback, no final progress call) and returns what it has.

    EDIT H (A09 store part) — DeviceStore._save_device_locked and
    _remove_device_locked apply the change to a copy, save, and replace
    self.config only if the save succeeded; on failure memory is
    unchanged and False is returned. remove_device returns False when
    the device is absent or the save failed. Docstrings state the
    return contract.

    EDIT I (A10, decision D5; contract for run 3) — device_store.py
    gains set_device_store_path(path: Optional[str]) -> None: it sets
    the path the shared instance is created with (None restores the
    default) and discards the current shared instance.
    get_device_store() uses that path. SimBluetoothPairing keeps
    calling get_device_store(). Until run 3 calls the new function for
    'simbt' sessions, behaviour is unchanged.

    EDIT J (A11, A12, last_connected, F03) — SimTransport.connect does
    not clear _shutdown; the two stale comments state the 60 s period
    and the midpoint start. A12: one comment at the discard site
    records the known limit (a reply arriving after the discard is
    read as the next reply; the PID check rejects other PIDs).
    BluetoothDevice: the str-to-datetime conversion of last_connected
    moves to from_dict (or the equivalent YAML entry point), the field
    stays Optional[datetime], and the type: ignore and TODO markers at
    that site are removed. tests/test_sim_transport.py: the wall-clock
    step test asserts the value at a time where it differs from t = 0
    (t = 15 s gives 6500 RPM, '41 0C 65 90').

    COMMENT RULE — In every comm file edited, comments that narrate
    history are reduced to the current behaviour plus at most one issue
    reference (CLAUDE.md section 4).
  alternatives_considered:
    - option: "A second, unfiltered scan for the fallback (decision D1 as first worded)."
      reason_rejected: "The first scan already returns the names; a second pass adds up to discovery_timeout with no new information. Recorded for approval in design-a3b4c5d6 section 4.3."
    - option: "A10: SimBluetoothPairing constructs its own DeviceStore."
      reason_rejected: "The setup interface and the application read the shared instance; two instances would disagree."
    - option: "A12: discard by time before each command."
      reason_rejected: "Delays every command at 20 to 50 Hz."
  benefits:
    - "No leaked link after setup re-entry; link loss detected on serial."
    - "Adapters with unlisted names can be selected without a toggle."
    - "Run 4 can cancel discovery and pairing through existing methods."
  risks:
    - risk: "EDIT A closes a handle that a concurrent caller expects."
      mitigation: "The handle was never published; the test covers disconnect during a blocking _open."
    - risk: "EDIT C: an OSError that is not a link loss now drops the link."
      mitigation: "The reconnect loop restores it; the cause is logged."
    - risk: "EDIT F lists unrelated named devices (phones, headsets)."
      mitigation: "Only when no ELM327-like device was found; run 4 labels the list."
    - risk: "EDIT E lengthens a chunk wait."
      mitigation: "The wait ends when the scan ends; only the abandon point moves."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits; one new module-level function."
  code_changes:
    - component: "comm"
      file: "transport.py, serial_transport.py, obd.py, pairing.py, system_bluetooth.py, device_store.py, sim_transport.py, models.py"
      change_summary: "EDITS A to J"
      functions_affected:
        - "OBDTransport.connect"
        - "OBDTransport.send_command"
        - "SerialTransport._discard_input"
        - "OBDProtocol.stop"
        - "OBDProtocol initialisation"
        - "BluetoothPairing.discover_elm327_devices"
        - "BluetoothPairing.pair_device"
        - "SystemBluetoothManager.discover_devices"
        - "DeviceStore._save_device_locked"
        - "DeviceStore._remove_device_locked"
        - "set_device_store_path (new)"
        - "SimTransport.connect"
        - "BluetoothDevice.from_dict"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "OBDProtocol.stop"
      change_type: "signature"
      details: "stop(timeout: float = 5.0)"
      backward_compatible: "yes"
    - interface: "BluetoothPairing.discover_elm327_devices"
      change_type: "contract"
      details: "May return UNKNOWN-classified devices when no ELM327-like device was found (EDIT F)."
      backward_compatible: "yes"
    - interface: "gtach.comm.device_store.set_device_store_path"
      change_type: "signature"
      details: "New function (EDIT I)."
      backward_compatible: "yes"
    - interface: "DeviceStore.save_device, remove_device"
      change_type: "contract"
      details: "Return False when the change did not reach disk; memory unchanged in that case."
      backward_compatible: "yes"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-cfa4e617"
      relationship: "precedes"

testing_requirements:
  test_approach: "Unit tests with stub handles, stub subprocess and temporary store files."
  test_cases:
    - scenario: "A01: a transport whose _open blocks on an event; call disconnect(), then release _open with a handle."
      expected_result: "connect returns False; the handle's close was called; state DISCONNECTED; is_connected False."
    - scenario: "A03: six refused connects, then a timeout."
      expected_result: "The cause is not the wedge cause."
    - scenario: "A04: send_command with a handle whose write raises ConnectionResetError."
      expected_result: "State DISCONNECTED and a non-empty failure cause."
    - scenario: "A02: SerialTransport with a handle whose in_waiting raises OSError(EIO)."
      expected_result: "send_command returns None, the link is dropped, no 'Unexpected error' record."
    - scenario: "A05: initialisation with 'NO DATA' for 0100, three times within 60 s, then a valid reply."
      expected_result: "One WARNING without exc_info; no ERROR; one INFO on recovery."
    - scenario: "B06: ThreadManager.stop_thread('obd_protocol', timeout=0.5) with a protocol loop that ignores the event for 2 s."
      expected_result: "Returns within about 0.5 s plus scheduling; stop(timeout=5.0) called directly still joins."
    - scenario: "A06: a stub back end whose scan takes chunk_duration + 6 s (time patched)."
      expected_result: "The chunk's devices are used; no second scan starts while the first runs."
    - scenario: "A07: subprocess.run stub returning code 1 and stderr text."
      expected_result: "Empty list and one WARNING naming the code; one manager across two module-level calls."
    - scenario: "Fallback: scan returns only devices named 'Phone' and 'Speaker'."
      expected_result: "Both returned with classification UNKNOWN; callback called for each; one INFO record."
    - scenario: "Fallback not used: scan returns 'OBDII' and 'Phone'."
      expected_result: "Only the ELM327-like device is returned."
    - scenario: "Fallback after cancel_discovery()."
      expected_result: "No fallback devices and no further callbacks."
    - scenario: "X01: cancel_pairing() before pair_device connects (stub socket)."
      expected_result: "Returns False; status_callback not called; socket closed."
    - scenario: "A09: save_device and remove_device with _save_config patched to return False."
      expected_result: "False returned; get_primary_device unchanged."
    - scenario: "A10: set_device_store_path(tmp/devices-sim.yaml), then get_device_store().save_device."
      expected_result: "The temporary file is written; the default path is untouched; set_device_store_path(None) restores the default."
    - scenario: "A11: SimTransport.disconnect() then connect()."
      expected_result: "_shutdown stays set."
    - scenario: "last_connected: from_dict with an ISO string, with None and with an invalid string."
      expected_result: "datetime, None, None."
    - scenario: "F03: sweep at t = 15 s with wall-clock steps."
      expected_result: "'41 0C 65 90'."
  regression_scope:
    - "tests/test_sim_transport.py, tests/test_lifecycle_sim.py, tests/test_medium_defects.py and all transport, pairing and device-store tests."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes; mypy src/ reports no issues."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to J and tests."
      owner: "tactical"
    - step: "Device session A: A01 procedure, link loss and reconnect, EBUSY re-test with the process's sockets listed."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-11-11"
  implemented_by: "Claude Code"
  verification_date: ""
  verified_by: ""
  test_results: "Commit 963fd0fc82ccead532d1192ef99aee25e23f26aa: pytest 619 passed (30 new in tests/test_comm_layer_defects.py); mypy src/ no issues (worker's results, report-b4f9607a section 4)."
  issues_found:
    - "EDIT G: pair_device still clears _cancel_pairing on entry and makes the initial CONNECTING status call before the first check; a cancel issued before pair_device starts has no effect. Accepted: run 4 ignores completions of cancelled operations. See report-b4f9607a section 6."
    - "EDIT E: a chunk may now wait up to 14 s before it is abandoned (previously 9 s), so a scan whose hcitool calls hang can take longer in total. To be measured in device session A."
    - "reset_device_store() does not reset the path set by set_device_store_path(); relevant to test isolation only."

traceability:
  design_updates:
    - "design-a6b7c8d9 (device store): return contract and set_device_store_path. Planner, in the design refresh after run 5."
    - "design-b1c2d3e4 (transport): shutdown test in connect(), refused-connect counter rule, send-time failure cause. Planner, in the design refresh after run 5."
  related_changes:
    - change_ref: "change-042dd7ff"
      relationship: "follows; calls set_device_store_path and relies on the non-joining OBD stop function"
    - change_ref: "change-34781bfe"
      relationship: "follows; uses the fallback result, cancel_discovery, cancel_pairing and the save_device result"
    - change_ref: "change-2550e4ee"
      relationship: "follows; uses the remove_device result"
  related_issues:
    - issue_ref: "issue-b4f9607a"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-b4f9607a iteration 1."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Implemented in 963fd0fc82ccead532d1192ef99aee25e23f26aa; awaiting device session A."

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
| 1.0 | 2026-11-11 | Initial change document. EDITS A to J. |
| 1.1 | 2026-11-11 | Approved for implementation. |
| 1.2 | 2026-11-11 | Implemented in 963fd0f; awaiting device session A. |

---

Copyright (c) 2026 William Watson. MIT License.
