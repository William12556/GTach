Created: 2026 July 30

# Prompt: Report the Shutdown Budget Overrun, Join Outside the State Lock, Stop the OBD Thread Before Joining It

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-2d545bf5"
  task_type: "debug"
  source_ref: "change-2d545bf5"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-2d545bf5"
    change_iteration: 1

context:
  purpose: >
    Three corrections in the thread-lifecycle path. ThreadManager.shutdown
    floors the per-thread join timeout at 1.0 s and can silently exceed
    the caller's aggregate budget. ThreadManager.stop_thread performs its
    join while holding _state_lock, contrary to the comment immediately
    above it, so every other thread's heartbeat blocks for the join's
    duration. GTachApplication._re_enter_setup joins the OBD thread
    before doing anything that could make the join succeed, so the full
    5.0 s always elapses on a UI-driven callback and the thread is not
    stopped.
  integration: >
    Two files: src/gtach/core/thread.py and src/gtach/app.py. Three
    edits. Executor is Claude Code; AEL is not used.

    ORDERING FACTS, verified against source, that the fix depends on.
    ThreadManager.stop_thread sets no event and does not call the
    stop_func recorded at core/thread.py:132. OBDProtocol's inner polling
    loop is bounded by transport.is_connected() (comm/obd.py:79) and its
    outer loop by shutdown_event (comm/obd.py:68); when the transport is
    down the outer loop sleeps 0.1 s and continues rather than returning
    (comm/obd.py:72-74). So disconnecting the transport alone does not
    end the thread, and calling OBDProtocol.stop alone does not either.
    Both are needed, in that order — which is precisely what
    GTachApplication.shutdown already documents at app.py:295-300 and
    performs at app.py:307-310.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/core/thread.py and src/gtach/app.py."
    - "Do NOT modify src/gtach/comm/obd.py. Its inner loop's exit condition is a known related observation owned by no triple yet; see change-2d545bf5 out_of_scope."
    - "Do NOT modify src/gtach/core/watchdog.py. Its lock discipline was corrected by change-5a9dc15e."
    - "Do NOT modify GTachApplication.shutdown (app.py:286-316). Its sequence is correct and is the model being copied."
    - "Do NOT remove the 1.0 s floor at core/thread.py:355. Report when it engages; keep max(1.0, ...)."
    - "Do NOT change the existing 'ThreadManager shutdown complete' log line at core/thread.py:374-377."
    - "Do NOT change stop_thread's early returns, its state transition, its restart cancellation, or the 'if name in self.threads' guard at core/thread.py:318."
    - "Do NOT work around worker_pool.shutdown's unbounded wait at core/thread.py:347. Python 3.9 has no timeout parameter, as the comment at core/thread.py:345 records."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Log the aggregate budget overrun in ThreadManager.shutdown; move
    ThreadManager.stop_thread's join outside the _state_lock block; give
    GTachApplication._re_enter_setup the shutdown sequence that makes its
    join succeed.
  requirements:
    functional:
      - "shutdown logs a WARNING when self.threads is non-empty and remaining_timeout / len(self.threads) is below 1.0."
      - "The WARNING carries the requested timeout, the remaining time, the thread count, the per-thread value in force and the projected worst-case total."
      - "shutdown logs no such WARNING when the quotient is at or above 1.0, or when no thread is registered."
      - "per_thread_timeout remains max(1.0, ...) — the floor is reported, not removed."
      - "stop_thread's join is executed with _state_lock released."
      - "stop_thread re-acquires _state_lock only for the final status write, as it does today."
      - "_re_enter_setup disconnects the transport, then calls OBDProtocol.stop, then calls stop_thread('obd_protocol') with an explicit timeout."
      - "Each of those three steps tolerates failure without preventing the others or the subsequent _start_setup_mode call."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "A UI-driven setup re-entry completes in well under 1.5 s instead of always taking 5 s"
      metric: "time"
    - target: "update_heartbeat, register_thread and get_thread_status are not blocked for the duration of any join"
      metric: "time"

