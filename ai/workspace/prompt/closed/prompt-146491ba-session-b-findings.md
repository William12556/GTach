# Prompt: Session B Findings — Reset Retry, Notice Text, Lost-Link Record

Created: 2026 November 12

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-146491ba"
  task_type: "bugfix"
  source_ref: "change-146491ba"
  target_profile: "claude_code"
  date: "2026-11-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-146491ba"
    change_iteration: 1

context:
  purpose: "Fix three findings of device session B: the post-pairing OBD check fails on a connection reset, the fallback notice is truncated, and a lost link during initialisation is logged as a silent vehicle."
  integration: "src/gtach/comm/transport.py, src/gtach/comm/obd.py, src/gtach/display/setup_components/bluetooth/interface.py; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-146491ba-session-b-findings.md"
    - "ai/workspace/change/change-146491ba-session-b-findings.md"
    - "ai/workspace/prompt/closed/prompt-d26ca557-obd-verify-ebusy-after-pairing.md (the busy retry this extends)"
    - "tests/test_obd_verify_busy_retry.py (scripted RFCOMM stand-in to reuse)"
    - "CLAUDE.md section 4"
  constraints:
    - "CRITICAL: transport.py gains only LINK_RESET_CAUSE, its comment and the ECONNRESET mapping entry."
    - "CRITICAL: the verify retry bound and delay are unchanged (_VERIFY_BUSY_ATTEMPTS = 3, _VERIFY_BUSY_RETRY_DELAY_S = 1.0); only the set of retried causes grows."
    - "EDIT C changes only the handling of a None 0100 reply with the transport disconnected; every other path of _initialize_protocol is unchanged."
    - "Do not change any DEVICE_LIST text other than FALLBACK_LIST_TEXT; a failing width case for another text is marked xfail with the measured width and reported."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to C of change-146491ba; add tests."
  requirements:
    functional:
      - "As in change-146491ba proposed_solution."
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
      type: "module"
      purpose: "Retry the post-pairing connect on a reset."
      logic:
        - "transport.py: LINK_RESET_CAUSE = 'connection reset by adapter' beside LINK_BUSY_CAUSE; _errno.ECONNRESET: LINK_RESET_CAUSE in _CONNECT_FAULT_CAUSES."
        - "interface.py: import LINK_RESET_CAUSE; a module or class tuple of retried causes (LINK_BUSY_CAUSE, LINK_RESET_CAUSE); the loop condition tests membership; the INFO record reads f'OBD verify: {cause}, retrying (attempt {n}/{N})'."
    - name: "EDIT B"
      type: "module"
      purpose: "Readable fallback notice."
      logic:
        - "Measure 'No ELM327 found' with get_label_small_font() under SDL_VIDEODRIVER=dummy. If <= 220 px, use it; otherwise use 'No ELM327'. State the measured widths in the report."
    - name: "EDIT C"
      type: "module"
      purpose: "No silent-vehicle report for a lost link."
      logic:
        - "In _initialize_protocol, after the 0100 send: if response is None and not self.transport.is_connected(): self.logger.debug('Link lost during initialisation'); return False. Place it before the existing 4100 check."

error_handling:
  strategy: "Unchanged."
  exceptions: []
  logging:
    level: "Retry record INFO (cause named); lost link during initialisation DEBUG"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-146491ba testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Reset then busy then success within three attempts."
    - "The transport disconnects between the ATSP0 send and the 0100 send."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place; extend tests/test_obd_verify_busy_retry.py for EDIT A; add tests/test_session_b_findings.py for EDITS B and C; one commit."
    - "Report ai/workspace/report/report-146491ba-session-b-findings.md: per EDIT, what changed; the measured text widths and the text chosen; any xfail case; deviations; test results."
  files:
    - path: "src/gtach/comm/transport.py"
      content: "EDIT A(1)"
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "EDIT A(2), EDIT B"
    - path: "src/gtach/comm/obd.py"
      content: "EDIT C"
    - path: "tests/test_obd_verify_busy_retry.py, tests/test_session_b_findings.py"
      content: "Tests"

success_criteria:
  - "verify_obd_connection retries LINK_BUSY_CAUSE and LINK_RESET_CAUSE only, at most three attempts, 1.0 s apart."
  - "LINK_RESET_CAUSE == _CONNECT_FAULT_CAUSES[errno.ECONNRESET] and is 40 characters or fewer."
  - "FALLBACK_LIST_TEXT renders at 220 px or less in get_label_small_font()."
  - "A None 0100 reply with the transport disconnected produces no WARNING and leaves _vehicle_silent unchanged."
  - "git diff touches only the three source files and the two test modules (plus the report)."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants:
      - name: "LINK_RESET_CAUSE"
        module: "gtach.comm.transport"
        value: "connection reset by adapter"

notes: "Model: Claude Opus 5.5, effort medium. No ultracode. Human verification: device check after merge (three setups with the emulator; fallback notice)."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial prompt implementing change-146491ba iteration 1. Target profile claude_code. |
| 1.1 | 2026-11-12 | Executed by Claude Code (33a40e3). EDITS A to C applied; deviations listed in report-146491ba. pytest and mypy pass. Closed and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
