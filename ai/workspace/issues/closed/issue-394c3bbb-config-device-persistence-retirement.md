Created: 2026 August 04

# Issue: A Second Device-Persistence Subsystem With No Callers, Whose Three Methods Would Raise AttributeError If Anything Called Them

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-394c3bbb"
  title: "ConfigManager carries a device-persistence path parallel to DeviceStore with no live caller, and its three methods reference a .address attribute that BluetoothDevice does not define, so any call would raise AttributeError immediately"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-394c3bbb"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Findings §5.1 (Parallel, largely disconnected device-persistence
    subsystem) and §3.6 (Non-existent .address attribute), with §7.0
    recommendation #6 and the retirement branch of recommendation #1.
    The correction branch of #1 was claimed separately by
    change-1143427b, which is closed. Disposition decided in ai/task.md
    §7.4.8. Task list reference ai/task.md §7.4.1.

affected_scope:
  components:
    - name: "ConfigManager.get_device_by_address"
      file_path: "src/gtach/utils/config.py"
    - name: "ConfigManager.add_or_update_device"
      file_path: "src/gtach/utils/config.py"
    - name: "ConfigManager.remove_device"
      file_path: "src/gtach/utils/config.py"
    - name: "BluetoothConfig.saved_devices"
      file_path: "src/gtach/utils/config.py"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: "Source checkout at 0.3.2."
  steps:
    - "§3.6 — read comm/models.py:20-24. BluetoothDevice defines name, mac_address, device_type and last_connected. There is no address field."
    - "§3.6 — read utils/config.py:1454. 'device.address.upper()' inside get_device_by_address."
    - "§3.6 — read utils/config.py:1470. 'self.get_device_by_address(config, device.address)' inside add_or_update_device."
    - "§3.6 — read utils/config.py:1498. 'config.bluetooth.last_device == device.address' inside remove_device."
    - "§3.6 — construct a BluetoothDevice and access .address. AttributeError."
    - "§5.1 — grep get_device_by_address, add_or_update_device and remove_device across src/gtach. The only hits outside utils/config.py are DeviceStore.remove_device (comm/device_store.py:236), a different method with a different signature."
    - "§5.1 — grep saved_devices across src/gtach. Every hit is inside utils/config.py."
    - "§5.1 — grep DeviceStore across src/gtach and count the call sites; it is the store the live pairing flow uses."
  frequency: "always"
  reproducibility_conditions: >
    The AttributeError is unconditional on any call. There are no calls,
    so it has never occurred. That is the finding.
  preconditions: "None."
  test_data: >
    CALL-GRAPH EVIDENCE, re-verified at 0.3.2 rather than taken from
    ai/task.md §7.4.8.

      ConfigManager.get_device_by_address — callers outside
      utils/config.py: 0. Internal callers: add_or_update_device
      (config.py:1470) and remove_device (config.py:1492).
      ConfigManager.add_or_update_device — callers: 0.
      ConfigManager.remove_device — callers: 0.
      BluetoothConfig.saved_devices — references outside
      utils/config.py: 0. Inside: the field (435), to_dict (462),
      from_dict (486-492) and the three methods (1453, 1474, 1475,
      1478, 1495).

      DeviceStore — used by app.py, comm/transport.py,
      comm/sim_bluetooth.py, display/setup.py, display/manager.py and
      display/setup_components/bluetooth/interface.py. It is the live
      store, backed by config/devices.yaml.

    So the subsystem is not merely disconnected; it is unreachable, and
    would fail immediately if it were reached.

    SCOPE CORRECTION — comm/models.py MUST NOT BE DELETED. ai/task.md
    §7.4 lists comm/models.py among 7.4.1's primary files. That is
    correct only in the sense that the file is implicated; the
    BluetoothDevice class it defines is LIVE and is used by
    comm/device_store.py (imported at device_store.py:27, constructed at
    197 and 224) and re-exported by comm/__init__.py:15. Deleting it, or
    the class, would break the surviving store. The only change this
    triple makes to that file is none.

    PERSISTED DATA. config/config.yaml carries bluetooth.saved_devices
    as an empty list. Deployed installations may carry entries. The
    retirement must tolerate the key's presence on load rather than
    failing on it, and should not rewrite the operator's file.
  error_output: >
    None observed. AttributeError: 'BluetoothDevice' object has no
    attribute 'address' would be raised on any call, and none occurs.

