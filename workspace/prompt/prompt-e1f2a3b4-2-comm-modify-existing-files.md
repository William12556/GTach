# Prompt: Comm Transport Abstraction — Modify Existing Comm Files

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
  sequence: "2 of 3"
  coupled_docs:
    change_ref: "change-e1f2a3b4"
    change_iteration: 1

  prerequisite: "prompt-e1f2a3b4-1 must be complete — transport.py, rfcomm.py, tcp_transport.py, serial_transport.py must exist"

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
  max_iterations: 20 — orchestrator uses this for both outer loop and inner phase.
```

---

## 2.0 Context

```yaml
context:
  purpose: >
    Modify four existing comm domain files to align with the new OBDTransport
    abstraction. Replace BluetoothManager dependency in OBDProtocol with
    OBDTransport. Rationalise BluetoothDevice fields. Fix cross-domain import
    in DeviceStore. Update comm package __init__.py exports.

  integration: >
    Prompt 1 of 3 created the new transport files. This prompt updates
    existing files to consume them. Prompt 3 of 3 will update app.py,
    main.py, pyproject.toml, and watchdog.py.

  project_root: "/Users/williamwatson/Documents/GitHub/GTach"
  source_root: "src/gtach/comm/"
  entry_point: "gtach.main:main (pyproject.toml [project.scripts])"
```

---

## 3.0 Specification

```yaml
specification:
  description: >
    Modify four existing files:
      1. src/gtach/comm/obd.py        — replace BluetoothManager with OBDTransport
      2. src/gtach/comm/models.py     — rationalise BluetoothDevice fields
      3. src/gtach/comm/device_store.py — fix cross-domain import; trim interface
      4. src/gtach/comm/__init__.py   — update exports

  requirements:
    functional:

      - id: "obd.py"
        changes:
          - "Remove: from .bluetooth import BluetoothManager"
          - "Add: from .transport import OBDTransport"
          - "OBDProtocol.__init__ signature: (self, transport: OBDTransport, thread_manager: ThreadManager)"
          - "Store transport as self.transport (not self.bluetooth)"
          - "_protocol_loop: replace self.bluetooth.is_connected() with self.transport.is_connected()"
          - "_send_command: replace self.bluetooth.send_command(command_str, timeout=self.timeout) with self.transport.send_command(command_str, timeout=self.timeout)"
          - "OBDResponse dataclass: unchanged"
          - "All other logic unchanged"

      - id: "models.py"
        changes:
          - "BluetoothDevice retains: name (str), mac_address (str), device_type (str, default 'UNKNOWN'), last_connected (Optional[datetime], default None)"
          - "Remove fields: address, connection_count, signal_strength, metadata"
          - "Fix mac_address normalisation in __post_init__: preserve colons, uppercase only — 'AA:BB:CC:DD:EE:FF' format (NOT stripping colons as current code does)"
          - "Auto-detect device_type from name if UNKNOWN: 'ELM' in name.upper() -> 'ELM327'; 'OBD' in name.upper() -> 'OBD'"
          - "to_dict(): serialise name, mac_address, device_type, last_connected (ISO string if not None)"
          - "from_dict(cls, data): deserialise same fields; parse last_connected ISO string to datetime"
          - "Retain __post_init__, to_dict, from_dict; remove to_json/from_json if present"

      - id: "device_store.py"
        changes:
          - "Fix import: replace 'from ..display.setup_models import BluetoothDevice' with 'from .models import BluetoothDevice'"
          - "Rename save_paired_device() -> save_device(); same body logic"
          - "Remove methods not in approved interface: set_primary_device(), is_setup_complete(), mark_setup_complete(), is_first_run(), get_discovery_timeout(), set_discovery_timeout(), clear_all_devices()"
          - "Implement atomic _save_config(): write to temp file (config_path + '.tmp'), then os.replace(tmp, config_path)"
          - "Remove 'setup' block from default config dict and from YAML structure"
          - "Retain: __init__, _ensure_config_dir, _load_config, _save_config, save_device, get_primary_device, get_all_devices, remove_device, get_device_by_mac"
          - "get_primary_device(): construct BluetoothDevice using keyword args matching new field names (name, mac_address, device_type, last_connected)"

      - id: "__init__.py"
        changes:
          - "Remove: from .bluetooth import BluetoothManager, BluetoothState"
          - "Remove stale inline comment '# Add this line'"
          - "Add exports: OBDTransport, TransportState, TransportError, RFCOMMTransport, TCPTransport, SerialTransport, select_transport"
          - "Retain: OBDProtocol, OBDResponse, BluetoothDevice"
          - "Update __all__ to match"
