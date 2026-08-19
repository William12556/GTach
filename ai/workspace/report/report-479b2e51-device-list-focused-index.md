Created: 2026 August 19

# Report: Focused-index Device List Rendering

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

`prompt-479b2e51-device-list-focused-index.md` (iteration 1, implementing
`change-479b2e51`) is implemented in full.

The DEVICE_LIST (Select Device) screen now renders exactly three slots,
centred on the display, whatever the discovered-device count. The focused
device occupies the middle slot, drawn with an accent border and a
background tint and registered as the only touch region; its neighbours
occupy the outer slots, and an outlined empty frame stands in wherever a
neighbour does not exist. A vertical swipe shifts the focus by exactly
one device, clamped at both ends; up/down arrow glyphs state whether a
device exists on that side. Zero discovered devices keeps the existing
"No devices found" message and draws no slots or arrows.

Five source files changed, plus one test module updated and one added. No
change to discovery, filtering or pairing, and none to any other setup
screen.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

### 2.1 `setup_components/state/coordinator.py`

`scroll_offset` and `max_scroll` are replaced by a single
`focused_index` — the 0-based index into `discovered_devices` of the
device in the middle slot. The prompt confirmed (mcp-ripgrep, 2026-08-19)
that neither old field had a consumer outside the class, and the rename
was left to implementer discretion; the honest name was chosen since the
semantics are no longer a scroll offset.

New and changed methods:

| Method | Behaviour |
|---|---|
| `_clamp_focused_index_locked()` | Clamps to `[0, len(devices) - 1]`, logs a WARNING when clamping was needed. Called with `_state_lock` already held. |
| `get_focus_info()` | Replaces `get_scroll_info()`. Returns the clamped `focused_index`, `device_count`, `has_previous`, `has_next`, plus the filter/manual-entry fields the old method carried. |
| `set_focused_index(index)` | Replaces `update_scroll_offset(offset, max_scroll)`. Clamped; returns whether the index changed. |
| `shift_focused_index(delta)` | Signed ±1 shift, clamped; returns False when the shift was clamped away at a bound. |
| `transition_to_screen(DEVICE_LIST)` | Resets `focused_index` to 0, as it previously reset `scroll_offset`. |
| `reset_discovery()` | Same reset. |

The clamp is applied on read, not only on write, because the discovery
worker mutates `discovered_devices` on another thread — this is what
makes the `IndexError` race named in the prompt's error-handling section
unreachable rather than merely caught.

### 2.2 `setup_components/layout/circular_positioning.py`

New `calculate_focused_slot_layout(item_height=45, item_spacing=10)`
returns exactly three entries — `top`, `middle`, `bottom` — each with the
same keys `calculate_curved_list_layout` produces plus a `slot` name. The
middle slot's vertical centre is `display_center[1]` (240); the others sit
one pitch either side.

The per-row curved maths (x-offset, width narrowing, scale, opacity,
safe-area flag) was extracted into `_calculate_curved_geometry(y_pos,
item_height)` and is now shared by both layout methods, so the three
fixed slots narrow and inset by exactly the rule the unbounded list used.
`calculate_curved_list_layout` keeps its cache and its behaviour; the
extraction removed its duplicated block and three variables that became
unused.

Resulting geometry at the defaults: top `y=163`, middle `y=218`, bottom
`y=273`, each 45px tall, widths 326/340/326.

### 2.3 `setup_components/rendering/device_surfaces.py`

- `create_curved_device_surface()` gains `selected: bool = False`
  (default preserves the old behaviour). When set, the row is filled
  with `selected_surface` (70, 70, 95) instead of the standard surface
  colour and outlined with `selected_border` (100, 150, 250) at
  `SELECTED_BORDER_WIDTH = 3`. The border is drawn before the content so
  no glyph is clipped by it, and `selected` is part of the cache key so
  the tinted and untinted forms cannot be confused.
- New `create_empty_slot_surface(layout_item, selected=False)` draws an
  outlined frame on the slot's exact footprint, using
  `empty_slot_border` (110, 110, 125) at `EMPTY_SLOT_BORDER_WIDTH = 2`.
  A selected empty slot keeps the accent border and tint.
