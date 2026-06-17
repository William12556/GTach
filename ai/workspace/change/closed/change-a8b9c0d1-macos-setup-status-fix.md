# Change: macOS Setup Mode Serial Port Discovery + Status Indicator Fix

Created: 2026-04-01

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-a8b9c0d1"
  title: "macOS setup mode: serial port discovery; fix status indicator thread name"
  date: "2026-04-01"
  author: "William Watson"
  status: "verified"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a8b9c0d1"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-a8b9c0d1"
  description: >
    Two defects: (1) BluetoothSetupInterface calls bluetoothctl unconditionally,
    failing on macOS. (2) _draw_status_indicator checks thread 'bluetooth' which
    no longer exists after transport abstraction refactor.

scope:
  summary: >
    Add macOS serial port discovery path to BluetoothSetupInterface.start_discovery()
    replacing the bluetoothctl path on Darwin. Fix _draw_status_indicator to check
    thread 'transport' instead of 'bluetooth'.
  affected_components:
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-7d3e9f5a-domain_comm.md"
      sections:
        - "Setup / discovery"
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
      sections:
        - "Status indicator"
  out_of_scope:
    - "Changes to SerialTransport, DeviceStore, or OBDProtocol"
    - "macOS Bluetooth pairing UI (user pairs in System Preferences)"
    - "TCPTransport or emulator support"

rational:
  problem_statement: >
    macOS has no bluetoothctl. Classic Bluetooth devices (ELM327) paired via
    macOS System Preferences are accessible as /dev/cu.* serial ports.
    The setup mode must enumerate these ports rather than calling bluetoothctl.
    Additionally, the status indicator has been broken since the transport
    abstraction refactor renamed the thread from 'bluetooth' to 'transport'.
  proposed_solution: >
    Defect 1: In BluetoothSetupInterface, detect Darwin platform before
    initialising BluetoothPairing. On Darwin, provide a serial_discovery_task()
    that calls serial.tools.list_ports.comports(), filters to /dev/cu.* matching
    ELM/OBD patterns (same logic as SerialTransport._discover_port()), and
    populates state.discovered_devices with synthetic BluetoothDevice objects
    where mac_address holds the port path. The existing device selection and
    DeviceStore persistence flow is unchanged; SerialTransport already reads the
    stored value to open the port.
    Defect 2: Replace string literal 'bluetooth' with 'transport' in
    _draw_status_indicator.
  alternatives_considered:
    - option: "Implement a full macOS Bluetooth scanning UI using IOBluetooth"
      reason_rejected: >
        IOBluetooth requires PyObjC and macOS entitlements. Excessive complexity
        for a development tool. System Preferences pairing is the correct macOS
        workflow; the app only needs to list already-paired ports.
    - option: "Skip setup mode on macOS and require manual config file editing"
      reason_rejected: >
        Violates the goal of macOS mode offering full Pi functionality.
  benefits:
    - "Setup mode fully functional on macOS using standard paired serial ports"
    - "Status indicator correctly reflects transport connection state"
    - "No new dependencies (pyserial already required)"
    - "Pi code path unaffected"
  risks:
    - risk: "macOS port enumeration returns no ports if device not paired"
      mitigation: >
        Discovery screen shows 'No devices found' (existing UI path). User
        must pair the ELM327 adapter in macOS System Preferences first.
        A hint text will be added to the discovery screen on macOS.

