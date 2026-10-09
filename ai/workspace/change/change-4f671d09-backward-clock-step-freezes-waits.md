Created: 2026 October 09

# Change: Clock-Step-Safe Waits for Supervision Loops

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-4f671d09"
  title: "Replace timed threading.Event.wait in the transport, watchdog and OBD loops with a sleep-polled wait that a backward wall-clock step cannot extend"
  date: "2026-10-09"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-4f671d09"
    issue_iteration: 1

source:
  type: "issue"
  reference: "ai/workspace/issues/issue-4f671d09-backward-clock-step-freezes-waits.md"
  description: >
    On the Pi (CPython 3.9.2) a backward wall-clock step extends a timed
    Event.wait already in progress by the size of the step. The transport
    supervision loop then stops noticing link loss and the watchdog stops
    checking, for up to the size of the step.

scope:
  summary: >
    Add one helper, gtach.utils.waits.wait_for_event(event, timeout), that
    waits by polling event.is_set() between time.sleep slices against a
    time.monotonic() deadline. Use it at the six timed waits whose loops
    do periodic work: three in OBDTransport.reconnect_indefinitely, one in
    WatchdogMonitor._monitor_loop, two in OBDProtocol.
  affected_components:
    - name: "wait_for_event (new)"
      file_path: "src/gtach/utils/waits.py"
      change_type: "add"
    - name: "OBDTransport.reconnect_indefinitely"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "WatchdogMonitor._monitor_loop"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
    - name: "OBDProtocol._protocol_loop, OBDProtocol._initialize_protocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "Regression tests (new)"
      file_path: "tests/test_monotonic_waits.py"
      change_type: "add"
  affected_designs:
    - design_ref: ""
      sections:
        - ""
  out_of_scope:
    - "app.py:594 main loop. Listed in the issue, but the loop only re-checks _stop_event; set() wakes the waiter immediately whatever the clock does, so a backward step has no observable effect there."
    - "interface.py:174 _pairing_ready.wait(10.0), splash.py:271 _completion_event.wait, async_operations.py:264 operation_queue.get(timeout=1.0), and Thread.join(timeout=...) calls. Same mechanism, but set()/put() still wake them; only their failure timeout is extended. Candidates for a follow-up issue if wanted."
    - "Upgrading the Pi interpreter to Python 3.11 or later."
    - "time.sleep call sites (already clock-step safe)."

rational:
  problem_statement: >
    CPython before 3.11 implements timed lock acquisition on Linux with
    sem_timedwait against CLOCK_REALTIME. The absolute deadline is computed
    once when the wait starts; it is recomputed from the monotonic clock
    only after EINTR. A backward step of S seconds therefore extends a wait
    in progress by S. Observed on gtach.local: transport thread silent for
    102.9 s; link loss not recovered until an operator Reset.
  proposed_solution: >
    A helper that never calls a timed lock acquire. It checks
    event.is_set(), then sleeps min(slice, remaining) with time.sleep, and
    repeats until the event is set or a time.monotonic() deadline passes.
    time.sleep on Linux uses select() with a relative timeout, which the
    kernel measures on a monotonic clock. Return value matches Event.wait:
    True if the event is set, otherwise False.
  alternatives_considered:
    - option: "Event.wait in short slices re-checked against time.monotonic() (issue candidate 1)."
      reason_rejected: "Each slice still has an absolute CLOCK_REALTIME deadline, so the slice in progress when the clock steps back is extended by the full step. Does not fix the defect."
    - option: "Python 3.11+ on the Pi (issue candidate 3)."
      reason_rejected: "Bullseye ships 3.9; building or packaging another interpreter is out of proportion to the defect."
    - option: "An event class backed by a self-pipe and select(), giving immediate wake-up with a monotonic timeout."
      reason_rejected: "More code and file descriptors per event for a latency gain (at most one slice) that no caller needs."
  benefits:
    - "Link loss is noticed within ~1 s and reconnection proceeds regardless of wall-clock steps."
    - "The watchdog keeps checking during and after a backward step."
  risks:
    - risk: "Wake-up on set() is delayed by up to one slice (0.1 s) instead of immediate, slightly slowing shutdown."
      mitigation: "Shutdown join timeouts are 5 s; 0.1 s is negligible."
    - risk: "Extra wake-ups: about 10/s per waiting thread (transport, watchdog; OBD only during retry/settle)."
      mitigation: "Negligible CPU on the Pi Zero 2W; slice is a module constant if tuning is needed."

