Created: 2026 August 12

# Change: Remove the Duplicate Simulate Button and Add a Retry-Countdown Arc

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-4f1e82b7"
  title: "Register and draw a single Setup button on the DISCONNECTED screen, and add a retry-countdown arc driven by the display frame clock so the operator can see that GTach is alive and when the next connect attempt falls"
  date: "2026-08-12"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-4f1e82b7"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-4f1e82b7"
  description: >
    Resolves issue-4f1e82b7. The Simulate button duplicates OPTIONS
    page 0's simulation_mode control, and the screen carries nothing
    that changes over time.

scope:
  summary: >
    Display-only, in one file. Drop the Simulate spec from the
    DISCONNECTED button column so a single Setup button is registered
    and drawn. Add a retry-countdown arc driven by the display's own
    frame clock. Keep the existing single cause line.
  affected_components:
    - name: "DisplayManager._register_disconnected_regions"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._render_disconnected"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager._draw_retry_arc"
      file_path: "src/gtach/display/manager.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "A Bluetooth reset button. Wanted in the freed space, but it needs privileged host access and a recovery action not yet established to work on this hardware — `hciconfig hci0 down && up` was tried on target and left the controller unable to come back. Raised separately once the working command is known."
    - "Additional status lines. The single cause line at y=210 introduced by issue-5e7a03c4 is retained and extended with more messages as they arise; no second or third line is added."
    - "_on_simulation_mode itself, and OPTIONS page 0's simulation_mode registration. Both unchanged; that control is where Simulate continues to live."
    - "src/gtach/comm/. The retry interval is read through a callback, not by reaching into the transport."
    - "_button_column, which is the single owner of button geometry and is called with a shorter spec tuple rather than modified."
    - "The Setup button's callback, _enter_setup_from_disconnected."

rational:
  problem_statement: >
    The DISCONNECTED screen's Simulate button calls _on_simulation_mode
    (manager.py:1720). The identical callback is already registered as
    'simulation_mode' on OPTIONS page 0 (manager.py:1622), and
    debug.log shows it being used from there four times. The button is
    a duplicate occupying half the screen's control area.

    Nothing on the screen changes over time. During the 2026-08-12
    sessions it was visually identical whether GTach was retrying every
    5 s, blocked on a wedged Bluetooth controller, or — as in
    issue-2ac1c602 — a live process with every worker torn down. The
    distinction that matters most to an operator watching a static
    screen is the one the screen cannot make.
  proposed_solution: >
    EDIT U — one button. Call _button_column with a single spec,
    ("disconnected_setup", NAVIGATION, _enter_setup_from_disconnected),
    and return one rect. _button_column already accepts a variable-length
    Sequence and centres what it is given, so no geometry change is
    needed. Draw one button in _render_disconnected accordingly.

    EDIT V — retry-countdown arc. Draw an arc below the button,
    sweeping from full to empty once per retry interval, driven by the
    display's own frame clock via time.monotonic() rather than by any
    transport state.

    That last point is the design's whole value. An indicator fed from
    transport state would freeze whenever the transport thread blocks
    in connect(), which is precisely when the operator needs to know
    the application is alive. Driven by the frame clock it stops only
    if the display loop itself stops — which is the fault worth
    signalling.

    The interval comes from a _retry_interval_callback attribute,
    defaulting to None and wired in app.py alongside the existing
    _link_connected_callback and _link_cause_callback. When unset the
    arc falls back to a 5.0 s period, matching reconnect_indefinitely's
    default.

    EDIT W — the cause line is unchanged. It remains the single status
    line; further messages are added to it rather than beside it.
  alternatives_considered:
    - option: "A spinner rather than a countdown arc."
      reason_rejected: >
        Conveys liveness only. The arc conveys liveness and
        time-to-next-attempt in one element for the same rendering
        cost, and reuses arc drawing the gauge already depends on.
    - option: "Drive the arc from the transport's retry state."
      reason_rejected: >
        It would freeze whenever the transport thread blocks in
        connect(), which is exactly the moment the indicator exists
        for. An indicator that stops when the subject stops implies a
        fault that may not exist.
    - option: "Keep Simulate and shrink both buttons to make room."
      reason_rejected: >
        Retains a duplicate control at the cost of touch-target size,
        which issue-b02ed4ea established a floor for.
    - option: "Add the Bluetooth reset button in the freed slot now."
      reason_rejected: >
        Deferred, not rejected. The action it should perform is not yet
        established: the one reset tried on target left the controller
        unable to come back. Shipping a button around an unverified
        command risks one that reliably makes things worse.
    - option: "Add further status lines rather than extending the one."
      reason_rejected: >
        The operator asked for one line extended as needed. More lines
        in a 480x480 circular viewport crowd the button and the arc.
  benefits:
    - "The operator can see that GTach is alive when the screen is otherwise static."
    - "The next connect attempt is visible before it happens."
    - "A duplicate control is removed without losing the capability."
    - "The freed space is available for the Bluetooth reset button when its action is known."
  risks:
    - risk: "The arc costs frame time on a Pi Zero 2W already targeting 30 FPS."
      mitigation: >
        One arc per frame on a screen with no gauge, no sweep and no
        RPM readout — a strictly lighter frame than RADIAL, which
        sustains 30.0 FPS per the 2026-08-12 logs. Confirm the FPS line
        still reports 30.0 on this screen during verification.
    - risk: "The arc period drifts from the actual retry cadence."
      mitigation: >
        Accepted and immaterial. It indicates approximately when the
        next attempt falls; it is not a synchronised countdown, and
        claiming precision it cannot have would be worse. The
        docstring must say so.
    - risk: "Removing a button changes the remaining button's position if the column centres vertically."
      mitigation: >
        _button_column takes an explicit top of 240 and stacks
        downward, so the first button's position is unchanged. Confirm
        by asserting the returned rect equals the previous first rect.
    - risk: "An operator accustomed to Simulate on this screen cannot find it."
      mitigation: >
        It is one downward swipe away on OPTIONS page 0, where the logs
        show it already being used. No capability is lost.

