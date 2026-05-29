Created: 2026 May 29

```yaml
issue_info:
  id: "issue-a1f4c7e2"
  title: "Welcome screen has no cancel option when a stored device exists"
  date: "2026-05-29"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-a1f4c7e2"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    When setup is entered from the options screen and a device is already stored,
    the WELCOME screen offers no way to abort. The user cannot return to the existing
    device without completing a new setup flow.

affected_scope:
  components:
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "current"

reproduction:
  prerequisites: "A device is stored in DeviceStore."
  steps:
    - "Enter setup from the options screen."
    - "Observe WELCOME screen — only 'Start Setup' is available."
    - "No cancel/abort path exists."
  frequency: "always"
  reproducibility_conditions: "Stored device present; setup entered from options screen."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    When a stored device exists, the WELCOME screen displays a 'Cancel' button.
    Tapping Cancel exits setup and resumes normal operation with the existing device.
  actual: >
    WELCOME screen shows only 'Start Setup'. No cancel path is available.
  impact: "User is forced through full re-pairing flow even when they did not intend to replace the device."
  workaround: "None."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    _re_enter_setup() in app.py deletes the stored device before entering setup,
    so WELCOME has no device context to cancel back to. The Welcome screen also
    has no conditional Cancel button.
  technical_notes: >
    Fix requires two changes:
    1. Remove device deletion from _re_enter_setup() — device should only be
       cleared by the explicit 'New Setup' action in setup.py.
    2. Add a conditional Cancel button to _render_welcome_screen() that is visible
       only when DeviceStore has a primary device. The cancel action invokes
       _on_complete(), which exits setup and resumes OBD via the existing device.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: "2026-05-29"
  approach: "See change-a1f4c7e2"
  change_ref: "change-a1f4c7e2"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Ensure setup entry paths do not mutate DeviceStore before user intent is confirmed."
  process_improvements: ""

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-a1f4c7e2"
  test_refs: []

notes: ""

version_history:
  - version: "1.0"
    date: "2026-05-29"
    author: "William Watson"
    changes:
      - "Initial issue document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
