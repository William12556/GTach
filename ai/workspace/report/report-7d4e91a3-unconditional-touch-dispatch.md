Created: 2026 August 12

# Report: Dispatch Short Presses to the Touch Coordinator Unconditionally

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
`prompt-7d4e91a3-unconditional-touch-dispatch.md` (iteration 1, coupled
to `change-7d4e91a3` and `issue-7d4e91a3`).

`TouchHandler._handle_short_press` called into the touch coordinator
only when `config.mode` was `DisplayMode.OPTIONS`, so the DISCONNECTED
screen's Setup and Simulate buttons and the ACKNOWLEDGEMENT screen's
dismiss region were registered, drawn, and never hit-tested. This change
removes the screen-enumerating conditional from the dispatch path.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT A — unconditional dispatch in `_handle_short_press` | ✅ Applied |
| EDIT B — remove the inert DISCONNECTED branch from `_handle_long_press` | ✅ Applied |
| `tests/test_touch_dispatch.py` | ✅ Created, 15 tests |
| `pytest tests/` | ✅ 73 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

`prompt-7d4e91a3-unconditional-touch-dispatch.md` moved to
`ai/workspace/prompt/closed/`. The issue and change T-Docs remain
active, as instructed. No T06 result document was created.

Two edits in one file. No other source file was modified, no new
imports, no new dependencies. `src/gtach/display/manager.py`,
`src/gtach/display/input/touch_coordinator.py` and
`src/gtach/display/models.py` are byte-identical to their pre-change
state.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT A — unconditional dispatch

The three-line block at the former touch.py:239–241 —

```python
if self.display_manager.config.mode == DisplayMode.OPTIONS:
    self._handle_options_touch(x, y)
    return
```

— was replaced by an unconditional dispatch as the last statement of the
`try` block (touch.py:245–246):

```python
action = self.display_manager.handle_touch_event((x, y))
self.logger.debug(f"Touch dispatch at ({x}, {y}) -> {action}")
```

The setup-mode branch (touch.py:171–173) and both swipe branches
(touch.py:196–219) are unchanged and retain their early returns, so the
dispatch is reached only by a press that is neither.

`_handle_options_touch` was deleted in its entirety. Its only caller was
the replaced block; `grep -rn` over `src/` and `tests/` confirmed no
other reference before deletion.

`exc_info=True` was added to the existing `except Exception` handler's
`logger.error` call, so a raising region callback is diagnosable. The
handler is otherwise unchanged in structure and remains the containment
boundary.

The block comment was replaced. It now states the new rule — the
coordinator is consulted on every screen, and screens with no registered
regions are a no-op by construction because
`DisplayManager._register_touch_regions` clears regions on every render
pass (manager.py:1454), returns early for SPLASH (manager.py:1456) and
registers nothing for connected RADIAL (manager.py:1484) — and cites
`issue-7d4e91a3`.

The part explaining why the swipe tests precede the dispatch was
retained, but its *reason* had to be restated. The old text justified
the ordering by the OPTIONS early return it now precedes, which no
longer exists. The surviving reason is the one that still holds: a swipe
ending over a registered region would otherwise be consumed as a tap on
it, and the dispatch returns nothing that distinguishes the two.

### 3.2 EDIT B — inert DISCONNECTED branch removed

Deleted from `_handle_long_press`: the function-local `from ..core
import ThreadStatus`, the `thread_status` and `is_disconnected`
assignments, and the whole `if is_disconnected:` block with its
`logger.info` call, comments and bare return. The branch logged
"entering SETUP" and then returned without entering setup — the comment
inside it conceded as much.

The method retains its docstring, the delegating call
`self.display_manager._handle_long_press((x, y), (x, y))` (touch.py:171)
and its `except` handler.

The surviving comment was amended. The sentence "Retained without a mode
change so the disconnected early return above still runs" was removed,
that return being gone. It now records that a long press delegates on
every screen, DISCONNECTED included, where it toggles the day/night
palette as it does elsewhere, citing `issue-7d4e91a3` and
`change-2b6f4d91`, and notes where Setup is actually reached — the
DISCONNECTED screen's button, which EDIT A made live.

