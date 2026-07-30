Created: 2026 July 30

# Prompt: RPM Signal Conditioning for the Display Path

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-4c038bed"
  task_type: "code_generation"
  source_ref: "change-4c038bed"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-4c038bed"
    change_iteration: 1

context:
  purpose: >
    Insert a conditioning stage between the raw RPM sample and every
    display consumer, so that a steady engine speed produces a steady
    picture. Four faults are corrected together because they share the
    same value-to-pixels path: band thrash, displayed-value churn, an
    unstable shift-cue duty cycle, and a contrast failure on the
    torque-approach band.
  integration: >
    One file: src/gtach/display/manager.py. Five edits. Executor is Claude
    Code; AEL is not used. This is the first item in the recommended
    authoring order of ai/task.md §7.6.2 and the report asks that it be
    implemented and observed before any framebuffer change is attempted.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py. Do not touch engine.py, monitor.py, models.py, obd.py, app.py, or config.yaml."
    - "self._last_rpm must continue to hold the RAW value. Conditioning is display-side only; no logged or reported RPM figure may change."
    - "Do not change the OBD poll rate, fps_limit, or any band threshold value in RPMBands."
    - "Do not add a dependency. Use only stdlib (math, time) and what manager.py already imports."
    - "_get_band_colour keeps its existing signature and return type: (bg_colour, text_colour)."
    - "_get_shift_cue keeps its existing signature and 4-tuple return: (border_colour, border_width, flash_centre, centre_colour)."
    - "Retain every existing try/except and its fallback return value. A conditioning fault must degrade to current behaviour, not blank the display."
    - "Do not replace the full-field band fill with an annular indicator. That is a separate change (change-5014040c)."
    - "Do not add frame skipping or reduce the frame rate. That is a separate change (change-9ed1c77e)."
    - "Type hints on all new public interfaces; Google-style docstrings; PEP 8."

specification:
  description: >
    Add EMA smoothing of the displayed RPM figure, directional hysteresis
    on band selection, a frame-counter-derived flash phase, and a
    corrected text colour for the torque-approach band.
  requirements:
    functional:
      - "A new _condition_rpm(raw) returns an exponentially smoothed RPM with a 150 ms time constant, computed from the measured inter-frame interval."
      - "Band selection is sticky: the active band changes only when the conditioned value passes the relevant threshold by the hysteresis margin in the direction of travel."
      - "The hysteresis margin is 75 RPM, clamped to less than half the narrowest adjacent gap in the live RPMBands."
      - "The torque-approach band returns white text (255,255,255) instead of black."
      - "The shift-cue flash phase derives from a monotonic frame counter scaled by fps_limit, giving a 2 Hz flash with equal on and off intervals at any frame rate."
      - "Both _draw_digital_mode and _draw_radial_mode use the conditioned value for the numeral, the band and the shift cue."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No measurable increase in per-frame render cost"
      metric: "time"

