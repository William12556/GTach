Created: 2026 October 09

# Test: Residual Dead Code Removed

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-273ca048"
  title: "Verify removal of dead-code groups D1-D8 left no reference and no behaviour change"
  date: "2026-10-09"
  author: "William Watson"
  status: "passed"
  type: "regression"
  priority: "medium"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-273ca048"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "Groups D1-D8 across display, performance, typography, touch, splash, setup models and tests/conftest.py"
  design_refs: []
  change_refs:
    - "change-273ca048"
  requirement_refs:
    - "issue-273ca048"

scope:
  description: >
    A removal change has no new behaviour to assert. Verification is
    therefore absence of references, an unchanged suite, unchanged enum
    values for the remaining SetupScreen members, a clean import and
    smoke run, and normal use on the device.
  test_objectives:
    - "Confirm no removed name is referenced in src, tests or bin."
    - "Confirm the full suite passes with no test deleted or adjusted."
    - "Confirm the remaining SetupScreen members keep their values."
    - "Confirm import and an 8 s simtcp run produce no ImportError or AttributeError."
    - "Confirm normal use on the device."
  in_scope:
    - "Files listed in report-273ca048 §2"
  out_scope:
    - "Further dead code listed in report-273ca048 §6 — deliberately kept"
  dependencies:
    - "Development venv with pip install -e .[dev]"
    - "TC-005 only: root@gtach.local"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development); Debian Linux on Raspberry Pi Zero 2W (TC-005)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest; shell (grep, git)"
  test_data_location: "None"

