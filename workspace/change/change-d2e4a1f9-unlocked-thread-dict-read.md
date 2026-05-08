Created: 2026 May 08

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-d2e4a1f9"
  title: "Replace direct threads dict access in _draw_status_indicator with locked public API"
  date: "2026-05-08"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-d2e4a1f9"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-d2e4a1f9"
  description: >
    Direct unlocked read of ThreadManager.threads in _draw_status_indicator
    is a data race with watchdog/OBD threads that modify the dict under lock.

scope:
  summary: >
    Replace direct threads dict access with thread_manager.get_thread_status()
    in DisplayManager._draw_status_indicator.
  affected_components:
    - name: "DisplayManager._draw_status_indicator"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs:
    - design_ref: ""
      sections: []
  out_of_scope:
    - "Any other direct threads dict reads (none identified elsewhere in manager.py)"
    - "ThreadManager internals"

rational:
  problem_statement: >
    Directly reading ThreadManager.threads from a different thread bypasses
    the _state_lock protection, violating the thread safety contract.
  proposed_solution: >
    Use the existing public get_thread_status(name) method which acquires
    _state_lock internally and returns a safe snapshot.
  alternatives_considered:
    - option: "Add a separate unlocked is_transport_running() method to ThreadManager"
      reason_rejected: "Unnecessary — get_thread_status already exists and is correct."
  benefits:
    - "Eliminates data race."
    - "Removes direct dependency on ThreadManager internal structure."
  risks: []

technical_details:
  current_behavior: |
    if 'transport' not in self.thread_manager.threads:
        status = ConnectionStatus.DISCONNECTED
    else:
        thread_status = self.thread_manager.threads['transport'].status
        if thread_status == ThreadStatus.RUNNING:
            status = ConnectionStatus.CONNECTED
        elif thread_status == ThreadStatus.STARTING:
            status = ConnectionStatus.CONNECTING
        else:
            status = ConnectionStatus.DISCONNECTED
  proposed_behavior: |
    thread_status = self.thread_manager.get_thread_status('transport')
    if thread_status == ThreadStatus.RUNNING:
        status = ConnectionStatus.CONNECTED
    elif thread_status == ThreadStatus.STARTING:
        status = ConnectionStatus.CONNECTING
    else:
        status = ConnectionStatus.DISCONNECTED
  implementation_approach: "Single targeted edit to _draw_status_indicator."
  code_changes:
    - component: "DisplayManager._draw_status_indicator"
      file: "src/gtach/display/manager.py"
      change_summary: "Replace direct threads dict access with get_thread_status()"
      functions_affected:
        - "_draw_status_indicator"
      classes_affected:
        - "DisplayManager"
  interface_changes: []

dependencies:
  internal:
    - component: "ThreadManager.get_thread_status"
      impact: "None. Method already exists and is used elsewhere."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Code review and visual confirmation of status indicator."
  test_cases:
    - scenario: "Normal running session"
      expected_result: "Status indicator renders without error."
    - scenario: "Transport not yet started"
      expected_result: "get_thread_status returns None — maps to DISCONNECTED."
  regression_scope:
    - "Status indicator visibility during simbt session"
  validation_criteria:
    - "No direct access to self.thread_manager.threads in _draw_status_indicator"
    - "Status indicator renders correctly"

implementation:
  implementation_steps:
    - step: "Edit _draw_status_indicator — replace dict access with get_thread_status()"
      owner: "Claude Code"
  rollback_procedure: "Revert src/gtach/display/manager.py."
  deployment_notes: "Rebuild wheel and deploy to Pi."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-d2e4a1f9"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-05-08"
    author: "William Watson"
    changes:
      - "Initial change document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
