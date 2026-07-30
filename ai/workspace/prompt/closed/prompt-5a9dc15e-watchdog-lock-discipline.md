Created: 2026 July 30

# Prompt: Watchdog Lock Discipline

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-5a9dc15e"
  task_type: "refactor"
  source_ref: "change-5a9dc15e"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-5a9dc15e"
    change_iteration: 1

context:
  purpose: >
    Remove every blocking call from inside ThreadManager's state lock in
    WatchdogMonitor. The soft-recovery observation currently holds the lock
    that the monitored thread needs in order to write the heartbeat being
    observed, so the check cannot succeed; and the health-check traversal
    dispatches recovery — including its sleeps — from inside the same lock,
    stalling all thread bookkeeping for seconds at a time.
  integration: >
    One file: src/gtach/core/watchdog.py. Two structural edits. Executor is
    Claude Code; AEL is not used. This is one of the two High severity core
    findings active in the running application (core report §6.0 item 2)
    and is step 3 in the recommended authoring order of ai/task.md §7.6.2.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/core/watchdog.py. Do NOT modify src/gtach/core/thread.py — ThreadManager, its locks and its public API are unchanged."
    - "Do not add a lock. Do not replace thread_manager._lock with a different lock."
    - "Do not change any handler signature: _handle_warning_timeout, _handle_recovery_timeout, _handle_critical_timeout and _reset_thread_health keep their current parameters."
    - "Do not change any threshold, comparison order, timeout value or sleep duration."
    - "Do not change how recovery_stats counters are incremented or where _recovery_lock is acquired."
    - "Leave _attempt_hard_recovery alone. Its time.sleep(2.0) at watchdog.py:273 is already outside the lock."
    - "Leave get_thread_health_status (watchdog.py:347) alone. It traverses under the lock but makes no blocking call."
    - "Leave _emergency_shutdown alone."
    - "Do not make the sleep interruptible or add stop-event handling. Out of scope."
    - "Type hints on all public interfaces; Google-style docstrings; PEP 8."

specification:
  description: >
    Convert _check_thread_health from traverse-and-dispatch to
    collect-then-dispatch, and split the _attempt_soft_recovery heartbeat
    observation into two short critical sections with the sleep between
    them.
  requirements:
    functional:
      - "No time.sleep call in watchdog.py executes while thread_manager._lock is held."
      - "_check_thread_health holds thread_manager._lock only for the traversal that builds the pending-action list."
      - "Every handler that was called before is still called, once, with the same arguments and in the same order."
      - "_attempt_soft_recovery reads last_heartbeat under the lock, sleeps with the lock released, then re-acquires to re-test membership and re-read last_heartbeat."
      - "A thread unregistered during the sleep window is treated as not recovered, with no exception."
      - "Recovery statistics are incremented exactly as they are today."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Time thread_manager._lock is held per health-check cycle is bounded by the traversal, not by recovery sleeps"
      metric: "time"

