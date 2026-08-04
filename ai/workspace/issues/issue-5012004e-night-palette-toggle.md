Created: 2026 August 04

# Issue: The Palette Is Fixed at Full Saturation and There Is No Way to Dim It

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-5012004e"
  title: "The display palette is fixed at full saturation with no day/night provision, and the panel backlight cannot be reduced in software, so at night the instrument is a bright light source in the driver's forward field of view"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-5012004e"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Finding §7.9 (No Day/Night Provision) with §9.5 recommendation 29.
    Scope is directed by ai/task.md §7.3.14, which accepts a dimmed
    night palette with a manual toggle and rules automatic switching out
    of scope. Task list reference ai/task.md §7.3.12.

affected_scope:
  components:
    - name: "DisplayManager face palette"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._get_band_colour"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._get_shift_cue"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._load_config"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._save_config"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: >
    Authored against the post-5014040c tree. That change introduces the
    named face constants this one varies; without it there is no single
    place to vary.
  steps:
    - "§7.9 — grep manager.py for any conditional on ambient light, time of day, or a brightness setting. There is none."
    - "§7.9 — read the HyperPixel documentation cited by report §7.2: the backlight cannot be switched off or dimmed by software on this panel."
    - "§7.9 — read manager.py:700-709. _get_shift_cue returns (0, 160, 0), (0, 180, 0), (0, 100, 255), (200, 0, 0) and (255, 128, 0)-class colours at full saturation regardless of conditions."
    - "§7.9 — read the six band colours in _get_band_colour. Pure blue, green, yellow, orange and red, all at 255."
    - "Confirm no persisted setting governs brightness: read _save_config (manager.py:342-373) and observe the six keys it writes."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional in code. The consequence requires darkness and has not
    been observed on the vehicle; it is inferred from the emitted-light
    argument the report makes for §7.2 and extends here.
  preconditions: "Night driving, for the consequence."
  test_data: >
    The three brightest elements at night, by area times relative
    luminance, after change-5014040c has darkened the face:

      the coloured fill arc, up to 114,700 px at full sweep, at
      luminance 0.7152 (green) or 0.9278 (yellow);
      the centre disc, 30,790 px, at 0.1699 (the green shift cue) or
      lower;
      the tick marks and numerals in FACE_TICK, small in area but the
      highest-contrast elements on the face.

    5014040c removes the largest contributor — the light-grey ground —
    so the arc becomes the dominant emitter. A night palette that dims
    the face but not the arc would therefore achieve little, which is
    the main design constraint on this change.
  error_output: "None."

