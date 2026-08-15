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
  iteration: 4
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
    72px "GTach") plus four fixed disclaimer lines at 24px and one
    instruction line, all at coordinates measured against the real
    font metrics on gtach.local.
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
    Iteration 3 (already implemented and deployed, closed prompt
    prompt-bdac4f18-3): _draw_acknowledgement_mode() calls
    self._get_plain_font(24) for four fixed body lines at
    y=208/240/272/304, and self._get_plain_font(24) for one
    mixed-case instruction line ("Tap to acknowledge and continue")
    at y=400. This is the baseline iteration 4 modifies.
  proposed_behavior: >
    Body: unchanged from iteration 2 — four fixed lines at
    self._get_plain_font(24), y=208/240/272/304. Instruction: text
    changed to ALL CAPS ("TAP TO ACKNOWLEDGE AND CONTINUE"), font size
    unchanged at 24px, position moved from (240, 400) to (240, 350).
    Title: unchanged.

    Root cause of the reported size mismatch (not a code defect —
    iteration 3 already set both blocks to size 24 identically):
    per-glyph ink metrics measured on gtach.local at size 24 show
    capital letters ('T', 'W') reaching 12px above baseline, while
    lowercase x-height letters ('a', 'o') reach only 9-10px. The body
    text is entirely capitals, so every character sits at the full
    12px; the iteration-3 instruction text was mostly lowercase, so
    most of its visual mass sat at 9-10px despite an identical point
    size and an identical _get_plain_font(24) call. Setting the
    instruction text to match the body's ALL CAPS treatment resolves
    the perceived mismatch without changing font size.

    ALL CAPS is wider than the original mixed-case string at the same
    size (328px vs 264px), which reduced the margin at the original
    y=400 to 12.2px — thinner than anywhere else in this design, and
    thinner than the 15.7px this change already rejected once in
    iteration 3's own sweep. Rather than shrink the text back down,
    the line was moved from y=400 to y=350: closer to the display's
    vertical centre, which widens the available chord.

    | y | text | measured width | chord margin (per side) |
    |---|---|---|---|
    | 208 | THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT | 396px | 37.8px |
    | 240 | WARRANTY OF ANY KIND. THE AUTHOR IS NOT | 388px | 44.0px |
    | 272 | LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER | 381px | 45.3px |
    | 304 | LIABILITY ARISING FROM ITS USE. | 277px | 90.7px |
    | 350 | TAP TO ACKNOWLEDGE AND CONTINUE | 328px | 47.1px |

    Margin computed against the r=238 viewport at each line's vertical
    offset from the display centre (240,240): chord width
    2*sqrt(238^2 - offset^2), margin = (chord width - text width) / 2.
    All five lines clear with positive margin; smallest is 37.8px, on
    a body line — the instruction line's margin (47.1px) is now
    squarely within the range the rest of the design already uses,
    not the outlier it was at y=400.

    y=350 leaves a 46px gap above the body block's last line (y=304),
    chosen from a sweep of y=320 through y=400 in 10px steps: y=340
    gave 52.0px margin / 36px gap, y=350 gave 47.1px margin / 46px
    gap, y=360 gave 41.5px margin / 56px gap. y=350 was picked as the
    point where the gap reads as a clear but not oversized separation
    between the two text blocks.
  implementation_approach: >
    Single-file change confined to src/gtach/display/manager.py: one
    new small method (_get_plain_font) and one rewritten method
    (_draw_acknowledgement_mode).
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Change the instruction line's text to ALL CAPS ("TAP TO
        ACKNOWLEDGE AND CONTINUE") and move its position from (240, 400)
        to (240, 350), inside _draw_acknowledgement_mode(). Font size
        (_get_plain_font(24)) is unchanged from iteration 3. Body block
        and title block unchanged.
      functions_affected:
        - "_draw_acknowledgement_mode"
      classes_affected:
        - "DisplayManager"
  interface_changes: []

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
      expected_result: "Title, four disclaimer lines, and instruction line all fully visible within the circular bezel; instruction line reads \"TAP TO ACKNOWLEDGE AND CONTINUE\" in ALL CAPS at y=350, visually matching the body text's apparent size."
    - scenario: "Tap to dismiss"
      expected_result: "Unchanged — _on_acknowledgement_dismissed() is not touched by this change. The full-screen dismiss region registered by _register_acknowledgement_regions() is independent of where the instruction text is drawn."
  regression_scope:
    - "src/gtach/display/manager.py — _draw_acknowledgement_mode() only; no other screen calls _get_plain_font()."
  validation_criteria:
    - "grep -n '_get_plain_font' src/gtach/display/manager.py shows one definition and five call sites, all at size 24, all inside _draw_acknowledgement_mode()."
    - "grep -n 'Tap to acknowledge and continue' src/gtach/display/manager.py returns no match — the mixed-case iteration-1/2/3 wording is fully replaced."
    - "grep -n 'TAP TO ACKNOWLEDGE AND CONTINUE' src/gtach/display/manager.py matches exactly once, on a line whose render_text() call centres it at (240, 350)."

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
  authoring, not estimated.

  ITERATION 4. Iterations 1 through 3 have all already been executed
  by Claude Code and moved to ai/workspace/prompt/closed/ — confirmed
  present in src/gtach/display/manager.py before this revision was
  authored. Iteration 3 (instruction enlarged to 24px, mixed case,
  y=400) resolved a reported font-size question that turned out on
  investigation not to be a code defect: both blocks already called
  _get_plain_font(24) identically. The actual cause was the optical
  effect of cap-height vs x-height at equal point size, confirmed via
  font.metrics() on gtach.local. This iteration addresses that
  directly (ALL CAPS instruction text) and its consequence (reduced
  margin from the wider ALL CAPS string, addressed by moving the line
  to y=350). A new prompt-bdac4f18 at iteration 4, coupled to this
  change's iteration 4, delivers this against the already-implemented
  iteration-3 baseline. The closed iteration-1, -2, and -3 prompts are
  not edited.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial change creation."
  - version: "1.1"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Revised layout after a size sweep (18-28px) measured on gtach.local: body text enlarged from 18px/3 lines to 24px/4 lines and moved up to start immediately below the title's measured (not estimated) bounding box. Coordinates updated throughout technical_details; call-site count in validation_criteria updated from four to five."
  - version: "1.2"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Iteration 3: instruction line enlarged from 20px to 24px (matching body text size) at its existing y=400 position, per a size sweep measured on gtach.local (20-40px; 24px chosen, 44.2px margin; 28px available at 15.7px margin but judged too thin). _get_plain_font() itself no longer a net-new interface as of this iteration — interface_changes cleared."
  - version: "1.3"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Iteration 4: diagnosed the reported iteration-3 size mismatch as a cap-height/x-height optical effect, not a code defect, via font.metrics() measured on gtach.local. Fix: instruction text changed to ALL CAPS at the unchanged 24px size, position moved from y=400 to y=350 (chosen from a y=320-400 sweep) to keep margin in line with the rest of the design after the wider ALL CAPS string reduced it to 12.2px at the original position. technical_details.proposed_behavior and validation_criteria rewritten accordingly."

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