design:
  architecture: >
    Two-phase lock discipline. The lock guards reads of ThreadManager's
    threads dictionary and nothing else. Work derived from those reads is
    performed after the lock is released. Where an observation needs a
    delay between two reads, the delay sits between two separate critical
    sections rather than inside one.
  components:
    - name: "WatchdogMonitor._check_thread_health"
      type: "function"
      purpose: "Collect the recovery actions required this cycle, then dispatch them outside the lock."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Dispatches to the existing handlers."
        raises:
          - "None."
      logic:
        - "Phase 1, under 'with self.thread_manager._lock:': iterate self.thread_manager.threads.items() exactly as now."
        - "Skip entries whose status is not in {ThreadStatus.RUNNING, ThreadStatus.STARTING} — unchanged."
        - "Create the ThreadHealth entry if absent, with is_critical=(name in self.critical_threads) — unchanged."
        - "Compute time_since_heartbeat = current_time - thread_info.last_heartbeat — unchanged."
        - "Instead of calling a handler, append ('critical'|'recovery'|'warning'|'reset', name, health, time_since_heartbeat) to a local list, selecting the tag by the same threshold comparisons in the same order: critical_timeout, then recovery_timeout, then warning_timeout, else reset."
        - "Phase 2, after the with block has exited: iterate the list and call the corresponding handler for each entry."
        - "Do not sort, deduplicate or reorder the list. Traversal order is dispatch order."
    - name: "WatchdogMonitor._attempt_soft_recovery"
      type: "function"
      purpose: "Observe whether a thread's heartbeat advances, without holding the lock it must acquire to advance it."
      interface:
        inputs:
          - name: "name"
            type: "str"
            description: "Thread name."
          - name: "health"
            type: "ThreadHealth"
            description: "Watchdog-owned health record for the thread."
          - name: "timeout"
            type: "float"
            description: "Measured time since the last heartbeat."
        outputs:
          type: "None"
          description: "Updates recovery statistics and health state."
        raises:
          - "None. Existing except Exception clause retained."
      logic:
        - "Leave the preamble unchanged: the logger.info, the _recovery_lock increment of soft_recovery_attempts, health.current_level = RecoveryLevel.SOFT_RECOVERY and health.recovery_attempts += 1."
        - "Stage 1 under the lock: return early if name not in self.thread_manager.threads; otherwise read thread_info and capture old_heartbeat; keep the existing display-thread debug branch here verbatim."
        - "Stage 2 with no lock held: time.sleep(1.0)."
        - "Stage 3 under the lock: re-test membership; if present, re-read last_heartbeat from the dictionary's CURRENT ThreadInfo into new_heartbeat; if absent, leave new_heartbeat at its not-recovered default."
        - "After stage 3, outside the lock: if new_heartbeat > old_heartbeat, log success, increment soft_recovery_successes under self._recovery_lock, call self._reset_thread_health(health) and return."
        - "Retain the trailing except Exception clause and its logging unchanged."
  dependencies:
    internal:
      - "ThreadManager (core/thread.py) — read only. _lock aliases _state_lock at thread.py:111; update_heartbeat acquires it at thread.py:140."
    external: []

error_handling:
  strategy: >
    The existing try/except structure is preserved. The new risk introduced
    by releasing the lock — a thread disappearing during the window — is
    handled by explicit re-testing rather than by exception handling.
  exceptions:
    - exception: "KeyError"
      condition: "The monitored thread is unregistered during the 1 s sleep and stage 3 indexes the dictionary."
      handling: "Prevented: stage 3 re-tests membership before indexing. If absent, the attempt is treated as not recovered."
    - exception: "Exception"
      condition: "Any other failure in _attempt_soft_recovery."
      handling: "Existing handler retained: logger.error with exc_info=True."
  logging:
    level: "INFO"
    format: "Existing messages retained verbatim. Add no new log line except where a stage-1 early return needs one."

testing:
  unit_tests:
    - scenario: "Soft recovery where the heartbeat advances during the sleep window."
      expected: "Success logged; soft_recovery_successes increments; _reset_thread_health called."
    - scenario: "Soft recovery where the heartbeat does not advance."
      expected: "No success; soft_recovery_successes unchanged; escalation proceeds as before."
    - scenario: "Thread unregistered during the sleep."
      expected: "Treated as not recovered. No KeyError or AttributeError."
    - scenario: "Competing update_heartbeat calls from another thread during a soft recovery."
      expected: "No individual call blocked for more than a few milliseconds."
    - scenario: "Health check with three simultaneously unhealthy threads."
      expected: "All three handlers invoked once each, in traversal order; the lock is held only for the traversal."
    - scenario: "Health check with all threads healthy."
      expected: "_reset_thread_health called once per thread, as before."
    - scenario: "A thread whose status is neither RUNNING nor STARTING."
      expected: "Skipped; no ThreadHealth entry created."
    - scenario: "Repeated cycles over a fixed input sequence."
      expected: "recovery_stats counters match the pre-change values."
  edge_cases:
    - "Empty threads dictionary — the collected list is empty and phase 2 is a no-op."
    - "A thread added to the dictionary between phase 1 and phase 2 — not acted on this cycle; picked up next cycle."
    - "The same thread appearing at more than one severity — impossible; the comparison chain is exclusive and appends exactly one tuple per thread."
    - "health record referenced by a collected action while the thread is removed before dispatch — the handlers already tolerate a missing thread."
  validation:
    - "grep confirms no 'time.sleep' appears between 'with self.thread_manager._lock:' and the end of that block."
    - "src/gtach/core/thread.py has no diff."

