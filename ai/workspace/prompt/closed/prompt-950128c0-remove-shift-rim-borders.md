Created: 2026 August 13

# Prompt: Remove Shift Rim Borders

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-950128c0"
  task_type: "refactor"
  source_ref: "change-950128c0"
  target_profile: "claude_code"
  date: "2026-08-13"
  iteration: 1
  coupled_docs:
    change_ref: "change-950128c0"
    change_iteration: 1

context:
  purpose: >
    Remove the coloured rim border drawn on every screen and the
    shift-state cue logic that fed it on RADIAL, with no replacement
    indicator on any channel.
  integration: >
    DisplayManager._draw_radial_mode() and six other DisplayManager draw
    methods currently call self._draw_shift_border(); RADIAL additionally
    calls self._get_shift_cue() to pick the border colour and the centre
    disc's flash state. Both methods are removed. RADIAL's centre disc
    keeps showing the active RPM band's colour, sourced directly from
    Palette.band_centres, with no flash.
  constraints:
    - "Do not add a replacement shift-state indicator on any visual channel — declined by the requester."
    - "Do not change RPM band thresholds, the arc sweep, the boundary marks, or the DISCONNECTED reconnect spinner."
    - "Palette.band_centres must remain on the dataclass and on both DAY_PALETTE and NIGHT_PALETTE — it is the centre disc's unconditional source after this change, not only a fallback."

specification:
  description: >
    Delete DisplayManager._draw_shift_border() and
    DisplayManager._get_shift_cue() from
    src/gtach/display/manager.py. Remove the two methods' seven call
    sites. In _draw_radial_mode(), replace the deleted
    _get_shift_cue() call with a direct read of
    palette.band_centres[active_band] for the centre disc colour, and
    change the RADIAL background fill from radius 232 to radius 244 so
    the circular face fills the space the border ring used to occupy.
    In the six other call sites, delete the
    self._draw_shift_border(...) line with no other change to the
    surrounding method. In src/gtach/display/models.py, remove the
    band_centres_lit, shift_border_caution, shift_centre_dark,
    shift_border_normal and shift_border_down fields from the Palette
    dataclass and the matching keyword arguments (and their comment
    blocks) from DAY_PALETTE and NIGHT_PALETTE. In the three listed
    test files, remove the
    "host._draw_shift_border = lambda colour: None" stub line.
  requirements:
    functional:
      - "No screen in the running application draws a coloured rim border."
      - "RADIAL's centre disc shows palette.band_centres[active_band] unconditionally — no flash, no shift-state colour."
      - "RADIAL's circular face has the same outer radius (244 px from centre (240, 240)) it had when the border ring occupied that space, so no unpainted ring is introduced."
      - "The six non-RADIAL screens render with no visible change from their current appearance."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "No new exception handling required — this is a deletion/simplification, not new logic."
        - "Preserve existing docstring and comment style on any method that is edited rather than deleted."
        - "Do not leave orphaned imports, unused local variables, or dead comments referencing the removed methods."

