Created: 2026 October 07

# Prompt: Process-Restart Recovery and Bounded OBD Heartbeat Gaps

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-860fd5f7"
  task_type: "debug"
  source_ref: "change-860fd5f7"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-860fd5f7"
    change_iteration: 1

context:
  purpose: >
    Replace in-process thread restart with process-restart recovery,
    make obd_protocol a critical thread, bound the OBD thread's
    heartbeat gaps so it cannot be falsely detected as stalled, and fix
    the OBD stop signal, stop_func handling, dead registry entries and
    the simulation transport's connection state.
  integration: >
    core/thread.py, core/watchdog.py, comm/obd.py, comm/transport.py,
    comm/sim_transport.py, app.py, tests. Implement after
    prompt-fbe7e98a.
  knowledge_references:
    - "ai/workspace/issues/issue-860fd5f7-thread-lifecycle-recovery.md"
    - "ai/workspace/change/change-860fd5f7-thread-lifecycle-recovery.md"
    - "CLAUDE.md §4 rule 8"
  constraints:
    - "CRITICAL: no code path may start a replacement for a registered thread. _restart_thread, handle_thread_failure and _attempt_hard_recovery are deleted."
    - "CRITICAL: the dead-thread rule applies only to threads that have been started (thread.ident is not None). Registered-but-not-started threads must not be marked STOPPED or trigger shutdown."
    - "CRITICAL: _re_enter_setup must stop obd_protocol through ThreadManager.stop_thread, never by calling self._obd.stop() directly, so the entry is STOPPING before the OBD thread exits."
    - "stop_func is called outside _state_lock (CLAUDE.md rule 8)."
    - "Do not change watchdog thresholds, the soft-recovery logic, the advisory tier or the two-phase lock discipline of _check_thread_health (no blocking call in phase 1)."
    - "Do not change GTachApplication.shutdown, drop_link, disconnect or reconnect_indefinitely."
    - "Do not remove worker_pool, _active_futures, ThreadInfo target capture or RecoveryStats fields (Phase 5)."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to F of change-860fd5f7 and add tests/test_thread_lifecycle.py."
  requirements:
    functional:
      - "A stale critical thread (display or obd_protocol) leads to graceful shutdown at critical_timeout; nothing is restarted in process."
      - "A stale non-critical thread produces ERROR logs only."
      - "A started thread that has exited while RUNNING/STARTING is marked STOPPED; if critical, graceful shutdown follows."
      - "stop_thread calls the registered stop_func before joining."
      - "register_thread replaces an entry whose thread is not alive."
      - "The OBD inner loop exits when shutdown_event is set even while connected."
      - "Every OBD command refreshes the obd_protocol heartbeat."
      - "send_command never runs longer than timeout + _READ_DEADLINE_MARGIN_S plus one write; the timeout is applied before the write."
      - "SimTransport reports its real connection state."
      - "Setup re-entry stops 'transport' then 'obd_protocol' via stop_thread."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Professional docstrings"
  performance:
    - target: "Longest heartbeat gap of the OBD thread in normal operation ≤ ATZ timeout + 1 s (about 6 s)"
      metric: "time"

