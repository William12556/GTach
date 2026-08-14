Created: 2026 August 13

# Issue: OPTIONS, ACKNOWLEDGEMENT, SETUP and SPLASH Do Not Match the DISCONNECTED Screen's Readability Scheme

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-ba2d5de2"
  title: "The DISCONNECTED screen was changed to a pale dusty-yellow background with black text for readability; OPTIONS, ACKNOWLEDGEMENT and the SETUP wizard still use the earlier dark backgrounds with light text and are now visually inconsistent with it"
  date: "2026-08-13"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "enhancement"
  iteration: 2
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "human_request"
  test_ref: ""
  description: >
    Requested 2026-08-13 by William. DISCONNECTED's background and text
    colours were changed (issue-<pending>, referenced in
    manager.py:2302-2308) from a saturated red field with light-grey
    text to a pale dusty-yellow background, (216, 200, 146), with black
    text, (0, 0, 0), for readability. Every other non-gauge screen
    still carries the earlier dark-background, light-text treatment,
    so the instrument now presents two unrelated visual languages
    depending on which screen is showing.

    CORRECTION, 2026-08-13, same day: SPLASH was removed from scope
    after change-ba2d5de2 iteration 1 was implemented and deployed.
    William specified the splash screen must remain black background
    with white text; the SPLASH edit in the deployed change was
    reverted directly in splash.py under the P03 §1.4.12 trivial
    exemption (single class, small delta, no interface change,
    human-approved), and this issue's scope is amended accordingly
    rather than left to describe a state that no longer applies.

affected_scope:
  components:
    - name: "DisplayManager OPTIONS menu, update and confirm-clear sub-views"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager ACKNOWLEDGEMENT screen"
      file_path: "src/gtach/display/manager.py"
    - name: "SetupDisplayManager (device-pairing wizard)"
      file_path: "src/gtach/display/setup.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: "GTach running on target, or read of the four files listed above."
  steps:
    - "Observe the DISCONNECTED screen: pale yellow background, black text."
    - "Swipe down to OPTIONS from RADIAL: dark background (40, 40, 50), white text."
    - "Trigger the ACKNOWLEDGEMENT screen: black background, white text."
    - "Enter SETUP (clear settings, or first boot with no paired device): dark background (20, 20, 30), white text."
  frequency: "always"
  # SPLASH removed from reproduction: William specified it must remain
  # black background / white text (correction, 2026-08-13).
  reproducibility_conditions: "Deterministic; a read of the four files confirms it without running the application."
  test_data: ""
  error_output: "None. Not a defect; a visual inconsistency."

behavior:
  expected: >
    A consistent colour language across the non-gauge screens, now
    that one of them has been changed for readability.
  actual: >
    DISCONNECTED alone uses the pale-yellow/black scheme. OPTIONS,
    ACKNOWLEDGEMENT, SETUP and SPLASH retain the earlier dark
    background/light text scheme, unchanged.
  impact: >
    Cosmetic. No functional or safety impact; severity is low
    accordingly. The inconsistency is visible on every transition
    between DISCONNECTED and any other non-gauge screen.
  workaround: "None needed; purely visual."

environment:
  python_version: "3.11"
  os: "Debian GNU/Linux 11 (Bullseye) 64-bit, Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "2.6.1"
  domain: "domain_1"

