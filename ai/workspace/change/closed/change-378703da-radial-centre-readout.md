Created: 2026 August 04

# Change: Put the Number in the Centre of the Gauge and Retire DIGITAL

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-378703da"
  title: "The RADIAL centre disc renders the conditioned RPM in place of the brand string; DisplayMode.DIGITAL, _draw_digital_mode, the two swipe handlers and _render_mode_selector are removed, with a read-side migration for persisted DIGITAL values"
  date: "2026-08-04"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-378703da"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-378703da"
  description: >
    Resolves issue-378703da. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 findings §7.5
    and §7.6 with §9.5 recommendation 25, scoped to the directed
    decision in ai/task.md §7.3.14. Task list reference ai/task.md
    §7.3.10.

scope:
  summary: >
    RADIAL becomes the only normal display mode and gains the numeric
    readout it lacked. DIGITAL and the machinery that existed to reach
    it are removed. Persisted or defaulted DIGITAL values are mapped to
    RADIAL on read, so no installed system fails to start.
  affected_components:
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_digital_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "remove"
    - name: "DisplayManager._handle_swipe_left"
      file_path: "src/gtach/display/manager.py"
      change_type: "remove"
    - name: "DisplayManager._handle_swipe_right"
      file_path: "src/gtach/display/manager.py"
      change_type: "remove"
    - name: "DisplayManager._render_mode_selector"
      file_path: "src/gtach/display/manager.py"
      change_type: "remove"
    - name: "DisplayManager._setup_touch_callbacks"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._handle_long_press"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._render_normal_modes"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._load_config"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayMode"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "DisplayConfig.from_dict"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
    - name: "display.mode"
      file_path: "config/config.yaml"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "_get_band_colour (manager.py:616-678). RETAINED though it becomes uncalled by this change. Task 7.3.11 (5014040c) requires its hysteresis-bearing band selection for the annular indicator. Deleting and reinstating it would discard the logic 4c038bed added."
    - "_condition_rpm (manager.py:581-614) and _get_shift_cue (manager.py:680-713). Unmodified."
    - "The touch subsystem's swipe gesture detection. Only DisplayManager's two handlers and their registration are removed; the gestures remain available and are used by the setup subsystem."
    - "DisplayMode.SPLASH, OPTIONS and ACKNOWLEDGEMENT, and the DISCONNECTED derived condition. Unmodified."
    - "The annular band indicator (7.3.11) and the night palette (7.3.12). Separate triples; both touch _draw_radial_mode and are written against this change."
    - "Render caching (7.3.5). The centre disc and its label are already classified as varying content by display report §5.3, so this change creates no cache-key obligation."
    - "_register_rpm_sliders, _render_slider_visuals and _register_save_button (manager.py:1463, 1489, 1519). Also unreachable, but not named by recommendation 25. Their removal is a separate dead-code question."
    - "TypographyConstants.FONT_RPM_LARGE (180 px). It was DIGITAL's numeral size; retained because the constant is harmless and removing it exceeds this scope."

