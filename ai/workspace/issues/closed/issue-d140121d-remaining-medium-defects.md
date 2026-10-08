Created: 2026 October 07

# Issue: Pairing Timeouts, Shared Setup State and Unbounded Shutdown

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-d140121d"
  title: "System Bluetooth socket ignores its timeout; hung discovery workers block shutdown; setup state is shared live and mutated without the coordinator lock; the async-operations map is unguarded; shutdown has no overall deadline and leaves touch, async and pairing threads running"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-d140121d"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-36b6ea95 findings A07, A08, D04, D05, X02 (medium) and A17, C14 (low)."

affected_scope:
  components:
    - name: "BluetoothSocket.connect"
      file_path: "src/gtach/comm/system_bluetooth.py"
    - name: "BluetoothPairing discovery and shutdown"
      file_path: "src/gtach/comm/pairing.py"
    - name: "SetupStateCoordinator.get_state; new add_discovered_device"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
    - name: "BluetoothSetupInterface state writes and _active_operations"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "SetupDisplayManager setup loop and stop_setup"
      file_path: "src/gtach/display/setup.py"
    - name: "DisplayManager.stop"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication.shutdown / _watchdog_shutdown"
      file_path: "src/gtach/app.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "Pi with Bluetooth, or tests with stubs."
  steps:
    - "A07: pair against an absent MAC on the 'system' backend; connect blocks for the kernel page timeout, not connection_timeout."
    - "D04: render DEVICE_LIST while discovery appends devices from a worker thread."
    - "X02: `time systemctl stop gtach` during discovery."
  frequency: "always (A07, D04 race intermittent)"
  reproducibility_conditions: "From source."
  test_data: >
    system_bluetooth.py BluetoothSocket.settimeout stores the value
    before connect(); connect() creates the socket and never applies it.
    pairing.py chunked discovery: futures that time out keep running;
    shutdown() uses wait=True and __del__ calls it; the chunk duration
    uses self.discovery_timeout // chunks rather than the effective
    timeout (A17).
    coordinator.get_state returns the live SetupState; interface.py
    assigns state.pairing_status, discovery_progress, discovered_devices,
    error_message and appends to discovered_devices from worker threads
    (about 25 sites) without the lock and without notifying callbacks.
    interface._active_operations is read and written from worker
    callbacks, the setup thread and the touch thread without a lock;
    setup.py reads it directly.
    app.shutdown has no overall deadline; the 20 s backstop is armed
    only on the watchdog path. DisplayManager.stop does not stop the
    touch handler (C14); the async operation manager and the pairing
    executor are never shut down.
  error_output: "None."

behavior:
  expected: "Bounded connects and shutdown; setup state changed only under the coordinator lock; readers see consistent copies."
  actual: "As in test_data."
  impact: "Long blocks during pairing; torn setup state; stops that run to systemd's timeout."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Missing lock discipline around shared setup state; incomplete component shutdown."
  technical_notes: >
    Once get_state returns a copy, every write that currently mutates a
    state object passed into interface.py must go through the
    coordinator, or it is lost. Tests construct the interface without a
    coordinator, so a fallback that mutates the passed object directly is
    kept for that case.

    ThreadPoolExecutor worker threads are joined at interpreter exit
    regardless of shutdown(wait=False); the process-level backstop
    (armed on every exit path) bounds that case.
  related_issues:
    - issue_ref: "issue-fbe7e98a"
      relationship: "related. Callbacks outside locks in the same components."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-d140121d."
  change_ref: "change-d140121d"
  resolved_date: "2026-10-08"
  resolved_by: "change-d140121d"
  fix_description: "BluetoothSocket applies its timeout before connect, pairing shutdown no longer waits on running scans, the setup coordinator owns setup state (get_state returns copies; writes go through update_state and add_discovered_device) with _active_operations locked, and shutdown arms the exit backstop on every path and stops the async workers, the pairing executor and the touch handler (commit 69eb605f2b086d666248bb39a4046032f9eb94d8)."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session B (2026-10-07): systemctl stop during discovery 0.41 s."
  closure_notes: "Closed at audit-36b6ea95 close-out after on-device verification."

prevention:
  preventive_measures: "State writes only through the coordinator; one shutdown path that stops every thread owner."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-d140121d."
    - "After the fix: `time systemctl stop gtach` during discovery completes well under 30 s."
  verification_results: "All verification steps complete; see verification.test_results."

traceability:
  design_refs: []
  change_refs:
    - "change-d140121d"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 A07, A08, A17, C14, D04, D05, X02."

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
      - "Initial issue document for Phase 5 remaining medium defects."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in 69eb605f2b086d666248bb39a4046032f9eb94d8; awaiting on-device verification."
  - version: "1.2"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "On-device verification complete; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial issue document. A07, A08, A17, C14, D04, D05, X02. |
| 1.1 | 2026-10-07 | Fix implemented in 69eb605f2b086d666248bb39a4046032f9eb94d8; awaiting on-device verification. |
| 1.2 | 2026-10-08 | On-device verification complete; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
