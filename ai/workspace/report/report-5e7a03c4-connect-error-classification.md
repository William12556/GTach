Created: 2026 August 12

# Report: Close Failed Sockets and Report Why a Connect Failed

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
`prompt-5e7a03c4-connect-error-classification.md` (iteration 1, coupled
to `change-5e7a03c4` and `issue-5e7a03c4`).

An adapter fault and a missing OBD dongle produced identical logs and an
identical DISCONNECTED screen; establishing which it was took a full
session of manual `hcitool` work to recover information errno already
carried. The socket whose connect raised was also abandoned open,
holding its ACL reference. This change captures errno where it was being
discarded, resolves it to a named cause, surfaces that cause on the
transport and the display, and closes the failed socket.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT O — `rfcomm.py`, close the socket on failure | ✅ Applied |
| EDIT P — `transport.py`, classify by errno | ✅ Applied |
| EDIT Q — adapter probe and DISCONNECTED status line | ✅ Applied |
| `app.py` — `_link_cause_callback` wiring | ✅ Applied, and nothing else |
| `tests/test_connect_error_classification.py` | ✅ Created, 29 tests |
| `pytest tests/` | ✅ 144 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

**The critical constraint is satisfied: this change reports, it does not
act.** No adapter reset, rfkill cycle, hciuart restart, module reload or
reboot exists on any code path. No `subprocess`, `os.system`,
`os.popen` or shell invocation was introduced, and no `hcitool`,
`hciconfig`, `btmgmt` or `rfkill` output is parsed. Controller presence
comes from a single sysfs directory listing. Two tests enforce this by
scanning the four edited files with comments and string literals
blanked — see §7 for why the enforcement is scoped to those files rather
than to all of `src/`.

`reconnect_indefinitely`, `drop_link` and `disconnect` do not appear in
the `transport.py` diff. `_register_disconnected_regions` is untouched —
its two occurrences in the `manager.py` diff are both comments.
`src/gtach/comm/obd.py`, `serial_transport.py`, `tcp_transport.py` and
`src/gtach/core/watchdog.py` are absent from `git status` entirely.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT O — close the socket on failure

`sock.connect(...)` and the subsequent `sock.settimeout(None)` in
`RFCOMMTransport._open` are now wrapped in `try/except BaseException`.
The handler closes the socket inside a nested `try/except` that swallows
close errors, then bare-`raise`s so the traceback and errno are
preserved and `OBDTransport.connect`'s existing `_IO_ERRORS` handling is
unaffected.

`BaseException` rather than `Exception`, so a `KeyboardInterrupt` or a
timeout delivered as a `BaseException` still closes the socket —
asserted by `test_base_exception_also_closes`.

The success path is unchanged: the socket is returned and ownership
passes to `connect()` as before.

The comment records why nothing else did this. The socket is a local,
and `connect()`'s `_IO_ERRORS` handler calls `_discard_handle()` against
`self._handle`, which is only assigned on the success path — so on
failure it discarded `None` while the real socket leaked.

### 3.2 EDIT P — classify by errno

`import errno as _errno` and `import os` added to the module imports.

`_CONNECT_FAULT_CAUSES` added at module level (transport.py:51), mapping
the seven errno values the prompt specifies. Every value is 40
characters or fewer so it renders on the 480×480 display;
`test_every_mapped_cause_fits_the_display` asserts that bound over the
whole mapping rather than over the values the other tests happen to
touch, so a later addition cannot quietly exceed it.

`self._last_failure_cause: Optional[str] = None` added to `__init__`,
with a read-only `last_failure_cause` property returning it under
`self._lock` — the display thread reads it while the transport thread
writes it.

`_classify_connect_error(self, exc: OSError) -> str` reads
`getattr(exc, 'errno', None)`, returns the mapped string when present,
otherwise the errno name via `_errno.errorcode.get`, otherwise
`str(exc)`, otherwise a literal fallback. The whole body is wrapped so
it cannot raise for any input — `test_never_raises_for_hostile_input`
drives it with an exception whose `errno` property and `__str__` both
raise.

In `connect()`'s `_IO_ERRORS` handler the cause is resolved, appended to
the existing `logger.error` message rather than substituted for it, and
stored under `_lock`. The existing `_discard_handle()` call and state
transition are retained unchanged.
`test_existing_log_content_is_retained` asserts both the original text
and the cause appear.

