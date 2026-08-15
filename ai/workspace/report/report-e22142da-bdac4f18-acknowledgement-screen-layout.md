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

This report covers all four iterations of `change-bdac4f18`. Sections 2.1–2.3
record iterations 1–3 (commits `a00132c`, `1086061`, `60353d6`); section 2.4
describes iteration 4, the current work.

Iteration 4 implemented
`prompt-bdac4f18-acknowledgement-screen-layout.md` (iteration 4) in full: the
instruction line's text became ALL CAPS
(`"TAP TO ACKNOWLEDGE AND CONTINUE"`) and its position moved from `(240, 400)`
to `(240, 350)`. The font size call is untouched — it remains
`_get_plain_font(24)` as iteration 3 left it.

Two-literal change, a two-line diff. No new files, no new imports, no new
methods.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

All edits across the four iterations are confined to
`src/gtach/display/manager.py`, inside `_draw_acknowledgement_mode()`.

### 2.1 Iteration 1 (prior work, for context)

`_get_plain_font(self, size: int) -> Optional[pygame.font.Font]` was added
after `_get_cached_font()`, returning a size-cached `pygame.font.Font(None,
size)` — the SDL/pygame default face, bypassing `FontManager`'s
Michroma-for-every-size resolution — with creation failure caught, logged at
ERROR, and returning `None`. The body became three `_get_plain_font(18)` lines
at `y=266/290/314` and the instruction moved to `_get_plain_font(20)` at
`(240, 400)`.

### 2.2 Iteration 2 (prior work, for context)

The body block's font became `_get_plain_font(24)` and its three
`render_text()` calls became four, at coordinates pinned by an on-device
18–28px size sweep:

| y | Text |
|---|---|
| 208 | `THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT` |
| 240 | `WARRANTY OF ANY KIND. THE AUTHOR IS NOT` |
| 272 | `LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER` |
| 304 | `LIABILITY ARISING FROM ITS USE.` |

### 2.3 Iteration 3 (prior work, for context)

The instruction block's `_get_plain_font(20)` became `_get_plain_font(24)`,
matching the body text size. Text and position were unchanged at that point.

### 2.4 Iteration 4 — ALL CAPS instruction, repositioned

Two literals in the instruction block's `render_text()` call changed:

| Argument | Before | After |
|---|---|---|
| text | `"Tap to acknowledge and continue"` | `"TAP TO ACKNOWLEDGE AND CONTINUE"` |
| position | `(240, 400)` | `(240, 350)` |

`git diff -U0` produces exactly two hunks, `@@ -2281 +2281 @@` and
`@@ -2284 +2284 @@` — the text line and the position line. Nothing else in the
call changed: the font remains `instruction_font` from `_get_plain_font(24)`,
the colour remains `self._DISCONNECTED_TEXT_COLOUR`, and `center` remains
`True`.

Both literals are the values pinned by the change document's on-device probes.
Nothing was recomputed during implementation.

The change document's framing is worth restating because it is unusual: this
iteration does **not** fix a code defect. Iteration 3 already set both blocks
to size 24 via identical `_get_plain_font(24)` calls, and the reported
"instruction still looks smaller" observation was an optical effect of
cap-height versus x-height at equal point size. The body text is entirely
capitals; the iteration-3 instruction text was mostly lowercase. Matching the
body's ALL CAPS treatment resolves the perceived mismatch without touching the
font size. The reposition to y=350 is a consequence of that — ALL CAPS is
wider, which would have squeezed the margin at y=400.

### 2.5 Explicitly not modified in iteration 4

- The title block — `_get_cached_font(72)`, `"GTach"`, `(240, 120)` — line 2227.
- The body block — `_get_plain_font(24)`, four lines at `y=208/240/272/304` —
  lines 2241–2274.
- The instruction block's font size call, `_get_plain_font(24)` — line 2277.
- `_get_plain_font()` (line 2581), `_register_acknowledgement_regions()`,
  `_on_acknowledgement_dismissed()`.
- The surrounding `try` / `except Exception`, the `if instruction_font:` guard,
  and `self.logger.debug("Acknowledgement screen rendered")`.
- `FontManager`, `typography.py`, `rendering/engine.py`.

`_register_acknowledgement_regions()` needing no change was confirmed rather
than assumed: the dismiss region is a full-screen rect, independent of where
the instruction text is drawn, so moving that text does not shift the tap
target.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

### 3.1 Success criteria (iteration 4)

| Criterion | Result |
|---|---|
| `grep -n '_get_plain_font'` → 1 def + call sites, all size 24, count unchanged from iteration 3 | Sizes all 24 and count unchanged; standing deviation on the expected number — see §4.1 |
| `grep -n 'Tap to acknowledge and continue'` returns no match anywhere | Pass — 0 |
| `grep -n 'TAP TO ACKNOWLEDGE AND CONTINUE'` matches exactly once | Pass — line 2281 |
| That `render_text()` call's position is `(240, 350)`, not `(240, 400)` | Pass — line 2284 |
| Title `render_text()` for `"GTach"` at `(240, 120)` via `_get_cached_font(72)` present and unchanged | Pass — line 2227 |
| Four body `render_text()` calls at y=208/240/272/304 via `_get_plain_font(24)` present and unchanged | Pass |
| `_get_plain_font()`, `_register_acknowledgement_regions()`, `_on_acknowledgement_dismissed()` byte-for-byte unchanged | Pass — the only diff hunks are lines 2281 and 2284 |
| `python -m py_compile src/gtach/display/manager.py` | Pass |
| Full pytest suite, no new failures | Pass — 225 passed, 1 warning |

