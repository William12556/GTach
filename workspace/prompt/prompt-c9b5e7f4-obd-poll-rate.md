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
  id: "prompt-c9b5e7f4"
  task_type: "debug"
  source_ref: "change-c9b5e7f4"
  date: "2026-05-08"
  iteration: 1
  coupled_docs:
    change_ref: "change-c9b5e7f4"
    change_iteration: 1

context:
  purpose: >
    Make OBD poll interval configurable per transport type, replacing the
    hard-coded 100ms sleep with a 50ms default and 20ms for fast transports.
  integration: >
    OBDProtocol (src/gtach/comm/obd.py) polls the transport in a tight loop
    with a fixed sleep. GTachApplication._start_obd (src/gtach/app.py)
    instantiates OBDProtocol. The poll interval should be passed from app.py
    based on the active transport type.
  knowledge_references: []
  constraints:
    - "Default poll_interval_s=0.05 — existing callers unaffected"
    - "No changes to transport layer, thread management, or display"
    - "sim/TCP transports use 0.02s; RFCOMM/serial use default"

specification:
  requirements:
    functional:
      - "OBDProtocol.__init__ accepts poll_interval_s=0.05 keyword argument"
      - "self.poll_interval_s stored as instance attribute"
      - "_protocol_loop uses time.sleep(self.poll_interval_s)"
      - "GTachApplication._start_obd passes poll_interval_s=0.02 for simbt, simtcp, tcp transports"
      - "GTachApplication._start_obd uses default for all other transports"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Backward compatible — no interface breaking change"

design:
  architecture: "Configurable poll interval passed at construction"
  components:
    - name: "OBDProtocol.__init__"
      type: "method"
      logic:
        - "Change signature to: def __init__(self, transport, thread_manager, poll_interval_s=0.05)"
        - "Add: self.poll_interval_s = poll_interval_s"

    - name: "OBDProtocol._protocol_loop"
      type: "method"
      logic:
        - "Change: time.sleep(0.1)"
        - "To: time.sleep(self.poll_interval_s)"

    - name: "GTachApplication._start_obd"
      type: "method"
      logic:
        - "Determine transport type from self._args.transport"
        - "fast_transports = ('simbt', 'simtcp', 'tcp')"
        - "poll_interval = 0.02 if transport_arg in fast_transports else 0.05"
        - "Pass: OBDProtocol(self._transport, self._thread_manager, poll_interval_s=poll_interval)"

  dependencies:
    internal:
      - "src/gtach/comm/obd.py"
      - "src/gtach/app.py"
    external: []

deliverables:
  - file: "src/gtach/comm/obd.py"
    changes: "poll_interval_s parameter; replace sleep constant"
  - file: "src/gtach/app.py"
    changes: "pass poll_interval_s based on transport type"

success_criteria:
  - "TX:010C log entries appear at ~40-50 Hz for simbt/tcp transports"
  - "No regression for RFCOMM transport"
  - "No queue full errors in log"
```

---

## 2. Tactical Brief

```yaml
tactical_brief: |
  Make OBD poll interval configurable; reduce to 20ms for fast transports.

  Files to modify:
    src/gtach/comm/obd.py
    src/gtach/app.py

  Changes:

  1. src/gtach/comm/obd.py — OBDProtocol.__init__
     Change signature:
       def __init__(self, transport: OBDTransport, thread_manager: ThreadManager):
     To:
       def __init__(self, transport: OBDTransport, thread_manager: ThreadManager, poll_interval_s: float = 0.05):
     Add after self.timeout = 1.0:
       self.poll_interval_s = poll_interval_s

  2. src/gtach/comm/obd.py — OBDProtocol._protocol_loop
     Change:
       time.sleep(0.1)
     To:
       time.sleep(self.poll_interval_s)

  3. src/gtach/app.py — GTachApplication._start_obd
     After: transport_arg = getattr(self._args, 'transport', None)
     Add:
       _fast_transports = ('simbt', 'simtcp', 'tcp')
       _poll_interval = 0.02 if transport_arg in _fast_transports else 0.05
     Change:
       self._obd = OBDProtocol(self._transport, self._thread_manager)
     To:
       self._obd = OBDProtocol(self._transport, self._thread_manager, poll_interval_s=_poll_interval)

  Hard constraints:
  - Default must remain 0.05 for backward compatibility
  - Do not modify transport, thread manager, or display files

  Success: TX:010C at ~40-50 Hz for simbt in log
```

---

## 3. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
