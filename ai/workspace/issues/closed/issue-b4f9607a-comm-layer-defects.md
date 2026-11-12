# Issue: Communication Layer Defects

Created: 2026 November 11

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-b4f9607a"
  title: "A connect that completes after disconnect leaves the link open; serial unplug is not detected; discovery, pairing cancellation, device-store persistence, simulation and OBD start-up logging defects in comm/"
  date: "2026-11-11"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-b4f9607a"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-71ab3751 findings A01, A02 (medium), A03, A04, A05, A06, A07, A09, A10, A11, A12, F03 (low), the comm parts of X01 and B06, and the ai/task.md rows 'Bluetooth discovery fallback' (mechanism) and 'last_connected accepts str'."

affected_scope:
  components:
    - name: "OBDTransport.connect, send_command"
      file_path: "src/gtach/comm/transport.py"
    - name: "SerialTransport._IO_ERRORS, _discard_input"
      file_path: "src/gtach/comm/serial_transport.py"
    - name: "OBDProtocol initialisation, stop, thread registration"
      file_path: "src/gtach/comm/obd.py"
    - name: "BluetoothPairing.discover_elm327_devices, pair_device"
      file_path: "src/gtach/comm/pairing.py"
    - name: "SystemBluetoothManager.discover_devices; module discover_devices"
      file_path: "src/gtach/comm/system_bluetooth.py"
    - name: "DeviceStore save and remove; shared-instance path"
      file_path: "src/gtach/comm/device_store.py"
    - name: "SimBluetoothPairing.pair_device"
      file_path: "src/gtach/comm/sim_bluetooth.py"
    - name: "SimTransport.connect; comments"
      file_path: "src/gtach/comm/sim_transport.py"
    - name: "BluetoothDevice.last_connected"
      file_path: "src/gtach/comm/models.py"
    - name: "test_rpm_sweep_ignores_wall_clock_steps"
      file_path: "tests/test_sim_transport.py"
  designs:
    - "design-b1c2d3e4-component_comm_transport"
    - "design-a6b7c8d9-component_comm_device_store"
  version: "0.4.13"

reproduction:
  prerequisites: "Pi with the emulator for A01; USB ELM327 for A02; otherwise from source or tests with stubs."
  steps:
    - "A01: audit-71ab3751 section 6.0."
    - "A02: run 'gtach --transport serial', unplug the adapter."
    - "A10: run 'gtach --transport simbt' on the Pi, complete simulated pairing, inspect config/devices.yaml."
    - "A05: power the OBD port with ignition off; read error.log."
  frequency: "A01 timing-dependent; A02 to be verified on hardware; others always"
  reproducibility_conditions: "From source."
  test_data: >
    A01: connect() stores the handle and sets CONNECTED after _open()
    without testing _shutdown; a disconnect() during a blocking _open()
    finds no handle, and the later handle is never closed.
    A02 (suspected): _IO_ERRORS is (serial.SerialException,);
    _discard_input reads in_waiting and catches only TypeError,
    ValueError, AttributeError; a raw OSError reaches send_command's
    generic handler, which neither drops the link nor counts a timeout.
    A03: refused connects increment _consecutive_connect_failures.
    A04: send_command's I/O handler records no _last_failure_cause.
    A05: a missing 4100 reply raises Exception and is logged at ERROR
    with a traceback on every retry cycle.
    A06: each discovery chunk waits chunk_duration + 5 = 9 s for a scan
    whose own limit is duration * 2 + 5 = 13 s; on expiry the results
    are dropped and the next chunk starts a concurrent scan.
    A07: discover_devices ignores hcitool's return code and stderr; the
    module-level discover_devices builds a SystemBluetoothManager per
    call, which runs 'bluetoothctl --version' each time.
    A09: _save_device_locked changes memory before saving;
    _remove_device_locked ignores _save_config()'s result.
    A10: SimBluetoothPairing saves its fake device as primary in the
    shared store.
    A11: SimTransport.connect clears _shutdown; two comments are stale.
    A12 (suspected): a late reply arriving after _discard_input is
    returned for the next command; a late 010C reply is accepted once.
    X01: pair_device never reads _cancel_pairing.
    B06: OBDProtocol registers stop as its stop function; stop joins
    for 5 s, so ThreadManager.stop_thread's timeout is not the bound.
    Discovery fallback: devices classified UNKNOWN are discarded, so an
    adapter with an unlisted name cannot be paired.
    last_connected: annotated Optional[datetime] but converted from str
    in __post_init__ under a type: ignore.
    F03: the test asserts the t = 30 s value, which equals the t = 0
    value.
  error_output: "A02 expected: 'Unexpected error during command send' with a traceback at the poll rate."

