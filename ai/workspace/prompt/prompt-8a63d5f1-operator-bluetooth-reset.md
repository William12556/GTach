Created: 2026 August 12

# Prompt: Operator-Initiated Bluetooth Reset From the DISCONNECTED Screen

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-8a63d5f1"
  task_type: "code_generation"
  source_ref: "change-8a63d5f1"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-8a63d5f1"
    change_iteration: 1

context:
  purpose: >
    The DISCONNECTED screen reports "bluetooth wedged - reset required"
    and offers no way to perform that reset. Add a Bluetooth Reset
    button in the slot change-4f1e82b7 left free, dispatching a
    bounded, debounced controller reset to a worker thread and
    reporting the outcome on the existing cause line.
  integration: >
    One new module, src/gtach/utils/bluetooth_reset.py; a dispatch
    method in src/gtach/app.py; a button in
    src/gtach/display/manager.py.
  knowledge_references:
    - "ai/workspace/issues/issue-8a63d5f1-operator-bluetooth-reset.md"
    - "ai/workspace/change/change-8a63d5f1-operator-bluetooth-reset.md"
  constraints:
    - "CRITICAL: the reset must NEVER run on the display thread. 'display' is a watchdog critical thread at a 45 s timeout, and since change-2ac1c602 a critical timeout terminates the process — so a synchronous subprocess in the touch callback would make the button restart the application. Dispatch to a daemon worker thread and return immediately."
    - "CRITICAL: there must be NO automatic invocation of reset_adapter, on any trigger — not a wedge diagnosis, not a retry count, not startup, not a timer. The button callback is the only call site. This boundary is the entire basis on which host action is permitted here."
    - "Do not use shell=True anywhere. Invoke a fixed argument list with an absolute path. No value derived from configuration, the network or the operator may reach the command line."
    - "Do not use `hciconfig hci0 down` followed by `up` as the reset. That exact sequence was attempted on target: down succeeded, up returned ETIMEDOUT, and the controller could not be brought back. Use `hciconfig hci0 reset`."
    - "Do not add systemctl, hciuart, rfkill or kernel module operations."
    - "subprocess may be imported ONLY in src/gtach/utils/bluetooth_reset.py. It must appear nowhere else, and in particular nowhere under src/gtach/comm/, where change-5e7a03c4 forbids it."
    - "Do not modify src/gtach/comm/ at all. The reconnect loop resumes on its own once the adapter recovers."
    - "Do not modify the retry-countdown arc, the cause line rendering, or the Setup button."
    - "Do not register the new button when its callback is unset, so the screen degrades to its current form."
    - "Python 3.9+ compatible. PEP 8. Type hints on all public interfaces. Google-style docstrings."

specification:
  description: "Apply edits X, Y and Z, then add the unit tests in the testing section."
  requirements:
    functional:
      - "A button press dispatches a controller reset to a worker thread and returns immediately."
      - "A press while a reset is in flight is ignored, not queued."
      - "The operation is bounded by a timeout; a hung command is killed."
      - "The adapter is confirmed up afterwards, with one up attempt if it is not."
      - "A failure that leaves the adapter down says so explicitly."
      - "Progress and outcome are written to the existing cause line."
      - "reset_adapter never raises."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "The display loop continues rendering at 30 FPS throughout a reset"
      metric: "time"

