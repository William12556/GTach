Created: 2026 July 30

# Issue: RPM Signal Conditioning — Band Thrash, Value Churn, Unstable Flash Phase, Blue Band Contrast

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-4c038bed"
  title: "Unconditioned RPM signal drives band thrash, displayed-value churn and an unstable flash duty cycle; blue band text fails contrast"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-4c038bed"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Recommendation 1 (§9.1) addressing findings §4.2 and §4.3;
    recommendation 5 (§9.1) addressing finding §4.4;
    recommendation 23 (§9.5) addressing finding §7.1.
    Task list reference: ai/task.md §7.3.1.

affected_scope:
  components:
    - name: "DisplayManager._get_band_colour"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._get_shift_cue"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_digital_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.2.64"

reproduction:
  prerequisites: >
    GTach running on gtach.local (Raspberry Pi Zero 2W, HyperPixel 2.1 Round)
    with a live OBD-II source, or with simulation mode enabled from the
    OPTIONS screen.
  steps:
    - "Enter DIGITAL mode."
    - "Hold engine RPM steady near a band boundary — torque_start = 3000 is the most accessible."
    - "Observe the full-field background alternating between blue and green."
    - "Hold RPM steady near a 100 RPM rounding boundary, for example 3050."
    - "Observe the leading numeral alternating between 3.0 and 3.1."
    - "Enter RADIAL mode and raise RPM above caution_start = 4500."
    - "Observe the centre disc flash; note that the on and off intervals are visibly unequal."
    - "Return to DIGITAL mode and hold RPM between idle_max = 999 and torque_start = 3000 so the blue band is active. Attempt to read the numeral."
  frequency: "always"
  reproducibility_conditions: >
    Band thrash and value churn require the RPM to sit within the sample
    noise band of a threshold; they are continuous under simulation mode,
    which sweeps 3000 + 3000·sin(t) through every boundary once per 6.28 s.
    The unstable flash duty cycle and the blue-band contrast failure are
    present unconditionally whenever their respective states are entered.
  preconditions: >
    OBD poll interval 0.02 s or 0.05 s (app.py), giving an effective RPM
    sample rate of 20-50 Hz. Frame target 60 Hz (config.yaml fps_limit).
  test_data: >
    Simulation mode synthetic source: rpm = int(3000 + 3000 * math.sin(time.time()))
    at manager.py:617 (DIGITAL) and manager.py:689 (RADIAL).
  error_output: "None. No exception is raised; the faults are visual."

