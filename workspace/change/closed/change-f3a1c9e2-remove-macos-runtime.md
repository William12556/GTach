Created: 2026 May 07

# Change: Remove macOS Runtime Code

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Testing Requirements](<#6.0 testing requirements>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-f3a1c9e2"
  title: "Remove macOS runtime code"
  date: "2026-05-07"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f3a1c9e2"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "enhancement"
  reference: "issue-f3a1c9e2"
  description: >
    Remove all macOS-specific runtime code. Mac remains build platform only.
    Pi is sole test and deployment target.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Delete all Darwin/macOS runtime paths from 13 source files. Remove
    start-gtach-macos-tcp.sh. Update README to reflect Pi-only workflow.
  affected_components:
    - name: "DisplayRenderingEngine"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
    - name: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "SerialTransport"
      file_path: "src/gtach/comm/serial_transport.py"
      change_type: "modify"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "modify"
    - name: "PlatformDetector"
      file_path: "src/gtach/utils/platform.py"
      change_type: "modify"
    - name: "ConfigManager"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
    - name: "DependencyChecker"
      file_path: "src/gtach/utils/dependencies.py"
      change_type: "modify"
    - name: "DependencyService"
      file_path: "src/gtach/utils/services/dependency.py"
      change_type: "modify"
    - name: "PerformancePlatform"
      file_path: "src/gtach/display/performance.py"
      change_type: "modify"
    - name: "main CLI"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "README"
      file_path: "README.md"
      change_type: "modify"
    - name: "macOS startup script"
      file_path: "start-gtach-macos-tcp.sh"
      change_type: "delete"
  out_of_scope:
    - "Build tooling (build.sh, pyproject.toml) — Mac is still the build host"
    - "Transport selection logic unrelated to Darwin guards"
    - "Platform detection used for Pi-specific hardware (RPi.GPIO, HyperPixel)"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    macOS runtime code accumulated across 13 source files during an unsuccessful
    attempt to enable local visual testing. The SDL2/Cocoa event model on Apple
    Silicon (SDL 2.28.4 / pygame 2.6.1) causes pygame.event.poll() to block on
    mouse button hold events with no viable workaround. macOS mode was reduced
    to headless (SDL dummy driver), providing only startup/shutdown verification
    — negligible value over Pi testing.
  proposed_solution: >
    Remove all Darwin runtime paths. Mac remains the build host (./build.sh,
    scp, install.sh). Pi is the sole runtime target.
  benefits:
    - "Eliminates ~200 lines of dead/harmful code"
    - "Removes confusing dual-platform surface area"
    - "Simplifies display, transport, and setup code paths"
    - "Eliminates the --macos CLI flag that no longer does anything useful"
  risks:
    - risk: "Darwin guards in serial_transport.py also skip /dev/tty.* ports"
      mitigation: "That guard is Mac-only. Pi uses /dev/rfcomm* — unaffected."
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    Application contains Darwin platform checks across display, transport,
    watchdog, thread manager, Bluetooth setup, and utility modules.
    macOS mode runs headless with SDL dummy driver. --macos CLI flag exists.
  proposed_behavior: >
    Single platform target: Pi/Linux. No Darwin checks at runtime.
    SDL_VIDEODRIVER=dummy set unconditionally (already required for Pi
    off-screen rendering). signal.pause() used unconditionally in app.run().
  implementation_approach: >
    File-by-file removal of Darwin guards and macOS-specific methods.
    Where a Darwin guard wraps the only path, the guard is removed and
    the Pi/Linux path becomes unconditional. See issue-f3a1c9e2 §5.0
    analysis.technical_notes for per-file detail.
  code_changes:
    - component: "DisplayRenderingEngine"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: >
        Remove Darwin branch in initialize(). Remove use_window attribute.
        SDL_VIDEODRIVER=dummy becomes unconditional. Remove use_window
        checks in write_to_framebuffer() (already removed in prior session).
      functions_affected:
        - "initialize()"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Remove _is_macos attribute (set False). Remove gesture worker init,
        _gesture_worker(), _dispatch_mouse_gesture(), mouse state attributes,
        _mouse_event_queue. Remove _is_macos branch in _display_loop().
        Remove Darwin guards in start() and stop(). run_main_thread_loop()
        becomes no-op or is removed.
      functions_affected:
        - "__init__()"
        - "start()"
        - "stop()"
        - "_display_loop()"
        - "_gesture_worker()"
        - "_dispatch_mouse_gesture()"
        - "run_main_thread_loop()"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Remove Darwin branch in run(). Use signal.pause() unconditionally.
      functions_affected:
        - "run()"
    - component: "WatchdogMonitor"
      file: "src/gtach/core/watchdog.py"
      change_summary: >
        Remove Darwin guard in _attempt_hard_recovery(). Display thread
        can always be restarted on Pi.
      functions_affected:
        - "_attempt_hard_recovery()"
    - component: "ThreadManager"
      file: "src/gtach/core/thread.py"
      change_summary: "Remove Darwin branch (line 164)."
    - component: "SerialTransport"
      file: "src/gtach/comm/serial_transport.py"
      change_summary: >
        Remove Darwin guard that skips /dev/tty.* ports. That guard
        is Mac-only; Pi serial discovery uses /dev/rfcomm* and is unaffected.
      functions_affected:
        - "_discover_port()"
    - component: "BluetoothSetupInterface"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: >
        Remove Darwin guard in __init__() (line 40) and start_discovery()
        (line 142). Remove _start_macos_serial_discovery() method and
        _macos_discovery_task inner function entirely.
      functions_affected:
        - "__init__()"
        - "start_discovery()"
        - "_start_macos_serial_discovery()"
    - component: "PlatformDetector"
      file: "src/gtach/utils/platform.py"
      change_summary: >
        Remove Darwin detection branch (line 464) that produces a
        MACOS platform type. Retain all Pi/Linux detection paths.
    - component: "ConfigManager"
      file: "src/gtach/utils/config.py"
      change_summary: "Remove is_mac flag (lines 334, 1599)."
    - component: "DependencyChecker"
      file: "src/gtach/utils/dependencies.py"
      change_summary: >
        Remove is_macos flag from platform_info dict and all usage
        (lines 103, 119, 251).
    - component: "DependencyService"
      file: "src/gtach/utils/services/dependency.py"
      change_summary: "Remove macos platform requirement check (line 329)."
    - component: "PerformancePlatform"
      file: "src/gtach/display/performance.py"
      change_summary: "Remove MACOS enum value (line 67)."
    - component: "main CLI"
      file: "src/gtach/main.py"
      change_summary: "Remove --macos argument (line 34)."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: >
    Deploy to Pi and verify: clean startup, splash, WELCOME screen, touch
    response, no regressions in Bluetooth setup flow. No Mac-side testing
    required or possible after this change.
  validation_criteria:
    - "python -c 'import ast; ast.parse(open(f).read())' passes for all modified files"
    - "No import errors on Pi startup"
    - "Splash → WELCOME transition confirmed in Pi log"
    - "grep -r Darwin src/gtach/ returns no matches"
    - "grep -r macos src/gtach/main.py returns no matches"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-07 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
