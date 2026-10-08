Created: 2026 October 07

# Change: Bounded Pairing, Coordinated Setup State, Complete Shutdown

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-d140121d"
  title: "Apply the socket timeout before connect; non-blocking pairing shutdown and correct chunk duration; get_state returns a copy and all setup-state writes go through the coordinator; lock the async-operations map; arm the exit backstop on every shutdown and stop touch, async and pairing threads"
  date: "2026-10-07"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-d140121d"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-d140121d"
  description: "Resolves issue-d140121d (audit-36b6ea95 A07, A08, A17, C14, D04, D05, X02)."

scope:
  summary: "Five edit groups in comm/ and display/, plus app.py."
  affected_components:
    - name: "BluetoothSocket"
      file_path: "src/gtach/comm/system_bluetooth.py"
      change_type: "modify"
    - name: "BluetoothPairing"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "SetupStateCoordinator"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
      change_type: "modify"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "DisplayManager.stop"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_medium_defects.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "DisplayManager view-state locking (audit C03): recorded as an accepted risk."
    - "PyBluez versus system backend selection."
    - "ThreadManager.shutdown internals."

rational:
  problem_statement: "See issue-d140121d."
  proposed_solution: >
    EDIT A (A07) — BluetoothSocket.connect: after creating self.sock, if
    self.timeout is not None call self.sock.settimeout(self.timeout)
    before connect.

    EDIT B (A08, A17) — BluetoothPairing.shutdown: set both cancel
    events, then self._executor.shutdown(wait=False, cancel_futures=True).
    __del__ unchanged (now non-blocking). In discovery, the chunk
    duration uses the effective `timeout // chunks` (at least 1) instead
    of self.discovery_timeout // chunks.

    EDIT C (D04) — SetupStateCoordinator.get_state returns
    dataclasses.replace(self.state, discovered_devices=list(self.state.discovered_devices))
    under the lock. Add add_discovered_device(device) -> bool: under the
    lock, append if not already present (by MAC) to a new list assigned
    to state.discovered_devices; notify 'discovered_devices' after
    release; return whether it was added.

    EDIT D (D04, D05) — BluetoothSetupInterface:
    (1) Add private helpers _set_state(state, **fields) (coordinator
    present → update_state(**fields); else setattr on the passed object)
    and _add_device(state, device) (coordinator → add_discovered_device;
    else append). Replace every `state.<field> = …` and
    `state.discovered_devices.append(…)` in the module with these.
    (2) Add self._ops_lock = threading.Lock(); every read or write of
    _active_operations is under it (copy values out before calling
    async_manager). Add has_active_operation(name: str) -> bool.
    setup.py uses has_active_operation('device_discovery') instead of
    reading _active_operations.
    (3) Add shutdown(): cancel_operations(); if self.pairing has
    shutdown(), call it (try/except, logged).

    EDIT E (X02, C14) — shutdown completeness.
    (1) app.py: factor the backstop timer from _watchdog_shutdown into
    _arm_exit_backstop() (idempotent via a flag); call it first in
    shutdown() and in _watchdog_shutdown.
    (2) app.shutdown: after stop_setup and before display.stop, call
    gtach.display.async_operations.shutdown_async_manager() (try/except,
    logged).
    (3) SetupDisplayManager.stop_setup calls
    self.bluetooth_interface.shutdown() instead of cancel_operations().
    (4) DisplayManager.stop: after the display thread join, call
    self.touch_handler.stop() if a touch handler exists (try/except,
    logged).
  alternatives_considered:
    - option: "Make SetupState immutable."
      reason_rejected: "Larger change; copies on read and coordinated writes are sufficient."
  benefits:
    - "Pairing connects bounded by the configured timeout."
    - "Consistent setup state across threads; renders see stable lists."
    - "Shutdown always bounded by the 20 s backstop; fewer stray threads."
  risks:
    - risk: "A write path in interface.py is missed and silently lost after get_state returns copies."
      mitigation: "Success criterion: no `state.<attr> =` assignment and no `.discovered_devices.append` remain in interface.py outside the fallback helper."
    - risk: "update_state notifications per discovery progress tick invalidate the render cache often."
      mitigation: "Discovery screens are not cached; invalidation is a dictionary operation."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits."
  code_changes:
    - component: "comm"
      file: "src/gtach/comm/system_bluetooth.py, src/gtach/comm/pairing.py"
      change_summary: "EDITS A, B"
      functions_affected:
        - "BluetoothSocket.connect"
        - "BluetoothPairing.shutdown"
        - "BluetoothPairing discovery chunking"
      classes_affected: []
    - component: "display"
      file: "coordinator.py, interface.py, setup.py, manager.py"
      change_summary: "EDITS C, D, E(3), E(4)"
      functions_affected:
        - "SetupStateCoordinator.get_state"
        - "SetupStateCoordinator.add_discovered_device (new)"
        - "BluetoothSetupInterface._set_state (new)"
        - "BluetoothSetupInterface._add_device (new)"
        - "BluetoothSetupInterface.has_active_operation (new)"
        - "BluetoothSetupInterface.shutdown (new)"
        - "SetupDisplayManager.stop_setup"
        - "DisplayManager.stop"
      classes_affected: []
    - component: "app"
      file: "src/gtach/app.py"
      change_summary: "EDIT E(1), E(2)"
      functions_affected:
        - "GTachApplication.shutdown"
        - "GTachApplication._watchdog_shutdown"
        - "GTachApplication._arm_exit_backstop (new)"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "SetupStateCoordinator.get_state"
      change_type: "contract"
      details: "Returns a copy; callers must write through the coordinator."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-52653cd6"
      relationship: "precedes in the run order (independent)."

