Created: 2026 August 12

# Report: Set a Cause on Link Drop and Escalate to a Wedge Diagnosis

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
- [9.0 Commit Record](<#9.0 commit record>)
- [10.0 Work Remaining](<#10.0 work remaining>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records the implementation of
`prompt-5e7a03c4-cause-on-drop-and-wedge-escalation.md` (iteration 2,
coupled to `change-5e7a03c4` iteration 2 and `issue-5e7a03c4`).

Iteration 1 populated `last_failure_cause` from `connect()` alone, which
left the DISCONNECTED screen with no explanation in exactly the
mid-session failure mode `change-9c2f41d8` exists to handle. The adapter
probe detected an absent controller but not a wedged one. And an
errno-less timeout produced `timed out (timed out)`. This iteration
closes all three.

The first two of those were raised as findings 1 and 2 in the iteration
1 report; the third was not spotted then.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT R — set a cause in `drop_link` | ✅ Applied |
| EDIT S — consecutive connect-failure escalation | ✅ Applied |
| EDIT T — suppress the duplicated suffix | ✅ Applied |
| `tests/test_connect_error_classification.py` extended | ✅ 21 tests added, existing 29 unmodified |
| `pytest tests/` | ✅ 189 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

All three edits are in `src/gtach/comm/transport.py`. No other source
file was modified: `src/gtach/display/manager.py`, `src/gtach/app.py`,
`src/gtach/comm/rfcomm.py`, `src/gtach/comm/obd.py` and
`src/gtach/core/watchdog.py` are absent from `git status` entirely.

**This remains a reporting change.** No adapter reset, rfkill cycle,
hciuart restart, module reload or reboot exists on any code path, and no
`subprocess`, `os.system`, `os.popen`, `ioctl` or Bluetooth tool
invocation was introduced. The only occurrence of any of those words in
`transport.py` is a docstring line stating what the module does not do.
The HCI_UP ioctl was not used, per the constraint; consecutive-failure
escalation is the mechanism.

`disconnect()`, `reconnect_indefinitely` and `send_command`'s
consecutive-timeout logic do not appear in the diff, and
`_MAX_CONSECUTIVE_TIMEOUTS` is unchanged at 5.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT R — a cause on link drop

`_SILENT_LINK_CAUSE = 'adapter stopped responding'` added at module
level (transport.py:66), 26 characters.

`drop_link`'s signature is now
`(self, cause: Optional[str] = None) -> None`. Both existing call sites
pass nothing and are unchanged — `test_no_argument_call_sites_still_work`
asserts the default and exercises a no-argument call. The optional
argument exists so a future caller with better information can supply
its own without touching those sites; no such caller was added.

`self._last_failure_cause = cause or _SILENT_LINK_CAUSE` was added
inside the method's existing `with self._lock:` block, alongside the
existing `_state` assignment. No second lock acquisition was introduced
and `_discard_handle_locked()` was not moved —
`test_single_lock_acquisition` asserts the block count is exactly one.

`drop_link` still contains no reference to `_shutdown` in its executable
body. This was verified by AST rather than by grep, because the
docstring names `_shutdown` in order to explain the distinction from
`disconnect()` that iteration 1 established.

### 3.2 EDIT S — wedge escalation

`_WEDGED_LINK_CAUSE = 'bluetooth wedged - reset required'` added at
module level (transport.py:72), 32 characters.

`_MAX_CONSECUTIVE_CONNECT_FAILURES: int = 6` added as a class constant
(transport.py:189), commented with its basis: at the 5.0 s retry
interval that is ~30 s of sustained failure, above any transient and
below the point an operator would reasonably keep waiting.

`self._consecutive_connect_failures = 0` added to `__init__`
(transport.py:207), reset on the success path beside the existing
`_last_failure_cause = None` (transport.py:345).

The comment on the new constant states explicitly that it is separate
from `_MAX_CONSECUTIVE_TIMEOUTS`, which counts read timeouts on an
established link, and that merging them would make either one's tuning
change the other's behaviour. `TestCountersAreIndependent` asserts the
separation behaviourally: it drives five read timeouts to the point of
a `drop_link` and confirms `_consecutive_connect_failures` is still 0.

In the `_IO_ERRORS` handler the counter is incremented under `_lock` and
its value captured, the cause is resolved as before, and the escalation
applies when all three of these hold: the count is at or above the
threshold, the resolved cause is not already `'no bluetooth
controller'`, and `_bluetooth_adapter_present()` is True. The probe is
called outside the lock because it touches the filesystem.

The adapter-present condition is load-bearing. If the controller is
genuinely absent, that is the more specific fact and must not be masked
— `test_absent_adapter_is_not_masked` and
`test_adapter_becoming_absent_mid_run` both assert it, the second
flipping the probe's answer partway through a failure run.

The counter is **not** reset on crossing the threshold. It latches: the
condition persists until a connect succeeds, and the cause should keep
reporting it. `test_counter_latches_beyond_the_threshold` drives eight
failures and asserts both the cause and the raw count. This is the
opposite of the read-timeout counter's behaviour, which resets on trip —
deliberately, and the comment says so.

### 3.3 EDIT T — suffix suppression

The `_IO_ERRORS` handler now appends the parenthesised cause only when
`cause != str(e)`, logging the iteration-0 message unchanged when they
are equal. An errno-less `socket.timeout` falls through
`_classify_connect_error` to `str(exc)`, which is what produced
`timed out (timed out)`.

This is presentation only. `self._last_failure_cause` is set to the
resolved cause in both branches, because the display has no other
source for it — `test_no_suffix_when_the_cause_duplicates_the_exception`
asserts both the clean log line and the recorded cause.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_connect_error_classification.py` extended by 21 tests,
covering all thirteen `testing.unit_tests` scenarios and all three edge
cases. The 29 iteration 1 tests are unmodified; the new material is
appended below a marker comment recording that boundary.

| Test | Prompt item |
|---|---|
| `test_default_cause_on_a_connected_transport` | item 1 |
| `test_explicit_cause_is_used` | item 2 |
| `test_no_argument_call_sites_still_work` | item 3, criterion 1 |
| `test_when_already_disconnected` | edge case 1 |
| `test_single_lock_acquisition` | criterion 2 |
| `test_still_never_touches_shutdown` | criterion 3 |
| `test_threshold_constant` | criterion 4 |
| `test_counter_starts_at_zero` | criterion 4 |
| `test_five_failures_do_not_escalate` | item 4 |
| `test_six_failures_escalate` | item 5 |
| `test_counter_latches_beyond_the_threshold` | item 6, criterion 7 |
| `test_absent_adapter_is_not_masked` | item 7, criterion 6 |
| `test_adapter_becoming_absent_mid_run` | edge case 3 |
| `test_success_resets_the_counter` | item 8 |
| `test_success_clears_cause_and_counter` | item 9, edge case 2 |
| `test_read_timeouts_do_not_touch_the_connect_counter` | item 10, criterion 5 |
| `test_attributes_are_distinct` | criterion 5 |
| `test_timeout_threshold_unchanged` | criterion 10 |
| `test_no_suffix_when_the_cause_duplicates_the_exception` | item 11 |
| `test_suffix_present_when_the_cause_adds_information` | item 12 |
| `test_all_causes_within_forty_characters` | item 13, criterion 9 |

Two harness notes:

**The counter-independence test drives the real `send_command`.** A
`_TimeoutStub` subclass supplies the read primitives and raises a
timeout from `_read`, so the five-timeout path runs end to end through
`change-9c2f41d8`'s logic, `drop_link` is observed being called exactly
once, and the connect counter is then asserted still zero. That is a
stronger claim than checking the two attribute names differ, which
`test_attributes_are_distinct` covers separately.

**`_shutdown` absence is asserted over an AST-derived body.** A helper
strips the docstring and comments before the check, because iteration
1's docstring deliberately names `_shutdown` to explain why `drop_link`
must not touch it. A naive `grep` would either fail on the prose or, if
loosened, stop detecting the regression it exists to catch. The same
class of mistake cost two iterations on the previous two prompts; here
it was anticipated.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

As in the seven preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt`; that file was restored with
`git checkout`.

```
$ pytest tests/
189 passed, 1 warning in 11.29s
```

Passed on the first run. The 168 tests standing at the end of
`prompt-4f1e82b7` pass alongside the 21 new ones.

`ast.parse` succeeded on `src/gtach/comm/transport.py`.

Byte-identity and structural claims were checked mechanically:

```
$ git diff src/gtach/comm/transport.py | grep -c "def disconnect"              → 0
$ git diff src/gtach/comm/transport.py | grep -c "def reconnect_indefinitely"  → 0
$ git status --porcelain src/gtach/display/ src/gtach/core/                    → empty
$ ast: drop_link body 'with self._lock:' count                                 → 1
$ ast: '_shutdown' in drop_link executable body                                → False
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

All twelve criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | `drop_link(self, cause=None)`; no-argument call sites still work | ✅ transport.py:402, asserted by test |
| 2 | Cause set in the existing single `_lock` block | ✅ AST-verified count of 1 |
| 3 | `drop_link` still contains no `_shutdown` reference | ✅ AST-verified over the body |
| 4 | `_MAX_CONSECUTIVE_CONNECT_FAILURES == 6`; counter initialised to 0 | ✅ transport.py:189, 207 |
| 5 | The two counters are distinct; neither assigned from the other | ✅ two tests |
| 6 | Wedge cause not applied when the adapter is absent | ✅ two tests |
| 7 | Connect counter not reset on crossing its threshold | ✅ asserted on the raw count |
| 8 | Suffix appended only when it differs from `str(e)` | ✅ two tests |
| 9 | All cause strings ≤ 40 characters | ✅ asserted over the whole set |
| 10 | `disconnect()`, `reconnect_indefinitely`, timeout handling, `_MAX_CONSECUTIVE_TIMEOUTS` unchanged | ✅ absent from the diff |
| 11 | `manager.py`, `app.py`, `rfcomm.py`, `obd.py`, `watchdog.py` byte-identical | ✅ absent from `git status` |
| 12 | `pytest tests/` passes | ✅ 189 passed |

The `validation` section's repo-wide grep — now also including `ioctl` —
carries the same caveat recorded at length in the iteration 1 report §7:
`comm/system_bluetooth.py`, `utils/platform.py`, `utils/dependencies.py`
and `utils/terminal.py` have pre-existing matches, none of them a
recovery action and none introduced by either iteration. The scoped
enforcement tests from iteration 1 still pass over the edited files.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

None. EDITs R, S and T were applied as specified, all thirteen unit-test
scenarios and all three edge cases were implemented, and the 29
iteration 1 tests pass unmodified as required.

Eight tests were added beyond the thirteen scenarios, each asserting a
success criterion the prompt lists but does not allocate to a scenario:
`test_when_already_disconnected`, `test_single_lock_acquisition`,
`test_still_never_touches_shutdown`, `test_threshold_constant`,
`test_counter_starts_at_zero`, `test_adapter_becoming_absent_mid_run`,
`test_attributes_are_distinct` and `test_timeout_threshold_unchanged`.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Findings Requiring Decision

Three, none blocking.

1. **The wedge diagnosis names a reset the application cannot perform,
   and the operator currently has no way to perform either.**
   `'bluetooth wedged - reset required'` tells the operator what is
   wrong and implies an action, but the reset button is a separate
   triple and is itself blocked on establishing a recovery command that
   works on this hardware. Until that lands, the screen will state a
   required action with no affordance for it. That is still strictly
   better than the silence it replaces, and the prompt is explicit that
   the button is out of scope — but the gap is worth holding in view,
   because a diagnosis the operator cannot act on invites a power cycle.

2. **Escalation is time-blind: it counts attempts, not elapsed time.**
   Six failures is ~30 s only while the retry cadence is the 5.0 s
   default. `reconnect_indefinitely` waits `retry_delay` between
   attempts and also after a link drop, so a future configured cadence
   would silently rescale the escalation window without the constant
   changing. Counting attempts is the simpler and more testable choice
   and matches what the prompt specified; recorded so that if the retry
   interval ever becomes configurable, this constant is revisited with
   it. Note this now couples to `prompt-4f1e82b7`'s
   `_retry_interval_callback`, which anticipates exactly such a
   configured value.

3. **A `drop_link` cause outlives the condition that set it.** The cause
   clears only on a successful connect. After a drop for silence, every
   subsequent failed connect overwrites it with a connect cause, which
   is correct — but if `connect()` never runs again for some reason, the
   screen keeps showing `'adapter stopped responding'` indefinitely.
   That is accurate rather than misleading, and the retry-countdown arc
   delivered by `change-4f1e82b7` now independently tells the operator
   whether the application is alive, which is the more important half of
   what a stale line could otherwise obscure.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Commit Record

Committed and pushed as a single commit containing
`src/gtach/comm/transport.py`, the extended
`tests/test_connect_error_classification.py`, this report and the prompt
T-Doc closure move.

Not included, and left uncommitted in the working tree: `.gitignore`,
`CLAUDE.md`, the `change-2ac1c602` and `issue-2ac1c602` modifications,
and the untracked `change-7d4e91a3` and `issue-7d4e91a3` T-Docs. These
are authoring work belonging to the user, not this prompt's deliverable.
The `change-5e7a03c4` and `issue-5e7a03c4` T-Docs for this triple were
already committed and remain active.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes:

1. With the emulator running, stop it mid-session and confirm the
   DISCONNECTED screen now shows a cause naming that the adapter stopped
   responding, where before it showed none.
2. Leave GTach failing to connect for ~30 s and confirm the cause
   escalates to the wedge diagnosis.
3. Restore the link and confirm the cause clears.

Two things remain outside this prompt. The DISCONNECTED screen redesign
was its own triple and has since been delivered as `change-4f1e82b7`, so
step 1's cause line will appear on the redesigned screen alongside the
retry-countdown arc — worth knowing when reading it, since the two
changes land together on target. An operator-initiated Bluetooth reset
button is a third triple, still blocked until a recovery command that
works on this hardware is established: `hciconfig hci0 down && up` was
tried on target and left the controller unable to come back. See §8
finding 1.

`issue-5e7a03c4` and `change-5e7a03c4` remain active pending the three
steps above.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-5e7a03c4 iteration 2: a cause recorded on drop_link, a separate latching connect-failure counter escalating to a wedge diagnosis at six consecutive failures, and suppression of the duplicated cause suffix. 21 tests added to the existing module, whose 29 iteration 1 tests pass unmodified. All twelve success criteria verified, no deviations. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