design:
  architecture: >
    A wait is not performed while holding a lock the awaited party needs.
    change-5a9dc15e established that rule for core/watchdog.py against
    findings §3.3 and §4.1; core/thread.py has the same defect in
    stop_thread and it is corrected the same way. A budget that a floor
    can override is reported rather than silently substituted. A caller
    that wants a thread stopped arranges the conditions under which it
    can stop, in the order the subsystem requires.
  components:
    - name: "ThreadManager.shutdown"
      type: "function"
      purpose: "Say when the per-thread floor has abandoned the caller's budget."
      interface:
        inputs:
          - name: "timeout"
            type: "float"
            description: "Aggregate shutdown budget in seconds. Default 10.0."
        outputs:
          type: "None"
          description: "Unchanged."
        raises:
          - "None. Unchanged."
      logic:
        - "Bind the unfloored quotient to a local before applying max(1.0, ...)."
        - "Emit a WARNING when self.threads is non-empty and that quotient is below 1.0."
        - "Leave every other statement of the method as it is."
    - name: "ThreadManager.stop_thread"
      type: "function"
      purpose: "Join without holding the shared state lock."
      logic:
        - "Close the 'with self._state_lock:' block after the restart-future cancellation."
        - "De-indent the join, the success test, the nested status write and the return by one level."
        - "Move the existing comment to the same level, so it describes what the code does."
    - name: "GTachApplication._re_enter_setup"
      type: "function"
      purpose: "Stop the OBD subsystem in the order that works, then re-enter setup."
      logic:
        - "Disconnect the transport under its existing hasattr and try guards."
        - "Call OBDProtocol.stop under a hasattr guard and its own try."
        - "Call stop_thread('obd_protocol', timeout=2.0)."
        - "Reset _obd_started and call _start_setup_mode, as now."
  dependencies:
    internal:
      - "OBDProtocol.stop — comm/obd.py:58-64; called from a second site, not modified."
      - "OBDTransport.disconnect — called earlier in the sequence; no transport implementation is modified."
      - "WatchdogMonitor — uses thread_manager._lock, which is _state_lock (core/thread.py:111); it benefits from the lock-scope correction and is not modified."
    external: []

error_handling:
  strategy: >
    Each step of the re-entry sequence is independently guarded, so a
    fault in one does not prevent the rest, matching the existing
    tolerance for a failing transport disconnect at app.py:223-224. The
    budget warning is a log, never an exception: a shutdown that cannot
    meet its budget must still shut down.
  exceptions:
    - exception: "Exception"
      condition: "Transport disconnect fails during re-entry."
      handling: "logger.warning, as now; continue to the OBD stop."
    - exception: "Exception"
      condition: "OBDProtocol.stop fails during re-entry."
      handling: "logger.warning; continue to stop_thread."
    - exception: "Exception"
      condition: "Anything else in _re_enter_setup."
      handling: "The existing outer handler at app.py:228-229 logs at ERROR with exc_info."
  logging:
    level: "WARNING"
    format: "self.logger.warning(f'...')"

