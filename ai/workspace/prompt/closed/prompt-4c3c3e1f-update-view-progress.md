Created: 2026 July 30

# Prompt: Animated Ring Indicator on the Update-Check View

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-4c3c3e1f"
  task_type: "code_generation"
  source_ref: "change-4c3c3e1f"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-4c3c3e1f"
    change_iteration: 1

context:
  purpose: >
    While the update check runs, the update sub-view shows the fixed
    string 'Checking…' and registers no control, so consecutive frames
    are identical and a running check cannot be told apart from a hung
    application. Add an animated indicator for the duration of the check.
  integration: >
    One file: src/gtach/display/manager.py. Two edits — one new private
    method and one call site. Executor is Claude Code; AEL is not used.

    IMPORTANT CONTEXT. The source report claims self._update_wheel is an
    unused spinner field. It is not. It holds the wheel filename returned
    by updater.find_available_update (assigned at manager.py:1339) and
    consumed by updater.stage_pending (manager.py:1349). Do not touch it.

    The report also claims the check is a network operation. It is not.
    updater.find_available_update (src/gtach/utils/updater.py:65-93)
    lists /opt/gtach/updates and CRC-checks each candidate wheel with
    zipfile testzip. The duration is still unpredictable from the
    operator's side, which is why the indicator is warranted.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py."
    - "Do NOT modify or read self._update_wheel. It is a live field holding a wheel filename, not a spinner."
    - "Do NOT modify src/gtach/utils/updater.py."
    - "Do NOT modify src/gtach/display/rendering/engine.py. Compose the indicator from the existing draw_circle."
    - "Do NOT add any instance attribute to DisplayManager.__init__. The animation is a pure function of self._frame_counter and self.config.fps_limit."
    - "Do NOT use time.monotonic, time.time or pygame.time in the new method. The timebase is the frame counter, per manager.py:694-698."
    - "Do NOT add, move or remove any touch region, and do not modify _register_update_view_regions."
    - "Do NOT change the status-string selection at manager.py:1234-1243, the button block at manager.py:1255-1271 or the hint text at manager.py:1273-1275."
    - "Draw the indicator only when self._update_status == 'checking'."
    - "Type hints on the new method; Google-style docstring; PEP 8."

specification:
  description: >
    Add DisplayManager._draw_update_spinner, an eight-dot ring whose
    highlighted dot advances with the frame counter, and call it from
    _draw_update_view while the check is in flight.
  requirements:
    functional:
      - "Eight dots are drawn, evenly spaced on a circle of radius 34 centred at (240, 270)."
      - "The first dot is at the top of the ring, at (240, 236)."
      - "Every dot has radius 6."
      - "Exactly one dot is highlighted per frame."
      - "The highlighted index is (self._frame_counter // step) % 8, where step = max(1, int(round(self.config.fps_limit / 8.0)))."
      - "At fps_limit 60 the step is 8 frames, so a revolution takes 64 frames, approximately 1.07 s."
      - "The indicator is drawn only when self._update_status == 'checking'."
      - "A drawing failure inside the indicator is logged and does not prevent the rest of _draw_update_view from rendering."
      - "No instance attribute is added and self._update_wheel is not referenced."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Eight draw_circle calls per frame, and only while a check is in flight"
      metric: "time"

design:
  architecture: >
    A stateless render helper. The animation phase is derived from the
    frame counter that _display_loop already advances at manager.py:451,
    which is the timebase change-4c038bed established for periodic
    display effects at manager.py:694-698. Nothing is stored between
    frames, so there is no state to reset when the view is entered or
    left.
  components:
    - name: "DisplayManager._draw_update_spinner"
      type: "function"
      purpose: "Draw an indeterminate progress indicator while an update check runs."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Draws eight circles on the back buffer."
        raises:
          - "None. Wrapped; logs at ERROR with exc_info."
      logic:
        - "Compute step = max(1, int(round(self.config.fps_limit / 8.0)))."
        - "Compute active = (self._frame_counter // step) % 8."
        - "For each i in range(8), compute the angle 2*pi*i/8 - pi/2 so index 0 is at the top."
        - "Place the dot at (240 + round(34*cos(angle)), 270 + round(34*sin(angle)))."
        - "Draw radius 6 in (255, 255, 255) when i == active, otherwise (90, 90, 110)."
    - name: "DisplayManager._draw_update_view"
      type: "function"
      purpose: "Call the indicator while the check is in flight."
      logic:
        - "After the status message is rendered and before the button block, call self._draw_update_spinner() when self._update_status == 'checking'."
        - "Change nothing else in the method."
  dependencies:
    internal:
      - "DisplayManager._frame_counter — read only; advanced in _display_loop at manager.py:451."
      - "DisplayConfig.fps_limit — read only; loaded at manager.py:298."
      - "RenderingEngine.draw_circle — display/rendering/engine.py:516; called from a new site, not modified."
    external:
      - "math — already imported at manager.py:18."

