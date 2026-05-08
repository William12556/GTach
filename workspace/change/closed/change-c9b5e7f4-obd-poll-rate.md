Created: 2026 May 08

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-c9b5e7f4"
  title: "Make OBD poll interval configurable; reduce default to 50ms"
  date: "2026-05-08"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c9b5e7f4"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-c9b5e7f4"

scope:
  summary: >
    Added poll_interval_s parameter to OBDProtocol. Replaced fixed sleep(0.1)
    with sleep(self.poll_interval_s). app.py passes 0.02 for sim/TCP transports.
  affected_components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "GTachApplication._start_obd"
      file_path: "src/gtach/app.py"
      change_type: "modify"

verification:
  implemented_date: "2026-05-08"
  implemented_by: "Claude Code"
  verification_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: >
    Code inspection confirmed. poll_interval_s in OBDProtocol.__init__ (obd.py line 34),
    stored at line 43, used at line 95. app.py passes poll_interval_s=_poll_interval
    at line 132.
  issues_found: []

traceability:
  related_issues:
    - issue_ref: "issue-c9b5e7f4"
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
