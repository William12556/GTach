Created: 2026 May 06

# Issue: Michroma Font Missing from Pi Wheel

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
  id: "issue-d7f2b4e6"
  title: "Michroma-Regular.ttf not packaged in wheel — missing on Pi deployment"
  date: "2026-05-06"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Pi debug log shows FontManager WARNING: Michroma font not found at
    /opt/gtach/venv/lib/python3.9/site-packages/gtach/assets/fonts/Michroma-Regular.ttf.
    Font file exists in the source tree but pyproject.toml has no package_data entry,
    so setuptools excludes it from the built wheel.

affected_scope:
  components:
    - name: "pyproject.toml — package data configuration"
      file_path: "pyproject.toml"
  designs: []
  version: "0.2.21"

reproduction:
  prerequisites: "Build wheel on Mac and deploy to Pi"
  steps:
    - "Run ./build.sh to produce dist/*.whl"
    - "scp dist/*.whl root@gtach.local:/tmp/"
    - "ssh root@gtach.local '/opt/gtach/install.sh'"
    - "ssh root@gtach.local 'gtach --debug 2>&1 | tee /opt/gtach/gtach-debug.log'"
    - "Search log for 'Michroma'"
  frequency: "always"
  reproducibility_conditions: "Any Pi deployment built from current pyproject.toml"
  preconditions: ""
  test_data: ""
  error_output: >
    2026-05-06 09:36:05,100 FontManager WARNING Michroma font not found at
    /opt/gtach/venv/lib/python3.9/site-packages/gtach/assets/fonts/Michroma-Regular.ttf

behavior:
  expected: >
    Michroma-Regular.ttf present at
    <site-packages>/gtach/assets/fonts/Michroma-Regular.ttf after wheel install.
    FontManager loads Michroma font; no WARNING logged.
  actual: >
    Font file absent from installed package. FontManager falls back to pygame default
    font. Splash and RPM displays render in pygame default font instead of Michroma.
  impact: >
    Visual regression on Pi: RPM display and splash title use default pygame font
    rather than the specified Michroma font. macOS development unaffected (font
    resolved from source tree at development path).
  workaround: "Manually copy Michroma-Regular.ttf to the Pi installation path"

environment:
  python_version: "3.9"
  os: "Raspberry Pi OS Debian 12"
  dependencies:
    - library: "setuptools"
      version: ">=61.0"
  domain: "build"

analysis:
  root_cause: >
    pyproject.toml [tool.setuptools] section lacks a package_data stanza for the
    gtach.assets.fonts package. Setuptools only includes .py files by default;
    non-Python assets (TTF, PNG, YAML, etc.) must be declared explicitly via
    package_data or MANIFEST.in. The font is at
    src/gtach/assets/fonts/Michroma-Regular.ttf and the assets/ directory is a
    Python package (has __init__.py or is discoverable), but the font file itself
    is excluded from the wheel.
  technical_notes: >
    Fix: add [tool.setuptools.package-data] to pyproject.toml:
      "gtach" = ["assets/fonts/*.ttf", "assets/fonts/*.otf"]
    Optionally include other asset types (PNG, YAML) under the same key.
    Verify with: unzip -l dist/*.whl | grep fonts
    after rebuilding.
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
| 0.1 | 2026-05-06 | Initial issue — Pi deployment log observation |

---

Copyright (c) 2026 William Watson. MIT License.
