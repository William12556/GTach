Created: 2026 August 12

# Prompt: Close Failed Sockets and Report Why a Connect Failed

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
  iteration: 1
  coupled_docs:
    change_ref: "change-5e7a03c4"
    change_iteration: 1

context:
  purpose: >
    Make a connect failure say why it failed, and stop abandoning
    sockets on the failure path. On target, an adapter fault and a
    missing OBD dongle produce identical logs and an identical
    DISCONNECTED screen; establishing which it was took a full session
    of manual hcitool work to recover information that errno already
    carried.
  integration: >
    Three edits across three files: src/gtach/comm/rfcomm.py,
    src/gtach/comm/transport.py, src/gtach/display/manager.py. No new
    dependencies.
  knowledge_references:
    - "ai/workspace/issues/issue-5e7a03c4-connect-error-classification.md"
    - "ai/workspace/change/change-5e7a03c4-connect-error-classification.md"
  constraints:
    - "CRITICAL: this change REPORTS. It must not ACT on the host. Do not add any adapter reset, rfkill cycle, hciuart restart, kernel module reload, reboot, or any other recovery action. On target a manual `hciconfig hci0 down && hciconfig hci0 up` saw the down succeed and the up fail with ETIMEDOUT, leaving the controller unable to come back; automating that unattended in a vehicle is not acceptable and is excluded by the change document."
    - "Do not use subprocess, os.system, os.popen, or any shell invocation. Do not parse hcitool, hciconfig, btmgmt or rfkill output. errno and sysfs carry everything needed."
    - "Do not change the retry cadence. EBUSY continues to retry at the existing interval; this change reports the cause, it does not alter policy."
    - "Do not modify src/gtach/comm/obd.py, src/gtach/comm/serial_transport.py, src/gtach/comm/tcp_transport.py or src/gtach/core/watchdog.py."
    - "Do not modify reconnect_indefinitely, drop_link or disconnect. change-9c2f41d8 delivered those and they are correct."
    - "Do not alter the DISCONNECTED screen's button geometry, regions or callbacks. _register_disconnected_regions owns them and is out of scope."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply edits O, P and Q, then add the unit tests in the testing section."
  requirements:
    functional:
      - "A socket that fails to connect is closed before the exception propagates."
      - "A connect failure resolves to a named cause derived from errno."
      - "An unmapped errno falls back to the errno name rather than being discarded."
      - "Where errno alone cannot discriminate, an adapter probe distinguishes a missing controller from an unreachable peer."
      - "The cause is readable from the transport and shown on the DISCONNECTED screen."
      - "A successful connect clears the recorded cause."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "The adapter probe is a sysfs path check performed only on a connect failure, never in the data path"
      metric: "time"

