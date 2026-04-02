# Change: Comm Layer Transport Abstraction and macOS Development Mode

Created: 2026 March 24

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

## 1.0 Change Information

```yaml
change_info:
  id: "change-e1f2a3b4"
  title: "Comm Layer Transport Abstraction and macOS Development Mode"
  date: "2026-03-24"
  author: "William Watson"
  status: "implemented"
  priority: "high"
  iteration: 1
  version_bump: "0.1.1 -> 0.2.0 (MINOR)"
  coupled_docs:
    issue_ref: "n/a"
    issue_iteration: 1
```

### 1.1 Document References

- **Domain Design**: [design-7d3e9f5a-domain_comm.md](<design-7d3e9f5a-domain_comm.md>) v2.0
- **Requirements**: [requirements-gtach-master.md](<requirements-gtach-master.md>) v0.9
- **Component — OBDTransport**: [design-b1c2d3e4-component_comm_transport.md](<design-b1c2d3e4-component_comm_transport.md>)
- **Component — RFCOMMTransport**: [design-c2d3e4f5-component_comm_rfcomm_transport.md](<design-c2d3e4f5-component_comm_rfcomm_transport.md>)
- **Component — TCPTransport**: [design-d3e4f5a6-component_comm_tcp_transport.md](<design-d3e4f5a6-component_comm_tcp_transport.md>)
- **Component — SerialTransport**: [design-e4f5a6b7-component_comm_serial_transport.md](<design-e4f5a6b7-component_comm_serial_transport.md>)
- **Component — OBDProtocol**: [design-f5a6b7c8-component_comm_obd_protocol.md](<design-f5a6b7c8-component_comm_obd_protocol.md>)
- **Component — DeviceStore + BluetoothDevice**: [design-a6b7c8d9-component_comm_device_store.md](<design-a6b7c8d9-component_comm_device_store.md>)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "enhancement"
  reference: "requirements-gtach-master.md ARCH e7f8a9b0, REQ g1h2i3j4, ARCH h2i3j4k5"
  description: >
    The existing comm layer uses Bleak (BLE library) for Bluetooth communication.
    Real ELM327 adapters use Classic Bluetooth SPP (RFCOMM), which is
    incompatible with BLE. Separately, macOS development mode was identified
    as a requirements addition (REQ g1h2i3j4). Both changes are addressed by
    replacing BluetoothManager/Bleak with an OBDTransport abstraction.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Replace the Bleak-based BluetoothManager with an OBDTransport abstract
    base class and three concrete transport implementations. Update OBDProtocol
    to depend on OBDTransport. Correct a cross-domain import in DeviceStore.
    Add --macos / --transport / --obd-host / --obd-port CLI flags to the
    application entry point. Remove bluetooth.py.

  affected_components:
    - name: "transport.py"
      file_path: "src/gtach/comm/transport.py"
      change_type: "add"
    - name: "rfcomm.py"
      file_path: "src/gtach/comm/rfcomm.py"
      change_type: "add"
    - name: "tcp_transport.py"
      file_path: "src/gtach/comm/tcp_transport.py"
      change_type: "add"
    - name: "serial_transport.py"
      file_path: "src/gtach/comm/serial_transport.py"
      change_type: "add"
    - name: "obd.py"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "models.py"
      file_path: "src/gtach/comm/models.py"
      change_type: "modify"
    - name: "device_store.py"
      file_path: "src/gtach/comm/device_store.py"
      change_type: "modify"
    - name: "__init__.py (comm)"
      file_path: "src/gtach/comm/__init__.py"
      change_type: "modify"
    - name: "bluetooth.py"
      file_path: "src/gtach/comm/bluetooth.py"
      change_type: "delete"
    - name: "app.py"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "main.py"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "pyproject.toml"
      file_path: "pyproject.toml"
      change_type: "modify"
    - name: "watchdog.py"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"

  affected_designs:
    - design_ref: "design-7d3e9f5a-domain_comm.md"
      sections:
        - "All sections — updated to v2.0"
    - design_ref: "design-b1c2d3e4-component_comm_transport.md"
      sections:
        - "New document"
    - design_ref: "design-c2d3e4f5-component_comm_rfcomm_transport.md"
      sections:
        - "New document"
    - design_ref: "design-d3e4f5a6-component_comm_tcp_transport.md"
      sections:
        - "New document"
    - design_ref: "design-e4f5a6b7-component_comm_serial_transport.md"
      sections:
        - "New document"
    - design_ref: "design-f5a6b7c8-component_comm_obd_protocol.md"
      sections:
        - "New document"
    - design_ref: "design-a6b7c8d9-component_comm_device_store.md"
      sections:
        - "New document"

  out_of_scope:
    - "Display domain changes"
    - "Core domain changes"
    - "Configuration domain changes"
    - "Watchdog or thread manager changes"
    - "Test document creation (separate T05/T06 cycle)"
    - "CLI argument handling beyond --macos, --transport, --obd-host, --obd-port, --serial-port"
    - "watchdog_enhanced.py (unreferenced; out of scope for this change)"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    BluetoothManager uses Bleak (a BLE library). ELM327 OBD-II adapters
    use Classic Bluetooth SPP (RFCOMM), not BLE. Bleak cannot communicate
    with ELM327 devices on any platform. This makes the existing comm layer
    non-functional for the intended hardware. Additionally, there is no path
    for macOS development without physical Pi hardware.

  proposed_solution: >
    Implement OBDTransport ABC with three concrete transports.
    RFCOMMTransport uses socket(AF_BLUETOOTH, BTPROTO_RFCOMM) — the
    correct mechanism for Classic Bluetooth SPP on Linux/Pi.
    TCPTransport uses socket(AF_INET) for the ircama emulator.
    SerialTransport uses pyserial for macOS paired SPP devices.
    OBDProtocol is updated to depend only on OBDTransport.
    select_transport() chooses the implementation at startup.

  alternatives_considered:
    - option: "Retain Bleak; add RFCOMM workaround"
      reason_rejected: >
        Bleak has no RFCOMM support. The workaround would require
        OS-level BlueZ socket calls that Bleak explicitly does not expose.
        Adding a separate RFCOMM path alongside Bleak adds complexity
        without benefit.
    - option: "Use python-bluetooth (PyBluez) for all transports"
      reason_rejected: >
        PyBluez has not been maintained and does not support macOS.
        Standard library socket with AF_BLUETOOTH is more portable on
        Linux and requires no additional dependency.

  benefits:
    - "Correct Bluetooth transport for ELM327 SPP devices on Pi/Linux"
    - "macOS development mode with TCP emulator — no Pi hardware required"
    - "OBDProtocol is transport-agnostic; single implementation for all platforms"
    - "Removes Bleak dependency; reduces install surface"
    - "No async event loop complexity; all transports are synchronous"

  risks:
    - risk: "AF_BLUETOOTH socket availability on macOS"
      mitigation: >
        macOS does not expose AF_BLUETOOTH in Python's socket module.
        SerialTransport (pyserial) and TCPTransport are the designated
        macOS transports. select_transport() never routes macOS to
        RFCOMMTransport. This is documented in the design.
    - risk: "RFCOMM channel on target ELM327 device may not be channel 1"
      mitigation: >
        Channel 1 is the universal SPP default. If a device differs,
        the channel is a constructor parameter on RFCOMMTransport.
    - risk: "pyserial adds a dependency not present in the current lockfile"
      mitigation: >
        pyserial is a widely deployed, stable library. It is added to
        pyproject.toml as an explicit dependency.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    BluetoothManager uses Bleak (BLE) for device discovery and communication.
    OBDProtocol depends directly on BluetoothManager.
    DeviceStore imports BluetoothDevice from display.setup_models (cross-domain).
    No macOS development mode exists.

  proposed_behavior: >
    OBDTransport ABC defines a uniform interface.
    Three concrete transports implement it: RFCOMMTransport, SerialTransport, TCPTransport.
    OBDProtocol depends on OBDTransport only.
    DeviceStore imports BluetoothDevice from comm.models (same domain).
    select_transport() instantiates the correct transport from CLI args / platform.
    --macos flag and --transport arg enable platform routing at the entry point.
    bluetooth.py is removed.

  implementation_approach: >
    New files are created first (transport.py, rfcomm.py, tcp_transport.py,
    serial_transport.py). Existing files are then modified (obd.py, models.py,
    device_store.py, __init__.py, app.py, main.py, pyproject.toml).
    bluetooth.py is deleted last, after all references are removed.

  code_changes:
    - component: "transport.py"
      file: "src/gtach/comm/transport.py"
      change_summary: "New file. OBDTransport ABC, TransportState enum, TransportError hierarchy, select_transport() factory."
      classes_affected:
        - "OBDTransport (new)"
        - "TransportState (new)"
        - "TransportError (new)"
        - "ConnectionError (new)"
        - "TimeoutError (new)"
        - "ProtocolError (new)"
      functions_affected:
        - "select_transport (new)"

    - component: "rfcomm.py"
      file: "src/gtach/comm/rfcomm.py"
      change_summary: "New file. RFCOMMTransport: RFCOMM socket transport for Pi/Linux."
      classes_affected:
        - "RFCOMMTransport (new)"

    - component: "tcp_transport.py"
      file: "src/gtach/comm/tcp_transport.py"
      change_summary: "New file. TCPTransport: TCP socket transport for ircama emulator."
      classes_affected:
        - "TCPTransport (new)"

    - component: "serial_transport.py"
      file: "src/gtach/comm/serial_transport.py"
      change_summary: "New file. SerialTransport: pyserial transport for macOS."
      classes_affected:
        - "SerialTransport (new)"

    - component: "obd.py"
      file: "src/gtach/comm/obd.py"
      change_summary: >
        Replace BluetoothManager dependency with OBDTransport.
        __init__ signature changes: bluetooth_manager -> transport (OBDTransport).
        Internal calls to self.bluetooth.* replaced with self.transport.*.
        OBDResponse dataclass unchanged.
      classes_affected:
        - "OBDProtocol (modify)"
      functions_affected:
        - "__init__"
        - "_protocol_loop"
        - "_initialize_protocol"
        - "_send_command"
        - "_request_rpm"

    - component: "models.py"
      file: "src/gtach/comm/models.py"
      change_summary: >
        Rationalise BluetoothDevice: remove BLE-specific fields
        (connection_count, signal_strength, metadata). Retain:
        name, mac_address, device_type, last_connected.
        Fix mac_address normalisation to preserve colons (AA:BB:CC:DD:EE:FF).
        No field name changes that affect DeviceStore YAML keys.
      classes_affected:
        - "BluetoothDevice (modify)"

    - component: "device_store.py"
      file: "src/gtach/comm/device_store.py"
      change_summary: >
        Fix import: replace 'from ..display.setup_models import BluetoothDevice'
        with 'from .models import BluetoothDevice'.
        Rename save_paired_device() -> save_device().
        Remove methods not in the approved interface:
        set_primary_device(), is_setup_complete(), mark_setup_complete(),
        is_first_run(), get_discovery_timeout(), set_discovery_timeout(),
        clear_all_devices().
        Implement atomic _save_config() via temp file + rename.
        Remove setup block from devices.yaml structure.
      classes_affected:
        - "DeviceStore (modify)"

    - component: "__init__.py (comm)"
      file: "src/gtach/comm/__init__.py"
      change_summary: >
        Update exports: add OBDTransport, TransportState, TransportError,
        RFCOMMTransport, TCPTransport, SerialTransport, select_transport.
        Remove BluetoothManager, BluetoothState, BluetoothConnectionError exports.
      functions_affected:
        - "__init__.py exports"

    - component: "bluetooth.py"
      file: "src/gtach/comm/bluetooth.py"
      change_summary: "Delete. Replaced entirely by transport abstraction."

    - component: "app.py"
      file: "src/gtach/app.py"
      change_summary: >
        Replace BluetoothManager instantiation with select_transport() call.
        Pass transport to OBDProtocol instead of BluetoothManager.
        Replace is_setup_complete() check (removed from DeviceStore) with
        get_primary_device() is None for setup mode detection (REQ d4e5f6a7).
        Add platform detection and args plumbing to select_transport().
        Update shutdown: self._bluetooth.stop() -> self._transport.stop().
      classes_affected:
        - "GTachApplication (modify)"

    - component: "main.py"
      file: "src/gtach/main.py"
      change_summary: >
        Remove OOS dead code: --service flag and run_as_service() (OOS-01),
        --test-hardware flag and test_hardware() (OOS-03), --validate-logging,
        --logging-health-check flags and all associated validation machinery
        (~400 lines, OOS-05/08). Remove session-based logging complexity;
        replace with simple basicConfig call (debug flag controls level).
        Fix version string: 'GTach 1.0.0' -> '0.2.0'.
        Add CLI arguments: --macos, --transport (tcp|serial|rfcomm),
        --obd-host (default localhost), --obd-port (default 35000),
        --serial-port (default None).
        Pass parsed args to GTachApplication initialisation.
        Result: ~80-100 lines.
      functions_affected:
        - "main (rewrite)"
        - "parse_arguments (modify)"
        - "setup_logging (simplify)"

    - component: "watchdog.py"
      file: "src/gtach/core/watchdog.py"
      change_summary: >
        Update critical_threads set: replace 'bluetooth' string with 'transport'.
        The transport thread registers under the name 'transport'.
      functions_affected:
        - "__init__ (critical_threads string)"

    - component: "pyproject.toml"
      file: "pyproject.toml"
      change_summary: >
        Add pyserial >= 3.5 to dependencies.
        Remove bleak from dependencies.
        Bump version to 0.2.0.

  interface_changes:
    - interface: "OBDProtocol.__init__"
      change_type: "signature"
      details: "bluetooth_manager: BluetoothManager -> transport: OBDTransport"
      backward_compatible: "no"
    - interface: "DeviceStore.save_paired_device"
      change_type: "signature"
      details: "Renamed to save_device(); same parameters otherwise"
      backward_compatible: "no"
    - interface: "comm package public API"
      change_type: "contract"
      details: "BluetoothManager, BluetoothState removed; OBDTransport, TransportState, concrete transports added"
      backward_compatible: "no"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Dependencies