On the success path `_last_failure_cause` is cleared to `None` beside
the existing `_state` assignment, inside the same lock acquisition.

### 3.3 EDIT Q — adapter probe and status line

`_bluetooth_adapter_present() -> bool` added at module level
(transport.py:67), reading `_BLUETOOTH_SYSFS = '/sys/class/bluetooth'`.
It returns True if any entry is listed, False if the directory exists
and is empty, and True if the check cannot be performed at all. The
whole probe is wrapped in `try/except Exception` returning True. The
unknown case is deliberately optimistic: an unreadable sysfs must never
be reported to the operator as a hardware fault.

The comment records that `PlatformDetector` already probes this same
path (platform.py:706), so this is a precedented pattern rather than a
new dependency.

In `_classify_connect_error`, a missing controller overrides the errno
mapping entirely — it is the more specific and more actionable fact, and
errno alone cannot discriminate an absent controller from a merely
unreachable peer.

In `manager.py`, `_link_cause_callback = None` was added beside the
existing `_link_connected_callback` (manager.py:109), and
`_render_disconnected` now draws the cause as a single centred line at
y=210, between the existing message at y=180 and the button column whose
top is 240. Nothing is drawn when the callback is unset or returns a
falsy value, so the screen is byte-for-byte what it was until there is
something to say. The existing `except Exception` around the whole
render remains the containment boundary.

In `app.py`, `_link_cause_callback` is wired at both sites that already
assign `_link_connected_callback`, using the same
`getattr(getattr(self, '_transport', None), ...)` guard for the same
reason: before `select_transport` has run there is no transport, and
'no transport' has no failure cause to report. Two hunks, eight lines
each; nothing else in `app.py` changed.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_connect_error_classification.py` — 29 tests covering all
thirteen `testing.unit_tests` scenarios and all three edge cases.

| Test | Prompt item |
|---|---|
| `test_socket_closed_when_connect_raises` | item 1 |
| `test_close_error_is_swallowed` | item 2 |
| `test_socket_not_closed_on_success` | item 3 |
| `test_base_exception_also_closes` | EDIT O's BaseException rule |
| `test_ebusy_maps_to_the_busy_string` | item 4 |
| `test_ehostdown_maps_to_unreachable` | item 5 |
| `test_missing_adapter_overrides_the_errno_mapping` | item 6 |
| `test_unmapped_errno_returns_its_name` | item 7 |
| `test_errno_none_does_not_raise` | item 8 |
| `test_never_raises_for_hostile_input` | data_schema validation |
| `test_every_mapped_cause_fits_the_display` | edge case 1, criterion 3 |
| `test_absent_path_returns_true` | item 9 |
| `test_empty_directory_returns_false` | item 10 |
| `test_populated_directory_returns_true` | boundary |
| `test_probe_failure_returns_true` | criterion 6 |
| `test_none_before_any_attempt` | criterion 4 |
| `test_set_after_a_failed_connect` | item 11 |
| `test_cleared_after_a_successful_connect` | item 11 |
| `test_repeated_failures_overwrite_rather_than_accumulate` | edge case 3 |
| `test_existing_log_content_is_retained` | criterion 5 |
| `test_property_is_read_only` | criterion 4 |
| `test_no_line_when_callback_unset` | item 12 |
| `test_no_line_when_cause_is_none` | item 12 |
| `test_line_drawn_above_the_button_column` | item 13 |
| `test_render_error_does_not_escape` | error_handling |
| `test_button_geometry_untouched` | criterion 10 |
| `test_no_shell_or_bluetooth_tooling_introduced` | criterion 7 |
| `test_no_recovery_action_introduced` | criterion 8 |

Three harness notes:

**`_open` is driven against a fake `socket` module.** `AF_BLUETOOTH`
does not exist on macOS, so `_open` raises before reaching the code
under test on the development platform. Replacing
`gtach.comm.rfcomm.socket` wholesale lets the real `_open` body run and
its close-on-failure behaviour be observed, on any platform.

**The DISCONNECTED render is called unbound against a minimal host.**
`_render_disconnected` uses only `rendering_engine`, `logger`,
`_get_cached_font`, `_draw_shift_border`, the two button attributes and
the new callback, so the tests supply exactly those and record what
`render_text` was asked to draw. That makes
`test_line_drawn_above_the_button_column` an assertion about the actual
y coordinate — `180 < y < 240` — rather than about a call happening.

**The constraint tests blank comments and strings before scanning.** A
`_code_only` helper tokenizes each file and replaces `COMMENT` and
`STRING` tokens with spaces, preserving line numbers so an offender is
reported at its real location. This matters because the comments and
docstrings of this change name the very tools and actions they exist to
explain *not* using — my first two drafts of these tests failed on
exactly that. Blanking string literals loses nothing here: every
construct being hunted for is a call, and the callable is a NAME token
that survives.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

As in the five preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt`; that file was restored with
`git checkout`.

