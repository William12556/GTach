# T07 Requirements Template

Created: 2025-12-13

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T07 Requirements Template v1.0 - YAML Format
# Optimized for LM code generation context efficiency

project_info:
  name: ""
  version: ""
  date: ""
  author: ""
  status: ""  # active, approved, closed

functional_requirements:
  - id: ""  # <8-char-uuid>
    type: "functional"
    description: ""
    acceptance_criteria:
      - ""
    source: ""  # stakeholder, regulation, constraint
    rationale: ""
    dependencies:
      - ""  # List of requirement IDs this depends on

non_functional_requirements:
  - id: ""  # <8-char-uuid>
    type: "non_functional"
    category: ""  # performance, security, reliability, usability, maintainability
    description: ""
    acceptance_criteria:
      - ""
    target_metric: ""  # Quantifiable target (e.g., "response time < 100ms")
    source: ""
    rationale: ""
    dependencies:
      - ""

architectural_requirements:
  - id: ""  # <8-char-uuid>
    type: "architectural"
    description: ""
    acceptance_criteria:
      - ""
    constraints:
      - ""
    source: ""
    rationale: ""
    dependencies:
      - ""

traceability:
  design_refs:
    - req_id: ""
      design_doc: ""
      design_section: ""
  test_refs:
    - req_id: ""
      test_doc: ""
      test_id: ""
  code_refs:
    - req_id: ""
      component: ""
      file_path: ""

validation:
  completeness_check: ""  # All requirements captured
  clarity_check: ""  # All requirements unambiguous
  testability_check: ""  # All requirements testable
  conflicts_identified:
    - req_id_1: ""
      req_id_2: ""
      conflict_description: ""
      resolution: ""

version_history:
  - version: ""
    date: ""
    author: ""
    changes:
      - ""

metadata:
  copyright: "Copyright (c) 2025 William Watson. This work is licensed under the MIT License."
  template_version: "1.0"
  schema_type: "t07_requirements"
```

---

## Schema

```yaml
# T07 Requirements Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - project_info
  - functional_requirements
  - non_functional_requirements
  - traceability
  - validation

properties:
  project_info:
    type: object
    required:
      - name
      - version
      - date
      - status
    properties:
      name:
        type: string
      version:
        type: string
      date:
        type: string
      author:
        type: string
      status:
        type: string
        enum:
          - active
          - approved
          - closed
  
  functional_requirements:
    type: array
    items:
      type: object
      required:
        - id
        - type
        - description
        - acceptance_criteria
      properties:
        id:
          type: string
          pattern: "^[0-9a-f]{8}$"
          description: "8-character UUID prefix"
        type:
          type: string
          enum:
            - functional
        description:
          type: string
        acceptance_criteria:
          type: array
          items:
            type: string
        source:
          type: string
        rationale:
          type: string
        dependencies:
          type: array
          items:
            type: string
            pattern: "^[0-9a-f]{8}$"
  
  non_functional_requirements:
    type: array
    items:
      type: object
      required:
        - id
        - type
        - category
        - description
        - acceptance_criteria
      properties:
        id:
          type: string
          pattern: "^[0-9a-f]{8}$"
        type:
          type: string
          enum:
            - non_functional
        category:
          type: string
          enum:
            - performance
            - security
            - reliability
            - usability
            - maintainability
        description:
          type: string
        acceptance_criteria:
          type: array
          items:
            type: string
        target_metric:
          type: string
        source:
          type: string
        rationale:
          type: string
        dependencies:
          type: array
          items:
            type: string
            pattern: "^[0-9a-f]{8}$"
  
  architectural_requirements:
    type: array
    items:
      type: object
      required:
        - id
        - type
        - description
        - acceptance_criteria
      properties:
        id:
          type: string
          pattern: "^[0-9a-f]{8}$"
        type:
          type: string
          enum:
            - architectural
        description:
          type: string
        acceptance_criteria:
          type: array
          items:
            type: string
        constraints:
          type: array
          items:
            type: string
        source:
          type: string
        rationale:
          type: string
        dependencies:
          type: array
          items:
            type: string
            pattern: "^[0-9a-f]{8}$"
  
  traceability:
    type: object
    properties:
      design_refs:
        type: array
        items:
          type: object
          properties:
            req_id:
              type: string
              pattern: "^[0-9a-f]{8}$"
            design_doc:
              type: string
            design_section:
              type: string
      test_refs:
        type: array
        items:
          type: object
          properties:
            req_id:
              type: string
              pattern: "^[0-9a-f]{8}$"
            test_doc:
              type: string
            test_id:
              type: string
      code_refs:
        type: array
        items:
          type: object
          properties:
            req_id:
              type: string
              pattern: "^[0-9a-f]{8}$"
            component:
              type: string
            file_path:
              type: string
  
  validation:
    type: object
    properties:
      completeness_check:
        type: string
      clarity_check:
        type: string
      testability_check:
        type: string
      conflicts_identified:
        type: array
        items:
          type: object
          properties:
            req_id_1:
              type: string
              pattern: "^[0-9a-f]{8}$"
            req_id_2:
              type: string
              pattern: "^[0-9a-f]{8}$"
            conflict_description:
              type: string
            resolution:
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
          - t07_requirements
```

---

## Version History

| Version | Date       | Description                          |
| ------- | ---------- | ------------------------------------ |
| 1.0     | 2025-12-13 | Initial creation for P10 Requirements protocol |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