rational:
  problem_statement: >
    RADIAL is the default mode and does not show the number. Its centre
    disc — 13.4% of the field, at the point of highest visual acuity —
    shows the fixed string 'GTach'. The number is available only in
    DIGITAL, which is reachable only by an unadvertised swipe, and
    which the operator is silently returned to every time they leave
    the options screen. Two modes are maintained where one, with the
    numeral added, is a superset of both.
  proposed_solution: >
    Render the conditioned RPM in the centre disc, making RADIAL a
    superset of DIGITAL, then remove DIGITAL and the reachability
    machinery that existed only to serve it. Map persisted DIGITAL to
    RADIAL on read rather than rewriting configuration files.
  alternatives_considered:
    - option: "Add the numeral to RADIAL and keep DIGITAL, adding the mode indicator display report §7.6 offers as its second resolution."
      reason_rejected: >
        This is the report's own alternative and it was considered at
        the task-list level rather than here: ai/task.md §7.3.14 records
        the decision to retire. Retention would mean maintaining two
        modes where one is a strict superset, and adding an indicator
        to advertise a mode that offers strictly less information.
    - option: "Retire DIGITAL but leave DisplayMode.DIGITAL in the enum as an accepted alias for RADIAL."
      reason_rejected: >
        Cheaper — no migration, no enum change — but it leaves a member
        that means something different from its name and that a future
        author may branch on. The migration is a handful of lines on
        the read path and is done once. Rejected in favour of removing
        the member outright.
    - option: "Rewrite config.yaml on load to replace DIGITAL with RADIAL."
      reason_rejected: >
        Writing to the operator's configuration during a read is a side
        effect that surprises, and it fails on a read-only filesystem.
        _save_config already writes the current mode on the ordinary
        path, so a migrated value persists at the next save without
        anything special being done.
    - option: "Keep the numeral out of the centre and place it below the gauge."
      reason_rejected: >
        The centre disc is the largest uninterrupted region and the one
        the eye is already on. TypographyConstants.FONT_RPM_MEDIUM
        (typography.py:80) was declared for exactly this and annotated
        'Gauge mode center readout'. Placing the numeral elsewhere
        would overlap the tick numerals or the inert bottom arc.
  benefits:
    - "The primary quantity appears in the primary mode, at the point of highest acuity."
    - "One normal display mode instead of two: less to render, test, document and explain."
    - "The operator is no longer switched between modes without asking, which the OPTIONS-exit path did on every visit."
    - "Roughly 70 lines of unreachable code removed (_draw_digital_mode, two handlers, _render_mode_selector)."
  risks:
    - risk: >
        The numeral must remain legible against every centre-disc
        colour _get_shift_cue returns, including the flashing
        (10, 10, 10) dark variant and the (0, 160, 0) green.
      mitigation: >
        White is used, as the existing 'GTach' label already is
        (manager.py:983). Contrast against the four possible fills is
        computed in the prompt and asserted in the tests, rather than
        assumed from the fact that the current label is white.
    - risk: >
        An installed system carrying mode: DIGITAL fails to start after
        the enum member is removed, because DisplayMode['DIGITAL']
        raises KeyError.
      mitigation: >
        manager.py:284-286 already catches KeyError from that lookup and
        falls back to RADIAL with a warning. The migration adds an
        explicit DIGITAL branch ahead of it so the fallback is a
        deliberate mapping with an informative log line rather than an
        incidental rescue. Both paths are tested.
    - risk: >
        Removing the swipe handlers removes the only consumer of the
        gesture registration in _setup_touch_callbacks, and an
        over-broad edit could remove the long-press registration with
        them — which would strand the operator with no route to OPTIONS.
      mitigation: >
        The long-press registration is explicitly out of scope and its
        survival is a success criterion. This is the single most
        dangerous edit in the change and is called out as such in the
        prompt.
    - risk: >
        _get_band_colour becomes uncalled and a subsequent dead-code
        sweep removes it correctly, discarding 4c038bed's hysteresis
        before 7.3.11 can use it.
      mitigation: >
        Retention is recorded in scope.out_of_scope, in the issue's
        prevention section, and as a comment on the method itself. The
        durable mitigation is to sequence 7.3.11 immediately after this
        triple, which ai/task.md §7.6.2 step 9 already implies.
  benefits_measurement: >
    Normal display modes: 2 -> 1. Unreachable methods in manager.py:
    4 -> 1 (the slider and save-button registrations remain, out of
    scope). Numeric readout available in the default mode: no -> yes.

technical_details:
  current_behavior: >
    _render_normal_modes (manager.py:539-560) dispatches DIGITAL to
    _draw_digital_mode (715-786) and RADIAL to _draw_radial_mode
    (788-990). The RADIAL centre disc is filled from _get_shift_cue at
    975-977 and labelled 'GTach' at 980-985. The two modes are
    exchanged by _handle_swipe_left (167-181) and _handle_swipe_right
    (183-197), registered in _setup_touch_callbacks (150-166).
    _handle_long_press sets DIGITAL when leaving OPTIONS (204).
    _render_mode_selector (1423-1461) is defined and never called.
    _load_config reads the mode at 275-286 with a RADIAL default and a
    KeyError fallback; utils/config.py:588 defaults to the string
    'DIGITAL'; config/config.yaml carries display.mode: DIGITAL.
  proposed_behavior: >
    _render_normal_modes dispatches RADIAL, OPTIONS, ACKNOWLEDGEMENT
    and the DISCONNECTED condition only. The RADIAL centre disc renders
    the conditioned RPM as a numeral. DIGITAL does not exist as an enum
    member; a persisted DIGITAL maps to RADIAL on read with a log line.
    Leaving OPTIONS returns to RADIAL.
  implementation_approach: >
    Six edits, in an order chosen so the tree compiles between steps.

    STEP 1 — add the numeral to _draw_radial_mode before removing
    anything, so RADIAL is a superset before DIGITAL goes. Replace the
    'GTach' render at manager.py:980-985 with the RPM numeral, using
    the same format DIGITAL used — f"{rpm/1000:.1f}" — at a size that
    fits the r=99 disc. Retain white.

    STEP 2 — remove _draw_digital_mode and its dispatch arm in
    _render_normal_modes.

    STEP 3 — remove _handle_swipe_left, _handle_swipe_right and their
    two registrations in _setup_touch_callbacks. Leave every other
    registration in that method untouched, the long press above all.

    STEP 4 — remove _render_mode_selector.

    STEP 5 — change _handle_long_press's OPTIONS-exit assignment from
    DIGITAL to RADIAL.

    STEP 6 — the migration. Remove DIGITAL from DisplayMode; add the
    explicit branch in _load_config; change utils/config.py:588's
    default; change config/config.yaml.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Centre disc renders the RPM numeral. _draw_digital_mode, both
        swipe handlers and _render_mode_selector removed, with their
        registrations and dispatch arms. Long-press OPTIONS exit
        returns RADIAL. _load_config maps DIGITAL to RADIAL explicitly.
      functions_affected:
        - "_draw_radial_mode"
        - "_draw_digital_mode"
        - "_handle_swipe_left"
        - "_handle_swipe_right"
        - "_render_mode_selector"
        - "_setup_touch_callbacks"
        - "_handle_long_press"
        - "_render_normal_modes"
        - "_load_config"
      classes_affected:
        - "DisplayManager"
    - component: "DisplayMode"
      file: "src/gtach/display/models.py"
      change_summary: "DIGITAL removed from the enum."
      classes_affected:
        - "DisplayMode"
    - component: "DisplayConfig.from_dict"
      file: "src/gtach/utils/config.py"
      change_summary: "The 'DIGITAL' string default becomes 'RADIAL'."
      functions_affected:
        - "from_dict"
  data_changes:
    - "config/config.yaml display.mode changes from DIGITAL to RADIAL. Existing deployed configuration files are NOT rewritten; a DIGITAL value found on disk is mapped on read."
  interface_changes:
    - "DisplayMode loses its DIGITAL member. Any external consumer branching on it would break; there is none in src/gtach outside the sites listed above."

