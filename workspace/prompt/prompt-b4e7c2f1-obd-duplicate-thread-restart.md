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
  id: "prompt-b4e7c2f1"
  task_type: "debug"
  source_ref: "change-b4e7c2f1"
  date: "2026-05-08"
  iteration: 1
  coupled_docs:
    change_ref: "change-b4e7c2f1"
    change_iteration: 1

context:
  purpose: >
    Fix duplicate OBD polling threads caused by ThreadManager._restart_thread spawning
    a replacement thread without stopping the original OBDProtocol thread.
  integration: >
    ThreadManager (src/gtach/core/thread.py) manages thread lifecycle including restart
    on watchdog timeout. OBDProtocol (src/gtach/comm/obd.py) runs the OBD polling loop.
    OBDProtocol owns a shutdown_event that its loop polls; ThreadManager has no reference
    to this event and cannot stop the original thread before restarting.
  knowledge_references: []
  constraints:
    - "register_thread signature change must be backward-compatible (stop_func=None default)"
    - "OBDProtocol.stop must be idempotent"
    - "No changes to WatchdogMonitor, transport layer, or display components"

specification:
  description: >
    Add an optional stop_func callable to ThreadInfo. ThreadManager._restart_thread
    calls stop_func() before spawning a replacement thread if stop_func is set.
    OBDProtocol passes self.stop as stop_func when registering its thread.
  requirements:
    functional:
      - "ThreadInfo stores stop_func: Optional[Callable] = None"
      - "ThreadManager.register_thread accepts optional stop_func kwarg; stores on ThreadInfo"
      - "ThreadManager._restart_thread calls stop_func() before creating new thread if set"
      - "OBDProtocol.__init__ passes stop_func=self.stop to register_thread"
      - "OBDProtocol.stop guards obd_thread.join with is_alive() check"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Thread-safe"
        - "Comprehensive error handling"
        - "Debug logging"

design:
  architecture: "Stop-before-restart pattern via optional stop callable stored on ThreadInfo"
  components:
    - name: "ThreadInfo.stop_func"
      type: "dataclass field"
      purpose: "Store optional callable that cleanly stops the thread before restart"
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Added field: stop_func: Optional[Callable] = None"
        raises: []
      logic:
        - "Add field after target_kwargs in ThreadInfo dataclass"
        - "Import Callable from typing (already present)"

    - name: "ThreadManager.register_thread"
      type: "method"
      purpose: "Accept and store stop_func at registration time"
      interface:
        inputs:
          - name: "stop_func"
            type: "Optional[Callable]"
            description: "Callable that stops the thread cleanly. Default None."
        outputs:
          type: "None"
          description: "No return value change"
        raises: []
      logic:
        - "Add stop_func=None to signature after thread parameter"
        - "After creating thread_info, set thread_info.stop_func = stop_func"

    - name: "ThreadManager._restart_thread"
      type: "method"
      purpose: "Stop original thread before starting replacement"
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "No return value change"
        raises: []
      logic:
        - "After backoff sleep, before 'Atomic transition to restarting state' block:"
        - "If thread_info.stop_func is not None, call thread_info.stop_func()"
        - "Log: logger.debug(f'Called stop_func for {name} before restart')"
        - "Wrap stop_func call in try/except; log error but do not abort restart on failure"

    - name: "OBDProtocol.__init__"
      type: "method"
      purpose: "Register stop_func so ThreadManager can stop the thread on restart"
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "No signature change"
        raises: []
      logic:
        - "Change: self.thread_manager.register_thread('obd_protocol', self.obd_thread)"
        - "To: self.thread_manager.register_thread('obd_protocol', self.obd_thread, stop_func=self.stop)"

    - name: "OBDProtocol.stop"
      type: "method"
      purpose: "Idempotent stop — safe to call before thread started or after already stopped"
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "No return value change"
        raises: []
      logic:
        - "Set self.shutdown_event.set() unconditionally (already present)"
        - "Guard join: only call self.obd_thread.join(timeout=5.0) if self.obd_thread.is_alive()"

  dependencies:
    internal:
      - "src/gtach/core/thread.py"
      - "src/gtach/comm/obd.py"
    external: []

deliverables:
  - file: "src/gtach/core/thread.py"
    changes: "ThreadInfo.stop_func field; register_thread stop_func kwarg; _restart_thread stop call"
  - file: "src/gtach/comm/obd.py"
    changes: "register_thread call updated; stop() idempotency guard"

success_criteria:
  - "No paired SimTransport TX:010C lines in log after any obd_protocol restart event"
  - "RPM sweep remains on a single smooth trajectory after restart"
  - "All existing callers of register_thread unaffected (stop_func defaults to None)"
  - "No regressions in setup thread or display thread behaviour"
```

---

## 2. Tactical Brief

```yaml
tactical_brief: |
  Fix duplicate OBD polling threads after watchdog restart.

  Files to modify:
    src/gtach/core/thread.py
    src/gtach/comm/obd.py

  Changes required:

  1. src/gtach/core/thread.py — ThreadInfo dataclass
     Add field after target_kwargs:
       stop_func: Optional[Callable] = None

  2. src/gtach/core/thread.py — ThreadManager.register_thread
     Change signature:
       def register_thread(self, name: str, thread: threading.Thread) -> None:
     To:
       def register_thread(self, name: str, thread: threading.Thread, stop_func=None) -> None:
     After creating thread_info, add:
       thread_info.stop_func = stop_func

  3. src/gtach/core/thread.py — ThreadManager._restart_thread
     Inside the with self._state_lock block, after the backoff sleep loop and before
     "Verify we're still in a restartable state", add:
       if thread_info.stop_func is not None:
           try:
               self.logger.debug(f"Calling stop_func for {name} before restart")
               thread_info.stop_func()
           except Exception as e:
               self.logger.error(f"stop_func failed for {name}: {e}")

  4. src/gtach/comm/obd.py — OBDProtocol.__init__
     Change:
       self.thread_manager.register_thread('obd_protocol', self.obd_thread)
     To:
       self.thread_manager.register_thread('obd_protocol', self.obd_thread, stop_func=self.stop)

  5. src/gtach/comm/obd.py — OBDProtocol.stop
     Change:
       self.obd_thread.join(timeout=5.0)
     To:
       if self.obd_thread.is_alive():
           self.obd_thread.join(timeout=5.0)

  Hard constraints:
  - stop_func default must be None (backward compatible)
  - Do not modify WatchdogMonitor, transport, or display files
  - stop_func call must be wrapped in try/except

  Success: no paired TX:010C lines in log after obd_protocol restart
```

---

## 3. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
