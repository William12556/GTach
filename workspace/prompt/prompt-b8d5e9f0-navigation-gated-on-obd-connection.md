Created: 2026 May 20

# Prompt: Gate Swipe Navigation on OBD Connection State

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Deliverables](<#5.0 deliverables>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Notes](<#7.0 notes>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-b8d5e9f0"
  task_type: "code_generation"
  source_ref: "change-b8d5e9f0"
  date: "2026-05-20"
  iteration: 1
  coupled_docs:
    change_ref: "change-b8d5e9f0"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Swipe gestures navigate between DIGITAL and RADIAL modes regardless of
    OBD connection state. When the transport thread is not RUNNING the
    swipe handlers must return TouchAction.NONE immediately.
    Long-press to settings is unaffected.
  integration: >
    Display domain — src/gtach/display/manager.py only.
    thread_manager.get_thread_status('transport') returns a ThreadStatus enum.
    ThreadStatus.RUNNING is the connected state.
  constraints:
    - "Modify src/gtach/display/manager.py only"
    - "Do not modify manager_backup.py or any backup/test file"
    - "Do not alter _handle_long_press — settings access must remain unblocked"
    - "Change is two guard clauses only — do not refactor surrounding logic"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Add an OBD connection state guard to _handle_swipe_left() and
    _handle_swipe_right(). If the transport thread is not RUNNING,
    log at DEBUG and return TouchAction.NONE without changing mode.
  requirements:
    functional:
      - "_handle_swipe_left() blocked when transport not RUNNING"
      - "_handle_swipe_right() blocked when transport not RUNNING"
      - "_handle_long_press() unchanged"
      - "DEBUG log emitted when swipe is blocked: 'Swipe blocked: OBD not connected'"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Minimal change — guard clause only, no refactoring"
        - "No new imports required (ThreadStatus already imported)"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Two guard clauses added at the top of each swipe handler"
  components:
    - name: "_handle_swipe_left"
      type: "function"
      purpose: "Block mode change when OBD disconnected"
      logic:
        - "At top of method, before existing mode checks:"
        - "  if self.thread_manager.get_thread_status('transport') != ThreadStatus.RUNNING:"
        - "      self.logger.debug('Swipe blocked: OBD not connected')"
        - "      return TouchAction.NONE"
        - "Existing logic follows unchanged"

    - name: "_handle_swipe_right"
      type: "function"
      purpose: "Block mode change when OBD disconnected"
      logic:
        - "Identical guard clause as _handle_swipe_left"
        - "Existing logic follows unchanged"

  dependencies:
    internal:
      - "ThreadStatus (already imported from ..core)"
      - "thread_manager.get_thread_status (ThreadManager)"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Modify the file in place — do not create new files"
  files:
    - path: "src/gtach/display/manager.py"
      content: "Add connection state guard to _handle_swipe_left and _handle_swipe_right"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "Swipe left/right has no effect when transport thread is not RUNNING"
  - "DEBUG log 'Swipe blocked: OBD not connected' emitted when blocked"
  - "Swipe navigation functions normally when transport thread is RUNNING"
  - "Long-press to settings unaffected in all connection states"
  - "No regressions in any display mode"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Notes

```yaml
notes: >
  ThreadStatus is imported in manager.py from ..core.
  Confirm the import is present before implementing; add if missing.
  get_thread_status('transport') returns None if the key is absent —
  the guard handles this correctly since None != ThreadStatus.RUNNING.
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  File: src/gtach/display/manager.py

  Task: Gate swipe navigation on OBD connection state.

  Steps:
  1. Verify ThreadStatus is imported from ..core (add if missing).

  2. In _handle_swipe_left(), insert at top of try block:
       if self.thread_manager.get_thread_status('transport') != ThreadStatus.RUNNING:
           self.logger.debug('Swipe blocked: OBD not connected')
           return TouchAction.NONE

  3. Apply identical guard to _handle_swipe_right().

  4. Do not touch _handle_long_press().

  Constraints:
  - manager.py only; no backups or other files
  - Guard clauses only — no surrounding refactoring

  Success: swipe blocked when disconnected; works when connected; long-press unaffected.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-20 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
