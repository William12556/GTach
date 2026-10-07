Created: 2026 October 07

# Change: Callbacks Outside Locks and an Asynchronous Continue Probe

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-fbe7e98a"
  title: "Invoke callbacks after releasing the lock in AsyncOperationManager, TouchCoordinator.handle_touch_down and _emit_touch_event; ignore non-terminal status in setup completion handlers; run the CURRENT_DEVICE Continue probe as an async operation"
  date: "2026-10-07"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-fbe7e98a"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-fbe7e98a"
  description: "Resolves issue-fbe7e98a (audit-36b6ea95 D03, D06, C04, C02; D12)."

scope:
  summary: "Five edits, each narrowing a lock or moving blocking work off the touch thread."
  affected_components:
    - name: "AsyncOperationManager._worker_loop, _update_operation_progress"
      file_path: "src/gtach/display/async_operations.py"
      change_type: "modify"
    - name: "TouchCoordinator.handle_touch_down, _handle_button_touch_down"
      file_path: "src/gtach/display/input/touch_coordinator.py"
      change_type: "modify"
    - name: "TouchInterface._emit_touch_event"
      file_path: "src/gtach/display/touch_interface.py"
      change_type: "modify"
    - name: "BluetoothSetupInterface (completion handlers; new start_device_probe)"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "SetupDisplayManager._handle_touch_action ('current_continue')"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_callbacks_outside_locks.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "TouchCoordinator.handle_touch_up, handle_touch_move and gesture callbacks (unreachable; audit C12)."
    - "Unguarded _active_operations dict (audit D05) and operations-dict pruning."
    - "A visible 'checking' indication on CURRENT_DEVICE while the probe runs."
    - "verify_obd_connection logic."
    - "SetupDisplayManager lock edits (change-e9216e17)."

rational:
  problem_statement: "See issue-fbe7e98a."
  proposed_solution: >
    EDIT A — AsyncOperationManager. In _worker_loop and
    _update_operation_progress, read `operation` and
    `callback = self.progress_callbacks.get(operation_id)` under
    _operations_lock, then invoke `callback(operation)` after releasing
    it, inside the existing try/except. Behaviour is otherwise unchanged.

    EDIT B — completion handlers ignore progress (D12). In
    interface.py, on_bluetooth_init_complete, on_discovery_complete and
    on_pairing_complete begin with:
    `if operation.status in (OperationStatus.PENDING, OperationStatus.RUNNING): return`.

    EDIT C — TouchCoordinator.handle_touch_down. Under _lock, keep all
    existing state updates and hit-testing, but for a button region
    capture the callback instead of calling it. Invoke the captured
    callback after the lock is released, with the existing error
    logging. _handle_button_touch_down no longer invokes the callback;
    it returns the action type and the callback to its caller. The
    return value of handle_touch_down is unchanged.

    EDIT D — _emit_touch_event. Read `callback = self._callback` under
    _lock; invoke it after releasing the lock with the existing
    try/except and debug message for the no-callback case.

    EDIT E — Continue probe. Add
    BluetoothSetupInterface.start_device_probe(on_result: Callable[[bool], None]) -> None.
    It submits an OBD_CONNECTION_TEST operation whose task loads the
    primary device from DeviceStore and returns True if
    RFCOMMTransport(mac).connect() succeeds (disconnecting afterwards),
    False if there is no device or the connect fails. In simulation
    (self._pairing_factory is not None) or without AF_BLUETOOTH, it
    returns True without connecting, matching verify_obd_connection.
    The completion handler ignores non-terminal status and calls
    on_result(result) on COMPLETED, on_result(False) on FAILED or
    CANCELLED. In setup.py, 'current_continue' calls
    start_device_probe with a handler that, on True, calls
    state_coordinator.complete_setup(), and on False, calls
    update_state(error_message="Device not available") then
    transition_to_screen(SetupScreen.WELCOME). A boolean
    _probe_in_flight, set before submission and cleared in the handler,
    makes repeated taps no-ops. The action returns None.
  alternatives_considered:
    - option: "Separate progress and completion callback slots in AsyncOperationManager."
      reason_rejected: "Larger interface change; the guard in three handlers is sufficient."
    - option: "Run verify_obd_connection as its own async operation."
      reason_rejected: "Unnecessary once callbacks run outside the lock; verification already runs on a worker thread."
  benefits:
    - "No UI freeze during verification, re-entry or the Continue probe."
    - "Discovery and init no longer act on progress updates."
    - "Continue works in simulation."
  risks:
    - risk: "A callback runs after its operation was cancelled or cleaned up."
      mitigation: "Handlers already check operation.status; behaviour matches pre-change ordering."
    - risk: "The Continue tap gives no immediate visual feedback."
      mitigation: "Same as before (screen is cached); feedback is out of scope. Taps during the probe are ignored."

