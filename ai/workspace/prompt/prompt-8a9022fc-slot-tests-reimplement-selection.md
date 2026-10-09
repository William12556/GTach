Created: 2026 October 09

# Prompt: Slot Tests Exercise Production Rendering

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-8a9022fc"
  task_type: "debug"
  source_ref: "change-8a9022fc"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-8a9022fc"
    change_iteration: 1

context:
  purpose: "Make the four slot-contents tests fail when the production slot rule changes."
  integration: "tests/test_device_list_focus.py only."
  knowledge_references:
    - "ai/workspace/issues/issue-8a9022fc-slot-tests-reimplement-selection.md"
    - "ai/workspace/change/change-8a9022fc-slot-tests-reimplement-selection.md"
  constraints:
    - "CRITICAL: no change under src/. The mutation check alters setup.py temporarily and must be reverted before commit."
    - "Do not change the other test classes or the two create_slot_surface tests in TestSlotContents."
    - "Python 3.9+; PEP 8."

specification:
  description: "Render through SetupDisplayManager._render_device_list_screen and assert what each slot received."
  requirements:
    functional:
      - "Four tests: 1 device focus 0 → [None, Device 0, None]; 2 devices focus 0 → [None, Device 0, Device 1]; 2 devices focus 1 → [Device 0, Device 1, None]; 5 devices focus 2 → [Device 1, Device 2, Device 3] (top, middle, bottom)."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Test docstrings"
  performance: []

design:
  architecture: "Recording spy around a real DeviceSurfaceRenderer."
  components:
    - name: "_Render"
      type: "class"
      purpose: "Add optional renderer parameter (default DeviceSurfaceRenderer()) assigned to host.device_renderer."
    - name: "_RecordingRenderer"
      type: "class"
      purpose: "Wraps a real DeviceSurfaceRenderer; create_slot_surface records (slot label from the layout item, device name or None) then delegates; other attributes delegate via __getattr__."
      logic:
        - "Read the create_slot_surface call in _render_device_list_screen to confirm argument order and the layout item's 'slot' key."
    - name: "TestSlotContents"
      type: "class"
      purpose: "Rewrite the four list tests to use _Render(count, focused_index, renderer=recorder); delete _slots."

data_schema:
  entities: []

error_handling:
  strategy: "Not applicable."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "The four rewritten tests."
      expected: "Pass against unmodified source."
    - scenario: "Mutation check: temporarily reverse the relative offsets in _render_device_list_screen; run the four tests; restore with git checkout src/gtach/display/setup.py."
      expected: "All four fail while altered; pass after restore. Record both runs in the report."
  edge_cases: []
  validation:
    - "git diff --stat shows only tests/test_device_list_focus.py for this change."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed path."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "tests/test_device_list_focus.py"
      content: "Recorder, _Render parameter, four rewritten tests"

success_criteria:
  - "grep -n '_slots' tests/test_device_list_focus.py returns nothing."
  - "Mutation check recorded: fail when altered, pass when restored."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "_render_device_list_screen"
        module: "gtach.display.setup.SetupDisplayManager"
        signature: "_render_device_list_screen(self, surface, state) -> None"
    constants: []

notes: "Human verification: none."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-8a9022fc iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
