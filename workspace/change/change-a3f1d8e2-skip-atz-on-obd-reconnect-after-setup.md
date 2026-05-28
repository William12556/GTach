Created: 2026 May 28

# Change a3f1d8e2 — Skip ATZ on OBD Reconnect After Setup

---

## Table of Contents

[1.0 Change Information](<#1.0 change information>)
[2.0 Source](<#2.0 source>)
[3.0 Scope](<#3.0 scope>)
[4.0 Rationale](<#4.0 rationale>)
[5.0 Technical Details](<#5.0 technical details>)
[6.0 Testing Requirements](<#6.0 testing requirements>)
[7.0 Verification](<#7.0 verification>)
[Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-a3f1d8e2"
  title: "Skip ATZ on OBD reconnect after setup wizard completes"
  date: "2026-05-28"
  author: "William Watson"
  status: "approved"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a3f1d8e2"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "issue"
  reference: "issue-a3f1d8e2"
  description: >
    OBDProtocol sends ATZ unconditionally on first reconnect after setup wizard
    completes. The setup probe already initialised the adapter. A second ATZ
    causes a timeout and prevents RPM polling from starting.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Add adapter_pre_initialised parameter to OBDProtocol. Set flag at
    construction when called after a successful setup run. Remove 500ms
    settle delay added as workaround in v0.2.56.
  affected_components:
    - name: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  out_of_scope:
    - "Transport layer reconnect logic"
    - "Setup wizard pairing flow"
    - "BluetoothPairing class"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    _adapter_initialised is cleared on every transport disconnect, including the
    setup-probe disconnect. OBD reconnects and sends ATZ unnecessarily, causing
    a timeout because the adapter is not ready immediately after the probe
    disconnects.
  proposed_solution: >
    OBDProtocol accepts adapter_pre_initialised=False at construction. When True,
    _adapter_initialised is pre-set so ATZ is skipped on the first connection.
    App passes True after a successful setup wizard run. The flag is still cleared
    on subsequent mid-session disconnects, preserving normal reconnect behaviour.
  alternatives_considered:
    - option: "Increase ATZ timeout"
      reason_rejected: "Does not eliminate the race; adds latency on every reconnect"
    - option: "Delay OBD start after setup"
      reason_rejected: "Fragile timing dependency; 500ms workaround already insufficient"
  benefits:
    - "Eliminates ATZ on post-setup reconnect"
    - "No additional latency on normal reconnects"
    - "Preserves existing reconnect behaviour for mid-session disconnects"
  risks:
    - risk: "If setup probe fails silently, OBD skips ATZ on an uninitialised adapter"
      mitigation: "adapter_pre_initialised is only set after verified successful setup"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    OBDProtocol.__init__ sets _adapter_initialised=False unconditionally.
    _protocol_loop resets it to False on every disconnect. Every reconnect
    sends ATZ regardless of prior initialisation state.
  proposed_behavior: >
    OBDProtocol.__init__ accepts adapter_pre_initialised: bool = False.
    _adapter_initialised is initialised to this value. When True, the first
    connection skips ATZ. Subsequent disconnects clear the flag as before.
  implementation_approach: >
    1. obd.py: add adapter_pre_initialised parameter to __init__; assign to
       self._adapter_initialised at construction.
    2. obd.py: remove 500ms time.sleep(0.5) settle workaround from
       _protocol_loop.
    3. app.py: after setup wizard completes successfully, set a flag
       self._setup_completed = True; pass adapter_pre_initialised=True
       when constructing OBDProtocol in _start_obd.
  code_changes:
    - component: "OBDProtocol"
      file: "src/gtach/comm/obd.py"
      change_summary: "Add adapter_pre_initialised param; remove 500ms settle delay"
      functions_affected:
        - "__init__"
        - "_protocol_loop"
      classes_affected:
        - "OBDProtocol"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: "Set _setup_completed flag; pass adapter_pre_initialised to OBDProtocol"
      functions_affected:
        - "_start_obd"
        - "_on_setup_complete"
      classes_affected:
        - "GTachApplication"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: "Manual on-device testing with ELM327 emulator"
  test_cases:
    - scenario: "Setup wizard completes — OBD connects without ATZ"
      expected_result: "RPM polling starts within 2 seconds of setup completion; no ATZ timeout in log"
    - scenario: "Mid-session Bluetooth disconnect and reconnect"
      expected_result: "OBD sends ATZ on reconnect as normal; RPM resumes"
    - scenario: "Application restart (no prior setup this session)"
      expected_result: "OBD sends ATZ on first connect as normal"
  validation_criteria:
    - "Log shows no 'Timeout waiting for response' after setup completes"
    - "Log shows 'Starting GTach application v0.2.57' or later"
    - "RPM value displayed within 2 seconds of setup completion"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Verification

```yaml
verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-28 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
