Created: 2026 October 09

# Prompt: Remove Residual Dead Code

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-273ca048"
  task_type: "refactor"
  source_ref: "change-273ca048"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-273ca048"
    change_iteration: 1

context:
  purpose: "Remove the unreferenced items listed in issue-273ca048 v1.1 without changing reachable behaviour."
  integration: "src/gtach/display/ and tests/conftest.py."
  knowledge_references:
    - "ai/workspace/issues/issue-273ca048-residual-dead-code.md"
    - "ai/workspace/change/change-273ca048-residual-dead-code.md"
  constraints:
    - "CRITICAL: before removing any item, grep src/, tests/ and bin/ for its name, including string forms (getattr, __all__) and iteration over SetupScreen. Remove only items referenced solely by their definition or export; keep and report anything else."
    - "CRITICAL: no behaviour change in reachable code; edits to reachable code are limited to deleting references to removed items (for example the setup.py cache-list entry)."
    - "Remove nothing beyond D1-D8; list any further dead code found in the report."
    - "Do not change time.time() sites (change-e215a184) or add type hints (change-ac11505d)."
    - "Line numbers in the issue are from 34c1ffd; locate code by symbol."

specification:
  description: "Apply removal groups D1 to D8 of change-273ca048, running pytest after each group."
  requirements:
    functional:
      - "D1 touch.py: TouchHandler.get_touch_interface_info."
      - "D2 circular_positioning.py: get_circular_safe_area, clear_layout_cache, and _circular_layout_cache if then only assigned in __init__."
      - "D3 touch_interface.py: normalize_coordinates, denormalize_coordinates, HyperPixelTouchInterface.simulate_touch_event, MockHyperPixelTouch.simulate_touch, and the log line (~416) that advises using simulate_touch_event()."
      - "D4 typography.py: ButtonSize, ButtonState."
      - "D5 display/performance/__init__.py: initialize_performance_manager, cleanup_performance_manager and their __all__ entries."
      - "D6 splash.py: SplashScreen.get_performance_report, its unreachable trim branch, and any attribute used only by it."
      - "D7 tests/conftest.py: ACQUIRE_TIMEOUT."
      - "D8 setup_models.py: SetupScreen.DEVICE_MANAGEMENT, SetupScreen.CONFIRMATION; setup.py: SetupScreen.CONFIRMATION in the should_cache screen list."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Deletions only"
  performance: []

design:
  architecture: "Deletion only."
  components:
    - name: "D1 to D8"
      type: "module"
      purpose: "As in change-273ca048."
      logic:
        - "Order D7, D5, D4, D1, D3, D2, D6, D8."
        - "After each group: pytest -q; on failure restore the item and record the referencing site."
        - "Delete a test only if its sole subject was removed; list it in the report."

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
    - scenario: "As listed in change-273ca048 testing_requirements.test_cases, including the 8 s simtcp smoke run."
      expected: "As listed there."
  edge_cases: []
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Deletions and minimal edits only."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/display/"
      content: "D1 to D6, D8"
    - path: "tests/conftest.py"
      content: "D7"

success_criteria:
  - "grep -rn 'get_touch_interface_info\\|get_circular_safe_area\\|clear_layout_cache\\|normalize_coordinates\\|simulate_touch\\|ButtonSize\\|ButtonState\\|initialize_performance_manager\\|cleanup_performance_manager\\|get_performance_report\\|ACQUIRE_TIMEOUT\\|DEVICE_MANAGEMENT\\|CONFIRMATION' src tests bin returns nothing, except items kept and reported."
  - "python -c 'import gtach.app, gtach.main' succeeds; the 8 s simtcp smoke run shows no import or attribute error."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants: []

notes: "The report lists, per group, items removed, items kept with the referencing site, and tests deleted or adjusted. Human verification: normal use on the Pi."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-273ca048 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-09 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
