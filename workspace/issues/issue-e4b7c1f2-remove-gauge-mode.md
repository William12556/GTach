Created: 2026 May 15

# Issue: Remove GAUGE Display Mode

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Behavior](<#4.0 behavior>)
- [5.0 Analysis](<#5.0 analysis>)
- [6.0 Resolution](<#6.0 resolution>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-e4b7c1f2"
  title: "Remove GAUGE display mode"
  date: "2026-05-15"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "requirement_change"
  iteration: 1
  coupled_docs:
    change_ref: "change-e4b7c1f2"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "requirement_change"
  description: >
    The GAUGE display mode is to be removed from GTach. The application
    will retain two display modes: DIGITAL and RADIAL. The GAUGE mode
    needle-and-arc rendering has not been maintained to the same standard
    as DIGITAL and RADIAL and adds complexity without proportionate value.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "DisplayMode"
      file_path: "src/gtach/display/models.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "FontManager / TypographyConstants"
      file_path: "src/gtach/display/typography.py"
    - name: "ConfigManager"
      file_path: "src/gtach/utils/config.py"
  designs:
    - design_ref: "design-gtach-master.md"
    - design_ref: "design-2c6b8e4d-domain_display.md"
  version: "current"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Behavior

```yaml
behavior:
  expected: >
    Application supports two display modes: DIGITAL and RADIAL.
    Swipe gestures cycle between DIGITAL and RADIAL only.
    Settings screen mode selector shows Digital and Radial buttons.
    No GAUGE enum value, rendering code, or typography constants exist.
  actual: >
    Application supports three display modes: DIGITAL, GAUGE, and RADIAL.
    Swipe gestures cycle through all three modes.
    Settings screen mode selector shows Digital and Gauge buttons (Radial absent).
    GAUGE rendering methods, typography constants, and config validation
    references exist across four source files.
  impact: >
    GAUGE mode is present but underutilised. Its removal simplifies the
    mode cycle, removes dead rendering code, and corrects the settings
    selector to expose the Radial mode button.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Analysis

```yaml
analysis:
  root_cause: "Requirement change — stakeholder decision to remove GAUGE mode."
  technical_notes: >
    GAUGE mode references span four files. The settings screen selector
    currently shows Digital | Gauge; it must be updated to show
    Digital | Radial. The swipe cycle must collapse from three to two modes.
    manager_backup.py is a non-active backup file and is excluded from scope.
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  approach: "See change-e4b7c1f2"
  change_ref: "change-e4b7c1f2"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author         | Changes           |
|---------|------------|----------------|-------------------|
| 1.0     | 2026-05-15 | William Watson | Initial creation  |

---

Copyright (c) 2026 William Watson. MIT License.
