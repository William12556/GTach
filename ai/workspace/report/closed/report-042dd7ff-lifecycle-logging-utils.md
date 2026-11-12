Created: 2026 November 11

# Report: Application Lifecycle, Logging and Utility Corrections

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Changes by Edit](<#2. changes by edit>)
3. [Cause of the importlib.resources Record](<#3. cause of the importlib.resources record>)
4. [Comment Rule](<#4. comment rule>)
5. [Tests](<#5. tests>)
6. [Success Criteria](<#6. success criteria>)
7. [Deviations and Notes for the Planner](<#7. deviations and notes for the planner>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-042dd7ff (change-042dd7ff, issue-042dd7ff; run 3 of proposal-71ab3751) was implemented in one commit on branch `claude/zen-wozniak-25wtfh`. EDITS A to F and the COMMENT RULE were applied. The issue and change T-Docs remain active pending test results. The prompt T-Doc was closed and moved to `ai/workspace/prompt/closed/`.

- pytest `tests/`: 654 passed (619 before, plus 35 in the new module). `TestProcessExit` in `test_lifecycle_sim.py` ran (pygame present, no `/opt/gtach`) and passed with the exit-status assertion.
- mypy `src/`: no issues. With `platform = "linux"` in `[tool.mypy]`, a plain `mypy src/` no longer depends on the host platform; `mypy --platform darwin src/` still reports the 4 platform-only errors, as expected.
- black, isort and flake8 report nothing in the touched files.
- `git diff` touches only `app.py`, `main.py`, `core/watchdog.py`, `utils/`, `pyproject.toml`, `tests/` and the T-Docs under `ai/workspace/`.

[Return to Table of Contents](<#table of contents>)

---

## 2. Changes by Edit

| Edit | File | Change |
|---|---|---|
| A(1) B01 | `app.py` | `_start_setup_mode` stores its `pairing_factory` in `_pairing_factory`; `_re_enter_setup` passes it back. A simbt session therefore re-enters setup with `SimBluetoothPairing`. |
| A(2) A10 | `app.py` | In `__init__`, before the first `get_device_store()`, transport `simbt` calls `set_device_store_path(gtach_home()/config/devices-sim.yaml)`. Other transports leave the default. |
| A(3) B02 | `app.py` | `_start_obd` passes `adapter_pre_initialised=True` only when a setup manager exists and `getattr(manager, 'adapter_reset_in_session', False)` is truthy. Until change-34781bfe adds the attribute, ATZ is always sent. |
| A(4) B03 | `app.py` | `_on_setup_complete` wraps `_start_obd`; on an exception it clears `_obd_started` under `_obd_lock` and logs with `exc_info`. The exception is not re-raised. |
| A(5) B04 | `app.py`, `main.py` | Module constants `EXIT_OK = 0`, `EXIT_FAILURE = 1`; attribute `_exit_status`, default 0. `_watchdog_shutdown` and the `except Exception` path of `run()` (which also catches a startup failure re-raised by `start()`) set 1. The signal handler and `_request_restart` leave 0. `run()` returns the status; `main()` returns `app.run()`. |
| A(6) B04 | `app.py` | `shutdown()` runs each step in its own `try/except` with `exc_info`. Order unchanged: watchdog, setup manager, async manager, display, transport, OBD, thread manager. A component attribute that is missing or None is skipped. Idempotence (`_shutdown_called`) and the single backstop arm are unchanged. |
| A(7) B06 | `app.py` | The `_re_enter_setup` comment states that each `stop_thread` call is bounded by its timeout; the stale reference to `OBDProtocol.stop` (report-b4f9607a note 6) is gone. |
| B(1) O1 | `main.py`, `app.py` | New `set_runtime_log_level(debug)`: root DEBUG when on, WARNING otherwise. `setup_logging` keeps DEBUG for startup. `_finish_startup_logging` calls it after closing start.log, with the debug state read from the debug handler's level. `toggle_debug_logging` calls it before logging its own INFO record. Both reach `gtach.main` through `sys.modules['gtach.main']`. Handler levels are unchanged. |
| B(2) G01 | `main.py` | New `_run_validation(args)`, called after argument parsing and before `setup_logging` and `stack_dump.install`. It configures `logging.basicConfig(stream=sys.stderr)` at WARNING (DEBUG with `--debug`) and opens no log file. Exit statuses are unchanged. |
| B(3) | `main.py` | `_derive_log_paths()` sets `_START_LOG`, `_DEBUG_LOG`, `_STACKS_LOG` and `_ERROR_LOG` from `gtach_home()`; `setup_logging` calls it first. At import the names hold the `DEFAULT_GTACH_HOME` paths, so the default home gives the present `/opt/gtach` paths. `stack_dump.install(lambda: _STACKS_LOG)` reads the derived value. `main.py` now imports `gtach.utils.home` at module level; that imports `gtach.utils` (config, dependencies, platform, terminal) but nothing under `comm` or `display`. |
| C B07 | `core/watchdog.py` | `_handle_critical_timeout`: the ERROR "initiating emergency procedures" and the shutdown are for critical threads only, unchanged. A non-critical thread gets one WARNING ("not critical, no action taken") when first seen at this level, then at most once per `NON_CRITICAL_WARNING_INTERVAL_S = 60.0` s on `time.monotonic`. The timestamp is a new `ThreadHealth.last_critical_warning_time` (default `-inf`), reset in `_reset_thread_health` when the thread recovers. |
| D(1) E06 | `utils/config.py` | New `_typed_value(kind, value)` serves `load()` and `validate()`: None and bool are rejected for every key; an int key accepts an int or an integral float (converted to int); a float key accepts an int or float; a str key accepts a str. `load()` warns and uses the default when it rejects a value. |
| D(2) E05 | `utils/config.py` | `ConfigStore._save_lock` serialises the whole save, which moved unchanged into `_save_locked`. `_lock` still guards only `_unknown` and is never held across I/O. |
| D(3) | `utils/config.py` | `_engine_profiles_path()` resolves `importlib.resources.files("gtach") / "assets" / "engine_profiles.yaml"`, then falls back to the path relative to the module. `load_engine_profile` and `_engine_profile_names` both use it. The `pkg_resources` branch and the `sys` and `cast` imports were removed. Cause: section 3. |
| D(4) E03 | `utils/dependencies.py` | The debug-mode `find_spec` is guarded against ImportError and ValueError; a failure is logged at DEBUG. |
| D(5) E04 | `utils/terminal.py` | `TerminalRestorer.__init__` takes no backup when `sys.stdin` is None or `fileno()` raises ValueError or OSError. |
| D(6) | `utils/pi_reset.py` | For a non-zero return code, `reboot_device` logs a WARNING with the code and the first line of stderr. A negative code returns "reboot initiated"; a positive code returns "reboot command failed". |
| D(7) E02 | `utils/pi_reset.py` | The module docstring states the boundary: pi_reset is the only module that acts on the host; `subprocess` is also used read-only in `comm/system_bluetooth.py` and `utils/platform.py`. |
| D(8) | `utils/ack_state.py` | `get_state_info` returns the loaded value only if it is a dict, else None. The `type: ignore` and TODO markers were removed. |
| E | `pyproject.toml` | `platform = "linux"` under `[tool.mypy]`. |
| F F01 | `tests/test_lifecycle_sim.py` | The SIGTERM test asserts `proc.wait(timeout=10.0) == 0`. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Cause of the importlib.resources Record

`src/gtach/assets/` has no `__init__.py`, so `gtach.assets` is a namespace package whose spec has `origin = None`. In CPython 3.9, `importlib.resources.files(package)` calls `_common.from_package`, which calls `fallback_resources(spec)`, which evaluates `pathlib.Path(spec.origin).parent`. With `origin = None` this raises TypeError. `load_engine_profile` caught it, logged "importlib.resources failed" at DEBUG and used the relative-path fallback. This happens on every start on the Pi (Python 3.9).

Evidence:

- The CPython 3.9 source of `Lib/importlib/_common.py` and `resources.py` was read: `files()` → `from_package()` → `fallback_resources()` → `pathlib.Path(spec.origin)`.
- A one-off run on this host: `pathlib.Path(importlib.util.find_spec("gtach.assets").origin)` raises TypeError; the same expression for `gtach` gives `src/gtach`.
- On Python 3.10 and later, `files()` supports namespace packages, so the record does not appear on this host (Python 3.13). Python 3.9 itself was not available here, so the record was not reproduced end to end; confidence in the cause is high.

Fix: resolve from the regular package `gtach` and join `assets/engine_profiles.yaml`; this works on 3.9 and later. `TestEngineProfile.test_assets_namespace_not_used` makes `files("gtach.assets")` raise TypeError and checks that no failure record is logged and the profile loads. Adding `assets/__init__.py` would also fix it, but that file lies outside the permitted diff.

[Return to Table of Contents](<#table of contents>)

---

## 4. Comment Rule

History-narrating comments were reduced to the current behaviour plus at most one reference in these places:

- `app.py`: `_EXIT_BACKSTOP_SEC`, `_watchdog_shutdown`, `_force_exit`, the two `sys.modules['gtach.main']` comments, `_on_reset_pi`, the reset-callback wiring in `_start_setup_mode`, `_re_enter_setup`, and the shutdown order.
- `main.py`: the `_stacks_rotated`, stacks, debug and error-log constants, the debug.log and error.log comments in `setup_logging`, and `enable_stack_dumps`.
- `utils/pi_reset.py`: the module docstring.
- `utils/config.py`: the `load_engine_profile` method comments, which were removed with the code they described.

`core/watchdog.py`, `utils/dependencies.py`, `utils/terminal.py` and `utils/ack_state.py` had no such comments in the edited regions.

[Return to Table of Contents](<#table of contents>)

---

## 5. Tests

The new module `tests/test_lifecycle_logging_utils.py` has 35 tests. It covers every scenario in the change's `testing_requirements`.

| Class | Covers |
|---|---|
| `TestReEnterSetupKeepsFactory` | B01: the second `SetupDisplayManager` receives the same factory. |
| `TestSimulatedDeviceStore` | A10: `simbt` uses `config/devices-sim.yaml`; `tcp` uses `config/devices.yaml`. |
| `TestAdapterPreInitialised` | B02: no manager, a manager without the attribute, and `adapter_reset_in_session=True` give False, False, True. |
| `TestSetupCompleteStartFailure` | B03: `_obd_started` is False after a TransportError, and a second call runs `_start_obd` again. |
| `TestExitStatus` | B04: start raising, signal, watchdog and restart give 1, 0, 1, 0. `main()` returns `run()`'s value. |
| `TestShutdownSteps` | B04: with `stop_setup` raising, the later steps still run in order; a second `shutdown()` runs nothing. |
| `TestRuntimeLogLevel` | O1: `set_runtime_log_level` False then True gives WARNING then DEBUG and the matching `isEnabledFor(DEBUG)`. `toggle_debug_logging` and `_finish_startup_logging` set the root level. |
| `TestValidateConfigOpensNoLog` | G01: `python -m gtach --validate-config` in a subprocess with GTACH_HOME at a temporary directory. start.log keeps its content, and no debug.log or error.log is created. Exit status 0 for a valid file, 1 for `fps_limit: 0`. |
| `TestLogPathsUnderHome` | The three handlers and `_STACKS_LOG` are under GTACH_HOME; the import-time names are the `/opt/gtach` paths. |
| `TestNonCriticalStall` | B07: six checks 5 s apart on a patched clock give one WARNING and no ERROR containing "emergency". A second WARNING follows after 60 s. |
| `TestConfigTypeRule` | E06: palette null, touch_long_press true and fps_limit 30.9 give three warnings, the defaults, and three `validate()` errors for the same keys. `fps_limit: 30.0` is accepted by both. |
| `TestConfigSaveSerialised` | E05: two threads × 200 saves all return True, and the file parses after each save. |
| `TestEngineProfile` | No "failed" record from `gtach.utils.config` at DEBUG; the profile loads (redline 6500), also with `files("gtach.assets")` made to raise. |
| `TestDependencyFindSpec` | E03: `_check_import("RPi.GPIO")` in debug mode with `RPi` absent returns unavailable and raises nothing. |
| `TestTerminalRestorer` | E04: `sys.stdin` None and a closed stdin; `original_termios` is None. |
| `TestResetOutcome` | Return codes 0, 1 and -15 give "reboot initiated", "reboot command failed" and "reboot initiated". Codes 1 and -15 each give one WARNING naming the code and the first stderr line. |
| `TestStateInfo` | A YAML list gives None; a mapping is returned. |

Existing tests changed because of the edits:

- `test_thread_lifecycle.py::test_stale_non_critical_thread_logs_only` asserted the ERROR record that EDIT C removes. It now asserts a WARNING, no "emergency" record, and no shutdown.
- `test_error_log.py`, `test_config_store.py` and `test_stack_dump_toggle.py`: the logging fixtures also set `GTACH_HOME` to their temporary directory, because `setup_logging` now derives the paths from it. They also restore `_STACKS_LOG`, which `setup_logging` now reassigns. `test_unopenable_path_does_not_raise` makes error.log unopenable by creating a directory at that path, because a monkeypatched `_ERROR_LOG` is now overwritten.

Regression scope: the full `tests/` suite passed (654), including `test_lifecycle_sim.py`, `test_watchdog_process_termination.py`, `test_medium_defects.py` and the config, logging and updater tests.

[Return to Table of Contents](<#table of contents>)

---

## 6. Success Criteria

| Criterion | Result |
|---|---|
| `_re_enter_setup` reuses the session's pairing factory | Met. |
| A 'simbt' session uses config/devices-sim.yaml | Met. |
| `adapter_pre_initialised` is True only when the setup manager reports `adapter_reset_in_session` | Met. |
| `_obd_started` is cleared when `_start_obd` raises | Met. |
| `main()` returns 1 after startup failure, runtime error or watchdog exit, and 0 otherwise | Met. |
| Each shutdown step is isolated | Met. |
| The root logger is at WARNING after startup with debug off and follows the debug switch | Met (Linux; both call sites are Linux-only, as before). |
| `--validate-config` and `--validate-dependencies` open no log file | Met; `--validate-config` is tested by subprocess. `--validate-dependencies` takes the same path but is not tested by subprocess. |
| Log paths derive from `gtach_home()` | Met. |
| No 'emergency procedures' record for a non-critical thread | Met. |
| `ConfigStore.load` and `validate()` apply the same type rule; save is serialised | Met. |
| No `type: ignore` remains at `get_state_info` | Met. |
| `git diff` touches only app.py, main.py, core/, utils/, pyproject.toml and tests/ | Met for source; the T-Doc move and this report are under `ai/workspace/`. |
| pytest passes; mypy reports no issues | Met. |

[Return to Table of Contents](<#table of contents>)

---

## 7. Deviations and Notes for the Planner

1. **E06, int rule.** Before this change `validate()` rejected every float for an int key. The shared rule now accepts an integral float (for example `fps_limit: 30.0`) in both methods, as the change's wording ("no non-integral float for an int") implies. `load()` also no longer turns `palette: null` into the string "None".
2. **O1, toggle off.** `toggle_debug_logging(False)` lowers the root level before it logs "Debug logging disabled", as the change specifies, so that record is not written anywhere. The docstring says so. Before this change it was not written either, because the debug handler had already been suppressed.
3. **O1, startup debug state.** `_finish_startup_logging` reads the debug state from the debug handler's level, not from `self._debug`, so a toggle made during startup is respected. If debug.log could not be opened, the root level is WARNING.
4. **B03.** The exception from `_start_obd` is logged and not re-raised to the setup thread. If `_start_obd` fails after starting the transport thread (for example in `OBDProtocol.start`), that thread keeps running. A retry is reached only through `_re_enter_setup`, which stops 'transport' and 'obd_protocol' first, so `register_thread` then replaces a stopped entry. A direct second `_start_obd` with the first transport thread still alive would have its registration refused ("already exists and is active"); no current path does this.
5. **A(6).** A component attribute that is None is skipped, where before only a missing attribute was skipped.
6. **B(3).** `main.py` imports `gtach.utils.home` at module level. This loads `gtach.utils` before argument parsing; nothing from `comm` or `display` is imported.
7. **Out of scope.** `reset_device_store()` still does not reset the path (report-b4f9607a note 7). The new tests restore it with `set_device_store_path(None)`.
8. **Design update pending (planner).** design-b4c5d6e7 needs the shared type rule for `load()`.
9. **Device session A** (human) remains to be done: start.log unchanged after `gtach --validate-config`, the debug toggle writes debug.log, Reset logs its return code, `systemctl status` after a forced startup failure, simbt re-entry, and ATZ after pairing (B02 interim).

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Implementation report for prompt-042dd7ff. |

---

Copyright (c) 2026 William Watson. MIT License.
