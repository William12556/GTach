Created: 2026 August 13

# Change: Remove Shift Rim Borders

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
change_info:
  id: "change-950128c0"
  title: "Remove rim border and shift-state cue from all screens"
  date: "2026-08-13"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-950128c0"
    issue_iteration: 1

source:
  type: "human_request"
  reference: "issue-950128c0"
  description: >
    Remove the coloured rim border from every screen and remove the
    shift-state cue (upshift flash, downshift/normal border colour)
    entirely rather than relocate it to another visual channel.

scope:
  summary: >
    Delete DisplayManager._draw_shift_border() and
    DisplayManager._get_shift_cue(); remove their seven call sites;
    replace RADIAL's centre-disc fill with the active band's
    unconditional colour; remove the now-unused Palette fields from
    models.py; update the three tests that stub _draw_shift_border.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "Palette"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "test_connect_error_classification"
      file_path: "tests/test_connect_error_classification.py"
      change_type: "modify"
    - name: "test_bluetooth_reset"
      file_path: "tests/test_bluetooth_reset.py"
      change_type: "modify"
    - name: "test_disconnected_screen"
      file_path: "tests/test_disconnected_screen.py"
      change_type: "modify"
  out_of_scope:
    - "Any replacement shift-state indicator on another visual channel — explicitly declined by reporter."
    - "RPM band colours, band boundary marks, or the arc sweep — unaffected."
    - "The retry/reconnect spinner on DISCONNECTED — unaffected, unrelated to the rim border."

rational:
  problem_statement: >
    The rim border is the only visible shift-state indicator (RADIAL) or
    an inert draw call (every other screen, drawn in the screen's own
    background colour). The reporter finds it distracting and not useful
    as a shift indicator, and wants it removed with no replacement cue.
  proposed_solution: >
    Delete the border-drawing method and the shift-cue method that feeds
    it; remove all seven call sites; the RADIAL centre disc keeps showing
    the active band's colour (as it already did for two of the three
    former shift states) but never flashes and never varies with RPM
    trend, only with band.
  benefits:
    - "Removes the reported distraction on RADIAL."
    - "Removes six inert draw calls (options menu, confirm view, update view, acknowledgement, disconnected, setup fallback)."
    - "Simplifies _draw_radial_mode(): one palette lookup replaces a discarded 2-of-4 tuple destructure."
    - "Removes five Palette fields (per palette instance) that exist for no remaining consumer."
  risks:
    - risk: "The three tests that stub _draw_shift_border no longer have a method to stub."
      mitigation: "Prompt instructs removal of the stub line in each of the three test files; the tests do not assert on border behaviour, only on unrelated screen state, so no test logic changes."
    - risk: "Removing band_centres_lit and shift_centre_dark from Palette could break a caller outside manager.py that this issue's search did not find."
      mitigation: "ripgrep search of the full repository for band_centres_lit and shift_centre_dark confirmed manager.py and models.py as the only occurrences before this change was authored."

