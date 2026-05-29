Created: 2026 May 29

```yaml
change_info:
  id: "change-a1f4c7e2"
  title: "Add Cancel button to Welcome screen when stored device exists"
  date: "2026-05-29"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a1f4c7e2"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-a1f4c7e2"
  description: >
    User requires ability to abort setup from the WELCOME screen and return to
    the currently stored device when setup is entered from the options screen.

scope:
  summary: >
    Two surgical modifications: (1) remove premature device deletion from
    _re_enter_setup() in app.py; (2) add a conditional Cancel button to
    _render_welcome_screen() in setup.py that is visible only when a stored
    device exists, invoking _on_complete() on tap.
  affected_components:
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master"
      sections:
        - "Setup flow"
  out_of_scope:
    - "New screens or state machine states"
    - "Changes to CURRENT_DEVICE screen"
    - "Changes to other setup screens"

rational:
  problem_statement: >
    _re_enter_setup() deletes the stored device unconditionally before entering
    setup. Consequently, by the time WELCOME renders, there is no device to
    return to, and no cancel path exists.
  proposed_solution: >
    Preserve the stored device on re-entry. Add a Cancel button to WELCOME that
    renders conditionally (DeviceStore has a primary device). Cancel invokes
    _on_complete(), which already correctly exits setup and starts OBD.
  alternatives_considered:
    - option: "Add Cancel to CURRENT_DEVICE screen instead"
      reason_rejected: "CURRENT_DEVICE already has Continue/New Setup; user request is specifically for WELCOME."
  benefits:
    - "User can abort accidental setup entry without re-pairing."
    - "No new state or screens required."
  risks:
    - risk: "_on_setup_complete _obd_started guard may block re-entry cancel"
      mitigation: "_re_enter_setup already resets _obd_started = False before calling _start_setup_mode."

technical_details:
  current_behavior: >
    _re_enter_setup() removes the stored device then calls _start_setup_mode().
    WELCOME screen renders a single 'Start Setup' button regardless of device state.
  proposed_behavior: >
    _re_enter_setup() no longer removes the stored device. WELCOME screen checks
    DeviceStore; if a device exists, a secondary 'Cancel' button is rendered below
    'Start Setup'. Tapping Cancel calls _on_complete().
  implementation_approach: >
    Minimal targeted edits. No new classes, enums, or screens.
  code_changes:
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: "Remove device deletion block from _re_enter_setup()"
      functions_affected:
        - "_re_enter_setup"
      classes_affected:
        - "GTachApplication"
    - component: "SetupDisplayManager"
      file: "src/gtach/display/setup.py"
      change_summary: >
        _render_welcome_screen: split Start button into two-button layout when
        device exists; add 'cancel_setup' touch region.
        _handle_touch_action: add 'cancel_setup' branch invoking _on_complete().
        _update_cached_screen_touch_regions: add cancel_setup rect when device exists.
      functions_affected:
        - "_render_welcome_screen"
        - "_handle_touch_action"
        - "_update_cached_screen_touch_regions"
      classes_affected:
        - "SetupDisplayManager"
  interface_changes: []

testing_requirements:
  test_approach: "Manual verification on device."
  test_cases:
    - scenario: "No stored device — enter setup"
      expected_result: "WELCOME shows only 'Start Setup'. No Cancel button."
    - scenario: "Stored device — enter setup from options"
      expected_result: "WELCOME shows 'Start Setup' and 'Cancel'. Tapping Cancel exits setup and resumes OBD."
    - scenario: "Stored device — tap Start Setup"
      expected_result: "Normal discovery flow proceeds; device cleared on 'New Setup' action."
  regression_scope:
    - "Normal first-run setup (no stored device)"
    - "New Setup flow from CURRENT_DEVICE screen"
    - "_re_enter_setup from DISCONNECTED screen"
  validation_criteria:
    - "Cancel button absent when no device stored."
    - "Cancel button present when device stored."
    - "Cancel returns to gauge/digital display without re-pairing."
    - "Start Setup proceeds to DISCOVERY as before."

implementation:
  implementation_steps:
    - step: "Remove device deletion from _re_enter_setup() in app.py"
      owner: "Claude Code"
    - step: "Modify _render_welcome_screen() for conditional Cancel button"
      owner: "Claude Code"
    - step: "Add cancel_setup handler in _handle_touch_action()"
      owner: "Claude Code"
    - step: "Update _update_cached_screen_touch_regions() for cancel_setup rect"
      owner: "Claude Code"
  rollback_procedure: "Revert two files via git."
  deployment_notes: "Build wheel and deploy to Pi as per standard workflow."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  related_changes: []
  related_issues:
    - issue_ref: "issue-a1f4c7e2"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-05-29"
    author: "William Watson"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
