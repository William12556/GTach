Created: 2026 October 07

# Issue: OBD Initialisation Never Succeeds After a Late 0100 Reply

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-dc52c4e4"
  title: "A 0100 reply arriving after its 1.0 s timeout shifts every later response by one command; with the strict 0100 check (issue-907de6de) initialisation then fails indefinitely"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-dc52c4e4"
    change_iteration: 1

source:
  origin: "on_device_verification"
  test_ref: "ai/workspace/test/test-36b6ea95-on-device-verification.md (Session A)"
  description: "Observed on 0.4.5 with the ELM327 emulator: every start shows DISCONNECTED; Setup -> Continue recovers only by chance."

affected_scope:
  components:
    - name: "OBDTransport.send_command"
      file_path: "src/gtach/comm/transport.py"
    - name: "OBDProtocol._initialize_protocol"
      file_path: "src/gtach/comm/obd.py"
  designs: []
  version: "0.4.5"

reproduction:
  prerequisites: "Pi with paired ELM327 emulator; service started normally."
  steps:
    - "Start gtach; observe the gauge."
  frequency: "always (observed on every start on 2026-10-07)"
  reproducibility_conditions: "First 0100 after ATSP0 takes slightly more than 1.0 s (protocol search, 'SEARCHING...')."
  test_data: >
    debug.log 14:19:29-14:21:30: 0100 times out at 1.0 s; the late reply
    'SEARCHING...\r4100...\r4100...' is read as the ATZ response; from then
    on ATE0 -> 'ELM327 v1.5', 0100 -> 'OK'. 36 initialisation failures in
    2 minutes; recovery only after Setup -> Continue (14:21:38).
  error_output: "OBDProtocol ERROR Initialization failed: No valid 0100 response: 'OK'"

behavior:
  expected: "Initialisation succeeds after the adapter answers 0100; one late reply does not affect later commands."
  actual: "Initialisation fails on every retry; DISCONNECTED until the operator re-enters setup, which does not reliably help."
  impact: "No RPM display after start."
  workaround: "Setup -> CURRENT_DEVICE -> Continue, possibly repeatedly."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    (1) The 0100 command uses the default 1.0 s timeout although an
    ELM327 protocol search after ATSP0 can take several seconds.
    (2) send_command neither discards stale input before writing nor stops
    at the first '>' prompt, so a late reply is consumed by the next
    command and the misalignment persists across retries.
    (3) issue-907de6de made initialisation require '4100' in the 0100
    reply, which turned the previously harmless misalignment into a
    permanent failure.
  technical_notes: "Related open item in ai/task.md: 'OBD response desync'."
  related_issues:
    - "issue-907de6de"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-dc52c4e4."
  change_ref: "change-dc52c4e4"
  resolved_date: "2026-10-07"
  resolved_by: "change-dc52c4e4"
  fix_description: "change-dc52c4e4 implemented 2026-10-07; verified on device."

verification:
  verified_date: "2026-10-07"
  verified_by: "William Watson"
  test_results: "Pi 0.4.6, 2026-10-07 14:51: RPM shown after reboot without operator action; first 0100 answered after 3.0 s ('SEARCHING...' + two 4100 replies) and passed within the 5 s timeout; no initialisation failure after the link was established."
  closure_notes: "Closed after on-device verification."

prevention:
  preventive_measures: "Unit test with a late reply."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Pi: start gtach with the emulator running; RPM shown without operator action; no 'Initialization failed' records after the first successful start."
  verification_results: "Passed 2026-10-07."

traceability:
  design_refs: []
  change_refs:
    - "change-dc52c4e4"
  test_refs: []

notes: ""

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial issue document from on-device verification Session A."
  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Verified on device; closed."

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
| 1.0 | 2026-10-07 | Initial issue document. |
| 1.1 | 2026-10-07 | Verified on device; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
