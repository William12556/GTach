# Change: Setup Flow — One Operation Rule, Presented Outcomes

Created: 2026 November 11

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-34781bfe"
  title: "Completions act only for the registered operation; cancellation is effective; empty, failed and fallback scans reach DEVICE_LIST; one scan per entry to DISCOVERY; probe guard; screen and async-manager corrections"
  date: "2026-11-11"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-34781bfe"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-34781bfe"
  description: "Resolves issue-34781bfe. Run 4 of proposal-71ab3751. Implements design-a3b4c5d6 v2.0."

scope:
  summary: "Seven edit groups in the setup flow files; one line in app.py; tests."
  affected_components:
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "SetupStateCoordinator"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
      change_type: "modify"
    - name: "AsyncOperationManager"
      file_path: "src/gtach/display/async_operations.py"
      change_type: "modify"
    - name: "SetupAction"
      file_path: "src/gtach/display/setup_models.py"
      change_type: "modify"
    - name: "SetupDisplayManager construction site (type: ignore removal only)"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_setup_flow.py (new)"
      change_type: "add"
  affected_designs:
    - "design-a3b4c5d6-component_display_setup_manager"
  out_of_scope:
    - "src/gtach/comm (provided by change-b4f9607a)."
    - "display/manager.py, display/touch.py and the gauge screens (run 5)."
    - "Screen geometry, fonts and colours, except the spinner fade and the removed Continue button."
    - "A manual filter toggle or manual MAC entry (removed by decision D2)."

