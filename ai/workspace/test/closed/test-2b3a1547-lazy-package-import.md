Created: 2026 October 09

# Test: Lazy Package Import

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-2b3a1547"
  title: "Verify importing gtach or gtach.main no longer imports gtach.app or pygame"
  date: "2026-10-09"
  author: "William Watson"
  status: "passed"
  type: "integration"
  priority: "medium"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-2b3a1547"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "src/gtach/__init__.py package exports"
  design_refs: []
  change_refs:
    - "change-2b3a1547"
  requirement_refs:
    - "issue-2b3a1547"

scope:
  description: >
    Verifies the package import cost, that __version__ remains
    available, that both entry points still work, and that no consumer
    still relies on the removed re-exports.
  test_objectives:
    - "Confirm import gtach.main leaves pygame and gtach.app out of sys.modules in a fresh interpreter."
    - "Confirm gtach.__version__ is non-empty."
    - "Confirm python -m gtach --version exits 0."
    - "Confirm the console script gtach = gtach.main:main is unaffected."
    - "Confirm no consumer references gtach.GTachApplication or from gtach import main."
    - "Confirm the service starts and --validate-config runs on the device."
  in_scope:
    - "src/gtach/__init__.py"
    - "pyproject.toml [project.scripts]"
  out_scope:
    - "Start-up time measurement — not a stated objective of the change"
  dependencies:
    - "Development venv with pip install -e .[dev]"
    - "TC-006 only: root@gtach.local"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development); Debian Linux on Raspberry Pi Zero 2W (TC-006)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest (subprocess with sys.executable)"
  test_data_location: "None"

test_cases:
  - case_id: "TC-001"
    description: "import gtach.main does not import app or pygame"
    category: "positive"
    preconditions:
      - "Fresh interpreter"
    test_steps:
      - step: "1"
        action: "Run python -c 'import gtach.main, sys; print(...)' checking sys.modules"
    inputs: []
    expected_outputs:
      - field: "'pygame' in sys.modules"
        expected_value: "False"
        validation: "Subprocess output"
      - field: "'gtach.app' in sys.modules"
        expected_value: "False"
        validation: "Subprocess output"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_package_import.py::test_import_main_does_not_import_app_or_pygame"
      pass_fail_criteria: "Both False"
    defects: []

  - case_id: "TC-002"
    description: "__version__ is available"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Run python -c 'import gtach; print(gtach.__version__)'"
    inputs: []
    expected_outputs:
      - field: "stdout"
        expected_value: "Non-empty"
        validation: "Subprocess output"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_package_import.py::test_version_is_available"
      pass_fail_criteria: "Non-empty value"
    defects: []

  - case_id: "TC-003"
    description: "Module entry point reports the version"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Run python -m gtach --version"
    inputs: []
    expected_outputs:
      - field: "exit code"
        expected_value: "0"
        validation: "Subprocess return code"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_package_import.py::test_module_entry_point_version"
      pass_fail_criteria: "Exit 0"
    defects: []

  - case_id: "TC-004"
    description: "Console script entry point is unaffected"
    category: "positive"
    preconditions:
      - "Package installed in the venv"
    test_steps:
      - step: "1"
        action: "grep -n 'gtach = ' pyproject.toml"
      - step: "2"
        action: "Run gtach --version from the venv"
    inputs: []
    expected_outputs:
      - field: "pyproject.toml"
        expected_value: "gtach = \"gtach.main:main\""
        validation: "Inspection (confirmed 2026-10-09)"
      - field: "exit code"
        expected_value: "0"
        validation: "Shell return code"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac and gtach.local, guided by Claude)"
      actual_result: "pyproject.toml line 65: gtach = \"gtach.main:main\". gtach --version printed 'GTach 0.4.9' on the Mac before the bump. On the Pi, after deploy, /opt/gtach/venv/bin/gtach --version printed 'GTach 0.4.10' with no pygame banner (before the deploy the banner was printed)"
      pass_fail_criteria: "Target unchanged; exit 0"
    defects: []

  - case_id: "TC-005"
    description: "No consumer relies on the removed re-exports"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -n 'from .app\\|from .main' src/gtach/__init__.py"
      - step: "2"
        action: "grep -rn 'gtach.GTachApplication\\|from gtach import main' src tests bin"
    inputs: []
    expected_outputs:
      - field: "matches"
        expected_value: "None for both"
        validation: "grep exit 1"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "Both greps returned no source match; only stale compiled files under __pycache__ matched, which are not source"
      pass_fail_criteria: "No match"
    defects: []

  - case_id: "TC-006"
    description: "On-device: service start and config validation"
    category: "positive"
    preconditions:
      - "Branch deployed to root@gtach.local"
    test_steps:
      - step: "1"
        action: "systemctl status gtach"
      - step: "2"
        action: "/opt/gtach/venv/bin/gtach --validate-config"
    inputs: []
    expected_outputs:
      - field: "service"
        expected_value: "active (running); display starts"
        validation: "systemctl output and observation"
      - field: "--validate-config"
        expected_value: "Exit 0 on a valid file"
        validation: "echo $?"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local, guided by Claude)"
      actual_result: "systemctl is-active gtach: active; display started (two-line splash, animated splash with version, gauge). gtach --validate-config: 'Config valid: /opt/gtach/config.yaml', exit 0"
      pass_fail_criteria: "Running and exit 0"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-2b3a1547"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]
  code_coverage:
    target: "Not applicable (module-level imports)"
    achieved: ""
  untested_areas:
    - component: "Third-party code importing gtach.GTachApplication"
      reason: "None known; the package has no external consumers"

test_execution_summary:
  total_cases: 6
  passed: 6
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: "100%"
  execution_time: "Targeted pytest run 26.8 s (137 passed); on-device checks 09:40-09:45"
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
  verification_notes: "Mac: pytest 9.1.1, Python 3.11.14. Pi: GTach 0.4.10, Python 3.9.2. Note: --validate-config runs the logging setup, so on a running Pi it truncates start.log and rotates debug.log (listed in ai/task.md)."
  sign_off: "Approved"

traceability:
  requirements:
    - requirement_ref: "issue-2b3a1547"
      test_cases: ["TC-001", "TC-005"]
  designs: []
  changes:
    - change_ref: "change-2b3a1547"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]

notes: >
  Generated pytest file: tests/test_package_import.py, per P06 §1.7.3.
  Written during implementation; recorded here retrospectively. TC-001 to
  TC-003 run in a subprocess so that modules already imported by other
  tests in the same session cannot mask a regression.
  Run: pytest tests/test_package_import.py -v.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-2b3a1547."
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
| 1.0 | 2026-10-09 | Initial test document for change-2b3a1547. |
| 1.1 | 2026-10-09 | Executed on Mac and gtach.local; results recorded per case; status passed. |

---

Copyright (c) 2026 William Watson. MIT License.
