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

Implemented `prompt-bdac4f18-acknowledgement-screen-layout.md` in full.
`DisplayManager._get_plain_font(size)` was added to
`src/gtach/display/manager.py`, and the body and instruction text of
`_draw_acknowledgement_mode()` were replaced with four pinned lines drawn in the
SDL default font at the coordinates measured on `gtach.local` and recorded in
`change-bdac4f18 §technical_details`.

Single-file change. No new files, no new imports, no change to `FontManager` or
`typography.py`, and no change to any other screen's rendering.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

All edits are confined to `src/gtach/display/manager.py`.

### 2.1 New method

`_get_plain_font(self, size: int) -> Optional[pygame.font.Font]`, inserted
immediately after `_get_cached_font()` (line 2573). Returns
`pygame.font.Font(None, size)` — the SDL/pygame default face, bypassing
`FontManager`'s Michroma-for-every-size resolution — cached by size in
`self._plain_font_cache`. On a size already cached it returns the same object
without reconstructing it. Font creation failure is caught, logged at ERROR, and
returns `None`.

The cache is initialised in `__init__` alongside `self._registered_view`
(line 143), and additionally resolved lazily via
`getattr(self, '_plain_font_cache', None)` inside the method — the prompt
permits either; both are present so the method is also safe on an instance
constructed without `__init__` having run.

### 2.2 Rewritten render blocks

The body block — one `_get_cached_font(24)` call and one `render_text()` for
`"OBD tachometer — experimental software"` at `(240, 240)` — was replaced by a
single `_get_plain_font(18)` call guarded by `if body_font:`, followed by three
`render_text()` calls, all `center=True` in `self._DISCONNECTED_TEXT_COLOUR`:

| y | Text |
|---|---|
| 266 | `THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY` |
| 290 | `OF ANY KIND. THE AUTHOR IS NOT LIABLE FOR ANY CLAIM,` |
| 314 | `DAMAGES, OR OTHER LIABILITY ARISING FROM ITS USE.` |

The instruction block now uses `_get_plain_font(20)` and draws
`"Tap to acknowledge and continue"` at `(240, 400)`, moved from `(240, 360)`.

The first body line is written with single outer quotes so the embedded
`"AS IS"` double quotes are preserved verbatim without escaping.

### 2.3 Explicitly not modified

- The title block — `_get_cached_font(72)`, `"GTach"`, `(240, 120)` — is
  unchanged (line 2227).
- `_register_acknowledgement_regions()` (line 1681) and
  `_on_acknowledgement_dismissed()` are byte-for-byte unchanged. The `git diff`
  hunk headers confirm it: hunks fall at old-file lines 142, 2233–2253, and
  2549, none of which touch either method.
- The surrounding `try` / `except Exception` and the
  `self.logger.debug("Acknowledgement screen rendered")` line are as they were.
- `FontManager`, `typography.py`, and `rendering/engine.py` were not touched.
- `DISCLAIMER.md` was not created or modified — it already exists at the
  repository root and is explicitly out of scope per
  `change-bdac4f18 §scope.out_of_scope` (repository-root documents fall outside
  the `src/` T-Doc workflow).

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

### 3.1 Success criteria

| Criterion | Result |
|---|---|
| `grep -n '_get_plain_font'` → 1 def + call sites | Deviation on the count — see §4.1 |
| `grep -n 'OBD tachometer'` returns no match | Pass — 0 |
| `grep -n 'THIS SOFTWARE IS PROVIDED'` matches once | Pass — 1 |
| `Tap to acknowledge and continue` matches once, followed by `(240, 400)` | Pass — line 2273, coordinate at 2276 |
| Title `render_text()` for `"GTach"` at `(240, 120)` via `_get_cached_font(72)` present and unchanged | Pass — line 2227 |
| `_register_acknowledgement_regions()` / `_on_acknowledgement_dismissed()` byte-for-byte unchanged | Pass |
| `python -m py_compile src/gtach/display/manager.py` | Pass |
| Full pytest suite, no new failures | Pass — 225 passed, 1 warning |

