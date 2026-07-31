Created: 2026 July 30

# Change: Report the Shutdown Budget Overrun, Join Outside the State Lock, Stop the OBD Thread Before Joining It

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-2d545bf5"
  title: "Log at WARNING when the per-thread shutdown floor engages; move stop_thread's join outside the _state_lock block its comment already claims it is outside; reorder _re_enter_setup to disconnect the transport and stop the OBD protocol before joining"
  date: "2026-07-30"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-2d545bf5"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-2d545bf5"
  description: >
    Resolves issue-2d545bf5. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 findings §5.5
    and §5.9, whose remedies are stated inside the findings because §7.0
    omits them, plus one fault found during verification and recorded in
    the issue. Task list reference ai/task.md §7.4.6.

scope:
  summary: >
    Three corrections across two files. In core/thread.py, say when the
    per-thread timeout floor has abandoned the caller's aggregate budget,
    and perform stop_thread's join outside _state_lock rather than
    inside it. In app.py, give _re_enter_setup the same shutdown sequence
    that GTachApplication.shutdown documents and follows, so the join it
    performs can succeed.
  affected_components:
    - name: "ThreadManager.shutdown"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "ThreadManager.stop_thread"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "GTachApplication._re_enter_setup"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-a1b2c3d4-component_core_thread_manager"
      sections:
        - "Thread lifecycle and shutdown"
  out_of_scope:
    - "OBDProtocol._protocol_loop's inner loop (comm/obd.py:79), which tests only transport.is_connected(). Making it also respect shutdown_event would be the general fix for a thread that cannot be stopped without taking its transport down, and would remove the ordering constraint this change works within. comm/obd.py belongs to task 7.4.7 and only for §4.2. Recorded as a candidate for a separate item."
    - "Having ThreadManager.stop_thread call the stop_func recorded at core/thread.py:132. It would give every caller a working stop, but OBDProtocol.stop itself joins for 5.0 s (comm/obd.py:63), so stop_thread would then join twice with two independent timeouts. That interaction needs designing rather than patching."
    - "The 1.0 s floor value itself. This change reports when it engages; whether the floor should exist, or should scale, is a design question the finding does not raise."
    - "worker_pool.shutdown's own unbounded wait at core/thread.py:347. Python 3.9 offers no timeout parameter, as the comment at core/thread.py:345 records, and working around it is a larger change than §5.5 asks for."
    - "core/watchdog.py. Its lock discipline was corrected by change-5a9dc15e and is not revisited."
    - "GTachApplication.shutdown itself (app.py:286-316). Its sequence is already correct and is the model this change copies."
    - "The nested self.threads lookup at core/thread.py:317-319. Moving the join out of the lock does not change the pre-existing possibility that the entry is replaced between the two acquisitions; the existing 'if name in self.threads' guard is retained unchanged."

