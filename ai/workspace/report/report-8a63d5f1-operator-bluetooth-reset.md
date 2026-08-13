Created: 2026 August 13

# Report: Operator-Initiated Bluetooth Reset From the DISCONNECTED Screen

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

Records the implementation of
`prompt-8a63d5f1-operator-bluetooth-reset.md` (iteration 1, coupled to
`change-8a63d5f1` and `issue-8a63d5f1`).

`change-5e7a03c4` iteration 2 made the DISCONNECTED screen report
"bluetooth wedged - reset required" while offering no way to perform
that reset — a gap that report raised as its own finding 1. This change
adds a Bluetooth Reset button in the slot `change-4f1e82b7` left free,
dispatching a bounded, debounced controller reset to a worker thread and
reporting the outcome on the existing cause line.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT X — `src/gtach/utils/bluetooth_reset.py` | ✅ New module |
| EDIT Y — debounced worker dispatch in `app.py` | ✅ Applied |
| EDIT Z — the button in `manager.py` | ✅ Applied |
| `tests/test_bluetooth_reset.py` | ✅ Created, 32 tests |
| `tests/test_disconnected_screen.py` | ⚠️ Two host lines updated — see §5 |
| `pytest tests/` | ✅ 228 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

**Both critical constraints hold and are enforced by test.**

*The reset never runs on the display thread.* `_on_bluetooth_reset`
starts a daemon thread named `bt_reset` and returns;
`test_single_press_returns_promptly` blocks the worker and asserts the
caller returns in under 0.5 s regardless, and
`test_callback_performs_no_blocking_call` asserts at source level that
no `reset_adapter` reference, `join(` or `time.sleep` exists outside the
nested worker. This matters because 'display' is a watchdog critical
thread at a 45 s timeout and, since `change-2ac1c602`, a critical
timeout terminates the process — a synchronous subprocess here would
have turned the button into an application restart.

*There is no automatic invocation.* `test_exactly_one_call_site` scans
every `.py` file under `src/` with comments and string literals blanked
and asserts exactly one definition and exactly one call, the call being
in `app.py`. No timer, scheduler, retry counter or startup path reaches
it.

`subprocess` appears in no file this change touched other than
`bluetooth_reset.py`, and nowhere under `src/gtach/comm/`, which is
byte-identical throughout. No `shell=True` anywhere. The reset command
is `hciconfig hci0 reset`; no `hci0 down` sequence exists in executable
code.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT X — `src/gtach/utils/bluetooth_reset.py`

New module, 170 lines, whose docstring states that it is the only place
in GTach permitted to invoke an external command and why: that boundary
is the entire basis on which host action is permitted at all. It records
the three rules that keep the privileged surface small — no
`shell=True`, `hciconfig hci0 reset` only, and no systemctl/hciuart/
rfkill/module operations — and the reason for the second, that
`hciconfig hci0 down` followed by `up` was attempted on target, the down
succeeded, the up returned ETIMEDOUT, and the controller could not be
brought back.

Imports are exactly `logging`, `shutil`, `subprocess` and `typing`;
`test_module_imports_are_minimal` asserts that set by AST.

`_hciconfig_path()` resolves via `shutil.which('hciconfig')`, falling
back to a second `shutil.which` scoped to `/usr/bin`. See §8 deviation 1
for why that rather than an existence check.

`reset_adapter(timeout=10.0) -> str` resolves the path, runs
`[path, 'hci0', 'reset']`, verifies via `[path, 'hci0']` treating the
presence of `UP RUNNING` in stdout as up, and returns
`'bluetooth adapter reset'`. If not up it runs `[path, 'hci0', 'up']`
once and re-verifies, returning the same string on success and
`'adapter down - reboot required'` otherwise. That last string is
deliberately blunt and commented as not to be softened: it is exactly
the state the manual attempt on this host produced.

