# Prompt: Simulation RPM Alignment

Created: 2026 November 24

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-0b3317b7"
  task_type: "refactor"
  source_ref: "change-0b3317b7"
  target_profile: "claude_code"
  date: "2026-11-24"
  iteration: 1
  coupled_docs:
    change_ref: "change-0b3317b7"
    change_iteration: 1

context:
  purpose: "Make the startup simulation and the OPTIONS simulation mode produce the same RPM sweep from one shared function."
  integration: "src/gtach/comm/sim_transport.py; src/gtach/display/manager.py; tests/test_sim_transport.py."
  knowledge_references:
    - "ai/workspace/issues/issue-0b3317b7-sim-rpm-alignment.md"
    - "ai/workspace/change/change-0b3317b7-sim-rpm-alignment.md (C1-C5 are the specification)"
    - "ai/workspace/design/design-7d3e9f5a-domain_comm.md (SimTransport)"
    - "CLAUDE.md"
  constraints:
    - "CRITICAL: sweep is exactly 800 + 2900 * (1 + sin(t * 2π / 15)), expressed through SIM_RPM_MIN, SIM_RPM_MAX, SIM_RPM_PERIOD_S."
    - "CRITICAL: DisplayManager imports sim_rpm inside the simulation-mode branch (circular-import risk: comm.pairing imports display.setup_models). No module-level import of gtach.comm in manager.py."
    - "CRITICAL: the simulation branch keeps self._last_rpm = rpm and rpm = self._condition_rpm(rpm) unchanged; engine-off, disconnected and live paths unchanged."
    - "CRITICAL: 010C encoding and all other SimTransport behaviour unchanged."
    - "No time.time() in either sweep path."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on new or changed signatures. Google-style docstrings citing change-0b3317b7."

specification:
  description: "Apply C1-C5 of change-0b3317b7."
  requirements:
    functional:
      - "As change-0b3317b7 technical_details.implementation_approach."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access (sim_rpm is pure)"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No measurable per-frame cost beyond one sin() call and a sys.modules lookup"
      metric: "time"

design:
  architecture: "Unchanged. A pure module-level function in comm/sim_transport.py is the single definition of the synthetic sweep."
  components:
    - name: "sim_rpm"
      type: "function"
      purpose: "Synthetic RPM for a time in seconds."
      interface:
        inputs:
          - name: "t"
            type: "float"
            description: "Time in seconds (any monotonic base)."
        outputs:
          type: "float"
          description: "RPM in [800, 6600], 15 s period."
        raises: []
      logic:
        - "C1-C5 exactly as change-0b3317b7, in that order."
  dependencies:
    internal:
      - "gtach.comm.sim_transport.sim_rpm (used by SimTransport and DisplayManager)"
    external: []

error_handling:
  strategy: "Unchanged; the simulation branch sits inside the existing try block of _draw_radial_mode."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As change-0b3317b7 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Do not sample at t = 15 s in a value test: it equals t = 0."
  validation:
    - "SDL_VIDEODRIVER=dummy pytest tests/ passes."
    - "mypy src/ reports no new issues; black, isort and flake8 clean on the changed src/ files."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
    - "Each changed test assertion is listed in the report with old and new value; unrelated assertions are not weakened."
    - "Move this prompt to ai/workspace/prompt/closed/ when finished. Leave the issue and change active (status: change implemented, issue resolved) pending device test."
    - "Report ai/workspace/report/report-0b3317b7-sim-rpm-alignment.md: per item C1-C5 what changed; deviations from the change document; test results."
  files:
    - path: "src/gtach/comm/sim_transport.py"
      content: "C1, C2"
    - path: "src/gtach/display/manager.py"
      content: "C3"
    - path: "tests/test_sim_transport.py"
      content: "C4, C5"

success_criteria:
  - "sim_rpm(0) == 3700, sim_rpm(3.75) == 6600, sim_rpm(11.25) == 800 (within 1e-6)."
  - "SimTransport returns '41 0C 39 D0' at t = 0 and '41 0C 67 20' at t = 3.75 s."
  - "The OPTIONS simulation mode calls sim_rpm(time.monotonic()); no time.time() remains in either sweep path."
  - "git diff touches only the three files above, this prompt's move, the issue and change status lines, and the report."
  - "pytest tests/ passes; mypy src/ reports no new issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "sim_rpm"
        module: "gtach.comm.sim_transport"
        signature: "(t: float) -> float"
    constants:
      - name: "SIM_RPM_MIN"
        module: "gtach.comm.sim_transport"
        type: "int"
      - name: "SIM_RPM_MAX"
        module: "gtach.comm.sim_transport"
        type: "int"
      - name: "SIM_RPM_PERIOD_S"
        module: "gtach.comm.sim_transport"
        type: "float"

notes: "Execution option C (Claude Code). Pull request reviewed by the planner before merge; device check after merge."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-24 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