testing:
  unit_tests:
    - scenario: "A thread that will not exit; stop_thread on one thread, update_heartbeat for a different registered thread on another."
      expected: "update_heartbeat returns while the join is still running. Before the change it blocks for the whole join."
    - scenario: "Same, with get_thread_status on the second thread."
      expected: "Returns promptly."
    - scenario: "Three registered threads; shutdown(timeout=2.0)."
      expected: "A WARNING naming the 2.0 s request, three threads, 1.0 s each and a 3.0 s worst case."
    - scenario: "Three registered threads; shutdown(timeout=10.0), worker pool instantaneous."
      expected: "No such WARNING. The quotient is 3.333."
    - scenario: "No registered threads; shutdown(timeout=0.5)."
      expected: "No WARNING."
    - scenario: "Worker pool patched to consume longer than the budget."
      expected: "A WARNING whose reported remaining time is negative."
    - scenario: "shutdown on a healthy manager."
      expected: "All threads stopped; self.threads and self._active_futures cleared; the 'ThreadManager shutdown complete' line unchanged in form."
    - scenario: "stop_thread('nosuchthread')."
      expected: "False, logged, no join attempted."
    - scenario: "stop_thread on a thread already in a terminal state."
      expected: "Returns from the can_transition_to branch as before, no join attempted."
    - scenario: "_re_enter_setup with recording stubs for _transport, _obd and _thread_manager."
      expected: "Order is transport.disconnect, obd.stop, thread_manager.stop_thread."
    - scenario: "Inspect the stop_thread call site in _re_enter_setup."
      expected: "timeout=2.0 passed explicitly."
    - scenario: "_transport.disconnect raises."
      expected: "obd.stop and stop_thread still run; a WARNING is logged."
    - scenario: "_obd.stop raises."
      expected: "stop_thread still runs and _start_setup_mode is still called."
    - scenario: "No _obd attribute."
      expected: "The other steps run; _start_setup_mode is called."
    - scenario: "No _transport and no _thread_manager attribute."
      expected: "_start_setup_mode is called."
  edge_cases:
    - "len(self.threads) is 0 — max(1, len(...)) already prevents a division by zero, and the WARNING is suppressed because there is no per-thread work to overrun."
    - "remaining_timeout negative — the quotient is negative, below the floor, so the WARNING fires and reports the negative figure rather than hiding it."
    - "self.threads mutated between stop_thread's two lock acquisitions — the existing 'if name in self.threads' guard covers it; thread_info is a local bound before the release, so the join is unaffected."
    - "_re_enter_setup called twice in quick succession — the second finds the thread already stopped, so stop_thread returns from its terminal-state branch without joining."
    - "OBDProtocol.stop's own 5.0 s join — with the transport already disconnected the outer loop reaches its shutdown_event test within one 0.1 s sleep, or within one 1.0 s send_command timeout if it is mid-request."
  validation:
    - "grep confirms stop_thread contains exactly two 'with self._state_lock:' statements and that neither encloses the join."
    - "AST or indentation check confirms every statement from 'success = True' to the closing 'return success' is at method-body level."

