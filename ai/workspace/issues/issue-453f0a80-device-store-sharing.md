Created: 2026 October 07

# Issue: Unshared, Unlocked DeviceStore With a Working-Directory Path

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-453f0a80"
  title: "DeviceStore is constructed independently at eight call sites with its own in-memory copy, has no lock, resolves devices.yaml relative to the working directory, and writes without fsync"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-453f0a80"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-36b6ea95 findings A09 (medium), A10 (low) and the devices.yaml part of G07."

affected_scope:
  components:
    - name: "DeviceStore"
      file_path: "src/gtach/comm/device_store.py"
    - name: "DeviceStore call sites"
      file_path: "src/gtach/app.py, src/gtach/comm/transport.py, src/gtach/comm/sim_bluetooth.py, src/gtach/display/manager.py, src/gtach/display/setup.py, src/gtach/display/setup_components/bluetooth/interface.py"
  designs:
    - "ai/workspace/design/design-f6a7b8c9-component_comm_device_store.md"
    - "ai/workspace/design/design-a6b7c8d9-component_comm_device_store.md"
  version: "0.4.3"

reproduction:
  prerequisites: "Any host."
  steps:
    - "Construct two DeviceStore instances, save a device through one, read through the other: the second does not see it until reconstructed; a save through the second overwrites the first's write."
  frequency: "always"
  reproducibility_conditions: "Deterministic from source."
  test_data: >
    device_store.py:32 default path 'config/devices.yaml' (CWD-relative;
    /opt/gtach/config/devices.yaml under systemd, the repository's
    tracked config/devices.yaml in development). No lock around load,
    mutate or save. _save_config writes a temporary file and os.replace
    without flush or fsync. DeviceStore() is constructed at app.py:64,
    transport.py:716, sim_bluetooth.py:211, manager.py:2069, setup.py
    (several), interface.py:29.
  error_output: "None."

behavior:
  expected: "One store instance, guarded by a lock, at an absolute path, durably written."
  actual: "As in test_data."
  impact: "Stale reads and lost writes between instances; possible empty devices.yaml after power loss; tracked file rewritten in development."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "DeviceStore was designed as a cheap value object but holds mutable state persisted to one file."
  technical_notes: >
    gtach_home()/config/devices.yaml equals the path the Pi uses today
    (/opt/gtach/config/devices.yaml), so no migration is needed.
    Several tests patch gtach.comm.device_store.DeviceStore; a lazily
    created shared instance plus a reset function keeps those patches
    effective.
  related_issues:
    - issue_ref: "issue-5fbff586"
      relationship: "blocked_by. Provides gtach_home()."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-453f0a80."
  change_ref: "change-453f0a80"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Single accessor; direct construction only in tests."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-453f0a80."
    - "After the fix: on the Pi, the paired device is still found after the upgrade."
  verification_results: "First step complete."

traceability:
  design_refs:
    - "design-f6a7b8c9-component_comm_device_store"
  change_refs:
    - "change-453f0a80"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 A09, A10, G07."

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
      - "Initial issue document from audit-36b6ea95 A09, A10, G07."

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
| 1.0 | 2026-10-07 | Initial issue document. Unshared, unlocked DeviceStore. |

---

Copyright (c) 2026 William Watson. MIT License.
