Created: 2026 April 30

# Issue: Sim Mode — Hardware-Free Full Application Testing

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [8.0 Resolution](<#8.0 resolution>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Prevention](<#10.0 prevention>)
- [11.0 Traceability](<#11.0 traceability>)
- [Version History](<#version history>)

---

```yaml
issue_info:
  id: "issue-c7e2f1a9"
  title: "Sim Mode — Hardware-Free Full Application Testing"
  date: "2026-04-30"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-c7e2f1a9"
    change_iteration: 1
```

---

## 1.0 Issue Information

Enhancement request to add two simulation transport modes enabling full application testing without
real Bluetooth hardware, an ELM327 adapter, or a running TCP emulator process.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: ""
  description: >
    No mechanism currently exists to exercise the full GTach application — OBD display pipeline
    and Bluetooth setup wizard — without physical hardware or a running emulator. This blocks
    UI and integration testing on macOS and Pi when hardware is unavailable.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "OBDTransport / select_transport"
      file_path: "src/gtach/comm/transport.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
    - name: "CLI argument parser"
      file_path: "src/gtach/main.py"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "SimTransport (new)"
      file_path: "src/gtach/comm/sim_transport.py"
    - name: "SimBluetoothPairing (new)"
      file_path: "src/gtach/comm/sim_bluetooth.py"
  designs:
    - design_ref: "design-gtach-master.md"
    - design_ref: "design-7d3e9f5a-domain_comm.md"
  version: "0.2.0"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: >
    macOS development environment with GTach v0.2.0 installed. No ELM327 hardware
    and no running ircama TCP emulator.
  steps:
    - "Attempt to run GTach with --transport tcp targeting a non-running emulator."
    - "Observe connection failure — no RPM display possible."
    - "Attempt to test Bluetooth setup wizard — no hardware discoverable."
  frequency: "always"
  reproducibility_conditions: "Any environment without ELM327 hardware or active TCP emulator."
  preconditions: "No paired device in device store (to trigger setup mode)."
  test_data: ""
  error_output: "TCPTransport: Failed to connect to TCP device localhost:35000"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behavior

```yaml
behavior:
  expected: >
    Two new --transport flag values activate fully simulated modes requiring no external
    hardware or processes:
      simtcp — SimTransport only; Bluetooth setup uses real hardware path.
      simbt  — SimTransport + SimBluetoothPairing; all hardware paths simulated.
    SimTransport generates synthetic ELM327 responses. RPM follows a sine-shaped sweep
    800->6500->800 RPM, ~12 s cycle, at 10 Hz, simulating engine rev-up and cool-down.
    SimBluetoothPairing returns 4 scripted fake devices after a simulated scan delay
    (~3 s with progress callbacks) and simulates pair_device with ~2 s latency,
    succeeding ~80% of the time and failing ~20% to exercise the failure path.
  actual: >
    No simulation modes exist. All transport modes require live hardware or a running
    external emulator process. Bluetooth setup cannot be tested without a real adapter.
  impact: >
    Full UI and integration testing of all application states (RPM display, disconnected
    state, setup wizard, pairing success/failure) is blocked without physical hardware.
  workaround: >
    Start ircama ELM327 TCP emulator manually for OBD testing. No workaround for
    Bluetooth setup testing without real hardware.
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.9+"
  os: "macOS (primary); Raspberry Pi OS (secondary)"
  dependencies:
    - library: "pygame"
      version: ">=2.0"
    - library: "pyserial"
      version: ">=3.5"
  domain: "domain_1"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    The OBDTransport factory (select_transport) and the BluetoothPairing instantiation
    in BluetoothSetupInterface have no simulation paths. Every execution path requires
    live hardware or an active external process.
  technical_notes: >
    Design:

    SimTransport implements OBDTransport. connect() returns True immediately.
    send_command() responds to ELM327 AT init commands with canonical strings and
    to "010C" with a computed RPM value derived from a sine sweep (800-6500 RPM,
    ~12 s period). No threads, no sockets, no external processes.

    SimBluetoothPairing is a duck-type replacement for BluetoothPairing exposing the
    same interface: discover_elm327_devices(), discover_all_devices(), pair_device(),
    cancel_discovery(), cancel_pairing(), shutdown(), is_discovery_active(),
    is_pairing_active(). Discovery returns 4 scripted BluetoothDevice instances
    after a ~3 s simulated delay with progress callbacks. pair_device() waits ~2 s
    then returns True (~80%) or False (~20%) to exercise both UI paths.

    Injection: BluetoothSetupInterface.__init__ accepts an optional pairing_factory
    parameter (callable returning a pairing instance). Default: BluetoothPairing().
    When --transport simbt: app.py passes lambda: SimBluetoothPairing().

    app.py: transport_forced check extended to include 'simtcp' and 'simbt'.
    simtcp bypasses device store / setup mode (acts like tcp).
    simbt enters setup mode with SimBluetoothPairing injected via pairing_factory.

    select_transport(): 'simtcp' and 'simbt' both return SimTransport().

    main.py: --transport choices extended to include 'simtcp' and 'simbt'.

    Files created:
      src/gtach/comm/sim_transport.py
      src/gtach/comm/sim_bluetooth.py

    Files modified:
      src/gtach/comm/transport.py
      src/gtach/main.py
      src/gtach/app.py
      src/gtach/display/setup_components/bluetooth/interface.py

  related_issues: []
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "AEL"
  target_date: ""
  approach: >
    Implement per technical_notes in analysis section. Create T02 change and T04 prompt
    documents. Execute via AEL.
  change_ref: "change-c7e2f1a9"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

verification_enhanced:
  verification_steps:
    - "Run: gtach --transport simtcp --debug — confirm splash, RPM display, RPM sweeps 800-6500 cyclically."
    - "Run: gtach --transport simbt --debug — confirm setup wizard launches with SimBluetoothPairing."
    - "In simbt setup: confirm 4 fake devices appear after scan progress completes."
    - "Select a fake device: confirm pairing animates ~2 s then shows success or failure."
    - "Repeat pairing ~5 times: confirm at least one failure occurs (20% failure rate)."
    - "Confirm no real Bluetooth hardware or TCP emulator process is required for any of the above."
    - "Confirm normal tcp, serial, rfcomm paths are unaffected."
  verification_results: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Prevention

```yaml
prevention:
  preventive_measures: >
    Document simtcp and simbt in CLAUDE.md and README as the standard test invocation
    for UI and integration testing without hardware.
  process_improvements: >
    Add simbt/simtcp invocations to the standard pre-commit test checklist.
```

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Traceability

```yaml
traceability:
  design_refs:
    - "design-gtach-master.md"
    - "design-7d3e9f5a-domain_comm.md"
  change_refs:
    - "change-c7e2f1a9"
  test_refs: []

notes: >
  simbt activates both SimTransport and SimBluetoothPairing — fully disconnected.
  simtcp activates SimTransport only — real Bluetooth hardware still required for setup.
  Both modes bypass the transport_forced / device store check in app.py.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-04-30 | William Watson | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
