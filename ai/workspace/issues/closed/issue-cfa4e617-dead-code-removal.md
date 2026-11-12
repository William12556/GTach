# Issue: Unused Code and Configuration Keys

Created: 2026 November 11

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-cfa4e617"
  title: "Code, configuration keys and one data file under src/gtach have no caller or reader"
  date: "2026-11-11"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-cfa4e617"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-71ab3751 finding E01, weakness W1 (report-71ab3751 section 5.0), decisions D2, D3 and D4 of proposal-71ab3751, and two ai/task.md mypy candidates (TouchAction.DRAG, unreachable manual-entry screen)."

affected_scope:
  components:
    - name: "TouchEventCoordinator move, up, gesture and slider paths"
      file_path: "src/gtach/display/input/touch_coordinator.py"
    - name: "TouchEventInterface abstract methods for the removed paths"
      file_path: "src/gtach/display/input/interfaces.py"
    - name: "DisplayConfig gesture_* fields, rpm_warning, rpm_danger"
      file_path: "src/gtach/display/models.py"
    - name: "AppConfig rpm_warning, rpm_danger; CONFIG_KEYS; dead yaml fallback"
      file_path: "src/gtach/utils/config.py"
    - name: "Retired default configuration text"
      file_path: "src/gtach/utils/default-config.txt"
    - name: "SetupStateCoordinator control auto-hide, filter toggle, manual MAC entry"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
    - name: "SetupAction members without a reference"
      file_path: "src/gtach/display/setup_models.py"
    - name: "Unreachable manual-entry branch and renderer; show_all_devices argument"
      file_path: "src/gtach/display/setup.py"
    - name: "Module-level capability helpers without callers"
      file_path: "src/gtach/utils/platform.py"
    - name: "Dirty-region members without callers"
      file_path: "src/gtach/display/performance/monitor.py"
    - name: "Gesture-callback registrations that are never dispatched; DisplayConfig construction sites"
      file_path: "src/gtach/display/manager.py"
    - name: "Dead import fallbacks marked TODO: issue-ac11505d"
      file_path: "src/gtach/display/, src/gtach/utils/, src/gtach/comm/device_store.py"
    - name: "Stale comment citing discover_all_devices"
      file_path: "src/gtach/comm/pairing.py"
  designs: []
  version: "0.4.13"

reproduction:
  prerequisites: "Source at commit 94ce959b or later."
  steps:
    - "Search src/gtach for a reference to each symbol named in test_data."
  frequency: "always"
  reproducibility_conditions: "From source."
  test_data: >
    Searched at 94ce959b. No reference outside the defining file (and
    none inside it other than the definition, or only from other members
    of the same unused group):
    touch_coordinator.py register_slider_region, get_slider_value,
    set_slider_value, _handle_slider_touch_down, _handle_slider_drag,
    _calculate_slider_value, _end_slider_interaction, _recognize_gesture,
    _is_drag_gesture, handle_touch_move, handle_touch_up, handle_gesture
    (manager.py states in a comment that handle_touch_up and
    handle_touch_move are never invoked; handle_touch_move returns
    TouchAction.DRAG, a member that does not exist).
    coordinator.py get_control_alpha, are_controls_visible,
    _update_control_visibility, register_interaction (to be confirmed),
    toggle_device_filter, enter_manual_entry_mode,
    exit_manual_entry_mode, update_manual_mac_input,
    is_valid_mac_address, set_focused_index.
    setup_models.py SetupAction.SAVE, TEST_CONNECTION, CHANGE_DEVICE,
    REMOVE_DEVICE, ADD_DEVICE, REFRESH, MANUAL_ENTRY, CONFIRM,
    EXIT_SETUP, TOGGLE_FILTER, CONNECT_MANUAL.
    setup.py _render_manual_entry_screen and its unreachable branch in
    _render_screen.
    monitor.py add_dirty_region, get_dirty_regions, clear_dirty_regions.
    platform.py PlatformError, run_platform_test, log_platform_info,
    clear_detection_cache, module-level check_gpio_availability.
    models.py eleven gesture_* fields; rpm_warning and rpm_danger are
    written (manager.py DisplayConfig construction, config.py) and read
    by no rendering or logic path.
    utils/default-config.txt is referenced by no source file.
    pairing.py discover_elm327_devices carries a comment citing
    discover_all_devices, which BluetoothPairing does not define.
    Ten files carry 'TODO: issue-ac11505d' fallbacks that assign None
    to a required import (pygame, yaml, SplashConfig, TouchHandler):
    display/manager.py, setup.py, splash.py, typography.py, __init__.py,
    graphics/splash_graphics.py,
    setup_components/rendering/device_surfaces.py, utils/config.py,
    utils/ack_state.py, comm/device_store.py.
  error_output: "None."

