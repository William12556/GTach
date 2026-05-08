Created: 2026 April 30

# Issue: Sim Mode — Hardware-Free Full Application Testing

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

```yaml
issue_info:
  id: "issue-c7e2f1a9"
  title: "Sim Mode — Hardware-Free Full Application Testing"
  date: "2026-04-30"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-c7e2f1a9"
    change_iteration: 1
```

---

## 1.0 Issue Information

Enhancement request to add two simulation transport modes enabling full application testing without
real Bluetooth hardware, an ELM327 adapter, or a running TCP emulator process.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: ""
  description: >
    No mechanism currently exists to exercise the full GTach application — OBD display pipeline
    and Bluetooth setup wizard — without physical hardware or a running emulator.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "OBDTransport / select_transport"
      file_path: "src/gtach/comm/transport.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
    - name: "CLI argument parser"
      file_path: "src/gtach/main.py"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "SimTransport (new)"
      file_path: "src/gtach/comm/sim_transport.py"
    - name: "SimBluetoothPairing (new)"
      file_path: "src/gtach/comm/sim_bluetooth.py"
  designs:
    - design_ref: "design-gtach-master.md"
    - design_ref: "design-7d3e9f5a-domain_comm.md"
  version: "0.2.0"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "AEL"
  target_date: ""
  approach: >
    Implement per technical_notes. Create T02 change and T04 prompt documents.
    Execute via AEL.
  change_ref: "change-c7e2f1a9"
  resolved_date: "2026-05-08"
  resolved_by: "AEL / Claude Code"
  fix_description: >
    SimTransport and SimBluetoothPairing created. --transport simtcp and simbt wired
    into transport.py, main.py, app.py, and interface.py. pairing_factory injection
    pattern implemented in BluetoothSetupInterface.
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification:
  verified_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: >
    Code inspection confirmed. sim_transport.py, sim_bluetooth.py present.
    simtcp and simbt in transport.py and main.py choices. pairing_factory in interface.py.
  closure_notes: "Implemented. Closed."

verification_enhanced:
  verification_steps:
    - "Run: gtach --transport simtcp --debug — confirm splash, RPM display, RPM sweeps 800-6500."
    - "Run: gtach --transport simbt --debug — confirm setup wizard with SimBluetoothPairing."
    - "Confirm 4 fake devices appear after scan."
    - "Confirm at least one pairing failure in ~5 attempts."
  verification_results: "Source inspection confirmed. Full runtime test pending on Pi."
```

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Traceability

```yaml
traceability:
  design_refs:
    - "design-gtach-master.md"
    - "design-7d3e9f5a-domain_comm.md"
  change_refs:
    - "change-c7e2f1a9"
  test_refs: []

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-04-30 | William Watson | Initial issue document |
| 0.2 | 2026-05-08 | William Watson | Closed — implementation verified in source |

---

Copyright (c) 2026 William Watson. MIT License.
