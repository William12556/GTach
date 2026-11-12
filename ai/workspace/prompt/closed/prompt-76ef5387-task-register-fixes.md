# Prompt: Task Register Fixes — Texts, Simulation, Log Levels, Connect Causes

Created: 2026 November 12

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-76ef5387"
  task_type: "debug"
  source_ref: "change-76ef5387"
  target_profile: "claude_code"
  date: "2026-11-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-76ef5387"
    change_iteration: 1

context:
  purpose: "Apply EDITS A to G of change-76ef5387: six small fixes from ai/task.md."
  integration: "src/gtach/comm/transport.py, src/gtach/comm/sim_bluetooth.py, src/gtach/display/setup_components/bluetooth/interface.py, bin/gtach.service; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-76ef5387-task-register-fixes.md"
    - "ai/workspace/change/change-76ef5387-task-register-fixes.md"
    - "tests/test_connect_error_classification.py (_StubTransport, wedge tests)"
    - "tests/test_session_b_findings.py (width test)"
    - "CLAUDE.md section 4"
  constraints:
    - "CRITICAL: no change to retry intervals, _MAX_CONSECUTIVE_CONNECT_FAILURES, _MAX_CONSECUTIVE_TIMEOUTS, the verify retry bound or delay."
    - "CRITICAL: EDIT C changes only the _IO_ERRORS handler of send_command; the timeout and generic handlers are unchanged."
    - "CRITICAL: EDIT E adds ordering only (After=); no Wants= or Requires= on hciuart."
    - "Existing tests keep passing unchanged, except the removal of the DEVICE_NOT_SAVED_TEXT xfail mark."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on public interfaces. Google-style docstrings. Comments cite issue-76ef5387."

specification:
  description: "Apply EDITS A to G; add tests."
  requirements:
    functional:
      - "As in change-76ef5387 rational.proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"

design:
  architecture: "Unchanged."
  components:
    - name: "EDIT A"
      type: "constant"
      purpose: "Error-line text fits 220 px."
      logic:
        - "interface.py: DEVICE_NOT_SAVED_TEXT = 'Not saved'."
        - "tests/test_session_b_findings.py: replace the pytest.param with xfail by plain DEVICE_NOT_SAVED_TEXT; update the module docstring to cite change-76ef5387."
    - name: "EDIT B"
      type: "data"
      purpose: "Simulation shows the normal device list."
      logic:
        - "sim_bluetooth.py: import DeviceType from ..display.setup_models."
        - "Set device_classification=DeviceType.HIGHLY_LIKELY_ELM327 on the three devices with device_type 'ELM327', and DeviceType.POSSIBLY_COMPATIBLE on 'Generic BT Adapter'."
    - name: "EDIT C"
      type: "function"
      purpose: "No ERROR for a handle this process closed."
      logic:
        - "In OBDTransport.send_command, at the top of the _IO_ERRORS handler: if self._acquire_handle() is not handle: logger.debug('Command %r ended by link close: %s', command, e); return None."
        - "Otherwise the existing ERROR record, cause classification, state change and discard, unchanged."
    - name: "EDIT D"
      type: "constant"
      purpose: "Readable, retried cause for ECONNABORTED."
      logic:
        - "transport.py: _errno.ECONNABORTED: LINK_RESET_CAUSE in _CONNECT_FAULT_CAUSES; extend the LINK_RESET_CAUSE comment to name ECONNABORTED."
    - name: "EDIT E"
      type: "config"
      purpose: "Start after the controller is attached at boot."
      logic:
        - "bin/gtach.service: append hciuart.service to the After= line; add a one-line comment: ordering only, the Pi Zero 2W controller appears when hciuart attaches it (issue-76ef5387)."
    - name: "EDIT F"
      type: "function"
      purpose: "A failed pairing is a WARNING."
      logic:
        - "interface.py on_pairing_complete: the branch operation.status == COMPLETED with a falsy result logs 'Failed to pair with device: ...' with self.logger.warning. The exception branch ('Pairing operation failed') stays at ERROR."
    - name: "EDIT G"
      type: "function"
      purpose: "No wedge diagnosis while the controller demonstrably works."
      logic:
        - "transport.py: module tuple _CONTROLLER_WORKING_CAUSES = (_CONNECT_FAULT_CAUSES[_errno.ECONNREFUSED], _CONNECT_FAULT_CAUSES[_errno.EHOSTDOWN]) with a comment: the peer answered or was paged, so the controller is working (issue-76ef5387)."
        - "OBDTransport.connect: replace 'refused = cause == ...ECONNREFUSED' with 'controller_working = cause in _CONTROLLER_WORKING_CAUSES'; increment the counter only when not controller_working; in the escalation condition replace the ECONNREFUSED comparison with 'cause not in _CONTROLLER_WORKING_CAUSES'. Update the adjacent comments."

error_handling:
  strategy: "Unchanged except EDIT C and EDIT F."
  exceptions: []
  logging:
    level: "Planned-close I/O error DEBUG; pairing returned False WARNING"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-76ef5387 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "EDIT C: disconnect() during the read of send_command (the handle replaced by None)."
    - "EDIT C: drop_link() during the read."
    - "EDIT G: alternating EHOSTDOWN and EBUSY never reaches the wedge threshold on EBUSY count alone below 6."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place. Tests: EDIT A in tests/test_session_b_findings.py; EDITS C, D, G in tests/test_connect_error_classification.py; EDITS B and F in a new tests/test_task_register_fixes.py (module docstring cites issue-76ef5387). One commit."
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
    - "Report ai/workspace/report/report-76ef5387-task-register-fixes.md: per EDIT, what changed; the measured width of 'Not saved'; deviations; test results."
  files:
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "EDIT A, EDIT F"
    - path: "src/gtach/comm/sim_bluetooth.py"
      content: "EDIT B"
    - path: "src/gtach/comm/transport.py"
      content: "EDIT C, EDIT D, EDIT G"
    - path: "bin/gtach.service"
      content: "EDIT E"
    - path: "tests/test_session_b_findings.py, tests/test_connect_error_classification.py, tests/test_task_register_fixes.py"
      content: "Tests"

success_criteria:
  - "DEVICE_NOT_SAVED_TEXT == 'Not saved' and renders at 220 px or less; no xfail remains in tests/test_session_b_findings.py."
  - "No SimBluetoothPairing fake device is DeviceType.UNKNOWN; a simbt scan result sets no error line."
  - "send_command on a handle closed by disconnect() or drop_link() logs nothing at ERROR and leaves last_failure_cause unchanged."
  - "_CONNECT_FAULT_CAUSES[errno.ECONNABORTED] == LINK_RESET_CAUSE."
  - "gtach.service After= contains hciuart.service; Wants= unchanged."
  - "A pairing that returns False is logged at WARNING."
  - "Repeated EHOSTDOWN or ECONNREFUSED never yields the wedge cause; six EBUSY still do."
  - "git diff touches only the four source/config files, the three test modules and the report."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants:
      - name: "DEVICE_NOT_SAVED_TEXT"
        module: "gtach.display.setup_components.bluetooth.interface"
        value: "Not saved"
      - name: "_CONTROLLER_WORKING_CAUSES"
        module: "gtach.comm.transport"
        type: "Tuple[str, ...]"

notes: "Model: Claude Opus 5.5, effort medium. No ultracode. Human verification after deploy: systemctl show hciuart -p Type,ActiveState; systemd-analyze critical-chain gtach.service; reboot with the adapter in range; service stop while connected; adapter radio off for 2 min; one setup with the emulator."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial prompt implementing change-76ef5387 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
