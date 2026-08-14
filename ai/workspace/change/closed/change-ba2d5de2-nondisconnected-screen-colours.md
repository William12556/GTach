Created: 2026 August 13

# Change: Extend the DISCONNECTED Colour Scheme to OPTIONS, ACKNOWLEDGEMENT and SETUP

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-ba2d5de2"
  title: "Apply the DISCONNECTED screen's pale dusty-yellow background (216, 200, 146) and black text (0, 0, 0) to OPTIONS, ACKNOWLEDGEMENT and SETUP, matching its background-coloured border and unchanged button/semantic colours; RADIAL, DISCONNECTED itself and SPLASH are unaffected"
  date: "2026-08-13"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 2
  coupled_docs:
    issue_ref: "issue-ba2d5de2"
    issue_iteration: 2

source:
  type: "issue"
  reference: "issue-ba2d5de2"
  description: >
    Resolves issue-ba2d5de2. DISCONNECTED alone carries the pale
    yellow/black readability scheme; OPTIONS, ACKNOWLEDGEMENT and
    SETUP still use the earlier dark-background/light-text treatment.
    SPLASH was originally included and was withdrawn 2026-08-13,
    same day, post-deployment — see scope.summary and EDIT C below.

scope:
  summary: >
    Background/text colour swaps in manager.py and setup.py, following
    the exact pattern DISCONNECTED's own _render_disconnected already
    establishes: background and border both become (216, 200, 146);
    every text colour drawn on that background becomes (0, 0, 0),
    with any existing dimmed/secondary tone collapsed to the same
    value; button fills, their white labels, and every semantic or
    status colour (success/warning/danger/primary accents, the
    ConnectionStatus dot) are left exactly as they are. SPLASH was
    originally included as a fourth file (splash.py) and was removed
    from scope 2026-08-13, same day, after this change had already
    been implemented and deployed: William specified the splash
    screen must remain black background with white text. The SPLASH
    edit was reverted directly in splash.py under the P03 §1.4.12
    trivial exemption, and this document is amended to withdraw EDIT
    C rather than leave it describing a state no longer on target.
  affected_components:
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_confirm_view"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_acknowledgement_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "SetupDisplayManager.colors, SetupDisplayManager._draw_circular_border"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "RADIAL and everything _draw_radial_mode touches: the shift-cue border/centre colours (change-64d8d8fc) and DAY_PALETTE / NIGHT_PALETTE (models.py). Excluded by explicit instruction."
    - "DISCONNECTED / _render_disconnected. It is the reference this change brings the others into line with, not a target of it."
    - "SPLASH / SplashScreen (src/gtach/display/splash.py) in full, including ._colors and ._draw_border. Originally EDIT C of this change; removed from scope 2026-08-13 (correction, same day, post-deployment) — William specified the splash screen must remain black background with white text, and it was reverted to that state directly under the P03 §1.4.12 trivial exemption."
    - "Button fill colours everywhere (OPTIONS's (80, 80, 100), the confirm view's (140, 40, 40) / (80, 80, 100), the update view's (0, 120, 0) / (80, 80, 100)) and their white labels. DISCONNECTED's own buttons keep a dark neutral fill unrelated to its background swap; these already follow the same convention and are not part of the inconsistency the issue names."
    - "SETUP's semantic accent colours: 'primary', 'success', 'warning', 'danger', 'border' entries in SetupDisplayManager.colors. Functional colour-coding, not the background/text pair in question."
    - "graphics/splash_graphics.py SPLASH_COLORS and the automotive-gauge progress indicator it feeds. Self-contained decorative sub-component with its own palette."
    - "models.py ConnectionStatus colours (the small status dot drawn on RADIAL, DISCONNECTED, OPTIONS and ACKNOWLEDGEMENT). Unchanged on DISCONNECTED today; unchanged here."
    - "Any RPM band, tick, or gauge colour. Palette-only, RADIAL-only."
    - "Layout, geometry, button positions, touch regions, timing and all non-colour behaviour in every affected file."

