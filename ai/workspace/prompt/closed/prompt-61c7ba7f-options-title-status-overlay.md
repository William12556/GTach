Created: 2026 August 14

# T04 Prompt — Reposition OPTIONS Screen Title and Controls

---

## 1.0 Table of Contents

[2.0 Document](<#2.0 document>)
[Version History](<#version history>)

---

## 2.0 Document

```yaml
# T04 Prompt - YAML Format

prompt_info:
  id: "prompt-61c7ba7f"
  task_type: "refactor"
  source_ref: "change-61c7ba7f"
  target_profile: "claude_code"
  date: "2026-08-14"
  iteration: 1
  coupled_docs:
    change_ref: "change-61c7ba7f"
    change_iteration: 1

context:
  purpose: >
    Move the OPTIONS screen's title, button column, page indicator, and
    hint text down by a uniform 45 px so the title no longer overlaps
    the status indicator dot.
  integration: "Single-file change within DisplayManager's OPTIONS render path."
  knowledge_references: []
  constraints:
    - "Do not change the status indicator's position or size."
    - "Do not change any screen other than the OPTIONS menu (update view, confirm view, DISCONNECTED are out of scope)."
    - "Do not change button dimensions, colours, or the buttons drawn/labels."
    - "Preserve the existing circular-viewport corner-safety check in _button_column unchanged."

specification:
  description: >
    In src/gtach/display/manager.py, update four fixed y-coordinate
    literals in the OPTIONS menu render/registration path.
  requirements:
    functional:
      - "Title 'Options' renders centred at (240, 100), was (240, 55)."
      - "_register_options_menu_regions calls _button_column with top=185, was top=140."
      - "Page indicator dots render at y=395, was y=350."
      - "'Swipe up to return' hint renders at (240, 445), was (240, 400)."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "No new functions, parameters, or state"
        - "No change to any other literal, colour, or draw call"
  performance: []

design:
  architecture: "Direct literal edits; no structural change."
  components:
    - name: "_draw_options_menu"
      type: "function"
      purpose: "Renders the OPTIONS menu title, buttons, page indicator, and hint text."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Renders directly to the back buffer."
        raises: []
      logic:
        - "Change the title render call's position argument from (240, 55) to (240, 100)."
        - "Change the page indicator loop's fixed y from 350 to 395."
        - "Change the hint text render call's position argument from (240, 400) to (240, 445)."
    - name: "_register_options_menu_regions"
      type: "function"
      purpose: "Computes and registers the options menu's button touch regions."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Registers touch regions and stores button rects on self."
        raises: []
      logic:
        - "Change the _button_column call's top=140 argument to top=185."
  dependencies:
    internal: []
    external: []

data_schema:
  entities: []

error_handling:
  strategy: "No change to existing exception handling in either function."
  exceptions: []
  logging:
    level: "unchanged"
    format: "unchanged"

testing:
  unit_tests: []
  edge_cases:
    - "Both options pages (page 0: simulation_mode/debug_toggle; page 1: clear_settings/check_updates) must show buttons within the circular viewport at the new top=185."
  validation:
    - "Manual on-target verification per change-61c7ba7f testing_requirements."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "Modify existing file: update the four y-coordinate literals described above."

# Scope: all four edits are confined to _draw_options_menu and
# _register_options_menu_regions in src/gtach/display/manager.py.
# Executable occurrences only.
success_criteria:
  - "In src/gtach/display/manager.py, _draw_options_menu's 'Options' title render call uses position (240, 100)."
  - "In src/gtach/display/manager.py, _register_options_menu_regions's _button_column call for the options menu uses top=185."
  - "In src/gtach/display/manager.py, _draw_options_menu's page indicator loop uses y=395 for the dot centre."
  - "In src/gtach/display/manager.py, _draw_options_menu's 'Swipe up to return' hint render call uses position (240, 445)."
  - "grep -n '(240, 55)' src/gtach/display/manager.py returns no executable occurrence within _draw_options_menu."
  - "grep -n 'top=140' src/gtach/display/manager.py returns no occurrence within _register_options_menu_regions."
  - "No other literal, function signature, class, or draw call in src/gtach/display/manager.py is altered."

element_registry:
  source: ""
  entries:
    modules: []
    classes:
      - name: "DisplayManager"
        module: "src/gtach/display/manager.py"
    functions:
      - name: "_draw_options_menu"
        module: "src/gtach/display/manager.py"
        signature: "def _draw_options_menu(self) -> None"
      - name: "_register_options_menu_regions"
        module: "src/gtach/display/manager.py"
        signature: "def _register_options_menu_regions(self) -> None"
    constants: []

tactical_brief: ""

notes: "target_profile is claude_code; tactical_brief intentionally left empty per template guidance."
```

[Return to Table of Contents](<#1.0 table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial prompt creation |

---

Copyright (c) 2026 William Watson. MIT License.
