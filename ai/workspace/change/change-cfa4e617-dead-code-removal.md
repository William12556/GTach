# Change: Remove Unused Code and Configuration Keys

Created: 2026 November 11

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-cfa4e617"
  title: "Delete code, configuration keys and one data file that have no caller or reader; no behaviour change"
  date: "2026-11-11"
  author: "William Watson"
  status: "verified"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-cfa4e617"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-cfa4e617"
  description: "Resolves issue-cfa4e617 (audit-71ab3751 E01, W1; decisions D2, D3, D4). Run 1 of proposal-71ab3751."

scope:
  summary: "Subtractive edits across display/, utils/ and two comm files; tests that exist only for deleted code are deleted."
  affected_components:
    - name: "TouchEventCoordinator, TouchEventInterface"
      file_path: "src/gtach/display/input/touch_coordinator.py, src/gtach/display/input/interfaces.py"
      change_type: "delete"
    - name: "DisplayConfig"
      file_path: "src/gtach/display/models.py"
      change_type: "delete"
    - name: "AppConfig, CONFIG_KEYS"
      file_path: "src/gtach/utils/config.py"
      change_type: "delete"
    - name: "default-config.txt"
      file_path: "src/gtach/utils/default-config.txt"
      change_type: "delete"
    - name: "SetupStateCoordinator"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
      change_type: "delete"
    - name: "SetupAction"
      file_path: "src/gtach/display/setup_models.py"
      change_type: "delete"
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
      change_type: "delete"
    - name: "Platform helpers"
      file_path: "src/gtach/utils/platform.py"
      change_type: "delete"
    - name: "PerformanceMonitor"
      file_path: "src/gtach/display/performance/monitor.py, src/gtach/display/performance/interfaces.py"
      change_type: "delete"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "delete"
    - name: "Dead import fallbacks"
      file_path: "the ten files listed in issue-cfa4e617 test_data"
      change_type: "delete"
    - name: "Stale comment"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "Comment rule"
      file_path: "CLAUDE.md"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any change of behaviour, including fixes for audit findings in the same files (runs 2 to 5)."
    - "Detection logic in utils/platform.py (decision D4: keep detection)."
    - "rpm_bands default (run 5), main_surface Optional (run 4), get_state_info, last_connected and the remaining TODO: issue-ac11505d markers that are not dead import fallbacks."
    - "Renaming, reformatting or comment rewriting outside lines that are deleted."

