Created: 2026 May 08

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-c9b5e7f4"
  title: "OBD poll rate hard-capped at 10 Hz producing stepped RPM motion"
  date: "2026-05-08"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "performance"
  iteration: 1
  coupled_docs:
    change_ref: "change-c9b5e7f4"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    OBDProtocol._protocol_loop has an unconditional time.sleep(0.1) at the
    end of every polling iteration, hard-capping the RPM data rate at 10 Hz.

affected_scope:
  components:
    - name: "OBDProtocol._protocol_loop"
      file_path: "src/gtach/comm/obd.py"
  version: "0.2.37"

behavior:
  expected: >
    RPM display updates as fast as the transport allows. poll_interval_s configurable per transport.
  actual: >
    Poll rate fixed at 10 Hz regardless of transport speed.
  impact: "RPM motion stepped at 10 Hz. Primary display metric smoothness degraded."
  workaround: "None."

resolution:
  assigned_to: "Claude Code"
  approach: >
    Add poll_interval_s parameter to OBDProtocol.__init__ (default 0.05).
    Replace time.sleep(0.1) with time.sleep(self.poll_interval_s).
    Pass poll_interval_s=0.02 from app.py for sim and TCP transports.
  change_ref: "change-c9b5e7f4"
  resolved_date: "2026-05-08"
  resolved_by: "Claude Code"
  fix_description: >
    poll_interval_s parameter added to OBDProtocol.__init__. sleep(0.1) replaced
    with sleep(self.poll_interval_s). app.py passes 0.02 for sim/TCP transports.

verification:
  verified_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: "Code inspection confirmed. poll_interval_s present in obd.py and app.py."
  closure_notes: "Implemented. Closed."

traceability:
  design_refs: []
  change_refs:
    - "change-c9b5e7f4"
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
