Created: 2026 May 06

# Issue: Splash Screen Displays Version Text

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [Version History](<#version history>)

---

```yaml
issue_info:
  id: "issue-f1a3c5e7"
  title: "Splash screen displays version text in automotive mode"
  date: "2026-05-06"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Visual test on Mac and Pi. Version string "v1.0.0" visible on splash screen.
    Requirement: automotive mode splash should show title only (no version, no subtitle).

affected_scope:
  components:
    - name: "SplashScreen._render_graphics"
      file_path: "src/gtach/display/splash.py"
  designs: []
  version: "current"

reproduction:
  prerequisites: "GTach installed and runnable"
  steps:
    - "Run: python -m gtach --macos --debug  (or run on Pi)"
    - "Observe splash screen"
  frequency: "always"
  reproducibility_conditions: "automotive graphics mode (default)"
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: "Automotive mode splash: title only, no version text, no subtitle"
  actual: "Version text \"v1.0.0\" rendered at center_y + 105 in automotive mode block"
  impact: "Cosmetic — version string visible on splash contrary to minimalist design intent"
  workaround: "None"

environment:
  python_version: "3.9+ (Pi), 3.11 (Mac)"
  os: "macOS (dev), Raspberry Pi OS Debian 12 (Pi)"
  dependencies:
    - library: "pygame"
      version: "current"
  domain: "display"

analysis:
  root_cause: >
    splash.py _render_graphics() automotive mode block calls
    self._draw_version_text(surface, center_x, center_y + 105) at line ~392.
    Prior fix correctly removed only the subtitle call; version call was not removed.
    _version_text defaults to "v1.0.0" (hardcoded placeholder at line 138).
  technical_notes: >
    Fix: remove self._draw_version_text(...) call from the automotive mode else-block.
    Method definition and _version_text field must remain intact (used by text_only
    and minimal modes). Qualifies for §1.4.12 trivial change exemption: single call
    site, net delta 1 line, no interface change, unambiguous.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial issue — visual test observation |

---

Copyright (c) 2026 William Watson. MIT License.
