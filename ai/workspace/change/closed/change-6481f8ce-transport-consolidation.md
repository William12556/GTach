Created: 2026 August 04

# Change: Fix the Race First, Then Remove the Reason It Had to Be Fixed Three Times

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-6481f8ce"
  title: "Three stages: each transport captures its handle under the lock and uses the captured reference; the common connect/disconnect/send_command skeleton is hoisted into OBDTransport; and the transport name set with its three classifications is defined once in transport.py"
  date: "2026-08-04"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-6481f8ce"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-6481f8ce"
  description: >
    Resolves issue-6481f8ce. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 findings
    §5.3, §4.3 and §5.8 with §7.0 recommendation #7. Ordering decision
    required by ai/task.md §7.6.3. Task list reference ai/task.md
    §7.4.5.

scope:
  summary: >
    A live concurrency defect and two maintainability findings that
    explain why it is expensive. Staged so the defect is fixed before
    anything is restructured.
  affected_components:
    - name: "RFCOMMTransport"
      file_path: "src/gtach/comm/rfcomm.py"
      change_type: "modify"
    - name: "TCPTransport"
      file_path: "src/gtach/comm/tcp_transport.py"
      change_type: "modify"
    - name: "SerialTransport"
      file_path: "src/gtach/comm/serial_transport.py"
      change_type: "modify"
    - name: "OBDTransport"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "TRANSPORT_NAMES"
      file_path: "src/gtach/comm/transport.py"
      change_type: "add"
    - name: "parse_arguments"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "GTachApplication.start"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "SimTransport (comm/sim_transport.py). It is dispatched by name from transport.py:145-147 and its dispatch is preserved; its internals are not touched."
    - "OBDProtocol (comm/obd.py). It calls send_command and is_connected; its behaviour must be unchanged."
    - "The reconnect_indefinitely loop at transport.py:111-122. Unmodified."
    - "app.py._re_enter_setup's shutdown sequence. change-2d545bf5 addressed §5.9 there; this change alters what happens on the other thread, not that one."
    - "The OBD poll interval VALUES at app.py:268 (0.02 / 0.05). Only where the classification is defined moves."
    - "Bluetooth discovery and pairing (comm/pairing.py, comm/bluetooth.py). Task 7.4.4 owns them."

rational:
  problem_statement: >
    send_command checks is_connected() under the lock and then uses
    self._sock or self._serial outside it. A concurrent disconnect()
    nulls the handle in the interval, and the call raises AttributeError
    rather than the socket error the surrounding handler expects, so the
    orderly reconnect does not occur. The same code exists three times,
    and the transport name set exists four times.
  proposed_solution: >
    Capture the handle under the lock and use the captured reference. Do
    that in all three transports first, then hoist the now-identical
    skeleton into the base class, then consolidate the name set.
  alternatives_considered:
    - option: "Hoist the skeleton into OBDTransport first, then apply the lock fix once."
      reason_rejected: >
        This is the first of the two orderings ai/task.md §7.6.3
        requires a decision between. It is fewer edits and a smaller
        final diff. Rejected because it delays a live defect behind a
        refactor of the class hierarchy on the path between the vehicle
        and the display, and because a defect fixed during a refactor
        cannot be attributed: if the race stops reproducing, it is not
        clear whether the lock discipline or the restructuring did it."
    - option: "Apply the lock fix in all three subclasses first, then refactor — TAKEN."
      reason_rejected: >
        Not rejected. This is §7.6.3's second ordering and the one
        taken. The fix lands in a small, reviewable, independently
        revertible commit that the §7.5.5 regression test can be run
        against directly. The duplicated edit is the price and it is
        three near-identical hunks."
    - option: "Hold the lock across the whole of send_command, including the receive loop."
      reason_rejected: >
        Simplest correct guard, and it serialises a call that blocks for
        up to the command timeout. disconnect() would then block behind
        an in-flight command for seconds, which is precisely the
        UI-freeze class of problem change-2d545bf5 addressed at §5.9.
        Capturing the reference gives correctness without the
        serialisation."
    - option: "Have is_connected() return the handle instead of a boolean."
      reason_rejected: >
        Attractive — it makes the misuse impossible rather than merely
        corrected — but is_connected is on the OBDTransport abstract
        interface (transport.py:92-99) and is called by OBDProtocol
        (obd.py:79) and by the reconnect loop. Changing its contract
        affects consumers outside this change's scope. A private
        _acquire_handle() is added instead and is_connected keeps its
        signature."
    - option: "Leave §5.8 alone."
      reason_rejected: >
        Legitimate — it has no runtime symptom — but the fourth list at
        app.py:267 was found only by grepping, and a name set kept in
        four places with three classifications will drift. It is Stage
        3 and can be dropped if the change proves too large."
  benefits:
    - "The race is closed and produces the handled transport error if the handle is closed under it."
    - "Future transport fixes are made once rather than three times."
    - "Adding a transport becomes one edit in one file instead of four across three."
  risks:
    - risk: >
        The regression test does not exist: ai/task.md §7.5.5 has not
        been carried out.
      mitigation: >
        Carry it out before implementing. It is the first implementation
        step. A concurrency fix without a test that failed beforehand is
        an assertion, not a result."
    - risk: >
        Stage 2 restructures the class hierarchy on the live data path.
        An error there affects every transport at once.
      mitigation: >
        Stage 2 is a separate commit, made only after Stage 1's test
        passes, and its acceptance criterion is that every transport's
        externally observable behaviour is unchanged. If Stage 2 proves
        difficult it can be abandoned with Stage 1 retained — the defect
        is fixed either way."
    - risk: >
        A captured reference is used after the object is closed, so the
        call fails on a closed socket rather than on None.
      mitigation: >
        That is the intent. A closed socket raises OSError, which the
        existing handlers catch and which marks the transport
        disconnected — the orderly path. The point is not to prevent the
        failure but to make it the failure the code already handles."
    - risk: >
        Consolidating the name set changes which transports are treated
        as forced or fast, altering startup behaviour.
      mitigation: >
        The consolidated definition must reproduce the current
        classification exactly, including the asymmetry that simtcp is
        forced while simbt routes through setup. That asymmetry is
        deliberate, per the report's §5.8, and is asserted rather than
        rationalised."
  benefits_measurement: >
    Places the lock discipline must be correct: 3 -> 1 after Stage 2.
    Places the transport name set is defined: 4 -> 1 after Stage 3.
    Unhandled AttributeError paths in send_command: 3 -> 0.