technical_details:
  current_behavior: >
    Two buttons, Setup and Simulate, at width 240 from top 240. The
    screen is static: title, message, optional cause line, buttons.
  proposed_behavior: >
    One Setup button in the same position. Below it, an arc sweeping
    once per retry interval, animated from the display frame clock. The
    cause line is unchanged.
  implementation_approach: >
    Two edits and one new private helper, all in
    src/gtach/display/manager.py, plus callback wiring in app.py. No
    new dependencies; time is already imported.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        _register_disconnected_regions passes one spec and returns one
        rect. _render_disconnected draws one button and calls the new
        _draw_retry_arc. _draw_retry_arc computes phase from
        time.monotonic() modulo the retry interval and draws the arc.
        Add _retry_interval_callback, defaulting to None.
      functions_affected:
        - "_register_disconnected_regions"
        - "_render_disconnected"
        - "_draw_retry_arc"
      classes_affected:
        - "DisplayManager"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Wire _retry_interval_callback beside the existing
        _link_connected_callback and _link_cause_callback assignments.
      functions_affected:
        - "_start_normal_mode"
      classes_affected:
        - "GTachApplication"
  data_changes: []
  interface_changes:
    - interface: "DisplayManager._retry_interval_callback"
      change_type: "contract"
      details: "New optional attribute, defaulting to None. Returns the transport retry interval in seconds. The arc falls back to 5.0 s when unset."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "_button_column"
      impact: "Called with a one-element sequence. Not modified; it already accepts a variable-length Sequence."
    - component: "TouchEventCoordinator"
      impact: "One fewer region registered on this screen. No coordinator change."
  external: []
  required_changes:
    - change_ref: "change-7d4e91a3"
      relationship: "blocked_by. Made this screen's controls reachable at all."
    - change_ref: "change-5e7a03c4"
      relationship: "blocked_by. Introduced the cause line this change retains."

