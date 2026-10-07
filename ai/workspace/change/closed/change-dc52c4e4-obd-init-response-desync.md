Created: 2026 October 07

# Change: Discard Stale Input and Allow for Protocol Search

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-dc52c4e4"
  title: "send_command discards stale input before writing and returns only the text before the first '>'; the initialisation 0100 uses a 5 s timeout"
  date: "2026-10-07"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-dc52c4e4"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-dc52c4e4"
  description: "Resolves issue-dc52c4e4."

scope:
  summary: "Two small edits in the transport skeleton and one in OBD initialisation, plus tests."
  affected_components:
    - name: "OBDTransport"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "SerialTransport"
      file_path: "src/gtach/comm/serial_transport.py"
      change_type: "modify"
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_response_alignment.py (new)"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Response parsing of 010C."
    - "The strict 0100 check of issue-907de6de (kept)."
    - "SimTransport (overrides send_command)."

rational:
  problem_statement: "See issue-dc52c4e4."
  proposed_solution: >
    EDIT A — transport.py: new primitive OBDTransport._discard_input(handle)
    -> int. Default: while select.select([handle], [], [], 0) reports the
    handle readable, handle.recv(4096); stop on b'' (EOF is left for the
    read loop to detect) or after 64 reads; return bytes discarded. Any
    TypeError, ValueError, AttributeError or OSError (e.g. a test double
    or closed handle) returns 0. send_command calls it after acquiring
    the handle and before the write, and logs a DEBUG record when bytes
    were discarded.

    EDIT B — transport.py send_command: after the read loop, keep only
    the bytes before the first b'>' (data after it is discarded with a
    DEBUG record).

    EDIT C — serial_transport.py: override _discard_input with
    handle.in_waiting then handle.reset_input_buffer().

    EDIT D — obd.py: class constant _INIT_0100_TIMEOUT_S = 5.0; the 0100
    in _initialize_protocol uses it. The read deadline (6 s with the
    existing margin) stays below the watchdog warning threshold (15 s).
  alternatives_considered:
    - option: "Relax the 0100 check back to 'any response'."
      reason_rejected: "Reintroduces the false initialisation success fixed by issue-907de6de."
  benefits:
    - "A late reply affects at most the command it belongs to."
  risks:
    - risk: "Discarding input that belongs to the current command."
      mitigation: "Discard runs before the write, so nothing for the new command can be pending yet."

technical_details:
  current_behavior: "Late replies are read by the next command; misalignment persists."
  proposed_behavior: "Each command starts with an empty input buffer and reads to its own prompt."
  implementation_approach: "Edits A to D."
  code_changes:
    - component: "OBDTransport"
      file: "src/gtach/comm/transport.py"
      change_summary: "_discard_input; truncate at first '>'"
      functions_affected: ["send_command", "_discard_input"]
      classes_affected: ["OBDTransport"]
    - component: "SerialTransport"
      file: "src/gtach/comm/serial_transport.py"
      change_summary: "_discard_input override"
      functions_affected: ["_discard_input"]
      classes_affected: ["SerialTransport"]
    - component: "OBDProtocol"
      file: "src/gtach/comm/obd.py"
      change_summary: "5 s timeout for initialisation 0100"
      functions_affected: ["_initialize_protocol"]
      classes_affected: ["OBDProtocol"]
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests with a socketpair-backed transport subclass."
  test_cases:
    - scenario: "Stale bytes ('4100...\\r>') pending before ATZ."
      expected_result: "ATZ returns its own reply; stale bytes discarded."
    - scenario: "Buffer holds 'OK\\r\\r>4100...' after one read."
      expected_result: "send_command returns 'OK'."
    - scenario: "Handle without fileno (test double)."
      expected_result: "_discard_input returns 0; send_command unchanged."
    - scenario: "_initialize_protocol sends 0100 with timeout 5.0."
      expected_result: "Asserted via a recording transport."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Edits A to D and tests."
      owner: "planner (this session)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Deploy with ./bin/deploy.sh."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude (planner session, approved by William Watson)"
  verification_date: "2026-10-07"
  verified_by: "William Watson"
  test_results: "Edits A-D implemented; tests/test_response_alignment.py added (8 tests). Pre-commit check in a stub environment: 8/8 pass; the late-reply test fails with the discard step disabled. Full suite on the Mac 2026-10-07: 463 passed, 2 xfailed."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-907de6de"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-dc52c4e4"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-dc52c4e4 iteration 1."
  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved; implemented in this session."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial change document. |
| 1.1 | 2026-10-07 | Approved and implemented. |

---

Copyright (c) 2026 William Watson. MIT License.
