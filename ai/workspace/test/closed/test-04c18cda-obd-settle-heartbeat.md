Created: 2026 October 09

# Test: OBD Settle Without Heartbeat Gap

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-04c18cda"
  title: "Verify the pre-initialised OBD settle waits in interruptible slices with a heartbeat after each"
  date: "2026-10-09"
  author: "William Watson"
  status: "passed"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-04c18cda"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "OBDProtocol._initialize_protocol pre-initialised branch (src/gtach/comm/obd.py)"
  design_refs: []
  change_refs:
    - "change-04c18cda"
  requirement_refs:
    - "issue-04c18cda"

scope:
  description: >
    Verifies that the 1.5 s settle no longer blocks the watchdog
    heartbeat, honours a stop request within one 0.5 s slice, and sends
    no command once a stop is requested. Includes one on-device check of
    the first connection after setup.
  test_objectives:
    - "Confirm the largest heartbeat gap during settle is at most 0.6 s and the settle lasts at least 1.4 s."
    - "Confirm a stop during settle returns False within one slice and sends no ATE0."
    - "Confirm a stop already set returns False immediately with no command sent."
    - "Confirm the watchdog reports no obd_protocol unresponsive warning in the lifecycle harness."
    - "Confirm time.sleep(1.5) is gone from obd.py."
  in_scope:
    - "src/gtach/comm/obd.py — _PRE_INIT_SETTLE_S, _SETTLE_SLICE_S, settle loop"
    - "tests/test_lifecycle_sim.py — TestWatchdogQuiet, TestHeartbeatBound"
  out_scope:
    - "Full-init (ATZ) branch — unchanged by this change"
  dependencies:
    - "Development venv with pip install -e .[dev]"
    - "TC-006 only: root@gtach.local with a paired ELM327 adapter or ELM327-Emulator.local"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development); Debian Linux on Raspberry Pi Zero 2W (TC-006)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest"
  test_data_location: "Inline protocol fixture"

