# T04 Prompt Template

Created: 2025-12-12

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T04 Prompt Template v1.0 - YAML Format
# Optimized for Strategic Domain → Tactical Domain filesystem communication
# Designed for minimal token usage while maintaining completeness

prompt_info:
  id: ""  # prompt-<uuid> format
  task_type: ""  # code_generation, debug, refactor, optimization
  source_ref: ""  # design-<uuid> or change-<uuid>
  date: ""
  priority: ""  # critical, high, medium, low
  iteration: 1  # Increments with each debug cycle
  coupled_docs:
    change_ref: "change-<uuid>"  # Must reference source change UUID
    change_iteration: 1  # Must match change.iteration

behavioral_standards:
  source: ""  # Path to behavioral-standards.yaml (e.g., "workspace/knowledge/behavioral-standards.yaml")
  enforcement_level: ""  # strict, advisory, disabled


tactical_execution:
  mode: ""  # ralph_loop, direct
  worker_model: ""  # Model name for code generation
  reviewer_model: ""  # Model name for review (ralph_loop only)
  max_iterations: 10  # Loop iteration limit (ralph_loop only)
  boundary_conditions:
    token_budget: 50000
    time_limit_minutes: 30

context:
  purpose: ""  # What this code accomplishes
  integration: ""  # How it fits in project
  knowledge_references: [] # workspace/knowledge/ docs consulted
  constraints:
    - ""  # Technical limitations

specification:
  description: ""
  requirements:
    functional:
      - ""
    technical:
      language: "Python"
      version: ""
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: ""
      metric: ""  # time, memory, throughput

design:
  architecture: ""  # Pattern or approach
  components:
    - name: ""
      type: ""  # class, function, module
      purpose: ""
      interface:
        inputs:
          - name: ""
            type: ""
            description: ""
        outputs:
          type: ""
          description: ""
        raises:
          - ""
      logic:
        - ""  # Implementation steps
  dependencies:
    internal:
      - ""
    external:
      - ""

data_schema:
  entities:
    - name: ""
      attributes:
        - name: ""
          type: ""
          constraints: ""
      validation:
        - ""

error_handling:
  strategy: ""  # How errors are handled
  exceptions:
    - exception: ""
      condition: ""
      handling: ""
  logging:
    level: ""  # DEBUG, INFO, WARNING, ERROR
    format: ""

testing:
  unit_tests:
    - scenario: ""
      expected: ""
  edge_cases:
    - ""
  validation:
    - ""

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
  files:
    - path: "src/<component>/<file>.py"
      content: ""

success_criteria:
  - ""

element_registry:
  source: ""  # Path to name registry master (e.g., "workspace/design/design-<project>-name_registry-master.md")
  entries:    # Relevant entries for this code generation task (copied from registry)
    modules:
      - name: ""
        path: ""
    classes:
      - name: ""
        module: ""
    functions:
      - name: ""
        module: ""
        signature: ""
    constants:
      - name: ""
        module: ""
        type: ""

notes: ""

metadata:
  copyright: "Copyright (c) 2025 William Watson. This work is licensed under the MIT License."
  template_version: "1.0"
  schema_type: "t04_prompt"
```

---

## Schema

```yaml
# T04 Prompt Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - prompt_info
  - specification
  - design
  - deliverable

