# Issue: Connecting Indicator

Created: 2026 November 22

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-9accfbe0"
  title: "While GTach connects, the gauge shows the information symbol as if the connection had failed, and nothing shows that the app is still working"
  date: "2026-11-22"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-9accfbe0"
    change_iteration: 1

source:
  origin: "test_result"
  test_ref: "issue-adb3afeb verification (device test 2026-11-20)"
  description: >
    Observed during the device test of change-adb3afeb: at startup the
    amber information symbol and red status dot show while GTach connects
    to the emulator. Expected under design-b8c9d0e1 v2.1 (no sample counts
    as a lost link). design-b8c9d0e1 v2.2 adds a Connecting sub-state and
    a reconnect indicator around the status dot.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs:
    - design_ref: "design-b8c9d0e1-component_display_manager (v2.2, sections 5.3, 5.4, 5.7, 8.0)"
  version: "1.0.0rc1 (ce1ef47)"

reproduction:
  prerequisites: "GTach at ce1ef47 on gtach.local; emulator on ELM327-Emulator.local."
  steps:
    - "Restart gtach, or stop and start the emulator."
    - "Watch the gauge until the first samples arrive."
  frequency: "always"
  reproducibility_conditions: "Any connect or reconnect."
  preconditions: ""
  test_data: ""
  error_output: "None (behaviour, not an error)."

behavior:
  expected: >
    Per design-b8c9d0e1 v2.2: while no connect has failed, the dimmed gauge
    shows no symbol, a yellow status dot and the reconnect indicator around
    it. After a failed connect or a dropped link, the information symbol and
    a red status dot show, with the reconnect indicator still turning.
  actual: "Information symbol and red dot from the first frame; no indication of activity on the gauge."
  impact: "Startup reads as a failure, and a long connect can look like a frozen app."
  workaround: "None."

environment:
  python_version: "3.9+"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "as installed"
  domain: "domain_1"

analysis:
  root_cause: "Design gap in v2.1: the disconnected view has one presentation for connecting and failed."
  technical_notes: >
    OBDTransport.last_failure_cause is None until a connect fails, cleared on
    every successful connect, and set on a failed connect or drop_link. It
    reaches the display through _link_cause_callback.
  related_issues:
    - issue_ref: "issue-adb3afeb"
      relationship: "related"

resolution:
  assigned_to: "Claude Code (cloud)"
  target_date: ""
  approach: "change-9accfbe0"
  change_ref: "change-9accfbe0"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: ""
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "pytest tests/ passes."
    - "On gtach.local: at startup the yellow dot and turning indicator show, no symbol; with the emulator stopped, after the first failed connect the amber symbol and red dot show with the indicator turning; a tap on the centre opens the panel in both sub-states; recovery returns to the live gauge."
  verification_results: ""

traceability:
  design_refs:
    - "design-b8c9d0e1-component_display_manager v2.2"
  change_refs:
    - "change-9accfbe0"
  test_refs: []

notes: ""

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-22"
    author: "William Watson"
    changes:
      - "Initial issue."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "issue"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-22 | Initial issue |

---

Copyright (c) 2026 William Watson. MIT License.
