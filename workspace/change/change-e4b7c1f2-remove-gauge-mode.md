Created: 2026 May 15

# Change: Remove GAUGE Display Mode

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Testing Requirements](<#6.0 testing requirements>)
- [7.0 Verification](<#7.0 verification>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-e4b7c1f2"
  title: "Remove GAUGE display mode"
  date: "2026-05-15"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e4b7c1f2"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "human_request"
  reference: "issue-e4b7c1f2"
  description: >
    Remove GAUGE display mode. Retain DIGITAL and RADIAL only.
    Update swipe cycle, settings selector, config validation, and
    typography constants accordingly.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Remove all GAUGE mode artefacts from four source files.
    Update swipe navigation to cycle DIGITAL ↔ RADIAL.
    Update settings screen mode selector to show Digital | Radial.
    Update config validation to reject 'GAUGE' as a valid mode.
    Remove gauge-specific typography constants and font method.
  affected_components:
    - name: "DisplayMode enum"
      file_path: "src/gtach/display/models.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "TypographyConstants / FontManager"
      file_path: "src/gtach/display/typography.py"
      change_type: "modify"
    - name: "ConfigManager"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
  out_of_scope:
    - "src/gtach/display/manager_backup.py — non-active backup file"
    - "src/gtach/display/setup_original_backup.py — non-active backup file"
    - "Requirements and design document updates"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    GAUGE mode adds implementation surface without proportionate value.
    The settings selector does not expose the RADIAL mode button, which
    is the more capable of the two arc/needle modes.
  proposed_solution: >
    Remove GAUGE enum value, all rendering methods, typography constants,
    and config validation references. Collapse swipe cycle to two modes.
    Replace the settings selector Digital | Gauge pair with Digital | Radial.
  benefits:
    - "Reduced code surface — five rendering methods removed from manager.py"
    - "Corrected settings selector exposes Radial mode"
    - "Simpler swipe navigation"
  risks:
    - risk: "Stored config.yaml may contain mode: GAUGE"
      mitigation: "On config load, if saved mode is GAUGE fall back to RADIAL"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    Three display modes: DIGITAL, GAUGE, RADIAL.
    Swipe left from DIGITAL → GAUGE → RADIAL → DIGITAL.
    Swipe right from DIGITAL → RADIAL → GAUGE → DIGITAL.
    Settings selector: Digital | Gauge buttons.
    typography.py: GAUGE_CENTER_SIZE, GAUGE_LABEL_SIZE constants; get_gauge_font() method.
    config.py valid_modes includes 'GAUGE'.
  proposed_behavior: >
    Two display modes: DIGITAL, RADIAL.
    Swipe left/right toggles between DIGITAL and RADIAL.
    Settings selector: Digital | Radial buttons.
    typography.py: gauge constants and get_gauge_font() removed.
    config.py valid_modes: ['DIGITAL', 'RADIAL'] only.
    Config load: if stored mode == 'GAUGE', substitute RADIAL.
  implementation_approach: >
    Four targeted file edits. No new files. No interface changes to
    external callers — DisplayMode.GAUGE removal is a breaking enum
    change but GAUGE was never exposed via a public API contract.
  code_changes:
    - component: "DisplayMode"
      file: "src/gtach/display/models.py"
      change_summary: "Remove GAUGE = auto() from enum"
      functions_affected: []
      classes_affected: ["DisplayMode"]
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Remove _draw_gauge_mode, _draw_gauge_zones, _draw_gauge_threshold_line,
        _draw_gauge_needle, _get_rpm_color methods.
        Rewrite _handle_swipe_left and _handle_swipe_right to toggle DIGITAL ↔ RADIAL.
        Remove GAUGE branch from _render_normal_modes.
        Rewrite _render_mode_selector to show Digital | Radial buttons.
        Add GAUGE fallback in _load_config.
      functions_affected:
        - "_handle_swipe_left"
        - "_handle_swipe_right"
        - "_render_normal_modes"
        - "_render_mode_selector"
        - "_load_config"
        - "_draw_gauge_mode"
        - "_draw_gauge_zones"
        - "_draw_gauge_threshold_line"
        - "_draw_gauge_needle"
        - "_get_rpm_color"
    - component: "TypographyConstants / FontManager"
      file: "src/gtach/display/typography.py"
      change_summary: >
        Remove GAUGE_CENTER_SIZE and GAUGE_LABEL_SIZE constants.
        Remove get_gauge_font() method.
      functions_affected:
        - "get_gauge_font"
      classes_affected:
        - "TypographyConstants"
        - "FontManager"
    - component: "ConfigManager"
      file: "src/gtach/utils/config.py"
      change_summary: "Remove 'GAUGE' from valid_modes list; update comment"
      functions_affected: []
      classes_affected: []
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: "Manual functional test on simbt transport"
  test_cases:
    - scenario: "Swipe left from DIGITAL"
      expected_result: "Mode transitions to RADIAL"
    - scenario: "Swipe left from RADIAL"
      expected_result: "Mode transitions to DIGITAL"
    - scenario: "Swipe right from DIGITAL"
      expected_result: "Mode transitions to RADIAL"
    - scenario: "Swipe right from RADIAL"
      expected_result: "Mode transitions to DIGITAL"
    - scenario: "Settings screen opened"
      expected_result: "Digital | Radial selector buttons visible; no Gauge button"
    - scenario: "config.yaml with mode: GAUGE loaded"
      expected_result: "Application starts in RADIAL mode without error"
  validation_criteria:
    - "No AttributeError or NameError referencing DisplayMode.GAUGE at runtime"
    - "No references to _draw_gauge_mode or get_gauge_font in active code paths"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Verification

```yaml
verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author         | Changes          |
|---------|------------|----------------|------------------|
| 1.0     | 2026-05-15 | William Watson | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