error_handling:
  strategy: >
    The indicator is decoration. A failure inside it must not prevent the
    status message, the buttons or the hint text from being drawn, so the
    body is wrapped and the exception is logged rather than propagated —
    the same convention as _draw_shift_border at manager.py:572-579.
  exceptions:
    - exception: "Exception"
      condition: "Any failure while computing the phase or issuing a draw call."
      handling: "self.logger.error with exc_info=True; return normally."
  logging:
    level: "ERROR"
    format: "self.logger.error(f'Update spinner error: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "48 frames at fps_limit 60 with _update_status 'checking'."
      expected: "All eight ring positions are highlighted at least once."
    - scenario: "Frame N against frame N + 8 at fps_limit 60."
      expected: "The highlighted index advances by exactly one, modulo eight."
    - scenario: "Frame N against frame N + 1 at fps_limit 60."
      expected: "The highlighted index is unchanged for seven of every eight consecutive pairs."
    - scenario: "fps_limit 30, 24 frames."
      expected: "The step is 4 frames; a revolution still takes 32 frames, approximately 1.07 s."
    - scenario: "_update_status set to 'idle', 'available', 'none', 'error' and 'pending' in turn."
      expected: "No spinner dot is drawn in any of the five."
    - scenario: "Distance from the viewport centre (240, 240) to the outermost spinner pixel."
      expected: "70 px — 30 px of centre offset plus 34 px ring radius plus 6 px dot radius — inside the 238 px viewport."
    - scenario: "Vertical extent of the ring against the status message and the hint text."
      expected: "Ring occupies y 230 to 310. The message is centred at y 180 in a 26 px font; the hint is at y 410. No overlap."
    - scenario: "draw_circle raises inside the spinner."
      expected: "Logged at ERROR with a traceback; the status message and hint text are still drawn."
    - scenario: "Render the view with _update_status 'available'."
      expected: "Install and cancel are drawn exactly as before this change; no dot is drawn."
  edge_cases:
    - "fps_limit below 8 — int(round(fps_limit / 8.0)) is 0 or 1, and max(1, ...) holds the step at 1 frame per step."
    - "_frame_counter is 0 on the first frame — active is 0, the top dot, which is a defined starting position."
    - "_update_status changes from 'checking' to 'available' between frames — the worker writes it, the next frame draws no spinner. No teardown is required because the helper holds no state."
    - "_frame_counter growing without bound — the modulo makes the value's magnitude irrelevant, as it already is for the shift-cue flash."
  validation:
    - "grep confirms _update_wheel appears at exactly the same four lines as before the change."
    - "grep confirms time.monotonic, time.time and pygame.time do not appear in _draw_update_spinner."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place. Create no new file."
    - "Apply the two edits below. Change nothing else."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        EDIT 1 — add _draw_update_spinner

        Place it immediately before _draw_update_view (currently at
        manager.py:1225).

            def _draw_update_spinner(self) -> None:
                """Draw an indeterminate progress ring while a check runs.

                Eight dots on a circle of radius 34 centred at (240, 270),
                with one highlighted. The highlighted index advances from
                self._frame_counter rather than from wall-clock time, so
                the rate is equal by construction at any frame rate — the
                same construction as the shift-cue flash phase
                (manager.py:694-698, change-4c038bed).

                The ring is 30 px below the viewport centre and its
                outermost pixel is 70 px from that centre, inside the
                238 px radius. It occupies y 230 to 310, which is clear of
                the status message at y 180 and of the hint text at y 410.
                No button is registered while the status is 'checking'
                (_register_update_view_regions), so nothing else occupies
                that band.

                Drawn only while _update_status is 'checking'. The caller
                applies that test.
                """
                try:
                    dot_count = 8
                    ring_radius = 34
                    dot_radius = 6
                    centre_x, centre_y = 240, 270

                    # One step per fps_limit/8 frames — a revolution in
                    # approximately 1.07 s for any fps_limit of 8 or
                    # more. Below that the max(1, ...) holds the step at
                    # one frame and the ring simply turns faster than
                    # once a second.
                    step = max(1, int(round(self.config.fps_limit / 8.0)))
                    active = (self._frame_counter // step) % dot_count

                    for index in range(dot_count):
                        # -pi/2 puts index 0 at the top of the ring.
                        angle = (2.0 * math.pi * index / dot_count) - (math.pi / 2.0)
                        dot_x = centre_x + int(round(ring_radius * math.cos(angle)))
                        dot_y = centre_y + int(round(ring_radius * math.sin(angle)))
                        colour = (255, 255, 255) if index == active else (90, 90, 110)
                        self.rendering_engine.draw_circle(
                            RenderTarget.BACK_BUFFER, colour, (dot_x, dot_y), dot_radius
                        )

                except Exception as e:
                    self.logger.error(f"Update spinner error: {e}", exc_info=True)

        EDIT 2 — call it from _draw_update_view

        The method currently reads, at manager.py:1245-1250:

                status_font = self._get_cached_font(26)
                if status_font:
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, msg, status_font, (255, 255, 255), (240, 180), center=True)

                center_x = 240
                button_font = self._get_cached_font(26)

        Insert the guarded call between the status message and the
        center_x assignment, so it reads:

                status_font = self._get_cached_font(26)
                if status_font:
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, msg, status_font, (255, 255, 255), (240, 180), center=True)

                # A check has no reportable progress — find_available_update
                # publishes no intermediate state — so the indicator is
                # indeterminate. It exists to distinguish a running check
                # from a stalled application (display review §7.8,
                # recommendation 28).
                if self._update_status == 'checking':
                    self._draw_update_spinner()

                center_x = 240
                button_font = self._get_cached_font(26)

        Change nothing else in _draw_update_view. In particular leave the
        status-string selection (manager.py:1234-1243), the button block
        (manager.py:1255-1271) and the hint text (manager.py:1273-1275)
        exactly as they are.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "pytest tests/ passes with no new failures."
  - "_draw_update_spinner exists and is called from exactly one site, guarded by _update_status == 'checking'."
  - "The helper issues exactly eight draw_circle calls per invocation."
  - "Exactly one of the eight uses the colour (255, 255, 255)."
  - "The highlighted index is derived from self._frame_counter, not from any clock."
  - "time.monotonic, time.time and pygame.time do not appear in _draw_update_spinner."
  - "No instance attribute is added to DisplayManager.__init__."
  - "self._update_wheel is neither read nor written by this change; its four occurrences at manager.py:76, 1324, 1339 and 1349 are unchanged."
  - "_register_update_view_regions is byte-identical to its current text."
  - "The status-string selection, the button block and the hint text in _draw_update_view are byte-identical to their current text."
  - "src/gtach/display/rendering/engine.py is unmodified."
  - "src/gtach/utils/updater.py is unmodified."
  - "No file other than src/gtach/display/manager.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "engine"
        path: "src/gtach/display/rendering/engine.py"
      - name: "updater"
        path: "src/gtach/utils/updater.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "DisplayRenderingEngine"
        module: "gtach.display.rendering.engine"
      - name: "RenderTarget"
        module: "gtach.display.rendering.engine"
    functions:
      - name: "_draw_update_spinner"
        module: "gtach.display.manager"
        signature: "_draw_update_spinner(self) -> None"
      - name: "_draw_update_view"
        module: "gtach.display.manager"
        signature: "_draw_update_view(self) -> None"
      - name: "draw_circle"
        module: "gtach.display.rendering.engine"
        signature: "draw_circle(self, target: RenderTarget, color: Tuple[int, int, int], center: Tuple[int, int], radius: int, width: int = 0) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-4c3c3e1f-update-view-progress.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  On-target confirmation is one tap. Stage a wheel with
  ./bin/deploy.sh --stage to exercise the 'available' path as well as
  the 'none' path, then tap OPTIONS then Check for updates.

  If the dots read as too small on the panel at 229 ppi, dot_radius and
  ring_radius are two constants in one method and the correction is a
  single edit. Increasing ring_radius beyond 60 would begin to encroach
  on the status message, so raise dot_radius first.

  Task 7.3.6 (9ed1c77e, recommendations 12 to 14) proposes skipping
  frames when nothing has changed. This indicator means the update view
  is always dirty while _update_status is 'checking'. That constraint is
  recorded in change-4c3c3e1f under dependencies.internal; ai/task.md
  §7.6.1 does not yet carry a row for it.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-4c3c3e1f. |
| 1.1 | 2026-07-31 | Executed by Claude Code. Both edits applied and all fourteen success criteria met, with no departure from the deliverable text required. 65 assertions against the real render path with a recording engine, all passing; pytest tests/ 11 passed. Finding §7.8 confirmed directly: 64 consecutive frames of the checking view were byte-identical before the change — one distinct frame — and comprise 8 distinct frames after. One error found in this document's test matrix: unit test 1 expects 48 frames at fps_limit 60 to highlight all eight positions, which contradicts the functional requirement fixing the step at 8 frames and the revolution at 64; 48 frames cover six positions. The implementation follows the requirement. Recorded in change-4c3c3e1f. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/; the issue and change remain active pending on-target results per ai/task.md §8.2.1. |

---

Copyright (c) 2026 William Watson. MIT License.
