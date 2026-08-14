Created: 2026 August 14

# Report: Reposition OPTIONS Screen Title and Controls

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Edits Applied](<#3.0 edits applied>)
- [4.0 Viewport Safety at the New Column Top](<#4.0 viewport safety at the new column top>)
- [5.0 A Pre-Existing Working-Tree Change](<#5.0 a pre-existing working-tree change>)
- [6.0 Verification Method](<#6.0 verification method>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Deviations from the Prompt Specification](<#8.0 deviations from the prompt specification>)
- [9.0 Commit Record](<#9.0 commit record>)
- [10.0 Work Remaining](<#10.0 work remaining>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records the implementation of
`prompt-61c7ba7f-options-title-status-overlay.md` (iteration 1, coupled
to `change-61c7ba7f` and `issue-61c7ba7f`).

The OPTIONS menu's title, button column, page indicator and hint text
move down by a uniform 45 px so the title no longer sits under the
status indicator dot. The indicator itself is untouched.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Instruction and Outcome

Four fixed y-coordinate literals in `src/gtach/display/manager.py` were
to be changed, all within `_draw_options_menu` and
`_register_options_menu_regions`. All four were changed as specified.
No other screen, colour, dimension, label, or draw call was altered,
and no function, parameter, or state was added.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

All in `src/gtach/display/manager.py`.

| Element | Was | Now | Location |
|---|---|---|---|
| `"Options"` title render position | `(240, 55)` | `(240, 100)` | `_draw_options_menu` |
| `_button_column` column top | `top=140` | `top=185` | `_register_options_menu_regions` |
| Page indicator dot centre y | `350` | `395` | `_draw_options_menu` (both the filled and the outlined `pygame.draw.circle` calls) |
| `"Swipe up to return"` hint position | `(240, 400)` | `(240, 445)` | `_draw_options_menu` |

The page indicator y appears twice in the loop — once for the active
page's filled dot, once for the outlined inactive dots. Both were
changed; leaving either would have split the indicator across two rows.

One comment block above the `_button_column` call was updated. It
stated the column's span (`y 140 to 300`) and the indicator's y
(`350`), both of which the edits invalidate. It now reads `y 185 to
345` and `y 395`, and names `change-61c7ba7f` as the reason the column
sits lower. No executable text changed with it.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Viewport Safety at the New Column Top

`_button_column` logs at ERROR when any button corner falls outside the
r=238 circular viewport. The prompt required this check be preserved
unchanged, so the new geometry was checked by hand against it rather
than by relaxing it.

At `top=185`, with `width=300`, `height=72` and `separation=16`:

- Button 1 spans y 185–257, button 2 spans y 273–345.
- x spans 90–390, so every corner is 150 px from the x centre.
- The worst corner is a bottom corner of button 2, at dy = 345 − 240 = 105.
- 150² + 105² = 33 525, against a radius² of 238² = 56 644.

Every corner is comfortably inside. Both pages use identical geometry —
they differ only in which two controls are registered — so this holds
for page 0 (`simulation_mode`, `debug_toggle`) and page 1
(`clear_settings`, `check_updates`) alike, satisfying the prompt's
edge case.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 A Pre-Existing Working-Tree Change

`src/gtach/display/manager.py` already carried an uncommitted edit when
this task began: the DISCONNECTED screen's title moved from y=155 to
y=145. That belongs to other work, the prompt places DISCONNECTED out
of scope, and it was left untouched — neither reverted nor committed
here. It remains uncommitted in the working tree.

The same is true of the untracked
`ai/workspace/change/change-950128c0-remove-shift-rim-borders.md` and
`ai/workspace/issues/issue-950128c0-remove-shift-rim-borders.md`, and
of the modification to `ai/task.md`. None were staged.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Verification Method

- `python -c "import ast; ast.parse(...)"` on the edited file — parses.
- `grep -n 'top=140\|(240, 55)' src/gtach/display/manager.py` — no
  occurrences remain anywhere in the file, executable or otherwise.
- `git diff --cached --stat` on `manager.py` — 9 insertions, 7
  deletions across three hunks: the four functional edits plus the
  corrected comment block. The pre-existing DISCONNECTED edit described
  in §5.0 was deliberately excluded from the commit and left unstaged.

The test suite was not run. It covers one unrelated module and exercises
no rendering geometry, so it can neither confirm nor refute these edits.
Confirmation is visual and on-target, per the change document's testing
requirements.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

| Criterion | Status |
|---|---|
| Title render call uses `(240, 100)` | Met |
| `_button_column` call uses `top=185` | Met |
| Page indicator loop uses y=395 | Met |
| Hint render call uses `(240, 445)` | Met |
| No executable `(240, 55)` in `_draw_options_menu` | Met — none in the file |
| No `top=140` in `_register_options_menu_regions` | Met — none in the file |
| No other literal, signature, class, or draw call altered | Met |

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Deviations from the Prompt Specification

One, and it is non-executable. The prompt's `logic` entry for
`_draw_options_menu` names a single page-indicator y; the code has two
occurrences of it, and both were changed (§3.0). The prompt's comment
block above `_button_column` was also corrected, since leaving it would
have left the file asserting geometry it no longer has.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Commit Record

One commit on `main`, containing the four coordinate edits, the
corrected comment, this report, and the prompt T-Doc moved to
`ai/workspace/prompt/closed/`. Pushed to `origin/main`.

Per the task instruction, `change-61c7ba7f` and `issue-61c7ba7f` remain
active pending on-target test results.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Work Remaining

On-target visual verification on the Raspberry Pi Zero 2W: confirm on
both options pages that the title clears the status indicator, that
both buttons render fully within the circular face, and that the page
indicator and the swipe hint remain legible at their new heights.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial report |

---

Copyright (c) 2026 William Watson. MIT License.
