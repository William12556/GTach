Created: 2026 August 19

# Issue: Device List Screen Lacks Pagination

---

## 1.0 Table of Contents

- [1.0 Table of Contents](<#1.0 table of contents>)
- [2.0 Issue Record](<#2.0 issue record>)
- [Version History](<#version history>)

---

## 2.0 Issue Record

```yaml
issue_info:
  id: "issue-479b2e51"
  title: "Device List screen lacks pagination for more than 3 discovered devices"
  date: "2026-08-19"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-479b2e51"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    The Select Device screen (SetupScreen.DEVICE_LIST) renders all
    discovered Bluetooth devices in a single unbounded curved-list
    column. With more than a small number of devices, the layout
    becomes visually crowded and risks colliding with the Back/Retry
    buttons and the circular safe-area boundary.

affected_scope:
  components:
    - name: "SetupDisplayManager._render_device_list_screen"
      file_path: "src/gtach/display/setup.py"
    - name: "CircularPositioningEngine.calculate_curved_list_layout"
      file_path: "src/gtach/display/setup_components/layout/circular_positioning.py"
    - name: "SetupStateCoordinator"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
    - name: "TouchHandler._handle_setup_touch / _process_touch"
      file_path: "src/gtach/display/touch.py"
  designs:
    - design_ref: "design-a3b4c5d6-component_display_setup_manager"
  version: ""

reproduction:
  prerequisites: "Bluetooth scan discovers more than 3 candidate devices"
  steps:
    - "Enter Setup, start discovery"
    - "Allow discovery to complete with 4 or more devices found"
    - "Observe Select Device screen"
  frequency: "always"
  reproducibility_conditions: "Discovered device count > 3"
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    Exactly 3 slots are always shown, centred vertically on the
    display. The focused device occupies the middle slot; the slots
    above and below show the previous/next device, or an empty
    outlined frame if none exists at that position. Only the middle
    slot is touch-selectable, and it is visually distinguished by an
    accent border and background tint. A vertical swipe moves the
    focus by 1 device. An up/down arrow indicator is shown whenever
    a device exists to scroll to on that side (i.e. whenever the
    focused index is not at that end of the discovered list).
  actual: >
    All discovered devices are rendered in a single column starting
    at y=100 with no upper bound, unpaginated, and every rendered
    device row is independently touch-selectable.
  impact: "Cosmetic/usability only; no functional failure."
  workaround: "None required; low device counts are unaffected."

environment:
  python_version: "3.11"
  os: "Debian GNU/Linux 11 (Bullseye)"
  dependencies:
    - library: "pygame"
      version: "2.6.1"
  domain: "domain_1"

analysis:
  root_cause: >
    _render_device_list_screen and calculate_curved_list_layout were
    designed for a small, fixed device set and never bounded the
    rendered window, nor restricted which rows are selectable.
    SetupStateCoordinator already defines
    scroll_offset/max_scroll/update_scroll_offset(), but no render or
    touch path consumes them.
  technical_notes: >
    TouchHandler explicitly bypasses gesture-handler swipe detection
    in setup mode (_process_touch: "Skip gesture handler in setup
    mode - route directly"), dispatching only tap position to
    SetupDisplayManager.handle_touch_event. Swipe-based focus change
    on DEVICE_LIST requires new drag-distance handling in this path.
  related_issues: []

resolution:
  assigned_to: "Claude Code / Strategic Domain"
  target_date: ""
  approach: "See change-479b2e51"
  change_ref: "change-479b2e51"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Bound rendered list windows by design going forward."
  process_improvements: ""

verification_enhanced:
  verification_steps: []
  verification_results: ""

traceability:
  design_refs:
    - "design-a3b4c5d6-component_display_setup_manager"
  change_refs:
    - "change-479b2e51"
  test_refs: []

notes: >
  Interaction mode confirmed with William: swipe gesture only (no tap
  targets on the arrows). Revised 2026-08-19: only the middle slot is
  selectable, 3 slots are always shown (empty ones as outlined
  frames), the middle slot carries a border + tint indicator, and
  arrow visibility follows whether a device exists on that side
  rather than a fixed device-count threshold. This supersedes the
  original 1-device-shift window model with a focused-index model
  (see change-479b2e51).

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-19"
    author: "Claude"
    changes:
      - "Initial issue creation"
  - version: "1.1"
    date: "2026-08-19"
    author: "Claude"
    changes:
      - "Revised expected behaviour: middle-slot-only selection, always-3-slots with empty-frame placeholders, border+tint selection indicator, device-presence-based arrow visibility"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#1.0 table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial issue creation |
| 1.1 | 2026-08-19 | Revised expected behaviour per additional requirements (middle-only selection, always-3-slots, selection indicator, arrow visibility rule) |

---

Copyright (c) 2026 William Watson. MIT License.
