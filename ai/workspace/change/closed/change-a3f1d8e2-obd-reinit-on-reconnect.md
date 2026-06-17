Created: 2026 May 08

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-a3f1d8e2"
  title: "Skip ATZ on reconnect to eliminate 5-9s RPM data gap"
  date: "2026-05-08"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a3f1d8e2"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-a3f1d8e2"

scope:
  summary: >
    Added _adapter_initialised flag to OBDProtocol. ATZ skipped when flag is True.
    Flag reset in stop() and on inner loop exit (transport disconnect).
  affected_components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"

verification:
  implemented_date: "2026-05-08"
  implemented_by: "Claude Code"
  verification_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: >
    Code inspection confirmed. _adapter_initialised present at obd.py lines 44, 59, 97,
    110, 122.
  issues_found: []

traceability:
  related_issues:
    - issue_ref: "issue-a3f1d8e2"
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
