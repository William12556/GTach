Created: 2026 July 30

# Issue: Watchdog Holds ThreadManager's State Lock Across Multi-Second Sleeps

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-5a9dc15e"
  title: "WatchdogMonitor holds thread_manager._lock across time.sleep during recovery, blocking the heartbeat it is waiting to observe and stalling all thread bookkeeping"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-5a9dc15e"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Finding §3.3 (ThreadManager lock held across time.sleep), finding §4.1
    (health-check loop serializes recovery work under a single lock), and
    §7.0 recommendation #2. Task list reference: ai/task.md §7.4.2.

affected_scope:
  components:
    - name: "WatchdogMonitor._check_thread_health"
      file_path: "src/gtach/core/watchdog.py"
    - name: "WatchdogMonitor._attempt_soft_recovery"
      file_path: "src/gtach/core/watchdog.py"
    - name: "WatchdogMonitor._attempt_hard_recovery"
      file_path: "src/gtach/core/watchdog.py"
    - name: "ThreadManager.update_heartbeat"
      file_path: "src/gtach/core/thread.py"
    - name: "ThreadManager.register_thread"
      file_path: "src/gtach/core/thread.py"
  designs: []
  version: "0.2.64"

reproduction:
  prerequisites: >
    GTach running with the watchdog active. A monitored thread must miss
    its heartbeat window — recovery_timeout or critical_timeout — to enter
    the recovery path.
  steps:
    - "Start the application so the display, transport and OBD threads register with ThreadManager."
    - "Cause one monitored thread to stop calling update_heartbeat for longer than recovery_timeout — for example by suspending the OBD thread or removing its data source."
    - "Observe that _check_thread_health enters _attempt_soft_recovery."
    - "Observe that all other threads' update_heartbeat calls block for the duration of the recovery attempt."
    - "Observe that the soft-recovery test reports failure even when the monitored thread is in fact alive."
  frequency: "always"
  reproducibility_conditions: >
    Occurs on every soft-recovery attempt (1.0 s hold) and every hard-recovery
    attempt (part of a 2.0 s window). The health-check loop compounds it: a
    single watchdog cycle touching more than one unhealthy thread can hold
    the lock for several seconds.
  preconditions: >
    thread_manager._lock is an alias for _state_lock, a threading.RLock
    assigned at core/thread.py:111. update_heartbeat acquires _state_lock at
    core/thread.py:140.
  test_data: ""
  error_output: >
    None. No exception is raised. The observable symptom is a stall in
    thread bookkeeping and a soft recovery that reports failure for a
    healthy thread.

