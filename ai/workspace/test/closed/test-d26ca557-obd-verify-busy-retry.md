Created: 2026 October 09

# Test: OBD Verify Busy Retry

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-d26ca557"
  title: "Verify the post-pairing OBD verify retries a link-busy connect and setup completes without Retry"
  date: "2026-10-09"
  author: "William Watson"
  status: "passed"
  type: "regression"
  priority: "medium"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-d26ca557"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "BluetoothSetupInterface.verify_obd_connection; gtach.comm.transport.LINK_BUSY_CAUSE"
  design_refs: []
  change_refs:
    - "change-d26ca557"
  requirement_refs:
    - "issue-d26ca557"

scope:
  description: >
    Verifies on the Mac that only the link-busy cause is retried, at most
    three attempts, and on gtach.local that re-pairing completes setup in
    one pass.
  test_objectives:
    - "Confirm tests/test_obd_verify_busy_retry.py passes."
    - "Confirm re-pairing on gtach.local completes setup without Retry."
    - "Record whether the retry path was exercised on the device."
  in_scope:
    - "verify_obd_connection retry loop"
    - "LINK_BUSY_CAUSE constant and mapping entry"
  out_scope:
    - "start_device_probe; persistent EBUSY after link loss (task.md item); EBUSY ERROR lines in error.log"
  dependencies:
    - "Branch claude/kind-euler-ft8se4 merged to main"
    - "TC-002: wheel deployed to root@gtach.local; ELM327 emulator in range"

test_environment:
  python_version: "3.11 (Mac); 3.9.2 (gtach.local)"
  os: "macOS (TC-001); Debian Linux on Raspberry Pi Zero 2W (TC-002)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
    - name: "BlueZ"
      version: "Bullseye package"
  test_framework: "pytest; on-device observation and log inspection"
  test_data_location: "~/Documents/gtach-testlogs/ (not in the repository)"

test_cases:
  - case_id: "TC-001"
    description: "Retry-behaviour unit tests pass"
    category: "positive"
    preconditions:
      - "Main contains commit a1e5e44"
    test_steps:
      - step: "1"
        action: "pytest tests/test_obd_verify_busy_retry.py -v"
    inputs: []
    expected_outputs:
      - field: "result"
        expected_value: "4 passed: test_busy_then_success, test_other_failure_is_not_retried, test_busy_three_times_gives_up, test_link_busy_cause_matches_mapping"
        validation: "pytest"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "Run together with tests/test_monotonic_waits.py: 16 passed (12 + 4), 1 warning, 1.88 s. Full suite: see test-4f671d09 TC-002 (577 passed)"
      pass_fail_criteria: "4 passed, 0 failed"
    defects: []

  - case_id: "TC-002"
    description: "On-device: re-pairing completes setup in one pass"
    category: "positive"
    preconditions:
      - "GTach running on gtach.local with the gauge connected; emulator in range"
      - "Debug on: OPTIONS, swipe left to page 1, tap 'Debug: Off' so it reads 'Debug: On'"
    test_steps:
      - step: "1"
        action: "Swipe down on the gauge to open OPTIONS (page 0); tap 'Clear settings'; on 'Clear settings?' tap 'Clear'"
      - step: "2"
        action: "On 'Welcome' tap 'Start Setup'; wait through 'Scanning...'"
      - step: "3"
        action: "On 'Select Device' bring ELM327-Emulator to the middle slot (vertical swipe if needed); tap the middle slot once; tap nothing else"
      - step: "4"
        action: "Observe 'Pairing Device', then 'Setup Complete!' and the gauge. A return to 'Select Device' with 'OBD check failed' is a failure"
      - step: "5"
        action: "Repeat steps 1-4 three times in total; then pull logs and record, per run, 'OBD verify: link busy, retrying' and 'OBD verify: pass' lines"
    inputs: []
    expected_outputs:
      - field: "display"
        expected_value: "Each run returns to the gauge without the operator tapping Retry"
        validation: "Observation"
      - field: "debug.log"
        expected_value: "'OBD verify: pass' per run; any retry line is followed by pass within ~2 s"
        validation: "Log inspection"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local v0.4.11, guided by Claude)"
      actual_result: "3 of 3 runs returned to the gauge without operator action (debug on). Run 1: paired 15:02:57.447, 'OBD verify: pass' 15:02:58.038. Run 2: paired 15:06:16.662; EBUSY at 15:06:16.682 (20 ms after pairing); 'link busy, retrying (attempt 2/3)' 15:06:16.694; 'OBD verify: pass' 15:06:18.322. Run 3: paired 15:06:53.110, pass 15:06:53.699. The retry path was exercised once and recovered on the second attempt. Observation: 'Setup Complete!' was replaced too quickly to read; addressed separately by a 2.0 s hold (commit 0e3212f, trivial exemption)"
      pass_fail_criteria: "3 of 3 runs complete without Retry"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-d26ca557"
      test_cases: ["TC-001", "TC-002"]
  code_coverage:
    target: "All three loop outcomes (success after busy, non-busy failure, busy exhaustion)"
    achieved: "Three of three by TC-001"
  untested_areas:
    - component: "Retry path on the device"
      reason: "EBUSY is intermittent; if no run in TC-002 logs a retry line, the device run shows no regression but does not exercise the fix. Record this in actual_result rather than failing the case."
    - component: "Non-busy failure on the device"
      reason: "Hard to provoke after a successful pairing; covered by TC-001 test_other_failure_is_not_retried."

test_execution_summary:
  total_cases: 2
  passed: 2
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: "100%"
  execution_time: "Mac pytest 1.88 s; on-device 15:02-15:07"
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: "2026-10-14"
  verified_by: "William Watson"
  verification_notes: "Mac: venv, 577 passed. Pi: GTach 0.4.11, Python 3.9.2. Logs pulled 2026-10-14 (logs/debug.log.1). The intermittent EBUSY occurred in 1 of 3 runs and was recovered by the retry."
  sign_off: "Approved"

traceability:
  requirements:
    - requirement_ref: "issue-d26ca557"
      test_cases: ["TC-002"]
  designs: []
  changes:
    - change_ref: "change-d26ca557"
      test_cases: ["TC-001", "TC-002"]

notes: >
  Generated pytest file: tests/test_obd_verify_busy_retry.py (4 tests).
  The full-suite run is recorded in test-4f671d09 TC-002. Retry log text
  'attempt n/3' names the attempt about to run (report-d26ca557 §5);
  kept as implemented. Implementation commit a1e5e44.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-d26ca557."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "TC-001 executed on the Mac after the merge; passed. Status in_progress."
  - version: "1.2"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "TC-002 steps corrected to the actual UI path (OPTIONS > Clear settings > Clear > Start Setup); debug-on precondition added."
  - version: "1.3"
    date: "2026-10-14"
    author: "William Watson"
    changes:
      - "TC-002 executed on gtach.local; passed (retry path exercised in run 2). Status passed."

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
| 1.0 | 2026-10-09 | Initial test document for change-d26ca557. |
| 1.1 | 2026-10-09 | TC-001 executed on the Mac; passed. Status in_progress. |
| 1.2 | 2026-10-09 | TC-002 steps corrected to the actual UI path; debug-on precondition added. |
| 1.3 | 2026-10-14 | TC-002 executed on gtach.local; passed (retry path exercised in run 2). Status passed. |

---

Copyright (c) 2026 William Watson. MIT License.
