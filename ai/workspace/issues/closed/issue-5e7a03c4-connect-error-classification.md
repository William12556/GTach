Created: 2026 August 12

# Issue: Every Connect Failure Looks the Same, and Failed Sockets Are Not Closed

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-5e7a03c4"
  title: "RFCOMMTransport._open abandons its socket when connect() raises, and every connect failure — absent peer, wedged link, absent controller — is logged and displayed identically, so an adapter fault is indistinguishable from a missing OBD dongle"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 2
  coupled_docs:
    change_ref: "change-5e7a03c4"
    change_iteration: 2

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Raised 2026-08-12 during on-target diagnosis of a persistent
    failure to connect after change-9c2f41d8 was deployed. The
    reconnect loop worked correctly; every attempt failed with
    [Errno 16] Device or resource busy, and the logs gave no way to
    tell that from an absent peer.

    Host diagnosis established that the Bluetooth controller itself was
    wedged. That is not a condition GTach can repair, but GTach could
    not report it either, which is what this issue addresses.

affected_scope:
  components:
    - name: "RFCOMMTransport._open"
      file_path: "src/gtach/comm/rfcomm.py"
    - name: "OBDTransport.connect / reconnect_indefinitely"
      file_path: "src/gtach/comm/transport.py"
    - name: "DisplayManager DISCONNECTED screen"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: "GTach on gtach.local with the Bluetooth controller in a wedged state."
  steps:
    - "Start GTach with no working Bluetooth controller."
    - "Observe debug.log: 'Failed to connect ... [Errno 16] Device or resource busy' every 5 s indefinitely."
    - "Observe the display: the DISCONNECTED screen, identical to the screen shown when the OBD adapter is merely out of range."
  frequency: "always"
  reproducibility_conditions: >
    Deterministic given the host condition. The logging and display
    behaviour follow from source and do not vary.
  test_data: >
    debug.log, 12:55 run (pid 1645): 10 x "[Errno 16] Device or
    resource busy", 2 x "timed out", 0 successes, from the first
    attempt at 12:55:12.447 onward. No connection was ever established,
    so no link-loss path was exercised.

    Host state on gtach.local during the run:

      pgrep -a gtach   -> 1645 only; matches systemd Main PID. No
                          surviving second instance.
      hcitool con      -> "< ACL DC:A6:32:54:AD:77 handle 12 state 9
                          lm SLAVE AUTH ENCRYPT". State 9 is BT_CLOSED
                          in BlueZ's connection-state enum: the link
                          was already closed yet its handle had not
                          been reaped.
      hcitool dcc      -> "Disconnect failed: Connection timed out".
      hciconfig hci0 down && hciconfig hci0 up
                       -> "Can't init device hci0: Connection timed
                          out (110)". The down succeeded; the up did
                          not. The controller could not be brought
                          back.
      hcitool con      -> empty, the device now being down.

    The zombie ACL was therefore a symptom of a wedged HCI controller,
    not its cause. Recovery is a host operation — on Raspberry Pi OS,
    restarting hciuart.service to re-attach the chip, or a reboot.

    Source, rfcomm.py:45-49 — _open creates the socket, sets a
    timeout, and calls connect(). If connect() raises, the socket is
    never closed. transport.connect()'s handler calls
    _discard_handle(), but self._handle was never assigned, so nothing
    closes it; only refcounting reclaims it.

    Source — grep for 'errno' across src/gtach/comm/ returns nothing.
    Every OSError is caught by the same handler and logged with the
    same message.
  error_output: >
    "RFCOMMTransport ERROR Failed to connect to RFCOMM device
    DC:A6:32:54:AD:77 on channel 1: [Errno 16] Device or resource
    busy", followed by "Failed to connect, retrying in 5.0 seconds...",
    every 5 s, indefinitely. Identical in form to the message produced
    when the peer is simply absent.

behavior:
  expected: >
    A failure the operator can act on should be distinguishable from
    one they cannot. An absent OBD adapter, a wedged link and a missing
    Bluetooth controller are three different conditions with three
    different responses.

    A socket that fails to connect should be closed.
  actual: >
    DEFECT 1, CONFIRMED. RFCOMMTransport._open (rfcomm.py:45-49)
    creates a socket and abandons it when connect() raises. The socket
    is a local; OBDTransport.connect()'s except handler calls
    _discard_handle(), but self._handle was never assigned. The
    descriptor is released only when refcounting happens to reclaim it.
    An unclosed RFCOMM socket holds its ACL reference, which is a
    credible route into the closed-but-unreaped link observed on
    target. Not proven to be the cause of this instance — the first
    attempt of a fresh process already failed — but a defect on its own
    terms and on exactly the paths that precede this state.

    DEFECT 2, CONFIRMED. No code in src/gtach/comm/ inspects
    OSError.errno. connect() catches _IO_ERRORS and logs one message
    for all of them. EBUSY (link or channel wedged), ETIMEDOUT,
    EHOSTDOWN (peer absent) and ENODEV (no controller) are
    indistinguishable in the log and identical on the display. The
    operator sees the same DISCONNECTED screen whether the dongle is
    out of range or the Pi's Bluetooth chip has stopped responding.
  impact: >
    Diagnostic. In this instance it cost a full on-target session and
    three rounds of manual hcitool work to establish what one errno
    would have said. In a vehicle it is worse: an adapter fault and an
    unplugged dongle present identically, so the driver cannot tell a
    fixable problem from a fault.

    Severity high on diagnostic grounds rather than functional: the
    application behaves correctly given the host condition.
  workaround: >
    Read the errno from the log message by hand, and run hcitool con
    and hciconfig on the target to establish controller state.

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "BlueZ / hci_uart (BCM43438)"
      version: "n/a"
  domain: "domain_1"

