Created: 2026 August 19

# Report: Options Menu Page Order

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

prompt-85050ff9 was implemented. The OPTIONS menu's two pages were exchanged so
that page 0 — the page OPTIONS always opens on (change-8c5a1e73) — now holds
Clear settings and Check for updates, and page 1 holds Simulation mode and Debug
toggle. The change is confined to `src/gtach/display/manager.py`: two
conditional blocks, one rects-unpacking block, and five docstring references to
the previous page assignment. No touch-region ID, callback, button geometry, or
paging-mechanism change was made.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

All changes are in `src/gtach/display/manager.py` (19 insertions, 19 deletions).

### 2.1 `_register_options_menu_regions`

The `specs` tuple under `if self._options_page == 0:` and the one under `else:`
were exchanged. Page 0 now builds `("clear_settings", …)` /
`("check_updates", …)`; page 1 now builds `("simulation_mode", …)` /
`("debug_toggle", …)`. Region IDs, `TouchAction.SETTINGS_CHANGE`, and the bound
lambdas are byte-identical to their previous forms — only the branch they sit
under moved.

The rects-unpacking conditional was exchanged to match: page 0 unpacks into
`self._options_btn_clear, self._options_btn_update`; page 1 unpacks into
`self._options_btn_sim, self._options_btn_debug`.

The guard that sets all four button attributes to `None` before the branch was
left unchanged, as were the `_button_column(specs, width=300, top=185)` call and
its explanatory comment.

The docstring paging note was updated from `page 0 — simulation_mode,
debug_toggle` / `page 1 — clear_settings, check_updates` to the reversed
assignment.

### 2.2 `_draw_options_menu`

The `page_items` tuples under the two branches were exchanged. Page 0 draws
`(self._options_btn_clear, "Clear settings")` and
`(self._options_btn_update, "Check for updates")`; page 1 draws
`(self._options_btn_sim, sim_label)` and
`(self._options_btn_debug, debug_label)`.

The `sim_label` / `debug_label` computation, the `None`-skipping drawing loop,
and the page indicator dots were left unchanged.

The docstring sentence "Clear settings is on page 1 and opens the
'confirm_clear' sub-view" was corrected to "page 0".

### 2.3 `_on_clear_settings_requested`

No functional change. Two docstring references were corrected:

- "Bound by the options menu's page 1 (change-8c5a1e73)" → "page 0".
- "The budget still binds. Page 1 must keep offering this method" → "Page 0".

### 2.4 `_register_disconnected_regions`

No functional change. One docstring reference was corrected: "Simulate was
removed from here because it duplicates OPTIONS page 0's simulation_mode
control" → "OPTIONS page 1's".

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

`src/gtach/display/manager.py` parses cleanly (`ast.parse`).

A repository-wide grep for `page 0` / `page 1` in `manager.py` was used to
confirm no remaining reference states the old assignment. The two surviving
matches (lines 99 and 324) concern `_options_page` resetting to 0 on OPTIONS
entry, which this change does not affect.

The full pytest suite was run against a throwaway Python 3.11 virtualenv (the
project has no `venv/` on this machine; pytest, pytest-cov, pygame, pyserial,
PyYAML, and psutil were installed into a scratchpad venv, with `PYTHONPATH=src`
and `SDL_VIDEODRIVER=dummy`):

```
1 failed, 286 passed, 1 warning in 7.25s
```

The single failure is
`tests/display/rendering/test_engine.py::test_compensation_is_announced_once_per_session`.
It was confirmed pre-existing and unrelated: `manager.py` was stashed to its
`HEAD` state and the same test failed identically, then the working copy was
restored and byte-compared against the edited file. No new failures were
introduced.

Manual on-device verification of the three scenarios named in change-85050ff9
(§`testing_requirements.test_cases`) has not been performed and remains
outstanding.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Judgement Calls and Discrepancies

The prompt and change documents both enumerated **three** docstring locations
carrying the old page assignment. Five were found. The two additional locations
were also corrected, on the ground that the change document's stated risk was
"a docstring reference to the old page assignment is missed, leaving stale
documentation", and both would have been stale after the swap:

- `_on_clear_settings_requested`, second paragraph: "Page 1 must keep offering
  this method…". This is inside one of the three enumerated docstrings, so the
  enumeration arguably already covered it, but the change document named only
  the first sentence.
- `_register_disconnected_regions`: "duplicates OPTIONS page 0's
  simulation_mode control". This is a fourth method not named in the change's
  `affected_components`. The edit is a comment-only correction of a factual
  statement the swap invalidated; no code in that method was touched.

The issue, change, and prompt documents are otherwise implemented as written.
No other deviation was made.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

- `ai/workspace/prompt/prompt-85050ff9-options-page-order.md` — **closed**,
  moved to `ai/workspace/prompt/closed/`.
- `ai/workspace/issues/issue-85050ff9-options-page-order.md` — **active**,
  pending on-device test results.
- `ai/workspace/change/change-85050ff9-options-page-order.md` — **active**,
  pending on-device test results.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial report document creation. |

---

Copyright (c) 2026 William Watson. MIT License.