behavior:
  expected: "A transport never holds an open link after disconnect(); link loss is detected on every transport; discovery and pairing can be cancelled; persistence results are true; simulation does not write the real device store."
  actual: "As in test_data."
  impact: "A01: later connects to the adapter can fail with EBUSY until restart. A02: no reconnect after a serial unplug and a traceback per poll. A10: the real paired adapter is replaced by a fake address. Others: misleading logs or status."
  workaround: "A01: restart the service. A10: repeat setup."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Individual omissions; no common cause."
  technical_notes: >
    A01 consequence, A02, A06 and A12 are suspected: they depend on
    runtime or library behaviour that was not exercised. The proposed
    fixes are safe if the fault does not occur.
    A12 has no fix proposed: discarding by time would delay every
    command. It is recorded as a known limit in the code.
  related_issues:
    - issue_ref: "issue-5e7a03c4"
      relationship: "related. Failure-cause reporting."
    - issue_ref: "issue-d140121d"
      relationship: "related. Discovery chunking and pairing shutdown."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-b4f9607a."
  change_ref: "change-b4f9607a"
  resolved_date: "2026-11-11"
  resolved_by: "change-b4f9607a"
  fix_description: "connect() closes a handle that arrives after disconnect(); OSError is a serial link loss; refused connects no longer count towards the wedge cause; send-time I/O errors record a cause; a missing 4100 reply is a rate-limited WARNING; OBDProtocol.stop(timeout) with a non-joining registered stop function; discovery chunk wait covers the back end's limit, hcitool return code logged, one shared manager; same-scan fallback to named UNKNOWN devices; pairing and discovery honour cancellation; DeviceStore save and remove return truthful results; set_device_store_path(); SimTransport keeps _shutdown; last_connected parsed in from_dict only; F03 test corrected (commit 963fd0fc82ccead532d1192ef99aee25e23f26aa; report-b4f9607a). A12 recorded as a known limit in a comment."

verification:
  verified_date: "2026-11-12"
  verified_by: "William Watson"
  test_results: "Device session A (test-71ab3751-device-session-a steps A4 to A7 and A9): all checks passed. A01 race not provoked (unit test covers it); A02 not tested (no serial adapter); fallback not observable (no Bluetooth device in range), to be observed in session B."
  closure_notes: "Closed with the 71ab3751 series (version 0.5.0). A01 race and A02 (serial adapter) were not provoked on the device; unit tests cover them. Recovery from the stuck Bluetooth (EBUSY) state remains a separate ai/task.md row."

prevention:
  preventive_measures: "State stored after a blocking call is checked against the shutdown flag; persistence methods return what happened."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE, audit-71ab3751.]"
    - "After the fix: unit tests per change-b4f9607a."
    - "After the fix: device session A — A01 procedure of audit-71ab3751 section 6.0 leaves no RFCOMM socket open; link loss and reconnect work; EBUSY re-test."
    - "After the fix, if hardware is available: A02 unplug test."
  verification_results: "pytest 619 passed and mypy clean (worker's results). Device session A passed on 2026-11-12; see verification.test_results."

traceability:
  design_refs:
    - "design-b1c2d3e4-component_comm_transport"
    - "design-a6b7c8d9-component_comm_device_store"
  change_refs:
    - "change-b4f9607a"
  test_refs: []

notes: "Audit reference: audit-71ab3751 A01-A07, A09 (store part), A10-A12, F03, X01 (comm part), B06 (obd part). Run 2 of proposal-71ab3751."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial issue document."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Resolved by change-b4f9607a (963fd0fc82ccead532d1192ef99aee25e23f26aa); awaiting device session A."

  - version: "1.2"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Verified on device in session A."

  - version: "1.3"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Closed with the 71ab3751 series; moved to issues/closed/."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial issue document. A01-A07, A09-A12, F03, X01, B06, discovery fallback, last_connected. |
| 1.1 | 2026-11-11 | Resolved by change-b4f9607a (963fd0f); awaiting device session A. |
| 1.2 | 2026-11-12 | Verified on device in session A. |
| 1.3 | 2026-11-12 | Closed with the 71ab3751 series; moved to closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
