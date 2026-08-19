Created: 2026 August 19

# Change: Options Menu Page Order

---

## 1.0 Table of Contents

[2.0 Template](<#2.0 template>)
[Version History](<#version history>)

---

## 2.0 Template

```yaml
# T02 Change Template v1.2 - YAML Format

change_info:
  id: "change-85050ff9"
  title: "Swap options menu page order: Clear settings/Check for updates first, Simulation/Debug second"
  date: "2026-08-19"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-85050ff9"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-85050ff9"
  description: "Reorder the two OPTIONS menu pages so the default (page 0) page holds Clear settings and Check for updates."

scope:
  summary: >
    Swap which control pair is registered and drawn on page 0 versus
    page 1 of the OPTIONS menu in DisplayManager. Update the three
    docstrings that state the current page assignment.
  affected_components:
    - name: "DisplayManager._register_options_menu_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_options_menu"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._on_clear_settings_requested"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "OPTIONS_PAGE_COUNT and the paging mechanism itself (change-8c5a1e73) — unchanged."
    - "Touch region IDs (simulation_mode, debug_toggle, clear_settings, check_updates) — unchanged, only the page they are registered under moves."
    - "Button geometry, colours, and the confirm_clear sub-view — unchanged."

rational:
  problem_statement: >
    The operator wants Clear settings and Check for updates to be the
    first page shown on OPTIONS entry, not Simulation mode and Debug
    toggle.
  proposed_solution: >
    Swap the two specs/page_items blocks between page 0 and page 1 in
    _register_options_menu_regions and _draw_options_menu, and correct
    the docstrings that name the current assignment.
  alternatives_considered:
    - option: "Change _options_page's default entry value instead of swapping content."
      reason_rejected: >
        Would leave the page-index-to-content mapping unchanged while
        making page 1 the entry page, which contradicts
        _handle_swipe_down's existing "OPTIONS always opens on page 0"
        invariant (change-8c5a1e73) and would require touching the
        same amount of code for no clarity gain.
  benefits:
    - "Matches operator's stated preference for default OPTIONS content."
  risks:
    - risk: "A docstring reference to the old page assignment is missed, leaving stale documentation."
      mitigation: "Change enumerates all three known docstring locations for the executor to update."

technical_details:
  current_behavior: >
    Page 0 registers/draws (simulation_mode, debug_toggle). Page 1
    registers/draws (clear_settings, check_updates). OPTIONS always
    opens on page 0 (change-8c5a1e73).
  proposed_behavior: >
    Page 0 registers/draws (clear_settings, check_updates). Page 1
    registers/draws (simulation_mode, debug_toggle). No other behaviour
    changes.
  implementation_approach: >
    In _register_options_menu_regions, swap the `specs` tuple assigned
    under `if self._options_page == 0` with the one under `else`, and
    swap the corresponding unpacking
    (`self._options_btn_sim, self._options_btn_debug = rects` /
    `self._options_btn_clear, self._options_btn_update = rects`)
    to match. In _draw_options_menu, swap the `page_items` tuple
    assigned under `if self._options_page == 0` with the one under
    `else`. Update the docstring in
    _register_options_menu_regions ("page 0 — simulation_mode,
    debug_toggle" / "page 1 — clear_settings, check_updates") and the
    docstring in _on_clear_settings_requested ("Bound by the options
    menu's page 1") to state the new page numbers.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "Swap page 0/page 1 content assignment for the OPTIONS menu; update three docstrings referencing the old assignment."
      functions_affected:
        - "_register_options_menu_regions"
        - "_draw_options_menu"
        - "_on_clear_settings_requested"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Manual on-device verification; no automated test currently covers OPTIONS page content."
  test_cases:
    - scenario: "Swipe down into OPTIONS."
      expected_result: "Clear settings and Check for updates buttons are drawn and registered on the first page shown."
    - scenario: "Swipe left or right once from the first OPTIONS page."
      expected_result: "Simulation mode and Debug toggle buttons are drawn and registered on the second page."
    - scenario: "Tap each button on each page."
      expected_result: "Each button's action matches its label (no touch-region/label mismatch)."
  regression_scope:
    - "confirm_clear sub-view still reachable from clear_settings on its new page."
    - "check_updates sub-view still reachable from its new page."
  validation_criteria:
    - "No change to touch region IDs, callbacks, or button geometry — only page assignment."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Swap specs tuples and rects unpacking in _register_options_menu_regions."
      owner: "Claude Code"
    - step: "Swap page_items tuples in _draw_options_menu."
      owner: "Claude Code"
    - step: "Correct page-number references in the three affected docstrings."
      owner: "Claude Code"
  rollback_procedure: "git revert the implementing commit."
  deployment_notes: "No config or migration impact; session-only page state."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-8c5a1e73"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-85050ff9"
      relationship: "source"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-08-19"
    author: "William Watson"
    changes:
      - "Initial change document creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.2"
  schema_type: "t02_change"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial change document creation. |

---

Copyright (c) 2026 William Watson. MIT License.