deliverable:
  format_requirements:
    - "Edit both files in place. Create no new file."
    - "Apply the three edits below. Change nothing else."
  files:
    - path: "src/gtach/core/thread.py"
      content: |
        EDIT 1 — shutdown budget warning

        Replace core/thread.py:353-355:

                # Stop all managed threads with proper state transitions
                with self._cleanup_lock:
                    remaining_timeout = timeout - (time.time() - shutdown_start)
                    per_thread_timeout = max(1.0, remaining_timeout / max(1, len(self.threads)))

        with:

                # Stop all managed threads with proper state transitions
                with self._cleanup_lock:
                    remaining_timeout = timeout - (time.time() - shutdown_start)
                    thread_count = len(self.threads)
                    budgeted_per_thread = remaining_timeout / max(1, thread_count)
                    per_thread_timeout = max(1.0, budgeted_per_thread)

                    # The floor guarantees each join a usable timeout and in
                    # doing so abandons the caller's aggregate budget. Say
                    # so rather than substituting it silently (core review
                    # §5.5). The __del__ path reaches this with a 2.0s
                    # budget and three threads — 0.667s each — so the
                    # overrun does not require a slow worker pool.
                    if thread_count and budgeted_per_thread < 1.0:
                        self.logger.warning(
                            f"Shutdown budget exceeded: {timeout:.1f}s requested, "
                            f"{remaining_timeout:.1f}s remaining for {thread_count} "
                            f"thread(s) ({budgeted_per_thread:.2f}s each); flooring at "
                            f"{per_thread_timeout:.1f}s, worst case "
                            f"{per_thread_timeout * thread_count:.1f}s"
                        )

        Leave the loop at core/thread.py:357-368 and the completion log at
        core/thread.py:370-377 exactly as they are.

        EDIT 2 — stop_thread joins outside the state lock

        The method currently reads, from core/thread.py:293:

                with self._state_lock:
                    if name not in self.threads:
                        ...
                    thread_info.status = ThreadStatus.STOPPING

                    # Cancel any pending restart
                    if thread_info.restart_future and not thread_info.restart_future.done():
                        thread_info.restart_future.cancel()

                # Join thread outside of lock to prevent deadlock
                    success = True
                    if thread_info.thread.is_alive():
                        thread_info.thread.join(timeout=timeout)
                        success = not thread_info.thread.is_alive()

                    # Update final status
                    with self._state_lock:
                        ...
                    return success

        The comment is at column 8 but everything after it is at column
        12, so it is still inside the 'with self._state_lock:' block and
        the join holds the lock — blocking update_heartbeat,
        register_thread and get_thread_status for its whole duration.
        _state_lock is an RLock (core/thread.py:92), which is why the
        nested re-acquisition does not self-deadlock and the fault is
        invisible.

        De-indent by one level every statement from 'success = True'
        through the closing 'return success', so they follow the with
        block rather than sitting inside it, and replace the comment with
        one that states the reason:

                # Join outside the lock. update_heartbeat, register_thread
                # and get_thread_status all take _state_lock, so joining
                # under it blocks the very threads whose progress the join
                # is waiting on — the same defect corrected in
                # core/watchdog.py by change-5a9dc15e. thread_info is
                # bound above, so the join is unaffected by the release.
                success = True
                if thread_info.thread.is_alive():
                    thread_info.thread.join(timeout=timeout)
                    success = not thread_info.thread.is_alive()

                # Update final status
                with self._state_lock:
                    if name in self.threads:
                        self.threads[name].status = ThreadStatus.STOPPED if success else ThreadStatus.FAILED

                if success:
                    self.logger.debug(f"Successfully stopped thread: {name}")
                else:
                    self.logger.warning(f"Thread {name} did not stop within {timeout}s")

                return success

        Everything above the comment — the early returns, the state
        transition and the restart cancellation — keeps its current text
        and its current indentation inside the with block.
    - path: "src/gtach/app.py"
      content: |
        EDIT 3 — _re_enter_setup performs the sequence that works

        Replace app.py:215-227:

                    self.logger.info("Re-entering setup from DISCONNECTED screen")
                    # Stop OBD if running
                    if hasattr(self, '_thread_manager'):
                        self._thread_manager.stop_thread('obd_protocol')
                    # Explicitly disconnect transport — it is not registered with ThreadManager
                    if hasattr(self, '_transport'):
                        try:
                            self._transport.disconnect()
                        except Exception as e:
                            self.logger.warning(f"Transport disconnect on re-entry: {e}")
                    self._obd_started = False
                    # Re-enter setup
                    self._start_setup_mode()

        with:

                    self.logger.info("Re-entering setup from DISCONNECTED screen")

                    # Same sequence as shutdown() (app.py:295-310), and for
                    # the same reason. ThreadManager.stop_thread sets no
                    # event and does not call the registered stop_func, so
                    # it can only join. OBDProtocol's inner loop is bounded
                    # by transport.is_connected() (obd.py:79) and its outer
                    # loop by shutdown_event (obd.py:68), and when the
                    # transport is down the outer loop sleeps and continues
                    # rather than returning (obd.py:72-74). Disconnecting
                    # alone does not end the thread and stopping alone does
                    # not either — both are required, in this order.
                    # Previously the join came first, could never succeed,
                    # and ran to its 5s default on a UI callback while
                    # holding the thread-state lock (core review §5.9).

                    # 1. Transport — closes the socket, releasing the OBD
                    #    thread from any blocking read.
                    if hasattr(self, '_transport'):
                        try:
                            self._transport.disconnect()
                        except Exception as e:
                            self.logger.warning(f"Transport disconnect on re-entry: {e}")

                    # 2. OBD — sets shutdown_event, which is the only thing
                    #    that ends _protocol_loop.
                    if hasattr(self, '_obd'):
                        try:
                            self._obd.stop()
                        except Exception as e:
                            self.logger.warning(f"OBD stop on re-entry: {e}")

                    # 3. Thread manager — bookkeeping. The thread is already
                    #    dead by now, so this records STOPPED rather than
                    #    FAILED. 2.0s rather than the 5.0s default because
                    #    this runs on a UI-driven callback and a join that
                    #    needs longer than that indicates a fault worth
                    #    seeing in the log.
                    if hasattr(self, '_thread_manager'):
                        self._thread_manager.stop_thread('obd_protocol', timeout=2.0)

                    self._obd_started = False
                    # Re-enter setup
                    self._start_setup_mode()

        Leave the surrounding try and its handler at app.py:228-229
        unchanged, and change no other method in the file. In particular
        GTachApplication.shutdown must remain byte-identical.

