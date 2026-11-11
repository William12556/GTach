# Prompt: Communication Layer Corrections

Created: 2026 November 11

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-b4f9607a"
  task_type: "debug"
  source_ref: "change-b4f9607a"
  target_profile: "claude_code"
  date: "2026-11-11"
  iteration: 1
  coupled_docs:
    change_ref: "change-b4f9607a"
    change_iteration: 1

context:
  purpose: "Run 2 of proposal-71ab3751: resolve the comm findings of audit-71ab3751 and provide the interfaces runs 3, 4 and 5 use."
  integration: "src/gtach/comm only, plus tests."
  knowledge_references:
    - "ai/workspace/issues/issue-b4f9607a-comm-layer-defects.md"
    - "ai/workspace/change/change-b4f9607a-comm-layer-defects.md"
    - "ai/workspace/audit/audit-71ab3751-src-gtach-static.md sections 3.0 and 6.0"
    - "CLAUDE.md section 4 (rule 8: no call-outs under a lock)"
  constraints:
    - "CRITICAL: edit no source file outside src/gtach/comm. Callers in app.py and display/ are changed by later runs; every interface change here is backward compatible."
    - "CRITICAL: EDIT A — the _shutdown test and the handle assignment happen under _lock; the close of a rejected handle happens after the lock is released."
    - "No call-outs under a lock: device_found_callback, status_callback and logging of subprocess output run outside any lock."
    - "DeviceStore._lock is not reentrant; the *_locked methods are called with it held."
    - "The transport reports faults and does not act on the host (change-5e7a03c4): no subprocess in transport code."
    - "Every logger .error or .critical in a broad handler passes exc_info=True; the A05 WARNING passes none."
    - "Monotonic clock for rate limiting and timeouts."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to J and the COMMENT RULE of change-b4f9607a; add tests/test_comm_layer_defects.py; correct tests/test_sim_transport.py."
  requirements:
    functional:
      - "As in change-b4f9607a proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"

design:
  architecture: "Unchanged. OBDTransport skeleton with four subclasses; BluetoothPairing for setup; one shared DeviceStore."
  components:
    - name: "EDITS A to J"
      type: "module"
      purpose: "As in change-b4f9607a."
      logic:
        - "EDIT A: read the symbols by name (connect, _open, _discard_handle, _discard_handle_locked, _shutdown); the rejected handle was never assigned to _handle, so close it with the subclass primitive the discard path uses."
        - "EDIT B: compare the classified cause with _CONNECT_FAULT_CAUSES[errno.ECONNREFUSED] before incrementing."
        - "EDIT D: keep the rate-limit state on the OBDProtocol instance; reset it on a successful initialisation."
        - "EDIT D: the registered stop function sets _adapter_initialised False and shutdown_event, exactly as stop() does, and does not join."
        - "EDIT E: compute the chunk wait from the same duration value that is passed to the back end."
        - "EDIT F: the fallback list is filled in the same loop that classifies devices; deduplicate by MAC as the main list does."
        - "EDIT H: copy.deepcopy(self.config), mutate the copy, call the save with the copy in place or restore on failure — choose the form that keeps _save_config's signature if tests patch it."
        - "EDIT I: set_device_store_path takes _shared_lock; it does not construct a store."

data_schema:
  entities: []

error_handling:
  strategy: "Link faults drop the link and record a cause; persistence faults return False; nothing new raises to callers."
  exceptions: []
  logging:
    level: "A05 at WARNING, rate-limited; A07 at WARNING; fallback at INFO"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-b4f9607a testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "disconnect() before connect() is called: connect returns False without leaving a handle."
    - "Fallback list empty and main list empty: empty result."
    - "set_device_store_path called while a shared instance exists: the next get_device_store() returns a new instance."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place; one new test module; one commit."
    - "Report: per EDIT, what changed; any deviation from the change document; test results."
  files:
    - path: "src/gtach/comm/transport.py, serial_transport.py, obd.py"
      content: "EDITS A to D"
    - path: "src/gtach/comm/pairing.py, system_bluetooth.py"
      content: "EDITS E, F, G"
    - path: "src/gtach/comm/device_store.py, sim_transport.py, models.py"
      content: "EDITS H, I, J"
    - path: "tests/test_comm_layer_defects.py, tests/test_sim_transport.py"
      content: "Tests"

success_criteria:
  - "connect() never leaves an open handle when _shutdown is set."
  - "OSError is in SerialTransport._IO_ERRORS."
  - "A missing 4100 reply produces no ERROR record and no traceback."
  - "stop_thread('obd_protocol', timeout=t) is bounded by t."
  - "discover_elm327_devices returns UNKNOWN-classified named devices only when no ELM327-like device was found and the scan was not cancelled."
  - "pair_device honours _cancel_pairing."
  - "save_device and remove_device return False, with memory unchanged, when the save fails."
  - "set_device_store_path exists and get_device_store() honours it."
  - "No type: ignore remains at BluetoothDevice.last_connected."
  - "git diff touches only src/gtach/comm and tests/."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "stop"
        module: "gtach.comm.obd"
        signature: "(self, timeout: float = 5.0) -> None"
      - name: "set_device_store_path"
        module: "gtach.comm.device_store"
        signature: "(path: Optional[str]) -> None"
      - name: "discover_elm327_devices"
        module: "gtach.comm.pairing"
        signature: "(self, timeout: Optional[int] = None, progress_callback: Optional[Callable[[float], None]] = None, device_found_callback: Optional[Callable[[BluetoothDevice], None]] = None, show_all_devices: bool = False) -> List[BluetoothDevice]"
    constants: []

notes: "Model: Claude Opus 5.5, effort medium, no ultracode. Human verification follows in device session A after run 3."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial prompt implementing change-b4f9607a iteration 1. Target profile claude_code. |
| 1.1 | 2026-11-11 | Executed by Claude Code. EDITS A to J and the COMMENT RULE applied; deviations are listed in report-b4f9607a. pytest and mypy pass. Closed and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
