Created: 2026 August 12

# Report: Give stacks.log a Run Header and Rotate It Once Per Process

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
`prompt-3b8c50f2-stacks-log-run-header-and-rotation.md` (iteration 1,
coupled to `change-3b8c50f2` and `issue-3b8c50f2`).

`stacks.log` is opened in append mode and faulthandler's dumps carry no
timestamp, PID or run identifier, so dumps from successive process
lifetimes concatenated indistinguishably — worst in the very scenario
the file exists for, a watchdog-triggered restart. It also had no
rotation or size cap, unlike `debug.log`. This change gives every arming
an identifying header and rotates the file once per process lifetime.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT I — module-level names | ✅ Applied |
| EDIT J — rotate on first arm | ✅ Applied |
| EDIT K — write the run header | ✅ Applied |
| `tests/test_stacks_log_rotation.py` | ✅ Created, 18 tests |
| `pytest tests/` | ✅ 92 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

`prompt-3b8c50f2-stacks-log-run-header-and-rotation.md` moved to
`ai/workspace/prompt/closed/`. The issue and change T-Docs remain
active, as instructed. No T06 result document was created.

All edits are inside `src/gtach/main.py`; no other file was modified.
`src/gtach/app.py`, `src/gtach/core/watchdog.py`,
`src/gtach/comm/transport.py`, `bin/gtach.service` and
`tests/test_stack_dump_toggle.py` are byte-identical to their pre-change
state, and `disable_stack_dumps` does not appear in the diff at all.

**No Python-side periodic timer, thread, or per-dump timestamp
mechanism was introduced.** This was the prompt's single most important
constraint, and it is now enforced by a test rather than by inspection:
`test_no_timer_or_thread_introduced` asserts that neither `threading`
nor `time.sleep` appears in any executable line of the module. Both
additions run only at arming time, when the process is by definition
healthy — which is precisely why the anchor they write survives a
stall.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT I — module-level names

`import datetime` added in alphabetical position among the existing
stdlib imports (main.py:14).

`_stacks_rotated = False` added beside `_stacks_file` (main.py:32),
commented with the reason rotation is once per *process* rather than
once per arm: arming occurs on every OPTIONS toggle-on, and rotating
each time would push a just-captured reproduction off the end of the
backup chain — an operator toggling debug off and on three times would
discard the very dumps they had gone to the trouble of provoking.

`_STACKS_BACKUPS = 3` added after `_STACKS_LOG` (main.py:44), commented
with the measured basis carried over from the change document: a dump of
four threads is ~604 bytes at a 15 s interval, so an armed run produces
~145 KB per hour, and three backups plus the live file bound cross-run
accumulation at four files.

### 3.2 EDIT J — rotate on first arm

`_rotate_stacks_log() -> None` added immediately before
`enable_stack_dumps` (main.py:117). It returns immediately when
`_STACKS_LOG` does not exist or is zero-length, so a run that armed and
produced nothing does not consume a generation. Otherwise it shifts
generations from the highest downwards —
`for i in range(_STACKS_BACKUPS - 1, 0, -1)` — then renames the live
file to `.1`.

Descending order is load-bearing and the docstring says so: ascending
order would overwrite each generation with the one below it before it
had itself been moved, collapsing the whole chain to one run's content.
`os.replace` rather than `os.rename`, so an existing destination is
overwritten rather than raising on some platforms; what was `.3` is
discarded, which is intended.

In `enable_stack_dumps`, `_stacks_rotated` joins the existing `global`
statement. After the already-armed early return and before the file is
opened, `_rotate_stacks_log()` is called when `_stacks_rotated` is
False, inside a `try/except OSError` printing the existing style of
warning to `sys.stderr`, with `_stacks_rotated = True` in a `finally`
clause so a persistent failure is not retried on every subsequent arm.
Arming proceeds regardless — a failure here costs history, not
evidence.

### 3.3 EDIT K — write the run header

`_stacks_header() -> str` added (main.py:147). It resolves the version
via `importlib.metadata.version('gtach')` inside a `try/except
Exception` falling back to the literal `'unknown'`, mirroring the
guarded pattern already used in `parse_arguments`, and returns:

```
=== gtach {version} pid {os.getpid()} armed {timestamp} ===\n
```

with `timestamp` from `datetime.datetime.now().isoformat(timespec='seconds')`.

In `enable_stack_dumps` the header is written immediately after the
successful open and before `faulthandler.enable` and
`faulthandler.dump_traceback_later`, inside its own `try/except
Exception` printing a warning and continuing. The ordering is required
so that no dump can be written above the header identifying it, and it
is asserted by test rather than left to inspection.

