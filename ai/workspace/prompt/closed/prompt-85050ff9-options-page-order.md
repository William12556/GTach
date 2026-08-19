Created: 2026 August 19

# Prompt: Options Menu Page Order

---

## 1.0 Table of Contents

[2.0 Template](<#2.0 template>)
[Version History](<#version history>)

---

## 2.0 Template

```yaml
# T04 Prompt Template v1.11 - YAML Format

prompt_info:
  id: "prompt-85050ff9"
  task_type: "refactor"
  source_ref: "change-85050ff9"
  target_profile: "claude_code"
  date: "2026-08-19"
  iteration: 1
  coupled_docs:
    change_ref: "change-85050ff9"
    change_iteration: 1

context:
  purpose: >
    Swap which pair of controls appears on OPTIONS page 0 (the default,
    always-first page) versus page 1, so Clear settings and Check for
    updates are shown first and Simulation mode / Debug toggle are
    shown second.
  integration: >
    Confined to DisplayManager in src/gtach/display/manager.py. Does
    not touch the paging mechanism (OPTIONS_PAGE_COUNT, _page_options,
    change-8c5a1e73), touch-region IDs, callbacks, or button geometry —
    only which page each pair is registered/drawn under.
  knowledge_references: []
  constraints:
    - "Do not change touch-region IDs (simulation_mode, debug_toggle, clear_settings, check_updates)."
    - "Do not change button geometry, colours, or the confirm_clear sub-view."
    - "Do not change OPTIONS_PAGE_COUNT or the paging (swipe) logic."
    - "Preserve the guard that sets all four button attributes to None before assigning the current page's rects."

specification:
  description: >
    In src/gtach/display/manager.py, exchange the content assigned to
    page 0 and page 1 in two methods, and correct three docstrings that
    state the old assignment.
  requirements:
    functional:
      - "Page 0 (OPTIONS default entry page) registers and draws Clear settings and Check for updates."
      - "Page 1 registers and draws Simulation mode and Debug toggle."
      - "All existing callbacks, touch-region IDs, and button geometry are unchanged — only the page they belong to moves."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "No behavioural change beyond page content assignment"
        - "Docstrings updated to match new assignment"
  performance: []

design:
  architecture: "Direct edit of two conditional blocks (register + draw) and their governing docstrings; no structural change."
  components:
    - name: "_register_options_menu_regions"
      type: "function"
      purpose: "Compute and register the current options page's two button regions."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Sets self._options_btn_clear, self._options_btn_sim, self._options_btn_debug, self._options_btn_update as a side effect."
        raises: []
      logic:
        - "Keep the existing 'all four rects set to None first' guard unchanged."
        - "Under `if self._options_page == 0:`, assign the specs tuple currently used for page 1: (\"clear_settings\", TouchAction.SETTINGS_CHANGE, lambda pos: self._on_clear_settings_requested()) and (\"check_updates\", TouchAction.SETTINGS_CHANGE, lambda pos: self._on_check_updates())."
        - "Under `else:` (page 1), assign the specs tuple currently used for page 0: (\"simulation_mode\", TouchAction.SETTINGS_CHANGE, lambda pos: self._on_simulation_mode()) and (\"debug_toggle\", TouchAction.SETTINGS_CHANGE, lambda pos: self._on_debug_toggle())."
        - "Swap the rects-unpacking to match: under the page-0 branch, `self._options_btn_clear, self._options_btn_update = rects`; under the page-1 branch, `self._options_btn_sim, self._options_btn_debug = rects`."
        - "Update the method's docstring paging note from 'page 0 — simulation_mode, debug_toggle / page 1 — clear_settings, check_updates' to 'page 0 — clear_settings, check_updates / page 1 — simulation_mode, debug_toggle'."
        - "Leave the _button_column call (width=300, top=185) unchanged."
      dependencies:
        internal: []
        external: []
    - name: "_draw_options_menu"
      type: "function"
      purpose: "Draw the current options page's two buttons and the page indicator."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Renders to the back buffer as a side effect."
        raises: []
      logic:
        - "Under `if self._options_page == 0:`, assign page_items = ((self._options_btn_clear, \"Clear settings\"), (self._options_btn_update, \"Check for updates\"))."
        - "Under `else:`, assign page_items = ((self._options_btn_sim, sim_label), (self._options_btn_debug, debug_label))."
        - "Leave sim_label/debug_label computation, the button drawing loop, and the page indicator dots unchanged."
      dependencies:
        internal: []
        external: []
    - name: "_on_clear_settings_requested"
      type: "function"
      purpose: "Enter the clear-settings confirmation sub-view."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Sets self._options_view = 'confirm_clear'."
        raises: []
      logic:
        - "No functional change. Update the docstring sentence 'Bound by the options menu's page 1' to 'Bound by the options menu's page 0' to match the new assignment."
      dependencies:
        internal: []
        external: []
  dependencies:
    internal:
      - "DisplayManager.OPTIONS_PAGE_COUNT (unchanged)"
    external: []

data_schema:
  entities: []

error_handling:
  strategy: "No change to existing exception handling in either method."
  exceptions: []
  logging:
    level: ""
    format: ""

testing:
  unit_tests:
    - scenario: "OPTIONS entered; _options_page == 0."
      expected: "self._options_btn_clear and self._options_btn_update are set; self._options_btn_sim and self._options_btn_debug are None."
    - scenario: "Page advanced to 1 via swipe."
      expected: "self._options_btn_sim and self._options_btn_debug are set; self._options_btn_clear and self._options_btn_update are None."
  edge_cases:
    - "Touch on a button rect while the opposite page's rects are None must not raise (existing guard behaviour, unchanged)."
  validation:
    - "pytest suite passes with no new failures."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
  files:
    - path: "src/gtach/display/manager.py"
      content: "Modify _register_options_menu_regions, _draw_options_menu, and _on_clear_settings_requested per design.components above."

success_criteria:
  - "Page 0 registers and draws Clear settings / Check for updates; page 1 registers and draws Simulation mode / Debug toggle."
  - "No touch-region ID, callback, geometry, or paging-mechanism change."
  - "All three identified docstrings updated to state the new page assignment."
  - "Existing pytest suite passes."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants: []

tactical_brief: ""

notes: "target_profile is claude_code; tactical_brief intentionally left empty per T04 schema (required only for target_profile: ael)."
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial prompt document creation. |

---

Copyright (c) 2026 William Watson. MIT License.
