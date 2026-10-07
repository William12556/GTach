Created: 2026 October 07

# Prompt: Shared, Locked DeviceStore Under GTACH_HOME

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-453f0a80"
  task_type: "refactor"
  source_ref: "change-453f0a80"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-453f0a80"
    change_iteration: 1

context:
  purpose: >
    Replace independent, unlocked DeviceStore instances with one shared,
    locked instance at gtach_home()/config/devices.yaml, with durable
    writes.
  integration: >
    comm/device_store.py and its call sites; config/devices.yaml;
    tests. Implement after prompt-5fbff586.
  knowledge_references:
    - "ai/workspace/issues/issue-453f0a80-device-store-sharing.md"
    - "ai/workspace/change/change-453f0a80-device-store-sharing.md"
    - "CLAUDE.md §4 rule 8"
  constraints:
    - "CRITICAL: on the Pi the resolved path must remain /opt/gtach/config/devices.yaml (gtach_home() default) and the file format unchanged."
    - "No call-outs under the store lock (CLAUDE.md rule 8); public methods must not call each other while holding the lock (threading.Lock is not reentrant)."
    - "get_device_store must construct through the module-level name DeviceStore so tests that patch it keep working."
    - "Do not change the devices.yaml schema or the BluetoothDevice model."
    - "Every logger .error/.critical in a broad handler passes exc_info=True."
    - "Do not modify src/gtach/display/manager_backup.py or setup_original_backup.py."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to F of change-453f0a80."
  requirements:
    functional:
      - "get_device_store() returns one shared instance until reset_device_store()."
      - "All public DeviceStore methods are safe under concurrent use."
      - "Saves flush and fsync the temporary file before os.replace."
      - "No production code constructs DeviceStore directly."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Module-level shared instance with an internal lock."
  components:
    - name: "EDITS A to C — device_store.py"
      type: "module"
      purpose: "Lock, durable save, accessor."
      logic:
        - "__init__(self, config_path: Optional[str] = None): resolve the default from gtach_home(); create self._lock before loading."
        - "Wrap each public method body in `with self._lock:`; where a public method used another public method internally, call an unlocked private helper instead."
        - "_save_config: inside the `with open(tmp_path, 'w') as f:` block, after yaml.dump: f.flush(); os.fsync(f.fileno()). Then os.replace."
        - "Add _shared, _shared_lock, get_device_store(), reset_device_store() with docstrings."
    - name: "EDIT D — call sites"
      type: "module"
      purpose: "Use the accessor."
      logic:
        - "Replace each `DeviceStore()` in app.py, comm/transport.py, comm/sim_bluetooth.py, display/manager.py, display/setup.py, display/setup_components/bluetooth/interface.py with `get_device_store()`, adjusting imports (keep inline imports inline)."
    - name: "EDITS E, F — repository and tests"
      type: "module"
      purpose: "No tracked runtime file; test isolation."
      logic:
        - "`git rm config/devices.yaml`."
        - "tests/conftest.py: autouse fixture calling gtach.comm.device_store.reset_device_store() after each test (import inside the fixture)."
        - "Add tests/test_device_store_shared.py per change testing_requirements; adjust existing tests only where they depended on per-call construction."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged; save failures return False and log with exc_info=True."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-453f0a80 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "YAML unavailable: in-memory fallback still works under the lock."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit in place; git rm the seed file."
  files:
    - path: "src/gtach/comm/device_store.py"
      content: "EDITS A to C"
    - path: "src/gtach/app.py, src/gtach/comm/transport.py, src/gtach/comm/sim_bluetooth.py, src/gtach/display/manager.py, src/gtach/display/setup.py, src/gtach/display/setup_components/bluetooth/interface.py"
      content: "EDIT D"
    - path: "config/devices.yaml"
      content: "removed (EDIT E)"
    - path: "tests/conftest.py, tests/test_device_store_shared.py"
      content: "EDIT F"

success_criteria:
  - "grep -rn 'DeviceStore()' src (backups excluded) shows only the construction inside get_device_store."
  - "DeviceStore has self._lock and every public method acquires it."
  - "_save_config calls os.fsync before os.replace."
  - "config/devices.yaml is removed from the repository."
  - "After a full pytest run, `git status --porcelain` shows nothing outside the commit."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "device_store"
        path: "src/gtach/comm/device_store.py"
    classes:
      - name: "DeviceStore"
        module: "gtach.comm.device_store"
    functions:
      - name: "get_device_store"
        module: "gtach.comm.device_store"
        signature: "() -> DeviceStore"
      - name: "reset_device_store"
        module: "gtach.comm.device_store"
        signature: "() -> None"
    constants: []

notes: "Human verification on the Pi: after the upgrade the paired adapter is still used without re-pairing."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-453f0a80 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-07 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