behavior:
  expected: "Every definition under src/gtach has a caller or is part of a documented interface."
  actual: "As in test_data."
  impact: "No runtime effect. The unused code enlarges the files later changes must read, and carries one latent AttributeError (TouchAction.DRAG)."
  workaround: "None needed."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Features that were designed or partly built (sliders, gesture dispatch through the coordinator, control auto-hide, manual MAC entry, filter toggle) were superseded and not removed."
  technical_notes: >
    ConfigStore preserves unknown keys on save, so config files that
    still contain rpm_warning, rpm_danger or gesture_* stay valid after
    the keys leave the schema.
    The caller searches above were textual. The change requires each
    candidate to be confirmed again before deletion.
  related_issues:
    - issue_ref: "issue-ac11505d"
      relationship: "related. Origin of the TODO markers and of the two mypy candidates."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-cfa4e617."
  change_ref: "change-cfa4e617"
  resolved_date: "2026-11-11"
  resolved_by: "change-cfa4e617"
  fix_description: "Unused code, the gesture_* configuration fields, utils/default-config.txt and the dead import fallbacks removed; rpm_warning and rpm_danger kept, because ConfigStore.validate() would reject existing files without them (commit f89dc2f6216ff113e7aaf819cb46c21ce873b4ce; report-cfa4e617)."

verification:
  verified_date: "2026-11-12"
  verified_by: "William Watson"
  test_results: "Device session A (test-71ab3751-device-session-a step A1): gauge, touch, palette and setup screens unchanged."
  closure_notes: "Closed with the 71ab3751 series (version 0.5.0). D3 deviation stands: rpm_warning and rpm_danger remain in the configuration schema and are read by no rendering path."

prevention:
  preventive_measures: "Remove superseded code in the change that supersedes it."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE for the list in test_data, textual search.]"
    - "After the change: pytest tests/ passes and mypy src/ reports no issues."
    - "After the change: device session A (proposal-71ab3751 section 7.0) shows gauge, touch and setup behaviour unchanged."
  verification_results: "pytest 589 passed and mypy clean (worker's results). Device session A passed on 2026-11-12."

traceability:
  design_refs: []
  change_refs:
    - "change-cfa4e617"
  test_refs: []

notes: "Audit reference: audit-71ab3751 E01; weakness W1. Run 1 of proposal-71ab3751."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial issue document."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Resolved by change-cfa4e617 (f89dc2f6216ff113e7aaf819cb46c21ce873b4ce); rpm_warning and rpm_danger kept; awaiting device session A."

  - version: "1.2"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Verified on device in session A."

  - version: "1.3"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Closed with the 71ab3751 series; moved to issues/closed/."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial issue document. E01, W1, D2, D3, D4. |
| 1.1 | 2026-11-11 | Resolved by change-cfa4e617 (f89dc2f); rpm_warning and rpm_danger kept; awaiting device session A. |
| 1.2 | 2026-11-12 | Verified on device in session A. |
| 1.3 | 2026-11-12 | Closed with the 71ab3751 series; moved to closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
