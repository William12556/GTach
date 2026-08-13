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
  title: "The DISCONNECTED screen was changed to a pale dusty-yellow background with black text for readability; OPTIONS, ACKNOWLEDGEMENT, the SETUP wizard and SPLASH still use the earlier dark backgrounds with light text and are now visually inconsistent with it"
  date: "2026-08-13"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
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

affected_scope:
  components:
    - name: "DisplayManager OPTIONS menu, update and confirm-clear sub-views"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager ACKNOWLEDGEMENT screen"
      file_path: "src/gtach/display/manager.py"
    - name: "SetupDisplayManager (device-pairing wizard)"
      file_path: "src/gtach/display/setup.py"
    - name: "SplashScreen"
      file_path: "src/gtach/display/splash.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: "GTach running on target, or read of the four files listed above."
  steps:
    - "Observe the DISCONNECTED screen: pale yellow background, black text."
    - "Swipe down to OPTIONS from RADIAL: dark background (40, 40, 50), white text."
    - "Trigger the ACKNOWLEDGEMENT screen: black background, white text."
    - "Enter SETUP (clear settings, or first boot with no paired device): dark background (20, 20, 30), white text."
    - "Observe SPLASH at startup: dark blue-grey background (15, 20, 25), white text."
  frequency: "always"
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
    ACKNOWLEDGEMENT, SETUP and SPLASH.

    DISCONNECTED's own implementation (manager.py _render_disconnected)
    establishes the pattern to follow: the background and border both
    take _DISCONNECTED_BG_COLOUR (216, 200, 146) — the border is drawn
    in the same colour as the fill, producing a soft edge rather than a
    contrasting ring — and all text on the screen takes
    _DISCONNECTED_TEXT_COLOUR (0, 0, 0), with no separate dimmed tone.
    Its two buttons keep a distinct dark neutral fill, (60, 60, 80),
    with white labels, unchanged by the background swap. The candidate
    change is to apply this same three-part pattern (background, text,
    button-chip treatment left alone) to the other four screens, and is
    detailed in the resolution.approach field below.

    SETUP additionally carries semantic accent colours — primary
    (button/spinner blue), success (green), warning (orange), danger
    (red) — that DISCONNECTED has no equivalent of. These are
    functional colour-coding, not the background/text pair the
    inconsistency concerns, and are proposed to remain unchanged. The
    same applies to SPLASH's automotive-gauge progress indicator
    (graphics/splash_graphics.py SPLASH_COLORS), which is a
    self-contained decorative sub-component with its own palette, and
    to the ConnectionStatus dot colours (models.py), which are
    unchanged on DISCONNECTED itself today.
  related_issues: []

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Apply the DISCONNECTED background/text pair — (216, 200, 146) and
    (0, 0, 0) — to OPTIONS (menu, update, confirm-clear), ACKNOWLEDGEMENT,
    SETUP and SPLASH, following the pattern DISCONNECTED itself sets:

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
      success, warning and danger accents; SPLASH's automotive-gauge
      palette; and the ConnectionStatus dot everywhere it appears.

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
    - "After the change: observe SPLASH on target at startup."
    - "Confirm RADIAL is visually unchanged."
    - "Confirm DISCONNECTED is visually unchanged."
  verification_results: "Pending — requires the change to exist."

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  RADIAL and DISCONNECTED are both explicitly out of scope: RADIAL per
  William's instruction, DISCONNECTED because it is the reference this
  issue brings the other screens into line with.

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

---

Copyright (c) 2026 William Watson. MIT License.
