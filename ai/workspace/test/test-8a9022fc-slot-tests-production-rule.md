Created: 2026 October 09

# Test: Slot Tests Use the Production Rule

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-8a9022fc"
  title: "Verify the slot-contents tests exercise the production selection rule, by mutation"
  date: "2026-10-09"
  author: "William Watson"
  status: "planned"
  type: "regression"
  priority: "medium"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-8a9022fc"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "tests/test_device_list_focus.py::TestSlotContents (four list tests)"
  design_refs:
    - "479b2e51 (Device List focused-index carousel)"
  change_refs:
    - "change-8a9022fc"
  requirement_refs:
    - "issue-8a9022fc"

scope:
  description: >
    The change altered tests only. This document verifies that the
    rewritten tests pass against production code and fail when the
    production selection rule in SetupDisplayManager._render_device_list_screen
    is mutated, which shows they no longer re-implement the rule.
  test_objectives:
    - "Confirm the four rewritten tests pass against unmodified source."
    - "Confirm reversing the slot offsets fails three of the four tests."
    - "Confirm all-zero offsets fail all four tests."
    - "Confirm the _slots helper is removed and no file under src/ changed."
  in_scope:
    - "tests/test_device_list_focus.py — _RecordingRenderer, _Render, the four TestSlotContents list tests"
  out_scope:
    - "Other test classes in the file — unchanged by constraint"
  dependencies:
    - "Development venv with pip install -e .[dev]"
    - "SDL_VIDEODRIVER=dummy"

test_environment:
  python_version: "3.9+ (development)"
  os: "macOS (development)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
    - name: "pygame"
      version: "SDL_VIDEODRIVER=dummy"
  test_framework: "pytest"
  test_data_location: "Inline device lists"

test_cases:
  - case_id: "TC-001"
    description: "Rewritten slot-contents tests pass against production code"
    category: "positive"
    preconditions:
      - "src/gtach/display/setup.py unmodified"
    test_steps:
      - step: "1"
        action: "pytest tests/test_device_list_focus.py::TestSlotContents -v"
    inputs: []
    expected_outputs:
      - field: "test_one_device_leaves_both_neighbours_empty"
        expected_value: "Pass"
        validation: "pytest"
      - field: "test_two_devices_focus_zero_fills_the_bottom_slot"
        expected_value: "Pass"
        validation: "pytest"
      - field: "test_two_devices_focus_one_fills_the_top_slot"
        expected_value: "Pass"
        validation: "pytest"
      - field: "test_five_devices_mid_list_fills_all_three"
        expected_value: "Pass"
        validation: "pytest"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "All four pass"
    defects: []

  - case_id: "TC-002"
    description: "Reversed offsets are detected"
    category: "negative"
    preconditions:
      - "Working tree clean"
    test_steps:
      - step: "1"
        action: "In setup.py change zip(layout_data, (-1, 0, 1)) to (1, 0, -1)"
      - step: "2"
        action: "PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider the four tests, after removing __pycache__ under src/gtach/display"
      - step: "3"
        action: "git checkout src/gtach/display/setup.py"
    inputs: []
    expected_outputs:
      - field: "failures"
        expected_value: "3 of 4; test_one_device_leaves_both_neighbours_empty passes"
        validation: "pytest summary"
    postconditions:
      - "The one-device case is symmetric under reversal; its pass here is expected"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Exactly the three asymmetric tests fail"
    defects: []

  - case_id: "TC-003"
    description: "All-zero offsets are detected"
    category: "negative"
    preconditions:
      - "Working tree clean"
    test_steps:
      - step: "1"
        action: "Change the offsets to (0, 0, 0)"
      - step: "2"
        action: "Run the four tests as in TC-002"
      - step: "3"
        action: "git checkout src/gtach/display/setup.py"
    inputs: []
    expected_outputs:
      - field: "failures"
        expected_value: "4 of 4"
        validation: "pytest summary"
    postconditions:
      - "Re-run TC-001 to confirm the restore (clear __pycache__ first)"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "All four fail"
    defects: []

  - case_id: "TC-004"
    description: "Re-implementation removed and production source untouched"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -n 'def _slots' tests/test_device_list_focus.py"
      - step: "2"
        action: "git show --stat d4e11e3"
    inputs: []
    expected_outputs:
      - field: "def _slots"
        expected_value: "No match"
        validation: "grep exit 1"
      - field: "files in d4e11e3"
        expected_value: "Only tests/ files"
        validation: "Inspection"
    postconditions:
      - "grep '_slots' without 'def' also matches two unrelated test names; use the narrower pattern"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Helper absent; no src/ change"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-8a9022fc"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004"]
  code_coverage:
    target: "Not applicable (test-only change)"
    achieved: ""
  untested_areas:
    - component: "Other mutations of the selection rule (e.g. off-by-one in the focus index)"
      reason: "Not required by the change; two mutations were judged sufficient"

test_execution_summary:
  total_cases: 4
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""
  execution_time: ""
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""

traceability:
  requirements:
    - requirement_ref: "issue-8a9022fc"
      test_cases: ["TC-002", "TC-003"]
  designs:
    - design_ref: "479b2e51"
      test_cases: ["TC-001"]
  changes:
    - change_ref: "change-8a9022fc"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004"]

notes: >
  The pytest file under test is tests/test_device_list_focus.py. TC-002
  and TC-003 are manual mutation checks; they temporarily edit src/ and
  must be reverted with git checkout before anything is committed. Clear
  __pycache__ and set PYTHONDONTWRITEBYTECODE=1: the implementation report
  records a false restore caused by a stale .pyc with identical size and
  mtime second.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-8a9022fc."

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
| 1.0 | 2026-10-09 | Initial test document for change-8a9022fc. |

---

Copyright (c) 2026 William Watson. MIT License.
