Created: 2026 August 04

# Change: Retire the Second Device Store

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-394c3bbb"
  title: "ConfigManager's three device-persistence methods, BluetoothConfig.saved_devices and its two serialisation sites are removed; a saved_devices key found in an existing configuration file is ignored rather than rejected, and the operator's file is not rewritten"
  date: "2026-08-04"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-394c3bbb"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-394c3bbb"
  description: >
    Resolves issue-394c3bbb. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 findings
    §5.1 and §3.6 with §7.0 recommendation #6 and the retirement branch
    of #1, implementing the §7.5.4 decision recorded in ai/task.md
    §7.4.8. Task list reference ai/task.md §7.4.1.

scope:
  summary: >
    One of two device-persistence subsystems is deleted. DeviceStore
    remains the sole store. About 70 lines go from utils/config.py; no
    other file changes.
  affected_components:
    - name: "ConfigManager.get_device_by_address"
      file_path: "src/gtach/utils/config.py"
      change_type: "remove"
    - name: "ConfigManager.add_or_update_device"
      file_path: "src/gtach/utils/config.py"
      change_type: "remove"
    - name: "ConfigManager.remove_device"
      file_path: "src/gtach/utils/config.py"
      change_type: "remove"
    - name: "BluetoothConfig.saved_devices"
      file_path: "src/gtach/utils/config.py"
      change_type: "remove"
    - name: "BluetoothConfig.to_dict"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
    - name: "BluetoothConfig.from_dict"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "comm/models.py. MUST NOT be modified. Its BluetoothDevice is live via comm/device_store.py:27, 197, 224 and is re-exported by comm/__init__.py:15. ai/task.md §7.4 lists it as a primary file; that is a scope error corrected in issue-394c3bbb."
    - "comm/device_store.py. MUST NOT be modified. It is the surviving store."
    - "The RWLock class in utils/config.py. change-1143427b corrected it; the retirement does not touch it and does not close §3.1."
    - "ConfigManager.__new__ and __init__, including the singleton warning added by change-d32ccc49."
    - "ConfigManager.load_config, save_config, the validator, the transactional-write machinery and session archival. All serve the main application configuration."
    - "config/config.yaml. The checked-in file carries bluetooth.saved_devices: [] and is left as it is; the loader ignores the key. Rewriting it is a data migration this change does not need."
    - "Every other field of BluetoothConfig — auto_connect, last_device, the timeouts, device_filter and the ELM327 settings. Only saved_devices goes."

rational:
  problem_statement: >
    ConfigManager carries a device-persistence path parallel to
    DeviceStore with no caller anywhere in src/gtach, whose three
    methods reference a .address attribute that BluetoothDevice does not
    define and would therefore raise AttributeError on any call.
  proposed_solution: >
    Delete it. DeviceStore is the sole store by the decision recorded in
    ai/task.md §7.4.8.
  alternatives_considered:
    - option: "Correct .address to .mac_address and keep both stores."
      reason_rejected: >
        This is the report's other branch at §5.1 and the §7.5.4
        decision went against it on 2026-07-30. Correcting the
        attribute would make the path callable without giving it a
        caller, which is the worst of both: live-looking code that is
        still dead, now without the AttributeError that proves it."
    - option: "Route the live pairing flow through ConfigManager and retire DeviceStore instead."
      reason_rejected: >
        Also considered at §7.5.4 and rejected. DeviceStore has around
        fifteen call sites across six modules and is backed by its own
        config/devices.yaml; ConfigManager's path has none and has never
        executed. Retiring the working store in favour of the one that
        has never run is the wrong direction."
    - option: "Leave saved_devices in BluetoothConfig and remove only the three methods."
      reason_rejected: >
        Smaller diff. Rejected because the field is the subsystem's
        data: with the methods gone nothing reads or writes it, and a
        list that is serialised on every save and never populated is
        exactly the confusion this change exists to remove."
    - option: "Rewrite deployed config.yaml files to drop the saved_devices key."
      reason_rejected: >
        A write during load surprises, and fails on a read-only
        filesystem. from_dict already ignores unknown keys by
        construction — it reads named fields rather than iterating the
        dict — so a stale key is inert. The key disappears from the file
        at the next ordinary save."
  benefits:
    - "One device store, so a future author cannot extend the wrong one."
    - "A method that would raise AttributeError on any call no longer exists to be called."
    - "About 70 lines and one dataclass field removed from a 1,676-line module."
  risks:
    - risk: >
        An external consumer outside src/gtach calls one of the three
        methods.
      mitigation: >
        They would receive AttributeError today, so no working consumer
        can exist. The risk is a consumer that catches broadly and
        treats the failure as 'no devices found'. grep across the
        repository, not only src/gtach, before deleting."
    - risk: >
        Deleting BluetoothDevice along with saved_devices, since the
        field is its only use inside utils/config.py.
      mitigation: >
        BluetoothDevice lives in comm/models.py and is live via
        DeviceStore. utils/config.py imports it at 37-45 with a
        try/except fallback; that import becomes unused and should be
        removed from utils/config.py, but the class and its module must
        not be touched. This is the single most likely way to break the
        build and is called out in the prompt."
    - risk: >
        A deployed config.yaml carrying saved_devices entries fails to
        load.
      mitigation: >
        from_dict reads named keys and ignores others, so the stale key
        is inert. Asserted with a fixture carrying populated entries."
    - risk: >
        The deletion region overlaps change-d32ccc49's singleton
        warning.
      mitigation: >
        It does not — verified. d32ccc49's edit is inside __init__'s
        double-initialisation guard around utils/config.py:1116-1140;
        the deletion is at 1440-1501. Cross-check D2 is discharged."
  benefits_measurement: >
    Device-persistence subsystems: 2 -> 1. Methods that raise
    AttributeError if called: 3 -> 0. utils/config.py: 1,676 -> about
    1,606 lines.