analysis:
  root_cause: >
    ITERATION 2 PREAMBLE. Iteration 1 is implemented and deployed;
    "[Errno 16] Device or resource busy (bluetooth link busy - may need
    reset)" is confirmed in the 13:43 and 13:44 logs. Three gaps in
    that delivery were found on review and in the logs. The iteration 1
    analysis below is retained unaltered.

    GAP 1, CONFIRMED — the cause goes blank in the failure mode
    change-9c2f41d8 exists to handle. _last_failure_cause is written
    only by connect() failing. A link that connects cleanly and then
    dies of silence is torn down by drop_link(), which sets no cause,
    so the operator is shown DISCONNECTED with nothing to explain it.
    The one screen that most needs a reason has none in precisely the
    case the reconnection work was built for.

    GAP 2, CONFIRMED — the adapter probe detects an ABSENT controller,
    not a WEDGED one. _bluetooth_adapter_present tests for an entry
    under /sys/class/bluetooth. A controller that is listed but will
    not initialise — gtach.local's state when hciconfig hci0 up
    returned ETIMEDOUT — still satisfies that test, so the cause falls
    through to the errno mapping and no controller fault is reported.
    Confirmed from the logs: 'no bluetooth controller' has never been
    reported in any run, across 44 EBUSY, 42 host-down and 13
    timed-out failures.

    GAP 3, CONFIRMED, COSMETIC — a duplicated suffix. socket.timeout
    carries errno None, so _classify_connect_error falls through to
    str(exc), which for that exception is the text already present in
    the log message. The result is
    "channel 1: timed out (timed out)", observed 4 times.

    ITERATION 1 ANALYSIS, RETAINED. The transport treats every OSError
    as one condition. errno is the
    information that distinguishes them and it is discarded at the
    point it arrives. Nothing downstream can recover it, so neither the
    log nor the display can say more than "failed".

    Separately, the failure path in _open has no cleanup. The success
    path returns the socket and hands ownership to connect(); the
    failure path simply propagates the exception, leaving the socket
    owned by nobody.
  technical_notes: >
    The evidence needed is cheap and already precedented in this
    codebase. errno is an attribute of the exception already caught.
    Controller presence is readable from sysfs — PlatformDetector
    already probes /sys/class/bluetooth (platform.py:706) alongside
    /sys/class/gpio and /sys/class/graphics/fb0. No subprocess, no root
    requirement, no new dependency.

    Shelling out to hcitool or hciconfig to gather the same information
    should be avoided: it parses human-readable output, requires root,
    and cannot be exercised on the development platform.

    Whether GTach should attempt RECOVERY as well as reporting — an
    adapter reset, an rfkill cycle, restarting hciuart — is a separate
    question and a real expansion of the application's remit. The
    on-target evidence argues for caution: `hciconfig hci0 down`
    succeeded and `up` then failed, leaving the controller in a worse
    state than before the attempt. An automated equivalent would have
    done the same thing unattended, in a vehicle. This issue therefore
    proposes reporting only, and leaves recovery to be decided
    separately and by consensus.
  related_issues:
    - issue_ref: "issue-9c2f41d8"
      relationship: >
        Parent context. Its fix works — the reconnect loop retried
        correctly throughout — but its link-loss path was never
        exercised, because no connection was ever established. That
        issue remains active pending a reproduction with a working
        controller.
    - issue_ref: "issue-4d9e2f18"
      relationship: >
        related. Established the DISCONNECTED condition from data
        recency. This issue proposes distinguishing WHY the link is
        absent, which that condition does not currently carry.
    - issue_ref: "issue-b3d7e2f1"
      relationship: >
        related. Serial transport ELM327 probing; the same
        undifferentiated-OSError treatment applies there.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    ITERATION 2. Three further corrections, still reporting only.

    4. Set a cause in drop_link(). It already takes _lock and already
    sets DISCONNECTED; recording a cause alongside is one assignment.
    The cause names sustained silence from the adapter rather than a
    failed connect, since that is what happened.

    5. Detect a wedged controller by consecutive-failure escalation
    rather than by probing for one. After a small number of
    consecutive connect failures with the adapter present, escalate the
    cause to name a probable controller wedge needing a reset. This
    reuses evidence already held and mirrors the consecutive-timeout
    pattern change-9c2f41d8 established in the same module. The
    alternative — reading the real HCI_UP flag by ioctl on an
    AF_BLUETOOTH/BTPROTO_HCI socket — is more truthful but adds struct
    packing and an ioctl that cannot be exercised on the development
    platform, and was rejected on the project's stated preference for
    technical simplicity.

    6. Suppress the duplicated suffix. When the resolved cause is
    identical to the exception text already in the message, do not
    append it.

    ITERATION 1 APPROACH, RETAINED. Three corrections, reporting only.

    1. Close the socket on every failure path in
    RFCOMMTransport._open. Wrap the connect in try/except, close the
    socket, re-raise unchanged so the caller's handling is unaffected.

    2. Classify connect failures by errno. Map the errnos that matter —
    EBUSY, ETIMEDOUT, EHOSTDOWN, EHOSTUNREACH, ENODEV, ENETDOWN — to a
    short cause description, log it alongside the existing message, and
    record the last failure cause on the transport so consumers can
    read it.

    3. Distinguish "no controller" from "no peer". On a connect
    failure, check /sys/class/bluetooth for an adapter, as
    PlatformDetector already does, and surface the resulting cause on
    the DISCONNECTED screen as a short status line beneath the existing
    affordances.

    Explicitly NOT proposed: any automated recovery action. See
    analysis.technical_notes.
  change_ref: ""
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
    Where an error carries a discriminator, discard it only
    deliberately. errno was available at every one of these failures
    and was thrown away at the first handler.
  process_improvements: >
    A resource created inside a function that can raise should be
    closed on the raising path, not left to refcounting.