rational:
  problem_statement: >
    DISCONNECTED's background/text colours were changed for
    readability; no other non-gauge screen followed, leaving two
    unrelated visual languages depending on which screen is showing.
  proposed_solution: >
    Four small, mechanical edits, one per rendering method group,
    each swapping a small number of RGB literals or dict values. No
    new colour is invented: (216, 200, 146) and (0, 0, 0) are
    DISCONNECTED's own _DISCONNECTED_BG_COLOUR and
    _DISCONNECTED_TEXT_COLOUR, already defined as class constants on
    DisplayManager and importable by name from manager.py.

    EDIT A — manager.py, OPTIONS (three sub-views). In
    _draw_options_menu, _draw_confirm_view and _draw_update_view:
    the clear_surface fill (40, 40, 50) becomes
    DisplayManager._DISCONNECTED_BG_COLOUR; the border call
    self._draw_shift_border((200, 0, 0)) becomes
    self._draw_shift_border(self._DISCONNECTED_BG_COLOUR); every text
    colour currently (255, 255, 255), (200, 200, 200) or (150, 150, 150)
    becomes DisplayManager._DISCONNECTED_TEXT_COLOUR. Button fills,
    the page-indicator dots (which read the active palette, unrelated
    to this change) and the spinner are untouched.

    EDIT B — manager.py, ACKNOWLEDGEMENT. In
    _draw_acknowledgement_mode: the clear_surface fill (0, 0, 0)
    becomes _DISCONNECTED_BG_COLOUR; the border call
    self._draw_shift_border((200, 0, 0)) becomes
    self._draw_shift_border(self._DISCONNECTED_BG_COLOUR); the title
    colour (255, 255, 255) and the two body/instruction colours,
    (200, 200, 200) and (150, 150, 150), all become
    _DISCONNECTED_TEXT_COLOUR.

    EDIT C — WITHDRAWN 2026-08-13, same day, post-deployment. Originally
    specified splash.py's SplashScreen._colors and _draw_border to
    match DISCONNECTED, as EDIT A/B/D do for their files. William
    specified the splash screen must remain black background with
    white text — distinct from every other screen this change touches
    — so splash.py is excluded from this change in full. It had
    already been implemented and deployed per the original EDIT C
    text; that deployment was reverted directly in splash.py under the
    P03 §1.4.12 trivial exemption (single class, small delta, no
    interface change, human-approved) rather than through a further
    T-Doc cycle, per governance §7.0's direct-edit allowance. splash.py
    is now byte-identical to its state before this change was ever
    implemented.

    EDIT D — setup.py, SetupDisplayManager. In self.colors:
    'background' (20, 20, 30) becomes (216, 200, 146); 'surface'
    (40, 40, 50), which nothing in the file currently reads, is left
    as dead configuration; 'text' (255, 255, 255) and 'text_dim'
    (180, 180, 180) both become (0, 0, 0). 'primary', 'success',
    'warning', 'danger' and 'border' are unchanged — see
    out_of_scope. In _draw_circular_border: the hard-coded (200, 0, 0)
    circle becomes self.colors['background'], i.e. (216, 200, 146).

    Each edit is a literal substitution against colour values already
    present in the file; no rendering logic, layout or control flow
    changes.
  alternatives_considered:
    - option: "Give each screen its own distinct light colour scheme."
      reason_rejected: >
        The issue asks for consistency with DISCONNECTED specifically,
        not a general light-mode redesign. Reusing its exact values is
        the smallest change that satisfies the request and keeps every
        non-gauge screen visually identical in treatment.
    - option: "Keep the red border and change only the fill and text."
      reason_rejected: >
        DISCONNECTED's own border is background-coloured, not red — a
        soft edge, not a ring. Keeping red on the other four screens
        while DISCONNECTED has none would itself be a new
        inconsistency, the opposite of this change's purpose.
    - option: "Also collapse SETUP's semantic accents (success/warning/danger/primary) into the two-colour scheme."
      reason_rejected: >
        These colours carry meaning DISCONNECTED has no equivalent
        of — pairing confirmation, discovery progress, error state.
        DISCONNECTED itself does not attempt to express this kind of
        state in its two-colour scheme; SETUP should not either.
    - option: "Also apply the scheme to SPLASH."
      reason_rejected: >
        Originally attempted as EDIT C and deployed, then withdrawn
        2026-08-13 (correction, same day): William specified the
        splash screen must remain black background with white text.
        The startup screen is treated as a distinct visual moment from
        the operational screens this change otherwise unifies.
  benefits:
    - "One consistent colour language across OPTIONS, ACKNOWLEDGEMENT, SETUP and DISCONNECTED, the operational non-gauge screens."
    - "Zero new colours introduced for the primary background/text pair; both are DISCONNECTED's own existing constants."
    - "Each edit is a small, reviewable literal substitution with no logic change, keeping regression risk low."
  risks:
    - risk: >
        Collapsing text_dim / secondary_text into the same colour as
        primary text removes the visual hierarchy those screens
        currently use to de-emphasise secondary lines.
      mitigation: >
        This is deliberate fidelity to DISCONNECTED's own pattern,
        which uses one text colour throughout rather than two. Recorded
        here so it is a stated decision, not an oversight, and is
        reversible in a follow-up if the collapsed hierarchy reads
        poorly on target.
    - risk: "Missing a literal colour occurrence in one of the four files leaves a stray dark-on-light or light-on-dark element."
      mitigation: >
        The coupled prompt enumerates every colour literal touched, by
        line content, and testing_requirements below lists an on-target
        visual pass over every screen and sub-view.