design:
  architecture: >
    The privileged surface is one function in one module, called from
    one place behind one button. Everything that can block runs on a
    worker; everything the display touches is a short string.
  components:
    - name: "EDIT X — src/gtach/utils/bluetooth_reset.py"
      type: "module"
      purpose: "Own the privileged operation, in one reviewable place."
      logic:
        - "New module with the project's standard copyright header and a module docstring stating that this is the ONLY place in GTach permitted to invoke an external command, and why."
        - "Import subprocess, shutil, logging and typing. No other imports."
        - "Module constant _ADAPTER = 'hci0'."
        - "Add `def _hciconfig_path() -> Optional[str]:` resolving via shutil.which('hciconfig'), falling back to '/usr/bin/hciconfig' when that exists, else None."
        - "Add `def reset_adapter(timeout: float = 10.0) -> str:` returning a short outcome string, 40 characters or fewer, suitable for the cause line."
        - "reset_adapter body: resolve the path; if None return 'hciconfig not found'. Run [path, _ADAPTER, 'reset'] with subprocess.run(capture_output=True, timeout=timeout, check=False)."
        - "Then verify: run [path, _ADAPTER] and treat the presence of 'UP RUNNING' in stdout as up. If up, return 'bluetooth adapter reset'."
        - "If not up, run [path, _ADAPTER, 'up'] once, then verify again. If up now, return 'bluetooth adapter reset'. If still not, return 'adapter down - reboot required'."
        - "That last string is deliberate and must not be softened: the manual attempt on this host left the controller in exactly this state, and the operator needs to be told plainly."
        - "Catch subprocess.TimeoutExpired and return 'bluetooth reset timed out'. subprocess.run kills the process on timeout; do not add a second kill."
        - "Catch PermissionError and return 'bluetooth reset not permitted'."
        - "Catch Exception and return 'bluetooth reset failed'. reset_adapter must never raise, for any input or environment."
        - "Log each command and its return code at DEBUG, and any exception with exc_info=True."
    - name: "EDIT Y — src/gtach/app.py: debounced worker dispatch"
      type: "class"
      purpose: "Keep the blocking work off the display thread and let exactly one reset run at a time."
      logic:
        - "In __init__, add self._bt_reset_in_flight = threading.Event()."
        - "Add `def _on_bluetooth_reset(self) -> None:`."
        - "It first tests the Event: `if self._bt_reset_in_flight.is_set(): return` — a press during a reset is ignored, NOT queued. Then set the Event."
        - "Write a progress cause so the operator sees the press registered. Use the same route the display already reads: set the transport's cause if one is available, otherwise hold the string on the application and expose it through the existing _link_cause_callback wiring. Choose whichever the existing code makes cleaner, and state the choice in a comment."
        - "Start a daemon threading.Thread targeting an inner function that calls bluetooth_reset.reset_adapter(), writes the returned outcome as the cause, and clears self._bt_reset_in_flight in a `finally` so a raising worker cannot wedge the button permanently."
        - "Wrap the worker body in try/except Exception, logging with exc_info=True and writing 'bluetooth reset failed' as the outcome."
        - "Name the thread 'bt_reset'. Do NOT register it with ThreadManager: it is short-lived and must not be monitored by WatchdogMonitor."
        - "_on_bluetooth_reset must return promptly. It performs no blocking call itself."
        - "In _start_normal_mode, wire self._display._bluetooth_reset_callback = self._on_bluetooth_reset, beside the existing _link_cause_callback and _retry_interval_callback assignments."
    - name: "EDIT Z — src/gtach/display/manager.py: the button"
      type: "function"
      purpose: "Put the control in the slot left free for it."
      logic:
        - "Add an instance attribute self._bluetooth_reset_callback = None, initialised beside _link_cause_callback and _retry_interval_callback."
        - "In _register_disconnected_regions, build the specs sequence conditionally: always the Setup entry; append ('disconnected_bt_reset', TouchAction.NAVIGATION, lambda pos: self._bluetooth_reset_callback()) ONLY when self._bluetooth_reset_callback is not None."
        - "Pass the sequence to _button_column with width=240 and top=240 unchanged, and assign the returned rects. The Setup rect must be identical whether one or two buttons are registered — _button_column stacks downward from an explicit top, so this holds; assert it in a test."
        - "Store the second rect as self._disconnected_btn_bt_reset, or None when the callback is unset."
        - "In _render_disconnected, draw the second button with label 'Bluetooth Reset' via the existing _draw_button, only when its rect is not None."
        - "If the label does not fit the 240 px button at the existing button font, use 'BT Reset'. Do not change the button width or the font size for other buttons."
        - "Do not modify _button_column, the arc, the cause line, or the Setup button's spec."

data_schema:
  entities:
    - name: "reset outcome"
      attributes:
        - name: "outcome"
          type: "str"
          constraints: "40 characters or fewer; never empty"
      validation:
        - "reset_adapter returns a non-empty string on every path, including every exception path."

error_handling:
  strategy: >
    A privileged operation invoked by an operator must fail visibly and
    safely. Every failure produces a string the operator can read, and
    none produces an exception that could reach the display thread.
  exceptions:
    - exception: "subprocess.TimeoutExpired"
      condition: "hciconfig hangs."
      handling: "Return 'bluetooth reset timed out'. subprocess.run has already killed the child."
    - exception: "PermissionError"
      condition: "Not running as root."
      handling: "Return 'bluetooth reset not permitted'."
    - exception: "FileNotFoundError"
      condition: "hciconfig missing despite path resolution."
      handling: "Return 'hciconfig not found'."
    - exception: "Exception"
      condition: "Anything else in reset_adapter."
      handling: "Log with exc_info=True; return 'bluetooth reset failed'."
    - exception: "Exception"
      condition: "The worker thread body raises."
      handling: "Log with exc_info=True; write 'bluetooth reset failed' as the outcome; clear the debounce Event in a finally."
  logging:
    level: "DEBUG for each command and return code; ERROR for exceptions"
    format: "Existing _LOG_FORMAT; no format change."