behavior:
  expected: >
    One device store. A method that references an attribute of a class
    it imports uses an attribute that class defines.
  actual: >
    Two device-persistence subsystems. DeviceStore
    (comm/device_store.py) is the live one, backed by
    config/devices.yaml and used across six modules. ConfigManager
    carries a second — BluetoothConfig.saved_devices plus three methods
    at utils/config.py:1440-1501 — that no code calls and that would
    raise AttributeError if it did, because it reads device.address
    where the model defines mac_address.
  impact: >
    Maintenance and confusion rather than malfunction. A reader
    encountering both stores must establish which is live. A future
    author may extend the wrong one — and would find it did not work,
    for a reason unrelated to what they were doing.

    The report also cites this as the reason §3.1's RWLock deadlock had
    not surfaced. That inference is wrong and was corrected in ai/task.md
    §7.4.8: _rw_lock guards load_config and save_config, which are on
    the live startup path. §3.1 was separated into change-1143427b and
    is closed.
  workaround: "Not applicable — nothing calls it."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "PyYAML"
      version: "any"
  domain: "domain_1"

analysis:
  root_cause: >
    Two implementations of the same concern written at different times.
    The ConfigManager path appears to predate DeviceStore; when
    DeviceStore became the live store the older path was not removed.
    The .address / mac_address mismatch is evidence that the older path
    was never exercised after the model settled on mac_address — a
    single call would have surfaced it.
  technical_notes: >
    DISPOSITION IS DECIDED. ai/task.md §7.4.8 records the §7.5.4
    decision taken on 2026-07-30: RETIRE. DeviceStore is the sole device
    store by declaration. This triple implements that decision; it does
    not reopen it. The alternative — fixing §3.1 and §3.6 and routing
    the live pairing flow through ConfigManager instead — is recorded in
    the report at §5.1 and was not taken.

    WHAT THE RETIREMENT DOES NOT CLOSE. §7.4.8 corrects an earlier
    misstatement worth repeating here: retiring the device methods does
    NOT close §3.1, the RWLock notification defect. _rw_lock guards
    ConfigManager.load_config and save_config, the whole configuration
    path, which app.py and main.py exercise on every start. §3.1 was
    separated into triple 7.4.9 (change-1143427b), which is implemented
    and closed. Nothing in this triple touches RWLock.

    THREE CORRECTIONS TO SCOPE AS RECORDED IN ai/task.md §7.4.

    (1) comm/models.py is listed as a primary file. It must not be
    modified. Its BluetoothDevice is live via DeviceStore. See
    test_data.

    (2) comm/device_store.py is listed as a primary file. It also
    requires no change: it is the survivor. It is listed presumably
    because the decision concerned which of the two stores lives, but
    the implementation touches only the loser. Recorded so an
    implementer does not go looking for an edit that is not there.

    (3) The report's "approximately 1,600 lines of parallel machinery"
    conflates the whole of utils/config.py with the device-persistence
    subset — a correction ai/task.md §7.4.8 already records. The actual
    deletion is three methods (about 62 lines), one dataclass field, and
    its two serialisation sites. The validator, transactional-write and
    session-archival machinery serves the main configuration and stays.

    ORDERING RELATIVE TO 7.4.7, ALREADY RESOLVED. ai/task.md §7.6.1
    records that 7.4.7 (d32ccc49) and this triple both modify
    utils/config.py, and required 7.4.7's §5.2 singleton warning to be
    sited in ConfigManager.__new__ or __init__ so the two would not
    collide. d32ccc49 is implemented and did exactly that — the warning
    is inside __init__'s double-initialisation guard, far above the
    region deleted here. Verified: no overlap. Cross-check discrepancy
    D2 is discharged.

    D1 TYPE OBLIGATION.
    ai/workspace/report/task-list-cross-check-discrepancies.md §5.4
    step 5 requires this issue to carry issue_info.type: defect under
    either disposition, §3.1 and §3.6 being recorded as defects whether
    fixed or removed. It does.
  related_issues:
    - issue_ref: "issue-1143427b"
      relationship: "related"
    - issue_ref: "issue-d32ccc49"
      relationship: "blocked_by"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Delete the three ConfigManager device methods, the
    BluetoothConfig.saved_devices field and its two serialisation sites.
    Tolerate a saved_devices key found in an existing configuration file
    without failing and without rewriting it. Change nothing in
    comm/models.py or comm/device_store.py. See change-394c3bbb.
  change_ref: "change-394c3bbb"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    Two implementations of one concern should not both be retained
    without a recorded reason for each. The .address mismatch is the
    signature of code that has never run: an attribute error on the
    first line of the first method is not survivable, so its absence
    from every log is proof of disuse.
  process_improvements: >
    The report inferred from §5.1 that §3.1 was low-exposure, and that
    inference was wrong in a way that would have silently dropped a
    Critical defect had the retirement proceeded without the §7.4.8
    re-examination. When a finding is used to downgrade another
    finding's severity, the dependency should be checked directly rather
    than accepted.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/utils/config.py passes."
    - "get_device_by_address, add_or_update_device and remove_device are absent from ConfigManager."
    - "BluetoothConfig has no saved_devices field."
    - "BluetoothConfig.to_dict emits no saved_devices key."
    - "BluetoothConfig.from_dict ignores a saved_devices key without raising."
    - "A config.yaml carrying bluetooth.saved_devices with entries loads without error."
    - "A round trip through load_config and save_config on such a file does not raise."
    - "grep confirms no reference to device.address remains in src/gtach."
    - "comm/models.py is byte-identical to its current text."
    - "comm/device_store.py is byte-identical to its current text."
    - "The RWLock class in utils/config.py is byte-identical — change-1143427b's correction is untouched."
    - "The singleton warning added by change-d32ccc49 in ConfigManager.__init__ is byte-identical."
    - "ConfigManager's remaining methods are unchanged in count and behaviour, other than the three removed."
    - "DeviceStore's behaviour is unchanged, exercised through its existing call sites."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-394c3bbb"
  test_refs: []