technical_details:
  current_behavior: >
    RFCOMMTransport.send_command checks is_connected at rfcomm.py:86 and
    calls self._sock.sendall at 93, with the receive loop reading
    self._sock at 101. TCPTransport is the same shape at
    tcp_transport.py:81, 89 and 97. SerialTransport at
    serial_transport.py:102, 109 and 115. disconnect nulls the handle
    via _close_socket (rfcomm.py:149-157, tcp_transport.py:146-154) or
    _close_serial (serial_transport.py:243-252).

    OBDTransport (transport.py:58-122) declares connect, disconnect,
    send_command, is_connected and state abstract, and provides
    __init__ and reconnect_indefinitely only.

    Transport names appear at main.py:72, app.py:80, app.py:84,
    app.py:267 and transport.py:145-158.
  proposed_behavior: >
    Each transport acquires its handle under the lock through a private
    accessor and operates on the captured reference. After Stage 2 the
    skeleton lives in OBDTransport and each subclass supplies only its
    own primitives. After Stage 3 the name set and its three
    classifications are defined once in transport.py.
  implementation_approach: >
    THREE STAGES, THREE COMMITS. §7.6.3's second ordering.

    STAGE 1 — the fix, three times.

    In each transport, add a private accessor:

        def _acquire_handle(self):
            """Return the socket/serial handle captured under the lock."""
            with self._lock:
                return self._sock          # or self._serial

    In send_command, replace the check-then-use with:

        handle = self._acquire_handle()
        if handle is None:
            ...existing not-connected path...
        handle.sendall(encoded_cmd)
        ...
        data = handle.recv(1024)

    The receive loop uses the same captured reference. A disconnect
    after the capture closes the socket the reference still names, so
    the call raises OSError — which the existing handler at
    rfcomm.py:122-124 catches — instead of AttributeError.

    is_connected keeps its signature and its callers.

    STAGE 2 — the hoist.

    With the three send_command bodies now identical but for the
    primitive calls, move the skeleton to OBDTransport:

      - connect: state transitions, error handling and retry, calling an
        abstract _open() supplied by the subclass;
      - disconnect: locking and state, calling abstract _close();
      - send_command: the capture, the write, the read-until-prompt loop
        and the error handling, calling abstract _write(handle, data)
        and _read(handle, n);
      - is_connected and state: concrete, reading the captured handle.

    Each subclass then supplies _open, _close, _write and _read only.
    SerialTransport's _discover_port and _probe_port remain its own.

    STAGE 3 — the name set.

    In transport.py:

        TRANSPORT_NAMES = ('tcp', 'serial', 'rfcomm', 'simtcp', 'simbt')
        TRANSPORT_FORCED = ('tcp', 'serial', 'simtcp')
        TRANSPORT_FAST = ('simbt', 'simtcp', 'tcp')

    main.py:72 takes choices=list(TRANSPORT_NAMES). app.py:80 tests
    against TRANSPORT_FORCED; app.py:84's elif becomes the complement,
    computed rather than restated. app.py:267 tests against
    TRANSPORT_FAST.

    The asymmetry — simtcp forced, simbt through setup — is preserved
    exactly and given a comment recording that it is deliberate, per
    report §5.8.
  code_changes:
    - component: "RFCOMMTransport, TCPTransport, SerialTransport"
      file: "src/gtach/comm/rfcomm.py, src/gtach/comm/tcp_transport.py, src/gtach/comm/serial_transport.py"
      change_summary: >
        Stage 1: _acquire_handle added; send_command and its receive
        loop use the captured reference. Stage 2: the common skeleton
        removed in favour of the base class's, leaving _open, _close,
        _write and _read.
      functions_affected:
        - "send_command"
        - "_acquire_handle"
        - "connect"
        - "disconnect"
        - "is_connected"
    - component: "OBDTransport"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        Stage 2: concrete connect, disconnect, send_command, is_connected
        and state; new abstract _open, _close, _write, _read. Stage 3:
        TRANSPORT_NAMES, TRANSPORT_FORCED and TRANSPORT_FAST added.
      classes_affected:
        - "OBDTransport"
    - component: "parse_arguments"
      file: "src/gtach/main.py"
      change_summary: "Stage 3: argparse choices derive from TRANSPORT_NAMES."
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: "Stage 3: the forced and fast classifications derive from transport.py."
  data_changes: []
  interface_changes:
    - "OBDTransport gains four abstract methods and makes five concrete. Any transport implemented outside this package would need updating; none exists."

