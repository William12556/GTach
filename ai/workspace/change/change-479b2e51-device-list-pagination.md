Created: 2026 August 19

# Change: Device List Screen Pagination

---

## 1.0 Table of Contents

- [1.0 Table of Contents](<#1.0 table of contents>)
- [2.0 Change Record](<#2.0 change record>)
- [Version History](<#version history>)

---

## 2.0 Change Record

```yaml
change_info:
  id: "change-479b2e51"
  title: "Focused-index Device List: 3 fixed slots, middle-only selection, swipe-only focus shift"
  date: "2026-08-19"
  author: "Claude"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-479b2e51"
    issue_iteration: 1

source:
  type: "human_request"
  reference: "issue-479b2e51"
  description: >
    William requested the Select Device screen show a maximum of 3
    devices at a time, centred on the vertical axis, with up/down
    arrow indicators. Confirmed: swipe-only interaction, 1-device
    shift per swipe. Subsequently added: only the middle (focused)
    slot is touch-selectable and must be visually indicated; exactly
    3 slots are always shown, with empty slots rendered as outlined
    frames when fewer than 3 devices are discovered. Arrow visibility
    follows device presence on that side, not a fixed count
    threshold.

scope:
  summary: >
    Replace the unbounded device column with a fixed 3-slot layout
    driven by a focused-device index. The middle slot always shows
    the focused device (border + background tint, touch-selectable);
    the top and bottom slots show the previous/next device or an
    empty outlined frame. Swipe up/down shifts the focused index by
    1, clamped to the discovered-device range. Up/down arrow glyphs
    indicate availability of a previous/next device respectively.
  affected_components:
    - name: "SetupDisplayManager._render_device_list_screen"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "SetupDisplayManager (new swipe handler method)"
      file_path: "src/gtach/display/setup.py"
      change_type: "add"
    - name: "DeviceSurfaceRenderer (selected-state / empty-frame rendering)"
      file_path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_type: "modify"
    - name: "CircularPositioningEngine (fixed 3-slot positions)"
      file_path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_type: "modify"
    - name: "SetupStateCoordinator (scroll_offset repurposed as focused_index)"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
      change_type: "modify"
    - name: "TouchHandler._process_touch / _handle_setup_touch"
      file_path: "src/gtach/display/touch.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-a3b4c5d6-component_display_setup_manager"
      sections:
        - "DEVICE_LIST screen behaviour"
  out_of_scope:
    - "Tap-target arrows (explicitly rejected — swipe only)"
    - "Multi-device shift per swipe (rejected — 1-device shift confirmed)"
    - "Changes to WELCOME, DISCOVERY, PAIRING, CURRENT_DEVICE screens"
    - "Changes to device discovery/filtering logic"

rational:
  problem_statement: >
    The device list column is unbounded and can overflow the
    circular safe area and collide with the Back/Retry buttons when
    more than a handful of devices are discovered. Additionally,
    every rendered row was independently selectable, which is
    inconsistent with a single-focus swipe interaction.
  proposed_solution: >
    Render exactly 3 fixed vertical slot positions, centred on the
    display. Maintain a single focused_index (0-based, into
    discovered_devices) in SetupStateCoordinator, repurposing the
    existing scroll_offset field. The middle slot renders
    discovered_devices[focused_index] with a border + tint indicator
    and is the only slot registered as a touch region. The top slot
    renders discovered_devices[focused_index - 1] if it exists, else
    an empty outlined frame; the bottom slot mirrors this for
    focused_index + 1. Swipe up decrements focused_index, swipe down
    increments it, both clamped to [0, len(discovered_devices) - 1].
    Up-arrow is drawn when focused_index > 0; down-arrow when
    focused_index < len(discovered_devices) - 1. With 0 devices, the
    existing "No devices found" message is retained and no slots are
    drawn.
  alternatives_considered:
    - option: "Tap-target arrow buttons"
      reason_rejected: "William specified swipe-only interaction."
    - option: "3-item sliding window (all 3 rows selectable, window moves by 1)"
      reason_rejected: "Superseded — William specified only the middle slot is selectable, with fixed 3-slot geometry regardless of device count."
    - option: "Arrow visibility gated on discovered count > 3 (original spec)"
      reason_rejected: "William confirmed arrows should instead reflect whether a device exists on that side, since middle-only selection requires swiping to reach any off-centre device even with as few as 2 total."
  benefits:
    - "Bounded, fixed-geometry layout regardless of discovered device count"
    - "Single unambiguous selection target; no accidental selection of a partially-scrolled row"
    - "Reuses existing scroll_offset state field (repurposed), no new SetupState fields required"
  risks:
    - risk: "Repurposing scroll_offset as focused_index changes its clamp range from [0, max_scroll] to [0, len(devices)-1]; any other reader of scroll_offset/max_scroll must be checked"
      mitigation: "mcp-ripgrep search of scroll_offset/max_scroll usage across src/ before implementation to confirm DEVICE_LIST is the only consumer"
    - risk: "Swipe detection added to setup mode touch path could interfere with existing tap dispatch on DEVICE_LIST (middle-slot selection, Back/Retry buttons)"
      mitigation: "Distinguish swipe from tap by movement distance threshold, consistent with existing non-setup swipe_threshold logic in TouchHandler._handle_short_press, before falling through to tap dispatch"
    - risk: "Empty-frame slots must still respect circular safe-area bounds"
      mitigation: "Reuse the same fixed slot rects for empty frames as for populated devices; validate with validate_all_layout_elements during test"

technical_details:
  current_behavior: >
    _render_device_list_screen calls
    calculate_curved_list_layout(len(discovered_devices), start_y=100)
    and renders every discovered device unconditionally, each with
    its own touch region. SetupStateCoordinator.scroll_offset/
    max_scroll exist but are never read by the render path.
    TouchHandler._process_touch explicitly skips swipe/gesture
    detection in setup mode and forwards only the touch-up (x, y)
    position.
  proposed_behavior: >
    On DEVICE_LIST, 3 fixed slot rects are computed once (top,
    middle, bottom; middle centred at display_center), independent
    of discovered_devices length. Each slot renders either a device
    (via DeviceSurfaceRenderer) or an empty outlined frame. Only the
    middle slot registers a touch region. The middle slot's device
    surface is rendered with an additional border + tint indicating
    it is selectable. TouchHandler detects vertical swipes while in
    setup mode and on DEVICE_LIST specifically, shifting focused_index
    by ±1 (clamped) rather than dispatching a tap.
  implementation_approach: >
    1. SetupStateCoordinator: rename usage of scroll_offset to
       represent focused_index conceptually (field name may be kept
       for minimal diff, or renamed — confirm during T04 authoring);
       on transition to DEVICE_LIST or reset_discovery(), clamp to
       [0, max(0, len(discovered_devices) - 1)].
    2. CircularPositioningEngine: add or reuse a fixed 3-slot
       position calculation (top/middle/bottom y-positions centred on
       display_center), replacing the per-count curved layout call
       for DEVICE_LIST specifically.
    3. DeviceSurfaceRenderer: add a `selected: bool` (or similarly
       named) parameter to the surface-creation call for the middle
       slot, applying a border + background tint; add an
       empty-frame rendering path for slots with no corresponding
       device.
    4. SetupDisplayManager._render_device_list_screen: compute the
       3 slot contents from focused_index, render each (device or
       empty frame), register a touch region for the middle slot
       only, draw up-arrow when focused_index > 0, down-arrow when
       focused_index < len(discovered_devices) - 1.
    5. SetupDisplayManager: add a method (e.g. handle_setup_swipe)
       that shifts focused_index by ±1 via
       state_coordinator.update_scroll_offset and invalidates the
       render cache.
    6. TouchHandler._process_touch: when
       display_manager.is_in_setup_mode() and the current setup
       screen is DEVICE_LIST, measure drag distance before
       dispatching; distances at or above the existing swipe
       threshold call the new SetupDisplayManager swipe handler
       instead of handle_touch_event; distances below the threshold
       fall through to existing tap dispatch unchanged.
  code_changes:
    - component: "SetupDisplayManager"
      file: "src/gtach/display/setup.py"
      change_summary: "Fixed 3-slot render from focused_index, middle-only touch region, add swipe handler"
      functions_affected:
        - "_render_device_list_screen"
      classes_affected:
        - "SetupDisplayManager"
    - component: "DeviceSurfaceRenderer"
      file: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_summary: "Add selected-state border/tint rendering and empty-frame rendering path"
      functions_affected: []
      classes_affected:
        - "DeviceSurfaceRenderer"
    - component: "CircularPositioningEngine"
      file: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_summary: "Add fixed 3-slot centred position calculation for DEVICE_LIST"
      functions_affected: []
      classes_affected:
        - "CircularPositioningEngine"
    - component: "SetupStateCoordinator"
      file: "src/gtach/display/setup_components/state/coordinator.py"
      change_summary: "Repurpose scroll_offset as focused_index; clamp to [0, len(devices)-1] on DEVICE_LIST entry/reset"
      functions_affected:
        - "transition_to_screen"
        - "reset_discovery"
        - "update_scroll_offset"
      classes_affected:
        - "SetupStateCoordinator"
    - component: "TouchHandler"
      file: "src/gtach/display/touch.py"
      change_summary: "Detect swipe distance on DEVICE_LIST before tap dispatch in setup mode"
      functions_affected:
        - "_process_touch"
        - "_handle_setup_touch"
      classes_affected:
        - "TouchHandler"
  data_changes: []
  interface_changes:
    - interface: "SetupDisplayManager (new swipe handler method)"
      change_type: "signature"
      details: "New method added; no existing signatures altered"
      backward_compatible: "yes"
    - interface: "DeviceSurfaceRenderer.create_curved_device_surface (or equivalent)"
      change_type: "signature"
      details: "Additional optional parameter(s) for selected-state indicator and empty-frame mode; exact signature to be finalised at T04 authoring"
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "SetupStateCoordinator"
      impact: "scroll_offset semantics change from window-start to focused-index"
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Manual on-device verification (per project convention: measure
    and verify on gtach.local, not macOS). Existing setup-mode test
    suite regression run.
  test_cases:
    - scenario: "Discovery finds 0 devices"
      expected_result: "\"No devices found\" message; no slots drawn"
    - scenario: "Discovery finds 1 device"
      expected_result: "Middle slot shows the device with border+tint, selectable; top and bottom slots are empty frames; no arrows"
    - scenario: "Discovery finds 2 devices, focused_index=0"
      expected_result: "Middle slot shows device 0, selectable; bottom slot shows device 1; top slot empty frame; down-arrow only"
    - scenario: "Swipe down once from focused_index=0, 2 devices total"
      expected_result: "focused_index=1; middle slot now shows device 1, selectable; top slot shows device 0; no down-arrow, up-arrow shown"
    - scenario: "Discovery finds 5 devices, focused_index=0"
      expected_result: "Middle slot device 0 selectable; top empty frame; bottom slot device 1; down-arrow only"
    - scenario: "Swipe up at focused_index=0"
      expected_result: "No change (clamped at 0)"
    - scenario: "Tap the middle slot"
      expected_result: "Correct focused device selected; pairing proceeds"
    - scenario: "Tap the top or bottom slot"
      expected_result: "No action (not a registered touch region)"
  regression_scope:
    - "tests/ setup-mode display tests, if present"
    - "Back/Retry button touch regions unaffected"
    - "mcp-ripgrep confirmation that DEVICE_LIST is the sole consumer of scroll_offset/max_scroll before repurposing"
  validation_criteria:
    - "All 3 slot positions, populated or empty, remain within circular safe area (validate_all_layout_elements)"
    - "Exactly one touch region exists on DEVICE_LIST when discovered_devices is non-empty; zero when empty"
    - "Arrow glyphs match focused_index position relative to discovered_devices bounds in all tested cases above"

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Author T04 prompt from this change"
      owner: "Claude (Strategic Domain)"
    - step: "Execute via Claude Code"
      owner: "William / Claude Code"
    - step: "On-device verification at gtach.local"
      owner: "William"
  rollback_procedure: "git revert the associated commit(s); no data/schema migration involved."
  deployment_notes: ""

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates:
    - design_ref: "design-a3b4c5d6-component_display_setup_manager"
      sections_updated:
        - "DEVICE_LIST screen behaviour"
      update_date: ""
  related_changes: []
  related_issues:
    - issue_ref: "issue-479b2e51"
      relationship: "resolves"

notes: >
  Revision 2026-08-19: superseded the original 3-item sliding-window
  model with a focused-index model per William's additional
  requirements (middle-only selection, always-3-slots with empty
  frames, border+tint selection indicator, device-presence-based
  arrow visibility).

version_history:
  - version: "1.0"
    date: "2026-08-19"
    author: "Claude"
    changes:
      - "Initial change creation"
  - version: "1.1"
    date: "2026-08-19"
    author: "Claude"
    changes:
      - "Superseded sliding-window model with focused-index model: middle-only selectable slot, always-3-slots with empty-frame placeholders, border+tint selection indicator, device-presence-based arrow visibility"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#1.0 table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial change creation |
| 1.1 | 2026-08-19 | Superseded sliding-window model with focused-index model per additional requirements |

---

Copyright (c) 2026 William Watson. MIT License.
