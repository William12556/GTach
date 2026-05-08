Created: 2026 May 08

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-c9b5e7f4"
  title: "OBD poll rate hard-capped at 10 Hz producing stepped RPM motion"
  date: "2026-05-08"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "performance"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "code_review"
  test_ref: ""
  description: >
    OBDProtocol._protocol_loop has an unconditional time.sleep(0.1) at the
    end of every polling iteration, hard-capping the RPM data rate at 10 Hz.
    The display renders at 60 Hz but can only show new data at 10 Hz, producing
    visibly stepped RPM motion especially in sim mode where the sine sweep is fast.

affected_scope:
  components:
    - name: "OBDProtocol._protocol_loop"
      file_path: "src/gtach/comm/obd.py"
  designs:
    - design_ref: ""
  version: "0.2.37"

reproduction:
  prerequisites: "Any transport. Observe RPM display during sweep or rapid RPM change."
  steps:
    - "Start gtach --transport simbt"
    - "Observe RPM value during sine sweep"
    - "Note stepped/discrete changes rather than smooth motion"
  frequency: "always"
  reproducibility_conditions: "Always visible when RPM is changing quickly."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    RPM display updates as fast as the transport allows. On SimTransport and
    TCP transports, round-trip time is under 5ms, allowing 100+ Hz polling.
    On a real ELM327 via RFCOMM, round-trip is typically 30-80ms, allowing
    12-30 Hz. In all cases the display should reflect the transport's actual
    capability rather than an artificial floor.
  actual: >
    Poll rate is fixed at 10 Hz regardless of transport speed. 100ms sleep
    is added after every response even when the transport could respond faster.
  impact: >
    RPM motion is stepped at 10 Hz. For a tachometer this is the primary
    display metric — smoothness is directly tied to update rate.
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Linux (Raspberry Pi Zero 2W, Debian)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    time.sleep(0.1) was added as a simple rate limiter to prevent the OBD
    thread from spinning at maximum CPU. The correct approach is to measure
    actual round-trip time and subtract it from a target interval, or simply
    remove the sleep and let the transport's natural latency govern the rate.
    For RFCOMM at 30-80ms RTT the natural rate is already 12-30 Hz without
    any sleep. For SimTransport at <5ms RTT an uncapped loop would poll at
    200+ Hz which is excessive; a short sleep of 20-30ms (targeting ~40 Hz)
    is more appropriate.
  technical_notes: >
    Recommended approach: reduce sleep to 0.02s (50 Hz ceiling) for sim/TCP
    transports and leave 0.05s (20 Hz ceiling) as the default for real
    hardware where RFCOMM latency naturally limits throughput anyway.
    A configurable poll_interval_s parameter in OBDProtocol.__init__ allows
    transport-specific tuning without hardcoding.
  related_issues:
    - issue_ref: ""
      relationship: ""

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Add poll_interval_s parameter to OBDProtocol.__init__ (default 0.05).
    Replace time.sleep(0.1) with time.sleep(self.poll_interval_s).
    Pass poll_interval_s=0.02 from app.py for sim and TCP transports.
  change_ref: "change-c9b5e7f4"
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
    Poll rate should be a configurable parameter, not a magic constant, so
    it can be tuned per transport type.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "Start gtach --transport simbt"
    - "Observe RPM sweep — confirm visibly smoother motion than 10 Hz"
    - "Check log — confirm TX:010C frequency increased"
    - "Start gtach with real RFCOMM transport"
    - "Confirm no excessive CPU usage or RFCOMM buffer overflow"
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-c9b5e7f4"
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
