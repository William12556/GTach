Created: 2026 August 04

# Issue: The Display Renders at Twice the Data Rate, Redraws Static Screens Sixty Times a Second, and Formats Debug Strings Nobody Reads

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-9ed1c77e"
  title: "fps_limit is 60 against a 20-50 Hz data rate, every frame is rendered whether or not the displayed state changed, an import statement executes inside the render function on every frame, and two per-frame debug f-strings are formatted before the logging call that discards them"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "resolved"
  severity: "medium"
  type: "performance"
  iteration: 1
  coupled_docs:
    change_ref: "change-9ed1c77e"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Findings §5.7 (Frame Rate Selection), §5.6 (Per-Frame Allocation and
    Import) and §4.5 (Frame-Time Jitter), with §9.2 recommendations 12,
    13 and 14. Task list reference ai/task.md §7.3.6.

affected_scope:
  components:
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "display.fps_limit"
      file_path: "config/config.yaml"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: >
    Source checkout at 0.3.2. Authored against the post-378703da and
    post-821919ce tree; see technical_notes.
  steps:
    - "rec 12 §5.7 — read config/config.yaml display.fps_limit: 60, and app.py:268 where the OBD poll interval is 0.02 s for fast transports and 0.05 s otherwise, giving 20-50 Hz."
    - "rec 12 §5.7 — between one and three frames in every group therefore present identical data."
    - "rec 13 §5.7 — read manager.py:422-497. The loop renders unconditionally; nothing compares the current displayed state with the previous one."
    - "rec 13 §5.7 — observe that the DISCONNECTED, OPTIONS and ACKNOWLEDGEMENT screens are wholly static and are redrawn 60 times a second."
    - "rec 14 §5.6 — read manager.py:798. 'import queue' executes inside _draw_radial_mode on every frame."
    - "rec 14 §5.6 — read manager.py:987. self.logger.debug(f'Radial mode: RPM={rpm:.0f}') formats the f-string before the call, so the cost is paid at 60 Hz whether or not DEBUG is enabled."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional. The waste is proportional to fps_limit and is
    independent of what is on screen.
  preconditions: "None."
  test_data: >
    FRAME BUDGET. 60 Hz gives 16.67 ms; 30 Hz gives 33.3 ms. The report
    argues that a tachometer needle at 30 Hz is not distinguishable from
    one at 60 Hz at normal shift rates and that the data arrives at
    20-50 Hz regardless, so half the frames carry no new information.

    THE FLASH CONSTRAINT, which is the whole difficulty of
    recommendation 13. change-4c038bed derives the shift-cue flash
    phase from the frame counter rather than wall-clock time
    (manager.py:694-698): half_period is fps_limit/4 and the phase is
    (self._frame_counter // half_period) % 2. self._frame_counter
    increments once per loop iteration at manager.py:451.

    Two consequences the report does not draw:

      (1) A skip condition of "quantised RPM, band and mode unchanged"
          does NOT include the flash phase. Above caution_start the
          centre disc alternates between (0, 160, 0) and (10, 10, 10)
          — a visible change on a frame where RPM, band and mode are
          all identical. Skipping that frame suppresses the flash.
          The report's own note at §9.2 says items 12 and 13 "interact
          with item 5: the flash requires frames even when the RPM is
          static", but does not say that the flash phase must therefore
          be a member of the skip condition. It must.

      (2) If _frame_counter advances only on rendered frames, skipping
          slows the flash; if it advances on skipped frames too, the
          phase stays correct but a skipped frame may be exactly the one
          on which the phase flips. Either way the counter's
          relationship to the skip logic must be stated, not left
          implicit.

    Additionally, halving fps_limit halves half_period, so the flash
    period in wall-clock terms is unchanged by recommendation 12 —
    which is the property change-4c038bed's frame-counter derivation was
    chosen for. Worth confirming rather than assuming.

    REC 14's SITES AFTER 378703da. The report cites manager.py:621 and
    693 for the import and manager.py:649 and 882 for the debug
    strings — two of each, one pair in DIGITAL and one in RADIAL.
    change-378703da removes _draw_digital_mode, so one of each pair is
    already gone. At 0.3.2 the survivors are the import at
    manager.py:798 and the debug call at manager.py:987.
  error_output: "None. A cost finding."

behavior:
  expected: >
    A display renders when what it shows has changed, at a rate matched
    to its data. Imports execute at module load. A logging call at 60 Hz
    does not pay formatting costs when its level is disabled.
  actual: >
    (a) rec 12, §5.7 and §4.5 — fps_limit is 60 against a 20-50 Hz data
    rate. The report links the resulting GIL occupancy to irregular OBD
    sample arrival, so the cost is not confined to the display thread.

    (b) rec 13, §5.7 — every frame is rendered regardless of whether
    anything changed. On the DISCONNECTED, OPTIONS and ACKNOWLEDGEMENT
    screens this is entirely wasted.

    (c) rec 14, §5.6 — 'import queue' executes inside _draw_radial_mode
    each frame; the module cache makes it cheap but not free.
    self.logger.debug(f'...') formats its f-string before the call, so
    the cost is paid at 60 Hz even when DEBUG is disabled — which is
    production, where logging is configured with a NullHandler.
  impact: >
    Frame time and GIL occupancy consumed to no effect. The report
    attributes part of §4.5's frame-time jitter to this, and jitter
    interacts with the tearing analysis in §4.1.

    Magnitude unmeasured. See technical_notes.
  workaround: >
    fps_limit can be lowered by hand in config.yaml today — that is
    recommendation 12, and it is the one part of this issue that needs
    no code.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) on Raspberry Pi Zero 2W, Cortex-A53"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    A fixed frame rate chosen as a conventional default rather than
    against the data rate, and an unconditional render loop, which is
    the correct starting design and remains correct until the cost
    matters. The import and the debug string are ordinary oversights of
    a kind that only matter inside a 60 Hz loop.
  technical_notes: >
    AUTHORED AHEAD OF ITS GATING OBSERVATION. ai/task.md §8.1 names this
    triple among those that "cannot be authored correctly yet": it
    depends on the §7.5.3 frame_time_ms baseline, and ai/task.md §7.6.1
    records it as depending on 7.3.5 (821919ce), because the
    static-layer cache changes what a frame costs and therefore what
    skipping one saves. Neither the baseline nor 821919ce is in place.

    Authored now by explicit instruction. Two assumptions, each bound in
    change-9ed1c77e to what must be revised if contradicted:

      A1. That frame cost is material enough for skipping to be worth
          its risk. If 821919ce reduces a RADIAL frame to a blit plus
          four primitives, the remaining cost may not justify the
          conditional-render machinery, and recommendation 13 should be
          withdrawn while 12 and 14 proceed.
      A2. That 30 Hz is visually acceptable for the needle. This is a
          judgement about a moving indicator that no static analysis
          settles, and the report asserts rather than demonstrates it.

    THE THREE RECOMMENDATIONS ARE NOT EQUALLY RISKY and should not
    travel together without that being said. Recommendation 14 is
    housekeeping in two lines. Recommendation 12 is a configuration
    default. Recommendation 13 is a change to when the display draws at
    all, on a device whose purpose is to show a changing number, and it
    carries the flash constraint described in test_data. They are
    grouped in one triple because ai/task.md §7.3 groups them; the
    change document separates them into independently revertible parts.

    THE FLASH IS THE CORRECTNESS RISK. See test_data. A skip condition
    that omits the flash phase will pass every test written against a
    static RPM and will suppress the shift cue above caution_start —
    the one moment the instrument most needs to be believed. This is the
    single most important thing in this triple.

    ON §4.5. The report lists recommendation 12 as addressing frame-time
    jitter. Jitter was also affected by change-0b00759c, which moved
    record_frame_end before the pacing sleep, and by 66ef59a0 and
    49b21ace on the write path. Whether jitter remains after those is
    unknown and is part of what the §8.4 session observes. This triple
    should not claim credit for §4.5 without that observation.
  related_issues:
    - issue_ref: "issue-821919ce"
      relationship: "blocked_by"
    - issue_ref: "issue-4c038bed"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Move the import to module scope and guard the debug f-string. Reduce
    the configured fps_limit to 30. Add a conditional render whose skip
    condition includes the flash phase alongside the quantised RPM, band
    and mode. See change-9ed1c77e.
  change_ref: "change-9ed1c77e"
  resolved_date: "2026-08-05"
  resolved_by: "Claude Code, per prompt-9ed1c77e (Parts 1 and 2 only)"
  fix_description: >
    Recommendation 14: 'import queue' moved to module scope (confirmed
    live at manager.py:20); the debug f-string guarded by
    logger.isEnabledFor(logging.DEBUG) (confirmed live at
    manager.py:1376). Recommendation 12: config/config.yaml
    display.fps_limit reduced to 30 (confirmed live). Recommendation 13
    (conditional render, the flash-phase-sensitive skip logic) is NOT
    implemented — deferred alongside issue-821919ce per ai/task.md
    §9.13, its own assumption A1 (frame cost material enough to justify
    skipping) having been falsified by the measured 46%-of-budget
    result recommendation 12 alone produced.