The docstring was extended to record the rotation and header behaviour,
the arming-time-only property and why it matters, and that the PID in
the header is direct evidence of a systemd restart when it changes
between two headers — which `issue-2ac1c602`'s verification requires.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_stacks_log_rotation.py` — 18 tests covering all ten
`testing.unit_tests` scenarios and all three edge cases.

| Test | Prompt item |
|---|---|
| `test_first_arm_writes_a_header_with_this_pid` | item 1 |
| `test_no_rotation_when_nothing_pre_existed` | item 1 |
| `test_header_precedes_arming` | success criterion 3 |
| `test_version_failure_still_emits_a_header` | item 8 |
| `test_write_failure_does_not_prevent_arming` | item 9 |
| `test_second_arm_without_disable_writes_one_header` | item 6 |
| `test_rearm_within_one_process_appends_a_second_header` | item 4 |
| `test_pre_existing_content_moves_to_generation_one` | item 2 |
| `test_empty_file_is_not_rotated` | item 3 |
| `test_rearm_does_not_rotate_again` | item 4, edge cases 1 and 3 |
| `test_four_process_lifetimes_keep_three_backups` | item 5 |
| `test_generations_shift_outward_by_exactly_one` | item 10 |
| `test_oldest_generation_is_discarded_without_raising` | edge case 2 |
| `test_rotation_failure_still_arms` | item 7 |
| `test_rotation_failure_is_not_retried` | error_handling |
| `test_no_timer_or_thread_introduced` | constraint 1 |
| `test_dump_interval_unchanged` | success criterion 8 |
| `test_stacks_log_path_and_backup_count` | success criteria 1, 8 |
| `test_rotation_flag_initialises_false` | success criterion 1 |

The header is matched against a compiled regex asserting the exact
shape the `data_schema` specifies — `'=== gtach '` prefix, `' ==='`
suffix, an integer PID equal to `os.getpid()`, and an ISO-8601
seconds-precision timestamp — rather than by substring, so a
malformed header fails rather than passing on a partial match.

`test_generations_shift_outward_by_exactly_one` is the one that would
catch an ascending-order regression: it seeds `stacks.log`, `.1` and
`.2` with distinguishable content and asserts each moves outward by
exactly one, which ascending order would collapse to three copies of the
live file.

Three harness notes:

**Rotation failure is injected at `_rotate_stacks_log`, not inside it.**
Monkeypatching the module attribute proves the caller's guard works
without depending on which filesystem operation happens to fail first,
which varies by platform.

**The header-write failure test shadows `open` as a module global.**
Python resolves a name in module globals before builtins, so
`monkeypatch.setattr(gtach_main, 'open', ..., raising=False)` reaches
`enable_stack_dumps`'s `open` call and nothing else in the process —
cleaner and far narrower than patching `__builtins__`.

**The module is fetched from `sys.modules`.** Same reason as the
preceding two prompts: `from gtach import main` retrieves the re-exported
`main` *function*, whose namespace has none of this state
(`issue-c1d4b8e6`).

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

