Created: 2026 April 30

# Change: Sim Mode — Hardware-Free Full Application Testing

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Dependencies](<#6.0 dependencies>)
- [7.0 Testing Requirements](<#7.0 testing requirements>)
- [8.0 Implementation](<#8.0 implementation>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Traceability](<#10.0 traceability>)
- [Version History](<#version history>)

---

```yaml
change_info:
  id: "change-c7e2f1a9"
  title: "Sim Mode — Hardware-Free Full Application Testing"
  date: "2026-04-30"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c7e2f1a9"
    issue_iteration: 1
```

---

## 1.0 Change Information

Implements two simulation transport modes (`--transport simtcp` and `--transport simbt`)
enabling full application testing — OBD display pipeline and Bluetooth setup wizard —
without physical hardware or a running external emulator process.

Related issue: [issue-c7e2f1a9-sim-mode.md](<issue-c7e2f1a9-sim-mode.md>)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "enhancement"
  reference: "issue-c7e2f1a9"
  description: >
    No simulation path exists in the transport factory or Bluetooth pairing layer.
    All execution paths require live hardware or an active external process. This
    enhancement adds SimTransport and SimBluetoothPairing and wires them into the
    application via two new --transport flag values.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Add SimTransport (synthetic ELM327 OBD responses) and SimBluetoothPairing
    (scripted device discovery and pairing). Wire both into the existing transport
    factory, CLI parser, application controller, and Bluetooth setup interface via
    an optional pairing_factory injection parameter.

  affected_components:
    - name: "SimTransport (new)"
      file_path: "src/gtach/comm/sim_transport.py"
      change_type: "add"
    - name: "SimBluetoothPairing (new)"
      file_path: "src/gtach/comm/sim_bluetooth.py"
      change_type: "add"
    - name: "select_transport / OBDTransport factory"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "CLI argument parser"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"

  affected_designs:
    - design_ref: "design-gtach-master.md"
      sections:
        - "8.2 Communication Domain"
        - "10.1 Internal Interfaces"
    - design_ref: "design-7d3e9f5a-domain_comm.md"
      sections:
        - "Transport implementations"

  out_of_scope:
    - "Simulation of any OBD PID other than 0x0C (RPM)"
    - "UI controls for configuring sim parameters at runtime"
    - "Simulation of the disconnected/reconnect state machine"
    - "Changes to RFCOMMTransport, SerialTransport, or TCPTransport"
    - "Changes to DeviceStore or pairing.py"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    Full application testing (RPM display pipeline + Bluetooth setup wizard) is blocked
    without physical ELM327 hardware or a running ircama TCP emulator. No workaround
    exists for Bluetooth setup testing.

  proposed_solution: >
    Two new --transport values activate fully simulated modes. simtcp replaces the OBD
    transport with SimTransport; simbt adds SimBluetoothPairing injection on top.
    Both require no external hardware or processes.

  alternatives_considered:
    - option: "Single --sim flag replacing both transport and BT"
      reason_rejected: >
        Less granular. simtcp lets the developer test OBD display with real Bluetooth
        setup flow if hardware is available. Two flags preserve that flexibility.
    - option: "Extend TCPTransport with a loopback/mock mode"
      reason_rejected: >
        Conflates simulation with the TCP transport implementation; complicates
        TCPTransport and does not address Bluetooth setup simulation.

  benefits:
    - "Full UI exercised without hardware on macOS and Pi"
    - "RPM display, disconnected state, setup wizard, pairing success/failure all testable"
    - "SimBluetoothPairing 20% failure rate exercises error path without needing a broken adapter"
    - "Zero new runtime dependencies"
    - "Injection via pairing_factory parameter is backward-compatible — no existing call sites change"

  risks:
    - risk: "SimBluetoothPairing diverges from real BluetoothPairing interface over time"
      mitigation: >
        SimBluetoothPairing exposes exactly the public methods called by
        BluetoothSetupInterface. Any interface change to BluetoothPairing that breaks
        BluetoothSetupInterface will also be visible on SimBluetoothPairing.
    - risk: "simbt enters setup mode unconditionally, ignoring device store"
      mitigation: >
        This is intentional and documented. simbt is a test mode; overriding
        the device store check is required to force setup mode entry.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    select_transport() accepts 'tcp', 'serial', 'rfcomm'. BluetoothSetupInterface
    always instantiates BluetoothPairing() directly. No simulation paths exist.

  proposed_behavior: >
    select_transport() additionally accepts 'simtcp' and 'simbt', both returning
    SimTransport(). BluetoothSetupInterface accepts an optional pairing_factory
    parameter; when None (default), behaviour is unchanged. app.py passes
    lambda: SimBluetoothPairing() when --transport simbt.

  implementation_approach: >
    1. Create sim_transport.py: SimTransport(OBDTransport) with sine-sweep RPM.
    2. Create sim_bluetooth.py: SimBluetoothPairing duck-typing BluetoothPairing.
    3. Modify transport.py: add 'simtcp'/'simbt' branches to select_transport().
    4. Modify main.py: extend --transport choices list.
    5. Modify interface.py: add pairing_factory=None parameter to __init__;
       replace bare BluetoothPairing() calls with pairing_factory() or BluetoothPairing().
    6. Modify app.py: extend transport_forced set; inject SimBluetoothPairing factory
       into SetupDisplayManager when simbt active.

  code_changes:
    - component: "SimTransport"
      file: "src/gtach/comm/sim_transport.py"
      change_summary: >
        New class. connect() → True. disconnect() → no-op. is_connected() → True.
        state → CONNECTED. send_command() maps AT init commands to canonical ELM327
        strings; maps '010C' to a hex-encoded RPM value computed from
        math.sin(time.time() * 2*pi / PERIOD) scaled to 800-6500 RPM.
        PERIOD = 12.0 s. No threads or sockets.
      functions_affected:
        - "connect"
        - "disconnect"
        - "send_command"
        - "is_connected"
        - "state (property)"
      classes_affected:
        - "SimTransport"

    - component: "SimBluetoothPairing"
      file: "src/gtach/comm/sim_bluetooth.py"
      change_summary: >
        New class. discover_elm327_devices() / discover_all_devices(): fires
        progress_callback at 0.0, 0.33, 0.66, 1.0 with time.sleep(0.75) between
        steps, then returns 4 hardcoded BluetoothDevice instances. pair_device():
        fires status_callback(CONNECTING), sleeps 1 s, fires status_callback(TESTING),
        sleeps 1 s, then returns True if random.random() > 0.2 else False with
        appropriate status_callback(SUCCESS/FAILED). cancel_discovery(),
        cancel_pairing(), shutdown(), is_discovery_active(), is_pairing_active()
        implemented as stubs matching BluetoothPairing signatures.
      functions_affected:
        - "discover_elm327_devices"
        - "discover_all_devices"
        - "pair_device"
        - "cancel_discovery"
        - "cancel_pairing"
        - "shutdown"
        - "is_discovery_active"
        - "is_pairing_active"
      classes_affected:
        - "SimBluetoothPairing"

    - component: "select_transport"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        Add 'simtcp' and 'simbt' branches before the platform auto-detect block.
        Both branches import and return SimTransport(). No other changes.
      functions_affected:
        - "select_transport"
      classes_affected: []

    - component: "parse_arguments"
      file: "src/gtach/main.py"
      change_summary: >
        Extend --transport choices list from ['tcp','serial','rfcomm'] to
        ['tcp','serial','rfcomm','simtcp','simbt'].
      functions_affected:
        - "parse_arguments"
      classes_affected: []

    - component: "GTachApplication.start"
      file: "src/gtach/app.py"
      change_summary: >
        Extend transport_forced condition: 'simtcp' joins 'tcp' and 'serial' in
        bypassing device store check. 'simbt' takes a separate branch that enters
        setup mode and passes pairing_factory=lambda: SimBluetoothPairing() to
        SetupDisplayManager (via BluetoothSetupInterface injection).
      functions_affected:
        - "start"
        - "_start_setup_mode"
      classes_affected:
        - "GTachApplication"

    - component: "BluetoothSetupInterface"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: >
        Add pairing_factory=None parameter to __init__. Store as
        self._pairing_factory. Replace both bare BluetoothPairing() instantiations
        (lines 52 and 111) with (self._pairing_factory or BluetoothPairing)(). No
        other logic changes.
      functions_affected:
        - "__init__"
        - "_init_bluetooth_pairing_async"
      classes_affected:
        - "BluetoothSetupInterface"

  interface_changes:
    - interface: "BluetoothSetupInterface.__init__"
      change_type: "signature"
      details: "Add optional pairing_factory=None keyword parameter."
      backward_compatible: "yes"

    - interface: "SetupDisplayManager.__init__ (via BluetoothSetupInterface)"
      change_type: "signature"
      details: >
        SetupDisplayManager passes pairing_factory through to BluetoothSetupInterface.
        Add optional pairing_factory=None to SetupDisplayManager.__init__ and forward
        to BluetoothSetupInterface constructor.
      backward_compatible: "yes"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Dependencies

```yaml
dependencies:
  internal:
    - component: "OBDTransport ABC"
      impact: "SimTransport must implement all four abstract methods."
    - component: "BluetoothPairing (pairing.py)"
      impact: >
        SimBluetoothPairing must expose identical public interface.
        No changes to BluetoothPairing itself.
    - component: "display/setup_models.BluetoothDevice"
      impact: "SimBluetoothPairing returns BluetoothDevice instances — existing model, no change."
    - component: "display/setup_models.PairingStatus"
      impact: "SimBluetoothPairing uses PairingStatus enum — existing model, no change."

  external: []

  required_changes: []
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: >
    Manual integration testing on macOS using the verification steps defined in
    issue-c7e2f1a9. Existing transport unit tests must remain unaffected.

  test_cases:
    - scenario: "simtcp — OBD display pipeline"
      expected_result: >
        gtach --transport simtcp --debug starts, shows splash, enters normal RPM display.
        RPM value cycles 800-6500 with a ~12 s period. No external process required.
    - scenario: "simbt — setup wizard full flow"
      expected_result: >
        gtach --transport simbt --debug enters setup mode. Discovery shows 4 fake
        devices after progress bar completes (~3 s). Selecting a device animates
        pairing for ~2 s then shows success or failure screen.
    - scenario: "simbt — pairing failure path"
      expected_result: >
        Over ~5 pairing attempts at least one failure is observed, exercising the
        retry/back UI path.
    - scenario: "Regression — existing transports unaffected"
      expected_result: >
        --transport tcp, --transport serial behaviour unchanged. No import errors
        introduced. Application starts normally without --transport flag.

  regression_scope:
    - "src/gtach/comm/transport.py select_transport()"
    - "src/gtach/main.py argument parsing"
    - "src/gtach/app.py start() normal and setup modes"
    - "src/gtach/display/setup_components/bluetooth/interface.py default path"

  validation_criteria:
    - "SimTransport.connect() always returns True"
    - "SimTransport.send_command('010C') returns a valid ELM327 hex response"
    - "RPM value decoded from response falls within 800-6500 range"
    - "SimBluetoothPairing.discover_elm327_devices() returns exactly 4 devices"
    - "SimBluetoothPairing.pair_device() returns False at least once in 10 calls"
    - "BluetoothSetupInterface default (no pairing_factory) behaviour unchanged"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Implementation

```yaml
implementation:
  implementation_steps:
    - step: "Create src/gtach/comm/sim_transport.py"
      owner: "AEL"
    - step: "Create src/gtach/comm/sim_bluetooth.py"
      owner: "AEL"
    - step: "Modify src/gtach/comm/transport.py — add simtcp/simbt branches"
      owner: "AEL"
    - step: "Modify src/gtach/main.py — extend --transport choices"
      owner: "AEL"
    - step: "Modify src/gtach/display/setup_components/bluetooth/interface.py — pairing_factory injection"
      owner: "AEL"
    - step: "Modify src/gtach/app.py — simbt setup mode entry and factory injection"
      owner: "AEL"

  rollback_procedure: >
    Revert via git. No schema or config file changes; rollback is a clean revert.

  deployment_notes: >
    simtcp and simbt are development/test modes only. No production deployment
    changes required. CLAUDE.md and README should be updated post-implementation
    to document the new flags.
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Traceability

```yaml
traceability:
  design_updates:
    - design_ref: "design-gtach-master.md"
      sections_updated:
        - "8.2 Communication Domain — add SimTransport and SimBluetoothPairing to component list"
        - "10.1 Internal Interfaces — document pairing_factory parameter"
      update_date: ""
    - design_ref: "design-7d3e9f5a-domain_comm.md"
      sections_updated:
        - "Transport implementations — add SimTransport entry"
      update_date: ""

  related_changes: []

  related_issues:
    - issue_ref: "issue-c7e2f1a9"
      relationship: "source"

notes: >
  SetupDisplayManager.__init__ also requires a pairing_factory parameter to forward
  to BluetoothSetupInterface. This is a one-line signature addition and is covered
  by the interface.py change step — AEL should trace the call chain and add it.

version_history:
  - version: "0.1"
    date: "2026-04-30"
    author: "William Watson"
    changes:
      - "Initial change document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-04-30 | William Watson | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
