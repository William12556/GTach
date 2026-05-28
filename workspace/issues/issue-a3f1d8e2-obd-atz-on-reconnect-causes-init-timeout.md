Created: 2026 May 28

# Issue a3f1d8e2 — OBD ATZ on Reconnect Causes Initialisation Timeout

---

## Table of Contents

[1.0 Issue Information](<#1.0 issue information>)
[2.0 Source](<#2.0 source>)
[3.0 Affected Scope](<#3.0 affected scope>)
[4.0 Reproduction](<#4.0 reproduction>)
[5.0 Behaviour](<#5.0 behaviour>)
[6.0 Environment](<#6.0 environment>)
[7.0 Analysis](<#7.0 analysis>)
[8.0 Resolution](<#8.0 resolution>)
[Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-a3f1d8e2"
  title: "OBD ATZ on reconnect causes initialisation timeout after setup"
  date: "2026-05-28"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: "change-a3f1d8e2"
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
    After setup wizard completes, OBD protocol handler reconnects to the ELM327
    adapter and sends ATZ unconditionally. The setup probe (BluetoothPairing) has
    already run ATZ and ATSP0, then disconnects the RFCOMM socket. The adapter or
    emulator is not ready to accept a second ATZ immediately after the probe
    disconnects. The OBD init times out and RPM polling never starts.
    A 500ms settle delay (v0.2.56) partially mitigates the symptom but does not
    address the root cause.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.56"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: "GTach paired and connected to ELM327 emulator via Bluetooth."
  steps:
    - "Launch GTach. Setup wizard runs."
    - "Select emulator device. Setup probe connects, runs ATZ/ATSP0, verifies OBD, disconnects."
    - "Setup marks complete. OBDProtocol starts and reconnects RFCOMM."
    - "OBDProtocol sends ATZ — adapter not yet ready."
    - "Timeout occurs. OBD init fails. RPM polling never starts."
  frequency: "always"
  reproducibility_conditions: "Occurs every time setup completes and OBD reconnects."
  error_output: >
    RFCOMMTransport  Timeout waiting for response from device
    OBDProtocol  Initialization failed: No connection to vehicle
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behaviour

```yaml
behavior:
  expected: >
    After setup completes, OBDProtocol reconnects and begins RPM polling without
    resending ATZ. The adapter was already initialised by the setup probe; a second
    ATZ reset is unnecessary and harmful.
  actual: >
    OBDProtocol sends ATZ on every reconnect regardless of whether the adapter was
    already initialised by the setup probe. The adapter does not respond in time;
    init fails; RPM polling does not start.
  impact: >
    RPM display remains at zero after setup completes. User must restart the
    application to obtain RPM data.
  workaround: >
    500ms settle delay added in v0.2.56 reduces failure rate but does not eliminate
    it. Application restart recovers the session.
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.11"
  os: "Raspberry Pi OS (Debian 12), Linux"
  dependencies:
    - library: "pyserial"
      version: "current"
  domain: "domain_1"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    OBDProtocol._protocol_loop resets _adapter_initialised to False whenever the
    transport disconnects (line: "self._adapter_initialised = False"). This occurs
    when the setup probe disconnects the RFCOMM socket. On the subsequent OBD
    reconnect, _initialize_protocol sees _adapter_initialised=False and sends ATZ,
    which the adapter cannot service immediately after the probe's disconnect.
  technical_notes: >
    The _adapter_initialised flag exists precisely to skip ATZ on reconnect.
    However it is cleared unconditionally on every disconnect, including the
    setup-probe disconnect. The fix is to not clear _adapter_initialised on the
    first reconnect after setup, or to carry the flag across the setup→OBD
    handoff so OBD knows the adapter is already ready.

    Proposed mechanism: OBDProtocol accepts an optional constructor parameter
    adapter_pre_initialised (bool, default False). When True, _adapter_initialised
    is set to True at construction time. The app sets this flag when starting OBD
    after a successful setup wizard run. On a genuine disconnect/reconnect mid-session
    the flag is cleared as before — only the initial post-setup connect skips ATZ.
  related_issues:
    - issue_ref: ""
      relationship: ""
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Add adapter_pre_initialised parameter to OBDProtocol.__init__. Set
    _adapter_initialised = adapter_pre_initialised at construction. In app.py,
    pass adapter_pre_initialised=True when constructing OBDProtocol after a
    successful setup wizard run. Remove or reduce the 500ms settle delay added
    in v0.2.56 once the root cause is resolved.
  change_ref: "change-a3f1d8e2"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-28 | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
