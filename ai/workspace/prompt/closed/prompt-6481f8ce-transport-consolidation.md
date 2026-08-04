Created: 2026 August 04

# Prompt: Capture the Handle Under the Lock, Then Consolidate

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-6481f8ce"
  task_type: "debug"
  source_ref: "change-6481f8ce"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-6481f8ce"
    change_iteration: 1

context:
  purpose: >
    Each transport's send_command calls is_connected(), which reads the
    socket or serial handle under the lock and releases it, and then
    dereferences that handle outside the lock. A concurrent disconnect()
    sets it to None in between, so the call raises AttributeError rather
    than the OSError the surrounding handler catches, and the orderly
    reconnect does not happen. The same code exists three times, and the
    set of transport names exists four times.
  integration: >
    Six files: src/gtach/comm/rfcomm.py, comm/tcp_transport.py,
    comm/serial_transport.py, comm/transport.py, src/gtach/main.py and
    src/gtach/app.py. Executor is Claude Code; AEL is not used.

    PREREQUISITE — ai/task.md §7.5.5. The controlled reproduction of the
    race has not been carried out. It is this task's regression test and
    its acceptance criterion. Before Stage 1, write a test that drives
    disconnect() into the window between the handle capture and its use
    with explicit synchronisation — the interval is a few bytecodes and
    cannot be hit by sleeping — and confirm it raises AttributeError
    against the current code. If it does not discriminate, STOP and
    report: the mechanism is not what the analysis says.

    ORDERING IS DECIDED. ai/task.md §7.6.3 offers two orderings and
    change-6481f8ce takes the second: fix the race in all three
    subclasses first, refactor afterwards. Do not reverse this. A defect
    fixed during a refactor cannot be attributed to either.

    THREE STAGES, THREE COMMITS. Stage 1 is the defect. Stages 2 and 3
    are maintainability and may be abandoned without losing the fix.
  knowledge_references: []
  constraints:
    - "Modify only the six files named above."
    - "Do NOT change is_connected()'s signature or its return type. It is on the OBDTransport abstract interface (transport.py:92-99) and is called by OBDProtocol at comm/obd.py:79 and by reconnect_indefinitely at transport.py:119."
    - "Do NOT hold self._lock across the network write or the receive loop. That would serialise disconnect() behind an in-flight command for up to the command timeout — the UI-freeze class of problem change-2d545bf5 addressed."
    - "Do NOT modify comm/obd.py, comm/sim_transport.py, comm/pairing.py or comm/bluetooth.py."
    - "Do NOT change the 0.02 / 0.05 poll interval values at app.py:268. Only where the fast/slow classification is DEFINED moves."
    - "Do NOT change which transports are forced. simtcp is forced and simbt routes through setup; that asymmetry is deliberate per report §5.8 and must be preserved exactly."
    - "Do NOT alter reconnect_indefinitely (transport.py:111-122)."
    - "Do NOT begin Stage 2 until the §7.5.5 test passes against Stage 1 and failed before it."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Capture the handle under the lock and operate on the captured
    reference in all three transports. Then hoist the resulting common
    skeleton into OBDTransport. Then define the transport name set and
    its three classifications once in transport.py.
  requirements:
    functional:
      - "Each transport has a private _acquire_handle() returning the handle captured under self._lock."
      - "send_command and its receive loop use the captured reference, never self._sock or self._serial directly."
      - "A disconnect() concurrent with send_command produces OSError, handled by the existing handler, not AttributeError."
      - "is_connected keeps its signature and its behaviour."
      - "After Stage 2, connect, disconnect, send_command, is_connected and state are concrete on OBDTransport and each subclass supplies only _open, _close, _write and _read."
      - "Every transport's observable behaviour is unchanged."
      - "After Stage 3, TRANSPORT_NAMES, TRANSPORT_FORCED and TRANSPORT_FAST are defined in transport.py and are the only place the five names appear as literals."
      - "main.py's argparse choices, app.py's forced test and app.py's fast test all derive from them."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Neutral. One extra lock acquisition per command, against a command that blocks on I/O for milliseconds"
      metric: "time"

