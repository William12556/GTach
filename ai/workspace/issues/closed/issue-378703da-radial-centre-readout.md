Created: 2026 August 04

# Issue: The Highest-Acuity Region of the Display Shows a Fixed Brand String, and a Second Mode Exists That Nothing Advertises

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-378703da"
  title: "The RADIAL centre disc displays the fixed string 'GTach' and the numeric RPM is not shown in RADIAL at all; DIGITAL is reachable only by an unadvertised horizontal swipe, and the mode selector written to advertise it is never called"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-378703da"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Findings §7.5 (Centre of the RADIAL Display Carries No Information)
    and §7.6 (Mode Change Has No Visible Affordance), with §9.5
    recommendation 25. The report's own numbering is preserved so
    coverage remains auditable after the report closes (ai/task.md
    §7.6.4). Scope is directed by ai/task.md §7.3.14, which resolves the
    report's conditional wording. Task list reference ai/task.md §7.3.10.

affected_scope:
  components:
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_digital_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._handle_swipe_left"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._handle_swipe_right"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._render_mode_selector"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._load_config"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._save_config"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayMode"
      file_path: "src/gtach/display/models.py"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: >
    Source checkout at 0.3.2. Observation of the centre disc requires
    the panel; the code findings do not.
  steps:
    - "rec 25 §7.5 — read manager.py:976-985. center_radius is 99 and the string rendered at the centre is the literal 'GTach'."
    - "rec 25 §7.5 — compute the area: pi * 99^2 = 30,790 px, against 230,400 for the 480x480 field — 13.4%."
    - "rec 25 §7.5 — grep _draw_radial_mode for the RPM value being rendered as text. It is not. rpm is used for the fill arc (manager.py:891-896) and the indicator line (956-964) only."
    - "rec 25 §7.5 — read typography.py:80. FONT_RPM_MEDIUM = 28 carries the comment 'Gauge mode center readout'."
    - "§7.6 — read manager.py:167-197. _handle_swipe_left maps DIGITAL to RADIAL and _handle_swipe_right maps RADIAL to DIGITAL. These are the only transitions between the two."
    - "§7.6 — read manager.py:1423-1461. _render_mode_selector draws a two-segment selector and registers both regions."
    - "§7.6 — grep _render_mode_selector across src/gtach and confirm the only occurrence is its own definition. It is never called."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional. Both findings are static properties of the code.

    §7.6's practical consequence — that an operator does not discover
    DIGITAL — cannot be reproduced from the source and has not been
    measured. It is inferred from the absence of any affordance.
  preconditions: "None for the code findings."
  test_data: >
    MODE REACHABILITY, established rather than assumed.

    The swipe handlers at manager.py:167-197 are gated at 171 and 187 on
    the obd_protocol thread being RUNNING or _sim_mode being set, so the
    modes cannot be exchanged from the DISCONNECTED screen at all.
    _handle_long_press (manager.py:199-213) sets mode to DIGITAL when
    leaving OPTIONS (manager.py:204), which is a third, unadvertised
    route into DIGITAL and one that fires whenever the operator leaves
    the options screen — regardless of which mode they were in when
    they entered it.

    That last point matters and the report does not record it: leaving
    OPTIONS silently switches a RADIAL user to DIGITAL. Anyone who has
    used the options screen is in DIGITAL afterwards whether they chose
    it or not.

    PERSISTENCE. manager.py:269-300 reads 'mode' from the display's own
    config.yaml, defaulting to RADIAL at 275, and rejects the three
    transient modes at 281-283 in favour of RADIAL. manager.py:342-373
    writes it back, substituting _post_splash_mode for transient modes.
    Independently, utils/config.py:588 defaults DisplayConfig.mode to
    the string 'DIGITAL' in from_dict, and the checked-in
    config/config.yaml carries display.mode: DIGITAL. An installed
    system will therefore have DIGITAL persisted in at least one of the
    two files, and the retirement must tolerate reading it rather than
    failing on it.

    WHAT DIES WITH DIGITAL, and what does not. _draw_digital_mode
    (manager.py:715-786) is reached only from _render_normal_modes at
    manager.py:548. _get_band_colour (manager.py:616-678) is called
    only from _draw_digital_mode at manager.py:737 — so on a literal
    reading it dies too. It must NOT be deleted: task 7.3.11
    (5014040c, the annular band indicator) needs exactly that
    hysteresis-bearing band selection for RADIAL. Deleting it here and
    reinstating it there would discard the hysteresis logic that
    4c038bed added and that 7.3.11 depends on. Recorded because a
    dead-code sweep after this change would otherwise remove it
    correctly and destructively.
  error_output: "None. Neither finding produces an error."