`subprocess.TimeoutExpired` returns `'bluetooth reset timed out'` with
no second kill, `subprocess.run` having already killed the child.
`PermissionError` returns `'bluetooth reset not permitted'`,
`FileNotFoundError` returns `'hciconfig not found'`, and a bare
`Exception` returns `'bluetooth reset failed'`. Every command and return
code logs at DEBUG; every exception logs with `exc_info=True`. The
function cannot raise, for any input or environment.

Unexpected stdout — including invalid UTF-8 — is treated as "not up",
so a parsing surprise costs one extra `up` attempt rather than an
exception. `test_unexpected_stdout_is_treated_as_down` covers it.

### 3.2 EDIT Y — debounced worker dispatch

`self._bt_reset_in_flight = threading.Event()` added to `__init__`,
along with `self._bt_reset_status` and a `threading.Lock` guarding it.

`_on_bluetooth_reset()` tests the Event and returns immediately when it
is set — a press during a reset is ignored, not queued — then sets it,
logs, writes `'resetting bluetooth...'` so the operator sees the press
register, and starts a daemon `threading.Thread` named `bt_reset`. The
worker calls `reset_adapter()`, writes the outcome, and clears the Event
in a `finally` so a raising worker cannot wedge the button for the life
of the process. The worker body is wrapped in `try/except Exception`
logging with `exc_info=True` and writing `'bluetooth reset failed'`.

The thread is deliberately **not** registered with `ThreadManager`; it
is short-lived and registering it would put it under `WatchdogMonitor`
for the seconds it exists. `test_worker_is_not_registered_with_thread_manager`
asserts `register_thread` does not appear in the method's source.

For the progress route the prompt offered a choice. **Holding the
string on the application was taken**, and the comment states why: the
transport's cause is guarded by its own lock and has no public setter,
so writing it from `app.py` would put the application inside `comm`'s
invariants for the sake of one string. A new `_disconnected_cause()`
method merges the two — a reset outcome supersedes the transport's cause
while it stands, and is discarded once `is_connected()` returns True so
a stale outcome cannot mask a later transport failure. Both existing
`_link_cause_callback` assignments now point at that method instead of
their previous lambdas.

`_bluetooth_reset_callback` is wired in `_start_normal_mode` and also in
`_start_setup_mode`; see §8 deviation 2.

### 3.3 EDIT Z — the button

`self._bluetooth_reset_callback = None` and
`self._disconnected_btn_bt_reset = None` added beside the existing
callback and button attributes.

`_register_disconnected_regions` now builds its specs list
conditionally: always the Setup entry, and `disconnected_bt_reset` only
when `_bluetooth_reset_callback is not None`, so the screen degrades to
its previous single-button form without it. `width=240` and `top=240`
are unchanged, and `_button_column` stacks downward from an explicit
top, so the Setup rect is identical either way —
`test_setup_rect_identical_either_way` asserts that by comparing the
one-button and two-button cases directly.

`_render_disconnected` draws the second button only when its rect is not
None.

The label is `'BT Reset'`, not `'Bluetooth Reset'`. This was measured
rather than assumed: against the font `_get_cached_font(28)` actually
returns, the full label renders at **300 px** on a 240 px button, and
the abbreviation at 174 px. `test_label_fits_the_button_width` re-runs
that measurement. The button width and the other buttons' font are
unchanged, as the prompt requires.