verification_enhanced:
  verification_steps:
    - "Confirm from source that _open abandons its socket when connect() raises. [DONE.]"
    - "Confirm that no code in src/gtach/comm/ inspects OSError.errno. [DONE.]"
    - "Confirm from host output that the controller, not GTach, was the failing element: single gtach PID, ACL in state 9, hciconfig up timing out. [DONE.]"
    - "After the fix: with the peer absent, confirm the log and display report an unreachable peer."
    - "After the fix: with the controller absent or down, confirm the log and display report an adapter fault, distinctly."
    - "After the fix: confirm a failed connect leaves no socket open, by inspecting /proc/<pid>/fd across several retry cycles."
  verification_results: >
    First three steps complete, as recorded in test_data. Remaining
    steps require the fix to exist.

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  The host condition that prompted this issue is not a GTach defect and
  cannot be fixed in GTach. Recovery on gtach.local is a host
  operation — restarting hciuart.service to re-attach the chip, or a
  reboot. What this issue addresses is that GTach could not say so.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial issue document from on-target diagnosis of persistent EBUSY on gtach.local."
      - "Confirmed defect 1: RFCOMMTransport._open abandons its socket when connect() raises."
      - "Confirmed defect 2: no code in src/gtach/comm/ inspects OSError.errno, so all connect failures are reported identically."
      - "Recorded the host diagnosis: single gtach process, ACL in state 9 (BT_CLOSED) unreaped, hciconfig up timing out — a wedged controller, not an application fault."
      - "Records that automated recovery is deliberately excluded pending a separate decision, on the evidence that a manual down/up left the controller worse than before."
  - version: "2.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Iteration 1 -> 2. Status open -> investigating. Coupled to change-5e7a03c4 iteration 2."
      - "Iteration 1 confirmed working on target: the classified cause appears in the 13:43 and 13:44 logs."
      - "GAP 1: _last_failure_cause is written only by connect() failing, so a link torn down by drop_link() leaves the DISCONNECTED screen with no explanation — in exactly the failure mode change-9c2f41d8 addresses."
      - "GAP 2: the sysfs probe detects an absent controller, not a wedged one. 'no bluetooth controller' has never been reported across 44 EBUSY, 42 host-down and 13 timed-out failures, despite the controller having been unable to initialise."
      - "GAP 3: socket.timeout carries errno None, so the fallback appends text already present in the message, producing 'timed out (timed out)' 4 times."
      - "Resolution extended with items 4-6. Wedge detection by consecutive-failure escalation, the HCI ioctl alternative recorded as rejected on simplicity grounds."
      - "Operator-initiated Bluetooth reset from the DISCONNECTED screen is NOT part of this iteration. It requires privileged host access and an action not yet established to work on this hardware; it will be raised separately once the working command is known."

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
| 1.0 | 2026-08-12 | Initial issue document. Failed sockets are not closed in RFCOMMTransport._open, and all connect failures are reported identically because errno is discarded. Automated recovery deliberately excluded from the proposed scope. |
| 2.0 | 2026-08-12 | Iteration 1 -> 2. Iteration 1 confirmed working on target. Three gaps recorded: no cause is set by drop_link, the probe detects an absent rather than a wedged controller, and a duplicated suffix appears for errno-less timeouts. Resolution extended with consecutive-failure wedge escalation. |

---

Copyright (c) 2026 William Watson. MIT License.
