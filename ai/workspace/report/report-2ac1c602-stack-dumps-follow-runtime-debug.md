Created: 2026 August 12

# Report: Arm Stack Dumps From the Runtime Debug Toggle

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

Records the implementation of
`prompt-2ac1c602-stack-dumps-follow-runtime-debug.md` (iteration 2,
coupled to `change-2ac1c602` iteration 2 and
`issue-2ac1c602`).

Iteration 1 armed faulthandler inside `setup_logging`, gated on that
function's `debug` argument, which derives from the `--debug`
command-line flag. `bin/gtach.service`'s ExecStart passes no such flag,
so `args.debug` is False on every service-launched run and the arming
was never reached — no `stacks.log` appeared on the 2026-08-12 09:11
verification run. This iteration moves the trigger onto the signal that
actually enables debug in the field: the OPTIONS screen toggle.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc, and
leave the issue and change T-Docs active pending test results.

| Item | Outcome |
|---|---|
| EDIT G — `main.py`, idempotent arm/disarm helpers | ✅ Applied |
| EDIT H — `app.py`, drive the helpers from the runtime toggle | ✅ Applied |
| `tests/test_stack_dump_toggle.py` | ✅ Created, 22 tests |
| `pytest tests/` | ✅ 56 passed, 0 failed |

`prompt-2ac1c602-stack-dumps-follow-runtime-debug.md` moved to
`ai/workspace/prompt/closed/`. The issue and change T-Docs remain
active, as instructed. No T06 result document was created.

No new modules and no new third-party dependencies. `bin/gtach.service`
is untouched; `--debug` was explicitly **not** added there, per the
constraint — doing so would make debug logging permanent in production
and write a full all-thread dump every 15 s for the life of every run.
`src/gtach/core/watchdog.py` and `src/gtach/comm/transport.py` are
byte-identical to their post-iteration-1 state, and every `app.py` diff
hunk falls inside `toggle_debug_logging`.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT G — `src/gtach/main.py`

Two module-level functions added after `setup_logging`.

`enable_stack_dumps() -> bool` (main.py:103) declares `global
_stacks_file` and returns `True` immediately when `_stacks_file` is not
`None` — already armed, no second handle, no second timer. Otherwise it
opens `_STACKS_LOG` with `mode='a'`, `buffering=1`,
`encoding='utf-8'`, assigns `_stacks_file`, calls
`faulthandler.enable(file=...)` and
`faulthandler.dump_traceback_later(15, repeat=True, file=...)`, and
returns `True`. On `OSError` it prints the existing style of warning to
`sys.stderr`, leaves `_stacks_file` as `None`, and returns `False`.

`disable_stack_dumps() -> None` (main.py:150) declares `global
_stacks_file` and returns immediately when nothing is armed. Otherwise
it calls `faulthandler.cancel_dump_traceback_later()`, then
`faulthandler.disable()`, then closes `_stacks_file` inside a
`try/except`, then sets `_stacks_file = None`. The order is as
specified and is load-bearing: cancelling the timer and disabling
faulthandler must precede the close, or a dump can fire against a closed
descriptor. `_stacks_file` is cleared even when the close raises, so a
failed close cannot permanently block re-arming.

The `if debug:` block in `setup_logging` is now a single guarded call to
`enable_stack_dumps()`. The explanatory comment moved onto
`enable_stack_dumps`'s docstring and was extended to record why arming
is no longer reached only from there: `bin/gtach.service` passes no
`--debug`, so the startup path is not the path that matters in
production.

The docstring also records the thread-safety position: faulthandler's
own calls are safe, and `_stacks_file` — the only shared state —
transitions by single assignment, so both helpers are safe to call from
a thread other than the one that ran `setup_logging`. The OPTIONS toggle
runs on the display thread, so this is exercised in practice.

### 3.2 EDIT H — `src/gtach/app.py`

`GTachApplication.toggle_debug_logging` retains every existing line: the
linux platform guard, the `sys.modules.get('gtach.main')` retrieval
established by `issue-c1d4b8e6`, both `None` checks, both
`_debug_handler` level changes and both INFO log lines.

