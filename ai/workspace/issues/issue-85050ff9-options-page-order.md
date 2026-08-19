Created: 2026 August 19

# Issue: Options Menu Page Order

---

## 1.0 Table of Contents

[2.0 Template](<#2.0 template>)
[Version History](<#version history>)

---

## 2.0 Template

```yaml
# T03 Issue Template v1.3 - YAML Format

issue_info:
  id: "issue-85050ff9"
  title: "Options menu shows Simulation/Debug on the default page instead of Clear settings/Check for updates"
  date: "2026-08-19"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-85050ff9"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    The OPTIONS screen always opens on page 0 (change-8c5a1e73). Page 0
    currently holds Simulation mode and Debug toggle; page 1 holds
    Clear settings and Check for updates. The operator wants Clear
    settings and Check for updates shown first by default, with
    Simulation mode and Debug toggle moved to the second page.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: ""

reproduction:
  prerequisites: "Application running, swipe down into OPTIONS from RADIAL."
  steps:
    - "Swipe down from the RADIAL gauge to enter OPTIONS."
  frequency: "always"
  reproducibility_conditions: "Every OPTIONS entry; _options_page resets to 0 each time (change-8c5a1e73)."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: "Clear settings and Check for updates are the first page shown on OPTIONS entry."
  actual: "Simulation mode and Debug toggle are the first page shown on OPTIONS entry."
  impact: "No functional defect; purely a default-page ordering preference."
  workaround: "Swipe left/right to reach the desired page."

environment:
  python_version: "3.11"
  os: "Debian GNU/Linux 11 (Bullseye)"
  dependencies: []
  domain: ""

analysis:
  root_cause: >
    _register_options_menu_regions and _draw_options_menu assign
    (simulation_mode, debug_toggle) to page 0 and
    (clear_settings, check_updates) to page 1. No defect; the
    assignment is simply the opposite of the desired default.
  technical_notes: >
    Swap is confined to two methods in manager.py plus three docstring
    references to the current page assignment
    (_register_options_menu_regions, _draw_options_menu,
    _on_clear_settings_requested). No interface, state, or touch-region
    ID changes. Does not qualify for the P03 §1.4.12 trivial exemption
    because it is not confined to a single function.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: "See change-85050ff9."
  change_ref: "change-85050ff9"
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
    - "Swipe down into OPTIONS and confirm Clear settings / Check for updates render first."
    - "Swipe left/right and confirm Simulation mode / Debug toggle render on the second page."
    - "Confirm touch regions on each page match the drawn labels."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-85050ff9"
  test_refs: []

notes: "Related prior work: change-8c5a1e73 introduced the two-page paging model this issue reorders."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-19"
    author: "William Watson"
    changes:
      - "Initial issue creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.3"
  schema_type: "t03_issue"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial issue creation. |

---

Copyright (c) 2026 William Watson. MIT License.
