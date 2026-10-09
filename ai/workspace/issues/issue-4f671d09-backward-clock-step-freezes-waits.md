Created: 2026 October 09

# Issue: Backward Clock Step Freezes Event Waits on Python 3.9

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-4f671d09"
  title: "A backward wall-clock step suspends threading.Event.wait for the size of the step on Python 3.9, stopping link reconnection"
  date: "2026-10-09"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "test_result"
  test_ref: "test-e215a184 TC-005 (forced clock steps on gtach.local, 2026-10-09)"
  description: >
    Found during on-device verification of the nine-change batch. Not
    caused by any change in that batch.

affected_scope:
  components:
    - name: "OBDTransport.reconnect_indefinitely / supervision loop"
      file_path: "src/gtach/comm/transport.py (lines 714, 727, 733)"
    - name: "WatchdogMonitor check loop"
      file_path: "src/gtach/core/watchdog.py (line 161)"
    - name: "OBDProtocol initialisation retry and pre-initialised settle"
      file_path: "src/gtach/comm/obd.py (lines 109, 169)"
    - name: "GTachApplication main loop"
      file_path: "src/gtach/app.py (line 594)"
  designs:
    - design_ref: ""
  version: "0.4.10 (b1dd162)"

reproduction:
  prerequisites: "GTach running on gtach.local (Python 3.9.2) with a connected adapter; debug logging on."
  steps:
    - "timedatectl set-ntp false; date -s @$(( $(date +%s) - 3600 ))"
    - "Wait 2 minutes."
    - "date -s @$(( $(date +%s) + 7200 ))"
    - "Observe debug.log: the watchdog logs the transport thread unresponsive for the interval between the two steps."
    - "Alternatively: after a backward step, switch the adapter off and on; no reconnect attempt is made."
  frequency: "always"
  reproducibility_conditions: "Python < 3.11 on Linux; a backward step of the system clock while a thread is inside Event.wait."
  preconditions: ""
  test_data: ""
  error_output: "2026-10-09 11:06:46,000 WatchdogMonitor WARNING Thread transport appears unresponsive (timeout: 102.9s)"

behavior:
  expected: "A wait with a timeout of N seconds returns after N seconds of elapsed time, whatever the wall clock does."
  actual: >
    After a backward step of S seconds, a wait in progress lasts about
    S seconds longer. Observed: the transport thread was silent for
    102.9 s, exactly the real interval between a -1 h and a +2 h step.
    In stage 7 (2026-10-09 10:11-10:14), after NTP stepped the clock
    back 1 h at ~10:08:30, the link dropped at 10:11:59 and no reconnect
    attempt was logged until the operator pressed Reset at 10:14:04. The
    watchdog also stayed silent, since its own check loop waits the
    same way.
  impact: >
    Link loss is not recovered, and the watchdog cannot report it, for
    up to the size of the backward step. A forward step, the usual
    NTP correction at boot on a Pi without an RTC, does not trigger it.
    The display thread is unaffected (time.sleep), so the gauge keeps
    rendering and shows DISCONNECTED.
  workaround: "Reset button on the DISCONNECTED screen, or systemctl restart gtach."

environment:
  python_version: "3.9.2 (gtach.local)"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "CPython threading"
      version: "3.9"
  domain: "comm, core"

analysis:
  root_cause: >
    Inferred, consistent with the evidence: on Linux, CPython before 3.11
    implements timed lock acquisition, and therefore Event.wait and
    Condition.wait, with sem_timedwait against CLOCK_REALTIME. CPython
    3.11 switched to sem_clockwait with CLOCK_MONOTONIC where glibc
    provides it. A backward step therefore moves the absolute deadline
    of a wait already in progress into the future.
  technical_notes: >
    Not reproduced on the Mac (macOS uses a different implementation).
    change-e215a184 moved duration measurements to time.monotonic(); this
    defect concerns the blocking waits, which that change did not cover.
    Candidate approaches, to be decided in the change: short bounded
    waits re-checked against time.monotonic(); time.sleep where no early
    wake-up is needed; or a newer interpreter on the Pi.
  related_issues:
    - issue_ref: "issue-e215a184"
      relationship: "related"
    - issue_ref: "issue-04c18cda"
      relationship: "related"

resolution:
  assigned_to: ""
  target_date: ""
  approach: ""
  change_ref: ""
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: ""
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "Repeat the reproduction steps; no watchdog unresponsive warning; a link drop after a backward step is reconnected without operator action."
  verification_results: ""

traceability:
  design_refs:
    - ""
  change_refs:
    - ""
  test_refs:
    - "test-e215a184 TC-005"
    - "~/Documents/gtach-testlogs/stage6/ and stage7/ (not in the repository)"

notes: "Raised from test_result per P03.1."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial issue document, raised during on-device verification of the nine-change batch."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial issue document, raised during on-device verification of the nine-change batch. |

---

Copyright (c) 2026 William Watson. MIT License.
