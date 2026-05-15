Created: 2026 May 15

```yaml
# T02 Change

change_info:
  id: "change-e4b7c3a1"
  title: "Shift cue display: implement gear shift visual indicators and improve radial mode legibility"
  date: "2026-05-15"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e4b7c3a1"
    issue_iteration: 1

source:
  type: "enhancement"
  reference: "issue-e4b7c3a1"
  description: >
    Implement directional shift cues in radial display mode.
    Remove danger-zone background flash. Increase border, tick, and numeral sizes.

scope:
  summary: >
    Two files modified: manager.py (shift cue logic, border, ticks, numerals)
    and typography.py (no change required — 52 px is within MAX_FONT_SIZE 180).
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  out_of_scope:
    - "Digital and gauge display modes"
    - "engine_profiles.yaml threshold values"
    - "Setup wizard"

rational:
  problem_statement: >
    GTach's primary purpose is gear shift cueing. The current display provides
    no directional shift information to the driver.
  proposed_solution: >
    Replace the undirected danger-zone flash with two shift cues and a normal state
    encoded as border colour and centre circle behaviour. Increase border and
    tick/numeral sizes for in-vehicle legibility.
    Red unsafe downshift cue dropped — RPM alone is insufficient to determine
    downshift safety without gear/speed data.
  benefits:
    - "Driver receives explicit upshift and downshift cues"
    - "Cues are peripheral-vision-compatible (border + centre flash)"
    - "Thresholds are engine-profile-specific via existing RPMBands"
    - "Larger border and numerals improve legibility at driving distance"

technical_details:
  current_behavior: >
    _draw_radial_mode(): static red border 4 px, ticks 20 px/5 px, numerals 40 px.
    _get_band_colour(): 2 Hz black background flash when RPM >= danger_start.
    _draw_circular_border(): hardcoded red (200,0,0), width 4.
  proposed_behavior: >
    Shift cue states:
      1. Upshift:       RPM >= caution_start → green border 12 px + green/black centre flash 2 Hz
      2. Safe downshift: RPM <= torque_start → blue border 12 px + blue centre fill, no flash
      3. Normal:        otherwise            → dark border 5 px, dark centre fill, no cue

    Border: 12 px (shift states), 5 px (normal). Ticks: 28 px long, 7 px wide.
    Numerals: 52 px, 58 px inset.
    Danger-zone background flash removed from _get_band_colour().
    _draw_circular_border() replaced by _draw_shift_border(colour, width).
  implementation_approach: >
    1. Remove danger flash block from _get_band_colour().
    2. Replace _draw_circular_border() with _draw_shift_border(colour, width=12).
    3. Add _get_shift_cue(rpm) -> (border_colour, border_width, flash_centre, centre_colour).
    4. In _draw_radial_mode():
       - Replace step 6 border call with _draw_shift_border() using cue values.
       - Update step 8 tick length 20->28, width 5->7, numeral font 40->52, inset 42->58.
       - Replace steps 12-14 centre logic with shift cue centre logic.
    5. Update all call sites of _draw_circular_border() to _draw_shift_border()
       with appropriate colour (red for setup/settings fallback, retain existing behaviour).
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "Shift cue logic, border refactor, tick/numeral size increase"
      functions_affected:
        - "_get_band_colour"
        - "_draw_circular_border"
        - "_draw_shift_border"
        - "_get_shift_cue"
        - "_draw_radial_mode"
        - "_draw_digital_mode"
        - "_draw_settings_mode"
        - "_draw_setup_mode_fallback"

testing_requirements:
  test_approach: "Manual verification via --transport simbt on Pi"
  test_cases:
    - scenario: "RPM <= torque_start (<=3000)"
      expected_result: "Blue border 12 px, blue centre fill, no flash"
    - scenario: "RPM between torque_start and caution_start (3001-4499)"
      expected_result: "Dark border 5 px, dark centre, no cue"
    - scenario: "RPM >= caution_start (>=4500)"
      expected_result: "Green border 12 px, green/black centre flash at 2 Hz"
  validation_criteria:
    - "All three RPM states produce correct border colour and width"
    - "Flash state cycles at approximately 2 Hz"
    - "No background flash in any band"
    - "Tick marks and numerals visibly larger than before"
    - "Border visibly thicker in shift cue states"

version_history:
  - version: "1.0"
    date: "2026-05-15"
    author: "William Watson"
    changes:
      - "Initial change creation"
  - version: "1.1"
    date: "2026-05-15"
    author: "William Watson"
    changes:
      - "Removed red unsafe downshift cue — RPM alone cannot determine downshift safety"
      - "Simplified to two cue states: upshift (green) and safe downshift (blue)"
      - "Normal state uses dark border 5 px, no cue"

metadata:
  copyright: "Copyright (c) 2026 William Watson. This work is licensed under the MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
