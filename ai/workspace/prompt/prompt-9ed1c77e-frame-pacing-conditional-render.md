Created: 2026 August 04

# Prompt: Render When Something Changed — Including the Flash

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-9ed1c77e"
  task_type: "implementation"
  source_ref: "change-9ed1c77e"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-9ed1c77e"
    change_iteration: 1

context:
  purpose: >
    The display renders 60 times a second against a 20-50 Hz data rate
    and redraws wholly static screens at the same rate. An import
    executes inside the render function on every frame, and a debug
    f-string is formatted at 60 Hz for a logger that discards it in
    production.
  integration: >
    Two files: src/gtach/display/manager.py and config/config.yaml.
    Executor is Claude Code; AEL is not used.

    GATE. ai/task.md §7.6.1 records this triple as depending on 7.3.5
    (change-821919ce), which changes what a frame costs and therefore
    what skipping one saves; ai/task.md §8.1 records the §7.5.3
    baseline as a further prerequisite. Confirm both before Part 3. If
    a RADIAL frame is already cheap after 821919ce, implement Parts 1
    and 2 and report — Part 3's risk would not be justified.

    THREE PARTS, THREE COMMITS, ASCENDING RISK. Part 1 cannot break
    anything. Part 2 is one configuration value. Part 3 changes when
    the instrument draws at all.

    THE ONE THING THAT MATTERS IN PART 3. The shift-cue flash
    alternates the centre disc between two colours on frames where the
    RPM, the band and the mode are all identical. The report's stated
    skip condition — quantised RPM, band, mode — omits it. A skip
    condition without the flash phase will pass every test written
    against a static RPM and will silently suppress the shift cue above
    caution_start. The flash phase is a member of the key.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and config/config.yaml."
    - "Do NOT omit the flash phase from the frame state key."
    - "Do NOT skip the loop iteration. Only the render block is conditional. The heartbeat, the frame counter, the shutdown check and the periodic performance log run on every iteration."
    - "Do NOT advance the frame counter only on rendered frames. The flash phase derives from it and would slow when frames are skipped."
    - "Do NOT skip SPLASH frames. The splash animates on its own timeline."
    - "Do NOT alter _get_shift_cue or the flash derivation added by change-4c038bed."
    - "Do NOT alter record_frame_start or record_frame_end, or where they sit relative to the pacing sleep. change-0b00759c placed them deliberately."
    - "Do NOT change the OBD poll interval at app.py:268."
    - "Do NOT make the frame rate adaptive. A binary skip is auditable; an adaptive rate is not."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Move the queue import to module scope, guard the radial debug call,
    reduce the configured fps_limit to 30, and render only when the
    frame state key changes.
  requirements:
    functional:
      - "'import queue' does not appear inside any function in manager.py."
      - "The radial debug f-string is not evaluated when DEBUG is disabled."
      - "config/config.yaml carries display.fps_limit: 30."
      - "_frame_state_key includes mode, setup flag, disconnected condition, options sub-view, update status, quantised RPM, active band, flash phase and palette identity."
      - "A frame is rendered when the key differs from the previous frame's, and skipped when it does not."
      - "SPLASH always renders."
      - "The heartbeat, frame counter, shutdown check and periodic log run on skipped iterations."
      - "Above caution_start with a perfectly static RPM, frames continue to render at the flash rate."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Rendered frames per second on a static screen: 60 -> 0. On a steady engine below caution_start: 60 -> the quantised-value change rate"
      metric: "time"

design:
  architecture: >
    A skip condition is a claim that nothing else can change the output.
    The key enumerates what the frame depends on, and the flash is the
    member most easily forgotten because it is the only one driven by
    time rather than by data.
  components:
    - name: "DisplayManager._frame_state_key"
      type: "function"
      purpose: "Everything that determines what is on screen."
      interface:
        outputs:
          type: "tuple"
      logic:
        - "self.config.mode."
        - "self._in_setup_mode."
        - "The disconnected condition, computed exactly as _current_view_key does at manager.py:1025-1029."
        - "self._options_view."
        - "self._update_status."
        - "Quantised RPM: round(self._rpm_display / 1000.0, 1) — the displayed resolution."
        - "self._active_band."
        - "Flash phase: (self._frame_counter // max(1, int(round(self.config.fps_limit / 4.0)))) % 2 — computed the same way _get_shift_cue computes it at manager.py:697-698."
        - "Palette identity: getattr(getattr(self, '_palette', None), 'name', 'fixed') — present so change-5012004e's toggle forces a render."
    - name: "DisplayManager._display_loop"
      type: "function"
      purpose: "Render conditionally."
      logic:
        - "Increment the counter, update the heartbeat and register view regions as today."
        - "Compute the key. Render if it differs from self._last_frame_key, or if mode is SPLASH."
        - "The conditional block is manager.py:454 (clear_surface) through 471 (record_frame_end) inclusive."
        - "Store the key after rendering."
        - "Pace and log as today, on every iteration."
  dependencies:
    internal:
      - "change-821919ce — prerequisite."
      - "change-4c038bed — supplies the frame-counter flash derivation the key member mirrors."
      - "change-0b00759c — its frame bracketing stays inside the conditional block, so it measures rendered frames."
    external: []

