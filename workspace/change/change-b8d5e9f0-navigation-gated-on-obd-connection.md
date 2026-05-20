Created: 2026 May 20

```yaml
change_info:
  id: "change-b8d5e9f0"
  title: "Gate swipe navigation on OBD connection state"
  date: "2026-05-20"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b8d5e9f0"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b8d5e9f0"
  description: >
    Swipe navigation between DIGITAL and RADIAL modes is permitted
    regardless of OBD connection state. When disconnected, navigation
    should be blocked; only long-press to setup is permitted.

scope:
  summary: >
    Add OBD connection state check to _handle_swipe_left() and
    _handle_swipe_right(). Return TouchAction.NONE immediately when
    transport thread is not RUNNING. Long-press (settings) is unaffected.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  out_of_scope:
    - "NavigationGestureHandler — swipe blocking handled at DisplayManager callback level"
    - "Long-press / settings navigation — must remain unblocked"
    - "Any OBD transport or protocol changes"

rational:
  problem_statement: >
    Gesture callbacks _handle_swipe_left() and _handle_swipe_right() do not
    consult OBD connection state. DIGITAL/RADIAL displays with RPM=0 are
    accessible with no valid data source, giving a misleading UI state.
  proposed_solution: >
    At the start of each swipe handler, check
    thread_manager.get_thread_status('transport') == ThreadStatus.RUNNING.
    If not RUNNING, log at DEBUG level and return TouchAction.NONE.
  alternatives_considered:
    - option: "Block in NavigationGestureHandler"
      reason_rejected: "Handler has no direct access to connection state; DisplayManager callback is the correct gate"
  benefits:
    - "UI accurately reflects system state"
    - "Minimal change — two guard clauses only"
  risks:
    - risk: "transport thread status may transiently show non-RUNNING during reconnect"
      mitigation: "Acceptable — user cannot navigate during brief reconnect window"

technical_details:
  current_behavior: >
    _handle_swipe_left() and _handle_swipe_right() check only config.mode
    (DIGITAL/RADIAL) and unconditionally change mode on swipe.
  proposed_behavior: >
    Both handlers check transport thread status first. If not RUNNING,
    return TouchAction.NONE immediately. If RUNNING, existing logic proceeds.
  implementation_approach: >
    Add guard at top of _handle_swipe_left() and _handle_swipe_right():
      if self.thread_manager.get_thread_status('transport') != ThreadStatus.RUNNING:
          self.logger.debug("Swipe blocked: OBD not connected")
          return TouchAction.NONE
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "Add connection state guard to both swipe handlers"
      functions_affected:
        - "_handle_swipe_left"
        - "_handle_swipe_right"
      classes_affected:
        - "DisplayManager"

testing_requirements:
  test_approach: "Manual Pi test with and without ELM327 connected"
  test_cases:
    - scenario: "Swipe while OBD disconnected"
      expected_result: "No mode transition; DEBUG log 'Swipe blocked: OBD not connected'"
    - scenario: "Swipe while OBD connected"
      expected_result: "Mode transitions as normal"
    - scenario: "Long-press while OBD disconnected"
      expected_result: "Settings mode entered normally"
  validation_criteria:
    - "Swipe has no effect when transport thread is not RUNNING"
    - "Swipe works normally when transport thread is RUNNING"
    - "Long-press is unaffected in all states"

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