technical_details:
  current_behavior: >
    _draw_radial_mode() calls _get_band_colour() then _get_shift_cue(),
    discards _get_shift_cue()'s border_colour and flash_centre, and uses
    centre_colour for the centre disc. It also calls
    _draw_shift_border(border_colour) to paint a 12 px ring at r=244
    before overpainting the interior to r=232 with palette.ground. Six
    other draw methods call _draw_shift_border() with a colour equal to
    their own background, producing no visible ring.
  proposed_behavior: >
    _draw_radial_mode() calls only _get_band_colour(), reads
    palette.band_centres[active_band] directly for the centre disc, and
    fills the full circular face (to r=244, the former outer edge of the
    border ring) with palette.ground in place of the border-then-ground
    sequence — so the usable circular face is the same size it was before
    the border occupied its outer 12 px, rather than leaving a
    258px-diameter face inside a now-unpainted ring. The six other draw
    methods drop their _draw_shift_border() call outright; their
    clear_surface() calls already paint the full 480x480 surface in the
    same colour the border used to repeat.
  implementation_approach: >
    Direct deletion and replacement in manager.py and models.py, plus
    the matching stub removal in three test files. No new abstractions
    introduced; two methods and five dataclass fields removed.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Delete _draw_shift_border() and _get_shift_cue() in full. In
        _draw_radial_mode(): remove the
        "border_colour, _, _, centre_colour = self._get_shift_cue(...)"
        call, set centre_colour from
        palette.band_centres[active_band] instead, remove the
        "self._draw_shift_border(border_colour)" call, and change the
        background fill from r=232 to r=244 so the face fills the space
        the border used to occupy. Remove the single
        "self._draw_shift_border(...)" line from each of
        _draw_options_menu(), _draw_confirm_view(), _draw_update_view(),
        _draw_acknowledgement_mode(), _render_disconnected(), and
        _draw_setup_mode_fallback(), with no other change to those
        methods.
      functions_affected:
        - "_draw_shift_border"
        - "_get_shift_cue"
        - "_draw_radial_mode"
        - "_draw_options_menu"
        - "_draw_confirm_view"
        - "_draw_update_view"
        - "_draw_acknowledgement_mode"
        - "_render_disconnected"
        - "_draw_setup_mode_fallback"
      classes_affected:
        - "DisplayManager"
    - component: "Palette"
      file: "src/gtach/display/models.py"
      change_summary: >
        Remove the band_centres_lit, shift_border_caution,
        shift_centre_dark, shift_border_normal and shift_border_down
        fields from the Palette dataclass, and the matching keyword
        arguments and comment blocks from both the DAY_PALETTE and
        NIGHT_PALETTE instances. band_centres is unchanged and remains
        required.
      functions_affected: []
      classes_affected:
        - "Palette"
    - component: "test_connect_error_classification"
      file: "tests/test_connect_error_classification.py"
      change_summary: "Remove the 'host._draw_shift_border = lambda colour: None' stub line."
      functions_affected: []
      classes_affected: []
    - component: "test_bluetooth_reset"
      file: "tests/test_bluetooth_reset.py"
      change_summary: "Remove the 'host._draw_shift_border = lambda colour: None' stub line."
      functions_affected: []
      classes_affected: []
    - component: "test_disconnected_screen"
      file: "tests/test_disconnected_screen.py"
      change_summary: "Remove the 'host._draw_shift_border = lambda colour: None' stub line."
      functions_affected: []
      classes_affected: []
  interface_changes:
    - interface: "DisplayManager._draw_shift_border"
      change_type: "signature"
      details: "Method removed entirely."
      backward_compatible: "no"
    - interface: "DisplayManager._get_shift_cue"
      change_type: "signature"
      details: "Method removed entirely."
      backward_compatible: "no"
    - interface: "Palette"
      change_type: "signature"
      details: "Five fields removed from the frozen dataclass; both module-level instances updated to match."
      backward_compatible: "no"

dependencies:
  internal:
    - component: "DAY_PALETTE / NIGHT_PALETTE"
      impact: "Both instances lose five keyword arguments each; band_centres retained on both."
  required_changes: []

testing_requirements:
  test_approach: >
    Manual verification on device (no automated visual regression exists
    for RADIAL rendering). Existing pytest suite must continue to pass
    after the three stub-line removals.
  test_cases:
    - scenario: "RADIAL mode at RPM in the caution/danger band"
      expected_result: "No rim border visible; centre disc shows the active band colour without flashing."
    - scenario: "RADIAL mode at RPM in the idle/torque band"
      expected_result: "No rim border visible; centre disc shows the active band colour, matching current non-flashing appearance."
    - scenario: "OPTIONS menu, confirm-clear view, update view, ACKNOWLEDGEMENT, DISCONNECTED, setup fallback"
      expected_result: "No visible change from current rendering — the border there was already invisible."
    - scenario: "pytest full suite"
      expected_result: "All tests pass, including the three edited files, with no reference to _draw_shift_border remaining."
  regression_scope:
    - "src/gtach/display/manager.py — RADIAL and every screen listed in affected_scope"
    - "src/gtach/display/models.py — DAY_PALETTE and NIGHT_PALETTE construction"
  validation_criteria:
    - "grep -rn '_draw_shift_border\\|_get_shift_cue' src/ tests/ returns no match."
    - "grep -rn 'band_centres_lit\\|shift_border_caution\\|shift_border_normal\\|shift_border_down\\|shift_centre_dark' src/ returns no match."
    - "python -c 'from gtach.display.models import DAY_PALETTE, NIGHT_PALETTE' succeeds without error on the device venv."

implementation:
  rollback_procedure: "git revert the commit; no data migration involved."
  deployment_notes: "Deploy via existing bin/deploy.sh; no config.yaml schema change."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""

traceability:
  related_issues:
    - issue_ref: "issue-950128c0"
      relationship: "source"
    - issue_ref: "issue-e4b7c3a1"
      relationship: "related"
    - issue_ref: "issue-64d8d8fc"
      relationship: "related"

notes: >
  issue-e4b7c3a1 introduced the border/flash pair this change removes;
  issue-64d8d8fc later moved the flash to the centre disc and reduced
  the border to a static state colour. This change completes that
  reduction to zero rather than continuing it.

version_history:
  - version: "1.0"
    date: "2026-08-13"
    author: "William Watson"
    changes:
      - "Initial change creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-13 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
