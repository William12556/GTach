Created: 2026 October 09

# Change: Single Conversion to the Persisted Bluetooth Device Model

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-c9de5fb0"
  title: "Add BluetoothDevice.from_discovered to comm/models.py and use it at both conversion sites"
  date: "2026-10-09"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c9de5fb0"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-c9de5fb0"
  description: "Resolves issue-c9de5fb0. Approach chosen 2026-10-09: one shared conversion; both models kept."

scope:
  summary: "One classmethod converts a discovered (setup) device into the persisted comm model; the two hand-written conversions call it."
  affected_components:
    - name: "comm BluetoothDevice"
      file_path: "src/gtach/comm/models.py"
      change_type: "modify"
    - name: "BluetoothSetupInterface (conversion site)"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "SimBluetoothPairing (conversion site)"
      file_path: "src/gtach/comm/sim_bluetooth.py"
      change_type: "modify"
    - name: "Conversion tests"
      file_path: "tests/test_bluetooth_device_conversion.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Merging the two dataclasses."
    - "DeviceStore, pairing.py and setup rendering."
    - "Which fields are converted: exactly name, mac_address and device_type, as today."

rational:
  problem_statement: >
    See issue-c9de5fb0. interface.py (~line 429) and sim_bluetooth.py
    (~line 219) each build a comm BluetoothDevice from a setup
    BluetoothDevice by hand, copying name, mac_address and device_type.
    The two copies can drift.
  proposed_solution: >
    In src/gtach/comm/models.py add a typing.Protocol DiscoveredDevice
    with attributes name: str, mac_address: str, device_type: str, and a
    classmethod BluetoothDevice.from_discovered(cls, device:
    DiscoveredDevice) -> BluetoothDevice returning cls(name=device.name,
    mac_address=device.mac_address, device_type=device.device_type).
    The Protocol keeps comm/models.py free of any import from
    gtach.display. Replace both hand-written constructions with
    CommBluetoothDevice.from_discovered(device), keeping each site's
    existing import alias and surrounding error handling.
  alternatives_considered:
    - option: "Merge the two models."
      reason_rejected: "Decided against on 2026-10-09; touches persistence and rendering."
    - option: "Import display.setup_models in comm/models.py for the type."
      reason_rejected: "Adds a comm → display dependency to the model module; a Protocol needs none."
  benefits:
    - "One conversion; a future field is added in one place."
  risks:
    - risk: "Behaviour drift at either site."
      mitigation: "The classmethod copies the same three fields; last_connected remains unset; __post_init__ normalisation unchanged."

technical_details:
  current_behavior: "Two identical hand-written conversions."
  proposed_behavior: "Both sites call BluetoothDevice.from_discovered."
  implementation_approach: "Add Protocol and classmethod; replace two call sites."
  code_changes:
    - component: "comm models"
      file: "src/gtach/comm/models.py"
      change_summary: "DiscoveredDevice Protocol; from_discovered classmethod."
      functions_affected:
        - "BluetoothDevice.from_discovered (new)"
      classes_affected:
        - "BluetoothDevice"
        - "DiscoveredDevice (new)"
    - component: "Bluetooth setup interface"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: "Use from_discovered."
      functions_affected: []
      classes_affected:
        - "BluetoothSetupInterface"
    - component: "Simulated pairing"
      file: "src/gtach/comm/sim_bluetooth.py"
      change_summary: "Use from_discovered."
      functions_affected:
        - "SimBluetoothPairing.pair_device"
      classes_affected:
        - "SimBluetoothPairing"
  data_changes: []
  interface_changes:
    - interface: "gtach.comm.models"
      change_type: "contract"
      details: "Adds DiscoveredDevice and BluetoothDevice.from_discovered."
      backward_compatible: "yes"

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests for the classmethod; existing setup and simulation tests for the call sites."
  test_cases:
    - scenario: "from_discovered on a setup BluetoothDevice(name='ELM327 X', mac_address='aa:bb:cc:dd:ee:ff', device_type='ELM327', ...)."
      expected_result: "comm BluetoothDevice with the same name, mac_address 'AA:BB:CC:DD:EE:FF', device_type 'ELM327', last_connected None."
    - scenario: "grep -rn 'CommBluetoothDevice(' src/gtach."
      expected_result: "No match."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "Add Protocol and classmethod; replace both sites; add tests."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Human verification: pair a device in setup on the Pi; it is saved and reconnects after restart."

verification:
  implemented_date: "2026-10-09"
  implemented_by: "Claude Code (commit 7c6574e)"
  verification_date: "2026-10-09"
  verified_by: "William Watson"
  test_results: "test-c9de5fb0 passed (6/6); pairing saved and survived a service restart on gtach.local."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-cd5ec050"
      relationship: "related. Removed the other parts of audit A14."
    - change_ref: "change-5fbff586"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-c9de5fb0"
      relationship: "resolves"

notes: "Line numbers are from ba661d4; locate code by symbol."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-c9de5fb0 iteration 1."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Implemented, verified by test-c9de5fb0, closed."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial change document resolving issue-c9de5fb0 iteration 1. |
| 1.1 | 2026-10-09 | Implemented, verified by test-c9de5fb0, closed. |

---

Copyright (c) 2026 William Watson. MIT License.
