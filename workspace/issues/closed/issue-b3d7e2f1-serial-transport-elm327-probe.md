# Issue: SerialTransport Connects to Phantom Bluetooth SPP Port Without ELM327 Validation

Created: 2026 April 17

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [8.0 Resolution](<#8.0 resolution>)
- [9.0 Verification](<#9.0 verification>)
- [10.0 Prevention](<#10.0 prevention>)
- [11.0 Traceability](<#11.0 traceability>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-b3d7e2f1"
  title: "SerialTransport connects to phantom Bluetooth SPP port without ELM327 validation"
  date: "2026-04-17"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: "change-b3d7e2f1"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: ""
  description: >
    SerialTransport._discover_port() matches /dev/cu.ELM327-Emulator on macOS —
    a phantom Bluetooth SPP virtual port created by macOS for a paired Pi device.
    The port opens successfully at the serial level but the Pi's ircama emulator
    only serves TCP (port 35000), not Bluetooth SPP. No ELM327 response is ever
    received. OBDProtocol reports repeated "Initialization failed: No connection
    to vehicle" errors indefinitely.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "SerialTransport"
      file_path: "src/gtach/comm/serial_transport.py"
  designs:
    - design_ref: "workspace/design/design-gtach-master.md"
  version: "0.2.0"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: >
    macOS with GTach v0.2.0. Raspberry Pi with ircama ELM327 emulator paired
    to the Mac via Bluetooth (creating /dev/cu.ELM327-Emulator). Emulator
    running in TCP mode only (python3 -m elm -s car -l -n 35000).
  steps:
    - "Launch GTach: python -m gtach --macos --transport serial --config workspace/config/config-macos-dev.yaml --debug"
    - "Observe SerialTransport connect to /dev/cu.ELM327-Emulator immediately."
    - "Observe OBDProtocol error: Initialization failed: No connection to vehicle, repeating indefinitely."
  frequency: "always"
  reproducibility_conditions: >
    Manifests on macOS whenever a Bluetooth device with 'ELM' in its name is
    paired at the OS level, regardless of whether it is serving ELM327 commands.
  preconditions: "macOS. /dev/cu.ELM327-Emulator present. Emulator TCP-only."
  test_data: ""
  error_output: |
    SerialTransport INFO Found OBD device on port /dev/cu.ELM327-Emulator
    SerialTransport INFO Connected to serial device /dev/cu.ELM327-Emulator at 38400 baud
    OBDProtocol ERROR Initialization failed: No connection to vehicle
    OBDProtocol ERROR Initialization failed: No connection to vehicle
    ... (repeating)
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behavior

```yaml
behavior:
  expected: >
    SerialTransport._discover_port() should verify that a candidate port
    responds to an ELM327 ATZ probe before declaring a connection. A port
    that opens at the OS level but yields no valid ELM327 response should
    be rejected and scanning should continue to the next candidate.
  actual: >
    _discover_port() matches any /dev/cu.* port whose device path or description
    contains 'ELM', 'OBD', or 'OBDII'. It returns the first match without
    sending any command. connect() opens the port and declares CONNECTED.
    OBDProtocol then fails all initialization attempts indefinitely because
    the port produces no ELM327 responses.
  impact: >
    With --transport serial on macOS, GTach connects to a non-functional phantom
    port and enters a permanent OBD initialization failure loop. The display
    runs but no RPM data is ever received. The application does not fall back
    to TCP or report a useful diagnostic.
  workaround: "Use --transport tcp with the ircama emulator running on TCP port 35000."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.11.14"
  os: "macOS (Darwin) Apple Silicon"
  dependencies:
    - library: "pyserial"
      version: "3.5+"
  domain: "domain_comm"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    SerialTransport._discover_port() performs name-pattern matching only
    (patterns: ['ELM', 'OBD', 'OBDII']). It does not verify that the port
    produces valid ELM327 responses. macOS creates /dev/cu.<device-name>
    virtual serial ports for all paired Bluetooth devices. If the paired
    device name contains 'ELM', the port matches and is returned regardless
    of whether it is serving ELM327 commands.

    The ircama ELM327 emulator when run as a TCP server does not bind a
    Bluetooth SPP RFCOMM channel. The /dev/cu.ELM327-Emulator port is a
    macOS-managed virtual port that exists because the Pi was paired via
    Bluetooth at the OS level. Writing to this port produces no response
    because the Pi emulator is not listening on SPP.

  technical_notes: >
    - _discover_port() returns on first pattern match; no ELM327 handshake.
    - connect() calls serial.Serial(...) which succeeds at OS level for any
      valid /dev/cu.* port regardless of whether the remote device is active.
    - ELM327 ATZ response: device resets and replies with "ELM327 vX.X".
    - A probe approach: open port, send "ATZ\r", read response with short
      timeout, check for "ELM327" in response. If absent, close and continue.
    - Probe must use a short timeout (e.g. 2s) to avoid stalling discovery.
    - Probe must not disrupt subsequent normal connect() behaviour — the
      validated port should be returned and connect() re-opens it normally.

  related_issues:
    - issue_ref: "issue-a8f2c3e1"
      relationship: "related — both manifest on macOS --transport serial"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "William Watson"
  target_date: "2026-04-17"
  approach: >
    Modify SerialTransport._discover_port() to probe each candidate port with
    an ATZ command after opening. Accept the port only if the response contains
    "ELM327". Close and continue scanning otherwise. See change-b3d7e2f1.
  change_ref: "change-b3d7e2f1"
  resolved_date: "2026-04-22"
  resolved_by: "William Watson"
  fix_description: >
    Added _probe_port(device: str) -> bool method to SerialTransport that opens
    a candidate port, sends ATZ\r, reads until '>', and verifies the response
    contains "ELM327". Modified _discover_port() to call _probe_port() after
    each name-pattern match. Ports that fail the probe are skipped with a WARNING
    log, and discovery continues to the next candidate. No other methods modified.
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  verified_date: "2026-04-22"
  verified_by: "William Watson"
  test_results: >-
    Run with --transport serial, /dev/cu.ELM327-Emulator present (TCP-only).
    Probe fired, no ELM327 response received, port skipped. SerialTransport
    entered retry loop. No indefinite OBD init failure loop. Display stable
    at 60 FPS throughout.
  closure_notes: "Verified by log output. Probe sequence correct."

verification_enhanced:
  verification_steps:
    - "Launch with --transport serial, /dev/cu.ELM327-Emulator present but TCP-only."
    - "Confirm _discover_port() probes /dev/cu.ELM327-Emulator, receives no ELM327 response, skips it."
    - "Confirm no port is selected and SerialTransport enters retry loop."
    - "Launch with a real ELM327 adapter paired via Bluetooth SPP."
    - "Confirm _discover_port() probes, receives ELM327 response, returns port."
    - "Confirm normal OBD initialization and RPM display."
  verification_results: >-
    Log confirmed: Probing port DEBUG, No ELM327 response DEBUG, matched
    pattern but failed probe WARNING, No OBD device found INFO, retry loop
    entered. Behaviour correct.
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Prevention

```yaml
prevention:
  preventive_measures: >
    Transport connection validation should include a protocol-level handshake,
    not just an OS-level port open. Any transport that declares CONNECTED should
    have confirmed the remote device is responsive at the application protocol level.
  process_improvements: >
    Consider adding a validate() method to OBDTransport ABC that performs a
    minimal protocol probe after connect(). OBDProtocol could call validate()
    before proceeding to full initialization.
```

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Traceability

```yaml
traceability:
  design_refs:
    - "workspace/design/design-gtach-master.md"
  change_refs: []
  test_refs: []

notes: >
  This issue is latent whenever --transport serial is used on macOS with any
  Bluetooth device whose name matches the OBD pattern. The TCP transport path
  is unaffected.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author         | Changes                |
| ------- | ---------- | -------------- | ---------------------- |
| 1.0     | 2026-04-17 | William Watson | Initial issue creation |
| 1.1     | 2026-04-22 | William Watson | Closed — verified by log output |

---

Copyright (c) 2026 William Watson. MIT License.
