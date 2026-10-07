Created: 2026 October 07

# Prompt: Callbacks Outside Locks and an Asynchronous Continue Probe

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-fbe7e98a"
  task_type: "debug"
  source_ref: "change-fbe7e98a"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-fbe7e98a"
    change_iteration: 1

context:
  purpose: >
    Remove UI stalls caused by callbacks running under locks and by a
    blocking RFCOMM probe on the touch thread, and stop setup completion
    handlers from acting on progress updates.
  integration: >
    async_operations.py, input/touch_coordinator.py, touch_interface.py,
    setup_components/bluetooth/interface.py, setup.py, one test module.
    Implement after prompt-e9216e17.
  knowledge_references:
    - "ai/workspace/issues/issue-fbe7e98a-callbacks-under-lock-ui-stalls.md"
    - "ai/workspace/change/change-fbe7e98a-callbacks-under-lock-ui-stalls.md"
    - "CLAUDE.md §4 rule 8"
  constraints:
    - "CRITICAL: no callback may be invoked while _operations_lock (AsyncOperationManager), _lock (TouchCoordinator) or _lock (touch interface) is held."
    - "Do not modify handle_touch_up, handle_touch_move, handle_gesture or slider handling in TouchCoordinator."
    - "Do not change verify_obd_connection, the pairing flow, or what any callback does, apart from EDIT B's early return."
    - "handle_touch_down's return values must be unchanged for every input."
    - "No RFCOMM or other blocking I/O may run on the touch thread in the 'current_continue' path."
    - "Do not modify src/gtach/display/manager_backup.py or setup_original_backup.py."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to E from the change document and add tests/test_callbacks_outside_locks.py."
  requirements:
    functional:
      - "Async operation callbacks run without _operations_lock held, for progress and completion."
      - "Completion handlers in interface.py return immediately for PENDING or RUNNING."
      - "Button callbacks from handle_touch_down run without the coordinator lock held."
      - "Touch-interface callbacks run without the interface lock held."
      - "'current_continue' submits one asynchronous probe and returns None; the outcome is applied by the completion handler."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Capture under lock, invoke after release (CLAUDE.md rule 8)."
  components:
    - name: "EDIT A — AsyncOperationManager"
      type: "class"
      purpose: "Callbacks outside _operations_lock."
      logic:
        - "In _worker_loop's 'Notify progress callback' block: `with self._operations_lock: operation = self.operations.get(operation_id); callback = self.progress_callbacks.get(operation_id)`; then, outside the lock, `if operation and callback:` call it inside the existing try/except."
        - "Apply the same pattern in _update_operation_progress's notify block."
    - name: "EDIT B — completion handler guards"
      type: "function"
      purpose: "Act only on terminal status (D12)."
      logic:
        - "First statement inside the try of on_bluetooth_init_complete, on_discovery_complete and on_pairing_complete: `if operation.status in (OperationStatus.PENDING, OperationStatus.RUNNING): return`."
    - name: "EDIT C — TouchCoordinator.handle_touch_down"
      type: "function"
      purpose: "Button callback after lock release."
      logic:
        - "Introduce `deferred = None` before `with self._lock:`."
        - "Change _handle_button_touch_down to return `(region.action_type, callback_or_None)` without invoking the callback; on error return `(TouchAction.NONE, None)`."
        - "In handle_touch_down, for the button branch, unpack into (action, deferred) and keep the action as the return value. Restructure so the method leaves the with-block before returning (e.g. compute `result` inside, return after)."
        - "After the with-block: `if deferred is not None:` call `deferred(pos)` in try/except with the existing 'Button callback error' log (exc_info=True)."
        - "Statistics updates and touch-state updates stay under the lock in their current order."
    - name: "EDIT D — _emit_touch_event"
      type: "function"
      purpose: "Callback after lock release."
      logic:
        - "`with self._lock: callback = self._callback`; then if callback, call it in the existing try/except; else the existing debug message."
    - name: "EDIT E — asynchronous Continue probe"
      type: "function"
      purpose: "No RFCOMM on the touch thread."
      logic:
        - "Add BluetoothSetupInterface.start_device_probe(self, on_result: Callable[[bool], None]) -> None with a Google-style docstring."
        - "Task: `import socket as _socket`; if self._pairing_factory is not None or not hasattr(_socket, 'AF_BLUETOOTH'): return True. Else device = self.device_store.get_primary_device(); return False if None; transport = RFCOMMTransport(device.mac_address, channel=1); ok = transport.connect(); if ok: transport.disconnect(); return ok."
        - "Completion handler: ignore PENDING/RUNNING; on COMPLETED call on_result(bool(operation.result)); otherwise on_result(False). Wrap on_result in try/except with logger.error(..., exc_info=True)."
        - "Submit with OperationType.OBD_CONNECTION_TEST and progress_callback=<handler>. On submission failure call on_result(False)."
        - "In SetupDisplayManager.__init__ add `self._probe_in_flight = False`."
        - "Replace the body of the 'current_continue' branch: if self._probe_in_flight: return None. Set it True. Define _on_probe_result(ok): clear the flag; if ok: self.state_coordinator.complete_setup(); else: log the existing warning (without the MAC if no device), self.state_coordinator.update_state(error_message='Device not available'), self.state_coordinator.transition_to_screen(SetupScreen.WELCOME). Call self.bluetooth_interface.start_device_probe(_on_probe_result); return None."
        - "Remove the now-unused DeviceStore and RFCOMMTransport imports from that branch only."