error_handling:
  strategy: >
    A failure computing the key must render, not skip. A missed frame is
    worse than a redundant one on an instrument.
  exceptions:
    - exception: "Exception"
      condition: "_frame_state_key raises."
      handling: "Log at ERROR with a traceback and return a unique sentinel, so the key always differs and the frame renders. Never skip on error."
    - exception: "Exception"
      condition: "Anything else in the loop."
      handling: "Existing handler at manager.py:495-497. Unchanged."
  logging:
    level: "ERROR on a key failure. Do NOT log per skipped frame — that would reintroduce the per-frame cost this change removes"
    format: "self.logger.error(f'Frame state key error: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "grep 'import queue' inside any function in manager.py."
      expected: "No occurrence; the module-scope import is present."
    - scenario: "The radial debug call with DEBUG disabled, asserted with a __format__-instrumented value."
      expected: "The f-string is not evaluated."
    - scenario: "The same with DEBUG enabled."
      expected: "Logged."
    - scenario: "config/config.yaml display.fps_limit."
      expected: "30."
    - scenario: "half_period at fps_limit 60 and 30."
      expected: "15 and 8 frames. Record the wall-clock periods, 0.250 s and 0.267 s."
    - scenario: "Sixty iterations, static RPM at 2000 (below caution_start), RADIAL."
      expected: "One render, 59 skips."
    - scenario: "Sixty iterations, static RPM at 5000 (above caution_start), RADIAL."
      expected: "Renders at every flash-phase flip — at least 6 with half_period 8. THIS IS THE TEST THAT CATCHES A KEY WITHOUT THE FLASH MEMBER. Assert the count is greater than 1."
    - scenario: "Sixty iterations on OPTIONS with no input."
      expected: "One render."
    - scenario: "Sixty iterations on the DISCONNECTED condition."
      expected: "One render."
    - scenario: "Sixty iterations on ACKNOWLEDGEMENT."
      expected: "One render."
    - scenario: "Sixty iterations on SPLASH."
      expected: "Sixty renders."
    - scenario: "RPM changing by 100 (0.1 in thousands)."
      expected: "Renders."
    - scenario: "RPM changing by 10."
      expected: "Skips."
    - scenario: "Band, mode, options sub-view, update status and palette each changed in turn."
      expected: "Renders in each case."
    - scenario: "Entering and leaving setup mode."
      expected: "Renders."
    - scenario: "Sixty iterations with 59 skips — heartbeat call count."
      expected: "Sixty."
    - scenario: "Sixty iterations with 59 skips — record_frame_start call count."
      expected: "One. It brackets rendered frames only."
    - scenario: "_shutdown_event set during a run of skips."
      expected: "The loop exits within one iteration."
    - scenario: "_frame_state_key forced to raise."
      expected: "The frame renders; an ERROR is logged."
  edge_cases:
    - "The first iteration: _last_frame_key is None, which differs from any tuple, so the first frame renders. Assert rather than assume."
    - "fps_limit changed at runtime — half_period changes and so does the flash phase, forcing a render. Correct, and harmless."
    - "self._rpm_display before any sample has arrived. It is initialised in __init__; confirm the key can read it on the first iteration."
    - "A skipped frame during which a touch registers: touch is handled on its own thread through the coordinator and does not depend on rendering. The state it changes — options sub-view, mode — is in the key, so the next iteration renders. Verify the region registration at manager.py:435-444 stays outside the conditional block, or a view change would register regions and then not draw them."
    - "Above caution_start the flash floors the render rate at 2/half_period per second, so the instrument never goes fully idle while the shift cue is active. That is intended."
  validation:
    - "grep confirms the heartbeat, counter increment, shutdown check and periodic log are outside the conditional block."
    - "grep confirms the view-region registration is outside the conditional block."
    - "git diff confirms _get_shift_cue is unmodified."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "Three commits, in the order given."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        PART 1 — housekeeping. Commit alone.

        (a) Move 'import queue' out of _draw_radial_mode
        (manager.py:798) to the module-level imports at the top of the
        file, beside the existing stdlib imports.

        (b) Guard the debug call at manager.py:987:

                self.logger.debug(f'Radial mode: RPM={rpm:.0f}')

        becomes:

                # The f-string is formatted before the call, so at 60 Hz
                # the cost was paid whether or not DEBUG was enabled —
                # and production configures a NullHandler
                # (display review §5.6, recommendation 14).
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f'Radial mode: RPM={rpm:.0f}')

        Confirm logging is imported at module scope in this file; it is.

        PART 3 — the conditional render. Commit last.

        (a) In __init__:

                self._last_frame_key = None

        (b) _frame_state_key:

            def _frame_state_key(self) -> tuple:
                """Everything that determines what is on screen.

                A frame whose key matches the previous frame's cannot
                differ from it, so it is not drawn. The flash-phase
                member is essential: the shift cue alternates the centre
                disc on frames where the RPM, band and mode are all
                unchanged, and a key without it would suppress the cue
                above caution_start (display review §5.7 recommendation
                13, with §9.2's note that the flash requires frames even
                when the RPM is static).
                """
                disconnected = (
                    self.thread_manager.get_thread_status('obd_protocol')
                    != ThreadStatus.RUNNING
                    and not self._sim_mode
                )
                half_period = max(1, int(round(self.config.fps_limit / 4.0)))
                flash_phase = (self._frame_counter // half_period) % 2
                palette = getattr(self, '_palette', None)
                return (
                    self.config.mode,
                    self._in_setup_mode,
                    disconnected,
                    self._options_view,
                    self._update_status,
                    round(getattr(self, '_rpm_display', 0.0) / 1000.0, 1),
                    getattr(self, '_active_band', 0),
                    flash_phase,
                    getattr(palette, 'name', 'fixed'),
                )

        half_period must be computed exactly as _get_shift_cue computes
        it at manager.py:697. If those two ever diverge the flash will
        be skipped on some phases and not others, which is worse than
        skipping it entirely because it will look like a hardware fault.

        (c) In _display_loop, wrap the block from clear_surface
        (manager.py:454) through record_frame_end (471):

                try:
                    _key = self._frame_state_key()
                except Exception as e:
                    self.logger.error(
                        f'Frame state key error: {e}', exc_info=True
                    )
                    _key = object()   # unique: always renders

                _force = self.config.mode == DisplayMode.SPLASH
                if _force or _key != self._last_frame_key:
                    self.rendering_engine.clear_surface(...)
                    ... existing render dispatch ...
                    self.rendering_engine.swap_buffers()
                    self.rendering_engine.write_to_framebuffer()
                    self.performance_monitor.record_frame_end(frame_id)
                    self._last_frame_key = _key

        record_frame_start at manager.py:447 moves INSIDE the
        conditional with its matching end, so the monitor brackets
        rendered frames only. Do not leave the start outside and the end
        inside — that would leave frames open forever and the monitor's
        expiry scan would grow.

        EVERYTHING ELSE STAYS OUTSIDE the conditional: the shutdown
        check at 422, the view-region registration at 435-444, the
        heartbeat at 449, the counter at 451, the pacing sleep at
        477-482 and the periodic log at 487-493.

        The view-region registration in particular must stay outside. If
        it were inside, a view change would be detected, the regions
        registered, and then the frame not drawn — leaving controls
        registered for a screen that is not on the display.
    - path: "config/config.yaml"
      content: |
        PART 2 — one value. Commit alone.

        Under the display: key:

            fps_limit: 60

        becomes:

            fps_limit: 30

        The data arrives at 20-50 Hz (app.py:268), so 60 Hz presents
        between one and three identical frames in every group
        (display review §5.7, §3.3, recommendation 12).

        Change nothing else in the file.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "config/config.yaml parses and carries display.fps_limit: 30."
  - "pytest tests/ passes with no new failures."
  - "'import queue' appears at module scope and inside no function."
  - "The radial debug f-string is not evaluated when DEBUG is disabled."
  - "_frame_state_key includes a flash-phase member computed identically to _get_shift_cue's."
  - "Sixty iterations at a static RPM above caution_start produce more than one render."
  - "Sixty iterations at a static RPM below caution_start produce exactly one render."
  - "Sixty iterations on OPTIONS, DISCONNECTED and ACKNOWLEDGEMENT each produce exactly one render."
  - "Sixty iterations on SPLASH produce sixty renders."
  - "The heartbeat is called on every iteration."
  - "record_frame_start and record_frame_end are both inside the conditional block and are called equally often."
  - "The view-region registration is outside the conditional block."
  - "_get_shift_cue is byte-identical to its current text."
  - "No file other than the two named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "_frame_state_key"
        module: "gtach.display.manager"
        signature: "_frame_state_key(self) -> tuple"
      - name: "_display_loop"
        module: "gtach.display.manager"
        signature: "_display_loop(self) -> None"
      - name: "_draw_radial_mode"
        module: "gtach.display.manager"
        signature: "_draw_radial_mode(self) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-9ed1c77e-frame-pacing-conditional-render.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  Check the gate before Part 3. If change-821919ce has already made a
  RADIAL frame cheap, Parts 1 and 2 may be the whole of the useful work
  here — that is an acceptable outcome and is why the parts are
  separable.

  Three ways to get Part 3 wrong, all of which compile and two of which
  pass a naive test suite:

    - omitting the flash phase, which suppresses the shift cue above
      caution_start while every static-RPM test passes;
    - computing half_period differently from _get_shift_cue, which
      makes the cue flash on some phases and not others — worse than
      not flashing, because it reads as a hardware fault;
    - putting the view-region registration inside the conditional,
      which registers controls for a screen that is then not drawn.

  The on-target acceptance test is simple and non-negotiable: hold the
  engine steady above caution_start and confirm the centre disc still
  flashes.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-9ed1c77e. |

---

Copyright (c) 2026 William Watson. MIT License.
