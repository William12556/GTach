# Prompt: Comm Transport Abstraction — New Files

Created: 2026 March 24

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Deliverables](<#5.0 deliverables>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Element Registry](<#7.0 element registry>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-e1f2a3b4"
  task_type: "code_generation"
  source_ref: "change-e1f2a3b4-comm-transport-abstraction.md"
  date: "2026-03-24"
  priority: "high"
  iteration: 1
  sequence: "1 of 3"
  coupled_docs:
    change_ref: "change-e1f2a3b4"
    change_iteration: 1

tactical_execution:
  mode: "ralph_loop"
  worker_model: "Devstral-Small-2-24B-Instruct-2512"
  reviewer_model: "Devstral-Small-2-24B-Instruct-2512"
  max_iterations: 20
  boundary_conditions:
    token_budget: 50000
    time_limit_minutes: 30

notes: >
  Context window: 393,216 tokens (Devstral-Small-2-24B-Instruct-2512).
  max_iterations: 20 — outer Ralph Loop cycles (worker+reviewer pairs).
  phase_max_iterations: set in config.yaml — inner tool-call iterations per phase.
  Previous run failed at 5 iterations (insufficient for 4 file writes + reads).
```

---

## 2.0 Context

```yaml
context:
  purpose: >
    Create four new Python source files implementing the OBDTransport abstraction
    layer for the GTach comm domain. These files replace the Bleak/BLE-based
    BluetoothManager with transport-agnostic interfaces for Classic Bluetooth
    RFCOMM, pyserial, and TCP socket communication.

  integration: >
    GTach is a Raspberry Pi tachometer application. The comm domain connects to
    an ELM327 OBD-II adapter. These new files form the foundation of the comm
    layer redesign. Subsequent prompts (2 of 3, 3 of 3) modify existing files
    to consume these interfaces. No existing files are modified in this prompt.

  project_root: "/Users/williamwatson/Documents/GitHub/GTach"
  source_root: "src/gtach/comm/"
  entry_point: "gtach.main:main (pyproject.toml [project.scripts])"

  constraints:
    - "Python >= 3.9"
    - "No async/await — all transports are synchronous and blocking"
    - "No third-party libraries except pyserial (SerialTransport only)"
    - "Thread-safe state via threading.RLock on _state and _sock/_serial attributes"
    - "All files include MIT license header matching existing source style"
    - "Do not modify any existing files in this task"
```

---

## 3.0 Specification

```yaml
specification:
  description: >
    Create four new files:
      1. src/gtach/comm/transport.py  — OBDTransport ABC, TransportState, TransportError hierarchy, select_transport() factory
      2. src/gtach/comm/rfcomm.py     — RFCOMMTransport: RFCOMM socket (AF_BLUETOOTH/BTPROTO_RFCOMM)
      3. src/gtach/comm/tcp_transport.py — TCPTransport: TCP socket (AF_INET)
      4. src/gtach/comm/serial_transport.py — SerialTransport: pyserial

  requirements:
    functional:
      - "OBDTransport ABC defines: connect()->bool, disconnect()->None, send_command(str,float)->Optional[str], is_connected()->bool, state property->TransportState"
      - "OBDTransport provides concrete reconnect_indefinitely(retry_delay) that loops connect() until success or _shutdown set"
      - "TransportState enum: DISCONNECTED, CONNECTING, CONNECTED, ERROR"
      - "TransportError base exception with subclasses: ConnectionError, TimeoutError, ProtocolError"
      - "select_transport(platform_type, args) factory: checks args.transport first ('tcp','serial','rfcomm'); falls back to platform auto-detect (MACOS->SerialTransport, RASPBERRY_PI->RFCOMMTransport); raises TransportError for unsupported platform with no CLI arg"
      - "RFCOMMTransport: socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM); connect to (mac_address, channel=1); send_command encodes command+'\\r', reads until '>' prompt; returns stripped response string or None on timeout/error"
      - "TCPTransport: socket(AF_INET, SOCK_STREAM); connect to (host, port); same send_command protocol as RFCOMM"
      - "SerialTransport: serial.Serial(port, baudrate=38400, timeout=2); auto-discover port via serial.tools.list_ports if port=None (match 'ELM','OBD','OBDII' in device or description, case-insensitive); send_command uses serial.read_until(b'>')"
      - "All transports: connect() sets CONNECTING then CONNECTED/DISCONNECTED; OSError/SerialException -> DISCONNECTED, return False; on recv() empty -> DISCONNECTED"
      - "All transports: send_command() returns None immediately if not CONNECTED"
      - "select_transport reads DeviceStore().get_primary_device() for mac_address when routing to RFCOMMTransport; raises TransportError('No paired device found') if None"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread safety: _lock (threading.RLock) guards _state and socket/serial handle"
        - "Logging: module-level logger named after class (e.g. logging.getLogger('RFCOMMTransport'))"
        - "Docstrings on all public methods"
        - "Type annotations on all method signatures"
        - "MIT license header block at top of each file (match style of existing src/gtach/comm/bluetooth.py)"
```

---

## 4.0 Design

### 4.1 transport.py

```yaml
components:
  - name: "TransportState"
    type: "enum"
    logic:
      - "from enum import Enum, auto"
      - "Members: DISCONNECTED, CONNECTING, CONNECTED, ERROR"

  - name: "TransportError"
    type: "exception hierarchy"
    logic:
      - "class TransportError(Exception): pass"
      - "class ConnectionError(TransportError): pass"
      - "class TimeoutError(TransportError): pass"
      - "class ProtocolError(TransportError): pass"

  - name: "OBDTransport"
    type: "class (ABC)"
    logic:
      - "from abc import ABC, abstractmethod"
      - "_shutdown = threading.Event() in __init__"
      - "_lock = threading.RLock() in __init__"
      - "Abstract: connect, disconnect, send_command, is_connected, state (property)"
      - "Concrete reconnect_indefinitely(retry_delay=5.0): while not _shutdown.is_set(): if connect(): return; log warning; time.sleep(retry_delay)"

  - name: "select_transport"
    type: "function"
    logic:
      - "signature: select_transport(platform_type: PlatformType, args: argparse.Namespace) -> OBDTransport"
      - "Import: from ..utils.platform import PlatformType"
      - "Import: from .device_store import DeviceStore"
      - "Import: from .rfcomm import RFCOMMTransport"
      - "Import: from .serial_transport import SerialTransport"
      - "Import: from .tcp_transport import TCPTransport"
      - "transport_arg = getattr(args, 'transport', None)"
      - "if transport_arg == 'tcp': return TCPTransport(host=getattr(args,'obd_host','localhost'), port=getattr(args,'obd_port',35000))"
      - "if transport_arg == 'serial': return SerialTransport(port=getattr(args,'serial_port',None))"
      - "if transport_arg == 'rfcomm': _get_rfcomm()"
      - "if no arg: MACOS -> SerialTransport(); RASPBERRY_PI_* -> _get_rfcomm()"
      - "else: raise TransportError('Unsupported platform')"
      - "_get_rfcomm(): ds=DeviceStore(); dev=ds.get_primary_device(); if not dev: raise TransportError('No paired device found'); return RFCOMMTransport(mac_address=dev.mac_address)"
```

### 4.2 rfcomm.py

```yaml
components:
  - name: "RFCOMMTransport"
    type: "class"
    dependencies:
      internal: ["OBDTransport", "TransportState"]
      external: ["socket"]
    logic:
      - "__init__(self, mac_address: str, channel: int = 1, retry_delay: float = 5.0)"
      - "_mac_address, _channel, _retry_delay stored; _sock = None; _state = DISCONNECTED"
      - "connect(): acquire _lock; set CONNECTING; create socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM); settimeout(10); connect((mac, channel)); settimeout(None); set CONNECTED; return True; on OSError: close sock; set DISCONNECTED; log error; return False"
      - "disconnect(): set _shutdown; close _sock under _lock; _sock=None; _state=DISCONNECTED"
      - "send_command(command, timeout=2.0): if not is_connected(): return None; encode (command.strip()+'\\r').encode('ascii'); sock.sendall(encoded); sock.settimeout(timeout); buf=b''; loop recv(1024) accumulating until b'>' in buf; decode; strip prompt+whitespace; return string; on socket.timeout: return None; on OSError or empty recv: set DISCONNECTED; return None"
      - "is_connected(): with _lock: return _state == TransportState.CONNECTED"
      - "state property: with _lock: return _state"
```

### 4.3 tcp_transport.py

```yaml
components:
  - name: "TCPTransport"
    type: "class"
    dependencies:
      internal: ["OBDTransport", "TransportState"]
      external: ["socket"]
    logic:
      - "__init__(self, host: str = 'localhost', port: int = 35000, retry_delay: float = 5.0)"
      - "connect(): socket(AF_INET, SOCK_STREAM); settimeout(10); connect((host, port)); settimeout(None); set CONNECTED; return True; on ConnectionRefusedError/OSError: close; set DISCONNECTED; return False"
      - "send_command: identical pattern to RFCOMMTransport (encode, sendall, recv loop until '>'); on socket.timeout: return None; on OSError/empty: set DISCONNECTED; return None"
      - "disconnect, is_connected, state: same pattern as RFCOMMTransport"
```

### 4.4 serial_transport.py

```yaml
components:
  - name: "SerialTransport"
    type: "class"
    dependencies:
      internal: ["OBDTransport", "TransportState"]
      external: ["serial", "serial.tools.list_ports"]
    logic:
      - "__init__(self, port: Optional[str] = None, baudrate: int = 38400, retry_delay: float = 5.0)"
      - "_discover_port(): import serial.tools.list_ports; iterate comports(); match 'ELM','OBD','OBDII' case-insensitive in port.device or port.description; return first match device path or None"
      - "connect(): resolve port (self._port or _discover_port()); if None: log warning; set DISCONNECTED; return False; serial.Serial(port, baudrate, timeout=2); set CONNECTED; return True; on SerialException: set DISCONNECTED; return False"
      - "send_command(command, timeout=2.0): if not connected: return None; write (command.strip()+'\\r').encode('ascii'); self._serial.timeout = timeout; response = self._serial.read_until(b'>'); decode; strip; return string; on SerialException: set DISCONNECTED; return None"
      - "disconnect, is_connected, state: same pattern"
```

---

## 5.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Write files directly to specified paths using MCP filesystem tools"
    - "Do not print file content to stdout — write to disk only"
    - "Each file must be complete and importable"

  files:
    - path: "src/gtach/comm/transport.py"
      description: "OBDTransport ABC, TransportState, TransportError, select_transport()"
    - path: "src/gtach/comm/rfcomm.py"
      description: "RFCOMMTransport"
    - path: "src/gtach/comm/tcp_transport.py"
      description: "TCPTransport"
    - path: "src/gtach/comm/serial_transport.py"
      description: "SerialTransport"
```

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "All four files exist at specified paths"
  - "Each file has MIT license header"
  - "transport.py: OBDTransport is abstract (instantiating it raises TypeError); TransportState has 4 members; select_transport is callable"
  - "rfcomm.py: RFCOMMTransport(mac_address='AA:BB:CC:DD:EE:FF') instantiates without error on any platform"
  - "tcp_transport.py: TCPTransport() instantiates without error"
  - "serial_transport.py: SerialTransport() instantiates without error (port=None is valid)"
  - "No imports fail on macOS (AF_BLUETOOTH import is guarded — socket.AF_BLUETOOTH may not exist on macOS; guard with try/except AttributeError or hasattr check)"
  - "reconnect_indefinitely exits when _shutdown is set"
  - "All send_command implementations return None (not raise) on timeout or disconnection"
```

---

## 7.0 Element Registry

```yaml
element_registry:
  modules:
    - name: "gtach.comm.transport"
      path: "src/gtach/comm/transport.py"
    - name: "gtach.comm.rfcomm"
      path: "src/gtach/comm/rfcomm.py"
    - name: "gtach.comm.tcp_transport"
      path: "src/gtach/comm/tcp_transport.py"
    - name: "gtach.comm.serial_transport"
      path: "src/gtach/comm/serial_transport.py"

  classes:
    - name: "TransportState"
      module: "gtach.comm.transport"
      base_classes: ["enum.Enum"]
    - name: "TransportError"
      module: "gtach.comm.transport"
      base_classes: ["Exception"]
    - name: "ConnectionError"
      module: "gtach.comm.transport"
      base_classes: ["TransportError"]
    - name: "TimeoutError"
      module: "gtach.comm.transport"
      base_classes: ["TransportError"]
    - name: "ProtocolError"
      module: "gtach.comm.transport"
      base_classes: ["TransportError"]
    - name: "OBDTransport"
      module: "gtach.comm.transport"
      base_classes: ["abc.ABC"]
    - name: "RFCOMMTransport"
      module: "gtach.comm.rfcomm"
      base_classes: ["OBDTransport"]
    - name: "TCPTransport"
      module: "gtach.comm.tcp_transport"
      base_classes: ["OBDTransport"]
    - name: "SerialTransport"
      module: "gtach.comm.serial_transport"
      base_classes: ["OBDTransport"]

  functions:
    - name: "select_transport"
      module: "gtach.comm.transport"
      signature: "select_transport(platform_type: PlatformType, args: argparse.Namespace) -> OBDTransport"
    - name: "reconnect_indefinitely"
      module: "gtach.comm.transport"
      signature: "reconnect_indefinitely(self, retry_delay: float = 5.0) -> None"
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  TASK: Create 4 new Python files in src/gtach/comm/. Do NOT modify any existing files.

  FILES TO CREATE:
  1. src/gtach/comm/transport.py
     - TransportState(Enum): DISCONNECTED, CONNECTING, CONNECTED, ERROR
     - TransportError(Exception) + subclasses: ConnectionError, TimeoutError, ProtocolError
     - OBDTransport(ABC): abstract connect()->bool, disconnect()->None,
       send_command(str,float=2.0)->Optional[str], is_connected()->bool,
       state property->TransportState; concrete reconnect_indefinitely(retry_delay=5.0)
       loops connect() until success or self._shutdown.is_set()
     - select_transport(platform_type: PlatformType, args: argparse.Namespace) -> OBDTransport
       Checks args.transport ('tcp'->TCPTransport, 'serial'->SerialTransport,
       'rfcomm'->RFCOMMTransport from DeviceStore); auto-detects platform if no arg
       (MACOS->SerialTransport, RASPBERRY_PI_*->RFCOMMTransport); raises TransportError
       for unsupported platform.

  2. src/gtach/comm/rfcomm.py
     - RFCOMMTransport(OBDTransport): __init__(mac_address, channel=1, retry_delay=5.0)
     - connect(): socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM), settimeout(10),
       connect((mac,channel)), settimeout(None), return True; OSError->False
     - send_command(): encode cmd+'\r', sendall, recv loop until '>' in buf,
       settimeout(timeout); socket.timeout->None; OSError/empty->DISCONNECTED,None
     - GUARD: AF_BLUETOOTH may not exist on macOS — guard import with try/except

  3. src/gtach/comm/tcp_transport.py
     - TCPTransport(OBDTransport): __init__(host='localhost', port=35000, retry_delay=5.0)
     - connect(): socket(AF_INET, SOCK_STREAM); identical send_command pattern to RFCOMM

  4. src/gtach/comm/serial_transport.py
     - SerialTransport(OBDTransport): __init__(port=None, baudrate=38400, retry_delay=5.0)
     - _discover_port(): serial.tools.list_ports, match 'ELM'/'OBD'/'OBDII' case-insensitive
     - connect(): resolve port or discover; serial.Serial(port,baudrate,timeout=2)
     - send_command(): write cmd+'\r', read_until(b'>'), SerialException->DISCONNECTED,None

  CONSTRAINTS:
  - All files: MIT license header, type annotations, logging.getLogger('<ClassName>')
  - threading.RLock guards _state + socket/serial handle in all transports
  - send_command returns None (never raises) on timeout or disconnection
  - RFCOMMTransport instantiation must succeed on macOS (guard AF_BLUETOOTH)
  - SerialTransport(port=None) must instantiate without error

  DELIVERABLES: Write files directly to disk via MCP filesystem tools.
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-24 | William Watson | Initial prompt |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
