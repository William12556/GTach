Created: 2026 August 04

# Prompt: Retire the Second Device Store

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-394c3bbb"
  task_type: "implementation"
  source_ref: "change-394c3bbb"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-394c3bbb"
    change_iteration: 1

context:
  purpose: >
    ConfigManager carries a device-persistence path parallel to
    DeviceStore. It has no caller anywhere in the package, and its three
    methods read device.address where BluetoothDevice defines
    mac_address — so any call would raise AttributeError on its first
    line. The §7.5.4 decision recorded in ai/task.md §7.4.8 is to retire
    it. DeviceStore is the sole device store.
  integration: >
    One file: src/gtach/utils/config.py. Executor is Claude Code; AEL is
    not used.

    THE DANGEROUS PART, STATED FIRST. BluetoothDevice is defined in
    src/gtach/comm/models.py and is LIVE — comm/device_store.py imports
    it at line 27 and constructs it at 197 and 224, and comm/__init__.py
    re-exports it at line 15. utils/config.py imports it only to type
    the field you are deleting. Remove that IMPORT from
    utils/config.py; do NOT touch comm/models.py, the class, or
    comm/device_store.py. ai/task.md §7.4 lists both files among this
    task's "primary files"; that is a scope error, corrected in
    issue-394c3bbb, and following it literally breaks the surviving
    store.

    WHAT THIS DOES NOT DO. It does not close core review §3.1, the
    RWLock notification defect. That was change-1143427b, which is
    implemented and closed. Do not touch RWLock.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/utils/config.py."
    - "Do NOT modify src/gtach/comm/models.py. BluetoothDevice is live via DeviceStore."
    - "Do NOT modify src/gtach/comm/device_store.py. It is the surviving store."
    - "Do NOT modify the RWLock class. change-1143427b corrected it and this change does not close §3.1."
    - "Do NOT modify ConfigManager.__new__ or __init__. change-d32ccc49's singleton warning lives in __init__ and must survive byte-identical."
    - "Do NOT modify load_config, save_config, the validator, the transactional-write machinery or session archival."
    - "Do NOT remove any BluetoothConfig field other than saved_devices."
    - "Do NOT rewrite config/config.yaml or any deployed configuration file. A stale saved_devices key is inert."
    - "Do NOT 'fix' device.address to device.mac_address. The decision is to retire, not to correct."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Delete ConfigManager's three device-persistence methods,
    BluetoothConfig.saved_devices, its two serialisation sites, and the
    BluetoothDevice import that served them.
  requirements:
    functional:
      - "ConfigManager has no get_device_by_address, add_or_update_device or remove_device."
      - "BluetoothConfig has no saved_devices field."
      - "BluetoothConfig.to_dict emits no saved_devices key."
      - "BluetoothConfig.from_dict ignores a saved_devices key without raising."
      - "A configuration file carrying populated saved_devices entries loads without error."
      - "The string 'saved_devices' appears nowhere in src/gtach."
      - "No reference to device.address remains in src/gtach."
      - "utils/config.py imports successfully with the BluetoothDevice import removed."
      - "comm/models.py, comm/device_store.py, RWLock, ConfigManager.__new__ and ConfigManager.__init__ are unchanged."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Negligible. Deleted code never executed"
      metric: "time"

design:
  architecture: >
    One concern, one implementation. The store that runs stays; the
    store that has never run goes. Data written by the retired path is
    tolerated on read and not migrated, because a loader that reads
    named keys is already indifferent to extra ones.
  components:
    - name: "ConfigManager"
      type: "class"
      purpose: "Lose three methods."
      logic:
        - "Delete get_device_by_address, add_or_update_device and remove_device."
        - "They are contiguous, between get_home_path and generate_session_id. Read the file to confirm the boundaries; do not cut by line number alone."
    - name: "BluetoothConfig"
      type: "dataclass"
      purpose: "Lose one field and its serialisation."
      logic:
        - "Delete the saved_devices field."
        - "Delete its entry from to_dict."
        - "Delete its construction and its keyword argument from from_dict."
        - "Leave the other fourteen fields untouched in all three places."
  dependencies:
    internal:
      - "comm/device_store.py — the surviving store. Read-only."
      - "comm/models.py — defines the live BluetoothDevice. Read-only."
      - "change-d32ccc49 — its singleton warning is in __init__, outside the deleted region."
    external: []

