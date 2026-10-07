Created: 2026 October 07

# Prompt: Low-Severity Corrections

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-4005360c"
  task_type: "debug"
  source_ref: "change-4005360c"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-4005360c"
    change_iteration: 1

context:
  purpose: "Apply fourteen small corrections and one CLAUDE.md clarification."
  integration: "See change-4005360c; one new test module."
  knowledge_references:
    - "ai/workspace/issues/issue-4005360c-low-severity-defects.md"
    - "ai/workspace/change/change-4005360c-low-severity-defects.md"
    - "ai/workspace/audit/audit-36b6ea95-full-codebase.md (the cited findings)"
  constraints:
    - "Each edit is limited to its finding; do not refactor surrounding code and do not remove dead code (a later task does that)."
    - "C16: only values used for durations or comparisons switch to time.monotonic(); keep time.time() for displayed or logged timestamps and simulation seeds."
    - "No call-outs under a lock (CLAUDE.md rule 8)."
    - "Every logger .error/.critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply each item of change-4005360c proposed_solution and add tests/test_low_defects.py."
  requirements:
    functional:
      - "As in change-4005360c proposed_solution, per item."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance: []

design:
  architecture: "No structural change."
  components:
    - name: "Items A12 to D11 and rule 8"
      type: "module"
      purpose: "As in change-4005360c."
      logic:
        - "Work item by item; run the affected tests after each item."
        - "For C16, list in the report every time.time() site changed and every site deliberately kept."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged."
  exceptions: []
  logging:
    level: "DEBUG for per-touch and splash progress logs"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-4005360c testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases: []
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit in place; add one test module."
  files:
    - path: "src/gtach/ (modules per item)"
      content: "Items"
    - path: "CLAUDE.md"
      content: "Rule 8 clarification"
    - path: "tests/test_low_defects.py"
      content: "Tests"

success_criteria:
  - "grep -rn '\\bConnectionError\\b\\|\\bTimeoutError\\b' src/gtach/comm/transport.py shows only builtin uses, if any; no class definitions of those names."
  - "No bare `except:` in src/gtach/core/watchdog.py."
  - "get_rpm_large_font contains no set_bold on a cached font."
  - "device_surfaces.py contains no `.rssi`."
  - "CLAUDE.md rule 8 contains the file-lock clarification."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules: []
    classes:
      - name: "TransportConnectionError"
        module: "gtach.comm.transport"
      - name: "TransportTimeoutError"
        module: "gtach.comm.transport"
    functions: []
    constants: []

notes: "Human verification on the Pi: signal bars show on DEVICE_LIST; simbt discovery works after a Cancel."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-4005360c iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
