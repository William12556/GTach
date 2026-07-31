Created: 2026 July 30

# Issue: Shutdown Can Exceed Its Own Budget by Arithmetic; Setup Re-Entry Blocks for the Full Join Timeout While Holding the Thread-State Lock

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-2d545bf5"
  title: "ThreadManager.shutdown floors per_thread_timeout at 1.0 s and can overrun the caller's budget; _re_enter_setup joins the OBD thread before disconnecting the transport, so the join always runs to its 5 s timeout; and stop_thread performs that join while holding _state_lock despite a comment saying otherwise"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "performance"
  iteration: 1
  coupled_docs:
    change_ref: "change-2d545bf5"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Finding §5.5 (shutdown timeout budget can silently shrink below the
    requested value) and finding §5.9 (_re_enter_setup may block the
    calling thread for several seconds). Neither has a numbered
    recommendation: §7.0 is a selective list of eight items and omits
    both, so each finding states its own remedy. A third fault, not
    recorded in either report, was found while verifying these two
    against source and is carried here because it is in the same file
    and is the mechanism by which §5.9 harms the rest of the
    application. Task list reference ai/task.md §7.4.6.

affected_scope:
  components:
    - name: "ThreadManager.shutdown"
      file_path: "src/gtach/core/thread.py"
    - name: "ThreadManager.stop_thread"
      file_path: "src/gtach/core/thread.py"
    - name: "GTachApplication._re_enter_setup"
      file_path: "src/gtach/app.py"
  designs:
    - design_ref: "design-a1b2c3d4-component_core_thread_manager"
  version: "0.2.67"

reproduction:
  prerequisites: >
    GTach running with the display, obd_protocol and setup threads
    registered — the three registration sites are
    display/manager.py:119, comm/obd.py:51 and display/setup.py:135.
  steps:
    - "§5.5 — read core/thread.py:353-355. remaining_timeout is computed once, before the loop, and per_thread_timeout once from it."
    - "§5.5 — evaluate per_thread_timeout for the __del__ path at core/thread.py:396, which calls shutdown(timeout=2.0), with three registered threads: 2.0 / 3 = 0.667, which is below the 1.0 floor, so per_thread_timeout is 1.0 and the worst case is 3.0 s against a 2.0 s budget."
    - "§5.9 — read app.py:212-229. _re_enter_setup calls stop_thread('obd_protocol') at app.py:218 and only then disconnects the transport at app.py:222."
    - "§5.9 — read core/thread.py:291-326. stop_thread sets the status to STOPPING and joins; it never calls the registered stop_func and sets no event."
    - "§5.9 — read comm/obd.py:51. OBDProtocol registers stop_func=self.stop, which sets shutdown_event."
    - "§5.9 — read comm/obd.py:79. The inner polling loop is bounded by self.transport.is_connected(), not by shutdown_event, so the thread cannot leave that loop while the transport is up."
    - "§5.9 — read comm/obd.py:68-74. The outer loop is bounded by shutdown_event, and when the transport is down it sleeps 0.1 s and continues rather than returning. So disconnecting the transport alone does not end the thread either; only setting shutdown_event does, and OBDProtocol.stop (comm/obd.py:58-64) is the only thing that sets it."
    - "§5.9 — conclude that stop_thread('obd_protocol') can never succeed from this path as written, whatever the transport state, and runs to its full 5.0 s default."
    - "Third fault — read core/thread.py:310 against 311-326. The comment 'Join thread outside of lock to prevent deadlock' is at column 8 but the statements after it are at column 12, still inside the 'with self._state_lock:' opened at core/thread.py:293."
  frequency: "always"
  reproducibility_conditions: >
    §5.5's overrun is arithmetic and holds whenever
    timeout / len(self.threads) is below 1.0, which the __del__ path at
    core/thread.py:396 satisfies with the application's normal three
    threads. It also holds for the 10.0 s default whenever
    worker_pool.shutdown consumes more than the budget.

    §5.9 manifests on every use of the Setup control on the DISCONNECTED
    screen while the transport is still connected. When the transport is
    already down the OBD thread is in the outer loop at comm/obd.py:68
    and can exit promptly, so the block is short — which is why the fault
    is easy to miss in testing, since the DISCONNECTED screen is usually
    reached because the transport dropped.

    The third fault is unconditional: every stop_thread call joins under
    the lock.
  preconditions: >
    Raspberry Pi Zero 2W. ThreadManager is constructed with its defaults
    at app.py:49 — three worker threads, core/thread.py:81. The watchdog
    is constructed at app.py:50-57 with check_interval 5.0 and
    warning_timeout 15.0.
  test_data: >
    §5.5 recomputed rather than repeated from the report.

    core/thread.py:354-355 read:
      remaining_timeout = timeout - (time.time() - shutdown_start)
      per_thread_timeout = max(1.0, remaining_timeout / max(1, len(self.threads)))

    Case A, the documented default. shutdown(timeout=10.0) with three
    threads and an instantaneous worker pool: 10.0 / 3 = 3.333, above the
    floor, worst case 3 x 3.333 = 10.0 s. The budget holds.

    Case B, the __del__ path. core/thread.py:396 calls
    shutdown(timeout=2.0). 2.0 / 3 = 0.667, below the floor, so
    per_thread_timeout is 1.0 and the worst case is 3 x 1.0 = 3.0 s — a
    50 per cent overrun with a healthy worker pool and nothing wrong.
    The report attributes the overrun solely to a slow
    worker_pool.shutdown; this case needs no such thing.

    Case C, the report's case. If worker_pool.shutdown takes 12 s against
    a 10.0 s budget, remaining_timeout is -2.0, per_thread_timeout is
    1.0, and the worst case is 12 + 3 = 15 s.

    §5.9 measured against source. stop_thread's default timeout is 5.0
    (core/thread.py:291). _re_enter_setup passes no timeout, so 5.0
    applies.
  error_output: >
    None for any of the three. §5.5 logs "cleanup took Xs" at
    core/thread.py:374-377 with the true figure, so the overrun is
    recorded but not remarked on. §5.9 logs "Thread obd_protocol did not
    stop within 5.0s" at WARNING (core/thread.py:324) — which is the
    evidence that the join always times out, and is currently read as
    noise.