```yaml
dependencies:
  internal:
    - component: "app.py / GTachApp"
      impact: "Must use select_transport() instead of BluetoothManager; args plumbing required"
    - component: "display domain (setup.py)"
      impact: >
        setup.py may reference BluetoothManager or BluetoothState.
        References must be updated to use OBDTransport / TransportState.
        Scope of display domain changes is limited to import corrections only.

  external:
    - library: "bleak"
      version_change: "removed"
      impact: "No longer a dependency; remove from pyproject.toml"
    - library: "pyserial"
      version_change: "added (>= 3.5)"
      impact: "Required for SerialTransport on macOS; add to pyproject.toml"
    - library: "socket (stdlib)"
      version_change: "none"
      impact: "Used by RFCOMMTransport and TCPTransport; no install required"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: >
    Manual integration test using ircama ELM327 emulator on macOS via
    TCPTransport. Pi/RFCOMM integration test against Pi 4 SPP emulator.
    Unit tests for transport interface compliance are deferred to a T05/T06 cycle.

  test_cases:
    - scenario: "macOS + TCPTransport + ircama emulator (localhost:35000)"
      expected_result: "App starts, splash screen displays, RPM values render from emulator data"
    - scenario: "macOS + SerialTransport + paired ELM327 via /dev/tty.*"
      expected_result: "App starts, connects via serial, RPM values render"
    - scenario: "Pi + RFCOMMTransport + Pi 4 SPP emulator"
      expected_result: "App starts, RFCOMM connects, RPM values render"
    - scenario: "Transport disconnection and reconnection"
      expected_result: "Disconnected state displays; reconnection loop resumes; RPM display restores"
    - scenario: "select_transport with --transport tcp flag on Pi"
      expected_result: "TCPTransport selected regardless of platform"

  regression_scope:
    - "RPM display pipeline unchanged — OBDResponse format and queue protocol intact"
    - "DeviceStore YAML file format compatible — primary device MAC still readable"
    - "ThreadManager integration unchanged"

  validation_criteria:
    - "No references to BluetoothManager or Bleak in comm domain post-change"
    - "DeviceStore imports BluetoothDevice from comm.models"
    - "pyproject.toml: bleak absent, pyserial present"
    - "All four transports instantiate without error on their target platforms"
    - "OBDProtocol._protocol_loop runs without modification for all transports"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Implementation

```yaml
implementation:
  effort_estimate: "1–2 AEL sessions"

  implementation_steps:
    - step: "1. Human approves design baseline; creates git tag on design documents"
      owner: "William Watson"
    - step: "2. Create T04 prompt for new comm files (transport.py, rfcomm.py, tcp_transport.py, serial_transport.py)"
      owner: "Claude (Strategic)"
    - step: "3. AEL generates new comm files"
      owner: "AEL (Tactical)"
    - step: "4. Create T04 prompt for comm file modifications (obd.py, models.py, device_store.py, __init__.py)"
      owner: "Claude (Strategic)"
    - step: "5. AEL modifies existing comm files"
      owner: "AEL (Tactical)"
    - step: "6. Create T04 prompt for entry point changes (app.py, main.py, pyproject.toml)"
      owner: "Claude (Strategic)"
    - step: "7. AEL modifies entry point and config files"
      owner: "AEL (Tactical)"
    - step: "8. Delete bluetooth.py"
      owner: "William Watson or AEL"
    - step: "8a. Archive watchdog_enhanced.py to deprecated/ (unreferenced artefact)"
      owner: "William Watson"
    - step: "9. Human runs validation test cases"
      owner: "William Watson"
    - step: "10. Strategic Domain reviews generated code; creates T06 result or T03 issues"
      owner: "Claude (Strategic)"

  rollback_procedure: >
    Revert to git tag created at step 1. bluetooth.py is preserved in
    git history. No database migrations required.

  deployment_notes: >
    pyserial must be installed in the venv: pip install pyserial.
    ircama ELM327 emulator for macOS testing: pip install ELM327-emulator.
    Pi deployment: pyserial is included in requirements; RFCOMM socket
    requires Bluetooth stack present (bluez) — no change from prior setup.
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  implemented_date: "2026-04-01"
  implemented_by: "William Watson"
  verification_date: "2026-04-01"
  verified_by: "William Watson"
  test_results: "macOS TCPTransport: window opens, renders at 60fps, RPM data received from emulator. Seven defects found and resolved under trivial change exemption (issues a2e8b4c7, b1d4e7f9, c9a2f3e1, d3f1a2c8, d5f8a2b3, e3c7b9a4, e5b2c9d1, f7c3a1e6). Pi/RFCOMM not yet tested."
  issues_found:
    - issue_ref: "issue-a2e8b4c7"
      title: "No macOS development configuration file"
      resolution: "Created workspace/config/config-macos-dev.yaml"
    - issue_ref: "issue-b1d4e7f9"
      title: "SDL dummy driver on macOS — no window shown"
      resolution: "Platform-aware rendering path in engine.py"
    - issue_ref: "issue-c9a2f3e1"
      title: "Display loop on background thread (NSInternalInconsistencyException)"
      resolution: "Display loop moved to main thread on macOS"
    - issue_ref: "issue-d3f1a2c8"
      title: "pygame not declared as macOS dependency"
      resolution: "Added [macos] optional-dependency group to pyproject.toml"
    - issue_ref: "issue-d5f8a2b3"
      title: "DisplayManager.stop() joins never-started thread on macOS"
      resolution: "Guarded display_thread.join() on Darwin"
    - issue_ref: "issue-e3c7b9a4"
      title: "Splash screen loops forever"
      resolution: "_save_config() saves _post_splash_mode when mode is SPLASH"
    - issue_ref: "issue-e5b2c9d1"
      title: "get_platform_type not exported from utils __init__.py"
      resolution: "Added to utils/__init__.py"
    - issue_ref: "issue-f7c3a1e6"
      title: "__main__.py missing from gtach package"
      resolution: "Created src/gtach/__main__.py"
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Traceability

