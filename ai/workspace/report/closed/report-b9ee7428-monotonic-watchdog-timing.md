Created: 2026 October 07

# Report: Monotonic Time for Heartbeats, Watchdog and Shutdown Budget

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

prompt-b9ee7428 (change-b9ee7428, issue-b9ee7428; audit-36b6ea95 B13) was implemented in commit `29bdebedc0343da5eb20ddf25ca4b5e5c4c9c66a`.

All elapsed-time arithmetic in `src/gtach/core/` now uses `time.monotonic()`. This covers heartbeat stamps (`register_thread`, `update_heartbeat`, `_restart_thread`), the watchdog health checks (`_check_thread_health`, `_handle_warning_timeout`, `_handle_recovery_timeout`, `get_thread_health_status`) and the `ThreadManager.shutdown` time budget.

`ThreadHealth.last_warning_time` and `last_recovery_time` now default to `float('-inf')`. With a 0.0 default, the first warning would be suppressed for 30 s after boot and the first recovery for 10 s.

A wall-clock step in either direction no longer changes any watchdog decision.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/core/thread.py` | EDIT E: six `time.time()` → `time.monotonic()`; comment on `ThreadInfo.last_heartbeat`. `creation_time` (`default_factory=time.time`) is unchanged. |
| `src/gtach/core/watchdog.py` | EDIT F: four `time.time()` → `time.monotonic()`; `get_thread_health_status` docstring states that `last_heartbeat` is monotonic. EDIT G: `ThreadHealth` defaults changed to `float('-inf')`, with a comment. |
| `tests/test_watchdog_process_termination.py` | EDIT H: `_aged_thread` uses `time.monotonic() - age`. No other change. |
| `tests/test_monotonic_watchdog_timing.py` | EDIT H: new module. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_monotonic_watchdog_timing.py` has six tests, one per prompt scenario plus the edge case:

- `test_forward_step_does_not_shut_down`: wall clock +400,000 s; no shutdown and no warning naming `display`.
- `test_backward_step_does_not_mask_a_genuine_stall`: wall clock −400,000 s with a monotonic stall beyond `critical_timeout`; shutdown is called once.
- `test_advisory_thread_with_forward_step_is_not_warned`: edge case; `transport` with a forward step is not warned.
- `test_critical_stall_shuts_down`: no clock patch; a monotonic stall still shuts down.
- `test_thread_health_defaults_are_minus_infinity`: `ThreadHealth(name='x')` defaults are `-inf`.
- `test_first_warning_not_suppressed_shortly_after_boot`: `time.monotonic` returns 5.0 and elapsed time lies between the warning and recovery timeouts; the warning is logged on the first check.

pytest after this commit: 293 passed (287 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| `grep -n 'time.time()' src/gtach/core/watchdog.py` returns nothing | Ran the grep | No matches |
| `grep -n 'time\.time' src/gtach/core/thread.py` returns only the `creation_time` line | Ran the grep | Only line 61 (`creation_time`) |
| `ThreadHealth` defaults are `float('-inf')` | `test_thread_health_defaults_are_minus_infinity` | Pass |
| Tiers, timeouts and two-phase locking unchanged | Reviewed `git diff` of `watchdog.py`: only the four clock calls, the defaults and the docstring changed | Pass |
| No file outside `src/gtach/core/` and `tests/` modified | `git show --stat 29bdebe` | Pass |
| `pytest tests/` passes | Full run | 293 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

Power the Pi off for more than a minute, boot with Wi-Fi available, and confirm that `journalctl -u gtach -b` shows no 'Succeeded' or 'Scheduled restart' entries.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-b9ee7428. |

---

Copyright (c) 2026 William Watson. MIT License.
