Created: 2026 August 12

# Issue: No Operator Recovery From a Wedged Bluetooth Adapter

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-8a63d5f1"
  title: "GTach can now diagnose a wedged Bluetooth adapter but offers the operator no way to act on it; the DISCONNECTED screen reports 'bluetooth wedged - reset required' and provides no means of performing that reset"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "human_request"
  test_ref: ""
  description: >
    Requested 2026-08-12 by William. change-5e7a03c4 iteration 2 is
    deployed and correctly escalates sustained connect failures to
    "bluetooth wedged - reset required", observed 17 times in the
    pulled logs. The screen now names an action the operator has no way
    to perform without an SSH session.

affected_scope:
  components:
    - name: "DisplayManager DISCONNECTED screen (free button slot)"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication (worker dispatch for the reset)"
      file_path: "src/gtach/app.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: "GTach running with the Bluetooth adapter in a wedged state."
  steps:
    - "Observe the DISCONNECTED screen after ~30 s of failed connects."
    - "Read the cause line: 'bluetooth wedged - reset required'."
    - "Observe that the screen offers only Setup, and the slot beside it is empty (change-4f1e82b7)."
  frequency: "always"
  reproducibility_conditions: "Deterministic once the escalation threshold is crossed."
  test_data: >
    Cause strings observed across the pulled logs:

      49  [Errno 16] Device or resource busy (bluetooth link busy - may need reset)
      44  [Errno 16] Device or resource busy          (pre-iteration-2)
      40  [Errno 112] Host is down
      17  [Errno 16] Device or resource busy (bluetooth wedged - reset required)
      12  timed out
       7  timed out (timed out)                        (pre-iteration-2)

    change-4f1e82b7 is deployed: _draw_retry_arc and
    _retry_interval_callback are present in manager.py, and no
    disconnected_simulate region remains. The lower button slot is free
    and was left free deliberately, pending this issue.

    IMPORTANT NEGATIVE EVIDENCE. The condition survives a full reboot
    of gtach.local. stacks.log headers show pid 720 at 14:52:37 and
    pid 671 at 14:56:32 — a decreasing pid, so the host rebooted
    between them. start.log shows the new run beginning 14:55:53, and
    debug.log shows the same [Errno 16] failures resuming immediately
    from 14:56:50 and escalating to the wedge diagnosis by 14:57:40.

    A reboot resets the controller, reloads the driver and clears every
    kernel structure. That the condition survives it means a local
    adapter reset — which is strictly weaker than a reboot — cannot be
    expected to clear THIS instance. The fault most likely lies off
    gtach.local, on the ELM327 emulator or in the pairing state.

    Only one "Connected to" line exists across all retained logs.
  error_output: "None. The application is behaving correctly; it simply cannot act."

behavior:
  expected: >
    Where GTach names a corrective action, the operator should be able
    to take it from the screen that names it.
  actual: >
    The cause line instructs a reset. The screen has one button,
    Setup, whose purpose is re-pairing. Performing the reset requires
    SSH to gtach.local and manual hciconfig or systemctl work, which is
    not available to a driver.
  impact: >
    Operational. In a vehicle, an adapter that wedges leaves the
    tachometer dead with an on-screen instruction the driver cannot
    follow.

    Severity medium, and deliberately not higher, because the evidence
    above indicates the button will not resolve the failure currently
    being experienced. It addresses a different and narrower class of
    wedge — a stale local ACL, of the kind observed on this host at
    13:xx before the reboot, where hcitool con showed a connection in
    state 9 (BT_CLOSED) with its handle unreaped.
  workaround: "SSH to gtach.local and reset the adapter by hand."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "BlueZ / hci_uart (BCM43438)"
      version: "n/a"
  domain: "domain_1"

