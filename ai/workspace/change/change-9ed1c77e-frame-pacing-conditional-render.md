Created: 2026 August 04

# Change: Render When Something Changed, at a Rate Matched to the Data

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-9ed1c77e"
  title: "Three separately revertible parts: the per-frame import moves to module scope and the debug f-string is guarded; fps_limit falls to 30; a conditional render skips frames whose displayed state — including the shift-cue flash phase — is unchanged"
  date: "2026-08-04"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-9ed1c77e"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-9ed1c77e"
  description: >
    Resolves issue-9ed1c77e. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 findings
    §5.6, §5.7 and §4.5 with §9.2 recommendations 12, 13 and 14. Task
    list reference ai/task.md §7.3.6.

scope:
  summary: >
    Housekeeping, a configuration default, and a conditional render.
    Grouped by the task list; separated here into three parts with very
    different risk, each independently revertible.
  affected_components:
    - name: "DisplayManager (module imports)"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._frame_state_key"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
    - name: "display.fps_limit"
      file_path: "config/config.yaml"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "The static-layer cache and the text cache. Task 7.3.5 (821919ce), which this change depends on."
    - "The framebuffer write path. Changes 66ef59a0 and 49b21ace."
    - "The performance monitor. change-0b00759c owns it; this change must not alter what it measures, only how often a frame occurs."
    - "The flash's period or its derivation from the frame counter. change-4c038bed owns it; this change must preserve its wall-clock behaviour."
    - "The heartbeat, the shutdown check and the periodic performance log. They run on every loop iteration, skipped frame or not."
    - "The OBD poll interval at app.py:268."

rational:
  problem_statement: >
    fps_limit is 60 against a 20-50 Hz data rate; every frame is
    rendered whether or not anything changed; an import executes inside
    the render function each frame; and a debug f-string is formatted at
    60 Hz for a logger that discards it in production.
  proposed_solution: >
    Move the import, guard the logging call, halve the configured frame
    rate, and skip rendering when the displayed state is unchanged —
    with the flash phase in the state, because it changes the display
    when nothing else does.
  alternatives_considered:
    - option: "Implement all three recommendations as one change."
      reason_rejected: >
        They differ by an order of magnitude in risk. Recommendation 14
        cannot break anything; recommendation 13 changes when the
        instrument draws. A single commit means a problem with the
        conditional render forces the housekeeping to be reverted with
        it. Three commits, in ascending risk."
    - option: "Skip on quantised RPM, band and mode only, as the report states."
      reason_rejected: >
        This is the report's own condition and it is incomplete. The
        shift-cue flash alternates the centre disc between two colours
        on frames where RPM, band and mode are all identical
        (manager.py:694-703). Skipping those frames suppresses the
        flash above caution_start — the one moment the instrument most
        needs to be believed. The flash phase is a member of the skip
        condition."
    - option: "Advance the frame counter only on rendered frames."
      reason_rejected: >
        The flash phase derives from the counter, so a counter that
        advances only on rendered frames would slow the flash exactly
        when frames are being skipped. The counter advances on every
        loop iteration, and the flash phase is computed from it and
        compared — so a phase flip forces a render."
    - option: "Reduce fps_limit to 30 and stop there, without a conditional render."
      reason_rejected: >
        Legitimate and much cheaper, and it may prove sufficient. It is
        the recommended fallback if assumption A1 fails — see risks.
        Not taken as the primary because static screens would still
        redraw 30 times a second to no effect."
    - option: "Make the frame rate adaptive rather than fixed."
      reason_rejected: >
        More sophisticated and harder to reason about on a device whose
        timing already interacts with tearing (report §4.1) and with
        the OBD thread's GIL access. A binary skip is auditable; an
        adaptive rate is not."
  benefits:
    - "Static screens — DISCONNECTED, OPTIONS, ACKNOWLEDGEMENT — stop rendering entirely."
    - "Frame rate matched to a 20-50 Hz data rate, returning GIL time to the OBD thread."
    - "An import and two f-string formats removed from a 60 Hz path."
  risks:
    - risk: >
        THE FLASH. A skip condition omitting the flash phase suppresses
        the shift cue above caution_start.
      mitigation: >
        The flash phase is an explicit member of _frame_state_key, and
        the test that asserts it uses a perfectly static RPM above
        caution_start — the exact case a naive implementation passes
        every other test while failing."
    - risk: >
        ASSUMPTION A1 — that frame cost after change-821919ce is high
        enough for skipping to be worth its risk.
      mitigation: >
        Measure after 821919ce lands. If a RADIAL frame is a blit plus
        four primitives, take the fps_limit reduction alone and withdraw
        Part 3. This is a real possible outcome and is the reason the
        parts are separable."
    - risk: >
        ASSUMPTION A2 — that 30 Hz is visually acceptable for a moving
        needle. The report asserts it without demonstration.
      mitigation: >
        fps_limit is configuration, so the observation is a one-line
        revert. Observe on gtach.local at both rates during the §8.4
        session."
    - risk: >
        A skipped frame stalls the heartbeat and the watchdog restarts
        the display thread.
      mitigation: >
        The skip is of RENDERING, not of the loop iteration. The
        heartbeat, the shutdown check, the frame counter and the
        periodic log all run regardless. This is stated as a constraint
        and asserted."
    - risk: >
        The performance monitor records fewer frames, changing the
        meaning of frame_time_ms against the §7.5.3 baseline.
      mitigation: >
        record_frame_start/end bracket rendered frames only, so
        frame_time_ms continues to measure render cost — which is what
        change-0b00759c made it measure. fps falls, correctly, because
        fewer frames are drawn. Note it in the release record so the
        baseline comparison is not misread."
  benefits_measurement: >
    Frames rendered per second on a static screen: 60 -> 0. On a live
    RPM below caution_start with a steady engine: 60 -> the rate at
    which the quantised value changes. Above caution_start: 30, the
    flash rate flooring it. Per-frame f-string formats: 1 -> 0.