behavior:
  expected: >
    A recovery attempt observes whether a thread's heartbeat advances,
    without preventing that thread from advancing it, and without blocking
    unrelated threads from registering or reporting.
  actual: >
    Two related faults.

    (a) Lock held across sleep — core/watchdog.py:225-244.
    _attempt_soft_recovery acquires thread_manager._lock at watchdog.py:225,
    reads thread_info.last_heartbeat, then calls time.sleep(1.0) at
    watchdog.py:237 while still holding it, and compares the heartbeat
    afterwards. thread_manager._lock is the same lock acquired by
    ThreadManager.update_heartbeat (core/thread.py:140). The monitored
    thread therefore cannot update its heartbeat during the observation
    window, so the check is structurally unable to observe what it is
    testing for. It also blocks every other thread's heartbeat and
    registration for a full second.

    _attempt_hard_recovery has the same shape in a milder form: it calls
    time.sleep(2.0) at watchdog.py:273 and then acquires the lock at
    watchdog.py:274. The sleep is outside the lock there, so only the
    post-sleep read blocks — that path is correct as written and is
    included in scope only for consistency review.

    (b) Recovery nested inside the health-check loop — core/watchdog.py:139-162.
    _check_thread_health iterates all threads while holding
    thread_manager._lock at watchdog.py:139, and dispatches from inside that
    loop into _handle_warning_timeout, _handle_recovery_timeout and
    _handle_critical_timeout, which in turn call the recovery methods and
    their sleeps. The lock is reentrant, so this does not deadlock against
    itself, but it serializes: a cycle touching several unhealthy threads
    holds the lock, and blocks all heartbeat and registration activity, for
    several seconds at a time.
  impact: >
    The report classifies this as High severity and notes that the path is
    exercised in the running application whenever a thread misses its
    heartbeat window. The soft-recovery mechanism cannot succeed by
    construction, so a recoverable thread is escalated to hard recovery —
    a thread restart — unnecessarily. Concurrently, threads that are
    entirely healthy are stalled by a fault in a different thread's
    recovery.
  workaround: >
    None. The behaviour is intrinsic to the current lock scope.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    The recovery code treats thread_manager._lock as a guard for the whole
    recovery operation rather than as a guard for reads of the threads
    dictionary. Because ThreadInfo objects are reached through that
    dictionary, holding the lock felt necessary for the duration; but the
    only operations that need it are the membership test and the field
    reads, each of which is momentary. The sleep between two reads is not a
    critical section — it is precisely the interval during which another
    thread must be free to write.

    The health-check loop has the same shape at a larger scale: it holds
    the lock for the traversal and then performs unbounded work inside the
    traversal, rather than collecting a work list under the lock and acting
    on it outside.
  technical_notes: >
    The correct pattern for the soft-recovery observation is: acquire,
    read last_heartbeat, release; sleep; acquire, re-read last_heartbeat,
    release; compare. The second acquisition must re-test membership,
    because the thread may have been removed during the sleep.

    The correct pattern for _check_thread_health is: acquire, build a list
    of (name, action, timeout) tuples describing what needs to be done,
    release; then dispatch. The health-tracking dictionary self.thread_health
    is owned by the watchdog, not by ThreadManager, and does not require
    thread_manager._lock — but it is touched from the monitor thread only,
    so no new lock is needed for it.

    ThreadManager already exposes get_thread_status(name) (core/thread.py:156)
    which acquires _state_lock internally. A narrow accessor for
    last_heartbeat would let the watchdog avoid touching the private
    _lock and threads dict at all, but adding one widens the change beyond
    the recommendation; the change document takes the narrower path and
    records the option.

    get_thread_health_status (core/watchdog.py:347) also traverses under
    thread_manager._lock but performs no sleeps, so it is correct as
    written and is out of scope.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Release thread_manager._lock before sleeping in _attempt_soft_recovery
    and re-acquire briefly to read the heartbeat for comparison. Restructure
    _check_thread_health to collect the required recovery actions under the
    lock, release it, then dispatch. See change-5a9dc15e.
  change_ref: "change-5a9dc15e"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A blocking call — sleep, join, network or serial I/O — must not appear
    inside a lock that guards shared bookkeeping. Where an observation
    requires a delay between two reads, the delay belongs between two
    separate critical sections, not inside one.
  process_improvements: >
    Traversals that dispatch into handlers should collect first and act
    second, so that the cost of the handler is not charged to the lock
    holding the collection.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/core/watchdog.py passes."
    - "Confirm by inspection that no time.sleep call in watchdog.py lies within a 'with self.thread_manager._lock' block."
    - "Confirm that _check_thread_health releases thread_manager._lock before dispatching to any _handle_* method."
    - "Unit test: with a mock ThreadManager whose heartbeat advances during the sleep window, confirm _attempt_soft_recovery reports success."
    - "Unit test: with a heartbeat that does not advance, confirm _attempt_soft_recovery does not report success and escalation proceeds as before."
    - "Unit test: confirm update_heartbeat from another thread is not blocked for more than a few milliseconds during a soft-recovery attempt."
    - "Unit test: with three simultaneously unhealthy threads, confirm the total time thread_manager._lock is held during one health-check cycle is bounded by the traversal, not by the recovery sleeps."
    - "Confirm recovery statistics — soft_recovery_attempts, soft_recovery_successes, hard_recovery_attempts — are still incremented as before."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-5a9dc15e"
  test_refs: []

notes: >
  This is task 7.4.2 in ai/task.md §7.4 and part of step 3 in the
  recommended authoring order (§7.6.2), being one of the two High severity
  core findings active in the running application. The core report's §6.0
  priority table lists it as item 2.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial issue document from core-comm-utils-code-review.md §3.3, §4.1 and recommendation #2."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial issue document from core-comm-utils-code-review.md §3.3, §4.1 and recommendation #2. |

---

Copyright (c) 2026 William Watson. MIT License.
