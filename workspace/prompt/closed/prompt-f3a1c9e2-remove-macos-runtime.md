Created: 2026 May 07

# Prompt: Remove macOS Runtime Code

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Per-File Instructions](<#4.0 per-file instructions>)
- [5.0 Non-Source Changes](<#5.0 non-source changes>)
- [6.0 Deliverables](<#6.0 deliverables>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-f3a1c9e2"
  task_type: "refactor"
  source_ref: "change-f3a1c9e2"
  date: "2026-05-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a1c9e2"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Remove all macOS-specific runtime code from GTach. Mac is build host only.
    Pi/Linux is the sole runtime target.
  integration: >
    GTach is a Pi-deployed OBD-II tachometer. Display uses pygame with SDL
    dummy driver and Linux framebuffer. Transport uses Bluetooth SPP on Pi.
    No macOS runtime is required or desired.
  constraints:
    - "Do not remove build tooling (build.sh, pyproject.toml)"
    - "Do not remove Pi/Linux platform detection (RPi.GPIO, HyperPixel, framebuffer)"
    - "Do not modify any file not listed in §4.0"
    - "Preserve all existing Pi runtime behaviour exactly"
    - "After each file edit, verify with: python -c \"import ast; ast.parse(open('<file>').read())\""
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Surgical removal of Darwin/macOS guards and methods. Where a Darwin branch
    is the only path, remove the guard and make the Pi/Linux path unconditional.
    Where a method exists solely for macOS, delete it entirely.
  requirements:
    functional:
      - "No Darwin platform checks remain in src/gtach/ after change"
      - "No --macos CLI argument in main.py"
      - "signal.pause() used unconditionally in app.run()"
      - "SDL_VIDEODRIVER=dummy set unconditionally in engine.initialize()"
      - "display_thread.start() called unconditionally in DisplayManager.start()"
      - "display_thread.join() called unconditionally in DisplayManager.stop()"
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "All modified files must parse cleanly (ast.parse)"
        - "No unused imports introduced"
        - "No functional changes to Pi runtime paths"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Per-File Instructions

### 4.1 src/gtach/display/rendering/engine.py

In `DisplayRenderingEngine.__init__()`:
- Remove the `self.use_window = False` attribute and comment.

In `DisplayRenderingEngine.initialize()`:
- Replace the entire Darwin/else branch with a single unconditional line:
  ```python
  os.environ['SDL_VIDEODRIVER'] = 'dummy'
  ```
  Then call `pygame.display.init()` and `pygame.font.init()` unconditionally
  (they follow immediately — no other changes needed in this block).
- Remove `self.use_window = False` and `import platform as _platform` if they
  were introduced only for this branch.

Verify `write_to_framebuffer()` contains no `use_window` references (already
removed in prior session — confirm with grep).

### 4.2 src/gtach/display/manager.py

In `DisplayManager.__init__()`:
- Remove the entire macOS mouse-as-touch simulation block:
  the `import platform as _plat`, `self._is_macos = ...`, and the
  `if self._is_macos:` block initialising mouse state and gesture worker.
- Remove `self._is_macos = False` line if present.

In `DisplayManager.start()`:
- Remove Darwin guard. Call `self.display_thread.start()` unconditionally.
- Update docstring to remove macOS reference.

In `DisplayManager.run_main_thread_loop()`:
- Remove method entirely, or replace body with `pass` if callers must not break.
  Prefer removal if no external callers exist outside app.py (which is also
  being modified to not call it).

In `DisplayManager.stop()`:
- Remove Darwin guard. Call `self.display_thread.join()` unconditionally.

In `DisplayManager._display_loop()`:
- Remove `elif self._is_macos:` branch and all nested mouse event handling
  (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP blocks).
- The outer `if event.type == pygame.QUIT` check remains.

Remove these methods entirely:
- `_gesture_worker()`
- `_dispatch_mouse_gesture()`

Remove these attributes if they remain after the above removals:
- `_mouse_down_pos`, `_mouse_down_time`, `_mouse_dragging`,
  `_mouse_current_pos`, `_mouse_event_queue`, `_gesture_worker_thread`

### 4.3 src/gtach/app.py

In `GTachApplication.run()`:
- Remove `import platform as _platform`.
- Remove Darwin branch. Use `signal.pause()` unconditionally.

### 4.4 src/gtach/core/watchdog.py

In `WatchdogMonitor._attempt_hard_recovery()`:
- Remove the Darwin guard block:
  ```python
  if platform.system() == 'Darwin' and name == 'display':
      self.logger.critical(...)
      self._initiate_graceful_shutdown(...)
      return
  ```
- The display thread can be restarted normally on Pi.
- Remove `import platform` if it is no longer used elsewhere in the file.

### 4.5 src/gtach/core/thread.py

- Locate line 164: `if platform.system() == 'Darwin':` and remove that
  Darwin branch entirely.
- Remove `import platform` if no longer used elsewhere in the file.

### 4.6 src/gtach/comm/serial_transport.py

In `SerialTransport._discover_port()`:
- Remove the Darwin guard that skips `/dev/tty.*` ports:
  ```python
  if platform.system() == 'Darwin' and '/dev/tty.' in port.device:
      continue
  ```
- Remove `import platform` if no longer used elsewhere in the file.

### 4.7 src/gtach/display/setup_components/bluetooth/interface.py

In `BluetoothSetupInterface.__init__()`:
- Remove Darwin guard (line ~40):
  ```python
  if platform.system() != 'Darwin' or pairing_factory is not None:
  ```
  Replace with unconditional initialisation of the Bluetooth pairing object.

In `BluetoothSetupInterface.start_discovery()` (or equivalent method):
- Remove Darwin branch (line ~142):
  ```python
  if platform.system() == 'Darwin':
      self._start_macos_serial_discovery(state)
  ```
  Remove that branch entirely. The remaining path (Pi Bluetooth discovery)
  becomes unconditional.

Remove entirely:
- `BluetoothSetupInterface._start_macos_serial_discovery()` method
  and its inner `_macos_discovery_task` and `on_complete` functions.

Remove `import platform` if no longer used elsewhere in the file.

### 4.8 src/gtach/utils/platform.py

- Remove the Darwin detection branch at line 464 that produces a MACOS
  platform type or score. Retain all RPi, Linux, and generic detection paths.
- Remove `import platform` only if no longer used; it is likely still needed
  for `platform.system()` calls that detect Linux/Pi.

### 4.9 src/gtach/utils/config.py

- Remove `'is_mac': system == 'Darwin'` dict entry (line ~334).
- Remove `is_mac = system == 'Darwin'` assignment (line ~1599) and any
  `if is_mac:` branches that follow it.
- Remove `import platform` only if no longer used elsewhere in the file.

### 4.10 src/gtach/utils/dependencies.py

- Remove `'is_macos': system == 'Darwin'` from the platform_info dict (line ~103).
- Remove `platform_info['is_macos'] or` from any boolean expression (line ~119).
- Remove `if "macos" in dep.platforms and self.platform_info['is_macos']:` branch
  (line ~251).

### 4.11 src/gtach/utils/services/dependency.py

- Remove `elif requirement == 'macos' and not platform_info.get('is_macos', False):`
  branch (line ~329).

### 4.12 src/gtach/display/performance.py

- Remove `MACOS = "macos"` from the platform enum (line ~67).

### 4.13 src/gtach/main.py

- Remove `parser.add_argument('--macos', action='store_true')` (line ~34).

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Non-Source Changes

### 5.1 README.md

Edit `/Users/williamwatson/Documents/GitHub/GTach/README.md`:

- In Requirements section: remove `§1.1 Development (macOS)` subsection entirely.
- In Development Setup section: remove Mac-specific venv/pip instructions;
  retain only the git clone line as context.
- In Running GTach section: remove `§4.2 Mac (development)` subsection entirely.
- Update Version History with a new entry recording these changes.

### 5.2 start-gtach-macos-tcp.sh

Do NOT delete this file directly. Provide the following command for human
execution:

```bash
rm /Users/williamwatson/Documents/GitHub/GTach/start-gtach-macos-tcp.sh
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deliverables

```yaml
deliverable:
  files:
    - path: "src/gtach/display/rendering/engine.py"
    - path: "src/gtach/display/manager.py"
    - path: "src/gtach/app.py"
    - path: "src/gtach/core/watchdog.py"
    - path: "src/gtach/core/thread.py"
    - path: "src/gtach/comm/serial_transport.py"
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - path: "src/gtach/utils/platform.py"
    - path: "src/gtach/utils/config.py"
    - path: "src/gtach/utils/dependencies.py"
    - path: "src/gtach/utils/services/dependency.py"
    - path: "src/gtach/display/performance.py"
    - path: "src/gtach/main.py"
    - path: "README.md"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "All 13 source files parse cleanly via ast.parse"
  - "grep -r Darwin src/gtach/ --include='*.py' returns no matches"
  - "grep 'macos' src/gtach/main.py returns no matches"
  - "grep 'is_macos\\|is_mac' src/gtach/utils/dependencies.py src/gtach/utils/config.py returns no matches"
  - "No references to _gesture_worker, _mouse_event_queue, run_main_thread_loop remain in manager.py"
  - "README.md contains no macOS development or run instructions"
  - "start-gtach-macos-tcp.sh rm command provided to human"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Remove all macOS/Darwin runtime code from GTach. 13 source files + README.

  For each file in §4.0:
  - Read the current file
  - Apply the removals described for that file
  - Verify with: python -c "import ast; ast.parse(open('<file>').read())"
  - Do not modify any file not listed

  Key removals per file:
  1. engine.py: remove Darwin branch in initialize(); SDL_VIDEODRIVER=dummy unconditional
  2. manager.py: remove _is_macos, gesture worker, mouse state, Darwin guards in start/stop
  3. app.py: remove Darwin branch in run(); signal.pause() unconditional
  4. watchdog.py: remove Darwin guard in _attempt_hard_recovery()
  5. thread.py: remove Darwin branch line 164
  6. serial_transport.py: remove Darwin /dev/tty.* skip guard in _discover_port()
  7. bluetooth/interface.py: remove Darwin guards in __init__ and start_discovery;
     delete _start_macos_serial_discovery() method entirely
  8. utils/platform.py: remove Darwin/MACOS platform type detection
  9. utils/config.py: remove is_mac flag lines 334 and 1599
  10. utils/dependencies.py: remove is_macos from platform_info; remove all usage
  11. utils/services/dependency.py: remove macos requirement check line 329
  12. display/performance.py: remove MACOS enum value line 67
  13. main.py: remove --macos argument line 34

  README.md: remove macOS Requirements, Development Setup, and Run sections.

  After all edits, provide this rm command for the human to execute:
    rm /Users/williamwatson/Documents/GitHub/GTach/start-gtach-macos-tcp.sh

  Do not delete or move any file directly.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-07 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
