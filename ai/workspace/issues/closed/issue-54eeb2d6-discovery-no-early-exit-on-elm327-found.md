Created: 2026 May 29

# Issue: Discovery Does Not Stop When ELM327 Device Is Found

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
  id: "issue-54eeb2d6"
  title: "Bluetooth discovery runs full 30s timeout without stopping when ELM327 found"
  date: "2026-05-29"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-54eeb2d6"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: "gtach-debug.log 2026-05-29 13:42-13:43"
  description: >
    On-Pi test with rfcomm transport against the ELM327 emulator. The target
    device is discovered early in the scan but the device list is not presented
    until the full discovery timeout elapses. The user observes that scanning
    continues even though the log shows the device has already been found.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "BluetoothPairing"
      file_path: "src/gtach/comm/pairing.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.61"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: "Pi deployment with rfcomm transport; ELM327 (or emulator) discoverable"
  steps:
    - "Boot GTach on Pi (gtach --debug)"
    - "Enter setup; tap Start Setup on WELCOME to begin discovery"
    - "Observe debug log: ELM327 device found within first scan chunk"
    - "Observe display: scanning animation continues; device list not shown"
  frequency: "always"
  reproducibility_conditions: "Target ELM327 device present and discoverable"
  error_output: |
    13:43:04,049 BluetoothPairing INFO Found ELM327 device: ELM327-Emulator (DC:A6:32:54:AD:77)
    13:43:35,911 BluetoothPairing INFO Discovery complete. Found 1 devices
    13:43:35,925 SetupStateCoordinator INFO Screen transition: DISCOVERY -> DEVICE_LIST
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behaviour

```yaml
behavior:
  expected: >
    When discovery identifies a device that is highly likely to be an ELM327
    adapter, scanning stops promptly and the device list is presented so the
    user can select it without waiting for the full timeout.
  actual: >
    discover_elm327_devices iterates a fixed number of scan chunks
    (timeout // chunk_duration = 30 // 4 = 7) for the entire 30s timeout and
    never breaks early when the target device is found. The device_found_callback
    fires immediately but the loop ignores it and continues scanning. The device
    list appears only after the full timeout (~31s observed: found 13:43:04,
    presented 13:43:35).
  impact: >
    Setup is slow and appears unresponsive: a ~30s delay between the adapter
    being found and the user being able to select it.
  workaround: "Wait for the full discovery timeout to elapse."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.9"
  os: "Raspberry Pi OS Debian 12 (Linux)"
  dependencies:
    - library: "pygame"
      version: "2.x"
  domain: "domain_2"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    discover_elm327_devices (pairing.py) loops `for chunk in range(chunks)`
    where chunks = max(1, timeout // chunk_duration). Each iteration runs a
    blocking ~4s scan and appends newly classified devices to the result list,
    invoking device_found_callback. There is no condition that terminates the
    loop once a confirmed ELM327 device is present; the loop only exits when
    all chunks are exhausted (full timeout) or on cancellation/error.
  technical_notes: >
    Fix: after processing each chunk's devices, when not in show_all_devices
    mode, break the chunk loop if any discovered device is classified
    DeviceType.HIGHLY_LIKELY_ELM327. The existing final progress_callback(1.0)
    and return path then run unchanged. show_all_devices mode must continue to
    run the full duration so the user can survey all nearby devices.
    Single function, small delta, no interface change.
  related_issues: []
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: "See change-54eeb2d6 and prompt-54eeb2d6"
  change_ref: "change-54eeb2d6"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-54eeb2d6"
  test_refs: []
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-29 | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
