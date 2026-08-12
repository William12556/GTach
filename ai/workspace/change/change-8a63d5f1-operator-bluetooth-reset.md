Created: 2026 August 12

# Change: Operator-Initiated Bluetooth Reset From the DISCONNECTED Screen

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-8a63d5f1"
  title: "Add a Bluetooth Reset button to the free slot on the DISCONNECTED screen, dispatching a bounded, debounced hciconfig reset to a worker thread and reporting its outcome on the existing cause line"
  date: "2026-08-12"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-8a63d5f1"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-8a63d5f1"
  description: >
    Resolves issue-8a63d5f1. The DISCONNECTED screen reports
    "bluetooth wedged - reset required" and offers no means of
    performing that reset.

scope:
  summary: >
    One new button in the slot change-4f1e82b7 left free, one worker
    dispatch in app.py, and one new module owning the reset operation.
    The reset is operator-initiated only, runs off the display thread,
    is bounded and debounced, and reports its outcome on the existing
    cause line.
  affected_components:
    - name: "DisplayManager._register_disconnected_regions / _render_disconnected"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication._on_bluetooth_reset (worker dispatch)"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "bluetooth_reset module"
      file_path: "src/gtach/utils/bluetooth_reset.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "ANY automatic invocation of the reset, on any trigger, including a repeated wedge diagnosis, a retry count, or application startup. The button is the only route. This is the boundary that makes the change acceptable at all."
    - "systemctl restart hciuart and kernel module reloads. Heavier than a controller reset and further outside the application's remit; not a first action and arguably not an in-application action."
    - "Diagnosing the condition currently affecting gtach.local. It survives a reboot, so it is not addressable by a controller reset; that investigation is separate and most probably belongs on the ELM327 emulator."
    - "src/gtach/comm/. The reconnect loop delivered by change-9c2f41d8 picks the link up on its own once the adapter recovers; no reconnect trigger is added."
    - "The retry-countdown arc and the Setup button, both unchanged."
    - "Making the reset available from OPTIONS. One entry point, on the screen that names the problem."

rational:
  problem_statement: >
    change-5e7a03c4 iteration 2 is deployed and escalates sustained
    connect failures to "bluetooth wedged - reset required", observed
    17 times. change-4f1e82b7 is deployed and left the lower button
    slot free. The screen names an action and provides no way to take
    it; performing it requires SSH, which a driver does not have.
  proposed_solution: >
    EDIT X — a new module, src/gtach/utils/bluetooth_reset.py, owning
    the operation. A single function runs `hciconfig hci0 reset` as a
    fixed argument list with an absolute path and a bounded timeout,
    then confirms the adapter is up, attempting one `hciconfig hci0 up`
    if it is not. It returns a short outcome string suitable for the
    cause line, and never raises.

    EDIT Y — GTachApplication._on_bluetooth_reset. Debounced by a
    threading.Event: a press while a reset is in flight is ignored, not
    queued. It writes a progress cause, dispatches the operation to a
    daemon worker thread, and on completion writes the outcome and
    clears the debounce.

    EDIT Z — the button. Register 'disconnected_bt_reset' in the free
    slot beneath Setup, via the existing _button_column, and draw it.
    Its callback reaches the application through a
    _bluetooth_reset_callback attribute wired in app.py, following the
    established pattern of _link_cause_callback and
    _retry_interval_callback.

    The four constraints from earlier evidence are all structural
    here, not advisory: the worker thread satisfies the first, the
    up-after-reset step the second, the subprocess timeout the third,
    and the Event the fourth.
  alternatives_considered:
    - option: "Run the reset synchronously from the touch callback."
      reason_rejected: >
        'display' is a watchdog critical thread at a 45 s timeout. A
        synchronous subprocess blocks the display loop, and since
        change-2ac1c602 a critical timeout terminates the process. The
        button would restart the application.
    - option: "hciconfig hci0 down followed by hciconfig hci0 up."
      reason_rejected: >
        Exactly the sequence attempted manually on this host: down
        succeeded, up returned ETIMEDOUT, and the controller could not
        be brought back. `reset` is a single operation that does not
        pass through an administratively-down state.
    - option: "systemctl restart hciuart."
      reason_rejected: >
        Re-attaches the chip over UART; heavier, slower, and a service
        management action rather than a device one. Held in reserve if
        `reset` proves insufficient in the field.
    - option: "Trigger the reset automatically after N wedge diagnoses."
      reason_rejected: >
        The whole basis for permitting host action here is that an
        operator is present, watching, and can reboot if it goes wrong.
        Automatic invocation removes every part of that and reinstates
        the risk change-5e7a03c4 excluded.
    - option: "Also offer the reset from the OPTIONS screen."
      reason_rejected: >
        Two entry points to a privileged action for no gain. The
        DISCONNECTED screen is where the diagnosis appears.
  benefits:
    - "The operator can act on the instruction the screen gives them."
    - "The action is bounded, debounced and reported, so a failed reset is visible rather than silent."
    - "The reconnect loop resumes on its own if the reset succeeds; nothing further is needed."
    - "The privileged surface is one function in one module, easy to review and easy to remove."
  risks:
    - risk: >
        The reset fails and leaves the adapter administratively down,
        as the manual attempt on this host did.
      mitigation: >
        The operation confirms the adapter is up afterwards and
        attempts one `up` if not. If that fails, the outcome string
        says so explicitly rather than reporting a bland failure, so
        the operator knows a reboot is required.
    - risk: "The subprocess hangs."
      mitigation: >
        A timeout on each invocation, and an overall bound. On timeout
        the process is killed and the outcome reports it.
    - risk: >
        The button raises expectations it cannot meet on the condition
        currently affecting gtach.local.
      mitigation: >
        Recorded, not engineered around. That condition survives a
        reboot and is therefore outside what a controller reset can
        address. issue-8a63d5f1 records this in behavior.impact so the
        button is not judged against a problem it was never scoped to
        solve.
    - risk: "hciconfig is absent or at a different path."
      mitigation: >
        Resolved once via shutil.which with a documented fallback to
        /usr/bin/hciconfig. When it cannot be found, the button reports
        that rather than failing obscurely, and the operation is a
        no-op.
    - risk: "The application does not run as root and the reset is refused."
      mitigation: >
        bin/gtach.service specifies User=root, so it does today. A
        permission failure is reported in the outcome string rather
        than raising.
    - risk: "Introducing subprocess to the codebase invites its wider use."
      mitigation: >
        Confined to one module whose name states its purpose, invoked
        from one call site behind one button. The prohibition on
        subprocess elsewhere in src/gtach/comm/ stands and remains a
        success criterion of change-5e7a03c4.