- New `create_slot_surface(device, layout_item, selected=False)` is the
  single entry point the render uses for all three slots. It dispatches
  to the device or empty path and — the load-bearing part — returns a
  touch rect **only** for a selected slot holding a device, `None`
  otherwise, so an unselectable slot cannot be registered by accident.

Only the three new colour entries were added; nothing else on the screen
changed colour.

### 2.4 `setup.py`

`_render_device_list_screen` now computes the three slots from
`get_focus_info()`, resolves `focused_index - 1 / focused_index /
focused_index + 1` to a device or `None`, renders each through
`create_slot_surface`, and appends a `("device", touch_rect, device)`
region only when a touch rect came back. The scaled-surface centring, the
"No devices found" path and the Back/Retry buttons are unchanged.

New `_draw_focus_arrows(surface, focus_info)` draws a filled triangle
above the column when `has_previous` and below it when `has_next`, in the
screen's existing text colour. Geometry is four class constants
(`_ARROW_HALF_WIDTH=11`, `_ARROW_HEIGHT=12`, `_ARROW_UP_BASE_Y=154`,
`_ARROW_DOWN_BASE_Y=322`), placed in the bands between the title and the
top slot, and between the bottom slot and the buttons at y=340. The
arrows are indicators only: no touch region is registered for them, per
the change's rejection of tap-target arrows.

New `handle_setup_swipe(direction)` no-ops off DEVICE_LIST, delegates the
clamped shift to the coordinator, invalidates the DEVICE_LIST render
cache when the index actually moved, and returns whether it moved.

### 2.5 `touch.py`

New `_handle_setup_swipe(x, y, start_x, start_y) -> bool`, called from
the setup branch of `_handle_short_press` before the tap dispatch. It
declines — returning False so the tap path is reached unchanged — unless
all of: a setup manager exposing `handle_setup_swipe` is present, the
current setup screen is DEVICE_LIST, `abs(dy) >= swipe_threshold`, and
`abs(dy) >= abs(dx)`. The threshold is read from
`touch_coordinator.swipe_threshold` with the same 100px fallback the
non-setup path uses, so both paths accept the same movement. Direction is
`sign(dy)`: down advances, up retreats.

Horizontal swipes and sub-threshold movement keep their existing
fall-through behaviour, and no other setup screen is affected.

### 2.6 Tests

- `tests/test_device_list_focus.py` (new, 62 tests) covers all nine
  prompt scenarios plus both edge cases: slot count and centring,
  safe-area and button clearance, exactly-one-touch-region across device
  counts and focus positions, slot content resolution, empty-frame
  footprint parity, selected-versus-plain pixel difference, arrow
  visibility rules and actual arrow pixels, focus shift and clamping at
  both bounds, repeated swipes at a bound, focus reset on screen entry
  and on `reset_discovery()`, clamping when the device list shrinks under
  the focus, and the touch-path wiring (swipe consumed before tap;
  sub-threshold still taps; other screens untouched).
- `tests/test_touch_dispatch.py`: its minimal host gains the real
  `_handle_setup_swipe`, which declines against a fake manager with no
  `_setup_manager`, so the existing setup-branch assertions still
  exercise the path as it now runs. No assertion changed.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

### 3.1 Test suite

`pytest tests/` — **286 passed, 1 failed**.

The failure is
`tests/display/rendering/test_engine.py::test_compensation_is_announced_once_per_session`,
pre-existing and unrelated (it follows from `VERTICAL_OFFSET_PX` being 0
since commit `0d9d061`); it was confirmed failing identically before this
change during the preceding task. No new failures.

### 3.2 Prompt validation criteria

| Criterion | Result |
|---|---|
| All slot rects pass `validate_circular_bounds` | Pass — `validate_all_layout_elements` reports 3/3 valid, max corner distance ~181 against a 200 safe radius |
| Exactly one non-None touch rect for DEVICE_LIST when devices exist | Pass — asserted for 1, 2 and 5 devices at every focus position |

### 3.3 Rendered output (pygame 2.6.1, `SDL_VIDEODRIVER=dummy`)

Off-screen renders were produced and inspected for 0, 1, 2 and 5
devices:

- **5 devices, focus 2** — three populated slots, middle tinted and
  outlined, both arrows drawn.
