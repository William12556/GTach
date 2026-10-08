Created: 2026 October 07

# Issue: Low-Severity Correctness Defects

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-4005360c"
  title: "Low-severity correctness defects across comm, core, display and utils: socket and process leaks, stuck simulation cancel flags, shadowed builtins, unused retry delay, unguarded flag, unbounded lists, a font mutated in a shared cache, wall-clock durations, a wrong device attribute, stale framebuffer handles, out-of-range configuration values"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-4005360c"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 low findings A12, A13, A16, A18, B07
    (bare except), B09, B10, B12, C10, C13, C15, C16, D08 (attribute
    defect), D11, and a CLAUDE.md §4 rule 8 clarification arising from
    report-453f0a80.

affected_scope:
  components:
    - name: "comm: tcp_transport, sim_bluetooth, system_bluetooth, transport"
      file_path: "src/gtach/comm/"
    - name: "core: watchdog"
      file_path: "src/gtach/core/watchdog.py"
    - name: "app, main"
      file_path: "src/gtach/app.py, src/gtach/main.py"
    - name: "display: splash, typography, manager, touch, touch_interface, input/touch_coordinator, setup_components/state/coordinator, async_operations, setup_components/rendering/device_surfaces, rendering/engine"
      file_path: "src/gtach/display/"
    - name: "utils: config (ConfigStore.load ranges)"
      file_path: "src/gtach/utils/config.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "Source review."
  steps:
    - "See test_data."
  frequency: "always"
  reproducibility_conditions: "Deterministic from source."
  test_data: >
    A12 tcp_transport._open leaves the socket open when connect raises.
    A13 SimBluetoothPairing cancel events are never cleared, so simbt
    breaks after the first Cancel. A16 transport.py defines
    ConnectionError and TimeoutError, shadowing builtins. A18
    system_bluetooth kills/terminates bluetoothctl without wait() and
    returns a dict still written by a reader thread. B07 watchdog.py
    `except:` (bare). B09 the transports store _retry_delay, but
    reconnect_indefinitely is started without it and the display reads
    a non-existent retry_delay. B10 implicit Optional annotations
    (main._start_handler/_debug_handler, app config_path) and run()
    annotated NoReturn although it returns. B12 _obd_started is checked
    and set without a lock from two threads. C10 an fps_limit of 0
    passes ConfigStore.load and divides by zero each frame. C13
    splash._font_render_times grows without bound, `% 1 == 0` is always
    true (INFO log every frame), and progress divides by a zero duration.
    C15 get_rpm_large_font calls set_bold on the shared cached font;
    DisplayManager logs every touch at INFO. C16 touch, splash, setup
    interaction and async-operation durations use time.time(). D08
    device_surfaces reads device.rssi, which the setup BluetoothDevice
    lacks (signal_strength), so signal bars never render. D11
    rendering cleanup closes fb and fb_dev without clearing them.
    CLAUDE.md rule 8 forbids blocking I/O under any lock, while
    DeviceStore deliberately writes its file under its own lock.
  error_output: "None."

behavior:
  expected: "As described per item in change-4005360c."
  actual: "As in test_data."
  impact: "Minor leaks, misleading logs, broken simulation after Cancel, missing signal bars."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Independent small defects."
  technical_notes: "Dead code is handled separately by change-cd5ec050."
  related_issues:
    - issue_ref: "issue-cd5ec050"
      relationship: "related. Dead-code removal in the same modules."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-4005360c."
  change_ref: "change-4005360c"
  resolved_date: "2026-10-08"
  resolved_by: "change-4005360c"
  fix_description: "Fourteen low-severity corrections (TCP socket closed on connect failure, per-run simulated cancel, renamed transport exceptions, reaped bluetoothctl children, no bare except, real retry_delay, Optional annotations, locked _obd_started, range-checked config values, bounded splash timing data, an unshared bold RPM font, monotonic durations, signal_strength in device surfaces, cleared framebuffer handles) and the CLAUDE.md rule 8 file-lock clarification (commit 2ade5a3769ce5396447b6526328a9b153af90182)."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Signal bars shown on DEVICE_LIST (Session E; small, tracked separately in task.md); simbt discovery after Cancel covered by tests/test_low_defects.py::TestSimPairingCancelIsPerRun; real discovery after Cancel passed on the Pi."
  closure_notes: "Closed at audit-36b6ea95 close-out after on-device verification."

prevention:
  preventive_measures: "Unit tests per item."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-4005360c; on the Pi, signal bars appear on DEVICE_LIST."
  verification_results: "All verification steps complete; see verification.test_results."

traceability:
  design_refs: []
  change_refs:
    - "change-4005360c"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 A12, A13, A16, A18, B07, B09, B10, B12, C10, C13, C15, C16, D08, D11."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial issue document for Phase 5 low-severity defects."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in 2ade5a3769ce5396447b6526328a9b153af90182; awaiting on-device verification."
  - version: "1.2"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "On-device verification complete; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial issue document. Low-severity correctness defects. |
| 1.1 | 2026-10-07 | Fix implemented in 2ade5a3769ce5396447b6526328a9b153af90182; awaiting on-device verification. |
| 1.2 | 2026-10-08 | On-device verification complete; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
