Created: 2026 May 15

# Prompt: Add RADIAL RPM Display Mode

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Error Handling](<#5.0 error handling>)
- [6.0 Testing](<#6.0 testing>)
- [7.0 Deliverable](<#7.0 deliverable>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-e4f7a2c9"
  task_type: "code_generation"
  source_ref: "change-e4f7a2c9"
  date: "2026-05-15"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4f7a2c9"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Add a third RPM display mode RADIAL to GTach. The mode renders RPM
    as a swept donut arc on the 480x480 circular display. It sits
    alongside the existing DIGITAL and GAUGE modes and is accessible
    via the existing swipe gesture.
  integration: >
    DisplayMode enum in models.py gains a RADIAL value. DisplayManager
    in manager.py gains _draw_radial_mode(). Swipe gesture routing in
    manager.py and touch.py is updated to cycle all three modes.
  constraints:
    - "Linux/Pi only runtime. No macOS paths."
    - "pygame >= 2.0 drawing primitives only — no external libraries."
    - "All arc geometry must fit within the 480x480 circular display."
    - "Reuse existing RPMBands colour logic and _get_band_colour() pattern."
    - "Danger flash must use time.monotonic() consistent with existing code."
    - "Do not modify DIGITAL or GAUGE rendering."
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Implement DisplayMode.RADIAL and _draw_radial_mode() in GTach.
  requirements:
    functional:
      - "DisplayMode.RADIAL enum value added to models.py."
      - "Arc sweeps from 7 o'clock (210 deg clock) to 5 o'clock (150 deg clock) via top — 300 degree active sweep."
      - "Arc is a donut: outer radius 198px, inner radius 88px, centre (240, 240)."
      - "Filled region (0 to current RPM): coloured per RPMBands using _get_band_colour() bg_colour."
      - "Headroom region (current RPM to 7000 RPM): light grey RGB(96, 96, 96)."
      - "Lower inert arc (5 o'clock to 7 o'clock, short path, 60 degrees): dark grey RGB(28, 28, 28)."
      - "Lower inert arc carries 'RPM x 1000' label in red RGB(200, 0, 0) centered at approx (240, 395)."
      - "Centre circle (radius 87px, centre 240,240): dark RGB(26, 26, 26) background."
      - "Centre circle carries 'GTach' label in red RGB(200, 0, 0) centered at (240, 240)."
      - "Danger flash: when rpm >= config.rpm_bands.danger_start, centre circle background flashes between RGB(136,0,0) and RGB(10,10,10) at 2 Hz using time.monotonic()."
      - "Major graduation marks at 1000 RPM intervals (1000-7000): white RGB(220,220,220) radial line, 20px long, on outer arc edge."
      - "Major graduation numerals 1-7: white, font size 13, positioned 40px inward from outer radius along the mark angle."
      - "Band boundary marks at RPMBands thresholds (idle_max, torque_start, caution_start, warning_start, danger_start, redline_rpm): coloured radial lines 28px long, colours matching band start colours (blue, green, yellow, orange, red, red)."
      - "White indicator line at current RPM: spans full arc band width (inner radius to outer radius), line width 2.5px."
      - "Red circular border: RGB(170,0,0), radius 208px, line width 5px."
      - "Swipe gesture cycles DIGITAL -> GAUGE -> RADIAL -> DIGITAL."
      - "RADIAL persists to config file as a valid mode name."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe queue drain pattern consistent with _draw_digital_mode()."
        - "Comprehensive try/except with logger.error() on all rendering steps."
        - "Debug logging consistent with existing display methods."
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: >
    Single new method _draw_radial_mode() in DisplayManager. Arc geometry
    uses math.cos/sin with clock-angle-to-canvas conversion. Danger flash
    uses time.monotonic() modulo pattern identical to _get_band_colour().
  components:
    - name: "_draw_radial_mode"
      type: "function"
      purpose: "Render RADIAL mode frame to back buffer."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Renders directly to back buffer surface."
        raises:
          - "Exception caught internally; logged via self.logger.error()."
      logic:
        - "Drain message queue; update self._last_rpm. Pattern identical to _draw_digital_mode()."
        - "rpm = getattr(self, '_last_rpm', 0); clamp to [0, 7000]."
        - "Obtain back buffer surface from rendering_engine."
        - "Fill circle with black background RGB(10,10,10), radius 208."
        - "Draw headroom arc (light grey) from start_angle to end_angle for full active zone."
        - "Draw inert bottom arc (dark grey) from 5 o'clock to 7 o'clock short path."
        - "For each RPMBands segment up to current rpm, draw coloured donut arc slice."
        - "Draw zone boundary separator lines at 5 o'clock and 7 o'clock angles."
        - "Draw red outer border circle."
        - "Draw inner arc edge ring (subtle dark stroke)."
        - "Draw major tick marks and numerals for r in range(1000, 8000, 1000) if r <= 7000."
        - "Draw band boundary marks for each threshold in rpm_bands."
        - "Draw white indicator line at rpmToAngle(rpm)."
        - "Draw inert lower arc 'RPM x 1000' label."
        - "Compute danger flash state: flash_on = int(time.monotonic() * 2) % 2 == 0."
        - "Draw centre circle with flash-conditional fill."
        - "Draw 'GTach' label in centre circle; colour inverts with flash."
        - "Draw connection status dot (reuse _draw_status_indicator pattern)."

    - name: "DisplayMode.RADIAL"
      type: "constant"
      purpose: "Enum value for radial display mode."
      logic:
        - "Add RADIAL = auto() to DisplayMode in models.py after GAUGE."

  dependencies:
    internal:
      - "self.config.rpm_bands (RPMBands dataclass)"
      - "self.config.rpm_danger"
      - "self.rendering_engine (back buffer surface access)"
      - "self.thread_manager.message_queue"
      - "_get_band_colour() for fill colour"
      - "_draw_circular_border() — NOT used; border drawn inline in _draw_radial_mode()"
    external:
      - "math (cos, sin, pi)"
      - "time (monotonic)"
      - "pygame (draw primitives)"

  arc_geometry_reference:
    center: "(240, 240)"
    outer_radius: 198
    inner_radius: 88
    border_radius: 208
    max_rpm: 7000
    active_sweep_degrees: 300
    start_clock_degrees: 210
    end_clock_degrees: 150
    conversion: >
      clock_angle_to_canvas_radians(deg) = (deg - 90) * pi / 180
      rpm_to_canvas_radians(rpm) = clock_angle_to_canvas_radians(210 + (rpm/7000)*300)
      point_on_circle(r, angle_rad) = (240 + r*cos(angle_rad), 240 + r*sin(angle_rad))
    donut_arc_draw: >
      Draw donut arc slice using pygame approach:
        surface = rendering_engine.get_surface(BACK_BUFFER)
        Draw to a temporary surface or use polygon approximation.
        Recommended: draw filled sector to back buffer then overdraw
        with inner circle fill to create donut effect. Use a mask
        surface clipped to the circle if pygame.draw.arc is insufficient
        for filled arcs. Alternatively use polygon with arc point list.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: >
    Wrap entire _draw_radial_mode() body in try/except Exception.
    Log with self.logger.error(). Consistent with existing display methods.
  exceptions:
    - exception: "Exception"
      condition: "Any rendering error in _draw_radial_mode()."
      handling: "self.logger.error(f'Radial display error: {e}')"
  logging:
    level: "ERROR on failure; DEBUG for per-frame RPM band transitions."
    format: "Consistent with existing display method logging."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing

```yaml
testing:
  unit_tests: []
  edge_cases:
    - "rpm = 0: no fill, full grey headroom arc."
    - "rpm = 7000: full fill, no headroom."
    - "rpm >= danger_start: centre flash active."
    - "rpm between 1000 RPM boundaries: indicator line between major ticks."
  validation:
    - "Visual inspection on Pi with --transport simbt."
    - "Swipe gesture cycles correctly through all three modes."
    - "Config persists RADIAL across restart."
    - "Danger flash visible and timed at approximately 2 Hz."
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deliverable

```yaml
deliverable:
  format_requirements:
    - "Modify files in place. Do not create new files."
  files:
    - path: "src/gtach/display/models.py"
      content: "Add RADIAL = auto() to DisplayMode enum after GAUGE."
    - path: "src/gtach/display/manager.py"
      content: >
        Add _draw_radial_mode() method. Update _render_normal_modes()
        to dispatch RADIAL. Update _handle_swipe_left() and
        _handle_swipe_right() to cycle three modes.
    - path: "src/gtach/display/touch.py"
      content: >
        Update mode toggle logic to include RADIAL in the
        DIGITAL -> GAUGE -> RADIAL -> DIGITAL cycle.

success_criteria:
  - "DisplayMode.RADIAL exists in models.py."
  - "_draw_radial_mode() implemented in manager.py with correct arc geometry."
  - "Swipe gesture cycles all three modes in manager.py and touch.py."
  - "RADIAL mode name persists to and loads from config.yaml."
  - "No regressions in DIGITAL or GAUGE modes."
  - "No syntax errors; application starts cleanly."
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: Add RADIAL display mode to GTach.

  Files to modify:
  1. src/gtach/display/models.py — add RADIAL = auto() to DisplayMode after GAUGE.
  2. src/gtach/display/manager.py — add _draw_radial_mode(), update
     _render_normal_modes() dispatch, update _handle_swipe_left() and
     _handle_swipe_right() to cycle DIGITAL->GAUGE->RADIAL->DIGITAL.
  3. src/gtach/display/touch.py — update mode toggle to include RADIAL in cycle.

  Arc geometry (centre 240,240):
  - Active arc: 7 o'clock (210 deg clock) to 5 o'clock (150 deg clock) via top, 300 deg sweep.
  - Outer radius 198px, inner radius 88px (donut). Border radius 208px.
  - Angle conversion: canvas_rad = (clock_deg - 90) * pi / 180
  - RPM to angle: clock_deg = 210 + (rpm / 7000) * 300
  - Inert bottom arc (60 deg, short path 5->7 o'clock): dark grey RGB(28,28,28).

  Rendering layers (back to front):
  1. Black background circle r=208.
  2. Headroom arc (full active zone): light grey RGB(96,96,96) donut.
  3. Inert bottom arc: dark grey RGB(28,28,28) donut.
  4. Coloured fill arcs per RPMBands up to current rpm (use _get_band_colour() bg_colour).
  5. Zone boundary lines at 5 o'clock and 7 o'clock angles.
  6. Red outer border: RGB(170,0,0) r=208 linewidth=5.
  7. Major ticks at 1000 RPM intervals: white RGB(220,220,220) 20px radial lines + numerals 1-7.
  8. Band boundary marks at rpm_bands thresholds: coloured 28px radial lines.
  9. White indicator line at current RPM: spans inner->outer radius, linewidth=2.5.
  10. Centre circle r=87: background dark RGB(26,26,26); danger flash RGB(136,0,0)/RGB(10,10,10) at 2Hz when rpm >= rpm_bands.danger_start. Use int(time.monotonic()*2)%2==0 for flash state.
  11. 'GTach' label: red RGB(200,0,0) centred at (240,240); inverts to RGB(255,204,204) on flash.
  12. 'RPM x 1000' label: red RGB(200,0,0) centred at approx (240,395) in inert arc.

  Queue drain pattern: identical to _draw_digital_mode() — drain message_queue, update self._last_rpm.
  Error handling: wrap full method body in try/except; log with self.logger.error().
  Do not modify _draw_digital_mode() or _draw_gauge_mode().
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes          |
|---------|------------|------------------|
| 1.0     | 2026-05-15 | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
