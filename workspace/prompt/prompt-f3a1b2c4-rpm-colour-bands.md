Created: 2026 May 07

# Prompt: Implement RPM Colour Bands

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Data Schema](<#5.0 data schema>)
- [6.0 Error Handling](<#6.0 error handling>)
- [7.0 Deliverables](<#7.0 deliverables>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-f3a1b2c4"
  task_type: "code_generation"
  source_ref: "change-f3a1b2c4"
  date: "2026-05-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a1b2c4"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Implement the six-band RPM colour display system for GTach.
    The display must change background and text colour based on current RPM,
    pulse at high RPM, load engine profile thresholds from YAML, and show
    an operator acknowledgement screen on first run.

  integration: >
    Changes are confined to four files:
      src/gtach/display/manager.py      — rendering logic
      src/gtach/display/models.py       — RPMBands dataclass, DisplayConfig update
      src/gtach/utils/config.py         — engine profile loading
      src/gtach/assets/engine_profiles.yaml  — new data file (create)

    Existing AcknowledgementStateManager (src/gtach/utils/ack_state.py) is
    already complete and must not be modified. It expects an RPMBands instance.

  constraints:
    - "Do not modify src/gtach/utils/ack_state.py"
    - "Do not modify transport, OBD, or threading modules"
    - "Do not change public interfaces of DisplayManager or DisplayConfig"
    - "pygame.time.get_ticks() for pulse — no new threads"
    - "Maintain 60 FPS target; background fill must not degrade performance"
    - "All hardware imports remain conditional (try/except ImportError)"
    - "macOS guard (platform.system() == 'Darwin') pattern must be preserved"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Six RPM colour bands. Configurable thresholds from engine profile YAML.
    Background fill per band. Text colour contrasting with background.
    2 Hz pulse at danger_start and redline_rpm. Operator acknowledgement
    on first run and after threshold/profile changes.
    Fix silent queue drain failure in _draw_digital_mode.

  requirements:
    functional:
      - "Six bands: idle(blue), sub-torque(black), torque(green), caution(yellow), warning(orange), danger(red)"
      - "Background filled with band colour each frame via draw_circle(radius=238)"
      - "Text colour contrasts with background (see colour table in §4.0)"
      - "2 Hz pulse: rpm >= danger_start → bg toggles band colour / darker shade"
      - "Engine profile loaded from src/gtach/assets/engine_profiles.yaml at startup"
      - "Fallback to hard-coded Abarth 595 Turismo defaults if YAML absent"
      - "Acknowledgement screen shown if not acknowledged for current RPMBands + profile"
      - "Queue drain bare except replaced with except queue.Empty; log unexpected exceptions"
      - "RPMBands dataclass added to models.py"
      - "DisplayConfig gains rpm_bands: RPMBands and engine_profile: str fields"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8, type hints on all public interfaces"
        - "Google-style docstrings"
        - "Thread-safe reads of self.config.rpm_bands (already protected by existing pattern)"
        - "Debug logging at DEBUG level for band transitions"
        - "Comprehensive error handling with exc_info=True on unexpected exceptions"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: >
    All changes are additive within the existing DisplayManager class.
    New _get_band_colour(rpm) method returns (bg_colour, text_colour) tuple.
    Pulse state derived from pygame.time.get_ticks() — no instance variable needed.

  components:
    - name: "RPMBands"
      type: "dataclass"
      purpose: "Holds six RPM threshold fields with Abarth 595 Turismo defaults"
      interface:
        inputs: []
        outputs:
          type: "dataclass instance"
          description: "idle_max, torque_start, caution_start, warning_start, danger_start, redline_rpm"
      logic:
        - "idle_max: int = 999"
        - "torque_start: int = 3000"
        - "caution_start: int = 4500"
        - "warning_start: int = 5500"
        - "danger_start: int = 5800"
        - "redline_rpm: int = 6000"
        - "Validation: must be strictly ascending; raise ValueError if not"

    - name: "_get_band_colour"
      type: "method"
      purpose: "Return (bg_colour, text_colour) tuple for given RPM including pulse logic"
      interface:
        inputs:
          - name: "rpm"
            type: "float"
            description: "Current RPM value"
        outputs:
          type: "Tuple[Tuple[int,int,int], Tuple[int,int,int]]"
          description: "(bg_colour, text_colour)"
      logic:
        - "bands = self.config.rpm_bands"
        - "Colour table:"
        - "  rpm < bands.idle_max:       bg=(0,0,80),    text=(100,100,255)"
        - "  rpm < bands.torque_start:   bg=(0,0,0),     text=(255,255,255)"
        - "  rpm < bands.caution_start:  bg=(0,50,0),    text=(0,220,0)"
        - "  rpm < bands.warning_start:  bg=(60,60,0),   text=(255,255,0)"
        - "  rpm < bands.danger_start:   bg=(70,35,0),   text=(255,165,0)"
        - "  rpm >= bands.danger_start:  bg=(80,0,0),    text=(255,0,0)"
        - "Pulse: if rpm >= bands.danger_start:"
        - "  ticks = pygame.time.get_ticks()"
        - "  if (ticks // 500) % 2 == 0: bg = darker_shade (multiply each channel by 0.5)"
        - "  (pulse period = 500ms on + 500ms off = 2 Hz)"

    - name: "_draw_digital_mode (revised)"
      type: "method"
      purpose: "Render RPM with band colour background; fix queue drain exception handling"
      logic:
        - "Queue drain: replace bare except: pass with except queue.Empty: pass"
        - "Add: except Exception as e: self.logger.debug(f'Queue drain error: {e}')"
        - "Call _get_band_colour(rpm) → (bg_colour, text_colour)"
        - "Fill background: draw_circle(BACK_BUFFER, bg_colour, (240,240), 238)"
        - "Render RPM text in text_colour at (240, 215)"
        - "Render 'RPM × 1000' label in (200,0,0) at (240, 390) — unchanged"
        - "Draw circular red border — unchanged"
        - "Log: self.logger.debug(f'RPM {rpm:.0f} band colour bg={bg_colour}')"

    - name: "_draw_splash_mode (revised)"
      type: "method"
      purpose: "Replace SimpleNamespace stub with actual rpm_bands in ack check"
      logic:
        - "Replace: __import__('types').SimpleNamespace(idle_max=0, torque_start=0, ...) stub"
        - "With: self.config.rpm_bands"
        - "Replace: self.config.engine_profile reference (already present in stub call)"
        - "With: self.config.engine_profile"

    - name: "_load_engine_profiles"
      type: "method on ConfigManager or inline in _load_config"
      purpose: "Load engine_profiles.yaml and populate rpm_bands on DisplayConfig"
      logic:
        - "Path: importlib.resources or os.path relative to src/gtach/assets/"
        - "Load YAML; select profile by engine_profile key (default: abarth_595_turismo)"
        - "Construct RPMBands from profile fields"
        - "If file absent or profile missing: log WARNING, use RPMBands() defaults"
        - "Assign to self.config.rpm_bands"

  dependencies:
    internal:
      - "src/gtach/display/models.py — RPMBands, DisplayConfig"
      - "src/gtach/utils/ack_state.py — AcknowledgementStateManager (read-only)"
    external:
      - "pygame (pygame.time.get_ticks)"
      - "pyyaml"
      - "queue (queue.Empty)"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Data Schema

```yaml
data_schema:
  entities:
    - name: "RPMBands"
      attributes:
        - name: "idle_max"
          type: "int"
          constraints: "default 999; > 0"
        - name: "torque_start"
          type: "int"
          constraints: "default 3000; > idle_max"
        - name: "caution_start"
          type: "int"
          constraints: "default 4500; > torque_start"
        - name: "warning_start"
          type: "int"
          constraints: "default 5500; > caution_start"
        - name: "danger_start"
          type: "int"
          constraints: "default 5800; > warning_start"
        - name: "redline_rpm"
          type: "int"
          constraints: "default 6000; > danger_start"
      validation:
        - "All fields strictly ascending"
        - "All fields > 0 and <= 15000"

    - name: "engine_profiles.yaml structure"
      attributes:
        - name: "profiles"
          type: "dict"
          constraints: "keyed by profile_id string"
        - name: "profiles.<id>.idle_max"
          type: "int"
          constraints: "same as RPMBands"
        - name: "profiles.<id>.torque_start .. redline_rpm"
          type: "int"
          constraints: "same as RPMBands"
        - name: "default_profile"
          type: "str"
          constraints: "must match a key in profiles"
      validation:
        - "Three minimum profiles: abarth_595_turismo, generic_turbo_4cyl, generic_na_4cyl"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Error Handling

```yaml
error_handling:
  strategy: >
    Graceful degradation. If engine profile YAML absent, use defaults silently
    (WARNING logged). If RPMBands validation fails, use defaults (ERROR logged).
    Queue decode failures logged at DEBUG — never crash display loop.

  exceptions:
    - exception: "queue.Empty"
      condition: "No new RPM data in queue this frame"
      handling: "pass — use _last_rpm"
    - exception: "Exception (unexpected)"
      condition: "Unexpected error in queue drain"
      handling: "logger.debug with message; continue with _last_rpm"
    - exception: "FileNotFoundError"
      condition: "engine_profiles.yaml not found"
      handling: "logger.warning; use RPMBands() defaults"
    - exception: "KeyError / ValueError"
      condition: "Profile key missing or threshold validation fails"
      handling: "logger.error; use RPMBands() defaults"

  logging:
    level: "DEBUG"
    format: "%(asctime)s %(name)s %(levelname)s %(message)s"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Save generated code directly to specified paths using filesystem tools"
    - "Do not create any files not listed below"
  files:
    - path: "src/gtach/display/models.py"
      content: "Add RPMBands dataclass; add rpm_bands and engine_profile to DisplayConfig"
    - path: "src/gtach/display/manager.py"
      content: "Revise _draw_digital_mode, _draw_splash_mode; add _get_band_colour"
    - path: "src/gtach/utils/config.py"
      content: "Add engine profile loading logic"
    - path: "src/gtach/assets/engine_profiles.yaml"
      content: "New file — three profiles as specified"

success_criteria:
  - "python -c \"import ast; ast.parse(open('src/gtach/display/manager.py').read())\" exits 0"
  - "python -c \"import ast; ast.parse(open('src/gtach/display/models.py').read())\" exits 0"
  - "python -c \"import ast; ast.parse(open('src/gtach/utils/config.py').read())\" exits 0"
  - "python -m gtach --macos --transport simbt --debug launches without exception"
  - "Log shows RPM band colour transitions during RPM sweep"
  - "No bare except: pass remains in _draw_digital_mode queue drain block"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Implement RPM colour bands in GTach. Four files to modify/create.

  FILE 1 — src/gtach/display/models.py
  Add RPMBands dataclass (fields: idle_max=999, torque_start=3000,
  caution_start=4500, warning_start=5500, danger_start=5800, redline_rpm=6000).
  Add rpm_bands: RPMBands and engine_profile: str = "abarth_595_turismo"
  fields to DisplayConfig.

  FILE 2 — src/gtach/display/manager.py
  (a) Fix queue drain in _draw_digital_mode: replace bare except: pass with
      except queue.Empty: pass; add except Exception as e: self.logger.debug(...)
  (b) Add _get_band_colour(self, rpm: float) -> Tuple:
      Returns (bg_colour, text_colour) per band:
        rpm < idle_max:       bg=(0,0,80),   text=(100,100,255)
        rpm < torque_start:   bg=(0,0,0),    text=(255,255,255)
        rpm < caution_start:  bg=(0,50,0),   text=(0,220,0)
        rpm < warning_start:  bg=(60,60,0),  text=(255,255,0)
        rpm < danger_start:   bg=(70,35,0),  text=(255,165,0)
        rpm >= danger_start:  bg=(80,0,0),   text=(255,0,0)
      Pulse at 2 Hz when rpm >= danger_start:
        if (pygame.time.get_ticks() // 500) % 2 == 0: darken bg by 50%
  (c) In _draw_digital_mode: call _get_band_colour; fill background circle
      (centre=240,240 radius=238) with bg_colour before rendering text;
      render RPM numeral in text_colour.
  (d) In _draw_splash_mode: replace SimpleNamespace stub with
      self.config.rpm_bands and self.config.engine_profile in ack check.

  FILE 3 — src/gtach/utils/config.py
  Add _load_engine_profile() called from _load_config():
    Load src/gtach/assets/engine_profiles.yaml.
    Select profile by self.config.engine_profile key.
    Construct RPMBands; assign to self.config.rpm_bands.
    On any failure: log WARNING/ERROR; use RPMBands() defaults.

  FILE 4 — src/gtach/assets/engine_profiles.yaml (CREATE)
  YAML with default_profile: abarth_595_turismo and profiles dict.
  Minimum three profiles: abarth_595_turismo, generic_turbo_4cyl, generic_na_4cyl.
  Each profile has: idle_max, torque_start, caution_start, warning_start,
  danger_start, redline_rpm.

  CONSTRAINTS:
  - Do not modify ack_state.py, transport, OBD, or threading modules
  - Do not change public interfaces
  - No new threads; pulse via pygame.time.get_ticks()
  - All hardware imports remain conditional

  SUCCESS: syntax check all three .py files passes; no bare except in queue
  drain; log shows RPM band colour debug output during simbt sweep.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-07 | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