behavior:
  expected: >
    A shutdown completes within the timeout its caller supplied, or says
    plainly that it cannot. A UI-driven callback does not block the
    calling thread for seconds. A thread asked to stop is asked to stop.
    Bookkeeping shared with every other thread is not held across a
    multi-second wait.
  actual: >
    Three faults in the thread-lifecycle path, grouped because they
    compose: the third makes the second harmful, and the first and second
    are both consequences of joins whose duration is not governed.

    (a) §5.5 — the budget floor. core/thread.py:355 computes
    per_thread_timeout once, before the loop, as
    max(1.0, remaining_timeout / max(1, len(self.threads))). When that
    quotient falls below 1.0 the floor engages for every thread, and the
    total can exceed the caller's timeout. Nothing logs that the budget
    has been exceeded; the "cleanup took Xs" line at core/thread.py:376
    reports the outcome without judging it.

    (b) §5.9 — a join that cannot succeed. _re_enter_setup (app.py:212)
    calls stop_thread('obd_protocol') at app.py:218 and disconnects the
    transport at app.py:222, in that order. stop_thread does not call
    the registered stop_func and sets no event. The OBD thread's inner
    loop is bounded by transport.is_connected() (comm/obd.py:79) and its
    outer loop by shutdown_event (comm/obd.py:68), and when the transport
    is down the outer loop sleeps and continues rather than returning
    (comm/obd.py:72-74). Nothing on this path sets shutdown_event, so the
    thread does not end whatever the transport state. The join runs to
    its full 5.0 s, stop_thread records success as False and writes
    ThreadStatus.FAILED at core/thread.py:319, and the thread continues
    to run. The re-entry then proceeds to _start_setup_mode with the old
    OBD thread still live.

    GTachApplication.shutdown already knows the correct sequence and
    documents it at app.py:295-300 — watchdog, display, "Transport —
    closes socket, unblocks any OBD thread blocked on recv", "OBD — safe
    to join now that socket is closed", then the thread manager — and
    follows it at app.py:301-312. The essential element is the pair:
    disconnect the transport, then call OBDProtocol.stop, which is the
    only caller of shutdown_event.set (comm/obd.py:61). _re_enter_setup
    does neither before it joins.

    (c) NOT IN EITHER REPORT — the join is performed under the shared
    lock. stop_thread opens 'with self._state_lock:' at
    core/thread.py:293. The comment at core/thread.py:310 reads "Join
    thread outside of lock to prevent deadlock" and is indented to
    column 8, but every statement after it, through the return at
    core/thread.py:326, is at column 12 and therefore still inside that
    block. The join at core/thread.py:313 executes while the lock is
    held. _state_lock is an RLock (core/thread.py:92), so the nested
    re-acquisition at core/thread.py:317 does not self-deadlock and the
    fault is invisible, but update_heartbeat (core/thread.py:140),
    register_thread (core/thread.py:120) and get_thread_status
    (core/thread.py:158) all block for the join's duration.
  impact: >
    (a) is a correctness-of-contract problem rather than a hazard: the
    caller's timeout is advisory in a case where it reads as binding. It
    matters most on the __del__ path, where the 2.0 s budget exists
    precisely because interpreter shutdown should not be delayed.

    (b) is operator-visible. The Setup control on the DISCONNECTED screen
    freezes the interface for five seconds and then re-enters setup with
    an OBD thread still running against a transport that is about to be
    disconnected underneath it. The stale thread is subsequently
    displaced when _start_obd registers a new one — register_thread
    overwrites an entry whose status is not RUNNING or STARTING
    (core/thread.py:121-125), and FAILED is not among those — so the
    application recovers, but through a path nobody designed.

    (c) is what turns (b) from a slow callback into a system-wide stall.
    For those five seconds no thread can report a heartbeat, because
    update_heartbeat waits on the same lock. The watchdog's
    warning_timeout is 15.0 s (app.py:53), so a single occurrence does
    not trip it; two in succession, or one during a shutdown that is
    already joining other threads, moves closer. This is the same defect
    class as §3.3 and §4.1, which the report rates High and which
    change-5a9dc15e corrected in core/watchdog.py — a lock held across a
    wait that the lock's other users need to make progress.
  workaround: >
    None for any of the three. Both routes into setup reach the same
    method: the DISCONNECTED screen's Setup control via
    _enter_setup_from_disconnected (display/manager.py:1635-1640) and
    OPTIONS then Clear settings via _on_clear_settings
    (display/manager.py:1286-1288), each invoking
    self._setup_entry_callback, which app.py:180 binds to
    _re_enter_setup. Choosing a different control does not avoid the
    block; it is avoided only when the transport is already down, which
    is the usual reason the DISCONNECTED screen is on show and the
    reason the fault is easy to miss.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "CPython threading"
      version: "stdlib"
  domain: "domain_1"

