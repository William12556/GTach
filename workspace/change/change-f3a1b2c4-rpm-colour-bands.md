Created: 2026 May 07

# Change: Implement RPM Colour Bands

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Testing Requirements](<#6.0 testing requirements>)
- [7.0 Traceability](<#7.0 traceability>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-f3a1b2c4"
  title: "Implement RPM colour bands — six-band display, engine profiles, acknowledgement, redline pulse"
  date: "2026-05-07"
  author: "William Watson"
  status: "approved"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f3a1b2c4"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "enhancement"
  reference: "issue-f3a1b2c4"
  description: >
    Implements the full RPM colour band feature per approved proposal
    workspace/proposal/proposal-rpm-colour-bands-enhancement.md v0.5.
    Resolves defect (silent queue drain failure) and missing feature
    (six-band colour system, engine profiles, acknowledgement screen,
    redline pulse) as documented in issue-f3a1b2c4.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Six files modified or created. Core change is in manager.py
    (_draw_digital_mode colour logic, background fill, pulse).
    Supporting changes: RPMBands dataclass in models.py; rpm_bands config
    schema in config.py; engine_profiles.yaml new data file;
    ack_state.py RPMBands wiring already present — no code change required there.
    Queue drain loop debug logging added to manager.py.

  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayConfig / RPMBands"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "ConfigManager"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
    - name: "engine_profiles.yaml"
      file_path: "src/gtach/assets/engine_profiles.yaml"
      change_type: "add"

  out_of_scope:
    - "Transport layer changes"
    - "OBD protocol changes"
    - "Threading architecture changes"
    - "Gauge mode colour bands (digital mode only in this change)"
    - "Settings UI for RPM band thresholds (existing warning/danger sliders retained)"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    The display shows static white text on black background at all RPM values.
    The core visual indicator of the application is non-functional.

  proposed_solution: >
    Implement the six-band colour scheme from proposal v0.5. Add RPMBands
    dataclass to hold configurable thresholds. Load defaults from engine
    profile YAML. Fill background colour per active band each frame.
    Change text colour to contrast with background. Implement 2 Hz pulse
    at danger_start and redline_rpm. Present acknowledgement screen on
    first run and after threshold changes. Fix silent queue drain failure
    by replacing bare except with typed exception and adding debug logging.

  benefits:
    - "Primary safety indicator functional"
    - "Configurable per-engine thresholds"
    - "Operator safety acknowledgement enforced"
    - "Silent decode failures now visible in debug log"

  risks:
    - risk: "Performance impact of per-frame background fill on Pi Zero 2W"
      mitigation: "Single pygame.draw.circle() call per frame; negligible cost at 55 FPS"
    - risk: "YAML profile file absent at runtime"
      mitigation: "Hard-coded Abarth 595 defaults used as fallback; warning logged"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    _draw_digital_mode() reads rpm from _last_rpm (default 0). Bare except: pass
    suppresses all decode errors silently. colour = white always (rpm never
    reaches rpm_warning=6500 threshold in most test conditions). Background
    never filled — always black from clear_surface(). No pulse. No engine profile.
    No acknowledgement screen for bands.

  proposed_behavior: >
    1. RPMBands dataclass added to models.py with fields:
       idle_max, torque_start, caution_start, warning_start,
       danger_start, redline_rpm.

    2. DisplayConfig gains rpm_bands: RPMBands field. engine_profile: str field.
       Legacy rpm_warning/rpm_danger retained for settings UI compatibility.

    3. engine_profiles.yaml shipped at src/gtach/assets/engine_profiles.yaml.
       Minimum profiles: abarth_595_turismo, generic_turbo_4cyl, generic_na_4cyl.
       ConfigManager loads selected profile at startup; populates rpm_bands defaults.

    4. _draw_digital_mode() revised:
       a. Queue drain bare except replaced with except queue.Empty; debug log
          on unexpected exception.
       b. _get_band_colour(rpm) returns (bg_colour, text_colour) tuple per band:
          - 0..idle_max       → bg=(0,0,80),    text=(100,100,255)   [blue]
          - idle_max..torque  → bg=(0,0,0),      text=(255,255,255)   [black/white]
          - torque..caution   → bg=(0,60,0),     text=(0,255,0)       [green]
          - caution..warning  → bg=(80,80,0),    text=(255,255,0)     [yellow]
          - warning..danger   → bg=(80,40,0),    text=(255,165,0)     [orange]
          - danger+           → bg=(80,0,0),     text=(255,0,0)       [red]
       c. Pulse logic: when rpm >= danger_start, bg toggles between active
          band colour and darker shade at 2 Hz using pygame.time.get_ticks().
       d. Background filled with bg_colour via draw_circle() to the full
          circular display area (radius 238) before text rendering.
       e. Text rendered in text_colour.

    5. Acknowledgement: _draw_splash_mode() already checks _ack_state_manager
       with a SimpleNamespace stub. Replace stub with actual self.config.rpm_bands.
       Acknowledgement screen displayed if not acknowledged. Existing
       AcknowledgementStateManager.is_acknowledged() / set_acknowledged() used.

  implementation_approach: >
    All changes confined to four files. No new threads or transport changes.
    Pulse uses pygame.time.get_ticks() modulo 500ms toggle — no new state
    object required. Engine profile loaded once at startup by ConfigManager.

  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Replace bare except in queue drain with typed exception + logging.
        Add _get_band_colour(rpm) method.
        Revise _draw_digital_mode() to fill background and use band colours.
        Add pulse toggle using pygame.time.get_ticks().
        Replace SimpleNamespace stub with self.config.rpm_bands in ack check.
      functions_affected:
        - "_draw_digital_mode"
        - "_draw_splash_mode"
        - "_get_band_colour (new)"

    - component: "DisplayConfig / RPMBands"
      file: "src/gtach/display/models.py"
      change_summary: >
        Add RPMBands dataclass with six threshold fields and defaults matching
        Abarth 595 Turismo profile.
        Add rpm_bands: RPMBands field and engine_profile: str field to DisplayConfig.
      classes_affected:
        - "RPMBands (new dataclass)"
        - "DisplayConfig"

    - component: "ConfigManager"
      file: "src/gtach/utils/config.py"
      change_summary: >
        Add _load_engine_profiles() to read src/gtach/assets/engine_profiles.yaml.
        Populate config.rpm_bands from selected profile on load.
        Fallback to hard-coded Abarth 595 defaults if profile file absent.
      functions_affected:
        - "_load_engine_profiles (new)"
        - "_load_config or equivalent load path"

    - component: "engine_profiles.yaml"
      file: "src/gtach/assets/engine_profiles.yaml"
      change_summary: >
        New YAML data file. Three profiles: abarth_595_turismo (default),
        generic_turbo_4cyl, generic_na_4cyl. Structure matches RPMBands fields.
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: >
    Manual validation on macOS with --transport simbt. Observe full RPM
    sine cycle and verify colour transitions at each band boundary.
    Verify pulse visible at danger_start and redline_rpm.
    Verify acknowledgement screen appears on first run.
    Verify acknowledgement not repeated on subsequent runs without config change.

  test_cases:
    - scenario: "Idle band (RPM < 1000)"
      expected_result: "Blue background, blue-tinted text"
    - scenario: "Black band (1000–2999 RPM)"
      expected_result: "Black background, white text"
    - scenario: "Green band (3000–4499 RPM)"
      expected_result: "Dark green background, green text"
    - scenario: "Yellow band (4500–5499 RPM)"
      expected_result: "Dark yellow background, yellow text"
    - scenario: "Orange band (5500–5799 RPM)"
      expected_result: "Dark orange background, orange text; pulse begins"
    - scenario: "Red band (5800+ RPM)"
      expected_result: "Dark red background, red text; red pulse at 2 Hz"
    - scenario: "First run (no ack state file)"
      expected_result: "Acknowledgement screen shown before DIGITAL mode"
    - scenario: "Subsequent run (ack state present)"
      expected_result: "Acknowledgement screen not shown"

  validation_criteria:
    - "Colour transitions visible at each band boundary during simbt sweep"
    - "Pulse visible at 2 Hz cadence at danger_start RPM"
    - "No regression in FPS (target >= 50 FPS on Pi Zero 2W)"
    - "Debug log shows RPM value and active band on each frame at DEBUG level"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Traceability

```yaml
traceability:
  design_updates:
    - design_ref: "workspace/design/design-gtach-master.md"
      sections_updated:
        - "DisplayConfig entity (add rpm_bands, engine_profile)"
        - "Display Mode Flow (add ACKNOWLEDGEMENT state)"
    - design_ref: "workspace/design/design-2c6b8e4d-domain_display.md"
      sections_updated:
        - "Band rendering logic"
        - "Pulse state"
  related_changes: []
  related_issues:
    - issue_ref: "issue-f3a1b2c4"
      relationship: "resolves"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-07 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
