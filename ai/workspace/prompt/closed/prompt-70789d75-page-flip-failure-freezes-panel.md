Created: 2026 October 07

# Prompt: Write to the Displayed Half After a Pan Failure

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-70789d75"
  task_type: "debug"
  source_ref: "change-70789d75"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-70789d75"
    change_iteration: 1

context:
  purpose: >
    After a failed pan with the second framebuffer half displayed, keep
    frames reaching the displayed half instead of the hidden one.
  integration: "src/gtach/display/rendering/engine.py and tests/display/rendering/test_engine.py."
  knowledge_references:
    - "ai/workspace/issues/issue-70789d75-page-flip-failure-freezes-panel.md"
    - "ai/workspace/change/change-70789d75-page-flip-failure-freezes-panel.md"
  constraints:
    - "Change only the three locations named in EDITS A to C."
    - "Do not change vertical-offset compensation, vsync waiting, mmap setup or _setup_page_flip."
    - "Do not add retries of page flipping."
    - "Python 3.9+ compatible. PEP 8."

specification:
  description: "Apply EDITS A to C and add the tests."
  requirements:
    functional:
      - "After a pan failure the current and all later frames are written at buffer_index * fb_size."
      - "With page flipping never established, writes remain at offset 0."
      - "The one-time pan failure message is logged at WARNING."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Professional docstrings"
  performance: []

design:
  architecture: "The displayed half is always buffer_index."
  components:
    - name: "EDIT A — failure path in the page-flip branch"
      type: "function"
      purpose: "Do not lose the current frame."
      logic:
        - "In the `else:` that sets `self.page_flip = False`, after that assignment: `self.fb.seek(self.buffer_index * self.fb_size)` and `self.fb.write(payload)`, with a comment citing issue-70789d75."
    - name: "EDIT B — single-buffer branch"
      type: "function"
      purpose: "Write to the displayed half."
      logic:
        - "Replace `self.fb.seek(0)` with `self.fb.seek(self.buffer_index * self.fb_size)`; comment: buffer_index is 0 unless a pan succeeded, and still names the displayed half after a failed pan (issue-70789d75)."
    - name: "EDIT C — _pan_display"
      type: "function"
      purpose: "Persist the degradation."
      logic:
        - "In the except branch change `self.logger.info(` to `self.logger.warning(` for the 'Page flip failed, reverting to direct write' message. Keep the once-only guard."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged."
  exceptions: []
  logging:
    level: "WARNING for the one-time pan failure"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "Using the existing engine fixture pattern in test_engine.py: page_flip True, buffer_index 1, _pan_display patched to return False; present one frame; record fb writes with their offsets."
      expected: "page_flip False; buffer_index 1; a write of the payload at offset fb_size occurred after the failed pan."
    - scenario: "Present a second frame."
      expected: "The write is at offset fb_size."
    - scenario: "page_flip False, buffer_index 0; present a frame."
      expected: "The write is at offset 0."
  edge_cases: []
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit existing files in place."
  files:
    - path: "src/gtach/display/rendering/engine.py"
      content: "EDITS A, B and C"
    - path: "tests/display/rendering/test_engine.py"
      content: "Three new tests"

success_criteria:
  - "The single-buffer branch seeks to self.buffer_index * self.fb_size."
  - "The pan-failure path writes the payload to the displayed half."
  - "_pan_display logs the failure with logger.warning."
  - "No other line in engine.py changed."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "engine"
        path: "src/gtach/display/rendering/engine.py"
    classes:
      - name: "DisplayRenderingEngine"
        module: "gtach.display.rendering.engine"
    functions:
      - name: "_pan_display"
        module: "gtach.display.rendering.engine"
        signature: "(self, index: int) -> bool"
    constants: []

notes: "No on-target step is required; the failure cannot be induced on hardware without patching."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-70789d75 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-07 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