rational:
  problem_statement: >
    ThreadManager.shutdown computes per_thread_timeout once at
    core/thread.py:355 as max(1.0, remaining_timeout / max(1, len(...))).
    When the quotient falls below 1.0 the floor engages for every thread
    and the aggregate can exceed the caller's timeout with nothing said.
    stop_thread performs its join at core/thread.py:313 while holding
    _state_lock, contrary to the comment at core/thread.py:310, so every
    other thread's heartbeat, registration and status query blocks for
    the join's duration. _re_enter_setup joins the OBD thread at
    app.py:218 before disconnecting the transport at app.py:222, and
    nothing on that path sets the OBD protocol's shutdown_event, so the
    join cannot succeed and the full 5.0 s always elapses — under the
    lock, on a UI-driven callback.
  proposed_solution: >
    Emit a WARNING from shutdown when the computed quotient is below the
    floor, naming the requested budget, the thread count and the
    projected worst case. De-indent stop_thread's join block so it runs
    after the state lock is released. Reorder _re_enter_setup to
    disconnect the transport, stop the OBD protocol and only then ask the
    thread manager to stop the thread, with an explicit 2.0 s timeout.
  alternatives_considered:
    - option: "Remove the 1.0 s floor and let per_thread_timeout go negative."
      reason_rejected: >
        Thread.join with a negative timeout returns immediately, so every
        thread would be abandoned rather than given a chance. The floor
        is defensible; its silence is not.
    - option: "Scale the floor, or drop threads once the budget is spent."
      reason_rejected: >
        Both change shutdown's behaviour. §5.5 asks only that the overrun
        be logged rather than silently substituted, and a behavioural
        change to shutdown deserves its own cycle.
    - option: "Give _re_enter_setup a shorter stop_thread timeout, as §5.9 suggests."
      reason_rejected: >
        It shortens the freeze without stopping the thread. The join
        cannot succeed on this path at all: stop_thread sets no event and
        calls no stop_func, and nothing else on the path sets
        shutdown_event. A shorter timeout would leave a running OBD
        thread and simply hide the symptom. The short timeout is retained
        here, but as a bound on a join that is now expected to succeed
        immediately.
    - option: "Perform the stop asynchronously with a status indicator, as §5.9 also suggests."
      reason_rejected: >
        It would present an indicator over an operation that never
        completes, for the same reason. It also adds a UI element and a
        worker submission to a path that, once ordered correctly,
        completes in well under a second.
    - option: "Disconnect the transport in _re_enter_setup but leave OBDProtocol.stop out."
      reason_rejected: >
        Insufficient, and checked rather than assumed. With the transport
        down the inner loop at comm/obd.py:79 exits, but the outer loop
        at comm/obd.py:68 sleeps 0.1 s and continues (comm/obd.py:72-74)
        rather than returning. Only shutdown_event ends the thread, and
        OBDProtocol.stop at comm/obd.py:61 is its only setter.
    - option: "Call OBDProtocol.stop but leave the transport connected."
      reason_rejected: >
        Also insufficient. The inner loop never re-tests shutdown_event,
        so with the transport up the thread stays in it. Both steps are
        required, in that order, which is exactly what
        GTachApplication.shutdown does at app.py:307-310.
    - option: "Fix the indentation in stop_thread as a Trivial Change Exemption (P03 §1.4.12)."
      reason_rejected: >
        It meets criteria 1 to 4 — one method, a handful of lines, no
        interface change, unambiguous — but it is a change to lock
        discipline in the thread manager, and it is grouped here with
        non-trivial work in the same file. ai/task.md §7.2 states the
        exemption is not claimed for any triple in this programme.
  benefits:
    - "A shutdown that cannot meet its budget says so, in the same log the operator already reads for the cleanup time."
    - "A join no longer blocks every other thread's heartbeat, which is what the comment at core/thread.py:310 has claimed since it was written."
    - "The Setup control on the DISCONNECTED screen responds promptly instead of freezing for five seconds."
    - "Setup re-entry no longer leaves a live OBD thread behind, marked FAILED, to be displaced later by register_thread's overwrite path."
    - "The two paths that stop the OBD subsystem — shutdown and setup re-entry — perform the same sequence, so there is one thing to know rather than two."
  risks:
    - risk: >
        Moving the join outside the lock lets another thread modify
        self.threads between the two acquisitions.
      mitigation: >
        The re-acquisition at core/thread.py:317 already guards with
        'if name in self.threads', and that guard is retained unchanged.
        The window it covers exists today between the join and the status
        write; releasing the outer lock widens it but does not create it.
        thread_info is a local bound before the release, so the join
        operates on the object the caller asked about regardless.
    - risk: >
        The WARNING becomes noise on every __del__-path shutdown.
      mitigation: >
        It fires only when the quotient is below the floor, and __del__'s
        2.0 s budget with three threads is exactly the case §5.5 exists
        to surface. If it proves noisy the correct response is to raise
        __del__'s budget or lower the floor, both of which the log makes
        arguable; suppressing the log would restore the silence.
    - risk: >
        _re_enter_setup calls OBDProtocol.stop, which joins for 5.0 s
        (comm/obd.py:63), so the callback could still block.
      mitigation: >
        With the transport already disconnected the outer loop reaches
        its shutdown_event test within one sleep interval — 0.1 s at
        comm/obd.py:73 — or within one send_command timeout of 1.0 s if
        the thread is mid-request. The join is expected to return in well
        under 1.5 s. A test asserts the ordering; the on-target step
        confirms the elapsed time.
    - risk: >
        _obd may not exist when _re_enter_setup runs.
      mitigation: >
        Guarded with hasattr, in the same style as the existing
        _transport and _thread_manager guards at app.py:217 and 220. It
        is absent only if setup never completed, in which case there is
        no OBD thread to stop.
    - risk: >
        Stopping the OBD protocol before re-entering setup changes what
        the setup flow finds.
      mitigation: >
        It is what the path already intends — app.py:218's comment reads
        "Stop OBD if running" — and _obd_started is reset to False at
        app.py:225 either way, so _on_setup_complete will construct a
        fresh OBDProtocol through _start_obd. The change makes the intent
        effective rather than altering it.

