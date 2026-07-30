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
  status: "closed"
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
  resolved_date: "2026-07-30"
  resolved_by: "Claude Code, per prompt-5a9dc15e"
  fix_description: >
    Two structural edits in src/gtach/core/watchdog.py, as specified.

    _check_thread_health became collect-then-dispatch. Phase 1 holds
    thread_manager._lock only for the traversal, appending a
    (level, name, health, elapsed) tuple per eligible thread with the
    threshold chain unchanged. Phase 2 runs after the with block exits and
    calls _handle_critical_timeout, _handle_recovery_timeout,
    _handle_warning_timeout or _reset_thread_health in traversal order.

    _attempt_soft_recovery split its heartbeat observation into three
    stages. Stage 1 acquires the lock, returns early with a debug log if
    the thread is no longer registered, otherwise captures old_heartbeat
    and runs the existing display-thread debug branch. Stage 2 sleeps
    1.0 s with no lock held. Stage 3 re-acquires, re-tests membership and
    re-reads last_heartbeat from the dictionary's current ThreadInfo,
    leaving new_heartbeat at its not-recovered default if the entry has
    gone. The success block — log, soft_recovery_successes increment under
    _recovery_lock, _reset_thread_health — now runs outside the lock.

    The method preamble, all handler signatures, every threshold, the
    sleep duration and the recovery_stats increment points are unchanged.
    src/gtach/core/thread.py has no diff.

verification:
  verified_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Verified 2026-07-30 on macOS 15 (Darwin 25.5.0), Python 3.11.14,
    pygame 2.6.1.

    tests/ contains no test modules — only README.md — so pytest collects
    zero items and the suite provides no regression signal. Verification
    was therefore performed with an ephemeral validation script driving
    WatchdogMonitor against a real ThreadManager instance with a second
    thread calling the public update_heartbeat API. Eighteen assertions,
    covering all eight test cases in change-5a9dc15e and all four edge
    cases in prompt-5a9dc15e. All eighteen pass.

    The same script was then run unchanged against the pre-change
    watchdog.py extracted from HEAD. Four assertions fail there and pass
    after the change, isolating the defect:

      - a competing update_heartbeat call was blocked for 951 ms during a
        soft-recovery attempt; after the change the worst observed block
        is 0.03 ms;
      - soft recovery reported failure for a thread that was writing its
        heartbeat throughout the window, and now reports success;
      - _reset_thread_health was consequently not called on a recovered
        thread, and now is;
      - handlers were dispatched with thread_manager._lock held — a probe
        thread could not acquire it within 500 ms — and are now dispatched
        with it free.

    The fourteen behaviour-preservation assertions pass identically before
    and after: dispatch order and multiplicity for three simultaneously
    unhealthy threads, _reset_thread_health once per healthy thread, the
    skip of non-RUNNING/STARTING threads with no ThreadHealth entry
    created, the empty-dictionary no-op, the stalled-heartbeat path,
    health.current_level and health.recovery_attempts, and the
    soft_recovery_attempts count including the stage-1 early-return case.
  closure_notes: >
    Both faults reported in behavior.actual are corrected. Fault (a) — the
    lock held across time.sleep(1.0) — is removed by the three-stage
    split, and the measurement above confirms the observation can now see
    the write it is testing for. Fault (b) — recovery dispatched from
    inside the locked traversal — is removed by collect-then-dispatch.
    _attempt_hard_recovery, get_thread_health_status and
    _emergency_shutdown were reviewed and left unchanged as the issue
    specifies; their sleeps lie outside any thread_manager lock.

    Two items remain open by design and are not conditions of this
    closure. Implementation step 4 of change-5a9dc15e — on-target
    confirmation on gtach.local that normal operation produces no spurious
    watchdog warnings and that an induced stall recovers — is owned by
    William Watson. The public ThreadManager.get_last_heartbeat accessor
    recorded under change-5a9dc15e alternatives_considered was
    deliberately not taken; it remains available as a separate
    encapsulation change.

    The absence of any test module under tests/ is a standing gap wider
    than this issue and is not raised as a residual against it.

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
  verification_results: >
    All eight steps executed 2026-07-30. All pass.

    1. python -m py_compile src/gtach/core/watchdog.py — passes.

    2. No time.sleep inside a 'with self.thread_manager._lock' block. The
    file has three sleeps and four lock blocks. Line 271 sleep(1.0) sits
    between the stage-1 block at 255 and the stage-3 block at 277. Line
    315 sleep(2.0) in _attempt_hard_recovery precedes its lock block at
    316, unchanged. Line 363 sleep(0.5) in _emergency_shutdown is in no
    lock block. The phase-1 block at 150 contains no call at all.

    3. _check_thread_health releases the lock before dispatch. The
    dispatch loop is outside the with block. Confirmed dynamically: during
    each of three handler invocations a probe thread acquired
    _state_lock within 500 ms, which it could not do before the change.

    4. Heartbeat advancing during the window — _attempt_soft_recovery
    reports success, soft_recovery_successes goes to 1 and
    _reset_thread_health is called once. Fails on the pre-change file.

    5. Heartbeat not advancing — no success reported,
    soft_recovery_successes stays 0, _reset_thread_health is not called,
    health.current_level is SOFT_RECOVERY and health.recovery_attempts is
    1, so _handle_recovery_timeout escalates on the next cycle exactly as
    before.

    6. Competing update_heartbeat from another thread during a soft
    recovery — worst observed block 0.03 ms over the 1 s window, against
    951 ms on the pre-change file.

    7. Three simultaneously unhealthy threads (50 s, 35 s, 20 s since
    heartbeat) — critical, recovery and warning handlers each invoked
    once, in traversal order, with the lock held only for the traversal.

    8. Recovery statistics — soft_recovery_attempts increments once per
    call including the stage-1 early-return path; soft_recovery_successes
    increments only on an advancing heartbeat; both under _recovery_lock
    at their original points. hard_recovery_attempts is untouched by this
    change; _attempt_hard_recovery was not modified.

    Additionally, a thread unregistered mid-sleep is treated as not
    recovered with no KeyError or AttributeError, and a thread absent at
    stage 1 returns in under 0.2 s without sleeping.

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
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Resolved by change-5a9dc15e via prompt-5a9dc15e. Resolution, verification and all eight verification steps recorded; status -> closed; moved to ai/workspace/issues/closed/ per P00 §1.1.14.4."

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
| 1.1 | 2026-07-30 | Resolved and verified. Status closed; moved to ai/workspace/issues/closed/ per P00 §1.1.14.4. |

---

Copyright (c) 2026 William Watson. MIT License.
