# Prompt: Engine Off Display State

Created: 2026 November 12

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-b29cbd71"
  task_type: "feature"
  source_ref: "change-b29cbd71"
  target_profile: "claude_code"
  date: "2026-11-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-b29cbd71"
    change_iteration: 1

context:
  purpose: "Show 'Engine off' instead of DISCONNECTED when the adapter is connected and reports a silent vehicle, and re-check the vehicle when RPM samples stop during polling."
  integration: "src/gtach/comm/obd.py, src/gtach/display/manager.py, src/gtach/app.py; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-b29cbd71-engine-off-state.md"
    - "ai/workspace/change/change-b29cbd71-engine-off-state.md"
    - "ai/workspace/design/design-e5f6a7b8-component_comm_obd_protocol.md section 6.3 (only this section is current)"
    - "ai/workspace/design/design-b8c9d0e1-component_display_manager.md section 5.4 (only this section is current)"
    - "tests/test_session_b_findings.py (stub transport for OBDProtocol to reuse)"
    - "CLAUDE.md section 4"
  constraints:
    - "CRITICAL: a 0100 reply of None never sets the silent timestamp; only a non-None reply without 4100 does."
    - "CRITICAL: every failure path of DisplayManager._engine_off returns False, so the display falls back to DISCONNECTED."
    - "CRITICAL: _link_lost, LINK_LOSS_TIMEOUT, LINK_RECOVERY_SAMPLES and the sample queue are unchanged; no synthetic message is queued."
    - "The re-check after silence during polling sends only 0100: no ATZ, no settle, no AT configuration command; _adapter_initialised is not changed by it."
    - "The initialisation path at connect, the DISCONNECTED screen and the A05 log rate limit are unchanged except as change-b29cbd71 states."
    - "The other sections of the two design documents describe older code; follow the source and the change document, not those sections."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to C of change-b29cbd71; add tests."
  requirements:
    functional:
      - "As in change-b29cbd71 proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access (the timestamp is a single attribute written by the protocol thread and read by the display thread)"
        - "Professional docstrings"

design:
  architecture: "Unchanged. The display reads protocol state through an injected callback, as for the transport."
  components:
    - name: "EDIT A"
      type: "module"
      purpose: "Silent-vehicle evidence and re-check in OBDProtocol."
      logic:
        - "_vehicle_silent_ts attribute; last_vehicle_silent_ts() accessor."
        - "One classification helper for a 0100 reply, used by _initialize_protocol and the re-check: 4100 -> answering (clear timestamp); non-None without 4100 -> silent (set timestamp, _report_no_vehicle); None -> _report_no_vehicle only, timestamp not set. The issue-146491ba lost-link branch stays ahead of it and also clears the timestamp."
        - "Clear the timestamp on a valid sample, when the loop finds the transport disconnected, and in _signal_stop."
        - "Poll loop: last-valid-sample time; after _RPM_SILENT_RECHECK_S (2.0) without one and with the transport connected, run the re-check loop (0100, classify, wait _INIT_RETRY_DELAY_S with wait_for_event and heartbeats) until 4100, disconnect or stop."
    - name: "EDIT B"
      type: "module"
      purpose: "Engine-off condition and screen in DisplayManager."
      logic:
        - "ENGINE_OFF_FRESHNESS_S = 15.0, ENGINE_OFF_TEXT = 'Engine off'; _vehicle_silent_callback and _frame_engine_off initialised early in __init__."
        - "_engine_off() per design-b8c9d0e1 section 5.4.1; set _frame_engine_off once per frame after _frame_link_lost."
        - "DISCONNECTED decision at the three sites becomes `_frame_link_lost and not _frame_engine_off`; view key includes _frame_engine_off; status indicator yellow when engine off."
        - "_draw_radial_mode: engine off draws 0 RPM and ENGINE_OFF_TEXT at the centre (font chosen so its width is 180 px or less), no numeric readout. Reset conditioning state and log INFO on entry; log INFO on exit."
    - name: "EDIT C"
      type: "module"
      purpose: "Wiring in app.py."
      logic:
        - "Both display construction sites: _vehicle_silent_callback = lambda returning self._obd.last_vehicle_silent_ts() when self._obd exists, else None."

error_handling:
  strategy: "Display side fails toward DISCONNECTED; protocol side unchanged."
  exceptions: []
  logging:
    level: "Re-check entry and resumption INFO; engine-off entry and exit INFO; existing A05 WARNING unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-b29cbd71 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Transport disconnects during the re-check wait."
    - "Stop requested during the re-check wait."
    - "Silent callback returns a timestamp exactly ENGINE_OFF_FRESHNESS_S old."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place; add tests/test_engine_off_state.py; one commit."
    - "Report ai/workspace/report/report-b29cbd71-engine-off-state.md: per EDIT, what changed; the font and measured width of ENGINE_OFF_TEXT; the time from last sample to the first silent timestamp in the mid-drive test; deviations; test results."
  files:
    - path: "src/gtach/comm/obd.py"
      content: "EDIT A"
    - path: "src/gtach/display/manager.py"
      content: "EDIT B"
    - path: "src/gtach/app.py"
      content: "EDIT C"
    - path: "tests/test_engine_off_state.py"
      content: "Tests"

success_criteria:
  - "A non-None 0100 reply without 4100 sets the silent timestamp; a None reply never does."
  - "After 2.0 s without a valid sample, the protocol re-checks with 0100 only and resumes polling on 4100."
  - "The display shows Engine off only with the transport connected and a timestamp no older than 15 s; otherwise DISCONNECTED as before."
  - "The DISCONNECTED Setup and Reset regions are not registered while Engine off is shown."
  - "git diff touches only the three source files and the new test module (plus the report)."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "last_vehicle_silent_ts"
        module: "gtach.comm.obd"
        class: "OBDProtocol"
      - name: "_engine_off"
        module: "gtach.display.manager"
        class: "DisplayManager"
    constants:
      - name: "_RPM_SILENT_RECHECK_S"
        module: "gtach.comm.obd"
        value: "2.0"
      - name: "ENGINE_OFF_FRESHNESS_S"
        module: "gtach.display.manager"
        value: "15.0"
      - name: "ENGINE_OFF_TEXT"
        module: "gtach.display.manager"
        value: "Engine off"

notes: "Model: Claude Opus 5.5, effort medium. No ultracode. Human verification: device check after merge (emulator engineoff, car, emulator stopped)."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial prompt implementing change-b29cbd71 iteration 1. Target profile claude_code. |
| 1.1 | 2026-11-12 | Executed by Claude Code. EDITS A to C applied; deviations are listed in report-b29cbd71. pytest and mypy pass. Closed and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
