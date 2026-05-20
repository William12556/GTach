Created: 2026 May 20

```yaml
issue_info:
  id: "issue-f3a7c2e1"
  title: "Acknowledgement screen does not block until explicitly dismissed"
  date: "2026-05-20"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a7c2e1"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Observed during live Pi test with --transport rfcomm. After the splash
    screen completes, the app transitions immediately to the RPM display
    without waiting for the operator to dismiss the acknowledgement screen.
    Log confirms: 'Splash completed - showing acknowledgement screen' is
    logged, but no dismissal event is recorded before RPM rendering begins.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.2.44"

reproduction:
  prerequisites: "Run gtach --transport rfcomm --debug on Pi"
  steps:
    - "Launch GTach"
    - "Observe splash screen complete"
    - "Acknowledgement screen is shown but immediately transitions to RPM display"
  frequency: "always"
  reproducibility_conditions: "Any run where ack_state.yaml does not exist or is not acknowledged"
  preconditions: ""
  test_data: "gtach-debug_PI.log 2026-05-20"
  error_output: |
    11:58:31 DisplayManager INFO Splash completed - showing acknowledgement screen
    (no ACK dismissed log entry)
    11:58:32 DisplayManager DEBUG RPM 0 band colour bg=(0, 0, 0)

behavior:
  expected: "Acknowledgement screen blocks all display transitions until operator explicitly dismisses it via touch."
  actual: "Acknowledgement screen is set as the mode but the display loop immediately renders the RPM display without waiting for a dismissal event."
  impact: "Operator acknowledgement requirement is bypassed on every startup where ack state is not already recorded."
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies:
    - library: "pygame"
      version: ""
  domain: "domain_1"

analysis:
  root_cause: >
    DisplayManager._render_normal_modes() does not check for
    DisplayMode.ACKNOWLEDGEMENT. When the mode is set to ACKNOWLEDGEMENT,
    _render_normal_modes() falls through without rendering a dismissable
    screen, and no blocking mechanism prevents transition to RPM rendering.
    The acknowledgement mode is set but never rendered or waited upon.
  technical_notes: >
    _draw_splash_mode() correctly sets config.mode = DisplayMode.ACKNOWLEDGEMENT.
    However _render_normal_modes() only handles DIGITAL, RADIAL, and SETTINGS.
    ACKNOWLEDGEMENT is unhandled. A touch-to-dismiss handler and explicit
    mode transition on acknowledgement are required.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Add ACKNOWLEDGEMENT rendering to _render_normal_modes(). Implement a
    dismissal handler that transitions to _post_splash_mode on tap.
    Do not auto-transition on timeout.
  change_ref: "change-f3a7c2e1"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "DisplayMode enum values must have corresponding render branches in _render_normal_modes()."
  process_improvements: ""

traceability:
  design_refs: []
  change_refs:
    - "change-f3a7c2e1"
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