technical_details:
  current_behavior: >
    OPTIONS (three sub-views), ACKNOWLEDGEMENT and SETUP each render a
    dark background with light text and a static red circular border.
    DISCONNECTED renders a pale dusty-yellow background with black
    text and a background-coloured border. SPLASH also rendered a
    dark background with light text and a red border, and continues
    to do so — explicitly excluded, see scope.summary.
  proposed_behavior: >
    All four screens (OPTIONS's three sub-views counted individually,
    plus ACKNOWLEDGEMENT and SETUP) render the same pale dusty-yellow
    background, black text, and background-coloured border as
    DISCONNECTED. Button fills, labels, and every semantic or status
    colour are unchanged. SPLASH is unchanged from its original dark
    background/light text/red border.
  implementation_approach: >
    Literal RGB substitution at each existing draw call and colour
    dictionary entry. No new methods, no new state, no change to
    which colour a given draw call reads from — only the values
    already read.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        EDIT A/B: background fill, border colour and text colour
        literals updated in _draw_options_menu, _draw_confirm_view,
        _draw_update_view and _draw_acknowledgement_mode to
        DisplayManager._DISCONNECTED_BG_COLOUR /
        _DISCONNECTED_TEXT_COLOUR.
      functions_affected:
        - "_draw_options_menu"
        - "_draw_confirm_view"
        - "_draw_update_view"
        - "_draw_acknowledgement_mode"
      classes_affected:
        - "DisplayManager"
    - component: "SetupDisplayManager"
      file: "src/gtach/display/setup.py"
      change_summary: >
        EDIT D: self.colors['background'], ['text'] and ['text_dim']
        updated; _draw_circular_border's hard-coded circle colour
        updated to read self.colors['background'].
      functions_affected:
        - "__init__"
        - "_draw_circular_border"
      classes_affected:
        - "SetupDisplayManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "DisplayManager._DISCONNECTED_BG_COLOUR / _DISCONNECTED_TEXT_COLOUR"
      impact: "Read from three additional methods on the same class (OPTIONS's three sub-views already share _draw_options_menu/_draw_confirm_view/_draw_update_view) and one more (_draw_acknowledgement_mode); no change to the constants themselves."
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    No unit tests are added: every edit is a colour-literal
    substitution with no branching, and Python has no framework-level
    way to assert a screen's rendered appearance short of a full
    surface-diff harness this project does not have. Verification is
    an on-target visual pass, listed below and in the issue's
    verification_enhanced.verification_steps.
  test_cases: []
  regression_scope:
    - "pytest tests/ passes (no functional code touched, but run in full per project convention)."
    - "Touch regions and button behaviour on OPTIONS, ACKNOWLEDGEMENT and SETUP — none of this change's edits touch _register_* methods or touch_coordinator calls, but a visual pass should confirm nothing shifted."
    - "SPLASH renders unchanged (black background, white/light-grey text, red border) — confirms the revert left no residue."
  validation_criteria:
    - "grep -n '(40, 40, 50)' src/gtach/display/manager.py returns no match inside _draw_options_menu, _draw_confirm_view or _draw_update_view."
    - "grep -n '(200, 0, 0)' src/gtach/display/manager.py and setup.py returns no match at the border-drawing call sites this change touches."
    - "grep -n '(216, 200, 146)' src/gtach/display/splash.py returns no match — SPLASH carries none of DISCONNECTED's colour values."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDIT A — OPTIONS's three sub-views in manager.py."
      owner: "tactical"
    - step: "EDIT B — ACKNOWLEDGEMENT in manager.py."
      owner: "tactical"
    - step: "EDIT C — WITHDRAWN. SplashScreen in splash.py was reverted to its pre-change state directly, under the P03 §1.4.12 trivial exemption, after having been implemented."
      owner: "human"
    - step: "EDIT D — SetupDisplayManager in setup.py."
      owner: "tactical"
    - step: "Deploy to gtach.local; visual pass over every affected screen and sub-view per testing_requirements."
      owner: "human"
  rollback_procedure: >
    Revert the commit for EDIT A, B and D. Each is a literal colour
    substitution in its file with no structural change, so the revert
    is exact and carries no residual state. EDIT C's revert is
    already captured directly in splash.py, outside this commit, per
    the trivial exemption.
  deployment_notes: "No unit change; no new dependency."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-ba2d5de2"
      relationship: "resolves"

