Created: 2026 August 04

# Change: Two Palettes, One Selector, and a Long-Press Toggle on the Gauge Itself

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-5012004e"
  title: "Every drawn colour gains a night variant behind a Palette selector; the toggle is a double-tap on the gauge face rather than an options-menu item, because b02ed4ea's three-control budget is full; the selection persists in config.yaml"
  date: "2026-08-04"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-5012004e"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-5012004e"
  description: >
    Resolves issue-5012004e. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 finding §7.9
    with §9.5 recommendation 29, scoped by ai/task.md §7.3.14. Task list
    reference ai/task.md §7.3.12.

scope:
  summary: >
    A Palette object holds every colour the instrument draws. Two
    instances exist, DAY and NIGHT. A selector on DisplayManager chooses
    between them, a double-tap on the gauge face toggles it, and the
    choice is written to config.yaml.
  affected_components:
    - name: "Palette"
      file_path: "src/gtach/display/models.py"
      change_type: "add"
    - name: "DisplayManager._palette"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._toggle_palette"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._handle_double_tap"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._get_band_colour"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._get_shift_cue"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._load_config"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._save_config"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Automatic day/night switching. Explicitly excluded by ai/task.md §7.3.14 — the target hardware has no ambient light sensor. No time-of-day heuristic either; that is automatic switching by another name."
    - "Backlight control. The HyperPixel 2.1 Round does not expose it to software."
    - "A brightness slider or any continuous control. Two states only."
    - "The options menu. It carries three targets and all three are occupied; see the siting decision below."
    - "The setup subsystem's palette. It has its own rendering and is not covered by recommendation 29."
    - "The splash screen's colours."
    - "The OPTIONS, ACKNOWLEDGEMENT and DISCONNECTED screens' colours. The finding concerns the instrument in use at night; those screens are transient. Recorded as a deliberate boundary, revisitable."

rational:
  problem_statement: >
    The palette is fixed at full saturation and the panel's backlight
    cannot be reduced in software, so at night the instrument is a
    bright light source in the driver's forward field of view with no
    operator control.
  proposed_solution: >
    Two complete palettes behind one selector, with a manual toggle and
    a persisted choice.
  alternatives_considered:
    - option: "Scale every day colour by a constant factor to derive the night palette."
      reason_rejected: >
        One line, and wrong. Scaling compresses the six band colours
        toward each other: a 0.4x yellow (102, 102, 0) and a 0.4x orange
        (102, 51, 0) are far less distinguishable than the originals,
        and the band cue is the instrument's primary signal. The night
        palette is authored colour by colour, with the pairwise
        separation of the band colours computed rather than assumed.
    - option: "Site the toggle on the options menu."
      reason_rejected: >
        The obvious place, and it is full. change-b02ed4ea caps the menu
        at three targets — a consequence of the circular viewport's
        vertical budget, not a preference — and all three are occupied
        by Bluetooth/Simulation, Debug and Check for updates. That
        change already had to remove Clear settings for want of a
        fourth slot. Adding this toggle as a fourth would contradict the
        constraint that b02ed4ea exists to establish."
    - option: "Wait for display report §7.7's circular options re-layout to free a slot."
      reason_rejected: >
        §7.7 is deferred to a P10 requirements cycle (ai/task.md
        §7.3.15) with no date, and is itself gated on observing
        b02ed4ea's three-item layout on the panel. Blocking a v0.4.0
        item on an undated future cycle is not a plan. Recorded as the
        preferred long-term home: when §7.7 delivers more room, the
        toggle should move to the menu and the gesture can be retired.
    - option: "A dedicated on-screen control on the gauge face."
      reason_rejected: >
        A permanent button on the instrument face costs area on the one
        screen whose area is most spoken for, and would itself be a lit
        element at night. Rejected in favour of a gesture, which costs
        no pixels.
    - option: "Double-tap on the gauge face — TAKEN."
      reason_rejected: >
        Not rejected; recorded here for comparison. Costs no screen
        area, is available in the mode where it is wanted, and reuses
        the existing gesture subsystem. Its weakness is discoverability
        — the same objection display §7.6 raised against the swipe
        that change-378703da retired. Mitigated by a brief on-screen
        confirmation of the new state when it fires, so an accidental
        toggle explains itself, and by the persistence making it a
        once-per-season action rather than a routine one.
  benefits:
    - "The operator gains control over the instrument's emitted light at night, which the hardware does not otherwise provide."
    - "Every drawable colour has one owner, so a future third palette is a third instance rather than a third set of literals."
    - "No screen area is consumed and b02ed4ea's three-control budget is not breached."
  risks:
    - risk: >
        A gesture is undiscoverable — the objection that retired the
        swipe in 378703da.
      mitigation: >
        Weaker here than there: the swipe hid an entire display mode,
        whereas this hides a setting whose absence leaves the
        instrument fully functional. The on-screen confirmation and the
        persistence both reduce the cost of not knowing. Recorded as the
        change's main weakness, with the options menu named as the
        preferred home once §7.7 frees a slot.
    - risk: >
        An accidental double-tap dims the instrument while driving.
      mitigation: >
        The confirmation names the new state, and a second double-tap
        restores it. The consequence is a visual change, not a
        functional one."
    - risk: >
        Night band colours are less distinguishable than day ones,
        degrading the primary cue in the condition where it matters.
      mitigation: >
        Pairwise separation of adjacent band colours is computed in the
        tests and recorded, not eyeballed. The night palette is authored
        per colour with hue separation preserved rather than derived by
        scaling."
    - risk: >
        7.3.5's static-layer cache serves a stale day-palette surface
        after a toggle.
      mitigation: >
        Cross-check D3 step 5 requires the palette variant in the cache
        key. change-821919ce carries it from the outset; this change
        verifies the redraw on toggle. Both halves are asserted.
  benefits_measurement: >
    Night-mode relative luminance, area-weighted across the face, arc,
    ticks and centre disc: targeted at below 25% of the day value.
    Minimum pairwise CIE76 delta-E between adjacent night band colours:
    recorded, with a floor of 25 as the acceptance figure.