testing_requirements:
  test_approach: "Unit tests with stubs."
  test_cases:
    - scenario: "BluetoothSocket with settimeout(3) before connect; socket.socket patched to a recorder."
      expected_result: "settimeout(3) called on the new socket before connect."
    - scenario: "BluetoothPairing.shutdown with a stub executor."
      expected_result: "shutdown(wait=False, cancel_futures=True); cancel events set."
    - scenario: "get_state twice; mutate the first copy's discovered_devices."
      expected_result: "Coordinator state unchanged; distinct list objects."
    - scenario: "add_discovered_device twice with the same MAC."
      expected_result: "True then False; one entry; one notification."
    - scenario: "Interface with a coordinator: run the discovery and pairing completion handlers with stub operations."
      expected_result: "Coordinator state reflects the writes; the passed state object is not relied on."
    - scenario: "Interface without a coordinator."
      expected_result: "Writes land on the passed state object (fallback)."
    - scenario: "has_active_operation from two threads while another thread adds and removes entries 1,000 times."
      expected_result: "No exception."
    - scenario: "app.shutdown via object.__new__ with stubs."
      expected_result: "_arm_exit_backstop called first; shutdown_async_manager called; order setup → async → display → transport → obd → thread manager."
    - scenario: "DisplayManager.stop with a stub touch handler."
      expected_result: "touch_handler.stop called once."
  regression_scope:
    - "tests/test_callbacks_outside_locks.py, tests/test_setup_lock_order.py, tests/test_device_list_focus.py, tests/test_setup_and_gauge.py, tests/test_watchdog_process_termination.py."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to E and tests."
      owner: "tactical"
    - step: "On the Pi: full pairing; stop during discovery."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session B (2026-10-07): systemctl stop during discovery 0.41 s."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-fbe7e98a"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-d140121d"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-d140121d iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in 69eb605f2b086d666248bb39a4046032f9eb94d8."
  - version: "1.3"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Verified on device; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial change document. A07, A08, A17, C14, D04, D05, X02. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in 69eb605f2b086d666248bb39a4046032f9eb94d8. |
| 1.3 | 2026-10-08 | Verified on device; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
