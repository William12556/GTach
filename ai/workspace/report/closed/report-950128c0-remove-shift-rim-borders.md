Created: 2026 August 13

# Report: Remove Shift Rim Borders

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Edits Applied](<#3.0 edits applied>)
- [4.0 The DISCONNECTED Screen Problem](<#4.0 the disconnected screen problem>)
- [5.0 A Pre-Existing Working-Tree Change](<#5.0 a pre-existing working-tree change>)
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
`prompt-950128c0-remove-shift-rim-borders.md` (iteration 1, coupled to
`change-950128c0` and `issue-950128c0`).

The coloured rim border drawn on every screen is removed, along with the
shift-state cue logic that fed it on RADIAL, with no replacement
indicator on any channel. RADIAL's centre disc keeps showing the active
band's colour, now read directly from `Palette.band_centres` with no
flash.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| `_draw_shift_border` deleted | ✅ |
| `_get_shift_cue` deleted | ✅ |
| Seven call sites removed | ✅ |
| `_draw_radial_mode` centre colour + r=244 face | ✅ |
| Five `Palette` fields removed from the dataclass and both instances | ✅ |
| Three test stub lines removed | ✅ |
| `pytest tests/` | ✅ 230 passed — identical to the pre-change baseline |
| Prompt T-Doc closed, committed and pushed | ✅ |

Exactly seven methods in `manager.py` differ from HEAD, two are removed,
and none is added. Verified by parsing both revisions and comparing each
function's source segment, not by reading the diff:

```
changed: _draw_acknowledgement_mode, _draw_confirm_view,
         _draw_options_menu, _draw_radial_mode,
         _draw_setup_mode_fallback, _draw_update_view,
         _render_disconnected
removed: _draw_shift_border, _get_shift_cue
added:   (none)
```

`models.py` has no function-level changes at all — only dataclass
fields, instance keywords and comments.

One edit departs from the prompt's literal instruction, and it is the
one that matters most: see §4.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 The two deleted methods

`_draw_shift_border` (37 lines with its docstring) and `_get_shift_cue`
(56 lines) are gone in full, including their `try/except` blocks. No
remaining code path can raise from the removed logic.

### 3.2 `_draw_radial_mode`

The `_get_shift_cue` call is replaced by
`centre_colour = palette.band_centres[active_band]`, with a comment
recording that the shift cue which coloured the rim and flashed this
disc went with the rim. `palette` is already bound above the call site,
so no new lookup was introduced — the "read the palette ONCE per frame"
discipline established by `change-5012004e` is preserved.

The step-1 block loses the border draw, and the background circle grows
from r=232 to r=244 so the face fills the space the rim occupied. Its
comment is rewritten to describe the two-step sequence that now runs.

The `# 6. (Border already drawn at step 1)` placeholder is deleted, and
steps 7–14 renumbered to 6–13 so the sequence stays contiguous. Two
further comments naming `_get_shift_cue` — one explaining where
`centre_colour` comes from, one asserting "White on every fill
`_get_shift_cue` returns, including the flashing dark phase" — are
reworded. The second mattered: with no flash there is no dark phase, so
the claim it made was about behaviour that no longer exists.

`border_radius = 236` is removed. It was read only by the deleted border
and became an assigned-but-never-used local — see §8 deviation 2.
`outer_radius` stays at 232 with a comment recording that the arc
geometry is deliberately unchanged despite the rim going, so the sweep
is exactly as before.

### 3.3 The five other call sites

`_draw_options_menu`, `_draw_confirm_view` and `_draw_update_view` each
lose one `self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)` line
and nothing else. All three already clear the full surface to
`_DISCONNECTED_BG_COLOUR`, so the removed call was painting the same
colour over the same area — the deletion is a visual no-op.

`_draw_acknowledgement_mode` loses the same line, and its preceding
comment drops the border reference, as specified.

`_draw_setup_mode_fallback` loses its `# Draw border` comment and its
`self._draw_shift_border((200, 0, 0), 5)` line. Worth noting what that
call actually did: `_draw_shift_border` drew a *filled* circle, so this
site painted a solid red disc of r=244 over the whole viewport *after*
rendering the "SETUP MODE" text — obliterating it. Removing the line
does not merely drop a border here, it makes a fallback screen legible
that could not previously have been read. That is a behavioural
improvement, not a regression, but it is a change to what the screen
shows.

`_render_disconnected` is the exception, discussed next.

### 3.4 `models.py`

`band_centres_lit`, `shift_border_caution`, `shift_centre_dark`,
`shift_border_normal` and `shift_border_down` are removed from the
`Palette` dataclass and from both `DAY_PALETTE` and `NIGHT_PALETTE`,
together with their explanatory comment blocks. `band_centres` is
retained unchanged on all three, as the constraint requires — it is now
the centre disc's unconditional source rather than one branch of the
cue.

The module-level comment above `DAY_PALETTE` named `_get_shift_cue`,
`band_centres_lit` and the `shift_border_*` constants; it is rewritten
to describe only what remains. This was necessary for criterion 1, which
requires no reference anywhere in `src/gtach/` — comments included.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 The DISCONNECTED Screen Problem

The prompt instructs, for `_render_disconnected`: delete the
`_draw_shift_border` line, and update or remove the preceding comment
"if the surrounding `clear_surface()` call already makes it redundant".

It does not. That method cleared to **black**, and relied on
`_draw_shift_border(self._DISCONNECTED_BG_COLOUR)` — which draws a
*filled* r=244 circle — to paint the entire pale-yellow face. Deleting
the line as written would have left the DISCONNECTED screen completely
black: no background, and black text on black.

That directly contradicts the prompt's own functional requirement that
"the six non-RADIAL screens render with no visible change from their
current appearance".

The fix taken is the minimal one that satisfies both: the `clear_surface`
colour changes from `(0, 0, 0)` to `self._DISCONNECTED_BG_COLOUR`. No
drawing call is added, and the result is pixel-identical inside the
panel's r=238 circular viewport. The corners this now paints yellow
rather than black lie outside that viewport and cannot be seen — which
is exactly the arrangement `_draw_options_menu` and the other three
OPTIONS/ACKNOWLEDGEMENT screens have used since `change-ba2d5de2`, so
this also makes the five screens consistent rather than special-casing
one.

The comment is rewritten to record all of this, so the next reader does
not restore the black clear.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 A Pre-Existing Working-Tree Change

`src/gtach/display/manager.py` again carried the uncommitted
`_render_disconnected` title y-shift — y=155 to y=145 with an
explanatory comment — that was flagged in the `ba2d5de2` report. It is
still not committed.

This prompt legitimately changes `_render_disconnected` too (§4), so the
two edits now sit in the same method, though on different lines. The
same precise-staging procedure was used: the working file was copied
aside, the y-shift reverted, `git add` run against that version, and the
full file restored. The commit therefore contains only this prompt's
work, and the y-shift remains in the working tree.

`ai/task.md` also carries an uncommitted row for `950128c0` and is
likewise excluded.

Both are left for you.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Verification Method

As in the ten preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted.

A baseline was captured **before** any edit, because criterion 6 asks
for no new failures relative to the pre-change state rather than for an
absolute number:

```
before:  230 passed, 1 warning
after:   230 passed, 1 warning
```

`ast.parse` succeeded on both edited sources.

Function-level identity was checked by parsing both revisions and
comparing each function's source segment. That is what confirmed the
change is confined to seven methods and adds none — a claim a 153-line
diff of a 2500-line file does not make legible. It is also what caught
the orphaned `border_radius` local described in §8.

The prompt's own greps all return the expected results:

```
_draw_shift_border | _get_shift_cue  in src/gtach/ and tests/   → no match
band_centres_lit | shift_border_* | shift_centre_dark in src/   → no match
band_centres:  in models.py                                     → still matches
from gtach.display.models import DAY_PALETTE, NIGHT_PALETTE     → constructs OK
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

All six criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | No `_draw_shift_border` / `_get_shift_cue` anywhere in `src/gtach/` or `tests/`, code or comment | ✅ |
| 2 | No `band_centres_lit` / `shift_border_*` / `shift_centre_dark` in `src/gtach/` | ✅ |
| 3 | `band_centres:` still present in `models.py` | ✅ line 100 |
| 4 | Both palettes construct with no `TypeError` | ✅ executed |
| 5 | The three named test modules pass | ✅ |
| 6 | Full suite passes with no new failures vs baseline | ✅ 230 before, 230 after |

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Deviations from the Prompt Specification

Three.

**1. `_render_disconnected` changes its `clear_surface` colour rather
than only losing a line.** Following the instruction literally would
have rendered the screen entirely black, contradicting the prompt's own
functional requirement. Detailed in §4. This is the one deviation that
changes what the code does rather than how it reads.

**2. `border_radius = 236` was removed from `_draw_radial_mode`.** The
prompt does not mention it, but it was read only by the deleted border,
and the technical standards require no "orphaned imports, unused local
variables, or dead comments referencing the removed methods". Leaving it
would have left an assigned-but-never-used local. `outer_radius` and
`inner_radius` are both still read and are untouched.

**3. Step comments 7–14 in `_draw_radial_mode` were renumbered to
6–13.** The prompt allows the `# 6.` placeholder to be "deleted along
with its numbered-step comment, or renumbered/reworded so the remaining
step comments stay accurate and sequential"; deleting alone would have
left a gap in the sequence, so both were done.

Beyond those, every deletion and substitution was applied as specified.
The prompt defines no unit tests — the change is a deletion — and none
were added; the three named modules had their stub lines removed and
pass unmodified otherwise.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Findings Requiring Decision

Three, none blocking.

1. **The upshift cue is gone from every channel, and that is the point.**
   Recording it plainly because it is a safety-adjacent removal made at
   the requester's explicit instruction, and the record should say so
   rather than leave it implied: RADIAL previously flashed the centre
   disc and turned the rim green above `caution_start`. Neither happens
   now, and nothing replaces them. The driver has the band colour and
   the numeric readout. `change-950128c0` carries the decision; this
   report notes only that it was carried out in full.

2. **`_draw_setup_mode_fallback` was drawing a solid red disc over its
   own text.** Described in §3.3. Removing the call fixes a screen that
   could never have been read. Nobody appears to have noticed, which
   suggests the fallback is rarely or never reached — worth knowing if
   it is ever relied on.

3. **The RADIAL face now extends to r=244 while the arcs still stop at
   r=232.** That is what the prompt specifies and it leaves no unpainted
   ring. But the 12 px annulus between them is now plain `palette.ground`
   where it was previously a saturated colour, so the gauge's outer
   edge will read as noticeably softer. The arc geometry was left
   untouched deliberately — moving it was not asked for and would change
   the sweep — but if the face reads as unfinished on the panel, growing
   `outer_radius` to 244 is the one-line follow-up, and it is a visual
   decision rather than a correctness one.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Commit Record

Committed and pushed as a single commit containing
`src/gtach/display/manager.py` (this prompt's work only — see §5),
`src/gtach/display/models.py`, the three test modules, this report and
the prompt T-Doc closure move.

Deliberately **not** included: the uncommitted `_render_disconnected`
title y-shift, and the `ai/task.md` row for `950128c0`. Both were in the
working tree before this prompt began.

The `change-950128c0` and `issue-950128c0` T-Docs are untracked in the
working tree and were left there, active, as instructed.

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Work Remaining

On-target verification on `gtach.local`:

1. Confirm no screen draws a coloured rim.
2. Confirm RADIAL's centre disc shows the band colour and never
   flashes, across idle, torque, caution, warning and danger.
3. Confirm RADIAL's face has no unpainted ring at its outer edge, and
   judge whether the plain annulus between r=232 and r=244 reads
   acceptably (§9 finding 3).
4. Confirm OPTIONS (both pages), the update and confirm-clear
   sub-views, ACKNOWLEDGEMENT and SETUP are visually unchanged.
5. **Confirm the DISCONNECTED screen still shows its pale background
   and readable text** — this is the screen whose edit departed from the
   prompt (§4), and the one that would fail most visibly if the
   reasoning there is wrong.

`issue-950128c0` and `change-950128c0` remain active pending the above.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-13 | Initial report. Implements prompt-950128c0 iteration 1: _draw_shift_border and _get_shift_cue deleted with all seven call sites, RADIAL's centre disc sourced directly from palette.band_centres and its face grown to r=244, five Palette fields removed from the dataclass and both instances, and three test stub lines removed. All six success criteria verified; 230 tests pass, identical to the captured pre-change baseline. Three deviations recorded, the significant one being _render_disconnected, where the literal instruction would have rendered the screen black. A pre-existing uncommitted y-shift and an ai/task.md row were excluded from the commit. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