design:
  architecture: >
    errno arrives at the first except handler and is currently
    discarded there. Capture it at that point, resolve it to a cause,
    and record the cause on the transport so that the log, the display
    and any future consumer read the same value. Controller presence
    comes from sysfs, mirroring PlatformDetector's existing probe of
    /sys/class/bluetooth (platform.py:706).
  components:
    - name: "EDIT O — src/gtach/comm/rfcomm.py: close the socket on failure"
      type: "function"
      purpose: "Stop abandoning a socket whose connect raised."
      logic:
        - "In _open, wrap the sock.connect(...) and the subsequent sock.settimeout(None) in try/except BaseException."
        - "In the handler: close the socket inside a nested try/except that swallows close errors, then `raise` to re-propagate the original exception unchanged."
        - "Use a bare `raise`, not `raise e`, so the traceback is preserved and OBDTransport.connect's existing _IO_ERRORS handling is unaffected."
        - "Catch BaseException rather than Exception so that a KeyboardInterrupt or a timeout delivered as BaseException still closes the socket."
        - "Do not change the success path: the socket is returned and ownership passes to connect() as now."
        - "Comment why: the socket is a local, and OBDTransport.connect's handler calls _discard_handle() against self._handle, which was never assigned — so nothing else closes it. An unclosed RFCOMM socket holds its ACL reference (issue-5e7a03c4)."
    - name: "EDIT P — src/gtach/comm/transport.py: classify by errno"
      type: "class"
      purpose: "Turn a discarded errno into a named cause."
      logic:
        - "Add `import errno as _errno` to the module imports."
        - "Add a module-level mapping _CONNECT_FAULT_CAUSES from errno value to a short lowercase cause string. Map at minimum: EBUSY -> 'bluetooth link busy — adapter may need reset'; ETIMEDOUT -> 'connection timed out'; EHOSTDOWN -> 'adapter not reachable'; EHOSTUNREACH -> 'adapter not reachable'; ENODEV -> 'no bluetooth controller'; ENETDOWN -> 'bluetooth controller down'; ECONNREFUSED -> 'connection refused by adapter'."
        - "Keep every string short enough to render on a 480x480 display: 40 characters or fewer."
        - "In OBDTransport.__init__, add self._last_failure_cause: Optional[str] = None."
        - "Add a read-only property `last_failure_cause` returning that value under self._lock."
        - "In connect()'s `except self._IO_ERRORS as e:` handler: resolve the cause via a new helper, store it under self._lock, and extend the existing logger.error call to include it. Retain the existing message content and the existing _discard_handle() and state transition; add to them, do not replace them."
        - "In connect()'s success path, clear self._last_failure_cause to None under self._lock, beside the existing _state assignment."
        - "Add a helper `_classify_connect_error(self, exc: OSError) -> str`. It reads getattr(exc, 'errno', None); returns the mapped string when present in _CONNECT_FAULT_CAUSES; otherwise returns the errno name via _errno.errorcode.get(code, ...) or, failing that, str(exc). It must not raise for any input, including errno None."
    - name: "EDIT Q — adapter probe and DISCONNECTED status line"
      type: "function"
      purpose: "Distinguish a missing controller from an unreachable peer, and show it."
      logic:
        - "In transport.py add a module-level `def _bluetooth_adapter_present() -> bool:`. It returns True if any entry exists under /sys/class/bluetooth, False if the directory exists and is empty, and True if the check cannot be performed at all — the conservative answer, so an unknown state is never reported as a hardware fault."
        - "Wrap the whole probe in try/except Exception returning True. It must never raise."
        - "Comment that PlatformDetector already probes /sys/class/bluetooth (platform.py:706), so this is a precedented pattern rather than a new dependency."
        - "In _classify_connect_error, after the errno mapping resolves: if the adapter is NOT present, override the cause with 'no bluetooth controller' regardless of errno. A missing controller is the more specific and more actionable fact."
        - "In src/gtach/display/manager.py, in the method that renders the DISCONNECTED screen (_render_disconnected, around manager.py:2269), draw the cause as a single short status line ABOVE the button column, using the existing typography helpers and palette."
        - "Obtain the cause without adding a hard dependency on the transport: use the same callback pattern already used for _link_connected_callback in app.py — add a _link_cause_callback attribute defaulting to None, render the line only when the callback is set and returns a non-empty string, and have app.py wire it alongside the existing _link_connected_callback assignments."
        - "The button column's top is 240 (see _register_disconnected_regions). Place the status line above that and below any existing heading; do not move the buttons."
        - "Render nothing when there is no cause, so the screen is unchanged from today when no connect has failed."

data_schema:
  entities:
    - name: "connect failure cause"
      attributes:
        - name: "cause"
          type: "Optional[str]"
          constraints: "40 characters or fewer; None when no connect has failed since the last success"
      validation:
        - "Never raises when resolved, for any errno including None."

error_handling:
  strategy: >
    Diagnostics must not become a new failure source. Every addition —
    the socket close, the errno lookup, the sysfs probe, the render —
    is guarded so that its failure degrades information rather than
    behaviour.
  exceptions:
    - exception: "BaseException"
      condition: "sock.connect raises in _open."
      handling: "Close the socket, swallowing any close error, then bare-raise the original."
    - exception: "Exception"
      condition: "The sysfs adapter probe fails for any reason."
      handling: "Return True — assume present. An unknown state must not be reported as a hardware fault."
    - exception: "Exception"
      condition: "Cause resolution encounters an unexpected exception object."
      handling: "Fall back to str(exc). _classify_connect_error must not raise."
    - exception: "Exception"
      condition: "The status line cannot be rendered."
      handling: "Caught by the existing render error handling in _render_disconnected; the screen must still draw its buttons."
  logging:
    level: "ERROR for the connect failure, as now"
    format: "Existing _LOG_FORMAT; the cause is appended to the existing message, not substituted for it."