dependencies:
  internal:
    - component: "_get_band_colour — manager.py:616"
      impact: "Becomes uncalled. Retained deliberately for 7.3.11."
    - component: "_get_shift_cue — manager.py:680"
      impact: "Still supplies the centre-disc fill the numeral is drawn on. Unmodified."
    - component: "_condition_rpm — manager.py:581"
      impact: "Supplies the value rendered. Unmodified."
    - component: "_current_view_key — manager.py:1002"
      impact: "Includes self.config.mode. One fewer possible value; no structural change."
    - component: "_save_config — manager.py:342"
      impact: "Its transient-mode list is unchanged. A migrated RADIAL persists at the next ordinary save."
  external: []
  required_changes:
    - change_ref: "change-5014040c"
      relationship: "blocks"
    - change_ref: "change-b02ed4ea"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with SDL_VIDEODRIVER=dummy and a mocked rendering engine,
    consistent with ai/task.md §8.2's DisplayManager target. Rendering
    is asserted by call inspection. The migration is tested against
    real YAML files in a temporary directory. Contrast figures are
    computed from the WCAG relative-luminance definition rather than
    asserted by eye.
  test_cases:
    - scenario: "_draw_radial_mode with a known RPM."
      expected_result: "render_text is called at the centre with the RPM formatted to one decimal in thousands, not with 'GTach'."
    - scenario: "Numeral colour against all four centre fills _get_shift_cue can return."
      expected_result: "White in every case; contrast computed and recorded for each."
    - scenario: "DisplayMode membership."
      expected_result: "No DIGITAL member; SPLASH, RADIAL, OPTIONS and ACKNOWLEDGEMENT present."
    - scenario: "grep for DisplayMode.DIGITAL across src/gtach."
      expected_result: "No occurrence."
    - scenario: "_load_config against a config.yaml carrying mode: DIGITAL."
      expected_result: "RADIAL, with a log line naming the migration. No exception."
    - scenario: "_load_config against mode: NONSENSE."
      expected_result: "RADIAL with the existing unknown-mode warning, unchanged from today."
    - scenario: "_load_config against mode: RADIAL, and against a missing file."
      expected_result: "RADIAL in both cases, unchanged from today."
    - scenario: "_load_config against mode: OPTIONS."
      expected_result: "RADIAL — the transient-mode rejection at manager.py:281-283 is unaffected."
    - scenario: "_handle_long_press entering OPTIONS from RADIAL, then leaving."
      expected_result: "RADIAL on exit."
    - scenario: "_setup_touch_callbacks after the change."
      expected_result: "The long-press callback is registered; neither swipe handler is."
    - scenario: "Every callback _setup_touch_callbacks registered before the change except the two swipe handlers."
      expected_result: "Still registered, asserted individually rather than by count."
    - scenario: "_render_normal_modes with each surviving mode."
      expected_result: "Correct dispatch; no branch references DIGITAL."
    - scenario: "_get_band_colour."
      expected_result: "Present, unmodified, and carrying the retention comment."
    - scenario: "DisplayConfig.from_dict with no mode key."
      expected_result: "'RADIAL'."
  regression_scope:
    - "tests/display/ — the display suite once populated per ai/task.md §8.2."
    - "On gtach.local: the application starts against the pre-upgrade config.yaml, which carries DIGITAL."
    - "On gtach.local: the numeral is legible in daylight and while the centre disc flashes above caution_start."
    - "On gtach.local: long press still reaches OPTIONS and returns to RADIAL."
    - "On gtach.local: a horizontal swipe does nothing and does not raise."
  validation_criteria:
    - "python -m py_compile on all four modified Python files passes."
    - "pytest tests/ passes with no new failures."
    - "grep 'DIGITAL' across src/gtach returns nothing."
    - "_get_band_colour is byte-identical to its current text apart from an added comment."
    - "The long-press registration in _setup_touch_callbacks is intact."

