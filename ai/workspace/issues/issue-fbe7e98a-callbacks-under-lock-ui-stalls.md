Created: 2026 October 07

# Issue: Callbacks Run Under Locks and Blocking Probes on UI Threads

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-fbe7e98a"
  title: "AsyncOperationManager, TouchCoordinator and the touch interface invoke callbacks while holding their locks; the CURRENT_DEVICE Continue probe blocks the touch thread; setup completion callbacks also fire on every progress update"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-fbe7e98a"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 findings D03 (high), D06, C04 and C02
    (medium). A further defect in the same mechanism was found while
    preparing this issue and is recorded here as D12 (new): the setup
    interface's completion callbacks are also invoked on every progress
    update and treat the RUNNING status as a terminal outcome.

affected_scope:
  components:
    - name: "AsyncOperationManager._worker_loop / _update_operation_progress"
      file_path: "src/gtach/display/async_operations.py"
    - name: "TouchCoordinator.handle_touch_down / _handle_button_touch_down"
      file_path: "src/gtach/display/input/touch_coordinator.py"
    - name: "TouchInterface._emit_touch_event"
      file_path: "src/gtach/display/touch_interface.py"
    - name: "SetupDisplayManager._handle_touch_action ('current_continue')"
      file_path: "src/gtach/display/setup.py"
    - name: "BluetoothSetupInterface completion callbacks"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "GTach in setup mode on the Pi, ELM327 adapter paired or absent."
  steps:
    - "D03: pair a device; during OBD verification (up to ~15 s) the setup and discovery screens stop updating."
    - "D06/C04: on DISCONNECTED, tap Setup; the display freezes for 2-7 s while re-entry joins threads."
    - "C02: on CURRENT_DEVICE with the adapter off, tap Continue; touch input is frozen for up to 10 s."
    - "D12: start discovery; the log shows 'Discovery ended with status: OperationStatus.RUNNING' at the first progress update."
  frequency: "always"
  reproducibility_conditions: "Deterministic from source."
  test_data: >
    async_operations.py:298-306 and 330-338 invoke
    progress_callbacks[operation_id](operation) inside
    `with self._operations_lock` (threading.Lock, line 76).
    _update_operation_progress (319-338) invokes the same callback on
    every progress update; interface.py registers its completion
    handlers as that callback (on_bluetooth_init_complete,
    on_discovery_complete, on_pairing_complete), and each treats any
    status other than COMPLETED or FAILED as final: init sets pairing to
    None and sets _pairing_ready; discovery sets pairing_status IDLE and
    removes its _active_operations entry; pairing sets pairing_status
    FAILED and removes its entry.

    on_pairing_complete runs verify_obd_connection (RFCOMM connect, 10 s
    timeout, plus ATZ, 5 s) inside that callback, so the operations lock
    is held for up to ~15 s; get_operation_status, cancel_operation and
    submit_operation block meanwhile.

    touch_coordinator.py:211-250, 468-479: handle_touch_down holds the
    RLock _lock and calls the button callback; DisplayManager's
    callbacks include app._re_enter_setup (2-7 s of joins). The display
    thread blocks in clear_regions / register_button_region meanwhile.

    touch_interface.py:166-178: _emit_touch_event calls the registered
    callback inside `with self._lock` (threading.Lock); the entire UI
    action chain runs under it.

    setup.py:775-791: 'current_continue' calls RFCOMMTransport.connect()
    synchronously on the touch thread. Under simulation the stored MAC
    never connects, so Continue always fails on the development host.
  error_output: "Warnings such as 'Discovery ended with status: OperationStatus.RUNNING'."

behavior:
  expected: >
    Callbacks run without the invoker's lock held; blocking I/O never
    runs on the touch thread; completion handlers act only on terminal
    status.
  actual: "As in test_data. All confirmed in source."
  impact: >
    UI freezes of 2-15 s during setup and DISCONNECTED → Setup.
    Self-deadlock if a callback queries its invoker. D12 can cause a
    discovery started during Bluetooth initialisation to fail, and hides
    discovery progress because the operation entry is removed early.
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    Call-outs under lock (audit X01), and a single callback slot used for
    both progress and completion without the handlers distinguishing the
    two.
  technical_notes: >
    TouchCoordinator.handle_touch_up, handle_touch_move and gesture
    callbacks are not reached in the current delivery path
    (manager.py:248-255); they are dead code (audit C12) and are left
    unchanged.

    Moving the OBD verification out from under the operations lock is
    sufficient: it still runs on an async worker thread, which is not a
    UI thread.
  related_issues:
    - issue_ref: "issue-e9216e17"
      relationship: "related. Same rule applied to the setup lock cycle; this issue depends on CLAUDE.md rule 8 added there."

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Invoke callbacks after releasing the lock in AsyncOperationManager,
    TouchCoordinator.handle_touch_down and _emit_touch_event. Return
    early from completion handlers on non-terminal status. Run the
    Continue probe as an async operation with a pass-through in
    simulation.
  change_ref: "change-fbe7e98a"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "CLAUDE.md rule 8 (issue-e9216e17)."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-fbe7e98a."
    - "After the fix: on the Pi, DISCONNECTED → Setup, pairing, and CURRENT_DEVICE → Continue with the adapter off; the display stays responsive."
  verification_results: "First step complete."

traceability:
  design_refs: []
  change_refs:
    - "change-fbe7e98a"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 D03, D06, C04, C02; new finding D12."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial issue document from audit-36b6ea95 D03, D06, C04, C02, plus new finding D12."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial issue document. Callbacks under lock; blocking Continue probe; completion handlers firing on progress (D12, new). |

---

Copyright (c) 2026 William Watson. MIT License.
