Created: 2026 October 09

# Prompt: SimTransport Observes drop_link

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-50bf25ad"
  task_type: "debug"
  source_ref: "change-50bf25ad"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-50bf25ad"
    change_iteration: 1

context:
  purpose: "Make a dropped SimTransport link observable so reconnection runs in simulation."
  integration: "src/gtach/comm/sim_transport.py; tests/test_lifecycle_sim.py; tests/test_sim_transport.py."
  knowledge_references:
    - "ai/workspace/issues/issue-50bf25ad-sim-transport-drop-link-not-observed.md"
    - "ai/workspace/change/change-50bf25ad-sim-transport-drop-link-not-observed.md"
  constraints:
    - "Do not modify OBDTransport (src/gtach/comm/transport.py)."
    - "Do not set _shutdown in drop_link: reconnection must remain possible."
    - "No logging and no call to super() while holding self._lock (CLAUDE.md §4 rule 8)."
    - "Do not change connect, disconnect, is_connected or state."
    - "Line numbers in the issue are stale; locate code by symbol."
    - "Python 3.9+; PEP 8; Google-style docstring."

specification:
  description: "Add SimTransport.drop_link and remove the strict xfail on the link-loss lifecycle test."
  requirements:
    functional:
      - "After drop_link(cause), is_connected() is False, state is DISCONNECTED, last_failure_cause is cause (or the base default), _shutdown is not set."
      - "reconnect_indefinitely reconnects after retry_delay and OBDProtocol resumes producing samples."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe: _connected written under self._lock"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Method override delegating to the base implementation."
  components:
    - name: "SimTransport.drop_link"
      type: "function"
      purpose: "Close the simulated link while leaving reconnection possible."
      interface:
        inputs:
          - name: "cause"
            type: "Optional[str]"
            description: "Why the link was dropped; None uses the base default."
        outputs:
          type: "None"
          description: ""
        raises: []
      logic:
        - "with self._lock: self._connected = False"
        - "super().drop_link(cause)  # after releasing the lock"
        - "Docstring references issue-50bf25ad and the drop_link/disconnect distinction."
    - name: "tests/test_lifecycle_sim.py"
      type: "module"
      purpose: "Remove the @pytest.mark.xfail(strict=True, ...) decorator from TestLinkLoss.test_drop_is_observed_and_link_reconnects only."
      logic:
        - "Leave the TestWatchdogQuiet xfail in place (change-04c18cda removes it)."
    - name: "tests/test_sim_transport.py"
      type: "module"
      purpose: "Unit tests for the override (create; extend if it already exists)."
      logic:
        - "Tests listed under testing.unit_tests."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged; the base drop_link tolerates a None handle."
  exceptions: []
  logging:
    level: "INFO (base class message)"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "connect(); drop_link('test cause')."
      expected: "is_connected() False; state DISCONNECTED; last_failure_cause 'test cause'; _shutdown.is_set() False."
    - scenario: "connect(); drop_link()."
      expected: "last_failure_cause equals gtach.comm.transport._SILENT_LINK_CAUSE."
    - scenario: "drop_link(); connect()."
      expected: "connect() True; is_connected() True."
    - scenario: "tests/test_lifecycle_sim.py::TestLinkLoss::test_drop_is_observed_and_link_reconnects without xfail."
      expected: "Passes."
  edge_cases:
    - "drop_link() before any connect(): no exception; is_connected() False."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/comm/sim_transport.py"
      content: "drop_link override"
    - path: "tests/test_lifecycle_sim.py"
      content: "xfail removed from TestLinkLoss.test_drop_is_observed_and_link_reconnects"
    - path: "tests/test_sim_transport.py"
      content: "Unit tests"

success_criteria:
  - "grep -n 'def drop_link' src/gtach/comm/sim_transport.py returns one match."
  - "TestLinkLoss.test_drop_is_observed_and_link_reconnects passes without xfail."
  - "git diff shows no change to src/gtach/comm/transport.py."
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
    functions:
      - name: "drop_link"
        module: "gtach.comm.sim_transport.SimTransport"
        signature: "drop_link(self, cause: Optional[str] = None) -> None"
    constants: []

notes: "Human verification: none on device; simulation only."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-50bf25ad iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-09 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
