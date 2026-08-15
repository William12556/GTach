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

This report covers all three iterations of `change-bdac4f18`. Sections 2.1 and
2.2 record iterations 1 and 2 (commits `a00132c` and `1086061`, prompts closed
as `prompt-bdac4f18-acknowledgement-screen-layout.md` and
`prompt-bdac4f18-2-acknowledgement-screen-layout.md`); section 2.3 describes
iteration 3, the current work.

Iteration 3 implemented
`prompt-bdac4f18-acknowledgement-screen-layout.md` (iteration 3) in full: the
instruction block's font size in
`DisplayManager._draw_acknowledgement_mode()` changed from 20px to 24px, so the
instruction line now matches the body text size. The line's text, position, and
colour are untouched.

One-token change — a single-line diff. No new files, no new imports, no new
methods.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

All edits across the three iterations are confined to
`src/gtach/display/manager.py`.

### 2.1 Iteration 1 (prior work, for context)

`_get_plain_font(self, size: int) -> Optional[pygame.font.Font]` was added
after `_get_cached_font()`, returning a size-cached `pygame.font.Font(None,
size)` — the SDL/pygame default face, bypassing `FontManager`'s
Michroma-for-every-size resolution — with creation failure caught, logged at
ERROR, and returning `None`. The body became three `_get_plain_font(18)` lines
at `y=266/290/314` and the instruction moved to `_get_plain_font(20)` at
`(240, 400)`.

### 2.2 Iteration 2 (prior work, for context)

The body block's `_get_plain_font(18)` became `_get_plain_font(24)`, and its
three `render_text()` calls became four, at the coordinates pinned by an
on-device 18–28px size sweep:

| y | Text |
|---|---|
| 208 | `THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT` |
| 240 | `WARRANTY OF ANY KIND. THE AUTHOR IS NOT` |
| 272 | `LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER` |
| 304 | `LIABILITY ARISING FROM ITS USE.` |

### 2.3 Iteration 3 — enlarged instruction line

`instruction_font = self._get_plain_font(20)` became
`self._get_plain_font(24)` (line 2277). That is the entire change: `git diff
-U0` produces exactly one hunk, `@@ -2277 +2277 @@`.

The size is the literal selected by the change document's on-device 20–40px
sweep at the fixed `y=400` position. Nothing was recomputed during
implementation. The `render_text()` call below the guard — its text
`"Tap to acknowledge and continue"`, its `(240, 400)` position, its
`center=True`, and its `self._DISCONNECTED_TEXT_COLOUR` — is byte-for-byte
unchanged.

A side effect worth recording: because `_get_plain_font()` caches by size, the
instruction line and the four body lines now share one `pygame.font.Font`
object, and `_plain_font_cache` holds a single entry (key `24`) instead of two.
This is behaviourally correct — the font is used read-only by `render_text()` —
and follows directly from the prompt's instruction to reuse the existing
caching method unchanged.

### 2.4 Explicitly not modified in iteration 3

- The title block — `_get_cached_font(72)`, `"GTach"`, `(240, 120)` — line 2227.
- The body block — `_get_plain_font(24)`, four lines at `y=208/240/272/304` —
  lines 2241–2274.
- `_get_plain_font()` (line 2581), `_register_acknowledgement_regions()`,
  `_on_acknowledgement_dismissed()`.
- The surrounding `try` / `except Exception`, the `if instruction_font:` guard,
  and `self.logger.debug("Acknowledgement screen rendered")`.
- `FontManager`, `typography.py`, `rendering/engine.py`.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

### 3.1 Success criteria (iteration 3)

| Criterion | Result |
|---|---|
| `grep -n '_get_plain_font'` → 1 def + call sites, all at size 24 | All sizes are 24; deviation on the count — see §4.1 |
| `grep -n '_get_plain_font(20)'` returns no match anywhere in the file | Pass — 0 |
| `Tap to acknowledge and continue` matches once, followed by `(240, 400)` | Pass — text line 2281, coordinate line 2284 |
| Title `render_text()` for `"GTach"` at `(240, 120)` via `_get_cached_font(72)` present and unchanged | Pass — line 2227 |
| Four body `render_text()` calls at y=208/240/272/304 via `_get_plain_font(24)` present and unchanged | Pass |
| `_get_plain_font()`, `_register_acknowledgement_regions()`, `_on_acknowledgement_dismissed()` byte-for-byte unchanged | Pass — the sole diff hunk is line 2277 |
| `python -m py_compile src/gtach/display/manager.py` | Pass |
| Full pytest suite, no new failures | Pass — 225 passed, 1 warning |