success_criteria:
  - "python -m py_compile src/gtach/core/thread.py src/gtach/app.py passes."
  - "pytest tests/ passes with no new failures."
  - "Every statement from 'success = True' to the closing 'return success' in stop_thread is at method-body indentation."
  - "stop_thread contains exactly two 'with self._state_lock:' statements and neither encloses the join."
  - "A second thread can call update_heartbeat while stop_thread is joining, and returns without waiting for the join."
  - "per_thread_timeout is still max(1.0, ...)."
  - "shutdown logs a WARNING for three threads and a 2.0 s budget, and does not for three threads and a 10.0 s budget with an instantaneous worker pool."
  - "shutdown logs no WARNING when no thread is registered."
  - "The 'ThreadManager shutdown complete' log line is byte-identical to its current text."
  - "_re_enter_setup calls _transport.disconnect, then _obd.stop, then _thread_manager.stop_thread, in that order."
  - "_re_enter_setup passes timeout=2.0 to stop_thread."
  - "Each of the three steps is individually guarded so a failure in one does not prevent the others or _start_setup_mode."
  - "GTachApplication.shutdown is byte-identical to its current text."
  - "src/gtach/comm/obd.py is unmodified."
  - "src/gtach/core/watchdog.py is unmodified."
  - "No file other than src/gtach/core/thread.py and src/gtach/app.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "thread"
        path: "src/gtach/core/thread.py"
      - name: "app"
        path: "src/gtach/app.py"
      - name: "obd"
        path: "src/gtach/comm/obd.py"
      - name: "watchdog"
        path: "src/gtach/core/watchdog.py"
    classes:
      - name: "ThreadManager"
        module: "gtach.core.thread"
      - name: "ThreadStatus"
        module: "gtach.core.thread"
      - name: "ThreadInfo"
        module: "gtach.core.thread"
      - name: "GTachApplication"
        module: "gtach.app"
      - name: "OBDProtocol"
        module: "gtach.comm.obd"
    functions:
      - name: "shutdown"
        module: "gtach.core.thread"
        signature: "shutdown(self, timeout: float = 10.0) -> None"
      - name: "stop_thread"
        module: "gtach.core.thread"
        signature: "stop_thread(self, name: str, timeout: float = 5.0) -> bool"
      - name: "update_heartbeat"
        module: "gtach.core.thread"
        signature: "update_heartbeat(self, name: str) -> None"
      - name: "_re_enter_setup"
        module: "gtach.app"
        signature: "_re_enter_setup(self) -> None"
      - name: "stop"
        module: "gtach.comm.obd"
        signature: "stop(self) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-2d545bf5-thread-shutdown-budget.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  The re-entry effect is only observable while the transport is still
  connected, which is not the usual state when the DISCONNECTED screen
  is on show. To reproduce it on target, reach OPTIONS with the
  transport up and use Clear settings, which invokes the same callback
  through display/manager.py:1286-1288.

  core/thread.py was left unmodified by change-5a9dc15e, which corrected
  core/watchdog.py alone. This is the first change to modify it.

  Two related observations are deliberately excluded and are recorded in
  change-2d545bf5 under out_of_scope: OBDProtocol's inner loop does not
  test shutdown_event, and ThreadManager.stop_thread never calls the
  stop_func it records at registration. Either would be a better general
  fix than the ordering this change relies on, and both need designing
  rather than patching. Do not implement either here.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-2d545bf5. |
| 1.1 | 2026-07-31 | Executed by Claude Code. All three edits applied and all sixteen success criteria met, with no departure from the prompt's text required. 53 assertions against a real ThreadManager with real threads and recording stubs for the re-entry path, all passing; pytest tests/ 11 passed. The lock defect was measured rather than argued: with a 2.0 s join 0.2 s underway, update_heartbeat for a different registered thread blocked 1803.5 ms against the pre-change code and 0.1 ms after — the watchdog reads thread state through the same lock, so a join could previously stall the mechanism meant to detect stalls. Run against the pre-change files the suite fails nineteen of forty-eight assertions. Recorded in change-2d545bf5. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/; the issue and change remain active pending on-target results per ai/task.md §8.2.1. |

---

Copyright (c) 2026 William Watson. MIT License.
