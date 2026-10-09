Created: 2026 October 09

# Test: ConfigStore Save Keeps Unknown Keys

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-ae65fa10"
  title: "Verify ConfigStore.save preserves unknown keys read from the file at save time"
  date: "2026-10-09"
  author: "William Watson"
  status: "passed"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-ae65fa10"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "ConfigStore.save, ConfigStore.load, _unknown_keys (src/gtach/utils/config.py)"
  design_refs: []
  change_refs:
    - "change-ae65fa10"
  requirement_refs:
    - "issue-ae65fa10"

scope:
  description: >
    Verifies that save takes unknown keys from the current file, falls
    back to the retained set when the file is missing, unreadable,
    invalid YAML or not a mapping, logs a WARNING on a read failure, and
    still writes the known keys.
  test_objectives:
    - "Confirm a save without a prior load keeps an unknown key."
    - "Confirm a key appended to the file after load survives a save."
    - "Confirm a missing file produces exactly CONFIG_KEYS."
    - "Confirm invalid YAML logs a WARNING, returns True and writes the known keys."
    - "Confirm a non-mapping file contributes no unknown keys."
    - "Confirm pre-existing round-trip behaviour is unchanged."
  in_scope:
    - "src/gtach/utils/config.py — _unknown_keys, load, save"
  out_scope:
    - "load() validation rules and CONFIG_KEYS — unchanged"
    - "Atomic write sequence — unchanged"
  dependencies:
    - "Development venv with pip install -e .[dev]"
    - "TC-007 only: root@gtach.local"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development); Debian Linux on Raspberry Pi Zero 2W (TC-007)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest"
  test_data_location: "tmp_path YAML files"

