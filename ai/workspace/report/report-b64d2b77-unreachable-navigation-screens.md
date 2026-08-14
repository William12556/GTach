Created: 2026 August 14

# Report: Screens Unreachable via Touch/Swipe Navigation

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Headline Finding](<#2.0 headline finding>)
- [3.0 Method](<#3.0 method>)
- [4.0 Finding A — DisplayMode.ACKNOWLEDGEMENT](<#4.0 finding a - displaymode.acknowledgement>)
- [5.0 Finding B — SetupScreen.DEVICE_MANAGEMENT](<#5.0 finding b - setupscreen.device_management>)
- [6.0 Finding C — SetupScreen.CONFIRMATION](<#6.0 finding c - setupscreen.confirmation>)
- [7.0 Screens Confirmed Reachable](<#7.0 screens confirmed reachable>)
- [8.0 Recommendations](<#8.0 recommendations>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Audit of every `DisplayMode` and `SetupScreen` enum member against the
touch and swipe code paths that assign them, to identify screens that
are drawn and handled but have no operator-reachable entry point. Scope
is navigation reachability only; rendering correctness of reachable
screens is not assessed.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Headline Finding

Three enum members have no code path that transitions the display into
them:

| Screen | Enum | Built? | Enterable? |
|---|---|---|---|
| Acknowledgement notice | `DisplayMode.ACKNOWLEDGEMENT` | Fully — render, touch region, dismiss handler, state persistence | No |
| Device management | `SetupScreen.DEVICE_MANAGEMENT` | No render branch in active code | No |
| Confirmation | `SetupScreen.CONFIRMATION` | No render branch in active code | No |

`ACKNOWLEDGEMENT` is the significant case: a complete, safety-relevant
screen with no trigger. The two `SetupScreen` members appear to be
vestiges of `setup_original_backup.py`'s retired flow.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Method

1. Enumerated every `Enum` class under `src/gtach/display/` (`rg
   "class.*Enum"`).
2. For `DisplayMode` and `SetupScreen`, the two enums with a `current
   screen` / `mode` role, searched all references to each member across
   `src/gtach/`.
3. For each member, traced whether any code path assigns it to
   `config.mode` / `current_screen` — via direct assignment,
   `change_mode()`, or `transition_to_screen()` — as opposed to merely
   comparing against it or drawing it once already active.
4. Cross-checked findings against in-code comments, several of which
   document earlier navigation defects (`issue-7d4e91a3`,
   `issue-2b6f4d91`) and confirmed those specific defects are already
   resolved in the active code.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Finding A — `DisplayMode.ACKNOWLEDGEMENT`

**File:** `src/gtach/display/manager.py`

The screen is fully implemented:

- `_draw_acknowledgement_mode()` renders title, warning body text, and
  a dismiss instruction.
- `_register_acknowledgement_regions()` registers a full-screen tap
  region.
- `_on_acknowledgement_dismissed()` calls
  `AcknowledgementStateManager.set_acknowledged()` and transitions to
  `self._post_splash_mode`.
- `_render_normal_modes()` and `_register_view_regions()` both branch
  on `DisplayMode.ACKNOWLEDGEMENT` correctly once that mode is active.
- `_load_config()` and `_save_config()` correctly exclude it from
  persistence as a transient mode, alongside `SPLASH` and `OPTIONS`.

No code path sets `config.mode = DisplayMode.ACKNOWLEDGEMENT` or calls
`change_mode(DisplayMode.ACKNOWLEDGEMENT)`. Confirmed by an exhaustive
search of `src/gtach/` for the string `ACKNOWLEDGEMENT`: every
occurrence is either the enum definition, a downstream consumer of an
already-set mode, or the transient-mode exclusion lists.

`AcknowledgementStateManager.is_acknowledged()` — the method that would
presumably decide whether the notice needs to be shown after an RPM
threshold or engine profile change — is never called anywhere in
`src/`. Its write side, `set_acknowledged()`, is called only from the
unreachable dismiss handler.

**Consequence:** the acknowledgement notice — "OBD tachometer —
experimental software" — cannot appear during normal operation. The
persistence mechanism built for it is complete but idle.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Finding B — `SetupScreen.DEVICE_MANAGEMENT`

**File:** `src/gtach/display/setup_models.py` (definition);
`src/gtach/display/setup.py` (active consumer)

`_render_screen()` in the active `setup.py` is an if/elif chain over
`state.current_screen` covering `WELCOME`, `DISCOVERY`, `DEVICE_LIST`,
`PAIRING`, `COMPLETE`, and `CURRENT_DEVICE`. There is no
`DEVICE_MANAGEMENT` branch; it falls through to the manual-entry check
and then the `WELCOME` fallback.

No call to `transition_to_screen(SetupScreen.DEVICE_MANAGEMENT)` exists
in `setup.py` or `setup_components/state/coordinator.py`. The only
references to this member are in `setup_original_backup.py`, which is
not imported or invoked by the active setup flow.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Finding C — `SetupScreen.CONFIRMATION`

**File:** `src/gtach/display/setup_models.py` (definition);
`src/gtach/display/setup.py` (active consumer)

Same pattern as Finding B: no `_render_screen()` branch, no
`transition_to_screen(SetupScreen.CONFIRMATION)` call anywhere in the
active flow. This member does, however, leave one live trace: it
appears in the `should_cache` list inside `render()`
(`setup.py`, alongside `WELCOME`, `COMPLETE`, and `CURRENT_DEVICE`),
which is a caching rule for a screen state that can never be entered.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Screens Confirmed Reachable

For contrast, the following transitions were traced and confirmed
live in the active code during this audit:

| Transition | Trigger |
|---|---|
| RADIAL → OPTIONS | Swipe down (`_handle_swipe_down`) |
| OPTIONS → prior mode | Swipe up (`_handle_swipe_up`) |
| OPTIONS page 0 ↔ page 1 | Horizontal swipe (`_page_options`) |
| OPTIONS → confirm_clear sub-view | Tap "Clear settings" |
| DISCONNECTED → SETUP | Tap "Setup" button |
| RADIAL/DISCONNECTED palette toggle | Long press |
| WELCOME → DISCOVERY → DEVICE_LIST → PAIRING → COMPLETE | Setup flow taps |
| WELCOME ↔ CURRENT_DEVICE | Determined by stored-device presence at setup start; "New Setup" / "Continue" taps |

The dismiss region for `ACKNOWLEDGEMENT` is itself correctly
hit-tested once active — the defect is entry, not exit.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Recommendations

1. **Treat Finding A as the priority.** It is a built, safety-relevant
   screen with no trigger, not a cleanup item. Before opening a T03
   issue, clarify the intended trigger condition — most likely a check
   against `AcknowledgementStateManager.is_acknowledged()` on startup
   or on RPM threshold/engine profile change, gating transition into
   `ACKNOWLEDGEMENT` before `_post_splash_mode` is reached.

2. **Treat Findings B and C as probable dead-code cleanup**, distinct
   from Finding A: removing two unused `SetupScreen` members and the
   stray `CONFIRMATION` cache-list entry, rather than adding new
   navigation. Confirm with the project owner whether either screen
   was intentionally deferred (in which case it should stay reserved)
   before removal.

3. **Do not combine A with B/C in a single T-Doc.** The root causes are
   unrelated — a missing trigger condition versus vestigial enum
   members from a retired implementation — and the governance workflow
   couples one issue to one change.

This report is investigative; no T03/T02/T04 documents have been
created from it.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial report. Records the navigation-reachability audit of `DisplayMode` and `SetupScreen`: `ACKNOWLEDGEMENT` fully built with no trigger; `DEVICE_MANAGEMENT` and `CONFIRMATION` vestigial with no render branch or transition. |

---

Copyright (c) 2026 William Watson. MIT License.
