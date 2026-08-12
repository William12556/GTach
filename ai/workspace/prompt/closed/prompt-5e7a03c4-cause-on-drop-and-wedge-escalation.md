Created: 2026 August 12

# Prompt: Set a Cause on Link Drop and Escalate to a Wedge Diagnosis

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-5e7a03c4"
  task_type: "debug"
  source_ref: "change-5e7a03c4"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 2
  coupled_docs:
    change_ref: "change-5e7a03c4"
    change_iteration: 2

context:
  purpose: >
    Close three gaps in iteration 1's delivery. The DISCONNECTED screen
    has no explanation in the one failure mode change-9c2f41d8 exists
    to handle, because only connect() sets a cause. The adapter probe
    detects an absent controller but not a wedged one. And an
    errno-less timeout produces "timed out (timed out)".
  integration: >
    All three edits are in src/gtach/comm/transport.py. No other file
    is modified. No new dependencies.
  knowledge_references:
    - "ai/workspace/issues/issue-5e7a03c4-connect-error-classification.md"
    - "ai/workspace/change/change-5e7a03c4-connect-error-classification.md"
    - "ai/workspace/prompt/closed/prompt-5e7a03c4-connect-error-classification.md"
  constraints:
    - "CRITICAL: this remains a REPORTING change. Do not add any adapter reset, rfkill cycle, hciuart restart, module reload or reboot. Do not use subprocess, os.system, os.popen, or invoke hcitool/hciconfig/btmgmt/rfkill. An operator-initiated reset button is being raised separately and is not part of this prompt."
    - "Do not modify src/gtach/display/manager.py, src/gtach/app.py, src/gtach/comm/rfcomm.py, src/gtach/comm/obd.py or src/gtach/core/watchdog.py."
    - "Do not modify disconnect(), reconnect_indefinitely, or the send_command consecutive-TIMEOUT logic delivered by change-9c2f41d8. EDIT S adds a separate consecutive-CONNECT-FAILURE counter; the two must not be conflated."
    - "Do not change the retry cadence or the _MAX_CONSECUTIVE_TIMEOUTS value."
    - "Do not read the HCI_UP flag by ioctl. It was considered and rejected on simplicity grounds; consecutive-failure escalation is the chosen approach."
    - "Every cause string must remain 40 characters or fewer, to render on the 480x480 display."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply edits R, S and T, then add the unit tests in the testing section."
  requirements:
    functional:
      - "A link dropped for sustained silence records a cause naming that condition."
      - "A successful connect clears the cause and both failure counters."
      - "Six consecutive connect failures with the adapter present escalate the cause to a wedge diagnosis naming a reset."
      - "The cause suffix is omitted from the connect-failure log when it duplicates the exception text."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance: []

