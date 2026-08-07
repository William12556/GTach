Created: 2026 August 04

# Issue: A Check-Then-Act Race That Must Be Fixed Three Times, in Three Files That Are Nearly the Same File

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-6481f8ce"
  title: "Each transport's send_command checks is_connected() under the lock and then uses the socket or serial handle outside it, so a concurrent disconnect() produces an AttributeError instead of the handled OSError; the same logic is duplicated across three files, and the set of valid transport names is maintained independently in four places"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-6481f8ce"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Findings §5.3 (Check-then-act race), §4.3 (Duplicated transport
    error-handling logic) and §5.8 (Transport-name lists duplicated),
    with §7.0 recommendation #7. Task list reference ai/task.md §7.4.5.

affected_scope:
  components:
    - name: "RFCOMMTransport.send_command"
      file_path: "src/gtach/comm/rfcomm.py"
    - name: "TCPTransport.send_command"
      file_path: "src/gtach/comm/tcp_transport.py"
    - name: "SerialTransport.send_command"
      file_path: "src/gtach/comm/serial_transport.py"
    - name: "OBDTransport"
      file_path: "src/gtach/comm/transport.py"
    - name: "select_transport"
      file_path: "src/gtach/comm/transport.py"
    - name: "parse_arguments"
      file_path: "src/gtach/main.py"
    - name: "GTachApplication.start"
      file_path: "src/gtach/app.py"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: >
    Source checkout at 0.3.2. The race requires two threads and has not
    been reproduced — see technical_notes.
  steps:
    - "§5.3 — read rfcomm.py:86. 'if not self.is_connected():' — is_connected acquires self._lock at rfcomm.py:136 and releases it before returning."
    - "§5.3 — read rfcomm.py:93. 'self._sock.sendall(encoded_cmd)' — outside any lock."
    - "§5.3 — read rfcomm.py:66-73. disconnect() takes the lock and calls _close_socket, which sets self._sock = None at rfcomm.py:157."
    - "§5.3 — the same shape at tcp_transport.py:81 and 89, with _close_socket at 146-154; and at serial_transport.py:102 and 109, with _close_serial at 243-252."
    - "§5.3 — identify the concurrent caller: app.py._re_enter_setup (app.py:212) runs on the UI/setup thread and stops the OBD thread; the OBD polling thread is inside send_command at that moment."
    - "§4.3 — diff rfcomm.py against tcp_transport.py. connect, disconnect, send_command, is_connected, state and the socket-closing helper are structurally identical, differing only in the socket construction."
    - "§5.8 — read main.py:72: choices=['tcp', 'serial', 'rfcomm', 'simtcp', 'simbt']."
    - "§5.8 — read app.py:80: transport_forced = transport_arg in ('tcp', 'serial', 'simtcp')."
    - "§5.8 — read app.py:84: elif transport_arg in ('simbt', 'rfcomm')."
    - "§5.8 — read transport.py:145, 149, 154, 158: the same five names dispatched again."
  frequency: "intermittent"
  reproducibility_conditions: >
    The §5.3 race requires disconnect() to execute between the
    is_connected() check and the handle's use — a window of a few
    bytecodes. It has not been reproduced. ai/task.md §7.5.5 exists to
    reproduce it under a controlled test and has not been carried out.

    §4.3 and §5.8 are unconditional structural findings.
  preconditions: >
    Two threads. In production: the OBD polling thread inside
    send_command and the setup thread in _re_enter_setup.
  test_data: >
    THE WINDOW, precisely. In RFCOMMTransport.send_command:

      line 86   if not self.is_connected():      # acquires and releases
      line 93   self._sock.sendall(encoded_cmd)  # unguarded

    is_connected returns self._sock is not None under the lock and then
    releases it. Between the return and line 93 the value is stale. If
    disconnect() runs in that interval, self._sock is None and line 93
    raises AttributeError: 'NoneType' object has no attribute 'sendall'.

    The handler at rfcomm.py:122-124 catches socket errors and marks the
    transport disconnected. An AttributeError is not what it expects, so
    the failure escapes as an unhandled exception on the polling thread
    rather than as an orderly reconnect.

    The same three-line pattern is at tcp_transport.py:81/89 and
    serial_transport.py:102/109, and the receive loops at rfcomm.py:101
    and tcp_transport.py:97 use the handle unguarded as well.

    A FOURTH TRANSPORT-NAME LIST, NOT IN THE REPORT. §5.8 names three
    places. There is a fourth: app.py:267,

        _fast_transports = ('simbt', 'simtcp', 'tcp')

    which selects a 0.02 s rather than 0.05 s OBD poll interval. It is a
    different classification of the same name set, and it is the one
    most likely to be missed when a transport is added, because its
    effect — a slower poll rate — is a performance change rather than a
    failure.

    So the name set is maintained in four places and classified three
    different ways: valid (main.py), forced versus setup-routed
    (app.py:80/84, transport.py:145-158), and fast versus slow
    (app.py:267).
  error_output: >
    Expected but not observed:
    AttributeError: 'NoneType' object has no attribute 'sendall'
    from comm/rfcomm.py:93, on the obd_protocol thread.

