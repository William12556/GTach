Created: 2026 August 12

# Prompt: Detect a Dead Link and Reconnect for the Life of the Process

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-9c2f41d8"
  task_type: "debug"
  source_ref: "change-9c2f41d8"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-9c2f41d8"
    change_iteration: 1

context:
  purpose: >
    Make GTach recover from losing an established OBD link. At present
    a read timeout leaves the transport reporting connected against a
    dead peer, so OBDProtocol polls a closed-at-the-far-end socket at
    ~1 Hz indefinitely (38 consecutive occurrences observed), and
    reconnect_indefinitely is never re-entered because its only two
    call sites are at startup in threads that return on first success.
  integration: >
    All three edits are in src/gtach/comm/transport.py. No other source
    file is modified. No new imports, no new dependencies.
  knowledge_references:
    - "ai/workspace/issues/issue-9c2f41d8-no-recovery-from-mid-session-link-loss.md"
    - "ai/workspace/change/change-9c2f41d8-link-loss-recovery.md"
  constraints:
    - "CRITICAL: do NOT call disconnect() to tear down a dead link, and do NOT set _shutdown anywhere outside disconnect(). disconnect() sets _shutdown at transport.py:228; reconnect_indefinitely loops on that same event at line 342 and waits on it at 349; nothing clears it. Reusing disconnect() here would permanently disable reconnection, while still passing any test that merely asserts the transport goes not-connected. This is the single most important constraint in this prompt."
    - "Do not modify disconnect(). It must continue to set _shutdown for the application-shutdown path."
    - "Do not modify src/gtach/comm/obd.py. Its inner loop already exits on `while self.transport.is_connected():` and already resets _adapter_initialised when it does. Making is_connected() truthful is the whole fix on that side."
    - "Do not modify src/gtach/app.py. Both transport-thread call sites already create a daemon thread registered with ThreadManager as 'transport' with a heartbeat binding; making reconnect_indefinitely long-lived means that thread simply never returns."
    - "Do not modify src/gtach/comm/rfcomm.py or src/gtach/core/watchdog.py. 'transport' must remain advisory-only."
    - "Do not clear _shutdown anywhere. It must stay monotonic."
    - "Use self._shutdown.wait(...) rather than time.sleep(...) for every wait in reconnect_indefinitely, so shutdown interrupts immediately."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: >
    Apply edits L, M and N to src/gtach/comm/transport.py, then add the
    unit tests in the testing section.
  requirements:
    functional:
      - "Five consecutive read timeouts drop the current link; any successful response resets the count."
      - "Dropping a link closes the handle and sets DISCONNECTED without setting _shutdown."
      - "reconnect_indefinitely does not return on a successful connect; it returns only when _shutdown is set."
      - "After a link drop, reconnect_indefinitely resumes retrying at the existing retry_delay."
      - "The heartbeat callable is invoked in both the connected and the retrying phase."
      - "disconnect() behaves exactly as before."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Link loss detected within approximately 5.4 s of the peer going silent"
      metric: "time"
    - target: "Shutdown while connected or retrying completes without waiting out a retry delay"
      metric: "time"