design:
  architecture: "Direct deletion and simplification within the existing DisplayManager render-method structure; no new components."
  components:
    - name: "DisplayManager._draw_radial_mode"
      type: "method"
      purpose: "Draw the RPM gauge screen; loses the border draw and the shift-cue lookup, keeps the band-coloured centre disc."
      logic:
        - >
          Locate the block:
          "active_band, band_colour = self._get_band_colour(rpm)"
          followed by
          "border_colour, _, _, centre_colour = self._get_shift_cue(
              rpm, active_band
          )".
          Replace the second statement with:
          "centre_colour = palette.band_centres[active_band]".
        - >
          Locate the block:
          "surface.fill((0, 0, 0))
          self._draw_shift_border(border_colour)
          pygame.draw.circle(surface, palette.ground, center, 232)".
          Replace with:
          "surface.fill((0, 0, 0))
          pygame.draw.circle(surface, palette.ground, center, 244)".
          The comment immediately above this block ("Fill corners black
          ... draw border ring as solid filled circle at r=244, then
          background at r=232.") must be updated to describe the new
          two-step sequence (fill corners black, then fill the full
          circular face at r=244) rather than describing a border step
          that no longer exists.
        - >
          The line "# 6. (Border already drawn at step 1)" mid-method
          references the removed border step and must be deleted along
          with its numbered-step comment, or renumbered/reworded so the
          remaining step comments stay accurate and sequential.
    - name: "DisplayManager._draw_shift_border"
      type: "method"
      purpose: "Deleted in full, including its docstring."
    - name: "DisplayManager._get_shift_cue"
      type: "method"
      purpose: "Deleted in full, including its docstring."
    - name: "DisplayManager._draw_options_menu"
      type: "method"
      purpose: "Delete its 'self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)' line only."
    - name: "DisplayManager._draw_confirm_view"
      type: "method"
      purpose: "Delete its 'self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)' line only."
    - name: "DisplayManager._draw_update_view"
      type: "method"
      purpose: "Delete its 'self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)' line only."
    - name: "DisplayManager._draw_acknowledgement_mode"
      type: "method"
      purpose: >
        Delete its 'self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)'
        line. The preceding comment ("Background and border share the
        DISCONNECTED screen's treatment (issue-ba2d5de2).") must be
        updated to drop the border reference, e.g. "Background matches
        the DISCONNECTED screen's treatment (issue-ba2d5de2)."
    - name: "DisplayManager._render_disconnected"
      type: "method"
      purpose: >
        Delete its 'self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)'
        line. The preceding comment "# Draw circular border/background"
        must be updated, e.g. "# Background fill" or removed if the
        surrounding clear_surface() call already makes it redundant.
    - name: "DisplayManager._draw_setup_mode_fallback"
      type: "method"
      purpose: >
        Delete its '# Draw border' comment and
        'self._draw_shift_border((200, 0, 0), 5)' line. No replacement
        drawing call is added.
    - name: "Palette"
      type: "dataclass"
      purpose: "Remove five fields no longer consumed by any caller."
      logic:
        - >
          In the frozen dataclass field list, remove these five lines:
          "band_centres_lit: Tuple[Tuple[int, int, int], ...]",
          "shift_border_caution: Tuple[int, int, int]",
          "shift_centre_dark: Tuple[int, int, int]",
          "shift_border_normal: Tuple[int, int, int]",
          "shift_border_down: Tuple[int, int, int]".
          Retain "band_centres: Tuple[Tuple[int, int, int], ...]"
          unchanged.
        - >
          In DAY_PALETTE, remove the band_centres_lit=(...) tuple, its
          preceding "# The lit phase of the upshift flash..." comment
          block, and the four trailing keyword lines
          shift_border_caution=(0, 180, 0), shift_centre_dark=(10, 10, 10),
          shift_border_normal=(200, 0, 0), shift_border_down=(0, 100, 255).
        - >
          In NIGHT_PALETTE, remove the band_centres_lit=(...) tuple, its
          preceding "# Equal to NIGHT_PALETTE.bands at present..." comment
          block, and the four trailing keyword lines
          shift_border_caution=(0, 110, 0), shift_centre_dark=(3, 3, 3),
          shift_border_normal=(120, 0, 0), shift_border_down=(0, 60, 150).
        - >
          The module-level comment above DAY_PALETTE beginning "Values
          copied verbatim from the constants in use before
          change-5012004e..." references band_centres_lit and the
          shift_border_* constants; update it to describe only the
          fields that remain (band_centres) or remove the sentence
          fragment naming the deleted fields.
  dependencies:
    internal:
      - "DisplayManager._draw_radial_mode reads Palette.band_centres directly after this change (previously indirect, via _get_shift_cue)."
    external: []

error_handling:
  strategy: >
    No new error handling. The deleted methods' try/except blocks are
    removed with them. No remaining code path can raise from the
    removed logic.

testing:
  unit_tests:
    - scenario: "tests/test_connect_error_classification.py"
      expected: "Remove the 'host._draw_shift_border = lambda colour: None' line; test still passes."
    - scenario: "tests/test_bluetooth_reset.py"
      expected: "Remove the 'host._draw_shift_border = lambda colour: None' line; test still passes."
    - scenario: "tests/test_disconnected_screen.py"
      expected: "Remove the 'host._draw_shift_border = lambda colour: None' line; test still passes."
  edge_cases:
    - "RPM at exactly bands.caution_start and bands.torque_start — centre disc must still resolve to a valid palette.band_centres index via the unchanged _get_band_colour() hysteresis; no new edge case is introduced by this change."
  validation:
    - "Full pytest suite run after the edits; no new failures."

deliverable:
  format_requirements:
    - "Edit files in place at their existing paths; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "Modified per design section above."
    - path: "src/gtach/display/models.py"
      content: "Modified per design section above."
    - path: "tests/test_connect_error_classification.py"
      content: "Stub line removed."
    - path: "tests/test_bluetooth_reset.py"
      content: "Stub line removed."
    - path: "tests/test_disconnected_screen.py"
      content: "Stub line removed."

success_criteria:
  - "grep -rn '_draw_shift_border\\|_get_shift_cue' src/gtach/ tests/ returns no match (executable code and comments alike — no reference should remain anywhere in either tree)."
  - "grep -rn 'band_centres_lit\\|shift_border_caution\\|shift_border_normal\\|shift_border_down\\|shift_centre_dark' src/gtach/ returns no match."
  - "grep -n 'band_centres:' src/gtach/display/models.py still matches — the field is retained, not removed."
  - "python -c 'from gtach.display.models import DAY_PALETTE, NIGHT_PALETTE' succeeds with no TypeError (confirms both Palette instances still construct with the reduced field set)."
  - "pytest tests/test_connect_error_classification.py tests/test_bluetooth_reset.py tests/test_disconnected_screen.py passes."
  - "Full pytest suite passes with no new failures relative to the pre-change baseline."

notes: >
  This prompt implements change-950128c0 / issue-950128c0. No
  tactical_brief is required — target_profile is claude_code, not ael.

version_history:
  - version: "1.0"
    date: "2026-08-13"
    author: "William Watson"
    changes:
      - "Initial prompt creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.10"
  schema_type: "t04_prompt"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-13 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
