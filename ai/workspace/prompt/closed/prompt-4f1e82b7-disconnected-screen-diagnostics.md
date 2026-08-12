Created: 2026 August 12

# Prompt: One Setup Button and a Retry-Countdown Arc on the DISCONNECTED Screen

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-4f1e82b7"
  task_type: "refactor"
  source_ref: "change-4f1e82b7"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-4f1e82b7"
    change_iteration: 1

context:
  purpose: >
    Remove the DISCONNECTED screen's Simulate button, which duplicates
    OPTIONS page 0's simulation_mode control, and give the screen a
    retry-countdown arc so an operator can see that GTach is alive and
    when the next connect attempt falls. At present the screen is
    visually identical whether GTach is retrying, blocked on a wedged
    Bluetooth controller, or a live process with every worker torn
    down.
  integration: >
    Two edits and one new private helper in
    src/gtach/display/manager.py, plus one callback wiring line in
    src/gtach/app.py. No other file is modified.
  knowledge_references:
    - "ai/workspace/issues/issue-4f1e82b7-disconnected-screen-diagnostics.md"
    - "ai/workspace/change/change-4f1e82b7-disconnected-screen-diagnostics.md"
  constraints:
    - "CRITICAL: the arc's animation phase must derive from time.monotonic() and from NO transport attribute or transport-derived state. Fed from the transport it would freeze whenever the transport thread blocks in connect() — precisely the moment the operator needs to know the application is alive. An indicator that stops when its subject stops implies a fault that may not exist."
    - "Do not add a Bluetooth reset button, or any control, in the freed slot. It is deliberately left empty pending a separate issue."
    - "Do not add a second or third status line. The single cause line at y=210 stays as it is."
    - "Do not modify _button_column. Call it with a one-element sequence; it already accepts a variable-length Sequence."
    - "Do not modify _on_simulation_mode or OPTIONS page 0's simulation_mode registration. That control is where Simulate continues to live."
    - "Do not modify _enter_setup_from_disconnected."
    - "Do not modify anything under src/gtach/comm/. The retry interval arrives through a callback."
    - "Do not move the Setup button. _button_column stacks downward from an explicit top of 240, so the first rect must be unchanged."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply edits U and V and the app.py wiring, then add the unit tests in the testing section."
  requirements:
    functional:
      - "Exactly one touch region, disconnected_setup, is registered on the DISCONNECTED screen."
      - "The Setup button occupies the same rect as before."
      - "An arc sweeps once per transport retry interval, below the button."
      - "The arc advances between two renders with no change in transport state."
      - "The arc falls back to a 5.0 s period when the interval is unavailable, zero, negative or raises."
      - "The existing cause line is unchanged."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "The DISCONNECTED screen still reports 30.0 FPS in the DisplayManager performance line"
      metric: "time"

design:
  architecture: >
    Liveness is a property of the display loop, so it must be measured
    by the display loop. The arc is a pure function of the frame clock
    and a period; nothing it reads can block.
  components:
    - name: "EDIT U — one button on the DISCONNECTED screen"
      type: "function"
      purpose: "Remove a control duplicated on OPTIONS page 0."
      logic:
        - "In _register_disconnected_regions (manager.py:1706-1724), reduce the specs tuple passed to _button_column to a single entry: (\"disconnected_setup\", TouchAction.NAVIGATION, lambda pos: self._enter_setup_from_disconnected())."
        - "Assign the single returned rect to self._disconnected_btn_setup. Remove self._disconnected_btn_sim entirely — the attribute, not just its assignment. Check for and remove any other reference to it."
        - "Keep width=240 and top=240 exactly as now, so the button does not move."
        - "Update the method docstring: one control, Setup; Simulate lives on OPTIONS page 0 and is one downward swipe away (issue-4f1e82b7)."
        - "In _render_disconnected, remove the drawing of the Simulate button and its label; draw only the Setup button, from self._disconnected_btn_setup, via the existing _draw_button."
    - name: "EDIT V — the retry-countdown arc"
      type: "function"
      purpose: "Show that the display loop is alive, and roughly when the next attempt falls."
      logic:
        - "Add an instance attribute self._retry_interval_callback = None wherever _link_cause_callback and _link_connected_callback are initialised, matching their pattern exactly."
        - "Add a private method `def _draw_retry_arc(self) -> None:`."
        - "Resolve the period: call self._retry_interval_callback() when it is set, inside try/except Exception; if it is unset, raises, or returns a value that is not a positive number, use 5.0 — the default of reconnect_indefinitely."
        - "Compute the phase as `(time.monotonic() % period) / period`, giving 0.0 to 1.0. Sweep the arc from full at phase 0 to empty as phase approaches 1, so the arc empties as the next attempt approaches."
        - "Draw below the Setup button and inside the r=238 circular viewport. The button column starts at top=240 with height >= 72, so place the arc's band below y=330 and keep it within the viewport."
        - "Use the existing arc rendering the RPM gauge already depends on and the existing palette; do not introduce a new drawing primitive."
        - "Wrap the whole body so a failure to draw the arc cannot prevent the rest of the screen rendering; log at DEBUG with exc_info=True."
        - "Call _draw_retry_arc from _render_disconnected, after the button is drawn."
        - "Docstring must state plainly: the phase comes from the display frame clock, NOT from transport state, so that it keeps animating while the transport thread is blocked in connect(); and that it indicates approximately when the next attempt falls rather than being a synchronised countdown."
    - name: "EDIT V(b) — wire the interval callback"
      type: "class"
      purpose: "Let the arc's period follow the transport's configured retry delay."
      logic:
        - "In src/gtach/app.py, beside the existing self._display._link_connected_callback and self._display._link_cause_callback assignments, add self._display._retry_interval_callback returning the transport's configured retry delay."
        - "Guard it the same way the existing _link_connected_callback lambda is guarded, so that no transport yet present yields the default rather than raising."
        - "This is the ONLY permitted change to app.py."

