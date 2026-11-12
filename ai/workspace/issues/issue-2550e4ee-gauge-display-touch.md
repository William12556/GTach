# Issue: Gauge Display and Touch Defects

Created: 2026 November 11

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-2550e4ee"
  title: "DisplayManager initialisation and setup-mode races; long press decided by duration alone; stale touch start; documentation and efficiency defects in the gauge display"
  date: "2026-11-11"
  reporter: "William Watson"
  status: "verified"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-2550e4ee"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-71ab3751 findings C03, C04, C05, C06, C07, C09, F02 (low), the display-manager part of A09, observations O2 and O5, and the ai/task.md rows 'get_font(18) in _render_disconnected' and 'rpm_bands default None'."

affected_scope:
  components:
    - name: "DisplayManager: _initialize_legacy_components, performance monitor set-up, display loop, handle_touch_event, exit_setup_mode, _toggle_palette, _gauge_max_rpm, _link_lost call sites, _render_disconnected, _on_clear_settings"
      file_path: "src/gtach/display/manager.py"
    - name: "TouchHandler._process_touch"
      file_path: "src/gtach/display/touch.py"
    - name: "DisplayConfig.rpm_bands"
      file_path: "src/gtach/display/models.py"
    - name: "SplashScreen text-fit checks"
      file_path: "src/gtach/display/splash.py"
    - name: "test_callback_may_register_regions"
      file_path: "tests/test_callbacks_outside_locks.py"
  designs:
    - "design-b8c9d0e1-component_display_manager"
  version: "0.4.13"

reproduction:
  prerequisites: "Pi with the touch display, or tests with stubs."
  steps:
    - "C06: on the gauge, swipe slowly (longer than touch_long_press)."
    - "C06: hold a button on the OPTIONS screen for longer than touch_long_press."
    - "C04: make create_touch_interface raise RuntimeError (stub) and start the display."
  frequency: "C06 always; C05 and C07 timing-dependent; C04 on a touch-interface fault"
  reproducibility_conditions: "From source."
  test_data: >
    C03: _toggle_palette's docstring states that a failed save leaves
    the palette unchanged; the palette is switched first and not
    reverted, and _save_config swallows the failure.
    C04: _setup_manager, _in_setup_mode, _setup_entry_callback and
    _splash_screen are first assigned after the touch initialisation
    inside one try block whose inner handler catches only ImportError;
    a RuntimeError from create_touch_interface() leaves them and
    touch_handler undefined. performance_monitor has the same pattern.
    C05: exit_setup_mode (setup thread) clears _setup_manager while the
    display thread and the touch thread test and then use it without a
    local copy.
    C06: a long press is decided by duration alone.
    C07 (suspected): _touch_start is recorded only when None and never
    expires; a lost touch-up makes the next gesture start from the
    stale time and position.
    C09: _gauge_max_rpm caps full scale at 9000 while its docstring
    states the configured redline is always on the dial; RPMBands
    accepts a redline up to 15000.
    A09: _on_clear_settings ignores remove_device()'s result and
    removes only the primary device.
    O2: _link_lost() is evaluated three times per frame, each taking
    the transport lock through the callback.
    O5: the splash calls validate_text_fits_circular_display on every
    frame, for a log-only result, with sizes that differ from the
    sizes drawn.
    get_font(18): the disconnection-cause line uses a literal 18 px
    font instead of FONT_SMALL_TEXT (20 px).
    rpm_bands: declared RPMBands with default None under a
    type: ignore and filled in __post_init__.
    F02: the callback in test_callback_may_register_regions re-enters
    the coordinator on the dispatching thread; the lock is an RLock, so
    the test passes whether or not callbacks run under the lock.
  error_output: "C04, C05: AttributeError on the display or touch thread."

behavior:
  expected: "The display starts and keeps running after a touch-interface fault; a slow swipe navigates; a held button presses; documentation matches behaviour."
  actual: "As in test_data."
  impact: "Low. C06 is the operator-visible item; C04 turns a touch fault into a per-frame error."
  workaround: "Swipe faster."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Individual omissions; no common cause."
  technical_notes: >
    C07 is suspected and cannot be provoked on demand; the proposed
    bound is harmless if touch-up events are never lost.
    Decision D6 (proposal-71ab3751): a long press requires movement
    below the swipe threshold; otherwise the gesture is a swipe.
    Decision D8: display/manager.py is not split.
  related_issues:
    - issue_ref: "issue-b4f9607a"
      relationship: "related. Provides remove_device's result."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-2550e4ee."
  change_ref: "change-2550e4ee"
  resolved_date: "2026-11-12"
  resolved_by: "change-2550e4ee"
  fix_description: "Display attributes get inactive defaults before fallible initialisation and touch initialisation catches any exception; _setup_manager is read once by each reader; a release with movement at or above the swipe threshold is a swipe, a hold at rest on a button presses it, a long press needs rest; a touch start older than 10 s is stale; _link_lost evaluated once per frame; cause line uses FONT_SMALL_TEXT; redline above full scale warned at load and documented; failed palette save warned and documented; Clear settings removes every stored device and checks the results; rpm_bands uses default_factory; splash fit checks once with the drawn size; the lock test detects a callback under the lock (commit afe74234f1207b8c931b4d21048b492651713af0; report-2550e4ee)."

verification:
  verified_date: "2026-11-12"
  verified_by: "William Watson"
  test_results: "Device session B (test-71ab3751-device-session-b steps B6 and B7): all checks passed. In-car test deferred."
  closure_notes: ""

prevention:
  preventive_measures: "Attributes read by other threads are assigned before any step that can fail; shared references are copied to a local before test-and-use."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE, audit-71ab3751.]"
    - "After the fix: unit tests per change-2550e4ee."
    - "After the fix: device session B — slow swipe, held button, long press at rest, palette toggle, DISCONNECTED cause line, Clear settings; then the in-car test."
  verification_results: "pytest 721 passed and mypy clean (worker's results). Device session B passed on 2026-11-12; in-car test deferred."

traceability:
  design_refs:
    - "design-b8c9d0e1-component_display_manager"
  change_refs:
    - "change-2550e4ee"
  test_refs: []

notes: "Audit reference: audit-71ab3751 C03-C07, C09, F02, A09 (display-manager part), O2, O5. Run 5 of proposal-71ab3751."

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
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Resolved by change-2550e4ee (afe74234f1207b8c931b4d21048b492651713af0); awaiting device session B."

  - version: "1.2"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Verified on device in session B; in-car test deferred."

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
| 1.0 | 2026-11-11 | Initial issue document. C03-C07, C09, F02, A09, O2, O5 and two task rows. |
| 1.1 | 2026-11-12 | Resolved by change-2550e4ee (afe7423); awaiting device session B. |
| 1.2 | 2026-11-12 | Verified on device in session B; in-car test deferred. |

---

Copyright (c) 2026 William Watson. MIT License.
