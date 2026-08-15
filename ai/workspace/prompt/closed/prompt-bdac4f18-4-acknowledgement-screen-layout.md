Created: 2026 August 14

# Prompt: Fix Acknowledgement Instruction Optical Size Mismatch (Iteration 4)

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-bdac4f18"
  task_type: "refactor"
  source_ref: "change-bdac4f18"
  target_profile: "claude_code"
  date: "2026-08-14"
  iteration: 4
  coupled_docs:
    change_ref: "change-bdac4f18"
    change_iteration: 4

context:
  purpose: >
    Iteration 3 of change-bdac4f18 (prompt-bdac4f18-3, now closed) is
    already implemented on disk: the disclaimer body is four ALL CAPS
    lines at 24px (y=208/240/272/304) and the instruction line is
    mixed-case text ("Tap to acknowledge and continue") also at 24px,
    at y=400. The reporter observed the instruction text still looked
    smaller than the body despite the identical font size. Measurement
    (font.metrics() on gtach.local) confirmed this is a cap-height vs
    x-height optical effect, not a code defect: capitals reach 12px
    above baseline, lowercase x-height letters only 9-10px, and the
    body text is all capitals while the instruction text was mostly
    lowercase. The fix is ALL CAPS instruction text at the same 24px
    size. Because ALL CAPS is wider than the original mixed-case
    string, its margin at the original y=400 position drops to 12.2px;
    the line is moved to y=350 (closer to the display's vertical
    centre, which widens the available chord) to restore a margin
    consistent with the rest of the design.
  integration: >
    This prompt modifies ONLY the instruction block inside
    DisplayManager._draw_acknowledgement_mode() (src/gtach/display/manager.py):
    its text string and its y-coordinate. The font size call
    (self._get_plain_font(24)) is unchanged. The title block, the body
    block, _get_plain_font() itself, _register_acknowledgement_regions(),
    and _on_acknowledgement_dismissed() are all unchanged from the
    current (iteration 3) implementation.
  constraints:
    - "Do not modify the title rendering block (Michroma, 72px, \"GTach\", position (240, 120))."
    - "Do not modify the body block \u2014 four self._get_plain_font(24) lines at y=208/240/272/304 \u2014 it is unchanged from iteration 2."
    - "Do not modify _get_plain_font() itself, and do not change the instruction block's font size argument \u2014 it stays self._get_plain_font(24), exactly as iteration 3 left it. Only the text string and the y-coordinate change."
    - "Do not modify _register_acknowledgement_regions() \u2014 the dismiss region is a full-screen rect independent of where the instruction text is drawn, and needs no change when that text moves."
    - "Do not modify _on_acknowledgement_dismissed()."
    - "Do not modify FontManager or typography.py."
    - "Use the exact text and y-coordinate given below \u2014 measured and chosen against /opt/gtach/venv/bin/python3 on gtach.local (pygame 2.6.1, SDL 2.28.4, Python 3.9.2) via a per-glyph metrics probe and a y-position sweep, and are not to be recomputed by this prompt's execution."

specification:
  description: >
    Change the instruction block's text from "Tap to acknowledge and
    continue" to "TAP TO ACKNOWLEDGE AND CONTINUE", and its position's
    y-coordinate from 400 to 350. The font size call and every other
    argument to that render_text() call are unchanged.
  requirements:
    functional:
      - "The instruction block's text string changes from \"Tap to acknowledge and continue\" to \"TAP TO ACKNOWLEDGE AND CONTINUE\"."
      - "The instruction block's position changes from (240, 400) to (240, 350)."
      - "The instruction block's font call remains self._get_plain_font(24), unchanged from iteration 3."
      - "The instruction block's center=True argument and self._DISCONNECTED_TEXT_COLOUR colour argument are unchanged."
      - "The body block (four self._get_plain_font(24) lines at y=208/240/272/304) is unchanged, byte-for-byte, from its current form."
      - "The title block (Michroma 72px \"GTach\" at (240, 120)) is unchanged, byte-for-byte, from its current form."
      - "_get_plain_font(), _register_acknowledgement_regions(), and _on_acknowledgement_dismissed() are unchanged, byte-for-byte."
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Match the existing try/except-with-logging style already present in _draw_acknowledgement_mode()."
        - "No new imports required."

