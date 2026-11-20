# Prompt: Gauge Status Symbols

Created: 2026 November 20

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-adb3afeb"
  task_type: "code_generation"
  source_ref: "change-adb3afeb"
  target_profile: "claude_code"
  date: "2026-11-20"
  iteration: 1
  coupled_docs:
    change_ref: "change-adb3afeb"
    change_iteration: 1

context:
  purpose: "Show Engine off and DISCONNECTED as symbols on the gauge, open the DISCONNECTED details as a panel on tap, and remove the OPTIONS title."
  integration: "src/gtach/display/models.py, src/gtach/display/manager.py; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-adb3afeb-gauge-status-symbols.md"
    - "ai/workspace/change/change-adb3afeb-gauge-status-symbols.md (EDIT A, EDIT B1-B10 are the specification)"
    - "ai/workspace/design/design-b8c9d0e1-component_display_manager.md v2.1 (sections 5.3, 5.4, 5.5, 5.7, 6.0, 8.0)"
    - "src/gtach/display/input/touch_coordinator.py (_find_hit_region: last registered region wins)"
    - "tests/test_engine_off_state.py, tests/test_disconnected_screen.py (stubbing patterns to reuse)"
    - "CLAUDE.md"
  constraints:
    - "CRITICAL: _link_lost(), _engine_off(), LINK_LOSS_TIMEOUT, LINK_RECOVERY_SAMPLES, ENGINE_OFF_FRESHNESS_S and the sample drain are unchanged."
    - "CRITICAL: _render_disconnected(), _register_disconnected_regions() and _draw_reconnect_spinner() are unchanged; the panel is the existing screen."
    - "CRITICAL: drawing code that stops being called is retained, not deleted (ENGINE_OFF_TEXT and its drawing block move to _draw_engine_off_text)."
    - "CRITICAL: the live gauge (link confirmed, not engine off) draws exactly as before."
    - "Touch regions are registered only in _register_view_regions, never in a render method; every state that decides which regions exist is in _current_view_key."
    - "No change to the acknowledgement screen, OPTIONS paging or buttons, setup screens, or swipe handlers."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on new methods. Google-style docstrings citing change-adb3afeb."

specification:
  description: "Apply EDIT A and EDIT B1-B10 of change-adb3afeb; update and add tests."
  requirements:
    functional:
      - "As change-adb3afeb technical_details.implementation_approach."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access (_disconnected_details_open is written by touch callbacks and the display thread, read by the display thread; a single bool assignment)"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No additional per-frame allocation beyond the symbol primitives"
      metric: "time"

design:
  architecture: "Unchanged. Derived conditions select what _draw_radial_mode draws and which regions _register_view_regions registers."
  components:
    - name: "EDIT A"
      type: "module"
      purpose: "Palette.symbol and Palette.alert with the day and night values in change-adb3afeb."
      logic:
        - "Add both fields after band_centres; set them in DAY_PALETTE and NIGHT_PALETTE."
    - name: "EDIT B"
      type: "module"
      purpose: "Symbols, dimmed gauge, details panel, OPTIONS title removal in DisplayManager."
      logic:
        - "B1-B10 exactly as change-adb3afeb, in that order."
        - "Geometry of both symbols as in change-adb3afeb B8, B9; both lie inside the centre disc r 99."
        - "Log INFO when the panel opens and when it closes (with the reason: tap, link recovered, engine off, mode change)."
  dependencies:
    internal:
      - "gtach.display.models.Palette"
      - "gtach.display.input.TouchEventCoordinator"
    external:
      - "pygame"

error_handling:
  strategy: "Drawing failures are logged and the frame continues, as in the existing draw methods. A failure in the symbol helpers must not prevent the rest of the gauge from drawing."
  exceptions: []
  logging:
    level: "INFO for panel open and close; ERROR with exc_info for draw failures"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As change-adb3afeb testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Tap on the info region in the same frame the link recovers."
    - "Engine off begins while the panel is open."
    - "_reset_callback is None: panel registers close and Setup only."
  validation:
    - "SDL_VIDEODRIVER=dummy pytest tests/ passes."
    - "mypy src/ reports no new issues."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
    - "Existing tests whose assertions encode the replaced behaviour (ENGINE_OFF_TEXT drawn; DISCONNECTED regions registered without a tap) are updated to the new behaviour; unrelated assertions are not weakened; each changed assertion is listed in the report."
    - "New test module tests/test_gauge_status_symbols.py, behaviour-named, with adb3afeb in its module docstring."
    - "Move this prompt to ai/workspace/prompt/closed/ when finished. Leave the issue and change active (status: change implemented, issue resolved) pending device test."
    - "Report ai/workspace/report/report-adb3afeb-gauge-status-symbols.md: per EDIT what changed; the observed behaviour of a swipe that starts on the open panel; deviations from the change document; test results."
  files:
    - path: "src/gtach/display/models.py"
      content: "EDIT A"
    - path: "src/gtach/display/manager.py"
      content: "EDIT B1-B10"
    - path: "tests/test_gauge_status_symbols.py"
      content: "New tests"
    - path: "tests/test_engine_off_state.py"
      content: "Assertions on replaced behaviour"
    - path: "tests/test_disconnected_screen.py"
      content: "Assertions on replaced behaviour"

success_criteria:
  - "Disconnected, panel closed: dimmed gauge, amber info symbol, red status dot, only 'disconnected_info' registered."
  - "Tap on the symbol opens the existing DISCONNECTED screen; Setup and Reset work; a tap outside them closes it."
  - "Link recovery, Engine off or entering OPTIONS closes the panel."
  - "Engine off: grey key symbol, no text, no regions."
  - "OPTIONS: no title; everything else unchanged."
  - "Live gauge unchanged."
  - "git diff touches only models.py, manager.py, the three test modules, this prompt's move, the issue and change status lines, and the report."
  - "pytest tests/ passes; mypy src/ reports no new issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes:
      - name: "Palette"
        module: "gtach.display.models"
    functions:
      - name: "_disconnected_view"
        module: "gtach.display.manager"
        signature: "(self) -> bool"
      - name: "_draw_info_symbol"
        module: "gtach.display.manager"
        signature: "(self, surface: pygame.Surface, palette: Palette) -> None"
      - name: "_draw_key_symbol"
        module: "gtach.display.manager"
        signature: "(self, surface: pygame.Surface, palette: Palette) -> None"
      - name: "_draw_engine_off_text"
        module: "gtach.display.manager"
        signature: "(self, center: Tuple[int, int]) -> None"
    constants:
      - name: "ICON_TOUCH_SIZE"
        module: "gtach.display.manager"
        type: "int (144)"

notes: "Executed by a Claude Code cloud session (Opus 5.5) on a claude/* branch; William opens and merges the pull request in the GitHub iOS app. Planner code review before merge. Device check after merge."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-20 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