design:
  architecture: >
    A boolean read under a lock is stale the moment the lock is
    released. The object itself is not: a reference captured under the
    lock still names a real object, so operating on it fails the way the
    code already expects — a closed socket raises OSError — rather than
    the way it does not.
  components:
    - name: "RFCOMMTransport._acquire_handle / TCPTransport._acquire_handle"
      type: "function"
      purpose: "Return the socket captured under the lock."
      interface:
        outputs:
          type: "Optional[socket.socket]"
      logic:
        - "with self._lock: return self._sock"
    - name: "SerialTransport._acquire_handle"
      type: "function"
      purpose: "Return the serial port captured under the lock."
      logic:
        - "with self._lock: return self._serial"
    - name: "send_command (all three)"
      type: "function"
      purpose: "Operate on the captured reference."
      logic:
        - "handle = self._acquire_handle()"
        - "if handle is None: take the existing not-connected path unchanged."
        - "Use handle for the write and for every read in the loop."
        - "Leave the existing except clauses as they are — they are what should now catch the failure."
    - name: "OBDTransport (Stage 2)"
      type: "class"
      purpose: "Hold the skeleton once."
      logic:
        - "Make connect, disconnect, send_command, is_connected and state concrete."
        - "Add abstract _open() -> handle, _close(handle), _write(handle, data), _read(handle, n)."
    - name: "TRANSPORT_NAMES / TRANSPORT_FORCED / TRANSPORT_FAST (Stage 3)"
      type: "constants"
      purpose: "One definition of the name set and its classifications."
  dependencies:
    internal:
      - "OBDProtocol — comm/obd.py:79. Calls is_connected and send_command; contracts unchanged."
      - "SimTransport — dispatched at transport.py:145-147; dispatch preserved, internals untouched."
      - "change-2d545bf5 — landed; addressed the other side of the setup re-entry interaction."
    external:
      - "socket, pyserial — unchanged."

error_handling:
  strategy: >
    The aim is not to prevent the failure but to make it the failure the
    code already handles. A captured reference to a socket that is
    subsequently closed raises OSError; the existing handlers catch it,
    mark the transport disconnected and let reconnect_indefinitely do
    its work. AttributeError on a None does none of that.
  exceptions:
    - exception: "OSError / socket.error / serial.SerialException"
      condition: "The captured handle was closed by a concurrent disconnect."
      handling: "The existing handlers at rfcomm.py:122-124, tcp_transport.py:119-121 and serial_transport.py:124-126. Unchanged."
    - exception: "AttributeError"
      condition: "Should no longer be reachable from send_command."
      handling: "Not caught. If it occurs the fix is incomplete and it should surface."
  logging:
    level: "Unchanged"
    format: "Existing"