verification:
  verified_date: "2026-08-05"
  verified_by: "William Watson (gtach.local, task.md §9.11.6-§9.13)"
  test_results: >
    On-target: 32 samples at exactly 30.0 FPS, zero exceeding 33.3 ms,
    against 32% overrunning at 60 Hz pre-change. Source re-check
    2026-08-07 confirms both Part 1 and Part 2 fixes live and byte-
    identical to the recorded description.
  closure_notes: >
    NOT MOVED TO closed/. This issue is intentionally left at
    "resolved" rather than "closed", per the same distinction task.md
    §17.0 introduced for change_info.status: Parts 1-2 are complete and
    on-target verified, but Part 3 is a genuine, deliberate deferral of
    part of this issue's own original scope, not an oversight or a
    closure formality. William confirmed 2026-08-07 that GTach is
    functioning correctly on gtach.local, which covers what Parts 1-2
    deliver. Should Part 3 (or 821919ce) later be picked up, revise
    this document rather than opening a new one — the assumptions and
    the flash-phase risk are already recorded here in full.

prevention:
  preventive_measures: >
    A skip condition is a claim that nothing else can change the output.
    Enumerating what the frame depends on — as the cache key in 821919ce
    does — is the same discipline applied to a different question, and
    the flash is the member both are most likely to omit.

    An f-string inside a logging call at 60 Hz is a cost regardless of
    level. isEnabledFor is the guard; lazy %-formatting is the
    alternative.
  process_improvements: >
    Grouping a two-line housekeeping fix with a change to when the
    display draws produced a triple whose parts have very different risk
    profiles. Where a task list groups by report section rather than by
    risk, the change document should separate them, as this one does.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "'import queue' does not appear inside any function in manager.py."
    - "No f-string is evaluated for a debug call inside the render path unless DEBUG is enabled."
    - "config.yaml carries display.fps_limit: 30."
    - "The wall-clock flash period is unchanged between fps_limit 60 and 30."
    - "Above caution_start with a perfectly static RPM, frames continue to be rendered and the centre disc flashes."
    - "Below caution_start with a static RPM, frames are skipped."
    - "On the DISCONNECTED, OPTIONS and ACKNOWLEDGEMENT screens, frames are skipped."
    - "A change in quantised RPM, band, mode or flash phase causes a frame to be rendered."
    - "Entering or leaving any screen renders."
    - "Heartbeat and shutdown handling continue on skipped frames."
    - "Measured frame_time_ms and CPU on gtach.local improve against the §7.5.3 baseline — evaluable only once that baseline exists."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-9ed1c77e"
  test_refs: []

