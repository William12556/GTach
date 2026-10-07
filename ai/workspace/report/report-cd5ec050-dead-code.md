Created: 2026 October 07

# Report: Dead Code and Backup Modules Removed

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests Added and Result](<#3. tests added and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [On-Device Verification Outstanding](<#6. on-device verification outstanding>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-cd5ec050 (change-cd5ec050, issue-cd5ec050; audit-36b6ea95 A15, B06, B08, C11, C12, C17, D07, D09, E03, E07, F03, F06, G06) was implemented in commit `f7899669ddad21b97dc81429595233e1d23d75b0`. The groups ran in the prescribed order, with pytest after each group. All runs passed except R4's first run, where one source-pinning test failed (`TestDisplayModeImportRetained`); it was handled as R14 prescribes.

- **R1:** the two backup modules were removed with `git rm`, along with the backup entries in `test_pi_reset.py`, `test_logging_policy.py` and CLAUDE.md §2.
- **R11:**
  - `ThreadStatus.RESTARTING` and its transitions;
  - `ThreadInfo` `restart_count`, `target_func/args/kwargs`, `__post_init__` and `restart_future`;
  - `ThreadManager._active_futures`;
  - `RecoveryLevel.HARD_RECOVERY`;
  - the `RecoveryStats` hard-recovery fields and their log and copy sites;
  - the one `hard_recovery_attempts` assertion.
- **R12:** the `signal` import in watchdog.py. app.py's is kept, because it installs the SIGINT and SIGTERM handlers.
- **R2:**
  - `comm/bluetooth.py` removed;
  - in pairing.py: the `signal` import, `_is_elm327_device`, `get_device_info`, `test_obd_connection` and `discover_all_devices`;
  - `SystemBluetoothManager.pair_device`, `connect_device`, `disconnect_device` and `is_device_connected`.
- **R3/R5:** `navigation_gestures.py` removed with `git rm`, together with the gesture-handler initialisation (including the duplicate `getattr` defaults, R5) and the `cancel_gesture` call.
- **R4:**
  - DisplayManager: the RPM sliders, slider visuals, the save button, `_update_config_from_sliders` (and its call), `change_mode` and `run_main_thread_loop`; the `_get_band_colour` comment corrected;
  - touch.py: `_process_settings_touch`, `_provide_touch_feedback`, `test_touch_simulation` and `simulate_settings_button_press`;
  - touch_interface.py: MockTouchInterface's simulation API, `get_available_interfaces`, `create_specific_interface` and the MockGPIO object;
  - typography.py: ButtonRenderer, `get_button_renderer`, `render_standard_button`, `get_button_size_info` and the `validate_*` helpers.
- **R6:** `create_manual_device` and `get_setup_progress`.
- **R7:**
  - `render_compact_device_item`, `get_cache_stats` and `optimize_cache`;
  - `position_in_circle`, `calculate_curved_list_layout` and the four statistics helpers;
  - the four splash_graphics functions;
  - `SplashScreen._draw_obdii_icon`, whose only call was commented out.
- **R8:** `get_performance_manager`, its export and setup.py's import.
- **R9:** `backup_framebuffer_settings` and the framebuffer restore block.
- **R10:**
  - in platform.py: MockRegistry, the default mocks, both `import_module_with_mock` and the duplicate `import sys`;
  - in ack_state.py: a `TYPE_CHECKING` import of RPMBands.
- **R13:** every F401, F841, F811, F402 and F541 finding in src/gtach. Unused imports and variables were removed with autoflake (installed in a scratch venv only, not added to the project) and reviewed. A side-effecting call (`self._splash_screen.render(...)`) was kept without its assignment. Placeholder-less f-strings became plain strings.
- **R14:**
  - `test_pi_reset.py` gains `os.system` and `os.popen` scans;
  - `test_touch_dispatch.py`'s `TestDisplayModeImportRetained` was deleted, because its only subject was the import kept for the removed `change_mode`.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/display/manager_backup.py`, `setup_original_backup.py`, `src/gtach/comm/bluetooth.py`, `src/gtach/display/navigation_gestures.py` | Removed (`git rm`). |
| `src/gtach/core/thread.py`, `core/watchdog.py` | R11, R12, R13. |
| `src/gtach/comm/pairing.py`, `comm/system_bluetooth.py` | R2, R13. |
| `src/gtach/display/manager.py`, `touch.py`, `touch_interface.py`, `typography.py` | R3, R4, R5, R13. |
| `src/gtach/display/setup_components/` (coordinator, device_surfaces, circular_positioning), `graphics/`, `splash.py`, `performance/__init__.py`, `setup.py` | R6, R7, R8, R13. |
| `src/gtach/utils/terminal.py`, `utils/platform.py`, `utils/ack_state.py` | R9, R10, R13. |
| Other modules under `src/gtach/` | R13 import and variable removals. |
| `tests/test_logging_policy.py`, `tests/test_pi_reset.py`, `tests/test_touch_dispatch.py`, `tests/test_watchdog_process_termination.py`, `tests/test_low_defects.py` | R1, R11, R14; the D08 test retargeted to `create_slot_surface`. |
| `CLAUDE.md` | §2 backup-files line removed. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

No new test module.
- **Tests deleted:** `TestDisplayModeImportRetained` (one test).
- **Tests added:** `test_no_shell_helpers_anywhere` (two parametrised cases).
- **Tests adjusted:** the `hard_recovery_attempts` assertion was removed; the D08 test was retargeted.

pytest after this commit: 447 passed (446 before the commit). 45 files changed and 8,669 lines were removed.

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| The four modules no longer exist | `ls` | Pass |
| No reference to the backup modules in src, tests or CLAUDE.md | `grep` | No matches |
| No RESTARTING, HARD_RECOVERY, hard_recovery, restart_future, _active_futures or target_func in src | `grep` | No matches |
| `flake8 --select F401,F841,F811,F402,F541 src/gtach` reports nothing | Ran it | Clean |
| `python -c 'import gtach.app, gtach.main'` succeeds; the 8 s simtcp smoke run shows no import or attribute error | Ran both. The smoke run had GTACH_HOME and the log paths in the scratchpad; the logs show SimTransport connected, the SIGINT received and shutdown complete in under 0.1 s. The only traceback was the expected framebuffer ioctl failure in the container | Pass |
| `pytest tests/` passes | Full run | 447 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

Kept, because they are still referenced or not in the removal list:
- the `signal` import in app.py (used);
- `validate_all_layout_elements` and `validate_circular_bounds` (used by `tests/test_device_list_focus.py`);
- `HyperPixelTouchInterface.simulate_touch_event` and `MockHyperPixelTouch.simulate_touch` (not listed);
- unreferenced but unlisted items: `TouchHandler.get_touch_interface_info`, `get_circular_safe_area`, `clear_layout_cache`, `normalize_coordinates`/`denormalize_coordinates`, the ButtonSize/ButtonState enums, and `initialize_performance_manager`/`cleanup_performance_manager`;
- `ThreadManager.worker_pool` and the rpm_warning/rpm_danger keys, as the prompt requires.

Removed beyond the list, because their only callers were removed code:
- `_draw_obdii_icon`;
- `MockTouchInterface._print_development_info` and its call;
- the DisplayManager slider call in `handle_touch_event`.

The availability-probe imports in touch_interface.py and the rendering engine are kept with `# noqa: F401`.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

Deploy and use normally; there is no on-device step specific to this change.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-cd5ec050. |

---

Copyright (c) 2026 William Watson. MIT License.