dependencies:
  internal:
    - component: "ai/task.md §7.5.5"
      impact: "PREREQUISITE. Supplies the regression test. Not yet carried out."
    - component: "OBDProtocol — comm/obd.py:79"
      impact: "Calls is_connected and send_command. Their contracts are unchanged. Not modified."
    - component: "change-2d545bf5"
      impact: "Landed. It addressed §5.9's shutdown blocking in app.py; this change alters the other side of the same interaction. No overlap in the lines touched."
    - component: "SimTransport — comm/sim_transport.py"
      impact: "Dispatched by name; its dispatch is preserved. Not modified."
  external: []
  required_changes:
    - change_ref: "change-2d545bf5"
      relationship: "related"

testing_requirements:
  test_approach: >
    Stage 1 is tested by the §7.5.5 reproduction, driven with explicit
    synchronisation rather than sleeps — the interval is a few
    bytecodes and cannot be hit by timing. Stage 2 is tested by
    asserting that every transport's observable behaviour is unchanged
    against a fake socket and a fake serial port. Stage 3 is tested by
    asserting that adding a name in one place makes it valid everywhere.
  test_cases:
    - scenario: "The §7.5.5 reproduction: disconnect() forced between the handle capture and its use, in each of the three transports."
      expected_result: "OSError, handled, transport marked disconnected. Against the pre-change implementation the same test raises AttributeError. This discrimination is the acceptance criterion for Stage 1."
    - scenario: "send_command with no connection."
      expected_result: "The existing not-connected path, unchanged."
    - scenario: "send_command on a healthy connection."
      expected_result: "The response, unchanged."
    - scenario: "A socket error mid-receive."
      expected_result: "Handled as today."
    - scenario: "disconnect() during the receive loop."
      expected_result: "OSError from the captured reference, handled."
    - scenario: "is_connected before and after."
      expected_result: "Same signature, same results."
    - scenario: "Each transport's connect, disconnect, send_command, is_connected and state, before and after Stage 2, against fakes."
      expected_result: "Identical observable behaviour for all three."
    - scenario: "Stage 2's abstract methods."
      expected_result: "Instantiating OBDTransport directly still fails; each concrete subclass implements all four."
    - scenario: "TRANSPORT_NAMES against main.py's argparse choices."
      expected_result: "Equal."
    - scenario: "A name appended to TRANSPORT_NAMES in a test."
      expected_result: "Accepted at the command line without editing main.py."
    - scenario: "The forced classification for each of the five names."
      expected_result: "tcp, serial and simtcp forced; rfcomm and simbt routed through setup — the current behaviour exactly."
    - scenario: "The fast classification for each of the five names."
      expected_result: "simbt, simtcp and tcp fast; the poll interval resolves to 0.02 for those and 0.05 otherwise."
    - scenario: "select_transport for each of the five names."
      expected_result: "The same class as today in each case."
  regression_scope:
    - "tests/comm/ — once populated per ai/task.md §8.2."
    - "On gtach.local: normal OBD polling over RFCOMM is unaffected."
    - "On gtach.local: re-entering setup from the DISCONNECTED screen while polling is active does not produce an unhandled exception on the obd_protocol thread — the production expression of the race."
    - "On ELM327-Emulator.local: the tcp and simtcp transports connect and poll."
    - "Serial transport against a physical adapter, if available."
  validation_criteria:
    - "python -m py_compile on all six files passes."
    - "pytest tests/ passes with no new failures."
    - "self._sock and self._serial are not dereferenced outside the lock anywhere in send_command or its receive loop."
    - "The §7.5.5 test fails against the pre-change implementation and passes after Stage 1."
    - "After Stage 2, the connect/disconnect/send_command skeleton appears once."
    - "After Stage 3, the five transport names appear as literals in transport.py only."

