Created: 2026 April 30

# Prompt: Sim Mode — Hardware-Free Full Application Testing

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Error Handling](<#5.0 error handling>)
- [6.0 Deliverables](<#6.0 deliverables>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

```yaml
prompt_info:
  id: "prompt-c7e2f1a9"
  task_type: "code_generation"
  source_ref: "change-c7e2f1a9"
  date: "2026-04-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-c7e2f1a9"
    change_iteration: 1
```

---

## 1.0 Prompt Information

Implement sim mode for GTach. Two new `--transport` values (`simtcp`, `simbt`) enable
full application testing without hardware or external processes.

Related documents:
- [change-c7e2f1a9-sim-mode.md](<../change/change-c7e2f1a9-sim-mode.md>)
- [issue-c7e2f1a9-sim-mode.md](<../issues/issue-c7e2f1a9-sim-mode.md>)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Add SimTransport (synthetic ELM327 OBD responses) and SimBluetoothPairing
    (scripted device discovery and pairing) to enable hardware-free testing of all
    GTach application states: RPM display, disconnected state, setup wizard,
    pairing success, and pairing failure.

  integration: >
    SimTransport slots into the existing OBDTransport abstraction.
    SimBluetoothPairing is injected into BluetoothSetupInterface via a new
    optional pairing_factory parameter. app.py wires both into the application
    when --transport simbt is specified.

  knowledge_references: []

  constraints:
    - "Python 3.9+ — no walrus operator (:=) in conditionals"
    - "No new runtime dependencies — math, time, random, threading from stdlib only"
    - "SimTransport must implement all four OBDTransport abstract methods"
    - "SimBluetoothPairing must be duck-type compatible with BluetoothPairing public interface"
    - "pairing_factory parameter addition to BluetoothSetupInterface must be backward-compatible (default None)"
    - "Do not modify RFCOMMTransport, SerialTransport, TCPTransport, or pairing.py"
    - "Conditional imports pattern applies: guard any optional imports with try/except"
    - "All logging via logging.getLogger(__name__) — no print statements"
    - "Production mode produces no log output (NullHandler); --debug enables DEBUG level"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Six source file changes: two new modules, four targeted modifications.
    All changes are additive; no existing behaviour is altered.

  requirements:
    functional:
      - "simtcp: SimTransport only; app bypasses device store check and enters normal mode"
      - "simbt: SimTransport + SimBluetoothPairing; app enters setup mode with sim pairing"
      - "SimTransport.connect() always returns True immediately"
      - "SimTransport.send_command('010C') returns hex-encoded RPM from sine sweep 800-6500 RPM, ~12 s period"
      - "SimTransport responds to all standard ELM327 AT init commands with canonical strings"
      - "SimBluetoothPairing.discover_elm327_devices() fires progress_callback at 0%, 33%, 66%, 100% with ~0.75 s sleep between steps, returns 4 scripted BluetoothDevice instances"
      - "SimBluetoothPairing.pair_device() fires status_callback(CONNECTING), sleeps 1 s, fires status_callback(TESTING), sleeps 1 s, then returns True if random.random() > 0.2 else calls status_callback(FAILED) and returns False"
      - "BluetoothSetupInterface accepts optional pairing_factory=None; uses it in place of bare BluetoothPairing() when provided"
      - "SetupDisplayManager accepts optional pairing_factory=None; forwards to BluetoothSetupInterface"
      - "app.py: 'simtcp' treated as transport_forced (same as 'tcp'); 'simbt' enters setup mode with SimBluetoothPairing factory injected"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8"
        - "Type hints on all public interfaces"
        - "Google-style docstrings"
        - "Thread-safe where concurrent access exists"
        - "Copyright header: Copyright (c) 2025 William Watson. MIT License."
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: >
    SimTransport extends OBDTransport ABC. SimBluetoothPairing is a standalone
    class (no base class) duck-typing BluetoothPairing. Injection via callable
    factory parameter preserves existing call sites unchanged.

  components:

    - name: "SimTransport"
      type: "class"
      purpose: "OBDTransport implementation returning synthetic ELM327 responses"
      interface:
        inputs: []
        outputs:
          type: "OBDTransport"
          description: "Drop-in transport requiring no hardware"
      logic:
        - "Inherit from OBDTransport (src/gtach/comm/transport.py)"
        - "Store _connected = True on init; state = CONNECTED"
        - "connect(): set _shutdown clear, return True"
        - "disconnect(): set _shutdown, set _connected = False"
        - "is_connected(): return True always (sim never drops)"
        - "state property: return TransportState.CONNECTED"
        - "send_command(command, timeout): strip and upper-case command, dispatch:"
        - "  'ATZ'  -> 'ELM327 v1.5'"
        - "  'ATE0' -> 'OK'"
        - "  'ATL0' -> 'OK'"
        - "  'ATS0' -> 'OK'"
        - "  'ATH0' -> 'OK'"
        - "  'ATSP0','ATSP8','ATSP6' -> 'OK'"
        - "  '0100' -> '41 00 BE 3E B8 11'"
        - "  '010C' -> compute RPM: rpm = 800 + 2850 * (1 + math.sin(time.time() * 2 * math.pi / 12.0)) (gives 800-6500); encode as ELM327 hex: A = int(rpm * 4) >> 8 & 0xFF, B = int(rpm * 4) & 0xFF; return f'41 0C {A:02X} {B:02X}'"
        - "  Any other command -> 'NO DATA'"
        - "Log send/receive at DEBUG level"

    - name: "SimBluetoothPairing"
      type: "class"
      purpose: "Duck-type replacement for BluetoothPairing; scripted discovery and pairing"
      interface:
        inputs: []
        outputs:
          type: "BluetoothPairing-compatible object"
          description: "Usable anywhere BluetoothPairing is used"
      logic:
        - "Import BluetoothDevice, PairingStatus from display.setup_models"
        - "Import DeviceType from display.setup_models"
        - "_FAKE_DEVICES: list of 4 BluetoothDevice instances defined at class/module level:"
        - "  name='ELM327 OBD Adapter', mac_address='AA:BB:CC:DD:EE:01', device_type='ELM327'"
        - "  name='OBDLink MX+', mac_address='AA:BB:CC:DD:EE:02', device_type='ELM327'"
        - "  name='VEEPEAK OBD2', mac_address='AA:BB:CC:DD:EE:03', device_type='ELM327'"
        - "  name='Generic BT Adapter', mac_address='AA:BB:CC:DD:EE:04', device_type='Compatible'"
        - "discover_elm327_devices(timeout, progress_callback, device_found_callback, show_all_devices):"
        - "  Set _discovery_active = True"
        - "  For progress in [0.0, 0.33, 0.66, 1.0]: call progress_callback(progress) if set, sleep 0.75 s"
        - "  For each device: call device_found_callback(device) if set"
        - "  Set _discovery_active = False; return _FAKE_DEVICES copy"
        - "discover_all_devices(timeout, progress_callback, device_found_callback):"
        - "  Delegate to discover_elm327_devices with show_all_devices=True"
        - "pair_device(device, status_callback):"
        - "  Set _pairing_active = True"
        - "  Call status_callback(PairingStatus.CONNECTING, 'Connecting...') if set; sleep 1.0"
        - "  Call status_callback(PairingStatus.TESTING, 'Testing...') if set; sleep 1.0"
        - "  success = random.random() > 0.2"
        - "  If success: call status_callback(PairingStatus.SUCCESS, 'Connected') if set"
        - "  Else: call status_callback(PairingStatus.FAILED, 'Simulated failure') if set"
        - "  Set _pairing_active = False; return success"
        - "cancel_discovery(): set _cancel_discovery event; log INFO"
        - "cancel_pairing(): set _cancel_pairing event; log INFO"
        - "shutdown(): log INFO; no-op otherwise"
        - "is_discovery_active(): return _discovery_active"
        - "is_pairing_active(): return _pairing_active"
        - "bluetooth_available attribute = True"

    - name: "select_transport (modify)"
      type: "function"
      purpose: "Add simtcp and simbt branches to factory"
      logic:
        - "Before the existing platform auto-detect block add:"
        - "  if transport_arg in ('simtcp', 'simbt'): from .sim_transport import SimTransport; return SimTransport()"

    - name: "parse_arguments (modify)"
      type: "function"
      purpose: "Extend --transport choices"
      logic:
        - "Change choices=['tcp','serial','rfcomm'] to choices=['tcp','serial','rfcomm','simtcp','simbt']"

    - name: "BluetoothSetupInterface.__init__ (modify)"
      type: "method"
      purpose: "Accept optional pairing_factory for sim injection"
      logic:
        - "Add pairing_factory=None parameter"
        - "Store as self._pairing_factory = pairing_factory"
        - "Replace both BluetoothPairing() instantiations (lines ~52 and ~111) with:"
        - "  (self._pairing_factory if self._pairing_factory else BluetoothPairing)()"
        - "On macOS (platform.system() == 'Darwin'): if pairing_factory is not None, skip the Darwin skip-branch and allow pairing_factory to be used; set self._pairing_ready"

    - name: "SetupDisplayManager.__init__ (modify)"
      type: "method"
      purpose: "Forward pairing_factory to BluetoothSetupInterface"
      logic:
        - "Add pairing_factory=None parameter"
        - "Pass pairing_factory=pairing_factory to BluetoothSetupInterface() constructor"

    - name: "GTachApplication.start / _start_setup_mode (modify)"
      type: "method"
      purpose: "Wire simbt into setup mode with SimBluetoothPairing factory"
      logic:
        - "Extend transport_forced condition: transport_arg in ('tcp', 'serial', 'simtcp')"
        - "Add simbt branch before existing setup/normal mode check:"
        - "  elif transport_arg == 'simbt':"
        - "    self._setup_mode = True"
        - "    self._start_setup_mode(pairing_factory=lambda: SimBluetoothPairing())"
        - "Add pairing_factory=None parameter to _start_setup_mode"
        - "Pass pairing_factory=pairing_factory to SetupDisplayManager constructor"
        - "Import SimBluetoothPairing at top of simbt branch (lazy import)"

  dependencies:
    internal:
      - "src/gtach/comm/transport.py — OBDTransport, TransportState"
      - "src/gtach/display/setup_models.py — BluetoothDevice, PairingStatus, DeviceType"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: >
    Sim classes do not raise exceptions in normal operation. Log at DEBUG level.
    Unexpected errors in discover/pair paths caught and logged; return empty list
    or False respectively.

  exceptions:
    - exception: "Exception (general)"
      condition: "Unexpected error in SimBluetoothPairing discover or pair"
      handling: "Log ERROR with exc_info=True; return [] or False"

  logging:
    level: "DEBUG for send/receive; INFO for connect/disconnect/discovery events"
    format: "%(asctime)s %(name)s %(levelname)s %(message)s"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Save all files to the exact paths listed below"
    - "Do not modify any file not listed below"
    - "Verify syntax with: python -c \"import ast; ast.parse(open('<path>').read())\""

  files:
    - path: "src/gtach/comm/sim_transport.py"
      content: "New file — SimTransport class"
    - path: "src/gtach/comm/sim_bluetooth.py"
      content: "New file — SimBluetoothPairing class"
    - path: "src/gtach/comm/transport.py"
      content: "Modify — add simtcp/simbt branches to select_transport()"
    - path: "src/gtach/main.py"
      content: "Modify — extend --transport choices"
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "Modify — add pairing_factory parameter; replace BluetoothPairing() instantiations"
    - path: "src/gtach/app.py"
      content: "Modify — simbt branch; pairing_factory forwarding; _start_setup_mode signature"
    - path: "src/gtach/display/setup.py"
      content: "Modify — add pairing_factory parameter to SetupDisplayManager.__init__; forward to BluetoothSetupInterface"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "All 7 files written with no syntax errors (ast.parse passes)"
  - "python -m gtach --transport simtcp --debug starts without error on macOS"
  - "python -m gtach --transport simbt --debug enters setup mode without error on macOS"
  - "SimTransport.send_command('010C') returns a string matching r'41 0C [0-9A-F]{2} [0-9A-F]{2}'"
  - "RPM decoded from response is in range 800-6500"
  - "SimBluetoothPairing.discover_elm327_devices() returns exactly 4 BluetoothDevice instances"
  - "SimBluetoothPairing.pair_device() returns False at least once in 10 sequential calls (20% failure rate)"
  - "Existing --transport tcp, serial, rfcomm paths unaffected"
  - "BluetoothSetupInterface() called with no arguments behaves identically to before this change"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: implement sim mode for GTach (change-c7e2f1a9).

  CREATE src/gtach/comm/sim_transport.py
    Class SimTransport(OBDTransport). connect()->True, disconnect()->no-op,
    is_connected()->True, state->CONNECTED. send_command() dispatches:
      ATZ->'ELM327 v1.5', ATE0/ATL0/ATS0/ATH0/ATSP*->'OK',
      0100->'41 00 BE 3E B8 11',
      010C->compute rpm=800+2850*(1+sin(t*2pi/12)), encode A=int(rpm*4)>>8&0xFF,
        B=int(rpm*4)&0xFF, return f'41 0C {A:02X} {B:02X}',
      else->'NO DATA'. Log TX/RX at DEBUG.

  CREATE src/gtach/comm/sim_bluetooth.py
    Class SimBluetoothPairing. 4 hardcoded BluetoothDevice instances (ELM327 type).
    discover_elm327_devices(): progress_callback at 0/0.33/0.66/1.0 with 0.75s
      sleep between steps; device_found_callback per device; return 4 devices.
    discover_all_devices(): delegates to discover_elm327_devices.
    pair_device(): status_callback(CONNECTING), sleep 1s, status_callback(TESTING),
      sleep 1s, success=random()>0.2, callback SUCCESS or FAILED, return bool.
    Stubs: cancel_discovery, cancel_pairing, shutdown, is_discovery_active,
      is_pairing_active. bluetooth_available=True.

  MODIFY src/gtach/comm/transport.py — select_transport():
    Add before platform auto-detect:
      if transport_arg in ('simtcp','simbt'):
          from .sim_transport import SimTransport; return SimTransport()

  MODIFY src/gtach/main.py — parse_arguments():
    choices=['tcp','serial','rfcomm','simtcp','simbt']

  MODIFY src/gtach/display/setup_components/bluetooth/interface.py:
    BluetoothSetupInterface.__init__(self, pairing_factory=None).
    self._pairing_factory = pairing_factory.
    Both BluetoothPairing() calls -> (self._pairing_factory or BluetoothPairing)().
    If pairing_factory is not None on Darwin: skip the Darwin skip-branch,
      proceed with init_bluetooth_pairing_async using the factory.

  MODIFY src/gtach/display/setup.py:
    SetupDisplayManager.__init__(self, surface, thread_manager, touch_handler, pairing_factory=None).
    Pass pairing_factory=pairing_factory to BluetoothSetupInterface().

  MODIFY src/gtach/app.py:
    transport_forced: transport_arg in ('tcp','serial','simtcp').
    Add elif transport_arg == 'simbt': branch that calls
      self._start_setup_mode(pairing_factory=lambda: SimBluetoothPairing()).
    _start_setup_mode(self, pairing_factory=None): pass pairing_factory to
      SetupDisplayManager constructor.
    Lazy import: from .comm.sim_bluetooth import SimBluetoothPairing inside simbt branch.

  VERIFY: python -c "import ast; ast.parse(open('src/gtach/comm/sim_transport.py').read())"
    (repeat for all 7 files). Run: python -m gtach --transport simtcp --debug (must start).
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-04-30 | William Watson | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
