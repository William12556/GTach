Created: 2026 June 12

```yaml
change_info:
  id: "change-9bae6cdd"
  title: "Add OPTIONS-screen debug logging toggle"
  date: "2026-06-12"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-9bae6cdd"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-9bae6cdd"
  description: >
    Expose toggle_debug_logging() through a third OPTIONS-screen button with a
    state-reflecting label.

scope:
  summary: >
    Add a _debug_toggle_callback to DisplayManager (mirroring _setup_entry_callback)
    and a _debug_logging_on state flag. Add a third OPTIONS button that toggles
    debug logging and reflects state in its label. Wire the callback and initial
    state in app.py at both DisplayManager creation sites.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master"
      sections:
        - "Options screen"
        - "Logging"
  out_of_scope:
    - "Persisting debug state across reboots — resets to launch value each boot."
    - "Changes to toggle_debug_logging() itself (delivered in bd8f95b7)."
    - "Changes to other OPTIONS buttons or the long-press navigation."

rational:
  problem_statement: >
    The runtime debug toggle has no UI. DisplayManager cannot reach the application.
  proposed_solution: >
    Reuse the established callback pattern. app.py assigns
    self._display._debug_toggle_callback = self.toggle_debug_logging and
    self._display._debug_logging_on = self._debug (the launch flag). The OPTIONS
    handler flips the flag, calls the callback, and the label re-renders.
  alternatives_considered:
    - option: "Pass the GTachApplication instance into DisplayManager."
      reason_rejected: "Tighter coupling than the existing callback pattern; inconsistent with _setup_entry_callback."
  benefits:
    - "Runtime debug control on an unattended device."
    - "Consistent with existing callback architecture."
  risks:
    - risk: "Callback unset (e.g. DisplayManager used standalone)."
      mitigation: "Handler guards on callback presence; flag still toggles label, logging unchanged."
    - risk: "Three buttons crowd the circular display."
      mitigation: "Geometry tightened: three 75px buttons at y=120/210/300 within the safe radius."

technical_details:
  current_behavior: >
    OPTIONS screen draws two buttons (Clear settings y=150, Bluetooth/Simulation
    y=270), each 300x80, registered via register_button_region with _on_* callbacks.
    DisplayManager has no debug awareness.
  proposed_behavior: >
    DisplayManager.__init__ initialises self._debug_toggle_callback = None and
    self._debug_logging_on = False. _draw_options_mode draws three buttons at
    y=120, y=210, y=300 (300x75): Clear settings, Bluetooth/Simulation, and Debug.
    The debug button label is 'Debug: On' or 'Debug: Off' per _debug_logging_on.
    A new _on_debug_toggle() flips _debug_logging_on, calls _debug_toggle_callback
    if set, and logs. app.py sets the callback and initial flag at both
    DisplayManager creation sites (normal mode and setup mode).
  implementation_approach: "Callback wiring plus one new button and handler; geometry retuned."
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        __init__: add _debug_toggle_callback = None and _debug_logging_on = False.
        _draw_options_mode: retune to three buttons (y=120/210/300, height 75);
        add Debug button with state label; register 'debug_toggle' region.
        Add _on_debug_toggle().
      functions_affected:
        - "__init__"
        - "_draw_options_mode"
        - "_on_debug_toggle"
      classes_affected:
        - "DisplayManager"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        __init__: store self._debug = debug (the flag is received but not
        currently stored). At both sites where self._display._setup_entry_callback
        is set, also set self._display._debug_toggle_callback =
        self.toggle_debug_logging and self._display._debug_logging_on = self._debug.
      functions_affected:
        - "__init__"
        - "_start_setup_mode"
        - "_start_normal_mode"
      classes_affected:
        - "GTachApplication"
  data_changes: []
  interface_changes:
    - interface: "DisplayManager._debug_toggle_callback"
      change_type: "contract"
      details: "Callable[[bool], None] set by app.py; receives the new debug state."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "GTachApplication.toggle_debug_logging"
      impact: "Invoked by the new callback; delivered in bd8f95b7."
  external: []
  required_changes:
    - change_ref: "change-bd8f95b7"
      relationship: "blocked_by"

testing_requirements:
  test_approach: "On-Pi verification after wheel deployment."
  test_cases:
    - scenario: "Enter OPTIONS without --debug."
      expected_result: "Three buttons shown; Debug button reads 'Debug: Off'."
    - scenario: "Tap Debug button."
      expected_result: "Label changes to 'Debug: On'; debug.log begins receiving records."
    - scenario: "Tap Debug button again."
      expected_result: "Label changes to 'Debug: Off'; debug.log stops receiving records."
    - scenario: "Launch with --debug, enter OPTIONS."
      expected_result: "Debug button reads 'Debug: On' initially."
    - scenario: "Long press in OPTIONS."
      expected_result: "Returns to display mode as before; navigation unaffected."
  regression_scope:
    - "Clear settings button."
    - "Bluetooth/Simulation mode button."
    - "OPTIONS long-press return."
  validation_criteria:
    - "All three buttons render within the circular viewport."
    - "Debug label reflects current state."
    - "Toggling controls debug.log writing."
    - "Existing two buttons function unchanged."

implementation:
  implementation_steps:
    - step: "Add callback/state fields to DisplayManager.__init__."
      owner: "Claude Code"
    - step: "Retune _draw_options_mode to three buttons; add Debug button and region."
      owner: "Claude Code"
    - step: "Add _on_debug_toggle()."
      owner: "Claude Code"
    - step: "Wire callback and initial flag at both app.py DisplayManager sites."
      owner: "Claude Code"
  rollback_procedure: "Revert manager.py and app.py via git."
  deployment_notes: "Build wheel and deploy to Pi per standard workflow."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  related_changes:
    - change_ref: "change-bd8f95b7"
      relationship: "depends_on"
  related_issues:
    - issue_ref: "issue-9bae6cdd"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-06-12"
    author: "William Watson"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
