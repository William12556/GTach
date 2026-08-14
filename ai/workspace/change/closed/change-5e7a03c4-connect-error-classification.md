Created: 2026 August 12

# Change: Close Failed Sockets and Report Why a Connect Failed

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-5e7a03c4"
  title: "Close the socket on every failure path in RFCOMMTransport._open; classify connect failures by errno and record the cause on the transport; distinguish an absent Bluetooth controller from an absent peer and surface the cause on the DISCONNECTED screen"
  date: "2026-08-12"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 2
  coupled_docs:
    issue_ref: "issue-5e7a03c4"
    issue_iteration: 2

source:
  type: "issue"
  reference: "issue-5e7a03c4"
  description: >
    Resolves issue-5e7a03c4. _open abandons its socket when connect()
    raises, and errno is discarded at the first handler, so an adapter
    fault and a missing OBD dongle are indistinguishable in the log and
    identical on the display.

scope:
  iteration_2_addendum: >
    Iteration 1 is implemented and deployed; its classified cause is
    confirmed in the 13:43 and 13:44 logs on gtach.local. Iteration 2
    adds three edits closing gaps found on review of that delivery.
    All remain reporting-only; nothing added here acts on the host.

    EDIT R — set a cause in drop_link(). _last_failure_cause is written
    only by connect() failing, so a link torn down for sustained
    silence leaves the DISCONNECTED screen with no explanation. That is
    the failure mode change-9c2f41d8 exists to handle, and the screen
    that most needs a reason has none. drop_link already takes _lock
    and already sets DISCONNECTED; recording a cause is one assignment
    beside them.

    EDIT S — escalate to a wedge diagnosis on consecutive failures.
    _bluetooth_adapter_present detects an ABSENT controller, not a
    WEDGED one: a controller listed under /sys/class/bluetooth but
    unable to initialise still satisfies the probe. Confirmed from the
    logs — 'no bluetooth controller' has never been reported across 44
    EBUSY, 42 host-down and 13 timed-out failures, including while the
    controller could not be brought up. Count consecutive connect
    failures and, past a small threshold with the adapter present,
    escalate the cause to name a probable wedge needing a reset.

    EDIT T — suppress the duplicated suffix. socket.timeout carries
    errno None, so _classify_connect_error falls through to str(exc),
    which for that exception is the text already in the log message.
    Observed 4 times as "channel 1: timed out (timed out)".

  summary: >
    Reporting only, in three parts. Close the socket on the failure
    path in rfcomm.py. Classify connect failures by errno in
    transport.py and record the cause. Read /sys/class/bluetooth to
    tell an absent controller from an absent peer, and show the cause
    as a status line on the DISCONNECTED screen.
  affected_components:
    - name: "RFCOMMTransport._open"
      file_path: "src/gtach/comm/rfcomm.py"
      change_type: "modify"
    - name: "OBDTransport.connect / last_failure_cause"
      file_path: "src/gtach/comm/transport.py"
      change_type: "modify"
    - name: "DisplayManager._render_disconnected (status line)"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "ANY automated recovery action: adapter reset, rfkill cycle, restarting hciuart, reloading kernel modules, or rebooting. Deliberately excluded. On target, a manual `hciconfig hci0 down && hciconfig hci0 up` saw the down succeed and the up fail with ETIMEDOUT, leaving the controller worse than before. An unattended equivalent would have done the same in a vehicle. Whether GTach should ever attempt recovery is a scope extension to be decided separately and by consensus, per governance."
    - "Shelling out to hcitool, hciconfig, btmgmt or rfkill. Parsing human-readable tool output requires root, cannot be exercised on the development platform, and is unnecessary: errno and sysfs carry what is needed."
    - "src/gtach/comm/obd.py and the OBD protocol layer."
    - "The retry cadence. EBUSY continues to retry at 5 s like any other failure; this change reports the cause, it does not alter the policy."
    - "SerialTransport and TCPTransport error classification. The same undifferentiated handling applies there, but RFCOMM is where the evidence is; extending it is a separate decision."
    - "The DISCONNECTED screen's Setup and Simulate affordances, their geometry and their callbacks."

