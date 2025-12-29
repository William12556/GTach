# T05 Test Template

Created: 2025-12-12

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T05 Test Template v1.0 - YAML Format
# Optimized for LM code generation context efficiency

test_info:
  id: ""  # test-<uuid> format
  title: ""
  date: ""
  author: ""
  status: ""  # planned, in_progress, executed, passed, failed, blocked
  type: ""  # unit, integration, system, acceptance, regression, performance
  priority: ""  # critical, high, medium, low
  iteration: 1  # Increments with each debug cycle
  coupled_docs:
    prompt_ref: "prompt-<uuid>"  # Must reference source prompt UUID
    prompt_iteration: 1  # Must match prompt.iteration
    result_ref: ""  # result-<uuid> when created

source:
  test_target: ""  # Component/feature under test
  design_refs:
    - ""  # Links to design documents
  change_refs:
    - ""  # Links to change documents if testing changes
  requirement_refs:
    - ""  # Links to requirements being validated

scope:
  description: ""
  test_objectives:
    - ""
  in_scope:
    - ""
  out_scope:
    - ""
  dependencies:
    - ""

test_environment:
  python_version: ""
  os: ""
  libraries:
    - name: ""
      version: ""
  test_framework: ""  # pytest, unittest, etc.
  test_data_location: ""

test_cases:
  - case_id: ""  # TC-NNN format
    description: ""
    category: ""  # positive, negative, boundary, edge
    preconditions:
      - ""
    test_steps:
      - step: ""
        action: ""
    inputs:
      - parameter: ""
        value: ""
        type: ""
    expected_outputs:
      - field: ""
        expected_value: ""
        validation: ""
    postconditions:
      - ""
    execution:
      status: ""  # not_run, passed, failed, blocked, skipped
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: ""
    defects:
      - issue_ref: ""  # Link to issue-<uuid> if failed
        description: ""

coverage:
  requirements_covered:
    - requirement_ref: ""
      test_cases:
        - ""
  code_coverage:
    target: ""  # e.g., "80%"
    achieved: ""
  untested_areas:
    - component: ""
      reason: ""

test_execution_summary:
  total_cases: 0
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""  # percentage
  execution_time: ""
  test_cycle: ""  # Initial, Regression, etc.

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues:
    - issue_ref: ""
      severity: ""
      status: ""

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""  # Approved, Rejected, Conditional

traceability:
  requirements:
    - requirement_ref: ""
      test_cases:
        - ""
  designs:
    - design_ref: ""
      test_cases:
        - ""
  changes:
    - change_ref: ""
      test_cases:
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
  schema_type: "t05_test"
```

---

## Schema

```yaml
# T05 Test Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - test_info
  - source
  - scope
  - test_cases

properties:
  test_info:
    type: object
    required:
      - id
      - title
      - date
      - status
      - type
      - iteration
      - coupled_docs
    properties:
      id:
        type: string
        pattern: "^test-[0-9a-f]{8}$"
      title:
        type: string
      date:
        type: string
      author:
        type: string
      status:
        type: string
        enum:
          - planned
          - in_progress
          - executed
          - passed
          - failed
          - blocked
      type:
        type: string
        enum:
          - unit
          - integration
          - system
          - acceptance
          - regression
          - performance
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
      coupled_docs:
        type: object
        required:
          - prompt_ref
          - prompt_iteration
        properties:
          prompt_ref:
            type: string
            pattern: "^prompt-[0-9a-f]{8}$"
          prompt_iteration:
            type: integer
            minimum: 1
          result_ref:
            type: string
            pattern: "^result-[0-9a-f]{8}$"
  
  source:
    type: object
    required:
      - test_target
    properties:
      test_target:
        type: string
      design_refs:
        type: array
        items:
          type: string
      change_refs:
        type: array
        items:
          type: string
      requirement_refs:
        type: array
        items:
          type: string
  
  scope:
    type: object
    required:
      - description
    properties:
      description:
        type: string
      test_objectives:
        type: array
        items:
          type: string
      in_scope:
        type: array
        items:
          type: string
      out_scope:
        type: array
        items:
          type: string
      dependencies:
        type: array
        items:
          type: string
  
  test_environment:
    type: object
    properties:
      python_version:
        type: string
      os:
        type: string
      libraries:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            version:
              type: string
      test_framework:
        type: string
      test_data_location:
        type: string
  
  test_cases:
    type: array
    items:
      type: object
      required:
        - case_id
        - description
      properties:
        case_id:
          type: string
          pattern: "^TC-[0-9]{3}$"
        description:
          type: string
        category:
          type: string
          enum:
            - positive
            - negative
            - boundary
            - edge
        preconditions:
          type: array
          items:
            type: string
        test_steps:
          type: array
          items:
            type: object
            properties:
              step:
                type: string
              action:
                type: string
        inputs:
          type: array
          items:
            type: object
            properties:
              parameter:
                type: string
              value:
                type: string
              type:
                type: string
        expected_outputs:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              expected_value:
                type: string
              validation:
                type: string
        postconditions:
          type: array
          items:
            type: string
        execution:
          type: object
          properties:
            status:
              type: string
              enum:
                - not_run
                - passed
                - failed
                - blocked
                - skipped
            executed_date:
              type: string
            executed_by:
              type: string
            actual_result:
              type: string
            pass_fail_criteria:
              type: string
        defects:
          type: array
          items:
            type: object
            properties:
              issue_ref:
                type: string
              description:
                type: string
  
  coverage:
    type: object
    properties:
      requirements_covered:
        type: array
        items:
          type: object
          properties:
            requirement_ref:
              type: string
            test_cases:
              type: array
              items:
                type: string
      code_coverage:
        type: object
        properties:
          target:
            type: string
          achieved:
            type: string
      untested_areas:
        type: array
        items:
          type: object
          properties:
            component:
              type: string
            reason:
              type: string
  
  test_execution_summary:
    type: object
    properties:
      total_cases:
        type: integer
      passed:
        type: integer
      failed:
        type: integer
      blocked:
        type: integer
      skipped:
        type: integer
      pass_rate:
        type: string
      execution_time:
        type: string
      test_cycle:
        type: string
  
  defect_summary:
    type: object
    properties:
      total_defects:
        type: integer
      critical:
        type: integer
      high:
        type: integer
      medium:
        type: integer
      low:
        type: integer
      issues:
        type: array
        items:
          type: object
          properties:
            issue_ref:
              type: string
            severity:
              type: string
            status:
              type: string
  
  verification:
    type: object
    properties:
      verified_date:
        type: string
      verified_by:
        type: string
      verification_notes:
        type: string
      sign_off:
        type: string
        enum:
          - Approved
          - Rejected
          - Conditional
  
  traceability:
    type: object
    properties:
      requirements:
        type: array
        items:
          type: object
          properties:
            requirement_ref:
              type: string
            test_cases:
              type: array
              items:
                type: string
      designs:
        type: array
        items:
          type: object
          properties:
            design_ref:
              type: string
            test_cases:
              type: array
              items:
                type: string
      changes:
        type: array
        items:
          type: object
          properties:
            change_ref:
              type: string
            test_cases:
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
          - t05_test
```

---

## Version History

| Version | Date       | Description                          |
| ------- | ---------- | ------------------------------------ |
| 1.0     | 2025-12-12 | Split from governance.md into separate file for maintainability |
| 1.1     | 2025-12-12 | UUID pattern migration: Replaced NNNN sequence numbering with 8-character UUID format (^[0-9a-f]{8}$) in all fields |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