deliverable:
  format_requirements:
    - "Edit src/gtach/core/watchdog.py in place. Create no new file."
    - "Make the two edits below and change nothing else."
  files:
    - path: "src/gtach/core/watchdog.py"
      content: |
        EDIT 1 — _check_thread_health (currently watchdog.py:135-162)

        Replace the whole method with:

            def _check_thread_health(self) -> None:
                """Check thread health and dispatch recovery outside the state lock.

                thread_manager._lock is held only for the traversal that builds
                the pending-action list. Recovery handlers — which sleep — are
                dispatched after the lock is released, so a cycle touching
                several unhealthy threads no longer blocks heartbeat and
                registration activity for the duration of the recovery
                (core review §4.1, recommendation #2).
                """
                current_time = time.time()

                # Phase 1 — collect under the lock. No blocking call here.
                pending = []

                with self.thread_manager._lock:
                    for name, thread_info in self.thread_manager.threads.items():
                        if thread_info.status not in {ThreadStatus.RUNNING, ThreadStatus.STARTING}:
                            continue

                        # Initialize thread health tracking if needed
                        if name not in self.thread_health:
                            self.thread_health[name] = ThreadHealth(
                                name=name,
                                is_critical=(name in self.critical_threads)
                            )

                        health = self.thread_health[name]
                        time_since_heartbeat = current_time - thread_info.last_heartbeat

                        # Determine appropriate response level
                        if time_since_heartbeat > self.critical_timeout:
                            level = 'critical'
                        elif time_since_heartbeat > self.recovery_timeout:
                            level = 'recovery'
                        elif time_since_heartbeat > self.warning_timeout:
                            level = 'warning'
                        else:
                            level = 'reset'

                        pending.append((level, name, health, time_since_heartbeat))

                # Phase 2 — dispatch with the lock released.
                for level, name, health, elapsed in pending:
                    if level == 'critical':
                        self._handle_critical_timeout(name, health, elapsed)
                    elif level == 'recovery':
                        self._handle_recovery_timeout(name, health, elapsed)
                    elif level == 'warning':
                        self._handle_warning_timeout(name, health, elapsed)
                    else:
                        self._reset_thread_health(health)

        EDIT 2 — _attempt_soft_recovery (currently watchdog.py:213-247)

        Replace the whole method with:

            def _attempt_soft_recovery(self, name: str, health: ThreadHealth, timeout: float) -> None:
                """Attempt soft recovery using thread interruption.

                The heartbeat observation is split across two short critical
                sections with the sleep between them. Holding
                thread_manager._lock across the sleep would block
                ThreadManager.update_heartbeat, which is the very write this
                method is waiting to observe (core review §3.3).
                """
                self.logger.info(f"Attempting soft recovery for thread {name} (timeout: {timeout:.1f}s)")

                with self._recovery_lock:
                    self.recovery_stats.soft_recovery_attempts += 1

                health.current_level = RecoveryLevel.SOFT_RECOVERY
                health.recovery_attempts += 1

                try:
                    # Stage 1 — read the current heartbeat under a short lock.
                    with self.thread_manager._lock:
                        if name not in self.thread_manager.threads:
                            self.logger.debug(f"Thread {name} no longer registered; soft recovery abandoned")
                            return

                        thread_info = self.thread_manager.threads[name]
                        thread = thread_info.thread
                        old_heartbeat = thread_info.last_heartbeat

                        # For display thread, try to trigger a refresh
                        if name == 'display' and hasattr(thread, '_target'):
                            self.logger.debug(f"Triggering display refresh for {name}")
                            # The display loop should detect this and recover

                    # Stage 2 — wait with NO lock held, so the monitored thread
                    # is free to acquire _state_lock and write its heartbeat.
                    time.sleep(1.0)

                    # Stage 3 — re-read under a short lock. Re-test membership:
                    # the thread may have been removed or restarted during the
                    # window, so do not reuse the ThreadInfo captured above.
                    new_heartbeat = old_heartbeat
                    with self.thread_manager._lock:
                        if name in self.thread_manager.threads:
                            new_heartbeat = self.thread_manager.threads[name].last_heartbeat

                    if new_heartbeat > old_heartbeat:
                        self.logger.info(f"Soft recovery successful for thread {name}")
                        with self._recovery_lock:
                            self.recovery_stats.soft_recovery_successes += 1
                        self._reset_thread_health(health)
                        return

                except Exception as e:
                    self.logger.error(f"Soft recovery failed for thread {name}: {e}", exc_info=True)

        Change nothing else in the file. In particular leave
        _attempt_hard_recovery, _handle_warning_timeout,
        _handle_recovery_timeout, _handle_critical_timeout,
        _reset_thread_health, get_thread_health_status and
        _emergency_shutdown exactly as they are.

