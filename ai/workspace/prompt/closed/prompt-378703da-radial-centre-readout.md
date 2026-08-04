Created: 2026 August 04

# Prompt: Put the Number in the Centre of the Gauge and Retire DIGITAL

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-378703da"
  task_type: "implementation"
  source_ref: "change-378703da"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-378703da"
    change_iteration: 1

context:
  purpose: >
    RADIAL is the default display mode and does not show the RPM
    number. Its centre disc — the largest uninterrupted region of the
    gauge — renders the fixed string 'GTach'. The number exists only in
    DIGITAL, which is reachable only by an unadvertised horizontal
    swipe, and which the operator is silently returned to every time
    they leave the options screen. Adding the numeral to RADIAL makes it
    a superset of DIGITAL, after which DIGITAL and the machinery that
    existed to reach it are removed.
  integration: >
    Four files: src/gtach/display/manager.py,
    src/gtach/display/models.py, src/gtach/utils/config.py and
    config/config.yaml. Executor is Claude Code; AEL is not used.

    SCOPE IS DIRECTED, NOT CONDITIONAL. The source report says
    "consider retiring DIGITAL". ai/task.md §7.3.14 resolves that as
    accepted. Retire it. Do not add the mode indicator the report
    offers as its alternative resolution — display §7.6 is closed by
    the retirement.

    ORDER MATTERS. Do the six steps in the order given. RADIAL must
    gain the numeral before DIGITAL is removed, so the tree is never in
    a state where neither mode shows the number.

    LINE NUMBERS. ai/task.md §7.3.14 cites manager.py:142-172 for the
    swipe handlers and manager.py:1091 for the mode selector. Both
    predate the current file. At 0.3.2 the handlers are at
    manager.py:167-197 and the selector at manager.py:1423-1461.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py, src/gtach/display/models.py, src/gtach/utils/config.py and config/config.yaml."
    - "Do NOT delete _get_band_colour (manager.py:616-678). It becomes uncalled by this change and it MUST survive: task 7.3.11 requires its hysteresis logic, which change-4c038bed added. Add the retention comment specified in EDIT 6."
    - "Do NOT remove or alter the long-press callback registration in _setup_touch_callbacks. It is the only route to OPTIONS. It sits beside the two swipe registrations you are removing — this is the most dangerous edit in the task."
    - "Do NOT remove _handle_long_press itself. Only its DIGITAL assignment at manager.py:204 changes."
    - "Do NOT modify _condition_rpm (manager.py:581) or _get_shift_cue (manager.py:680)."
    - "Do NOT touch _register_rpm_sliders (manager.py:1463), _render_slider_visuals (1489) or _register_save_button (1519). Also unreachable, also not in scope."
    - "Do NOT rewrite any configuration file at runtime. The migration is read-side only."
    - "Do NOT remove DisplayMode.SPLASH, OPTIONS or ACKNOWLEDGEMENT."
    - "Do NOT remove TypographyConstants.FONT_RPM_LARGE. Out of scope even though its only consumer goes."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Render the conditioned RPM in the RADIAL centre disc in place of
    'GTach'. Remove _draw_digital_mode, _handle_swipe_left,
    _handle_swipe_right and _render_mode_selector, with their
    registrations and dispatch arms. Return to RADIAL when leaving
    OPTIONS. Remove DisplayMode.DIGITAL and map a persisted DIGITAL to
    RADIAL on read.
  requirements:
    functional:
      - "The RADIAL centre disc renders the conditioned RPM formatted as f\"{rpm/1000:.1f}\"."
      - "The numeral is white."
      - "The string 'GTach' does not appear in _draw_radial_mode."
      - "DisplayMode has no DIGITAL member."
      - "No reference to DisplayMode.DIGITAL remains anywhere in src/gtach."
      - "_draw_digital_mode, _handle_swipe_left, _handle_swipe_right and _render_mode_selector are absent."
      - "_setup_touch_callbacks registers the long press and everything else it registers today, and neither swipe handler."
      - "_handle_long_press sets RADIAL when leaving OPTIONS."
      - "A config.yaml carrying mode: DIGITAL loads and yields RADIAL, with a log line, and does not raise."
      - "utils/config.py DisplayConfig.from_dict defaults mode to 'RADIAL'."
      - "config/config.yaml carries display.mode: RADIAL."
      - "_get_band_colour is present and functionally unmodified."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Net reduction. One render_text call replaces another in RADIAL; DIGITAL's 180 px rasterisation is removed from the application entirely"
      metric: "time"

