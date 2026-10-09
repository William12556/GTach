Created: 2026 October 07

# Issue: Duplicate BluetoothDevice Models

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-c9de5fb0
  title: Two BluetoothDevice dataclasses (comm and setup) are converted by hand
    at two call sites
  date: '2026-10-07'
  reporter: Claude Code
  status: closed
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-c9de5fb0
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: Remaining part of audit-36b6ea95 A14. The other two parts (pairing.py
    reading YAML directly; duplicated connect-and-test logic) were removed by change-5fbff586
    and change-cd5ec050.
affected_scope:
  components:
  - name: comm BluetoothDevice
    file_path: src/gtach/comm/models.py
  - name: setup BluetoothDevice
    file_path: src/gtach/display/setup_models.py
  - name: BluetoothSetupInterface (conversion)
    file_path: src/gtach/display/setup_components/bluetooth/interface.py
  - name: SimBluetoothPairing (conversion)
    file_path: src/gtach/comm/sim_bluetooth.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: ''
  steps:
  - Inspect comm/models.py:20 and display/setup_models.py:52.
  - Inspect the conversions at interface.py:429 and sim_bluetooth.py:219.
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: One device model, or one conversion function used by both call sites.
  actual: Two models with different fields (signal_strength/last_seen vs last_connected)
    and two hand-written conversions.
  impact: A field added to one model is silently dropped at conversion; the two
    conversions can drift.
  workaround: ''
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: Separate models grew in comm and display; DeviceStore persists the
    comm model, setup works with the display model.
  technical_notes: ''
  related_issues:
  - issue_ref: issue-cd5ec050
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: Add a single conversion (for example a classmethod on the comm model)
    used by both sites, or merge the models.
  change_ref: change-c9de5fb0
  resolved_date: '2026-10-09'
  resolved_by: Claude Code (change-c9de5fb0, commit 7c6574e)
  fix_description: ''
verification:
  verified_date: '2026-10-09'
  verified_by: William Watson
  test_results: test-c9de5fb0 passed (6/6); pairing saved with an upper-case MAC and survived a service restart on gtach.local.
  closure_notes: Closed after on-device verification. A pre-existing EBUSY failure of the post-pairing probe was raised as issue-d26ca557.
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - Both call sites use the shared conversion; pytest passes.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-c9de5fb0
  test_refs:
  - ''
notes: audit-36b6ea95 A14 (partial).
loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ''
  last_review_feedback: ''
version_history:
- version: '1.0'
  date: '2026-10-07'
  author: Claude Code
  changes:
  - Initial issue document, raised at the close of audit-36b6ea95 remediation.
- version: '1.1'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Coupled to change-c9de5fb0 (P03.7); approach chosen - one shared conversion, both models kept.
- version: '1.2'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Resolved by change-c9de5fb0; verified by test-c9de5fb0; closed.
metadata:
  copyright: Copyright (c) 2026 William Watson. MIT License.
  template_version: '1.0'
  schema_type: t03_issue
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial issue document. Raised at the close of audit-36b6ea95 remediation. |
| 1.1 | 2026-10-09 | Coupled to change-c9de5fb0; shared conversion chosen. |
| 1.2 | 2026-10-09 | Resolved by change-c9de5fb0; verified by test-c9de5fb0; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
