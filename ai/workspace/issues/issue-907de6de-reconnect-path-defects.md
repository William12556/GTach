Created: 2026 October 07

# Issue: Reconnect-Path Defects in OBD Initialisation and Transports

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-907de6de"
  title: "OBD init accepts error responses and retries without back-off; peer close leaks the handle and records no cause; Bluetooth fault classification applies to TCP and serial; serial dead-peer detection cannot trip; RPM decoding ignores the PID byte"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-907de6de"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-36b6ea95 findings A02, A03, A04, A05, A06 (medium) and A19 (low); traced end to end in X03."

affected_scope:
  components:
    - name: "OBDProtocol._initialize_protocol / _protocol_loop / _request_rpm"
      file_path: "src/gtach/comm/obd.py"
    - name: "OBDTransport.send_command / _classify_connect_error / connect"
      file_path: "src/gtach/comm/transport.py"
    - name: "RFCOMMTransport"
      file_path: "src/gtach/comm/rfcomm.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "GTach against the ELM327 emulator, a TCP emulator, or a USB-serial adapter."
  steps:
    - "A02/A03: emulator with the vehicle off (0100 → NO DATA): init reports success; with an adapter that answers ATZ but fails 0100, init retries immediately in a loop."
    - "A04: stop the TCP emulator so it closes the socket: the DISCONNECTED screen shows no cause."
    - "A05: six failed connects to a TCP emulator: cause becomes 'bluetooth wedged - reset required'."
    - "A06: power off a USB-serial adapter without unplugging: polling continues indefinitely."
  frequency: "always"
  reproducibility_conditions: "Deterministic from source."
  test_data: >
    obd.py _initialize_protocol: `if not response or response.startswith('7F')`
    accepts 'NO DATA', 'UNABLE TO CONNECT', '?', 'SEARCHING...'. On
    failure the outer loop `continue`s with no wait.

    transport.py send_command, empty read with _EMPTY_READ_IS_EOF True:
    sets DISCONNECTED only; the handle is not closed (connect() later
    overwrites self._handle) and _last_failure_cause is not set.

    transport.py _classify_connect_error and connect(): the
    'no bluetooth controller' check and the wedge escalation run for
    every transport class.

    serial_transport.py: _EMPTY_READ_IS_EOF False; pyserial returns b''
    on timeout; send_command breaks and returns '' as a response, which
    resets _consecutive_timeouts, so drop_link never trips.

    obd.py _request_rpm: checks the '41' prefix but not that data[1] is
    0x0C.
  error_output: "None specific."

behavior:
  expected: >
    Init succeeds only on a valid 0100 answer and retries with a pause;
    every link loss closes the handle and records a cause; adapter
    diagnoses apply to Bluetooth only; a silent serial adapter is
    detected; only PID 0C responses are decoded as RPM.
  actual: "As in test_data. All confirmed in source."
  impact: >
    Misleading 'connected' state with no RPM; CPU and log load on the
    Pi Zero; leaked sockets; wrong remedy shown to the operator;
    permanently stale serial link; possible wrong RPM from a stray
    response.
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Independent gaps on the reconnect path; see test_data."
  technical_notes: >
    tests/test_connect_error_classification.py uses a _StubTransport
    derived from OBDTransport and expects Bluetooth classification. Once
    classification becomes opt-in, that stub must opt in, and a
    non-Bluetooth stub must be tested for the opposite.

    The init back-off waits on shutdown_event so that stop() is not
    delayed, and stays well under the 15 s watchdog warning threshold
    (change-860fd5f7).
  related_issues:
    - issue_ref: "issue-9c2f41d8"
      relationship: "related. drop_link and consecutive-timeout counting reused."
    - issue_ref: "issue-860fd5f7"
      relationship: "related. Bounded heartbeat gaps on the OBD thread."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-907de6de."
  change_ref: "change-907de6de"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Unit tests per defect."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-907de6de."
    - "After the fix: emulator with vehicle off; DISCONNECTED or no-data state, no init-success log; init retries every 2 s."
  verification_results: "First step complete."

traceability:
  design_refs: []
  change_refs:
    - "change-907de6de"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 A02, A03, A04, A05, A06, A19, X03."

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
      - "Initial issue document from audit-36b6ea95 A02-A06, A19."

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
| 1.0 | 2026-10-07 | Initial issue document. Reconnect-path defects A02-A06, A19. |

---

Copyright (c) 2026 William Watson. MIT License.
