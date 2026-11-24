# Report: Gauge Status Symbols — Implementation of prompt-adb3afeb

Created: 2026 November 20

---

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 What Was Changed](#20-what-was-changed)
- [3.0 Swipe Starting on the Open Panel](#30-swipe-starting-on-the-open-panel)
- [4.0 Testing](#40-testing)
- [5.0 Deviations and Observations](#50-deviations-and-observations)
- [6.0 T-Doc Disposition](#60-t-doc-disposition)
- [Version History](#version-history)

---

## 1.0 Summary

`prompt-adb3afeb-gauge-status-symbols.md` was implemented: EDIT A and
EDIT B1–B10 of `change-adb3afeb`. Engine off now draws a grey ignition-key
symbol and no text. DISCONNECTED draws a dimmed gauge with an amber
information symbol and the red status dot; a tap on the symbol opens the
existing DISCONNECTED screen as a panel, and a tap outside its buttons
closes it. The panel also closes when the link recovers, when Engine off
begins, or when the mode leaves RADIAL. The OPTIONS title is removed. The
live gauge draws as before.

- `SDL_VIDEODRIVER=dummy pytest tests/`: **843 passed** (baseline before
  the change: 818 passed; 25 tests added).
- `mypy src/`: no issues (unchanged from the baseline).
- `flake8` on the changed files: clean.

**Not verified on target.** The symbol legibility in both palettes, the
grey key contrast on the night band-0 disc, and the panel interaction on
the touch panel remain the device check listed in the issue.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 What Was Changed

Files: `src/gtach/display/models.py`, `src/gtach/display/manager.py`,
`tests/test_engine_off_state.py`, `tests/test_gauge_status_symbols.py`
(new), and the T-Docs listed in section 6.

### 2.1 EDIT A — `models.py`

`Palette` gains `symbol` and `alert` (`Tuple[int, int, int]`) after
`band_centres`. Values: day `symbol (150, 150, 150)`, `alert (230, 160, 0)`;
night `symbol (120, 120, 120)`, `alert (150, 105, 0)`.

### 2.2 EDIT B — `manager.py`

| Edit | Change |
|---|---|
| B1 | `ICON_TOUCH_SIZE = 144`. `ENGINE_OFF_TEXT` kept; its comment now states that only `_draw_engine_off_text` draws it. |
| B2 | `self._disconnected_details_open = False`, initialised beside `_frame_engine_off`. |
| B3 | `_disconnected_view() -> bool` returns `_frame_link_lost and not _frame_engine_off and mode == RADIAL`; used in `_render_normal_modes`, `_register_view_regions` and `_draw_radial_mode`. In the frame loop, directly after `_set_frame_engine_off`, an open panel is closed when `_disconnected_view()` is false, with the reason `link recovered`, `engine off` or `mode change`. |
| B4 | `_current_view_key()` gains `_disconnected_details_open` after the disconnected member; docstring and `Returns` updated. |
| B5 | `_render_normal_modes()`: panel open → `_render_disconnected()` and return; otherwise control falls through to the existing RADIAL branch, which calls `_draw_radial_mode()` and then `_draw_status_indicator()`. |
| B6 | `_register_view_regions()`: panel open → `disconnected_close` (0, 0, 480, 480) registered first, then `_register_disconnected_regions()` unchanged, so Setup and Reset are above it in z-order. Panel closed → only `disconnected_info`, a 144 px square centred on (240, 240). Both are button regions with action `NAVIGATION`. |
| B7 | `_draw_radial_mode()`: in the disconnected view rpm is 0 (no fill arc, no indicator line), there is no readout, ticks, numerals, band boundary marks and the `RPM × 1000` label are in `palette.line`, the centre disc is `palette.track`, and `_draw_info_symbol()` is called. Engine off calls `_draw_key_symbol()` in place of the text block. The text block moved unchanged to `_draw_engine_off_text(center)`, which nothing calls; its docstring says it is kept for later use. |
| B8 | `_draw_info_symbol(surface, palette)`: disc r 40 at (240, 240) in `palette.alert`; black dot r 5 at (240, 222); black bar `Rect(236, 232, 9, 27)` (x 236–244, y 232–258 inclusive). |
| B9 | `_draw_key_symbol(surface, palette)`: `palette.symbol`, width 6; bow ring centre (222, 240) r 18; shaft (240, 240)–(276, 240); teeth (264, 240)–(264, 252) and (274, 240)–(274, 252). |
| B10 | `_draw_options_menu()`: the `Options` title block removed. Nothing else moved. |

Both symbol helpers catch their own exceptions and log them with
`logger.error(..., exc_info=True)`, so a symbol failure does not stop the
rest of the gauge from drawing. INFO lines are logged as
`DISCONNECTED details opened` and `DISCONNECTED details closed: <reason>`.

Unchanged, as required: `_link_lost()`, `_engine_off()`,
`LINK_LOSS_TIMEOUT`, `LINK_RECOVERY_SAMPLES`, `ENGINE_OFF_FRESHNESS_S`,
the sample drain, `_render_disconnected()`,
`_register_disconnected_regions()`, `_draw_reconnect_spinner()`, the
acknowledgement screen, OPTIONS paging and buttons, setup screens and the
swipe handlers.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Swipe Starting on the Open Panel

**Observed: OPTIONS is entered and the panel flag is cleared.** The panel
is not closed by the swipe itself.

`TouchHandler._handle_short_press` classifies a movement at or above the
swipe threshold as a swipe before it consults the touch coordinator, so
the full-screen `disconnected_close` region never receives the gesture. A
downward swipe calls `_handle_swipe_down`, which sets the mode to OPTIONS.
On the next frame `_disconnected_view()` is false and the frame loop logs
`DISCONNECTED details closed: mode change`. A swipe up from OPTIONS then
returns to RADIAL with the panel closed (only `disconnected_info`
registered). Both are covered by
`TestPanelClosesWithTheView.test_swipe_down_on_open_panel_enters_options`
and `test_swipe_up_from_options_returns_to_closed_panel`.

A hold below the swipe threshold that starts on the open panel presses
the button it starts on: `disconnected_close` if outside Setup and Reset,
so the panel closes and the palette does not toggle. A hold on the
`disconnected_info` region opens the panel and does not toggle the
palette (`test_hold_on_symbol_opens_panel_not_palette`). A hold elsewhere
on the dimmed gauge is a long press and toggles the palette, as on the
live gauge.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Testing

`SDL_VIDEODRIVER=dummy pytest tests/`: 843 passed, 0 failed.

### 4.1 Changed assertions in existing tests

All in `tests/test_engine_off_state.py`, class `TestEngineOffCondition`.
No assertion in `tests/test_disconnected_screen.py` encoded replaced
behaviour: it drives `_render_disconnected` and
`_register_disconnected_regions` directly, and both are unchanged. That
file was therefore not modified.

| Test | Before | After |
|---|---|---|
| `test_fresh_evidence_shows_engine_off` | `ENGINE_OFF_TEXT in drawn["text"]` | `ENGINE_OFF_TEXT not in drawn["text"]` |
| `test_stale_evidence_is_disconnected` | `drawn["disconnected"] == [1]` (full screen rendered) | `manager._disconnected_view() is True` and `drawn["disconnected"] == []` (panel closed) |
| `test_view_key_and_regions` | `_disconnected_btn_setup is not None` and regions non-empty | regions are exactly `["disconnected_info"]` |

The remaining assertions in those tests are unchanged.

### 4.2 New module `tests/test_gauge_status_symbols.py` (25 tests)

| Class | Covers |
|---|---|
| `TestPaletteColours` | EDIT A values, day and night. |
| `TestDisconnectedPanelClosed` | Only `disconnected_info` registered, 144 px and centred; `_render_disconnected` not called; info symbol drawn, key not; no readout; pixel checks of the symbol and the `palette.track` disc in day and night; status dot drawn; a hold on the symbol opens the panel without toggling the palette. |
| `TestPanelOpenAndClose` | A tap opens the panel and changes the view key; region z-order `close, setup[, reset]`; close region is 0, 0, 480, 480; Setup and Reset fire above close; a tap outside them closes the panel and restores `disconnected_info`; INFO logs. |
| `TestPanelClosesWithTheView` | Link recovery and Engine off clear the flag in the same frame, with the reason logged; a tap in the frame the link recovers leaves no panel and no regions; swipe down / swipe up as in section 3. |
| `TestEngineOff` | Key symbol drawn, no text, no readout, no regions; key pixel geometry on the band-0 disc; `_draw_engine_off_text` retained, never referenced by another method, and draws `ENGINE_OFF_TEXT` when called. |
| `TestLiveGauge` | Neither symbol nor panel drawn; readout drawn; no regions. |
| `TestSymbolFailure` | A raising draw primitive inside either helper is logged once at ERROR with `exc_info` and does not propagate. |
| `TestOptionsMenu` | No `Options` text; both page-0 buttons, the return hint and the two regions unchanged. |

Edge case `_reset_callback is None` is covered by
`test_tap_opens_panel` (regions `disconnected_close`, `disconnected_setup`
only).

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Deviations and Observations

1. **Two private helpers not listed in the element registry:**
   `_open_disconnected_details()` and `_close_disconnected_details(reason)`.
   The open and close INFO logs required by the prompt cannot be written in
   a lambda, and the close path is shared by the tap callback and the
   frame loop. Each sets the flag and logs one line.
2. **`getattr` guard in `_draw_radial_mode`.** `disconnected` is computed
   as `bool(getattr(self, "_frame_link_lost", False)) and
   self._disconnected_view()`. `tests/test_rpm_signal_conditioning.py`
   calls `_draw_radial_mode` on a host built without `__init__` that has
   neither `_frame_link_lost` nor `config.mode`; the existing
   `_frame_engine_off` read uses `getattr` for the same reason. In
   production the result is identical to `_disconnected_view()`.
3. **B5 by fall-through.** The closed-panel case is not a separate branch:
   it falls through to the existing RADIAL branch, which already calls
   `_draw_radial_mode()` and then `_draw_status_indicator()`. The behaviour
   is as specified.
4. **Observation, not changed: the panel survives a Setup visit.**
   Entering setup from the panel's Setup button sets `_in_setup_mode` but
   does not change `config.mode`, so `_disconnected_view()` stays true and
   the flag is not cleared. If the link is still lost on return from setup,
   the panel is shown open. The change document lists only link recovery,
   Engine off and mode change as close conditions, so this was left as is.
   Confidence: high from reading `set_setup_mode`/`exit_setup_mode`;
   verifiable on device by tapping Setup on the panel and backing out.
5. `_get_band_colour(0)` is still called once per frame in the disconnected
   view, as it is for Engine off. Its result is not used for the disc
   colour there; the sticky band index steps toward 0.

[Return to Table of Contents](#table-of-contents)

---

## 6.0 T-Doc Disposition

| Document | Action |
|---|---|
| `prompt-adb3afeb-gauge-status-symbols.md` | Moved to `ai/workspace/prompt/closed/`. |
| `change-adb3afeb-gauge-status-symbols.md` | Active; `status: "implemented"`. Pending device test. |
| `issue-adb3afeb-gauge-status-symbols.md` | Active; `status: "resolved"`. Pending device test. |

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-20 | Initial report |
| 1.1 | 2026-11-24 | Layout conformed to README.md: title first, numbered sections, GitHub heading links, Return links |

---

Copyright (c) 2026 William Watson. MIT License.