technical_details:
  current_behavior: >
    The DISCONNECTED screen shows one Setup button, the retry arc, and
    a cause line that may read "bluetooth wedged - reset required". No
    control performs a reset.
  proposed_behavior: >
    A second button, Bluetooth Reset, occupies the free slot. Pressing
    it writes a progress cause, runs a bounded controller reset on a
    worker thread, and writes the outcome. The display loop continues
    rendering and the arc continues animating throughout.
  implementation_approach: >
    One new small module for the privileged operation; one dispatch
    method in app.py; one button registration and one draw call in
    manager.py. subprocess is used only in the new module.
  code_changes:
    - component: "bluetooth_reset"
      file: "src/gtach/utils/bluetooth_reset.py"
      change_summary: >
        New module. reset_adapter(timeout: float) -> str runs the
        controller reset as a fixed argv list, confirms the adapter is
        up, attempts one up if not, and returns a short outcome string.
        Never raises.
      functions_affected:
        - "reset_adapter"
      classes_affected: []
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Add _bluetooth_reset_in_flight (threading.Event) and
        _on_bluetooth_reset, which debounces, writes a progress cause,
        dispatches to a daemon worker, writes the outcome and clears
        the flag. Wire _bluetooth_reset_callback on the display beside
        the existing callbacks.
      functions_affected:
        - "__init__"
        - "_on_bluetooth_reset"
        - "_start_normal_mode"
      classes_affected:
        - "GTachApplication"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Register and draw a second button, disconnected_bt_reset, in
        the free slot; add _bluetooth_reset_callback defaulting to
        None. The button is registered only when that callback is set.
      functions_affected:
        - "_register_disconnected_regions"
        - "_render_disconnected"
      classes_affected:
        - "DisplayManager"
  data_changes: []
  interface_changes:
    - interface: "DisplayManager._bluetooth_reset_callback"
      change_type: "contract"
      details: "New optional attribute, defaulting to None. When unset the button is neither registered nor drawn, so the screen degrades to its current form."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "OBDTransport.reconnect_indefinitely"
      impact: "None. It picks the link up on its own once the adapter recovers. No reconnect trigger is added."
    - component: "WatchdogMonitor"
      impact: "None, by design. The worker thread is unregistered and unmonitored; the display thread is never blocked."
  external:
    - library: "subprocess (stdlib)"
      version_change: "none"
      impact: "First use in this codebase, confined to src/gtach/utils/bluetooth_reset.py."
    - library: "hciconfig (BlueZ)"
      version_change: "none"
      impact: "External command invoked by absolute path with a fixed argument list."
  required_changes:
    - change_ref: "change-4f1e82b7"
      relationship: "blocked_by. Freed the button slot this change fills."
    - change_ref: "change-5e7a03c4"
      relationship: "blocked_by. Produces the wedge diagnosis and owns the cause line the outcome is written to."

