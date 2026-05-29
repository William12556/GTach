Created: 2026 May 28

# Prompt a3f1d8e2 — Skip ATZ on OBD Reconnect After Setup

---

## Table of Contents

[1.0 Prompt Information](<#1.0 prompt information>)
[2.0 Context](<#2.0 context>)
[3.0 Specification](<#3.0 specification>)
[4.0 Design](<#4.0 design>)
[5.0 Error Handling](<#5.0 error handling>)
[6.0 Deliverables](<#6.0 deliverables>)
[7.0 Success Criteria](<#7.0 success criteria>)
[8.0 Tactical Brief](<#8.0 tactical brief>)
[Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-a3f1d8e2"
  task_type: "debug"
  source_ref: "change-a3f1d8e2"
  date: "2026-05-28"
  iteration: 1
  status: "closed"
  coupled_docs:
    change_ref: "change-a3f1d8e2"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    OBDProtocol sends ATZ on the first reconnect after the setup wizard completes.
    The setup probe (BluetoothPairing) already ran ATZ and ATSP0. A second ATZ
    causes a timeout because the adapter is not ready immediately after the probe
    disconnects. This change skips ATZ on the post-setup OBD connection only.
  integration: >
    OBDProtocol is constructed in app.py._start_obd (called from _on_setup_complete)
    and in app.py._start_normal_mode. Only the _start_obd path requires
    adapter_pre_initialised=True. The _start_normal_mode path remains unchanged.
  constraints:
    - "Do not alter setup wizard, BluetoothPairing, or transport layer"
    - "Mid-session disconnect/reconnect behaviour must be preserved (ATZ is sent)"
    - "500ms settle delay (time.sleep(0.5)) in _protocol_loop must be removed"
    - "No new public API surface beyond the constructor parameter"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Add adapter_pre_initialised parameter to OBDProtocol.__init__. When True,
    _adapter_initialised is pre-set so ATZ is skipped on the first connection.
    In app.py._start_obd, pass adapter_pre_initialised=True so post-setup
    reconnects do not repeat the ATZ already performed by the setup probe.
    Remove the 500ms settle delay workaround from _protocol_loop.
  requirements:
    functional:
      - "OBDProtocol accepts adapter_pre_initialised: bool = False in __init__"
      - "_adapter_initialised is initialised to adapter_pre_initialised value"
      - "app._start_obd passes adapter_pre_initialised=True to OBDProtocol"
      - "500ms time.sleep(0.5) removed from _protocol_loop after connect check"
      - "Mid-session disconnects still clear _adapter_initialised and send ATZ on next connect"
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Parameter injection — caller signals pre-initialised state at construction"
  components:
    - name: "OBDProtocol.__init__"
      type: "function"
      purpose: "Accept and apply adapter_pre_initialised flag"
      logic:
        - "Add adapter_pre_initialised: bool = False parameter"
        - "Set self._adapter_initialised = adapter_pre_initialised"
        - "Existing self._adapter_initialised = False line is replaced, not added alongside"

    - name: "OBDProtocol._protocol_loop"
      type: "function"
      purpose: "Remove 500ms settle delay"
      logic:
        - "Remove: time.sleep(0.5) and its comment after the is_connected() check"
        - "The block should read: if not connected: sleep(0.1); continue — then directly call _initialize_protocol"

    - name: "GTachApplication._start_obd"
      type: "function"
      purpose: "Pass adapter_pre_initialised=True after successful setup"
      logic:
        - "Current line (158): self._obd = OBDProtocol(self._transport, self._thread_manager, poll_interval_s=_poll_interval)"
        - "Replace with: self._obd = OBDProtocol(self._transport, self._thread_manager, poll_interval_s=_poll_interval, adapter_pre_initialised=True)"
        - "_start_normal_mode (line 177) constructs OBDProtocol without the flag — leave unchanged"

  dependencies:
    internal:
      - "src/gtach/comm/obd.py"
      - "src/gtach/app.py"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: "No new error paths introduced. Existing exception handling in _protocol_loop is unchanged."
  logging:
    level: "INFO"
    format: "Log adapter_pre_initialised value at OBDProtocol start for diagnostic traceability"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Save changes directly to specified file paths"
    - "Do not alter any other files"
  files:
    - path: "src/gtach/comm/obd.py"
      content: "Modified __init__ and _protocol_loop as specified"
    - path: "src/gtach/app.py"
      content: "Modified _start_obd OBDProtocol construction call"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "OBDProtocol.__init__ signature includes adapter_pre_initialised: bool = False"
  - "_adapter_initialised is set to adapter_pre_initialised at construction, not hardcoded False"
  - "500ms time.sleep(0.5) and its comment are absent from _protocol_loop"
  - "_start_obd constructs OBDProtocol with adapter_pre_initialised=True"
  - "_start_normal_mode OBDProtocol construction is unchanged"
  - "No other files modified"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Modify two files to skip ATZ on OBD reconnect after setup wizard.

  FILE 1: src/gtach/comm/obd.py

  1. In OBDProtocol.__init__, add parameter adapter_pre_initialised: bool = False.
     Replace the line:
       self._adapter_initialised = False
     with:
       self._adapter_initialised = adapter_pre_initialised
     Add log line after: self.logger.info(f"OBDProtocol init — adapter_pre_initialised={adapter_pre_initialised}")

  2. In OBDProtocol._protocol_loop, remove the 500ms settle delay and its comment:
       # Brief settle after connect — allow emulator/adapter to be ready
       time.sleep(0.5)
     These two lines are located immediately after the is_connected() / continue block.

  FILE 2: src/gtach/app.py

  3. In _start_obd (line ~158), replace:
       self._obd = OBDProtocol(self._transport, self._thread_manager, poll_interval_s=_poll_interval)
     with:
       self._obd = OBDProtocol(self._transport, self._thread_manager, poll_interval_s=_poll_interval, adapter_pre_initialised=True)

  Do NOT modify _start_normal_mode or any other file.

  Success: __init__ signature has adapter_pre_initialised param; _protocol_loop has no 500ms sleep; _start_obd passes adapter_pre_initialised=True.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-28 | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
