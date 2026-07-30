Created: 2026 July 30

# Change: RPM Signal Conditioning for the Display Path

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-4c038bed"
  title: "Add display-side RPM smoothing and band hysteresis; derive flash phase from a frame counter; correct blue band text colour"
  date: "2026-07-30"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-4c038bed"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-4c038bed"
  description: >
    Resolves issue-4c038bed. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 recommendations
    1, 5 and 23. Task list reference ai/task.md §7.3.1.

scope:
  summary: >
    Insert a conditioning stage between the raw RPM sample and every
    display consumer in DisplayManager. Four coordinated edits, all in
    src/gtach/display/manager.py: an exponential moving average on the
    displayed figure; directional hysteresis on band selection; a
    frame-counter-derived shift-cue flash phase; and correction of the
    torque-approach band's text colour from black to white.
  affected_components:
    - name: "DisplayManager.__init__"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._condition_rpm"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "DisplayManager._get_band_colour"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._get_shift_cue"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_digital_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any change to comm/obd.py, app.py, or the OBD poll rate. The raw sample rate is not altered."
    - "Any change to the value logged or reported through get_status(). Conditioning is display-side only."
    - "The framebuffer write path (engine.py). Recommendations 2, 3, 4, 6, 7 and 8 are tasks 7.3.2 and 7.3.4."
    - "Replacing the full-field band colour with an annular indicator. That is recommendation 26, task 7.3.11."
    - "Reducing fps_limit or skipping unchanged frames. Those are recommendations 12 and 13, task 7.3.6."
    - "Adding a night palette. That is recommendation 29, task 7.3.12."

rational:
  problem_statement: >
    The RPM value reaches the renderer unconditioned. Band selection uses
    bare threshold comparisons, so a signal sitting within its own noise
    amplitude of a threshold alternates the full-field background between
    two saturated colours at up to 50 Hz. The displayed numeral is
    quantised to 100 RPM from a 0.25 RPM source with no deadband, so it
    alternates at rounding boundaries. The shift-cue flash phase is read
    from wall-clock time and sampled at an irregular frame rate, producing
    an unstable duty cycle. Separately, the torque-approach band pairs pure
    blue with black text at a 2.44:1 contrast ratio, below the WCAG 2.1
    large-text minimum of 3:1.
  proposed_solution: >
    Add a single conditioning function that both render paths call once per
    frame, returning the smoothed value used for display. Apply band
    hysteresis by making the active band sticky: a transition occurs only
    when the conditioned value passes the threshold by the hysteresis
    margin in the direction of travel. Replace the wall-clock flash phase
    with a phase derived from the display loop's own frame counter.
    Change the torque-approach band's text colour constant to (255,255,255).
  alternatives_considered:
    - option: "Apply the smoothing in comm/obd.py, at the source."
      reason_rejected: >
        The raw value is the correct record for logging and for any future
        consumer. Conditioning is a presentation decision and belongs in
        the presentation layer. Filtering at source would also make the
        logged value unusable as ground truth during the flicker
        investigation.
    - option: "Increase the displayed resolution to 10 RPM to remove the rounding boundary."
      reason_rejected: >
        This makes churn worse, not better — a finer quantum crosses more
        boundaries per unit of noise. It also does not address band thrash.
    - option: "Rate-limit the display update instead of smoothing the value."
      reason_rejected: >
        A rate limit alone still alternates, only more slowly, which is
        more visible rather than less. Smoothing removes the alternation;
        rate limiting merely reduces its frequency.
    - option: "Apply hysteresis only at torque_start, the boundary most often held."
      reason_rejected: >
        The mechanism is identical at all five boundaries. A partial fix
        leaves four reproductions in place and complicates the observation
        planned in ai/task.md §7.5.2.
  benefits:
    - "Removes the two highest-confidence candidate causes of the reported flicker, at low risk and in a single file."
    - "Establishes whether the residual symptom is tearing (report §4.1) before any framebuffer change is attempted, which is the sequencing the report requests."
    - "Stabilises the shift-cue duty cycle so the deliberate flash is no longer confusable with a fault."
    - "Raises the torque-approach band's text contrast from 2.44:1 to 8.59:1."
  risks:
    - risk: >
        Smoothing introduces display lag. An EMA with tau of 150 ms delays
        the displayed figure by approximately that time constant, which is
        material for a shift cue.
      mitigation: >
        Apply the EMA to the displayed numeral only. Band selection and the
        shift cue read the conditioned value but with hysteresis rather
        than a time constant, so the transition into the caution band is
        not delayed by the filter. State the realised lag in the T06 result
        so it can be judged against observed behaviour on the vehicle.
    - risk: >
        Hysteresis can hide a genuine band transition if the margin exceeds
        the band width.
      mitigation: >
        The margin is plus or minus 75 RPM. The narrowest default band gap
        is 300 RPM (danger_start 5800 minus warning_start 5500), so a
        symmetric band cannot span two thresholds. The implementation must
        clamp the margin to less than half the narrowest adjacent gap if
        RPMBands is later configured with closer thresholds.
    - risk: >
        A frame-counter-derived flash phase changes rate if fps_limit
        changes, which task 7.3.6 (recommendation 12) proposes to do.
      mitigation: >
        Derive the phase from the frame counter and the configured
        fps_limit together so the realised flash rate stays at 2 Hz
        independent of frame rate. Recorded as a dependency of 7.3.6 on
        this task in ai/task.md §7.6.1.

