Created: 2026 August 04

# Prompt: Two Palettes Behind One Selector, Toggled by Double-Tap

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-5012004e"
  task_type: "implementation"
  source_ref: "change-5012004e"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-5012004e"
    change_iteration: 1

context:
  purpose: >
    The instrument's palette is fixed at full saturation and the
    HyperPixel's backlight cannot be reduced in software, so at night it
    is a bright light source in the driver's forward field of view with
    no operator control. Give every drawn colour a night variant behind
    one selector, with a manual toggle and a persisted choice.
  integration: >
    Two files: src/gtach/display/models.py and
    src/gtach/display/manager.py. Executor is Claude Code; AEL is not
    used.

    TWO PREREQUISITES. change-5014040c must have landed — it creates the
    FACE_ constants and the BAND_COLOURS table this change converts into
    palette fields. change-b02ed4ea must have landed — it establishes
    the three-control options budget that rules the menu out as the
    toggle's home. If either is absent, STOP and report.

    EXPLICITLY EXCLUDED. ai/task.md §7.3.14 rules out automatic
    switching: the target hardware has no ambient light sensor. Do not
    add one, and do not substitute a time-of-day heuristic, which is
    automatic switching under another name.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and src/gtach/display/models.py."
    - "Do NOT add automatic switching of any kind — no sensor, no clock, no heuristic."
    - "Do NOT add the toggle to the options menu. It carries three targets and all three are occupied; a fourth contradicts change-b02ed4ea's central constraint."
    - "Do NOT add a brightness slider or any continuous control. Two states."
    - "Do NOT derive NIGHT_PALETTE by scaling DAY_PALETTE. Author each colour. Scaling compresses the band colours toward one another and the band cue is the instrument's primary signal."
    - "DAY_PALETTE must carry exactly the values in use today, so day rendering is provably unchanged."
    - "Do NOT alter the hysteresis block in _get_band_colour (manager.py:643-670 as it stands after 5014040c). Only where it reads its colours changes."
    - "Do NOT gate the toggle anywhere but RADIAL. It must not fire in OPTIONS, ACKNOWLEDGEMENT, SPLASH or setup mode."
    - "Palette must be a frozen dataclass. A drawing path must not be able to mutate it."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Add a frozen Palette dataclass holding every colour the instrument
    draws, two instances, a selector on DisplayManager, a double-tap
    toggle gated to RADIAL with a transient on-screen confirmation, and
    persistence of the selection in config.yaml.
  requirements:
    functional:
      - "Palette is a frozen dataclass with a field for each of the six face colours, the six band colours, and the five shift-cue colours."
      - "DAY_PALETTE's field values are identical to the constants in use before this change."
      - "Every NIGHT_PALETTE colour has lower relative luminance than its day counterpart."
      - "Adjacent night band colours are separated by CIE76 delta-E >= 25."
      - "Every drawing site reads through self._palette; no colour literal remains at a drawing site."
      - "A double-tap in RADIAL toggles the palette, and in no other mode."
      - "A toggle shows 'Night' or 'Day' on the face for about two seconds."
      - "The selection is written to config.yaml as 'palette' and restored at startup."
      - "An absent palette key yields day mode with no warning; an unrecognised value yields day mode with a warning."
      - "No ambient-light, clock or automatic switching code exists."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Neutral. An attribute read replaces a constant read per drawing call"
      metric: "time"

design:
  architecture: >
    Every colour the instrument can draw lives in one frozen object.
    Choosing a palette is choosing which object to read. Because the
    object is frozen and complete, a third palette later is a third
    instance and not a third set of edits.
  components:
    - name: "Palette"
      type: "dataclass"
      purpose: "Hold every drawable colour."
      logic:
        - "@dataclass(frozen=True)."
        - "Fields: ground, track, tick, line, edge, label; bands as a Tuple of six; shift_border_caution, shift_centre_lit, shift_centre_dark, shift_border_normal, shift_centre_normal, shift_border_down, shift_centre_down — one per colour _get_shift_cue returns."
        - "A name field, 'day' or 'night', so persistence writes the palette's own identity rather than a separate flag."
    - name: "DisplayManager._palette"
      type: "attribute"
      purpose: "The active palette."
      logic:
        - "Initialised in __init__ to DAY_PALETTE, then overwritten by _load_config."
    - name: "DisplayManager._toggle_palette"
      type: "function"
      purpose: "Swap, notify, persist."
      logic:
        - "Swap _palette between DAY_PALETTE and NIGHT_PALETTE."
        - "Set self._palette_notice_until = time.monotonic() + 2.0."
        - "Call self._save_config()."
        - "Log at INFO."
    - name: "DisplayManager._handle_double_tap"
      type: "function"
      purpose: "The gesture handler."
      logic:
        - "Return TouchAction.NONE unless self.config.mode is RADIAL and not self._in_setup_mode."
        - "Otherwise call _toggle_palette and return TouchAction.SETTINGS_CHANGE."
  dependencies:
    internal:
      - "change-5014040c — prerequisite. Its FACE_ constants and BAND_COLOURS become Palette fields."
      - "change-b02ed4ea — prerequisite. Its three-control budget is why the toggle is a gesture."
      - "The gesture subsystem — display/input and the registrations in _setup_touch_callbacks (manager.py:150-166). Read-only."
    external: []

