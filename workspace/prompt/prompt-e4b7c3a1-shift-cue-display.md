Created: 2026 May 15

```yaml
# T04 Prompt

prompt_info:
  id: "prompt-e4b7c3a1"
  task_type: "code_generation"
  source_ref: "change-e4b7c3a1"
  date: "2026-05-15"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4b7c3a1"
    change_iteration: 1

context:
  purpose: >
    Implement directional gear shift visual cues in GTach radial display mode.
    Provide driver with green (upshift), red (unsafe downshift), and blue
    (safe downshift) border and centre circle indicators.
  integration: >
    All changes confined to src/gtach/display/manager.py.
    RPMBands thresholds sourced from self.config.rpm_bands (already loaded).
    No changes to typography.py, models.py, or engine_profiles.yaml.
  constraints:
    - "Do not modify any file other than manager.py"
    - "Do not change RPMBands field names or defaults"
    - "Preserve all existing display modes (digital, gauge, settings, setup)"
    - "Preserve _draw_status_indicator() unchanged"
    - "Flash uses time.monotonic() — already imported"

specification:
  description: >
    Refactor _draw_circular_border() into _draw_shift_border(colour, width=12).
    Add _get_shift_cue(rpm) returning (border_colour, flash_centre, centre_colour).
    Remove danger flash from _get_band_colour().
    Update _draw_radial_mode() tick/numeral sizes and shift cue rendering.
    Update all existing call sites of _draw_circular_border().
  requirements:
    functional:
      - "RPM >= caution_start: green border 12 px, centre flashes green/black at 2 Hz"
      - "RPM <= torque_start: blue border 12 px, blue centre fill (0,40,100), no flash"
      - "Otherwise (normal): dark border (170,0,0) width 5, dark centre fill (26,26,26), no flash"
      - "Remove 2 Hz background flash from _get_band_colour() danger zone"
      - "Border width 12 px for shift cue states, 5 px for normal state"
      - "Tick marks: length 28 px, width 7 px"
      - "Numerals: font size 52 px, inset 58 px from outer_radius"
    technical:
      language: "Python"
      standards:
        - "Thread-safe — no new shared state introduced"
        - "Error handling with logger.error() on all except blocks"
        - "Existing docstring style preserved"

design:
  architecture: "Modify existing methods in DisplayManager class"
  components:
    - name: "_get_shift_cue"
      type: "function"
      purpose: "Determine shift cue state from RPM"
      interface:
        inputs:
          - name: "rpm"
            type: "float"
            description: "Current RPM value"
        outputs:
          type: "Tuple[Tuple,int,bool,Tuple]"
          description: "(border_colour, border_width, flash_centre, centre_colour)"
      logic:
        - "Read self.config.rpm_bands"
        - "if rpm >= bands.caution_start: green border 12 px, flash centre green/black"
        - "elif rpm <= bands.torque_start: blue border 12 px, blue centre, no flash"
        - "else: dark border 5 px, dark centre, no flash"
        - "Flash state: int(time.monotonic() * 2) % 2 == 0"
        - "Return border_colour, border_width, flash_centre bool, centre_colour"

    - name: "_draw_shift_border"
      type: "function"
      purpose: "Draw circular border with given colour and width"
      interface:
        inputs:
          - name: "colour"
            type: "Tuple[int,int,int]"
            description: "RGB border colour"
          - name: "width"
            type: "int"
            description: "Border width in px (default 12)"
      logic:
        - "Get BACK_BUFFER surface"
        - "pygame.draw.circle(surface, colour, (240,240), 238, width)"

    - name: "_get_shift_cue (modified)"
      type: "function"
      purpose: "Radial arc display with shift cues"
      logic:
        - "Steps 1-5, 7, 9-11 unchanged"
        - "Step 6: call _draw_shift_border() with colour and width from _get_shift_cue()"
        - "Step 8 ticks: length=28, width=7; numerals: font=52, inset=58"
        - "Steps 12-14 centre: use flash_centre and centre_colour from _get_shift_cue()"
        - "Centre flash: if flash_centre True and flash on, use flash colour; else use base colour"
        - "GTach label: white (255,255,255) in all states"

    - name: "_get_band_colour (modified)"
      type: "function"
      purpose: "Background/text colour by RPM band — danger flash removed"
      logic:
        - "Remove the 2 Hz black flash block in the danger zone"
        - "Danger zone returns (255,0,0) bg and (0,0,0) text, no flash"

  dependencies:
    internal:
      - "self.config.rpm_bands (RPMBands)"
      - "self.rendering_engine (DisplayRenderingEngine)"
      - "time.monotonic()"

deliverable:
  format_requirements:
    - "Save changes directly to specified path"
  files:
    - path: "src/gtach/display/manager.py"
      content: "Modified in place — all changes within DisplayManager class"

success_criteria:
  - "_get_shift_cue() returns correct tuple for all three RPM states"
  - "_draw_shift_border() replaces _draw_circular_border() at all call sites"
  - "Radial mode border is green 12 px when RPM >= caution_start"
  - "Radial mode border is blue 12 px when RPM <= torque_start"
  - "Radial mode border is dark 5 px in normal range"
  - "Centre circle flashes at 2 Hz in upshift state only"
  - "No background flash in any band"
  - "Tick marks visibly longer/wider; numerals visibly larger"
  - "No regressions in digital, gauge, settings, or setup modes"

element_registry:
  source: "workspace/design/"
  entries:
    classes:
      - name: "DisplayManager"
        module: "src/gtach/display/manager.py"
    functions:
      - name: "_get_band_colour"
        module: "src/gtach/display/manager.py"
        signature: "(self, rpm: float) -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]"
      - name: "_draw_circular_border"
        module: "src/gtach/display/manager.py"
        signature: "(self) -> None"
      - name: "_draw_radial_mode"
        module: "src/gtach/display/manager.py"
        signature: "(self) -> None"
    constants:
      - name: "RPMBands.caution_start"
        module: "src/gtach/display/models.py"
        type: "int"
      - name: "RPMBands.danger_start"
        module: "src/gtach/display/models.py"
        type: "int"
      - name: "RPMBands.torque_start"
        module: "src/gtach/display/models.py"
        type: "int"
```