As in the three preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt` as a side effect; that file was restored
with `git checkout`.

```
$ pytest tests/
92 passed, 1 warning in 9.00s
```

Passed on the first run. The 74 tests standing at the end of
`prompt-7d4e91a3` pass alongside the 18 new ones, and
`tests/test_stack_dump_toggle.py` is unmodified — it does not appear in
`git status`, and its `fh` fixture, which does not patch
`_stacks_rotated`, is unaffected because rotation against a
non-existent temporary path is a no-op.

`ast.parse` succeeded on `src/gtach/main.py` and the new test file.

`git diff -U0 src/gtach/main.py` produces nine hunks, confined to the
imports, the module constants, the two new helpers and
`enable_stack_dumps`. `git diff src/gtach/main.py | grep -c
'disable_stack_dumps'` returns 0.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

All twelve criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | `_STACKS_BACKUPS = 3` and module-level `_stacks_rotated = False` | ✅ main.py:44, 32 |
| 2 | Module-level `_rotate_stacks_log` and `_stacks_header` | ✅ main.py:117, 147 |
| 3 | Header written after the open, before `dump_traceback_later` | ✅ asserted by call-order test |
| 4 | `_rotate_stacks_log` called only when `_stacks_rotated` is False; flag set either way | ✅ two tests |
| 5 | Descending generation shift using `os.replace` | ✅ main.py:139–144 |
| 6 | Still `mode='a'`; no `mode='w'` against `_STACKS_LOG` | ✅ |
| 7 | `disable_stack_dumps` byte-identical | ✅ absent from the diff |
| 8 | `_STACKS_LOG` unchanged; interval still `15`, `repeat=True` | ✅ two tests |
| 9 | No `threading.Timer`, `threading.Thread` or periodic Python-side timer anywhere in `main.py` | ✅ asserted by test over executable lines |
| 10 | `app.py`, `watchdog.py`, `transport.py`, `bin/gtach.service` byte-identical | ✅ absent from `git status` |
| 11 | `tests/test_stack_dump_toggle.py` passes unmodified | ✅ |
| 12 | `pytest tests/` passes | ✅ 92 passed |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

None. EDITs I, J and K were applied as specified, and all ten unit-test
scenarios plus the three edge cases were implemented.

Five tests were added beyond the ten scenarios, each asserting a
success criterion or a stated error-handling rule the prompt lists but
does not allocate to a scenario: `test_header_precedes_arming`
(criterion 3), `test_rotation_failure_is_not_retried` (the `finally`
clause's stated purpose), `test_no_timer_or_thread_introduced`
(criterion 9 and the primary constraint), `test_dump_interval_unchanged`
and `test_stacks_log_path_and_backup_count` (criterion 8), and
`test_rotation_flag_initialises_false` (criterion 1).

That last one asserts the *initialiser* in the module source rather than
the runtime value of `_stacks_rotated`. The runtime value is genuine
cross-test state — `tests/test_stack_dump_toggle.py` calls
`enable_stack_dumps` without patching the flag, so its value at any
point depends on test execution order. Asserting the source text is the
only order-independent form of that check, and the prompt's criterion is
about initialisation.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Findings Requiring Decision

Two, neither blocking, both concerning the boundary of what this change
bounds.

1. **Rotation bounds cross-run accumulation, not within-run growth.**
   The prompt's scope is explicitly the former, and the design is
   correct for it. But a single run left armed indefinitely still grows
   `stacks.log` without limit at ~145 KB per hour — the figure in
   `_STACKS_BACKUPS`'s own comment — and nothing rotates it until the
   next process starts. Roughly 3.5 MB per day on a card-backed
   filesystem. In the intended use (enable, reproduce, disable) this
   does not arise, and adding a size check would require a periodic
   Python-side mechanism the prompt rightly forbids. If it ever needs
   addressing, the arming-time check is the place: `_rotate_stacks_log`
   could take a size threshold and be consulted on re-arm as well as
   first arm, keeping everything at arming time. Flagged rather than
   done, being outside this prompt.

2. **The four-file bound assumes rotation succeeds.** If
   `_rotate_stacks_log` raises, `_stacks_rotated` is set True anyway —
   correct, and specified, since retrying a persistent failure on every
   arm would be noise. The consequence is that a run whose rotation
   failed appends to the existing `stacks.log` for its whole lifetime,
   and the header is what makes that recoverable: the reader sees two
   headers with different PIDs in one file rather than a silently
   merged pair of runs. Worth knowing when reading a file that turns
   out to span more runs than expected.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Commit Record

Committed and pushed as a single commit containing `src/gtach/main.py`,
`tests/test_stacks_log_rotation.py`, this report and the prompt T-Doc
closure move. The closure move is meaningless without the code it
certifies, so they travel together.

Not included, and left uncommitted in the working tree: `.gitignore`,
`CLAUDE.md`, the `change-2ac1c602` and `issue-2ac1c602` modifications,
and the untracked `change-7d4e91a3` and
`issue-7d4e91a3` T-Docs. These are authoring work belonging to the
user, not this prompt's deliverable. The `change-3b8c50f2` and
`issue-3b8c50f2` T-Docs for this triple were already committed before
this session's work began and remain active and unmodified.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes:

1. Restart the service; enable debug through the OPTIONS toggle.
2. Confirm `stacks.log` opens with a header whose pid matches
   `systemctl show gtach -p MainPID`.
3. Confirm the previous run's dumps are now at `stacks.log.1`.
4. Toggle debug off and on again; confirm a second header appears with
   no further rotation.

The PID in the header is not incidental. `issue-2ac1c602` remains active
pending evidence that a watchdog critical timeout produces a systemd
restart, and two headers with different PIDs in one `stacks.log` is
exactly that evidence — captured automatically rather than requiring an
operator to be watching `systemctl` at the moment it happens. This
change therefore makes `issue-2ac1c602`'s outstanding verification
cheaper to obtain, but does not itself close it.

`issue-3b8c50f2` and `change-3b8c50f2` remain active pending the four
steps above.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-3b8c50f2 iteration 1: _STACKS_BACKUPS and _stacks_rotated module names, _rotate_stacks_log and _stacks_header helpers, and their integration into enable_stack_dumps, plus 18 unit tests. All twelve success criteria verified, no deviations. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