rational:
  problem_statement: >
    RFCOMMTransport._open (rfcomm.py:45-49) creates a socket and
    abandons it when connect() raises. OBDTransport.connect()'s handler
    calls _discard_handle(), but self._handle was never assigned, so
    nothing closes it; only refcounting reclaims it. An unclosed RFCOMM
    socket holds its ACL reference.

    Separately, grep for 'errno' across src/gtach/comm/ returns
    nothing. connect() catches _IO_ERRORS and logs one message for all
    of them, so EBUSY, ETIMEDOUT, EHOSTDOWN and ENODEV are
    indistinguishable in the log and identical on the display.

    On target this cost a full session and three rounds of manual
    hcitool work to establish what one errno would have said: a single
    gtach process (1645), an ACL to the adapter in state 9 (BT_CLOSED)
    with its handle unreaped, and `hciconfig hci0 up` timing out. The
    controller was wedged. GTach reported "Failed to connect, retrying
    in 5.0 seconds" 12 times and showed the same DISCONNECTED screen it
    shows for a dongle out of range.
  proposed_solution: >
    EDIT O — close the socket on failure. Wrap the connect in _open in
    try/except, close the socket, re-raise unchanged so the caller's
    existing handling is untouched.

    EDIT P — classify by errno. Add a module-level mapping from the
    errnos that matter to a short cause string, and a
    last_failure_cause property on OBDTransport. In connect()'s
    _IO_ERRORS handler, resolve the cause, record it, and include it in
    the existing log message. Unmapped errnos fall back to the errno
    name.

    EDIT Q — distinguish adapter from peer. When the cause is one that
    could mean either, check for an adapter under /sys/class/bluetooth,
    as PlatformDetector already does (platform.py:706). Absent means an
    adapter fault, which is a different cause from an unreachable peer.
    Expose the cause to the display and render it as a short status
    line on the DISCONNECTED screen.

    Reporting only. Nothing in this change acts on the host.
  alternatives_considered:
    - option: "Have GTach reset the adapter when it sees repeated EBUSY."
      reason_rejected: >
        The on-target evidence is directly against it. A manual down/up
        left the controller unable to come back at all. Automating that
        unattended, in a vehicle, converts a diagnosable fault into an
        unrecoverable one. Excluded pending a separate decision.
    - option: "Shell out to hcitool con and hciconfig to gather state."
      reason_rejected: >
        Parses human-readable output, requires root, and cannot be
        exercised on the development platform. errno and sysfs give the
        same discrimination with a file read.
    - option: "Log errno numerically and stop there."
      reason_rejected: >
        Moves the interpretation burden to whoever reads the log later,
        which is the cost this change exists to remove. The display
        cannot show a number usefully either.
    - option: "Back off the retry interval on EBUSY, since retrying cannot clear it."
      reason_rejected: >
        Not rejected on merit, but out of scope. It is a policy change
        and this change is diagnostic. Revisit once the reported cause
        has been seen in the field.
    - option: "Add the same classification to SerialTransport and TCPTransport now."
      reason_rejected: >
        The evidence is RFCOMM-specific and the errnos that matter
        differ per transport. Extending it should follow evidence, not
        precede it.
  benefits:
    - "An adapter fault and a missing dongle become distinguishable, in the log and on the display."
    - "A failed connect no longer leaves a socket open, on the paths that precede a wedged link."
    - "Diagnosis stops requiring an SSH session and manual hcitool work."
    - "No new dependency, no subprocess, no root requirement."
  risks:
    - risk: "An errno is mapped to a misleading cause."
      mitigation: >
        Only errnos with an unambiguous meaning for a connecting RFCOMM
        socket are mapped. Anything else falls back to the errno name,
        which is still strictly more information than today.
    - risk: "The sysfs probe is wrong on some platform."
      mitigation: >
        Guarded and non-fatal: if the probe cannot be performed the
        cause degrades to the errno-derived one. PlatformDetector
        already reads the same path, so the pattern is precedented.
    - risk: "The DISCONNECTED status line crowds the screen or overlaps the buttons."
      mitigation: >
        Placed above the button column, whose geometry is owned by
        _register_disconnected_regions and is not modified. Text is
        short and rendered with the existing typography.
    - risk: "last_failure_cause is written by the transport thread and read by the display thread."
      mitigation: >
        A single string attribute written under the existing _lock and
        read under it. No compound state.