```
$ pytest tests/
144 passed, 1 warning in 5.26s
```

The 115 tests standing at the end of `prompt-9c2f41d8` pass unchanged
alongside the 29 new ones. No existing test needed modification.

`ast.parse` succeeded on all four edited sources and the new test file.

Byte-identity was checked by diff rather than by inspection:

```
$ git diff src/gtach/comm/transport.py | grep -c "def reconnect_indefinitely"   → 0
$ git diff src/gtach/comm/transport.py | grep -c "def drop_link"                → 0
$ git diff src/gtach/comm/transport.py | grep -c "def disconnect"               → 0
$ git diff -U0 src/gtach/app.py | grep "^@@"    → two hunks, both the wiring
$ git diff -U0 src/gtach/display/manager.py | grep "^@@"  → two hunks, neither in
                                                  _register_disconnected_regions
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

Twelve of thirteen verified as written. Criterion 7 is satisfied in
substance but cannot hold as literally worded; see §7.

| # | Criterion | Result |
|---|---|---|
| 1 | `_open` closes the socket on failure and re-raises bare | ✅ four tests |
| 2 | `_CONNECT_FAULT_CAUSES`, `_bluetooth_adapter_present`, `_classify_connect_error` defined | ✅ transport.py:51, 67, 262 |
| 3 | Every mapped value ≤ 40 characters | ✅ asserted over the whole mapping |
| 4 | Read-only `last_failure_cause`, set on failure, cleared on success | ✅ four tests |
| 5 | Existing log content, `_discard_handle()` and state transition all retained | ✅ asserted by test |
| 6 | Probe returns True when it cannot be performed | ✅ asserted by test |
| 7 | Repo-wide grep for shell/Bluetooth tooling returns no match | ⚠️ see §7 — satisfied for this change, not achievable repo-wide |
| 8 | No code path performs any Bluetooth recovery action | ✅ asserted by test |
| 9 | `reconnect_indefinitely`, `drop_link`, `disconnect` byte-identical | ✅ absent from the diff |
| 10 | `_register_disconnected_regions` byte-identical | ✅ diff hunks fall outside it |
| 11 | `obd.py`, `serial_transport.py`, `tcp_transport.py`, `watchdog.py` byte-identical | ✅ absent from `git status` |
| 12 | The only `app.py` change is the `_link_cause_callback` wiring | ✅ two hunks, both the wiring |
| 13 | `pytest tests/` passes | ✅ 144 passed |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

One, and it concerns a success criterion that cannot be met as written.

**Criterion 7 — "`grep -rn 'subprocess|os.system|os.popen|hcitool|
hciconfig|btmgmt|rfkill' src/` returns no match" — is false of the
pre-existing codebase and was false before this change.** The matches
are:

- `src/gtach/comm/system_bluetooth.py` — drives `bluetoothctl` and
  `hcitool scan` for device DISCOVERY during setup mode. This is the
  pairing subsystem; removing it would break setup entirely.
- `src/gtach/utils/platform.py` — `subprocess.run(['which',
  'bluetoothctl'])` for capability detection, and `/dev/rfkill` as one
  of two Bluetooth-presence indicators.
- `src/gtach/utils/dependencies.py` — `subprocess` for dependency
  validation.
- `src/gtach/utils/terminal.py` — `os.system('stty sane')` for terminal
  restoration.

None was introduced by this change; none is a recovery action; and the
prompt's own constraints forbid modifying files outside its three named
targets. Deleting the pairing subsystem to satisfy a grep would be a
far larger and unmandated change.

The prompt's `validation` section states the intent correctly and
narrowly: "grep -rn 'subprocess\|os.system\|os.popen'
`src/gtach/comm/` `src/gtach/display/manager.py` returns no match
**introduced by this change**". I implemented that reading. The two
constraint tests scan the four files this change edits —
`transport.py`, `rfcomm.py`, `manager.py`, `app.py` — with comments and
strings blanked, and both return clean. `test_no_recovery_action_introduced`
additionally bars `hciuart`, `modprobe`, `insmod`, `rmmod`, `systemctl`
and `reboot` from those same files.