`_button_column`, `_draw_retry_arc` and the cause line rendering do not
appear in the diff.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_bluetooth_reset.py` — 32 tests covering all fourteen
`testing.unit_tests` scenarios and all three edge cases.

| Test | Prompt item |
|---|---|
| `test_reset_then_up_running` | item 1 |
| `test_up_attempt_recovers` | item 2 |
| `test_adapter_stays_down` | item 3 |
| `test_timeout` | item 4 |
| `test_path_unresolved` | item 5 |
| `test_permission_error` | item 6 |
| `test_file_not_found` | error_handling |
| `test_arbitrary_exception` | item 7 |
| `test_unexpected_stdout_is_treated_as_down` | edge case 3 |
| `test_timeout_is_passed_through` | requirement: bounded |
| `test_every_outcome_fits_the_cause_line` | item 8 |
| `test_reboot_message_is_not_softened` | EDIT X's explicit instruction |
| `test_subprocess_only_in_the_reset_module` | criterion 2 |
| `test_no_subprocess_under_comm` | constraint |
| `test_no_shell_true_anywhere` | criterion 3 |
| `test_exactly_one_call_site` | criteria 4, 5 |
| `test_no_down_then_up_sequence` | criterion 9 |
| `test_no_systemctl_hciuart_rfkill_or_modules` | constraint |
| `test_module_imports_are_minimal` | EDIT X's import list |
| `test_single_press_returns_promptly` | item 9, criterion 6 |
| `test_worker_is_a_daemon` | edge case 1 |
| `test_worker_is_not_registered_with_thread_manager` | criterion 7 |
| `test_second_press_while_in_flight_is_ignored` | item 10 |
| `test_press_after_completion_starts_a_new_worker` | item 12 |
| `test_raising_worker_clears_the_event` | item 11, criterion 8 |
| `test_progress_then_outcome_written` | requirement: progress shown |
| `test_callback_performs_no_blocking_call` | criterion 6 |
| `test_no_transport_and_no_status` | edge case 2 |
| `test_transport_cause_when_no_reset_status` | cause-line merge |
| `test_reset_status_supersedes_transport_cause` | cause-line merge |
| `test_status_cleared_once_the_link_returns` | cause-line merge |
| `test_button_press_with_no_transport_is_guarded` | edge case 2 |
| `test_callback_unset_registers_only_setup` | item 13, criterion 11 |
| `test_callback_set_registers_both` | item 14 |
| `test_setup_rect_identical_either_way` | item 14, criterion 12 |
| `test_reset_spec_invokes_the_callback` | wiring |
| `test_not_drawn_when_rect_is_none` | criterion 11 |
| `test_drawn_when_rect_exists` | EDIT Z |
| `test_label_fits_the_button_width` | EDIT Z's label rule |

Three harness notes:

**The debounce tests block the worker deliberately.** `reset_adapter` is
replaced by a callable that waits on an Event the test controls, so the
"in flight" window is real rather than simulated. That is what makes
`test_single_press_returns_promptly` a claim about dispatch — the caller
returns while the worker is provably still inside the reset — and
`test_second_press_while_in_flight_is_ignored` a claim about debounce
rather than about timing luck. Every wait is bounded by
`JOIN_TIMEOUT = 5.0`.

**The containment scans blank comments and string literals.** A
`_code_only` tokenizer replaces `COMMENT` and `STRING` tokens with
spaces, preserving line numbers. This is necessary because
`bluetooth_reset.py`'s own docstring names `subprocess`, `shell=True`,
`hciuart`, `rfkill` and the down/up sequence precisely in order to state
the rules it follows — the first run of these tests failed on exactly
that, on three of them at once.

**`_on_bluetooth_reset` and `_disconnected_cause` are called unbound.**
Both use only a handful of attributes, so the tests supply a
`SimpleNamespace` rather than constructing a `GTachApplication`, whose
constructor needs a terminal and a device store.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Existing Test Module Updated

`tests/test_disconnected_screen.py` required two lines. Its render host
needed `_disconnected_btn_bt_reset`, and its registration host needed
`_bluetooth_reset_callback`; without them the `SimpleNamespace` hosts
raise `AttributeError` inside the methods under test.

The registration host sets the callback to `None` **deliberately**, with
a comment saying so: that is the configuration in which the
single-button form those tests describe still holds, so their
assertions — exactly one region, Setup at `rect-0`, `width=240`,
`top=240` — remain true and unmodified. No assertion in that module
changed. `change-4f1e82b7`'s claims are all still enforced.

Flagged here rather than buried because "added an attribute so the test
still runs" and "adjusted a test until it passed" look similar in a
diff. This is the first.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Verification Method

As in the eight preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt`; that file was restored with
`git checkout`.

```
$ pytest tests/
228 passed, 1 warning in 6.79s
```