The pytest run used the throwaway scratchpad venv (`pytest`, `pytest-cov`,
`pyserial`, `pygame`, `pyyaml`, `psutil`), since no `venv/` exists in the tree.
225 passed, identical to the iteration-2 baseline; no test exercises the
acknowledgement render path.

### 3.2 Unit scenario

The prompt's single `testing:unit_tests` scenario was exercised with an
ephemeral script against a `DisplayManager` built via `__new__` with a mocked
`rendering_engine`. The script lives in the session scratchpad and was not
added to `tests/` — the prompt's deliverable is `manager.py` only.

| Scenario | Expected | Result |
|---|---|---|
| `_draw_acknowledgement_mode()` with pygame available | Instruction `render_text()` uses a font from `_get_plain_font(24)`, not `(20)` | Pass — `_plain_font_cache` keys are `[24]` only |
| — same run | Six `render_text()` calls: title y=120, body y=208/240/272/304, instruction y=400, all `center=True` | Pass |
| — same run | Instruction text and `(240, 400)` position unchanged | Pass |
| Every font `None` | No exception propagates, zero `render_text()` calls | Pass |

### 3.3 Independent confirmation of the pinned measurement

The instruction line was re-measured at 24px from `font.size()` on the macOS
development host (pygame 2.6.1, SDL 2.28.4) and compared against the change
document's `gtach.local` figure (Python 3.9.2):

| y | Size | Measured width | Change doc width | Chord margin/side | Change doc margin |
|---|---|---|---|---|---|
| 400 | 24px | 264px | 264px | 44.2px | 44.2px |

The width matches to the pixel and the margin reproduces the change document's
figure exactly using its stated formula — chord at the line's centre offset
from (240, 240), `2*sqrt(238² - offset²)`, margin `(chord - width) / 2`. A
stricter variant taking the chord at the worst-case bottom edge of the glyph
box still clears at 36.6px per side. The line does not clip the r=238 bezel.

Vertical spacing remains clear: the body block's bottom glyph edge is y=312 and
the instruction's top glyph edge is y=392, an 80px gap (down from 88px at
20px). The screen-wide minimum margin is unchanged at 37.8px, which falls on a
body line rather than the instruction.

### 3.4 Not verified

On-device visual appearance. `change-bdac4f18 §testing_requirements` calls for
visual inspection on the Pi that the instruction line reads as visibly larger,
matches the body text size, and stays clear of the bezel. The arithmetic above
is a strong predictor but is not a substitute for seeing the panel. The issue
and change T-Docs remain active pending that check, as instructed.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Discrepancies Noted

### 4.1 "Five call sites" for `_get_plain_font`

The iteration-3 success criterion expects "five call sites, all at size 24".
The implementation has two `_get_plain_font(24)` lookups: one feeding the four
body `render_text()` calls, one feeding the instruction call.

This follows the prompt's own design section verbatim, which for iteration 3
directs a single-token edit — change `20` to `24` in the existing
`instruction_font = self._get_plain_font(20)` line, with no other token
changing. Adding call sites would contradict that instruction directly. As in
iterations 1 and 2, the criterion appears to count `render_text()` lines rather
than font lookups. All five rendered lines are drawn at size 24 as intended.

The same off-by-one wording persists in
`change-bdac4f18 §testing_requirements.validation_criteria`; the change
document was not edited, as it is out of this prompt's scope. This is the third
iteration in which the criterion has been miscounted the same way — worth
correcting at the change-document level rather than re-reporting each time.

### 4.2 Filename collisions on closing the prompts

Each iteration's prompt reuses the same filename. Iterations 2 and 3 were
therefore closed as `prompt-bdac4f18-2-...` and `prompt-bdac4f18-3-...`,
following the existing `prompt-e1f2a3b4-<n>-...` numbering precedent in
`ai/workspace/prompt/closed/`, so all three iterations remain distinguishable.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

| Document | Status | Action |
|---|---|---|
| `prompt-bdac4f18` (iteration 1) | Closed | `ai/workspace/prompt/closed/prompt-bdac4f18-acknowledgement-screen-layout.md` |
| `prompt-bdac4f18` (iteration 2) | Closed | `ai/workspace/prompt/closed/prompt-bdac4f18-2-acknowledgement-screen-layout.md` |
| `prompt-bdac4f18` (iteration 3) | Closed | `ai/workspace/prompt/closed/prompt-bdac4f18-3-acknowledgement-screen-layout.md` |
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
| 3.0     | 2026-08-15 | Iteration 3: instruction line enlarged from 20px to 24px at y=400 |

---

Copyright (c) 2026 William Watson. MIT License.