behavior:
  expected: >
    An instrument intended for night use offers a dimmed presentation,
    since the panel itself cannot be dimmed.
  actual: >
    The palette is fixed. Every colour — the band colours, the shift-cue
    colours, the face constants introduced by 5014040c — is a literal
    with one value. There is no toggle, no setting, and no code path
    that varies any of them.
  impact: >
    At night the instrument is a bright, saturated light source
    positioned in the driver's forward field of view, with no operator
    control. The report classifies this as a scope decision rather than
    a defect, and ai/task.md §7.3.14 has taken that decision.
  workaround: >
    None in software. Physically obscuring the panel is the only
    recourse, which defeats its purpose.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    The palette was chosen for daylight legibility, which is the harder
    case, and no second case was provided for. The panel's inability to
    dim its own backlight makes this a software problem rather than a
    hardware setting, which is not obvious and is easily assumed away.
  technical_notes: >
    SCOPE IS DIRECTED AND BOUNDED. ai/task.md §7.3.14 accepts a dimmed
    night palette with a manual toggle and states that no ambient light
    sensor is available on the target hardware, so automatic switching
    is out of scope and MUST NOT be specified. It further requires this
    change document to state where the toggle lives in the UI and
    whether its state persists across restart. Both are answered in
    change-5012004e.

    THE SITING PROBLEM, WHICH IS REAL AND CONSTRAINED FROM TWO SIDES.

    §7.3.14 notes the toggle "is a new touch target and is subject to
    the same >= 72 px / >= 16 px geometry" as 7.3.9 (b02ed4ea). That
    change establishes a three-target maximum on the options menu,
    derived from the circular viewport's vertical budget, and already
    fills all three: Bluetooth/Simulation, Debug, Check for updates. It
    also removes Clear settings from the menu for want of a fourth slot,
    leaving that control without a top-level entry point pending display
    report §7.7's re-layout.

    So the options menu has no room. Adding a fourth control there would
    directly contradict b02ed4ea's central constraint. Three sitings
    remain, and change-5012004e records the choice with its reasons.

    DEPENDENCY ON 5014040c IS STRONGER THAN THE TASK LIST RECORDS.
    ai/task.md §7.6.1 records 7.3.12 as depending on 7.3.11 because
    "the night palette must cover the annular indicator's colours". The
    stronger reason is structural: 5014040c is what converts the face's
    colours from scattered literals into six named constants. Without
    that, a night palette must find and vary eight inline literals in
    _draw_radial_mode plus two palettes, and the change becomes
    substantially larger and more error-prone.

    THE ARC IS THE PROBLEM, NOT THE FACE. See test_data. After 5014040c
    the fill arc is the dominant night emitter, so a night palette that
    varies only the FACE_ constants would be largely cosmetic. The band
    colours must have night variants too, and those variants must remain
    mutually distinguishable — a dimmed yellow and a dimmed orange are
    closer together than the full-saturation pair, and the band cue is
    the instrument's primary signal. This is the substantive design
    constraint and is the reason the change is not simply a scalar
    multiply.

    D3 CACHE-KEY OBLIGATION. Cross-check discrepancy D3
    (ai/workspace/report/task-list-cross-check-discrepancies.md §7.0,
    step 5) requires this change to add the palette variant to 7.3.5's
    static-layer cache key, and to verify that toggling produces a full
    redraw rather than a stale blit. If 821919ce has landed, that
    obligation is live here; if it has not, its change document must
    include the palette variant in the key from the outset, which
    change-821919ce records.
  related_issues:
    - issue_ref: "issue-5014040c"
      relationship: "blocked_by"
    - issue_ref: "issue-b02ed4ea"
      relationship: "blocked_by"
    - issue_ref: "issue-821919ce"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Introduce a day and a night variant of every colour the instrument
    draws — face constants, band colours and shift-cue colours — behind
    a single palette selector. Add a manual toggle, sited per
    change-5012004e, and persist its state. See change-5012004e.
  change_ref: "change-5012004e"
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
    A palette chosen for one lighting condition should record that it
    was, so the absence of the other case is visible rather than
    implicit.
  process_improvements: >
    The siting conflict between this triple and b02ed4ea was foreseeable
    from ai/task.md §7.3.14's own note and was not surfaced until both
    were authored. Where a plan states that one triple adds a control
    and another caps the number of controls, the two should be reconciled
    at plan time.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "Every colour the instrument draws has a day and a night value; no drawing call reads a bare literal."
    - "In night mode, every element's relative luminance is lower than its day value."
    - "The six night band colours are mutually distinguishable: minimum pairwise CIE76 delta-E across adjacent bands is computed and recorded."
    - "Night tick and numeral contrast against the night ground is >= 4.5:1."
    - "Night band colours against the night ground are >= 3:1."
    - "The toggle is a touch target of height >= 72 px with >= 16 px separation from its neighbours, per b02ed4ea."
    - "Toggling changes the rendered colours on the next frame."
    - "The toggle's state survives a restart."
    - "No ambient light sensor, time-of-day check or automatic switch exists anywhere in the change."
    - "If change-821919ce has landed: the static-layer cache key includes the palette variant, and toggling produces a full redraw rather than a stale blit."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-5012004e"
  test_refs: []

notes: >
  This is task 7.3.12 in ai/task.md §7.3 and step 9 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5).

  issue_info.type is enhancement per ai/task.md §7.2. Severity low: the
  report itself classifies §7.9 as a scope decision rather than a
  defect, and nothing malfunctions without it.

  Two prerequisites, both stronger than ai/task.md §7.6.1 records.
  5014040c must land first because it creates the named constants this
  change varies. b02ed4ea must land first because it establishes the
  touch-target geometry and the three-control budget that determine
  where this toggle can go — and it leaves no room on the options menu,
  which change-5012004e addresses directly.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial issue document from display-ui-graphics-review.md finding §7.9 with §9.5 recommendation 29, scoped to ai/task.md §7.3.14's directed decision: manual toggle only, no automatic switching."
      - "Recorded the siting conflict with b02ed4ea: that change caps the options menu at three targets and already fills all three, so the toggle cannot go there without contradicting its central constraint."
      - "Recorded that the fill arc, not the face, is the dominant night emitter after 5014040c, so the band colours require night variants that remain mutually distinguishable — the substantive design constraint."
      - "Recorded that the dependency on 5014040c is structural, not merely a matter of covering the indicator's colours: it creates the named constants this change varies."
      - "Recorded the D3 cache-key obligation toward 7.3.5."

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
| 1.0 | 2026-08-04 | Initial issue document from display review finding §7.9 with recommendation 29. Records the siting conflict with b02ed4ea's three-control budget, the fill arc as the dominant night emitter, and the structural dependency on 5014040c. |

---

Copyright (c) 2026 William Watson. MIT License.
