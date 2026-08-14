Created: 2026 August 14

# Report: Add Entry Gate for DisplayMode.ACKNOWLEDGEMENT

---

## Table of Contents

- [1.0 Summary](<#1.0 summary>)
- [2.0 Changes Made](<#2.0 changes made>)
- [3.0 Verification](<#3.0 verification>)
- [4.0 Discrepancy Noted](<#4.0 discrepancy noted>)
- [5.0 Document Status](<#5.0 document status>)
- [Version History](<#version history>)

---

## 1.0 Summary

Implemented `prompt-e22142da-acknowledgement-screen-unreachable.md` in full.
`DisplayManager._enter_post_splash_mode()` was added to
`src/gtach/display/manager.py`, and the six unconditional
`self.config.mode = self._post_splash_mode` assignments that transition out of a
transient state (SPLASH or SETUP) into normal operation now call it instead.
`AcknowledgementStateManager.is_acknowledged()` gains its first caller, closing
the entry-half gap recorded in `issue-e22142da`.

Single-file change. No new files, no new imports, no new state, no interface
changes to existing methods.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

All edits are confined to `src/gtach/display/manager.py`.

### 2.1 New method

`_enter_post_splash_mode(self) -> None`, inserted immediately after
`_draw_splash_mode()` and before `_render_setup_mode()` (line 795). Resolution
order:

| Condition | Resulting `self.config.mode` |
|---|---|
| `self._ack_state_manager` attribute absent | `self._post_splash_mode` |
| `is_acknowledged()` returns `False` | `DisplayMode.ACKNOWLEDGEMENT` |
| `is_acknowledged()` returns `True` | `self._post_splash_mode` |
| `is_acknowledged()` raises | `DisplayMode.ACKNOWLEDGEMENT`, logged at ERROR with `exc_info=True` |

The missing-attribute branch is checked explicitly via
`getattr(self, '_ack_state_manager', None)` rather than caught as an exception,
so it is the one path that does not fail toward showing the notice — per the
prompt's rationale that a state manager which does not exist could not persist a
dismissal either. Every other failure resolves toward showing the notice.

The call passes `self.config.rpm_bands` and `self.config.engine_profile`,
matching the `is_acknowledged(rpm_bands, profile_id)` signature in
`src/gtach/utils/ack_state.py:90`.

### 2.2 Call-site substitutions

| Method | Site | Line |
|---|---|---|
| `start_splash()` | no-splash-screen branch | 660 |
| `start_splash()` | exception handler | 663 |
| `_draw_splash_mode()` | no-splash-screen early return | 771 |
| `_draw_splash_mode()` | splash-complete branch | 780 |
| `_draw_splash_mode()` | exception handler | 793 |
| `exit_setup_mode()` | sole assignment | 2566 |

### 2.3 Log-line correction

The splash-complete log at line 781 was changed from
`f"Splash completed - transitioning to {self._post_splash_mode.name}"` to
`f"Splash completed - transitioning to {self.config.mode.name}"`, read after the
gate call, so it reports ACKNOWLEDGEMENT when that is the mode actually entered.

### 2.4 Explicitly not modified

`_on_acknowledgement_dismissed()` is byte-for-byte unchanged. The `git diff`
hunk headers confirm no hunk touches it: the six hunks are at lines 660, 663,
771, 780, 793, and 2530. Its two `self.config.mode = self._post_splash_mode`
assignments (main path and exception fallback) and its own
`{self._post_splash_mode.name}` log line remain as they were — that log line is
correct in place, since the dismissal path always targets `_post_splash_mode`.

`src/gtach/utils/ack_state.py`, `models.py`, and `setup_models.py` were not
touched.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

### 3.1 Success criteria

| Criterion | Result |
|---|---|
| `grep -n '_enter_post_splash_mode'` → 7 matches (1 def + 6 call sites) | Pass — 7 |
| Six replaced sites no longer assign directly | Pass |
| `grep -n 'transitioning to {self.config.mode.name}'` matches | Pass — line 781 |
| `grep -n 'transitioning to {self._post_splash_mode.name}'` returns no match | Deviation — see §4.0 |
| `_on_acknowledgement_dismissed()` byte-for-byte unchanged | Pass |
| `python -m py_compile src/gtach/display/manager.py` | Pass |
| Full pytest suite, no new failures | Pass — 225 passed, 1 warning |

The pytest run used a throwaway venv in the session scratchpad
(`pytest`, `pytest-cov`, `pyserial`, `pygame`, `pyyaml`, `psutil`), since no
`venv/` exists in the working tree and no project dependencies are installed
system-wide. All 225 tests pass; no test in the suite asserts on
`DisplayMode.ACKNOWLEDGEMENT` entry, so no behaviour changed incidentally.

### 3.2 Unit scenarios

The four scenarios in the prompt's `testing:unit_tests`, plus an argument-
forwarding check, were exercised with an ephemeral script against a
`DisplayManager` instance built via `__new__` with a stubbed state manager.
The script lives in the session scratchpad and was not added to `tests/` — the
prompt's deliverable is `manager.py` only, and adding test files was not
requested.

| Scenario | Expected | Result |
|---|---|---|
| `is_acknowledged()` returns `False` | `ACKNOWLEDGEMENT` | Pass |
| `is_acknowledged()` returns `True` | `_post_splash_mode` | Pass |
| `is_acknowledged()` raises | `ACKNOWLEDGEMENT`, no propagation | Pass |
| `_ack_state_manager` absent | `_post_splash_mode`, no `AttributeError` | Pass |
| `rpm_bands` / `engine_profile` forwarded | Both passed through | Pass |

### 3.3 Not verified

On-device behaviour. The five `test_cases` in
`change-e22142da §testing_requirements` require manual verification on the Pi —
no automated harness exercises the splash or setup-completion transition. The
issue and change T-Docs remain active pending those results, as instructed.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Discrepancy Noted

One success criterion is arithmetically inconsistent with the design section of
the same prompt, and the design section was followed.

The criterion states that
`grep -n 'self\.config\.mode = self\._post_splash_mode'` should return "three
matches total" — two in `_on_acknowledgement_dismissed()` plus "the one inside
the newly added `_enter_post_splash_mode()` itself". The actual count is four,
because the prompt's own `design:components:logic` for
`_enter_post_splash_mode` specifies **two** such assignments in the new method:

- "If `ack_manager` is None, set `self.config.mode = self._post_splash_mode` and return."
- "After the try/except … set `self.config.mode = self._post_splash_mode`."

The functional requirements likewise mandate both branches. The implementation
therefore contains two occurrences inside the new method (lines 815 and 829) and
two inside the untouched dismiss handler (lines 2280 and 2287) — four total,
none at any of the six replaced call sites. The substantive part of the
criterion, that none of the six replaced sites still assigns directly, holds.

Similarly, the criterion that
`grep -n 'transitioning to {self._post_splash_mode.name}'` returns "no match
anywhere in the file" cannot be satisfied without editing
`_on_acknowledgement_dismissed()`, whose log line at line 2282 uses that exact
text. Editing it is forbidden by the prompt's first constraint and by
`change-e22142da §scope.out_of_scope`. The constraint was honoured and the
criterion left unmet; the corrected log line the criterion is actually aimed at
(the splash-complete one) is correct.

Neither deviation affects behaviour. Both are counting errors in the criteria
rather than defects in the change, so implementation proceeded rather than
stopping — the prompt's `notes` instruct stopping only on a mismatched count of
pre-existing `self.config.mode = self._post_splash_mode` occurrences, and that
count was exactly the eight predicted (six replaced, two untouched).

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

| Document | Status | Action |
|---|---|---|
| `prompt-e22142da` | Closed | Moved to `ai/workspace/prompt/closed/` |
| `issue-e22142da` | Active | Left open pending on-device test results |
| `change-e22142da` | Active | Left open pending on-device test results |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