testing:
  unit_tests:
    - scenario: "THE ACCEPTANCE TEST. disconnect() forced between the handle capture and its use, in each of the three transports, with explicit synchronisation."
      expected: "OSError, handled, transport marked disconnected. The SAME test against the pre-change file raises AttributeError. Run it both ways and record both results — a test that passes against both files proves nothing."
    - scenario: "send_command with no connection at all."
      expected: "The existing not-connected path; unchanged."
    - scenario: "send_command on a healthy fake socket."
      expected: "The response; unchanged."
    - scenario: "A socket error raised mid-receive."
      expected: "Handled as today."
    - scenario: "disconnect() during the receive loop rather than before the write."
      expected: "OSError from the captured reference; handled."
    - scenario: "is_connected before and after the change."
      expected: "Same signature, same results for connected and disconnected states."
    - scenario: "Every public method of each transport, before and after Stage 2, against a fake socket and a fake serial port."
      expected: "Identical observable behaviour for all three."
    - scenario: "Instantiating OBDTransport directly after Stage 2."
      expected: "TypeError — it is still abstract."
    - scenario: "Each concrete transport after Stage 2."
      expected: "Implements _open, _close, _write and _read."
    - scenario: "main.py's argparse choices against TRANSPORT_NAMES."
      expected: "Equal."
    - scenario: "A sixth name appended to TRANSPORT_NAMES in a test."
      expected: "Accepted at the command line with no edit to main.py."
    - scenario: "The forced classification for each of tcp, serial, rfcomm, simtcp, simbt."
      expected: "tcp, serial, simtcp forced; rfcomm and simbt routed through setup. Assert each of the five individually."
    - scenario: "The fast classification for each of the five."
      expected: "simbt, simtcp, tcp resolve to 0.02; serial and rfcomm to 0.05."
    - scenario: "select_transport for each of the five names."
      expected: "The same class as before the change in every case."
  edge_cases:
    - "The handle captured, then disconnect, then reconnect: the captured reference names the OLD socket, now closed. OSError, handled, and the transport reconnects. Correct — do not attempt to detect and retry on the new handle inside send_command."
    - "SerialTransport's _close_serial checks is_open before closing (serial_transport.py:247). A captured reference to a closed port raises on write; confirm pyserial's exception type is caught by the existing handler and add it if not."
    - "The receive loops at rfcomm.py:101 and tcp_transport.py:97 call handle.recv inside a while loop with a timeout. Capture once before the loop, not per iteration — re-capturing per iteration would reintroduce the window."
    - "app.py:84's elif in Stage 3 is the complement of the forced set, not an independent list. Compute it rather than restating it, or the two can drift the way the four lists already have."
    - "SimTransport is returned for both simtcp and simbt (transport.py:145-147) but they are classified differently for forcing. That is not an inconsistency; it is the pairing-simulation design and report §5.8 confirms it is intentional."
  validation:
    - "grep confirms self._sock and self._serial are not dereferenced in send_command or its receive loop."
    - "git diff confirms comm/obd.py and comm/sim_transport.py are unmodified."
    - "grep confirms the five transport names appear as literals only in transport.py after Stage 3."