technical_details:
  current_behavior: >
    reconnect_indefinitely waits with self._shutdown.wait(1.0) while
    supervising and self._shutdown.wait(retry_delay) between attempts;
    _monitor_loop waits with self._stop_event.wait(self.check_interval);
    _protocol_loop waits with shutdown_event.wait(_INIT_RETRY_DELAY_S);
    _initialize_protocol waits with shutdown_event.wait(min(slice, remaining)).
  proposed_behavior: >
    Each of those six calls becomes wait_for_event(<same event>, <same
    timeout>). Return values are used exactly as before (the settle loop
    still returns False when the event is set). No other logic changes.
  implementation_approach: >
    1. Add src/gtach/utils/waits.py with _POLL_SLICE_S = 0.1 and
    wait_for_event(event, timeout) -> bool. Docstring cites issue-4f671d09
    and states why Event.wait is not used. timeout <= 0 returns
    event.is_set() at once. 2. Replace the six calls. Update the
    reconnect_indefinitely docstring sentence that says every wait is on
    _shutdown. 3. Add tests/test_monotonic_waits.py.
  code_changes:
    - component: "waits"
      file: "src/gtach/utils/waits.py"
      change_summary: "New helper."
      functions_affected:
        - "wait_for_event"
      classes_affected: []
    - component: "transport"
      file: "src/gtach/comm/transport.py"
      change_summary: "Three waits in reconnect_indefinitely use wait_for_event."
      functions_affected:
        - "OBDTransport.reconnect_indefinitely"
      classes_affected:
        - "OBDTransport"
    - component: "watchdog"
      file: "src/gtach/core/watchdog.py"
      change_summary: "Monitor loop wait uses wait_for_event."
      functions_affected:
        - "WatchdogMonitor._monitor_loop"
      classes_affected:
        - "WatchdogMonitor"
    - component: "obd"
      file: "src/gtach/comm/obd.py"
      change_summary: "Init retry wait and settle-slice wait use wait_for_event."
      functions_affected:
        - "OBDProtocol._protocol_loop"
        - "OBDProtocol._initialize_protocol"
      classes_affected:
        - "OBDProtocol"
  data_changes: []
  interface_changes:
    - interface: "gtach.utils.waits.wait_for_event(event: threading.Event, timeout: float) -> bool"
      change_type: "contract"
      details: "New internal function. Existing public interfaces unchanged."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "SimTransport"
      impact: "Inherits reconnect_indefinitely; behaviour unchanged apart from the wait mechanism."
  external: []
  required_changes:
    - change_ref: "change-d26ca557"
      relationship: "related (both modify transport.py; implement this change first)"

testing_requirements:
  test_approach: "Unit tests on the helper and on each call site with an event double that fails any timed wait. On-device clock-step reproduction by the operator."
  test_cases:
    - scenario: "wait_for_event on an event already set."
      expected_result: "Returns True without sleeping."
    - scenario: "wait_for_event; another thread sets the event after ~0.2 s; timeout 5 s."
      expected_result: "Returns True within 0.2 s + one slice."
    - scenario: "wait_for_event; event never set; timeout 0.3 s."
      expected_result: "Returns False; elapsed (monotonic) >= 0.3 s and < 0.3 s + one slice + margin."
    - scenario: "wait_for_event with an object exposing only is_set() (no wait attribute)."
      expected_result: "Works; proves Event.wait is never called."
    - scenario: "reconnect_indefinitely with _shutdown replaced by an Event subclass whose wait() raises AssertionError; connect fails once, then the test sets the event."
      expected_result: "Loop exits cleanly; no AssertionError."
    - scenario: "WatchdogMonitor._monitor_loop with the same double for _stop_event; _check_thread_health patched to set it."
      expected_result: "Loop exits; no AssertionError."
    - scenario: "OBDProtocol init-retry and pre-initialised settle paths with the same double for shutdown_event."
      expected_result: "No AssertionError; settle still returns False when the event is set."
  regression_scope:
    - "tests/ (full suite)"
  validation_criteria:
    - "No timed Event.wait remains in reconnect_indefinitely, _monitor_loop, _protocol_loop or _initialize_protocol."
    - "pytest tests/ passes."
    - "On gtach.local: issue reproduction steps produce no watchdog unresponsive warning, and a link drop after a backward step is reconnected without operator action."

implementation:
  effort_estimate: "2 hours"
  implementation_steps:
    - step: "Implement per prompt-4f671d09."
      owner: "Claude Code"
    - step: "Deploy and repeat the issue reproduction on gtach.local."
      owner: "William Watson"
  rollback_procedure: "git revert the implementing commit."
  deployment_notes: "Normal wheel deploy; no configuration change."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found:
    - issue_ref: ""

traceability:
  design_updates:
    - design_ref: ""
      sections_updated:
        - ""
      update_date: ""
  related_changes:
    - change_ref: "change-e215a184"
      relationship: "related (moved durations to time.monotonic; did not cover blocking waits)"
    - change_ref: "change-04c18cda"
      relationship: "related (introduced the sliced settle wait modified here)"
    - change_ref: "change-d26ca557"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-4f671d09"
      relationship: "source"

notes: "Root cause is inferred from CPython 3.9 source behaviour and matches the observed 102.9 s silence exactly. Line numbers are from b464bee; locate code by symbol."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document from issue-4f671d09 iteration 1."

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
| 1.0 | 2026-10-09 | Initial change document from issue-4f671d09 iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
