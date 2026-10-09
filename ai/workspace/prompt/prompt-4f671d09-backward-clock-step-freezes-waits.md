Created: 2026 October 09

# Prompt: Clock-Step-Safe Waits for Supervision Loops

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-4f671d09"
  task_type: "debug"
  source_ref: "change-4f671d09"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-4f671d09"
    change_iteration: 1

context:
  purpose: "Timed waits in the transport, watchdog and OBD loops are not extended by a backward wall-clock step on Python 3.9."
  integration: "New src/gtach/utils/waits.py; edits to comm/transport.py, core/watchdog.py, comm/obd.py; new tests/test_monotonic_waits.py."
  knowledge_references:
    - "ai/workspace/issues/issue-4f671d09-backward-clock-step-freezes-waits.md"
    - "ai/workspace/change/change-4f671d09-backward-clock-step-freezes-waits.md"
  constraints:
    - "CRITICAL: wait_for_event must never call event.wait() or any timed lock acquire. Slicing Event.wait does NOT fix the defect: each slice has an absolute CLOCK_REALTIME deadline on Python < 3.11. Use only event.is_set(), time.sleep and time.monotonic."
    - "Replace exactly six calls: transport.py reconnect_indefinitely (three _shutdown.wait), watchdog.py _monitor_loop (_stop_event.wait), obd.py _protocol_loop (shutdown_event.wait(_INIT_RETRY_DELAY_S)) and _initialize_protocol (settle-slice wait). Keep each caller's use of the return value."
    - "Do not change app.py, interface.py, splash.py, async_operations.py or any join() call (out of scope per the change)."
    - "Do not add an import of gtach.utils.waits to gtach/utils/__init__.py; import the module directly where used."
    - "Line numbers are from b464bee; locate code by symbol."

specification:
  description: "Sleep-polled event wait per change-4f671d09."
  requirements:
    functional:
      - "wait_for_event(event, timeout) returns True as soon as event.is_set() is observed, False once time.monotonic() passes the deadline."
      - "Wall-clock steps have no effect on how long it waits."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Module docstring cites issue-4f671d09 and explains why Event.wait is avoided"
        - "Type hints; mypy src/ stays at 0 errors"
        - "black, isort, flake8 clean on changed files"
  performance:
    - target: "Wake-up latency after set() <= _POLL_SLICE_S (0.1 s)"
      metric: "time"

design:
  architecture: "One stateless helper; call sites swap one expression each."
  components:
    - name: "wait_for_event"
      type: "function"
      purpose: "Clock-step-safe replacement for threading.Event.wait(timeout)."
      interface:
        inputs:
          - name: "event"
            type: "threading.Event (anything with is_set())"
            description: "Event to observe."
          - name: "timeout"
            type: "float"
            description: "Seconds of elapsed (monotonic) time to wait."
        outputs:
          type: "bool"
          description: "True if the event is set, else False."
        raises: []
      logic:
        - "If event.is_set(): return True."
        - "deadline = time.monotonic() + timeout."
        - "Loop: remaining = deadline - time.monotonic(); if remaining <= 0: return event.is_set(); time.sleep(min(_POLL_SLICE_S, remaining)); if event.is_set(): return True."
    - name: "reconnect_indefinitely docstring"
      type: "function"
      purpose: "Replace the sentence saying every wait is on _shutdown rather than time.sleep with one stating waits use wait_for_event (issue-4f671d09) and observe shutdown within one slice."
    - name: "tests/test_monotonic_waits.py"
      type: "module"
      purpose: "Helper and call-site regression tests. Module docstring lists issue-4f671d09."
  dependencies:
    internal:
      - "gtach.utils.waits"
    external: []

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged at call sites. The helper raises nothing of its own."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "Event already set."
      expected: "True; time.sleep not called (spy)."
    - scenario: "Another thread sets the event after ~0.2 s; timeout 5 s."
      expected: "True; elapsed < 0.2 + 0.1 + 0.2 margin."
    - scenario: "Never set; timeout 0.3 s."
      expected: "False; 0.3 <= elapsed < 0.6."
    - scenario: "Object with only is_set() (no wait attribute)."
      expected: "Works."
    - scenario: "reconnect_indefinitely on a minimal OBDTransport subclass whose connect() fails; _shutdown replaced by an Event subclass whose wait() raises AssertionError; set the event from a timer thread; retry_delay small."
      expected: "Returns; no AssertionError."
    - scenario: "Same double on WatchdogMonitor._stop_event; _check_thread_health patched to set it; call _monitor_loop directly."
      expected: "Returns; no AssertionError."
    - scenario: "Same double on OBDProtocol.shutdown_event: (a) _initialize_protocol fails once, then the event is set; (b) adapter_pre_initialised=True settle with the event set before the call."
      expected: "(a) _protocol_loop returns, no AssertionError; (b) _initialize_protocol returns False."
  edge_cases:
    - "timeout <= 0: return event.is_set() without sleeping."
  validation:
    - "Run each call-site test against the unmodified source first and confirm it fails (AssertionError); report the result."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/utils/waits.py"
      content: "New helper"
    - path: "src/gtach/comm/transport.py"
      content: "Three waits replaced; docstring sentence updated"
    - path: "src/gtach/core/watchdog.py"
      content: "One wait replaced"
    - path: "src/gtach/comm/obd.py"
      content: "Two waits replaced"
    - path: "tests/test_monotonic_waits.py"
      content: "Regression tests"

success_criteria:
  - "grep shows no '.wait(' in reconnect_indefinitely, _monitor_loop, _protocol_loop or _initialize_protocol."
  - "Call-site tests fail on the old source and pass on the new."
  - "pytest tests/ passes; mypy src/ 0 errors."

element_registry:
  source: ""
  entries:
    modules:
      - name: "gtach.utils.waits"
        path: "src/gtach/utils/waits.py"
    classes:
      - name: "OBDTransport"
        module: "gtach.comm.transport"
      - name: "WatchdogMonitor"
        module: "gtach.core.watchdog"
      - name: "OBDProtocol"
        module: "gtach.comm.obd"
    functions:
      - name: "wait_for_event"
        module: "gtach.utils.waits"
        signature: "wait_for_event(event: threading.Event, timeout: float) -> bool"
    constants:
      - name: "_POLL_SLICE_S"
        module: "gtach.utils.waits"
        type: "float (0.1)"

notes: "Human verification on gtach.local: repeat the issue reproduction steps (NTP off, -1 h, wait 2 min, +2 h); no 'Thread transport appears unresponsive' warning; adapter off/on after a backward step reconnects without Reset."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-4f671d09 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