testing:
  unit_tests:
    - scenario: "_open where sock.connect raises OSError."
      expected: "close() called exactly once on the socket; the original OSError propagates with its errno intact."
    - scenario: "_open where sock.connect raises and close() also raises."
      expected: "The original OSError still propagates; the close error is swallowed."
    - scenario: "_open where connect succeeds."
      expected: "close() not called; the socket is returned."
    - scenario: "_classify_connect_error with errno EBUSY, adapter present."
      expected: "The mapped busy-link string; 40 characters or fewer."
    - scenario: "_classify_connect_error with errno EHOSTDOWN, adapter present."
      expected: "The mapped unreachable-adapter string."
    - scenario: "_classify_connect_error with any errno, adapter ABSENT."
      expected: "'no bluetooth controller', overriding the errno mapping."
    - scenario: "_classify_connect_error with an unmapped errno, e.g. EPERM."
      expected: "The errno name is returned; no exception."
    - scenario: "_classify_connect_error with an OSError whose errno is None."
      expected: "No exception; a non-empty string is returned."
    - scenario: "_bluetooth_adapter_present where the sysfs path does not exist."
      expected: "Returns True — the conservative answer."
    - scenario: "_bluetooth_adapter_present where the directory exists and is empty."
      expected: "Returns False."
    - scenario: "connect() failing, then succeeding."
      expected: "last_failure_cause is a non-empty string after the failure and None after the success."
    - scenario: "_render_disconnected with _link_cause_callback unset."
      expected: "No status line is drawn; the screen is unchanged from before this change."
    - scenario: "_render_disconnected with _link_cause_callback returning a cause."
      expected: "The status line is drawn above the button column; the button rects are unchanged."
  edge_cases:
    - "A cause longer than the display width — strings are capped at 40 characters by construction; assert this in a test over the whole mapping."
    - "last_failure_cause read from the display thread while connect() writes it from the transport thread — both go through _lock."
    - "Repeated failures with the same errno — the cause is overwritten, not accumulated."
  validation:
    - "grep -rn 'subprocess\\|os.system\\|os.popen' src/gtach/comm/ src/gtach/display/manager.py returns no match introduced by this change."
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/comm/transport.py').read())\" and the same for rfcomm.py and manager.py."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing files in place. Do not create new modules."
  files:
    - path: "src/gtach/comm/rfcomm.py"
      content: "EDIT O"
    - path: "src/gtach/comm/transport.py"
      content: "EDIT P and the transport half of EDIT Q"
    - path: "src/gtach/display/manager.py"
      content: "The display half of EDIT Q"
    - path: "src/gtach/app.py"
      content: "Wire _link_cause_callback alongside the existing _link_connected_callback assignments. This is the ONLY permitted change to app.py."
    - path: "tests/test_connect_error_classification.py"
      content: "Unit tests for testing.unit_tests items 1-13"

success_criteria:
  - "RFCOMMTransport._open closes the socket on the failure path and re-raises with a bare `raise`."
  - "src/gtach/comm/transport.py defines _CONNECT_FAULT_CAUSES, _bluetooth_adapter_present and OBDTransport._classify_connect_error."
  - "Every value in _CONNECT_FAULT_CAUSES is 40 characters or fewer."
  - "OBDTransport exposes a read-only last_failure_cause property, set on connect failure and cleared to None on connect success."
  - "connect()'s existing logger.error message content, _discard_handle() call and state transition are all retained; the cause is added to the message, not substituted for it."
  - "_bluetooth_adapter_present returns True when the probe cannot be performed."
  - "grep -rn 'subprocess|os.system|os.popen|hcitool|hciconfig|btmgmt|rfkill' src/ returns no match."
  - "No code path performs any Bluetooth recovery action."
  - "reconnect_indefinitely, drop_link and disconnect are byte-identical to their pre-change state."
  - "_register_disconnected_regions is byte-identical to its pre-change state."
  - "src/gtach/comm/obd.py, serial_transport.py, tcp_transport.py and src/gtach/core/watchdog.py are byte-identical to their pre-change state."
  - "The only change to src/gtach/app.py is the _link_cause_callback wiring."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "rfcomm"
        path: "src/gtach/comm/rfcomm.py"
      - name: "transport"
        path: "src/gtach/comm/transport.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
    classes:
      - name: "RFCOMMTransport"
        module: "gtach.comm.rfcomm"
      - name: "OBDTransport"
        module: "gtach.comm.transport"
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "_open"
        module: "gtach.comm.rfcomm"
        signature: "(self) -> Optional[socket.socket]"
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
      - name: "_CONNECT_FAULT_CAUSES"
        module: "gtach.comm.transport"
        type: "dict"

notes: >
  On-target verification is a human step. With the controller healthy
  and the OBD peer absent, confirm the log and the DISCONNECTED screen
  report an unreachable peer. With the controller down, confirm both
  report an adapter fault, distinctly. Across several retry cycles
  against a failing connect, confirm /proc/<pid>/fd shows no growth in
  socket descriptors.

  Note that on gtach.local the controller is currently wedged:
  `hciconfig hci0 up` fails with ETIMEDOUT. Recovery is a host
  operation — restarting hciuart.service to re-attach the chip, or a
  reboot — and is deliberately not something this change attempts.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial prompt implementing change-5e7a03c4 iteration 1. Three edits plus one line of app.py wiring, and one unit test module. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
