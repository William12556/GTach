# Prompt: Connecting Indicator

Created: 2026 November 22

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-9accfbe0"
  task_type: "code_generation"
  source_ref: "change-9accfbe0"
  target_profile: "claude_code"
  date: "2026-11-22"
  iteration: 1
  coupled_docs:
    change_ref: "change-9accfbe0"
    change_iteration: 1

context:
  purpose: "Distinguish Connecting from Failed in the disconnected view and show the reconnect indicator around the status dot on the dimmed gauge."
  integration: "src/gtach/display/manager.py; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-9accfbe0-connecting-indicator.md"
    - "ai/workspace/change/change-9accfbe0-connecting-indicator.md (C1-C7 are the specification)"
    - "ai/workspace/design/design-b8c9d0e1-component_display_manager.md v2.2 (sections 5.3, 5.4, 5.7, 8.0)"
    - "src/gtach/comm/transport.py (last_failure_cause semantics)"
    - "tests/test_gauge_status_symbols.py (stubbing patterns to reuse)"
    - "CLAUDE.md"
  constraints:
    - "CRITICAL: _link_lost(), _engine_off(), _disconnected_view(), touch regions and _current_view_key() are unchanged."
    - "CRITICAL: _link_connecting() fails towards Failed: an absent callback or any exception returns False."
    - "CRITICAL: the details panel, including its reconnect indicator colours and geometry, is unchanged."
    - "CRITICAL: the live gauge, Engine off and simulation mode draw exactly as before."
    - "Existing drawing code is retained, not deleted."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on new or changed signatures. Google-style docstrings citing change-9accfbe0."

specification:
  description: "Apply C1-C7 of change-9accfbe0; update and add tests."
  requirements:
    functional:
      - "As change-9accfbe0 technical_details.implementation_approach."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access (_frame_connecting is written and read by the display thread only; the cause callback takes the transport lock)"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "One cause-callback call per frame"
      metric: "time"

design:
  architecture: "Unchanged. A second per-frame flag refines the disconnected view."
  components:
    - name: "C1-C7"
      type: "module"
      purpose: "Connecting sub-state and gauge reconnect indicator in DisplayManager."
      logic:
        - "C1-C7 exactly as change-9accfbe0, in that order."
  dependencies:
    internal:
      - "gtach.display.models.Palette"
      - "GTachApplication._disconnected_cause (via _link_cause_callback)"
    external:
      - "pygame"

error_handling:
  strategy: "The cause read fails towards Failed; drawing failures are logged and the frame continues."
  exceptions: []
  logging:
    level: "INFO on Connecting/Failed transitions; DEBUG with exc_info for a raising cause callback"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As change-9accfbe0 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Cause appears in the same frame as the first sample."
    - "Panel open during the Connecting to Failed transition."
  validation:
    - "SDL_VIDEODRIVER=dummy pytest tests/ passes."
    - "mypy src/ reports no new issues."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
    - "Existing tests that assume the information symbol in every disconnected frame are updated to set a failure cause; unrelated assertions are not weakened; each changed assertion is listed in the report."
    - "New test module tests/test_connecting_indicator.py, behaviour-named, with 9accfbe0 in its module docstring."
    - "Move this prompt to ai/workspace/prompt/closed/ when finished. Leave the issue and change active (status: change implemented, issue resolved) pending device test."
    - "Report ai/workspace/report/report-9accfbe0-connecting-indicator.md: per item what changed; deviations from the change document; test results."
  files:
    - path: "src/gtach/display/manager.py"
      content: "C1-C7"
    - path: "tests/test_connecting_indicator.py"
      content: "New tests"
    - path: "tests/test_gauge_status_symbols.py"
      content: "Assertions that assume the symbol in every disconnected frame"

success_criteria:
  - "Connecting (no cause): dimmed gauge, no symbol, yellow dot, indicator turning around the dot."
  - "Failed (cause, absent or raising callback): information symbol, red dot, indicator turning."
  - "A tap on the centre opens the panel in both sub-states; the panel is unchanged."
  - "Live gauge, Engine off and simulation mode unchanged."
  - "git diff touches only manager.py, the two test modules, this prompt's move, the issue and change status lines, and the report."
  - "pytest tests/ passes; mypy src/ reports no new issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "_link_connecting"
        module: "gtach.display.manager"
        signature: "(self) -> bool"
      - name: "_draw_reconnect_spinner"
        module: "gtach.display.manager"
        signature: "(self, dim: Optional[Tuple[int, int, int]] = None, bright: Optional[Tuple[int, int, int]] = None) -> None"
    constants: []

notes: "Executed by a Claude Code cloud session (Opus 5.5); pull request merged by William after planner review. Device check after merge."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-22 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
