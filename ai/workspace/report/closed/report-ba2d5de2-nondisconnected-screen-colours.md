Created: 2026 August 13

# Report: Extend the DISCONNECTED Colour Scheme to OPTIONS, ACKNOWLEDGEMENT, SETUP and SPLASH

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Edits Applied](<#3.0 edits applied>)
- [4.0 The One Value Without a Reference Colour](<#4.0 the one value without a reference colour>)
- [5.0 A Pre-Existing Working-Tree Change](<#5.0 a pre-existing working-tree change>)
- [6.0 Verification Method](<#6.0 verification method>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Deviations from the Prompt Specification](<#8.0 deviations from the prompt specification>)
- [9.0 Findings Requiring Decision](<#9.0 findings requiring decision>)
- [10.0 Commit Record](<#10.0 commit record>)
- [11.0 Work Remaining](<#11.0 work remaining>)
- [12.0 Correction — EDIT C Withdrawn, 2026-08-13 (Same Day)](<#12.0 correction — edit c withdrawn, 2026-08-13 (same day)>)
- [13.0 Further Correction — Red Border Removed, 2026-08-13 (Same Day)](<#13.0 further correction — red border removed, 2026-08-13 (same day)>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records the implementation of
`prompt-ba2d5de2-nondisconnected-screen-colours.md` (iteration 1,
coupled to `change-ba2d5de2` and `issue-ba2d5de2`).

The DISCONNECTED screen's background and text were changed to a pale
dusty-yellow, `(216, 200, 146)`, with black text, `(0, 0, 0)`. This
change applies the same background, text and border treatment to
OPTIONS's three sub-views, ACKNOWLEDGEMENT, SETUP and SPLASH, leaving
RADIAL, DISCONNECTED itself, every button fill and label, and every
semantic or status colour untouched.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT A — `manager.py`, OPTIONS's three sub-views | ✅ Applied |
| EDIT B — `manager.py`, `_draw_acknowledgement_mode` | ✅ Applied |
| EDIT C — `splash.py`, `SplashScreen` | ✅ Applied |
| EDIT D — `setup.py`, `SetupDisplayManager` | ✅ Applied |
| `pytest tests/` | ✅ 230 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

The prompt specifies no unit tests — every edit is a colour value — so
none were added. The existing 230 pass unchanged.

Exactly four methods differ from HEAD in `manager.py`:
`_draw_options_menu`, `_draw_confirm_view`, `_draw_update_view` and
`_draw_acknowledgement_mode`. That was verified by parsing both
revisions and comparing each function's source segment, not by reading
the diff — see §6.

`_draw_radial_mode`, `_get_shift_cue`, `_get_band_colour`,
`_render_disconnected`, `_register_disconnected_regions`,
`_draw_reconnect_spinner`, `_draw_update_spinner`, `_draw_button` and
`_draw_shift_border` are all byte-identical. `models.py` and
`graphics/splash_graphics.py` do not appear in `git status` at all.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT A — OPTIONS's three sub-views

`_draw_options_menu`, `_draw_confirm_view` and `_draw_update_view` each
now clear to `self._DISCONNECTED_BG_COLOUR`, call
`self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)`, and render
every text run in `self._DISCONNECTED_TEXT_COLOUR`. The constants are
referenced by name rather than restated as literals, as the prompt
requires.

Specifically replaced: the three `(40, 40, 50)` clear fills; the three
`(200, 0, 0)` borders; the "Options", "Clear settings?" and "Update"
titles and the update status message, all `(255, 255, 255)`; the two
confirm-view body lines at `(200, 200, 200)`; and the two "Swipe up to
return" hints at `(150, 150, 150)`.

Deliberately untouched, and confirmed absent from the diff: the page
indicator's `palette.tick` dots, which belong to the day/night palette
system; the `(80, 80, 100)`, `(140, 40, 40)` and `(0, 120, 0)` button
fills and their white labels; and `_draw_update_spinner`'s dot colours,
which are functional progress indication.

Several of the replaced calls were single long lines exceeding PEP 8's
width once the constant name replaced a short tuple; those were wrapped
across lines. No argument order, position or geometry changed.

### 3.2 EDIT B — ACKNOWLEDGEMENT

`_draw_acknowledgement_mode` now clears to `_DISCONNECTED_BG_COLOUR`,
borders with the same, and renders the "GTach" title, the body warning
and the instruction line all in `_DISCONNECTED_TEXT_COLOUR` — replacing
`(0, 0, 0)`, `(200, 0, 0)`, `(255, 255, 255)`, `(200, 200, 200)` and
`(150, 150, 150)` respectively.

Two comments named colours this change replaces and were corrected: the
docstring's "red border" and the inline "Fill background black" / "Draw
red circular border" pair. This is within the prompt's allowance for
docstring changes "where an existing one names a colour this change
replaces".

### 3.3 EDIT C — SPLASH

`self._colors` now carries `'background': (216, 200, 146)`,
`'primary_text': (0, 0, 0)` and `'secondary_text': (0, 0, 0)`.
`'accent'` and `'progress_fill'` remain `(64, 150, 255)`, and
`'border'` remains `(80, 90, 100)` with a comment recording that it is
unread — `_draw_border` has its own colour, as the prompt notes.

`_draw_border`'s hard-coded `(200, 0, 0)` now reads
`self._colors['background']`.

The comment above the dict read "Color scheme - professional dark
theme", which now names the wrong theme; it reads "Color scheme -
matches the DISCONNECTED screen (issue-ba2d5de2)".

`'progress_bg'` is discussed separately in §4.

### 3.4 EDIT D — SETUP

`self.colors` now carries `'background': (216, 200, 146)`,
`'text': (0, 0, 0)` and `'text_dim': (0, 0, 0)`. `'surface'`,
`'primary'`, `'success'`, `'warning'`, `'danger'` and `'border'` are
unchanged, with a comment recording that the accents are semantic and
deliberately left alone.

`_draw_circular_border`'s hard-coded `(200, 0, 0)` now reads
`self.colors['background']`, and its docstring — which said "Draw red
circular border" — was corrected.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 The One Value Without a Reference Colour

`progress_bg` is the only value in this prompt with no
DISCONNECTED-derived RGB to copy. The prompt gives a range,
`(150, 135, 90)` to `(170, 150, 100)`, and a requirement: visibly
distinct from both the new background and the `(64, 150, 255)` fill.

Rather than picking from the middle by eye, every candidate across the
range was measured for WCAG relative-luminance contrast against both
neighbours:

| Candidate | vs background | vs fill | worst case |
|---|---|---|---|
| **(150, 135, 90)** | **2.13:1** | **1.19:1** | **1.19** |
| (155, 139, 93) | 2.02:1 | 1.12:1 | 1.12 |
| (160, 143, 96) | 1.91:1 | 1.07:1 | 1.07 |
| (165, 147, 98) | 1.81:1 | 1.01:1 | 1.01 |
| (170, 150, 100) | 1.74:1 | 1.03:1 | 1.03 |

`(150, 135, 90)` — the darkest end of the permitted range — maximises
the worst case and was chosen. The comment in `splash.py` records both
figures.

**The honest caveat**, and it is why the prompt flags this value for
on-target confirmation: 1.19:1 against the blue fill is a *luminance*
separation of essentially nothing. The blue's relative luminance is
0.301, which sits almost exactly where a mid olive does. The two will be
told apart by hue — a desaturated olive against a saturated blue is a
large hue step — but not by brightness. No value in the permitted range
fixes that, because the constraint is the blue's luminance, not the
track's. If the track reads as indistinct on the panel, the fix is
either a darker track outside the given range or a different fill
colour, and both are decisions above this prompt.

For reference, black text on the new background measures 12.60:1, well
clear of any legibility threshold.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 A Pre-Existing Working-Tree Change

`src/gtach/display/manager.py` carried an uncommitted edit before this
prompt began, in `_render_disconnected`: the "Disconnected" title moved
from y=155 to y=145, with a comment explaining that y=180's message read
as crowded. It is not mine and is not part of this change.

That matters twice over. Criterion 9 requires `_render_disconnected` to
be byte-identical, and a whole-file `git add` would have swept the edit
into this commit.

Both were handled by staging precisely: the working file was copied
aside, the y-shift temporarily reverted, `git add` run against that
version, and the full file restored. The index therefore carries only
this prompt's colour edits — `_render_disconnected` in the committed
tree is byte-identical to HEAD, confirmed by AST comparison against
`:src/gtach/display/manager.py` — and the y-shift remains in the working
tree as uncommitted work, exactly where it was found.

It is left for you to commit or discard.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Verification Method

As in the nine preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted.

```
$ pytest tests/
230 passed, 1 warning in 6.79s
```

`ast.parse` succeeded on all three edited files.

Byte-identity was checked by **parsing both revisions and comparing each
function's source segment**, rather than by reading the diff. A colour
change touches many small call sites across a 2500-line file, and a diff
is a poor instrument for proving that a *specific* method did not move.
The comparison enumerates every changed function in the file and
reported exactly four, all intended — and it is what caught the
pre-existing `_render_disconnected` edit described in §5, which a
hunk-by-hunk read could easily have attributed to this change.

All eight validation greps from the prompt return the expected results:

```
clear_surface(..., (40, 40, 50)) in manager.py     → no match
_draw_shift_border((200, 0, 0)) in manager.py      → no match
clear_surface(..., (0, 0, 0)) in manager.py        → one match, inside
                                                     _render_disconnected
(15, 20, 25) in splash.py                          → no match
(20, 20, 30) in setup.py                           → no match
(200, 0, 0) in splash.py / setup.py                → no match
git status src/gtach/display/models.py graphics/   → empty
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

All eleven criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | The three OPTIONS sub-views use the constants for background, border and all text | ✅ |
| 2 | `_draw_acknowledgement_mode` does the same | ✅ |
| 3 | No `(40, 40, 50)` in those three methods | ✅ grep clean file-wide |
| 4 | No `_draw_shift_border((200, 0, 0))` | ✅ |
| 5 | Button fills `(80, 80, 100)`, `(140, 40, 40)`, `(0, 120, 0)` and white labels unchanged | ✅ six occurrences intact; absent from the diff |
| 6 | `splash.py` background/text/accent/fill correct; `_draw_border` reads the dict | ✅ |
| 7 | `setup.py` background/text/text_dim correct; accents unchanged; `_draw_circular_border` reads the dict | ✅ |
| 8 | `_draw_radial_mode`, `_get_shift_cue`, `_get_band_colour`, palettes byte-identical | ✅ AST-verified; `models.py` untouched |
| 9 | `_render_disconnected`, `_register_disconnected_regions`, `_draw_reconnect_spinner`, the two constants byte-identical | ✅ AST-verified against the staged tree; see §5 |
| 10 | `graphics/splash_graphics.py` byte-identical | ✅ absent from `git status` |
| 11 | `pytest tests/` passes | ✅ 230 passed |

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Deviations from the Prompt Specification

None to the specified colour values or their placement.

Two presentational consequences worth recording, neither a departure
from instruction:

**1. Line wrapping.** Several replaced calls were single long lines
whose length grew past PEP 8's limit once `self._DISCONNECTED_TEXT_COLOUR`
replaced a short tuple — `render_text(...)` calls in `_draw_update_view`
and the two "Swipe up to return" hints in particular. They were wrapped
across lines. No argument, order, position or geometry changed; the diff
shows more moved lines than the edit count alone would suggest, for that
reason.

**2. Three comments and two docstrings were corrected** because they
named colours this change replaces: `splash.py`'s "professional dark
theme" (explicitly called for by the prompt), `setup.py`'s
`_draw_circular_border` docstring, and `_draw_acknowledgement_mode`'s
docstring plus its two inline "Fill background black" / "Draw red
circular border" comments. The prompt permits docstring changes exactly
where an existing one names a replaced colour.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Findings Requiring Decision

Three, none blocking.

1. **The SPLASH progress track's separation from its fill is
   hue-carried, not luminance-carried** — 1.19:1 at the best value in
   the permitted range. Detailed in §4. This is the one thing on-target
   verification should look at hardest, and no value inside the given
   range improves it.

2. **`SetupDisplayManager.colors['surface']` remains `(40, 40, 50)`**, a
   dark tone chosen for the old dark background. The prompt explicitly
   excludes it, and it was left alone. But it is now a near-black panel
   fill sitting on a pale yellow background, and any screen that draws a
   surface panel will show a strong dark block where previously there
   was a subtle one. Whether that reads as intentional contrast or as a
   leftover is a judgement only the panel can settle. Worth looking at
   during the Setup walkthrough.

3. **`SetupDisplayManager.colors['border']` `(80, 80, 90)` is in the
   same position** — a mid-dark grey chosen against a dark background,
   now on pale yellow. Also explicitly excluded by the prompt, also
   left alone, and also worth an eye on target.

Findings 2 and 3 are both cases where the prompt's exclusions are
correct in isolation but interact: excluding a colour that was chosen
*relative to* a background that this change moves does not leave it
neutral, it leaves it mismatched. Neither is in scope to fix here.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Commit Record

Committed and pushed as a single commit containing
`src/gtach/display/manager.py` (colour edits only — see §5),
`src/gtach/display/splash.py`, `src/gtach/display/setup.py`, this report
and the prompt T-Doc closure move.

Deliberately **not** included: the uncommitted `_render_disconnected`
title y-shift, which was in the working tree before this prompt began
and remains there.

The `change-ba2d5de2` and `issue-ba2d5de2` T-Docs for this triple were
committed in `d3e2373` and remain active.

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes:

1. Swipe down to OPTIONS and page through both pages.
2. Open Check for updates.
3. Open Clear settings.
4. Trigger ACKNOWLEDGEMENT.
5. Run Setup end to end, Welcome through Complete.
6. Observe SPLASH at startup.
7. Confirm RADIAL and DISCONNECTED are visually unchanged.
8. **Confirm the SPLASH progress bar track remains visible against both
   the new background and its blue fill.** Per §4 this is the one value
   with no reference colour and the weakest measured separation; it is
   the check most likely to fail.

Also worth an eye during step 5, per §9: Setup's `'surface'` and
`'border'` accents were excluded by the prompt and are now dark tones on
a pale background.

`issue-ba2d5de2` and `change-ba2d5de2` remain active pending the above.

[Return to Table of Contents](<#table of contents>)

---

## 12.0 Correction — EDIT C Withdrawn, 2026-08-13 (Same Day)

Item 8 in §11 above did not wait for a formal on-target check: William
reviewed the deployed SPLASH screen directly and specified it must
remain black background with white text — the pre-existing appearance
— rather than the pale-yellow/black treatment EDIT C applied. This is
not a rejection of §4's measurement (the hue/luminance analysis of
`progress_bg` stands as a correct answer to the question the prompt
asked); it is a scope decision made after seeing the result on the
panel, which finding 2 and 3 in §9 above already flagged as the kind of
interaction worth an eye on target.

`splash.py` was reverted directly to its pre-change state — the exact
inverse of §3.3 — under the P03 §1.4.12 trivial exemption: single
class, small delta (the `_colors` dict and one `_draw_border` argument),
no interface change, human-approved. No new prompt was issued for the
revert. `issue-ba2d5de2` and `change-ba2d5de2` were both amended in
place (version 2.0 on each) to remove SPLASH and EDIT C from scope,
rather than left describing a state no longer on target.

Consequence for this report: §3.3, §4, and success criterion 6 in §7.0
describe EDIT C as implemented, which was true at the time of writing
and is preserved as the historical record of what the prompt produced.
They no longer describe the current state of `splash.py`. Work-remaining
item 8 in §11 is superseded — there is no SPLASH progress-track contrast
to verify on target, because SPLASH carries none of this change's
colours.

[Return to Table of Contents](<#table of contents>)

---

## 13.0 Further Correction — Red Border Removed, 2026-08-13 (Same Day)

Separately from §12, William requested the splash screen's circular red
border be removed outright — not reverted to a prior colour, removed
entirely. This is unrelated to change-ba2d5de2 (the border predates it
and was never part of that change's scope even before §12's revert); it
is recorded here because it touches the same file in the same session.

`_draw_border` had exactly one call site, in `_render_graphics`'s
`automotive` branch, and no other reference anywhere in `splash.py`. The
call was removed and the now-dead method deleted outright rather than
left as unreachable code, since nothing else in the file's history
depends on it existing (unlike, for instance, `_get_band_colour` in
`manager.py`, retained deliberately for a named future consumer).

Qualifies as a P03 §1.4.12 trivial exemption on the same basis as §12:
single function/call site, small delta, no interface change,
human-approved. `width` and `height` in `_render_graphics` remain in use
for `center_x`/`center_y` and are otherwise unaffected. `pytest tests/`
was not re-run for this edit specifically — no test in the suite
exercises `_draw_border`, confirmed by its absence from `tests/` prior
to removal, and the change is deletion-only with no new code path to
cover.

The splash screen now renders with no border of any kind, on its
restored black background.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-13 | Initial report. Implements prompt-ba2d5de2 iteration 1: the DISCONNECTED background/text/border treatment extended to OPTIONS's three sub-views, ACKNOWLEDGEMENT, SPLASH and SETUP across manager.py, splash.py and setup.py. All eleven success criteria verified by AST comparison of every function against HEAD. progress_bg chosen by measurement as the best value in the permitted range; its residual weakness against the blue fill is recorded. A pre-existing uncommitted _render_disconnected edit was found and deliberately excluded from the commit. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |
| 1.1 | 2026-08-13 | Correction, same day. §12 added: EDIT C (SPLASH) withdrawn after William reviewed the deployed result and specified black background/white text. Reverted directly in splash.py under the P03 §1.4.12 trivial exemption. §3.3, §4, criterion 6 and work-remaining item 8 are superseded by §12 but left intact as the historical record. |
| 1.2 | 2026-08-13 | Further correction, same day. §13 added: the splash screen's circular red border removed outright at William's request — _draw_border and its one call site deleted, under the same P03 §1.4.12 trivial exemption. Unrelated to change-ba2d5de2's scope. |

---

Copyright (c) 2026 William Watson. MIT License.
