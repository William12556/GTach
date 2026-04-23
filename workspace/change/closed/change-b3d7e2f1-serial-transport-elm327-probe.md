# Change: SerialTransport ELM327 ATZ Probe Validation in Port Discovery

Created: 2026 April 17

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Dependencies](<#6.0 dependencies>)
- [7.0 Testing Requirements](<#7.0 testing requirements>)
- [8.0 Implementation](<#8.0 implementation>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Traceability](<#10.0 traceability>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-b3d7e2f1"
  title: "SerialTransport ELM327 ATZ probe validation in port discovery"
  date: "2026-04-17"
  author: "William Watson"
  status: "verified"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b3d7e2f1"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "issue"
  reference: "issue-b3d7e2f1"
  description: >
    SerialTransport._discover_port() matches /dev/cu.ELM327-Emulator on macOS
    — a phantom Bluetooth SPP virtual port — by name pattern alone. The port
    opens at OS level but yields no ELM327 responses because the Pi emulator
    serves TCP only. OBDProtocol enters an indefinite initialization failure
    loop.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Add an ELM327 ATZ probe to SerialTransport._discover_port(). After a
    candidate port matches the name pattern, open it briefly, send ATZ\r,
    and check the response for "ELM327". Accept the port only on a positive
    response; close and continue scanning otherwise. No changes to connect(),
    disconnect(), send_command(), or any other transport.
  affected_components:
    - name: "SerialTransport"
      file_path: "src/gtach/comm/serial_transport.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "workspace/design/design-gtach-master.md"
      sections:
        - "Communication domain — SerialTransport"
  out_of_scope:
    - "TCPTransport"
    - "RFCOMMTransport"
    - "OBDProtocol"
    - "OBDTransport ABC"
    - "Transport auto-selection logic in transport.py"
    - "General transport intelligence or auto-switching between TCP/serial/RFCOMM"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    _discover_port() performs name-pattern matching only. A port whose name
    matches but which is not serving ELM327 commands is indistinguishable
    from a valid adapter. macOS creates /dev/cu.* virtual ports for all
    paired Bluetooth devices; any device with 'ELM' in its name will match.
  proposed_solution: >
    Probe each name-matched candidate with ATZ\r using a short timeout (2s).
    The ELM327 ATZ response always contains the string "ELM327". A missing
    or unrecognised response means the port is not a functional ELM327 adapter
    and should be skipped. The probe uses a dedicated serial.Serial instance
    that is closed after the check; connect() re-opens the validated port
    independently and is not affected.
  alternatives_considered:
    - option: "Configurable port name in config.yaml — user specifies exact port"
      reason_rejected: >
        Requires manual configuration per machine. Defeats the purpose of
        auto-discovery and is not feasible on the Pi touch display.
    - option: "Exclude /dev/cu.ELM327-Emulator by name pattern on macOS"
      reason_rejected: >
        Brittle. Hardcodes a specific device name. Does not generalise to
        other phantom ports or future device names.
    - option: "Add validate() to OBDTransport ABC; probe after connect()"
      reason_rejected: >
        Larger scope change affecting all transports. The probe belongs in
        discovery, before connect() commits to a port. Deferred to prevention
        note in issue-b3d7e2f1.
  benefits:
    - "Eliminates indefinite OBD init failure loop caused by phantom serial ports."
    - "Confined to _discover_port(); connect() and all other methods unchanged."
    - "Generalises correctly to any non-ELM327 port that matches the name pattern."
    - "No behavioural change when a real ELM327 adapter is present and responding."
  risks:
    - risk: "Probe adds ~2s latency to port discovery per candidate port."
      mitigation: >
        Acceptable for startup-time discovery. In practice only one or two
        /dev/cu.* ports will match the pattern.
    - risk: "ATZ resets the ELM327 adapter state."
      mitigation: >
        ATZ is the standard ELM327 initialization command. connect() sends
        ATZ as the first step of its own initialization sequence. The probe
        reset is harmless and consistent with normal operation.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    SerialTransport._discover_port() (serial_transport.py):
      - Iterates list_ports.comports().
      - Skips /dev/tty.* on Darwin.
      - Returns first port whose device path or description matches
        any of ['ELM', 'OBD', 'OBDII'] (case-insensitive).
      - No ELM327 command is sent; OS-level port existence is the sole criterion.

  proposed_behavior: >
    SerialTransport._discover_port() (serial_transport.py):
      - Same iteration and tty.* skip as current.
      - For each name-matched candidate, call new helper _probe_port(device).
      - _probe_port returns True if "ELM327" in ATZ response; False otherwise.
      - If True: log confirmation, return device path.
      - If False: log skip, continue to next candidate.
      - If no candidate passes: return None (existing behaviour).

  implementation_approach: >
    Single new private method _probe_port(device: str) -> bool added to
    SerialTransport. One call to _probe_port inserted in _discover_port()
    after the existing pattern-match check. No other methods modified.

  code_changes:
    - component: "SerialTransport"
      file: "src/gtach/comm/serial_transport.py"
      change_summary: >
        Add _probe_port(device) helper. Insert _probe_port call in
        _discover_port() after pattern match. Net delta ~25 lines.
      functions_affected:
        - "_discover_port"
        - "_probe_port (new)"
      classes_affected:
        - "SerialTransport"

  data_changes: []
  interface_changes: []
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Dependencies

```yaml
dependencies:
  internal:
    - component: "SerialTransport.connect()"
      impact: "Not modified. connect() re-opens the validated port independently."
  external:
    - library: "pyserial"
      version: ">=3.5"
      impact: "serial.Serial used in _probe_port. Already a project dependency."
  required_changes: []
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: >
    Manual validation on macOS with phantom port present.
  test_cases:
    - scenario: "macOS, /dev/cu.ELM327-Emulator present, TCP-only Pi emulator"
      expected_result: "Port probed, no ELM327 response, skipped. No OBD init failure loop."
    - scenario: "macOS, real ELM327 adapter paired via Bluetooth SPP"
      expected_result: "Port probed, ELM327 response received, port selected, normal operation."
  regression_scope:
    - "src/gtach/comm/serial_transport.py"
  validation_criteria:
    - "No indefinite OBD init failure loop with phantom port present."
    - "No behavioural change on Raspberry Pi (RFCOMM transport unaffected)."
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Implementation

```yaml
implementation:
  implementation_steps:
    - step: "Add _probe_port(self, device: str) -> bool to SerialTransport."
      owner: "Tactical Domain"
    - step: "In _discover_port(), call _probe_port() after each pattern match. Return only on True."
      owner: "Tactical Domain"
  rollback_procedure: "Revert serial_transport.py to prior commit."
  deployment_notes: "macOS development only. No Pi changes required."
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  implemented_date: "2026-04-17"
  implemented_by: "William Watson"
  verification_date: "2026-04-22"
  verified_by: "William Watson"
  test_results: >-
    Run with --transport serial, /dev/cu.ELM327-Emulator present (TCP-only).
    Probe fired, no ELM327 response, port skipped, retry loop entered.
    No indefinite OBD init failure loop. Display stable at 60 FPS.
  issues_found: []
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Traceability

```yaml
traceability:
  design_updates:
    - design_ref: "workspace/design/design-gtach-master.md"
      sections_updated:
        - "Communication domain — SerialTransport"
      update_date: "2026-04-22"
  related_changes: []
  related_issues:
    - issue_ref: "issue-b3d7e2f1"
      relationship: "resolves"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author         | Changes                 |
| ------- | ---------- | -------------- | ----------------------- |
| 1.0     | 2026-04-17 | William Watson | Initial change creation |
| 1.1     | 2026-04-22 | William Watson | Verified by log output — closing |

---

Copyright (c) 2026 William Watson. MIT License.
