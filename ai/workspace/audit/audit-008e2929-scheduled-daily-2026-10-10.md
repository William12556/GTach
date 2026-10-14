Created: 2026 October 10

# GTach Scheduled Daily Audit — 2026-10-10 (audit-008e2929)

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Method](<#2.0 method>)
- [3.0 Activity Summary](<#3.0 activity summary>)
- [4.0 Finding F1: Orphaned Module Global After Legacy Function Removal](<#4.0 finding f1 orphaned module global after legacy function removal>)
- [5.0 Observations](<#5.0 observations>)
- [6.0 Changes Reviewed Without Finding](<#6.0 changes reviewed without finding>)
- [7.0 Recommendations](<#7.0 recommendations>)
- [Version History](<#version history>)

---

## 1.0 Purpose

This audit reviews code changes committed to the GTach repository in the 24 hours preceding 2026-10-10 01:03 UTC for defects.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

- The repository was cloned anonymously with `--filter=blob:none`.
- The window comprises 51 commits, oldest `4720d39` (2026-10-09 04:44 UTC), newest `171e531` (2026-10-09 12:32 UTC). The diff range is `4720d39^..HEAD`.
- The full diff of every `*.py`, `*.toml` and `*.yaml` path under `src/`, `tests/` and the project root was read. The deleted `ai-local/retired-5bcd46ad/` tree was counted but not reviewed line by line, since it was removed in full.
- Orphaned references to every removed symbol were searched with `git grep` across `src`, `tests`, `bin` and `config`.
- The test suite was not executed: `pygame` could not be installed in the audit container.
- The GitHub MCP tools returned zero open issues and zero open pull requests.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Activity Summary

| Scope | Commits | Files | Insertions | Deletions | New tags |
|---|---|---|---|---|---|
| Repository | 51 | 183 | 11302 | 20011 | 0 |
| `src/`, `tests/`, `pyproject.toml` | — | 59 | 1423 | 685 | — |
| `ai-local/` (deleted) | 1 | 30 | 0 | 12153 | — |

- Files by type: 84 `.md`, 64 `.py`, 11 `.txt`, 5 `.yaml`, 1 `.toml`, 18 `.fuse_hidden*` (removed by `8225f38`; none remain at HEAD).
- The version was bumped from 0.4.9 to 0.4.10 (`b1dd162`). No tag was created; the newest tag remains `v0.4.0`.
- Code changes implement eleven change records: 50bf25ad, 04c18cda, ae65fa10, c9de5fb0, 2b3a1547, 8a9022fc, 273ca048, e215a184, ac11505d, 4f671d09 and d26ca557.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Finding F1: Orphaned Module Global After Legacy Function Removal

- **Classification:** Confirmed.
- **Severity:** Low.
- **Commit:** `bf03008` (change-273ca048, residual dead code).
- **Location:** `src/gtach/display/performance/__init__.py:18-19`.

Change 273ca048 removed `initialize_performance_manager` and `cleanup_performance_manager`, the only readers and writers of `_global_performance_manager`. The global and its comment remain:

```python
# Legacy compatibility functions
_global_performance_manager = None
```

`git grep _global_performance_manager -- src tests` returns only this definition. The comment now describes functions that no longer exist. The defect has no runtime effect; it leaves the dead-code removal that 273ca048 set out to complete unfinished.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Observations

- Change ac11505d adds several `# type: ignore[...]  # TODO: issue-ac11505d candidate defect` markers rather than resolving the underlying issues. Notable ones: `app.py` passes `rendering_engine.main_surface` that may be `None` to `SetupDisplayManager`; `touch_coordinator.py` calls `self._is_drag_gesture()`, which mypy reports as undefined (`attr-defined`); `setup.py` contains an unreachable `manual_entry_mode` branch. These are pre-existing and self-declared, so they are not counted as findings. The `_is_drag_gesture` marker, if accurate, denotes an `AttributeError` on the drag path and merits a separate issue.
- Change 4f671d09 deliberately leaves `app.py:594` (`self._stop_event.wait(timeout=0.5)`), `async_operations.py:264` and the `Thread.join` timeouts on timed `Event`/queue waits. The change record documents the rationale; the exclusion is consistent with it.
- `wait_for_event` polls at 0.1 s. Each converted long-lived wait (transport supervisor, watchdog, OBD back-off) now wakes ten times per second. The cost on a Pi Zero 2 W is expected to be small but has not been measured here.
- `verify_obd_connection` sleeps with `time.sleep` between busy retries and does not observe a shutdown request. The worst-case added delay is 2 s.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Changes Reviewed Without Finding

- **4f671d09** — `utils/waits.py` `wait_for_event`: correct early return, monotonic deadline, non-positive timeout handled. Call sites in `transport.py`, `obd.py`, `watchdog.py`, `interface.py` and `splash.py` preserve the boolean contract; `splash.wait_for_completion` keeps an untimed `Event.wait()` for `None`.
- **04c18cda** — OBD pre-initialised settle is sliced at 0.5 s with a heartbeat per slice and returns `False` on stop; the protocol loop handles `False` with back-off.
- **d26ca557** — `LINK_BUSY_CAUSE` constant replaces the literal in `_CONNECT_FAULT_CAUSES`; the retry is bounded to three attempts, retries only that cause, and cannot be pre-empted by the wedge escalation (`_MAX_CONSECUTIVE_CONNECT_FAILURES` is 6).
- **50bf25ad** — `SimTransport.drop_link` clears `_connected` and delegates to the base without setting `_shutdown`; the two strict `xfail` markers are correctly removed.
- **ae65fa10** — `ConfigStore.save` re-reads unknown keys from the file, falls back to retained keys on `OSError`/`YAMLError` or a non-mapping document, and performs file I/O outside the lock.
- **c9de5fb0** — `BluetoothDevice.from_discovered` replaces both duplicated conversions (`interface.py`, `sim_bluetooth.py`).
- **2b3a1547** — package re-exports removed; no `from gtach import` usages remain; the `gtach.main:main` entry point is unaffected.
- **273ca048** — removed symbols (`ButtonSize`, `ButtonState`, `SetupScreen.CONFIRMATION`/`DEVICE_MANAGEMENT`, `get_circular_safe_area`, `clear_layout_cache`, `get_performance_report`, `get_touch_interface_info`, `ACQUIRE_TIMEOUT`) have no remaining references in `src`, `tests` or `bin`; F1 excepted.
- **e215a184** — duration and cache-age conversions to `time.monotonic()`; zero-initialised timestamps are guarded by truthiness or `is not None` checks, so short uptime does not produce false cache hits.
- **8a9022fc** — slot-content tests now render through `_render_device_list_screen` with a recording wrapper; assertions match the documented slot rule.
- **ac11505d** — `_record_timeout` call sites now return `None` explicitly; behaviour is unchanged. Remaining edits are annotations and stub dependencies.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Recommendations

1. Remove `_global_performance_manager` and its comment from `src/gtach/display/performance/__init__.py` (F1).
2. Verify whether `TouchCoordinator._is_drag_gesture` exists; if not, raise an issue for the drag path.
3. Run the full test suite on the Mac and on `gtach.local` for 0.4.10, since this audit could not execute it.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-10 | Initial scheduled daily audit. |

Copyright (c) 2026 William Watson. MIT License.