behavior:
  expected: >
    The largest and most central region of a gauge shows the quantity
    the gauge measures. A product does not carry two display modes when
    one is a superset of the other, and does not switch the operator
    between them without being asked.
  actual: >
    (a) §7.5 — the centre disc, 13.4% of the field and the region of
    highest visual acuity for a centred gaze, renders the fixed string
    'GTach' (manager.py:983). The numeric RPM appears nowhere in RADIAL.
    An operator wanting the number must switch to DIGITAL.

    (b) §7.6 — DIGITAL and RADIAL are exchanged only by horizontal
    swipe (manager.py:167-197), with nothing on either screen
    indicating that a second mode exists or that swiping does anything.
    _render_mode_selector (manager.py:1423) draws precisely such a
    control, complete with touch registration, and is called from
    nowhere. Additionally, and not recorded in the report, leaving the
    OPTIONS screen forces DIGITAL (manager.py:204) irrespective of the
    mode in use beforehand.
  impact: >
    (a) The primary readout is absent from the primary display mode.
    This is the substantive finding; the rest follows from it.

    (b) Two modes are maintained, tested and documented where one would
    do, and the mode in force is not under the operator's control after
    a visit to the options screen.
  workaround: >
    (a) Switch to DIGITAL, losing the arc.
    (b) None. The swipe is undiscoverable without documentation.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    (a) The centre disc was designed as a shift-cue indicator — it is
    filled from _get_shift_cue (manager.py:975-977) and flashes above
    caution_start — and the brand string was placed on it because the
    disc existed and was empty. The readout that
    TypographyConstants.FONT_RPM_MEDIUM was declared for
    (typography.py:80, "Gauge mode center readout") was never built.

    (b) DIGITAL preceded RADIAL. When RADIAL was added it became a
    parallel mode rather than a replacement, and the selector written
    to expose the choice was never wired in. The DIGITAL default at
    manager.py:204 is a remnant of DIGITAL having once been the only
    mode.
  technical_notes: >
    SCOPE IS DIRECTED, NOT CONDITIONAL. The report's recommendation 25
    reads "Place the numeric RPM in the RADIAL centre disc; consider
    retiring DIGITAL as a separate mode", and §7.6 offers two
    resolutions. ai/task.md §7.3.14 resolves both: the numeral is
    placed in the centre disc AND DIGITAL is retired as a separate
    mode. The triple is authored to that decision, not to the report's
    conditional wording. §7.6 is therefore closed by retirement rather
    than by adding the mode indicator the report offers as the
    alternative.

    FOUR CONSEQUENCES OF THE RETIREMENT, per ai/task.md §7.3.14.

    (1) The horizontal-swipe mode change (manager.py:167-197) becomes
    dead and is removed. §7.3.14 cites "manager.py:142-172"; at 0.3.2
    the handlers are at 167-197 and their registration is at
    _setup_touch_callbacks (manager.py:150-166). The swipe *gestures*
    themselves are provided by the touch subsystem and are used
    elsewhere; only these two handlers and their registration go.

    (2) _render_mode_selector (manager.py:1423) becomes dead and is
    removed. §7.3.14 cites manager.py:1091; it is at 1423 at 0.3.2.

    (3) §7.6 is closed by retirement. No mode indicator is added.

    (4) DisplayMode.DIGITAL (models.py:65) and any persisted
    config.mode value require a migration path. See test_data: DIGITAL
    is the checked-in default in config/config.yaml and the hard-coded
    default in utils/config.py:588, so it will be present in the field.

    ONE CORRECTION AND ONE ADDITION TO §7.3.14.

    Correction — §7.3.14 says the swipe handler and the mode selector
    "become dead and are removed". _handle_long_press (manager.py:199)
    does not become dead: it is the only route into and out of OPTIONS
    and must survive. Only its DIGITAL assignment at manager.py:204
    changes, to RADIAL. §7.3.14 does not mention it and a literal
    reading of "the horizontal-swipe mode change ... is removed" would
    leave manager.py:204 setting a retired mode.

    Addition — _get_band_colour must be retained despite becoming
    uncalled by this change, because 7.3.11 (5014040c) requires it. See
    test_data.

    RELATIONSHIP TO 7.3.11 AND 7.3.5. This change puts a numeral in the
    centre disc, which 7.3.5 (821919ce, render caching) classifies as
    part of the varying content rather than the static layer — the
    report's §5.3 already lists "the centre disc with its label" among
    the three varying elements, so no cache-key consequence arises.
    7.3.11 replaces the full-field band colour with an annular
    indicator; that is a separate region and does not conflict with the
    centre readout, but both triples touch _draw_radial_mode and the
    later of the two is written against the earlier.
  related_issues:
    - issue_ref: "issue-5014040c"
      relationship: "related"
    - issue_ref: "issue-b02ed4ea"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Render the conditioned RPM as a numeral in the RADIAL centre disc in
    place of the brand string. Remove _draw_digital_mode, the two swipe
    handlers and their registration, and _render_mode_selector. Retire
    DisplayMode.DIGITAL with a migration that maps a persisted or
    defaulted DIGITAL to RADIAL on read. Retain _get_band_colour for
    7.3.11. See change-378703da.
  change_ref: "change-378703da"
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
    A control that is written but never called is indistinguishable
    from one that was deleted, except that it survives review as though
    it were live. _render_mode_selector registered touch regions and
    would have appeared functional to anyone reading it in isolation.

    A mode added alongside an existing one rather than replacing it
    doubles the surface permanently unless the decision to keep both is
    recorded with a reason.
  process_improvements: >
    The retention of _get_band_colour against a future caller is
    recorded here and in change-378703da precisely because a dead-code
    analysis run after this change would correctly identify it as
    uncalled. Sequencing 7.3.11 immediately after this triple would
    remove the window; if that is not done, the retention note is the
    only thing standing between the hysteresis logic and a correct
    deletion.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/manager.py src/gtach/display/models.py src/gtach/utils/config.py passes."
    - "DisplayMode has no DIGITAL member."
    - "grep confirms no reference to DisplayMode.DIGITAL remains in src/gtach."
    - "The RADIAL centre disc renders the conditioned RPM, formatted to one decimal in thousands, in place of 'GTach'."
    - "The numeral is legible against every centre-disc colour _get_shift_cue can return, including the flashing dark variant."
    - "_draw_digital_mode, _handle_swipe_left, _handle_swipe_right and _render_mode_selector are absent."
    - "_setup_touch_callbacks no longer registers the two swipe handlers, and registers everything else it does today."
    - "_handle_long_press exists and sets RADIAL, not DIGITAL, when leaving OPTIONS."
    - "A config.yaml carrying mode: DIGITAL loads without error and yields RADIAL."
    - "A config.yaml carrying an unknown mode string still yields RADIAL with a warning, as it does today."
    - "utils/config.py DisplayConfig.from_dict no longer defaults to the string 'DIGITAL'."
    - "config/config.yaml no longer carries display.mode: DIGITAL."
    - "_get_band_colour is present and unmodified, with a comment recording why it is retained."
    - "_condition_rpm and _get_shift_cue are unmodified."
    - "Long press still enters and leaves OPTIONS; the ACKNOWLEDGEMENT and DISCONNECTED paths are unaffected."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-378703da"
  test_refs: []