rational:
  problem_statement: "See issue-34781bfe."
  proposed_solution: >
    PRECONDITION — design-a3b4c5d6 v2.0 is approved. Where this change
    and the design differ, stop and report; the design governs.

    EDIT A (operation rule; X01, C08, D04; design section 6.0) —
    BluetoothSetupInterface.
    (1) _active_operations maps each name ('device_discovery',
    'device_pairing', 'device_probe') to the id of the operation that
    is currently wanted. Add _is_current(name, operation_id) -> bool
    (under _ops_lock).
    (2) Every completion callback (on_discovery_complete,
    on_pairing_complete, on_probe_complete) and every callback a
    running task makes into setup state (device found, progress,
    pairing status) first checks _is_current; if the operation is no
    longer registered it returns without writing state or changing
    screen. A terminal completion removes its own registration.
    (3) Add cancel_operation(name: str) -> None: remove the
    registration under the lock; then, outside the lock, call
    async_manager.cancel_operation(id) and the back end's
    cancel_discovery() or cancel_pairing() as the name requires.
    cancel_operations() cancels every name through it.
    (4) SetupDisplayManager: the Cancel action on DISCOVERY and the
    Back action on PAIRING call cancel_operation for their operation
    before the coordinator action; stop_setup keeps using
    interface.shutdown(), which cancels through the same path.
    (5) SetupStateCoordinator.handle_setup_action: START_DISCOVERY and
    CANCEL reset the device list before the screen transition, as
    RETRY does.

    EDIT B (outcomes; D01, discovery fallback; design 4.2, 4.3, 5.2) —
    (1) A scan is started once per entry to DISCOVERY, by the code
    that handles the transition into DISCOVERY (START_DISCOVERY and
    RETRY from DEVICE_LIST), not by the setup loop's polling condition.
    The loop's branch that starts a scan when it sees DISCOVERY + IDLE
    + no devices is removed, and so is its branch that advances to
    DEVICE_LIST.
    (2) on_discovery_complete decides what follows, for the current
    operation only: devices found -> DEVICE_LIST; no device ->
    DEVICE_LIST with an empty list; failed -> DEVICE_LIST with an
    empty list and error line 'Scan failed'. When every returned
    device has device_classification UNKNOWN (the fallback of
    change-b4f9607a EDIT F) the error line is
    'No ELM327 found - showing all devices'.
    (3) _render_device_list_screen: the zero-device state draws
    'No devices found', the error line when present, and Back and
    Retry; it is reachable with an empty list.
    (4) pairing_status is IDLE on entry to DEVICE_LIST.

    EDIT C (C08; design 5.4) — _on_probe_result is covered by EDIT
    A(2) through on_probe_complete. In addition the CURRENT_DEVICE
    screen does not register the New Setup region while a probe is in
    flight, and 'new_setup' cancels a registered probe before it
    removes the stored device.

    EDIT D (C01, C02; design 5.3, 5.5) — The PAIRING screen draws no
    Continue button; the 'continue' touch action, SetupAction.NEXT
    handling and _handle_next_navigation are removed if no reference
    remains. One helper draws the eight-dot spinner for both screens
    and fades each dot by blending its colour toward the background
    colour; no alpha value is passed to pygame.draw.circle.

    EDIT E (D02, D03, O4) — AsyncOperationManager: a task receives the
    progress callback by keyword when its signature declares a
    parameter named progress_callback (inspect.signature at submit
    time); the inspection of local-variable names is removed.
    discovery_task and pairing_task rename progress_callback_inner to
    progress_callback and stop shadowing the closure variable. A
    finished operation and its progress callback are removed from the
    manager's maps after its completion callback has run;
    cleanup_completed_operations is deleted if it then has no purpose.
    cancel_operation keeps cancelling PENDING operations and returns
    False for RUNNING ones (the interface rule makes those harmless).
    SetupDisplayManager.render draws uncached screens directly onto
    the target surface; cached screens keep their own surface.

    EDIT F (A09 interface part; B02 setup part) — on_pairing_complete
    uses save_device()'s result: on False it sets pairing_status
    FAILED with error line 'Device not saved' and does not verify or
    complete. SetupDisplayManager gains the read-only attribute
    adapter_reset_in_session: bool, False at construction and set True
    when verify_obd_connection sent ATZ and received a reply in this
    manager's lifetime (not on the simulation pass-through, not on the
    stored-device probe, not on Cancel).

    EDIT G (Optional surface) — SetupDisplayManager.__init__ accepts
    Optional['pygame.Surface'] for its surface and render() returns
    without drawing when neither it nor target_surface is available.
    In app.py the type: ignore and the two TODO: issue-ac11505d
    comments at the SetupDisplayManager construction are removed. This
    is the only edit outside the setup flow files.

    COMMENT RULE — In every file edited, comments that narrate history
    are reduced to the current behaviour plus at most one issue
    reference (CLAUDE.md section 4).
  alternatives_considered:
    - option: "Three separate patches for X01, C08 and D04."
      reason_rejected: "They share one cause (W2); one rule is smaller and covers future operations."
    - option: "Make running operations interruptible in AsyncOperationManager."
      reason_rejected: "A blocking Bluetooth call cannot be interrupted; ignoring its completion is sufficient."
    - option: "Keep the setup loop's polling condition and add branches for the empty and failed cases."
      reason_rejected: "Keeps two places deciding the same thing; the endless rescan came from that split."
  benefits:
    - "Every scan outcome is shown and can be retried."
    - "Stale completions cannot change state or screen."
    - "The application knows whether the adapter was reset (B02)."
  risks:
    - risk: "A path that relied on the loop to start discovery no longer starts it."
      mitigation: "Success criterion: every transition into DISCOVERY starts exactly one scan; test per entry path."
    - risk: "A completion is dropped because its registration was removed too early."
      mitigation: "Registration is removed only by cancel and by the terminal completion itself; tests for normal completion of all three operations."
    - risk: "Regression in the simbt path."
      mitigation: "tests/test_lifecycle_sim.py and device session B."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "design-a3b4c5d6 v2.0 sections 4.0 to 6.0."
  implementation_approach: "Restructure of the completion and cancel paths inside the existing classes; no new class."
  code_changes:
    - component: "display setup"
      file: "setup.py, setup_components/bluetooth/interface.py, setup_components/state/coordinator.py, async_operations.py, setup_models.py"
      change_summary: "EDITS A to G"
      functions_affected:
        - "BluetoothSetupInterface.start_discovery"
        - "BluetoothSetupInterface.start_pairing"
        - "BluetoothSetupInterface.start_device_probe"
        - "BluetoothSetupInterface.cancel_operations"
        - "BluetoothSetupInterface.cancel_operation (new)"
        - "BluetoothSetupInterface._is_current (new)"
        - "SetupDisplayManager._setup_loop"
        - "SetupDisplayManager._handle_touch_action"
        - "SetupDisplayManager.render"
        - "SetupDisplayManager._render_discovery_screen"
        - "SetupDisplayManager._render_device_list_screen"
        - "SetupDisplayManager._render_pairing_screen"
        - "SetupDisplayManager._render_current_device_screen"
        - "SetupStateCoordinator.handle_setup_action"
        - "AsyncOperationManager.submit_operation"
        - "AsyncOperationManager._worker_loop"
      classes_affected: []
    - component: "app"
      file: "src/gtach/app.py"
      change_summary: "EDIT G: comment and type: ignore removal at one call"
      functions_affected:
        - "GTachApplication._start_setup_mode"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "SetupDisplayManager.adapter_reset_in_session"
      change_type: "contract"
      details: "New bool attribute read by GTachApplication._start_obd (change-042dd7ff)."
      backward_compatible: "yes"
    - interface: "AsyncOperationManager task signature"
      change_type: "contract"
      details: "Progress callback passed by keyword to a declared progress_callback parameter."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-b4f9607a"
      relationship: "precedes; provides the fallback result, effective cancel_pairing and the save_device result"
    - change_ref: "change-042dd7ff"
      relationship: "precedes; reads adapter_reset_in_session"
    - change_ref: "change-cfa4e617"
      relationship: "precedes; removes the manual-entry and filter-toggle code"

