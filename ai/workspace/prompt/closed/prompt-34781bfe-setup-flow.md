# Prompt: Setup Flow — One Operation Rule, Presented Outcomes

Created: 2026 November 11

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-34781bfe"
  task_type: "refactor"
  source_ref: "change-34781bfe"
  target_profile: "claude_code"
  date: "2026-11-11"
  iteration: 1
  coupled_docs:
    change_ref: "change-34781bfe"
    change_iteration: 1

context:
  purpose: "Run 4 of proposal-71ab3751: implement design-a3b4c5d6 v2.0 in the setup flow."
  integration: "src/gtach/display/setup.py, setup_components/*, async_operations.py, setup_models.py; one line in app.py; tests."
  knowledge_references:
    - "ai/workspace/design/design-a3b4c5d6-component_display_setup_manager.md (sections 4.0 to 6.0 govern)"
    - "ai/workspace/issues/issue-34781bfe-setup-flow.md"
    - "ai/workspace/change/change-34781bfe-setup-flow.md"
    - "ai/workspace/change/change-b4f9607a-comm-layer-defects.md (EDITS F, G, H: back-end contracts)"
    - "ai/workspace/change/change-042dd7ff-lifecycle-logging-utils.md (EDIT A(3): reader of adapter_reset_in_session)"
    - "CLAUDE.md section 4 (rule 8)"
  constraints:
    - "CRITICAL: before editing, confirm that design-a3b4c5d6 has status approved and that the comm interfaces of change-b4f9607a exist in the source (the fallback result, pair_device honouring cancellation, save_device returning bool). If either is missing, stop and report."
    - "CRITICAL: setup state is written only through the coordinator (update_state, add_discovered_device, transition_to_screen) or the interface's _set_state and _add_device helpers (issue-d140121d)."
    - "CRITICAL: no call-outs under a lock. _is_current is evaluated under _ops_lock; state writes, screen transitions, async_manager calls and back-end cancel calls happen after it is released."
    - "A scan is started in exactly one place per entry to DISCOVERY; the setup loop starts none."
    - "The setup thread keeps its heartbeat and the COMPLETE hold; stop_setup does not join the calling thread (issue-674bec49)."
    - "The only edit outside the setup flow files is the removal of the type: ignore and TODO comments at the SetupDisplayManager construction in app.py."
    - "Screen geometry, fonts, colours and texts stay as they are, except as the change states. Error-line texts exactly as given in the change."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to G and the COMMENT RULE of change-34781bfe; add tests/test_setup_flow.py."
  requirements:
    functional:
      - "As in change-34781bfe proposed_solution and design-a3b4c5d6 sections 4.0 to 6.0."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance:
    - target: "Uncached setup screens are drawn without the per-frame surface copy and blit"
      metric: "time"

design:
  architecture: "Coordinator owns state; the interface owns operations and decides what follows each completion; the setup loop only sends heartbeats, holds COMPLETE and invokes the completion callback."
  components:
    - name: "EDITS A to G"
      type: "module"
      purpose: "As in change-34781bfe."
      logic:
        - "Read the five files in full before editing; the edits interact."
        - "EDIT A: capture the operation id returned by submit_operation in the closure of each callback, and register it before the worker can run the task (register under _ops_lock immediately after submit, and make _is_current tolerate a callback that arrives before registration by registering first with a reserved id if submit_operation allows an id to be supplied; otherwise state the chosen approach in the report)."
        - "EDIT A: the pairing status_callback and the discovery device-found callback run on a worker thread during the task; they use the same _is_current check."
        - "EDIT B(1): start the scan from the handler of the transition into DISCOVERY; _handle_touch_action already calls start_pairing in the same manner for SELECT_DEVICE."
        - "EDIT B(2): recognise the fallback by all(d.device_classification is DeviceType.UNKNOWN for d in devices) on a non-empty list."
        - "EDIT C: _probe_in_flight already exists on SetupDisplayManager; use it for the region decision and clear it when the probe is cancelled."
        - "EDIT D: blend = background + (dot - background) * factor, per channel, factor from 1.0 down to about 0.2 across the eight dots."
        - "EDIT E: inspect.signature(task).parameters; pass progress_callback only when the name is declared."
        - "EDIT F: set adapter_reset_in_session from the interface through a callback or attribute the manager reads; simulation pass-through returns True without sending ATZ and must not set it."

data_schema:
  entities: []

error_handling:
  strategy: "A completion for an operation that is no longer registered is ignored silently at DEBUG. Failures of the current operation are shown on the error line."
  exceptions: []
  logging:
    level: "Unchanged; ignored completions at DEBUG"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-34781bfe testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Cancel tapped twice."
    - "Retry tapped on DEVICE_LIST while the previous scan's task is still running: the old completion is ignored and the new scan's result is shown."
    - "stop_setup during a scan: no state write after stop."
    - "A completion callback that arrives before its registration was stored."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place; one new test module; one commit."
    - "Report: per EDIT, what changed; where the scan is started; how the registration race was handled; any deviation from the design or the change; test results."
  files:
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "EDITS A, B(2), E (task parameter names), F"
    - path: "src/gtach/display/setup.py"
      content: "EDITS A(4), B(1), B(3), C, D, E (render), F, G"
    - path: "src/gtach/display/setup_components/state/coordinator.py, src/gtach/display/setup_models.py"
      content: "EDITS A(5), D"
    - path: "src/gtach/display/async_operations.py"
      content: "EDIT E"
    - path: "src/gtach/app.py"
      content: "EDIT G (one call site)"
    - path: "tests/test_setup_flow.py"
      content: "Tests"

success_criteria:
  - "Every completion and in-task callback in interface.py checks _is_current before it writes state or changes screen."
  - "Cancel on DISCOVERY and Back on PAIRING call cancel_operation; an abandoned operation's completion changes nothing."
  - "_setup_loop contains no call to start_discovery and no transition to DEVICE_LIST."
  - "Empty, failed and fallback scans reach DEVICE_LIST with the stated texts; no automatic rescan."
  - "The New Setup region is absent while a probe is in flight."
  - "The PAIRING screen has no Continue button."
  - "No RGBA colour is passed to pygame.draw.circle in the spinners."
  - "AsyncOperationManager holds no finished operation; no inspection of local-variable names remains."
  - "on_pairing_complete uses save_device's result."
  - "SetupDisplayManager.adapter_reset_in_session exists with the stated meaning."
  - "No type: ignore remains at the SetupDisplayManager construction in app.py."
  - "git diff touches only the setup flow files, that one call in app.py, and tests/."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "cancel_operation"
        module: "gtach.display.setup_components.bluetooth.interface"
        signature: "(self, name: str) -> None"
      - name: "_is_current"
        module: "gtach.display.setup_components.bluetooth.interface"
        signature: "(self, name: str, operation_id: str) -> bool"
    constants: []

notes: "Model: Claude Opus 5.5, effort medium; effort high may be chosen for this run. No ultracode. Human verification: device session B after run 5."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial prompt implementing change-34781bfe iteration 1. Target profile claude_code. |
| 1.1 | 2026-11-12 | Executed by Claude Code. EDITS A to G and the COMMENT RULE applied; deviations are listed in report-34781bfe. pytest and mypy pass. Closed and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
