# Prompt: RPM Colour Band Enhancement

Created: 2026 April 23

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Data Schema](<#5.0 data schema>)
- [6.0 Error Handling](<#6.0 error handling>)
- [7.0 Testing](<#7.0 testing>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-3f7a1b9c"
  task_type: "code_generation"
  source_ref: "change-3f7a1b9c"
  date: "2026-04-23"
  iteration: 1
  coupled_docs:
    change_ref: "change-3f7a1b9c"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Extend the GTach RPM colour band system from four fixed bands to six
    configurable bands with engine profile support, a pre-redline pulse
    alert, and a one-time operator safety acknowledgement screen.
  integration: >
    GTach is a real-time automotive tachometer running on Raspberry Pi Zero 2W
    with a 480x480 HyperPixel Round touchscreen. Development runs on macOS
    via TCP transport to an ELM327 emulator. The display pipeline is:
    OBDProtocol → DisplayManager → rendering functions in manager.py.
    Band colour logic currently lives in manager.py. DisplayConfig is
    defined in display/models.py (runtime) and utils/config.py (YAML
    persistence) — both require extension.
  constraints:
    - "Display loop runs on main thread (macOS Cocoa requirement)"
    - "No additional threads for pulse — use pygame.time.get_ticks()"
    - "Python 3.9+ compatible"
    - "pygame 2.x"
    - "PyYAML required for all YAML operations"
    - "All new source files must carry the MIT copyright header"
    - "Do not modify manager_backup.py or ui_testing_framework.py"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Implement six configurable RPM colour bands replacing the existing two-threshold
    (rpm_warning / rpm_danger) model. Add engine profile YAML, acknowledgement
    state manager, pulse logic in the display render, and profile/acknowledgement
    screens in the setup flow.

  requirements:
    functional:
      - "Six bands: blue (idle), black (sub-torque), green (optimal), yellow (caution), orange (warning/danger), red (redline)"
      - "Band thresholds: idle_max, torque_start, caution_start, warning_start, danger_start, redline_rpm"
      - "Strictly ascending validation: idle_max < torque_start < caution_start < warning_start < danger_start < redline_rpm"
      - "Invalid ordering: log WARNING, fall back to built-in defaults"
      - "Threshold ceiling: 15000 RPM"
      - "Background pulses at 2 Hz from danger_start upward; orange pulse in danger band, red pulse in redline band"
      - "Pulse implemented as time-based toggle via pygame.time.get_ticks(); no additional thread"
      - "engine_profiles.yaml ships with application; minimum three profiles"
      - "Profile selection presented on first run via setup flow"
      - "Profile populates rpm_bands defaults; operator may override individual thresholds"
      - "Profile file loaded at startup; re-loadable in setup mode"
      - "Acknowledgement screen displayed on first run and after any threshold or profile change"
      - "Acknowledgement requires deliberate touch confirm button; screen not skippable"
      - "Acknowledgement state persisted to separate state file, independent of YAML config"
      - "Absence or hash mismatch of state file triggers acknowledgement screen"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe where concurrent access exists (ConfigManager RWLock pattern already in place)"
        - "Comprehensive error handling with logging"
        - "Professional docstrings"
        - "MIT copyright header on all new files"
        - "Existing code style: dataclasses, classmethod from_dict / to_dict pattern"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: >
    Six implementation units across five files plus two new files.
    Band colour resolved by a new _get_band_colour(rpm) method in DisplayManager
    that consults DisplayConfig.rpm_bands. Pulse state held as instance variable
    in DisplayManager, toggled per frame using pygame.time.get_ticks().
    AcknowledgementStateManager is a standalone utility class with no
    dependency on ConfigManager. Engine profile load is performed by a new
    EngineProfileLoader utility at startup and in setup mode.

  components:

    - name: "RPMBands"
      type: "dataclass"
      purpose: "Hold six threshold values with validation and default factory"
      file: "src/gtach/display/models.py"
      interface:
        attributes:
          - "idle_max: int = 999"
          - "torque_start: int = 3000"
          - "caution_start: int = 4500"
          - "warning_start: int = 5500"
          - "danger_start: int = 5800"
          - "redline_rpm: int = 6000"
        methods:
          - "is_valid() -> bool  # checks strictly ascending order and ceiling"
          - "to_dict() -> dict"
          - "classmethod from_dict(data) -> RPMBands"
      logic:
        - "is_valid: return idle_max < torque_start < caution_start < warning_start < danger_start < redline_rpm and redline_rpm <= 15000"
        - "Built-in defaults match Abarth 595 Turismo profile"

    - name: "DisplayConfig (extend)"
      type: "dataclass"
      purpose: "Add rpm_bands and engine_profile fields to existing DisplayConfig"
      file: "src/gtach/display/models.py"
      interface:
        new_fields:
          - "rpm_bands: RPMBands = field(default_factory=RPMBands)"
          - "engine_profile: str = 'abarth_595_turismo'"
      logic:
        - "Extend existing to_dict() and from_dict() to include rpm_bands and engine_profile"
        - "from_dict: construct RPMBands from nested dict; validate; on invalid fall back to RPMBands() defaults and log WARNING"

    - name: "DisplayConfig in config.py (extend)"
      type: "dataclass"
      purpose: "Mirror rpm_bands and engine_profile in YAML persistence config"
      file: "src/gtach/utils/config.py"
      logic:
        - "Add rpm_bands sub-dict and engine_profile to DisplayConfig.to_dict() and from_dict()"
        - "Validation delegated to RPMBands.is_valid(); fallback to defaults on failure"
        - "Note: config.py DisplayConfig is separate from display/models.py DisplayConfig"

    - name: "EngineProfileLoader"
      type: "class"
      purpose: "Load engine_profiles.yaml; return RPMBands for a given profile ID"
      file: "src/gtach/utils/engine_profiles.py"
      interface:
        inputs:
          - name: "profiles_path"
            type: "Path"
            description: "Path to engine_profiles.yaml; defaults to src/gtach/data/engine_profiles.yaml"
        methods:
          - "load() -> bool"
          - "get_profile(profile_id: str) -> Optional[RPMBands]"
          - "list_profiles() -> List[str]"
      logic:
        - "load(): read YAML; cache profiles dict; return False on IOError/parse error"
        - "get_profile(): return RPMBands.from_dict(profiles[profile_id]); return None if not found"
        - "If profiles_path not found, log WARNING and return empty profile list"

    - name: "AcknowledgementStateManager"
      type: "class"
      purpose: "Persist and check operator acknowledgement state in a file separate from YAML config"
      file: "src/gtach/utils/ack_state.py"
      interface:
        methods:
          - "is_acknowledged(rpm_bands: RPMBands, profile_id: str) -> bool"
          - "set_acknowledged(rpm_bands: RPMBands, profile_id: str) -> bool"
          - "clear() -> bool"
        state_file_location: "~/.config/gtach/ack_state.yaml (or equivalent via get_home_path())"
      logic:
        - "Hash = hashlib.sha256 of sorted threshold values + profile_id"
        - "is_acknowledged: load state file; compare stored hash to computed hash; return False if file absent, unreadable, or hash mismatch"
        - "set_acknowledged: write {acknowledged: true, threshold_hash: <hash>, profile_id: <id>} to state file atomically"
        - "Use tmp file + rename for atomic write (same pattern as ConfigManager)"

    - name: "_get_band_colour (new method in DisplayManager)"
      type: "function"
      purpose: "Return background colour tuple for given RPM using six-band lookup"
      file: "src/gtach/display/manager.py"
      interface:
        inputs:
          - name: "rpm"
            type: "int"
            description: "Current RPM value"
        outputs:
          type: "Tuple[int, int, int]"
          description: "RGB colour tuple for background"
      logic:
        - "bands = self.config.rpm_bands"
        - "if rpm >= bands.redline_rpm: return RED (255, 0, 0)"
        - "elif rpm >= bands.danger_start: return ORANGE (255, 100, 0)"
        - "elif rpm >= bands.warning_start: return YELLOW (255, 200, 0)"
        - "elif rpm >= bands.caution_start: return GREEN (0, 180, 0)"  
        - "elif rpm >= bands.torque_start: return GREEN (0, 180, 0)  # same green — caution is yellow above"
        - "elif rpm >= 1: return BLACK (10, 10, 10)"
        - "else: return BLUE_DIM (30, 60, 120)"
        - "Correction: yellow=caution, green=torque_start–caution_start-1, black=idle_max+1–torque_start-1, blue=0–idle_max"

    - name: "_get_pulse_colour (new method in DisplayManager)"
      type: "function"
      purpose: "Return pulsed colour for danger and redline bands using pygame.time.get_ticks()"
      file: "src/gtach/display/manager.py"
      interface:
        inputs:
          - name: "rpm"
            type: "int"
        outputs:
          type: "Tuple[int, int, int]"
      logic:
        - "PULSE_HZ = 2; PULSE_PERIOD_MS = 1000 // PULSE_HZ  # 500 ms"
        - "pulse_on = (pygame.time.get_ticks() % PULSE_PERIOD_MS) < (PULSE_PERIOD_MS // 2)"
        - "if rpm >= redline_rpm: return RED if pulse_on else DARK_RED (120, 0, 0)"
        - "elif rpm >= danger_start: return ORANGE if pulse_on else DARK_ORANGE (140, 50, 0)"
        - "else: return _get_band_colour(rpm)  # no pulse below danger_start"

    - name: "Replace rpm_warning/rpm_danger references in DisplayManager"
      type: "refactor"
      purpose: "Replace old two-threshold colour lookups with _get_pulse_colour calls"
      file: "src/gtach/display/manager.py"
      logic:
        - "manager.py line 502-507: replace colour block with bg_colour = self._get_pulse_colour(rpm)"
        - "manager.py line 646-651: replace _get_rpm_colour body with call to _get_pulse_colour"
        - "Gauge zone arcs (lines 590-599): update to use six thresholds from self.config.rpm_bands"
        - "_save_config (line 278-284): add rpm_bands and engine_profile to saved dict"
        - "_load_config (line 239-243): add rpm_bands and engine_profile to loaded DisplayConfig"

    - name: "AcknowledgementScreen"
      type: "function"
      purpose: "Render one-time safety notice with touch confirm button"
      file: "src/gtach/display/manager.py"
      logic:
        - "Add DisplayMode.ACKNOWLEDGEMENT to DisplayMode enum in models.py"
        - "Check AcknowledgementStateManager.is_acknowledged() in _determine_initial_state()"
        - "If not acknowledged: enter ACKNOWLEDGEMENT mode before normal mode"
        - "Render: safety notice text centred on display; CONFIRM button at bottom"
        - "On CONFIRM touch: call set_acknowledged(); transition to normal mode"
        - "Screen not skippable — no timeout, no back gesture"

    - name: "ProfileSelectionScreen"
      type: "function"
      purpose: "Present engine profile list for selection; populate rpm_bands; trigger acknowledgement"
      file: "src/gtach/display/setup.py"
      logic:
        - "Called from setup flow on first run (before device pairing) or from setup mode"
        - "Load profiles via EngineProfileLoader"
        - "Render scrollable list of profile names; touch selects"
        - "On selection: update config.rpm_bands from profile; save config; trigger acknowledgement"
        - "Re-loadable: EngineProfileLoader.load() called each entry into profile selection screen"

  dependencies:
    internal:
      - "src/gtach/display/models.py — RPMBands, DisplayConfig, DisplayMode"
      - "src/gtach/utils/config.py — DisplayConfig (YAML persistence)"
      - "src/gtach/utils/home.py — get_home_path() for ack_state.yaml path"
      - "src/gtach/display/manager.py — DisplayManager"
      - "src/gtach/display/setup.py — SetupDisplayManager"
    external:
      - "pygame 2.x — pygame.time.get_ticks()"
      - "PyYAML — engine_profiles.yaml, ack_state.yaml"
      - "hashlib — acknowledgement hash (stdlib)"
      - "pathlib — file paths (stdlib)"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Data Schema

```yaml
data_schema:
  entities:

    - name: "engine_profiles.yaml"
      path: "src/gtach/data/engine_profiles.yaml"
      schema: |
        profiles:
          abarth_595_turismo:
            name: "Abarth 595 Turismo 1.4T"
            idle_max: 999
            torque_start: 3000
            caution_start: 4500
            warning_start: 5500
            danger_start: 5800
            redline_rpm: 6000
          generic_turbo_4cyl:
            name: "Generic Turbocharged 4-cylinder"
            idle_max: 999
            torque_start: 2500
            caution_start: 4000
            warning_start: 5000
            danger_start: 5500
            redline_rpm: 6000
          generic_na_4cyl:
            name: "Generic Naturally Aspirated 4-cylinder"
            idle_max: 999
            torque_start: 2000
            caution_start: 4500
            warning_start: 5500
            danger_start: 6000
            redline_rpm: 6500
      validation:
        - "All threshold fields must be positive integers"
        - "Strictly ascending: idle_max < torque_start < caution_start < warning_start < danger_start < redline_rpm"
        - "redline_rpm <= 15000"

    - name: "ack_state.yaml"
      path: "~/.config/gtach/ack_state.yaml"
      schema: |
        acknowledged: true
        threshold_hash: "<sha256 hex string>"
        profile_id: "abarth_595_turismo"
      validation:
        - "acknowledged must be boolean true"
        - "threshold_hash must match computed hash of current rpm_bands + profile_id"
        - "Absent file or any mismatch = not acknowledged"

    - name: "RPMBands (dataclass fields)"
      attributes:
        - name: "idle_max"
          type: "int"
          constraints: "> 0, < torque_start"
        - name: "torque_start"
          type: "int"
          constraints: "> idle_max, < caution_start"
        - name: "caution_start"
          type: "int"
          constraints: "> torque_start, < warning_start"
        - name: "warning_start"
          type: "int"
          constraints: "> caution_start, < danger_start"
        - name: "danger_start"
          type: "int"
          constraints: "> warning_start, < redline_rpm"
        - name: "redline_rpm"
          type: "int"
          constraints: "> danger_start, <= 15000"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Error Handling

```yaml
error_handling:
  strategy: >
    Fail-safe: any configuration, profile, or state file error falls back to
    built-in defaults. No exception propagates to the display loop. Log all
    fallbacks at WARNING level.
  exceptions:
    - exception: "RPMBands validation failure"
      condition: "Thresholds not strictly ascending or redline_rpm > 15000"
      handling: "Log WARNING with values; substitute RPMBands() built-in defaults"
    - exception: "engine_profiles.yaml not found or parse error"
      condition: "File absent or YAML parse fails"
      handling: "Log WARNING; EngineProfileLoader.load() returns False; get_profile() returns None"
    - exception: "ack_state.yaml absent or unreadable"
      condition: "File missing, permissions error, or parse error"
      handling: "AcknowledgementStateManager.is_acknowledged() returns False; acknowledgement screen shown"
    - exception: "Atomic write failure (ack_state or config)"
      condition: "IOError on temp file or rename"
      handling: "Log ERROR; return False from set_acknowledged()/save_config()"
  logging:
    level: "WARNING for fallbacks, ERROR for write failures, DEBUG for normal operations"
    format: "Existing project format: '%(asctime)s - [%(name)s:%(funcName)s:%(lineno)d] - %(levelname)s - %(message)s'"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Testing

```yaml
testing:
  unit_tests:
    - scenario: "RPMBands.is_valid() with valid ascending thresholds"
      expected: "returns True"
    - scenario: "RPMBands.is_valid() with danger_start >= redline_rpm"
      expected: "returns False"
    - scenario: "RPMBands.is_valid() with redline_rpm = 15001"
      expected: "returns False"
    - scenario: "_get_band_colour(rpm=0)"
      expected: "returns blue dim colour"
    - scenario: "_get_band_colour(rpm=999)"
      expected: "returns blue dim colour (idle_max boundary)"
    - scenario: "_get_band_colour(rpm=1000)"
      expected: "returns black (torque_start-1)"
    - scenario: "_get_band_colour(rpm=5799)"
      expected: "returns orange (danger_start-1)"
    - scenario: "_get_band_colour(rpm=5800)"
      expected: "returns orange (danger_start, pulse onset)"
    - scenario: "_get_band_colour(rpm=6000)"
      expected: "returns red (redline_rpm)"
    - scenario: "DisplayConfig.from_dict with invalid threshold ordering"
      expected: "falls back to RPMBands() defaults, logs WARNING"
    - scenario: "AcknowledgementStateManager.is_acknowledged() with absent state file"
      expected: "returns False"
    - scenario: "AcknowledgementStateManager hash mismatch after threshold change"
      expected: "returns False"
    - scenario: "EngineProfileLoader with valid engine_profiles.yaml"
      expected: "get_profile('abarth_595_turismo') returns RPMBands with correct values"
  edge_cases:
    - "RPM exactly at each band boundary (idle_max, torque_start, caution_start, warning_start, danger_start, redline_rpm)"
    - "RPM = 0"
    - "RPM > redline_rpm"
    - "engine_profiles.yaml with an additional user-added profile"
    - "ack_state.yaml written then config threshold changed — hash mismatch detected"
  validation:
    - "GTach starts on macOS, splash transitions to DIGITAL mode with TCP transport"
    - "Band colours visible and transition at correct RPM boundaries (simulate via emulator)"
    - "Pulse visible at danger_start and redline_rpm (trigger via emulator RPM override)"
    - "Acknowledgement screen appears on first run; does not appear on second run with unchanged thresholds"
    - "Profile selection screen appears in setup mode; selecting profile updates rpm_bands"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: >
  Implement six-band configurable RPM colour display for GTach.
  Change ref: change-3f7a1b9c. Read CLAUDE.md and ai/profiles/claude.md before starting.

  FILES TO CREATE:
  1. src/gtach/data/engine_profiles.yaml — three profiles (abarth_595_turismo,
     generic_turbo_4cyl, generic_na_4cyl) with six threshold fields each.
  2. src/gtach/utils/engine_profiles.py — EngineProfileLoader class:
     load(), get_profile(profile_id) -> Optional[RPMBands], list_profiles().
  3. src/gtach/utils/ack_state.py — AcknowledgementStateManager class:
     is_acknowledged(rpm_bands, profile_id) -> bool,
     set_acknowledged(rpm_bands, profile_id) -> bool.
     Hash = sha256 of sorted threshold values + profile_id.
     State file: get_home_path() / 'ack_state.yaml'.
     Atomic write via tmp file + rename.

  FILES TO MODIFY:
  4. src/gtach/display/models.py:
     - Add RPMBands dataclass (6 fields, defaults = Abarth 595 profile values,
       is_valid(), to_dict(), from_dict()).
     - Extend DisplayConfig: add rpm_bands: RPMBands field, engine_profile: str field.
     - Add DisplayMode.ACKNOWLEDGEMENT to DisplayMode enum.
  5. src/gtach/utils/config.py:
     - Extend DisplayConfig dataclass: add rpm_bands sub-dict and engine_profile field
       to to_dict() and from_dict(). Validate via RPMBands.is_valid(); fall back to
       RPMBands() defaults on failure.
     - Note: this is a separate DisplayConfig from display/models.py.
  6. src/gtach/display/manager.py:
     - Add _get_band_colour(rpm: int) -> Tuple[int,int,int]:
       Bands (using self.config.rpm_bands defaults):
         0–idle_max: BLUE_DIM (30,60,120)
         idle_max+1–torque_start-1: BLACK (10,10,10)
         torque_start–caution_start-1: GREEN (0,180,0)
         caution_start–warning_start-1: YELLOW (255,200,0)
         warning_start–danger_start-1: ORANGE (255,100,0)
         danger_start+: RED (255,0,0)
     - Add _get_pulse_colour(rpm: int) -> Tuple[int,int,int]:
         PULSE_PERIOD_MS = 500 (2 Hz).
         pulse_on = (pygame.time.get_ticks() % 500) < 250.
         rpm >= redline_rpm: RED if pulse_on else (120,0,0).
         rpm >= danger_start: ORANGE if pulse_on else (140,50,0).
         else: _get_band_colour(rpm).
     - Replace rpm_danger/rpm_warning colour lookups (lines ~502-507, ~646-651)
       with _get_pulse_colour(rpm).
     - Update _save_config and _load_config to include rpm_bands and engine_profile.
     - Add ACKNOWLEDGEMENT display state: check AcknowledgementStateManager in
       _determine_initial_state(); render notice + CONFIRM button; on confirm call
       set_acknowledged() and transition.
  7. src/gtach/display/setup.py:
     - Add profile selection screen: load profiles via EngineProfileLoader;
       render scrollable list; on selection update config.rpm_bands; save config;
       clear acknowledgement state; transition to acknowledgement screen.
     - Re-load engine_profiles.yaml on each entry to profile selection screen.

  HARD CONSTRAINTS:
  - Do NOT modify manager_backup.py or ui_testing_framework.py.
  - Pulse uses pygame.time.get_ticks() only — no threads.
  - All new files: MIT copyright header (Copyright (c) 2026 William Watson).
  - Threshold validation: strictly ascending chain; redline_rpm <= 15000; on
    failure log WARNING and substitute RPMBands() defaults.
  - ack_state.yaml is independent of the main YAML config file.

  SUCCESS CRITERIA:
  - GTach starts on macOS with TCP transport; splash → DIGITAL mode.
  - Band colours transition at correct RPM boundaries.
  - Pulse visible at danger_start (orange) and redline_rpm (red).
  - Acknowledgement screen appears on first run; suppressed on subsequent runs
    with unchanged thresholds.
  - Profile selection in setup mode updates rpm_bands and triggers acknowledgement.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-23 | Initial prompt document |
| 1.1 | 2026-04-23 | Closed after macOS verification |

---

Copyright (c) 2026 William Watson. MIT License.