implementation:
  implementation_steps:
    - step: "PREREQUISITE: carry out ai/task.md §7.5.5 — reproduce the race under a controlled test calling disconnect() concurrently with send_command(). Record the observed failure. This test is the acceptance criterion for Stage 1."
      owner: "William Watson"
    - step: "Stage 1 — _acquire_handle and the captured-reference use, in all three transports. Commit."
      owner: "Claude Code"
    - step: "Confirm the §7.5.5 test now passes and failed before. Commit only if it discriminates."
      owner: "Claude Code"
    - step: "Stage 2 — hoist the skeleton into OBDTransport. Commit."
      owner: "Claude Code"
    - step: "Stage 3 — consolidate the name set and its three classifications. Commit."
      owner: "Claude Code"
    - step: "Deploy and exercise on gtach.local and ELM327-Emulator.local, including setup re-entry during active polling."
      owner: "William Watson"
  rollback_procedure: >
    Three commits. Stage 3 and Stage 2 can each be reverted alone,
    leaving the defect fixed. Stage 1 is the one that must survive; it
    is also the smallest.
  deployment_notes: >
    No visible change. The race is rare and its correction is the
    absence of an exception that was itself rare. Ships in v0.4.0
    (ai/task.md §8.5). The on-target check that matters is re-entering
    setup while polling is active, which is the production expression of
    the race.

verification:
  implemented_date: "2026-08-04"
  implemented_by: "Claude Code, per prompt-6481f8ce (commits 3f5fc5e, fe879f9, 51a930b)"
  verification_date: "2026-08-05"
  verified_by: "Claude Code (development-platform script); William Watson (gtach.local)"
  test_results: >
    Delivered as specified across three stage commits. §7.5.5
    reproduction discharged pre- and post-Stage-1 with explicit
    synchronisation, discriminating by logged message rather than
    return value. Source re-check 2026-08-07 confirms OBDTransport's
    hoisted skeleton and the consolidated TRANSPORT_NAMES/FORCED/FAST
    constants imported and used by main.py and app.py.
  issues_found:
    - "app.py:91 still tests transport_arg == 'simbt' as a literal, a fourth transport-name site the prompt named three sites and instructed to leave alone. Documented, not a blocker."

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-2d545bf5"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-6481f8ce"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-6481f8ce."
      - "States the ai/task.md §7.6.3 ordering decision: the lock fix is applied in all three subclasses first and the refactor follows, so the defect is not delayed behind a hierarchy change and its correction is attributable."
      - "Recorded that holding the lock across the whole of send_command was rejected because it would serialise disconnect behind an in-flight command — the failure class change-2d545bf5 addressed at §5.9."
      - "Recorded that is_connected keeps its signature, a private _acquire_handle being added instead, because is_connected is on the abstract interface and has consumers outside this scope."
      - "Recorded the fourth transport-name list at app.py:267 in Stage 3's scope, and the simtcp/simbt asymmetry as deliberate and to be preserved exactly."
      - "Staged so Stages 2 and 3 can be abandoned with the defect still fixed."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial change document coupled to issue-6481f8ce. States the §7.6.3 ordering decision — fix then refactor — and stages the work so the concurrency fix survives abandonment of either later stage. |
| 1.1 | 2026-08-07 | Status proposed → closed. Implementation and verification recorded (three stage commits); source re-check confirms the hoisted skeleton and consolidated name-set constants. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