error_handling:
  strategy: >
    A palette fault must not stop the instrument drawing. An
    unrecognised persisted value falls back to day with a warning, as
    the mode does. A failure inside the toggle is logged and leaves the
    current palette in place.
  exceptions:
    - exception: "Exception"
      condition: "Anything in _toggle_palette, including the save."
      handling: "Log with a traceback; leave _palette as it was. A failed save must not leave the display in a state the configuration does not describe."
    - exception: "Exception"
      condition: "Anything in _handle_double_tap."
      handling: "Log and return TouchAction.NONE, matching the existing gesture handlers' convention at manager.py:179-181."
  logging:
    level: "INFO on toggle; WARNING on an unrecognised persisted value"
    format: "self.logger.info(f'Palette switched to {self._palette.name}')"

testing:
  unit_tests:
    - scenario: "DAY_PALETTE field by field against the constants in use before the change."
      expected: "Identical."
    - scenario: "A frame rendered in day mode, before and after."
      expected: "The same colours reach the same primitives."
    - scenario: "Relative luminance of every night field against its day counterpart."
      expected: "Lower in every case."
    - scenario: "CIE76 delta-E between each adjacent pair of night band colours."
      expected: ">= 25; record the six figures."
    - scenario: "Night tick against night ground."
      expected: ">= 4.5:1."
    - scenario: "Each night band colour against night ground."
      expected: ">= 3:1."
    - scenario: "Area-weighted night luminance across face, arc, ticks and centre, against day."
      expected: "< 25%."
    - scenario: "_toggle_palette from day, then from night."
      expected: "NIGHT_PALETTE then DAY_PALETTE; _save_config called each time."
    - scenario: "A frame immediately after a toggle."
      expected: "Night colours."
    - scenario: "_handle_double_tap in RADIAL."
      expected: "Toggles; returns SETTINGS_CHANGE."
    - scenario: "_handle_double_tap in OPTIONS, ACKNOWLEDGEMENT, SPLASH, and with _in_setup_mode set."
      expected: "No toggle; returns NONE in each case."
    - scenario: "The confirmation text."
      expected: "Rendered while within the two-second window; absent after."
    - scenario: "_save_config then _load_config round trip, night."
      expected: "NIGHT_PALETTE restored."
    - scenario: "_load_config with no palette key."
      expected: "DAY_PALETTE, no warning."
    - scenario: "_load_config with palette: twilight."
      expected: "DAY_PALETTE with a warning."
    - scenario: "_save_config raising, forced, during a toggle."
      expected: "Logged; _palette unchanged; no exception escapes."
    - scenario: "Attempting to set a field on a Palette instance."
      expected: "FrozenInstanceError — the dataclass is frozen."
    - scenario: "grep for sensor, ambient, datetime or localtime in the diff."
      expected: "No occurrence."
  edge_cases:
    - "A toggle during the shift-cue flash: the centre alternates between two palette colours, both of which must come from the same palette in a given frame. Read _palette once per frame rather than per call."
    - "A double-tap that the gesture subsystem also reports as two single taps — verify the subsystem's disambiguation rather than assuming it, since a stray single tap in RADIAL registers nothing today."
    - "config.yaml written by a build before this change has no palette key. That is the upgrade case and must be silent, not warned."
    - "If change-821919ce has landed, the static-layer cache must be invalidated on toggle. Verify a full redraw rather than a stale blit — cross-check D3 step 5. If it has not landed, note in the verification that the check was not applicable."
  validation:
    - "grep confirms no RGB tuple literal appears in _draw_radial_mode, _get_band_colour or _get_shift_cue."
    - "grep confirms Palette is declared frozen."
    - "git diff confirms the hysteresis block in _get_band_colour is unchanged."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "Cite the review section in a comment where a change is motivated by one."
  files:
    - path: "src/gtach/display/models.py"
      content: |
        Add, after the existing DisplayMode and ConnectionStatus
        declarations:

            @dataclass(frozen=True)
            class Palette:
                """Every colour the instrument draws.

                The HyperPixel 2.1 Round's backlight cannot be reduced in
                software, so the palette's own luminance is the only
                control over emitted light. Two instances exist; the
                operator chooses between them (display review §7.9,
                recommendation 29; ai/task.md §7.3.14).

                Frozen so a drawing path cannot mutate the active
                palette.
                """
                name: str
                ground: Tuple[int, int, int]
                track: Tuple[int, int, int]
                tick: Tuple[int, int, int]
                line: Tuple[int, int, int]
                edge: Tuple[int, int, int]
                label: Tuple[int, int, int]
                bands: Tuple[Tuple[int, int, int], ...]
                shift_border_caution: Tuple[int, int, int]
                shift_centre_lit: Tuple[int, int, int]
                shift_centre_dark: Tuple[int, int, int]
                shift_border_normal: Tuple[int, int, int]
                shift_centre_normal: Tuple[int, int, int]
                shift_border_down: Tuple[int, int, int]
                shift_centre_down: Tuple[int, int, int]

        Then two instances. DAY_PALETTE takes its values from the
        constants currently in manager.py — the six FACE_ constants and
        BAND_COLOURS introduced by change-5014040c, and the five colours
        returned by _get_shift_cue at manager.py:700-709. Copy them;
        do not retype them from memory, and do not adjust any of them.

        NIGHT_PALETTE is authored. Guidance, not a formula:
          - ground darker than day's (16, 16, 16) only marginally — it
            is already near black; (8, 8, 8) is sufficient.
          - tick and label reduced substantially: the ticks are the
            highest-contrast elements and the largest easy saving.
          - bands: preserve hue separation. Reduce value, not
            chroma, so that dimmed yellow and dimmed orange remain
            distinguishable. Verify with the delta-E test rather than
            by eye.
          - shift-cue colours reduced in proportion; the flashing pair
            must remain visibly a flash.

        Import Tuple in models.py if it is not already imported.

    - path: "src/gtach/display/manager.py"
      content: |
        FOUR EDITS.

        EDIT 1 — the selector. In __init__, after the existing display
        state is set up:

            # Active palette. The panel's backlight cannot be dimmed in
            # software, so this is the only control over emitted light
            # at night (display review §7.9, recommendation 29).
            self._palette = DAY_PALETTE
            self._palette_notice_until = 0.0

        Import Palette, DAY_PALETTE and NIGHT_PALETTE from .models
        alongside the existing DisplayMode import at manager.py:46.

        Remove the six FACE_ class constants and BAND_COLOURS that
        change-5014040c added; their values now live in DAY_PALETTE.

        EDIT 2 — route the drawing sites.

        In _draw_radial_mode, read the palette ONCE at the top:

            palette = self._palette

        then use palette.ground, palette.track, palette.tick,
        palette.line, palette.edge and palette.label at the eight sites
        5014040c established. Reading once per frame rather than per
        call matters: a toggle occurring mid-frame would otherwise draw
        half a frame in each palette.

        In _get_band_colour, the palette's bands tuple replaces
        BAND_COLOURS. The threshold, gap, margin and sticky-selection
        block is unchanged.

        In _get_shift_cue, the five literals at manager.py:700-709
        become the corresponding palette fields.

        EDIT 3 — the toggle.

        (a) _toggle_palette:

            def _toggle_palette(self) -> None:
                try:
                    self._palette = (
                        NIGHT_PALETTE if self._palette is DAY_PALETTE
                        else DAY_PALETTE
                    )
                    self._palette_notice_until = time.monotonic() + 2.0
                    self._save_config()
                    self.logger.info(
                        f'Palette switched to {self._palette.name}'
                    )
                except Exception as e:
                    self.logger.error(
                        f'Palette toggle error: {e}', exc_info=True
                    )

        (b) _handle_double_tap, following the shape of the gesture
        handlers that _handle_long_press uses:

            def _handle_double_tap(self, start_pos, end_pos) -> TouchAction:
                try:
                    if self._in_setup_mode:
                        return TouchAction.NONE
                    if self.config.mode != DisplayMode.RADIAL:
                        return TouchAction.NONE
                    self._toggle_palette()
                    return TouchAction.SETTINGS_CHANGE
                except Exception as e:
                    self.logger.error(f'Double tap handling error: {e}')
                    return TouchAction.NONE

        (c) Register it in _setup_touch_callbacks alongside the long
        press. Read that method first and follow its existing
        registration convention exactly. Do not disturb the long-press
        registration.

        (d) The confirmation. In _draw_radial_mode, after the centre
        readout:

            if time.monotonic() < self._palette_notice_until:
                notice_font = self._get_cached_font(24)
                if notice_font:
                    self.rendering_engine.render_text(
                        RenderTarget.BACK_BUFFER,
                        'Night' if palette is NIGHT_PALETTE else 'Day',
                        notice_font, palette.tick, (240, 330),
                        center=True
                    )

        EDIT 4 — persistence.

        In _save_config, add to the config_data dict at
        manager.py:360-367:

            'palette': self._palette.name,

        In _load_config, after the mode handling:

            palette_name = config_data.get('palette', 'day')
            if palette_name == 'night':
                self._palette = NIGHT_PALETTE
            elif palette_name == 'day':
                self._palette = DAY_PALETTE
            else:
                self.logger.warning(
                    f"Unknown palette '{palette_name}', using day"
                )
                self._palette = DAY_PALETTE

        An absent key yields 'day' through the default and warns
        nothing — that is every existing installation and is not an
        error.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/display/models.py passes."
  - "pytest tests/ passes with no new failures."
  - "Palette is declared @dataclass(frozen=True)."
  - "DAY_PALETTE's values are identical to the constants in use before this change."
  - "A day-mode frame passes the same colours to the same primitives as before the change."
  - "Every NIGHT_PALETTE colour has lower relative luminance than its day counterpart."
  - "Adjacent night band colours are separated by delta-E >= 25, with the figures recorded."
  - "No RGB tuple literal appears in _draw_radial_mode, _get_band_colour or _get_shift_cue."
  - "_draw_radial_mode reads self._palette exactly once per frame."
  - "A double-tap toggles in RADIAL and in no other mode or in setup."
  - "The selection round-trips through config.yaml."
  - "An absent palette key produces day mode and no warning."
  - "The hysteresis block in _get_band_colour is byte-identical to its current text."
  - "The long-press registration in _setup_touch_callbacks is byte-identical to its current text."
  - "No sensor, clock or automatic switching appears anywhere in the diff."
  - "No file other than the two named above is modified."

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
      - name: "Palette"
        module: "gtach.display.models"
    functions:
      - name: "_toggle_palette"
        module: "gtach.display.manager"
        signature: "_toggle_palette(self) -> None"
      - name: "_handle_double_tap"
        module: "gtach.display.manager"
        signature: "_handle_double_tap(self, start_pos, end_pos) -> TouchAction"
      - name: "_draw_radial_mode"
        module: "gtach.display.manager"
        signature: "_draw_radial_mode(self) -> None"
      - name: "_get_band_colour"
        module: "gtach.display.manager"
        signature: "_get_band_colour(self, rpm: float) -> Tuple[int, Tuple[int, int, int]]"
      - name: "_get_shift_cue"
        module: "gtach.display.manager"
        signature: "_get_shift_cue(self, rpm: float) -> Tuple[Tuple[int, int, int], int, bool, Tuple[int, int, int]]"
    constants:
      - name: "DAY_PALETTE"
        module: "gtach.display.models"
      - name: "NIGHT_PALETTE"
        module: "gtach.display.models"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-5012004e-night-palette-toggle.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  Check both prerequisites before starting. Without 5014040c the face
  colours are still scattered literals and this change becomes a much
  larger edit; without b02ed4ea the siting rationale does not hold.

  The night palette is the part that needs judgement rather than
  transcription. Reducing value while preserving hue separation is what
  keeps the band cue working in the condition the change exists for; a
  uniform scaling will pass every luminance assertion and fail the
  delta-E one, which is why that test is there.

  The on-target step is not optional. Whether six dimmed colours remain
  distinguishable on a 229 ppi panel at night, through a windscreen, is
  not something the delta-E figure settles on its own.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-5012004e. |

---

Copyright (c) 2026 William Watson. MIT License.
