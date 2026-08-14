Created: 2026 August 12

# Report: Detect a Dead Link and Reconnect for the Life of the Process

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Edits Applied](<#3.0 edits applied>)
- [4.0 Tests Added](<#4.0 tests added>)
- [5.0 Existing Test Module Updated](<#5.0 existing test module updated>)
- [6.0 Verification Method](<#6.0 verification method>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Deviations from the Prompt Specification](<#8.0 deviations from the prompt specification>)
- [9.0 Findings Requiring Decision](<#9.0 findings requiring decision>)
- [10.0 Commit Record](<#10.0 commit record>)
- [11.0 Work Remaining](<#11.0 work remaining>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records the implementation of `prompt-9c2f41d8-link-loss-recovery.md`
(iteration 1, coupled to `change-9c2f41d8` and `issue-9c2f41d8`).

A read timeout left the transport reporting connected against a dead
peer, so `OBDProtocol` polled a closed-at-the-far-end socket at ~1 Hz
indefinitely (38 consecutive occurrences observed), and
`reconnect_indefinitely` was never re-entered because its only two call
sites are at startup in threads that returned on first success. This
change makes `is_connected()` tell the truth and makes the reconnect
loop live for the life of the process.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT L — consecutive read-timeout thresholding in `send_command` | ✅ Applied |
| EDIT M — `drop_link`, teardown that does not end the transport | ✅ Applied |
| EDIT N — `reconnect_indefinitely` as a supervising loop | ✅ Applied |
| `tests/test_link_loss_recovery.py` | ✅ Created, 23 tests |
| `tests/test_transport_heartbeat.py` | ⚠️ Updated — see §5 |
| `pytest tests/` | ✅ 115 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

All three source edits are in `src/gtach/comm/transport.py`. No other
source file was modified: `src/gtach/comm/obd.py`,
`src/gtach/comm/rfcomm.py`, `src/gtach/app.py` and
`src/gtach/core/watchdog.py` are byte-identical to their pre-change
state, as is `disconnect()`, which does not appear in the diff.

**The prompt's critical constraint is satisfied and is now enforced by
test.** `disconnect()` is not used to tear down a dead link, and
`_shutdown` is set in exactly one place. `grep -n '_shutdown.set()'`
returns a single match, at transport.py:237, inside `disconnect()`.
`drop_link`'s executable body contains no reference to `_shutdown` at
all, asserted by `test_drop_link_source_never_touches_shutdown`, and
three behavioural tests assert `_shutdown.is_set() is False` after a
link drop — the check that distinguishes a correct implementation from
one that merely makes the transport go not-connected while permanently
disabling reconnection.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT L — consecutive read-timeout thresholding

`_MAX_CONSECUTIVE_TIMEOUTS: int = 5` added as a class-level constant on
`OBDTransport` (transport.py:114), commented against the observed
timings: a command timeout is 1.0 s and the observed failure cycled at
~1.07 s, so the threshold trips at ~5.4 s — above any single slow
adapter response, below `WatchdogMonitor`'s 15 s warning threshold, so
the link is dropped and reconnection under way before the watchdog has
anything to say about it.

`self._consecutive_timeouts = 0` added to `__init__` (transport.py:131).

On the success path, immediately before `return response` and after the
RX debug log, the counter is reset to 0 under `self._lock`
(transport.py:323). Any answer at all means the peer is alive, so an
occasional slow response never accumulates towards a drop.

In the `except self._TIMEOUT_ERRORS:` branch the existing warning is
retained, then under `self._lock` the counter is incremented and the
trip decision captured. When the threshold is reached the counter is
reset **under the same lock that observed the trip**, so a sixth timeout
cannot drop the link a second time. An ERROR naming the count and the
endpoint via `self._describe()` is logged, then `drop_link()` is called
**outside** the lock — `drop_link` takes `_lock` itself, so the decision
is captured under the lock and acted on after releasing it. `None` is
returned as before.

The except ordering is unchanged: `_TIMEOUT_ERRORS` still precedes
`_IO_ERRORS`, `socket.timeout` being an `OSError` subclass. This is
asserted by `test_timeout_branch_precedes_io_branch`.

### 3.2 EDIT M — `drop_link`

Added immediately after `disconnect()` (transport.py:243) so the two are
read together. It takes `self._lock`, calls `_discard_handle_locked()`,
sets `_state = TransportState.DISCONNECTED`, and logs at INFO that the
link to `self._describe()` was dropped and reconnection will be
attempted. It does not touch `_shutdown`.

The docstring states the distinction explicitly and at length, because
it is the one thing about this change that must not be collapsed by a
later edit: `disconnect()` ends the transport's life and sets the event
`reconnect_indefinitely` loops on and waits on, which nothing ever
clears; `drop_link()` closes only the current link so the supervising
loop can re-establish it. It records that tearing a dead link down via
`disconnect()` would permanently disable reconnection while still
satisfying any check that merely asserts the transport went
not-connected, citing `issue-9c2f41d8`.

Safe to call when nothing is connected — `_discard_handle_locked`
tolerates a `None` handle — which is asserted by
`test_drop_link_when_already_disconnected`.

### 3.3 EDIT N — supervising loop

The signature is unchanged, including the `heartbeat` keyword and its
`None` default, asserted by `test_signature_is_unchanged`. The guarded
`_beat()` helper introduced by `change-2ac1c602` is retained verbatim,
so a raising callback still cannot break the loop.

The body is now:

```python
while not self._shutdown.is_set():
    _beat()
    if self.connect():
        _beat()
        while self.is_connected() and not self._shutdown.is_set():
            _beat()
            self._shutdown.wait(1.0)
        if self._shutdown.is_set():
            return
        logger.info("Link lost - resuming reconnection attempts in ...")
        self._shutdown.wait(retry_delay)
        continue
    _beat()
    logger.warning("Failed to connect, retrying in %.1f seconds...", retry_delay)
    self._shutdown.wait(retry_delay)
```

The 1.0 s supervising poll bounds how long after a `drop_link` the loop
notices, and keeps the `'transport'` heartbeat flowing while connected —
which the ThreadManager registration added by `change-2ac1c602`
requires, since without it the thread would look stalled for as long as
the link stayed healthy.

The method does not return on a successful connect. Its only return is
`_shutdown` being set, asserted structurally by
`test_no_return_reachable_while_shutdown_is_unset`, which parses the
function and checks that the single `return` inside the loop is
immediately preceded by `if self._shutdown.is_set():`.

Every wait is `self._shutdown.wait(...)`; there is no `time.sleep`
anywhere in the file outside one docstring mention.

The docstring records that the method supervises the link for the life
of the process, returns only on shutdown, and resumes retrying on a
dropped link, and why it previously could not.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_link_loss_recovery.py` — 23 tests covering all thirteen
`testing.unit_tests` scenarios and all three edge cases.

| Test | Prompt item |
|---|---|
| `test_threshold_is_five` | success criterion 1 |
| `test_counter_starts_at_zero` | success criterion 1 |
| `test_four_timeouts_then_success_does_not_drop` | item 1 |
| `test_five_timeouts_drops_the_link` | item 2 |
| `test_three_one_three_does_not_drop` | item 3 |
| `test_six_timeouts_drop_once_not_twice` | item 4 |
| `test_timeout_branch_precedes_io_branch` | edge case 2, criterion 6 |
| `test_success_resets_the_counter` | criterion 7 |
| `test_drop_link_closes_the_handle_without_shutdown` | item 5 |
| `test_drop_link_when_already_disconnected` | item 6 |
| `test_disconnect_still_sets_shutdown` | item 7 |
| `test_drop_link_source_never_touches_shutdown` | criterion 3 |
| `test_does_not_return_on_successful_connect` | item 8 |
| `test_reconnects_after_a_drop` | item 8, edge case 1 |
| `test_shutdown_while_connected_returns_promptly` | item 9 |
| `test_shutdown_while_retrying_returns_promptly` | item 10 |
| `test_no_return_reachable_while_shutdown_is_unset` | criterion 8 |
| `test_every_wait_is_on_shutdown` | criterion 9 |
| `test_signature_is_unchanged` | criterion 10 |
| `test_beats_while_connected_and_while_retrying` | item 11 |
| `test_raising_heartbeat_does_not_break_the_loop` | item 12 |
| `test_no_heartbeat_argument` | item 13 |
| `test_repeated_instant_drops_are_rate_limited` | edge case 3 |

The stub subclasses `OBDTransport` and supplies all four handle
primitives plus a scripted `_read`, overriding `_TIMEOUT_ERRORS` with a
local exception type. The timeout-threshold tests therefore drive the
real `send_command` end to end rather than calling the counter logic
directly, so the lock discipline and the except ordering are exercised
as written.

Every blocking assertion is bounded by `JOIN_TIMEOUT = 5.0`. A
regression in the supervising loop manifests as a thread that never
returns, so an unbounded join would convert a failure into a hung run
with no diagnostic.

Two source-level assertions parse the function with `ast` and strip the
docstring and comments before asserting. Both docstrings legitimately
name `_shutdown` and `time.sleep` while explaining what the code
deliberately does *not* do, and must stay free to — my first draft of
both tests failed on exactly that, which is a useful reminder that
source-text assertions must be told what is prose.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Existing Test Module Updated

`tests/test_transport_heartbeat.py` required updating, and this is worth
stating plainly rather than burying: three of its tests encoded the old
contract, in which `reconnect_indefinitely` **returns after a successful
connect**. That is precisely the behaviour this change removes. Under
the new contract those tests do not merely fail — their stub scripts end
in a successful connect, which now means the loop supervises the link
forever.

The prompt did not list this module as one that must pass unmodified —
unlike `prompt-3b8c50f2`, which named `test_stack_dump_toggle.py`
explicitly — but success criterion 12 requires `pytest tests/` to pass,
so it had to be reconciled one way or the other.

The change made is minimal: each of the three scripts changed from
`[False, True]` to `[False]`, so the run is one failed connect followed
by script exhaustion, which the stub already handled by setting
`_shutdown`. Every assertion in those tests is unchanged and still
passes, including `connect_calls == 2`. The class docstring now records
why the scripts must end in exhaustion.

What that loses is coverage of the heartbeat firing around a
*successful* connect. That is not left uncovered: it moved to
`TestSupervisingLoopHeartbeat::test_beats_while_connected_and_while_retrying`
in the new module, which asserts beats occur in both the connected and
the retrying phase — the stronger form of the same check, under the
contract that now holds. The old module's remaining subject, the
optionality and containment of the heartbeat hook, is untouched.

I have flagged this rather than treating it as routine because
"weakened an existing test until it passed" and "updated a test that
asserted behaviour the change deliberately removes" look identical in a
diff. This is the second, and §7's criterion 11 is unaffected — that
criterion lists source files only.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Verification Method

As in the four preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted.

```
$ pytest tests/
115 passed, 1 warning in 5.18s
```

The new module is timing-sensitive — it runs the supervising loop on
real threads and asserts on elapsed time — so it was run five further
times in isolation to check for flakiness:

```
$ for i in 1 2 3 4 5; do pytest tests/test_link_loss_recovery.py -q; done
23 passed  (×5, 3.15–3.17 s)
```

Stable. The timing assertions are deliberately loose: prompt exits are
asserted under 3.0 s against a 30.0 s `retry_delay`, a two-order margin
that discriminates a wait-on-`_shutdown` from a wait-on-delay without
being sensitive to scheduler jitter.

`ast.parse` succeeded on `src/gtach/comm/transport.py` and the new test
file.

`git diff src/gtach/comm/transport.py | grep -c 'def disconnect'`
returns 0, confirming `disconnect()` is untouched.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

All twelve criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | `_MAX_CONSECUTIVE_TIMEOUTS == 5`; `_consecutive_timeouts = 0` in `__init__` | ✅ transport.py:114, 131 |
| 2 | Public method `drop_link` | ✅ transport.py:243 |
| 3 | `drop_link` contains no reference to `_shutdown` | ✅ asserted over executable lines |
| 4 | `grep -n '_shutdown.set()'` returns exactly one match, inside `disconnect()` | ✅ transport.py:237 |
| 5 | `disconnect()` byte-identical | ✅ absent from the diff |
| 6 | `_TIMEOUT_ERRORS` still precedes `_IO_ERRORS` | ✅ asserted by test |
| 7 | `_consecutive_timeouts` reset to 0 on the success path | ✅ transport.py:323 |
| 8 | No `return` reachable while `_shutdown` is unset | ✅ asserted structurally via `ast` |
| 9 | Every wait uses `self._shutdown.wait(...)`; no `time.sleep` introduced | ✅ only a docstring mention |
| 10 | `reconnect_indefinitely` signature unchanged | ✅ asserted by test |
| 11 | `obd.py`, `rfcomm.py`, `app.py`, `watchdog.py` byte-identical | ✅ absent from `git status` |
| 12 | `pytest tests/` passes | ✅ 115 passed |

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Deviations from the Prompt Specification

Two, both consequences of following the prompt's own stated
requirements where its prose was less specific than its edge cases.

**1. A `retry_delay` wait was added on the link-drop path.** EDIT N's
prose says that on leaving the supervising wait "the link dropped and
control falls through to the next outer iteration, which retries",
which read alone means retrying immediately. But `edge_cases` requires
that "the loop must not busy-spin; each retry passes through
`_shutdown.wait(retry_delay)`", and `requirements.functional` item 4
requires that "after a link drop, `reconnect_indefinitely` resumes
retrying at the existing `retry_delay`". A link that dropped instantly
after every connect would spin the loop at full speed under the literal
prose. `self._shutdown.wait(retry_delay)` therefore precedes the
`continue`, satisfying both the edge case and functional item 4. Because
it waits on `_shutdown`, it costs nothing at shutdown.
`test_repeated_instant_drops_are_rate_limited` asserts it.

**2. `tests/test_transport_heartbeat.py` was modified.** Documented in
full in §5.

Beyond those, EDITs L, M and N were applied as specified, and all
thirteen unit-test scenarios plus the three edge cases were implemented.
Ten tests were added beyond the thirteen scenarios, each asserting a
success criterion the prompt lists but does not allocate to a scenario.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Findings Requiring Decision

Three, none blocking.

1. **`connect()` is still synchronous and can block for tens of
   seconds.** The supervising loop calls it on the transport thread,
   which is registered with `ThreadManager` but advisory-only in
   `WatchdogMonitor` (`change-2ac1c602`), so a long blocking connect
   produces a warning and nothing worse — which is the designed
   behaviour. But no heartbeat is emitted *during* a `connect()` call,
   only either side of it. A Bluetooth connect lasting longer than the
   watchdog's 15 s warning threshold will still log a warning for
   `'transport'` on every cycle it spans. Expected and harmless given
   the advisory tier; noted because the log line will appear on target
   and should not be mistaken for a regression.

2. **The threshold counts timeouts across all commands, not per
   command.** `_consecutive_timeouts` is a single transport-wide
   counter, which is correct for the failure being addressed — a dead
   peer answers nothing. If a future adapter were slow on one specific
   PID but healthy on others, an interleaved poll cycle would reset the
   counter on every alternate command and the threshold would never
   trip. Not a concern for the observed failure, and per-command
   tracking would be materially more complex; recorded in case the
   symptom ever presents that way.

3. **`[Errno 16] Device or resource busy` remains unaddressed**, as the
   prompt directs. It is worth noting that this change plausibly bears
   on it: the prompt's own note observes it "may prove to be a
   consequence of the abandoned socket that this change stops
   abandoning". `drop_link` now closes the handle via
   `_discard_handle_locked` on every threshold trip, where previously
   the socket was left open indefinitely. Whether that resolves the
   Errno 16 condition is exactly what the post-deployment re-examination
   should establish first, before any separate investigation is opened.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Commit Record

Committed and pushed as a single commit containing
`src/gtach/comm/transport.py`, `tests/test_link_loss_recovery.py`, the
`tests/test_transport_heartbeat.py` update, this report and the prompt
T-Doc closure move.

Not included, and left uncommitted in the working tree: `.gitignore`,
`CLAUDE.md`, the `change-2ac1c602` and `issue-2ac1c602` modifications,
and the untracked `change-7d4e91a3` and `issue-7d4e91a3` T-Docs. These
are authoring work belonging to the user, not this prompt's deliverable.
The `change-9c2f41d8` and `issue-9c2f41d8` T-Docs for this triple were
already committed and remain active and unmodified.

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes. With
GTach connected to the ELM327 emulator and debug enabled:

1. Stop the emulator; confirm that within ~5.4 s an ERROR records the
   link being dropped, that the "Timeout waiting for response"
   repetition stops, and that reconnect attempts begin at 5 s intervals.
2. Restart the emulator; confirm GTach reconnects with no operator
   action, the adapter re-initialises, and RPM resumes.
3. Shut the application down while it is reconnecting; confirm shutdown
   completes promptly with no thread-join warning.
4. Confirm no "Heartbeat for unknown thread: transport" warning appears
   across a reconnect cycle.

Then re-examine `[Errno 16] Device or resource busy`, which occurred 12
times in one log after a restart following link loss. Per §9 finding 3,
establish first whether this change has already resolved it before
opening a separate investigation.

`issue-9c2f41d8` and `change-9c2f41d8` remain active pending the four
steps above.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-9c2f41d8 iteration 1: consecutive read-timeout thresholding in send_command, drop_link, and reconnect_indefinitely as a process-lifetime supervising loop, plus 23 unit tests. All twelve success criteria verified. Two deviations recorded: a retry_delay wait on the link-drop path required by the prompt's own edge case, and an update to tests/test_transport_heartbeat.py, which encoded the superseded return-on-first-success contract. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
