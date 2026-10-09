Created: 2026 October 09

# Prompt: Bounded EBUSY Retry in Post-Pairing OBD Verify

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-d26ca557"
  task_type: "debug"
  source_ref: "change-d26ca557"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-d26ca557"
    change_iteration: 1

context:
  purpose: "The post-pairing OBD verify retries a link-busy RFCOMM connect instead of failing on the first attempt."
  integration: "comm/transport.py (constant only); display/setup_components/bluetooth/interface.py; new tests/test_obd_verify_busy_retry.py."
  knowledge_references:
    - "ai/workspace/issues/issue-d26ca557-obd-verify-ebusy-after-pairing.md"
    - "ai/workspace/change/change-d26ca557-obd-verify-ebusy-after-pairing.md"
  constraints:
    - "Implement after prompt-4f671d09; both edit transport.py and interface.py (4f671d09 changes ensure_pairing_initialized only)."
    - "Retry ONLY when transport.last_failure_cause == LINK_BUSY_CAUSE. Any other failure returns False after one attempt."
    - "transport.py: add LINK_BUSY_CAUSE and use it in _CONNECT_FAULT_CAUSES; no other edit to that file in this change."
    - "Do not change start_device_probe, the pairing-success callback, or RFCOMMTransport."
    - "Line numbers are from b464bee; locate code by symbol."

specification:
  description: "Busy-only bounded retry per change-d26ca557."
  requirements:
    functional:
      - "Up to _VERIFY_BUSY_ATTEMPTS (3) connect attempts while the cause is link-busy, _VERIFY_BUSY_RETRY_DELAY_S (1.0) apart."
      - "Each retry logs at INFO: 'OBD verify: link busy, retrying (attempt n/3)'."
      - "Success path (ATZ probe, disconnect in finally) unchanged."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Comment at the class constants citing issue-d26ca557"
        - "mypy src/ stays at 0 errors; black, isort, flake8 clean on changed files"
  performance: []

design:
  architecture: "Loop around connect() inside verify_obd_connection, reusing one transport instance."
  components:
    - name: "LINK_BUSY_CAUSE"
      type: "constant"
      purpose: "Single definition of the EBUSY cause string, shared by the mapping and the caller."
    - name: "BluetoothSetupInterface.verify_obd_connection"
      type: "function"
      purpose: "Retry on link-busy."
      logic:
        - "transport = RFCOMMTransport(device.mac_address, channel=1)."
        - "for attempt in 1..N: if transport.connect(): break; if transport.last_failure_cause != LINK_BUSY_CAUSE or attempt == N: log the existing warning, return False; log INFO retry; time.sleep(delay)."
        - "Then the existing ATZ try/finally block."
    - name: "tests/test_obd_verify_busy_retry.py"
      type: "module"
      purpose: "Retry behaviour tests. Module docstring lists issue-d26ca557."
  dependencies:
    internal:
      - "gtach.comm.transport.LINK_BUSY_CAUSE"
    external: []

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged outer try/except."
  exceptions: []
  logging:
    level: "INFO for retries; existing WARNING on final failure"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "Busy, then success; ATZ reply 'ELM327 v1.5'."
      expected: "True; 2 connects; time.sleep called once with 1.0; disconnect called."
    - scenario: "Failure with 'connection timed out'."
      expected: "False; 1 connect; no sleep."
    - scenario: "Busy three times."
      expected: "False; 3 connects; 2 sleeps."
    - scenario: "LINK_BUSY_CAUSE vs _CONNECT_FAULT_CAUSES[errno.EBUSY]."
      expected: "Equal."
  edge_cases:
    - "The verify passes through when _pairing_factory is set or socket lacks AF_BLUETOOTH: tests must use monkeypatch.setattr(socket, 'AF_BLUETOOTH', 31, raising=False) and an instance with _pairing_factory None."
    - "Construct the interface without triggering the async Bluetooth init (e.g. BluetoothSetupInterface.__new__ plus the attributes verify_obd_connection reads: logger, device_store stub, _pairing_factory=None)."
    - "Patch gtach.comm.rfcomm.RFCOMMTransport (imported inside the function) with a fake; patch time.sleep in interface.py's namespace or globally."
  validation:
    - "Run the busy-then-success test against the unmodified source first and confirm it fails; report the result."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/comm/transport.py"
      content: "LINK_BUSY_CAUSE constant"
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "Bounded busy retry"
    - path: "tests/test_obd_verify_busy_retry.py"
      content: "Regression tests"

success_criteria:
  - "The four tests pass; the busy-then-success test fails on the old source."
  - "pytest tests/ passes; mypy src/ 0 errors."

element_registry:
  source: ""
  entries:
    modules: []
    classes:
      - name: "BluetoothSetupInterface"
        module: "gtach.display.setup_components.bluetooth.interface"
      - name: "RFCOMMTransport"
        module: "gtach.comm.rfcomm"
    functions: []
    constants:
      - name: "LINK_BUSY_CAUSE"
        module: "gtach.comm.transport"
        type: "str"
      - name: "_VERIFY_BUSY_ATTEMPTS"
        module: "gtach.display.setup_components.bluetooth.interface"
        type: "int (3)"
      - name: "_VERIFY_BUSY_RETRY_DELAY_S"
        module: "gtach.display.setup_components.bluetooth.interface"
        type: "float (1.0)"

notes: "Human verification on gtach.local: re-pair the ELM327 emulator several times; setup completes without Retry; error.log may still show one EBUSY line per busy attempt (out of scope)."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-d26ca557 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-09 | Ordering constraint notes the shared interface.py. |

---

Copyright (c) 2026 William Watson. MIT License.