behavior:
  expected: >
    The displayed RPM figure, the selected band, and the shift-cue flash
    phase are all stable when the engine is running at a steady speed. Text
    is legible against every band background.
  actual: >
    Four distinct faults in the value-to-pixels path.

    (a) Band thrash. _get_band_colour (manager.py:540-579) maps RPM to a
    full-screen background colour through hard thresholds with no
    hysteresis, and _draw_digital_mode fills the entire 480x480 viewport
    with that colour (manager.py:641-646). Samples straddling a threshold
    alternate the whole field between two saturated colours at up to 50 Hz.
    Perceptually this is a full-field flash, not a colour change. The
    mechanism applies at all five band boundaries.

    (b) Displayed value churn. _draw_digital_mode formats the value as
    f"{rpm/1000:.1f}" (manager.py:662). Displayed resolution is 100 RPM
    against a source resolution of 0.25 RPM. Near a rounding boundary the
    numeral, rendered at 180 px, alternates at the sample rate. There is no
    smoothing, deadband or update-rate limit anywhere in the path.

    (c) Unstable flash duty cycle. _get_shift_cue derives the flash phase
    from int(time.monotonic() * 2) % 2 == 0 (manager.py:595). The phase is
    computed from wall-clock time and sampled at an irregular frame rate,
    so the realised on and off intervals are unequal and vary frame to
    frame. The flash itself is intended behaviour; its instability is not.

    (d) Blue band contrast failure. _get_band_colour pairs background
    (0,0,255) with text (0,0,0) for the torque-approach band
    (manager.py:558-560). The computed WCAG 2.1 contrast ratio is 2.44:1,
    below the 3:1 large-text minimum. Pure blue has relative luminance
    0.0722, close to black. White text on the same blue yields 8.59:1.
  impact: >
    Faults (a) and (b) are the two highest-confidence candidate causes of
    the flicker reported on target hardware, and the report identifies this
    work as the item to implement and observe first: it is the cheapest
    change, confined to one file, and resolves the symptom outright if the
    cause is band thrash rather than tearing. Fault (d) makes the
    torque-approach band effectively unreadable in normal driving.
  workaround: >
    None. Avoiding steady operation near a band threshold is not a
    controllable condition in vehicle use.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    The RPM value travels from the OBD queue to the renderer with no
    conditioning stage. Every consumer — band selection, numeral
    formatting, radial arc extent — reads the same raw instantaneous
    sample. Band selection additionally uses bare inequality tests against
    fixed thresholds, which is unconditionally unstable for any signal with
    noise amplitude comparable to the distance from a threshold. The flash
    phase reads a clock that is independent of the frame cadence, so the
    sampled phase aliases against the frame rate. The blue-band text colour
    is an independent constant-selection error.
  technical_notes: >
    Recommendation 1 suggests an exponential moving average with tau of
    approximately 150 ms for the displayed figure and plus or minus 75 RPM
    hysteresis on band transitions. At a 20-50 Hz sample rate, tau = 150 ms
    corresponds to alpha in the range 0.12 to 0.30 depending on the
    realised interval; the smoothing coefficient should be derived from the
    measured inter-sample interval rather than assumed, or the filter
    applied per frame at the known frame interval.

    Hysteresis of plus or minus 75 RPM is smaller than the narrowest band
    gap in the default RPMBands (danger_start 5800 minus warning_start 5500
    = 300 RPM), so a symmetric band cannot span two thresholds.

    Recommendation 5 requires the flash phase to derive from a monotonic
    frame counter rather than wall-clock time so that the duty cycle is
    stable by construction.

    The conditioned value must not be substituted for the raw value in the
    OBD or logging paths; the conditioning is a display concern only.
  related_issues:
    - issue_ref: "issue-66ef59a0"
      relationship: "related"
    - issue_ref: "issue-49b21ace"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Introduce a display-side signal conditioning stage in manager.py: an
    exponential moving average on the displayed figure, directional
    hysteresis on band transitions, a frame-counter-derived flash phase,
    and correction of the blue band's text colour to white. See
    change-4c038bed.
  change_ref: "change-4c038bed"
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
    Any future threshold-driven visual state should be specified with an
    explicit hysteresis margin at design time. Any value rendered at a
    coarser resolution than its source should carry a stated smoothing or
    deadband policy.
  process_improvements: >
    Contrast ratios for new background and foreground colour pairs should
    be computed against the WCAG 2.1 relative-luminance definition before
    the pair is committed, not discovered in review.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "Enable simulation mode. The synthetic sweep crosses every band boundary once per 6.28 s. Confirm that band transitions occur once per crossing and do not oscillate."
    - "With simulation mode active, confirm the DIGITAL numeral advances monotonically through the sweep with no back-and-forth alternation at rounding boundaries."
    - "Above caution_start, time the shift-cue flash over 10 seconds and confirm the on and off intervals are equal to within one frame period."
    - "Hold RPM in the torque-approach band and confirm the numeral renders white on blue."
    - "Confirm that the RPM value written to the log and consumed by comm/obd.py is unchanged — conditioning is display-side only."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-4c038bed"
  test_refs: []

notes: >
  This is task 7.3.1 in ai/task.md §7.3 and the first item in the
  recommended authoring order (§7.6.2). Report finding §7.2 proposes
  replacing the full-field band colour with an annular indicator
  (recommendation 26, task 7.3.11). If that is implemented, the
  white-on-blue correction made here is superseded for the main readout;
  the hysteresis and smoothing are not, and remain required. Recorded in
  ai/task.md §7.6.1 as a dependency of 7.3.11 on this task.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial issue document from display-ui-graphics-review.md recommendations 1, 5 and 23."

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
| 1.0 | 2026-07-30 | Initial issue document from display-ui-graphics-review.md recommendations 1, 5 and 23. |

---

Copyright (c) 2026 William Watson. MIT License.