testing:
  unit_tests:
    - scenario: "reset_adapter where reset returns 0 and verification reports UP RUNNING."
      expected: "'bluetooth adapter reset'; exactly two commands run."
    - scenario: "reset_adapter where reset returns 0 but verification does not report UP RUNNING, and the subsequent up succeeds."
      expected: "'bluetooth adapter reset'; an up command was run."
    - scenario: "reset_adapter where reset succeeds, the adapter stays down, and up fails."
      expected: "'adapter down - reboot required'."
    - scenario: "reset_adapter where subprocess.run raises TimeoutExpired."
      expected: "'bluetooth reset timed out'; no exception."
    - scenario: "reset_adapter where the path cannot be resolved."
      expected: "'hciconfig not found'; no command attempted."
    - scenario: "reset_adapter where subprocess.run raises PermissionError."
      expected: "'bluetooth reset not permitted'."
    - scenario: "reset_adapter where subprocess.run raises an arbitrary Exception."
      expected: "'bluetooth reset failed'; no exception propagates."
    - scenario: "Every outcome string reset_adapter can return."
      expected: "All are non-empty and 40 characters or fewer."
    - scenario: "_on_bluetooth_reset pressed once."
      expected: "Returns promptly; one worker thread started; the Event is set."
    - scenario: "_on_bluetooth_reset pressed twice in rapid succession."
      expected: "Exactly one worker; the second call returns without starting anything."
    - scenario: "_on_bluetooth_reset where the worker body raises."
      expected: "The Event is cleared; an outcome is written; nothing propagates."
    - scenario: "_on_bluetooth_reset after a completed reset."
      expected: "A second press starts a new worker."
    - scenario: "_register_disconnected_regions with _bluetooth_reset_callback unset."
      expected: "Only disconnected_setup registered; no disconnected_bt_reset."
    - scenario: "_register_disconnected_regions with the callback set."
      expected: "Two regions; the disconnected_setup rect is identical to the one-button case."
  edge_cases:
    - "Application shutdown while a reset is in flight — the worker is a daemon and must not delay interpreter exit."
    - "The button pressed with no transport yet constructed — the cause write must be guarded."
    - "hciconfig present but returning unexpected stdout — treated as not up, so the up path runs; no parsing exception."
  validation:
    - "grep -rn 'subprocess' src/ shows matches only in src/gtach/utils/bluetooth_reset.py."
    - "grep -rn 'shell=True' src/ returns no match."
    - "grep -rn 'reset_adapter' src/ shows the definition and exactly one call site."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
  files:
    - path: "src/gtach/utils/bluetooth_reset.py"
      content: "EDIT X — new module"
    - path: "src/gtach/app.py"
      content: "EDIT Y"
    - path: "src/gtach/display/manager.py"
      content: "EDIT Z"
    - path: "tests/test_bluetooth_reset.py"
      content: "Unit tests for testing.unit_tests items 1-14"

success_criteria:
  - "src/gtach/utils/bluetooth_reset.py exists and defines reset_adapter returning a non-empty string on every path."
  - "grep -rn 'subprocess' src/ matches only src/gtach/utils/bluetooth_reset.py."
  - "grep -rn 'shell=True' src/ returns no match."
  - "grep -rn 'reset_adapter' src/ shows the definition and exactly one call site, inside GTachApplication._on_bluetooth_reset."
  - "No timer, scheduler, retry counter or startup path invokes reset_adapter."
  - "_on_bluetooth_reset returns without performing any blocking call, and starts a daemon thread named 'bt_reset'."
  - "The reset worker thread is NOT registered with ThreadManager."
  - "The debounce Event is cleared in a finally clause."
  - "The reset command is `hciconfig hci0 reset`; no occurrence of `hci0 down` exists in src/."
  - "'adapter down - reboot required' is returned when the adapter cannot be brought back up."
  - "The disconnected_bt_reset region is registered only when _bluetooth_reset_callback is set."
  - "The disconnected_setup rect is identical whether one or two buttons are registered."
  - "src/gtach/comm/ is byte-identical throughout; _button_column, _draw_retry_arc and the cause line rendering are unchanged."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "bluetooth_reset"
        path: "src/gtach/utils/bluetooth_reset.py"
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
      - name: "reset_adapter"
        module: "gtach.utils.bluetooth_reset"
        signature: "(timeout: float = 10.0) -> str"
      - name: "_hciconfig_path"
        module: "gtach.utils.bluetooth_reset"
        signature: "() -> Optional[str]"
      - name: "_on_bluetooth_reset"
        module: "gtach.app"
        signature: "(self) -> None"
      - name: "_register_disconnected_regions"
        module: "gtach.display.manager"
        signature: "(self) -> None"
    constants:
      - name: "_ADAPTER"
        module: "gtach.utils.bluetooth_reset"
        type: "str"

notes: >
  On-target verification is a human step. Press the button and confirm
  the retry arc keeps animating and the performance line still reports
  30.0 FPS throughout — if the display stalls, the dispatch is wrong
  and the watchdog will eventually restart the application. Confirm the
  outcome appears on the cause line. Press twice quickly and confirm
  only one reset runs.

  IMPORTANT EXPECTATION. This button is NOT expected to fix the failure
  currently on gtach.local. That condition survives a full reboot —
  stacks.log headers show pid 720 at 14:52:37 then pid 671 at 14:56:32,
  a decreasing pid, with the same [Errno 16] failures resuming
  immediately on the new run. A controller reset is strictly weaker
  than a reboot. The button addresses a narrower class of wedge, of the
  kind observed on this host earlier at 13:xx where hcitool con showed
  an ACL in state 9 with its handle unreaped. Locating the present
  fault is a separate investigation, most probably on the ELM327
  emulator.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial prompt implementing change-8a63d5f1 iteration 1. New bluetooth_reset module, debounced worker dispatch, and the DISCONNECTED button. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
