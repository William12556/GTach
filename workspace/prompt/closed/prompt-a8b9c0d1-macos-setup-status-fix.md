# Prompt: macOS Setup Mode Serial Discovery + Status Indicator Fix

Created: 2026-04-01

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Source Reference](<#5.0 source reference>)
- [6.0 Deliverable](<#6.0 deliverable>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-a8b9c0d1"
  task_type: "code_generation"
  source_ref: "change-a8b9c0d1"
  date: "2026-04-01"
  iteration: 1
  coupled_docs:
    change_ref: "change-a8b9c0d1"
    change_iteration: 1
```

---

## 2.0 Context

```yaml
context:
  purpose: >
    Two defects prevent macOS from functioning as a complete Pi development
    environment.
    Defect 1: BluetoothSetupInterface unconditionally initialises BluetoothPairing
    and calls bluetoothctl during device discovery. bluetoothctl is Linux-only;
    this fails immediately on macOS. On macOS, Classic Bluetooth devices paired
    via System Preferences appear as /dev/cu.* serial ports. Setup mode must
    enumerate these ports instead.
    Defect 2: DisplayManager._draw_status_indicator checks for a thread named
    'bluetooth'. The transport thread is registered as 'transport' in app.py
    (line 115). The indicator therefore permanently shows DISCONNECTED.
  integration: >
    BluetoothSetupInterface is in setup_components/bluetooth/interface.py.
    It uses an async operation framework (async_manager.submit_operation) to run
    discovery in a worker thread. The macOS path must follow the same async
    pattern so the existing state machine and UI render loop are unaffected.
    BluetoothDevice.mac_address is an opaque string; on macOS it will hold the
    /dev/cu.* port path. DeviceStore and SerialTransport already treat this field
    as an opaque identifier.
  constraints:
    - "Only two files modified: interface.py and manager.py"
    - "Pi/Linux discovery path (bluetoothctl) must be unchanged"
    - "Async operation pattern must be preserved for the macOS discovery path"
    - "No changes to DeviceStore, SerialTransport, BluetoothDevice, or any other file"
    - "pyserial (serial.tools.list_ports) is already a project dependency"
```

---

## 3.0 Specification

```yaml
specification:
  description: >
    Defect 1: Add a macOS serial port discovery path to BluetoothSetupInterface.
    Skip BluetoothPairing initialisation on Darwin. In start_discovery(), detect
    Darwin and dispatch a serial port enumeration task instead of the bluetoothctl
    task. Populate state.discovered_devices with BluetoothDevice objects where
    mac_address holds the /dev/cu.* path.
    Defect 2: Replace the string literal 'bluetooth' with 'transport' in
    DisplayManager._draw_status_indicator.
  requirements:
    functional:
      - "On Darwin, BluetoothPairing is never instantiated; _pairing_ready is set immediately"
      - "On Darwin, start_discovery() enumerates /dev/cu.* ports via serial.tools.list_ports"
      - "Port filter: device path contains '/dev/cu.' AND (name or description contains ELM or OBD case-insensitive)"
      - "Unfiltered fallback: if no ELM/OBD match found, include all /dev/cu.* ports"
      - "Each matching port becomes BluetoothDevice(name=port.description or port.device, mac_address=port.device, device_type='ELM327')"
      - "state.discovered_devices populated; state.pairing_status set to IDLE on completion"
      - "Status indicator thread lookup uses key 'transport' not 'bluetooth'"
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Import platform at top of interface.py (add if absent)"
        - "Import serial.tools.list_ports in the Darwin discovery method (local import inside method is acceptable)"
        - "Error handling with logger.error and exc_info=True"
        - "Debug logging for each port found/skipped"
```

---

## 4.0 Design

### 4.1 BluetoothSetupInterface changes

```yaml
design:
  components:
    - name: "BluetoothSetupInterface.__init__ (Darwin guard)"
      type: "method section"
      purpose: "Skip bluetoothctl initialisation on macOS"
      logic:
        - "Add: import platform at module level (or inside __init__)"
        - "Replace unconditional call to self._init_bluetooth_pairing_async() with:"
        - "  if platform.system() != 'Darwin':"
        - "      self._init_bluetooth_pairing_async()"
        - "  else:"
        - "      self.logger.info('macOS: skipping BluetoothPairing init; using serial discovery')"
        - "      self._pairing_ready.set()  # Not needed on macOS but keeps state consistent"

    - name: "BluetoothSetupInterface.start_discovery (Darwin branch)"
      type: "method section"
      purpose: "Route macOS discovery to serial port enumeration"
      logic:
        - "At the start of start_discovery(), before the existing async submit block, add:"
        - "  if platform.system() == 'Darwin':"
        - "      self._start_macos_serial_discovery(state)"
        - "      return"
        - "Existing Linux/Pi code is unchanged below the guard"

    - name: "BluetoothSetupInterface._start_macos_serial_discovery"
      type: "method"
      purpose: "Enumerate /dev/cu.* serial ports and populate state.discovered_devices"
      interface:
        inputs:
          - name: "state"
            type: "SetupState"
            description: "Setup state object to populate"
        outputs:
          type: "None"
      logic:
        - "def _macos_discovery_task(progress_callback_inner=None):"
        - "  from serial.tools import list_ports"
        - "  state.pairing_status = PairingStatus.DISCOVERING"
        - "  state.discovered_devices = []"
        - "  if progress_callback_inner: progress_callback_inner(0.1, 'Scanning serial ports...')"
        - "  matched = []"
        - "  all_cu = []"
        - "  patterns = ['elm', 'obd']"
        - "  for port in list_ports.comports():"
        - "      if '/dev/cu.' not in port.device: continue"
        - "      all_cu.append(port)"
        - "      name_lower = port.device.lower()"
        - "      desc_lower = (port.description or '').lower()"
        - "      if any(p in name_lower or p in desc_lower for p in patterns):"
        - "          matched.append(port)"
        - "          logger.debug('macOS: matched port %s (%s)', port.device, port.description)"
        - "  candidates = matched if matched else all_cu"
        - "  for port in candidates:"
        - "      device = BluetoothDevice("
        - "          name=port.description if port.description else port.device,"
        - "          mac_address=port.device,"
        - "          device_type='ELM327'"
        - "      )"
        - "      state.discovered_devices.append(device)"
        - "  if progress_callback_inner: progress_callback_inner(1.0, f'{len(state.discovered_devices)} port(s) found')"
        - "  return state.discovered_devices"
        - ""
        - "def on_complete(operation):"
        - "  if operation.status == OperationStatus.COMPLETED:"
        - "      state.pairing_status = PairingStatus.IDLE"
        - "      self.logger.info('macOS serial discovery complete: %d port(s)', len(state.discovered_devices))"
        - "  else:"
        - "      state.pairing_status = PairingStatus.FAILED"
        - "      self.logger.error('macOS serial discovery failed: %s', operation.error)"
        - "  if 'device_discovery' in self._active_operations:"
        - "      del self._active_operations['device_discovery']"
        - ""
        - "operation_id = self.async_manager.submit_operation("
        - "    OperationType.DEVICE_DISCOVERY, _macos_discovery_task,"
        - "    progress_callback=on_complete"
        - ")"
        - "self._active_operations['device_discovery'] = operation_id"
        - "self.logger.info('macOS serial discovery started (operation: %s)', operation_id)"

    - name: "DisplayManager._draw_status_indicator (thread name fix)"
      type: "method"
      purpose: "Fix stale thread name reference"
      logic:
        - "In src/gtach/display/manager.py, _draw_status_indicator:"
        - "  Change: if 'bluetooth' not in self.thread_manager.threads:"
        - "  To:     if 'transport' not in self.thread_manager.threads:"
        - "  Change: thread_status = self.thread_manager.threads['bluetooth'].status"
        - "  To:     thread_status = self.thread_manager.threads['transport'].status"
        - "  (There may be one combined check — replace any occurrence of 'bluetooth' with 'transport' in this method only)"
```

---

## 5.0 Source Reference

Read the following files before implementing. Modify only `interface.py` and `manager.py`.

- `src/gtach/display/setup_components/bluetooth/interface.py` — primary file; read fully
- `src/gtach/display/manager.py` — read `_draw_status_indicator` method only
- `src/gtach/display/setup_models.py` — confirm `BluetoothDevice` constructor signature and `PairingStatus` enum values
- `src/gtach/display/async_operations.py` — confirm `OperationType.DEVICE_DISCOVERY` exists

### BluetoothDevice constructor (from setup_models.py — confirm before use)

Expected signature: `BluetoothDevice(name: str, mac_address: str, device_type: str = 'UNKNOWN')`

Verify this matches what is in setup_models.py before implementing.

---

## 6.0 Deliverable

```yaml
deliverable:
  files:
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "Modified in place — Darwin guard in __init__, Darwin branch in start_discovery, new _start_macos_serial_discovery method"
    - path: "src/gtach/display/manager.py"
      content: "Modified in place — 'bluetooth' -> 'transport' in _draw_status_indicator"
```

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "On Darwin, BluetoothPairing.__init__ is never called"
  - "On Darwin, start_discovery() calls _start_macos_serial_discovery() and returns"
  - "Linux/Pi start_discovery() code path is structurally unchanged"
  - "_draw_status_indicator references 'transport' not 'bluetooth'"
  - "No other files modified"
  - "Syntax check passes for both files:"
  - "  python -c \"import ast; ast.parse(open('src/gtach/display/setup_components/bluetooth/interface.py').read())\""
  - "  python -c \"import ast; ast.parse(open('src/gtach/display/manager.py').read())\""
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Modify two files: interface.py and manager.py.

  FILE 1: src/gtach/display/setup_components/bluetooth/interface.py

  Step 1 — Add platform import at module level if not present:
      import platform

  Step 2 — In __init__, replace:
      self._init_bluetooth_pairing_async()
  With:
      if platform.system() != 'Darwin':
          self._init_bluetooth_pairing_async()
      else:
          self.logger.info('macOS: skipping BluetoothPairing; using serial discovery')
          self._pairing_ready.set()

  Step 3 — At the start of start_discovery(), before the existing try block, add:
      if platform.system() == 'Darwin':
          self._start_macos_serial_discovery(state)
          return

  Step 4 — Add new method _start_macos_serial_discovery(self, state):
    Verify BluetoothDevice constructor signature in setup_models.py first.
    The method must:
    - Submit an async DEVICE_DISCOVERY operation via self.async_manager.submit_operation()
    - The task function enumerates serial.tools.list_ports.comports()
    - Filter to ports where '/dev/cu.' is in port.device
    - Match ELM/OBD patterns (case-insensitive) against device name and description
    - If no matches, fall back to all /dev/cu.* ports
    - Create BluetoothDevice for each candidate; populate state.discovered_devices
    - Set state.pairing_status = PairingStatus.IDLE on success, FAILED on error
    - Track operation in self._active_operations['device_discovery']

  FILE 2: src/gtach/display/manager.py

  Step 5 — In _draw_status_indicator, replace all occurrences of the string
  'bluetooth' with 'transport' (this method only — grep the method to find them).

  After both edits, run syntax checks:
    python -c "import ast; ast.parse(open('src/gtach/display/setup_components/bluetooth/interface.py').read())"
    python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | William Watson | Initial prompt document |
| 1.1 | 2026-04-01 | William Watson | Closed — executed by Claude Code and verified |

---

Copyright (c) 2026 William Watson. MIT License.
