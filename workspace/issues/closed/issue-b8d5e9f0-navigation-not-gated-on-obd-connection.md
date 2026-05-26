Created: 2026 May 20

# Issue: Display Navigation Not Gated on OBD Connection State

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
issue_info:
  id: "issue-b8d5e9f0"
  title: "Display navigation not gated on OBD connection state"
  date: "2026-05-20"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-b8d5e9f0"
    change_iteration: 1

source:
  origin: "user_report"
  description: >
    Swipe gestures navigate between DIGITAL and RADIAL display modes freely
    despite no OBD connection. Only setup mode should be accessible while
    OBD is disconnected.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  version: "0.2.44"

behavior:
  expected: >
    While OBD is disconnected, swipe navigation between DIGITAL and RADIAL
    is blocked. Only long-press to enter setup mode is permitted.
  actual: "Swipe gestures freely navigate between modes regardless of OBD connection state."
  impact: "User can interact with displays showing meaningless RPM=0 data."

resolution:
  assigned_to: "Claude Code"
  approach: "Implemented per change-b8d5e9f0."
  change_ref: "change-b8d5e9f0"
  resolved_date: "2026-05-26"
  resolved_by: "Claude Code"
  fix_description: >
    Guard clause added at top of _handle_swipe_left() and _handle_swipe_right().
    Returns TouchAction.NONE with DEBUG log when transport thread is not RUNNING.
    Long-press unaffected.

verification:
  verified_date: "2026-05-26"
  verified_by: "William Watson"
  test_results: "'Swipe blocked: OBD not connected' log confirmed at lines 135 and 154 in manager.py."
  closure_notes: "All success criteria met. Prompt audit confirmed."

traceability:
  change_refs:
    - "change-b8d5e9f0"

version_history:
  - version: "1.0"
    date: "2026-05-20"
    author: "William Watson"
    changes:
      - "Initial issue creation."
  - version: "1.1"
    date: "2026-05-26"
    author: "William Watson"
    changes:
      - "Closed — implementation verified."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes                          |
|---------|------------|----------------------------------|
| 1.0     | 2026-05-20 | Initial creation                 |
| 1.1     | 2026-05-26 | Closed — implementation verified |

---

Copyright (c) 2026 William Watson. MIT License.
