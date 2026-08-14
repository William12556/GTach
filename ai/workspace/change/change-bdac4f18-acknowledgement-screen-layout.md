Created: 2026 August 14

# Change: Re-Lay Out Acknowledgement Screen With Measured Disclaimer Text

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
change_info:
  id: "change-bdac4f18"
  title: "Rewrite _draw_acknowledgement_mode() with a plain-font, verified-fit disclaimer"
  date: "2026-08-14"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-bdac4f18"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-bdac4f18"
  description: >
    Replace the acknowledgement screen's single-line, Michroma-rendered
    body and instruction text with pinned, on-device-measured lines in
    a plain (non-Michroma) font, and add a new DISCLAIMER.md at the
    repository root.

scope:
  summary: >
    Add DisplayManager._get_plain_font(), a small local cache returning
    pygame.font.Font(None, size) — bypassing FontManager's
    Michroma-first resolution — and rewrite
    _draw_acknowledgement_mode() to draw the title (unchanged: Michroma
    72px "GTach") plus three fixed disclaimer lines and one instruction
    line, all at coordinates measured against the real font metrics on
    gtach.local.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  out_of_scope:
    - "A general-purpose word-wrap helper. The exact line breaks were measured against the chosen text, font, and size on-device (see technical_details below) and are pinned as literals — declined in favour of a runtime wrapper, see rational.alternatives_considered."
    - "Changing Michroma usage anywhere else in the application (RADIAL, OPTIONS, DISCONNECTED, buttons, etc.) — this change touches only the acknowledgement screen's body/instruction text."
    - "FontManager / typography.py — not modified. The plain font is obtained locally in DisplayManager, alongside the existing Michroma-via-FontManager path, not by changing the shared font resolution every other screen depends on."
    - "DISCLAIMER.md is out of scope for this src/ change — it is a repository-root document, already created directly per governance (ai/task.md primer §7.0: full T-Doc workflow applies to src/ changes only)."

rational:
  problem_statement: >
    The acknowledgement screen's body and instruction text clip the
    circular viewport, per issue-bdac4f18.
  proposed_solution: >
    Pin the exact wording, font, size, and line breaks to values
    measured against the real deployment environment
    (/opt/gtach/venv/bin/python3 on gtach.local), rather than computing
    wrap at runtime from an estimate.
  alternatives_considered:
    - option: "Add a runtime word-wrap helper (measure each candidate line via font.size(), break greedily to a max width)."
      reason_rejected: >
        More general and would survive a future text change without a
        new measurement pass, but the text, font, and size were already
        measured and confirmed to fit with 52-69px margin on the actual
        target hardware; a runtime wrapper reintroduces exactly the
        estimate-vs-reality gap this change exists to close, for a
        screen whose content changes rarely. Revisit if the
        acknowledgement screen gains more variable content.
    - option: "Keep Michroma for the disclaimer body, reduce its size until it fits."
      reason_rejected: >
        Michroma at a size small enough to fit three lines of legal
        text within a 480px circle was judged illegible; the reporter
        chose to switch the body/instruction text to a plainer font
        rather than shrink Michroma further.
  benefits:
    - "Closes the clipping defect with numbers verified against production hardware, not estimated."
    - "Title styling (Michroma, brand-consistent) is unchanged."
    - "No change to FontManager/typography.py, so no risk to any other screen's rendering."
  risks:
    - risk: "The pinned line breaks are specific to this exact wording; editing the disclaimer text later requires re-measuring rather than automatically re-wrapping."
      mitigation: "Accepted per rational.alternatives_considered — this screen's text changes rarely, and the measurement process (ai/workspace/report or a comment in the change history) is now documented and repeatable via the on-device script used to produce these figures."

technical_details:
  current_behavior: >
    _draw_acknowledgement_mode() calls self._get_cached_font(24) and
    self._get_cached_font(20) for the body and instruction lines. Both
    resolve through FontManager.get_font() to Michroma-Regular.ttf.
    Each string is drawn with one render_text() call — no wrapping.
  proposed_behavior: >
    Body: three fixed lines drawn with a new self._get_plain_font(18),
    centred at x=240, y=266/290/314. Instruction: one line drawn with
    self._get_plain_font(20), centred at (240, 400). Title: unchanged.
    Exact text and coordinates below, measured on gtach.local
    (/opt/gtach/venv/bin/python3, pygame 2.6.1, SDL 2.28.4,
    Python 3.9.2):

    | y | text | measured width | chord margin (per side) |
    |---|---|---|---|
    | 266 | THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY | 369px | 52.1px |
    | 290 | OF ANY KIND. THE AUTHOR IS NOT LIABLE FOR ANY CLAIM, | 359px | 53.2px |
    | 314 | DAMAGES, OR OTHER LIABILITY ARISING FROM ITS USE. | 341px | 55.7px |
    | 400 | Tap to acknowledge and continue | 215px | 68.7px |

    Margin computed against the r=238 viewport at each line's vertical
    offset from the display centre (240,240): chord width
    2*sqrt(238^2 - offset^2), margin = (chord width - text width) / 2.
    All four lines clear with positive margin; smallest is 52.1px.
  implementation_approach: >
    Single-file change confined to src/gtach/display/manager.py: one
    new small method (_get_plain_font) and one rewritten method
    (_draw_acknowledgement_mode).
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Add _get_plain_font(size) returning a cached
        pygame.font.Font(None, size) — the SDL default font, not
        Michroma. Rewrite _draw_acknowledgement_mode() to draw the
        unchanged Michroma title, then three fixed disclaimer lines and
        one instruction line via _get_plain_font(), at the measured
        coordinates in technical_details above.
      functions_affected:
        - "_get_plain_font"
        - "_draw_acknowledgement_mode"
      classes_affected:
        - "DisplayManager"
  interface_changes:
    - interface: "DisplayManager._get_plain_font"
      change_type: "signature"
      details: "New private method; no existing interface altered."
      backward_compatible: "yes"

dependencies:
  internal: []
  required_changes:
    - change_ref: "change-e22142da"
      relationship: "blocked_by"

testing_requirements:
  test_approach: >
    Manual verification on device — visual inspection that no text
    clips the bezel, plus a re-run of the measurement script against
    the deployed build to confirm the pinned coordinates still match
    the pinned text.
  test_cases:
    - scenario: "ACKNOWLEDGEMENT screen shown (unacknowledged state)"
      expected_result: "Title, three disclaimer lines, and instruction line all fully visible within the circular bezel, matching the coordinates in technical_details."
    - scenario: "Tap to dismiss"
      expected_result: "Unchanged — _on_acknowledgement_dismissed() is not touched by this change."
  regression_scope:
    - "src/gtach/display/manager.py — _draw_acknowledgement_mode() only; no other screen calls _get_plain_font()."
  validation_criteria:
    - "grep -n '_get_plain_font' src/gtach/display/manager.py shows one definition and four call sites (three body lines + one instruction) inside _draw_acknowledgement_mode()."
    - "grep -n 'OBD tachometer' src/gtach/display/manager.py returns no match — the old single-line body text is fully replaced."

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
    - issue_ref: "issue-bdac4f18"
      relationship: "source"
    - issue_ref: "issue-e22142da"
      relationship: "related"

notes: >
  The exact text, font, size, and coordinates in this document were
  measured against /opt/gtach/venv/bin/python3 on gtach.local before
  authoring, not estimated. See conversation record for the two
  on-device measurement scripts used (word-wrap width probe, then
  circular-margin verification against all four lines).

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial change creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.4"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