technical_details:
  current_behavior: >
    _draw_digital_mode (manager.py:612) and _draw_radial_mode
    (manager.py:684) each drain the OBD message queue to self._last_rpm and
    read it raw. _get_band_colour (manager.py:540-579) returns a
    (bg_colour, text_colour) pair selected by five bare inequality tests
    against RPMBands, with (0,0,255) paired with (0,0,0) for the
    torque-approach band. _get_shift_cue (manager.py:581) computes
    flash = int(time.monotonic() * 2) % 2 == 0 at manager.py:595. The
    numeral is formatted f"{rpm/1000:.1f}" at manager.py:662.
  proposed_behavior: >
    Both render paths call a new _condition_rpm(raw) once per frame and use
    its return value for display. _get_band_colour selects the band via a
    sticky comparison against the previously active band with a plus or
    minus 75 RPM margin, and returns white text for the torque-approach
    band. _get_shift_cue derives its flash phase from the display loop's
    frame counter scaled to a 2 Hz rate, giving equal on and off intervals
    by construction.
  implementation_approach: >
    Five edits, all in src/gtach/display/manager.py.

    EDIT 1 — DisplayManager.__init__. Add conditioning state alongside the
    existing display state:
      self._rpm_display = 0.0        # EMA output, displayed figure
      self._rpm_ema_tau = 0.150      # seconds
      self._active_band = 0          # index into the band table, sticky
      self._band_hysteresis = 75.0   # RPM
      self._frame_counter = 0        # monotonic, incremented per frame

    EDIT 2 — add DisplayManager._condition_rpm(self, raw: float) -> float
    immediately before _get_band_colour. Implements a first-order EMA over
    the actual inter-frame interval:
      alpha = 1.0 - math.exp(-dt / self._rpm_ema_tau)
      self._rpm_display += alpha * (raw - self._rpm_display)
    where dt is the measured interval since the previous call, obtained
    from time.monotonic() and clamped to a sane range (for example 0.001
    to 0.5 s) so a stalled frame does not produce a step. Deriving alpha
    from the measured dt rather than assuming a fixed frame rate keeps the
    time constant correct when fps_limit changes. Guard the first call:
    seed _rpm_display with raw rather than filtering from zero. Wrap in
    try/except and return raw on error so a conditioning fault degrades to
    the present behaviour rather than blanking the display.

    EDIT 3 — _get_band_colour. Replace the five-way if/elif chain with a
    band table and a sticky selection. The band index changes from the
    current _active_band only when the value passes the relevant threshold
    by _band_hysteresis in the direction of travel: to move up a band the
    value must exceed the upper threshold plus the margin; to move down it
    must fall below the lower threshold minus the margin. Clamp the
    effective margin to less than half the narrowest adjacent gap in the
    live RPMBands so a narrow configuration cannot deadlock the selection.
    Change the torque-approach band's text colour from (0,0,0) to
    (255,255,255). Retain the existing except clause and its
    ((0,0,0),(255,255,255)) fallback.

    EDIT 4 — _get_shift_cue. Replace
      flash = int(time.monotonic() * 2) % 2 == 0
    with a phase derived from the frame counter and the configured frame
    rate, so that the flash completes one full cycle every
    self.config.fps_limit / 2 frames and the on and off halves contain an
    equal number of frames. Leave the returned colours, border width and
    threshold logic unchanged.

    EDIT 5 — _display_loop and the two render paths. Increment
    self._frame_counter once per iteration of the display loop
    (manager.py:397-456), at the same point the heartbeat is updated. In
    _draw_digital_mode and _draw_radial_mode, after the queue drain sets
    self._last_rpm, pass the raw value through _condition_rpm and use the
    returned value for the numeral, the band selection and the shift cue.
    Do not alter self._last_rpm itself — it remains the raw record.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Add conditioning state to __init__; add _condition_rpm; rewrite
        _get_band_colour band selection with hysteresis and correct the
        blue band text colour; rewrite the _get_shift_cue flash phase;
        increment a frame counter in _display_loop; route both render paths
        through the conditioner.
      functions_affected:
        - "__init__"
        - "_condition_rpm"
        - "_get_band_colour"
        - "_get_shift_cue"
        - "_draw_digital_mode"
        - "_draw_radial_mode"
        - "_display_loop"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes:
    - interface: "DisplayManager._get_band_colour(rpm)"
      change_type: "contract"
      details: >
        Signature and return type are unchanged: (bg_colour, text_colour).
        The function becomes stateful — its result now depends on the
        previously selected band as well as the argument. Callers must
        therefore invoke it exactly once per frame. Both existing callers
        (_draw_digital_mode at manager.py:633 and the radial path) already
        satisfy this.
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "display/models.py RPMBands"
      impact: "Read only. Thresholds and their spacing constrain the hysteresis margin clamp. No change to the dataclass."
    - component: "display/models.py DisplayConfig.fps_limit"
      impact: "Read by the flash-phase calculation. No change to the dataclass."
  external: []
  required_changes:
    - change_ref: "change-9ed1c77e"
      relationship: "blocks"
    - change_ref: "change-821919ce"
      relationship: "blocks"
    - change_ref: "change-5014040c"
      relationship: "blocks"

