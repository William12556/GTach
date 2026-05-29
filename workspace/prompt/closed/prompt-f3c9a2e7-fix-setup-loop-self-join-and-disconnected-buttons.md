Created: 2026 May 27

# Prompt: Fix Setup Loop Self-Join and Disconnected Screen Buttons

---

## Table of Contents

[1.0 Prompt Information](<#1.0 prompt information>)
[2.0 Context](<#2.0 context>)
[3.0 Specification](<#3.0 specification>)
[4.0 Design](<#4.0 design>)
[5.0 Error Handling](<#5.0 error handling>)
[6.0 Testing](<#6.0 testing>)
[7.0 Deliverable](<#7.0 deliverable>)
[8.0 Tactical Brief](<#8.0 tactical brief>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-f3c9a2e7"
  task_type: "debug"
  source_ref: "change-f3c9a2e7"
  date: "2026-05-27"
  iteration: 1
  status: "closed"
  coupled_docs:
    change_ref: "change-f3c9a2e7"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Fix two bugs that cause the app to freeze on the DISCONNECTED screen
    after initial Bluetooth setup completes on the Pi.
  integration: >
    Three files are modified: setup.py (setup loop exit), manager.py
    (callback attribute + _enter_setup_from_disconnected), app.py
    (register callback). No new classes or public interfaces.
  constraints:
    - "Do not modify any other logic in _setup_loop beyond the stop_thread call"
    - "setup_entry_callback pattern must mirror the existing on_complete callback"
    - "Guard _enter_setup_from_disconnected with 'if self._setup_entry_callback'"
    - "app.py callback must clear DeviceStore and call _start_setup_mode"
    - "Do not alter OBD, watchdog, or transport logic"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Three targeted single-function edits to eliminate a self-join RuntimeError
    on setup completion and to implement the two DISCONNECTED screen buttons.
  requirements:
    functional:
      - "Setup completes without RuntimeError: cannot join current thread"
      - "Tapping Simulate on DISCONNECTED activates _sim_mode and DIGITAL display"
      - "Tapping Setup on DISCONNECTED clears DeviceStore and enters setup flow"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Thread-safe: no shared state touched without existing locks"
        - "Debug logging for callback invocation and guard branches"
        - "No new dependencies"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Targeted bug-fix — no architectural change"
  components:

    - name: "SetupDisplayManager._setup_loop"
      type: "function"
      purpose: "Exit setup thread cleanly after on_complete fires"
      logic:
        - "Locate: if state.current_screen == SetupScreen.COMPLETE: block"
        - "Remove: self.thread_manager.stop_thread('setup')"
        - "Replace with: break"
        - "The daemon thread exits when _setup_loop returns; no join needed"

    - name: "DisplayManager._initialize_legacy_components (or __init__)"
      type: "function"
      purpose: "Declare setup_entry_callback attribute"
      logic:
        - "Add: self._setup_entry_callback = None"
        - "Place adjacent to existing self._setup_manager = None line"

    - name: "DisplayManager._enter_setup_from_disconnected"
      type: "function"
      purpose: "Invoke app-level setup re-entry callback"
      logic:
        - "Remove stub comment and DIGITAL transition"
        - "If self._setup_entry_callback is not None: call self._setup_entry_callback()"
        - "Else: log warning 'setup_entry_callback not registered'"

    - name: "GTachApplication (app.py)"
      type: "function"
      purpose: "Register setup re-entry callback on DisplayManager"
      logic:
        - "After self._display is constructed (end of __init__ or start of run)"
        - "Define _re_enter_setup(self) method: stop OBD if running, clear DeviceStore, call self._start_setup_mode()"
        - "Assign: self._display._setup_entry_callback = self._re_enter_setup"

  dependencies:
    internal:
      - "src/gtach/display/setup.py"
      - "src/gtach/display/manager.py"
      - "src/gtach/app.py"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: "Guard callback with presence check; log warning on absent callback"
  exceptions:
    - exception: "Any exception in _re_enter_setup"
      condition: "OBD stop or setup start fails"
      handling: "Wrap in try/except; log ERROR with exc_info=True"
  logging:
    level: "DEBUG for callback invocation; WARNING for absent callback; ERROR for exceptions"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing

```yaml
testing:
  unit_tests: []
  edge_cases:
    - "Setup completes a second time after re-entering from DISCONNECTED"
    - "_setup_entry_callback not yet set when DISCONNECTED screen first renders"
  validation:
    - "No 'cannot join current thread' in log after setup completes"
    - "Simulate button reaches DIGITAL/RADIAL within one tap"
    - "Setup button enters setup mode within one tap"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deliverable

```yaml
deliverable:
  format_requirements:
    - "Edit files in-place; do not create new files"
  files:
    - path: "src/gtach/display/setup.py"
      content: "Replace stop_thread('setup') with break in _setup_loop COMPLETE branch"
    - path: "src/gtach/display/manager.py"
      content: "Add _setup_entry_callback = None; implement _enter_setup_from_disconnected"
    - path: "src/gtach/app.py"
      content: "Add _re_enter_setup method; assign to display._setup_entry_callback"

success_criteria:
  - "Three files modified; no other files changed"
  - "setup.py _setup_loop COMPLETE branch contains break, not stop_thread"
  - "manager.py _enter_setup_from_disconnected calls _setup_entry_callback"
  - "app.py assigns _re_enter_setup to display._setup_entry_callback"
  - "No RuntimeError in log on Pi test after setup completion"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Fix two bugs causing DISCONNECTED screen freeze (v0.2.48, rfcomm, Pi).

  FILE 1: src/gtach/display/setup.py
  In _setup_loop, COMPLETE branch (~line 161):
    Remove:  self.thread_manager.stop_thread('setup')
    Add:     break
  (Thread exits when function returns; joining current thread is illegal.)

  FILE 2: src/gtach/display/manager.py
  In _initialize_legacy_components (near self._setup_manager = None):
    Add:  self._setup_entry_callback = None

  Replace _enter_setup_from_disconnected body:
    if self._setup_entry_callback:
        self.logger.info("Invoking setup_entry_callback from DISCONNECTED")
        self._setup_entry_callback()
    else:
        self.logger.warning("setup_entry_callback not registered")

  FILE 3: src/gtach/app.py
  Add method to GTachApplication:
    def _re_enter_setup(self) -> None:
        try:
            self.logger.info("Re-entering setup from DISCONNECTED screen")
            # Stop OBD if running
            self._thread_manager.stop_thread('obd_protocol')
            self._thread_manager.stop_thread('transport')
            self._obd_started = False
            # Clear stored device
            self._device_store.clear()
            # Re-enter setup
            self._start_setup_mode()
        except Exception as e:
            self.logger.error(f"Re-enter setup error: {e}", exc_info=True)

  After display_manager construction in __init__ or run():
    self._display._setup_entry_callback = self._re_enter_setup

  Success: no RuntimeError after setup; Simulate and Setup buttons functional.
```

[Return to Table of Contents](<#table of contents>)

---

Copyright (c) 2026 William Watson. MIT License.
