# Prompt: Watchdog Darwin Guard for Display Thread Hard Recovery

Created: 2026 April 15

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Error Handling](<#5.0 error handling>)
- [6.0 Testing](<#6.0 testing>)
- [7.0 Deliverable](<#7.0 deliverable>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-a8f2c3e1"
  task_type: "debug"
  source_ref: "change-a8f2c3e1"
  date: "2026-04-15"
  iteration: 1
  coupled_docs:
    change_ref: "change-a8f2c3e1"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Prevent GTach from crashing with NSInternalInconsistencyException on macOS
    when --transport serial is used and no OBD device is present. The crash occurs
    because WatchdogMonitor._attempt_hard_recovery calls handle_thread_failure for
    the 'display' thread, which causes ThreadManager._restart_thread to start
    _display_loop on a ThreadPoolExecutor worker (background thread), violating
    the macOS Cocoa main-thread requirement for NSApplication event operations.
  integration: >
    Single file edit: src/gtach/core/watchdog.py.
    WatchdogMonitor._attempt_hard_recovery gains a Darwin platform guard at the
    top of its method body. No other files are touched.
  knowledge_references: []
  constraints:
    - "Edit confined to _attempt_hard_recovery in watchdog.py only."
    - "No changes to ThreadManager, DisplayManager, app.py, or any other file."
    - "Linux/Raspberry Pi behaviour must be unchanged."
    - "Existing _initiate_graceful_shutdown method called as-is; no changes to it."
    - "import platform is available at module level in watchdog.py — no new imports needed."
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Insert a Darwin platform guard at the top of
    WatchdogMonitor._attempt_hard_recovery. When platform.system() == 'Darwin'
    AND name == 'display', log a critical message and call
    _initiate_graceful_shutdown; then return without executing the remainder of
    the method. All other calls (any other thread name, or any platform other
    than Darwin) fall through to existing logic unchanged.
  requirements:
    functional:
      - >
        Guard must execute before any existing logic in _attempt_hard_recovery
        (before the force/recovery_attempts check).
      - >
        Guard condition: platform.system() == 'Darwin' and name == 'display'.
      - >
        When guard fires: call self.logger.critical(...) then call
        self._initiate_graceful_shutdown(reason) then return.
      - >
        Log message must identify: the thread name, the timeout duration, and
        the Darwin constraint as the reason.
      - >
        Graceful shutdown reason string passed to _initiate_graceful_shutdown
        must include thread name and timeout value.
      - >
        When guard does NOT fire: all existing method logic executes exactly as
        before — no changes to the non-guard path.
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8"
        - "platform.system() for OS detection per project standard"
        - "logger.critical() for platform constraint enforcement messages"
        - "Google-style docstring update if method docstring exists"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Single targeted insertion at the top of an existing method."
  components:
    - name: "WatchdogMonitor._attempt_hard_recovery"
      type: "method"
      purpose: >
        Existing method that attempts hard recovery by calling
        handle_thread_failure. Modified to detect Darwin + 'display' thread
        and route to graceful shutdown instead.
      interface:
        inputs:
          - name: "name"
            type: "str"
            description: "Thread name being recovered."
          - name: "health"
            type: "ThreadHealth"
            description: "Health tracking object for the thread."
          - name: "timeout"
            type: "float"
            description: "Seconds since last heartbeat."
          - name: "force"
            type: "bool"
            description: "Force recovery regardless of attempt count."
        outputs:
          type: "None"
          description: "Returns early on Darwin + display guard."
        raises: []
      logic:
        - >
          [INSERTION — top of method body, before existing logic]
          if platform.system() == 'Darwin' and name == 'display':
              self.logger.critical(
                  f"Display thread unhealthy on Darwin (timeout: {timeout:.1f}s) — "
                  f"Cocoa main-thread constraint prevents background restart. "
                  f"Initiating graceful shutdown."
              )
              self._initiate_graceful_shutdown(
                  f"Display thread timeout on Darwin: {name} ({timeout:.1f}s)"
              )
              return
        - "[EXISTING logic unchanged below the guard]"
  dependencies:
    internal:
      - "WatchdogMonitor._initiate_graceful_shutdown (existing, no changes)"
      - "platform module (already in Python stdlib, verify import present in watchdog.py)"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: "Guard is defensive — fires only when both conditions match; no exceptions expected."
  exceptions: []
  logging:
    level: "CRITICAL"
    format: "Matches existing watchdog logger format. Logger name: 'WatchdogMonitor'."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing

```yaml
testing:
  unit_tests:
    - scenario: "Darwin, name='display' — guard fires"
      expected: "_initiate_graceful_shutdown called; handle_thread_failure not called; method returns."
    - scenario: "Darwin, name='transport' — guard does not fire"
      expected: "Existing path executes; handle_thread_failure called as before."
    - scenario: "Linux, name='display' — guard does not fire"
      expected: "Existing path executes; handle_thread_failure called as before."
  edge_cases:
    - "name='display' on Darwin with force=True — guard still fires (guard is before force check)."
    - "name='Display' (wrong case) on Darwin — guard does NOT fire (case-sensitive)."
  validation:
    - "Syntax check: python -c \"import ast; ast.parse(open('src/gtach/core/watchdog.py').read())\""
    - >
      Manual macOS test: launch with --transport serial, no device, wait 60s.
      Confirm no NSInternalInconsistencyException. Confirm graceful shutdown log.
    - >
      macOS --transport tcp test: launch with emulator running. Confirm normal
      operation; watchdog guard never fires.
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deliverable

```yaml
deliverable:
  format_requirements:
    - "Modify src/gtach/core/watchdog.py in-place."
    - "Do not create any new files."
    - "Do not modify any other file."
  files:
    - path: "src/gtach/core/watchdog.py"
      content: >
        Insert Darwin guard block at the top of _attempt_hard_recovery method
        body as specified in section 4.0 Design. All other content unchanged.

success_criteria:
  - "Guard block present at top of _attempt_hard_recovery, before existing logic."
  - "Guard condition: platform.system() == 'Darwin' and name == 'display'."
  - "logger.critical(...) called with Darwin constraint explanation."
  - "_initiate_graceful_shutdown called with descriptive reason string."
  - "return statement follows _initiate_graceful_shutdown call."
  - "All existing method logic below guard is byte-for-byte identical to original."
  - "No other methods or files modified."
  - "Syntax check passes: ast.parse() succeeds on modified watchdog.py."
  - "import platform present at module level in watchdog.py."
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  File to modify: src/gtach/core/watchdog.py
  Method: WatchdogMonitor._attempt_hard_recovery

  Task: Insert Darwin platform guard at the TOP of _attempt_hard_recovery,
  before any existing logic.

  Guard code to insert:
      if platform.system() == 'Darwin' and name == 'display':
          self.logger.critical(
              f"Display thread unhealthy on Darwin (timeout: {timeout:.1f}s) — "
              f"Cocoa main-thread constraint prevents background restart. "
              f"Initiating graceful shutdown."
          )
          self._initiate_graceful_shutdown(
              f"Display thread timeout on Darwin: {name} ({timeout:.1f}s)"
          )
          return

  Constraints:
  - Insert guard before existing force/recovery_attempts check.
  - Verify `import platform` is present at module level; add if absent.
  - Touch no other methods, classes, or files.
  - All existing logic below the guard unchanged.

  Verification after edit:
    python -c "import ast; ast.parse(open('src/gtach/core/watchdog.py').read())"

  Deliverable: modified src/gtach/core/watchdog.py only.
```

[Return to Table of Contents](<#table of contents>)

---

## Element Registry

```yaml
element_registry:
  source: "workspace/design/design-gtach-name_registry-master.md"
  entries:
    modules:
      - name: "watchdog"
        path: "src/gtach/core/watchdog.py"
    classes:
      - name: "WatchdogMonitor"
        module: "watchdog"
    functions:
      - name: "_attempt_hard_recovery"
        module: "watchdog"
        signature: "_attempt_hard_recovery(self, name: str, health: ThreadHealth, timeout: float, force: bool = False) -> None"
      - name: "_initiate_graceful_shutdown"
        module: "watchdog"
        signature: "_initiate_graceful_shutdown(self, reason: str) -> None"
```

---

## Notes

```yaml
notes: >
  This change is classified as trivial and surgical per P03 §1.4.12 criteria —
  confined to a single method, net delta ~8 lines, no interface changes,
  unambiguous implementation — but is being executed via Claude Code with T04
  documentation per project practice for critical-severity fixes.
  Execution: paste tactical_brief to Claude Code with instruction:
  implement workspace/prompt/prompt-a8f2c3e1-watchdog-display-restart-darwin.md
```

---

## Version History

| Version | Date       | Author          | Changes                |
| ------- | ---------- | --------------- | ---------------------- |
| 1.0     | 2026-04-15 | William Watson  | Initial prompt creation |

---

Copyright (c) 2026 William Watson. MIT License.