behavior:
  expected: >
    A check and the use it authorises are made under one acquisition of
    the lock, or the checked object is captured under the lock and the
    captured reference used. A fault in a transport surfaces as the
    handled transport error, not as an attribute error on a None. One
    definition of the transport name set.
  actual: >
    (a) §5.3 — every transport checks is_connected() and then uses
    self._sock or self._serial outside the lock. A concurrent
    disconnect() nulls the handle in between and the call raises
    AttributeError, which the surrounding handler does not anticipate.

    (b) §4.3 — the same connect, disconnect, send_command and close
    logic exists three times, so this fix must be made three times, as
    must every future one.

    (c) §5.8 — the transport names are enumerated in main.py, twice in
    app.py and again in transport.py, with three different
    classifications. Adding a transport requires four edits and an
    omission changes behaviour silently rather than raising.
  impact: >
    An unhandled exception on the OBD polling thread at exactly the
    moment the operator re-enters setup — which is to say, when the
    transport is already misbehaving and the operator is trying to fix
    it. The reconnect logic that should engage does not, because the
    exception is of the wrong type.

    Frequency unknown: the window is small and the race has not been
    reproduced.
  workaround: >
    None in code. Avoiding setup re-entry while polling is active is not
    a workaround an operator can be asked for.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pyserial"
      version: "any"
  domain: "domain_1"