design:
  architecture: >
    The transport already owns the cause; iteration 1 only populated it
    from one of the two paths that ends a link. This completes the
    other, and adds a second-order signal — persistence — that no
    single errno can carry.
  components:
    - name: "EDIT R — set a cause in drop_link"
      type: "function"
      purpose: "Explain a link torn down for silence, not only one that failed to open."
      logic:
        - "Add a module-level constant:  _SILENT_LINK_CAUSE = 'adapter stopped responding'  (40 characters or fewer)."
        - "Change drop_link's signature to `def drop_link(self, cause: Optional[str] = None) -> None:`. Both existing call sites pass nothing and must continue to work unchanged."
        - "Inside the existing `with self._lock:` block, alongside the existing _state assignment, set self._last_failure_cause = cause or _SILENT_LINK_CAUSE."
        - "Do not add a second lock acquisition and do not move the existing _discard_handle_locked() call."
        - "Update the docstring: drop_link now records why the link was dropped, so the DISCONNECTED screen has an explanation in the mid-session case; cite issue-5e7a03c4 iteration 2."
        - "The optional argument exists so a future caller with better information can supply its own cause without changing call sites. Do not add such a caller in this prompt."
    - name: "EDIT S — consecutive connect-failure escalation"
      type: "class"
      purpose: "Report a probable controller wedge, which no single errno identifies."
      logic:
        - "Add a class-level constant:  _MAX_CONSECUTIVE_CONNECT_FAILURES: int = 6"
        - "Comment the value: at the 5.0 s retry interval this is ~30 s of sustained failure — above any transient, below the point an operator would reasonably keep waiting."
        - "Add a module-level constant:  _WEDGED_LINK_CAUSE = 'bluetooth wedged - reset required'  (40 characters or fewer)."
        - "In __init__, add self._consecutive_connect_failures = 0."
        - "This counter is SEPARATE from _consecutive_timeouts, which change-9c2f41d8 uses for read timeouts on an established link. Do not merge them; they count different events with different thresholds."
        - "In connect()'s success path, reset self._consecutive_connect_failures to 0 under _lock, beside the existing _last_failure_cause = None."
        - "In connect()'s `except self._IO_ERRORS as e:` handler, under _lock, increment the counter and capture its value."
        - "Resolve the cause as now via _classify_connect_error, then: if the captured count is at or above _MAX_CONSECUTIVE_CONNECT_FAILURES AND _bluetooth_adapter_present() is True AND the resolved cause is not already 'no bluetooth controller', override the cause with _WEDGED_LINK_CAUSE."
        - "The adapter-present condition matters: if the controller is genuinely absent, that is the more specific fact and must not be masked by a wedge diagnosis."
        - "Do NOT reset the counter when the threshold is crossed. Unlike the read-timeout counter, this one must latch: the condition persists until a connect succeeds, and the cause should keep reporting it."
        - "Call _bluetooth_adapter_present outside the lock; it performs filesystem access."
    - name: "EDIT T — suppress the duplicated suffix"
      type: "function"
      purpose: "Stop emitting 'timed out (timed out)'."
      logic:
        - "In connect()'s _IO_ERRORS handler, the existing logger.error already interpolates the exception. Append the cause in parentheses only when `cause != str(e)`."
        - "When they are equal, log exactly the iteration-0 message with no parenthesised suffix."
        - "This is presentation only: self._last_failure_cause is still set to the resolved cause in both branches, because the display has no other source for it."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged from iteration 1. Every addition is guarded so a diagnostic cannot become a failure source."
  exceptions:
    - exception: "Exception"
      condition: "_bluetooth_adapter_present fails during escalation."
      handling: "It already returns True on any internal failure. No additional handling; the escalation simply proceeds on the conservative assumption that an adapter is present."
    - exception: "Exception"
      condition: "Anything unexpected while resolving or recording a cause."
      handling: "_classify_connect_error already returns 'unknown connection failure' rather than raising. Preserve that property."
  logging:
    level: "ERROR for connect failure, INFO for drop_link — both as now"
    format: "Existing _LOG_FORMAT; no format change."

testing:
  unit_tests:
    - scenario: "drop_link() with no argument on a connected transport."
      expected: "last_failure_cause == _SILENT_LINK_CAUSE; _state is DISCONNECTED; _shutdown is NOT set."
    - scenario: "drop_link('custom reason')."
      expected: "last_failure_cause == 'custom reason'."
    - scenario: "drop_link() called from the two existing call sites' signatures, i.e. with no arguments."
      expected: "No TypeError; behaviour as above."
    - scenario: "Five consecutive connect failures with EBUSY, adapter present."
      expected: "last_failure_cause is the EBUSY mapping, NOT the wedge cause."
    - scenario: "Six consecutive connect failures with EBUSY, adapter present."
      expected: "last_failure_cause == _WEDGED_LINK_CAUSE."
    - scenario: "Eight consecutive connect failures."
      expected: "last_failure_cause remains _WEDGED_LINK_CAUSE — the counter latches and is not reset by crossing the threshold."
    - scenario: "Six consecutive connect failures with the adapter ABSENT."
      expected: "last_failure_cause == 'no bluetooth controller'; the wedge cause does not mask it."
    - scenario: "Five failures, one success, then five more failures."
      expected: "No escalation: the success reset the counter."
    - scenario: "Connect succeeds after failures."
      expected: "last_failure_cause is None and _consecutive_connect_failures is 0."
    - scenario: "Read timeouts on an established link reaching _MAX_CONSECUTIVE_TIMEOUTS."
      expected: "drop_link is called as change-9c2f41d8 specified; _consecutive_connect_failures is unaffected. The two counters are independent."
    - scenario: "connect() failing with socket.timeout, whose errno is None."
      expected: "The log message contains no parenthesised suffix; last_failure_cause is still set to a non-empty string."
    - scenario: "connect() failing with EBUSY."
      expected: "The log message DOES carry the parenthesised cause, the cause differing from str(e)."
    - scenario: "Every value in _CONNECT_FAULT_CAUSES plus _SILENT_LINK_CAUSE and _WEDGED_LINK_CAUSE."
      expected: "All are 40 characters or fewer."
  edge_cases:
    - "drop_link called when already disconnected — must not raise and must still record the cause."
    - "A wedge escalation followed by a successful connect — the cause must clear, not persist."
    - "The adapter becoming absent partway through a failure run — the absent-controller cause must win from that point."
  validation:
    - "grep -rn 'subprocess|os.system|os.popen|hcitool|hciconfig|btmgmt|rfkill|ioctl' src/ returns no match."
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/comm/transport.py').read())\""

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing file in place. Do not create new modules."
  files:
    - path: "src/gtach/comm/transport.py"
      content: "EDIT R, EDIT S and EDIT T"
    - path: "tests/test_connect_error_classification.py"
      content: "Extend with unit tests for testing.unit_tests items 1-13. Existing tests must continue to pass unmodified."

