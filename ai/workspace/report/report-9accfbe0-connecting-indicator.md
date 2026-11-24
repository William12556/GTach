# Report: Connecting Indicator — Implementation of prompt-9accfbe0

Created: 2026 November 22

---

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 What Was Changed](#20-what-was-changed)
- [3.0 Testing](#30-testing)
- [4.0 Deviations and Observations](#40-deviations-and-observations)
- [5.0 T-Doc Disposition](#50-t-doc-disposition)
- [Version History](#version-history)

---

## 1.0 Summary

`prompt-9accfbe0-connecting-indicator.md` was implemented: C1–C7 of
`change-9accfbe0`. The disconnected view now has two sub-states. While no
connect has failed (Connecting) the dimmed gauge carries no information
symbol and the status dot is yellow; after a failed connect or a dropped
link (Failed) the amber information symbol and the red dot return. In both
sub-states, with the details panel closed, the existing reconnect
indicator turns around the status dot in the gauge palette's colours
(`palette.track` to `palette.tick`). The details panel, the live gauge,
Engine off and simulation mode draw exactly as before.

- `SDL_VIDEODRIVER=dummy pytest tests/`: **865 passed** (baseline before
  the change: 843 passed; 22 tests added).
- `mypy src/`: 9 errors, all pre-existing missing-stub and `no-any-return`
  errors in `comm/` — **none in `display/manager.py`**, and the same 9 on
  the unmodified tree.
- `black --check`, `isort --check-only`, `flake8` on the changed files:
  clean.

**Not verified on target.** The yellow dot and the indicator's legibility
against the dimmed face in both palettes, and the Connecting-to-Failed
transition on a real connect, remain the device check listed in the issue.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 What Was Changed

Files: `src/gtach/display/manager.py`,
`tests/test_connecting_indicator.py` (new),
`tests/test_gauge_status_symbols.py`, and the T-Docs in section 5.

| Item | Change |
|---|---|
| C1 | `self._frame_connecting = False` in `__init__`, directly after `_frame_engine_off`, with a comment stating that it is set at frame start. |
| C2 | New `_link_connecting(self) -> bool`, placed after `_engine_off()`. Returns `not cb()` when `_link_cause_callback` is set — so `None` and `""` are Connecting, any non-empty cause is Failed. An absent callback returns False; a raising callback is logged `Link cause callback failed: …` at DEBUG with `exc_info=True` and returns False. The docstring states that every failure path returns False, matching `_link_lost`'s treatment of an unavailable callback. |
| C3 | `_display_loop`, directly after `_set_frame_engine_off(self._engine_off())`: `_disconnected = self._disconnected_view()`, `_connecting = _disconnected and self._link_connecting()`; when `_disconnected` and the value differs from `_frame_connecting`, one INFO line is logged — `Disconnected: connecting` or `Disconnected: connect failed` — and `_frame_connecting` is assigned. Leaving the view is therefore not logged as a transition. |
| C4 | `_draw_radial_mode()`: the info-symbol branch is now `elif disconnected and not getattr(self, "_frame_connecting", False)`. Nothing else in the dimmed face changed; the readout is still suppressed for the whole disconnected view. |
| C5 | `_draw_status_indicator()`: a new branch `elif self._frame_link_lost and self._frame_connecting` gives `ConnectionStatus.CONNECTING` (yellow). The Engine off, DISCONNECTED, CONNECTING and CONNECTED branches around it are unchanged, as is the dot's position and radius. |
| C6 | `_draw_reconnect_spinner(self, dim: Optional[Tuple[int, int, int]] = None, bright: Optional[Tuple[int, int, int]] = None) -> None`. `dim_colour`/`bright_colour` fall back to `_DISCONNECTED_BG_COLOUR`/`_DISCONNECTED_TEXT_COLOUR` when the argument is `None`. Geometry, period, phase source and the fade loop are unchanged; the docstring gains an `Args` block and one line on the two call sites. The panel's call in `_render_disconnected` is unchanged. |
| C7 | `_render_normal_modes()`: after `self._draw_status_indicator()`, `if self._disconnected_view():` reads `palette = self._palette` and calls `self._draw_reconnect_spinner(palette.track, palette.tick)`. The panel-open case returns before this point, so only the closed-panel gauge reaches it. |

Unchanged, as required: `_link_lost()`, `_engine_off()`,
`_set_frame_engine_off()`, `_disconnected_view()`, `_current_view_key()`,
`_register_view_regions()` and `_register_disconnected_regions()` (the
centre region is still registered in both sub-states),
`_render_disconnected()` including its cause line and its own indicator
colours, `_draw_info_symbol()`, `_draw_key_symbol()`, the sample drain and
every other drawing path.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Testing

`SDL_VIDEODRIVER=dummy pytest tests/`: 865 passed, 0 failed, 1 warning
(pre-existing `pkg_resources` deprecation from pygame).

### 3.1 Changed assertions in existing tests

**One line changed, no assertion weakened or removed.** In
`tests/test_gauge_status_symbols.py` the `manager` fixture gains
`dm._link_cause_callback = lambda: "no route to host"`, and its docstring
now says that the fixture is the Failed sub-state and that Connecting is
covered by the new module.

That module's assertions on the information symbol
(`test_dimmed_gauge_with_info_symbol`, `test_tap_outside_buttons_closes`,
the two pixel-geometry tests and `TestSymbolFailure`) pass either way,
because an absent cause callback is Failed under C2; the explicit cause
states the intent rather than relying on the absent-callback fallback. No
other test module asserts on the information symbol in a disconnected
frame: `tests/test_engine_off_state.py` asserts only
`_disconnected_view()` and the registered regions, and
`tests/test_disconnected_screen.py` drives `_render_disconnected` and
`_register_disconnected_regions`, which are unchanged.

### 3.2 New module `tests/test_connecting_indicator.py` (22 tests)

| Class | Covers |
|---|---|
| `TestConnecting` | Cause `None`: `_frame_connecting` True, no information symbol, yellow dot, indicator called with `(palette.track, palette.tick)`, panel not rendered, `disconnected_info` registered. Empty-string cause is Connecting. The night palette colours the indicator. |
| `TestFailed` | Cause string: `_frame_connecting` False, information symbol, red dot, indicator still drawn, region unchanged. Absent callback is Failed. A raising callback is Failed and logs exactly one DEBUG line with `exc_info`. Edge case: a cause set in the same frame as the first sample is still Failed. |
| `TestTransitionLogging` | Connecting → Failed → Connecting over six frames logs exactly three lines, one per transition. Leaving the view on link recovery logs none. |
| `TestPanelOpen` | Panel open: `_render_disconnected` runs, the indicator is called with `(None, None)` — the panel colours — and no second, gauge-coloured call is made. Edge case: the Connecting-to-Failed transition with the panel open logs both lines and leaves the panel's two frames identical. |
| `TestOtherViews` | Engine off, live gauge (green dot, readout path) and simulation mode: `_frame_connecting` False, no gauge indicator, no information symbol. |
| `TestLinkConnecting` | `_link_connecting()` directly: `None` and `""` True; a cause and `" "` False; absent callback False. |
| `TestSpinnerColours` | With the phase frozen at the start of a rotation: 8 dots; the lead dot is `_DISCONNECTED_TEXT_COLOUR` by default and `palette.tick` when arguments are given, with the panel colour then absent; the ring's top dot lands at `(240, 60 − 26)`, i.e. centred on the status dot. |

The `drawn` fixture records the information symbol, the panel render, the
indicator's arguments and every status-dot `draw_circle`, so the sub-state
is asserted through what is drawn rather than through the flag alone.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Deviations and Observations

1. **C3 is inline in the frame loop, not a `_set_frame_connecting` helper.**
   The change document specifies the assignment and the logging in the
   loop, and the element registry lists only `_link_connecting` and
   `_draw_reconnect_spinner`, so no third method was added. `_frame_engine_off`
   keeps its existing setter; the two are therefore not symmetrical.
2. **`getattr` guard in `_draw_radial_mode`.** `_frame_connecting` is read
   as `getattr(self, "_frame_connecting", False)`, matching the existing
   `_frame_engine_off` read: `tests/test_rpm_signal_conditioning.py` calls
   `_draw_radial_mode` on a host built without `__init__`. In production
   the result is identical to the attribute.
3. **`_disconnected_view()` is evaluated twice per frame in the
   disconnected view** — once in the loop for C3 and once in
   `_render_normal_modes` for C7. It only reads per-frame flags and
   `config.mode`, so this is three attribute reads, not a transport call.
   The cause callback is read exactly once per frame, as the prompt's
   performance target requires.
4. **`" "` (a single space) is Failed.** C2 defines Connecting as a falsy
   cause; a whitespace-only cause is truthy and so reads as Failed. No
   transport produces one — the strings come from `last_failure_cause` —
   and this is asserted in `TestLinkConnecting` to pin the behaviour.
5. **Observation, not changed: a connected transport whose samples stop
   shows Connecting.** `last_failure_cause` is cleared on a successful
   connect, so between the stall and the protocol's `drop_link` the view
   is Connecting with a yellow dot. This is the risk accepted in design
   v2.2 and recorded in the change document.
6. **The indicator's lead dot never reaches the given `bright` colour at an
   arbitrary phase.** The fade weight is `1 − offset/8` and reaches 1.0 only
   when the lead sits exactly on a dot position, which is why the colour
   tests freeze `time.monotonic()` at 0. Unchanged behaviour from the
   panel's indicator; noted so the test's fixture is not mistaken for a
   workaround.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 T-Doc Disposition

| Document | Action |
|---|---|
| `prompt-9accfbe0-connecting-indicator.md` | Moved to `ai/workspace/prompt/closed/`. |
| `change-9accfbe0-connecting-indicator.md` | Active; `status: "implemented"`, `implemented_date`, `implemented_by` and `test_results` filled. Pending device test. |
| `issue-9accfbe0-connecting-indicator.md` | Active; `status: "resolved"`, `resolved_date`, `resolved_by` and `fix_description` filled. Pending device test. |

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-22 | Initial report |
| 1.1 | 2026-11-24 | Layout conformed to README.md: title first, numbered sections, GitHub heading links, Return links |

---

Copyright (c) 2026 William Watson. MIT License.
