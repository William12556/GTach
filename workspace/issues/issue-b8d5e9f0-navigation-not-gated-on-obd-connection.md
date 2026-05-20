Created: 2026 May 20

```yaml
issue_info:
  id: "issue-b8d5e9f0"
  title: "Display navigation not gated on OBD connection state"
  date: "2026-05-20"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-b8d5e9f0"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Observed during live Pi test with --transport rfcomm. RFCOMM connection
    fails with [Errno 112] Host is down. Despite no OBD connection, swipe
    gestures navigate between DIGITAL and RADIAL display modes freely.
    Only setup mode should be accessible while OBD is disconnected.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "NavigationGestureHandler"
      file_path: "src/gtach/display/navigation_gestures.py"
  designs: []
  version: "0.2.44"

reproduction:
  prerequisites: "Run gtach --transport rfcomm --debug with no ELM327 device present"
  steps:
    - "Launch GTach"
    - "Allow splash and acknowledgement screens to complete"
    - "Swipe left or right on the display"
    - "Display transitions to Radial or Digital mode"
  frequency: "always"
  reproducibility_conditions: "OBD transport disconnected or failing"
  preconditions: ""
  test_data: "gtach-debug_PI.log 2026-05-20"
  error_output: |
    11:58:32 RFCOMMTransport ERROR Failed to connect to RFCOMM device: [Errno 112] Host is down
    11:58:35 DisplayManager DEBUG Radial mode: RPM=0
    (navigation accepted despite no connection)

behavior:
  expected: >
    While OBD is disconnected, swipe navigation between DIGITAL and RADIAL
    is blocked. Only long-press to enter setup mode is permitted.
    A 'waiting for connection' indicator is shown.
  actual: "Swipe gestures freely navigate between DIGITAL and RADIAL regardless of OBD connection state."
  impact: "User can interact with tachometer displays that show meaningless RPM=0 data with no indication that no valid OBD data source is present."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    _handle_swipe_left() and _handle_swipe_right() in DisplayManager check
    only the current display mode (DIGITAL/RADIAL) with no check against
    OBD connection state. ConnectionStatus is available via
    _draw_status_indicator() logic (thread_manager.get_thread_status('transport'))
    but is not consulted in gesture handlers.
  technical_notes: >
    The transport thread status is already queried in _draw_status_indicator().
    The same check (get_thread_status('transport') == ThreadStatus.RUNNING)
    should be used as a gate in the swipe handlers. When not RUNNING, swipe
    gestures should be silently ignored. Long-press to settings must remain
    unblocked.
  related_issues:
    - issue_ref: "issue-f3a7c2e1"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Add OBD connection state check to _handle_swipe_left() and
    _handle_swipe_right(). If transport thread is not RUNNING, return
    TouchAction.NONE immediately. _handle_long_press() is unaffected.
  change_ref: "change-b8d5e9f0"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Gesture handlers must consult connection state before permitting mode transitions."
  process_improvements: ""

traceability:
  design_refs: []
  change_refs:
    - "change-b8d5e9f0"
  test_refs: []

notes: ""

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-05-20"
    author: "William Watson"
    changes:
      - "Initial issue creation"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