`ThreadStatus` does not appear anywhere in touch.py after the deletion;
it was a function-local import used by this branch alone.

The `from .models import DisplayMode` import at touch.py:26 is retained
and still used by `change_mode(DisplayMode.RADIAL)` at touch.py:288.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_touch_dispatch.py` — 15 tests covering all eight
`testing.unit_tests` scenarios and all three edge cases.

| Test | Prompt item |
|---|---|
| `test_dispatches_on_every_mode[RADIAL]` | item 1 |
| `test_dispatches_on_every_mode[ACKNOWLEDGEMENT]` | item 2 |
| `test_dispatches_on_every_mode[OPTIONS]` | item 3 |
| `test_dispatch_position_is_the_end_point` | success criterion 3 |
| `test_no_mode_test_encloses_the_dispatch` | success criterion 3 |
| `test_setup_mode_bypasses_the_dispatch` | item 4 |
| `test_swipe_down_bypasses_the_dispatch` | item 5 |
| `test_swipe_left_bypasses_the_dispatch` | item 6 |
| `test_displacement_exactly_at_threshold_is_a_swipe` | edge case 1 |
| `test_one_below_threshold_dispatches` | boundary |
| `test_exact_diagonal_falls_to_the_vertical_branch` | edge case 2 |
| `test_exception_is_logged_and_swallowed` | item 7 |
| `test_none_result_still_logs_and_does_nothing_else` | edge case 3 |
| `test_delegates_when_disconnected` | item 8 |
| `test_thread_status_is_not_consulted` | success criterion 5 |
| `test_module_no_longer_imports_thread_status` | success criterion 5 |
| `test_display_mode_still_referenced` | success criterion 8 |

Two choices in the harness worth recording:

**Both methods are called unbound against a minimal host.**
`TouchHandler.__init__` builds a real touch interface, which needs
hardware or an SDL event pump. Neither method under test touches it —
they use only `self.logger`, `self.display_manager` and
`self._handle_setup_touch` — so the tests pass a `SimpleNamespace`
supplying exactly those three. This keeps the tests on the dispatch
logic rather than on interface construction.

**The fake DisplayManager still exposes `thread_manager`.** It is unused
after EDIT B, and is kept deliberately: if the `ThreadStatus` branch were
ever reintroduced it would find something to read and
`test_delegates_when_disconnected` would then fail on the delegation
assertion rather than erroring on a missing attribute, which is the more
legible failure.

`test_no_mode_test_encloses_the_dispatch` strips comment lines before
asserting, because the comment explaining why the gate was removed names
`DisplayMode.OPTIONS` and must be free to.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

As in the two preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt` as a side effect; that file was restored
with `git checkout`.

```
$ pytest tests/
73 passed, 1 warning in 2.94s
```

The 56 tests standing at the end of `prompt-2ac1c602` iteration 2 pass
unchanged alongside the 15 new ones, `_handle_short_press` and
`_handle_long_press` being untouched by that work.

`ast.parse` succeeded on `src/gtach/display/touch.py` and the new test
file.

`git status` shows `src/gtach/display/touch.py` as the only modified
source file; `manager.py`, `touch_coordinator.py` and `models.py` do not
appear.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

All ten criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | `grep -n '_handle_options_touch' src/gtach/display/touch.py` returns no match | ✅ |
| 2 | No executable occurrence of `_handle_options_touch` in `src/` or `tests/` | ✅ see §7 |
| 3 | The `handle_touch_event` call is not enclosed by any `config.mode` test | ✅ asserted over executable lines |
| 4 | Setup branch and both swipe branches retain their early returns, otherwise unchanged | ✅ six tests |
| 5 | `grep -n 'ThreadStatus' src/gtach/display/touch.py` returns no match | ✅ |
| 6 | `grep -n 'Long press from DISCONNECTED'` returns no match | ✅ |
| 7 | `_handle_long_press` still calls `self.display_manager._handle_long_press((x, y), (x, y))` | ✅ touch.py:171 |
| 8 | `from .models import DisplayMode` retained and `DisplayMode` still referenced | ✅ touch.py:26, 288 |
| 9 | `manager.py`, `touch_coordinator.py`, `models.py` byte-identical | ✅ absent from `git status` |
| 10 | `pytest tests/` passes | ✅ 73 passed |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

