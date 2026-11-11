# Prompt: Gauge Display and Touch Corrections

Created: 2026 November 11

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-2550e4ee"
  task_type: "debug"
  source_ref: "change-2550e4ee"
  target_profile: "claude_code"
  date: "2026-11-11"
  iteration: 1
  coupled_docs:
    change_ref: "change-2550e4ee"
    change_iteration: 1

context:
  purpose: "Run 5 of proposal-71ab3751: gauge display and touch findings of audit-71ab3751 and two ai/task.md rows."
  integration: "src/gtach/display/manager.py, touch.py, models.py, splash.py; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-2550e4ee-gauge-display-touch.md"
    - "ai/workspace/change/change-2550e4ee-gauge-display-touch.md"
    - "ai/workspace/proposal/proposal-71ab3751-audit-remediation-and-simplification.md section 6.0 (decisions D6, D8)"
    - "CLAUDE.md section 4"
  constraints:
    - "CRITICAL: edit no source file outside display/manager.py, display/touch.py, display/input/*, display/models.py and display/splash.py."
    - "CRITICAL: _link_lost keeps its property that every failure path returns True, and its latch and transition logging (issue-4d9e2f18)."
    - "CRITICAL: setup mode keeps routing every release directly to the short-press path; EDIT B applies outside setup mode only."
    - "Do not split or reorganise display/manager.py (decision D8). Do not change gauge geometry, colours or the 9000 RPM cap."
    - "'display' is a watchdog-critical thread: no blocking call is added to the render or touch path."
    - "No call-outs under a lock (CLAUDE.md section 4 rule 8)."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Monotonic clock for touch timing, consistent with the timestamps the handler already receives."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to E and the COMMENT RULE of change-2550e4ee; add tests/test_gauge_display_touch.py."
  requirements:
    functional:
      - "As in change-2550e4ee proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance:
    - target: "_link_lost evaluated once per frame"
      metric: "resources"

design:
  architecture: "Unchanged."
  components:
    - name: "EDITS A to E"
      type: "module"
      purpose: "As in change-2550e4ee."
      logic:
        - "EDIT A(1): find every first assignment of the six attributes by name; move the default assignments ahead of the try blocks in __init__ or at the top of _initialize_legacy_components, whichever runs before any reader thread starts."
        - "EDIT A(2): pattern 'manager = self._setup_manager; if self._in_setup_mode and manager: manager.render(...)'."
        - "EDIT B(1): reuse the swipe-threshold lookup the short-press path already performs; do not introduce a second threshold. Determine 'starts on a registered button region' with the coordinator's existing hit test, without invoking the action twice."
        - "EDIT B(2): one class constant _TOUCH_START_MAX_AGE_S = 10.0."
        - "EDIT C(1): store the per-frame value on the instance at the start of the frame; code outside the frame (for example touch handling) keeps calling _link_lost() directly."
        - "EDIT C(3): log the warning where the configuration is loaded, not in the render path."
        - "EDIT D: RPMBands must be defined before DisplayConfig for default_factory; keep an explicit rpm_bands argument working."
        - "EDIT E: the coordinator lock is an RLock; only a different thread can show that it is held."

data_schema:
  entities: []

error_handling:
  strategy: "Initialisation faults degrade to an inactive component and are logged once; render and touch paths do not raise."
  exceptions: []
  logging:
    level: "Unchanged, plus the WARNING records named in the change"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-2550e4ee testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Release exactly at the swipe threshold: swipe."
    - "Release with duration exactly touch_long_press and no movement: long press."
    - "performance_monitor None in the display loop and in the status report."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place; one new test module; one commit."
    - "Report: per EDIT, what changed; any deviation from the change document; test results."
  files:
    - path: "src/gtach/display/manager.py"
      content: "EDITS A, C"
    - path: "src/gtach/display/touch.py"
      content: "EDIT B"
    - path: "src/gtach/display/models.py, src/gtach/display/splash.py"
      content: "EDIT D"
    - path: "tests/test_gauge_display_touch.py, tests/test_callbacks_outside_locks.py"
      content: "Tests, EDIT E"

success_criteria:
  - "DisplayManager constructs and renders when the touch interface or the performance monitor fails to initialise."
  - "No reader of _setup_manager tests and uses the attribute in two reads."
  - "A release with movement at or above the swipe threshold is never a long press; a hold on a button presses it."
  - "A touch start older than 10 s is not used."
  - "One _link_lost evaluation per frame."
  - "The cause line uses FONT_SMALL_TEXT."
  - "Docstrings of _gauge_max_rpm and _toggle_palette match behaviour."
  - "_on_clear_settings removes all stored devices and checks the results."
  - "No type: ignore remains at DisplayConfig.rpm_bands."
  - "The splash performs each text-fit check once."
  - "test_callback_may_register_regions fails when callbacks run under the lock."
  - "git diff touches only the files named in the constraints and tests/."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants:
      - name: "_TOUCH_START_MAX_AGE_S"
        module: "gtach.display.touch"
        value: "10.0"

notes: "Model: Claude Opus 5.5, effort medium, no ultracode. Human verification: device session B, then the in-car test."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial prompt implementing change-2550e4ee iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