The substance of the constraint — that this change reports and does not
act — holds completely. What does not hold is the criterion's claim
about the repository as a whole, which was already untrue when the
prompt was written.

Beyond that, EDITs O, P and Q were applied as specified, all thirteen
unit-test scenarios and all three edge cases were implemented, and no
existing test required modification. Sixteen tests were added beyond the
thirteen scenarios, each asserting a success criterion or stated
error-handling rule the prompt lists without allocating to a scenario.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Findings Requiring Decision

Three, none blocking.

1. **The cause is stale on the DISCONNECTED screen after a successful
   reconnect that later drops.** `last_failure_cause` is cleared only on
   a successful `connect()`, and `drop_link` — which
   `change-9c2f41d8` calls on five consecutive read timeouts — does not
   set it. So a link that connects cleanly and then dies of silence
   shows no cause at all, because the last connect succeeded. That is
   arguably correct (nothing about the *connect* failed), but the
   operator sees a DISCONNECTED screen with no explanation in the one
   failure mode `change-9c2f41d8` was written for. Setting a cause such
   as 'no response from adapter' in `drop_link` would close that gap;
   it was not specified here and `drop_link` is explicitly out of scope.

2. **The adapter probe answers about the host, not the link.** With the
   controller wedged as it currently is on `gtach.local`
   (`hciconfig hci0 up` failing with ETIMEDOUT), `/sys/class/bluetooth`
   still lists `hci0` — the device node exists, it simply will not come
   up. `_bluetooth_adapter_present` therefore returns True and the cause
   falls through to the errno mapping, most likely 'bluetooth link busy
   - may need reset'. That is a reasonable answer and better than
   today's silence, but it is worth knowing that the probe detects an
   *absent* controller, not a *wedged* one. Distinguishing those would
   need `/sys/class/bluetooth/hci0/` attribute reads, which is more than
   this prompt asked for.

3. **EDIT O may resolve the EBUSY condition that `prompt-9c2f41d8`
   deferred**, and this is now the second change to bear on it. That
   prompt's §9 noted `drop_link` stopped abandoning sockets on the
   read-timeout path; EDIT O stops abandoning them on the connect-failure
   path, which is the one that actually preceded the observed
   `[Errno 16]` runs. Both should be assessed together at the next
   deployment, before any separate investigation is opened.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Commit Record

Committed and pushed as a single commit containing
`src/gtach/comm/rfcomm.py`, `src/gtach/comm/transport.py`,
`src/gtach/display/manager.py`, `src/gtach/app.py`,
`tests/test_connect_error_classification.py`, this report and the prompt
T-Doc closure move.

Not included, and left uncommitted in the working tree: `.gitignore`,
`CLAUDE.md`, the `change-2ac1c602` and `issue-2ac1c602` modifications,
and the untracked `change-7d4e91a3` and `issue-7d4e91a3` T-Docs. These
are authoring work belonging to the user, not this prompt's deliverable.
The `change-5e7a03c4` and `issue-5e7a03c4` T-Docs for this triple were
already committed and remain active and unmodified.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes:

1. With the controller healthy and the OBD peer absent, confirm the log
   and the DISCONNECTED screen report an unreachable peer.
2. With the controller down, confirm both report an adapter fault,
   distinctly.
3. Across several retry cycles against a failing connect, confirm
   `/proc/<pid>/fd` shows no growth in socket descriptors — the direct
   test of EDIT O.

Note that the controller on `gtach.local` is currently wedged:
`hciconfig hci0 up` fails with ETIMEDOUT. Recovery is a host operation —
restarting `hciuart.service` to re-attach the chip, or a reboot — and is
deliberately not something this change attempts. Step 2 above may
require that recovery first, and per §8 finding 2 a wedged controller
will report via the errno mapping rather than as a missing controller.

`issue-5e7a03c4` and `change-5e7a03c4` remain active pending the three
steps above.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-5e7a03c4 iteration 1: socket close on connect failure in rfcomm.py, errno classification and last_failure_cause in transport.py, sysfs adapter probe, DISCONNECTED status line in manager.py and its app.py wiring, plus 29 unit tests. Twelve of thirteen success criteria verified as written; criterion 7's repo-wide grep is false of the pre-existing codebase and was implemented per the prompt's own narrower validation wording. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
