# Issue: Task Register Fixes — Texts, Simulation, Log Levels, Connect Causes

Created: 2026 November 12

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-76ef5387"
  title: "Six open ai/task.md items: truncated 'Device not saved', unclassified simulated devices, EBADF at ERROR on planned disconnect, unmapped ECONNABORTED after setup, no-controller connect at boot, and a 'wedged' diagnosis for an adapter that is simply off"
  date: "2026-11-12"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-76ef5387"
    change_iteration: 1

source:
  origin: "test_result"
  test_ref: "test-71ab3751-device-session-b; b29cbd71 device check (2026-11-12)"
  description: "Open rows of ai/task.md, bundled into one triple at the owner's request (2026-11-12). The owner delegated the technical decisions to the planner."

affected_scope:
  components:
    - name: "DEVICE_NOT_SAVED_TEXT; BluetoothSetupInterface.start_pairing (on_pairing_complete)"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "_FAKE_DEVICES"
      file_path: "src/gtach/comm/sim_bluetooth.py"
    - name: "_CONNECT_FAULT_CAUSES; OBDTransport.connect; OBDTransport.send_command"
      file_path: "src/gtach/comm/transport.py"
    - name: "gtach.service"
      file_path: "bin/gtach.service"
  designs:
    - "design-a3b4c5d6-component_display_setup_manager"
  version: "0.5.0"

reproduction:
  prerequisites: "Pi with GTach 0.5.0; ELM327 emulator on Bluetooth; for F2, a simbt session."
  steps:
    - "F1: a paired device that cannot be saved (DEVICE_LIST error line)."
    - "F2: gtach --transport simbt; run discovery."
    - "F3: systemctl stop gtach, or Clear settings, while connected."
    - "F4: complete setup; observe the first connect of the main transport."
    - "F5: reboot the Pi with a paired adapter in range."
    - "F6: switch the adapter's radio off while GTach is connected; wait about 1 min."
  frequency: "F1, F2, F3 always; F4, F5 observed in session B; F6 always"
  reproducibility_conditions: "F1 and F2 from source and unit tests; F3 to F6 on the device."
  test_data: >
    F1: DEVICE_NOT_SAVED_TEXT 'Device not saved' measures 221 px in
    get_label_small_font(); the DEVICE_LIST error line is 220 px, so
    _fit_text shortens it. tests/test_session_b_findings.py marks the
    case strict xfail.
    F2: _FAKE_DEVICES set no device_classification, so all four are
    DeviceType.UNKNOWN and _present_scan_result shows FALLBACK_LIST_TEXT
    ('No ELM327'), which it shows only when every device is UNKNOWN.
    F3: disconnect() closes the socket while the protocol thread is in
    send_command; the read raises EBADF, which the _IO_ERRORS handler
    logs as 'Error communicating with device: [Errno 9] Bad file
    descriptor' at ERROR and records as the failure cause.
    F4: the first connect after setup fails with ECONNABORTED, which is
    unmapped, so the cause shown is the errno name; the next retry about
    6 s later succeeds.
    F5: the first connect after boot fails with EHOSTUNREACH; sysfs has
    no controller yet, so the cause is 'no bluetooth controller'; the
    retry about 5 s later succeeds. The controller on the Pi Zero 2W is
    attached by hciuart.service, which gtach.service is not ordered
    after. Related: a pairing that returns False is logged at ERROR
    ('Failed to pair with device'), including the 20 % simulated
    failures of SimBluetoothPairing.
    F6: every attempt fails with EHOSTDOWN ('adapter not reachable');
    after _MAX_CONSECUTIVE_CONNECT_FAILURES (6) the cause escalates to
    'bluetooth wedged - reset required' (b29cbd71 device check
    2026-11-12 12:11:45 to 12:12:36).
  error_output: "F3: 'Error communicating with device: [Errno 9] Bad file descriptor'. F6: 'bluetooth wedged - reset required' on DISCONNECTED."

behavior:
  expected: "F1: the text renders in full. F2: simulation exercises the normal device list. F3: a planned close is not an error. F4: a readable cause. F5: no failed connect at boot when the controller is merely late. F6: an adapter that is off is reported as not reachable, not as a wedged controller. A failed pairing is a WARNING."
  actual: "As in test_data."
  impact: "F1, F2, F4: cosmetic. F3, F5: misleading ERROR records. F6: a misleading operator instruction (reset) on the DISCONNECTED screen."
  workaround: "None needed; every case recovers on its own except F6, where the operator may reset the Pi needlessly."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "F1: text 1 px too wide. F2: missing data. F3: the I/O handler does not distinguish a handle closed by this process. F4: errno not mapped. F5: boot ordering. F6: EHOSTDOWN counts towards the wedge escalation although it shows a working controller (it paged the peer)."
  technical_notes: >
    F3: EBADF can arise only from a file descriptor closed by this
    process; the handle captured by send_command no longer being the
    current handle identifies that case without inspecting errno.
    F4: inferred, not confirmed from logs, to be the same mechanism as
    the ECONNRESET of issue-146491ba (the setup probe's link still
    closing). F6: EHOSTDOWN and EHOSTUNREACH share the cause 'adapter
    not reachable'; with no controller present, the sysfs check
    overrides it with 'no bluetooth controller' first. Confidence
    moderate that a wedged controller never reports EHOSTDOWN; the only
    wedge observed (2026-10-08) reported EBUSY.
  related_issues:
    - issue_ref: "issue-146491ba"
      relationship: "related; LINK_RESET_CAUSE and the verify retry"
    - issue_ref: "issue-5e7a03c4"
      relationship: "related; connect-fault causes and the wedge escalation"
    - issue_ref: "issue-34781bfe"
      relationship: "related; introduced the fallback notice"

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-76ef5387."
  change_ref: "change-76ef5387"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Unit tests per change-76ef5387."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE, 2026-11-12.]"
    - "After the fix: unit tests per change-76ef5387."
    - "After the fix: device check — hciuart.service state and type; service stop while connected; adapter radio off for 2 min; reboot with the adapter in range; one setup."
  verification_results: ""

traceability:
  design_refs:
    - "design-a3b4c5d6-component_display_setup_manager"
  change_refs:
    - "change-76ef5387"
  test_refs:
    - "test-71ab3751-device-session-b"

notes: >
  Dropped without change (owner delegated decision, 2026-11-12): the
  re-check loop for a vehicle that answers 0100 but never 010C (PID 0C
  unsupported). PID 0C is supported by practically every OBD-II vehicle;
  the loop is bounded, recovers by itself and costs two INFO records per
  cycle. Out of scope: automatic recovery from the stuck Bluetooth state
  (separate ai/task.md row).

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-12"
    author: "William Watson"
    changes:
      - "Initial issue document."

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
| 1.0 | 2026-11-12 | Initial issue document. Findings F1 to F6 from ai/task.md. |

---

Copyright (c) 2026 William Watson. MIT License.
