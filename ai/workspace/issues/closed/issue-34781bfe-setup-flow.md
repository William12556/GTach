# Issue: Setup Flow Outcomes and Cancellation

Created: 2026 November 11

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-34781bfe"
  title: "Discovery outcomes are not presented and scans repeat without end; the stored-device probe acts after the operator has left its screen; cancellation does not stop or silence running operations; further setup-screen defects"
  date: "2026-11-11"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-34781bfe"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-71ab3751 findings D01, C08 (medium), C01, C02, D02, D03, D04 (low), the display parts of X01 and A09, the setup part of B02, observation O4, weakness W2 (report-71ab3751 section 5.0), the ai/task.md rows 'Bluetooth discovery fallback' (user interface) and 'Optional surface to SetupDisplayManager'."

affected_scope:
  components:
    - name: "SetupDisplayManager: setup loop, rendering, touch actions, probe callback"
      file_path: "src/gtach/display/setup.py"
    - name: "BluetoothSetupInterface: discovery, pairing and probe operations; cancellation"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "SetupStateCoordinator.handle_setup_action"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
    - name: "AsyncOperationManager: progress injection, operation retention, cancel"
      file_path: "src/gtach/display/async_operations.py"
    - name: "SetupState, SetupAction"
      file_path: "src/gtach/display/setup_models.py"
  designs:
    - "design-a3b4c5d6-component_display_setup_manager"
    - "design-2c6b8e4d-domain_display"
  version: "0.4.13"

reproduction:
  prerequisites: "Pi; for D01 no discoverable adapter in range; for C08 a stored device."
  steps:
    - "D01: start setup with no adapter in range and watch the DISCOVERY screen."
    - "C08: on CURRENT_DEVICE tap Continue, then New Setup while the probe runs."
    - "X01: on DISCOVERY tap Cancel and wait on the WELCOME screen."
    - "C01: on PAIRING after 'Pairing successful' tap Continue."
  frequency: "D01, C01, X01 always; C08 and D04 timing-dependent"
  reproducibility_conditions: "From source."
  test_data: >
    D01: on_discovery_complete with zero devices sets error_message and
    status IDLE; _render_discovery_screen does not draw error_message;
    _setup_loop sees DISCOVERY + IDLE + no devices + no active
    operation and starts the next scan. A failed scan sets FAILED,
    which no branch handles. The DEVICE_LIST 'No devices found' branch
    is entered only with a non-empty list.
    C08: _on_probe_result does not check that the screen is still
    CURRENT_DEVICE; 'new_setup' stays available while the probe runs.
    X01: AsyncOperationManager.cancel_operation cancels only PENDING
    operations; the Cancel action on DISCOVERY calls neither
    cancel_operations nor cancel_discovery; an abandoned scan's
    completion still writes the device list and error message.
    C01: the PAIRING screen's Continue button maps to SetupAction.NEXT,
    for which _handle_next_navigation has no PAIRING branch.
    C02: the two spinners pass an RGBA colour to pygame.draw.circle on
    a surface without per-pixel alpha; all eight dots have one colour.
    D02: progress is injected only for a task local named
    'progress_callback'; discovery_task and pairing_task name theirs
    'progress_callback_inner'.
    D03: cleanup_completed_operations has no caller; operations and
    their closures are kept for the life of the process.
    D04: START_DISCOVERY and CANCEL transition first and reset the
    device list second.
    A09: on_pairing_complete ignores save_device()'s result.
    B02: the application cannot tell whether this setup session sent
    ATZ; verify_obd_connection sends it only on the real pairing path.
    O4: render() copies the 480x480 target, draws into the copy and
    blits it back on every frame of the uncached screens.
    Optional surface: the application passes
    rendering_engine.main_surface, which may be None, under a
    type: ignore.
    W2: what follows a finished operation is decided in three places
    (completion callbacks, the setup loop's polling condition, touch
    handlers), which is the common origin of D01, C08, X01 and D04.
  error_output: "None."

