Created: 2026 May 08

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-a3f1d8e2"
  title: "OBDProtocol re-initialises adapter on every reconnect causing 5-9s RPM data gap"
  date: "2026-05-08"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "code_review"
  test_ref: ""
  description: >
    On any transport disconnect/reconnect cycle the OBD outer loop re-enters
    _initialize_protocol(). This sends ATZ (5s timeout) followed by ATE0, ATL0,
    ATS0, ATSP0, and 0100. No RPM data is produced during this sequence.
    Duration on reconnect: 5-9 seconds of frozen RPM display.

affected_scope:
  components:
    - name: "OBDProtocol._protocol_loop"
      file_path: "src/gtach/comm/obd.py"
    - name: "OBDProtocol._initialize_protocol"
      file_path: "src/gtach/comm/obd.py"
    - name: "OBDTransport.reconnect_indefinitely"
      file_path: "src/gtach/comm/transport.py"
  designs:
    - design_ref: ""
  version: "0.2.37"

reproduction:
  prerequisites: "Running on Pi with any transport. Disconnect and reconnect OBD adapter."
  steps:
    - "Start gtach with any transport"
    - "Disconnect OBD adapter or allow transport to drop"
    - "Reconnect adapter"
    - "Observe RPM display — frozen for 5-9 seconds"
  frequency: "always"
  reproducibility_conditions: "Any transport disconnect followed by reconnect."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    RPM display resumes within 1-2 seconds of reconnect. ATZ is sent only once at
    first connect; subsequent reconnects skip ATZ and use a faster re-init sequence.
  actual: >
    Full adapter init sequence including ATZ (5s timeout) runs on every reconnect.
    RPM display is frozen for the full duration of the sequence.
  impact: >
    In a moving vehicle a 5-9 second RPM data gap is safety-relevant. Engine
    state is unknown to the driver during the gap.
  workaround: "None. Avoid transport disconnections."

environment:
  python_version: "3.9"
  os: "Linux (Raspberry Pi Zero 2W, Debian)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    _protocol_loop has a single code path through _initialize_protocol on every
    outer loop iteration. There is no distinction between first connect and
    reconnect. ATZ is a hard reset of the ELM327 adapter — it is only necessary
    once at startup or after a power cycle of the adapter hardware, not on every
    socket reconnect.
  technical_notes: >
    Two improvements:
    (A) Skip ATZ on reconnect. Track whether this is the first connect via an
        instance flag _adapter_initialised: bool = False. On reconnect, send only
        ATE0/ATL0/ATS0/ATSP0/0100. Reset flag only when transport is fully
        disconnected (not just dropped).
    (B) Coordinate with transport.reconnect_indefinitely so the OBD loop waits
        for a confirmed connection before starting the init sequence rather than
        immediately probing a potentially-connecting transport. The existing
        is_connected() check handles this for the normal case; no change required
        here as long as (A) is implemented.
  related_issues:
    - issue_ref: ""
      relationship: ""

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Add _adapter_initialised flag to OBDProtocol. In _initialize_protocol, skip
    ATZ when flag is True. Set flag to True after successful init. Reset flag in
    stop() and when transport disconnects (inner loop exits).
  change_ref: "change-a3f1d8e2"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    Distinguish hardware reset commands (ATZ) from protocol setup commands
    (ATE0 etc.) in documentation and code. Hardware reset commands should be
    guarded by first-connect flags.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "Start gtach --transport simbt, confirm RPM displays"
    - "Kill and restart SimTransport to simulate disconnect/reconnect"
    - "Confirm RPM resumes within 2 seconds"
    - "Confirm ATZ does not appear in log on reconnect"
    - "Confirm ATE0/ATL0/ATS0/ATSP0/0100 do appear in log on reconnect"
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-a3f1d8e2"
  test_refs: []

notes: ""

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial issue document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
