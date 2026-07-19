Created: 2026 June 28

# T08 Audit Template

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T08 Audit Template v1.0 - YAML Format
# Audit report deliverable for P08. Used by both audit modes:
#   strategic (Claude Desktop, authored directly) and
#   tactical (AEL audit loop, archived from audit-report.md).

audit_info:
  id: ""  # audit-<uuid> format
  title: ""
  date: ""
  mode: ""  # strategic, tactical
  status: ""  # open, in_progress, complete, closed
  auditor: ""  # Strategic Domain, or AEL model identifier

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
      issue_ref: ""  # issue-<uuid> when promoted via P04
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

metrics:
  items_audited: 0
  findings_total: 0
  findings_by_severity:
    critical: 0
    high: 0
    medium: 0
    low: 0

recommendations:
  - ""

traceability:
  design_refs:
    - ""
  issue_refs:
    - ""  # issues created from findings
  related_audits:
    - audit_ref: ""
      relationship: ""  # follow_up, supersedes, related

notes: ""

version_history:
  - version: ""
    date: ""
    changes:
      - ""

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t08_audit"
```

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
          - t08_audit
```

---

## Version History

| Version | Date       | Description |
| ------- | ---------- | ----------- |
| 1.0     | 2026-06-28 | Initial audit report template; supports strategic and tactical audit modes |

---

Copyright (c) 2026 William Watson. MIT License.