technical_details:
  current_behavior: >
    core/thread.py:353-355 computes remaining_timeout and
    per_thread_timeout once, inside 'with self._cleanup_lock:', and the
    loop at core/thread.py:360-368 applies the same value to every
    thread. No log distinguishes a floored value from a computed one.

    core/thread.py:293 opens 'with self._state_lock:'. The comment at
    core/thread.py:310 is at column 8 and says the join is outside the
    lock; core/thread.py:311-326 are at column 12 and are inside it, so
    the join at core/thread.py:313 holds the lock for its duration.

    app.py:212-229: _re_enter_setup logs, calls
    stop_thread('obd_protocol') at app.py:218 with the 5.0 s default,
    disconnects the transport at app.py:222, resets _obd_started and
    re-enters setup.
  proposed_behavior: >
    shutdown emits a WARNING when the quotient is below the floor,
    naming the requested timeout, the remaining time, the thread count,
    the floored per-thread value and the projected worst case. Its
    behaviour is otherwise unchanged.

    stop_thread releases _state_lock before joining and re-acquires it
    only for the status write, as its comment already states.

    _re_enter_setup disconnects the transport, calls OBDProtocol.stop,
    then calls stop_thread('obd_protocol', timeout=2.0), which finds the
    thread already stopped and records STOPPED rather than FAILED.
  implementation_approach: >
    Three edits across two files.

    src/gtach/core/thread.py

    EDIT 1 — shutdown budget warning. Compute the unfloored quotient
    into a named local, keep per_thread_timeout as max(1.0, quotient),
    and emit a WARNING when self.threads is non-empty and the quotient is
    below 1.0. The message must carry the caller's timeout, the
    remaining time, the thread count, the per-thread value in force and
    the worst-case total, because the point of the log is that the
    reader can see the overrun rather than infer it.

    EDIT 2 — stop_thread lock scope. De-indent core/thread.py:311-326 by
    one level so they follow the 'with self._state_lock:' block rather
    than sitting inside it, and move the comment at core/thread.py:310
    to the same level so it describes what happens. Nothing else in the
    method changes: the early returns, the state transition, the restart
    cancellation, the nested re-acquisition and its 'if name in
    self.threads' guard all keep their current text.

    src/gtach/app.py

    EDIT 3 — _re_enter_setup sequence. Replace the body between the
    opening log line and the _obd_started reset with the sequence
    shutdown uses: transport disconnect under its existing try, then
    OBDProtocol.stop under a hasattr guard and its own try, then
    stop_thread with an explicit 2.0 s timeout. Each step tolerates
    failure so that a fault in one does not prevent the others, matching
    the existing tolerance at app.py:223-224.
  code_changes:
    - component: "ThreadManager"
      file: "src/gtach/core/thread.py"
      change_summary: >
        Report the aggregate budget overrun when the per-thread floor
        engages; perform stop_thread's join outside _state_lock.
      functions_affected:
        - "shutdown"
        - "stop_thread"
      classes_affected:
        - "ThreadManager"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Disconnect the transport and stop the OBD protocol before joining
        the OBD thread on setup re-entry, mirroring shutdown's sequence.
      functions_affected:
        - "_re_enter_setup"
      classes_affected:
        - "GTachApplication"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "OBDProtocol.stop"
      impact: "Called from a second site. comm/obd.py:58-64 is unmodified; the change is that _re_enter_setup now calls it, as shutdown already does at app.py:310."
    - component: "OBDTransport.disconnect"
      impact: "Called earlier in the sequence than before. No transport implementation is modified."
    - component: "WatchdogMonitor"
      impact: "Benefits. It calls into thread_manager._lock, which is _state_lock (core/thread.py:111); that lock is no longer held across stop_thread's join. core/watchdog.py is unmodified."
    - component: "ThreadManager.register_thread"
      impact: "Unchanged, but the overwrite path at core/thread.py:121-125 is no longer relied on to displace a FAILED obd_protocol entry after a setup re-entry, because the entry is now STOPPED and the thread is dead."
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Unit tests on the development platform with real threading
    primitives, since lock discipline and join behaviour are the subject
    and a mock would test the mock. app.py is tested with recording stubs
    for _transport, _obd and _thread_manager, since the subject there is
    call order. On-target confirmation for the operator-visible effect.
  test_cases:
    - scenario: "Register a thread that will not exit; call stop_thread from one thread and update_heartbeat for another thread from a second."
      expected_result: "update_heartbeat returns while the join is still in progress. Before the change it blocks for the full join timeout."
    - scenario: "Same, but call get_thread_status from the second thread."
      expected_result: "Returns promptly."
    - scenario: "Register three threads; call shutdown(timeout=2.0)."
      expected_result: "A WARNING is logged naming the 2.0 s request, the three threads and the 3.0 s worst case."
    - scenario: "Register three threads; call shutdown(timeout=10.0) with an instantaneous worker pool."
      expected_result: "No such WARNING. 10.0 / 3 = 3.333 is above the floor."
    - scenario: "Call shutdown with no registered threads."
      expected_result: "No WARNING, whatever the timeout. There is no per-thread work to overrun."
    - scenario: "Call shutdown after a worker pool that consumed more than the budget."
      expected_result: "A WARNING; the remaining time it reports is negative."
    - scenario: "Call shutdown normally."
      expected_result: "Every thread stopped, self.threads and self._active_futures cleared, and the existing 'ThreadManager shutdown complete' line unchanged in form."
    - scenario: "stop_thread against an unregistered name."
      expected_result: "Returns False and logs, as before, without reaching the join."
    - scenario: "stop_thread against a thread already STOPPED."
      expected_result: "Returns True from the terminal-state branch, as before, without reaching the join."
    - scenario: "_re_enter_setup with recording stubs for _transport, _obd and _thread_manager."
      expected_result: "Call order is transport.disconnect, obd.stop, thread_manager.stop_thread."
    - scenario: "Inspect the stop_thread call in _re_enter_setup."
      expected_result: "An explicit timeout is passed; the 5.0 s default is not used."
    - scenario: "_re_enter_setup with _transport.disconnect raising."
      expected_result: "obd.stop and stop_thread still run; the failure is logged at WARNING as it is today."
    - scenario: "_re_enter_setup with no _obd attribute."
      expected_result: "The other steps run and _start_setup_mode is still called."
    - scenario: "_re_enter_setup with no _transport and no _thread_manager attribute."
      expected_result: "_start_setup_mode is still called, as the existing hasattr guards allow."
  regression_scope:
    - "pytest tests/ — no new failures."
    - "Manual on target: SIGINT shutdown still completes and the terminal is restored."
    - "Manual on target: watchdog-driven shutdown still completes."
    - "Manual on target: with the transport connected, tap Setup on the DISCONNECTED screen and confirm setup is entered without a multi-second freeze."
    - "Manual on target: complete setup after such a re-entry and confirm the OBD protocol starts and RPM is displayed."
    - "Manual on target: confirm no 'Thread obd_protocol did not stop within' WARNING appears on the re-entry path."
  validation_criteria:
    - "python -m py_compile src/gtach/core/thread.py src/gtach/app.py passes."
    - "Every statement from 'success = True' to the closing 'return success' in stop_thread is at method-body indentation."
    - "stop_thread contains exactly two 'with self._state_lock:' statements, neither enclosing the join."
    - "shutdown's WARNING is emitted only when self.threads is non-empty and the unfloored quotient is below 1.0."
    - "per_thread_timeout is still max(1.0, ...) — the floor is reported, not removed."
    - "_re_enter_setup calls disconnect, then stop, then stop_thread, in that order."
    - "src/gtach/comm/obd.py is unmodified."
    - "src/gtach/core/watchdog.py is unmodified."
    - "GTachApplication.shutdown is byte-identical to its current text."
    - "No file other than src/gtach/core/thread.py and src/gtach/app.py is modified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — shutdown budget warning in core/thread.py."
      owner: "Claude Code"
    - step: "EDIT 2 — de-indent stop_thread's join block out of the state lock."
      owner: "Claude Code"
    - step: "EDIT 3 — _re_enter_setup sequence in app.py."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Unit tests with real threading primitives for the lock discipline, and recording stubs for the call order."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; exercise setup re-entry with the transport up, and both shutdown paths."
      owner: "William Watson"
  rollback_procedure: >
    Two files, one commit. git revert restores the previous behaviour.
    No data, configuration or interface migration is involved.
  deployment_notes: >
    The re-entry effect is only observable while the transport is still
    connected, which is not the usual state when the DISCONNECTED screen
    is shown. To reproduce it, reach OPTIONS with the transport up and
    use Clear settings, which invokes the same callback via
    display/manager.py:1286-1288.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5a9dc15e"
      relationship: "related"
    - change_ref: "change-b4e7c2f1"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-2d545bf5"
      relationship: "resolves"

