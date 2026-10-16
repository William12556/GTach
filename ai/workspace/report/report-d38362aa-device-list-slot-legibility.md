Created: 2026 October 16

# Report: DEVICE_LIST Slot Column Enlargement and Signal Bar Legibility

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Edits Applied](<#3.0 edits applied>)
- [4.0 Tests](<#4.0 tests>)
- [5.0 Verification Method](<#5.0 verification method>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Deviations from the Prompt Specification](<#7.0 deviations from the prompt specification>)
- [8.0 Work Remaining](<#8.0 work remaining>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records the implementation of
`prompt-d38362aa-device-list-slot-legibility.md` (iteration 1, coupled to
`change-d38362aa` and `issue-d38362aa`).

The DEVICE_LIST slot column moves up into the unused band below the
title and grows to 60 px slots with 10 px gaps (column y=118–318, middle
centre y=218). Slot scale and opacity are fixed at 1.0. The slot
interior is laid out with fixed offsets: name and type on the left, four
5 px signal bars on the right, and no dBm text. The up arrow and the
error line move with the column.

Scope is what was changed and how it was verified. On-device
verification is a human step and is outside this prompt.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, leave every T-Doc in place
and active, write this report, and commit and push.

| Item | Outcome |
|---|---|
| `circular_positioning.py`: `calculate_focused_slot_layout` | ✅ Applied |
| `device_surfaces.py`: `create_curved_device_surface` | ✅ Applied |
| `setup.py`: `_ARROW_UP_BASE_Y`, DEVICE_LIST error line | ✅ Applied |
| `tests/test_device_list_focus.py` | ✅ 1 test replaced, 5 added, 2 updated |
| `tests/test_setup_and_gauge.py` | ⚠️ One fixture line added (see §7) |
| `pytest tests/` | ✅ 588 passed, 0 failed |
| T02/T03/T04 documents | Unchanged, as instructed |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 `src/gtach/display/setup_components/layout/circular_positioning.py`

`calculate_focused_slot_layout` now has the signature
`(self, item_height: int = 60, item_spacing: int = 10, column_centre_y: int = 218)`.
`middle_y = column_centre_y - item_height // 2`. The slots sit one pitch
either side, so they are at y=118, 188 and 258. Width and x still come
from `_calculate_curved_geometry`, which measures against
`display_center`. After that call, `scale` and `opacity` are set to 1.0.
The exception fallback uses the same `column_centre_y`. The docstring no
longer says the middle slot is centred on the display. It gives the
column-centre reason instead and cites change-d38362aa.

Resulting geometry in this environment: top x=91 w=301, middle x=72
w=337, bottom x=75 w=330. All three are inside the safe area.

### 3.2 `src/gtach/display/setup_components/rendering/device_surfaces.py`

- New class constants: `TEXT_LEFT=24`, `NAME_Y=0`, `TYPE_Y=27`,
  `TYPE_DOT_X=14`, `TYPE_DOT_RADIUS=6`, `NAME_RIGHT_RESERVE=79`,
  `BAR_COUNT=4`, `BAR_WIDTH=5`, `BAR_GAP=3`, `BAR_BASE_HEIGHT=8`,
  `BAR_STEP=6`, `BAR_RIGHT_INSET=14`, plus `BAR_BOTTOM_BELOW_CENTRE=13`
  (see §7).
- New colour keys: `signal_lit` (220,220,220) and `signal_unlit`
  (110,110,125).
- The surface is now `item_width × item_height`. The background and the
  selected border are unchanged: the bg rect height is the surface
  height − 2, the corner radius is 8, and the colours are the same.
- Type dot at `(14, bg_height // 2)`, radius 6.
- Name: `FONT_BODY`, truncated to `item_width − 79`, `colors['text']`,
  blitted at (24, 0).
- Type: `FONT_SMALL_TEXT`, `colors['text_dim']`, blitted at (24, 27).
- The bars are drawn only when `signal_strength` is not None, by a new
  private helper `_draw_signal_bars` (see §7). The block is 29 px wide,
  its left edge is at `width − 43` and its bottom at
  `bg_height // 2 + 13` (y=42). Bar `i` is `8 + 6·i` px high, at
  `x = left + i·8`. A bar is lit when `i < get_signal_bars(rssi)`.
- The dBm text block is deleted.
- The scaling arithmetic is removed: scaled font sizes, scaled offsets,
  and the per-element alpha surfaces for the name, type and dBm. The
  cache key still includes `scale` and `opacity`, and the touch rect is
  unchanged.

### 3.3 `src/gtach/display/setup.py`

- `_ARROW_UP_BASE_Y` changed from 154 to 114, so the up arrow occupies
  y=102–114. `_ARROW_DOWN_BASE_Y` is unchanged (322). The constants
  comment now gives column y=118–318.
- `_render_device_list_screen`: the error text is
  `self._fit_text(font_minimal, state.error_message, max_width=220)`,
  centred at (240, 84). The comment is updated.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests

`tests/test_device_list_focus.py`:

| Test | Change |
|---|---|
| `test_middle_slot_is_centred_on_the_column_centre` | Replaces `test_middle_slot_is_centred_on_the_display`; middle centre y=218 |
| `test_slot_geometry_matches_the_target` | New; y=(118,188,258), height 60, scale and opacity 1.0 |
| `test_the_region_rect_covers_the_middle_slot` | `centery ≈ 218` (abs = height // 2) |
| `TestArrowGlyphs.UP_POINT` | (240, 148) → (240, 108); `DOWN_POINT` unchanged |
| `TestSlotLegibility.test_strong_signal_draws_lit_bars` | New; RSSI −35 → `signal_lit` pixels in the bar block |
| `TestSlotLegibility.test_weak_signal_draws_only_unlit_bars` | New; RSSI −90 → `signal_unlit` present, no `signal_lit` in the bar block |
| `TestSlotLegibility.test_no_signal_strength_renders_without_bars` | New; edge case `signal_strength=None` |
| `TestSlotLegibility.test_type_label_fits_inside_the_slot` | New; surface height 60 and `TYPE_Y + FONT_SMALL_TEXT height ≤ 60` |

The module docstring now says the slots are no longer centred on the
display. `_device()` takes an optional `signal_strength` argument.

The font height is read from `get_font_manager()` at runtime. It is not
hard-coded. The bar-block pixel region is derived from the renderer's
class constants. The test reads it only inside the bar block, because
the name text uses the same colour as `signal_lit`.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

Dependencies were installed with `pip install -e .[dev]` (Python 3.13,
pygame 2.6.1).

```
$ SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest tests/
Baseline (before the change):  583 passed, 1 warning
After the change:              588 passed, 1 warning
```

`test_compensation_is_announced_once_per_session` passed in this
environment. No unrelated failure was observed.

Font metrics in this environment match the Pi measurements in
issue-d38362aa. FONT_BODY (24) has height 35 and ascent 28.
FONT_SMALL_TEXT (20) has height 29 and ascent 24. The type label
therefore ends at y=56 in a 60 px surface.

Other checks:

```
$ grep -n 'dBm' src/gtach/display/setup_components/rendering/device_surfaces.py
(no output)
$ black --check <changed files>        → unchanged
$ flake8 <changed files>               → clean
$ mypy <three source files>            → same 5 errors in these files as
                                          before the change (missing pygame
                                          stubs); none introduced
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | All change-d38362aa §2 values present in source | ✅ Pass | §3; asserted by `test_slot_geometry_matches_the_target`, `TestArrowGlyphs`, `TestSlotLegibility` |
| 2 | `grep -n 'dBm' device_surfaces.py` returns nothing | ✅ Pass | §5 |
| 3 | `pytest tests/` passes | ✅ Pass | 588 passed, 0 failed |
| 4 | Human verification on the Pi | ⏳ Pending | §8 |
| 5 | `git diff --stat` lists only the files in scope | ⚠️ Partial | It also lists `tests/test_setup_and_gauge.py` (+4 lines); §7 deviation 1 |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

Three.

**1. `tests/test_setup_and_gauge.py` received one fixture entry.** The
prompt requires `self._fit_text(...)` in `_render_device_list_screen`.
`TestPersistentErrors.test_device_list_render_keeps_error` calls that
method unbound on a `SimpleNamespace` host that has no `_fit_text`, so
it raised `AttributeError` (1 failed, 587 passed). The host now has a
`_fit_text` entry that delegates to `SetupDisplayManager._fit_text`. No
assertion changed. The change document lists this module in its
regression scope. The prompt's file list omits it. The alternative was
to call `SetupDisplayManager._fit_text(self, …)` in production code to
suit a test double, which I rejected.

**2. Extra constant `BAR_BOTTOM_BELOW_CENTRE = 13`.** The prompt gives
the bar bottom as `bg_height // 2 + 13` but lists no constant for the
13. I named it so that no fixed value is left unnamed (CLAUDE.md §6). It
also lets the test derive the bar block. The value is unchanged.

**3. The bars are drawn by a private helper, `_draw_signal_bars`.** The
logic is exactly as specified. Moving it out keeps
`create_curved_device_surface` shorter. There is no public interface
change.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Work Remaining

On-device verification on `gtach.local`, per the prompt notes:

1. Run with the emulator and at least one other device. Confirm that
   name and type are fully visible in all three slots.
2. Confirm that lit and unlit bars are distinguishable in both selected
   and unselected slots.
3. Confirm that no dBm text is shown.
4. Trigger "OBD check failed" and confirm the error line sits between
   the title and the up arrow.

Points to look at closely:

- **Top slot name truncation.** The top slot is the narrowest (301 px),
  so its name budget is 222 px against 258 px for the middle slot. A
  long name truncates sooner when it is in the top slot.
- **Error line versus up arrow.** Measured here, "OBD check failed" in
  the label-small font renders as a 217 × 29 px box (y=70–99). The arrow
  apex is at y=102, so the gap is 3 px, and the text is 3 px inside the
  220 px fit limit. Glyph ink is smaller than the box.
- **Empty frames.** These are now unscaled (scale 1.0), so they are
  slightly larger than before and still match the populated footprint.
- **Unselected slot contrast.** Unlit bars (110,110,125) on the
  unselected slot colour (40,40,50) have the lowest contrast of the
  combinations.

`issue-d38362aa`, `change-d38362aa` and `prompt-d38362aa` remain active
and unmoved. design-a3b4c5d6 §5.3 still needs its update (owner:
Claude, strategic).

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-16 | Initial report. Implements prompt-d38362aa iteration 1: slot column at y=118/188/258 with 60 px slots, scale and opacity 1.0, fixed-offset slot interior with four 5 px bars and no dBm text, up arrow at y=102–114, error line at y=84 fitted to 220 px. 588 tests pass. Three deviations: a one-entry fixture update in tests/test_setup_and_gauge.py, a named constant for the bar bottom offset, and a private bar-drawing helper. |

---

Copyright (c) 2026 William Watson. MIT License.
