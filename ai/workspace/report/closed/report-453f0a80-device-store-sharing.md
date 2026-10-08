Created: 2026 October 07

# Report: Shared, Locked DeviceStore Under GTACH_HOME

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

prompt-453f0a80 (change-453f0a80, issue-453f0a80; audit-36b6ea95 A09 and A10) was implemented in commit `3747d2fd16f15cecb30316b47cee8bfd7b8e5d1f`.

- **EDIT A:**
  - `DeviceStore.__init__(config_path: Optional[str] = None)` defaults to `gtach_home()/config/devices.yaml`, which is `/opt/gtach/config/devices.yaml` on the Pi.
  - `self._lock` is created before the load.
  - Each public method (`save_device`, `get_primary_device`, `get_all_devices`, `remove_device`, `get_device_by_mac`) takes the lock and delegates to a `_*_locked` helper. The helpers call only other helpers, so no public method calls another while holding the non-reentrant lock.
- **EDIT B:** `_save_config` flushes and fsyncs the temporary file before `os.replace`.
- **EDIT C:** module-level `_shared`, `_shared_lock`, `get_device_store()` (constructs through the module-level name `DeviceStore`) and `reset_device_store()`.
- **EDIT D:** every production `DeviceStore()` construction now calls `get_device_store()`. This covers `app.py`, `transport.py`, `sim_bluetooth.py`, `manager.py`, `setup.py` (four sites) and `interface.py`. Inline imports stay inline.
- **EDITS E and F:**
  - `config/devices.yaml` is removed from the repository.
  - conftest resets the shared store after each test.
  - The new test module is added.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/device_store.py` | EDITS A to C. |
| `src/gtach/app.py`, `src/gtach/comm/transport.py`, `src/gtach/comm/sim_bluetooth.py`, `src/gtach/display/manager.py`, `src/gtach/display/setup.py`, `src/gtach/display/setup_components/bluetooth/interface.py` | EDIT D. |
| `config/devices.yaml` | Removed (EDIT E). |
| `tests/conftest.py` | EDIT F: autouse `reset_device_store` fixture. |
| `tests/test_device_store_shared.py` | New: 8 tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_device_store_shared.py` has 8 tests, covering every change test case:

- **Shared instance:**
  - the same object twice;
  - the default path is `tmp_path/config/devices.yaml`;
  - a device saved through one call site is returned through another;
  - after a reset, a new object.
- **Concurrency:**
  - two threads each save 50 secondaries; no exception, the file parses and all 100 are present;
  - every public method blocks while another thread holds `_lock` (additional).
- **Durable save:** `fsync` is called before `os.replace`.
- **Patched class:** the accessor constructs through the module-level name (additional).

No existing test needed changing. Those that patch `device_store_module.DeviceStore` keep working because of the per-test reset.

pytest after this commit: 399 passed (391 before the commit). `git status --porcelain` after the run showed only this task's changes; no `config/devices.yaml` was recreated and `/opt/gtach` was not created.

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| `grep -rn 'DeviceStore()' src` shows only the construction in `get_device_store` | Ran the grep (backups excluded) | Only `device_store.py:341` |
| `DeviceStore` has `self._lock` and every public method acquires it | Code review; `test_every_public_method_takes_the_lock` | Pass |
| `_save_config` calls `os.fsync` before `os.replace` | `test_fsync_before_replace` | Pass |
| `config/devices.yaml` removed from the repository | `git show --stat 3747d2f` | Pass |
| `git status --porcelain` after a full run shows nothing outside the commit | Ran it after the full run | Pass |
| `pytest tests/` passes | Full run | 399 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- **File I/O under the lock:** the device file is read and written while `_lock` is held. The change requires each read-modify-save to run under the lock; this departs from the "no blocking I/O under a lock" part of CLAUDE.md §4 rule 8. No callback or foreign component is called under the lock.
- **Extra tests:** two tests beyond the change's cases, the lock-held probe and the patched-class test.
- **File creation:** as before, `DeviceStore` creates the devices file on first construction when it is missing; it now does so under `gtach_home()`.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

On the Pi, after the upgrade, the paired adapter is still used without re-pairing.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-453f0a80. |

---

Copyright (c) 2026 William Watson. MIT License.