The `if enable:` branch now calls `enable_stack_dumps` after its level
change and INFO log; the `else:` branch calls `disable_stack_dumps`
after its own. Each sits in its own `try/except Exception` logging at
DEBUG with `exc_info=True`, so a failure to arm or disarm cannot prevent
the debug log handler from being toggled — the operator's primary
diagnostic control. Access is via `getattr(_main, '<name>', None)` with
a `None` check, so a partially loaded or older `gtach.main` cannot raise
`AttributeError` out of the method.

The docstring was updated: it previously described only `debug.log`, and
now records that the same signal arms and disarms stack dumps, that this
is the signal that turns debug on in the field, and that the two
diagnostics degrade independently.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_stack_dump_toggle.py` — 22 tests covering all twelve
`testing.unit_tests` scenarios plus the three listed edge cases and four
constraint assertions.

| Test | Prompt item |
|---|---|
| `test_arms_once` | item 1 |
| `test_dump_interval_is_fifteen_seconds_repeating` | success criterion 7 |
| `test_second_call_opens_no_second_handle` | item 2 |
| `test_unwritable_path_returns_false` | item 6 |
| `test_closes_file_and_clears_state` | item 3 |
| `test_cancels_before_closing` | success criterion 6 |
| `test_no_op_when_not_armed` | item 4 |
| `test_close_failure_still_clears_state` | error_handling |
| `test_enable_disable_enable_rearms` | item 5 |
| `test_off_on_off` | edge case 2 |
| `test_debug_false_does_not_arm` | item 7 |
| `test_debug_true_arms_exactly_once` | item 8 |
| `test_no_direct_faulthandler_call_in_setup_logging` | success criterion 2 |
| `test_enable_sets_level_and_arms` | item 9 |
| `test_disable_raises_level_and_disarms` | item 10 |
| `test_arming_failure_does_not_block_the_handler` | item 11 |
| `test_disarming_failure_does_not_block_the_handler` | item 11 (disable side) |
| `test_missing_helper_is_not_an_attribute_error` | item 12 |
| `test_non_linux_returns_before_any_stack_dump_call` | edge case 3 |
| `test_second_arming_is_a_no_op` | edge case 1 |
| `test_stacks_log_path` | success criterion 7 |
| `test_exit_backstop_unchanged` | success criterion 10 |

Three deliberate choices in the harness:

**faulthandler is replaced by a recording double.** Arming the real one
would start a 15 s repeating timer writing into the test process for the
remainder of the run, and the teardown *order* that
`disable_stack_dumps` must observe — cancel and disable before close —
is only assertable against a recorder. `test_cancels_before_closing`
wraps the file handle's `close` to record its position in the call
sequence and asserts it falls after both.

**The module is fetched from `sys.modules`, not imported.**
`gtach/__init__.py` re-exports the `main` *function* under the name
`main`, so `from gtach import main` retrieves the function, whose
namespace has no `_stacks_file` or `_STACKS_LOG`. This is the trap
`issue-c1d4b8e6` documents and the reason `toggle_debug_logging` reaches
for `sys.modules` itself. The first run of this suite failed on exactly
that, which is a useful confirmation that the trap is still live.

**`toggle_debug_logging` is called unbound against a minimal host.** The
method uses only `self.logger`, so the tests pass a
`SimpleNamespace` rather than constructing a full `GTachApplication`.
`sys.platform` is patched to `'linux'` because the method early-returns
off linux and the suite runs on macOS.

A module-level fixture resets `_stacks_file` to `None` on the way out of
every test, so one test's armed handle cannot leak into the next.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

As in iteration 1, no `venv/` exists in the working tree and the
interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt` as a side effect; that file was
restored with `git checkout`.

```
$ pytest tests/
56 passed, 1 warning in 2.95s
```

The 34 tests standing at the end of iteration 1 pass unchanged alongside
the 22 new ones.

`ast.parse` succeeded on both edited sources and the new test file.

`git diff -U0 src/gtach/app.py` produces four hunks, all inside
`toggle_debug_logging` (lines 209–267). `_watchdog_shutdown`,
`_force_exit`, `_EXIT_BACKSTOP_SEC`, the `WatchdogMonitor` construction
and the transport registration are untouched, and
`src/gtach/core/watchdog.py`, `src/gtach/comm/transport.py` and
`bin/gtach.service` do not appear in `git status` at all.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