design:
  architecture: "A two-literal change (text string, y-coordinate) inside an existing method; no new components, no new methods."
  components:
    - name: "DisplayManager._draw_acknowledgement_mode"
      type: "method"
      purpose: "Existing method (already modified three times, by iterations 1, 2, and 3). Change only the instruction block's text and y-coordinate."
      logic:
        - >
          Locate the instruction block: currently
          "instruction_font = self._get_plain_font(24)" followed by an
          "if instruction_font:" guard containing one render_text()
          call for "Tap to acknowledge and continue" at (240, 400).
        - >
          Change the text argument from "Tap to acknowledge and
          continue" to "TAP TO ACKNOWLEDGE AND CONTINUE", and the
          position argument's y value from 400 to 350 \u2014 i.e. the
          position tuple becomes (240, 350). No other argument to this
          render_text() call changes: font remains instruction_font
          from self._get_plain_font(24), colour remains
          self._DISCONNECTED_TEXT_COLOUR, center remains True.
        - >
          Everything before this block (the title block and the body
          block) and everything after it (the trailing
          self.logger.debug(...) call and the except handler) is left
          exactly as it currently stands.
  dependencies:
    internal: []
    external: []

error_handling:
  strategy: >
    Unchanged from iteration 3 \u2014 the existing "if instruction_font:"
    guard already means a failed font simply skips the instruction
    render_text() call rather than raising; this prompt does not alter
    that pattern, and does not touch font acquisition at all.
  exceptions: []
  logging:
    level: "ERROR"
    format: "Unchanged from iteration 3."

testing:
  unit_tests:
    - scenario: "_draw_acknowledgement_mode() called with pygame available"
      expected: "The instruction render_text() call occurs with text \"TAP TO ACKNOWLEDGE AND CONTINUE\" at position (240, 350), still using a font from self._get_plain_font(24)."
  edge_cases:
    - "None \u2014 the text and y-coordinate are fixed literals verified in change-bdac4f18 iteration 4; no runtime measurement occurs in this prompt's code."
  validation:
    - "Full pytest suite run after the edit; no new failures relative to the pre-change baseline."
    - "Manual on-device visual check: instruction line reads in ALL CAPS, sits closer to the disclaimer block than before, visually matches the body text's apparent size, and still clears the bezel."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "Instruction block's text string and y-coordinate within _draw_acknowledgement_mode() changed; all other lines in the method unchanged."

success_criteria:
  - "grep -n '_get_plain_font' src/gtach/display/manager.py returns exactly one 'def _get_plain_font' and five call sites, all at size 24, all inside _draw_acknowledgement_mode() \u2014 unchanged count and sizes from iteration 3."
  - "grep -n 'Tap to acknowledge and continue' src/gtach/display/manager.py returns no match anywhere in the file."
  - "grep -n 'TAP TO ACKNOWLEDGE AND CONTINUE' src/gtach/display/manager.py matches exactly once."
  - "The render_text() call containing \"TAP TO ACKNOWLEDGE AND CONTINUE\" has (240, 350) as its position argument, not (240, 400)."
  - "The title render_text() call for \"GTach\" at (240, 120) using self._get_cached_font(72) is present and unchanged."
  - "The four body render_text() calls at y=208/240/272/304 using self._get_plain_font(24) are present and unchanged."
  - "_get_plain_font(), _register_acknowledgement_regions(), and _on_acknowledgement_dismissed() are byte-for-byte unchanged from their state before this prompt was executed."
  - "python -m py_compile src/gtach/display/manager.py succeeds."
  - "Full pytest suite (pytest tests/) passes with no new failures relative to the pre-change baseline."

notes: >
  This prompt implements change-bdac4f18 iteration 4 / issue-bdac4f18,
  superseding the instruction-line text and position already delivered
  by the closed prompt-bdac4f18-3 (ai/workspace/prompt/closed/). It
  depends on that iteration-3 execution already being present on disk
  \u2014 the success criteria explicitly reject the old mixed-case text and
  confirm the new ALL CAPS text and y-coordinate. No tactical_brief is
  required \u2014 target_profile is claude_code, not ael.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial iteration-4 prompt creation, superseding the closed iteration-3 prompt-bdac4f18-3."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.11"
  schema_type: "t04_prompt"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation (iteration 4). |

---

Copyright (c) 2026 William Watson. MIT License.
