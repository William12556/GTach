Created: 2026 May 20

```yaml
change_info:
  id: "change-f3a7c2e1"
  title: "Implement blocking acknowledgement screen with explicit dismissal"
  date: "2026-05-20"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f3a7c2e1"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-f3a7c2e1"
  description: >
    Acknowledgement screen transitions immediately to RPM display without
    waiting for operator dismissal. ACKNOWLEDGEMENT mode is set but never
    rendered or handled in the display loop.

scope:
  summary: >
    Add a rendered acknowledgement screen to _render_normal_modes() that
    blocks all display transitions until the operator taps to dismiss.
    Transition to _post_splash_mode on dismissal.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  out_of_scope:
    - "Acknowledgement state persistence (ack_state.py) — unchanged"
    - "Splash screen timing — unchanged"
    - "Any other display modes"

rational:
  problem_statement: >
    DisplayMode.ACKNOWLEDGEMENT is set after splash completes but
    _render_normal_modes() has no branch for it. The screen is
    never rendered and no dismissal mechanism exists.
  proposed_solution: >
    Add _draw_acknowledgement_mode() method. Add ACKNOWLEDGEMENT branch
    in _render_normal_modes(). Register a tap handler that calls
    _on_acknowledgement_dismissed() which transitions to _post_splash_mode
    and records the acknowledgement via _ack_state_manager.
  alternatives_considered:
    - option: "Timeout-based auto-dismiss"
      reason_rejected: "Requirement specifies explicit dismissal only"
  benefits:
    - "Operator acknowledgement is enforced as intended"
    - "Acknowledgement state is correctly persisted"
  risks:
    - risk: "Touch handler registration may conflict with existing regions"
      mitigation: "Use touch_coordinator.clear_regions() at start of ack render"

technical_details:
  current_behavior: >
    _render_normal_modes() handles DIGITAL, RADIAL, SETTINGS only.
    ACKNOWLEDGEMENT mode falls through unrendered. No tap dismissal exists.
  proposed_behavior: >
    _render_normal_modes() routes ACKNOWLEDGEMENT to _draw_acknowledgement_mode().
    Screen displays a prompt and tap-to-continue instruction.
    On tap, transitions to _post_splash_mode and calls
    _ack_state_manager.save_acknowledgement().
  implementation_approach: >
    1. Add _draw_acknowledgement_mode() — renders simple prompt on black
       background with circular border. Registers a full-screen tap region
       via touch_coordinator.
    2. Add _on_acknowledgement_dismissed() — saves ack state, clears touch
       regions, sets config.mode = _post_splash_mode.
    3. Add ACKNOWLEDGEMENT branch in _render_normal_modes().
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "Add ack screen render method, dismissal handler, and branch in _render_normal_modes"
      functions_affected:
        - "_render_normal_modes"
        - "_draw_acknowledgement_mode (new)"
        - "_on_acknowledgement_dismissed (new)"
      classes_affected:
        - "DisplayManager"

testing_requirements:
  test_approach: "Manual Pi test: verify ack screen displays, blocks swipe, dismisses on tap"
  test_cases:
    - scenario: "Ack state not present — ack screen shown after splash"
      expected_result: "Screen renders and does not transition until tapped"
    - scenario: "Tap to dismiss"
      expected_result: "Transitions to _post_splash_mode; ack state saved"
    - scenario: "Ack state already present — skip ack screen"
      expected_result: "Transitions directly to _post_splash_mode (existing behaviour)"
  validation_criteria:
    - "No auto-transition from ACKNOWLEDGEMENT mode"
    - "Tap dismisses and persists ack state"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-05-20"
    author: "William Watson"
    changes:
      - "Initial change document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
