Created: 2026 October 09

# Prompt: Single Conversion to the Persisted Bluetooth Device Model

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-c9de5fb0"
  task_type: "refactor"
  source_ref: "change-c9de5fb0"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-c9de5fb0"
    change_iteration: 1

context:
  purpose: "Replace two hand-written setup→comm BluetoothDevice conversions with one classmethod."
  integration: "src/gtach/comm/models.py; display/setup_components/bluetooth/interface.py; comm/sim_bluetooth.py."
  knowledge_references:
    - "ai/workspace/issues/issue-c9de5fb0-duplicate-bluetooth-device-models.md"
    - "ai/workspace/change/change-c9de5fb0-duplicate-bluetooth-device-models.md"
  constraints:
    - "Do not merge or alter either dataclass's fields."
    - "comm/models.py must not import from gtach.display."
    - "Convert exactly name, mac_address, device_type; last_connected stays unset."
    - "Keep each call site's existing import alias and surrounding try/except."
    - "Python 3.9+ (typing.Protocol is available); PEP 8."

specification:
  description: "Add DiscoveredDevice Protocol and BluetoothDevice.from_discovered; use it at both sites."
  requirements:
    functional:
      - "Both call sites produce the same comm BluetoothDevice as before."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Professional docstrings"
  performance: []

design:
  architecture: "Structural typing (Protocol) to avoid a comm → display import."
  components:
    - name: "DiscoveredDevice"
      type: "class"
      purpose: "typing.Protocol with attributes name: str, mac_address: str, device_type: str."
    - name: "BluetoothDevice.from_discovered"
      type: "function"
      purpose: "Classmethod returning cls(name=device.name, mac_address=device.mac_address, device_type=device.device_type)."
      interface:
        inputs:
          - name: "device"
            type: "DiscoveredDevice"
            description: "A discovered device (setup model)."
        outputs:
          type: "BluetoothDevice"
          description: "The persisted comm model."
        raises: []
    - name: "Call sites"
      type: "function"
      purpose: "interface.py (~line 429) and sim_bluetooth.py SimBluetoothPairing.pair_device (~line 219): replace CommBluetoothDevice(name=..., mac_address=..., device_type=...) with CommBluetoothDevice.from_discovered(device)."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged at call sites."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "from_discovered(setup BluetoothDevice(name='ELM327 X', mac_address='aa:bb:cc:dd:ee:ff', signal_strength=-60, device_type='ELM327', last_seen=datetime.now()))."
      expected: "name 'ELM327 X'; mac_address 'AA:BB:CC:DD:EE:FF'; device_type 'ELM327'; last_connected None."
    - scenario: "from_discovered on a types.SimpleNamespace with the three attributes."
      expected: "Works (structural typing)."
  edge_cases:
    - "device_type 'UNKNOWN' with 'OBD' in the name: __post_init__ classification applies as before."
  validation:
    - "grep -rn 'CommBluetoothDevice(' src/gtach returns nothing."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/comm/models.py"
      content: "DiscoveredDevice; from_discovered"
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "Use from_discovered"
    - path: "src/gtach/comm/sim_bluetooth.py"
      content: "Use from_discovered"
    - path: "tests/test_bluetooth_device_conversion.py"
      content: "Unit tests"

success_criteria:
  - "grep -rn 'CommBluetoothDevice(' src/gtach returns nothing."
  - "grep -n 'gtach.display\\|from \\.\\.display' src/gtach/comm/models.py returns nothing."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "models"
        path: "src/gtach/comm/models.py"
    classes:
      - name: "BluetoothDevice"
        module: "gtach.comm.models"
      - name: "DiscoveredDevice"
        module: "gtach.comm.models"
    functions:
      - name: "from_discovered"
        module: "gtach.comm.models.BluetoothDevice"
        signature: "from_discovered(cls, device: DiscoveredDevice) -> BluetoothDevice"
    constants: []

notes: "Human verification on the Pi: pair a device in setup; it is saved and reconnects after a service restart."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-c9de5fb0 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
