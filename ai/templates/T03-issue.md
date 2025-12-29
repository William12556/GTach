# T03 Issue Template

Created: 2025-12-12

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T03 Issue Template v1.0 - YAML Format
# Optimized for LM code generation context efficiency

issue_info:
  id: ""  # issue-<uuid> format
  title: ""
  date: ""
  reporter: ""
  status: ""  # open, investigating, resolved, verified, closed, deferred
  severity: ""  # critical, high, medium, low
  type: ""  # bug, defect, error, performance, security
  iteration: 1  # Increments with each debug cycle
  coupled_docs:
    change_ref: ""  # change-<uuid> when created
    change_iteration: null  # Matches change.iteration

source:
  origin: ""  # test_result, user_report, code_review, monitoring
  test_ref: ""  # Link to test result if applicable
  description: ""

affected_scope:
  components:
    - name: ""
      file_path: ""
  designs:
    - design_ref: ""
  version: ""  # Code version where issue found

reproduction:
  prerequisites: ""  # Required conditions before issue can occur
  steps:
    - ""
  frequency: ""  # always, intermittent, once
  reproducibility_conditions: ""  # Specific conditions when issue manifests
  preconditions: ""
  test_data: ""
  error_output: ""  # Error messages, stack traces

behavior:
  expected: ""
  actual: ""
  impact: ""  # Functional impact description
  workaround: ""  # Available workaround if any

environment:
  python_version: ""
  os: ""
  dependencies:
    - library: ""
      version: ""
  domain: ""  # domain_1, domain_2

analysis:
  root_cause: ""
  technical_notes: ""
  related_issues:
    - issue_ref: ""
      relationship: ""  # duplicate, related, blocks, blocked_by

resolution:
  assigned_to: ""
  target_date: ""
  approach: ""
  change_ref: ""  # Link to change document
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: ""  # How to prevent similar issues in future
  process_improvements: ""  # Process changes to prevent recurrence

verification_enhanced:
  verification_steps:
    - ""  # Step-by-step verification procedures
  verification_results: ""  # Detailed results of verification testing

traceability:
  design_refs:
    - ""
  change_refs:
    - ""
  test_refs:
    - ""

notes: ""

version_history:
  - version: ""
    date: ""
    author: ""
    changes:
      - ""

metadata:
  copyright: "Copyright (c) 2025 William Watson. This work is licensed under the MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## Schema

```yaml
# T03 Issue Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - issue_info
  - source
  - affected_scope
  - behavior

properties:
  issue_info:
    type: object
    required:
      - id
      - title
      - date
      - status
      - severity
      - type
      - iteration
    properties:
      id:
        type: string
        pattern: "^issue-[0-9a-f]{8}$"
      title:
        type: string
      date:
        type: string
      reporter:
        type: string
      status:
        type: string
        enum:
          - open
          - investigating
          - resolved
          - verified
          - closed
          - deferred
      severity:
        type: string
        enum:
          - critical
          - high
          - medium
          - low
      type:
        type: string
        enum:
          - bug
          - defect
          - error
          - performance
          - security
      iteration:
        type: integer
        minimum: 1
        description: "Increments with each debug cycle"
      coupled_docs:
        type: object
        properties:
          change_ref:
            type: string
            pattern: "^change-[0-9a-f]{8}$"
          change_iteration:
            type: integer
            minimum: 1
  
  source:
    type: object
    required:
      - origin
      - description
    properties:
      origin:
        type: string
        enum:
          - test_result
          - user_report
          - code_review
          - monitoring
      test_ref:
        type: string
      description:
        type: string
  
  affected_scope:
    type: object
    required:
      - components
    properties:
      components:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            file_path:
              type: string
      designs:
        type: array
        items:
          type: object
          properties:
            design_ref:
              type: string
      version:
        type: string
  
  reproduction:
    type: object
    properties:
      steps:
        type: array
        items:
          type: string
      frequency:
        type: string
        enum:
          - always
          - intermittent
          - once
      preconditions:
        type: string
      test_data:
        type: string
      error_output:
        type: string
  
  behavior:
    type: object
    required:
      - expected
      - actual
    properties:
      expected:
        type: string
      actual:
        type: string
      impact:
        type: string
      workaround:
        type: string
  
  environment:
    type: object
    properties:
      python_version:
        type: string
      os:
        type: string
      dependencies:
        type: array
        items:
          type: object
          properties:
            library:
              type: string
            version:
              type: string
      domain:
        type: string
        enum:
          - domain_1
          - domain_2
  
  analysis:
    type: object
    properties:
      root_cause:
        type: string
      technical_notes:
        type: string
      related_issues:
        type: array
        items:
          type: object
          properties:
            issue_ref:
              type: string
            relationship:
              type: string
  
  resolution:
    type: object
    properties:
      assigned_to:
        type: string
      target_date:
        type: string
      approach:
        type: string
      change_ref:
        type: string
      resolved_date:
        type: string
      resolved_by:
        type: string
      fix_description:
        type: string
  
  verification:
    type: object
    properties:
      verified_date:
        type: string
      verified_by:
        type: string
      test_results:
        type: string
      closure_notes:
        type: string
  
  traceability:
    type: object
    properties:
      design_refs:
        type: array
        items:
          type: string
      change_refs:
        type: array
        items:
          type: string
      test_refs:
        type: array
        items:
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
        author:
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
          - t03_issue
```

---

## Version History

| Version | Date       | Description                          |
| ------- | ---------- | ------------------------------------ |
| 1.0     | 2025-12-12 | Split from governance.md into separate file for maintainability |
| 1.1     | 2025-12-12 | UUID pattern migration: Replaced NNNN sequence numbering with 8-character UUID format (^[0-9a-f]{8}$) in all fields |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
