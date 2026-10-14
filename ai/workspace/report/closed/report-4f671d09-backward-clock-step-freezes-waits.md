Created: 2026 October 09

# Report: Clock-Step-Safe Waits for Supervision Loops

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests and Results](<#3. tests and results>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [Human Decisions and On-Device Verification](<#6. human decisions and on-device verification>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-4f671d09 (change-4f671d09, issue-4f671d09) was implemented in the commit that adds this report.

New helper `gtach.utils.waits.wait_for_event(event, timeout)` polls `event.is_set()` between `time.sleep` slices of at most `_POLL_SLICE_S` (0.1 s) against a `time.monotonic()` deadline. It never calls `Event.wait` or any timed lock acquire. `timeout <= 0` returns `event.is_set()` without sleeping. The module docstring cites issue-4f671d09 and explains why `Event.wait` is avoided, including why slicing it does not help.

The eight timed waits named in the prompt now call `wait_for_event` with the same event and timeout. Each caller uses the return value as before. `SplashScreen.wait_for_completion` keeps the untimed `self._completion_event.wait()` when `effective_timeout` is `None`. `verify_obd_connection`, `app.py`, `async_operations.py`, `join()` calls and `gtach/utils/__init__.py` were not changed.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/utils/waits.py` | New: `_POLL_SLICE_S`, `wait_for_event`. |
| `src/gtach/comm/transport.py` | Import; three `_shutdown.wait` calls in `reconnect_indefinitely` replaced; docstring sentence about waits updated. |
| `src/gtach/core/watchdog.py` | Import; `_monitor_loop` wait replaced. |
| `src/gtach/comm/obd.py` | Import; `_protocol_loop` init-retry wait and `_initialize_protocol` settle-slice wait replaced. |
| `src/gtach/display/setup_components/bluetooth/interface.py` | Import; `ensure_pairing_initialized` wait replaced. |
| `src/gtach/display/splash.py` | Import; `wait_for_completion` timed branch replaced, untimed branch kept. |
| `tests/test_monotonic_waits.py` | New: 12 tests. |
| `tests/test_link_loss_recovery.py` | Deviation (§5): `test_every_wait_is_on_shutdown` updated. |
| `tests/test_reconnect_path.py` | Deviation (§5): `test_failure_waits_on_shutdown_event` updated. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Results

`tests/test_monotonic_waits.py`:

- Helper (5): already set (no sleep, spy); set by a timer after 0.2 s; never set with timeout 0.3 s; an object exposing only `is_set()`; timeout 0 and −1 do not sleep.
- Call sites (7): `reconnect_indefinitely`, `_monitor_loop`, `_protocol_loop` init retry, `_initialize_protocol` settle, `ensure_pairing_initialized`, `wait_for_completion` timed, `wait_for_completion` untimed. Each event is replaced by an `Event` subclass whose `wait()` counts the call and raises `AssertionError`. Each test asserts the call count is 0. The counter is needed because `_protocol_loop`, `_initialize_protocol` and `ensure_pairing_initialized` catch `Exception`, which would otherwise hide the `AssertionError`. Loops run on a thread with a 5 s join bound, so a hang fails the test.

Before the call sites were changed, with `waits.py` already present so the module imports:

- 6 failed: all six timed call-site tests, each with `AssertionError: Event.wait called`.
- 6 passed: the five helper tests and the untimed splash test. The untimed branch is unchanged by design.

After implementation:

| Check | Result |
|---|---|
| `tests/test_monotonic_waits.py` | 12 passed |
| `pytest tests/` before the change | 561 passed |
| `pytest tests/` after call-site edits, before the §5 test updates | 571 passed, 2 failed (the two tests in §5) |
| `pytest tests/` final | 573 passed |
| `mypy src/` | 0 errors in 60 source files (59 before; `waits.py` added) |
| `black --check`, `isort --check-only`, `flake8` on all changed files | Clean |

Environment: the container runs Python 3.13.16. mypy 2.4.0 warns that `python_version = 3.9` in `pyproject.toml` is unsupported, and still reports 0 errors. Python 3.13 is not affected by the defect, so these tests check the mechanism (no `Event.wait`), not the clock-step behaviour itself.

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| No timed `.wait(` in the six named functions or branches | `grep -n "\.wait("` over the five source files finds only the untimed `self._completion_event.wait()` in `splash.py` |
| Call-site tests fail on the old source and pass on the new | 6/6 failed before, 7/7 pass after |
| `pytest tests/` passes; `mypy src/` 0 errors | 573 passed; 0 errors |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

Two existing tests asserted the removed mechanism and failed after the change. Neither file is listed in the prompt. The operator approved minimal updates in this session:

- `tests/test_link_loss_recovery.py::TestSupervisingLoop::test_every_wait_is_on_shutdown` counted `self._shutdown.wait(` == 3. It now counts `wait_for_event(self._shutdown,` == 3 and asserts no `.wait(` remains in `reconnect_indefinitely`.
- `tests/test_reconnect_path.py::TestInitBackOff::test_failure_waits_on_shutdown_event` monkeypatched `shutdown_event.wait`. It now monkeypatches `gtach.comm.obd.wait_for_event` and keeps the same assertion (at least two 2.0 s back-offs on `shutdown_event`).

No other deviations.

[Return to Table of Contents](<#table of contents>)

---

## 6. Human Decisions and On-Device Verification

- On gtach.local (Python 3.9): repeat the issue reproduction (NTP off, −1 h, wait 2 min, +2 h). Expect no "Thread transport appears unresponsive" warning. Turning the adapter off and on after a backward step should reconnect without Reset.
- The issue and change T-Docs remain active pending that result.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-4f671d09. |

---

Copyright (c) 2026 William Watson. MIT License.
