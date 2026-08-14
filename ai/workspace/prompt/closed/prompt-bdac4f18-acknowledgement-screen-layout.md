Created: 2026 August 14

# Prompt: Rewrite Acknowledgement Screen Layout

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
  iteration: 1
  coupled_docs:
    change_ref: "change-bdac4f18"
    change_iteration: 1

context:
  purpose: >
    The ACKNOWLEDGEMENT screen's body and instruction text clip the
    circular viewport (issue-bdac4f18): they are single un-wrapped
    lines rendered in Michroma at 24px/20px, too wide for the 480px
    circle. Replace them with pinned, on-device-measured text in a
    plain font.
  integration: >
    DisplayManager._draw_acknowledgement_mode() (src/gtach/display/manager.py)
    currently draws three render_text() calls: title (Michroma 72px,
    unchanged by this prompt), body ("OBD tachometer — experimental
    software", Michroma 24px, single line), instruction ("Tap to
    acknowledge and continue", Michroma 20px, single line). Replace the
    body and instruction rendering only. DisplayManager._get_cached_font()
    resolves through FontManager.get_font(), which loads
    Michroma-Regular.ttf for every size; a new sibling method,
    _get_plain_font(), is added to obtain the SDL default font instead,
    used only by this screen.
  constraints:
    - "Do not modify the title rendering block (Michroma, 72px, \"GTach\", position (240, 120)) — unchanged by this prompt."
    - "Do not modify _register_acknowledgement_regions() or _on_acknowledgement_dismissed() — the dismiss region and dismissal logic are unaffected by a text layout change."
    - "Do not modify FontManager or typography.py — _get_plain_font() is added to DisplayManager only, alongside the existing _get_cached_font(), and is not called from any other screen's draw method."
    - "Use the exact text, font size, and y-coordinates given below — they were measured against /opt/gtach/venv/bin/python3 on gtach.local (pygame 2.6.1, SDL 2.28.4, Python 3.9.2) and are not to be recomputed or re-wrapped by this prompt's execution."

specification:
  description: >
    Add DisplayManager._get_plain_font(size), then rewrite the body and
    instruction portions of _draw_acknowledgement_mode() to draw four
    fixed lines at measured coordinates using that font.
  requirements:
    functional:
      - "_get_plain_font(size) returns pygame.font.Font(None, size) — no font file path, the SDL/pygame default font — cached by size in a new self._plain_font_cache dict, analogous in structure to FontManager's cache but local to DisplayManager and never touching Michroma."
      - "_get_plain_font(size) catches any exception from font creation and returns None, matching _get_cached_font()'s existing failure behaviour, so a missing font never raises out of the render path."
      - "The three body lines below are drawn via self._get_plain_font(18), each centred at x=240, at the given y, in self._DISCONNECTED_TEXT_COLOUR, replacing the current single 'OBD tachometer — experimental software' line entirely:"
      - "  y=266: THIS SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY"
      - "  y=290: OF ANY KIND. THE AUTHOR IS NOT LIABLE FOR ANY CLAIM,"
      - "  y=314: DAMAGES, OR OTHER LIABILITY ARISING FROM ITS USE."
      - "The instruction line is drawn via self._get_plain_font(20), centred at (240, 400), replacing the current y=360 position: \"Tap to acknowledge and continue\""
      - "The title block (Michroma 72px \"GTach\" at (240, 120)) is unchanged, byte-for-byte, from its current form."
      - "_register_acknowledgement_regions() and _on_acknowledgement_dismissed() are unchanged, byte-for-byte, from their current form."
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Match the existing try/except-with-logging style in _draw_acknowledgement_mode() and _get_cached_font()."
        - "No new imports required — pygame is already imported in manager.py."

design:
  architecture: "One new small font-cache method, one rewritten render method; no new components."
  components:
    - name: "DisplayManager._get_plain_font"
      type: "method"
      purpose: "Return a cached SDL-default-font pygame.font.Font for the given size, bypassing FontManager's Michroma resolution."
      interface:
        inputs:
          - name: "size"
            type: "int"
            description: "Font size in pixels."
        outputs:
          type: "Optional[pygame.font.Font]"
          description: "Cached font object, or None on failure."
        raises: []
      logic:
        - "Insert immediately after _get_cached_font() in the class body."
        - "On first call for a given size: create pygame.font.Font(None, size) inside a try/except; on success store it in self._plain_font_cache[size] and return it; on exception log at ERROR (matching _get_cached_font()'s style) and return None."
        - "On subsequent calls for a size already in self._plain_font_cache, return the cached object directly without recreating it."
        - "self._plain_font_cache is initialised as an empty dict; add its initialisation to __init__ alongside the other font/cache-related attributes (e.g. near self._registered_view), or lazily via getattr(self, '_plain_font_cache', None) followed by creation if absent — either is acceptable as long as the dict persists across calls on the same instance."
    - name: "DisplayManager._draw_acknowledgement_mode"
      type: "method"
      purpose: "Existing method. Replace the body and instruction render_text() calls; leave the title block untouched."
      logic:
        - >
          Locate the title block (self._get_cached_font(72), "GTach",
          position (240, 120)) — leave it exactly as it is.
        - >
          Replace the body block — currently one
          self._get_cached_font(24) call and one render_text() call
          for "OBD tachometer — experimental software" at (240, 240) —
          with: body_font = self._get_plain_font(18); if body_font:
          three render_text() calls, one per line listed in
          specification.requirements.functional above, each at (240, y)
          with center=True, using body_font and
          self._DISCONNECTED_TEXT_COLOUR.
        - >
          Replace the instruction block — currently
          self._get_cached_font(20) and render_text() for "Tap to
          acknowledge and continue" at (240, 360) — with:
          instruction_font = self._get_plain_font(20); if
          instruction_font: one render_text() call for "Tap to
          acknowledge and continue" at (240, 400), center=True, using
          instruction_font and self._DISCONNECTED_TEXT_COLOUR.
        - >
          Leave the surrounding try/except and the
          self.logger.debug("Acknowledgement screen rendered") /
          except-branch logging exactly as they are.
  dependencies:
    internal: []
    external: []

error_handling:
  strategy: >
    _get_plain_font() catches font-creation failure and returns None,
    matching _get_cached_font(). _draw_acknowledgement_mode()'s
    existing `if body_font:` / `if instruction_font:` guards (matching
    the existing `if title_font:` pattern already in the method) mean a
    failed font simply skips that block's render_text() calls rather
    than raising.
  exceptions:
    - exception: "Exception (broad, matching _get_cached_font())"
      condition: "pygame.font.Font(None, size) raises"
      handling: "Log at ERROR; _get_plain_font() returns None."
  logging:
    level: "ERROR"
    format: "Match _get_cached_font()'s existing style."

testing:
  unit_tests:
    - scenario: "_get_plain_font(18) called twice with the same size"
      expected: "Second call returns the same cached object as the first (identity check), not a newly constructed one."
    - scenario: "_draw_acknowledgement_mode() called with pygame unavailable / font creation failing"
      expected: "No exception propagates; the method logs and returns, matching current behaviour when title_font is None."
  edge_cases:
    - "None — the four lines and their coordinates are fixed literals verified in change-bdac4f18; no runtime wrapping or measurement occurs in this prompt's code."
  validation:
    - "Full pytest suite run after the edits; no new failures relative to the pre-change baseline."
    - "Manual on-device visual check per change-bdac4f18 §testing_requirements."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "Modified per design section above: one new method, one rewritten method."

success_criteria:
  - "grep -n '_get_plain_font' src/gtach/display/manager.py returns exactly one 'def _get_plain_font' and four call sites (three at size 18, one at size 20), all inside _draw_acknowledgement_mode()."
  - "grep -n 'OBD tachometer' src/gtach/display/manager.py returns no match anywhere in the file."
  - "grep -n 'THIS SOFTWARE IS PROVIDED' src/gtach/display/manager.py matches exactly once."
  - "grep -n 'Tap to acknowledge and continue' src/gtach/display/manager.py matches exactly once, and the line containing it is followed within the same render_text() call by the literal (240, 400)."
  - "The title render_text() call for \"GTach\" at (240, 120) using self._get_cached_font(72) is present and unchanged."
  - "_register_acknowledgement_regions() and _on_acknowledgement_dismissed() are byte-for-byte unchanged from their state before this prompt was executed."
  - "python -m py_compile src/gtach/display/manager.py succeeds."
  - "Full pytest suite (pytest tests/) passes with no new failures relative to the pre-change baseline."

notes: >
  This prompt implements change-bdac4f18 / issue-bdac4f18, and depends
  on change-e22142da already being implemented (ACKNOWLEDGEMENT must be
  reachable for this screen to ever render). No tactical_brief is
  required — target_profile is claude_code, not ael.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial prompt creation."

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
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