success_criteria:
  - "drop_link's signature is (self, cause: Optional[str] = None) -> None and both existing no-argument call sites still work."
  - "drop_link sets _last_failure_cause inside its existing single _lock block; the file contains no second lock acquisition in that method."
  - "drop_link still contains no reference to _shutdown."
  - "OBDTransport defines _MAX_CONSECUTIVE_CONNECT_FAILURES == 6 and initialises _consecutive_connect_failures = 0."
  - "_consecutive_connect_failures and _consecutive_timeouts are distinct attributes; neither is assigned from the other."
  - "The wedge cause is not applied when _bluetooth_adapter_present() is False."
  - "The connect-failure counter is NOT reset on crossing its threshold; it is reset only on a successful connect."
  - "connect()'s log appends the parenthesised cause only when it differs from str(e)."
  - "_SILENT_LINK_CAUSE, _WEDGED_LINK_CAUSE and every value in _CONNECT_FAULT_CAUSES are 40 characters or fewer."
  - "disconnect(), reconnect_indefinitely, send_command's timeout handling, and _MAX_CONSECUTIVE_TIMEOUTS are unchanged."
  - "src/gtach/display/manager.py, src/gtach/app.py, src/gtach/comm/rfcomm.py, src/gtach/comm/obd.py and src/gtach/core/watchdog.py are byte-identical to their pre-change state."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "transport"
        path: "src/gtach/comm/transport.py"
    classes:
      - name: "OBDTransport"
        module: "gtach.comm.transport"
    functions:
      - name: "drop_link"
        module: "gtach.comm.transport"
        signature: "(self, cause: Optional[str] = None) -> None"
      - name: "connect"
        module: "gtach.comm.transport"
        signature: "(self) -> bool"
      - name: "_classify_connect_error"
        module: "gtach.comm.transport"
        signature: "(self, exc: OSError) -> str"
      - name: "_bluetooth_adapter_present"
        module: "gtach.comm.transport"
        signature: "() -> bool"
      - name: "last_failure_cause"
        module: "gtach.comm.transport"
        signature: "(self) -> Optional[str]"
    constants:
      - name: "_SILENT_LINK_CAUSE"
        module: "gtach.comm.transport"
        type: "str"
      - name: "_WEDGED_LINK_CAUSE"
        module: "gtach.comm.transport"
        type: "str"
      - name: "_MAX_CONSECUTIVE_CONNECT_FAILURES"
        module: "gtach.comm.transport"
        type: "int"

notes: >
  On-target verification is a human step. With the emulator running,
  stop it mid-session and confirm the DISCONNECTED screen now shows a
  cause naming that the adapter stopped responding, where before it
  showed none. Leave GTach failing to connect for ~30 s and confirm the
  cause escalates to the wedge diagnosis. Restore the link and confirm
  the cause clears.

  Two things remain out of this prompt. The DISCONNECTED screen
  redesign — removing Simulate, adding the retry-countdown arc — is a
  separate triple. An operator-initiated Bluetooth reset button is a
  third, and is blocked until the recovery command that actually works
  on this hardware is established: `hciconfig hci0 down && up` was
  tried on target and left the controller unable to come back.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Prompt iteration 2 for change-5e7a03c4 iteration 2. Cause set in drop_link, consecutive connect-failure escalation to a wedge diagnosis, and suppression of the duplicated cause suffix. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
