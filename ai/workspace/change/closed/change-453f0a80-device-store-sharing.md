Created: 2026 October 07

# Change: Shared, Locked DeviceStore Under GTACH_HOME

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-453f0a80"
  title: "DeviceStore defaults to gtach_home()/config/devices.yaml, guards its state with a lock, fsyncs before replace, and is obtained through get_device_store(); all production call sites use the accessor; the tracked config/devices.yaml is removed"
  date: "2026-10-07"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-453f0a80"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-453f0a80"
  description: "Resolves issue-453f0a80 (audit-36b6ea95 A09, A10, G07)."

scope:
  summary: "One shared DeviceStore instance with a lock and durable writes, located under GTACH_HOME."
  affected_components:
    - name: "DeviceStore, get_device_store, reset_device_store"
      file_path: "src/gtach/comm/device_store.py"
      change_type: "modify"
    - name: "Call sites"
      file_path: "src/gtach/app.py, src/gtach/comm/transport.py, src/gtach/comm/sim_bluetooth.py, src/gtach/display/manager.py, src/gtach/display/setup.py, src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "Repository seed file"
      file_path: "config/devices.yaml"
      change_type: "delete"
    - name: "Tests"
      file_path: "tests/"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-f6a7b8c9-component_comm_device_store"
      update_required: "Update after implementation (P04.3)."
  out_of_scope:
    - "devices.yaml schema and the primary/secondary model."
    - "BluetoothDevice model duplication (audit A14)."

rational:
  problem_statement: "See issue-453f0a80."
  proposed_solution: >
    EDIT A — DeviceStore.__init__(self, config_path: Optional[str] = None):
    default str(gtach_home() / 'config' / 'devices.yaml'). Add
    self._lock = threading.Lock(). Every public method (save_device,
    get_primary_device, get_all_devices, remove_device,
    get_device_by_mac) performs its read or read-modify-save under the
    lock. Private helpers assume the lock is held where called from a
    public method; document this. No callbacks or foreign calls under
    the lock.

    EDIT B — _save_config: after yaml.dump to the temporary file, call
    f.flush() and os.fsync(f.fileno()) before os.replace.

    EDIT C — module-level accessor:
    `_shared: Optional[DeviceStore] = None`, `_shared_lock = threading.Lock()`,
    `def get_device_store() -> DeviceStore` (create on first call via
    the module-level name DeviceStore so tests that patch the class keep
    working), `def reset_device_store() -> None` (sets _shared to None;
    for tests and setup re-entry is not required).

    EDIT D — replace every production `DeviceStore()` construction with
    get_device_store(): app.py, transport.py, sim_bluetooth.py,
    manager.py, setup.py (all), interface.py. Imports adjusted.

    EDIT E — `git rm config/devices.yaml`.

    EDIT F — tests: conftest autouse fixture calls reset_device_store()
    after each test. Tests that monkeypatch DeviceStore continue to
    work; adjust any that rely on per-call construction. Add
    tests/test_device_store_shared.py.
  alternatives_considered:
    - option: "Inject a DeviceStore through constructors."
      reason_rejected: "Touches many signatures; the accessor gives one instance with fewer changes."
  benefits:
    - "No stale reads or lost writes."
    - "Durable writes across power loss."
    - "No runtime writes to tracked files."
  risks:
    - risk: "A long-lived instance holds state another process changed on disk."
      mitigation: "GTach is the only writer of devices.yaml."

technical_details:
  current_behavior: "Independent unlocked instances at a CWD-relative path."
  proposed_behavior: "One locked instance at gtach_home()/config/devices.yaml."
  implementation_approach: "Lock in DeviceStore; accessor; call-site replacement."
  code_changes:
    - component: "DeviceStore"
      file: "src/gtach/comm/device_store.py"
      change_summary: "EDITS A to C"
      functions_affected:
        - "__init__"
        - "_save_config"
        - "save_device"
        - "get_primary_device"
        - "get_all_devices"
        - "remove_device"
        - "get_device_by_mac"
        - "get_device_store (new)"
        - "reset_device_store (new)"
      classes_affected:
        - "DeviceStore"
  data_changes:
    - entity: "devices.yaml"
      change_type: "migration"
      details: "Location becomes gtach_home()/config/devices.yaml, identical to /opt/gtach/config/devices.yaml on the Pi; no data migration required."
  interface_changes:
    - interface: "gtach.comm.device_store.get_device_store"
      change_type: "contract"
      details: "New accessor for the shared instance."
      backward_compatible: "yes"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-5fbff586"
      relationship: "blocked_by. gtach_home()."

testing_requirements:
  test_approach: "Unit tests with GTACH_HOME at tmp_path."
  test_cases:
    - scenario: "get_device_store() twice."
      expected_result: "Same object."
    - scenario: "Default path with GTACH_HOME=tmp_path."
      expected_result: "tmp_path/config/devices.yaml."
    - scenario: "save_device then get_primary_device via the accessor from another call site."
      expected_result: "Device returned."
    - scenario: "Two threads each saving 50 devices as secondary concurrently."
      expected_result: "No exception; file parses; all entries present."
    - scenario: "_save_config with os.fsync patched to record."
      expected_result: "fsync called before os.replace."
    - scenario: "reset_device_store then get_device_store."
      expected_result: "New object."
  regression_scope:
    - "tests/test_setup_lock_order.py, tests/test_setup_and_gauge.py, tests/test_callbacks_outside_locks.py, tests/test_connect_error_classification.py."
    - "Full tests/ suite."
  validation_criteria:
    - "grep -rn 'DeviceStore()' src (backups excluded) returns only the construction inside get_device_store."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to F."
      owner: "tactical"
    - step: "On the Pi: paired device still found after upgrade."
      owner: "human"
    - step: "Update design-f6a7b8c9 (P04.3)."
      owner: "strategic"
  rollback_procedure: "Revert the commit."
  deployment_notes: "No action on the Pi; the path is unchanged there."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session A (2026-10-07): devices.yaml read from the new location; paired adapter used via CURRENT_DEVICE without re-pairing."
  issues_found: []

traceability:
  design_updates:
    - design_ref: "design-a6b7c8d9-component_comm_device_store"
      sections_updated: ["2.3", "5.2", "5.3 (new)", "7.0", "version 1.1"]
      update_date: "2026-10-07"
    - design_ref: "design-f6a7b8c9-component_comm_device_store"
      sections_updated: ["marked superseded by design-a6b7c8d9"]
      update_date: "2026-10-07"
  related_changes:
    - change_ref: "change-5fbff586"
      relationship: "blocked_by"
  related_issues:
    - issue_ref: "issue-453f0a80"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-453f0a80 iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in 3747d2fd16f15cecb30316b47cee8bfd7b8e5d1f."
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
| 1.0 | 2026-10-07 | Initial change document. Shared, locked DeviceStore under GTACH_HOME. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in 3747d2fd16f15cecb30316b47cee8bfd7b8e5d1f. |
| 1.3 | 2026-10-08 | Verified on device; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