technical_details:
  current_behavior: >
    A failed connect abandons its socket and produces one message
    regardless of cause. The DISCONNECTED screen is identical for every
    cause.
  proposed_behavior: >
    A failed connect closes its socket and logs a named cause. The
    transport records that cause. The DISCONNECTED screen shows it as a
    short status line, distinguishing at minimum an adapter fault, a
    wedged link and an unreachable peer.
  implementation_approach: >
    Three localised edits across three files. No new dependencies. The
    errno mapping is a module-level dict; the sysfs probe is a guarded
    path existence check.
  code_changes:
    - component: "RFCOMMTransport"
      file: "src/gtach/comm/rfcomm.py"
      change_summary: "Close the socket when connect() raises, then re-raise unchanged."
      functions_affected:
        - "_open"
      classes_affected:
        - "RFCOMMTransport"
    - component: "OBDTransport"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        Add an errno-to-cause mapping and a last_failure_cause
        property; resolve, record and log the cause in connect()'s
        _IO_ERRORS handler; perform the adapter probe when the errno
        alone cannot discriminate.
      functions_affected:
        - "__init__"
        - "connect"
        - "last_failure_cause"
      classes_affected:
        - "OBDTransport"
    - component: "EDIT R (iteration 2) — OBDTransport.drop_link"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        Set _last_failure_cause under the existing _lock, alongside the
        existing DISCONNECTED assignment, naming sustained silence from
        the adapter rather than a failed connect. Accept an optional
        cause argument defaulting to a module-level constant, so a
        future caller with better information can supply its own
        without changing existing call sites.
      functions_affected:
        - "drop_link"
      classes_affected:
        - "OBDTransport"
    - component: "EDIT S (iteration 2) — consecutive connect-failure escalation"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        Add _MAX_CONSECUTIVE_CONNECT_FAILURES = 6 and a
        _consecutive_connect_failures counter reset on any successful
        connect. In connect()'s failure handler, increment it and, on
        reaching the threshold with the adapter present, override the
        resolved cause with a wedge diagnosis naming a reset. Six at
        the 5.0 s retry interval is ~30 s of sustained failure, above
        any transient and below the point an operator would reasonably
        wait.
      functions_affected:
        - "__init__"
        - "connect"
        - "_classify_connect_error"
      classes_affected:
        - "OBDTransport"
    - component: "EDIT T (iteration 2) — duplicate-suffix suppression"
      file: "src/gtach/comm/transport.py"
      change_summary: >
        In connect()'s failure logging, append the cause only when it
        differs from str(exc), which is already interpolated into the
        message.
      functions_affected:
        - "connect"
      classes_affected:
        - "OBDTransport"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Render the transport's last failure cause as a short status
        line on the DISCONNECTED screen, above the existing button
        column.
      functions_affected:
        - "_render_disconnected"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes:
    - interface: "OBDTransport.last_failure_cause"
      change_type: "contract"
      details: "New read-only property returning a short human-readable cause string, or None if no connect has failed."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "PlatformDetector"
      impact: "None. Its /sys/class/bluetooth probe is the precedent for the adapter check, not a dependency of it."
    - component: "DisplayManager._link_lost"
      impact: "None. The DISCONNECTED condition is unchanged; only what is drawn on that screen gains a line."
  external: []
  required_changes:
    - change_ref: "change-9c2f41d8"
      relationship: "blocked_by. Modifies the same connect and reconnect paths."

