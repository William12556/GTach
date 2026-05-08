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
  status: "closed"
  severity: "high"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: "change-b4e7c2f1"
    change_iteration: 1

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
  prerequisites: "App running with --transport simbt. Watchdog must trigger obd_protocol restart."
  steps:
    - "Start gtach --transport simbt"
    - "Complete setup, allow OBD to connect"
    - "Wait ~45 seconds for watchdog to fire obd_protocol critical timeout"
    - "Observe RPM display for erratic jumps"
  frequency: "always"
  reproducibility_conditions: "Requires watchdog timeout on obd_protocol thread."
  preconditions: ""
  test_data: "gtach-simbt.log"
  error_output: ""

behavior:
  expected: "Single OBD polling thread active at all times. RPM values follow a single smooth sine sweep."
  actual: >
    Two obd_protocol threads run concurrently after watchdog restart. Each thread has an
    independent sine wave phase. Display alternates between the two threads' RPM values
    producing apparent random jumps and RPM screen flickering.
  impact: >
    RPM display is unreliable whenever a watchdog restart has occurred.
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
    ThreadManager._restart_thread() creates and starts a new threading.Thread but
    never signals or joins the original thread. The original OBDProtocol thread
    therefore continues to run indefinitely alongside the new thread.
  technical_notes: >
    Fix: store an optional stop_func callable in ThreadInfo. ThreadManager calls
    stop_func() before restart. OBDProtocol passes self.stop as stop_func.

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Implement Option A: add optional stop_func field to ThreadInfo; call it in
    _restart_thread before spawning new thread; register OBDProtocol.stop as stop_func.
  change_ref: "change-b4e7c2f1"
  resolved_date: "2026-05-08"
  resolved_by: "Claude Code"
  fix_description: >
    stop_func: Optional[Callable] = None added to ThreadInfo. register_thread()
    accepts stop_func kwarg. _restart_thread calls stop_func() before new thread.
    OBDProtocol.__init__ passes stop_func=self.stop.

verification:
  verified_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: "Code inspection confirmed. stop_func present in thread.py and obd.py."
  closure_notes: "Implemented. Closed."

prevention:
  preventive_measures: "All thread registrations that wrap stateful objects with a stop method should register stop_func at registration time."
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "Run gtach --transport simbt"
    - "Allow OBD to connect and run for at least 90 seconds"
    - "Confirm log shows no paired SimTransport TX:010C lines"
    - "Confirm RPM sweep is smooth with no jumps"
  verification_results: "stop_func wiring confirmed in source. Full runtime test pending."

traceability:
  design_refs: []
  change_refs:
    - "change-b4e7c2f1"
  test_refs: []

notes: >
  Two trivial fixes were applied under §1.4.12 exemption in the same session:
  (1) obd.py inner loop heartbeat.
  (2) setup.py clean exit.
  This issue addresses the restart path defect.

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
  - version: "1.1"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Closed — implementation verified in source"

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
| 1.1 | 2026-05-08 | Closed — implementation verified in source |

---

Copyright (c) 2026 William Watson. MIT License.