testing_requirements:
  test_approach: >
    Unit tests for region registration and arc phase, plus on-target
    confirmation that the arc animates while the transport is blocked.
  test_cases:
    - scenario: "_register_disconnected_regions is called."
      expected_result: "Exactly one region is registered, named disconnected_setup; no disconnected_simulate region exists."
    - scenario: "The returned Setup rect."
      expected_result: "Identical to the first rect returned before this change; the button has not moved."
    - scenario: "_draw_retry_arc with _retry_interval_callback unset."
      expected_result: "A 5.0 s period is used; no exception."
    - scenario: "_draw_retry_arc with the callback returning 5.0, sampled at t and t+2.5."
      expected_result: "The computed phase differs by approximately half a sweep."
    - scenario: "_draw_retry_arc with the callback returning 0 or a negative value."
      expected_result: "Falls back to 5.0 s rather than dividing by zero."
    - scenario: "_draw_retry_arc with the callback raising."
      expected_result: "Falls back to 5.0 s; no exception propagates; the screen still renders."
    - scenario: "Two _render_disconnected calls with no transport state change between them."
      expected_result: "The arc phase differs, the frame clock having advanced. The indicator does not depend on transport state."
    - scenario: "Rendering the DISCONNECTED screen with a cause set."
      expected_result: "The cause line is drawn at its existing position, unchanged by this change."
  regression_scope:
    - "Setup entry from the DISCONNECTED screen."
    - "Simulation mode entry from OPTIONS page 0."
    - "The downward swipe from DISCONNECTED to OPTIONS."
    - "The cause line introduced by change-5e7a03c4."
    - "Frame rate on the DISCONNECTED screen."
    - "tests/ suite in full."
  validation_criteria:
    - "No region named disconnected_simulate is registered anywhere."
    - "_on_simulation_mode remains reachable from OPTIONS page 0."
    - "The arc's phase derives from time.monotonic() and from no transport attribute."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDIT U — one spec in _register_disconnected_regions; one button drawn."
      owner: "tactical"
    - step: "EDIT V — _draw_retry_arc and its call from _render_disconnected."
      owner: "tactical"
    - step: "Wire _retry_interval_callback in app.py."
      owner: "tactical"
    - step: "Add unit tests per testing_requirements.test_cases items 1-8."
      owner: "tactical"
    - step: "Deploy to gtach.local; confirm the arc animates while a connect attempt is blocked, and that FPS holds at 30."
      owner: "human"
  rollback_procedure: "Revert the commit. Two files, both localised."
  deployment_notes: "Display-only. No service, packaging or configuration change."

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
    - change_ref: "change-7d4e91a3"
      relationship: "blocked_by."
    - change_ref: "change-5e7a03c4"
      relationship: "blocked_by."
    - change_ref: "change-9c2f41d8"
      relationship: "related. Its indefinite retry is what the arc counts down to."
  related_issues:
    - issue_ref: "issue-4f1e82b7"
      relationship: "resolves"
    - issue_ref: "issue-b02ed4ea"
      relationship: "related. Its touch-target floor is why shrinking two buttons was rejected in favour of removing one."
    - issue_ref: "issue-2ac1c602"
      relationship: >
        related. The live-but-inert process it concerned would have
        been visible on this screen had a frame-clock liveness
        indicator existed.

notes: >
  The single design point that must not be compromised: the arc is
  driven by the display frame clock, not by transport state. Fed from
  the transport it would freeze whenever the transport thread blocks —
  the exact moment the operator needs to know the application is alive.
  Stated in the issue, here, and as a success criterion in the prompt.

  The freed button slot is deliberately left empty. It is where the
  Bluetooth reset button will go once the recovery command that works
  on this hardware is established.

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-4f1e82b7 iteration 1."
      - "Removes the duplicate Simulate button; adds a frame-clock-driven retry-countdown arc; retains the single cause line."
      - "Records the rejection of a spinner, of transport-driven animation, of shrinking both buttons, and of additional status lines."
      - "Records that the Bluetooth reset button is deferred, not rejected, pending an established recovery command."

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
| 1.0 | 2026-08-12 | Initial change document. One Setup button on the DISCONNECTED screen, a frame-clock-driven retry-countdown arc, and the existing cause line retained. |

---

Copyright (c) 2026 William Watson. MIT License.
