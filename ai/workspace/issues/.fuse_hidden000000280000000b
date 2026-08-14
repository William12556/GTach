Created: 2026 August 14

```yaml
issue_info:
  id: "issue-4ab5ff88"
  title: "DISCONNECTED screen's Bluetooth Reset button does not reliably restore the link"
  date: "2026-08-14"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-4ab5ff88"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    The DISCONNECTED screen's "BT Reset" button (issue-8a63d5f1,
    change-8a63d5f1) invokes hciconfig hci0 reset via
    utils/bluetooth_reset.py. In field use this frequently fails to
    restore the Bluetooth link; only a full reboot of the Pi reliably
    recovers it. GTach is a single-purpose device, so a reboot carries
    no cost a Bluetooth-only reset does not already carry in the
    operator's mind.

affected_scope:
  components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
    - name: "bluetooth_reset"
      file_path: "src/gtach/utils/bluetooth_reset.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.4.1"

reproduction:
  prerequisites: "Deployed device with the DISCONNECTED screen active (no OBD/Bluetooth link)."
  steps:
    - "Trigger the DISCONNECTED screen (power up without a paired adapter in range, or let the link drop)."
    - "Press the 'BT Reset' button."
    - "Observe the cause line's outcome string."
  frequency: "intermittent"
  reproducibility_conditions: "Adapter left in a state hciconfig hci0 reset cannot recover; a full reboot recovers it in the same state."
  preconditions: ""
  test_data: ""
  error_output: "Cause line reports 'adapter down - reboot required' (bluetooth_reset._DOWN) or 'bluetooth reset timed out'."

behavior:
  expected: >
    The operator's one available recovery action from the DISCONNECTED
    screen reliably restores the link.
  actual: >
    hciconfig hci0 reset (and the single hciconfig hci0 up retry already
    built into reset_adapter) frequently leaves the adapter down. Only a
    reboot of the Pi has proven reliable on target.
  impact: >
    Operator has no reliably effective recovery path short of a manual
    power cycle, which the touchscreen-only device gives no on-screen
    route to.
  workaround: "Manual power cycle of the Pi."

environment:
  python_version: "3.11"
  os: "Debian GNU/Linux 11 (Bullseye), Raspberry Pi Zero 2W"
  dependencies:
    - library: "hciconfig"
      version: ""
  domain: "domain_1"

analysis:
  root_cause: >
    hciconfig hci0 reset operates on the Bluetooth controller only; it
    cannot recover states that require a full kernel/module reload,
    which a reboot performs. This was anticipated in bluetooth_reset.py's
    own _DOWN outcome string ("adapter down - reboot required") but the
    DISCONNECTED screen gave the operator no button that performs one.
  technical_notes: >
    bin/gtach.service specifies User=root, so a reboot subprocess call
    requires no privilege escalation. utils/bluetooth_reset.py documents
    itself as the only module in GTach permitted to invoke subprocess
    (change-5e7a03c4, issue-8a63d5f1); replacing its sole call site
    rather than adding a second one preserves that invariant.
  related_issues:
    - issue_ref: "issue-8a63d5f1"
      relationship: "supersedes"

resolution:
  assigned_to: "William Watson"
  target_date: ""
  approach: >
    Remove the Bluetooth-adapter-reset path entirely (button, callback
    chain, hciconfig logic) and replace the DISCONNECTED screen's second
    button with a "Reset" control that reboots the Pi directly via
    /sbin/reboot.
  change_ref: "change-4ab5ff88"
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
    None specific; the original design (change-8a63d5f1) already
    anticipated and logged the reboot-required outcome without acting on
    it.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - ""
  verification_results: ""

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-4ab5ff88"
  test_refs: []

notes: >
  Reported directly by the operator from field use; not derived from a
  test failure or AEL BLOCKED outcome.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson / Claude"
    changes:
      - "Initial issue creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

Copyright (c) 2026 William Watson. MIT License.