deliverable:
  format_requirements:
    - "Three commits, in stage order. Do not combine them."
    - "Edit the six files in place. Create no new file, except the test module the prerequisite calls for."
  files:
    - path: "src/gtach/comm/rfcomm.py"
      content: |
        STAGE 1. Add above send_command:

            def _acquire_handle(self):
                """Return the socket captured under the lock.

                is_connected() reads self._sock under the lock and
                releases it, so a caller acting on its result is acting
                on a stale answer: a concurrent disconnect() sets
                self._sock to None and the subsequent call raises
                AttributeError instead of the OSError the handler below
                expects (core review §5.3). Capturing the reference
                means a closed socket fails the way the code already
                handles.

                Returns:
                    The socket, or None if not connected.
                """
                with self._lock:
                    return self._sock

        In send_command (rfcomm.py:75-128):

          - replace the is_connected() check at line 86 with:

                handle = self._acquire_handle()
                if handle is None:
                    <the existing not-connected body, unchanged>

          - line 93: self._sock.sendall(...)  -> handle.sendall(...)
          - line 96: self._sock.settimeout(...) -> handle.settimeout(...)
          - line 101: self._sock.recv(1024)  -> handle.recv(1024)

        Capture ONCE, before the receive loop. Do not call
        _acquire_handle inside the loop.

        Leave the except clauses at rfcomm.py:104-124 exactly as they
        are. They are what should now catch this.

        Leave connect, disconnect, is_connected, state and _close_socket
        unchanged in Stage 1.
    - path: "src/gtach/comm/tcp_transport.py"
      content: |
        STAGE 1. The same edit, at tcp_transport.py:70-124:

          - _acquire_handle returning self._sock under the lock;
          - the is_connected check at line 81 replaced by the capture;
          - line 89 sendall, line 92 settimeout and line 97 recv on the
            captured handle.

        Same comment, same constraints. Leave the handlers alone.
    - path: "src/gtach/comm/serial_transport.py"
      content: |
        STAGE 1. The same edit, at serial_transport.py:91-129, against
        self._serial:

          - _acquire_handle returning self._serial under the lock;
          - the is_connected check at line 102 replaced by the capture;
          - line 109 write, line 112 timeout assignment and line 115
            read_until on the captured handle.

        pyserial raises SerialException rather than OSError on a closed
        port. Confirm the existing handler at serial_transport.py:124-126
        catches it; if it catches only OSError, widen it to include
        serial.SerialException. State in the commit message if you had
        to.
    - path: "src/gtach/comm/transport.py"
      content: |
        STAGE 2 — after Stage 1's test passes.

        Make concrete on OBDTransport: connect, disconnect,
        send_command, is_connected and state, using the now-identical
        logic from the three subclasses. Add abstract:

            @abstractmethod
            def _open(self): ...
            @abstractmethod
            def _close(self, handle) -> None: ...
            @abstractmethod
            def _write(self, handle, data: bytes) -> None: ...
            @abstractmethod
            def _read(self, handle, n: int) -> bytes: ...

        The base send_command keeps the capture-then-use discipline
        Stage 1 established — that is the whole point of doing Stage 1
        first.

        Each subclass then retains only _open, _close, _write, _read and
        its own extras (SerialTransport._discover_port and _probe_port).

        STAGE 3 — the name set. Add near the top of transport.py:

            # The transport name set and its classifications, defined
            # once. Previously maintained in four places — main.py's
            # argparse choices, app.py's forced test, app.py's fast-poll
            # test and select_transport below — with an omission in any
            # one of them changing behaviour silently rather than
            # raising (core review §5.8).
            TRANSPORT_NAMES = ('tcp', 'serial', 'rfcomm', 'simtcp', 'simbt')

            # Forced transports skip setup mode. simtcp is forced while
            # simbt routes through setup: that asymmetry is deliberate
            # and serves the pairing-simulation design. Do not
            # 'correct' it.
            TRANSPORT_FORCED = ('tcp', 'serial', 'simtcp')

            # Fast transports poll at 0.02 s rather than 0.05 s.
            TRANSPORT_FAST = ('simbt', 'simtcp', 'tcp')

        Have select_transport's dispatch read from TRANSPORT_NAMES where
        it enumerates, keeping its per-name construction as it is.
    - path: "src/gtach/main.py"
      content: |
        STAGE 3. At main.py:72:

            parser.add_argument('--transport', choices=['tcp', 'serial', 'rfcomm', 'simtcp', 'simbt'], default=None)

        becomes:

            parser.add_argument('--transport',
                                choices=list(TRANSPORT_NAMES),
                                default=None)

        with TRANSPORT_NAMES imported from .comm.transport. Check the
        existing import block and follow its style; if importing
        comm.transport at module scope in main.py creates a cycle,
        import inside parse_arguments and say so in the commit message.

        Change nothing else in this file.
    - path: "src/gtach/app.py"
      content: |
        STAGE 3. Two sites.

        At app.py:80:

            transport_forced = transport_arg in ('tcp', 'serial', 'simtcp')

        becomes:

            transport_forced = transport_arg in TRANSPORT_FORCED

        At app.py:84:

            elif transport_arg in ('simbt', 'rfcomm'):

        becomes the computed complement, so the two cannot drift:

            elif transport_arg in TRANSPORT_NAMES and transport_arg not in TRANSPORT_FORCED:

        At app.py:267:

            _fast_transports = ('simbt', 'simtcp', 'tcp')
            _poll_interval = 0.02 if transport_arg in _fast_transports else 0.05

        becomes:

            _poll_interval = 0.02 if transport_arg in TRANSPORT_FAST else 0.05

        Keep the 0.02 and 0.05 values exactly. Change nothing else.