The pytest run used the throwaway scratchpad venv (`pytest`, `pytest-cov`,
`pyserial`, `pygame`, `pyyaml`, `psutil`), since no `venv/` exists in the tree.
225 passed, identical to the pre-change baseline; no test exercises the
acknowledgement render path.

### 3.2 Unit scenarios

Both scenarios from the prompt's `testing:unit_tests`, plus three additional
checks, were exercised with an ephemeral script against a `DisplayManager` built
via `__new__`. The script lives in the session scratchpad and was not added to
`tests/` — the prompt's deliverable is `manager.py` only.

| Scenario | Expected | Result |
|---|---|---|
| `_get_plain_font(18)` called twice | Second call returns the identical cached object | Pass |
| `_plain_font_cache` absent on the instance | Lazily created, no `AttributeError` | Pass |
| `pygame.font.Font` raises | Returns `None`, logged, no propagation | Pass |
| `_draw_acknowledgement_mode()` with every font `None` | No exception propagates, no `render_text()` call attempted | Pass |
| Pinned coordinates vs. the r=238 viewport | Every line clears with positive margin | Pass |

### 3.3 Independent confirmation of the pinned measurements

The fit check re-derived each line's rendered width from `font.size()` and
computed the chord margin as
`(2*sqrt(238² - offset²) - width) / 2`, reproducing the change document's
on-device table exactly:

| y | Measured width | Chord | Margin/side | Change doc margin |
|---|---|---|---|---|
| 266 | 369px | 473.2px | 52.1px | 52.1px |
| 290 | 359px | 465.4px | 53.2px | 53.2px |
| 314 | 341px | 452.4px | 55.7px | 55.7px |
| 400 | 215px | 352.4px | 68.7px | 68.7px |

This was run on the macOS development host (pygame 2.6.1, SDL 2.28.4) rather
than on `gtach.local` (Python 3.9.2), and the figures match to the pixel — the
pinned coordinates are consistent across both environments. Smallest margin is
52.1px per side; no line clips.

### 3.4 Not verified

On-device visual appearance. `change-bdac4f18 §testing_requirements` calls for
visual inspection on the Pi that no text clips the bezel, plus a re-run of the
measurement script against the deployed build. The arithmetic above is a strong
predictor but is not a substitute for seeing the panel. The issue and change
T-Docs remain active pending that check, as instructed.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Discrepancies Noted

Two minor inconsistencies within the prompt; in both cases the design section
was followed over the conflicting text, and neither affects behaviour.

### 4.1 "Four call sites" for `_get_plain_font`

The success criterion expects "four call sites (three at size 18, one at size
20)". The implementation has two: one `_get_plain_font(18)` whose result feeds
all three body `render_text()` calls, and one `_get_plain_font(20)`.

This follows the prompt's own design section verbatim — "body_font =
self._get_plain_font(18); if body_font: three render_text() calls, one per
line" — which specifies a single font call guarded once, feeding three renders.
The criterion appears to have counted the four `render_text()` lines rather than
the font lookups. Calling `_get_plain_font(18)` three times would also be
redundant given the caching requirement in the same prompt, and would break the
single `if body_font:` guard the design prescribes. The four rendered lines at
the four specified sizes and coordinates are all present.

### 4.2 `_get_cached_font()` does not log

The prompt directs `_get_plain_font()` to "log at ERROR (matching
`_get_cached_font()`'s style)". `_get_cached_font()` (line 2539) in fact uses
bare `except:` clauses and logs nothing at all, so there is no logging style
there to match. The explicit instruction in `error_handling` — "Log at ERROR;
`_get_plain_font()` returns `None`" — was followed, using
`self.logger.error(...)` with a broad `except Exception as e:` in the prevailing
style of the rest of the class. The `None` return on failure matches
`_get_cached_font()` exactly, which is the behavioural half of the requirement.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

| Document | Status | Action |
|---|---|---|
| `prompt-bdac4f18` | Closed | Moved to `ai/workspace/prompt/closed/` |
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
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