test_cases:
  - case_id: "TC-001"
    description: "No reference to any removed name"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -rnE 'ACQUIRE_TIMEOUT|initialize_performance_manager|cleanup_performance_manager|ButtonSize|ButtonState|get_touch_interface_info|\\bsimulate_touch\\b|simulate_touch_event|normalize_coordinates|get_circular_safe_area|clear_layout_cache|_circular_layout_cache|get_performance_report|SetupScreen\\.(DEVICE_MANAGEMENT|CONFIRMATION)' src tests bin"
    inputs: []
    expected_outputs:
      - field: "matches"
        expected_value: "None"
        validation: "grep exit 1"
    postconditions:
      - "normalize_coordinates also covers denormalize_coordinates"
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "No source match. Matches only in stale compiled files under __pycache__ (Python 3.10/3.11 bytecode, including setup_original_backup), which are not source"
      pass_fail_criteria: "No match"
    defects: []

  - case_id: "TC-002"
    description: "Full suite passes; no test removed by this change"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "git show --stat bf03008 -- tests"
      - step: "2"
        action: "pytest tests/"
    inputs: []
    expected_outputs:
      - field: "tests changed in bf03008"
        expected_value: "tests/conftest.py only (ACQUIRE_TIMEOUT)"
        validation: "Inspection"
      - field: "pytest"
        expected_value: "All pass (561 at HEAD per the batch report)"
        validation: "pytest summary"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "bf03008 changed tests/conftest.py only (8 deletions). pytest tests/: 561 passed"
      pass_fail_criteria: "No test file other than conftest.py changed; suite passes"
    defects: []

  - case_id: "TC-003"
    description: "Remaining SetupScreen members keep their values"
    category: "boundary"
    preconditions: []
    test_steps:
      - step: "1"
        action: "git show bf03008^:src/gtach/display/setup_models.py and the current file; compare the SetupScreen member order"
      - step: "2"
        action: "python -c 'from gtach.display.setup_models import SetupScreen as S; print([(m.name, m.value) for m in S])'"
    inputs: []
    expected_outputs:
      - field: "members"
        expected_value: "Six members, the former first six in unchanged order and value"
        validation: "Comparison with the parent commit"
    postconditions:
      - "Guards against a shifted auto() value"
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "Current: WELCOME 1, DISCOVERY 2, DEVICE_LIST 3, PAIRING 4, COMPLETE 5, CURRENT_DEVICE 6. Parent commit lists the same six first, followed by DEVICE_MANAGEMENT and CONFIRMATION"
      pass_fail_criteria: "Names and values identical"
    defects: []

  - case_id: "TC-004"
    description: "Import and simtcp smoke run"
    category: "positive"
    preconditions:
      - "SDL_VIDEODRIVER=dummy; temporary GTACH_HOME"
    test_steps:
      - step: "1"
        action: "python -c 'import gtach.app, gtach.main'"
      - step: "2"
        action: "SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 python -m gtach --transport simtcp"
    inputs: []
    expected_outputs:
      - field: "import"
        expected_value: "Exit 0"
        validation: "Shell return code"
      - field: "smoke run"
        expected_value: "Exit 124 (timeout); no ImportError or AttributeError"
        validation: "Output inspection"
    postconditions:
      - "On macOS a framebuffer OSError traceback is environmental and is not a failure"
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "No ImportError, AttributeError or traceback; only the expected /dev/fb0 messages on the Mac. Process alive at 8 s. macOS has no timeout(1); run backgrounded instead, where zsh suspended it on tty output, so SIGTERM shutdown was not measurable on the Mac (observed on the Pi instead: clean stop on restart, 4/4 threads in 0.45 s)"
      pass_fail_criteria: "Clean import; run reaches the timeout"
    defects: []

  - case_id: "TC-005"
    description: "On-device normal use"
    category: "positive"
    preconditions:
      - "Branch deployed to root@gtach.local"
    test_steps:
      - step: "1"
        action: "Boot; observe the splash"
      - step: "2"
        action: "Walk the setup flow: welcome, discovery, device list, pairing, complete or current device"
      - step: "3"
        action: "Exercise taps and swipes; view the gauge"
      - step: "4"
        action: "Pull logs; inspect error.log"
    inputs: []
    expected_outputs:
      - field: "behaviour"
        expected_value: "Each screen renders and responds"
        validation: "Observation"
      - field: "error.log"
        expected_value: "No AttributeError or ImportError"
        validation: "Log inspection"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local, guided by Claude)"
      actual_result: "Boot splash, GTach splash and gauge normal; OPTIONS paging both ways; long-press palette toggle; DISCONNECTED screen with spinner, Setup and Reset; setup flow Current Device, New Setup, Welcome, Scanning, Select Device (one device, so no swipe or arrows to exercise), Pairing, gauge. error.log shows no AttributeError or ImportError"
      pass_fail_criteria: "Normal use; clean log"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-273ca048"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005"]
  code_coverage:
    target: "Not applicable (removal)"
    achieved: ""
  untested_areas:
    - component: "Newly orphaned code (get_info methods, _global_performance_manager, _cache_lock, simulated_taps)"
      reason: "Kept by constraint; candidates for a follow-up issue"

test_execution_summary:
  total_cases: 5
  passed: 5
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: "100%"
  execution_time: "Full suite 42.6 s; on-device use 09:38-10:34"
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
  verification_notes: "Mac: pytest 9.1.1, Python 3.11.14. Pi: GTach 0.4.10, Python 3.9.2."
  sign_off: "Approved"

traceability:
  requirements:
    - requirement_ref: "issue-273ca048"
      test_cases: ["TC-001", "TC-002"]
  designs: []
  changes:
    - change_ref: "change-273ca048"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005"]

notes: >
  No pytest file was generated for this change; verification is by
  static search, the existing suite and smoke runs. TC-003 is included
  because removing enum members is the only D-group with a plausible
  silent behaviour change; the report states the last two members were
  removed so no value shifts, which TC-003 confirms independently.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-273ca048."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Executed on Mac and gtach.local; results recorded per case; status passed."

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
| 1.0 | 2026-10-09 | Initial test document for change-273ca048. |
| 1.1 | 2026-10-09 | Executed on Mac and gtach.local; results recorded per case; status passed. |

---

Copyright (c) 2026 William Watson. MIT License.
