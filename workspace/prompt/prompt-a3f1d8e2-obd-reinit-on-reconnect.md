Created: 2026 May 08

---

## Table of Contents

- [1. Prompt Information](<#1. prompt information>)
- [2. Tactical Brief](<#2. tactical brief>)
- [3. Version History](<#3. version history>)

---

## 1. Prompt Information

```yaml
prompt_info:
  id: "prompt-a3f1d8e2"
  task_type: "debug"
  source_ref: "change-a3f1d8e2"
  date: "2026-05-08"
  iteration: 1
  coupled_docs:
    change_ref: "change-a3f1d8e2"
    change_iteration: 1

context:
  purpose: >
    Eliminate 5-9 second RPM data gap on transport reconnect by skipping the
    ATZ hardware reset command when the adapter has already been initialised.
  integration: >
    OBDProtocol (src/gtach/comm/obd.py) manages the ELM327 adapter init
    sequence. _initialize_protocol() currently sends ATZ on every connect
    including reconnects. A simple boolean flag distinguishes first connect
    from reconnect.
  knowledge_references: []
  constraints:
    - "ATZ must still be sent on first connect and after explicit stop/start"
    - "No changes to transport layer or thread management"
    - "Flag reset must occur when transport disconnects (inner loop exits)"

specification:
  requirements:
    functional:
      - "OBDProtocol.__init__ sets self._adapter_initialised = False"
      - "_initialize_protocol skips ATZ when self._adapter_initialised is True"
      - "_initialize_protocol sets self._adapter_initialised = True on successful 0100 response"
      - "stop() resets self._adapter_initialised = False"
      - "_protocol_loop resets self._adapter_initialised = False after inner while loop exits"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Thread-safe (flag written only from obd_thread; read only from obd_thread)"
        - "No interface changes"

design:
  architecture: "First-connect flag pattern"
  components:
    - name: "OBDProtocol._adapter_initialised"
      type: "instance attribute"
      purpose: "Track whether adapter has been successfully initialised at least once"
      logic:
        - "Initialised to False in __init__"
        - "Set to True after successful _initialize_protocol"
        - "Reset to False in stop() and after inner loop exits"

    - name: "OBDProtocol._initialize_protocol"
      type: "method"
      purpose: "Conditional ATZ"
      logic:
        - "If not self._adapter_initialised: send ATZ with 5s timeout, then update heartbeat"
        - "Continue with ATE0, ATL0, ATS0, ATSP0, 0100 regardless"
        - "On successful return: set self._adapter_initialised = True"

    - name: "OBDProtocol._protocol_loop"
      type: "method"
      purpose: "Reset flag on transport disconnect"
      logic:
        - "After 'while self.transport.is_connected()' loop exits, add:"
        - "  self._adapter_initialised = False"
        - "  self.logger.debug('Transport disconnected — adapter init flag reset')"

    - name: "OBDProtocol.stop"
      type: "method"
      purpose: "Reset flag on explicit stop"
      logic:
        - "Add self._adapter_initialised = False before or after shutdown_event.set()"

  dependencies:
    internal:
      - "src/gtach/comm/obd.py"
    external: []

deliverables:
  - file: "src/gtach/comm/obd.py"
    changes: "_adapter_initialised flag; conditional ATZ; resets in stop and _protocol_loop"

success_criteria:
  - "ATZ appears in log only on first connect and after stop/restart"
  - "RPM resumes within 2 seconds of transport reconnect"
  - "No regressions in normal connect behaviour"
```

---

## 2. Tactical Brief

```yaml
tactical_brief: |
  Skip ATZ on OBD reconnect to eliminate 5-9s RPM data gap.

  File to modify: src/gtach/comm/obd.py

  Changes:

  1. OBDProtocol.__init__
     Add after self.timeout = 1.0:
       self._adapter_initialised = False

  2. OBDProtocol._initialize_protocol
     Current start:
       self.thread_manager.update_heartbeat('obd_protocol')
       self._send_command(b"ATZ", timeout=5.0)
       self.thread_manager.update_heartbeat('obd_protocol')
     Replace with:
       self.thread_manager.update_heartbeat('obd_protocol')
       if not self._adapter_initialised:
           self._send_command(b"ATZ", timeout=5.0)
           self.thread_manager.update_heartbeat('obd_protocol')
     At the end of the try block, after "return True", add before return:
       self._adapter_initialised = True

  3. OBDProtocol._protocol_loop
     After the inner "while self.transport.is_connected():" loop exits
     (i.e. after the inner while block, before the outer except),
     add:
       self._adapter_initialised = False
       self.logger.debug("Transport disconnected — adapter init flag reset")

  4. OBDProtocol.stop
     Add before or after self.shutdown_event.set():
       self._adapter_initialised = False

  Hard constraints:
  - Do not modify transport layer, thread manager, or display files
  - Flag is only read/written from obd_thread — no lock needed

  Success: ATZ absent from log on reconnect; RPM resumes within 2 seconds
```

---

## 3. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