design:
  architecture: >
    One normal display mode. The gauge shows the arc, the indicator and
    the number, so nothing is lost by removing the mode that showed only
    the number. A retired enum member is removed rather than aliased,
    and the values already written to disk under the old name are
    translated when they are read, not by editing the operator's files.
  components:
    - name: "DisplayManager._draw_radial_mode"
      type: "function"
      purpose: "Render the gauge, now including the numeric readout."
      logic:
        - "At the centre-label site (manager.py:980-985), render the RPM instead of 'GTach'."
        - "Format f\"{rpm/1000:.1f}\" — the same format DIGITAL used, so the displayed resolution is unchanged."
        - "White text, as the current label already is."
        - "Font size 72 via self._get_cached_font(72). The r=99 disc admits a chord of 198 px; three glyphs at 72 px measure roughly 120 px wide and 72 tall, comfortably inside it. Do NOT use FONT_RPM_LARGE (180) — it does not fit."
    - name: "DisplayManager._render_normal_modes"
      type: "function"
      purpose: "Dispatch without DIGITAL."
      logic:
        - "Remove the DIGITAL arm at manager.py:548-549."
        - "Leave the DISCONNECTED precedence check at 542-546 exactly as it is."
    - name: "DisplayManager._setup_touch_callbacks"
      type: "function"
      purpose: "Register the gestures that remain."
      logic:
        - "Remove only the two swipe-handler registrations."
        - "Preserve the long-press registration and every other registration in the method."
    - name: "DisplayManager._handle_long_press"
      type: "function"
      purpose: "Enter and leave OPTIONS."
      logic:
        - "manager.py:204: DisplayMode.DIGITAL becomes DisplayMode.RADIAL."
        - "Also reset self._options_view = 'menu' on exit, so a sub-view is not waiting on the next entry."
    - name: "DisplayManager._load_config"
      type: "function"
      purpose: "Migrate a persisted DIGITAL."
      logic:
        - "Before the DisplayMode[saved_mode_str] lookup at manager.py:279, add an explicit branch mapping the literal 'DIGITAL' to RADIAL with an INFO log line."
        - "Leave the KeyError fallback at 284-286 in place — it is the net for any other unknown string."
        - "Leave the transient-mode rejection at 281-283 unchanged."
    - name: "DisplayMode"
      type: "class"
      purpose: "One fewer member."
      logic:
        - "Remove the DIGITAL line at models.py:65."
        - "auto() renumbers the remaining members. Nothing persists the integer value — _save_config writes mode.name (manager.py:361) — so the renumbering is safe. Confirm this rather than assuming it."
  dependencies:
    internal:
      - "_condition_rpm — manager.py:581. Supplies the value. Unmodified."
      - "_get_shift_cue — manager.py:680. Supplies the disc fill the numeral sits on. Unmodified."
      - "_get_band_colour — manager.py:616. Becomes uncalled; retained for 7.3.11."
    external: []

error_handling:
  strategy: >
    The migration must not be able to prevent startup. A configuration
    value naming a mode that no longer exists is expected, not
    exceptional, and is logged at INFO rather than WARNING because it is
    the anticipated state of every system upgrading to this release.
  exceptions:
    - exception: "KeyError"
      condition: "DisplayMode[saved_mode_str] for any unrecognised string."
      handling: "Existing handler at manager.py:284-286 — warn and use RADIAL. Unchanged."
    - exception: "Exception"
      condition: "Anything in _draw_radial_mode."
      handling: "Existing handler at manager.py:989-990. Unchanged."
  logging:
    level: "INFO for the DIGITAL migration; WARNING retained for genuinely unknown modes"
    format: "self.logger.info('Display mode DIGITAL was retired in v0.4.0; using RADIAL, which now shows the numeric readout')"

