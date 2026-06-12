Created: 2026 June 12

```yaml
change_info:
  id: "change-54eeb2d6"
  title: "End ELM327 discovery early when a confirmed adapter is found"
  date: "2026-06-12"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-54eeb2d6"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-54eeb2d6"
  description: >
    Discovery iterates the full timeout even after a confirmed ELM327 adapter is
    found, delaying presentation of the device list by up to ~30s.

scope:
  summary: >
    Add a single early-exit condition to the chunk loop in
    discover_elm327_devices: in targeted mode (not show_all_devices), break once a
    discovered device is classified HIGHLY_LIKELY_ELM327. Full-survey mode is
    unchanged and still runs the complete timeout.
  affected_components:
    - name: "BluetoothPairing"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master"
      sections:
        - "Bluetooth discovery"
  out_of_scope:
    - "show_all_devices (full survey) behaviour."
    - "Device classification logic."
    - "Discovery cancellation, progress reporting, or timeout configuration."
    - "Any interface or signature change."

rational:
  problem_statement: >
    The chunk loop in discover_elm327_devices runs every chunk for the full
    timeout and never terminates when the target adapter is found. The
    device_found_callback fires immediately, but the loop ignores it.
  proposed_solution: >
    After each chunk is processed, in targeted mode only, break the loop if any
    accumulated device is classified HIGHLY_LIKELY_ELM327. The existing final
    progress_callback(1.0) and return path then run unchanged.
  alternatives_considered:
    - option: "Break on the first POSSIBLY_COMPATIBLE device as well."
      reason_rejected: "Possibly-compatible modules are not confirmed adapters; ending early risks hiding the real adapter discovered in a later chunk."
  benefits:
    - "Device list appears promptly once the adapter is found."
    - "No interface change; single-function, low-risk edit."
  risks:
    - risk: "Adapter classified only POSSIBLY_COMPATIBLE would not trigger early exit."
      mitigation: "Intended: full timeout still applies in that case, preserving current behaviour for ambiguous devices."

technical_details:
  current_behavior: >
    for chunk in range(chunks): runs a blocking scan per chunk, appends classified
    devices, fires device_found_callback, and only exits when all chunks are
    exhausted (full timeout) or on cancel/error.
  proposed_behavior: >
    After processing each chunk, in targeted mode, if any accumulated device is
    HIGHLY_LIKELY_ELM327, log and break. Survey mode and all other paths unchanged.
  implementation_approach: >
    Insert a guarded break at the end of the chunk loop body, after the chunk
    discovery try/except and before the next iteration.
  code_changes:
    - component: "BluetoothPairing"
      file: "src/gtach/comm/pairing.py"
      change_summary: >
        In discover_elm327_devices, add after the per-chunk try/except:
        if not show_all_devices and any device in devices is
        DeviceType.HIGHLY_LIKELY_ELM327 -> log and break.
      functions_affected:
        - "discover_elm327_devices"
      classes_affected:
        - "BluetoothPairing"
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "On-Pi verification with the ELM327 emulator (rfcomm transport)."
  test_cases:
    - scenario: "Targeted discovery, ELM327 present."
      expected_result: "Loop breaks in the chunk where the adapter is classified HIGHLY_LIKELY_ELM327; device list appears without waiting for the full timeout."
    - scenario: "Targeted discovery, only POSSIBLY_COMPATIBLE devices present."
      expected_result: "Full timeout runs as before; no early exit."
    - scenario: "Full survey (show_all_devices=True)."
      expected_result: "Full timeout runs; no early exit regardless of classification."
    - scenario: "Discovery cancelled mid-scan."
      expected_result: "Existing cancellation break unaffected."
  regression_scope:
    - "discover_all_devices (delegates with show_all_devices=True)."
    - "Progress reporting and final progress_callback(1.0)."
  validation_criteria:
    - "Targeted mode ends promptly on a confirmed adapter."
    - "Survey mode and ambiguous-device cases retain full-timeout behaviour."
    - "No change to method signature or return type."

implementation:
  implementation_steps:
    - step: "Add the guarded early-exit break in discover_elm327_devices."
      owner: "Claude Code"
  rollback_procedure: "Revert pairing.py via git."
  deployment_notes: "Build wheel and deploy to Pi per standard workflow."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  related_changes: []
  related_issues:
    - issue_ref: "issue-54eeb2d6"
      relationship: "resolves"

notes: >
  The issue notes this is a single-function, small-delta, no-interface change —
  near the trivial-exemption boundary. Routed through the full pipeline for an
  explicit record at William's direction.

version_history:
  - version: "1.0"
    date: "2026-06-12"
    author: "William Watson"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
