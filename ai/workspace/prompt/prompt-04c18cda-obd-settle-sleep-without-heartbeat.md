Created: 2026 October 09

# Prompt: Interruptible OBD Settle With Heartbeats

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-04c18cda"
  task_type: "debug"
  source_ref: "change-04c18cda"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-04c18cda"
    change_iteration: 1

context:
  purpose: "Remove the 1.5 s heartbeat gap and the uninterruptible wait in the pre-initialised settle."
  integration: "src/gtach/comm/obd.py; tests/test_lifecycle_sim.py; tests/test_obd_settle.py."
  knowledge_references:
    - "ai/workspace/issues/issue-04c18cda-obd-settle-sleep-without-heartbeat.md"
    - "ai/workspace/change/change-04c18cda-obd-settle-sleep-without-heartbeat.md"
  constraints:
    - "CRITICAL: do not use a single shutdown_event.wait(1.5); the heartbeat gap must not exceed 0.5 s (the issue's proposed approach is superseded by the change)."
    - "Keep the total settle at 1.5 s."
    - "Change only the adapter_pre_initialised branch of _initialize_protocol and add two class constants."
    - "Requires change-50bf25ad already applied."
    - "Line numbers in the issue are stale; locate code by symbol."
    - "Python 3.9+; PEP 8."

specification:
  description: "Sliced, interruptible settle with a heartbeat after each slice; remove the TestWatchdogQuiet strict xfail."
  requirements:
    functional:
      - "Settle lasts 1.5 s when not interrupted; heartbeat at least every 0.5 s."
      - "If shutdown_event is set during the settle, _initialize_protocol returns False within one slice and sends no further command."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "time.monotonic() for the deadline"
        - "Professional docstrings and comments citing issue-04c18cda"
  performance:
    - target: "Largest heartbeat gap in the settle ≤ 0.5 s"
      metric: "time"

design:
  architecture: "Bounded wait loop on shutdown_event."
  components:
    - name: "OBDProtocol class constants"
      type: "constant"
      purpose: "_PRE_INIT_SETTLE_S: float = 1.5; _SETTLE_SLICE_S: float = 0.5"
    - name: "OBDProtocol._initialize_protocol (pre-initialised branch)"
      type: "function"
      purpose: "Replace time.sleep(1.5)."
      logic:
        - "self.logger.debug(f'Skipping ATZ — adapter pre-initialised; settling {self._PRE_INIT_SETTLE_S}s')"
        - "deadline = time.monotonic() + self._PRE_INIT_SETTLE_S"
        - "Loop: remaining = deadline - time.monotonic(); break when remaining <= 0"
        - "if self.shutdown_event.wait(min(self._SETTLE_SLICE_S, remaining)): log DEBUG 'Settle interrupted by stop'; return False"
        - "self.thread_manager.update_heartbeat('obd_protocol')"
    - name: "tests/test_lifecycle_sim.py"
      type: "module"
      purpose: "Remove the strict xfail decorator from TestWatchdogQuiet.test_no_obd_unresponsive_warning."
    - name: "tests/test_obd_settle.py"
      type: "module"
      purpose: "Regression tests (create; extend if it already exists)."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged; the existing try/except in _initialize_protocol is kept."
  exceptions: []
  logging:
    level: "DEBUG"
    format: "Unchanged style"

testing:
  unit_tests:
    - scenario: "OBDProtocol(SimTransport connected, ThreadManager, adapter_pre_initialised=True); record update_heartbeat('obd_protocol') call times (monkeypatch) during _initialize_protocol()."
      expected: "Returns True; max gap between recorded heartbeats ≤ 0.6 s; total call duration ≥ 1.4 s."
    - scenario: "Same setup; a thread sets shutdown_event after 0.2 s."
      expected: "Returns False within 0.7 s; transport received no ATE0 (spy on send_command)."
    - scenario: "tests/test_lifecycle_sim.py::TestWatchdogQuiet::test_no_obd_unresponsive_warning without xfail."
      expected: "Passes."
  edge_cases:
    - "shutdown_event already set on entry: returns False immediately."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/comm/obd.py"
      content: "Constants and settle loop"
    - path: "tests/test_lifecycle_sim.py"
      content: "xfail removed from TestWatchdogQuiet.test_no_obd_unresponsive_warning"
    - path: "tests/test_obd_settle.py"
      content: "Regression tests"

success_criteria:
  - "grep -n 'time.sleep(1.5)' src/gtach/comm/obd.py returns nothing."
  - "No xfail marker remains in tests/test_lifecycle_sim.py."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "obd"
        path: "src/gtach/comm/obd.py"
    classes:
      - name: "OBDProtocol"
        module: "gtach.comm.obd"
    functions:
      - name: "_initialize_protocol"
        module: "gtach.comm.obd.OBDProtocol"
        signature: "_initialize_protocol(self) -> bool"
    constants:
      - name: "_PRE_INIT_SETTLE_S"
        module: "gtach.comm.obd.OBDProtocol"
        type: "float"
      - name: "_SETTLE_SLICE_S"
        module: "gtach.comm.obd.OBDProtocol"
        type: "float"

notes: "Human verification on the Pi: after setup completes, the first OBD connection initialises and RPM appears."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-04c18cda iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
