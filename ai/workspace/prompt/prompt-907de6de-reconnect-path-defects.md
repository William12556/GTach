Created: 2026 October 07

# Prompt: Reconnect-Path Corrections

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-907de6de"
  task_type: "debug"
  source_ref: "change-907de6de"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-907de6de"
    change_iteration: 1

context:
  purpose: >
    Correct six defects on the OBD reconnect path: invalid init
    acceptance, busy init retry, handle leak and missing cause on peer
    close, Bluetooth-only diagnoses applied to all transports, serial
    dead-peer detection, and RPM decoding without a PID check.
  integration: "src/gtach/comm/obd.py, transport.py, rfcomm.py; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-907de6de-reconnect-path-defects.md"
    - "ai/workspace/change/change-907de6de-reconnect-path-defects.md"
  constraints:
    - "The init back-off must wait on shutdown_event, never time.sleep, and must heartbeat before waiting."
    - "Do not change drop_link, disconnect, reconnect_indefinitely, the read deadline or _record_timeout."
    - "Partial serial responses without '>' are still returned unchanged."
    - "Do not change pairing.py, system_bluetooth.py, serial_transport.py port discovery or tcp_transport.py."
    - "Do not modify src/gtach/display/manager_backup.py or setup_original_backup.py."
    - "Every logger .error/.critical in a broad handler passes exc_info=True (tests/test_logging_policy.py)."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to F of change-907de6de and add tests/test_reconnect_path.py."
  requirements:
    functional:
      - "Init succeeds only if the 0100 response contains '4100' after removing whitespace and upper-casing."
      - "After an init failure the loop waits _INIT_RETRY_DELAY_S (2.0 s) on shutdown_event."
      - "Peer close (EOF read) calls drop_link with cause 'adapter closed the connection'."
      - "Only transports with _ADAPTER_CHECKS True report 'no bluetooth controller' or the wedge cause; RFCOMMTransport sets it True."
      - "An empty read on a non-EOF transport with nothing buffered counts as a timeout."
      - "_request_rpm decodes only responses whose second byte is 0x0C."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Local corrections; no structural change."
  components:
    - name: "EDIT A — _initialize_protocol"
      type: "function"
      purpose: "Validate 0100."
      logic:
        - "Replace `if not response or response.startswith('7F'): raise Exception(\"No connection to vehicle\")` with: `normalised = re.sub(r'\\s', '', (response or '').upper())`; `if '4100' not in normalised: raise Exception(f\"No valid 0100 response: {response!r}\")`."
    - name: "EDIT B — _protocol_loop back-off"
      type: "function"
      purpose: "No busy retry."
      logic:
        - "Class constant `_INIT_RETRY_DELAY_S: float = 2.0` on OBDProtocol."
        - "Replace `if not self._initialize_protocol(): continue` with: `if not self._initialize_protocol(): self.thread_manager.update_heartbeat('obd_protocol'); self.shutdown_event.wait(self._INIT_RETRY_DELAY_S); continue`."
    - name: "EDIT C — EOF branch"
      type: "function"
      purpose: "Close the handle and record a cause."
      logic:
        - "Module constant `_PEER_CLOSED_CAUSE = 'adapter closed the connection'` beside _SILENT_LINK_CAUSE, with a one-line comment."
        - "In send_command's `if self._EMPTY_READ_IS_EOF:` branch: keep `logger.error(\"Connection closed by device\")`, replace the `with self._lock: self._state = ...` block with `self.drop_link(cause=_PEER_CLOSED_CAUSE)`, then `return None`."
    - name: "EDIT D — opt-in adapter checks"
      type: "class"
      purpose: "Bluetooth diagnoses for Bluetooth only."
      logic:
        - "OBDTransport: `_ADAPTER_CHECKS: bool = False` with a comment: only Bluetooth transports may report adapter faults (audit A05)."
        - "RFCOMMTransport: `_ADAPTER_CHECKS = True`."
        - "_classify_connect_error: `if self._ADAPTER_CHECKS and not _bluetooth_adapter_present(): return 'no bluetooth controller'`."
        - "connect(): add `self._ADAPTER_CHECKS and` as the first term of the wedge-escalation condition."
    - name: "EDIT E — serial empty read"
      type: "function"
      purpose: "Make serial dead-peer detection work."
      logic:
        - "In the non-EOF path (currently `break`): `if not buf: return self._record_timeout(command, timeout)`; else `break`."
    - name: "EDIT F — PID check"
      type: "function"
      purpose: "Decode RPM only from PID 0C."
      logic:
        - "After `data = bytes.fromhex(hex_str)`: `if len(data) < 4 or data[0] != 0x41 or data[1] != self.RPM_PID: return None`."