testing:
  unit_tests:
    - scenario: "_draw_radial_mode at rpm 3456."
      expected: "render_text called at (240, 240) with '3.5'."
    - scenario: "_draw_radial_mode at rpm 0."
      expected: "'0.0' rendered; no exception."
    - scenario: "grep 'GTach' in _draw_radial_mode."
      expected: "No occurrence."
    - scenario: "Numeral colour against each of the four fills _get_shift_cue returns — (0,160,0), (10,10,10), (0,40,100), (26,26,26)."
      expected: "White in every case. Compute and record the WCAG contrast for each; all four must exceed 3:1 for large text."
    - scenario: "DisplayMode member list."
      expected: "SPLASH, RADIAL, OPTIONS, ACKNOWLEDGEMENT. No DIGITAL."
    - scenario: "grep 'DIGITAL' across src/gtach."
      expected: "No occurrence."
    - scenario: "_load_config against a temporary config.yaml with mode: DIGITAL."
      expected: "_post_splash_mode is RADIAL; the INFO line is emitted; no exception."
    - scenario: "_load_config with mode: RADIAL."
      expected: "RADIAL; no migration line."
    - scenario: "_load_config with mode: NONSENSE."
      expected: "RADIAL; the existing unknown-mode WARNING."
    - scenario: "_load_config with mode: OPTIONS."
      expected: "RADIAL, via the transient-mode rejection."
    - scenario: "_load_config with no file present."
      expected: "Defaults unchanged from today."
    - scenario: "_save_config after a migrated load."
      expected: "Writes RADIAL."
    - scenario: "_setup_touch_callbacks."
      expected: "Long press registered. Assert every other callback registered today is still registered, individually and by name."
    - scenario: "_handle_long_press entering then leaving OPTIONS."
      expected: "RADIAL on exit; _options_view is 'menu'."
    - scenario: "_render_normal_modes for RADIAL, OPTIONS, ACKNOWLEDGEMENT and the disconnected condition."
      expected: "Correct dispatch in each case."
    - scenario: "_get_band_colour called directly with a sweep across every threshold."
      expected: "Identical results to the pre-change implementation, including hysteresis behaviour."
  edge_cases:
    - "A saved config.yaml written by a pre-change build immediately before the upgrade — the ordinary case on every deployed unit. Covered by the DIGITAL migration test."
    - "config/config.yaml's display.mode and the display's own config.yaml are different files read by different code paths. Both must be handled; do not assume correcting one covers the other."
    - "The numeral at 7000 RPM renders '7.0' — three glyphs. At a hypothetical 10000+ it would be four and could overflow the disc; the value is clamped to 7000 at manager.py:810, so this cannot occur. Note it rather than guarding it."
    - "The centre disc flashes above caution_start (manager.py:697-703). The numeral must be drawn after the disc fill in both flash phases, not only the lit one."
  validation:
    - "grep confirms 'DIGITAL' appears nowhere in src/gtach."
    - "grep confirms _get_band_colour is still defined."
    - "git diff confirms the long-press registration in _setup_touch_callbacks is unchanged."

