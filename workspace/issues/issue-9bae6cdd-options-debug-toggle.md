Created: 2026 June 12

```yaml
issue_info:
  id: "issue-9bae6cdd"
  title: "No in-app control to toggle debug logging"
  date: "2026-06-12"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-9bae6cdd"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    Debug logging to debug.log can only be enabled at launch via the --debug
    flag. Under systemd auto-start there is no opportunity to pass the flag, so
    debug.log is never populated in normal operation. An OPTIONS-screen toggle is
    required to enable/disable debug logging at runtime via the
    GTachApplication.toggle_debug_logging() method delivered in bd8f95b7.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.61"

reproduction:
  prerequisites: "GTach running under systemd auto-start (no --debug flag)."
  steps:
    - "Long-press to enter OPTIONS."
    - "Observe: only 'Clear settings' and 'Bluetooth/Simulation mode' buttons exist."
    - "No way to enable debug logging without restarting with --debug."
  frequency: "always"
  reproducibility_conditions: "Any boot under systemd."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    The OPTIONS screen presents a 'Debug: Off' / 'Debug: On' toggle button.
    Tapping it calls toggle_debug_logging(), which starts or stops writing to
    debug.log immediately. The button label reflects the current state.
  actual: >
    No toggle exists. Debug logging is fixed at launch and cannot change at runtime.
  impact: >
    Field diagnosis requires a restart with manual flag injection, impractical
    on an unattended device.
  workaround: "Restart with --debug (not possible under unattended systemd)."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    The debug toggle mechanism (toggle_debug_logging) exists on GTachApplication
    but has no UI affordance. DisplayManager holds no reference to the application
    and the OPTIONS screen has only two buttons.
  technical_notes: >
    DisplayManager already uses a callback pattern for cross-domain actions
    (_setup_entry_callback, set by app.py after DisplayManager creation). The same
    pattern provides a _debug_toggle_callback. DisplayManager tracks its own
    _debug_logging_on flag for label state, initialised from the launch --debug
    value passed by app.py. The OPTIONS screen adds a third button; geometry is
    tightened to fit three buttons in the circular safe zone.
  related_issues:
    - issue_ref: "issue-bd8f95b7"
      relationship: "blocked_by"

resolution:
  assigned_to: "Claude Code"
  target_date: "2026-06-12"
  approach: "See change-9bae6cdd"
  change_ref: "change-9bae6cdd"
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

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-9bae6cdd"
  test_refs: []

notes: >
  Depends on bd8f95b7 (toggle_debug_logging delivered). Completes logging Item 3.

version_history:
  - version: "1.0"
    date: "2026-06-12"
    author: "William Watson"
    changes:
      - "Initial issue document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
