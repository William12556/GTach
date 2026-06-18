Created: 2026 June 18

```yaml
prompt_info:
  id: "prompt-f2c8a3e7"
  task_type: "refactor"
  source_ref: "change-f2c8a3e7"
  date: "2026-06-18"
  iteration: 1
  coupled_docs:
    change_ref: "change-f2c8a3e7"
    change_iteration: 1

context:
  purpose: "Remove deprecated macOS platform references from GTach source."
  integration: "Three surgical deletions across platform, transport, and config modules."
  constraints:
    - "Do not modify manager_backup.py or setup_original_backup.py"
    - "Do not remove MockRegistry or pygame mock from platform.py"
    - "No interface changes — deletions only"

specification:
  description: "Delete MACOS enum value, MACOS transport branch, and dead _validate_mac_constraints() method."
  requirements:
    functional:
      - "PlatformType enum no longer contains MACOS"
      - "select_transport() no longer references PlatformType.MACOS"
      - "_validate_mac_constraints() method removed from ConfigValidator"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Minimal delta — delete only, no rewrites"

design:
  architecture: "Surgical deletion"
  components:
    - name: "PlatformType"
      type: "class"
      purpose: "Remove MACOS = auto() line"
      logic:
        - "In src/gtach/utils/platform.py, class PlatformType(Enum):"
        - "Delete the line: MACOS = auto()"
    - name: "select_transport"
      type: "function"
      purpose: "Remove MACOS auto-detect branch"
      logic:
        - "In src/gtach/comm/transport.py, function select_transport():"
        - "Delete: if platform_type == PlatformType.MACOS: return SerialTransport()"
        - "The elif platform_type.name.startswith('RASPBERRY_PI') branch becomes the first branch after explicit transport args"
        - "Result: unsupported platforms reach raise TransportError('Unsupported platform') directly"
    - name: "ConfigValidator._validate_mac_constraints"
      type: "function"
      purpose: "Remove dead method"
      logic:
        - "In src/gtach/utils/config.py, class ConfigValidator:"
        - "Delete the entire _validate_mac_constraints() method"
        - "It is not called from anywhere — no call site to remove"

deliverable:
  format_requirements:
    - "Edit files in place at specified paths"
  files:
    - path: "src/gtach/utils/platform.py"
      content: "Remove MACOS = auto() from PlatformType enum"
    - path: "src/gtach/comm/transport.py"
      content: "Remove MACOS branch from select_transport()"
    - path: "src/gtach/utils/config.py"
      content: "Remove _validate_mac_constraints() method from ConfigValidator"

success_criteria:
  - "grep -r 'MACOS' src/ returns no matches"
  - "grep -r '_validate_mac_constraints' src/ returns no matches"
  - "python3 -c 'from gtach.utils.platform import PlatformType' succeeds without MACOS attribute"
  - "No other source files modified"
```

---

```yaml
tactical_brief: |
  Refactor: remove deprecated macOS references from three source files.

  FILE 1: src/gtach/utils/platform.py
  In class PlatformType(Enum), delete the line:
      MACOS = auto()

  FILE 2: src/gtach/comm/transport.py
  In function select_transport(), after the explicit transport arg
  handling (simtcp/simbt, tcp, serial, rfcomm), delete this block:
      if platform_type == PlatformType.MACOS:
          return SerialTransport()
  The elif that follows becomes the new first branch in the
  auto-detect section. Also remove PlatformType from the import
  in transport.py if it is no longer referenced after this change
  (verify before removing).

  FILE 3: src/gtach/utils/config.py
  In class ConfigValidator, delete the entire _validate_mac_constraints()
  method. It has no call site — pure dead code.

  CONSTRAINTS:
  - Do not touch manager_backup.py or setup_original_backup.py
  - Do not remove MockRegistry or pygame mock from platform.py
  - Deletions only — no rewrites or reformatting

  VERIFY:
  grep -r 'MACOS' src/
  grep -r '_validate_mac_constraints' src/
  Both must return no matches.
```
