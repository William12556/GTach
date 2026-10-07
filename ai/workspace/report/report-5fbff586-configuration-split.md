Created: 2026 October 07

# Report: Single Configuration Store Under GTACH_HOME

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

prompt-5fbff586 (change-5fbff586, issue-5fbff586; audit-36b6ea95 E01, E02, E04, E08, G07 and X04 in part) was implemented in commit `f5ab73a994fe898d521f26fdd41225a53c69f90c`.

- **EDIT A:** `utils/home.py` is now `GTACH_HOME_ENV`, `DEFAULT_GTACH_HOME` (`/opt/gtach`) and `gtach_home()`. It returns `$GTACH_HOME` if set and non-empty, else `/opt/gtach`, and creates no directory.
- **EDIT B:** `utils/config.py` keeps `load_engine_profile` and `SplashConfig` verbatim. Everything else is replaced by `AppConfig` (seven flat keys) and `ConfigStore`:
  - `load()` never writes. It coerces types, replaces invalid values by defaults with a warning, maps DIGITAL to RADIAL, and retains unknown keys.
  - `save()` merges over the retained unknown keys and writes atomically: temporary file in the same directory, flush, fsync, `os.replace`.
  - `validate()` returns a list of errors.
  - Removed: ConfigManager, ConfigValidator, ConfigTransaction, RWLock, BluetoothConfig, the utils DisplayConfig, SessionConfig, SessionManager, OBDConfig and the INI path. The module went from 1,605 to 380 lines.
- **EDITS C to I:**
  - `utils/__init__.py` exports the new names.
  - DisplayManager takes an injected `config_store` and does no configuration file I/O of its own. The first-run save is removed.
  - `GTachApplication` creates one store and injects it.
  - `main.py` loses `find_configuration_file`; `--validate-config` exits 1 on any error.
  - `BluetoothPairing` uses constant timeouts.
  - `setup.py` loses an unused import.
  - The acknowledgement state moves to `gtach_home()/config/ack_state.yaml`, with its directory created on save.
- **EDITS J to L:**
  - `config/config.yaml` is replaced by `config/config.example.yaml`.
  - conftest sets `GTACH_HOME` and loses the ConfigManager reset fixture.
  - `tests/utils/test_rwlock.py` is removed.
  - CLAUDE.md §3 and §9 are updated, with Version History 1.4.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/utils/home.py` | EDIT A (rewritten). |
| `src/gtach/utils/config.py` | EDIT B (rewritten; obsolete classes removed). |
| `src/gtach/utils/__init__.py` | EDIT C. |
| `src/gtach/display/manager.py` | EDIT D: constructor, `_load_config`, `_save_config`; YAML import removed. |
| `src/gtach/app.py` | EDIT E. |
| `src/gtach/main.py` | EDIT F. |
| `src/gtach/comm/pairing.py` | EDIT G: timeout class constants; ConfigManager parameter and YAML read removed. |
| `src/gtach/display/setup.py` | EDIT H. |
| `src/gtach/utils/ack_state.py` | EDIT I. |
| `config/config.yaml` | Removed (EDIT J). |
| `config/config.example.yaml` | New (EDIT J). |
| `tests/conftest.py` | EDIT K: `GTACH_HOME`; ConfigManager reset fixture removed. |
| `tests/utils/test_rwlock.py` | Removed (EDIT K). |
| `tests/test_config_store.py` | New: 30 tests (EDIT K). |
| `CLAUDE.md` | EDIT L. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_config_store.py` has 30 tests, covering every change test case and both edge cases:

- **`gtach_home`:** unset, empty and set; the ConfigStore default path.
- **`load`:**
  - a missing file gives the defaults and creates nothing;
  - the device's file loads with its values;
  - DIGITAL → RADIAL;
  - `fps_limit: abc` → 30, with a warning;
  - invalid YAML and a YAML list each give the defaults.
- **`save`:**
  - the round trip keeps `foo: 1`;
  - a file with only unknown keys keeps them;
  - a missing directory is created and no temporary file is left behind.
- **`validate`:**
  - a valid file, a missing file and DIGITAL each give [];
  - nine invalid cases (unknown key, wrong type, mode, palette, engine profile, fps_limit low and high, touch_long_press low and high) each give one error naming the key;
  - a non-mapping gives one error.
- **CLI:** `--validate-config` on an invalid file exits 1 and prints the error; on a valid file it exits 0.
- **DisplayManager on a host object:**
  - loading does not create the file, and the palette and mode round-trip through the store;
  - `_save_config` produces exactly one `AppConfig` through the store.

pytest after this commit: 391 passed (372 before; the 11 RWLock tests were removed with their module). `git status --porcelain` after the run showed only this task's changes, and `/opt/gtach` was not created.

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| grep for ConfigManager, OBDConfig, OBDII_HOME, OBDIIHome, RWLock, ConfigValidator, SessionManager, find_configuration_file in src and tests returns nothing | Ran the grep (backups excluded) | No matches |
| DisplayManager has no `open()`, `yaml.dump` or `yaml.safe_load` for configuration | `grep -n 'open(\|yaml\.' src/gtach/display/manager.py` | No matches |
| `config/config.yaml` removed; `config/config.example.yaml` exists | `git show --stat f5ab73a` | Pass |
| `tests/utils/test_rwlock.py` removed | `git show --stat f5ab73a` | Pass |
| `git status --porcelain` after a full run shows nothing outside the commit | Ran it after the full run | Pass |
| `python -c 'import gtach.app, gtach.main'` succeeds | Ran it | Pass |
| `pytest tests/` passes | Full run | 391 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- **`fps_limit` default:** where config.yaml lacks the key or is missing, the default is now 30 (the `AppConfig` default) instead of 60 (the `DisplayConfig` default). The Pi's file sets `fps_limit: 30`, so behaviour there is unchanged.
- **DIGITAL log:** the INFO line DisplayManager logged when mapping DIGITAL to RADIAL is gone. `ConfigStore.load` now does the mapping without logging.
- **Profile lookup:** `validate()` finds the profile file through a small helper, `_engine_profile_names()`, which repeats `load_engine_profile`'s path resolution, because `load_engine_profile` had to stay unchanged.
- **Unknown keys:** they are retained from the store's most recent `load()`. A `save()` on a store that has never loaded would drop them. DisplayManager always loads before saving.
- **Validation details:** `validate()` rejects booleans for int and float keys. `load()` logs a non-mapping file at WARNING (an invalid value) rather than ERROR.
- **Unused constant:** `tests/conftest.py` keeps the `ACQUIRE_TIMEOUT` constant, which only the removed RWLock tests used. Only the ConfigManager fixture was in scope to remove.
- **Audit script:** `bin/gtach-audit-checks.sh` still describes the old configuration locations. It is outside the prompt's file list.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

On the Pi, after deployment:

1. The display settings from `/opt/gtach/config.yaml` still apply.
2. `/opt/gtach/venv/bin/gtach --validate-config` prints 'Config valid'.
3. Setting `fps_limit` to 0 makes it exit 1. Restore the value afterwards.
4. The acknowledgement screen appears once after the upgrade and is then remembered.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-5fbff586. |

---

Copyright (c) 2026 William Watson. MIT License.