technical_details:
  current_behavior: >
    BluetoothConfig declares saved_devices at utils/config.py:435,
    serialises it at 462 and deserialises it at 486-492.
    ConfigManager defines get_device_by_address (1440-1457),
    add_or_update_device (1459-1480) and remove_device (1482-1501). The
    three reference device.address at 1454, 1470 and 1498.
    BluetoothDevice is imported at 37-45.
  proposed_behavior: >
    None of the above exists. BluetoothConfig carries its remaining
    fourteen fields. A saved_devices key in an existing file is read by
    nothing and written by nothing.
  implementation_approach: >
    FOUR EDITS, ALL IN src/gtach/utils/config.py.

    1. Remove the three methods at utils/config.py:1440-1501. They are
       contiguous, between get_home_path (1436-1438) and
       generate_session_id (1503). Confirm the boundaries by reading
       rather than by line number.

    2. Remove the saved_devices field at 435.

    3. Remove the "saved_devices" entry from to_dict at 462, and the
       saved_devices construction and argument in from_dict at 486-492.
       Keep every other field in both.

    4. Remove the now-unused BluetoothDevice import at 37-45 — but only
       after confirming nothing else in utils/config.py references the
       name. This import has a try/except fallback for two package
       layouts; remove the whole construct, not one branch.

    The order matters for a clean intermediate state: remove the
    methods first, then the field and its serialisation, then the
    import last, when it is provably unused.
  code_changes:
    - component: "ConfigManager"
      file: "src/gtach/utils/config.py"
      change_summary: "Three device-persistence methods removed."
      functions_affected:
        - "get_device_by_address"
        - "add_or_update_device"
        - "remove_device"
      classes_affected:
        - "ConfigManager"
    - component: "BluetoothConfig"
      file: "src/gtach/utils/config.py"
      change_summary: "saved_devices field and its two serialisation sites removed."
      functions_affected:
        - "to_dict"
        - "from_dict"
      classes_affected:
        - "BluetoothConfig"
  data_changes:
    - "Configuration files written after this change carry no bluetooth.saved_devices key. Files carrying it are loaded without error and are not rewritten; the key disappears at the next ordinary save."
  interface_changes:
    - "ConfigManager loses three public methods. No caller exists in the repository, and any that existed would be receiving AttributeError."
    - "BluetoothConfig loses one field."

dependencies:
  internal:
    - component: "change-d32ccc49"
      impact: "Landed. Its §5.2 singleton warning is in ConfigManager.__init__, outside the deleted region. Verified; cross-check D2 discharged."
    - component: "change-1143427b"
      impact: "Landed and closed. Its RWLock correction is untouched. The retirement does NOT close §3.1."
    - component: "comm/device_store.py"
      impact: "The surviving store. Unmodified; its behaviour must be unchanged."
    - component: "comm/models.py"
      impact: "Defines the live BluetoothDevice. Unmodified."
  external: []
  required_changes:
    - change_ref: "change-d32ccc49"
      relationship: "blocked_by"
    - change_ref: "change-1143427b"
      relationship: "related"