technical_details:
  current_behavior: >
    After change-5014040c the face colours are six class constants on
    DisplayManager — FACE_GROUND, FACE_TRACK, FACE_TICK, FACE_LINE,
    FACE_EDGE, FACE_LABEL — and the band colours are one BAND_COLOURS
    tuple. _get_shift_cue (manager.py:680-713) still holds its five
    colours as inline literals. Nothing varies any of them.
  proposed_behavior: >
    A frozen Palette dataclass in display/models.py holds all of them.
    DAY_PALETTE and NIGHT_PALETTE are module-level instances.
    DisplayManager._palette references one; every drawing site reads
    through it. A double-tap toggles the reference and writes the
    choice; _load_config restores it.
  implementation_approach: >
    FOUR STEPS.

    STEP 1 — the Palette dataclass in display/models.py, frozen, with a
    field per colour: the six face colours, the six band colours as a
    tuple, and the five shift-cue colours. Two module-level instances,
    DAY_PALETTE carrying exactly today's values and NIGHT_PALETTE
    carrying authored night values.

    Authoring DAY_PALETTE from the current constants rather than
    inventing values is what makes the change behaviour-preserving in
    day mode, and lets the tests assert that day rendering is
    unchanged colour for colour.

    STEP 2 — route every drawing site through self._palette. The eight
    face sites in _draw_radial_mode, the BAND_COLOURS reads in
    _get_band_colour and the arc loop, and the five returns in
    _get_shift_cue.

    STEP 3 — the toggle. Register a double-tap handler through the
    existing gesture subsystem, gated to RADIAL so it cannot fire on
    the options or setup screens. It swaps _palette, sets a
    _palette_notice_until timestamp, and calls _save_config.
    _draw_radial_mode renders 'Night' or 'Day' near the bottom of the
    face while that timestamp is in the future.

    STEP 4 — persistence. _save_config writes a seventh key,
    'palette'; _load_config reads it, defaulting to 'day' and
    tolerating an unknown value with a warning, as it does for mode.
  code_changes:
    - component: "Palette, DAY_PALETTE, NIGHT_PALETTE"
      file: "src/gtach/display/models.py"
      change_summary: "A frozen dataclass holding every drawable colour, and two instances."
      classes_affected:
        - "Palette"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _palette selector added and read at every drawing site. Double-tap
        toggle with a transient on-screen confirmation. Palette
        persisted through _save_config and restored in _load_config.
      functions_affected:
        - "_draw_radial_mode"
        - "_get_band_colour"
        - "_get_shift_cue"
        - "_toggle_palette"
        - "_handle_double_tap"
        - "_setup_touch_callbacks"
        - "_load_config"
        - "_save_config"
      classes_affected:
        - "DisplayManager"
  data_changes:
    - "config.yaml gains a 'palette' key with values 'day' or 'night'. Absent in existing files, which default to 'day' — the current behaviour."
  interface_changes:
    - "_get_band_colour and _get_shift_cue read self._palette rather than class constants. Their signatures are unchanged."

