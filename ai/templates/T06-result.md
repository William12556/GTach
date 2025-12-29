# T06 Result Template

Created: 2025-12-12

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T06 Result Template v1.0 - YAML Format
# Test execution results documentation

result_info:
  id: ""  # result-<uuid> format
  title: ""
  date: ""
  executor: ""
  status: ""  # passed, failed, blocked, partial
  iteration: 1  # Matches parent test iteration
  coupled_docs:
    test_ref: "test-<uuid>"  # Must reference parent test UUID
    test_iteration: 1  # Must match test.iteration

execution:
  timestamp: ""
  environment:
    python_version: ""
    os: ""
    test_framework: ""
  duration: ""

summary:
  total_cases: 0
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""

failures:
  - case_id: ""
    description: ""
    error_output: ""
    stack_trace: ""
    issue_created: ""  # issue-<uuid> if failure triggered issue

passed_cases:
  - case_id: ""
    description: ""
    execution_time: ""

coverage:
  code_coverage: ""
  requirements_validated:
    - ""

issues_created:
  - issue_ref: "issue-<uuid>"
    severity: ""
    description: ""

recommendations:
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
  schema_type: "t06_result"
```

---

## Schema

```yaml
# T06 Result Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - result_info
  - execution
  - summary

properties:
  result_info:
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
        pattern: "^result-[0-9a-f]{8}$"
      title:
        type: string
      date:
        type: string
      executor:
        type: string
      status:
        type: string
        enum:
          - passed
          - failed
          - blocked
          - partial
      iteration:
        type: integer
        minimum: 1
      coupled_docs:
        type: object
        required:
          - test_ref
          - test_iteration
        properties:
          test_ref:
            type: string
            pattern: "^test-[0-9a-f]{8}$"
          test_iteration:
            type: integer
            minimum: 1
  
  execution:
    type: object
    required:
      - timestamp
    properties:
      timestamp:
        type: string
      environment:
        type: object
        properties:
          python_version:
            type: string
          os:
            type: string
          test_framework:
            type: string
      duration:
        type: string
  
  summary:
    type: object
    required:
      - total_cases
      - passed
      - failed
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
  
  failures:
    type: array
    items:
      type: object
      properties:
        case_id:
          type: string
        description:
          type: string
        error_output:
          type: string
        stack_trace:
          type: string
        issue_created:
        type: string
        pattern: "^issue-[0-9a-f]{8}$"
  
  passed_cases:
    type: array
    items:
      type: object
      properties:
        case_id:
          type: string
        description:
          type: string
        execution_time:
          type: string
  
  coverage:
    type: object
    properties:
      code_coverage:
        type: string
      requirements_validated:
        type: array
        items:
          type: string
  
  issues_created:
    type: array
    items:
      type: object
      properties:
        issue_ref:
        type: string
        pattern: "^issue-[0-9a-f]{8}$"
        severity:
          type: string
        description:
          type: string
  
  recommendations:
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
          - t06_result
```

---

## Version History

| Version | Date       | Description                          |
| ------- | ---------- | ------------------------------------ |
| 1.0     | 2025-12-12 | Split from governance.md into separate file for maintainability |
| 1.1     | 2025-12-12 | UUID pattern migration: Replaced NNNN sequence numbering with 8-character UUID format (^[0-9a-f]{8}$) in all fields |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
