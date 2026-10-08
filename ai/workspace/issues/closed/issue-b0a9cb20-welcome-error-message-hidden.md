Created: 2026 October 08

# Issue: WELCOME Error Message Not Visible

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-b0a9cb20"
  title: "The WELCOME screen draws error_message in orange on the beige setup background (contrast 1.18:1), so 'Device not available' is effectively not visible"
  date: "2026-10-08"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-b0a9cb20"
    change_iteration: 1

source:
  origin: "on_device_verification"
  test_ref: "ai/workspace/test/test-36b6ea95-on-device-verification.md (Session E, E1)"
  description: "Verification step of issue-674bec49: 'Device not available' on WELCOME after a failed Continue probe."

affected_scope:
  components:
    - name: "SetupDisplayManager._render_welcome_screen"
      file_path: "src/gtach/display/setup.py"
  designs: []
  version: "0.4.7"

reproduction:
  prerequisites: "Adapter paired; adapter off."
  steps:
    - "DISCONNECTED -> Setup -> CURRENT_DEVICE -> Continue."
  frequency: "always"
  reproducibility_conditions: "Two-button WELCOME layout (stored device)."
  test_data: >
    debug.log 2026-10-08: error_message = 'Device not available' set at
    09:08:10 and 09:25:24 and held until the next tap (20 s at 09:25);
    operator reports the text was not visible.
  error_output: "None."

behavior:
  expected: "The message is visible on WELCOME until the next tap."
  actual: "The message is not visible."
  impact: "The operator is not told why Continue returned to WELCOME."
  workaround: "None."

environment:
  python_version: "3.9.2"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    Confirmed on device 2026-10-08 (0.4.8): the text is drawn but hard to
    see. It is rendered in colors['warning'] (255,165,0) on
    colors['background'] (216,200,146), a contrast ratio of 1.18:1
    (readable text needs at least 4.5:1). The first hypothesis, placement
    at y=440 under the Cancel button and beyond the 200 px safe radius
    (change-b0a9cb20 iteration 1), did not resolve the defect; the new
    position (y=235) is retained.
  technical_notes: "Free band between the description (last line y=192) and the Start Setup button (y=270 two-button, y=330 one-button)."
  related_issues:
    - "issue-674bec49"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-b0a9cb20."
  change_ref: "change-b0a9cb20"
  resolved_date: "2026-10-08"
  resolved_by: "change-b0a9cb20"
  fix_description: "change-b0a9cb20 iteration 1 (position y=235) deployed in 0.4.8, text still hard to see; iteration 2 (dark red error_text colour, 6.0:1) implemented 2026-10-08; verified on device in 0.4.9."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Pi 0.4.9: adapter off, DISCONNECTED -> Setup -> Continue; 'Device not available' clearly visible in dark red on WELCOME."
  closure_notes: "Closed after on-device verification. Completes the remaining on-device step of issue-674bec49."

prevention:
  preventive_measures: "Unit test asserting the message lies inside the safe radius and clear of the buttons."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Pi: adapter off; DISCONNECTED -> Setup -> Continue; 'Device not available' visible on WELCOME until the next tap."
  verification_results: "Passed 2026-10-08 (0.4.9)."

traceability:
  design_refs: []
  change_refs:
    - "change-b0a9cb20"
  test_refs: []

notes: "Closing this issue also completes the remaining on-device step of issue-674bec49."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Initial issue document from Session E."
  - version: "1.1"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Root cause corrected to low contrast after the 0.4.8 re-test; placement hypothesis disproved."
  - version: "1.2"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Verified on device (0.4.9); closed."

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
| 1.0 | 2026-10-08 | Initial issue document. |
| 1.1 | 2026-10-08 | Root cause corrected: contrast 1.18:1, not placement. |
| 1.2 | 2026-10-08 | Verified on device (0.4.9); closed. |

---

Copyright (c) 2026 William Watson. MIT License.
