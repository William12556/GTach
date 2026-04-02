# Issue: macOS Setup Mode Non-Functional + Status Indicator Bug

Created: 2026-04-01

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-a8b9c0d1"
  title: "macOS setup mode fails (bluetoothctl unavailable); status indicator checks wrong thread name"
  date: "2026-04-01"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: "change-a8b9c0d1"
    change_iteration: 1

source:
  origin: "code_review"
  description: >
    Two defects prevent macOS from operating as a functional Pi equivalent.
    (1) BluetoothSetupInterface calls BluetoothPairing which invokes bluetoothctl,
    a Linux-only tool. On macOS this fails immediately, making setup mode unusable.
    The correct macOS mechanism is serial port enumeration: Classic Bluetooth
    devices paired via System Preferences appear as /dev/cu.* serial ports.
    (2) _draw_status_indicator in DisplayManager checks for a thread named
    'bluetooth', but app.py registers the transport thread as 'transport'.
    The status indicator therefore always shows DISCONNECTED regardless of
    actual transport state.

affected_scope:
  components:
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs:
    - design_ref: "design-gtach-master.md §8.2"
    - design_ref: "design-7d3e9f5a-domain_comm.md"
    - design_ref: "design-2c6b8e4d-domain_display.md"
  version: "0.2.0"

reproduction:
  prerequisites: "Running GTach on macOS with no stored device (triggers setup mode)"
  steps:
    - "Delete or rename ~/.config/gtach/devices.yaml to force first-run"
    - "Launch GTach on macOS"
    - "Observe setup mode failure or exception from bluetoothctl"
  frequency: "always"
  reproducibility_conditions: "macOS platform, setup mode triggered"
  error_output: >
    BluetoothPairing init fails; bluetoothctl subprocess not found or returns
    non-zero exit on macOS. Status dot permanently shows disconnected colour.

behavior:
  expected: >
    On macOS, setup mode enumerates /dev/cu.* serial ports (Bluetooth SPP devices
    paired via System Preferences) and presents them for selection. On selection,
    the port path is stored in DeviceStore and SerialTransport uses it to connect.
    Status indicator reads thread 'transport' and reflects actual connection state.
  actual: >
    Setup mode attempts to invoke bluetoothctl via BluetoothPairing; this fails on
    macOS. Status indicator checks thread 'bluetooth' which does not exist; always
    evaluates to DISCONNECTED.
  impact: >
    macOS setup mode is entirely non-functional. Status indicator provides no
    useful information on macOS. Neither defect surfaces a Python exception visible
    to the user — both fail silently.
  workaround: >
    Manually create devices.yaml with a known port path to skip setup mode.
    No workaround for status indicator.

environment:
  python_version: "3.9+"
  os: "macOS 14+ (Darwin)"
  dependencies:
    - library: "pyserial"
      version: ">=3.5"
    - library: "pygame"
      version: ">=2.0"
  domain: "domain_1"

analysis:
  root_cause: >
    Defect 1: BluetoothSetupInterface.start_discovery() unconditionally
    instantiates BluetoothPairing regardless of platform. No macOS code
    path exists.
    Defect 2: The transport thread was renamed from 'bluetooth' to 'transport'
    in app.py during the transport abstraction refactor (change e1f2a3b4) but
    _draw_status_indicator was not updated.
  technical_notes: >
    For Defect 1: SerialTransport._discover_port() already implements /dev/cu.*
    port scanning with ELM/OBD pattern matching. The fix wraps the discovery
    worker with a platform check: on Darwin, call list_ports.comports() directly
    (the same logic used by SerialTransport) and populate state.discovered_devices
    with synthetic BluetoothDevice objects carrying the port path in mac_address.
    DeviceStore already stores this field; SerialTransport reads it on connect.
    BluetoothPairing is not instantiated on macOS.
    For Defect 2: Replace the string literal 'bluetooth' with 'transport' in
    _draw_status_indicator.
  related_issues:
    - issue_ref: "issue-e1f2a3b4 (transport abstraction — change e1f2a3b4)"
      relationship: "related"

resolution:
  approach: >
    Defect 1: Add platform guard to BluetoothSetupInterface._init_bluetooth_pairing
    and start_discovery; provide macOS serial port discovery path.
    Defect 2: Fix thread name string in _draw_status_indicator.
  change_ref: "change-a8b9c0d1"
  resolved_date: "2026-04-01"
  resolved_by: "Claude Code"
  fix_description: >\n    Defect 1: Added platform guard to BluetoothSetupInterface.__init__ skipping\n    BluetoothPairing on Darwin. Added _start_macos_serial_discovery() method using\n    serial.tools.list_ports to enumerate /dev/cu.* ports. Darwin branch added to\n    start_discovery(). Defect 2: Fixed _draw_status_indicator comment and thread\n    name reference 'bluetooth' -> 'transport' in manager.py.

traceability:
  design_refs:
    - "design-gtach-master.md"
    - "design-7d3e9f5a-domain_comm.md"
    - "design-2c6b8e4d-domain_display.md"
  change_refs:
    - "change-a8b9c0d1"

version_history:
  - version: "1.0"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Initial issue document"
  - version: "1.1"
    date: "2026-04-01"
    author: "William Watson"
    changes:
      - "Closed — implemented and verified"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | William Watson | Initial issue document |
| 1.1 | 2026-04-01 | William Watson | Closed — implemented and verified |

---

Copyright (c) 2026 William Watson. MIT License.
