Created: 2026 August 12

# Report: Watchdog Critical-Thread Recovery Must Terminate the Process

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Edits Applied](<#3.0 edits applied>)
- [4.0 Tests Added](<#4.0 tests added>)
- [5.0 Verification Method](<#5.0 verification method>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Deviations from the Prompt Specification](<#7.0 deviations from the prompt specification>)
- [8.0 Findings Requiring Decision](<#8.0 findings requiring decision>)
- [9.0 Work Remaining](<#9.0 work remaining>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records the implementation of `prompt-2ac1c602-watchdog-terminates-process.md`
(iteration 1, coupled to `change-2ac1c602` and `issue-2ac1c602`).

Scope is what was changed and how it was verified. It does not re-argue
the design; that is in the coupled change document. On-target
verification is a human step and is explicitly outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc, and
leave the issue and change T-Docs active pending test results.

| Item | Outcome |
|---|---|
| EDIT A — `main.py`, faulthandler to an app-owned log | ✅ Applied |
| EDIT B — `app.py`, remove relocated faulthandler block | ✅ Applied |
| EDIT C — `app.py`, terminating watchdog callback | ✅ Applied |
| EDIT D — `app.py` + `transport.py`, register and heartbeat transport | ✅ Applied |
| EDIT E — `watchdog.py`, advisory monitoring tier | ✅ Applied |
| `tests/test_watchdog_process_termination.py` | ✅ Created, 10 tests |
| `tests/test_transport_heartbeat.py` | ✅ Created, 5 tests |
| `pytest tests/` | ✅ 34 passed, 0 failed |

`prompt-2ac1c602-watchdog-terminates-process.md` moved to
`ai/workspace/prompt/closed/`. The issue and change T-Docs remain
active, as instructed. No T06 result document was created.

No new modules and no new third-party dependencies. `bin/gtach.service`
and `src/gtach/comm/rfcomm.py` are byte-identical to their pre-change
state, as required by the constraints.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT A — `src/gtach/main.py`

Module-level `import faulthandler` added. `_STACKS_LOG =
'/opt/gtach/stacks.log'` added below `_DEBUG_LOG`. Module-level
`_stacks_file = None` added beside the existing handler references, and
`_stacks_file` added to `setup_logging`'s `global` statement.

A guarded block at the end of `setup_logging` opens `_STACKS_LOG` in
mode `'a'` with `buffering=1` and `encoding='utf-8'`, then calls
`faulthandler.enable(file=...)` and
`faulthandler.dump_traceback_later(15, repeat=True, file=...)`. It runs
only when `debug` is truthy. `OSError` is caught, a warning is printed
to `sys.stderr` in the style of the existing `_START_LOG` handler, and
`_stacks_file` is left as `None`.

The comment records why the relocation matters: faulthandler's repeat
timer runs in a C thread and does not need the GIL to schedule itself,
so its dumps still land while every Python thread is stalled — which is
the window that needs observing. Previously they went to `sys.stderr`,
which under systemd is the journal, not the app-owned log set beside
`start.log` and `debug.log`.

### 3.2 EDIT B — `src/gtach/app.py`

The faulthandler block in `GTachApplication.__init__`, including its
local `import faulthandler` / `import sys` lines and the comment
asserting that stderr is captured by a tee (false under systemd), was
deleted. `self._debug = debug` is retained.

### 3.3 EDIT C — `src/gtach/app.py`

Module-level `import os` added. Class constant `_EXIT_BACKSTOP_SEC:
float = 20.0` added to `GTachApplication`.

`self._stop_event = threading.Event()` moved so it is assigned at
`app.py:51`, before `self._watchdog = WatchdogMonitor(...)` at
`app.py:54`. The `WatchdogMonitor` construction now passes
`shutdown_callback=self._watchdog_shutdown`; `check_interval`,
`warning_timeout`, `recovery_timeout` and `critical_timeout` are
unchanged.

`_watchdog_shutdown(self) -> None` logs at CRITICAL, sets
`self._stop_event`, and starts a daemon `threading.Timer` targeting
`self._force_exit`. It contains no call to `self.shutdown()`. Its
docstring records the ordering decision: teardown is left to `run()`'s
finally block, which is idempotent via `_shutdown_called`, so
`shutdown()` is never invoked from the watchdog thread and the recovery
path does not depend on `WatchdogMonitor.stop()`'s self-join guard.

`_force_exit(self) -> None` logs at CRITICAL, calls `logging.shutdown()`
inside a bare `try/except Exception`, then calls `os._exit(1)`.

### 3.4 EDIT D — `src/gtach/comm/transport.py` and `src/gtach/app.py`

`Callable` added to the existing `from typing import Optional` import.
`OBDTransport.reconnect_indefinitely` now takes
`heartbeat: Optional[Callable[[], None]] = None`, documented in the
existing Args block.

The heartbeat is invoked at the top of each loop iteration and on both
sides of the `if self.connect():` outcome — on the True branch before
`return`, and on the False branch before the warning log. Each
invocation goes through a local `_beat()` helper that wraps the call in
`try/except Exception` and logs at DEBUG with `exc_info=True`, so a
raising callback cannot break the reconnect loop.

Both thread-construction sites in `app.py` — `_start_obd` and
`_start_normal_mode` — were edited identically: the thread is built with
`kwargs={'heartbeat': lambda: self._thread_manager.update_heartbeat('transport')}`
and `name='transport'`, and
`self._thread_manager.register_thread('transport', transport_thread)`
precedes `transport_thread.start()`, matching the registration order
used for the display thread. A comment at each site records that
registration is what makes the thread visible to `WatchdogMonitor`,
which iterates `thread_manager.threads` only.

No import of any `gtach.core` module was added to `gtach.comm`; the
heartbeat crosses the boundary as a plain callable supplied by the
caller.

### 3.5 EDIT E — `src/gtach/core/watchdog.py`

`self.critical_threads` is now `{'display'}`, with `self.advisory_threads
= {'transport'}` immediately below it. Both are commented as specified:
`'main'` was never registered with `ThreadManager` and so was never
monitored; `'transport'` is now registered but advisory, because a
blocking `connect()` lasting tens of seconds is expected transport
behaviour rather than a fault.

In `_check_thread_health` phase 1, after `level` is determined and
before `pending.append(...)`:

```python
if name in self.advisory_threads and level in ('critical', 'recovery'):
    level = 'warning'
```

The clamp is a dict lookup and a comparison — no blocking call — so the
lock discipline established by `change-5a9dc15e` is preserved. Phase 2
dispatch is unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

### 4.1 `tests/test_watchdog_process_termination.py` — 10 tests

Covers `testing.unit_tests` items 1–5 plus three of the listed edge
cases.

| Test | Prompt item |
|---|---|
| `test_sets_stop_event_and_does_not_shut_down` | item 1 |
| `test_second_invocation_is_harmless` | edge case 1 |
| `test_backstop_timer_is_a_daemon` | edge case 4 |
| `test_backstop_delay_is_twenty_seconds` | success criterion |
| `test_run_returns_and_shuts_down_once` | item 2 |
| `test_watchdog_shutdown_before_loop_entry` | edge case 2 |
| `test_second_call_is_a_no_op` | item 3 |
| `test_membership` | success criterion |
| `test_advisory_timeout_warns_but_never_recovers` | item 4 |
| `test_critical_timeout_still_shuts_down` | item 5 |

The `app` fixture constructs a real `GTachApplication` with nothing
started, in a `tmp_path` working directory (`DeviceStore` writes
`config/devices.yaml` relative to the cwd), with `atexit.register`
suppressed and `_force_exit` replaced by an event setter so that a
backstop timer cannot call `os._exit` inside the test process.

`test_run_returns_and_shuts_down_once` runs `run()` in a thread with
`start()` stubbed, sleeps 50 ms so the loop has reached its `wait`
before signalling — exercising the wake-up rather than the pre-loop
test — and asserts return within 1.0 s with exactly one `shutdown()`
call.

### 4.2 `tests/test_transport_heartbeat.py` — 5 tests

Covers items 6–8. A `_StubTransport` subclass of `OBDTransport` scripts
`connect()`'s return sequence; the four handle primitives are never
reached and are not supplied, which the class permits by design. The
stub sets `_shutdown` if its script runs dry, so a defect cannot produce
an unbounded loop.

| Test | Prompt item |
|---|---|
| `test_signature_defaults_to_none` | item 8 / success criterion |
| `test_invoked_on_both_iterations` | item 6 |
| `test_raising_heartbeat_does_not_break_the_loop` | item 7 |
| `test_no_heartbeat_argument_behaves_as_before` | item 8 |
| `test_shutdown_before_entry_skips_the_loop` | boundary |

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

No `venv/` exists in the working tree and the interpreter has none of
the project's dependencies installed. A throwaway virtualenv was built
in the session scratchpad with `pytest`, `pytest-cov`, `pygame`,
`pyserial`, `pyyaml` and `psutil`, and the package installed with
`pip install -e .`. The scratchpad venv is outside the repository and
nothing about it was committed. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt` as a side effect; that file was
restored with `git checkout` and the working tree contains only the four
edited sources and the two new test files.

```
$ pytest tests/
34 passed, 1 warning in 2.89s
```

The 19 pre-existing tests (`tests/display/rendering/test_engine.py`,
`tests/utils/test_rwlock.py`) pass unchanged alongside the 15 new ones.

`ast.parse` succeeded on all four edited sources and both new test
files.

Note for future sessions: `pytest` must be run without
`-p no:cacheprovider`. `pyproject.toml` sets both `--strict-config` and
`cache_dir`, and disabling the cache plugin makes `cache_dir` an unknown
option, which under `--strict-config` aborts the run after collection
with a misleading "collected N items" and no results.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

All fourteen criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | `shutdown_callback=self._watchdog_shutdown`; no match for `shutdown_callback=self.shutdown` | ✅ grep returns nothing |
| 2 | `_stop_event` assigned before `_watchdog` | ✅ line 51 before line 54 |
| 3 | `_watchdog_shutdown` sets the event, starts a daemon Timer, calls no `shutdown()` | ✅ |
| 4 | `_force_exit` exists and calls `os._exit(1)` | ✅ |
| 5 | `_EXIT_BACKSTOP_SEC == 20.0` | ✅ asserted in test |
| 6 | No executable `faulthandler` occurrence in `src/gtach/app.py` | ✅ grep over `src/` finds it only in `main.py` |
| 7 | `main.py` defines `_STACKS_LOG` and arms the dump only when `debug` | ✅ |
| 8 | `reconnect_indefinitely` accepts `heartbeat=None`; no-arg call unchanged | ✅ two tests |
| 9 | Both `name='transport'` sites preceded by `register_thread` and pass a heartbeat | ✅ lines 356–363, 400–407 |
| 10 | `critical_threads == {'display'}`, `advisory_threads == {'transport'}` | ✅ asserted in test |
| 11 | Advisory thread past `critical_timeout` warns, never reaches `_handle_critical_timeout` or `_attempt_hard_recovery` | ✅ asserted in test |
| 12 | No `gtach.core` import in `src/gtach/comm/transport.py` | ✅ |
| 13 | `bin/gtach.service` and `src/gtach/comm/rfcomm.py` byte-identical | ✅ absent from `git status` |
| 14 | `pytest tests/` passes | ✅ 34 passed |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

One, and it is a test-harness accommodation rather than a change to the
specified behaviour.

`TerminalRestorer` is stubbed in the `app` fixture. Its constructor
calls `os.isatty(sys.stdin.fileno())`, and pytest's capture replaces
`sys.stdin` with a pseudofile whose `fileno()` raises
`io.UnsupportedOperation`, so constructing a real `GTachApplication`
under pytest fails before reaching anything under test. The stub is
confined to the fixture; no source was changed for it. This is a
pre-existing property of `TerminalRestorer` under pytest, not a
consequence of this change, and nothing in this prompt's scope touches
the terminal.

Two additions beyond the eight specified unit-test scenarios, both
directly asserting success criteria the prompt lists but does not
allocate to a test: `test_backstop_delay_is_twenty_seconds` (criterion
5) and `test_membership` (criterion 10). Plus
`test_shutdown_before_entry_skips_the_loop` as a boundary on the
reconnect loop.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Findings Requiring Decision

None arising from the implementation. Two observations recorded for the
human verification step, neither of which is in scope here:

1. `_force_exit` reaches `os._exit(1)` unconditionally, which bypasses
   `TerminalRestorer`'s atexit handler. On the Pi target under systemd
   this is correct — there is no terminal to restore and the whole point
   is that nothing can hold the process open. On a `--macos` development
   run with the backstop firing, the terminal would be left in whatever
   state pygame left it. The prompt specifies `os._exit(1)`
   unconditionally and it was implemented as specified.

2. `register_thread` returns early with a warning when a stale
   `'transport'` entry is still RUNNING, which the prompt anticipates as
   edge case 3. In that case the thread starts and the reconnect loop
   functions, but `update_heartbeat('transport')` then refreshes the
   stale entry rather than a new one. Since `'transport'` is advisory,
   the worst outcome is a suppressed warning — no recovery or shutdown
   can be triggered either way. No test was written for this because it
   requires driving `_start_obd` twice against a live thread manager,
   which is integration rather than unit scope.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes section:

1. Start with no reachable ELM327 emulator or Bluetooth adapter, wait
   through one failed connect cycle, and confirm `systemctl status
   gtach` reports a NEW main PID and that `systemctl show gtach -p
   NRestarts` has incremented.
2. Repeat with `--debug` and confirm `/opt/gtach/stacks.log` contains
   dumps timestamped inside the stall window, listing every thread's
   stack.

The second is the evidence needed to identify the cause of the ~52 s
process-wide thread stall, which this prompt deliberately does not
attempt to fix. `issue-2ac1c602` and `change-2ac1c602` remain active
pending those results.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-2ac1c602 iteration 1: five edits across app.py, main.py, watchdog.py and transport.py, plus two unit test modules totalling 15 tests. All fourteen success criteria verified. Prompt T-Doc closed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
