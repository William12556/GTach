# T02 Change Template

Created: 2025-12-12

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T02 Change Template v1.0 - YAML Format
# Optimized for LM code generation context efficiency

change_info:
  id: ""  # change-<uuid> format
  title: ""
  date: ""
  author: ""
  status: ""  # proposed, approved, implemented, verified, rejected
  priority: ""  # critical, high, medium, low
  iteration: 1  # Increments with each debug cycle
  coupled_docs:
    issue_ref: "issue-<uuid>"  # Must reference source issue UUID
    issue_iteration: 1  # Must match issue.iteration

source:
  type: ""  # issue, human_request, enhancement, refactor
  reference: ""  # Link to source issue or request
  description: ""

scope:
  summary: ""
  affected_components:
    - name: ""
      file_path: ""
      change_type: ""  # add, modify, delete, refactor
  affected_designs:
    - design_ref: ""
      sections:
        - ""
  out_of_scope:
    - ""

rational:
  problem_statement: ""
  proposed_solution: ""
  alternatives_considered:
    - option: ""
      reason_rejected: ""
  benefits:
    - ""
  risks:
    - risk: ""
      mitigation: ""

technical_details:
  current_behavior: ""
  proposed_behavior: ""
  implementation_approach: ""
  code_changes:
    - component: ""
      file: ""
      change_summary: ""
      functions_affected:
        - ""
      classes_affected:
        - ""
  data_changes:
    - entity: ""
      change_type: ""  # schema, validation, migration
      details: ""
  interface_changes:
    - interface: ""
      change_type: ""  # signature, contract, protocol
      details: ""
      backward_compatible: ""  # yes, no, n/a

dependencies:
  internal:
    - component: ""
      impact: ""
  external:
    - library: ""
      version_change: ""
      impact: ""
  required_changes:
    - change_ref: ""
      relationship: ""  # blocks, blocked_by, related

testing_requirements:
  test_approach: ""
  test_cases:
    - scenario: ""
      expected_result: ""
  regression_scope:
    - ""
  validation_criteria:
    - ""

implementation:
  effort_estimate: ""  # hours, days
  implementation_steps:
    - step: ""
      owner: ""
  rollback_procedure: ""
  deployment_notes: ""

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found:
    - issue_ref: ""

traceability:
  design_updates:
    - design_ref: ""
      sections_updated:
        - ""
      update_date: ""
  related_changes:
    - change_ref: ""
      relationship: ""
  related_issues:
    - issue_ref: ""
      relationship: ""

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
  schema_type: "t02_change"
```

---

## Schema

```yaml
# T02 Change Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - change_info
  - source
  - scope
  - rational
  - technical_details

properties:
  change_info:
    type: object
    required:
      - id
      - title
      - date
      - status
      - iteration
      - coupled_docs
    properties:
      id:
        type: string
        pattern: "^change-[0-9a-f]{8}$"
      title:
        type: string
      date:
        type: string
      author:
        type: string
      status:
        type: string
        enum:
          - proposed
          - approved
          - implemented
          - verified
          - rejected
      priority:
        type: string
        enum:
          - critical
          - high
          - medium
          - low
      iteration:
        type: integer
        minimum: 1
        description: "Increments with each debug cycle"
      coupled_docs:
        type: object
        required:
          - issue_ref
          - issue_iteration
        properties:
          issue_ref:
            type: string
            pattern: "^issue-[0-9a-f]{8}$"
          issue_iteration:
            type: integer
            minimum: 1
  
  source:
    type: object
    required:
      - type
      - description
    properties:
      type:
        type: string
        enum:
          - issue
          - human_request
          - enhancement
          - refactor
      reference:
        type: string
      description:
        type: string
  
  scope:
    type: object
    required:
      - summary
      - affected_components
    properties:
      summary:
        type: string
      affected_components:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            file_path:
              type: string
            change_type:
              type: string
              enum:
                - add
                - modify
                - delete
                - refactor
      affected_designs:
        type: array
        items:
          type: object
          properties:
            design_ref:
              type: string
            sections:
              type: array
              items:
                type: string
      out_of_scope:
        type: array
        items:
          type: string
  
  rational:
    type: object
    required:
      - problem_statement
      - proposed_solution
    properties:
      problem_statement:
        type: string
      proposed_solution:
        type: string
      alternatives_considered:
        type: array
        items:
          type: object
          properties:
            option:
              type: string
            reason_rejected:
              type: string
      benefits:
        type: array
        items:
          type: string
      risks:
        type: array
        items:
          type: object
          properties:
            risk:
              type: string
            mitigation:
              type: string
  
  technical_details:
    type: object
    required:
      - current_behavior
      - proposed_behavior
      - implementation_approach
    properties:
      current_behavior:
        type: string
      proposed_behavior:
        type: string
      implementation_approach:
        type: string
      code_changes:
        type: array
        items:
          type: object
          properties:
            component:
              type: string
            file:
              type: string
            change_summary:
              type: string
            functions_affected:
              type: array
              items:
                type: string
            classes_affected:
              type: array
              items:
                type: string
      data_changes:
        type: array
        items:
          type: object
          properties:
            entity:
              type: string
            change_type:
              type: string
            details:
              type: string
      interface_changes:
        type: array
        items:
          type: object
          properties:
            interface:
              type: string
            change_type:
              type: string
            details:
              type: string
            backward_compatible:
              type: string
  
  dependencies:
    type: object
    properties:
      internal:
        type: array
        items:
          type: object
          properties:
            component:
              type: string
            impact:
              type: string
      external:
        type: array
        items:
          type: object
          properties:
            library:
              type: string
            version_change:
              type: string
            impact:
              type: string
      required_changes:
        type: array
        items:
          type: object
          properties:
            change_ref:
              type: string
            relationship:
              type: string
  
  testing_requirements:
    type: object
    properties:
      test_approach:
        type: string
      test_cases:
        type: array
        items:
          type: object
          properties:
            scenario:
              type: string
            expected_result:
              type: string
      regression_scope:
        type: array
        items:
          type: string
      validation_criteria:
        type: array
        items:
          type: string
  
  implementation:
    type: object
    properties:
      effort_estimate:
        type: string
      implementation_steps:
        type: array
        items:
          type: object
          properties:
            step:
              type: string
            owner:
              type: string
      rollback_procedure:
        type: string
      deployment_notes:
        type: string
  
  verification:
    type: object
    properties:
      implemented_date:
        type: string
      implemented_by:
        type: string
      verification_date:
        type: string
      verified_by:
        type: string
      test_results:
        type: string
      issues_found:
        type: array
        items:
          type: object
          properties:
            issue_ref:
              type: string
  
  traceability:
    type: object
    properties:
      design_updates:
        type: array
        items:
          type: object
          properties:
            design_ref:
              type: string
            sections_updated:
              type: array
              items:
                type: string
            update_date:
              type: string
      related_changes:
        type: array
        items:
          type: object
          properties:
            change_ref:
              type: string
            relationship:
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
          - t02_change
```

---

## Version History

| Version | Date       | Description                          |
| ------- | ---------- | ------------------------------------ |
| 1.0     | 2025-12-12 | Split from governance.md into separate file for maintainability |
| 1.1     | 2025-12-12 | UUID pattern migration: Replaced NNNN sequence numbering with 8-character UUID format (^[0-9a-f]{8}$) in all fields |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