The new module runs real threads and asserts on elapsed time, so the
suite was run three further times to check for flakiness: 228 passed
each time, 6.75–6.83 s. Stable.

The label measurement was taken against the real font manager under
`SDL_VIDEODRIVER=dummy`, not estimated:

```
'Bluetooth Reset'  width=300px   (240 px button — overflows)
'BT Reset'         width=174px
```

`ast.parse` succeeded on all three sources and the new test file.

Containment was checked at the shell as well as by test:

```
$ grep -rn "shell=True" src/          → one docstring line only
$ grep -rn "hci0 down" src/           → one docstring line only
$ grep -rn "reset_adapter" src/       → definition + one call (app.py:345)
$ git status --porcelain src/gtach/comm/   → empty
$ git diff src/gtach/display/manager.py | grep -E "^[-+].*(def _button_column|def _draw_retry_arc)"  → empty
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

All fourteen criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | Module exists; `reset_adapter` returns a non-empty string on every path | ✅ eleven tests |
| 2 | `subprocess` matches only the reset module | ✅ see §9 finding 3 on pre-existing files |
| 3 | No `shell=True` | ✅ asserted over blanked source |
| 4 | Definition plus exactly one call site, in `_on_bluetooth_reset` | ✅ asserted by test |
| 5 | No timer, scheduler, retry counter or startup path invokes it | ✅ same test |
| 6 | Returns without blocking; starts a daemon thread named `bt_reset` | ✅ three tests |
| 7 | Worker not registered with ThreadManager | ✅ asserted by test |
| 8 | Debounce Event cleared in a `finally` | ✅ asserted by test |
| 9 | Command is `hciconfig hci0 reset`; no `hci0 down` in `src/` | ✅ |
| 10 | `'adapter down - reboot required'` returned when it cannot come back | ✅ two tests |
| 11 | Region registered only when the callback is set | ✅ two tests |
| 12 | Setup rect identical either way | ✅ direct comparison |
| 13 | `src/gtach/comm/` byte-identical; `_button_column`, `_draw_retry_arc`, cause line unchanged | ✅ absent from diffs |
| 14 | `pytest tests/` passes | ✅ 228 passed |

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Deviations from the Prompt Specification

Three.

**1. `_hciconfig_path` uses `shutil.which('hciconfig', path='/usr/bin')`
rather than an existence check on `/usr/bin/hciconfig`.** EDIT X
specifies "falling back to '/usr/bin/hciconfig' when that exists", but
also restricts imports to `subprocess`, `shutil`, `logging` and
`typing` — and `os.path.exists` needs `os`. Reaching it via `shutil.os`
would work and is what I wrote first, but it is a hack. The scoped
`which` stays inside the permitted imports, and is strictly better: it
confirms the file is executable, which `exists()` would not.

**2. `_bluetooth_reset_callback` is wired in `_start_setup_mode` as well
as `_start_normal_mode`.** EDIT Y names only `_start_normal_mode`. I
believe that is an oversight, and wiring only there would ship a defect:
`_start_obd` runs "against the existing display" (app.py:485), which on
the setup route is the `DisplayManager` created by `_start_setup_mode`.
The DISCONNECTED screen reached after completing setup is therefore
drawn by that instance, and with the callback unset the button would be
neither registered nor drawn — so every operator who passed through
setup would never see it. Every other display callback
(`_setup_entry_callback`, `_restart_callback`, `_debug_toggle_callback`,
`_link_connected_callback`, `_link_cause_callback`,
`_retry_interval_callback`) is already wired at both sites. This is one
line and is commented with the reasoning; delete it if the single-site
wiring was intended.

**3. Two lines added to `tests/test_disconnected_screen.py`.** Detailed
in §5.

Beyond those, EDITs X, Y and Z were applied as specified, and all
fourteen unit-test scenarios plus the three edge cases were implemented.
Eighteen tests were added beyond the fourteen scenarios, each asserting
a success criterion or stated constraint the prompt lists without
allocating to a scenario.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Findings Requiring Decision

Four, none blocking.

1. **The button will very probably not fix the fault currently on
   `gtach.local`, and the prompt says so.** Recording it here too
   because it is the thing most likely to be misread on target: the
   present condition survives a full reboot — `stacks.log` headers show
   pid 720 at 14:52:37 then pid 671 at 14:56:32, a *decreasing* pid,
   with the same `[Errno 16]` failures resuming immediately on the new
   run — and a controller reset is strictly weaker than a reboot. The
   button addresses the narrower wedge seen earlier at 13:xx, where
   `hcitool con` showed an ACL in state 9 with its handle unreaped. A
   press that changes nothing is the expected outcome today and is not
   evidence the button is broken.

2. **`reset_adapter` will almost certainly return
   `'bluetooth reset not permitted'` unless GTach runs as root.**
   `hciconfig hci0 reset` requires `CAP_NET_ADMIN`. `bin/gtach.service`
   was not examined for a `User=` directive because the prompt forbids
   modifying it, so this is untested rather than known. If the service
   runs unprivileged, the button will report the permission failure
   clearly — which is correct behaviour and readable to the operator,
   but not useful. Worth confirming before the on-target session, since
   it determines whether steps 2 and 3 below can produce a meaningful
   result at all.

3. **A dead file skews any repo-wide `subprocess` scan.**
   `src/gtach/display/manager_backup.py` is unreferenced, 0% covered,
   superseded by `manager.py`, and imports `subprocess` at line 21. It
   is in `src/` only because it was never deleted.
   `src/gtach/display/setup_original_backup.py` is in the same
   condition. Criterion 2 is met in substance — nothing this change
   touched imports `subprocess` outside the reset module — but the
   containment test needs an explicit allowlist naming these files,
   which is documented in it. Deleting both backups would let that
   allowlist shrink to the three genuine pre-existing users; it is out
   of scope here.

4. **The reset outcome persists on screen until the link returns.**
   `_disconnected_cause` clears `_bt_reset_status` only when
   `is_connected()` becomes True. After a failed reset the operator sees
   the outcome indefinitely, which is accurate, but a subsequent
   transport cause change will not surface while it stands. The
   retry-countdown arc from `change-4f1e82b7` continues to show
   independently that the application is alive, which is the more
   important half.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Commit Record

Committed and pushed as a single commit containing
`src/gtach/utils/bluetooth_reset.py`, `src/gtach/app.py`,
`src/gtach/display/manager.py`, `tests/test_bluetooth_reset.py`, the
two-line `tests/test_disconnected_screen.py` update, this report and the
prompt T-Doc closure move.

The `change-8a63d5f1` and `issue-8a63d5f1` T-Docs for this triple were
already committed and remain active. The working tree carried no other
uncommitted authoring work at the time of this commit.

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes:

1. Press the button and confirm the retry arc keeps animating and the
   performance line still reports 30.0 FPS throughout. **If the display
   stalls, the dispatch is wrong** and the watchdog will eventually
   restart the application — this is the check that matters most.
2. Confirm the outcome appears on the cause line.
3. Press twice quickly and confirm only one reset runs.

Per §9 finding 2, confirm first whether the service runs with the
privileges `hciconfig hci0 reset` needs; if not, steps 2 and 3 will
exercise the permission-denied path rather than the reset itself.

Per §9 finding 1, this button is **not** expected to fix the failure
currently on `gtach.local`. Locating that fault is a separate
investigation, most probably on the ELM327 emulator.

`issue-8a63d5f1` and `change-8a63d5f1` remain active pending the three
steps above.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-13 | Initial report. Implements prompt-8a63d5f1 iteration 1: new bluetooth_reset module owning the only external-command invocation in GTach, debounced daemon-worker dispatch in app.py, and the conditionally registered BT Reset button on the DISCONNECTED screen, plus 32 unit tests. All fourteen success criteria verified. Three deviations recorded: a scoped shutil.which in place of an os.path.exists the import list forbade, the reset callback additionally wired in _start_setup_mode to avoid shipping the button absent on the setup route, and two attribute lines added to tests/test_disconnected_screen.py. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