error_handling:
  strategy: >
    Unchanged. This change removes code rather than adding behaviour.
    The only error-handling consideration is that from_dict must remain
    tolerant of a key it no longer reads, which it is by construction —
    it reads named keys rather than iterating.
  exceptions:
    - exception: "None added or removed."
      condition: "n/a"
      handling: "n/a"
  logging:
    level: "None added"
    format: "n/a"

testing:
  unit_tests:
    - scenario: "hasattr(ConfigManager, 'get_device_by_address'), and the same for the other two."
      expected: "False for all three."
    - scenario: "ConfigManager's public method set compared against the pre-change set."
      expected: "Differs by exactly those three names."
    - scenario: "The field list of BluetoothConfig."
      expected: "Fourteen fields; saved_devices absent."
    - scenario: "BluetoothConfig().to_dict() keys."
      expected: "No saved_devices; auto_connect, last_device, scan_duration, retry_limit, retry_delay, timeout, bleak_timeout, service_discovery_timeout, notification_timeout, keepalive_interval, device_filter, elm327_timeout, elm327_retries and elm327_init_delay all present."
    - scenario: "BluetoothConfig.from_dict on a dict carrying saved_devices with three device dicts."
      expected: "Constructs; no exception; the other fields read correctly."
    - scenario: "from_dict on a dict with no saved_devices."
      expected: "Constructs."
    - scenario: "from_dict on {}."
      expected: "Defaults, as today."
    - scenario: "A round trip: from_dict(to_dict(BluetoothConfig()))."
      expected: "Equal to the original."
    - scenario: "load_config against a config.yaml fixture carrying populated bluetooth.saved_devices."
      expected: "No exception; the bluetooth settings load."
    - scenario: "load_config then save_config on that fixture."
      expected: "No exception; the written file has no saved_devices key and every other setting survives."
    - scenario: "import gtach.utils.config."
      expected: "Succeeds. This is the test that catches an over-eager import removal."
    - scenario: "from gtach.comm import BluetoothDevice; construct one."
      expected: "Succeeds; mac_address present, address absent."
    - scenario: "DeviceStore save_device, get_primary_device, get_all_devices, get_device_by_mac and remove_device."
      expected: "Unchanged behaviour, exercised against a temporary devices.yaml."
    - scenario: "tests/utils/test_rwlock.py."
      expected: "Passes unchanged."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager('/tmp/b.yaml')."
      expected: "One WARNING, as change-d32ccc49 established."
  edge_cases:
    - "The BluetoothDevice import at utils/config.py:37-45 is a try/except over two package layouts. Remove the whole construct, not one branch, and only after confirming the name is unreferenced elsewhere in the file."
    - "get_home_path immediately precedes the deleted block and generate_session_id follows it. Cutting one line too far in either direction removes a live method; verify both survive."
    - "A deployed devices.yaml is DeviceStore's file and is unrelated to this change. Do not confuse it with config.yaml."
    - "config/config.yaml in the repository carries bluetooth.saved_devices: []. Leave it. It is inert after this change and disappears at the next save."
  validation:
    - "grep -r saved_devices src/gtach returns nothing."
    - "grep -r 'device.address' src/gtach returns nothing."
    - "git diff --stat shows exactly one file changed."

