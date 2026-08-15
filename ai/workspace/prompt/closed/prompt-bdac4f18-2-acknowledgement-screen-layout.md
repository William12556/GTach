Created: 2026 August 14

# Prompt: Enlarge and Raise Acknowledgement Screen Disclaimer (Iteration 2)

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
  iteration: 2
  coupled_docs:
    change_ref: "change-bdac4f18"
    change_iteration: 2

context:
  purpose: >
    Iteration 1 of change-bdac4f18 (prompt-bdac4f18, now closed) is
    already implemented on disk: _draw_acknowledgement_mode() draws
    three plain-font body lines at 18px (y=266/290/314) and one
    instruction line at 20px (y=400). The reporter asked for the
    disclaimer text enlarged and moved closer to the title, given
    unused vertical space. A size sweep measured on gtach.local
    selected 24px/four lines, starting immediately below the title's
    measured (not estimated) bounding box.
  integration: >
    This prompt modifies ONLY the body block inside
    DisplayManager._draw_acknowledgement_mode() (src/gtach/display/manager.py):
    the self._get_plain_font(18) call and its three render_text() calls.
    The title block, the instruction block, _get_plain_font() itself,
    _register_acknowledgement_regions(), and _on_acknowledgement_dismissed()
    are all unchanged from the current (iteration 1) implementation.
  constraints:
    - "Do not modify the title rendering block (Michroma, 72px, \"GTach\", position (240, 120))."
    - "Do not modify the instruction block — self._get_plain_font(20), \"Tap to acknowledge and continue\", position (240, 400) — it is unchanged from iteration 1."
    - "Do not modify _get_plain_font() itself — it already exists from iteration 1 and its signature/behaviour/caching are correct as-is; this prompt only changes which size and how many times it is called for the body block."
    - "Do not modify _register_acknowledgement_regions() or _on_acknowledgement_dismissed()."
    - "Do not modify FontManager or typography.py."
    - "Use the exact text, font size, and y-coordinates given below — measured against /opt/gtach/venv/bin/python3 on gtach.local (pygame 2.6.1, SDL 2.28.4, Python 3.9.2) via a size sweep from 18px to 28px, and are not to be recomputed or re-wrapped by this prompt's execution."

specification:
  description: >
    Replace the three self._get_plain_font(18) body lines (y=266/290/314)
    with four self._get_plain_font(24) body lines (y=208/240/272/304)
    inside _draw_acknowledgement_mode(). Nothing else in the method
    changes.
  requirements:
    functional:
      - "The current body block — one self._get_plain_font(18) call and three render_text() calls at y=266/290/314 for the three iteration-1 lines — is replaced entirely."
      - "The four body lines below are drawn via self._get_plain_font(24), each centred at x=240, at the given y, in self._DISCONNECTED_TEXT_COLOUR:"
      - "  y=208: THIS SOFTWARE IS PROVIDED \"AS IS\", WITHOUT"
      - "  y=240: WARRANTY OF ANY KIND. THE AUTHOR IS NOT"
      - "  y=272: LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER"
      - "  y=304: LIABILITY ARISING FROM ITS USE."
      - "The instruction block (self._get_plain_font(20), \"Tap to acknowledge and continue\", (240, 400)) is unchanged, byte-for-byte, from its current form."
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
  architecture: "One rewritten block inside an existing method; no new components, no new methods."
  components:
    - name: "DisplayManager._draw_acknowledgement_mode"
      type: "method"
      purpose: "Existing method (already modified once, by iteration 1). Replace only the body block's font size, line count, text, and y-coordinates."
      logic:
        - >
          Locate the body block: currently
          "body_font = self._get_plain_font(18)" followed by an
          "if body_font:" guard containing three render_text() calls
          for the iteration-1 lines at y=266, y=290, y=314.
        - >
          Replace with: "body_font = self._get_plain_font(24)"
          followed by an "if body_font:" guard containing four
          render_text() calls, one per line listed in
          specification.requirements.functional above, each at
          (240, y) with center=True, using body_font and
          self._DISCONNECTED_TEXT_COLOUR — matching the existing
          per-line render_text() call pattern from iteration 1 exactly,
          just with four lines instead of three and the new size/y
          values.
        - >
          Everything before this block (the title block) and
          everything after it (the instruction block, the trailing
          self.logger.debug(...) call, and the except handler) is left
          exactly as it currently stands.
  dependencies:
    internal: []
    external: []

error_handling:
  strategy: >
    Unchanged from iteration 1 — the existing "if body_font:" guard
    already means a failed font simply skips the body render_text()
    calls rather than raising; this prompt does not alter that
    pattern, only the size passed to _get_plain_font() and the
    line/coordinate literals inside the guard.
  exceptions: []
  logging:
    level: "ERROR"
    format: "Unchanged from iteration 1."

testing:
  unit_tests:
    - scenario: "_draw_acknowledgement_mode() called with pygame available"
      expected: "Four render_text() calls occur for the body block, at y=208/240/272/304, using a font from self._get_plain_font(24)."
  edge_cases:
    - "None — the four lines and their coordinates are fixed literals verified in change-bdac4f18 iteration 2; no runtime wrapping or measurement occurs in this prompt's code."
  validation:
    - "Full pytest suite run after the edits; no new failures relative to the pre-change baseline."
    - "Manual on-device visual check: four body lines and the instruction line all visible with no clipping, body block visibly closer to the title than iteration 1."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "Body block within _draw_acknowledgement_mode() modified per design section above; all other lines in the method unchanged."

success_criteria:
  - "grep -n '_get_plain_font' src/gtach/display/manager.py returns exactly one 'def _get_plain_font' and five call sites (four at size 24, one at size 20), all inside _draw_acknowledgement_mode()."
  - "grep -n '_get_plain_font(18)' src/gtach/display/manager.py returns no match — the iteration-1 body size is fully replaced."
  - "grep -n 'THIS SOFTWARE IS PROVIDED' src/gtach/display/manager.py matches exactly once, on a line whose render_text() call centres it at y=208."
  - "grep -n 'LIABILITY ARISING FROM ITS USE' src/gtach/display/manager.py matches exactly once, on a line whose render_text() call centres it at y=304."
  - "grep -n 'Tap to acknowledge and continue' src/gtach/display/manager.py matches exactly once, and the line containing it is followed within the same render_text() call by the literal (240, 400) — unchanged from iteration 1."
  - "The title render_text() call for \"GTach\" at (240, 120) using self._get_cached_font(72) is present and unchanged."
  - "_get_plain_font(), _register_acknowledgement_regions(), and _on_acknowledgement_dismissed() are byte-for-byte unchanged from their state before this prompt was executed."
  - "python -m py_compile src/gtach/display/manager.py succeeds."
  - "Full pytest suite (pytest tests/) passes with no new failures relative to the pre-change baseline."

notes: >
  This prompt implements change-bdac4f18 iteration 2 / issue-bdac4f18,
  superseding the iteration-1 body layout already delivered by the
  closed prompt-bdac4f18 (ai/workspace/prompt/closed/). It depends on
  that iteration-1 execution already being present on disk — the
  success criteria explicitly reject the old 18px call and confirm the
  new 24px one. No tactical_brief is required — target_profile is
  claude_code, not ael.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial iteration-2 prompt creation, superseding the closed iteration-1 prompt-bdac4f18."

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
| 1.0     | 2026-08-14 | Initial creation (iteration 2). |

---

Copyright (c) 2026 William Watson. MIT License.