design:
  architecture: >
    Recovery by process restart under systemd. Monitored threads are
    made of bounded steps separated by heartbeats.
  components:
    - name: "EDIT A — ThreadManager"
      type: "class"
      purpose: "No restart; stop_func on stop; replace dead entries."
      logic:
        - "Delete _restart_thread and handle_thread_failure."
        - "stop_thread: after the first with-block (status STOPPING, restart_future cancel kept), and before the join: `stop_func = thread_info.stop_func`; if not None, call it in try/except logging `logger.error(f'stop_func failed for {name}: {e}', exc_info=True)`."
        - "register_thread: inside the lock, if name exists and old.status in {RUNNING, STARTING} and old.thread.is_alive(): keep the existing warning and return. Otherwise, if name exists, log debug 'Replacing stale entry for {name}' and continue to create the new ThreadInfo."
    - name: "EDIT B — WatchdogMonitor"
      type: "class"
      purpose: "Escalation without restart; dead-thread rule; OBD critical."
      logic:
        - "critical_threads = {'display', 'obd_protocol'} with an updated comment."
        - "Delete _attempt_hard_recovery. _handle_recovery_timeout: consecutive_failures == 1 → soft recovery (unchanged); >= 2 → logger.error(f'Thread {name} unresponsive ({timeout:.1f}s); no in-process restart')."
        - "_handle_critical_timeout: critical → unchanged; non-critical → the existing ERROR line only."
        - "_check_thread_health phase 1: before computing heartbeat age, `t = thread_info.thread`; if t.ident is not None and not t.is_alive(): set thread_info.status = ThreadStatus.STOPPED, append ('exited', name, health, 0.0) to pending, and continue."
        - "Phase 2: for 'exited': if name in self.critical_threads: logger.critical(f'Critical thread {name} exited unexpectedly') and self._initiate_graceful_shutdown(f'Critical thread {name} exited'); else logger.info(f'Thread {name} exited; marked STOPPED')."
        - "Update the class docstring escalation list to remove HARD_RECOVERY and describe process restart."
    - name: "EDIT C — OBDProtocol"
      type: "class"
      purpose: "Honour stop; heartbeat per command."
      logic:
        - "_protocol_loop inner loop: `while self.transport.is_connected() and not self.shutdown_event.is_set():`."
        - "_send_command: first statement inside try: `self.thread_manager.update_heartbeat('obd_protocol')`."
    - name: "EDIT D — OBDTransport.send_command"
      type: "function"
      purpose: "Bounded command duration."
      logic:
        - "Class constant `_READ_DEADLINE_MARGIN_S: float = 1.0` with a comment citing change-860fd5f7."
        - "Move `self._set_timeout(handle, timeout)` before `self._write(handle, encoded_cmd)`."
        - "Before the read loop: `deadline = time.monotonic() + timeout + self._READ_DEADLINE_MARGIN_S`."
        - "At the top of each loop iteration: `remaining = deadline - time.monotonic()`; if remaining <= 0: `return self._record_timeout(command, timeout)`; else `self._set_timeout(handle, min(timeout, remaining))`."
        - "Extract the existing `except self._TIMEOUT_ERRORS:` body into `def _record_timeout(self, command: str, timeout: float) -> None` (logger obtained as in send_command); the except branch becomes `return self._record_timeout(command, timeout)`. Behaviour of the timeout path is otherwise unchanged."
        - "Import time if not already imported."
    - name: "EDIT E — SimTransport"
      type: "class"
      purpose: "Real connection state."
      logic:
        - "is_connected: `with self._lock: return self._connected`."
        - "state: CONNECTED if is_connected() else DISCONNECTED."
        - "Update both docstrings."
    - name: "EDIT F — GTachApplication"
      type: "class"
      purpose: "Coherent stop on re-entry."
      logic:
        - "In _start_obd and _start_normal_mode: `self._thread_manager.register_thread('transport', transport_thread, stop_func=self._transport.disconnect)`."
        - "In _re_enter_setup replace steps 1-3 with: `if hasattr(self, '_thread_manager'): self._thread_manager.stop_thread('transport', timeout=2.0); self._thread_manager.stop_thread('obd_protocol', timeout=2.0)`. Keep `self._obd_started = False` and `self._start_setup_mode()`."
        - "Replace the comment block with one describing: transport first (its stop_func closes the socket and releases the OBD thread), then obd_protocol (its stop_func is OBDProtocol.stop); stop_thread marks STOPPING before calling stop_func, so the watchdog never sees a dead critical thread in RUNNING (change-860fd5f7)."

data_schema:
  entities: []

