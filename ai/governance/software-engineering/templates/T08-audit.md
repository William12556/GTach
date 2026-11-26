Created: 2026 June 28

# T08 Audit Template

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](#version-history)

---

## Template

```yaml
# T08 Audit Template v1.0 - YAML Format
# Audit report deliverable for P02. Used by both audit modes:
#   strategic (Claude Desktop, authored directly) and
#   tactical (engine audit loop, archived from audit-report.md).

audit_info:
  id: ""  # audit-<uuid> format
  title: ""
  date: ""
  mode: ""  # strategic, tactical
  class: ""  # optional: verification, ad_hoc (P02.10)
  status: ""  # open, in_progress, complete, closed
  auditor: ""  # planner, or engine model identifier

scope:
  target: ""  # path to audited source tree (e.g. /path/to/project/src/)
  criteria:
    - ""  # e.g. protocol_compliance, naming_consistency, error_handling, security, dead_code
  exclusions:
    - ""

findings:
  critical:
    - location: ""  # file:line or file::symbol
      description: ""
      issue_ref: ""  # issue-<uuid> when promoted via P03
  high:
    - location: ""
      description: ""
      issue_ref: ""
  medium:
    - location: ""
      description: ""
  low:
    - location: ""
      description: ""
  info:  # optional
    - location: ""
      description: ""

observations:  # optional; verification audits: pre-existing defects noticed in passing, one line each (P02.10.1)
  - ""

metrics:
  items_audited: 0
  findings_total: 0
  findings_by_severity:
    critical: 0
    high: 0
    medium: 0
    low: 0
    info: 0  # optional

recommendations:
  - ""

traceability:
  design_refs:
    - ""
  issue_refs:
    - ""  # issues created from findings
  related_audits:
    - audit_ref: ""
      relationship: ""  # verification, supersedes, related

notes: ""

version_history:
  - version: ""
    date: ""
    changes:
      - ""

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "audit"
```

[Return to Table of Contents](#table-of-contents)

---

## Schema

```yaml
# T08 Audit Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - audit_info
  - scope
  - findings

properties:
  audit_info:
    type: object
    required:
      - id
      - title
      - date
      - mode
      - status
    properties:
      id:
        type: string
        pattern: "^audit-[0-9a-f]{8}$"
      title:
        type: string
      date:
        type: string
      mode:
        type: string
        enum:
          - strategic
          - tactical
      class:
        type: string
        enum:
          - verification
          - ad_hoc
      status:
        type: string
        enum:
          - open
          - in_progress
          - complete
          - closed
      auditor:
        type: string

  scope:
    type: object
    required:
      - target
      - criteria
    properties:
      target:
        type: string
      criteria:
        type: array
        items:
          type: string
      exclusions:
        type: array
        items:
          type: string

  findings:
    type: object
    properties:
      critical:
        type: array
        items:
          type: object
          properties:
            location:
              type: string
            description:
              type: string
            issue_ref:
              type: string
      high:
        type: array
        items:
          type: object
          properties:
            location:
              type: string
            description:
              type: string
            issue_ref:
              type: string
      medium:
        type: array
        items:
          type: object
          properties:
            location:
              type: string
            description:
              type: string
      low:
        type: array
        items:
          type: object
          properties:
            location:
              type: string
            description:
              type: string
      info:
        type: array
        items:
          type: object
          properties:
            location:
              type: string
            description:
              type: string

  observations:
    type: array
    items:
      type: string

  metrics:
    type: object
    properties:
      items_audited:
        type: integer
      findings_total:
        type: integer
      findings_by_severity:
        type: object
        properties:
          critical:
            type: integer
          high:
            type: integer
          medium:
            type: integer
          low:
            type: integer
          info:
            type: integer

  recommendations:
    type: array
    items:
      type: string

  traceability:
    type: object
    properties:
      design_refs:
        type: array
        items:
          type: string
      issue_refs:
        type: array
        items:
          type: string
      related_audits:
        type: array
        items:
          type: object
          properties:
            audit_ref:
              type: string
            relationship:
              type: string

  notes:
    type: string

  version_history:
    type: array
    items:
      type: object
      properties:
        version:
          type: string
        date:
          type: string
        changes:
          type: array
          items:
            type: string

  metadata:
    type: object
    required:
      - template_version
      - schema_type
    properties:
      copyright:
        type: string
      template_version:
        type: string
      schema_type:
        type: string
        enum:
          - audit
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date       | Description |
| ------- | ---------- | ----------- |
| 1.0     | 2026-06-28 | Initial audit report template; supports strategic and tactical audit modes |
| 1.1 | 2026-09-25 | change-5bcd46ad: layout and terminology migration (engine and governance paths; AEL → engine, Ralph Loop → loop, ael-mcp → engine-mcp) |
| 1.2 | 2026-10-01 | Terminology: Strategic Domain → planner, Tactical Domain → worker and reviewer (change-155cc014) |
| 1.3 | 2026-11-07 | change-e4428fd5: schema_type class word |
| 1.4 | 2026-11-14 | Layout conformance with README.md v4.5: Return to Table of Contents links added (dev/task.md work item 7a) |
| 1.5 | 2026-11-18 | Governance 12.13: optional `audit_info.class` (verification, ad_hoc), `info` findings and count, `observations` |
| 1.6 | 2026-11-25 | Governance 12.14: `relationship` value `verification` replaces `follow_up` |

---

Copyright (c) 2026 William Watson. MIT License.
