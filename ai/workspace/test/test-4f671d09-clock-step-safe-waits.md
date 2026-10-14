Created: 2026 October 09

# Test: Clock-Step-Safe Waits

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-4f671d09"
  title: "Verify timed waits in the supervision loops and one-shot waits are not extended by a backward wall-clock step"
  date: "2026-10-09"
  author: "William Watson"
  status: "passed"
  type: "regression"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-4f671d09"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "gtach.utils.waits.wait_for_event and its eight call sites in transport.py, watchdog.py, obd.py, interface.py, splash.py"
  design_refs: []
  change_refs:
    - "change-4f671d09"
  requirement_refs:
    - "issue-4f671d09"

scope:
  description: >
    Verifies the mechanism on the Mac (no timed Event.wait remains at the
    eight call sites; the helper honours its contract) and the behaviour
    on gtach.local, where Python 3.9.2 exhibits the defect: after a
    backward clock step the watchdog keeps checking and a dropped link is
    reconnected without operator action.
  test_objectives:
    - "Confirm tests/test_monotonic_waits.py passes."
    - "Confirm the full suite passes after the merge to main."
    - "Confirm no timed .wait( remains in the five changed source files."
    - "Confirm no 'Thread transport appears unresponsive' warning across a backward step on the device."
    - "Confirm a link drop after a backward step is reconnected without Reset."
    - "Confirm service stop is still prompt (polling adds at most 0.1 s per waiting thread)."
  in_scope:
    - "The eight call sites listed in report-4f671d09 §2"
    - "tests/test_link_loss_recovery.py and tests/test_reconnect_path.py, updated in this change"
  out_scope:
    - "app.py main loop, async_operations.py queue, timed join() calls (change-4f671d09 out_of_scope)"
  dependencies:
    - "Branch claude/kind-euler-ft8se4 merged to main"
    - "Development venv with pip install -e .[dev]"
    - "TC-004 to TC-006: wheel deployed to root@gtach.local; ELM327 emulator running on ELM327-Emulator.local"

test_environment:
  python_version: "3.11 (Mac); 3.9.2 (gtach.local)"
  os: "macOS (TC-001 to TC-003); Debian Linux on Raspberry Pi Zero 2W (TC-004 to TC-006)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest; on-device log inspection"
  test_data_location: "~/Documents/gtach-testlogs/ (not in the repository)"