notes: >
  DISCONNECTED's own colour constants are reused by direct reference
  (DisplayManager._DISCONNECTED_BG_COLOUR / _DISCONNECTED_TEXT_COLOUR)
  in manager.py rather than restated as new literals, so a future
  change to DISCONNECTED's scheme would need a deliberate follow-up
  decision about whether to propagate it here again — it will not
  happen silently, since setup.py holds its own literal copy of the
  same RGB values, not a shared reference.

  CORRECTION, 2026-08-13, same day, post-deployment. EDIT A, B and D
  were implemented and deployed as specified. EDIT C (SplashScreen)
  was also implemented and deployed, then withdrawn the same day:
  William specified the splash screen must remain black background
  with white text. splash.py was reverted directly to its pre-change
  state under the P03 §1.4.12 trivial exemption — single class, small
  delta (the _colors dict and one draw-call argument), no interface
  change, human-approved — rather than through a further T-Doc cycle.
  This document, and its coupled issue-ba2d5de2, are amended in place
  to withdraw EDIT C and remove SPLASH from every scope, rationale and
  validation section, per governance §7.0's allowance for direct
  editing of ai/workspace/ documents.

version_history:
  - version: "1.0"
    date: "2026-08-13"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-ba2d5de2 iteration 1."
      - "Four edits: OPTIONS's three sub-views and ACKNOWLEDGEMENT in manager.py (by direct reference to DISCONNECTED's own colour constants), SplashScreen in splash.py, SetupDisplayManager in setup.py (both by literal RGB match)."
      - "Records that button fills and every semantic/status colour (SETUP's primary/success/warning/danger, SPLASH's automotive-gauge palette, the ConnectionStatus dot) are explicitly out of scope."
      - "Records progress_bg in splash.py as the one value with no DISCONNECTED-derived literal to copy, constrained instead by a stated legibility requirement."
  - version: "2.0"
    date: "2026-08-13"
    author: "William Watson"
    changes:
      - "CORRECTION, same day, post-deployment: EDIT C withdrawn. SplashScreen must remain black background with white text; reverted directly in splash.py under the P03 §1.4.12 trivial exemption."
      - "status changed proposed -> implemented, reflecting that EDIT A, B and D were carried out on target as specified."
      - "Every scope, out_of_scope, rational, technical_details, dependencies, testing_requirements and implementation section naming SPLASH or EDIT C is amended to reflect the withdrawal."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-13 | Initial change document. Extends DISCONNECTED's background/text colours to OPTIONS, ACKNOWLEDGEMENT, SETUP and SPLASH via four literal colour substitutions; button fills and semantic/status colours unchanged. |
| 2.0 | 2026-08-13 | Correction, same day, post-deployment. EDIT C (SPLASH) withdrawn and reverted directly under the P03 §1.4.12 trivial exemption; status advanced to implemented for EDIT A, B and D. |

---

Copyright (c) 2026 William Watson. MIT License.