testing_requirements:
  test_approach: >
    Unit tests on the development platform with the OBD source mocked,
    plus a simulation-mode observation on the target. Unit tests exercise
    _condition_rpm and the band selection directly; they do not require
    pygame surfaces.
  test_cases:
    - scenario: "Feed _condition_rpm a step from 0 to 3000 at a fixed 60 Hz dt."
      expected_result: "Output reaches 63% of the step within 150 ms plus or minus one frame, and converges monotonically."
    - scenario: "Feed alternating samples 2998 / 3002 through band selection starting from the idle-approach band."
      expected_result: "The active band does not change. No transition occurs until the value exceeds 3075."
    - scenario: "Sweep the value from 2900 up to 3200 then back down to 2900."
      expected_result: "One upward transition at 3075 and one downward transition at 2925. Exactly two transitions total."
    - scenario: "Request the band colour pair for a value in the torque-approach band."
      expected_result: "Returns ((0,0,255), (255,255,255))."
    - scenario: "Advance the frame counter through 240 frames at fps_limit = 60 and record the flash boolean."
      expected_result: "Eight complete flash cycles, each with exactly 15 frames on and 15 frames off."
    - scenario: "Set fps_limit to 30 and repeat the previous case over 120 frames."
      expected_result: "Still eight complete cycles at 2 Hz, each with 7 or 8 frames on and the same number off."
    - scenario: "Configure RPMBands with adjacent thresholds 100 RPM apart and select bands across that pair."
      expected_result: "The hysteresis margin is clamped below 50 RPM and both transitions remain reachable."
    - scenario: "Call _condition_rpm with a non-numeric value."
      expected_result: "Returns the argument unchanged and logs at ERROR with exc_info; the display does not blank."
  regression_scope:
    - "tests/display/ — full existing display suite."
    - "Manual: SPLASH, OPTIONS, DISCONNECTED and ACKNOWLEDGEMENT screens render unchanged."
    - "Manual: RADIAL arc extent tracks the conditioned value smoothly with no visible stepping."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "pytest tests/ passes with no new failures."
    - "self._last_rpm continues to hold the raw value; no logged or reported RPM figure changes."
    - "In simulation mode the synthetic sweep produces exactly one band transition per boundary crossing."

implementation:
  implementation_steps:
    - step: "EDIT 1 — add conditioning state to DisplayManager.__init__."
      owner: "Claude Code"
    - step: "EDIT 2 — add _condition_rpm."
      owner: "Claude Code"
    - step: "EDIT 3 — rewrite _get_band_colour selection; correct the blue band text colour."
      owner: "Claude Code"
    - step: "EDIT 4 — rewrite the _get_shift_cue flash phase."
      owner: "Claude Code"
    - step: "EDIT 5 — increment the frame counter and route both render paths through the conditioner."
      owner: "Claude Code"
    - step: "Compile check and run the existing test suite."
      owner: "Claude Code"
    - step: "Observe on gtach.local in simulation mode per ai/task.md §7.5.2."
      owner: "William Watson"
  rollback_procedure: >
    Single file, single commit. git revert of the implementing commit
    restores the previous behaviour. No data, configuration or interface
    migration is involved.
  deployment_notes: >
    No configuration change. The tau and hysteresis values are module
    constants in this iteration; if observation on the vehicle indicates
    they need tuning, promoting them to config.yaml is a separate change.

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
    - change_ref: "change-9ed1c77e"
      relationship: "blocks"
    - change_ref: "change-5014040c"
      relationship: "blocks"
  related_issues:
    - issue_ref: "issue-4c038bed"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-4c038bed."

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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-4c038bed. |

---

Copyright (c) 2026 William Watson. MIT License.