analysis:
  root_cause: >
    (a) A floor was applied to a per-item budget without a corresponding
    check on the aggregate. max(1.0, ...) guarantees each join gets a
    usable timeout and thereby abandons the guarantee the parameter
    expresses.

    (b) stop_thread's contract is "join and hope". It records a stop_func
    at registration (core/thread.py:132) and calls it only on the restart
    path (core/thread.py:230-235), never on the stop path. Every caller
    that wants a thread to actually stop must therefore arrange the
    stopping condition itself, and _re_enter_setup arranges it in the
    wrong order.

    (c) An editing accident. The comment was dedented and the block it
    was meant to close was not, so the code now asserts the opposite of
    what it does. Nothing detects this, because the lock is reentrant.
  technical_notes: >
    TWO CORRECTIONS AND ONE ADDITION TO THE SOURCE REPORT, all found by
    reading src/gtach at 0.2.67.

    (1) §5.5's mechanism is narrower than stated and its reach is wider.
    The report says "every subsequent thread is forced down to the 1.0
    second floor", which implies per_thread_timeout is recomputed inside
    the loop. It is computed once, at core/thread.py:355, before the loop
    at core/thread.py:360, so the floor applies uniformly rather than
    progressively. The report also attributes the overrun to
    worker_pool.shutdown consuming more than the caller's timeout. The
    __del__ path at core/thread.py:396 overruns without that: with a
    2.0 s budget and three threads the quotient is 0.667 and the floor
    engages immediately.

    (2) §5.9 understates the fault. "May block the calling thread for
    several seconds" and "can block for up to its default timeout" both
    describe an upper bound. On this path the join cannot succeed at all,
    so the full 5.0 s always elapses and the thread is not stopped. The
    report's proposed remedies follow from the understatement: "a shorter
    timeout for this specific call" would shorten the freeze without
    stopping the thread, and "perform the stop asynchronously with a
    status indicator" would present a spinner over a thread that will
    never stop.

    The effective remedy is the pair app.py:301-312 already performs in
    shutdown: disconnect the transport, then call OBDProtocol.stop.
    Disconnecting alone is not sufficient — comm/obd.py:72-74 sleeps and
    continues when the transport is down rather than returning — and
    calling stop alone is not sufficient either, because with the
    transport up the inner loop at comm/obd.py:79 never re-tests
    shutdown_event. Both were checked against source; the ordering was
    not inferred from shutdown's comment.

    (3) An addition. Neither report records that stop_thread joins under
    _state_lock. It belongs to this triple: it is in the declared file
    set, it is the mechanism by which (b) harms unrelated threads, and it
    is the same defect class as §3.3, which the report rates High.

    ON NOT WIDENING THE SCOPE. Two further observations were made and are
    deliberately not claimed here, because each is a change to a
    subsystem this triple does not own.

      - OBDProtocol._protocol_loop's inner loop (comm/obd.py:79) tests
        only transport.is_connected(). Setting shutdown_event does not
        break it, so OBDProtocol.stop (comm/obd.py:58-64) also relies on
        the transport being taken down first, and its own 5.0 s join has
        the same character. Making the inner loop respect shutdown_event
        would be the general fix. comm/obd.py is task 7.4.7's file, and
        only for §4.2.
      - stop_thread never calls the registered stop_func. Making it do so
        would give every caller a working stop, but OBDProtocol.stop
        itself joins for 5.0 s (comm/obd.py:63), so stop_thread would
        then join twice. That interaction needs designing, not patching.

    Both are recorded in change-2d545bf5 under out_of_scope so they are
    not rediscovered, and both are candidates for a separate item.
  related_issues:
    - issue_ref: "issue-5a9dc15e"
      relationship: "related"
    - issue_ref: "issue-b4e7c2f1"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    In core/thread.py, log at WARNING when the per-thread budget floor
    engages and record the projected overrun, rather than substituting
    the floor silently; and correct the indentation so the join runs
    outside _state_lock, as the existing comment says it should. In
    app.py, have _re_enter_setup disconnect the transport and call
    OBDProtocol.stop before asking the thread manager to stop the thread
    — the sequence shutdown already documents and follows at
    app.py:295-312 — and pass an explicit short timeout to the join,
    which is then a formality. See change-2d545bf5.
  change_ref: "change-2d545bf5"
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
    A floor applied to a derived budget needs a companion check on the
    aggregate, or the parameter it derives from is not a budget. A join
    is a wait, and a wait is not performed while holding a lock that the
    awaited party needs — the rule change-5a9dc15e established for
    core/watchdog.py applies to core/thread.py unchanged. When a comment
    states a locking property, that property is worth asserting in a
    test, because indentation can move and comments cannot.
  process_improvements: >
    ai/task.md §8.2 already schedules WatchdogMonitor lock-discipline
    tests. Adding a ThreadManager equivalent — assert that a second
    thread can call update_heartbeat while stop_thread is joining — would
    have caught fault (c) and will catch its recurrence.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/core/thread.py src/gtach/app.py passes."
    - "Read core/thread.py:311-326 and confirm every statement is at the method-body indentation, outside the 'with self._state_lock:' block."
    - "Unit test: start a thread that will not exit; call stop_thread from one thread and update_heartbeat from another; confirm the second returns promptly rather than after the join."
    - "Unit test: register three threads, call shutdown(timeout=2.0), and confirm a WARNING naming the budget is logged."
    - "Unit test: register three threads, call shutdown(timeout=10.0), and confirm no such WARNING is logged."
    - "Unit test: confirm the WARNING states the caller's timeout, the number of threads and the projected worst case."
    - "Unit test: confirm shutdown still stops every thread and still clears self.threads, with the log line at core/thread.py:374-377 unchanged in form."
    - "Unit test: call _re_enter_setup with stub _transport, _obd and _thread_manager objects that record call order; confirm the order is transport.disconnect, obd.stop, thread_manager.stop_thread."
    - "Unit test: confirm stop_thread is called with an explicit timeout rather than the 5.0 s default."
    - "Unit test: confirm _re_enter_setup still tolerates the absence of _transport, _obd and _thread_manager, as the hasattr guards allow, and still calls _start_setup_mode in each case."
    - "Unit test: confirm a raise from transport.disconnect does not prevent obd.stop and stop_thread from running, matching the existing tolerance at app.py:223-224."
    - "On gtach.local: with the transport connected, tap Setup on the DISCONNECTED screen and confirm setup is entered without a multi-second freeze."
    - "On gtach.local: confirm the log no longer carries 'Thread obd_protocol did not stop within' on that path."
  verification_results: ""

