Created: 2026 October 07

# Prompt: Bounded Pairing, Coordinated Setup State, Complete Shutdown

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-d140121d"
  task_type: "debug"
  source_ref: "change-d140121d"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-d140121d"
    change_iteration: 1

context:
  purpose: "Resolve the remaining medium findings A07, A08, D04, D05, X02 with A17 and C14."
  integration: "comm/system_bluetooth.py, comm/pairing.py, display/setup_components/state/coordinator.py, display/setup_components/bluetooth/interface.py, display/setup.py, display/manager.py, app.py; one test module."
  knowledge_references:
    - "ai/workspace/issues/issue-d140121d-remaining-medium-defects.md"
    - "ai/workspace/change/change-d140121d-remaining-medium-defects.md"
    - "CLAUDE.md §4 rule 8"
  constraints:
    - "CRITICAL: after get_state returns copies, no write to setup state may go through a state object except in the no-coordinator fallback helper. Search interface.py for every `state.` assignment and every `.discovered_devices.append` before finishing."
    - "No call-outs under a lock (CLAUDE.md rule 8): notifications after release; async_manager calls outside _ops_lock."
    - "Shutdown order otherwise unchanged; the backstop is armed exactly once per process."
    - "Do not change ThreadManager, WatchdogMonitor or transports."
    - "Every logger .error/.critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to E of change-d140121d and add tests/test_medium_defects.py."
  requirements:
    functional:
      - "As in change-d140121d proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance:
    - target: "Shutdown bounded by the 20 s backstop on every exit path"
      metric: "time"

design:
  architecture: "Coordinator owns setup state; readers get copies; one bounded shutdown."
  components:
    - name: "EDITS A to E"
      type: "module"
      purpose: "As in change-d140121d."
      logic:
        - "EDIT C: import dataclasses.replace; add_discovered_device compares mac_address."
        - "EDIT D(1): helpers are methods on BluetoothSetupInterface; they take the `state` argument the handlers already receive."
        - "EDIT D(2): get_active_operation_progress copies the dict under _ops_lock before querying async_manager."
        - "EDIT E(1): `self._backstop_armed = False` set in __init__; _arm_exit_backstop returns early if True."

data_schema:
  entities: []

error_handling:
  strategy: "New shutdown calls wrapped and logged; never raise out of shutdown."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-d140121d testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "shutdown called twice: backstop armed once."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit in place; add one test module."
  files:
    - path: "src/gtach/comm/system_bluetooth.py, src/gtach/comm/pairing.py"
      content: "EDITS A, B"
    - path: "src/gtach/display/setup_components/state/coordinator.py, src/gtach/display/setup_components/bluetooth/interface.py, src/gtach/display/setup.py"
      content: "EDITS C, D, E(3)"
    - path: "src/gtach/display/manager.py"
      content: "EDIT E(4)"
    - path: "src/gtach/app.py"
      content: "EDIT E(1), E(2)"
    - path: "tests/test_medium_defects.py"
      content: "Tests"

success_criteria:
  - "BluetoothSocket.connect applies self.timeout before connect."
  - "BluetoothPairing.shutdown uses wait=False and cancel_futures=True."
  - "get_state returns a copy; add_discovered_device exists."
  - "interface.py contains no `state.<attr> =` assignment and no `.discovered_devices.append` outside _set_state/_add_device."
  - "_active_operations is accessed only under _ops_lock; setup.py uses has_active_operation."
  - "app.shutdown arms the backstop first and calls shutdown_async_manager; DisplayManager.stop stops the touch handler."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "add_discovered_device"
        module: "gtach.display.setup_components.state.coordinator"
        signature: "(self, device: BluetoothDevice) -> bool"
      - name: "has_active_operation"
        module: "gtach.display.setup_components.bluetooth.interface"
        signature: "(self, name: str) -> bool"
      - name: "_arm_exit_backstop"
        module: "gtach.app"
        signature: "(self) -> None"
    constants: []

notes: "Human verification on the Pi: a full pairing works; `time systemctl stop gtach` during discovery stays well under 30 s."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-d140121d iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
