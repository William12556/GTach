Created: 2026 May 08

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-b4e7c2f1"
  title: "Duplicate obd_protocol thread spawned on watchdog restart causes concurrent OBD polling"
  date: "2026-05-08"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Observed during simbt transport testing. RPM display shows rapid jumps between two
    divergent RPM trajectories. Log analysis confirms two simultaneous SimTransport TX:010C
    requests firing at identical timestamps throughout the session after the first
    watchdog-triggered restart of obd_protocol.

affected_scope:
  components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
    - name: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
  designs:
    - design_ref: ""
  version: "0.2.35"

reproduction:
  prerequisites: "App running with --transport simbt. Watchdog must trigger obd_protocol restart (occurs ~45s after OBD connects due to heartbeat starvation — separate fix applied)."
  steps:
    - "Start gtach --transport simbt"
    - "Complete setup, allow OBD to connect"
    - "Wait ~45 seconds for watchdog to fire obd_protocol critical timeout"
    - "Observe RPM display for erratic jumps"
  frequency: "always"
  reproducibility_conditions: "Requires watchdog timeout on obd_protocol thread. With heartbeat fix applied to inner loop, timeout window is greatly reduced but restart path remains defective."
  preconditions: ""
  test_data: "gtach-simbt.log"
  error_output: |
    2026-05-08 10:54:49,234 SimTransport DEBUG SimTransport TX: 010C
    2026-05-08 10:54:49,234 SimTransport DEBUG SimTransport TX: 010C
    2026-05-08 10:54:49,236 SimTransport DEBUG SimTransport RX: 41 0C 2F E0
    2026-05-08 10:54:49,236 SimTransport DEBUG SimTransport RX: 41 0C 59 F4
    2026-05-08 10:54:49,243 DisplayManager DEBUG RPM 5757 band colour bg=(255, 128, 0)
    2026-05-08 10:54:49,270 SimTransport DEBUG SimTransport TX: 010C
    2026-05-08 10:54:49,272 SimTransport DEBUG SimTransport RX: 41 0C 30 0A
    2026-05-08 10:54:49,280 DisplayManager DEBUG RPM 3074 band colour bg=(0, 255, 0)

behavior:
  expected: "Single OBD polling thread active at all times. RPM values follow a single smooth sine sweep."
  actual: >
    Two obd_protocol threads run concurrently after watchdog restart. Each thread has an
    independent sine wave phase. Display alternates between the two threads' RPM values
    producing apparent random jumps and RPM screen flickering.
  impact: >
    RPM display is unreliable whenever a watchdog restart has occurred. Visual output is
    unusable. Applies to any transport mode where a restart is triggered.
  workaround: "Restart application."

environment:
  python_version: "3.9"
  os: "Linux (Raspberry Pi Zero 2W, Debian)"
  dependencies:
    - library: "pygame"
      version: "2.x"
  domain: "domain_1"

analysis:
  root_cause: >
    ThreadManager._restart_thread() creates and starts a new threading.Thread using the
    stored target_func from ThreadInfo. It updates thread_info.thread to reference the new
    thread, but never signals or joins the original thread. OBDProtocol._protocol_loop
    runs until self.shutdown_event.is_set(), which is an instance-level Event on
    OBDProtocol. The restart path in ThreadManager has no reference to OBDProtocol and
    cannot set that event. The original thread therefore continues to run indefinitely
    alongside the new thread. Both threads share the same SimTransport instance and
    message_queue, producing interleaved responses and display corruption.
  technical_notes: >
    The fix requires a stop mechanism callable from ThreadManager._restart_thread before
    the new thread is started. Options:
    (A) Store a stop callable in ThreadInfo alongside target_func, callable by
        ThreadManager before restart. OBDProtocol.stop() sets shutdown_event and joins.
    (B) Add a threading.Event to ThreadInfo that OBDProtocol._protocol_loop polls, so
        ThreadManager can signal stop without knowing the OBDProtocol instance.
    Option A is preferred — it is explicit, consistent with the existing stop() pattern,
    and does not require changes to the polling loop logic. ThreadInfo gains an optional
    stop_func: Optional[Callable] field. ThreadManager._restart_thread calls stop_func()
    before starting the new thread if stop_func is set.
    OBDProtocol.__init__ passes self.stop as stop_func when registering the thread.
    OBDProtocol.stop() must be idempotent (safe to call when not yet started or already
    stopped).
  related_issues:
    - issue_ref: ""
      relationship: ""

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Implement Option A: add optional stop_func field to ThreadInfo; call it in
    _restart_thread before spawning new thread; register OBDProtocol.stop as stop_func.
  change_ref: "change-b4e7c2f1"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "All thread registrations that wrap stateful objects with a stop method should register stop_func at registration time."
  process_improvements: "ThreadManager restart documentation should state that restart is only safe when a stop_func is registered."

verification_enhanced:
  verification_steps:
    - "Run gtach --transport simbt"
    - "Allow OBD to connect and run for at least 90 seconds"
    - "Confirm log shows no paired SimTransport TX:010C lines"
    - "Confirm RPM sweep is smooth with no jumps"
    - "If watchdog fires and restart occurs, confirm only one TX:010C per poll cycle after restart"
  verification_results: ""

traceability:
  design_refs:
    - ""
  change_refs:
    - "change-b4e7c2f1"
  test_refs:
    - ""

notes: >
  Two trivial fixes were applied under §1.4.12 exemption in the same session:
  (1) obd.py inner loop heartbeat — prevents the watchdog timeout that triggers the restart.
  (2) setup.py clean exit — stops setup thread being falsely flagged as timed out.
  This issue addresses the restart path defect which persists regardless of fix (1).

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial issue document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
