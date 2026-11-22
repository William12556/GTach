# Change: Connecting Indicator

Created: 2026 November 22

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-9accfbe0"
  title: "Split the disconnected view into Connecting and Failed; turn the reconnect indicator around the status dot on the dimmed gauge"
  date: "2026-11-22"
  author: "William Watson"
  status: "implemented"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-9accfbe0"
    issue_iteration: 1
    prompt_ref: "prompt-9accfbe0"

source:
  type: "issue"
  reference: "issue-9accfbe0"
  description: "Implements design-b8c9d0e1 v2.2."

scope:
  summary: >
    manager.py evaluates a per-frame Connecting flag from the failure cause,
    draws the information symbol only when Failed, shows a yellow status dot
    while Connecting, and draws the existing reconnect indicator around the
    status dot on the dimmed gauge; tests updated and added.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_connecting_indicator.py (new); tests/test_gauge_status_symbols.py (assertions that assume the symbol in every disconnected frame)"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-b8c9d0e1-component_display_manager"
      sections:
        - "5.3, 5.4, 5.7, 8.0"
  out_of_scope:
    - "_link_lost(), _engine_off(), _disconnected_view() and their constants: unchanged."
    - "Touch regions and _current_view_key(): unchanged; the centre region is registered in both sub-states as now."
    - "The details panel content and layout, including its own reconnect indicator: unchanged."
    - "OBDTransport and the cause strings: unchanged."
    - "The status dot position and its overlap with the 4000 RPM numeral on 8000 RPM gauges (ai/task.md)."

rational:
  problem_statement: "See issue-9accfbe0."
  proposed_solution: "As technical_details.implementation_approach."
  alternatives_considered:
    - option: "Reconnect indicator around the information symbol in the centre disc"
      reason_rejected: "Inconsistent with the details panel, where the indicator turns around the status dot."
    - option: "Indicator only, no Connecting sub-state"
      reason_rejected: "Startup would still read as a failure."
  benefits:
    - "Startup and reconnects no longer read as failures."
    - "Visible activity while the transport blocks in connect()."
  risks:
    - risk: "A connected transport whose samples stop shows Connecting until the protocol drops the link."
      mitigation: "Accepted in design v2.2; the drop sets a cause within seconds."
    - risk: "Ring overlaps the 4000 RPM numeral on 8000 RPM gauges."
      mitigation: "Recorded in ai/task.md; abarth_595_turismo is clear."

technical_details:
  current_behavior: >
    In the disconnected view with the panel closed, _draw_radial_mode draws
    the information symbol and the status dot is red. The reconnect indicator
    is drawn only by _render_disconnected (panel).
  proposed_behavior: "design-b8c9d0e1 v2.2 sections 5.3, 5.4, 5.7."
  implementation_approach: >
    C1. Attribute _frame_connecting = False, initialised early in __init__
        beside _frame_engine_off.
    C2. New method _link_connecting() -> bool: returns True only when
        _link_cause_callback is set and returns a falsy value (None or
        empty string). An absent callback or an exception returns False
        (Failed); an exception is logged at DEBUG with exc_info.
    C3. Frame loop, directly after _set_frame_engine_off: set
        _frame_connecting = _disconnected_view() and _link_connecting().
        Log INFO once on each change of _frame_connecting while in the
        disconnected view ("Disconnected: connecting" / "Disconnected:
        connect failed").
    C4. _draw_radial_mode(): in the disconnected view draw
        _draw_info_symbol() only when not _frame_connecting. Everything
        else in the dimmed face is unchanged.
    C5. _draw_status_indicator(): when _frame_link_lost and
        _frame_connecting, status is CONNECTING (yellow); the other
        branches are unchanged.
    C6. _draw_reconnect_spinner(dim=None, bright=None): optional colour
        arguments; None keeps the current panel colours
        (_DISCONNECTED_BG_COLOUR, _DISCONNECTED_TEXT_COLOUR). Geometry and
        timing unchanged. The panel call is unchanged.
    C7. _render_normal_modes(): in the disconnected view with the panel
        closed, after _draw_status_indicator(), call
        _draw_reconnect_spinner(palette.track, palette.tick) using the
        palette read for the frame.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "C1-C7"
      functions_affected:
        - "__init__"
        - "_display_loop"
        - "_render_normal_modes"
        - "_draw_radial_mode"
        - "_draw_status_indicator"
        - "_draw_reconnect_spinner"
        - "_link_connecting (new)"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes:
    - interface: "_draw_reconnect_spinner"
      change_type: "signature"
      details: "Two optional keyword arguments; existing calls unchanged."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "GTachApplication._disconnected_cause / OBDTransport.last_failure_cause"
      impact: "Read only; semantics as in design-b1c2d3e4."
  external: []
  required_changes:
    - change_ref: "change-adb3afeb"
      relationship: "related"

testing_requirements:
  test_approach: "Unit tests with stubbed rendering and callbacks, as in tests/test_gauge_status_symbols.py; SDL_VIDEODRIVER=dummy."
  test_cases:
    - scenario: "Disconnected, cause callback returns None"
      expected_result: "_frame_connecting True; no information symbol; status CONNECTING; spinner drawn with palette.track and palette.tick; 'disconnected_info' registered."
    - scenario: "Disconnected, cause callback returns a string"
      expected_result: "_frame_connecting False; information symbol; status DISCONNECTED; spinner drawn."
    - scenario: "Cause callback absent or raises"
      expected_result: "Failed: information symbol, red."
    - scenario: "Cause callback returns an empty string"
      expected_result: "Connecting."
    - scenario: "Transition Connecting to Failed and back"
      expected_result: "One INFO line per transition."
    - scenario: "Panel open"
      expected_result: "_render_disconnected unchanged; its spinner uses the panel colours."
    - scenario: "Engine off, live gauge, simulation mode"
      expected_result: "_frame_connecting False; drawing unchanged; no gauge spinner."
  regression_scope:
    - "tests/"
  validation_criteria:
    - "pytest tests/ passes."
    - "mypy src/ reports no new issues."

implementation:
  effort_estimate: "Hours"
  implementation_steps:
    - step: "Claude Code cloud session executes prompt-9accfbe0 and opens a pull request."
      owner: "Claude Code"
    - step: "Planner code review; William merges in Safari."
      owner: "Planner / William"
    - step: "Remote Control session: pull, deploy, device test."
      owner: "William"
  rollback_procedure: "git revert of the merge commit."
  deployment_notes: "bin/deploy.sh from the Mac clone after merge."

verification:
  implemented_date: "2026-11-22"
  implemented_by: "Claude Code session, branch change-9accfbe0-connecting-indicator"
  verification_date: ""
  verified_by: ""
  test_results: "SDL_VIDEODRIVER=dummy pytest tests/: 865 passed (843 before, 22 added). mypy src/: no new errors (9 pre-existing, none in manager.py). black, isort and flake8 clean. Device test pending."
  issues_found: []

traceability:
  design_updates:
    - design_ref: "design-b8c9d0e1-component_display_manager"
      sections_updated:
        - "v2.2"
      update_date: "2026-11-22"
  related_changes:
    - change_ref: "change-adb3afeb"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-9accfbe0"
      relationship: "source"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-11-22"
    author: "William Watson"
    changes:
      - "Initial change."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-22 | Initial change |

---

Copyright (c) 2026 William Watson. MIT License.
