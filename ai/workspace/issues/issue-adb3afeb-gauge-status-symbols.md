# Issue: Gauge Status Symbols

Created: 2026 November 20

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-adb3afeb"
  title: "Engine off and DISCONNECTED are shown as text and a full screen; design-b8c9d0e1 v2.1 shows them as symbols on the gauge"
  date: "2026-11-20"
  reporter: "William Watson"
  status: "resolved"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-adb3afeb"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    UI polish agreed in the planning session of 2026-11-19: hide or
    simplify information where reasonable. design-b8c9d0e1 was revised to
    v2.1 (commit f6427b3) and the source no longer matches it.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "Palette, DAY_PALETTE, NIGHT_PALETTE"
      file_path: "src/gtach/display/models.py"
  designs:
    - design_ref: "design-b8c9d0e1-component_display_manager (v2.1, sections 3.0, 4.0, 5.2-5.5, 5.7, 6.0, 8.0)"
  version: "1.0.0rc1"

reproduction:
  prerequisites: "GTach with the source at commit f6427b3."
  steps:
    - "Engine off: run the emulator engineoff scenario; the centre disc shows the text 'Engine off'."
    - "DISCONNECTED: stop the emulator; the gauge is replaced by the full black-on-yellow DISCONNECTED screen."
    - "OPTIONS: swipe down; the menu shows the title 'Options'."
  frequency: "always"
  reproducibility_conditions: "Any."
  preconditions: ""
  test_data: ""
  error_output: "None (behaviour, not an error)."

behavior:
  expected: >
    Per design-b8c9d0e1 v2.1: Engine off shows a grey ignition-key symbol
    in the centre disc. DISCONNECTED shows the gauge dimmed with an amber
    information symbol; a tap on the symbol opens the existing DISCONNECTED
    panel, and a tap outside its buttons closes it. OPTIONS has no title.
  actual: "Text for Engine off; a full-screen DISCONNECTED view; an OPTIONS title."
  impact: "Presentation only. The instrument reads as a prototype rather than a finished product."
  workaround: "None needed."

environment:
  python_version: "3.9+"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "as installed"
  domain: "domain_1"

analysis:
  root_cause: "Design change (design-b8c9d0e1 v2.0 -> v2.1); not a defect."
  technical_notes: >
    The DISCONNECTED and Engine off conditions, their evaluation and
    precedence (design-b8c9d0e1 sections 5.3, 5.4) are unchanged; only
    what is drawn and which touch regions exist change.
  related_issues:
    - issue_ref: "issue-b29cbd71"
      relationship: "related"

resolution:
  assigned_to: "Claude Code (cloud)"
  target_date: ""
  approach: "change-adb3afeb"
  change_ref: "change-adb3afeb"
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
    - "On gtach.local with the emulator: engineoff scenario shows the key symbol; emulator stopped shows the dimmed gauge and amber symbol; tap opens and closes the panel; Setup and Reset work from the panel; OPTIONS has no title; day and night palettes both legible."
  verification_results: ""

traceability:
  design_refs:
    - "design-b8c9d0e1-component_display_manager v2.1"
    - "design-gtach-master v3.1"
  change_refs:
    - "change-adb3afeb"
  test_refs: []

notes: "Remote-workflow trial: implemented by a Claude Code cloud session on a claude/* branch, merged by pull request."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-20"
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
| 1.0 | 2026-11-20 | Initial issue |

---

Copyright (c) 2026 William Watson. MIT License.
