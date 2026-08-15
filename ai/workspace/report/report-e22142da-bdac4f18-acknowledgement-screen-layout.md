Created: 2026 August 14

# Report: Rewrite Acknowledgement Screen Layout

---

## Table of Contents

- [1.0 Summary](<#1.0 summary>)
- [2.0 Changes Made](<#2.0 changes made>)
- [3.0 Verification](<#3.0 verification>)
- [4.0 Discrepancies Noted](<#4.0 discrepancies noted>)
- [5.0 Document Status](<#5.0 document status>)
- [Version History](<#version history>)

---

## 1.0 Summary

This report covers both iterations of `change-bdac4f18`. Section 2.1 records
iteration 1 (delivered in commit `a00132c`, prompt now at
`ai/workspace/prompt/closed/prompt-bdac4f18-acknowledgement-screen-layout.md`);
sections 2.2 onward describe iteration 2, the current work.

Iteration 2 implemented
`prompt-bdac4f18-acknowledgement-screen-layout.md` (iteration 2) in full: the
body block of `DisplayManager._draw_acknowledgement_mode()` in
`src/gtach/display/manager.py` was replaced — three 18px lines at
`y=266/290/314` became four 24px lines at `y=208/240/272/304`, enlarging the
disclaimer and raising it to sit immediately below the title's measured
bounding box.

Single-method change. No new files, no new imports, no new methods. The title
block, the instruction block, `_get_plain_font()`,
`_register_acknowledgement_regions()`, and `_on_acknowledgement_dismissed()`
are all byte-for-byte unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

All edits are confined to `src/gtach/display/manager.py`.

### 2.1 Iteration 1 (prior work, for context)

`_get_plain_font(self, size: int) -> Optional[pygame.font.Font]` was added
after `_get_cached_font()`, returning a size-cached `pygame.font.Font(None,
size)` — the SDL/pygame default face, bypassing `FontManager`'s
Michroma-for-every-size resolution — with creation failure caught, logged at
ERROR, and returning `None`. The body became three `_get_plain_font(18)` lines
at `y=266/290/314` and the instruction moved to `_get_plain_font(20)` at
`(240, 400)`. Iteration 2 leaves `_get_plain_font()` and the instruction block
untouched.

### 2.2 Iteration 2 — rewritten body block

The body block's single `_get_plain_font(18)` call became
`_get_plain_font(24)`, and its three `render_text()` calls became four, all
`center=True` at `x=240` in `self._DISCONNECTED_TEXT_COLOUR`:

| y | Text |
|---|---|
| 208 | `THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT` |
| 240 | `WARRANTY OF ANY KIND. THE AUTHOR IS NOT` |
| 272 | `LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER` |
| 304 | `LIABILITY ARISING FROM ITS USE.` |

The text, size, and coordinates are the literals pinned in
`change-bdac4f18 §technical_details` (iteration 2), measured on `gtach.local`
via an 18–28px size sweep. Nothing was recomputed or re-wrapped during
implementation. The first line retains single outer quotes so the embedded
`"AS IS"` double quotes are preserved verbatim without escaping. The comment
above the block, which already cites the change document as the source of the
pinned coordinates, was left as-is.

### 2.3 Explicitly not modified

- The title block — `_get_cached_font(72)`, `"GTach"`, `(240, 120)` — line 2227.
- The instruction block — `_get_plain_font(20)`,
  `"Tap to acknowledge and continue"`, `(240, 400)` — lines 2277–2286.
- `_get_plain_font()` (line 2581), `_register_acknowledgement_regions()`,
  `_on_acknowledgement_dismissed()`.
- The surrounding `try` / `except Exception`, the `if body_font:` guard
  structure, and `self.logger.debug("Acknowledgement screen rendered")`.
- `FontManager`, `typography.py`, `rendering/engine.py`.

`git diff -U0` confirms it: every hunk in this iteration falls between old-file
lines 2241 and 2264, entirely inside the body block.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

### 3.1 Success criteria

| Criterion | Result |
|---|---|
| `grep -n '_get_plain_font'` → 1 def + call sites | Deviation on the count — see §4.1 |
| `grep -n '_get_plain_font(18)'` returns no match | Pass — 0 |
| `THIS SOFTWARE IS PROVIDED` matches once, centred at y=208 | Pass — text line 2245, coordinate line 2248 |
| `LIABILITY ARISING FROM ITS USE` matches once, centred at y=304 | Pass — text line 2269, coordinate line 2272 |
| `Tap to acknowledge and continue` matches once, followed by `(240, 400)` | Pass — line 2281, coordinate line 2284 |
| Title `render_text()` for `"GTach"` at `(240, 120)` via `_get_cached_font(72)` present and unchanged | Pass — line 2227 |
| `_get_plain_font()`, `_register_acknowledgement_regions()`, `_on_acknowledgement_dismissed()` byte-for-byte unchanged | Pass — confirmed by hunk headers |
| `python -m py_compile src/gtach/display/manager.py` | Pass |
| Full pytest suite, no new failures | Pass — 225 passed, 1 warning |

The pytest run used the throwaway scratchpad venv (`pytest`, `pytest-cov`,
`pyserial`, `pygame`, `pyyaml`, `psutil`), since no `venv/` exists in the tree.
225 passed, identical to the pre-change baseline; no test exercises the
acknowledgement render path.

### 3.2 Unit scenario

The prompt's single `testing:unit_tests` scenario was exercised with an
ephemeral script against a `DisplayManager` built via `__new__` with a mocked
`rendering_engine`. The script lives in the session scratchpad and was not
added to `tests/` — the prompt's deliverable is `manager.py` only.

| Scenario | Expected | Result |
|---|---|---|
| `_draw_acknowledgement_mode()` with pygame available | Four body `render_text()` calls at y=208/240/272/304 | Pass |
| — same run | All four use the one font object from `_get_plain_font(24)` | Pass |
| — same run | Title at y=120 and instruction at y=400 still drawn, `center=True` throughout | Pass |
| Every font `None` | No exception propagates, zero `render_text()` calls | Pass |

### 3.3 Independent confirmation of the pinned measurements

Each line's rendered width was re-derived from `font.size()` on the macOS
development host (pygame 2.6.1, SDL 2.28.4) and compared against the change
document's on-device table (Python 3.9.2 on `gtach.local`):

| y | Measured width | Change doc width | Chord margin/side | Change doc margin |
|---|---|---|---|---|
| 208 | 396px | 396px | 37.8px | 37.8px |
| 240 | 388px | 388px | 44.0px | 44.0px |
| 272 | 381px | 381px | 45.3px | 45.3px |
| 304 | 277px | 277px | 90.7px | 90.7px |
| 400 | 215px | 215px | 68.7px | 68.7px |

Every width matches to the pixel, and the margins reproduce the change
document's figures exactly using its stated formula — chord at the line's
centre offset from (240, 240), `2*sqrt(238² - offset²)`, margin
`(chord - width) / 2`. A stricter variant that takes the chord at the worst-case
top/bottom edge of each glyph box rather than at the line centre still clears
on every line, with a minimum of 36.6px per side. No line clips the r=238
bezel.

Vertical spacing is also clear: the body block spans y=200 to y=312 (glyph-box
edges), leaving 88px of empty space before the instruction line's top edge at
y=393, and the block's top sits well below the title's measured bottom of
y=172.

### 3.4 Not verified

On-device visual appearance. `change-bdac4f18 §testing_requirements` calls for
visual inspection on the Pi that no text clips the bezel and that the body
block reads as visibly larger and closer to the title than iteration 1. The
arithmetic above is a strong predictor but is not a substitute for seeing the
panel. The issue and change T-Docs remain active pending that check, as
instructed.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Discrepancies Noted

### 4.1 "Five call sites" for `_get_plain_font`

The iteration-2 success criterion expects "five call sites (four at size 24,
one at size 20)". The implementation has two: one `_get_plain_font(24)` whose
result feeds all four body `render_text()` calls, and one
`_get_plain_font(20)`.

This follows the prompt's own design section verbatim — `"body_font =
self._get_plain_font(24)" followed by an "if body_font:" guard containing four
render_text() calls` — which specifies a single font lookup guarded once,
feeding four renders. As in iteration 1, the criterion appears to have counted
`render_text()` lines rather than font lookups. Calling `_get_plain_font(24)`
four times would be redundant given the method's caching and would break the
single `if body_font:` guard the design prescribes. All four rendered lines, at
the specified size and coordinates, are present.

The same off-by-one wording appears in
`change-bdac4f18 §testing_requirements.validation_criteria`; the change
document was not edited to correct it, as it is out of this prompt's scope.

### 4.2 Filename collision on closing the prompt

The iteration-2 prompt shares its filename with the closed iteration-1 prompt
already in `ai/workspace/prompt/closed/`. It was closed as
`prompt-bdac4f18-2-acknowledgement-screen-layout.md`, following the existing
`prompt-e1f2a3b4-<n>-...` numbering precedent in that folder, so both
iterations remain distinguishable.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

| Document | Status | Action |
|---|---|---|
| `prompt-bdac4f18` (iteration 1) | Closed | Previously moved to `ai/workspace/prompt/closed/` |
| `prompt-bdac4f18` (iteration 2) | Closed | Moved to `ai/workspace/prompt/closed/prompt-bdac4f18-2-acknowledgement-screen-layout.md` |
| `issue-bdac4f18` | Active | Left open pending on-device visual check |
| `change-bdac4f18` | Active | Left open pending on-device visual check |
| `issue-e22142da` | Active | Unchanged by this work; still pending its own test results |
| `change-e22142da` | Active | Unchanged by this work; still pending its own test results |

`change-bdac4f18` declares `change-e22142da` as `blocked_by`. That dependency is
satisfied — `change-e22142da` was implemented in commit `684aa67`, so
`DisplayMode.ACKNOWLEDGEMENT` is reachable and this screen can render.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation (iteration 1) |
| 2.0     | 2026-08-15 | Iteration 2: 24px four-line body block at y=208/240/272/304 |

---

Copyright (c) 2026 William Watson. MIT License.
