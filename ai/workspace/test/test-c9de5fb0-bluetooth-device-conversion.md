Created: 2026 October 09

# Test: Single Bluetooth Device Conversion

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-c9de5fb0"
  title: "Verify BluetoothDevice.from_discovered replaces both setup-to-comm conversions"
  date: "2026-10-09"
  author: "William Watson"
  status: "planned"
  type: "unit"
  priority: "medium"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-c9de5fb0"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "DiscoveredDevice Protocol and BluetoothDevice.from_discovered (src/gtach/comm/models.py)"
  design_refs: []
  change_refs:
    - "change-c9de5fb0"
  requirement_refs:
    - "issue-c9de5fb0"

scope:
  description: >
    Verifies the single conversion from any object exposing name,
    mac_address and device_type into a comm BluetoothDevice, that both
    call sites use it, and that comm does not import display. Includes
    one on-device pairing-persistence check.
  test_objectives:
    - "Confirm a setup-model device converts with an upper-cased MAC and last_connected None."
    - "Confirm structural typing: any object with the three attributes converts."
    - "Confirm an UNKNOWN device_type with 'OBD' in the name is classified OBD."
    - "Confirm no hand-written CommBluetoothDevice( construction remains in src/gtach."
    - "Confirm comm/models.py does not import from display."
    - "Confirm a pairing persists across a service restart on the device."
  in_scope:
    - "src/gtach/comm/models.py"
    - "src/gtach/display/setup_components/bluetooth/interface.py — pairing-success path"
    - "src/gtach/comm/sim_bluetooth.py — SimBluetoothPairing.pair_device"
  out_scope:
    - "Dataclass field definitions — unchanged"
  dependencies:
    - "Development venv with pip install -e .[dev]"
    - "TC-006 only: root@gtach.local and a pairable ELM327 adapter"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development); Debian Linux on Raspberry Pi Zero 2W (TC-006)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest"
  test_data_location: "Inline objects"

test_cases:
  - case_id: "TC-001"
    description: "Setup model converts"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Call BluetoothDevice.from_discovered on a setup-model device with a lower-case MAC"
    inputs: []
    expected_outputs:
      - field: "mac_address"
        expected_value: "Upper-cased"
        validation: "Equality"
      - field: "last_connected"
        expected_value: "None"
        validation: "is None"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_bluetooth_device_conversion.py::test_from_setup_device"
      pass_fail_criteria: "Both fields as expected"
    defects: []

  - case_id: "TC-002"
    description: "Any object with the three attributes converts"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Call from_discovered on a SimpleNamespace(name, mac_address, device_type)"
    inputs: []
    expected_outputs:
      - field: "result"
        expected_value: "BluetoothDevice with matching fields"
        validation: "Field equality"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_bluetooth_device_conversion.py::test_from_any_object_with_the_three_attributes"
      pass_fail_criteria: "Conversion succeeds"
    defects: []

  - case_id: "TC-003"
    description: "UNKNOWN type with OBD in the name is classified OBD"
    category: "edge"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Convert an object with device_type 'UNKNOWN' and a name containing 'OBD'"
    inputs: []
    expected_outputs:
      - field: "device_type"
        expected_value: "OBD"
        validation: "Equality; set by __post_init__"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_bluetooth_device_conversion.py::test_unknown_type_is_classified_from_name"
      pass_fail_criteria: "Classified OBD"
    defects: []

  - case_id: "TC-004"
    description: "No hand-written conversion remains"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -rn 'CommBluetoothDevice(' src/gtach"
    inputs: []
    expected_outputs:
      - field: "matches"
        expected_value: "None"
        validation: "grep exit 1"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No match"
    defects: []

  - case_id: "TC-005"
    description: "comm does not depend on display"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -n 'display' src/gtach/comm/models.py | grep -i import"
    inputs: []
    expected_outputs:
      - field: "matches"
        expected_value: "None"
        validation: "grep exit 1"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No display import"
    defects: []

  - case_id: "TC-006"
    description: "On-device: pairing persists across restart"
    category: "positive"
    preconditions:
      - "Branch deployed to root@gtach.local"
    test_steps:
      - step: "1"
        action: "Pair a device in setup"
      - step: "2"
        action: "Confirm the devices file under GTACH_HOME contains it"
      - step: "3"
        action: "systemctl restart gtach"
    inputs: []
    expected_outputs:
      - field: "devices file"
        expected_value: "Paired device present with upper-case MAC"
        validation: "Inspection"
      - field: "after restart"
        expected_value: "Reconnects without re-pairing"
        validation: "Observation and debug.log"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Saved and reconnected"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-c9de5fb0"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]
  code_coverage:
    target: "from_discovered; both call sites"
    achieved: ""
  untested_areas:
    - component: "The two call sites (interface.py pairing-success path, SimBluetoothPairing.pair_device)"
      reason: "No pytest case exercises them directly; TC-004 is static and TC-006 covers the real path on device only. A unit case for SimBluetoothPairing.pair_device is a candidate addition, pending agreement"

test_execution_summary:
  total_cases: 6
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""
  execution_time: ""
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""

traceability:
  requirements:
    - requirement_ref: "issue-c9de5fb0"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004"]
  designs: []
  changes:
    - change_ref: "change-c9de5fb0"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]

notes: >
  Generated pytest file: tests/test_bluetooth_device_conversion.py, per
  P06 §1.7.3. Written during implementation; recorded here
  retrospectively. Section 5.0 finding 6 of the batch report
  (last_connected annotated Optional[datetime] but accepting str) is in
  the same class and is out of scope here.
  Run: pytest tests/test_bluetooth_device_conversion.py -v.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-c9de5fb0."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t05_test"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial test document for change-c9de5fb0. |

---

Copyright (c) 2026 William Watson. MIT License.