data_schema:
  entities: []

error_handling:
  strategy: "The indicator must never be able to break the screen it is meant to reassure the operator about."
  exceptions:
    - exception: "Exception"
      condition: "_retry_interval_callback raises or returns an unusable value."
      handling: "Use the 5.0 s default. No propagation."
    - exception: "Exception"
      condition: "Arc drawing fails."
      handling: "Log at DEBUG with exc_info=True; the button, title, message and cause line must still render."
  logging:
    level: "DEBUG"
    format: "Existing _LOG_FORMAT; no format change."

testing:
  unit_tests:
    - scenario: "_register_disconnected_regions is called."
      expected: "Exactly one region is registered; its id is 'disconnected_setup'; no region named 'disconnected_simulate' is registered."
    - scenario: "The rect returned for the Setup button."
      expected: "Equal to the first rect returned by the pre-change two-button call with the same width and top."
    - scenario: "_draw_retry_arc with _retry_interval_callback unset."
      expected: "Uses a 5.0 s period; no exception."
    - scenario: "_draw_retry_arc with the callback returning 5.0, at monotonic times t and t + 2.5."
      expected: "The computed phase differs by approximately 0.5."
    - scenario: "_draw_retry_arc with the callback returning 0."
      expected: "Falls back to 5.0; no ZeroDivisionError."
    - scenario: "_draw_retry_arc with the callback returning -1."
      expected: "Falls back to 5.0."
    - scenario: "_draw_retry_arc with the callback raising."
      expected: "Falls back to 5.0; no exception propagates."
    - scenario: "_draw_retry_arc where the arc drawing primitive raises."
      expected: "No exception propagates; a DEBUG log is emitted."
    - scenario: "Two _render_disconnected calls with the monotonic clock advanced and NO transport state changed."
      expected: "The arc phase differs between the two. Assert the phase computation reads no transport attribute."
    - scenario: "_render_disconnected with a cause set."
      expected: "The cause line is drawn at its existing position with its existing font and colour."
    - scenario: "grep the phase computation for transport references."
      expected: "It derives from time.monotonic() and the resolved period only."
  edge_cases:
    - "A period shorter than one frame interval — the phase must remain within 0.0 to 1.0 and must not raise."
    - "time.monotonic() returning a very large value — the modulo must still yield a valid phase."
    - "Rendering before any transport exists — the callback guard yields the default."
  validation:
    - "grep -n 'disconnected_simulate' src/gtach/display/manager.py returns no match."
    - "grep -n '_disconnected_btn_sim' src/gtach/display/manager.py returns no match."
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/display/manager.py').read())\""

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing files in place. Do not create new modules."
  files:
    - path: "src/gtach/display/manager.py"
      content: "EDIT U and EDIT V"
    - path: "src/gtach/app.py"
      content: "EDIT V(b) — the _retry_interval_callback wiring only"
    - path: "tests/test_disconnected_screen.py"
      content: "Unit tests for testing.unit_tests items 1-11"

success_criteria:
  - "grep -n 'disconnected_simulate' src/gtach/display/manager.py returns no match."
  - "grep -n '_disconnected_btn_sim' src/gtach/display/manager.py returns no match."
  - "_register_disconnected_regions passes a one-element sequence to _button_column with width=240 and top=240 unchanged."
  - "DisplayManager defines _draw_retry_arc, called from _render_disconnected."
  - "The arc phase computation references time.monotonic() and contains no reference to any transport attribute or to _link_connected_callback."
  - "The period falls back to 5.0 when the callback is unset, raises, or returns a non-positive value."
  - "_button_column is byte-identical to its pre-change state."
  - "_on_simulation_mode and the OPTIONS page 0 simulation_mode registration are byte-identical to their pre-change state."
  - "_enter_setup_from_disconnected is byte-identical to its pre-change state."
  - "The cause line rendering introduced by change-5e7a03c4 is unchanged."
  - "No control is added in the freed button slot."
  - "The only change to src/gtach/app.py is the _retry_interval_callback wiring."
  - "src/gtach/comm/ is byte-identical throughout."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "app"
        path: "src/gtach/app.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "GTachApplication"
        module: "gtach.app"
    functions:
      - name: "_register_disconnected_regions"
        module: "gtach.display.manager"
        signature: "(self) -> None"
      - name: "_render_disconnected"
        module: "gtach.display.manager"
        signature: "(self) -> None"
      - name: "_draw_retry_arc"
        module: "gtach.display.manager"
        signature: "(self) -> None"
      - name: "_button_column"
        module: "gtach.display.manager"
        signature: "(self, specs, width, top, height=None, separation=None) -> List[pygame.Rect]"
    constants: []

notes: >
  On-target verification is a human step. With no OBD connection
  available: confirm one button only; confirm Simulate is still
  reachable on OPTIONS page 0 by the downward swipe; confirm the arc
  sweeps and empties roughly once per retry interval; and — the point
  of the change — confirm the arc KEEPS animating while a connect
  attempt is blocked, which on gtach.local's current EBUSY state is
  readily reproducible. Confirm the performance line still reports
  30.0 FPS on this screen.

  The freed button slot is intentionally empty. A Bluetooth reset
  button is wanted there and is blocked on establishing which recovery
  command works on this hardware: `hciconfig hci0 down && up` was tried
  on target and left the controller unable to come back.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial prompt implementing change-4f1e82b7 iteration 1. Two edits in manager.py, one wiring line in app.py, one unit test module. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
