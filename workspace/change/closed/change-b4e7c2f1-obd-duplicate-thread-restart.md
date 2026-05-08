Created: 2026 May 08

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-b4e7c2f1"
  title: "Add stop_func to ThreadInfo to prevent duplicate threads on watchdog restart"
  date: "2026-05-08"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b4e7c2f1"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b4e7c2f1"

scope:
  summary: >
    Added optional stop_func callable to ThreadInfo. ThreadManager._restart_thread
    calls stop_func() before spawning replacement thread. OBDProtocol registers
    self.stop as stop_func at thread registration time.
  affected_components:
    - name: "ThreadInfo"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "ThreadManager._restart_thread"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "OBDProtocol.__init__"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"

verification:
  implemented_date: "2026-05-08"
  implemented_by: "Claude Code"
  verification_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: >
    Code inspection confirmed. stop_func field in ThreadInfo (thread.py line 61).
    register_thread accepts stop_func kwarg (line 200). _restart_thread calls
    stop_func before new thread (lines 381-387). OBDProtocol passes self.stop
    as stop_func (obd.py line 50).
  issues_found: []

traceability:
  related_issues:
    - issue_ref: "issue-b4e7c2f1"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial change document"
  - version: "1.1"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Closed — implementation verified in source"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial change document |
| 1.1 | 2026-05-08 | Closed — implementation verified in source |

---

Copyright (c) 2026 William Watson. MIT License.