deliverable:
  format_requirements:
    - "Edit the one file in place. Create no new file."
    - "Four edits, in the order given, so the import is removed only when provably unused."
  files:
    - path: "src/gtach/utils/config.py"
      content: |
        BEFORE STARTING: grep the whole repository — not just src/gtach —
        for get_device_by_address, add_or_update_device and
        remove_device. Note that comm/device_store.py:236 defines its
        OWN remove_device(mac_address) with real callers at
        display/setup.py:693 and display/manager.py:1341. That is a
        different method on a different class and must survive. If the
        grep finds any caller of the ConfigManager versions, STOP and
        report.

        EDIT 1 — remove the three methods.

        They occupy utils/config.py:1440-1501, contiguous, between
        get_home_path (1436-1438) and generate_session_id (1503).
        Read the surrounding lines and confirm both neighbours survive.

        Delete:
          - get_device_by_address (1440-1457)
          - add_or_update_device (1459-1480)
          - remove_device (1482-1501)

        EDIT 2 — remove the field.

        At utils/config.py:435, inside BluetoothConfig:

            saved_devices: List[BluetoothDevice] = field(default_factory=list)

        Delete that line. Leave every other field in the dataclass.

        EDIT 3 — remove the serialisation.

        In to_dict, at utils/config.py:462, delete:

            "saved_devices": [device.to_dict() for device in self.saved_devices],

        In from_dict, at utils/config.py:485-492, delete the extraction
        block:

            # Extract and convert the saved devices
            saved_devices = []
            for device_data in data.get("saved_devices", []):
                if isinstance(device_data, dict):
                    saved_devices.append(BluetoothDevice.from_dict(device_data))

        and the keyword argument in the return:

            saved_devices=saved_devices,

        Keep the return's other arguments exactly as they are. from_dict
        reads named keys, so a saved_devices key in an existing file is
        simply not read — which is the whole migration.

        EDIT 4 — remove the import, LAST.

        First confirm BluetoothDevice is now unreferenced anywhere in
        utils/config.py. Then remove the import construct at
        utils/config.py:37-45:

            # Import the BluetoothDevice class from the comm module
            try:
                from ..comm.models import BluetoothDevice
            except ImportError:
                ...
                from comm.models import BluetoothDevice

        Remove the whole try/except, both branches and the comment.

        DO NOT touch src/gtach/comm/models.py. BluetoothDevice remains
        defined there and is used by comm/device_store.py and
        re-exported by comm/__init__.py. Removing the import from THIS
        file is correct; removing the class is not.

        If List is now unused in this file, leave the typing import
        alone unless the compile check flags it — other fields
        (device_filter at 452) still use it.

success_criteria:
  - "python -m py_compile src/gtach/utils/config.py passes."
  - "python -c 'import gtach.utils.config' succeeds."
  - "python -c 'from gtach.comm import BluetoothDevice; BluetoothDevice(name=\"x\", mac_address=\"AA:BB\")' succeeds."
  - "pytest tests/ passes with no new failures, including tests/utils/test_rwlock.py."
  - "ConfigManager has no get_device_by_address, add_or_update_device or remove_device."
  - "BluetoothConfig has no saved_devices field and to_dict emits no such key."
  - "from_dict on a dict carrying saved_devices constructs without raising."
  - "grep -r saved_devices src/gtach returns nothing."
  - "grep -r 'device.address' src/gtach returns nothing."
  - "src/gtach/comm/models.py is byte-identical to its current text."
  - "src/gtach/comm/device_store.py is byte-identical to its current text."
  - "The RWLock class in utils/config.py is byte-identical to its current text."
  - "ConfigManager.__new__ and ConfigManager.__init__ are byte-identical to their current text."
  - "ConfigManager.get_home_path and ConfigManager.generate_session_id are byte-identical to their current text."
  - "Every BluetoothConfig field other than saved_devices survives in the dataclass, to_dict and from_dict."
  - "No file other than src/gtach/utils/config.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "config"
        path: "src/gtach/utils/config.py"
      - name: "models"
        path: "src/gtach/comm/models.py"
      - name: "device_store"
        path: "src/gtach/comm/device_store.py"
    classes:
      - name: "ConfigManager"
        module: "gtach.utils.config"
      - name: "BluetoothConfig"
        module: "gtach.utils.config"
      - name: "BluetoothDevice"
        module: "gtach.comm.models"
      - name: "DeviceStore"
        module: "gtach.comm.device_store"
    functions:
      - name: "to_dict"
        module: "gtach.utils.config"
        signature: "to_dict(self) -> Dict[str, Any]"
      - name: "from_dict"
        module: "gtach.utils.config"
        signature: "from_dict(cls, data: Dict[str, Any]) -> 'BluetoothConfig'"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-394c3bbb-config-device-persistence-retirement.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  This is a deletion, so the risk is entirely in cutting too much. Three
  specific hazards:

    - deleting BluetoothDevice or its module along with the field it
      typed. The class is live via DeviceStore; only the IMPORT in
      utils/config.py goes.
    - deleting comm/device_store.py's own remove_device, which shares a
      name with one of the three and has real callers.
    - cutting one line past the block's boundaries and taking
      get_home_path or generate_session_id with it.

  The deleted code has never executed — its first line would raise
  AttributeError — so nothing observable changes. The on-target step is
  a confirmation that pairing still works, which exercises DeviceStore,
  the store this change does not touch.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-394c3bbb. |

---

Copyright (c) 2026 William Watson. MIT License.
