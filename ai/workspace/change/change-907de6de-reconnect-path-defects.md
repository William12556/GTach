Created: 2026 October 07

# Change: Reconnect-Path Corrections

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-907de6de"
  title: "Require a 41 00 answer to 0100; back off 2 s after init failure; drop_link with a cause on peer close; make adapter classification opt-in (RFCOMM only); count an empty serial read as a timeout; check the PID byte in RPM decoding"
  date: "2026-10-07"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-907de6de"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-907de6de"
  description: "Resolves issue-907de6de (audit-36b6ea95 A02-A06, A19)."

scope:
  summary: "Six small edits in obd.py, transport.py and rfcomm.py, with tests."
  affected_components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "OBDTransport"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "RFCOMMTransport"
      file_path: "src/gtach/comm/rfcomm.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_reconnect_path.py"
      change_type: "add"
    - name: "Classification test stub"
      file_path: "tests/test_connect_error_classification.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Serial port discovery and probing."
    - "Pairing and system_bluetooth modules (A07, A08, A17, A18)."
    - "Partial serial responses without '>' (still returned as today)."
    - "Renaming the module's ConnectionError/TimeoutError classes (A16)."

rational:
  problem_statement: "See issue-907de6de."
  proposed_solution: >
    EDIT A (A02) — _initialize_protocol: after the 0100 command,
    `normalised = re.sub(r'\s', '', (response or '').upper())`; succeed
    only if '4100' in normalised; otherwise raise
    Exception(f"No valid 0100 response: {response!r}") inside the
    existing try (logged with exc_info, returns False).

    EDIT B (A03) — _protocol_loop: when _initialize_protocol() returns
    False, heartbeat, then `self.shutdown_event.wait(self._INIT_RETRY_DELAY_S)`
    before continuing. Class constant _INIT_RETRY_DELAY_S = 2.0.

    EDIT C (A04) — send_command EOF branch: keep the ERROR log, replace
    the state assignment with `self.drop_link(cause=_PEER_CLOSED_CAUSE)`
    and return None. Module constant _PEER_CLOSED_CAUSE =
    'adapter closed the connection', defined beside _SILENT_LINK_CAUSE.

    EDIT D (A05) — class attribute `_ADAPTER_CHECKS: bool = False` on
    OBDTransport; `_ADAPTER_CHECKS = True` on RFCOMMTransport. In
    _classify_connect_error, the 'no bluetooth controller' check runs
    only if self._ADAPTER_CHECKS. In connect(), the wedge escalation
    condition additionally requires self._ADAPTER_CHECKS.

    EDIT E (A06) — send_command non-EOF empty-read branch: if buf is
    empty, `return self._record_timeout(command, timeout)`; otherwise
    break as today.

    EDIT F (A19) — _request_rpm: after `data = bytes.fromhex(hex_str)`,
    return None unless data[0] == 0x41 and data[1] == self.RPM_PID.
  alternatives_considered:
    - option: "Treat a list of ELM error strings as failure."
      reason_rejected: "A positive test for '4100' is shorter and also rejects unlisted errors."
  benefits:
    - "Init reports success only when the vehicle answers."
    - "No busy retry loop."
    - "Every link loss closes its handle and shows a cause."
    - "Correct diagnoses for TCP and serial."
    - "Serial dead-peer detection works."
  risks:
    - risk: "A real ECU answers 0100 in a format without '4100' (e.g. headers on)."
      mitigation: "ATH0 is the ELM default and init sends ATS0; with headers on, '4100' still appears after the header bytes."
    - risk: "Serial reads that time out with no data during slow init commands now count towards a drop."
      mitigation: "Five consecutive empty reads are needed, the same threshold as RFCOMM and TCP."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Line-level edits."
  code_changes:
    - component: "OBDProtocol"
      file: "src/gtach/comm/obd.py"
      change_summary: "EDITS A, B, F"
      functions_affected:
        - "_initialize_protocol"
        - "_protocol_loop"
        - "_request_rpm"
      classes_affected:
        - "OBDProtocol"
    - component: "OBDTransport"
      file: "src/gtach/comm/transport.py"
      change_summary: "EDITS C, D, E"
      functions_affected:
        - "send_command"
        - "_classify_connect_error"
        - "connect"
      classes_affected:
        - "OBDTransport"
    - component: "RFCOMMTransport"
      file: "src/gtach/comm/rfcomm.py"
      change_summary: "EDIT D"
      functions_affected: []
      classes_affected:
        - "RFCOMMTransport"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "DisplayManager DISCONNECTED cause text"
      impact: "May now show 'adapter closed the connection'."
  external: []
  required_changes:
    - change_ref: "change-860fd5f7"
      relationship: "blocked_by. _record_timeout and the read deadline (implemented)."

testing_requirements:
  test_approach: "Unit tests with stub transports and a stub thread manager."
  test_cases:
    - scenario: "_initialize_protocol with 0100 → '41 00 BE 3E B8 11', '4100BE3EB811', 'SEARCHING...\\r41 00 BE 3E B8 11'."
      expected_result: "True."
    - scenario: "_initialize_protocol with 0100 → 'NO DATA', 'UNABLE TO CONNECT', '?', '7F 01 12', None."
      expected_result: "False."
    - scenario: "_protocol_loop with init failing twice then succeeding; shutdown_event.wait patched to record."
      expected_result: "wait called with 2.0 after each failure."
    - scenario: "send_command on an EOF-type stub whose read returns b''."
      expected_result: "Returns None; handle closed; is_connected() False; last_failure_cause == 'adapter closed the connection'."
    - scenario: "Non-adapter stub (_ADAPTER_CHECKS False), no /sys/class/bluetooth, connect raising ECONNREFUSED six times."
      expected_result: "Cause is the errno cause, never 'no bluetooth controller' nor the wedge cause."
    - scenario: "Serial-type stub (_EMPTY_READ_IS_EOF False) returning b'' five times."
      expected_result: "Five warnings; drop_link called once; is_connected() False."
    - scenario: "Serial-type stub returning b'41 0C 1A F8' then b''."
      expected_result: "Returns '41 0C 1A F8' (partial response behaviour unchanged)."
    - scenario: "_request_rpm with '41 0D 1A F8' and with '41 0C 1A F8'."
      expected_result: "None, then an OBDResponse with data b'\\x1a\\xf8'."
  regression_scope:
    - "tests/test_connect_error_classification.py (set _ADAPTER_CHECKS = True on _StubTransport)."
    - "tests/test_link_loss_recovery.py, tests/test_thread_lifecycle.py."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to F and tests."
      owner: "tactical"
    - step: "Emulator: vehicle-off and peer-close scenarios."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-860fd5f7"
      relationship: "blocked_by"
  related_issues:
    - issue_ref: "issue-907de6de"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-907de6de iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

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
| 1.0 | 2026-10-07 | Initial change document. Reconnect-path corrections A02-A06, A19. |
| 1.1 | 2026-10-07 | Approved for implementation. |

---

Copyright (c) 2026 William Watson. MIT License.