data_schema:
  entities: []

error_handling:
  strategy: "Existing handlers retained."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "_initialize_protocol (adapter_pre_initialised False) against a stub transport answering ATZ 'ELM327 v1.5', AT commands 'OK', and 0100 each of: '41 00 BE 3E B8 11', '4100BE3EB811', 'SEARCHING...\\r41 00 BE 3E B8 11'."
      expected: "True for each."
    - scenario: "Same with 0100 → 'NO DATA', 'UNABLE TO CONNECT', '?', '7F 01 12', None."
      expected: "False for each."
    - scenario: "_protocol_loop with _initialize_protocol patched to return False, False, then set shutdown_event; shutdown_event.wait wrapped to record its argument."
      expected: "wait called with 2.0 at least twice; loop exits."
    - scenario: "OBDTransport stub (_EMPTY_READ_IS_EOF True) connected; _read returns b''; send_command('010C', timeout=0.2)."
      expected: "None; handle closed; is_connected() False; last_failure_cause == 'adapter closed the connection'."
    - scenario: "Stub with _ADAPTER_CHECKS False; _bluetooth_adapter_present patched False; _open raises OSError(ECONNREFUSED) six times."
      expected: "last_failure_cause is never 'no bluetooth controller' or the wedge cause."
    - scenario: "Same stub with _ADAPTER_CHECKS True."
      expected: "'no bluetooth controller' (behaviour preserved for Bluetooth)."
    - scenario: "Stub with _EMPTY_READ_IS_EOF False; _read returns b'' always; five send_command calls (timeout 0.1)."
      expected: "drop_link called exactly once; is_connected() False."
    - scenario: "Stub with _EMPTY_READ_IS_EOF False; _read returns b'41 0C 1A F8' then b''."
      expected: "Returns '41 0C 1A F8'."
    - scenario: "_request_rpm with stub responses '41 0D 1A F8' and '41 0C 1A F8'."
      expected: "None; then OBDResponse with data == b'\\x1a\\xf8'."
  edge_cases:
    - "RFCOMMTransport._ADAPTER_CHECKS is True; TCPTransport and SerialTransport inherit False."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit existing files in place; add one test module."
    - "In tests/test_connect_error_classification.py set `_ADAPTER_CHECKS = True` on _StubTransport with a comment that it models the RFCOMM transport. Change nothing else there."
  files:
    - path: "src/gtach/comm/obd.py"
      content: "EDITS A, B, F"
    - path: "src/gtach/comm/transport.py"
      content: "EDITS C, D, E"
    - path: "src/gtach/comm/rfcomm.py"
      content: "EDIT D"
    - path: "tests/test_reconnect_path.py"
      content: "testing.unit_tests"
    - path: "tests/test_connect_error_classification.py"
      content: "_StubTransport opt-in"

success_criteria:
  - "'startswith(\\'7F\\')' no longer appears in obd.py; '4100' validation present."
  - "OBDProtocol._INIT_RETRY_DELAY_S == 2.0 and the loop waits on shutdown_event after init failure."
  - "The EOF branch calls drop_link(cause=_PEER_CLOSED_CAUSE)."
  - "OBDTransport._ADAPTER_CHECKS is False; RFCOMMTransport._ADAPTER_CHECKS is True."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "obd"
        path: "src/gtach/comm/obd.py"
      - name: "transport"
        path: "src/gtach/comm/transport.py"
      - name: "rfcomm"
        path: "src/gtach/comm/rfcomm.py"
    classes:
      - name: "OBDProtocol"
        module: "gtach.comm.obd"
      - name: "OBDTransport"
        module: "gtach.comm.transport"
      - name: "RFCOMMTransport"
        module: "gtach.comm.rfcomm"
    functions: []
    constants:
      - name: "_PEER_CLOSED_CAUSE"
        module: "gtach.comm.transport"
        type: "str"
      - name: "_INIT_RETRY_DELAY_S"
        module: "gtach.comm.obd"
        type: "float"
      - name: "_ADAPTER_CHECKS"
        module: "gtach.comm.transport"
        type: "bool"

notes: >
  Human verification with the ELM327 emulator: vehicle off (0100 → NO
  DATA) must not log init success and must retry every 2 s; stopping the
  emulator so it closes the socket must show 'adapter closed the
  connection' on the DISCONNECTED screen.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-907de6de iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
