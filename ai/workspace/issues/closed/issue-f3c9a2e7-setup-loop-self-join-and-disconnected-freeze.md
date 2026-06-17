Created: 2026 May 27

# Issue: Setup Loop Self-Join and Disconnected Screen Freeze

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
  id: "issue-f3c9a2e7"
  title: "Setup loop self-join RuntimeError causes freeze on DISCONNECTED screen"
  date: "2026-05-27"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3c9a2e7"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "user_report"
  test_ref: "gtach-debug.log 2026-05-27"
  description: >
    On-Pi test with rfcomm transport. After setup completes the DISCONNECTED
    screen is displayed and does not respond to Setup or Simulate button taps.
    Debug log confirms RuntimeError: cannot join current thread raised inside
    _setup_loop, and _enter_setup_from_disconnected is an unimplemented stub
    that transitions to DIGITAL, which immediately re-enters DISCONNECTED
    because the transport thread has not yet reached RUNNING state.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
  designs:
    - design_ref: "design-2c6b8e4d-domain_display.md"
    - design_ref: "design-a3b4c5d6-component_display_setup_manager.md"
  version: "0.2.48"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: "Pi deployment with rfcomm transport; stored device present; ELM327 adapter reachable"
  steps:
    - "Boot GTach on Pi (gtach --debug)"
    - "Wait for splash and setup CURRENT_DEVICE screen"
    - "Tap Continue — device is probed via RFCOMMTransport.connect()"
    - "On_complete fires; app transitions to normal OBD mode"
    - "Observe DISCONNECTED screen; tap Setup or Simulate buttons"
  frequency: "always"
  reproducibility_conditions: "rfcomm transport with stored device"
  error_output: |
    2026-05-27 12:15:42,545 SetupDisplayManager ERROR Setup loop error: cannot join current thread
    Traceback (most recent call last):
      File ".../gtach/display/setup.py", line 161, in _setup_loop
        self.thread_manager.stop_thread('setup')
      File ".../gtach/core/thread.py", line 466, in stop_thread
        thread_info.thread.join(timeout=timeout)
      File ".../threading.py", line 1030, in join
        raise RuntimeError("cannot join current thread")
    RuntimeError: cannot join current thread
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behaviour

```yaml
behavior:
  expected: >
    After setup completes the app transitions cleanly to OBD mode. If OBD
    is not yet connected the DISCONNECTED screen is shown. Tapping Simulate
    activates simulation mode and RPM display begins. Tapping Setup re-enters
    the Bluetooth setup flow.
  actual: >
    _setup_loop calls stop_thread('setup') from within the setup thread,
    raising RuntimeError: cannot join current thread. The exception is caught
    and the loop retries after 1 s. Meanwhile on_complete has already fired,
    exiting setup mode and starting OBD. The display enters DISCONNECTED.
    Tapping Simulate has no effect because _on_simulation_mode transitions
    to DIGITAL, which immediately re-evaluates transport status and falls
    back to DISCONNECTED. Tapping Setup calls _enter_setup_from_disconnected,
    a stub that also transitions to DIGITAL and loops back to DISCONNECTED.
    The screen is effectively frozen.
  impact: >
    Application is unusable after initial setup. Simulate and Setup buttons
    on DISCONNECTED screen are non-functional. Only restart recovers.
  workaround: "Restart GTach."
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
    Three distinct defects contribute to the freeze:

    1. Self-join in _setup_loop (setup.py line 161): When SetupScreen.COMPLETE
       is reached, _setup_loop calls self.thread_manager.stop_thread('setup').
       stop_thread calls thread.join() on the calling thread itself, which
       Python disallows (RuntimeError). The fix is to break out of the loop
       directly; the daemon thread exits naturally without a join.

    2. Unimplemented _enter_setup_from_disconnected (manager.py): The method
       is a documented stub. It transitions to DIGITAL, which immediately
       re-enters _render_disconnected because transport is not RUNNING.
       The fix is to invoke the app-level setup re-entry path, clearing
       the device store and starting SetupDisplayManager.

    3. Transport RUNNING race: After on_complete fires, the OBD protocol
       thread is registered and started but may not reach RUNNING state
       within one display frame. The display falls to DISCONNECTED for
       one or more frames. This is a secondary cosmetic effect; the primary
       lock is defect 1 and 2 above.

  technical_notes: >
    Defect 1 fix: replace stop_thread call with break in _setup_loop.
    Defect 2 fix: implement _enter_setup_from_disconnected to call the
    app controller callback registered on DisplayManager, which clears
    DeviceStore and re-initialises SetupDisplayManager. Requires a
    setup_entry_callback attribute on DisplayManager, set by app.py
    analogous to the existing on_complete callback pattern.
    Defect 3: no code change required; arises naturally from async
    thread startup and resolves within one reconnect cycle.
  related_issues: []
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  target_date: "2026-05-28"
  approach: "See change-f3c9a2e7 and prompt-f3c9a2e7"
  change_ref: "change-f3c9a2e7"
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
    - "design-2c6b8e4d-domain_display.md"
    - "design-a3b4c5d6-component_display_setup_manager.md"
  change_refs:
    - "change-f3c9a2e7"
  test_refs: []
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-27 | Initial issue document |

---

Copyright (c) 2026 William Watson. MIT License.