notes: >
  This is task 7.3.6 in ai/task.md §7.3 and step 6 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5).

  issue_info.type is performance per ai/task.md §7.2.

  Authored ahead of both its gating observation (§7.5.3) and its
  prerequisite change (821919ce), contrary to ai/task.md §8.1, by
  explicit instruction. Two assumptions are enumerated in
  technical_notes. Recommendation 13 in particular should be reviewed
  against the post-821919ce frame cost before it is implemented.

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
      - "Initial issue document from display-ui-graphics-review.md findings §5.6, §5.7 and §4.5 with §9.2 recommendations 12, 13 and 14."
      - "Recorded the flash constraint in full: the skip condition must include the flash phase, which the report's stated condition of quantised RPM, band and mode does not, and which would suppress the shift cue above caution_start."
      - "Recorded that the frame counter's relationship to skipped frames must be stated explicitly, since the flash phase derives from it."
      - "Recorded that the three recommendations differ greatly in risk and that the change document separates them into independently revertible parts."
      - "Recorded that one of each pair of rec 14's sites has already gone with change-378703da, and identified the survivors."
      - "Recorded two assumptions arising from authoring ahead of the §7.5.3 baseline and of change-821919ce."
  - version: "1.1"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Status open -> resolved. Recommendations 12 and 14 are implemented; recommendation 13 is deferred."
      - "Recommendation 14 (module-scope import, guarded debug f-string) and recommendation 12 (fps_limit 30) landed on 2026-08-05 as Parts 1 and 2."
      - "Recommendation 12's effect was larger than this issue claimed. It removed EVERY budget overrun: 32 samples at exactly 30.0 FPS, none exceeding 33.3 ms, against 32% overrunning at 60 Hz. Measured FPS went from six distinct values to one, which is the frame-time jitter of display report §4.5 eliminated rather than reduced."
      - "That jitter removal is the most likely contributor to the flicker's disappearance (ai/task.md §9.11.7), though no single change is provable as the cause and this document does not claim one."
      - "Recommendation 13 (conditional render) is DEFERRED. Assumption A1 — that frame cost would still justify skipping — is false at 46% of budget with no overruns and no visible fault. Static screens redrawing thirty times a second remains real waste that the instrument can afford."
      - "Both remaining assumptions are now settled: A1 false, and A2 (30 Hz acceptable for the needle) confirmed by observation on the panel."
      - "Left active pending a T06 result for the implemented parts, per ai/task.md §8.2.1. Recommendation 13 does not gate that closure; it is deferred, not outstanding."
  - version: "1.2"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Resolution and verification recorded for Parts 1-2 (module-scope import, guarded debug f-string, fps_limit 30), confirmed live by source re-check."
      - "Deliberately left at status resolved, not closed. Part 3 remains a genuine open deferral of this issue's original scope, not a closure formality. William confirmed GTach functions correctly on gtach.local, covering what Parts 1-2 deliver."

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
| 1.0 | 2026-08-04 | Initial issue document from display review findings §5.6, §5.7 and §4.5 with recommendations 12, 13 and 14. Records the flash-phase omission in the report's stated skip condition, the differing risk profiles of the three recommendations, and two assumptions from authoring ahead of the §7.5.3 baseline. |
| 1.1 | 2026-08-05 | Status open → resolved. Recommendations 12 and 14 implemented as Parts 1-2, measured to remove every budget overrun; recommendation 13 deferred, its own assumption A1 falsified by that result. |
| 1.2 | 2026-08-07 | Resolution and verification recorded for Parts 1-2, confirmed by source re-check. Deliberately left at "resolved", not "closed" — Part 3 remains a genuine open deferral, not a closure formality. William confirmed GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
