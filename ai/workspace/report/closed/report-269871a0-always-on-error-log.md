Created: 2026 October 07

# Report: Always-On Error Log and Tracebacks on Broad Handlers

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

prompt-269871a0 (change-269871a0, issue-269871a0; audit-36b6ea95 B04 and A11) was implemented in commit `5f3c50be158bf2bea57f47edf7383062032c3213`.

- **EDIT A:** `setup_logging` now adds a third root handler: `/opt/gtach/error.log` at WARNING, `RotatingFileHandler` at 1 MiB × 5, never rotated at start. If the file cannot be opened, the handler is skipped with a warning on stderr.
- **EDIT B:** `exc_info=True` was added to every ERROR/CRITICAL call in a broad exception handler. That is 204 calls in 25 modules, all of them logger calls (`self.logger` or `logger`), so the non-logger allow-list is empty. The audit estimate was 206 sites; the policy test found 204 distinct call sites, and the policy test is authoritative.
- **EDIT C:** the policy test, the error.log tests and the fixture redirect.
- **EDIT D:** CLAUDE.md §3 Logging row and Version History 1.2.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/main.py` | EDIT A: `_ERROR_LOG`, `_ERROR_MAX_BYTES`, `_ERROR_BACKUPS`, `_error_handler`; handler creation in `setup_logging`; docstring describing the three handlers. |
| 25 modules under `src/gtach/` | EDIT B, 204 lines: comm/ (device_store 6, obd 3, pairing 9, system_bluetooth 7, transport 2), core/thread 2, display/ (async_operations 2, graphics/splash_graphics 12, input/touch_coordinator 18, manager 22, navigation_gestures 15, performance/monitor 14, rendering/engine 10, setup 4, setup_components bluetooth/interface 11, layout/circular_positioning 10, rendering/device_surfaces 6, state/coordinator 6, splash 8, touch 11, touch_interface 12, typography 3), utils/ (config 3, platform 4, terminal 4). |
| `tests/test_logging_policy.py` | New: AST policy test and checker tests. |
| `tests/test_error_log.py` | New: EDIT A tests. |
| `tests/test_stack_dump_toggle.py` | `isolated_logging` also redirects `_ERROR_LOG`. No other change. |
| `CLAUDE.md` | EDIT D. |

`src/gtach/app.py` had no policy-test sites and is unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

- **`tests/test_logging_policy.py`** (3 tests):
  - zero violations across `src/gtach` (backup modules excluded);
  - a synthetic source with one violation, a narrow handler and an explicit `exc_info=False` reports exactly one violation;
  - bare, tuple and nested broad handlers are all detected.
- **`tests/test_error_log.py`** (6 tests):
  - the constants;
  - WARNING and ERROR are written but not INFO;
  - the handler type, level and rotation settings;
  - an ERROR is recorded after start.log is silenced to CRITICAL + 1;
  - pre-existing content stays in the live file and no `error.log.1` is created;
  - an unopenable path gives no exception, a `None` handler and a stderr warning.

All tests redirect `_START_LOG`, `_DEBUG_LOG` and `_ERROR_LOG` to `tmp_path` and restore the root handlers afterwards.

pytest after this commit: 302 passed (293 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| Constants and `_error_handler` defined | `test_constants`; code review | Pass |
| WARNING `RotatingFileHandler`, no `doRollover` on it | `test_handler_is_rotating_at_warning`, `test_not_rotated_at_start`; `grep doRollover main.py` shows only the debug.log call (and a comment) | Pass |
| debug.log block unchanged | `git diff` of `main.py`: all hunks are additions outside the debug.log block | Pass |
| `_finish_startup_logging` and `toggle_debug_logging` unchanged | `git diff 5f3c50b^ 5f3c50b -- src/gtach/app.py` is empty | Pass |
| Policy test passes with zero violations | `tests/test_logging_policy.py` | Pass |
| EDIT B diff is only added `exc_info=True` | Script comparing every removed/added line pair: the added line minus `, exc_info=True` equals the removed line; 204 pairs, 0 mismatches | Pass |
| No test writes under `/opt/gtach` | Every `setup_logging` caller redirects all three paths; `/opt/gtach` did not exist before or after the full run | Pass |
| `pytest tests/` passes | Full run | 302 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None. The EDIT A tests were placed in a new module, `tests/test_error_log.py`; the prompt left the location open.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

With debug off, power off the adapter for 30 s and confirm that `error.log` records the event with a traceback. Then restart the service and confirm the earlier records remain.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-269871a0. |

---

Copyright (c) 2026 William Watson. MIT License.
