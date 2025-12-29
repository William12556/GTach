# T01 Design Template

Created: 2025-12-12

---

## Table of Contents

- [Template](#template)
- [Schema](#schema)
- [Version History](<#version history>)

---

## Template

```yaml
# T01 Design Template v1.0 - YAML Format
# Optimized for LM code generation context efficiency

project_info:
  name: ""
  version: ""
  date: ""
  author: ""

scope:
  purpose: ""
  in_scope:
    - ""
  out_scope:
    - ""
  terminology:
    - term: ""
      definition: ""

system_overview:
  description: ""
  context_flow: ""  # e.g., "ExternalSystem → Component → Output"
  primary_functions:
    - ""

design_constraints:
  technical:
    - ""
  implementation:
    language: ""
    framework: ""
    libraries:
      - ""
    standards:
      - ""
  performance_targets:
    - metric: ""
      value: ""

development_environment:
  platform: ""  # e.g., "macOS 14+", "Ubuntu 22.04"
  python_version: ""
  toolchain: []  # pytest, mypy, ruff, etc.

target_platform:
  type: ""  # embedded, server, desktop, cloud
  os: ""
  architecture: ""  # ARM64, x86_64, etc.
  constraints:
    - ""  # Memory, CPU, storage, network limitations

architecture:
  pattern: ""  # e.g., "layered", "pipeline", "microservices"
  component_relationships: ""  # e.g., "A → B → C"
  technology_stack:
    language: ""
    framework: ""
    libraries:
      - ""
    data_store: ""
  directory_structure:
    - ""

components:
  - name: ""
    purpose: ""
    responsibilities:
      - ""
    inputs:
      - field: ""
        type: ""
        description: ""
    outputs:
      - field: ""
        type: ""
        description: ""
    key_elements:
      - name: ""  # class/function name
        type: ""  # "class" or "function"
        purpose: ""
    dependencies:
      internal:
        - ""
      external:
        - ""
    processing_logic:
      - ""
    error_conditions:
      - condition: ""
        handling: ""

data_design:
  entities:
    - name: ""
      purpose: ""
      attributes:
        - name: ""
          type: ""
          constraints: ""
      relationships:
        - target: ""
          type: ""  # e.g., "one-to-many", "many-to-many"
  storage:
    - name: ""  # table/collection name
      fields:
        - name: ""
          type: ""
          constraints: ""
      indexes:
        - ""
  validation_rules:
    - ""

interfaces:
  internal:
    - name: ""
      purpose: ""
      signature: ""  # function/method signature with types
      parameters:
        - name: ""
          type: ""
          description: ""
      returns:
        type: ""
        description: ""
      raises:
        - exception: ""
          condition: ""
  external:
    - name: ""
      protocol: ""  # API, message queue, file, etc.
      data_format: ""  # JSON, XML, binary, etc.
      specification: ""  # endpoint, schema, etc.

error_handling:
  exception_hierarchy:
    base: ""
    specific:
      - ""
  strategy:
    validation_errors: ""
    runtime_errors: ""
    external_failures: ""
  logging:
    levels:
      - ""
    required_info:
      - ""
    format: ""

nonfunctional_requirements:
  performance:
    - metric: ""
      target: ""
  security:
    authentication: ""
    authorization: ""
    data_protection:
      - ""
  reliability:
    error_recovery: ""
    fault_tolerance:
      - ""
  maintainability:
    code_organization:
      - ""
    documentation:
      - ""
    testing:
      coverage_target: ""
      approaches:
        - ""

visual_documentation:
  diagrams_required: "Embed Mermaid diagrams within design document"
  diagram_types:
    system_architecture: "Overall structure showing modules and relationships"
    component_interaction: "Data flow between modules and interface contracts"
    state_machine: "State transitions and event handling logic"
    data_flow: "Information processing paths through system"
  mermaid_syntax: "All diagrams use Mermaid markdown code blocks"
  diagram_elements:
    - "Purpose statement explaining diagram"
    - "Legend explaining symbols and notation"
    - "Cross-references to related design sections"

version_history:
  - version: ""
    date: ""
    author: ""
    changes:
      - ""

metadata:
  copyright: "Copyright (c) 2025 William Watson. This work is licensed under the MIT License."
  template_version: "1.0"
  schema_type: "t01_design"
```

---

## Schema

```yaml
# T01 Design Schema v1.0
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - project_info
  - scope
  - system_overview
  - architecture
  - components

properties:
  project_info:
    type: object
    required:
      - name
      - version
      - date
    properties:
      name:
        type: string
      version:
        type: string
      date:
        type: string
      author:
        type: string
  
  scope:
    type: object
    required:
      - purpose
    properties:
      purpose:
        type: string
      in_scope:
        type: array
        items:
          type: string
      out_scope:
        type: array
        items:
          type: string
      terminology:
        type: array
        items:
          type: object
          properties:
            term:
              type: string
            definition:
              type: string
  
  system_overview:
    type: object
    required:
      - description
    properties:
      description:
        type: string
      context_flow:
        type: string
      primary_functions:
        type: array
        items:
          type: string
  
  design_constraints:
    type: object
    properties:
      technical:
        type: array
        items:
          type: string
      implementation:
        type: object
        properties:
          language:
            type: string
          framework:
            type: string
          libraries:
            type: array
            items:
              type: string
          standards:
            type: array
            items:
              type: string
      performance_targets:
        type: array
        items:
          type: object
          properties:
            metric:
              type: string
            value:
              type: string
  
  development_environment:
    type: object
    properties:
      platform:
        type: string
      python_version:
        type: string
      toolchain:
        type: array
        items:
          type: string
  
  target_platform:
    type: object
    properties:
      type:
        type: string
        enum:
          - embedded
          - server
          - desktop
          - cloud
      os:
        type: string
      architecture:
        type: string
      constraints:
        type: array
        items:
          type: string
  
  architecture:
    type: object
    required:
      - pattern
      - technology_stack
    properties:
      pattern:
        type: string
      component_relationships:
        type: string
      technology_stack:
        type: object
        properties:
          language:
            type: string
          framework:
            type: string
          libraries:
            type: array
            items:
              type: string
          data_store:
            type: string
      directory_structure:
        type: array
        items:
          type: string
  
  components:
    type: array
    items:
      type: object
      required:
        - name
        - purpose
      properties:
        name:
          type: string
        purpose:
          type: string
        responsibilities:
          type: array
          items:
            type: string
        inputs:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              type:
                type: string
              description:
                type: string
        outputs:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              type:
                type: string
              description:
                type: string
        key_elements:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              type:
                type: string
                enum:
                  - class
                  - function
              purpose:
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
        processing_logic:
          type: array
          items:
            type: string
        error_conditions:
          type: array
          items:
            type: object
            properties:
              condition:
                type: string
              handling:
                type: string
  
  data_design:
    type: object
    properties:
      entities:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            purpose:
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
            relationships:
              type: array
              items:
                type: object
                properties:
                  target:
                    type: string
                  type:
                    type: string
      storage:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            fields:
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
            indexes:
              type: array
              items:
                type: string
      validation_rules:
        type: array
        items:
          type: string
  
  interfaces:
    type: object
    properties:
      internal:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            purpose:
              type: string
            signature:
              type: string
            parameters:
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
            returns:
              type: object
              properties:
                type:
                  type: string
                description:
                  type: string
            raises:
              type: array
              items:
                type: object
                properties:
                  exception:
                    type: string
                  condition:
                    type: string
      external:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            protocol:
              type: string
            data_format:
              type: string
            specification:
              type: string
  
  error_handling:
    type: object
    properties:
      exception_hierarchy:
        type: object
        properties:
          base:
            type: string
          specific:
            type: array
            items:
              type: string
      strategy:
        type: object
        properties:
          validation_errors:
            type: string
          runtime_errors:
            type: string
          external_failures:
            type: string
      logging:
        type: object
        properties:
          levels:
            type: array
            items:
              type: string
          required_info:
            type: array
            items:
              type: string
          format:
            type: string
  
  nonfunctional_requirements:
    type: object
    properties:
      performance:
        type: array
        items:
          type: object
          properties:
            metric:
              type: string
            target:
              type: string
      security:
        type: object
        properties:
          authentication:
            type: string
          authorization:
            type: string
          data_protection:
            type: array
            items:
              type: string
      reliability:
        type: object
        properties:
          error_recovery:
            type: string
          fault_tolerance:
            type: array
            items:
              type: string
      maintainability:
        type: object
        properties:
          code_organization:
            type: array
            items:
              type: string
          documentation:
            type: array
            items:
              type: string
          testing:
            type: object
            properties:
              coverage_target:
                type: string
              approaches:
                type: array
                items:
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
          - t01_design
```


---

## Version History

| Version | Date       | Description                          |
| ------- | ---------- | ------------------------------------ |
| 1.0     | 2025-12-12 | Split from governance.md into separate file for maintainability |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
