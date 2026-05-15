Created: 2026 May 15

```yaml
# T03 Issue

issue_info:
  id: "issue-e4b7c3a1"
  title: "Shift cue display: implement gear shift visual indicators and improve radial mode legibility"
  date: "2026-05-15"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4b7c3a1"
    change_iteration: 1

source:
  origin: "requirement_change"
  description: >
    Primary goal of GTach is to provide the driver with visible gear shift cues.
    Current danger-zone flash (background) does not encode shift direction.
    Border is too thin and tick marks/numerals too small for in-vehicle legibility.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "TypographyConstants"
      file_path: "src/gtach/display/typography.py"
  version: "current"

behavior:
  expected: >
    Radial mode displays two shift cues and a normal state:
    - Upshift (RPM >= caution_start): green border 12 px + green/black centre flash at 2 Hz.
    - Safe downshift (RPM <= torque_start): blue border 12 px + blue centre fill, no flash.
    - Normal (torque_start < RPM < caution_start): dark border 5 px, dark centre, no cue.
    Danger-zone background flash removed.
    Border width 12 px. Tick marks 28 px long, 7 px wide. Numerals 52 px font,
    positioned 58 px inset from outer radius.
  actual: >
    Single danger-zone red background flash only. No shift cues.
    Border 4 px. Ticks 20 px / 5 px. Numerals 40 px at 42 px inset.
  impact: "Driver receives no directional shift guidance during normal operation."

analysis:
  root_cause: >
    Shift cue logic was not part of the original display design.
    Border width and tick/numeral sizing were initial defaults not tuned for
    in-vehicle viewing distance.
  technical_notes: >
    _get_band_colour() contains the danger flash logic to be removed.
    _draw_radial_mode() draws the border (step 6), ticks and numerals (step 8),
    and centre circle (steps 13-14). Shift cue logic added here.
    _draw_circular_border() draws static red border — replaced by
    _draw_shift_border(colour, width) accepting colour and width arguments.
    Two shift states only: upshift (green) and safe downshift (blue).
    Red unsafe downshift cue dropped — RPM alone is insufficient to determine
    downshift safety without gear/speed data.

resolution:
  approach: "Modify manager.py and typography.py per change-e4b7c3a1."

version_history:
  - version: "1.0"
    date: "2026-05-15"
    author: "William Watson"
    changes:
      - "Initial issue creation"
  - version: "1.1"
    date: "2026-05-15"
    author: "William Watson"
    changes:
      - "Removed red unsafe downshift cue — RPM alone cannot determine downshift safety"
      - "Simplified to two cue states: upshift (green) and safe downshift (blue)"

metadata:
  copyright: "Copyright (c) 2026 William Watson. This work is licensed under the MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