testing_requirements:
  test_approach: "Unit tests with a stub async manager, a stub pairing back end and a real SetupStateCoordinator; pygame with the dummy video driver."
  test_cases:
    - scenario: "Discovery completes with two ELM327 devices."
      expected_result: "DEVICE_LIST with two devices; no error line."
    - scenario: "Discovery completes with no device."
      expected_result: "DEVICE_LIST, empty list, 'No devices found' drawn, Back and Retry regions registered; no second scan is submitted during 2 s of setup-loop cycles."
    - scenario: "Discovery fails."
      expected_result: "DEVICE_LIST with error line 'Scan failed'; no second scan."
    - scenario: "Discovery returns only UNKNOWN-classified devices."
      expected_result: "DEVICE_LIST listing them with error line 'No ELM327 found - showing all devices'."
    - scenario: "Each entry into DISCOVERY (Start Setup, Retry from DEVICE_LIST)."
      expected_result: "Exactly one discovery operation is submitted."
    - scenario: "Cancel on DISCOVERY, then the abandoned scan completes with devices and with an error."
      expected_result: "cancel_discovery called once; screen stays WELCOME; device list empty; no error message."
    - scenario: "A device-found callback from a cancelled scan."
      expected_result: "No device is added."
    - scenario: "Back on PAIRING while pairing runs, then pairing completes successfully."
      expected_result: "cancel_pairing called; no save_device call; screen unchanged by the completion."
    - scenario: "Continue on CURRENT_DEVICE, New Setup region while the probe runs."
      expected_result: "The New Setup region is not registered."
    - scenario: "Probe completes after the screen left CURRENT_DEVICE through a cancelled registration."
      expected_result: "No complete_setup; no transition."
    - scenario: "PAIRING screen with status SUCCESS."
      expected_result: "No 'continue' region."
    - scenario: "Spinner helper at eight phases on a surface without per-pixel alpha."
      expected_result: "The eight dots have at least three distinct colours."
    - scenario: "A task declaring progress_callback reports progress."
      expected_result: "The operation's progress and message are updated; a task without the parameter is called without it."
    - scenario: "Ten operations complete."
      expected_result: "The manager's operation and callback maps are empty afterwards."
    - scenario: "Pairing succeeds and save_device returns False."
      expected_result: "Status FAILED, error line 'Device not saved', verify_obd_connection not called."
    - scenario: "adapter_reset_in_session after: construction; a successful real verification (stub transport answering ATZ); the simulation pass-through; a stored-device probe."
      expected_result: "False, True, False, False."
    - scenario: "SetupDisplayManager constructed with surface None, render() without a target."
      expected_result: "No exception."
    - scenario: "START_DISCOVERY and CANCEL with a stale device list, observed through a state-change callback."
      expected_result: "The list is empty before the new screen is announced."
  regression_scope:
    - "tests/test_medium_defects.py, tests/test_device_list_focus.py, tests/test_setup_and_gauge.py, tests/test_setup_lock_order.py, tests/test_callbacks_outside_locks.py, tests/test_lifecycle_sim.py."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes; mypy src/ reports no issues."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to G and tests."
      owner: "tactical"
    - step: "Device session B: setup end to end, empty scan, cancel during scan, New Setup during probe, simbt."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: "2026-11-12"
  implemented_by: "Claude Code"
  verification_date: "2026-11-12"
  verified_by: "William Watson"
  test_results: "Commit c8901f50feec06824916813f496a667bd4e68dfc: pytest 694 passed (40 new in tests/test_setup_flow.py); mypy src/ no issues (worker's results, report-34781bfe section 7). Removing the _is_current checks made six new tests fail (mutation check). Device session B (2026-11-12, test-71ab3751-device-session-b): B2 one scan per tap, no Continue, ATZ skipped after pairing; B3 probe completes, stored device kept; B4 three cancels, completions ignored, WELCOME unchanged; B5 no rescan, fallback list with notice; B8 simulated setup completes. Not observable on device: New Setup hidden during a 0.9 s probe, and an empty device list (named devices always in range); unit tests cover both."
  issues_found:
    - "EDIT A: the closures hold a registration id issued by the interface before submit, not the async manager's id, because submit_operation cannot be given an id and may complete before it returns. The async id is kept separately for cancellation. Accepted."
    - "EDIT B(1): Retry now depends on the screen (scan on DEVICE_LIST, pairing on PAIRING); previously Retry on DEVICE_LIST could pair a leftover selected device. Accepted."
    - "EDIT B(4): pairing_status is reset on every entry to DEVICE_LIST, not only after a scan. Accepted."
    - "EDIT C: New Setup is neither drawn nor registered while the probe runs; a one-frame render-cache window can still show it, and new_setup then cancels the probe. Accepted."
    - "cancel_operations() no longer calls cancel_discovery() and cancel_pairing() unconditionally; shutdown() still sets both back-end cancel events through pairing.shutdown()."
    - "The discovery task checks _is_current after its 2 s settle delay, so a Cancel during the delay prevents the 36 s scan."
    - "In simbt sessions all fake devices are unclassified, so DEVICE_LIST shows the fallback notice; fix belongs in comm/sim_bluetooth.py (ai/task.md)."

traceability:
  design_updates:
    - "design-a3b4c5d6 v2.0: remove the '(change)' marks once implemented and verified. Planner."
  related_changes:
    - change_ref: "change-b4f9607a"
      relationship: "depends on"
    - change_ref: "change-042dd7ff"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-34781bfe"
      relationship: "resolves"

notes: "Not to be started before design-a3b4c5d6 v2.0 is approved and device session A has passed."

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-34781bfe iteration 1."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Implemented in c8901f50feec06824916813f496a667bd4e68dfc; awaiting device session B."

  - version: "1.3"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Verified on device in session B (test-71ab3751-device-session-b)."

  - version: "1.4"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Closed with the 71ab3751 series (version 0.5.0); moved to change/closed/."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial change document. EDITS A to G. |
| 1.1 | 2026-11-11 | Approved for implementation. |
| 1.2 | 2026-11-12 | Implemented in c8901f5; awaiting device session B. |
| 1.3 | 2026-11-12 | Verified on device in session B. |
| 1.4 | 2026-11-12 | Closed with the 71ab3751 series; moved to closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
