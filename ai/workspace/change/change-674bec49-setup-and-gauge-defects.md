Created: 2026 October 07

# Change: Setup Lifecycle, Gauge Range, Cached Device Presence, Persistent Errors

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-674bec49"
  title: "Stop the setup manager on completion, cancel and re-entry without self-join; derive the gauge range from the redline; cache device presence; keep setup errors until the next tap and show their text"
  date: "2026-10-07"
  author: "William Watson"
  status: "implemented"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-674bec49"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-674bec49"
  description: "Resolves issue-674bec49 (audit-36b6ea95 C01, C05, C06, C08)."

scope:
  summary: "Four groups of edits in setup.py, app.py and manager.py, with tests."
  affected_components:
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "GTachApplication._on_setup_complete, _start_setup_mode"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_setup_and_gauge.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Configuration unification (audit E01, Phase 3)."
    - "SetupStateCoordinator.get_state returning live state (D04) and direct state mutation in interface.py."
    - "Other DeviceStore() constructions not on a per-frame path."
    - "Gauge visual design (arc geometry, palette, tick style)."
    - "The repeated-discovery behaviour when discovery finds nothing."

rational:
  problem_statement: "See issue-674bec49."
  proposed_solution: >
    EDIT A (C01) — setup lifecycle.
    (1) SetupDisplayManager.stop_setup joins the setup thread only if it
    is not threading.current_thread(); it remains idempotent.
    (2) GTachApplication._on_setup_complete, after the duplicate guard
    and before exit_setup_mode, calls self._setup_manager.stop_setup()
    if a setup manager exists (wrapped in try/except with
    logger.error(..., exc_info=True)). This covers completion (setup
    thread) and cancel (touch thread).
    (3) GTachApplication._start_setup_mode, before constructing a new
    SetupDisplayManager, calls stop_setup() on any existing one (same
    guard).

    EDIT B (C05) — gauge range. Add
    DisplayManager._gauge_max_rpm(self) -> int returning
    min(9000, max(7000, ceil((redline + 500) / 1000) * 1000)) where
    redline = self.config.rpm_bands.redline_rpm (falling back to 6000 if
    unavailable). In _draw_radial_mode compute it once per frame; clamp
    rpm to [0, max_rpm]; use it for max_rpm; ticks iterate
    range(1000, max_rpm + 1, 1000). Update the readout comment (clamped
    to at most 9000, so three glyphs).

    EDIT C (C06) — cached device presence. Add self._has_device:
    bool = False and _refresh_has_device() which reads
    DeviceStore().get_primary_device() is not None. Call it in
    start_setup (replacing the local DeviceStore use there) and in
    _on_screen_transition when new_screen is WELCOME, before the cache
    is invalidated. _render_welcome_screen and
    _update_cached_screen_touch_regions use self._has_device and no
    longer construct DeviceStore.

    EDIT D (C08) — persistent errors.
    (1) Remove the update_state(error_message=None) call from
    _render_device_list_screen.
    (2) In handle_touch_event, after the hit is found and before
    dispatch, clear a set error_message via
    state_coordinator.update_state(error_message=None).
    (3) _render_welcome_screen renders state.error_message instead of
    the fixed text. If the rendered width exceeds 400 px, render the
    text up to the first '. ' (keeping the full stop); if still wider,
    truncate characters and append '…' until it fits.
  alternatives_considered:
    - option: "Clear errors after a timeout."
      reason_rejected: "Needs a timer; the next tap is a clear and simple trigger."
    - option: "Scale the gauge to any redline."
      reason_rejected: "Above 9000 the readout and tick numerals no longer fit the current layout."
  benefits:
    - "No leaked setup threads."
    - "Gauge covers the redline for profiles up to 8500 RPM; current profile unchanged."
    - "No YAML parsing per frame."
    - "Operators see why a setup step failed."
  risks:
    - risk: "stop_setup from the setup thread no longer joins."
      mitigation: "The loop exits at its next check (≤ 0.05 s) because the event is set and it breaks on COMPLETE."
    - risk: "_has_device stale after the store changes outside setup."
      mitigation: "Refreshed on every entry to WELCOME, which is the only screen that uses it."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits."
  code_changes:
    - component: "SetupDisplayManager"
      file: "src/gtach/display/setup.py"
      change_summary: "EDITS A(1), C, D"
      functions_affected:
        - "stop_setup"
        - "start_setup"
        - "_on_screen_transition"
        - "_render_welcome_screen"
        - "_update_cached_screen_touch_regions"
        - "_render_device_list_screen"
        - "handle_touch_event"
        - "_refresh_has_device (new)"
      classes_affected:
        - "SetupDisplayManager"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: "EDIT A(2), A(3)"
      functions_affected:
        - "_on_setup_complete"
        - "_start_setup_mode"
      classes_affected:
        - "GTachApplication"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "EDIT B"
      functions_affected:
        - "_draw_radial_mode"
        - "_gauge_max_rpm (new)"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "change-e9216e17 lock rules"
      impact: "handle_touch_event clears the error after releasing _touch_regions_lock; update_state notifies after releasing _state_lock."
  external: []
  required_changes:
    - change_ref: "change-860fd5f7"
      relationship: "blocked_by (implemented)."

testing_requirements:
  test_approach: "Unit tests with stubs; pygame surfaces off-screen."
  test_cases:
    - scenario: "stop_setup called from the setup thread itself."
      expected_result: "No RuntimeError; returns; the thread exits."
    - scenario: "stop_setup called twice from another thread."
      expected_result: "Both return; no exception."
    - scenario: "_on_setup_complete with a stub setup manager."
      expected_result: "stop_setup called once before exit_setup_mode; a second call is ignored by the duplicate guard."
    - scenario: "_start_setup_mode with an existing stub setup manager."
      expected_result: "stop_setup called on the old manager before the new one is created."
    - scenario: "_gauge_max_rpm for redlines 6000, 7000, 7500, 8500, 9000, 12000."
      expected_result: "7000, 8000, 8000, 9000, 9000, 9000."
    - scenario: "_update_cached_screen_touch_regions on WELCOME with DeviceStore patched to raise if constructed."
      expected_result: "No construction; regions follow _has_device."
    - scenario: "Transition to WELCOME."
      expected_result: "_refresh_has_device called once."
    - scenario: "_render_device_list_screen with error_message set."
      expected_result: "error_message still set after rendering."
    - scenario: "handle_touch_event on a region with error_message set."
      expected_result: "error_message None before the action runs."
    - scenario: "_render_welcome_screen with error_message 'Device not available' and with the long discovery sentence."
      expected_result: "Text drawn; rendered width ≤ 400 px in both cases."
  regression_scope:
    - "tests/test_setup_lock_order.py, tests/test_device_list_focus.py, tests/test_callbacks_outside_locks.py."
    - "Full tests/ suite."
  validation_criteria:
    - "No DeviceStore() construction in _update_cached_screen_touch_regions or _render_welcome_screen."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to D and tests."
      owner: "tactical"
    - step: "On the Pi: gauge unchanged with the current profile; Cancel and re-entry leave one setup thread at most."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-860fd5f7"
      relationship: "blocked_by"
    - change_ref: "change-e9216e17"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-674bec49"
      relationship: "resolves"

notes: "The gauge rule keeps the device's current profile (redline 6000) at exactly 7000 RPM."

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-674bec49 iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in 5ea2cfd77665ae7fec7e7749f2d6e499136fee7a."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial change document. C01, C05, C06, C08. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in 5ea2cfd77665ae7fec7e7749f2d6e499136fee7a. |

---

Copyright (c) 2026 William Watson. MIT License.
