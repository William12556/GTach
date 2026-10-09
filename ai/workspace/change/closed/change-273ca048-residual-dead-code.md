Created: 2026 October 09

# Change: Remove Residual Dead Code

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-273ca048"
  title: "Remove the unreferenced helpers, constants and SetupScreen members listed in issue-273ca048 v1.1"
  date: "2026-10-09"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-273ca048"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-273ca048"
  description: "Resolves issue-273ca048 (v1.1, including report-b64d2b77 findings B and C)."

scope:
  summary: "Deletion only, after a fresh reference check per item, plus the minimal edits needed for remaining code and tests to stay correct."
  affected_components:
    - name: "TouchHandler"
      file_path: "src/gtach/display/touch.py"
      change_type: "delete"
    - name: "CircularPositioningEngine"
      file_path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_type: "delete"
    - name: "touch_interface"
      file_path: "src/gtach/display/touch_interface.py"
      change_type: "delete"
    - name: "typography"
      file_path: "src/gtach/display/typography.py"
      change_type: "delete"
    - name: "display.performance package exports"
      file_path: "src/gtach/display/performance/__init__.py"
      change_type: "delete"
    - name: "SplashScreen"
      file_path: "src/gtach/display/splash.py"
      change_type: "delete"
    - name: "test configuration"
      file_path: "tests/conftest.py"
      change_type: "delete"
    - name: "SetupScreen"
      file_path: "src/gtach/display/setup_models.py"
      change_type: "delete"
    - name: "SetupDisplayManager render-cache screen list"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any behaviour change of reachable code."
    - "time.time() sites in circular_positioning.py (change-e215a184)."
    - "Typing (change-ac11505d) and formatting."
    - "Dead code not listed below; record any found in the report instead."

rational:
  problem_statement: "See issue-273ca048. change-cd5ec050 removed only listed items; these remained or became unreferenced."
  proposed_solution: >
    For each item, first grep src/, tests/ and bin/ for the name
    (including getattr strings, __all__ entries and iteration over the
    enum). Remove only items whose sole references are their definition
    or export; keep and report anything else.

    D1 touch.py: TouchHandler.get_touch_interface_info.
    D2 circular_positioning.py: get_circular_safe_area,
    clear_layout_cache, and the _circular_layout_cache attribute if it
    is then only assigned in __init__.
    D3 touch_interface.py: normalize_coordinates,
    denormalize_coordinates, HyperPixelTouchInterface.simulate_touch_event,
    MockHyperPixelTouch.simulate_touch, and the log line (~416) that
    advises using simulate_touch_event().
    D4 typography.py: ButtonSize, ButtonState.
    D5 display/performance/__init__.py: initialize_performance_manager,
    cleanup_performance_manager and their __all__ entries.
    D6 splash.py: SplashScreen.get_performance_report, including its
    unreachable trim branch, and any attribute used only by it.
    D7 tests/conftest.py: ACQUIRE_TIMEOUT.
    D8 setup_models.py: SetupScreen.DEVICE_MANAGEMENT and
    SetupScreen.CONFIRMATION; setup.py: the SetupScreen.CONFIRMATION
    entry in the should_cache screen list (~line 324). Both members are
    the last two in the Enum, so the auto() values of the remaining
    members do not change. The owner confirmed on 2026-10-09 that
    neither screen is reserved.
  alternatives_considered: []
  benefits:
    - "Less unreachable code to maintain and type-check."
  risks:
    - risk: "A reachable reference is missed (dynamic lookup, Enum iteration)."
      mitigation: "Per-item grep including string and iteration forms; full test suite; import smoke check; 8 s simtcp smoke run."

technical_details:
  current_behavior: "Unreferenced code present."
  proposed_behavior: "Unreferenced code removed."
  implementation_approach: "Deletion in the order D1 to D8, running pytest after each group."
  code_changes:
    - component: "display"
      file: "src/gtach/display/"
      change_summary: "D1 to D6, D8"
      functions_affected: []
      classes_affected: []
    - component: "tests"
      file: "tests/conftest.py"
      change_summary: "D7"
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "Removed unused public and private APIs"
      change_type: "signature"
      details: "Only names with no reachable reference."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-e215a184"
      relationship: "blocks. Both edit circular_positioning.py; implement this change first."
    - change_ref: "change-ac11505d"
      relationship: "blocks. Removing dead code first avoids typing it."

testing_requirements:
  test_approach: "Existing suite plus smoke checks."
  test_cases:
    - scenario: "pytest tests/."
      expected_result: "Passes."
    - scenario: "grep -rn for each removed name over src, tests and bin."
      expected_result: "No match (or the item is kept and reported)."
    - scenario: "python -c 'import gtach.app, gtach.main'."
      expected_result: "Succeeds."
    - scenario: "SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 python -m gtach --transport simtcp."
      expected_result: "Runs until the timeout without import or attribute errors."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "D1 to D8 with a grep before and pytest after each."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Human verification: none specific; normal use on the Pi."

verification:
  implemented_date: "2026-10-09"
  implemented_by: "Claude Code (commit bf03008)"
  verification_date: "2026-10-09"
  verified_by: "William Watson"
  test_results: "test-273ca048 passed (5/5); normal use on gtach.local."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-cd5ec050"
      relationship: "related. Previous dead-code removal."
    - change_ref: "change-4005360c"
      relationship: "related. Bounded the splash deque, making the trim branch unreachable."
  related_issues:
    - issue_ref: "issue-273ca048"
      relationship: "resolves"

notes: "Line numbers in the issue are from 34c1ffd; locate code by symbol."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-273ca048 iteration 1."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Implemented, verified by test-273ca048, closed."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial change document resolving issue-273ca048 iteration 1. |
| 1.1 | 2026-10-09 | Implemented, verified by test-273ca048, closed. |

---

Copyright (c) 2026 William Watson. MIT License.
