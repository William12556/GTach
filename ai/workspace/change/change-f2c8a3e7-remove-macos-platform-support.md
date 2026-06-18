Created: 2026 June 18

```yaml
change_info:
  id: "change-f2c8a3e7"
  title: "Remove macOS platform support from source"
  date: "2026-06-18"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f2c8a3e7"
    issue_iteration: 1

source:
  type: "requirement_change"
  reference: "issue-f2c8a3e7"
  description: "macOS deprecated. Remove residual source references post Phase 1 cleanup."

scope:
  summary: "Remove PlatformType.MACOS enum value, transport auto-detect MACOS branch, and dead _validate_mac_constraints() method."
  affected_components:
    - name: "PlatformType"
      file_path: "src/gtach/utils/platform.py"
      change_type: "modify"
    - name: "select_transport"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "ConfigValidator"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
  out_of_scope:
    - "manager_backup.py"
    - "setup_original_backup.py"
    - "MockRegistry and pygame mock in platform.py (retained for non-Pi Linux)"

rational:
  problem_statement: "macOS runtime support is deprecated. Three source artefacts retain macOS references after Phase 1 script/config cleanup."
  proposed_solution: "Delete MACOS enum value; remove transport MACOS branch; delete dead _validate_mac_constraints() method."
  benefits:
    - "Eliminates dead code"
    - "Enum accurately reflects supported platforms"
    - "Removes misleading transport branch"

technical_details:
  current_behavior: "PlatformType.MACOS exists in enum; select_transport() has MACOS auto-detect branch; _validate_mac_constraints() exists but is never called."
  proposed_behavior: "Enum contains only Pi variants, LINUX_GENERIC, WINDOWS, UNKNOWN. Transport raises TransportError for non-Pi platforms. Dead method removed."
  implementation_approach: "Surgical deletions only. No interface changes."
  code_changes:
    - component: "PlatformType"
      file: "src/gtach/utils/platform.py"
      change_summary: "Remove MACOS = auto() from enum"
      classes_affected:
        - "PlatformType"
    - component: "select_transport"
      file: "src/gtach/comm/transport.py"
      change_summary: "Remove 'if platform_type == PlatformType.MACOS: return SerialTransport()' branch"
      functions_affected:
        - "select_transport"
    - component: "ConfigValidator"
      file: "src/gtach/utils/config.py"
      change_summary: "Delete _validate_mac_constraints() method (dead code)"
      classes_affected:
        - "ConfigValidator"

testing_requirements:
  test_approach: "Grep verification post-change"
  validation_criteria:
    - "grep -r MACOS src/ returns no matches"
    - "grep -r _validate_mac_constraints src/ returns no matches"
    - "python3 -c 'from gtach.utils.platform import PlatformType; print(PlatformType.MACOS)' raises AttributeError"

version_history:
  - version: "1.0"
    date: "2026-06-18"
    author: "William Watson"
    changes:
      - "Initial change document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