analysis:
  root_cause: >
    Not a defect. The DISCONNECTED colour change was scoped to that
    one screen when made; no companion change extended it to the
    other non-gauge screens.
  technical_notes: >
    RADIAL (the RPM gauge) is explicitly excluded: its border and
    centre-disc colours are the shift cue (change-64d8d8fc) and its
    palette (DAY_PALETTE / NIGHT_PALETTE, models.py) is a distinct,
    deliberately tuned system serving a different purpose. This issue
    concerns only the screens that, like DISCONNECTED, are flat
    background-plus-text presentations: OPTIONS (all three sub-views),
    ACKNOWLEDGEMENT and SETUP. SPLASH was originally included and was
    removed from scope 2026-08-13, same day, after implementation:
    William specified it must remain black background with white
    text, distinct from the DISCONNECTED-derived scheme applied
    elsewhere.

    DISCONNECTED's own implementation (manager.py _render_disconnected)
    establishes the pattern to follow: the background and border both
    take _DISCONNECTED_BG_COLOUR (216, 200, 146) — the border is drawn
    in the same colour as the fill, producing a soft edge rather than a
    contrasting ring — and all text on the screen takes
    _DISCONNECTED_TEXT_COLOUR (0, 0, 0), with no separate dimmed tone.
    Its two buttons keep a distinct dark neutral fill, (60, 60, 80),
    with white labels, unchanged by the background swap. The candidate
    change is to apply this same three-part pattern (background, text,
    button-chip treatment left alone) to the other three screens, and is
    detailed in the resolution.approach field below.

    SETUP additionally carries semantic accent colours — primary
    (button/spinner blue), success (green), warning (orange), danger
    (red) — that DISCONNECTED has no equivalent of. These are
    functional colour-coding, not the background/text pair the
    inconsistency concerns, and are proposed to remain unchanged. The
    same applies to the ConnectionStatus dot colours (models.py),
    which are unchanged on DISCONNECTED itself today.

    SPLASH is out of scope entirely (see the correction recorded
    above), so its automotive-gauge progress indicator
    (graphics/splash_graphics.py SPLASH_COLORS) was never a candidate
    for this issue and remains a self-contained decorative
    sub-component regardless.
  related_issues: []

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Apply the DISCONNECTED background/text pair — (216, 200, 146) and
    (0, 0, 0) — to OPTIONS (menu, update, confirm-clear), ACKNOWLEDGEMENT
    and SETUP, following the pattern DISCONNECTED itself sets. SPLASH is
    excluded (correction, 2026-08-13): it must remain black background
    with white text.

    - Screen background fill becomes (216, 200, 146).
    - Every text colour drawn directly on that background becomes
      (0, 0, 0), collapsing any existing dimmed/secondary text tone to
      the same value, as DISCONNECTED does — it draws its title,
      message and cause line in one colour, not two.
    - Each screen's circular border, currently a static red ring
      (200, 0, 0), is drawn in the background colour instead, matching
      _draw_shift_border(self._DISCONNECTED_BG_COLOUR) in
      _render_disconnected — a soft edge, not a contrasting ring.
    - Button fills and their (white) labels are left exactly as they
      are: DISCONNECTED's own buttons keep a dark neutral fill
      unrelated to the background swap, and OPTIONS/confirm/update's
      existing button fills already follow that same convention.
    - Semantic/status colours are left unchanged: SETUP's primary,
      success, warning and danger accents, and the ConnectionStatus
      dot everywhere it appears.

    Full detail, file by file, is left to the coupled change document.
  change_ref: ""
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    When a screen's colour treatment is changed for a stated reason
    (here, readability), check whether sibling screens sharing the same
    visual role should change with it.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "After the change: visually inspect OPTIONS (both pages), the update sub-view and the confirm-clear sub-view on target — background and text match DISCONNECTED."
    - "After the change: visually inspect ACKNOWLEDGEMENT on target."
    - "After the change: run through SETUP (welcome, discovery, device list, pairing, complete, current device) on target."
    - "Confirm SPLASH is visually unchanged (black background, white text) — explicitly excluded from this issue."
    - "Confirm RADIAL is visually unchanged."
    - "Confirm DISCONNECTED is visually unchanged."
  verification_results: "Pending — requires the change to exist."

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  RADIAL, DISCONNECTED and SPLASH are all explicitly out of scope:
  RADIAL per William's instruction, DISCONNECTED because it is the
  reference this issue brings the other screens into line with, and
  SPLASH per William's correction of 2026-08-13 — it must remain black
  background with white text and was reverted to that state directly
  in splash.py under the P03 §1.4.12 trivial exemption after
  change-ba2d5de2 iteration 1 had already applied the DISCONNECTED
  scheme to it.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-13"
    author: "William Watson"
    changes:
      - "Initial issue document from user request to extend DISCONNECTED's readability colour scheme to the other non-gauge screens."
      - "Scopes the change to OPTIONS, ACKNOWLEDGEMENT, SETUP and SPLASH; excludes RADIAL (explicit) and DISCONNECTED (the reference)."
      - "Records the pattern DISCONNECTED itself sets: background and border share one colour, all text collapses to one colour, button chips and semantic/status colours are left unchanged."
  - version: "2.0"
    date: "2026-08-13"
    author: "William Watson"
    changes:
      - "CORRECTION, same day: SPLASH removed from scope. William specified the splash screen must remain black background with white text."
      - "change-ba2d5de2 iteration 1 had already been implemented and deployed with SPLASH included; the SPLASH edit was reverted directly in splash.py under the P03 §1.4.12 trivial exemption rather than through a new T-Doc cycle, per governance §7.0's direct-edit allowance for ai/workspace/ documents."
      - "Every affected_scope, reproduction, technical_notes, resolution.approach and verification_enhanced entry naming SPLASH is amended to remove it from scope."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-13 | Initial issue document. Extends the DISCONNECTED screen's pale-yellow/black readability scheme to OPTIONS, ACKNOWLEDGEMENT, SETUP and SPLASH, excluding RADIAL and DISCONNECTED itself. |
| 2.0 | 2026-08-13 | Correction, same day. SPLASH removed from scope after deployment; it must remain black background with white text and was reverted under the P03 §1.4.12 trivial exemption. |

---

Copyright (c) 2026 William Watson. MIT License.