success_criteria:
  - "python -m py_compile on all six files passes."
  - "pytest tests/ passes with no new failures."
  - "The §7.5.5 reproduction fails with AttributeError against the pre-change files and passes after Stage 1, in all three transports. Both results recorded."
  - "self._sock and self._serial are not dereferenced in send_command or its receive loop in any transport."
  - "is_connected's signature and behaviour are unchanged in all three."
  - "self._lock is not held across a network write or a receive loop."
  - "After Stage 2, connect/disconnect/send_command/is_connected/state appear once, on OBDTransport."
  - "After Stage 2, every transport's observable behaviour against fakes is identical to before."
  - "After Stage 3, the five transport names appear as literals only in transport.py."
  - "The forced classification is unchanged for all five names, asserted individually."
  - "The fast classification is unchanged for all five names, asserted individually."
  - "select_transport returns the same class for each of the five names."
  - "src/gtach/comm/obd.py and src/gtach/comm/sim_transport.py are byte-identical to their current text."
  - "The 0.02 and 0.05 poll interval values are unchanged."
  - "No file other than the six named above is modified, apart from the added test module."

element_registry:
  source: ""
  entries:
    modules:
      - name: "rfcomm"
        path: "src/gtach/comm/rfcomm.py"
      - name: "tcp_transport"
        path: "src/gtach/comm/tcp_transport.py"
      - name: "serial_transport"
        path: "src/gtach/comm/serial_transport.py"
      - name: "transport"
        path: "src/gtach/comm/transport.py"
      - name: "main"
        path: "src/gtach/main.py"
      - name: "app"
        path: "src/gtach/app.py"
    classes:
      - name: "OBDTransport"
        module: "gtach.comm.transport"
      - name: "RFCOMMTransport"
        module: "gtach.comm.rfcomm"
      - name: "TCPTransport"
        module: "gtach.comm.tcp_transport"
      - name: "SerialTransport"
        module: "gtach.comm.serial_transport"
    functions:
      - name: "_acquire_handle"
        module: "gtach.comm.rfcomm"
        signature: "_acquire_handle(self) -> Optional[socket.socket]"
      - name: "send_command"
        module: "gtach.comm.rfcomm"
        signature: "send_command(self, command: str, timeout: float = 2.0) -> Optional[str]"
      - name: "select_transport"
        module: "gtach.comm.transport"
        signature: "select_transport(platform_type: PlatformType, args: argparse.Namespace) -> OBDTransport"
      - name: "parse_arguments"
        module: "gtach.main"
        signature: "parse_arguments()"
    constants:
      - name: "TRANSPORT_NAMES"
        module: "gtach.comm.transport"
      - name: "TRANSPORT_FORCED"
        module: "gtach.comm.transport"
      - name: "TRANSPORT_FAST"
        module: "gtach.comm.transport"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-6481f8ce-transport-consolidation.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  Do the §7.5.5 reproduction first and run it against the UNCHANGED
  files. A concurrency test that has never failed is not evidence of
  anything, and this is the one task in the set where that distinction
  is the whole result. If the test cannot be made to fail against the
  current code, the analysis is wrong and the rest of this prompt should
  not be executed.

  The reproduction needs explicit synchronisation, not sleeps. The
  window between the capture and the use is a few bytecodes wide. Hook
  the point between them — patch _acquire_handle to signal an event and
  wait on another before returning — and drive disconnect() from the
  second thread in that interval. The same technique was used
  successfully for change-1143427b's deadlock reproduction; see its
  verification block for the pattern.

  Stages 2 and 3 are optional in the sense that matters: if either
  proves larger than expected, land Stage 1 and report. The defect is
  what this triple exists to fix; the rest is why it was expensive.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-6481f8ce. |

---

Copyright (c) 2026 William Watson. MIT License.