analysis:
  root_cause: >
    is_connected() is a correct predicate and an incorrect guard. It
    answers a question about a moment that has passed by the time the
    caller acts on it. The three-file duplication is why the pattern
    survived: the same mistake in one place is a defect, and in three
    places it looks like a convention.

    The four name lists are the ordinary result of adding a
    classification where it is needed rather than where the data lives.
  technical_notes: >
    GATED ON AN OBSERVATION NOT YET TAKEN. ai/task.md §7.5.5 requires
    the race to be reproduced under a controlled test calling
    disconnect() concurrently with send_command(), to confirm the
    failure mode and to supply the regression test for this triple.
    ai/task.md §8.1 names this triple among those that cannot be
    authored correctly until then. It is authored now by explicit
    instruction.

    The assumption this creates is narrow and worth stating exactly:
    that the failure mode is AttributeError rather than something else.
    The reasoning is direct — _close_socket sets self._sock = None
    (rfcomm.py:157) and line 93 calls a method on it — so the
    assumption is strong. What the reproduction adds is not confirmation
    of the mechanism but a regression test that fails before the fix,
    which §7.5.5 exists to supply and which change-6481f8ce cannot
    substitute for.

    §7.6.3 REQUIRES AN ORDERING DECISION. ai/task.md §7.6.3 states that
    the §5.3 race must currently be fixed in three files and that two
    orderings are available — hoist the common skeleton into
    OBDTransport first and fix once, or fix three times and refactor
    afterwards — and that the change document must state which is
    taken. change-6481f8ce states it.

    ONE ADDITION TO THE REPORT. §5.8 names three places holding the
    transport-name set. There is a fourth, app.py:267's
    _fast_transports. See test_data. Consolidating three of four would
    leave the least visible one behind.

    ONE OBSERVATION ABOUT SCOPE. This is the largest of the eight
    remaining triples: it touches six files and restructures a class
    hierarchy on the path between the vehicle and the display. §4.3 and
    §5.8 are maintainability findings with no runtime symptom, while
    §5.3 is a live defect. They are grouped because ai/task.md §7.4
    groups them and because §4.3 is the reason §5.3 is expensive to fix
    — but the risk profiles differ sharply, and change-6481f8ce
    separates them into stages that can be landed and reverted
    independently.
  related_issues:
    - issue_ref: "issue-2d545bf5"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Capture the handle under the lock and use the captured reference,
    in all three transports first, so the defect is fixed before
    anything is restructured. Then hoist the common skeleton into
    OBDTransport. Then define the transport name set and its three
    classifications once, in transport.py, and have main.py and app.py
    read them. See change-6481f8ce.
  change_ref: "change-6481f8ce"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A predicate that reads shared state and returns a boolean cannot
    guard the use of that state. Where the caller needs the object, the
    accessor should return the object under the lock — so that holding
    a stale reference is at least holding a real one, and the failure is
    the handled socket error rather than an attribute error.

    Duplicated logic converts one defect into three and disguises the
    third as a convention.
  process_improvements: >
    The fourth transport-name list was found by grepping for the name
    set rather than by reading the three locations the report cites.
    Where a report says a value is duplicated in N places, the check is
    a grep for the value, not a reading of the N.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "In each transport, the handle is captured under the lock and the captured reference is used; self._sock and self._serial are not dereferenced outside the lock in send_command."
    - "A concurrent disconnect() during send_command produces the handled transport error, not AttributeError."
    - "The regression test from ai/task.md §7.5.5 fails against the pre-change implementation and passes after."
    - "The receive loops use the captured reference too."
    - "The common connect/disconnect/send_command skeleton exists once, in OBDTransport."
    - "Each subclass supplies only its own socket or serial primitives."
    - "Every transport's externally observable behaviour is unchanged: connect, disconnect, send_command, is_connected and state."
    - "The transport name set is defined once in transport.py."
    - "main.py's argparse choices derive from it."
    - "app.py's forced/setup-routed classification derives from it."
    - "app.py's fast/slow poll classification derives from it."
    - "Adding a name to the set in transport.py alone makes it valid at the command line — asserted by test rather than by inspection."
    - "SimTransport's dispatch for simtcp and simbt is unchanged."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-6481f8ce"
  test_refs: []

notes: >
  This is task 7.4.5 in ai/task.md §7.4 and step 8 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5).

  issue_info.type is defect per ai/task.md §7.2 and the D1 discharge
  step at task-list-cross-check-discrepancies.md §5.4 item 4: §5.3 is a
  check-then-act race producing an unhandled AttributeError, and it
  outranks §4.3 and §5.8, which are maintainability findings.

  Authored ahead of ai/task.md §7.5.5, the controlled reproduction that
  supplies this triple's regression test, contrary to §8.1. Carry out
  §7.5.5 before implementing; the reproduction is the test, and a fix
  shipped without one cannot be shown to have worked.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial issue document from core-comm-utils-code-review.md findings §5.3, §4.3 and §5.8 with §7.0 recommendation #7."
      - "Recorded the race window precisely, line by line, in all three transports, and identified the concurrent caller as app.py._re_enter_setup."
      - "Recorded a fourth transport-name list the report does not name: app.py:267's _fast_transports, which classifies the same names by poll rate and whose omission would be the least visible."
      - "Recorded that the receive loops dereference the handle unguarded as well as the send paths."
      - "Recorded the narrow assumption created by authoring ahead of §7.5.5 — that the failure mode is AttributeError — and that what the reproduction supplies is the regression test rather than confirmation of the mechanism."
      - "Recorded that the three findings differ sharply in risk and that the change document stages them accordingly."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial issue document from core review findings §5.3, §4.3 and §5.8 with recommendation #7. Records the race window line by line, a fourth transport-name list the report omits, and the assumption created by authoring ahead of the §7.5.5 reproduction. |

---

Copyright (c) 2026 William Watson. MIT License.
