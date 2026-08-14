Created: 2026 August 12

# Issue: The DISCONNECTED Screen Carries a Duplicate Control and No Sign of Life

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-4f1e82b7"
  title: "The DISCONNECTED screen's Simulate button duplicates a control already on OPTIONS page 0, occupying space wanted for diagnostics, and the screen gives the operator no indication that GTach is still running and still retrying"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "human_request"
  test_ref: ""
  description: >
    Raised 2026-08-12 by William during extended on-target diagnosis of
    connection failures. Long periods spent watching the DISCONNECTED
    screen while GTach retried in the background made two shortcomings
    apparent: the screen cannot say whether the application is alive
    and working, and half its control area is spent on a duplicate.

affected_scope:
  components:
    - name: "DisplayManager._register_disconnected_regions"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._render_disconnected"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: "GTach running with no OBD connection available."
  steps:
    - "Observe the DISCONNECTED screen."
    - "Note the two buttons: Setup and Simulate."
    - "Note that nothing on the screen changes over time, whether GTach is retrying, wedged, or dead."
  frequency: "always"
  reproducibility_conditions: "Static screen content; deterministic."
  test_data: >
    Current layout, from _render_disconnected (manager.py:2269-2325)
    and _register_disconnected_regions (manager.py:1706-1724):

      y=155  "Disconnected", font 36
      y=180  "OBD connection not available", font 20
      y=210  cause line, font 18, drawn only when a cause is known
             (issue-5e7a03c4)
      y=240  button column top; two buttons, width 240,
             height >= 72, separation >= 16

    The Simulate button's callback is _on_simulation_mode
    (manager.py:1720). The identical callback is already registered as
    'simulation_mode' on OPTIONS page 0 (manager.py:1622). Confirmed in
    use from that screen in debug.log: "Button simulation_mode pressed"
    followed by "Simulation mode on/off", four occurrences.

    Removing the second button frees the lower button slot and its
    separation — approximately 88 px in the 240-400 band.
  error_output: "None. This is a design shortcoming, not a fault."

behavior:
  expected: >
    The screen should tell the operator what is wrong, that the
    application is alive, and when the next attempt will be made. Its
    control area should not be spent on a control available elsewhere.
  actual: >
    Simulate duplicates OPTIONS page 0's simulation_mode control
    exactly, calling the same _on_simulation_mode method. Nothing on
    the screen changes over time. During the 2026-08-12 sessions the
    screen was visually identical whether GTach was retrying every 5 s,
    blocked on a wedged controller, or would have been dead — the
    condition issue-2ac1c602 concerned, where the process survived with
    every worker torn down.
  impact: >
    Diagnostic and operational. The operator cannot distinguish a
    working application waiting on an absent adapter from a hung one,
    which is the distinction that matters most when the screen has gone
    static. Space that could carry that information is spent on a
    duplicate control.

    Severity medium: no function is lost and a workaround exists in
    reading the logs, which is not available to a driver.
  workaround: "Read debug.log over SSH."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    The DISCONNECTED screen was designed as an error state to be
    escaped, not as a state to be waited in. Its two affordances are
    both exits. Now that the transport retries indefinitely
    (change-9c2f41d8) and can be blocked by conditions outside GTach's
    control (issue-5e7a03c4), it is a screen operators spend real time
    looking at, and it carries nothing that changes.
  technical_notes: >
    The retry interval is the transport's own retry_delay, 5.0 s by
    default and already passed to reconnect_indefinitely. An arc that
    sweeps once per interval conveys liveness and time-to-next-attempt
    in one element, and reuses the arc rendering the gauge already
    depends on. A spinner would convey only the first.

    The indicator must be driven from the display's own frame clock,
    not from transport state, or it will freeze whenever the transport
    thread blocks in connect() — which is exactly when the operator
    most needs to know the application is alive. This is the central
    design constraint: an indicator that stops when the thing it is
    reporting on stops is worse than none, because it implies a fault
    that may not exist.

    Simulate's removal costs nothing. The same callback is registered
    on OPTIONS page 0 and is reachable from DISCONNECTED by the
    existing downward swipe.
  related_issues:
    - issue_ref: "issue-7d4e91a3"
      relationship: >
        related. Made this screen's controls live at all. Its removal
        of the Simulate affordance here does not affect the Setup
        button, which is the screen's remaining and now sole exit.
    - issue_ref: "issue-5e7a03c4"
      relationship: >
        related. Introduced the cause line at y=210 that this issue
        keeps and expects to carry more messages over time.
    - issue_ref: "issue-9c2f41d8"
      relationship: >
        related. Made the transport retry indefinitely, which is what
        turned this screen into one that is waited in.
    - issue_ref: "issue-2ac1c602"
      relationship: >
        related. The condition it concerned — a live process with every
        worker torn down — is indistinguishable on this screen from
        normal retrying. A liveness indicator would have made it
        visible at the time.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Three changes to the DISCONNECTED screen, display-only.

    1. Remove the Simulate button. Register and draw a single Setup
    button. Simulate remains on OPTIONS page 0, reachable by the
    existing downward swipe.

    2. Add a retry-countdown arc, driven by the display's own frame
    clock, sweeping once per transport retry interval. It must
    continue to animate while the transport thread is blocked, since
    demonstrating that the display loop is alive is its purpose.

    3. Keep the existing cause line at y=210 as the single status line
    and add messages to it as they become available, rather than
    introducing further lines.

    Explicitly not in this scope: a Bluetooth reset button. It is
    wanted in the freed space, but requires privileged host access and
    a recovery action not yet established to work on this hardware, and
    is being raised separately.
  change_ref: ""
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A screen that can be displayed indefinitely should carry evidence
    that the application behind it is alive.
  process_improvements: >
    A control duplicated on two screens should be noticed when the
    second is added, not when space runs short on the first.

verification_enhanced:
  verification_steps:
    - "Confirm that the DISCONNECTED Simulate button and OPTIONS page 0's simulation_mode both call _on_simulation_mode. [DONE — manager.py:1622 and 1720.]"
    - "Confirm from debug.log that simulation_mode is used from the OPTIONS screen. [DONE — four occurrences.]"
    - "After the change: confirm only one button is registered and drawn on DISCONNECTED, and that its rect matches the registered region."
    - "After the change: confirm the arc animates continuously while the transport thread is blocked in a connect attempt."
    - "After the change: confirm Simulate is still reachable from OPTIONS page 0 by the downward swipe."
    - "After the change: confirm the arc's period tracks the transport's configured retry interval."
  verification_results: "First two steps complete. Remainder require the change to exist."

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  The liveness indicator's value is highest in precisely the case it
  cannot be tested for easily: a display loop that is running while
  everything behind it is not. Driving it from the frame clock rather
  than from transport state is what makes it meaningful, and is the one
  detail that must not be compromised for convenience.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial issue document from user request during on-target diagnosis."
      - "Confirmed that the DISCONNECTED Simulate button duplicates OPTIONS page 0's simulation_mode control, both calling _on_simulation_mode."
      - "Records that the screen carries nothing that changes over time, so a working application and a hung one are indistinguishable on it."
      - "Records the design constraint that the liveness indicator must be driven by the display frame clock, not by transport state."
      - "Records that a Bluetooth reset button, though wanted in the freed space, is deferred pending an established recovery command."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial issue document. The DISCONNECTED screen's Simulate button duplicates an OPTIONS control, and the screen gives no indication the application is alive. |

---

Copyright (c) 2026 William Watson. MIT License.