behavior:
  expected: "As design-a3b4c5d6 v2.0 sections 4.0 to 6.0."
  actual: "As in test_data."
  impact: "The operator gets no feedback from an empty or failed scan; setup can complete against a removed device; stale results appear on other screens."
  workaround: "Restart setup."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "No single rule ties a completion to the operation that is currently wanted (W2)."
  technical_notes: >
    design-a3b4c5d6 v2.0 section 6.0 states the rule: a completion acts
    only while its operation id is the registered one for its name;
    cancelling removes the registration and then asks the back end to
    stop. The back-end parts (pair_device honouring cancellation, the
    same-scan fallback result, save_device's result) are provided by
    change-b4f9607a.
  related_issues:
    - issue_ref: "issue-b4f9607a"
      relationship: "depends on."
    - issue_ref: "issue-042dd7ff"
      relationship: "related. Reads adapter_reset_in_session."
    - issue_ref: "issue-d140121d"
      relationship: "related. Coordinator-owned state and _ops_lock."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-34781bfe."
  change_ref: "change-34781bfe"
  resolved_date: "2026-11-12"
  resolved_by: "change-34781bfe"
  fix_description: "Operations are registered by name with an id issued before submit; completions and in-task callbacks act only while current; Cancel on DISCOVERY and Back on PAIRING cancel through one path; a scan starts only on Start Setup and on Retry from DEVICE_LIST; empty, failed and fallback scans reach DEVICE_LIST ('Scan failed', 'No ELM327 found - showing all devices'); New Setup is not offered while the probe runs; no Continue on PAIRING; spinner fade by colour blend; progress passed to a declared progress_callback; finished operations removed; uncached screens drawn on the target; save_device result honoured ('Device not saved'); SetupDisplayManager.adapter_reset_in_session; Optional surface (commit c8901f50feec06824916813f496a667bd4e68dfc; report-34781bfe)."

verification:
  verified_date: "2026-11-12"
  verified_by: "William Watson"
  test_results: "Device session B (test-71ab3751-device-session-b steps B2 to B5 and B8): all checks passed. New Setup visibility during the probe and an empty device list were not observable on the device; unit tests cover both."
  closure_notes: "Closed with the 71ab3751 series (version 0.5.0). New Setup during a probe and an empty device list were not observable on the device; unit tests cover both. The simbt device classification remains an ai/task.md row."

prevention:
  preventive_measures: "The operation rule of design-a3b4c5d6 section 6.0 applies to every new setup operation."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE, audit-71ab3751.]"
    - "After the fix: unit tests per change-34781bfe."
    - "After the fix: device session B — setup end to end with the emulator; empty scan; Cancel during a scan; New Setup during a probe; simbt path."
  verification_results: "pytest 694 passed and mypy clean (worker's results). Device session B passed on 2026-11-12."

traceability:
  design_refs:
    - "design-a3b4c5d6-component_display_setup_manager"
  change_refs:
    - "change-34781bfe"
  test_refs: []

notes: "Audit reference: audit-71ab3751 D01-D04, C01, C02, C08, X01 (display part), A09 (interface part), B02 (setup part), O4; weakness W2. Run 4 of proposal-71ab3751."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial issue document."

  - version: "1.1"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Resolved by change-34781bfe (c8901f50feec06824916813f496a667bd4e68dfc); awaiting device session B."

  - version: "1.2"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Verified on device in session B."

  - version: "1.3"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Closed with the 71ab3751 series; moved to issues/closed/."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial issue document. D01-D04, C01, C02, C08, X01, A09, B02, O4, W2. |
| 1.1 | 2026-11-12 | Resolved by change-34781bfe (c8901f5); awaiting device session B. |
| 1.2 | 2026-11-12 | Verified on device in session B. |
| 1.3 | 2026-11-12 | Closed with the 71ab3751 series; moved to closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