```

---

## 4.0 Design

### 4.1 obd.py — key diff

```python
# REMOVE:
from .bluetooth import BluetoothManager

# ADD:
from .transport import OBDTransport

# CHANGE __init__ signature:
def __init__(self, transport: OBDTransport, thread_manager: ThreadManager):
    self.transport = transport   # was: self.bluetooth = bluetooth_manager
    ...

# CHANGE in _protocol_loop:
if not self.transport.is_connected():   # was: self.bluetooth.is_connected()

# CHANGE in _send_command:
response = self.transport.send_command(command_str, timeout=self.timeout)
# was: self.bluetooth.send_command(command_str, timeout=self.timeout)
```

### 4.2 models.py — BluetoothDevice

```python
@dataclass
class BluetoothDevice:
    name: str
    mac_address: str
    device_type: str = "UNKNOWN"
    last_connected: Optional[datetime.datetime] = None

    def __post_init__(self):
        # Normalise mac_address: uppercase, preserve colons
        self.mac_address = self.mac_address.upper()
        # Auto-detect device_type
        if self.device_type == "UNKNOWN":
            if "ELM" in self.name.upper():
                self.device_type = "ELM327"
            elif "OBD" in self.name.upper():
                self.device_type = "OBD"
        # Parse string timestamp
        if isinstance(self.last_connected, str):
            try:
                self.last_connected = datetime.datetime.fromisoformat(self.last_connected)
            except (ValueError, TypeError):
                self.last_connected = None