design:
  architecture: >
    A single conditioning function owned by DisplayManager, called once per
    frame from each render path, plus a sticky band selector and a
    frame-counter phase source. All state lives on the DisplayManager
    instance and is touched only from the display thread.
  components:
    - name: "DisplayManager._condition_rpm"
      type: "function"
      purpose: "First-order exponential smoothing of the raw RPM for display."
      interface:
        inputs:
          - name: "raw"
            type: "float"
            description: "Raw RPM sample as drained from the OBD message queue."
        outputs:
          type: "float"
          description: "Smoothed RPM for display consumers."
        raises:
          - "None. Returns raw on any internal error, logged at ERROR with exc_info."
      logic:
        - "Read time.monotonic(); compute dt against the stored previous timestamp; clamp dt to [0.001, 0.5]."
        - "On the first call (no previous timestamp), seed self._rpm_display with raw and return raw — do not filter up from zero."
        - "alpha = 1.0 - math.exp(-dt / self._rpm_ema_tau)"
        - "self._rpm_display += alpha * (raw - self._rpm_display)"
        - "Store the new timestamp; return self._rpm_display."
        - "Wrap the body in try/except Exception; on error log with exc_info=True and return raw."
    - name: "DisplayManager._get_band_colour"
      type: "function"
      purpose: "Sticky band selection with directional hysteresis; returns background and text colours."
      interface:
        inputs:
          - name: "rpm"
            type: "float"
            description: "Conditioned RPM value."
        outputs:
          type: "Tuple[Tuple[int, int, int], Tuple[int, int, int]]"
          description: "(bg_colour, text_colour) — unchanged from the current contract."
        raises:
          - "None. Existing except clause returns ((0,0,0),(255,255,255))."
      logic:
        - "Build an ordered band table from self.config.rpm_bands: index 0 idle (0,0,0)/white; 1 torque-approach (0,0,255)/WHITE; 2 torque (0,255,0)/black; 3 caution (255,255,0)/black; 4 warning (255,128,0)/black; 5 danger (255,0,0)/black."
        - "Thresholds in ascending order: idle_max, torque_start, caution_start, warning_start, danger_start."
        - "Compute the effective margin: min(self._band_hysteresis, 0.49 * narrowest gap between adjacent thresholds)."
        - "To move up from band i: require rpm > threshold[i] + margin. To move down from band i: require rpm < threshold[i-1] - margin."
        - "Apply at most one band step per call so a large jump settles over consecutive frames rather than skipping the hysteresis test."
        - "Store the resulting index in self._active_band; return that band's colour pair."
        - "Keep the existing except Exception clause and its fallback verbatim."
    - name: "DisplayManager._get_shift_cue"
      type: "function"
      purpose: "Shift cue colours and flash state, with a stable duty cycle."
      interface:
        inputs:
          - name: "rpm"
            type: "float"
            description: "Conditioned RPM value."
        outputs:
          type: "Tuple[Tuple[int, int, int], int, bool, Tuple[int, int, int]]"
          description: "(border_colour, border_width, flash_centre, centre_colour) — unchanged."
        raises:
          - "None. Existing except clause returns ((200,0,0), 12, False, (26,26,26))."
      logic:
        - "Replace flash = int(time.monotonic() * 2) % 2 == 0."
        - "half_period = max(1, int(round(self.config.fps_limit / 4.0)))  # frames per half cycle at 2 Hz"
        - "flash = (self._frame_counter // half_period) % 2 == 0"
        - "Leave the three RPM branches, their colours and the border width of 12 exactly as they are."
    - name: "DisplayManager.__init__"
      type: "function"
      purpose: "Initialise conditioning state."
      logic:
        - "Add self._rpm_display = 0.0"
        - "Add self._rpm_ema_tau = 0.150"
        - "Add self._rpm_last_ts = None"
        - "Add self._active_band = 0"
        - "Add self._band_hysteresis = 75.0"
        - "Add self._frame_counter = 0"
    - name: "DisplayManager._display_loop"
      type: "function"
      purpose: "Advance the frame counter."
      logic:
        - "Immediately after self.thread_manager.update_heartbeat('display') (currently manager.py:415), add self._frame_counter += 1."
    - name: "DisplayManager._draw_digital_mode / _draw_radial_mode"
      type: "function"
      purpose: "Route display consumers through the conditioner."
      logic:
        - "After the existing queue drain sets self._last_rpm and rpm is read from it, insert rpm = self._condition_rpm(rpm)."
        - "Apply in both methods, including the simulation-mode branch, so the synthetic sweep is conditioned identically."
        - "Do NOT write the conditioned value back to self._last_rpm."
  dependencies:
    internal:
      - "display/models.py RPMBands — read only, for thresholds and gap spacing."
      - "display/models.py DisplayConfig.fps_limit — read only, for the flash half-period."
    external: []

