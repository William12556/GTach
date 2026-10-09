Created: 2026 October 09

# Test: mypy Strict Clean

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-ac11505d"
  title: "Verify mypy strict reports zero errors with no relaxed settings and no runtime change"
  date: "2026-10-09"
  author: "William Watson"
  status: "planned"
  type: "regression"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-ac11505d"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "src/gtach (all subpackages); pyproject.toml [tool.mypy] and [project.optional-dependencies].dev"
  design_refs: []
  change_refs:
    - "change-ac11505d"
  requirement_refs:
    - "issue-ac11505d"

scope:
  description: >
    The change is annotation-only by intent, with a small set of
    runtime-identical edits. Verification is a clean strict type check
    under unchanged settings, a disciplined suppression set, an unchanged
    test suite, imports on the oldest supported interpreter, and normal
    use on the device, including the real hyperpixel2r touch path.
  test_objectives:
    - "Confirm mypy src/ reports no issues."
    - "Confirm no [tool.mypy] setting was relaxed and only stub packages were added."
    - "Confirm every type: ignore carries an error code and the issue-ac11505d tag, and there are exactly 20."
    - "Confirm the suite passes and no test file was changed by the five commits."
    - "Confirm all gtach modules import on the target interpreter."
    - "Confirm normal use and real touch on the device."
  in_scope:
    - "Commits e5ceb62, dae7d83, 5ebd823, 954fb6d, 1a2ebee"
  out_scope:
    - "Fixing the behavioural defects found (batch report §5.0) — suppressed by design, for follow-up issues"
  dependencies:
    - "Development venv with pip install -e .[dev] (installs types-PyYAML, types-pyserial, types-psutil)"
    - "TC-005 and TC-007: root@gtach.local"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development); Debian Linux on Raspberry Pi Zero 2W (TC-005, TC-007)"
  libraries:
    - name: "mypy"
      version: "As pinned in [dev]"
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "mypy; pytest; shell"
  test_data_location: "None"

test_cases:
  - case_id: "TC-001"
    description: "Strict type check is clean"
    category: "positive"
    preconditions:
      - "[dev] extras freshly installed"
    test_steps:
      - step: "1"
        action: "mypy src/"
    inputs: []
    expected_outputs:
      - field: "output"
        expected_value: "Success: no issues found in 59 source files"
        validation: "Exact match on 'Success: no issues found'"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Zero errors"
    defects: []

  - case_id: "TC-002"
    description: "No mypy setting relaxed"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "git diff 00c9129 1a2ebee -- pyproject.toml"
      - step: "2"
        action: "grep -n 'ignore_errors' pyproject.toml"
    inputs: []
    expected_outputs:
      - field: "pyproject diff"
        expected_value: "Only types-PyYAML, types-pyserial, types-psutil added to [dev]"
        validation: "Inspection"
      - field: "ignore_errors"
        expected_value: "No match"
        validation: "grep exit 1"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No relaxation"
    defects: []

  - case_id: "TC-003"
    description: "Suppressions are coded and tagged"
    category: "boundary"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -rn 'type: ignore' src/gtach | wc -l"
      - step: "2"
        action: "grep -rn 'type: ignore' src/gtach | grep -v 'type: ignore\\[[a-z-, ]*\\]  # TODO: issue-ac11505d'"
    inputs: []
    expected_outputs:
      - field: "count"
        expected_value: "20"
        validation: "Equality"
      - field: "untagged or uncoded"
        expected_value: "None"
        validation: "grep exit 1"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "20, all conforming"
    defects: []

  - case_id: "TC-004"
    description: "Suite passes; no test file changed"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "git diff --stat 00c9129 1a2ebee -- tests"
      - step: "2"
        action: "pytest tests/"
    inputs: []
    expected_outputs:
      - field: "tests diff"
        expected_value: "Empty"
        validation: "Inspection"
      - field: "pytest"
        expected_value: "All pass (561 per the report)"
        validation: "pytest summary"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No test change; all pass"
    defects: []

  - case_id: "TC-005"
    description: "All modules import on the target interpreter"
    category: "positive"
    preconditions:
      - "Branch deployed to root@gtach.local"
    test_steps:
      - step: "1"
        action: "ssh root@gtach.local \"SDL_VIDEODRIVER=dummy /opt/gtach/venv/bin/python3 -c 'import pkgutil, importlib, gtach; [importlib.import_module(m.name) for m in pkgutil.walk_packages(gtach.__path__, \\\"gtach.\\\")]'\""
    inputs: []
    expected_outputs:
      - field: "exit code"
        expected_value: "0"
        validation: "Shell return code"
    postconditions:
      - "The report's 3.9.25 import check ran in a throwaway venv in the implementation session; this case repeats it on the authoritative interpreter"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No import error"
    defects: []

  - case_id: "TC-006"
    description: "Import and simtcp smoke run"
    category: "positive"
    preconditions:
      - "Development machine"
    test_steps:
      - step: "1"
        action: "SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 python -m gtach --transport simtcp"
    inputs: []
    expected_outputs:
      - field: "exit"
        expected_value: "124 (timeout); no traceback other than the environmental framebuffer OSError"
        validation: "Output inspection"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Run reaches the timeout cleanly"
    defects: []

  - case_id: "TC-007"
    description: "On-device normal use and real touch"
    category: "positive"
    preconditions:
      - "Deployed with bin/deploy.sh"
    test_steps:
      - step: "1"
        action: "Observe service start, splash, gauge with live RPM"
      - step: "2"
        action: "Exercise OPTIONS, taps and swipes, the DISCONNECTED screen with retry arc and Reset, and setup with pairing"
      - step: "3"
        action: "Pull logs; inspect error.log"
    inputs: []
    expected_outputs:
      - field: "behaviour"
        expected_value: "Unchanged from before the change; taps register via hyperpixel2r"
        validation: "Observation"
      - field: "error.log"
        expected_value: "No TypeError, AttributeError or AssertionError introduced"
        validation: "Log inspection"
    postconditions:
      - "Drag AttributeError from TouchAction.DRAG (batch report §5.0 item 1) is pre-existing and expected"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Normal use; no new errors"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-ac11505d"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007"]
  code_coverage:
    target: "Not applicable (type annotations)"
    achieved: ""
  untested_areas:
    - component: "Runtime-identical edits (send_command split returns, Popen asserts, typing.cast sites)"
      reason: "Covered only by the existing suite and TC-007; no case targets them individually. The Popen asserts run only on the real Bluetooth discovery path"
    - component: "Six behavioural defects suppressed with TODOs"
      reason: "Out of scope; follow-up issues per batch report §8.0"

test_execution_summary:
  total_cases: 7
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
    - requirement_ref: "issue-ac11505d"
      test_cases: ["TC-001", "TC-002", "TC-003"]
  designs: []
  changes:
    - change_ref: "change-ac11505d"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007"]

notes: >
  No pytest file was generated for this change. 00c9129 (change-e215a184)
  is the parent of the first ac11505d commit and is used as the baseline
  in TC-002 and TC-004. The report notes mypy checks with 3.10+ semantics
  because python_version = "3.9" is unsupported by the installed mypy;
  TC-005 compensates by importing on the device interpreter.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-ac11505d."

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
| 1.0 | 2026-10-09 | Initial test document for change-ac11505d. |

---

Copyright (c) 2026 William Watson. MIT License.