test_cases:
  - case_id: "TC-001"
    description: "Helper and call-site regression tests pass"
    category: "positive"
    preconditions:
      - "Main contains commit 07bb8e5"
    test_steps:
      - step: "1"
        action: "pytest tests/test_monotonic_waits.py -v"
    inputs: []
    expected_outputs:
      - field: "result"
        expected_value: "12 passed (5 TestWaitForEvent, 7 TestCallSites)"
        validation: "pytest"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "Run together with tests/test_obd_verify_busy_retry.py: 16 passed (12 + 4), 1 warning, 1.88 s"
      pass_fail_criteria: "12 passed, 0 failed"
    defects: []

  - case_id: "TC-002"
    description: "Full suite passes after the merge"
    category: "positive"
    preconditions:
      - "Main fast-forwarded to 7f2ecc2"
    test_steps:
      - step: "1"
        action: "pytest tests/"
    inputs: []
    expected_outputs:
      - field: "result"
        expected_value: "577 passed (report-d26ca557 §3, includes test-d26ca557 TC-001)"
        validation: "pytest summary line"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (Mac, guided by Claude)"
      actual_result: "577 passed, 1 warning, 45.75 s; coverage 49% overall"
      pass_fail_criteria: "0 failed"
    defects: []

  - case_id: "TC-003"
    description: "No timed Event.wait remains in the changed files"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "grep -n '\\.wait(' src/gtach/comm/transport.py src/gtach/core/watchdog.py src/gtach/comm/obd.py src/gtach/display/splash.py src/gtach/display/setup_components/bluetooth/interface.py"
    inputs: []
    expected_outputs:
      - field: "matches"
        expected_value: "One: the untimed self._completion_event.wait() in splash.py wait_for_completion"
        validation: "Inspection"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "Claude (mcp-ripgrep on the merged working tree)"
      actual_result: "One match: splash.py:274 'return self._completion_event.wait()' (untimed branch). wait_for_event calls present: transport.py 721, 734, 740; watchdog.py 162; obd.py 110, 170; interface.py 183; splash.py 275 (eight)"
      pass_fail_criteria: "Only the untimed splash wait"
    defects: []

  - case_id: "TC-004"
    description: "On-device: watchdog stays responsive across a backward step (issue reproduction)"
    category: "negative"
    preconditions:
      - "GTach running on gtach.local with the emulator connected; debug logging on"
    test_steps:
      - step: "1"
        action: "timedatectl set-ntp false; date -s @$(( $(date +%s) - 3600 ))"
      - step: "2"
        action: "Wait 2 minutes"
      - step: "3"
        action: "date -s @$(( $(date +%s) + 7200 ))"
      - step: "4"
        action: "Pull logs; search debug.log for 'appears unresponsive' and check transport heartbeat lines continue through the interval"
    inputs:
      - parameter: "wall-clock steps"
        value: "-3600, then +7200"
        type: "int (s)"
    expected_outputs:
      - field: "WatchdogMonitor warnings"
        expected_value: "No 'Thread transport appears unresponsive' in the test interval"
        validation: "Log inspection"
    postconditions:
      - "timedatectl set-ntp true; confirm the clock is correct (timedatectl status)"
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local v0.4.11, guided by Claude)"
      actual_result: "NTP off; real 14:42:49 stepped to 13:42:49; after 120 s stepped +2 h to 15:44:49; checked 20 s later. error.log 'unresponsive' lines: only the pre-fix 2026-10-09 11:06:46 (102.9 s) entry; none in the test window. Before the fix the warning appeared at the forward step. NTP restored afterwards (a further ~1 h backward step)"
      pass_fail_criteria: "No unresponsive warning (before the fix: 102.9 s warning)"
    defects: []

  - case_id: "TC-005"
    description: "On-device: link drop after a backward step is reconnected without Reset"
    category: "negative"
    preconditions:
      - "As TC-004; NTP off"
    test_steps:
      - step: "1"
        action: "date -s @$(( $(date +%s) - 3600 ))"
      - step: "2"
        action: "Stop the ELM327 emulator on ELM327-Emulator.local; wait for the DISCONNECTED screen"
      - step: "3"
        action: "Start the emulator again; do not touch the display"
      - step: "4"
        action: "Observe the gauge; pull logs"
    inputs:
      - parameter: "wall-clock step"
        value: "-3600"
        type: "int (s)"
    expected_outputs:
      - field: "debug.log"
        expected_value: "'Failed to connect, retrying in 5.0 seconds' repeats about every 5 s while the emulator is down, then 'Connected to RFCOMM device'"
        validation: "Log inspection"
      - field: "display"
        expected_value: "Gauge returns with RPM without Reset"
        validation: "Observation"
    postconditions:
      - "timedatectl set-ntp true; confirm the clock is correct"
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local v0.4.11, guided by Claude)"
      actual_result: "NTP off, clock stepped back 1 h; systemctl stop elm327-emulator.service; DISCONNECTED shown. error.log (Pi clock): link error 13:49:04; 'Failed to connect, retrying in 5.0 seconds' at 13:49:11, :17, :22, :28, :34, :40, :45, :51, :57, 13:50:03 (5.6-5.9 s apart); emulator started ~30 s after DISCONNECTED; gauge returned with RPM about 5 s later, no Reset; no further errors. NTP restored. Before the fix no reconnect attempt was made after a backward step"
      pass_fail_criteria: "Automatic reconnection within ~10 s of the emulator returning"
    defects: []

  - case_id: "TC-006"
    description: "On-device: service stop remains prompt"
    category: "boundary"
    preconditions:
      - "GTach running normally"
    test_steps:
      - step: "1"
        action: "time systemctl restart gtach"
      - step: "2"
        action: "journalctl -u gtach -n 50 for stop/start lines"
    inputs: []
    expected_outputs:
      - field: "restart duration"
        expected_value: "Comparable to before the change (no thread join timeouts logged)"
        validation: "Command timing; no 'did not stop cleanly' in logs"
    postconditions: []
    execution:
      status: "passed"
      executed_date: "2026-10-09"
      executed_by: "William Watson (gtach.local v0.4.11, guided by Claude)"
      actual_result: "systemctl restart gtach at 14:41:37: real 0.612 s; active before and after; no 'did not stop' or join lines in error.log"
      pass_fail_criteria: "No join timeout warnings"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-4f671d09"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]
  code_coverage:
    target: "All eight call sites"
    achieved: "Eight of eight by TC-001 (mechanism)"
  untested_areas:
    - component: "Clock-step behaviour under Python 3.9 in pytest"
      reason: "Unit tests run on Python 3.11+/3.13, which do not have the defect; they check the mechanism only. TC-004 and TC-005 are authoritative."
    - component: "ensure_pairing_initialized and SplashScreen.wait_for_completion under a real clock step"
      reason: "One-shot failure-timeout paths; covered by TC-001 mechanism tests only. wait_for_completion has no callers."

test_execution_summary:
  total_cases: 6
  passed: 6
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: "100%"
  execution_time: "Mac pytest 45.75 s; on-device 14:41-14:51"
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
  verification_notes: "Mac: venv, 577 passed. Pi: GTach 0.4.11, Python 3.9.2. Logs pulled to logs/ (bin/pull_logs.sh) after TC-005. Out-of-scope observation in notes."
  sign_off: "Approved"

traceability:
  requirements:
    - requirement_ref: "issue-4f671d09"
      test_cases: ["TC-004", "TC-005"]
  designs: []
  changes:
    - change_ref: "change-4f671d09"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006"]

notes: >
  Generated pytest file: tests/test_monotonic_waits.py (12 tests);
  tests/test_link_loss_recovery.py and tests/test_reconnect_path.py were
  updated to the new mechanism with their intent preserved
  (report-4f671d09 §5). Run TC-004 before TC-005 and restore NTP after
  each. Implementation commits 07bb8e5 (code) and 7f2ecc2 (session report).
  Out-of-scope observation (TC-005): with the emulator service stopped,
  six consecutive ECONNREFUSED connects escalated the displayed cause
  from 'connection refused by adapter' to 'bluetooth wedged - reset
  required', although the controller was healthy. Wedge escalation
  (change-5e7a03c4) does not distinguish a refusing peer from a wedged
  controller. Not a failure of this change.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-4f671d09."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "TC-001 to TC-003 executed on the Mac after the merge; passed. Status in_progress."
  - version: "1.2"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "TC-004 to TC-006 executed on gtach.local; passed. Out-of-scope wedge-cause observation noted. Status passed."

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
| 1.0 | 2026-10-09 | Initial test document for change-4f671d09. |
| 1.1 | 2026-10-09 | TC-001 to TC-003 executed on the Mac; passed. Status in_progress. |
| 1.2 | 2026-10-09 | TC-004 to TC-006 executed on gtach.local; passed. Wedge-cause observation noted. Status passed. |

---

Copyright (c) 2026 William Watson. MIT License.
