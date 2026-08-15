Created: 2026 August 14

# Prompt: Enlarge Acknowledgement Instruction Text (Iteration 3)

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
  iteration: 3
  coupled_docs:
    change_ref: "change-bdac4f18"
    change_iteration: 3

context:
  purpose: >
    Iteration 2 of change-bdac4f18 (prompt-bdac4f18-2, now closed) is
    already implemented on disk: the disclaimer body is four lines at
    24px (y=208/240/272/304) and the instruction line is one line at
    20px (y=400). The reporter asked for the instruction line enlarged.
    A size sweep at the existing y=400 position selected 24px, matching
    the body text size.
  integration: >
    This prompt modifies ONLY the instruction block inside
    DisplayManager._draw_acknowledgement_mode() (src/gtach/display/manager.py):
    the self._get_plain_font(20) call and its one render_text() call.
    The title block, the body block, _get_plain_font() itself,
    _register_acknowledgement_regions(), and _on_acknowledgement_dismissed()
    are all unchanged from the current (iteration 2) implementation.
  constraints:
    - "Do not modify the title rendering block (Michroma, 72px, \"GTach\", position (240, 120))."
    - "Do not modify the body block \u2014 four self._get_plain_font(24) lines at y=208/240/272/304 \u2014 it is unchanged from iteration 2."
    - "Do not modify _get_plain_font() itself."
    - "Do not modify the instruction line's text (\"Tap to acknowledge and continue\") or its y-coordinate (400) \u2014 only its font size changes."
    - "Do not modify _register_acknowledgement_regions() or _on_acknowledgement_dismissed()."
    - "Do not modify FontManager or typography.py."
    - "Use the exact size given below \u2014 measured against /opt/gtach/venv/bin/python3 on gtach.local (pygame 2.6.1, SDL 2.28.4, Python 3.9.2) via a size sweep from 20px to 40px at the fixed y=400 position, and is not to be recomputed by this prompt's execution."

specification:
  description: >
    Change the single self._get_plain_font(20) call in the instruction
    block to self._get_plain_font(24). Nothing else in the method
    changes.
  requirements:
    functional:
      - "The instruction block's font call changes from self._get_plain_font(20) to self._get_plain_font(24)."
      - "The instruction line's text (\"Tap to acknowledge and continue\"), position ((240, 400), center=True), and colour (self._DISCONNECTED_TEXT_COLOUR) are unchanged."
      - "The body block (four self._get_plain_font(24) lines at y=208/240/272/304) is unchanged, byte-for-byte, from its current form."
      - "The title block (Michroma 72px \"GTach\" at (240, 120)) is unchanged, byte-for-byte, from its current form."
      - "_get_plain_font() itself is unchanged, byte-for-byte."
      - "_register_acknowledgement_regions() and _on_acknowledgement_dismissed() are unchanged, byte-for-byte."
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Match the existing try/except-with-logging style already present in _draw_acknowledgement_mode()."
        - "No new imports required."

design:
  architecture: "One single-token change inside an existing method; no new components, no new methods."
  components:
    - name: "DisplayManager._draw_acknowledgement_mode"
      type: "method"
      purpose: "Existing method (already modified twice, by iterations 1 and 2). Change only the instruction block's font size argument."
      logic:
        - >
          Locate the instruction block: currently
          "instruction_font = self._get_plain_font(20)" followed by an
          "if instruction_font:" guard containing one render_text()
          call for "Tap to acknowledge and continue" at (240, 400).
        - >
          Change "self._get_plain_font(20)" to
          "self._get_plain_font(24)". No other token in this block
          changes \u2014 the render_text() call, its text argument, its
          position argument, and its colour argument are all identical
          to the current form.
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
    Unchanged from iteration 2 \u2014 the existing "if instruction_font:"
    guard already means a failed font simply skips the instruction
    render_text() call rather than raising; this prompt does not alter
    that pattern.
  exceptions: []
  logging:
    level: "ERROR"
    format: "Unchanged from iteration 2."

testing:
  unit_tests:
    - scenario: "_draw_acknowledgement_mode() called with pygame available"
      expected: "The instruction render_text() call occurs using a font from self._get_plain_font(24), not self._get_plain_font(20)."
  edge_cases:
    - "None \u2014 the size is a fixed literal verified in change-bdac4f18 iteration 3; no runtime measurement occurs in this prompt's code."
  validation:
    - "Full pytest suite run after the edit; no new failures relative to the pre-change baseline."
    - "Manual on-device visual check: instruction line visibly larger, matching the body text size, still fully clear of the bezel."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "Instruction block's font-size argument within _draw_acknowledgement_mode() changed from 20 to 24; all other lines in the method unchanged."

success_criteria:
  - "grep -n '_get_plain_font' src/gtach/display/manager.py returns exactly one 'def _get_plain_font' and five call sites, all at size 24, all inside _draw_acknowledgement_mode()."
  - "grep -n '_get_plain_font(20)' src/gtach/display/manager.py returns no match anywhere in the file."
  - "grep -n 'Tap to acknowledge and continue' src/gtach/display/manager.py matches exactly once, and the line containing it is followed within the same render_text() call by the literal (240, 400) \u2014 unchanged from iteration 2."
  - "The title render_text() call for \"GTach\" at (240, 120) using self._get_cached_font(72) is present and unchanged."
  - "The four body render_text() calls at y=208/240/272/304 using self._get_plain_font(24) are present and unchanged."
  - "_get_plain_font(), _register_acknowledgement_regions(), and _on_acknowledgement_dismissed() are byte-for-byte unchanged from their state before this prompt was executed."
  - "python -m py_compile src/gtach/display/manager.py succeeds."
  - "Full pytest suite (pytest tests/) passes with no new failures relative to the pre-change baseline."

notes: >
  This prompt implements change-bdac4f18 iteration 3 / issue-bdac4f18,
  superseding the instruction-line size already delivered by the
  closed prompt-bdac4f18-2 (ai/workspace/prompt/closed/). It depends on
  that iteration-2 execution already being present on disk \u2014 the
  success criteria explicitly reject the old size-20 call and confirm
  the new size-24 one. No tactical_brief is required \u2014 target_profile
  is claude_code, not ael.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial iteration-3 prompt creation, superseding the closed iteration-2 prompt-bdac4f18-2."

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
| 1.0     | 2026-08-14 | Initial creation (iteration 3). |

---

Copyright (c) 2026 William Watson. MIT License.