technical_details:
  current_behavior: >
    _display_loop (manager.py:422-497) renders every iteration.
    self._frame_counter increments at 451. Rendering dispatches at
    457-462, buffers swap at 465-466, the frame closes at 471 and the
    loop sleeps at 481-482 against 1.0/self.config.fps_limit.
    'import queue' is inside _draw_radial_mode at 798. The debug call is
    at 987. config/config.yaml carries display.fps_limit: 60.
  proposed_behavior: >
    The loop computes a state key, renders and presents only when it
    differs from the previous one, and otherwise sleeps. Everything else
    in the iteration is unchanged. The import is at module scope and the
    debug call is guarded.
  implementation_approach: >
    THREE PARTS, THREE COMMITS, ASCENDING RISK.

    PART 1 — recommendation 14. Move 'import queue' from
    _draw_radial_mode to the module imports. Guard the debug call:

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f'Radial mode: RPM={rpm:.0f}')

    PART 2 — recommendation 12. config/config.yaml
    display.fps_limit: 60 -> 30.

    Confirm, rather than assume, that this leaves the flash period
    unchanged: half_period is max(1, round(fps_limit / 4.0))
    (manager.py:697), so at 60 it is 15 frames and at 30 it is 8 —
    0.25 s and 0.267 s respectively. Close but not identical, the
    rounding of 7.5 to 8 shifting it by 7%. Record this; it is within
    tolerance for a shift cue and is not worth special-casing, but it
    should be observed rather than discovered.

    PART 3 — recommendation 13. _frame_state_key returns a tuple of
    everything that determines what is on screen:

      (mode,
       in_setup_mode,
       disconnected,
       options sub-view,
       update status,
       quantised RPM,
       active band,
       flash phase,
       palette identity)

    Quantised RPM is round(rpm, 1) in thousands — the displayed
    resolution, so a change below it cannot alter the output.

    Flash phase is (self._frame_counter // half_period) % 2, computed
    the same way _get_shift_cue computes it. THIS MEMBER IS THE POINT
    OF THE DESIGN.

    Palette identity is present so that change-5012004e's toggle forces
    a render, in the same spirit as 821919ce's cache key.

    In _display_loop: increment the counter, compute the key, and if it
    equals the previous one, skip the render/swap/present block and go
    to the pacing sleep. Otherwise render and store the key.

    The heartbeat at manager.py:449, the shutdown check at 422, the
    counter at 451 and the periodic log at 487-493 run on every
    iteration regardless. Only the block from clear_surface (454)
    through record_frame_end (471) is conditional.

    SPLASH is never skipped: it animates on its own timeline. Force a
    render whenever mode is SPLASH.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        queue imported at module scope; the radial debug call guarded by
        isEnabledFor; _frame_state_key added; _display_loop renders
        conditionally on it.
      functions_affected:
        - "_display_loop"
        - "_draw_radial_mode"
        - "_frame_state_key"
      classes_affected:
        - "DisplayManager"
    - component: "display.fps_limit"
      file: "config/config.yaml"
      change_summary: "60 -> 30."
  data_changes:
    - "config/config.yaml display.fps_limit changes. Deployed files carrying 60 continue to work; the value is a setting, not a schema."
  interface_changes: []

dependencies:
  internal:
    - component: "change-821919ce"
      impact: "PREREQUISITE per ai/task.md §7.6.1. It changes what a frame costs and therefore what skipping one saves. Assumption A1 is evaluated against the post-821919ce cost."
    - component: "change-4c038bed"
      impact: "Shipped. Its frame-counter flash derivation is what makes the flash phase computable as a key member. Unmodified."
    - component: "change-0b00759c"
      impact: "Shipped. Its record_frame_start/end continue to bracket rendered frames only; fps falls and frame_time_ms does not."
    - component: "change-5012004e"
      impact: "Its palette toggle must force a render; the key member is provided from the outset."
  external: []
  required_changes:
    - change_ref: "change-821919ce"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "related"

testing_requirements:
  test_approach: >
    Headless with SDL_VIDEODRIVER=dummy and a mocked rendering engine,
    counting calls to the render dispatch to establish whether a frame
    was drawn. The flash case is tested with a fixed RPM above
    caution_start across a span of frame counters — the case a naive
    implementation fails.
  test_cases:
    - scenario: "grep 'import queue' inside any function in manager.py."
      expected_result: "No occurrence."
    - scenario: "The radial debug call with DEBUG disabled, with a mock asserting the f-string is not evaluated."
      expected_result: "Not evaluated."
    - scenario: "The same with DEBUG enabled."
      expected_result: "Logged as before."
    - scenario: "config.yaml display.fps_limit."
      expected_result: "30."
    - scenario: "Flash half_period at fps_limit 60 and 30."
      expected_result: "15 and 8 frames — 0.250 s and 0.267 s. Recorded, and within tolerance."
    - scenario: "Static RPM below caution_start across 60 iterations."
      expected_result: "One render; 59 skips."
    - scenario: "STATIC RPM ABOVE caution_start across 60 iterations."
      expected_result: "The centre flashes: renders occur at every phase flip, giving at least 2 * 60 / (2 * half_period) renders. This is the test that catches a key omitting the flash phase."
    - scenario: "The OPTIONS screen across 60 iterations with no input."
      expected_result: "One render."
    - scenario: "The DISCONNECTED screen across 60 iterations."
      expected_result: "One render."
    - scenario: "The ACKNOWLEDGEMENT screen across 60 iterations."
      expected_result: "One render."
    - scenario: "SPLASH across 60 iterations."
      expected_result: "Sixty renders — never skipped."
    - scenario: "A quantised RPM change of 0.1 in thousands."
      expected_result: "Renders."
    - scenario: "An RPM change below the quantisation."
      expected_result: "Skips."
    - scenario: "A band change, a mode change, an options sub-view change, an update-status change."
      expected_result: "Renders in each case."
    - scenario: "A palette change."
      expected_result: "Renders."
    - scenario: "Entering and leaving setup mode."
      expected_result: "Renders."
    - scenario: "Heartbeat calls across 60 iterations with 59 skips."
      expected_result: "Sixty heartbeats — the skip is of rendering, not of the iteration."
    - scenario: "The shutdown event set during a run of skipped frames."
      expected_result: "The loop exits promptly."
    - scenario: "record_frame_start/end call counts."
      expected_result: "Equal to the number of rendered frames, not iterations."
  regression_scope:
    - "tests/display/ — the display suite once populated per ai/task.md §8.2."
    - "On gtach.local: the shift cue flashes above caution_start with the engine held steady. This is the acceptance test."
    - "On gtach.local: the needle at 30 Hz is acceptable during a sweep."
    - "On gtach.local: the watchdog does not restart the display thread during a long run of skipped frames."
    - "On gtach.local: touch remains responsive on the static screens."
  validation_criteria:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "config/config.yaml parses and carries display.fps_limit: 30."
    - "pytest tests/ passes with no new failures."
    - "The flash phase is a member of _frame_state_key."
    - "The heartbeat, counter, shutdown check and periodic log are outside the conditional block."
    - "SPLASH is never skipped."

implementation:
  implementation_steps:
    - step: "PRECONDITION: change-821919ce landed and the §7.5.3 baseline collected. Evaluate assumption A1 — if frame cost is already low, implement Parts 1 and 2 only and report."
      owner: "William Watson"
    - step: "Part 1 — the import and the guarded debug call. Commit."
      owner: "Claude Code"
    - step: "Part 2 — fps_limit 30. Commit."
      owner: "Claude Code"
    - step: "Part 3 — _frame_state_key and the conditional render. Commit."
      owner: "Claude Code"
    - step: "Confirm the flash above caution_start with a static RPM, on the bench before the vehicle."
      owner: "Claude Code"
    - step: "Observe on gtach.local: the flash, the needle at 30 Hz, watchdog stability and touch responsiveness on static screens."
      owner: "William Watson"
  rollback_procedure: >
    Three commits. Part 3 can be reverted alone, leaving the frame-rate
    reduction and the housekeeping in place — which is the expected
    outcome if assumption A1 fails. Part 2 is a one-line configuration
    revert.
  deployment_notes: >
    Part 2 is visible as a slower needle if 30 Hz proves insufficient.
    Part 3 is invisible when correct and conspicuous when wrong — a
    suppressed shift cue. Ships in v0.4.0 (ai/task.md §8.5) after
    821919ce.

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
    - change_ref: "change-821919ce"
      relationship: "blocked_by"
    - change_ref: "change-5012004e"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-9ed1c77e"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-9ed1c77e."
      - "Separated the three recommendations into independently revertible parts in ascending order of risk, the task list having grouped them by report section."
      - "Added the shift-cue flash phase to the skip condition, which the report's stated condition omits and whose omission would suppress the cue above caution_start."
      - "Recorded that the frame counter advances on every iteration including skipped ones, so the flash phase stays correct and a phase flip forces a render."
      - "Recorded that halving fps_limit shifts the flash period by 7% through the rounding at manager.py:697 — within tolerance, but observed rather than discovered."
      - "Recorded that only the render block is conditional: heartbeat, counter, shutdown check and periodic log run on every iteration."
      - "Recorded taking the fps_limit reduction alone as the stated fallback if assumption A1 fails."

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
| 1.0 | 2026-08-04 | Initial change document coupled to issue-9ed1c77e. Specifies three independently revertible parts, with the shift-cue flash phase added to the skip condition the report omits it from. |

---

Copyright (c) 2026 William Watson. MIT License.
