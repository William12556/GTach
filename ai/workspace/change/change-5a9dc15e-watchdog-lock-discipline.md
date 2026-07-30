Created: 2026 July 30

# Change: Watchdog Lock Discipline — No Blocking Calls Inside ThreadManager's State Lock

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-5a9dc15e"
  title: "Release thread_manager._lock before sleeping in soft recovery; collect recovery actions under the lock and dispatch outside it"
  date: "2026-07-30"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-5a9dc15e"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-5a9dc15e"
  description: >
    Resolves issue-5a9dc15e. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 findings §3.3
    and §4.1 and recommendation #2. Task list reference ai/task.md §7.4.2.

scope:
  summary: >
    Narrow the scope of thread_manager._lock in WatchdogMonitor so that no
    blocking call is made while holding it. Two structural edits in
    src/gtach/core/watchdog.py: split the soft-recovery observation into
    two short critical sections either side of the sleep, and convert
    _check_thread_health from traverse-and-dispatch into
    collect-then-dispatch.
  affected_components:
    - name: "WatchdogMonitor._check_thread_health"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "refactor"
    - name: "WatchdogMonitor._attempt_soft_recovery"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/core/thread.py. No change to ThreadManager, its locks or its public API. The file is listed in ai/task.md §7.4.2 as the location of the contended lock, not as a file to modify."
    - "_attempt_hard_recovery. Its time.sleep(2.0) at watchdog.py:273 is already outside the lock and the subsequent read is momentary. Reviewed and left unchanged."
    - "get_thread_health_status (watchdog.py:347). Traverses under the lock but performs no blocking call. Correct as written."
    - "_emergency_shutdown (watchdog.py:315). Its time.sleep(0.5) is not inside any thread_manager lock."
    - "Adding a public last_heartbeat accessor to ThreadManager. Recorded as an alternative; not taken."
    - "Thread shutdown timeout budgeting — core report §5.5 and §5.9, task 7.4.6."

rational:
  problem_statement: >
    _attempt_soft_recovery holds thread_manager._lock across time.sleep(1.0)
    while waiting to see whether a thread's heartbeat advances. That lock is
    the one ThreadManager.update_heartbeat must acquire, so the observation
    prevents the event it is observing, and every other thread's heartbeat
    and registration is stalled for the duration. Separately,
    _check_thread_health traverses the threads dictionary under the same
    lock and dispatches into the recovery handlers from inside the
    traversal, so a cycle touching several unhealthy threads can hold the
    lock for several seconds.
  proposed_solution: >
    Split the soft-recovery observation into two short critical sections:
    acquire, read last_heartbeat, release; sleep outside the lock; acquire,
    re-test membership and re-read last_heartbeat, release; compare. Convert
    _check_thread_health to build a list of pending recovery actions while
    holding the lock, release the lock, and then dispatch. No blocking call
    remains inside a thread_manager._lock block.
  alternatives_considered:
    - option: "Give WatchdogMonitor its own lock and stop using thread_manager._lock."
      reason_rejected: >
        The data being read — threads and ThreadInfo.last_heartbeat — is
        owned by ThreadManager and written under its lock. A separate lock
        would not protect those reads. It would introduce a second lock
        over the same data, which is worse than the present state.
    - option: "Add a public ThreadManager.get_last_heartbeat(name) accessor and have the watchdog use it instead of touching _lock and threads directly."
      reason_rejected: >
        Cleaner, and worth doing eventually, but it modifies thread.py and
        widens the change beyond recommendation #2. The narrower fix
        removes the fault; the accessor is an encapsulation improvement
        that can be raised separately. Recorded here so the option is not
        lost.
    - option: "Shorten the sleep from 1.0 s to something small enough not to matter."
      reason_rejected: >
        Does not fix the defect. The observation would still be structurally
        unable to see a heartbeat written under the lock it holds, however
        short the window.
    - option: "Make the sleep interruptible via the stop event so shutdown is not delayed."
      reason_rejected: >
        A separate concern and a separate benefit. Not part of this
        recommendation; would obscure the fix under review. Note that once
        the lock is released the sleep no longer blocks other threads, so
        the shutdown-latency argument is much weaker.
  benefits:
    - "Soft recovery becomes capable of succeeding: the monitored thread can write its heartbeat during the observation window."
    - "Healthy threads are no longer stalled by another thread's recovery attempt."
    - "A watchdog cycle touching several unhealthy threads no longer holds the state lock for several seconds."
    - "Avoids unnecessary escalation from soft recovery to a thread restart."
  risks:
    - risk: >
        Releasing the lock between the two heartbeat reads opens a window in
        which the thread may be unregistered, restarted or replaced.
      mitigation: >
        The second critical section re-tests 'name in self.thread_manager.threads'
        and re-reads the ThreadInfo from the dictionary rather than reusing
        the object captured before the sleep. A thread that disappeared
        during the window is treated as not-recovered, which is the
        conservative outcome and matches the current behaviour on a missing
        entry.
    - risk: >
        Collecting actions under the lock and dispatching afterwards means
        the dispatch acts on a snapshot that may be one cycle stale.
      mitigation: >
        The snapshot is at most check_interval old and the handlers already
        re-read state when they act. The alternative — acting on live state
        while holding the lock — is the defect being corrected. Each
        collected action carries the name and the measured timeout, so no
        handler signature changes.
    - risk: >
        self.thread_health entries were previously created inside the locked
        traversal. Moving creation changes when they appear.
      mitigation: >
        thread_health is owned by WatchdogMonitor and touched only from the
        monitor thread, so its creation point is not a concurrency concern.
        Create entries during collection, as now, so the handlers receive a
        populated ThreadHealth exactly as they do today.
    - risk: >
        Recovery statistics could double-count if an action is collected and
        the thread recovers before dispatch.
      mitigation: >
        Statistics are incremented inside the handlers, which are called
        exactly once per collected action, as they are today. The counting
        semantics are unchanged.