dependencies:
  internal:
    - component: "change-5014040c"
      impact: "PREREQUISITE. It creates the named face constants and the single BAND_COLOURS table this change converts into palette fields. Without it this change must find and vary eight inline literals."
    - component: "change-b02ed4ea"
      impact: "PREREQUISITE. It establishes the touch-target geometry and the three-control budget that rule the options menu out as the toggle's home."
    - component: "change-821919ce"
      impact: "If landed, its cache key must include the palette variant — cross-check D3 step 5. This change verifies the redraw on toggle."
    - component: "The gesture subsystem — touch.py and the registrations in _setup_touch_callbacks (manager.py:150-166)"
      impact: "Supplies double-tap detection. Read-only; the registration is added alongside the surviving long press."
  external: []
  required_changes:
    - change_ref: "change-5014040c"
      relationship: "blocked_by"
    - change_ref: "change-b02ed4ea"
      relationship: "blocked_by"
    - change_ref: "change-821919ce"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with SDL_VIDEODRIVER=dummy and a mocked rendering engine.
    Colour relationships are computed from the palette instances rather
    than inspected. Persistence is tested against real YAML in a
    temporary directory. Day-mode rendering is asserted equal to the
    pre-change output, colour for colour, which is the guarantee that
    the refactor is behaviour-preserving.
  test_cases:
    - scenario: "DAY_PALETTE's fields against the pre-change constants."
      expected_result: "Identical, field for field."
    - scenario: "Rendering one frame per band in day mode, before and after the change."
      expected_result: "The same colours are passed to the same primitives."
    - scenario: "Every NIGHT_PALETTE field against its DAY_PALETTE counterpart."
      expected_result: "Lower relative luminance in every case."
    - scenario: "Pairwise CIE76 delta-E between adjacent night band colours."
      expected_result: ">= 25 for every adjacent pair; the figures recorded."
    - scenario: "Night tick and numeral contrast against the night ground."
      expected_result: ">= 4.5:1."
    - scenario: "Each night band colour against the night ground."
      expected_result: ">= 3:1."
    - scenario: "Area-weighted night luminance against day."
      expected_result: "< 25%."
    - scenario: "_toggle_palette from day."
      expected_result: "_palette is NIGHT_PALETTE; _save_config is called."
    - scenario: "_toggle_palette twice."
      expected_result: "Back to DAY_PALETTE."
    - scenario: "A frame rendered immediately after a toggle."
      expected_result: "Night colours, not day."
    - scenario: "The double-tap handler while in OPTIONS or setup mode."
      expected_result: "No toggle."
    - scenario: "The transient confirmation."
      expected_result: "Rendered while _palette_notice_until is in the future, absent afterwards."
    - scenario: "_save_config then _load_config with palette night."
      expected_result: "NIGHT_PALETTE restored."
    - scenario: "_load_config with no palette key."
      expected_result: "DAY_PALETTE; no warning — absence is the upgrade case."
    - scenario: "_load_config with palette: nonsense."
      expected_result: "DAY_PALETTE with a warning."
    - scenario: "grep for any ambient-light, time-of-day or automatic switch."
      expected_result: "None — §7.3.14 excludes it."
  regression_scope:
    - "tests/display/ — the display suite once populated per ai/task.md §8.2."
    - "On gtach.local at night: the instrument is materially dimmer and every band is still identifiable."
    - "On gtach.local in daylight: day mode is indistinguishable from the pre-change build."
    - "On gtach.local: the toggle survives a restart."
    - "On gtach.local: a double-tap in OPTIONS does not toggle."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py src/gtach/display/models.py passes."
    - "pytest tests/ passes with no new failures."
    - "No colour literal remains at any drawing site in _draw_radial_mode, _get_band_colour or _get_shift_cue."
    - "Palette is frozen — a drawing path cannot mutate it."
    - "No automatic switching exists."

implementation:
  implementation_steps:
    - step: "Add the Palette dataclass and the two instances, DAY_PALETTE carrying today's values exactly."
      owner: "Claude Code"
    - step: "Route every drawing site through self._palette."
      owner: "Claude Code"
    - step: "Add the double-tap toggle, its RADIAL gate and the transient confirmation."
      owner: "Claude Code"
    - step: "Persist and restore the selection."
      owner: "Claude Code"
    - step: "Compile check, the colour computations, and the existing suite."
      owner: "Claude Code"
    - step: "Observe both palettes on gtach.local, at night and in daylight, and confirm every band remains identifiable in night mode."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the fixed
    palette. A config.yaml carrying the palette key remains valid — the
    reverted _load_config ignores unknown keys.
  deployment_notes: >
    Day mode is visually identical to the previous build, so an operator
    who never toggles sees no change. Ships in v0.4.0 (ai/task.md §8.5),
    after 5014040c and b02ed4ea within that release. The release notes
    must document the double-tap, since it is the change's one
    discoverability weakness.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5014040c"
      relationship: "blocked_by"
    - change_ref: "change-b02ed4ea"
      relationship: "blocked_by"
    - change_ref: "change-821919ce"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-5012004e"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-5012004e."
      - "Answers ai/task.md §7.3.14's two questions: the toggle is a double-tap on the gauge face, not an options-menu item, because b02ed4ea's three-control budget is full; and the state persists in config.yaml."
      - "Recorded the options menu as the preferred long-term home once display report §7.7 frees a slot, and the gesture as an interim siting with a stated discoverability weakness."
      - "Recorded that the night palette is authored per colour rather than derived by scaling, because scaling compresses the band colours toward each other and the band cue is the primary signal."
      - "Recorded DAY_PALETTE as carrying today's values exactly, so day rendering is provably unchanged."

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
| 1.0 | 2026-08-04 | Initial change document coupled to issue-5012004e. Specifies the Palette dataclass, the day and night instances, the double-tap toggle and its siting rationale, and persistence through config.yaml. |

---

Copyright (c) 2026 William Watson. MIT License.