data_schema:
  entities: []

error_handling:
  strategy: "Existing try/except blocks retained; new code logs with exc_info=True."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "AsyncOperationManager(max_workers=1) started; task calls progress_callback(0.5); registered callback records `mgr._operations_lock.acquire(blocking=False)` (releasing if acquired) for each invocation; wait for completion; stop manager."
      expected: "At least two invocations (progress and completion), all True."
    - scenario: "Callback that calls mgr.get_operation_status(operation.id)."
      expected: "Completes within 5 s."
    - scenario: "Call each of the three interface completion handlers (obtained by submitting with a stub async manager that captures progress_callback) with a stub operation of status RUNNING."
      expected: "No change to state.pairing_status, interface.pairing, _pairing_ready or _active_operations."
    - scenario: "TouchCoordinator with a button region whose callback starts a helper thread that does `coordinator._lock.acquire(timeout=1)` and records the result, then joins it."
      expected: "Recorded True; handle_touch_down returned the region's action type."
    - scenario: "Touch interface with a callback recording `iface._lock.acquire(blocking=False)`; call _emit_touch_event."
      expected: "True."
    - scenario: "start_device_probe with pairing_factory set, using a synchronous stub async manager."
      expected: "on_result(True); RFCOMMTransport never constructed (patched to raise if called)."
    - scenario: "start_device_probe with pairing_factory None, socket.AF_BLUETOOTH present (patch if absent), a primary device in a stub store, RFCOMMTransport.connect patched to False."
      expected: "on_result(False)."
    - scenario: "SetupDisplayManager 'current_continue' twice with a stub bluetooth_interface that records calls and never completes."
      expected: "start_device_probe called once; both calls return None."
  edge_cases:
    - "A button callback that registers new regions on the coordinator (as DisplayManager does) must not deadlock."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit existing files in place; add one test module."
  files:
    - path: "src/gtach/display/async_operations.py"
      content: "EDIT A"
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "EDITS B and E"
    - path: "src/gtach/display/input/touch_coordinator.py"
      content: "EDIT C"
    - path: "src/gtach/display/touch_interface.py"
      content: "EDIT D"
    - path: "src/gtach/display/setup.py"
      content: "EDIT E caller"
    - path: "tests/test_callbacks_outside_locks.py"
      content: "testing.unit_tests"

success_criteria:
  - "No progress_callbacks[...](...) call lies inside `with self._operations_lock:` in async_operations.py."
  - "Each of the three completion handlers returns early on PENDING or RUNNING."
  - "_handle_button_touch_down contains no callback invocation; handle_touch_down invokes the deferred callback after its with-block."
  - "_emit_touch_event invokes the callback after its with-block."
  - "The 'current_continue' branch contains no RFCOMMTransport reference."
  - "BluetoothSetupInterface.start_device_probe exists with the specified signature."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "async_operations"
        path: "src/gtach/display/async_operations.py"
      - name: "interface"
        path: "src/gtach/display/setup_components/bluetooth/interface.py"
      - name: "touch_coordinator"
        path: "src/gtach/display/input/touch_coordinator.py"
      - name: "touch_interface"
        path: "src/gtach/display/touch_interface.py"
    classes:
      - name: "AsyncOperationManager"
        module: "gtach.display.async_operations"
      - name: "BluetoothSetupInterface"
        module: "gtach.display.setup_components.bluetooth.interface"
      - name: "TouchCoordinator"
        module: "gtach.display.input.touch_coordinator"
    functions:
      - name: "start_device_probe"
        module: "gtach.display.setup_components.bluetooth.interface"
        signature: "(self, on_result: Callable[[bool], None]) -> None"
      - name: "handle_touch_down"
        module: "gtach.display.input.touch_coordinator"
        signature: "(self, pos: Tuple[int, int]) -> Optional[TouchAction]"
    constants: []

notes: >
  _emit_touch_event is defined on the abstract base TouchInterface
  (touch_interface.py:105) and inherited by HyperPixelTouchInterface and
  MockTouchInterface. On-target verification is a human
  step: DISCONNECTED → Setup, a full pairing, and CURRENT_DEVICE →
  Continue with the adapter powered off; the display must stay
  responsive throughout.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-fbe7e98a iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
