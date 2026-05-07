Created: 2026 May 07

# Issue: RPM Colour Bands Not Implemented

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behaviour](<#5.0 behaviour>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [8.0 Resolution](<#8.0 resolution>)
- [9.0 Traceability](<#9.0 traceability>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-f3a1b2c4"
  title: "RPM colour bands not implemented — text colour static, background colour absent"
  date: "2026-05-07"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a1b2c4"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  description: >
    Operator observed that the display screen does not change colour as RPM cycles
    through low and high values during simbt transport testing. Log analysis
    (gtach-simbt.log) confirms SimTransport is delivering a full RPM sine sweep
    (800–6500 RPM). The display renders RPM numerals but neither the text colour
    nor the background colour respond to the RPM value.

    Root cause (defect): In _draw_digital_mode(), the queue drain loop uses bare
    except: pass, silently suppressing any OBDResponse decode failure. If
    rpm_data.data access raises AttributeError or similar, _last_rpm is never
    updated, rpm remains 0, and the colour threshold branch always resolves to
    white. No debug logging is present to expose this failure.

    Root cause (missing feature): The proposal-rpm-colour-bands-enhancement.md
    (v0.5, approved) specifies six configurable colour bands with background fill,
    redline pulse, engine profiles, and operator acknowledgement. None of these
    have been implemented. Only two legacy threshold fields (rpm_warning,
    rpm_danger) exist in DisplayConfig. The six-band scheme from the proposal is
    the intended target state.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayConfig"
      file_path: "src/gtach/display/models.py"
    - name: "ConfigManager"
      file_path: "src/gtach/utils/config.py"
    - name: "AcknowledgementStateManager"
      file_path: "src/gtach/utils/ack_state.py"
  designs:
    - design_ref: "design-gtach-master.md"
    - design_ref: "design-2c6b8e4d-domain_display.md"
    - design_ref: "design-c9d0e1f2-component_display_rendering_engine.md"
    - design_ref: "design-b4c5d6e7-component_utils_config_manager.md"
  version: "current"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: "GTach running with --transport simbt or --transport simtcp"
  steps:
    - "Launch: python -m gtach --macos --transport simbt --debug"
    - "Complete Bluetooth pairing setup"
    - "Observe DIGITAL display mode"
    - "Watch RPM numeral and screen background over one full sine cycle (~12s)"
  frequency: "always"
  reproducibility_conditions: "All transport modes. RPM text colour is always white. Background is always black."
  error_output: >
    No error in log. SimTransport TX/RX confirms RPM data flowing.
    DisplayManager INFO Performance: 55.0 FPS confirms render loop active.
    No colour-related debug output present.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behaviour

```yaml
behavior:
  expected: >
    RPM text colour changes with RPM band (blue / white / green / yellow / orange / red).
    Screen background fill changes to match the active RPM band colour.
    At danger_start RPM, background pulses orange at 2 Hz.
    At redline_rpm, background pulses red at 2 Hz.
    On first run, operator acknowledgement screen is presented before DIGITAL mode.
    Engine profile (Abarth 595 Turismo default) populates RPM thresholds.
  actual: >
    RPM text is always white regardless of RPM value.
    Screen background is always black.
    No pulse effect.
    No acknowledgement screen (ack_state_manager present but no bands configured).
    No engine profile system.
  impact: >
    Primary safety indicator non-functional. Operator receives no visual warning
    of high or dangerous RPM. The application's core display feature does not work.
  workaround: "None. Numeric RPM value is visible but colour cues are absent."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.11"
  os: "Raspberry Pi Zero 2W, Debian Linux / macOS Apple Silicon (development)"
  dependencies:
    - library: "pygame"
      version: "2.x"
    - library: "pyyaml"
      version: "6.x"
  domain: "domain_1"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    Two distinct root causes:

    1. Defect — silent queue drain failure. The bare except: pass in
       _draw_digital_mode() suppresses OBDResponse decode errors without logging.
       If _last_rpm is never set, rpm=0 always, and the colour threshold
       condition (rpm >= rpm_warning) is never satisfied.

    2. Missing feature — six-band colour system not implemented. Only two
       legacy threshold constants (rpm_warning=6500, rpm_danger=7000) exist.
       DisplayConfig has no RPMBands dataclass, no engine_profile field,
       no band colour lookup, no background fill, and no pulse logic.
       The AcknowledgementStateManager is instantiated but its RPMBands
       parameter is a SimpleNamespace stub with all thresholds=0.

  technical_notes: >
    Proposal workspace/proposal/proposal-rpm-colour-bands-enhancement.md v0.5
    is approved and defines the complete target design:
    - Six bands: blue(idle)/black/green/yellow/orange/red
    - Configurable thresholds via YAML rpm_bands section
    - Engine profiles in engine_profiles.yaml
    - Operator acknowledgement on first run / post-config-change
    - 2 Hz pulse at danger_start and redline_rpm using pygame.time.get_ticks()
    - AcknowledgementStateManager already stubbed; needs RPMBands wired in

    The fix must also add debug logging to the queue drain loop so future
    decode failures are visible.
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code (Tactical Domain)"
  approach: >
    Implement the full RPM colour band enhancement per proposal v0.5.
    See change-f3a1b2c4 and prompt-f3a1b2c4 for implementation specification.
  change_ref: "change-f3a1b2c4"
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Traceability

```yaml
traceability:
  design_refs:
    - "workspace/design/design-gtach-master.md"
    - "workspace/design/design-2c6b8e4d-domain_display.md"
  change_refs:
    - "change-f3a1b2c4"
  test_refs: []
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-07 | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
