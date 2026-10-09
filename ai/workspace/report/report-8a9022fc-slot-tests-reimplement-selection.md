Created: 2026 October 09

# Report: Slot Tests Use the Production Rule

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests and Result](<#3. tests and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [Items Kept](<#6. items kept>)
7. [On-Device Verification Outstanding](<#7. on-device verification outstanding>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-8a9022fc (change-8a9022fc, issue-8a9022fc) is implemented. The four slot-contents tests in `TestSlotContents` no longer re-implement the selection rule. They render through `SetupDisplayManager._render_device_list_screen` with a recording renderer and assert the (slot label, device name) each slot received. No file under `src/` changed.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `tests/test_device_list_focus.py` | New `_RecordingRenderer` (wraps a real `DeviceSurfaceRenderer`; records `(layout_item["slot"], device name or None)` and delegates; `__getattr__` delegates the rest). `_Render` gains `renderer=None` (default `DeviceSurfaceRenderer()`). The four list tests are rewritten; `_slots` is deleted. |

The argument order was confirmed from the call in `_render_device_list_screen`: `create_slot_surface(device, layout_item, selected=selected)`.

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Result

- Before: 559 passed. After: 559 passed (same count; four tests rewritten).
- Mutation check, `src/gtach/display/setup.py` restored with `git checkout` after each:

| Mutation of `zip(layout_data, (-1, 0, 1))` | Result on the four tests |
|---|---|
| Reversed: `(1, 0, -1)` (the prompt's check) | 3 failed, 1 passed |
| All zero: `(0, 0, 0)` (added) | 4 failed |
| Restored | 4 passed |

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| `grep -n '_slots'` returns nothing | Not literally met: the helper `_slots` is gone, but the grep also matches two unrelated existing test names, `test_layout_is_always_three_slots` and `test_slots_are_evenly_pitched`, which the constraints forbid changing. |
| Mutation check recorded | Met, with the deviation below |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- **Mutation check.** Reversing the offsets cannot fail `test_one_device_leaves_both_neighbours_empty`: with one device, both neighbours are absent either way, so the output is the same. Three of four tests fail under reversal, not four. A second mutation (all offsets 0) was added and fails all four, which shows the one-device test is also tied to the production rule.
- **Stale bytecode.** The first restore run reused the mutated `.pyc`, because the mutated and restored files have the same size and the same mtime second. The recorded runs used `PYTHONDONTWRITEBYTECODE=1` and a cleared `__pycache__`.

[Return to Table of Contents](<#table of contents>)

---

## 6. Items Kept

- The other test classes and the `create_slot_surface` tests in `TestSlotContents` are unchanged.
- `tests/test_device_list_focus.py` was formatted with black; only the new code changed.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification Outstanding

None.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-8a9022fc. |

---

Copyright (c) 2026 William Watson. MIT License.