notes: >
  This is task 7.4.1 in ai/task.md §7.4 and step 8 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5) as a large
  deletion, deliberately separated from the v0.3.0 corrections.

  issue_info.type is defect per ai/task.md §7.2 and the D1 discharge
  step at task-list-cross-check-discrepancies.md §5.4 item 5.

  The §7.5.4 disposition is decided — retire (§7.4.8) — so this triple
  is not gated. Its only ordering constraint, the shared utils/config.py
  edit with 7.4.7, is already discharged: d32ccc49 landed with its edit
  confined to ConfigManager.__init__.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial issue document from core-comm-utils-code-review.md findings §5.1 and §3.6 with §7.0 recommendation #6 and the retirement branch of #1, implementing the decision recorded in ai/task.md §7.4.8."
      - "Re-verified the call-graph evidence at 0.3.2 rather than citing §7.4.8: the three methods have no external callers and saved_devices has no reference outside utils/config.py."
      - "Recorded three scope corrections to ai/task.md §7.4: comm/models.py must not be modified, its BluetoothDevice being live via DeviceStore; comm/device_store.py requires no change, being the survivor; and the report's 1,600-line figure describes the whole file rather than the subset deleted."
      - "Recorded that the 7.4.7 ordering constraint is already discharged, change-d32ccc49 having confined its edit to ConfigManager.__init__."
      - "Recorded that the retirement does not close §3.1, which change-1143427b handled separately and which is closed."

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
| 1.0 | 2026-08-04 | Initial issue document from core review findings §5.1 and §3.6 with recommendations #1 (retirement branch) and #6. Re-verifies the call-graph evidence at 0.3.2 and records three scope corrections to ai/task.md §7.4, chiefly that `comm/models.py` must not be modified. |

---

Copyright (c) 2026 William Watson. MIT License.
