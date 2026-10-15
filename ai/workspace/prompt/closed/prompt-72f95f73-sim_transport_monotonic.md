Created: 2026 October 14

# Prompt: Monotonic Clock for the SimTransport RPM Sweep

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-72f95f73"
  task_type: "debug"
  source_ref: "change-72f95f73"
  target_profile: "engine"
  date: "2026-10-14"
  iteration: 1
  coupled_docs:
    change_ref: "change-72f95f73"
    change_iteration: 1

context:
  purpose: "SimTransport measures the RPM sweep's elapsed time with time.monotonic()."
  integration: "src/gtach/comm/sim_transport.py; tests/test_sim_transport.py."
  knowledge_references:
    - "ai/workspace/issues/issue-72f95f73-sim-transport-wall-clock.md"
    - "ai/workspace/change/change-72f95f73-sim-transport-monotonic.md"
  constraints:
    - "Change only the two time.time() calls in sim_transport.py (SimTransport.__init__ _start_time; _compute_rpm_response elapsed time t). Do not change responses, the sweep formula, period or range."
    - "Edit only the two deliverable files. Keep the existing four tests in tests/test_sim_transport.py unchanged."
    - "Locate code by symbol; line numbers are from bb29226."

specification:
  description: "Clock switch per change-72f95f73 with clock-step regression tests."
  requirements:
    functional:
      - "Wall-clock steps do not affect the simulated RPM sweep."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Comment at the _start_time assignment citing issue-72f95f73"
  performance: []

design:
  architecture: "Two-line clock switch."
  components:
    - name: "SimTransport"
      type: "class"
      purpose: "_start_time = time.monotonic(); t = time.monotonic() - self._start_time."
      logic:
        - "Replace time.time() with time.monotonic() at both sites; keep 'import time'."
    - name: "tests/test_sim_transport.py"
      type: "module"
      purpose: "Two regression tests appended after the existing tests."
      logic:
        - "In each test, monkeypatch the attribute 'time' of module gtach.comm.sim_transport (not the global time module) with types.SimpleNamespace(monotonic=<scripted function>, time=<function that raises AssertionError>)."
  dependencies:
    internal:
      - "gtach.comm.sim_transport.SimTransport"
    external:
      - "pytest (monkeypatch)"

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "monotonic() returns 1000.0 for every call; construct SimTransport; send_command('010C')."
      expected: "'41 0C 39 08'; time() never called."
    - scenario: "monotonic() returns 1000.0 at construction, then 1030.0; send_command('010C')."
      expected: "'41 0C 39 08' (half period, sine 0); time() never called."
  edge_cases: []
  validation:
    - "grep -n 'time.time()' src/gtach/comm/sim_transport.py returns nothing."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary."
  files:
    - path: "src/gtach/comm/sim_transport.py"
      content: "Clock switch"
    - path: "tests/test_sim_transport.py"
      content: "Two regression tests appended"

success_criteria:
  - "No time.time() remains in sim_transport.py."
  - "Both new tests pass; the four existing tests are unchanged and pass."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "sim_transport"
        path: "src/gtach/comm/sim_transport.py"
    classes:
      - name: "SimTransport"
        module: "gtach.comm.sim_transport"
    functions: []
    constants: []

tactical_brief: |
  Files: src/gtach/comm/sim_transport.py and tests/test_sim_transport.py only.

  1. In sim_transport.py replace the two time.time() calls with time.monotonic():
     - SimTransport.__init__: self._start_time = time.monotonic()
       Add the comment "# monotonic: elapsed time only (issue-72f95f73)".
     - SimTransport._compute_rpm_response: t = time.monotonic() - self._start_time
     Change nothing else. Keep "import time".

  2. Append two tests to tests/test_sim_transport.py. Do not change the four
     existing tests. In each test, replace the module's time reference:
       import types
       import gtach.comm.sim_transport as sim_module
       monkeypatch.setattr(sim_module, "time", types.SimpleNamespace(
           monotonic=<scripted function>, time=<function raising AssertionError>))
     a) test_rpm_sweep_uses_monotonic_clock: monotonic() always returns 1000.0;
        SimTransport().send_command("010C") == "41 0C 39 08".
     b) test_rpm_sweep_ignores_wall_clock_steps: monotonic() returns 1000.0 on
        the first call and 1030.0 afterwards; the response is "41 0C 39 08".

  3. Run: python -m pytest -q tests/test_sim_transport.py, then the full tests/ suite.

  Success: no time.time() in sim_transport.py; the six tests in
  test_sim_transport.py pass; the full suite passes.

notes: "Engine loop on the Mistral API (both roles mistral-medium-2604). Also the live validation of framework change-7d953510 (api_key_keychain via engine-mcp)."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-14 | Initial prompt implementing change-72f95f73 iteration 1. Target profile engine. |
| 1.1 | 2026-10-14 | Implemented by engine run 1e00fd66 (SHIP after one cycle); closed |

---

Copyright (c) 2026 William Watson. MIT License.