test_cases:
  - case_id: "TC-001"
    description: "Save without load keeps an unknown key"
    category: "positive"
    preconditions:
      - "File contains foo: 1 and known keys; no load() called"
    test_steps:
      - step: "1"
        action: "Call save()"
      - step: "2"
        action: "Read the file"
    inputs:
      - parameter: "unknown key"
        value: "foo: 1"
        type: "YAML"
    expected_outputs:
      - field: "file contents"
        expected_value: "foo: 1 present"
        validation: "yaml.safe_load"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_config_store.py::TestSave::test_save_without_load_keeps_unknown_key"
      pass_fail_criteria: "Key present"
    defects: []

  - case_id: "TC-002"
    description: "Key added to the file after load is kept"
    category: "positive"
    preconditions:
      - "load() called; a new key then appended to the file externally"
    test_steps:
      - step: "1"
        action: "Call save()"
    inputs: []
    expected_outputs:
      - field: "file contents"
        expected_value: "Appended key present"
        validation: "yaml.safe_load"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_config_store.py::TestSave::test_key_added_after_load_is_kept"
      pass_fail_criteria: "Key present"
    defects: []

  - case_id: "TC-003"
    description: "Missing file writes known keys only"
    category: "boundary"
    preconditions:
      - "No config file exists"
    test_steps:
      - step: "1"
        action: "Call save()"
    inputs: []
    expected_outputs:
      - field: "written keys"
        expected_value: "Exactly CONFIG_KEYS"
        validation: "Set equality"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_config_store.py::TestSave::test_missing_file_writes_known_keys_only"
      pass_fail_criteria: "Set equality holds"
    defects: []

  - case_id: "TC-004"
    description: "Invalid YAML warns and saves"
    category: "negative"
    preconditions:
      - "File contains invalid YAML"
    test_steps:
      - step: "1"
        action: "Call save() with caplog capturing"
    inputs: []
    expected_outputs:
      - field: "return"
        expected_value: "True"
        validation: "Equality"
      - field: "log"
        expected_value: "One WARNING record"
        validation: "caplog"
      - field: "file contents"
        expected_value: "Valid YAML with the known keys"
        validation: "yaml.safe_load"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_config_store.py::TestSave::test_invalid_yaml_warns_and_saves"
      pass_fail_criteria: "All three as expected"
    defects: []

  - case_id: "TC-005"
    description: "A YAML list contributes no unknown keys"
    category: "edge"
    preconditions:
      - "File contains a YAML list"
    test_steps:
      - step: "1"
        action: "Call save()"
    inputs: []
    expected_outputs:
      - field: "written keys"
        expected_value: "Known keys only"
        validation: "Set equality"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_config_store.py::TestSave::test_list_file_gives_no_unknown_keys"
      pass_fail_criteria: "No extra keys"
    defects: []

  - case_id: "TC-006"
    description: "Pre-existing round-trip behaviour unchanged"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Run TestSave::test_round_trip_keeps_unknown_key and ::test_only_unknown_keys_preserved, and the TestLoad class"
    inputs: []
    expected_outputs:
      - field: "result"
        expected_value: "All pass"
        validation: "pytest exit 0"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "TestSave::test_round_trip_keeps_unknown_key, ::test_only_unknown_keys_preserved and all TestLoad cases PASSED"
      pass_fail_criteria: "All pass"
    defects: []

  - case_id: "TC-007"
    description: "Optional on-device: unknown key survives a palette change"
    category: "positive"
    preconditions:
      - "Optional; branch deployed to root@gtach.local"
    test_steps:
      - step: "1"
        action: "Add an unknown key to /opt/gtach/config.yaml"
      - step: "2"
        action: "Change the palette on the OPTIONS screen"
      - step: "3"
        action: "Inspect the file"
    inputs: []
    expected_outputs:
      - field: "config.yaml"
        expected_value: "Unknown key still present"
        validation: "Inspection"
    postconditions:
      - "Remove the test key afterwards"
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local, guided by Claude)"
      actual_result: "test_marker: 1 appended over SSH; palette toggled day -> night -> day by long press on the RADIAL gauge (the palette is not set from OPTIONS; step 2 wording corrected here); test_marker: 1 present after both saves, written first in the file; key removed afterwards"
      pass_fail_criteria: "Key retained"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-ae65fa10"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007"]
  code_coverage:
    target: "All branches of save's read-and-fallback logic"
    achieved: ""
  untested_areas:
    - component: "Empty file (safe_load returns None) falls back to the retained set"
      reason: "Specified behaviour per the change report §6, but no pytest case exists. Candidate addition; not generated, pending agreement"
    - component: "Unreadable file (permission error) path"
      reason: "No pytest case exists; shares the fallback branch with TC-004"
    - component: "Concurrent load and save"
      reason: "Lock covers only the _unknown update; not specified by the change"

test_execution_summary:
  total_cases: 7
  passed: 7
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: "100%"
  execution_time: "Targeted pytest run 26.8 s (137 passed); on-device check 09:45-09:47"
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: "2026-10-09"
  verified_by: "William Watson"
  verification_notes: "Mac: pytest 9.1.1, Python 3.11.14. Pi: GTach 0.4.10. The untested areas listed under coverage remain untested."
  sign_off: "Approved"

traceability:
  requirements:
    - requirement_ref: "issue-ae65fa10"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005"]
  designs: []
  changes:
    - change_ref: "change-ae65fa10"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007"]

notes: >
  Generated pytest file: tests/test_config_store.py (five cases added to
  TestSave), per P06 §1.7.3. Written during implementation; recorded here
  retrospectively. The change report states 3 of the 5 new cases fail
  against the pre-change source (TC-001, TC-002 and one other); this
  document does not re-establish which, and that claim is unverified.
  Run: pytest tests/test_config_store.py -v.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-ae65fa10."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Executed on Mac and gtach.local; results recorded per case; TC-007 step wording corrected in its result (palette is toggled by long press); status passed."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t05_test"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial test document for change-ae65fa10. |
| 1.1 | 2026-10-09 | Executed on Mac and gtach.local; results recorded per case; status passed. |

---

Copyright (c) 2026 William Watson. MIT License.
