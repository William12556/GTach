Created: 2026 October 07

# Report: Setup-Path Lock-Order Deadlock Removed

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests Added and Result](<#3. tests added and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [On-Device Verification Outstanding](<#6. on-device verification outstanding>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-e9216e17 (change-e9216e17, issue-e9216e17; audit-36b6ea95 D01 and X01) was implemented in commit `f22640a18710bcce996835fe997979672ae6244b`.

All three edges of the setup lock cycle are removed. Each lock is released before any callback, touch action or call that takes another lock:

- **EDIT A:** `SetupStateCoordinator.transition_to_screen` and `update_state` decide under `_state_lock` and notify their callbacks after releasing it. Callbacks fire only when something changed.
- **EDIT B:** in the cache-hit path of `SetupDisplayManager.render`, `_render_cache_lock` is held only for the dictionary read. The blit, `_update_cached_screen_touch_regions` and the border run after release.
- **EDIT C:** `SetupDisplayManager.handle_touch_event` finds the hit region under `_touch_regions_lock` and calls `_handle_touch_action` after release.
- **EDIT D:** CLAUDE.md §4 rule 8: no call-outs while holding a lock.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/display/setup_components/state/coordinator.py` | EDIT A: `transitioned` and `changed_fields` captured under the lock, notification after it; both `_notify_*` docstrings say they must be called without `_state_lock` held. |
| `src/gtach/display/setup.py` | EDIT B (`render` cache-hit path) and EDIT C (`handle_touch_event`). |
| `CLAUDE.md` | EDIT D: §4 rule 8; Version History 1.3. |
| `tests/test_setup_lock_order.py` | New: 7 tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_setup_lock_order.py` has 7 tests:

- the transition callback and the state-change callback each run with `_state_lock` free;
- no callback fires when nothing changes;
- a callback that calls `get_state()` completes (the edge case);
- the touch action runs with `_touch_regions_lock` free;
- `_update_cached_screen_touch_regions` runs with `_render_cache_lock` free;
- the stress test: 500 renders of the cached WELCOME screen against 500 taps that alternate WELCOME and CURRENT_DEVICE; both threads finish within 10 s.

Five of the seven tests fail on the pre-change code.

pytest after this commit: 309 passed (302 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| No `_notify_*` call inside a `with self._state_lock:` block in `coordinator.py` | AST walk of every `_state_lock` with-block | Pass |
| `render` cache-hit `_render_cache_lock` block holds only the dictionary read | AST: the with-block body is the single `.get` assignment | Pass |
| `_handle_touch_action` called outside the `_touch_regions_lock` block | AST: the with-block calls only `collidepoint` | Pass |
| CLAUDE.md §4 contains rule 8 | Read the file | Pass |
| `tests/test_setup_lock_order.py` passes, including the stress test | Test run | Pass |
| `pytest tests/` passes | Full run | 309 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

Enter setup, then tap Start Setup and Cancel on WELCOME repeatedly for one minute. The display must stay responsive and `error.log` must show no watchdog shutdown.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-e9216e17. |

---

Copyright (c) 2026 William Watson. MIT License.