properties:
  prompt_info:
    type: object
    required:
      - id
      - task_type
      - source_ref
      - date
      - iteration
      - coupled_docs
    properties:
      id:
        type: string
        pattern: "^prompt-[0-9a-f]{8}$"
      task_type:
        type: string
        enum:
          - code_generation
          - debug
          - refactor
          - optimization
      source_ref:
        type: string
      date:
        type: string
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
          - change_ref
          - change_iteration
        properties:
          change_ref:
            type: string
            pattern: "^change-[0-9a-f]{8}$"
          change_iteration:
            type: integer
            minimum: 1
  
  mcp_config:
    type: object
    required:
      - model
    properties:
      model:
        type: string
      temperature:
        type: number
        minimum: 0.0
        maximum: 1.0
      max_tokens:
        type: integer
      system_prompt:
        type: string
  
  behavioral_standards:
    type: object
    properties:
      source:
        type: string
        pattern: "^workspace/knowledge/.*\\.yaml$"
        description: "Path to behavioral standards YAML file"
      enforcement_level:
        type: string
        enum:
          - strict
          - advisory
          - disabled
        description: "Level of behavioral constraint enforcement"

  tactical_execution:
    type: object
    properties:
      mode:
        type: string
        enum:
          - ralph_loop
          - direct
      worker_model:
        type: string
      reviewer_model:
        type: string
      max_iterations:
        type: integer
        minimum: 1
        maximum: 100
      boundary_conditions:
        type: object
        properties:
          token_budget:
            type: integer
          time_limit_minutes:
            type: integer
  
  context:
    type: object
    properties:
      purpose:
        type: string
      integration:
        type: string
      constraints:
        type: array
        items:
          type: string
  
  specification:
    type: object
    required:
      - description
      - requirements
    properties:
      description:
        type: string
      requirements:
        type: object
        properties:
          functional:
            type: array
            items:
              type: string
          technical:
            type: object
            properties:
              language:
                type: string
              version:
                type: string
              standards:
                type: array
                items:
                  type: string
      performance:
        type: array
        items:
          type: object
          properties:
            target:
              type: string
            metric:
              type: string
  
  design:
    type: object
    required:
      - components
    properties:
      architecture:
        type: string
      components:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            type:
              type: string
            purpose:
              type: string
            interface:
              type: object
              properties:
                inputs:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      type:
                        type: string
                      description:
                        type: string
                outputs:
                  type: object
                  properties:
                    type:
                      type: string
                    description:
                      type: string
                raises:
                  type: array
                  items:
                    type: string
            logic:
              type: array
              items:
                type: string
      dependencies:
        type: object
        properties:
          internal:
            type: array
            items:
              type: string
          external:
            type: array
            items:
              type: string
  
  data_schema:
    type: object
    properties:
      entities:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            attributes:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  type:
                    type: string
                  constraints:
                    type: string
            validation:
              type: array
              items:
                type: string
  
  error_handling:
    type: object
    properties:
      strategy:
        type: string
      exceptions:
        type: array
        items:
          type: object
          properties:
            exception:
              type: string
            condition:
              type: string
            handling:
              type: string
      logging:
        type: object
        properties:
          level:
            type: string
          format:
            type: string
  
  testing:
    type: object
    properties:
      unit_tests:
        type: array
        items:
          type: object
          properties:
            scenario:
              type: string
            expected:
              type: string
      edge_cases:
        type: array
        items:
          type: string
      validation:
        type: array
        items:
          type: string
  
  output_format:
    type: object
    properties:
      structure:
        type: string
        enum:
          - code_only
          - code_with_comments
          - full_explanation
      integration_notes:
        type: string
        enum:
          - none
          - brief
          - detailed
      constraints:
        type: array
        items:
          type: string
  
  deliverable:
    type: object
    required:
      - files
    properties:
      format_requirements:
        type: array
        items:
          type: string
      files:
        type: array
        items:
          type: object
          properties:
            path:
              type: string
            content:
              type: string
      documentation:
        type: array
        items:
          type: string
  
  success_criteria:
    type: array
    items:
      type: string
  
  element_registry:
    type: object
    properties:
      source:
        type: string
        description: "Path to name registry master document"
      entries:
        type: object
        properties:
          modules:
            type: array
            items:
              type: object
              properties:
                name:
                  type: string
                path:
                  type: string
          classes:
            type: array
            items:
              type: object
              properties:
                name:
                  type: string
                module:
                  type: string
          functions:
            type: array
            items:
              type: object
              properties:
                name:
                  type: string
                module:
                  type: string
                signature:
                  type: string
          constants:
            type: array
            items:
              type: object
              properties:
                name:
                  type: string
                module:
                  type: string
                type:
                  type: string
  
  notes:
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
          - t04_prompt
```

---

## Version History

| Version | Date       | Description                          |
| ------- | ---------- | ------------------------------------ |
| 1.0     | 2025-12-12 | Split from governance.md into separate file for maintainability |
| 1.1     | 2025-12-12 | UUID pattern migration: Replaced NNNN sequence numbering with 8-character UUID format (^[0-9a-f]{8}$) in all fields |
| 1.2     | 2025-02-13 | Added behavioral_standards section for autonomous loop execution behavioral constraints |
| 1.3     | 2025-02-13 | Added tactical_execution section for Ralph Loop integration: mode selection, worker/reviewer model specification, iteration limits, boundary conditions |
| 1.4     | 2026-03-12 | Added element_registry field with source reference and scoped entries for canonical naming contract |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