design:
  architecture: >
    The transport currently models whether a socket is open. It must
    model whether the peer is answering. DisplayManager._link_lost
    already reasons from data recency rather than socket state
    (issue-4d9e2f18), which is why the DISCONNECTED screen appeared
    correctly while the transport carried on regardless; this change is
    the transport-side counterpart of that same insight.
  components:
    - name: "EDIT L — consecutive read-timeout thresholding in send_command"
      type: "function"
      purpose: "Make is_connected() tell the truth when the peer stops answering."
      logic:
        - "Add a class-level constant on OBDTransport:  _MAX_CONSECUTIVE_TIMEOUTS: int = 5"
        - "Comment the value against the observed timings: a command timeout is 1.0 s and the observed failure cycled at ~1.07 s, so the threshold trips at ~5.4 s — above a single slow adapter response, below WatchdogMonitor's 15 s warning threshold."
        - "In __init__, add:  self._consecutive_timeouts = 0"
        - "In send_command, on the success path — immediately before `return response`, after the RX debug log — reset the counter to 0 under self._lock."
        - "In the `except self._TIMEOUT_ERRORS:` branch (currently transport.py:285-288), retain the existing warning, then under self._lock increment self._consecutive_timeouts and capture whether it has reached _MAX_CONSECUTIVE_TIMEOUTS."
        - "If the threshold is reached, log at ERROR — naming the count and the endpoint via self._describe() — then call self.drop_link() OUTSIDE the lock, and reset the counter to 0. Return None as before."
        - "drop_link takes _lock itself, so it must not be called while _lock is held. Capture the decision under the lock, act after releasing it."
        - "Do not alter the ordering of the except branches. _TIMEOUT_ERRORS must continue to precede _IO_ERRORS, socket.timeout being an OSError subclass."
    - name: "EDIT M — drop_link, a teardown that does not end the transport"
      type: "function"
      purpose: "Close the current link while leaving reconnection possible."
      logic:
        - "Add a public method `def drop_link(self) -> None:` positioned immediately after disconnect() so the two are read together."
        - "It takes self._lock, calls self._discard_handle_locked(), and sets self._state = TransportState.DISCONNECTED. It does NOT touch self._shutdown."
        - "Log at INFO that the link to self._describe() was dropped and that reconnection will be attempted."
        - "The docstring must state the distinction explicitly: disconnect() ends the transport's life and sets the shutdown event that reconnect_indefinitely loops on; drop_link() closes only the current link so the supervising loop can re-establish it. Cite issue-9c2f41d8."
        - "Make it safe to call when nothing is connected: _discard_handle_locked already tolerates a None handle."
    - name: "EDIT N — reconnect_indefinitely as a process-lifetime supervising loop"
      type: "function"
      purpose: "Resume retrying whenever the link drops, for as long as the process lives."
      logic:
        - "Retain the signature exactly: (self, retry_delay: float = 5.0, heartbeat: Optional[Callable[[], None]] = None) -> None."
        - "Retain the guarded heartbeat helper introduced by change-2ac1c602: every heartbeat invocation stays wrapped so a raising callback cannot break the loop."
        - "Restructure the body as: while not self._shutdown.is_set():  →  heartbeat; if self.connect(): enter a supervising inner wait; else log the existing retry warning and self._shutdown.wait(retry_delay)."
        - "The supervising inner wait is: while self.is_connected() and not self._shutdown.is_set(): heartbeat; self._shutdown.wait(1.0). On leaving it, if _shutdown is set the method returns; otherwise the link dropped and control falls through to the next outer iteration, which retries."
        - "A 1.0 s supervising poll is deliberate: it bounds how long after a drop_link the loop notices, and it keeps the 'transport' heartbeat flowing while connected, which the ThreadManager registration added by change-2ac1c602 requires."
        - "The method must NOT return on a successful connect. Its only return is _shutdown being set."
        - "Update the docstring: it supervises the link for the life of the process; it returns only on shutdown; a dropped link resumes retrying."

data_schema:
  entities: []

error_handling:
  strategy: >
    The supervising loop must survive anything a consumer or callback
    throws, and must never be the reason shutdown is delayed.
  exceptions:
    - exception: "Exception"
      condition: "The heartbeat callable raises."
      handling: "Existing behaviour retained: logged at DEBUG with exc_info=True; the loop continues."
    - exception: "self._TIMEOUT_ERRORS"
      condition: "A read times out in send_command."
      handling: "Warning as now; counter incremented; drop_link on reaching the threshold; return None."
    - exception: "self._IO_ERRORS"
      condition: "A socket error other than timeout."
      handling: "Unchanged. That branch already discards the handle and sets DISCONNECTED."
  logging:
    level: "ERROR for the threshold trip, INFO for drop_link"
    format: "Existing _LOG_FORMAT; no format change."

testing:
  unit_tests:
    - scenario: "Four consecutive read timeouts, then one successful response."
      expected: "drop_link is not called; _consecutive_timeouts is 0 afterwards."
    - scenario: "Five consecutive read timeouts."
      expected: "drop_link is called exactly once; is_connected() is False; an ERROR is logged."
    - scenario: "Three timeouts, one success, three more timeouts."
      expected: "drop_link is not called."
    - scenario: "Six consecutive timeouts."
      expected: "drop_link is called once, not twice: the counter resets when the threshold trips."
    - scenario: "drop_link on a connected transport."
      expected: "The handle is closed; _state is DISCONNECTED; _shutdown.is_set() is False."
    - scenario: "drop_link on a transport that is already disconnected."
      expected: "No exception."
    - scenario: "disconnect() on a connected transport."
      expected: "_shutdown.is_set() is True and _state is DISCONNECTED — unchanged from before this prompt."
    - scenario: "reconnect_indefinitely where connect() succeeds, then the link is dropped from another thread, then connect() succeeds again; _shutdown set after the second connect."
      expected: "The method does not return between the two connects; connect() was called twice; the method returns after _shutdown is set."
    - scenario: "reconnect_indefinitely with _shutdown set while connected."
      expected: "Returns within approximately one supervising poll, without waiting out retry_delay."
    - scenario: "reconnect_indefinitely with _shutdown set while retrying a failing connect."
      expected: "Returns promptly."
    - scenario: "reconnect_indefinitely with a heartbeat callable, across one connect, one drop and one reconnect."
      expected: "The callable is invoked during the connected phase AND during the retrying phase."
    - scenario: "reconnect_indefinitely with a heartbeat callable that always raises."
      expected: "The loop still proceeds; no exception propagates out."
    - scenario: "reconnect_indefinitely called with no heartbeat argument."
      expected: "No exception; behaviour otherwise as specified."
  edge_cases:
    - "drop_link called from the OBD thread while the transport thread is inside its supervising wait — the drop must be observed within one poll."
    - "The threshold trip occurring on the same call that would also have raised an IO error — the timeout branch is ordered first and must remain so."
    - "connect() succeeding and the link dropping again immediately, repeatedly — the loop must not busy-spin; each retry passes through _shutdown.wait(retry_delay)."
  validation:
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/comm/transport.py').read())\""

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing file in place. Do not create new modules."
  files:
    - path: "src/gtach/comm/transport.py"
      content: "EDIT L, EDIT M and EDIT N"
    - path: "tests/test_link_loss_recovery.py"
      content: "Unit tests for testing.unit_tests items 1-13"

