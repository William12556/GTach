Created: 2026 June 18

```yaml
issue_info:
  id: "issue-f2c8a3e7"
  title: "Remove macOS platform support from source"
  date: "2026-06-18"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "requirement_change"
  iteration: 1
  coupled_docs:
    change_ref: "change-f2c8a3e7"
    change_iteration: 1

source:
  origin: "requirement_change"
  description: >
    macOS runtime support has been deprecated. Scripts and pyproject.toml were
    cleaned in Phase 1. Three source artefacts retain macOS references:
    PlatformType.MACOS enum value, a transport auto-detect branch for MACOS,
    and a dead _validate_mac_constraints() method in ConfigValidator.

affected_scope:
  components:
    - name: "PlatformType"
      file_path: "src/gtach/utils/platform.py"
    - name: "select_transport"
      file_path: "src/gtach/comm/transport.py"
    - name: "ConfigValidator._validate_mac_constraints"
      file_path: "src/gtach/utils/config.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.63"

reproduction:
  prerequisites: "Inspect source"
  steps:
    - "grep -r MACOS src/"
  frequency: "always"

behavior:
  expected: "No macOS references in source"
  actual: "PlatformType.MACOS enum value present; transport auto-detect branch for MACOS present; dead _validate_mac_constraints() method present"
  impact: "Dead code; misleading platform enum"
  workaround: "None required — macOS path is unreachable at runtime"

environment:
  python_version: "3.9"
  os: "Linux (Raspberry Pi)"
  domain: "domain_2"

analysis:
  root_cause: "macOS support was removed from scripts and config in Phase 1 but source was deferred"
  technical_notes: >
    _validate_mac_constraints() is never called from _validate_platform_constraints().
    It is pure dead code. The MACOS enum value and transport branch are the remaining
    active references.

resolution:
  assigned_to: "Claude Code"
  approach: "Remove MACOS enum value; remove transport branch; delete dead method"
  change_ref: "change-f2c8a3e7"

traceability:
  change_refs:
    - "change-f2c8a3e7"

version_history:
  - version: "1.0"
    date: "2026-06-18"
    author: "William Watson"
    changes:
      - "Initial issue"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