rational:
  problem_statement: "See issue-cfa4e617."
  proposed_solution: >
    RULE — A symbol is deleted only after a search of src/ and tests/
    confirms that it has no caller, no reader, no subclass override that
    is called, and no lookup by string (getattr, dictionary of names,
    configuration key, argparse). A candidate that fails this check is
    left in place and listed in the report with the reference found.
    A test that exists only for deleted code is deleted; a test that
    also covers kept behaviour is reduced.
    Write-only state counts as unused: a member whose only callers
    maintain state that nothing reads is deleted together with those
    call sites, after the same search confirms that nothing reads the
    state.

    EDIT A (touch coordinator) — In TouchEventCoordinator delete
    handle_touch_move, handle_touch_up, handle_gesture,
    register_gesture_callback, register_slider_region,
    _handle_slider_touch_down, _handle_slider_drag,
    _calculate_slider_value, _end_slider_interaction,
    _recognize_gesture, _is_drag_gesture, get_slider_value,
    set_slider_value and the state they alone use. Delete the matching
    abstract methods in TouchEventInterface. In DisplayManager delete
    the two register_gesture_callback calls and the comment that
    explains why they never fire; keep _handle_swipe_down and
    _handle_swipe_up if display/touch.py calls them. Delete GestureType
    and its exports only if no reference remains.

    EDIT B (configuration, decision D3) — Delete the eleven gesture_*
    fields of DisplayConfig. Delete rpm_warning and rpm_danger from
    AppConfig, CONFIG_KEYS and any range table in utils/config.py, from
    DisplayConfig, and from the DisplayConfig construction sites in
    DisplayManager. Delete utils/default-config.txt and any packaging
    reference to it in pyproject.toml.

    EDIT C (setup coordinator, decision D2) — In SetupStateCoordinator
    delete the control auto-hide group (register_interaction,
    _update_control_visibility, get_control_alpha, are_controls_visible
    and their attributes). register_interaction is called from
    SetupDisplayManager.handle_touch_event and update_animation from
    _setup_loop, but they only maintain visibility state that nothing
    reads; delete register_interaction with its call site, and
    update_animation with its call site only if it then does nothing.
    Delete the filter toggle
    (toggle_device_filter, show_all_devices attribute), the manual
    entry group (enter_manual_entry_mode, exit_manual_entry_mode,
    update_manual_mac_input, is_valid_mac_address, manual_entry_mode,
    manual_mac_input) and set_focused_index; remove the removed
    attributes from get_focus_info. In SetupDisplayManager delete
    _render_manual_entry_screen and its branch in _render_screen, and
    drop the show_all_devices argument from the start_discovery call in
    _setup_loop (the parameter keeps its default False). Delete the
    SetupAction members that have no reference.
    BluetoothSetupInterface.start_discovery and
    BluetoothPairing.discover_elm327_devices keep their
    show_all_devices parameter (used by run 2 and run 4).

    EDIT D (platform, decision D4) — In utils/platform.py delete only
    members without a caller in src/: PlatformError, run_platform_test,
    log_platform_info, clear_detection_cache and the module-level
    check_gpio_availability, plus private helpers that become
    unreferenced as a result. get_platform_type, get_platform_info,
    is_raspberry_pi, PlatformType and the detection methods stay.

    EDIT E (performance monitor) — Delete add_dirty_region,
    get_dirty_regions, clear_dirty_regions, their state, and any other
    member of PerformanceMonitor without a caller. Members used by
    DisplayManager stay: start_monitoring, stop_monitoring,
    record_frame_start, record_frame_end, should_log_periodic,
    get_current_metrics, get_performance_summary, _monitoring. Reduce
    PerformanceMonitorInterface to match.

    EDIT F (dead import fallbacks) — Where a try/except ImportError
    around a required dependency (pygame, PyYAML) or around a
    package-internal import (SplashConfig, TouchHandler) assigns None
    and carries 'TODO: issue-ac11505d', replace it with the plain
    import. Remove an availability flag (for example YAML_AVAILABLE)
    and the branches that test it only if the flag is then constant;
    the branch for the available case stays. Optional dependencies
    (hyperpixel2r, RPi.GPIO, PyBluez, pyserial) are not touched.

    EDIT G (comment) — In BluetoothPairing.discover_elm327_devices
    replace the comment that cites discover_all_devices with one line
    stating that the timeout is coerced to int.

    EDIT H (comment rule) — Add one rule to CLAUDE.md section 4:
    'A comment states the current behaviour and at most one issue
    reference; history belongs in the change documents.' Add the
    matching row to the CLAUDE.md version history.
  alternatives_considered:
    - option: "Delete during the later runs, file by file."
      reason_rejected: "Later runs would read and partly repair code that is then deleted."
  benefits:
    - "Smaller files for runs 2 to 5."
    - "Removes the TouchAction.DRAG and unreachable manual-entry candidates."
  risks:
    - risk: "A deleted symbol is used through a path a textual search misses."
      mitigation: "The RULE; independent adversarial check per candidate; pytest and mypy as the gate; removed symbols listed in the report."
    - risk: "Removing an import fallback changes behaviour on a host without the package."
      mitigation: "Only required dependencies declared in pyproject.toml; the application cannot start without them today."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "Identical runtime behaviour with the unused definitions absent."
  implementation_approach: "Deletion only. No new code except the plain imports of EDIT F."
  code_changes:
    - component: "display"
      file: "input/touch_coordinator.py, input/interfaces.py, manager.py, models.py, setup.py, setup_models.py, setup_components/state/coordinator.py, performance/monitor.py, performance/interfaces.py and the fallback files"
      change_summary: "EDITS A, B, C, E, F"
      functions_affected: []
      classes_affected:
        - "TouchEventCoordinator"
        - "DisplayConfig"
        - "SetupStateCoordinator"
        - "SetupAction"
        - "PerformanceMonitor"
    - component: "utils"
      file: "config.py, platform.py, ack_state.py, default-config.txt"
      change_summary: "EDITS B, D, F"
      functions_affected: []
      classes_affected:
        - "AppConfig"
    - component: "comm"
      file: "pairing.py, device_store.py"
      change_summary: "EDITS F, G"
      functions_affected: []
      classes_affected: []
  data_changes:
    - entity: "config.yaml schema"
      change_type: "schema"
      details: "rpm_warning and rpm_danger leave the schema. Existing files stay valid: ConfigStore keeps unknown keys."
  interface_changes:
    - interface: "TouchEventInterface"
      change_type: "signature"
      details: "Abstract methods for move, up and gesture handling removed."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Existing suite; no new behaviour to test."
  test_cases:
    - scenario: "pytest tests/ after the deletions."
      expected_result: "Passes. Deleted tests are listed in the report with the symbol they covered."
    - scenario: "mypy src/ with the project configuration."
      expected_result: "No issues; no new type: ignore."
    - scenario: "ConfigStore.load on a file that still contains rpm_warning, rpm_danger and a gesture_* key, then save."
      expected_result: "Loads without warning for those keys; save keeps them as unknown keys. Add this one test."
    - scenario: "Search src/ for each removed name."
      expected_result: "No match."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes; mypy clean."
    - "Line count of src/gtach before and after reported."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Confirm each candidate against the RULE; EDITS A to H."
      owner: "tactical"
    - step: "Planner review of the removed-symbol list."
      owner: "strategic"
    - step: "Device session A after runs 1 to 3."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-11-11"
  implemented_by: "Claude Code"
  verification_date: "2026-11-12"
  verified_by: "William Watson"
  test_results: "Commit f89dc2f6216ff113e7aaf819cb46c21ce873b4ce (merged to main): pytest 589 passed; mypy src/ no issues (worker's results, report-cfa4e617 section 6). Device session A (2026-11-12, test-71ab3751-device-session-a step A1): display, touch and palette unchanged; pass."
  issues_found:
    - "EDIT B partly not applied: rpm_warning and rpm_danger kept. ConfigStore.validate() reports keys outside CONFIG_KEYS as unknown, so removing them would make --validate-config fail on existing config files. Decision D3 rested on a premise that holds for load and save only. Accepted deviation; see report-cfa4e617 sections 4 and 9."
    - "Pre-existing flaky test tests/test_pi_reset.py::TestDispatchIsOffThread::test_second_press_while_in_flight_is_ignored (fails about 1 in 8 full-suite runs on the unchanged tree). Not caused by this change."

