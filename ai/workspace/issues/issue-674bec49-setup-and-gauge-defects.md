Created: 2026 October 07

# Issue: Setup Lifecycle, Gauge Range, Per-Frame File Reads and Hidden Errors

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-674bec49"
  title: "Setup threads are not stopped on completion, cancel or re-entry; the gauge is fixed at 7000 RPM; devices.yaml is read every frame on WELCOME; setup error messages are visible for one frame or replaced by fixed text"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-674bec49"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 findings C01, C05, C06 and C08 (medium).
    The watchdog restart cycle part of C01 was removed by
    change-860fd5f7; the remaining C01 items are covered here.

affected_scope:
  components:
    - name: "SetupDisplayManager.stop_setup / start_setup / _render_welcome_screen / _update_cached_screen_touch_regions / _on_screen_transition / _render_device_list_screen / handle_touch_event"
      file_path: "src/gtach/display/setup.py"
    - name: "GTachApplication._on_setup_complete / _start_setup_mode"
      file_path: "src/gtach/app.py"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "GTach on the Pi or the development host."
  steps:
    - "C01: on WELCOME with a stored device, tap Cancel; the setup thread keeps looping. Re-enter setup from DISCONNECTED; the previous SetupDisplayManager's thread is never stopped."
    - "C05: select generic_na_4cyl (redline 7500); RPM above 7000 is not shown and the redline mark is off scale."
    - "C06: stay on WELCOME; devices.yaml is parsed on every frame."
    - "C08: fail OBD verification after pairing; 'OBD check failed' is visible for one frame on DEVICE_LIST. On WELCOME, any error is shown as 'No devices found'."
  frequency: "always"
  reproducibility_conditions: "Deterministic from source."
  test_data: >
    setup.py stop_setup sets _shutdown_event and joins the setup thread;
    it is called only from GTachApplication.shutdown. 'cancel_setup'
    calls on_complete from the touch thread without stopping the loop.
    app._start_setup_mode creates a new SetupDisplayManager without
    stopping the previous one. on_complete is also invoked from the
    setup thread itself (setup loop on COMPLETE), so any stop called
    there must not join the current thread (cf. issue-f3c9a2e7).

    manager.py _draw_radial_mode: `rpm = max(0, min(7000, rpm))` and
    `max_rpm = 7000`; ticks iterate range(1000, 8000, 1000); the centre
    readout comment relies on the 7000 clamp for a three-glyph width.
    engine_profiles.yaml redlines: 6000 (abarth_595_turismo, in use on
    the device), 7000, 7500.

    setup.py _update_cached_screen_touch_regions (every frame on cached
    WELCOME) and _render_welcome_screen construct DeviceStore() and read
    the primary device.

    setup.py _render_device_list_screen clears error_message
    immediately after drawing it; _render_welcome_screen draws the fixed
    text 'No devices found' for any error_message.
  error_output: "None."

behavior:
  expected: >
    Setup threads end when setup ends; the gauge covers the configured
    redline; no file I/O per frame; error messages stay visible until
    the next user action and say what happened.
  actual: "As in test_data. All confirmed in source."
  impact: >
    Leaked setup threads; gauge saturation below redline for profiles
    above 6500 RPM; CPU on the Pi Zero; operators cannot see why pairing
    or the Continue probe failed.
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Independent gaps; see test_data."
  technical_notes: >
    Gauge range rule: max_rpm = min(9000, max(7000,
    ceil((redline_rpm + 500) / 1000) * 1000)). This keeps the current
    profile (redline 6000) at exactly 7000, so the display on the
    device is unchanged; gives 8000 for redlines 7000 and 7500; and caps
    at 9000 so the centre readout stays three glyphs and tick numerals
    one digit.

    The WELCOME error line can be long (the discovery message is a full
    sentence). Rendering it must fit the 480 px circle.
  related_issues:
    - issue_ref: "issue-860fd5f7"
      relationship: "related. Removed the watchdog restart cycle for the completed setup thread."
    - issue_ref: "issue-f3c9a2e7"
      relationship: "related. Prior setup-loop self-join defect."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-674bec49."
  change_ref: "change-674bec49"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Unit tests per defect."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-674bec49."
    - "After the fix: on the Pi, the gauge looks unchanged with abarth_595_turismo; Cancel on WELCOME and re-entry leave no extra SetupManager thread (stacks.log with debug on)."
  verification_results: "First step complete."

traceability:
  design_refs: []
  change_refs:
    - "change-674bec49"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 C01, C05, C06, C08."

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
      - "Initial issue document from audit-36b6ea95 C01, C05, C06, C08."

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
| 1.0 | 2026-10-07 | Initial issue document. Setup lifecycle, gauge range, per-frame reads, hidden errors. |

---

Copyright (c) 2026 William Watson. MIT License.
