Created: 2026 May 07

# Issue: Remove macOS Runtime Code

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Behavior](<#4.0 behavior>)
- [5.0 Analysis](<#5.0 analysis>)
- [6.0 Resolution](<#6.0 resolution>)
- [Version History](<#version history>)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-f3a1c9e2"
  title: "Remove macOS runtime code"
  date: "2026-05-07"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a1c9e2"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "requirement_change"
  description: >
    macOS runtime support was originally added to enable visual verification of
    UI layouts and general workflow during development. After extended investigation,
    the SDL2/Cocoa event model on macOS Apple Silicon (SDL 2.28.4, pygame 2.6.1)
    cannot be made reliable — pygame.event.poll() blocks when mouse buttons are
    held, and no viable workaround exists within the pygame/SDL2 stack without
    invasive architectural changes.

    macOS development testing has been reduced to headless startup/shutdown
    verification only, which provides negligible value over Pi testing.

    Decision: remove all macOS-specific runtime code. The Mac remains the build
    platform only (wheel build, scp, install). Pi is the sole test and deployment
    target.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "DisplayRenderingEngine"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
    - name: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
    - name: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
    - name: "SerialTransport"
      file_path: "src/gtach/comm/serial_transport.py"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "PlatformDetector"
      file_path: "src/gtach/utils/platform.py"
    - name: "ConfigManager"
      file_path: "src/gtach/utils/config.py"
    - name: "DependencyChecker"
      file_path: "src/gtach/utils/dependencies.py"
    - name: "DependencyService"
      file_path: "src/gtach/utils/services/dependency.py"
    - name: "PerformancePlatform enum"
      file_path: "src/gtach/display/performance.py"
    - name: "main (CLI)"
      file_path: "src/gtach/main.py"
    - name: "README"
      file_path: "README.md"
    - name: "macOS startup script"
      file_path: "start-gtach-macos-tcp.sh"
  version: "0.2.23"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Behavior

```yaml
behavior:
  expected: >
    Codebase contains no macOS-specific runtime paths, Darwin guards, SDL dummy
    driver setup, headless mode, macOS gesture workers, or Mac-specific transport
    discovery. The --macos CLI flag is removed. README reflects Pi-only deployment.
    start-gtach-macos-tcp.sh is deleted.
  actual: >
    Codebase contains Darwin guards and macOS code paths across 13 source files
    and 2 non-source files accumulated over multiple development sessions.
    Current macOS mode is headless (SDL dummy driver) providing no meaningful
    test value. The --macos flag still exists in CLI.
  impact: "Complexity without benefit. Dead code paths and confusing dual-platform surface."
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Analysis

```yaml
analysis:
  root_cause: >
    macOS support was added incrementally to enable local visual testing.
    SDL2/Cocoa event blocking on Apple Silicon proved unresolvable within
    the pygame 2.6.1 / SDL 2.28.4 stack. The code was reduced to headless
    mode, which has no testing value. The complexity remains without benefit.
  technical_notes: >
    Files to modify (source code):
      1. src/gtach/display/rendering/engine.py
         - Remove Darwin branch in initialize()
         - Remove use_window attribute and all references
         - SDL_VIDEODRIVER dummy applies to all platforms — simplify
      2. src/gtach/display/manager.py
         - Remove _is_macos attribute and gesture worker initialization
         - Remove run_main_thread_loop() or make it a no-op stub
         - Remove Darwin guards in start() and stop()
         - Remove _gesture_worker(), _dispatch_mouse_gesture(),
           _mouse_event_queue, and related mouse state attributes
         - Remove _is_macos branch in _display_loop() event processing
      3. src/gtach/app.py
         - Remove Darwin branch in run()
         - Use signal.pause() unconditionally
      4. src/gtach/core/watchdog.py
         - Remove Darwin guard in _attempt_hard_recovery()
         - Remove "Cocoa main-thread constraint" message
         - Simplify: display thread can always be restarted
      5. src/gtach/core/thread.py
         - Remove Darwin branch (line 164)
      6. src/gtach/comm/serial_transport.py
         - Remove Darwin guard that skips /dev/tty.* ports
         - That guard was Mac-specific; Pi uses /dev/rfcomm* only
      7. src/gtach/display/setup_components/bluetooth/interface.py
         - Remove Darwin guard in __init__ (line 40)
         - Remove Darwin guard in start_discovery (line 142)
         - Remove _start_macos_serial_discovery() method entirely
         - Remove _macos_discovery_task inner function
      8. src/gtach/utils/platform.py
         - Remove Darwin detection branch (line 464) if it produces
           a Mac-specific platform type; retain Linux/Pi detection
      9. src/gtach/utils/config.py
         - Remove is_mac flag (lines 334, 1599)
      10. src/gtach/utils/dependencies.py
          - Remove is_macos flag and all references (lines 103, 119, 251)
      11. src/gtach/utils/services/dependency.py
          - Remove macos platform requirement check (line 329)
      12. src/gtach/display/performance.py
          - Remove MACOS enum value from platform enum (line 67)
      13. src/gtach/main.py
          - Remove --macos argument (line 34)

    Files to modify (non-source):
      14. README.md
          - Remove §1.1 Development (macOS) from Requirements
          - Remove §2 Development Setup (Mac-specific venv instructions)
          - Remove §4.2 Mac running section
          - Update to reflect Pi-only workflow
      15. start-gtach-macos-tcp.sh
          - Delete file (provide rm command for human execution)
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  approach: "Remove all Darwin/macOS runtime paths per affected scope above"
  change_ref: "change-f3a1c9e2"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-07 | Initial issue |

---

Copyright (c) 2026 William Watson. MIT License.