traceability:
  design_updates:
    - "design-b4c5d6e7 (config): none required; rpm_warning and rpm_danger stay in the schema (issues_found)."
  related_changes:
    - change_ref: "change-b4f9607a"
      relationship: "follows"
    - change_ref: "change-34781bfe"
      relationship: "follows; relies on the show_all_devices parameter being kept"
  related_issues:
    - issue_ref: "issue-cfa4e617"
      relationship: "resolves"

notes: "This run edits files that runs 2, 4 and 5 own. It runs first and alone. The data_changes entry for rpm_warning and rpm_danger was not applied (issues_found)."

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-cfa4e617 iteration 1."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Implemented in f89dc2f6216ff113e7aaf819cb46c21ce873b4ce; EDIT B partly not applied (rpm_warning, rpm_danger kept); awaiting device session A."

  - version: "1.3"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Verified on device in session A (test-71ab3751-device-session-a)."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial change document. E01, W1, D2, D3, D4. |
| 1.1 | 2026-11-11 | Approved for implementation. |
| 1.2 | 2026-11-11 | Implemented in f89dc2f; rpm_warning and rpm_danger kept (D3 deviation); awaiting device session A. |
| 1.3 | 2026-11-12 | Verified on device in session A. |

---

Copyright (c) 2026 William Watson. MIT License.
