Created: 2026 August 19

# Report: Small-Text Font Standardisation and Font-Path Consolidation

---

## Table of Contents

- [1.0 Summary](<#1.0 summary>)
- [2.0 Changes Made](<#2.0 changes made>)
- [3.0 Verification](<#3.0 verification>)
- [4.0 Judgement Calls and Discrepancies](<#4.0 judgement calls and discrepancies>)
- [5.0 Document Status](<#5.0 document status>)
- [Version History](<#version history>)

---

## 1.0 Summary

`prompt-ba672e81-text-standardisation.md` (iteration 1, implementing
`change-ba672e81`) is implemented in full.

Small text across every screen now renders at a single size,
`TypographyConstants.FONT_SMALL_TEXT = 18`, replacing `FONT_LABEL_SMALL`
(16), `FONT_MINIMAL` (14) and an ungoverned 12px raw fallback.
`FontManager` is now the only place in the application that constructs a
`pygame.font.Font`: `DisplayManager._get_cached_font()` is gone, its 16
call sites go to `FontManager` directly, and every caller-side raw-pygame
fallback branch has been deleted.

Five source files changed plus two test modules that stubbed the removed
method. No behavioural change outside the display rendering layer.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

### 2.1 `src/gtach/display/typography.py`

**Constants.** `FONT_LABEL_SMALL` and `FONT_MINIMAL` removed;
`FONT_SMALL_TEXT = 18` added with a comment recording what it replaces
and why. `FONT_RPM_*`, `FONT_TITLE`, `FONT_HEADING`, `FONT_BODY`,
`FONT_BUTTON` and every `BUTTON_FONT_*` constant are untouched.

**`FontManager.get_font()` hardened.** It no longer returns `None`. The
signature is now `-> pygame.font.Font`. Behaviour:

- pygame absent → logs ERROR, raises `RuntimeError`.
- Font system not initialised → one `_initialize_pygame_fonts()` retry;
  still failing → logs ERROR, raises `RuntimeError`.
- Michroma load failure at a given size → logs WARNING with traceback and
  falls through to `pygame.font.Font(None, size)`. This is FontManager's
  own internal fallback and was retained as the prompt requires; it is now
  reached by an explicit branch rather than a nested `try`, so the
  system-default substitution is logged rather than silent.
- SDL default also failing → logs ERROR with traceback, raises
  `RuntimeError` chained from the original exception.

Size clamping via `_validate_font_size()` is unchanged: out-of-range sizes
still clamp and log a warning.

**`get_plain_font()` added** (see §4.1) — the SDL-default, no-Michroma
font used by the acknowledgement screen, with its own size-keyed cache
under the existing `_cache_lock`. `clear_cache()` clears both caches.

**`calculate_text_bounds()`** now calls `get_font()` inside its `try`, so
an unavailable font system degrades to the pre-existing width estimate
instead of propagating. Measurement is advisory, so this is the one place
that deliberately absorbs the new exception.

**Accessors consolidated.** `get_label_small_font()` is the single
small-text accessor and returns a font at `FONT_SMALL_TEXT`. Both
definitions of `get_minimal_font()` were removed — the `FONT_MINIMAL`-based
one and the earlier `FontCategory.MINIMAL` one that it had been silently
shadowing (see §4.2). Module-level `get_font()` and
`get_font_for_category()` return types were corrected to non-`Optional`
with their new `Raises:` clauses documented.

### 2.2 `src/gtach/display/manager.py`

`_get_cached_font()` deleted. All 16 call sites repointed:

| Former call | Now | Sites |
|---|---|---|
| `self._get_cached_font(16)` | `get_label_small_font()` | 2 — `'RPM × 1000'` label, slider label |
| `self._get_cached_font(36)` | `get_title_display_font()` | 1 — DISCONNECTED title (`FONT_TITLE` is 36) |
| `self._get_cached_font(N)` | `get_font_manager().get_font(N)` | 13 — N ∈ {18, 20, 22, 24, 26, 28, 52, 72} |

The two 16px sites were the in-scope small-text elements named in the
prompt; both now render at 18px. All other sites keep their previous point
size exactly.

`_get_plain_font()` retained — its callers are the acknowledgement screen
(`change-bdac4f18`), not `_get_cached_font()`, so it was not redundant. Its
body now delegates to `FontManager.get_plain_font()`; it keeps its
signature, its `Optional` return and its error-logging contract, so the
acknowledgement screen is unaffected.

`get_minimal_font` removed from the typography import list.

### 2.3 `src/gtach/display/splash.py`

- The raw `pygame.font.Font(None, fallback_size)` branch in the local
  `_get_cached_font()` is removed; a `None` from the typography path now
  logs ERROR and returns `None`. The method, its cache and its
  `font_type` dispatch are retained. `fallback_size` is kept in the
  signature for call-site compatibility and documented as unused.
- The stale docstring and the `FONT_LABEL_SMALL` references in
  `_draw_version_text()` and the label-font debug line now read
  `FONT_SMALL_TEXT`.
- `_draw_title_text()` and `_draw_version_text()` each loaded
  `Michroma-Regular.ttf` from disk directly (72px and 40px), falling back
  to `pygame.font.Font(None, …)`. Both now call
  `get_font_manager().get_font(72)` / `.get_font(40)`, which resolves the
  same file and owns the same fallback. Same faces, same sizes, now cached
  and governed (see §4.3).

### 2.4 `src/gtach/display/setup_components/rendering/device_surfaces.py`

All six raw `pygame.font.Font(None, …)` fallback branches removed, in both
the fixed-literal block and the `scale_factor` block. Each site collapses
from a seven-line `try/except` to a single accessor call.

In the `scale_factor` block, `minimal_font_size` (14 × sf) and
`signal_font_size` (16 × sf) are replaced by one `small_text_font_size`
(18 × sf), matching the consolidation. In the fixed-literal block the
device-type font moves from `get_minimal_font()` to
`get_label_small_font()`. The duplicate-block question itself is untouched
and remains deferred per `ai/task.md`.

### 2.5 `src/gtach/display/setup.py`

The four `get_minimal_font()` call sites (error message, progress message,
error-message rendering, pairing status text) now call
`get_label_small_font()`; the import list is updated. These four elements
move 14px → 18px.

### 2.6 Tests

`tests/test_disconnected_screen.py` and
`tests/test_connect_error_classification.py` each drove
`DisplayManager._render_disconnected` against a `SimpleNamespace` host
carrying `host._get_cached_font = lambda size: f'font-{size}'`. With the
method gone, that stub is dead and the render would have constructed real
fonts. Each file gains an autouse fixture that monkeypatches
`gtach.display.manager.get_font_manager`, `get_title_display_font` and
`get_label_small_font` to return the same `'font-N'` sentinels, and the
host-level stub line is removed. No assertion changed.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

### 3.1 Prompt validation greps

| Check | Result |
|---|---|
| `FONT_LABEL_SMALL` / `FONT_MINIMAL` in active `src/` | 0 code references (2 explanatory comment mentions in `typography.py`; backup files out of scope) |
| `pygame.font.Font(None` in `src/gtach/display/*.py` outside `typography.py` | 0 |
| `_get_cached_font` in `manager.py` | 0 |
| `get_minimal_font` in active `src/` | 0 |

### 3.2 Behavioural smoke test (pygame 2.6.1, `SDL_VIDEODRIVER=dummy`)

- `get_font(18)` returns a valid `Font`; a second call returns the same
  cached object.
- `get_font(2)` clamps to `MIN_FONT_SIZE` and `get_font(9999)` to
  `MAX_FONT_SIZE`, both logging a warning — unchanged by the hardening.
- `get_label_small_font()` is identical to `get_font(FONT_SMALL_TEXT)`.
- `TypographyConstants.FONT_LABEL_SMALL`, `.FONT_MINIMAL`,
  `DisplayManager._get_cached_font` and `typography.get_minimal_font` all
  absent; `DisplayManager._get_plain_font` present and working.
- `validate_font_system()` reports all four checks true.
- `typography`, `manager`, `splash`, `setup` and `device_surfaces` all
  import cleanly.

### 3.3 Test suite

`pytest tests/` — **224 passed, 1 failed**.

The single failure is
`tests/display/rendering/test_engine.py::test_compensation_is_announced_once_per_session`.
It is pre-existing and unrelated: confirmed by stashing this change and
re-running the module, which fails identically. It follows from
`VERTICAL_OFFSET_PX` being reset to 0 in commit `0d9d061`, so no
compensation is announced.

No new failures.

### 3.4 Not verified here

All visual and measurement verification is on-device only
(`root@gtach.local`), per the prompt's constraint. Whether 18px reads
correctly on the HyperPixel at 30–50cm remains open; `FONT_SMALL_TEXT`
makes any adjustment a one-line change.

### 3.5 Exception-propagation audit

Because `get_font()` now raises rather than returning `None`, every call
site reached by the new exception was checked by AST walk. Each one is
inside a `try/except Exception` that logs — either in the drawing method
itself (`_draw_radial_mode`, `_render_disconnected`,
`_render_slider_visuals`, `_draw_acknowledgement_mode`, `_register_save_button`,
all of `device_surfaces.py`) or in its immediate caller
(`_draw_options_mode` wraps `_draw_options_menu`, `_draw_confirm_view` and
`_draw_update_view`; `SetupDisplayManager.render()` wraps `_render_screen`).
Worst case under a font-system failure is a skipped frame and an ERROR
log — which is the intended surfacing behaviour, replacing the previous
silent masking.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Judgement Calls and Discrepancies

### 4.1 `_get_plain_font()` versus the "zero raw pygame.font.Font" criterion

Two prompt clauses pulled against each other. The design section permits
retaining `_get_plain_font()` if it serves a distinct, still-needed
purpose — it does; its callers are the acknowledgement screen, not
`_get_cached_font()`, and it deliberately avoids Michroma, which is too
wide for multi-word body text. But its body contained
`pygame.font.Font(None, size)` in `manager.py`, which the success criteria
and the validation grep both require to be zero.

Resolution: the creation and caching moved into
`FontManager.get_plain_font()`, and `DisplayManager._get_plain_font()`
became a thin delegate. Both clauses are satisfied, the acknowledgement
screen's rendering is byte-identical, and the constraint that only
caller-side bypasses be removed is honoured — this was a caller-side
bypass, and it is now inside FontManager where the file's own internal
system-default fallback legitimately lives.

### 4.2 Two `get_minimal_font()` definitions

`typography.py` defined `get_minimal_font()` twice: a
`FontCategory.MINIMAL` accessor at module line ~659 and a
`FONT_MINIMAL`-based one at ~702. The second shadowed the first, so the
category version had been dead code for as long as both existed.

Removing only the `FONT_MINIMAL` version would have un-shadowed the other
and left the name alive, silently serving 16px — precisely the class of
trap this change exists to remove. Both were removed so the name is gone.
`FontCategory.MINIMAL`, `MINIMAL_SIZE` and `get_font_for_category()` are
untouched; only the module-level accessor is gone, and it had no callers.

### 4.3 Two additional font bypasses in `splash.py`

`_draw_title_text()` and `_draw_version_text()` each contained a direct
`Michroma-Regular.ttf` load with a `pygame.font.Font(None, …)` fallback.
The prompt's requirements list does not name them, but the success
criteria and the validation grep cover them, and they are exactly the
"parallel font-creation path" the change targets. They were repointed to
`FontManager.get_font()` at the same sizes (72px, 40px). Same font file,
same sizes, same fallback semantics — now cached rather than re-loaded
from disk per frame.

### 4.4 The 18px disconnection-cause line

`change-ba672e81` lists `_render_disconnected`'s cause line as out of
scope — "already at target size, not modified, but should be reviewed for
consistency once the new constant lands". It was therefore left as
`get_font_manager().get_font(18)` with a literal, not repointed to
`FONT_SMALL_TEXT`. It is a small-text status message at exactly the target
size, so binding it to the constant is a zero-behaviour-change tidy-up
whenever that review happens.

### 4.5 Accessor name

The prompt directed that one of the two accessor names be retained rather
than a new one introduced. `get_label_small_font()` was kept, since the
prompt's own requirement text directs `setup.py`'s `get_minimal_font()`
sites at "the consolidated accessor". The name is now slightly narrower
than what it returns — it serves all small text, not only labels — and
renaming it to `get_small_text_font()` would be a mechanical follow-up
across five files if that is wanted.

### 4.6 Sizes that changed

Beyond the two 16px `manager.py` sites the prompt names, consolidation
moves these elements to 18px, all of them small text within the change's
stated scope:

- `setup.py` — error message, progress message, error-message rendering,
  pairing status text (14 → 18).
- `device_surfaces.py` fixed block — device type text (14 → 18); signal
  strength text (16 → 18, and its 12px fallback path is gone).
- `device_surfaces.py` scaled block — device type (14 × sf → 18 × sf);
  signal strength (16 × sf → 18 × sf).
- `splash.py` — version text label validation reference (16 → 18); the
  rendered version glyphs remain 40px, unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

- `prompt-ba672e81-text-standardisation.md` — **closed**, moved to
  `ai/workspace/prompt/closed/`.
- `issue-ba672e81-text-standardisation.md` — **active**, pending
  on-device test results.
- `change-ba672e81-text-standardisation.md` — **active**, pending
  on-device test results.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial report for prompt-ba672e81 iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
