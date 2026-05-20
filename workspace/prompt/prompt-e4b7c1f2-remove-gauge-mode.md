Created: 2026 May 15

# Prompt: Remove GAUGE Display Mode

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Deliverables](<#5.0 deliverables>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Notes](<#7.0 notes>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-e4b7c1f2"
  task_type: "refactor"
  source_ref: "change-e4b7c1f2"
  date: "2026-05-15"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4b7c1f2"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: "Remove GAUGE display mode from GTach. Retain DIGITAL and RADIAL only."
  integration: "Display domain — models.py, manager.py, typography.py, utils/config.py"
  constraints:
    - "Do not modify manager_backup.py or setup_original_backup.py"
    - "Do not create new files"
    - "No interface changes to external callers outside display domain"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Remove all GAUGE mode artefacts across four source files.
    Update navigation, settings selector, and config validation.
  requirements:
    functional:
      - "DisplayMode enum contains DIGITAL and RADIAL only — no GAUGE value"
      - "Swipe left and swipe right both toggle between DIGITAL and RADIAL"
      - "Settings mode selector shows Digital | Radial buttons"
      - "If config.yaml stores mode: GAUGE, load falls back to RADIAL without error"
      - "TypographyConstants has no GAUGE_CENTER_SIZE or GAUGE_LABEL_SIZE"
      - "FontManager has no get_gauge_font() method"
      - "config.py valid_modes is ['DIGITAL', 'RADIAL']"
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Preserve all existing exception handling patterns"
        - "Preserve copyright headers"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Four targeted edits — no structural changes"
  components:
    - name: "models.py"
      type: "module"
      purpose: "Remove GAUGE enum value"
      logic:
        - "Delete line: GAUGE = auto()"

    - name: "manager.py — swipe handlers"
      type: "function"
      purpose: "Collapse three-mode cycle to two-mode toggle"
      logic:
        - "_handle_swipe_left: if DIGITAL → RADIAL; if RADIAL → DIGITAL; remove GAUGE branch"
        - "_handle_swipe_right: same logic as swipe_left (toggle is symmetric)"

    - name: "manager.py — _render_normal_modes"
      type: "function"
      purpose: "Remove GAUGE dispatch branch"
      logic:
        - "Delete elif self.config.mode == DisplayMode.GAUGE: self._draw_gauge_mode()"

    - name: "manager.py — _render_mode_selector"
      type: "function"
      purpose: "Replace Gauge button with Radial button"
      logic:
        - "Second button: label Radial, sets mode to DisplayMode.RADIAL"
        - "Active highlight: button is highlighted when config.mode == DisplayMode.RADIAL"
        - "Touch region id: mode_radial (was mode_gauge)"

    - name: "manager.py — _load_config"
      type: "function"
      purpose: "Guard against stored GAUGE mode"
      logic:
        - "After parsing saved_mode, if saved_mode == DisplayMode.GAUGE substitute DisplayMode.RADIAL"
        - "Note: DisplayMode['GAUGE'] will raise KeyError after enum removal — catch KeyError and fall back to RADIAL"

    - name: "manager.py — remove dead methods"
      type: "function"
      purpose: "Delete GAUGE rendering code"
      logic:
        - "Delete: _draw_gauge_mode, _draw_gauge_zones, _draw_gauge_threshold_line, _draw_gauge_needle, _get_rpm_color"

    - name: "typography.py"
      type: "module"
      purpose: "Remove gauge typography artefacts"
      logic:
        - "Delete: GAUGE_CENTER_SIZE = 28 and GAUGE_LABEL_SIZE = 16 from TypographyConstants"
        - "Delete: get_gauge_font() method from FontManager"
        - "Delete: docstring reference to gauge center in get_rpm_medium_font (line 683)"

    - name: "config.py"
      type: "module"
      purpose: "Remove GAUGE from valid modes"
      logic:
        - "Change: valid_modes = ['DIGITAL', 'GAUGE'] to valid_modes = ['DIGITAL', 'RADIAL']"
        - "Update inline comment on DisplayConfig.mode default if it references GAUGE"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Deliverables

```yaml
deliverable:
  files:
    - path: "src/gtach/display/models.py"
    - path: "src/gtach/display/manager.py"
    - path: "src/gtach/display/typography.py"
    - path: "src/gtach/utils/config.py"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "No AttributeError or NameError referencing DisplayMode.GAUGE at runtime"
  - "Swipe left and right both toggle DIGITAL ↔ RADIAL"
  - "Settings selector shows Digital | Radial; no Gauge button"
  - "Application starts without error when config.yaml contains mode: GAUGE"
  - "grep -r 'DisplayMode.GAUGE' src/gtach/ returns no results (excluding backups)"
  - "grep -r 'get_gauge_font\|GAUGE_CENTER_SIZE\|GAUGE_LABEL_SIZE' src/gtach/ returns no results (excluding backups)"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Notes

```yaml
notes: >
  The _load_config GAUGE fallback must handle both KeyError (enum lookup fails
  after GAUGE is removed) and an explicit value check — whichever is encountered
  depending on execution path. Prefer a try/except KeyError around
  DisplayMode[saved_mode_str] with fallback to RADIAL.
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: >
  Remove GAUGE display mode from GTach. Edit four files only:

  1. src/gtach/display/models.py
     - Delete: GAUGE = auto() from DisplayMode enum

  2. src/gtach/display/manager.py
     - _handle_swipe_left/_handle_swipe_right: replace three-mode cycle with
       DIGITAL ↔ RADIAL toggle (symmetric)
     - _render_normal_modes: delete GAUGE elif branch
     - _render_mode_selector: replace Gauge button with Radial button
       (id=mode_radial, sets mode=DisplayMode.RADIAL, highlight when RADIAL active)
     - _load_config: wrap DisplayMode[saved_mode_str] in try/except KeyError,
       fall back to RADIAL; also substitute RADIAL if parsed mode is GAUGE
     - Delete methods: _draw_gauge_mode, _draw_gauge_zones,
       _draw_gauge_threshold_line, _draw_gauge_needle, _get_rpm_color

  3. src/gtach/display/typography.py
     - Delete: GAUGE_CENTER_SIZE, GAUGE_LABEL_SIZE from TypographyConstants
     - Delete: get_gauge_font() method from FontManager

  4. src/gtach/utils/config.py
     - Change valid_modes to ['DIGITAL', 'RADIAL']

  Do NOT touch manager_backup.py or setup_original_backup.py.
  No new files. No interface changes outside display domain.
  Preserve copyright headers and exception handling patterns.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author         | Changes          |
|---------|------------|----------------|------------------|
| 1.0     | 2026-05-15 | William Watson | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