testing_requirements:
  test_approach: >
    Unit tests with a fake socket whose connect raises a chosen errno,
    plus on-target confirmation of the two distinguishable cases.
  test_cases:
    - scenario: "_open where connect() raises."
      expected_result: "The socket's close() was called exactly once; the original exception propagates unchanged."
    - scenario: "_open where connect() succeeds."
      expected_result: "close() is not called; the socket is returned."
    - scenario: "connect() failing with EBUSY."
      expected_result: "last_failure_cause names a busy or wedged link; the log message includes it."
    - scenario: "connect() failing with EHOSTDOWN."
      expected_result: "last_failure_cause names an unreachable peer."
    - scenario: "connect() failing with ENODEV, with no adapter under /sys/class/bluetooth."
      expected_result: "last_failure_cause names an adapter fault."
    - scenario: "connect() failing with an unmapped errno."
      expected_result: "last_failure_cause falls back to the errno name; no exception."
    - scenario: "The sysfs probe raising."
      expected_result: "The cause degrades to the errno-derived one; connect() still returns False."
    - scenario: "connect() succeeding after a prior failure."
      expected_result: "last_failure_cause is cleared."
    - scenario: "On target: run with the OBD peer absent but the controller healthy."
      expected_result: "Log and display report an unreachable peer."
    - scenario: "On target: run with the controller down."
      expected_result: "Log and display report an adapter fault, distinctly from the above."
    - scenario: "On target: several retry cycles against a failing connect."
      expected_result: "/proc/<pid>/fd shows no growth in socket descriptors."
  regression_scope:
    - "Successful connect at startup and after a link drop."
    - "The reconnect loop's cadence and shutdown behaviour (change-9c2f41d8)."
    - "The DISCONNECTED screen's Setup and Simulate controls (change-7d4e91a3)."
    - "Simulation transports, which do not use RFCOMM."
    - "tests/ suite in full."
  validation_criteria:
    - "No subprocess, os.system or shell invocation is introduced."
    - "No code path performs a Bluetooth recovery action."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDIT O in rfcomm.py."
      owner: "tactical"
    - step: "EDIT P in transport.py."
      owner: "tactical"
    - step: "EDIT Q in manager.py."
      owner: "tactical"
    - step: "Add unit tests per testing_requirements.test_cases items 1-8."
      owner: "tactical"
    - step: "Deploy to gtach.local and confirm the two distinguishable cases."
      owner: "human"
  rollback_procedure: "Revert the commit. Three files, all additive or localised."
  deployment_notes: >
    No service, packaging or configuration change. Verification of the
    adapter-fault case requires the controller to be down, which on
    gtach.local currently requires restarting hciuart.service or a
    reboot to undo.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-9c2f41d8"
      relationship: "blocked_by. Same connect and reconnect paths."
    - change_ref: "change-7d4e91a3"
      relationship: "related. Made the DISCONNECTED screen's controls live; this change adds a status line to the same screen."
  related_issues:
    - issue_ref: "issue-5e7a03c4"
      relationship: "resolves"
    - issue_ref: "issue-9c2f41d8"
      relationship: >
        related. Still active: its link-loss path has not been
        exercised, no connection having been established during the
        session that produced this issue.

notes: >
  This change reports; it does not act. The exclusion of automated
  recovery is recorded in out_of_scope with its evidence, so that it
  reads as a decision rather than an omission. If recovery is later
  wanted, it should be raised as its own issue with its own risk
  assessment — an application that power-cycles the host's Bluetooth
  controller unattended is a materially different thing from one that
  displays a fault.

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-5e7a03c4 iteration 1."
      - "Three edits: close failed sockets in _open, classify connect failures by errno and record the cause, distinguish an absent controller from an absent peer and show the cause on the DISCONNECTED screen."
      - "Records the deliberate exclusion of automated recovery, with the on-target evidence that a manual adapter down/up left the controller unable to come back."
  - version: "2.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Iteration 1 -> 2. Status proposed -> implemented; coupled issue_iteration raised 1 -> 2."
      - "EDIT R: set a cause in drop_link, so the DISCONNECTED screen has an explanation in the mid-session link-loss case change-9c2f41d8 addresses."
      - "EDIT S: consecutive connect-failure escalation at 6 failures (~30 s), overriding the resolved cause with a wedge diagnosis. Closes the gap that the sysfs probe sees an absent controller but not a wedged one."
      - "EDIT T: suppress the cause suffix when it duplicates str(exc), which produced 'timed out (timed out)'."
      - "Rejected for EDIT S: reading the real HCI_UP flag via HCIGETDEVINFO ioctl on an AF_BLUETOOTH/BTPROTO_HCI socket. More truthful, but adds struct packing and an ioctl untestable on the development platform."
      - "An operator-initiated Bluetooth reset button remains out of scope and will be raised separately once the working recovery command is established on target."

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
| 1.0 | 2026-08-12 | Initial change document. Close failed sockets, classify connect failures by errno, distinguish adapter fault from unreachable peer and surface it on the DISCONNECTED screen. Automated recovery excluded with recorded evidence. |
| 2.0 | 2026-08-12 | Iteration 1 -> 2. Adds EDIT R (cause set in drop_link), EDIT S (consecutive connect-failure escalation to a wedge diagnosis) and EDIT T (suppress the duplicated cause suffix). Still reporting-only. |

---

Copyright (c) 2026 William Watson. MIT License.