- **1 device** — middle populated and indicated, outlined empty frames
  above and below, no arrows.
- **2 devices, focus 0** — middle and bottom populated, top an empty
  frame, down-arrow only.
- **0 devices** — "No devices found" retained, no slots, no arrows, only
  the Back/Retry regions registered.

The middle slot's touch rect is `(65, 218, 350, 45)` and contains the
display centre; Back and Retry remain at `(80, 340, 130, 60)` and
`(270, 340, 130, 60)`.

### 3.4 Not verified here

Final pixel positioning and touch-region accuracy must be confirmed
on-device at `root@gtach.local` per project convention; the swipe
gesture in particular has only been exercised synthetically, not against
the HyperPixel touch panel.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Judgement Calls and Discrepancies

### 4.1 Swipe detection placed in `_handle_short_press`

The prompt names `TouchHandler._process_touch / _handle_setup_touch` as
the site. In the current code `_process_touch`'s setup branch immediately
delegates to `_handle_short_press(x, y, start_x, start_y)`, which is
where the non-setup swipe test already lives and which still has the
start coordinates; `_handle_setup_touch(x, y)` has already lost them.
The check therefore went into `_handle_short_press`'s setup branch, as a
new `_handle_setup_swipe` helper — same position in the call order the
prompt describes (before tap dispatch), without widening
`_handle_setup_touch`'s signature, which an existing test stubs by
arity.

### 4.2 Reaching the setup manager

`TouchHandler` has no public accessor for the setup manager, and
`manager.py` is not among the prompt's deliverable files, so adding a
`DisplayManager` pass-through was avoided. The helper reads
`getattr(display_manager, '_setup_manager', None)` and checks for
`handle_setup_swipe` before using it, declining safely when either is
absent.

### 4.3 Error-message position moved

`state.error_message` rendered at `(240, 310)`, which falls inside the
new bottom slot (y=273–318). It was moved to `(240, 118)`, in the free
band between the title and the top slot. Nothing else about that path
changed. This is not in the prompt's requirement list, but leaving it
would have shipped a text-over-frame collision created by this change.

### 4.4 `get_scroll_info` / `update_scroll_offset` removed rather than kept

`change-479b2e51`'s implementation sketch mentioned shifting focus "via
`state_coordinator.update_scroll_offset`", while the prompt asks for a
signed-delta method and permits repurposing `get_scroll_info`. Since both
old methods were confirmed to have no consumers, they were replaced
outright by `set_focused_index` / `shift_focused_index` /
`get_focus_info` rather than left as misleadingly named shims.

### 4.5 `calculate_curved_list_layout` retained but now unused

With DEVICE_LIST on the fixed-slot method, the unbounded curved layout
has no remaining caller in active source. It was kept — removing a public
engine method is beyond this prompt's scope, and it still holds the
shared geometry helper's only cache. It is a clean candidate for deletion
in a later tidy-up.

### 4.6 Slot content overflow (pre-existing, not addressed)

At the inherited 45px slot height, a device row's second line (the
device-type text, drawn at y=26 in an 18px font since
`change-ba672e81`) extends past the row's lower edge and is clipped. This
is unchanged from the previous unbounded list, which used the same 45px
rows and the same renderer, so it is not a regression — but it is more
conspicuous now that slots have visible frames. Raising the slot height
was rejected here: at 52px the bottom slot reaches y=328 and leaves no
band for the down-arrow above the buttons at y=340. It belongs with the
deferred `device_surfaces.py` row-rendering consolidation recorded in
`ai/task.md`.

### 4.7 Design document not updated

`change-479b2e51` lists `design-a3b4c5d6-component_display_setup_manager`
(section "DEVICE_LIST screen behaviour") as affected. The prompt's
deliverables do not include it and the prime directive bars unrequested
document edits, so it was left untouched and is flagged here.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

- `prompt-479b2e51-device-list-focused-index.md` — **closed**, moved to
  `ai/workspace/prompt/closed/`.
- `issue-479b2e51-device-list-pagination.md` — **active**, pending
  on-device test results.
- `change-479b2e51-device-list-pagination.md` — **active**, pending
  on-device test results.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial report for prompt-479b2e51 iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