test_cases:
  - case_id: "TC-001"
    description: "Heartbeat gap stays bounded during settle"
    category: "positive"
    preconditions:
      - "Protocol marked pre-initialised; shutdown_event clear"
    test_steps:
      - step: "1"
        action: "Run _initialize_protocol and record heartbeat timestamps"
    inputs: []
    expected_outputs:
      - field: "largest heartbeat gap"
        expected_value: "<= 0.6 s"
        validation: "Computed from recorded timestamps"
      - field: "settle duration"
        expected_value: ">= 1.4 s"
        validation: "Monotonic clock difference"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_obd_settle.py::test_settle_keeps_heartbeat_gap_bounded"
      pass_fail_criteria: "Both bounds met"
    defects: []

  - case_id: "TC-002"
    description: "Stop during settle returns False within one slice"
    category: "negative"
    preconditions:
      - "Protocol pre-initialised"
    test_steps:
      - step: "1"
        action: "Start _initialize_protocol; set shutdown_event at 0.2 s"
    inputs:
      - parameter: "stop time"
        value: "0.2"
        type: "float (s)"
    expected_outputs:
      - field: "return"
        expected_value: "False"
        validation: "Equality"
      - field: "elapsed"
        expected_value: "< 0.7 s"
        validation: "Monotonic clock difference"
      - field: "commands sent"
        expected_value: "No ATE0"
        validation: "Fake transport record"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_obd_settle.py::test_stop_during_settle_returns_false_without_commands"
      pass_fail_criteria: "All three as expected"
    defects: []

  - case_id: "TC-003"
    description: "Stop already set returns immediately"
    category: "boundary"
    preconditions:
      - "shutdown_event set before the call"
    test_steps:
      - step: "1"
        action: "Call _initialize_protocol"
    inputs: []
    expected_outputs:
      - field: "return"
        expected_value: "False"
        validation: "Equality"
      - field: "commands sent"
        expected_value: "None"
        validation: "Fake transport record empty"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "tests/test_obd_settle.py::test_stop_already_set_returns_immediately"
      pass_fail_criteria: "False and no command"
    defects: []

  - case_id: "TC-004"
    description: "Watchdog quiet and heartbeat bound in the lifecycle harness"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Run tests/test_lifecycle_sim.py::TestWatchdogQuiet and ::TestHeartbeatBound"
    inputs: []
    expected_outputs:
      - field: "TestWatchdogQuiet::test_no_obd_unresponsive_warning"
        expected_value: "Passes with no xfail marker"
        validation: "pytest exit 0"
      - field: "TestHeartbeatBound::test_largest_obd_gap_below_two_seconds"
        expected_value: "Passes"
        validation: "pytest exit 0"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "TestWatchdogQuiet::test_no_shutdown, ::test_no_obd_unresponsive_warning and TestHeartbeatBound::test_largest_obd_gap_below_two_seconds PASSED; no xfail marker in the file"
      pass_fail_criteria: "All pass"
    defects: []

  - case_id: "TC-005"
    description: "The blocking sleep is removed"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -n 'time.sleep(1.5)' src/gtach/comm/obd.py"
    inputs: []
    expected_outputs:
      - field: "matches"
        expected_value: "None"
        validation: "grep exit 1"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "grep returned no match"
      pass_fail_criteria: "No match"
    defects: []

  - case_id: "TC-006"
    description: "On-device: first OBD connection after setup"
    category: "positive"
    preconditions:
      - "Branch deployed to root@gtach.local"
      - "Setup completed; adapter reachable"
    test_steps:
      - step: "1"
        action: "Complete setup and allow the first OBD connection"
      - step: "2"
        action: "Pull logs with bin/pull_logs.sh; inspect error.log"
    inputs: []
    expected_outputs:
      - field: "display"
        expected_value: "RPM appears"
        validation: "Observation"
      - field: "error.log"
        expected_value: "No obd_protocol unresponsive warning during the first connection"
        validation: "Log inspection"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local, guided by Claude)"
      actual_result: "Re-pair at 10:28 (stage 8): OBDProtocol init adapter_pre_initialised=True 10:28:37.661, connected 10:28:37.711, Link restored 10:28:42.530; RPM shown; no watchdog unresponsive warning in debug.log or error.log"
      pass_fail_criteria: "RPM shown and no warning"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-04c18cda"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]
  code_coverage:
    target: "All branches of the settle loop"
    achieved: ""
  untested_areas:
    - component: "Full-init (ATZ) branch"
      reason: "Unchanged by this change"

test_execution_summary:
  total_cases: 6
  passed: 6
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: "100%"
  execution_time: "Targeted pytest run 26.8 s (137 passed); on-device re-pair 10:27-10:29"
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
  verification_notes: "Mac: pytest 9.1.1, Python 3.11.14. Pi: GTach 0.4.10, Python 3.9.2, emulator adapter DC:A6:32:54:AD:77. Evidence under ~/Documents/gtach-testlogs/ (mac/, stage8-pair/)."
  sign_off: "Approved"

traceability:
  requirements:
    - requirement_ref: "issue-04c18cda"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-006"]
  designs: []
  changes:
    - change_ref: "change-04c18cda"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]

notes: >
  Generated pytest files: tests/test_obd_settle.py (new) and
  tests/test_lifecycle_sim.py (xfail removed), per P06 §1.7.3. Written
  during implementation; recorded here retrospectively. TC-001 and TC-002
  rely on real timing; run on an otherwise idle machine to avoid
  scheduler-induced false failures. TC-006 is the only on-device case.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-04c18cda."
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
| 1.0 | 2026-10-09 | Initial test document for change-04c18cda. |
| 1.1 | 2026-10-09 | Executed on Mac and gtach.local; results recorded per case; status passed. |

---

Copyright (c) 2026 William Watson. MIT License.
