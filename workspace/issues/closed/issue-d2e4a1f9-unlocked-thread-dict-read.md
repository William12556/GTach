Created: 2026 May 08

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-d2e4a1f9"
  title: "DisplayManager reads ThreadManager.threads dict without state lock — data race"
  date: "2026-05-08"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-d2e4a1f9"
    change_iteration: 1

source:
  origin: "code_review"
  description: >
    _draw_status_indicator in manager.py accesses self.thread_manager.threads
    directly without acquiring _state_lock.

affected_scope:
  components:
    - name: "DisplayManager._draw_status_indicator"
      file_path: "src/gtach/display/manager.py"
    - name: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
  version: "0.2.37"

behavior:
  expected: "Status indicator reads thread state via locked public API."
  actual: "Direct unlocked dict access bypasses _state_lock."
  impact: "Low. Status indicator may show incorrect state for one frame. No crash risk."
  workaround: "None needed — impact is cosmetic."

analysis:
  root_cause: >
    _draw_status_indicator bypasses ThreadManager's public API. ThreadManager provides
    get_thread_status(name) which acquires _state_lock.
  technical_notes: >
    Replace direct dict access with thread_manager.get_thread_status('transport').

resolution:
  assigned_to: "Claude Code"
  approach: >
    Replace direct threads dict access in _draw_status_indicator with
    thread_manager.get_thread_status('transport').
  change_ref: "change-d2e4a1f9"
  resolved_date: "2026-05-08"
  resolved_by: "Claude Code"
  fix_description: >
    Direct threads dict access replaced with get_thread_status('transport') in
    _draw_status_indicator in manager.py.

verification:
  verified_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: "Code inspection confirmed. get_thread_status used in manager.py line 907."
  closure_notes: "Implemented. Closed."

traceability:
  design_refs: []
  change_refs:
    - "change-d2e4a1f9"
  test_refs: []

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial issue document"
  - version: "1.1"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Closed — implementation verified in source"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial issue document |
| 1.1 | 2026-05-08 | Closed — implementation verified in source |

---

Copyright (c) 2026 William Watson. MIT License.