analysis:
  root_cause: >
    Not a defect. GTach's diagnostic capability advanced ahead of its
    remedial capability: change-5e7a03c4 taught it to name a wedge, and
    nothing was added to let the operator clear one.
  technical_notes: >
    This reverses a constraint set deliberately in change-5e7a03c4,
    which excluded all host action and forbade subprocess use. That
    exclusion was argued against UNATTENDED recovery: an automated
    down/up that fails leaves the controller dead with nobody watching,
    and on this host a manual attempt did exactly that — `hciconfig
    hci0 down` succeeded and `up` returned ETIMEDOUT. An
    operator-initiated action is a different proposition: intentional,
    observed, and recoverable by reboot. The reversal is therefore
    scoped strictly to a button press and must not be extended to any
    automatic trigger.

    Four constraints follow from the earlier evidence, and none is
    optional:

    1. The reset must not run on the display thread. 'display' is a
    watchdog critical thread at a 45 s timeout; a synchronous
    subprocess call from a touch callback blocks the display loop, and
    since change-2ac1c602 that terminates the process. It must be
    dispatched to a worker.

    2. It must never leave the adapter down. The manual attempt on this
    host did precisely that. A sequence that brings the adapter down
    must bring it back up or report loudly that it could not.

    3. It must be bounded and it must report. A timeout on the
    operation, and the outcome written to the cause line the operator
    is already reading.

    4. It must be debounced. A second press while the first is running
    must be ignored, not queued.

    On the action itself: `hciconfig hci0 reset` is preferable to
    `down` followed by `up`, being a single controller reset that does
    not pass through a state where the adapter is administratively
    down. `systemctl restart hciuart` re-attaches the chip and is
    heavier; it should not be the first action, and arguably should not
    be in the application at all.
  related_issues:
    - issue_ref: "issue-5e7a03c4"
      relationship: >
        Parent. Its iteration 2 produces the wedge diagnosis this issue
        gives the operator a response to. Its exclusion of host action
        is reversed here, for operator-initiated action only.
    - issue_ref: "issue-4f1e82b7"
      relationship: >
        blocked_by. Removed the duplicate Simulate button and left the
        slot free for exactly this control.
    - issue_ref: "issue-2ac1c602"
      relationship: >
        related. Its watchdog termination path is why the reset must
        not block the display thread.
    - issue_ref: "issue-9c2f41d8"
      relationship: >
        related. Its reconnect loop is what will pick the link up again
        if a reset succeeds; no additional reconnect trigger is needed.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Add a Bluetooth Reset button in the free slot on the DISCONNECTED
    screen, below Setup.

    On press: disable the control, write a progress cause, and dispatch
    to a worker thread. The worker runs `hciconfig hci0 reset` with a
    bounded timeout, then confirms the adapter is up, attempting a
    single `hciconfig hci0 up` if it is not. It writes the outcome to
    the cause line and re-enables the control. The existing reconnect
    loop picks the link up without further prompting.

    Invoked as a fixed argument list with an absolute path, never
    through a shell. No operator input reaches the command line.

    Explicitly not proposed: any automatic invocation, on any trigger,
    including repeated wedge diagnoses. The button is the only route.

    The evidence says this will not fix the failure currently on
    gtach.local, which survived a reboot. That is recorded in
    behavior.impact so the button is not later judged against a problem
    it was never scoped to solve. Locating the current fault is a
    separate investigation, most probably on the ELM327 emulator.
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
    Where a diagnostic names a corrective action, check whether the
    operator can perform it from where they are standing.
  process_improvements: >
    A condition that survives a reboot should be diagnosed off-host
    before host-side remedies are built for it.

verification_enhanced:
  verification_steps:
    - "Confirm the wedge diagnosis is produced on target. [DONE — 17 occurrences.]"
    - "Confirm the DISCONNECTED slot is free. [DONE — change-4f1e82b7 deployed, no disconnected_simulate region.]"
    - "Confirm the condition survives a reboot. [DONE — decreasing pid across stacks.log headers, failures resuming immediately on the new run.]"
    - "After the change: press the button and confirm the display loop keeps rendering and the arc keeps animating throughout."
    - "After the change: confirm the outcome is written to the cause line, for both success and failure."
    - "After the change: confirm a second press during a reset is ignored."
    - "After the change: confirm that if the reset fails, the adapter is not left administratively down."
    - "After the change: confirm no watchdog warning is logged for the display thread during a reset."
  verification_results: "First three steps complete. Remainder require the change to exist."

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  The reversal of change-5e7a03c4's no-host-action constraint is
  deliberate and bounded. It applies to an operator pressing a button
  and to nothing else. Any future proposal to invoke this
  automatically should be treated as a new scope decision, not as an
  extension of this one.

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
      - "Initial issue document from user request for an operator-initiated Bluetooth reset."
      - "Records that change-5e7a03c4 iteration 2 produces the wedge diagnosis on target, 17 occurrences."
      - "Records the negative evidence that the current condition survives a full reboot of gtach.local, so a local adapter reset cannot be expected to clear it; the button addresses a narrower class of wedge."
      - "Records the four constraints carried forward from earlier evidence: off the display thread, never leave the adapter down, bounded and reported, debounced."
      - "Records that change-5e7a03c4's exclusion of host action is reversed for operator-initiated action only."

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
| 1.0 | 2026-08-12 | Initial issue document. GTach names a required reset the operator cannot perform. Records that the present condition survives a reboot, so the button addresses a narrower class of wedge than the one currently being experienced. |

---

Copyright (c) 2026 William Watson. MIT License.