All eleven criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | `main.py` defines `enable_stack_dumps` and `disable_stack_dumps` | ✅ lines 103, 150 |
| 2 | `setup_logging` contains no direct `faulthandler.dump_traceback_later`; it appears only in `enable_stack_dumps` | ✅ asserted by test over `inspect.getsource` |
| 3 | `setup_logging` calls `enable_stack_dumps()` iff `debug` is truthy | ✅ two tests |
| 4 | `toggle_debug_logging` calls each helper on its branch, each inside its own guard | ✅ app.py:245–267 |
| 5 | Two `enable_stack_dumps` calls open no second file object | ✅ asserted by identity of `_stacks_file` |
| 6 | `cancel_dump_traceback_later` precedes the close | ✅ asserted by call-order recorder |
| 7 | `_STACKS_LOG == '/opt/gtach/stacks.log'`; interval still `15`, `repeat=True` | ✅ two tests |
| 8 | `bin/gtach.service` byte-identical; `grep -n 'debug'` returns no match | ✅ |
| 9 | `watchdog.py` and `transport.py` byte-identical to post-iteration-1 | ✅ absent from `git status` |
| 10 | `_watchdog_shutdown`, `_force_exit`, `_EXIT_BACKSTOP_SEC` unchanged | ✅ diff hunks confined to `toggle_debug_logging` |
| 11 | `pytest tests/` passes | ✅ 56 passed |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

One, small and confined to the block being replaced.

`setup_logging`'s `global` statement was reduced from
`global _start_handler, _debug_handler, _stacks_file` back to
`global _start_handler, _debug_handler`. Iteration 1 added `_stacks_file`
to that statement because the arming block assigned it; EDIT G moves
that assignment into `enable_stack_dumps`, leaving the declaration
naming a variable the function no longer touches. The prompt specifies
replacing the block but says nothing about the `global`. Removing it is
debris-clearing from the exact block under replacement rather than a
behavioural change — a `global` declaration with no assignment in scope
is a no-op that misleads a reader into thinking `setup_logging` still
owns the handle.

Beyond that, this report was written to
`ai/workspace/report/report-2ac1c602-stack-dumps-follow-runtime-debug.md`
rather than the `ai/workspace/report-…` path given in the instruction,
matching where the iteration 1 report now lives and the path this
prompt's own `knowledge_references` cite.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Findings Requiring Decision

Two, both about coverage this change does not extend and neither
blocking.

1. **The `--debug` startup path and the OPTIONS path now converge on the
   same guard, but only the OPTIONS path disarms.** Nothing calls
   `disable_stack_dumps` on shutdown. The handle is closed by
   interpreter exit, and `_force_exit`'s `os._exit(1)` bypasses that —
   but `buffering=1` means every dump is already flushed line by line,
   so no dump content is lost either way. Adding a disarm to
   `GTachApplication.shutdown` was not specified and was not done.

2. **`stacks.log` is not rotated and has no size cap**, unlike
   `debug.log`, which `main.py` rotates at start with ten backups. A
   full all-thread dump every 15 s with debug left on indefinitely will
   grow the file without bound on a card-backed filesystem. In the
   intended use — enable via OPTIONS, reproduce the stall, disable —
   this does not arise, and the prompt neither specifies rotation nor
   permits changing `_STACKS_LOG`. Worth a decision if the toggle is
   ever left on for a long field session.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes section.
After deployment with no reachable OBD transport:

1. Confirm `/opt/gtach/stacks.log` does **not** exist at startup.
2. Enable debug through the OPTIONS toggle; confirm the file appears and
   gains an all-thread dump roughly every 15 s.
3. Disable debug; confirm dumps stop.
4. Re-enable; confirm they resume.

The purpose of this edit is to make the ~52 s process-wide stall
observable. That stall did not recur on the 2026-08-12 09:11 run, so
both it and the process-termination path delivered by iteration 1 remain
unverified on target. Neither `issue-2ac1c602` nor `change-2ac1c602`
should be closed on this prompt alone; both remain active.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-2ac1c602 iteration 2: enable_stack_dumps/disable_stack_dumps extracted into main.py and driven from GTachApplication.toggle_debug_logging, plus 22 unit tests. All eleven success criteria verified. Prompt T-Doc closed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