```

### 4.3 device_store.py — _save_config atomic write

```python
def _save_config(self) -> None:
    if not YAML_AVAILABLE:
        self.logger.debug("YAML not available — config not persisted")
        return
    tmp = self.config_path + '.tmp'
    try:
        with open(tmp, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        os.replace(tmp, self.config_path)
    except Exception as e:
        self.logger.error(f"Failed to save config: {e}")
```

### 4.4 __init__.py

```python
from .transport import OBDTransport, TransportState, TransportError, select_transport
from .rfcomm import RFCOMMTransport
from .tcp_transport import TCPTransport
from .serial_transport import SerialTransport
from .obd import OBDProtocol, OBDResponse
from .models import BluetoothDevice

__all__ = [
    'OBDTransport', 'TransportState', 'TransportError', 'select_transport',
    'RFCOMMTransport', 'TCPTransport', 'SerialTransport',
    'OBDProtocol', 'OBDResponse',
    'BluetoothDevice',
]
```

---

## 5.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Modify files in place using MCP filesystem tools"
    - "Do not create new files — only modify the four listed files"

  files:
    - path: "src/gtach/comm/obd.py"
      action: "modify"
    - path: "src/gtach/comm/models.py"
      action: "modify"
    - path: "src/gtach/comm/device_store.py"
      action: "modify"
    - path: "src/gtach/comm/__init__.py"
      action: "modify"
```

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "obd.py: no import of BluetoothManager; OBDProtocol.__init__ accepts OBDTransport as first arg"
  - "obd.py: self.transport used throughout; self.bluetooth absent"
  - "models.py: BluetoothDevice has exactly 4 fields: name, mac_address, device_type, last_connected"
  - "models.py: mac_address normalisation preserves colons (uppercase only)"
  - "device_store.py: import of BluetoothDevice from .models (not from display)"
  - "device_store.py: save_device() exists; save_paired_device() absent"
  - "device_store.py: is_setup_complete(), mark_setup_complete(), is_first_run() absent"
  - "device_store.py: _save_config uses atomic os.replace pattern"
  - "__init__.py: OBDTransport, TransportState, select_transport exported; BluetoothManager absent"
  - "__init__.py: no stale inline comments"
  - "No import errors when running: python -c 'from gtach.comm import OBDTransport, OBDProtocol, BluetoothDevice'"
```

---

## 7.0 Element Registry

```yaml
element_registry:
  modules:
    - name: "gtach.comm.obd"
      path: "src/gtach/comm/obd.py"
    - name: "gtach.comm.models"
      path: "src/gtach/comm/models.py"
    - name: "gtach.comm.device_store"
      path: "src/gtach/comm/device_store.py"
    - name: "gtach.comm"
      path: "src/gtach/comm/__init__.py"

  classes:
    - name: "OBDResponse"
      module: "gtach.comm.obd"
      base_classes: []
    - name: "OBDProtocol"
      module: "gtach.comm.obd"
      base_classes: []
    - name: "BluetoothDevice"
      module: "gtach.comm.models"
      base_classes: []
    - name: "DeviceStore"
      module: "gtach.comm.device_store"
      base_classes: []

  functions:
    - name: "__init__"
      module: "gtach.comm.obd"
      signature: "__init__(self, transport: OBDTransport, thread_manager: ThreadManager) -> None"
    - name: "save_device"
      module: "gtach.comm.device_store"
      signature: "save_device(self, device: BluetoothDevice, is_primary: bool = True) -> None"
    - name: "get_primary_device"
      module: "gtach.comm.device_store"
      signature: "get_primary_device(self) -> Optional[BluetoothDevice]"
```

---

## 8.0 Tactical Brief

```
TASK: Modify 4 existing files in src/gtach/comm/. Do NOT create new files.
Prerequisite: transport.py, rfcomm.py, tcp_transport.py, serial_transport.py must exist.

FILE 1: src/gtach/comm/obd.py
- Remove: from .bluetooth import BluetoothManager
- Add: from .transport import OBDTransport
- OBDProtocol.__init__(self, transport: OBDTransport, thread_manager)
- Replace all self.bluetooth.* with self.transport.*
- OBDResponse dataclass and all other logic unchanged

FILE 2: src/gtach/comm/models.py
- BluetoothDevice keeps only: name(str), mac_address(str), device_type(str='UNKNOWN'), last_connected(Optional[datetime]=None)
- Remove: address, connection_count, signal_strength, metadata fields
- __post_init__: uppercase mac_address PRESERVING colons (not stripping them)
- to_dict/from_dict: serialise/deserialise these 4 fields only

FILE 3: src/gtach/comm/device_store.py
- Fix import: from .models import BluetoothDevice  (was from ..display.setup_models)
- Rename save_paired_device() -> save_device()
- Remove: set_primary_device, is_setup_complete, mark_setup_complete,
  is_first_run, get_discovery_timeout, set_discovery_timeout, clear_all_devices
- _save_config(): write to config_path+'.tmp' then os.replace(tmp, config_path)
- Remove 'setup' block from default config structure
- get_primary_device(): use new BluetoothDevice field names (mac_address not address)

FILE 4: src/gtach/comm/__init__.py
- Remove: from .bluetooth import BluetoothManager, BluetoothState; remove stale comments
- Add imports: OBDTransport, TransportState, TransportError, select_transport,
  RFCOMMTransport, TCPTransport, SerialTransport
- __all__: BluetoothManager absent; all new transport names present

SUCCESS: python -c 'from gtach.comm import OBDTransport, OBDProtocol, BluetoothDevice' imports cleanly.
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-24 | William Watson | Initial prompt |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