testing_requirements:
  test_approach: >
    Unit tests against BluetoothConfig's serialisation with real YAML
    fixtures, including one carrying populated saved_devices entries.
    ConfigManager's surviving surface is compared before and after by
    method set. DeviceStore is exercised through its existing behaviour
    to confirm it is untouched.
  test_cases:
    - scenario: "ConfigManager's public method set, before and after."
      expected_result: "Differs by exactly the three removed methods."
    - scenario: "hasattr(ConfigManager, 'get_device_by_address') and the other two."
      expected_result: "False for all three."
    - scenario: "BluetoothConfig fields."
      expected_result: "Fourteen; saved_devices absent."
    - scenario: "BluetoothConfig.to_dict output keys."
      expected_result: "No saved_devices key; every other key present and unchanged."
    - scenario: "BluetoothConfig.from_dict on a dict carrying saved_devices with three entries."
      expected_result: "Constructs successfully; the entries are ignored; every other field is read."
    - scenario: "from_dict on a dict with no saved_devices key."
      expected_result: "Constructs successfully."
    - scenario: "from_dict on an empty dict."
      expected_result: "Defaults, as today."
    - scenario: "A full load_config on a config.yaml fixture carrying populated saved_devices."
      expected_result: "No exception; the remaining bluetooth settings are correct."
    - scenario: "load_config then save_config on that fixture."
      expected_result: "No exception; the written file has no saved_devices key; every other setting round-trips."
    - scenario: "grep device.address across the whole repository."
      expected_result: "No occurrence in src/gtach."
    - scenario: "import gtach.utils.config."
      expected_result: "Succeeds — confirming the BluetoothDevice import removal did not break the module."
    - scenario: "import gtach.comm and construct a BluetoothDevice."
      expected_result: "Succeeds — the class is untouched."
    - scenario: "DeviceStore save_device, get_primary_device and get_all_devices."
      expected_result: "Unchanged behaviour."
    - scenario: "RWLock acquire/release, reader concurrency and writer exclusivity."
      expected_result: "Unchanged — change-1143427b's correction intact."
    - scenario: "A second ConfigManager construction with a different path."
      expected_result: "One WARNING, as change-d32ccc49 established."
  regression_scope:
    - "tests/utils/ and tests/comm/ — once populated per ai/task.md §8.2. tests/utils/test_rwlock.py exists and must still pass."
    - "On gtach.local: the application starts against the pre-upgrade config.yaml, which carries the saved_devices key."
    - "On gtach.local: an existing pairing still connects — DeviceStore is the store and is untouched."
    - "On gtach.local: re-pairing through the setup flow still persists the device."
  validation_criteria:
    - "python -m py_compile src/gtach/utils/config.py passes."
    - "pytest tests/ passes with no new failures."
    - "The three methods are absent."
    - "saved_devices appears nowhere in src/gtach."
    - "comm/models.py and comm/device_store.py are byte-identical to their current text."
    - "The RWLock class is byte-identical."
    - "ConfigManager.__new__ and __init__ are byte-identical."

implementation:
  implementation_steps:
    - step: "grep the whole repository — not only src/gtach — for the three method names, to confirm no consumer outside the package."
      owner: "Claude Code"
    - step: "Remove the three methods."
      owner: "Claude Code"
    - step: "Remove the saved_devices field and its two serialisation sites."
      owner: "Claude Code"
    - step: "Confirm BluetoothDevice is unreferenced in utils/config.py, then remove its import."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite, including tests/utils/test_rwlock.py."
      owner: "Claude Code"
    - step: "Deploy to gtach.local against the pre-upgrade configuration; confirm start, an existing pairing connecting, and a re-pair persisting."
      owner: "William Watson"
  rollback_procedure: >
    Single commit in one file. git revert restores the methods and the
    field. No configuration file is rewritten, so a revert requires no
    data migration — a config.yaml saved after this change simply lacks
    a key the restored from_dict defaults to an empty list.
  deployment_notes: >
    No visible change and no behavioural change: the deleted code has
    never executed. The on-target step is a confirmation that pairing
    still works, which exercises DeviceStore rather than anything this
    change touches. Ships in v0.4.0 (ai/task.md §8.5), separated from
    the v0.3.0 corrections because it is a large deletion.

verification:
  implemented_date: "2026-08-04"
  implemented_by: "Claude Code, per prompt-394c3bbb (commit 251ea74)"
  verification_date: "2026-08-05"
  verified_by: "Claude Code (development-platform script); William Watson (gtach.local)"
  test_results: >
    Delivered as specified. Development-platform script confirmed
    BluetoothConfig's field count, to_dict/from_dict behaviour on a
    legacy payload, and byte-identity of comm/models.py,
    comm/device_store.py, RWLock and the d32ccc49 singleton warning.
    Source re-check 2026-08-07 confirms all three retired methods,
    saved_devices and the BluetoothDevice import absent from
    utils/config.py. William confirmed GTach functions correctly on
    gtach.local.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-d32ccc49"
      relationship: "blocked_by"
    - change_ref: "change-1143427b"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-394c3bbb"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-394c3bbb, implementing the §7.5.4 retire decision recorded in ai/task.md §7.4.8."
      - "Recorded comm/models.py and comm/device_store.py as explicitly out of scope, correcting ai/task.md §7.4's file list; BluetoothDevice is live via DeviceStore and deleting it with the field it serves is the most likely way to break the build."
      - "Recorded that the saved_devices key in deployed configuration files is ignored on load rather than migrated, from_dict reading named keys."
      - "Verified and recorded that the deletion region does not overlap change-d32ccc49's singleton warning, discharging cross-check D2."
      - "Recorded that the retirement does not close §3.1, which change-1143427b handled."
      - "Specified the edit order — methods, then field and serialisation, then the import — so the import is removed only when provably unused."

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
| 1.0 | 2026-08-04 | Initial change document coupled to issue-394c3bbb. Specifies the deletion of the three `ConfigManager` device methods, `saved_devices` and its serialisation, with `comm/models.py` and `comm/device_store.py` explicitly out of scope. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation and verification recorded (commit 251ea74); source re-check confirms clean. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