success_criteria:
  - "python -m py_compile src/gtach/core/watchdog.py passes."
  - "pytest tests/ passes with no new failures."
  - "src/gtach/core/thread.py shows no diff."
  - "No time.sleep call in watchdog.py appears inside a 'with self.thread_manager._lock' block, by source inspection."
  - "_check_thread_health builds a pending list under the lock and dispatches after the with block exits."
  - "_check_thread_health still skips threads whose status is not RUNNING or STARTING, and still creates missing ThreadHealth entries."
  - "The threshold comparison order — critical_timeout, recovery_timeout, warning_timeout, else reset — is unchanged."
  - "_attempt_soft_recovery contains exactly two 'with self.thread_manager._lock' blocks with time.sleep(1.0) between them."
  - "Stage 3 re-tests 'name in self.thread_manager.threads' before indexing."
  - "recovery_stats.soft_recovery_attempts and soft_recovery_successes are incremented at the same points as before, under self._recovery_lock."
  - "No handler signature changed."
  - "No file other than src/gtach/core/watchdog.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "watchdog"
        path: "src/gtach/core/watchdog.py"
      - name: "thread"
        path: "src/gtach/core/thread.py"
    classes:
      - name: "WatchdogMonitor"
        module: "gtach.core.watchdog"
      - name: "ThreadHealth"
        module: "gtach.core.watchdog"
      - name: "RecoveryLevel"
        module: "gtach.core.watchdog"
      - name: "RecoveryStats"
        module: "gtach.core.watchdog"
      - name: "ThreadManager"
        module: "gtach.core.thread"
      - name: "ThreadStatus"
        module: "gtach.core.thread"
    functions:
      - name: "_check_thread_health"
        module: "gtach.core.watchdog"
        signature: "_check_thread_health(self) -> None"
      - name: "_attempt_soft_recovery"
        module: "gtach.core.watchdog"
        signature: "_attempt_soft_recovery(self, name: str, health: ThreadHealth, timeout: float) -> None"
      - name: "update_heartbeat"
        module: "gtach.core.thread"
        signature: "update_heartbeat(self, name: str) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-5a9dc15e-watchdog-lock-discipline.md

  Behaviour under fault changes: soft recovery becomes capable of
  succeeding where it previously always escalated to a thread restart. A
  fall in hard_recovery_attempts after deployment is the expected outcome,
  not a regression.

  A cleaner encapsulation — adding a public ThreadManager.get_last_heartbeat
  accessor so the watchdog need not touch _lock or the threads dictionary
  directly — was considered and deliberately not taken, because it modifies
  thread.py and exceeds the scope of recommendation #2. It is recorded in
  change-5a9dc15e under alternatives_considered.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-5a9dc15e. |
| 1.1 | 2026-07-30 | Executed by Claude Code. Both edits applied; twelve success criteria met, with the pytest criterion satisfied only vacuously — tests/ holds no test modules — and verification recorded against an ephemeral script under change-5a9dc15e. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