testing_requirements:
  test_approach: >
    Unit tests against a patched subprocess for the module and a
    patched worker for the dispatch, plus on-target confirmation that
    the display keeps rendering during a reset.
  test_cases:
    - scenario: "reset_adapter where the reset command returns 0 and the adapter is up."
      expected_result: "A success outcome string; no second command run."
    - scenario: "reset_adapter where reset returns 0 but the adapter is down."
      expected_result: "One up command is run; the outcome reflects its result."
    - scenario: "reset_adapter where reset and the subsequent up both fail."
      expected_result: "An outcome that explicitly states the adapter is down and a reboot is needed."
    - scenario: "reset_adapter where the command times out."
      expected_result: "The process is killed; a timeout outcome is returned; no exception."
    - scenario: "reset_adapter where hciconfig cannot be found."
      expected_result: "An outcome saying so; no command is run; no exception."
    - scenario: "reset_adapter where the command raises PermissionError."
      expected_result: "An outcome naming the permission problem; no exception."
    - scenario: "_on_bluetooth_reset pressed once."
      expected_result: "A progress cause is written; a worker is started; the calling thread returns immediately."
    - scenario: "_on_bluetooth_reset pressed again while a reset is in flight."
      expected_result: "The second press is ignored; exactly one worker exists; nothing is queued."
    - scenario: "_on_bluetooth_reset after a completed reset."
      expected_result: "The debounce is cleared and a second press starts a new worker."
    - scenario: "The worker raising."
      expected_result: "The debounce is still cleared; an outcome is still written; no exception escapes the thread."
    - scenario: "_register_disconnected_regions with _bluetooth_reset_callback unset."
      expected_result: "Only disconnected_setup is registered; the screen is as it is today."
    - scenario: "_register_disconnected_regions with the callback set."
      expected_result: "Two regions; the Setup rect is unchanged from the one-button case."
    - scenario: "On target: press the button."
      expected_result: "The arc keeps animating and the FPS line still reports 30.0 throughout; no watchdog warning for the display thread."
  regression_scope:
    - "Setup entry from the DISCONNECTED screen."
    - "The retry-countdown arc and the cause line."
    - "The reconnect loop's cadence."
    - "Application shutdown while a reset is in flight."
    - "tests/ suite in full."
  validation_criteria:
    - "subprocess appears only in src/gtach/utils/bluetooth_reset.py."
    - "No code path invokes reset_adapter other than the button callback."
    - "shell=True appears nowhere."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDIT X — the bluetooth_reset module."
      owner: "tactical"
    - step: "EDIT Y — dispatch and debounce in app.py."
      owner: "tactical"
    - step: "EDIT Z — the button in manager.py."
      owner: "tactical"
    - step: "Unit tests per testing_requirements.test_cases items 1-12."
      owner: "tactical"
    - step: "Deploy to gtach.local; press the button and confirm the display never stalls."
      owner: "human"
  rollback_procedure: >
    Revert the commit. The privileged surface is one module which the
    revert removes entirely; the button and dispatch are localised.
  deployment_notes: >
    Requires hciconfig on the target and the service to run as root,
    both already true per bin/gtach.service. No unit change.

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
    - change_ref: "change-4f1e82b7"
      relationship: "blocked_by."
    - change_ref: "change-5e7a03c4"
      relationship: "blocked_by. This change reverses its exclusion of host action, for operator-initiated action only."
    - change_ref: "change-2ac1c602"
      relationship: "related. Its watchdog termination path is why the reset must not block the display thread."
    - change_ref: "change-9c2f41d8"
      relationship: "related. Its reconnect loop resumes the link without a trigger from this change."
  related_issues:
    - issue_ref: "issue-8a63d5f1"
      relationship: "resolves"

notes: >
  The exclusion of host action recorded in change-5e7a03c4 is reversed
  here for a button press and for nothing else. That boundary is what
  makes the change acceptable: an operator is present, watching, and
  can reboot if it goes wrong. Any later proposal to invoke this
  automatically is a new scope decision, not an extension of this one.

  The current condition on gtach.local survives a reboot and is
  therefore beyond what a controller reset can address. This change is
  not expected to fix it and should not be judged against it.

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-8a63d5f1 iteration 1."
      - "Operator-initiated Bluetooth reset: new bluetooth_reset module, debounced worker dispatch in app.py, button in the slot change-4f1e82b7 freed."
      - "Records the four structural constraints: off the display thread, never leave the adapter down, bounded and reported, debounced."
      - "Records the rejection of synchronous invocation, of down/up in place of reset, of hciuart restart as a first action, of automatic invocation, and of a second entry point on OPTIONS."
      - "Records that change-5e7a03c4's exclusion of host action is reversed for operator-initiated action only."

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
| 1.0 | 2026-08-12 | Initial change document. Operator-initiated Bluetooth reset button on the DISCONNECTED screen, dispatched to a bounded, debounced worker and reported on the cause line. |

---

Copyright (c) 2026 William Watson. MIT License.