traceability:
  design_refs:
    - "design-a1b2c3d4-component_core_thread_manager"
  change_refs:
    - "change-2d545bf5"
  test_refs: []

notes: >
  This is task 7.4.6 in ai/task.md §7.4 and part of step 5 in the
  recommended authoring order (§7.6.2). Released in v0.3.0 (§8.3).

  issue_info.type is performance per ai/task.md §7.2 as extended in v6.0,
  and per the discharge step recorded in
  ai/workspace/report/task-list-cross-check-discrepancies.md §5.4 item 1:
  §5.5 and §5.9 are both latency concerns, so the whole triple takes
  performance. The type is retained despite the added lock finding, which
  is a latency concern of the same kind — a wait imposed on threads that
  are not party to it.

  The report rates §5.5 and §5.9 Low in its §6.0 summary, item 9.
  severity is recorded as medium rather than low because of fault (c),
  which is not in the report's classification and is the same shape as
  the High-rated §3.3.

  core/thread.py was left unmodified by change-5a9dc15e, which corrected
  core/watchdog.py only. This is the first triple to modify it.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

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
      - "Initial issue document from core-comm-utils-code-review.md findings §5.5 and §5.9."
      - "Recorded two corrections to the source report: per_thread_timeout is computed once rather than per thread, and the __del__ path overruns its budget without a slow worker pool; and the §5.9 join cannot succeed at all in the case the finding names, so the full timeout always elapses and the thread is not stopped."
      - "Recorded a third fault found during verification and not present in either report: stop_thread joins while holding _state_lock, contradicting the comment at core/thread.py:310."
      - "Recorded two related observations — the OBD inner loop's exit condition and stop_thread's unused stop_func — as deliberately unclaimed."

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
| 1.0 | 2026-07-30 | Initial issue document from core-comm-utils-code-review.md findings §5.5 and §5.9, with two recorded corrections to the report, one fault added from verification, and two related observations recorded as unclaimed. |

---

Copyright (c) 2026 William Watson. MIT License.