error_handling:
  strategy: "stop_func and callbacks wrapped; exceptions logged with exc_info=True."
  exceptions: []
  logging:
    level: "CRITICAL for a critical thread exiting; ERROR for unresponsive threads; INFO for a non-critical exit"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "WatchdogMonitor with recording shutdown_callback; register 'obd_protocol' (not started) with heartbeat aged critical_timeout + 5 on the monotonic clock; _check_thread_health()."
      expected: "Shutdown callback called once."
    - scenario: "Non-critical, non-advisory 'worker' (not started) aged past critical_timeout; call _check_thread_health() three times, resetting health.last_recovery_time to float('-inf') between calls."
      expected: "ERROR records present; manager.threads['worker'].thread is the original object; no shutdown."
    - scenario: "Critical 'display' thread started with a target that returns immediately, joined, status still RUNNING; _check_thread_health()."
      expected: "Status STOPPED; shutdown callback called once."
    - scenario: "Same for a non-critical name."
      expected: "Status STOPPED; no shutdown; INFO logged."
    - scenario: "Critical 'display' registered, not started, fresh heartbeat."
      expected: "Status unchanged; no shutdown."
    - scenario: "stop_thread('x') where stop_func starts a helper thread that does manager._state_lock.acquire(timeout=1) and records the result, and the registered thread waits on an Event that stop_func sets."
      expected: "stop_func called once; helper recorded True; stop_thread returns True."
    - scenario: "register_thread('x', t2) when the existing 'x' thread has finished but status is RUNNING."
      expected: "manager.threads['x'].thread is t2."
    - scenario: "register_thread('x', t2) when the existing 'x' thread is alive and RUNNING."
      expected: "Entry still holds the original thread; warning logged."
    - scenario: "OBDProtocol(SimTransport connected, ThreadManager()); start(); after 0.3 s call stop() while still connected."
      expected: "obd_thread not alive within 2 s."
    - scenario: "SimTransport: connect(), check, disconnect(), check."
      expected: "is_connected True/False; state CONNECTED/DISCONNECTED."
    - scenario: "OBDTransport subclass with fake _open/_write/_read/_set_timeout where _read returns b'SEARCHING' every call; connect; send_command('0100', timeout=0.2)."
      expected: "Returns None in under 0.2 + 1.0 + 0.5 s; _consecutive_timeouts == 1."
    - scenario: "Same fake recording call order; send_command('010C', timeout=0.2) with _read returning b'41 0C 1A F8\\r>'."
      expected: "First _set_timeout precedes _write; response returned."
    - scenario: "OBDProtocol._send_command(b'ATE0') with a recording thread manager and a stub transport."
      expected: "update_heartbeat('obd_protocol') called once."
    - scenario: "GTachApplication instance created without __init__ (object.__new__), with a recording _thread_manager, stub _transport and _obd, and _start_setup_mode patched; call _re_enter_setup()."
      expected: "stop_thread calls in order ('transport', 2.0) then ('obd_protocol', 2.0); _obd.stop not called directly."
    - scenario: "tests/test_watchdog_process_termination.py TestAdvisoryTier.test_membership."
      expected: "Updated to assert critical_threads == {'display', 'obd_protocol'}."
  edge_cases:
    - "A thread whose stop_func raises: stop_thread still joins and returns the join result."
    - "send_command when the peer sends the full response in one read: no change in behaviour."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit existing files in place; add one test module; update one test assertion."
  files:
    - path: "src/gtach/core/thread.py"
      content: "EDIT A"
    - path: "src/gtach/core/watchdog.py"
      content: "EDIT B"
    - path: "src/gtach/comm/obd.py"
      content: "EDIT C"
    - path: "src/gtach/comm/transport.py"
      content: "EDIT D"
    - path: "src/gtach/comm/sim_transport.py"
      content: "EDIT E"
    - path: "src/gtach/app.py"
      content: "EDIT F"
    - path: "tests/test_thread_lifecycle.py"
      content: "testing.unit_tests"
    - path: "tests/test_watchdog_process_termination.py"
      content: "critical_threads assertion"

success_criteria:
  - "grep -rn '_restart_thread\\|handle_thread_failure\\|_attempt_hard_recovery' src/ returns nothing."
  - "WatchdogMonitor().critical_threads == {'display', 'obd_protocol'}."
  - "The dead-thread rule tests thread.ident is not None."
  - "stop_thread invokes stop_func after releasing _state_lock and before join."
  - "_re_enter_setup contains no direct call to self._obd.stop() or self._transport.disconnect()."
  - "In send_command, _set_timeout precedes _write and the read loop is bounded by a monotonic deadline."
  - "OBDProtocol._send_command calls update_heartbeat('obd_protocol')."
  - "SimTransport.is_connected returns the connection flag."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "thread"
        path: "src/gtach/core/thread.py"
      - name: "watchdog"
        path: "src/gtach/core/watchdog.py"
      - name: "obd"
        path: "src/gtach/comm/obd.py"
      - name: "transport"
        path: "src/gtach/comm/transport.py"
      - name: "sim_transport"
        path: "src/gtach/comm/sim_transport.py"
      - name: "app"
        path: "src/gtach/app.py"
    classes:
      - name: "ThreadManager"
        module: "gtach.core.thread"
      - name: "WatchdogMonitor"
        module: "gtach.core.watchdog"
      - name: "OBDProtocol"
        module: "gtach.comm.obd"
      - name: "OBDTransport"
        module: "gtach.comm.transport"
      - name: "SimTransport"
        module: "gtach.comm.sim_transport"
      - name: "GTachApplication"
        module: "gtach.app"
    functions:
      - name: "stop_thread"
        module: "gtach.core.thread"
        signature: "(self, name: str, timeout: float = 5.0) -> bool"
      - name: "register_thread"
        module: "gtach.core.thread"
        signature: "(self, name: str, thread: threading.Thread, stop_func=None) -> None"
      - name: "_record_timeout"
        module: "gtach.comm.transport"
        signature: "(self, command: str, timeout: float) -> None"
    constants:
      - name: "_READ_DEADLINE_MARGIN_S"
        module: "gtach.comm.transport"
        type: "float"

notes: >
  Human verification: (1) on the development host, run
  `gtach --transport simtcp`, send SIGTERM, and confirm exit within a
  few seconds; (2) on the Pi, a soak test of several hours with link
  losses, adapter power cycles and emulator restarts, after which
  /opt/gtach/error.log must contain no 'appears unresponsive' warning
  for obd_protocol and no unexpected shutdown.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-860fd5f7 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
