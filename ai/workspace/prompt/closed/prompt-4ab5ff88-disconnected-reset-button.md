Created: 2026 August 14

# Prompt: Replace the DISCONNECTED Screen's Bluetooth Reset Button With a Reset Button That Reboots the Pi

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-4ab5ff88"
  task_type: "refactor"
  source_ref: "change-4ab5ff88"
  target_profile: "claude_code"
  date: "2026-08-14"
  iteration: 1
  coupled_docs:
    change_ref: "change-4ab5ff88"
    change_iteration: 1

context:
  purpose: >
    hciconfig hci0 reset (the DISCONNECTED screen's "BT Reset" button)
    frequently fails to restore the Bluetooth link; only a reboot of
    the Pi has proven reliable in the field. Remove the
    Bluetooth-adapter-reset path entirely and replace it with a
    "Reset" button that reboots the Pi directly.
  integration: >
    Deletes src/gtach/utils/bluetooth_reset.py and
    tests/test_bluetooth_reset.py. Adds src/gtach/utils/pi_reset.py
    and tests/test_pi_reset.py. Modifies the dispatch method and its
    two wiring sites in src/gtach/app.py, the button identifiers and
    label in src/gtach/display/manager.py, and two attribute
    references in tests/test_disconnected_screen.py.
  knowledge_references:
    - "ai/workspace/issues/issue-4ab5ff88-disconnected-reset-button.md"
    - "ai/workspace/change/change-4ab5ff88-disconnected-reset-button.md"
  constraints:
    - "CRITICAL: the reboot dispatch must NEVER run on the display thread. 'display' is a watchdog critical thread at a 45 s timeout, and since change-2ac1c602 a critical timeout terminates the process — so a synchronous subprocess in the touch callback would race the reboot itself. Dispatch to a daemon worker thread and return immediately, exactly as the Bluetooth reset it replaces did."
    - "CRITICAL: there must be NO automatic invocation of reboot_device, on any trigger — not a wedge diagnosis, not a retry count, not startup, not a timer. The button callback is the only call site."
    - "Do not use shell=True anywhere. Invoke a fixed argument list, ['/sbin/reboot'], with no arguments and no value derived from configuration, the network or the operator."
    - "Invoke /sbin/reboot at that literal, fixed path. Do NOT use shutil.which, systemctl reboot, or shutdown -r now — this was an explicit choice, not an oversight."
    - "src/gtach/utils/bluetooth_reset.py and tests/test_bluetooth_reset.py must be deleted, not left in place unwired. There is no remaining caller once this change lands."
    - "subprocess may be imported ONLY in src/gtach/utils/pi_reset.py. It must appear nowhere else, and in particular nowhere under src/gtach/comm/, where change-5e7a03c4 forbids it."
    - "Do not modify src/gtach/comm/, gtach.service, or install.sh. User=root in gtach.service already covers the reboot call's privilege requirement; no unit change is needed."
    - "Do not modify _button_column, the reconnect spinner, the cause-line rendering geometry, or the Setup button's spec."
    - "Do not add any outcome string to the cause line for the reset action. A successful reboot ends the process before any such status could be read; the debounce Event alone prevents a stacked second invocation. This is a deliberate simplification versus the Bluetooth-reset design it replaces, not an oversight — do not port over _bt_reset_status, _bt_reset_lock, or the merge branch in _disconnected_cause."
    - "Historical prose in comments or docstrings that refers to the retired Bluetooth Reset button as a past event (for example, tests/test_disconnected_screen.py's module docstring explaining why the reconnect spinner moved) is NOT in scope and must not be altered — only executable identifiers, registered region ids, and the drawn label change."
    - "Python 3.9+ compatible. PEP 8. Type hints on all public interfaces. Google-style docstrings."

specification:
  description: "Apply edits W, X, Y and Z, then add the unit tests in the testing section."
  requirements:
    functional:
      - "A Reset button press dispatches a Pi reboot to a worker thread and returns immediately."
      - "A press while a reboot is in flight is ignored, not queued."
      - "The reboot invocation is bounded by a timeout; a hung command does not block the worker forever."
      - "reboot_device never raises, on any input or environment."
      - "The DISCONNECTED screen's second button is registered and drawn only when the reset callback is set, exactly as the Bluetooth Reset button was."
      - "The Setup button's rect is identical whether one or two buttons are registered."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "The display loop continues rendering at 30 FPS throughout a reset dispatch (up to the point the OS begins shutting the process down)"
      metric: "time"

design:
  architecture: >
    The privileged surface remains one function in one module, called
    from one place behind one button — the same shape as the Bluetooth
    reset it replaces, with the module's responsibility transferred
    rather than duplicated.
  components:
    - name: "EDIT W — delete src/gtach/utils/bluetooth_reset.py and tests/test_bluetooth_reset.py"
      type: "module"
      purpose: "Remove the Bluetooth-adapter-reset path entirely; no remaining caller after EDIT Y."
      logic:
        - "Delete both files outright."
    - name: "EDIT X — src/gtach/utils/pi_reset.py"
      type: "module"
      purpose: "Own the privileged reboot operation, in one reviewable place, taking over bluetooth_reset.py's role as GTach's only subprocess-permitted module."
      logic:
        - "New module with the project's standard copyright header and a module docstring stating that this is the ONLY place in GTach permitted to invoke an external command, and why (mirror bluetooth_reset.py's docstring structure: single call site, no shell=True, fixed argument list at a fixed path)."
        - "Import logging, os and subprocess. No other imports."
        - "Module constant _REBOOT_PATH = '/sbin/reboot'."
        - "Add `def reboot_device(timeout: float = 10.0) -> str:` returning a short outcome string, 40 characters or fewer, never empty, and never raising."
        - "Body: if not os.path.exists(_REBOOT_PATH), return 'reboot command not found' without attempting subprocess.run."
        - "Otherwise run [_REBOOT_PATH] with subprocess.run(capture_output=True, timeout=timeout, check=False). If returncode == 0, return 'reboot initiated'. Otherwise return 'reboot command failed'."
        - "Catch subprocess.TimeoutExpired and return 'reboot timed out'. subprocess.run has already killed the child; do not add a second kill."
        - "Catch PermissionError and return 'reboot not permitted'."
        - "Catch FileNotFoundError and return 'reboot command not found'."
        - "Catch Exception and return 'reboot failed'."
        - "Log the command and its return code at DEBUG, and any exception with exc_info=True."
    - name: "EDIT Y — src/gtach/app.py: reset dispatch"
      type: "class"
      purpose: "Keep the reboot call off the display thread and let exactly one dispatch run at a time, replacing _on_bluetooth_reset."
      logic:
        - "Remove self._bt_reset_in_flight, self._bt_reset_status, self._bt_reset_lock, _set_bt_reset_status, and _on_bluetooth_reset."
        - "In __init__, add self._reset_in_flight = threading.Event(), initialised where _bt_reset_in_flight was."
        - "Add `def _on_reset_pi(self) -> None:`. It first tests self._reset_in_flight: if set, log at INFO that a reset is already in flight and return. Otherwise set the Event."
        - "Start a daemon threading.Thread, name 'pi_reset', targeting an inner function that calls pi_reset.reboot_device(), logs the returned outcome at INFO, and clears self._reset_in_flight in a finally so a raising worker cannot wedge the button permanently."
        - "Wrap the worker body in try/except Exception, logging with exc_info=True; the finally clause still clears the Event."
        - "Do NOT register the thread with ThreadManager: it is short-lived and must not be watchdog-monitored."
        - "_on_reset_pi must return promptly and perform no blocking call itself."
        - "Simplify _disconnected_cause: remove the block that reads/clears self._bt_reset_status and supersedes the transport cause with it. The method becomes: resolve transport via getattr(self, '_transport', None); return getattr(transport, 'last_failure_cause', None). Keep the docstring but remove the paragraph describing the reset-outcome merge."
        - "In both _start_setup_mode and _start_normal_mode, change self._display._bluetooth_reset_callback = self._on_bluetooth_reset to self._display._reset_callback = self._on_reset_pi."
    - name: "EDIT Z — src/gtach/display/manager.py: the button"
      type: "function"
      purpose: "Rename the identifiers and label; behaviour (conditional registration, geometry) is unchanged."
      logic:
        - "Rename the instance attribute self._bluetooth_reset_callback to self._reset_callback (__init__). Update its comment to describe the Reset/reboot button and reference issue-4ab5ff88 in place of issue-8a63d5f1."
        - "Rename self._disconnected_btn_bt_reset to self._disconnected_btn_reset (__init__ and _register_disconnected_regions)."
        - "In _register_disconnected_regions, rename the region id 'disconnected_bt_reset' to 'disconnected_reset', and the callback reference from self._bluetooth_reset_callback to self._reset_callback. Update the docstring's references to 'Bluetooth Reset' / issue-8a63d5f1 to describe the Reset/reboot button and issue-4ab5ff88. The conditional-registration structure (specs.append only when the callback is not None) is unchanged."
        - "In _render_disconnected, change the drawn label from 'BT Reset' to 'Reset', and remove the comment measuring the abbreviated label against the 240 px button — 'Reset' fits at the existing button font with no abbreviation needed, so the comment no longer applies. Reference self._disconnected_btn_reset in place of self._disconnected_btn_bt_reset."
        - "Do not change button width, top, font size, or _button_column's call signature."

data_schema:
  entities:
    - name: "reboot outcome"
      attributes:
        - name: "outcome"
          type: "str"
          constraints: "40 characters or fewer; never empty"
      validation:
        - "reboot_device returns a non-empty string on every path, including every exception path."

error_handling:
  strategy: >
    A privileged operation invoked by an operator must fail visibly
    (to the log; there is deliberately no cause-line outcome for this
    action) and safely. Every failure produces a loggable string, and
    none produces an exception that could reach the display thread.
  exceptions:
    - exception: "subprocess.TimeoutExpired"
      condition: "/sbin/reboot hangs."
      handling: "Return 'reboot timed out'. subprocess.run has already killed the child."
    - exception: "PermissionError"
      condition: "Not running as root."
      handling: "Return 'reboot not permitted'."
    - exception: "FileNotFoundError"
      condition: "/sbin/reboot vanishes between the os.path.exists check and invocation."
      handling: "Return 'reboot command not found'."
    - exception: "Exception"
      condition: "Anything else in reboot_device."
      handling: "Log with exc_info=True; return 'reboot failed'."
    - exception: "Exception"
      condition: "The worker thread body raises."
      handling: "Log with exc_info=True; clear self._reset_in_flight in a finally."
  logging:
    level: "DEBUG for the command and return code in pi_reset; INFO for the dispatch outcome in app.py; ERROR for exceptions"
    format: "Existing log format; no format change."

testing:
  unit_tests:
    - scenario: "reboot_device where /sbin/reboot exists and subprocess.run returns rc=0."
      expected: "'reboot initiated'; subprocess.run called once with ['/sbin/reboot'] and no shell=True."
    - scenario: "reboot_device where /sbin/reboot exists and subprocess.run returns a non-zero rc."
      expected: "'reboot command failed'."
    - scenario: "reboot_device where os.path.exists(_REBOOT_PATH) is False."
      expected: "'reboot command not found'; subprocess.run is never called."
    - scenario: "reboot_device where subprocess.run raises TimeoutExpired."
      expected: "'reboot timed out'; no exception."
    - scenario: "reboot_device where subprocess.run raises PermissionError."
      expected: "'reboot not permitted'."
    - scenario: "reboot_device where subprocess.run raises FileNotFoundError."
      expected: "'reboot command not found'."
    - scenario: "reboot_device where subprocess.run raises an arbitrary Exception."
      expected: "'reboot failed'; no exception propagates."
    - scenario: "Every outcome string reboot_device can return."
      expected: "All are non-empty and 40 characters or fewer."
    - scenario: "reboot_device with a custom timeout."
      expected: "The timeout value is passed through to subprocess.run."
    - scenario: "_on_reset_pi pressed once."
      expected: "Returns promptly; one daemon worker thread named 'pi_reset' started; the Event is set; the worker is not registered with ThreadManager."
    - scenario: "_on_reset_pi pressed twice in rapid succession."
      expected: "Exactly one worker thread exists; the second call returns without starting anything."
    - scenario: "_on_reset_pi where the worker body raises."
      expected: "The Event is cleared in the finally; nothing propagates out of the worker."
    - scenario: "_on_reset_pi after a completed dispatch."
      expected: "A second press starts a new worker."
    - scenario: "_on_reset_pi's outer body (excluding the nested worker function)."
      expected: "Contains no call to reboot_device, no join(), and no time.sleep."
    - scenario: "_disconnected_cause with no transport set."
      expected: "Returns None."
    - scenario: "_disconnected_cause with a transport whose last_failure_cause is set."
      expected: "Returns that value; no bt-reset-status merge branch remains."
    - scenario: "_register_disconnected_regions with _reset_callback unset."
      expected: "Only 'disconnected_setup' registered; self._disconnected_btn_reset is None."
    - scenario: "_register_disconnected_regions with _reset_callback set."
      expected: "Both regions registered, in order 'disconnected_setup' then 'disconnected_reset'; the Setup rect is identical to the one-button case."
    - scenario: "_render_disconnected with self._disconnected_btn_reset set."
      expected: "The second button is drawn with label exactly 'Reset'."
    - scenario: "_render_disconnected with self._disconnected_btn_reset None."
      expected: "Only the Setup button is drawn."
    - scenario: "subprocess-only-module invariant, project-wide."
      expected: "grep-equivalent scan of src/ finds 'subprocess' only in src/gtach/utils/pi_reset.py; exactly one call site to reboot_device exists, inside app.py."
  edge_cases:
    - "Application shutdown while a reset is in flight — the worker is a daemon and must not delay interpreter exit."
    - "The button pressed with no transport yet constructed — _disconnected_cause must not raise."
    - "/sbin/reboot present but returning a non-zero code without raising — treated as 'reboot command failed', not silently as success."
  validation:
    - "grep -rn 'subprocess' src/ shows matches only in src/gtach/utils/pi_reset.py."
    - "grep -rn 'shell=True' src/ returns no match."
    - "grep -rn 'reboot_device' src/ shows the definition and exactly one call site."
    - "grep -rn '_bluetooth_reset_callback\\|_disconnected_btn_bt_reset\\|disconnected_bt_reset\\|_bt_reset_in_flight\\|_bt_reset_status\\|_on_bluetooth_reset\\|reset_adapter' src/ tests/ returns no executable occurrence (historical prose in comments/docstrings, e.g. test_disconnected_screen.py's module docstring, is out of scope)."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Delete files specified for deletion; do not leave them in place unwired"
  files:
    - path: "src/gtach/utils/bluetooth_reset.py"
      content: "EDIT W — delete"
    - path: "tests/test_bluetooth_reset.py"
      content: "EDIT W — delete"
    - path: "src/gtach/utils/pi_reset.py"
      content: "EDIT X — new module"
    - path: "src/gtach/app.py"
      content: "EDIT Y"
    - path: "src/gtach/display/manager.py"
      content: "EDIT Z"
    - path: "tests/test_pi_reset.py"
      content: "Unit tests for testing.unit_tests items 1-14 and 20 (reboot_device, dispatch, subprocess-invariant)"
    - path: "tests/test_disconnected_screen.py"
      content: "Rename host._disconnected_btn_bt_reset to host._disconnected_btn_reset and host._bluetooth_reset_callback to host._reset_callback wherever they appear as attribute assignments. Add unit tests for testing.unit_tests items 15-19 (_disconnected_cause simplification, registration, rendering) if not already covered by an existing test class; do not alter the module docstring's historical account of why the reconnect spinner moved."

success_criteria:
  - "src/gtach/utils/bluetooth_reset.py and tests/test_bluetooth_reset.py no longer exist."
  - "src/gtach/utils/pi_reset.py exists and defines reboot_device returning a non-empty string, 40 characters or fewer, on every path."
  - "grep -rn 'subprocess' src/ shows matches only in src/gtach/utils/pi_reset.py."
  - "grep -rn 'shell=True' src/ returns no match."
  - "grep -rn 'reboot_device' src/ shows the definition and exactly one call site, inside GTachApplication's reset dispatch method."
  - "No timer, scheduler, retry counter or startup path invokes reboot_device."
  - "_on_reset_pi returns without performing any blocking call, and starts a daemon thread named 'pi_reset' not registered with ThreadManager."
  - "The reset dispatch's debounce Event is cleared in a finally clause."
  - "The reboot command invoked is exactly ['/sbin/reboot'], with no shutil.which, systemctl, or shutdown invocation anywhere in src/."
  - "No executable occurrence of '_bluetooth_reset_callback', '_disconnected_btn_bt_reset', 'disconnected_bt_reset', '_bt_reset_in_flight', '_bt_reset_status', '_on_bluetooth_reset', or 'reset_adapter' remains in src/ or tests/ (historical prose in comments/docstrings is out of scope and unaltered)."
  - "The disconnected_reset region is registered only when self._reset_callback is set; the disconnected_setup rect is identical whether one or two buttons are registered."
  - "The DISCONNECTED screen's second button, when registered, is drawn with label exactly 'Reset'."
  - "_disconnected_cause contains no reference to a reset-status merge; it reads only the transport's last_failure_cause."
  - "src/gtach/comm/, bin/gtach.service and bin/install.sh are byte-identical to their pre-change state."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "pi_reset"
        path: "src/gtach/utils/pi_reset.py"
      - name: "app"
        path: "src/gtach/app.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
    classes:
      - name: "GTachApplication"
        module: "gtach.app"
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "reboot_device"
        module: "gtach.utils.pi_reset"
        signature: "(timeout: float = 10.0) -> str"
      - name: "_on_reset_pi"
        module: "gtach.app"
        signature: "(self) -> None"
      - name: "_disconnected_cause"
        module: "gtach.app"
        signature: "(self) -> Optional[str]"
      - name: "_register_disconnected_regions"
        module: "gtach.display.manager"
        signature: "(self) -> None"
    constants:
      - name: "_REBOOT_PATH"
        module: "gtach.utils.pi_reset"
        type: "str"

notes: >
  On-target verification is a human step. Deploy, trigger the
  DISCONNECTED screen, press Reset once and confirm the Pi reboots.
  Press twice quickly beforehand on a non-critical bench test if
  practical, to confirm only one reboot dispatch occurs (a second
  reboot request while one is already underway is generally harmless
  on Linux, but the debounce should still prevent the second call from
  reaching reboot_device at all).

  change-950128c0 (open, unrelated) lists tests/test_bluetooth_reset.py
  in its own regression scope. That file is deleted by this prompt. If
  change-950128c0 executes afterward, its regression check must read
  tests/test_pi_reset.py in its place — William sequences the two.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial prompt implementing change-4ab5ff88 iteration 1. Deletes bluetooth_reset.py and its test; adds pi_reset.py and its test; renames the DISCONNECTED screen's second button and its callback chain; removes the reset-outcome cause-line merge. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