technical_details:
  current_behavior: >
    BluetoothSetupInterface._init_bluetooth_pairing unconditionally creates a
    BluetoothPairing instance; start_discovery calls pairing.discover_elm327_devices()
    which invokes bluetoothctl. Fails immediately on macOS.
    _draw_status_indicator checks self.thread_manager.threads.get('bluetooth');
    'bluetooth' thread does not exist; status always DISCONNECTED.
  proposed_behavior: >
    Defect 1:
    - _init_bluetooth_pairing: add platform.system() == 'Darwin' guard;
      skip BluetoothPairing instantiation on macOS.
    - start_discovery: add Darwin branch. Instead of calling pairing.discover_elm327_devices(),
      enumerate serial.tools.list_ports.comports(). For each port where
      '/dev/cu.' is in port.device and any ELM/OBD pattern matches device or
      description, create a BluetoothDevice(name=port.description or port.device,
      mac_address=port.device, device_type='ELM327'). Populate state.discovered_devices.
      If no matching ports found, populate with all /dev/cu.* ports (unfiltered
      fallback, same as Pi 'show all devices' option). Add hint in discovery
      screen label: 'Pair device in System Preferences first'.
    Defect 2:
    - _draw_status_indicator: change 'bluetooth' to 'transport'.
  implementation_approach: >
    Both changes are platform-guarded and confined to their respective files.
    Serial port enumeration reuses the pattern matching already present in
    SerialTransport._discover_port(); it is not refactored out — the logic
    is duplicated in the setup interface to keep transport and display layers
    independent.
  code_changes:
    - component: "BluetoothSetupInterface"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: >
        Add Darwin guard to _init_bluetooth_pairing_async; add
        _serial_discovery_task() macOS serial port enumeration method;
        add Darwin branch in start_discovery to dispatch _serial_discovery_task
        instead of bluetoothctl-backed discovery.
      functions_affected:
        - "_init_bluetooth_pairing_async (inner function init_bluetooth_pairing)"
        - "start_discovery"
      classes_affected:
        - "BluetoothSetupInterface"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Replace thread name string 'bluetooth' with 'transport' in
        _draw_status_indicator.
      functions_affected:
        - "_draw_status_indicator"
      classes_affected:
        - "DisplayManager"

dependencies:
  internal:
    - component: "DeviceStore"
      impact: >
        No change. DeviceStore stores BluetoothDevice.mac_address; on macOS this
        field holds the port path (/dev/cu.OBDII-DevB). SerialTransport already
        reads this value.
    - component: "SerialTransport"
      impact: >
        No change. _discover_port() falls back to port scanning only if no port
        was explicitly provided. When DeviceStore provides a port path, it is
        passed directly to SerialTransport constructor.
  external:
    - library: "pyserial (serial.tools.list_ports)"
      version_change: "none"
      impact: "Used for port enumeration in setup mode on macOS"

testing_requirements:
  test_approach: "Manual functional test on macOS with real ELM327 adapter paired"
  test_cases:
    - scenario: "macOS, ELM327 paired, launch with no stored device"
      expected_result: >
        Setup mode shows discovery screen; /dev/cu.OBDII-* port appears in device list
    - scenario: "Select port from list"
      expected_result: >
        Port path stored in DeviceStore; app transitions to normal mode;
        SerialTransport connects to ELM327
    - scenario: "macOS, no device paired"
      expected_result: "'No devices found' shown; hint text visible"
    - scenario: "Pi launch (unchanged path)"
      expected_result: "bluetoothctl discovery proceeds as before"
    - scenario: "Transport connected on macOS"
      expected_result: "Status indicator shows connected colour (green dot)"
    - scenario: "Transport disconnected on macOS"
      expected_result: "Status indicator shows disconnected colour"
  validation_criteria:
    - "Setup mode completes on macOS without invoking bluetoothctl"
    - "Status indicator correctly reflects transport thread state"
    - "Pi discovery behaviour unchanged"

implementation:
  implementation_steps:
    - step: "Add Darwin guard and serial discovery to BluetoothSetupInterface"
      owner: "AEL"
    - step: "Fix thread name in _draw_status_indicator"
      owner: "AEL"
  rollback_procedure: "Revert interface.py and manager.py to prior commits"

traceability:
  design_updates:
    - design_ref: "design-7d3e9f5a-domain_comm.md"
      sections_updated:
        - "macOS platform behaviour"
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
      sections_updated:
        - "Status indicator thread reference"
  related_issues:
    - issue_ref: "issue-a8b9c0d1"
      relationship: "resolves"

notes: >
  BluetoothDevice.mac_address is used to store the serial port path on macOS.
  The field name is a misnomer in this context but changing it is out of scope.
  DeviceStore and all downstream code treat this as an opaque string identifier,
  so no schema change is required.

version_history:
  - version: "1.0"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Initial change document"
  - version: "1.1"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Closed — implemented by Claude Code and verified"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | William Watson | Initial change document |
| 1.1 | 2026-04-01 | William Watson | Closed — implemented by Claude Code and verified |

---

Copyright (c) 2026 William Watson. MIT License.