technical_details:
  current_behavior: "Callbacks under lock; synchronous probe on touch thread; handlers fire on progress."
  proposed_behavior: "Callbacks after release; probe on a worker; handlers act on terminal status only."
  implementation_approach: "Narrow with-blocks; add one method; guard three handlers."
  code_changes:
    - component: "AsyncOperationManager"
      file: "src/gtach/display/async_operations.py"
      change_summary: "EDIT A"
      functions_affected:
        - "_worker_loop"
        - "_update_operation_progress"
      classes_affected:
        - "AsyncOperationManager"
    - component: "BluetoothSetupInterface"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: "EDITS B and E"
      functions_affected:
        - "_init_bluetooth_pairing_async"
        - "start_discovery"
        - "start_pairing"
        - "start_device_probe"
      classes_affected:
        - "BluetoothSetupInterface"
    - component: "TouchCoordinator"
      file: "src/gtach/display/input/touch_coordinator.py"
      change_summary: "EDIT C"
      functions_affected:
        - "handle_touch_down"
        - "_handle_button_touch_down"
      classes_affected:
        - "TouchCoordinator"
    - component: "TouchInterface"
      file: "src/gtach/display/touch_interface.py"
      change_summary: "EDIT D"
      functions_affected:
        - "_emit_touch_event"
      classes_affected: []
    - component: "SetupDisplayManager"
      file: "src/gtach/display/setup.py"
      change_summary: "EDIT E caller"
      functions_affected:
        - "_handle_touch_action"
      classes_affected:
        - "SetupDisplayManager"
  data_changes: []
  interface_changes:
    - interface: "BluetoothSetupInterface.start_device_probe"
      change_type: "contract"
      details: "New method."
      backward_compatible: "yes"
    - interface: "TouchCoordinator._handle_button_touch_down"
      change_type: "signature"
      details: "Private; returns (TouchAction, Optional[Callable]) instead of invoking the callback."
      backward_compatible: "no"

dependencies:
  internal:
    - component: "DisplayManager button callbacks"
      impact: "Now invoked without the coordinator lock; the display thread no longer blocks on them."
  external: []
  required_changes:
    - change_ref: "change-e9216e17"
      relationship: "blocked_by. Introduces CLAUDE.md rule 8 and lock-safe coordinator notifications used by EDIT E's handler."

testing_requirements:
  test_approach: "Unit tests asserting lock state inside callbacks; functional tests of the probe and handler guards."
  test_cases:
    - scenario: "AsyncOperationManager: submit an operation whose callback records _operations_lock.acquire(blocking=False) for both a progress update and completion."
      expected_result: "All recorded values True."
    - scenario: "AsyncOperationManager: a callback that calls get_operation_status on its own operation."
      expected_result: "Returns without deadlock (bounded join)."
    - scenario: "on_discovery_complete invoked with an operation in RUNNING."
      expected_result: "No state change; _active_operations entry retained."
    - scenario: "TouchCoordinator: button region with a callback recording _lock acquisition from a second thread (non-blocking acquire in a helper thread)."
      expected_result: "The helper thread acquires the lock while the callback runs; handle_touch_down returns the region's action type."
    - scenario: "_emit_touch_event: callback records _lock.acquire(blocking=False)."
      expected_result: "True."
    - scenario: "start_device_probe in simulation (pairing_factory set)."
      expected_result: "on_result(True) called; no RFCOMMTransport constructed."
    - scenario: "start_device_probe with RFCOMMTransport.connect patched to return False and AF_BLUETOOTH present."
      expected_result: "on_result(False)."
    - scenario: "'current_continue' twice in quick succession."
      expected_result: "One probe submitted."
  regression_scope:
    - "tests/test_touch_dispatch.py, tests/test_disconnected_screen.py."
    - "Full tests/ suite."
  validation_criteria:
    - "No callback invocation lexically inside the relevant `with` blocks."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to E and tests."
      owner: "tactical"
    - step: "On the Pi: DISCONNECTED → Setup; pairing; CURRENT_DEVICE → Continue with adapter off."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-e9216e17"
      relationship: "blocked_by"
  related_issues:
    - issue_ref: "issue-fbe7e98a"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-fbe7e98a iteration 1."

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
| 1.0 | 2026-10-07 | Initial change document. Callbacks outside locks; completion-handler guard (D12); asynchronous Continue probe. |

---

Copyright (c) 2026 William Watson. MIT License.