deliverable:
  format_requirements:
    - "Edit the four files in place. Create no new file."
    - "Follow the existing convention of citing the review section in a comment where a change is motivated by one."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        SIX EDITS, IN THIS ORDER.

        EDIT 1 — the centre readout. In _draw_radial_mode, replace the
        block at manager.py:979-985:

            # Draw 'GTach' label in centre circle (always white text)
            gtach_font = self._get_cached_font(42)
            if gtach_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, "GTach", gtach_font,
                    (255, 255, 255), center, center=True
                )

        with:

            # The numeric readout. The centre disc is the largest
            # uninterrupted region of the gauge and the point of highest
            # visual acuity for a centred gaze; it previously carried a
            # fixed brand string while the number the instrument exists
            # to show appeared only in DIGITAL (display review §7.5,
            # recommendation 25). White on every fill _get_shift_cue
            # returns, including the flashing dark phase.
            readout_font = self._get_cached_font(72)
            if readout_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, f"{rpm/1000:.1f}",
                    readout_font, (255, 255, 255), center, center=True
                )

        72 px, not FONT_RPM_LARGE's 180: the disc is r=99 and 180 px
        glyphs do not fit inside it.

        EDIT 2 — remove _draw_digital_mode (manager.py:715-786) in full,
        and its dispatch arm in _render_normal_modes at
        manager.py:548-549:

            if self.config.mode == DisplayMode.DIGITAL:
                self._draw_digital_mode()
            elif self.config.mode == DisplayMode.RADIAL:

        becomes:

            if self.config.mode == DisplayMode.RADIAL:

        Leave the DISCONNECTED precedence check at manager.py:542-546
        exactly as it is.

        EDIT 3 — remove _handle_swipe_left (manager.py:167-181) and
        _handle_swipe_right (183-197) in full, and their two
        registrations in _setup_touch_callbacks (150-166).

        READ THE WHOLE OF _setup_touch_callbacks BEFORE EDITING IT.
        Remove only the two swipe registrations. The long-press
        registration is in the same method and is the only route to the
        OPTIONS screen; removing it strands the operator. Every other
        registration in that method survives.

        EDIT 4 — remove _render_mode_selector (manager.py:1423-1461) in
        full. It is defined and never called; it registers touch
        regions, so leaving it would be a live hazard if anything ever
        called it after DIGITAL is gone.

        EDIT 5 — _handle_long_press. At manager.py:202-210:

            if self.config.mode == DisplayMode.OPTIONS:
                # Exit options mode
                self.config.mode = DisplayMode.DIGITAL

        becomes:

            if self.config.mode == DisplayMode.OPTIONS:
                # Exit options mode. Returns to RADIAL, the only normal
                # mode after DIGITAL's retirement. Previously this
                # forced DIGITAL regardless of the mode in use before
                # OPTIONS was entered.
                self.config.mode = DisplayMode.RADIAL
                self._options_view = 'menu'

        EDIT 6 — the migration and the retention comment.

        (a) In _load_config, immediately before the try block at
        manager.py:278-286, insert:

            # DIGITAL was retired in v0.4.0 (display review §7.5/§7.6,
            # recommendation 25; ai/task.md §7.3.14). Every system
            # upgrading from an earlier build has it persisted, so this
            # is the expected case rather than an error. RADIAL now
            # shows the numeric readout DIGITAL existed for.
            if saved_mode_str == 'DIGITAL':
                self.logger.info(
                    "Display mode DIGITAL was retired; using RADIAL, "
                    "which now shows the numeric readout"
                )
                saved_mode_str = 'RADIAL'

        Leave the KeyError fallback and the transient-mode rejection
        below it exactly as they are.

        (b) Add a retention comment above _get_band_colour
        (manager.py:616):

            # RETAINED DELIBERATELY. This method has no caller after
            # DIGITAL's retirement (change-378703da) and a dead-code
            # analysis will correctly report it as unreachable. It is
            # kept because task 7.3.11 (change-5014040c, the annular
            # band indicator) requires exactly this band selection,
            # including the hysteresis added by change-4c038bed. Do not
            # remove it before that change lands.
    - path: "src/gtach/display/models.py"
      content: |
        Remove the DIGITAL member at models.py:65:

            DIGITAL = auto()          # Digital RPM display mode

        The remaining members renumber, which is safe: _save_config
        persists mode.name (manager.py:361), not the integer, and
        _load_config resolves by name. Verify that no code compares a
        DisplayMode to an integer before relying on this.

        Update the RADIAL comment at models.py:66 to record that it is
        now the only normal display mode and carries the numeric
        readout.
    - path: "src/gtach/utils/config.py"
      content: |
        At utils/config.py:588, in DisplayConfig.from_dict:

            mode=data.get("mode", "DIGITAL"),

        becomes:

            mode=data.get("mode", "RADIAL"),

        Change nothing else in this file. Note that this DisplayConfig
        is a different class from display/models.py's DisplayConfig and
        stores the mode as a string; it is not the one DisplayManager
        uses at runtime. Both are corrected because both carry the
        retired default.
    - path: "config/config.yaml"
      content: |
        Under the display: key, change:

            mode: DIGITAL

        to:

            mode: RADIAL

        Change nothing else in the file. Deployed configuration files
        are NOT rewritten by this change — EDIT 6(a) handles those on
        read.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/display/models.py src/gtach/utils/config.py passes."
  - "config/config.yaml parses as valid YAML and carries display.mode: RADIAL."
  - "pytest tests/ passes with no new failures."
  - "grep -r 'DIGITAL' src/gtach returns no match."
  - "DisplayMode has exactly four members: SPLASH, RADIAL, OPTIONS, ACKNOWLEDGEMENT."
  - "_draw_radial_mode renders f\"{rpm/1000:.1f}\" at the centre and does not render 'GTach'."
  - "_draw_digital_mode, _handle_swipe_left, _handle_swipe_right and _render_mode_selector are absent from manager.py."
  - "The long-press registration in _setup_touch_callbacks is byte-identical to its current text."
  - "Every callback registered by _setup_touch_callbacks before this change, other than the two swipe handlers, is still registered."
  - "_handle_long_press sets DisplayMode.RADIAL on OPTIONS exit."
  - "_load_config against mode: DIGITAL yields RADIAL and logs at INFO, without raising."
  - "_get_band_colour is present, functionally byte-identical, and carries the retention comment."
  - "_condition_rpm and _get_shift_cue are byte-identical to their current text."
  - "_register_rpm_sliders, _render_slider_visuals and _register_save_button are byte-identical to their current text."
  - "No file other than the four named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "models"
        path: "src/gtach/display/models.py"
      - name: "config"
        path: "src/gtach/utils/config.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "DisplayMode"
        module: "gtach.display.models"
      - name: "DisplayConfig"
        module: "gtach.utils.config"
    functions:
      - name: "_draw_radial_mode"
        module: "gtach.display.manager"
        signature: "_draw_radial_mode(self) -> None"
      - name: "_render_normal_modes"
        module: "gtach.display.manager"
        signature: "_render_normal_modes(self) -> None"
      - name: "_setup_touch_callbacks"
        module: "gtach.display.manager"
        signature: "_setup_touch_callbacks(self) -> None"
      - name: "_handle_long_press"
        module: "gtach.display.manager"
        signature: "_handle_long_press(self, start_pos, end_pos) -> TouchAction"
      - name: "_load_config"
        module: "gtach.display.manager"
        signature: "_load_config(self) -> None"
      - name: "_get_band_colour"
        module: "gtach.display.manager"
        signature: "_get_band_colour(self, rpm: float) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-378703da-radial-centre-readout.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  This is the largest behavioural change in v0.4.0 (ai/task.md §8.5).
  The on-target step is not a formality: deploy against the
  pre-upgrade configuration, which carries DIGITAL, and confirm the
  application starts rather than falling back. Then confirm the numeral
  is legible while the centre disc flashes above caution_start, which
  is the one lighting condition a static review cannot judge.

  Two things in this task are easy to get wrong and expensive to
  discover late. The first is removing the long-press registration
  along with the swipe registrations, which leaves no route to the
  options screen. The second is deleting _get_band_colour, which a
  correct dead-code analysis will recommend and which task 7.3.11
  depends on. Both are called out in the constraints; neither is a
  matter of judgement.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-378703da. |

---

Copyright (c) 2026 William Watson. MIT License.