error_handling:
  strategy: >
    Every new code path degrades to the current behaviour rather than
    failing. _condition_rpm returns its argument on error. Band selection
    retains its existing fallback pair. No new exception type is
    introduced and no exception propagates to the display loop.
  exceptions:
    - exception: "Exception"
      condition: "Any failure inside _condition_rpm — non-numeric input, clock anomaly, attribute error."
      handling: "logger.error(msg, exc_info=True); return raw."
    - exception: "Exception"
      condition: "Any failure inside _get_band_colour."
      handling: "Existing handler retained: logger.error with exc_info; return ((0,0,0),(255,255,255))."
    - exception: "ZeroDivisionError"
      condition: "fps_limit is zero or absent when computing the flash half-period."
      handling: "half_period is guarded by max(1, ...); no division by the counter occurs."
  logging:
    level: "ERROR"
    format: "logger.error(f'...: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "Step input 0 to 3000 at a fixed 60 Hz dt through _condition_rpm."
      expected: "Reaches 63% of the step within 150 ms plus or minus one frame; converges monotonically."
    - scenario: "First call to _condition_rpm."
      expected: "Returns raw exactly; does not ramp from zero."
    - scenario: "Alternating 2998 / 3002 with the active band already below torque_start."
      expected: "No band change. First transition only above 3075."
    - scenario: "Sweep 2900 up to 3200 and back to 2900."
      expected: "Exactly two transitions: up at 3075, down at 2925."
    - scenario: "Band colour pair requested for the torque-approach band."
      expected: "((0,0,255), (255,255,255))."
    - scenario: "240 frames at fps_limit 60, recording the flash boolean."
      expected: "Eight complete cycles; 15 frames on and 15 off in each."
    - scenario: "120 frames at fps_limit 30."
      expected: "Eight complete cycles at 2 Hz; equal on and off frame counts."
    - scenario: "RPMBands configured with adjacent thresholds 100 RPM apart."
      expected: "Effective margin clamped below 50 RPM; both transitions remain reachable."
  edge_cases:
    - "dt of zero or negative from a clock anomaly — clamped to the lower bound."
    - "dt of several seconds after a stalled frame — clamped to 0.5 s, so the filter converges quickly rather than stepping."
    - "raw is None or a string — caught, logged, argument returned."
    - "fps_limit of 0 in a malformed config — half_period floors at 1."
    - "RPM jumping across four bands in one sample — one band step per call; settles over consecutive frames."
  validation:
    - "self._last_rpm holds the raw value after every render call."
    - "No call site of _get_band_colour or _get_shift_cue required a signature change."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place. Create no new file."
    - "Make the five edits described in design.components. Change nothing else in the file."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        EDIT 1 — DisplayManager.__init__

        Add the following instance attributes alongside the existing display
        state initialisation. Place them together, with the comment shown:

            # RPM signal conditioning (change-4c038bed)
            self._rpm_display = 0.0          # EMA output — the displayed figure
            self._rpm_ema_tau = 0.150        # EMA time constant, seconds
            self._rpm_last_ts = None         # time.monotonic() of previous conditioning call
            self._active_band = 0            # sticky band index for hysteresis
            self._band_hysteresis = 75.0     # band transition margin, RPM
            self._frame_counter = 0          # monotonic frame counter, advanced in _display_loop

        EDIT 2 — add _condition_rpm immediately BEFORE _get_band_colour
        (currently at manager.py:540):

            def _condition_rpm(self, raw: float) -> float:
                """Smooth the raw RPM sample for display.

                Applies a first-order exponential moving average with the time
                constant self._rpm_ema_tau, computed against the measured
                interval since the previous call so the time constant holds
                regardless of frame rate. The raw value is not modified;
                self._last_rpm continues to hold it.

                Args:
                    raw: Raw RPM sample as drained from the OBD message queue.

                Returns:
                    Smoothed RPM for display consumers. Returns raw unchanged
                    if conditioning fails.
                """
                try:
                    now = time.monotonic()
                    if self._rpm_last_ts is None:
                        self._rpm_last_ts = now
                        self._rpm_display = float(raw)
                        return self._rpm_display

                    dt = now - self._rpm_last_ts
                    dt = min(0.5, max(0.001, dt))
                    self._rpm_last_ts = now

                    alpha = 1.0 - math.exp(-dt / self._rpm_ema_tau)
                    self._rpm_display += alpha * (float(raw) - self._rpm_display)
                    return self._rpm_display

                except Exception as e:
                    self.logger.error(f'RPM conditioning error: {e}', exc_info=True)
                    return raw

        EDIT 3 — replace the band-selection body of _get_band_colour
        (manager.py:540-579). Keep the def line, the docstring and the
        trailing except clause EXACTLY as they are. Replace only the body of
        the try block — that is, the lines from "bands = self.config.rpm_bands"
        through "return (bg_colour, text_colour)" — with:

                    bands = self.config.rpm_bands

                    # Ordered band table: (bg_colour, text_colour).
                    # Index 1 text corrected to white — WCAG 2.1 contrast on
                    # pure blue is 2.44:1 with black, 8.59:1 with white
                    # (display review §7.1, recommendation 23).
                    palette = (
                        ((0, 0, 0), (255, 255, 255)),        # 0 idle
                        ((0, 0, 255), (255, 255, 255)),      # 1 torque approach
                        ((0, 255, 0), (0, 0, 0)),            # 2 torque
                        ((255, 255, 0), (0, 0, 0)),          # 3 caution
                        ((255, 128, 0), (0, 0, 0)),          # 4 warning
                        ((255, 0, 0), (0, 0, 0)),            # 5 danger
                    )

                    # Ascending thresholds; threshold[i] separates band i from i+1.
                    thresholds = (
                        bands.idle_max,
                        bands.torque_start,
                        bands.caution_start,
                        bands.warning_start,
                        bands.danger_start,
                    )

                    # Clamp the hysteresis margin below half the narrowest gap so
                    # a closely spaced RPMBands cannot make a band unreachable.
                    gaps = [
                        thresholds[i + 1] - thresholds[i]
                        for i in range(len(thresholds) - 1)
                    ]
                    narrowest = min(gaps) if gaps else self._band_hysteresis
                    margin = min(self._band_hysteresis, 0.49 * narrowest)

                    # Sticky selection: at most one step per call, and only when
                    # the value clears the threshold by the margin in the
                    # direction of travel.
                    band = self._active_band
                    if band < len(thresholds) and rpm > thresholds[band] + margin:
                        band += 1
                    elif band > 0 and rpm < thresholds[band - 1] - margin:
                        band -= 1

                    self._active_band = band
                    bg_colour, text_colour = palette[band]

                    return (bg_colour, text_colour)

        EDIT 4 — _get_shift_cue (manager.py:581). Replace the single line

            flash = int(time.monotonic() * 2) % 2 == 0

        (currently manager.py:595) with:

                    # Flash phase from the frame counter, not wall-clock time, so
                    # the duty cycle is equal by construction at any frame rate
                    # (display review §4.4, recommendation 5).
                    half_period = max(1, int(round(self.config.fps_limit / 4.0)))
                    flash = (self._frame_counter // half_period) % 2 == 0

        Change nothing else in the method. The three RPM branches, their
        colours and the border width of 12 remain as they are.

        EDIT 5a — _display_loop. Immediately after the existing line

            self.thread_manager.update_heartbeat('display')

        (currently manager.py:415) add:

                        self._frame_counter += 1

        EDIT 5b — _draw_digital_mode. In the simulation branch, replace

            rpm = int(3000 + 3000 * math.sin(time.time()))
            self._last_rpm = rpm

        with

            rpm = int(3000 + 3000 * math.sin(time.time()))
            self._last_rpm = rpm
            rpm = self._condition_rpm(rpm)

        and in the live branch, replace

            rpm = getattr(self, '_last_rpm', 0)

        with

            rpm = self._condition_rpm(getattr(self, '_last_rpm', 0))

        EDIT 5c — _draw_radial_mode. Apply the identical two substitutions to
        that method's simulation branch and its "rpm = getattr(self,
        '_last_rpm', 0)" line.

        Note on EDIT 5: self._last_rpm is assigned the RAW value in both
        methods and must remain so. Only the local variable rpm is
        conditioned.

        Confirm at the top of the file that `math` and `time` are already
        imported. Both are. Add no new import.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "pytest tests/ passes with no new failures."
  - "DisplayManager.__init__ defines _rpm_display, _rpm_ema_tau, _rpm_last_ts, _active_band, _band_hysteresis and _frame_counter."
  - "_condition_rpm exists, seeds on first call, clamps dt to [0.001, 0.5] and returns raw inside its except clause."
  - "_get_band_colour returns ((0,0,255), (255,255,255)) for the torque-approach band."
  - "_get_band_colour reads and writes self._active_band and applies at most one band step per call."
  - "The string 'int(time.monotonic() * 2)' no longer appears anywhere in manager.py."
  - "_get_shift_cue computes flash from self._frame_counter and self.config.fps_limit."
  - "self._frame_counter is incremented exactly once per display loop iteration."
  - "_draw_digital_mode and _draw_radial_mode each call _condition_rpm in both the simulation and live branches."
  - "grep confirms self._last_rpm is assigned only the raw value; no assignment of a conditioned value to it exists."
  - "No file other than src/gtach/display/manager.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "models"
        path: "src/gtach/display/models.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "RPMBands"
        module: "gtach.display.models"
      - name: "DisplayConfig"
        module: "gtach.display.models"
    functions:
      - name: "_condition_rpm"
        module: "gtach.display.manager"
        signature: "_condition_rpm(self, raw: float) -> float"
      - name: "_get_band_colour"
        module: "gtach.display.manager"
        signature: "_get_band_colour(self, rpm: float) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]"
      - name: "_get_shift_cue"
        module: "gtach.display.manager"
        signature: "_get_shift_cue(self, rpm: float) -> Tuple[Tuple[int, int, int], int, bool, Tuple[int, int, int]]"
    constants:
      - name: "idle_max"
        module: "gtach.display.models"
        type: "int"
      - name: "torque_start"
        module: "gtach.display.models"
        type: "int"
      - name: "caution_start"
        module: "gtach.display.models"
        type: "int"
      - name: "warning_start"
        module: "gtach.display.models"
        type: "int"
      - name: "danger_start"
        module: "gtach.display.models"
        type: "int"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-4c038bed-rpm-signal-conditioning.md

  After implementation, carry out the simulation-mode observation recorded
  as ai/task.md §7.5.2 before proceeding to any framebuffer change. If the
  flicker resolves, tasks 7.3.4 and possibly 7.3.2 reduce from fault
  correction to efficiency work.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-4c038bed. |
| 1.1 | 2026-07-30 | Executed by Claude Code. All five edits applied; all twelve success criteria met. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