One, made to satisfy a success criterion literally.

A test named `test_options_touch_helper_is_gone`, asserting `not
hasattr(TouchHandler, '_handle_options_touch')`, was written and then
removed. Criterion 2 requires that no executable occurrence of that name
remain anywhere in `src/` **or `tests/`**, and a `hasattr` guard is an
executable occurrence in `tests/`. The regression it guarded is covered
by `test_no_mode_test_encloses_the_dispatch`, which fails if the mode
gate returns in any form, so nothing was lost. The criterion is now
satisfied with `grep -rn '_handle_options_touch' src/ tests/` returning
nothing at all.

Otherwise EDITs A and B were applied as specified. The one judgement
call inside the specification was the comment rewrite described in
§3.1: the prompt asks to "retain the parts of the existing comment that
explain why the swipe tests precede the dispatch", but the existing
explanation was framed entirely in terms of the OPTIONS early return
being removed. The ordering constraint was restated on the reason that
survives the change rather than reproduced verbatim.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Findings Requiring Decision

One, and it is the intended behaviour change rather than a defect.

`_handle_short_press` now dispatches on **every** screen including
SPLASH. `_register_touch_regions` returns early for SPLASH without
clearing regions only when setup owns them; in the normal path it
clears first, so a SPLASH tap hit-tests an empty region set and returns
`None`. That is the designed no-op, but it means the correctness of the
new dispatch rests entirely on `_register_touch_regions` clearing
before every early return. That method is out of scope here and was
read, not modified. If a future edit adds an early return above the
`clear_regions()` call at manager.py:1454, stale regions from the
previous screen would become tappable on the next one. Worth a note in
`change-7d4e91a3` if that file is revisited.

The palette-toggle change on DISCONNECTED long press is deliberate,
recorded under `rational.risks` in `change-7d4e91a3`, and is not
re-raised here.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Commit Record

The instruction was to commit and push the prompt T-Doc. The closure
move is meaningless without the code it certifies, so the commit
contains the source edit, its tests, this report and the T-Doc closure
move together, and nothing else.

Not included, and left uncommitted in the working tree: `CLAUDE.md`, the
`change-2ac1c602` and `issue-2ac1c602` edits, the `change-7d4e91a3` and
`issue-7d4e91a3` T-Docs, and the `prompt-2ac1c602` iteration 2 work
(`app.py`, `main.py`, `tests/test_stack_dump_toggle.py` and its report).
These are the user's authoring work or a separate change's deliverable
and are not this prompt's to commit. See §10.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Work Remaining

**Uncommitted work from `prompt-2ac1c602` iteration 2.** That prompt did
not ask for a commit and none was made. `src/gtach/app.py`,
`src/gtach/main.py`, `tests/test_stack_dump_toggle.py`,
`ai/workspace/report/report-2ac1c602-stack-dumps-follow-runtime-debug.md`
and the closed `prompt-2ac1c602-stack-dumps-follow-runtime-debug.md`
remain in the working tree. They need a commit of their own.

**On-target verification on `gtach.local`**, per the prompt's notes,
with no reachable OBD transport:

1. Tap Setup on the DISCONNECTED screen; confirm setup mode is entered.
2. Tap Simulate; confirm simulation mode is entered.
3. Confirm the ACKNOWLEDGEMENT screen dismisses on tap.
4. Confirm a tap on the connected RADIAL gauge does nothing and logs no
   error.
5. Confirm swipe navigation and OPTIONS paging are unchanged.
6. Confirm a long press on DISCONNECTED toggles the palette — the
   intended change from EDIT B.

`issue-f3e2d1c0` and `issue-f3a7c2e1` both closed on the registration
half of this feature without verifying that a callback fired.
Verification must observe an effect on target, not a registration line
in a log. `issue-7d4e91a3` and `change-7d4e91a3` remain active until it
does.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-7d4e91a3 iteration 1: unconditional coordinator dispatch in _handle_short_press, deletion of _handle_options_touch, and removal of the inert DISCONNECTED branch from _handle_long_press, plus 15 unit tests. All ten success criteria verified. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