notes: >
  This is task 7.3.10 in ai/task.md §7.3 and step 9 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5), where it is
  recorded as "the largest behavioural change in the set".

  issue_info.type is enhancement per ai/task.md §7.2: §7.5 and §7.6 are
  display §7.x user interface proposals. Severity is medium — the
  absent readout is a real functional gap in the primary mode, but
  nothing is broken.

  Scope is directed by ai/task.md §7.3.14, which resolves the report's
  "consider" as accepted. One correction to that section is recorded in
  technical_notes: _handle_long_press survives and its DIGITAL
  assignment changes, which §7.3.14 does not mention.

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
      - "Initial issue document from display-ui-graphics-review.md findings §7.5 and §7.6 with §9.5 recommendation 25, scoped to the directed decision in ai/task.md §7.3.14."
      - "Recorded a third, unadvertised route into DIGITAL that the report does not: _handle_long_press forces DIGITAL when leaving OPTIONS, so any operator who visits the options screen is switched out of RADIAL."
      - "Recorded one correction to §7.3.14 — _handle_long_press survives the retirement and only its DIGITAL assignment changes — and one addition: _get_band_colour becomes uncalled but must be retained for 7.3.11, or the hysteresis added by 4c038bed is lost to a correct dead-code deletion."
      - "Recorded the persistence surface requiring migration: config/config.yaml display.mode, utils/config.py:588's 'DIGITAL' default, and the display's own config.yaml read at manager.py:275."

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
| 1.0 | 2026-08-04 | Initial issue document from display review findings §7.5 and §7.6 with recommendation 25, scoped to ai/task.md §7.3.14's directed decision. Records the undocumented OPTIONS-exit route into DIGITAL, a correction and an addition to §7.3.14, and the full persistence surface requiring migration. |

---

Copyright (c) 2026 William Watson. MIT License.