```yaml
traceability:
  design_updates:
    - design_ref: "design-7d3e9f5a-domain_comm.md"
      sections_updated:
        - "All sections — v2.0"
      update_date: "2026-03-24"
    - design_ref: "design-b1c2d3e4-component_comm_transport.md"
      sections_updated:
        - "New document v1.0"
      update_date: "2026-03-24"
    - design_ref: "design-c2d3e4f5-component_comm_rfcomm_transport.md"
      sections_updated:
        - "New document v1.0"
      update_date: "2026-03-24"
    - design_ref: "design-d3e4f5a6-component_comm_tcp_transport.md"
      sections_updated:
        - "New document v1.0"
      update_date: "2026-03-24"
    - design_ref: "design-e4f5a6b7-component_comm_serial_transport.md"
      sections_updated:
        - "New document v1.0"
      update_date: "2026-03-24"
    - design_ref: "design-f5a6b7c8-component_comm_obd_protocol.md"
      sections_updated:
        - "New document v1.0"
      update_date: "2026-03-24"
    - design_ref: "design-a6b7c8d9-component_comm_device_store.md"
      sections_updated:
        - "New document v1.0"
      update_date: "2026-03-24"

  requirements_refs:
    - "ARCH e7f8a9b0 — OBDTransport abstraction"
    - "REQ g1h2i3j4 — macOS development mode"
    - "ARCH h2i3j4k5 — macOS as development platform"
    - "NFR b4c5d6e7 — conditional imports, transport abstraction"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-24 | William Watson | Initial change document |
| 1.1 | 2026-04-01 | William Watson | Status updated to implemented; verification section populated with macOS test results and issue references |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