technical_details:
  current_behavior: >
    _check_thread_health (watchdog.py:135) acquires thread_manager._lock at
    watchdog.py:139 and iterates self.thread_manager.threads.items(). Inside
    the loop it creates missing ThreadHealth entries, computes
    time_since_heartbeat, and calls _handle_critical_timeout,
    _handle_recovery_timeout, _handle_warning_timeout or
    _reset_thread_health — all while the lock is held. The recovery
    handlers call _attempt_soft_recovery and _attempt_hard_recovery, whose
    sleeps therefore execute inside the lock.

    _attempt_soft_recovery (watchdog.py:213) acquires thread_manager._lock
    at watchdog.py:225, reads old_heartbeat, calls time.sleep(1.0) at
    watchdog.py:237, then compares thread_info.last_heartbeat against
    old_heartbeat — all inside the same with block.
  proposed_behavior: >
    _check_thread_health holds thread_manager._lock only for the traversal
    that builds a pending-action list, then releases it and dispatches.
    _attempt_soft_recovery reads the heartbeat under a short lock, sleeps
    with the lock released, then re-acquires briefly to re-test membership
    and re-read the heartbeat.
  implementation_approach: >
    Two edits, both in src/gtach/core/watchdog.py.

    EDIT 1 — _check_thread_health. Restructure into two phases.

    Phase 1, under 'with self.thread_manager._lock:', iterate
    self.thread_manager.threads.items() exactly as now: skip threads whose
    status is not RUNNING or STARTING; create the ThreadHealth entry if
    absent; compute time_since_heartbeat. Instead of calling a handler,
    append a tuple (level, name, health, time_since_heartbeat) to a local
    list, where level is one of 'critical', 'recovery', 'warning' or
    'reset', selected by the same threshold comparisons in the same order.

    Phase 2, after the with block has exited, iterate the collected list and
    call the corresponding handler for each entry:
      critical -> self._handle_critical_timeout(name, health, elapsed)
      recovery -> self._handle_recovery_timeout(name, health, elapsed)
      warning  -> self._handle_warning_timeout(name, health, elapsed)
      reset    -> self._reset_thread_health(health)

    No handler signature changes. The comparison order and thresholds are
    preserved exactly.

    EDIT 2 — _attempt_soft_recovery. Replace the single 'with
    self.thread_manager._lock:' block (watchdog.py:225-244) with three
    stages inside the existing try:

      Stage 1, under the lock: if name not in self.thread_manager.threads,
      log and return. Otherwise read thread_info, capture
      old_heartbeat = thread_info.last_heartbeat, and preserve the existing
      display-thread debug branch (the 'if name == "display" and
      hasattr(thread, "_target")' block) unchanged. Release.

      Stage 2, outside any lock: time.sleep(1.0).

      Stage 3, under the lock: re-test 'name in self.thread_manager.threads'.
      If absent, treat as not recovered and fall through. Otherwise re-read
      new_heartbeat from the dictionary's current ThreadInfo — do not reuse
      the object captured in stage 1. Release.

      After stage 3: if new_heartbeat > old_heartbeat, log success,
      increment recovery_stats.soft_recovery_successes under
      self._recovery_lock, call self._reset_thread_health(health) and
      return — exactly the existing success block, moved outside the lock.

    Leave the method's preamble unchanged: the _recovery_lock increment of
    soft_recovery_attempts, health.current_level assignment and
    health.recovery_attempts increment all stay where they are. Leave the
    trailing 'except Exception' clause and its logging unchanged.
  code_changes:
    - component: "WatchdogMonitor"
      file: "src/gtach/core/watchdog.py"
      change_summary: >
        _check_thread_health becomes collect-then-dispatch;
        _attempt_soft_recovery observes the heartbeat across two short
        critical sections with the sleep between them.
      functions_affected:
        - "_check_thread_health"
        - "_attempt_soft_recovery"
      classes_affected:
        - "WatchdogMonitor"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "ThreadManager (core/thread.py)"
      impact: >
        Read only. _lock is an alias for _state_lock (thread.py:111);
        update_heartbeat acquires it at thread.py:140. No modification to
        thread.py is made or required.
    - component: "WatchdogMonitor._handle_warning_timeout / _handle_recovery_timeout / _handle_critical_timeout / _reset_thread_health"
      impact: "Called from a new site with identical arguments. No signature change."
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Unit tests on the development platform against WatchdogMonitor with a
    mock or real ThreadManager, driving the heartbeat from a second thread.
    Concurrency behaviour is asserted by measuring how long a competing
    update_heartbeat call is blocked.
  test_cases:
    - scenario: "Soft recovery where the monitored thread advances its heartbeat during the 1 s window."
      expected_result: "Reports success; soft_recovery_successes increments; _reset_thread_health is called."
    - scenario: "Soft recovery where the heartbeat does not advance."
      expected_result: "Does not report success; soft_recovery_successes does not increment; escalation proceeds as before."
    - scenario: "Soft recovery where the thread is unregistered during the sleep."
      expected_result: "Treated as not recovered. No KeyError, no AttributeError."
    - scenario: "A second thread calls update_heartbeat repeatedly while a soft recovery is in progress."
      expected_result: "No individual call is blocked for more than a few milliseconds."
    - scenario: "Health check with three simultaneously unhealthy threads."
      expected_result: "thread_manager._lock is held only for the traversal. All three handlers are invoked, once each, in the same order as the traversal."
    - scenario: "Health check with all threads healthy."
      expected_result: "_reset_thread_health is called for each, exactly as before."
    - scenario: "Health check where a thread's status is not RUNNING or STARTING."
      expected_result: "Skipped, and no ThreadHealth entry is created for it."
    - scenario: "Repeated health-check cycles."
      expected_result: "recovery_stats counters match the pre-change values for the same input sequence."
  regression_scope:
    - "tests/core/ — full existing core suite."
    - "Watchdog-initiated graceful shutdown path (_initiate_graceful_shutdown) still reachable from _handle_critical_timeout."
    - "Manual: application starts, all threads register, watchdog logs no spurious warnings during normal operation."
  validation_criteria:
    - "python -m py_compile src/gtach/core/watchdog.py passes."
    - "pytest tests/ passes with no new failures."
    - "No time.sleep call in watchdog.py lies within a 'with self.thread_manager._lock' block, by source inspection."
    - "src/gtach/core/thread.py is unmodified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — restructure _check_thread_health into collect-then-dispatch."
      owner: "Claude Code"
    - step: "EDIT 2 — split the _attempt_soft_recovery observation across two short critical sections."
      owner: "Claude Code"
    - step: "Compile check and run the existing test suite."
      owner: "Claude Code"
    - step: "Verify on gtach.local that normal operation produces no watchdog warnings and that an induced stall recovers as expected."
      owner: "William Watson"
  rollback_procedure: >
    Single file, single commit. git revert restores the previous behaviour.
    No data, configuration or interface migration is involved.
  deployment_notes: >
    Behaviour under fault changes: soft recovery may now succeed where it
    previously always escalated. A fall in hard_recovery_attempts after
    deployment is the expected outcome.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-5a9dc15e"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-5a9dc15e."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial change document coupled to issue-5a9dc15e. |

---

Copyright (c) 2026 William Watson. MIT License.