implementation:
  implementation_steps:
    - step: "Add the centre numeral to _draw_radial_mode."
      owner: "Claude Code"
    - step: "Remove _draw_digital_mode and its dispatch arm."
      owner: "Claude Code"
    - step: "Remove the two swipe handlers and their registrations, preserving every other registration."
      owner: "Claude Code"
    - step: "Remove _render_mode_selector."
      owner: "Claude Code"
    - step: "Change the long-press OPTIONS exit to RADIAL."
      owner: "Claude Code"
    - step: "Remove DisplayMode.DIGITAL; add the read-side migration; correct the two configuration defaults."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Deploy to gtach.local against the pre-upgrade configuration and confirm start, legibility and long-press navigation."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across four files. git revert restores DIGITAL and
    both modes. No configuration file is rewritten by this change, so a
    revert requires no data migration; a config.yaml already saved with
    RADIAL remains valid under the reverted code.
  deployment_notes: >
    The most visible change in v0.4.0. RADIAL is the only normal mode
    and shows the number; horizontal swipes no longer do anything. An
    operator who used DIGITAL will find the gauge in its place, with the
    numeral in the centre. Release notes must say so explicitly. Ships
    in v0.4.0 per ai/task.md §8.5.

verification:
  implemented_date: "2026-08-04"
  implemented_by: "Claude Code, per prompt-378703da (commit 7035a93)"
  verification_date: "2026-08-05"
  verified_by: "Claude Code (development-platform script); William Watson (gtach.local, sessions §9.9-§9.10)"
  test_results: >
    Delivered per implementation_approach, all six steps. Development-
    platform script confirmed enum membership, migration for a
    persisted and an unknown mode, numeral contrast, and byte-identity
    of _get_band_colour, _condition_rpm and _get_shift_cue. On-target
    session §9.9 found a defect outside this change's four-file scope
    (touch.py, navigation_gestures.py still referencing DisplayMode.
    DIGITAL, trapping the operator on OPTIONS); corrected under
    issue-7f2a9c04 and confirmed clean in session §9.10 (one ERROR in
    362 KB, no DIGITAL line). William confirmed 2026-08-07 that GTach
    functions correctly on gtach.local.
  issues_found:
    - "On-target: display/touch.py and display/navigation_gestures.py, both runtime-instantiated and outside this change's four-file scope, still referenced the removed DisplayMode.DIGITAL member, trapping the operator on the OPTIONS screen. Corrected under issue-7f2a9c04, confirmed on-target."
    - "Residual: utils/config.py's DisplayConfig dataclass field default and its legacy-INI-reader default both still read the literal 'DIGITAL' (config.py:552, 1344), missed by this change's own validation_criteria grep because it targets DisplayMode.DIGITAL usage, not this string default. Not on DisplayManager's own (confirmed-correct) config path. Flagged for a follow-up trivial fix."

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-5014040c"
      relationship: "blocks"
    - change_ref: "change-b02ed4ea"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-378703da"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-378703da, scoped to ai/task.md §7.3.14's directed decision to place the numeral in the centre disc and retire DIGITAL."
      - "Recorded _get_band_colour as retained despite becoming uncalled, for 7.3.11's benefit, with the sequencing mitigation that removes the window."
      - "Recorded the migration as read-side only: no configuration file is rewritten on load."
      - "Recorded the removal of the swipe registrations as the change's most dangerous edit, the long-press registration being adjacent and load-bearing."
      - "Recorded the ordering of the six steps as chosen so the tree compiles between them, RADIAL becoming a superset before DIGITAL is removed."

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
| 1.0 | 2026-08-04 | Initial change document coupled to issue-378703da. Specifies the centre readout, the removal of DIGITAL and its reachability machinery, the read-side migration, and the deliberate retention of `_get_band_colour` for 7.3.11. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation and verification recorded (commit 7035a93), including the on-target defect found and fixed under issue-7f2a9c04 and a residual config.py default flagged for follow-up. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