notes: >
  Task 7.4.6 in ai/task.md §7.4, released in v0.3.0 (§8.3). Per §8.2.1
  this change is left active when the code lands, pending a passing T06
  result; only prompt-2d545bf5 closes on implementation.

  core/thread.py was left unmodified by change-5a9dc15e, which corrected
  core/watchdog.py alone. This is the first change to modify it, so
  there is no prior edit to write against.

  ai/task.md §7.6.1 records no dependency for this task, and none was
  found: core/thread.py is claimed by 7.4.2, which is implemented and
  closed, and app.py is claimed by 7.4.5, which is gated on §7.5.5 and
  whose app.py interest is the duplicated transport-name list in
  GTachApplication.start (core review §5.8, app.py:79-90), not
  _re_enter_setup. The two edits are disjoint regions of the same file.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-2d545bf5."
      - "Records why both of §5.9's proposed remedies are rejected, and why disconnecting the transport alone or calling OBDProtocol.stop alone is insufficient."
      - "Records the OBD inner-loop exit condition and stop_thread's unused stop_func as out of scope and as candidates for a separate item."

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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-2d545bf5. Rejects both of §5.9's proposed remedies with recorded reasons, carries the lock-scope correction found during verification, and records two related observations as out of scope. |

---

Copyright (c) 2026 William Watson. MIT License.