The pytest run used the throwaway scratchpad venv (`pytest`, `pytest-cov`,
`pyserial`, `pygame`, `pyyaml`, `psutil`), since no `venv/` exists in the tree.
225 passed, identical to the iteration-3 baseline; no test exercises the
acknowledgement render path.

### 3.2 Unit scenario

The prompt's single `testing:unit_tests` scenario was exercised with an
ephemeral script against a `DisplayManager` built via `__new__` with a mocked
`rendering_engine`. The script lives in the session scratchpad and was not
added to `tests/` — the prompt's deliverable is `manager.py` only.

| Scenario | Expected | Result |
|---|---|---|
| `_draw_acknowledgement_mode()` with pygame available | Instruction `render_text()` with `"TAP TO ACKNOWLEDGE AND CONTINUE"` at `(240, 350)` | Pass |
| — same run | Still uses a font from `_get_plain_font(24)` | Pass — `_plain_font_cache` keys are `[24]` only |
| — same run | Title y=120 and the four body lines y=208/240/272/304 still drawn, `center=True` throughout | Pass |
| Every font `None` | No exception propagates, zero `render_text()` calls | Pass |

### 3.3 Independent confirmation of the pinned values

**Root cause.** The change document's cap-height/x-height explanation was
re-derived from `font.metrics()` at size 24 on the macOS development host
(pygame 2.6.1, SDL 2.28.4), reproducing the `gtach.local` figures exactly:

| Glyph | Ink height above baseline |
|---|---|
| `T` | 12px |
| `W` | 12px |
| `a` | 10px |
| `o` | 9px |

Capitals reach 12px, lowercase x-height letters 9–10px — a 17–25% shortfall in
apparent height at an identical point size. The diagnosis holds.

**Fit.** Every line's width and margin was re-measured and matches the change
document to the pixel:

| y | Text | Measured width | Change doc width | Margin/side | Change doc margin |
|---|---|---|---|---|---|
| 208 | body line 1 | 396px | 396px | 37.8px | 37.8px |
| 240 | body line 2 | 388px | 388px | 44.0px | 44.0px |
| 272 | body line 3 | 381px | 381px | 45.3px | 45.3px |
| 304 | body line 4 | 277px | 277px | 90.7px | 90.7px |
| 350 | instruction | 328px | 328px | 47.1px | 47.1px |

Margins use the change document's formula — chord at the line's centre offset
from (240, 240), `2*sqrt(238² - offset²)`, margin `(chord - width) / 2`. Under
a stricter variant taking the chord at the worst-case glyph-box edge, every
line still clears, minimum 36.6px. Nothing clips the r=238 bezel.

The reposition achieves what the change document claimed: the instruction's
47.1px margin now sits inside the 37.8–90.7px range the body block already
occupies, rather than being the 12.2px outlier it would have been at y=400 in
ALL CAPS. Vertical separation between the body block's last line and the
instruction is 46px centre-to-centre (30px between glyph-box edges).

### 3.4 Not verified

On-device visual appearance. `change-bdac4f18 §testing_requirements` calls for
visual inspection on the Pi that the instruction reads in ALL CAPS, sits closer
to the disclaimer block, visually matches the body text's apparent size, and
clears the bezel. That last point is the one the arithmetic above covers well;
the "visually matches" judgement is inherently perceptual and is exactly what
this iteration exists to settle, so it genuinely needs eyes on the panel. The
issue and change T-Docs remain active pending that check, as instructed.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Discrepancies Noted

### 4.1 "Five call sites" for `_get_plain_font`

The success criterion again expects "five call sites, all at size 24". The
implementation has two lookups: one `_get_plain_font(24)` feeding the four body
`render_text()` calls, one feeding the instruction call. Iteration 4 did not
touch either, so this is inherited state, not a new deviation — and the
criterion's own qualifier ("unchanged count and sizes from iteration 3") is
satisfied exactly.

The count reflects the prompts' design sections, which have consistently
specified one guarded font lookup per block. The criterion appears to count
`render_text()` lines instead. All five rendered lines are drawn at size 24.

This is the fourth consecutive iteration carrying the same off-by-one in both
the prompt and `change-bdac4f18 §testing_requirements.validation_criteria`.
Correcting the wording in the change document would stop it recurring; that
edit is outside this prompt's scope, so it has not been made.

### 4.2 Filename collisions on closing the prompts

Each iteration's prompt reuses the same filename. Iterations 2, 3, and 4 were
closed as `prompt-bdac4f18-2-...`, `-3-`, and `-4-`, following the existing
`prompt-e1f2a3b4-<n>-...` numbering precedent in
`ai/workspace/prompt/closed/`, so all four iterations remain distinguishable.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

| Document | Status | Action |
|---|---|---|
| `prompt-bdac4f18` (iteration 1) | Closed | `ai/workspace/prompt/closed/prompt-bdac4f18-acknowledgement-screen-layout.md` |
| `prompt-bdac4f18` (iteration 2) | Closed | `ai/workspace/prompt/closed/prompt-bdac4f18-2-acknowledgement-screen-layout.md` |
| `prompt-bdac4f18` (iteration 3) | Closed | `ai/workspace/prompt/closed/prompt-bdac4f18-3-acknowledgement-screen-layout.md` |
| `prompt-bdac4f18` (iteration 4) | Closed | `ai/workspace/prompt/closed/prompt-bdac4f18-4-acknowledgement-screen-layout.md` |
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
| 4.0     | 2026-08-15 | Iteration 4: instruction line set ALL CAPS and moved to y=350 |

---

Copyright (c) 2026 William Watson. MIT License.