success_criteria:
  - "OBDTransport defines _MAX_CONSECUTIVE_TIMEOUTS == 5 and initialises self._consecutive_timeouts = 0 in __init__."
  - "OBDTransport defines a public method drop_link."
  - "drop_link contains no reference to _shutdown."
  - "grep -n '_shutdown.set()' src/gtach/comm/transport.py returns exactly one match, inside disconnect()."
  - "disconnect() is byte-identical to its pre-change state."
  - "send_command's except branches remain ordered _TIMEOUT_ERRORS before _IO_ERRORS."
  - "send_command resets _consecutive_timeouts to 0 on the success path."
  - "reconnect_indefinitely contains no `return` that is reachable while _shutdown is unset."
  - "reconnect_indefinitely uses self._shutdown.wait(...) for every wait; grep -n 'time.sleep' src/gtach/comm/transport.py shows no occurrence introduced by this change."
  - "reconnect_indefinitely's signature is unchanged, including the heartbeat keyword parameter and its default of None."
  - "src/gtach/comm/obd.py, src/gtach/comm/rfcomm.py, src/gtach/app.py and src/gtach/core/watchdog.py are byte-identical to their pre-change state."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "transport"
        path: "src/gtach/comm/transport.py"
      - name: "obd"
        path: "src/gtach/comm/obd.py"
    classes:
      - name: "OBDTransport"
        module: "gtach.comm.transport"
      - name: "TransportState"
        module: "gtach.comm.transport"
      - name: "OBDProtocol"
        module: "gtach.comm.obd"
    functions:
      - name: "send_command"
        module: "gtach.comm.transport"
        signature: "(self, command: str, timeout: float = 2.0) -> Optional[str]"
      - name: "drop_link"
        module: "gtach.comm.transport"
        signature: "(self) -> None"
      - name: "disconnect"
        module: "gtach.comm.transport"
        signature: "(self) -> None"
      - name: "reconnect_indefinitely"
        module: "gtach.comm.transport"
        signature: "(self, retry_delay: float = 5.0, heartbeat: Optional[Callable[[], None]] = None) -> None"
      - name: "_discard_handle_locked"
        module: "gtach.comm.transport"
        signature: "(self) -> None"
      - name: "is_connected"
        module: "gtach.comm.transport"
        signature: "(self) -> bool"
    constants:
      - name: "_MAX_CONSECUTIVE_TIMEOUTS"
        module: "gtach.comm.transport"
        type: "int"

notes: >
  On-target verification is a human step. With GTach connected to the
  ELM327 emulator and debug enabled: stop the emulator and confirm that
  within ~5.4 s an ERROR records the link being dropped, that the
  "Timeout waiting for response" repetition stops, and that reconnect
  attempts begin at 5 s intervals. Restart the emulator and confirm
  GTach reconnects with no operator action, the adapter re-initialises,
  and RPM resumes. Then shut the application down while it is
  reconnecting and confirm shutdown completes promptly with no
  thread-join warning.

  Also confirm no "Heartbeat for unknown thread: transport" warning
  appears across a reconnect cycle.

  One condition is deliberately NOT addressed here. After the
  application was restarted following a link loss, every connect
  attempt failed with [Errno 16] Device or resource busy, 12 times in
  one log. Its mechanism is not established and it may prove to be a
  consequence of the abandoned socket that this change stops
  abandoning. Re-examine it after this change is deployed rather than
  attempting to address it in this prompt.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial prompt implementing change-9c2f41d8 iteration 1. Three edits in src/gtach/comm/transport.py plus one unit test module. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