```yaml
tactical_brief: |
  File: src/gtach/display/manager.py

  1. REMOVE danger flash from _get_band_colour():
     Delete the block "if int(time.monotonic() * 2) % 2 == 0: bg_colour = (0,0,0) ..."
     Danger zone returns bg=(255,0,0), text=(0,0,0) unconditionally.

  2. REPLACE _draw_circular_border() with _draw_shift_border(colour, width=12):
     pygame.draw.circle(surface, colour, (240,240), 238, width)
     Update all call sites:
       - _draw_digital_mode(): _draw_shift_border((200,0,0), 5)
       - _draw_settings_mode(): _draw_shift_border((200,0,0), 5)
       - _draw_setup_mode_fallback(): _draw_shift_border((200,0,0), 5)

  3. ADD _get_shift_cue(self, rpm: float):
     bands = self.config.rpm_bands
     flash = int(time.monotonic() * 2) % 2 == 0
     if rpm >= bands.caution_start:
         centre = (0,160,0) if flash else (10,10,10)
         return (0,180,0), 12, True, centre
     elif rpm <= bands.torque_start:
         return (0,100,255), 12, False, (0,40,100)
     else:
         return (170,0,0), 5, False, (26,26,26)

  4. IN _draw_radial_mode():
     Step 6 border: replace pygame.draw.circle(surface,(170,0,0),center,border_radius,5)
       with border_colour, border_width, _, _ = self._get_shift_cue(rpm)
            self._draw_shift_border(border_colour, border_width)

     Step 8 ticks: change tick length 20->28, line width 5->7
       tick_start_x = center[0] + (outer_radius - 28) * math.cos(angle_rad)
       pygame.draw.line(..., 7)
     Step 8 numerals: _get_cached_font(52), inset 42->58
       num_x = center[0] + (outer_radius - 58) * math.cos(angle_rad)

     Steps 12-14 centre: replace flash logic with:
       _, _, flash_centre, centre_colour = self._get_shift_cue(rpm)
       pygame.draw.circle(surface, centre_colour, center, center_radius)
       (GTach label text_colour: white (255,255,255) always)

  Constraints:
    - No other files modified
    - Preserve all other display modes unchanged
    - Error handling: wrap new methods in try/except with logger.error()
```
