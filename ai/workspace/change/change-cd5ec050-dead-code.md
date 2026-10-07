Created: 2026 October 07

# Change: Remove Dead Code and the Backup Modules

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-cd5ec050"
  title: "Delete the backup modules and unreachable code listed in the audit, the in-process restart remnants, and unused imports and variables; adjust tests and CLAUDE.md"
  date: "2026-10-07"
  author: "William Watson"
  status: "implemented"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-cd5ec050"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-cd5ec050"
  description: "Resolves issue-cd5ec050."

scope:
  summary: "Deletion only, plus the minimal edits needed for remaining code and tests to stay correct."
  affected_components:
    - name: "src/gtach"
      file_path: "src/gtach/"
      change_type: "delete"
    - name: "tests"
      file_path: "tests/"
      change_type: "modify"
    - name: "CLAUDE.md §2"
      file_path: "CLAUDE.md"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any behaviour change of reachable code."
    - "Formatting (change-e4ee50fd) and typing (later phase)."
    - "ThreadManager.worker_pool (used by the update check)."
    - "rpm_warning/rpm_danger configuration keys (kept for compatibility)."

rational:
  problem_statement: "See issue-cd5ec050."
  proposed_solution: >
    Removal list. For every item, first confirm with grep over src/,
    tests/ and bin/ that nothing reachable references it; if something
    does, keep the item and record it in the report.

    R1 (G06) git rm src/gtach/display/manager_backup.py and
    src/gtach/display/setup_original_backup.py. Remove backup references
    from tests (tests/test_pi_reset.py allow-list, tests/test_logging_policy.py
    exclusions) and CLAUDE.md §2 ('Backup files … are excluded from all
    changes and audits').
    R2 (A15) git rm src/gtach/comm/bluetooth.py (empty); pairing.py:
    unused `signal` import and _is_elm327_device, get_device_info,
    test_obd_connection, discover_all_devices; system_bluetooth.py:
    SystemBluetoothManager.pair_device, connect_device,
    disconnect_device, is_device_connected.
    R3 (C11) git rm src/gtach/display/navigation_gestures.py; remove the
    gesture-handler initialisation in DisplayManager and the
    cancel_gesture call in touch.py.
    R4 (C12) DisplayManager: RPM sliders and save button, change_mode
    (if only dead callers), run_main_thread_loop, _process_settings_touch,
    _provide_touch_feedback; correct the stale comment near
    _get_band_colour. touch.py simulation helpers; touch_interface.py
    MockTouchInterface simulation API, get_available_interfaces,
    create_specific_interface, MockGPIO object; typography.py
    ButtonRenderer, get_button_renderer, render_standard_button and the
    validate_* helpers (and setup.py's import of them).
    R5 (C17) the getattr gesture defaults in DisplayManager that
    duplicate DisplayConfig fields (manager.py near the former gesture
    initialisation), if not already removed by R3.
    R6 (D07) SetupStateCoordinator.create_manual_device and
    get_setup_progress.
    R7 (D08) device_surfaces.render_compact_device_item, get_cache_stats,
    optimize_cache; unused CircularPositioningEngine methods
    (position_in_circle, validate_*, curved-list and statistics
    helpers); splash_graphics draw_obdii_connector, draw_progress_bar,
    draw_animated_dots, create_gradient_surface.
    R8 (D09) display/performance get_performance_manager and its export;
    setup.py's unused import of it.
    R9 (E03) terminal.py backup_framebuffer_settings and the framebuffer
    restore block in restore_terminal with the related attributes.
    R10 (E07) platform.py MockRegistry, the GPIO/hyperpixel/pygame mocks,
    import_module_with_mock, the duplicate `import sys`; ack_state.py
    forward reference to RPMBands via a TYPE_CHECKING import.
    R11 (B06, B08, restart remnants) ThreadStatus.RESTARTING and its
    transitions; ThreadInfo target_func/target_args/target_kwargs,
    __post_init__ and restart_future (and restart_count if unused);
    ThreadManager._active_futures and its uses; RecoveryLevel.HARD_RECOVERY;
    RecoveryStats hard_recovery_attempts/successes and their log and
    copy sites. tests/test_watchdog_process_termination.py: delete the
    `hard_recovery_attempts == 0` assertion only.
    R12 (B07) unused `signal` imports in watchdog.py and app.py.
    R13 flake8 F401, F841, F811, F402, F541 in src/gtach: remove unused
    imports and variables, duplicate imports, shadowing loop variable,
    placeholder-less f-strings (convert to plain strings).
    R14 (F03, F06) tests: adjust tests/test_touch_dispatch.py source
    assertions that pin removed code; extend tests/test_pi_reset.py scans
    to os.system and os.popen; delete tests whose only subject was
    removed code and list them in the report.
  alternatives_considered:
    - option: "Keep the backup modules out of the wheel only."
      reason_rejected: "Decided against on 2026-10-07; git history keeps them."
  benefits:
    - "Smaller wheel and codebase; fewer misleading paths; no latent defects in unreachable code."
  risks:
    - risk: "Something reachable is removed."
      mitigation: "grep confirmation per item; full test suite; `python -c 'import gtach.app, gtach.main'`; a simulation start smoke test with SDL_VIDEODRIVER=dummy for 5 s."

technical_details:
  current_behavior: "Dead code present."
  proposed_behavior: "Dead code removed."
  implementation_approach: "Deletion in the order R1 to R14, running pytest after each group."
  code_changes:
    - component: "gtach"
      file: "src/gtach/"
      change_summary: "R1 to R13"
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "Removed private and unused public APIs"
      change_type: "signature"
      details: "Only APIs with no reachable caller."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-4005360c"
      relationship: "blocked_by. Corrections applied before removal."

testing_requirements:
  test_approach: "Existing suite plus smoke checks."
  test_cases:
    - scenario: "pytest tests/."
      expected_result: "Passes."
    - scenario: "python -c 'import gtach.app, gtach.main'."
      expected_result: "Succeeds."
    - scenario: "SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 gtach --transport simtcp; then check exit and logs."
      expected_result: "Starts and runs without import or attribute errors until the timeout."
    - scenario: "flake8 --select F401,F841,F811,F402,F541 src/gtach."
      expected_result: "No findings."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "R1 to R14."
      owner: "tactical"
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
    - change_ref: "change-4005360c"
      relationship: "blocked_by"
    - change_ref: "change-52653cd6"
      relationship: "related. G06 version source."
  related_issues:
    - issue_ref: "issue-cd5ec050"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-cd5ec050 iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in f7899669ddad21b97dc81429595233e1d23d75b0."

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
| 1.0 | 2026-10-07 | Initial change document. Dead code and backup modules removed. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in f7899669ddad21b97dc81429595233e1d23d75b0. |

---

Copyright (c) 2026 William Watson. MIT License.
