# Component Design: GTach Home Directory

Created: 2025-12-29

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [2.0 Component Overview](<#2.0 component overview>)
- [3.0 Function Specification](<#3.0 function specification>)
- [4.0 Path Resolution](<#4.0 path resolution>)
- [5.0 Visual Documentation](<#5.0 visual documentation>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
document_info:
  document_id: "design-f8a9b0c1-component_utils_home"
  tier: 3
  domain: "Utilities"
  component: "gtach_home"
  parent: "design-9a1f3c7e-domain_utils.md"
  source_file: "src/gtach/utils/home.py"
  version: "2.0"
  date: "2026-10-07"
  author: "William Watson"
  change_ref: "change-5fbff586"
```

### 1.1 Parent Reference

- **Domain Design**: [design-9a1f3c7e-domain_utils.md](<design-9a1f3c7e-domain_utils.md>)
- **Source Change**: [change-5fbff586](<../change/change-5fbff586-configuration-split.md>)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Component Overview

### 2.1 Purpose

`gtach_home()` is the single location rule for every file GTach reads or writes at runtime. It replaces the former `OBDIIHome` resolver, which searched several locations, treated any path containing `src/gtach` as development, and created directories as a side effect (audit-36b6ea95 E08).

### 2.2 Responsibilities

1. Return `$GTACH_HOME` when set and non-empty.
2. Otherwise return `/opt/gtach`, the installed location on the Pi.
3. Create nothing; callers create directories when they write.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Function Specification

```python
GTACH_HOME_ENV = 'GTACH_HOME'
DEFAULT_GTACH_HOME = Path('/opt/gtach')

def gtach_home() -> Path: ...
```

The function has no side effects and no caching; changing the environment variable takes effect on the next call.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Path Resolution

| File | Path | Owner |
|---|---|---|
| Configuration | `gtach_home()/config.yaml` (or `--config`) | `ConfigStore` |
| Paired devices | `gtach_home()/config/devices.yaml` | `DeviceStore` |
| Acknowledgement state | `gtach_home()/config/ack_state.yaml` | `AcknowledgementStateManager` |

Log files (`start.log`, `debug.log`, `error.log`, `stacks.log`) keep their fixed paths under `/opt/gtach` in `main.py` and are not resolved through `gtach_home()`.

Development and the test suite set `GTACH_HOME` to a directory of their own, so nothing is written into the repository. The systemd service sets nothing and therefore uses `/opt/gtach`.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Visual Documentation

```mermaid
flowchart TD
    A[gtach_home] --> B{GTACH_HOME set and non-empty?}
    B -- Yes --> C[Path of GTACH_HOME]
    B -- No --> D[/opt/gtach]
    C --> E[ConfigStore, DeviceStore, AcknowledgementStateManager]
    D --> E
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-29 | William Watson | Initial component design document |
| 2.0 | 2026-10-07 | William Watson | Rewritten for [change-5fbff586](<../change/change-5fbff586-configuration-split.md>): OBDIIHome replaced by gtach_home(); GTACH_HOME with default /opt/gtach; no side effects. DeviceStore location per [change-453f0a80](<../change/change-453f0a80-device-store-sharing.md>). Matches commits f5ab73a and 3747d2f. |

---

Copyright (c) 2026 William Watson. MIT License.
